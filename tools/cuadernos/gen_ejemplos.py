import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import AYUDANTE, Cuaderno

nb = Cuaderno("ejem")
md, code = nb.md, nb.code

md(r"""
# Ejemplos de preguntas de econometría

**Autor:** Marcos Bujosa

Este cuaderno es un *caso real*: una pregunta de econometría (multicolinealidad) escrita
en Python como la escribiría el autor, revisada, guardada en JSON y exportada. Usa la
notación LaTeX del curso (`\ajusteMLG`, `\Mat{X}`, …, definidas en un paquete propio que
se pasa a los exportadores con `aux_latex`), así que los `.tex` generados no compilan
fuera de ese curso; lo que interesa aquí es el flujo. Empieza con una lección breve
sobre cómo escribir LaTeX dentro de cadenas de Python, que es el primer tropiezo de
cualquiera. Ejecuta las celdas en orden, desde la carpeta raíz del repositorio.

1. [LaTeX dentro de cadenas de Python](#latex)
2. [La pregunta sobre multicolinealidad](#pregunta)
3. [Revisión, `lint`, JSON y exportación](#flujo)
""")

md(r"""
<a id="latex"></a>
## 1. LaTeX dentro de cadenas de Python

### Cadenas crudas (*raw strings*)

En Python, la barra invertida `\` introduce caracteres especiales (`\n` es un salto de
línea, `\t` un tabulador). LaTeX también usa la barra invertida para todos sus comandos
(`\alpha`, `\textbf{}`, `\emph{}`), así que al escribir LaTeX en una cadena normal pueden
pasar dos cosas: que Python convierta `\nabla` en un salto de línea seguido de `abla`, o
que avise de una secuencia de escape no válida (`\e` en `\emph`). Anteponer una `r` a la
cadena (`r"..."`) le dice a Python que trate la barra como un carácter literal:
""")

code(r'''
cadena_normal = "Texto con \nabla y \times"      # Python interpreta \n y \t
print(cadena_normal)
print()
cadena_cruda = r"Texto con \nabla y \times"      # cadena cruda: llega intacta a LaTeX
print(cadena_cruda)
''')

md(r"""
### La alternativa: doblar la barra

También se puede *escapar* la barra escribiéndola dos veces (`\\`): Python lee la primera
como «viene un carácter especial» y la segunda como «ese carácter es una barra». Es lo
que hay que hacer en los ficheros JSON, donde no existen las cadenas crudas.
""")

code(r'''
print("Texto con \\nabla y \\times")
''')

md(r"""
| Método | Ventajas | Desventajas |
|---|---|---|
| Cadenas crudas `r"..."` | Código más limpio; se puede copiar y pegar una fórmula de Overleaf tal cual | No pueden terminar en una sola barra (`r"texto\"` da error) |
| Doblar la barra `"\\..."` | Funciona en cualquier parte de la cadena; es lo que usa el JSON | Las fórmulas largas se vuelven ilegibles y es fácil olvidar una barra |

> **En la práctica:** en Python, escribe las cadenas con LaTeX siempre con `r`. Recuerda
> además que `%` es un comentario en LaTeX: escribe `\%` (`r"un 5 \% de..."`).
""")

md(r"""
<a id="pregunta"></a>
## 2. La pregunta sobre multicolinealidad

Primero cargamos `qbank` para que Python sepa lo que son `Supuesto`, `Cuestion`, etc., y
definimos `muestra`, un ayudante que imprime las variantes (o la vista profe) con sus marcas
y, si la pregunta la lleva, la opción por defecto. Es el mismo en los tres cuadernos.
""")

code(r'''
from qbank import *
''' + AYUDANTE)

md(r"""
### El enunciado

El enunciado es el principio de la lista plana de componentes: un texto fijo, una lista de
cuatro `Supuesto` y otro texto fijo. Dos `Supuesto` afirman `v('Mcoli')` (multicolinealidad
perfecta) y dos la niegan, cada uno con su propia redacción. Lógicamente solo hay dos
situaciones, pero **para el motor cada `Supuesto` sorteado es un mundo distinto** (su texto
cambia el enunciado): la vista profe, `tabla_mundos` y `lint` hablan de cuatro mundos.
""")

code(r'''
enunciado = [
    r'En el ajuste MCO:\; $\ajusteMLG$,\; ',
    [
        Supuesto(r'donde $\Matdim{X}{N}{k}$, si $rg(\Mat{X})<k$, con $k \leq N$,', v('Mcoli')),
        Supuesto(r'si $(\MTM{X})$ es singular,',                                  v('Mcoli')),
        Supuesto(r'donde $\Matdim{X}{N}{k}$, si $rg(\Mat{X})=k$, con $k \leq N$,', -v('Mcoli')),
        Supuesto(r'si $(\MTM{X})$ es invertible,',                                -v('Mcoli')),
    ],
    ' entonces: ',
]
''')

md(r"""
Un texto o un `Supuesto` suelto (sin corchetes) aparece en todas las variantes; una
*lista* es un sorteo: en cada variante se elige uno de sus elementos. Como el tercer
y el cuarto mundos afirman `-v('Mcoli')` directamente, las cuestiones con esa semántica se
deducen sin necesidad de un axioma.

### Las cuestiones

Tres **huecos**, cada uno una lista de alternativas de la que se sortea una; con la
opción por defecto (`last_choice`), el alumno ve cuatro opciones. Las explicaciones
(`exp`) las muestra Moodle tras responder.
""")

code(r'''
preguntas = [
    [
        Cuestion(r'ningún regresor es combinación lineal del resto', -v('Mcoli'),
                 exp=r'cuando $(\MTM{X})$ es invertible, es decir, cuando $rg(\Mat{X}) = k$'),
        Cuestion(r'las \emph{columnas} de $\Mat{X}$ son linealmente indep.', -v('Mcoli'),
                 exp=r'cuando $(\MTM{X})$ es invertible, es decir, cuando $rg(\Mat{X}) = k$'),
        Cuestion(r'las \emph{filas} de $\Mat{X}$ son linealmente indep.', False,
                 exp=r'solo si $N=rg(\Mat{X})$'),
        Cuestion(r'algún regresor es combinación lineal del resto', v('Mcoli'),
                 exp=r'cuando $(\MTM{X})$ es singular, es decir, cuando $rg(\Mat{X}) < k$'),
    ],
    [
        Cuestion(r'$\Vect{y}$ es combinación lineal de los regresores', False, precond=-v('Mcoli'),
                 exp=r'cuando $\Vect{y}$ es de la forma $\MV{X}{\beta}$, es decir cuando $\res=\Vect{0}$'),
        Cuestion(r'$\MTM{X}\Vect{\beta}=\MTV{X}{y}$ tiene solución \emph{única}', -v('Mcoli'),
                 exp=r'cuando $(\MTM{X})$ es invertible, es decir, cuando $rg(\Mat{X}) = k$'),
        Cuestion(r'$\MTM{X}\Vect{\beta}=\MTV{X}{y}$ es compatible (tiene sol.)', True,
                 exp=r'las ecuaciones normales siempre tienen solución'),
    ],
    [
        Cuestion(r'el vector $\Estmc{\Vect{\beta}}$ está definido', -v('Mcoli'),
                 exp=r'cuando $\MTM{X}\Vect{\beta}=\MTV{X}{y}$ tiene solución \emph{única}'),
        Cuestion(r'el vector $\Estmc{\Vect{\beta}}$ es indeterminado', v('Mcoli'),
                 exp=r'cuando $\MTM{X}\Vect{\beta}=\MTV{X}{y}$ tiene infinitas soluciones'),
        Cuestion(r'la correlación entre algunos regresores es 1 en valor absoluto', False,
                 exp=r'cuando algún regresor es un múltiplo de otro'),
        Cuestion(r'la correlación entre regresores es \emph{menor} que 1 en valor absoluto', -v('Mcoli'),
                 exp=r'cuando los regresores son linealmente independientes'),
    ],
]
''')

md(r"""
### El problema completo

El problema es la concatenación (`+`) de las dos listas, con las preferencias de
exportación y el nombre (que será el del fichero JSON):
""")

code(r'''
pt = ProblemaTipo(enunciado + preguntas,
                  export={"last_choice": True, "cols": 2},
                  nombre="multicolinealidad")
print(len(list(pt.por_partes())), "variantes")
''')

md(r"""
<a id="flujo"></a>
## 3. Revisión, `lint`, JSON y exportación

### Vista profe

`por_partes_profe()` muestra, para cada mundo (aquí los cuatro `Supuesto`: dos con
multicolinealidad y dos sin ella), **todas** las cuestiones de cada hueco con su marca:
`[✓]` correcta, `[✗]` incorrecta, `[·]` rechazada por su precondición (con el motivo). Es
la forma de verificar la lógica. Para no alargar la salida se omiten las explicaciones.
""")

code(r'''
muestra(pt, n=4, profe=True, con_exp=False)
''')

md(r"""
### Comprobación automática

`lint` revisa todas las variantes: mezcla de correctas e incorrectas (contando la opción
por defecto), negaciones deducibles, número de variantes, textos problemáticos…

Aquí no hay `ERROR` ni `AVISO`. Los `INFO` [`constante`] señalan las cuestiones con
`semantica` literal (`True`/`False`) que valen lo mismo en todos los mundos: son
distractores deliberados («las filas son linealmente independientes», siempre falsa) o
verdades que no dependen del supuesto (las ecuaciones normales siempre tienen solución).
Si una cuestión con fórmula, como `-v('Mcoli')`, saliera constante, `lint` daría `AVISO`:
por ejemplo, si «tiene solución única» llevara `precond=-v('Mcoli')`, solo aparecería en
los mundos sin multicolinealidad, siempre correcta, y nunca serviría de distractor.
""")

code(r'''
for a in lint(pt):
    print(a)
print()
print(tabla_mundos(pt))
''')

md(r"""
### Todas las variantes (vista alumno)

Lo que verá el alumno: se muestran las cuatro primeras variantes, con sus explicaciones y
la opción por defecto (para ver más, cambia `n`).
""")

code(r'''
print(len(list(pt.por_partes())), "variantes; las cuatro primeras:\n")
muestra(pt, n=4)
''')

md(r"""
### Guardar en JSON y recargar

El JSON es el formato de las preguntas de un banco. `load_problema` lo recupera y el
problema se comporta igual.
""")

code(r'''
import os, json
os.makedirs("mis_problemas", exist_ok=True)

save_problema(pt, "mis_problemas/multicolinealidad.json")
with open("mis_problemas/multicolinealidad.json", encoding="utf-8") as f:
    print(json.dumps(json.load(f), indent=2, ensure_ascii=False)[:1200], "…")

pt2 = load_problema("mis_problemas/multicolinealidad.json")
print("\nOriginal:", len(list(pt.por_partes())), "variantes; cargado:", len(list(pt2.por_partes())))
''')

md(r"""
### Guardar como guion de Python

`save_problema_py` escribe el problema como lista de listas editable, que puede
ejecutarse y volver a guardarse con `save_problema`.
""")

code(r'''
save_problema_py(pt, "mis_problemas/multicolinealidad.py")
print(problema_to_python(pt)[:700], "…")
''')

md(r"""
### Exportar a Moodle y AMC

`QuizMoodle` escribe el `.tex` que, compilado con `xelatex` (o `pdflatex` + `fix_moodle_xml.py`; paquete `moodle`), produce
el PDF de revisión y `multicolinealidad-moodle.xml`; `QuizAMCProfe` escribe la vista profe
en LaTeX para AMC. Esta pregunta necesita el paquete LaTeX del curso, que se pasa con
`aux_latex`. En un banco creado con `qbank-init`, `make moodle` y `make amc` hacen esto
para todas las preguntas.
""")

code(r'''
n = QuizMoodle("multicolinealidad", "mis_problemas/", pt,
               last_choice=True, aux_latex=r"\usepackage{nacal-moodle}")
print(f"{n} variantes → mis_problemas/multicolinealidad.tex (xelatex → multicolinealidad-moodle.xml)")

n = QuizAMCProfe("multicolinealidad", "mis_problemas/", pt, cols=2, last_choice=True)
print(f"{n} variantes (vista profe) → mis_problemas/multicolinealidad_profe.tex")
''')

nb.write("Ejemplos.ipynb")
