---
title: Glossar
description: Zentrale Begriffe und Terminologie der AMR-Plattform.
---

# Glossar

## Ebenen-Modell

| Begriff | Beschreibung |
|---------|-------------|
| **Ebene A – Fahrkern** | ESP32-S3 Drive-Knoten und Sensor-Knoten. Echtzeit-Regelung, Sensorerfassung, Sicherheits-Basisfunktionen |
| **Ebene B – Bedien- und Leitstandsebene** | Pi 5 mit ROS2, SLAM, Navigation, Benutzeroberflaeche |
| **Ebene C – Intelligente Interaktion** | Hailo-8L, Gemini Cloud, gTTS, ReSpeaker (optional) |

## Knoten und Komponenten

| Begriff | Beschreibung |
|---------|-------------|
| **Drive-Knoten (Fahrkern)** | ESP32-S3 fuer Motorregelung, Encoder, PID, Odometrie, LED |
| **Sensor-Knoten (Sensor- und Sicherheitsbasis)** | ESP32-S3 fuer IMU, Ultraschall, Cliff, Batterie, Servo |
| **Pi 5** | Zentrale ROS2- und Docker-Laufzeit (Raspberry Pi 5, 8 GB) |
| **micro-ROS Agent** | Serial-Bridge zwischen ROS2 und den ESP32-Knoten |
| **Benutzeroberflaeche** | React/Vite Weboberflaeche fuer Telemetrie und Fernsteuerung |

## Funktionen und Systeme

| Begriff | Beschreibung |
|---------|-------------|
| **Lokalisierung und Kartierung** | SLAM Toolbox — simultane Positionsbestimmung und Kartenerstellung |
| **Navigation** | Nav2-Stack mit RPP Controller und NavFn Planer |
| **Sicherheitslogik** | Cliff-Safety-Knoten: multiplext `/cmd_vel`, blockiert bei Cliff oder Hindernis |
| **Freigabelogik** | Prueft Sprachbefehle auf zulaessige Missionskommandos |
| **Sprachschnittstelle** | ReSpeaker + Gemini Audio-STT (Cloud, primaer) / faster-whisper (Offline-Fallback) fuer freihaendige Bedienung |
| **Dual-Path** | micro-ROS/UART (primaer) + CAN-Bus (sekundaer, Redundanz) |

## Projektbezogene Begriffe

| Begriff | Beschreibung |
|---------|-------------|
| **Projektfrage (PF)** | Forschungsleitende Fragen der Projektarbeit (PF1, PF2, PF3) |
| **VDI 2206** | Richtlinie fuer die Entwicklung mechatronischer Systeme (V-Modell) |
| **V-Modell** | Entwicklungsprozess mit Phasen (Entwurf → Implementierung → Validierung) |
| **Missionskommando** | Freigegebener Befehl aus der Sprachverarbeitung (z.B. "Fahre zur Ladestation") |
| **Intent** | Semantisch erkannter Zweck eines Sprachbefehls |

## Abkuerzungen

| Kuerzel | Bedeutung |
|---------|-----------|
| AMR | Autonomous Mobile Robot |
| ATE | Absolute Trajectory Error |
| CAN | Controller Area Network |
| DoA | Direction of Arrival |
| DDS | Data Distribution Service |
| IMU | Inertial Measurement Unit |
| Nav2 | ROS 2 Navigation Stack |
| PID | Proportional-Integral-Derivative (Regelung) |
| QoS | Quality of Service |
| RPP | Regulated Pure Pursuit (Controller) |
| SLAM | Simultaneous Localization and Mapping |
| STT | Speech-to-Text |
| TF | Transform (ROS2 Koordinatensystem) |
| TTS | Text-to-Speech |
| TWAI | Two-Wire Automotive Interface (ESP32 CAN) |
| VAD | Voice Activity Detection |
| XRCE-DDS | eXtremely Resource Constrained Environments DDS |
