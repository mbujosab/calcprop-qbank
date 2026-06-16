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
Editor visual de ProblemaTipo para Jupyter (ipywidgets).

Uso básico::

    from qbank import ProblemaTipoEditor

    # Editor vacío
    editor = ProblemaTipoEditor()

    # Editor cargado desde fichero JSON
    editor = ProblemaTipoEditor('mi_ejercicio.json')

    # Editor cargado desde un problema ya en memoria
    p = load_problema('mi_ejercicio.json')
    editor = ProblemaTipoEditor(p)

    # Obtener el problema editado
    p = editor.to_problema()
"""

__all__ = ['ProblemaTipoEditor']

import io as _io
import contextlib as _contextlib

try:
    import ipywidgets as _w
    from IPython.display import display as _display, clear_output as _clear
    _HAS_WIDGETS = True
except ImportError:
    _HAS_WIDGETS = False

from qbank._quiz import (ProblemaTipo, Cuestion,
                         _plan_partes, _normaliza_slot)
from qbank._json import problema_from_dict, problema_to_dict, load_problema, save_problema, problema_to_python


def _need_widgets():
    if not _HAS_WIDGETS:
        raise ImportError(
            "ipywidgets no está instalado. Ejecuta:\n"
            "  pip install ipywidgets")


# ── Widget de una alternativa (texto | Supuesto | Cuestion) ──────────────────

class _AltWidget:
    """Una alternativa dentro de un slot. Su tipo (=kind=) lo fija el slot
    padre, de modo que un slot nunca mezcla tipos (invariante I1)."""

    def __init__(self, kind='Cuestion', d=None, on_delete=None, on_move=None):
        self._kind = kind
        self._on_delete = on_delete
        self._on_move = on_move
        if isinstance(d, str):
            d = {'enunciado': d}
        elif d is None:
            d = {}

        self.e = _w.Text(
            value=d.get('enunciado', ''), placeholder='enunciado',
            layout=_w.Layout(width='260px'))

        up_btn = _w.Button(
            description='▲', tooltip='subir alternativa',
            layout=_w.Layout(width='auto', height='28px'))
        dn_btn = _w.Button(
            description='▼', tooltip='bajar alternativa',
            layout=_w.Layout(width='auto', height='28px'))
        up_btn.on_click(lambda _: self._on_move(self, -1) if self._on_move else None)
        dn_btn.on_click(lambda _: self._on_move(self, +1) if self._on_move else None)
        del_btn = _w.Button(
            description='✕', button_style='danger',
            layout=_w.Layout(width='auto', height='28px'))
        del_btn.on_click(lambda _: self._on_delete(self) if self._on_delete else None)

        if kind == 'texto':
            fila = [_w.Label('txt:', layout=_w.Layout(width='30px')), self.e]
        else:
            self.s = _w.Text(
                value=d.get('semantica', 'True'), placeholder="v('A')",
                layout=_w.Layout(width='130px'))
            self.p = _w.Text(
                value=d.get('precond', 'True'), placeholder='precond',
                layout=_w.Layout(width='70px'))
            fila = [
                _w.Label('e:', layout=_w.Layout(width='15px')), self.e,
                _w.Label('s:', layout=_w.Layout(width='15px')), self.s,
                _w.Label('p:', layout=_w.Layout(width='15px')), self.p,
            ]
            if kind == 'Cuestion':
                self.x = _w.Text(
                    value=d.get('exp', ''), placeholder='explicación',
                    layout=_w.Layout(width='120px'))
                fila += [_w.Label('exp:', layout=_w.Layout(width='30px')), self.x]

        self.box = _w.HBox(fila + [up_btn, dn_btn, del_btn])

    def raw(self):
        """Datos comunes de la alternativa, para conservarlos cuando el slot
        padre cambia de tipo."""
        d = {'enunciado': self.e.value}
        if self._kind != 'texto':
            d['semantica'] = self.s.value
            d['precond']   = self.p.value
        if self._kind == 'Cuestion':
            d['exp'] = self.x.value
        return d

    def to_json(self):
        if self._kind == 'texto':
            return self.e.value
        d = {'tipo': self._kind, 'enunciado': self.e.value,
             'semantica': self.s.value, 'precond': self.p.value}
        if self._kind == 'Cuestion':
            d['exp'] = self.x.value
        return d
# ── Widget de un slot (texto | supuestos | cuestiones) ───────────────────────

class _SlotWidget:
    """Un «hueco» del problema: lista de alternativas homogéneas de un único
    tipo. El tipo del slot fija el de sus alternativas, garantizando I1."""

    # tipo de slot -> kind de las alternativas
    _KIND = {'texto': 'texto', 'supuestos': 'Supuesto', 'cuestiones': 'Cuestion'}

    def __init__(self, data=None, tipo=None, on_delete=None, on_change=None,
                 on_move=None, on_insert=None, index=0):
        self._on_delete = on_delete
        self._on_change = on_change
        self._on_move   = on_move
        self._on_insert = on_insert
        self._alts = []

        if data is None and tipo is not None:
            tipo_init, alts_init = tipo, []       # slot nuevo del tipo indicado
        else:
            tipo_init, alts_init = self._inferir(data)

        self._tipo_dd = _w.Dropdown(
            options=['texto', 'supuestos', 'cuestiones'], value=tipo_init,
            layout=_w.Layout(width='110px'))
        self._lbl = _w.Label(
            f'Slot {index + 1}', layout=_w.Layout(width='52px'))

        self._alts_box = _w.VBox([])
        add_btn = _w.Button(
            description='+ alt', button_style='info',
            layout=_w.Layout(width='70px', height='26px'))
        add_btn.on_click(lambda _: self._add_alt())

        up_btn = _w.Button(
            description='▲', tooltip='subir slot',
            layout=_w.Layout(width='auto', height='28px'))
        dn_btn = _w.Button(
            description='▼', tooltip='bajar slot',
            layout=_w.Layout(width='auto', height='28px'))
        ins_btn = _w.Button(
            description='＋', tooltip='insertar slot debajo', button_style='success',
            layout=_w.Layout(width='auto', height='28px'))
        up_btn.on_click(lambda _: self._on_move(self, -1) if self._on_move else None)
        dn_btn.on_click(lambda _: self._on_move(self, +1) if self._on_move else None)
        ins_btn.on_click(lambda _: self._on_insert(self) if self._on_insert else None)
        del_btn = _w.Button(
            description='✕', button_style='danger',
            layout=_w.Layout(width='auto', height='28px'))
        del_btn.on_click(lambda _: self._on_delete(self) if self._on_delete else None)

        self._tipo_dd.observe(self._on_tipo, names='value')
        self.box = _w.VBox([
            _w.HBox([self._lbl, self._tipo_dd, up_btn, dn_btn, ins_btn, del_btn]),
            self._alts_box,
            add_btn,
        ])

        for a in alts_init:
            self._add_alt(a)
        if not self._alts:                        # un slot nuevo arranca con
            self._add_alt()                       # una alternativa vacía

    @staticmethod
    def _inferir(data):
        """(tipo_slot, [datos_de_alternativa]) a partir del componente JSON."""
        if data is None:
            return 'texto', []
        if isinstance(data, str):
            return 'texto', [data]
        if isinstance(data, dict):                # componente suelto
            tipo = data.get('tipo', 'Cuestion')
            return ('supuestos' if tipo == 'Supuesto' else 'cuestiones'), [data]
        if not data:                              # lista vacía
            return 'texto', []
        first = data[0]                           # sublista homogénea
        if isinstance(first, str):
            return 'texto', list(data)
        tipo = first.get('tipo', 'Cuestion') if isinstance(first, dict) else 'Cuestion'
        return ('supuestos' if tipo == 'Supuesto' else 'cuestiones'), list(data)

    def tipo(self):
        return self._tipo_dd.value

    def _on_tipo(self, change):
        # Reconstruye las alternativas con el nuevo tipo conservando los datos
        # comunes (enunciado, etc.) y avisa al editor para repintar separadores.
        datos = [a.raw() for a in self._alts]
        self._alts = []
        for d in datos:
            self._add_alt(d)
        if not self._alts:
            self._add_alt()
        if self._on_change:
            self._on_change()

    def _add_alt(self, d=None):
        kind = self._KIND[self._tipo_dd.value]
        alt = _AltWidget(kind=kind, d=d, on_delete=self._del_alt,
                         on_move=self._move_alt)
        self._alts.append(alt)
        self._render_alts()

    def _del_alt(self, alt):
        self._alts = [a for a in self._alts if a is not alt]
        self._render_alts()

    def _move_alt(self, alt, delta):
        i = self._alts.index(alt)
        j = i + delta
        if 0 <= j < len(self._alts):
            self._alts[i], self._alts[j] = self._alts[j], self._alts[i]
            self._render_alts()

    def _render_alts(self):
        self._alts_box.children = [a.box for a in self._alts]

    def update_label(self, i):
        self._lbl.value = f'Slot {i + 1}'

    def to_json(self):
        if self._tipo_dd.value == 'texto':
            textos = [a.to_json() for a in self._alts]
            if len(textos) <= 1:                  # cadena suelta (no en [...])
                return textos[0] if textos else ''
            return textos                         # sublista de textos alternativos
        return [a.to_json() for a in self._alts]
# ── Editor principal ───────────────────────────────────────────────────────────

class ProblemaTipoEditor:
    """Editor visual de ProblemaTipo para Jupyter.

    Parameters
    ----------
    source : str | dict | ProblemaTipo | None
        Fuente inicial. Puede ser la ruta a un fichero JSON, un dict,
        un objeto ProblemaTipo (creado con load_problema), o None para
        empezar un problema nuevo.
    """

    def __init__(self, source=None):
        _need_widgets()
        self._slots = []

        # ── Cabecera ──
        self._nombre = _w.Text(
            value='', placeholder='nombre del ejercicio',
            layout=_w.Layout(width='320px'))
        self._nombre_warn = _w.HTML(value='')
        self._nombre.observe(self._on_nombre_change, names='value')
        self._setup = _w.Textarea(
            value='', placeholder='código Python del setup (opcional)',
            layout=_w.Layout(width='380px', height='58px'))
        self._seed = _w.Text(
            value='', placeholder='sin semilla',
            layout=_w.Layout(width='100px'))
        self._last_choice = _w.Checkbox(
            value=False, description='last_choice', indent=False,
            layout=_w.Layout(width='130px'))
        self._cols = _w.BoundedIntText(
            value=1, min=1, max=10,
            layout=_w.Layout(width='55px'))

        header = _w.VBox([
            _w.HBox([_w.Label('Nombre:', layout=_w.Layout(width='65px')),
                     self._nombre, self._nombre_warn]),
            _w.HBox([_w.Label('Setup:', layout=_w.Layout(width='65px')),
                     self._setup,
                     _w.Label('semilla:', layout=_w.Layout(width='60px')),
                     self._seed]),
            _w.HBox([_w.Label('Export:', layout=_w.Layout(width='65px')),
                     self._last_choice,
                     _w.Label('cols:', layout=_w.Layout(width='35px')),
                     self._cols]),
        ])

        # ── Zona de slots ──
        self._slots_box = _w.VBox([])
        add_slot_btn = _w.Button(
            description='+ slot', button_style='success',
            layout=_w.Layout(width='85px'))
        add_slot_btn.on_click(lambda _: self._add_slot())

        # ── Controles inferiores ──
        self._filepath = _w.Text(
            value='problema.json', placeholder='ruta del fichero JSON',
            layout=_w.Layout(width='260px'))
        self._n_prev = _w.BoundedIntText(
            value=5, min=1, max=100,
            layout=_w.Layout(width='55px'))
        self._profe = _w.Checkbox(
            value=True, description='vista profe', indent=False,
            layout=_w.Layout(width='110px'))

        prev_btn  = _w.Button(description='▶ Preview',    button_style='primary',
                               layout=_w.Layout(width='105px'))
        json_btn  = _w.Button(description='{ } JSON',    layout=_w.Layout(width='95px'))
        showpy_btn= _w.Button(description='</> .py',     layout=_w.Layout(width='95px'))
        save_btn  = _w.Button(description='💾 Guardar',  layout=_w.Layout(width='95px'))
        load_btn  = _w.Button(description='📂 Cargar',   layout=_w.Layout(width='95px'))
        dl_btn    = _w.Button(description='⬇ .json',     layout=_w.Layout(width='85px'))
        py_btn    = _w.Button(description='⬇ .py',       layout=_w.Layout(width='80px'))

        prev_btn.on_click(self._on_preview)
        json_btn.on_click(self._on_show_json)
        showpy_btn.on_click(self._on_show_py)
        save_btn.on_click(self._on_save)
        load_btn.on_click(self._on_load)
        dl_btn.on_click(self._on_download)
        py_btn.on_click(self._on_download_py)

        self._out = _w.Output()

        # Dos filas de controles: previsualización arriba, fichero/descargas abajo.
        fila_preview = _w.HBox([
            prev_btn,
            _w.Label('vars:', layout=_w.Layout(width='32px')),
            self._n_prev,
            self._profe,
            _w.Label(' ', layout=_w.Layout(width='12px')),
            json_btn, showpy_btn,
        ])
        fila_fichero = _w.HBox([
            self._filepath,
            save_btn, load_btn,
            _w.Label(' ', layout=_w.Layout(width='12px')),
            dl_btn, py_btn,
        ])

        self._ui = _w.VBox([
            header,
            _w.HTML('<hr style="margin:4px 0">'),
            self._slots_box,
            add_slot_btn,
            _w.HTML('<hr style="margin:4px 0">'),
            fila_preview,
            fila_fichero,
            self._out,
        ])

        # Carga inicial
        if source is not None:
            self._load_source(source)

        _display(self._ui)

    # ── Gestión de slots ──────────────────────────────────────────

    def _make_slot(self, data=None, tipo=None):
        return _SlotWidget(data=data, tipo=tipo, on_delete=self._del_slot,
                           on_change=self._refresh, on_move=self._move_slot,
                           on_insert=self._insert_slot_after)

    def _add_slot(self, data=None):
        # Un slot nuevo (botón «+ slot») hereda el tipo del último, de modo que
        # encadenar varias cuestiones no dispare un separador de parte prematuro:
        # la parte nueva solo se marca cuando el docente elige un tipo texto o
        # supuestos tras las cuestiones (inicio explícito de la nueva parte).
        tipo = self._slots[-1].tipo() if (data is None and self._slots) else None
        self._slots.append(self._make_slot(data=data, tipo=tipo))
        self._refresh()

    def _insert_slot_after(self, slot):
        # Inserta un slot nuevo justo debajo de `slot`, heredando su tipo (p. ej.
        # para añadir otra sublista a una parte anterior antes del separador).
        i = self._slots.index(slot)
        self._slots.insert(i + 1, self._make_slot(tipo=slot.tipo()))
        self._refresh()

    def _move_slot(self, slot, delta):
        i = self._slots.index(slot)
        j = i + delta
        if 0 <= j < len(self._slots):
            self._slots[i], self._slots[j] = self._slots[j], self._slots[i]
            self._refresh()

    def _del_slot(self, slot):
        self._slots = [s for s in self._slots if s is not slot]
        self._refresh()

    def _plan_partes(self):
        """Índice de parte de cada slot (regla I2), reutilizando la lógica
        canónica de =_quiz=: un slot 'cuestiones' aporta una Cuestion; los
        demás (texto / supuestos), una cadena."""
        muestra = [Cuestion('', 'True') if s.tipo() == 'cuestiones' else ''
                   for s in self._slots]
        return _plan_partes([_normaliza_slot(x) for x in muestra])

    def _refresh(self):
        plan = self._plan_partes()
        npar = (plan[-1] + 1) if plan else 1
        children, parte_actual = [], -1
        for i, s in enumerate(self._slots):
            s.update_label(i)
            if npar > 1 and plan[i] != parte_actual:   # frontera de parte (I2)
                parte_actual = plan[i]
                children.append(_w.HTML(
                    f'<div style="color:#888;font-weight:bold;margin:6px 0 2px">'
                    f'── Parte {parte_actual + 1} ──</div>'))
            children.append(s.box)
        self._slots_box.children = children

    # ── Carga de datos ────────────────────────────────────────────

    def _load_source(self, source):
        if isinstance(source, str):
            p = load_problema(source)
            self._filepath.value = source
            d = problema_to_dict(p)
        elif isinstance(source, ProblemaTipo):
            d = problema_to_dict(source)
        elif isinstance(source, dict):
            d = source
        else:
            raise ValueError(f"Fuente no reconocida: {type(source)}")

        self._nombre.value = d.get('nombre', '')
        self._setup.value  = d.get('setup', '') or ''
        seed = d.get('seed')
        self._seed.value   = str(seed) if seed is not None else ''
        exp = d.get('export', {})
        self._last_choice.value = bool(exp.get('last_choice', False))
        self._cols.value        = int(exp.get('cols', 1))
        self._slots = []
        for comp in d.get('componentes', []):
            self._add_slot(data=comp)

    # ── Serialización ─────────────────────────────────────────────

    def to_dict(self):
        """Devuelve el problema actual como dict JSON."""
        setup = self._setup.value.strip() or None
        seed_str = self._seed.value.strip()
        try:
            seed = int(seed_str) if seed_str else None
        except ValueError:
            seed = None
        exp = {}
        if self._last_choice.value:
            exp['last_choice'] = True
        if self._cols.value != 1:
            exp['cols'] = self._cols.value
        d = {
            'version':     '1',
            'tipo':        'ProblemaTipo',
            'nombre':      self._nombre.value,
            'setup':       setup,
            'componentes': [s.to_json() for s in self._slots],
        }
        if seed is not None:
            d['seed'] = seed
        if exp:
            d['export'] = exp
        return d

    def to_problema(self):
        """Devuelve un ProblemaTipo listo para iterar."""
        return problema_from_dict(self.to_dict())

    # ── Callbacks de botones ──────────────────────────────────────

    def _on_nombre_change(self, change):
        nombre = change['new']
        if ':' in nombre:
            self._nombre_warn.value = (
                '<span style="color:#c00;margin-left:8px">'
                '⚠ «:» rompe GNU Make — usa «-» en su lugar</span>')
        else:
            self._nombre_warn.value = ''

    def _on_preview(self, _):
        with self._out:
            _clear()
            try:
                # Vista por partes: cada parte muestra su enunciado en una línea
                # y, debajo, sus cuestiones; el enunciado de la parte k+1 aparece
                # tras las cuestiones de la parte k (no concatenado al principio).
                # Con la casilla «vista profe» desmarcada se usa por_partes() —la
                # misma salida que ven el alumno y los exportadores (WYSIWYG)—;
                # marcada, por_partes_profe() muestra TODAS las cuestiones de cada
                # sublista y marca como rechazadas (⊘) las que no superan su
                # precondición, en vez de descartar la variante.
                p     = self.to_problema()
                n     = self._n_prev.value
                profe = self._profe.value
                if profe:
                    print("» vista profe: todas las cuestiones; ⊘ = rechazada "
                          "por precondición (no la ve el alumno).\n")
                variantes = p.por_partes_profe() if profe else p.por_partes()
                cnt = 0
                for etiqueta, partes in variantes:
                    print(f"── Variante {etiqueta} ──")
                    for enunciado, cuestiones in partes:
                        if enunciado:
                            print(enunciado)
                        for c in cuestiones:
                            if c[1] is True:
                                print(f"   ✓ {c[0]}")
                            elif c[1] is False:
                                print(f"   ✗ {c[0]}")
                            else:                       # rechazada: c[1] es el motivo
                                print(f"   ⊘ {c[0]}  [{c[1]}]")
                    print()
                    cnt += 1
                    if cnt >= n:
                        break
                if cnt == 0:
                    print("(sin variantes)")
                if not profe:
                    with _contextlib.redirect_stdout(_io.StringIO()):
                        remaining = sum(1 for _ in variantes)
                    total = cnt + remaining
                    print(f"» {total} variante{'s' if total != 1 else ''} válida{'s' if total != 1 else ''} en total.")
            except Exception as exc:
                print(f"Error: {exc}")

    def _on_save(self, _):
        with self._out:
            _clear()
            try:
                path = self._filepath.value.strip()
                p    = problema_from_dict(self.to_dict())
                save_problema(p, path)
                print(f"✓ Guardado en {path!r}")
            except Exception as exc:
                print(f"Error al guardar: {exc}")

    def _on_load(self, _):
        with self._out:
            _clear()
            try:
                path = self._filepath.value.strip()
                self._slots = []
                self._load_source(path)
                print(f"✓ Cargado desde {path!r}")
            except Exception as exc:
                print(f"Error al cargar: {exc}")

    def _on_show_json(self, _):
        with self._out:
            _clear()
            try:
                import json
                print(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))
            except Exception as exc:
                print(f"Error: {exc}")

    def _on_show_py(self, _):
        # Previsualiza el guión Python (problema_to_python) en el área de salida,
        # de forma análoga a {JSON}, sin generar el enlace de descarga.
        with self._out:
            _clear()
            try:
                p = problema_from_dict(self.to_dict())
                print(problema_to_python(p))
            except Exception as exc:
                print(f"Error: {exc}")

    def _on_download(self, _):
        # JupyterLab no ejecuta el JS de IPython.display.Javascript desde un
        # callback de botón (solo muestra «<IPython.core.display.Javascript object>»).
        # En su lugar mostramos un enlace HTML con el JSON embebido como data URI
        # (atributo `download`): el navegador lo descarga al pulsarlo, sin ejecutar JS.
        import json as _j
        import os, base64
        from IPython.display import HTML
        with self._out:
            _clear()
            try:
                data     = _j.dumps(self.to_dict(), ensure_ascii=False, indent=2)
                filename = os.path.basename(self._filepath.value.strip() or 'problema.json')
                b64      = base64.b64encode(data.encode('utf-8')).decode('ascii')
                href     = f"data:application/json;base64,{b64}"
                _display(HTML(
                    f'<a download="{filename}" href="{href}" '
                    f'style="font-size:14px;font-weight:bold">'
                    f'⬇ Descargar {filename}</a>'
                    f'<br><span style="color:gray">(pulsa el enlace para guardar el fichero)</span>'))
            except Exception as exc:
                print(f"Error al descargar: {exc}")

    def _on_download_py(self, _):
        # Igual que _on_download pero exporta el problema como guión Python
        # editable (problema_to_python). El nombre del fichero se deriva de la
        # ruta JSON cambiando la extensión a .py.
        import os, base64
        from IPython.display import HTML
        with self._out:
            _clear()
            try:
                p        = problema_from_dict(self.to_dict())
                code     = problema_to_python(p)
                base     = os.path.basename(self._filepath.value.strip() or 'problema.json')
                filename = os.path.splitext(base)[0] + '.py'
                b64      = base64.b64encode(code.encode('utf-8')).decode('ascii')
                href     = f"data:text/x-python;base64,{b64}"
                _display(HTML(
                    f'<a download="{filename}" href="{href}" '
                    f'style="font-size:14px;font-weight:bold">'
                    f'⬇ Descargar {filename}</a>'
                    f'<br><span style="color:gray">(pulsa el enlace para guardar el fichero)</span>'))
            except Exception as exc:
                print(f"Error al descargar: {exc}")
