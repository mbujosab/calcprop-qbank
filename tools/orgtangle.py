# Copyright (C) 2026  Marcos Bujosa
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tangle noweb de los .org literate de qbank sin necesidad de Emacs.

Reproduce byte a byte lo que hace ``org-babel-tangle`` sobre CalcPropQuiz.org y
CalcPropExport.org (referencias ``<<nombre>>`` con sangría, varios bloques con el
mismo ``:tangle`` concatenados con una línea en blanco, subárboles ``COMMENT``
ignorados, referencias sin definir omitidas y blancos finales recortados).

Uso, desde la raíz del repositorio::

    python tools/orgtangle.py check            # ¿src/ coincide con los .org?  (salida 1 si no)
    python tools/orgtangle.py write            # regenera src/qbank/*.py desde los .org
    python tools/orgtangle.py informe          # qué bloques difieren y en cuántas líneas

Las fuentes de verdad son los .org: edítalos y ejecuta ``write`` (o tanglea
desde Emacs). ``tests/test_literate.py`` ejecuta ``check`` en la suite.
"""
import difflib
import re
import sys
from pathlib import Path

ORGS = ['CalcPropQuiz.org', 'CalcPropExport.org']

BEGIN = re.compile(r'^\s*#\+begin_src\s+python(.*)$', re.I)
END   = re.compile(r'^\s*#\+end_src\s*$', re.I)
NAME  = re.compile(r'^\s*#\+name:\s*(.+?)\s*$', re.I)
REF   = re.compile(r'^(\s*)<<(.+?)>>\s*$')
HEAD  = re.compile(r'^(\*+)\s+(COMMENT\b)?')


def parse(org_path):
    """Bloques ``python`` del fichero: dict(name, tangle, body, line)."""
    blocks, name, cur, comment_level = [], None, None, None
    for n, raw in enumerate(Path(org_path).read_text(encoding='utf-8').splitlines(), 1):
        h = HEAD.match(raw)
        if h and cur is None:
            lvl = len(h.group(1))
            if comment_level is not None and lvl <= comment_level:
                comment_level = None
            if h.group(2) and comment_level is None:
                comment_level = lvl
        if comment_level is not None and cur is None:
            continue
        if cur is None:
            m = NAME.match(raw)
            if m:
                name = m.group(1)
                continue
            m = BEGIN.match(raw)
            if m:
                t = re.search(r':tangle\s+(\S+)', m.group(1))
                cur = dict(name=name, body=[], line=n,
                           tangle=(t.group(1) if t and t.group(1) != 'no' else None))
                name = None
                continue
            if raw.strip():
                name = None
        elif END.match(raw):
            blocks.append(cur)
            cur = None
        else:
            cur['body'].append(raw)
    return blocks


def _expand(body, byname, prov, out, seen=()):
    for raw in body:
        m = REF.match(raw)
        if m and m.group(2) in byname:
            indent, ref = m.group(1), m.group(2)
            if ref in seen:
                raise RuntimeError(f"referencia circular: {ref}")
            for b in byname[ref]:
                sub = []
                _expand(b['body'], byname, ref, sub, seen + (ref,))
                out.extend((indent + l, p) for l, p in sub)
        elif m:
            continue                        # referencia sin definir: Emacs la omite
        else:
            out.append((raw, prov))


def tangle(org_path):
    """{target: [(línea, bloque_de_origen)]} para cada destino ``:tangle``."""
    blocks = parse(org_path)
    byname = {}
    for b in blocks:
        if b['name']:
            byname.setdefault(b['name'], []).append(b)
    targets = {}
    for b in blocks:
        if b['tangle']:
            out = []
            _expand(b['body'], byname, b['name'] or f"(bloque línea {b['line']})", out)
            while out and not out[-1][0].strip():
                out.pop()                   # Emacs recorta los blancos finales
            targets.setdefault(b['tangle'], []).append(out)
    result = {}
    for t, parts in targets.items():
        lines = []
        for i, part in enumerate(parts):
            if i:
                lines.append(('', '(separador)'))
            lines.extend(part)
        result[t] = lines
    return result


def texto(lines):
    return '\n'.join(l for l, _ in lines) + '\n'


def targets_src(repo):
    """{target: texto} de todos los destinos bajo src/ de los .org del repo."""
    res = {}
    for org in ORGS:
        for t, lines in tangle(Path(repo) / org).items():
            if t.startswith('src/'):
                res[t] = texto(lines)
    return res


def diferencias(repo):
    """[(target, unified_diff)] de los destinos cuyo contenido no coincide con src/."""
    out = []
    for t, contenido in targets_src(repo).items():
        p = Path(repo) / t
        actual = p.read_text(encoding='utf-8') if p.exists() else ''
        if actual != contenido:
            d = difflib.unified_diff(contenido.splitlines(), actual.splitlines(),
                                     f'{t} (tangle)', f'{t} (src)', lineterm='', n=1)
            out.append((t, '\n'.join(d)))
    return out


def informe(repo):
    for org in ORGS:
        for t, lines in tangle(Path(repo) / org).items():
            if not t.startswith('src/'):
                continue
            src = (Path(repo) / t).read_text(encoding='utf-8').splitlines()
            sm = difflib.SequenceMatcher(None, [l for l, _ in lines], src, autojunk=False)
            cambios = {}
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != 'equal':
                    bl = lines[min(i1, len(lines) - 1)][1]
                    c = cambios.setdefault(bl, [0, 0])
                    c[0] += i2 - i1
                    c[1] += j2 - j1
            print(f"== {t}: " + ('IDÉNTICO' if not cambios else
                                  f"{sum(a + b for a, b in cambios.values())} líneas afectadas"))
            for bl, (a, b) in cambios.items():
                print(f"   {bl:<70} -{a} +{b}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else 'check'
    repo = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    if cmd == 'check':
        difs = diferencias(repo)
        for t, d in difs:
            print(d)
            print()
        print('src/ coincide con los .org' if not difs else
              f'{len(difs)} fichero(s) de src/ NO coinciden con los .org')
        return 1 if difs else 0
    if cmd == 'write':
        for t, contenido in targets_src(repo).items():
            p = Path(repo) / t
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding='utf-8') != contenido:
                p.write_text(contenido, encoding='utf-8')
                print('escrito', t)
        return 0
    if cmd == 'informe':
        informe(repo)
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
