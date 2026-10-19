#!/usr/bin/env python3
"""Fusiona los build/moodle/*-moodle.xml en build/moodle/_banco.xml, un único
fichero importable en Moodle con todas las preguntas del banco."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import RAIZ  # noqa: E402

SALIDA = RAIZ / 'build' / 'moodle'
DESTINO = SALIDA / '_banco.xml'

xmls = sorted(SALIDA.glob('*-moodle.xml'))
if not xmls:
    raise SystemExit(f'No hay ficheros *-moodle.xml en {SALIDA}')

bloques = []
for f in xmls:
    m = re.search(r'<quiz>(.*?)</quiz>', f.read_text(encoding='iso-8859-1'), re.DOTALL)
    if m:
        bloques.append(m.group(1).strip())

DESTINO.write_text('<?xml version="1.0" encoding="iso-8859-1"?>\n<quiz>\n\n'
                   + '\n\n'.join(bloques) + '\n\n</quiz>\n', encoding='iso-8859-1')
print(f'  {len(xmls)} fichero(s) fusionados en {DESTINO.relative_to(RAIZ)}')
