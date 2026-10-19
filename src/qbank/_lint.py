# Copyright (C) 2020-2026  Marcos Bujosa
#
# This file is part of calcprop-qbank.
#
# calcprop-qbank is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# calcprop-qbank is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Comprobador automático de preguntas (``qbank lint``).

Revisa un ``ProblemaTipo`` (objeto, dict o ruta a un JSON) y devuelve una
lista de :class:`Aviso` con nivel ``ERROR``, ``AVISO`` o ``INFO``. No modifica
ficheros ni compila LaTeX. Uso::

    from qbank import lint, tabla_mundos
    for a in lint("preguntas/L-01-ejemplo.json"):
        print(a)
    print(tabla_mundos("preguntas/L-01-ejemplo.json"))

o desde la línea de órdenes::

    python -m qbank.lint preguntas/*.json [--instances N] [--seed S] [--tabla] [--quiet]

Reglas (código del aviso entre paréntesis):

1. Garantía de mezcla (``mezcla``, ERROR): en toda variante y parte,
   ``1 <= correctas <= opciones - 1``, contando la opción por defecto si
   ``export.last_choice`` está activo (misma regla que ``AMCblock``). Si el
   número de opciones de una parte no es constante entre variantes
   (``opciones``, AVISO). Si una parte muestra al alumno menos de
   ``MIN_OPCIONES`` (3) opciones (``pocas-opciones``, AVISO): una lista de
   ``Cuestion`` sortea UNA por variante; para mostrar varias a la vez van
   como elementos consecutivos.
2. Número de variantes (``variantes``, AVISO): < 16 sin ``setup``; < 60 con
   ``setup`` (contando ``instances``). Más de 300 (INFO): un solo examcopy
   AMC con tantas variantes puede agotar la memoria de pdflatex.
3. Tabla texto → mundo (``constante``, AVISO/INFO; ``solape``, AVISO): una
   ``Cuestion`` verdadera (o falsa) en TODOS los mundos en que puede
   aparecer es candidata a distractor memorizable; dos ``Cuestion`` con el
   mismo texto en el mismo slot no deberían poder aparecer en un mismo mundo.
4. Negación sin ``unoDe`` (``negacion``, ERROR): ``-v('X')`` en una
   ``semantica`` o ``precond`` que se evalúa con ``test()`` solo puede
   deducirse si un ``Supuesto`` suelto declara ``unoDe(..., v('X'), ...)``.
5. Interpolación fallida (``interp``, ERROR): ``@{...}`` que sobrevive en el
   texto renderizado.
6. Etiquetas huérfanas (``huerfana``, AVISO; ``sin-uso``, INFO).
7. Estructura (``tipo``, ``nombre``, ``estructura``, ERROR; ``lista-1``,
   ``seed``, ``instances``, AVISO).
8. Texto (``texto``, AVISO): caracteres que rompen el paquete ``moodle``,
   delimitadores ``\\( \\)``, citas a números de lección, ``@{`` sin
   cerrar, dobles espacios, comillas simples, textos que parecen código
   ``lambda ns:`` (desde JSON no se evalúan).
9. Setup (``setup``, INFO): instancias necesarias para llegar a 60 variantes.
"""

import argparse as _argparse
import json as _json
import math as _math
import re as _re
import sys as _sys
from collections import defaultdict as _defaultdict
from dataclasses import dataclass as _dataclass
from pathlib import Path as _Path

from calcprop import Proposicion as _Proposicion, test as _test
from qbank._quiz import (Supuesto, Cuestion, ProblemaTipo, Marcador as _Marcador,
                         _normaliza_slot, _clasifica_slot, _ns_eval, _ns_interp,
                         validar_componentes as _validar_componentes)
from qbank._json import load_problema as _load_problema

__all__ = ['Aviso', 'lint', 'tabla_mundos', 'main', 'ERROR', 'AVISO', 'INFO']

ERROR, AVISO, INFO = 'ERROR', 'AVISO', 'INFO'
_ORDEN = {ERROR: 0, AVISO: 1, INFO: 2}

MIN_VARIANTES_SIN_SETUP = 16
MIN_VARIANTES_CON_SETUP = 60
MIN_OPCIONES            = 3       # opciones que debe ver el alumno en cada parte (con last_choice)
MAX_VARIANTES_AMC       = 300     # por encima, la vista alumno AMC en un solo examcopy agota pdflatex
_MAX_REPETIDOS = 5          # avisos idénticos que se listan antes de resumir


@_dataclass
class Aviso:
    nivel: str
    codigo: str
    mensaje: str
    donde: str = ''

    def __str__(self):
        s = f"{self.nivel:<5} [{self.codigo}] {self.mensaje}"
        return s + (f"  @ {self.donde}" if self.donde else '')


# ── Utilidades ────────────────────────────────────────────────────────────────

def _rec(s, n=60):
    """Recorta un texto a n caracteres para los mensajes."""
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + '…'


def _donde(i, j=None, texto=None):
    loc = f"comp {i}" if j is None else f"comp {i}[{j}]"
    return loc if texto is None else f"{loc}: {_rec(texto)}"


def _es_prop(f):
    return isinstance(f, _Proposicion)


def _atomos(f):
    """Conjunto de etiquetas v('X') que aparecen en una fórmula calcprop."""
    if not _es_prop(f):
        return set()
    if isinstance(f.data, list):
        return set().union(*(_atomos(x) for x in f.data[1:]))
    return {f.data}


def _atomos_negados(f):
    """Etiquetas que aparecen bajo algún operador 'not'."""
    if not _es_prop(f) or not isinstance(f.data, list):
        return set()
    if f.data[0] == 'not':
        return _atomos(f.data[1])
    return set().union(*(_atomos_negados(x) for x in f.data[1:]))


def _asertados(f, signo=True):
    """Literales (etiqueta, signo) que un Supuesto afirma sin condiciones:
    v('X'), -v('X') o una conjunción de ellos (no lo que aparece dentro de
    >>, |, unoDe…)."""
    if not _es_prop(f):
        return set()
    if isinstance(f.data, list):
        if f.data[0] == 'and':
            return set().union(*(_asertados(x, signo) for x in f.data[1:]))
        if f.data[0] == 'not':
            return _asertados(f.data[1], not signo)
        return set()
    return {(f.data, signo)}


def _args_unoDe(f):
    """Etiquetas listadas en un unoDe(...) de nivel superior."""
    if _es_prop(f) and isinstance(f.data, list) and f.data[0] == 'unoDe':
        return set().union(*(_atomos(x) for x in f.data[1:]))
    return set()


def _slots(p):
    """[(i, slot_normalizado, es_lista_en_origen)]"""
    return [(i, _normaliza_slot(x), isinstance(x, list)) for i, x in enumerate(p.e)]


# ── Carga ─────────────────────────────────────────────────────────────────────

def _carga(x, avisos):
    """Devuelve (ProblemaTipo | None, ruta | None)."""
    if isinstance(x, ProblemaTipo):
        return x, None
    ruta, d = None, None
    if isinstance(x, (str, _Path)):
        ruta = _Path(x)
        try:
            d = _json.loads(ruta.read_text(encoding='utf-8'))
        except Exception as e:                      # noqa: BLE001
            avisos.append(Aviso(ERROR, 'carga', f"no se puede leer el JSON: {e}"))
            return None, ruta
    elif isinstance(x, dict):
        d = x
    else:
        avisos.append(Aviso(ERROR, 'tipo',
                            f"se esperaba ProblemaTipo, dict o ruta; recibido {type(x).__name__}"))
        return None, None
    if not isinstance(d, dict):
        avisos.append(Aviso(ERROR, 'carga', "el JSON no es un objeto"))
        return None, ruta
    if 'banco' in d:
        avisos.append(Aviso(ERROR, 'tipo', "es un banco de problemas; lint revisa un problema por fichero"))
        return None, ruta
    tipo = d.get('tipo')
    if tipo != 'ProblemaTipo':
        avisos.append(Aviso(ERROR, 'tipo', f"tipo debe ser 'ProblemaTipo', no {tipo!r}"))
        return None, ruta
    try:
        p = _load_problema(d)
    except Exception as e:                          # noqa: BLE001
        avisos.append(Aviso(ERROR, 'carga', f"load_problema falla: {type(e).__name__}: {e}"))
        return None, ruta
    return p, ruta


# ── Regla 7: estructura ──────────────────────────────────────────────────────

def _regla_estructura(p, avisos, ruta):
    nombre = getattr(p, '_nombre', '') or ''
    if ruta is not None and nombre != ruta.stem:
        avisos.append(Aviso(ERROR, 'nombre',
                            f"'nombre' ({nombre!r}) no coincide con el fichero ({ruta.stem!r})"))
    if ':' in nombre:
        avisos.append(Aviso(ERROR, 'nombre', f"'nombre' contiene ':' ({nombre!r})"))

    try:
        _validar_componentes(p.e)        # listas vacías, mixtas o anidadas
    except ValueError as e:
        avisos.append(Aviso(ERROR, 'estructura', str(e)))
        return False

    for i, x in enumerate(p.e):
        if isinstance(x, list) and len(x) == 1:
            c = x[0]
            etiq = c if isinstance(c, str) else (c.e if isinstance(c.e, str) and c.e.strip()
                                                 else f"semantica={c.s!r}")
            avisos.append(Aviso(AVISO, 'lista-1',
                                "lista de un solo elemento; debería ir suelto",
                                _donde(i, None, etiq)))

    setup_str = getattr(p, '_setup_str', None)
    if p.setup is None or setup_str is not None:
        usa_random = bool(setup_str) and _re.search(r'\brandom\b', setup_str) is not None
        if usa_random and p.seed is None:
            avisos.append(Aviso(AVISO, 'seed', "el setup usa random pero no hay 'seed'"))
        if not usa_random and p.seed is not None:
            avisos.append(Aviso(AVISO, 'seed', "'seed' presente sin setup aleatorio"))

    export = p.export if isinstance(p.export, dict) else {}
    if not isinstance(p.export, dict):
        avisos.append(Aviso(ERROR, 'estructura', "'export' debe ser un objeto"))
    inst = export.get('instances', 1)
    if p.setup is None and isinstance(inst, int) and inst > 1:
        avisos.append(Aviso(AVISO, 'instances',
                            f"export.instances = {inst} sin setup: las instancias serían idénticas"))
    return True


# ── Regla 8: texto ───────────────────────────────────────────────────────────

_CHECKS_TEXTO = [
    (_re.compile(r'[°«»]'),
     "caracteres '°', '«' o '»' (rompen el paquete moodle; usa ^\\circ y ``...'')"),
    (_re.compile(r'(?<!\\)\\[()\[\]]'),
     "delimitadores \\( \\) \\[ \\] en vez de $...$ / $$...$$"),
    (_re.compile(r'lecci[oó]n\s*\d', _re.IGNORECASE),
     "cita un número de lección"),
    (_re.compile(r'@\{[^}]*(?:@\{|$)'),
     "'@{' sin cerrar"),
    (_re.compile(r'\S  +\S'),
     "doble espacio"),
    (_re.compile(r"(?<![\w\\'$})\]])'[^']+'(?!')"),
     "comillas simples '...' en vez de ``...''"),
    (_re.compile(r'^\s*lambda\s+ns\s*:'),
     "parece código lambda: desde JSON no se evalúa (usa @{var} y calcula el texto en setup)"),
]


def _textos(p):
    """[(donde, texto)] de todos los textos literales del problema."""
    out = []
    for i, slot, _ in _slots(p):
        for j, c in enumerate(slot):
            jj = j if len(slot) > 1 else None
            if isinstance(c, str):
                out.append((_donde(i, jj), c))
            else:
                if isinstance(c.e, str):
                    out.append((_donde(i, jj), c.e))
                if isinstance(c, Cuestion) and isinstance(c.x, str) and c.x:
                    out.append((_donde(i, jj) + ' exp', c.x))
    return out


def _regla_texto(p, avisos):
    for donde, texto in _textos(p):
        for rx, msg in _CHECKS_TEXTO:
            m = rx.search(texto)
            if m:
                avisos.append(Aviso(AVISO, 'texto', f"{msg}: {_rec(m.group(0), 30)!r}",
                                    f"{donde}: {_rec(texto)}"))


# ── Reglas 4 y 6: etiquetas ──────────────────────────────────────────────────

def _regla_etiquetas(p, avisos):
    en_supuestos   = set()      # etiquetas de cualquier Supuesto
    en_alternativa = set()      # etiquetas afirmadas (v('X')) por un Supuesto de una lista de 2+
    en_fijo        = set()      # etiquetas afirmadas (v('X')) por un Supuesto suelto
    negadas_sup    = set()      # etiquetas afirmadas negadas (-v('X')) por algún Supuesto
    unoDe          = set()      # etiquetas declaradas en unoDe de un Supuesto suelto
    usadas         = set()      # etiquetas usadas en semantica/precond de Cuestion o precond de Supuesto
    negadas        = []         # (etiqueta, donde) bajo 'not' en algo evaluado con test()

    for i, slot, _ in _slots(p):
        for j, c in enumerate(slot):
            if isinstance(c, str):
                continue
            jj = j if len(slot) > 1 else None
            if isinstance(c, Supuesto):
                en_supuestos |= _atomos(c.s)
                lits = _asertados(c.s)
                negadas_sup |= {x for x, pos in lits if not pos}
                if len(slot) > 1:
                    en_alternativa |= {x for x, pos in lits if pos}
                else:
                    en_fijo |= {x for x, pos in lits if pos}
                    unoDe |= _args_unoDe(c.s)
                testeadas = [('precond', c.p)]
            else:
                testeadas = [('semantica', c.s), ('precond', c.p)]
            for campo, f in testeadas:
                usadas |= _atomos(f)
                for x in _atomos_negados(f):
                    negadas.append((x, campo, _donde(i, jj, c.e)))

    for x, campo, donde in negadas:
        if x in negadas_sup:
            continue                      # algún Supuesto afirma -v(x) directamente
        if x in en_alternativa and x not in unoDe:
            avisos.append(Aviso(ERROR, 'negacion',
                                f"-v({x!r}) en {campo} nunca se deduce: falta un Supuesto suelto "
                                f"con unoDe(...) que incluya v({x!r})", donde))
        elif x in en_fijo and x not in en_alternativa and x not in unoDe:
            avisos.append(Aviso(AVISO, 'negacion',
                                f"-v({x!r}) en {campo} niega un Supuesto siempre presente: nunca es cierta",
                                donde))

    for x in sorted(usadas - en_supuestos):
        avisos.append(Aviso(AVISO, 'huerfana',
                            f"v({x!r}) no aparece en ningún Supuesto: nunca puede ser cierta"))
    for x in sorted(en_supuestos - usadas):
        avisos.append(Aviso(INFO, 'sin-uso',
                            f"v({x!r}) se declara en un Supuesto pero ninguna Cuestion la usa"))


# ── Reglas 1, 2, 5 y 9: variantes ────────────────────────────────────────────

_RE_INTERP = _re.compile(r'@\{[^}]*\}')


def _regla_variantes(p, avisos, instances, seed):
    export = p.export if isinstance(p.export, dict) else {}
    inst_export = export.get('instances', 1)
    inst = instances if instances is not None else inst_export
    inst = max(1, int(inst)) if p.setup is not None else 1
    last = bool(export.get('last_choice', False))

    try:
        variantes = list(p.por_partes(instances=inst, base_seed=seed, verbose=False))
    except Exception as e:                          # noqa: BLE001
        avisos.append(Aviso(ERROR, 'ejecucion', f"por_partes() falla: {type(e).__name__}: {e}"))
        return
    n = len(variantes)
    if n == 0:
        avisos.append(Aviso(ERROR, 'variantes', "no genera ninguna variante válida"))
        return

    opciones = _defaultdict(set)
    mezcla   = []
    interp   = {}
    for etiqueta, partes in variantes:
        for k, (enunciado, cuestiones) in enumerate(partes):
            reales    = len(cuestiones)
            correctas = sum(1 for c in cuestiones if c[1])
            if last:
                total, corr = reales + 1, correctas + (1 if correctas == 0 else 0)
            else:
                total, corr = reales, correctas
            opciones[k].add(total)
            if not (1 <= corr <= total - 1):
                mezcla.append((etiqueta, k, corr, total, enunciado))
            textos = [('enunciado', enunciado)]
            for c in cuestiones:
                textos.append(('cuestión', c[0]))
                if len(c) > 3 and c[3]:
                    textos.append(('exp', c[3]))
            for tipo, t in textos:
                for m in _RE_INTERP.findall(t):
                    interp.setdefault((m, tipo, _rec(t)), etiqueta)

    for etiqueta, k, corr, total, enunciado in mezcla[:_MAX_REPETIDOS]:
        avisos.append(Aviso(ERROR, 'mezcla',
                            f"variante {etiqueta}, parte {k + 1}: {corr} correctas de {total} opciones",
                            _rec(enunciado)))
    if len(mezcla) > _MAX_REPETIDOS:
        avisos.append(Aviso(ERROR, 'mezcla',
                            f"… y {len(mezcla) - _MAX_REPETIDOS} más ({len(mezcla)} de {n} variantes "
                            "violan 1 <= correctas <= opciones-1)"))
    for k, ns_ in sorted(opciones.items()):
        if len(ns_) > 1:
            avisos.append(Aviso(AVISO, 'opciones',
                                f"parte {k + 1}: el número de opciones varía entre variantes: "
                                f"{sorted(ns_)}"))
        if min(ns_) < MIN_OPCIONES:
            avisos.append(Aviso(AVISO, 'pocas-opciones',
                                f"parte {k + 1}: el alumno solo ve {min(ns_)} opción(es). Una lista "
                                "de Cuestion sortea UNA por variante: para mostrar varias a la vez "
                                "ponlas como elementos consecutivos (y/o activa export.last_choice)"))
    for (m, tipo, t), etiqueta in interp.items():
        avisos.append(Aviso(ERROR, 'interp',
                            f"{m} sin interpolar en {tipo} (variante {etiqueta})", t))

    if n > MAX_VARIANTES_AMC:
        avisos.append(Aviso(INFO, 'variantes',
                            f"{n} variantes: por encima de ~{MAX_VARIANTES_AMC} la vista alumno AMC "
                            "en un solo examcopy puede agotar la memoria de pdflatex"))
    if p.setup is None:
        if n < MIN_VARIANTES_SIN_SETUP:
            avisos.append(Aviso(AVISO, 'variantes',
                                f"solo {n} variantes (mínimo recomendado {MIN_VARIANTES_SIN_SETUP})"))
    else:
        if n < MIN_VARIANTES_CON_SETUP:
            avisos.append(Aviso(AVISO, 'variantes',
                                f"solo {n} variantes con instances={inst} "
                                f"(objetivo {MIN_VARIANTES_CON_SETUP})"))
        por_inst = n / inst
        necesarias = max(1, _math.ceil(MIN_VARIANTES_CON_SETUP / por_inst))
        avisos.append(Aviso(INFO, 'setup',
                            f"≈{por_inst:.0f} variantes por instancia; hacen falta {necesarias} "
                            f"instancias para ≥{MIN_VARIANTES_CON_SETUP} (export.instances = {inst_export})"))


# ── Regla 3: tabla texto → mundo ─────────────────────────────────────────────

def _mundos(p):
    """Evalúa cada Cuestion candidata en cada mundo alcanzable.

    Devuelve (mundos, filas):
      mundos : lista ordenada de claves (tupla de textos de Supuesto activos)
      filas  : [(i, j, texto, literal_bool, {mundo: {True|False|'rechazada'}})]
    """
    L        = [s for _, s, _ in _slots(p)]
    enun_idx = [i for i, s in enumerate(L) if _clasifica_slot(s) == 'enunciado']
    cues_idx = [i for i, s in enumerate(L) if _clasifica_slot(s) == 'cuestiones']
    combos   = _Marcador([len(L[i]) for i in enun_idx]) if enun_idx else [[]]

    mundos = []
    filas  = {}
    for combo in combos:
        ns, hip, textos, ok = (p.setup() if p.setup else {}), [], [], True
        for i, k in zip(enun_idx, combo):
            c = L[i][k]
            if not isinstance(c, Supuesto):
                continue
            if not _test(_ns_eval(c.p, ns), hip):
                ok = False
                break
            t = _ns_interp(_ns_eval(c.e, ns), ns).strip()
            if t:
                textos.append(t)
            hip.append(_ns_eval(c.s, ns))
        if not ok:
            continue
        mundo = tuple(textos)
        if mundo not in mundos:
            mundos.append(mundo)
        for i in cues_idx:
            for j, c in enumerate(L[i]):
                if (i, j) not in filas:
                    texto   = _ns_interp(_ns_eval(c.e, ns), ns)
                    literal = isinstance(c.s, bool)
                    filas[(i, j)] = (i, j, texto, literal, _defaultdict(set))
                vals = filas[(i, j)][4]
                if not _test(_ns_eval(c.p, ns), hip):
                    vals[mundo].add('rechazada')
                else:
                    vals[mundo].add(bool(_test(_ns_eval(c.s, ns), hip)))
    return mundos, [filas[k] for k in sorted(filas)]


def _regla_mundos(p, avisos):
    try:
        mundos, filas = _mundos(p)
    except Exception as e:                          # noqa: BLE001
        avisos.append(Aviso(ERROR, 'ejecucion', f"tabla de mundos falla: {type(e).__name__}: {e}"))
        return
    if len(mundos) < 2:
        return

    for i, j, texto, literal, vals in filas:
        alcanzables = {m: v - {'rechazada'} for m, v in vals.items() if v - {'rechazada'}}
        if len(alcanzables) < 2:
            continue
        union = set().union(*alcanzables.values())
        if union == {True} or union == {False}:
            valor = 'verdadera' if union == {True} else 'falsa'
            avisos.append(Aviso(INFO if literal else AVISO, 'constante',
                                f"{valor} en los {len(alcanzables)} mundos en que aparece"
                                + (" (semantica literal)" if literal else ""),
                                _donde(i, j, texto)))

    por_texto = _defaultdict(list)
    for i, j, texto, _, vals in filas:
        por_texto[(i, texto)].append((j, vals))
    for (i, texto), lst in por_texto.items():
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                ja, va = lst[a]
                jb, vb = lst[b]
                comunes = [m for m in mundos
                           if va[m] - {'rechazada'} and vb[m] - {'rechazada'}]
                if comunes:
                    avisos.append(Aviso(AVISO, 'solape',
                                        f"comp {i}[{ja}] y comp {i}[{jb}] tienen el mismo texto y "
                                        f"coinciden en {len(comunes)} mundo(s)", _rec(texto)))


def tabla_mundos(problema, ancho=50):
    """Tabla en texto plano: una fila por Cuestion, una columna por mundo.

    Celdas: ``V`` verdadera, ``F`` falsa, ``-`` rechazada por precond, ``?``
    valor no constante dentro del mismo mundo (solo posible con setup).
    """
    avisos = []
    p, _ = _carga(problema, avisos)
    if p is None:
        return '\n'.join(str(a) for a in avisos)
    mundos, filas = _mundos(p)
    if not mundos:
        return "(sin mundos alcanzables)"

    def celda(v):
        v = set(v)
        if v == {'rechazada'}:
            return '-'
        v -= {'rechazada'}
        if v == {True}:
            return 'V'
        if v == {False}:
            return 'F'
        return '?'

    out = ["Mundos:"]
    for k, m in enumerate(mundos, 1):
        out.append(f"  M{k}: {_rec(' / '.join(m) or '(sin supuestos)', 100)}")
    cab = ' '.join(f"M{k}" for k in range(1, len(mundos) + 1))
    etiq = [f"[{i}.{j}] {_rec(t, ancho)}" for i, j, t, _, _ in filas]
    w = max(len(e) for e in etiq) if etiq else 0
    out.append('')
    out.append(' ' * w + '  ' + cab)
    for (i, j, t, _, vals), e in zip(filas, etiq):
        celdas = ' '.join(f"{celda(vals.get(m, {'rechazada'})):>{len(f'M{k}')}}"
                          for k, m in enumerate(mundos, 1))
        out.append(f"{e:<{w}}  {celdas}")
    return '\n'.join(out)


# ── API ──────────────────────────────────────────────────────────────────────

def lint(problema, instances=None, seed=None):
    """Revisa un problema y devuelve la lista de :class:`Aviso` (errores primero).

    problema  : ProblemaTipo, dict JSON o ruta a un fichero JSON.
    instances : sobreescribe ``export.instances`` (solo con setup).
    seed      : semilla base para ``por_partes`` (por defecto la del problema).
    """
    avisos = []
    p, ruta = _carga(problema, avisos)
    if p is None:
        return avisos
    if not _regla_estructura(p, avisos, ruta):
        return avisos
    _regla_texto(p, avisos)
    _regla_etiquetas(p, avisos)
    _regla_variantes(p, avisos, instances, seed)
    _regla_mundos(p, avisos)
    avisos.sort(key=lambda a: _ORDEN[a.nivel])
    return avisos


def _resumen(avisos):
    ne = sum(a.nivel == ERROR for a in avisos)
    na = sum(a.nivel == AVISO for a in avisos)
    ni = sum(a.nivel == INFO for a in avisos)
    if ne == na == 0:
        return 'OK' + (f" ({ni} info)" if ni else '')
    return f"{ne} errores, {na} avisos" + (f", {ni} info" if ni else '')


def main(argv=None):
    ap = _argparse.ArgumentParser(
        prog='python -m qbank.lint',
        description="Comprueba preguntas qbank (JSON). Código de salida 1 si hay algún ERROR.")
    ap.add_argument('ficheros', nargs='+', metavar='FICHERO.json')
    ap.add_argument('--instances', type=int, default=None,
                    help="número de instancias (por defecto export.instances)")
    ap.add_argument('--seed', type=int, default=None, help="semilla base")
    ap.add_argument('--tabla', action='store_true',
                    help="imprime la tabla Cuestion × mundo aunque no haya avisos")
    ap.add_argument('--quiet', action='store_true',
                    help="omite los INFO y los ficheros sin avisos")
    args = ap.parse_args(argv)

    hay_error = False
    for f in args.ficheros:
        avisos = lint(f, instances=args.instances, seed=args.seed)
        hay_error |= any(a.nivel == ERROR for a in avisos)
        if args.quiet:
            avisos = [a for a in avisos if a.nivel != INFO]
            if not avisos and not args.tabla:
                continue
        print(f"{f}: {_resumen(avisos)}")
        for a in avisos:
            print('  ' + str(a))
        if args.tabla:
            print('\n'.join('  ' + l for l in tabla_mundos(f).splitlines()))
            print()
    return 1 if hay_error else 0


if __name__ == '__main__':
    _sys.exit(main())
