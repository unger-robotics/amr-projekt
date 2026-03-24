---
title: FreeRTOS-Architektur
description: Dual-Core Task-Verteilung auf den ESP32-S3-Knoten mit FreeRTOS.
---

# FreeRTOS-Architektur

Beide MCU-Knoten verwenden dasselbe Dual-Core-Pattern:

```
Core 0 (Arduino loop()):
  - micro-ROS Executor: spin_some() fuer Publisher und Subscriber
  - Servo-I2C-Writes (nur Sensor-Knoten, PCA9685)
  - ~500 Hz Zyklusrate

Core 1 (FreeRTOS Task):
  - Drive-Knoten: PID-Regelung (50 Hz), Encoder-Polling, CAN-Sends
  - Sensor-Knoten: IMU-Reads (50 Hz), Ultraschall (10 Hz), Cliff (20 Hz),
    Batterie (2 Hz), CAN-Sends
  - Inter-Core Heartbeat-Check (Watchdog)
```

Die Core-Zuordnung wird explizit festgelegt: `-DARDUINO_RUNNING_CORE=0` in `platformio.ini` setzt Arduino `loop()` auf Core 0 (Board-Default waere Core 1). `xTaskCreatePinnedToCore(..., 1)` fixiert die Echtzeit-Tasks auf Core 1.

## Drive-Knoten (Fahrkern)

| Core | Aufgabe | Rate |
|------|---------|------|
| 0 | micro-ROS Executor: Sub `/cmd_vel`, `/hardware`, `/battery_shutdown`; Pub `/odom` | 20 Hz Pub |
| 0 | LED-Steuerung (MOSFET-PWM) | bei Aenderung |
| 1 | PID-Regelschleife, Encoder-Auswertung | 50 Hz |
| 1 | CAN-Send: Odom, Rad-Geschwindigkeit, PWM, Heartbeat | 1–20 Hz |
| 1 | CAN-Receive: Cliff-Stop (0x120), Battery-Shutdown (0x141) | non-blocking |

## Sensor-Knoten (Sensor- und Sicherheitsbasis)

| Core | Aufgabe | Rate |
|------|---------|------|
| 0 | micro-ROS Executor: Sub `/servo_cmd`, `/hardware`; Pub `/range`, `/cliff`, `/imu`, `/battery` | je nach Sensor |
| 0 | Servo-I2C-Write (PCA9685) | 5 Hz |
| 1 | Cliff-Sensor (MH-B IR) | 20 Hz |
| 1 | Ultraschall (HC-SR04, ISR) | 10 Hz |
| 1 | IMU (MPU6050, I2C) | 50 Hz |
| 1 | Batterie (INA260, I2C) | 2 Hz |
| 1 | CAN-Send: Range, Cliff, IMU, Batterie, Heartbeat | je nach Sensor |

## Synchronisation

### SharedData-Mutex

`SharedData`-Struct mit `SemaphoreHandle_t` schuetzt den Datenaustausch zwischen Core 0 und Core 1. Beide Cores verwenden `xSemaphoreTake()`/`xSemaphoreGive()` mit kurzem Timeout.

### I2C-Mutex (nur Sensor-Knoten)

Drei Geraete teilen den I2C-Bus (400 kHz):

| Geraet | Adresse | Zugriff | Core |
|--------|---------|---------|------|
| MPU6050 | 0x68 | Read (50 Hz) | Core 1 |
| INA260 | 0x40 | Read (2 Hz) | Core 1 |
| PCA9685 | 0x41 (A0-Loetbruecke) | Write (bei Aenderung) | Core 0 |

`i2c_mutex` mit 5 ms Timeout verhindert gleichzeitige Bus-Zugriffe.

**Init-Reihenfolge:** PCA9685 vor MPU6050 und INA260 initialisieren. `delay(2000)` vor `Wire.begin()`.

## Watchdog

Core 0 prueft periodisch `core1_heartbeat` (Zeitstempel). Bei Ausbleiben > 50 Zyklen (~1 s) ohne Core-1-Update wird ein Fehler gemeldet und die Motoren gestoppt.
