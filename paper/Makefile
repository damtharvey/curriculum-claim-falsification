# Build the acmart SIGPLAN preprint
# Usage: make -C paper

LATEX := pdflatex -interaction=nonstopmode -halt-on-error
BIBTEX := bibtex

.PHONY: all clean

all: main.pdf

main.pdf: main.tex abstract.tex intro.tex related.tex method.tex results.tex limitations.tex appendix.tex references.bib
	$(LATEX) main
	$(BIBTEX) main
	$(LATEX) main
	$(LATEX) main

clean:
	rm -f main.aux main.bbl main.blg main.log main.out main.pdf main.toc
