"""Ajustes del banco. Los scripts de scripts/ importan este fichero."""

# LaTeX adicional para los documentos AMC (vista profe y vista alumno):
# paquetes, macros del curso, etc. Se inserta en el preámbulo. babel en español
# parte bien las palabras (sin él, «con-stante»); es-noshorthands desactiva los
# atajos de babel para el español (", ~, <, >), que alterarían textos y fórmulas.
PREAMBULO_AMC = r"""
\usepackage[spanish,es-noshorthands]{babel}
\usepackage{amsmath,amssymb}
"""

# LaTeX adicional para los documentos Moodle (se pasa a QuizMoodle como aux_latex).
AUX_LATEX_MOODLE = r"""
\usepackage{amsmath,amssymb}
"""

# Texto de la opción por defecto (la que es correcta solo si las demás son falsas).
LAST_CHOICE_TEXT_AMC    = "Ninguna de las anteriores"
LAST_CHOICE_TEXT_MOODLE = "Las demás opciones son falsas"

# Vista de lectura (make lectura): usa PREAMBULO_AMC salvo que definas
# PREAMBULO_LECTURA. EXTRAS_LECTURA: sorteos extra por mundo (con enunciado
# distinto) en las preguntas con setup que no declaran "lectura": {"cubrir": [...]}.
EXTRAS_LECTURA = 2

# Vista profe de las preguntas con setup aleatorio: cuántos sorteos se exploran
# y cuántos casos distintos (mundo × patrón de marcas) se imprimen como máximo.
N_SORTEOS_PROFE = 150
MAX_CASOS_PROFE = 12

# Notación del curso que se da por conocida: el inventario de objetos de
# `make lint` (regla 12 de qbank.lint) avisa de todo símbolo que una cuestión
# o una explicación nombra sin que el enunciado de esa variante lo presente,
# salvo estos. Escríbelos como en las preguntas: r"\mathrm{SRC}",
# r"\boldsymbol{y}", "H_0"; "\\beta_" (con la barra final) cubre \beta_1,
# \beta_2… La lista corresponde a la «notación aceptada como conocida» de
# prompts/PROMPT-proyecto.org: mantén las dos iguales.
NOTACION_CONOCIDA = []

# Separadores decimales que el lint lee como tales en las cifras (reglas de
# patrones y de gemelas). Por defecto admite 0{,}5, 0,5 y 0.5. Si el banco
# escribe siempre los decimales como 0{,}5, declara DECIMAL = "{,}": así una
# coma desnuda dentro de una fórmula, (2,2,-1), separa componentes y no se lee
# como el decimal 2,2. Varios separadores, separados por espacios: "{,} .".
# DECIMAL = "{,}"
