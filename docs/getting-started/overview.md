---
title: Ueberblick
description: Einfuehrung in die AMR-Plattform und Schnellstart-Anleitung.
---

# Ueberblick

Die **AMR-Plattform** (Autonomous Mobile Robot) ist ein offenes Robotik-Projekt, das im Rahmen einer Projektarbeit entsteht. Die Plattform dient als Lernplattform fuer autonomes Fahren (Kfz) und die Entwicklung folgt dem VDI-2206-V-Modell fuer mechatronische Systeme.

## Kerndaten

| Eigenschaft | Wert |
|-------------|------|
| **Antrieb** | Differentialantrieb, JGA25-370-Motoren (1:34) |
| **Sensorik** | RPLIDAR A1 (360 Grad LiDAR), MPU-6050 (IMU), IR-Cliff, HC-SR04 |
| **KI-Beschleuniger** | Hailo-8L (13 TOPS) |
| **Kamera** | Pan/Tilt mit TowerPro MG996R Servos |
| **Akku** | 3S Li-Ion (Samsung INR18650-35E, 10.8 V, 3.35 Ah) |
| **Rechner** | Raspberry Pi 5 (8 GB), ROS 2 Humble im Docker |
| **MCU** | 2x Seeed XIAO ESP32-S3 (FreeRTOS + micro-ROS) |

## Schnellstart

### 1. Repository klonen

```bash
git clone https://github.com/unger-robotics/amr-projekt.git
cd amr-projekt
```

### 2. Host-Setup und Docker-Image

```bash
cd amr/docker/
sudo bash host_setup.sh        # udev, Gruppen, Kamera-Bridge
docker compose build            # ~15–20 Min auf Pi 5
./run.sh colcon build --packages-select my_bot --symlink-install
```

### 3. Firmware flashen

```bash
cd amr/mcu_firmware/drive_node/
pio run -e drive_node -t upload -t monitor

cd amr/mcu_firmware/sensor_node/
pio run -e sensor_node -t upload -t monitor
```

### 4. ROS2-Stack starten

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py
```

### 5. Verbindung pruefen

```bash
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /odom     # Erwartet: ~20 Hz
./run.sh exec ros2 topic hz /cliff    # Erwartet: ~20 Hz
```

## Naechste Schritte

- [Hardware-Stueckliste](bom.md) — Alle Komponenten mit Bezugsquellen
- [Aufbau](assembly.md) — Ersteinrichtung und Inbetriebnahme
- [Systemuebersicht](../architecture/system-overview.md) — Architekturdiagramm
