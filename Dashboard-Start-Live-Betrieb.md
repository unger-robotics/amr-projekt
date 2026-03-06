# Dashboard + Vision + SLAM: Live-Betrieb Startanleitung

Vollstaendige Startsequenz fuer das Dashboard mit SLAM-Kartierung, Kamera, Hailo-8L Objekterkennung und Gemini-Semantik. Die Einhaltung der Startreihenfolge ist kritisch, da die ESP32-Mikrocontroller keine eigenstaendige Reconnection-Logik besitzen.

**Netzwerk-Konfiguration:**
* **Ports:** WebSocket 9090, MJPEG 8082, Vite 5173, Hailo UDP 5005
* **URL:** http://192.168.1.24:5173

## 1. Systemuebersicht

Das System besteht im Live-Betrieb aus bis zu 18 interagierenden Komponenten: 13 ROS2-Nodes und 2 micro-ROS-Agents im Docker-Container, 1 Host-Prozess (Hailo-Runner), 2 ESP32 micro-ROS Nodes (Drive und Sensor) sowie 1 Host-Service fuer die Kamera-Bridge.

### 1.1 Komponentenliste

| #  | Komponente                 | Typ               | Funktion                                                            |
|----|----------------------------|-------------------|---------------------------------------------------------------------|
| 1  | `rplidar_node`             | Container-Node    | RPLidar A1 LiDAR-Scanner (10 Hz)                                    |
| 2  | `laser_tf_publisher`       | Container-Node    | Statischer TF: base_link -> laser                                   |
| 3  | `camera_tf_publisher`      | Container-Node    | Statischer TF: base_link -> camera_link                             |
| 4  | `ultrasonic_tf_publisher`  | Container-Node    | Statischer TF: base_link -> ultrasonic_link (bei `use_sensors`)     |
| 5  | `micro_ros_agent` (drive)  | Container-Prozess | Serial-Bridge Drive-Node <-> ROS2 (`/dev/ttyACM1`)                  |
| 6  | `micro_ros_agent` (sensor) | Container-Prozess | Serial-Bridge Sensor-Node <-> ROS2 (`/dev/ttyACM0`)                 |
| 7  | `odom_to_tf`               | Container-Node    | Odometrie -> TF-Broadcast (odom -> base_link)                       |
| 8  | `slam_toolbox`             | Container-Node    | Async SLAM (Ceres-Solver, 5 cm Aufloesung)                         |
| 9  | `v4l2_camera_node`         | Container-Node    | IMX296 Kamera via v4l2loopback (640x480, 15 fps, bgr8)             |
| 10 | `dashboard_bridge`         | Container-Node    | WebSocket (JSON) + MJPEG-Server (HTTP)                              |
| 11 | `hailo_udp_receiver`       | Container-Node    | UDP-Empfaenger -> `/vision/detections`                              |
| 12 | `gemini_semantic_node`     | Container-Node    | Gemini Cloud-Analyse (gemini-3-flash-preview) -> `/vision/semantics`|
| 13 | `cliff_safety_node`        | Container-Node    | cmd_vel-Multiplexer mit Cliff-Notbremse (bei `use_cliff_safety`)   |
| 14 | `audio_feedback_node`      | Container-Node    | WAV-Wiedergabe via aplay/MAX98357A (bei `use_audio`)               |
| 15 | `drive_node`               | ESP32 micro-ROS   | Odom (20 Hz), cmd_vel, PID, LED, Motor-Limit                       |
| 16 | `sensor_node`              | ESP32 micro-ROS   | Ultraschall (10 Hz), Cliff (20 Hz), IMU, Batterie, Servo           |
| 17 | `host_hailo_runner.py`     | Host-Prozess      | YOLOv8 Inference auf Hailo-8L (5 Hz, ~34 ms)                       |
| 18 | `camera-v4l2-bridge`       | Host-Service      | rpicam-vid (640x480) -> ffmpeg -> /dev/video10                      |

### 1.2 Datenfluss und Schnittstellen-Status

| #  | Komponente                | Schnittstelle / Port             | Erwarteter Status                            |
|----|---------------------------|----------------------------------|----------------------------------------------|
| 1  | micro_ros_agent_drive     | `/dev/ttyACM1` (Serial)          | session established                          |
| 2  | micro_ros_agent_sensor    | `/dev/ttyACM0` (Serial)          | session established                          |
| 3  | drive_node (ESP32-S3)     | Serial E8:06:90:9D:9B:A0        | 1 Publisher (odom), 3 Subscriber             |
| 4  | sensor_node (ESP32-S3)    | Serial 98:3D:AE:EA:08:1C        | 2+ Publisher (range, cliff), 3 Subscriber    |
| 5  | rplidar_node              | /dev/ttyUSB0                     | Sensitivity-Modus, 10 Hz                     |
| 6  | odom_to_tf                | ROS2 intern (TF)                 | aktiv                                        |
| 7  | slam_toolbox              | ROS2 intern (TF/Topics)          | Registering sensor                           |
| 8  | v4l2_camera_node          | `/dev/video10`                   | YUYV @ 640x480                               |
| 9  | laser_tf_publisher        | ROS2 intern (TF)                 | base_link -> laser                           |
| 10 | camera_tf_publisher       | ROS2 intern (TF)                 | base_link -> camera_link                     |
| 11 | ultrasonic_tf_publisher   | ROS2 intern (TF)                 | base_link -> ultrasonic_link                 |
| 12 | dashboard_bridge          | TCP 9090 (WS), TCP 8082 (MJPEG)  | WS :9090 + MJPEG :8082                       |
| 13 | hailo_udp_receiver        | UDP 5005                         | UDP :5005                                    |
| 14 | gemini_semantic_node      | Cloud API (HTTPS)                | gemini-3-flash-preview                       |
| 15 | host_hailo_runner         | Liest TCP 8082, sendet UDP 5005  | ~34 ms/Frame                                 |
| 16 | Frontend                  | TCP 5173 (HTTP)                  | http://192.168.1.24:5173                     |

---

## 2. Voraussetzungen

* HEF-Modell fuer Edge-KI vorhanden: `hardware/models/yolov8s.hef`.
* Umgebungsvariable `GEMINI_API_KEY` ist in der Datei `amr/docker/.env` gesetzt.
* Das Docker-Image ist aktuell (`docker compose build`), sodass das `google-genai` SDK integriert ist.
* Kein anderer Host-Dienst blockiert die ESP32-Ports `/dev/ttyACM0` und `/dev/ttyACM1`.
* **Drive-Node Firmware korrekt geflasht** (NICHT `led_test`!). Pruefen: `timeout 3 cat /dev/amr_drive | od -A x -t x1z | head -3` — binaere XRCE-DDS-Daten (0x7e Header) = OK. Text-Ausgabe wie `duty= 255/1023` = LED-Test-Firmware! Fix: `cd amr/mcu_firmware/drive_node && pio run -e drive_node -t upload`.

---

## 3. Startsequenz (Benoetigt 3 Terminals)

### Terminal 1: System-Reset und Docker Full-Stack

Im ersten Terminal bereiten wir die Hardware vor und starten den Container.

```bash
# 1. Alte Container und Ports freigeben
docker stop $(docker ps -q) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp 2>/dev/null
sudo systemctl stop embedded-bridge.service selection-panel.service 2>/dev/null

# 2. Kamera-Bridge pruefen/starten
sudo systemctl is-active camera-v4l2-bridge.service || {
    sudo modprobe -r v4l2loopback 2>/dev/null
    sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1
    sudo systemctl restart camera-v4l2-bridge.service
    sleep 4
}

# 3. Hardware-Reset beider ESP32 via DTR/RTS
# Zwingt die Boards in eine Ping-Schleife, um auf den micro-ROS Agent zu warten
python3 -c "
import serial, time
for port in ['/dev/ttyACM0', '/dev/ttyACM1']:
    try:
        s = serial.Serial(port, 115200)
        s.setDTR(False); s.setRTS(True); time.sleep(0.1)
        s.setDTR(True); s.setRTS(False); time.sleep(0.05)
        s.setDTR(False); s.close()
        print(f'{port} Reset OK')
    except Exception as e:
        print(f'{port} Reset FEHLER: {e}')
"

# 4. Docker Full-Stack starten (13 Nodes + 2 micro_ros_agents)
# WICHTIG: Physische Device-Pfade verwenden — udev-Symlinks existieren nicht im Container!
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_slam:=True use_dashboard:=True use_camera:=True use_vision:=True \
    use_rviz:=False use_nav:=False \
    drive_serial_port:=/dev/ttyACM1 sensor_serial_port:=/dev/ttyACM0

```

**Erfolgreicher Start in Terminal 1 zeigt:**

* `[micro_ros_agent_drive]` -> `session established` (Drive-ESP32 verbunden)
* `[micro_ros_agent_sensor]` -> `session established` (Sensor-ESP32 verbunden)
* `[slam_toolbox]` -> `Registering sensor` (LiDAR erkannt, odom->base_link TF vorhanden)
* `[dashboard_bridge]` -> `WebSocket-Server gestartet` + `MJPEG-Server gestartet`
* `[gemini_semantic_node]` -> `Gemini-Modell konfiguriert: gemini-3-flash-preview`
* `[hailo_udp_receiver]` -> `warte auf host_hailo_runner.py`

### Terminal 2: Edge-KI Host-Prozess (Hailo-Runner)

Startet die latenzarme Bildverarbeitung direkt auf dem Raspberry Pi Host (ausserhalb von ROS 2).

```bash
cd ~/AMR-Bachelorarbeit
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py \
    --model hardware/models/yolov8s.hef --threshold 0.35

```

**Erwartete Ausgabe:**

```text
=== Hailo-8 Host Runner ===
[HAILO] Lade Modell: .../yolov8s.hef
[HAILO] Initialisiert: 1 Input(s), 1 Output(s)
[HAILO] MJPEG-Stream verbunden (Versuch 1)
[HAILO] 2 Objekt(e) in 34.1 ms: Koffer, Stuhl

```

Der Runner verbindet sich automatisch mit dem MJPEG-Stream der `dashboard_bridge` und unternimmt bis zu 10 Versuche mit Backoff, falls die Bridge noch nicht bereit ist. (Nutze `--fallback` anstelle von `--model`, falls keine Hailo-Hardware angeschlossen ist).

### Terminal 3: Dashboard-Frontend (Vite)

```bash
cd ~/AMR-Bachelorarbeit/dashboard
npm run dev -- --host

```

Das Dashboard ist nun unter http://192.168.1.24:5173 auf Mobilgeraeten oder im Browser erreichbar. (Fuer den statischen Produktivbetrieb: `python3 -m http.server 3000 -d ~/AMR-Bachelorarbeit/dashboard/dist/` nach einem `npm run build`).

---

## 4. Verifikation

Nach dem Start aller 3 Terminals im Container pruefen (zweites Terminal: `./run.sh exec bash`):

```bash
# Topic-Liste (erwartete Kern-Topics)
ros2 topic list --no-daemon
# /odom, /scan, /range/front, /cliff, /cmd_vel, /map, /vision/detections, /camera/image_raw

# Odom-Rate (Drive-Node, erwartet ~17-20 Hz)
timeout 5 ros2 topic hz /odom

# LiDAR-Rate (erwartet ~7.5 Hz)
timeout 5 ros2 topic hz /scan

# Odom-Daten pruefen
ros2 topic echo /odom --once --no-daemon

# Vision-Detektionen (erwartet nach Hailo-Runner-Start)
ros2 topic echo /vision/detections --once --no-daemon
```

---

## 5. System herunterfahren

1. **Terminal 2 & 3:** Prozesse mit `Ctrl+C` beenden.
2. **Terminal 1:** ROS2-Launch mit `Ctrl+C` beenden.
3. **Ports bereinigen:**

```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp

```

---

## 6. Einmalige Vorbereitung: HEF-Modell herunterladen

Falls das YOLOv8-Modell fuer den Beschleuniger noch fehlt:

```bash
mkdir -p hardware/models
wget -O hardware/models/yolov8s.hef \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8s.hef"

```

---

## 7. Troubleshooting

### micro_ros_agent: "running..." aber kein "session established"

**Ursache 1: LED-Test-Firmware auf Drive-ESP32.** `pio run -t upload` (ohne `-e`) flasht das letzte Environment (`led_test`), nicht `drive_node`! Serieller Output zeigt `duty= 255/1023` statt binaerer XRCE-DDS-Daten.
* **Fix:** `cd amr/mcu_firmware/drive_node && pio run -e drive_node -t upload` (immer `-e drive_node` angeben!)

**Ursache 2: ESP32 im falschen Zustand.** Nach Container-Neustart ohne Reset wartet der ESP32 nicht mehr auf den Agent.
* **Fix:** DTR/RTS-Reset ausfuehren (Schritt 3 in Terminal 1), DANN Container starten.

### SLAM: "Message Filter dropping message"

SLAM Toolbox verwirft Laser-Scans wenn der TF `odom -> base_link` fehlt. Das passiert wenn der Drive-Node nicht verbunden ist (kein `/odom` -> kein TF).
* **Fix:** Drive-Node Verbindung pruefen: `ros2 topic echo /odom --once --no-daemon`. Falls leer: ESP32-Reset + Firmware pruefen.

### Docker: "/dev/amr_drive not found"

udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) existieren nur auf dem Host, NICHT im Container.
* **Fix:** Physische Pfade als Launch-Argumente verwenden: `drive_serial_port:=/dev/ttyACM1 sensor_serial_port:=/dev/ttyACM0`

### Hailo: "HAILO_OUT_OF_PHYSICAL_DEVICES"

Ein alter Runner-Prozess haelt das Hailo-Device belegt.
* **Fix:** `pkill -f host_hailo_runner` und erneut starten.

### Port-Konflikt bei Neustart

WebSocket/MJPEG-Ports noch von altem Container belegt.
* **Fix:** `sudo fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp`

### PlatformIO: micro-ROS Build schlaegt fehl (Debian Trixie)

PEP 668 blockiert `pip install` fuer micro-ROS Build-Dependencies.
* **Fix (einmalig):** `python3 -m venv /home/pi/.platformio/penv && /home/pi/.platformio/penv/bin/pip install lark-parser importlib-resources pyyaml "markupsafe==2.0.1" "empy==3.3.4" catkin_pkg "colcon-common-extensions>=0.3.0"`
