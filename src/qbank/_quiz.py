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
        return 'Cuestión( Enunciado: ' + self.e + '; Semántica: ' + self.s + '; Precondición: ' + self.p + ')'
class Cuestion:
    def __init__(self, enunciado, semantica, precond=True, exp=""):
        self.e = enunciado
        self.s = semantica
        self.p = precond
        self.x = exp

    def __repr__(self):
        """Método de representación"""
        return 'Cuestión( Enunciado: ' + self.e + '; Semántica: ' + self.s + '; Precondición: ' + self.p + ')'
class ProblemaTipo:
    def __init__(self, supuestos_y_cuestiones):
        self.e = supuestos_y_cuestiones

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
    
            enunciado    = ""
            hipotesis    = []
            cuestiones   = []
    
            for n in range(self.long+1):
                if n == self.long:
                    return (str(self.c), enunciado, cuestiones)
    
                componente = self.l[n][variante[n]]
                if isinstance(componente, str):
                    enunciado = enunciado + componente
                
                elif isinstance(componente, Supuesto):
                    if test(componente.p, hipotesis):
                        enunciado = enunciado +  componente.e
                        hipotesis = hipotesis + [componente.s]
                    else:
                        print('\n Supuesto: '   + str(componente.e) \
                            + ' rechazado por ' + str(componente.p) + '\n')
                        break
                
                elif isinstance(componente, Cuestion):
                    if test(componente.p, hipotesis):
                        cuestiones = cuestiones + \
                            [(componente.e,(True if test(componente.s, hipotesis) else False),1,componente.x)]
                    else:
                        cuestiones = cuestiones + \
                            [(componente.e,'rechazada por ' + str(componente.p),0,componente.x)]
                        print('\n Cuestion: '   + str(componente.e) \
                            + ' rechazada por ' + str(componente.p) + '\n')
                        break
class ProblemaTipoProfe:
    def __init__(self, supuestos_y_cuestiones):
        self.e = CuestionesJuntas(supuestos_y_cuestiones)

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
    
            enunciado     = ""
            hipotesis     = []
            cuestiones    = []
    
            for n in range(self.long+1):
                if n == self.long:
                    return (str(self.c), enunciado, cuestiones)
    
                componente = self.l[n][variante[n]]
                if isinstance(componente, str):
                    enunciado = enunciado + componente
                
                elif isinstance(componente, Supuesto):
                    if test(componente.p, hipotesis):
                        enunciado = enunciado +  componente.e
                        hipotesis = hipotesis + [componente.s]
                    else:
                        print('\n Supuesto: '   + str(componente.e) \
                            + ' rechazado por ' + str(componente.p) + '\n')
                        break
                
                elif isinstance(componente, Cuestion):
                    if test(componente.p, hipotesis):
                        cuestiones = cuestiones + \
                            [(componente.e,(True if test(componente.s, hipotesis) else False),1,componente.x)]
                    else:
                        cuestiones = cuestiones + \
                            [(componente.e,'rechazada por ' + str(componente.p),0)]
                
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
