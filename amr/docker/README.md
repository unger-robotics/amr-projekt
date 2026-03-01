# ROS2 Humble Docker-Setup fuer AMR auf Raspberry Pi 5

Docker-basierte ROS2 Humble Umgebung fuer den Autonomen Mobilen Roboter (Differentialantrieb, SLAM, Nav2, micro-ROS). Erforderlich, weil der Pi 5 auf Debian Trixie laeuft und ROS2 Humble nur unter Ubuntu 22.04 unterstuetzt wird.

## Voraussetzungen

- Raspberry Pi 5 (aarch64, Debian Trixie oder Bookworm)
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

| Mount (Host) | Ziel im Container | Modus | Zweck |
|---|---|---|---|
| `ros2_ws/src/my_bot` | `/ros2_ws/src/my_bot` | rw | ROS2-Paket (Quellcode) |
| `amr/scripts` | `/amr_scripts` | ro | Validierungsskripte |
| `hardware/` | `/hardware` | ro | `config.h` (Hardware-Parameter) |
| `/tmp/.X11-unix` | `/tmp/.X11-unix` | rw | X11-Socket fuer RViz2 |
| Docker Volumes | `/ros2_ws/build,install,log` | rw | Persistenter Build-Cache |

**Entrypoint:** `entrypoint.sh` sourced automatisch alle Workspaces (ROS2 Humble, micro-ROS Agent, Projekt-Workspace). Kein manuelles `source setup.bash` noetig.

## Hilfs-Skripte

**run.sh** -- Convenience-Wrapper fuer `docker compose run/exec`. Beliebige Befehle via `./run.sh <befehl>` ausfuehrbar (z.B. `./run.sh ros2 topic list`). Setzt automatisch X11-Zugriff (`xhost +local:docker`), prueft bei `use_camera:=True` ob die Kamera-Bridge aktiv ist, und bietet mit `./run.sh exec bash` Zugang zu einem bereits laufenden Container.

**verify.sh** -- Automatischer Verifikationstest: Prueft Image-Existenz, ROS2-Distribution, installierte Pakete, Device-Zugriff, Kamera-Bridge, Workspace-Build und Paket-Executables. Gibt eine PASS/FAIL/WARN-Zusammenfassung aus.

**host_setup.sh** -- Einmalige Host-Konfiguration: Gruppen, udev-Regeln (`/dev/amr_esp32`, `/dev/amr_lidar`), X11-Pakete, v4l2loopback-Installation mit modprobe-Config, IMX296-Kamera-Erkennung, und Installation des systemd-Services fuer die Kamera-Bridge.

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

## Troubleshooting

**Serial-Port belegt:** Der ESP32-Port wird von mehreren Projekten geteilt. Vor dem Start pruefen:

```bash
sudo fuser -v /dev/ttyACM0
sudo systemctl stop embedded-bridge.service   # Falls aktiv
```

**Docker-Image ohne Cache oder Build-Cache zuruecksetzen:**

```bash
docker compose build --no-cache
docker volume rm amr-docker_ros2_build amr-docker_ros2_install amr-docker_ros2_log
```

**Kamera-Bridge (/dev/video10 fehlt):**

```bash
sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1
sudo systemctl restart camera-v4l2-bridge.service
```

Weitere Hinweise: siehe `CLAUDE.md` (Abschnitt Troubleshooting).

## Lizenz

Siehe [../LICENSE](../LICENSE).
