"""Tests de la plantilla de proyecto (qbank-init) y de la autoría en Python:
setup como cadena, semántica/precond como cadena y nombre= en ProblemaTipo."""
import shutil
import subprocess
import sys

import pytest
from qbank import (AMC_multipart, Cuestion, ProblemaTipo, QuizAMCProfe, Supuesto, lint,
                   load_problema, problema_to_dict, save_problema, v)
from qbank._lint import AVISO, ERROR, INFO
from qbank._plantilla import crear, main, ruta_plantilla


# ---------------------------------------------------------------------------
# Autoría en Python
# ---------------------------------------------------------------------------

def test_setup_y_expresiones_como_cadena_se_serializan(tmp_path):
    p = ProblemaTipo(
        ["Sea $x = @{x}$. ",
         [Supuesto("Positivo.", v('pos'), precond="lambda ns: ns['x'] > 0"),
          Supuesto("Negativo.", "v('neg')", precond="lambda ns: ns['x'] < 0")],
         " Entonces:",
         [Cuestion("$x^3 > 0$", "v('pos')"), Cuestion("$x^3 < 0$", v('neg'))],
         Cuestion("$x^2 > 0$", "True"),
         Cuestion("$x = 0$", False)],
        setup="import numpy as np\nx = int(np.random.choice([-2, 3]))",
        seed=1, export={"last_choice": True}, nombre="p")
    d = problema_to_dict(p)
    assert d["nombre"] == "p" and d["seed"] == 1
    assert d["setup"].startswith("import numpy")
    assert d["componentes"][1][0]["precond"] == "lambda ns: ns['x'] > 0"
    assert d["componentes"][1][1]["semantica"] == "v('neg')"
    assert d["componentes"][3][0]["semantica"] == "v('pos')"
    assert d["componentes"][3][1]["semantica"] == "v('neg')"      # repr de calcprop
    assert d["componentes"][4]["semantica"] == "True"
    assert d["componentes"][5]["semantica"] == "False"
    ruta = tmp_path / "p.json"
    save_problema(p, ruta)
    assert problema_to_dict(load_problema(str(ruta))) == d
    assert len(list(load_problema(str(ruta)).por_partes(instances=2))) > 0


def test_setup_cadena_vacia_equivale_a_ninguno():
    p = ProblemaTipo(["a", Cuestion("b", True)], setup="  \n")
    assert p.setup is None and problema_to_dict(p)["setup"] is None


def test_setup_conserva_la_cadena_y_admite_indentacion():
    codigo = "    x = 1\n    y = x + 1\n"
    p = ProblemaTipo(["$@{y}$", Cuestion("b", True)], setup=codigo)
    assert problema_to_dict(p)["setup"] == codigo            # tal cual, con su \n final
    assert next(iter(p.por_partes()))[1][0][0] == "$2$"       # dedent al ejecutar


def test_expresiones_raras_dan_error_con_contexto():
    assert Cuestion("x", "true").s is True and Cuestion("x", " FALSE ").s is False
    with pytest.raises(ValueError, match="Cuestion 'Sea A', campo semantica: expresión vacía"):
        Cuestion("Sea A", "")
    with pytest.raises(ValueError, match=r"campo precond: no se puede evaluar 'v\(A\)'"):
        Supuesto("s", "True", precond="v(A)")


def test_exp_none_se_guarda_como_null():
    assert problema_to_dict(ProblemaTipo(["a", Cuestion("b", True, exp=None)]))["componentes"][1]["exp"] is None


def test_problema_to_python_vuelve_a_guardarse(tmp_path):
    from qbank import problema_to_python
    p = ProblemaTipo(["Sea $x = @{x}$. ",
                      [Supuesto("Positivo.", v('pos'), precond="lambda ns: ns['x'] > 0"),
                       Supuesto("Negativo.", v('neg'), precond="lambda ns: ns['x'] < 0")],
                      [Cuestion("$x^3 > 0$", v('pos')), Cuestion("$x^3 < 0$", "lambda ns: ns['x'] < 0",
                                                                  exp="porque @{x} < 0")]],
                     setup="import numpy as np\nx = int(np.random.choice([-2, 3]))\n",
                     seed=3, export={"last_choice": True}, nombre="L-00-P")
    d = problema_to_dict(p)
    codigo = problema_to_python(p)
    assert "_SETUP = r\"\"\"" in codigo and "nombre='L-00-P'" in codigo
    ns = {}
    exec(codigo, ns)
    assert problema_to_dict(ns["p"]) == d


def test_setup_callable_sigue_sin_serializarse():
    p = ProblemaTipo(["a", Cuestion("b", True)], setup=lambda: {})
    with pytest.raises(ValueError, match="cadena"):
        problema_to_dict(p)


def test_lambda_python_en_precond_no_se_serializa():
    p = ProblemaTipo(["a", Cuestion("b", True, precond=lambda ns: True)])
    with pytest.raises(ValueError, match="cadena"):
        problema_to_dict(p)
    p = ProblemaTipo(["a", Cuestion("b", True, exp=lambda ns: "x")])
    with pytest.raises(ValueError, match="exp"):
        problema_to_dict(p)


def test_precond_cadena_se_muestra_legible_al_rechazar(capsys):
    p = ProblemaTipo(["Sea $x=@{x}$ ", [Supuesto("pos.", v('p'), precond="lambda ns: ns['x'] > 0"),
                                        Supuesto("neg.", v('n'), precond="lambda ns: ns['x'] < 0")],
                      Cuestion("c", v('p'))], setup="x = 1")
    list(p.por_partes(verbose=True))
    assert "rechazado por lambda ns: ns['x'] < 0" in capsys.readouterr().out


def test_lint_no_marca_huerfanas_con_supuesto_lambda():
    p = ProblemaTipo(["Sea $x=@{x}$. ",
                      Supuesto("", "lambda ns: v('gt') if ns['x'] > 3 else -v('gt')"),
                      Cuestion("$x > 3$", "v('gt')"), Cuestion("$x \\le 3$", "-v('gt')"),
                      Cuestion("$x < 0$", False)],
                     setup="import numpy as np\nx = int(np.random.randint(0, 8))", seed=1,
                     export={"last_choice": True, "instances": 8})
    av = lint(p)
    assert not [a for a in av if a.codigo == "huerfana" and a.nivel == AVISO]
    assert [a for a in av if a.codigo == "huerfana" and a.nivel == INFO]


# ---------------------------------------------------------------------------
# Multiparte en AMC
# ---------------------------------------------------------------------------

def test_amc_multipart_un_questionmult_con_un_bloque_por_parte():
    p = ProblemaTipo(["Sea $A$ ", [Supuesto("invertible.", v('inv')), Supuesto("singular.", v('sing'))],
                      " Determinante:", Cuestion("$\\det A \\neq 0$", v('inv')), Cuestion("$\\det A = 0$", v('sing')),
                      " Sistema:", Cuestion("solución única", v('inv')), Cuestion("infinitas", v('sing'))],
                     export={"last_choice": True, "cols": 2}, nombre="M")
    etiqueta, partes = next(iter(p.por_partes()))
    assert len(partes) == 2
    tex = AMC_multipart("M", etiqueta, "", partes, last_choice=True, cols=2)
    assert tex.count(r"\begin{questionmult}") == 1 and r"{M-1}" in tex
    assert tex.count(r"\begin{choices}") == 2 and tex.count(r"\lastchoices") == 2
    assert tex.count(r"\begin{multicols}{2}") == 2
    assert "Sea $A$ invertible. Determinante:" in tex and r"\emph{Sistema:}" in tex
    # vista profe: las rechazadas de todas las partes en un solo \explain
    etiqueta, partes = next(iter(p.por_partes_profe(verbose=False)))
    assert AMC_multipart("M", etiqueta, "", partes, profe=True).count(r"\end{questionmult}") == 1
    # QuizAMCProfe usa AMC_multipart: una pregunta por variante; con last_choice
    # cada parte lleva la opción por defecto
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        n = QuizAMCProfe("M", d + "/", p, last_choice=True, last_choice_text="ZZZ")
        tex = open(d + "/M_profe.tex").read()
    assert n == 2 and tex.count(r"\begin{questionmult}") == 2 and tex.count("ZZZ") == 4
    # compatibilidad: opc=[aux] y enunciado común no vacío (las intros van en \emph)
    tex = AMC_multipart("M", "1", "Común.", partes, opc=[r"\relax"])
    assert r"{\relax" in tex and "Común." in tex and r"\emph{Sea $A$" in tex


def test_lint_parte_vacia_no_aconseja_sobre_listas():
    av = lint(_d(["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")],
                  _C("A", "v('A')"), _C("B", "v('B')"), _C("ni", "False"), " Y además:"]))
    assert [a for a in av if a.codigo == "opciones" and "parte vacía" in a.mensaje]
    assert not [a for a in av if a.codigo == "pocas-opciones"]


# ---------------------------------------------------------------------------
# Regla de lint «pocas-opciones»
# ---------------------------------------------------------------------------

def _C(enunciado, semantica):
    return {"tipo": "Cuestion", "enunciado": enunciado, "semantica": semantica,
            "precond": "True", "exp": ""}


def _S(enunciado, semantica):
    return {"tipo": "Supuesto", "enunciado": enunciado, "semantica": semantica, "precond": "True"}


def _d(componentes):
    return {"version": "1", "tipo": "ProblemaTipo", "nombre": "p", "setup": None,
            "export": {"last_choice": True}, "componentes": componentes}


def test_lint_avisa_si_las_opciones_van_en_una_sola_lista():
    # error típico: una única lista de tres Cuestion creyendo que se muestran juntas
    av = lint(_d(["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")],
                  [_C("A", "v('A')"), _C("B", "v('B')"), _C("ni A ni B", "False")]]))
    pocas = [a for a in av if a.codigo == "pocas-opciones"]
    assert pocas and pocas[0].nivel == AVISO and "sortea" in pocas[0].mensaje


def test_lint_no_avisa_con_tres_elementos_consecutivos():
    av = lint(_d(["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")],
                  _C("A", "v('A')"), _C("B", "v('B')"), _C("ni A ni B", "False")]))
    assert not [a for a in av if a.codigo == "pocas-opciones"]


# ---------------------------------------------------------------------------
# Plantilla
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def proyecto(tmp_path_factory):
    return crear(tmp_path_factory.mktemp("banco") / "mi-banco")


def _run(proyecto, *args):
    r = subprocess.run([sys.executable, *args], cwd=proyecto, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def test_crear_copia_la_plantilla(proyecto):
    assert ruta_plantilla().is_dir()
    for f in ["Makefile", "README.org", "config.py", "nueva_pregunta.py", ".gitignore",
              "scripts/_comun.py", "scripts/gen_amc.py", "scripts/gen_amc_student.py",
              "scripts/gen_moodle.py", "scripts/merge_moodle_xml.py", "scripts/fix_moodle_xml.py",
              "scripts/gen_lectura.py",
              "CLAUDE.md", "prompts/PROMPT-qbank-generico.org", "prompts/PROMPT-proyecto.org"]:
        assert (proyecto / f).is_file(), f
    assert len(list((proyecto / "preguntas").glob("L-*.json"))) == 5


def test_no_sobreescribe_sin_forzar(proyecto):
    with pytest.raises(FileExistsError):
        crear(proyecto)
    assert crear(proyecto, forzar=True) == proyecto


def test_main_cli(tmp_path, capsys):
    assert main([str(tmp_path / "b")]) == 0
    assert "make lint" in capsys.readouterr().out
    assert main([str(tmp_path / "b")]) == 1
    (tmp_path / "f").write_text("x")
    assert main([str(tmp_path / "f")]) == 1                  # el destino es un fichero
    assert "qbank-init:" in capsys.readouterr().err


def test_lecciones_invalidas_y_nombres_raros(proyecto):
    r = subprocess.run([sys.executable, "scripts/_comun.py", "--leccion", "3-"],
                       cwd=proyecto, capture_output=True, text=True)
    assert r.returncode != 0 and "formato no válido" in r.stderr
    assert len(_run(proyecto, "scripts/_comun.py", "--leccion", " ").split()) == 5
    raro = proyecto / "preguntas" / "L-07-Con Espacio.json"
    raro.write_text("{}")
    r = subprocess.run([sys.executable, "scripts/_comun.py"], cwd=proyecto, capture_output=True, text=True)
    raro.unlink()
    assert "se ignora L-07-Con Espacio.json" in r.stderr and len(r.stdout.split()) == 5


@pytest.mark.skipif(shutil.which("make") is None, reason="sin make")
def test_make_sin_preguntas_termina(proyecto):
    r = subprocess.run(["make", "amc", "LECCION=9", f"PYTHON={sys.executable}"],
                       cwd=proyecto, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    r = subprocess.run(["make", "lint", f"PYTHON={sys.executable}"],
                       cwd=proyecto, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    r = subprocess.run(["make", "lint", "PYTHON=/bin/false"],
                       cwd=proyecto, capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and "qbank no está instalado" in r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("make") is None, reason="sin make")
def test_make_lint_y_tabla_comodos(proyecto):
    def make(*args):
        return subprocess.run(["make", *args, f"PYTHON={sys.executable}"],
                              cwd=proyecto, capture_output=True, text=True, timeout=60)
    r = make("lint", "LECCION=9")                       # lección sin preguntas
    assert r.returncode == 0 and "no hay preguntas" in r.stdout, r.stdout + r.stderr
    for pregunta in ("L-01-FuncionMonotona", "L-01-FuncionMonotona.json",
                     "preguntas/L-01-FuncionMonotona.json"):
        r = make("tabla", f"PREGUNTA={pregunta}")
        assert r.returncode == 0 and "Mundos:" in r.stdout, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("make") is None, reason="sin make")
def test_make_rechaza_un_qbank_antiguo(proyecto, tmp_path):
    # Un intérprete que carga un qbank viejo (como el python3 del sistema con un
    # qbank 0.3 en ~/.local) debe dar el mensaje de PYTHON=, no fallar después.
    for version, con_lint in (("0.5.0", True), (None, False)):
        falso = tmp_path / f"falso-{version}"
        (falso / "qbank").mkdir(parents=True)
        (falso / "qbank" / "__init__.py").write_text(
            f"__version__ = {version!r}\n" if version else "")
        if con_lint:
            (falso / "qbank" / "lint.py").write_text("")
        py = tmp_path / f"python-{version}"
        py.write_text(f"#!/bin/sh\nPYTHONPATH={falso} exec {sys.executable} \"$@\"\n")
        py.chmod(0o755)
        r = subprocess.run(["make", "lint", f"PYTHON={py}"], cwd=proyecto,
                           capture_output=True, text=True, timeout=60)
        salida = r.stdout + r.stderr
        assert r.returncode != 0 and "anterior a la 0.6" in salida and "PYTHON=" in salida, salida


def test_gen_amc_cuenta_mundos_y_solo_casos_con_setup(proyecto):
    import json
    salida = _run(proyecto, "scripts/gen_amc.py")
    for ruta in sorted((proyecto / "preguntas").glob("L-*.json")):
        linea = next(l for l in salida.splitlines() if f"{ruta.stem}.tex" in l)
        con_setup = json.loads(ruta.read_text(encoding="utf-8")).get("setup") is not None
        assert "mundo(s)" in linea and ("caso(s)" in linea) == con_setup, linea


def test_nombre_con_guion_bajo_usa_el_grupo_sanitizado(proyecto):
    import json
    origen = proyecto / "preguntas" / "L-01-ParidadSumaProducto.json"
    d = json.loads(origen.read_text()); d["nombre"] = "L-08-Con_Guion"
    (proyecto / "preguntas" / "L-08-Con_Guion.json").write_text(json.dumps(d, ensure_ascii=False))
    try:
        _run(proyecto, "scripts/gen_amc.py", "--leccion", "8")
        doc = (proyecto / "build/amc/L-08-Con_Guion-doc.tex").read_text()
        tex = (proyecto / "build/amc/L-08-Con_Guion.tex").read_text()
        assert r"\input{L-08-Con_Guion}" in doc and r"\insertgroup{L-08-Con-Guion}" in doc
        assert r"\element{L-08-Con-Guion}" in tex
    finally:
        (proyecto / "preguntas" / "L-08-Con_Guion.json").unlink()


def test_gen_amc_falla_si_una_pregunta_no_tiene_variantes(proyecto):
    import json
    d = {"version": "1", "tipo": "ProblemaTipo", "nombre": "L-09-Imposible",
         "setup": "x = 1", "export": {"last_choice": True},
         "componentes": ["Sea ", {"tipo": "Supuesto", "enunciado": "grande.", "semantica": "True",
                                  "precond": "lambda ns: ns['x'] > 5"},
                         _C("a", "True"), _C("b", "False"), _C("c", "False")]}
    ruta = proyecto / "preguntas" / "L-09-Imposible.json"
    ruta.write_text(json.dumps(d))
    try:
        r = subprocess.run([sys.executable, "scripts/gen_amc.py", "--leccion", "9"],
                           cwd=proyecto, capture_output=True, text=True)
        assert r.returncode == 1 and "ninguna variante" in r.stdout
    finally:
        ruta.unlink()


def test_merge_solo_las_preguntas_existentes(proyecto):
    moodle = proyecto / "build" / "moodle"
    moodle.mkdir(parents=True, exist_ok=True)
    nombres = [p.stem for p in (proyecto / "preguntas").glob("L-*.json")]
    for n in nombres[:2] + ["L-09-Borrada"]:
        (moodle / f"{n}-moodle.xml").write_text(f"<quiz><question>{n}</question></quiz>", encoding="iso-8859-1")
    out = _run(proyecto, "scripts/merge_moodle_xml.py")
    banco = (moodle / "_banco.xml").read_text(encoding="iso-8859-1")
    assert "L-09-Borrada" not in banco and all(n in banco for n in nombres[:2])
    assert "AVISO: sin XML" in out
    for f in moodle.glob("*-moodle.xml"):
        f.unlink()


def test_lint_texto_porcentajes_y_comillas():
    base = ["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")]]
    def codigos(*cs):
        return {(a.nivel, a.mensaje.split(":")[0].split(" (")[0]) for a in lint(_d(base + list(cs))) if a.codigo == "texto"}
    assert (ERROR, "'%' sin barra") in codigos(_C("un 25 % del valor", "v('A')"), _C("b", "v('B')"), _C("c", "False"))
    assert not codigos(_C("un 25 \\% del valor", "v('A')"), _C("b", "v('B')"), _C("c", "False"))
    assert (AVISO, "'\\%' dentro de $...$") in codigos(_C("al $5\\,\\%$", "v('A')"), _C("b", "v('B')"), _C("c", "False"))
    assert not codigos(_C("al $5$\\,\\% y $x$", "v('A')"), _C("b", "v('B')"), _C("c", "False"))
    assert (AVISO, "comillas rectas \"") in codigos(_C('la "gran depresión"', "v('A')"), _C("b", "v('B')"), _C("c", "False"))
    assert not codigos(_C("la ``gran depresión''", "v('A')"), _C("b", "v('B')"), _C("c", "False"))


def test_fix_moodle_xml_codificacion():
    import importlib.util
    ruta = ruta_plantilla() / "scripts" / "fix_moodle_xml.py"
    spec = importlib.util.spec_from_file_location("fix_moodle_xml", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    datos = '<?xml version="1.0" encoding="iso-8859-1"?>\n<quiz><q>¿Qu&eacute; “pasa”?</q></quiz>'.encode("utf-8")
    texto, cambio = mod.arregla_codificacion(mod.decodifica(datos))
    assert cambio and texto.startswith('<?xml version="1.0" encoding="utf-8"?>') and "¿Qu&eacute; “pasa”?" in texto
    assert mod.decodifica("caf\xe9".encode("iso-8859-1")) == "café"


def test_fix_moodle_xml_arregla():
    import importlib.util
    ruta = ruta_plantilla() / "scripts" / "fix_moodle_xml.py"
    spec = importlib.util.spec_from_file_location("fix_moodle_xml", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    texto = r"intro &lt; fuera {1:MULTIRESPONSE_S:=\(a &lt; b\)#f \} g~x &lt; y} fin &lt;"
    nuevo, n = mod.arregla(texto)
    assert n == 2 and nuevo.count("&amp;lt;") == 2 and nuevo.startswith("intro &lt;") and nuevo.endswith("fin &lt;")


def test_preguntas_de_ejemplo_pasan_lint_sin_avisos(proyecto):
    for ruta in sorted((proyecto / "preguntas").glob("L-*.json")):
        av = [a for a in lint(str(ruta)) if a.nivel in (ERROR, AVISO)]
        assert not av, (ruta.name, av)


def test_listado_por_leccion(proyecto):
    nombres = _run(proyecto, "scripts/_comun.py", "--leccion", "2").split()
    assert nombres and all(n.startswith("L-02-") for n in nombres)
    assert len(_run(proyecto, "scripts/_comun.py").split()) == 5


def test_scripts_generan_tex(proyecto):
    _run(proyecto, "scripts/gen_amc.py")
    _run(proyecto, "scripts/gen_amc_student.py", "--leccion", "1")
    _run(proyecto, "scripts/gen_moodle.py")
    nombres = sorted(p.stem for p in (proyecto / "preguntas").glob("L-*.json"))
    for n in nombres:
        assert r"\element{" in (proyecto / "build/amc" / f"{n}.tex").read_text()
        assert r"\insertgroup" in (proyecto / "build/amc" / f"{n}-doc.tex").read_text()
        assert r"\end{quiz}" in (proyecto / "build/moodle" / f"{n}.tex").read_text()
        existe = (proyecto / "build/amc-student" / f"{n}-doc.tex").exists()
        assert existe == n.startswith("L-01-"), n
    assert (proyecto / "build/amc/_catalogo.tex").read_text().count(r"\input") == 5
    # los setups se exploran por sorteos: la vista profe de una pregunta con setup
    # imprime varios casos etiquetados mundoN-casoK
    assert "mundo1-caso1" in (proyecto / "build/amc/L-02-ComparacionNumerica.tex").read_text()
    # multiparte: un questionmult por variante con dos bloques de casillas, y las
    # explicaciones en cursiva en la vista profe
    profe = (proyecto / "build/amc/L-02-MatrizInvertible.tex").read_text()
    assert profe.count(r"\begin{questionmult}") == 2 and profe.count(r"\begin{choices}") == 4
    assert r"\footnotesize\itshape" in profe
    _run(proyecto, "scripts/gen_amc_student.py", "--leccion", "2")
    alumno = (proyecto / "build/amc-student/L-02-MatrizInvertible.tex").read_text()
    assert alumno.count(r"\begin{questionmult}") == alumno.count(r"\begin{choices}") // 2
    assert "{L-02-MatrizInvertible-1}" in alumno and alumno.count("{L-02-MatrizInvertible-1}") == 1
    # segunda pasada: nada cambia, no se reescribe (y make no recompila)
    assert "sin cambios" in _run(proyecto, "scripts/gen_amc.py")


def test_nueva_pregunta_guarda_un_json_valido(proyecto):
    salida = _run(proyecto, "nueva_pregunta.py")
    assert "vista profe" in salida and "lint" in salida
    _run(proyecto, "nueva_pregunta.py", "--guardar")
    ruta = proyecto / "preguntas" / "L-00-SignoYCuadrado.json"
    assert ruta.exists()
    av = [a for a in lint(str(ruta)) if a.nivel == ERROR]
    assert not av, av
    ruta.unlink()


# ---------------------------------------------------------------------------
# Hallazgos de la auditoría de lint y reproducibilidad
# ---------------------------------------------------------------------------

def test_tabla_de_mundos_solo_usa_los_supuestos_anteriores():
    from qbank import tabla_mundos
    p = ProblemaTipo(["Parte 1. ", [Supuesto("A.", v('A')), Supuesto("B.", v('B'))],
                      Cuestion("¿C?", v('C')), Cuestion("¿A?", v('A')), Cuestion("x", False),
                      " Parte 2, ahora con C. ", Supuesto("", v('C')),
                      Cuestion("¿C ahora?", v('C')), Cuestion("y", False), Cuestion("z", False)],
                     export={"last_choice": True})
    tabla = tabla_mundos(p)
    fila_c = [l for l in tabla.splitlines() if "¿C?" in l][0]
    assert fila_c.rstrip().endswith("F  F")          # como el motor: C aún no es hipótesis
    av = [a for a in lint(p) if a.codigo == "constante" and "¿C?" in (a.donde or "")]
    assert av and av[0].mensaje.startswith("falsa")  # y no «verdadera», como decía antes


def test_seed_siembra_tambien_el_modulo_random_y_base_seed_con_una_instancia():
    p = ProblemaTipo(["$@{x}$ ", Cuestion("a", True), Cuestion("b", False), Cuestion("c", False)],
                     setup="import random\nx = random.randint(1, 10**6)", seed=5,
                     export={"last_choice": True})
    def xs(**kw):
        return [partes[0][0] for _, partes in p.por_partes(**kw)]
    assert xs() == xs()                                           # seed cubre random
    assert xs(instances=2) == xs(instances=2)
    assert xs(base_seed=1) == xs(base_seed=1) and xs(base_seed=1) != xs(base_seed=2)


def test_claves_propias_del_json_se_conservan():
    d = _d(["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")],
            _C("A", "v('A')"), _C("B", "v('B')"), _C("ni", "False")])
    d["_nivel"] = "M"
    d["_tema"] = {"bloque": 2}
    d2 = problema_to_dict(load_problema(d))
    assert d2["_nivel"] == "M" and d2["_tema"] == {"bloque": 2}


def test_lint_no_revienta_con_export_mal_tipado():
    d = _d(["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")],
            _C("A", "v('A')"), _C("B", "v('B')"), _C("ni", "False")])
    d["setup"] = "x = 1"
    d["export"] = {"instances": "diez", "last_choice": "false", "cols": "2"}
    d["seed"] = "7"
    msgs = [a.mensaje for a in lint(d) if a.codigo == "estructura" and a.nivel == ERROR]
    assert any("instances" in m for m in msgs) and any("last_choice" in m for m in msgs)
    assert any("cols" in m for m in msgs) and any("seed" in m for m in msgs)


def test_negacion_deducible_no_es_error():
    def errores(*comps):
        return [a for a in lint(_d(list(comps))) if a.codigo == "negacion" and a.nivel == ERROR]
    mundos = [_S("A.", "v('A')"), _S("B.", "v('B')")]
    huecos = [_C("no B", "-v('B')"), _C("A", "v('A')"), _C("x", "False")]
    assert errores("Sea ", mundos, *huecos)                                   # sin axioma: ERROR
    assert not errores("Sea ", mundos, _S("", "v('C') & unoDe(v('A'), v('B'))"), *huecos)
    assert not errores("Sea ", mundos, _S("", "v('A') >> -v('B')"), *huecos)
    assert not errores("Sea ", [_S("A.", "v('A') & unoDe(v('A'), v('B'))"),
                                _S("B.", "v('B') & unoDe(v('A'), v('B'))")], *huecos)


def test_sin_uso_calla_si_hay_cuestiones_lambda():
    p = ProblemaTipo(["Sea $x=@{x}$. ", [Supuesto("A.", v('A')), Supuesto("B.", v('B'))],
                      Cuestion("lam", "lambda ns: v('A') if ns['x'] else v('B')"),
                      Cuestion("a", v('A')), Cuestion("x", False)],
                     setup="x = 1", export={"last_choice": True})
    assert not [a for a in lint(p) if a.codigo == "sin-uso"]


def test_doble_espacio_dentro_de_formulas_no_avisa():
    base = ["Sea ", [_S("A.", "v('A')"), _S("B.", "v('B')")]]
    av = lint(_d(base + [_C("$H_1:\\beta_2   > 0$", "v('A')"), _C("b", "v('B')"), _C("c", "False")]))
    assert not [a for a in av if "doble espacio" in a.mensaje]
    av = lint(_d(base + [_C("texto  con  dobles", "v('A')"), _C("b", "v('B')"), _C("c", "False")]))
    assert [a for a in av if "doble espacio" in a.mensaje]


def test_arroba_doble_es_arroba_literal_tambien_sin_setup():
    p = ProblemaTipo(["Escribe a nombre@@dominio.es ", Cuestion("a", True), Cuestion("b", False),
                      Cuestion("c", False)])
    assert next(iter(p.por_partes()))[1][0][0].startswith("Escribe a nombre@dominio.es")


def test_tabla_de_mundos_es_reproducible_con_setup():
    from qbank import tabla_mundos
    p = ProblemaTipo(["Sea $x = @{x}$. ", [Supuesto("A.", v('A')), Supuesto("B.", v('B'))],
                      Cuestion("$x$ par", "lambda ns: ns['x'] % 2 == 0"), Cuestion("a", v('A')),
                      Cuestion("z", False)],
                     setup="import numpy as np\nx = int(np.random.randint(1, 10**6))", seed=4,
                     export={"last_choice": True})
    assert len({tabla_mundos(p) for _ in range(10)}) == 1


def test_exportadores_aceptan_directorio_sin_barra(tmp_path):
    from qbank import QuizMoodle
    p = ProblemaTipo(["Sea ", [Supuesto("A.", v('A')), Supuesto("B.", v('B'))],
                      Cuestion("a", v('A')), Cuestion("b", v('B')), Cuestion("c", False)],
                     export={"last_choice": True})
    QuizMoodle("q", str(tmp_path), p)
    QuizAMCProfe("q", str(tmp_path), p)
    assert (tmp_path / "q.tex").exists() and (tmp_path / "q_profe.tex").exists()


def test_gen_lectura_un_documento_por_leccion(proyecto):
    salida = _run(proyecto, "scripts/gen_lectura.py")
    assert "L-01-lectura.tex" in salida and "L-03-lectura.tex" in salida
    tex = (proyecto / "build/lectura/L-02-lectura.tex").read_text(encoding="utf-8")
    assert tex.startswith("\\documentclass") and tex.rstrip().endswith("\\end{document}")
    assert "\\section*{L-02-MatrizInvertible}" in tex and "\\section*{L-02-ComparacionNumerica}" in tex
    assert "Hueco 6" in tex                       # dos partes de tres huecos, numerados seguidos
    assert "\\qbV" in tex and "\\qbF" in tex
    assert "es-noshorthands" in tex               # el preámbulo del proyecto (config.PREAMBULO_AMC)
    # segunda ejecución: nada cambia (make no recompila)
    assert "sin cambios" in _run(proyecto, "scripts/gen_lectura.py", "--leccion", "2")
    assert "L-01" not in _run(proyecto, "scripts/gen_lectura.py", "--leccion", "2")
