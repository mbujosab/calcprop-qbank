# Copyright (C) 2020-2026  Andrés Bujosa, Marcos Bujosa
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

try:
    from importlib.metadata import version as _version
    __version__ = _version("calcprop-qbank")
except Exception:                   # sin metadatos: p. ej. src/ en el path sin instalar
    __version__ = "desconocida"

from qbank._quiz import *
from qbank._export import *
from qbank._json import *
from qbank._lint import lint, tabla_mundos, Aviso
try:
    from qbank._widgets import *
except ImportError:
    pass
