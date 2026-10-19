[![](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mbujosab/calcprop-qbank/main?urlpath=lab/tree/Tutorial.ipynb)

Genera variantes de preguntas de opción múltiple cuyas respuestas
correctas se determinan automáticamente mediante cálculo proposicional.
Combina supuestos e ítems de respuesta por combinatoria, calcula la
veracidad o falsedad de cada ítem según las hipótesis activas y exporta
el resultado a LaTeX (AMC) o Moodle (XML vía LaTeX).

Construido sobre [`calcprop`](https://github.com/mbujosab/calcprop).

# Instalación

``` bash
pip install calcprop calcprop-qbank
```

Con soporte para el editor visual en Jupyter:

``` bash
pip install "calcprop-qbank[jupyter]"
```

La versión publicada en PyPI (0.5.0) todavía no trae `qbank-init` ni
`lint`, que necesitan la 0.6. Mientras no se publique, instala desde el
repositorio:

``` bash
pip install "calcprop-qbank[jupyter] @ git+https://github.com/mbujosab/calcprop-qbank"
```

El paquete solo instala el código. El tutorial (`Tutorial.ipynb`), la
guía de diseño (`GuiaDiseno.org`), el manual y los ejemplos de
`ejemplosManual/` están en el
[repositorio](https://github.com/mbujosab/calcprop-qbank): clónalo con
`git clone https://github.com/mbujosab/calcprop-qbank` o abre el
tutorial sin instalar nada con la insignia de MyBinder de arriba.

# Crear un banco de preguntas

La forma recomendada de empezar es la plantilla de proyecto que se
distribuye con el paquete (`qbank-init` necesita la versión 0.6, que aún
no está en PyPI: instala desde el repositorio como se indica arriba):

``` bash
qbank-init mi-banco
cd mi-banco
make lint          # comprueba las preguntas de ejemplo (sin LaTeX)
make amc           # PDF de revisión (vista profe) en build/amc/
```

El proyecto contiene cinco preguntas de ejemplo en `preguntas/`, los
scripts que las exportan a AMC y Moodle, un `Makefile` (`lint`, `tabla`,
`amc`, `amc-student`, `moodle`, `clean`, filtro `LECCION=N`) y
`nueva_pregunta.py`, un guion para escribir una pregunta en Python y
guardarla como JSON. Su `README.org` explica el flujo.

`make` usa el intérprete `python3` del sistema. Si instalaste qbank en
un entorno virtual, actívalo antes (`source .venv/bin/activate`) o
indícalo con `PYTHON`: `make lint PYTHON=/ruta/al/.venv/bin/python`. Con
un qbank antiguo en el intérprete, `make` falla con mensajes engañosos.

# Uso rápido

``` python
from qbank import *

p = ProblemaTipo(
    [
        "Sea $f$ una función ",
        [   # mundos alternativos: en cada variante se sortea uno
            Supuesto("estrictamente creciente", v('crec')),
            Supuesto("estrictamente decreciente", v('decr')),
        ],
        " y sean $a < b$. Entonces:",
        [   # hueco 1: el alumno ve una de estas dos
            Cuestion("$f(a) < f(b)$", v('crec')),
            Cuestion("$f(a) > f(b)$", v('decr')),
        ],
        Cuestion("$f(a) = f(b)$", False),              # hueco 2: siempre
        [   # hueco 3
            Cuestion("$f(b) - f(a) > 0$", v('crec')),
            Cuestion("$f(b) - f(a) < 0$", v('decr')),
        ],
    ],
    export={"last_choice": True},   # + «Ninguna de las anteriores»
)

for etiqueta, partes in p.por_partes():
    for enunciado, cuestiones in partes:
        print(f"Variante {etiqueta}: {enunciado}")
        for texto, correcto, activa, exp in cuestiones:
            print(f"  {'✓' if correcto else '✗'} {texto}")
```

Ocho variantes (pocas para un banco real: `lint` lo avisa), cada una con
tres opciones más la opción por defecto («Ninguna de las anteriores»,
correcta solo si las otras tres son falsas). Una **lista** de `Cuestion`
sortea una por variante; el alumno ve tantas opciones como
elementos-Cuestion consecutivos haya (`GuiaDiseno.org` lo explica).

# Características

## Generación combinatoria de variantes

`ProblemaTipo` toma una lista de supuestos y cuestiones (cada uno con su
semántica proposicional) y genera todas las combinaciones posibles. Para
cada variante calcula automáticamente qué ítems son verdaderos y cuáles
falsos. Las variantes con hipótesis incoherentes o precondiciones
insatisfechas se descartan.

El método `por_partes_profe()` muestra todas las cuestiones de cada
hueco (marcando las rechazadas por su precondición en vez de descartar
la variante), facilitando la revisión del banco.

## Preguntas multi-parte

La misma lista plana de componentes admite varias partes: cada vez que
tras un bloque de cuestiones aparece texto o un `Supuesto` se abre una
parte nueva. Es útil para preguntas AMC con múltiples apartados o para
el formato cloze de Moodle. El método `por_partes()` devuelve, por
variante, un par `(enunciado, cuestiones)` por parte:

``` python
from qbank import *

p = ProblemaTipo([
    Supuesto("", unoDe(v("A"), v("B"))),    # axioma: exactamente una es verdadera
    "Exactamente una de las proposiciones $A$ y $B$ es verdadera, y la verdadera es ",
    [Supuesto("$A$.", v("A")),
     Supuesto("$B$.", v("B"))],
    " Sobre $A$:",                           # parte 1: tres huecos
    [Cuestion("$A$ es verdadera.", v("A")), Cuestion("$A$ es falsa.", -v("A"))],
    [Cuestion("$\\lnot A$ es verdadera.", -v("A")), Cuestion("$\\lnot A$ es falsa.", v("A"))],
    [Cuestion("$A \\to B$ es verdadera.", v("A") >> v("B")),
     Cuestion("$B \\to A$ es verdadera.", v("B") >> v("A"))],
    "Sobre $B$:",                            # texto tras las cuestiones: parte 2
    [Cuestion("$B$ es verdadera.", v("B")), Cuestion("$B$ es falsa.", -v("B"))],
    [Cuestion("$\\lnot B$ es verdadera.", -v("B")), Cuestion("$\\lnot B$ es falsa.", v("B"))],
    [Cuestion("$A \\land \\lnot B$ es verdadera.", v("A") & -v("B")),
     Cuestion("$\\lnot A \\land B$ es verdadera.", -v("A") & v("B"))],
], export={"last_choice": True})   # + «Ninguna de las anteriores» en cada parte

for etiqueta, partes in p.por_partes():
    for enunciado, cuestiones in partes:
        ...
```

Cada parte tiene tres huecos (una lista sortea una `Cuestion`, así que
una sola lista daría una única opción) más la opción por defecto. Las
negaciones `-v("A")` se deducen gracias al axioma `unoDe`; sin él,
`lint` da ERROR `negacion`. Este ejemplo pasa `lint` sin avisos (128
variantes).

(`ProblemaMultiParte` y `SubPregunta` siguen existiendo por
compatibilidad, pero están deprecados y devuelven un `ProblemaTipo`
equivalente.)

## Preguntas paramétricas con `setup`

El parámetro `setup` (código Python, como cadena) se ejecuta antes de
cada variante; sus variables se interpolan en los textos con
`@{variable}` y están disponibles en `ns` para semánticas y
precondiciones escritas como `lambda`:

``` python
p = ProblemaTipo(
    ["Sean $a = @{a}$ y $b = @{b}$. Entonces:",
     [Cuestion("$a + b = @{suma}$", True),
      Cuestion("$a + b = @{suma_falsa}$", False)],
     [Cuestion("$a + b > 10$", "lambda ns: ns['a'] + ns['b'] > 10"),
      Cuestion("$a + b < 10$", "lambda ns: ns['a'] + ns['b'] < 10")],
     Cuestion("$a \\cdot b = @{producto}$", True)],
    setup="import numpy as np\n"
          "a, b = (int(x) for x in np.random.randint(1, 10, 2))\n"
          "suma, suma_falsa, producto = a + b, a + b + 1, a * b",
    seed=1, export={"last_choice": True, "instances": 15},
)
```

Con `seed` la pregunta es reproducible e `instances` fija cuántas
instancias (sorteos del `setup`) se generan (aquí 4 variantes × 15 = 60,
el mínimo que recomienda `lint` con `setup`). `seed` siembra
`numpy.random` y `random`; usa `np.random` en el `setup`, porque los
scripts de la vista profe solo siembran numpy.

## Persistencia en formato JSON

Guarda y carga problemas (`ProblemaTipo`, `ProblemaVF`) sin reescribir
el código Python:

``` python
from qbank import load_problema, save_problema

p = load_problema('mi_problema.json')
save_problema(p, 'copia.json')
```

Para bancos de múltiples problemas: `load_banco` / `save_banco`.

## Editor visual en Jupyter

`ProblemaTipoEditor` es un formulario interactivo (requiere
`ipywidgets`) que permite construir, previsualizar y guardar problemas
sin escribir código:

``` python
from qbank import ProblemaTipoEditor

editor = ProblemaTipoEditor()           # editor vacío
editor = ProblemaTipoEditor('p.json')  # cargar desde fichero

p = editor.to_problema()               # obtener el ProblemaTipo
```

Ver
[Manual.org](https://github.com/mbujosab/calcprop-qbank/blob/main/Manual.org)
si los widgets se muestran como texto en lugar del formulario.

## Exportación a AMC y Moodle

### Formato AMC (LaTeX)

Las funciones de exportación **no leen** el campo `export` del problema:
pásales `last_choice=`, `instances=` y `cols=` tú mismo. Los scripts de
un banco creado con `qbank-init` sí lo leen.

`AMCblock` y `AMC_multipart` son funciones de bajo nivel que devuelven
un bloque LaTeX listo para escribir al fichero. Una pregunta multi-parte
necesita `AMC_multipart` (un único `questionmult` con un bloque de
casillas por parte): un `AMCblock` por parte daría identificadores
duplicados y la segunda parte sin las hipótesis.

``` python
with open("preguntas.tex", "w") as f:
    for etiqueta, partes in p.por_partes():
        if len(partes) > 1:
            f.write(AMC_multipart("MiCuestionario", etiqueta, "", partes, last_choice=True))
        else:
            f.write(AMCblock("MiCuestionario", etiqueta, partes[0][0], partes[0][1],
                             last_choice=True))
```

Vista profe (todas las cuestiones de cada hueco, con marcas; usa
`AMC_multipart` cuando hace falta):

``` python
import os
os.makedirs("exportaciones", exist_ok=True)

n = QuizAMCProfe("MiCuestionario", "exportaciones", p, last_choice=True)
print(f"{n} bloque(s) escritos")
```

### Formato Moodle (XML vía LaTeX)

``` python
import os
os.makedirs("exportaciones", exist_ok=True)

# Vista alumno
n = QuizMoodle("MiCuestionario", "exportaciones/", p, last_choice=True)
print(f"{n} variante(s) escritas")

# Vista profe (fracciones de puntuación visibles)
QuizMoodleProfe("MiCuestionario", "exportaciones/", p, last_choice=True)

# Con paquete LaTeX adicional y texto de la opción por defecto personalizados
QuizMoodle("MiCuestionario", "exportaciones/", p,
           aux_latex=r"\usepackage{nacal-moodle}",
           last_choice_text="Las demás opciones son falsas")
```

`QuizMoodle` y `QuizMoodleProfe` devuelven un `int` con el número de
variantes escritas, útil para logging en scripts de build.

Para preguntas `ProblemaVF`: `QuizVFMoodle`.

## Exportación a código Python editable

`save_problema_py` genera un fichero `.py` con la definición del
problema como listas editables:

``` python
from qbank import save_problema_py

save_problema_py(p, 'mi_problema.py')
```

El fichero resultante puede abrirse con cualquier editor, modificarse y
ejecutarse directamente con Python.

## Comprobación automática de preguntas (`lint`)

`lint` revisa un problema (objeto, dict o ruta a JSON) sin modificar
nada ni compilar LaTeX y devuelve una lista de
`Aviso(nivel, codigo, mensaje, donde)` con nivel `ERROR`, `AVISO` o
`INFO`:

``` python
from qbank import lint, tabla_mundos

for a in lint("preguntas/L-01-FuncionMonotona.json"):
    print(a)
print(tabla_mundos("preguntas/L-01-FuncionMonotona.json"))   # Cuestion × mundo
```

Desde la línea de órdenes (código de salida 1 si hay algún `ERROR`):

``` bash
python -m qbank.lint preguntas/*.json [--instances N] [--seed S] [--tabla] [--quiet]
qbank-lint preguntas/*.json --quiet      # equivalente; omite INFO y ficheros OK
```

Comprueba, entre otras cosas, la garantía de mezcla (`1 <` correctas \<=
opciones-1= en toda variante, contando la opción por defecto de
`last_choice`), el número de variantes, negaciones `-v('X')` que nunca
podrían deducirse por falta de un `unoDe(...)`, interpolaciones `@{var}`
sin resolver, etiquetas huérfanas, la estructura del JSON y caracteres
que rompen la exportación a Moodle. La tabla de mundos muestra el valor
de cada `Cuestion` en cada combinación de `Supuesto` (`V`, `F` o `-` si
la rechaza su `precond`), para localizar distractores constantes.

# Documentación

En este orden:

-   `Tutorial.ipynb` — ejemplos progresivos ejecutables (también en
    MyBinder); `ejemplosManual/Demo.ipynb` recorre la API Python.
-   `GuiaDiseno.org` — cómo diseñar buenas preguntas: la mecánica de
    listas y mundos, el patrón de tres huecos + opción por defecto,
    `setup`, redacción de cuestiones y explicaciones, trampas de
    LaTeX/Moodle y checklist.
-   `Manual.org` — referencia completa de la API y del formato JSON.
-   `CalcPropQuiz.org` y `CalcPropExport.org` — código fuente comentado
    (programación literate) de los módulos `_quiz`, `_json`, `_widgets`,
    `_lint`, `_export` y `_plantilla`. Son la fuente de `src/qbank/`:
    los `.py` se generan con `org-babel-tangle` o, sin Emacs, con
    `python tools/orgtangle.py write`; `tests/test_literate.py`
    comprueba que coinciden.

# Tests

``` bash
pytest
```

# Autoría y licencia

Copyright (C) 2020-2026 Andrés Bujosa, Marcos Bujosa (`_quiz`)  
Copyright (C) 2020-2026 Marcos Bujosa (`_export`, `_json`, `_widgets`)

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

See the
[LICENSE](https://github.com/mbujosab/calcprop-qbank/blob/main/LICENSE)
file for details.
