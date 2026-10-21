#!/bin/sh
# Regenera Tutorial.ipynb, Demo.ipynb y Ejemplos.ipynb desde los
# guiones gen_*.py (sin salidas, kernel «qbank») y, si se pasa --ejecuta, los
# ejecuta con nbconvert para comprobar que no fallan. Lanzar desde la raíz del repo.
set -e
cd "$(dirname "$0")/../.."
for g in tutorial demo ejemplos; do .venv/bin/python tools/cuadernos/gen_$g.py; done
if [ "$1" = "--ejecuta" ]; then
  J=$PWD/.venv/bin/jupyter; OUT=$(mktemp -d)
  $J nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=qbank --output-dir "$OUT" Tutorial.ipynb Demo.ipynb Ejemplos.ipynb 2>&1 | grep -i "error\|Writing" || true
  echo "Cuadernos ejecutados en $OUT"
fi
