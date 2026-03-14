# Build und Deployment

## Firmware (PlatformIO, zwei getrennte Projekte)

Die MCU-Firmware besteht aus zwei getrennten PlatformIO-Projekten mit identischem Dual-Core-Pattern (Core 0: micro-ROS Executor, Core 1: Echtzeit-Datenerfassung + CAN).

### Drive-Node (Antrieb, PID, Odometrie, LED)

```bash
cd amr/mcu_firmware/drive_node
pio run                                    # Kompilieren
pio run -t upload -t monitor               # Upload + Monitor
pio run -e led_test -t upload -t monitor   # MOSFET-Diagnose (~5s)
```

### Sensor-Node (Ultraschall, Cliff, IMU, Batterie, Servo)

```bash
cd amr/mcu_firmware/sensor_node
pio run                                    # Kompilieren
pio run -t upload -t monitor               # Upload + Monitor
```

Erster Build pro Node: ~15 Min (micro-ROS aus Source). Folgebuilds gecached.

### Firmware-Pruefung des Drive-Node

Falls unklar ist, ob die korrekte Firmware laeuft:

```bash
timeout 3 cat /dev/amr_drive | od -A x -t x1z | head -3
```

Kriterium:

* Binaere XRCE-DDS-Daten mit `0x7e`-Header: korrekt
* Text wie `duty= 255/1023`: falsches Environment (`led_test`)

Falls die falsche Firmware aktiv ist:

```bash
cd amr/mcu_firmware/drive_node
pio run -e drive_node -t upload
```

## ROS2 und Docker

ROS2 Humble laeuft auf dem Pi 5 im Docker-Container (`amr_ros2`). Das Docker-Image wird aus `amr/docker/Dockerfile` gebaut.

### Einmalige Einrichtung

```bash
cd amr/docker/
sudo bash host_setup.sh     # udev-Regeln, Gruppen, Kamera-Bridge, CAN-Service
docker compose build         # Image bauen (~15-20 Min auf Pi 5)
```

### Container-Wrapper `run.sh`

Der Convenience-Wrapper `amr/docker/run.sh` verwaltet den Container-Lebenszyklus:

```bash
cd amr/docker/
./run.sh                                          # Interaktive Shell
./run.sh bash                                     # Interaktive Shell (explizit)
./run.sh ros2 topic list                          # Einzelbefehl ausfuehren
./run.sh ros2 launch my_bot full_stack.launch.py  # Full-Stack starten
./run.sh colcon build --packages-select my_bot --symlink-install  # Build
./run.sh exec bash                                # Zweites Terminal im laufenden Container
```

`run.sh` erledigt automatisch:

* Container via `docker compose up -d` starten (falls nicht laufend)
* udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) im Container anlegen
* Kamera-Bridge-Pruefung bei `use_camera:=True`

### Colcon Build

```bash
./run.sh colcon build --packages-select my_bot --symlink-install
```

### Verifikation

```bash
./verify.sh    # Gesamttest (Topics, TF, Raten)
```

## Full-Stack Launch

### Launch-Argumente

| Argument | Default | Beschreibung |
|---|---|---|
| `use_slam` | `True` | SLAM Toolbox (async Modus) |
| `use_nav` | `True` | Nav2 Navigation Stack |
| `use_rviz` | `True` | RViz2 Visualisierung |
| `use_sensors` | `True` | Sensor-Node ESP32-S3 |
| `use_dashboard` | `False` | Dashboard-Bridge (WebSocket :9090, MJPEG :8082) |
| `use_camera` | `False` | Kamera-Node (v4l2_camera_node) |
| `use_vision` | `False` | Vision-Pipeline (Hailo UDP + Gemini) |
| `use_cliff_safety` | `True` | Cliff-Safety cmd_vel-Multiplexer |
| `use_audio` | `False` | Audio-Feedback (PCM5102A HifiBerry DAC) |
| `use_can` | `False` | CAN-to-ROS2 Bridge (SocketCAN) |
| `use_respeaker` | `False` | ReSpeaker Mic Array DoA/VAD |
| `drive_serial_port` | `/dev/amr_drive` | Serieller Port Drive-Node |
| `sensor_serial_port` | `/dev/amr_sensor` | Serieller Port Sensor-Node |
| `camera_device` | `/dev/video10` | Video-Device (v4l2loopback-Bridge) |
| `params_file` | `nav2_params.yaml` | Nav2 Parameter-Datei |
| `slam_params_file` | `mapper_params_online_async.yaml` | SLAM Toolbox Parameter-Datei |

### Haeufige Startkombinationen

```bash
cd amr/docker/

# Nur SLAM (ohne Navigation)
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false

# SLAM + Navigation + Dashboard (ohne RViz)
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_rviz:=False

# Vollsystem mit Kamera und Vision
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_camera:=True use_vision:=True use_rviz:=False
```

## ESP32-Reset

Die ESP32-S3-Knoten besitzen keine eigenstaendige Reconnection-Logik fuer den micro-ROS-Agent. Ein Reset vor dem Containerstart stellt sicher, dass die Knoten beim Agent-Start in den Wartezustand eintreten.

```bash
python3 -c "
import serial, time
for name, port in [('Drive', '/dev/amr_drive'), ('Sensor', '/dev/amr_sensor')]:
    try:
        s = serial.Serial(port, 921600)
        s.dtr = False
        s.rts = True
        time.sleep(0.1)
        s.dtr = False
        s.rts = False
        time.sleep(0.1)
        s.close()
        print(f'{name} ({port}) reset OK')
    except Exception as e:
        print(f'{name} ({port}) reset FEHLER: {e}')
time.sleep(2)
print('Warte 2s auf Boot...')
"
```

## Live-Betrieb: Dashboard + Vision + SLAM

Dieser Ablauf startet das Gesamtsystem fuer den Live-Betrieb mit SLAM, Kamera, Dashboard, Hailo-basierter Objekterkennung und semantischer Auswertung.

### Voraussetzungen

- Das HEF-Modell liegt unter `hardware/models/yolov8s.hef`.
- `GEMINI_API_KEY` ist in `amr/docker/.env` gesetzt.
- Das Docker-Image ist aktuell (`docker compose build`).
- Kein anderer Prozess blockiert die seriellen Ports.
- Auf dem Drive-Node laeuft die korrekte Firmware, nicht `led_test`.

### Startsequenz

Der Live-Betrieb benoetigt drei Terminals.

### Terminal 1: ESP32-Reset und Docker-Full-Stack

```bash
# Alte Container und Ports freigeben
docker stop $(docker ps -q) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp 2>/dev/null

# Kamera-Bridge pruefen oder starten
sudo systemctl is-active camera-v4l2-bridge.service || {
    sudo modprobe -r v4l2loopback 2>/dev/null
    sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1
    sudo systemctl restart camera-v4l2-bridge.service
    sleep 4
}

# Beide ESP32 per DTR/RTS resetten
python3 -c "
import serial, time
for name, port in [('Drive', '/dev/amr_drive'), ('Sensor', '/dev/amr_sensor')]:
    try:
        s = serial.Serial(port, 921600)
        s.dtr = False; s.rts = True; time.sleep(0.1)
        s.dtr = False; s.rts = False; time.sleep(0.1)
        s.close()
        print(f'{name} ({port}) reset OK')
    except Exception as e:
        print(f'{name} ({port}) reset FEHLER: {e}')
time.sleep(2)
"

# Docker-Full-Stack starten
cd ~/amr-projekt/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_slam:=True use_dashboard:=True use_camera:=True use_vision:=True \
    use_rviz:=False use_nav:=False
```

Erfolgsindikatoren in Terminal 1:

* `micro_ros_agent_drive`: `session established`
* `micro_ros_agent_sensor`: `session established`
* `slam_toolbox`: `Registering sensor`
* `dashboard_bridge`: WebSocket- und MJPEG-Server gestartet
* `gemini_semantic_node`: Modell konfiguriert
* `hailo_udp_receiver`: wartet auf den Host-Runner

### Terminal 2: Hailo-Runner auf dem Host starten

```bash
cd ~/amr-projekt
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py \
    --model hardware/models/yolov8s.hef --threshold 0.35
```

Falls keine Hailo-Hardware angeschlossen ist:

```bash
cd ~/amr-projekt
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py --fallback
```

Kriterium:

* Der Runner verbindet sich mit dem MJPEG-Stream der `dashboard_bridge`.
* Erste Detektionen erscheinen nach erfolgreichem Stream-Zugriff.

### Terminal 3: Dashboard-Benutzeroberflaeche starten

```bash
cd ~/amr-projekt/dashboard
npm run dev -- --host 0.0.0.0
```

Die Benutzeroberflaeche ist danach erreichbar unter `http://<Pi-IP>:5173/`.

### Verifikation

Im laufenden System ueber ein zweites Terminal pruefen:

```bash
cd ~/amr-projekt/amr/docker
./run.sh exec bash
```

Dann im Container:

```bash
ros2 topic list --no-daemon
timeout 5 ros2 topic hz /odom
timeout 5 ros2 topic hz /scan
ros2 topic echo /odom --once --no-daemon
ros2 topic echo /vision/detections --once --no-daemon
```

Erwartete Kerndaten:

* `/odom` aktiv (~18 Hz)
* `/scan` aktiv (~7-8 Hz)
* `/map` aktiv
* `/camera/image_raw` aktiv
* `/vision/detections` aktiv nach Start des Hailo-Runners

### System herunterfahren

1. Host-Runner und Benutzeroberflaeche mit `Ctrl+C` beenden.
2. ROS2-Launch in Terminal 1 mit `Ctrl+C` beenden.
3. Container und Ports bereinigen:

```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
fuser -k 8082/tcp 9090/tcp 5173/tcp
```

## CAN-Bus (SocketCAN)

`host_setup.sh` Sektion 6 installiert `can-utils` und den `can0.service` (systemd, 1 Mbit/s, txqueuelen=1000). Nach Aenderungen an `/boot/firmware/config.txt` ist ein Reboot noetig.

```bash
# CAN-Status pruefen
ip -details link show can0

# CAN-Bridge Diagnostik-Node (im Docker)
ros2 launch my_bot full_stack.launch.py use_can:=True

# ReSpeaker DoA/VAD-Node (im Docker)
ros2 launch my_bot full_stack.launch.py use_respeaker:=True

# Standalone CAN-Validierung (ohne Docker)
python3 amr/scripts/can_validation_test.py --duration 30
```

## Dashboard (React + Vite + TypeScript + Tailwind)

```bash
cd dashboard/
npm install && npm run dev -- --host 0.0.0.0   # Entwicklung (http://<Pi-IP>:5173)
npm run build                                   # Produktion (tsc + vite build)
npm run lint                                    # ESLint
npx tsc --noEmit                                # TypeScript Type-Check
```

Das Dashboard verbindet sich automatisch per WebSocket (`ws://<Pi-IP>:9090`) mit der `dashboard_bridge` im Container. SLAM-Kartenklick sendet ein Nav2 NavigateToPose Goal.

## Wartungsskripte

```bash
# Projekt-Abhaengigkeiten aktualisieren (npm, pip, PlatformIO, Docker, ROS2-Image)
./scripts/update_dependencies.sh

# Systemwartung mit AMR-Diagnose (Temperatur, Speicher, Services, USB, EEPROM)
sudo ./scripts/rover_wartung.sh            # Vollstaendig mit apt-Updates
sudo ./scripts/rover_wartung.sh --check    # Nur Diagnose, keine Aenderungen
```

## Typische Fehlerbilder

### micro-ROS-Agent laeuft, aber keine Session

Ursachen:

* Falsche Drive-Node-Firmware (`led_test` statt `drive_node`)
* ESP32 nach Neustart nicht resettet

Massnahmen:

* `drive_node` explizit flashen: `cd amr/mcu_firmware/drive_node && pio run -e drive_node -t upload`
* DTR/RTS-Reset vor dem Containerstart erneut ausfuehren (siehe Abschnitt ESP32-Reset)

### SLAM meldet `Message Filter dropping message`

Ursache:

* `odom -> base_link` TF fehlt, meist wegen fehlender Verbindung zum Drive-Node

Massnahme:

```bash
ros2 topic echo /odom --once --no-daemon
```

Falls keine Daten: Drive-Node Reset und micro-ROS-Agent-Verbindung pruefen.

### Hailo meldet `HAILO_OUT_OF_PHYSICAL_DEVICES`

Ursache:

* Alter Runner-Prozess blockiert das Device

Massnahme:

```bash
pkill -f host_hailo_runner
```

### Port-Konflikte bei Neustart

Massnahme:

```bash
fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp
```

## Regel

Lange Kommandoablaeufe bleiben hier und nicht in `CLAUDE.md`.
