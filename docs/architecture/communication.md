---
title: Kommunikation
description: Dual-Path-Kommunikation (micro-ROS/UART + CAN-Bus) und CAN-Notstopp-Redundanzpfad.
---

# Kommunikation

## Dual-Path-Architektur

Die MCU-Knoten kommunizieren ueber zwei parallele Kanaele mit dem Pi 5:

- **micro-ROS/UART** (primaer): ROS2-Topics via Serial Transport, 921600 Baud
- **CAN-Bus** (sekundaer): 1 Mbit/s, MCP2515/SocketCAN auf Pi 5, TWAI auf ESP32-S3

CAN-Sends laufen in den Core-1-Tasks (`controlTask`/`sensorTask`), damit sie unabhaengig vom micro-ROS Agent funktionieren.

## CAN-Notstopp-Redundanzpfad

Der Drive-Knoten empfaengt Cliff- (0x120) und Battery-Shutdown-Signale (0x141) vom Sensor-Knoten ueber CAN-Bus und stoppt die Motoren direkt — unabhaengig von Pi 5 und micro-ROS.

```
Sensor-Knoten (Core 1, sensorTask)
  ├── CAN 0x120 (Cliff, 20 Hz, 1 Byte: 0x00=OK, 0x01=Cliff)
  └── CAN 0x141 (Battery Shutdown, Event, 1 Byte: 0x00=OK, 0x01=Shutdown)
        │
        ▼
Drive-Knoten (Core 1, controlTask, non-blocking receive)
  → can_cliff_stop / can_battery_stop Flags
  → tv=0, tw=0 (Motoren stoppen)
```

| Eigenschaft | Wert |
|-------------|------|
| Latenz | < 20 ms (ein controlTask-Zyklus bei 50 Hz) |
| Unabhaengigkeit | Funktioniert ohne Pi 5, Docker oder micro-ROS |
| Non-blocking | `twai_receive()` mit `pdMS_TO_TICKS(0)` |

## Dashboard-Anbindung

```
ROS2 Topics → dashboard_bridge.py → WSS:9090 → useWebSocket → Zustand Store → React
Browser-Events → useJoystick → Rate-Limiting → WSS:9090 → dashboard_bridge → ROS2
MJPEG: /image_raw → MJPEG-Server :8082 → <img> Tag
```

### Server → Client

| Nachricht | Rate | Inhalt |
|-----------|------|--------|
| telemetry | 10 Hz | Odometrie, Geschwindigkeit |
| scan | 2 Hz | LiDAR-Daten |
| system | 1 Hz | CPU, RAM, Temperatur |
| map | 0.5 Hz | SLAM-Kartendaten |
| sensor_status | 2 Hz | Cliff, Ultraschall, IMU |

### Client → Server

| Nachricht | Rate | Inhalt |
|-----------|------|--------|
| cmd_vel | 10 Hz | Joystick-Steuerung |
| heartbeat | 5 Hz | Deadman-Signal |
| servo_cmd | 10 Hz | Servo-Position |
| nav_goal | Einmalig | Navigationsziel (Kartenklick) |

## Datenfluss Ende-zu-Ende (Cliff-Erkennung)

```
Sensor-Knoten Core 1 (sensorTask, 20 Hz)
  IR-Sensor → cliff_detected = true
       │
       ├──► SharedData (Mutex) → Core 0 → micro-ROS /cliff
       │                                     │
       │                               cliff_safety_node
       │                                 /cmd_vel = Zero-Twist
       │                                 /audio/play = "cliff_alarm"
       │                                     └──► dashboard_bridge → WSS → Browser
       │
       └──► CAN 0x120 ──► Drive-Knoten → tv=0, tw=0 (< 20 ms)
```

Zwei parallele Pfade: ROS2 (ueber Pi 5, ~50 ms) und CAN (direkt MCU-zu-MCU, < 20 ms).
