from django.db import migrations

# Liste officielle des établissements de santé conventionnés avec la CNAM.
# Format : (nom, type, spécialité / activités, ville).
# Le nom reste seul dans la base : la recherche porte sur lui, pas sur les
# compléments, qui ne servent qu'à l'affichage (liste déroulante et PDF).
ETABLISSEMENTS_OFFICIELS = [
    ("Centre Hospitalier National (CHN)", "HOPITAL",
     "Hôpital général", "Nouakchott"),
    ("Hôpital Cheikh Zayed (HCZ)", "HOPITAL",
     "Hôpital général et urgences", "Nouakchott"),
    ("Hôpital Militaire de Nouakchott (HMN)", "HOPITAL",
     "Soins généraux, chirurgie et urgences", "Nouakchott"),
    ("Hôpital de l'Amitié", "HOPITAL",
     "Hôpital général", "Nouakchott"),
    ("Centre Hospitalier de la Mère et de l'Enfant (CHME)", "CENTRE_MEDICAL",
     "Pédiatrie, gynécologie et obstétrique", "Nouakchott"),
    ("Centre National de Cardiologie (CNC)", "CENTRE_MEDICAL",
     "Spécialités cardiovasculaires", "Nouakchott"),
    ("Centre National d'Oncologie (CNO)", "CENTRE_MEDICAL",
     "Traitement du cancer et radiothérapie", "Nouakchott"),
    ("Centre Hospitalier Spécialisé (CHS / Dia)", "CENTRE_MEDICAL",
     "Neuro-psychiatrie et santé mentale", "Nouakchott"),
    ("Centre Hospitalier Régional de Nouadhibou", "HOPITAL",
     "Hôpital général", "Nouadhibou"),
    ("Centre Hospitalier Régional de Kiffa", "HOPITAL",
     "Hôpital général", "Kiffa"),
    ("Centre Hospitalier Régional de Rosso", "HOPITAL",
     "Hôpital général", "Rosso"),
    ("Centre Hospitalier Régional de Kaédi", "HOPITAL",
     "Hôpital général", "Kaédi"),
    ("Centre Hospitalier Régional de Néma", "HOPITAL",
     "Hôpital général", "Néma"),
    ("Centre Hospitalier Régional d'Aïoun", "HOPITAL",
     "Hôpital général", "Aïoun"),
    ("Centre Hospitalier Régional d'Aleg", "HOPITAL",
     "Hôpital général", "Aleg"),
    ("Centre Hospitalier Régional d'Atar", "HOPITAL",
     "Hôpital général", "Atar"),
    ("Centre Hospitalier Régional de Tidjikja", "HOPITAL",
     "Hôpital général", "Tidjikja"),
    ("Centre Hospitalier Régional de Sélibaby", "HOPITAL",
     "Hôpital général", "Sélibaby"),
    ("Centre Hospitalier Régional de Zouerate", "HOPITAL",
     "Hôpital général", "Zouerate"),
    ("Centre Hospitalier Régional d'Akjoujt", "HOPITAL",
     "Hôpital général", "Akjoujt"),
]

# Établissements du jeu de départ (migration 0004), remplacés par la liste
# officielle ci-dessus. Seuls ces noms-là sont retirés : les établissements
# éventuellement ajoutés depuis dans l'administration sont conservés.
ETABLISSEMENTS_PROVISOIRES = [
    "Hôpital National", "Hôpital Cheikh Zaid", "Hôpital Saint-François",
    "Hôpital de Rosso", "Hôpital de Kaédi", "Hôpital de Zouérate",
    "Hôpital de Kiffa", "Hôpital de Néma", "Hôpital d'Akkouch",
    "Hôpital de Sélibaby", "Hôpital de Boutilimit", "Hôpital d'Aleg",
    "Hôpital de Nouadhibou", "Clinique El Bassar", "Clinique La Guérache",
    "Centre médical de Tevragh-Zaouria", "Centre de santé de Saba",
    "Centre de santé de Médina", "Centre de santé de Tichitt",
    "Centre de santé de Chinguetti", "Centre de santé d'Atar",
    "Centre de santé de Néma", "Centre de santé de Zouérate",
    "Dispensaire de Nouadhibou", "Dispensaire de Tekane",
    "Dispensaire de Mbewea",
]


def installer_liste_officielle(apps, schema_editor):
    """Remplace le jeu de départ par la liste officielle des hôpitaux."""
    Etablissement = apps.get_model('fds', 'Etablissement')

    noms_officiels = [ligne[0] for ligne in ETABLISSEMENTS_OFFICIELS]
    Etablissement.objects.filter(
        nom__in=ETABLISSEMENTS_PROVISOIRES
    ).exclude(nom__in=noms_officiels).delete()

    for nom, type_etablissement, specialite, ville in ETABLISSEMENTS_OFFICIELS:
        Etablissement.objects.update_or_create(
            nom=nom,
            defaults={
                'type_etablissement': type_etablissement,
                'specialite': specialite,
                'ville': ville,
                'conventionne': True,
            },
        )


class Migration(migrations.Migration):
    """Liste officielle des hôpitaux et centres de santé conventionnés CNAM.

    Idempotente (update_or_create par nom). L'annulation ne supprime rien :
    la liste reste consultable telle quelle, ce qui évite toute perte.
    """

    dependencies = [
        ('fds', '0005_etablissement_specialite'),
    ]

    operations = [
        migrations.RunPython(installer_liste_officielle, migrations.RunPython.noop),
    ]
