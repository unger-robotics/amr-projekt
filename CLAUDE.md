# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektziel

Projektarbeit: Autonomer Mobiler Roboter (AMR) fuer Intralogistik mit KLT-Transport.

Kurzarchitektur:
- Raspberry Pi 5 als ROS2-, SLAM-, Navigation- und Integrationsrechner
- XIAO ESP32-S3 Drive-Node fuer Antrieb, PID, Odometrie und LED
- XIAO ESP32-S3 Sensor-Node fuer Ultraschall, Cliff, IMU, Batterie und Servo
- Verbindung zwischen Pi 5 und MCU-Knoten ueber micro-ROS/UART und CAN-Bus (Dual-Path)

## Arbeitsregeln

- Sprache: Deutsch im wissenschaftlich-technischen Stil
- In Markdown-Dateien keine UTF-8-Umlaute, sondern ae, oe, ue, ss (gilt fuer Git-Markdown; in LaTeX-/Pandoc-Quelltexten der Projektarbeit sind UTF-8-Umlaute zulaessig)
- udev-Seriennummern fuer die ESP32-S3-Zuordnung stehen in docs/serial_port_management.md
- Terminologie konsistent beibehalten
- Keine Annahmen ueber ungelesene Dateien, Messwerte oder Hardware-Zustaende treffen
- Kleine, pruefbare Aenderungen bevorzugen
- Folgen fuer Architektur, Schnittstellen und Sicherheit explizit beachten

## Zentrale Begriffe

- Drive-Node (Fahrkern): ESP32-S3 fuer Motorregelung, Encoder, Odometrie, LED
- Sensor-Node (Sensor- und Sicherheitsbasis): ESP32-S3 fuer Sensorik, Batterie, IMU, Servo und Naeherungssensoren
- Pi 5: zentrale ROS2- und Docker-Laufzeit
- micro-ROS Agent: Serial-Bridge zwischen ROS2 und den ESP32-Knoten
- Dashboard (Bedien- und Leitstandsebene): Weboberflaeche fuer Telemetrie und Fernsteuerung

## Terminologie-Norm (aus planung/roadmap.md)

Normierte Begriffe in allen Dokumenten konsistent verwenden:
- Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung (nicht Komma!)
- Navigation, Bedien- und Leitstandsebene (nicht "Navigations- und Leitstandsebene")
- Sprachschnittstelle, Sicherheitslogik, Freigabelogik, Missionskommando, Intent
- Benutzeroberflaeche (nicht "Frontend", "UI", "Web-UI")
- Knoten (nicht "Node" im deutschen Fliesstext)
- Projektfrage (nicht "Forschungsfrage"), Kuerzel PF1, PF2, PF3 (nicht FF1-FF3)
- Drei Ebenen: A (Fahrkern), B (Bedien- und Leitstandsebene), C (Intelligente Interaktion)

## Architektur (Big Picture)

```
[Drive-Node ESP32-S3] --micro-ROS/UART 921600--> [Raspberry Pi 5 (Docker: ROS2 Humble)]
  Antrieb, PID, Odometrie, LED                     Nav2, SLAM Toolbox, micro-ROS Agents

[Sensor-Node ESP32-S3] --micro-ROS/UART 921600--> [Pi 5] --WebSocket/MJPEG--> [Dashboard (React)]
  IMU, Ultraschall, Cliff, Batterie, Servo

[Beide ESP32-S3] --CAN-Bus 1 Mbit/s (optional)--> can_bridge_node im Container
```

- MCU Dual-Core: Core 0 = micro-ROS Executor, Core 1 = Echtzeit-Datenerfassung + CAN
- `full_stack.launch.py` orchestriert alle ROS2-Nodes (micro-ROS Agents, SLAM, Nav2, Dashboard, Vision)
- Vision-Pipeline: Host-seitiger Hailo-8L Runner → UDP → Docker-Receiver → Gemini Cloud
- Skripte in `amr/scripts/` werden als Symlinks in `my_bot/my_bot/` referenziert und via `setup.py` entry_points installiert

## Launch-Argumente (full_stack.launch.py)

Haeufig genutzte Toggles (`use_<name>:=True/False`):

| Argument | Default | Funktion |
|---|---|---|
| `use_slam` | True | SLAM Toolbox (Kartierung) |
| `use_nav` | True | Nav2 (Navigation) |
| `use_rviz` | True | RViz2 (Visualisierung) |
| `use_sensors` | True | Sensor-Node micro-ROS Agent |
| `use_cliff_safety` | True | Cliff + Ultraschall Sicherheitslogik |
| `use_camera` | False | v4l2 Kamera-Node |
| `use_dashboard` | False | WebSocket/MJPEG Bridge |
| `use_vision` | False | Hailo UDP Receiver + Gemini |
| `use_audio` | False | Audio-Feedback-Node |
| `use_can` | False | CAN-Bus Bridge |
| `use_tts` | False | TTS-Sprachausgabe (Gemini-Semantik) |
| `use_respeaker` | False | ReSpeaker DoA |

Beispiel: `./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false use_dashboard:=True use_rviz:=False`

## Feste Architekturregeln

- Die MCU-Firmware besteht aus zwei getrennten PlatformIO-Projekten
- Drive-Knoten und Sensor-Knoten werden getrennt gebaut, geflasht und betrieben
- ROS2 Humble laeuft auf dem Pi 5 im Docker-Container
- Die serielle Kommunikation erfolgt ueber getrennte Pfade pro Knoten
- Dashboard (zwei Seiten: Steuerung + Details), Kamera, Vision, Audio und ReSpeaker sind optionale Teilsysteme
- Cliff-Safety-Node multiplext /cmd_vel: blockiert bei Cliff ODER Ultraschall < 80 mm
- Dashboard-Entwicklung erfordert zwei Prozesse: `use_dashboard:=True` im Launch UND `cd dashboard && npm run dev -- --host 0.0.0.0` (HTTPS via mkcert)
- Lange Tabellen, Parameterlisten und Betriebsprozeduren nicht in diese Datei duplizieren

## Neues ROS2-Skript hinzufuegen

Das Symlink-Pattern erfordert vier Schritte:

1. Skript anlegen: `amr/scripts/<name>.py`
2. Symlink erzeugen: `cd amr/pi5/ros2_ws/src/my_bot/my_bot && ln -s ../../../../scripts/<name>.py`
3. Entry-Point in `setup.py` ergaenzen: `'<name> = my_bot.<name>:main'`
4. Rebuild: `cd amr/docker && ./run.sh colcon build --packages-select my_bot --symlink-install`

## Build-Befehle

### MCU Firmware (PlatformIO, zwei getrennte Projekte)

**Wichtig:** Beim Upload immer `-e <environment>` angeben! `pio run -t upload` ohne `-e` flasht ALLE Environments — das letzte ueberschreibt die vorherigen.

```bash
# Drive-Node (Antrieb, PID, Odometrie, LED):
cd amr/mcu_firmware/drive_node && pio run -e drive_node                      # Kompilieren
cd amr/mcu_firmware/drive_node && pio run -e drive_node -t upload -t monitor # Upload + Monitor
cd amr/mcu_firmware/drive_node && pio run -e led_test -t upload -t monitor   # LED-Diagnose

# Sensor-Node (Ultraschall, Cliff, IMU, Batterie, Servo):
cd amr/mcu_firmware/sensor_node && pio run -e sensor_node                      # Kompilieren
cd amr/mcu_firmware/sensor_node && pio run -e sensor_node -t upload -t monitor # Upload + Monitor
cd amr/mcu_firmware/sensor_node && pio run -e servo_test -t upload -t monitor  # Servo-Kalibrierung
```

Erster Build pro Knoten: ~15 Min (micro-ROS aus Source). Folgebuilds gecached.

### ROS2 (Docker auf Pi 5)

```bash
cd amr/docker/
docker compose build                        # Image bauen (~15-20 Min)
./run.sh colcon build --packages-select my_bot --symlink-install
./run.sh ros2 launch my_bot full_stack.launch.py                    # Full-Stack
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false     # Nur SLAM
./run.sh exec bash                          # Zweites Terminal im Container
./verify.sh                                 # Gesamttest
```

### Dashboard (React + Vite + TypeScript + Tailwind)

```bash
cd dashboard/
npm install && npm run dev     # Entwicklung (https://amr.local:5173)
npm run build                  # Produktion (tsc + vite build)
npm run lint                   # ESLint
```

HTTPS via mkcert-Zertifikate (`amr.local+5.pem` / `amr.local+5-key.pem` in `dashboard/`).
WebSocket-Server (`wss://`, Port 9090) und MJPEG-Server (`https://`, Port 8082) nutzen
dieselben Zertifikate via Volume-Mount (`/dashboard:ro` im Container). Ohne Zertifikate
Fallback auf unverschluesseltes HTTP/WS.

### LaTeX-Dokumente

```bash
cd projektarbeit/latex/ && make        # Projektarbeit PDF (2x pdflatex)
cd projektarbeit/latex/ && make once   # Schnelldurchlauf (1x)
cd hardware/latex/ && make             # Hardware-Spezifikation PDF
cd planung/vortrag/ && make            # Beamer-Vortrag PDF
```

### Linting

```bash
ruff check amr/                    # Python-Lint
ruff format --check amr/           # Python-Format
mypy --config-file mypy.ini        # Python Type-Check
clang-format --dry-run --Werror amr/mcu_firmware/drive_node/src/*.cpp amr/mcu_firmware/drive_node/include/*.hpp amr/mcu_firmware/sensor_node/src/*.cpp amr/mcu_firmware/sensor_node/include/*.hpp  # C++ Format
pre-commit run --all-files         # Alle Hooks (ruff, mypy, clang-format, eslint, trailing-whitespace)
```

Einmalig einrichten: `pip3 install pre-commit && pre-commit install`

### Wartung und Abhaengigkeiten

```bash
# Projekt-Abhaengigkeiten aktualisieren (npm, pip, PlatformIO, Docker, ROS2-Image)
./scripts/update_dependencies.sh

# Systemwartung mit AMR-Diagnose (Temperatur, Speicher, Services, USB, EEPROM)
sudo ./scripts/rover_wartung.sh            # Vollstaendig mit apt-Updates
sudo ./scripts/rover_wartung.sh --check    # Nur Diagnose, keine Aenderungen
```

## Code-Style-Kurzreferenz

- **Python**: Zeilenlaenge 100, Python 3.10, Double Quotes, isort-Import-Sortierung (ruff.toml)
- **C++**: Zeilenlaenge 100, 4 Spaces, LLVM-basiert, Braces Attach, C++17 (.clang-format)
- **C++ Benennung** (.clang-tidy): `CamelCase` Klassen, `camelBack` Methoden, `lower_case` Funktionen/Variablen/Parameter
- **TypeScript**: ESLint Flat Config, React Hooks Plugin (dashboard/eslint.config.js)

## Relevante Projektpfade

- `amr/mcu_firmware/drive_node/` — ESP32-S3 Firmware Antrieb (eigene CLAUDE.md in `amr/mcu_firmware/`)
- `amr/mcu_firmware/sensor_node/` — ESP32-S3 Firmware Sensorik
- `amr/pi5/ros2_ws/src/my_bot/` — ROS2 ament_python-Paket (Launch, Nodes, Config)
- `amr/docker/` — Dockerfile, docker-compose.yml, run.sh, verify.sh
- `amr/scripts/` — Validierungsskripte, ROS2-Runtime-Nodes, Host-Only-Tools
- `scripts/` — Wartungsskripte (update_dependencies.sh, rover_wartung.sh)
- `dashboard/` — React/Vite Benutzeroberflaeche
- `projektarbeit/` — Projektarbeit (Markdown-Kapitel + LaTeX)
- `planung/vortrag/` — Beamer-Praesentationen
- `hardware/` — Hardware-Spezifikationen + LaTeX-Dokument

Detaillierte CLAUDE.md fuer den technischen Kern: `amr/CLAUDE.md` und `amr/mcu_firmware/CLAUDE.md`.

## Typische Arbeitsreihenfolge

1. Aufgabenbereich identifizieren
2. Nur fachlich passende Dateien lesen
3. Betroffene Schnittstellen und Abhaengigkeiten bestimmen
4. Aenderung mit minimalem Umfang umsetzen
5. Build-, Start- oder Pruefpfad angeben
6. Auswirkungen auf Architektur, Topics, Parameter und Dokumentation benennen

## Harte Randbedingungen

- Serielle Geraetepfade und Parallelzugriffe vorsichtig behandeln (Docker-Container benoetigt Symlink-Update via `run.sh` nach ESP32-Flash)
- micro-ROS-Konfigurationen sind node-spezifisch
- Schnittstellen zwischen ESP32, ROS2 und Dashboard nur konsistent aendern
- Hardware-nahe Parameter nicht ohne Begruendung umbenennen oder verschieben
- Bei Launch-, Topic- oder TF-Aenderungen immer Folgeeffekte auf Navigation, Dashboard und Validierung beachten

## Detaildokumente

- `docs/architecture.md`
- `docs/build_and_deploy.md`
- `docs/ros2_system.md`
- `docs/dashboard.md`
- `docs/vision_pipeline.md`
- `docs/serial_port_management.md`
- `docs/robot_parameters.md`
- `docs/validation.md`
- `docs/quality_checks.md`
- `docs/projektarbeit_style.md`
- `docs/literature_workflow.md`
- `planung/abschlussbericht.md`
- `planung/systemdokumentation.md`
- `planung/benutzerhandbuch.md`
- `planung/testanleitung_phase1_phase2.md`
- `planung/messprotokoll_phase1_phase2.md`
- `planung/testanleitung_phase3.md`
- `planung/messprotokoll_phase3.md`
- `planung/testanleitung_phase4.md`
- `planung/messprotokoll_phase4.md`
- `planung/testanleitung_phase5.md`
- `planung/messprotokoll_phase5.md`
