---
description: >-
  Dokumentationsstruktur, Schreibregeln, LaTeX-Build
  und uebergreifende Qualitaetspruefungen.
robots: noindex, nofollow
---

# Dokumentation und Qualitaetssicherung

## Zweck

Uebersicht ueber Dokumentationsstruktur, Schreibregeln, LaTeX-Build-Prozess, V-Modell-Validierung und uebergreifende Qualitaetspruefungen.

## Regel

Diese Datei ist die zentrale Referenz fuer Dokumentationskonventionen. Detaillierte Pruefkonfigurationen stehen in `docs/quality_checks.md`, Validierungsskripte in `docs/validation.md`.

---

## 1. Dokumentationsstruktur

| Verzeichnis | Inhalt | Format |
|---|---|---|
| `projektarbeit/` | Wissenschaftliche Projektarbeit (7 Kapitel) | Markdown + LaTeX |
| `projektarbeit/latex/` | LaTeX-Kompilation der Projektarbeit | `.tex`, `.cls`, `.bib` |
| `planung/` | Roadmap, Testanleitungen, Messprotokolle, Abschlussbericht | Markdown |
| `planung/vortrag/` | Beamer-Praesentationen | LaTeX |
| `hardware/` | Hardware-Spezifikationen, Datenblaetter, Kosten | Markdown + LaTeX |
| `hardware/latex/` | Hardware-Spezifikation als PDF | LaTeX |
| `docs/` | Technische Referenzdokumente | Markdown |

---

## 2. Projektarbeit

7 Kapitel als Markdown-Quelldateien in `projektarbeit/`:

| Kapitel | Datei | Inhalt |
|---|---|---|
| 1 | `kapitel_01_einleitung.md` | Ausgangssituation, Zielsetzung, Methodik, Aufbau |
| 2 | `kapitel_02_grundlagen.md` | AMR, Modellierung, Sensorik, Software, SLAM, Nav2 |
| 3 | `kapitel_03_anforderungsanalyse.md` | Szenario, Randbedingungen, Anforderungsliste |
| 4 | `kapitel_04_systemkonzept.md` | Morphologischer Kasten, Architektur, Mechanik, Software, Regelung |
| 5 | `kapitel_05_implementierung.md` | Hardware, Firmware, ROS2, Kalibrierung, Navigation, Integration |
| 6 | `kapitel_06_validierung.md` | Testkonzept, Subsystem-Tests, Navigation, Docking, Ressourcen, Diskussion |
| 7 | `kapitel_07_fazit.md` | Zusammenfassung, kritische Wuerdigung, Ausblick |

LaTeX-Dateien in `projektarbeit/latex/`:

| Datei | Funktion |
|---|---|
| `main.tex` | Hauptdokument (bindet Kapitel ein) |
| `amr.cls` | Dokumentklasse (NICHT aendern ohne zwingenden Grund) |
| `literatur.bib` | BibTeX-Literaturdatenbank |
| `kap1.tex` bis `kap7.tex` | Kapitel (aus Markdown konvertiert oder direkt in LaTeX) |

---

## 3. Sprache und Stil

### Allgemeine Regeln

- **Deutsch** im wissenschaftlich-technischen Stil
- Aktiv, neutral, konsistent
- Ein Thema pro Abschnitt
- Ablauf: Daten → Regel → Schluss → Konsequenz
- Formeln und Einheiten mit Bezug und sauberer Schreibweise

### Umlaut-Regel

- **Markdown-Dateien im Git-Repository:** Keine UTF-8-Umlaute. Stattdessen ae, oe, ue, ss verwenden.
- **LaTeX-/Pandoc-Quelltexte** (`.tex`-Dateien): UTF-8-Umlaute zulaessig.

### Terminologie-Norm (zwingend)

Normierte Begriffe in allen Dokumenten konsistent verwenden:

| Normierter Begriff | NICHT verwenden |
|---|---|
| Fahrkern | "Drive-Node" im Fliesstext |
| Sensor- und Sicherheitsbasis | "Sensor-Node" im Fliesstext |
| Lokalisierung und Kartierung | "Lokalisierung, Kartierung" (kein Komma) |
| Navigation | "Navigations-..." |
| Bedien- und Leitstandsebene | "Dashboard-Ebene", "Navigations- und Leitstandsebene" |
| Benutzeroberflaeche | "Frontend", "UI", "Web-UI" |
| Knoten | "Node" im deutschen Fliesstext |
| Projektfrage (PF1, PF2, PF3) | "Forschungsfrage", "FF1-FF3" |
| Sprachschnittstelle | — |
| Sicherheitslogik | — |
| Freigabelogik | — |
| Missionskommando | — |
| Intent | — |

### Drei Ebenen

| Ebene | Bezeichnung | Umfang |
|---|---|---|
| A | Fahrkern | Antrieb, Regelung, Odometrie, Sensorik |
| B | Bedien- und Leitstandsebene | Dashboard, Fernsteuerung, Telemetrie |
| C | Intelligente Interaktion | Sprache, Semantik, KI-Erkennung |

Vollstaendige Stilregeln: `docs/projektarbeit_style.md`.

---

## 4. LaTeX-Build

```bash
cd projektarbeit/latex/ && make        # Projektarbeit PDF (2x pdflatex + bibtex)
cd projektarbeit/latex/ && make once   # Schnelldurchlauf (1x pdflatex)
cd hardware/latex/ && make             # Hardware-Spezifikation PDF
cd planung/vortrag/ && make            # Beamer-Vortrag PDF
```

---

## 5. V-Modell und Testphasen

Die Validierung folgt einem V-Modell mit 5 Phasen:

| Phase | Funktionsbereich | Testanleitung | Messprotokoll |
|---|---|---|---|
| 1+2 | Fahrkern + Sensor- und Sicherheitsbasis | `planung/testanleitung_phase1_phase2.md` | `planung/messprotokoll_phase1_phase2.md` |
| 3 | Lokalisierung und Kartierung | `planung/testanleitung_phase3.md` | `planung/messprotokoll_phase3.md` |
| 4 | Navigation + Docking | `planung/testanleitung_phase4.md` | `planung/messprotokoll_phase4.md` |
| 5 | Systemintegration | `planung/testanleitung_phase5.md` | `planung/messprotokoll_phase5.md` |

### Quantitative Akzeptanzkriterien (Auswahl)

| Test | Messgroesse | Kriterium |
|---|---|---|
| SLAM (Phase 3) | ATE (RMSE) | < 0.20 m |
| SLAM (Phase 3) | TF-Rate map→odom | >= 1.5 Hz |
| Navigation (Phase 4) | Positionsfehler (xy) | < 0.10 m |
| Navigation (Phase 4) | Orientierungsfehler (yaw) | < 0.15 rad |
| Docking (Phase 4) | Erfolgsquote | 100% (10/10) |
| Cliff-Latenz | End-to-End | < 50 ms |

### Ergebnisformat

Jedes Validierungsskript erzeugt eine JSON-Datei (`<name>_results.json`). Aggregation:

```bash
python3 amr/scripts/validation_report.py
```

Vollstaendige Skript-Referenz: `docs/validation.md`.

---

## 6. Qualitaetspruefungen

### Gesamtlauf (11 Hooks)

```bash
pre-commit run --all-files
```

### Einzelpruefungen nach Domaene

| Domaene | Befehl | Konfiguration |
|---|---|---|
| Python | `ruff check amr/` | `ruff.toml` |
| Python Format | `ruff format --check amr/` | `ruff.toml` |
| Python Types | `mypy --config-file mypy.ini` | `mypy.ini` |
| C++ Format | `clang-format --dry-run --Werror amr/mcu_firmware/...` | `.clang-format` |
| TypeScript | `cd dashboard && npm run lint` | `dashboard/eslint.config.js` |
| TypeScript Types | `cd dashboard && npx tsc --noEmit` | `dashboard/tsconfig.json` |

Detaillierte Konfiguration aller Hooks: `docs/quality_checks.md`.

---

## 7. Referenzdokumente

| Dokument | Inhalt |
|---|---|
| `docs/architecture.md` | Systemarchitektur, Kommunikationspfade |
| `docs/build_and_deploy.md` | Build- und Deployment-Prozesse |
| `docs/ros2_system.md` | ROS2 Topics, TF, Launch-Parameter, QoS |
| `docs/dashboard.md` | Dashboard WebSocket-Protokoll, Seiten, Sicherheit |
| `docs/firmware.md` | MCU-Firmware Architektur, Module, CAN-Bus |
| `docs/vision_pipeline.md` | Vision-Pipeline (Hailo, Gemini) |
| `docs/serial_port_management.md` | USB-Port-Zuordnung (udev) |
| `docs/robot_parameters.md` | Roboter-Parameter |
| `docs/validation.md` | Validierungsskripte und Messkriterien |
| `docs/quality_checks.md` | Pre-commit Hooks und Linting-Konfiguration |
| `docs/projektarbeit_style.md` | Stilregeln fuer die Projektarbeit |
| `docs/literature_workflow.md` | Literatur-Workflow |
| `planung/roadmap.md` | Projekt-Roadmap |
| `planung/abschlussbericht.md` | Abschlussbericht |
| `planung/systemdokumentation.md` | Systemdokumentation |
| `planung/benutzerhandbuch.md` | Benutzerhandbuch |
