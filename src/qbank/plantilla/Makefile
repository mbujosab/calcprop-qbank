# ── Banco de preguntas qbank ─────────────────────────────────────────────
# Objetivos:
#   make lint         — comprueba las preguntas con qbank.lint (sin LaTeX)
#   make tabla PREGUNTA=L-01-Nombre — lint de una pregunta con su tabla de mundos
#                       (con o sin .json)
#   make amc          — build/amc/<pregunta>.pdf: vista profe (todas las cuestiones con marcas)
#   make lectura      — build/lectura/<leccion>-lectura.pdf: vista de lectura, un documento
#                       por lección (ejemplos por mundo, alternativas por hueco con V/F y exp)
#   make amc-student  — build/amc-student/<pregunta>.pdf: vista alumno (variantes)
#   make moodle       — build/moodle/<pregunta>-moodle.xml (+ PDF de revisión) y
#                       build/moodle/_banco.xml con todas, para importar en Moodle
#   make all          — amc, amc-student y moodle (por defecto; lectura va aparte)
#   make clean        — borra build/
#
# LECCION limita cualquier objetivo a las preguntas L-NN-* de esas lecciones:
#   make amc LECCION=2        make lint LECCION=2-3        make moodle LECCION=1,3
#
# PYTHON es el intérprete que tiene instalado qbank >= 0.6 (por defecto, python3
# del PATH: activa el entorno virtual antes, o pasa PYTHON=/ruta/al/venv/bin/python).
#
# Solo se recompila lo que ha cambiado: los scripts gen_*.py reescriben un .tex
# únicamente si su contenido cambia, y cada PDF/XML depende de su .tex.
# ─────────────────────────────────────────────────────────────────────────

PYTHON       ?= python3
LATEX_AMC    ?= pdflatex -interaction=nonstopmode
LATEX_MOODLE ?= pdflatex -interaction=nonstopmode -halt-on-error
NOMBRES      := $(shell $(PYTHON) scripts/_comun.py --leccion "$(LECCION)")

.PHONY: all comprueba lint lint-previo tabla amc amc-student moodle lectura lectura-pdf clean

all: amc amc-student moodle

# ¿Tiene el intérprete elegido un qbank reciente (con qbank.lint y versión >=
# QBANK_MIN)? Un python3 del sistema puede cargar un qbank viejo (p. ej. de
# ~/.local) que no lo tiene: el mensaje dice qué hacer.
QBANK_MIN := 0.6
comprueba:
	@$(PYTHON) -c "import re, qbank, qbank.lint; \
	  v = getattr(qbank, '__version__', '0'); \
	  n = tuple(int(x) for x in re.findall(r'\d+', v)[:2]); \
	  raise SystemExit(0 if not n or n >= tuple(int(x) for x in '$(QBANK_MIN)'.split('.')) else 1)" \
	  2>/dev/null || { \
	  echo "ERROR: qbank no está instalado en '$(PYTHON)', o es anterior a la $(QBANK_MIN)."; \
	  echo "       Activa el entorno virtual del banco o usa: make ... PYTHON=/ruta/al/venv/bin/python"; \
	  exit 1; }

lint: comprueba
	@if test -z "$(NOMBRES)"; then echo "lint: no hay preguntas que comprobar$(if $(LECCION), en LECCION=$(LECCION))"; \
	 else $(PYTHON) -m qbank.lint $(addprefix preguntas/,$(addsuffix .json,$(NOMBRES))); fi

# PREGUNTA admite el nombre con o sin .json (y con preguntas/ delante).
tabla: comprueba
	@test -n "$(PREGUNTA)" || { echo "uso: make tabla PREGUNTA=L-01-Nombre"; exit 1; }
	@$(PYTHON) -m qbank.lint preguntas/$(notdir $(PREGUNTA:.json=)).json --tabla

# Antes de exportar, lint: un ERROR (p. ej. un «%» sin barra, que LaTeX toma
# por comentario y no siempre delata) detiene la exportación.
lint-previo: comprueba
	@test -z "$(NOMBRES)" || $(PYTHON) -m qbank.lint --quiet $(addprefix preguntas/,$(addsuffix .json,$(NOMBRES))) \
	  || { echo "ERROR: lint ha encontrado errores; corrígelos antes de exportar"; exit 1; }

# Con la lista de preguntas vacía no hay nada que compilar (y un sub-make sin
# objetivos ejecutaría «all» y entraría en bucle).
amc: lint-previo
	$(PYTHON) scripts/gen_amc.py --leccion "$(LECCION)"
	@test -z "$(NOMBRES)" || $(MAKE) --no-print-directory $(addprefix build/amc/,$(addsuffix .pdf,$(NOMBRES)))

amc-student: lint-previo
	$(PYTHON) scripts/gen_amc_student.py --leccion "$(LECCION)"
	@test -z "$(NOMBRES)" || $(MAKE) --no-print-directory $(addprefix build/amc-student/,$(addsuffix .pdf,$(NOMBRES)))

# Lectura: la lista de documentos (uno por lección) solo se conoce tras
# ejecutar el script, de ahí el sub-make con wildcard.
lectura: lint-previo
	$(PYTHON) scripts/gen_lectura.py --leccion "$(LECCION)"
	@$(MAKE) --no-print-directory lectura-pdf

lectura-pdf: $(patsubst %.tex,%.pdf,$(wildcard build/lectura/*-lectura.tex))

moodle: lint-previo
	$(PYTHON) scripts/gen_moodle.py --leccion "$(LECCION)"
	@test -z "$(NOMBRES)" || $(MAKE) --no-print-directory $(addprefix build/moodle/,$(addsuffix -moodle.xml,$(NOMBRES)))
	$(PYTHON) scripts/merge_moodle_xml.py

# AMC: <pregunta>-doc.tex es un documento autónomo que carga <pregunta>.tex.
# Sin -halt-on-error: automultiplechoice emite algún «Missing $» no fatal que
# corrige solo y el PDF se produce igualmente. Pero un «%» sin barra o un
# \element roto también «producen» un PDF (vacío), así que además se buscan en
# el .log los errores que de verdad lo invalidan.
ERRORES_LATEX := 'Emergency stop|File ended while|No group mode|Undefined control sequence|Runaway argument'

build/amc/%.pdf: build/amc/%-doc.tex build/amc/%.tex
	@echo "  pdflatex $*"
	@cd build/amc && rm -f $*.pdf; $(LATEX_AMC) -jobname=$* $*-doc.tex > /dev/null; \
	 if ! test -f $*.pdf || grep -qE $(ERRORES_LATEX) $*.log; then \
	   rm -f $*.pdf; echo "  ERROR en $* (ver build/amc/$*.log)"; exit 1; fi

build/amc-student/%.pdf: build/amc-student/%-doc.tex build/amc-student/%.tex
	@echo "  pdflatex $*"
	@cd build/amc-student && rm -f $*.pdf; $(LATEX_AMC) -jobname=$* $*-doc.tex > /dev/null; \
	 if ! test -f $*.pdf || grep -qE $(ERRORES_LATEX) $*.log; then \
	   rm -f $*.pdf; echo "  ERROR en $* (ver build/amc-student/$*.log)"; exit 1; fi

build/lectura/%.pdf: build/lectura/%.tex
	@echo "  pdflatex $*"
	@cd build/lectura && rm -f $*.pdf; $(LATEX_AMC) $*.tex > /dev/null; \
	 if ! test -f $*.pdf || grep -qE $(ERRORES_LATEX) $*.log; then \
	   rm -f $*.pdf; echo "  ERROR en $* (ver build/lectura/$*.log)"; exit 1; fi

# Moodle: el paquete moodle escribe <pregunta>-moodle.xml al compilar el .tex.
build/moodle/%-moodle.xml: build/moodle/%.tex
	@echo "  pdflatex $*"
	@cd build/moodle && $(LATEX_MOODLE) $*.tex > /dev/null \
	 || { echo "  ERROR en $* (ver build/moodle/$*.log)"; exit 1; }
	@$(PYTHON) scripts/fix_moodle_xml.py $@

clean:
	rm -rf build/
