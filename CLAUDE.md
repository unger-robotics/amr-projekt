# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektübersicht

Bachelorarbeit: Autonomer Mobiler Roboter (AMR) für Intralogistik (KLT-Transport). Differentialantrieb-Roboter mit XIAO ESP32-S3 (Low-Level-Steuerung) und Raspberry Pi 5 (Navigation/SLAM) über micro-ROS/UART verbunden. Sprache: Deutsch (wissenschaftlicher Stil, keine Umlaute in Markdown-Dateien).

## Build & Deployment

### ESP32 Firmware (PlatformIO)

```bash
# Im Verzeichnis: technische_umsetzung/esp32_amr_firmware/
pio run                    # Firmware kompilieren
pio run -t upload          # Auf ESP32 flashen (921600 Baud)
pio run -t monitor         # Seriellen Monitor starten (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor kombiniert
```

### ROS2 Workspace (Raspberry Pi)

```bash
# Im Verzeichnis: technische_umsetzung/pi5/ros2_ws/
colcon build
source install/setup.bash
ros2 launch slam_toolbox async_slam_toolbox_launch.py
ros2 launch nav2_bringup navigation_launch.py
```

### Python-Hilfsskripte

```bash
# Virtuelle Umgebung im Projekt-Root: .venv/
source .venv/bin/activate
python suche/download_sources.py   # Literatur-PDFs herunterladen
```

## Architektur

### Dual-Core XIAO ESP32-S3 Firmware (`technische_umsetzung/esp32_amr_firmware/src/`)

Die Firmware läuft auf einem Seeed Studio XIAO ESP32-S3 (Xtensa LX7 Dual-Core) und partitioniert die Kerne für Echtzeit-Garantien:

- **Core 0**: micro-ROS Agent – empfängt `cmd_vel` (Twist), publiziert `Odometry` (20 Hz)
- **Core 1**: Regelschleife – PID-Motorregelung bei 50 Hz (20 ms Takt)
- **Thread-Safety**: FreeRTOS-Mutex schützt geteilte Daten zwischen den Cores

Datenfluss: `cmd_vel` → inverse Kinematik → PID → Cytron MDD3A (Dual-PWM) → Encoder-Feedback (Hall, A-only) → Vorwärtskinematik → Odometrie-Publish

### Firmware-Module (Header-only Pattern)

| Datei | Funktion |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Subscriber/Publisher |
| `robot_hal.hpp` | Hardware-Abstraktion: GPIO, Encoder-ISR (A-only), PWM-Steuerung, Deadzone |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup, Ausgang [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwärts-/Inverskinematik (Parameter aus `config.h`) |

Alle Hardware-Parameter werden zentral über `hardware/config.h` definiert (Single Source of Truth), eingebunden via `-I../../hardware` Build-Flag.

### ROS2 Navigation Stack (Raspberry Pi)

Konfiguration in `technische_umsetzung/pi5/ros2_ws/src/my_bot/config/`:

- **nav2_params.yaml**: Vollständiger Nav2-Stack – AMCL-Lokalisierung, Regulated Pure Pursuit Controller (0.4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors
- **mapper_params_online_async.yaml**: SLAM Toolbox – Ceres-Solver, 5 cm Auflösung, Loop Closure aktiv
- **aruco_docking.py** (`scripts/`): Visual Servoing mit ArUco-Markern für Ladestation-Andockung (OpenCV)

### Kommunikationsschicht

XIAO ESP32-S3 ↔ Raspberry Pi: micro-ROS über UART (Serial Transport, USB-CDC, Humble-Distribution). Gewählt wegen deterministischem Timing gegenüber WiFi/Ethernet.

## Roboter-Parameter

- MCU: Seeed Studio XIAO ESP32-S3 (Xtensa LX7 Dual-Core)
- Motortreiber: Cytron MDD3A (Dual-PWM-Modus, 3,3 V Logik, keine Pegelanpassung)
- Encoder: JGA25-370 Hall-Encoder, A-only (~374 Ticks/Rev), Richtung aus PWM abgeleitet
- Raddurchmesser: 65 mm (Radradius 32,5 mm)
- Spurbreite (Wheelbase): 178 mm
- Konversionsfaktor: 0,546 mm/Tick
- PWM-Deadzone: 35
- LiDAR: RPLIDAR A1 (SLAMTEC, 12 m Reichweite)
- Kamera: Raspberry Pi Global Shutter Camera (Sony IMX296) mit 6 mm CS-Mount über CSI
- Akku: 4S LiFePO4 (12,8 V nominal)
- Zielgeschwindigkeit: 0.4 m/s
- Positionstoleranz: 10 cm (xy), 8° (Gier)
- Kartenauflösung: 5 cm
- Materialkosten: 482,48 EUR (beschafft) + ~31 EUR (vorhanden)

## Validierung

- Odometrie-Kalibrierung: UMBmark-Test
- Testparcours: 10 m × 10 m mit statischen/dynamischen Hindernissen
- Datenaufzeichnung: rosbag2 für Sensor-Replay und Analyse
- Keine automatisierten Tests vorhanden – Validierung erfolgt experimentell

## Bachelorarbeit (Markdown-Dokument)

### Gliederung nach VDI 2206

Das Exposé und die vollständige Gliederung befinden sich in `suche/amr_expose_literaturstrategie.md`. Die Arbeit folgt dem V-Modell nach VDI 2206 für mechatronische Systeme.

### Forschungsfragen

Die drei Forschungsfragen strukturieren die gesamte Arbeit und werden in Kapitel 7 beantwortet:

- **FF1 (Architektur):** Wie laesst sich auf einem ESP32 eine echtzeitfaehige Regelung unter Nutzung von micro-ROS realisieren, ohne dass WLAN-Latenzen die Motorsteuerung destabilisieren?
- **FF2 (Praezision):** Welchen Einfluss hat eine systematische Odometrie-Kalibrierung (UMBmark) auf die absolute Navigationsgenauigkeit eines Low-Cost-Differentialantriebs?
- **FF3 (Funktionalitaet):** Ist ein monokulares Kamerasystem mit ArUco-Markern hinreichend robust, um einen mechanischen Ladekontakt autonom zu treffen?

### Kapitelstruktur

Die Bachelorarbeit ist vollstaendig (7 Kapitel, ~42.800 Woerter). Jedes Kapitel liegt als kombinierte Datei und als Einzelabschnitte vor:

| Datei | Inhalt |
|---|---|
| `bachelorarbeit/kapitel_01_einleitung.md` | Kap. 1: Einleitung (~2.900 Woerter) |
| `bachelorarbeit/kapitel_02_grundlagen.md` | Kap. 2: Grundlagen und Stand der Technik (~4.400 Woerter) |
| `bachelorarbeit/kapitel_03_anforderungsanalyse.md` | Kap. 3: Anforderungsanalyse (~4.500 Woerter) |
| `bachelorarbeit/kapitel/01_1_*.md` bis `01_4_*.md` | Einzelabschnitte Kap. 1 |
| `bachelorarbeit/kapitel/02_1_*.md` bis `02_6_*.md` | Einzelabschnitte Kap. 2 |
| `bachelorarbeit/kapitel/03_1_*.md` bis `03_5_*.md` | Einzelabschnitte Kap. 3 |
| `bachelorarbeit/kapitel_04_systemkonzept.md` | Kap. 4: Systemkonzept und Entwurf (~8.300 Woerter) |
| `bachelorarbeit/kapitel/04_1_*.md` bis `04_5_*.md` | Einzelabschnitte Kap. 4 |
| `bachelorarbeit/kapitel_05_implementierung.md` | Kap. 5: Implementierung (~10.000 Woerter) |
| `bachelorarbeit/kapitel/05_1_*.md` bis `05_6_*.md` | Einzelabschnitte Kap. 5 |
| `bachelorarbeit/kapitel_06_validierung.md` | Kap. 6: Validierung und Testergebnisse (~9.600 Woerter) |
| `bachelorarbeit/kapitel/06_1_*.md` bis `06_6_*.md` | Einzelabschnitte Kap. 6 |
| `bachelorarbeit/kapitel_07_fazit.md` | Kap. 7: Fazit und Ausblick (~3.000 Woerter) |
| `bachelorarbeit/kapitel/07_1_*.md` bis `07_3_*.md` | Einzelabschnitte Kap. 7 |

### Schreibkonventionen

- Umlaute werden als ae, oe, ue, ss geschrieben (kein UTF-8-Umlaut in Kapitel-Dateien)
- Zitationen im Format: `(vgl. Nachname et al. Jahr, S. X)`
- Gleichungen als Code-Blöcke mit erklärenden Variablendefinitionen
- Keine Bullet-Point-Listen im Fließtext – vollständige Sätze und Absätze
- Jeder Abschnitt beginnt mit einem kontextualisierenden Einleitungssatz

### Workflow: Kapitel generieren

Kapitel werden mit parallelen Agent-Teams erstellt:
1. Team erstellen (`TeamCreate`) mit N Agents (1 pro Unterabschnitt)
2. Tasks erstellen mit Exposé-Vorgaben + zugewiesenen Kernaussagen-Dateien
3. Agents parallel spawnen, jeder schreibt seinen Abschnitt
4. Outputs prüfen und zu kombinierter Kapiteldatei zusammenführen
5. Team herunterfahren und aufräumen

## Literaturverwaltung

### Quellen (17 PDFs)

Wissenschaftliche Literatur liegt in `sources/` als PDF:

| Nr. | Kurzname | Thema |
|---|---|---|
| 01 | Macenski 2022 | ROS 2 Architektur |
| 02 | Macenski 2023 | Nav2 Survey |
| 04 | Siegwart 2004 | Mobile Roboter (Lehrbuch) |
| 05 | Macenski SLAM Toolbox | SLAM Toolbox |
| 06 | Hess 2016 | Google Cartographer |
| 07 | Moore 2014 | robot_localization / EKF |
| 09 | Borenstein 1996 | Odometrie / UMBmark |
| 10 | Abaza 2025 | ESP32 AMR Stack |
| 11 | Albarran 2023 | ESP32 Differentialantrieb |
| 12 | Yordanov 2025 | ESP32 Dual-Core Partitionierung |
| 13 | Ince 2025 | SLAM Toolbox vs. Cartographer |
| 14 | Staschulat 2020 | rclc Executor |
| 15 | Oh/Kim 2025 | ArUco Docking |
| 16 | Zhang 2024 | 2DLIW-SLAM |
| 18 | De Giorgi 2024 | Odometrie-Kalibrierung |
| 19 | Nguyen 2022 | micro-ROS Thesis |
| 20 | Wang 2024 | PoDS Scheduling |

### Kernaussagen

Für jede Quelle existiert eine extrahierte Kernaussagen-Datei in `sources/kernaussagen/`:
- 15 Einzeldateien (`01_*` bis `15_*`) mit strukturierten Kernaussagen, Zitaten und Seitenzahlen
- `00_Uebersicht_Querverweise.md`: Querverweismatrix zwischen allen Kernaussagen, thematische Cluster, Zitationshäufigkeiten und Kapitelzuordnung

## Projektstruktur

```
hardware/
  config.h                   # Zentrale Hardware-Konfiguration (Single Source of Truth)
  docs/                      # Hardware-Dokumentation, Migrationsplan, Aenderungsliste
technische_umsetzung/
  esp32_amr_firmware/        # PlatformIO-Projekt (XIAO ESP32-S3 Firmware)
    src/                     # main.cpp, robot_hal.hpp, pid_controller.hpp, diff_drive_kinematics.hpp
  pi5/ros2_ws/               # ROS2 Colcon-Workspace (Raspberry Pi 5)
    src/my_bot/config/       # nav2_params.yaml, mapper_params_online_async.yaml
    src/my_bot/scripts/      # aruco_docking.py
bachelorarbeit/              # Bachelorarbeit als Markdown (vollstaendig, 7 Kapitel)
  kapitel_01_einleitung.md   # Kombinierte Kapiteldateien (01-07)
  ...
  kapitel_07_fazit.md
  kapitel/                   # Einzelne Unterabschnitte (01_1_* bis 07_3_*, 35 Dateien)
sources/                     # Wissenschaftliche Literatur (17 PDFs)
  kernaussagen/              # Extrahierte Kernaussagen (15 Dateien + Uebersicht)
suche/                       # Literaturrecherche-Skripte und Strategiedokumente
  amr_expose_literaturstrategie.md  # Master-Expose mit Gliederung
  download_sources.py        # PDF-Download-Skript
```
