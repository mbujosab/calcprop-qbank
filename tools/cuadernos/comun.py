"""Piezas comunes de los generadores de Tutorial.ipynb, Demo.ipynb y Ejemplos.ipynb."""
import json

# El mismo ayudante de impresión, idéntico en los tres cuadernos.
AYUDANTE = r'''
import itertools

def muestra(p, n=2, instances=1, profe=False, con_exp=True):
    """Imprime las n primeras variantes de p tal como las verá el alumno o, con
    profe=True, los n primeros mundos de la vista profe (todas las cuestiones de
    cada hueco).

    Marcas: [✓] correcta, [✗] incorrecta, [·] rechazada por su precond (solo en la
    vista profe, con el motivo); → la explicación (exp), si con_exp. Si
    export.last_choice está activo añade la opción por defecto, como hacen los
    exportadores."""
    if profe:
        iterador, rotulo = p.por_partes_profe(verbose=False), "Mundo"
    else:
        iterador, rotulo = p.por_partes(instances=instances), "Variante"
    for etiqueta, partes in itertools.islice(iterador, n):
        print(f"── {rotulo} {etiqueta} ──")
        for enunciado, cuestiones in partes:
            print(f"   {enunciado.strip()}")
            for texto, vf, activa, *exp in cuestiones:
                if not activa:
                    print(f"   [·] {texto}   ({vf})")
                    continue
                print(f"   [{'✓' if vf else '✗'}] {texto}")
                if con_exp and exp and exp[0]:
                    print(f"         → {exp[0]}")
            if p.export.get("last_choice"):
                if profe:
                    print("   [+] Ninguna de las anteriores   (opción por defecto: correcta"
                          " en las variantes cuyas opciones son todas falsas)")
                else:
                    ninguna = not any(vf is True for _, vf, *_ in cuestiones)
                    print(f"   [{'✓' if ninguna else '✗'}] Ninguna de las anteriores   (opción por defecto)")
        print()
'''


class Cuaderno:
    def __init__(self, prefijo):
        self.prefijo, self.cells = prefijo, []

    def _id(self):
        return f"{self.prefijo}-{len(self.cells):02d}"

    def md(self, s):
        self.cells.append({"cell_type": "markdown", "id": self._id(), "metadata": {},
                           "source": s.strip("\n")})

    def code(self, s):
        self.cells.append({"cell_type": "code", "id": self._id(), "metadata": {},
                           "execution_count": None, "outputs": [], "source": s.strip("\n")})

    def write(self, ruta):
        nb = {"cells": self.cells,
              "metadata": {"kernelspec": {"display_name": "Python (qbank)", "language": "python",
                                          "name": "qbank"},
                           "language_info": {"name": "python"}},
              "nbformat": 4, "nbformat_minor": 5}
        for c in nb["cells"]:
            s = c["source"]
            c["source"] = [l + "\n" for l in s.split("\n")[:-1]] + [s.split("\n")[-1]]
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(ruta, "celdas:", len(self.cells))
