"""Tests de la plantilla de proyecto (qbank-init) y de la autoría en Python:
setup como cadena, semántica/precond como cadena y nombre= en ProblemaTipo."""
import subprocess
import sys

import pytest
from qbank import (Cuestion, ProblemaTipo, Supuesto, lint, load_problema,
                   problema_to_dict, save_problema, v)
from qbank._lint import AVISO, ERROR
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


def test_setup_callable_sigue_sin_serializarse():
    p = ProblemaTipo(["a", Cuestion("b", True)], setup=lambda: {})
    with pytest.raises(ValueError, match="cadena"):
        problema_to_dict(p)


def test_lambda_python_en_precond_no_se_serializa():
    p = ProblemaTipo(["a", Cuestion("b", True, precond=lambda ns: True)])
    with pytest.raises(ValueError, match="cadena"):
        problema_to_dict(p)


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
              "scripts/gen_moodle.py", "scripts/merge_moodle_xml.py", "scripts/fix_moodle_xml.py"]:
        assert (proyecto / f).is_file(), f
    assert len(list((proyecto / "preguntas").glob("L-*.json"))) == 4


def test_no_sobreescribe_sin_forzar(proyecto):
    with pytest.raises(FileExistsError):
        crear(proyecto)
    assert crear(proyecto, forzar=True) == proyecto


def test_main_cli(tmp_path, capsys):
    assert main([str(tmp_path / "b")]) == 0
    assert "make lint" in capsys.readouterr().out
    assert main([str(tmp_path / "b")]) == 1


def test_preguntas_de_ejemplo_pasan_lint_sin_avisos(proyecto):
    for ruta in sorted((proyecto / "preguntas").glob("L-*.json")):
        av = [a for a in lint(str(ruta)) if a.nivel in (ERROR, AVISO)]
        assert not av, (ruta.name, av)


def test_listado_por_leccion(proyecto):
    nombres = _run(proyecto, "scripts/_comun.py", "--leccion", "2").split()
    assert nombres and all(n.startswith("L-02-") for n in nombres)
    assert len(_run(proyecto, "scripts/_comun.py").split()) == 4


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
        assert existe == n.startswith("L-01-")
    assert (proyecto / "build/amc/_catalogo.tex").read_text().count(r"\input") == 4
    # los setups se exploran por sorteos: la vista profe de una pregunta con setup
    # imprime varios casos etiquetados mundoN-casoK
    assert "mundo1-caso1" in (proyecto / "build/amc/L-02-ComparacionNumerica.tex").read_text()
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
