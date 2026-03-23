---
title: Systemuebersicht
description: Drei-Ebenen-Architektur der AMR-Plattform mit Systemdiagramm und Datenfluss.
---

# Systemuebersicht

Der AMR besteht aus einem Raspberry Pi 5 als zentralem ROS2-Rechner und zwei ESP32-S3-Knoten fuer echtzeitnahe I/O- und Regelaufgaben.

## Drei-Ebenen-Modell

| Ebene | Bezeichnung | Komponenten | Aufgabe |
|-------|-------------|-------------|---------|
| A | Fahrkern sowie Sensor- und Sicherheitsbasis | Drive-Knoten, Sensor-Knoten (ESP32-S3) | Echtzeit-Regelung, Sensorerfassung, Sicherheits-Basisfunktionen |
| B | Bedien- und Leitstandsebene | Pi 5 (ROS2, Nav2, SLAM), Benutzeroberflaeche (React) | Koordination, Kartierung, Navigation, Fernsteuerung |
| C | Intelligente Interaktion | Hailo-8L, Gemini Cloud, gTTS, ReSpeaker | Objekterkennung, Sprachausgabe, semantische Beschreibung |

Ebene A arbeitet autonom — der CAN-Notstopp funktioniert ohne Pi 5. Ebene B setzt auf micro-ROS-Kommunikation mit A auf. Ebene C ist vollstaendig optional und ueber Launch-Argumente zuschaltbar.

## Hauptkomponenten

- **Pi 5:** ROS2, SLAM, Navigation, Dashboard-Bridge, optionale Vision, Audio-Feedback und TTS-Sprachausgabe (MAX98357A I2S)
- **Drive-Knoten:** Motoransteuerung, Encoder, PID, Odometrie, LED
- **Sensor-Knoten:** Ultraschall, Cliff, IMU, Batterie, Servo (PCA9685 PWM)
- **Peripherie:** LiDAR, Kamera, optionale Hailo-/Gemini-Pipeline

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
│  [Browser: Benutzeroberflaeche React/Vite]  HTTPS:5173                          │
│    Zustand Store ◄──► useWebSocket ◄──WSS:9090──► dashboard_bridge              │
│    Joystick → cmd_vel 10 Hz, Heartbeat 5 Hz                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Ebene A — Fahrkern                                                             │
│                                                                                 │
│  [Drive-Knoten ESP32-S3]              [Sensor-Knoten ESP32-S3]                  │
│    Core 0: micro-ROS Executor         Core 0: micro-ROS Executor                │
│      Sub: /cmd_vel, /hardware           Sub: /servo_cmd, /hardware              │
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
└───────────────────────────────────────────────────────────────────────┘

┌── Host (Raspberry Pi 5, Debian Trixie) ────────────────────────────┐
│  host_hailo_runner.py (Python 3.13, Hailo-8L SDK)                     │
│  Dashboard Dev-Server (npm run dev, :5173)                            │
│  mkcert-Zertifikate                                                   │
└───────────────────────────────────────────────────────────────────────┘
```

## TF-Baum

```
odom → base_link              (dynamisch, odom_to_tf, 20 Hz)
  ├── laser                   (statisch, x=0.10, z=0.235, yaw=pi)
  ├── camera_link             (statisch, x=0.10, z=0.08, use_camera)
  └── ultrasonic_link         (statisch, x=0.15, z=0.05, use_sensors)
```

Der LiDAR ist 180 Grad gedreht montiert — die TF-Transformation (`yaw=pi`) kompensiert dies.
