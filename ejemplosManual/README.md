# Ejemplos del Manual y de los cuadernos

Preguntas de ejemplo en JSON que cargan `Manual.org` y los cuadernos
`Tutorial.ipynb` y `Demo.ipynb`, que están en la raíz del repositorio y se
ejecutan desde allí. Todas pasan
`python -m qbank.lint ejemplosManual/*.json` sin ERROR ni AVISO.

| Fichero | Qué ilustra |
|---|---|
| `ej_a_literales.json` … `ej_e_lambda.json` | Los cinco ejemplos progresivos del Tutorial: literales, mundos, `precond`, `setup` con `@{var}` y semántica `lambda`. |
| `ejercicio.json` | El ejemplo principal del Manual: dos listas de `Supuesto` y tres huecos (48 variantes). |
| `matriz_rango.json`, `numeros.json` | `setup` aleatorio con `seed` e `instances`; `numeros.json` es el que carga el editor visual de `Demo.ipynb`. |
| `superheroes.json` | Pregunta de tres partes. |
| `EjemploMoodle.pdf`, `EjemploMoodle-moodle.xml` | Lo que produce el ejemplo «Exportar a Moodle» del Manual con `ejercicio.json`. |

`Demo.ipynb` escribe sus salidas en `ejemplosManual/mis_problemas/` y
`ejemplosManual/exportaciones/`, que no se versionan.
