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
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_vision:=True use_dashboard:=True use_rviz:=False  # Kamera + Vision + Dashboard
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

Dashboard-Ports: WebSocket 9090, MJPEG 8082, Vite Dev 5173, Hailo UDP 5005. Tech-Stack: React 19 + TypeScript + Vite 7.3 + Tailwind CSS 4.2 + nipplejs (Joystick) + Zustand (State-Management). `dashboard_bridge` Node verbindet ROS2 Topics (/odom, /imu, /scan, /camera/image_raw, /map, /tf, /battery) mit dem Browser via WebSocket (JSON) und MJPEG (HTTP, `ThreadingHTTPServer` fuer parallele Clients — noetig weil Hailo-Runner ebenfalls MJPEG liest). Empfaengt Servo-Befehle vom Browser und publiziert auf `/servo_cmd`. Sicherheit: 3-Schicht-Deadman (Frontend 0ms, Backend 300ms, ESP32 500ms), Velocity-Clamping (0.4 m/s, 1.0 rad/s). Vollstaendige Startanleitung: `Dashboard-Start-Live-Betrieb.md`.

WebSocket-Protokoll (Custom JSON, kein rosbridge):
- **Server→Client**: `telemetry` (10 Hz, Odom+IMU+Battery+Servo+Connection), `scan` (2 Hz, LiDAR-Ranges), `system` (1 Hz, CPU/RAM/Disk/Devices/IP, inkl. INA260-Indikator), `map` (0.5 Hz, SLAM-Karte als Base64-PNG + Roboterposition), `vision_detections` (5 Hz, Hailo-8 BBoxen + Inference-Zeit), `vision_semantics` (0.5 Hz, Gemini-Analyse)
- **Client→Server**: `cmd_vel` (Joystick-Steuerung), `servo_cmd` (Pan/Tilt-Servo, 10 Hz throttled), `heartbeat` (Deadman-Switch)
- Typdefinitionen: `dashboard/src/types/ros.ts` (`ServerMessage = TelemetryMsg | ScanMsg | SystemMsg | MapMsg | VisionDetectionsMsg | VisionSemanticsMsg`, `ClientMessage = CmdVelMsg | HeartbeatMsg | ServoCmdMsg`)

Komponenten: `Dashboard.tsx` (Layout+WebSocket, responsive: untereinander auf Mobile/Tablet, nebeneinander auf Desktop), `Joystick.tsx` (nipplejs), `ServoControl.tsx` (Pan/Tilt-Slider 0-180° mit Zentrieren-Button, sendet `servo_cmd` via WebSocket, 10 Hz throttled), `LidarView.tsx` (Canvas-Radar + kinematisches Modell: Cyan-Chassis, dunkle Raeder, orange LiDAR-Ring, rote Laser-Emitter, cyan Kamera-FOV, statisch egozentrisch), `MapView.tsx` (allozentrische SLAM-Karte im Saugroboter-Stil: hellblau befahrbar, dunkelgrau Waende, schwarz unbekannt; weisser Roboter-Pfad-Trail max 500 Punkte mit 2cm Deduplizierung, weisser Richtungspfeil, gruener Mittelpunkt, Image-Smoothing, weisse Massstabsleiste), `CameraView.tsx` (MJPEG mit CSS `rotate-180` fuer kopfueber montierte Kamera, Scanline-Overlay, Vision-BBox-Overlay mit deutschen Labels, Gemini-Semantik-Streifen am unteren Bildrand), `StatusPanel.tsx` (Odom/IMU/Connection), `EmergencyStop.tsx` (Nothalt), `SystemMetrics.tsx` (Netzwerk-IP + Batterie-Abschnitt: Spannungs-/SOC-Balken mit Farbverlauf rot→gruen, Strom/Leistung, 3S1P-Label + CPU/RAM/Disk-Balken + ESP32/LiDAR/Kamera/Hailo/INA260-Indikatoren + Vision-Section: Inference-Zeit/Det.Hz/Objektanzahl). Hooks (`src/hooks/`): `useWebSocket.ts` (Reconnection-Logik, `sendServoCmd()` mit 10 Hz Throttling), `useJoystick.ts` (nipplejs + cmd_vel-Mapping), `useImageFit.ts` (object-contain Canvas-Positionierung). State: `telemetryStore.ts` (Zustand, inkl. Battery/Servo-Felder). HUD-Aesthetik: Cyan/Dark-Farbschema, JetBrains Mono, definiert in `index.css` (@theme Block).

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

**Symlink-Muster:** Die ROS2-Nodes erfordern, dass die Skripte aus `amr/scripts/` als Symlinks im Paketverzeichnis `my_bot/my_bot/` liegen (siehe `09_umsetzungsanleitung.md`, Abschnitt 2.2.5). Konkret: `encoder_test.py`, `motor_test.py`, `pid_tuning.py`, `kinematic_test.py`, `slam_validation.py`, `nav_test.py`, `docking_test.py`, `imu_test.py`, `rotation_test.py`, `straight_drive_test.py`, `rplidar_test.py`, `dashboard_bridge.py`, `hailo_inference_node.py`, `hailo_udp_receiver_node.py`, `gemini_semantic_node.py` und `amr_utils.py` sind Symlinks von `my_bot/my_bot/` → `amr/scripts/`. `aruco_docking.py` ist ein Symlink innerhalb des Pakets (`my_bot/my_bot/` → `my_bot/scripts/`). Nur `odom_to_tf.py` lebt nativ in `my_bot/my_bot/` (kein Symlink).

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

- **Core 0** (`loop()`): micro-ROS Agent – empfaengt `cmd_vel` (Twist) und `servo_cmd` (Point), publiziert `Odometry` (20 Hz), `Imu` (50 Hz), `BatteryState` (2 Hz, INA260), Watchdog-Ueberwachung
- **Core 1** (`controlTask`): PID-Regelschleife bei 50 Hz (20 ms Takt via `vTaskDelayUntil`), PCA9685-Servo-Rampenaktualisierung (vor Motor-PID)
- **Thread-Safety**: FreeRTOS-Mutex (`SharedData`) schuetzt geteilte Daten zwischen den Cores

Datenfluss: `cmd_vel` → inverse Kinematik → PID → Cytron MDD3A (Dual-PWM) → Encoder-Feedback (Hall, Quadratur A+B) → Vorwaertskinematik → Odometrie-Publish. Servo-Pfad: `servo_cmd` (Point) → Clamping 0-180° → `setTargetAngle()` → `updateRamp()` (Core 1, 50 Hz) → PCA9685 PWM

### Firmware-Module (Header-only Pattern)

| Datei | Funktion |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Odom/IMU/Battery Publisher, `/servo_cmd` Subscriber (Point), INA260/PCA9685 Init, Batterie-Unterspannungsabschaltung |
| `robot_hal.hpp` | Hardware-Abstraktion: GPIO, Encoder-ISR (Quadratur A+B, Richtung aus Phasenversatz), PWM-Steuerung, Deadzone (`amr::pid::deadband_threshold`), LED-MOSFET-PWM |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup und D-Term-Tiefpass (`amr::pid::d_filter_tau`), Ausgang [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik (Parameter via Konstruktor) |
| `mpu6050.hpp` | MPU6050 I2C-Treiber (±2g/±250°/s), Gyro-Bias-Kalibrierung, Komplementaerfilter (`amr::imu::complementary_alpha`) |
| `ina260.hpp` | TI INA260 I2C-Leistungsmonitor: Spannung/Strom/Leistung, Unterspannungs-Alert (`amr::ina260::`) |
| `pca9685.hpp` | NXP PCA9685 I2C-Servo-PWM: `setAngle()`, nicht-blockierende Rampe (`updateRamp()`), `allOff()` Notaus (`amr::servo::`) |

Alle Regelparameter zentral in `hardware/config.h` (Namespaces `amr::pid::`, `amr::pwm::`, `amr::kinematics::` etc.): PID-Gains (Kp=0.4, Ki=0.1, Kd=0.0), EMA-Filter (`ema_alpha=0.3`), Beschleunigungsrampe (`max_accel_rad_s2=5.0`), Dead-Band (`deadband_threshold=0.08`), Stillstand-Bypass (`stillstand_threshold=0.01`). Rohdaten fuer Odometrie, gefilterte Werte fuer PID. Kommunikation mit dem Pi 5: micro-ROS ueber UART (Serial Transport, USB-CDC, Humble-Distribution).

**Batterie-Ueberwachung (INA260):** Bei Packspannung < 9.5 V (`amr::battery::threshold_motor_shutdown_v`): Motoren + Servos werden abgeschaltet (PCA9685 `allOff()`). Hysterese 0.3 V fuer Wiederaktivierung. SOC-Schaetzung per linearer Interpolation. BatteryState-Topic `/battery` @ 2 Hz.

**Servo-Steuerung (PCA9685):** Pan/Tilt-Servos (MG996R) auf Kanaelen 0/1, Mittelstellung (90°) bei Startup. Nicht-blockierende Rampenfahrt (1°/20ms, in `controlTask` Core 1). Fernsteuerung via `/servo_cmd` Topic (Point: x=Pan, y=Tilt, 0-180°). I2C-Bus: 400 kHz, Adressen 0x40 (INA260), 0x41 (PCA9685), 0x68 (MPU6050).

**LED-Status (D10, IRLZ24N Low-Side MOSFET):** Langsames Blinken = Agent-Suche, schnelles Blinken = Init-Fehler, gedimmt = Setup OK, Heartbeat-Toggle = `loop()` laeuft, Dauer-An = Publish-Fehler.

**Encoder-Hinweis**: Firmware nutzt Quadratur-Dekodierung (Phase A + B). Phase A (D6/D7) als CHANGE-Interrupt, Phase B (D8/D9) fuer Richtungserkennung. 2x-Zaehlung (~748 Ticks/Rev). D8/D9 sind nicht fuer Servos verfuegbar.

### ROS2 Navigation Stack (Raspberry Pi)

Konfiguration in `amr/pi5/ros2_ws/src/my_bot/config/`:

- **nav2_params.yaml**: Nav2-Stack – AMCL, Regulated Pure Pursuit Controller (0.4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors
- **mapper_params_online_async.yaml**: SLAM Toolbox – Ceres-Solver, 5 cm Aufloesung, Loop Closure
- **aruco_docking.py** (`scripts/`): Visual Servoing mit ArUco-Markern (OpenCV `cv2.aruco.ArucoDetector`-API >= 4.7)
- **full_stack.launch.py** (`launch/`): Kombiniertes Launch-File fuer micro-ROS Agent + SLAM + Nav2 + RViz2 + Kamera (optional)
- **package.xml/setup.py/setup.cfg**: ament_python-Paketstruktur mit 17 entry_points (console_scripts): `aruco_docking`, `encoder_test`, `motor_test`, `pid_tuning`, `kinematic_test`, `slam_validation`, `nav_test`, `docking_test`, `imu_test`, `rotation_test`, `straight_drive_test`, `rplidar_test`, `dashboard_bridge`, `odom_to_tf`, `hailo_inference_node`, `hailo_udp_receiver_node`, `gemini_semantic_node` (alle aus `my_bot.<name>:main`)

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
| `use_vision` | False | Vision-Pipeline (Hailo UDP Receiver + Gemini Semantik, host_hailo_runner.py separat starten!) |

### ROS2 Topics und Nodes

| Topic | Typ | Quelle | Beschreibung |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 / Teleop / Dashboard → ESP32 | Geschwindigkeitskommandos |
| `/servo_cmd` | `geometry_msgs/Point` | Dashboard-Bridge → ESP32 | Pan/Tilt-Servo-Winkel (x=Pan, y=Tilt, 0-180°) |
| `/odom` | `nav_msgs/Odometry` | ESP32 (20 Hz) | Rad-Odometrie |
| `/scan` | `sensor_msgs/LaserScan` | RPLidar A1 | 2D-Laserscan |
| `/camera/image_raw` | `sensor_msgs/Image` | v4l2_camera_node | Kamerabild (optional) |
| `/imu` | `sensor_msgs/Imu` | ESP32 (20 Hz) | IMU-Daten (Beschleunigung, Drehrate, fusionierte Orientierung) |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM Toolbox | Belegungskarte (5 cm Aufloesung, via dashboard_bridge als PNG zum Browser) |
| `/tf`, `/tf_static` | TF2 | odom_to_tf, static_transform_publisher, slam_toolbox | TF-Baum (inkl. map→odom von SLAM) |
| `/battery` | `sensor_msgs/BatteryState` | ESP32 (2 Hz, INA260) | Packspannung, Strom, SOC-Schaetzung |
| `/vision/detections` | `std_msgs/String` | hailo_udp_receiver_node (5 Hz, via UDP von host_hailo_runner.py) | JSON-kodierte YOLOv8-Detektionen (Hailo-8) |
| `/vision/semantics` | `std_msgs/String` | gemini_semantic_node | JSON-kodierte semantische Analyse (Gemini Cloud) |

Zentrale Nodes (Full-Stack mit Vision+SLAM: 11 ROS2-Nodes + 1 Host-Prozess + 1 ESP32-Node = 13 Komponenten): `micro_ros_agent` (Serial-Bridge), `esp32_bot` (micro-ROS auf ESP32), `odom_to_tf` (Odom→TF, siehe TF-Baum), `rplidar_node`, `slam_toolbox`, `laser_tf_publisher`, `camera_tf_publisher`, `v4l2_camera_node` (optional), `dashboard_bridge` (WebSocket+MJPEG), `hailo_udp_receiver_node` (UDP-Empfaenger fuer Objekterkennung), `gemini_semantic_node` (semantische Analyse, optional), `host_hailo_runner.py` (Host-seitig, kein ROS2). Ohne Vision/Kamera reduziert sich die Anzahl entsprechend. Vollstaendige Komponentenliste: `Dashboard-Start-Live-Betrieb.md`.

Debug-Kommandos (im Container via `./run.sh exec bash`): `ros2 topic echo /odom --once`, `ros2 topic hz /scan`, `ros2 topic echo /battery --once`, `ros2 topic echo /servo_cmd --once`, `ros2 topic pub /servo_cmd geometry_msgs/msg/Point "{x: 45.0, y: 90.0}" --once`, `ros2 run tf2_ros tf2_echo base_link laser`, `ros2 run tf2_ros tf2_echo odom base_link`.

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
- **180°-Drehung**: Kamera ist kopfueber montiert. `/camera/image_raw` liefert das Rohbild (ungedreht). Drehung erfolgt an 3 Stellen: CSS `rotate-180` (Dashboard), `cv2.rotate()` (host_hailo_runner.py vor Inference), `cv2.rotate()` (gemini_semantic_node.py vor API-Aufruf).

```bash
# Kamera-Bridge starten/pruefen (Host):
sudo systemctl start camera-v4l2-bridge.service
sudo systemctl status camera-v4l2-bridge.service
v4l2-ctl -d /dev/video10 --all   # Pruefen ob Frames ankommen
```

### Vision-Pipeline (Objekterkennung)

Hybride KI-Pipeline: Lokale Echtzeit-Inference (Hailo-8) + Cloud-Semantik (Google Gemini). UDP-Bruecke zwischen Host (Python 3.13 + hailort) und Docker-Container (Python 3.10 + ROS2).

```
Host (Python 3.13):                    Docker (Python 3.10, ROS2):

host_hailo_runner.py                   hailo_udp_receiver_node
  │ MJPEG von :8082/stream               │ UDP 0.0.0.0:5005
  │ Hailo-8 YOLOv8 @ 5 Hz                │ Publiziert /vision/detections
  └── UDP 127.0.0.1:5005 ──────────────▶│
                                          ▼
                                   gemini_semantic_node (unveraendert)
                                   dashboard_bridge (unveraendert)
```

- **host_hailo_runner.py** (`amr/scripts/`, Host-seitig, kein ROS2): Liest MJPEG-Stream von `http://127.0.0.1:8082/stream` (dashboard_bridge), dreht Bild 180° (Kamera kopfueber montiert), fuehrt YOLOv8-Inference auf Hailo-8 PCIe aus (640x640, COCO 80 Klassen, 5 Hz), sendet Detektionen mit deutschen Labels (`COCO_LABELS_DE`) als JSON via UDP an `127.0.0.1:5005`. Parameter: `--model` (HEF-Pfad), `--threshold` (0.35), `--fallback` (Dummy-Detektionen ohne Hailo-Hardware).
- **hailo_udp_receiver_node** (Docker/ROS2): Empfaengt JSON-Detektionen via UDP (Port 5005), validiert und publiziert auf `/vision/detections`. Identisches JSON-Schema wie `hailo_inference_node`.
- **hailo_inference_node** (Legacy): Direkter Hailo-8 Zugriff aus dem Container – bleibt als Datei/Entry-Point fuer Rueckwaertskompatibilitaet, wird aber nicht mehr gelauncht.
- **gemini_semantic_node**: Subscribt `/camera/image_raw` + `/vision/detections`, dreht Bild 180° (Kamera kopfueber montiert), verkleinert auf max 640px, sendet an Gemini API (`gemini-2.5-flash`), publiziert Schluesselwort-Analyse auf `/vision/semantics` (z.B. "Gerolsteiner Medium, klare Glasflasche"). Benoetigt `GEMINI_API_KEY` Umgebungsvariable. Rate-Limiting: min. 4s zwischen API-Aufrufen.
- **Modell**: YOLOv8s als HEF (Hailo Executable Format), vorkompiliert aus Hailo Model Zoo v2.11.0 fuer **Hailo-8L** (`hardware/models/yolov8s.hef`, 25 MB, in `.gitignore`). Download: `wget -O hardware/models/yolov8s.hef "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8s.hef"`. **Achtung**: Hailo-8 und Hailo-8L HEFs sind inkompatibel (Device-Arch-Pruefung). Das HEF enthaelt integriertes NMS — Output-Shape `(80, N, 5)` mit `[y_min, x_min, y_max, x_max, confidence]` normalisiert, NICHT das Software-Format `[num_boxes, 84]`. Inference ~36 ms/Frame.
- **Python-Deps**: Docker: `pip3 install google-generativeai` (Gemini). Host: `hailort` + `opencv-python` + `numpy` (auf Pi 5 vorinstalliert).

```bash
# 1. Container: Vision-Pipeline starten (use_dashboard fuer MJPEG noetig):
./run.sh ros2 launch my_bot full_stack.launch.py use_vision:=True use_dashboard:=True use_camera:=True use_rviz:=False use_nav:=False

# 2. Host: Hailo-Runner starten (separates Terminal):
python3 ~/AMR-Bachelorarbeit/amr/scripts/host_hailo_runner.py --model hardware/models/yolov8s.hef
python3 ~/AMR-Bachelorarbeit/amr/scripts/host_hailo_runner.py --fallback   # Ohne Hailo-Hardware

# 3. Container: Detektionen pruefen:
ros2 topic echo /vision/detections --once
ros2 topic hz /vision/detections   # ~5 Hz erwartet
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

Zentral in `hardware/config.h` v2.3.2 definiert (Single Source of Truth, C++-Namespaces statt flache `#define`s). Code-relevante Werte:

- **Kinematik** (`amr::kinematics::`): Raddurchmesser 65.67 mm (kalibriert), Spurbreite 178 mm, Encoder ~748 Ticks/Rev (2x Quadratur)
- **PWM** (`amr::pwm::`): Motor-Deadzone 35, 20 kHz/8-bit (Motoren), 5 kHz/10-bit (LED-Kanal 4)
- **PID** (`amr::pid::`): Kp=0.4, Ki=0.1, Kd=0.0, EMA alpha=0.3, Rampe 5.0 rad/s², Deadband 0.08, D-Term-Tiefpass tau=0.02s
- **Timing** (`amr::timing::`): Regelschleife 50 Hz, Odom 20 Hz, IMU 50 Hz, Batterie 2 Hz, Failsafe 500 ms, Watchdog 50 Zyklen
- **IMU** (`amr::imu::`): Komplementaerfilter alpha=0.98 (98% Gyro), Gyro-Sensitivity 131.0 (±250°/s), 500 Kalibrierproben
- **Batterie** (`amr::battery::`): Samsung INR18650-35E 3S1P, 10.80 V nominal, Warnung 10.0 V, Motor-Shutdown 9.5 V, System-Shutdown 9.0 V
- **Servo** (`amr::servo::`): PCA9685 50 Hz, MG996R 600-2400 µs, Rampe 1°/20ms, Pan=CH0, Tilt=CH1
- **I2C** (`amr::i2c::`): 400 kHz, INA260=0x40, PCA9685=0x41, MPU6050=0x68

## Firmware-Constraints

- **C++11**: ESP32-Arduino-Toolchain kompiliert mit C++11. Kein `std::clamp` (C++17) – stattdessen `std::max(min, std::min(val, max))`.
- **Typen**: `int32_t`/`uint8_t`/`int16_t` statt `int`/`long` (MISRA-inspiriert). Encoder-Zaehler sind `volatile int32_t`.
- **ISR**: Alle ISR-Funktionen mit `IRAM_ATTR` markieren.
- **Speicher**: Keine dynamische Allokation zur Laufzeit (nur beim Startup).

## Validierung

- Keine automatisierten Unit-Tests – Validierung erfolgt experimentell ueber V-Modell-Phasenplan (Akzeptanzkriterien in `hardware/docs/umsetzungsanleitung.md`, Anhang A)
- 21 Dateien in `amr/scripts/` (18 Skripte + `host_hailo_runner.py` Host-Skript + `hardware_info.py` + `amr_utils.py` Shared-Modul, alle `py_compile`-validiert)
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

- `hardware/config.h` – Alle Hardware-Parameter (Single Source of Truth, v2.3.2, C++-Namespaces `amr::*`), eingebunden via `-I../../hardware` Build-Flag
- `hardware/docs/umsetzungsanleitung.md` – Schrittweise Inbetriebnahme-Anleitung (v3.0, Docker-basiert)
- `hardware/docs/kalibrierung_anleitung.md` – Encoder-Kalibrierung und UMBmark-Prozedur
- `suche/amr_expose_literaturstrategie.md` – Expose, Gliederung und Literaturstrategie
- `scripts/` (Projekt-Root) – Thesis-Hilfsskripte: `md_to_html_converter.py` (Markdown→HTML), `pdf_splitter.py`/`pdf_splitter_manuell.py` (PDF-Aufteilung, Anleitung in `pdf_splitter_anleitung.md`), `optimize_project_images.sh` (Bildoptimierung), `convert_mov_to_mp4.sh` (Video-Konvertierung) – NICHT verwechseln mit `amr/scripts/` (ROS2-Validierungsskripte)
- `hardware/models/yolov8s.hef` – Vorkompiliertes YOLOv8s-Modell fuer Hailo-8L (aus Hailo Model Zoo v2.11.0, 25 MB, in `.gitignore`)
- `Dashboard-Start-Live-Betrieb.md` – Vollstaendige Startanleitung fuer Dashboard + Vision + SLAM Live-Betrieb (3 Terminals, 13 Komponenten, Reihenfolge, Troubleshooting)

## Projektdokumente (Projektroot)

- `systemdokumentation.md` – Technische Systembeschreibung (~2 DIN-A4-Seiten, Architektur, Hardware, Software, Kommunikation, Navigation, Parameter)
- `benutzerhandbuch.md` – Inbetriebnahme, Bedienung, Troubleshooting (~2 DIN-A4-Seiten, 7 Abschnitte)
- `beamer.md` – Praesentationsfolien (~10 Folien, Pandoc/Beamer-kompatibel, Metropolis-Theme)
- `reproduzierbarkeit.md` – Reproduzierbarkeitsanleitung (Hardware-Stueckliste, Software-Setup, Kalibrierung)
- `abschlussbericht.md` – Abschlussbericht der Bachelorarbeit
- `validierung_todo.md` – Validierungs-Checkliste (offene und abgeschlossene Testpunkte)

## Nicht-getrackte Dateien (.gitignore)

Folgende Muster werden von Git ignoriert: `.venv/`, `.pio/`, `__pycache__/`, `.claude/`, `build/`/`install/`/`log/` (colcon), `*.db3`/`metadata.yaml` (rosbag-Aufzeichnungen), `*_map.pgm`/`*_map.yaml`/`*_map_img.*` (lokal generierte SLAM-Karten), `node_modules/`, `dashboard/dist/` (Frontend-Build), `.vscode/`, `.idea/`, `.DS_Store`, `amr/docker/.env` (Secrets), `*.log` (Log-Dateien), `gstshark_*/` (Profiling-Daten).

`objekterkennung/` ist getrackt: Konzepte und Planungsdokumente fuer Objekterkennung (Hailo-8 AI Accelerator, Pan-Tilt-System, ReSpeaker Mikrofon-Array, Datenblaetter, Rechnungen, TikZ-Diagramme, 16 Komponentendokus in `objekterkennung/docs/`). Die implementierte Vision-Pipeline (`hailo_udp_receiver_node`, `host_hailo_runner.py`, `hailo_inference_node` Legacy, `gemini_semantic_node`) liegt in `amr/scripts/`.

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
- **INA260 nicht erkannt**: Manufacturer-ID (0xFE) gibt nicht 0x5449 zurueck. I2C-Adresse pruefen: Default 0x40 (A0=GND, A1=GND). `i2cdetect -y 1` auf dem ESP32 nicht verfuegbar — stattdessen Serial-Monitor-Output pruefen.
- **PCA9685 Prescaler falsch**: Prescaler-Verifizierung in `init()` schlaegt fehl. PCA9685 muss im Sleep-Modus sein vor Prescaler-Aenderung. Bei Loetbruecke A0 offen: Adresse ist 0x40 (Kollision mit INA260!) — A0 muss geschlossen sein fuer 0x41.
- **Servos zittern**: MG996R brummt am Endanschlag. Sicheren Pulsbereich (600-2400 µs) einhalten. `pca9685.allOff()` bei Nichtgebrauch aufrufen.
- **Batterie-Shutdown zu frueh**: `threshold_motor_shutdown_v` (9.5 V) evtl. zu hoch bei hohem Strom (Spannungseinbruch durch Pack-Impedanz 183 mOhm). INA260-Spannung unter Last pruefen: `ros2 topic echo /battery --once`.
