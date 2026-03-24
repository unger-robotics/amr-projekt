---
title: Sensorik und Aktorik
description: Module beider ESP32-S3-Knoten – Motoren, PID, Sensoren, I2C, CAN-Bus.
---

# Sensorik und Aktorik

## Drive-Knoten Module

| Datei | Klasse | Beschreibung |
|---|---|---|
| `robot_hal.hpp` | `RobotHAL` | Motorsteuerung (Cytron MDD3A), PWM (LEDC), Encoder-ISR (Quadratur) |
| `pid_controller.hpp` | `PidController` | PID-Regler mit Anti-Windup (Kp=0.4, Ki=0.1, Kd=0.0) |
| `diff_drive_kinematics.hpp` | `DiffDriveKinematics` | (v, w) → (v_l, v_r), Odometrie-Integration |
| `twai_can.hpp` | `TwaiCan` | CAN 2.0B Sender (TWAI, 1 Mbit/s), IDs 0x200–0x2FF |

### PID-Regelung (50 Hz, Core 1)

```
Encoder-Ticks → Ist-Geschwindigkeit (m/s) → PID → PWM-Duty → Motor
                                                ↑
                                      Soll-Geschwindigkeit (aus /cmd_vel)
```

### LED-Steuerung (MOSFET-PWM)

SMD 5050 LED-Streifen via IRLZ24N MOSFET, LEDC Kanal 4. Konfigurierbar ueber `/hardware_cmd` (z-Feld = LED-PWM 0–255). Statusanzeige: Idle (Cyan pulsierend), Fahrt (Gruen), Fehler (Rot blinkend).

## Sensor-Knoten Module

| Datei | Klasse | Beschreibung |
|---|---|---|
| `range_sensor.hpp` | `RangeSensor` | HC-SR04 Ultraschall, ISR-basiert (Trigger/tryRead) |
| `cliff_sensor.hpp` | `CliffSensor` | MH-B IR Cliff-Sensor, GPIO-Poll |
| `mpu6050.hpp` | `MPU6050` | 6-Achsen IMU (I2C, 0x68), Komplementaerfilter (alpha=0.98) |
| `ina260.hpp` | `INA260` | Leistungs-Monitor (I2C, 0x40), Spannung/Strom/Power |
| `pca9685.hpp` | `PCA9685` | 16-Kanal PWM Servo-Controller (I2C, 0x41 via A0-Loetbruecke), Pan/Tilt |
| `twai_can.hpp` | `TwaiCan` | CAN 2.0B Sender (TWAI, 1 Mbit/s), IDs 0x110–0x1F0 |

### I2C-Bus (Wire, 400 kHz)

| Geraet | Adresse | Zugriff | Core | Rate |
|--------|---------|---------|------|------|
| MPU6050 | 0x68 | Read | Core 1 | 50 Hz |
| INA260 | 0x40 | Read | Core 1 | 2 Hz |
| PCA9685 | 0x41 (A0-Loetbruecke) | Write | Core 0 | bei Aenderung |

### Batterie-Ueberwachung (INA260)

- Spannung, Strom, Leistung mit 2 Hz
- Unterspannungsschutz: < 9.5 V → `/battery_shutdown` (Event) an Drive-Knoten
- Prozentberechnung: Lineare Interpolation 9.0–12.6 V (3S Li-Ion)

## CAN-Bus (Optional, TWAI 1 Mbit/s)

Hardware: SN65HVD230 CAN-Transceiver auf beiden Knoten + MCP2515/SocketCAN auf Pi 5.

### Drive-Knoten CAN-Frames (0x200–0x2FF)

| ID | Inhalt | Rate | Bytes |
|---|---|---|---|
| 0x200 | Odom Position (x, y als float32 LE) | 20 Hz | 8 |
| 0x201 | Odom Heading + Speed (yaw, v_linear) | 20 Hz | 8 |
| 0x210 | Rad-Geschwindigkeit (L, R als float32 rad/s) | 10 Hz | 8 |
| 0x220 | Motor-PWM (L, R als int16) | 10 Hz | 4 |
| 0x2F0 | Heartbeat (flags + uptime_mod256) | 1 Hz | 2 |

### Sensor-Knoten CAN-Frames (0x110–0x1F0)

| ID | Inhalt | Rate | Bytes |
|---|---|---|---|
| 0x110 | Ultraschall Range (float32 LE, Meter) | 10 Hz | 4 |
| 0x120 | Cliff (uint8: 0=OK, 1=Cliff) | 20 Hz | 1 |
| 0x130 | IMU ax, ay, az (mg) + gz (4x int16) | 50 Hz | 8 |
| 0x131 | IMU Heading (float32) | 50 Hz | 4 |
| 0x140 | Batterie V/I/P (uint16 mV + int16 mA + uint16 mW) | 2 Hz | 6 |
| 0x141 | Battery Shutdown (uint8: 0=OK, 1=Shutdown) | Event | 1 |
| 0x1F0 | Heartbeat (flags + uptime_mod256) | 1 Hz | 2 |
