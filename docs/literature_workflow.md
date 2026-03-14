# Literatur-Workflow

## Zweck

Ablage- und Arbeitsregeln fuer Quellen, PDFs und Kernaussagen der Projektarbeit.

## Verzeichnisstruktur

```
sources/
  01_Macenski_2022_ROS2_Arch.pdf
  02_Macenski_2023_Nav2_Survey.pdf
  ...
  kernaussagen/
    00_Uebersicht_Querverweise.md
    01_ROS2_Architektur_Kernaussagen.md
    02_Nav2_SLAM_Kernaussagen.md
    ...
```

## Dateibenennung

PDFs folgen dem Schema: `<Nr>_<Autor>_<Jahr>_<Kurzthema>.pdf`

Beispiel: `01_Macenski_2022_ROS2_Arch.pdf`

Kernaussagen-Dateien verwenden dasselbe Nummernschema: `<Nr>_<Thema>_Kernaussagen.md`

## Kernaussagen-Extraktion

Fuer jede relevante Quelle wird eine Kernaussagen-Datei in `sources/kernaussagen/` angelegt. Inhalt:

1. Bibliografische Angaben
2. Zentrale Thesen und Ergebnisse
3. Relevanz fuer die eigene Arbeit
4. Querverweise zu betroffenen Kapiteln

Die Datei `00_Uebersicht_Querverweise.md` verknuepft Quellen mit Kapiteln der Projektarbeit.

## Projektarbeit-Struktur

Die Projektarbeit existiert in zwei Formaten:

- **Markdown-Kapitel** in `projektarbeit/`: `kapitel_01_einleitung.md` bis `kapitel_07_fazit.md`
- **LaTeX-Kapitel** in `projektarbeit/latex/`: `kap1.tex` bis `kap7.tex`

```
projektarbeit/
  kapitel_01_einleitung.md - kapitel_07_fazit.md  # Markdown-Kapitel
  latex/
    main.tex          # Hauptdokument
    amr.cls           # Dokumentklasse
    literatur.bib     # BibTeX-Datenbank
    kap1.tex - kap7.tex  # LaTeX-Kapitel
    Makefile          # Build-Automatisierung
```

### Zitierkonventionen

- BibTeX-Eintraege in `literatur.bib` pflegen
- Schluessel-Format: `<Autor><Jahr>` (z.B. `Macenski2022`)
- Einheiten mit Bezug und sauberer Schreibweise (LaTeX-Mathe konsistent)
- Begriffe, Annahmen und Randbedingungen vor der Bewertung nennen

### Stilregeln (aus projektarbeit_style.md)

- Wissenschaftlich-technischer Stil: aktiv, neutral, konsistent
- Keine UTF-8-Umlaute in Markdown-Dateien (ae, oe, ue, ss); in LaTeX-/Pandoc-Quelltexten sind UTF-8-Umlaute zulaessig
- Terminologie-Norm beachten (siehe docs/projektarbeit_style.md): Projektfrage (nicht Forschungsfrage), PF1/PF2/PF3, Benutzeroberflaeche (nicht Frontend/UI), Knoten (nicht Node im Fliesstext)
- Ein Thema pro Abschnitt
- Ablauf: Daten -> Regel -> Schluss -> Konsequenz

## Verknuepfung Quelle -- Kapitel

Jede Quelle soll mindestens einem Kapitel zugeordnet sein. Die Zuordnung erfolgt in `00_Uebersicht_Querverweise.md` und durch `\cite{}`-Befehle in den `.tex`-Dateien.
