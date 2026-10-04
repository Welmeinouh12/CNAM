"""Génération de la Feuille de soins PDF.

Deux stratégies, dans cet ordre :

1. **Pose sur le modèle officiel** (mode normal). Le PDF fourni est ouvert tel
   quel et seules les données dynamiques de PostgreSQL sont écrites par-dessus,
   à l'emplacement prévu par `fds.feuille_soins_layout`. La structure, les
   tableaux, les logos, la mise en page et les dimensions du modèle sont donc
   conservés à l'identique.
2. **Pose sur le modèle image** (`settings.CNAM_FEUILLE_SOINS_MODELE_IMAGE`).
   L'image PNG de la feuille (format A4, 910 x 1287 px) sert de fond de page :
   seules les zones dynamiques (numéro, centre, identité, date des soins,
   photo, code QR) sont masquées — filets préservés — puis réécrites
   par-dessus, à la géométrie mesurée sur l'image.
3. **Reproduction fidèle du modèle** (repli automatique, utilisé tant qu'aucun
   modèle n'est déposé dans le projet). Elle reprend le même formulaire :
   en-tête, blocs « Feuille de Soins », « Prescription de
   médecin », « Analyses, Examens et Radio », « Hospitalisation », photo et
   code QR à la même place.

Le point d'entrée unique est `generer_feuille_soins(donnees)` qui retourne les
octets du PDF.
"""

import io
import logging
import os

from django.conf import settings

import qrcode
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from PIL import Image, UnidentifiedImageError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import Paragraph, Table, TableStyle

from . import feuille_soins_layout as layout

try:  # PyMuPDF >= 1.24
    import pymupdf
except ImportError:  # pragma: no cover - anciennes versions
    import fitz as pymupdf

logger = logging.getLogger(__name__)

# Polices système contenant les glyphes arabes (présentation contextuelle).
POLICES_ARABE_CANDIDATES = (
    r'C:\Windows\Fonts\arial.ttf',
    r'C:\Windows\Fonts\tahoma.ttf',
    r'C:\Windows\Fonts\segoeui.ttf',
    r'C:\Windows\Fonts\times.ttf',
    '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
    '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
    '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/Library/Fonts/Arial.ttf',
)

NOM_POLICE_ARABE = 'CnamArabic'
_LATIN = 'Helvetica'
_LATIN_GRAS = 'Helvetica-Bold'

_cache_police = {'chemin': None, 'cherche': False, 'reportlab': False}
_cache_logo = {}

# Le logo source est réduit à cette hauteur (points images) avant intégration.
_HAUTEUR_MAX_LOGO = 240


class _Donnees(dict):
    """Accès tolérant aux données de la feuille (clé absente → chaîne vide)."""

    def __missing__(self, cle):
        return ''


# ---------------------------------------------------------------------------
# Polices et texte arabe
# ---------------------------------------------------------------------------
def chemin_police_arabe():
    """Retourne le chemin d'une police gérant l'arabe, ou None."""
    if _cache_police['cherche']:
        return _cache_police['chemin']

    _cache_police['cherche'] = True
    candidates = [p for p in (getattr(settings, 'CNAM_FEUILLE_SOINS_FONT', ''),)
                  + POLICES_ARABE_CANDIDATES if p]

    for chemin in candidates:
        if not os.path.isfile(chemin):
            continue
        try:
            if pymupdf.Font(fontfile=chemin).has_glyph(ord('ا')):
                _cache_police['chemin'] = chemin
                break
        except Exception:  # pragma: no cover - police illisible
            logger.warning("Police arabe illisible, ignorée : %s", chemin)

    if _cache_police['chemin'] is None:
        logger.warning(
            "Aucune police arabe trouvée : les libellés arabes sont omis du PDF. "
            "Renseignez CNAM_FEUILLE_SOINS_FONT avec un fichier .ttf arabe."
        )
    return _cache_police['chemin']


def police_arabe_reportlab():
    """Enregistre la police arabe auprès de ReportLab (nom de police ou None)."""
    chemin = chemin_police_arabe()
    if not chemin:
        return None
    if not _cache_police['reportlab']:
        pdfmetrics.registerFont(TTFont(NOM_POLICE_ARABE, chemin))
        _cache_police['reportlab'] = True
    return NOM_POLICE_ARABE


def est_arabe(texte):
    """Vrai si le texte contient au moins un caractère arabe."""
    return any('\u0600' <= caractere <= '\u06ff' for caractere in str(texte or ''))


def texte_arabe(texte):
    """Met le texte arabe en forme pour un rendu de gauche à droite."""
    return get_display(reshape(str(texte or '')))


def _libelle_arabe(texte):
    """Libellé arabe prêt à imprimer, ou None si aucune police n'est disponible."""
    if not texte:
        return None
    return texte_arabe(texte) if chemin_police_arabe() else None


# ---------------------------------------------------------------------------
# Images : code QR, photo de l'assuré, logo
# ---------------------------------------------------------------------------
def code_qr_png(contenu, taille_module=10):
    """Génère le code QR (PNG) du contenu fourni."""
    generateur = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=taille_module,
        border=1,
    )
    generateur.add_data(str(contenu or ''))
    generateur.make(fit=True)
    tampon = io.BytesIO()
    generateur.make_image(fill_color='black', back_color='white').save(tampon, format='PNG')
    return tampon.getvalue()


def _dimensions_image(octets):
    """Retourne (largeur, hauteur) d'une image, ou None si illisible."""
    try:
        with Image.open(io.BytesIO(octets)) as image:
            return image.size
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _lecteur_logo():
    """Lecteur du logo d'en-tête (réduit à la taille utile), sinon None.

    Le fichier source peut être très grand : il est redimensionné une fois pour
    éviter d'alourdir inutilement la feuille de soins générée.
    """
    if 'octets' in _cache_logo:
        octets = _cache_logo['octets']
        return ImageReader(io.BytesIO(octets)) if octets else None

    chemin = getattr(settings, 'CNAM_FEUILLE_SOINS_LOGO', '')
    octets = None
    if chemin and os.path.isfile(chemin):
        try:
            with Image.open(chemin) as image:
                image = image.convert('RGBA')
                if image.height > _HAUTEUR_MAX_LOGO:
                    largeur = max(1, round(image.width * _HAUTEUR_MAX_LOGO / image.height))
                    image = image.resize((largeur, _HAUTEUR_MAX_LOGO), Image.LANCZOS)
                tampon = io.BytesIO()
                image.save(tampon, format='PNG', optimize=True)
                octets = tampon.getvalue()
        except (UnidentifiedImageError, OSError, ValueError):
            logger.warning("Logo d'en-tête illisible : %s", chemin)

    _cache_logo['octets'] = octets
    return ImageReader(io.BytesIO(octets)) if octets else None


# ---------------------------------------------------------------------------
# 1) Pose des données dynamiques sur le PDF modèle officiel
# ---------------------------------------------------------------------------
def _rect_fraction(page, fractions):
    """Convertit une boîte en fractions de page en rectangle PyMuPDF."""
    x0, y0, x1, y1 = fractions
    return pymupdf.Rect(
        page.rect.x0 + x0 * page.rect.width,
        page.rect.y0 + y0 * page.rect.height,
        page.rect.x0 + x1 * page.rect.width,
        page.rect.y0 + y1 * page.rect.height,
    )


def _ligne_de_texte(page, rect_ancre):
    """Retourne (boîte, origine) de la ligne de texte contenant l'ancre.

    La boîte couvre toute la ligne (donc la valeur d'origine juste après le
    libellé) et l'origine donne la ligne de base exacte du modèle, ce qui
    permet d'écrire la nouvelle valeur parfaitement alignée.
    """
    for bloc in page.get_text('dict').get('blocks', []):
        for ligne in bloc.get('lines', []):
            for span in ligne.get('spans', []):
                if pymupdf.Rect(span['bbox']).intersects(rect_ancre):
                    return pymupdf.Rect(ligne['bbox']), span.get('origin')
    return rect_ancre, None


def _largeur_texte(valeur, police, taille):
    try:
        return pymupdf.get_text_length(valeur, fontname=police, fontsize=taille)
    except Exception:  # pragma: no cover - police non mesurable
        return 0.0


def _etendue_de_ligne(page, ligne, rect_ancre):
    """Étend la ligne à toute la rangée du modèle.

    Selon la façon dont le modèle a été généré, la valeur peut se trouver sur
    la même ligne de texte que le libellé (un seul bloc) ou dans une cellule
    voisine (bloc séparé). On réunit donc tous les textes situés sur la même
    hauteur et à droite de l'ancre.
    """
    etendue = pymupdf.Rect(ligne)
    tolerance = max(ligne.height, 6.0) * 0.6
    centre = (ligne.y0 + ligne.y1) / 2

    for bloc in page.get_text('dict').get('blocks', []):
        for voisine in bloc.get('lines', []):
            boite = pymupdf.Rect(voisine['bbox'])
            if abs((boite.y0 + boite.y1) / 2 - centre) > tolerance:
                continue
            if boite.x1 <= rect_ancre.x1:
                continue
            etendue |= boite

    return etendue


def _zone_de_pose(page, champ, ligne, rect_ancre):
    """Zone où la valeur dynamique est écrite (et l'ancienne supprimée)."""
    depart = champ.get('depart', 'apres_ancre')

    if isinstance(depart, str):
        etendue = _etendue_de_ligne(page, ligne, rect_ancre)
        gauche = rect_ancre.x1 + 2.0 if depart == 'apres_ancre' else ligne.x0
        base_droite = etendue.x1
    else:
        gauche = ligne.x0 + float(depart) * ligne.width
        base_droite = ligne.x0 + ligne.width

    droite = gauche + float(champ.get('fin', 1.0)) * (base_droite - gauche)

    # Borne facultative : le remplacement s'arrête avant une autre ancre
    # (ex. « Date de Naissance » s'arrête avant « Age »).
    limite = champ.get('jusqu_a')
    if limite:
        butoirs = page.search_for(limite)
        if butoirs:
            droite = min(droite, butoirs[0].x0 - 2.0)

    return pymupdf.Rect(gauche, ligne.y0, max(droite, gauche), ligne.y1)


def _preparer_champs(page, donnees):
    """Phase 1 : localise les champs et retire les valeurs d'origine du modèle.

    Retourne la liste des champs prêts à être écrits. La suppression est une
    vraie suppression du texte (et non un masque blanc) : l'ancienne valeur
    disparaît aussi du calque texte du PDF.
    """
    a_poser = []

    for champ in layout.CHAMPS:
        valeur = str(champ.get('gabarit', '')).format_map(_Donnees(donnees))
        if not valeur.strip():
            continue

        ancre = champ.get('ancre')
        emplacements = page.search_for(ancre) if ancre else []
        if not emplacements:
            logger.warning(
                "Ancre « %s » introuvable dans le modèle PDF : champ « %s » non posé.",
                ancre,
                champ.get('cle', '?'),
            )
            continue

        ligne, origine = _ligne_de_texte(page, emplacements[0])
        zone = _zone_de_pose(page, champ, ligne, emplacements[0])
        page.add_redact_annot(zone, fill=(1, 1, 1))
        a_poser.append((champ, valeur, zone, origine))

    if a_poser:
        try:
            page.apply_redactions(
                images=pymupdf.PDF_REDACT_IMAGE_NONE,
                graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                text=pymupdf.PDF_REDACT_TEXT_REMOVE,
            )
        except TypeError:  # pragma: no cover - version de PyMuPDF plus ancienne
            page.apply_redactions()

    return a_poser


def _ecrire_champs(page, a_poser):
    """Phase 2 : écrit les valeurs dynamiques dans les zones préparées."""
    for champ, valeur, zone, origine in a_poser:
        taille = float(champ.get('taille', 7.5))

        if est_arabe(valeur):
            chemin = chemin_police_arabe()
            if not chemin:
                continue
            valeur = texte_arabe(valeur)
            police = NOM_POLICE_ARABE
            page.insert_font(fontname=police, fontfile=chemin)
        else:
            police = 'hebo' if champ.get('gras') else 'helv'

        alignement = champ.get('align', 'left')
        if alignement == 'center':
            x = (zone.x0 + zone.x1) / 2 - _largeur_texte(valeur, police, taille) / 2
            x = max(x, zone.x0)
        elif alignement == 'right':
            x = zone.x1 - _largeur_texte(valeur, police, taille)
        else:
            x = zone.x0

        # L'origine du modèle garantit l'alignement sur la ligne exacte.
        y = origine[1] if origine else zone.y1 - taille * 0.25
        page.insert_text((x, y), valeur, fontname=police, fontsize=taille, color=(0, 0, 0))


def _poser_photo(page, donnees):
    """Insère la photo de l'assuré dans la zone prévue du modèle."""
    octets = donnees.get('photo')
    if not octets:
        # Aucune photo en base : la zone du modèle reste telle quelle.
        return
    if _dimensions_image(octets) is None:
        logger.warning("Photo de l'assuré illisible : zone photo laissée vide.")
        return

    try:
        page.insert_image(
            _rect_fraction(page, layout.PHOTO_BOITE),
            stream=octets,
            keep_proportion=True,
            overlay=True,
        )
    except Exception:
        logger.exception("Insertion de la photo impossible sur la feuille de soins.")


def _poser_code_qr(page, donnees):
    """Insère le code QR / code scanné dans la zone prévue du modèle."""
    octets = code_qr_png(donnees.get('qr_contenu', ''))
    zone = _rect_fraction(page, layout.QR_BOITE)

    if layout.QR_LIBELLE:
        hauteur_libelle = 9.0
        zone = pymupdf.Rect(zone.x0, zone.y0, zone.x1, max(zone.y1 - hauteur_libelle, zone.y0 + 10))
        page.insert_text(
            ((zone.x0 + zone.x1) / 2 - _largeur_texte(layout.QR_LIBELLE, 'helv', 5.5) / 2,
             zone.y1 + 7.0),
            layout.QR_LIBELLE,
            fontname='helv',
            fontsize=5.5,
            color=(0, 0, 0),
        )

    page.insert_image(zone, stream=octets, keep_proportion=True, overlay=True)


def _generer_depuis_modele(donnees, chemin_modele):
    """Recopie le modèle officiel en y posant les données dynamiques."""
    document = pymupdf.open(chemin_modele)
    try:
        if document.page_count < 1:
            raise ValueError('Le modèle de feuille de soins ne contient aucune page.')
        page = document[0]

        a_poser = _preparer_champs(page, donnees)
        _ecrire_champs(page, a_poser)
        _poser_photo(page, donnees)
        _poser_code_qr(page, donnees)

        tampon = io.BytesIO()
        document.save(tampon, garbage=3, deflate=True)
        return tampon.getvalue()
    finally:
        document.close()


# ---------------------------------------------------------------------------
# 2) Reproduction fidèle du modèle (repli si le fichier modèle est absent)
# ---------------------------------------------------------------------------
_LARGEUR_PAGE, _HAUTEUR_PAGE = A4
_MARGE = 22.0
_X_DROITE = _LARGEUR_PAGE - _MARGE
_EPAISSEUR = 0.7

# Colonnes / hauteurs de lignes mesurées sur le modèle officiel.
_COL_FEUILLE = [205.0, 150.0, 100.0, 96.28]
_LIGNES_FEUILLE = [18.0, 18.0, 25.0, 25.0, 25.0, 25.0, 27.0]
_COL_PRESCRIPTION = [300.0, 45.0, 60.0, 146.28]
_LIGNES_PRESCRIPTION = [18.0, 16.0, 12.0, 56.0, 10.0, 14.8, 14.8, 14.8, 14.8, 14.8]
_COL_ANALYSES = [60.0, 395.0, 96.28]
_LIGNES_ANALYSES = [18.0, 14.0, 16.0, 16.83, 16.83, 16.83, 16.83, 16.83, 16.83]
_COL_HOSPITALISATION = [275.64, 275.64]
_LIGNES_HOSPITALISATION = [18.0, 20.67, 20.67, 20.67]

_POLICE_CACHET = ParagraphStyle(
    'cachet', fontName=_LATIN, fontSize=6.2, leading=7.6, alignment=1
)


def _dessiner_tableau(c, lignes, largeurs, hauteurs, haut, styles=None):
    """Dessine un tableau du formulaire et retourne l'ordonnée suivante."""
    tableau = Table(lignes, colWidths=largeurs, rowHeights=hauteurs)
    style = [
        ('GRID', (0, 0), (-1, -1), _EPAISSEUR, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), _LATIN),
        ('FONTSIZE', (0, 0), (-1, -1), 7.2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]
    style.extend(styles or [])
    tableau.setStyle(TableStyle(style))

    _, hauteur = tableau.wrapOn(c, sum(largeurs), sum(hauteurs))
    tableau.drawOn(c, _MARGE, _HAUTEUR_PAGE - haut - hauteur)
    return haut + hauteur


def _image_ajustee(octets, largeur_cellule, hauteur_cellule):
    """Image à la bonne taille pour la cellule, proportions conservées."""
    dimensions = _dimensions_image(octets)
    if dimensions is None:
        return ''
    largeur_px, hauteur_px = dimensions
    if not largeur_px or not hauteur_px:
        return ''
    facteur = min(largeur_cellule / largeur_px, hauteur_cellule / hauteur_px)
    return PdfImage(
        io.BytesIO(octets), width=largeur_px * facteur, height=hauteur_px * facteur
    )


def _styles_photo(ligne_debut, ligne_fin, colonne):
    """Style de la cellule photo : aucune marge, image centrée."""
    return [
        ('SPAN', (colonne, ligne_debut), (colonne, ligne_fin)),
        ('ALIGN', (colonne, ligne_debut), (colonne, ligne_fin), 'CENTER'),
        ('VALIGN', (colonne, ligne_debut), (colonne, ligne_fin), 'MIDDLE'),
        ('LEFTPADDING', (colonne, ligne_debut), (colonne, ligne_fin), 0),
        ('RIGHTPADDING', (colonne, ligne_debut), (colonne, ligne_fin), 0),
        ('TOPPADDING', (colonne, ligne_debut), (colonne, ligne_fin), 0),
        ('BOTTOMPADDING', (colonne, ligne_debut), (colonne, ligne_fin), 0),
    ]


def _styles_arabe(police_arabe, cellule_debut, cellule_fin):
    """Style des libellés arabes d'un tableau."""
    if not police_arabe:
        return []
    return [
        ('FONTNAME', cellule_debut, cellule_fin, police_arabe),
        ('FONTSIZE', cellule_debut, cellule_fin, 6.4),
        ('ALIGN', cellule_debut, cellule_fin, 'RIGHT'),
    ]


def _en_tete(c):
    """En-tête du formulaire : logos, titres arabe et français."""
    logo = _lecteur_logo()
    if logo is not None:
        try:
            largeur, hauteur = logo.getSize()
            hauteur_logo = 46.0
            largeur_logo = hauteur_logo * largeur / hauteur if hauteur else hauteur_logo
            haut_logo = _HAUTEUR_PAGE - 17 - hauteur_logo
            c.drawImage(logo, _MARGE, haut_logo, largeur_logo, hauteur_logo, mask='auto')
            c.drawImage(
                logo,
                _X_DROITE - largeur_logo,
                haut_logo,
                largeur_logo,
                hauteur_logo,
                mask='auto',
            )
        except Exception:  # pragma: no cover - logo illisible
            logger.warning("Logo d'en-tête illisible : feuille générée sans logo.")

    police_arabe = police_arabe_reportlab()
    titre_arabe = _libelle_arabe('الصندوق الوطني للتأمين الصحي')
    if titre_arabe and police_arabe:
        c.setFont(police_arabe, 12)
        c.drawCentredString(_LARGEUR_PAGE / 2, _HAUTEUR_PAGE - 42, titre_arabe)

    c.setFont(_LATIN_GRAS, 10.5)
    c.drawCentredString(
        _LARGEUR_PAGE / 2,
        _HAUTEUR_PAGE - 60,
        "Caisse Nationale d'Assurance Maladie - CNAM",
    )


def _bloc_feuille_de_soins(c, donnees, haut):
    """Bloc 1 : identité de l'assuré, photo, cachet du prescripteur."""
    police_arabe = police_arabe_reportlab()
    naissance = donnees['date_naissance_texte']
    if donnees['age_texte']:
        naissance = f"{naissance} : {donnees['age_texte']}" if naissance else donnees['age_texte']

    lignes = [
        [f"Feuille de Soins - {donnees['numero_feuille']}", '', '', 'SP/100'],
        [donnees['centre_hospitalier'], '', '', ''],
        ["Nom de l'assuré :", donnees['nom_complet'], _libelle_arabe('اسم المؤمن'), ''],
        [
            "Identifiant National d'Assurance Maladie :",
            donnees['inam'],
            _libelle_arabe('الرقم الوطني للتأمين الصحي'),
            '',
        ],
        [
            "Numéro National d'Identification :",
            donnees['nni'],
            _libelle_arabe('الرقم الوطني للتعريف'),
            '',
        ],
        [
            "Date de Naissance : Age :",
            naissance,
            _libelle_arabe('تاريخ الولادة : العمر'),
            '',
        ],
        [
            'Signature et cachet du prescripteur(Obligatoire):',
            '',
            f"Date des soins : {donnees['date_soins_texte']}",
            '',
        ],
    ]

    hauteur_photo = sum(_LIGNES_FEUILLE[2:6])
    lignes[2][3] = (
        _image_ajustee(donnees['photo'], _COL_FEUILLE[3] - 3, hauteur_photo - 3)
        if donnees['photo']
        else ''
    )

    styles = [
        ('SPAN', (0, 0), (2, 0)),
        ('SPAN', (0, 1), (2, 1)),
        ('SPAN', (0, 6), (1, 6)),
        ('FONTNAME', (0, 0), (0, 0), _LATIN_GRAS),
        ('FONTSIZE', (0, 0), (0, 0), 6.8),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTSIZE', (3, 0), (3, 0), 5.5),
        ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
        ('FONTSIZE', (0, 1), (0, 1), 6.2),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('ALIGN', (2, 6), (2, 6), 'RIGHT'),
    ]
    styles += _styles_arabe(police_arabe, (2, 2), (2, 5))
    styles += _styles_photo(2, 5, 3)

    return _dessiner_tableau(c, lignes, _COL_FEUILLE, _LIGNES_FEUILLE, haut, styles)


def _bloc_prescription(c, donnees, haut):
    """Bloc 2 : prescription du médecin et cachet de la pharmacie."""
    qr = code_qr_png(donnees.get('qr_contenu', ''))
    cote_qr = min(_COL_PRESCRIPTION[3] - 30, _LIGNES_PRESCRIPTION[3] - 4)

    lignes = [
        ['Prescription de médecin', '', '', ''],
        ['Medicament', 'Qté', 'Prix U', ''],
        ['', '', '', ''],
        ['', '', '', _image_ajustee(qr, cote_qr, cote_qr)],
        ['', '', '', 'SCAN ME'],
        [
            '',
            '',
            '',
            Paragraph(
                'Cachet &amp; Signature<br/>de la Pharmacie(Obligatoire)',
                _POLICE_CACHET,
            ),
        ],
        ['', '', '', ''],
        ['', '', '', ''],
        ['', '', '', ''],
        ['', '', '', ''],
    ]

    styles = [
        ('SPAN', (0, 0), (3, 0)),
        ('FONTNAME', (0, 0), (0, 0), _LATIN_GRAS),
        ('FONTSIZE', (0, 0), (0, 0), 7.4),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (2, 1), _LATIN_GRAS),
        ('SPAN', (3, 3), (3, 3)),
        ('ALIGN', (3, 3), (3, 3), 'CENTER'),
        ('ALIGN', (3, 4), (3, 4), 'CENTER'),
        ('FONTSIZE', (3, 4), (3, 4), 5.8),
        ('SPAN', (3, 5), (3, 9)),
        ('VALIGN', (3, 5), (3, 9), 'BOTTOM'),
    ]

    return _dessiner_tableau(
        c, lignes, _COL_PRESCRIPTION, _LIGNES_PRESCRIPTION, haut, styles
    )


def _bloc_analyses(c, donnees, haut):
    """Bloc 3 : analyses, examens et radio."""
    lignes = [
        ['Analyses, Examens et Radio', '', ''],
        ['Veuillez inscrire les codes/libellés des prestations', '', ''],
        ['Code', 'Libellé', ''],
        ['', '', ''],
        ['', '', ''],
        ['', '', ''],
        ['', '', ''],
        ['', '', ''],
        ['', '', ''],
    ]
    lignes[3][2] = Paragraph(
        'Cachet &amp; Signature Labo /<br/>Radio(Obligatoire)', _POLICE_CACHET
    )

    styles = [
        ('SPAN', (0, 0), (2, 0)),
        ('FONTNAME', (0, 0), (0, 0), _LATIN_GRAS),
        ('FONTSIZE', (0, 0), (0, 0), 7.4),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('SPAN', (0, 1), (2, 1)),
        ('FONTSIZE', (0, 1), (0, 1), 6.4),
        ('FONTNAME', (0, 2), (1, 2), _LATIN_GRAS),
        ('ALIGN', (0, 2), (1, 2), 'CENTER'),
        ('SPAN', (2, 3), (2, 8)),
    ]

    return _dessiner_tableau(c, lignes, _COL_ANALYSES, _LIGNES_ANALYSES, haut, styles)


def _bloc_hospitalisation(c, donnees, haut):
    """Bloc 4 : hospitalisation."""
    lignes = [
        ['Hospitalisation', ''],
        ["Motif de l'Hospitalisation (DRG):   ....... / ....... / ...................", ''],
        ["Date d'entrée :   ....... / ....... / .......", "Date de sortie :   ....... / ....... / ......."],
        ['Montant global facturé :', 'Montant remboursé CNAM:'],
    ]

    styles = [
        ('SPAN', (0, 0), (1, 0)),
        ('FONTNAME', (0, 0), (0, 0), _LATIN_GRAS),
        ('FONTSIZE', (0, 0), (0, 0), 7.4),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('SPAN', (0, 1), (1, 1)),
    ]

    return _dessiner_tableau(
        c, lignes, _COL_HOSPITALISATION, _LIGNES_HOSPITALISATION, haut, styles
    )


def _generer_reproduction(donnees):
    """Reproduit le formulaire officiel avec les données dynamiques."""
    tampon = io.BytesIO()
    document = canvas.Canvas(tampon, pagesize=A4)
    document.setTitle(f"Feuille de soins - {donnees['nom_complet']} ({donnees['nni']})")
    document.setAuthor("Caisse Nationale d'Assurance Maladie")
    document.setSubject("Feuille de soins")

    _en_tete(document)

    haut = 74.0
    haut = _bloc_feuille_de_soins(document, donnees, haut)
    haut = _bloc_prescription(document, donnees, haut + 3.0)
    haut = _bloc_analyses(document, donnees, haut + 3.0)
    _bloc_hospitalisation(document, donnees, haut + 3.0)

    document.showPage()
    document.save()
    return tampon.getvalue()


# ---------------------------------------------------------------------------
# 3) Pose des données dynamiques sur le modèle image (PNG)
# ---------------------------------------------------------------------------
# Le modèle image est le rendu 110 dpi de la feuille A4 (910 x 1287 px).
# Les coordonnées ci-dessous sont exprimées en points PDF, origine en haut à
# gauche, et reprennent la géométrie de la reproduction (voir plus haut) :
# seules les valeurs dynamiques sont masquées (filets préservés) puis
# réécrites par-dessus l'image.

_IMG_COL = (22.0, 227.0, 377.0, 477.0, 573.2756)   # bornes du bloc identité
_IMG_ROW = (74.0, 92.0, 110.0, 135.0, 160.0, 185.0, 210.0, 237.0)
_IMG_QR = (427.0, 286.0, 573.2756, 342.0)          # cellule du code QR

_IMG_FILET = 0.5        # retrait du masque par rapport aux filets (pt)
_IMG_LEADING = 12.0     # CellStyle.leading des cellules platypus (non surchargé)
_IMG_PAD = 4.0          # marge de texte des cellules (LEFT/RIGHTPADDING)


def _img_cellule(x0, y0, x1, y1):
    """Intérieur d'une cellule, filets de bordure préservés."""
    return (x0 + _IMG_FILET, y0 + _IMG_FILET, x1 - _IMG_FILET, y1 - _IMG_FILET)


def _img_masque(c, cellule):
    """Rectangle blanc masquant l'ancienne valeur du modèle image."""
    x0, y0, x1, y1 = cellule
    c.setFillColor(colors.white)
    c.rect(x0, _HAUTEUR_PAGE - y1, x1 - x0, y1 - y0, stroke=0, fill=1)


def _img_texte(c, cellule, valeur, police=_LATIN, taille=7.2, aligne='gauche'):
    """Écrit une valeur comme le ferait la cellule du tableau de la reproduction.

    Reproduit la formule platypus `VALIGN MIDDLE` (tables.py) :
    ligne de base = centre de la ligne + leading / 2 - taille de police.
    """
    x0, y0, x1, y1 = cellule
    ligne_base = (
        _HAUTEUR_PAGE - (y0 + y1) / 2.0 + _IMG_LEADING / 2.0 - taille
    )
    c.setFillColor(colors.black)
    c.setFont(police, taille)
    if aligne == 'centre':
        c.drawCentredString((x0 + x1) / 2.0, ligne_base, valeur)
    elif aligne == 'droite':
        c.drawRightString(x1 - _IMG_PAD, ligne_base, valeur)
    else:
        c.drawString(x0 + _IMG_PAD, ligne_base, valeur)


def _img_pose(c, cellule, valeur, police=_LATIN, taille=7.2, aligne='gauche'):
    """Masque l'ancienne valeur de la cellule puis écrit la nouvelle."""
    _img_masque(c, _img_cellule(*cellule))
    if valeur:
        _img_texte(c, cellule, valeur, police, taille, aligne)


def _img_photo(c, donnees):
    """Photo de l'assuré dans la cellule du modèle (blanc si absente)."""
    x0, y0, x1, y1 = _IMG_COL[3], _IMG_ROW[2], _IMG_COL[4], _IMG_ROW[6]
    _img_masque(c, _img_cellule(x0, y0, x1, y1))

    octets = donnees.get('photo')
    if not octets:
        return
    dimensions = _dimensions_image(octets)
    if dimensions is None:
        return
    largeur_px, hauteur_px = dimensions
    if not largeur_px or not hauteur_px:
        return

    # Même règle que la reproduction : gîte dans (cellule - 3 pt), centré.
    facteur = min((x1 - x0 - 3) / largeur_px, (y1 - y0 - 3) / hauteur_px)
    largeur = largeur_px * facteur
    hauteur = hauteur_px * facteur
    c.drawImage(
        ImageReader(io.BytesIO(bytes(octets))),
        (x0 + x1) / 2.0 - largeur / 2.0,
        _HAUTEUR_PAGE - (y0 + y1) / 2.0 - hauteur / 2.0,
        largeur,
        hauteur,
        mask='auto',
    )


def _img_qr(c, donnees):
    """Code QR du modèle remplacé par le contenu dynamique (blanc si absent)."""
    x0, y0, x1, y1 = _IMG_QR
    _img_masque(c, _img_cellule(x0, y0, x1, y1))

    contenu = donnees.get('qr_contenu', '')
    if not str(contenu or '').strip():
        return
    png = code_qr_png(contenu)
    if not png:
        return
    dimensions = _dimensions_image(png)
    if dimensions is None:
        return
    largeur_px, hauteur_px = dimensions
    if not largeur_px or not hauteur_px:
        return

    # Côté du carré : identique à la reproduction (cellule - 30 / - 4 pt).
    cote = min((x1 - x0) - 30, (y1 - y0) - 4)
    facteur = min(cote / largeur_px, cote / hauteur_px)
    largeur = largeur_px * facteur
    hauteur = hauteur_px * facteur
    c.drawImage(
        ImageReader(io.BytesIO(bytes(png))),
        (x0 + x1) / 2.0 - largeur / 2.0,
        _HAUTEUR_PAGE - (y0 + y1) / 2.0 - hauteur / 2.0,
        largeur,
        hauteur,
        mask='auto',
    )


def _generer_sur_image(donnees, chemin):
    """Pose les données dynamiques sur l'image modèle (fond de page A4)."""
    with Image.open(chemin) as image_modele:
        if image_modele.mode != 'RGB':
            image_modele = image_modele.convert('RGB')
        tampon_fond = io.BytesIO()
        image_modele.save(tampon_fond, format='PNG')

    tampon = io.BytesIO()
    c = canvas.Canvas(tampon, pagesize=A4)
    c.setTitle(f"Feuille de soins - {donnees['nom_complet']} ({donnees['nni']})")
    c.setAuthor("Caisse Nationale d'Assurance Maladie")
    c.setSubject("Feuille de soins")
    c.drawImage(
        ImageReader(io.BytesIO(tampon_fond.getvalue())),
        0, 0, width=_LARGEUR_PAGE, height=_HAUTEUR_PAGE,
    )

    naissance = donnees['date_naissance_texte']
    if donnees['age_texte']:
        naissance = (
            f"{naissance} : {donnees['age_texte']}" if naissance
            else donnees['age_texte']
        )

    # Ligne 0 : numéro de feuille (centré sur les colonnes 0 à 2 du tableau).
    _img_pose(
        c, (_IMG_COL[0], _IMG_ROW[0], _IMG_COL[3], _IMG_ROW[1]),
        f"Feuille de Soins - {donnees['numero_feuille']}",
        _LATIN_GRAS, 6.8, 'centre',
    )
    # Ligne 1 : centre hospitalier (centré sur les colonnes 0 à 2 du tableau).
    _img_pose(
        c, (_IMG_COL[0], _IMG_ROW[1], _IMG_COL[3], _IMG_ROW[2]),
        donnees['centre_hospitalier'], _LATIN, 6.2, 'centre',
    )
    # Lignes 2 à 5 : identité de l'assuré (colonne 1, alignée à gauche).
    for index, valeur in (
        (2, donnees['nom_complet']),
        (3, donnees['inam']),
        (4, donnees['nni']),
        (5, naissance),
    ):
        _img_pose(
            c,
            (_IMG_COL[1], _IMG_ROW[index], _IMG_COL[2], _IMG_ROW[index + 1]),
            valeur,
        )

    # Ligne 6 : date des soins (à droite de la colonne 2, débord possible sur
    # la colonne 1 comme dans la reproduction) : les deux cellules sont masquées.
    _img_masque(c, _img_cellule(_IMG_COL[1], _IMG_ROW[6], _IMG_COL[2], _IMG_ROW[7]))
    cellule_date = (_IMG_COL[2], _IMG_ROW[6], _IMG_COL[3], _IMG_ROW[7])
    _img_masque(c, _img_cellule(*cellule_date))
    if donnees['date_soins_texte']:
        _img_texte(
            c, cellule_date, f"Date des soins : {donnees['date_soins_texte']}",
            _LATIN, 7.2, 'droite',
        )

    _img_photo(c, donnees)
    _img_qr(c, donnees)

    c.showPage()
    c.save()
    return tampon.getvalue()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
def generer_feuille_soins(donnees):
    """Retourne les octets de la Feuille de soins PDF.

    Le modèle officiel est utilisé dès qu'il est présent : seule une relecture
    du fichier est effectuée, la mise en page reste donc strictement identique.
    À défaut de PDF officiel, l'image modèle (`CNAM_FEUILLE_SOINS_MODELE_IMAGE`)
    sert de fond de page et reçoit la pose des données dynamiques. Sans aucun
    modèle, la reproduction fidèle du formulaire est générée.
    """
    chemin_modele = getattr(settings, 'CNAM_FEUILLE_SOINS_MODELE', '')
    if chemin_modele and os.path.isfile(chemin_modele):
        try:
            return _generer_depuis_modele(donnees, chemin_modele)
        except Exception:
            logger.exception(
                "Pose des données sur le modèle PDF impossible : reproduction "
                "du modèle utilisée pour la feuille de soins."
            )
    else:
        logger.info(
            "Modèle PDF introuvable (%s) : pose sur l'image modèle ou "
            "reproduction du modèle.",
            chemin_modele,
        )

    chemin_image = getattr(settings, 'CNAM_FEUILLE_SOINS_MODELE_IMAGE', '')
    if chemin_image and os.path.isfile(chemin_image):
        try:
            return _generer_sur_image(donnees, chemin_image)
        except Exception:
            logger.exception(
                "Pose des données sur l'image modèle impossible : reproduction "
                "du modèle utilisée pour la feuille de soins."
            )
    else:
        logger.info(
            "Modèle image introuvable (%s) : reproduction du modèle utilisée.",
            chemin_image,
        )

    return _generer_reproduction(donnees)




