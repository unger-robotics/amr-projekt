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
- Vision-Pipeline: Host-seitiger Hailo-8L Runner (HTTPS MJPEG) → UDP → Docker-Receiver → Gemini Cloud
- Vision-Toggle: Dashboard AI-Schalter steuert Broadcast-Gate in Bridge + `/vision/enable` Topic fuer TTS
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
| `use_camera` | False | v4l2 Kamera-Knoten |
| `use_dashboard` | False | WebSocket/MJPEG Bridge |
| `use_vision` | False | Hailo UDP Receiver + Gemini |
| `use_audio` | False | Audio-Feedback-Knoten |
| `use_can` | False | CAN-Bus Bridge |
| `use_tts` | False | TTS-Sprachausgabe (Gemini-Semantik) |
| `use_respeaker` | False | ReSpeaker DoA |
| `use_voice` | False | Sprachsteuerung (ReSpeaker + Gemini STT) |

Beispiel: `./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false use_dashboard:=True use_rviz:=False`

## Feste Architekturregeln

- Die MCU-Firmware besteht aus zwei getrennten PlatformIO-Projekten
- Drive-Knoten und Sensor-Knoten werden getrennt gebaut, geflasht und betrieben
- ROS2 Humble laeuft auf dem Pi 5 im Docker-Container
- Die serielle Kommunikation erfolgt ueber getrennte Pfade pro Knoten
- Dashboard, Kamera, Vision (AI-Toggle), Audio und ReSpeaker sind optionale Teilsysteme
- Cliff-Safety-Node multiplext /cmd_vel: blockiert bei Cliff ODER Ultraschall < 80 mm
- Dashboard-Entwicklung erfordert zwei Prozesse: `use_dashboard:=True` im Launch UND `cd dashboard && npm run dev -- --host 0.0.0.0` (HTTPS via mkcert)
- Lange Tabellen, Parameterlisten und Betriebsprozeduren nicht in diese Datei duplizieren

## Neues ROS2-Skript hinzufuegen

Das Symlink-Pattern erfordert vier Schritte:

1. Skript anlegen: `amr/scripts/<name>.py`
2. Symlink erzeugen: `cd amr/pi5/ros2_ws/src/my_bot/my_bot && ln -s ../../../../../scripts/<name>.py`
3. Entry-Point in `setup.py` ergaenzen: `'<name> = my_bot.<name>:main'`
4. Rebuild: `cd amr/docker && ./run.sh colcon build --packages-select my_bot --symlink-install`

## Build-Befehle

### MCU Firmware (PlatformIO, zwei getrennte Projekte)

**Wichtig:** Beim Upload immer `-e <environment>` angeben! `pio run -t upload` ohne `-e` flasht ALLE Environments — das letzte ueberschreibt die vorherigen.

```bash
# Drive-Node (Antrieb, PID, Odometrie, LED):
cd amr/mcu_firmware/drive_node && pio run -e drive_node                      # Kompilieren
cd amr/mcu_firmware/drive_node && pio run -e drive_node -t upload -t monitor # Upload + Monitor
cd amr/mcu_firmware/drive_node && pio run -e led_test -t upload -t monitor   # LED/MOSFET-Diagnose

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
./verify.sh                                 # Gesamttest (Packages, Devices, Build)
```

**run.sh-Verhalten:** `run.sh` ist der zentrale Container-Wrapper. Bei jedem Aufruf:
- Startet den Container via `docker compose up -d` falls nicht laufend
- Aktualisiert serielle Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) im Container (Host-udev greift im Container nicht)
- Gibt Ports 5173, 5174, 8082, 9090 frei falls belegt
- Prueft `camera-v4l2-bridge.service` bei `use_camera:=True`

Nach ESP32-Flash muessen Symlinks aktualisiert werden — naechster `./run.sh`-Aufruf erledigt das automatisch.

**Docker Named Volumes:** Build-Artefakte (`ros2_build`, `ros2_install`, `ros2_log`) sind persistente Docker Volumes. Colcon-Rebuilds sind dadurch ueber Container-Neustarts hinweg gecached.

### Dashboard (React + Vite + TypeScript + Tailwind)

```bash
cd dashboard/
npm install && npm run dev -- --host 0.0.0.0   # Entwicklung (https://amr.local:5173)
npm run build                  # Produktion (tsc + vite build)
npm run lint                   # ESLint
```

HTTPS via mkcert-Zertifikate (`amr.local+5.pem` / `amr.local+5-key.pem` in `dashboard/`).
WebSocket-Server (`wss://`, Port 9090) und MJPEG-Server (`https://`, Port 8082) nutzen
dieselben Zertifikate via Volume-Mount (`/dashboard:ro` im Container). Ohne Zertifikate:
Backend (dashboard_bridge.py) faellt auf HTTP/WS zurueck; Vite-Frontend erfordert Zertifikate (crasht ohne).

### Vollstart (alle Subsysteme, vier Terminals)

```bash
# T1: Reset beider ESP32-S3 via DTR/RTS, dann Geraete pruefen
lsusb
ls /dev/ttyACM* /dev/ttyUSB* /dev/amr_*
cd ~/amr-projekt
python3 -c "import serial,time;[exec('s=serial.Serial(p,921600);s.dtr=False;s.rts=True;time.sleep(0.1);s.dtr=True;s.rts=False;s.close()') for p in ['/dev/amr_drive','/dev/amr_sensor']]"

# T2: Full-Stack Launch mit allen Subsystemen
cd ~/amr-projekt/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_camera:=True use_vision:=True use_audio:=True use_respeaker:=True use_tts:=True use_voice:=True

# T3: Hailo-8L Vision auf dem Host (Python 3.13, erfordert GEMINI_API_KEY)
cd ~/amr-projekt
python3 amr/scripts/host_hailo_runner.py

# T4: Vite-Dev-Server Dashboard
cd ~/amr-projekt/dashboard
npm run dev -- --host 0.0.0.0
```

T1 ist einmalig (Reset + Pruefung), T2-T4 sind langlebige Prozesse in separaten Terminals.

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

### Tests und Validierung

Keine automatisierten Unit-Tests — Validierung erfolgt experimentell ueber ROS2-Testknoten auf dem Pi 5 (V-Modell-Phasenplan):

```bash
cd amr/docker/
./run.sh ros2 run my_bot motor_test          # Motortest
./run.sh ros2 run my_bot encoder_test        # Encoder-Validierung
./run.sh ros2 run my_bot pid_tuning          # PID-Abstimmung
./run.sh ros2 run my_bot imu_test            # IMU-Kalibrierung
./run.sh ros2 run my_bot sensor_test         # Sensor-Gesamttest
./run.sh ros2 run my_bot slam_validation     # SLAM-Validierung
./run.sh ros2 run my_bot nav_test            # Navigationstest
./run.sh ros2 run my_bot nav_square_test     # Quadratfahrt-Test
./run.sh ros2 run my_bot docking_test        # ArUco-Docking-Test
./run.sh ros2 run my_bot can_validation_test # CAN-Bus-Validierung
```

Testprozeduren und erwartete Messwerte: `planung/testanleitung_phase*.md` und `planung/messprotokoll_phase*.md`

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
- **C++ Benennung** (.clang-tidy): `CamelCase` Klassen, `camelBack` Methoden/Funktionen, `lower_case` Variablen/Parameter
- **TypeScript**: ESLint Flat Config, React Hooks Plugin (dashboard/eslint.config.js)

## Relevante Projektpfade

- `amr/mcu_firmware/drive_node/` — ESP32-S3 Firmware Antrieb (eigene CLAUDE.md in `amr/mcu_firmware/`)
- `amr/mcu_firmware/sensor_node/` — ESP32-S3 Firmware Sensorik
- `amr/pi5/ros2_ws/src/my_bot/` — ROS2 ament_python-Paket (Launch, Knoten, Config)
- `amr/docker/` — Dockerfile, docker-compose.yml, run.sh, verify.sh
- `amr/scripts/` — Validierungsskripte, ROS2-Runtime-Knoten, Host-Only-Tools
- `scripts/` — Wartungsskripte (update_dependencies.sh, rover_wartung.sh)
- `docs/` — Architektur-, Build-, System- und Validierungsdokumentation
- `dashboard/` — React/Vite Benutzeroberflaeche
- `projektarbeit/` — Projektarbeit (Markdown-Kapitel + LaTeX)
- `planung/vortrag/` — Beamer-Praesentationen
- `hardware/` — Hardware-Spezifikationen + LaTeX-Dokument

Detaillierte CLAUDE.md fuer Teilbereiche: `amr/CLAUDE.md`, `amr/mcu_firmware/CLAUDE.md` und `dashboard/CLAUDE.md`.

## Typische Arbeitsreihenfolge

1. Aufgabenbereich identifizieren
2. Nur fachlich passende Dateien lesen
3. Betroffene Schnittstellen und Abhaengigkeiten bestimmen
4. Aenderung mit minimalem Umfang umsetzen
5. Build-, Start- oder Pruefpfad angeben
6. Auswirkungen auf Architektur, Topics, Parameter und Dokumentation benennen

## Python-Versionen

- **Container (ROS2 Humble):** Python 3.10 — alle ROS2-Nodes und Skripte in `amr/scripts/`
- **Host (Pi 5):** Python 3.13 — nur `host_hailo_runner.py` (Hailo SDK erfordert Host-Python)

## Umgebungsvariablen

- `GEMINI_API_KEY`: Erforderlich fuer Vision (`use_vision`), TTS (`use_tts`) und Sprachsteuerung (`use_voice`). Wird via `docker-compose.yml` aus der Host-Umgebung in den Container durchgereicht (`${GEMINI_API_KEY:-}`). Ohne Key starten die betroffenen Knoten mit Fehler.

## Harte Randbedingungen

- Serielle Geraetepfade und Parallelzugriffe vorsichtig behandeln (Docker-Container benoetigt Symlink-Update via `run.sh` nach ESP32-Flash)
- micro-ROS-Konfigurationen sind node-spezifisch
- Schnittstellen zwischen ESP32, ROS2 und Dashboard nur konsistent aendern
- Hardware-nahe Parameter nicht ohne Begruendung umbenennen oder verschieben
- Bei Launch-, Topic- oder TF-Aenderungen immer Folgeeffekte auf Navigation, Dashboard und Validierung beachten

## Detaildokumente

Technische Referenzen in `docs/`:
- `architecture.md` — Systemarchitektur und Komponentenuebersicht
- `ros2_system.md` — ROS2-Topics, TF-Baum, QoS
- `firmware.md` — MCU-Firmware-Details
- `dashboard.md` — Dashboard-Architektur und WebSocket-Protokoll
- `vision_pipeline.md` — Hailo/Gemini Vision-Pipeline
- `serial_port_management.md` — udev-Regeln und Seriennummern
- `robot_parameters.md` — Physikalische Parameter (Raddurchmesser, PID, Batterie)
- `build_and_deploy.md`, `validation.md`, `quality_checks.md` — Build, Validierung, Qualitaet

Schreibstil und Literatur: `docs/projektarbeit_style.md`, `docs/literature_workflow.md`

Planung und Betrieb: `planung/` enthaelt Testanleitungen, Messprotokolle, Systemdokumentation, Benutzerhandbuch und Netzwerkkonfiguration
