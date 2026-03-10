# =============================================================================
# Makefile fuer AMR-Praesentationen und Design
# =============================================================================

LATEX = xelatex
# nonstopmode zeigt Fehler an, bricht aber nicht interaktiv ab
LATEX_FLAGS = -interaction=nonstopmode
STY_FILE = amr-style.sty

# Dateien fuer Kolloquium
TEX_SRC = vortrag_kolloquium.tex
TEX_PDF = vortrag_kolloquium.pdf

# Dateien fuer Showcase
PANDOC = pandoc
MD_SRC = vortrag_showcase.md
MD_PDF = vortrag_showcase.pdf

# Datei fuer Farbdesign (DIN A4 Quer)
DESIGN_SRC = farbdesign.tex
DESIGN_PDF = farbdesign.pdf

# Finde alle SVGs im Ordner und definiere die Ziel-PDFs
SVGS = $(wildcard *.svg)
SVG_PDFS = $(SVGS:.svg=.pdf)

# Standard-Ziel: Baue erst alle Bilder, dann alle Dokumente
all: $(SVG_PDFS) $(TEX_PDF) $(MD_PDF) $(DESIGN_PDF)

# 1. Konvertiere SVGs in PDFs via Inkscape (Warnungen werden unterdrueckt)
%.pdf: %.svg
	@echo "Konvertiere $< zu $@..."
	@inkscape $< --export-filename=$@ 2>/dev/null

# 2. Kolloquium: LaTeX zu PDF (abhaengig von Bildern und Style-Datei)
$(TEX_PDF): $(TEX_SRC) $(STY_FILE) $(SVG_PDFS)
	@echo "Kompiliere $< mit XeLaTeX (Durchlauf 1/2)..."
	@$(LATEX) $(LATEX_FLAGS) $<
	@echo "Kompiliere $< mit XeLaTeX (Durchlauf 2/2)..."
	@$(LATEX) $(LATEX_FLAGS) $<
	@echo "$@ erfolgreich erstellt."

# 3. Showcase: Markdown zu PDF via Pandoc
$(MD_PDF): $(MD_SRC) $(SVG_PDFS)
	@echo "Generiere $@ via Pandoc..."
	@$(PANDOC) $< -t beamer -o $@ --slide-level=2 --pdf-engine=xelatex -V aspectratio=169
	@echo "$@ erfolgreich erstellt."

# 4. Farbdesign: LaTeX zu PDF (nur ein Durchlauf noetig)
$(DESIGN_PDF): $(DESIGN_SRC)
	@echo "Kompiliere $< mit XeLaTeX..."
	@$(LATEX) $(LATEX_FLAGS) $<
	@echo "$@ erfolgreich erstellt."

# Aufraeumen
clean:
	rm -f *.aux *.log *.out *.toc *.nav *.snm *.vrb
	rm -rf svg-inkscape/

tidy: clean

.PHONY: all clean tidy
