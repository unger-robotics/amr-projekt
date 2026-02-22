# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektuebersicht

Bachelorarbeit: Autonomer Mobiler Roboter (AMR) fuer Intralogistik (KLT-Transport). Differentialantrieb-Roboter mit XIAO ESP32-S3 (Low-Level-Steuerung) und Raspberry Pi 5 (Navigation/SLAM) ueber micro-ROS/UART verbunden. Sprache: Deutsch (wissenschaftlicher Stil, keine UTF-8-Umlaute in Markdown-Dateien – ae/oe/ue/ss verwenden).

## Build & Deployment

### ESP32 Firmware (PlatformIO)

```bash
# Im Verzeichnis: amr/esp32_amr_firmware/ (platformio.ini liegt dort)
# PlatformIO-Env: seeed_xiao_esp32s3
pio run                       # Firmware kompilieren
pio run -t upload             # Auf ESP32 flashen (921600 Baud)
pio run -t monitor            # Seriellen Monitor starten (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor kombiniert
```

Wichtige Build-Flags in `platformio.ini`: `-DARDUINO_USB_CDC_ON_BOOT=1` (USB-CDC als Serial), `-I../../hardware` (config.h Include-Pfad). micro-ROS-Konfiguration: `board_microros_transport = serial`, `board_microros_distro = humble`.

### ROS2 via Docker (Raspberry Pi 5)

Der Pi 5 laeuft auf Debian Trixie – ROS2 Humble ist nur via Docker (Ubuntu 22.04) verfuegbar. Basis-Image: `ros:humble-ros-base` (arm64). `osrf/ros:humble-desktop` ist amd64-only. micro-ROS Agent wird aus Source gebaut (kein apt-Paket fuer arm64).

```bash
# Im Verzeichnis: amr/docker/
sudo bash host_setup.sh           # Einmalig: udev-Regeln, Gruppen, X11
docker compose build               # Image bauen (~15-20 Min, danach gecached)
./run.sh                           # Interaktive Container-Shell
./run.sh colcon build --packages-select my_bot --symlink-install  # Workspace bauen
./run.sh ros2 launch my_bot full_stack.launch.py                  # Full-Stack starten
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false   # Nur SLAM
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True # Mit Kamera (ArUco-Docking)
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_nav:=False use_slam:=False use_rviz:=False  # Nur Kamera
./run.sh exec bash                 # Zweites Terminal im laufenden Container
./verify.sh                        # Gesamttest: Image, ROS_DISTRO, Pakete (nav2, slam_toolbox, rplidar, cv_bridge, micro_ros_agent), colcon, Serial-Device, Kamera-Bridge, Workspace-Build, Node-Count
```

Container-Konfiguration: `network_mode: host` (DDS Multicast), `privileged: true` (Serial/Kamera), Volume-Mounts fuer `ros2_ws` (rw), `amr/scripts` (ro, Dual-Mount auf `/amr_scripts` und `/scripts` fuer Symlink-Kompatibilitaet), `hardware/` (ro). Build-Artefakte in Docker-Volumes persistiert. `entrypoint.sh` sourced automatisch alle Workspaces -- kein manuelles `source setup.bash` noetig. `./run.sh exec` erfordert einen bereits laufenden Container (gestartet via `./run.sh` oder `./run.sh ros2 launch ...`). Environment: `ROS_DOMAIN_ID=0`, `DISPLAY=${DISPLAY:-:0}`, `QT_X11_NO_MITSHM=1`, `GEMINI_API_KEY` (aus `amr/docker/.env`, fuer Gemini Semantic Node).

RViz2 benoetigt X11 auf dem Host: `export DISPLAY=:0 && xhost +local:docker`. Alternativ RViz2 auf separatem PC ausfuehren und per ROS2 DDS verbinden (`ROS_DOMAIN_ID=0`).

### ROS2 Workspace (nativ, falls Ubuntu 22.04)

```bash
# Im Verzeichnis: amr/pi5/ros2_ws/
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
ros2 launch my_bot full_stack.launch.py                # Gesamtsystem (micro-ROS + SLAM + Nav2 + RViz2)
ros2 launch my_bot full_stack.launch.py use_nav:=false  # Nur SLAM (ohne Navigation)
ros2 launch my_bot full_stack.launch.py use_rviz:=False # Ohne RViz2
ros2 launch my_bot full_stack.launch.py use_slam:=False # Nur Navigation mit bestehender Karte
ros2 launch my_bot full_stack.launch.py use_camera:=True  # Mit Kamera (ArUco-Docking)
ros2 launch my_bot full_stack.launch.py serial_port:=/dev/ttyUSB0  # Alternativer Serial-Port
ros2 launch my_bot full_stack.launch.py camera_device:=/dev/video10  # Alternatives Kamera-Device
```

### Web Dashboard (optional)

```bash
# Backend starten (im Docker-Container):
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_rviz:=False

# Frontend entwickeln (auf beliebigem Rechner):
cd dashboard && npm install && npm run dev
# Oeffnet http://localhost:5173, WebSocket verbindet zum Pi

# Frontend bauen und als statische Dateien servieren:
cd dashboard && npm run build
python3 -m http.server 3000 -d dashboard/dist/
# Oeffnet http://<PI_IP>:3000 auf iPhone/Tablet/Mac
```

Dashboard-Ports: WebSocket 9090, MJPEG 8082, Vite Dev 5173. Tech-Stack: React 19 + TypeScript + Vite 7.3 + Tailwind CSS 4.2 + nipplejs (Joystick) + Zustand (State-Management). `dashboard_bridge` Node verbindet ROS2 Topics (/odom, /imu, /scan, /camera/image_raw, /map, /tf) mit dem Browser via WebSocket (JSON) und MJPEG (HTTP). Sicherheit: 3-Schicht-Deadman (Frontend 0ms, Backend 300ms, ESP32 500ms), Velocity-Clamping (0.4 m/s, 1.0 rad/s).

WebSocket-Protokoll (Custom JSON, kein rosbridge):
- **Server→Client**: `telemetry` (10 Hz, Odom+IMU+Connection), `scan` (2 Hz, LiDAR-Ranges), `system` (1 Hz, CPU/RAM/Disk/Devices/IP), `map` (0.5 Hz, SLAM-Karte als Base64-PNG + Roboterposition)
- **Client→Server**: `cmd_vel` (Joystick-Steuerung), `heartbeat` (Deadman-Switch)
- Typdefinitionen: `dashboard/src/types/ros.ts` (`ServerMessage = TelemetryMsg | ScanMsg | SystemMsg | MapMsg`)

Komponenten: `Dashboard.tsx` (Layout+WebSocket, responsive: untereinander auf Mobile/Tablet, nebeneinander auf Desktop), `Joystick.tsx` (nipplejs), `LidarView.tsx` (Canvas-Radar + kinematisches Modell: Cyan-Chassis, dunkle Raeder, orange LiDAR-Ring, rote Laser-Emitter, cyan Kamera-FOV, statisch egozentrisch), `MapView.tsx` (allozentrische SLAM-Karte: Base64-PNG auf Canvas, Roboter-Richtungspfeil, Massstabsleiste, HUD-Labels), `CameraView.tsx` (MJPEG+Scanline-Overlay), `StatusPanel.tsx` (Odom/IMU/Connection), `EmergencyStop.tsx` (Nothalt), `SystemMetrics.tsx` (Netzwerk-IP + CPU/RAM/Disk-Balken + ESP32/LiDAR/Kamera/Hailo-Indikatoren). State: `telemetryStore.ts` (Zustand). HUD-Aesthetik: Cyan/Dark-Farbschema, JetBrains Mono, definiert in `index.css` (@theme Block).

### Validierungsskripte (Raspberry Pi)

```bash
# Standalone-Skripte (kein ROS2 noetig):
python3 amr/scripts/pre_flight_check.py    # Interaktive Hardware-Checkliste
python3 amr/scripts/hardware_info.py        # Hardware-Report generieren (Zeitstempel-Markdown, z.B. hardware_info_20260215_180556.md)
python3 amr/scripts/umbmark_analysis.py     # UMBmark-Auswertung (numpy/matplotlib)
python3 amr/scripts/validation_report.py    # Gesamt-Report aus JSON-Ergebnissen

# ROS2-Nodes (micro-ROS Agent muss laufen):
ros2 run my_bot encoder_test      # Encoder-Kalibrierung (10-Umdrehungen-Test)
ros2 run my_bot motor_test        # Motor-Deadzone und Richtungstest
ros2 run my_bot pid_tuning        # PID-Sprungantwort-Analyse
ros2 run my_bot kinematic_test    # Geradeaus-/Dreh-/Kreisfahrt-Verifikation
ros2 run my_bot slam_validation   # ATE-Berechnung und TF-Ketten-Check
ros2 run my_bot nav_test          # Waypoint-Navigation mit Positionsfehler-Messung
ros2 run my_bot docking_test      # 10-Versuch ArUco-Docking-Test
ros2 run my_bot imu_test         # Gyro-Drift und Accelerometer-Bias Test (60s statisch)
ros2 run my_bot rotation_test    # Closed-Loop 360°-Drehung mit IMU-Feedback
ros2 run my_bot straight_drive_test  # Geradeausfahrt mit IMU-Heading-Korrektur
ros2 run my_bot rplidar_test     # RPLidar A1 Scan-Rate, Datenqualitaet, TF-Check (5 min)
```

**Symlink-Muster:** Die ROS2-Nodes erfordern, dass die Skripte aus `amr/scripts/` als Symlinks im Paketverzeichnis `my_bot/my_bot/` liegen (siehe `09_umsetzungsanleitung.md`, Abschnitt 2.2.5). Konkret: `encoder_test.py`, `motor_test.py`, `pid_tuning.py`, `kinematic_test.py`, `slam_validation.py`, `nav_test.py`, `docking_test.py`, `imu_test.py`, `rotation_test.py`, `straight_drive_test.py`, `rplidar_test.py`, `dashboard_bridge.py`, `hailo_inference_node.py`, `gemini_semantic_node.py` und `amr_utils.py` sind Symlinks von `my_bot/my_bot/` → `amr/scripts/`. `aruco_docking.py` ist ein Symlink innerhalb des Pakets (`my_bot/my_bot/` → `my_bot/scripts/`). Nur `odom_to_tf.py` lebt nativ in `my_bot/my_bot/` (kein Symlink).

**Docker Dual-Mount-Pattern:** Die relativen Symlinks (`../../../../../amr/scripts/`) loesen im Container anders auf als auf dem Host. Daher mountet `docker-compose.yml` das Skript-Verzeichnis doppelt: `../scripts:/amr_scripts:ro` und `../scripts:/scripts:ro`. Beide Pfade sind noetig, damit die Symlinks sowohl im Host-Kontext als auch im Container korrekt aufloesen.

### Deployment auf Raspberry Pi

```bash
# Gesamtes Projekt auf den Pi5 synchronisieren (~2-3 MB statt 1.2 GB):
rsync -avz --delete \
  --exclude='.git/' \
  --exclude='.pio/' \
  --exclude='.venv/' \
  --exclude='.DS_Store' \
  --exclude='.claude/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='sources/' \
  --exclude='hardware/media/' \
  --exclude='hardware/datasheet/' \
  --exclude='node_modules/' \
  --exclude='dashboard/dist/' \
  <lokaler-projekt-pfad>/AMR-Bachelorarbeit/ pi@rover:~/AMR-Bachelorarbeit
# Literatur-PDFs herunterladen (virtuelle Umgebung .venv/ im Projekt-Root):
source .venv/bin/activate && python suche/download_sources.py
```

## Architektur

### Dual-Core XIAO ESP32-S3 Firmware (`amr/esp32_amr_firmware/src/`)

Die Firmware partitioniert die Kerne fuer Echtzeit-Garantien:

- **Core 0** (`loop()`): micro-ROS Agent – empfaengt `cmd_vel` (Twist), publiziert `Odometry` (20 Hz), Watchdog-Ueberwachung
- **Core 1** (`controlTask`): PID-Regelschleife bei 50 Hz (20 ms Takt via `vTaskDelayUntil`)
- **Thread-Safety**: FreeRTOS-Mutex (`SharedData`) schuetzt geteilte Daten zwischen den Cores

Datenfluss: `cmd_vel` → inverse Kinematik → PID → Cytron MDD3A (Dual-PWM) → Encoder-Feedback (Hall, Quadratur A+B) → Vorwaertskinematik → Odometrie-Publish

### Firmware-Module (Header-only Pattern)

| Datei | Funktion |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Subscriber/Publisher, Safety-Mechanismen |
| `robot_hal.hpp` | Hardware-Abstraktion: GPIO, Encoder-ISR (Quadratur A+B, Richtung aus Phasenversatz), PWM-Steuerung, Deadzone, LED-MOSFET-PWM |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup, Ausgang [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik (Parameter aus `config.h`) |
| `mpu6050.hpp` | MPU6050 I2C-Treiber (±2g/±250°/s), Gyro-Bias-Kalibrierung, Complementary-Filter |

PID-Gains sind in `main.cpp` hardcoded (Kp=0.4, Ki=0.1, Kd=0.0). EMA-Filter (alpha=0.3) auf Encoder-Geschwindigkeit fuer PID, Rohdaten fuer Odometrie. Beschleunigungsrampe (MAX_ACCEL=5.0 rad/s²) begrenzt Sollwertaenderungen. Dead-Band (0.08) in `driveMotor()` unterdrueckt PID-Rauschen nahe Null, Stillstand-Bypass setzt PID zurueck wenn beide Sollwerte < 0.01. Kommunikation mit dem Pi 5: micro-ROS ueber UART (Serial Transport, USB-CDC, Humble-Distribution).

**LED-Status (D10, IRLZ24N Low-Side MOSFET):** Langsames Blinken = Agent-Suche, schnelles Blinken = Init-Fehler, gedimmt = Setup OK, Heartbeat-Toggle = `loop()` laeuft, Dauer-An = Publish-Fehler.

**Encoder-Hinweis**: Firmware nutzt Quadratur-Dekodierung (Phase A + B). Phase A (D6/D7) als CHANGE-Interrupt, Phase B (D8/D9) fuer Richtungserkennung. 2x-Zaehlung (~748 Ticks/Rev). D8/D9 sind nicht fuer Servos verfuegbar.

### ROS2 Navigation Stack (Raspberry Pi)

Konfiguration in `amr/pi5/ros2_ws/src/my_bot/config/`:

- **nav2_params.yaml**: Nav2-Stack – AMCL, Regulated Pure Pursuit Controller (0.4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors
- **mapper_params_online_async.yaml**: SLAM Toolbox – Ceres-Solver, 5 cm Aufloesung, Loop Closure
- **aruco_docking.py** (`scripts/`): Visual Servoing mit ArUco-Markern (OpenCV `cv2.aruco.ArucoDetector`-API >= 4.7)
- **full_stack.launch.py** (`launch/`): Kombiniertes Launch-File fuer micro-ROS Agent + SLAM + Nav2 + RViz2 + Kamera (optional)
- **package.xml/setup.py/setup.cfg**: ament_python-Paketstruktur mit 16 entry_points (console_scripts): `aruco_docking`, `encoder_test`, `motor_test`, `pid_tuning`, `kinematic_test`, `slam_validation`, `nav_test`, `docking_test`, `imu_test`, `rotation_test`, `straight_drive_test`, `rplidar_test`, `dashboard_bridge`, `odom_to_tf`, `hailo_inference_node`, `gemini_semantic_node` (alle aus `my_bot.<name>:main`)

**Launch-Parameter (vollstaendig):**

| Parameter | Default | Beschreibung |
|---|---|---|
| `use_slam` | True | SLAM Toolbox starten |
| `use_nav` | True | Nav2 Navigation Stack |
| `use_rviz` | True | RViz2 Visualisierung |
| `serial_port` | /dev/ttyACM0 | ESP32 Serial-Port |
| `params_file` | nav2_params.yaml | Nav2 Parameterdatei (Pfad relativ zu config/) |
| `slam_params_file` | mapper_params_online_async.yaml | SLAM Parameterdatei (Pfad relativ zu config/) |
| `use_camera` | False | Kamera und ArUco-Docking aktivieren |
| `camera_device` | /dev/video10 | v4l2loopback-Device fuer Kamera-Bridge |
| `use_dashboard` | False | Web-Dashboard (WebSocket + MJPEG) starten |

### ROS2 Topics und Nodes

| Topic | Typ | Quelle | Beschreibung |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 / Teleop → ESP32 | Geschwindigkeitskommandos |
| `/odom` | `nav_msgs/Odometry` | ESP32 (20 Hz) | Rad-Odometrie |
| `/scan` | `sensor_msgs/LaserScan` | RPLidar A1 | 2D-Laserscan |
| `/camera/image_raw` | `sensor_msgs/Image` | v4l2_camera_node | Kamerabild (optional) |
| `/imu` | `sensor_msgs/Imu` | ESP32 (20 Hz) | IMU-Daten (Beschleunigung, Drehrate, fusionierte Orientierung) |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM Toolbox | Belegungskarte (5 cm Aufloesung, via dashboard_bridge als PNG zum Browser) |
| `/tf`, `/tf_static` | TF2 | odom_to_tf, static_transform_publisher, slam_toolbox | TF-Baum (inkl. map→odom von SLAM) |
| `/vision/detections` | `std_msgs/String` | hailo_inference_node (5 Hz) | JSON-kodierte YOLOv8-Detektionen (Hailo-8) |
| `/vision/semantics` | `std_msgs/String` | gemini_semantic_node | JSON-kodierte semantische Analyse (Gemini Cloud) |

Zentrale Nodes: `micro_ros_agent` (Serial-Bridge), `odom_to_tf` (Odom→TF, siehe TF-Baum), `rplidar_node`, `slam_toolbox`, `nav2` (Lifecycle-Stack), `v4l2_camera_node` (optional), `hailo_inference_node` (Objekterkennung), `gemini_semantic_node` (semantische Analyse, optional).

Debug-Kommandos (im Container via `./run.sh exec bash`): `ros2 topic echo /odom --once`, `ros2 topic hz /scan`, `ros2 run tf2_ros tf2_echo base_link laser`, `ros2 run tf2_ros tf2_echo odom base_link`.

### micro-ROS / XRCE-DDS Constraints

- **MTU-Limit**: `UXR_CONFIG_CUSTOM_TRANSPORT_MTU = 512` Bytes (Standard in micro_ros_platformio). Konfiguration in `.pio/libdeps/seeed_xiao_esp32s3/micro_ros_platformio/libmicroros/include/uxr/client/config.h`.
- **Best-Effort Streams haben KEINE Fragmentierung**. Nachrichten > 512 Bytes schlagen still fehl. `nav_msgs/Odometry` serialisiert ~725 Bytes (2x36 doubles Kovarianz = 576 Bytes).
- **Loesung**: `rclc_publisher_init_default()` (Reliable QoS) statt `rmw_qos_profile_sensor_data` (Best-Effort). Reliable Streams unterstuetzen Fragmentierung (max `MTU * STREAM_HISTORY_OUTPUT` = 512 * 4 = 2048 Bytes).
- **Output-Buffer**: `RMW_UXRCE_MAX_OUTPUT_BUFFER_SIZE = MTU * STREAM_HISTORY_OUTPUT` (2048 Bytes). Konfiguriert in `rmw_microxrcedds_c/config.h`.
- MTU aendern erfordert Neuaufbau der micro-ROS-Libraries (`board_microros_user_meta` in platformio.ini).

### TF-Baum

```
odom → base_link → laser (statisch, 180° Yaw)
  (dynamisch)    → camera_link (statisch, optional bei use_camera:=True)
```

Statische TFs via `static_transform_publisher` im Launch-File:
- **laser**: x=0.10m, y=0.0, z=0.05m, roll=π, pitch=0, yaw=0 (Sensor 180° gedreht montiert)
- **camera_link**: x=0.10m, y=0.0, z=0.08m, roll=0, pitch=0, yaw=0 (nur bei `use_camera:=True`)

Dynamische TF `odom → base_link` wird von `odom_to_tf` erzeugt (`my_bot/odom_to_tf.py`): abonniert `/odom` und broadcastet den entsprechenden TF, da micro-ROS selbst keinen TF publiziert.

### Kamera-Pipeline (IMX296 Global Shutter)

Die Sony IMX296 CSI-Kamera wird ueber eine v4l2loopback-Bridge in den Docker-Container gebracht:

```
IMX296 (CSI) → rpicam-vid (Host) → ffmpeg → /dev/video10 (v4l2loopback) → v4l2_camera_node (Docker/ROS2)
```

- **Host-seitig**: `camera-v4l2-bridge.service` (systemd) startet die Pipeline (`rpicam-vid --codec mjpeg | ffmpeg -f v4l2 -pix_fmt yuyv422 /dev/video10`). Aufloesung: 1456x1088 @ 15fps.
- **Container-seitig**: `v4l2_camera_node` liest `/dev/video10` (YUYV) und publiziert auf `/camera/image_raw`.
- **Setup**: `host_setup.sh` installiert v4l2loopback-dkms, modprobe-Config und den systemd-Service. `run.sh` prueft automatisch ob die Bridge aktiv ist bei `use_camera:=True`.

```bash
# Kamera-Bridge starten/pruefen (Host):
sudo systemctl start camera-v4l2-bridge.service
sudo systemctl status camera-v4l2-bridge.service
v4l2-ctl -d /dev/video10 --all   # Pruefen ob Frames ankommen
```

### Vision-Pipeline (Objekterkennung)

Hybride KI-Pipeline: Lokale Echtzeit-Inference (Hailo-8) + Cloud-Semantik (Google Gemini).

```
/camera/image_raw → [hailo_inference_node] → /vision/detections (JSON)
                            │ Hailo-8 PCIe, YOLOv8s @ 5 Hz       │
                            │ hardware/models/yolov8s.hef          ▼
/camera/image_raw → [gemini_semantic_node] → /vision/semantics (JSON)
                            │ Gemini 3.1 Pro, Rate-Limited 2s
```

- **hailo_inference_node**: Subscribt `/camera/image_raw`, fuehrt YOLOv8-Inference auf Hailo-8 PCIe aus (640x640, COCO 80 Klassen), publiziert Bounding-Boxen als JSON auf `/vision/detections`. Parameter: `model_path`, `confidence_threshold` (0.5), `inference_hz` (5.0).
- **gemini_semantic_node**: Subscribt `/camera/image_raw` + `/vision/detections`, sendet Bild + Detektions-Kontext an Gemini API (`gemini-3.1-pro-preview`), publiziert semantische Beschreibung auf `/vision/semantics`. Benoetigt `GEMINI_API_KEY` Umgebungsvariable. Rate-Limiting: min. 2s zwischen API-Aufrufen.
- **Modell**: YOLOv8s als HEF (Hailo Executable Format), Platzhalter-Pfad `hardware/models/yolov8s.hef`. Kompilierung via Hailo Model Zoo / Dataflow Compiler.
- **Python-Deps** (im Docker): `pip3 install google-generativeai` (Gemini), `hailort` (Hailo-8, auf Pi 5 vorinstalliert).

```bash
# Nodes einzeln starten (Kamera + micro-ROS Agent muessen laufen):
ros2 run my_bot hailo_inference_node
ros2 run my_bot gemini_semantic_node
# Detektionen pruefen:
ros2 topic echo /vision/detections --once
```

### Serial-Port-Management (3 Projekte teilen ESP32)

Der ESP32-Port `/dev/ttyACM0` wird von 3 Projekten geteilt (`selection-panel.service`, `embedded-bridge.service`, AMR Docker). Lockfile: `/var/lock/esp32-serial.lock` (flock-basiert).

**Stabile Device-Pfade (udev):** `host_setup.sh` erstellt udev-Symlinks, die unabhaengig von der USB-Enumerierungsreihenfolge stabil bleiben:
- `/dev/amr_esp32` → XIAO ESP32-S3 (Vendor 303a, Product 1001)
- `/dev/amr_lidar` → RPLIDAR A1 (Vendor 10c4, Product ea60)

```bash
# Vor micro-ROS Agent Start sicherstellen, dass kein anderer Prozess den Port haelt:
sudo systemctl stop embedded-bridge.service   # Falls aktiv
sudo fuser -v /dev/ttyACM0                    # Pruefen ob Port frei
sudo lslocks | grep esp32-serial              # Lock-Status pruefen
```

## Roboter-Parameter

Zentral in `hardware/config.h` definiert (Single Source of Truth). Code-relevante Werte:

- Raddurchmesser: 65.67 mm (kalibriert), Spurbreite: 178 mm, Encoder: ~748 Ticks/Rev (2x Quadratur), PWM-Deadzone: 35
- Zielgeschwindigkeit: 0.4 m/s, Positionstoleranz: 10 cm (xy) / 8° (Gier), Failsafe-Timeout: 500 ms
- LED-Streifen: D10 ueber IRLZ24N MOSFET (PWM-Kanal 4, 5 kHz, 8-bit)

## Firmware-Constraints

- **C++11**: ESP32-Arduino-Toolchain kompiliert mit C++11. Kein `std::clamp` (C++17) – stattdessen `std::max(min, std::min(val, max))`.
- **Typen**: `int32_t`/`uint8_t`/`int16_t` statt `int`/`long` (MISRA-inspiriert). Encoder-Zaehler sind `volatile int32_t`.
- **ISR**: Alle ISR-Funktionen mit `IRAM_ATTR` markieren.
- **Speicher**: Keine dynamische Allokation zur Laufzeit (nur beim Startup).

## Validierung

- Keine automatisierten Unit-Tests – Validierung erfolgt experimentell ueber V-Modell-Phasenplan (Akzeptanzkriterien in `hardware/docs/umsetzungsanleitung.md`, Anhang A)
- 19 Dateien in `amr/scripts/` (17 Skripte + `hardware_info.py` + `amr_utils.py` Shared-Modul, alle `py_compile`-validiert)
- Ergebnisse werden als JSON gespeichert und mit `validation_report.py` zu einem Gesamt-Report aggregiert
- Methoden: UMBmark (Borenstein 1996), PID-Sprungantwort, rosbag2-Aufzeichnung

## Bachelorarbeit (Markdown-Dokument)

Die Arbeit folgt dem V-Modell nach VDI 2206. Expose und Gliederung in `suche/amr_expose_literaturstrategie.md`. 7 Kapitel, ~46.000 Woerter.

### Dateistruktur

Jedes Kapitel existiert in zwei Formen:
- **Kombinierte Datei**: `bachelorarbeit/kapitel_XX_name.md` (z.B. `kapitel_04_systemkonzept.md`)
- **Einzelabschnitte**: `bachelorarbeit/kapitel/XX_Y_name.md` (z.B. `04_2_gesamtsystemarchitektur.md`)

### Schreibkonventionen

- Umlaute als ae, oe, ue, ss (kein UTF-8-Umlaut in Kapitel-Dateien)
- Zitationen: `(vgl. Nachname et al. Jahr, S. X)`
- Gleichungen als Code-Bloecke mit erklaerenden Variablendefinitionen
- Keine Bullet-Point-Listen im Fliesstext – vollstaendige Saetze und Absaetze
- Jeder Abschnitt beginnt mit einem kontextualisierenden Einleitungssatz
- **Dual-File-Regel**: Jede Aenderung muss in BEIDEN Dateien erfolgen – der Einzelabschnitt-Datei UND der kombinierten Kapiteldatei

### Workflow: Kapitel generieren

Kapitel werden mit parallelen Agent-Teams erstellt:
1. Team erstellen (`TeamCreate`) mit N Agents (1 pro Unterabschnitt)
2. Tasks erstellen mit Expose-Vorgaben + zugewiesenen Kernaussagen-Dateien
3. Agents parallel spawnen, jeder schreibt seinen Abschnitt
4. Outputs pruefen und zu kombinierter Kapiteldatei zusammenfuehren
5. Team herunterfahren und aufraeumen

## Literaturverwaltung

Kernaussagen mit Seitenzahlen fuer Zitationen in `sources/kernaussagen/` (16 Dateien + Querverweismatrix `00_Uebersicht_Querverweise.md`). PDFs in `sources/`.

## Wichtige Pfade (nicht offensichtlich)

- `hardware/config.h` – Alle Hardware-Parameter (Single Source of Truth), eingebunden via `-I../../hardware` Build-Flag
- `hardware/docs/umsetzungsanleitung.md` – Schrittweise Inbetriebnahme-Anleitung (v3.0, Docker-basiert)
- `hardware/docs/kalibrierung_anleitung.md` – Encoder-Kalibrierung und UMBmark-Prozedur
- `suche/amr_expose_literaturstrategie.md` – Expose, Gliederung und Literaturstrategie
- `scripts/` (Projekt-Root) – Thesis-Hilfsskripte: `md_to_html_converter.py` (Markdown→HTML), `pdf_splitter.py`/`pdf_splitter_manuell.py` (PDF-Aufteilung, Anleitung in `pdf_splitter_anleitung.md`), `optimize_project_images.sh` (Bildoptimierung), `convert_mov_to_mp4.sh` (Video-Konvertierung) – NICHT verwechseln mit `amr/scripts/` (ROS2-Validierungsskripte)
- `hardware/models/yolov8s.hef` – Vorkompiliertes YOLOv8s-Modell fuer Hailo-8 (Platzhalter, muss via Hailo Model Zoo erstellt werden)

## Projektdokumente (Projektroot)

- `systemdokumentation.md` – Technische Systembeschreibung (~2 DIN-A4-Seiten, Architektur, Hardware, Software, Kommunikation, Navigation, Parameter)
- `benutzerhandbuch.md` – Inbetriebnahme, Bedienung, Troubleshooting (~2 DIN-A4-Seiten, 7 Abschnitte)
- `beamer.md` – Praesentationsfolien (~10 Folien, Pandoc/Beamer-kompatibel, Metropolis-Theme)

## Nicht-getrackte Dateien (.gitignore)

Folgende Muster werden von Git ignoriert: `.venv/`, `.pio/`, `__pycache__/`, `.claude/`, `build/`/`install/`/`log/` (colcon), `*.db3`/`metadata.yaml` (rosbag-Aufzeichnungen), `*_map.pgm`/`*_map.yaml`/`*_map_img.*` (lokal generierte SLAM-Karten), `node_modules/`, `dashboard/dist/` (Frontend-Build), `.vscode/`, `.idea/`, `.DS_Store`.

Nicht getrackt (aber nicht in `.gitignore`): `objekterkennung/` – Konzepte und Planungsdokumente fuer Objekterkennung (Hailo-8 AI Accelerator, Pan-Tilt-System, ReSpeaker Mikrofon-Array, erweiterte Schaltplaene). Die implementierte Vision-Pipeline (`hailo_inference_node`, `gemini_semantic_node`) liegt in `amr/scripts/`.

## Troubleshooting

- **Permission denied auf /dev/ttyACM0**: `sudo usermod -aG dialout $USER` (ab- und wieder anmelden)
- **Docker-Image ohne Cache neu bauen**: `docker compose build --no-cache` (in `amr/docker/`)
- **Docker-Build-Cache loeschen**: `docker volume rm amr-docker_ros2_build amr-docker_ros2_install amr-docker_ros2_log`
- **Odom-Topic leer trotz Session**: XRCE-DDS MTU-Problem – siehe Abschnitt "micro-ROS / XRCE-DDS Constraints".
- **PlatformIO flasht falschen Port**: Auto-Erkennung waehlt `/dev/ttyUSB0` (RPLIDAR) statt ESP32. Fix: `upload_port = /dev/ttyACM0` in `platformio.ini`.
- **Serial-Port belegt**: Siehe Abschnitt "Serial-Port-Management". Kurzfassung: `sudo fuser -v /dev/ttyACM0` und ggf. `sudo systemctl stop embedded-bridge.service`.
- **Kamera nicht erkannt (IMX296)**: `camera_auto_detect=1` erkennt IMX296 nicht automatisch. Explizit `dtoverlay=imx296` in `/boot/firmware/config.txt` unter `[all]` eintragen. Reboot erforderlich. Bei I2C-Fehler -121: CSI-Kabel pruefen (Standard-auf-Mini, Kontakte fest).
- **rpicam-hello statt libcamera-hello**: Debian Trixie / Pi OS Bookworm verwendet `rpicam-hello --list-cameras` statt `libcamera-hello`.
- **ESP32 USB-CDC haengt**: `Serial.setTxTimeoutMs(50)` in `setup()` setzen und `delay(1)` nach `rclc_executor_spin_some()` fuer Buffer-Flush einfuegen.
- **Kamera-Bridge: /dev/video10 fehlt**: `sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1`. Falls Modul mit falschen Optionen geladen: `sudo modprobe -r v4l2loopback` zuerst.
- **Kamera-Bridge-Service haengt**: `journalctl -u camera-v4l2-bridge.service -f` pruefen. Haeufige Ursache: rpicam-vid verliert CSI-Verbindung nach Suspend. Fix: `sudo systemctl restart camera-v4l2-bridge.service`.
- **IMU nicht erkannt (MPU6050)**: WHO_AM_I Register (0x75) gibt nicht 0x68 zurueck. I2C-Verbindung pruefen: SDA=D4, SCL=D5. Pullup-Widerstaende (4.7k Ohm) vorhanden? Wire.begin() erfolgreich?
- **IMU Gyro-Drift hoch**: Kalibrierung laeuft 500 Samples beim Startup. Roboter muss waehrend der ersten ~5s nach Power-On still stehen.
