# Dashboard + Vision + SLAM: Live-Betrieb Startanleitung

Vollständige Startsequenz für das Dashboard mit SLAM-Kartierung, Kamera, Hailo-8L Objekterkennung und Gemini-Semantik. Die Einhaltung der Startreihenfolge ist kritisch, da die ESP32-Mikrocontroller keine eigenständige Reconnection-Logik besitzen.

**Netzwerk-Konfiguration:**
* **Ports:** WebSocket 9090, MJPEG 8082, Vite 5173, Hailo UDP 5005
* **URL:** http://192.168.1.24:5173

## 1. Systemübersicht

Das System besteht im Live-Betrieb aus 17 interagierenden Komponenten: 13 ROS2-Nodes und 2 micro-ROS-Agents im Docker-Container, 1 Host-Prozess (Hailo-Runner), 2 ESP32 micro-ROS Nodes (Drive und Sensor) sowie 1 Host-Service für die Kamera-Bridge.

### 1.1 Komponentenliste

| #  | Komponente                 | Typ               | Funktion                                                            |
|----|----------------------------|-------------------|---------------------------------------------------------------------|
| 1  | `rplidar_node`             | Container-Node    | RPLidar A1 LiDAR-Scanner (10 Hz)                                    |
| 2  | `laser_tf_publisher`       | Container-Node    | Statischer TF: base_link → laser                                    |
| 3  | `camera_tf_publisher`      | Container-Node    | Statischer TF: base_link → camera_link                              |
| 4  | `ultrasonic_tf_publisher`  | Container-Node    | Statischer TF: base_link → ultrasonic_link (bei `use_sensors`)      |
| 5  | `micro_ros_agent` (drive)  | Container-Prozess | Serial-Bridge Drive-Node ↔ ROS2 (`/dev/amr_drive`)                  |
| 6  | `micro_ros_agent` (sensor) | Container-Prozess | Serial-Bridge Sensor-Node ↔ ROS2 (`/dev/amr_sensor`)                |
| 7  | `odom_to_tf`               | Container-Node    | Odometrie → TF-Broadcast (odom → base_link)                         |
| 8  | `slam_toolbox`             | Container-Node    | Async SLAM (Ceres-Solver, 5 cm Auflösung)                           |
| 9  | `v4l2_camera_node`         | Container-Node    | IMX296 Kamera via v4l2loopback (640x480, 15 fps, bgr8)              |
| 10 | `dashboard_bridge`         | Container-Node    | WebSocket (JSON) + MJPEG-Server (HTTP)                              |
| 11 | `hailo_udp_receiver`       | Container-Node    | UDP-Empfänger → `/vision/detections`                                |
| 12 | `gemini_semantic_node`     | Container-Node    | Gemini Cloud-Analyse (gemini-3-flash-preview) → `/vision/semantics` |
| 13 | `cliff_safety_node`        | Container-Node    | cmd_vel-Multiplexer mit Cliff-Notbremse (bei `use_cliff_safety`)    |
| 14 | `audio_feedback_node`      | Container-Node    | WAV-Wiedergabe via aplay/MAX98357A (bei `use_audio`)                |
| 15 | `drive_node`               | ESP32 micro-ROS   | Odom (20 Hz), IMU (50 Hz), Battery (2 Hz), cmd_vel, Servo, PID      |
| 16 | `sensor_node`              | ESP32 micro-ROS   | Ultraschall /range/front (10 Hz), Cliff /cliff (20 Hz)              |
| 17 | `host_hailo_runner.py`     | Host-Prozess      | YOLOv8 Inference auf Hailo-8L (5 Hz, ~36 ms)                        |
| 18 | `camera-v4l2-bridge`       | Host-Service      | rpicam-vid (640x480) → ffmpeg → /dev/video10                        |

### 1.2 Datenfluss und Schnittstellen-Status

| #  | Komponente                | Schnittstelle / Port            | Erwarteter Status                            |
|----|---------------------------|---------------------------------|----------------------------------------------|
| 1  | micro_ros_agent_drive     | `/dev/amr_drive` (Serial)       | session established                          |
| 2  | micro_ros_agent_sensor    | `/dev/amr_sensor` (Serial)      | session established                          |
| 3  | drive_node (ESP32-S3 #1)  | `/dev/amr_drive` (Serial)       | 3 Publisher (odom/imu/battery), 3 Subscriber |
| 4  | sensor_node (ESP32-S3 #2) | `/dev/amr_sensor` (Serial)      | 2 Publisher (range/front, cliff)             |
| 5  | rplidar_node              | Lidar-Interface                 | Sensitivity-Modus, 10 Hz                     |
| 6  | odom_to_tf                | ROS2 intern (TF)                | aktiv                                        |
| 7  | slam_toolbox              | ROS2 intern (TF/Topics)         | Registering sensor, laser_range 0.2 m        |
| 8  | v4l2_camera_node          | `/dev/video10`                  | YUYV @ 640x480                               |
| 9  | laser_tf_publisher        | ROS2 intern (TF)                | base_link → laser                            |
| 10 | camera_tf_publisher       | ROS2 intern (TF)                | base_link → camera_link                      |
| 11 | ultrasonic_tf_publisher   | ROS2 intern (TF)                | base_link → ultrasonic_link                  |
| 12 | dashboard_bridge          | TCP 9090 (WS), TCP 8082 (MJPEG) | WS :9090 + MJPEG :8082 (2 Clients)           |
| 13 | hailo_udp_receiver        | UDP 5005                        | UDP :5005                                    |
| 14 | gemini_semantic_node      | Cloud API (HTTPS)               | gemini-3-flash-preview                       |
| 15 | host_hailo_runner         | Liest TCP 8082, sendet UDP 5005 | ~34 ms/Frame                                 |
| 16 | Frontend                  | TCP 5173 (HTTP)                 | http://192.168.1.24:5173                     |

---

## 2. Voraussetzungen

* HEF-Modell für Edge-KI vorhanden: `hardware/models/yolov8s.hef`.
* Umgebungsvariable `GEMINI_API_KEY` ist in der Datei `amr/docker/.env` gesetzt.
* Das Docker-Image ist aktuell (`docker compose build`), sodass das `google-genai` SDK integriert ist.
* Kein anderer Host-Dienst blockiert die ESP32-Ports `/dev/amr_drive` und `/dev/amr_sensor`.

---

## 3. Startsequenz (Benötigt 3 Terminals)

### Terminal 1: System-Reset und Docker Full-Stack

Im ersten Terminal bereiten wir die Hardware vor und starten den Container.

```bash
# 1. Alte Container und Ports freigeben
docker stop $(docker ps -q) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp 2>/dev/null
sudo systemctl stop embedded-bridge.service selection-panel.service 2>/dev/null

# 2. Kamera-Bridge prüfen/starten
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
for port in ['/dev/amr_drive', '/dev/amr_sensor']:
    try:
        s = serial.Serial(port, 115200)
        s.setDTR(False); s.setRTS(True); time.sleep(0.1)
        s.setDTR(True); s.setRTS(False); time.sleep(0.05)
        s.setDTR(False); s.close()
        print(f'{port} Reset OK')
    except Exception as e:
        print(f'{port} Reset FEHLER: {e}')
"

# 4. Docker Full-Stack starten (10 Nodes + 2 micro_ros_agents)
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_slam:=True use_dashboard:=True use_camera:=True use_vision:=True \
    use_rviz:=False use_nav:=False

```

**Erfolgreicher Start in Terminal 1 zeigt:**

* `[micro_ros_agent]` → `session established` (beide ESP32 verbunden)
* `[slam_toolbox]` → `Registering sensor` (LiDAR erkannt)
* `[dashboard_bridge]` → `WebSocket-Server gestartet` + `MJPEG-Server gestartet`
* `[gemini_semantic_node]` → `Gemini-Modell konfiguriert: gemini-3-flash-preview`
* `[hailo_udp_receiver]` → `warte auf host_hailo_runner.py`

### Terminal 2: Edge-KI Host-Prozess (Hailo-Runner)

Startet die latenzarme Bildverarbeitung direkt auf dem Raspberry Pi Host (außerhalb von ROS 2).

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
[HAILO] 3 Objekt(e) in 35.5 ms: Stuhl, Stuhl, Buch

```

Der Runner verbindet sich automatisch mit dem MJPEG-Stream der `dashboard_bridge` und unternimmt bis zu 10 Versuche mit Backoff, falls die Bridge noch nicht bereit ist. (Nutze `--fallback` anstelle von `--model`, falls keine Hailo-Hardware angeschlossen ist).

### Terminal 3: Dashboard-Frontend (Vite)

```bash
cd ~/AMR-Bachelorarbeit/dashboard
npm run dev -- --host

```

Das Dashboard ist nun unter http://192.168.1.24:5173 auf Mobilgeräten oder im Browser erreichbar. (Für den statischen Produktivbetrieb: `python3 -m http.server 3000 -d ~/AMR-Bachelorarbeit/dashboard/dist/` nach einem `npm run build`).

---

## 4. System herunterfahren

1. **Terminal 2 & 3:** Prozesse mit `Ctrl+C` beenden.
2. **Terminal 1:** ROS2-Launch mit `Ctrl+C` beenden.
3. **Ports bereinigen:**

```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp

```

---

## 5. Einmalige Vorbereitung: HEF-Modell herunterladen

Falls das YOLOv8-Modell für den Beschleuniger noch fehlt:

```bash
mkdir -p hardware/models
wget -O hardware/models/yolov8s.hef \
    "[https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8s.hef](https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8s.hef)"

```
