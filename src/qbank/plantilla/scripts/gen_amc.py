#!/usr/bin/env python3
"""Vista profe en AMC: escribe build/amc/<pregunta>.tex (bloques \\element) y
<pregunta>-doc.tex (documento autónomo); `make amc` los compila a PDF.

Cada variante muestra TODAS las cuestiones con su marca (correcta/incorrecta)
y, en un bloque «Exclusiones», las rechazadas por su precondición. En las
preguntas con setup aleatorio se imprime un caso por mundo y por patrón de
marcas distinto (hasta config.MAX_CASOS_PROFE), explorando
config.N_SORTEOS_PROFE sorteos: así la revisión ve cada rama de la pregunta
sin repetir casos numéricos que no cambian nada.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ, config, documento_amc, escribe_si_cambia, parser, preguntas  # noqa: E402

import numpy as np                     # noqa: E402
from qbank import AMCblock, load_problema  # noqa: E402

os.chdir(RAIZ)
args = parser('Vista profe AMC: build/amc/<pregunta>.tex y -doc.tex.').parse_args()
SALIDA = Path('build/amc')
SALIDA.mkdir(parents=True, exist_ok=True)


def bloques_profe(p, nombre):
    cols = p.export.get('cols', 1)
    if p.setup is None:
        return [AMCblock(nombre, etiqueta, enunciado, cuestiones, cols=cols, profe=True)
                for etiqueta, partes in p.por_partes_profe(verbose=False)
                for enunciado, cuestiones in partes]
    p.seed = None                       # manda la semilla de cada sorteo
    bloques, patrones = [], {}
    for sorteo in range(config.N_SORTEOS_PROFE):
        np.random.seed(sorteo)
        for etiqueta, partes in p.por_partes_profe(verbose=False):
            patron = (etiqueta, tuple('R' if len(c) == 3 else bool(c[1])
                                      for _, cs in partes for c in cs))
            if patron in patrones:
                continue
            patrones[patron] = len(patrones) + 1
            if len(patrones) > config.MAX_CASOS_PROFE:
                print(f'  AVISO: {nombre} tiene más de {config.MAX_CASOS_PROFE} patrones; '
                      'se imprimen los primeros')
                return bloques
            for enunciado, cuestiones in partes:
                bloques.append(AMCblock(nombre, f'mundo{etiqueta}-caso{patrones[patron]}',
                                        enunciado, cuestiones, cols=cols, profe=True))
    return bloques


for ruta in preguntas(args.leccion):
    nombre = ruta.stem
    bloques = bloques_profe(load_problema(str(ruta)), nombre)
    cambiado = escribe_si_cambia(SALIDA / f'{nombre}.tex', ''.join(bloques))
    escribe_si_cambia(SALIDA / f'{nombre}-doc.tex', documento_amc(nombre, explain=True))
    print(f'  {nombre}.tex  ({len(bloques)} variante(s){"" if cambiado else ", sin cambios"})')

escribe_si_cambia(SALIDA / '_catalogo.tex', ''.join(f'\\input{{{r.stem}}}\n' for r in preguntas()))
