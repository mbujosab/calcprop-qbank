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

import os as _os
import re as _re
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
             last_choice=False, cols=1, profe=False, *,
             aux_latex="", last_choice_text="Ninguna de las anteriores"):
    """Genera el bloque AMC para una pregunta de tipo multichoice.

    Parámetros
    ----------
    nombre           : identificador del grupo AMC (se sanitiza: ':' → '-')
    etiqueta         : etiqueta de la variante
    enunciado        : texto del enunciado (``$$...$$`` se convierte a ``\\[...\\]``)
    cuestiones       : lista de (texto, correcto, activa[, exp])
    last_choice      : si True, añade la opción por defecto con ``\\lastchoices``
    cols             : número de columnas multicols (1 = sin multicols)
    profe            : si True, añade ``\\explain`` con cuestiones rechazadas
    aux_latex        : instrucciones LaTeX extra dentro del bloque \\element{}
    last_choice_text : texto de la opción por defecto
    """
    nombre_tex = _sanitize_name(nombre)
    s  = '\\element{' + nombre_tex + '}{' + aux_latex + '\n'
    s += ' \\begin{questionmult}{' + nombre_tex + '-' + str(etiqueta) + '}\n'
    s += '  ' + _fix_display(enunciado) + '\n'
    choices, ex = _amc_choices(cuestiones, last_choice, cols, profe, last_choice_text)
    s += choices
    if profe and ex:
        s += '   \\explain{' + ex + '            }\n'
    s += ' \\end{questionmult} '
    s += '}\n\n'
    return s


def _fix_display(t):
    """``$$…$$`` → ``\\[…\\]`` (automultiplechoice se lleva mal con ``$$``)."""
    return _re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', t, flags=_re.DOTALL)


def _amc_choices(cuestiones, last_choice, cols, profe, last_choice_text):
    """Bloque ``\\begin{choices}…\\end{choices}`` de una parte (dentro de
    multicols si cols > 1, con la opción por defecto si last_choice) y, para
    la vista profe, el texto de las cuestiones rechazadas que irá en ``\\explain``."""
    s, ex = '', ''
    if cols > 1:
        s += '   \\begin{multicols}{' + str(cols) + '}\\AMCBoxedAnswers\n'
        ch_indent = '      '
    else:
        ch_indent = '     '

    s += ch_indent + '\\begin{choices}\n'
    for c in cuestiones:
        texto = _fix_display(c[0])
        if c[2]:
            s += ' ' * 7 + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + texto + '}\n'
        elif profe:
            ex += ' cuestión: ' + texto + '; ' + str(c[1]) + '\n'

    if last_choice:
        s += ' ' * 7 + '\\lastchoices\n'
        s += ' ' * 7 + ('\\wrongchoice  {' if any(c[2] and c[1] for c in cuestiones) else '\\correctchoice{') + last_choice_text + '}\n'

    s += ch_indent + '\\end{choices}\n'

    if cols > 1:
        s += '   \\end{multicols}\n'
    return s, ex


# ── AMC para ProblemaVF y multiparte ─────────────────────────────────────────

def AMC_VF(nombre, etiqueta, enunciado, cuestiones, opc=None):
    if opc is None:
        opc = ["", "Ninguna de las anteriores"]
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

def AMC_multipart(nombre, etiqueta, enunciado, partes,
                  last_choice=False, cols=1, profe=False, *,
                  aux_latex="", last_choice_text="Ninguna de las anteriores", opc=None):
    """Bloque AMC de una pregunta multiparte: un único questionmult con un
    bloque de casillas por parte.

    partes    : [(enunciado_parte, cuestiones), ...] tal como lo devuelven
                por_partes() y por_partes_profe()
    enunciado : texto común que precede a todas las partes; normalmente ""
                porque el enunciado de la primera parte ya lo contiene
    last_choice, cols, profe, aux_latex, last_choice_text : como en AMCblock,
                aplicados a cada parte (con last_choice, cada parte lleva su
                propia opción por defecto)
    opc       : forma antigua de pasar aux_latex ([aux_latex]); se mantiene
                por compatibilidad
    """
    if opc:
        aux_latex = opc[0]
    nombre_tex = _sanitize_name(nombre)
    s  = '\\element{' + nombre_tex + '}{' + aux_latex + '\n'
    s += ' \\begin{questionmult}{' + nombre_tex + '-' + str(etiqueta) + '}\n'
    if enunciado:
        s += '  ' + _fix_display(enunciado) + '\n\n'
    ex = ''
    for k, (intro, cuestiones) in enumerate(partes):
        if intro.strip():
            intro_tex = _fix_display(intro.strip())
            s += '  ' + (intro_tex if k == 0 and not enunciado else '\\emph{' + intro_tex + '}') + '\n'
        choices, ex_parte = _amc_choices(cuestiones, last_choice, cols, profe, last_choice_text)
        s += '  {\\AMCnoCompleteMulti\n' + choices + '  }\n\n'
        ex += ex_parte.replace(' cuestión:', f' parte {k + 1}, cuestión:')
    if profe and ex:
        s += '   \\explain{' + ex + '            }\n'
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
               instances=1, *,
               aux_latex="", last_choice_text="Las demás opciones son falsas"):
    """Exporta un problema (o dict de problemas) al formato Moodle XML vía LaTeX.

    Parámetros
    ----------
    nombre           : nombre del quiz (identifica el grupo en Moodle)
    directorio       : ruta al directorio de salida (con o sin '/' final)
    problema         : ProblemaTipo o dict {nombre: ProblemaTipo}
    last_choice      : si True, añade la opción por defecto «las demás son falsas»
    aux_latex        : cabecera LaTeX adicional (p.ej. \\usepackage{...})
    last_choice_text : texto de la opción por defecto
    instances        : número de instancias con semillas distintas (ver por_partes())

    Retorna
    -------
    int : número de variantes escritas
    """
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)

    cuerpo = (lambda c: _ClozeMultiLastCh(c, last_choice_text)) if last_choice else _ClozeMulti

    count = 0
    with open(_os.path.join(directorio, nombre + ".tex"), "w") as f:
        f.write(_moodle_header(nombre, auxLaTeX=aux_latex))
        for nom in problema:
            for etiqueta, partes in problema[nom].por_partes(instances=instances):
                f.write(_ClozeBlock(nom, etiqueta, partes, cuerpo))
                count += 1
        f.write("\\end{quiz}\n\n\\end{document}\n")
    return count

def QuizMoodleProfe(nombre, directorio, problema, *, aux_latex="",
                    last_choice=False, instances=1,
                    last_choice_text="Las demás opciones son falsas"):
    """Vista profe para Moodle: mismas variantes que el alumno con fracciones visibles.

    Exporta las mismas variantes que QuizMoodle con los mismos last_choice e
    instances, pero con el esquema de corrección visible (porcentajes de
    puntuación por opción). Útil para que el profesor revise cómo puntúa
    Moodle cada variante.

    Para ver todas las cuestiones de cada hueco con sus marcas, usa
    QuizAMCProfe(), que genera un PDF AMC con \\explain{} para las rechazadas.

    Parámetros
    ----------
    nombre           : nombre del quiz (identifica el grupo en Moodle)
    directorio       : ruta al directorio de salida (con o sin '/' final)
    problema         : ProblemaTipo o dict {nombre: ProblemaTipo}
    aux_latex        : cabecera LaTeX adicional (p.ej. \\usepackage{...})
    last_choice      : si True, añade la opción por defecto (correcta solo si
                       las demás son falsas), como QuizMoodle(last_choice=True)
    instances        : número de instancias con semillas distintas (ver por_partes())
    last_choice_text : texto de la opción por defecto

    Retorna
    -------
    int : número de variantes escritas
    """
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)

    def cuerpo(cuestiones):
        if last_choice:
            ninguna = not any(c[2] and c[1] for c in cuestiones)
            cuestiones = cuestiones + [(last_choice_text, ninguna, 1, '')]
        return _ClozeMultiProfe(cuestiones)

    count = 0
    with open(_os.path.join(directorio, nombre + ".tex"), "w") as f:
        f.write(_moodle_header(nombre, auxLaTeX=aux_latex))
        for nom in problema:
            for etiqueta, partes in problema[nom].por_partes(instances=instances):
                f.write(_ClozeBlock(nom, etiqueta, partes, cuerpo))
                count += 1
        f.write("\\end{quiz}\n\n\\end{document}\n")
    return count


def QuizAMCProfe(nombre, directorio, problema, cols=1, *,
                 last_choice=False, aux_latex="",
                 last_choice_text="Ninguna de las anteriores"):
    """Vista profe para AMC: todas las cuestiones de cada hueco.

    Usa por_partes_profe() para mostrar TODAS las cuestiones de cada hueco
    (no solo la seleccionada para el alumno) con marcas de correcto/incorrecto.
    Las cuestiones rechazadas por precondición aparecen en \\explain{}.

    Útil para revisar en papel la lógica de corrección de una pregunta.
    El fichero generado se incluye en el documento AMC con \\input{nombre_profe.tex}.

    Parámetros
    ----------
    nombre           : identificador del grupo AMC
    directorio       : ruta al directorio de salida (con o sin '/' final)
    problema         : ProblemaTipo o dict {nombre: ProblemaTipo}
    cols             : número de columnas multicols (1 = sin multicols)
    last_choice      : si True, añade la opción por defecto (como en la vista alumno)
    aux_latex        : instrucciones LaTeX extra dentro del bloque \\element{}
    last_choice_text : texto de la opción por defecto (solo con last_choice)

    Retorna
    -------
    int : número de variantes escritas (una pregunta AMC por variante)
    """
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    count = 0
    with open(_os.path.join(directorio, nombre + "_profe.tex"), "w") as f:
        for nom in problema:
            for etiqueta, partes in problema[nom].por_partes_profe():
                if len(partes) > 1:
                    f.write(AMC_multipart(nom, etiqueta, "", partes,
                                          last_choice=last_choice, cols=cols, profe=True,
                                          aux_latex=aux_latex,
                                          last_choice_text=last_choice_text))
                else:
                    f.write(AMCblock(nom, etiqueta, partes[0][0], partes[0][1],
                                     last_choice=last_choice, cols=cols, profe=True,
                                     aux_latex=aux_latex,
                                     last_choice_text=last_choice_text))
                count += 1
    return count

def QuizVFMoodle(nombre, directorio, GenVar, num, opc=None):
    if opc is None:
        opc = ["", ""]
    auxLaTeX = opc[0]
    with open(_os.path.join(directorio, nombre + ".tex"), "w") as f:
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
