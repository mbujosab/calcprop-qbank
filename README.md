# qbank — generador de bancos de preguntas de opción múltiple

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mbujosab/calcprop-qbank/main?urlpath=lab/tree/ejemplosManual)

Genera variantes de preguntas de opción múltiple cuyas respuestas correctas se determinan automáticamente mediante cálculo proposicional. Combina supuestos e ítems de respuesta por combinatoria, calcula la veracidad o falsedad de cada ítem según las hipótesis activas y exporta el resultado a LaTeX (AMC) o Moodle (XML vía LaTeX).

Construido sobre [`calcprop`](https://github.com/mbujosab/calcprop).

## Instalación

```bash
pip install calcprop calcprop-qbank
```

Con soporte para el editor visual en Jupyter:

```bash
pip install "calcprop-qbank[jupyter]"
```

## Uso rápido

```python
from qbank import *

p = ProblemaTipo([
    "Dado que ",
    [
        Supuesto("$\\mathcal{A}$ es verdadero, ", v("A")),
        Supuesto("$\\mathcal{B}$ es verdadero, ", v("B")),
    ],
    "indique qué opción es correcta: ",
    [
        Cuestion("$\\mathcal{A}$ es verdadero.", v("A")),
        Cuestion("$\\mathcal{B}$ es verdadero.", v("B")),
    ],
])

for etiqueta, enunciado, cuestiones in p:
    print(f"Variante {etiqueta}: {enunciado}")
    for texto, correcto, activa, exp in cuestiones:
        print(f"  {'✓' if correcto else '✗'} {texto}")
```

## Características

### Generación combinatoria de variantes

`ProblemaTipo` toma una lista de supuestos y cuestiones (cada uno con su semántica proposicional), y genera todas las combinaciones posibles. Para cada variante calcula automáticamente qué ítems son verdaderos y cuáles falsos. Las variantes con hipótesis incoherentes o precondiciones insatisfechas se descartan.

`ProblemaTipoProfe` muestra todas las cuestiones para cada enunciado (sin descartar), facilitando la revisión del banco.

### Preguntas multi-parte

`ProblemaMultiParte` genera variantes en las que cada enunciado va seguido de varios bloques de sub-preguntas independientes. Es útil para preguntas AMC con múltiples apartados o para el formato cloze de Moodle:

```python
from qbank import *

subpreguntas = [
    SubPregunta("¿Cuál es el valor de $A$? ",
                [Cuestion("Verdadero.", v("A")),
                 Cuestion("Falso.",    ~v("A"))]),
    SubPregunta("¿Cuál es el valor de $B$? ",
                [Cuestion("Verdadero.", v("B")),
                 Cuestion("Falso.",    ~v("B"))]),
]

p = ProblemaMultiParte(
    ["Suponga que ",
     [Supuesto("$A$ es verdadero, ", v("A")),
      Supuesto("$B$ es verdadero, ", v("B"))]],
    subpreguntas,
)

for etiqueta, enunciado, subs in p:
    print(f"Variante {etiqueta}: {enunciado}")
    for intro, cuestiones in subs:
        print(f"  {intro}")
        for texto, correcto, activa, exp in cuestiones:
            print(f"    {'✓' if correcto else '✗'} {texto}")
```

### Preguntas paramétricas con `setup`

El parámetro `setup` permite que los valores numéricos o simbólicos cambien en cada variante. El texto de los slots admite marcadores `@variable` para interpolación:

```python
import random

def numeros():
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    return {'a': a, 'b': b, 'suma': a + b}

p = ProblemaTipo(
    ["Sean $a = @a$ y $b = @b$. ",
     [Cuestion("$a + b = @suma$", True),
      Cuestion("$a + b > 10$", lambda ns: ns['a'] + ns['b'] > 10)]],
    setup=numeros,
)
```

### Persistencia en formato JSON

Guarda y carga problemas (`ProblemaTipo`, `ProblemaMultiParte`, `ProblemaVF`) sin reescribir el código Python:

```python
from qbank import load_problema, save_problema

p = load_problema('mi_problema.json')
save_problema(p, 'copia.json')
```

Para bancos de múltiples problemas: `load_banco` / `save_banco`.

### Editor visual en Jupyter

`ProblemaTipoEditor` es un formulario interactivo (requiere `ipywidgets`) que permite construir, previsualizar y guardar problemas sin escribir código:

```python
from qbank import ProblemaTipoEditor

editor = ProblemaTipoEditor()            # editor vacío
editor = ProblemaTipoEditor('p.json')   # cargar desde fichero

p = editor.to_problema()                # obtener el ProblemaTipo
```

Ver la [guía de instalación de ipywidgets en JupyterLab](Manual.org) si los widgets se muestran como texto en lugar del formulario.

### Exportación a AMC y Moodle

**Preguntas estándar (`ProblemaTipo`):**

- **AMC (LaTeX)**: `AMC`, `AMClastCh`, `AMCmc`, `AMCmcProfe`, …
- **Moodle (XML vía LaTeX)**: `QuizMoodle`, `QuizMoodleLastCh`, `QuizVFMoodle`, …

```python
with open("preguntas.tex", "w") as f:
    for etiqueta, enunciado, cuestiones in p:
        f.write(AMC("MiCuestionario", etiqueta, enunciado, cuestiones))
```

**Preguntas multi-parte (`ProblemaMultiParte`):**

- **AMC**: `AMC_multipart` — genera un único `\begin{questionmult}` con un bloque `\begin{choices}` por sub-pregunta.
- **Moodle cloze**: `QuizClozeMulti` — genera preguntas `\begin{cloze}` con sub-bloques `\begin{multi}` incrustados.

```python
with open("preguntas.tex", "w") as f:
    for etiqueta, enunciado, subs in p:
        f.write(AMC_multipart("MiCuestionario", etiqueta, enunciado, subs))
```

### Exportación a código Python editable

`problema_to_python` / `save_problema_py` generan un fichero `.py` con la definición del problema como listas editables, tanto para `ProblemaTipo` como para `ProblemaMultiParte`:

```python
from qbank import save_problema_py

save_problema_py(p, 'mi_problema.py')
```

El fichero resultante puede abrirse con cualquier editor, modificarse y ejecutarse directamente con Python.

## Documentación

- `CalcPropQuiz.org` — código fuente comentado del módulo `_quiz`, `_json` y `_widgets`.
- `CalcPropExport.org` — código fuente comentado del módulo `_export`.
- `Manual.org` — manual de usuario con ejemplos.

Los ficheros Python se generan desde los `.org` mediante `org-babel-tangle`.

## Autoría y licencia

Copyright (C) 2020-2026  Andrés Bujosa, Marcos Bujosa (`_quiz`) /
Copyright (C) 2020-2026  Marcos Bujosa (`_export`, `_json`, `_widgets`)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the [LICENSE](LICENSE) file for details.
