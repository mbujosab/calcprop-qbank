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
    # codchar no convierte «»: llega tal cual al .tex y tiene que ir en UTF-8
    import builtins
    open_original = builtins.open

    def open_cp1252(f, mode="r", *args, **kw):
        if "b" not in mode and "encoding" not in kw and len(args) < 2:
            kw["encoding"] = "cp1252"
        return open_original(f, mode, *args, **kw)

    p = ProblemaTipo(["«Qué» ocurre. ", [Supuesto("A. ", v("A")), Supuesto("B. ", v("B"))],
                      Cuestion("A", v("A")), Cuestion("B", v("B")), Cuestion("C", False)])
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setattr(builtins, "open", open_cp1252)
        exportar(d, p)
        monkeypatch.undo()
        assert "«Qu" in (Path(d) / fichero).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Vista de lectura
# ---------------------------------------------------------------------------

def test_por_partes_lectura_agrupa_por_hueco(problema_simple):
    from qbank import Lectura
    rs = list(problema_simple.por_partes_lectura())
    assert len(rs) == 2 and all(isinstance(r, Lectura) for r in rs)
    assert [r.mundo for r in rs] == [(0, 0, 0), (0, 1, 0)]   # solo cambia el slot de Supuesto
    assert rs[0].ns == {} and rs[0].descarte is None
    (parte,) = rs[0].partes
    assert parte.enunciado.startswith("Considere")
    assert [len(h) for h in parte.huecos] == [2]                # un hueco de dos alternativas
    assert [a.valor for a in parte.huecos[0]] == [True, False]
    assert [a.valor for a in rs[1].partes[0].huecos[0]] == [False, True]


def test_por_partes_lectura_excluidas_y_descartes():
    p = ProblemaTipo([
        [Supuesto("A.", v("A")), Supuesto("B.", v("B"))],
        Supuesto("", v("C"), precond=v("A")),                  # descarta el mundo B
        [Cuestion("a", v("A")), Cuestion("solo si A", v("A"), precond=v("A"))],
    ])
    rs = list(p.por_partes_lectura(descartes=True))
    assert [r.descarte is None for r in rs] == [True, False]
    assert "rechazado por" in rs[1].descarte and rs[1].partes is None
    assert list(p.por_partes_lectura()) == rs[:1]
    p2 = ProblemaTipo([[Supuesto("A.", v("A")), Supuesto("B.", v("B"))],
                       [Cuestion("a", v("A")), Cuestion("solo si A", v("A"), precond=v("A"))]])
    mundo_b = list(p2.por_partes_lectura())[1]
    a = mundo_b.partes[0].huecos[0][1]
    assert a.valor is None and a.motivo.startswith("rechazada por") and a.exp == ""


def test_ejemplos_lectura_cubre_las_combinaciones():
    from qbank._export import _ejemplos_lectura
    p = ProblemaTipo([
        "Sea $x=@{a}$ (@{ctx}).", [Supuesto("Crece.", v("C")), Supuesto("Decrece.", -v("C"))],
        [Cuestion("$f(@{a})>f(0)$", "lambda ns: ns['a'] > 0", exp="Porque @{a}."),
         Cuestion("$f(@{a})<f(0)$", "lambda ns: ns['a'] < 0", exp="Porque @{a}.")],
    ], setup="import numpy as np\na = int(np.random.choice([-1, 1]))\nb = np.random.randint(0, 3)\n"
             "ctx = str(np.random.choice(['casa', 'coche']))",
       seed=3, lectura={"cubrir": ["a", "b"]})
    ejemplos, descartes, faltan = _ejemplos_lectura(p, max_semillas=60)
    assert descartes == [] and faltan == []
    assert len(ejemplos) == 2 * 2 * 3                           # 2 mundos × a × b
    assert [k for _, k, _ in ejemplos][:3] == [(("a", "-1"), ("b", "0")), (("a", "-1"), ("b", "1")),
                                               (("a", "-1"), ("b", "2"))]
    assert all(r.ns["a"] == int(dict(k)["a"]) for _, k, r in ejemplos)
    # sin cubrir: un ejemplo por mundo, y con extras uno más por mundo con otro
    # contexto (las cifras no cuentan como enunciado distinto)
    p.lectura = {}
    assert len(_ejemplos_lectura(p)[0]) == 2
    ex = _ejemplos_lectura(p, extras=1)[0]
    assert len(ex) == 4 and [k for _, k, _ in ex][1][0][0] == "sorteo"
    textos = {r.partes[0].enunciado.split("(")[1].split(")")[0] for _, _, r in ex if r.mundo == (0, 0)}
    assert textos == {"casa", "coche"}


def test_quiz_lectura_escribe_un_documento(problema_simple, tmp_path):
    from qbank import QuizLectura
    p2 = ProblemaTipo([
        "Texto.", [Cuestion("misma", "True", exp="E"), Cuestion("otra", "False", exp="E")],
        Cuestion("y otra", "False", exp="F"), Cuestion("z", "True"),
    ], nombre="L-01-Dos_partes", export={"last_choice": True})
    n = QuizLectura("doc", str(tmp_path), [problema_simple, p2], aux_latex="% preambulo del proyecto")
    assert n == 3
    tex = (tmp_path / "doc.tex").read_text(encoding="utf-8")
    assert tex.count("\\section*{") == 2 and "\\section*{L-01-Dos\\_partes}" in tex
    assert "% preambulo del proyecto" in tex and "\\end{document}" in tex
    assert "la opción 4 es «Ninguna de las anteriores»" in tex       # 3 huecos + last_choice
    assert "El alumno ve 1 opción." in tex                            # problema_simple: un hueco, sin last_choice
    assert tex.count("la misma retroalimentación que la anterior") == 1
    assert "\\subsection*{Mundo 1}" in tex and "\\subsection*{Mundo único}" in tex
    assert QuizLectura("uno", str(tmp_path), problema_simple, last_choice=True) == 2
    assert "la opción 2 es" in (tmp_path / "uno.tex").read_text(encoding="utf-8")   # 1 hueco + opción por defecto


def test_codchar_cubre_los_caracteres_del_espanol():
    # moodle.sty pasa las órdenes de acento a entidades HTML; un carácter sin
    # convertir llega al XML en UTF-8 y Moodle lo muestra mal (antigÃ¼edad).
    s = codchar("¿Antigüedad? ¡Índice! Árbol Él Óleo Último Ñu Ü")
    assert all(ord(ch) < 128 for ch in s)
    assert s.startswith("\\textquestiondown Antig\\\"{u}edad? \\textexclamdown \\'{I}ndice!")


# ---------------------------------------------------------------------------
# Motivo legible de las exclusiones (encargo de PE del 26-10)
# ---------------------------------------------------------------------------

class TestMotivoExclusion:
    @staticmethod
    def _problema(motivo_c="", motivo_s=""):
        from qbank import load_problema
        sup = {"tipo": "Supuesto", "enunciado": "Sea $x=@{x}$.", "semantica": "True",
               "precond": "lambda ns: ns['x'] < 0"}
        cue = {"tipo": "Cuestion", "enunciado": "$x$ es grande", "semantica": "True",
               "precond": "lambda ns: ns['x_max'] > 5", "exp": ""}
        if motivo_s:
            sup["motivo"] = motivo_s
        if motivo_c:
            cue["motivo"] = motivo_c
        return load_problema({"version": "1", "tipo": "ProblemaTipo", "nombre": "M",
                              "setup": "x = 1\nx_max = 3", "componentes": [
                                  [sup, {"tipo": "Supuesto", "enunciado": "Otro.",
                                         "semantica": "True"}], cue,
                                  {"tipo": "Cuestion", "enunciado": "a", "semantica": "True"},
                                  {"tipo": "Cuestion", "enunciado": "b", "semantica": "False"}]})

    def test_sin_motivo_la_precondicion_en_texttt(self):
        _, partes = next(iter(self._problema().por_partes_profe(verbose=False)))
        r = partes[0][1][0][1]
        assert r == "rechazada por lambda ns: ns['x_max'] > 5"
        assert r.tex() == (r"rechazada por \texttt{lambda ns: ns[\textquotesingle{}x\_max"
                           r"\textquotesingle{}] > 5}")

    def test_con_motivo_se_usa_el_motivo(self):
        from qbank import AMC_multipart, AMCblock
        p = self._problema("solo si $x$ supera el máximo")
        etiqueta, partes = next(iter(p.por_partes_profe(verbose=False)))
        r = partes[0][1][0][1]
        assert r == "solo si $x$ supera el máximo" and r.tex() == r
        tex = AMCblock("M", etiqueta, partes[0][0], partes[0][1], profe=True)
        assert r"\explain{ cuestión: $x$ es grande; solo si $x$ supera el máximo" in tex
        lect = next(iter(p.por_partes_lectura()))
        assert lect.partes[0].huecos[0][0].motivo == "solo si $x$ supera el máximo"

    def test_quiz_lectura_y_descartes(self, tmp_path):
        from qbank import QuizLectura
        QuizLectura("L", str(tmp_path), [self._problema(motivo_s="solo con $x$ positivo")])
        tex = (tmp_path / "L.tex").read_text(encoding="utf-8")
        assert "solo con $x$ positivo" in tex           # el mundo descartado, en prosa
        QuizLectura("L2", str(tmp_path), [self._problema()])
        tex = (tmp_path / "L2.tex").read_text(encoding="utf-8")
        assert r"rechazado por \texttt{lambda ns: ns[\textquotesingle{}x\textquotesingle{}] < 0}" in tex

    def test_json_y_python_conservan_el_motivo(self, tmp_path):
        from qbank import (Cuestion, load_problema, problema_to_dict, problema_to_python,
                           save_problema)
        p = self._problema("en prosa", "también")
        d = problema_to_dict(p)
        assert d["componentes"][0][0]["motivo"] == "también"
        assert d["componentes"][1]["motivo"] == "en prosa"
        assert "motivo" not in d["componentes"][2]
        assert "motivo = " in problema_to_python(p) and "en prosa" in problema_to_python(p)
        q = ProblemaTipo(["E ", Cuestion("a", True, "lambda ns: False", motivo="nunca"),
                          Cuestion("b", True), Cuestion("c", False)], nombre="Q")
        save_problema(q, str(tmp_path / "Q.json"))
        assert load_problema(str(tmp_path / "Q.json")).e[1].motivo == "nunca"
