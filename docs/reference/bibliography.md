---
title: Quellenverzeichnis
description: Standards, Frameworks und Werkzeuge der AMR-Plattform.
---

# Quellenverzeichnis

## Standards und Richtlinien

| Bezeichnung | Beschreibung |
|-------------|-------------|
| VDI 2206 | Entwicklungsmethodik fuer mechatronische Systeme (V-Modell) |
| ISO 11898 | Controller Area Network (CAN) Spezifikation |
| DDS-XRCE | OMG DDS for eXtremely Resource Constrained Environments |

## Robotik-Frameworks

| Projekt | Version | Verwendung |
|---------|---------|-----------|
| [ROS 2 Humble](https://docs.ros.org/en/humble/) | Humble Hawksbill | Middleware, Message-Passing, Launch |
| [Nav2](https://docs.nav2.org/) | Humble | Navigation (RPP Controller, NavFn Planer) |
| [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox) | — | Lokalisierung und Kartierung |
| [micro-ROS](https://micro.ros.org/) | Humble | ROS2-Anbindung der ESP32-S3-Knoten |

## Firmware und Embedded

| Projekt | Version | Verwendung |
|---------|---------|-----------|
| [ESP-IDF](https://docs.espressif.com/projects/esp-idf/) | v5.x (via PlatformIO) | ESP32-S3 HAL und FreeRTOS |
| [FreeRTOS](https://www.freertos.org/) | in ESP-IDF | Dual-Core Task-Verwaltung |
| [PlatformIO](https://platformio.org/) | — | Build-System fuer Firmware |

## KI und Vision

| Projekt | Version | Verwendung |
|---------|---------|-----------|
| [Hailo AI SDK](https://hailo.ai/) | — | YOLOv8 Objekterkennung (Hailo-8L, 13 TOPS) |
| [Google Gemini](https://ai.google.dev/) | 3.1 flash-lite | Semantische Szenenbeschreibung, STT |
| [gTTS](https://gtts.readthedocs.io/) | — | Text-to-Speech (Deutsch) |
| [YOLOv8](https://docs.ultralytics.com/) | s-Variante | Objekterkennung |

## Benutzeroberflaeche

| Projekt | Version | Verwendung |
|---------|---------|-----------|
| [React](https://react.dev/) | 19.x | UI-Framework |
| [Vite](https://vite.dev/) | 7.x | Build-Tool und Dev-Server |
| [TypeScript](https://www.typescriptlang.org/) | 5.9 | Typsicherheit |
| [Tailwind CSS](https://tailwindcss.com/) | 4.x | Styling |
| [Zustand](https://zustand.docs.pmnd.rs/) | — | State Management |

## Hardware-Referenzen

| Komponente | Datenblatt/Ressource |
|------------|---------------------|
| ESP32-S3 | [Espressif Technical Reference Manual](https://www.espressif.com/en/products/socs/esp32-s3) |
| Raspberry Pi 5 | [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/) |
| MPU-6050 | InvenSense Product Specification, Rev. 3.4 |
| INA260 | Texas Instruments SBOS656A |
| PCA9685 | NXP Semiconductors Product Data Sheet |
| Cytron MDD3A | Cytron Technologies User Manual |
| RPLIDAR A1 | Slamtec RPLIDAR A1 Development Kit User Manual |
| SN65HVD230 | Texas Instruments CAN-Bus Transceiver |
