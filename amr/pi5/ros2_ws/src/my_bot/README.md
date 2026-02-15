# my_bot

ROS2-Humble-Paket fuer einen autonomen mobilen Roboter (AMR) mit Differentialantrieb: SLAM, Navigation, ArUco-Docking und Hardware-Validierung.

## Abhaengigkeiten

- **ROS2 Humble** (Ubuntu 22.04 nativ oder via Docker auf Pi 5)
- **Nav2** (`nav2_bringup`) -- Navigation Stack mit Regulated Pure Pursuit Controller
- **SLAM Toolbox** (`slam_toolbox`) -- Online Async SLAM mit Ceres-Solver
- **micro-ROS Agent** (`micro_ros_agent`) -- Serial Transport zum XIAO ESP32-S3
- **RPLIDAR ROS** (`rplidar_ros`) -- Treiber fuer RPLIDAR A1
- **v4l2_camera** -- Kamera-Node fuer ArUco-Docking (optional)
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
| `use_rviz` | `True` | RViz2 Visualisierung starten |
| `use_camera` | `False` | Kamera-Node und camera_link TF starten (ArUco-Docking) |
| `serial_port` | `/dev/ttyACM0` | Serieller Port fuer micro-ROS Agent |
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

# Alternativer Serial-Port
ros2 launch my_bot full_stack.launch.py serial_port:=/dev/ttyUSB0
```

## Paketstruktur

```
my_bot/
  config/
    nav2_params.yaml                   # Nav2: AMCL, RPP Controller, Costmaps, Recovery
    mapper_params_online_async.yaml    # SLAM Toolbox: Ceres-Solver, 5 cm Aufloesung
  launch/
    full_stack.launch.py               # Gesamtsystem (micro-ROS + RPLIDAR + SLAM + Nav2 + RViz2 + Kamera)
  my_bot/
    __init__.py
    amr_utils.py                       # Shared Utility-Modul (Symlink -> amr/scripts/amr_utils.py) (*)
    odom_to_tf.py                      # Bruecke /odom -> TF (odom -> base_link)
    aruco_docking.py                   # ArUco-Marker Visual Servoing (*)
    encoder_test.py                    # Encoder-Kalibrierung (*)
    motor_test.py                      # Motor-Deadzone-Test (*)
    pid_tuning.py                      # PID-Sprungantwort-Analyse (*)
    kinematic_test.py                  # Kinematik-Verifikation (*)
    slam_validation.py                 # ATE und TF-Ketten-Check (*)
    nav_test.py                        # Waypoint-Navigation (*)
    docking_test.py                    # 10-Versuch Docking-Test (*)
  scripts/
    aruco_docking.py                   # Standalone-Version des Docking-Skripts
  package.xml
  setup.py
  setup.cfg
```

(*) Symlinks nach `amr/scripts/`. Gemeinsame Konstanten in `amr_utils.py`.

### Nodes (entry_points)

| Executable | Beschreibung |
|---|---|
| `odom_to_tf` | Wandelt `/odom` (Odometry) in dynamischen TF `odom -> base_link` um |
| `aruco_docking` | Visual Servoing mit ArUco-Markern (State Machine: SEARCHING -> APPROACHING -> DOCKED) |
| `encoder_test` | Encoder-Kalibrierung: 10-Umdrehungen-Test |
| `motor_test` | Motor-Deadzone und Richtungstest |
| `pid_tuning` | PID-Sprungantwort-Analyse |
| `kinematic_test` | Geradeaus-, Dreh- und Kreisfahrt-Verifikation |
| `slam_validation` | Absolute Trajectory Error (ATE) und TF-Ketten-Check |
| `nav_test` | Waypoint-Navigation mit Positionsfehler-Messung |
| `docking_test` | 10-Versuch ArUco-Docking-Test |

## Validierungsskripte

Die Validierungs-Nodes (`encoder_test`, `motor_test`, `pid_tuning`, `kinematic_test`, `slam_validation`, `nav_test`, `docking_test`) setzen einen laufenden micro-ROS Agent voraus. Ausfuehrung ueber:

```bash
ros2 run my_bot encoder_test
ros2 run my_bot motor_test
# usw.
```

Zusaetzliche Standalone-Skripte (ohne ROS2) liegen in `amr/scripts/`:
- `pre_flight_check.py` -- Interaktive Hardware-Checkliste
- `hardware_info.py` -- Hardware-Info-Report (Systemdaten sammeln)
- `umbmark_analysis.py` -- UMBmark-Auswertung (numpy/matplotlib)
- `validation_report.py` -- Gesamt-Report aus JSON-Ergebnissen

Details zum Validierungsablauf: siehe `hardware/docs/umsetzungsanleitung.md`, Anhang A.

## Lizenz

MIT -- siehe [LICENSE](../../../../LICENSE).
