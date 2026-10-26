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
                                          [--patrones [N]] [--conocidos LISTA] [--decimal SEP]

Reglas (código del aviso entre paréntesis):

1. Garantía de mezcla (``mezcla``, ERROR): en toda variante y parte,
   ``1 <= correctas <= opciones - 1``, contando la opción por defecto si
   ``export.last_choice`` está activo (misma regla que ``AMCblock``). Si el
   número de opciones de una parte no es constante entre variantes, o una
   parte no tiene ninguna ``Cuestion`` (``opciones``, AVISO; esa parte no
   da además ``mezcla``). Si una parte muestra al alumno menos de
   ``MIN_OPCIONES`` (3) opciones (``pocas-opciones``, AVISO): una lista de
   ``Cuestion`` sortea UNA por variante; para mostrar varias a la vez van
   como elementos consecutivos.
2. Número de variantes (``variantes``): ninguna variante válida, ERROR;
   < 16 sin ``setup`` o < 60 con ``setup`` (contando ``instances``), AVISO;
   más de 300, INFO (un solo examcopy AMC con tantas variantes puede agotar
   la memoria de pdflatex; con lualatex, el motor de la plantilla, no). Si el ``setup`` o el recorrido lanzan una
   excepción, ERROR ``ejecucion``.
3. Tabla texto → mundo (``constante``, AVISO/INFO; ``solape``, AVISO): una
   ``Cuestion`` verdadera (o falsa) en TODOS los mundos en que puede
   aparecer es candidata a distractor memorizable (INFO si su semántica es
   el literal True/False, o una lambda con setup: la tabla usa un solo
   sorteo); dos ``Cuestion`` con el mismo texto en el mismo hueco no
   deberían poder aparecer en un mismo mundo.
4. Negación (``negacion``): ``-v('X')`` en una ``semantica`` o ``precond``
   que se evalúa con ``test()`` solo se deduce si algún ``Supuesto`` lo
   permite: un ``unoDe(..., v('X'), ...)`` a cualquier profundidad, o
   ``-v('X')`` afirmado o como consecuente (``>> -v('X')``). Si no, y
   ``v('X')`` es una alternativa de una lista, ERROR; si niega un
   ``Supuesto`` suelto (siempre presente), AVISO: nunca será cierta.
5. Interpolación fallida (``interp``, ERROR): ``@{...}`` que sobrevive en el
   texto renderizado (salvo el escape ``@@{x}``, que da «@{x}»).
6. Etiquetas huérfanas (``huerfana``, AVISO; ``sin-uso``, INFO). Si algún
   ``Supuesto`` tiene semántica lambda (inyecta fórmulas calculadas en el
   setup) las etiquetas no son visibles y la regla se degrada a un único
   INFO que lista las etiquetas no localizadas (incluidas las que fueran
   huérfanas de verdad: revísalas a mano).
7. Estructura (``carga``, ``tipo``, ``nombre``, ``estructura``, ERROR;
   ``lista-1``, ``seed``, ``instances``, AVISO). ``carga``: el JSON no se
   lee o ``load_problema`` falla. ``nombre``: no coincide con el fichero,
   lleva ``:`` o espacios (los scripts del banco ignoran esos ficheros).
   ``estructura``: listas vacías, mixtas o anidadas; ``seed`` que no es un
   entero (``true`` tampoco); ``export`` mal tipado (también
   ``export.amc_partes`` distinto de ``"juntas"`` o ``"separadas"``).
   Una pregunta de varias partes sin ``export.amc_partes`` da INFO
   ``amc-partes`` (en AMC saldrá en el modo ``"juntas"``).
8. Texto (``texto``): un ``%`` sin barra es ERROR (en LaTeX empieza un
   comentario y el PDF sale vacío o roto sin que pdflatex pare); son AVISO
   ``\\%`` dentro de ``$...$`` (Moodle lo pierde), ``°``/``«»`` y comillas
   rectas ``"`` (no existen en la codificación del paquete ``moodle`` o
   salen como ”), delimitadores ``\\( \\)`` y ``\\[ \\]``, citas a
   números de lección, ``@{`` sin cerrar, dobles espacios fuera de las
   fórmulas, comillas simples, textos que parecen código ``lambda ns:`` (desde JSON no se
   evalúan). Las dos reglas de ``%`` se aplican también al texto
   interpolado con unos sorteos del ``setup``.
9. Setup (``setup``, INFO): instancias necesarias para llegar a 60 variantes.
10. Vista de lectura (``lectura``): ``lectura`` que no es un objeto o
    ``lectura.cubrir`` que no es una lista de nombres, ERROR ``estructura``;
    una variable de ``cubrir`` que no define el ``setup`` (o ``cubrir`` sin
    ``setup``), ERROR; valores reales o más de ``MAX_COMBINACIONES_LECTURA``
    combinaciones de valores, AVISO (la vista de lectura se acota).
11. Patrones memorizables (``patron``, AVISO; solo con ``patrones=`` /
    ``--patrones``): lo que un alumno podría acertar sin leer el enunciado,
    muestreando las variantes con ``N_SEMILLAS_PATRONES`` sorteos del
    ``setup`` (uno si no lo hay). Una ``Cuestion`` de verdad variable pero
    «casi constante» (≥ 85 % de las veces el mismo valor), o constante en
    toda la muestra siendo lambda con ``setup`` (la regla 3 solo dio INFO);
    dentro de un tipo de frase (el texto sin cifras), una cifra cuyo valor
    separa por completo las V de las F, o cuya forma (entera o con
    decimales, múltiplo de 5 o de 10) predice la verdad; un rasgo
    superficial de la opción
    —una palabra, una cifra concreta, repetir una cifra del enunciado, tener
    la cifra mayor o menor del hueco, un intervalo ``[a, b]``, ser más larga
    que la mediana— que, con él o sin él, predice la verdad en ≥ 85 % de
    los casos, ≥ 15 puntos sobre la tasa base, con soporte en ambos lados y
    p-valor corregido < 0,01. Los rasgos que solo reúnen ``Cuestion``
    enteras no cuentan (eso ya lo dicen ``constante`` y «casi constante»),
    salvo un rasgo de cifras que reúne dos o más y deja fuera otras dos o
    más («las que escriben un intervalo son siempre falsas»). Son indicios:
    hay que leerlos y decidir.
12. Inventario de objetos (``inventario``, AVISO/INFO): un objeto concreto
    que una ``Cuestion`` nombra —``\\text{…}`` o ``\\mathrm{…}`` y sus
    productos ``\\text{a}\\cdot\\text{b}`` como una unidad, ``\\boldsymbol{…}``
    o ``\\mathbf{…}``, un símbolo con subíndice numérico (``\\hat\\beta_3``,
    ``x_2``)— y que el enunciado de esa misma variante no presenta (con
    unos sorteos del ``setup``); lo mismo para la ``exp``, que además puede
    apoyarse en lo que nombra su propia ``Cuestion``. Es INFO si la propia
    opción lo presenta («X (definición)», «X, que …», «en lugar de X»). La
    notación del curso que no hace falta presentar se declara con
    ``conocidos=`` / ``--conocidos`` (en un proyecto, ``NOTACION_CONOCIDA``
    de ``config.py``). Una secuencia ``\\beta_1,\\dots,\\beta_k`` presenta
    todos los subíndices del rango, y un símbolo escrito dentro de una
    hipótesis de la propia opción (``H_0\\!:\\beta_3=0``) cuenta como
    presentado. No ve los objetos nombrados en prosa («el modelo sin
    restringir»).
13. Longitud de las opciones (``longitud``, AVISO): una alternativa
    claramente más larga (o más corta) que las que se muestran con ella
    —longitud *visible*, sin ``$``, llaves ni nombres de macros; el doble
    y ``_MIN_DIF_LONGITUD`` caracteres más que una alternativa de cada otro
    hueco, en al menos la mitad de las combinaciones— es un rasgo
    memorable; si en su hueco
    no tiene una pareja de longitud parecida (razón ≤ 1,3, o menos de
    ``_MIN_DIF_LONGITUD`` caracteres de diferencia) y valor contrario, «la
    opción larga es la verdadera». Se comprueba mundo a
    mundo con unos sorteos del ``setup``; una opción que destaca unas veces
    como verdadera y otras como falsa es su propia pareja. Y si, entre lo
    que se muestra en esa parte, la claramente más corta (o más larga) es
    verdadera entre el 30 % y el 70 % de las veces, los avisos de ese lado
    callan: no hay nada que aprender.
14. Verdadera sin gemela (``gemela``, AVISO): una alternativa verdadera
    siempre que aparece, con contenido calculable (una cifra, o una fórmula
    con una igualdad, desigualdad u operación), en un hueco donde ninguna
    falsa comparte su esqueleto: el mismo texto con otras cifras (símbolos
    iguales) o con otros símbolos (cifras iguales), ignorando el orden, con
    «mayor»/«menor», ``+``/``-``, ``<``/``>`` y la negación identificados;
    basta con que la falsa comparta el 80 % de los tokens (una coletilla no
    rompe la gemela). No cuentan como cifra los subíndices, los rótulos
    «(1)», el 0 y el 1 ni un porcentaje que el enunciado ya da; y una
    verdadera que solo repite cifras del enunciado no avisa si una falsa
    del hueco lleva alguna de ellas (la cifra no delata). Una fórmula
    dentro de una frase es INFO, salvo que opere con dos o más objetos del
    enunciado («pasa a ser $\\hat\\beta_2+\\hat\\beta_3$»): entonces es AVISO.
    Sin gemela, el alumno la marca sin comprobar nada.
"""

import argparse as _argparse
import json as _json
import itertools as _itertools
import math as _math
import random as _random
import re as _re
import sys as _sys
from collections import defaultdict as _defaultdict, Counter as _Counter
from dataclasses import dataclass as _dataclass
from pathlib import Path as _Path

from calcprop import Proposicion as _Proposicion, test as _test
from qbank._quiz import (Supuesto, Cuestion, ProblemaTipo, Marcador as _Marcador,
                         _normaliza_slot, _clasifica_slot, _ns_eval, _ns_interp, _siembra,
                         _plan_partes, validar_componentes as _validar_componentes)
from qbank._json import load_problema as _load_problema

__all__ = ['Aviso', 'lint', 'tabla_mundos', 'main', 'ERROR', 'AVISO', 'INFO']

ERROR, AVISO, INFO = 'ERROR', 'AVISO', 'INFO'
_ORDEN = {ERROR: 0, AVISO: 1, INFO: 2}

MIN_VARIANTES_SIN_SETUP = 16
MIN_VARIANTES_CON_SETUP = 60
AMC_PARTES              = ('juntas', 'separadas')  # valores de export.amc_partes
MIN_OPCIONES            = 3       # opciones que debe ver el alumno en cada parte (con last_choice)
MAX_VARIANTES_AMC       = 300     # por encima, la vista alumno AMC en un solo examcopy agota pdflatex
MAX_COMBINACIONES_LECTURA = 24    # combinaciones de lectura.cubrir a partir de las cuales se avisa
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


def _atomos_unoDe(f):
    """Etiquetas listadas en cualquier unoDe(...) de la fórmula, a cualquier
    profundidad (p. ej. dentro de una conjunción)."""
    if not _es_prop(f) or not isinstance(f.data, list):
        return set()
    if f.data[0] == 'unoDe':
        return set().union(*(_atomos(x) for x in f.data[1:]))
    return set().union(*(_atomos_unoDe(x) for x in f.data[1:]))


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
    fichero = ruta.name if ruta is not None else ''
    if any(ch.isspace() for ch in nombre + fichero):
        quien = f"el fichero ({fichero!r})" if any(ch.isspace() for ch in fichero) else f"'nombre' ({nombre!r})"
        avisos.append(Aviso(ERROR, 'nombre',
                            f"{quien} lleva espacios: rompen make y LaTeX, y los scripts del "
                            "banco ignoran ese fichero al exportar"))

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

    if p.seed is not None and (not isinstance(p.seed, int) or isinstance(p.seed, bool)):
        avisos.append(Aviso(ERROR, 'estructura', f"'seed' debe ser un entero, no {p.seed!r}"))

    export = p.export if isinstance(p.export, dict) else {}
    if not isinstance(p.export, dict):
        avisos.append(Aviso(ERROR, 'estructura', "'export' debe ser un objeto"))
    inst = export.get('instances', 1)
    if not isinstance(inst, int) or isinstance(inst, bool) or inst < 1:
        avisos.append(Aviso(ERROR, 'estructura',
                            f"export.instances debe ser un entero >= 1, no {inst!r}"))
    elif p.setup is None and inst > 1:
        avisos.append(Aviso(AVISO, 'instances',
                            f"export.instances = {inst} sin setup: las instancias serían idénticas"))
    for clave in ('last_choice',):
        if clave in export and not isinstance(export[clave], bool):
            avisos.append(Aviso(ERROR, 'estructura',
                                f"export.{clave} debe ser true o false (sin comillas), no {export[clave]!r}"))
    cols = export.get('cols', 1)
    if not isinstance(cols, int) or isinstance(cols, bool) or cols < 1:
        avisos.append(Aviso(ERROR, 'estructura', f"export.cols debe ser un entero >= 1, no {cols!r}"))
    modo = export.get('amc_partes', 'juntas')
    if modo not in AMC_PARTES:
        avisos.append(Aviso(ERROR, 'estructura',
                            f"export.amc_partes debe ser {' o '.join(map(repr, AMC_PARTES))}, no {modo!r}"))
    elif 'amc_partes' not in export:
        try:
            n_partes = len(_huecos_comp(p))
        except Exception:
            n_partes = 0
        if n_partes > 1:
            avisos.append(Aviso(INFO, 'amc-partes',
                                f"{n_partes} partes sin export.amc_partes: en AMC saldrán como una "
                                "sola pregunta con varios bloques de casillas ('juntas'); "
                                "'separadas' las numera como preguntas consecutivas"))
    return True


# ── Regla 8: texto ───────────────────────────────────────────────────────────

def _sin_matematicas(texto):
    """El texto con cada fórmula ($...$ o $$...$$) sustituida por una X: dentro
    de ellas LaTeX ignora los espacios."""
    return _re.sub(r'\$\$.*?\$\$|\$[^$]*\$', 'X', texto, flags=_re.DOTALL)


def _pct_en_matematicas(texto):
    """'\\%' dentro de $...$ (el paquete moodle lo deja como '%' y MathJax lo
    toma por comentario). Devuelve el fragmento o None."""
    partes = _re.split(r'(?<!\\)\$', texto.replace('$$', '$'))
    for seg in partes[1::2]:
        if '\\%' in seg:
            return '$' + seg + '$'
    return None


# (nivel, comprobación, mensaje): la comprobación es una expresión regular o
# una función que devuelve el fragmento problemático (o None).
_CHECKS_TEXTO = [
    (ERROR, _re.compile(r'(?<!\\)%'),
     "'%' sin barra: en LaTeX empieza un comentario y se pierde el resto de la línea "
     "(escribe \\%; en Python, dentro de una cadena r\"...\" o como \\\\%)"),
    (AVISO, _pct_en_matematicas,
     "'\\%' dentro de $...$: en Moodle se pierde (ponlo fuera de los dólares: al $5$\\,\\%)"),
    (AVISO, _re.compile(r'[°«»]'),
     "'°', '«' o '»' no existen en la codificación del paquete moodle: grados con ^\\circ; "
     "comillas con ``...'' (dos acentos graves para abrir, dos apóstrofos para cerrar)"),
    (AVISO, _re.compile(r'(?<!\\)"'),
     "comillas rectas \" (salen como ” en los dos lados): usa ``...'' "
     "(dos acentos graves para abrir, dos apóstrofos para cerrar)"),
    (AVISO, _re.compile(r'(?<!\\)\\[()\[\]]'),
     "delimitadores \\( \\) \\[ \\] en vez de $...$ / $$...$$"),
    (AVISO, _re.compile(r'\blecci[oó]n\s*\d', _re.IGNORECASE),
     "cita un número de lección"),
    (AVISO, _re.compile(r'@\{[^}]*(?:@\{|$)'),
     "'@{' sin cerrar"),
    (AVISO, lambda t: (m := _re.search(r'\S  +\S', _sin_matematicas(t))) and m.group(0),
     "doble espacio"),
    (AVISO, _re.compile(r"(?<![\w\\'$})\]|])'[^']+'(?!')"),
     "comillas simples '...' en vez de ``...''"),
    (AVISO, _re.compile(r'^\s*lambda\s+ns\s*:'),
     "parece código lambda: desde JSON no se evalúa (usa @{var} y calcula el texto en setup)"),
]


_CHECKS_PCT = _CHECKS_TEXTO[:2]   # los de '%': se aplican también al texto interpolado
_N_SORTEOS_TEXTO = 20             # sorteos del setup con que se interpolan los textos


def _aplica(check, texto):
    """Fragmento problemático que encuentra una comprobación de texto, o None."""
    if callable(check):
        return check(texto)
    m = check.search(texto)
    return m.group(0) if m else None


def _sorteos_ns(p, n=_N_SORTEOS_TEXTO):
    """Hasta n espacios de nombres del setup, sembrados con ``seed`` (o 42) como
    la tabla de mundos, sin alterar el estado de los generadores aleatorios.
    Si el setup falla devuelve los que haya: la regla de variantes ya lo
    informa (``ejecucion``)."""
    if p.setup is None:
        return []
    import random as _random
    estado = _random.getstate()
    try:
        import numpy as _np
        estado_np = _np.random.get_state()
    except ImportError:
        _np = None
    out = []
    try:
        _siembra(p.seed if p.seed is not None else 42)
        for _ in range(n):
            out.append(p.setup())
    except Exception:                               # noqa: BLE001
        pass
    finally:
        _random.setstate(estado)
        if _np is not None:
            _np.random.set_state(estado_np)
    return out


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
    textos = _textos(p)
    nss = _sorteos_ns(p) if any('@' in t for _, t in textos) else []
    for donde, texto in textos:
        for nivel, check, msg in _CHECKS_TEXTO:
            hit = _aplica(check, texto)
            if hit:
                avisos.append(Aviso(nivel, 'texto', f"{msg}: {_rec(hit, 30)!r}",
                                    f"{donde}: {_rec(texto)}"))
        if '@' not in texto:
            continue
        # Un '%' que llega con @{var} (p. ej. pct = f'{p} %' en el setup) solo
        # se ve en el texto interpolado; si el literal ya da el aviso, no se repite.
        for nivel, check, msg in _CHECKS_PCT:
            if _aplica(check, texto):
                continue
            for ns in nss:
                t = _ns_interp(texto, ns)
                hit = _aplica(check, t)
                if hit:
                    avisos.append(Aviso(nivel, 'texto',
                                        f"{msg}: {_rec(hit, 30)!r} (en el texto interpolado)",
                                        f"{donde}: {_rec(t)}"))
                    break
def _regla_lectura(p, avisos):
    lectura = getattr(p, 'lectura', None)
    if not lectura:
        return
    if not isinstance(lectura, dict):
        avisos.append(Aviso(ERROR, 'estructura',
                            "'lectura' debe ser un objeto, p. ej. {\"cubrir\": [\"x\"]}"))
        return
    raras = sorted(set(lectura) - {'cubrir'})
    if raras:
        avisos.append(Aviso(AVISO, 'lectura', f"claves desconocidas en 'lectura': {raras}"))
    cubrir = lectura.get('cubrir', [])
    if not isinstance(cubrir, list) or not all(isinstance(x, str) for x in cubrir):
        avisos.append(Aviso(ERROR, 'estructura',
                            "lectura.cubrir debe ser una lista de nombres de variables del setup"))
        return
    if not cubrir:
        return
    if p.setup is None:
        avisos.append(Aviso(ERROR, 'lectura', "lectura.cubrir sin setup: no hay variables que cubrir"))
        return
    nss = _sorteos_ns(p)
    if not nss:                       # el setup falla: lo informa la regla de variantes
        return
    combinaciones = 1
    for var in cubrir:
        if not all(var in ns for ns in nss):
            avisos.append(Aviso(ERROR, 'lectura', f"lectura.cubrir: {var!r} no está en el setup"))
            continue
        valores = [ns[var] for ns in nss]
        if any(isinstance(x, float) or type(x).__name__.startswith('float') for x in valores):
            avisos.append(Aviso(AVISO, 'lectura',
                                f"lectura.cubrir: {var!r} toma valores reales; cada sorteo será "
                                "una combinación nueva (sortea un valor discreto en el setup)"))
        combinaciones *= len({repr(x) for x in valores})
    if combinaciones > MAX_COMBINACIONES_LECTURA:
        avisos.append(Aviso(AVISO, 'lectura',
                            f"lectura.cubrir: al menos {combinaciones} combinaciones de valores; "
                            "la vista de lectura se acota a unos 40 ejemplos por pregunta"))


# ── Reglas 4 y 6: etiquetas ──────────────────────────────────────────────────

def _regla_etiquetas(p, avisos):
    en_supuestos   = set()      # etiquetas de cualquier Supuesto
    en_alternativa = set()      # etiquetas afirmadas (v('X')) por un Supuesto de una lista de 2+
    en_fijo        = set()      # etiquetas afirmadas (v('X')) por un Supuesto suelto
    negadas_sup    = set()      # etiquetas afirmadas negadas (-v('X')) por algún Supuesto
    unoDe          = set()      # etiquetas declaradas en unoDe de un Supuesto suelto
    usadas         = set()      # etiquetas usadas en semantica/precond de Cuestion o precond de Supuesto
    negadas        = []         # (etiqueta, donde) bajo 'not' en algo evaluado con test()
    sup_lambda     = False      # algún Supuesto tiene semántica lambda (etiquetas no visibles)
    cues_lambda    = False      # alguna Cuestion tiene semántica o precond lambda
    deducibles     = set()      # etiquetas cuya negación puede deducirse de algún Supuesto:
                                # aparecen negadas (a cualquier profundidad, p. ej. como
                                # consecuente de >>) o dentro de un unoDe (a cualquier profundidad)

    for i, slot, _ in _slots(p):
        for j, c in enumerate(slot):
            if isinstance(c, str):
                continue
            jj = j if len(slot) > 1 else None
            if isinstance(c, Supuesto):
                if callable(c.s):
                    sup_lambda = True
                en_supuestos |= _atomos(c.s)
                deducibles |= _atomos_negados(c.s) | _atomos_unoDe(c.s)
                lits = _asertados(c.s)
                negadas_sup |= {x for x, pos in lits if not pos}
                if len(slot) > 1:
                    en_alternativa |= {x for x, pos in lits if pos}
                else:
                    en_fijo |= {x for x, pos in lits if pos}
                    unoDe |= _args_unoDe(c.s)
                testeadas = [('precond', c.p)]
            else:
                if callable(c.s) or callable(c.p):
                    cues_lambda = True
                testeadas = [('semantica', c.s), ('precond', c.p)]
            for campo, f in testeadas:
                usadas |= _atomos(f)
                for x in _atomos_negados(f):
                    negadas.append((x, campo, _donde(i, jj, c.e)))

    for x, campo, donde in negadas:
        if x in negadas_sup or x in deducibles:
            continue                      # algún Supuesto permite deducir -v(x)
        if x in en_alternativa:
            avisos.append(Aviso(ERROR, 'negacion',
                                f"-v({x!r}) en {campo} nunca se deduce: falta un Supuesto suelto "
                                f"con unoDe(...) que incluya v({x!r})", donde))
        elif x in en_fijo:
            avisos.append(Aviso(AVISO, 'negacion',
                                f"-v({x!r}) en {campo} niega un Supuesto siempre presente: nunca es cierta",
                                donde))

    if sup_lambda and usadas - en_supuestos:
        avisos.append(Aviso(INFO, 'huerfana',
                            "algún Supuesto tiene semántica lambda: no se comprueban las etiquetas "
                            f"huérfanas ({', '.join(sorted(usadas - en_supuestos))})"))
    elif not sup_lambda:
        for x in sorted(usadas - en_supuestos):
            avisos.append(Aviso(AVISO, 'huerfana',
                                f"v({x!r}) no aparece en ningún Supuesto: nunca puede ser cierta"))
    if not cues_lambda:                   # una lambda puede usar etiquetas que no vemos
        for x in sorted(en_supuestos - usadas):
            avisos.append(Aviso(INFO, 'sin-uso',
                                f"v({x!r}) se declara en un Supuesto pero ninguna Cuestion la usa"))


# ── Reglas 1, 2, 5 y 9: variantes ────────────────────────────────────────────

_RE_INTERP = _re.compile(r'@\{[^}]*\}')


def _regla_variantes(p, avisos, instances, seed):
    export = p.export if isinstance(p.export, dict) else {}
    inst_export = export.get('instances', 1)
    inst = instances if instances is not None else inst_export
    try:
        inst = max(1, int(inst)) if p.setup is not None else 1
    except (TypeError, ValueError):             # ya avisado por la regla de estructura
        inst = 1
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
    n_reales = _defaultdict(set)
    mezcla   = []
    interp   = {}
    # @@{x} es el escape documentado: se renderiza como «@{x}» a propósito
    escapadas = {m[1:] for _, t in _textos(p) for m in _re.findall(r'@@\{[^}]*\}', t)}
    for etiqueta, partes in variantes:
        for k, (enunciado, cuestiones) in enumerate(partes):
            reales    = len(cuestiones)
            correctas = sum(1 for c in cuestiones if c[1])
            if last:
                total, corr = reales + 1, correctas + (1 if correctas == 0 else 0)
            else:
                total, corr = reales, correctas
            opciones[k].add(total)
            n_reales[k].add(reales)
            if reales and not (1 <= corr <= total - 1):    # parte vacía: solo AVISO opciones
                mezcla.append((etiqueta, k, corr, total, enunciado))
            textos = [('enunciado', enunciado)]
            for c in cuestiones:
                textos.append(('cuestión', c[0]))
                if len(c) > 3 and c[3]:
                    textos.append(('exp', c[3]))
            for tipo, t in textos:
                for m in _RE_INTERP.findall(t):
                    if m not in escapadas:
                        interp.setdefault((m, tipo, _rec(t)), etiqueta)

    for etiqueta, k, corr, total, enunciado in mezcla[:_MAX_REPETIDOS]:
        avisos.append(Aviso(ERROR, 'mezcla',
                            f"variante {etiqueta}, parte {k + 1}: {corr} correctas de {total} opciones",
                            _rec(enunciado)))
    if len(mezcla) > _MAX_REPETIDOS:
        n_var = len({et for et, *_ in mezcla})
        avisos.append(Aviso(ERROR, 'mezcla',
                            f"… y {len(mezcla) - _MAX_REPETIDOS} más ({n_var} de {n} variantes "
                            "violan 1 <= correctas <= opciones-1)"))
    for k, ns_ in sorted(opciones.items()):
        if len(ns_) > 1:
            avisos.append(Aviso(AVISO, 'opciones',
                                f"parte {k + 1}: el número de opciones varía entre variantes: "
                                f"{sorted(ns_)}"))
        if min(n_reales[k]) == 0:
            avisos.append(Aviso(AVISO, 'opciones',
                                f"parte {k + 1}: sin ninguna Cuestion en alguna variante (un texto "
                                "suelto tras la última Cuestion abre una parte vacía)"))
        elif min(ns_) < MIN_OPCIONES:
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
                            "en un solo examcopy puede agotar la memoria de pdflatex "
                            "(compila con lualatex, como el Makefile de la plantilla)"))
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
    if p.setup is not None:                 # tabla reproducible
        _siembra(p.seed if p.seed is not None else 42)

    mundos = []
    filas  = {}
    for combo in combos:
        ns, hip, pos, textos, ok = (p.setup() if p.setup else {}), [], [], [], True
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
            pos.append(i)                   # para usar solo las hipótesis anteriores
        if not ok:
            continue
        mundo = tuple(textos)
        if mundo not in mundos:
            mundos.append(mundo)
        for i in cues_idx:
            # Como el motor: una Cuestion solo ve los Supuesto que la preceden
            hip_i = [h for h, q in zip(hip, pos) if q < i]
            for j, c in enumerate(L[i]):
                if (i, j) not in filas:
                    texto   = _ns_interp(_ns_eval(c.e, ns), ns)
                    literal = isinstance(c.s, bool)
                    filas[(i, j)] = (i, j, texto, literal, _defaultdict(set))
                vals = filas[(i, j)][4]
                if not _test(_ns_eval(c.p, ns), hip_i):
                    vals[mundo].add('rechazada')
                else:
                    vals[mundo].add(bool(_test(_ns_eval(c.s, ns), hip_i)))
    return mundos, [filas[k] for k in sorted(filas)]


def _regla_mundos(p, avisos):
    try:
        mundos, filas = _mundos(p)
    except Exception as e:                          # noqa: BLE001
        avisos.append(Aviso(ERROR, 'ejecucion', f"tabla de mundos falla: {type(e).__name__}: {e}"))
        return
    if len(mundos) < 2:
        return

    L = [s for _, s, _ in _slots(p)]
    for i, j, texto, literal, vals in filas:
        alcanzables = {m: v - {'rechazada'} for m, v in vals.items() if v - {'rechazada'}}
        if len(alcanzables) < 2:
            continue
        union = set().union(*alcanzables.values())
        if union == {True} or union == {False}:
            valor = 'verdadera' if union == {True} else 'falsa'
            # Una semantica lambda depende del setup y la tabla usa un solo sorteo:
            # en otras variantes puede cambiar de valor, así que solo se informa.
            lam = p.setup is not None and callable(L[i][j].s)
            nota = (" (semantica literal)" if literal else
                    " en el sorteo de la tabla (semantica lambda: depende del setup y puede "
                    "cambiar en otras variantes; compruébalo con la vista profe)" if lam else "")
            avisos.append(Aviso(INFO if literal or lam else AVISO, 'constante',
                                f"{valor} en los {len(alcanzables)} mundos en que aparece" + nota,
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


def tabla_mundos(problema, ancho=50, linea=None, elipsis='…'):
    """Tabla en texto plano: una fila por Cuestion, una columna por mundo.

    Celdas: ``V`` verdadera, ``F`` falsa, ``-`` rechazada por precond, ``?``
    valor no constante dentro del mismo mundo (solo posible con setup).
    ``ancho`` recorta el texto de cada Cuestion; con ``linea`` (caracteres
    por línea) el recorte se calcula para que cada fila ocupe ``linea``.
    ``elipsis`` marca el texto recortado (en LaTeX ``…`` ocupa tres
    caracteres de ancho y desalinea las columnas: allí se pasa ``'...'``).
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

    def rec(t, n):
        t = ' '.join(str(t).split())
        return t if len(t) <= n else t[:n - len(elipsis)].rstrip() + elipsis

    out = ["Mundos:"]
    for k, m in enumerate(mundos, 1):
        n = 100 if linea is None else max(20, linea - len(f"  M{k}: "))
        out.append(f"  M{k}: {rec(' / '.join(m) or '(sin supuestos)', n)}")
    cab = ' '.join(f"M{k}" for k in range(1, len(mundos) + 1))
    if linea is not None:
        pre = max((len(f"[{i}.{j}] ") for i, j, _, _, _ in filas), default=0)
        ancho = max(20, linea - pre - 2 - len(cab))
    etiq = [f"[{i}.{j}] {rec(t, ancho)}" for i, j, t, _, _ in filas]
    w = max(len(e) for e in etiq) if etiq else 0
    out.append('')
    out.append(' ' * w + '  ' + cab)
    for (i, j, t, _, vals), e in zip(filas, etiq):
        celdas = ' '.join(f"{celda(vals.get(m, {'rechazada'})):>{len(f'M{k}')}}"
                          for k, m in enumerate(mundos, 1))
        out.append(f"{e:<{w}}  {celdas}")
    return '\n'.join(out)


# ── Regla 11: patrones memorizables ──────────────────────────────────────────

N_SEMILLAS_PATRONES = 40     # sorteos del setup que muestrea --patrones (uno si no hay setup)
_MIN_CASOS_PATRON   = 8      # casos mínimos para analizar un hueco, una Cuestion o un tipo de frase
_SOPORTE_PATRON     = 0.10   # cada lado de un rasgo: al menos esta fracción de los casos (y 3)
_PRECISION_PATRON   = 0.85   # acierto mínimo de un rasgo (y de una Cuestion «casi constante»)
_MEJORA_PATRON      = 0.15   # … y al menos esta mejora sobre la tasa base del hueco
_P_PATRON           = 0.01   # p-valor hipergeométrico, corregido por el número de rasgos probados
_MAX_PATRONES_HUECO = 3      # rasgos que se listan por hueco
_MIN_LETRAS_PALABRA = 4      # palabras más cortas (artículos, preposiciones…) no son señal
_ORDEN_FORMAS = ('entera', 'con decimales', 'múltiplo de 10', 'múltiplo de 5')   # de la forma más simple a la más fina

_RE_SUBIND  = _re.compile(r'[_^](\{[^}]*\}|\\?\w)')     # subíndices y exponentes: no se leen como cifras
_RE_NOTACION = _re.compile(r'\\(?:boldsymbol|mathbf|mathbb|mathcal|mathrm|mathit|bm|symbf|textbf|vec|hat|bar|tilde)'
                           r'\s*(?:\{\s*\d+\s*\}|\d)')   # \boldsymbol 1, \mathbf{1}: notación, no cifras
_RE_CMD     = _re.compile(r'\\[A-Za-z]+')
_RE_FRAC    = _re.compile(r'(-?)\\[dt]?frac\{(-?\d+(?:[.,]\d+)?)\}\{(-?\d+(?:[.,]\d+)?)\}')
_RE_PALABRA = _re.compile(r'[^\W\d_]{%d,}' % _MIN_LETRAS_PALABRA)
_SEP_DECIMAL = ('{,}', ',', '.')     # separadores decimales admitidos por defecto: 0{,}5, 0,5 y 0.5
_re_cifras   = {}


def _re_cifra(decimal=None):
    """Regex de las cifras con los separadores decimales admitidos: por defecto
    _SEP_DECIMAL; «{,}» (lint(decimal='{,}'), --decimal, DECIMAL en config.py)
    si el banco escribe siempre 0{,}5 y una coma desnuda separa componentes,
    (2,2,-1). Varios separadores, separados por espacios: «{,} .»."""
    seps = tuple(decimal.split()) if isinstance(decimal, str) else tuple(decimal or _SEP_DECIMAL)
    if seps not in _re_cifras:
        sueltos = ''.join(_re.escape(x) for x in seps if len(x) == 1)
        _re_cifras[seps] = _re.compile(r'(?:(?<!\w)-(?=\d))?(?<![\w%s])\d+(?:(?:%s)\d+)?'
                                       % (sueltos, '|'.join(map(_re.escape, seps))))
    return _re_cifras[seps]


_RE_CIFRA = _re_cifra()


def _sin_fracciones(texto):
    """Sustituye cada \\frac{a}{b} numérica por su valor decimal."""
    def valor(m):
        num, den = (float(x.replace(',', '.')) for x in m.group(2, 3))
        return f" {m.group(1)}{num / den:.6g} " if den else m.group(0)
    return _RE_FRAC.sub(valor, texto)


def _limpia(texto):
    return _RE_CMD.sub(' ', _RE_SUBIND.sub(' ', _RE_NOTACION.sub(' ', _sin_fracciones(texto))))


def _formas_cifra(s):
    """Rasgos de la forma de una cifra tal como está escrita: entera (y múltiplo
    de 5 o de 10) o con decimales (y cuántos)."""
    ent, _, dec = s.lstrip('-').replace('{,}', ',').replace('.', ',').partition(',')
    if not dec:
        f = {'entera'}
        if int(ent) % 5 == 0:
            f.add('múltiplo de 5')
        if int(ent) % 10 == 0:
            f.add('múltiplo de 10')
        return f
    return {'con decimales', f"con {len(dec)} decimal{'es' if len(dec) > 1 else ''}"}


def _cifras_y_formas(texto, decimal=None):
    """Cifras legibles del texto, como float (coma o punto decimal, {,} de LaTeX;
    o solo los separadores de `decimal`), y los rasgos de forma de cada una."""
    out, formas = [], []
    for m in _re_cifra(decimal).finditer(_limpia(texto)):
        try:
            out.append(float(m.group(0).replace('{,}', '.').replace(',', '.')))
        except ValueError:
            continue
        formas.append(_formas_cifra(m.group(0)))
    return out, formas


def _cifras(texto, decimal=None):
    return _cifras_y_formas(texto, decimal)[0]


def _tipo_frase(texto, decimal=None):
    """El texto con cada cifra sustituida por «#»: agrupa las opciones que solo difieren en los números."""
    return ' '.join(_re_cifra(decimal).sub('#', _limpia(texto)).split())


def _palabras(texto):
    return {w.lower() for w in _RE_PALABRA.findall(_RE_CMD.sub(' ', texto))}


def _fmt_cifra(x):
    return f"{x:g}".replace('.', ',')


def _iguales(a, b):
    return abs(a - b) <= 1e-9 + 0.005 * max(abs(a), abs(b))


_RE_INTERVALO = _re.compile(r'\[\s*-?\d[\d{},.]*\s*[,;]\s*(?:\\[,;!]\s*)*-?\d[\d{},.]*\s*\]')   # [20,\,40]


def _rasgos(texto, cifras, cifras_enun, cifras_hueco, longitudes):
    """Rasgos superficiales de una opción: lo que un alumno puede ver sin entenderla."""
    r = {f"«{w}»" for w in _palabras(texto)}
    r |= {f"cifra {_fmt_cifra(x)}" for x in cifras}
    if cifras:
        r.add('cifras')
        if any(_iguales(x, y) for x in cifras for y in cifras_enun):
            r.add('una cifra del enunciado')
        otras = [c for c in cifras_hueco if c is not cifras]
        if otras:
            if all(max(cifras) > max(o) for o in otras):
                r.add('la cifra mayor del hueco')
            if all(min(cifras) < min(o) for o in otras):
                r.add('la cifra menor del hueco')
    if '$' in texto:
        r.add('fórmula')
    if _RE_INTERVALO.search(texto):
        r.add('un intervalo [a, b]')
    if len(texto) > sorted(longitudes)[len(longitudes) // 2]:
        r.add('texto más largo que la mediana del hueco')
    return r


def _huecos_comp(p):
    """{parte k: [índice de componente de cada hueco]}, en el orden de por_partes_lectura."""
    L     = [_normaliza_slot(x) for x in p.e]
    plan  = _plan_partes(L)
    comps = _defaultdict(list)
    for n, slot in enumerate(L):
        if _clasifica_slot(slot) == 'cuestiones':
            comps[plan[n]].append(n)
    return comps


def _lecturas(p, n_semillas):
    """Las lecturas (un ejemplo por mundo) de n_semillas sorteos del setup (uno
    solo si no hay setup), sin alterar los generadores aleatorios."""
    semillas = range(n_semillas) if p.setup is not None else [None]
    import random as _random
    estado = _random.getstate()
    try:
        import numpy as _np
        estado_np = _np.random.get_state()
    except ImportError:
        _np = None
    out = []
    try:
        for s in semillas:
            out.extend(p.por_partes_lectura(seed=s))
    finally:
        _random.setstate(estado)
        if _np is not None:
            _np.random.set_state(estado_np)
    return out


def _muestra_patrones(p, n_semillas, decimal=None):
    """Un caso por alternativa no excluida, en cada mundo y en n_semillas sorteos
    del setup. Cada caso: dict con parte k, hueco h, componente i, alternativa j,
    texto, valor, rasgos, cifras (y sus formas) y tipo de frase."""
    comps = _huecos_comp(p)
    casos = []
    for r in _lecturas(p, n_semillas):
        for k, parte in enumerate(r.partes):
            cifras_enun = _cifras(parte.enunciado, decimal)
            for h, hueco in enumerate(parte.huecos):
                activas = [(j, a) for j, a in enumerate(hueco) if a.valor is not None]
                if not activas:
                    continue
                cifras = {j: _cifras_y_formas(a.texto, decimal) for j, a in activas}
                con_cifras = [c for c, _ in cifras.values() if c]
                longitudes = [len(a.texto) for _, a in activas]
                for j, a in activas:
                    casos.append(dict(k=k, h=h, i=comps[k][h], j=j, texto=a.texto, valor=bool(a.valor),
                                      rasgos=_rasgos(a.texto, cifras[j][0], cifras_enun, con_cifras, longitudes),
                                      cifras=cifras[j][0], formas=cifras[j][1], tipo=_tipo_frase(a.texto, decimal)))
    return casos


def _log_comb(n, k):
    return _math.lgamma(n + 1) - _math.lgamma(k + 1) - _math.lgamma(n - k + 1)


def _p_cola(N, K, n, k):
    """P(X >= k) para X hipergeométrica: K éxitos entre N casos, n extracciones."""
    return sum(_math.exp(_log_comb(K, x) + _log_comb(N - K, n - x) - _log_comb(N, n))
               for x in range(k, min(K, n) + 1))


def _rango(xs):
    lo, hi = min(xs), max(xs)
    return _fmt_cifra(lo) if lo == hi else f"{_fmt_cifra(lo)}–{_fmt_cifra(hi)}"


def _patrones_cuestiones(p, avisos, por_j, i):
    """Cuestiones casi constantes (y constantes en la muestra si son lambda con setup)."""
    L = [s for _, s, _ in _slots(p)]
    for j, lst in sorted(por_j.items()):
        n, nV = len(lst), sum(c['valor'] for c in lst)
        if n < _MIN_CASOS_PATRON:
            continue
        if 0 < nV < n:
            frac = max(nV, n - nV) / n
            if frac >= _PRECISION_PATRON:
                avisos.append(Aviso(AVISO, 'patron',
                                    f"casi constante: {'verdadera' if 2 * nV > n else 'falsa'} en el "
                                    f"{frac:.0%} de las {n} veces que aparece (se puede memorizar)",
                                    _donde(i, j, lst[0]['texto'])))
        elif p.setup is not None and callable(L[i][j].s):      # la regla 3 solo dio INFO
            avisos.append(Aviso(AVISO, 'patron',
                                f"{'verdadera' if nV else 'falsa'} en las {n} veces que aparece en la muestra "
                                "(semantica lambda: la tabla de mundos solo usa un sorteo)",
                                _donde(i, j, lst[0]['texto'])))


def _tasa(casos):
    """(nº de V, tasa base de V y de F, soporte mínimo por lado) de un grupo de casos."""
    N = len(casos)
    nV = sum(c['valor'] for c in casos)
    return nV, {True: nV / N, False: 1 - nV / N}, max(3, _math.ceil(_SOPORTE_PATRON * N))


def _predice(casos, con, m):
    """Si el subconjunto `con` de `casos` predice la verdad (acierto ≥ _PRECISION_PATRON,
    ≥ _MEJORA_PATRON sobre la tasa base, soporte mínimo a ambos lados y p-valor
    hipergeométrico corregido por las m pruebas < _P_PATRON), devuelve
    (precision, soporte, cubre, hacia, ejemplo); si no, None."""
    N, n = len(casos), len(con)
    nV, base, minimo = _tasa(casos)
    if n < minimo or N - n < minimo:
        return None
    v = sum(c['valor'] for c in con)
    for hacia, k in ((True, v), (False, n - v)):
        prec = k / n
        if prec < _PRECISION_PATRON or prec - base[hacia] < _MEJORA_PATRON:
            continue
        if _p_cola(N, nV if hacia else N - nV, n, k) * m > _P_PATRON:
            continue
        return (prec, n, frozenset(id(c) for c in con), hacia,
                next(c['texto'] for c in con if c['valor'] == hacia))
    return None


def _por_tipo_frase(casos):
    por_tipo = _defaultdict(list)
    for c in casos:
        por_tipo[(c['tipo'], len(c['cifras']))].append(c)
    return [(tipo, nc, G) for (tipo, nc), G in por_tipo.items() if nc and len(G) >= _MIN_CASOS_PATRON]


def _patrones_umbral(casos):
    """Candidatos (precision, soporte, cubre, nombre, hacia, ejemplo): dentro de un
    tipo de frase, una cifra cuyo valor separa por completo las V de las F."""
    out = []
    for tipo, nc, G in _por_tipo_frase(casos):
        for pos in range(nc):
            V = [c['cifras'][pos] for c in G if c['valor']]
            F = [c['cifras'][pos] for c in G if not c['valor']]
            if len(V) >= 3 and len(F) >= 3 and (max(V) < min(F) or max(F) < min(V)):
                cual = '' if nc == 1 else f" nº {pos + 1}"
                out.append((1.0, len(G), frozenset(id(c) for c in G if c['valor']),
                            f"en «{_rec(tipo, 50)}» la cifra{cual} separa V ({_rango(V)}) de F ({_rango(F)})",
                            None, None))
                break                                   # las demás cifras del tipo suelen derivar de esta
    return out


def _patrones_forma(casos):
    """Candidatos: dentro de un tipo de frase, la forma de una cifra (entera o con
    decimales, múltiplo de 5 o de 10) que, con ella o sin ella, predice la verdad:
    la cifra redonda es siempre la aproximación, y la aproximación siempre falsa."""
    out = {}                                        # (cubre, hacia) -> candidato: «con decimales» y «no entera» son lo mismo
    for tipo, nc, G in _por_tipo_frase(casos):
        formas = set().union(*(f for c in G for f in c['formas']))
        formas = [f for f in _ORDEN_FORMAS if f in formas] + sorted(formas - set(_ORDEN_FORMAS))
        m = 2 * nc * len(formas)
        for pos in range(nc):
            for f in formas:
                for neg in (False, True):
                    con = [c for c in G if (f in c['formas'][pos]) != neg]
                    r = _predice(G, con, m)
                    if r is not None:
                        prec, n, cubre, hacia, ejemplo = r
                        cual = '' if nc == 1 else f" nº {pos + 1}"
                        out.setdefault((cubre, hacia), (prec, n, cubre, f"en «{_rec(tipo, 50)}» la cifra{cual} "
                                                        f"{'no ' if neg else ''}{f}", hacia, ejemplo))
    return list(out.values())


def _rasgo_de_cifras(f):
    """Rasgos que el alumno ve sin leer: lleva cifras, un intervalo, la cifra mayor…;
    no las palabras ni la longitud."""
    return not f.startswith('«') and 'mediana' not in f


def _patrones_rasgos(casos, por_j):
    """Candidatos: rasgos superficiales (con o sin ellos) que predicen la verdad en
    el hueco. Se descartan los que solo reúnen Cuestiones enteras: esos reexpresan
    «constante» o «casi constante». Excepción: un rasgo de cifras que reúne dos o más
    Cuestiones enteras y deja fuera otras dos o más («las que escriben un intervalo
    son siempre falsas») sí se aprende sin leer, y se conserva."""
    _, base, _ = _tasa(casos)
    rasgos = set().union(*(c['rasgos'] for c in casos))
    m = 2 * len(rasgos)
    ids_j = [frozenset(id(c) for c in lst) for lst in por_j.values()]
    out = []
    for f in rasgos:
        for neg in (False, True):
            con = [c for c in casos if (f in c['rasgos']) != neg]
            r = _predice(casos, con, m)
            if r is None:
                continue
            prec, n, cubre, hacia, ejemplo = r
            enteras = sum(ids <= cubre for ids in ids_j)
            if (all(ids <= cubre or not (ids & cubre) for ids in ids_j)
                    and not (_rasgo_de_cifras(f) and 2 <= enteras <= len(ids_j) - 2)):
                continue                            # (a un lado o al otro queda una sola Cuestion: eso es «constante»)
            out.append((prec, n, cubre, ('sin ' if neg else 'con ') + f, hacia, ejemplo))
    return out, base, len(casos)


def _regla_patrones(p, avisos, n_semillas=N_SEMILLAS_PATRONES, decimal=None):
    try:
        casos = _muestra_patrones(p, n_semillas, decimal)
    except Exception:                               # noqa: BLE001
        return                                      # la regla 2 ya informa (ejecucion)
    por_hueco = _defaultdict(list)
    for c in casos:
        por_hueco[(c['k'], c['h'], c['i'])].append(c)
    for (k, h, i), R in sorted(por_hueco.items()):
        por_j = _defaultdict(list)
        for c in R:
            por_j[c['j']].append(c)
        _patrones_cuestiones(p, avisos, por_j, i)
        if len(R) < _MIN_CASOS_PATRON:
            continue
        candidatos = _patrones_umbral(R) + _patrones_forma(R)
        rasgos, base, N = _patrones_rasgos(R, por_j)
        candidatos += rasgos
        # Un candidato que cubre los mismos casos que otro mejor se funde con él; uno
        # que cubre un subconjunto (p. ej. «la» dentro de «precio») no añade nada.
        aceptados = []
        for cand in sorted(candidatos, key=lambda c: (-c[0], -c[1])):
            for a in aceptados:
                if cand[4] == a['hacia'] and cand[2] <= a['cubre']:
                    if cand[2] == a['cubre']:
                        a['nombres'].append(cand[3])
                    break
            else:
                aceptados.append(dict(prec=cand[0], n=cand[1], cubre=cand[2], nombres=[cand[3]],
                                      hacia=cand[4], ejemplo=cand[5]))
        donde = f"parte {k + 1}, hueco {h + 1} (comp {i})"
        for a in aceptados[:_MAX_PATRONES_HUECO]:
            nombres = ' / '.join(a['nombres'][:3]) + (f" (+{len(a['nombres']) - 3})" if len(a['nombres']) > 3 else '')
            if a['hacia'] is None:
                avisos.append(Aviso(AVISO, 'patron', nombres, donde))
            else:
                avisos.append(Aviso(AVISO, 'patron',
                                    f"{nombres} ⇒ {'V' if a['hacia'] else 'F'} en el {a['prec']:.0%} de "
                                    f"{a['n']} casos (base {base[a['hacia']]:.0%} en {N})",
                                    f"{donde}: {_rec(a['ejemplo'])}"))
        if len(aceptados) > _MAX_PATRONES_HUECO:
            avisos.append(Aviso(INFO, 'patron', f"… y {len(aceptados) - _MAX_PATRONES_HUECO} rasgo(s) más", donde))


# ── Regla 12: inventario de objetos ──────────────────────────────────────────

_N_SORTEOS_LECTURAS = 10          # sorteos del setup con que se recorren las lecturas (reglas 12 a 14)
_ALCANCE_RANGO      = 80          # caracteres entre \beta_1 y los puntos de «\beta_1,\dots,\beta_k»
_PRESENTA_TRAS  = ('(', ', que ', ', cuy', 'en lugar de ', 'en vez de ')   # «X (…)», «X, que …», «X en lugar de Y»
_PRESENTA_ANTES = ('en lugar de', 'en vez de')                              # «… en lugar de X»

_OBJ_TEXTO    = r'\\(?:text|textrm|textit|mathrm|mathit|operatorname)\s*\{[^{}]*\}'
_RE_OBJ_TEXTO = _re.compile(_OBJ_TEXTO + r'(?:\s*\\(?:cdot|times)\s*' + _OBJ_TEXTO + r')*')
_RE_OBJ_NEGRITA = _re.compile(r'\\(?:boldsymbol|mathbf|bm|symbf)\s*(?:\{([^{}]*)\}|(\\?[A-Za-z]+))')
_DECORACION     = r'(?:\\(?:hat|widehat|bar|overline|tilde|widetilde|vec|dot|boldsymbol|mathbf|bm|symbf|mathrm|text)\s*\{?\s*)*'
_RE_OBJ_SUBIND  = _re.compile(_DECORACION + r'(\\?[A-Za-z]+)\s*\}*\s*_\s*(?:\{\s*(\d+)\s*\}|(\d))(?!\d)')
_RE_SUBIND_FIN  = _re.compile(_DECORACION + r'(\\?[A-Za-z]+)\s*\}*\s*_\s*(?:\{\s*(\w+)\s*\}|(\w))')   # también simbólico: \beta_k
_RE_PUNTOS      = _re.compile(r'\\[lc]?dots\b|…|\.\.\.')
_RE_HIPOTESIS   = _re.compile(r'H_(?:\{[^}]*\}|\w)\s*(?:\\[!,;:]\s*)*(?::|\\colon)')   # «H_0\!:» antes del objeto


def _presentado(texto, ini, fin):
    """¿Presenta el propio texto el objeto que ocupa texto[ini:fin]? «X (…)»,
    «X, que …», «en lugar de X», o X dentro de una hipótesis escrita, «H_0: X = 0»."""
    tras  = texto[fin:].lstrip('$ \t\n')
    antes = texto[:ini].rstrip('$ \t\n')
    return (tras.startswith(_PRESENTA_TRAS) or antes.endswith(_PRESENTA_ANTES)
            or bool(_RE_HIPOTESIS.search(texto[:ini].rsplit('$', 1)[-1])))


def _rangos(texto, out):
    """«\\beta_1,\\dots,\\beta_k» presenta también los subíndices intermedios: con
    fin numérico, cada uno del rango; con fin simbólico (k, n), todos los de esa
    base, que se anota con la clave «\\beta_» (como en conocidos=)."""
    for m in _RE_OBJ_SUBIND.finditer(texto):
        resto = texto[m.end():m.end() + _ALCANCE_RANGO]
        mp = _RE_PUNTOS.search(resto)
        if not mp or '$' in resto[:mp.start()]:
            continue
        mf = _RE_SUBIND_FIN.search(resto, mp.end())
        if not mf or mf.group(1) != m.group(1):
            continue
        base, a, fin = m.group(1), int(m.group(2) or m.group(3)), mf.group(2) or mf.group(3)
        if fin.isdigit():
            for n in range(a, int(fin) + 1):
                out.setdefault(f"{base}_{n}", ('subindice', False))
        else:
            out.setdefault(base + '_', ('subindice', False))


def _objetos(texto, rangos=False):
    """Objetos concretos que nombra un texto: {clave normalizada: (familia, lo
    presenta el propio texto)}; familias 'texto', 'negrita' y 'subindice'. Con
    rangos=True (el enunciado) añade los que presenta una secuencia con puntos."""
    out = {}

    def anota(familia, clave, m):
        out[clave] = (familia, out.get(clave, (None, False))[1] or _presentado(texto, m.start(), m.end()))

    for m in _RE_OBJ_TEXTO.finditer(texto):
        partes = [' '.join(x.split()) for x in _re.findall(r'\{([^{}]*)\}', m.group(0))]
        if all(partes) and not all(x.replace('.', '').isdigit() for x in partes):
            anota('texto', '·'.join(partes), m)
    for m in _RE_OBJ_NEGRITA.finditer(texto):
        c = ''.join((m.group(1) or m.group(2)).split())
        if c and not c.isdigit():
            anota('negrita', '\\boldsymbol{' + c + '}', m)
    for m in _RE_OBJ_SUBIND.finditer(texto):
        anota('subindice', m.group(1) + '_' + (m.group(2) or m.group(3)), m)
    if rangos:
        _rangos(texto, out)
    return out


def _en(clave, enun):
    """¿Presenta el enunciado la clave, o toda su base («\\beta_», por un rango con puntos)?"""
    return clave in enun or clave.rsplit('_', 1)[0] + '_' in enun


def _hermanos(clave, enun):
    """Objetos del enunciado con la misma base y otro subíndice: \\beta_1, \\beta_2 para \\beta_6."""
    base = clave.rsplit('_', 1)[0] + '_'
    return sorted(k for k in enun if k.startswith(base) and k != clave and not k.endswith('_'))


def _conocidos(entradas):
    """Claves normalizadas de la notación declarada conocida: cada entrada se lee
    como se escribiría en una pregunta (\\mathrm{SRC}, \\boldsymbol{y}, \\hat\\beta_2) o ya
    normalizada (SRC); una que termina en «_» cubre todos los subíndices (\\beta_)."""
    out = set()
    for e in entradas or ():
        e = e.strip()
        if e:
            out |= set(_objetos(e)) or {e}
    return out


def _es_conocido(clave, conocidos):
    return clave in conocidos or any(c.endswith('_') and clave.startswith(c) for c in conocidos)


def _regla_inventario(p, avisos, conocidos=(), lecturas=None):
    if lecturas is None:
        try:
            lecturas = _lecturas(p, _N_SORTEOS_LECTURAS)
        except Exception:                           # noqa: BLE001
            return                                  # la regla 2 ya informa (ejecucion)
    conocidos = _conocidos(conocidos)
    comps  = _huecos_comp(p)
    faltan = {}                                     # (i, j, tipo, clave) -> [veces, presentado, texto, hermanos]
    dudosos = _defaultdict(set)                     # clave -> {(i, j, tipo)}: negritas y subíndices sueltos
    veces  = _defaultdict(int)                      # (i, j) -> apariciones de la alternativa
    for r in lecturas:
        enun = _objetos(' '.join(parte.enunciado for parte in r.partes), rangos=True)
        for k, parte in enumerate(r.partes):
            for h, hueco in enumerate(parte.huecos):
                i = comps[k][h]
                for j, a in enumerate(hueco):
                    if a.valor is None:
                        continue
                    veces[(i, j)] += 1
                    opcion = _objetos(a.texto)
                    pares = [('cuestión', a.texto, clave, fam, pres) for clave, (fam, pres) in opcion.items()
                             if not _en(clave, enun) and not _es_conocido(clave, conocidos)]
                    if a.exp:
                        pares += [('exp', a.exp, clave, fam, pres) for clave, (fam, pres) in _objetos(a.exp).items()
                                  if not _en(clave, enun) and clave not in opcion and not _es_conocido(clave, conocidos)]
                    for tipo, texto, clave, fam, pres in pares:
                        hermanos = _hermanos(clave, enun) if fam == 'subindice' else []
                        if fam == 'negrita' or (fam == 'subindice' and not hermanos):
                            dudosos[clave].add((i, j, tipo))      # letras de una identidad general, notación…
                            continue
                        reg = faltan.setdefault((i, j, tipo, clave), [0, True, texto, hermanos])
                        reg[0] += 1
                        reg[1] = reg[1] and pres
    for (i, j, tipo, clave), (nf, pres, texto, hermanos) in sorted(faltan.items()):
        cuantas = f"en {nf} de las {veces[(i, j)]} veces que aparece"
        if pres:
            avisos.append(Aviso(INFO, 'inventario',
                                f"la {tipo} presenta ella misma «{clave}», que no está en el enunciado ({cuantas})",
                                _donde(i, j, texto)))
        else:
            quien = "el enunciado no presenta" if tipo == 'cuestión' else "ni el enunciado ni la cuestión presentan"
            si = f" (sí presenta {', '.join(hermanos[:3])})" if hermanos else ''
            avisos.append(Aviso(AVISO, 'inventario',
                                f"la {tipo} nombra «{clave}», que {quien}{si} ({cuantas})",
                                _donde(i, j, texto)))
    if dudosos:
        lista = ', '.join(f"«{clave}» ({len(d)})" for clave, d in sorted(dudosos.items()))
        avisos.append(Aviso(INFO, 'inventario',
                            "símbolos que el enunciado no presenta, con el nº de cuestiones o exp que los usan: "
                            f"{lista}. Pueden ser notación del curso (decláralos en conocidos=) o las letras de "
                            "una identidad general; si no, preséntalos"))


# ── Reglas 13 y 14: longitud de las opciones y gemelas ───────────────────────

_DESTACA_LONGITUD  = 2.0    # una opción es claramente más larga que otra si mide el doble (y _MIN_DIF_LONGITUD más)
_P_DESTACA         = 0.5    # … y destaca si lo es frente a todas las que el alumno ve con ella en al menos esta fracción de las variantes
_PARECIDA_LONGITUD = 1.3    # su pareja mide parecido: razón de longitudes ≤ 1,3 (el 30 % de la regla del banco)
_MIN_DIF_LONGITUD  = 10     # diferencia mínima, en caracteres visibles, para que algo destaque
_COMPENSADA        = (0.3, 0.7)   # si la claramente más corta (o larga) de lo que se muestra es verdadera entre estas fracciones de las veces, no hay nada que aprender
_MAX_COMBINACIONES = 2000   # combinaciones de una alternativa por hueco que se recorren por parte y lectura (más: una muestra)
_MAX_PROSA_FORMULA = 30     # caracteres visibles fuera de $…$ para que una opción cuente como fórmula
_GEMELA_PARECIDO   = 0.8    # una falsa es gemela si comparte con la verdadera esta fracción (Dice) de los tokens de un esqueleto

_RE_TEXTO_VISIBLE = _re.compile(r'\\(?:text|textrm|textit|textbf|mathrm|mathit|mathsf|mathfrak|mathcal|mathbb|operatorname)\s*\{([^{}]*)\}')
_RE_INVISIBLE     = _re.compile(r'\\(?:hat|widehat|bar|overline|tilde|widetilde|vec|dot|boldsymbol|mathbf|bm|symbf|mathop|left|right|'
                                r'displaystyle|frac|dfrac|tfrac|quad|qquad|,|!|;|:| )\s*')
_RE_MACRO_VISIBLE = _re.compile(r'\\[A-Za-z]+\s*')


def _visible(texto):
    """Caracteres que ve el alumno: sin $, llaves ni nombres de macros (cada macro
    con glifo, \\beta o \\le, cuenta uno; las decoraciones y los espacios, nada)."""
    t = _RE_TEXTO_VISIBLE.sub(r' \1 ', texto)
    t = _re.sub(r'\\([%$&#_{}])', r'\1', t)
    t = _RE_MACRO_VISIBLE.sub('x', _RE_INVISIBLE.sub('', t))
    return len(' '.join(_re.sub(r'[${}_^&~]', '', t).split()))


def _mas(l, otra):
    """¿Es l claramente mayor que otra?"""
    return l >= _DESTACA_LONGITUD * otra and l - otra >= _MIN_DIF_LONGITUD


def _parecida(l, otra):
    """¿Miden parecido? Razón ≤ _PARECIDA_LONGITUD, o menos de _MIN_DIF_LONGITUD caracteres de
    diferencia (entre «$F=4$» y «$F=14$» la razón es 1,33, pero nada destaca)."""
    return max(l, otra) <= _PARECIDA_LONGITUD * min(l, otra) or abs(l - otra) < _MIN_DIF_LONGITUD


def _destaca(l, companeras):
    """Con qué probabilidad una opción de longitud l es claramente la más larga (o la
    más corta) de las que el alumno ve con ella: una alternativa activa de cada otro
    hueco, equiprobables. Devuelve ('larga'|'corta', probabilidad) o (None, 0)."""
    p_larga = p_corta = 1.0
    for lst in companeras:
        p_larga *= sum(_mas(l, x) for x in lst) / len(lst)
        p_corta *= sum(_mas(x, l) for x in lst) / len(lst)
    if p_larga >= _P_DESTACA:
        return 'larga', p_larga
    if p_corta >= _P_DESTACA:
        return 'corta', p_corta
    return None, 0.0


def _destacadas(listas):
    """Recorre las combinaciones de una alternativa (longitud, valor) por hueco —todas, o
    una muestra si son más de _MAX_COMBINACIONES— y cuenta, para cada lado, cuántas
    veces hay una claramente más corta (o más larga) que las demás y cuántas de ellas
    es verdadera: {'corta': [nV, n], 'larga': [nV, n]}."""
    total = _math.prod(len(l) for l in listas)
    if total <= _MAX_COMBINACIONES:
        combos = _itertools.product(*listas)
    else:
        rng = _random.Random(total)                 # propio: no toca los generadores del banco
        combos = (tuple(rng.choice(l) for l in listas) for _ in range(_MAX_COMBINACIONES))
    out = {'corta': [0, 0], 'larga': [0, 0]}
    for combo in combos:
        for n, (l, v) in enumerate(combo):
            otras = [l2 for m, (l2, _) in enumerate(combo) if m != n]
            if all(_mas(l, l2) for l2 in otras):
                out['larga'][0] += v
                out['larga'][1] += 1
            elif all(_mas(l2, l) for l2 in otras):
                out['corta'][0] += v
                out['corta'][1] += 1
    return out


def _regla_longitud(p, avisos, lecturas):
    comps  = _huecos_comp(p)
    orden  = {}                                     # mundo -> número de orden (su primera lectura)
    veces  = _defaultdict(int)                      # (i, j) -> apariciones
    solas  = {}                                     # (i, j) -> [nV, nF, mundos, (lado, l, prob), texto]
    comp   = _defaultdict(lambda: [0, 0])           # (parte, lado) -> [destacadas verdaderas, destacadas]
    parte_de = {}                                   # (i, j) -> parte
    for r in lecturas:
        orden.setdefault(r.mundo, len(orden) + 1)
        for k, parte in enumerate(r.partes):
            activas = {h: [(j, _visible(a.texto), bool(a.valor)) for j, a in enumerate(hueco) if a.valor is not None]
                       for h, hueco in enumerate(parte.huecos)}
            activas = {h: lst for h, lst in activas.items() if lst}
            if len(activas) < 2:
                continue                            # sin compañeras no hay con qué destacar
            for lado, (nV, n) in _destacadas([[(l, v) for _, l, v in lst] for lst in activas.values()]).items():
                comp[(k, lado)][0] += nV
                comp[(k, lado)][1] += n
            for h, lst in activas.items():
                companeras = [[l2 for _, l2, _ in lst2] for h2, lst2 in activas.items() if h2 != h]
                for j, l, valor in lst:
                    i = comps[k][h]
                    veces[(i, j)] += 1
                    parte_de[(i, j)] = k
                    lado, prob = _destaca(l, companeras)
                    if lado is None:
                        continue
                    pareja = any(v2 != valor and _parecida(l, l2) for j2, l2, v2 in lst if j2 != j)
                    if not pareja:
                        reg = solas.setdefault((i, j), [0, 0, set(), (lado, l, prob), parte.huecos[h][j].texto])
                        reg[0 if valor else 1] += 1
                        reg[2].add(orden[r.mundo])
    for (i, j), (nV, nF, mundos, (lado, l, prob), texto) in sorted(solas.items()):
        n = nV + nF
        if max(nV, nF) < _PRECISION_PATRON * n:
            continue                                # unas veces verdadera y otras falsa: es su propia pareja
        nV_c, n_c = comp[(parte_de[(i, j)], lado)]
        if n_c and _COMPENSADA[0] <= nV_c / n_c <= _COMPENSADA[1]:
            continue                                # entre lo que se muestra, la destacada es unas veces V y otras F: nada que aprender
        valor = "verdadera" if nV >= nF else "falsa"
        en = f"en {n} de las {veces[(i, j)]} veces que aparece" if n < veces[(i, j)] else "siempre"
        donde_m = (f"; mundo{'s' if len(mundos) > 1 else ''} {', '.join(map(str, sorted(mundos)))} de {len(orden)}"
                   if len(orden) > 1 else '')
        avisos.append(Aviso(AVISO, 'longitud',
                            f"opción claramente más {lado} que las que se muestran con ella ({l} caracteres visibles; lo es en "
                            f"el {prob:.0%} de las variantes) y {valor}, sin pareja de longitud parecida y valor contrario en "
                            f"su hueco ({en}{donde_m}): recórtala (el porqué va al exp) o dale una gemela",
                            _donde(i, j, texto)))


_RE_NUMERO_SUELTO = _re.compile(r'\$(\s*-?\d[\d{},.\s]*)\$')   # una fórmula que es solo un número: $-2{,}5$
_RE_PORCENTAJE    = _re.compile(r'\s*(?:\\[,;!]\s*)*\\?%')          # lo que sigue a la cifra de «al $5$\,\%»
_RE_CALCULO = _re.compile(r'\$[^$]*(?:[=<>+\-/]|\\(?:le|ge|leq|geq|ne|neq|approx|frac|dfrac|tfrac|sqrt|cdot|times|sum|pm|mp)\b)[^$]*\$')
_RE_TOKEN   = _re.compile(r'§[^§]*§|\\[A-Za-z]+|\\.|[^\W\d_]+|\S')
_ANTONIMOS  = (('mayor', 'menor'), ('mayores', 'menores'), ('más', 'menos'), ('máximo', 'mínimo'), ('máxima', 'mínima'),
               ('multiplica', 'divide'), ('multiplicada', 'dividida'), ('multiplicado', 'dividido'), ('multiplicar', 'dividir'),
               ('aumenta', 'disminuye'), ('aumentar', 'disminuir'), ('crece', 'decrece'), ('sube', 'baja'), ('mejor', 'peor'),
               ('positivo', 'negativo'), ('positiva', 'negativa'), ('positivos', 'negativos'), ('positivas', 'negativas'),
               ('numerador', 'denominador'), ('izquierda', 'derecha'), ('antes', 'después'), ('par', 'impar'),
               ('creciente', 'decreciente'), ('convexa', 'cóncava'), ('verdadera', 'falsa'), ('cierta', 'falsa'),
               ('siempre', 'nunca'), ('todos', 'ninguno'), ('alguno', 'ninguno'), ('directa', 'inversa'),
               ('superior', 'inferior'), ('encima', 'debajo'), ('grande', 'pequeño'), ('alto', 'bajo'), ('alta', 'baja'),
               ('largo', 'corto'), ('primero', 'último'), ('primera', 'última'), ('suma', 'resta'), ('sumar', 'restar'),
               ('producto', 'cociente'), ('igual', 'distinto'), ('iguales', 'distintos'), ('independiente', 'dependiente'),
               ('exógena', 'endógena'), ('sesgado', 'insesgado'), ('eficiente', 'ineficiente'), ('consistente', 'inconsistente'),
               ('rechaza', 'acepta'), ('rechazar', 'aceptar'), ('sobreestima', 'subestima'), ('exacta', 'aproximada'),
               ('exacto', 'aproximado'))
_OPUESTOS   = {'>': '<', '\\le': '<', '\\leq': '<', '\\ge': '<', '\\geq': '<', '\\ne': '=', '\\neq': '=',
               '\\approx': '=', '/': '\\cdot', '\\times': '\\cdot', '*': '\\cdot', '\\dfrac': '\\frac', '\\tfrac': '\\frac',
               '\\mp': '\\pm'}
_CANON      = {**{b: a for a, b in _ANTONIMOS}, **_OPUESTOS}
_SIN_PESO   = {'no', 'ni', ',', '.', ';', ':', '(', ')', '[', ']', '|', '{', '}', '_', '^', '+', '-', '\\left', '\\right', '\\mathop', '\\displaystyle',
               '\\quad', '\\qquad', '\\,', '\\!', '\\;', '\\:', '\\ ', '\\hat', '\\widehat', '\\bar', '\\overline', '\\tilde',
               '\\widetilde', '\\vec', '\\dot', '\\boldsymbol', '\\mathbf', '\\bm', '\\symbf', '\\mathrm', '\\mathit', '\\text',
               '\\textrm', '\\textit', '\\mathsf', '\\mathcal', '\\mathbb', '\\mathfrak', '\\operatorname'}
_GRIEGAS    = {'\\' + g for g in ('alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu '
                                   'xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta '
                                   'Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega ell').split()}


def _cifras_calculo(texto, decimal=None, cifras_enun=()):
    """Cifras de una opción que son un dato o un resultado, como [(valor, va dentro de
    una fórmula)]. Una fórmula que es solo un número ($-2{,}5$) cuenta como prosa. Fuera
    quedan las cifras incidentales: subíndices y exponentes, los rótulos «(1)», el 0 y
    el 1 (una indicadora, «un 1 % más») y un porcentaje que el enunciado ya da («al 5 %»)."""
    texto = _RE_SUBIND.sub(' ', _RE_NUMERO_SUELTO.sub(r' \1 ', texto))
    out = []
    for m in _re_cifra(decimal).finditer(texto):
        antes, despues = texto[:m.start()], texto[m.end():]
        if antes.rstrip().endswith('(') and despues.lstrip().startswith(')'):
            continue
        x = float(m.group(0).replace('{,}', '.').replace(',', '.'))
        if x in (0.0, 1.0) or (_RE_PORCENTAJE.match(despues) and any(_iguales(x, y) for y in cifras_enun)):
            continue
        out.append((x, antes.count('$') % 2 == 1))
    return out


def _calculable(texto, decimal=None, cifras_enun=()):
    """Contenido calculable de una opción: 'cifra' si lleva un valor (en la prosa o
    como fórmula suelta, $-2{,}5$; una cifra dentro de una ecuación no cuenta); 'fórmula' si es
    una fórmula con igualdad, desigualdad u operación y poca prosa alrededor; 'prosa'
    si la fórmula va dentro de una frase (una propiedad enunciada, no un cálculo);
    None si no hay nada que calcular."""
    cifras = _cifras_calculo(texto, decimal, cifras_enun)
    if any(not en_formula for _, en_formula in cifras):
        return 'cifra'                              # un valor: en la prosa o como fórmula suelta
    if not (_RE_CALCULO.search(texto) or cifras):
        return None
    return 'fórmula' if _visible(' '.join(texto.split('$')[::2])) <= _MAX_PROSA_FORMULA else 'prosa'


def _parecidos(e, f):
    """Fracción de tokens que comparten dos esqueletos (coeficiente de Dice)."""
    if not e or not f:
        return 0.0
    return 2 * sum((_Counter(e) & _Counter(f)).values()) / (len(e) + len(f))


_RE_OPERACION = _re.compile(r'[+\-/]|\\(?:frac|dfrac|tfrac|cdot|times|sqrt)\b')


def _opera_con_objetos(texto, enun):
    """¿Alguna fórmula del texto opera (suma, resta, cociente, producto) con dos o más
    objetos con subíndice, todos presentados por el enunciado? «pasa a ser
    $\\hat\\beta_2+\\hat\\beta_3$» es un cálculo con los datos; «$\\rho_{x_2x_3}=0$» o
    «$E[U\\mid X]=0$» son propiedades, y «$\\beta_1v_1+\\beta_2v_2$» con $\\beta_1$, $\\beta_2$
    sin presentar es una definición."""
    for m in _RE_CALCULO.finditer(texto):
        objs = _objetos(m.group(0))
        if (_RE_OPERACION.search(_RE_SUBIND.sub(' ', m.group(0))) and objs and all(_en(c, enun) for c in objs)
                and sum(fam == 'subindice' for fam, _ in objs.values()) >= 2):
            return True
    return False


def _esqueletos(texto, decimal=None):
    """Dos bolsas de tokens del texto: con las cifras abstraídas («#») y con los
    símbolos de las fórmulas abstraídos («S»). Antónimos y operadores opuestos
    identificados, negación y decoraciones fuera."""
    t = _re_cifra(decimal).sub(lambda m: f" §{_fmt_cifra(float(m.group(0).replace('{,}', '.').replace(',', '.')))}§ ",
                               texto)
    trozos = t.split('$')
    cifras, simbolos = [], []
    for n, trozo in enumerate(trozos):
        formula = n % 2 == 1 and len(trozos) % 2 == 1
        for tok in _RE_TOKEN.findall(trozo):
            if tok in _SIN_PESO:
                continue
            tok = _CANON.get(tok.lower() if tok.isalpha() else tok, tok.lower() if tok.isalpha() else tok)
            if tok.startswith('§'):
                cifras.append('#')
                simbolos.append(tok)
            elif formula and (tok in _GRIEGAS or tok.isalpha()):
                cifras.append(tok)
                simbolos.append('S')
            else:
                cifras.append(tok)
                simbolos.append(tok)
    return tuple(sorted(cifras)), tuple(sorted(simbolos))


_ORDEN_CALCULABLE = {None: 0, 'prosa': 1, 'fórmula': 2, 'cifra': 3}


def _regla_gemela(p, avisos, lecturas, decimal=None):
    comps   = _huecos_comp(p)
    valores = _defaultdict(set)                     # (i, j) -> {True, False} con que aparece
    textos  = {}                                    # (i, j) -> último texto
    ques    = _defaultdict(set)                     # (i, j) -> contenido calculable en cada lectura
    veces   = _defaultdict(int)
    falsas  = _defaultdict(set)                     # i -> textos de las alternativas falsas alguna vez
    copiada = {}                                    # (i, j) -> en todas sus lecturas, sus cifras son del enunciado y una falsa del hueco lleva alguna
    calculo = {}                                    # (i, j) -> en alguna lectura, su fórmula opera con objetos del enunciado
    enuns   = {}
    for r in lecturas:
        enun = ''
        for k, parte in enumerate(r.partes):
            enun += ' ' + parte.enunciado           # el de esta parte y los anteriores
            if enun not in enuns:
                enuns[enun] = (_cifras(enun, decimal), _objetos(enun, rangos=True))
            c_enun, o_enun = enuns[enun]
            for h, hueco in enumerate(parte.huecos):
                i = comps[k][h]
                c_falsas = [x for a in hueco if a.valor is not None and not a.valor
                            for x, _ in _cifras_calculo(a.texto, decimal, c_enun)]
                for j, a in enumerate(hueco):
                    if a.valor is None:
                        continue
                    valores[(i, j)].add(bool(a.valor))
                    textos[(i, j)] = a.texto
                    veces[(i, j)] += 1
                    if not a.valor:
                        falsas[i].add(a.texto)
                        continue
                    ques[(i, j)].add(_calculable(a.texto, decimal, c_enun))
                    cs = [x for x, _ in _cifras_calculo(a.texto, decimal, c_enun)]
                    copiada[(i, j)] = (copiada.get((i, j), True) and bool(cs)
                                       and all(any(_iguales(abs(x), abs(y)) for y in c_enun) for x in cs)
                                       and any(_iguales(abs(x), abs(y)) for x in cs for y in c_falsas))
                    calculo[(i, j)] = calculo.get((i, j), False) or _opera_con_objetos(a.texto, o_enun)
    for (i, j), vs in sorted(valores.items()):
        texto = textos[(i, j)]
        que = max(ques[(i, j)], key=_ORDEN_CALCULABLE.get) if vs == {True} else None
        if que is None or (que == 'cifra' and copiada[(i, j)]):
            continue                                # copia una cifra del enunciado que una falsa también lleva: la cifra no delata
        esq = _esqueletos(texto, decimal)
        if any(_parecidos(e, f) >= _GEMELA_PARECIDO for fs in (_esqueletos(f, decimal) for f in falsas[i])
               for e, f in zip(esq, fs)):
            continue
        n = veces[(i, j)]
        siempre = f"verdadera siempre que aparece ({n} lectura{'s' if n > 1 else ''})"
        sin = "el hueco no tiene ninguna falsa" if not falsas[i] else "ninguna falsa del hueco es su gemela"
        if que == 'prosa' and not calculo[(i, j)]:
            avisos.append(Aviso(INFO, 'gemela', f"{siempre}, con una fórmula dentro de la frase; {sin}. Si es un "
                                "cálculo y no una propiedad, dale una versión falsa", _donde(i, j, texto)))
        elif que == 'prosa':
            avisos.append(Aviso(AVISO, 'gemela', f"{siempre} y con un cálculo entre objetos del enunciado dentro de la "
                                f"frase; {sin}: dale una versión falsa (otro resultado u otros símbolos)", _donde(i, j, texto)))
        else:
            avisos.append(Aviso(AVISO, 'gemela', f"{siempre} y con {que}; {sin}: sortéala con una versión falsa "
                                "(otras cifras o símbolos, el signo o la desigualdad al revés)", _donde(i, j, texto)))


# ── API ──────────────────────────────────────────────────────────────────────

def lint(problema, instances=None, seed=None, patrones=None, conocidos=(), decimal=None):
    """Revisa un problema y devuelve la lista de :class:`Aviso` (errores primero).

    problema  : ProblemaTipo, dict JSON o ruta a un fichero JSON.
    instances : sobreescribe ``export.instances`` (solo con setup).
    seed      : semilla base para ``por_partes`` (por defecto la del problema).
    patrones  : True (o un número de sorteos del setup) activa además la regla 11,
                patrones memorizables (más lenta); por defecto no corre.
    conocidos : notación del curso que la regla 12 (inventario) no exige presentar
                en el enunciado: una lista de objetos tal como se escriben
                (``\\mathrm{SRC}``, ``\\boldsymbol{y}``, ``H_0``; ``\\beta_`` cubre
                todos los subíndices) o una cadena separada por comas.
    decimal   : separadores decimales que las reglas 11 y 14 leen como tales
                (por defecto ``{,}``, ``,`` y ``.``; ``"{,}"`` si el banco escribe
                siempre ``0{,}5`` y una coma desnuda separa componentes, ``(2,2,-1)``;
                varios, separados por espacios).
    """
    if isinstance(conocidos, str):
        conocidos = conocidos.split(',')
    avisos = []
    p, ruta = _carga(problema, avisos)
    if p is None:
        return avisos
    if not _regla_estructura(p, avisos, ruta):
        return avisos
    _regla_texto(p, avisos)
    _regla_lectura(p, avisos)
    _regla_etiquetas(p, avisos)
    _regla_variantes(p, avisos, instances, seed)
    _regla_mundos(p, avisos)
    try:
        lecturas = _lecturas(p, _N_SORTEOS_LECTURAS)   # reglas 12 a 14
    except Exception:                               # noqa: BLE001
        lecturas = None                             # la regla 2 ya informa (ejecucion)
    if lecturas is not None:
        _regla_inventario(p, avisos, conocidos, lecturas)
        _regla_longitud(p, avisos, lecturas)
        _regla_gemela(p, avisos, lecturas, decimal)
    if patrones:
        _regla_patrones(p, avisos, N_SEMILLAS_PATRONES if patrones is True else int(patrones), decimal)
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
    ap.add_argument('ficheros', nargs='*', metavar='FICHERO.json')
    ap.add_argument('--instances', type=int, default=None,
                    help="número de instancias (por defecto export.instances)")
    ap.add_argument('--seed', type=int, default=None, help="semilla base")
    ap.add_argument('--tabla', action='store_true',
                    help="imprime la tabla Cuestion × mundo aunque no haya avisos")
    ap.add_argument('--quiet', action='store_true',
                    help="omite los INFO y los ficheros sin avisos")
    ap.add_argument('--patrones', nargs='?', const=True, default=None, metavar='N',
                    help="busca además patrones memorizables (regla 11, más lenta), "
                         f"con N sorteos del setup (por defecto {N_SEMILLAS_PATRONES})")
    ap.add_argument('--conocidos', action='append', default=[], metavar='LISTA',
                    help="notación del curso que el inventario de objetos (regla 12) no exige "
                         "presentar en el enunciado, separada por comas (\\mathrm{SRC},\\boldsymbol{y},H_0,\\beta_)")
    ap.add_argument('--decimal', default=None, metavar='SEP',
                    help="separadores decimales (por defecto «{,} , .»); con '{,}' una coma desnuda "
                         "separa componentes, (2,2,-1), y no es un decimal (reglas 11 y 14)")
    args = ap.parse_args(argv)
    conocidos = [c for lista in args.conocidos for c in lista.split(',')]
    if isinstance(args.patrones, str):              # «--patrones fichero.json»: N era un fichero
        try:
            args.patrones = int(args.patrones)
        except ValueError:
            args.ficheros.insert(0, args.patrones)
            args.patrones = True
    if not args.ficheros:
        ap.error("hace falta al menos un FICHERO.json")

    hay_error = False
    for f in args.ficheros:
        avisos = lint(f, instances=args.instances, seed=args.seed, patrones=args.patrones, conocidos=conocidos,
                      decimal=args.decimal)
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
