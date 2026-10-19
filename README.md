[![](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mbujosab/calcprop-qbank/main?urlpath=lab/tree/ejemplosManual)

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

# Crear un banco de preguntas

La forma recomendada de empezar es la plantilla de proyecto que se
distribuye con el paquete (desde la versión 0.6.0; con una versión
anterior, instala desde el repositorio:
`pip install git+https://github.com/mbujosab/calcprop-qbank`):

``` bash
qbank-init mi-banco
cd mi-banco
make lint          # comprueba las preguntas de ejemplo (sin LaTeX)
make amc           # PDF de revisión (vista profe) en build/amc/
```

El proyecto contiene cuatro preguntas de ejemplo en `preguntas/`, los
scripts que las exportan a AMC y Moodle, un `Makefile` (`lint`, `amc`,
`amc-student`, `moodle`, filtro `LECCION=N`) y `nueva_pregunta.py`, un
guion para escribir una pregunta en Python y guardarla como JSON. Su
`README.org` explica el flujo.

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

Ocho variantes, cada una con tres opciones más la opción por defecto.
Una **lista** de `Cuestion` sortea una por variante; el alumno ve tantas
opciones como elementos-Cuestion consecutivos haya (`GuiaDiseno.org` lo
explica).

# Características

## Generación combinatoria de variantes

`ProblemaTipo` toma una lista de supuestos y cuestiones (cada uno con su
semántica proposicional) y genera todas las combinaciones posibles. Para
cada variante calcula automáticamente qué ítems son verdaderos y cuáles
falsos. Las variantes con hipótesis incoherentes o precondiciones
insatisfechas se descartan.

El método `por_partes_profe()` muestra todas las cuestiones de cada
sublista (sin descartar, marcando las rechazadas por su precondición),
facilitando la revisión del banco.

## Preguntas multi-parte

La misma lista plana de componentes admite varias partes: cada vez que
tras un bloque de cuestiones aparece texto o un `Supuesto` se abre una
parte nueva. Es útil para preguntas AMC con múltiples apartados o para
el formato cloze de Moodle. El método `por_partes()` devuelve, por
variante, un par `(enunciado, cuestiones)` por parte:

``` python
from qbank import *

p = ProblemaTipo([
    "Suponga que ",
    [Supuesto("$A$ es verdadero, ", v("A")),
     Supuesto("$B$ es verdadero, ", v("B"))],
    "¿Cuál es el valor de $A$? ",
    [Cuestion("Verdadero.", v("A")), Cuestion("Falso.", -v("A"))],
    "¿Cuál es el valor de $B$? ",
    [Cuestion("Verdadero.", v("B")), Cuestion("Falso.", -v("B"))],
])

for etiqueta, partes in p.por_partes():
    for enunciado, cuestiones in partes:
        ...
```

(`ProblemaMultiParte` y `SubPregunta` siguen existiendo por
compatibilidad, pero están deprecados y devuelven un `ProblemaTipo`
equivalente.)

## Preguntas paramétricas con `setup`

El parámetro `setup` permite que los valores numéricos o simbólicos
cambien en cada variante. El texto de los slots admite marcadores
`@{variable}` para interpolación:

``` python
import random

def numeros():
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    return {'a': a, 'b': b, 'suma': a + b}

p = ProblemaTipo(
    ["Sean $a = @{a}$ y $b = @{b}$. ",
     [Cuestion("$a + b = @{suma}$", True),
      Cuestion("$a + b > 10$", lambda ns: ns['a'] + ns['b'] > 10)]],
    setup=numeros,
)
```

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

Función de bajo nivel que devuelve un bloque LaTeX listo para escribir
al fichero:

``` python
with open("preguntas.tex", "w") as f:
    for etiqueta, partes in p.por_partes():
        for enunciado, cuestiones in partes:
            f.write(AMCblock("MiCuestionario", etiqueta, enunciado, cuestiones))
```

Vista aplanada para el profesor (todas las cuestiones con marcas):

``` python
n = QuizAMCProfe("MiCuestionario", "exportaciones/", p)
print(f"{n} bloque(s) escritos")
```

Para preguntas multi-parte, `AMC_multipart(nombre, etiqueta, "", partes,
last_choice=…, cols=…)` produce un único `questionmult` con un bloque de
casillas por parte.

### Formato Moodle (XML vía LaTeX)

``` python
# Vista alumno
n = QuizMoodle("MiCuestionario", "exportaciones/", p, last_choice=True)
print(f"{n} variante(s) escritas")

# Vista profe (fracciones de puntuación visibles)
QuizMoodleProfe("MiCuestionario", "exportaciones/", p)

# Con paquete LaTeX adicional y texto comodín personalizados
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

for a in lint("preguntas/L-01-ejemplo.json"):
    print(a)
print(tabla_mundos("preguntas/L-01-ejemplo.json"))   # Cuestion × mundo
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
    `_lint` y `_export`. Son la fuente de `src/qbank/`: los `.py` se
    generan con `org-babel-tangle` o, sin Emacs, con
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
