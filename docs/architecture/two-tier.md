---
title: Zwei-Ebenen-Architektur
description: Dual-Core FreeRTOS Pattern und Sicherheitsarchitektur der AMR-Plattform.
---

# Zwei-Ebenen-Architektur

Zeitkritische Low-Level-Funktionen bleiben auf den MCU-Knoten (Ebene A). Koordination, Kartierung und Navigation bleiben auf dem Pi 5 (Ebene B).

## Dual-Core-Pattern (ESP32-S3)

Beide MCU-Knoten nutzen FreeRTOS mit fester Core-Zuordnung:

### Drive-Knoten

- **Core 0:** micro-ROS Executor — Subscriber (`/cmd_vel`, `/hardware`, `/battery_shutdown`), Publisher (`/odom` 20 Hz), LED-Steuerung
- **Core 1:** `controlTask` 50 Hz — PID-Regelschleife, Encoder-Auswertung, CAN-Send und -Empfang

### Sensor-Knoten

- **Core 0:** micro-ROS Executor — Subscriber (`/servo_cmd`, `/hardware`), Publisher (`/range` 10 Hz, `/cliff` 20 Hz, `/imu` 50 Hz, `/battery` 2 Hz), Servo-I2C 5 Hz
- **Core 1:** `sensorTask` — Cliff 20 Hz, Ultraschall 10 Hz, IMU 50 Hz, Batterie 2 Hz, CAN-Sends

### Synchronisation

- **`mutex`** (SemaphoreHandle_t): Schuetzt `SharedData`-Struct zwischen Core 0 und Core 1
- **`i2c_mutex`** (nur Sensor-Knoten): Schuetzt I2C-Bus, 5 ms Timeout mit `xSemaphoreTake()`
- I2C-Aufteilung Sensor-Knoten: Reads (MPU6050, INA260) auf Core 1, Writes (PCA9685) auf Core 0

### Watchdog

Core 0 prueft periodisch `core1_heartbeat` (Zeitstempel von Core 1). Bei Ausbleiben > Timeout (50 Zyklen, ~1 s) wird ein Fehler gemeldet.

## Sicherheitsarchitektur

Der AMR implementiert sechs gestaffelte Sicherheitsebenen. Die ersten vier liegen auf Ebene A (MCU), die fuenfte auf Ebene B (ROS2), die sechste auf Ebene B (Benutzeroberflaeche):

| Ebene | Mechanismus | Ausloeser | Latenz | Abhaengigkeit |
|-------|-------------|-----------|--------|---------------|
| 1 | MCU Failsafe-Timer | Kein `/cmd_vel` > 500 ms | < 520 ms | Keine (lokal auf Fahrkern) |
| 2 | Batterie-Unterspannung | < 9.5 V (Hysterese +0.3 V) | Sofort | Sensor- und Sicherheitsbasis, INA260 |
| 3 | CAN-Notstopp | Cliff (0x120) oder Battery-Shutdown (0x141) | < 20 ms | CAN-Bus, kein Pi 5 noetig |
| 4 | Inter-Core-Watchdog | 50 Zyklen (~1 s) ohne Core-1-Heartbeat | ~1 s | Lokal auf Fahrkern |
| 5 | Cliff-Safety-Knoten (ROS2) | `/cliff` OR `/range/front` < 80 mm | ~50 ms | Pi 5, Docker, micro-ROS |
| 6 | Dashboard Deadman-Timer | Kein Heartbeat > 300 ms | 300 ms | Netzwerk, Browser |

Zusaetzliche MCU-Schutzmechanismen:

- **Hard-Stop:** Bei |tv| < 0.01 wird die PID-Rampe umgangen — sofortiger Stillstand (< 20 ms)
- **PID-Stillstandserkennung:** Sollwert nahe Null → PID umgehen, PWM = 0

Die Ebenen sind redundant: Faellt Ebene B aus, schuetzen Ebenen 1–4 auf MCU-Ebene.
