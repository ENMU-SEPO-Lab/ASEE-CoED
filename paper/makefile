TEX = latexmk -f -pdf -pdflatex="pdflatex -interaction=nonstopmode" -use-make
TEXDIR = ./tex
FIGDIR = ./fig

.PHONY: all view

all : build view

view :
	open main.pdf

build : main.tex
	$(TEX) main.tex

#commit: clean
#	git add $(wildcard $(shell find . -name "*.tex"))
#	git add $(wildcard $(shell find . -name "*.pdf"))
#	git add $(wildcard $(shell find . -name "*.png"))
#	git add *.{sty,bib}
#	git add Makefile
#	git commit -m 'doc dissertation'
#	git push
clean:
	latexmk -CA
	rm -f ./$(TEXDIR)/*.{aux,dvi,log,bbl,blg,brf,fls,toc,thm,out,fdb_latexmk,lof,lot,log}
	rm -f ./*.{aux,dvi,log,bbl,blg,brf,fls,toc,thm,out,fdb_latexmk,lof,lot,pdf,log}
	chmod -x $(wildcard ./$(TEXDIR)/*.tex ./*.tex)

