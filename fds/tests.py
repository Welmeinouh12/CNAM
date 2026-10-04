import io
import json
import shutil
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pymupdf
from PIL import Image
from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .feuille_soins_layout import PHOTO_BOITE
from .feuille_soins_pdf import _generer_reproduction, generer_feuille_soins
from .models import Assure, Etablissement, EmailVerificationCode
from .services import donnees_feuille_soins, rechercher_assure

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

    def test_home_page_expose_la_recherche_d_assure(self):
        """Champ NNI/INAM, bouton « Vérifier » et zones de résultat."""
        response = self.client.get(reverse('accueil_fds'))

        self.assertContains(response, 'assure-identifiant')
        self.assertContains(response, 'btn-verifier-assure')
        self.assertContains(response, 'verifierAssure()')
        self.assertContains(response, 'assure-resultat')
        self.assertContains(response, 'assure-introuvable')
        self.assertContains(response, 'btn-telecharger-feuille')
        self.assertContains(response, 'telechargerFeuilleSoins()')



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


# ===========================================================================
# RECHERCHE DE L'ASSURÉ (NNI / INAM) ET FEUILLE DE SOINS PDF
# ===========================================================================
def photo_de_test(couleur=(17, 66, 146)):
    """Retourne les octets d'une photo JPEG (35 x 45 mm) pour les tests."""
    image = Image.new('RGB', (413, 531), couleur)
    tampon = io.BytesIO()
    image.save(tampon, format='JPEG', quality=80)
    return tampon.getvalue()


def texte_du_pdf(octets):
    """Texte du calque texte d'un PDF (pour vérifier les valeurs posées)."""
    document = pymupdf.open(stream=octets, filetype='pdf')
    try:
        return '\n'.join(page.get_text() for page in document)
    finally:
        document.close()


def donnees_de_test(**surcharges):
    """Données de feuille de soins pour un assuré non enregistré."""
    attributs = {
        'nni': '0124336042',
        'inam': '180612797938-E',
        'numero_carte': 'CN-9948271',
        'nom': 'SidAhmed',
        'prenom': 'Ahmed Vali',
        'sexe': 'M',
        'date_naissance': date(2002, 1, 15),
        'telephone': '22 33 44 55',
        'photo': photo_de_test(),
        'photo_type': 'image/jpeg',
    }
    attributs.update(surcharges)
    return donnees_feuille_soins(Assure(**attributs), timezone.now())


class AssureModeleTests(TestCase):
    """Modèle Assure : âge, nom complet et récupération de la photo."""

    def test_age_calcule_depuis_la_date_de_naissance(self):
        assure = Assure(
            nni='0124336042', nom='SidAhmed', prenom='Ahmed Vali',
            date_naissance=date(2000, 1, 1),
        )
        aujourdhui = timezone.localdate()

        self.assertEqual(assure.age, aujourdhui.year - 2000)

    def test_age_none_sans_date_de_naissance(self):
        self.assertIsNone(Assure(nni='1', nom='Test').age)

    def test_nom_complet(self):
        assure = Assure(nni='1', nom='Ould Ahmed', prenom='Mohamed Lemine')

        self.assertEqual(assure.nom_complet, 'Ould Ahmed Mohamed Lemine')

    def test_photo_binaire_lit_le_binaire_de_la_base(self):
        assure = Assure(nni='1', nom='Test', photo=photo_de_test())

        self.assertTrue(assure.photo_binaire().startswith(b'\xff\xd8'))

    def test_photo_binaire_lit_un_fichier_sur_le_disque(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / 'photo.jpg'
            chemin.write_bytes(photo_de_test())
            assure = Assure(nni='1', nom='Test', photo_path=str(chemin))

            self.assertIsNotNone(assure.photo_binaire())

    def test_photo_binaire_none_sans_photo(self):
        self.assertIsNone(Assure(nni='1', nom='Test').photo_binaire())

    def test_photo_binaire_none_si_le_fichier_est_absent(self):
        assure = Assure(nni='1', nom='Test', photo_path='inexistant.jpg')

        self.assertIsNone(assure.photo_binaire())


class RechercheAssureTests(TestCase):
    """`services.rechercher_assure` : recherche par NNI ou par INAM."""

    def setUp(self):
        self.assure = Assure.objects.create(
            nni='0124336042',
            inam='180612797938-E',
            nom='SidAhmed',
            prenom='Ahmed Vali',
            date_naissance=date(2002, 1, 15),
        )

    def test_recherche_par_nni(self):
        self.assertEqual(rechercher_assure('0124336042').pk, self.assure.pk)

    def test_recherche_par_inam(self):
        self.assertEqual(rechercher_assure('180612797938-E').pk, self.assure.pk)

    def test_recherche_insensible_a_la_casse(self):
        self.assertEqual(rechercher_assure('180612797938-e').pk, self.assure.pk)

    def test_recherche_ignore_les_espaces_saisis(self):
        self.assertEqual(rechercher_assure(' 0124 336042 ').pk, self.assure.pk)

    def test_recherche_tolere_les_espaces_en_base(self):
        Assure.objects.create(nni='7734512098', inam='170900123456  -B', nom='Mint')
        trouve = rechercher_assure('170900123456-B')

        self.assertIsNotNone(trouve)
        self.assertEqual(trouve.inam, '170900123456  -B')

    def test_assure_introuvable(self):
        self.assertIsNone(rechercher_assure('9999999999'))

    def test_identifiant_trop_court(self):
        self.assertIsNone(rechercher_assure('12'))

    def test_identifiant_vide(self):
        self.assertIsNone(rechercher_assure('   '))
        self.assertIsNone(rechercher_assure(None))


class FeuilleSoinsDonneesTests(TestCase):
    """Données dynamiques posées sur la feuille de soins."""

    def test_numero_de_feuille_genere(self):
        donnees = donnees_de_test()

        self.assertRegex(donnees['numero_feuille'], r'^\d{6}/\d{4}/PH\d{5}$')

    def test_numero_de_feuille_de_postgresql_est_prioritaire(self):
        donnees = donnees_de_test(numero_feuille='124826/2025/PH13096')

        self.assertEqual(donnees['numero_feuille'], '124826/2025/PH13096')

    def test_date_de_soins_est_la_date_du_jour(self):
        donnees = donnees_de_test()
        aujourdhui = timezone.localtime().strftime('%Y/%m/%d')

        self.assertTrue(donnees['date_soins_texte'].startswith(aujourdhui))

    def test_code_qr_genere_depuis_l_assure(self):
        contenu = donnees_de_test()['qr_contenu']

        self.assertIn('0124336042', contenu)
        self.assertIn('180612797938-E', contenu)
        self.assertIn('SidAhmed', contenu)

    def test_code_qr_de_postgresql_est_prioritaire(self):
        donnees = donnees_de_test(code_qr='CNAM|QR|OFFICIEL')

        self.assertEqual(donnees['qr_contenu'], 'CNAM|QR|OFFICIEL')

    def test_age_et_date_de_naissance_mis_en_forme(self):
        donnees = donnees_de_test()

        self.assertEqual(donnees['date_naissance_texte'], '15/01/2002')
        self.assertTrue(donnees['age_texte'].endswith(' ans'))

    def test_photo_transmise_au_pdf(self):
        self.assertTrue(donnees_de_test()['photo'])

    def test_sans_photo_ni_date_de_naissance(self):
        donnees = donnees_de_test(photo=None, date_naissance=None)

        self.assertIsNone(donnees['photo'])
        self.assertEqual(donnees['date_naissance_texte'], '')
        self.assertEqual(donnees['age_texte'], '')


@override_settings(CNAM_FEUILLE_SOINS_MODELE='', CNAM_FEUILLE_SOINS_MODELE_IMAGE='')
class FeuilleSoinsPdfTests(TestCase):
    """Génération du PDF (reproduction du modèle, sans fichier modèle)."""

    def test_pdf_genere_avec_les_donnees_de_l_assure(self):
        contenu = generer_feuille_soins(donnees_de_test())
        texte = texte_du_pdf(contenu)

        self.assertTrue(contenu.startswith(b'%PDF-'))
        self.assertIn('SidAhmed Ahmed Vali', texte)
        self.assertIn('0124336042', texte)
        self.assertIn('180612797938-E', texte)
        self.assertIn('15/01/2002', texte)
        self.assertIn('Feuille de Soins', texte)

    def test_pdf_reprend_la_structure_du_modele(self):
        texte = texte_du_pdf(generer_feuille_soins(donnees_de_test()))

        for libelle in (
            "Caisse Nationale d'Assurance Maladie - CNAM",
            'Prescription de médecin',
            'Analyses, Examens et Radio',
            'Hospitalisation',
            'Signature et cachet du prescripteur(Obligatoire):',
            'Cachet & Signature',
        ):
            self.assertIn(libelle, texte)

    def test_pdf_avec_et_sans_photo(self):
        avec = pymupdf.open(stream=generer_feuille_soins(donnees_de_test()), filetype='pdf')
        sans = pymupdf.open(
            stream=generer_feuille_soins(donnees_de_test(photo=None)), filetype='pdf'
        )
        try:
            self.assertGreater(len(avec[0].get_images()), len(sans[0].get_images()))
        finally:
            avec.close()
            sans.close()

    def test_pdf_sans_photo_ni_donnees_optionnelles(self):
        donnees = donnees_de_test(photo=None, date_naissance=None, inam='')
        contenu = generer_feuille_soins(donnees)

        self.assertTrue(contenu.startswith(b'%PDF-'))
        self.assertIn('0124336042', texte_du_pdf(contenu))

    def test_pdf_contient_le_code_qr(self):
        document = pymupdf.open(
            stream=generer_feuille_soins(donnees_de_test()), filetype='pdf'
        )
        try:
            self.assertIn('SCAN ME', document[0].get_text())
            self.assertGreaterEqual(len(document[0].get_images()), 2)
        finally:
            document.close()

    def test_pdf_avec_date_de_soins_imposee(self):
        donnees = donnees_feuille_soins(
            Assure(
                nni='0124336042',
                inam='180612797938-E',
                nom='SidAhmed',
                date_naissance=date(2002, 1, 15),
            ),
            datetime(2026, 9, 23, 9, 27, 28),
        )

        self.assertEqual(donnees['date_soins_texte'], '2026/09/23 09:27:28')
        self.assertIn('2026/09/23 09:27:28', texte_du_pdf(generer_feuille_soins(donnees)))


class FeuilleSoinsPdfModeleTests(TestCase):
    """Pose des données sur le modèle PDF officiel (mode « overlay »)."""

    def setUp(self):
        # Le fichier modèle utilisé ici est une reproduction du formulaire : il
        # porte les mêmes libellés, ce qui permet de vérifier que les valeurs
        # d'origine sont remplacées et le reste du document conservé à l'identique.
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dossier, True)

        modele = Path(self.dossier) / 'feuille_de_soins_modele.pdf'
        modele.write_bytes(
            _generer_reproduction(
                donnees_de_test(
                    nni='0000000000',
                    inam='000000000000-Z',
                    photo=None,
                    nom='MODELE',
                    prenom='',
                )
            )
        )

        surcharge = override_settings(CNAM_FEUILLE_SOINS_MODELE=str(modele))
        surcharge.enable()
        self.addCleanup(surcharge.disable)

    def test_les_valeurs_du_modele_sont_remplacees(self):
        texte = texte_du_pdf(generer_feuille_soins(donnees_de_test()))

        self.assertIn('0124336042', texte)
        self.assertIn('180612797938-E', texte)
        self.assertNotIn('0000000000', texte)
        self.assertNotIn('000000000000-Z', texte)

    def test_le_reste_du_modele_est_conserve(self):
        texte = texte_du_pdf(generer_feuille_soins(donnees_de_test()))

        for libelle in (
            'Prescription de médecin',
            'Analyses, Examens et Radio',
            'Hospitalisation',
            'Signature et cachet du prescripteur(Obligatoire):',
        ):
            self.assertIn(libelle, texte)

    def _zone_photo(self, page):
        return pymupdf.Rect(
            PHOTO_BOITE[0] * page.rect.width,
            PHOTO_BOITE[1] * page.rect.height,
            PHOTO_BOITE[2] * page.rect.width,
            PHOTO_BOITE[3] * page.rect.height,
        )

    def _images_de_la_zone_photo(self, octets):
        document = pymupdf.open(stream=octets, filetype='pdf')
        try:
            page = document[0]
            zone = self._zone_photo(page)
            return [
                pymupdf.Rect(info['bbox'])
                for info in page.get_image_info()
                if pymupdf.Rect(info['bbox']).intersects(zone)
            ]
        finally:
            document.close()

    def test_la_photo_est_posee_dans_la_zone_du_modele(self):
        self.assertTrue(self._images_de_la_zone_photo(generer_feuille_soins(donnees_de_test())))

    def test_photo_absente_laisse_la_zone_du_modele_intacte(self):
        self.assertFalse(
            self._images_de_la_zone_photo(generer_feuille_soins(donnees_de_test(photo=None)))
        )

    def test_format_et_nombre_de_pages_du_modele_conserves(self):
        document = pymupdf.open(
            stream=generer_feuille_soins(donnees_de_test()), filetype='pdf'
        )
        try:
            self.assertEqual(document.page_count, 1)
            self.assertAlmostEqual(document[0].rect.width, 595.28, places=1)
            self.assertAlmostEqual(document[0].rect.height, 841.89, places=1)
        finally:
            document.close()


class FeuilleSoinsImageTests(TestCase):
    """Pose des données sur le modèle image PNG (fond de page)."""

    def setUp(self):
        # Image modèle = rendu 110 dpi d'une reproduction du formulaire, donc
        # mêmes libellés : les anciennes valeurs ne sont présentes que dans le
        # bitmap et disparaissent de l'extraction de texte une fois masquées.
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dossier, True)

        image = Path(self.dossier) / 'Feuille_text.png'
        document = pymupdf.open(
            stream=_generer_reproduction(
                donnees_de_test(
                    nni='0000000000',
                    inam='000000000000-Z',
                    photo=None,
                    nom='MODELE',
                    prenom='',
                )
            ),
            filetype='pdf',
        )
        try:
            document[0].get_pixmap(dpi=110).save(str(image))
        finally:
            document.close()

        surcharge = override_settings(
            CNAM_FEUILLE_SOINS_MODELE='',
            CNAM_FEUILLE_SOINS_MODELE_IMAGE=str(image),
        )
        surcharge.enable()
        self.addCleanup(surcharge.disable)

    def test_pdf_genere_avec_l_image_comme_fond(self):
        contenu = generer_feuille_soins(donnees_de_test())
        document = pymupdf.open(stream=contenu, filetype='pdf')
        try:
            self.assertTrue(contenu.startswith(b'%PDF-'))
            self.assertEqual(document.page_count, 1)
            self.assertGreaterEqual(len(document[0].get_images()), 1)
        finally:
            document.close()

    def test_les_valeurs_dynamiques_sont_posees_sur_l_image(self):
        donnees = donnees_de_test()
        texte = texte_du_pdf(generer_feuille_soins(donnees))

        for valeur in (
            'SidAhmed Ahmed Vali', '0124336042', '180612797938-E',
            '15/01/2002', donnees['date_soins_texte'],
        ):
            self.assertIn(valeur, texte)
        # Les anciennes valeurs du modèle ne subsistent que dans l'image.
        self.assertNotIn('MODELE', texte)
        self.assertNotIn('0000000000', texte)

    def test_sans_modele_image_la_reproduction_est_utilisee(self):
        surcharge = override_settings(CNAM_FEUILLE_SOINS_MODELE_IMAGE='')
        surcharge.enable()
        self.addCleanup(surcharge.disable)

        texte = texte_du_pdf(generer_feuille_soins(donnees_de_test()))
        self.assertIn('Prescription de médecin', texte)


class AssureApiTestCase(ApiTestCase):
    """Socle commun : un assuré enregistré et les URL de la feuille de soins."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.verifier_url = reverse('verifier_assure')
        cls.feuille_url = reverse('feuille_de_soins_pdf', args=['0124336042'])
        cls.photo_url = reverse('assure_photo', args=['0124336042'])

    def setUp(self):
        super().setUp()
        cache.clear()   # évite toute interférence de la limitation de débit
        self.assure = Assure.objects.create(
            nni='0124336042',
            inam='180612797938-E',
            numero_carte='CN-9948271',
            nom='SidAhmed',
            prenom='Ahmed Vali',
            sexe=Assure.SEXE_MASCULIN,
            date_naissance=date(2002, 1, 15),
            telephone='22 33 44 55',
            photo=photo_de_test(),
            photo_type='image/jpeg',
        )

    def test_la_verification_refuse_get(self):
        self.assertEqual(self.client.get(self.verifier_url).status_code, 405)


class VerifierAssureApiTests(AssureApiTestCase):
    """POST /api/assures/verifier/ : recherche par NNI ou par INAM."""

    def test_assure_trouve_par_nni(self):
        response = self.post_json(self.verifier_url, {'identifiant': '0124336042'})
        donnees = response.json()

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(donnees['trouve'])
        self.assertEqual(donnees['assure']['nom_complet'], 'SidAhmed Ahmed Vali')
        self.assertEqual(donnees['assure']['age'], self.assure.age)
        self.assertTrue(donnees['photo_disponible'])
        self.assertEqual(donnees['feuille_url'], self.feuille_url)
        self.assertEqual(donnees['photo_url'], self.photo_url)
        self.assertTrue(
            donnees['date_soins'].startswith(timezone.localtime().strftime('%Y/%m/%d'))
        )
        self.assertIn(self.assure.nni, donnees['qr_contenu'])

    def test_assure_trouve_par_inam(self):
        response = self.post_json(self.verifier_url, {'identifiant': ' 180612797938-e '})

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['trouve'])

    def test_assure_introuvable(self):
        response = self.post_json(self.verifier_url, {'identifiant': '9999999999'})
        donnees = response.json()

        self.assertEqual(response.status_code, 404)
        self.assertFalse(donnees['trouve'])
        self.assertIn('introuvable', donnees['error'].lower())

    def test_identifiant_obligatoire(self):
        response = self.post_json(self.verifier_url, {'identifiant': '   '})

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_corps_json_invalide(self):
        response = self.client.post(
            self.verifier_url, data='pas du json', content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_assure_sans_photo(self):
        Assure.objects.filter(pk=self.assure.pk).update(
            photo=None, photo_type='', photo_path=''
        )
        response = self.post_json(self.verifier_url, {'identifiant': '0124336042'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['photo_disponible'])


class FeuilleDeSoinsApiTests(AssureApiTestCase):
    """GET de la feuille de soins PDF et de la photo de l'assuré."""

    def test_telechargement_de_la_feuille_de_soins(self):
        response = self.client.get(self.feuille_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('feuille_de_soins_0124336042.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

        texte = texte_du_pdf(response.content)
        self.assertIn('SidAhmed Ahmed Vali', texte)
        self.assertIn('0124336042', texte)

    def test_feuille_de_soins_par_numero_inam(self):
        response = self.client.get(reverse('feuille_de_soins_pdf', args=['180612797938-E']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_feuille_de_soins_assure_inconnu(self):
        response = self.client.get(reverse('feuille_de_soins_pdf', args=['9999999999']))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['trouve'])

    def test_affichage_en_ligne_du_pdf(self):
        response = self.client.get(self.feuille_url, {'inline': '1'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('inline', response['Content-Disposition'])

    def test_photo_de_l_assure(self):
        response = self.client.get(self.photo_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertTrue(response.content.startswith(b'\xff\xd8'))

    def test_photo_absente(self):
        Assure.objects.filter(pk=self.assure.pk).update(photo=None, photo_path='')
        response = self.client.get(self.photo_url)

        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_photo_assure_inconnu(self):
        response = self.client.get(reverse('assure_photo', args=['9999999999']))

        self.assertEqual(response.status_code, 404)


# ===========================================================================
# ÉTABLISSEMENTS DE SANTÉ CONVENTIONNÉS (liste déroulante du formulaire)
# ===========================================================================
class EtablissementsApiTests(TestCase):
    """GET /api/etablissements/ : liste déroulante et recherche par nom."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('etablissements')
        # Noms absents de la liste initiale : les tests restent indépendants
        # du contenu réellement installé dans la base.
        cls.hopital = Etablissement.objects.create(
            nom="Hôpital Kassala",
            type_etablissement=Etablissement.TYPE_HOPITAL,
            ville="Nouakchott",
        )
        cls.centre = Etablissement.objects.create(
            nom="Centre de santé de Boghé",
            type_etablissement=Etablissement.TYPE_CENTRE_SANTE,
            ville="Boghé",
        )
        cls.ferme = Etablissement.objects.create(
            nom="Dispensaire de Rosso",
            type_etablissement=Etablissement.TYPE_DISPENSAIRE,
            conventionne=False,
        )

    def test_liste_complete_triee_par_nom(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        donnees = response.json()
        noms = [etablissement['nom'] for etablissement in donnees['etablissements']]

        self.assertEqual(noms, sorted(noms))
        self.assertIn("Hôpital Kassala", noms)
        self.assertIn("Centre de santé de Boghé", noms)
        self.assertEqual(
            donnees['total'], Etablissement.objects.filter(conventionne=True).count()
        )
        self.assertEqual(donnees['requete'], '')

    def test_etablissement_non_conventionne_exclu(self):
        noms = [
            etablissement['nom']
            for etablissement in self.client.get(self.url).json()['etablissements']
        ]

        self.assertNotIn("Dispensaire de Rosso", noms)

    def test_recherche_par_nom(self):
        response = self.client.get(self.url, {'q': 'kassala'})

        self.assertEqual(response.status_code, 200)
        etablissements = response.json()['etablissements']
        self.assertEqual(
            [etablissement['nom'] for etablissement in etablissements],
            ["Hôpital Kassala"],
        )

    def test_recherche_ignore_la_casse_et_les_accents(self):
        for requete in ('KASSALA', 'hopital', '  Kassala  '):
            with self.subTest(requete=requete):
                etablissements = self.client.get(
                    self.url, {'q': requete}
                ).json()['etablissements']
                self.assertIn(
                    "Hôpital Kassala",
                    [etablissement['nom'] for etablissement in etablissements],
                )

    def test_recherche_par_ville(self):
        reponse = self.client.get(self.url, {'q': 'Boghé'})

        self.assertEqual(
            [etablissement['nom'] for etablissement in
             reponse.json()['etablissements']],
            ["Centre de santé de Boghé"],
        )

    def test_recherche_sans_resultat(self):
        donnees = self.client.get(self.url, {'q': 'Timbuktu'}).json()

        self.assertEqual(donnees['etablissements'], [])
        self.assertEqual(donnees['total'], 0)

    def test_libelle_et_type_exposes(self):
        etablissement = self.client.get(
            self.url, {'q': 'Boghé'}
        ).json()['etablissements'][0]

        self.assertEqual(etablissement['id'], self.centre.pk)
        self.assertEqual(etablissement['nom'], "Centre de santé de Boghé")
        self.assertEqual(
            etablissement['libelle'], "Centre de santé de Boghé - Boghé"
        )
        self.assertEqual(etablissement['type'], "Centre de santé")
        self.assertEqual(etablissement['ville'], "Boghé")

    def test_libelle_avec_specialite_et_ville(self):
        centre = Etablissement.objects.create(
            nom="Centre de Cardiologie Essai",
            type_etablissement=Etablissement.TYPE_CENTRE_MEDICAL,
            specialite="Spécialités cardiovasculaires",
            ville="Nouakchott",
        )

        reponse = self.client.get(self.url, {'q': 'cardiologie'})

        self.assertEqual(reponse.status_code, 200)
        etablissements = reponse.json()['etablissements']
        trouve = next(e for e in etablissements if e['id'] == centre.pk)
        self.assertEqual(
            trouve['libelle'],
            "Centre de Cardiologie Essai - Spécialités cardiovasculaires (Nouakchott)",
        )
        self.assertEqual(trouve['type'], "Centre médical")
        # Le Centre National de Cardiologie de la liste officielle est présent aussi.
        self.assertIn(
            "Centre National de Cardiologie (CNC) - Spécialités cardiovasculaires (Nouakchott)",
            [e['libelle'] for e in etablissements],
        )


class EtablissementSelectionneTests(AssureApiTestCase):
    """L'établissement choisi est inscrit sur la Feuille de soins de l'assuré."""

    def setUp(self):
        super().setUp()
        self.hopital = Etablissement.objects.create(
            nom="Hôpital Kassala",
            type_etablissement=Etablissement.TYPE_HOPITAL,
            ville="Nouakchott",
        )
        self.centre = Etablissement.objects.create(
            nom="Centre de santé de Boghé",
            type_etablissement=Etablissement.TYPE_CENTRE_SANTE,
            ville="Boghé",
        )

    def test_etablissement_selectionne_est_associe(self):
        response = self.post_json(
            self.verifier_url,
            {'identifiant': '0124336042', 'etablissement': str(self.hopital.pk)},
        )

        self.assertEqual(response.status_code, 200)
        donnees = response.json()
        self.assertEqual(donnees['etablissement_selectionne'], self.hopital.libelle)
        self.assertEqual(donnees['centre_hospitalier'], self.hopital.libelle)

        self.assure.refresh_from_db()
        self.assertEqual(self.assure.centre_hospitalier, self.hopital.libelle)

    def test_etablissement_selectionne_est_imprime_dans_le_pdf(self):
        self.post_json(
            self.verifier_url,
            {'identifiant': '0124336042', 'etablissement': str(self.hopital.pk)},
        )

        reponse_pdf = self.client.get(self.feuille_url)

        self.assertEqual(reponse_pdf.status_code, 200)
        self.assertIn("Hôpital Kassala", texte_du_pdf(reponse_pdf.content))

    def test_selection_par_nom_ou_par_libelle(self):
        valeurs = (
            "Centre de santé de Boghé",
            "centre de sante de boghe",
            self.centre.libelle,
        )
        for valeur in valeurs:
            with self.subTest(valeur=valeur):
                response = self.post_json(
                    self.verifier_url,
                    {'identifiant': '0124336042', 'etablissement': valeur},
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json()['centre_hospitalier'], self.centre.libelle
                )

    def test_selection_par_numero_inam(self):
        response = self.post_json(
            self.verifier_url,
            {'identifiant': '180612797938-E', 'etablissement': str(self.centre.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['centre_hospitalier'], self.centre.libelle)

    def test_etablissement_inconnu_refuse(self):
        response = self.post_json(
            self.verifier_url,
            {'identifiant': '0124336042', 'etablissement': 'Hôpital inexistant'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('inconnu', response.json()['error'].lower())

        self.assure.refresh_from_db()
        self.assertEqual(self.assure.centre_hospitalier, '')

    def test_etablissement_non_conventionne_refuse(self):
        ferme = Etablissement.objects.create(
            nom="Dispensaire de Rosso", conventionne=False
        )
        response = self.post_json(
            self.verifier_url,
            {'identifiant': '0124336042', 'etablissement': str(ferme.pk)},
        )

        self.assertEqual(response.status_code, 400)

    def test_sans_selection_le_centre_en_base_est_conserve(self):
        Assure.objects.filter(pk=self.assure.pk).update(
            centre_hospitalier='Hôpital National'
        )

        response = self.post_json(self.verifier_url, {'identifiant': '0124336042'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['centre_hospitalier'], 'Hôpital National')
        self.assertEqual(response.json()['etablissement_selectionne'], '')

    def test_sans_selection_le_centre_par_defaut_est_utilise(self):
        response = self.post_json(self.verifier_url, {'identifiant': '0124336042'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['centre_hospitalier'], settings.CNAM_FEUILLE_SOINS_CENTRE
        )
        self.assertEqual(response.json()['etablissement_selectionne'], '')

    def test_une_nouvelle_selection_remplace_la_precedente(self):
        self.post_json(
            self.verifier_url,
            {'identifiant': '0124336042', 'etablissement': str(self.hopital.pk)},
        )
        response = self.post_json(
            self.verifier_url,
            {'identifiant': '0124336042', 'etablissement': str(self.centre.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['centre_hospitalier'], self.centre.libelle)

        self.assure.refresh_from_db()
        self.assertEqual(self.assure.centre_hospitalier, self.centre.libelle)


class EtablissementsMigrationTests(TestCase):
    """La liste officielle des hôpitaux est fournie à l'installation."""

    def test_liste_officielle_presente(self):
        noms = set(
            Etablissement.objects.filter(conventionne=True).values_list('nom', flat=True)
        )

        self.assertEqual(len(noms), 20)
        self.assertIn("Centre Hospitalier National (CHN)", noms)
        self.assertIn("Hôpital Cheikh Zayed (HCZ)", noms)
        self.assertIn("Centre National de Cardiologie (CNC)", noms)
        self.assertIn("Centre Hospitalier Régional d'Akjoujt", noms)

    def test_jeu_de_demarrage_remplace(self):
        noms = set(Etablissement.objects.values_list('nom', flat=True))

        self.assertNotIn("Hôpital Cheikh Zaid", noms)
        self.assertNotIn("Dispensaire de Mbewea", noms)

    def test_specialites_enregistrees(self):
        chn = Etablissement.objects.get(nom="Centre Hospitalier National (CHN)")

        self.assertEqual(chn.specialite, "Hôpital général")
        self.assertEqual(chn.ville, "Nouakchott")
        self.assertEqual(chn.libelle, "Centre Hospitalier National (CHN) - Hôpital général (Nouakchott)")
        self.assertEqual(chn.get_type_etablissement_display(), "Hôpital")







