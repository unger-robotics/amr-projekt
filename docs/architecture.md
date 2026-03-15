# Architektur

## Zielbild

Der AMR besteht aus einem Raspberry Pi 5 als zentralem ROS2-Rechner und zwei ESP32-S3-Knoten fuer echtzeitnahe I/O- und Regelaufgaben.

## Hauptkomponenten

- Pi 5: ROS2, SLAM, Navigation, Dashboard-Bridge, optionale Vision, Audio-Feedback (MAX98357A I2S)
- Drive-Knoten: Motoransteuerung, Encoder, PID, Odometrie, LED
- Sensor-Knoten: Ultraschall, Cliff, IMU, Batterie, Servo (PCA9685 PWM)
- LiDAR, Kamera, optionale Hailo-/Gemini-Pipeline

## Kommunikationspfade (Dual-Path)

Die MCU-Knoten kommunizieren ueber zwei parallele Kanaele mit dem Pi 5:

- **micro-ROS/UART** (primaer): ROS2-Topics via Serial Transport, Subscriber/Publisher fuer Steuerung und Telemetrie
- **CAN-Bus** (sekundaer): 1 Mbit/s, MCP2515/SocketCAN auf Pi 5, TWAI auf ESP32-S3, Fire-and-forget Diagnostik

CAN-Sends laufen in den Core-1-Tasks (`controlTask`/`sensorTask`), damit sie unabhaengig vom micro-ROS Agent funktionieren. Hardware-Dokumentation: `hardware/can-bus/CAN-Bus.md`.

## CAN-Notstopp-Redundanzpfad

Der Drive-Node empfaengt Cliff- (0x120) und Battery-Shutdown-Signale (0x141) vom Sensor-Node ueber CAN-Bus und stoppt die Motoren direkt — unabhaengig von Pi 5 und micro-ROS.

### Datenfluss

```
Sensor-Node (Core 1, sensorTask)
  ├── CAN 0x120 (Cliff, 20 Hz, 1 Byte: 0x00=OK, 0x01=Cliff)
  └── CAN 0x141 (Battery Shutdown, Event, 1 Byte: 0x00=OK, 0x01=Shutdown)
        │
        ▼
Drive-Node (Core 1, controlTask, non-blocking receive)
  → can_cliff_stop / can_battery_stop Flags
  → tv=0, tw=0 (Motoren stoppen)
```

### Eigenschaften

- **Latenz**: < 20 ms (ein controlTask-Zyklus bei 50 Hz)
- **Unabhaengigkeit**: Funktioniert ohne laufenden Pi 5, Docker-Container oder micro-ROS Agent
- **Nicht-latched**: Cliff-Stop folgt dem aktuellen Sensor-Zustand und reset sich automatisch
- **Non-blocking**: `twai_receive()` mit `pdMS_TO_TICKS(0)` blockiert den PID-Loop nicht
- **Redundanz**: Ergaenzt den bestehenden ROS2-Pfad (`/cliff` → `cliff_safety_node` → `/cmd_vel`)

## Architekturregel

Zeitkritische Low-Level-Funktionen bleiben auf den MCU-Knoten. Koordination, Mapping und Navigation bleiben auf dem Pi 5.

## Weitergehende Details

Die vollstaendige Systemarchitektur mit Datenflussdiagramm, Modulgrenzen und optionalen Teilsystemen (Dashboard, Kamera, Vision, Audio, ReSpeaker) ist in `planung/systemdokumentation.md` dokumentiert.
