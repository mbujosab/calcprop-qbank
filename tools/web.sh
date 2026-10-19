#!/bin/sh
# Regenera docs/ (la página de GitHub Pages) desde los .org: no se edita a mano.
# Uso: sh tools/web.sh   (desde cualquier sitio; trabaja en la raíz del repo)
# Los PDF se copian tal como están: regéneralos antes si has cambiado los .org.
set -eu
cd "$(dirname "$0")/.."
mkdir -p docs
emacs --batch -l tools/web.el
cp GuiaDiseno.pdf Manual.pdf Fase5-prueba.pdf docs/
touch docs/.nojekyll          # Pages sirve los ficheros tal cual, sin Jekyll
echo "docs/ regenerado: $(ls docs | tr '\n' ' ')"
