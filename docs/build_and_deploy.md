# Build und Deployment

## Firmware

Die Firmware besteht aus zwei getrennten PlatformIO-Projekten:

- `amr/mcu_firmware/drive_node/`
- `amr/mcu_firmware/sensor_node/`

## ROS2 und Docker

ROS2 Humble laeuft auf dem Pi 5 im Docker-Container.

## Empfohlene Inhalte fuer die Uebernahme

- Build-, Upload- und Monitor-Kommandos pro Node
- Docker-Build und Container-Start
- `run.sh`, `verify.sh`, `host_setup.sh`
- Deployment auf den Raspberry Pi 5

## Regel

Lange Kommandoablaeufe bleiben hier und nicht in `CLAUDE.md`.

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

## Live-Betrieb: Dashboard + Vision + SLAM

Dieser Ablauf startet das Gesamtsystem fuer den Live-Betrieb mit SLAM, Kamera, Dashboard, Hailo-basierter Objekterkennung und semantischer Auswertung. Die Startreihenfolge ist kritisch, weil die ESP32-Nodes keine eigenstaendige Reconnection-Logik fuer den micro-ROS-Agent besitzen.

### Voraussetzungen

Vor dem Start muessen folgende Bedingungen erfuellt sein:

- Das HEF-Modell liegt unter `hardware/models/yolov8s.hef`.
- `GEMINI_API_KEY` ist in `amr/docker/.env` gesetzt.
- Das Docker-Image ist aktuell.
- Kein anderer Prozess blockiert `/dev/ttyACM0` oder `/dev/ttyACM1`. **Hinweis:** Die Zuordnung von `ttyACM0`/`ttyACM1` zu Drive-/Sensor-Knoten ist nicht deterministisch. Falls udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) im Container verfuegbar sind, diese bevorzugen (siehe `docs/serial_port_management.md`).
- Auf dem Drive-Node laeuft die korrekte Firmware, nicht `led_test`.

Firmware-Pruefung des Drive-Node:

```bash
timeout 3 cat /dev/amr_drive | od -A x -t x1z | head -3
```

Kriterium:

* binaere XRCE-DDS-Daten mit `0x7e`-Header: korrekt
* Text wie `duty= 255/1023`: falsches Environment

Falls die falsche Firmware aktiv ist:

```bash
cd amr/mcu_firmware/drive_node
pio run -e drive_node -t upload
```

### Startsequenz

Der Live-Betrieb benoetigt drei Terminals.

### Terminal 1: System vorbereiten und Docker-Full-Stack starten

```bash
# Alte Container und Ports freigeben
docker stop $(docker ps -q) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp 2>/dev/null
sudo systemctl stop embedded-bridge.service selection-panel.service 2>/dev/null

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

# Docker-Full-Stack starten
cd ~/amr-projekt/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_slam:=True use_dashboard:=True use_camera:=True use_vision:=True \
    use_rviz:=False use_nav:=False \
    drive_serial_port:=/dev/ttyACM1 sensor_serial_port:=/dev/ttyACM0
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
npm run dev -- --host
```

Danach ist die Benutzeroberflaeche ueber den konfigurierten Host erreichbar.

### Verifikation

Nach dem Start sollte in einem zweiten Shell-Zugang zum Container geprueft werden:

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

* `/odom` aktiv
* `/scan` aktiv
* `/map` aktiv
* `/camera/image_raw` aktiv
* `/vision/detections` aktiv nach Start des Hailo-Runners

### System herunterfahren

1. Host-Runner und Benutzeroberflaeche mit `Ctrl+C` beenden.
2. ROS2-Launch in Terminal 1 mit `Ctrl+C` beenden.
3. Container und Ports bereinigen:

```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp
```

### Typische Fehlerbilder

#### micro-ROS-Agent laeuft, aber keine Session

Ursachen:

* falsche Drive-Node-Firmware
* ESP32 nach Neustart nicht erneut in den Wartezustand gebracht

Massnahmen:

* `drive_node` explizit mit `pio run -e drive_node -t upload` flashen
* DTR/RTS-Reset vor dem Containerstart erneut ausfuehren

#### SLAM meldet `Message Filter dropping message`

Ursache:

* `odom -> base_link` fehlt, meist wegen fehlender Verbindung zum Drive-Node

Massnahme:

```bash
ros2 topic echo /odom --once --no-daemon
```

#### `/dev/amr_drive not found` im Container

Ursache:

* udev-Symlinks existieren nur auf dem Host

Massnahme:

* im Container immer physische Pfade verwenden:
  `drive_serial_port:=/dev/ttyACM1`
  `sensor_serial_port:=/dev/ttyACM0`

#### Hailo meldet `HAILO_OUT_OF_PHYSICAL_DEVICES`

Ursache:

* alter Runner-Prozess blockiert das Device

Massnahme:

```bash
pkill -f host_hailo_runner
```

#### Port-Konflikte bei Neustart

Massnahme:

```bash
sudo fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp
```
