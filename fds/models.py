import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


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
