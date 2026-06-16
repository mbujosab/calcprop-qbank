"""Tests para las funciones de exportación de alto nivel (QuizMoodle, etc.)."""
import tempfile
from pathlib import Path

import pytest
from qbank import (
    Cuestion,
    ProblemaTipo,
    QuizAMCProfe,
    QuizMoodle,
    QuizMoodleProfe,
    Supuesto,
    codchar,
    v,
)


# ---------------------------------------------------------------------------
# Fixture compartida
# ---------------------------------------------------------------------------

@pytest.fixture()
def problema_simple():
    """ProblemaTipo mínimo con dos supuestos y dos cuestiones."""
    return ProblemaTipo([
        "Considere ",
        [Supuesto(r"$\mathcal{A}$ ", v("A")), Supuesto(r"$\mathcal{B}$ ", v("B"))],
        "Indique qué opción es correcta: ",
        [
            Cuestion(r"Entonces $\mathcal{A}$ es verdadero", v("A")),
            Cuestion(r"Entonces $\mathcal{B}$ es verdadero", v("B")),
        ],
    ])


@pytest.fixture()
def problema_dict(problema_simple):
    """Dict {nombre: ProblemaTipo} con dos entradas."""
    return {"pA": problema_simple, "pB": problema_simple}


# ---------------------------------------------------------------------------
# QuizMoodle — valor de retorno
# ---------------------------------------------------------------------------

class TestQuizMoodleReturn:
    def test_devuelve_int(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            resultado = QuizMoodle("q", d + "/", problema_simple)
        assert isinstance(resultado, int)

    def test_devuelve_positivo(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            resultado = QuizMoodle("q", d + "/", problema_simple)
        assert resultado > 0

    def test_instances_multiplica_count(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            n1 = QuizMoodle("q", d + "/", problema_simple, instances=1)
        with tempfile.TemporaryDirectory() as d:
            n2 = QuizMoodle("q", d + "/", problema_simple, instances=2)
        assert n2 == 2 * n1

    def test_dict_acumula_count(self, problema_dict):
        with tempfile.TemporaryDirectory() as d:
            n_dict = QuizMoodle("q", d + "/", problema_dict)
        with tempfile.TemporaryDirectory() as d:
            n_uno = QuizMoodle("q", d + "/", next(iter(problema_dict.values())))
        assert n_dict == 2 * n_uno


# ---------------------------------------------------------------------------
# QuizMoodle — kwargs nuevos (aux_latex, last_choice_text)
# ---------------------------------------------------------------------------

class TestQuizMoodleKwargs:
    def test_aux_latex_aparece_en_fichero(self, problema_simple):
        paquete = r"\usepackage{nacal-moodle}"
        with tempfile.TemporaryDirectory() as d:
            QuizMoodle("q", d + "/", problema_simple, aux_latex=paquete)
            contenido = Path(d, "q.tex").read_text()
        assert paquete in contenido

    def test_last_choice_text_aparece_en_fichero(self, problema_simple):
        texto = "Las demás alternativas son incorrectas"
        with tempfile.TemporaryDirectory() as d:
            QuizMoodle("q", d + "/", problema_simple,
                       last_choice=True, last_choice_text=texto)
            contenido = Path(d, "q.tex").read_text()
        assert codchar(texto) in contenido

    def test_sin_last_choice_no_aparece_texto(self, problema_simple):
        texto = "Las demás alternativas son incorrectas"
        with tempfile.TemporaryDirectory() as d:
            QuizMoodle("q", d + "/", problema_simple,
                       last_choice=False, last_choice_text=texto)
            contenido = Path(d, "q.tex").read_text()
        assert codchar(texto) not in contenido


# ---------------------------------------------------------------------------
# QuizMoodleProfe — valor de retorno y kwargs
# ---------------------------------------------------------------------------

class TestQuizMoodleProfe:
    def test_devuelve_int_positivo(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            resultado = QuizMoodleProfe("q", d + "/", problema_simple)
        assert isinstance(resultado, int) and resultado > 0

    def test_mismo_count_que_quizmoodle(self, problema_simple):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            n_alum = QuizMoodle("q", d1 + "/", problema_simple)
            n_prof = QuizMoodleProfe("q", d2 + "/", problema_simple)
        assert n_alum == n_prof

    def test_aux_latex_aparece_en_fichero(self, problema_simple):
        paquete = r"\usepackage{nacal-moodle}"
        with tempfile.TemporaryDirectory() as d:
            QuizMoodleProfe("q", d + "/", problema_simple, aux_latex=paquete)
            contenido = Path(d, "q.tex").read_text()
        assert paquete in contenido


# ---------------------------------------------------------------------------
# QuizAMCProfe — valor de retorno y kwargs
# ---------------------------------------------------------------------------

class TestQuizAMCProfe:
    def test_devuelve_int_positivo(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            resultado = QuizAMCProfe("q", d + "/", problema_simple)
        assert isinstance(resultado, int) and resultado > 0

