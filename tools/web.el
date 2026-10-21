;;; web.el --- exporta los .org de la documentación a docs/*.html  -*- lexical-binding: t -*-
;; Copyright (C) 2026  Marcos Bujosa
;; SPDX-License-Identifier: GPL-3.0-or-later
;;
;; Uso (lo llama tools/web.sh desde la raíz del repositorio):
;;   emacs --batch -l tools/web.el
;;
;; Los ajustes de HTML van aquí y no en los .org, para no tocar su exportación
;; a PDF: hoja de estilos propia sin CSS ni JavaScript de Org (la única
;; excepción es MathJax, un solo <script>, para las fórmulas de la Guía y el
;; Manual), <title> sin marcado y un índice de dos niveles en las páginas que
;; no lo piden en el .org.

(require 'ox-html)

(setq org-export-use-babel nil            ; los #+RESULTS se exportan como están
      org-confirm-babel-evaluate nil
      org-html-doctype "html5"
      org-html-html5-fancy t
      org-html-head-include-default-style nil
      org-html-head-include-scripts nil
      org-html-head "<link rel=\"stylesheet\" href=\"style.css\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
      org-html-with-latex 'mathjax
      ;; Org pasa $…$ a \(…\) y $$…$$ a \[…\], los delimitadores por defecto
      ;; de MathJax 3, que además no entra en <pre> ni <code>.
      org-html-mathjax-template
      "<script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js\"></script>"
      org-html-htmlize-output-type nil    ; código sin colorear (sin htmlize)
      org-html-validation-link nil
      org-html-postamble nil
      org-export-time-stamp-file nil      ; sin la hora en el HTML: regenerar
      make-backup-files nil)              ; sin cambios no ensucia el historial

;; El <title> lleva el título en texto plano, pero Org deja en él las marcas
;; =código= y ~código~ («Manual de uso de =qbank=»): se quitan al final.
(defun qbank-web-titulo (html _backend _info)
  (replace-regexp-in-string
   "<title>\\(.*?\\)</title>"
   (lambda (m)
     (concat "<title>"
             (replace-regexp-in-string "[=~]\\([^=~<]+\\)[=~]" "\\1"
                                       (match-string 1 m))
             "</title>"))
   html t t))

(add-hook 'org-export-filter-final-output-functions #'qbank-web-titulo)

(defun qbank-web-exporta (fuente destino &optional con-indice)
  "Exporta FUENTE a DESTINO (rutas desde la raíz del repositorio).
Con CON-INDICE añade un índice de dos niveles."
  (setq destino (expand-file-name destino))   ; si no, relativa al .org
  (random "qbank")   ; Org numera ids (orgXXXXXXX) al azar: misma semilla, mismos ids
  (with-current-buffer (find-file-noselect fuente)
    (let ((org-export-before-processing-functions
           (if con-indice
               ;; Una línea #+OPTIONS al final gana a la del principio; se
               ;; añade solo en la copia que exporta Org, no en el fichero.
               (list (lambda (_backend)
                       (goto-char (point-max))
                       (insert "\n#+OPTIONS: toc:2\n")))
             nil)))
      (org-export-to-file 'html destino))
    (message "escrito %s" destino)))

(qbank-web-exporta "index.org"                     "docs/index.html")
(qbank-web-exporta "README.org"                    "docs/readme.html" t)
(qbank-web-exporta "src/qbank/plantilla/README.org" "docs/plantilla.html" t)
(qbank-web-exporta "GuiaDiseno.org"                "docs/guia.html")   ; ya trae #+TOC
(qbank-web-exporta "Manual.org"                    "docs/manual.html") ; ya trae #+TOC
(qbank-web-exporta "Fase5-prueba.org"              "docs/fase5.html")  ; hoja de la Fase 5
(qbank-web-exporta "src/qbank/plantilla/prompts/PROMPT-qbank-generico.org" "docs/prompt.html" t)
