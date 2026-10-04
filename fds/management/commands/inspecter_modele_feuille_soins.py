"""Affiche le texte et les coordonnées du modèle PDF de feuille de soins.

Sert à calibrer `fds/feuille_soins_layout.py` sur le fichier officiel :

    python manage.py inspecter_modele_feuille_soins
    python manage.py inspecter_modele_feuille_soins --chemin "C:/.../modele.pdf"
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Liste les textes du modèle PDF (ancres possibles pour la pose des données)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--chemin',
            default='',
            help="Chemin du PDF modèle (par défaut : CNAM_FEUILLE_SOINS_MODELE).",
        )

    def handle(self, *args, **options):
        chemin = options['chemin'] or getattr(settings, 'CNAM_FEUILLE_SOINS_MODELE', '')
        if not chemin or not os.path.isfile(chemin):
            raise CommandError(
                f"Modèle PDF introuvable : {chemin or '(chemin non défini)'}\n"
                "Déposez le fichier officiel ou utilisez --chemin."
            )

        try:
            import pymupdf
        except ImportError:  # pragma: no cover - anciennes versions
            import fitz as pymupdf

        document = pymupdf.open(chemin)
        try:
            self.stdout.write(f"Fichier : {chemin}")
            self.stdout.write(
                f"Pages   : {document.page_count}  "
                f"Format  : {document[0].rect.width:.1f} x {document[0].rect.height:.1f} pt"
            )

            page = document[0]
            for bloc in page.get_text('dict').get('blocks', []):
                for ligne in bloc.get('lines', []):
                    contenu = ''.join(span.get('text', '') for span in ligne.get('spans', []))
                    if not contenu.strip():
                        continue
                    boite = ligne['bbox']
                    self.stdout.write(
                        f"[{boite[0]:7.2f} {boite[1]:7.2f} {boite[2]:7.2f} {boite[3]:7.2f}] "
                        f"  {contenu.strip()}"
                    )
        finally:
            document.close()

        self.stdout.write(self.style.SUCCESS(
            "Reportez les libellés souhaités dans la clé « ancre » de "
            "fds/feuille_soins_layout.py (CHAMPS), et les zones "
            "photo/QR dans PHOTO_BOITE et QR_BOITE "
            "(fractions de la page : x0, y0, x1, y1 depuis le coin haut-gauche)."
        ))
