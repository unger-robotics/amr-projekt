# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektübersicht

Bachelorarbeit: Autonomer Mobiler Roboter (AMR) für Intralogistik (KLT-Transport). Differentialantrieb-Roboter mit ESP32 (Low-Level-Steuerung) und Raspberry Pi 5 (Navigation/SLAM) über micro-ROS/UART verbunden.

## Build & Deployment

### ESP32 Firmware (PlatformIO)

```bash
# Im Verzeichnis: Bachelorarbeit technische Umsetzung/esp32_amr_firmware/
pio run                    # Firmware kompilieren
pio run -t upload          # Auf ESP32 flashen (921600 Baud)
pio run -t monitor         # Seriellen Monitor starten (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor kombiniert
```

### ROS2 Workspace (Raspberry Pi)

```bash
# Im Verzeichnis: Bachelorarbeit technische Umsetzung/pi/ros2_ws/
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

### Dual-Core ESP32 Firmware (`esp32_amr_firmware/src/`)

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

Konfiguration in `pi/ros2_ws/src/my_bot/config/`:

- **nav2_params.yaml**: Vollständiger Nav2-Stack – AMCL-Lokalisierung, Regulated Pure Pursuit Controller (0.4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors
- **mapper_params_online_async.yaml**: SLAM Toolbox – Ceres-Solver, 5 cm Auflösung, Loop Closure aktiv
- **aruco_docking.py**: Visual Servoing mit ArUco-Markern für Ladestation-Andockung (OpenCV)

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

## Projektstruktur (Kernverzeichnisse)

```
Bachelorarbeit technische Umsetzung/
  esp32_amr_firmware/        # PlatformIO-Projekt (ESP32 C++ Firmware)
  pi/ros2_ws/                # ROS2 Colcon-Workspace (Raspberry Pi)
sources/                     # Wissenschaftliche Literatur (17 PDFs)
suche/                       # Literaturrecherche-Skripte und Strategiedokumente
```
