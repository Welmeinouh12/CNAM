"""Importe un assuré dans la base réellement utilisée par le projet.

Ce module sert de passerelle entre pgAdmin et le portail : un assuré inséré
dans PostgreSQL peut être recréé dans la base du projet (SQLite) à partir des
mêmes informations, photo comprise.

Il ne modifie que la base configurée : aucune donnée n'est écrite dans
PostgreSQL.

Usage::

    python manage.py importer_assure --nni 0124330042 --inam 180612797938-E ^
        --nom "Sid'Ahmed Ahmed Vall" --naissance 2002-01-15 --photo C:\\temp\\sd.png

Les options `--prenom`, `--sexe`, `--telephone` et `--centre` sont facultatives.
Sans `--photo`, l'assuré est importé sans image.
"""

import mimetypes
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from fds.models import Assure


class Command(BaseCommand):
    help = "Importe un assuré (avec sa photo) dans la base utilisée par le projet."

    def add_arguments(self, parser):
        parser.add_argument('--nni', required=True, help='Numéro NNI (10 chiffres).')
        parser.add_argument('--inam', default='', help="Numéro d'assuré INAM.")
        parser.add_argument('--nom', required=True, help='Nom de famille.')
        parser.add_argument('--prenom', default='', help='Prénom.')
        parser.add_argument(
            '--naissance', default='', help='Date de naissance (AAAA-MM-JJ).'
        )
        parser.add_argument('--sexe', default='', choices=['', 'M', 'F'], help='M ou F.')
        parser.add_argument('--telephone', default='', help='Téléphone portable.')
        parser.add_argument(
            '--centre', default='', help='Centre hospitalier / établissement.'
        )
        parser.add_argument('--photo', default='', help="Chemin d'un fichier image.")

    def handle(self, *args, **options):
        nni = (options['nni'] or '').strip()

        naissance = None
        if options['naissance']:
            try:
                naissance = datetime.strptime(
                    options['naissance'].strip(), '%Y-%m-%d'
                ).date()
            except ValueError as exc:
                raise CommandError(
                    'Date de naissance invalide (AAAA-MM-JJ attendu) : '
                    f"{options['naissance']} ({exc})"
                )

        photo, photo_type = self._lire_photo(options['photo'])

        valeurs = {
            'inam': (options['inam'] or '').strip(),
            'nom': (options['nom'] or '').strip(),
            'prenom': (options['prenom'] or '').strip(),
            'sexe': options['sexe'] or '',
            'date_naissance': naissance,
            'telephone': (options['telephone'] or '').strip(),
            'centre_hospitalier': (options['centre'] or '').strip(),
        }
        if photo is not None:
            valeurs['photo'] = photo
            valeurs['photo_type'] = photo_type

        assure, cree = Assure.objects.update_or_create(nni=nni, defaults=valeurs)

        action = 'importé' if cree else 'mis à jour'
        self.stdout.write(
            self.style.SUCCESS(
                f'Assuré {action} : {assure.nom_complet} (NNI {assure.nni})'
            )
        )
        if photo is not None:
            self.stdout.write(f'  Photo : {len(photo)} octets ({photo_type})')
        else:
            self.stdout.write('  Photo : aucune')

    def _lire_photo(self, chemin):
        """Retourne (octets, type MIME) pour un fichier image, ou (None, '')."""
        chemin = (chemin or '').strip()
        if not chemin:
            return None, ''

        fichier = Path(chemin)
        if not fichier.is_file():
            raise CommandError(f'Fichier photo introuvable : {fichier}')

        donnees = fichier.read_bytes()
        type_mime = mimetypes.guess_type(fichier.name)[0] or 'image/jpeg'
        return donnees, type_mime
