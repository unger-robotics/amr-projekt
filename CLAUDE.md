# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Projektziel

Bachelorarbeit: Autonomer Mobiler Roboter (AMR) fuer Intralogistik mit KLT-Transport.

Kurzarchitektur:
- Raspberry Pi 5 als ROS2-, SLAM-, Navigation- und Integrationsrechner
- XIAO ESP32-S3 Drive-Node fuer Antrieb, PID, Odometrie und LED
- XIAO ESP32-S3 Sensor-Node fuer Ultraschall, Cliff, IMU, Batterie und Servo
- Verbindung zwischen Pi 5 und MCU-Nodes ueber micro-ROS/UART und CAN-Bus (Dual-Path)

## Arbeitsregeln

- Sprache: Deutsch im wissenschaftlich-technischen Stil
- In Markdown-Dateien keine UTF-8-Umlaute, sondern ae, oe, ue, ss
- Terminologie konsistent beibehalten
- Keine Annahmen ueber ungelesene Dateien, Messwerte oder Hardware-Zustaende treffen
- Kleine, pruefbare Aenderungen bevorzugen
- Folgen fuer Architektur, Schnittstellen und Sicherheit explizit beachten

## Zentrale Begriffe

- Drive-Node: ESP32-S3 fuer Motorregelung, Encoder, Odometrie, LED
- Sensor-Node: ESP32-S3 fuer Sensorik, Batterie, IMU, Servo und Naeherungssensoren
- Pi 5: zentrale ROS2- und Docker-Laufzeit
- micro-ROS Agent: Serial-Bridge zwischen ROS2 und den ESP32-Nodes
- Dashboard: Weboberflaeche fuer Telemetrie und Fernsteuerung

## Feste Architekturregeln

- Die MCU-Firmware besteht aus zwei getrennten PlatformIO-Projekten
- Drive-Node und Sensor-Node werden getrennt gebaut, geflasht und betrieben
- ROS2 Humble laeuft auf dem Pi 5 im Docker-Container
- Die serielle Kommunikation erfolgt ueber getrennte Pfade pro Node
- Dashboard, Kamera, Vision, Audio und ReSpeaker sind optionale Teilsysteme
- Lange Tabellen, Parameterlisten und Betriebsprozeduren nicht in diese Datei duplizieren

## Relevante Projektpfade

- `amr/mcu_firmware/drive_node/`
- `amr/mcu_firmware/sensor_node/`
- `amr/docker/`
- `amr/scripts/`
- `dashboard/`
- `my_bot/`
- `bachelorarbeit/`
- `sources/`

## Typische Arbeitsreihenfolge

1. Aufgabenbereich identifizieren
2. Nur fachlich passende Dateien lesen
3. Betroffene Schnittstellen und Abhaengigkeiten bestimmen
4. Aenderung mit minimalem Umfang umsetzen
5. Build-, Start- oder Pruefpfad angeben
6. Auswirkungen auf Architektur, Topics, Parameter und Dokumentation benennen

## Harte Randbedingungen

- Serielle Geraetepfade und Parallelzugriffe vorsichtig behandeln
- micro-ROS-Konfigurationen sind node-spezifisch
- Schnittstellen zwischen ESP32, ROS2 und Dashboard nur konsistent aendern
- Hardware-nahe Parameter nicht ohne Begruendung umbenennen oder verschieben
- Bei Launch-, Topic- oder TF-Aenderungen immer Folgeeffekte auf Navigation, Dashboard und Validierung beachten

## Detaildokumente

- `docs/architecture.md`
- `docs/build_and_deploy.md`
- `docs/ros2_system.md`
- `docs/dashboard.md`
- `docs/vision_pipeline.md`
- `docs/serial_port_management.md`
- `docs/robot_parameters.md`
- `docs/validation.md`
- `docs/quality_checks.md`
- `docs/bachelorarbeit_style.md`
- `docs/literature_workflow.md`
