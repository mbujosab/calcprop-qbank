# Ejemplos del Manual y de los cuadernos

Preguntas de ejemplo en JSON que cargan `Manual.org`, `Tutorial.ipynb` y
`Demo.ipynb` (ejecútalos desde la raíz del repositorio). Todas pasan
`python -m qbank.lint ejemplosManual/*.json` sin ERROR ni AVISO.

| Fichero | Qué ilustra |
|---|---|
| `ej_a_literales.json` … `ej_e_lambda.json` | Los cinco ejemplos progresivos del Tutorial: literales, mundos, `precond`, `setup` con `@{var}` y semántica `lambda`. |
| `ejercicio.json` | El ejemplo principal del Manual: dos listas de `Supuesto` y tres huecos (48 variantes). |
| `matriz_rango.json`, `numeros.json` | `setup` aleatorio con `seed` e `instances`; `numeros.json` es el que carga el editor visual de `Demo.ipynb`. |
| `superheroes.json` | Pregunta de tres partes. |
| `Demo.ipynb` | Recorrido por la API Python (construcción, editor visual, exportadores). |
| `EjemploMoodle.pdf`, `EjemploMoodle-moodle.xml` | Lo que produce el ejemplo «Exportar a Moodle» del Manual con `ejercicio.json`. |
| `EjemploVF.pdf`, `EjemploVF-moodle.xml` | Salida antigua de una pregunta `ProblemaVF` (verdadero/falso; ver el apéndice del Manual). |

Los cuadernos escriben sus salidas en `mis_problemas/` y `exportaciones/`,
que no se versionan.
