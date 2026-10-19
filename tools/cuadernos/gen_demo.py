import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import AYUDANTE, Cuaderno

nb = Cuaderno("demo")
md, code = nb.md, nb.code

md(r"""
# qbank — recorrido por la API de Python

`qbank` genera variantes de preguntas de opción múltiple cuyas respuestas correctas se
determinan automáticamente mediante lógica proposicional. Este cuaderno recorre la API
*desde Python*: construir preguntas como listas de `Supuesto` y `Cuestion`, revisarlas,
guardarlas en JSON, el editor visual y los exportadores. Es complementario de
`Tutorial.ipynb` (los ejemplos progresivos, en JSON) y de `GuiaDiseno.org` (cómo diseñar
buenas preguntas). Ejecuta las celdas en orden con **Shift+Enter**, desde la carpeta
`ejemplosManual/`.

**Contenidos:**
1. [Bloque básico: `ProblemaTipo`](#1)
2. [Vista profe: `por_partes_profe()`](#2)
3. [Preguntas paramétricas con `setup`](#3)
4. [Comprobación: `lint` y `tabla_mundos`](#4)
5. [Persistencia en JSON](#5)
6. [Banco de múltiples problemas](#6)
7. [Conversiones entre formatos](#7)
8. [Editor visual](#8)
9. [Preguntas con varias partes](#9)
10. [Exportar a AMC (LaTeX)](#10)
11. [Exportar a Moodle (vía LaTeX)](#11)
12. [Apéndice: verdadero/falso con `ProblemaVF`](#12)
""")

md(r"""
La celda siguiente carga `qbank` y define `muestra`, un ayudante que imprime las variantes
(o la vista profe) con sus marcas y, si la pregunta la lleva, la opción por defecto. Es el
mismo en los tres cuadernos.
""")

code(r'''
from qbank import *
import os
''' + AYUDANTE)

md(r"""
<a id="1"></a>
## 1. Bloque básico: `ProblemaTipo`

Un `ProblemaTipo` es una lista plana de componentes:
- **Cadenas de texto**: aparecen en todas las variantes.
- **`Supuesto`** (sueltos o en lista): hipótesis. Una *lista* de `Supuesto` son mundos
  alternativos: se sortea uno por variante y su fórmula pasa a ser hipótesis.
- **`Cuestion`** (sueltas o en lista): opciones de respuesta. Cada elemento-`Cuestion`
  consecutivo es un **hueco** (una opción que ve el alumno); de una *lista* se sortea una.

Patrón recomendado: tres huecos + `export={"last_choice": True}`, que añade la opción
«Ninguna de las anteriores» (correcta solo si las demás son falsas).

El ejemplo sigue ese patrón: un `Supuesto` suelto ($\mathcal{B}$ es verdadero, en todas las
variantes), dos mundos ($\mathcal{A}$ verdadero o falso) y tres huecos de dos cuestiones,
todas con una marca que cambia de un mundo a otro: $2 \times 2 \times 2 \times 2 = 16$
variantes. Las cadenas con LaTeX van con `r"..."` para no doblar las barras.

**Operadores lógicos** (variables con `v('nombre')`):

| Operador | Significado |
|----------|-------------|
| `v('A')` | variable proposicional A |
| `-v('A')` | negación de A |
| `v('A') & v('B')` | A y B |
| `v('A') \| v('B')` | A o B |
| `v('A') >> v('B')` | si A entonces B |
| `v('A') ** v('B')` | A si y solo si B (equivalencia) |
| `alguno(v('A'), v('B'), v('C'))` | alguna de la lista es verdadera |
| `unoDe(v('A'), v('B'), v('C'))` | exactamente una de la lista es verdadera |
| `True` / `False` | siempre verdadero / siempre falso |
""")

code(r'''
p = ProblemaTipo(
    [
        Supuesto(r"Sabiendo que $\mathcal{B}$ es verdadero", v('B')),   # suelto: en todas las variantes
        r" y que $\mathcal{A}$ es ",
        [   # mundos: se sortea uno
            Supuesto("verdadero,", v('A')),
            Supuesto("falso,", -v('A')),
        ],
        " indique qué afirmaciones son correctas:",
        [   # hueco 1
            Cuestion(r"$\mathcal{A}$ es verdadero", v('A')),
            Cuestion(r"$\mathcal{A}$ es falso", -v('A')),
        ],
        [   # hueco 2
            Cuestion(r"$\mathcal{A}$ y $\mathcal{B}$ son verdaderos", v('A') & v('B')),
            Cuestion(r"$\mathcal{A}$ y $\mathcal{B}$ tienen el mismo valor de verdad", v('A') ** v('B')),
        ],
        [   # hueco 3
            Cuestion(r"$\mathcal{A}$ es falso y $\mathcal{B}$ es verdadero", -v('A') & v('B')),
            Cuestion(r"si $\mathcal{B}$ es verdadero, también lo es $\mathcal{A}$", v('B') >> v('A')),
        ],
    ],
    export={"last_choice": True, "cols": 2},
    nombre="basico",
)

print(len(list(p.por_partes())), "variantes")
muestra(p, n=4)
''')

md(r"""
<a id="2"></a>
## 2. Vista profe: `por_partes_profe()`

`por_partes_profe()` recorre los mismos mundos que `por_partes()`, pero muestra **todas**
las cuestiones de cada hueco (no una por variante). Es lo que conviene revisar antes de
exportar (en un banco creado con `qbank-init`, `make amc` la imprime en PDF).

Devuelve `(etiqueta, [(enunciado, cuestiones), ...])`, un par por parte (aquí una sola).
Cada cuestión es `(texto, marca, activa, exp)`. Si una cuestión tiene una `precond` que
no se cumple en ese mundo, en vez de descartar la variante la vista profe la incluye con
`activa = 0` y la marca `'rechazada por …'`; `muestra` la imprime como `[·]`. Esta pregunta
no tiene `precond`, así que no aparece ninguna: hay ejemplos en el Ejemplo C del
`Tutorial.ipynb` y en `Ejemplos.ipynb`. La opción por defecto sale al final, marcada `[+]`,
porque su valor depende de qué cuestiones se sorteen en cada variante.
""")

code(r'''
muestra(p, n=2, profe=True)
''')

md(r"""
<a id="3"></a>
## 3. Preguntas paramétricas con `setup`

`setup` es código Python (una cadena) que se ejecuta antes de cada variante; sus variables
se interpolan en los textos con `@{variable}` y están en `ns` para las semánticas y
precondiciones escritas como `lambda`. Escribe el `setup` y las lambdas **como cadenas**:
es lo que guarda el JSON (una función Python no se puede serializar).

- `seed` hace reproducible la pregunta: siembra `numpy.random` y `random`. Usa `np.random`,
  porque los scripts de la vista profe solo siembran numpy.
- Como el `setup` se ejecuta en cada variante, cada combinación de huecos sale con sus
  propios números. `instances=N` repite el recorrido completo de combinaciones $N$ veces,
  con semillas distintas: aquí, 4 combinaciones × 15 instancias = 60 variantes.
- Las funciones de `qbank` no leen `export` por su cuenta (los scripts de un banco sí):
  hay que pasarles `instances=`, `last_choice=`, `cols=`.
""")

code(r'''
p_param = ProblemaTipo(
    [
        "Sean $a = @{a}$ y $b = @{b}$. Entonces:",
        [
            Cuestion("$a + b = @{suma}$", True),
            Cuestion("$a + b = @{suma_falsa}$", False, exp="Porque $@{a} + @{b} = @{suma}$."),
        ],
        [
            Cuestion("$a + b > 10$", "lambda ns: ns['a'] + ns['b'] > 10"),
            Cuestion("$a + b < 10$", "lambda ns: ns['a'] + ns['b'] < 10"),
        ],
        Cuestion("$a \\cdot b = @{producto}$", True),
    ],
    setup="import numpy as np\n"
          "a, b = (int(x) for x in np.random.randint(1, 10, 2))\n"
          "suma, suma_falsa, producto = a + b, a + b + 1, a * b",
    seed=1,
    export={"last_choice": True, "instances": 15},
    nombre="parametrica",
)

n_inst = p_param.export["instances"]
print(len(list(p_param.por_partes(instances=n_inst))), f"variantes con instances={n_inst}")
muestra(p_param, n=3, instances=n_inst)
''')

md(r"""
<a id="4"></a>
## 4. Comprobación: `lint` y `tabla_mundos`

`lint` devuelve avisos con nivel `ERROR` (la pregunta está rota), `AVISO` (hay que
leerlo y decidir) e `INFO`. `tabla_mundos` muestra el valor de cada `Cuestion` en cada
mundo. Las dos preguntas de arriba pasan `lint` sin `ERROR` ni `AVISO` (como mucho algún
`INFO`, que no pide nada). Una pregunta rota a propósito, con lo que dice `lint` de ella,
está al final del `Tutorial.ipynb`.
""")

code(r'''
for q in (p, p_param):
    avisos = lint(q)
    print(f"── {problema_to_dict(q)['nombre']}: {len(avisos)} aviso(s) ──")
    for a in avisos:
        print("  ", a)
print()
print(tabla_mundos(p))
''')

md(r"""
<a id="5"></a>
## 5. Persistencia en JSON

`save_problema` y `load_problema` guardan y recuperan un problema en formato JSON sin
perder información (incluidos `setup` y lambdas escritos como cadenas, `seed`, `export`
y `nombre`). El JSON es el formato de las preguntas de un banco.
""")

code(r'''
os.makedirs("mis_problemas", exist_ok=True)

save_problema(p_param, "mis_problemas/parametrica.json")
p2 = load_problema("mis_problemas/parametrica.json")
assert problema_to_dict(p2) == problema_to_dict(p_param)
print("Guardado y recuperado sin pérdida:", len(list(p2.por_partes(instances=15))), "variantes")
''')

md(r"""
<a id="6"></a>
## 6. Banco de múltiples problemas

`save_banco` y `load_banco` agrupan varios problemas en un único fichero JSON. Los
proyectos creados con `qbank-init` usan en cambio un fichero por pregunta (más cómodo
con `make` y con el control de versiones).
""")

code(r'''
save_banco([p, p_param], "mis_problemas/banco.json")
problemas = load_banco("mis_problemas/banco.json")
print(f"Cargados {len(problemas)} problemas:", [problema_to_dict(q)["nombre"] for q in problemas])
''')

md(r"""
<a id="7"></a>
## 7. Conversiones entre formatos

`qbank` usa el diccionario JSON como formato pivote. Desde cualquier representación
puedes obtener cualquier otra:

```
Lista de listas Python
      ↕  problema_to_dict() / problema_from_dict()
   Dict JSON  ←→  fichero .json  (save_problema / load_problema)
      ↓  problema_to_python()
  Código Python editable (.py)   →  ejecutable, y de vuelta con save_problema
```
""")

code(r'''
import json

d = problema_to_dict(p)
print(json.dumps(d, ensure_ascii=False, indent=2)[:900], "…")
''')

code(r'''
codigo = problema_to_python(p_param)
print(codigo)
save_problema_py(p_param, "mis_problemas/parametrica.py")

ns = {}
exec(codigo, ns)                                    # define p
assert problema_to_dict(ns["p"]) == problema_to_dict(p_param)
print("El guion Python reconstruye la misma pregunta.")
''')

md(r"""
<a id="8"></a>
## 8. Editor visual

`ProblemaTipoEditor` es un formulario interactivo para diseñar problemas sin escribir
la lista de listas a mano. Requiere `ipywidgets` (`pip install "calcprop-qbank[jupyter]"`).
La cabecera tiene `Nombre:`, `Setup:` con su `semilla:`, y `Export:` con la casilla
`last_choice` y `cols:`. Debajo va la lista de componentes, una fila por elemento con
sus alternativas. El editor llama «Hueco N» a cada fila, sea del tipo que sea (`texto`,
`supuestos` o `cuestiones`); en el resto del cuaderno, un hueco es solo una fila de
cuestiones, la que da una opción al alumno.

| Botón | Acción |
|-------|--------|
| **+ hueco** | añade una fila al final; **▲ ▼ ＋ ✕** suben, bajan, insertan debajo o borran un hueco |
| **+ alt** | añade una alternativa al hueco |
| **▶ Preview** | muestra las primeras *n* variantes (con la casilla *vista profe*, todas las cuestiones) |
| **{ } JSON** / **</> .py** | muestra el JSON o el guion Python equivalente |
| **💾 Guardar** / **📂 Cargar** | escribe o lee el JSON del fichero indicado |
| **⬇ .json** / **⬇ .py** | descarga directamente al navegador |

> **Nota**: si el editor muestra texto en lugar del formulario (`VBox(children=...`),
> la extensión de widgets de JupyterLab no está activa; el apéndice del Manual dice cómo
> activarla. En MyBinder funciona directamente.

### 8.1 Editor vacío
""")

code(r'''
from qbank import ProblemaTipoEditor

editor = ProblemaTipoEditor()
''')

md(r"""
### 8.2 Editor cargando un ejemplo con `setup`

Se carga `numeros.json`: el campo **Setup** muestra el código que sortea dos números y
calcula su suma y su producto (y una suma y un producto falsos, para las parejas V/F).
Cada supuesto (`$a>b$`, `$a<b$`, `$a=b$`, `$a\ne b$`) lleva una **precondición** sobre los
números sorteados (`lambda ns: ns['a'] > ns['b']`, …), de modo que el enunciado nunca
afirma algo falso sobre los números mostrados.

La pregunta tiene **dos huecos** (de cuatro y tres alternativas) y la opción por
defecto: el alumno ve tres opciones. La **previsualización** con *vista profe* muestra,
para cada mundo, todas las cuestiones marcadas; cuando el sorteo no cumple la
precondición de un supuesto, esa variante no aparece.
""")

code(r'''
editor_numeros = ProblemaTipoEditor('numeros.json')
''')

code(r'''
# `to_problema()` devuelve el ProblemaTipo con el estado actual del formulario;
# `to_dict()` el JSON (conservando seed, export y las claves que el formulario no edita).
print(problema_to_python(editor_numeros.to_problema())[:600], "…")
''')

md(r"""
<a id="9"></a>
## 9. Preguntas con varias partes

Cuando tras un bloque de cuestiones vuelve a aparecer texto o un `Supuesto`, se abre
una **parte** nueva: una pregunta con varios bloques de opciones bajo un enunciado común.
`por_partes()` devuelve un par `(enunciado, cuestiones)` por parte, y las hipótesis se
acumulan a lo largo de las partes. (`ProblemaMultiParte` y `SubPregunta` siguen
disponibles pero están deprecados: devuelven un `ProblemaTipo` equivalente.)

### 9.1 Ejemplo de álgebra lineal

Dos mundos (el segundo afirma directamente `-v('SP')`, así que las cuestiones con esa
semántica se deducen sin axioma) y dos partes de dos huecos cada una, más la opción
por defecto en cada parte.
""")

code(r'''
# v('SP') representa el supuesto «A es simétrica definida positiva»
p_matriz = ProblemaTipo([
    "Sea $A$ una matriz cuadrada ",
    [
        Supuesto("simétrica y definida positiva. ", v('SP')),
        Supuesto("con un autovalor cero cuya multiplicidad algebraica supera a la geométrica. ", -v('SP')),
    ],
    "Con toda seguridad, $A$...",
    [
        Cuestion("es diagonalizable.", v('SP'),
                 exp="Las matrices s.d.p. son siempre diagonalizables (teorema espectral)."),
        Cuestion("no es diagonalizable.", -v('SP'),
                 exp="Si la multiplicidad algebraica supera a la geométrica, no es diagonalizable."),
    ],
    [
        Cuestion("tiene todos sus autovalores positivos.", v('SP'),
                 exp="Es la definición de definida positiva (para una matriz simétrica)."),
        Cuestion("tiene algún autovalor nulo.", -v('SP'),
                 exp="El enunciado lo dice: un autovalor cero."),
    ],
    "En cuanto a $A^T$, con toda seguridad...",
    [
        Cuestion("es invertible.", v('SP'), exp="$A$ s.d.p. implica $A^T = A$ invertible."),
        Cuestion("es singular.", -v('SP'),
                 exp="Autovalor cero $\\Rightarrow$ $\\det(A)=0$ $\\Rightarrow$ $\\det(A^T)=0$."),
    ],
    [
        Cuestion("es simétrica.", v('SP'), exp="$A$ simétrica implica $A^T = A$, simétrica."),
        Cuestion("tiene el mismo determinante que $A$.", True, exp="$\\det(A^T) = \\det(A)$ siempre."),
    ],
], export={"last_choice": True}, nombre="matriz")

muestra(p_matriz, n=2, profe=True)
print(len(list(p_matriz.por_partes())), "variantes")
for a in lint(p_matriz):
    print("  ", a)
''')

md(r"""
### 9.2 Editor visual con un ejercicio de varias partes

El editor también soporta ejercicios de varias partes. Se carga `superheroes.json`, un
ejemplo de tres partes sobre cuatro superhéroes (cuatro mundos).
""")

code(r'''
editor_superheroes = ProblemaTipoEditor('superheroes.json')
''')

md(r"""
### 9.3 Varias partes con `setup` numérico

El `setup` también funciona con varias partes. Aquí se sortean tres enteros y cada parte
evalúa un cálculo distinto con lambdas (como cadenas) sobre los valores del `setup`. Cada
parte sigue el patrón recomendado: tres huecos y la opción por defecto, que `muestra`
imprime en cada parte ($2^6 = 64$ variantes, cada una con sus propios números: no hacen
falta más instancias).
""")

code(r'''
p_numeros_multi = ProblemaTipo([
    "Sean $a = @{a}$, $b = @{b}$ y $c = @{c}$ números naturales.",
    r" El producto $a \cdot b$...",
    [   # hueco 1 de la parte 1
        Cuestion("vale $@{ab}$.", True),
        Cuestion("vale $@{ab_falso}$.", False, exp=r"$@{a} \cdot @{b} = @{ab}$."),
    ],
    [   # hueco 2
        Cuestion(r"es mayor que $b \cdot c = @{bc}$.", "lambda ns: ns['ab'] > ns['bc']"),
        Cuestion(r"es menor o igual que $b \cdot c = @{bc}$.", "lambda ns: ns['ab'] <= ns['bc']"),
    ],
    [   # hueco 3
        Cuestion("es par.", "lambda ns: ns['ab'] % 2 == 0"),
        Cuestion("es impar.", "lambda ns: ns['ab'] % 2 == 1"),
    ],
    " La suma $a + b + c$...",
    [   # hueco 1 de la parte 2
        Cuestion("vale $@{suma}$.", True),
        Cuestion("vale $@{suma_falsa}$.", False, exp="$@{a} + @{b} + @{c} = @{suma}$."),
    ],
    [   # hueco 2
        Cuestion(r"es mayor que $a \cdot b = @{ab}$.", "lambda ns: ns['suma'] > ns['ab']"),
        Cuestion(r"es menor o igual que $a \cdot b = @{ab}$.", "lambda ns: ns['suma'] <= ns['ab']"),
    ],
    [   # hueco 3
        Cuestion("es múltiplo de 3.", "lambda ns: ns['suma'] % 3 == 0"),
        Cuestion("no es múltiplo de 3.", "lambda ns: ns['suma'] % 3 != 0"),
    ],
], setup="import numpy as np\n"
         "a, b, c = (int(x) for x in np.random.randint(2, 10, 3))\n"
         "ab, bc, suma = a * b, b * c, a + b + c\n"
         "ab_falso, suma_falsa = ab + a, suma + 1",
   seed=3, export={"last_choice": True}, nombre="numeros_multi")
n_var = len(list(p_numeros_multi.por_partes()))
print(n_var, "variantes")
muestra(p_numeros_multi, n=2)
for a in lint(p_numeros_multi):
    print("  ", a)
''')

md(r"""
<a id="10"></a>
## 10. Exportar a AMC (LaTeX)

`AMCblock` genera el bloque LaTeX de una variante para **Auto Multiple Choice**; en un
banco, el fichero con todos los bloques se incluye en el examen con `\input` y
`\insertgroup[1]{grupo}` (el README de la plantilla de `qbank-init` da el procedimiento).
`last_choice=True` añade la opción por defecto (`\lastchoices`) y `cols=N` dispone las
opciones en N columnas. Para una pregunta de varias partes, `AMC_multipart` produce un
único `questionmult` con un bloque de casillas por parte.
""")

code(r'''
os.makedirs("exportaciones", exist_ok=True)

p_numeros = load_problema("numeros.json")       # el ejemplo de la sección 8.2
with open("exportaciones/numeros_amc.tex", "w") as f:
    for etiqueta, partes in p_numeros.por_partes(instances=p_numeros.export.get("instances", 1)):
        enunciado, cuestiones = partes[0]
        f.write(AMCblock("Numeros", etiqueta, enunciado, cuestiones,
                         last_choice=p_numeros.export.get("last_choice", False),
                         cols=p_numeros.export.get("cols", 1)))

with open("exportaciones/numeros_amc.tex") as f:
    print(f.read()[:700], "…")
''')

code(r'''
with open("exportaciones/matriz_amc.tex", "w") as f:
    for etiqueta, partes in p_matriz.por_partes():
        f.write(AMC_multipart("AlgebraLineal", etiqueta, "", partes, last_choice=True))

with open("exportaciones/matriz_amc.tex") as f:
    print(f.read()[:900], "…")
''')

md(r"""
<a id="11"></a>
## 11. Exportar a Moodle (vía LaTeX)

`QuizMoodle` escribe un fichero `.tex` autónomo (paquete `moodle`) con todas las
variantes. Al compilarlo se obtienen un PDF de revisión y el fichero
`<nombre>-moodle.xml`, que se importa en Moodle (**Banco de preguntas → Importar →
Formato Moodle XML**):

```bash
cd exportaciones
xelatex MiCuestionario.tex      # → MiCuestionario.pdf y MiCuestionario-moodle.xml
```

El `.tex` compila también con `pdflatex`, pero entonces el paquete `moodle` declara el
XML en `iso-8859-1` aunque escribe `¿ ¡` en UTF-8 (Moodle mostraría `Â¿`): es lo que
hacen los proyectos de `qbank-init`, que lo corrigen después con `scripts/fix_moodle_xml.py`
(`make moodle`). A mano, `xelatex` evita el problema.

Una pregunta de varias partes sale como una pregunta *cloze* con un bloque por parte,
sin hacer nada especial.
""")

code(r'''
n = QuizMoodle("MiCuestionario", "exportaciones/", p, last_choice=True)
print(f"{n} variantes en exportaciones/MiCuestionario.tex\n")
with open("exportaciones/MiCuestionario.tex") as f:
    print(f.read()[:800], "…")
''')

code(r'''
QuizMoodle("AlgebraLineal", "exportaciones/", p_matriz, last_choice=True)
QuizMoodle("Superheroes", "exportaciones/", load_problema("superheroes.json"), last_choice=True)
print("Escritos exportaciones/AlgebraLineal.tex y exportaciones/Superheroes.tex (cloze con varias partes)")
''')

md(r"""
<a id="12"></a>
## 12. Apéndice: verdadero/falso con `ProblemaVF`

`ProblemaVF` es un formato aparte: toma aleatoriamente `NumPreguntas` ítems de un banco
fijo de afirmaciones verdadero/falso, sin lógica proposicional. `lint` y los scripts de
`qbank-init` no lo manejan; para un banco nuevo, una pregunta de tres huecos de
`ProblemaTipo` cubre el mismo uso. Se exporta con `AMC_VF` y `QuizVFMoodle`.

`ProblemaVF` sortea con el módulo `random` de Python y no tiene `seed`: para que el ejemplo
salga igual cada vez que se ejecuta, la celda siembra `random` a mano con `random.seed(42)`.
""")

code(r'''
import random
random.seed(42)

banco_vf = [
    ("La derivada de $x^2$ es $2x$.",         True),
    ("La integral de $2x$ es $x^2 + C$.",      True),
    ("$\\sin^2(x) + \\cos^2(x) = 2$.",         False),
    ("El número $e$ es irracional.",            True),
    ("$\\ln(1) = 1$.",                          False),
    ("$\\sqrt{2}$ es irracional.",              True),
]
p_vf = ProblemaVF("Indique cuáles de las siguientes afirmaciones son verdaderas:", banco_vf, NumPreguntas=3)

for etiqueta, enunciado, cuestiones in itertools.islice(p_vf, 2):   # ProblemaVF sortea sin fin: se toman 2
    print(f"── Variante {etiqueta} ──")
    for texto, correcto in cuestiones:
        print(f"   [{'✓' if correcto else '✗'}] {texto}")
    print()
''')

md(r"""
---
## Siguiente paso

- `qbank-init mi-banco` crea un proyecto con preguntas de ejemplo, `make lint`, `make amc`,
  `make amc-student` y `make moodle`.
- `GuiaDiseno.org`: cómo diseñar buenas preguntas.
- `Manual.org`: la referencia completa de la API y del formato JSON.
""")

nb.write("ejemplosManual/Demo.ipynb")
