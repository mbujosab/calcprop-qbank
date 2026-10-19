;;; web.el --- exporta los .org de la documentación a docs/*.html  -*- lexical-binding: t -*-
;; Copyright (C) 2026  Marcos Bujosa
;; SPDX-License-Identifier: GPL-3.0-or-later
;;
;; Uso (lo llama tools/web.sh desde la raíz del repositorio):
;;   emacs --batch -l tools/web.el
;;
;; Los ajustes de HTML van aquí y no en los .org, para no tocar su exportación
;; a PDF: hoja de estilos propia sin CSS ni JavaScript de Org, fórmulas sin
;; MathJax y un índice de dos niveles en las páginas que no lo
;; piden en el .org.

(require 'ox-html)

(setq org-export-use-babel nil            ; los #+RESULTS se exportan como están
      org-confirm-babel-evaluate nil
      org-html-doctype "html5"
      org-html-html5-fancy t
      org-html-head-include-default-style nil
      org-html-head-include-scripts nil
      org-html-head "<link rel=\"stylesheet\" href=\"style.css\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
      org-html-mathjax-template ""        ; sin MathJax: ver qbank-web-formula
      org-html-htmlize-output-type nil    ; código sin colorear (sin htmlize)
      org-html-validation-link nil
      org-html-postamble nil
      make-backup-files nil)

;; Sin MathJax: las fórmulas sencillas fuera del código ($N$, $2 \times 2 = 4$,
;; $\land$…) se escriben con caracteres Unicode; las que tengan otras macros
;; se dejan tal cual se escriben en LaTeX.
(defconst qbank-web-macros
  '(("\\times" . "×") ("\\cdot" . "·") ("\\pm" . "±") ("\\neq" . "≠")
    ("\\leq" . "≤") ("\\geq" . "≥") ("\\perp" . "⊥") ("\\land" . "∧")
    ("\\lor" . "∨") ("\\implies" . "⇒") ("\\iff" . "⇔")
    ("\\Leftrightarrow" . "⇔") ("\\Rightarrow" . "⇒") ("\\alpha" . "α")
    ("\\theta" . "θ") ("\\lambda" . "λ") ("^2" . "²")))

(defun qbank-web-formula (fragmento _contenido _info)
  "Sustituye a `org-html-latex-fragment': Unicode o el LaTeX tal cual."
  (let ((texto (org-element-property :value fragmento)))
    (if (not (string-match "\\`\\$\\(.*\\)\\$\\'" texto))
        (org-html-encode-plain-text texto)
      (let ((f (match-string 1 texto)))
        (dolist (m qbank-web-macros)
          (setq f (replace-regexp-in-string (regexp-quote (car m)) (cdr m) f t t)))
        (if (string-match-p "[\\^_{}]" f)
            (org-html-encode-plain-text texto)       ; como se escribe en LaTeX
          (format "<span class=\"math\">%s</span>" (org-html-encode-plain-text f)))))))

(advice-add 'org-html-latex-fragment :override #'qbank-web-formula)

(defun qbank-web-exporta (fuente destino &optional con-indice)
  "Exporta FUENTE a DESTINO (rutas desde la raíz del repositorio).
Con CON-INDICE añade un índice de dos niveles."
  (setq destino (expand-file-name destino))   ; si no, relativa al .org
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
