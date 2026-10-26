#!/usr/bin/env python3
"""Vista profe en AMC: escribe build/amc/<pregunta>.tex (bloques \\element) y
<pregunta>-doc.tex (documento autónomo); `make amc` los compila a PDF.

Cada variante muestra TODAS las cuestiones con su marca (correcta/incorrecta),
cada explicación (exp) en cursiva tras una raya junto a su cuestión y, en un
bloque «Exclusiones», las rechazadas por su precondición. En las preguntas con
setup aleatorio se imprime un caso por cada combinación distinta de enunciado
(sin contar los números) y patrón de marcas, explorando config.N_SORTEOS_PROFE
sorteos y hasta config.MAX_CASOS_PROFE casos, etiquetados mundoM-casoK: así la
revisión ve cada rama de la pregunta sin repetir casos numéricos que no
cambian nada. Las preguntas multiparte salen como una sola pregunta AMC con
un bloque de casillas por parte (AMC_multipart) o, con
"amc_partes": "separadas" en export, como preguntas numeradas consecutivas.

Termina con error si alguna pregunta no produce ninguna variante (pasa
`make lint`, que dice por qué).
"""
import os
import re
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

_NUMERO = re.compile(r'-?\d+(?:[.,]\d+)?')


def con_exp(cuestiones):
    """Añade a cada cuestión aceptada su explicación, en cursiva y pequeño."""
    return [(c[0] + (r' {\footnotesize\itshape --- ' + c[3] + '}' if len(c) > 3 and c[3] else ''),
             *c[1:]) for c in cuestiones]


def bloque(nombre, etiqueta, partes, cols, separadas=False):
    partes = [(enunciado, con_exp(cuestiones)) for enunciado, cuestiones in partes]
    if len(partes) > 1:
        return AMC_multipart(nombre, etiqueta, '', partes, cols=cols, profe=True,
                             separadas=separadas)
    return AMCblock(nombre, etiqueta, partes[0][0], partes[0][1], cols=cols, profe=True)


def bloques_profe(p, nombre):
    """(bloques, número de mundos). Sin setup, una entrada por mundo; con
    setup, una por caso (mundo × patrón de marcas)."""
    cols = p.export.get('cols', 1)
    separadas = p.export.get('amc_partes', 'juntas') == 'separadas'
    if p.setup is None:
        bloques = [bloque(nombre, etiqueta, partes, cols, separadas)
                   for etiqueta, partes in p.por_partes_profe(verbose=False)]
        return bloques, len(bloques)
    p.seed = None                       # manda la semilla de cada sorteo
    bloques, mundos, casos = [], {}, {}
    for sorteo in range(config.N_SORTEOS_PROFE):
        np.random.seed(sorteo)
        for _, partes in p.por_partes_profe(verbose=False):
            # El mundo es el enunciado sin sus números: así dos sorteos con el
            # mismo supuesto activo cuentan como el mismo mundo aunque los
            # valores cambien, y los casos distinguen los patrones de marcas.
            mundo  = tuple(_NUMERO.sub('#', enunciado) for enunciado, _ in partes)
            marcas = tuple('R' if len(c) == 3 else bool(c[1]) for _, cs in partes for c in cs)
            if (mundo, marcas) in casos:
                continue
            if len(casos) >= config.MAX_CASOS_PROFE:
                print(f'  AVISO: {nombre} tiene más de {config.MAX_CASOS_PROFE} casos distintos; '
                      'se imprimen los primeros')
                return bloques, len(mundos)
            m = mundos.setdefault(mundo, len(mundos) + 1)
            k = sum(1 for mu, _ in casos if mu == mundo) + 1
            casos[(mundo, marcas)] = (m, k)
            bloques.append(bloque(nombre, f'mundo{m}-caso{k}', partes, cols, separadas))
    return bloques, len(mundos)


sin_variantes = []
for ruta in preguntas(args.leccion):
    nombre = ruta.stem
    p = load_problema(str(ruta))
    bloques, n_mundos = bloques_profe(p, nombre)
    cambiado = escribe_si_cambia(SALIDA / f'{nombre}.tex', ''.join(bloques))
    escribe_si_cambia(SALIDA / f'{nombre}-doc.tex', documento_amc(nombre, explain=True))
    # La vista profe tiene una entrada por mundo; con setup, una por caso.
    cuenta = (f'{n_mundos} mundo(s)' if p.setup is None
              else f'{n_mundos} mundo(s), {len(bloques)} caso(s)')
    print(f'  {nombre}.tex  ({cuenta}{"" if cambiado else ", sin cambios"})')
    if not bloques:
        sin_variantes.append(nombre)
        print(f'  ERROR: {nombre} no produce ninguna variante válida (pasa make lint)')

escribe_si_cambia(SALIDA / '_catalogo.tex', ''.join(f'\\input{{{r.stem}}}\n' for r in preguntas()))
if sin_variantes:
    sys.exit(1)
