# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektziel

Projektarbeit nach VDI 2206: Autonomer Mobiler Roboter (AMR / Autonomous Mobile Robot) als skaliertes Modell eines autonomen Fahrzeugs (Kfz). Lernplattform fuer autonomes Fahren.

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
- Dual-Path-Redundanz: Prio 1 micro-ROS/UART → Prio 2 CAN-Fallback (UART > 500 ms Timeout) → Prio 3 Firmware-Stopp (tv=0, tw=0). Pi 5 ist fuer Notstopp nicht erforderlich
- `full_stack.launch.py` orchestriert alle ROS2-Nodes (micro-ROS Agents, SLAM, Nav2, Dashboard, Vision)
- Vision-Pipeline: Host-seitiger Hailo-8L Runner (HTTPS MJPEG) → UDP → Docker-Receiver → Gemini Cloud mit Sensorfusion (Ultraschall + LiDAR, optional, Frische-Pruefung 5 s)
- Vision-Toggle: Dashboard AI-Schalter steuert Broadcast-Gate in Bridge + `/vision/enable` Topic fuer TTS
- Skripte in `amr/scripts/` werden als Symlinks in `my_bot/my_bot/` referenziert und via `setup.py` entry_points installiert

## Launch-Argumente (full_stack.launch.py)

Haeufig genutzte Toggles (`use_<name>:=True/False`):

| Argument | Default | Funktion |
|---|---|---|
| `use_slam` | True | SLAM Toolbox (Kartierung) |
| `use_nav` | True | Nav2 (Navigation) |
| `use_rviz` | False | RViz2 (Visualisierung, erfordert X11) |
| `use_sensors` | True | Sensor-Node micro-ROS Agent |
| `use_cliff_safety` | True | Cliff + Ultraschall Sicherheitslogik |
| `use_camera` | False | v4l2 Kamera-Knoten |
| `use_dashboard` | False | WebSocket/MJPEG Bridge |
| `use_vision` | False | Hailo UDP Receiver + Gemini (Sensorfusion) |
| `use_audio` | False | Audio-Feedback-Knoten |
| `use_can` | False | CAN-Bus Bridge |
| `use_tts` | False | TTS-Sprachausgabe (Gemini-Semantik) |
| `use_respeaker` | False | ReSpeaker DoA |
| `use_voice` | False | Sprachsteuerung (Gemini Audio-STT / faster-whisper Fallback) |

Beispiel: `./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false use_dashboard:=True use_rviz:=False`

## Feste Architekturregeln

- Die MCU-Firmware besteht aus zwei getrennten PlatformIO-Projekten
- Drive-Knoten und Sensor-Knoten werden getrennt gebaut, geflasht und betrieben
- ROS2 Humble laeuft auf dem Pi 5 im Docker-Container
- Die serielle Kommunikation erfolgt ueber getrennte Pfade pro Knoten
- Dashboard, Kamera, Vision (AI-Toggle), Audio und ReSpeaker sind optionale Teilsysteme
- Cliff-Safety-Node multiplext /cmd_vel: blockiert bei Cliff ODER Ultraschall < 100 mm (nur Vorwaertsfahrt; Rueckwaerts und Drehung bleiben erlaubt)
- Dashboard-Entwicklung erfordert zwei Prozesse: `use_dashboard:=True` im Launch UND `cd dashboard && npm run dev -- --host 0.0.0.0` (HTTPS via mkcert)
- Lange Tabellen, Parameterlisten und Betriebsprozeduren nicht in diese Datei duplizieren

## Neues ROS2-Skript hinzufuegen

Das Symlink-Pattern erfordert vier Schritte:

1. Skript anlegen: `amr/scripts/<name>.py`
2. Symlink erzeugen: `cd amr/pi5/ros2_ws/src/my_bot/my_bot && ln -s ../../../../../scripts/<name>.py`
3. Entry-Point in `setup.py` ergaenzen: `'<name> = my_bot.<name>:main'`
4. Rebuild: `cd amr/docker && ./run.sh colcon build --packages-select my_bot --symlink-install`

**Import-Pattern fuer `amr_utils`:** Bei `ros2 run` liegt das Modul unter dem Paket-Namespace. Daher immer den try/except-Fallback verwenden:

```python
try:
    from amr_utils import quaternion_to_yaw
except ImportError:
    from my_bot.amr_utils import quaternion_to_yaw
```

## Voraussetzungen

- Raspberry Pi 5 (Debian Trixie) mit Docker und docker-compose
- PlatformIO CLI (MCU-Firmware)
- Node.js 20+ (Dashboard)
- mkcert (HTTPS-Zertifikate fuer Dashboard)
- `GEMINI_API_KEY` in Host-Umgebung (fuer Vision und TTS; nicht fuer Sprachsteuerung)

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
sudo bash host_setup.sh                     # Einmalig: udev, Gruppen, Kamera-Bridge
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
npx tsc --noEmit               # TypeScript Type-Check (ohne Build)
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
./run.sh ros2 run my_bot kinematic_test      # Kinematik-Validierung
./run.sh ros2 run my_bot imu_test            # IMU-Kalibrierung
./run.sh ros2 run my_bot sensor_test         # Sensor-Gesamttest
./run.sh ros2 run my_bot rotation_test       # Rotationstest (360°)
./run.sh ros2 run my_bot straight_drive_test # Geradeausfahrt-Test
./run.sh ros2 run my_bot rplidar_test        # LiDAR-Validierung
./run.sh ros2 run my_bot slam_validation     # SLAM-Validierung
./run.sh ros2 run my_bot nav_test            # Navigationstest
./run.sh ros2 run my_bot nav_square_test     # Quadratfahrt-Test
./run.sh ros2 run my_bot docking_test        # ArUco-Docking-Test
./run.sh ros2 run my_bot can_validation_test # CAN-Bus-Validierung
./run.sh ros2 run my_bot cliff_latency_test  # Cliff-Latenz-Messung
./run.sh ros2 run my_bot dashboard_latency_test # Dashboard-Latenz-Messung
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
- **TypeScript**: ESLint Flat Config (neues Format, kein `.eslintrc`), React Hooks Plugin (dashboard/eslint.config.js). React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4

## Relevante Projektpfade

- `amr/mcu_firmware/drive_node/` — ESP32-S3 Firmware Antrieb (eigene CLAUDE.md in `amr/mcu_firmware/`)
- `amr/mcu_firmware/sensor_node/` — ESP32-S3 Firmware Sensorik
- `amr/pi5/ros2_ws/src/my_bot/` — ROS2 ament_python-Paket (Launch, Knoten, Config)
- `amr/docker/` — Dockerfile, docker-compose.yml, run.sh, verify.sh
- `amr/scripts/` — Validierungsskripte, ROS2-Runtime-Knoten, Host-Only-Tools
- `scripts/` — Wartungsskripte (update_dependencies.sh, rover_wartung.sh)
- `docs/` — MkDocs-Quelldateien (Online-Doku) + Architektur-, Build-, System- und Validierungsdokumentation
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
- **Syntax-Einschraenkung:** ROS2-Code muss Python-3.10-kompatibel bleiben — kein `match/case`, kein `X | Y` Type-Union, kein `ExceptionGroup`. `ruff.toml` und `mypy.ini` erzwingen `target-version = py310`

## Umgebungsvariablen

- `GEMINI_API_KEY`: Erforderlich fuer Vision (`use_vision`), TTS (`use_tts`) und Gemini Audio-STT in der Sprachsteuerung (`use_voice` mit `use_gemini_stt:=True`). Wird via `docker-compose.yml` aus der Host-Umgebung in den Container durchgereicht (`${GEMINI_API_KEY:-}`). Ohne Key starten Vision/TTS mit Fehler; Sprachsteuerung faellt automatisch auf lokales faster-whisper zurueck (offline, kein API-Key noetig).

## Bekannte Fallstricke

- **Cliff-Safety/Dashboard-Remapping**: Bei `use_cliff_safety:=True` UND `use_dashboard:=True` wird `/cmd_vel` der Dashboard-Bridge auf `/dashboard_cmd_vel` remapped — die Cliff-Safety-Node multiplext dann zwischen Dashboard- und Nav2-Befehlen. Bei `use_cliff_safety:=False` entfaellt das Remapping
- **micro-ROS kein Reconnect**: Verlust der Agent-Verbindung erfordert ESP32 Power-Cycle (kein automatisches Wiederverbinden). Serielle Symlinks nach Flash erst beim naechsten `./run.sh`-Aufruf aktualisiert
- **ESP32 Boot-Reihenfolge**: Sensor-Node braucht ggf. DTR/RTS-Reset NACH Container-Start, da `setup()` blockiert bis der micro-ROS Agent den Port geoeffnet hat. Wenn der Agent vor dem ESP32 startet, verbindet sich der ESP32 nicht automatisch
- **TWAI CAN-Bus Interrupt**: `TWAI_GENERAL_CONFIG_DEFAULT` setzt `intr_flags = ESP_INTR_FLAG_LEVEL1`, der auf ESP32-S3 mit USB-CDC belegt sein kann. Fix: `g_config.intr_flags = 0` (automatische Auswahl). Ohne Fix crasht die Firmware mit `abort()` in `twai_driver_install`
- **Hailo-8L Device-Lock**: `host_hailo_runner.py` haelt `/dev/hailo0` exklusiv. Bei Absturz bleibt das Device gesperrt — vor Neustart `sudo fuser /dev/hailo0` pruefen und ggf. `sudo kill -9 <PID>`
- **run.sh ALSA-Sync**: `run.sh` synchronisiert `/dev/snd/*`-Geraete in den Container, da USB-Audio (ReSpeaker) nach Container-Start enumeriert werden kann. Audio-Device-Name fuer Voice: `plughw:CARD=ArrayUAC10,DEV=0` (hardcoded in Launch)
- **Dashboard-Zertifikate**: Ohne mkcert-Zertifikate (`amr.local+5.pem`) crasht `npm run dev` sofort — `vite.config.ts` liest sie synchron, kein Fallback
- **Mypy Moderate Mode**: `disallow_untyped_defs = false` — bestehender Code hat wenig Type-Hints. ROS2-Pakete sind in `mypy.ini` als `ignore_missing_imports` konfiguriert
- **ruff-Ausschluesse**: `amr/pi5/ros2_ws/src/my_bot/my_bot/` (Symlink-Verzeichnis), `dashboard/`, `build/`, `install/` sind in `ruff.toml` ausgeschlossen. Mehrere Skripte haben Per-File-Ignores
- **Host-Hailo-Runner**: `host_hailo_runner.py` MUSS auf dem Host laufen (nicht im Container) — sendet UDP an `127.0.0.1:5005`. Ohne laufenden Runner haengt `hailo_udp_receiver_node` wartend
- **Docker Micro-ROS Fallback**: Falls `ros-humble-micro-ros-agent` apt-Paket auf arm64 fehlt, baut das Dockerfile es aus Source (~30+ Min zusaetzlich)
- **Docker numpy<2 Pin**: cv_bridge (apt) ist gegen NumPy 1.x ABI kompiliert. Ohne `numpy<2` Pin crasht cv_bridge mit `_ARRAY_API`-Fehler. `openwakeword==0.6.0` ist fixiert (neuere Versionen aendern Modell-API)
- **Gemini-Quota (Free-Tier)**: `gemini-2.0-flash-lite` Free-Tier hat 1500 RPD (Requests/Tag) und 30 RPM. Bei 8s-Intervall (~450 Req/h) ist das Tageslimit nach ~3h erreicht. Symptom: `429 RESOURCE_EXHAUSTED` in Logs, Dashboard zeigt dauerhaft "Warte auf Vision-Pipeline...". Quota-Status pruefen unter https://aistudio.google.com/
- **Vision-Pipeline stille Fehler**: `gemini_semantic_node` scheitert still wenn `/camera/image_raw` fehlt (v4l2_camera_node abgestuerzt) oder Gemini-Quota erschoepft. Warn-Log fuer fehlendes Kamerabild seit 03.04.2026 eingebaut (gedrosselt 10s)

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
- `vision_pipeline.md` — Hailo/Gemini Vision-Pipeline mit Sensorfusion
- `serial_port_management.md` — udev-Regeln und Seriennummern
- `robot_parameters.md` — Physikalische Parameter (Raddurchmesser, PID, Batterie)
- `build_and_deploy.md`, `validation.md`, `quality_checks.md` — Build, Validierung, Qualitaet

Schreibstil und Literatur: `docs/projektarbeit_style.md`, `docs/literature_workflow.md`

Planung und Betrieb: `planung/` enthaelt Testanleitungen, Messprotokolle, Systemdokumentation, Benutzerhandbuch und Netzwerkkonfiguration

## Online-Dokumentation (MkDocs Material + GitHub Pages)

- Live-Site: `https://unger-robotics.github.io/amr-projekt/`
- Konfiguration: `mkdocs.yml` (Material-Theme, deutsche Sprache, Mermaid, Minify)
- Custom Theme: `docs/stylesheets/extra.css` (HUD-Farbdesign: BgBase #0B131E, AccPrim #00E5FF, StatSucc #00FF66, StatCrit #FF2A40)
- Logo/Favicon: `docs/assets/amr_hud_icon.svg`
- Deployment: `.github/workflows/deploy-docs.yml` (GitHub Actions, Trigger bei docs/** oder mkdocs.yml)
- Sitemap: automatisch generiert, in Google Search Console eingereicht
- Mermaid-Diagramme: `<br>` statt `<br/>`, keine Bindestriche in Subgraph-IDs, `<-->` nur im Systemdiagramm (getestet)
- Nav-Struktur: Startseite, Erste Schritte (3), Architektur (3), Firmware (3), ROS 2 (3), Referenz (2)

```bash
# Lokal testen
pip install mkdocs-material mkdocs-minify-plugin pymdown-extensions
mkdocs serve --dev-addr 0.0.0.0:8000

# Build pruefen
mkdocs build --strict
```

## Sync-Workflow (Dreiecks-Workflow Pi5-GitHub-Mac)

```bash
./scripts/sync/push-to-github.sh "feat: Beschreibung"   # Code → GitHub
./scripts/sync/sync_to_mac.sh all                        # Medien → Mac(s)
./scripts/sync/sync_from_mac.sh mac                      # Medien ← Mac
```

Code wird ueber GitHub synchronisiert, grosse Mediendateien direkt via rsync zwischen Pi 5 und Mac(s).
