# Copyright (C) 2020-2026  Andrés Bujosa, Marcos Bujosa
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

from calcprop import *
from string import Template

import calcprop as _calcprop_mod
import textwrap as _textwrap

_EVAL_NS = vars(_calcprop_mod).copy()   # espacio de nombres para evaluar cadenas

def _eval_expr(expr):
    """Evalúa una semántica o precondición escrita como cadena en el espacio
    de nombres de calcprop; los valores que no son cadenas se devuelven tal
    cual. "True"/"False" (en cualquier caja) son los booleanos; una cadena
    vacía o inválida produce un ValueError que dice qué expresión falló."""
    if not isinstance(expr, str):
        return expr
    texto = expr.strip()
    if texto.lower() == "true":
        return True
    if texto.lower() == "false":
        return False
    if not texto:
        raise ValueError('expresión vacía: escribe "True", "False", una fórmula v(...) o una lambda')
    try:
        return eval(texto, _EVAL_NS)
    except Exception as e:                                  # noqa: BLE001
        raise ValueError(f"no se puede evaluar {expr!r}: {type(e).__name__}: {e}") from None

def _eval_campo(valor, campo, clase, enunciado):
    """_eval_expr con el componente y el campo en el mensaje de error."""
    try:
        return _eval_expr(valor)
    except ValueError as e:
        raise ValueError(f"{clase} {str(enunciado)[:50]!r}, campo {campo}: {e}") from None

def _siembra(semilla):
    """Siembra los generadores que puede usar un setup: numpy.random (si está
    instalado) y el módulo random de Python, con la misma semilla."""
    if semilla is None:
        return
    import random as _random
    _random.seed(int(semilla))
    try:
        import numpy as _np
        _np.random.seed(int(semilla))
    except ImportError:
        pass

def _setup_desde_str(code_str):
    """Callable setup() a partir del código Python (cadena) de un setup.
    Se elimina la indentación común, para admitir cadenas escritas dentro de
    un bloque indentado."""
    codigo = _textwrap.dedent(code_str)
    def setup():
        ns = {}
        exec(codigo, ns)
        return {k: v for k, v in ns.items() if not k.startswith('_')}
    return setup

class _NsTemplate(Template):
    delimiter = '@'

def _ns_eval(val, ns):
    return val(ns) if callable(val) else val

STRICT_INTERP = False   # si True, _ns_interp lanza ValueError ante @{var} desconocida

def _vars_sin_resolver(s):
    """Nombres @{var} que quedan sin sustituir en un texto."""
    return [m.group('braced') for m in _NsTemplate.pattern.finditer(s) if m.group('braced')]

def _ns_interp(s, ns, strict=None):
    """Sustituye @{var} / @var por los valores de ns. Con strict=True (o el
    módulo con STRICT_INTERP=True) lanza ValueError si queda alguna @{var}
    sin resolver; por defecto la deja intacta."""
    out = _NsTemplate(s).safe_substitute(ns or {})     # también sin setup: @@ → @
    if strict is None:
        strict = STRICT_INTERP
    if strict:
        faltan = _vars_sin_resolver(out)
        if faltan:
            raise ValueError(f"interpolación: variable(s) desconocida(s) {faltan} en {s[:60]!r}")
    return out

def _fuente_precond(componente):
    """Representación legible de la precondición de un componente.

    Si el componente se cargó desde JSON, devuelve la cadena de código
    original (p. ej. ``lambda ns: ns['a'] > ns['b']``); en otro caso usa
    ``repr()``, que para una lambda definida directamente en Python da algo
    como ``<function <lambda> at 0x...>``.
    """
    j = getattr(componente, '_json', None)
    if j and j.get('precond') is not None:
        return j['precond']
    orig = getattr(componente, '_orig', None)
    if orig and isinstance(orig[1], str):
        return orig[1]
    return repr(componente.p)
def CuestionesJuntas(lista):
    def CreaLista(t):
        return t if isinstance(t, list) else [t]
    p = []
    for e in lista:
        if isinstance(e,str):
            p.append(e)
        elif not isinstance(CreaLista(e)[0],Cuestion):
            p.append(e)
        else:
            p.extend(CreaLista(e))
    return p
from collections import namedtuple as _namedtuple

Lectura      = _namedtuple('Lectura', 'etiqueta mundo ns partes descarte')
ParteLectura = _namedtuple('ParteLectura', 'enunciado huecos')
Alternativa  = _namedtuple('Alternativa', 'texto valor exp motivo')
class Marcador:
    def __init__(self, data):
        self.data = data
    def __iter__(self):
        self.p = [0 for x in self.data]
        return self
    def __next__(self):
        def Siguiente(x,y):
            if x == [] :
                return []
            s = Siguiente(x[1:],y[1:])
            if s == []:
                if x[0]+1 == y[0]:
                    return []
                else:
                    return [x[0]+1] + [0 for i in x[1:]]
            else:
                return [x[0]] + s
        if self.p == []:
            raise StopIteration
        n = self.p
        self.p = Siguiente(self.p, self.data)
        return n

class Supuesto:
    def __init__(self, enunciado, semantica, precond=True):
        self.e = enunciado
        self.s = _eval_campo(semantica, 'semantica', 'Supuesto', enunciado)
        self.p = _eval_campo(precond, 'precond', 'Supuesto', enunciado)
        self._orig = (semantica, precond)   # tal como se escribieron, para serializar

    def __repr__(self):
        """Método de representación"""
        return f"Supuesto(enunciado={self.e!r}, semantica={self.s!r}, precond={self.p!r})"
class Cuestion:
    def __init__(self, enunciado, semantica, precond=True, exp=""):
        self.e = enunciado
        self.s = _eval_campo(semantica, 'semantica', 'Cuestion', enunciado)
        self.p = _eval_campo(precond, 'precond', 'Cuestion', enunciado)
        self.x = exp
        self._orig = (semantica, precond)   # tal como se escribieron, para serializar

    def __repr__(self):
        """Método de representación"""
        return (f"Cuestion(enunciado={self.e!r}, semantica={self.s!r}, "
                f"precond={self.p!r}, exp={self.x!r})")
def _normaliza_slot(x):
    """Envuelve los escalares en una sublista; deja las listas tal cual."""
    return x if isinstance(x, list) else [x]

def _tipo_componente(e):
    if isinstance(e, str):      return 'str'
    if isinstance(e, Supuesto): return 'Supuesto'
    if isinstance(e, Cuestion): return 'Cuestion'
    raise ValueError(
        f"Componente de tipo no soportado: {type(e).__name__} ({e!r}). "
        "Cada componente debe ser str, Supuesto o Cuestion.")

def _clasifica_slot(slot):
    """'cuestiones' si la sublista (ya normalizada y homogénea) es de Cuestion;
    'enunciado' en otro caso (cadenas o Supuesto)."""
    return 'cuestiones' if isinstance(slot[0], Cuestion) else 'enunciado'

def _une_enunciado(acc, pieza):
    """Concatena dos fragmentos de enunciado (de slots distintos) separándolos
    con un espacio, salvo que ya haya separación —uno termina o el otro empieza
    por espacio— o alguno esté vacío. Evita textos pegados sin romper el
    contenido que ya incluye sus propios espacios."""
    if acc and pieza and not acc[-1].isspace() and not pieza[0].isspace():
        return acc + ' ' + pieza
    return acc + pieza

def validar_componentes(componentes):
    """Comprueba la invariante de homogeneidad (I1).

    Tras normalizar, cada slot debe contener un único tipo entre
    {str, Supuesto, Cuestion}. Lanza ValueError indicando el slot infractor.
    """
    for i, x in enumerate(componentes):
        slot = _normaliza_slot(x)
        if not slot:
            raise ValueError(f"El slot {i} está vacío.")
        tipos = {_tipo_componente(e) for e in slot}
        if len(tipos) > 1:
            raise ValueError(
                f"El slot {i} mezcla tipos {sorted(tipos)}; cada sublista debe "
                "contener un único tipo (solo cadenas, solo Supuesto o solo Cuestion).")

def segmentar(componentes):
    """Divide la lista de componentes en partes según las invariantes I1 e I2.

    Devuelve una lista de tuplas (slots_enunciado, [slots_cuestiones]).
    Una transición cuestiones->enunciado abre una parte nueva. Un ejercicio
    de una sola parte produce una lista de longitud 1.
    """
    validar_componentes(componentes)
    L = [_normaliza_slot(x) for x in componentes]
    partes, enun, cues, vistas = [], [], [], False
    for slot in L:
        if _clasifica_slot(slot) == 'cuestiones':
            cues.append(slot)
            vistas = True
        else:
            if vistas:                       # I2: cierra parte y abre una nueva
                partes.append((enun, cues))
                enun, cues, vistas = [], [], False
            enun.append(slot)
    partes.append((enun, cues))
    return partes

def _plan_partes(L):
    """Índice de parte (0, 1, 2, …) de cada slot ya normalizado, según la
    regla I2. La transición cuestiones->enunciado incrementa el índice."""
    plan, parte, vistas = [], 0, False
    for slot in L:
        es_cues = _clasifica_slot(slot) == 'cuestiones'
        if not es_cues and vistas:
            parte += 1
            vistas = False
        if es_cues:
            vistas = True
        plan.append(parte)
    return plan
class ProblemaTipo:
    def __init__(self, supuestos_y_cuestiones, setup=None, export=None, seed=None, nombre=None,
                 lectura=None):
        self.e = supuestos_y_cuestiones
        if isinstance(setup, str):
            if setup.strip():
                self._setup_str = setup      # tal cual, para guardar el problema en JSON
                setup = _setup_desde_str(setup)
            else:
                setup = None
        self.setup  = setup
        self.export = export if export is not None else {}
        self.seed   = seed
        self.lectura = lectura if lectura is not None else {}
        if nombre is not None:
            self._nombre = nombre

    def _variantes(self, _skip_seed=False, verbose=True):
        if not _skip_seed and self.setup is not None:
            _siembra(self.seed)
        L    = [_normaliza_slot(x) for x in self.e]
        plan = _plan_partes(L)
        npar = (plan[-1] + 1) if plan else 1
        c    = 0
        for variante in Marcador([len(x) for x in L]):
            ns         = self.setup() if self.setup else {}
            hipotesis  = []
            enunciados = ['' for _ in range(npar)]
            cuestiones = [[] for _ in range(npar)]
            descartada = False
            for n in range(len(L)):
                parte      = plan[n]
                componente = L[n][variante[n]]
                if isinstance(componente, str):
                    enunciados[parte] = _une_enunciado(enunciados[parte], _ns_interp(componente, ns))
                
                elif isinstance(componente, Supuesto):
                    precond = _ns_eval(componente.p, ns)
                    if test(precond, hipotesis):
                        enunciados[parte] = _une_enunciado(
                            enunciados[parte], _ns_interp(_ns_eval(componente.e, ns), ns))
                        hipotesis = hipotesis + [_ns_eval(componente.s, ns)]
                    else:
                        if verbose:
                            print('\n Supuesto: '   + str(componente.e) \
                                + ' rechazado por ' + _fuente_precond(componente) + '\n')
                        descartada = True
                        break
                
                elif isinstance(componente, Cuestion):
                    precond   = _ns_eval(componente.p, ns)
                    semantica = _ns_eval(componente.s, ns)
                    texto     = _ns_interp(_ns_eval(componente.e, ns), ns)
                    exp       = _ns_interp(_ns_eval(componente.x, ns), ns)
                    if test(precond, hipotesis):
                        cuestiones[parte].append(
                            (texto, (True if test(semantica, hipotesis) else False), 1, exp))
                    else:
                        if verbose:
                            print('\n Cuestion: '   + str(componente.e) \
                                + ' rechazada por ' + _fuente_precond(componente) + '\n')
                        descartada = True
                        break
            if not descartada:
                c += 1
                yield (str(c), list(zip(enunciados, cuestiones)))
    def _variantes_profe(self, verbose=True):
        if self.setup is not None:
            _siembra(self.seed)
        L    = [_normaliza_slot(x) for x in CuestionesJuntas(self.e)]
        plan = _plan_partes(L)
        npar = (plan[-1] + 1) if plan else 1
        c    = 0
        for variante in Marcador([len(x) for x in L]):
            ns         = self.setup() if self.setup else {}
            hipotesis  = []
            enunciados = ['' for _ in range(npar)]
            cuestiones = [[] for _ in range(npar)]
            descartada = False
            for n in range(len(L)):
                parte      = plan[n]
                componente = L[n][variante[n]]
                if isinstance(componente, str):
                    enunciados[parte] = _une_enunciado(enunciados[parte], _ns_interp(componente, ns))
                elif isinstance(componente, Supuesto):
                    precond = _ns_eval(componente.p, ns)
                    if test(precond, hipotesis):
                        enunciados[parte] = _une_enunciado(
                            enunciados[parte], _ns_interp(_ns_eval(componente.e, ns), ns))
                        hipotesis = hipotesis + [_ns_eval(componente.s, ns)]
                    else:
                        if verbose:
                            print('\n Supuesto: '   + str(componente.e) \
                                + ' rechazado por ' + _fuente_precond(componente) + '\n')
                        descartada = True
                        break
                elif isinstance(componente, Cuestion):
                    precond = _ns_eval(componente.p, ns)
                    texto   = _ns_interp(_ns_eval(componente.e, ns), ns)
                    if test(precond, hipotesis):
                        semantica = _ns_eval(componente.s, ns)
                        exp = _ns_interp(_ns_eval(componente.x, ns), ns)
                        cuestiones[parte].append(
                            (texto, (True if test(semantica, hipotesis) else False), 1, exp))
                    else:
                        cuestiones[parte].append(
                            (texto, 'rechazada por ' + _fuente_precond(componente), 0))
            if not descartada:
                c += 1
                yield (str(c), list(zip(enunciados, cuestiones)))
    def _variantes_lectura(self, seed=None, verbose=False):
        if self.setup is not None:
            _siembra(self.seed if seed is None else seed)
        L        = [_normaliza_slot(x) for x in self.e]
        plan     = _plan_partes(L)
        npar     = (plan[-1] + 1) if plan else 1
        es_hueco = [_clasifica_slot(x) == 'cuestiones' for x in L]
        c        = 0
        for variante in Marcador([1 if h else len(x) for x, h in zip(L, es_hueco)]):
            ns         = self.setup() if self.setup else {}
            hipotesis  = []
            enunciados = ['' for _ in range(npar)]
            huecos     = [[] for _ in range(npar)]
            mundo      = tuple(i for i, h in zip(variante, es_hueco) if not h)
            descarte   = None
            for n in range(len(L)):
                parte = plan[n]
                if es_hueco[n]:
                    hueco = []
                    for componente in L[n]:
                        precond = _ns_eval(componente.p, ns)
                        texto   = _ns_interp(_ns_eval(componente.e, ns), ns)
                        if test(precond, hipotesis):
                            semantica = _ns_eval(componente.s, ns)
                            exp = _ns_interp(_ns_eval(componente.x, ns), ns)
                            hueco.append(Alternativa(texto, bool(test(semantica, hipotesis)), exp, None))
                        else:
                            hueco.append(Alternativa(texto, None, '',
                                                     'rechazada por ' + _fuente_precond(componente)))
                    huecos[parte].append(hueco)
                    continue
                componente = L[n][variante[n]]
                if isinstance(componente, str):
                    enunciados[parte] = _une_enunciado(enunciados[parte], _ns_interp(componente, ns))
                else:                                   # Supuesto
                    precond = _ns_eval(componente.p, ns)
                    texto   = _ns_interp(_ns_eval(componente.e, ns), ns)
                    if test(precond, hipotesis):
                        enunciados[parte] = _une_enunciado(enunciados[parte], texto)
                        hipotesis = hipotesis + [_ns_eval(componente.s, ns)]
                    else:
                        descarte = ('Supuesto ' + repr(texto) + ' rechazado por '
                                    + _fuente_precond(componente))
                        if verbose:
                            print('\n ' + descarte + '\n')
                        break
            if descarte is None:
                c += 1
                yield Lectura(str(c), mundo, ns,
                              [ParteLectura(e, h) for e, h in zip(enunciados, huecos)], None)
            else:
                yield Lectura('', mundo, ns, None, descarte)
    
    def por_partes_lectura(self, seed=None, verbose=False, descartes=False):
        """Vista de lectura: como por_partes_profe(), pero con las cuestiones
        agrupadas por hueco y con el espacio de nombres del setup de cada
        variante. Devuelve registros Lectura(etiqueta, mundo, ns, partes,
        descarte); cada parte es ParteLectura(enunciado, huecos) y cada
        alternativa Alternativa(texto, valor, exp, motivo), con valor None (y
        motivo) si la precondición la excluye en ese mundo.
    
        seed      : semilla del setup (por defecto, la del problema).
        verbose   : imprime los Supuesto rechazados por precondición.
        descartes : si True, emite también los mundos descartados (partes=None
                    y descarte con el motivo)."""
        for r in self._variantes_lectura(seed=seed, verbose=verbose):
            if descartes or r.descarte is None:
                yield r
    
    def por_partes(self, instances=1, base_seed=None, verbose=False):
        """Itera las variantes válidas como (etiqueta, [(enunciado, cuestiones), …]).
    
        Es la vía recomendada para ejercicios multiparte. En un ejercicio de una
        sola parte cada elemento es una lista de longitud 1.
    
        instances : número de instancias con semillas distintas. Útil cuando el
                    setup usa np.random y una sola instancia produce pocas variantes.
                    La instancia i se evalúa con np.random.seed(base_seed + i * 997).
                    Con instances > 1 en un problema sin setup se emite UserWarning
                    (todas las instancias serían idénticas).
        base_seed : semilla base. Con instances=1, si no se pasa explícitamente
                    se usa self.seed (del JSON). Con instances>1, si no se pasa
                    se usa self.seed o 42 como fallback. Se siembran numpy.random
                    y el módulo random de Python.
        verbose   : si True, imprime las cuestiones/supuestos rechazados por
                    precondición. Por defecto False (silencioso en batch).
        """
        effective_base = base_seed if base_seed is not None else self.seed
        if instances > 1:
            if self.setup is None:
                import warnings
                warnings.warn(
                    "instances > 1 en un ProblemaTipo sin setup: "
                    "se generarán variantes duplicadas.",
                    UserWarning, stacklevel=2)
            actual_base = effective_base if effective_base is not None else 42
            offset = 0
            for inst in range(instances):
                _siembra(actual_base + inst * 997)
                count = 0
                for etiqueta, partes in self._variantes(_skip_seed=True, verbose=verbose):
                    count += 1
                    yield (str(offset + int(etiqueta)), partes)
                offset += count
        elif base_seed is not None and self.setup is not None:
            _siembra(base_seed)
            yield from self._variantes(_skip_seed=True, verbose=verbose)
        else:
            yield from self._variantes(verbose=verbose)
    
    def por_partes_profe(self, verbose=True):
        """Vista de revisión del profesor, en el mismo formato por partes que
        por_partes(): muestra TODAS las cuestiones de cada sublista (no una por
        variante) y marca las que no superan su precondición como rechazadas en vez
        de descartar la variante. No es la salida que ve el alumno ni la exportada.
    
        verbose : si True (por defecto), imprime los Supuesto rechazados por
                  precondición (las variantes descartadas)."""
        return self._variantes_profe(verbose=verbose)
    
    def __iter__(self):
        self._gen = self._variantes()
        return self
    
    def __next__(self):
        etiqueta, partes = next(self._gen)   # propaga StopIteration al agotarse
        if len(partes) > 1:
            raise ValueError(
                "Este ProblemaTipo tiene varias partes; itéralo con .por_partes(), "
                "que devuelve (etiqueta, [(enunciado, cuestiones), …]).")
        (enunciado, cuestiones), = partes
        return (etiqueta, enunciado, cuestiones)
class ProblemaTipoProfe:
    def __init__(self, supuestos_y_cuestiones, setup=None):
        import warnings
        warnings.warn(
            "ProblemaTipoProfe está deprecada: usa ProblemaTipo(...).por_partes_profe().",
            DeprecationWarning, stacklevel=2)
        self.e = CuestionesJuntas(supuestos_y_cuestiones)
        self.setup = setup

    def __iter__(self):
        self.l    = [x if isinstance(x,list) else [x] for x in self.e]
        self.long = len(self.l)
        self.i    = iter(Marcador([len(x) for x in self.l]))
        self.c    = 0
        return self
    def __next__(self):
        self.c += 1
        while True:
            try:
                variante = next(self.i)
            except StopIteration:
                raise StopIteration
    
            ns = self.setup() if self.setup else {}
            enunciado     = ""
            hipotesis     = []
            cuestiones    = []
    
            for n in range(self.long+1):
                if n == self.long:
                    return (str(self.c), enunciado, cuestiones)
    
                componente = self.l[n][variante[n]]
                if isinstance(componente, str):
                    enunciado = _une_enunciado(enunciado, _ns_interp(componente, ns))
                
                elif isinstance(componente, Supuesto):
                    precond = _ns_eval(componente.p, ns)
                    if test(precond, hipotesis):
                        enunciado = _une_enunciado(
                            enunciado, _ns_interp(_ns_eval(componente.e, ns), ns))
                        hipotesis = hipotesis + [_ns_eval(componente.s, ns)]
                    else:
                        print('\n Supuesto: '   + str(componente.e) \
                            + ' rechazado por ' + _fuente_precond(componente) + '\n')
                        break
                
                elif isinstance(componente, Cuestion):
                    precond   = _ns_eval(componente.p, ns)
                    semantica = _ns_eval(componente.s, ns)
                    texto     = _ns_interp(_ns_eval(componente.e, ns), ns)
                    if test(precond, hipotesis):
                        exp = _ns_interp(_ns_eval(componente.x, ns), ns)
                        cuestiones = cuestiones + \
                            [(texto, (True if test(semantica, hipotesis) else False), 1, exp)]
                    else:
                        cuestiones = cuestiones + \
                            [(texto, 'rechazada por ' + _fuente_precond(componente), 0)]
                
from random import sample
class ProblemaVF():
    def __init__(self, enunciado, cuestiones, NumPreguntas):
        self.e = enunciado
        self.c = cuestiones
        self.NumPreguntas = NumPreguntas

    def __iter__(self):
        self.contador = 0
        return self

    def __next__(self):
        cuestiones = sample(self.c, self.NumPreguntas)
        self.contador += 1
        return (str(self.contador), self.e, cuestiones)
    
class SubPregunta:
    """DEPRECADO. Contenedor (intro, lista de Cuestion) del antiguo
    ProblemaMultiParte. Se conserva solo para compatibilidad; usa ProblemaTipo
    con su lista plana de componentes."""
    def __init__(self, intro, cuestiones):
        self.intro = intro
        self.cuestiones = cuestiones if isinstance(cuestiones, list) else [cuestiones]


class ProblemaMultiParte:
    """DEPRECADO. Devuelve un ProblemaTipo equivalente.

    La estructura multiparte ya no es un tipo propio: se representa como un
    ProblemaTipo cuya lista plana intercala el enunciado común y, por cada
    SubPregunta, su intro seguido de su sublista de Cuestion. Las partes se
    infieren con la regla I2 y se recorren con por_partes().
    """
    def __new__(cls, componentes, subpreguntas, setup=None):
        import warnings
        warnings.warn(
            "ProblemaMultiParte y SubPregunta están deprecados: usa ProblemaTipo "
            "con su lista plana de componentes (las partes se infieren) y recórrelo "
            "con .por_partes().",
            DeprecationWarning, stacklevel=2)
        flat = list(componentes)
        for sp in subpreguntas:
            flat.append(sp.intro)
            flat.append(list(sp.cuestiones))
        return ProblemaTipo(flat, setup=setup)
