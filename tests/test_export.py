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


# ---------------------------------------------------------------------------
# Cuestion.exp — interpolación dinámica @{var} / lambda ns
# ---------------------------------------------------------------------------

class TestExpDinamico:
    def _problema_con_exp(self, exp):
        def setup():
            return {"a": 3, "b": 5}
        c = Cuestion("$@{a} + @{b} = 8$", lambda ns: ns["a"] + ns["b"] == 8, exp=exp)
        return ProblemaTipo(["Base ", [c]], setup=setup)

    def test_interpola_cadena_con_at_var(self):
        p = self._problema_con_exp("Porque @{a}+@{b}=8.")
        _, partes = next(p.por_partes())
        _, cuestiones = partes[0]
        assert cuestiones[0][3] == "Porque 3+5=8."

    def test_admite_lambda_ns(self):
        p = self._problema_con_exp(lambda ns: f"Porque {ns['a']}+{ns['b']}=8.")
        _, partes = next(p.por_partes())
        _, cuestiones = partes[0]
        assert cuestiones[0][3] == "Porque 3+5=8."

    def test_por_partes_profe_tambien_interpola(self):
        p = self._problema_con_exp("Porque @{a}+@{b}=8.")
        _, partes = next(p.por_partes_profe())
        _, cuestiones = partes[0]
        assert cuestiones[0][3] == "Porque 3+5=8."

    def test_exp_interpolado_llega_al_tex_exportado(self):
        p = self._problema_con_exp("Porque @{a}+@{b}=8.")
        with tempfile.TemporaryDirectory() as d:
            QuizMoodle("q", d + "/", p)
            contenido = Path(d, "q.tex").read_text()
        assert codchar("Porque 3+5=8.") in contenido



# ---------------------------------------------------------------------------
# Revisión de la Fase 3 (2026-10-19)
# ---------------------------------------------------------------------------

class TestOpcionPorDefectoVistaProfe:
    """En la vista profe una cuestión rechazada lleva en c[1] el motivo (una
    cadena, verdadera como valor lógico): no debe contar como correcta."""

    def test_rechazada_no_cuenta_como_correcta(self):
        from qbank import AMCblock
        cuestiones = [("a", False, 1, ""), ("b", False, 1, ""), ("c", "rechazada por x", 0)]
        s = AMCblock("X", "1", "E", cuestiones, last_choice=True, profe=True)
        assert r"\correctchoice{Ninguna de las anteriores}" in s

    def test_con_una_activa_verdadera_es_wrongchoice(self):
        from qbank import AMCblock
        cuestiones = [("a", True, 1, ""), ("b", False, 1, ""), ("c", "rechazada por x", 0)]
        s = AMCblock("X", "1", "E", cuestiones, last_choice=True, profe=True)
        assert "Ninguna de las anteriores" in s
        assert r"\correctchoice{Ninguna de las anteriores}" not in s

    def test_amc_multipart_igual(self):
        from qbank import AMC_multipart
        partes = [("P1", [("a", False, 1, ""), ("c", "rechazada por x", 0)]),
                  ("P2", [("b", True, 1, "")])]
        s = AMC_multipart("X", "1", "", partes, last_choice=True, profe=True)
        assert s.count(r"\correctchoice{Ninguna de las anteriores}") == 1


class TestQuizMoodleProfeLastChoiceInstances:
    @pytest.fixture()
    def con_setup(self):
        return ProblemaTipo([
            "Sea $x=@{x}$ ",
            [Supuesto("y A. ", v("A")), Supuesto("y B. ", v("B"))],
            Cuestion("A", v("A")), Cuestion("B", v("B")),
        ], setup="import numpy as np\nx = int(np.random.randint(100))", seed=3)

    def test_last_choice_anade_opcion_por_defecto(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            QuizMoodleProfe("q", d, problema_simple, last_choice=True)
            tex = (Path(d) / "q.tex").read_text()
        assert codchar("Las demás opciones son falsas") in tex

    def test_sin_last_choice_no_la_anade(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            QuizMoodleProfe("q", d, problema_simple)
            tex = (Path(d) / "q.tex").read_text()
        assert codchar("Las demás opciones son falsas") not in tex

    def test_last_choice_text(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            QuizMoodleProfe("q", d, problema_simple, last_choice=True,
                            last_choice_text="Ninguna es cierta")
            tex = (Path(d) / "q.tex").read_text()
        assert "Ninguna es cierta" in tex

    def test_opcion_por_defecto_correcta_si_ninguna_lo_es(self):
        # Mundo B con una única cuestión «A»: la opción por defecto es la correcta
        p = ProblemaTipo(["Sea ", [Supuesto("B. ", v("B"))], Cuestion("A", v("A")),
                          Cuestion("C", v("C"))])
        with tempfile.TemporaryDirectory() as d:
            QuizMoodleProfe("q", d, p, last_choice=True, last_choice_text="Ninguna")
            tex = (Path(d) / "q.tex").read_text()
        assert r"\item[fraction=100,\feedback={}]Ninguna" in tex

    def test_mismas_variantes_que_quizmoodle(self, con_setup):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            n_alu = QuizMoodle("q", d1, con_setup, last_choice=True, instances=3)
            n_pro = QuizMoodleProfe("q", d2, con_setup, last_choice=True, instances=3)
            alu = (Path(d1) / "q.tex").read_text()
            pro = (Path(d2) / "q.tex").read_text()
        assert n_alu == n_pro == 6
        import re
        enun = lambda t: re.findall(r"Sea \$x=\d+\$", t)
        assert enun(alu) == enun(pro)

    def test_solo_por_palabra_clave(self, problema_simple):
        with tempfile.TemporaryDirectory() as d:
            with pytest.raises(TypeError):
                QuizMoodleProfe("q", d, problema_simple, True)


# ---------------------------------------------------------------------------
# Codificación de los .tex (en Windows open() usa cp1252 por defecto)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("exportar,fichero", [
    (lambda d, p: QuizMoodle("q", d, p), "q.tex"),
    (lambda d, p: QuizMoodleProfe("q", d, p), "q.tex"),
    (lambda d, p: QuizAMCProfe("q", d, p), "q_profe.tex"),
])
def test_tex_en_utf8_aunque_el_sistema_no_lo_sea(monkeypatch, exportar, fichero):
    # codchar no convierte «¿»: llega tal cual al .tex y tiene que ir en UTF-8
    import builtins
    open_original = builtins.open

    def open_cp1252(f, mode="r", *args, **kw):
        if "b" not in mode and "encoding" not in kw and len(args) < 2:
            kw["encoding"] = "cp1252"
        return open_original(f, mode, *args, **kw)

    p = ProblemaTipo(["¿Qué ocurre? ", [Supuesto("A. ", v("A")), Supuesto("B. ", v("B"))],
                      Cuestion("A", v("A")), Cuestion("B", v("B")), Cuestion("C", False)])
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setattr(builtins, "open", open_cp1252)
        exportar(d, p)
        monkeypatch.undo()
        assert "¿Qu" in (Path(d) / fichero).read_text(encoding="utf-8")
