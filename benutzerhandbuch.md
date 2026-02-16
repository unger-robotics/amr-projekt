# Benutzerhandbuch: Autonomer Mobiler Roboter (AMR)

## 1. Voraussetzungen

### Hardware

- Raspberry Pi 5 (8 GB) mit Debian Trixie
- XIAO ESP32-S3 (geflasht mit AMR-Firmware) ueber USB-C am Pi angeschlossen
- Cytron MDD3A Motortreiber mit zwei JGA25-370 Motoren (Hall-Encoder)
- RPLIDAR A1 (ueber USB am Pi angeschlossen)
- 3S1P Li-Ion Akkupack (11.1-12.6 V) mit 15-A-Sicherung
- Raspberry Pi Global Shutter Camera (IMX296) mit CSI-Adapter (22-pin Mini auf 15-pin)
- MPU6050 IMU (I2C an D4/D5)

### Software

- Docker (>= 20.x) und Docker Compose (>= 2.x) auf dem Pi installiert
- PlatformIO CLI (`pip install platformio`) fuer Firmware-Updates
- Benutzer muss in den Gruppen `docker`, `dialout` und `video` sein

Gruppenzugehoerigkeit pruefen:

```bash
id -nG    # Ausgabe muss docker, dialout, video enthalten
```

---

## 2. Ersteinrichtung

Die Ersteinrichtung ist einmalig erforderlich. Danach genuegt der Schnellstart (Abschnitt 3).

### 2.1 Host-Setup ausfuehren

Das Skript richtet udev-Regeln, Gruppenzugehoerigkeiten, X11-Zugriff und die Kamera-Bridge ein:

```bash
cd amr/docker/
sudo bash host_setup.sh
```

Nach Ausfuehrung ab- und wieder anmelden (damit Gruppenaenderungen wirksam werden).

### 2.2 Docker-Image bauen

```bash
cd amr/docker/
docker compose build    # Erster Durchlauf: ~15-20 Min, danach gecached
```

### 2.3 Setup verifizieren

```bash
cd amr/docker/
./verify.sh
```

Bei Ausgabe "Verifikation BESTANDEN" (0 FAIL) ist das Setup vollstaendig.

### 2.4 ESP32-Firmware flashen

Falls die Firmware noch nicht auf dem ESP32 ist oder ein Update noetig ist:

```bash
cd amr/esp32_amr_firmware/
pio run -t upload    # Flashen (921600 Baud)
```

Die Status-LED (D10) zeigt den Zustand an:
- Langsames Blinken: Firmware sucht micro-ROS Agent (normal vor Container-Start)
- Schnelles Blinken: Initialisierungsfehler (Agent-Konfiguration pruefen)
- Gedimmt/Heartbeat: Betriebsbereit

### 2.5 ROS2-Workspace bauen

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install
```

---

## 3. Inbetriebnahme (Schnellstart)

### Schritt 1: Serial-Port freigeben

Vor dem Start sicherstellen, dass kein anderer Dienst den ESP32-Port belegt:

```bash
sudo systemctl stop embedded-bridge.service    # Falls aktiv
sudo fuser -v /dev/ttyACM0                     # Port muss frei sein
```

### Schritt 2: Roboter einschalten

1. Akkupack anschliessen (Hauptsicherung pruefen)
2. USB-C-Kabel zwischen ESP32 und Pi pruefen
3. RPLIDAR A1 per USB anschliessen
4. Warten bis Status-LED am ESP32 langsam blinkt (Agent-Suche)

### Schritt 3: ROS2-Stack starten

```bash
cd amr/docker/

# Vollstaendiger Stack (SLAM + Navigation + RViz2):
./run.sh ros2 launch my_bot full_stack.launch.py

# Nur Kartenerstellung (ohne Navigation):
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false

# Headless-Modus (ohne RViz2, spart Ressourcen):
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False
```

### Schritt 4: Verbindung pruefen

In einem zweiten Terminal:

```bash
cd amr/docker/
./run.sh exec ros2 topic list           # /cmd_vel und /odom muessen erscheinen
./run.sh exec ros2 topic hz /odom       # Soll: 18-22 Hz
./run.sh exec ros2 topic echo /odom --once   # Odometrie-Werte pruefen
```

---

## 4. Betriebsmodi

### 4.1 SLAM-Modus (Kartenerstellung)

Erstellt eine 2D-Karte der Umgebung mittels SLAM Toolbox:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false
```

Den Roboter langsam durch die Umgebung fahren (manuell via Teleop oder Fernsteuerung). Die Karte wird in Echtzeit aufgebaut. Karte speichern:

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map
```

### 4.2 Navigationsmodus

Autonome Navigation auf einer bestehenden Karte:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False
```

Waypoints koennen ueber RViz2 ("2D Nav Goal") oder programmatisch gesetzt werden. Der Regulated Pure Pursuit Controller steuert den Roboter mit maximal 0.4 m/s.

### 4.3 Kamera und ArUco-Docking

Fuer praezises Andocken an ArUco-Marker:

```bash
# Kamera-Bridge auf dem Host starten (falls nicht automatisch):
sudo systemctl start camera-v4l2-bridge.service

# ROS2-Stack mit Kamera:
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True
```

Das Visual-Servoing-Modul erkennt ArUco-Marker und steuert den Roboter zur Docking-Position.

### 4.4 Manuelles Fahren (Teleop)

Einzelne Geschwindigkeitskommandos senden:

```bash
./run.sh exec ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --rate 10
```

Stopp: Ctrl+C (Failsafe stoppt Motoren automatisch nach 500 ms).

---

## 5. Validierung und Diagnose

### 5.1 Pre-Flight-Checkliste

Interaktive Hardware-Pruefung (kein ROS2 erforderlich):

```bash
python3 amr/scripts/pre_flight_check.py
```

Prueft USB-Enumeration, Spannungsversorgung, Pin-Belegung, Firmware-Status und Sensoren. Erzeugt ein Markdown-Protokoll.

### 5.2 Hardware-Report

```bash
python3 amr/scripts/hardware_info.py
```

Generiert einen Zeitstempel-Markdown-Report mit System- und Hardware-Informationen.

### 5.3 Validierungsskripte (ROS2 erforderlich)

Alle Skripte werden im Docker-Container ausgefuehrt. Der micro-ROS Agent muss laufen.

| Befehl                                          | Funktion                                         |
|-------------------------------------------------|--------------------------------------------------|
| `./run.sh exec ros2 run my_bot encoder_test`    | Encoder-Kalibrierung (10-Umdrehungen-Test)       |
| `./run.sh exec ros2 run my_bot motor_test`      | Motor-Deadzone, Richtung, Failsafe               |
| `./run.sh exec ros2 run my_bot pid_tuning`      | PID-Sprungantwort-Analyse                        |
| `./run.sh exec ros2 run my_bot kinematic_test`  | Geradeaus-/Dreh-/Kreisfahrt                      |
| `./run.sh exec ros2 run my_bot imu_test`        | Gyro-Drift und Accelerometer-Bias (60s statisch) |
| `./run.sh exec ros2 run my_bot slam_validation` | ATE-Berechnung und TF-Ketten-Check               |
| `./run.sh exec ros2 run my_bot nav_test`        | 4-Waypoint-Navigation mit Fehler-Messung         |
| `./run.sh exec ros2 run my_bot docking_test`    | 10-Versuch ArUco-Docking-Test                    |

Gesamt-Report aus allen JSON-Ergebnissen:

```bash
python3 amr/scripts/validation_report.py
```

### 5.4 Debug-Kommandos

```bash
# Topics und Frequenzen:
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /scan              # LiDAR: ~7.6 Hz erwartet
./run.sh exec ros2 topic hz /odom              # Odometrie: ~20 Hz erwartet

# TF-Baum pruefen:
./run.sh exec ros2 run tf2_ros tf2_echo odom base_link
./run.sh exec ros2 run tf2_ros tf2_echo base_link laser

# TF-Baum als PDF exportieren:
./run.sh exec ros2 run tf2_tools view_frames
```

---

## 7. Sicherheitshinweise

1. **Akku-Sicherheit**: Nur 3S Li-Ion Akkupacks mit integriertem BMS verwenden. Hauptsicherung (15 A) niemals ueberbruecken. Bei Beschaedigung oder Aufblaehen des Akkus sofort vom Roboter trennen.

2. **Motortest**: Bei erstmaliger Inbetriebnahme und Motortests den Roboter stets aufbocken (Raeder frei drehend) oder in sicherer Umgebung betreiben. Ctrl+C sendet sofort einen Stopp-Befehl.

3. **Failsafe**: Die Firmware stoppt die Motoren automatisch nach 500 ms ohne `cmd_vel`-Nachricht. Diesen Mechanismus nicht deaktivieren.

4. **Beaufsichtigung**: Den Roboter waehrend autonomer Navigation nicht unbeaufsichtigt lassen. Die Hinderniserkennung basiert ausschliesslich auf dem 2D-LiDAR und erfasst keine niedrigen oder ueberstehenden Hindernisse.

5. **Stromversorgung**: Gemeinsame Masse (Sternpunkt-GND) zwischen Pi, Buck-Converter, Motortreiber und ESP32 sicherstellen. Fehlende Masseverbindungen koennen zu undefiniertem Verhalten fuehren.

6. **ESP32-Reset**: Nach einem Neustart des micro-ROS Agents muss der ESP32 per Reset-Taster oder USB-Reconnect zurueckgesetzt werden, da die Firmware keine automatische Reconnection unterstuetzt.

7. **Serial-Port-Konflikte**: Vor dem Start des AMR-Stacks sicherstellen, dass kein anderer Dienst (`embedded-bridge.service`, `selection-panel.service`) den ESP32-Port belegt. Paralleler Zugriff fuehrt zu Datenverlust.
