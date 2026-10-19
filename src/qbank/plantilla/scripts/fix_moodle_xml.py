#!/usr/bin/env python3
"""Arregla los XML de Moodle que escribe el paquete LaTeX «moodle».

1. Codificación. El paquete declara `encoding="iso-8859-1"` pero escribe los
   caracteres no ASCII que no convierte en entidades (¿ ¡ “ ” … y los que
   vengan del texto) tal como están en el .tex, es decir, en UTF-8. Un
   importador que respete la declaración los leería como «Â¿». Se cambia la
   declaración a UTF-8, que es lo que de verdad contiene el fichero.

2. El «<» dentro de las alternativas cloze. moodle.sty escribe «<» en modo
   matemático como &lt;, que es correcto en el enunciado (el texto va en CDATA
   y Moodle lo guarda como HTML tal cual). Pero Moodle aplica
   html_entity_decode a cada alternativa y a cada retroalimentación de un
   bloque cloze ({N:MULTIRESPONSE_S:...}), así que &lt; pasa a ser un «<»
   crudo en HTML, el navegador lo lee como apertura de etiqueta y la opción
   se trunca («\\(F» sin cerrar). Dentro de los bloques hay que escribir
   &amp;lt;, que tras la decodificación queda &lt; y MathJax ve «<». El «>»
   no sufre esto (un «>» suelto es inofensivo en HTML).

Uso: fix_moodle_xml.py build/moodle/*-moodle.xml   (modifica en el sitio)
"""
import re
import sys
from pathlib import Path

BLOQUE = re.compile(r"\{\d+:[A-Z_]+:")
DECLARACION = re.compile(r'encoding="iso-8859-1"', re.IGNORECASE)


def decodifica(datos):
    """Texto del XML: UTF-8 (lo que escribe el paquete moodle) o, si no lo es, latin-1."""
    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return datos.decode("iso-8859-1")


def arregla_codificacion(texto):
    """Devuelve (texto con la declaración en UTF-8, True si cambió)."""
    nuevo, n = DECLARACION.subn('encoding="utf-8"', texto, count=1)
    return nuevo, bool(n)


def arregla(texto):
    """Devuelve (texto con «<» escapado dentro de los bloques cloze, nº de sustituciones)."""
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
        texto, cambio = arregla_codificacion(decodifica(f.read_bytes()))
        nuevo, n = arregla(texto)
        if cambio or n:
            f.write_text(nuevo, encoding="utf-8")
        if n:
            print(f"  {f.name}: {n} «<» escapados dentro de bloques cloze "
                  "(arreglo que Moodle necesita; no es un error)")


if __name__ == "__main__":
    main(sys.argv[1:])
