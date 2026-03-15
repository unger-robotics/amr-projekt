# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kontext

`amr/` ist das technische Kernverzeichnis des amr-projekt-Projekts (Autonomer Mobiler Roboter, Differentialantrieb, KLT-Intralogistik). Uebergeordnete Projektdokumentation, Troubleshooting und Projektarbeit-Konventionen: `../CLAUDE.md`.

**Sprache:** Deutsch, wissenschaftlicher Stil. Keine UTF-8-Umlaute in Markdown — ae/oe/ue/ss verwenden.

## Verzeichnisstruktur

```
amr/
  mcu_firmware/            # Zwei-Node MCU-Firmware (eigene CLAUDE.md)
    drive_node/            # PlatformIO: Antrieb, PID, Odometrie, LED (kein I2C)
    sensor_node/           # PlatformIO: Ultraschall, Cliff, IMU (MPU6050), Batterie (INA260), Servo (PCA9685)
  pi5/ros2_ws/src/my_bot/  # ROS2 Humble ament_python-Paket (Nav2, SLAM, Validierung)
  docker/               # Docker-Setup fuer ROS2 auf Pi 5 (Debian Trixie)
  scripts/              # Validierungsskripte, Runtime-Nodes, Host-Only-Tools
```

## Build-Befehle

### MCU Firmware (Zwei-Node-Architektur)

```bash
# Drive-Node (Antrieb, PID, Odometrie, LED):
cd mcu_firmware/drive_node && pio run -e drive_node                      # Kompilieren
cd mcu_firmware/drive_node && pio run -e drive_node -t upload -t monitor # Upload + Monitor
cd mcu_firmware/drive_node && pio run -e led_test -t upload -t monitor   # MOSFET-Diagnose (~5s)

# Sensor-Node (Ultraschall, Cliff, IMU, Batterie, Servo):
cd mcu_firmware/sensor_node && pio run -e sensor_node                      # Kompilieren
cd mcu_firmware/sensor_node && pio run -e sensor_node -t upload -t monitor # Upload + Monitor
cd mcu_firmware/sensor_node && pio run -e servo_test -t upload -t monitor  # Servo-Kalibrierung
```

Erster Build pro Node: ~15 Min (micro-ROS aus Source). Folgebuilds gecached.

### ROS2 (Docker auf Pi 5)

```bash
cd docker/
sudo bash host_setup.sh                    # Einmalig: udev, Gruppen, Kamera-Bridge
docker compose build                        # Image bauen (~15-20 Min)
./run.sh colcon build --packages-select my_bot --symlink-install
./run.sh ros2 launch my_bot full_stack.launch.py                    # Full-Stack
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false     # Nur SLAM
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_vision:=True use_dashboard:=True use_rviz:=False
./run.sh exec bash                          # Zweites Terminal im Container
./verify.sh                                 # Gesamttest
```

### Dashboard (React)

```bash
cd ../dashboard/
npm install && npm run dev     # Entwicklung (http://localhost:5173)
npm run build                  # Produktion
npx tsc --noEmit               # TypeScript Type-Check
```

### Linting

```bash
ruff check amr/               # Python-Lint
ruff format --check amr/      # Python-Format
mypy --config-file ../mypy.ini # Type-Check
clang-format --dry-run --Werror mcu_firmware/drive_node/src/*.cpp mcu_firmware/drive_node/include/*.hpp mcu_firmware/sensor_node/src/*.cpp mcu_firmware/sensor_node/include/*.hpp
pre-commit run --all-files     # Alle Hooks
```

## Architektur (Big Picture)

### Zwei-Ebenen-System

```
[Drive-Node ESP32-S3]  <-- micro-ROS/UART 921600 (/dev/amr_drive) -->  [Raspberry Pi 5 (Docker)]
  50 Hz PID, Odometrie, LED                                             Navigation, SLAM, Vision
  Kein I2C                                                              Nav2, SLAM Toolbox

[Sensor-Node ESP32-S3] <-- micro-ROS/UART 921600 (/dev/amr_sensor) --> Dashboard, Hailo-8 AI
  IMU (50 Hz), Batterie (2 Hz), Servos                                  /battery_shutdown → Drive-Node
  Ultraschall (10 Hz ISR), Cliff (20 Hz)

[Beide ESP32-S3]       <-- CAN-Bus 1 Mbit/s (can0) -->  can_bridge_node (optional, use_can:=True)
  Dual-Path: Sensor-Daten via CAN parallel zu micro-ROS   Publiziert /imu, /cliff, /range, /battery
```

### MCU Dual-Core (mcu_firmware/)

Beide Nodes (Drive + Sensor) nutzen dasselbe Dual-Core-Pattern:

- **Core 0** (`loop()`): micro-ROS Executor (Publisher/Subscriber), Deferred I2C (nur Sensor-Node)
- **Core 1** (FreeRTOS Task): Echtzeit-Datenerfassung + CAN-Bus-Sends (Drive: 50 Hz PID + Encoder + CAN, Sensor: 50 Hz IMU + 10/20 Hz Ultraschall/Cliff + CAN)
- CAN-Sends laufen in Core 1, damit sie unabhaengig vom micro-ROS Agent funktionieren (`setup()` blockiert bis Agent verbunden)
- Zwei Mutexe: `mutex` (SharedData), `i2c_mutex` (alle I2C-Zugriffe MPU6050/INA260/PCA9685, 5 ms Timeout, nur Sensor-Node)
- **Kritisch:** Kein I2C in Subscriber-Callbacks! Deferred-Pattern verwenden (Callback → RAM struct → loop() → I2C)

### ROS2 Stack (pi5/ros2_ws/src/my_bot/)

Launch-File `full_stack.launch.py` orchestriert: micro_ros_agent → odom_to_tf → rplidar_node → slam_toolbox → Nav2 → RViz2. Optional: v4l2_camera_node, dashboard_bridge, hailo_udp_receiver_node, gemini_semantic_node, can_bridge_node. Cliff-Safety-Multiplexer (`cliff_safety_node`, default an) schaltet `/cmd_vel` bei Cliff-Erkennung auf Null. CAN-Bridge (`can_bridge_node`, `use_can:=True`) publiziert Sensor-Topics via SocketCAN als Alternative zu micro-ROS (select-basiert, ~8% CPU). Audio-Feedback-Node (`audio_feedback_node`, optional) spielt WAV-Dateien via aplay/MAX98357A I2S-Verstaerker. TTS-Speak-Node (`tts_speak_node`, `use_tts:=True`) spricht Gemini-Semantik via gTTS Cloud-Synthese ueber den Lautsprecher (Deutsch, Rate-Limiting 10 s).

TF-Baum: `odom → base_link → laser (180° Yaw) / camera_link (optional) / ultrasonic_link (optional)`

### Symlink-Pattern (scripts/)

Skripte leben in `scripts/`, werden als Symlinks in `my_bot/my_bot/` referenziert und via `setup.py` entry_points als `ros2 run my_bot <name>` ausfuehrbar. Docker `docker-compose.yml` mountet `scripts/` doppelt (`/amr_scripts` + `/scripts`) damit Symlinks in beiden Kontexten aufloesen.

### Vision-Pipeline (Hybrid)

```
Host: host_hailo_runner.py (Python 3.13, Hailo-8 YOLOv8 @ 5 Hz)
  → UDP 127.0.0.1:5005 →
Docker: hailo_udp_receiver_node → /vision/detections
        gemini_semantic_node (Gemini Cloud) → /vision/semantics
```

UDP-Bruecke noetig weil hailort nur mit Host-Python 3.13 kompatibel, ROS2-Container Python 3.10.

## Konfiguration

Jeder Node hat seine eigene Config im lokalen `include/`-Ordner (eingebunden via `-I include`):

- `mcu_firmware/drive_node/include/config_drive.h` (v4.0.0): Antrieb, PID, Kinematik, LED — Namespaces `amr::pid::`, `amr::pwm::`, `amr::kinematics::`, `amr::timing::` (kein I2C, keine Batterie/Servo/IMU)
- `mcu_firmware/sensor_node/include/config_sensors.h` (v3.0.0): Ultraschall-Timing, Cliff, Sensorphysik, IMU, Batterie, Servo, I2C — Namespaces `amr::sensor::`, `amr::imu::`, `amr::battery::`, `amr::servo::`, `amr::i2c::`, `amr::ina260::`

Beide Configs verwenden `inline constexpr` in `amr::`-Namespaces mit `static_assert` Compile-Time-Validierung.

## Keine automatisierten Tests

Validierung erfolgt experimentell ueber ROS2-Nodes auf dem Pi 5 (V-Modell-Phasenplan). Ergebnisse als JSON, aggregiert mit `scripts/validation_report.py`.

## micro-ROS Constraints

- Zwei separate micro-ROS Agents: `/dev/amr_drive` (Drive-Node) und `/dev/amr_sensor` (Sensor-Node), 921600 Baud
- XRCE-DDS MTU = 512 Bytes. Best-Effort hat KEINE Fragmentierung
- Odometrie (~725 Bytes, Drive-Node) MUSS mit Reliable QoS publiziert werden (`rclc_publisher_init_default()`)
- Sensor-Node Topics (`Range`, `Bool`) sind klein genug fuer Best-Effort. `Imu` und `BatteryState` vom Sensor-Node nutzen ebenfalls Reliable QoS
- Nachrichten > 2048 Bytes (MTU * STREAM_HISTORY) sind nicht moeglich
