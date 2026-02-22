# Dashboard + Vision: Live-Betrieb Startanleitung

Vollstaendige Startsequenz fuer Dashboard mit Kamera, Hailo-8L Objekterkennung und Gemini-Semantik.
Reihenfolge kritisch — ESP32 hat keine Reconnection-Logik!

**Ports:** WebSocket 9090, MJPEG 8082, Vite 5173, Hailo UDP 5005
**URL:** http://192.168.1.24:5173

## Voraussetzungen

- HEF-Modell vorhanden: `hardware/models/yolov8s.hef` (sonst: siehe Abschnitt "HEF herunterladen")
- `GEMINI_API_KEY` in `amr/docker/.env` gesetzt (fuer Gemini-Semantik)
- Kein anderer Dienst auf dem ESP32-Port (`/dev/ttyACM0`)

## Startsequenz (4 Terminals)

### Terminal 1: Infrastruktur bereinigen

```bash
# 1. Alte Container und Ports freigeben
docker stop $(docker ps -q) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp 2>/dev/null
sudo systemctl stop embedded-bridge.service selection-panel.service 2>/dev/null

# 2. Kamera-Bridge sauber neu laden
sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1
sudo systemctl restart camera-v4l2-bridge.service
sleep 4
sudo systemctl is-active camera-v4l2-bridge.service   # → "active"

# 3. ESP32 per DTR/RTS resetten (geht in ping-Schleife, wartet auf Agent)
python3 -c "
import serial, time
s = serial.Serial('/dev/ttyACM0', 115200)
s.setDTR(False); s.setRTS(True); time.sleep(0.1)
s.setDTR(True); s.setRTS(False); time.sleep(0.05)
s.setDTR(False); s.close()
print('ESP32 Reset OK')
"
```

### Terminal 1: Docker Full-Stack starten

```bash
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_camera:=True use_vision:=True \
    use_rviz:=False use_nav:=False
```

Warten bis `[dashboard_bridge]` und `[gemini_semantic_node]` gestartet melden.

### Terminal 2: Hailo-Runner (Host-nativ)

```bash
cd ~/AMR-Bachelorarbeit
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py \
    --model hardware/models/yolov8s.hef --threshold 0.3
```

Erwartete Ausgabe:
```
[DEBUG] Output "yolov8s/yolov8_nms_postprocess": 80 Klassen, N Detektionen gesamt
[HAILO] 1 Objekt(e) in 36.0 ms: bottle
```

Ohne Hailo-Hardware: `--fallback` statt `--model ...`

### Terminal 3: Dashboard-Frontend

```bash
cd ~/AMR-Bachelorarbeit/dashboard
npm run dev -- --host
```

Oeffnet http://192.168.1.24:5173 auf iPhone/Tablet/Mac.

### Terminal 4 (optional): Debugging

```bash
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh exec bash
# Im Container:
ros2 topic hz /vision/detections      # ~5 Hz erwartet
ros2 topic echo /vision/detections --once
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
| Kein Kamerabild im Dashboard | MJPEG-Server war single-threaded, Hailo blockierte | `ThreadingHTTPServer` Fix (bereits eingespielt) |
| `HAILO_OUT_OF_PHYSICAL_DEVICES` | Alter Runner-Prozess haelt Device | `pkill -f host_hailo_runner` |
| `HAILO_HEF_NOT_COMPATIBLE` | Falsches HEF (hailo8 statt hailo8l) | Neu herunterladen mit `hailo8l` URL |
| `NETWORK_GROUP_NOT_ACTIVATED` | `activate()` fehlt | Bereits im Code gefixt |
| `/dev/video10` fehlt | v4l2loopback nicht geladen | `sudo modprobe v4l2loopback video_nr=10 ...` |
| Port 8082 belegt | Alter Container/Prozess | `sudo fuser -k 8082/tcp` |
| ESP32 inaktiv | Firmware hat keine Reconnection | DTR/RTS Reset-Sequenz ausfuehren |
| 0 Detektionen | Kein COCO-Objekt vor Kamera | Person/Flasche/Stuhl vor Kamera halten |
