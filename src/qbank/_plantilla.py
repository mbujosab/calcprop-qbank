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

"""Plantilla de proyecto para un banco de preguntas (``qbank-init``).

    qbank-init mi-banco                 # crea mi-banco/ a partir de la plantilla
    python -m qbank._plantilla mi-banco # equivalente

La plantilla vive en ``qbank/plantilla/`` dentro del paquete: preguntas de
ejemplo, scripts de generación AMC/Moodle, Makefile, un guion para escribir
preguntas en Python (``nueva_pregunta.py``) y un README con el flujo de
trabajo. Tras crear el proyecto: ``cd mi-banco && make lint && make amc``.
"""
import argparse as _argparse
import shutil as _shutil
import sys as _sys
from importlib import resources as _resources
from pathlib import Path as _Path

__all__ = ['ruta_plantilla', 'crear', 'main']

_IGNORAR = _shutil.ignore_patterns('__pycache__', '*.pyc', 'build')


def ruta_plantilla():
    """Directorio de la plantilla dentro del paquete instalado."""
    return _Path(str(_resources.files('qbank').joinpath('plantilla')))


def crear(destino, forzar=False):
    """Copia la plantilla en ``destino`` y devuelve su ruta.

    Se niega a escribir en un directorio no vacío salvo con ``forzar=True``
    (entonces sobreescribe los ficheros de la plantilla y conserva el resto).
    """
    destino = _Path(destino)
    if destino.exists() and any(destino.iterdir()) and not forzar:
        raise FileExistsError(f"{destino} existe y no está vacío (usa --forzar para sobreescribir)")
    _shutil.copytree(ruta_plantilla(), destino, ignore=_IGNORAR, dirs_exist_ok=True)
    return destino


def main(argv=None):
    parser = _argparse.ArgumentParser(
        prog='qbank-init',
        description='Crea un proyecto de banco de preguntas qbank a partir de la plantilla.')
    parser.add_argument('destino', help='carpeta del nuevo proyecto (se crea si no existe)')
    parser.add_argument('--forzar', action='store_true',
                        help='escribir aunque la carpeta no esté vacía (sobreescribe la plantilla)')
    args = parser.parse_args(argv)
    try:
        destino = crear(args.destino, args.forzar)
    except OSError as e:                     # existe y no está vacío, es un fichero, sin permisos…
        print(f"qbank-init: {e}", file=_sys.stderr)
        return 1
    print(f"Proyecto creado en {destino}/\n"
          f"\n  cd {destino}\n"
          f"  make lint        # comprueba las preguntas de ejemplo\n"
          f"  make amc         # PDF de revisión (vista profe) en build/amc/\n"
          f"\nEl flujo completo está en {destino}/README.org")
    return 0


if __name__ == '__main__':
    _sys.exit(main())
