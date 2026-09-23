import json
from datetime import timedelta

from django.contrib.auth import SESSION_KEY, get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerificationCode

# Les codes sont envoyés via le backend "locmem" pendant les tests afin
# qu'ils soient capturés dans `django.core.mail.outbox` au lieu d'être
# réellement expédiés.
LOCMEM_MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}


class ApiTestCase(TestCase):
    """Socle commun aux tests de l'API de l'espace assuré."""

    password = 'Xy7-Trebuchet-Cnam'

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('register')
        cls.login_url = reverse('login_api')
        cls.logout_url = reverse('logout_api')
        cls.send_url = reverse('otp_send')
        cls.verify_url = reverse('otp_verify')

    def setUp(self):
        mail.outbox = []

    def post_json(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def request_code(self, email='assure@example.com'):
        """Demande un code de vérification et retourne l'enregistrement créé."""
        response = self.post_json(self.send_url, {'email': email})
        self.assertEqual(response.status_code, 200, response.content)
        # L'API normalise l'adresse (minuscules, sans espaces) avant stockage.
        return EmailVerificationCode.objects.filter(email=email.strip().lower()).latest('created_at')


@override_settings(MAILERS=LOCMEM_MAILERS)
class OtpSendViewTests(ApiTestCase):
    """POST /api/otp/send/ (vérification par e-mail, optionnelle)"""

    def test_send_creates_code_and_sends_email(self):
        code = self.request_code()

        self.assertEqual(len(code.code), EmailVerificationCode.CODE_LENGTH)
        self.assertTrue(code.code.isdigit())
        self.assertTrue(code.is_usable)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['assure@example.com'])
        self.assertIn(code.code, mail.outbox[0].body)

    def test_send_normalises_email(self):
        self.request_code('  Assure@Example.com ')
        self.assertTrue(EmailVerificationCode.objects.filter(email='assure@example.com').exists())

    def test_send_rejects_invalid_email(self):
        response = self.post_json(self.send_url, {'email': 'pas-un-email'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(EmailVerificationCode.objects.count(), 0)

    def test_send_rejects_missing_email(self):
        response = self.post_json(self.send_url, {})

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_send_rejects_malformed_json(self):
        response = self.client.post(
            self.send_url, data='pas du json', content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_send_rejects_existing_account(self):
        User = get_user_model()
        User.objects.create_user(
            username='assure@example.com', email='assure@example.com', password=self.password
        )

        response = self.post_json(self.send_url, {'email': 'assure@example.com'})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_invalidates_previous_code(self):
        first = self.request_code()
        second = self.request_code()

        first.refresh_from_db()
        self.assertFalse(first.is_usable)
        self.assertTrue(second.is_usable)

    def test_send_only_accepts_post(self):
        self.assertEqual(self.client.get(self.send_url).status_code, 405)


@override_settings(MAILERS=LOCMEM_MAILERS)
class OtpVerifyViewTests(ApiTestCase):
    """POST /api/otp/verify/ – création du compte après saisie du code"""

    def verify(self, code, email='assure@example.com', password=None):
        return self.post_json(
            self.verify_url,
            {'email': email, 'code': code, 'password': password or self.password},
        )

    def test_verify_creates_account_and_consumes_code(self):
        verification = self.request_code()

        response = self.verify(verification.code)

        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn('message', response.json())

        user = get_user_model().objects.get(username='assure@example.com')
        self.assertEqual(user.email, 'assure@example.com')
        self.assertTrue(user.check_password(self.password))

        verification.refresh_from_db()
        self.assertIsNotNone(verification.consumed_at)

    def test_verify_rejects_wrong_code(self):
        verification = self.request_code()
        wrong_code = '000000' if verification.code != '000000' else '111111'

        response = self.verify(wrong_code)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Code incorrect', response.json()['error'])
        self.assertFalse(get_user_model().objects.exists())

        verification.refresh_from_db()
        self.assertEqual(verification.attempts, 1)
        self.assertTrue(verification.is_usable)

    def test_verify_blocks_after_too_many_attempts(self):
        verification = self.request_code()
        wrong_code = '000000' if verification.code != '000000' else '111111'

        for _ in range(EmailVerificationCode.MAX_ATTEMPTS):
            self.verify(wrong_code)

        verification.refresh_from_db()
        self.assertFalse(verification.is_usable)

        # Même avec le bon code, un code bloqué ne peut plus être utilisé.
        response = self.verify(verification.code)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Trop de tentatives', response.json()['error'])
        self.assertFalse(get_user_model().objects.exists())

    def test_verify_rejects_expired_code(self):
        verification = self.request_code()
        EmailVerificationCode.objects.filter(pk=verification.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        response = self.verify(verification.code)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Aucun code valide', response.json()['error'])
        self.assertFalse(get_user_model().objects.exists())

    def test_verify_rejects_reused_code(self):
        verification = self.request_code()

        self.assertEqual(self.verify(verification.code).status_code, 200)
        second = self.verify(verification.code)

        self.assertEqual(second.status_code, 400)
        self.assertIn('Aucun code valide', second.json()['error'])

    def test_verify_rejects_code_belonging_to_another_email(self):
        verification = self.request_code('assure@example.com')

        response = self.verify(verification.code, email='autre@example.com')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.exists())

    def test_verify_requires_six_digits(self):
        self.request_code()

        response = self.verify('123')

        self.assertEqual(response.status_code, 400)
        self.assertIn('6 chiffres', response.json()['error'])

    def test_verify_rejects_short_password(self):
        verification = self.request_code()

        response = self.verify(verification.code, password='abc')

        self.assertEqual(response.status_code, 400)
        self.assertIn('8 caractères', response.json()['error'])
        self.assertFalse(get_user_model().objects.exists())

    def test_verify_normalises_email_case(self):
        verification = self.request_code('assure@example.com')

        response = self.verify(verification.code, email='ASSURE@example.com')

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(get_user_model().objects.filter(username='assure@example.com').exists())

    def test_verify_only_accepts_post(self):
        self.assertEqual(self.client.get(self.verify_url).status_code, 405)


class HomePageTests(TestCase):
    """La page d'accueil expose les formulaires et la protection CSRF utilisée par script.js."""

    def test_home_page_renders_forms_and_sets_csrf_cookie(self):
        response = self.client.get(reverse('accueil_fds'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)
        self.assertContains(response, 'reg-email')
        self.assertContains(response, 'handleRegistration')
        self.assertContains(response, 'handleLogin')
        self.assertContains(response, 'login-message')
        self.assertContains(response, 'register-message')

    def test_home_page_has_no_otp_verification_page(self):
        response = self.client.get(reverse('accueil_fds'))

        self.assertNotContains(response, 'otp-view')
        self.assertNotContains(response, 'verifyOtpPage')
        self.assertNotContains(response, 'otp-digit')


class RegisterApiTests(ApiTestCase):
    """POST /api/register/ : inscription par e-mail + mot de passe, sans code OTP."""

    def register(self, email='assure@example.com', password=None, confirmation=None):
        chosen = password or self.password
        return self.post_json(
            self.register_url,
            {
                'email': email,
                'password': chosen,
                'password_confirm': chosen if confirmation is None else confirmation,
            },
        )

    def test_register_creates_account_and_opens_session(self):
        response = self.register()

        self.assertEqual(response.status_code, 201, response.content)
        self.assertIn('message', response.json())
        self.assertEqual(len(mail.outbox), 0)  # ni e-mail, ni code OTP

        user = get_user_model().objects.get(username='assure@example.com')
        self.assertEqual(user.email, 'assure@example.com')
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        # L'assuré entre directement dans son espace : session ouverte dès l'inscription.
        self.assertEqual(self.client.session.get(SESSION_KEY), str(user.pk))

    def test_register_normalises_email(self):
        response = self.register(email='  Assure@Example.com ')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(username='assure@example.com').exists())

    def test_register_rejects_duplicate_email(self):
        self.register()

        response = self.register()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_register_rejects_mismatched_confirmation(self):
        response = self.register(confirmation='AutreMotDePasse123')

        self.assertEqual(response.status_code, 400)
        self.assertIn('ne correspondent pas', response.json()['error'])
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_register_rejects_short_password(self):
        response = self.register(password='abc')

        self.assertEqual(response.status_code, 400)
        self.assertIn('8 caractères', response.json()['error'])
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_register_rejects_invalid_email(self):
        response = self.register(email='pas-un-email')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_register_only_accepts_post(self):
        self.assertEqual(self.client.get(self.register_url).status_code, 405)


class LoginApiTests(ApiTestCase):
    """POST /api/login/ : connexion par e-mail + mot de passe, sans code OTP."""

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            username='assure@example.com',
            email='assure@example.com',
            password=self.password,
        )

    def login(self, email='assure@example.com', password=None):
        return self.post_json(
            self.login_url,
            {'email': email, 'password': self.password if password is None else password},
        )

    def test_login_with_email_and_password(self):
        response = self.login()

        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn('message', response.json())
        self.assertEqual(self.client.session.get(SESSION_KEY), str(self.user.pk))

    def test_login_accepts_uppercase_email(self):
        response = self.login(email='ASSURE@Example.com')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get(SESSION_KEY), str(self.user.pk))

    def test_login_rejects_wrong_password(self):
        response = self.login(password='MauvaisMotDePasse123')

        self.assertEqual(response.status_code, 401)
        self.assertIn('incorrect', response.json()['error'])
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_rejects_unknown_email(self):
        response = self.login(email='inconnu@example.com')

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_rejects_missing_password(self):
        response = self.login(password='')

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_only_accepts_post(self):
        self.assertEqual(self.client.get(self.login_url).status_code, 405)


class LogoutApiTests(ApiTestCase):
    """POST /api/logout/ : fermeture de la session."""

    def test_logout_clears_session(self):
        user = get_user_model().objects.create_user(
            username='assure@example.com',
            email='assure@example.com',
            password=self.password,
        )
        self.client.force_login(user)
        self.assertIn(SESSION_KEY, self.client.session)

        response = self.post_json(self.logout_url, {})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)

