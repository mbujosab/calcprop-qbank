# Copyright (C) 2020-2026  Marcos Bujosa
# GNU General Public License v3 or later — see <https://www.gnu.org/licenses/>

from qbank import *
p = ProblemaTipo([
      "Considere ",
      [
          Supuesto("$\\mathcal{A}$ ", v("A")),
          Supuesto("$\\mathcal{B}$ ", v("B")),
      ],
      [
          Supuesto("y que $\\mathcal{A}\\Rightarrow\\mathcal{C}$. ", v("A") >> v("C")),
          Supuesto("y que $\\mathcal{B}\\Leftrightarrow\\mathcal{D}$. ", v("B") ** v("D")),
      ],
      "Indique qué opción es correcta: ",
      [
          Cuestion("Entonces $\\mathcal{C}$ es verdadero", v("C")),
          Cuestion("Entonces $\\mathcal{D}$ es verdadero", v("D")),
          Cuestion("Entonces $\\mathcal{E}$ es verdadero", v("E"), v("D")),
      ],
])
nombre = "EjemploMoodle"
directorio = "../ejemplos/"
QuizMoodleLastCh(nombre, directorio, p)
