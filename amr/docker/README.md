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
