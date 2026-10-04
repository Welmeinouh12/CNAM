import os
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .db_compat import valeur as _valeur


class EmailVerificationCode(models.Model):
    """Code de vérification (OTP) envoyé par e-mail pendant l'inscription.

    Un seul code reste actif par adresse e-mail : l'émission d'un nouveau code
    invalide automatiquement les précédents.
    """

    CODE_LENGTH = 6
    VALIDITY_MINUTES = 10
    MAX_ATTEMPTS = 5

    email = models.EmailField("Adresse e-mail")
    code = models.CharField("Code", max_length=CODE_LENGTH)
    attempts = models.PositiveSmallIntegerField("Tentatives", default=0)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    expires_at = models.DateTimeField("Expire le")
    consumed_at = models.DateTimeField("Consommé le", null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = "Code de vérification e-mail"
        verbose_name_plural = "Codes de vérification e-mail"

    def __str__(self):
        return f"{self.email} - {self.code}"

    @classmethod
    def generate_code(cls):
        """Génère un code numérique aléatoire cryptographiquement sûr."""
        return ''.join(secrets.choice('0123456789') for _ in range(cls.CODE_LENGTH))

    @classmethod
    def issue(cls, email):
        """Invalide les codes en attente puis émet un nouveau code pour `email`."""
        cls.objects.filter(email__iexact=email, consumed_at__isnull=True).update(
            consumed_at=timezone.now()
        )
        return cls.objects.create(
            email=email,
            code=cls.generate_code(),
            expires_at=timezone.now() + timedelta(minutes=cls.VALIDITY_MINUTES),
        )

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_usable(self):
        return (
            self.consumed_at is None
            and not self.is_expired
            and self.attempts < self.MAX_ATTEMPTS
        )

    @property
    def remaining_attempts(self):
        return max(self.MAX_ATTEMPTS - self.attempts, 0)

    def consume(self):
        self.consumed_at = timezone.now()
        self.save(update_fields=['consumed_at'])


class Assure(models.Model):
    """Assuré CNAM tel qu'il est enregistré dans PostgreSQL.

    La recherche se fait par NNI ou par numéro d'assuré INAM (voir
    `fds.services.rechercher_assure`) puis alimente la Feuille de soins PDF.

    La table existe déjà dans PostgreSQL : son nom se règle avec la variable
    d'environnement `CNAM_ASSURES_TABLE` (défaut : « assures ») et chaque
    colonne peut être renommée via `db_column` si votre schéma diffère.
    """

    SEXE_MASCULIN = 'M'
    SEXE_FEMININ = 'F'
    SEXE_CHOICES = [
        (SEXE_MASCULIN, "Masculin"),
        (SEXE_FEMININ, "Féminin"),
    ]

    # --- Identification ---------------------------------------------------
    nni = models.CharField(
        "Numéro National d'Identification (NNI)",
        max_length=32,
        unique=True,
        db_index=True,
    )
    inam = models.CharField(
        "Numéro d'Assuré INAM", max_length=32, blank=True, default='', db_index=True
    )
    numero_carte = models.CharField(
        "N° de carte d'assuré", max_length=32, blank=True, default=''
    )
    numero_feuille = models.CharField(
        "N° de feuille de soins", max_length=64, blank=True, default=''
    )

    # --- État civil -------------------------------------------------------
    nom = models.CharField("Nom de famille", max_length=100)
    prenom = models.CharField("Prénom", max_length=100, blank=True, default='')
    nom_ar = models.CharField("Nom (arabe)", max_length=100, blank=True, default='')
    prenom_ar = models.CharField("Prénom (arabe)", max_length=100, blank=True, default='')
    sexe = models.CharField(
        "Sexe", max_length=1, choices=SEXE_CHOICES, blank=True, default=''
    )
    date_naissance = models.DateField("Date de naissance", null=True, blank=True)
    lieu_naissance = models.CharField(
        "Lieu de naissance", max_length=100, blank=True, default=''
    )
    telephone = models.CharField(
        "Téléphone portable", max_length=32, blank=True, default=''
    )

    # --- Établissement prescripteur --------------------------------------
    centre_hospitalier = models.CharField(
        "Centre hospitalier", max_length=160, blank=True, default=''
    )

    # --- Photo de profil --------------------------------------------------
    # `photo` contient le binaire (colonne PostgreSQL de type bytea).
    photo = models.BinaryField("Photo (bytea)", null=True, blank=True)
    photo_type = models.CharField(
        "Type MIME de la photo", max_length=64, blank=True, default=''
    )
    photo_nom = models.CharField(
        "Nom du fichier photo", max_length=160, blank=True, default=''
    )
    # Variante : la photo est stockée sur le disque et la base ne contient que
    # le chemin du fichier (relatif à CNAM_PHOTO_ROOT ou chemin absolu).
    photo_path = models.CharField(
        "Chemin de la photo", max_length=255, blank=True, default=''
    )

    # --- Code scanné / QR -------------------------------------------------
    code_qr = models.TextField(
        "Contenu du code QR",
        blank=True,
        default='',
        help_text="Laisser vide pour générer automatiquement le code à partir de l'assuré.",
    )

    class Meta:
        db_table = getattr(settings, 'CNAM_ASSURES_TABLE', 'assures')
        verbose_name = "Assuré"
        verbose_name_plural = "Assurés"
        ordering = ('nom', 'prenom', 'nni')

    def __str__(self):
        return f"{self.nom_complet} ({self.nni})"

    # ------------------------------------------------------------------
    # Propriétés métier
    # ------------------------------------------------------------------
    @property
    def nom_complet(self):
        """Nom et prénom de l'assuré, sous la forme utilisée sur le PDF.

        Les colonnes absentes de la table (schéma PostgreSQL réduit) sont
        simplement ignorées : le nom seul est alors renvoyé.
        """
        return ' '.join(
            part for part in (_valeur(self, 'nom'), _valeur(self, 'prenom')) if part
        ).strip()

    @property
    def nom_complet_ar(self):
        return ' '.join(
            part
            for part in (_valeur(self, 'nom_ar'), _valeur(self, 'prenom_ar'))
            if part
        ).strip()

    @property
    def age(self):
        """Âge révolu en années, calculé le jour de l'édition de la feuille."""
        date_naissance = _valeur(self, 'date_naissance', None)
        if not date_naissance:
            return None
        today = timezone.localdate()
        annees = today.year - date_naissance.year
        anniversaire_passe = (today.month, today.day) >= (
            date_naissance.month,
            date_naissance.day,
        )
        return annees if anniversaire_passe else annees - 1

    def photo_binaire(self):
        """Retourne les octets de la photo, ou None si l'assuré n'en a pas.

        Gère les deux modes de stockage possibles dans PostgreSQL : le binaire
        (colonne bytea) et le chemin de fichier sur le disque.
        """
        binaire = _valeur(self, 'photo', None)
        if binaire:
            return bytes(binaire)

        chemin = (_valeur(self, 'photo_path', '') or '').strip()
        if not chemin:
            return None

        if not os.path.isabs(chemin):
            chemin = os.path.join(settings.CNAM_PHOTO_ROOT, chemin)

        try:
            with open(chemin, 'rb') as fichier:
                return fichier.read()
        except OSError:
            return None


class Etablissement(models.Model):
    """Établissement de santé conventionné avec la CNAM.

    Ces lignes alimentent la liste déroulante « Hôpital / Centre de santé » du
    formulaire de vérification. L'établissement choisi par l'assuré est
    enregistré sur sa fiche (`Assure.centre_hospitalier`) : il est alors
    imprimé automatiquement sur la Feuille de soins, sans toucher au
    formulaire ni à sa mise en page.

    Le contenu de la table est modifiable dans l'administration Django
    (`/admin/fds/etablissement/`) : la liste n'est donc pas figée dans le code.
    """

    TYPE_HOPITAL = 'HOPITAL'
    TYPE_CLINIQUE = 'CLINIQUE'
    TYPE_CENTRE_SANTE = 'CENTRE_SANTE'
    TYPE_CENTRE_MEDICAL = 'CENTRE_MEDICAL'
    TYPE_DISPENSAIRE = 'DISPENSAIRE'
    TYPE_CHOICES = [
        (TYPE_HOPITAL, "Hôpital"),
        (TYPE_CLINIQUE, "Clinique"),
        (TYPE_CENTRE_SANTE, "Centre de santé"),
        (TYPE_CENTRE_MEDICAL, "Centre médical"),
        (TYPE_DISPENSAIRE, "Dispensaire"),
    ]

    nom = models.CharField("Nom de l'établissement", max_length=160, unique=True)
    type_etablissement = models.CharField(
        "Type d'établissement",
        max_length=32,
        choices=TYPE_CHOICES,
        default=TYPE_CENTRE_SANTE,
    )
    specialite = models.CharField(
        "Spécialités / activités",
        max_length=160,
        blank=True,
        default='',
        help_text="Texte affiché après le nom, ex : « Hôpital général et urgences ».",
    )
    ville = models.CharField("Ville", max_length=100, blank=True, default='')
    adresse = models.CharField("Adresse", max_length=200, blank=True, default='')
    telephone = models.CharField("Téléphone", max_length=32, blank=True, default='')
    conventionne = models.BooleanField("Conventionné CNAM", default=True)

    class Meta:
        db_table = 'etablissements'
        verbose_name = "Établissement de santé"
        verbose_name_plural = "Établissements de santé"
        ordering = ('nom', 'ville')

    def __str__(self):
        return self.libelle

    @property
    def libelle(self):
        """Libellé de la liste déroulante, également imprimé sur le PDF.

        Rendu attendu : « Centre Hospitalier National (CHN) - Hôpital général
        (Nouakchott) ». Le tiret simple est voluntarily utilisé plutôt que le
        tiret cadratin, plus sûr avec les polices du PDF. Le nom reste seul
        dans la base : les compléments n'affectent donc pas la recherche.
        """
        if self.specialite and self.ville:
            return f'{self.nom} - {self.specialite} ({self.ville})'
        if self.specialite:
            return f'{self.nom} - {self.specialite}'
        if self.ville:
            return f'{self.nom} - {self.ville}'
        return self.nom

