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

class _NsTemplate(Template):
    delimiter = '@'

def _ns_eval(val, ns):
    return val(ns) if callable(val) else val

def _ns_interp(s, ns):
    return _NsTemplate(s).safe_substitute(ns) if ns else s

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
        self.s = semantica
        self.p = precond

    def __repr__(self):
        """Método de representación"""
        return f"Supuesto(enunciado={self.e!r}, semantica={self.s!r}, precond={self.p!r})"
class Cuestion:
    def __init__(self, enunciado, semantica, precond=True, exp=""):
        self.e = enunciado
        self.s = semantica
        self.p = precond
        self.x = exp

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
    def __init__(self, supuestos_y_cuestiones, setup=None):
        self.e = supuestos_y_cuestiones
        self.setup = setup

    def _variantes(self):
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
                    enunciados[parte] += _ns_interp(componente, ns)
                
                elif isinstance(componente, Supuesto):
                    precond = _ns_eval(componente.p, ns)
                    if test(precond, hipotesis):
                        enunciados[parte] += _ns_interp(_ns_eval(componente.e, ns), ns)
                        hipotesis = hipotesis + [_ns_eval(componente.s, ns)]
                    else:
                        print('\n Supuesto: '   + str(componente.e) \
                            + ' rechazado por ' + _fuente_precond(componente) + '\n')
                        descartada = True
                        break
                
                elif isinstance(componente, Cuestion):
                    precond   = _ns_eval(componente.p, ns)
                    semantica = _ns_eval(componente.s, ns)
                    texto     = _ns_interp(_ns_eval(componente.e, ns), ns)
                    if test(precond, hipotesis):
                        cuestiones[parte].append(
                            (texto, (True if test(semantica, hipotesis) else False), 1, componente.x))
                    else:
                        print('\n Cuestion: '   + str(componente.e) \
                            + ' rechazada por ' + _fuente_precond(componente) + '\n')
                        descartada = True
                        break
            if not descartada:
                c += 1
                yield (str(c), list(zip(enunciados, cuestiones)))
    def por_partes(self):
        """Itera las variantes válidas como (etiqueta, [(enunciado, cuestiones), …]).
    
        Es la vía recomendada para ejercicios multiparte. En un ejercicio de una
        sola parte cada elemento es una lista de longitud 1.
        """
        return self._variantes()
    
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
                    enunciado = enunciado + _ns_interp(componente, ns)
                
                elif isinstance(componente, Supuesto):
                    precond = _ns_eval(componente.p, ns)
                    if test(precond, hipotesis):
                        enunciado = enunciado + _ns_interp(_ns_eval(componente.e, ns), ns)
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
                        cuestiones = cuestiones + \
                            [(texto, (True if test(semantica, hipotesis) else False), 1, componente.x)]
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
    def __init__(self, intro, cuestiones):
        self.intro = intro
        self.cuestiones = cuestiones if isinstance(cuestiones, list) else [cuestiones]


class ProblemaMultiParte:
    def __init__(self, componentes, subpreguntas, setup=None):
        """
        componentes:  list de str / Supuesto / list de Supuesto (enunciado común)
        subpreguntas: list de SubPregunta
        setup:        callable opcional
        """
        self.componentes  = componentes
        self.subpreguntas = subpreguntas
        self.setup        = setup

    def __iter__(self):
        self.l    = [x if isinstance(x, list) else [x] for x in self.componentes]
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

            ns        = self.setup() if self.setup else {}
            enunciado = ""
            hipotesis = []

            for n in range(self.long):
                componente = self.l[n][variante[n]]
                if isinstance(componente, str):
                    enunciado += _ns_interp(componente, ns)
                elif isinstance(componente, Supuesto):
                    precond = _ns_eval(componente.p, ns)
                    if test(precond, hipotesis):
                        enunciado += _ns_interp(_ns_eval(componente.e, ns), ns)
                        hipotesis  = hipotesis + [_ns_eval(componente.s, ns)]
                    else:
                        print('\n Supuesto: '   + str(componente.e)
                              + ' rechazado por ' + _fuente_precond(componente) + '\n')
                        break
            else:
                subpregs = []
                for sp in self.subpreguntas:
                    intro_text = _ns_interp(sp.intro, ns)
                    cuestiones = []
                    for c in sp.cuestiones:
                        precond   = _ns_eval(c.p, ns)
                        semantica = _ns_eval(c.s, ns)
                        texto     = _ns_interp(_ns_eval(c.e, ns), ns)
                        if test(precond, hipotesis):
                            correcto = True if test(semantica, hipotesis) else False
                            cuestiones.append((texto, correcto, 1, c.x))
                    subpregs.append((intro_text, cuestiones))
                return (str(self.c), enunciado, subpregs)
