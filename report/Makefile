# Build the report. Requires latexmk (ships with MiKTeX, already on PATH).
#
#   make          -> main.pdf (runs pdflatex/bibtex as many times as needed)
#   make watch    -> rebuild on every save
#   make clean    -> remove aux files, keep the PDF
#   make distclean-> remove aux files and the PDF

MAIN := main

.PHONY: all watch clean distclean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex preamble.tex references.bib $(wildcard sections/*.tex)
	latexmk -pdf -halt-on-error -interaction=nonstopmode $(MAIN).tex

watch:
	latexmk -pdf -pvc -halt-on-error -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -c

distclean:
	latexmk -C
