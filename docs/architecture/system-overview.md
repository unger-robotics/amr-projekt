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

## Systemdiagramm

``` mermaid
graph TB
  subgraph C["Ebene C — Intelligente Interaktion (optional)"]
    HAILO["Host: Hailo-8L Runner<br/>YOLOv8 @ 5 Hz"]
    UDP["hailo_udp_receiver"]
    GEMINI["gemini_semantic_node<br/>Gemini 3.1 flash-lite"]
    TTS["tts_speak_node<br/>gTTS → MAX98357A"]
    RESPEAKER["ReSpeaker DoA"]
    HAILO -->|UDP:5005| UDP
    UDP -->|"/vision/detections"| GEMINI
    GEMINI -->|"/vision/semantics"| TTS
    RESPEAKER -->|"/sound_direction"| TTS
  end

  subgraph B["Ebene B — Bedien- und Leitstandsebene"]
    subgraph DOCKER["Docker-Container (ros:humble)"]
      AGENT_D["micro-ROS Agent<br/>/dev/amr_drive"]
      AGENT_S["micro-ROS Agent<br/>/dev/amr_sensor"]
      SLAM["SLAM Toolbox"]
      NAV["Nav2"]
      ODOM_TF["odom_to_tf"]
      CLIFF["cliff_safety_node"]
      AUDIO["audio_feedback_node"]
      CAN_BR["can_bridge_node"]
      DASH_BR["dashboard_bridge<br/>WSS:9090 / MJPEG:8082"]
    end
    BROWSER["Benutzeroberflaeche<br/>React/Vite HTTPS:5173"]
    BROWSER -->|WSS:9090| DASH_BR
    DASH_BR -->|WSS:9090| BROWSER
  end

  subgraph A["Ebene A — Fahrkern"]
    DRIVE["Drive-Knoten ESP32-S3<br/>Core 0: micro-ROS<br/>Core 1: PID 50 Hz"]
    SENSOR["Sensor-Knoten ESP32-S3<br/>Core 0: micro-ROS<br/>Core 1: Sensorerfassung"]
    CAN_BUS["CAN-Bus 1 Mbit/s<br/>Cliff 0x120 / Battery 0x141"]
    DRIVE --- CAN_BUS
    SENSOR --- CAN_BUS
  end

  DRIVE -->|"UART 921600"| AGENT_D
  AGENT_D -->|"UART 921600"| DRIVE
  SENSOR -->|"UART 921600"| AGENT_S
  AGENT_S -->|"UART 921600"| SENSOR

  style C fill:#1a0a2e,stroke:#00E5FF,color:#cdd9e5
  style B fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style A fill:#0B131E,stroke:#00E5FF,color:#cdd9e5
  style DOCKER fill:#162435,stroke:#517C96,color:#cdd9e5
```

## Docker-Container-Grenzen

``` mermaid
graph LR
  subgraph CONTAINER["Docker-Container (arm64)"]
    direction TB
    NODES["ROS2 Nodes:<br/>micro-ROS Agents, SLAM, Nav2,<br/>cliff_safety, dashboard_bridge,<br/>audio, can_bridge, vision, TTS"]
    DEV["Devices:<br/>/dev/amr_drive, /dev/amr_sensor,<br/>/dev/ttyUSB0, /dev/snd"]
    VOL["Volumes:<br/>my_bot (rw), scripts (ro),<br/>dashboard (ro), Named Volumes"]
    NET["Network: host, Privileged: true"]
  end

  subgraph HOST["Host (Pi 5, Debian Trixie)"]
    HAILO_H["host_hailo_runner.py<br/>Python 3.13, Hailo-8L"]
    VITE["Dashboard Dev-Server<br/>npm run dev :5173"]
    CERT["mkcert-Zertifikate"]
  end

  HOST -->|localhost| CONTAINER
  CONTAINER -->|localhost| HOST

  style CONTAINER fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style HOST fill:#0B131E,stroke:#517C96,color:#cdd9e5
```

## TF-Baum

``` mermaid
graph LR
  ODOM["odom"] -->|"dynamisch, 20 Hz<br/>odom_to_tf"| BASE["base_link"]
  BASE -->|"statisch<br/>x=0.10, z=0.235, yaw=pi"| LASER["laser"]
  BASE -->|"statisch<br/>x=0.10, z=0.08"| CAM["camera_link"]
  BASE -->|"statisch<br/>x=0.15, z=0.05"| US["ultrasonic_link"]

  style ODOM fill:#111D2B,stroke:#00E5FF,color:#00E5FF
  style BASE fill:#111D2B,stroke:#00E5FF,color:#00E5FF
  style LASER fill:#111D2B,stroke:#00FF66,color:#00FF66
  style CAM fill:#111D2B,stroke:#517C96,color:#517C96
  style US fill:#111D2B,stroke:#517C96,color:#517C96
```

Der LiDAR ist 180 Grad gedreht montiert — die TF-Transformation (`yaw=pi`) kompensiert dies.
