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
    tipo         = d.get("tipo")
    enunciado    = d["enunciado"]
    semantica_str = d["semantica"]
    precond_str  = d.get("precond", "True")

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


def _slot_to_json(slot):
    if isinstance(slot, str):
        return slot
    elif isinstance(slot, (Supuesto, Cuestion)):
        if not hasattr(slot, '_json'):
            raise ValueError(
                f"El componente '{slot.e}' no fue creado desde JSON. "
                "problema_to_dict() solo funciona con problemas cargados mediante "
                "load_problema() o problema_from_dict().")
        return slot._json
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
        p = ProblemaTipo(componentes, setup=setup)
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

    Para ProblemaTipo, requiere que los componentes (Supuesto/Cuestion) hayan
    sido creados con problema_from_dict() o load_problema(). ProblemaVF siempre
    puede serializarse.
    """
    if isinstance(problema, ProblemaTipo):
        componentes = [_slot_to_json(s) for s in problema.e]
        return {
            "version":     "1",
            "tipo":        "ProblemaTipo",
            "nombre":      getattr(problema, '_nombre', ''),
            "setup":       getattr(problema, '_setup_str', None),
            "componentes": componentes,
        }
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
