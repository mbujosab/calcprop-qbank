"""Los .org literate (CalcPropQuiz.org, CalcPropExport.org) son la fuente de
src/qbank/*.py: este test comprueba que el tangle de los .org reproduce src/
byte a byte. Si falla, edita el .org y ejecuta `python tools/orgtangle.py write`
(o tanglea desde Emacs). Se omite fuera del repositorio (p. ej. en el sdist)."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ORGS = [REPO / 'CalcPropQuiz.org', REPO / 'CalcPropExport.org']

pytestmark = pytest.mark.skipif(
    not all(o.exists() for o in ORGS) or not (REPO / 'tools' / 'orgtangle.py').exists(),
    reason="fuentes .org no disponibles (fuera del repositorio)")


@pytest.fixture(scope="module")
def orgtangle():
    sys.path.insert(0, str(REPO / 'tools'))
    import orgtangle
    return orgtangle


def test_src_coincide_con_org(orgtangle):
    difs = orgtangle.diferencias(REPO)
    assert not difs, "src/ no coincide con los .org:\n\n" + "\n\n".join(d for _, d in difs)


def test_todos_los_modulos_tienen_origen_literate(orgtangle):
    targets = set(orgtangle.targets_src(REPO))
    modulos = {f"src/qbank/{p.name}" for p in (REPO / 'src' / 'qbank').glob('*.py')}
    assert modulos <= targets, f"módulos sin bloque :tangle en los .org: {sorted(modulos - targets)}"
