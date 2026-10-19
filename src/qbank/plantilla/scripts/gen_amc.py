#!/usr/bin/env python3
"""Vista profe en AMC: escribe build/amc/<pregunta>.tex (bloques \\element) y
<pregunta>-doc.tex (documento autónomo); `make amc` los compila a PDF.

Cada variante muestra TODAS las cuestiones con su marca (correcta/incorrecta),
cada explicación (exp) en cursiva junto a su cuestión y, en un bloque
«Exclusiones», las rechazadas por su precondición. En las preguntas con setup
aleatorio se imprime un caso por mundo y por patrón de marcas distinto (hasta
config.MAX_CASOS_PROFE), explorando config.N_SORTEOS_PROFE sorteos: así la
revisión ve cada rama de la pregunta sin repetir casos numéricos que no
cambian nada. Las preguntas multiparte salen como una sola pregunta AMC con
un bloque de casillas por parte (AMC_multipart).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ, config, documento_amc, escribe_si_cambia, parser, preguntas  # noqa: E402

import numpy as np                     # noqa: E402
from qbank import AMC_multipart, AMCblock, load_problema  # noqa: E402

os.chdir(RAIZ)
args = parser('Vista profe AMC: build/amc/<pregunta>.tex y -doc.tex.').parse_args()
SALIDA = Path('build/amc')
SALIDA.mkdir(parents=True, exist_ok=True)


def con_exp(cuestiones):
    """Añade a cada cuestión aceptada su explicación, en cursiva y pequeño."""
    return [(c[0] + (r' {\footnotesize\itshape ' + c[3] + '}' if len(c) > 3 and c[3] else ''),
             *c[1:]) for c in cuestiones]


def bloque(nombre, etiqueta, partes, cols):
    partes = [(enunciado, con_exp(cuestiones)) for enunciado, cuestiones in partes]
    if len(partes) > 1:
        return AMC_multipart(nombre, etiqueta, '', partes, cols=cols, profe=True)
    return AMCblock(nombre, etiqueta, partes[0][0], partes[0][1], cols=cols, profe=True)


def bloques_profe(p, nombre):
    cols = p.export.get('cols', 1)
    if p.setup is None:
        return [bloque(nombre, etiqueta, partes, cols)
                for etiqueta, partes in p.por_partes_profe(verbose=False)]
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
            bloques.append(bloque(nombre, f'mundo{etiqueta}-caso{patrones[patron]}', partes, cols))
    return bloques


for ruta in preguntas(args.leccion):
    nombre = ruta.stem
    bloques = bloques_profe(load_problema(str(ruta)), nombre)
    cambiado = escribe_si_cambia(SALIDA / f'{nombre}.tex', ''.join(bloques))
    escribe_si_cambia(SALIDA / f'{nombre}-doc.tex', documento_amc(nombre, explain=True))
    print(f'  {nombre}.tex  ({len(bloques)} caso(s){"" if cambiado else ", sin cambios"})')

escribe_si_cambia(SALIDA / '_catalogo.tex', ''.join(f'\\input{{{r.stem}}}\n' for r in preguntas()))
