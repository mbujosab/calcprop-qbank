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
Serialización y deserialización de problemas qbank en formato JSON.

Formato de un ProblemaTipo::

    {
      "version": "1",
      "tipo": "ProblemaTipo",
      "nombre": "identificador_opcional",
      "setup": null,
      "export": {"last_choice": true, "cols": 2},
      "componentes": [
        "texto fijo ",
        {"tipo": "Supuesto", "enunciado": "A ", "semantica": "v('A')", "precond": "True"},
        [
          {"tipo": "Supuesto", "enunciado": "alt 1 ", "semantica": "v('A')"},
          {"tipo": "Supuesto", "enunciado": "alt 2 ", "semantica": "v('B')"}
        ],
        [
          {"tipo": "Cuestion", "enunciado": "¿A?", "semantica": "v('A')", "exp": ""}
        ]
      ]
    }

Formato de un ProblemaVF::

    {
      "version": "1",
      "tipo": "ProblemaVF",
      "nombre": "identificador_opcional",
      "enunciado": "Marque las verdaderas:",
      "NumPreguntas": 3,
      "cuestiones": [
        {"texto": "Pregunta 1", "respuesta": true},
        {"texto": "Pregunta 2", "respuesta": false}
      ]
    }

Formato de un banco (múltiples problemas)::

    {
      "version": "1",
      "banco": [ {problema1}, {problema2}, ... ]
    }

En semantica y precond se admiten:
- Expresiones calcprop:  "v('A') & v('B')"
- Booleanos literales:   "True" / "False"
- Lambdas para setup:    "lambda ns: ns['x'] > 0"
"""

import json as _json
import calcprop as _calcprop_mod
from qbank._quiz import Supuesto, Cuestion, ProblemaTipo, ProblemaVF

__all__ = [
    'problema_from_dict',
    'problema_to_dict',
    'load_problema',
    'save_problema',
    'load_banco',
    'save_banco',
    'problema_to_python',
    'save_problema_py',
]

_EVAL_NS = vars(_calcprop_mod).copy()
def _eval_expr(expr):
    """Evalúa una expresión (string o bool) en el namespace de calcprop."""
    if isinstance(expr, bool):
        return expr
    if expr == "True":
        return True
    if expr == "False":
        return False
    return eval(expr, _EVAL_NS)
def _make_setup_fn(code_str):
    """Crea un callable setup() a partir de código Python en string."""
    def setup():
        ns = {}
        exec(code_str, ns)
        return {k: v for k, v in ns.items() if not k.startswith('_')}
    return setup
def _componente_from_dict(d):
    tipo          = d.get("tipo")
    enunciado     = d["enunciado"]
    semantica_str = d["semantica"]
    precond_str   = d.get("precond", "True")

    semantica = _eval_expr(semantica_str)
    precond   = _eval_expr(precond_str)

    if tipo == "Supuesto":
        obj = Supuesto(enunciado, semantica, precond)
        obj._json = {"tipo": "Supuesto", "enunciado": enunciado,
                     "semantica": semantica_str, "precond": precond_str}
    elif tipo == "Cuestion":
        exp = d.get("exp", "")
        obj = Cuestion(enunciado, semantica, precond, exp)
        obj._json = {"tipo": "Cuestion", "enunciado": enunciado,
                     "semantica": semantica_str, "precond": precond_str, "exp": exp}
    else:
        raise ValueError(f"Tipo de componente desconocido: {tipo!r}")
    return obj
def _slot_from_json(slot):
    if isinstance(slot, str):
        return slot
    elif isinstance(slot, dict):
        return _componente_from_dict(slot)
    elif isinstance(slot, list):
        return [_slot_from_json(item) for item in slot]
    else:
        raise ValueError(f"Componente JSON inválido: {slot!r}")
def _expr_to_str(val, campo):
    """Convierte una semántica o precondición al string JSON equivalente.

    Usa repr() sobre objetos calcprop (cuyo repr es evaluable con _eval_expr).
    Falla con un mensaje claro si val es un callable (lambda de setup paramétrico).
    """
    if callable(val):
        raise ValueError(
            f"El campo '{campo}' es un callable (lambda). "
            "Los componentes con semánticas o precondiciones lambda solo pueden "
            "serializarse si fueron cargados con load_problema() o problema_from_dict().")
    return repr(val)


def _slot_to_json(slot):
    if isinstance(slot, str):
        return slot
    elif isinstance(slot, (Supuesto, Cuestion)):
        if hasattr(slot, '_json'):
            return slot._json
        # Fallback para objetos creados directamente en Python:
        # repr() de cualquier fórmula calcprop es evaluable por _eval_expr.
        d = {
            'tipo':      'Supuesto' if isinstance(slot, Supuesto) else 'Cuestion',
            'enunciado': slot.e,
            'semantica': _expr_to_str(slot.s, 'semantica'),
            'precond':   _expr_to_str(slot.p, 'precond'),
        }
        if isinstance(slot, Cuestion):
            d['exp'] = slot.x
        return d
    elif isinstance(slot, list):
        return [_slot_to_json(item) for item in slot]
    else:
        raise ValueError(f"Tipo no serializable: {type(slot)}")
def problema_from_dict(d):
    """Crea un ProblemaTipo o ProblemaVF a partir de un dict JSON."""
    tipo = d.get("tipo")

    if tipo == "ProblemaTipo":
        componentes = [_slot_from_json(s) for s in d["componentes"]]
        setup_str   = d.get("setup")
        setup       = _make_setup_fn(setup_str) if setup_str else None
        export      = d.get("export", {})
        seed        = d.get("seed")
        p = ProblemaTipo(componentes, setup=setup, export=export, seed=seed)
        p._nombre    = d.get("nombre", "")
        p._setup_str = setup_str
        return p

    elif tipo == "ProblemaMultiParte":
        # Schema heredado: se aplana a un ProblemaTipo multiparte unificado.
        # Cada subpregunta aporta su intro (material de enunciado) seguido de su
        # sublista de Cuestion; la transición cuestiones->enunciado segmenta las
        # partes (regla I2), de modo que por_partes() reconstruye las subpreguntas.
        componentes = [_slot_from_json(s) for s in d["componentes"]]
        for sp in d["subpreguntas"]:
            componentes.append(sp["intro"])
            componentes.append([_componente_from_dict(c) for c in sp["cuestiones"]])
        setup_str = d.get("setup")
        setup     = _make_setup_fn(setup_str) if setup_str else None
        export    = d.get("export", {})
        seed      = d.get("seed")
        p = ProblemaTipo(componentes, setup=setup, export=export, seed=seed)
        p._nombre    = d.get("nombre", "")
        p._setup_str = setup_str
        return p

    elif tipo == "ProblemaVF":
        enunciado  = d["enunciado"]
        cuestiones = [(c["texto"], c["respuesta"]) for c in d["cuestiones"]]
        num        = d["NumPreguntas"]
        p = ProblemaVF(enunciado, cuestiones, num)
        p._nombre = d.get("nombre", "")
        return p

    else:
        raise ValueError(f"Tipo de problema desconocido: {tipo!r}")
def problema_to_dict(problema):
    """Serializa un ProblemaTipo o ProblemaVF a dict.

    ProblemaTipo con componentes creados directamente en Python se serializa
    usando repr() sobre las fórmulas calcprop. Si alguna semántica o precondición
    es un callable (lambda de setup paramétrico), la serialización falla.
    Los setup definidos como funciones Python (no cargados desde JSON) no pueden
    serializarse; en ese caso se lanza un error. ProblemaVF siempre puede serializarse.
    """
    if isinstance(problema, ProblemaTipo):
        componentes = [_slot_to_json(s) for s in problema.e]
        setup_str = getattr(problema, '_setup_str', None)
        if setup_str is None and problema.setup is not None:
            raise ValueError(
                "ProblemaTipo tiene un setup callable pero no fue creado desde JSON. "
                "No es posible serializar un setup definido directamente en Python. "
                "Escribe el código del setup como cadena y carga el problema con "
                "problema_from_dict().")
        d = {
            "version":     "1",
            "tipo":        "ProblemaTipo",
            "nombre":      getattr(problema, '_nombre', ''),
            "setup":       setup_str,
            "componentes": componentes,
        }
        seed = getattr(problema, 'seed', None)
        if seed is not None:
            d["seed"] = seed
        exp = getattr(problema, 'export', {})
        if exp:
            d["export"] = exp
        return d
    elif isinstance(problema, ProblemaVF):
        return {
            "version":      "1",
            "tipo":         "ProblemaVF",
            "nombre":       getattr(problema, '_nombre', ''),
            "enunciado":    problema.e,
            "NumPreguntas": problema.NumPreguntas,
            "cuestiones":   [{"texto": t, "respuesta": r} for t, r in problema.c],
        }
    else:
        raise ValueError(f"Tipo no soportado: {type(problema)}")
def load_problema(filepath):
    """Carga un único problema desde un fichero JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        d = _json.load(f)
    if "banco" in d:
        raise ValueError(f"{filepath!r} contiene un banco de problemas. Usa load_banco().")
    return problema_from_dict(d)


def save_problema(problema, filepath):
    """Guarda un único problema en un fichero JSON."""
    d = problema_to_dict(problema)
    with open(filepath, 'w', encoding='utf-8') as f:
        _json.dump(d, f, ensure_ascii=False, indent=2)
def load_banco(filepath):
    """Carga un banco de problemas desde un fichero JSON.
    Devuelve una lista de ProblemaTipo / ProblemaVF."""
    with open(filepath, 'r', encoding='utf-8') as f:
        d = _json.load(f)
    if "banco" in d:
        return [problema_from_dict(p) for p in d["banco"]]
    else:
        return [problema_from_dict(d)]


def save_banco(problemas, filepath):
    """Guarda una lista (o dict) de problemas en un fichero JSON de banco."""
    items = list(problemas.values() if isinstance(problemas, dict) else problemas)
    banco = [problema_to_dict(p) for p in items]
    d = {"version": "1", "banco": banco}
    with open(filepath, 'w', encoding='utf-8') as f:
        _json.dump(d, f, ensure_ascii=False, indent=2)
# ── Exportación a código Python ───────────────────────────────────────────────

def _py_text(s):
    """Literal de texto Python legible: usa una raw string cuando es seguro
    (para que el LaTeX se lea sin barras invertidas dobladas) y repr() en caso
    contrario (texto con comillas conflictivas, salto de línea o backslash final)."""
    if "\n" not in s:
        trailing_bs = len(s) - len(s.rstrip("\\"))
        if trailing_bs % 2 == 0:           # raw string segura respecto al backslash final
            if "'" not in s:
                return f"r'{s}'"
            if '"' not in s:
                return f'r"{s}"'
    return repr(s)


def _slot_to_python(slot, nivel=1):
    pad = "    " * nivel

    if isinstance(slot, str):
        return f"{pad}{_py_text(slot)},"

    elif isinstance(slot, dict):
        # Constructor con todos los argumentos nombrados, uno por línea, para
        # que el guión Python resultante sea fácil de leer y editar a mano.
        tipo = slot["tipo"]
        ipad = "    " * (nivel + 1)
        args = [
            f"{ipad}enunciado = {_py_text(slot['enunciado'])},",
            f"{ipad}semantica = {slot['semantica']},",      # cadena evaluable: "v('A')", "True", …
            f"{ipad}precond = {slot.get('precond', 'True')}",
        ]
        if tipo == "Cuestion":
            args[-1] += ","
            args.append(f"{ipad}exp = {_py_text(slot.get('exp', ''))}")
        cuerpo = "\n".join(args)
        return f"{pad}{tipo}(\n{cuerpo}\n{pad}),"

    elif isinstance(slot, list):
        inner = "\n".join(_slot_to_python(item, nivel + 1) for item in slot)
        return f"{pad}[\n{inner}\n{pad}],"

    raise ValueError(f"Tipo no convertible a Python: {type(slot)}")


def problema_to_python(problema, varname="ejercicio"):
    """Genera código Python que recrea el problema como listas editables.

    El fichero resultante puede abrirse con cualquier editor de texto,
    modificarse y ejecutarse directamente con Python. Los problemas multiparte
    se generan como un ProblemaTipo (lista plana), igual que los de una sola parte.
    Para problemas con setup, el código del setup queda como función Python
    editable (_setup). Si el setup es un callable sin _setup_str, falla.
    """
    d = problema_to_dict(problema)

    lines = ["from qbank import Supuesto, Cuestion, ProblemaTipo",
             "from calcprop import *", ""]

    setup_str = d.get("setup")
    if setup_str:
        lines += ["", "def _setup():"]
        for line in setup_str.splitlines():
            lines.append(f"    {line}")
        lines += [
            "    _locs = locals()",
            "    return {k: v for k, v in _locs.items() if not k.startswith('_')}",
            "",
        ]

    setup_arg  = ", setup=_setup" if setup_str else ""
    export_dict = d.get("export", {})
    export_arg  = f", export={export_dict!r}" if export_dict else ""

    lines.append(f"{varname} = [")
    for comp in d["componentes"]:
        lines.append(_slot_to_python(comp, nivel=1))
    lines.append("]")
    lines.append("")
    lines.append(f"p = ProblemaTipo({varname}{setup_arg}{export_arg})")

    lines.append("")
    return "\n".join(lines)


def save_problema_py(problema, filepath, varname="ejercicio"):
    """Guarda el problema como código Python editable en un fichero .py."""
    code = problema_to_python(problema, varname=varname)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
