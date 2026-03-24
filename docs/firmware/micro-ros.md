---
title: micro-ROS-Integration
description: micro-ROS Serial Transport, QoS-Konfiguration und Zwei-Knoten-Architektur.
---

# micro-ROS-Integration

## Zwei-Knoten-Architektur

Die Firmware besteht aus zwei getrennten PlatformIO-Projekten. Jeder ESP32-S3 erhaelt eine eigene micro-ROS-Library (statisch kompiliert).

!!! info "ESP32-S3-Support"
    ESP32-S3 ist nicht in der offiziellen [micro_ros_platformio Board-Tabelle](https://github.com/micro-ROS/micro_ros_platformio) gelistet. Der Support ist Community-basiert und im Projekt erfolgreich validiert.

| Eigenschaft | Drive-Knoten | Sensor-Knoten |
|---|---|---|
| **Verzeichnis** | `amr/mcu_firmware/drive_node/` | `amr/mcu_firmware/sensor_node/` |
| **Konfiguration** | `include/config_drive.h` (v4.0.0) | `include/config_sensors.h` (v3.0.0) |
| **udev-Symlink** | `/dev/amr_drive` | `/dev/amr_sensor` |
| **Baudrate** | 921600 (micro-ROS UART) | 921600 (micro-ROS UART) |
| **Funktion** | Motoren, PID, Encoder, Odometrie, LED | IMU, Ultraschall, Cliff, Batterie, Servo |
| **CAN-ID-Bereich** | 0x200–0x2FF | 0x110–0x1F0 |

## micro-ROS Agent (Pi 5)

Zwei separate Agenten laufen im Docker-Container:

```bash
# Drive-Agent
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/amr_drive -b 921600

# Sensor-Agent
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/amr_sensor -b 921600
```

Beide werden automatisch ueber `full_stack.launch.py` gestartet.

## QoS-Konfiguration

### Publisher-Seite (Firmware)

Alle MCU-Publisher verwenden **Reliable** QoS (`rclc_publisher_init_default()`):

- `/odom` (~725 Bytes) — ueberschreitet XRCE-DDS MTU (512 B), erfordert Fragmentierung
- `/imu` (~550 Bytes) — ebenfalls fragmentiert
- `/battery`, `/cliff`, `/range/front`, `/battery_shutdown` — kleiner, aber einheitlich Reliable

### Subscriber-Seite (ROS2)

Der `cliff_safety_node` verwendet **Best-Effort** QoS fuer `/cliff`, damit er auch bei QoS-Mismatch Nachrichten empfaengt:

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy
qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
self.create_subscription(Bool, "/cliff", self.cliff_callback, qos_sensor)
```

### Maximale Nachrichtengroesse

2048 Bytes (MTU × STREAM_HISTORY).

## Build-Befehle

```bash
# Drive-Knoten
cd amr/mcu_firmware/drive_node
pio run -e drive_node                      # Kompilieren
pio run -e drive_node -t upload -t monitor # Upload + Serial Monitor

# Sensor-Knoten
cd amr/mcu_firmware/sensor_node
pio run -e sensor_node                      # Kompilieren
pio run -e sensor_node -t upload -t monitor # Upload + Serial Monitor
```

!!! warning "Immer `-e` angeben"
    `pio run -t upload` ohne `-e` flasht ALLE Environments — das letzte ueberschreibt die vorherigen.

Erster Build pro Knoten: ~15 Min (micro-ROS aus Source). Folgebuilds gecacht.

## Harte Constraints

- **Typen:** `int32_t`/`uint8_t`/`int16_t` statt `int`/`long`. Encoder-Zaehler: `volatile int32_t`
- **ISR:** `IRAM_ATTR`, globaler Scope (kein Namespace), volatile Globals
- **Speicher:** Keine dynamische Allokation zur Laufzeit
- **I2C in Callbacks:** Verboten. Deferred-Pattern: Callback → RAM-Struct → loop()/sensorTask → I2C
- **Getrennte Projekte:** Drive-Knoten und Sensor-Knoten werden immer getrennt gebaut, geflasht und betrieben
