# calcprop-qbank (qbank)

## Modelo recomendado: Sonnet

## Qué es este repo

Motor de generación de bancos de preguntas de opción múltiple usando cálculo
proposicional (`calcprop`). Exporta a AMC (PDF) y Moodle (XML + PDF).

- **Paquete PyPI:** `calcprop-qbank`
- **Importación:** `from qbank import *`
- **Dependencias:** `calcprop>=0.2.0`, `numpy`, `ipywidgets>=8` (extra `jupyter`)
- **Entorno:** `.venv/` en este repo (calcprop instalado en modo editable desde
  su propio repo en `~/SynologyDrive/ReposGH/Docencia/calcprop`)

## Estructura de fuentes

```
src/qbank/
  __init__.py   — re-exporta _quiz, _export, _json, _widgets
  _quiz.py      — clases núcleo: Supuesto, Cuestion, ProblemaTipo, ProblemaVF
  _export.py    — AMCblock, QuizMoodle, QuizAMCProfe, AMC_VF, AMC_multipart
  _json.py      — load_problema, save_problema, load_banco, save_banco
  _widgets.py   — widgets Jupyter (importación opcional)
  _lint.py      — lint, tabla_mundos, Aviso; lint.py es el shim de `python -m qbank.lint`
```

## Fuentes de verdad y ficheros generados

- **Programación literate: `CalcPropQuiz.org` y `CalcPropExport.org` son la
  fuente de `src/qbank/*.py`** (noweb: cada módulo es un esqueleto de
  referencias `<<Sección>>` y cada función vive en su bloque con nombre junto a
  su prosa). Flujo para cambiar código:
  1. Editar el bloque correspondiente del `.org` (y su prosa).
  2. `python tools/orgtangle.py write` regenera `src/` sin necesidad de Emacs
     (equivale byte a byte a `org-babel-tangle`); o tanglear desde Emacs.
  3. `python tools/orgtangle.py check` (lo ejecuta `tests/test_literate.py`)
     falla si `src/` y los `.org` no coinciden. Nunca editar solo el `.py`.
  Para código nuevo: bloque `#+NAME:` + referencia en el esqueleto del módulo.
  Ojo: Emacs sangra también las líneas en blanco dentro de una referencia
  indentada; `write` reproduce eso, así que `src/` puede tener blancos con
  espacios. `informe` dice qué bloques difieren si alguien editó el `.py`.
- **`README.md` se genera desde `README.org`:**
  `pandoc -f org -t gfm README.org -o README.md`. Editar siempre el `.org`.
- `Manual.org` es el manual de usuario (su PDF se exporta desde Emacs).
- `PLAN-documentacion.org` es el plan vigente de reorganización de la
  documentación (diagnóstico, decisiones y fases con su estado).
- `tests/test_lint.py` y `tests/test_export.py` son la suite: `.venv/bin/python -m pytest`.

## API pública principal

### Construcción de preguntas (Python-first)

```python
from qbank import *

s = Supuesto("Enunciado", semantica, precond=True)
c = Cuestion("¿Verdad?", semantica, precond=True, exp="")
p = ProblemaTipo("nombre", [s, [s1, s2], [c1, c2]])
```

### Iteración de variantes

```python
# Todas las variantes (una por combinación de mundos)
for etiqueta, partes in p.por_partes():
    for enunciado, cuestiones in partes:
        ...

# Con instancias aleatorias (requiere numpy; setup con np.random)
for etiqueta, partes in p.por_partes(instances=10, base_seed=42):
    ...

# Vista profe (incluye rechazadas)
for etiqueta, partes in p.por_partes_profe():
    ...
```

### Serialización JSON

```python
save_problema(p, "mi_pregunta.json")
p = load_problema("mi_pregunta.json")   # desde fichero
p = load_problema(d)                    # desde dict en memoria
```

Formato JSON (`version: "1"`, `tipo: "ProblemaTipo"`):

```json
{
  "version": "1",
  "tipo": "ProblemaTipo",
  "nombre": "L-07-ejemplo",
  "seed": 7,
  "setup": "import numpy as np\nx = np.random.randint(1, 10)",
  "export": {"last_choice": true, "cols": 2, "instances": 10},
  "componentes": [...]
}
```

- `seed`: solo en preguntas con `np.random` en setup. Garantiza reproducibilidad.
- `instances`: `max(1, ceil(60 / variantes_por_instancia))` — objetivo ≥60 variantes.
- Textos sueltos van como cadenas directas, no dentro de `[...]`.
- `precond` usa semántica lambda sobre el namespace `ns`.
- Interpolación: `@{var}` en enunciados (delimitador `@` en `_NsTemplate`).
- `exp` (explicación) admite la misma interpolación `@{var}` que `enunciado`.
  Así una sola explicación sirve para todas las variantes, mostrando los
  valores concretos de cada una. **Desde JSON solo se evalúan `semantica` y
  `precond`**: un `enunciado` o `exp` escrito como `"lambda ns: ..."` llega
  literal al alumno (el lint lo avisa). Para textos que dependen de los datos,
  calcula el texto como variable en `setup` y usa `"exp": "@{exp_plano}"`.
  Las lambdas reales en `enunciado`/`exp` solo existen construyendo los
  objetos en Python.

### Exportación AMC

```python
# Bloque AMC para una variante
AMCblock(nombre, etiqueta, enunciado, cuestiones,
         last_choice=False, cols=1, profe=False,
         last_choice_text="Ninguna de las anteriores")

# Quiz AMC completo (vista profe)
QuizAMCProfe(nombre, directorio, problema, last_choice=False, cols=1)
```

### Exportación Moodle

```python
# Genera .tex, .pdf y -moodle.xml en directorio/
QuizMoodle(nombre, directorio, problema,
           last_choice=False, instances=1,
           last_choice_text="Las demás opciones son falsas")
```

- `$$...$$` se convierte automáticamente a `\[...\]`.
- Los nombres sanitizan `:` y `_` → `-` para compatibilidad LaTeX.
- `cols` solo actúa si se pasa: `QuizAMCProfe(..., cols=N)` y
  `AMCblock(..., cols=N)`. Un script que genere la vista profe sin pasar
  `export.cols` la mostrará a una columna aunque la vista alumno use dos.
- La vista alumno AMC pone todas las variantes en un `examcopy`; por encima
  de ~300 `pdflatex` puede agotar la memoria (el lint lo informa).

### Comprobación automática (`lint`)

```python
avisos = lint(problema_o_ruta, instances=None, seed=None)   # -> list[Aviso]
print(tabla_mundos(problema_o_ruta))                         # Cuestion × mundo
```

CLI: `python -m qbank.lint preguntas/*.json [--instances N] [--seed S] [--tabla] [--quiet]`
(también `qbank-lint`). Código de salida 1 si hay algún `ERROR`. `--quiet`
omite los INFO y los ficheros sin avisos.

Implementación en `src/qbank/_lint.py` (el docstring lista las 9 reglas y
sus códigos). Niveles: `ERROR` (la pregunta está rota: mezcla, negación sin
`unoDe`, `@{var}` sin resolver, estructura, nombre), `AVISO` (revisar:
pocas variantes, `Cuestion` constante en todos sus mundos, lista de un
elemento, seed/instances incoherentes, texto sospechoso), `INFO`.

- La regla de negación considera deducible `-v('X')` si hay `unoDe(...)`
  con `v('X')` en un `Supuesto` suelto **o** si algún `Supuesto` afirma
  directamente `-v('X')` (patrón habitual: dos alternativas `v('X')` /
  `-v('X')`).
- Una `Cuestion` con `semantica` literal `True`/`False` constante en todos
  sus mundos es INFO, no AVISO (es un distractor deliberado).
- `_ns_interp(s, ns, strict=None)`: con `strict=True` (o
  `qbank._quiz.STRICT_INTERP = True`) lanza `ValueError` ante `@{var}`
  desconocida. Por defecto sigue dejando el texto intacto.
- `por_partes_profe(verbose=True)` admite `verbose=False` como `por_partes`.

## Notebooks de referencia

- **`Ejemplos.ipynb`** — workflow Python-first completo con ejemplo de
  econometría (multicolinealidad): `Supuesto`/`Cuestion` → `ProblemaTipo` →
  `por_partes_profe()` → `save_problema` → `load_problema` → `QuizMoodle` /
  `QuizAMCProfe`.

- **`Tutorial.ipynb`** — 5 ejemplos progresivos con JSONs en `ejemplosManual/`.
  Sin dependencias de econometría. Cubre: T/F literales, mundos proposicionales,
  `precond`, interpolación `@{var}` y semántica lambda.

- **`ejemplosManual/Demo.ipynb`** — demostración interactiva que usa los mismos
  JSONs de `ejemplosManual/`.

Los tres deben funcionar en MyBinder tras cada release.

## Publicar una nueva versión

1. Incrementar `version` en `pyproject.toml`.
2. Commit + `git tag vX.Y.Z && git push && git push --tags`.
3. `python -m build && twine upload dist/*`.
4. Añadir `numpy` (y cualquier dependencia nueva) a `binder/requirements.txt`
   para forzar rebuild de la imagen MyBinder.
5. Verificar que los tres notebooks arrancan en MyBinder.
6. Actualizar el entorno del banco de econometría:
   `pip install -e /ruta/a/qbank` (o `pip install calcprop-qbank==X.Y.Z`).

## Banco de econometría

El repo usuario principal de qbank está en
`~/SynologyDrive/ReposGH/Docencia/qbank-econometria` (su CLAUDE.md tiene
detalles de uso, campo `export`, regla de `instances`, etc.).
