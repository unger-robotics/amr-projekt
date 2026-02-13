# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektuebersicht

Bachelorarbeit: Autonomer Mobiler Roboter (AMR) fuer Intralogistik (KLT-Transport). Differentialantrieb-Roboter mit XIAO ESP32-S3 (Low-Level-Steuerung) und Raspberry Pi 5 (Navigation/SLAM) ueber micro-ROS/UART verbunden. Sprache: Deutsch (wissenschaftlicher Stil, keine UTF-8-Umlaute in Markdown-Dateien – ae/oe/ue/ss verwenden).

## Build & Deployment

### ESP32 Firmware (PlatformIO)

```bash
# Im Verzeichnis: amr/esp32_amr_firmware/
# PlatformIO-Env: seeed_xiao_esp32s3
pio run                       # Firmware kompilieren
pio run -t upload             # Auf ESP32 flashen (921600 Baud)
pio run -t monitor            # Seriellen Monitor starten (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor kombiniert
```

### ROS2 Workspace (Raspberry Pi)

```bash
# Im Verzeichnis: amr/pi5/ros2_ws/
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
ros2 launch my_bot full_stack.launch.py                # Gesamtsystem (micro-ROS + SLAM + Nav2 + RViz2)
ros2 launch my_bot full_stack.launch.py use_nav:=false  # Nur SLAM (ohne Navigation)
ros2 launch my_bot full_stack.launch.py use_rviz:=False # Ohne RViz2
ros2 launch my_bot full_stack.launch.py use_slam:=False # Nur Navigation mit bestehender Karte
ros2 launch my_bot full_stack.launch.py serial_port:=/dev/ttyUSB0  # Alternativer Serial-Port
```

### Validierungsskripte (Raspberry Pi)

```bash
# Standalone-Skripte (kein ROS2 noetig):
python3 amr/scripts/pre_flight_check.py    # Interaktive Hardware-Checkliste
python3 amr/scripts/umbmark_analysis.py     # UMBmark-Auswertung (numpy/matplotlib)
python3 amr/scripts/validation_report.py    # Gesamt-Report aus JSON-Ergebnissen

# ROS2-Nodes (micro-ROS Agent muss laufen):
ros2 run my_bot encoder_test      # Encoder-Kalibrierung (10-Umdrehungen-Test)
ros2 run my_bot motor_test        # Motor-Deadzone und Richtungstest
ros2 run my_bot pid_tuning        # PID-Sprungantwort-Analyse
ros2 run my_bot kinematic_test    # Geradeaus-/Dreh-/Kreisfahrt-Verifikation
ros2 run my_bot slam_validation   # ATE-Berechnung und TF-Ketten-Check
ros2 run my_bot nav_test          # Waypoint-Navigation mit Positionsfehler-Messung
ros2 run my_bot docking_test      # 10-Versuch ArUco-Docking-Test
```

**Hinweis:** Die ROS2-Nodes erfordern, dass die Skripte aus `amr/scripts/` als Symlinks oder Kopien im Paketverzeichnis `my_bot/my_bot/` liegen (siehe `09_umsetzungsanleitung.md`, Abschnitt 2.2.5).

### Deployment auf Raspberry Pi

```bash
# Vom Mac auf den Pi5 synchronisieren:
rsync -avz --delete --exclude='__pycache__/' --exclude='*.pyc' --exclude='.git/' amr/ pi@rover:~/amr
```

### Python-Hilfsskripte

```bash
# Virtuelle Umgebung im Projekt-Root: .venv/
source .venv/bin/activate
python suche/download_sources.py   # Literatur-PDFs herunterladen
```

## Architektur

### Dual-Core XIAO ESP32-S3 Firmware (`amr/esp32_amr_firmware/src/`)

Die Firmware partitioniert die Kerne fuer Echtzeit-Garantien:

- **Core 0** (`loop()`): micro-ROS Agent – empfaengt `cmd_vel` (Twist), publiziert `Odometry` (20 Hz), Watchdog-Ueberwachung
- **Core 1** (`controlTask`): PID-Regelschleife bei 50 Hz (20 ms Takt via `vTaskDelayUntil`)
- **Thread-Safety**: FreeRTOS-Mutex (`SharedData`) schuetzt geteilte Daten zwischen den Cores

Datenfluss: `cmd_vel` → inverse Kinematik → PID → Cytron MDD3A (Dual-PWM) → Encoder-Feedback (Hall, A-only) → Vorwaertskinematik → Odometrie-Publish

### Firmware-Module (Header-only Pattern)

| Datei | Funktion |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Subscriber/Publisher, Safety-Mechanismen |
| `robot_hal.hpp` | Hardware-Abstraktion: GPIO, Encoder-ISR (A-only), PWM-Steuerung, Deadzone |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup, Ausgang [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik (Parameter aus `config.h`) |

Alle Hardware-Parameter in `hardware/config.h` (Single Source of Truth), eingebunden via `-I../../hardware` Build-Flag. PID-Gains sind in `main.cpp` hardcoded (Kp=1.5, Ki=0.5, Kd=0.0).

### Safety-Mechanismen (Firmware)

- **Failsafe-Timeout**: 500 ms ohne `cmd_vel` → Motoren stopp (`FAILSAFE_TIMEOUT_MS` in config.h)
- **Inter-Core-Watchdog**: `core1_heartbeat`-Zaehler auf Core 1, von `loop()` auf Core 0 ueberwacht
- **RCL-Error-Handling**: Alle `rclc_*`-Initialisierungen mit `rcl_ret_t` geprueft → LED-Blinksignal bei Fehler

### ROS2 Navigation Stack (Raspberry Pi)

Konfiguration in `amr/pi5/ros2_ws/src/my_bot/config/`:

- **nav2_params.yaml**: Nav2-Stack – AMCL, Regulated Pure Pursuit Controller (0.4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors
- **mapper_params_online_async.yaml**: SLAM Toolbox – Ceres-Solver, 5 cm Aufloesung, Loop Closure
- **aruco_docking.py** (`scripts/`): Visual Servoing mit ArUco-Markern (OpenCV `cv2.aruco.ArucoDetector`-API >= 4.7)
- **full_stack.launch.py** (`launch/`): Kombiniertes Launch-File fuer micro-ROS Agent + SLAM + Nav2 + RViz2
- **package.xml/setup.py/setup.cfg**: ament_python-Paketstruktur mit 8 entry_points (console_scripts)

### Kommunikationsschicht

XIAO ESP32-S3 ↔ Raspberry Pi: micro-ROS ueber UART (Serial Transport, USB-CDC, Humble-Distribution).

## Roboter-Parameter

Zentral in `hardware/config.h` definiert. Wichtigste Werte:

- Raddurchmesser: 65 mm, Spurbreite: 178 mm
- Encoder: ~374 Ticks/Rev (A-only), PWM-Deadzone: 35
- LiDAR: RPLIDAR A1, Kamera: RPi Global Shutter (Sony IMX296, 6 mm CS-Mount)
- Akku: 4S LiFePO4 (12,8 V nominal)
- Zielgeschwindigkeit: 0.4 m/s, Positionstoleranz: 10 cm (xy) / 8° (Gier)

## Firmware-Constraints

- **C++11**: ESP32-Arduino-Toolchain kompiliert mit C++11. Kein `std::clamp` (C++17) – stattdessen `std::max(min, std::min(val, max))`.
- **Typen**: `int32_t`/`uint8_t`/`int16_t` statt `int`/`long` (MISRA-inspiriert). Encoder-Zaehler sind `volatile int32_t`.
- **ISR**: Alle ISR-Funktionen mit `IRAM_ATTR` markieren.
- **Speicher**: Keine dynamische Allokation zur Laufzeit (nur beim Startup).

## Validierung

- Keine automatisierten Unit-Tests – Validierung erfolgt experimentell ueber V-Modell-Phasenplan (`hardware/docs/08_validierungsplan.md`)
- 10 Validierungsskripte in `amr/scripts/` (alle `py_compile`-validiert)
- Ergebnisse werden als JSON gespeichert und mit `validation_report.py` zu einem Gesamt-Report aggregiert
- Methoden: UMBmark (Borenstein 1996), PID-Sprungantwort, rosbag2-Aufzeichnung

## Bachelorarbeit (Markdown-Dokument)

### Gliederung

Die Arbeit folgt dem V-Modell nach VDI 2206. Expose und Gliederung in `suche/amr_expose_literaturstrategie.md`. Vollstaendig: 7 Kapitel, ~42.800 Woerter.

### Forschungsfragen

- **FF1 (Architektur):** Echtzeitfaehige Regelung auf ESP32 mit micro-ROS ohne WLAN-Latenzen?
- **FF2 (Praezision):** Einfluss systematischer Odometrie-Kalibrierung (UMBmark) auf Navigationsgenauigkeit?
- **FF3 (Funktionalitaet):** Monokulares ArUco-Docking hinreichend robust fuer mechanischen Ladekontakt?

### Dateistruktur

Jedes Kapitel existiert in zwei Formen:
- **Kombinierte Datei**: `bachelorarbeit/kapitel_XX_name.md` (z.B. `kapitel_04_systemkonzept.md`)
- **Einzelabschnitte**: `bachelorarbeit/kapitel/XX_Y_name.md` (z.B. `04_2_gesamtsystemarchitektur.md`)

### Schreibkonventionen

- Umlaute als ae, oe, ue, ss (kein UTF-8-Umlaut in Kapitel-Dateien)
- Zitationen: `(vgl. Nachname et al. Jahr, S. X)`
- Gleichungen als Code-Bloecke mit erklaerenden Variablendefinitionen
- Keine Bullet-Point-Listen im Fliesstext – vollstaendige Saetze und Absaetze
- Jeder Abschnitt beginnt mit einem kontextualisierenden Einleitungssatz
- **Dual-File-Regel**: Jede Aenderung muss in BEIDEN Dateien erfolgen – der Einzelabschnitt-Datei UND der kombinierten Kapiteldatei

### Workflow: Kapitel generieren

Kapitel werden mit parallelen Agent-Teams erstellt:
1. Team erstellen (`TeamCreate`) mit N Agents (1 pro Unterabschnitt)
2. Tasks erstellen mit Expose-Vorgaben + zugewiesenen Kernaussagen-Dateien
3. Agents parallel spawnen, jeder schreibt seinen Abschnitt
4. Outputs pruefen und zu kombinierter Kapiteldatei zusammenfuehren
5. Team herunterfahren und aufraeumen

## Literaturverwaltung

- 17 PDFs in `sources/` (Macenski, Siegwart, Borenstein, etc.)
- Extrahierte Kernaussagen in `sources/kernaussagen/` (16 Einzeldateien + Querverweismatrix in `00_Uebersicht_Querverweise.md`)

## Wichtige Verzeichnisse

- `hardware/config.h` – Zentrale Hardware-Konfiguration (Single Source of Truth)
- `hardware/docs/` – 9 Hardware-Dokumente (Pinout, Antrieb, Stromversorgung, BOM, Migrationsplan, Validierungsplan, Umsetzungsanleitung)
- `amr/esp32_amr_firmware/src/` – 4 Firmware-Dateien (main.cpp + 3 Header)
- `amr/pi5/ros2_ws/src/my_bot/` – ROS2-Paket (package.xml, setup.py, config/, launch/, scripts/)
- `amr/scripts/` – 10 Validierungsskripte
- `bachelorarbeit/` – Vollstaendige Bachelorarbeit (7 kombinierte + 35 Einzelabschnitt-Dateien)
- `sources/kernaussagen/` – Kernaussagen mit Seitenzahlen fuer Zitationen
