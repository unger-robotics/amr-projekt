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

Das Skript erledigt: Gruppenzugehoerigkeit pruefen und korrigieren, udev-Regeln fuer ESP32 und RPLIDAR anlegen, X11-Zugriff konfigurieren, v4l2loopback fuer die Kamera-Bridge installieren und den systemd-Service registrieren. Nach Aenderungen an den Gruppen ist ein Re-Login noetig.

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

**Basis-Image:** `ros:humble-ros-base` (Ubuntu 22.04, arm64 multi-arch). `osrf/ros:humble-desktop` ist nicht fuer arm64 verfuegbar -- stattdessen werden RViz2, Nav2, SLAM Toolbox und micro-ROS Agent einzeln installiert. Der micro-ROS Agent wird aus Source gebaut, da kein arm64-apt-Paket existiert.

**Netzwerk:** `network_mode: host` -- noetig fuer ROS2 DDS Multicast Discovery. Alle ROS2-Topics sind direkt auf dem Host sichtbar.

**Privilegien:** `privileged: true` fuer Zugriff auf Serial-Devices (ESP32, RPLIDAR), Kamera (`/dev/video10`) und GPIO.

**Volumes:**

| Mount (Host)         | Ziel im Container            | Modus | Zweck                                            |
|----------------------|------------------------------|-------|--------------------------------------------------|
| `ros2_ws/src/my_bot` | `/ros2_ws/src/my_bot`        | rw    | ROS2-Paket (Quellcode)                           |
| `amr/scripts`        | `/amr_scripts`               | ro    | Validierungsskripte                              |
| `amr/scripts`        | `/scripts`                   | ro    | Symlink-Aufloesung fuer `my_bot/my_bot/`         |
| `hardware/`          | `/hardware`                  | ro    | HEF-Modelle (`models/`), Dokumentation (`docs/`) |
| `dashboard/`         | `/dashboard`                 | ro    | TLS-Zertifikate fuer HTTPS/WSS                   |
| `asound.conf`        | `/etc/asound.conf`           | ro    | ALSA-Konfiguration                               |
| `/tmp/.X11-unix`     | `/tmp/.X11-unix`             | rw    | X11-Socket fuer RViz2                            |
| Docker Volumes       | `/ros2_ws/build,install,log` | rw    | Persistenter Build-Cache                         |

**Entrypoint:** `entrypoint.sh` sourced automatisch alle Workspaces (ROS2 Humble, micro-ROS Agent, Projekt-Workspace). Kein manuelles `source setup.bash` noetig.

## Hilfs-Skripte

**run.sh** -- Convenience-Wrapper fuer `docker compose run/exec`. Beliebige Befehle via `./run.sh <befehl>` ausfuehrbar (z.B. `./run.sh ros2 topic list`). Bei jedem Aufruf:
- Startet Container via `docker compose up -d` falls nicht laufend
- Gibt Ports 5173, 5174, 8082, 9090 frei falls belegt (via `fuser -k`)
- Aktualisiert serielle Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) im Container
- Synchronisiert `/dev/snd/*`-Geraete in den Container (USB-Audio/ReSpeaker kann nach Container-Start enumeriert werden)
- Setzt X11-Zugriff (`xhost +local:docker`)
- Prueft bei `use_camera:=True` ob `camera-v4l2-bridge.service` aktiv ist und `/dev/video10` existiert
- `./run.sh exec bash` oeffnet ein zweites Terminal in einem bereits laufenden Container

**verify.sh** -- Automatischer Verifikationstest: Prueft Image-Existenz, ROS2-Distribution, installierte Pakete, Device-Zugriff, Kamera-Bridge, Workspace-Build und Paket-Executables. Gibt eine PASS/FAIL/WARN-Zusammenfassung aus.

**host_setup.sh** -- Einmalige Host-Konfiguration: Gruppen, udev-Regeln (`/dev/amr_drive`, `/dev/amr_sensor`, `/dev/amr_lidar`), X11-Pakete, v4l2loopback-Installation mit modprobe-Config, IMX296-Kamera-Erkennung, und Installation des systemd-Services fuer die Kamera-Bridge.

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
