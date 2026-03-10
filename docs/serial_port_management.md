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

## micro-ROS Agent

Zwei separate Agents laufen im Docker-Container, jeweils auf einem eigenen seriellen Pfad:

```
micro_ros_agent serial --dev /dev/amr_drive -b 921600
micro_ros_agent serial --dev /dev/amr_sensor -b 921600
```

Agent-Workspace: `source /opt/microros_ws/install/setup.bash` (nicht `/opt/ros/humble/`).
