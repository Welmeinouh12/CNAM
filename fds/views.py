"""Vues de l'application fds : pages et API de l'espace assuré CNAM."""

import json
import logging
import secrets

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from rest_framework.throttling import SimpleRateThrottle

from .models import EmailVerificationCode

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8


def login_view(request):
    return render(request, 'login.html')  # ou 'fds/login.html' selon l'emplacement de votre fichier


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def _read_json(request):
    """Retourne le corps JSON de la requête, ou None s'il est invalide."""
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _clean_email(value):
    return str(value or '').strip().lower()


def _email_error(email):
    """Retourne un message d'erreur si l'adresse e-mail est inutilisable."""
    if not email:
        return "L'adresse e-mail est obligatoire."
    try:
        validate_email(email)
    except ValidationError:
        return "Adresse e-mail invalide."
    return None


def _existing_user(email):
    """Recherche un compte déjà lié à cette adresse e-mail (nom d'utilisateur ou e-mail)."""
    User = get_user_model()
    return (
        User.objects.filter(username__iexact=email).first()
        or User.objects.filter(email__iexact=email).first()
    )


def _password_error(password, user):
    """Retourne un message d'erreur si le mot de passe est refusé, sinon None."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Le mot de passe doit comporter au moins {MIN_PASSWORD_LENGTH} caractères."
    try:
        validate_password(password, user)
    except ValidationError as exc:
        return ' '.join(exc.messages)
    return None


class _EmailThrottle(SimpleRateThrottle):
    """Base commune : limitation par adresse e-mail (IP en secours).

    Les débits sont définis dans REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
    """

    def get_cache_key(self, request, view):
        ident = getattr(request, 'cnam_throttle_ident', None) or self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class OtpSendThrottle(_EmailThrottle):
    scope = 'otp_send'


class RegisterThrottle(_EmailThrottle):
    scope = 'register'


class LoginThrottle(_EmailThrottle):
    scope = 'login'


def _throttled_response(request, ident, throttle_class=OtpSendThrottle):
    """Retourne une réponse 429 si la limite est atteinte, sinon None."""
    request.cnam_throttle_ident = ident
    throttle = throttle_class()
    if throttle.allow_request(request, view=None):
        return None
    wait = int(throttle.wait() or 0)
    return JsonResponse(
        {'error': f"Trop de tentatives. Réessayez dans {wait} seconde(s)."},
        status=429,
    )


# ---------------------------------------------------------------------------
# API d'inscription : envoi du code puis vérification
# ---------------------------------------------------------------------------
@require_POST
def otp_send_view(request):
    """Génère un code à 6 chiffres et l'envoie à l'adresse indiquée."""
    payload = _read_json(request)
    if payload is None:
        return JsonResponse(
            {'error': "Requête invalide : le corps de la requête doit être un objet JSON."},
            status=400,
        )

    email = _clean_email(payload.get('email'))
    error = _email_error(email)
    if error:
        return JsonResponse({'error': error}, status=400)

    throttled = _throttled_response(request, email)
    if throttled:
        return throttled

    if _existing_user(email):
        return JsonResponse(
            {'error': "Un compte existe déjà avec cette adresse e-mail. Connectez-vous."},
            status=409,
        )

    verification = EmailVerificationCode.issue(email)

    try:
        send_mail(
            subject="CNAM - Votre code de vérification",
            message=(
                "CAISSE NATIONALE D'ASSURANCE MALADIE\n"
                "Espace Assuré - Vérification de l'adresse e-mail\n\n"
                f"Votre code de vérification est : {verification.code}\n\n"
                f"Ce code est valable {EmailVerificationCode.VALIDITY_MINUTES} minutes.\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Envoi du code de vérification impossible pour %s", email)
        verification.delete()
        return JsonResponse(
            {'error': "L'envoi de l'e-mail a échoué. Vérifiez la configuration e-mail du serveur."},
            status=502,
        )

    return JsonResponse(
        {'message': f"Un code de vérification à 6 chiffres a été envoyé à {email}."}
    )



@require_POST
def otp_verify_view(request):
    """Vérifie le code reçu par e-mail puis crée le compte de l'assuré."""
    payload = _read_json(request)
    if payload is None:
        return JsonResponse(
            {'error': "Requête invalide : le corps de la requête doit être un objet JSON."},
            status=400,
        )

    email = _clean_email(payload.get('email'))
    code = str(payload.get('code') or '').strip()
    password = str(payload.get('password') or '')

    error = _email_error(email)
    if error:
        return JsonResponse({'error': error}, status=400)

    if not code.isdigit() or len(code) != EmailVerificationCode.CODE_LENGTH:
        return JsonResponse({'error': "Saisissez les 6 chiffres reçus par e-mail."}, status=400)

    verification = (
        EmailVerificationCode.objects
        .filter(email__iexact=email, consumed_at__isnull=True)
        .order_by('-created_at')
        .first()
    )

    if verification is None or verification.is_expired:
        return JsonResponse(
            {'error': "Aucun code valide pour cette adresse. Demandez un nouveau code."},
            status=400,
        )

    if not verification.is_usable:
        return JsonResponse(
            {'error': "Trop de tentatives invalides. Demandez un nouveau code."},
            status=400,
        )

    if not secrets.compare_digest(verification.code, code):
        verification.attempts += 1
        verification.save(update_fields=['attempts'])
        remaining = verification.remaining_attempts
        if remaining <= 0:
            return JsonResponse(
                {'error': "Trop de tentatives invalides. Demandez un nouveau code."},
                status=400,
            )
        return JsonResponse(
            {'error': f"Code incorrect. Il vous reste {remaining} tentative(s)."},
            status=400,
        )

    if _existing_user(email):
        verification.consume()
        return JsonResponse(
            {'error': "Un compte existe déjà avec cette adresse e-mail. Connectez-vous."},
            status=409,
        )

    User = get_user_model()
    user = User(username=email, email=email)

    error = _password_error(password, user)
    if error:
        return JsonResponse({'error': error}, status=400)

    user.set_password(password)
    user.save()

    verification.consume()

    return JsonResponse(
        {
            'message': "Votre compte CNAM a été créé avec succès. Vous pouvez vous connecter.",
            'email': user.email,
        }
    )


# ---------------------------------------------------------------------------
# API d'inscription / connexion directes (e-mail + mot de passe, sans OTP)
# ---------------------------------------------------------------------------
@require_POST
def register_view(request):
    """Crée un compte assuré à partir d'une adresse e-mail et d'un mot de passe."""
    payload = _read_json(request)
    if payload is None:
        return JsonResponse(
            {'error': "Requête invalide : le corps de la requête doit être un objet JSON."},
            status=400,
        )

    email = _clean_email(payload.get('email'))
    password = str(payload.get('password') or '')
    confirmation = str(payload.get('password_confirm') or password)

    error = _email_error(email)
    if error:
        return JsonResponse({'error': error}, status=400)

    throttled = _throttled_response(request, email, RegisterThrottle)
    if throttled:
        return throttled

    if password != confirmation:
        return JsonResponse({'error': "Les mots de passe ne correspondent pas."}, status=400)

    if _existing_user(email):
        return JsonResponse(
            {'error': "Un compte existe déjà avec cette adresse e-mail. Connectez-vous."},
            status=409,
        )

    User = get_user_model()
    user = User(username=email, email=email)

    error = _password_error(password, user)
    if error:
        return JsonResponse({'error': error}, status=400)

    user.set_password(password)
    user.save()

    # Connexion immédiate : l'assuré entre dans son espace, sans code OTP.
    login(request, user)

    return JsonResponse(
        {
            'message': "Votre compte CNAM a été créé avec succès. Bienvenue dans votre espace assuré.",
            'email': user.email,
        },
        status=201,
    )


@require_POST
def login_api_view(request):
    """Connecte l'assuré avec son adresse e-mail et son mot de passe."""
    payload = _read_json(request)
    if payload is None:
        return JsonResponse(
            {'error': "Requête invalide : le corps de la requête doit être un objet JSON."},
            status=400,
        )

    email = _clean_email(payload.get('email'))
    password = str(payload.get('password') or '')

    error = _email_error(email)
    if error:
        return JsonResponse({'error': error}, status=400)

    if not password:
        return JsonResponse({'error': "Le mot de passe est obligatoire."}, status=400)

    throttled = _throttled_response(request, email, LoginThrottle)
    if throttled:
        return throttled

    # Les comptes créés par l'espace assuré utilisent l'e-mail comme identifiant.
    user = authenticate(request, username=email, password=password)

    if user is None:
        # Repli : comptes dont le nom d'utilisateur diffère de l'adresse e-mail.
        existing = _existing_user(email)
        if existing is not None:
            user = authenticate(request, username=existing.get_username(), password=password)

    if user is None or not user.is_active:
        return JsonResponse({'error': "Adresse e-mail ou mot de passe incorrect."}, status=401)

    login(request, user)

    return JsonResponse(
        {
            'message': f"Bienvenue {user.email or user.get_username()}.",
            'email': user.email or user.get_username(),
        }
    )


@require_POST
def logout_api_view(request):
    """Ferme la session de l'assuré connecté."""
    logout(request)
    return JsonResponse({'message': "Vous avez été déconnecté."})

