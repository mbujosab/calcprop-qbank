#!/usr/bin/env python3
"""Fusiona los build/moodle/<pregunta>-moodle.xml de las preguntas que existen
en preguntas/ en build/moodle/_banco.xml, un único fichero importable en
Moodle con todo el banco. Los XML de preguntas que ya no están en preguntas/
se ignoran; si falta el XML de alguna pregunta, avisa (make moodle sin
LECCION los genera todos)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ, preguntas  # noqa: E402

SALIDA = RAIZ / 'build' / 'moodle'
DESTINO = SALIDA / '_banco.xml'

xmls, faltan = [], []
for ruta in preguntas():
    xml = SALIDA / f'{ruta.stem}-moodle.xml'
    (xmls if xml.exists() else faltan).append(xml)
if faltan:
    print(f'  AVISO: sin XML todavía (make moodle los genera): '
          + ', '.join(x.name.replace('-moodle.xml', '') for x in faltan))
if not xmls:
    raise SystemExit(f'No hay ningún *-moodle.xml de preguntas/ en {SALIDA}')

bloques = []
for f in xmls:
    m = re.search(r'<quiz>(.*?)</quiz>', f.read_text(encoding='iso-8859-1'), re.DOTALL)
    if m:
        bloques.append(m.group(1).strip())

DESTINO.write_text('<?xml version="1.0" encoding="iso-8859-1"?>\n<quiz>\n\n'
                   + '\n\n'.join(bloques) + '\n\n</quiz>\n', encoding='iso-8859-1')
print(f'  {len(xmls)} pregunta(s) fusionadas en {DESTINO.relative_to(RAIZ)}')
