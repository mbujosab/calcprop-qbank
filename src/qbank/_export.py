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

from qbank._quiz import *

def AMC (nombre, etiqueta, enunciado, cuestiones, opc=["",""]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'

    s = s + '     \\begin{choices}\n'
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
    s = s + '     \\end{choices}\n'
    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s
def AMC_VF (nombre, etiqueta, enunciado, cuestiones, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
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
def AMCProfe (nombre, etiqueta, enunciado, cuestiones, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    ex = ''
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'

    s = s + '     \\begin{choices}\n'
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
        else:
            ex = ex + ' cuestion: ' + c[0] + '; ' + str(c[1]) + '\n'
    s = s + '     \\end{choices}\n'
    if ex:
        s = s + '   \\explain{' + ex + '            }\n'
    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s
def AMClastCh (nombre, etiqueta, enunciado, cuestiones, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'

    s = s + '     \\begin{choices}\n'
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
    s = s + (' ' * 7) + '\\lastchoices\n'
    s = s + (' ' * 7) + ('\\wrongchoice  {' if any([c[1] for c in cuestiones]) else '\\correctchoice{') + OpcPorDefecto + '}\n'
    s = s + '     \\end{choices}\n'

    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s
def AMCmc (nombre, etiqueta, enunciado, cuestiones, ncols, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'
    s = s + '   \\begin{multicols}{' + str(ncols) + '}\\AMCBoxedAnswers\n'
    s = s + '      \\begin{choices}\n'
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
    s = s + '      \\end{choices}\n'
    s = s + '   \\end{multicols}\n'
    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s
def AMCmcProfe (nombre, etiqueta, enunciado, cuestiones, ncols, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    ex = ''
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'
    s = s + '   \\begin{multicols}{' + str(ncols) + '}\\AMCBoxedAnswers\n'
    s = s + '      \\begin{choices}\n'
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
        else:
            ex = ex + ' cuestion: ' + c[0] + '; ' + str(c[1]) + '\n'
    s = s + '     \\end{choices}\n'
    s = s + '   \\end{multicols}\n'
    if ex:
        s = s + '   \\explain{' + ex + '            }\n'
    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s
def AMClastChmc (nombre, etiqueta, enunciado, cuestiones, ncols, opc=["","Ninguna de las anteriores"]):
    InstruccionesAux = opc[0]
    OpcPorDefecto    = opc[1]
    s = '\\element{' + nombre + '}{' + InstruccionesAux + '\n'
    s = s + ' \\begin{questionmult}{' + nombre + '-' + str(etiqueta) + '}\n'
    s = s + '  ' + enunciado + '\n'
    s = s + '   \\begin{multicols}{' + str(ncols) + '}\\AMCBoxedAnswers\n'
    s = s + '      \\begin{choices}\n'
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + ('\\correctchoice{' if c[1] else '\\wrongchoice  {') + c[0] + '}\n'
    s = s + (' ' * 7) + '\\lastchoices\n'
    s = s + (' ' * 7) + ('\\wrongchoice  {' if any([c[1] for c in cuestiones]) else '\\correctchoice{') + OpcPorDefecto + '}\n'
    s = s + '      \\end{choices}\n'
    s = s + '   \\end{multicols}\n'
    s = s + ' \\end{questionmult} '
    s = s + '}\n\n'
    return s

def codchar(s):
     s = s.replace("á", "\\'{a}")
     s = s.replace("é", "\\'{e}")
     s = s.replace("í", "\\'{i}")
     s = s.replace("ó", "\\'{o}")
     s = s.replace("ú", "\\'{u}")
     s = s.replace("ñ", "\\~{n}")
     return s

def QuizMoodle (nombre, directorio, problema, opc=["",""]):
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    auxLaTeX = opc[0]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i,nom in enumerate(problema):
            for var in problema[nom]:
                f.write( MoodleMulti(codchar(nom), var[0], codchar(var[1]), var[2]) )
        f.write("\\end{quiz}\n\n\\end{document}\n")
def QuizMoodleConVariables (nombre, directorio, problema, environment, Valores, opc=["",""]):
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    auxLaTeX = opc[0]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i,nom in enumerate(problema):
            for var in problema[nom]:
                template = environment.from_string(MoodleMulti(codchar(nom), var[0], codchar(var[1]), var[2]))
                content = template.render(Valores())
                f.write(content)
        f.write("\\end{quiz}\n\n\\end{document}\n")
def QuizMoodleProfe (nombre, directorio, problema, opc=["",""]):
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    auxLaTeX = opc[0]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i,nom in enumerate(problema):
            for var in problema[nom]:
                f.write( MoodleMultiProfe(codchar(nom), var[0], codchar(var[1]), var[2]) )
        f.write("\\end{quiz}\n\n\\end{document}\n")
def QuizMoodleProfeConVariables (nombre, directorio, problema, environment, Valores, opc=["",""]):
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    auxLaTeX = opc[0]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i,nom in enumerate(problema):
            for var in problema[nom]:
                template = environment.from_string(MoodleMultiProfe(codchar(nom), var[0], codchar(var[1]), var[2]))
                content = template.render(Valores())
                f.write(content)
        f.write("\\end{quiz}\n\n\\end{document}\n")
def QuizVFMoodle (nombre, directorio, GenVar, num, opc=["",""]):
    auxLaTeX      = opc[0]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i in range(num):
            var = next(GenVar)
            f.write( MoodleMulti (codchar(nombre), var[0], codchar(var[1]), var[2]) )
        f.write("\\end{quiz}\n\n\\end{document}\n")
def MoodleMulti (nombre, variante, enunciado, cuestiones):
    def itemBuena(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]* ") if aclaracion else r"\item* "
    
    def itemMala(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]  ") if aclaracion else r"\item  "
    
    ex = ''
    s = " \\begin{multi}[multiple, points=" + str(len(cuestiones)-1) +"]"
    s = s + "{" + codchar(nombre) + "-" + str(variante) + "}\n"
    s = s + "    " + enunciado + "\n"
    
    for c in cuestiones:
        fb = c[3] if len(c) > 3 else ''
        s = s + (' ' * 7) + (itemBuena(fb) if c[1] else itemMala(fb)) + codchar(c[0]) + '\n'
    
    s = s + " \\end{multi}\n\n"
    return s
def MoodleMultiProfe (nombre, variante, enunciado, cuestiones):
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
    
    ex = ''
    s = " \\begin{multi}[multiple, fractiontol=5.1"  +"]"
    s = s + "{" + codchar(nombre) + "-" + str(variante) + "}\n"
    s = s + "    " + enunciado + "\n"
    
    for c in cuestiones:
        if c[2]:
            s = s + (' ' * 7) + (itemBuena(b, c[3]) if c[1] else itemMala(m, c[3])) + codchar(c[0]) + "\n"
        else:
            ex = ex + ' cuestion: ' + c[0] + '; ' + str(c[1]) + '\n'
    
    s = s + " \\end{multi}\n\n"
    return s

def QuizMoodleLastCh (nombre, directorio, problema, opc=["","Las demás opciones son falsas"]):
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema      = creaDiccionario(problema, nombre)
    auxLaTeX      = opc[0]
    OpcPorDefecto = opc[1]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i,nom in enumerate(problema):
            for var in problema[nom]:
                f.write(MoodleMultiLastCh(codchar(nom),var[0],codchar(var[1]),var[2],opc[1]))
        f.write("\\end{quiz}\n\n\\end{document}\n")
def QuizMoodleLastChConVariables (nombre, directorio, problema, environment, Valores, opc=["","Las demás opciones son falsas"]):
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema      = creaDiccionario(problema, nombre)
    auxLaTeX      = opc[0]
    OpcPorDefecto = opc[1]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i,nom in enumerate(problema):
            for var in problema[nom]:
                template = environment.from_string(MoodleMultiLastCh(codchar(nom), var[0], codchar(var[1]), var[2]))
                content = template.render(Valores())
                f.write(content)
        f.write("\\end{quiz}\n\n\\end{document}\n")
def QuizVFMoodleLastCh (nombre, directorio, GenVar, num, opc=["","Las demás opciones son falsas"]):
    auxLaTeX      = opc[0]
    s = "\\documentclass[11pt]{article}\n\n"
    s = s + "\\usepackage[cm,headings]{fullpage}\n\n"
    s = s + "\\usepackage{moodle}\n\n"
    s = s + "\\usepackage{graphicx}\n\n"
    s = s + "\\usepackage{fancyvrb}\n\n"
    s = s + "\\ifPDFTeX                    % FOR LATEX and PDFLATEX\n"
    s = s + "    \\usepackage[utf8]{inputenc}   % necessary\n"
    s = s + "    \\usepackage[OT1] {fontenc}    % necessary\n"
    s = s + "\\else                        % assuming XELATEX or LUALATEX\n"
    s = s + "    \\usepackage{fontspec}\n"
    s = s + "\\fi\n\n"
    s = s + auxLaTeX + "\n" + "\\newcommand\\peque{}" + "\n\n"
    s = s + "\\begin{document}\n\n"
    s = s + "\\begin{quiz}{" + nombre + "}\n\n"
    with open(directorio + nombre + ".tex","w") as f:
        f.write(s)
        for i in range(num):
            var = next(GenVar)
            f.write(MoodleMultiLastCh(codchar(nombre),var[0],codchar(var[1]),var[2],opc[1]))
        f.write("\\end{quiz}\n\n\\end{document}\n")
def MoodleMultiLastCh (nombre, variante, enunciado, cuestiones, \
                        lastchoice="Las demás opciones son falsas"):
    v = [c[1] for c in cuestiones].count(True)
    cuestiones = cuestiones + [(codchar(lastchoice), (False if v else True), 1, '')]
    def itemBuena(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]* ") if aclaracion else r"\item* "
    
    def itemMala(aclaracion):
        return ("\\item[feedback={" + codchar(aclaracion) + "}]  ") if aclaracion else r"\item  "
    
    ex = ''
    s = " \\begin{multi}[multiple, points=" + str(len(cuestiones)-1) +"]"
    s = s + "{" + codchar(nombre) + "-" + str(variante) + "}\n"
    s = s + "    " + enunciado + "\n"
    
    for c in cuestiones:
        fb = c[3] if len(c) > 3 else ''
        s = s + (' ' * 7) + (itemBuena(fb) if c[1] else itemMala(fb)) + codchar(c[0]) + '\n'
    
    s = s + " \\end{multi}\n\n"
    return s
