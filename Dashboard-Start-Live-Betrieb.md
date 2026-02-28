# Dashboard + Vision + SLAM: Live-Betrieb Startanleitung

Vollstaendige Startsequenz fuer Dashboard mit SLAM-Kartierung, Kamera, Hailo-8L Objekterkennung und Gemini-Semantik.
Reihenfolge kritisch — ESP32 hat keine Reconnection-Logik!

**Ports:** WebSocket 9090, MJPEG 8082, Vite 5173, Hailo UDP 5005
**URL:** http://192.168.1.24:5173

## Systemuebersicht

13 Komponenten im Live-Betrieb: 11 ROS2-Nodes im Docker-Container, 1 Host-Prozess, 1 ESP32 micro-ROS Node.

| # | Komponente | Typ | Funktion |
|---|---|---|---|
| 1 | `rplidar_node` | Container-Node | RPLidar A1 LiDAR-Scanner (10 Hz) |
| 2 | `laser_tf_publisher` | Container-Node | Statischer TF: base_link → laser |
| 3 | `camera_tf_publisher` | Container-Node | Statischer TF: base_link → camera_link |
| 4 | `micro_ros_agent` | Container-Prozess | Serial-Bridge ESP32 ↔ ROS2 (USB-CDC) |
| 5 | `odom_to_tf` | Container-Node | Odometrie → TF-Broadcast (odom → base_link) |
| 6 | `slam_toolbox` | Container-Node | Async SLAM (Ceres-Solver, 5 cm Aufloesung) |
| 7 | `v4l2_camera_node` | Container-Node | IMX296 Kamera via v4l2loopback (640x480, 15 fps, bgr8) |
| 8 | `dashboard_bridge` | Container-Node | WebSocket (JSON) + MJPEG-Server (HTTP) |
| 9 | `hailo_udp_receiver` | Container-Node | UDP-Empfaenger → `/vision/detections` |
| 10 | `gemini_semantic_node` | Container-Node | Gemini Cloud-Analyse (gemini-3-flash-preview) → `/vision/semantics` |
| 11 | `esp32_bot` | ESP32 micro-ROS | Odom (20 Hz), IMU (50 Hz), Battery (2 Hz) |
| 12 | `host_hailo_runner.py` | Host-Prozess | YOLOv8 Inference auf Hailo-8L (5 Hz, ~36 ms) |
| 13 | `camera-v4l2-bridge` | Host-Service | rpicam-vid (640x480) → ffmpeg → /dev/video10 |

## Voraussetzungen

- HEF-Modell vorhanden: `hardware/models/yolov8s.hef` (sonst: siehe Abschnitt "HEF herunterladen")
- `GEMINI_API_KEY` in `amr/docker/.env` gesetzt (fuer Gemini-Semantik)
- Docker-Image aktuell: `docker compose build` (enthaelt `google-genai` SDK)
- Kein anderer Dienst auf dem ESP32-Port (`/dev/ttyACM0`)

## Startsequenz (3 Terminals)

### Terminal 1: Vorbereitung + Docker Full-Stack

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

# 3. ESP32 per DTR/RTS resetten (geht in ping-Schleife, wartet auf Agent)
python3 -c "
import serial, time
s = serial.Serial('/dev/ttyACM0', 115200)
s.setDTR(False); s.setRTS(True); time.sleep(0.1)
s.setDTR(True); s.setRTS(False); time.sleep(0.05)
s.setDTR(False); s.close()
print('ESP32 Reset OK')
"

# 4. Docker Full-Stack starten (10 Nodes + micro_ros_agent)
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_slam:=True use_dashboard:=True use_camera:=True use_vision:=True \
    use_rviz:=False use_nav:=False
```

Warten bis alle Nodes gestartet melden:
- `[micro_ros_agent]` → `session established` (ESP32 verbunden)
- `[slam_toolbox]` → `Registering sensor` (LiDAR erkannt)
- `[dashboard_bridge]` → `WebSocket-Server gestartet` + `MJPEG-Server gestartet`
- `[gemini_semantic_node]` → `Gemini-Modell konfiguriert: gemini-3-flash-preview`
- `[hailo_udp_receiver]` → `warte auf host_hailo_runner.py`

### Terminal 2: Hailo-Runner (Host-nativ, kein ROS2)

```bash
cd ~/AMR-Bachelorarbeit
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py \
    --model hardware/models/yolov8s.hef --threshold 0.35
```

Erwartete Ausgabe:
```
=== Hailo-8 Host Runner ===
[HAILO] Lade Modell: .../yolov8s.hef
[HAILO] Initialisiert: 1 Input(s), 1 Output(s)
[HAILO] MJPEG-Stream verbunden (Versuch 1)
[HAILO] 3 Objekt(e) in 35.5 ms: Stuhl, Stuhl, Buch
```

Der Runner wartet automatisch auf den MJPEG-Stream (bis zu 10 Versuche mit Backoff), falls `dashboard_bridge` noch nicht bereit ist.

Ohne Hailo-Hardware: `--fallback` statt `--model ...`

### Terminal 3: Dashboard-Frontend

```bash
cd ~/AMR-Bachelorarbeit/dashboard
npm run dev -- --host
```

Oeffnet http://192.168.1.24:5173 auf iPhone/Tablet/Mac.

Alternativ statisch servieren (nach `npm run build`):
```bash
python3 -m http.server 3000 -d ~/AMR-Bachelorarbeit/dashboard/dist/
```

### Optional: Debugging (zweite Container-Shell)

```bash
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh exec bash

# Im Container:
ros2 node list                         # 11 Nodes erwartet
ros2 topic hz /vision/detections       # ~5 Hz erwartet
ros2 topic echo /vision/detections --once
ros2 topic hz /scan                    # ~7.5 Hz erwartet
ros2 topic echo /battery --once        # Batterie-Status
ros2 topic echo /odom --once           # Odometrie
ros2 topic hz /camera/image_raw        # ~15 Hz erwartet
```

## Stoppen

```bash
# Terminal 2+3: Ctrl+C
# Terminal 1: Ctrl+C (Docker), dann:
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp
```

## HEF herunterladen (einmalig)

```bash
mkdir -p hardware/models
wget -O hardware/models/yolov8s.hef \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8s.hef"
```

**Wichtig:** URL enthaelt `hailo8l` (nicht `hailo8`). Device ist Hailo-8L, HEFs sind architektur-inkompatibel.

## Troubleshooting

| Problem | Ursache | Loesung |
|---|---|---|
| ESP32 inaktiv nach Container-Start | Firmware hat keine Reconnection-Logik | ESP32 VOR Container-Start resetten (DTR/RTS) |
| `micro_ros_agent` Segfault | Race Condition beim Reconnect | Container stoppen, ESP32 resetten, Container neu starten |
| `HAILO_OUT_OF_PHYSICAL_DEVICES` | Alter Runner-Prozess haelt Device | `pkill -9 -f host_hailo_runner && sleep 2` |
| `HAILO_HEF_NOT_COMPATIBLE` | Falsches HEF (hailo8 statt hailo8l) | Neu herunterladen mit `hailo8l` URL |
| Kein Kamerabild im Dashboard | MJPEG-Server blockiert | `ThreadingHTTPServer` Fix (bereits eingespielt) |
| `/dev/video10` fehlt | v4l2loopback nicht geladen | `sudo modprobe v4l2loopback video_nr=10 ...` |
| Port 8082/9090 belegt | Alter Container/Prozess | `sudo fuser -k 8082/tcp 9090/tcp` |
| Warte auf SLAM-Karte | ESP32 nicht verbunden → kein Odom → kein TF | ESP32-Status pruefen, ggf. DTR/RTS Reset |
| 0 Detektionen | Kein COCO-Objekt vor Kamera | Person/Flasche/Stuhl vor Kamera halten |
| Gemini 429 (Rate Limit) | Free-Tier-Quote erschoepft | Min. 4s zwischen Aufrufen, Modell: `gemini-3-flash-preview` |
| SLAM `Message Filter dropping` | ESP32 nicht verbunden → kein odom→base_link TF | ESP32 VOR Container-Start resetten |
| YAML-Aenderung wirkt nicht | Colcon-Build-Cache veraltet | `docker volume rm amr-docker_ros2_build amr-docker_ros2_install amr-docker_ros2_log` + `colcon build` |
