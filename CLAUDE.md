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
  _plantilla.py — qbank-init: copia plantilla/ (proyecto de banco) a un directorio
  plantilla/    — datos del paquete: preguntas/ de ejemplo, scripts/, Makefile,
                  config.py, nueva_pregunta.py, README.org, CLAUDE.md (el del banco,
                  no este) y prompts/ (Fase 4: prompts para una IA) (ver tests/test_plantilla.py)
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
- `Manual.org` es el manual de usuario. **Los PDF** (`Manual`, `GuiaDiseno`,
  `CalcPropQuiz`, `CalcPropExport`, `Fase5-prueba`) se generan con Emacs en
  batch y lualatex (tres pasadas), y se versionan:
  `emacs --batch X.org --eval '(progn (require (quote ox-latex)) (setq org-confirm-babel-evaluate nil org-export-use-babel nil org-latex-pdf-process (list "lualatex -interaction nonstopmode -output-directory %o %f" "lualatex -interaction nonstopmode -output-directory %o %f" "lualatex -interaction nonstopmode -output-directory %o %f")) (org-latex-export-to-pdf))'`
  y después borrar `X.tex X.aux X.log X.out X.toc`. Comprobar en el `.log`
  que no hay `Missing character` ni `Overfull` grandes fuera de tablas.
- **`docs/` es la web de GitHub Pages** (https://mbujosab.github.io/calcprop-qbank/,
  servida desde `main:/docs`) y **se genera con `sh tools/web.sh`; no se edita
  a mano** (salvo `docs/style.css`, la hoja única). `tools/web.el` exporta
  `index.org` (portada, en la raíz), `README.org`, el README de la plantilla,
  `GuiaDiseno.org` y `Manual.org` a HTML y copia los dos PDF (regenéralos
  antes). Los ajustes de HTML van en `web.el`, no en los `.org`: sin CSS ni
  JavaScript de Org salvo MathJax (un solo `<script>` desde CDN, no entra
  en `<pre>` ni `<code>`), `<title>` sin marcado, índice de dos niveles. Un fragmento solo para HTML
  en un `.org` va como `@@html:…@@` junto a su `@@latex:…@@`.
- `GuiaDiseno.org` es la guía de diseño de preguntas para personas
  (mecánica, patrón 3 huecos + `last_choice`, `setup`, redacción, `exp`,
  trampas LaTeX/Moodle, checklist). Destilada de
  `qbank-PEconometria/PROMPT-qbank-generico.org`, sin fechas ni referencias
  a lecciones; los prompts deben remitir a ella, no duplicarla.
- `PLAN-documentacion.org` es el plan vigente de reorganización de la
  documentación (diagnóstico, decisiones y fases con su estado).
- La suite (`.venv/bin/python -m pytest`): `tests/test_lint.py`, `test_export.py`,
  `test_plantilla.py` (autoría en Python, plantilla y sus scripts) y
  `test_literate.py` (los `.org` coinciden con `src/`).

## API pública principal

### Construcción de preguntas (Python-first)

```python
from qbank import *

s = Supuesto("Enunciado", semantica, precond=True)
c = Cuestion("¿Verdad?", semantica, precond=True, exp="")
p = ProblemaTipo([s, [s1, s2], [c1, c2]], setup=None, export=None, seed=None, nombre=None)
```

- `semantica` y `precond` admiten también la **cadena** que los representa
  (`"v('A') >> v('B')"`, `"lambda ns: ns['x'] > 0"`), evaluada igual que
  desde JSON; los originales se guardan en `_orig` y `save_problema` los
  serializa. Una lambda escrita como función Python no se puede guardar.
- `setup` admite el **código Python como cadena** (lo que guarda el JSON);
  `ProblemaTipo` lo compila y conserva `_setup_str`. Un `setup` función
  tampoco se puede guardar.
- `nombre=` fija `_nombre` (el campo `nombre` del JSON).
- `_eval_expr` acepta `"true"`/`"false"` en cualquier caja; una cadena vacía o
  inválida lanza `ValueError` con el componente y el campo. El código del
  `setup` se conserva tal cual en `_setup_str` y se ejecuta con `dedent`.
- `problema_to_python` emite `_SETUP = r"""…"""`, las lambdas entre comillas y
  `nombre=`: el `.py` resultante vuelve a guardarse con `save_problema`.
- `QuizAMCProfe(nombre, directorio, problema, cols=1, *, last_choice=False, …)`
  y `QuizMoodleProfe(..., *, last_choice=False, instances=1, …)`: las mismas
  variantes que la vista alumno. Las funciones de exportación **no leen**
  `export`: hay que pasarles `last_choice=`, `instances=`, `cols=` (los
  scripts de la plantilla sí lo leen).
- `qbank.__version__` (de los metadatos); el `Makefile` de la plantilla exige
  ≥ 0.7 en `comprueba` (desde 0.7.0, por `make lectura`).
- `seed` / `base_seed` siembran `numpy.random` **y** el módulo `random`
  (`_siembra`); `por_partes(base_seed=S)` también actúa con `instances=1`.
  `tabla_mundos` siembra con `seed` (o 42) y, como el motor, cada `Cuestion`
  solo ve los `Supuesto` que la preceden (antes usaba los de partes
  posteriores).
- Las claves no reconocidas del JSON (`_nivel`, …) se conservan en
  `p._extra` y `save_problema` las devuelve; el editor de widgets conserva
  también `export.instances` y demás.
- `_ns_interp` sustituye siempre (también sin `setup`): `@@` → `@`.
- Los `Quiz*` aceptan `directorio` con o sin `/` final (`os.path.join`).
- `lint`: `negacion` no es ERROR si la negación es deducible de algún
  `Supuesto` a cualquier profundidad (`>> -v('X')`, `unoDe` dentro de una
  conjunción o en Supuestos de lista); `sin-uso` calla si alguna `Cuestion`
  usa lambdas; `doble espacio` ignora el interior de `$…$`; `export` y
  `seed` mal tipados (también `seed: true`) son ERROR `estructura` (no
  revientan); `@@{x}` no es ERROR `interp`; `constante` es INFO si la
  `Cuestion` es lambda con `setup`; las reglas de `%` miran también el texto
  interpolado; espacios en `nombre` o en el fichero son ERROR `nombre`.
- Flujo recomendado para escribir a mano: lista Python → `save_problema` →
  JSON en `preguntas/` (es lo que hace `plantilla/nueva_pregunta.py`).

### Proyecto de banco (`qbank-init`)

`qbank-init DIR` (o `python -m qbank._plantilla DIR`) copia
`src/qbank/plantilla/` a `DIR`: `preguntas/*.json`, `scripts/gen_amc.py`,
`gen_amc_student.py`, `gen_moodle.py`, `_comun.py` (filtro `--leccion`,
escritura solo-si-cambia, preámbulo AMC), `fix_moodle_xml.py`,
`merge_moodle_xml.py`, `gen_lectura.py`, `Makefile` (`lint`, `tabla PREGUNTA=`, `amc`,
`amc-student`, `moodle`, `lectura`, `all`, `clean`, `LECCION=`; `PYTHON=` para el
intérprete), `config.py`, `nueva_pregunta.py`, `README.org`. Los scripts leen `export` de cada JSON.
`tests/test_plantilla.py` ejecuta los scripts sobre las preguntas de ejemplo
(sin compilar LaTeX); las preguntas de ejemplo deben pasar `lint` sin AVISO.

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
         last_choice=False, cols=1, profe=False, *, aux_latex="",
         last_choice_text="Ninguna de las anteriores")

# Quiz AMC completo (vista profe): directorio/nombre_profe.tex, una entrada
# por mundo; devuelve el número de mundos
QuizAMCProfe(nombre, directorio, problema, cols=1, *,
             last_choice=False, aux_latex="",
             last_choice_text="Ninguna de las anteriores")
```

### Exportación Moodle

```python
# Escribe directorio/nombre.tex; al compilarlo con pdflatex (paquete moodle)
# salen nombre.pdf y nombre-moodle.xml
QuizMoodle(nombre, directorio, problema,
           last_choice=False, instances=1, *, aux_latex="",
           last_choice_text="Las demás opciones son falsas")

# Vista profe (fracciones visibles); mismos last_choice/instances. Escribe
# también directorio/nombre.tex: usar otro nombre que la vista alumno
QuizMoodleProfe(nombre, directorio, problema, *, aux_latex="",
                last_choice=False, instances=1,
                last_choice_text="Las demás opciones son falsas")
```

- Los nombres sanitizan `:` y `_` → `-` para compatibilidad LaTeX.
- `codchar` (lo aplican las funciones Moodle) convierte todas las letras del
  español (también mayúsculas y `ü`) y `¿` `¡` (`\textquestiondown ` con
  espacio, no `{}`, que llegaría literal al HTML). `moodle.sty` las pasa a
  entidades HTML; un carácter no convertido llega al XML en UTF-8 bajo la
  declaración `iso-8859-1` (`antigÃ¼edad` en Moodle) y solo lo salva el
  `fix_moodle_xml.py` de la plantilla (los bancos tenían una copia antigua).
- Subir/actualizar en Moodle desde el terminal con la cookie `MoodleSession`:
  `scripts/moodle_sync.py` y `moodle_quiz.py` del banco PEconometria,
  documentados en `Manual.org` («Subir y actualizar el banco en Moodle desde
  el terminal»); fechas y visibilidad, a mano.
- Los `Quiz*` escriben el `.tex` en UTF-8 explícito (en Windows `open()`
  usaría cp1252 y un carácter que `codchar` no convierte —«¿» hasta 0.7.0,
  hoy p. ej. «“»— rompía `gen_moodle.py`).
- (AMC, no Moodle) `AMCblock` y `AMC_multipart` convierten `$$...$$` a `\[...\]`.
- **Multiparte en AMC**: `AMC_multipart(nombre, etiqueta, "", partes,
  last_choice=, cols=, profe=, last_choice_text=)` — un solo `questionmult`
  con un bloque de casillas por parte. Escribir un `AMCblock` por parte
  produce identificadores duplicados y la segunda parte sin hipótesis;
  `QuizAMCProfe` y los scripts de la plantilla ya usan `AMC_multipart`
  cuando `len(partes) > 1`, igual que los `gen_amc*.py` de los dos bancos.
- `cols` solo actúa si se pasa: `QuizAMCProfe(..., cols=N)` y
  `AMCblock(..., cols=N)`. Un script que genere la vista profe sin pasar
  `export.cols` la mostrará a una columna aunque la vista alumno use dos.
- La vista alumno AMC pone todas las variantes en un `examcopy`; por encima
  de ~300 `pdflatex` puede agotar la memoria (el lint lo informa).

### Vista de lectura

```python
QuizLectura(nombre, directorio, problemas, *, aux_latex="", titulo=None,
            last_choice=None, last_choice_text="Ninguna de las anteriores",
            extras=0, max_semillas=400)        # escribe directorio/nombre.tex; -> nº ejemplos
for r in p.por_partes_lectura(seed=None, verbose=False, descartes=False):
    r.etiqueta, r.mundo, r.ns, r.partes, r.descarte      # Lectura; partes: ParteLectura(enunciado, huecos)
```

- Documento completo para *leer* las preguntas (no para el examen): tabla
  de mundos, un ejemplo por mundo (y por combinación de valores de
  `lectura.cubrir` con `setup`), alternativas por hueco con V/F y `exp`,
  excluidas en gris con motivo, mundos descartados. `problemas` admite
  lista (un documento por lección) o dict; `last_choice=None` lee
  `export.last_choice` de cada pregunta (excepción documentada).
- Clave JSON oficial `lectura` (`{"cubrir": [...]}`) → `p.lectura`;
  `ProblemaTipo(..., lectura=)`, `save_problema` y `problema_to_python` la
  conservan. `lint` regla 10 (`lectura`): var ausente del `setup` o
  `cubrir` sin `setup` ERROR; valores reales o > 24 combinaciones AVISO.
- Plantilla: `scripts/gen_lectura.py` y `make lectura [LECCION=N]` →
  `build/lectura/L-NN-lectura.pdf` (preámbulo `config.PREAMBULO_AMC` o
  `PREAMBULO_LECTURA`; `config.EXTRAS_LECTURA` sorteos extra sin `cubrir`).

### Comprobación automática (`lint`)

```python
avisos = lint(problema_o_ruta, instances=None, seed=None)   # -> list[Aviso]
print(tabla_mundos(problema_o_ruta))                         # Cuestion × mundo
```

CLI: `python -m qbank.lint preguntas/*.json [--instances N] [--seed S] [--tabla] [--quiet]`
(también `qbank-lint`). Código de salida 1 si hay algún `ERROR`. `--quiet`
omite los INFO y los ficheros sin avisos.

Implementación en `src/qbank/_lint.py` (el docstring lista las 9 reglas y
sus códigos). Niveles: `ERROR` (la pregunta está rota: `mezcla`, `negacion`
sin `unoDe`, `interp` —`@{var}` sin resolver—, `estructura`, `nombre`,
`tipo`, `carga`, `ejecucion` —el `setup` lanza—, `variantes` —ninguna
variante válida—, `texto` —`%` sin barra—), `AVISO` (revisar: pocas
variantes, `pocas-opciones`, `opciones`, `constante`, `lista-1`,
`seed`/`instances` incoherentes, `negacion` de un Supuesto fijo, `solape`,
`huerfana`, `texto` sospechoso —comillas rectas, `\(…\)`, `\[…\]`, `\%` en
`$…$`…—), `INFO` (`setup` —instancias necesarias—, `variantes` —más de ~300—,
`constante` de literales o de lambdas con `setup`, `huerfana` con lambdas).

- La regla de negación considera deducible `-v('X')` si hay `unoDe(...)`
  con `v('X')` en un `Supuesto` suelto **o** si algún `Supuesto` afirma
  directamente `-v('X')` (patrón habitual: dos alternativas `v('X')` /
  `-v('X')`).
- Una `Cuestion` con `semantica` literal `True`/`False` constante en todos
  sus mundos es INFO, no AVISO (es un distractor deliberado).
- `pocas-opciones` (AVISO): una parte muestra al alumno menos de
  `MIN_OPCIONES` (3) opciones, contando `last_choice`. Detecta el error
  típico de poner las opciones en una única lista de `Cuestion` (una lista
  sortea una). No salta en ninguna pregunta de los dos bancos. Una parte sin
  ninguna `Cuestion` (texto suelto tras la última) da solo AVISO `opciones`
  (sin los `mezcla` de esa parte).
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

- **`Demo.ipynb`** — demostración interactiva que usa los mismos
  JSONs de `ejemplosManual/`.

Los tres deben funcionar en MyBinder tras cada release.

**Los tres se generan con `tools/cuadernos/gen_*.py`** (`comun.py` tiene el
ayudante de impresión `muestra()` común y la clase `Cuaderno`); editar el
guion, no el `.ipynb`. `sh tools/cuadernos/regenera.sh [--ejecuta]` los
reescribe (sin salidas, kernel `qbank`) y, con `--ejecuta`, los ejecuta con
`nbconvert` para comprobar que no fallan.

## Publicar una nueva versión

1. Incrementar `version` en `pyproject.toml`.
2. Commit + `git tag vX.Y.Z && git push && git push --tags`.
3. `rm -rf dist && .venv/bin/python -m build && .venv/bin/twine check dist/* && .venv/bin/twine upload dist/*`
   (borrar `dist/` antes: si quedan ficheros de versiones anteriores, `twine`
   intentaría subirlos también). Usar el `twine` del `.venv`: el del sistema
   (4.0) no entiende el Metadata-Version 2.4 de hatchling y da un falso
   «missing required fields: Name, Version».
4. Añadir `numpy` (y cualquier dependencia nueva) a `binder/requirements.txt`
   para forzar rebuild de la imagen MyBinder.
5. Verificar que los tres notebooks arrancan en MyBinder.
5b. Regenerar los PDF si cambiaron los `.org`, después `sh tools/web.sh`,
    commit y push de `docs/` (Pages publica desde `main`), y crear la release:
    `gh release create vX.Y.Z --title "qbank X.Y.Z" --notes "…"`.
6. Actualizar el entorno del banco de econometría:
   `pip install -e /ruta/a/qbank` (o `pip install calcprop-qbank==X.Y.Z`).

## Banco de econometría

El repo usuario principal de qbank está en
`~/SynologyDrive/ReposGH/Docencia/qbank-econometria` (su CLAUDE.md tiene
detalles de uso, campo `export`, regla de `instances`, etc.).
