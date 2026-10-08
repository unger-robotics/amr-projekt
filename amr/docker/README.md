# ROS2 Humble Docker-Setup fuer AMR auf Raspberry Pi 5

Docker-basierte ROS2 Humble Umgebung fuer den Autonomen Mobilen Roboter (Differentialantrieb, SLAM, Nav2, micro-ROS). Erforderlich, weil der Pi 5 auf Debian Trixie laeuft und ROS2 Humble nur unter Ubuntu 22.04 unterstuetzt wird.

## Voraussetzungen

- Raspberry Pi 5 (aarch64, Debian Trixie)
- Docker >= 20.10 mit Compose V2 (`docker compose`)
- Benutzer in den Gruppen `docker`, `dialout`, `video`
- Optional: X11-Display fuer RViz2

## Ersteinrichtung

Einmalig auf dem Host ausfuehren (erfordert `sudo`):

```bash
sudo bash host_setup.sh
```

Das Skript erledigt: Gruppenzugehoerigkeit pruefen und korrigieren, udev-Regeln fuer ESP32 und RPLIDAR anlegen, X11-Zugriff konfigurieren, v4l2loopback fuer die Kamera-Bridge installieren und den systemd-Service registrieren, ReSpeaker-udev-Regel (USB Vendor Control ohne sudo), CAN-Bus-Setup (SocketCAN can0, MCP2515-Overlay, can-utils, systemd-Service). Nach Aenderungen an den Gruppen ist ein Re-Login noetig.

## Build & Run

```bash
# Image bauen (~15-20 Min beim ersten Mal, danach gecached)
docker compose build

# Interaktive Shell im Container
./run.sh

# ROS2-Workspace bauen (im Container)
./run.sh colcon build --packages-select my_bot --symlink-install

# Full-Stack starten (micro-ROS Agent + SLAM + Nav2 + RViz2)
./run.sh ros2 launch my_bot full_stack.launch.py

# Nur SLAM ohne Navigation
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false

# Mit Kamera (ArUco-Docking)
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True

# Zweites Terminal in laufendem Container oeffnen
./run.sh exec bash
```

## Container-Architektur

**Basis-Image:** `ros:humble-ros-base` (Ubuntu 22.04, arm64 multi-arch). `osrf/ros:humble-desktop` ist nicht fuer arm64 verfuegbar -- stattdessen werden RViz2, Nav2, SLAM Toolbox und micro-ROS Agent einzeln installiert. Der micro-ROS Agent wird aus Source gebaut, da kein arm64-apt-Paket existiert. Python-Abhaengigkeiten: `numpy<2` (ABI-Kompatibilitaet mit cv_bridge), `openwakeword==0.6.0` (fixierte Version), `faster-whisper` (lokales STT, Offline-Fallback), `google-genai` (Gemini Audio-STT, Cloud-primaer). openwakeword-Modelle (`hey_jarvis`) werden im Build heruntergeladen, mit Fallback im Entrypoint.

**Netzwerk:** `network_mode: host` -- noetig fuer ROS2 DDS Multicast Discovery. Alle ROS2-Topics sind direkt auf dem Host sichtbar.

**Privilegien:** `privileged: true` fuer Zugriff auf Serial-Devices (ESP32, RPLIDAR), Kamera (`/dev/video10`) und GPIO.

**Volumes:**

| Mount (Host)         | Ziel im Container            | Modus | Zweck                                            |
|----------------------|------------------------------|-------|--------------------------------------------------|
| `ros2_ws/src`        | `/ros2_ws/src`               | rw    | ROS2-Pakete (Quellcode, ab K7 auch weitere)      |
| `amr/scripts`        | `/amr_scripts`               | ro    | Validierungsskripte                              |
| `amr/scripts`        | `/scripts`                   | ro    | Symlink-Aufloesung fuer `my_bot/my_bot/`         |
| `hardware/`          | `/hardware`                  | ro    | HEF-Modelle (`models/`), Dokumentation (`docs/`) |
| `amr/mcu_firmware`   | `/mcu_firmware`              | ro    | Firmware-Versionen fuer `baseline_snapshot`      |
| `dashboard/`         | `/dashboard`                 | ro    | TLS-Zertifikate fuer HTTPS/WSS                   |
| `asound.conf`        | `/etc/asound.conf`           | ro    | ALSA-Konfiguration                               |
| `/tmp/.X11-unix`     | `/tmp/.X11-unix`             | rw    | X11-Socket fuer RViz2                            |
| `~/amr_bags`         | `/amr_bags`                  | rw    | Referenzaufnahmen (rosbag2, K7-V)                |
| Docker Volumes       | `/ros2_ws/build,install,log` | rw    | Persistenter Build-Cache                         |

`~/amr_bags` vor dem ersten Start als Benutzer anlegen (`mkdir -p ~/amr_bags`), sonst legt Docker das Verzeichnis mit Eigentuemer root an.

**Umgebungsvariablen:**

| Variable | Quelle | Beschreibung |
|---|---|---|
| `DISPLAY` | Host | X11-Display fuer RViz2 |
| `ROS_DOMAIN_ID` | `0` | ROS2 DDS Domain |
| `GEMINI_API_KEY` | Host-Env | Vision, TTS und Gemini Audio-STT (optional; Sprachsteuerung faellt auf lokales Whisper zurueck ohne Key) |
| `OPENWEATHER_API_KEY` | Host-Env | Standort/Wetter in Sprachsteuerung (optional) |
| `AMR_LOCATION` | Host-Env | Standort fuer Wetter-Abfragen (Default: "Wuppertal Vohwinkel") |

**Entrypoint:** `entrypoint.sh` sourced automatisch alle Workspaces (ROS2 Humble, micro-ROS Agent, Projekt-Workspace) und erstellt bei Bedarf eine ALSA-Konfiguration fuer den MAX98357A-Verstaerker. Kein manuelles `source setup.bash` noetig.

## Hilfs-Skripte

**run.sh** -- Convenience-Wrapper fuer `docker compose up -d` + `docker compose exec`. Beliebige Befehle via `./run.sh <befehl>` ausfuehrbar (z.B. `./run.sh ros2 topic list`). Bei jedem Aufruf:
- Startet Container via `docker compose up -d` falls nicht laufend
- Gibt Ports 5173, 5174, 8082, 9090 frei falls belegt (via `fuser -k`)
- Aktualisiert serielle Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) im Container (Host-udev greift im Container nicht)
- Synchronisiert `/dev/snd/*`-Geraete in den Container via `mknod` (USB-Audio/ReSpeaker kann nach Container-Start enumeriert werden)
- Setzt X11-Zugriff (`xhost +local:docker`)
- Prueft bei `use_camera:=True` ob `camera-v4l2-bridge.service` aktiv ist und `/dev/video10` existiert
- `./run.sh exec bash` oeffnet ein zweites Terminal in einem bereits laufenden Container

**verify.sh** -- Automatischer Verifikationstest: Prueft Image-Existenz, ROS2-Distribution, installierte Pakete, Device-Zugriff, Kamera-Bridge, Workspace-Build und Paket-Executables. Gibt eine PASS/FAIL/WARN-Zusammenfassung aus.

**host_setup.sh** -- Einmalige Host-Konfiguration: Gruppen, udev-Regeln (`/dev/amr_drive`, `/dev/amr_sensor`, `/dev/amr_lidar`), X11-Pakete, v4l2loopback-Installation mit modprobe-Config, IMX296-Kamera-Erkennung, und Installation des systemd-Services fuer die Kamera-Bridge.

## Entwicklung ohne Roboter (docker-compose.dev.yml)

`docker-compose.dev.yml` startet dasselbe Image ohne Roboter, etwa auf dem Mac (arm64) oder dem iMac (x86_64). Der Container dient dem Paketbau und der Wiedergabe von Referenzaufnahmen (rosbag2, K7-V). Er bindet keine Geraete ein und laeuft ohne `privileged`, ohne Audio-, Kamera-, X11- und Zertifikat-Mounts und ohne API-Schluessel.

**Isolation (sicherheitsrelevant):** Referenzaufnahmen enthalten Fahrbefehle (`/cmd_vel`, `/nav_cmd_vel`, `/dashboard_cmd_vel`). Der Container laeuft deshalb im Bridge-Netz statt mit `network_mode: host`, dazu mit `ROS_DOMAIN_ID=42` und `ROS_LOCALHOST_ONLY=1`. Eine Wiedergabe erreicht so keinen ROS-2-Teilnehmer ausserhalb des Containers.

**Aufnahmen nur im dev-Container abspielen, auch auf dem Pi.** Der Pi-Container `amr_ros2` laeuft im Host-Netz mit `ROS_DOMAIN_ID=0`. Ein dort abgespieltes `/cmd_vel` erreicht den Fahrkern. `/nav_cmd_vel` und `/dashboard_cmd_vel` leiten `velocity_smoother` bzw. `cliff_safety_node` im laufenden Stack auf `/cmd_vel` weiter; ein Umbenennen von `/cmd_vel` allein reicht deshalb nicht. Ein abgespieltes `/tf` stoert zudem SLAM und Nav2. Der Container `amr_ros2_dev` kann neben `amr_ros2` laufen; `run.sh` beachtet ihn nicht.

| Mount (Host)                     | Ziel im Container            | Modus | Zweck                                          |
|----------------------------------|------------------------------|-------|------------------------------------------------|
| `ros2_ws/src`                    | `/ros2_ws/src`               | rw    | ROS2-Pakete (Quellcode)                        |
| `amr/scripts`                    | `/amr_scripts`, `/scripts`   | ro    | Symlink-Aufloesung fuer `my_bot/my_bot/`       |
| `~/amr_bags`                     | `/amr_bags`                  | ro    | Referenzaufnahmen                              |
| Volumes `dev_build/install/log`  | `/ros2_ws/build,install,log` | rw    | Eigener Build-Cache, getrennt vom Pi-Container |

**Einrichtung** (einmalig):

```bash
mkdir -p ~/amr_bags                              # vor dem ersten Start, sonst legt Docker es als root an
cd amr-projekt/amr/docker
docker compose -f docker-compose.dev.yml build   # nur Mac/iMac; braucht Internet (auf dem Pi ca. 15-20 Min)
```

Auf dem Pi existiert das Image bereits. Dort mit dieser Datei **nicht** bauen, sonst ersetzt ein Neubau das Produktiv-Image `amr-ros2-humble:latest`; stattdessen immer `up -d --no-build` verwenden.

**Start, Shell und Paketbau:**

```bash
docker compose -f docker-compose.dev.yml up -d   # auf dem Pi: up -d --no-build
docker compose -f docker-compose.dev.yml exec amr-dev /entrypoint.sh bash

# im Container
cd /ros2_ws && colcon build --packages-select my_bot --symlink-install
source install/setup.bash
```

**Selbsttest ohne Aufnahme vom Pi** (im Container):

```bash
ros2 topic pub -r 10 /k7v_probe std_msgs/msg/String "{data: probe}" > /dev/null &
timeout -s INT 5 ros2 bag record -s sqlite3 -o /tmp/k7v_probe /k7v_probe
kill %1
ros2 bag info /tmp/k7v_probe
ros2 bag play /tmp/k7v_probe
```

**Referenzaufnahmen holen und abspielen:**

```bash
# auf dem Mac
rsync -av pi@amr.local:amr_bags/ ~/amr_bags/

# im Container
ros2 bag info /amr_bags/<JJJJMMTT_HHMM>_<szene>
ros2 bag play /amr_bags/<JJJJMMTT_HHMM>_<szene> --clock
# Knoten, die gegen die Aufnahme laufen, mit use_sim_time:=true starten
```

**Beenden:**

```bash
docker compose -f docker-compose.dev.yml down    # Volumes (Build-Cache) bleiben erhalten
```

## Kamera-Bridge (IMX296 Global Shutter)

Die Sony IMX296 CSI-Kamera ist nicht direkt im Docker-Container nutzbar. Stattdessen laeuft eine v4l2loopback-Bridge auf dem Host:

```
IMX296 (CSI) -> rpicam-vid (MJPEG) -> ffmpeg -> /dev/video10 (YUYV422) -> v4l2_camera_node (Container)
```

Der systemd-Service `camera-v4l2-bridge.service` wird durch `host_setup.sh` installiert und beim Boot aktiviert. Aufloesung: 640x480 bei 15 fps.

```bash
# Service starten/pruefen
sudo systemctl start camera-v4l2-bridge.service
sudo systemctl status camera-v4l2-bridge.service

# Pruefen ob Frames ankommen
v4l2-ctl -d /dev/video10 --all

# ROS2-Stack mit Kamera starten (ArUco-Docking)
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True
```

## Lizenz

Siehe [../LICENSE](../LICENSE).
