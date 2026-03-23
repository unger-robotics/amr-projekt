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

``` mermaid
graph TD
  SENSOR["Sensor-Knoten<br/>Core 1, sensorTask"] -->|"CAN 0x120<br/>Cliff, 20 Hz"| DRIVE["Drive-Knoten<br/>Core 1, controlTask"]
  SENSOR -->|"CAN 0x141<br/>Battery Shutdown"| DRIVE
  DRIVE --> STOP["tv=0, tw=0<br/>Motoren stoppen"]

  style SENSOR fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style DRIVE fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style STOP fill:#111D2B,stroke:#FF2A40,color:#FF2A40
```

| Eigenschaft | Wert |
|-------------|------|
| Latenz | < 20 ms (ein controlTask-Zyklus bei 50 Hz) |
| Unabhaengigkeit | Funktioniert ohne Pi 5, Docker oder micro-ROS |
| Non-blocking | `twai_receive()` mit `pdMS_TO_TICKS(0)` |

## Dashboard-Anbindung

``` mermaid
graph LR
  subgraph Server-to-Client
    TOPICS["ROS2 Topics"] --> BRIDGE["dashboard_bridge<br/>WSS:9090"]
    BRIDGE --> WS["useWebSocket"]
    WS --> STORE["Zustand Store"]
    STORE --> REACT["React UI"]
  end

  subgraph Client-to-Server
    JOY["Joystick"] --> RATE["Rate-Limiting<br/>10 Hz"]
    RATE --> BRIDGE2["dashboard_bridge"]
    BRIDGE2 --> ROS["ROS2 Publish"]
  end

  MJPEG["/image_raw"] --> STREAM["MJPEG :8082"]
  STREAM --> IMG["Browser img-Tag"]

  style BRIDGE fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style BRIDGE2 fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
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

``` mermaid
graph TD
  IR["IR-Sensor<br/>cliff_detected = true"] --> SHARED["SharedData<br/>Mutex"]
  IR --> CAN["CAN 0x120"]

  subgraph ROS2-Pfad ["ROS2-Pfad (~50 ms)"]
    SHARED --> CORE0["Core 0<br/>micro-ROS /cliff"]
    CORE0 --> AGENT["micro-ROS Agent<br/>UART 921600"]
    AGENT --> SAFETY["cliff_safety_node"]
    SAFETY --> CMDVEL["/cmd_vel = Zero-Twist"]
    SAFETY --> ALARM["/audio/play = cliff_alarm"]
    SAFETY --> DASH["dashboard_bridge<br/>→ WSS → Browser"]
  end

  subgraph CAN-Pfad ["CAN-Pfad (< 20 ms)"]
    CAN --> DRIVE_CAN["Drive-Knoten<br/>can_cliff_stop = true"]
    DRIVE_CAN --> MOTOR_STOP["tv=0, tw=0"]
  end

  style IR fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style MOTOR_STOP fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style CMDVEL fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style ROS2-Pfad fill:#0B131E,stroke:#517C96,color:#cdd9e5
  style CAN-Pfad fill:#0B131E,stroke:#00FF66,color:#cdd9e5
```

Zwei parallele Pfade: ROS2 (ueber Pi 5, ~50 ms) und CAN (direkt MCU-zu-MCU, < 20 ms).
