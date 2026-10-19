#!/usr/bin/env python3
"""Arregla el «<» dentro de las alternativas cloze de los XML de Moodle.

moodle.sty escribe «<» en modo matemático como &lt;, que es correcto en el
enunciado (el texto va en CDATA y Moodle lo guarda como HTML tal cual). Pero
Moodle aplica html_entity_decode a cada alternativa y a cada
retroalimentación de un bloque cloze ({N:MULTIRESPONSE_S:...}), así que
&lt; pasa a ser un «<» crudo en HTML, el navegador lo lee como apertura de
etiqueta y la opción se trunca («\\(F» sin cerrar). Dentro de los bloques
hay que escribir &amp;lt;, que tras la decodificación queda &lt; y MathJax
ve «<». El «>» no sufre esto (un «>» suelto es inofensivo en HTML).

Uso: fix_moodle_xml.py build/moodle/*-moodle.xml   (modifica en el sitio)
"""
import re
import sys
from pathlib import Path

BLOQUE = re.compile(r"\{\d+:[A-Z_]+:")


def arregla(texto):
    """Devuelve (texto arreglado, nº de sustituciones)."""
    out = []
    pos = 0
    n = 0
    while True:
        m = BLOQUE.search(texto, pos)
        if not m:
            out.append(texto[pos:])
            break
        # fin del bloque: primera «}» no escapada con «\»
        i = m.end()
        while i < len(texto):
            if texto[i] == "\\":
                i += 2
                continue
            if texto[i] == "}":
                break
            i += 1
        bloque = texto[m.start():i]
        n += bloque.count("&lt;")
        out.append(texto[pos:m.start()])
        out.append(bloque.replace("&lt;", "&amp;lt;"))
        pos = i
    return "".join(out), n


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    for nombre in argv:
        f = Path(nombre)
        nuevo, n = arregla(f.read_text(encoding="iso-8859-1"))
        if n:
            f.write_text(nuevo, encoding="iso-8859-1")
            print(f"  {f.name}: {n} «<» escapados dentro de bloques cloze "
                  "(arreglo que Moodle necesita; no es un error)")


if __name__ == "__main__":
    main(sys.argv[1:])
