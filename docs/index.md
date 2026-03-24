---
description: >-
  Open-Source AMR-Plattform mit ESP32-S3 (FreeRTOS + micro-ROS) und
  Raspberry Pi 5 (ROS 2 Humble). Projektarbeit nach VDI 2206.
  Lernplattform fuer autonomes Fahren (Kfz).
---

# AMR-Plattform – Autonomer Mobiler Roboter

Die **AMR-Plattform** (Autonomous Mobile Robot) ist ein offenes Robotik-Projekt,
das im Rahmen einer Projektarbeit entsteht.
Die Plattform dient als **Lernplattform fuer autonomes Fahren (Kfz)** und
die Entwicklung folgt dem **VDI-2206-V-Modell** fuer mechatronische Systeme.

## Zwei-Ebenen-Architektur

Das System besteht aus zwei Rechenebenen, die ueber micro-ROS kommunizieren:

| Ebene | Hardware | Aufgabe | Software |
|-------|----------|---------|----------|
| **Echtzeit** | Seeed XIAO ESP32-S3 | Motorsteuerung, Sensorik, Cliff-Detection | FreeRTOS + micro-ROS (C/C++) |
| **High-Level** | Raspberry Pi 5 (8 GB) | Navigation, SLAM, Planung | ROS 2 Humble (Python/C++) |

## Kerndaten

- **Antrieb:** Differentialantrieb mit JGA25-370-Motoren (Uebersetzung 1:34)
- **Sensorik:** RPLIDAR A1 (360 Grad LiDAR), MPU-6050 (IMU), IR-Cliff-Sensoren
- **KI-Beschleuniger:** Hailo-8L (13 TOPS)
- **Kamera:** Pan/Tilt mit TowerPro MG996R Servos (11 kg cm @ 6 V)
- **Akku:** 3S Li-Ion (Samsung INR18650-35E, Nennspannung 10,8 V)

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
├── amr/mcu_firmware/      # ESP32-S3 Firmware (PlatformIO + micro-ROS)
├── amr/pi5/ros2_ws/       # ROS 2 Workspace (Pi 5)
├── amr/docker/            # Dockerfile, docker-compose, run.sh
├── amr/scripts/           # ROS2-Knoten und Validierungsskripte
├── dashboard/             # React/TypeScript/Vite Benutzeroberflaeche
├── docs/                  # Diese Dokumentation (MkDocs)
├── projektarbeit/         # Projektarbeit (Markdown + LaTeX)
├── planung/               # Testanleitungen, Messprotokolle
├── mkdocs.yml             # MkDocs-Konfiguration
└── README.md
```

## Weiterfuehrende Seiten

- [Systemuebersicht](architecture/system-overview.md) – Drei-Ebenen-Architektur und Systemdiagramm
- [FreeRTOS-Architektur](firmware/freertos.md) – Dual-Core Task-Verteilung
- [ROS 2 Knoten](ros2/nodes.md) – Topics, TF-Baum und Launch-Parameter
- [Hardware-Stueckliste](getting-started/bom.md) – Alle Komponenten mit Spezifikationen
- [Glossar](reference/glossary.md) – Zentrale Begriffe und Abkuerzungen

## Kontakt

Dieses Projekt ist Teil einer Projektarbeit.

[:fontawesome-brands-github: Repository auf GitHub](https://github.com/unger-robotics/amr-projekt){ .md-button .md-button--primary }
