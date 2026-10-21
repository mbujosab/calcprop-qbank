#!/usr/bin/env python3
"""Vista de lectura: escribe build/lectura/<leccion>-lectura.tex, un documento
por lección (L-NN) con las preguntas seleccionadas; `make lectura` lo compila.

Para cada pregunta: la tabla de mundos, un ejemplo por mundo (y, si la
pregunta declara "lectura": {"cubrir": [...]}, por cada combinación de
valores de esas variables del setup), con el enunciado en un recuadro, las
alternativas agrupadas por hueco, cada una marcada V/F y con su explicación
(exp) debajo, y las que la precondición excluye en ese mundo en gris con su
motivo. Es el documento para leer y opinar sobre las preguntas; la vista
profe de AMC (make amc) sigue siendo la del examen.

Las preguntas con setup que no declaran "lectura" añaden config.EXTRAS_LECTURA
sorteos más por mundo con enunciado distinto (--extras N lo cambia). El
preámbulo es config.PREAMBULO_LECTURA si existe; si no, config.PREAMBULO_AMC.
Las preguntas que no siguen la convención L-NN- van a otras-lectura.tex.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ, config, escribe_si_cambia, parser, preguntas  # noqa: E402

from qbank import QuizLectura, load_problema  # noqa: E402

os.chdir(RAIZ)
ap = parser('Vista de lectura: build/lectura/<leccion>-lectura.tex (un documento por lección).')
ap.add_argument('--extras', type=int, default=getattr(config, 'EXTRAS_LECTURA', 0),
                help='sorteos extra por mundo en las preguntas con setup sin "lectura"')
args = ap.parse_args()
SALIDA = Path('build/lectura')
SALIDA.mkdir(parents=True, exist_ok=True)
PREAMBULO = getattr(config, 'PREAMBULO_LECTURA', config.PREAMBULO_AMC)

_LECCION = re.compile(r'^(L-\d+)-')
grupos = {}
for ruta in preguntas(args.leccion):
    m = _LECCION.match(ruta.name)
    grupos.setdefault(m.group(1) if m else 'otras', []).append(ruta)

for grupo, rutas in sorted(grupos.items()):
    nombre = f'{grupo}-lectura'
    problemas = [load_problema(str(r)) for r in rutas]
    titulo = (f'Lección {int(grupo[2:])}: preguntas para leer' if grupo != 'otras'
              else 'Preguntas para leer')
    with tempfile.TemporaryDirectory() as tmp:        # QuizLectura escribe; make solo si cambia
        n = QuizLectura(nombre, tmp, problemas, aux_latex=PREAMBULO, titulo=titulo,
                        extras=args.extras)
        texto = (Path(tmp) / f'{nombre}.tex').read_text(encoding='utf-8')
    cambiado = escribe_si_cambia(SALIDA / f'{nombre}.tex', texto)
    print(f'  {nombre}.tex  ({len(problemas)} pregunta(s), {n} ejemplo(s)'
          f'{"" if cambiado else ", sin cambios"})')
