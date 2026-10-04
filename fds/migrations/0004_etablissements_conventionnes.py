from django.db import migrations

# Liste officielle des établissements de santé conventionnés avec la CNAM.
#
# Ces lignes ne sont qu'un jeu de départ : la liste affichée par le formulaire
# est celle de la table `etablissements`, modifiable ensuite à volonté dans
# l'administration Django (/admin/fds/etablissement/) ou en base. L'opération
# est idempotente (get_or_create sur le nom) et n'efface rien au retour.
ETABLISSEMENTS_CONVENTIONNES = [
    ("Hôpital National", "HOPITAL", "Nouakchott", "Av. Mokhtar Ould Daddah", ""),
    ("Hôpital Cheikh Zaid", "HOPITAL", "Nouakchott", "Tevragh-Zaouria", ""),
    ("Hôpital Saint-François", "HOPITAL", "Nouakchott", "Ksar", ""),
    ("Hôpital de Rosso", "HOPITAL", "Rosso", "", ""),
    ("Hôpital de Kaédi", "HOPITAL", "Kaédi", "", ""),
    ("Hôpital de Zouérate", "HOPITAL", "Zouérate", "", ""),
    ("Hôpital de Kiffa", "HOPITAL", "Kiffa", "", ""),
    ("Hôpital de Néma", "HOPITAL", "Néma", "", ""),
    ("Hôpital d'Akkouch", "HOPITAL", "Akkouch", "", ""),
    ("Hôpital de Sélibaby", "HOPITAL", "Sélibaby", "", ""),
    ("Hôpital de Boutilimit", "HOPITAL", "Boutilimit", "", ""),
    ("Hôpital d'Aleg", "HOPITAL", "Aleg", "", ""),
    ("Hôpital de Nouadhibou", "HOPITAL", "Nouadhibou", "", ""),
    ("Clinique El Bassar", "CLINIQUE", "Nouakchott", "", ""),
    ("Clinique La Guérache", "CLINIQUE", "Nouakchott", "", ""),
    ("Centre médical de Tevragh-Zaouria", "CENTRE_MEDICAL", "Nouakchott", "", ""),
    ("Centre de santé de Saba", "CENTRE_SANTE", "Nouakchott", "", ""),
    ("Centre de santé de Médina", "CENTRE_SANTE", "Nouakchott", "", ""),
    ("Centre de santé de Tichitt", "CENTRE_SANTE", "Tichitt", "", ""),
    ("Centre de santé de Chinguetti", "CENTRE_SANTE", "Chinguetti", "", ""),
    ("Centre de santé d'Atar", "CENTRE_SANTE", "Atar", "", ""),
    ("Centre de santé de Néma", "CENTRE_SANTE", "Néma", "", ""),
    ("Centre de santé de Zouérate", "CENTRE_SANTE", "Zouérate", "", ""),
    ("Dispensaire de Nouadhibou", "DISPENSAIRE", "Nouadhibou", "", ""),
    ("Dispensaire de Tekane", "DISPENSAIRE", "Amed Guidance", "", ""),
    ("Dispensaire de Mbewea", "DISPENSAIRE", "Nouakchott", "", ""),
]


def creer_etablissements(apps, schema_editor):
    """Remplit la table des établissements conventionnés (sans doublon)."""
    Etablissement = apps.get_model('fds', 'Etablissement')

    for nom, type_etablissement, ville, adresse, telephone in ETABLISSEMENTS_CONVENTIONNES:
        Etablissement.objects.get_or_create(
            nom=nom,
            defaults={
                'type_etablissement': type_etablissement,
                'ville': ville,
                'adresse': adresse,
                'telephone': telephone,
                'conventionne': True,
            },
        )


def supprimer_etablissements(apps, schema_editor):
    """Annule la migration sans toucher aux établissements ajoutés ensuite."""
    Etablissement = apps.get_model('fds', 'Etablissement')

    noms = [ligne[0] for ligne in ETABLISSEMENTS_CONVENTIONNES]
    Etablissement.objects.filter(nom__in=noms).delete()


class Migration(migrations.Migration):
    """Table des établissements de santé conventionnés + liste initiale."""

    dependencies = [
        ('fds', '0003_etablissement'),
    ]

    operations = [
        migrations.RunPython(creer_etablissements, supprimer_etablissements),
    ]
