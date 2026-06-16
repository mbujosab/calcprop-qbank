# Copyright (C) 2020-2026  Marcos Bujosa
#
# This file is part of calcprop-qbank.
#
# calcprop-qbank is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# calcprop-qbank is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re as _re
import warnings as _warnings
from qbank._quiz import *

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sanitize_name(nombre):
    """Sustituye ':' y '_' por '-' en identificadores LaTeX."""
    return nombre.replace(':', '-').replace('_', '-')

def codchar(s):
     s = s.replace("á", "\\'{a}")
     s = s.replace("é", "\\'{e}")
     s = s.replace("í", "\\'{i}")
     s = s.replace("ó", "\\'{o}")
     s = s.replace("ú", "\\'{u}")
     s = s.replace("ñ", "\\~{n}")
     return s

# ── Exportadores AMC ──────────────────────────────────────────────────────────

def AMCblock(nombre, etiqueta, enunciado, cuestiones,
             last_choice=False, cols=1, profe=False,
             opc=["", "Ninguna de las anteriores"]):
    """Genera el bloque AMC para una pregunta de tipo multichoice.

    Parámetros
    ----------
    nombre      : identificador del grupo AMC (se sanitiza: ':' → '-')
    etiqueta    : etiqueta de la variante
    enunciado   : texto del enunciado (``$$...$$`` se convierte a ``\\[...\\]``)
    cuestiones  : lista de (texto, correcto, activa[, exp])
    last_choice : si True, añade opción comodín con ``\\lastchoices``
    cols        : número de columnas multicols (1 = sin multicols)
    profe       : si True, añade ``\\explain`` con cuestiones rechazadas
    opc         : [instrucciones_extra, texto_lastchoice]
    """
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    _fix = lambda t: _re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', t, flags=_re.DOTALL)
    nombre_tex    = _sanitize_name(nombre)
    enunciado_tex = _fix(enunciado)

    ex = ''
    s  = '\\element{' + nombre_tex + '}{' + InstruccionesAux + '\n'
    s += ' \\begin{questionmult}{' + nombre_tex + '-' + str(etiqueta) + '}\n'
    s += '  ' + enunciado_tex + '\n'

    if cols > 1:
        s += '   \\begin{multicols}{' + str(cols) + '}\\AMCBoxedAnswers\n'
        ch_indent = '      '
    else:
        ch_indent = '     '

    s += ch_indent + '\\begin{choices}\n'
    for c in cuestiones:
        texto = _fix(c[0])
        if c[2]:
            s += ' ' * 7 + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + texto + '}\n'
        elif profe:
            ex += ' cuestion: ' + texto + '; ' + str(c[1]) + '\n'

    if last_choice:
        s += ' ' * 7 + '\\lastchoices\n'
        s += ' ' * 7 + ('\\wrongchoice  {' if any(c[1] for c in cuestiones) else '\\correctchoice{') + OpcPorDefecto + '}\n'

    s += ch_indent + '\\end{choices}\n'

    if cols > 1:
        s += '   \\end{multicols}\n'

    if profe and ex:
        s += '   \\explain{' + ex + '            }\n'

    s += ' \\end{questionmult} '
    s += '}\n\n'
    return s


# ── AMC para ProblemaVF y multiparte ─────────────────────────────────────────

def AMC_VF(nombre, etiqueta, enunciado, cuestiones, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    nombre = _sanitize_name(nombre)
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'

    s = s + '     \\begin{choices}\n'
    for c in cuestiones:
        s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
    s = s + '     \\end{choices}\n'

    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s

def AMC_multipart(nombre, etiqueta, enunciado, subpreguntas, opc=[""]):
    """Genera el bloque AMC para una pregunta con enunciado común y sub-preguntas.

    subpreguntas: list de (intro, [(texto, correcto, activa, exp), ...])
    Cada sub-pregunta produce un bloque \\begin{choices} independiente precedido
    por \\emph{intro} y envuelto en \\AMCnoCompleteMulti.
    """
    InstruccionesAux = opc[0] if opc else ""
    nombre = _sanitize_name(nombre)
    s  = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s += ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s += '  ' + enunciado + '\n\n'
    for intro, cuestiones in subpreguntas:
        s += '  \\emph{' + intro + '}\n'
        s += '  {\\AMCnoCompleteMulti\n'
        s += '   \\begin{choices}\n'
        for c in cuestiones:
            s += ' ' * 5 + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
        s += '   \\end{choices}\n'
        s += '  }\n\n'
    s += ' \\end{questionmult} '
    s += '}\n\n'
    return s


# ── Exportadores Moodle ───────────────────────────────────────────────────────

_MOODLE_HEADER = """\
\\documentclass[11pt]{{article}}

\\usepackage[cm,headings]{{fullpage}}

\\usepackage{{moodle}}

\\usepackage{{graphicx}}

\\usepackage{{fancyvrb}}

\\ifPDFTeX                    % FOR LATEX and PDFLATEX
    \\usepackage[utf8]{{inputenc}}   % necessary
    \\usepackage[OT1] {{fontenc}}    % necessary
\\else                        % assuming XELATEX or LUALATEX
    \\usepackage{{fontspec}}
\\fi

{auxLaTeX}
\\newcommand\\peque{{}}

\\begin{{document}}

\\begin{{quiz}}{{{nombre_tex}}}

"""

def _moodle_header(nombre, auxLaTeX=""):
    return _MOODLE_HEADER.format(
        auxLaTeX=auxLaTeX,
        nombre_tex=_sanitize_name(nombre),
    )

def QuizMoodle(nombre, directorio, problema, last_choice=False,
               opc=None, instances=1, *,
               aux_latex="", last_choice_text="Las demás opciones son falsas"):
    """Exporta un problema (o dict de problemas) al formato Moodle XML vía LaTeX.

    Parámetros
    ----------
    nombre           : nombre del quiz (identifica el grupo en Moodle)
    directorio       : ruta al directorio de salida (con '/' al final)
    problema         : ProblemaTipo o dict {nombre: ProblemaTipo}
    last_choice      : si True, añade la opción comodín «las demás son falsas»
    aux_latex        : cabecera LaTeX adicional (p.ej. \\usepackage{...})
    last_choice_text : texto de la opción comodín
    instances        : número de instancias con semillas distintas (ver por_partes())

    Retorna
    -------
    int : número de variantes escritas
    """
    if opc is not None:
        _warnings.warn(
            "El parámetro 'opc' está deprecado; usa aux_latex= y last_choice_text=",
            DeprecationWarning, stacklevel=2,
        )
        aux_latex        = opc[0]
        last_choice_text = opc[1]

    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)

    cuerpo = (lambda c: _ClozeMultiLastCh(c, last_choice_text)) if last_choice else _ClozeMulti

    count = 0
    with open(directorio + nombre + ".tex", "w") as f:
        f.write(_moodle_header(nombre, auxLaTeX=aux_latex))
        for nom in problema:
            for etiqueta, partes in problema[nom].por_partes(instances=instances):
                f.write(_ClozeBlock(nom, etiqueta, partes, cuerpo))
                count += 1
        f.write("\\end{quiz}\n\n\\end{document}\n")
    return count

def QuizMoodleProfe(nombre, directorio, problema, opc=None, *, aux_latex=""):
    """Vista profe para Moodle: mismas variantes que el alumno con fracciones visibles.

    Exporta exactamente las mismas variantes que QuizMoodle pero con el esquema
    de corrección visible (porcentajes de puntuación por opción). Útil para que
    el profesor revise cómo puntúa Moodle cada variante.

    Para la vista aplanada (todas las cuestiones de cada sublista con marcas),
    usa QuizAMCProfe() que genera un PDF AMC con \\explain{} para rechazadas.

    Parámetros
    ----------
    nombre      : nombre del quiz (identifica el grupo en Moodle)
    directorio  : ruta al directorio de salida (con '/' al final)
    problema    : ProblemaTipo o dict {nombre: ProblemaTipo}
    aux_latex   : cabecera LaTeX adicional (p.ej. \\usepackage{...})

    Retorna
    -------
    int : número de variantes escritas
    """
    if opc is not None:
        _warnings.warn(
            "El parámetro 'opc' está deprecado; usa aux_latex=",
            DeprecationWarning, stacklevel=2,
        )
        aux_latex = opc[0]

    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    count = 0
    with open(directorio + nombre + ".tex", "w") as f:
        f.write(_moodle_header(nombre, auxLaTeX=aux_latex))
        for nom in problema:
            for etiqueta, partes in problema[nom].por_partes():
                f.write(_ClozeBlock(nom, etiqueta, partes, _ClozeMultiProfe))
                count += 1
        f.write("\\end{quiz}\n\n\\end{document}\n")
    return count


def QuizAMCProfe(nombre, directorio, problema, cols=1,
                 opc=None, *,
                 aux_latex="", last_choice_text="Ninguna de las anteriores"):
    """Vista profe aplanada para AMC: todas las cuestiones de cada sublista.

    Usa por_partes_profe() para mostrar TODAS las cuestiones de cada sublista
    (no solo la seleccionada para el alumno) con marcas de correcto/incorrecto.
    Las cuestiones rechazadas por precondición aparecen en \\explain{}.

    Útil para revisar en papel la lógica de corrección de una pregunta.
    El fichero generado se incluye en el documento AMC con \\input{nombre_profe.tex}.

    Parámetros
    ----------
    nombre           : identificador del grupo AMC
    directorio       : ruta al directorio de salida (con '/' al final)
    problema         : ProblemaTipo o dict {nombre: ProblemaTipo}
    cols             : número de columnas multicols (1 = sin multicols)
    aux_latex        : instrucciones LaTeX extra dentro del bloque \\element{}
    last_choice_text : texto de la opción comodín

    Retorna
    -------
    int : número de bloques AMC escritos
    """
    if opc is not None:
        _warnings.warn(
            "El parámetro 'opc' está deprecado; usa aux_latex= y last_choice_text=",
            DeprecationWarning, stacklevel=2,
        )
        aux_latex        = opc[0]
        last_choice_text = opc[1]

    _opc = [aux_latex, last_choice_text]
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    count = 0
    with open(directorio + nombre + "_profe.tex", "w") as f:
        for nom in problema:
            for etiqueta, partes in problema[nom].por_partes_profe():
                for i, (enunciado, cuestiones) in enumerate(partes):
                    etiq = f"{etiqueta}-{i+1}" if len(partes) > 1 else etiqueta
                    f.write(AMCblock(nom, etiq, enunciado, cuestiones,
                                     cols=cols, profe=True, opc=_opc))
                    count += 1
    return count

def QuizVFMoodle(nombre, directorio, GenVar, num, opc=["",""]):
    auxLaTeX = opc[0]
    with open(directorio + nombre + ".tex", "w") as f:
        f.write(_moodle_header(nombre, auxLaTeX=auxLaTeX))
        for i in range(num):
            var = next(GenVar)
            f.write(MoodleMulti(codchar(nombre), var[0], codchar(var[1]), var[2]))
        f.write("\\end{quiz}\n\n\\end{document}\n")

def MoodleMulti(nombre, variante, enunciado, cuestiones):
    def itemBuena(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]* ") if aclaracion else r"\item* "

    def itemMala(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]  ") if aclaracion else r"\item  "

    s = " \\begin{multi}[multiple, points=" + str(len(cuestiones)-1) +"]"
    s = s + "{" + codchar(nombre) + "-" + str(variante) + "}\n"
    s = s + "    " + enunciado + "\n"

    for c in cuestiones:
        fb = c[3] if len(c) > 3 else ''
        s = s + (' ' * 7) + (itemBuena(fb) if c[1] else itemMala(fb)) + codchar(c[0]) + '\n'

    s = s + " \\end{multi}\n\n"
    return s

def MoodleMultiProfe(nombre, variante, enunciado, cuestiones):
    def feedback(texto):
        return r",\feedback={"+codchar(texto)+"}"
    b = 0; m = 0;
    for c in cuestiones:
        if c[2]:
            if c[1]:
                b+=1
            else:
                m+=1
    def itemBuena(numBuenas, aclaracion):
        return ("\\item[fraction=" + str(round(100/numBuenas)) + feedback(aclaracion) + "]") if numBuenas else "\\item*"

    def itemMala(numMalas, aclaracion):
        return ("\\item[fraction=" + str(-round(100/numMalas)) + feedback(aclaracion) + "]") if numMalas else "\\item"

    s = " \\begin{multi}[multiple, fractiontol=5.1"  +"]"
    s = s + "{" + codchar(nombre) + "-" + str(variante) + "}\n"
    s = s + "    " + enunciado + "\n"

    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + (itemBuena(b, c[3]) if c[1] else itemMala(m, c[3])) + codchar(c[0]) + "\n"

    s = s + " \\end{multi}\n\n"
    return s

def MoodleMultiLastCh(nombre, variante, enunciado, cuestiones,
                      lastchoice="Las demás opciones son falsas"):
    v = [c[1] for c in cuestiones].count(True)
    cuestiones = cuestiones + [(codchar(lastchoice), (False if v else True), 1, '')]
    def itemBuena(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]* ") if aclaracion else r"\item* "

    def itemMala(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]  ") if aclaracion else r"\item  "

    s = " \\begin{multi}[multiple, points=" + str(len(cuestiones)-1) +"]"
    s = s + "{" + codchar(nombre) + "-" + str(variante) + "}\n"
    s = s + "    " + enunciado + "\n"

    for c in cuestiones:
        fb = c[3] if len(c) > 3 else ''
        s = s + (' ' * 7) + (itemBuena(fb) if c[1] else itemMala(fb)) + codchar(c[0]) + '\n'

    s = s + " \\end{multi}\n\n"
    return s


# ── Bloques Cloze (Moodle interno) ───────────────────────────────────────────

def _ClozeMulti(cuestiones):
    def itemBuena(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]* ") if aclaracion else r"\item* "

    def itemMala(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]  ") if aclaracion else r"\item  "

    s = "  \\begin{multi}[multiple, points=" + str(len(cuestiones)-1) + "]\n"
    for c in cuestiones:
        fb = c[3] if len(c) > 3 else ''
        s = s + (' ' * 7) + (itemBuena(fb) if c[1] else itemMala(fb)) + codchar(c[0]) + '\n'
    s = s + "  \\end{multi}\n\n"
    return s

def _ClozeMultiLastCh(cuestiones, lastchoice="Las demás opciones son falsas"):
    v = [c[1] for c in cuestiones].count(True)
    cuestiones = cuestiones + [(codchar(lastchoice), (False if v else True), 1, '')]
    def itemBuena(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]* ") if aclaracion else r"\item* "

    def itemMala(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]  ") if aclaracion else r"\item  "

    s = "  \\begin{multi}[multiple, points=" + str(len(cuestiones)-1) + "]\n"
    for c in cuestiones:
        fb = c[3] if len(c) > 3 else ''
        s = s + (' ' * 7) + (itemBuena(fb) if c[1] else itemMala(fb)) + codchar(c[0]) + '\n'
    s = s + "  \\end{multi}\n\n"
    return s

def _ClozeMultiProfe(cuestiones):
    def feedback(texto):
        return r",\feedback={"+codchar(texto)+"}"
    b = 0; m = 0;
    for c in cuestiones:
        if c[2]:
            if c[1]:
                b+=1
            else:
                m+=1
    def itemBuena(numBuenas, aclaracion):
        return ("\\item[fraction=" + str(round(100/numBuenas)) + feedback(aclaracion) + "]") if numBuenas else "\\item*"

    def itemMala(numMalas, aclaracion):
        return ("\\item[fraction=" + str(-round(100/numMalas)) + feedback(aclaracion) + "]") if numMalas else "\\item"

    s = "  \\begin{multi}[multiple, fractiontol=5.1]\n"
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + (itemBuena(b, c[3]) if c[1] else itemMala(m, c[3])) + codchar(c[0]) + "\n"
    s = s + "  \\end{multi}\n\n"
    return s

def _ClozeBlock(nombre, etiqueta, partes, cuerpo):
    """Envuelve las partes de una variante en un entorno cloze.
    `cuerpo(cuestiones)` genera el bloque \\begin{multi}…\\end{multi} de cada parte."""
    nombre_tex = codchar(_sanitize_name(nombre))
    s = " \\begin{cloze}{" + nombre_tex + "-" + str(etiqueta) + "}\n"
    for enunciado, cuestiones in partes:
        s += "  " + codchar(enunciado) + "\n"
        s += cuerpo(cuestiones)
    s += " \\end{cloze}\n\n"
    return s
