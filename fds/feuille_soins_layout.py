"""Plan de pose des données dynamiques sur le modèle PDF officiel.

RÈGLE : le PDF modèle n'est jamais redessiné. On ouvre le fichier original
(`settings.CNAM_FEUILLE_SOINS_MODELE`), on masque uniquement la valeur
d'origine d'un champ puis on écrit la valeur issue de PostgreSQL à sa place.

Deux modes de pose, par champ :

* ``ancre``   : court texte présent dans le PDF modèle (ex. « Nom de l'assuré »).
  Le moteur localise la ligne de texte qui contient cette ancre, puis place la
  valeur dans la partie droite de cette ligne (fractions ``depart``/``fin`` de
  la largeur de la ligne).
* ``boite``   : rectangle explicite, exprimé en fractions de la page
  (x0, y0, x1, y1) mesurées depuis le coin supérieur gauche. Indispensable pour
  la photo et le code QR, qui n'ont pas d'ancre textuelle.

Pour calibrer sur VOTRE fichier modèle, lancer :

    python manage.py inspecter_modele_feuille_soins

La commande affiche chaque ligne de texte du PDF avec ses coordonnées : il
suffit alors d'ajuster les ancres (ou les boîtes) ci-dessous.
"""

# ---------------------------------------------------------------------------
# Gabarits de valeurs : {…} reprend les clés de `services.donnees_feuille_soins`
# ---------------------------------------------------------------------------

#: Champs texte posés sur le modèle. L'ordre n'a pas d'importance.
#:
#: * ``depart`` : ``'apres_ancre'`` (la valeur d'origine se trouve juste après
#:   le libellé recherché) ou une fraction de la largeur de la ligne (``0.0``
#:   pour réécrire toute la ligne).
#: * ``fin`` : fraction de largeur de ligne où s'arrête le remplacement.
#: * ``jusqu_a`` : ancre facultative devant laquelle le remplacement s'arrête
#:   (ex. la date de naissance s'arrête avant le libellé « Age »).
CHAMPS = [
    {
        # « Feuille de Soins - 124826/2025/PH13096 » : toute la ligne est réécrite.
        'cle': 'numero_feuille',
        'ancre': 'Feuille de Soins',
        'gabarit': 'Feuille de Soins - {numero_feuille}',
        'depart': 0.0,
        'fin': 1.0,
        'align': 'center',
        'gras': True,
        'taille': 6.8,
    },
    {
        # « Centre Hospitalier National (ex CardioLogie (CNC)) »
        'cle': 'centre_hospitalier',
        'ancre': 'Centre Hospitalier',
        'gabarit': '{centre_hospitalier}',
        'depart': 0.0,
        'fin': 1.0,
        'align': 'center',
        'gras': False,
        'taille': 6.0,
    },
    {
        # « Nom de l'assuré : SidAhmed Ahmed Vali »
        'cle': 'nom_complet',
        'ancre': "Nom de l'assuré",
        'gabarit': '{nom_complet}',
        'depart': 'apres_ancre',
        'fin': 1.0,
        'align': 'left',
        'gras': False,
        'taille': 7.5,
    },
    {
        # « Identifiant National d'Assurance Maladie : 180612797938-E »
        'cle': 'inam',
        'ancre': "Identifiant National d'Assurance Maladie",
        'gabarit': '{inam}',
        'depart': 'apres_ancre',
        'fin': 1.0,
        'align': 'left',
        'gras': False,
        'taille': 7.5,
    },
    {
        # « Numéro National d'Identification : 0124336042 »
        'cle': 'nni',
        'ancre': "Numéro National d'Identification",
        'gabarit': '{nni}',
        'depart': 'apres_ancre',
        'fin': 1.0,
        'align': 'left',
        'gras': False,
        'taille': 7.5,
    },
    {
        # « Date de Naissance : 15/01/2002 » (s'arrête avant le libellé « Age »)
        'cle': 'date_naissance',
        'ancre': 'Date de Naissance',
        'gabarit': '{date_naissance_texte}',
        'depart': 'apres_ancre',
        'fin': 1.0,
        'jusqu_a': 'Age',
        'align': 'left',
        'gras': False,
        'taille': 7.5,
    },
    {
        # « Age : 24 ans »
        'cle': 'age',
        'ancre': 'Age',
        'gabarit': '{age_texte}',
        'depart': 'apres_ancre',
        'fin': 1.0,
        'align': 'left',
        'gras': False,
        'taille': 7.5,
    },
    {
        # « Date des soins : 2026/09/23 09:27:28 » (date et heure du jour)
        'cle': 'date_soins',
        'ancre': 'Date des soins',
        'gabarit': '{date_soins_texte}',
        'depart': 'apres_ancre',
        'fin': 1.0,
        'align': 'left',
        'gras': False,
        'taille': 7.5,
    },
]

#: Photo de profil de l'assuré (fractions de la page). Si l'assuré n'a pas de
#: photo, la zone du modèle est laissée intacte.
PHOTO_BOITE = (0.8013, 0.1414, 0.9630, 0.2483)

#: Code QR / code scanné (fractions de la page).
QR_BOITE = (0.8000, 0.2840, 0.8840, 0.3450)

#: Libellé imprimé sous le code QR (None pour ne rien imprimer).
QR_LIBELLE = 'SCAN ME'

#: Dimensions en points de la page A4 utilisée pour exprimer les fractions.
PAGE_LARGEUR_PT = 595.2756
PAGE_HAUTEUR_PT = 841.8898
