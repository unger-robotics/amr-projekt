---
title: Hardware-Stueckliste
description: Alle Hardware-Komponenten der AMR-Plattform mit Spezifikationen.
---

# Hardware-Stueckliste

## Recheneinheiten

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| Raspberry Pi 5 | 8 GB RAM, Debian Trixie | ROS2, SLAM, Navigation, Docker |
| Seeed XIAO ESP32-S3 (x2) | Dual-Core 240 MHz, WiFi/BLE | Drive-Knoten + Sensor-Knoten |
| Hailo-8L | 13 TOPS, M.2 PCIe | KI-Beschleuniger (YOLOv8) |

## Antrieb

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| JGA25-370 Motoren (x2) | Uebersetzung 1:34, Hall-Encoder 11 CPR | Differentialantrieb |
| Cytron MDD3A | Dual-Channel, 3 A | Motortreiber |
| Raddurchmesser | 65.67 mm (kalibriert) | — |
| Spurbreite | 178.0 mm (Mitte-Mitte) | — |
| Ticks/Umdrehung | 748.6 (L) / 747.2 (R) | kalibriert |

## Sensorik

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| RPLIDAR A1 | 360 Grad, 12 m, ~7 Hz, USB | LiDAR (Lokalisierung und Kartierung) |
| MPU-6050 | 6-Achsen, I2C (0x68) | IMU (Beschleunigung + Gyroskop) |
| INA260 | I2C (0x40), 1.25 mA/mV LSB | Batterieueberwachung |
| HC-SR04 | 0.02–4.00 m, ISR-basiert | Ultraschall (Hinderniserkennung) |
| MH-B IR | GPIO-Poll, 20 Hz | Cliff-Sensor (Kantenerkennung) |

## Kamera und Vision

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| RPi Global Shutter IMX296 | CSI (22→15 Pin Adapter) | Kamera |
| PCA9685 | I2C (0x41), 16-Kanal PWM | Servo-Controller |
| TowerPro MG996R (x2) | 11 kg·cm @ 6 V | Pan/Tilt Servos |

## Audio und Sprache

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| MAX98357A | I2S, 3 W | Verstaerker + Lautsprecher |
| ReSpeaker Mic Array v2.0 | XMOS XVF-3000, USB | Mikrofonarray (DoA/VAD) |

## Stromversorgung

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| Samsung INR18650-35E (x3) | 3S1P, 10.8–12.6 V, 3.35 Ah | Akkupack |
| Hauptsicherung | 10 A | Ueberstromschutz |
| Motor-Abschaltung | < 9.5 V (Hysterese +0.3 V) | Unterspannungsschutz |

## Kommunikation

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| USB-C (x2) | micro-ROS UART, 921600 Baud | Serielle MCU-Verbindung |
| SN65HVD230 (x2) | CAN 2.0B, 1 Mbit/s | CAN-Transceiver |
| MCP2515 | SPI, SocketCAN | CAN-Interface (Pi 5) |

## Weitere Hardware

| Komponente | Spezifikation | Funktion |
|------------|---------------|----------|
| SMD 5050 LED-Streifen | via IRLZ24N MOSFET, LEDC | Status-LED |
| ArUco-Marker (ID 0) | 10 cm, gedruckt | Docking-Referenz |
