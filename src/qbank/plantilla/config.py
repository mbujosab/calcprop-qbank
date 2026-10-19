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

# Vista profe de las preguntas con setup aleatorio: cuántos sorteos se exploran
# y cuántos casos distintos (mundo × patrón de marcas) se imprimen como máximo.
N_SORTEOS_PROFE = 150
MAX_CASOS_PROFE = 12
