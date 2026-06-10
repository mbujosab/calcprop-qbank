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

try:
    import ipywidgets as _w
    from IPython.display import display as _display, clear_output as _clear
    _HAS_WIDGETS = True
except ImportError:
    _HAS_WIDGETS = False

from qbank._quiz import ProblemaTipo, ProblemaTipoProfe
from qbank._json import problema_from_dict, problema_to_dict, load_problema, save_problema


def _need_widgets():
    if not _HAS_WIDGETS:
        raise ImportError(
            "ipywidgets no está instalado. Ejecuta:\n"
            "  pip install ipywidgets")


# ── Widget de una alternativa (Supuesto o Cuestion) ──────────────────────────

class _AltWidget:
    def __init__(self, d=None, on_delete=None):
        if d is None:
            d = {}
        self._on_delete = on_delete

        self.tipo = _w.Dropdown(
            options=['Supuesto', 'Cuestion'],
            value=d.get('tipo', 'Cuestion'),
            layout=_w.Layout(width='95px'))
        self.e = _w.Text(
            value=d.get('enunciado', ''), placeholder='enunciado',
            layout=_w.Layout(width='210px'))
        self.s = _w.Text(
            value=d.get('semantica', 'True'), placeholder="v('A')",
            layout=_w.Layout(width='130px'))
        self.p = _w.Text(
            value=d.get('precond', 'True'), placeholder='precond',
            layout=_w.Layout(width='70px'))
        self.x = _w.Text(
            value=d.get('exp', ''), placeholder='explicación',
            layout=_w.Layout(width='120px'))
        self._exp_lbl = _w.Label('exp:', layout=_w.Layout(width='30px'))

        del_btn = _w.Button(
            description='✕', button_style='danger',
            layout=_w.Layout(width='30px', height='28px'))
        del_btn.on_click(lambda _: self._on_delete(self) if self._on_delete else None)
        self.tipo.observe(lambda _: self._sync_exp(), names='value')
        self._sync_exp()

        self.box = _w.HBox([
            self.tipo,
            _w.Label('e:', layout=_w.Layout(width='15px')), self.e,
            _w.Label('s:', layout=_w.Layout(width='15px')), self.s,
            _w.Label('p:', layout=_w.Layout(width='15px')), self.p,
            self._exp_lbl, self.x,
            del_btn,
        ])

    def _sync_exp(self):
        vis = 'visible' if self.tipo.value == 'Cuestion' else 'hidden'
        self.x.layout.visibility = vis
        self._exp_lbl.layout.visibility = vis

    def to_dict(self):
        d = {'tipo': self.tipo.value, 'enunciado': self.e.value,
             'semantica': self.s.value, 'precond': self.p.value}
        if self.tipo.value == 'Cuestion':
            d['exp'] = self.x.value
        return d
# ── Widget de un slot (texto | lista de alternativas) ─────────────────────────

class _SlotWidget:
    def __init__(self, data=None, on_delete=None, index=0):
        self._on_delete = on_delete
        self._alts = []

        if data is None or isinstance(data, str):
            tipo_init, text_init, alts_init = 'texto', data or '', []
        elif isinstance(data, dict):              # single component
            tipo_init, text_init, alts_init = 'alternativas', '', [data]
        else:                                     # list of components
            tipo_init, text_init, alts_init = 'alternativas', '', data

        self._tipo_dd = _w.Dropdown(
            options=['texto', 'alternativas'], value=tipo_init,
            layout=_w.Layout(width='110px'))
        self._lbl = _w.Label(
            f'Slot {index + 1}', layout=_w.Layout(width='52px'))

        self._text = _w.Text(
            value=text_init, placeholder='texto del enunciado…',
            layout=_w.Layout(width='360px'))

        self._alts_box = _w.VBox([])
        _add_btn = _w.Button(
            description='+ alt', button_style='info',
            layout=_w.Layout(width='70px', height='26px'))
        _add_btn.on_click(lambda _: self._add_alt())
        self._alts_area = _w.VBox([self._alts_box, _add_btn])

        del_btn = _w.Button(
            description='✕', button_style='danger',
            layout=_w.Layout(width='30px', height='28px'))
        del_btn.on_click(lambda _: self._on_delete(self) if self._on_delete else None)

        self._content = _w.HBox([self._text])
        self._tipo_dd.observe(self._on_tipo, names='value')
        self.box = _w.VBox([
            _w.HBox([self._lbl, self._tipo_dd, self._content, del_btn])
        ])

        if tipo_init == 'alternativas':
            self._content.children = [self._alts_area]
            for a in alts_init:
                self._add_alt(a)

    def _on_tipo(self, change):
        self._content.children = (
            [self._text] if change['new'] == 'texto' else [self._alts_area])

    def _add_alt(self, d=None):
        alt = _AltWidget(d=d, on_delete=self._del_alt)
        self._alts.append(alt)
        self._alts_box.children = [a.box for a in self._alts]

    def _del_alt(self, alt):
        self._alts = [a for a in self._alts if a is not alt]
        self._alts_box.children = [a.box for a in self._alts]

    def update_label(self, i):
        self._lbl.value = f'Slot {i + 1}'

    def to_json(self):
        if self._tipo_dd.value == 'texto':
            return self._text.value
        return [a.to_dict() for a in self._alts]
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
        self._setup = _w.Textarea(
            value='', placeholder='código Python del setup (opcional)',
            layout=_w.Layout(width='520px', height='58px'))

        header = _w.VBox([
            _w.HBox([_w.Label('Nombre:', layout=_w.Layout(width='65px')),
                     self._nombre]),
            _w.HBox([_w.Label('Setup:', layout=_w.Layout(width='65px')),
                     self._setup]),
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

        prev_btn  = _w.Button(description='▶ Preview',    button_style='primary',
                               layout=_w.Layout(width='105px'))
        save_btn  = _w.Button(description='💾 Guardar',  layout=_w.Layout(width='95px'))
        load_btn  = _w.Button(description='📂 Cargar',   layout=_w.Layout(width='95px'))
        json_btn  = _w.Button(description='{ } JSON',    layout=_w.Layout(width='95px'))
        dl_btn    = _w.Button(description='⬇ Descargar', layout=_w.Layout(width='105px'))

        prev_btn.on_click(self._on_preview)
        save_btn.on_click(self._on_save)
        load_btn.on_click(self._on_load)
        json_btn.on_click(self._on_show_json)
        dl_btn.on_click(self._on_download)

        self._out = _w.Output()

        self._ui = _w.VBox([
            header,
            _w.HTML('<hr style="margin:4px 0">'),
            self._slots_box,
            add_slot_btn,
            _w.HTML('<hr style="margin:4px 0">'),
            _w.HBox([
                prev_btn,
                _w.Label('vars:', layout=_w.Layout(width='32px')),
                self._n_prev,
                _w.Label('  '),
                save_btn, load_btn,
                _w.Label('  '),
                self._filepath,
                _w.Label('  '),
                json_btn, dl_btn,
            ]),
            self._out,
        ])

        # Carga inicial
        if source is not None:
            self._load_source(source)

        _display(self._ui)

    # ── Gestión de slots ──────────────────────────────────────────

    def _add_slot(self, data=None):
        s = _SlotWidget(data=data, on_delete=self._del_slot,
                        index=len(self._slots))
        self._slots.append(s)
        self._refresh()

    def _del_slot(self, slot):
        self._slots = [s for s in self._slots if s is not slot]
        self._refresh()

    def _refresh(self):
        for i, s in enumerate(self._slots):
            s.update_label(i)
        self._slots_box.children = [s.box for s in self._slots]

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
        self._slots = []
        for comp in d.get('componentes', []):
            self._add_slot(data=comp)

    # ── Serialización ─────────────────────────────────────────────

    def to_dict(self):
        """Devuelve el problema actual como dict JSON."""
        setup = self._setup.value.strip() or None
        return {
            'version':     '1',
            'tipo':        'ProblemaTipo',
            'nombre':      self._nombre.value,
            'setup':       setup,
            'componentes': [s.to_json() for s in self._slots],
        }

    def to_problema(self):
        """Devuelve un ProblemaTipo listo para iterar."""
        return problema_from_dict(self.to_dict())

    # ── Callbacks de botones ──────────────────────────────────────

    def _on_preview(self, _):
        with self._out:
            _clear()
            try:
                # Vista «profe»: para cada combinación de supuestos se muestran
                # todas las cuestiones posibles (sin descartar las inconsistentes),
                # marcando cada una como correcta/incorrecta.
                p   = self.to_problema()
                n   = self._n_prev.value
                cnt = 0
                for var in ProblemaTipoProfe(p.e, setup=p.setup):
                    if cnt >= n:
                        break
                    id_, enunciado, cuestiones = var
                    print(f"── Variante {id_} ──  {enunciado}")
                    for c in cuestiones:
                        mark = '✓' if c[1] is True else ('✗' if c[1] is False else '?')
                        print(f"   {mark} {c[0]}")
                    cnt += 1
                if cnt == 0:
                    print("(sin variantes)")
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
