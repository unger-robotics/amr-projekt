# Architektur

## Zielbild

Der AMR besteht aus einem Raspberry Pi 5 als zentralem ROS2-Rechner und zwei ESP32-S3-Knoten fuer echtzeitnahe I/O- und Regelaufgaben.

## Hauptkomponenten

- Pi 5: ROS2, SLAM, Navigation, Dashboard-Bridge, optionale Vision
- Drive-Node: Motoransteuerung, Encoder, PID, Odometrie, LED
- Sensor-Node: Ultraschall, Cliff, IMU, Batterie, Servo
- LiDAR, Kamera, optionale Hailo-/Gemini-Pipeline

## Kommunikationspfade (Dual-Path)

Die MCU-Knoten kommunizieren ueber zwei parallele Kanaele mit dem Pi 5:

- **micro-ROS/UART** (primaer): ROS2-Topics via Serial Transport, Subscriber/Publisher fuer Steuerung und Telemetrie
- **CAN-Bus** (sekundaer): 1 Mbit/s, MCP2515/SocketCAN auf Pi 5, TWAI auf ESP32-S3, Fire-and-forget Diagnostik

CAN-Sends laufen in den Core-1-Tasks (`controlTask`/`sensorTask`), damit sie unabhaengig vom micro-ROS Agent funktionieren. Hardware-Dokumentation: `hardware/can-bus/CAN-Bus.md`.

## Architekturregel

Zeitkritische Low-Level-Funktionen bleiben auf den MCU-Knoten. Koordination, Mapping und Navigation bleiben auf dem Pi 5.

## Offene Uebernahme aus der Originaldatei

- Datenflussdiagramm Pi 5 <-> micro-ROS Agent <-> Drive-/Sensor-Knoten
- Modulgrenzen pro Knoten
- optionale Teilsysteme: Dashboard, Kamera, Vision, Audio, ReSpeaker (DoA/VAD)
