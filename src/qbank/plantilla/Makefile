# ── Banco de preguntas qbank ─────────────────────────────────────────────
# Objetivos:
#   make lint         — comprueba las preguntas con qbank.lint (sin LaTeX)
#   make amc          — build/amc/<pregunta>.pdf: vista profe (todas las cuestiones con marcas)
#   make amc-student  — build/amc-student/<pregunta>.pdf: vista alumno (variantes)
#   make moodle       — build/moodle/<pregunta>-moodle.xml (+ PDF de revisión) y
#                       build/moodle/_banco.xml con todas, para importar en Moodle
#   make all          — los tres (por defecto)
#   make clean        — borra build/
#
# LECCION limita cualquier objetivo a las preguntas L-NN-* de esas lecciones:
#   make amc LECCION=2        make lint LECCION=2-3        make moodle LECCION=1,3
#
# Solo se recompila lo que ha cambiado: los scripts gen_*.py reescriben un .tex
# únicamente si su contenido cambia, y cada PDF/XML depende de su .tex.
# ─────────────────────────────────────────────────────────────────────────

PYTHON       ?= python3
LATEX_AMC    ?= pdflatex -interaction=nonstopmode
LATEX_MOODLE ?= pdflatex -interaction=nonstopmode -halt-on-error
NOMBRES      := $(shell $(PYTHON) scripts/_comun.py --leccion "$(LECCION)")

.PHONY: all lint amc amc-student moodle clean

all: amc amc-student moodle

lint:
	$(PYTHON) -m qbank.lint $(addprefix preguntas/,$(addsuffix .json,$(NOMBRES)))

amc:
	$(PYTHON) scripts/gen_amc.py --leccion "$(LECCION)"
	@$(MAKE) --no-print-directory $(addprefix build/amc/,$(addsuffix .pdf,$(NOMBRES)))

amc-student:
	$(PYTHON) scripts/gen_amc_student.py --leccion "$(LECCION)"
	@$(MAKE) --no-print-directory $(addprefix build/amc-student/,$(addsuffix .pdf,$(NOMBRES)))

moodle:
	$(PYTHON) scripts/gen_moodle.py --leccion "$(LECCION)"
	@$(MAKE) --no-print-directory $(addprefix build/moodle/,$(addsuffix -moodle.xml,$(NOMBRES)))
	$(PYTHON) scripts/merge_moodle_xml.py

# AMC: <pregunta>-doc.tex es un documento autónomo que carga <pregunta>.tex.
# Sin -halt-on-error: automultiplechoice emite algún «Missing $» no fatal que
# corrige solo y el PDF se produce igualmente, así que se comprueba que exista.
build/amc/%.pdf: build/amc/%-doc.tex build/amc/%.tex
	@echo "  $*"
	@cd build/amc && rm -f $*.pdf; $(LATEX_AMC) -jobname=$* $*-doc.tex > /dev/null; \
	 test -f $*.pdf || { echo "  ERROR en $* (ver build/amc/$*.log)"; exit 1; }

build/amc-student/%.pdf: build/amc-student/%-doc.tex build/amc-student/%.tex
	@echo "  $*"
	@cd build/amc-student && rm -f $*.pdf; $(LATEX_AMC) -jobname=$* $*-doc.tex > /dev/null; \
	 test -f $*.pdf || { echo "  ERROR en $* (ver build/amc-student/$*.log)"; exit 1; }

# Moodle: el paquete moodle escribe <pregunta>-moodle.xml al compilar el .tex.
build/moodle/%-moodle.xml: build/moodle/%.tex
	@echo "  $*"
	@cd build/moodle && $(LATEX_MOODLE) $*.tex > /dev/null \
	 || { echo "  ERROR en $* (ver build/moodle/$*.log)"; exit 1; }
	@$(PYTHON) scripts/fix_moodle_xml.py $@

clean:
	rm -rf build/
