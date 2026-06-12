from qbank import *

enunciado = "Indique qué afirmaciones son verdaderas:"
bancoVF = [
     ("Todo alumno que va a clase aprueba",   False),
     ("Todo alumno que suspende va a clase",  False),
     ("Todo alumno que sabe aprueba",         True ),
     ("Si aprueban todos eres buen profesor", False),
     ("Si suspenden todos eres mal profesor", False),
     ("Si suspenden todos es frustrante",     True ),]
GenVar = iter( ProblemaVF (enunciado, bancoVF, 3) ) # Tres preguntas por variante

nombre     = "EjemploVF"
directorio = "../ejemplos/"
with open(directorio + nombre + ".tex","w") as f:
    for i in range(4):                            # Cuatro variantes
        var = (next(GenVar))
        f.write(AMC_VF(nombre,var[0],var[1],var[2]))
