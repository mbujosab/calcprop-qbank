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
from qbank._quiz import _normaliza_slot, _clasifica_slot   # no los exporta el *

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
    with open(_os.path.join(directorio, nombre + ".tex"), "w", encoding="utf-8") as f:
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
    with open(_os.path.join(directorio, nombre + ".tex"), "w", encoding="utf-8") as f:
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
    int : número de entradas escritas (una pregunta AMC por mundo)
    """
    def creaDiccionario(x, key='key'):
        return x if isinstance(x, dict) else {key: x}
    problema = creaDiccionario(problema, nombre)
    count = 0
    with open(_os.path.join(directorio, nombre + "_profe.tex"), "w", encoding="utf-8") as f:
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
MAX_EJEMPLOS_LECTURA = 40     # ejemplos por pregunta, como mucho

_CIFRAS_RE = _re.compile(r'-?\d+(?:[.,]\d+)?')


def _ejemplos_lectura(p, extras=0, max_semillas=400):
    """Ejemplos de la vista de lectura de un problema.

    Devuelve (ejemplos, descartes, faltan): ejemplos es una lista de
    (mundo, valores, registro Lectura) ordenada por mundo y valores, donde
    valores es la tupla de (variable, repr(valor)) de lectura.cubrir;
    descartes, los textos de los mundos que un Supuesto descarta (con la
    semilla del problema); faltan, las combinaciones de cubrir que no han
    aparecido en ningún mundo tras max_semillas semillas."""
    lectura = p.lectura if isinstance(p.lectura, dict) else {}
    cubrir  = [v for v in lectura.get('cubrir', []) if isinstance(v, str)]
    vistos, descartes = {}, []
    def clave(r):
        return tuple((v, _valor_lectura(r.ns.get(v))) for v in cubrir)
    def guarda(r, k):
        if (r.mundo, k) not in vistos and len(vistos) < MAX_EJEMPLOS_LECTURA:
            vistos[(r.mundo, k)] = r
            return True
        return False
    for r in p.por_partes_lectura(descartes=True):
        if r.descarte is not None:
            if r.descarte not in descartes:
                descartes.append(r.descarte)
        else:
            guarda(r, clave(r))
    if p.setup is not None and cubrir:
        base = p.seed if p.seed is not None else 0
        for semilla in range(base + 1, base + max_semillas):
            for r in p.por_partes_lectura(seed=semilla):
                guarda(r, clave(r))
    elif p.setup is not None and extras:
        base = p.seed if p.seed is not None else 0
        enunciados = {(r.mundo, tuple(_CIFRAS_RE.sub('#', pa.enunciado) for pa in r.partes))
                      for r in vistos.values()}
        cuantos = {m: 0 for m, _ in vistos}
        for semilla in range(base + 1, base + max_semillas):
            if all(n >= extras for n in cuantos.values()):
                break
            for r in p.por_partes_lectura(seed=semilla):
                e = (r.mundo, tuple(_CIFRAS_RE.sub('#', pa.enunciado) for pa in r.partes))
                if e in enunciados or cuantos.get(r.mundo, 0) >= extras:
                    continue
                enunciados.add(e)
                if guarda(r, (('sorteo', semilla),)):
                    cuantos[r.mundo] = cuantos.get(r.mundo, 0) + 1
    ejemplos = sorted(((m, k, r) for (m, k), r in vistos.items()),
                      key=lambda x: (x[0], tuple(_orden_lectura(val) for _, val in x[1])))
    faltan = []
    if cubrir:
        import itertools as _it
        mundos = {m for m, _ in vistos}
        valores = {v: sorted({dict(k)[v] for _, k in vistos}) for v in cubrir}
        for m in sorted(mundos):
            for combo in _it.product(*(valores[v] for v in cubrir)):
                k = tuple(zip(cubrir, combo))
                if (m, k) not in vistos:
                    faltan.append((m, k))
    return ejemplos, descartes, faltan


def _valor_lectura(x):
    """Valor de una variable del setup tal como se muestra y se compara:
    los escalares (también los de numpy) por su str(); el resto por repr()."""
    if isinstance(x, (str, bool)) or x is None:
        return str(x)
    try:
        return str(x.item()) if hasattr(x, 'item') else str(x)
    except Exception:                                        # noqa: BLE001
        return repr(x)


def _orden_lectura(x):
    """Clave de ordenación: numérica si el valor lo es, alfabética si no."""
    try:
        return (0, float(str(x).replace(',', '.')), '')
    except ValueError:
        return (1, 0.0, str(x))


def _tex_lectura_escapa(s):
    """Escapa en texto LaTeX los caracteres de un valor del setup."""
    return (str(s).replace('\\', r'\textbackslash{}').replace('_', r'\_').replace('%', r'\%')
            .replace('&', r'\&').replace('#', r'\#').replace('$', r'\$').replace('{', r'\{')
            .replace('}', r'\}').replace('~', r'\textasciitilde{}').replace('^', r'\^{}'))


def _fecha_lectura():
    import datetime as _dt
    hoy = _dt.date.today()
    meses = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
             'septiembre', 'octubre', 'noviembre', 'diciembre')
    return f'{hoy.day} de {meses[hoy.month - 1]} de {hoy.year}'


def _tex_lectura_cabecera(titulo, aux_latex):
    return (
        '\\documentclass[11pt,a4paper]{article}\n'
        '\\usepackage[utf8]{inputenc}\n'
        '\\usepackage[T1]{fontenc}\n'
        '\\usepackage{amsmath,amssymb}\n'
        '\\usepackage[margin=2.2cm]{geometry}\n'
        '\\usepackage{xcolor,enumitem,graphicx}\n'
        + aux_latex.strip() + '\n'
        '\\definecolor{qbverde}{rgb}{0,0.5,0}\\definecolor{qbrojo}{rgb}{0.75,0,0}\n'
        '\\newcommand{\\qbV}{\\textbf{\\textcolor{qbverde}{V}}}\n'
        '\\newcommand{\\qbF}{\\textbf{\\textcolor{qbrojo}{F}}}\n'
        '\\newcommand{\\qbX}{\\textcolor{black!40}{--}}\n'
        '\\newcommand{\\qbExp}[1]{\\par\\vspace{1pt}{\\small\\color{black!65}\\emph{#1}}\\par}\n'
        '\\newcommand{\\qbRecuadro}[1]{\\noindent\\fbox{\\parbox{\\dimexpr\\linewidth-2\\fboxsep-2\\fboxrule}{#1}}}\n'
        '\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{4pt}\n'
        '\\title{' + titulo + '}\\date{' + _fecha_lectura() + '}\n'
        '\\begin{document}\\maketitle\n'
        'Un ejemplo por cada mundo de cada pregunta (y, si la pregunta lo pide, por cada '
        'combinación de valores de su \\texttt{setup}). En cada hueco el alumno recibe '
        '\\emph{una} de las alternativas listadas. \\qbV/\\qbF{} es el valor de verdad en ese '
        'ejemplo; debajo, en gris, la retroalimentación. Las alternativas que la precondición '
        'excluye en ese mundo van en gris claro, con su motivo.\n\n')


def _tex_lectura_pregunta(nombre, p, ejemplos, descartes, faltan, last_choice, last_choice_text):
    from qbank._lint import tabla_mundos
    L = ['\\clearpage\\section*{' + _tex_lectura_escapa(nombre) + '}\n']
    if ejemplos:
        n_huecos = [len(pa.huecos) for pa in ejemplos[0][2].partes]
        opciones = [n + (1 if last_choice else 0) for n in n_huecos]
        def plural(o):
            return f'{o} opción' if o == 1 else f'{o} opciones'
        if len(opciones) == 1:
            nota = 'El alumno ve ' + plural(opciones[0])
        else:
            nota = 'El alumno ve ' + ', '.join(f'{plural(o)} en la parte {k + 1}'
                                               for k, o in enumerate(opciones))
        if last_choice:
            nota += ('; la última' if len(opciones) > 1 or opciones[0] != n_huecos[0] + 1
                     else f'; la opción {opciones[0]}') + \
                    ' es «' + last_choice_text + '», correcta solo si las demás son falsas'
        L.append(nota + '.\n\n')
    try:
        # 96 caracteres: los que caben en \\footnotesize monoespaciada con margin=2.2cm.
        L.append('{\\footnotesize\\begin{verbatim}\n' + tabla_mundos(p, linea=96, elipsis='...')
                 + '\n\\end{verbatim}}\n')
    except Exception as e:                                   # noqa: BLE001
        L.append('{\\small\\color{black!65}(sin tabla de mundos: ' + _tex_lectura_escapa(e) + ')}\n\n')
    # Solo los slots de enunciado con más de una opción identifican el mundo.
    multi = [j for j, x in enumerate(x for x in p.e
                                     if _clasifica_slot(_normaliza_slot(x)) != 'cuestiones')
             if len(_normaliza_slot(x)) > 1]
    def nombre_mundo(mundo):
        return ('Mundo ' + '.'.join(str(mundo[j] + 1) for j in multi)) if multi else 'Mundo único'
    for mundo, valores, r in ejemplos:
        cab = nombre_mundo(mundo)
        if valores:
            cab += ' · ' + ' · '.join(f'{_tex_lectura_escapa(v)} = {_tex_lectura_escapa(x)}'
                                      for v, x in valores)
        L.append('\\subsection*{' + cab + '}\n')
        h = 0
        for k, pa in enumerate(r.partes):
            if pa.enunciado.strip():
                L.append('\\qbRecuadro{' + pa.enunciado.strip() + '}\\par\\medskip\n')
            for hueco in pa.huecos:
                h += 1
                L.append('\\par\\textbf{Hueco ' + str(h) + '}\\begin{itemize}[leftmargin=2.2em,itemsep=3pt]\n')
                prev = None
                for a in hueco:
                    if a.valor is None:
                        L.append('\\item[\\qbX] {\\color{black!40} ' + a.texto + ' --- '
                                 + _tex_lectura_escapa(a.motivo) + '}\n')
                        continue
                    exp = ('la misma retroalimentación que la anterior'
                           if a.exp and a.exp == prev else a.exp)
                    L.append('\\item[' + ('\\qbV' if a.valor else '\\qbF') + '] ' + a.texto
                             + ('\\qbExp{' + exp + '}' if exp else '') + '\n')
                    prev = a.exp
                L.append('\\end{itemize}\n')
    if descartes:
        L.append('\\par{\\small\\color{black!65}Mundos descartados: '
                 + '; '.join(_tex_lectura_escapa(d) for d in descartes) + '.}\n')
    if faltan:
        L.append('\\par{\\small\\color{black!65}Combinaciones no encontradas: '
                 + '; '.join(nombre_mundo(m) + ' con '
                             + ', '.join(f'{_tex_lectura_escapa(v)} = {_tex_lectura_escapa(x)}'
                                         for v, x in k) for m, k in faltan) + '.}\n')
    if not ejemplos:
        L.append('{\\color{qbrojo}Sin ninguna variante válida.}\n')
    return ''.join(L)


def QuizLectura(nombre, directorio, problemas, *, aux_latex="", titulo=None,
                last_choice=None, last_choice_text="Ninguna de las anteriores",
                extras=0, max_semillas=400):
    """Vista de lectura: escribe directorio/nombre.tex, un documento LaTeX
    completo con, por cada pregunta, un ejemplo por mundo (y por combinación
    de valores de lectura.cubrir), las alternativas por hueco con V/F y su
    exp, y las excluidas por precondición con su motivo.

    problemas        : ProblemaTipo, lista de ProblemaTipo (nombre = _nombre)
                       o dict {nombre: ProblemaTipo}
    aux_latex        : preámbulo del proyecto (macros, babel), como en AMC/Moodle
    titulo           : título del documento (por defecto, nombre)
    last_choice      : None lee export.last_choice de cada pregunta; True/False
                       lo fija para todas (solo afecta a la nota inicial)
    last_choice_text : texto de la opción por defecto en esa nota
    extras           : sin lectura.cubrir, sorteos extra por mundo con enunciado
                       distinto (solo con setup)
    max_semillas     : semillas que se recorren buscando combinaciones

    Devuelve el número de ejemplos escritos."""
    if isinstance(problemas, dict):
        pares = list(problemas.items())
    elif isinstance(problemas, (list, tuple)):
        pares = [(getattr(p, '_nombre', '') or f'pregunta{i + 1}', p) for i, p in enumerate(problemas)]
    else:
        pares = [(nombre, problemas)]
    total = 0
    partes = [_tex_lectura_cabecera(titulo if titulo is not None else _tex_lectura_escapa(nombre),
                                    aux_latex)]
    for nom, p in pares:
        ejemplos, descartes, faltan = _ejemplos_lectura(p, extras=extras, max_semillas=max_semillas)
        lc = (p.export.get('last_choice', False) if isinstance(p.export, dict) else False) \
             if last_choice is None else last_choice
        partes.append(_tex_lectura_pregunta(nom, p, ejemplos, descartes, faltan, lc, last_choice_text))
        total += len(ejemplos)
    partes.append('\\end{document}\n')
    with open(_os.path.join(directorio, nombre + '.tex'), 'w', encoding='utf-8') as f:
        f.write(''.join(partes))
    return total


def QuizVFMoodle(nombre, directorio, GenVar, num, opc=None):
    if opc is None:
        opc = ["", ""]
    auxLaTeX = opc[0]
    with open(_os.path.join(directorio, nombre + ".tex"), "w", encoding="utf-8") as f:
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
