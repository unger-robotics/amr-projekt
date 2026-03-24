---
description: >-
  Komponentenuebersicht der Drei-Ebenen-Architektur mit Hauptmodulen
  und Systemlogik.
---

# Architektur

## Zielbild

Der AMR besteht aus einem Raspberry Pi 5 als zentralem ROS2-Rechner und zwei ESP32-S3-Knoten fuer echtzeitnahe I/O- und Regelaufgaben. Die Architektur gliedert sich in drei Ebenen mit klarer Verantwortungstrennung.

Detaillierte Beschreibungen der einzelnen Architekturaspekte:

- [Systemuebersicht](architecture/system-overview.md) — Drei-Ebenen-Modell, Hauptkomponenten, Datenflussdiagramm
- [Zwei-Ebenen-Architektur](architecture/two-tier.md) — Sicherheitsarchitektur (6 Ebenen), Dual-Core-Pattern, Watchdog
- [Kommunikation](architecture/communication.md) — Dual-Path (micro-ROS/UART + CAN-Bus), CAN-Notstopp-Redundanzpfad

## Vollstaendiges Systemdiagramm

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Ebene C — Intelligente Interaktion (optional)                                  │
│                                                                                 │
│  [Host: Hailo-8L Runner]──UDP:5005──>[Docker: hailo_udp_receiver]               │
│       YOLOv8 5 Hz                       │                                       │
│                                         ▼                                       │
│                                  /vision/detections                             │
│                                         │                                       │
│                                         ▼                                       │
│                              [gemini_semantic_node]──>/vision/semantics          │
│                               Gemini 3.1 flash-lite         │                   │
│                                                             ▼                   │
│                                                      [tts_speak_node]           │
│                                                       gTTS → mpg123            │
│  [ReSpeaker DoA]──>/sound_direction                    → MAX98357A I2S          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Ebene B — Bedien- und Leitstandsebene                                          │
│                                                                                 │
│  ┌── Docker-Container (ros:humble, network_mode:host, privileged) ───────────┐  │
│  │                                                                           │  │
│  │  [micro-ROS Agent x2]   [SLAM Toolbox]   [Nav2]   [odom_to_tf]           │  │
│  │    /dev/amr_drive          /map            /cmd_vel   odom→base_link      │  │
│  │    /dev/amr_sensor         /scan                                          │  │
│  │                                                                           │  │
│  │  [cliff_safety_node]   [audio_feedback_node]   [can_bridge_node]          │  │
│  │    /nav_cmd_vel →          /audio/play →          SocketCAN →             │  │
│  │    /cmd_vel                aplay → /dev/snd       Queue 512, 100 Hz       │  │
│  │                                                                           │  │
│  │  [dashboard_bridge]                                                       │  │
│  │    WSS:9090 ◄──► ROS2 Topics                                             │  │
│  │    MJPEG:8082 ← /image_raw                                               │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  [Browser: Benutzeroberflaeche React/Vite]  HTTPS:5173                                    │
│    Zustand Store ◄──► useWebSocket ◄──WSS:9090──► dashboard_bridge              │
│    Joystick → cmd_vel 10 Hz, Heartbeat 5 Hz                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Ebene A — Fahrkern                                                             │
│                                                                                 │
│  [Drive-Knoten ESP32-S3]              [Sensor-Knoten ESP32-S3]                      │
│    Core 0: micro-ROS Executor         Core 0: micro-ROS Executor                │
│      Sub: /cmd_vel, /hardware_cmd      Sub: /servo_cmd, /hardware_cmd           │
│      Pub: /odom 20 Hz                   Pub: /range, /cliff, /imu, /battery     │
│    Core 1: PID 50 Hz, Encoder,        Core 1: Sensorerfassung                   │
│      CAN TX/RX                          (Cliff 20 Hz, US 10 Hz,                │
│                                          IMU 50 Hz, Batt 2 Hz), CAN TX         │
│         │          ▲                       │          ▲                          │
│         │ UART     │ UART                  │ UART     │ UART                    │
│         │ 921600   │ 921600                │ 921600   │ 921600                  │
│         ▼          │                       ▼          │                          │
│      [Pi 5 /dev/amr_drive]          [Pi 5 /dev/amr_sensor]                      │
│                                                                                 │
│  ───── CAN-Bus 1 Mbit/s (MCP2515/TWAI) ─────                                   │
│    Drive ◄──0x120 Cliff──► Sensor                                               │
│    Drive ◄──0x141 Battery──► Sensor                                             │
│    + Diagnostik-Frames (bidirektional)                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Docker-Container-Grenzen

```
┌── Docker-Container (ros:humble-ros-base, arm64) ─────────────────────┐
│                                                                       │
│  ROS2 Nodes: micro-ROS Agents, SLAM, Nav2, cliff_safety,             │
│              dashboard_bridge, audio_feedback, can_bridge,            │
│              hailo_udp_receiver, gemini_semantic, tts_speak,          │
│              odom_to_tf, aruco_docking                                │
│                                                                       │
│  Devices:  /dev/amr_drive, /dev/amr_sensor, /dev/ttyUSB0, /dev/snd   │
│  Volumes:  my_bot (rw), scripts (ro), dashboard (ro, TLS-Certs),     │
│            hardware (ro), asound.conf, X11, Named (build/install/log) │
│  Network:  host (kein Bridge-Netzwerk)                                │
│  Privileged: true                                                     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

┌── Host (Raspberry Pi 5, Debian Trixie) ────────────────────────────┐
│  host_hailo_runner.py (Python 3.13, Hailo-8L SDK)                     │
│  Dashboard Dev-Server (npm run dev, :5173)                            │
│  mkcert-Zertifikate                                                   │
└───────────────────────────────────────────────────────────────────────┘
```

Der Container laeuft mit `network_mode: host` und `privileged: true`, um Zugriff auf serielle Geraete, Audio-Hardware und SocketCAN zu ermoeglichen. Host-only-Prozesse (Hailo-Runner, Dashboard-Dev-Server) kommunizieren ueber localhost-Ports.

## Datenfluss Ende-zu-Ende

Beispiel: Cliff-Erkennung bis Dashboard-Anzeige und Motorstopp:

```
1. Sensor-Knoten Core 1 (sensorTask, 20 Hz)
   IR-Sensor → cliff_detected = true
        │
        ├──► SharedData.cliff (Mutex) → Core 0 micro-ROS Pub /cliff
        │                                      │
        │                                      ▼
        │                               micro-ROS Agent (UART 921600)
        │                                      │
        │                                      ▼
        │                               cliff_safety_node
        │                                 /cmd_vel = Zero-Twist (20 Hz)
        │                                 /audio/play = "cliff_alarm"
        │                                      │
        │                                      ├──► dashboard_bridge → WSS → Browser
        │                                      │     sensor_status (event)
        │                                      │
        │                                      └──► audio_feedback_node
        │                                            aplay → MAX98357A
        │
        └──► CAN 0x120 (1 Byte: 0x01) ──► Drive-Knoten Core 1
                                            can_cliff_stop = true
                                            tv=0, tw=0 (< 20 ms)
```

Zwei parallele Pfade: ROS2 (ueber Pi 5, ~50 ms) und CAN (direkt MCU-zu-MCU, < 20 ms). Der CAN-Pfad ist die Rueckfallebene bei Ausfall von Pi 5 oder micro-ROS.

## Architekturregel

Zeitkritische Low-Level-Funktionen bleiben auf den MCU-Knoten. Koordination, Kartierung und Navigation bleiben auf dem Pi 5.

## TF-Baum

```
odom → base_link              (dynamisch, odom_to_tf, 20 Hz)
  ├── laser                   (statisch, x=0.10, z=0.235, yaw=pi)
  ├── camera_link             (statisch, x=0.10, z=0.08, use_camera)
  └── ultrasonic_link         (statisch, x=0.15, z=0.05, use_sensors)
```

Der LiDAR ist 180° gedreht montiert — die TF-Transformation (`yaw=pi`) kompensiert dies.

## Weitergehende Details

| Bereich | Dokument |
|---------|----------|
| Firmware (Drive-Knoten, Sensor-Knoten) | `amr/mcu_firmware/CLAUDE.md` |
| ROS2-System (Topics, Launch, Nodes) | [Topics und TF-Baum](ros2_system.md) |
| Dashboard (Komponenten, API) | [Dashboard](dashboard.md) |
| Vision-Pipeline | [Vision-Pipeline](vision_pipeline.md) |
| Hardware und Schaltplan | `hardware/docs/hardware-setup.md` |
| CAN-Bus Spezifikation | `hardware/can-bus/CAN-Bus.md` |
| Serielle Ports und udev | [Serielle Schnittstellen](serial_port_management.md) |
| Roboter-Parameter | [Roboter-Parameter](robot_parameters.md) |
| Build und Deployment | [Build und Deployment](build_and_deploy.md) |
| Systemdokumentation | [Systemdokumentation](systemdokumentation.md) |
| Benutzerhandbuch | [Benutzerhandbuch](benutzerhandbuch.md) |
