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
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from rest_framework.throttling import SimpleRateThrottle

from .db_compat import valeur as _valeur
from .models import EmailVerificationCode
from .services import (
    associer_etablissement,
    donnees_feuille_soins,
    lister_etablissements,
    nom_fichier_feuille_soins,
    rechercher_assure,
)
from .services import _sexe_texte

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


class AssureVerifyThrottle(_EmailThrottle):
    """Limite les recherches d'assurés (par identifiant, IP en secours)."""

    scope = 'assure_verify'


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


# ---------------------------------------------------------------------------
# Feuille de soins : recherche de l'assuré (NNI / INAM) et PDF
# ---------------------------------------------------------------------------
def _resume_assure(assure):
    """Informations affichées par l'interface après une recherche réussie.

    Les colonnes absentes de la table (schéma PostgreSQL réduit) renvoient une
    chaîne vide : la fiche reste donc affichable au lieu d'une erreur 500.
    """
    naissance = _valeur(assure, 'date_naissance', None)
    return {
        'nni': _valeur(assure, 'nni'),
        'inam': _valeur(assure, 'inam'),
        'numero_carte': _valeur(assure, 'numero_carte'),
        'nom': _valeur(assure, 'nom'),
        'prenom': _valeur(assure, 'prenom'),
        'nom_complet': assure.nom_complet,
        'date_naissance': naissance.strftime('%d/%m/%Y') if naissance else '',
        'age': assure.age,
        'sexe': _sexe_texte(assure),
        'telephone': _valeur(assure, 'telephone'),
        'centre_hospitalier': _valeur(assure, 'centre_hospitalier'),
    }


@require_GET
def etablissements_view(request):
    """Liste des établissements de santé conventionnés (liste déroulante).

    Le paramètre `q` filtre la liste par nom (et par ville) : c'est la
    recherche saisie dans le formulaire. Sans paramètre, la liste complète est
    renvoyée pour alimenter la liste déroulante.
    """
    requete = request.GET.get('q', '') or request.GET.get('recherche', '')
    etablissements = lister_etablissements(requete)

    return JsonResponse(
        {
            'etablissements': etablissements,
            'total': len(etablissements),
            'requete': str(requete).strip(),
        }
    )


@require_POST
def verifier_assure_view(request):
    """Recherche un assuré par NNI ou INAM dans PostgreSQL.

    Retourne ses informations et l'URL de téléchargement de sa Feuille de soins
    (générée à la demande avec la date et l'heure courantes).
    """
    payload = _read_json(request)
    if payload is None:
        return JsonResponse(
            {'error': "Requête invalide : le corps de la requête doit être un objet JSON."},
            status=400,
        )

    identifiant = str(
        payload.get('identifiant') or payload.get('nni') or payload.get('inam') or ''
    ).strip()

    if not identifiant:
        return JsonResponse(
            {'trouve': False, 'error': "Saisissez un NNI ou un numéro d'assuré INAM."},
            status=400,
        )

    throttled = _throttled_response(request, identifiant, AssureVerifyThrottle)
    if throttled:
        return throttled

    assure = rechercher_assure(identifiant)
    if assure is None:
        return JsonResponse(
            {
                'trouve': False,
                'error': (
                    "Assuré introuvable : aucun assuré ne correspond au numéro "
                    f"« {identifiant} ». Vérifiez le NNI ou le numéro INAM saisi."
                ),
            },
            status=404,
        )

    # L'établissement choisi est enregistré sur la fiche de l'assuré : il est
    # ainsi repris automatiquement sur la Feuille de soins.
    try:
        etablissement = associer_etablissement(assure, payload.get('etablissement'))
    except ValueError as exc:
        return JsonResponse(
            {'trouve': False, 'error': str(exc)},
            status=400,
        )

    donnees = donnees_feuille_soins(assure, timezone.localtime())

    return JsonResponse(
        {
            'trouve': True,
            'message': f"Assuré trouvé : {assure.nom_complet}.",
            'centre_hospitalier': donnees['centre_hospitalier'],
            'etablissement_selectionne': (
                etablissement.libelle if etablissement is not None else ''
            ),
            'assure': _resume_assure(assure),
            'date_soins': donnees['date_soins_texte'],
            'numero_feuille': donnees['numero_feuille'],
            'photo_disponible': bool(donnees['photo']),
            'photo_url': reverse('assure_photo', args=[assure.nni]),
            'qr_contenu': donnees['qr_contenu'],
            'feuille_url': reverse('feuille_de_soins_pdf', args=[assure.nni]),
            'feuille_nom': nom_fichier_feuille_soins(assure),
        }
    )


@require_GET
def assure_photo_view(request, nni):
    """Renvoie la photo de profil de l'assuré (404 si aucune photo en base)."""
    assure = rechercher_assure(nni)
    octets = assure.photo_binaire() if assure is not None else None
    if not octets:
        return JsonResponse(
            {'error': "Aucune photo enregistrée pour cet assuré."}, status=404
        )

    type_photo = _valeur(assure, 'photo_type', '') or 'image/jpeg'
    reponse = HttpResponse(octets, content_type=type_photo)
    reponse['Cache-Control'] = 'private, max-age=300'
    return reponse


@require_GET
def feuille_de_soins_pdf_view(request, nni):
    """Génère et renvoie la Feuille de soins PDF d'un assuré (NNI ou INAM)."""
    assure = rechercher_assure(nni)
    if assure is None:
        return JsonResponse(
            {'trouve': False, 'error': "Assuré introuvable : feuille de soins non générée."},
            status=404,
        )

    donnees = donnees_feuille_soins(assure, timezone.localtime())

    # Import paresseux : si une dépendance PDF manque, seul cet endpoint est
    # concerné (le reste du portail continue de fonctionner).
    try:
        from .feuille_soins_pdf import generer_feuille_soins
    except ImportError:
        logger.exception("Dépendances de génération PDF manquantes.")
        return JsonResponse(
            {
                'error': (
                    "Génération de la feuille de soins indisponible : installez "
                    "les dépendances (pip install -r requirements.txt)."
                )
            },
            status=500,
        )

    try:
        contenu = generer_feuille_soins(donnees)
    except Exception:
        logger.exception("Génération de la feuille de soins impossible (NNI=%s).", nni)
        return JsonResponse(
            {'error': "La génération de la feuille de soins a échoué. Réessayez dans un instant."},
            status=500,
        )

    disposition = 'inline' if request.GET.get('inline') else 'attachment'
    reponse = HttpResponse(contenu, content_type='application/pdf')
    reponse['Content-Disposition'] = (
        f'{disposition}; filename="{nom_fichier_feuille_soins(assure)}"'
    )
    reponse['Cache-Control'] = 'no-store'
    return reponse


