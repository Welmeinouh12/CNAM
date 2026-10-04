"""Version automatique des fichiers statiques.

Django sert les fichiers statiques directement depuis le disque, mais le
navigateur les met en cache. Il faut donc ajouter une « version » à l'URL
pour qu'un fichier modifié soit réellement rechargé.

La version retenue ici est la date de modification du fichier, calculée à
chaque affichage de la page : toute modification de `script.js` ou
`style.css` change automatiquement l'URL, sans avoir à renseigner une
version à la main dans le gabarit (ce qui est très vite oublié, et laisse
le navigateur servir un ancien fichier).
"""

from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_versioned(chemin):
    """URL d'un fichier statique, suffixée par sa date de modification.

    `chemin` est le chemin du fichier tel que Django le connaît
    (par exemple « fds/script.js »). Le fichier est localisé via les
    « staticfiles finders », donc le calcul reste correct même si la
    disposition des dossiers change. Si le fichier est introuvable,
    l'URL est renvoyée telle quelle : la page reste fonctionnelle.
    """
    url = static(chemin)
    fichier = finders.find(chemin)
    if not fichier:
        return url
    try:
        version = Path(fichier).stat().st_mtime_ns
    except OSError:
        return url
    return f"{url}?v={version}"
