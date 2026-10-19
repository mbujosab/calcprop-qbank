#!/usr/bin/env python3
"""Vista alumno en AMC: escribe build/amc-student/<pregunta>.tex (bloques
\\element, una variante por combinación e instancia) y <pregunta>-doc.tex
(documento autónomo); `make amc-student` los compila a PDF.

Lee last_choice, cols e instances del campo export de cada pregunta. También
escribe build/amc-student/_catalogo.tex, con un \\input por pregunta, para
incluir el banco entero en un examen AMC real.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ, config, documento_amc, escribe_si_cambia, parser, preguntas  # noqa: E402

import numpy as np                     # noqa: E402
from qbank import AMCblock, load_problema  # noqa: E402

os.chdir(RAIZ)
args = parser('Vista alumno AMC: build/amc-student/<pregunta>.tex y -doc.tex.').parse_args()
SALIDA = Path('build/amc-student')
SALIDA.mkdir(parents=True, exist_ok=True)

for ruta in preguntas(args.leccion):
    nombre = ruta.stem
    p = load_problema(str(ruta))
    np.random.seed(42)                  # reproducible aunque la pregunta no tenga seed
    bloques = [AMCblock(nombre, etiqueta, enunciado, cuestiones,
                        last_choice=p.export.get('last_choice', False),
                        cols=p.export.get('cols', 1),
                        last_choice_text=config.LAST_CHOICE_TEXT_AMC)
               for etiqueta, partes in p.por_partes(instances=p.export.get('instances', 1))
               for enunciado, cuestiones in partes]
    cambiado = escribe_si_cambia(SALIDA / f'{nombre}.tex', ''.join(bloques))
    escribe_si_cambia(SALIDA / f'{nombre}-doc.tex', documento_amc(nombre))
    print(f'  {nombre}.tex  ({len(bloques)} variante(s){"" if cambiado else ", sin cambios"})')

escribe_si_cambia(SALIDA / '_catalogo.tex', ''.join(f'\\input{{{r.stem}}}\n' for r in preguntas()))
