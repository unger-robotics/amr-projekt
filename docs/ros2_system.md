# ROS2-System

## Zweck

Vollstaendige Referenz fuer Launch-Dateien, Knoten, Topics, TF-Baum, Parameter und Betriebsmodi des AMR-ROS2-Stacks. Alle Angaben sind aus dem Quellcode abgeleitet (`full_stack.launch.py`, Firmware-CLAUDE.md, Skript-Quellen).

## Regel

Topic-Tabellen, TF-Details und Launch-Parameter gehoeren nur in diese Datei.

---

## 1. Knoten-Uebersicht

Alle Knoten werden ueber `full_stack.launch.py` orchestriert. Optionale Knoten sind per Launch-Parameter steuerbar.

| Knoten | Paket | Executable | Aktivierung | Beschreibung |
|---|---|---|---|---|
| `rplidar_node` | `rplidar_ros` | `rplidar_node` | immer | RPLidar A1 Laserscanner, `/dev/ttyUSB0`, 115200 Baud |
| `laser_tf_publisher` | `tf2_ros` | `static_transform_publisher` | immer | Statischer TF `base_link` → `laser` (180° Yaw) |
| `micro_ros_agent_drive` | `micro_ros_agent` | `micro_ros_agent` | immer | Serial-Bridge zum Drive-Node ESP32-S3 (`/dev/amr_drive`) |
| `micro_ros_agent_sensor` | `micro_ros_agent` | `micro_ros_agent` | `use_sensors` | Serial-Bridge zum Sensor-Node ESP32-S3 (`/dev/amr_sensor`) |
| `odom_to_tf` | `my_bot` | `odom_to_tf` | immer | Dynamischer TF `odom` → `base_link` aus `/odom` |
| `slam_toolbox` | `slam_toolbox` | `async_slam_toolbox_node` | `use_slam` | SLAM Toolbox im async Online-Modus |
| Nav2-Stack | `nav2_bringup` | `navigation_launch.py` | `use_nav` | Navigation (RPP Controller, NavFn Planer, 10 Hz) |
| `rviz2` | `rviz2` | `rviz2` | `use_rviz` | Visualisierung (Nav2-Standardansicht) |
| `v4l2_camera_node` | `v4l2_camera` | `v4l2_camera_node` | `use_camera` | Kamera via v4l2loopback-Bridge, 640x480, YUYV→bgr8 |
| `camera_tf_publisher` | `tf2_ros` | `static_transform_publisher` | `use_camera` | Statischer TF `base_link` → `camera_link` |
| `ultrasonic_tf_publisher` | `tf2_ros` | `static_transform_publisher` | `use_sensors` | Statischer TF `base_link` → `ultrasonic_link` |
| `dashboard_bridge` | `my_bot` | `dashboard_bridge` | `use_dashboard` | WebSocket :9090, MJPEG :8082, Telemetrie und Fernsteuerung |
| `hailo_udp_receiver` | `my_bot` | `hailo_udp_receiver_node` | `use_vision` | Empfaengt Hailo-8 Inferenz via UDP 127.0.0.1:5005 |
| `gemini_semantic_node` | `my_bot` | `gemini_semantic_node` | `use_vision` | Gemini-Cloud-Semantik aus Kamerabild und Detektionen |
| `cliff_safety_node` | `my_bot` | `cliff_safety_node` | `use_cliff_safety` | Cliff-Sicherheits-Multiplexer, blockiert `/cmd_vel` bei Abgrund |
| `audio_feedback_node` | `my_bot` | `audio_feedback_node` | `use_audio` | WAV-Wiedergabe via aplay/MAX98357A I2S |
| `can_bridge_node` | `my_bot` | `can_bridge_node` | `use_can` | CAN-Bus Diagnostik (MCP2515/SocketCAN → `/diagnostics/can`) |
| `respeaker_doa_node` | `my_bot` | `respeaker_doa_node` | `use_respeaker` | ReSpeaker Mic Array v2.0 DoA/VAD via USB (pyusb) |

---

## 2. Topic-Tabelle

### 2.1 MCU-Topics (micro-ROS, ESP32-S3)

| Topic | Typ | Rate | QoS | Publisher / Subscriber | Beschreibung |
|---|---|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | 20 Hz | Reliable | Drive-Node (Pub) | Radodometrie, ~725 Bytes, Reliable wg. XRCE-DDS MTU |
| `/imu` | `sensor_msgs/Imu` | 50 Hz | Reliable | Sensor-Node (Pub) | MPU6050 Beschleunigung + Gyroskop |
| `/battery` | `sensor_msgs/BatteryState` | 2 Hz | Reliable | Sensor-Node (Pub) | INA260 Spannung, Strom, Leistung |
| `/battery_shutdown` | `std_msgs/Bool` | Event | Reliable | Sensor-Node (Pub) | Unterspannungs-Notaus (< 9.5 V) |
| `/range/front` | `sensor_msgs/Range` | 10 Hz | Reliable | Sensor-Node (Pub) | HC-SR04 Ultraschall, frame: `ultrasonic_link` |
| `/cliff` | `std_msgs/Bool` | 20 Hz | **Best-Effort** | Sensor-Node (Pub) | MH-B IR Cliff (true = Abgrund erkannt) |
| `/cmd_vel` | `geometry_msgs/Twist` | — | Reliable | Drive-Node (Sub) | Fahrbefehl (linear.x, angular.z) |
| `/servo_cmd` | `geometry_msgs/Point` | — | Reliable | Sensor-Node (Sub) | Servo-Winkel (x=Pan, y=Tilt) |
| `/hardware_cmd` | `geometry_msgs/Point` | — | Reliable | Drive (Sub: x=Motor-Limit, z=LED-PWM), Sensor (Sub: y=Servo-Speed) | Geraetekonfiguration |

### 2.2 Pi-5-Topics (ROS2-Knoten)

| Topic | Typ | Rate | QoS | Publisher / Subscriber | Beschreibung |
|---|---|---|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | ~7.5 Hz | Sensor | rplidar_node (Pub) | RPLidar A1 Laserscandaten |
| `/nav_cmd_vel` | `geometry_msgs/Twist` | — | Reliable | Nav2 controller_server (Pub) | Nav2-Fahrbefehl (nur mit Cliff-Safety aktiv) |
| `/dashboard_cmd_vel` | `geometry_msgs/Twist` | — | Reliable | dashboard_bridge (Pub) | Dashboard-Joystick (nur mit Cliff-Safety aktiv) |
| `/sound_direction` | `std_msgs/Int32` | 10 Hz | Reliable | respeaker_doa_node (Pub) | Azimut 0-359 Grad (Direction of Arrival) |
| `/is_voice` | `std_msgs/Bool` | 10 Hz | Reliable | respeaker_doa_node (Pub) | Sprache erkannt (Voice Activity Detection) |
| `/vision/detections` | `std_msgs/String` | ~5 Hz | Reliable | hailo_udp_receiver (Pub) | Hailo-8 YOLOv8 Objekterkennung (JSON) |
| `/vision/semantics` | `std_msgs/String` | — | Reliable | gemini_semantic_node (Pub) | Gemini-Cloud Szenenbeschreibung (JSON) |
| `/diagnostics/can` | `diagnostic_msgs/DiagnosticArray` | — | Reliable | can_bridge_node (Pub) | CAN-Bus Diagnostik und Frame-Statistiken |
| `/audio/play` | `std_msgs/String` | — | Reliable | cliff_safety_node (Pub), audio_feedback_node (Sub) | WAV-Dateiname fuer Audio-Wiedergabe |
| `/camera/image_raw` | `sensor_msgs/Image` | — | Reliable | v4l2_camera_node (Pub) | Kamerabild 640x480 bgr8 |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | — | Reliable | v4l2_camera_node (Pub) | Kamera-Kalibrierungsdaten |

---

## 3. TF-Baum

```
odom
  └── base_link              (dynamisch, odom_to_tf, aus /odom)
        ├── laser             (statisch, x=0.10, z=0.05, Yaw=180°/pi)
        ├── camera_link       (statisch, x=0.10, z=0.08, optional: use_camera)
        └── ultrasonic_link   (statisch, x=0.15, z=0.10, optional: use_sensors)
```

| Frame | Parent | Typ | Knoten | Bedingung |
|---|---|---|---|---|
| `base_link` | `odom` | dynamisch | `odom_to_tf` | immer |
| `laser` | `base_link` | statisch | `laser_tf_publisher` | immer |
| `camera_link` | `base_link` | statisch | `camera_tf_publisher` | `use_camera:=True` |
| `ultrasonic_link` | `base_link` | statisch | `ultrasonic_tf_publisher` | `use_sensors:=True` |

Der `odom_to_tf`-Knoten subscribt `/odom` (Odometry) und broadcastet den dynamischen Transform `odom` → `base_link`, da micro-ROS keinen eigenen TF-Broadcaster enthaelt.

---

## 4. Launch-Parameter

Alle Parameter fuer `full_stack.launch.py`:

| Parameter | Default | Beschreibung |
|---|---|---|
| `use_slam` | `True` | SLAM Toolbox starten (async Modus) |
| `use_nav` | `True` | Nav2 Navigation Stack starten |
| `use_rviz` | `True` | RViz2 Visualisierung starten |
| `drive_serial_port` | `/dev/amr_drive` | Serieller Port fuer micro-ROS Agent Drive-Node (USB-CDC) |
| `sensor_serial_port` | `/dev/amr_sensor` | Serieller Port fuer micro-ROS Agent Sensor-Node (USB-CDC) |
| `use_sensors` | `True` | Sensor-Node ESP32-S3 (Ultraschall, Cliff) starten |
| `params_file` | `config/nav2_params.yaml` | Pfad zur Nav2 Parameter-YAML-Datei |
| `slam_params_file` | `config/mapper_params_online_async.yaml` | Pfad zur SLAM Toolbox Parameter-YAML-Datei |
| `use_camera` | `False` | Kamera-Knoten starten (v4l2_camera_node fuer ArUco-Docking) |
| `camera_device` | `/dev/video10` | Video-Device fuer die Kamera (v4l2loopback-Bridge) |
| `use_dashboard` | `False` | Web-Dashboard starten (WebSocket :9090, MJPEG :8082) |
| `use_vision` | `False` | Vision-Pipeline starten (Hailo UDP Receiver + Gemini Semantik) |
| `use_cliff_safety` | `True` | Cliff-Safety cmd_vel-Multiplexer aktivieren |
| `use_audio` | `False` | Audio-Feedback-Knoten (MAX98357A I2S) |
| `use_can` | `False` | CAN-Bridge Diagnostik-Knoten (MCP2515/SocketCAN) |
| `use_respeaker` | `False` | ReSpeaker Mic Array v2.0 DoA/VAD-Knoten (USB, pyusb) |

**Beispiele:**

```bash
# Standard (SLAM + Nav2 + RViz2, Cliff-Safety an):
ros2 launch my_bot full_stack.launch.py

# Nur SLAM, ohne Navigation:
ros2 launch my_bot full_stack.launch.py use_nav:=False

# Vollausbau mit optionalen Subsystemen:
ros2 launch my_bot full_stack.launch.py use_camera:=True use_vision:=True use_dashboard:=True use_rviz:=False

# Ohne Sensor-Node und ohne RViz2:
ros2 launch my_bot full_stack.launch.py use_sensors:=False use_rviz:=False
```

---

## 5. Cliff-Safety cmd_vel-Remapping

Der `cliff_safety_node` ist ein Sicherheits-Multiplexer, der Fahrbefehle bei Cliff-Erkennung blockiert. Er ist per Default aktiv (`use_cliff_safety:=True`).

### 5.1 Datenfluss mit Cliff-Safety (Default)

```
Nav2 controller_server ──→ /nav_cmd_vel ──→ cliff_safety_node ──→ /cmd_vel ──→ Drive-Node
Dashboard Joystick ──→ /dashboard_cmd_vel ──→ cliff_safety_node ──→ /cmd_vel ──→ Drive-Node
Sensor-Node ──→ /cliff ──→ cliff_safety_node (blockiert bei true)
cliff_safety_node ──→ /audio/play ──→ audio_feedback_node (einmaliger Alarm)
```

Bei aktiver Cliff-Erkennung (`/cliff` = true):
- Alle Fahrbefehle werden blockiert
- Ein Null-Twist wird mit 20 Hz auf `/cmd_vel` gesendet
- Ein einmaliger Audio-Alarm (`cliff_alarm`) wird auf `/audio/play` publiziert

Bei aufgehobener Cliff-Erkennung (`/cliff` = false):
- Fahrbefehle von `/nav_cmd_vel` und `/dashboard_cmd_vel` werden an `/cmd_vel` weitergeleitet

**Remapping im Launch-File:**
- Der `dashboard_bridge`-Knoten wird per Launch-Remapping von `/cmd_vel` auf `/dashboard_cmd_vel` umgeleitet
- Nav2 muss separat konfiguriert werden, um auf `/nav_cmd_vel` zu publizieren
- Hinweis: In ROS2 Humble ist `SetRemap` nicht verfuegbar (erst ab Iron)

### 5.2 Datenfluss ohne Cliff-Safety

```
Nav2 controller_server ──→ /cmd_vel ──→ Drive-Node
Dashboard Joystick ──→ /cmd_vel ──→ Drive-Node
```

Ohne Cliff-Safety (`use_cliff_safety:=False`) publizieren Nav2 und Dashboard direkt auf `/cmd_vel`. Der `dashboard_bridge`-Knoten wird ohne Remapping gestartet.

---

## 6. ReSpeaker DoA/VAD-Knoten (optional)

Der `respeaker_doa_node` pollt Direction-of-Arrival und Voice Activity Detection vom ReSpeaker Mic Array v2.0 (XMOS XVF-3000) via USB Vendor Control Transfers (pyusb) mit 10 Hz.

**Topics:**
- `/sound_direction` (`std_msgs/Int32`) — Azimut 0-359 Grad
- `/is_voice` (`std_msgs/Bool`) — Sprache erkannt (VAD)

**Parameter:**
- `poll_rate_hz` (float, default 10.0) — Abfragerate

**Start:**
```bash
ros2 launch my_bot full_stack.launch.py use_respeaker:=True
```

**Voraussetzungen:**
- ReSpeaker per USB angeschlossen (Vendor 2886, Product 0018)
- udev-Regel via `host_setup.sh` installiert (USB-Zugriff ohne sudo)
- `pyusb` im Docker-Image (wird automatisch installiert)

---

## 7. QoS-Hinweise

### 7.1 /cliff: Best-Effort QoS

Das Topic `/cliff` wird vom Sensor-Node ESP32-S3 mit **Best-Effort** QoS publiziert. Subscriber muessen die QoS-Policy entsprechend setzen, sonst werden keine Nachrichten empfangen.

**Python-Beispiel:**

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool

qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)

self.create_subscription(Bool, "/cliff", self.cliff_callback, qos_sensor)
```

### 7.2 micro-ROS QoS-Regeln

- **Reliable** (`rclc_publisher_init_default()`): Pflicht fuer Nachrichten > 512 Bytes (XRCE-DDS MTU), da Best-Effort keine Fragmentierung unterstuetzt. Betrifft `/odom` (~725 Bytes), `/imu`, `/battery`.
- **Best-Effort** (`rclc_publisher_init_best_effort()`): Fuer kleine Nachrichten wie `/cliff` (Bool) und `/range/front` (Range).
- Maximale Nachrichtengroesse: 2048 Bytes (MTU * STREAM_HISTORY).

---

## 8. Debug- und Diagnosekommandos

```bash
# Topic-Liste und Raten anzeigen:
ros2 topic list
ros2 topic hz /odom
ros2 topic hz /cliff

# Topic-Inhalt anzeigen:
ros2 topic echo /odom --once
ros2 topic echo /cliff --qos-reliability best_effort

# TF-Baum inspizieren:
ros2 run tf2_tools view_frames
ros2 topic echo /tf --once

# Knoten-Liste:
ros2 node list
ros2 node info /cliff_safety_node

# Nav2-Status:
ros2 topic echo /behavior_tree_log --once

# micro-ROS Agent Status (Drive):
ros2 topic hz /odom   # 20 Hz = Agent + Drive-Node verbunden
```
