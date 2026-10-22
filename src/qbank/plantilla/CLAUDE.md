# Banco de preguntas (proyecto `qbank-init`)

Banco de preguntas de opción múltiple para [RELLENAR: asignatura],
generado con el motor [`calcprop-qbank`](https://github.com/mbujosab/calcprop-qbank).
Este fichero es solo el punto de entrada y no duplica la documentación.
Antes de escribir o modificar una pregunta, lee en este orden:

1. `prompts/PROMPT-qbank-generico.org`: qué leer, el proceso de trabajo
   y las reglas sin excepción para una IA. Remite a la Guía de diseño y
   al Manual de `qbank`, que son la fuente de verdad del motor.
2. `prompts/PROMPT-proyecto.org`: las decisiones de este banco (fuentes,
   nombres, notación, objetivo, checklist propio, registro de decisiones).
3. `README.org`: qué hay en la carpeta, el flujo con `make` y cómo leer la
   vista profe.

## Entorno

- Intérprete con `qbank`: [RELLENAR: `.venv/bin/python` de este proyecto,
  o la ruta de otro entorno]. Pásalo a `make` si no está activado:
  `make lint PYTHON=/ruta/al/python`.
- Comprobar la versión: `python -c "import qbank; print(qbank.__version__)"`
  (el `Makefile` exige 0.8 o posterior).
- LaTeX: [RELLENAR: disponible (`pdflatex` con `automultiplechoice` y
  `moodle`) o no; sin LaTeX solo `make lint` y `make tabla`].

## Estructura

```
preguntas/L-NN-Descripcion.json   una pregunta por fichero (ProblemaTipo)
prompts/                          instrucciones para la IA (los dos de arriba)
nueva_pregunta.py                 escribir una pregunta en Python y guardarla como JSON
config.py                         preámbulo LaTeX propio y textos de la opción por defecto
scripts/, Makefile                generadores AMC y Moodle; no se tocan
build/                            todo lo generado; no se versiona
```

## Órdenes habituales

```sh
make lint                         # todas las preguntas; LECCION=N para una lección
make tabla PREGUNTA=L-01-Nombre   # lint + tabla de mundos de una pregunta
make patrones                     # lint --patrones: pistas memorizables (más lento; LECCION=N)
make amc                          # vista profe en build/amc/ (repasar entera)
make lectura                      # documento por lección para leer las preguntas (build/lectura/)
make amc-student                  # variantes del alumno (AMC)
make moodle                       # XML de Moodle + PDF de revisión
```

## Reglas del banco (resumen; detalle en `prompts/`)

- Ninguna pregunta se acepta sin `make lint` limpio de `ERROR` y sin haber
  repasado su vista profe en todos los mundos.
- Patrón por defecto: tres huecos más la opción por defecto
  (`"export": {"last_choice": true}`).
- Toda decisión que afecte a más de una pregunta se anota, con fecha, en
  el registro de `prompts/PROMPT-proyecto.org`.
- [RELLENAR: reglas duras propias de este banco].
