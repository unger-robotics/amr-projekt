# Benutzerhandbuch: Autonomer mobiler Roboter (AMR)

## 1. Voraussetzungen

### 1.1 Hardware

Fuer den Betrieb werden die folgenden Hardware-Komponenten benoetigt:

- Raspberry Pi 5 mit 8 GB RAM und Debian Trixie
- zwei XIAO ESP32-S3 als Drive-Knoten und Sensor-Knoten, jeweils per USB-C mit dem Raspberry Pi verbunden
- Cytron MDD3A Motortreiber mit zwei JGA25-370-Gleichstrommotoren inklusive Hall-Encoder
- RPLIDAR A1, per USB mit dem Raspberry Pi verbunden
- 3S1P-Li-Ion-Akkupack mit 10,8 bis 12,6 V und 10 A Sicherung
- Raspberry Pi Global Shutter Camera IMX296 mit CSI-Adapter von 22-polig Mini auf 15-polig
- MPU6050-IMU, per I2C an D4 und D5 des Sensor-Knotens angebunden
- Hailo-8L PCIe-KI-Beschleuniger ueber M.2-Anbindung am Raspberry Pi 5
- PCM5102A-I2S-DAC (HifiBerry DAC) mit Lautsprecher an den I2S-Pins des Raspberry Pi 5
- Infrarot-Kanten-Sensor MH-B an den GPIOs des Sensor-Knotens

### 1.2 Software

Fuer den Betrieb werden die folgenden Software-Komponenten benoetigt:

- Docker ab Version 20.x
- Docker Compose ab Version 2.x
- PlatformIO CLI, installiert ueber `pip install platformio`
- zwei Firmware-Verzeichnisse unter `mcu_firmware/drive_node/` und `mcu_firmware/sensor_node/`
- ein gueltiger Gemini-API-Schluessel als Umgebungsvariable `GEMINI_API_KEY`

Das Benutzerkonto muss Mitglied der Gruppen `docker`, `dialout`, `video` und `audio` sein.

Gruppenzugehoerigkeit pruefen:

```bash
id -nG

```

Die Ausgabe muss `docker`, `dialout`, `video` und `audio` enthalten.

---

## 2. Ersteinrichtung

Die Ersteinrichtung ist nur einmal erforderlich. Danach genuegt der Schnellstart aus Abschnitt 3.

### 2.1 Host-Setup ausfuehren

Das Host-Setup richtet udev-Regeln, Gruppenzugehoerigkeiten, X11-Zugriff und die Kamera-Bridge ein.

```bash
cd amr/docker/
sudo bash host_setup.sh

```

Nach Abschluss muessen Benutzerkonto und Sitzung neu angemeldet werden, damit Gruppenaenderungen wirksam werden.

### 2.2 Docker-Image bauen

```bash
cd amr/docker/
docker compose build

```

Der erste Build benoetigt deutlich mehr Zeit als spaetere, gecachte Builds.

### 2.3 Setup verifizieren

```bash
cd amr/docker/
./verify.sh

```

Die Ausgabe `Verifikation BESTANDEN` mit `0 FAIL` bestaetigt ein vollstaendiges Setup.

### 2.4 Firmware der ESP32-S3 flashen

Die Firmware muss auf beiden Knoten vorhanden sein. Updates werden getrennt fuer Drive-Knoten und Sensor-Knoten eingespielt.

Drive-Knoten flashen:

```bash
cd amr/mcu_firmware/drive_node/
pio run -t upload

```

Sensor-Knoten flashen:

```bash
cd amr/mcu_firmware/sensor_node/
pio run -t upload

```

Die Upload-Geschwindigkeit betraegt 921600 Baud.

Die Status-LED an D10 des Drive-Knotens signalisiert den Betriebszustand:

* langsames Blinken: Suche nach dem micro-ROS-Agenten, normal vor dem Container-Start
* schnelles Blinken: Initialisierungsfehler, Agent-Konfiguration pruefen
* gedimmtes Heartbeat-Muster: Betriebsbereitschaft

### 2.5 ROS-2-Workspace bauen

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install

```

---

## 3. Inbetriebnahme (Schnellstart)

### 3.1 Serielle Schnittstellen freigeben

Vor dem Start muessen die seriellen Schnittstellen frei sein. Andere Dienste duerfen die Geraete `/dev/amr_drive` und `/dev/amr_sensor` nicht belegen.

```bash
sudo systemctl stop embedded-bridge.service
sudo fuser -v /dev/amr_drive /dev/amr_sensor

```

Die Ausgabe von `fuser` darf keine aktiven Prozesse fuer beide Geraete zeigen.

### 3.2 Roboter einschalten

Die Inbetriebnahme erfolgt in vier Schritten:

1. Akkupack anschliessen und Hauptsicherung pruefen.
2. USB-C-Verbindungen zwischen beiden ESP32-S3-Knoten und dem Raspberry Pi pruefen.
3. RPLIDAR A1 per USB anschliessen.
4. Warten, bis die Status-LED des Drive-Knotens langsam blinkt.

Langsames Blinken zeigt die Suche nach dem micro-ROS-Agenten an.

### 3.3 ROS-2-Stack starten

Vollstaendigen Stack mit Lokalisierung und Kartierung, Navigation, Bedien- und Leitstandsebene, Vision und Audio starten:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True

```

Headless-Betrieb ohne RViz2 starten:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True

```

Der Host-Prozess `host_hailo_runner` muss separat auf dem Host-System laufen, damit die hardwarebeschleunigte Bildverarbeitung verfuegbar ist.

### 3.4 Verbindung pruefen

In einem zweiten Terminal die verfuegbaren Topics und Frequenzen pruefen:

```bash
cd amr/docker/
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /cliff

```

Erwartete Werte:

* `/odom`: etwa 18 bis 22 Hz
* `/cliff`: etwa 20 Hz

---

## 4. Betriebsmodi

### 4.1 Modus fuer Lokalisierung und Kartierung

Dieser Modus erzeugt eine zweidimensionale Karte der Umgebung mit `slam_toolbox`.

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false

```

Fuer den Kartenaufbau den Roboter langsam manuell durch die Umgebung bewegen, zum Beispiel per Teleoperation oder Fernsteuerung.

Karte speichern:

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map

```

### 4.2 Navigationsmodus

Dieser Modus nutzt eine vorhandene Karte fuer autonome Zielanfahrt.

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False

```

Zielpunkte koennen ueber RViz2 mit `2D Nav Goal` oder programmatisch gesetzt werden. Der Regulated-Pure-Pursuit-Controller begrenzt die Fahrgeschwindigkeit auf maximal 0,4 m/s.

### 4.3 Bedien- und Leitstandsebene mit Vision

Dieser Modus stellt Dashboard, Kamerabild und Vision-Pipeline bereit.

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_vision:=True use_camera:=True

```

Ablauf:

1. Benutzeroberflaeche im Browser unter `http://<IP-des-Raspberry-Pi>:5173` oeffnen.
2. Live-Bild ueber den MJPEG-Stream an Port 8082 pruefen.
3. Lokale Objekterkennung ueber Hailo-8L und semantische Auswertung ueber externes Sprachmodell als Overlay ueber WebSocket an Port 9090 pruefen.

### 4.4 Manuelles Fahren

Geschwindigkeitskommando direkt an den Fahrkern senden:

```bash
./run.sh exec ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --rate 10

```

Das Beenden mit `Ctrl+C` stoppt die Kommandouebertragung. Zusaetzlich stoppt der Failsafe die Motoren automatisch nach 500 ms ohne neue Geschwindigkeitskommandos.

---

## 5. Validierung und Diagnose

### 5.1 Pre-Flight-Checkliste

Die Pre-Flight-Pruefung arbeitet ohne laufenden ROS-2-Stack.

```bash
python3 amr/scripts/pre_flight_check.py

```

Das Skript prueft USB-Enumeration, Spannungsversorgung, Pin-Belegung, Firmware-Status und Sensorik. Anschliessend erzeugt das Skript ein Protokoll im Markdown-Format.

### 5.2 Hardware-Report

```bash
python3 amr/scripts/hardware_info.py

```

Das Skript erzeugt einen zeitgestempelten Markdown-Report mit System- und Hardware-Informationen.

### 5.3 Validierungsskripte im ROS-2-Betrieb

Fuer alle Befehle in diesem Abschnitt muessen die micro-ROS-Agenten laufen.

| Befehl                                          | Funktion                                                             |
|-------------------------------------------------|----------------------------------------------------------------------|
| `./run.sh exec ros2 run my_bot encoder_test`    | Encoder-Kalibrierung mit 10-Umdrehungen-Test                         |
| `./run.sh exec ros2 run my_bot motor_test`      | Pruefung von Motor-Deadzone, Drehrichtung und Failsafe               |
| `./run.sh exec ros2 run my_bot pid_tuning`      | Analyse der PID-Sprungantwort                                        |
| `./run.sh exec ros2 run my_bot kinematic_test`  | Pruefung von Geradeausfahrt, Drehfahrt und Kreisfahrt                |
| `./run.sh exec ros2 run my_bot imu_test`        | Pruefung von Gyro-Drift und Beschleunigungs-Bias bei 60 s Stillstand |
| `./run.sh exec ros2 run my_bot slam_validation` | Berechnung des Absolute Trajectory Error und Pruefung der TF-Kette   |
| `./run.sh exec ros2 run my_bot nav_test`        | Navigationstest mit vier Wegpunkten und Fehlermessung                |
| `./run.sh exec ros2 run my_bot docking_test`    | ArUco-Docking-Test mit 10 Versuchen                                  |
| `./run.sh exec ros2 run my_bot cliff_test`      | Pruefung des Kanten-Notstopps ueber die Sicherheitslogik             |

Gesamt-Report aus allen JSON-Ergebnissen erzeugen:

```bash
python3 amr/scripts/validation_report.py

```

### 5.4 Diagnosebefehle

Topics und Frequenzen pruefen:

```bash
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /cliff

```

Erwartete Richtwerte:

* `/scan`: etwa 7,5 Hz
* `/odom`: etwa 20 Hz
* `/cliff`: etwa 20 Hz

TF-Kette pruefen:

```bash
./run.sh exec ros2 run tf2_ros tf2_echo odom base_link
./run.sh exec ros2 run tf2_ros tf2_echo base_link ultrasonic_link

```

TF-Baum als PDF exportieren:

```bash
./run.sh exec ros2 run tf2_tools view_frames

```

---

## 6. Betriebslogik und Sicherheitslogik

### 6.1 Rollen der Knoten

Der Drive-Knoten bildet den Fahrkern. Der Knoten verarbeitet Geschwindigkeitskommandos, regelt die Motoren und publiziert Odometrie.

Der Sensor-Knoten bildet die Sensor- und Sicherheitsbasis. Der Knoten verarbeitet IMU, Batterieueberwachung, Kanten-Sensor und weitere hardwarenahe Signale.

Der Raspberry Pi 5 uebernimmt Lokalisierung und Kartierung, Navigation, Bedien- und Leitstandsebene, Vision und Audio.

### 6.2 Prioritaet der Sicherheitslogik

Die Sicherheitslogik hat stets Vorrang vor Navigation und manueller Bedienung. Meldet der Kanten-Sensor eine kritische Situation, blockiert die Sicherheitslogik eingehende Bewegungsbefehle und erzeugt ein Stop-Kommando mit Nullgeschwindigkeit.

Diese Prioritaetsregel gilt unabhaengig davon, ob das Kommando aus der Navigation, der Bedien- und Leitstandsebene oder aus einem Testskript stammt.

### 6.3 Freigabelogik fuer spaetere Sprachschnittstelle

Eine spaetere Sprachschnittstelle darf keine direkte Motoransteuerung ausloesen. Zulaessig ist nur die Kette aus Sprachbefehl, Intent, Freigabelogik und freigegebenem Missionskommando.

Nicht zulaessig ist die Kette:

> Sprachbefehl -> direkte Motoransteuerung

Zulaessig ist die Kette:

> Sprachbefehl -> Intent -> Freigabelogik -> Missionskommando -> Navigation oder Bedien- und Leitstandsebene

---

## 7. Haeufige Fehlerbilder

### 7.1 `/odom` erscheint nicht

Moegliche Ursachen:

* micro-ROS-Agent laeuft nicht
* serielle Schnittstelle ist belegt
* Drive-Knoten wurde nicht korrekt geflasht

Pruefschritte:

```bash
sudo fuser -v /dev/amr_drive
./run.sh exec ros2 topic list

```

### 7.2 Kanten-Sensor stoppt nicht

Moegliche Ursachen:

* Sensor-Knoten laeuft nicht
* Topic `/cliff` publiziert nicht
* Sicherheitslogik ist nicht gestartet

Pruefschritte:

```bash
./run.sh exec ros2 topic echo /cliff
./run.sh exec ros2 topic hz /cliff

```

### 7.3 Dashboard zeigt kein Kamerabild

Moegliche Ursachen:

* Kamera-Bridge laeuft nicht
* MJPEG-Stream an Port 8082 ist nicht erreichbar
* `host_hailo_runner` oder Kamerazugriff auf dem Host fehlen

Pruefschritte:

```bash
./run.sh exec ros2 topic list
curl [http://127.0.0.1:8082](http://127.0.0.1:8082)

```

### 7.4 Navigation startet nicht

Moegliche Ursachen:

* keine gueltige Karte vorhanden
* TF-Kette ist unvollstaendig
* Laserscan oder Odometrie fehlen

Pruefschritte:

```bash
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 run tf2_ros tf2_echo map odom

```

---

## 8. Kurzreferenz

### 8.1 Vollstaendigen Stack starten

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True

```

### 8.2 Headless starten

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True

```

### 8.3 Karte speichern

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map

```

### 8.4 Frequenzen pruefen

```bash
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /cliff

```
