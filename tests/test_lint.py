"""Tests de qbank.lint: un caso correcto y uno que viola cada regla."""
import copy
import json
from pathlib import Path

import pytest
from qbank import Cuestion, ProblemaTipo, Supuesto, lint, tabla_mundos, v
from qbank._lint import AVISO, ERROR, INFO, main
from qbank._quiz import _ns_interp

EJEMPLOS = sorted(Path(__file__).resolve().parents[1].glob("ejemplosManual/ej_*.json"))


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def S(enunciado, semantica, precond="True"):
    return {"tipo": "Supuesto", "enunciado": enunciado, "semantica": semantica, "precond": precond}


def C(enunciado, semantica, precond="True", exp=""):
    return {"tipo": "Cuestion", "enunciado": enunciado, "semantica": semantica,
            "precond": precond, "exp": exp}


def problema(componentes, nombre="p", setup=None, seed=None, **export):
    d = {"version": "1", "tipo": "ProblemaTipo", "nombre": nombre,
         "setup": setup, "export": {"last_choice": True, **export},
         "componentes": componentes}
    if seed is not None:
        d["seed"] = seed
    return d


def codigos(avisos, nivel=None):
    return {a.codigo for a in avisos if nivel is None or a.nivel == nivel}


def errores(avisos):
    return [a for a in avisos if a.nivel == ERROR]


# Base correcta: 2 mundos (A / B), 3 slots de 3 alternativas → 54 variantes.
def base():
    mundos = [S("si A,", "v('A')"), S("si B,", "v('B')")]
    slot = [C("entonces A", "v('A')"), C("entonces B", "v('B')"), C("nada", "False")]
    return problema(["Sea", mundos, "entonces:", slot, copy.deepcopy(slot), copy.deepcopy(slot)])


# ---------------------------------------------------------------------------
# Casos correctos
# ---------------------------------------------------------------------------

class TestCasosCorrectos:
    def test_base_sin_errores_ni_avisos(self):
        avisos = lint(base())
        assert not errores(avisos)
        assert not codigos(avisos, AVISO)

    @pytest.mark.parametrize("ruta", EJEMPLOS, ids=[p.stem for p in EJEMPLOS])
    def test_ejemplos_manual_sin_errores(self, ruta):
        assert not errores(lint(ruta)), [str(a) for a in errores(lint(ruta))]

    def test_acepta_problematipo_en_memoria(self):
        p = ProblemaTipo(["Sea", [Supuesto("si A,", v("A")), Supuesto("si B,", v("B"))],
                          [Cuestion("A", v("A")), Cuestion("B", v("B"))]],
                         export={"last_choice": True})
        assert not errores(lint(p))

    def test_errores_van_primero(self):
        d = base()
        d["nombre"] = "a:b"                      # ERROR nombre
        d["componentes"][1] = [d["componentes"][1][0]]   # AVISO lista-1
        niveles = [a.nivel for a in lint(d)]
        assert niveles == sorted(niveles, key=[ERROR, AVISO, INFO].index)


# ---------------------------------------------------------------------------
# Regla 1: garantía de mezcla
# ---------------------------------------------------------------------------

class TestMezcla:
    def test_sin_last_choice_todas_falsas_es_error(self):
        d = base()
        d["export"]["last_choice"] = False
        avisos = lint(d)
        assert "mezcla" in codigos(avisos, ERROR)

    def test_con_last_choice_ok(self):
        assert "mezcla" not in codigos(lint(base()))

    def test_todas_verdaderas_sin_last_choice_es_error(self):
        d = problema(["Sea", S("A", "v('A')"), C("A", "v('A')"), C("A otra vez", "v('A')")])
        d["export"]["last_choice"] = False
        assert "mezcla" in codigos(lint(d), ERROR)

    def test_todas_verdaderas_con_last_choice_ok(self):
        # la opción por defecto es incorrecta si alguna real es correcta
        d = problema(["Sea", S("A", "v('A')"), C("A", "v('A')"), C("A otra vez", "v('A')")])
        assert "mezcla" not in codigos(lint(d))

    def test_resume_violaciones_repetidas(self):
        d = base()
        d["export"]["last_choice"] = False
        msgs = [a.mensaje for a in lint(d) if a.codigo == "mezcla"]
        assert len(msgs) <= 6 and any("más" in m for m in msgs)

    def test_precond_descarta_variante_no_reduce_opciones(self):
        # una Cuestion rechazada descarta la variante entera: el nº de opciones es constante
        d = problema(["Sea", [S("A", "v('A')"), S("B", "v('B')")],
                      C("A", "v('A')"), C("B", "v('B')", precond="v('B')"), C("no", "False")])
        assert "opciones" not in codigos(lint(d))


# ---------------------------------------------------------------------------
# Regla 2 y 9: número de variantes / setup
# ---------------------------------------------------------------------------

class TestVariantes:
    def test_pocas_variantes_sin_setup(self):
        d = problema(["Sea", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")])
        assert "variantes" in codigos(lint(d), AVISO)

    def test_pocas_variantes_con_setup(self):
        d = problema(["Sea $x=@{x}$.", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")],
                     setup="import numpy as np\nx = int(np.random.randint(1, 5))",
                     seed=1, instances=3)
        avisos = lint(d)
        assert "variantes" in codigos(avisos, AVISO)
        assert "setup" in codigos(avisos, INFO)

    def test_instances_parametro_sobreescribe(self):
        d = problema(["Sea $x=@{x}$.", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")],
                     setup="import numpy as np\nx = int(np.random.randint(1, 5))",
                     seed=1, instances=3)
        assert "variantes" not in codigos(lint(d, instances=60), AVISO)

    def test_ninguna_variante_es_error(self):
        d = problema(["Sea", S("A", "v('A')", precond="v('B')"), C("A", "v('A')")])
        assert "variantes" in codigos(lint(d), ERROR)


# ---------------------------------------------------------------------------
# Regla 3: tabla texto → mundo
# ---------------------------------------------------------------------------

class TestMundos:
    def test_constante_no_literal_es_aviso(self):
        d = base()
        d["componentes"][3][0] = C("A o B", "v('A') | v('B')")
        av = [a for a in lint(d) if a.codigo == "constante"]
        assert any(a.nivel == AVISO and "verdadera" in a.mensaje for a in av)

    def test_constante_literal_es_info(self):
        av = [a for a in lint(base()) if a.codigo == "constante"]
        assert av and all(a.nivel == INFO for a in av)

    def test_no_constante_sin_aviso(self):
        av = [a for a in lint(base()) if a.codigo == "constante" and "entonces A" in a.donde]
        assert not av

    def test_un_solo_mundo_no_avisa(self):
        d = problema(["Sea", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")])
        assert "constante" not in codigos(lint(d))

    def test_solape_de_textos_identicos(self):
        d = base()
        d["componentes"][3] = [C("A", "v('A')", precond="v('A')"), C("A", "v('A')", precond="True")]
        assert "solape" in codigos(lint(d), AVISO)

    def test_sin_solape_si_precond_excluyentes(self):
        d = base()
        d["componentes"][3] = [C("A", "v('A')", precond="v('A')"), C("A", "False", precond="v('B')")]
        assert "solape" not in codigos(lint(d))

    def test_tabla_mundos_texto(self):
        t = tabla_mundos(base())
        assert "M1: si A," in t and "M2: si B," in t
        assert "V  F" in t and "F  V" in t and "F  F" in t


# ---------------------------------------------------------------------------
# Regla 4: negación sin unoDe
# ---------------------------------------------------------------------------

class TestNegacion:
    def _con_negacion(self, unoDe):
        comps = ["Sea", [S("A", "v('A')"), S("B", "v('B')")], C("no A", "-v('A')"), C("no", "False")]
        if unoDe:
            comps.insert(0, S("", "unoDe(v('A'),v('B'))"))
        return problema(comps)

    def test_sin_unoDe_es_error(self):
        assert "negacion" in codigos(lint(self._con_negacion(False)), ERROR)

    def test_con_unoDe_ok(self):
        assert "negacion" not in codigos(lint(self._con_negacion(True)))

    def test_supuesto_que_afirma_la_negacion_ok(self):
        d = problema(["Sea", [S("A", "v('A')"), S("no A", "-v('A')")],
                      C("no A", "-v('A')"), C("A", "v('A')"), C("no", "False")])
        assert "negacion" not in codigos(lint(d))

    def test_negacion_de_supuesto_fijo_es_aviso(self):
        d = problema(["Sea", S("A", "v('A')"), [S("B", "v('B')"), S("C", "v('C')")],
                      C("no A", "-v('A')"), C("B", "v('B')"), C("no", "False")])
        assert "negacion" in codigos(lint(d), AVISO)
        assert "negacion" not in codigos(lint(d), ERROR)

    def test_negacion_en_precond_tambien(self):
        d = problema(["Sea", [S("A", "v('A')"), S("B", "v('B')")],
                      C("x", "True", precond="-v('A')"), C("B", "v('B')"), C("no", "False")])
        assert "negacion" in codigos(lint(d), ERROR)


# ---------------------------------------------------------------------------
# Regla 5: interpolación fallida
# ---------------------------------------------------------------------------

class TestInterpolacion:
    def test_variable_desconocida_es_error(self):
        d = problema(["Sea $x=@{x}$ y $z=@{z}$.", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")],
                     setup="import numpy as np\nx = int(np.random.randint(1, 5))", seed=1)
        av = [a for a in lint(d) if a.codigo == "interp"]
        assert av and av[0].nivel == ERROR and "@{z}" in av[0].mensaje

    def test_interpolacion_en_exp(self):
        d = problema(["Sea $x=@{x}$.", S("A", "v('A')"),
                      C("A", "v('A')", exp="porque @{nada}"), C("no", "False")],
                     setup="import numpy as np\nx = int(np.random.randint(1, 5))", seed=1)
        assert any(a.codigo == "interp" and "exp" in a.mensaje for a in lint(d))

    def test_sin_setup_tambien_detecta(self):
        d = problema(["Sea $x=@{x}$.", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")])
        assert "interp" in codigos(lint(d), ERROR)

    def test_ns_interp_strict(self):
        assert _ns_interp("a=@{a} b=@{b}", {"a": 1}) == "a=1 b=@{b}"
        with pytest.raises(ValueError, match="'b'"):
            _ns_interp("a=@{a} b=@{b}", {"a": 1}, strict=True)
        assert _ns_interp("a=@{a}", {"a": 1}, strict=True) == "a=1"


# ---------------------------------------------------------------------------
# Regla 6: etiquetas huérfanas
# ---------------------------------------------------------------------------

class TestEtiquetas:
    def test_etiqueta_sin_supuesto_es_aviso(self):
        d = base()
        d["componentes"][3][2] = C("C", "v('C')")
        av = [a for a in lint(d) if a.codigo == "huerfana"]
        assert av and "'C'" in av[0].mensaje and av[0].nivel == AVISO

    def test_supuesto_sin_uso_es_info(self):
        d = base()
        d["componentes"][1].append(S("si C,", "v('C')"))
        av = [a for a in lint(d) if a.codigo == "sin-uso"]
        assert av and "'C'" in av[0].mensaje and av[0].nivel == INFO

    def test_base_sin_huerfanas(self):
        assert not codigos(lint(base())) & {"huerfana", "sin-uso"}


# ---------------------------------------------------------------------------
# Regla 7: estructura
# ---------------------------------------------------------------------------

class TestEstructura:
    def test_tipo_incorrecto(self):
        d = base()
        d["tipo"] = "ProblemaVF"
        av = lint(d)
        assert codigos(av, ERROR) == {"tipo"} and len(av) == 1

    def test_nombre_distinto_del_fichero(self, tmp_path):
        f = tmp_path / "otro.json"
        f.write_text(json.dumps(base()), encoding="utf-8")
        assert "nombre" in codigos(lint(f), ERROR)

    def test_nombre_igual_al_fichero_ok(self, tmp_path):
        f = tmp_path / "p.json"
        f.write_text(json.dumps(base()), encoding="utf-8")
        assert "nombre" not in codigos(lint(f))

    def test_dos_puntos_en_nombre(self):
        d = base()
        d["nombre"] = "L-01:x"
        assert "nombre" in codigos(lint(d), ERROR)

    def test_lista_mixta_es_error(self):
        d = base()
        d["componentes"][1].append("texto")
        assert "estructura" in codigos(lint(d), ERROR)

    def test_lista_anidada_es_error(self):
        d = base()
        d["componentes"][3] = [d["componentes"][3]]
        assert "estructura" in codigos(lint(d), ERROR)

    def test_lista_de_uno_es_aviso(self):
        d = base()
        d["componentes"][2] = ["entonces:"]
        assert "lista-1" in codigos(lint(d), AVISO)

    def test_seed_sin_random(self):
        d = base()
        d["seed"] = 3
        assert "seed" in codigos(lint(d), AVISO)

    def test_random_sin_seed(self):
        d = problema(["Sea $x=@{x}$.", S("A", "v('A')"), C("A", "v('A')"), C("no", "False")],
                     setup="import numpy as np\nx = int(np.random.randint(1, 5))")
        assert "seed" in codigos(lint(d), AVISO)

    def test_instances_sin_setup(self):
        d = base()
        d["export"]["instances"] = 5
        assert "instances" in codigos(lint(d), AVISO)

    def test_json_ilegible(self, tmp_path):
        f = tmp_path / "p.json"
        f.write_text("{no es json", encoding="utf-8")
        assert "carga" in codigos(lint(f), ERROR)

    def test_semantica_invalida(self):
        d = base()
        d["componentes"][3][0]["semantica"] = "v('A' +"
        assert "carga" in codigos(lint(d), ERROR)


# ---------------------------------------------------------------------------
# Regla 8: texto
# ---------------------------------------------------------------------------

class TestTexto:
    @pytest.mark.parametrize("texto", [
        "ángulo de 90° grados",
        "dice «hola»",
        r"la fórmula \(x^2\)",
        r"la fórmula \[x^2\]",
        "como se vio en la lección 3",
        "En la Lección  4",
        "valor @{x sin cerrar",
        "doble  espacio",
        "la palabra 'clave' entre comillas",
    ])
    def test_texto_sospechoso(self, texto):
        d = base()
        d["componentes"][0] = texto
        assert "texto" in codigos(lint(d), AVISO), texto

    @pytest.mark.parametrize("texto", [
        "ángulo de $90^\\circ$",
        "dice ``hola''",
        "derivada $f'(x)$ y $\\hat{y}'$",
        "valores absolutos $|x|'$ y $|y|'$",
        "salto \\\\[2pt] de línea",
        "vector $\\boldsymbol{x}$ con $@{x}$ valores",
        "texto normal, sin nada raro.",
    ])
    def test_texto_correcto(self, texto):
        d = base()
        d["componentes"][0] = texto
        assert "texto" not in codigos(lint(d)), texto

    def test_revisa_exp(self):
        d = base()
        d["componentes"][3][0]["exp"] = "ver lección 2"
        assert any(a.codigo == "texto" and "exp" in a.donde for a in lint(d))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def _escribe(self, tmp_path, nombre, d):
        d = copy.deepcopy(d)
        d["nombre"] = nombre
        f = tmp_path / f"{nombre}.json"
        f.write_text(json.dumps(d), encoding="utf-8")
        return str(f)

    def test_ok_devuelve_0(self, tmp_path, capsys):
        f = self._escribe(tmp_path, "ok", base())
        assert main([f]) == 0
        assert "OK" in capsys.readouterr().out

    def test_error_devuelve_1(self, tmp_path, capsys):
        d = base()
        d["export"]["last_choice"] = False
        f = self._escribe(tmp_path, "mal", d)
        assert main([f]) == 1
        out = capsys.readouterr().out
        assert "errores" in out and "[mezcla]" in out

    def test_quiet_omite_ok_e_info(self, tmp_path, capsys):
        f = self._escribe(tmp_path, "ok", base())
        main([f, "--quiet"])
        assert capsys.readouterr().out == ""

    def test_tabla(self, tmp_path, capsys):
        f = self._escribe(tmp_path, "ok", base())
        main([f, "--tabla"])
        assert "Mundos:" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# PENDIENTE.md (2026-09-19): lambda como texto desde JSON y exceso de variantes
# ---------------------------------------------------------------------------

class TestPendiente:
    def test_texto_lambda_desde_json_es_aviso(self):
        d = base()
        d["componentes"][3][0]["exp"] = "lambda ns: 'a' if ns['x'] > 0 else 'b'"
        av = [a for a in lint(d) if a.codigo == "texto" and "lambda" in a.mensaje]
        assert av and av[0].nivel == AVISO and "exp" in av[0].donde

    def test_mas_de_300_variantes_es_info(self):
        mundos = [S(f"si {k},", f"v('{k}')") for k in "ABC"]
        slot = [C(f"entonces {k}", f"v('{k}')") for k in "ABC"] + [C(f"nada {i}", "False") for i in range(4)]
        d = problema(["Sea", mundos, slot, copy.deepcopy(slot), copy.deepcopy(slot)])   # 3·7³ = 1029
        av = [a for a in lint(d) if a.codigo == "variantes"]
        assert av and av[0].nivel == INFO and "pdflatex" in av[0].mensaje

    def test_menos_de_300_sin_info(self):
        assert not [a for a in lint(base()) if a.codigo == "variantes"]


# ---------------------------------------------------------------------------
# Revisión de la Fase 3 (2026-10-19): falsos positivos y negativos de lint
# ---------------------------------------------------------------------------

class TestRevisionFase3:
    def test_arroba_doble_no_es_interp(self):
        d = base()
        d["componentes"][0] = "Escriba @@{x} literal"
        assert "interp" not in codigos(lint(d))

    def test_arroba_sin_resolver_sigue_siendo_interp(self):
        d = base()
        d["componentes"][0] = "Escriba @@{x} y @{y}"
        av = [a for a in lint(d) if a.codigo == "interp"]
        assert av and all("@{y}" in a.mensaje for a in av)

    @pytest.mark.parametrize("texto", ["En la elección 2019", "Tras la selección 3",
                                       "De la colección 2", "Por la Elección 4"])
    def test_palabras_con_leccion_dentro_no_avisan(self, texto):
        d = base()
        d["componentes"][0] = texto
        assert not [a for a in lint(d) if "lección" in a.mensaje]

    @pytest.mark.parametrize("texto", ["Como en la lección 3", "Lección 12: repaso", "leccion 2"])
    def test_numero_de_leccion_si_avisa(self, texto):
        d = base()
        d["componentes"][0] = texto
        assert [a for a in lint(d) if "lección" in a.mensaje]

    def _con_lambda(self):
        d = base()
        d["setup"] = "import numpy as np\nx = int(np.random.randint(0, 10))"
        d["seed"] = 2
        d["export"]["instances"] = 3
        d["componentes"][5] = [C("$x > 4$", "lambda ns: ns['x'] > 4"),
                               C("entonces A", "v('A')"), C("nada", "False")]
        return d

    def test_constante_lambda_con_setup_es_info(self):
        av = [a for a in lint(self._con_lambda()) if a.codigo == "constante" and "x > 4" in a.donde]
        # con seed=2 el único sorteo de la tabla da x > 4 en los dos mundos
        assert av and av[0].nivel == INFO and "lambda" in av[0].mensaje

    def test_constante_no_lambda_sigue_siendo_aviso(self):
        d = base()
        d["componentes"][5] = [C("A o B", "v('A') | v('B')"), C("entonces A", "v('A')")]
        av = [a for a in lint(d) if a.codigo == "constante"]
        assert av and av[0].nivel == AVISO

    def test_pct_sin_barra_en_texto_interpolado(self):
        d = base()
        d["setup"] = "import numpy as np\np = int(np.random.randint(1, 9))\npct = f'{p} %'"
        d["seed"] = 2
        d["componentes"][0] = "Sea @{pct}"
        av = [a for a in lint(d) if a.codigo == "texto" and a.nivel == ERROR]
        assert len(av) == 1 and "interpolado" in av[0].mensaje

    def test_pct_en_math_en_texto_interpolado(self):
        d = base()
        d["setup"] = "import numpy as np\np = int(np.random.randint(1, 9))\npct = f'{p}\\\\%'"
        d["seed"] = 2
        d["componentes"][0] = "Sea $@{pct}$"
        av = [a for a in lint(d) if a.codigo == "texto" and "dentro de $" in a.mensaje]
        assert len(av) == 1 and av[0].nivel == AVISO and "interpolado" in av[0].mensaje

    def test_pct_literal_no_se_duplica(self):
        d = base()
        d["setup"] = "import numpy as np\np = int(np.random.randint(1, 9))"
        d["seed"] = 2
        d["componentes"][0] = "Sea @{p} %"
        av = [a for a in lint(d) if a.codigo == "texto" and a.nivel == ERROR]
        assert len(av) == 1 and "interpolado" not in av[0].mensaje

    def test_pct_escapado_interpolado_sin_aviso(self):
        d = base()
        d["setup"] = "import numpy as np\np = int(np.random.randint(1, 9))\npct = f'{p}\\\\,\\\\%'"
        d["seed"] = 2
        d["componentes"][0] = "Sea @{pct}"
        assert not [a for a in lint(d) if a.codigo == "texto"]

    def test_sorteo_de_texto_no_cambia_las_variantes(self):
        d = base()
        d["setup"] = "import numpy as np\np = int(np.random.randint(1, 9))"
        d["componentes"][0] = "Sea @{p}"          # sin seed: depende del estado global
        import numpy as np
        np.random.seed(0)
        estado = np.random.get_state()[1].copy()
        from qbank._lint import _sorteos_ns
        _sorteos_ns(load_problema_dict(d))
        assert (np.random.get_state()[1] == estado).all()

    def test_nombre_con_espacios_es_error(self):
        d = base()
        d["nombre"] = "con espacios"
        av = [a for a in lint(d) if a.codigo == "nombre"]
        assert av and av[0].nivel == ERROR and "espacios" in av[0].mensaje

    def test_fichero_con_espacios_es_error(self, tmp_path):
        d = base()
        d["nombre"] = "con espacios"
        f = tmp_path / "con espacios.json"
        f.write_text(json.dumps(d), encoding="utf-8")
        av = [a for a in lint(f) if a.codigo == "nombre"]
        assert av and av[0].nivel == ERROR and "ignoran" in av[0].mensaje

    def test_seed_bool_es_error_estructura(self):
        d = base()
        d["setup"] = "import numpy as np\nx = int(np.random.randint(3))"
        d["seed"] = True
        av = [a for a in lint(d) if a.codigo == "estructura"]
        assert av and av[0].nivel == ERROR and "seed" in av[0].mensaje

    def test_parte_sin_cuestion_solo_aviso_opciones(self):
        d = base()
        d["componentes"].append("Texto final suelto.")
        avisos = lint(d)
        assert "mezcla" not in codigos(avisos)
        assert "opciones" in codigos(avisos, AVISO)


def load_problema_dict(d):
    from qbank import load_problema
    return load_problema(copy.deepcopy(d))


# ---------------------------------------------------------------------------
# Regla 10: lectura
# ---------------------------------------------------------------------------

def test_lint_lectura():
    setup = "import numpy as np\na = int(np.random.randint(0, 3))\nr = float(np.random.rand())"
    comps = ["$x=@{a}$.", [S("A.", "v('A')"), S("B.", "v('B')")],
             C("a", "v('A')"), C("b", "v('B')"), C("c", "v('A')")]
    def con(lectura, **kw):
        d = problema(comps, setup=setup, seed=1, instances=4, **kw)
        d["lectura"] = lectura
        return lint(d)
    assert "lectura" not in codigos(con({"cubrir": ["a"]}))
    assert "lectura" in codigos(con({"cubrir": ["zz"]}), ERROR)
    assert "lectura" in codigos(con({"cubrir": ["r"]}), AVISO)       # valores reales
    assert "estructura" in codigos(con({"cubrir": "a"}), ERROR)
    assert "estructura" in codigos(con(["a"]), ERROR)
    assert "lectura" in codigos(con({"cubrir": ["a"], "otra": 1}), AVISO)
    d = problema(comps[1:], nombre="p"); d["lectura"] = {"cubrir": ["a"]}
    assert "lectura" in codigos(lint(d), ERROR)                      # cubrir sin setup


# ---------------------------------------------------------------------------
# Regla 11: patrones memorizables (solo con patrones=)
# ---------------------------------------------------------------------------

def _patrones(d, n=30):
    return [a for a in lint(d, patrones=n) if a.codigo == "patron"]


def test_patrones_no_corre_por_defecto():
    d = problema(["Si $b=@{b}$,", [C("$b<1$", "lambda ns: ns['b'] < 1"), C("$b>5$", "lambda ns: ns['b'] > 5"),
                                    C("$b$ es par", "lambda ns: ns['b'] % 2 == 0")]],
                 setup="import numpy as np\nb = int(np.random.randint(1, 40))", seed=1)
    assert "patron" not in codigos(lint(d))
    assert "patron" in codigos(lint(d, patrones=True))


def test_patron_casi_constante_y_lambda_constante_en_la_muestra():
    d = problema(["Sea $n=@{n}$.", [C("$n>1$", "lambda ns: ns['n'] > 1"), C("$n$ es par", "lambda ns: ns['n'] % 2 == 0"),
                                    C("$n<0$", "lambda ns: ns['n'] < 0")]],
                 setup="import numpy as np\nn = int(np.random.randint(1, 40))", seed=1)
    av = _patrones(d)
    assert any("casi constante" in a.mensaje and "comp 1[0]" in a.donde for a in av)
    assert any("semantica lambda" in a.mensaje and "comp 1[2]" in a.donde for a in av)
    assert not any("comp 1[1]" in a.donde for a in av)                 # 50 %: nada que memorizar
    assert all(a.nivel == AVISO for a in av)


def test_patron_umbral_en_un_tipo_de_frase():
    # La elasticidad verdadera siempre < 1 y su gemela falsa siempre > 1 (el caso de la auditoría).
    comps = ["El modelo estimado es", [S("nivel-log.", "v('nl') & -v('ln')"), S("log-nivel.", "v('ln') & -v('nl')")],
             "Entonces", [C("un 1 % más de $x$ da $@{c_nl}$ unidades más", "True", "v('nl')"),
                          C("un 1 % más de $x$ da $@{c_ll}$ unidades más", "False", "v('nl')"),
                          C("una unidad más de $x$ da un $@{c_ln}$ % más", "True", "v('ln')"),
                          C("una unidad más de $x$ da un $@{c_nn}$ % más", "False", "v('ln')"),
                          C("el modelo es lineal", "False")]]
    setup = ("import numpy as np\nc_nl = round(float(np.random.uniform(1.5, 3)), 2)\n"
             "c_ll = round(float(np.random.uniform(0.2, 0.9)), 2)\nc_ln = round(float(np.random.uniform(0.2, 0.9)), 2)\n"
             "c_nn = round(float(np.random.uniform(1.5, 3)), 2)")
    av = _patrones(problema(comps, setup=setup, seed=1))
    assert sum("separa V" in a.mensaje for a in av) == 2
    assert any("unidades más" in a.mensaje and "de F (0,2" in a.mensaje for a in av)


def test_patron_cifra_mayor_del_hueco():
    # La gemela falsa es siempre mayor que la verdadera: «elige la menor» acierta siempre.
    comps = ["Con $\\hat\\beta=@{b}$,", [C("la elasticidad vale $@{e}$", "lambda ns: ns['e'] == ns['e_real']"),
                                          C("la elasticidad vale $@{e2}$", "lambda ns: ns['e2'] == ns['e_real']")]]
    setup = ("import numpy as np\nb = round(float(np.random.uniform(0.2, 3)), 1); e_real = b\n"
             "e = round(float(np.random.choice([e_real, e_real + 1])), 1); e2 = round(e_real + 1 if e == e_real else e_real, 1)")
    av = _patrones(problema(comps, setup=setup, seed=1))
    assert any("con la cifra mayor del hueco" in a.mensaje and "⇒ F" in a.mensaje for a in av)
    assert any("con la cifra menor del hueco" in a.mensaje and "⇒ V" in a.mensaje for a in av)


def test_patron_calculo_legitimo_y_mundos_equilibrados_no_avisan():
    comps = ["Sea $x=@{x}$ e $y=@{y}$. Entonces", [C("$x+y=@{s}$", "True"), C("$x+y=@{s1}$", "False"),
                                                   C("$xy=@{p}$", "True"), C("$xy=@{p1}$", "False")]]
    setup = ("import numpy as np\nx = int(np.random.randint(2, 20)); y = int(np.random.randint(2, 20)); s = x + y; p = x * y\n"
             "s1 = s + int(np.random.choice([-2, -1, 1, 2])); p1 = p + int(np.random.choice([-3, -1, 1, 3]))")
    assert _patrones(problema(comps, setup=setup, seed=1)) == []
    comps = ["Sea", [S("A.", "v('A') & -v('B')"), S("B.", "v('B') & -v('A')")],
             [C("entonces A", "v('A')"), C("entonces B", "v('B')"), C("A o B", "True"), C("A y B", "False")]]
    assert _patrones(problema(comps)) == []


def test_patron_no_repite_lo_que_dice_constante():
    # Las falsas largas son constantes: la regla 3 ya las señala; «patron» calla.
    comps = ["Sea", [S("A.", "v('A') & -v('B')"), S("B.", "v('B') & -v('A')")],
             [C("A", "v('A')"), C("B", "v('B')"),
              C("no A, porque en general la condición no se cumple nunca", "False"),
              C("no B, lo que se demuestra sin más en general", "False")]]
    av = lint(problema(comps), patrones=True)
    assert "constante" in codigos(av)
    assert "patron" not in codigos(av)


def test_patron_cifras_ignora_la_notacion():
    from qbank._lint import _cifras
    assert _cifras(r"el vector $\boldsymbol 1$ y $\mathbf{1}$ frente a $x_1^2$") == []
    assert _cifras(r"mayor que $1$, $0{,}5$, $-\frac{2}{3}$ y 12 %") == pytest.approx([1.0, 0.5, -2 / 3, 12.0], abs=1e-5)


def test_patron_cli(tmp_path, capsys):
    d = problema(["Sea $n=@{n}$.", [C("$n>1$", "lambda ns: ns['n'] > 1"), C("$n$ es par", "lambda ns: ns['n'] % 2 == 0"),
                                    C("$n<0$", "lambda ns: ns['n'] < 0")]],
                 setup="import numpy as np\nn = int(np.random.randint(1, 40))", seed=1)
    f = tmp_path / "p.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    assert main([str(f), "--quiet"]) == 0
    assert "[patron]" not in capsys.readouterr().out
    assert main([str(f), "--patrones", "20", "--quiet"]) == 0           # un AVISO no cambia el código de salida
    out = capsys.readouterr().out
    assert "[patron]" in out and "casi constante" in out
    assert main([str(f), "--patrones"]) == 0
    assert "[patron]" in capsys.readouterr().out
    assert main(["--quiet", "--patrones", str(f)]) == 0               # el fichero tras --patrones no es N
    assert "[patron]" in capsys.readouterr().out


def test_patron_ignora_palabras_cortas():
    from qbank._lint import _palabras
    assert _palabras("el precio de los coches usados y la edad") == {"precio", "coches", "usados", "edad"}


# ---------------------------------------------------------------------------
# Regla 11, forma de la cifra; regla 12, inventario de objetos
# ---------------------------------------------------------------------------

def test_patron_cifra_redonda_en_un_tipo_de_frase():
    # L-16-DiferenciaPorcentualEnLogNivel: la cifra redonda (100·beta) era siempre la aproximación,
    # y por tanto siempre falsa; la exacta verdadera nunca era redonda. Los valores se solapan,
    # así que el umbral no lo ve: lo ve la forma de la cifra.
    comps = ["El coeficiente de la indicadora es $@{b}$. Entonces el salario es, en diferencia porcentual exacta,",
             [C("un $@{ex}$\\,\\% mayor", "True"), C("un $@{apr}$\\,\\% mayor", "False"),
              C("un $@{otro}$\\,\\% mayor", "False")]]
    setup = ("import numpy as np\nb = float(np.random.choice([0.2, 0.3, 0.4]))\n"
             "ex = {0.2: 22, 0.3: 35, 0.4: 49}[b]; apr = int(round(100 * b))\n"
             "otro = {0.2: 18, 0.3: 26, 0.4: 33}[b]")
    av = _patrones(problema(comps, setup=setup, seed=1))
    assert any("múltiplo de 10" in a.mensaje and "⇒ F" in a.mensaje for a in av)
    # Con una exacta verdadera redonda a veces (e^0,223 = 1,25; e^0,405 = 1,5) la forma ya no decide.
    setup2 = ("import numpy as np\nb = float(np.random.choice([0.2, 0.3, 0.4, 0.223, 0.405]))\n"
              "ex = {0.2: 22, 0.3: 35, 0.4: 49, 0.223: 25, 0.405: 50}[b]; apr = round(100 * b, 1)\n"
              "apr = int(apr) if apr == int(apr) else apr\n"
              "otro = {0.2: 18, 0.3: 26, 0.4: 33, 0.223: 20, 0.405: 33}[b]")
    av = _patrones(problema(comps, setup=setup2, seed=1))
    assert not any("múltiplo de 10" in a.mensaje for a in av)


def test_formas_cifra():
    from qbank._lint import _formas_cifra, _cifras_y_formas
    assert _formas_cifra("20") == {"entera", "múltiplo de 5", "múltiplo de 10"}
    assert _formas_cifra("-15") == {"entera", "múltiplo de 5"}
    assert _formas_cifra("0{,}80") == {"con decimales", "con 2 decimales"}
    assert _formas_cifra("22.3") == {"con decimales", "con 1 decimal"}
    cifras, formas = _cifras_y_formas("un $22{,}3$\\,\\% y 40")
    assert cifras == [22.3, 40.0] and "múltiplo de 10" in formas[1]


def _inventario(d, **kw):
    return [a for a in lint(d, **kw) if a.codigo == "inventario"]


def test_inventario_objeto_que_el_enunciado_no_presenta():
    # L-16-InteraccionYChow: el enunciado mostraba el modelo con mujer·exper y las opciones hablaban
    # del modelo con mujer·educ, que no se había presentado; el exp calculaba con sus columnas.
    comps = ["Se estima $y$ sobre la constante, $\\text{mujer}$, $\\text{educ}$, $\\text{exper}$ y "
             "$\\text{mujer}\\cdot\\text{exper}$. Entonces",
             [C("el coeficiente de $\\text{mujer}\\cdot\\text{exper}$ es la diferencia de pendientes", "True"),
              C("el modelo con $\\text{mujer}\\cdot\\text{educ}$ y $\\text{mujer}\\cdot\\text{exper}$ es el sin restringir",
                "True", exp="con $\\text{mujer}\\cdot\\text{educ}$ tiene seis columnas"),
              C("la pendiente de $\\text{exper}$ es común", "False", exp="no: véase $\\mathrm{exper}$ y el modelo con $\\text{mujer}\\cdot\\text{educ}$")]]
    av = _inventario(problema(comps))
    assert [(a.nivel, a.donde[:9]) for a in av] == [(AVISO, "comp 1[1]"), (AVISO, "comp 1[2]")]
    assert "«mujer·educ»" in av[0].mensaje and "1 de las 1 veces" in av[0].mensaje
    assert av[1].mensaje.startswith("la exp nombra «mujer·educ»")       # \mathrm{exper} = \text{exper}: presentado
    # El objeto de la exp que ya nombra la cuestión no se avisa dos veces (comp 1[1]).


def test_inventario_info_si_la_opcion_lo_presenta_y_por_variante():
    comps = ["Se estima $y$ sobre la constante y la indicadora $\\text{@{ind}}$. Entonces",
             [C("con la indicadora $\\text{@{otra}}$ ($1$ en los demás) el coeficiente cambia de signo", "True"),
              C("con la indicadora $\\text{@{otra}}$ en lugar de $\\text{@{ind}}$ el ajuste no cambia", "True"),
              C("el coeficiente de $\\text{hombre}$ mide la diferencia", "False")]]
    setup = "import numpy as np\ni = int(np.random.randint(2)); ind = ['mujer', 'hombre'][i]; otra = ['hombre', 'mujer'][i]"
    av = _inventario(problema(comps, setup=setup, seed=3))
    info = [a for a in av if a.nivel == INFO]
    assert {a.donde[:9] for a in info} == {"comp 1[0]", "comp 1[1]"} and all("presenta ella misma" in a.mensaje for a in info)
    aviso = [a for a in av if a.nivel == AVISO]
    assert len(aviso) == 1 and "«hombre»" in aviso[0].mensaje and "de las 10 veces" in aviso[0].mensaje
    assert not aviso[0].mensaje.split("(en ")[1].startswith("10 de")      # solo falta cuando la indicadora es mujer


def test_inventario_subindices_negritas_y_conocidos():
    from qbank._lint import _objetos
    assert _objetos(r"$\hat{\beta}_{3}$, $\boldsymbol 1$, $\mathbf{X}_2$ y $y_t$") == {
        "\\beta_3": ("subindice", False), "\\boldsymbol{X}": ("negrita", False), "X_2": ("subindice", False)}
    comps = ["Sea $\\hat\\beta_1 + \\hat\\beta_2 x$, con $\\boldsymbol{y}$ e $\\mathrm{SRC}=3$. Entonces",
             [C("$\\beta_2$ es la pendiente", "True"),                 # presentado (sin el sombrero)
              C("$\\beta_3$ es cero", "False"),                         # un índice que el enunciado no muestra: AVISO
              C("$\\boldsymbol{u}$ es el residuo y $\\mathrm{STC}>\\mathrm{SRC}$", "True"),   # STC: AVISO
              C("para cualesquiera $u_1$, $u_2$ y $\\boldsymbol{v}$ se cumple", "True")]]     # letras generales: INFO
    av = _inventario(problema(comps))
    assert [(a.nivel, a.donde[:9]) for a in av if a.nivel == AVISO] == [(AVISO, "comp 1[1]"), (AVISO, "comp 1[2]")]
    assert "sí presenta \\beta_1, \\beta_2" in av[0].mensaje and "«STC»" in av[1].mensaje
    resumen = [a for a in av if a.nivel == INFO]
    assert len(resumen) == 1 and "«\\boldsymbol{u}» (1)" in resumen[0].mensaje and "«u_1» (1)" in resumen[0].mensaje
    # Notación declarada conocida: como se escribe, normalizada, o toda una base de subíndices.
    assert _inventario(problema(comps), conocidos=[r"\mathrm{STC}", r"\beta_", r"\boldsymbol{u}", "u_1", "u_2", r"\mathbf{v}"]) == []
    assert [a.mensaje[:30] for a in _inventario(problema(comps), conocidos="STC,\\beta_3")] == \
        [a.mensaje[:30] for a in av if a.nivel == INFO]


def test_inventario_cli_conocidos(tmp_path, capsys):
    d = problema(["Con $\\mathrm{STC}=10$:", [C("$\\mathrm{SRC}$ es menor", "True"), C("$\\mathrm{SRC}$ es mayor", "False"),
                                                C("$\\mathrm{SEC}$ es cero", "False")]])
    f = tmp_path / "p.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    assert main([str(f), "--quiet"]) == 0
    assert capsys.readouterr().out.count("[inventario]") == 3
    assert main([str(f), "--quiet", "--conocidos", r"\mathrm{SRC},SEC"]) == 0
    assert "[inventario]" not in capsys.readouterr().out
    assert main([str(f), "--quiet", "--conocidos", "SRC", "--conocidos", "SEC"]) == 0
    assert "[inventario]" not in capsys.readouterr().out


# ── Reglas 13 y 14: longitud y gemela ────────────────────────────────────────

def _codigo(d, codigo, **kw):
    return [a for a in lint(d, **kw) if a.codigo == codigo]


def test_longitud_opcion_destacada_sin_pareja():
    # La verdadera lleva su «porque…» (destaca) y en su hueco solo hay falsas desnudas.
    largo = C("entonces A o B, porque la hipótesis lo garantiza en cada caso", "True")
    slot = [largo, C("entonces B", "v('B')"), C("nada de nada", "False")]
    d = problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:", slot,
                  [C("A es cierta", "v('A')"), C("B es cierta", "v('B')"), C("ninguna lo es", "False")]])
    av = _codigo(d, "longitud")
    assert len(av) == 1 and av[0].nivel == AVISO and "comp 3[0]" in av[0].donde
    assert "más larga" in av[0].mensaje and "verdadera" in av[0].mensaje and "siempre" in av[0].mensaje
    assert "mundos 1, 2 de 2" in av[0].mensaje and "100%" in av[0].mensaje
    # Con una pareja larga y de valor contrario en el mismo hueco, calla: el alumno ve largas
    # verdaderas y largas falsas.
    slot.append(C("entonces ni A ni B, porque la hipótesis lo impide en cada caso", "False"))
    assert not _codigo(d, "longitud")
    # Una pareja larga pero del mismo valor no sirve.
    slot[-1] = C("entonces A o B, porque así lo dice la hipótesis de partida", "True")
    assert _codigo(d, "longitud")
    # Si otro hueco muestra casi siempre una opción igual de larga, la primera ya no destaca.
    slot.pop()
    d["componentes"][4] = [C("A es cierta, porque la hipótesis de partida lo garantiza", "v('A')"),
                           C("B es cierta, porque la hipótesis de partida lo garantiza", "v('B')"), C("ninguna", "False")]
    assert not [a for a in _codigo(d, "longitud") if "comp 3[0]" in a.donde]


def test_longitud_mide_lo_visible_y_no_castiga_huecos_compensados():
    from qbank._lint import _visible
    assert _visible(r"$\hat\beta_1=\mu_y-\hat\beta_2\mu_x$") == 10          # β1=μy-β2μx
    assert _visible(r"la media $\boldsymbol{x}$") == len("la media x")
    assert 10 <= _visible(r"$\text{mujer}\cdot\text{educ}$") <= 12                # mujer · educ
    # Fórmula larga en LaTeX pero corta a la vista frente a frases: nada destaca.
    slot = [C(r"$\dfrac{\sigma_{\boldsymbol{x}\boldsymbol{y}}}{\sigma_{\boldsymbol{x}}^{2}}$", "v('A')"),
            C("la covarianza", "v('B')"), C("la varianza", "False")]
    d = problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:", slot])
    assert not _codigo(d, "longitud")
    # Medias desplazadas pero sin opción destacada sin pareja (la larga verdadera tiene su larga
    # falsa): el alumno ve una larga que unas veces es V y otras F.
    d = problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:",
                  [C("entonces A, porque la hipótesis lo garantiza siempre", "v('A')"),
                   C("entonces B, porque la hipótesis lo garantiza siempre", "v('B')"), C("nada", "False")],
                  [C("A", "v('A')"), C("B", "v('B')"), C("C", "False")]])
    assert not _codigo(d, "longitud")


def test_longitud_la_corta_tambien_destaca_y_una_variable_es_su_propia_pareja():
    # Todas largas salvo una corta, siempre falsa.
    d = problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:",
                  [C("entonces A, por la hipótesis de partida", "v('A')"), C("entonces B, por la hipótesis de partida", "v('B')"),
                   C("nada", "False")],
                  [C("A se cumple en todos los casos posibles", "v('A')"), C("B se cumple en todos los casos posibles", "v('B')")]])
    av = _codigo(d, "longitud")
    assert len(av) == 1 and "más corta" in av[0].mensaje and "falsa" in av[0].mensaje and "comp 3[2]" in av[0].donde
    # Si la corta es verdadera en un mundo y falsa en el otro, no delata nada.
    d["componentes"][3][2] = C("nada", "v('A')")
    assert not _codigo(d, "longitud")


def test_gemela_verdadera_fija_con_cifra_sin_version_falsa():
    base_ = base()
    base_["componentes"][3] = [C("$\\sigma_x^2 = 2/3$", "True"), C("$\\sigma_{xy} = -1$", "False"),
                               C("$\\sigma_{xy} = 4$", "False")]
    av = _codigo(base_, "gemela")
    assert len(av) == 1 and av[0].nivel == AVISO and "con fórmula" in av[0].mensaje and "comp 3[0]" in av[0].donde
    # Un valor suelto («$300$ mil euros es…») cuenta como cifra aunque la prosa sea larga.
    assert "con cifra" in _codigo(problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:",
                                            [C("$300$ mil euros es la previsión de la mediana del precio, no de su esperanza", "True"),
                                             C("la previsión es insesgada", "False"), C("nada", "False")]]), "gemela")[0].mensaje
    # Con su gemela (misma fórmula, otra cifra) calla…
    base_["componentes"][3].append(C("$\\sigma_x^2 = 3/2$", "False"))
    assert not _codigo(base_, "gemela")
    # … y también si la gemela cambia los símbolos y conserva la cifra.
    base_["componentes"][3][-1] = C("$\\sigma_y^2 = 2/3$", "False")
    assert not _codigo(base_, "gemela")


def test_gemela_reconoce_antonimos_signo_negacion_y_orden():
    for v, f in [("la coordenada de $x_2$ pasa a ser $\\hat\\beta_2+\\hat\\beta_3$",
                  "la coordenada de $x_2$ pasa a ser $\\hat\\beta_2-\\hat\\beta_3$"),
                 ("$\\sigma_{xy}$ es mayor que $0{,}5$", "$\\sigma_{xy}$ es menor que $0{,}5$"),
                 ("$\\det(A^\\top) = \\det(A)$", "$\\det(A^\\top) = -\\det(A)$"),
                 ("$\\mu_{x^2} \\geq \\mu_x^2$", "$\\mu_{x^2} \\leq \\mu_x^2$"),
                 ("$x$ es $2y$", "$x$ no es $2y$"),
                 ("$\\hat\\beta_1 = \\mu_y - \\hat\\beta_2\\mu_x$", "$\\hat\\beta_2 = \\mu_x - \\hat\\beta_1\\mu_y$")]:
        d = base()
        d["componentes"][3] = [C(v, "True"), C(f, "False"), C("otra cosa", "False")]
        assert not _codigo(d, "gemela"), (v, f)


def test_gemela_info_si_la_formula_va_dentro_de_una_frase_y_calla_sin_calculo():
    d = base()
    d["componentes"][3] = [C("la insesgadez del estimador se apoya en que $E[U\\mid X]=0$ para toda muestra", "True"),
                           C("la insesgadez del estimador se apoya en la normalidad", "False"), C("nada", "False")]
    av = _codigo(d, "gemela")
    assert len(av) == 1 and av[0].nivel == INFO
    d["componentes"][3][0] = C("el estimador $\\hat\\beta$ es insesgado", "True")   # símbolo suelto: nada que calcular
    assert not _codigo(d, "gemela")
    # Una verdadera que a veces es falsa no es «siempre cierta».
    d["componentes"][3][0] = C("$x = 2$", "v('A')")
    assert not _codigo(d, "gemela")


def test_gemela_sin_ninguna_falsa_en_el_hueco():
    d = base()
    d["componentes"][3] = [C("$\\det(A) \\neq 0$", "True", "v('A')"), C("$\\det(A) = 0$", "True", "v('B')")]
    av = _codigo(d, "gemela")
    assert len(av) == 2 and all("no tiene ninguna falsa" in a.mensaje for a in av)


# ── Regla 12: rangos con puntos e hipótesis escritas ─────────────────────────

def test_inventario_rango_con_puntos_presenta_los_subindices_intermedios():
    enun = r"Sea $\hat{\boldsymbol\beta}=(\hat\beta_1,\dots,\hat\beta_k)$ el vector de coeficientes."
    cues = [C(r"$\hat\beta_2$ es la segunda coordenada", "v('A')"), C(r"$\hat\beta_3$ es la primera", "v('B')"),
            C("nada", "False")]
    d = problema([enun, [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:", cues])
    assert not [a for a in _inventario(d) if a.nivel == AVISO]
    # Fin numérico: solo el rango; \beta_7 queda fuera y tiene hermanos presentados.
    d["componentes"][0] = r"Sea $(\beta_1,\ldots,\beta_5)$ el vector de coeficientes."
    d["componentes"][3][1] = C(r"$\hat\beta_7$ es la primera", "v('B')")
    av = [a for a in _inventario(d) if a.nivel == AVISO]
    assert len(av) == 1 and "\\beta_7" in av[0].mensaje and "sí presenta" in av[0].mensaje


def test_inventario_hipotesis_escrita_en_la_opcion_es_info():
    d = problema([r"Con el modelo $y=\beta_1+\beta_2 x+U$ estimado,", [S("si A,", "v('A')"), S("si B,", "v('B')")],
                  "entonces:", [C(r"el contraste conjunto ($H_0\!:\beta_2=\beta_3=0$) rechaza", "v('A')"),
                                C(r"el contraste de $\beta_3$ rechaza", "v('B')"), C("nada", "False")]])
    av = _inventario(d)
    # \beta_3 dentro de «H_0: …» en la opción: presentado por ella misma (INFO); suelto en la otra: AVISO.
    assert {a.nivel for a in av if "comp 3[0]" in a.donde} == {INFO}
    assert [a for a in av if a.nivel == AVISO and "\\beta_3" in a.mensaje and "comp 3[1]" in a.donde]


# ── Separador decimal ────────────────────────────────────────────────────────

def test_decimal_del_banco_en_cifras_y_tipo_de_frase(tmp_path, capsys):
    from qbank._lint import _cifras, _tipo_frase
    assert _cifras("$(2,2,-1)$ y $0{,}5$") == pytest.approx([2.2, -1.0, 0.5])
    assert _cifras("$(2,2,-1)$ y $0{,}5$", decimal="{,}") == pytest.approx([2.0, 2.0, -1.0, 0.5])
    assert _cifras("2.5 y 0{,}5", decimal="{,} .") == pytest.approx([2.5, 0.5])
    assert _tipo_frase("$(2,2,-1)$", decimal="{,}") == "$(#,#,#)$" and _tipo_frase("$(2,2,-1)$") == "$(#,#)$"
    # Con decimal="{,}", $(2,2,-1)$ y $(2,3,-1)$ son gemelas (misma forma, otras cifras).
    d = base()
    d["componentes"][3] = [C("$\\boldsymbol{v} = (2,2,-1)$", "True"), C("$\\boldsymbol{v} = (2,3,-1)$", "False"),
                           C("$\\boldsymbol{v} = (1,1,1)$", "False")]
    assert not _codigo(d, "gemela", decimal="{,}") and not _codigo(d, "gemela")
    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps(d), encoding="utf-8")
    assert main([str(ruta), "--decimal", "{,}", "--quiet"]) == 0


# ── Reglas 13, 14 y 11: ajustes tras la lectura de PE (23-10) ────────────────

def test_gemela_cifra_copiada_del_enunciado_con_falsa_vecina_no_avisa():
    enun = "La media del precio es $28$ junto al río y $22$ sin río; el coeficiente de la indicadora es $6$."
    v = C("la constante, $22$, es la media del precio de los barrios sin río, la categoría base", "True")
    f = C("la constante, $22$, es la media del precio de toda la muestra", "False")
    d = problema([enun, [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:", [v, f, C("nada", "False")]])
    assert not _codigo(d, "gemela")
    # Sin una falsa que lleve la cifra, la cifra delata.
    d["componentes"][3][1] = C("la constante es la media del precio de toda la muestra", "False")
    assert len(_codigo(d, "gemela")) == 1
    # Una cifra que no da el enunciado (un resultado) necesita gemela numérica aunque una falsa la repita.
    d["componentes"][3] = [C("la diferencia de medias es $6{,}5$ unidades", "True"),
                           C("la diferencia de medias, $6{,}5$, es la media de toda la muestra", "False"), C("nada", "False")]
    assert "con cifra" in _codigo(d, "gemela")[0].mensaje


def test_gemela_una_coletilla_no_rompe_la_gemela():
    d = base()
    d["componentes"][3] = [C("el modelo solo produce dos valores ajustados, $22$ para los barrios sin río y $28$ para los "
                             "barrios junto al río: las medias de los dos grupos", "True"),
                           C("el modelo solo produce dos valores ajustados, $22$ para los barrios sin río y $6$ para los "
                             "barrios junto al río", "False"), C("nada", "False")]
    assert not _codigo(d, "gemela")
    from qbank._lint import _parecidos
    assert _parecidos(("a", "b", "c", "d"), ("a", "b", "c", "d", "e")) == pytest.approx(8 / 9)
    assert _parecidos(("a", "a", "b"), ("a", "c")) == pytest.approx(0.4)


def test_gemela_cifras_incidentales_no_son_contenido_calculable():
    from qbank._lint import _calculable
    assert _calculable("la indicadora vale $1$ para los hombres y $0$ para las mujeres") is None
    assert _calculable("el modelo (1) anida al modelo (2)") is None
    assert _calculable("la coordenada $x_{2}$ y el cuadrado $x^2$ no cambian") is None
    assert _calculable("$H_0$ se rechaza al $5$\\,\\% de significación", cifras_enun=[5.0]) is None
    assert _calculable("$H_0$ se rechaza al $5$\\,\\% de significación") == "cifra"
    assert _calculable("$300$ mil euros es la previsión") == "cifra"
    assert _calculable("$\\sigma_x^2 = 2/3$") == "fórmula"


def test_gemela_calculo_entre_objetos_del_enunciado_dentro_de_una_frase_es_aviso():
    enun = (r"Se regresa $\boldsymbol{y}$ sobre $\boldsymbol{1}$, $\boldsymbol{x}_2$ y $\boldsymbol{x}_3$, "
            r"con coordenadas $\hat\beta_2$ y $\hat\beta_3$.")
    v = C(r"si se sustituye $\boldsymbol{x}_3$ por $\boldsymbol{x}_3-\boldsymbol{x}_2$, el ajuste no cambia, "
          r"pero la coordenada de $\boldsymbol{x}_2$ pasa a ser $\hat\beta_2+\hat\beta_3$", "True")
    d = problema([enun, [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:",
                  [v, C("el ajuste cambia porque los regresores son otros", "False"), C("nada", "False")]])
    av = _codigo(d, "gemela")
    assert len(av) == 1 and av[0].nivel == AVISO and "cálculo entre objetos" in av[0].mensaje
    # Una propiedad (igualdad sin operación entre objetos) sigue siendo INFO…
    d["componentes"][3][0] = C(r"si $\rho_{\boldsymbol{x}_2\boldsymbol{x}_3}=0$, la coordenada de $\boldsymbol{x}_2$ "
                               r"es la misma en los dos ajustes", "True")
    av = _codigo(d, "gemela")
    assert len(av) == 1 and av[0].nivel == INFO
    # … y una definición con símbolos que el enunciado no presenta, también.
    d["componentes"][3][0] = C(r"$\mathcal{L}(\boldsymbol{x}_2,\boldsymbol{x}_3)$ es el conjunto de las combinaciones "
                               r"$\gamma_1\boldsymbol{x}_2+\gamma_2\boldsymbol{x}_3$ con $\gamma_1,\gamma_2$ reales", "True")
    av = _codigo(d, "gemela")
    assert len(av) == 1 and av[0].nivel == INFO


def test_longitud_pareja_de_cadenas_cortas():
    from qbank._lint import _parecida
    assert _parecida(3, 4) and _parecida(100, 125) and not _parecida(20, 40)
    # «$F=4$» (3 visibles) y «$F=14$» (4): razón 1,33, pero entre ellas nada destaca.
    slot = [C("$F=4$", "True"), C("$F=14$", "False")]
    largo = [C("la hipótesis nula no se rechaza al nivel habitual de significación", "v('A')"),
             C("la hipótesis nula se rechaza al nivel habitual de significación", "v('B')"), C("ninguna lo es", "False")]
    d = problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:", slot, largo])
    assert not [a for a in _codigo(d, "longitud") if "comp 3[" in a.donde]


def test_patron_rasgo_de_cifras_que_reune_cuestiones_enteras():
    # Dos distractores constantes escriben un intervalo y ninguna verdadera lo hace: se aprende sin leer.
    comps = ["Sea", [S("A.", "v('A') & -v('B')"), S("B.", "v('B') & -v('A')")],
             [C("A", "v('A')"), C("B", "v('B')"),
              C("el intervalo es $[20,\\,40]$\\,\\%", "False"), C("el intervalo es $[25,\\,45]$\\,\\%", "False")]]
    av = [a for a in lint(problema(comps, setup="x = 1"), patrones=True) if a.codigo == "patron"]
    assert any("intervalo" in a.mensaje or "cifras" in a.mensaje for a in av)
    # Una sola Cuestion entera sigue siendo cosa de «constante».
    comps[2].pop()
    av = [a for a in lint(problema(comps, setup="x = 1"), patrones=True) if a.codigo == "patron"]
    assert not av


def test_longitud_calla_si_la_destacada_de_lo_mostrado_es_verdadera_la_mitad_de_las_veces():
    # Hueco 3: larga siempre V sin pareja; hueco 4: larga siempre F sin pareja. Entre lo que el
    # alumno ve, la claramente más larga es V la mitad de las veces: nada que aprender.
    larga_v = C("entonces A o B, porque la hipótesis lo garantiza en todos los casos", "True")
    larga_f = C("ninguna, porque la hipótesis nunca garantiza nada en ningún caso", "False")
    d = problema(["Sea", [S("si A,", "v('A')"), S("si B,", "v('B')")], "entonces:",
                  [larga_v, C("entonces B", "v('B')"), C("nada", "False")],
                  [larga_f, C("A es cierta", "v('A')"), C("B es cierta", "v('B')")]])
    assert not _codigo(d, "longitud")
    # Si la larga falsa desaparece, la destacada es siempre verdadera y el aviso vuelve.
    d["componentes"][4][0] = C("ninguna", "False")
    assert [a for a in _codigo(d, "longitud") if "comp 3[0]" in a.donde and "más larga" in a.mensaje]
