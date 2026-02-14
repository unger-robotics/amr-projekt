# ROS2 Humble Docker-Setup fuer AMR

ROS2 Humble laeuft in einem Docker-Container (Ubuntu 22.04), da der Raspberry Pi 5
auf Debian Trixie laeuft und keine offiziellen ROS2-Humble-apt-Pakete verfuegbar sind.

## Voraussetzungen

- Docker >= 29.x mit Compose Plugin
- User in Gruppen `docker`, `dialout`, `video`
- Einmaliges Host-Setup:

```bash
sudo bash host_setup.sh
```

## Image bauen

```bash
cd amr/docker/
docker compose build    # ~15-20 Min auf Pi 5, danach gecached
```

## Container starten

```bash
# Interaktive Shell
./run.sh

# Einzelbefehl ausfuehren
./run.sh ros2 topic list

# Workspace bauen (einmalig nach Aenderungen)
./run.sh colcon build --packages-select my_bot --symlink-install

# Full-Stack starten (micro-ROS + SLAM + Nav2)
./run.sh ros2 launch my_bot full_stack.launch.py

# Nur SLAM (ohne Navigation)
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false
```

## Zweites Terminal

Waehrend der Container laeuft:

```bash
./run.sh exec bash
```

Dann z.B.:

```bash
ros2 topic list
ros2 topic echo /odom --once
```

## Verifikation

```bash
./verify.sh
```

Prueft: ROS2-Distribution, installierte Pakete, Device-Zugriff, Workspace-Build,
und listet alle 8 my_bot Nodes.

## Volume-Mounts

| Host-Pfad | Container-Pfad | Modus |
|---|---|---|
| `amr/pi5/ros2_ws/src/my_bot/` | `/ros2_ws/src/my_bot/` | rw |
| `amr/scripts/` | `/amr_scripts/` | ro |
| `hardware/` | `/hardware/` | ro |

Build-Artefakte (`build/`, `install/`, `log/`) werden in Docker-Volumes persistiert.

## RViz2 (GUI)

RViz2 benoetigt X11 auf dem Host. Falls kein Desktop laeuft:

```bash
export DISPLAY=:0
xhost +local:docker
```

Alternativ RViz2 auf einem separaten PC ausfuehren und per ROS2 DDS verbinden
(`ROS_DOMAIN_ID=0`).

## Kamera-Setup (IMX296 Global Shutter)

Die Sony IMX296 CSI-Kamera wird ueber eine v4l2loopback-Bridge in den Container gebracht:
`rpicam-vid (Host) → ffmpeg → /dev/video10 (v4l2loopback) → v4l2_camera_node (Docker)`.

### Erstmalige Einrichtung

```bash
# host_setup.sh installiert v4l2loopback, erstellt modprobe-Config und den systemd-Service:
sudo bash host_setup.sh

# Kamera-Erkennung pruefen (IMX296 muss gelistet sein):
rpicam-hello --list-cameras

# Bridge-Service starten:
sudo systemctl start camera-v4l2-bridge.service

# Pruefen ob /dev/video10 Frames liefert:
v4l2-ctl -d /dev/video10 --all
```

### ROS2-Stack mit Kamera starten

```bash
# Full-Stack mit Kamera (fuer ArUco-Docking):
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True

# Nur Kamera (ohne SLAM/Navigation):
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_nav:=False use_slam:=False use_rviz:=False

# Kamera-Topic pruefen (in zweitem Terminal):
./run.sh exec bash
ros2 topic echo /camera/image_raw --once
ros2 run tf2_ros tf2_echo base_link camera_link
```

### Kamera-Troubleshooting

**IMX296 nicht erkannt (I2C Error -121):**
- CSI-Kabel pruefen (Pi 5 hat 22-pin Mini-CSI, aeltere Kameras brauchen Adapter)
- `dtoverlay=imx296` in `/boot/firmware/config.txt` unter `[all]` eintragen
- `sudo reboot`

**Bridge-Service laeuft nicht:**
```bash
sudo systemctl status camera-v4l2-bridge.service
journalctl -u camera-v4l2-bridge.service -f
```

**/dev/video10 fehlt:**
```bash
sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1
```

## Troubleshooting

**Permission denied auf /dev/ttyACM0:**
```bash
sudo usermod -aG dialout $USER
# Ab- und wieder anmelden
```

**Image neu bauen (ohne Cache):**
```bash
docker compose build --no-cache
```

**Build-Cache loeschen:**
```bash
docker volume rm amr-docker_ros2_build amr-docker_ros2_install amr-docker_ros2_log
```
