---
description: >-
  ROS2-Topics, TF-Baum, QoS-Profile und Launch-Parameter
  der AMR-Plattform.
---

# ROS2-System

## Zweck

Referenz fuer den ROS2-Stack auf dem Raspberry Pi 5. Beschreibt Knoten, Topics, TF-Baum, Launch-Parameter, Docker-Setup, Symlink-Pattern und Betriebsmodi.

## Regel

Topic-Tabellen, TF-Details, Launch-Parameter und Docker-Konfiguration gehoeren nur in diese Datei. Firmware-Details stehen in `docs/firmware.md`, Dashboard-Details in `docs/dashboard.md`.

---

## 1. Knoten-Uebersicht

Alle Knoten werden ueber `full_stack.launch.py` orchestriert. Optionale Knoten sind per Launch-Parameter steuerbar.

| Knoten | Paket | Executable | Aktivierung | Beschreibung |
|---|---|---|---|---|
| `rplidar_node` | `rplidar_ros` | `rplidar_node` | immer | RPLidar A1, `/dev/ttyUSB0`, 115200 Baud |
| `laser_tf_publisher` | `tf2_ros` | `static_transform_publisher` | immer | Statischer TF `base_link` → `laser` (180 Grad Yaw) |
| `micro_ros_agent_drive` | `micro_ros_agent` | `micro_ros_agent` | immer | Serial-Bridge zum Drive-Node (`/dev/amr_drive`), 921600 Baud |
| `micro_ros_agent_sensor` | `micro_ros_agent` | `micro_ros_agent` | `use_sensors` | Serial-Bridge zum Sensor-Node (`/dev/amr_sensor`), 921600 Baud |
| `odom_to_tf` | `my_bot` | `odom_to_tf` | immer | Dynamischer TF `odom` → `base_link` aus `/odom` |
| `slam_toolbox` | `slam_toolbox` | `async_slam_toolbox_node` | `use_slam` | SLAM Toolbox async Online-Modus |
| Nav2-Stack | `nav2_bringup` | `navigation_launch.py` | `use_nav` | RPP Controller 20 Hz, NavFn Planer 10 Hz |
| `rviz2` | `rviz2` | `rviz2` | `use_rviz` | Visualisierung (Nav2-Standardansicht) |
| `v4l2_camera_node` | `v4l2_camera` | `v4l2_camera_node` | `use_camera` | Kamera via v4l2loopback, 640x480, YUYV→bgr8 |
| `camera_tf_publisher` | `tf2_ros` | `static_transform_publisher` | `use_camera` | Statischer TF `base_link` → `camera_link` |
| `ultrasonic_tf_publisher` | `tf2_ros` | `static_transform_publisher` | `use_sensors` | Statischer TF `base_link` → `ultrasonic_link` |
| `dashboard_bridge` | `my_bot` | `dashboard_bridge` | `use_dashboard` | WebSocket :9090, MJPEG :8082 |
| `hailo_udp_receiver` | `my_bot` | `hailo_udp_receiver_node` | `use_vision` | Hailo-8L Inferenz via UDP 127.0.0.1:5005 |
| `gemini_semantic_node` | `my_bot` | `gemini_semantic_node` | `use_vision` | Gemini-Cloud-Semantik |
| `cliff_safety_node` | `my_bot` | `cliff_safety_node` | `use_cliff_safety` | Cliff- und Hindernisstopp-Multiplexer |
| `audio_feedback_node` | `my_bot` | `audio_feedback_node` | `use_audio` | WAV via aplay/MAX98357A I2S |
| `can_bridge_node` | `my_bot` | `can_bridge_node` | `use_can` | CAN-to-ROS2-Bridge (SocketCAN) |
| `tts_speak_node` | `my_bot` | `tts_speak_node` | `use_tts` | TTS via gTTS + mpg123 |
| `respeaker_doa_node` | `my_bot` | `respeaker_doa_node` | `use_respeaker` | ReSpeaker Mic Array v2.0 DoA/VAD (USB, pyusb) |
| `voice_command_node` | `my_bot` | `voice_command_node` | `use_voice` | Sprachsteuerung ReSpeaker + Gemini Audio-STT (Cloud, primaer) / faster-whisper (Offline-Fallback) |
| `aruco_docking` | `my_bot` | `aruco_docking` | manuell | ArUco-Marker Visual Servoing (Standalone) |
| `hailo_inference_node` | `my_bot` | `hailo_inference_node` | manuell | Hailo-8L Echtzeit-Objekterkennung (YOLOv8) |

---

## 2. Topic-Tabelle

### 2.1 MCU-Topics (micro-ROS, ESP32-S3)

| Topic | Typ | Rate | QoS | Publisher / Subscriber | Beschreibung |
|---|---|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | 20 Hz | Reliable | Drive-Node (Pub) | Radodometrie, ~725 Bytes, Reliable wg. XRCE-DDS MTU |
| `/imu` | `sensor_msgs/Imu` | 50 Hz (Soll), ~30–35 Hz (Ist) | Reliable | Sensor-Node (Pub) | MPU6050 Beschleunigung + Gyroskop |
| `/battery` | `sensor_msgs/BatteryState` | 2 Hz | Reliable | Sensor-Node (Pub) | INA260 Spannung, Strom, Leistung |
| `/battery_shutdown` | `std_msgs/Bool` | Event | Reliable | Sensor-Node (Pub) | Unterspannungs-Notaus (< 9.5 V) |
| `/range/front` | `sensor_msgs/Range` | 10 Hz (Soll), ~8–9 Hz (Ist) | Reliable | Sensor-Node (Pub) | HC-SR04 Ultraschall, frame: `ultrasonic_link` |
| `/cliff` | `std_msgs/Bool` | 20 Hz | Reliable | Sensor-Node (Pub) | MH-B IR Cliff (true = Abgrund) |
| `/cmd_vel` | `geometry_msgs/Twist` | — | Reliable | Drive-Node (Sub) | Fahrbefehl (linear.x, angular.z) |
| `/servo_cmd` | `geometry_msgs/Point` | — | Reliable | Sensor-Node (Sub) | Servo-Winkel (x=Pan, y=Tilt) |
| `/hardware_cmd` | `geometry_msgs/Point` | — | Reliable | Drive (Sub: x=Motor-Limit, z=LED-PWM), Sensor (Sub: y=Servo-Speed) | Geraetekonfiguration |

### 2.2 Pi-5-Topics (ROS2-Knoten)

| Topic | Typ | Rate | QoS | Publisher / Subscriber | Beschreibung |
|---|---|---|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | 7,0 Hz | Sensor | rplidar_node (Pub) | RPLidar A1 Laserscandaten |
| `/nav_cmd_vel` | `geometry_msgs/Twist` | — | Reliable | Nav2 controller_server (Pub) | Nav2-Fahrbefehl (nur mit Cliff-Safety) |
| `/dashboard_cmd_vel` | `geometry_msgs/Twist` | — | Reliable | dashboard_bridge (Pub) | Dashboard-Joystick (nur mit Cliff-Safety) |
| `/sound_direction` | `std_msgs/Int32` | 10 Hz | Reliable | respeaker_doa_node (Pub) | Azimut 0–359 Grad |
| `/is_voice` | `std_msgs/Bool` | 10 Hz | Reliable | respeaker_doa_node (Pub) | Sprache erkannt (VAD) |
| `/voice/command` | `std_msgs/String` | event | Reliable | voice_command_node (Pub) | Strukturierter Sprachbefehl (Freitext) |
| `/voice/text` | `std_msgs/String` | event | Reliable | voice_command_node (Pub) | Rohtranskription |
| `/vision/detections` | `std_msgs/String` | ~5 Hz | Reliable | hailo_udp_receiver (Pub) | Hailo-8L YOLOv8 (JSON) |
| `/vision/semantics` | `std_msgs/String` | — | Reliable | gemini_semantic_node (Pub) | Gemini Szenenbeschreibung (JSON) |
| `/diagnostics/can` | `diagnostic_msgs/DiagnosticArray` | — | Reliable | can_bridge_node (Pub) | CAN-Bus Diagnostik |
| `/audio/play` | `std_msgs/String` | — | Reliable | cliff_safety_node (Pub), dashboard_bridge (Pub), audio_feedback_node (Sub) | WAV-Dateiname |
| `/audio/volume` | `std_msgs/Int32` | — | Reliable | dashboard_bridge (Pub), audio_feedback_node (Sub) | Lautstaerke 0–100% |
| `/camera/image_raw` | `sensor_msgs/Image` | — | Reliable | v4l2_camera_node (Pub) | Kamerabild 640x480 bgr8 |

---

## 3. TF-Baum

```
odom
  └── base_link              (dynamisch, odom_to_tf, aus /odom)
        ├── laser             (statisch, x=0.10, z=0.235, Yaw=180 Grad/pi)
        ├── camera_link       (statisch, x=0.10, z=0.08, optional: use_camera)
        └── ultrasonic_link   (statisch, x=0.15, z=0.05, optional: use_sensors)
```

| Frame | Parent | Typ | Knoten | Bedingung |
|---|---|---|---|---|
| `base_link` | `odom` | dynamisch | `odom_to_tf` | immer |
| `laser` | `base_link` | statisch | `laser_tf_publisher` | immer |
| `camera_link` | `base_link` | statisch | `camera_tf_publisher` | `use_camera:=True` |
| `ultrasonic_link` | `base_link` | statisch | `ultrasonic_tf_publisher` | `use_sensors:=True` |

Der `odom_to_tf`-Knoten subscribt `/odom` und broadcastet `odom` → `base_link`, da micro-ROS keinen eigenen TF-Broadcaster enthaelt.

---

## 4. Launch-Parameter

Alle Parameter fuer `full_stack.launch.py`:

| Parameter | Default | Beschreibung |
|---|---|---|
| `use_slam` | `True` | SLAM Toolbox (async Modus) |
| `use_nav` | `True` | Nav2 Navigation Stack |
| `use_rviz` | `False` | RViz2 Visualisierung |
| `drive_serial_port` | `/dev/amr_drive` | Serieller Port Drive-Node (USB-CDC) |
| `sensor_serial_port` | `/dev/amr_sensor` | Serieller Port Sensor-Node (USB-CDC) |
| `use_sensors` | `True` | Sensor-Node ESP32-S3 |
| `params_file` | `config/nav2_params.yaml` | Nav2-Parameter |
| `slam_params_file` | `config/mapper_params_online_async.yaml` | SLAM-Parameter |
| `use_camera` | `False` | Kamera-Knoten (v4l2loopback) |
| `camera_device` | `/dev/video10` | Video-Device |
| `use_dashboard` | `False` | Dashboard (WebSocket + MJPEG) |
| `use_vision` | `False` | Vision-Pipeline (Hailo + Gemini) |
| `use_cliff_safety` | `True` | Cliff-Safety cmd_vel-Multiplexer |
| `use_audio` | `False` | Audio-Feedback (MAX98357A I2S) |
| `use_can` | `False` | CAN-to-ROS2-Bridge (SocketCAN) |
| `use_tts` | `False` | TTS-Sprachausgabe (gTTS, Deutsch) |
| `use_respeaker` | `False` | ReSpeaker DoA/VAD (USB, pyusb) |
| `use_voice` | `False` | Sprachsteuerung (erfordert `use_respeaker:=True`, Gemini Audio-STT primaer / faster-whisper Fallback) |

**Beispiele:**

```bash
# Standard (SLAM + Nav2, Cliff-Safety an, RViz2 aus):
ros2 launch my_bot full_stack.launch.py

# Nur SLAM, ohne Navigation:
ros2 launch my_bot full_stack.launch.py use_nav:=False

# Vollausbau mit optionalen Subsystemen:
ros2 launch my_bot full_stack.launch.py use_camera:=True use_vision:=True use_dashboard:=True use_rviz:=False
```

---

## 5. Docker-Setup

### Basis-Image

`ros:humble-ros-base` (Ubuntu 22.04, arm64 multi-arch). Manuell installiert: RViz2, SLAM Toolbox, Nav2, RPLidar, v4l2_camera, micro-ROS Agent, Python 3.10 + Pakete.

### docker-compose.yml (vereinfachte Darstellung)

```yaml
services:
  amr:
    image: amr-ros2-humble:latest
    container_name: amr_ros2
    network_mode: host             # ROS2 DDS Multicast
    privileged: true               # Serial + GPIO
    devices:
      - "/dev/amr_drive:/dev/amr_drive"
      - "/dev/amr_sensor:/dev/amr_sensor"
      - "/dev/ttyUSB0:/dev/ttyUSB0"
      - "/dev/snd:/dev/snd"
    volumes:
      - ../pi5/ros2_ws/src/my_bot:/ros2_ws/src/my_bot:rw
      - ../scripts:/amr_scripts:ro
      - ../scripts:/scripts:ro         # Dual-Mount fuer Symlinks
      - ros2_build:/ros2_ws/build
      - ros2_install:/ros2_ws/install
    environment:
      - DISPLAY=${DISPLAY:-:0}
      - ROS_DOMAIN_ID=0
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
```

**Kritisch:** `../scripts` wird doppelt gemountet (`/amr_scripts` + `/scripts`), damit Symlinks in beiden Kontexten aufgeloest werden.

### Convenience-Befehle (run.sh)

```bash
cd amr/docker/
docker compose build                                                    # Image bauen (~15–20 Min)
./run.sh colcon build --packages-select my_bot --symlink-install        # Paket bauen
./run.sh ros2 launch my_bot full_stack.launch.py                        # Full-Stack
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false         # Nur SLAM
./run.sh exec bash                                                      # Shell im Container
./verify.sh                                                             # Gesamttest
```

`run.sh` prueft automatisch: X11-Zugriff, Kamera-Bridge-Status, serielle Symlinks, TTY-Flags.

---

## 6. Symlink-Pattern

Skripte leben in `amr/scripts/`, werden als Symlinks in `my_bot/my_bot/` referenziert und via `setup.py` entry_points als `ros2 run my_bot <name>` ausfuehrbar gemacht.

### Neues Skript hinzufuegen (4 Schritte)

1. Skript anlegen: `amr/scripts/<name>.py`
2. Symlink erzeugen: `cd amr/pi5/ros2_ws/src/my_bot/my_bot && ln -s ../../../../../scripts/<name>.py`
3. Entry-Point in `setup.py` ergaenzen: `'<name> = my_bot.<name>:main'`
4. Rebuild: `cd amr/docker && ./run.sh colcon build --packages-select my_bot --symlink-install`

### Entry-Points (29 Executables)

Runtime-Knoten: `odom_to_tf`, `dashboard_bridge`, `cliff_safety_node`, `can_bridge_node`, `hailo_udp_receiver_node`, `hailo_inference_node`, `gemini_semantic_node`, `audio_feedback_node`, `tts_speak_node`, `respeaker_doa_node`, `voice_command_node`

Validierungstests: `encoder_test`, `motor_test`, `pid_tuning`, `kinematic_test`, `imu_test`, `rotation_test`, `straight_drive_test`, `rplidar_test`, `slam_validation`, `nav_test`, `nav_square_test`, `docking_test`, `sensor_test`, `serial_latency_logger`, `aruco_docking`, `can_validation_test`, `cliff_latency_test`, `dashboard_latency_test`

---

## 7. Cliff-Safety und Hindernisstopp

### Datenfluss mit Cliff-Safety (Default)

```
Nav2 controller_server ──→ /nav_cmd_vel ──→ cliff_safety_node ──→ /cmd_vel ──→ Drive-Node
Dashboard Joystick ──→ /dashboard_cmd_vel ──→ cliff_safety_node ──→ /cmd_vel ──→ Drive-Node
Sensor-Node ──→ /cliff ──→ cliff_safety_node (blockiert bei true)
Sensor-Node ──→ /range/front ──→ cliff_safety_node (Stopp < 100 mm, Freigabe > 140 mm)
cliff_safety_node ──→ /audio/play ──→ audio_feedback_node (einmaliger Alarm)
```

**Funktionsweise:**
- Normalbetrieb: Twist-Nachrichten werden an `/cmd_vel` weitergeleitet
- Cliff (`/cliff` = true): Blockiert alle Fahrbefehle, sendet Null-Twist (20 Hz)
- Ultraschall < 100 mm: Blockiert, Freigabe > 140 mm (Hysterese)
- Audio-Alarm (`cliff_alarm`) einmalig bei Blockierung

**Remapping:**
- `dashboard_bridge`: `/cmd_vel` → `/dashboard_cmd_vel` (bei `use_cliff_safety:=True`)
- Nav2: separat konfiguriert auf `/nav_cmd_vel`

### Datenfluss ohne Cliff-Safety

```
Nav2 / Dashboard ──→ /cmd_vel ──→ Drive-Node
```

---

## 8. Vision-Pipeline

```
Host (Python 3.13): host_hailo_runner.py (Hailo-8 YOLOv8 @ 5 Hz)
  → UDP 127.0.0.1:5005 →
Docker (Python 3.10): hailo_udp_receiver_node → /vision/detections
                      gemini_semantic_node (Gemini Cloud) → /vision/semantics
                      tts_speak_node (gTTS) → Audio
```

UDP-Bruecke noetig weil `hailort` nur mit Host-Python 3.13 kompatibel. Dashboard AI-Schalter steuert Broadcast-Gate in Bridge + `/vision/enable` Topic fuer TTS.

---

## 9. Konfigurationsdateien

| Datei | Inhalt |
|---|---|
| `config/nav2_params.yaml` | AMCL (2000 Partikel, diff-drive), BT Navigator, RPP Controller, NavFn Planer |
| `config/mapper_params_online_async.yaml` | SLAM Toolbox Ceres-Solver (SPARSE_NORMAL_CHOLESKY), 0.05 m Aufloesung, 12 m LiDAR-Reichweite |
| `config/amr_camera.yaml` | v4l2_camera: 640x480, YUYV, bgr8 |

---

## 10. QoS-Hinweise

### /cliff: Subscriber-seitig Best-Effort QoS

Der Publisher (Firmware) nutzt Reliable (`rclc_publisher_init_default`). Der Subscriber (`cliff_safety_node`) nutzt Best-Effort, damit er auch bei QoS-Mismatch Nachrichten empfaengt:

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy
qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
self.create_subscription(Bool, "/cliff", self.cliff_callback, qos_sensor)
```

### micro-ROS QoS-Regeln

- **Reliable** (`rclc_publisher_init_default()`): Alle MCU-Publisher (`/odom`, `/imu`, `/battery`, `/cliff`, `/range/front`, `/battery_shutdown`).
- Maximale Nachrichtengroesse: 2048 Bytes (MTU * STREAM_HISTORY).

---

## 11. Linting

```bash
ruff check amr/                    # Python-Lint
ruff format --check amr/           # Python-Format
mypy --config-file mypy.ini        # Type-Check
```

Python-Stil: Zeilenlaenge 100, Python 3.10, Double Quotes, isort-Import-Sortierung (ruff.toml).

---

## 12. Debug- und Diagnosekommandos

```bash
# Topic-Liste und Raten:
ros2 topic list
ros2 topic hz /odom
ros2 topic hz /cliff

# Topic-Inhalt:
ros2 topic echo /odom --once
ros2 topic echo /cliff --qos-reliability best_effort

# TF-Baum:
ros2 run tf2_tools view_frames
ros2 topic echo /tf --once

# Knoten:
ros2 node list
ros2 node info /cliff_safety_node

# micro-ROS Agent Status:
ros2 topic hz /odom   # 20 Hz = Agent + Drive-Node verbunden
```

---

## 13. ReSpeaker DoA/VAD-Knoten (optional)

Pollt Direction-of-Arrival und Voice Activity Detection vom ReSpeaker Mic Array v2.0 (XMOS XVF-3000) via USB Vendor Control Transfers (pyusb) mit 10 Hz.

- `/sound_direction` (`std_msgs/Int32`) — Azimut 0–359 Grad
- `/is_voice` (`std_msgs/Bool`) — Sprache erkannt
- Parameter: `poll_rate_hz` (float, default 10.0)
- Voraussetzungen: ReSpeaker per USB, udev-Regel via `host_setup.sh`, `pyusb` im Docker-Image

---

## 14. Abgrenzung

- Firmware-Details (Dual-Core, ISR, CAN-IDs): `docs/firmware.md`
- Dashboard-Details (Komponenten, Store, Theme): `docs/dashboard.md`
- Systemarchitektur, CAN-Notstopp: `docs/architecture.md`
- Vision-Pipeline: `docs/vision_pipeline.md`
- Serielle Ports (udev): `docs/serial_port_management.md`
- Build und Deployment: `docs/build_and_deploy.md`
- Validierungsskripte: `docs/validation.md`
