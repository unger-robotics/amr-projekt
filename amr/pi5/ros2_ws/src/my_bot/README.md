# my_bot

ROS2-Humble-Paket fuer einen autonomen mobilen Roboter (AMR) mit Differentialantrieb: SLAM, Navigation, ArUco-Docking und Hardware-Validierung.

## Abhaengigkeiten

- **ROS2 Humble** (Ubuntu 22.04 nativ oder via Docker auf Pi 5)
- **Nav2** (`nav2_bringup`) -- Navigation Stack mit Regulated Pure Pursuit Controller
- **SLAM Toolbox** (`slam_toolbox`) -- Online Async SLAM mit Ceres-Solver
- **micro-ROS Agent** (`micro_ros_agent`) -- Serial Transport zu zwei XIAO ESP32-S3 (Drive-Node `/dev/amr_drive` + Sensor-Node `/dev/amr_sensor`)
- **RPLIDAR ROS** (`rplidar_ros`) -- Treiber fuer RPLIDAR A1
- **v4l2_camera** -- Kamera-Knoten fuer ArUco-Docking (optional)
- **cv_bridge**, **tf2_ros**, **rclpy**, **std_msgs**, **geometry_msgs**, **sensor_msgs**, **nav_msgs**

## Build

```bash
cd amr/pi5/ros2_ws/
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
```

Bei Verwendung des Docker-Setups (empfohlen auf Pi 5):

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install
```

## Launch

Das zentrale Launch-File `full_stack.launch.py` startet den gesamten AMR-Stack:

```bash
ros2 launch my_bot full_stack.launch.py
```

### Parameter

| Parameter | Default | Beschreibung |
|---|---|---|
| `use_slam` | `True` | SLAM Toolbox (async Modus) starten |
| `use_nav` | `True` | Nav2 Navigation Stack starten |
| `use_rviz` | `False` | RViz2 Visualisierung starten (erfordert X11-Display) |
| `use_camera` | `False` | Kamera-Knoten und camera_link TF starten (ArUco-Docking) |
| `drive_serial_port` | `/dev/amr_drive` | Serieller Port fuer Drive-Node (micro-ROS Agent) |
| `sensor_serial_port` | `/dev/amr_sensor` | Serieller Port fuer Sensor-Node (micro-ROS Agent) |
| `use_sensors` | `True` | Sensor-Node micro-ROS Agent starten |
| `use_dashboard` | `False` | Dashboard (WebSocket :9090, MJPEG :8082) starten |
| `use_vision` | `False` | Vision-Pipeline (Hailo UDP Receiver + Gemini Semantik) starten |
| `use_cliff_safety` | `True` | Cliff-Safety cmd_vel-Multiplexer (Notbremse bei Abgrunderkennung) |
| `use_audio` | `False` | Audio-Feedback-Knoten (WAV-Wiedergabe via aplay/MAX98357A) |
| `use_can` | `False` | CAN-Bus Bridge (Dual-Path) starten |
| `use_tts` | `False` | TTS-Sprachausgabe (gTTS, Deutsch) starten |
| `use_respeaker` | `False` | ReSpeaker DoA-Mikrofon starten |
| `use_voice` | `False` | Sprachsteuerung (ReSpeaker VAD + Gemini Flash STT) |
| `params_file` | `config/nav2_params.yaml` | Nav2-Parameterdatei |
| `slam_params_file` | `config/mapper_params_online_async.yaml` | SLAM-Toolbox-Parameterdatei |
| `camera_device` | `/dev/video10` | Video-Device (v4l2loopback-Bridge) |

### Beispiele

```bash
# Nur SLAM ohne Navigation
ros2 launch my_bot full_stack.launch.py use_nav:=False

# Navigation mit bestehender Karte (ohne SLAM)
ros2 launch my_bot full_stack.launch.py use_slam:=False

# Headless (ohne RViz2)
ros2 launch my_bot full_stack.launch.py use_rviz:=False

# Mit Kamera fuer ArUco-Docking
ros2 launch my_bot full_stack.launch.py use_camera:=True

# Alternative Serial-Ports
ros2 launch my_bot full_stack.launch.py drive_serial_port:=/dev/ttyACM0 sensor_serial_port:=/dev/ttyACM1
```

## Paketstruktur

```
my_bot/
  config/
    nav2_params.yaml                   # Nav2: AMCL, RPP Controller, Costmaps, Recovery
    mapper_params_online_async.yaml    # SLAM Toolbox: Ceres-Solver, 5 cm Aufloesung
    amr_camera.yaml                    # Kamera-Parameter (IMX296, Aufloesung, Framerate)
  launch/
    full_stack.launch.py               # Gesamtsystem (2x micro-ROS Agent + RPLIDAR + SLAM + Nav2 + RViz2 + Kamera)
  my_bot/
    __init__.py
    amr_utils.py                       # Shared Utility-Modul (Symlink) (*)
    odom_to_tf.py                      # Bruecke /odom -> TF (odom -> base_link)
    aruco_docking.py                   # ArUco-Marker Visual Servoing (*)
    audio_feedback_node.py             # Audio-Feedback via aplay/MAX98357A (*)
    can_bridge_node.py                 # CAN-Bus Bridge: SocketCAN -> ROS2 Topics (*)
    can_validation_test.py             # CAN-Bus Validierungstest (*)
    cliff_latency_test.py             # Cliff-Latenz-Messung (*)
    cliff_safety_node.py               # cmd_vel-Multiplexer mit Cliff-Notbremse (*)
    dashboard_bridge.py                # WebSocket/MJPEG Bridge fuer Dashboard (*)
    dashboard_latency_test.py          # Dashboard-Latenz-Messung (*)
    docking_test.py                    # 10-Versuch Docking-Test (*)
    encoder_test.py                    # Encoder-Kalibrierung (*)
    gemini_semantic_node.py            # Gemini Cloud Semantik-Stufe (*)
    hailo_inference_node.py            # Hailo-8L Inferenz-Knoten (*)
    hailo_udp_receiver_node.py         # Hailo UDP Receiver im Container (*)
    imu_test.py                        # Gyro-Drift und Accelerometer-Bias Test (*)
    kinematic_test.py                  # Kinematik-Verifikation (*)
    motor_test.py                      # Motor-Deadzone-Test (*)
    nav_square_test.py                 # Quadratfahrt-Test (*)
    nav_test.py                        # Waypoint-Navigation (*)
    pid_tuning.py                      # PID-Sprungantwort-Analyse (*)
    respeaker_doa_node.py              # ReSpeaker Direction-of-Arrival (*)
    rotation_test.py                   # Rotationstest (*)
    rplidar_test.py                    # RPLIDAR-Funktionstest (*)
    sensor_test.py                     # Sensor-Gesamttest (*)
    serial_latency_logger.py           # Serielle Latenz-Messung (*)
    slam_validation.py                 # ATE und TF-Ketten-Check (*)
    straight_drive_test.py             # Geradeausfahrt-Test (*)
    tts_speak_node.py                  # TTS-Sprachausgabe via gTTS (*)
    voice_command_node.py              # Sprachsteuerung ReSpeaker + Gemini STT (*)
  sounds/
    alert.wav                          # Cliff-Alarm-Ton (880 Hz, 0.5s)
    nav_reached.wav                    # Navigationsziel-erreicht-Ton
    nav_start.wav                      # Navigationsstart-Ton
    startup.wav                        # System-Startup-Ton
  scripts/
    aruco_docking.py                   # Standalone-Version des Docking-Skripts
  package.xml
  setup.py
  setup.cfg
```

(*) Symlinks nach `amr/scripts/`. Gemeinsame Konstanten in `amr_utils.py`.

### Knoten (entry_points)

| Executable | Beschreibung |
|---|---|
| **Runtime-Knoten** | |
| `odom_to_tf` | Wandelt `/odom` (Odometry) in dynamischen TF `odom -> base_link` um |
| `aruco_docking` | Visual Servoing mit ArUco-Markern (State Machine: SEARCHING -> APPROACHING -> DOCKED) |
| `cliff_safety_node` | cmd_vel-Multiplexer mit Cliff-Notbremse (muxed Nav2 + Dashboard) |
| `audio_feedback_node` | WAV-Wiedergabe via aplay/MAX98357A (subscribt /audio/play) |
| `can_bridge_node` | CAN-to-ROS2 Bridge: SocketCAN-Frames zu Sensor-Topics (select-basiert, ~8% CPU) |
| `dashboard_bridge` | WebSocket- (Port 9090) und MJPEG-Bridge (Port 8082) fuer das Dashboard |
| `hailo_inference_node` | Echtzeit-Objekterkennung mit Hailo-8 AI Accelerator (YOLOv8) |
| `hailo_udp_receiver_node` | UDP-Empfaenger fuer Hailo-Detektionen aus Host-Python (Port 5005) |
| `gemini_semantic_node` | Semantische Bildanalyse via Google Gemini API (Cloud-Stufe) |
| `respeaker_doa_node` | ReSpeaker Mic Array v2.0: Direction-of-Arrival und VAD via USB |
| `tts_speak_node` | Text-to-Speech Sprachausgabe fuer Gemini-Semantik (gTTS, Deutsch, Rate-Limiting 10 s) |
| `voice_command_node` | Sprachsteuerung: ReSpeaker VAD → Gemini Flash STT → Intent → `/voice/command` + `/voice/text` |
| **Validierungs-Knoten** | |
| `encoder_test` | Encoder-Kalibrierung: 10-Umdrehungen-Test |
| `motor_test` | Motor-Deadzone und Richtungstest |
| `pid_tuning` | PID-Sprungantwort-Analyse |
| `kinematic_test` | Geradeaus-, Dreh- und Kreisfahrt-Verifikation |
| `slam_validation` | Absolute Trajectory Error (ATE) und TF-Ketten-Check |
| `nav_test` | Waypoint-Navigation mit Positionsfehler-Messung |
| `docking_test` | 10-Versuch ArUco-Docking-Test |
| `imu_test` | Gyro-Drift- und Accelerometer-Bias-Test (60s statisch) |
| `nav_square_test` | Quadrat-Navigationstest (1 m x 1 m) mit Vektornavigation und Sensorfusion |
| `rotation_test` | Closed-Loop Rotation mit IMU-Gyro-Feedback (P-Regler) |
| `straight_drive_test` | Geradeausfahrt-Test (1 m) mit optionaler IMU-Heading-Korrektur |
| `rplidar_test` | RPLidar-Validierung: Scan-Rate, Datenqualitaet, statischer TF-Check |
| `serial_latency_logger` | Serial-Latenz-Logger: ESP32->Pi Transportlatenz via header.stamp (CSV) |
| `can_validation_test` | CAN-Bus Validierung: automatisierte Pruefung aller CAN-Frames (python-can) |
| `sensor_test` | Ultraschall- und Cliff-Sensor-Validierung (8 Tests, interaktiv) |
| `cliff_latency_test` | End-to-End Cliff-Safety-Latenztest (Cliff-Erkennung bis Motorstopp) |
| `dashboard_latency_test` | Bedien- und Leitstandsebene Validierung: Latenz, Telemetrie, Deadman, Notaus |

## Validierungsskripte

Die Validierungs-Knoten (`encoder_test`, `motor_test`, `pid_tuning`, `kinematic_test`, `slam_validation`, `nav_test`, `docking_test`, `imu_test`) setzen einen laufenden micro-ROS Agent fuer den Drive-Node voraus. Ausfuehrung ueber:

```bash
ros2 run my_bot encoder_test
ros2 run my_bot motor_test
ros2 run my_bot imu_test
# usw.
```

Zusaetzliche Standalone-Skripte (ohne ROS2) liegen in `amr/scripts/`:
- `pre_flight_check.py` -- Interaktive Hardware-Checkliste
- `hardware_info/` -- Hardware-Report-Paket (aufrufbar via `python -m hardware_info`)
- `umbmark_analysis.py` -- UMBmark-Auswertung (numpy/matplotlib)
- `validation_report.py` -- Gesamt-Report aus JSON-Ergebnissen

Details zum Validierungsablauf: siehe `docs/validation.md`.

## Lizenz

MIT -- siehe [LICENSE](../../../../LICENSE).
