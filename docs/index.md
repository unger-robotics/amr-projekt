---
title: AMR-Plattform – Autonomer Mobiler Roboter mit ROS 2 und ESP32-S3
description: >-
  Open-Source AMR-Plattform mit ESP32-S3 (FreeRTOS + micro-ROS) und
  Raspberry Pi 5 (ROS 2 Humble). Bachelorarbeit nach VDI 2206.
---

# AMR-Plattform – Autonomer Mobiler Roboter

Die **AMR-Plattform** (Autonomous Mobile Robot) ist ein offenes Robotik-Projekt,
das im Rahmen einer Bachelorarbeit an der
[Wilhelm Büchner Hochschule](https://www.wb-fernstudium.de/) entsteht.
Die Entwicklung folgt dem **VDI-2206-V-Modell** für mechatronische Systeme.

## Zwei-Ebenen-Architektur

Das System besteht aus zwei Rechenebenen, die über micro-ROS kommunizieren:

| Ebene | Hardware | Aufgabe | Software |
|-------|----------|---------|----------|
| **Echtzeit** | Seeed XIAO ESP32-S3 | Motorsteuerung, Sensorik, Cliff-Detection | FreeRTOS + micro-ROS (C/C++) |
| **High-Level** | Raspberry Pi 5 (8 GB) | Navigation, SLAM, Planung | ROS 2 Humble (Python/C++) |

## Kerndaten

- **Antrieb:** Differentialantrieb mit JGA25-370-Motoren (Übersetzung 1:34)
- **Sensorik:** RPLIDAR A1 (360° LiDAR), MPU-6050 (IMU), IR-Cliff-Sensoren
- **KI-Beschleuniger:** Hailo-8L (13 TOPS)
- **Kamera:** Pan/Tilt mit TowerPro MG996R Servos (11 kg·cm @ 6 V)
- **Akku:** 3S LiIon (Samsung INR18650-35E, Nennspannung 10,8 V)

## Schnellstart

```bash
# Repository klonen
git clone https://github.com/unger-robotics/amr-projekt.git
cd amr-projekt

# Dokumentation lokal bauen (erfordert Python 3.10+)
pip install mkdocs-material mkdocs-minify-plugin pymdown-extensions
mkdocs serve
```

Die Dokumentation ist dann unter `http://127.0.0.1:8000` erreichbar.

## Projektstruktur

```
amr-projekt/
├── docs/                  # Diese Dokumentation (MkDocs)
├── firmware/              # ESP32-S3 Firmware (ESP-IDF + micro-ROS)
├── ros2_ws/               # ROS 2 Workspace (Pi 5)
├── dashboard/             # React/TypeScript/Vite Web-Dashboard
├── hardware/              # KiCad-Schaltpläne, Stückliste
├── mkdocs.yml             # MkDocs-Konfiguration
└── README.md
```

## Weiterführende Seiten

- [Systemübersicht](architecture/system-overview.md) – Architekturdiagramm und Datenfluss
- [FreeRTOS-Architektur](firmware/freertos.md) – Dual-Core Task-Verteilung
- [ROS 2 Nodes](ros2/nodes.md) – Topic-/Service-Übersicht
- [Hardware-Stückliste](getting-started/bom.md) – Alle Komponenten mit Bezugsquellen

## Lizenz & Kontakt

Dieses Projekt ist Teil einer akademischen Arbeit.
Quellcode und Dokumentation stehen unter der [MIT-Lizenz](https://opensource.org/licenses/MIT).

[:fontawesome-brands-github: Repository auf GitHub](https://github.com/unger-robotics/amr-projekt){ .md-button .md-button--primary }
