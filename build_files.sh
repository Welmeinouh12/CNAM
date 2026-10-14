#!/bin/sh
# Génération des fichiers statiques pour le déploiement Vercel.
#
# Les variables sensibles (SECRET_KEY, DATABASE_URL, ...) sont fournies par
# Vercel : Settings > Environment Variables. Ne rien écrire en dur ici.
#
# Ce fichier est exécuté par Vercel via « @vercel/static-build » si le projet
# l'utilise, et peut aussi être lancé manuellement :
#     sh build_files.sh
#
# « collectstatic » remplit STATIC_ROOT (dossier « staticfiles/ »). Ce dossier
# fait partie du paquet de la fonction Lambda : c'est donc lui, et non le CDN
# de Vercel, qui sert les fichiers via WhiteNoise.
#
# Le manifeste « staticfiles.json » est volontairement produit ici : avec lui,
# « {% static %} » génère des URL suffixées par une empreinte (« style.abc.css »)
# que le navigateur peut mettre en cache très longtemps. Ces URL ne fonctionnent
# que si les fichiers suffixés voyagent eux aussi dans « staticfiles/ » : ils
# doivent donc être versionnés avec le projet (voir .gitignore).
set -e

python manage.py collectstatic --noinput

# Vérification : le manifeste doit exister, sinon Django retomberait sur les
# noms d'origine et le cache long serait perdu.
test -f staticfiles/staticfiles.json || echo "ATTENTION : staticfiles.json absent"
