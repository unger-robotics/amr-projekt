# Literatur-Workflow

## Zweck

Ablage- und Arbeitsregeln fuer Quellen, PDFs und Kernaussagen der Bachelorarbeit.

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

Die Datei `00_Uebersicht_Querverweise.md` verknuepft Quellen mit Kapiteln der Bachelorarbeit.

## LaTeX-Workflow

Die Bachelorarbeit liegt in `bachelorarbeit/latex/`:

```
bachelorarbeit/latex/
  main.tex          # Hauptdokument
  amr.cls           # Dokumentklasse
  literatur.bib     # BibTeX-Datenbank
  kap1.tex - kap7.tex  # Kapitel
  Makefile          # Build-Automatisierung
```

### Zitierkonventionen

- BibTeX-Eintraege in `literatur.bib` pflegen
- Schluessel-Format: `<Autor><Jahr>` (z.B. `Macenski2022`)
- Einheiten mit Bezug und sauberer Schreibweise (LaTeX-Mathe konsistent)
- Begriffe, Annahmen und Randbedingungen vor der Bewertung nennen

### Stilregeln (aus bachelorarbeit_style.md)

- Wissenschaftlich-technischer Stil: aktiv, neutral, konsistent
- Keine UTF-8-Umlaute in Markdown-Dateien (ae, oe, ue, ss)
- Ein Thema pro Abschnitt
- Ablauf: Daten → Regel → Schluss → Konsequenz

## Verknuepfung Quelle — Kapitel

Jede Quelle soll mindestens einem Kapitel zugeordnet sein. Die Zuordnung erfolgt in `00_Uebersicht_Querverweise.md` und durch `\cite{}`-Befehle in den `.tex`-Dateien.
