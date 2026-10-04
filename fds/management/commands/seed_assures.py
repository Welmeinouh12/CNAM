"""Crée des assurés de démonstration dans la base des assurés.

Utile pour tester la recherche NNI / INAM et la Feuille de soins sans
attendre le branchement de la base PostgreSQL :

    python manage.py seed_assures
    python manage.py seed_assures --reinitialiser
"""

import io
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from fds.models import Assure

ASSURES_DEMO = [
    {
        'nni': '0124336042',
        'inam': '180612797938-E',
        'numero_carte': 'CN-9948271',
        'numero_feuille': '',
        'nom': 'SidAhmed',
        'prenom': 'Ahmed Vali',
        'nom_ar': 'سيد أحمد',
        'prenom_ar': 'أحمد والي',
        'sexe': Assure.SEXE_MASCULIN,
        'date_naissance': date(2002, 1, 15),
        'lieu_naissance': 'Nouakchott',
        'telephone': '22 33 44 55',
        'centre_hospitalier': '',
        'couleur': (17, 66, 146),
    },
    {
        'nni': '1092837465',
        'inam': '150723482910-A',
        'numero_carte': 'CN-1122334',
        'numero_feuille': '',
        'nom': 'Ould Ahmed',
        'prenom': 'Mohamed Lemine',
        'nom_ar': 'أحمد',
        'prenom_ar': 'محمد لمين',
        'sexe': Assure.SEXE_MASCULIN,
        'date_naissance': date(1988, 6, 3),
        'lieu_naissance': 'Rosso',
        'telephone': '46 11 22 33',
        'centre_hospitalier': '',
        'couleur': (213, 24, 126),
    },
    {
        # Assurée sans photo en base : la zone photo du modèle doit rester vide.
        'nni': '7734512098',
        'inam': '170900123456-B',
        'numero_carte': '',
        'numero_feuille': '',
        'nom': 'Mint Salem',
        'prenom': 'Fatimetou',
        'nom_ar': 'سالم',
        'prenom_ar': 'فاطمة',
        'sexe': Assure.SEXE_FEMININ,
        'date_naissance': date(1995, 11, 27),
        'lieu_naissance': 'Kaédi',
        'telephone': '30 55 66 77',
        'centre_hospitalier': '',
        'couleur': (0, 164, 216),
        'sans_photo': True,
    },
]


def _photo_demo(initiales, couleur, largeur=413, hauteur=531):
    """Génère une image de profil (format 35x45 mm) pour les tests."""
    image = Image.new('RGB', (largeur, hauteur), (243, 246, 252))
    dessin = ImageDraw.Draw(image)
    dessin.rectangle([0, 0, largeur, int(hauteur * 0.34)], fill=couleur)
    dessin.ellipse(
        [largeur * 0.30, hauteur * 0.36, largeur * 0.70, hauteur * 0.76], fill=couleur
    )
    dessin.rectangle(
        [largeur * 0.22, hauteur * 0.74, largeur * 0.78, hauteur],
        fill=couleur,
    )
    dessin.text((largeur * 0.40, hauteur * 0.16), initiales, fill=(255, 255, 255))
    tampon = io.BytesIO()
    image.save(tampon, format='JPEG', quality=88)
    return tampon.getvalue()


class Command(BaseCommand):
    help = "Insère des assurés de démonstration (recherche NNI / INAM et PDF)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reinitialiser',
            action='store_true',
            help="Supprime les assurés de démonstration avant de les recréer.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reinitialiser']:
            nni_demo = [assure['nni'] for assure in ASSURES_DEMO]
            supprimes, _ = Assure.objects.filter(nni__in=nni_demo).delete()
            self.stdout.write(f"{supprimes} enregistrement(s) de démonstration supprimé(s).")

        for modele in ASSURES_DEMO:
            donnees = dict(modele)
            couleur = donnees.pop('couleur')
            sans_photo = donnees.pop('sans_photo', False)
            photo = None if sans_photo else _photo_demo(
                donnees['nom'][:2].upper(), couleur
            )

            assure, cree = Assure.objects.update_or_create(
                nni=donnees['nni'],
                defaults={
                    **{cle: valeur for cle, valeur in donnees.items() if cle != 'nni'},
                    'photo': photo,
                    'photo_type': 'image/jpeg' if photo else '',
                    'photo_nom': f"{donnees['nni']}.jpg" if photo else '',
                },
            )
            action = 'créé' if cree else 'mis à jour'
            self.stdout.write(
                f"Assuré {action} : {assure.nom_complet} - NNI {assure.nni} "
                f"(INAM {assure.inam or '—'})"
            )

        self.stdout.write(self.style.SUCCESS(
            f"{len(ASSURES_DEMO)} assurés de démonstration disponibles "
            f"(base : {timezone.now():%d/%m/%Y %H:%M})."
        ))
