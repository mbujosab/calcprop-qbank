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
from qbank._quiz import (Supuesto, Cuestion, ProblemaTipo, ProblemaVF,
                         _EVAL_NS, _eval_expr)

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

def _componente_from_dict(d):
    tipo          = d.get("tipo")
    enunciado     = d["enunciado"]
    semantica_str = d["semantica"]
    precond_str   = d.get("precond", "True")

    semantica = _eval_expr(semantica_str)
    precond   = _eval_expr(precond_str)

    motivo    = d.get("motivo", "")

    if tipo == "Supuesto":
        obj = Supuesto(enunciado, semantica, precond, motivo=motivo)
        obj._json = {"tipo": "Supuesto", "enunciado": enunciado,
                     "semantica": semantica_str, "precond": precond_str}
    elif tipo == "Cuestion":
        exp = d.get("exp", "")
        obj = Cuestion(enunciado, semantica, precond, exp, motivo=motivo)
        obj._json = {"tipo": "Cuestion", "enunciado": enunciado,
                     "semantica": semantica_str, "precond": precond_str, "exp": exp}
    else:
        raise ValueError(f"Tipo de componente desconocido: {tipo!r}")
    if "motivo" in d:
        obj._json["motivo"] = motivo
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

    Devuelve la cadena original si se escribió como tal, repr() sobre objetos
    calcprop (cuyo repr es evaluable con _eval_expr), y falla con un mensaje
    claro si val es una función Python (lambda), cuyo código no es recuperable.
    """
    if isinstance(val, str):
        return val
    if callable(val):
        raise ValueError(
            f"El campo '{campo}' es una función Python (lambda) y no puede guardarse. "
            "Escríbela como cadena, p. ej. precond=\"lambda ns: ns['x'] > 0\".")
    return repr(val)


def _slot_to_json(slot):
    if isinstance(slot, str):
        return slot
    elif isinstance(slot, (Supuesto, Cuestion)):
        if hasattr(slot, '_json'):
            return slot._json
        # Objetos creados directamente en Python: valores tal como se escribieron.
        semantica, precond = getattr(slot, '_orig', (slot.s, slot.p))
        d = {
            'tipo':      'Supuesto' if isinstance(slot, Supuesto) else 'Cuestion',
            'enunciado': slot.e,
            'semantica': _expr_to_str(semantica, 'semantica'),
            'precond':   _expr_to_str(precond, 'precond'),
        }
        if isinstance(slot, Cuestion):
            d['exp'] = None if slot.x is None else _expr_to_str(slot.x, 'exp')
        if getattr(slot, 'motivo', ''):
            d['motivo'] = slot.motivo
        return d
    elif isinstance(slot, list):
        return [_slot_to_json(item) for item in slot]
    else:
        raise ValueError(f"Tipo no serializable: {type(slot)}")
_CLAVES_PROBLEMA = {"version", "tipo", "nombre", "setup", "seed", "export", "lectura", "componentes"}


def problema_from_dict(d):
    """Crea un ProblemaTipo o ProblemaVF a partir de un dict JSON."""
    tipo = d.get("tipo")

    if tipo == "ProblemaTipo":
        componentes = [_slot_from_json(s) for s in d["componentes"]]
        p = ProblemaTipo(componentes, setup=d.get("setup") or None,
                         export=d.get("export", {}), seed=d.get("seed"),
                         nombre=d.get("nombre", ""), lectura=d.get("lectura"))
        # Claves propias del usuario (p. ej. "_nivel"): se conservan para que
        # save_problema las devuelva intactas.
        p._extra = {k: v for k, v in d.items() if k not in _CLAVES_PROBLEMA}
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
        return ProblemaTipo(componentes, setup=d.get("setup") or None,
                            export=d.get("export", {}), seed=d.get("seed"),
                            nombre=d.get("nombre", ""))

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
                "El setup de este ProblemaTipo es una función Python y su código no es "
                "recuperable. Pásalo como cadena de código: "
                "ProblemaTipo(..., setup=\"import numpy as np\\nx = ...\").")
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
        lectura = getattr(problema, 'lectura', None)
        if lectura:
            d["lectura"] = lectura
        d.update(getattr(problema, '_extra', {}))       # claves propias del usuario
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
    """Carga un único problema desde un fichero JSON o desde un dict en memoria."""
    if isinstance(filepath, dict):
        d = filepath
    else:
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


def _py_expr(s):
    """Semántica o precondición en el guión: las fórmulas calcprop y True/False
    tal cual (son código Python válido); las lambdas entre comillas, como
    cadena, que es como ProblemaTipo las acepta y save_problema las guarda."""
    return repr(s) if s.strip().startswith("lambda") else s


def _py_bloque(s):
    """Literal de varias líneas para el código del setup: raw string triple
    cuando es seguro, repr() en caso contrario."""
    if '"""' not in s and not s.endswith("\\"):
        return 'r"""' + s + '"""'
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
            f"{ipad}semantica = {_py_expr(slot['semantica'])},",   # "v('A')", "True", "lambda ns: …"
            f"{ipad}precond = {_py_expr(slot.get('precond', 'True'))}",
        ]
        if tipo == "Cuestion":
            args[-1] += ","
            args.append(f"{ipad}exp = {_py_text(slot.get('exp', ''))}")
        if slot.get('motivo'):
            args[-1] += ","
            args.append(f"{ipad}motivo = {_py_text(slot['motivo'])}")
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
    El código del setup, si lo hay, queda en la cadena _SETUP (el mismo texto
    que guarda el JSON) y las lambdas como cadenas, de modo que el guión
    puede volver a guardarse con save_problema. Si el setup es un callable
    sin _setup_str, falla.
    """
    d = problema_to_dict(problema)

    lines = ["from qbank import Supuesto, Cuestion, ProblemaTipo",
             "from calcprop import *", ""]

    setup_str = d.get("setup")
    if setup_str:
        lines += ["", f"_SETUP = {_py_bloque(setup_str)}", ""]

    setup_arg  = ", setup=_SETUP" if setup_str else ""
    seed       = d.get("seed")
    seed_arg   = f", seed={seed!r}" if seed is not None else ""
    export_dict = d.get("export", {})
    export_arg  = f", export={export_dict!r}" if export_dict else ""
    nombre      = d.get("nombre") or ""
    nombre_arg  = f", nombre={nombre!r}" if nombre else ""
    lectura     = d.get("lectura", {})
    lectura_arg = f", lectura={lectura!r}" if lectura else ""

    lines.append(f"{varname} = [")
    for comp in d["componentes"]:
        lines.append(_slot_to_python(comp, nivel=1))
    lines.append("]")
    lines.append("")
    lines.append(f"p = ProblemaTipo({varname}{setup_arg}{seed_arg}{export_arg}{nombre_arg}{lectura_arg})")

    lines.append("")
    return "\n".join(lines)


def save_problema_py(problema, filepath, varname="ejercicio"):
    """Guarda el problema como código Python editable en un fichero .py."""
    code = problema_to_python(problema, varname=varname)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
