#!/usr/bin/env python3
"""Moodle: escribe build/moodle/<pregunta>.tex, un documento autónomo con el
paquete LaTeX «moodle». Al compilarlo (`make moodle`) se obtienen a la vez
<pregunta>.pdf (revisión) y <pregunta>-moodle.xml (importable en Moodle).

Lee last_choice e instances del campo export de cada pregunta, igual que
gen_amc_student.py, de modo que Moodle reciba las mismas variantes que el
examen en papel.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ, config, escribe_si_cambia, parser, preguntas  # noqa: E402

import numpy as np                     # noqa: E402
from qbank import QuizMoodle, load_problema  # noqa: E402

os.chdir(RAIZ)
args = parser('Moodle: build/moodle/<pregunta>.tex.').parse_args()
SALIDA = Path('build/moodle')
TMP = SALIDA / '.tmp'                   # QuizMoodle escribe siempre; aquí, y se copia solo si cambia
TMP.mkdir(parents=True, exist_ok=True)

for ruta in preguntas(args.leccion):
    nombre = ruta.stem
    p = load_problema(str(ruta))
    np.random.seed(42)
    n = QuizMoodle(nombre, str(TMP) + '/', p,
                   last_choice=p.export.get('last_choice', False),
                   instances=p.export.get('instances', 1),
                   aux_latex=config.AUX_LATEX_MOODLE,
                   last_choice_text=config.LAST_CHOICE_TEXT_MOODLE)
    texto = (TMP / f'{nombre}.tex').read_text(encoding='utf-8')
    cambiado = escribe_si_cambia(SALIDA / f'{nombre}.tex', texto)
    print(f'  {nombre}.tex  ({n} variante(s){"" if cambiado else ", sin cambios"})')
