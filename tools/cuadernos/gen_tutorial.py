import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import AYUDANTE, Cuaderno

nb = Cuaderno("tut")
md, code = nb.md, nb.code

md(r"""
# Tutorial de `qbank`: ejemplos progresivos

Este cuaderno recorre cinco preguntas de `ejemplosManual/`, cada una con una mecánica
nueva sobre la anterior, y termina comprobándolas con `lint` y exportándolas a AMC y
Moodle. Ejecuta las celdas en orden (desde la carpeta raíz del repositorio; en MyBinder
ya está todo preparado).

**El flujo de trabajo que se practica aquí** es el mismo que seguirás en tu banco:

1. Escribir la pregunta, en un fichero JSON o como lista de Python (al final se ve que son equivalentes).
2. Cargarla con `load_problema` y mirar sus variantes: `por_partes()` es lo que ve el alumno,
   `por_partes_profe()` es la *vista profe* (todas las cuestiones con sus marcas).
3. Pasarle `lint`.
4. Exportarla a AMC (papel) o Moodle.

Para crear un banco de verdad, con `Makefile` y scripts, el siguiente paso es `qbank-init`
(ver el README); para diseñar buenas preguntas, `GuiaDiseno.org`. El recorrido por la API
de Python (construir preguntas en Python, editor visual, exportadores) está en
`ejemplosManual/Demo.ipynb`.

## Cuatro palabras y una advertencia

- **Variante**: cada versión concreta de la pregunta (enunciado + opciones + marcas) que verá un alumno.
- **Mundo**: las hipótesis activas en una variante, es decir, las fórmulas de los `Supuesto` sorteados (más los axiomas, `Supuesto` sin texto que valen siempre); cada `Cuestion` es correcta si se deduce de ellas.
- **Hueco**: cada posición que se convierte en una opción: una `Cuestion` suelta, o una lista de `Cuestion` de la que se sortea *una*.
- **Opción por defecto**: la que añade `"export": {"last_choice": true}` («Ninguna de las anteriores»); es correcta solo si las demás son falsas, y garantiza que nunca sean todas correctas ni todas falsas.

> **La advertencia que ahorra más disgustos:** una *lista* de `Cuestion` **no** son «las opciones que
> se muestran juntas». De una lista se sortea **una** por variante. El alumno ve tantas opciones
> como **huecos** haya (elementos-`Cuestion` consecutivos, sueltos o listas), más la opción por
> defecto. El patrón recomendado: tres huecos + `last_choice`.

La celda siguiente carga `qbank` y define `muestra`, un ayudante que imprime las variantes
(o la vista profe) con sus marcas y, si la pregunta la lleva, la opción por defecto. Es el
mismo en los tres cuadernos.
""")

code(r'''
from qbank import load_problema, lint, tabla_mundos
''' + AYUDANTE)

md(r"""
---
## Ejemplo A — valores de verdad literales, tres huecos (`ej_a_literales.json`)

La forma más simple de `ProblemaTipo`: sin `setup`, sin hipótesis. Cada `Cuestion` lleva
`"semantica": "True"` o `"False"`. Hay un texto fijo y **tres huecos**, cada uno una lista
de cinco cuestiones de la que se sortea una: $5 \times 5 \times 5 = 125$ variantes, cada una
con tres opciones (más la opción por defecto, porque `export.last_choice` es `true`).

```json
{
  "version": "1", "tipo": "ProblemaTipo", "nombre": "ej_a_literales",
  "setup": null,
  "export": {"last_choice": true, "cols": 2},
  "componentes": [
    "Sea $n$ un número par y $m$ un número impar.",
    [ {"tipo": "Cuestion", "enunciado": "$n+m$ es par",   "semantica": "False", "precond": "True", "exp": ""},
      {"tipo": "Cuestion", "enunciado": "$n+m$ es impar", "semantica": "True",  "precond": "True", "exp": ""},
      ... ],
    [ ... ],
    [ ... ]
  ]
}
```

Los campos de nivel superior: `nombre` (igual que el fichero, sin `.json`), `setup`
(código Python o `null`), `export` (`last_choice`, `cols` para AMC —aquí dos columnas—,
`instances` con `setup` aleatorio) y `componentes`, la lista plana de textos, `Supuesto`
y `Cuestion`.
""")

code(r'''
p_a = load_problema("ejemplosManual/ej_a_literales.json")
print(f"{len(list(p_a.por_partes()))} variantes")
muestra(p_a, n=2)
''')

md(r"""
---
## Ejemplo B — una lista de `Supuesto`: dos mundos (`ej_b_mundos.json`)

Una lista de `Supuesto` crea **mundos alternativos**: en cada variante se sortea uno, su
texto entra en el enunciado y su fórmula pasa a ser hipótesis. La `semantica` de cada
`Cuestion` es ahora una fórmula con esas etiquetas: `"v('crec')"` es correcta en el mundo
«creciente» e incorrecta en el «decreciente».

```json
[
  {"tipo": "Supuesto", "enunciado": "estrictamente creciente,",
   "semantica": "v('crec')", "precond": "True"},
  {"tipo": "Supuesto", "enunciado": "estrictamente decreciente,",
   "semantica": "v('decr')", "precond": "True"}
]
```

Las etiquetas `v('crec')`, `v('decr')` las eliges tú; solo tienen que ser consistentes
dentro de la pregunta. El número de variantes es (nº de mundos) × (combinaciones de los
huecos) = 2 × 3 × 3 × 4 = 72.
""")

code(r'''
p_b = load_problema("ejemplosManual/ej_b_mundos.json")
print(f"{len(list(p_b.por_partes()))} variantes")
muestra(p_b, n=2)
''')

md(r"""
### La vista profe (`por_partes_profe`)

`por_partes_profe()` muestra, para cada mundo, **todas** las cuestiones de cada hueco —no solo
la sorteada— con sus marcas. Es lo que conviene repasar antes de dar una pregunta por buena
(en un banco creado con `qbank-init`, `make amc` la imprime en PDF). Aquí la opción por
defecto se lista al final de cada mundo marcada `[+]`, aunque su valor depende de qué opciones
se sorteen en cada variante; el PDF de `make amc` no la incluye (se comprueba en las variantes
de `make amc-student`).
""")

code(r'''
muestra(p_b, n=2, profe=True)
''')

md(r"""
---
## Ejemplo C — axioma y `precond` por mundo (`ej_c_precond.json`)

Un `Supuesto` suelto con `"enunciado": ""` es un **axioma**: añade su fórmula en todas las
variantes sin aportar texto. Aquí declara que los dos mundos son excluyentes,
`unoDe(v('inv'), v('sing'))`: sin él, de «invertible» no se deduciría «no singular».

Las cuestiones usan `precond` para **aparecer solo en el mundo donde tienen sentido**:
`"precond": "v('inv')"` hace que la cuestión no se sortee en el mundo `sing` (y la
variante que la hubiera sorteado se descarta). En la vista profe aparecen marcadas con
`[·]` y el motivo (`rechazada por …`).

```json
{"tipo": "Cuestion", "enunciado": "$\\det(A) \\neq 0$",
 "semantica": "True", "precond": "v('inv')", "exp": ""}
```

**Diferencia con B:** en B todas las cuestiones aparecen en todos los mundos (solo cambia
su marca). En C algunas cuestiones no aparecen en ciertos mundos, y por eso hay menos
variantes que combinaciones.
""")

code(r'''
p_c = load_problema("ejemplosManual/ej_c_precond.json")
print(f"{len(list(p_c.por_partes()))} variantes")
muestra(p_c, n=2, profe=True)
''')

md(r"""
---
## Ejemplo D — `setup` e interpolación `@{var}` (`ej_d_setup_vars.json`)

El campo `setup` es código Python (una cadena en el JSON) que se ejecuta antes de cada
variante. Sus variables se interpolan en los textos con `@{nombre}`:

```python
# setup del problema
import numpy as np
a = int(np.random.randint(1, 8))
b = int(a + np.random.randint(1, 6))
```

```json
{"enunciado": "$f(@{a}) < f(@{b})$", "semantica": "v('crec')",
 "exp": "Como $@{a} < @{b}$: si $f$ es estrictamente creciente, $f(@{a}) < f(@{b})$; si es estrictamente decreciente, $f(@{a}) > f(@{b})$."}
```

La marca sigue siendo proposicional (depende del mundo), pero el enunciado muestra los
valores concretos. Cuatro detalles:

- El `setup` se ejecuta **en cada variante**: cada combinación de mundo y huecos sale con sus
  propios números.
- `seed` (nivel superior del JSON) hace reproducible la pregunta: siembra `numpy.random` y
  `random`. Usa `np.random`, porque los scripts de la vista profe solo siembran numpy.
- `export.instances = N` repite el recorrido completo de combinaciones $N$ veces, con
  semillas distintas: multiplica por $N$ las variantes (objetivo: al menos 60; `lint`
  calcula cuántas instancias hacen falta). Aquí, 54 combinaciones × 2 instancias = 108.
- `exp` admite la misma interpolación: una sola explicación sirve para todas las variantes. Desde
  JSON no se evalúan lambdas en `exp`; si el texto depende de una condición, calcúlalo en `setup`
  como variable y usa `@{esa_variable}`.

Las funciones de `qbank` no leen `export` por su cuenta (los scripts de un banco sí): por eso
la celda pasa `instances=` con el valor del JSON.
""")

code(r'''
p_d = load_problema("ejemplosManual/ej_d_setup_vars.json")
n_inst = p_d.export.get("instances", 1)
print(f"{len(list(p_d.por_partes(instances=n_inst)))} variantes con instances={n_inst}")
muestra(p_d, n=3, instances=n_inst)
''')

md(r"""
---
## Ejemplo E — semántica `lambda` (`ej_e_lambda.json`)

Cuando la marca **depende de los números del `setup`** y no de un mundo sorteado, la
`semantica` (o la `precond`) es una `lambda` que recibe `ns`, el diccionario del `setup`,
y devuelve `True`/`False`… o una fórmula. Aquí el `setup` calcula fórmulas según el valor
de `x` y un `Supuesto` axioma las inyecta como hipótesis:

```python
# setup
import numpy as np
from calcprop import v
x = int(np.random.randint(0, 11))
sup_u1 = v('gt_u1') if x > 3 else -v('gt_u1')
sup_u2 = v('gt_u2') if x > 7 else -v('gt_u2')
```

```json
{"tipo": "Supuesto", "enunciado": "", "semantica": "lambda ns: ns['sup_u1'] & ns['sup_u2']", "precond": "True"}
```

Dos axiomas más (`v('gt_u2') >> v('gt_u1')` y su contrarrecíproco) dan al motor la
relación entre los umbrales, y las cuestiones usan fórmulas normales. La forma más
sencilla de lambda es la directa, `"semantica": "lambda ns: ns['x'] > 3"`; esta variante
inyectada es útil cuando varias cuestiones comparten la misma lógica.

**Diferencia con D:** en D los números solo aparecen en el texto; en E también deciden la marca.

Como no hay listas que sortear, cada instancia da una sola variante. La celda muestra 12;
el JSON pide 60 para llegar al objetivo de `lint`, pero `x` solo puede tomar 11 valores,
así que muchas instancias repiten la misma variante: con pocos valores posibles, subir
`instances` no da más preguntas distintas.
""")

code(r'''
p_e = load_problema("ejemplosManual/ej_e_lambda.json")
print("x  | x>3  x>7  x≤3  3<x≤7")
for etiqueta, partes in p_e.por_partes(instances=12):
    enunciado, cuestiones = partes[0]
    x_val = enunciado.split("$x = ")[1].split("$")[0]
    marcas = "    ".join("✓" if vf else "✗" for _, vf, *_ in cuestiones)
    print(f"{x_val:>2} |  {marcas}")
''')

md(r"""
---
## La misma pregunta como lista de Python

El JSON es el formato en que se guardan las preguntas (es lo que leen `lint` y los scripts
de un banco), pero puedes *escribirlas* en Python, que se lee mejor: `v('crec')` sin
comillas, cadenas crudas `r"..."` sin doblar barras. `problema_to_python` muestra la
traducción del Ejemplo B; `save_problema` hace el camino inverso (de Python a JSON). La
comprobación de que el guion reconstruye exactamente la misma pregunta está en
`ejemplosManual/Demo.ipynb` (sección 7). En un banco creado con `qbank-init`,
`nueva_pregunta.py` es la plantilla para este camino.
""")

code(r'''
from qbank import problema_to_python

print(problema_to_python(p_b))
''')

md(r"""
---
## Probar una pregunta sin escribirla a disco

`load_problema` también acepta un `dict`: útil para probar una idea en el cuaderno. Esta
pregunta sigue el patrón recomendado: tres huecos (cada uno con una verdadera y su
«gemela» falsa) y la opción por defecto. Solo tiene $2 \times 2 \times 2 = 8$ variantes, y
`lint` lo avisa.
""")

code(r'''
d = {
    "version": "1", "tipo": "ProblemaTipo", "nombre": "prueba_rapida",
    "setup": None,
    "export": {"last_choice": True},
    "componentes": [
        "Sea $p$ un número primo mayor que 2. Entonces:",
        [{"tipo": "Cuestion", "enunciado": "$p$ es impar", "semantica": "True",  "precond": "True", "exp": ""},
         {"tipo": "Cuestion", "enunciado": "$p$ es par",   "semantica": "False", "precond": "True", "exp": ""}],
        [{"tipo": "Cuestion", "enunciado": "$p$ tiene exactamente dos divisores positivos", "semantica": "True",  "precond": "True", "exp": ""},
         {"tipo": "Cuestion", "enunciado": "$p$ tiene exactamente un divisor positivo",     "semantica": "False", "precond": "True", "exp": ""}],
        [{"tipo": "Cuestion", "enunciado": "$p + 1$ es par",   "semantica": "True",  "precond": "True", "exp": ""},
         {"tipo": "Cuestion", "enunciado": "$p + 1$ es primo", "semantica": "False", "precond": "True", "exp": ""}],
    ],
}
p_dict = load_problema(d)
print(f"{len(list(p_dict.por_partes()))} variantes")
muestra(p_dict, n=2)

for a in lint(p_dict):
    print(a)
''')

md(r"""
---
## Comprobación automática (`lint`)

Antes de exportar, `lint` revisa una pregunta (objeto, `dict` o ruta a un JSON) y devuelve
avisos de tres niveles: `ERROR` (la pregunta está rota: alguna variante con todas las opciones
correctas o todas falsas, una negación que nunca se deduce, un `@{var}` sin resolver, un `%`
sin barra…), `AVISO` (hay que leerlo y decidir: pocas variantes, un distractor constante, una
lista de un elemento…) e `INFO`. `tabla_mundos` muestra el valor de cada `Cuestion` en cada
mundo (`V`, `F`, o `-` si la rechaza su `precond`): la forma más rápida de auditar la lógica.

Desde la terminal, sobre todos los ejemplos: `python -m qbank.lint ejemplosManual/*.json --quiet`
(en un banco, `make lint`).
""")

code(r'''
for ruta in ["ejemplosManual/ej_c_precond.json", "ejemplosManual/ej_d_setup_vars.json"]:
    avisos = lint(ruta)
    print(f"── {ruta}: {len(avisos)} aviso(s) ──")
    for a in avisos:
        print("  ", a)
    print()

print("── tabla_mundos de ej_c_precond.json ──")
print(tabla_mundos("ejemplosManual/ej_c_precond.json"))
''')

md(r"""
### Una pregunta rota a propósito

El error típico de la advertencia del principio: poner las tres afirmaciones en **una sola
lista**. De la lista se sortea una, así que el alumno ve una afirmación más la opción por
defecto, dos opciones en total; `lint` lo detecta (`pocas-opciones`) y, de paso, avisa de
que solo hay tres variantes.
""")

code(r'''
rota = {
    "version": "1", "tipo": "ProblemaTipo", "nombre": "rota",
    "setup": None,
    "export": {"last_choice": True},
    "componentes": [
        "Sea $p$ un número primo mayor que 2. Entonces:",
        [   # UNA sola lista: se sortea una de las tres en cada variante
            {"tipo": "Cuestion", "enunciado": "$p$ es impar", "semantica": "True", "precond": "True", "exp": ""},
            {"tipo": "Cuestion", "enunciado": "$p$ tiene exactamente dos divisores positivos", "semantica": "True", "precond": "True", "exp": ""},
            {"tipo": "Cuestion", "enunciado": "$p + 1$ es par", "semantica": "True", "precond": "True", "exp": ""},
        ],
    ],
}
muestra(load_problema(rota), n=1)
print("── lint de la pregunta rota ──")
for a in lint(rota):
    print("  ", a)
''')

md(r"""
---
## Exportar a AMC y Moodle

Con la pregunta revisada, se exporta. `AMCblock` devuelve el bloque LaTeX de una variante
(los scripts de un banco los escriben todos en un `.tex`); `QuizMoodle` escribe un `.tex`
completo que, compilado con `xelatex`, produce un PDF de revisión y el `-moodle.xml`
importable en Moodle. (Con `pdflatex` el XML sale declarado en `iso-8859-1` y Moodle
mostraría `Â¿`; los proyectos de `qbank-init` usan `pdflatex` y lo corrigen después.) En
un banco creado con `qbank-init` todo esto lo hacen `make amc`, `make amc-student` y
`make moodle`.
""")

code(r'''
import os
from qbank import AMCblock, QuizMoodle

os.makedirs("ejemplosManual/exportaciones", exist_ok=True)

# AMC: el bloque LaTeX de la primera variante del Ejemplo B, con la opción por defecto
etiqueta, partes = next(iter(p_b.por_partes()))
enunciado, cuestiones = partes[0]
print(AMCblock("EjemploB", etiqueta, enunciado, cuestiones, last_choice=True))
''')

code(r'''
# Moodle: el .tex con todas las variantes (después: xelatex EjemploB.tex → EjemploB-moodle.xml)
n = QuizMoodle("EjemploB", "ejemplosManual/exportaciones/", p_b, last_choice=True)
print(f"{n} variantes escritas en ejemplosManual/exportaciones/EjemploB.tex")
''')

md(r"""
---
## Siguiente paso

- `qbank-init mi-banco` crea un proyecto con cinco preguntas de ejemplo, `make lint`, `make amc`,
  `make amc-student` y `make moodle`; su `README.org` explica el flujo completo.
- `GuiaDiseno.org` explica cómo diseñar buenas preguntas (mundos, huecos, `setup`, redacción,
  explicaciones, trampas de LaTeX y Moodle).
- `ejemplosManual/Demo.ipynb` recorre la API de Python: construir preguntas en Python,
  guardarlas, el editor visual y los exportadores.
- `Manual.org` es la referencia completa de la API y del formato JSON.
""")

nb.write("Tutorial.ipynb")
