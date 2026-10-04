"""Compatibilité avec le schéma réel de la table des assurés.

La table `assure` existe déjà dans PostgreSQL et ne contient pas forcément
l'intégralité des colonnes du modèle `fds.Assure` (pgAdmin, par exemple, crée
souvent une table réduite à `nni, inam, nom, date_naissance, photo`).

Exiger une migration `makemigrations` / `migrate` détruirait les données
existantes, ce qui est inacceptable ici. Ce module rend donc la lecture
possible quel que soit le schéma, en lecture seule :

* il **introspecte** la table réelle (une requête, résultat mis en cache) ;
* il **diffère** (`defer()`) les colonnes absentes : elles ne sont jamais
  sélectionnées et ne provoquent donc aucune erreur SQL ;
* il fournit un **accesseur sûr** renvoyant une valeur par défaut pour un
  champ absent, différé ou vide.

Aucune donnée n'est écrite ni modifiée par ce module.

Usage typique::

    from .db_compat import queryset, valeur

    assure = queryset(Assure).filter(nni__in=variantes).first()
    telephone = valeur(assure, 'telephone', '')
"""


from time import monotonic

from django.db import connections

# Colonnes réellement présentes, mises en cache par (alias, table) avec
# l'instant où elles ont été lues. L'introspection n'est donc exécutée
# qu'une fois par table…
_cache = {}

# …mais seulement pendant cette durée. Sans cela, un serveur lancé avant
# l'ajout d'une colonne continuerait d'ignorer cette colonne jusqu'au
# redémarrage, sans aucun message d'erreur : les données seraient
# simplement « perdues » silencieusement.
DUREE_CACHE_SECONDES = 60


def _decrire(model, alias='default'):
    """Retourne la description de la table du modèle.

    Clé renvoyée : `existe`, `colonnes` (frozenset), `pk` (nom de colonne ou
    None) et `erreur` (message si l'introspection a échoué).

    Le résultat est mémorisé `DUREE_CACHE_SECONDES` secondes : une
    modification du schéma en base est donc prise en compte sans avoir à
    redémarrer le serveur.
    """
    cle = (alias, model._meta.db_table)
    memorise = _cache.get(cle)
    if memorise is not None and (monotonic() - memorise[0]) < DUREE_CACHE_SECONDES:
        return memorise[1]

    connexion = connections[alias]
    info = {
        'existe': False,
        'colonnes': frozenset(),
        'pk': None,
        'erreur': '',
    }

    try:
        with connexion.cursor() as curseur:
            tables = connexion.introspection.table_names(curseur)
            if model._meta.db_table in tables:
                description = connexion.introspection.get_table_description(
                    curseur, model._meta.db_table
                )
                info['existe'] = True
                info['colonnes'] = frozenset(colonne.name for colonne in description)
                info['pk'] = connexion.introspection.get_primary_key_column(
                    curseur, model._meta.db_table
                )
    except Exception as exc:  # base injoignable : l'erreur reste visible
        info['erreur'] = str(exc)

    _cache[cle] = (monotonic(), info)
    return info


def vider_cache():
    """Oublie les colonnes mises en cache (après un changement de schéma)."""
    _cache.clear()


def table_existe(model, alias='default'):
    """Indique si la table du modèle est réellement présente en base."""
    return _decrire(model, alias)['existe']


def colonnes_reelles(model, alias='default'):
    """Ensemble des noms de colonnes trouvées dans la table."""
    return _decrire(model, alias)['colonnes']


def champs_disponibles(model, alias='default'):
    """Noms des champs du modèle réellement stockés en base."""
    info = _decrire(model, alias)
    if not info['existe']:
        # Table absente ou base injoignable : on ne filtre rien, afin que
        # l'erreur SQL d'origine reste visible et exploitable.
        return {champ.name for champ in model._meta.concrete_fields}
    return {
        champ.name
        for champ in model._meta.concrete_fields
        if champ.column in info['colonnes']
    }


def champs_manquants(model, alias='default'):
    """Noms des champs du modèle absents de la table."""
    return (
        {champ.name for champ in model._meta.concrete_fields}
        - champs_disponibles(model, alias)
    )


def queryset(model, alias='default'):
    """Queryset sur le modèle, purgé des colonnes absentes de la table.

    L'ordre par défaut du modèle est filtré lui aussi : `ORDER BY` porte sur
    une colonne non sélectionnée, or PostgreSQL refuse de trier sur une
    colonne que la table ne contient pas. Seuls les champs réellement
    stockés sont donc conservés ; si aucun ne l'est, le tri est retiré.
    """
    resultat = model._default_manager.using(alias).all()
    manquants = sorted(champs_manquants(model, alias))
    if not manquants:
        return resultat

    resultat = resultat.defer(*manquants)

    ordre = model._meta.ordering or ()
    if any(str(champ).lstrip('-') in manquants for champ in ordre):
        disponibles = champs_disponibles(model, alias)
        resultat = resultat.order_by(
            *[champ for champ in ordre if str(champ).lstrip('-') in disponibles]
        )
    return resultat


def valeur(instance, champ, defaut=''):
    """Valeur d'un champ, ou `defaut` s'il est absent, différé ou vide.

    Un champ différé n'est pas relancé en base : l'attribut n'est jamais
    demandé, ce qui évite une requête qui échouerait sur une colonne
    inexistante.
    """
    if instance is None:
        return defaut
    if champ in instance.get_deferred_fields():
        return defaut
    contenu = getattr(instance, champ, None)
    return defaut if contenu is None else contenu
