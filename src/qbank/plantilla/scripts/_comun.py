"""Utilidades compartidas por los scripts de scripts/.

- RAIZ: carpeta del proyecto (la que contiene preguntas/, scripts/ y config.py).
- preguntas(spec): rutas de preguntas/*.json, filtradas por lección.
- escribe_si_cambia(ruta, texto): escribe solo si el contenido cambia, para que
  make recompile únicamente lo que ha cambiado.
- documento_amc(nombre, explain): documento LaTeX autónomo que compila una pregunta.

Como programa imprime, uno por línea, los nombres de las preguntas
seleccionadas (lo usa el Makefile):   python scripts/_comun.py --leccion 2-3

Convención de nombres: preguntas/L-NN-Descripcion.json, con NN el número de la
lección (o tema, capítulo...). --leccion acepta "3", "3-6" o "1,3,5-7"; sin
filtro se procesan todas las preguntas, sigan o no la convención.
"""
import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import config  # noqa: E402  (config.py, en la raíz del proyecto)

_LECCION_RE = re.compile(r'^L-0*(\d+)-')


def _lecciones(spec):
    """"3", "3-6" o "1,3,5-7" -> {3}, {3, 4, 5, 6}, {1, 3, 5, 6, 7}."""
    out = set()
    for parte in spec.split(','):
        parte = parte.strip()
        if not parte:
            continue
        if '-' in parte:
            ini, fin = (int(x) for x in parte.split('-', 1))
            if fin < ini:
                raise ValueError(f'rango de lección inválido: {parte!r}')
            out.update(range(ini, fin + 1))
        else:
            out.add(int(parte))
    return out


def preguntas(spec=None):
    """Rutas de preguntas/*.json; si spec no está vacío, solo las de esas lecciones."""
    todas = sorted((RAIZ / 'preguntas').glob('*.json'))
    if not spec:
        return todas
    lecc = _lecciones(spec)
    return [p for p in todas
            if (m := _LECCION_RE.match(p.name)) and int(m.group(1)) in lecc]


def parser(descripcion):
    p = argparse.ArgumentParser(description=descripcion)
    p.add_argument('--leccion', '-l', metavar='SPEC', default=None,
                   help='solo las preguntas L-NN-* de esas lecciones: "3", "3-6" o "1,3,5-7"')
    return p


def escribe_si_cambia(ruta, texto):
    """Escribe texto en ruta solo si cambia. Devuelve True si escribió."""
    ruta = Path(ruta)
    if ruta.exists() and ruta.read_text(encoding='utf-8') == texto:
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding='utf-8')
    return True


def documento_amc(nombre, explain=False):
    """Documento LaTeX autónomo que compila los bloques \\element de <nombre>.tex
    con automultiplechoice en modo catálogo (una copia con todas las variantes)."""
    exclusiones = r'  \AMCtext{explain}{\textbf{Exclusiones:}}' + '\n' if explain else ''
    return (
        '\\documentclass[a4paper]{article}\n'
        '\\usepackage[utf8]{inputenc}\n'
        '\\usepackage[T1]{fontenc}\n'
        '\\usepackage{multicol}\n'
        '\\usepackage{graphicx}\n'
        + config.PREAMBULO_AMC.strip() + '\n'
        '\\usepackage[box,lang=ES,catalog]{automultiplechoice}\n'
        '\\makeatletter\n'
        '  \\def\\multiSymbole{}\n'
        "  \\AMCtext{catalog}{\\textit{Cat\\'alogo provisional}}\n"
        + exclusiones +
        '\\makeatother\n'
        '\\begin{document}\n'
        f'\\input{{{nombre}}}\n'
        '\\begin{examcopy}[1]\n'
        f'  \\insertgroup{{{nombre}}}\n'
        '\\end{examcopy}\n'
        '\\end{document}\n'
    )


if __name__ == '__main__':
    args = parser('Imprime los nombres de las preguntas seleccionadas.').parse_args()
    for ruta in preguntas(args.leccion):
        print(ruta.stem)
