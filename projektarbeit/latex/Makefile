# =============================================================================
#  Makefile – amr LaTeX-Projekt
# =============================================================================
#  Verwendung:
#    make            → PDF erzeugen (2× pdflatex für Verweise)
#    make once       → 1× pdflatex (Schnelldurchlauf)
#    make clean      → Hilfsdateien löschen
#    make distclean  → alles außer Quellen löschen
#    make watch      → kontinuierlich bauen (benötigt latexmk)
#    make check      → Warnungen/Fehler anzeigen
#    make wc         → Wörter zählen (benötigt texcount)
# =============================================================================

# -------------------------  Konfiguration  -----------------------------------
MAIN     := main
TEX      := pdflatex
TEXFLAGS := -interaction=nonstopmode -halt-on-error -file-line-error
BIBTOOL  := bibtex
LATEXMK  := latexmk

# Quelldateien (für Abhängigkeitserkennung)
CLS      := amr.cls
# Pfade angepasst: Sucht nun im Hauptverzeichnis nach kap*.tex
SOURCES  := $(MAIN).tex $(CLS) $(wildcard kap*.tex) $(wildcard bilder/*.pdf)

# -------------------------  Standardziel  ------------------------------------
.PHONY: all once clean distclean watch check wc help

all: $(MAIN).pdf

# -------------------------  PDF erzeugen  ------------------------------------
$(MAIN).pdf: $(SOURCES)
	@echo "=== 1. Durchlauf ==="
	$(TEX) $(TEXFLAGS) $(MAIN).tex
	@echo "=== 2. Durchlauf (Verweise) ==="
	$(TEX) $(TEXFLAGS) $(MAIN).tex
	@echo "=== Fertig: $@ ==="

# Schnelldurchlauf (1×, ohne Verweise)
once:
	$(TEX) $(TEXFLAGS) $(MAIN).tex

# -------------------------  Mit BibTeX  --------------------------------------
# Falls BibTeX statt \begin{thebibliography} verwendet wird:
# bib: $(SOURCES)
# 	$(TEX) $(TEXFLAGS) $(MAIN).tex
# 	$(BIBTOOL) $(MAIN)
# 	$(TEX) $(TEXFLAGS) $(MAIN).tex
# 	$(TEX) $(TEXFLAGS) $(MAIN).tex

# -------------------------  Kontinuierlich bauen  ----------------------------
watch:
	$(LATEXMK) -pdf -pvc -interaction=nonstopmode $(MAIN).tex

# -------------------------  Prüfungen  ---------------------------------------
check: $(MAIN).log
	@echo "=== Warnungen ==="
	@grep -i "warning" $(MAIN).log || echo "(keine)"
	@echo ""
	@echo "=== Underfull/Overfull Boxes ==="
	@grep -c "Overfull" $(MAIN).log || true
	@grep -c "Underfull" $(MAIN).log || true
	@echo ""
	@echo "=== Undefined References ==="
	@grep -i "undefined" $(MAIN).log || echo "(keine)"

wc:
	@command -v texcount >/dev/null 2>&1 && \
		texcount -inc -utf8 $(MAIN).tex || \
		echo "texcount nicht installiert: brew install texcount / apt install texcount"

# -------------------------  Aufräumen  ---------------------------------------
AUXFILES := aux log out toc lof lot bbl blg bcf run.xml \
            nav snm vrb fdb_latexmk fls synctex.gz idx ind ilg

clean:
	@echo "Lösche Hilfsdateien ..."
	@for ext in $(AUXFILES); do \
		rm -f *.$$ext; \
	done
	@rm -f texput.log

distclean: clean
	@echo "Lösche PDF ..."
	@rm -f $(MAIN).pdf

# -------------------------  Hilfe  -------------------------------------------
help:
	@echo ""
	@echo "  amr – Build-Targets"
	@echo "  ================================"
	@echo "  make            PDF erzeugen (2× pdflatex)"
	@echo "  make once       Schnelldurchlauf (1×)"
	@echo "  make watch      Kontinuierlich bauen (latexmk)"
	@echo "  make check      Warnungen/Fehler anzeigen"
	@echo "  make wc         Wörter zählen"
	@echo "  make clean      Hilfsdateien löschen"
	@echo "  make distclean  Alles außer Quellen löschen"
	@echo ""
