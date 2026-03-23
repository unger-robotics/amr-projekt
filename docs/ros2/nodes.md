---
title: Knotenuebersicht
description: Alle ROS2-Knoten, Topics, TF-Baum und Launch-Parameter der AMR-Plattform.
---

# Knotenuebersicht

Alle Knoten werden ueber `full_stack.launch.py` orchestriert. Optionale Knoten sind per Launch-Parameter steuerbar.

## Knoten

| Knoten | Aktivierung | Beschreibung |
|---|---|---|
| `rplidar_node` | immer | RPLidar A1, `/dev/ttyUSB0`, 115200 Baud |
| `micro_ros_agent_drive` | immer | Serial-Bridge zum Drive-Knoten, 921600 Baud |
| `micro_ros_agent_sensor` | `use_sensors` | Serial-Bridge zum Sensor-Knoten, 921600 Baud |
| `odom_to_tf` | immer | Dynamischer TF `odom` → `base_link` aus `/odom` |
| `slam_toolbox` | `use_slam` | SLAM Toolbox async Online-Modus |
| Nav2-Stack | `use_nav` | RPP Controller 20 Hz, NavFn Planer 10 Hz |
| `cliff_safety_node` | `use_cliff_safety` | Cliff- und Hindernisstopp-Multiplexer |
| `dashboard_bridge` | `use_dashboard` | WebSocket :9090, MJPEG :8082 |
| `hailo_udp_receiver` | `use_vision` | Hailo-8L Inferenz via UDP |
| `gemini_semantic_node` | `use_vision` | Gemini-Cloud-Semantik |
| `audio_feedback_node` | `use_audio` | WAV via aplay/MAX98357A I2S |
| `tts_speak_node` | `use_tts` | TTS via gTTS + mpg123 |
| `can_bridge_node` | `use_can` | CAN-to-ROS2-Bridge (SocketCAN) |
| `respeaker_doa_node` | `use_respeaker` | ReSpeaker Mic Array DoA/VAD |
| `voice_command_node` | `use_voice` | Sprachsteuerung (Gemini Flash STT) |

## MCU-Topics (micro-ROS)

| Topic | Typ | Rate | Beschreibung |
|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | 20 Hz | Radodometrie (~725 B, Reliable) |
| `/imu` | `sensor_msgs/Imu` | ~30–35 Hz | MPU6050 Beschleunigung + Gyroskop |
| `/battery` | `sensor_msgs/BatteryState` | 2 Hz | INA260 Spannung, Strom, Leistung |
| `/range/front` | `sensor_msgs/Range` | ~8–9 Hz | HC-SR04 Ultraschall |
| `/cliff` | `std_msgs/Bool` | 20 Hz | MH-B IR Cliff (true = Abgrund) |
| `/cmd_vel` | `geometry_msgs/Twist` | — | Fahrbefehl (linear.x, angular.z) |
| `/servo_cmd` | `geometry_msgs/Point` | — | Servo-Winkel (x=Pan, y=Tilt) |

## Pi-5-Topics

| Topic | Typ | Rate | Beschreibung |
|---|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | 7.0 Hz | RPLidar A1 Laserscandaten |
| `/nav_cmd_vel` | `geometry_msgs/Twist` | — | Nav2-Fahrbefehl |
| `/dashboard_cmd_vel` | `geometry_msgs/Twist` | — | Dashboard-Joystick |
| `/vision/detections` | `std_msgs/String` | ~5 Hz | Hailo YOLOv8 (JSON) |
| `/vision/semantics` | `std_msgs/String` | — | Gemini Szenenbeschreibung |
| `/voice/command` | `std_msgs/String` | event | Strukturierter Sprachbefehl |
| `/audio/play` | `std_msgs/String` | — | WAV-Dateiname |

## Launch-Parameter

| Parameter | Default | Beschreibung |
|---|---|---|
| `use_slam` | True | SLAM Toolbox |
| `use_nav` | True | Nav2 Navigation |
| `use_rviz` | False | RViz2 Visualisierung |
| `use_sensors` | True | Sensor-Knoten |
| `use_cliff_safety` | True | Cliff-Safety Multiplexer |
| `use_camera` | False | Kamera (v4l2loopback) |
| `use_dashboard` | False | WebSocket + MJPEG |
| `use_vision` | False | Hailo + Gemini |
| `use_audio` | False | Audio-Feedback |
| `use_can` | False | CAN-to-ROS2-Bridge |
| `use_tts` | False | TTS-Sprachausgabe |
| `use_respeaker` | False | ReSpeaker DoA/VAD |
| `use_voice` | False | Sprachsteuerung |
