# calcprop-qbank (qbank)

## Modelo recomendado: Sonnet

## Qué es este repo

Motor de generación de bancos de preguntas de opción múltiple usando cálculo
proposicional (`calcprop`). Exporta a AMC (PDF) y Moodle (XML + PDF).

- **Paquete PyPI:** `calcprop-qbank`
- **Importación:** `from qbank import *`
- **Dependencias:** `calcprop>=0.1`, `numpy`, `ipywidgets>=8` (extra `jupyter`)
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
```

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
