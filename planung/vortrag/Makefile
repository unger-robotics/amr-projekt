# Variablen
LATEX = pdflatex
LATEX_FLAGS = -interaction=batchmode
STY_FILE = amr-dashboard.sty

# Suche alle .tex Dateien im aktuellen Verzeichnis
SOURCES = $(wildcard *.tex)
# Erzeuge die Namen der Ziel-PDFs
PDFS = $(SOURCES:.tex=.pdf)

# Standard-Ziel: Alle PDFs erstellen
all: $(PDFS)

# Regel zum Erstellen der PDFs
# Abhängig von der jeweiligen .tex Datei UND der zentralen .sty Datei
%.pdf: %.tex $(STY_FILE)
	@echo "Kompiliere $<..."
	@$(LATEX) $(LATEX_FLAGS) $<
	@echo "$@ erfolgreich erstellt."

# Hilfsfunktion: Temporäre LaTeX-Dateien löschen
clean:
	rm -f *.aux *.log *.out *.pdf

# Hilfsfunktion: Nur temporäre Dateien löschen, PDFs behalten
tidy:
	rm -f *.aux *.log *.out

.PHONY: all clean tidy
