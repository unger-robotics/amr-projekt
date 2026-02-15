# Umsetzungsanleitung: AMR Inbetriebnahme

## Dokumentinformationen

| Eigenschaft | Wert                                                               |
|-------------|--------------------------------------------------------------------|
| Projekt     | Autonomer Mobiler Roboter (AMR) fuer Intralogistik                 |
| Version     | 3.0 (vereinfacht)                                                  |
| Datum       | 2026-02-15                                                         |
| Bezug       | V-Modell Validierungsplan (Akzeptanzkriterien siehe Anhang A)      |

Diese Anleitung beschreibt die schrittweise Inbetriebnahme des AMR-Prototyps vom ersten Firmware-Upload bis zur vollstaendigen Navigationsvalidierung. Der Aufbau folgt dem V-Modell-Phasenplan und gliedert sich in vier Teile: Teil 1 behandelt die ESP32-S3 Firmware (Phasen 1-3), Teil 2 die ROS2-Umgebung auf dem Raspberry Pi 5, Teil 3 die Integration beider Subsysteme ueber micro-ROS, und Teil 4 verweist auf die separate Kalibrierungsanleitung. Jede Phase baut auf der vorhergehenden auf -- ein Ueberspringen einzelner Schritte ist nicht vorgesehen.

---

## Teil 1: ESP32-S3 Firmware (Phasen 1-3)

### 1.1 Voraussetzungen und Werkzeuge

**Software:** PlatformIO CLI oder VSCode-Extension.

```bash
pip install platformio
pio --version
```

**Hardware:** XIAO ESP32-S3, Cytron MDD3A, JGA25-370 Motoren mit Hall-Encoder (2x), 3S1P Li-Ion Akkupack, USB-C-Datenkabel. Detaillierte Verdrahtung und Pin-Belegung siehe `hardware/docs/hardware-setup.md`.

### 1.2 PlatformIO-Projekt konfigurieren

**Verzeichnisstruktur:**

```text
amr/esp32_amr_firmware/
  platformio.ini              # Build-Konfiguration
  src/
    main.cpp                  # FreeRTOS-Tasks, micro-ROS, Safety
    robot_hal.hpp             # Hardware-Abstraktion (GPIO, Encoder, PWM)
    pid_controller.hpp        # PID-Regler mit Anti-Windup
    diff_drive_kinematics.hpp # Vorwaerts-/Inverskinematik

hardware/
  config.h                    # Zentrale Parameter (Single Source of Truth)
```

**platformio.ini:**

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
framework = arduino
monitor_speed = 115200
upload_speed = 921600
upload_port = /dev/ttyACM0

build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1
    -I../../hardware

; micro-ROS Konfiguration
board_microros_transport = serial
board_microros_distro = humble

lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio
```

### 1.3 Firmware kompilieren und flashen (Phase 1)

```bash
cd amr/esp32_amr_firmware/

# Kompilieren (erster Durchlauf: 5-15 Min wg. Toolchain-Download)
pio run

# Flashen
pio run -t upload

# Kompilieren + Flashen + Monitor (empfohlener Workflow)
pio run -t upload -t monitor
```

### 1.4 Serieller Monitor und Boot-Verifikation

Der serielle Port wird von micro-ROS belegt (`set_microros_serial_transports(Serial)`). Der Monitor zeigt daher **binaere Daten** statt lesbarem Text -- das ist erwartetes Verhalten.

```bash
pio run -t monitor
```

**Boot-Verifikation ueber Status-LED (D10):**

- **LED blinkt schnell (200 ms):** micro-ROS-Initialisierung fehlgeschlagen. Agent laeuft nicht oder ROS2-Distribution stimmt nicht ueberein.
- **LED zeigt normales Verhalten:** Firmware korrekt gestartet.

Vollstaendige Verifikation der micro-ROS-Kommunikation erst mit laufendem Agent moeglich (siehe Teil 3).

### 1.5 Encoder-Validierung (Phase 2)

**Pre-Flight-Checkliste (optional, empfohlen vor erster Inbetriebnahme):**

```bash
python3 amr/scripts/pre_flight_check.py
```

Prueft USB-Enumeration, Spannungsversorgung, Pin-Belegung und Firmware-Upload. Erzeugt ein Markdown-Protokoll.

**Encoder-Kalibrierung:**

```bash
# Terminal 1: micro-ROS Agent starten
cd amr/docker/
./run.sh ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0

# Terminal 2: Encoder-Test starten
./run.sh exec ros2 run my_bot encoder_test
```

Das Skript bietet vier Modi:

| Modus | Funktion | Akzeptanzkriterium |
|-------|----------|--------------------|
| 10-Umdrehungen-Test | Manuell 10 Umdrehungen drehen, Ticks zaehlen (3 Durchgaenge/Rad) | 370-380 Ticks/Rev, Abweichung < 2 Ticks |
| Richtungstest | Vorzeichenkonvention pruefen (vorwaerts = positiv) | Korrekte Vorzeichen |
| Asymmetrie-Test | Tick-Raten beider Raeder vergleichen | < 5 % gut, 5-10 % akzeptabel, > 10 % mechanisches Problem |
| Live-Anzeige | Aktuelle Geschwindigkeiten und Tick-Raten | -- |

**config.h aktualisieren:**

Nach der Kalibrierung die gemessenen Werte in `hardware/config.h` eintragen:

```c
// Vor Kalibrierung (Platzhalter):
#define TICKS_PER_REV_LEFT 374.3f  // kalibriert (10-Umdrehungen-Test)
#define TICKS_PER_REV_RIGHT 373.6f // kalibriert (10-Umdrehungen-Test)

// Nach Kalibrierung (Beispielwerte):
#define TICKS_PER_REV_LEFT 375.2f  // Kalibriert am 2026-02-15
#define TICKS_PER_REV_RIGHT 374.8f // Kalibriert am 2026-02-15
```

Abgeleitete Konstanten (`METERS_PER_TICK_*`) werden automatisch ueber Praeprozessor-Makros neu berechnet. Firmware danach neu flashen:

```bash
cd amr/esp32_amr_firmware/
pio run -t upload
```

### 1.6 Motor-Validierung (Phase 3)

```bash
./run.sh exec ros2 run my_bot motor_test
```

**Sicherheitshinweis:** Roboter auf Bloecke stellen (Raeder frei drehend) oder sichere Umgebung nutzen. Ctrl+C sendet sofort Stopp-Befehl.

Vier Test-Modi:

| Modus | Funktion | Akzeptanzkriterium |
|-------|----------|--------------------|
| Deadzone-Test | `cmd_vel` von 0-0,2 m/s in 0,01er-Schritten, misst Anlauf-PWM | Anlauf-PWM im Bereich 30-40 (ggf. `PWM_DEADZONE` in `config.h` anpassen) |
| Richtungstest | Einzelne Raeder und Kombinationen in alle Richtungen (je 3 s) | Korrekte Drehrichtung (sonst Motoranschluesse am MDD3A tauschen) |
| Failsafe-Test | Sendet `cmd_vel`, stoppt Senden, misst Zeit bis Stillstand | ~500 ms (+/- 200 ms), entspricht `FAILSAFE_TIMEOUT_MS` in `config.h` |
| Rampen-Test | 0 auf 0,4 m/s ueber 5 s, haelt 2 s | Raeder drehen nicht durch, Beschleunigungsrampe korrekt |

**Hinweis:** Der Validierungsplan nennt an einer Stelle 1000 ms als Failsafe-Timeout. Der autoritative Wert ist `FAILSAFE_TIMEOUT_MS = 500` aus `config.h`.

### 1.7 Troubleshooting ESP32

| Problem | Loesung |
|---------|---------|
| Upload: "Failed to connect to ESP32-S3" | USB-Datenkabel pruefen (nicht Ladekabel). Geraet muss als `/dev/ttyACM*` enumerieren. |
| ESP32 enumeriert nicht als `/dev/ttyACM*` | Boot-Button (GPIO 0) halten waehrend USB einstecken → Bootloader-Modus. Nach Flash per Reset neu starten. |
| Kompilierungsfehler `ledcSetup`/`ledcAttachPin` | Arduino-ESP32 v3.x hat neue LEDC-API (`ledcAttach()`). Firmware nutzt aeltere API (espressif32 v6.x). Bei Plattform-Upgrade LEDC-Aufrufe in `robot_hal.hpp` anpassen. |
| LED D10 blinkt schnell nach Start | micro-ROS-Init fehlgeschlagen. Agent auf Pi starten, ROS2-Distribution (Humble) pruefen. |
| Sporadische Encoder-Ticks bei Stillstand | Encoder-VCC pruefen (stabil 3,3 V). EMI-Stoerungen: Encoder-Leitungen als Twisted Pair, ggf. 100 nF Kondensator an D6/D7 gegen GND. |
| PID schwingt / Motoren brummen | Bei 374 Ticks/Rev ist Quantisierungsrauschen hoeher. PID-Gains (Kp=1,5, Ki=0,5, Kd=0,0 in `main.cpp`) nach Encoder-Kalibrierung anpassen (siehe Teil 4, PID-Tuning). |

---

## Teil 2: Raspberry Pi 5 ROS2-Umgebung

Dieses Kapitel beschreibt die Einrichtung des Raspberry Pi 5 als zentralen Navigationsrechner des AMR. Der Pi uebernimmt SLAM, Pfadplanung und die Kommunikation mit dem ESP32-S3 ueber micro-ROS.

### 2.1 Voraussetzungen und ROS2-Installation via Docker

Der Raspberry Pi 5 laeuft auf Debian Trixie (13), fuer das keine offiziellen ROS2-Pakete verfuegbar sind. ROS2 Humble wird daher ueber Docker bereitgestellt: Ein Container auf Basis von Ubuntu 22.04 (`ros:humble-ros-base`, multi-arch arm64) stellt die vollstaendige ROS2-Umgebung inklusive micro-ROS Agent (aus Source gebaut, da kein arm64-apt-Paket verfuegbar) zur Verfuegung.

**Host-Voraussetzungen:**

Auf dem Raspberry Pi muessen Docker und Docker Compose installiert sein. Der Benutzer muss den Gruppen `docker`, `dialout` und `video` angehoeren:

```bash
docker --version        # >= 20.x erwartet
docker compose version  # >= 2.x erwartet
id -nG                  # docker, dialout, video muessen enthalten sein
```

**Einmalige Host-Einrichtung:**

Das Skript `host_setup.sh` konfiguriert Gruppenzugehoerigkeiten, udev-Regeln fuer stabile Geraetepfade (`/dev/amr_esp32`, `/dev/amr_lidar`), X11-Zugriff fuer RViz2, v4l2loopback fuer die Kamera-Bridge und den `camera-v4l2-bridge.service` (systemd):

```bash
cd amr/docker/
sudo bash host_setup.sh
```

Nach dem Ausfuehren ist ein Ab- und Wiederanmelden erforderlich, falls Gruppenaenderungen vorgenommen wurden.

**Docker-Image bauen:**

```bash
cd amr/docker/
docker compose build    # ~15-20 Min beim ersten Durchlauf, danach gecached
```

Das Image installiert alle benoetigten ROS2-Pakete (Nav2, SLAM Toolbox, RPLIDAR-Treiber, v4l2-camera, cv-bridge, RViz2, rqt), den micro-ROS Agent sowie Python-Bibliotheken. Details zu den installierten Paketen stehen im `Dockerfile`.

**Verifikation des Docker-Setups:**

```bash
./verify.sh
```

Das Skript prueft Image, ROS2-Distribution, Pakete, Serial-Zugriff, Kamera-Bridge, Workspace-Build und Executables. Bei 0 FAIL und Ausgabe "Verifikation BESTANDEN" ist das Setup vollstaendig.

**Arbeiten mit dem Docker-Container:**

Der Convenience-Wrapper `run.sh` vereinfacht den Container-Zugriff:

```bash
cd amr/docker/

# 1. Interaktive Shell im Container
./run.sh

# 2. Einzelbefehl ausfuehren
./run.sh ros2 topic list
./run.sh colcon build --packages-select my_bot --symlink-install

# 3. Zweites Terminal in einem bereits laufenden Container oeffnen
./run.sh exec bash
./run.sh exec ros2 topic list
```

Der Container verwendet `network_mode: host` (DDS-Multicast) und `privileged: true` (Serial/Kamera-Zugriff). Die `entrypoint.sh` sourced automatisch alle ROS2-Workspaces -- ein manuelles `source setup.bash` ist nicht erforderlich. Details zu Volume-Mounts und Container-Konfiguration stehen in `amr/docker/README.md`.

### 2.2 ROS2-Paket my_bot

Das ROS2-Paket `my_bot` liegt unter `amr/pi5/ros2_ws/src/my_bot/` und wird als Volume (read-write) in den Container gemountet. Alle Paket-Metadateien (`package.xml`, `setup.py`, `setup.cfg`, `resource/my_bot`, `my_bot/__init__.py`) sind bereits im Repository vorhanden.

Die `setup.py` registriert 9 Python-Skripte als ausfuehrbare ROS2-Nodes ueber `entry_points`:

| Node | Funktion |
|------|----------|
| `aruco_docking` | Visual Servoing mit ArUco-Markern |
| `odom_to_tf` | Odometrie-zu-TF-Transformation |
| `encoder_test` | Encoder-Kalibrierung (10-Umdrehungen-Test) |
| `motor_test` | Motor-Deadzone und Richtungstest |
| `pid_tuning` | PID-Sprungantwort-Analyse |
| `kinematic_test` | Geradeaus-/Dreh-/Kreisfahrt-Verifikation |
| `slam_validation` | ATE-Berechnung und TF-Ketten-Check |
| `nav_test` | Waypoint-Navigation mit Positionsfehler-Messung |
| `docking_test` | 10-Versuch ArUco-Docking-Test |

#### 2.2.1 Skripte verlinken

Die Python-Skripte liegen im `scripts/`-Verzeichnis und muessen als Modul im `my_bot/`-Paketverzeichnis erreichbar sein. Dafuer werden symbolische Links erstellt:

```bash
cd amr/pi5/ros2_ws/src/my_bot/my_bot/

# ArUco-Docking verlinkt auf das Skript im Paket-eigenen scripts/-Verzeichnis:
ln -s ../scripts/aruco_docking.py aruco_docking.py

# Validierungsskripte verlinken auf amr/scripts/ (5 Ebenen hoeher):
ln -s ../../../../../scripts/encoder_test.py encoder_test.py
ln -s ../../../../../scripts/motor_test.py motor_test.py
ln -s ../../../../../scripts/pid_tuning.py pid_tuning.py
ln -s ../../../../../scripts/kinematic_test.py kinematic_test.py
ln -s ../../../../../scripts/slam_validation.py slam_validation.py
ln -s ../../../../../scripts/nav_test.py nav_test.py
ln -s ../../../../../scripts/docking_test.py docking_test.py
```

**Hinweis:** `odom_to_tf.py` ist eine eigenstaendige Datei (kein Symlink) und liegt bereits in `my_bot/my_bot/`.

Die relativen Symlink-Pfade bleiben im Docker-Container erhalten, da die Verzeichnisstruktur innerhalb des Volume-Mounts identisch ist. Die Validierungsskripte in `amr/scripts/` erfordern den laengeren Pfad (`../../../../../scripts/`), da sie fuenf Verzeichnisebenen oberhalb des Paketverzeichnisses liegen.

### 2.3 Workspace bauen

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install
```

Das Flag `--symlink-install` erstellt symbolische Links statt Kopien -- Aenderungen an Python-Skripten und Konfigurationsdateien werden sofort wirksam. Die Build-Artefakte werden in Docker-Volumes persistiert und ueberleben Container-Neustarts.

Verifikation:

```bash
./run.sh ros2 pkg executables my_bot    # Sollte 9 Nodes listen
```

### 2.4 RPLIDAR A1 einrichten

Der RPLIDAR A1 wird ueber USB angeschlossen. Der ROS2-Treiber (`ros-humble-rplidar-ros`) ist im Docker-Image vorinstalliert. Die udev-Regeln aus `host_setup.sh` erstellen den stabilen Symlink `/dev/amr_lidar` und setzen `MODE="0666"`.

```bash
# Host: Pruefen ob LiDAR erkannt wird
ls /dev/ttyUSB*           # Erwartet: /dev/ttyUSB0
ls -la /dev/amr_lidar     # Erwartet: Symlink auf ttyUSB0

# Docker: LiDAR testen
cd amr/docker/
./run.sh ros2 launch rplidar_ros rplidar_a1_launch.py

# Zweites Terminal: Scan-Daten pruefen
./run.sh exec ros2 topic echo /scan --once
```

Der RPLIDAR A1 benoetigt 5V-Versorgung ueber USB. Bei Verwendung eines USB-Hubs muss dieser aktiv (mit eigenem Netzteil) sein.

### 2.5 Kamera einrichten (IMX296 Global Shutter)

Der AMR verwendet eine Raspberry Pi Global Shutter Camera (Sony IMX296, 1456x1088 Pixel) mit einem 6 mm CS-Mount-Objektiv. Da die IMX296 ueber das CSI-Interface angebunden ist und Docker keinen direkten Zugriff auf die libcamera-Pipeline hat, wird eine v4l2loopback-Bridge eingesetzt:

```
IMX296 (CSI) --> rpicam-vid (Host) --> ffmpeg --> /dev/video10 (v4l2loopback) --> v4l2_camera_node (Docker/ROS2)
```

**Kamera-Erkennung pruefen (Host):**

Die IMX296 wird nicht automatisch erkannt. In `/boot/firmware/config.txt` muss unter `[all]` der Eintrag `dtoverlay=imx296` vorhanden sein (wird von `host_setup.sh` konfiguriert). Nach einem Reboot:

```bash
rpicam-hello --list-cameras
# Erwartet: 0 : imx296 [1456x1088] (...)
```

**Bridge-Service starten und pruefen:**

Der systemd-Service `camera-v4l2-bridge.service` wird von `host_setup.sh` eingerichtet. Er startet `rpicam-vid` im MJPEG-Modus und leitet den Stream ueber `ffmpeg` auf `/dev/video10` (v4l2loopback, YUYV, 1456x1088 @ 15fps):

```bash
sudo systemctl start camera-v4l2-bridge.service
sudo systemctl status camera-v4l2-bridge.service
v4l2-ctl -d /dev/video10 --all    # Pruefen ob Frames ankommen
```

**ROS2-Stack mit Kamera starten:**

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True

# Zweites Terminal: Kamera-Topic pruefen
./run.sh exec ros2 topic echo /camera/image_raw --once
```

**Kamera-Troubleshooting:**

- **IMX296 nicht erkannt (I2C Error -121):** CSI-Kabel pruefen. Der Pi 5 hat einen 22-pin Mini-CSI-Stecker, aeltere Kameras brauchen einen 22-pin-auf-15-pin Adapter.
- **`/dev/video10` fehlt:** `sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1`
- **Bridge-Service haengt:** `journalctl -u camera-v4l2-bridge.service -f` pruefen. Fix: `sudo systemctl restart camera-v4l2-bridge.service`

### 2.6 udev-Regeln

Die udev-Regeln werden automatisch durch `host_setup.sh` (siehe Abschnitt 2.1) eingerichtet. Das Skript erstellt `/etc/udev/rules.d/99-amr-devices.rules` mit stabilen Symlinks `/dev/amr_esp32` und `/dev/amr_lidar` sowie `MODE="0666"` fuer beide Geraete.

Pruefen, ob die Symlinks aktiv sind:

```bash
ls -la /dev/amr_*
# Erwartet:
# /dev/amr_esp32 -> ttyACM0
# /dev/amr_lidar -> ttyUSB0
```

### 2.7 micro-ROS Agent testen

Der micro-ROS Agent uebersetzt DDS-XRCE-Nachrichten vom ESP32-S3 in Standard-ROS2-Topics. Er ist im Docker-Image vorinstalliert (aus Source gebaut).

**Wichtig:** Vor dem Start sicherstellen, dass kein anderer Prozess den Serial-Port belegt:

```bash
# Host-Befehle
sudo systemctl stop embedded-bridge.service   # Falls aktiv
sudo fuser -v /dev/ttyACM0                    # Port muss frei sein
```

Test der Verbindung:

```bash
cd amr/docker/
./run.sh ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/amr_esp32 -b 115200
```

In einem zweiten Terminal die Topics pruefen:

```bash
./run.sh exec ros2 topic list
# Erwartet: /cmd_vel, /odom, /parameter_events, /rosout

./run.sh exec ros2 topic echo /odom --once
# Erwartet: nav_msgs/Odometry mit Position und Geschwindigkeit (20 Hz)
```

### 2.8 Troubleshooting Raspberry Pi / Docker

**Serial-Port: Permission denied oder belegt:**
`sudo bash amr/docker/host_setup.sh` ausfuehren (setzt udev-Regeln mit `MODE="0666"`), danach ab- und wieder anmelden. Port-Belegung pruefen: `sudo fuser -v /dev/ttyACM0`. Ggf. `sudo systemctl stop embedded-bridge.service`.

**micro-ROS Agent verbindet sich nicht:**
Baudrate muss 115200 sein. ESP32 muss geflasht und laufend sein (LED-Status). Kein anderer Prozess darf den Port belegen (`sudo fuser /dev/ttyACM0`). Nach Agent-Neustart muss der ESP32 zurueckgesetzt werden (Reset-Taster oder USB-Reconnect), da die Firmware keine Reconnection-Logik hat.

**colcon build schlaegt fehl:**
Sicherstellen, dass alle Paketdateien vorhanden sind (`package.xml`, `setup.py`, `setup.cfg`, `resource/my_bot`, `my_bot/__init__.py`). Bei korruptem Build-Cache: `docker volume rm amr-docker_ros2_build amr-docker_ros2_install amr-docker_ros2_log` und erneut bauen.

**RViz2 zeigt kein Bild:**
X11-Zugriff erlauben: `xhost +local:docker` (wird von `run.sh` automatisch aufgerufen). Bei OpenGL-Problemen: `LIBGL_ALWAYS_SOFTWARE=1` setzen. Alternativ RViz2 auf separatem PC ausfuehren und per ROS2 DDS verbinden (`ROS_DOMAIN_ID=0`, `use_rviz:=False` auf dem Pi).

---

## Teil 3: Zusammenspiel ESP32 <-> Pi5 (Phase 7)

Alle folgenden Schritte setzen voraus, dass die Firmware erfolgreich geflasht wurde (Teil 1) und die ROS2-Docker-Umgebung funktionsfaehig ist (Teil 2, `./verify.sh` bestanden). Alle `ros2`-Befehle werden im Docker-Container ausgefuehrt -- entweder ueber `./run.sh <befehl>` vom Host oder direkt in einer interaktiven Container-Shell (`./run.sh`).

### 3.1 Topic-Verifikation

Der micro-ROS Agent wird bereits in Teil 2 (Abschnitt 2.7) getestet. Falls die Session steht, muessen `/cmd_vel` und `/odom` im ROS2-Graphen sichtbar sein:

```bash
./run.sh exec ros2 topic list          # /cmd_vel und /odom muessen erscheinen
./run.sh exec ros2 topic echo /odom --once   # Odometrie pruefen
./run.sh exec ros2 topic hz /odom      # Soll: 18-22 Hz
```

Wichtig: `header.frame_id` muss `"odom"` und `child_frame_id` muss `"base_link"` lauten. Bei manueller Raddrehung muessen sich die Odometrie-Werte sichtbar aendern. Falls sie bei Null bleiben, liegt ein Encoder- oder Firmware-Problem vor (siehe Abschnitt 3.5).

### 3.2 Failsafe-Test

Die Firmware stoppt die Motoren automatisch nach 500 ms ohne `cmd_vel` (`FAILSAFE_TIMEOUT_MS` in `config.h`). Test:

```bash
# Motoren starten (Raeder angehoben oder sichere Umgebung):
./run.sh exec ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}" --rate 10

# Ctrl+C -> Motoren muessen innerhalb von 500 ms stoppen
```

### 3.3 Full-Stack Launch

Das Launch-File `full_stack.launch.py` startet alle Subsysteme (micro-ROS Agent, SLAM Toolbox, Nav2, RViz2):

```bash
cd amr/docker/

# Vollstaendiger Stack (Standard):
./run.sh ros2 launch my_bot full_stack.launch.py

# Nur SLAM (Kartenerstellung, ohne Navigation):
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false

# Headless (ohne RViz2, spart CPU/GPU):
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False

# Nur Navigation mit bestehender Karte:
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False

# Mit Kamera (ArUco-Docking):
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True

# Alternativer serieller Port:
./run.sh ros2 launch my_bot full_stack.launch.py serial_port:=/dev/ttyUSB0

# Kombination:
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false use_rviz:=False serial_port:=/dev/ttyUSB0
```

SLAM-Konfiguration: `config/mapper_params_online_async.yaml` (Ceres-Solver, 5 cm Aufloesung, Loop Closure). Nav2-Konfiguration: `config/nav2_params.yaml` (AMCL, Regulated Pure Pursuit Controller 0.4 m/s, Navfn-Planer).

### 3.4 TF-Baum-Verifikation

Der Navigations-Stack benoetigt die vollstaendige TF-Kette:

```text
map -> odom -> base_link -> laser
                         -> camera_link (optional, bei use_camera:=True)
```

Verifikation:

```bash
# TF-Baum als PDF exportieren:
./run.sh exec ros2 run tf2_tools view_frames
docker cp amr_ros2:/ros2_ws/frames_*.pdf .

# Einzelne Transformation pruefen:
./run.sh exec ros2 run tf2_ros tf2_echo map base_link
```

Falls `map -> odom` fehlt, wurde die SLAM Toolbox noch nicht korrekt gestartet oder hat noch keine Scan-Daten empfangen.

### 3.5 Troubleshooting Kommunikation

| Problem | Loesung |
|---------|---------|
| Agent findet ESP32 nicht | `ls /dev/ttyACM*` pruefen (Host + Container). USB-Datenkabel verwenden. Ggf. ESP32 neu flashen. |
| Topics `/cmd_vel` und `/odom` fehlen | micro-ROS-Session nicht aufgebaut. Agent-Terminal auf Fehler pruefen. `ROS_DOMAIN_ID=0` sicherstellen. |
| `Package 'my_bot' not found` | Workspace einmalig bauen: `./run.sh colcon build --packages-select my_bot --symlink-install` |
| Odom-Werte aendern sich nicht bei Raddrehung | Encoder-Pins D6/D7 pruefen. Phase B isoliert? `ros2 run my_bot encoder_test` zur Diagnose. |
| Motoren reagieren nicht auf `cmd_vel` | PWM-Deadzone (35) erfordert mind. 0.05 m/s. `cmd_vel` muss alle 500 ms erneut gesendet werden (Failsafe). |

Weitere Probleme zu Serial-Ports und Docker siehe Abschnitt 2.8.

---

## Teil 4: Kalibrierung und Validierung (Phasen 4-9)

Die systematische Kalibrierung und Validierung des Gesamtsystems ist in einer separaten Anleitung dokumentiert:

-> **`hardware/docs/kalibrierung_anleitung.md`**

Diese Anleitung deckt ab:
- Kinematik-Validierung (Geradeausfahrt, Drehung, Kreisfahrt)
- UMBmark-Kalibrierung nach Borenstein & Feng (1996)
- PID-Re-Tuning (Sprungantwort-Analyse)
- SLAM-Validierung (ATE-Berechnung)
- Navigations-Validierung (Waypoint-Parcours)
- Docking-Validierung (ArUco-Marker)
- Gesamt-Validierungsbericht

**Voraussetzung:** Teile 1-3 dieser Anleitung muessen erfolgreich abgeschlossen sein.

---

## Anhang A: Akzeptanzkriterien

Die folgende Tabelle fasst alle Akzeptanzkriterien des V-Modell-Validierungsplans zusammen.

| Nr.   | Phase | Testbereich | Kriterium                         | Schwellwert                                    | Messmethode                                           |
|-------|-------|-------------|-----------------------------------|------------------------------------------------|-------------------------------------------------------|
| AK-01 | 2     | Encoder     | Wiederholgenauigkeit Ticks/Rev    | Abweichung < 2 Ticks/Rev zwischen Durchgaengen | 10-Umdrehungen-Test (encoder_test), 3x wiederholen    |
| AK-02 | 2     | Encoder     | Ticks/Rev im Sollbereich          | 370-380 Ticks/Rev (A-only Hall)                | 10-Umdrehungen-Test, Mittelwert aus 3 Durchgaengen    |
| AK-03 | 2     | Encoder     | Links/Rechts-Asymmetrie           | < 5 %                                          | Identischer PWM-Wert, 10 s Laufzeit, Tick-Vergleich   |
| AK-04 | 3     | Motor       | PWM-Deadzone                      | Anlauf-PWM im Bereich 30-40                    | motor_test, schrittweise PWM-Erhoehung                 |
| AK-05 | 3     | Motor       | Failsafe-Timeout                  | Motoren stoppen innerhalb 500 ms ohne cmd_vel  | cmd_vel unterbrechen, Stoppzeit messen                 |
| AK-06 | 4     | Kinematik   | Geradeausfahrt Streckenabweichung | < 5 % auf 1 m                                  | kinematic_test, Geradeausfahrt-Test                    |
| AK-07 | 4     | Kinematik   | Geradeausfahrt laterale Drift     | < 5 cm auf 1 m                                 | kinematic_test, Geradeausfahrt-Test                    |
| AK-08 | 4     | Kinematik   | 90-Grad-Drehung Winkelabweichung  | < 5 Grad                                       | kinematic_test, 5x CW + 5x CCW                        |
| AK-09 | 5     | UMBmark     | Fehlerreduktion nach Kalibrierung | Faktor >= 10                                   | umbmark_analysis, Vergleich vor/nach                   |
| AK-10 | 6     | PID         | Anstiegszeit (10%-90%)            | < 500 ms                                       | pid_tuning, Sprungantwort 0 -> 0,4 m/s                |
| AK-11 | 6     | PID         | Ueberschwingen                    | < 15 %                                         | pid_tuning, Sprungantwort-Analyse                      |
| AK-12 | 6     | PID         | Einschwingzeit (+/- 5%)           | < 1,0 s                                        | pid_tuning, Sprungantwort-Analyse                      |
| AK-13 | 6     | PID         | Stationaerer Regelfehler          | < 5 %                                          | pid_tuning, letzte 20% der Messdaten                   |
| AK-14 | 7     | micro-ROS   | Odometrie-Publikationsrate        | 20 Hz +/- 2 Hz                                 | ros2 topic hz /odom, 5 min Messung                     |
| AK-15 | 7     | micro-ROS   | Paketverlust                      | < 0,1 %                                        | ros2 topic hz /odom -w 1000, 60 s Messung              |
| AK-16 | 8     | SLAM        | Absolute Trajectory Error (ATE)   | < 0,20 m (RMSE)                                | slam_validation, Live-Modus 120 s                      |
| AK-17 | 8     | Navigation  | Positionsfehler xy                | < 10 cm                                        | nav_test, 4-Waypoint-Parcours                          |
| AK-18 | 8     | Navigation  | Orientierungsfehler Gier          | < 8 Grad (0,15 rad)                            | nav_test, 4-Waypoint-Parcours                          |
| AK-19 | 9     | Docking     | Erfolgsquote                      | >= 80 % (8/10 Versuche)                        | docking_test, 10 Versuche                              |

---

## Anhang B: Referenztabelle Validierungsskripte

Alle Validierungsskripte liegen in `amr/scripts/`. Die detaillierte Kalibrierungsanleitung mit Schritt-fuer-Schritt-Ablauf findet sich in `hardware/docs/kalibrierung_anleitung.md`.

**Hinweis:** Alle ROS2-Befehle (`ros2 run my_bot ...`) werden im Docker-Container ausgefuehrt. Vom Host: `cd amr/docker/ && ./run.sh exec ros2 run my_bot <node>`. Die Entry-Points werden ohne `.py`-Suffix aufgerufen.

| Skript                 | Phase          | ROS2 | Aufruf                                                       | Beschreibung                                                     | Akzeptanzkriterium                            |
|------------------------|----------------|------|--------------------------------------------------------------|------------------------------------------------------------------|-----------------------------------------------|
| `pre_flight_check.py`  | 1 (Pre-Flash)  | Nein | `python3 pre_flight_check.py`                                | Interaktive Hardware-Checkliste mit Markdown-Protokoll           | Alle Checks bestanden (0 FAIL)                |
| `encoder_test.py`      | 2 (Encoder)    | Ja   | `ros2 run my_bot encoder_test`                               | 10-Umdrehungen-Test, Richtungs- und Asymmetrie-Pruefung         | AK-01 bis AK-03                               |
| `motor_test.py`        | 3 (Motoren)    | Ja   | `ros2 run my_bot motor_test`                                 | Deadzone-, Richtungs-, Failsafe- und Rampen-Test                | AK-04, AK-05                                  |
| `pid_tuning.py`        | 6 (PID)        | Ja   | `ros2 run my_bot pid_tuning live`                            | PID-Sprungantwort: Anstiegszeit, Ueberschwingen, Einschwingzeit | AK-10 bis AK-13                               |
| `kinematic_test.py`    | 4 (Kinematik)  | Ja   | `ros2 run my_bot kinematic_test`                             | Geradeaus-, Dreh- und Kreisfahrt-Verifikation                   | AK-06 bis AK-08                               |
| `umbmark_analysis.py`  | 5 (UMBmark)    | Nein | `python3 umbmark_analysis.py`                                | UMBmark-Auswertung nach Borenstein (1996), Korrekturfaktoren    | AK-09                                         |
| `slam_validation.py`   | 8 (SLAM)       | Ja   | `ros2 run my_bot slam_validation --live --duration 120`      | ATE-Berechnung und TF-Ketten-Pruefung                           | AK-16                                         |
| `nav_test.py`          | 8 (Navigation) | Ja   | `ros2 run my_bot nav_test`                                   | 4-Waypoint-Navigationstest mit Positions-/Gierfehler            | AK-17, AK-18                                  |
| `docking_test.py`      | 9 (Docking)    | Ja   | `ros2 run my_bot docking_test`                               | 10-Versuch ArUco-Docking mit Erfolgsquote                       | AK-19                                         |
| `validation_report.py` | 9 (Report)     | Nein | `python3 validation_report.py`                               | Gesamt-Report aus JSON-Ergebnissen aller Tests                  | Alle 14 Kriterien PASS                        |

**Zusaetzliche Entry-Points** (keine Validierungsskripte):

| Entry-Point       | Aufruf                           | Beschreibung                                              |
|--------------------|----------------------------------|-----------------------------------------------------------|
| `aruco_docking`    | `ros2 run my_bot aruco_docking`  | Visual-Servoing-Node fuer ArUco-Marker-Docking            |
| `odom_to_tf`       | `ros2 run my_bot odom_to_tf`     | Publiziert odom->base_link TF aus /odom-Nachrichten       |

---

## Anhang C: Referenztabelle Quelldateien

Alle Pfade relativ zum Projekt-Root (`AMR-Bachelorarbeit/`).

### C.1 ESP32 Firmware

| Datei                     | Pfad                                                   | Beschreibung                                                       |
|---------------------------|--------------------------------------------------------|--------------------------------------------------------------------|
| main.cpp                  | `amr/esp32_amr_firmware/src/main.cpp`                  | FreeRTOS-Tasks, micro-ROS, Subscriber/Publisher, Safety-Mechanismen |
| robot_hal.hpp             | `amr/esp32_amr_firmware/src/robot_hal.hpp`             | Hardware-Abstraktion: GPIO, Encoder-ISR, PWM, Deadzone              |
| pid_controller.hpp        | `amr/esp32_amr_firmware/src/pid_controller.hpp`        | PID-Regler mit Anti-Windup, Ausgang [-1.0, 1.0]                    |
| diff_drive_kinematics.hpp | `amr/esp32_amr_firmware/src/diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik, Odometrie-Update                       |
| platformio.ini            | `amr/esp32_amr_firmware/platformio.ini`                | Build-Konfiguration: Board, Framework, micro-ROS-Bibliothek         |

### C.2 Zentrale Konfiguration

| Datei    | Pfad                | Beschreibung                                                                        |
|----------|---------------------|-------------------------------------------------------------------------------------|
| config.h | `hardware/config.h` | Single Source of Truth: Pin-Mapping, Kinematik, Encoder, PWM, Safety, static_assert |

### C.3 Hardware-Dokumentation

| Datei                       | Pfad                                        | Beschreibung                                                     |
|-----------------------------|---------------------------------------------|------------------------------------------------------------------|
| hardware-setup.md           | `hardware/docs/hardware-setup.md`           | Physischer Aufbau: Stromversorgung, Verkabelung, Pin-Mapping     |
| kalibrierung_anleitung.md   | `hardware/docs/kalibrierung_anleitung.md`   | Schritt-fuer-Schritt Kalibrierungsanleitung (UMBmark, PID etc.) |
| kosten.md                   | `hardware/docs/kosten.md`                   | Stueckliste mit Kostenaufstellung                                |

### C.4 ROS2-Paket (Raspberry Pi)

| Datei                           | Pfad                                                                | Beschreibung                                                          |
|---------------------------------|---------------------------------------------------------------------|-----------------------------------------------------------------------|
| nav2_params.yaml                | `amr/pi5/ros2_ws/src/my_bot/config/nav2_params.yaml`                | Nav2-Stack: AMCL, Regulated Pure Pursuit, Costmaps, Recovery          |
| mapper_params_online_async.yaml | `amr/pi5/ros2_ws/src/my_bot/config/mapper_params_online_async.yaml` | SLAM Toolbox: Ceres-Solver, 5 cm Aufloesung, Loop Closure             |
| full_stack.launch.py            | `amr/pi5/ros2_ws/src/my_bot/launch/full_stack.launch.py`            | Launch-File: micro-ROS + SLAM + Nav2 + RViz2 + Kamera (optional)     |
| aruco_docking.py                | `amr/pi5/ros2_ws/src/my_bot/scripts/aruco_docking.py`               | Visual Servoing mit ArUco-Markern (OpenCV >= 4.7)                     |
| odom_to_tf.py                   | `amr/pi5/ros2_ws/src/my_bot/my_bot/odom_to_tf.py`                   | Odom-zu-TF-Bridge: publiziert odom->base_footprint                   |

### C.5 Validierungsskripte

| Datei                | Pfad                               | ROS2 | Beschreibung                                                    |
|----------------------|------------------------------------|------|-----------------------------------------------------------------|
| pre_flight_check.py  | `amr/scripts/pre_flight_check.py`  | Nein | Interaktive Hardware-Checkliste mit Markdown-Protokoll          |
| encoder_test.py      | `amr/scripts/encoder_test.py`      | Ja   | 10-Umdrehungen-Test, Richtungs- und Asymmetrie-Pruefung        |
| motor_test.py        | `amr/scripts/motor_test.py`        | Ja   | Deadzone-, Richtungs-, Failsafe- und Rampen-Test               |
| pid_tuning.py        | `amr/scripts/pid_tuning.py`        | Ja   | PID-Sprungantwort-Analyse mit Tuning-Empfehlungen              |
| kinematic_test.py    | `amr/scripts/kinematic_test.py`    | Ja   | Geradeaus-, Dreh- und Kreisfahrt-Verifikation                  |
| umbmark_analysis.py  | `amr/scripts/umbmark_analysis.py`  | Nein | UMBmark-Auswertung nach Borenstein (1996), Korrekturfaktoren   |
| slam_validation.py   | `amr/scripts/slam_validation.py`   | Ja   | ATE-Berechnung und TF-Ketten-Pruefung                          |
| nav_test.py          | `amr/scripts/nav_test.py`          | Ja   | 4-Waypoint-Navigation mit Positions-/Gierfehler-Messung        |
| docking_test.py      | `amr/scripts/docking_test.py`      | Ja   | 10-Versuch ArUco-Docking-Test mit Erfolgsquote                 |
| validation_report.py | `amr/scripts/validation_report.py` | Nein | Gesamt-Report aus JSON-Ergebnissen aller Validierungsskripte   |

### C.6 Docker-Konfiguration

Alle Dateien im Verzeichnis `amr/docker/`. Sie stellen die ROS2-Humble-Umgebung via Docker auf dem Raspberry Pi 5 (Debian Trixie) bereit.

| Datei              | Pfad                            | Beschreibung                                                        |
|--------------------|---------------------------------|---------------------------------------------------------------------|
| Dockerfile         | `amr/docker/Dockerfile`         | Image auf Basis `ros:humble-ros-base` (arm64), micro-ROS aus Source |
| docker-compose.yml | `amr/docker/docker-compose.yml` | Service: network_mode host, privileged, Volume-Mounts               |
| entrypoint.sh      | `amr/docker/entrypoint.sh`      | Sourced ROS2 Humble + micro-ROS + Projekt-Workspace automatisch     |
| run.sh             | `amr/docker/run.sh`             | Convenience-Wrapper: Shell, Befehle, zweites Terminal               |
| verify.sh          | `amr/docker/verify.sh`          | Automatisierter Gesamttest (dynamische Check-Anzahl)                |
| host_setup.sh      | `amr/docker/host_setup.sh`      | Einmalige Host-Einrichtung: Gruppen, udev, X11, Kamera             |
