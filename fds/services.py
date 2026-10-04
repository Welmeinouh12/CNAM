"""Recherche des assurés et préparation des données de la Feuille de soins.

Ce module ne contient que la logique métier : le rendu du PDF se trouve dans
`fds.feuille_soins_pdf`.
"""

import re
import unicodedata

from django.conf import settings
from django.db.models import Q, Value
from django.db.models.functions import Replace
from django.utils import timezone

from .db_compat import champs_disponibles as _colonnes_disponibles
from .db_compat import queryset as _queryset_compatible
from .db_compat import valeur as _valeur

from .models import Assure, Etablissement

# Identifiant trop court pour être un NNI (10 chiffres) ou un INAM.
LONGUEUR_MINIMALE_IDENTIFIANT = 4

# Un NNI complet comporte 10 chiffres et commence par un 0.
LONGUEUR_NNI = 10


class _ModeleTolerant(dict):
    """Dictionnaire de formatage qui ignore les champs manquants."""

    def __missing__(self, cle):
        return ''


def normaliser_identifiant(valeur):
    """Met l'identifiant saisi sous une forme comparable (majuscules, sans espaces)."""
    return re.sub(r'\s+', '', str(valeur or '')).upper()


def _derniers_chiffres(valeur, taille):
    """Retourne les `taille` derniers chiffres d'une chaîne (zéros si vide)."""
    chiffres = re.sub(r'\D', '', valeur or '')
    if not chiffres:
        return '0' * taille
    return chiffres[-taille:].zfill(taille)


def variantes_identifiant(cle):
    """Renvoie les formes comparables d'un identifiant saisi.

    Le NNI comporte 10 chiffres et commence par un 0 : ce zéro initial est
    facilement perdu (copier-coller depuis un tableur, saisie dans un champ
    numérique, lecture d'une étiquette). La variante complétée par des zéros
    est donc testée, comme la forme sans tirets.
    """
    variantes = [cle]

    if cle.isdigit() and len(cle) < LONGUEUR_NNI:
        variantes.append(cle.zfill(LONGUEUR_NNI))

    sans_tirets = cle.replace('-', '')
    if sans_tirets and sans_tirets not in variantes:
        variantes.append(sans_tirets)

    if sans_tirets.isdigit() and len(sans_tirets) < LONGUEUR_NNI:
        variantes.append(sans_tirets.zfill(LONGUEUR_NNI))

    return list(dict.fromkeys(v for v in variantes if v))


def rechercher_assure(identifiant):
    """Recherche l'assuré correspondant au NNI **ou** au numéro INAM.

    Retourne un `Assure` ou `None`. La comparaison ignore la casse et les
    espaces ; un second passage ignore en plus les tirets présents en base
    (ex. « 1806127 97938 - E » saisi face à « 180612797938-E » stocké) ainsi
    que le zéro initial d'un NNI saisi sans celui-ci.

    Les colonnes absentes de la table PostgreSQL (table `assure` créée à la
    main dans pgAdmin) sont différées par `db_compat` : la recherche aboutit
    donc même si le schéma ne contient que quelques colonnes.
    """
    cle = normaliser_identifiant(identifiant)
    if len(cle) < LONGUEUR_MINIMALE_IDENTIFIANT:
        return None

    variantes = variantes_identifiant(cle)

    assure = _queryset_compatible(Assure).filter(
        Q(nni__in=variantes) | Q(inam__in=variantes)
    ).first()
    if assure is not None:
        return assure

    # Repli : la base peut contenir des espaces ou des tirets dans les numéros.
    return (
        _queryset_compatible(Assure)
        .annotate(
            _nni_cle=Replace(
                Replace('nni', Value(' '), Value('')), Value('-'), Value('')
            ),
            _inam_cle=Replace(
                Replace('inam', Value(' '), Value('')), Value('-'), Value('')
            ),
        )
        .filter(
            Q(_nni_cle__in=variantes) | Q(_inam_cle__in=variantes)
        )
        .first()
    )


def _sexe_texte(assure):
    """Libellé du sexe (« Masculin » / « Féminin »), ou chaîne vide.

    La colonne `sexe` peut manquer dans une table PostgreSQL réduite : le
    genre n'est alors simplement pas imprimé sur la feuille de soins.
    """
    code = _valeur(assure, 'sexe', '')
    return assure.get_sexe_display() if code else ''


def numero_feuille_soins(assure, date_soins=None):
    """Numéro imprimé en haut de la feuille de soins.

    Celui enregistré dans PostgreSQL est prioritaire ; sinon il est construit
    avec le modèle `CNAM_FEUILLE_SOINS_NUMERO` (ex. « 336042/2026/PH33604 »).
    """
    numero = (_valeur(assure, 'numero_feuille', '') or '').strip()
    if numero:
        return numero

    date_soins = date_soins or timezone.localtime()
    modele = getattr(
        settings, 'CNAM_FEUILLE_SOINS_NUMERO', '{serie}/{annee}/PH{serie_courte}'
    )
    valeurs = _ModeleTolerant(
        nni=_derniers_chiffres(_valeur(assure, 'nni'), 10),
        inam=_valeur(assure, 'inam'),
        annee=f'{date_soins.year:04d}',
        mois=f'{date_soins.month:02d}',
        jour=f'{date_soins.day:02d}',
        serie=_derniers_chiffres(assure.nni, 6),
        serie_courte=_derniers_chiffres(assure.nni, 5),
    )
    try:
        return modele.format_map(valeurs)
    except (KeyError, ValueError, IndexError):
        return f'{_derniers_chiffres(assure.nni, 6)}/{date_soins.year:04d}'


def contenu_qr(assure, date_soins=None, numero_feuille=''):
    """Charge utile du code QR (code scanné) apposé sur la feuille de soins.

    Le contenu stocké dans PostgreSQL (`code_qr`) est prioritaire ; sinon le
    code est généré avec le modèle `CNAM_QR_CONTENU` à partir de l'assuré.
    """
    contenu = (_valeur(assure, 'code_qr', '') or '').strip()
    if contenu:
        return contenu

    date_soins = date_soins or timezone.localtime()
    modele = getattr(settings, 'CNAM_QR_CONTENU', '{nni}|{inam}|{nom}|{prenom}')
    nni = _valeur(assure, 'nni')
    inam = _valeur(assure, 'inam')
    naissance = _valeur(assure, 'date_naissance', None)
    age = assure.age
    valeurs = _ModeleTolerant(
        nni=nni,
        inam=inam,
        nom=_valeur(assure, 'nom'),
        prenom=_valeur(assure, 'prenom'),
        nom_complet=assure.nom_complet,
        nom_complet_ar=assure.nom_complet_ar,
        date_naissance=naissance.isoformat() if naissance else '',
        age='' if age is None else str(age),
        sexe=_valeur(assure, 'sexe'),
        numero_carte=_valeur(assure, 'numero_carte'),
        numero_feuille=numero_feuille,
        date_soins=date_soins.strftime('%Y/%m/%d %H:%M:%S'),
        date_soins_iso=date_soins.strftime('%Y-%m-%dT%H:%M:%S'),
    )
    try:
        return modele.format_map(valeurs)
    except (KeyError, ValueError, IndexError):
        return f'{nni}|{inam}'


def donnees_feuille_soins(assure, date_soins=None):
    """Rassemble les données dynamiques imprimées sur la feuille de soins.

    La date de soins est générée automatiquement ici (date et heure courantes)
    si elle n'est pas fournie par l'appelant.
    """
    date_soins = date_soins or timezone.localtime()
    numero = numero_feuille_soins(assure, date_soins)
    naissance = _valeur(assure, 'date_naissance', None)
    age = assure.age

    return {
        'assure': assure,
        'date_soins': date_soins,
        'date_soins_texte': date_soins.strftime('%Y/%m/%d %H:%M:%S'),
        'numero_feuille': numero,
        'centre_hospitalier': (
            (_valeur(assure, 'centre_hospitalier', '') or '').strip()
            or getattr(settings, 'CNAM_FEUILLE_SOINS_CENTRE', '')
        ),
        'nni': _valeur(assure, 'nni'),
        'inam': _valeur(assure, 'inam'),
        'numero_carte': _valeur(assure, 'numero_carte'),
        'nom_complet': assure.nom_complet,
        'nom_complet_ar': assure.nom_complet_ar,
        'date_naissance_texte': naissance.strftime('%d/%m/%Y') if naissance else '',
        'age': age,
        'age_texte': '' if age is None else f'{age} ans',
        'sexe_texte': _sexe_texte(assure),
        'telephone': _valeur(assure, 'telephone'),
        'photo': assure.photo_binaire(),
        'qr_contenu': contenu_qr(assure, date_soins, numero),
    }


def nom_fichier_feuille_soins(assure):
    """Nom du fichier proposé au téléchargement."""
    reference = re.sub(r'[^A-Za-z0-9_-]', '', _valeur(assure, 'nni')) or 'assure'
    return f'feuille_de_soins_{reference}.pdf'


# ---------------------------------------------------------------------------
# Établissements de santé conventionnés (liste déroulante du formulaire)
# ---------------------------------------------------------------------------
def normaliser_etablissement(valeur):
    """Met un nom d'établissement sous une forme comparable.

    Accents, casse, tirets et espaces multiples sont ignorés : « Hôpital
    Cheikh Zaid » et « hopital  cheikh-zaid » désignent le même
    établissement.
    """
    texte = unicodedata.normalize('NFKD', str(valeur or ''))
    sans_accent = ''.join(
        caractere for caractere in texte if not unicodedata.combining(caractere)
    )
    return re.sub(r'[^a-z0-9]+', ' ', sans_accent.lower()).strip()


def lister_etablissements(requete=''):
    """Établissements conventionnés proposés dans la liste déroulante.

    Seuls les établissements conventionnés sont retournés, triés par nom. Le
    filtre porte sur le nom et la ville (recherche par nom insensible à la
    casse et aux accents) : c'est lui qui alimente le champ de recherche du
    formulaire. Sans recherche, la liste complète est renvoyée.
    """
    requete = str(requete or '').strip()
    queryset = Etablissement.objects.filter(conventionne=True).order_by('nom', 'ville')

    if not requete:
        etablissements = list(queryset)
    else:
        etablissements = list(
            queryset.filter(Q(nom__icontains=requete) | Q(ville__icontains=requete))
        )
        if not etablissements:
            # Repli : la comparaison SQL est sensible aux accents, « hopital »
            # ne trouve donc pas « Hôpital ». On réessaie sans accent ni casse.
            cible = normaliser_etablissement(requete)
            if cible:
                etablissements = [
                    etablissement
                    for etablissement in queryset
                    if cible in normaliser_etablissement(etablissement.nom)
                    or cible in normaliser_etablissement(etablissement.ville)
                ]

    return [
        {
            'id': etablissement.pk,
            'nom': etablissement.nom,
            'type': etablissement.get_type_etablissement_display(),
            'specialite': etablissement.specialite,
            'ville': etablissement.ville,
            'libelle': etablissement.libelle,
        }
        for etablissement in etablissements
    ]


def rechercher_etablissement(valeur):
    """Retrouve un établissement conventionné à partir de ce qu'envoie le formulaire.

    `valeur` est soit l'identifiant de l'établissement (option value de la
    liste déroulante), soit son nom ou son libellé complet. Les accents, la
    casse, les tirets et les espaces sont ignorés. Retourne None si rien ne
    correspond.
    """
    valeur = str(valeur or '').strip()
    if not valeur:
        return None

    if valeur.isdigit():
        etablissement = Etablissement.objects.filter(
            pk=int(valeur), conventionne=True
        ).first()
        if etablissement is not None:
            return etablissement

    cible = normaliser_etablissement(valeur)
    if not cible:
        return None

    for etablissement in Etablissement.objects.filter(conventionne=True):
        if cible in (
            normaliser_etablissement(etablissement.nom),
            normaliser_etablissement(etablissement.libelle),
        ):
            return etablissement
    return None


def associer_etablissement(assure, valeur):
    """Rattache l'établissement choisi à l'assuré (donc à sa Feuille de soins).

    L'enregistrement est fait une seule fois sur la colonne
    `centre_hospitalier`, déjà imprimée par `donnees_feuille_soins` : la mise
    en page du PDF reste donc strictement inchangée. Retourne l'établissement
    retenu, ou None si aucun établissement n'a été choisi (champ laissé vide).

    La colonne `centre_hospitalier` peut manquer d'une table PostgreSQL
    réduite : l'établissement choisi est alors simplement non enregistré,
    la Feuille de soins reprenant la valeur par défaut du projet.
    """
    valeur = str(valeur or '').strip()
    if not valeur:
        return None

    etablissement = rechercher_etablissement(valeur)
    if etablissement is None:
        raise ValueError(
            f"Établissement de santé inconnu : « {valeur} ». "
            "Choisissez un établissement dans la liste déroulante."
        )

    if 'centre_hospitalier' in _colonnes_disponibles(Assure):
        actuel = (_valeur(assure, 'centre_hospitalier', '') or '').strip()
        if actuel != etablissement.libelle:
            assure.centre_hospitalier = etablissement.libelle
            assure.save(update_fields=['centre_hospitalier'])

    return etablissement

