# Herramientas de mantenimiento

Para quien modifica qbank, no para quien lo usa.

- `orgtangle.py` — genera `src/qbank/*.py` a partir de `CalcPropQuiz.org` y
  `CalcPropExport.org` sin Emacs (`write`), comprueba que coinciden (`check`,
  lo ejecuta `tests/test_literate.py`) o dice qué bloques difieren (`informe`).
- `cuadernos/` — guiones que generan `Tutorial.ipynb`, `Ejemplos.ipynb` y
  `ejemplosManual/Demo.ipynb`: se edita el guion, no el cuaderno.
  `sh tools/cuadernos/regenera.sh [--ejecuta]` los reescribe y, con
  `--ejecuta`, los ejecuta con el kernel `qbank` para comprobar que no fallan.
- `web.sh` y `web.el` — regeneran `docs/`, la web de GitHub Pages
  (https://mbujosab.github.io/calcprop-qbank/): exportan a HTML `index.org`,
  `README.org`, el README de la plantilla, la Guía y el Manual, y copian sus
  PDF. `docs/` no se edita a mano, salvo la hoja `docs/style.css`.
