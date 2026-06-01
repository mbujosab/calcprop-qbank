# Copyright (C) 2020-2026  Marcos Bujosa
# GNU General Public License v3 or later — see <https://www.gnu.org/licenses/>

from qbank import *

enunciado = "Indique qué afirmaciones son verdaderas:"
banco = [
  ("Todo alumno que va a clase aprueba",   False),
  ("Todo alumno que suspende va a clase",  False),
  ("Todo alumno que sabe aprueba",         True),
  ("Si aprueban todos eres buen profesor", False),
  ("Si suspenden todos eres mal profesor", False),
  ("Si suspenden todos es frustrante",     True),
]

b = [(codchar(p[0]), p[1]) for p in banco]
GenVar = iter(ProblemaVF(codchar(enunciado), b, 3))

nombre = "EjemploVFMoodle"
directorio = "../ejemplos/"
QuizVFMoodleLastCh(nombre, directorio, GenVar, 4)
