# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektübersicht

Bachelorarbeit: Autonomer Mobiler Roboter (AMR) für Intralogistik (KLT-Transport). Differentialantrieb-Roboter mit ESP32 (Low-Level-Steuerung) und Raspberry Pi 5 (Navigation/SLAM) über micro-ROS/UART verbunden. Sprache: Deutsch (wissenschaftlicher Stil, keine Umlaute in Markdown-Dateien).

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

### Dual-Core ESP32 Firmware (`technische_umsetzung/esp32_amr_firmware/src/`)

Die Firmware partitioniert die ESP32-Kerne für Echtzeit-Garantien:

- **Core 0**: micro-ROS Agent – empfängt `cmd_vel` (Twist), publiziert `Odometry` (20 Hz)
- **Core 1**: Regelschleife – PID-Motorregelung bei 50 Hz (20 ms Takt)
- **Thread-Safety**: FreeRTOS-Mutex schützt geteilte Daten zwischen den Cores

Datenfluss: `cmd_vel` → inverse Kinematik → PID → PWM-Motoren → Encoder-Feedback → Vorwärtskinematik → Odometrie-Publish

### Firmware-Module (Header-only Pattern)

| Datei | Funktion |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Subscriber/Publisher |
| `robot_hal.hpp` | Hardware-Abstraktion: GPIO, Encoder-ISR, PWM-Steuerung |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup, Ausgang [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwärts-/Inverskinematik (Radradius 32mm, Spurbreite 145mm) |

### ROS2 Navigation Stack (Raspberry Pi)

Konfiguration in `technische_umsetzung/pi5/ros2_ws/src/my_bot/config/`:

- **nav2_params.yaml**: Vollständiger Nav2-Stack – AMCL-Lokalisierung, Regulated Pure Pursuit Controller (0.4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors
- **mapper_params_online_async.yaml**: SLAM Toolbox – Ceres-Solver, 5 cm Auflösung, Loop Closure aktiv
- **aruco_docking.py** (`scripts/`): Visual Servoing mit ArUco-Markern für Ladestation-Andockung (OpenCV)

### Kommunikationsschicht

ESP32 ↔ Raspberry Pi: micro-ROS über UART (Serial Transport, Humble-Distribution). Gewählt wegen deterministischem Timing gegenüber WiFi/Ethernet.

## Roboter-Parameter

- Radradius: 32 mm
- Spurbreite (Wheelbase): 145 mm
- Zielgeschwindigkeit: 0.4 m/s
- Positionstoleranz: 10 cm (xy), 8° (Gier)
- Kartenauflösung: 5 cm

## Validierung

- Odometrie-Kalibrierung: UMBmark-Test
- Testparcours: 10 m × 10 m mit statischen/dynamischen Hindernissen
- Datenaufzeichnung: rosbag2 für Sensor-Replay und Analyse
- Keine automatisierten Tests vorhanden – Validierung erfolgt experimentell

## Bachelorarbeit (Markdown-Dokument)

### Gliederung nach VDI 2206

Das Exposé und die vollständige Gliederung befinden sich in `suche/amr_expose_literaturstrategie.md`. Die Arbeit folgt dem V-Modell nach VDI 2206 für mechatronische Systeme.

### Forschungsfragen

Die drei Forschungsfragen strukturieren die gesamte Arbeit und muessen in Kapitel 7 beantwortet werden:

- **FF1 (Architektur):** Wie laesst sich auf einem ESP32 eine echtzeitfaehige Regelung unter Nutzung von micro-ROS realisieren, ohne dass WLAN-Latenzen die Motorsteuerung destabilisieren?
- **FF2 (Praezision):** Welchen Einfluss hat eine systematische Odometrie-Kalibrierung (UMBmark) auf die absolute Navigationsgenauigkeit eines Low-Cost-Differentialantriebs?
- **FF3 (Funktionalitaet):** Ist ein monokulares Kamerasystem mit ArUco-Markern hinreichend robust, um einen mechanischen Ladekontakt autonom zu treffen?

### Kapitelstruktur

Fertige Kapitel liegen als kombinierte Dateien und als Einzelabschnitte vor:

| Datei | Inhalt |
|---|---|
| `bachelorarbeit/kapitel_01_einleitung.md` | Kap. 1: Einleitung (kombiniert, ~2.900 Woerter) |
| `bachelorarbeit/kapitel_02_grundlagen.md` | Kap. 2: Grundlagen und Stand der Technik (kombiniert, ~4.400 Woerter) |
| `bachelorarbeit/kapitel_03_anforderungsanalyse.md` | Kap. 3: Anforderungsanalyse (kombiniert) |
| `bachelorarbeit/kapitel/01_1_*.md` bis `01_4_*.md` | Einzelabschnitte Kap. 1 |
| `bachelorarbeit/kapitel/02_1_*.md` bis `02_6_*.md` | Einzelabschnitte Kap. 2 |
| `bachelorarbeit/kapitel/03_1_*.md` bis `03_5_*.md` | Einzelabschnitte Kap. 3 |
| `bachelorarbeit/kapitel_04_systemkonzept.md` | Kap. 4: Systemkonzept und Entwurf (kombiniert, ~8.500 Woerter) |
| `bachelorarbeit/kapitel/04_1_*.md` bis `04_5_*.md` | Einzelabschnitte Kap. 4 |

### Geplante Kapitel (noch nicht geschrieben)

Gemaess Expose (`suche/amr_expose_literaturstrategie.md`, VDI 2206 V-Modell):

- **Kap. 5**: Implementierung (Hardwareaufbau, ESP32-Firmware, ROS2-Integration, Kalibrierung/SLAM, Navigation/Docking)
- **Kap. 6**: Validierung und Testergebnisse (Testkonzept, Subsystem-Verifikation, Navigations-/Docking-Validierung, Soll-Ist-Vergleich)
- **Kap. 7**: Fazit und Ausblick (Beantwortung der Forschungsfragen FF1-FF3)

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
technische_umsetzung/
  esp32_amr_firmware/        # PlatformIO-Projekt (ESP32 C++ Firmware)
    src/                     # main.cpp, robot_hal.hpp, pid_controller.hpp, diff_drive_kinematics.hpp
  pi5/ros2_ws/               # ROS2 Colcon-Workspace (Raspberry Pi 5)
    src/my_bot/config/       # nav2_params.yaml, mapper_params_online_async.yaml
    src/my_bot/scripts/      # aruco_docking.py
bachelorarbeit/              # Bachelorarbeit als Markdown
  kapitel_01_einleitung.md   # Kombiniertes Kapitel 1
  kapitel_02_grundlagen.md   # Kombiniertes Kapitel 2
  kapitel/                   # Einzelne Unterabschnitte (01_1_* bis 02_6_*)
sources/                     # Wissenschaftliche Literatur (17 PDFs)
  kernaussagen/              # Extrahierte Kernaussagen (15 Dateien + Übersicht)
suche/                       # Literaturrecherche-Skripte und Strategiedokumente
  amr_expose_literaturstrategie.md  # Master-Exposé mit Gliederung
  download_sources.py        # PDF-Download-Skript
```
