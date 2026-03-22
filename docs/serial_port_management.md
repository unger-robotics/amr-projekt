# Serial-Port-Management

## Zweck

Stabile und konfliktarme Nutzung der seriellen Schnittstellen fuer Drive-Knoten, Sensor-Knoten und weitere Tools.

## udev-Symlinks

Beide ESP32-S3 (Seeed Studio XIAO) haben identische USB VID/PID. Die Linux-Enumeration (`/dev/ttyACM0` vs `/dev/ttyACM1`) ist nicht-deterministisch. Loesung: udev-Regeln basierend auf der Hardware-Seriennummer (`ATTRS{serial}`), die stabile Symlinks erzeugen.

| Symlink | ESP32-S3 | Seriennummer | Funktion |
|---|---|---|---|
| `/dev/amr_drive` | #1 | `E8:06:90:9D:9B:A0` | Antrieb, PID, Odometrie, LED |
| `/dev/amr_sensor` | #2 | `98:3D:AE:EA:08:1C` | Ultraschall, Cliff, IMU, Batterie, Servo |

## Einrichtung

Die udev-Regeln werden durch `host_setup.sh` installiert:

```bash
cd ~/amr-projekt/amr/docker
sudo bash host_setup.sh
```

Die `platformio.ini` beider Knoten verwenden diese Symlinks als `upload_port` und `monitor_port`.

## DTR/RTS-Reset-Sequenz

Nach einem Agent-Kill oder bei haengendem micro-ROS-Zustand muss der ESP32 per DTR/RTS zurueckgesetzt werden. Die Firmware hat keine Reconnection-Logik.

```python
setDTR(False)
setRTS(True)
time.sleep(0.1)
setDTR(True)
setRTS(False)
time.sleep(0.05)
setDTR(False)
```

## Konfliktvermeidung

- **Kein paralleler Zugriff:** Nur ein Prozess darf einen seriellen Port gleichzeitig oeffnen. PlatformIO-Monitor, micro-ROS Agent und `docker compose run` konkurrieren um denselben Port.
- **`docker compose run` vs `up -d`:** Alte `run`-Container blockieren den Serial-Port auch nach Beendigung des Vordergrundprozesses. Immer `docker compose up -d` verwenden oder gestoppte Container entfernen.
- **Pruefschritte vor Agent-Start:**
  1. `ls -la /dev/amr_*` — Symlinks vorhanden?
  2. `lsof /dev/amr_drive /dev/amr_sensor` — kein anderer Prozess aktiv?
  3. `docker ps` — keine alten `run`-Container?

## Docker-Integration

### docker-compose.yml Device-Mapping

Die `docker-compose.yml` mappt die udev-Symlinks explizit in den Container:

```yaml
devices:
  - "/dev/amr_drive:/dev/amr_drive"     # ESP32-S3 #1 (Antrieb)
  - "/dev/amr_sensor:/dev/amr_sensor"   # ESP32-S3 #2 (Sensorik)
  - "/dev/ttyUSB0:/dev/ttyUSB0"         # RPLIDAR A1
  - "/dev/video10:/dev/video10"         # IMX296 Kamera (v4l2loopback-Bridge, dynamisch via cgroup)
  - "/dev/snd:/dev/snd"                 # I2S Audio-Ausgabe
```

Zusaetzlich sind Cgroup-Regeln fuer dynamisch eingesteckte USB-Geraete definiert (`c 166:* rmw` fuer ttyACM, `c 188:* rmw` fuer ttyUSB).

### Container-Symlinks via run.sh

Da Host-udev-Regeln im Container nicht greifen, erstellt `run.sh` nach dem Start des Containers die Symlinks manuell. Die Funktion `_setup_serial_symlinks` liest fuer jeden Symlink (`/dev/amr_drive`, `/dev/amr_sensor`) das Host-Ziel (z.B. `/dev/ttyACM0`) und erstellt per `docker exec ln -sf` den entsprechenden Symlink im Container.

**Wichtig:** `run.sh` verwendet `docker compose up -d` statt `docker compose run`, da `run` die `devices:`-Mappings aus der Compose-Datei ignoriert.

## micro-ROS Agent

Zwei separate Agents laufen im Docker-Container, jeweils auf einem eigenen seriellen Pfad. Die Standard-Ports werden im Launch-File (`full_stack.launch.py`) definiert:

```
drive_serial_port:=/dev/amr_drive    (Default)
sensor_serial_port:=/dev/amr_sensor  (Default)
```

Aufruf der Agents:

```
micro_ros_agent serial --dev /dev/amr_drive -b 921600
micro_ros_agent serial --dev /dev/amr_sensor -b 921600
```

Agent-Workspace: `source /opt/microros_ws/install/setup.bash` (nicht `/opt/ros/humble/`).
