"""Diagnostic de la connexion à la base et de la table des assurés.

Affiche le moteur réellement utilisé, la table visée, la liste des colonnes
présentes en base, les colonnes attendues par le modèle mais absentes, puis
optionnellement teste la recherche d'un NNI ou d'un INAM.

Usage::

    python manage.py verifier_base
    python manage.py verifier_base 0124330042
    python manage.py verifier_base 180612797938-E
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from fds import db_compat
from fds.models import Assure
from fds.services import rechercher_assure


class Command(BaseCommand):
    help = "Affiche la base utilisée, le schéma réel de la table des assurés et teste une recherche."

    def add_arguments(self, parser):
        parser.add_argument(
            'identifiant',
            nargs='?',
            default='',
            help="NNI ou numéro INAM à rechercher (facultatif).",
        )

    def handle(self, *args, **options):
        identifiant = (options.get('identifiant') or '').strip()

        self.stdout.write(self.style.MIGRATE_HEADING('Base de données'))
        config = settings.DATABASES['default']
        self.stdout.write(f'  Moteur      : {config["ENGINE"]}')
        self.stdout.write(f'  Base        : {config.get("NAME")}')
        self.stdout.write(f'  Hôte        : {config.get("HOST") or "(local)"}')
        self.stdout.write(f'  Port        : {config.get("PORT") or "(défaut)"}')
        self.stdout.write(f'  Utilisateur : {config.get("USER") or "(défaut)"}')

        moteur = config['ENGINE']
        if 'sqlite' in moteur:
            self.stdout.write(
                self.style.WARNING(
                    '  ATTENTION : le projet fonctionne sur SQLite. Les données '
                    'insérées dans PostgreSQL via pgAdmin ne sont PAS visibles.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "  Pour lire PostgreSQL : renseignez CNAM_DB_ENGINE, "
                    "CNAM_DB_NAME, CNAM_DB_USER et CNAM_DB_PASSWORD (voir .env.example)."
                )
            )
        else:
            try:
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS('  Connexion PostgreSQL établie.'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'  Connexion impossible : {exc}'))
                return

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Table des assurés'))
        self.stdout.write(f'  Table attendue : {Assure._meta.db_table}')

        info = db_compat._decrire(Assure)
        if not info['existe']:
            message = f'  Table introuvable en base : {Assure._meta.db_table}'
            if info['erreur']:
                message += f' ({info["erreur"]})'
            self.stdout.write(self.style.ERROR(message))
            return

        reelles = sorted(info['colonnes'])
        self.stdout.write(f'  Colonnes présentes ({len(reelles)}) : {", ".join(reelles)}')
        self.stdout.write(f'  Clé primaire : {info["pk"] or "(aucune)"}')

        attendues = {champ.column for champ in Assure._meta.concrete_fields}
        manquantes = sorted(attendues - set(reelles))
        if manquantes:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    f'  Colonnes du modèle absentes de la table ({len(manquantes)}) : '
                    f'{", ".join(manquantes)}'
                )
            )
            self.stdout.write(
                '  Elles sont ignorées automatiquement (aucune migration n\'est requise),'
            )
            self.stdout.write(
                '  mais les informations correspondantes resteront vides.'
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('  Le schéma de la table est complet.')
            )

        try:
            total = db_compat.queryset(Assure).count()
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'  Lecture impossible : {exc}'))
            return

        self.stdout.write('')
        self.stdout.write(f'  Nombre d\'assurés lisibles : {total}')

        if identifiant:
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(f'Recherche « {identifiant} »'))
            assure = rechercher_assure(identifiant)
            if assure is None:
                self.stdout.write(
                    self.style.ERROR('  INTROUVABLE dans la base actuellement utilisée.')
                )
                self.stdout.write(
                    '  Vérifiez que le numéro saisi correspond bien aux données de '
                    f'{Assure._meta.db_table}, et non à une autre base.'
                )
            else:
                self.stdout.write(self.style.SUCCESS('  Trouvé :'))
                self.stdout.write(f'    NNI            : {db_compat.valeur(assure, "nni")}')
                self.stdout.write(f'    INAM           : {db_compat.valeur(assure, "inam")}')
                self.stdout.write(f'    Nom            : {assure.nom_complet}')
                self.stdout.write(f'    Naissance      : {db_compat.valeur(assure, "date_naissance", "")}')
                photo = assure.photo_binaire()
                self.stdout.write(
                    f'    Photo          : {len(photo)} octets' if photo else '    Photo          : aucune'
                )
