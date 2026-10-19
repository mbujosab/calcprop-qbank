#!/usr/bin/env python3
"""Escribe una pregunta en Python (listas de Supuesto/Cuestion) y guárdala como JSON.

Desde la carpeta del proyecto (la que contiene preguntas/ y el Makefile):

    python nueva_pregunta.py             # imprime las primeras variantes (vista profe) y el lint
    python nueva_pregunta.py --guardar   # además escribe preguntas/<NOMBRE>.json

Copia este fichero con otro nombre en esta misma carpeta (o edítalo), cambia
NOMBRE, SETUP y PREGUNTA, ejecútalo hasta que lo que imprime y el lint te
convenzan, y guarda. A partir de ahí la pregunta vive en preguntas/<NOMBRE>.json,
que es lo que leen make lint, make amc y make moodle; este .py puedes borrarlo o
conservarlo como borrador. La vista profe completa (todas las variantes, en PDF)
es la de `make amc`.

Recordatorio de la mecánica (la trampa habitual al empezar):
  * una LISTA de Cuestion sortea UNA de ellas por variante (son alternativas);
  * el alumno ve tantas opciones como elementos-Cuestion CONSECUTIVOS haya
    (sueltos o listas), más la opción por defecto si export.last_choice es True;
  * una LISTA de Supuesto sortea uno (mundos alternativos); un Supuesto suelto
    con enunciado "" es un axioma (añade su fórmula sin texto).
"""
import sys

import numpy as np
from qbank import Cuestion, ProblemaTipo, Supuesto, alguno, lint, save_problema, unoDe, v  # noqa: F401

NOMBRE = "L-00-SignoYCuadrado"     # nombre del fichero JSON (sin .json); sin ':'

# Código que se ejecuta antes de cada variante. Sus variables se interpolan con
# @{nombre} en los textos y están en ns['nombre'] para las lambdas. None si no
# hace falta. Usa np.random (no random) para que seed e instances funcionen.
SETUP = r"""
import numpy as np
x = int(np.random.choice([-9, -7, -5, -3, -2, 2, 3, 5, 7, 9]))
cuadrado = x ** 2
cuadrado_falso = -cuadrado if x < 0 else cuadrado + 2 * abs(x)
"""

PREGUNTA = ProblemaTipo(
    [
        "Sea $x = @{x}$ un número entero. Suponga que $x$ es ",
        [   # mundos alternativos: se sortea uno; su precond filtra los valores del setup
            Supuesto("positivo.", v('pos'), precond="lambda ns: ns['x'] > 0"),
            Supuesto("negativo.", v('neg'), precond="lambda ns: ns['x'] < 0"),
        ],
        " Entonces:",
        [   # hueco 1: en cada variante se muestra UNA de estas dos
            Cuestion("$x^3 > 0$", v('pos'), exp="El cubo conserva el signo de $x$."),
            Cuestion("$x^3 < 0$", v('neg'), exp="El cubo conserva el signo de $x$."),
        ],
        [   # hueco 2
            Cuestion("$|x| = x$",  v('pos'), exp=r"$|x| = x$ si $x \ge 0$ y $|x| = -x$ si $x < 0$."),
            Cuestion("$|x| = -x$", v('neg'), exp=r"$|x| = x$ si $x \ge 0$ y $|x| = -x$ si $x < 0$."),
        ],
        [   # hueco 3: una afirmación numérica verdadera y su «gemela» falsa
            Cuestion("$x^2 = @{cuadrado}$", True),
            Cuestion("$x^2 = @{cuadrado_falso}$", False,
                     exp="El cuadrado de $@{x}$ es $@{cuadrado}$: nunca es negativo y no depende del signo."),
        ],
    ],
    setup=SETUP,
    seed=0,                                                   # solo si SETUP usa np.random
    export={"last_choice": True, "cols": 2, "instances": 8},  # 3 huecos + opción por defecto = 4 opciones
    nombre=NOMBRE,
)


MAX_VARIANTES = 4      # cuántas variantes se imprimen (la vista completa es make amc)
MAX_SORTEOS = 50       # con setup, cuántos sorteos se prueban para reunirlas


def primeras_variantes(p, n):
    """Las n primeras variantes de la vista profe. Con setup aleatorio recorre
    varios sorteos: un Supuesto cuya precond rechaza los números de un sorteo
    hace desaparecer la variante entera, y un solo sorteo puede no dar ninguna."""
    out = []
    if p.setup is None:
        for variante in p.por_partes_profe(verbose=False):
            out.append(variante)
            if len(out) >= n:
                break
        return out
    seed, p.seed = p.seed, None          # que mande la semilla de cada sorteo
    try:
        for sorteo in range(MAX_SORTEOS):
            np.random.seed(sorteo)
            for variante in p.por_partes_profe(verbose=False):
                out.append(variante)
                if len(out) >= n:
                    return out
    finally:
        p.seed = seed
    return out


def main(argv):
    print(f"── {NOMBRE}: primeras {MAX_VARIANTES} variantes de la vista profe "
          "(✓ correcta, ✗ incorrecta, · Cuestion rechazada por su precond) ──")
    variantes = primeras_variantes(PREGUNTA, MAX_VARIANTES)
    if not variantes:
        print(f"\n   ninguna variante en {MAX_SORTEOS} sorteos: todos los Supuesto quedan "
              "rechazados por su precond (revisa el setup y las precondiciones)")
    for etiqueta, partes in variantes:
        for enunciado, cuestiones in partes:
            print(f"\n[{etiqueta}] {enunciado}")
            for texto, correcto, activa, *resto in cuestiones:
                marca = ('✓' if correcto else '✗') if activa else '·'
                print(f"   {marca} {texto}")
    if len(variantes) >= MAX_VARIANTES:
        print("\n   … (el resto, con las explicaciones y las exclusiones, en make amc)")

    print("\n── lint ──")
    avisos = lint(PREGUNTA)
    for a in avisos:
        print("  ", a)
    if not avisos:
        print("   sin avisos")

    if '--guardar' in argv:
        ruta = f"preguntas/{NOMBRE}.json"
        save_problema(PREGUNTA, ruta)
        print(f"\nGuardada en {ruta}")
    else:
        print(f"\n(añade --guardar para escribir preguntas/{NOMBRE}.json)")


if __name__ == '__main__':
    main(sys.argv[1:])
