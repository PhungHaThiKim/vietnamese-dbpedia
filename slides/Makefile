# Build the slides. Requires latexmk (ships with MiKTeX, already on PATH).
#
#   make          -> main.pdf
#   make watch    -> rebuild on every save
#   make clean    -> remove aux files, keep the PDF
#   make distclean-> remove aux files and the PDF
#
# make is not on PATH on this machine; `latexmk -pdf main.tex` does the same.

MAIN := main

.PHONY: all watch clean distclean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex preamble.tex $(wildcard sections/*.tex) $(wildcard figures/*)
	latexmk -pdf -halt-on-error -interaction=nonstopmode $(MAIN).tex

watch:
	latexmk -pdf -pvc -halt-on-error -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -c

distclean:
	latexmk -C
