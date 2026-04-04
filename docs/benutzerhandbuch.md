---
description: >-
  Bedienungsanleitung fuer Hardware-Inbetriebnahme, Systemstart,
  Betrieb und Fehlerdiagnose.
---

# Benutzerhandbuch: Autonomer mobiler Roboter (AMR)

## 1. Voraussetzungen

### 1.1 Hardware

Fuer den Betrieb werden die folgenden Hardware-Komponenten benoetigt:

* Raspberry Pi 5 mit 8 GB RAM und Debian Trixie.
* Zwei XIAO ESP32-S3 als Drive-Knoten (Fahrkern) und Sensor-Knoten (Sensor- und Sicherheitsbasis), jeweils per USB-C mit dem Raspberry Pi verbunden.
* Cytron MDD3A Motortreiber mit zwei JGA25-370-Gleichstrommotoren inklusive Hall-Encoder.
* RPLIDAR A1, per USB mit dem Raspberry Pi verbunden.
* 3S1P-Li-Ion-Akkupack mit 10,8 bis 12,6 V und 10 A Sicherung.
* Raspberry Pi Global Shutter Camera IMX296 mit CSI-Adapter von 22-polig Mini auf 15-polig.
* MPU6050-IMU, per I2C an D4 und D5 des Sensor-Knotens angebunden.
* Hailo-8L PCIe-KI-Beschleuniger ueber M.2-Anbindung am Raspberry Pi 5.
* MAX98357A-I2S-Verstaerker mit Lautsprecher an den I2S-Pins des Raspberry Pi 5.
* Infrarot-Kanten-Sensor MH-B an den GPIOs des Sensor-Knotens.

### 1.2 Software

Fuer den Betrieb werden die folgenden Software-Komponenten benoetigt:

* Docker ab Version 20.x.
* Docker Compose ab Version 2.x.
* PlatformIO CLI, installiert ueber `pip install platformio`.
* Zwei Firmware-Verzeichnisse unter `amr/mcu_firmware/drive_node/` und `amr/mcu_firmware/sensor_node/`.
* Ein gueltiger Gemini-API-Schluessel als Umgebungsvariable `GEMINI_API_KEY` in `amr/docker/.env`.

Das Benutzerkonto muss Mitglied der Gruppen `docker`, `dialout`, `video` und `audio` sein. Gruppenzugehoerigkeit pruefen:

```bash
id -nG
```

Die Ausgabe muss `docker`, `dialout`, `video` und `audio` enthalten.

---

## 2. Ersteinrichtung

Die Ersteinrichtung ist nur einmal erforderlich. Danach genuegt der Schnellstart aus Abschnitt 3. Fuer erweiterte Deployment-Optionen, den Live-Betrieb mit Vision und ESP32-Reset-Prozeduren siehe [build_and_deploy.md](build_and_deploy.md).

### 2.1 Host-Setup ausfuehren

Das Host-Setup richtet udev-Regeln, Gruppenzugehoerigkeiten, X11-Zugriff, CAN-Service und die Kamera-Bridge ein.

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

Der erste Build benoetigt etwa 15 bis 20 Minuten auf dem Raspberry Pi 5. Folgebuilds nutzen den Docker-Cache und sind deutlich schneller.

### 2.3 Setup verifizieren

```bash
cd amr/docker/
./verify.sh
```

Die Ausgabe `Verifikation BESTANDEN` mit `0 FAIL` bestaetigt ein vollstaendiges Setup.

### 2.4 Firmware der ESP32-S3 flashen

Die Firmware muss auf beiden Knoten vorhanden sein. Updates werden getrennt fuer den Fahrkern und die Sensor- und Sicherheitsbasis eingespielt. Beim Upload immer `-e <environment>` angeben, da `pio run -t upload` ohne `-e` alle Environments flasht und das letzte die vorherigen ueberschreibt.

Drive-Knoten flashen:

```bash
cd amr/mcu_firmware/drive_node/
pio run -e drive_node -t upload -t monitor
```

Sensor-Knoten flashen:

```bash
cd amr/mcu_firmware/sensor_node/
pio run -e sensor_node -t upload -t monitor
```

Die Upload-Geschwindigkeit betraegt 921600 Baud. Der erste Build pro Knoten dauert etwa 15 Minuten, da micro-ROS aus den Quellen kompiliert wird. Folgebuilds sind durch den Cache deutlich schneller.

Die Status-LED an D10 des Drive-Knotens signalisiert den Betriebszustand:

* Langsames Blinken: Suche nach dem micro-ROS-Agenten, normal vor dem Container-Start.
* Schnelles Blinken: Initialisierungsfehler, Agent-Konfiguration pruefen.
* Gedimmtes Heartbeat-Muster: Betriebsbereitschaft.

### 2.5 ROS2-Workspace bauen

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install
```

---

## 3. Inbetriebnahme (Schnellstart)

### 3.1 Serielle Schnittstellen freigeben

Vor dem Start muessen die seriellen Schnittstellen frei sein. Kein anderer Dienst darf die Geraete `/dev/amr_drive` und `/dev/amr_sensor` belegen.

```bash
sudo systemctl stop embedded-bridge.service
sudo fuser -v /dev/amr_drive /dev/amr_sensor
```

Die Ausgabe von `fuser` darf keine aktiven Prozesse fuer beide Geraete zeigen. Zusaetzlich sicherstellen, dass keine alten Docker-Container die Ports blockieren:

```bash
docker ps
```

### 3.2 Roboter einschalten

Die Inbetriebnahme erfolgt in vier Schritten:

1. Akkupack anschliessen und Hauptsicherung pruefen.
2. USB-C-Verbindungen zwischen beiden ESP32-S3-Knoten und dem Raspberry Pi pruefen.
3. RPLIDAR A1 per USB anschliessen.
4. Warten, bis die Status-LED des Drive-Knotens langsam blinkt.

### 3.3 ROS2-Stack starten

Vollstaendigen Stack mit Lokalisierung und Kartierung (SLAM), Navigation, Bedien- und Leitstandsebene, Vision und Audio starten:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True
```

Headless-Betrieb ohne RViz2 starten:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_rviz:=False use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True
```

Der Host-Prozess `host_hailo_runner` muss separat auf dem Host-System laufen, damit die hardwarebeschleunigte Bildverarbeitung verfuegbar ist (siehe Abschnitt 4.3).

### 3.4 Verbindung pruefen

In einem zweiten Terminal die verfuegbaren Topics und Frequenzen pruefen:

```bash
cd amr/docker/
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /cliff
```

Erwartete Werte:

* `/odom`: etwa 18 bis 22 Hz.
* `/cliff`: etwa 20 Hz.
* `/scan`: etwa 7 bis 8 Hz.

---

## 4. Betriebsmodi

Fuer die vollstaendige Tabelle aller Launch-Parameter siehe [ros2_system.md](ros2_system.md), Abschnitt 4.

### 4.1 Modus fuer Lokalisierung und Kartierung (SLAM)

Dieser Modus erzeugt eine zweidimensionale Karte der Umgebung mit `slam_toolbox`.

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false
```

Fuer den Kartenaufbau den Roboter langsam manuell durch die Umgebung bewegen, zum Beispiel per Joystick in der Benutzeroberflaeche oder per Teleoperation.

Karte speichern:

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map
```

### 4.2 Navigationsmodus

Dieser Modus nutzt eine vorhandene Karte fuer autonome Zielanfahrt.

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False
```

Zielpunkte koennen ueber RViz2 mit `2D Nav Goal`, per Kartenklick in der Benutzeroberflaeche oder programmatisch gesetzt werden. Der Regulated-Pure-Pursuit-Controller begrenzt die Fahrgeschwindigkeit auf maximal 0,15 m/s (autonom) bzw. 0,4 m/s (Joystick).

### 4.3 Bedien- und Leitstandsebene mit Vision

Dieser Modus stellt die Benutzeroberflaeche, das Kamerabild und die Vision-Pipeline bereit. Fuer Komponentendetails, WebSocket-Protokoll und State Management siehe [dashboard.md](dashboard.md). Der Betrieb erfordert drei Terminals.

**Terminal 1 — ROS2-Stack:**

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_camera:=True use_vision:=True use_rviz:=False
```

**Terminal 2 — Hailo-Runner auf dem Host:**

```bash
cd ~/amr-projekt
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py \
    --model hardware/models/yolov8s.hef --threshold 0.35
```

Falls keine Hailo-Hardware angeschlossen ist, den Fallback-Modus verwenden:

```bash
PYTHONUNBUFFERED=1 python3 amr/scripts/host_hailo_runner.py --fallback
```

**Terminal 3 — Benutzeroberflaeche:**

```bash
cd ~/amr-projekt/dashboard
npm run dev -- --host 0.0.0.0
```

Die Benutzeroberflaeche ist danach erreichbar unter `https://amr.local:5173/`. Das Kamerabild wird als MJPEG-Stream ueber Port 8082 eingebunden. Erkennungen des Hailo-8L erscheinen als farbige Bounding-Boxen im Kamerabild. Navigationsziele koennen per Klick auf die SLAM-Karte gesetzt werden.

### 4.4 Manuelles Fahren

Geschwindigkeitskommando direkt an den Fahrkern senden:

```bash
./run.sh exec ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --rate 10
```

Das Beenden mit `Ctrl+C` stoppt die Kommandouebertragung. Der Failsafe stoppt die Motoren automatisch nach 500 ms ohne neue Geschwindigkeitskommandos.

### 4.5 CAN-Bus-Redundanz aktivieren

Der regulaere Datenfluss zwischen Sensorik und dem Host-Rechner erfolgt ueber micro-ROS via UART. Zur Entlastung der seriellen Verbindung und fuer eine hardwarenahe Signalfuehrung laesst sich die CAN-to-ROS2-Bridge aktivieren:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_can:=True
```

Bei aktiviertem Launch-Argument `use_can` publiziert der Sensor-Knoten die Topics `/imu`, `/cliff`, `/range/front` und `/battery` direkt ueber den CAN-Bus (1 Mbit/s). Der Knoten `can_bridge_node` empfaengt diese via SocketCAN und speist sie in den ROS2-Graphen ein, wodurch der Overhead des XRCE-DDS umgangen wird.

CAN-Status pruefen:

```bash
ip -details link show can0
```

### 4.6 Sprachschnittstelle (ReSpeaker)

Das System verfuegt ueber eine Sprachschnittstelle fuer die freihaendige Bedienung der Bedien- und Leitstandsebene, ohne dabei die primaere Navigations- oder Sicherheitslogik auszuhebeln:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_respeaker:=True
```

Das ReSpeaker Mic Array v2.0 erfasst Audiobefehle. Der Knoten `respeaker_doa_node` publiziert die Sprachrichtung auf `/sound_direction` (10 Hz) und den Spracherkennungsstatus auf `/is_voice`. Die Sprachverarbeitung arbeitet intent-basiert: Sprachbefehle werden nicht direkt in Motorbewegungen umgesetzt, sondern durch einen Multiplexer in definierte Missionskommandos uebersetzt.

* Ein Befehl wie "Notstopp" erzwingt einen sofortigen Halt.
* Ein Befehl wie "Fahre zur Ladestation" loest eine ROS2-Aktion fuer den Nav2-Stack aus, ohne direkte PWM-Werte zu senden.

---

## 5. Benutzeroberflaeche (Dashboard)

Die Benutzeroberflaeche ist unter `https://amr.local:5173/` erreichbar und bietet vier Tabs (Steuerung, Details, Validierung, Sprache), zwischen denen ueber die obere Tab-Leiste gewechselt wird. Technische Details zu Architektur, State Management und WebSocket-Protokoll stehen in [dashboard.md](dashboard.md).

### 5.1 Steuerungsseite

Die Standardansicht zeigt vier Bereiche nebeneinander (Desktop) bzw. untereinander (Mobil):

* **Sidebar (links):** Verbindungsstatus, Latenz, Odometrie (x, y, Yaw), IMU-Heading, CPU-Temperatur, RAM/Disk-Auslastung, Batterie-SOC und ein Freitext-Kommandofeld (z.B. "fahre 1 m vorwaerts", "drehe 90 grad links", "nav 1.0 0.5", "help").
* **Kamerabild:** MJPEG-Livestream (Port 8082). Bei aktivierter Vision-Pipeline erscheinen farbige Bounding-Boxen der Hailo-8L-Objekterkennung und die semantische Beschreibung. Der AI-Schalter aktiviert/deaktiviert die Vision-Pipeline.
* **SLAM-Karte:** Belegungskarte mit Roboter-Position (Dreieck mit Glow-Effekt), Fahrpfad-Trail und Massstabsbalken. Ein Klick auf die Karte setzt ein Navigationsziel (siehe 5.3).
* **LiDAR:** 360-Grad-Polardarstellung der Laserscandaten mit farbkodierten Entfernungswerten.

Unterhalb dieser vier Bereiche befinden sich:

* **Joystick:** Virtuelle 2D-Steuerung (nipplejs). Begrenzt auf 0,4 m/s linear und 1,0 rad/s angular.
* **Servo-Steuerung:** Pan- und Tilt-Regler fuer die Kamera-Plattform (PCA9685).
* **Hardware-Steuerung:** Motor-Limit (0-100%), Servo-Geschwindigkeit (1-10), LED-PWM (0-255).

### 5.2 Detailseite

Die Detailseite zeigt erweiterte System- und Sensorinformationen:

* **Aktive Geraete:** Status und Frequenz von sechs Geraeten (ESP32 Drive, ESP32 Sensor, RPLidar, IMX296-Kamera, Hailo-8L, INA260).
* **Sensordetails:** Ultraschall-Distanz als Balkendiagramm (0-4 m), Cliff-Erkennung (KANTE/SICHER), LiDAR-Status.
* **Audio:** ReSpeaker-Richtungsanzeige (Kompass), Sprachaktivitaetsindikator, Lautstaerkeregler und vier Sound-Buttons (Startup, Nav-Start, Nav-Erreicht, Cliff-Alarm).
* **Roboter-Info:** Netzwerk-IP, Seitenansicht-SVG mit Abmessungen und Sensorpositionen.

### 5.3 Navigationsziel per Kartenklick

In der Steuerungsseite kann ein Navigationsziel durch Klick auf die SLAM-Karte gesetzt werden. Der Klick erzeugt ein `nav_goal`-Kommando mit den Kartenkoordinaten. Waehrend der Navigation zeigt ein Overlay den Status (NAV + verbleibende Distanz) und bietet eine Abbrechen-Schaltflaeche. Nach Erreichen des Ziels oder bei Fehler wechselt die Statusanzeige entsprechend (ZIEL ERREICHT / NAV FEHLER / ABGEBROCHEN).

### 5.4 Notaus-Funktion

Der Notaus-Button (roter STOP-Button, oben rechts neben dem Verbindungsindikator) sendet fuenf aufeinanderfolgende Zero-Velocity-Kommandos an den Fahrkern. Dies garantiert auch bei Paketverlust einen sofortigen Halt. Der Notaus ist auf beiden Seiten (Steuerung und Details) sichtbar.

---

## 6. Validierung und Diagnose

Fuer Akzeptanzkriterien, JSON-Ergebnisformat und phasenweise Testanleitungen siehe [validation.md](validation.md).

### 6.1 Pre-Flight-Checkliste

Die Pre-Flight-Pruefung arbeitet ohne laufenden ROS2-Stack und prueft USB-Enumeration, Spannungsversorgung, Pin-Belegung, Firmware-Status und Sensorik.

```bash
python3 amr/scripts/pre_flight_check.py
```

### 6.2 Validierungsskripte im ROS2-Betrieb

Fuer alle Befehle in diesem Abschnitt muessen die micro-ROS-Agenten laufen.

| Befehl | Zweck |
|---|---|
| `./run.sh exec ros2 run my_bot encoder_test` | Encoder-Kalibrierung mit 10-Umdrehungen-Test |
| `./run.sh exec ros2 run my_bot motor_test` | Pruefung von Motor-Deadzone, Drehrichtung und Failsafe |
| `./run.sh exec ros2 run my_bot pid_tuning` | Analyse der PID-Sprungantwort |
| `./run.sh exec ros2 run my_bot kinematic_test` | Pruefung von Geradeausfahrt, Drehfahrt und Kreisfahrt |
| `./run.sh exec ros2 run my_bot imu_test` | Gyro-Drift und Beschleunigungs-Bias bei 60 s Stillstand |
| `./run.sh exec ros2 run my_bot sensor_test` | Ultraschall- und Cliff-Validierung |
| `./run.sh exec ros2 run my_bot rplidar_test` | LiDAR-Rate, Aufloesung und Scan-Qualitaet |
| `./run.sh exec ros2 run my_bot slam_validation` | Absolute Trajectory Error und TF-Ketten-Pruefung |
| `./run.sh exec ros2 run my_bot nav_test` | Navigationstest mit vier Wegpunkten und Fehlermessung |
| `./run.sh exec ros2 run my_bot nav_square_test` | Quadrat-Navigationstest (1 m x 1 m) via Vektornavigation |
| `./run.sh exec ros2 run my_bot docking_test` | ArUco-Docking-Test mit 10 Versuchen |
| `./run.sh exec ros2 run my_bot cliff_latency_test` | Pruefung des Kanten-Notstopps ueber die Sicherheitslogik |

Gesamt-Report aus allen JSON-Ergebnissen erzeugen:

```bash
python3 amr/scripts/validation_report.py
```

### 6.3 Diagnosebefehle

Topics und Frequenzen pruefen:

```bash
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /cliff
```

TF-Kette pruefen:

```bash
./run.sh exec ros2 run tf2_ros tf2_echo odom base_link
./run.sh exec ros2 run tf2_ros tf2_echo base_link ultrasonic_link
./run.sh exec ros2 run tf2_ros tf2_echo map odom
```

Firmware-Pruefung des Drive-Knotens (ausserhalb von Docker):

```bash
timeout 3 cat /dev/amr_drive | od -A x -t x1z | head -3
```

Binaere XRCE-DDS-Daten mit `0x7e`-Header bedeuten korrekte Firmware. Text wie `duty= 255/1023` weist auf das falsche Environment (`led_test`) hin.

---

## 7. Betriebslogik und Sicherheitslogik

### 7.1 Rollen der Knoten

Der Drive-Knoten bildet den Fahrkern (Ebene A). Er verarbeitet Geschwindigkeitskommandos, regelt die Motoren per PID und publiziert Odometrie.

Der Sensor-Knoten bildet die Sensor- und Sicherheitsbasis. Er verarbeitet IMU-Daten, Batterieueberwachung, Kanten-Sensor, Ultraschall und weitere hardwarenahe Signale.

Der Raspberry Pi 5 uebernimmt Lokalisierung und Kartierung (SLAM), Navigation, die Bedien- und Leitstandsebene (Ebene B) sowie Vision und Audio. Alle ROS2-Knoten laufen im Docker-Container.

### 7.2 Prioritaet der Sicherheitslogik

Die Sicherheitslogik hat stets Vorrang vor Navigation und manueller Bedienung. Der Knoten `cliff_safety_node` multiplext alle eingehenden Fahrbefehle (`/nav_cmd_vel`, `/dashboard_cmd_vel`) und leitet sie an `/cmd_vel` weiter. Die Blockierung erfolgt in zwei Faellen:

* Der Kanten-Sensor meldet eine kritische Situation (`/cliff` = true).
* Der Ultraschall-Sensor misst weniger als 100 mm (`/range/front`). Die Freigabe erfolgt erst bei mehr als 140 mm (Hysterese).

Bei Blockierung wird ein Stop-Kommando mit Nullgeschwindigkeit erzeugt und ein akustischer Alarm (`cliff_alarm`) einmalig ausgeloest.

### 7.3 Freigabelogik

Eine Sprachschnittstelle darf keine direkte Motoransteuerung ausloesen. Zulaessig ist nur die Kette aus Sprachbefehl, Intent, Freigabelogik und freigegebenem Missionskommando. Die Benutzeroberflaeche sendet Fahrbefehle ausschliesslich ueber die `dashboard_bridge`, die ihrerseits die Geschwindigkeitsbegrenzung (0,4 m/s linear, 1,0 rad/s angular) hart durchsetzt. Der Deadman-Timer stoppt den Roboter automatisch nach 300 ms ohne Heartbeat-Signal.

---

## 8. Batteriemanagement und Stromversorgung

Die Stromversorgung basiert auf einem 3S1P-Li-Ion-Akkupack. Der Sensor-Knoten ueberwacht die Zellspannung kontinuierlich ueber den INA260-Sensor.

* **Betriebsgrenzen:** Die maximale Ladespannung betraegt 12,60 V.
* **Sicherheitsabschaltung (Motor-Shutdown):** Faellt die Spannung unter den Schwellenwert von 9,5 V, stoppt der Drive-Knoten die Motorversorgung automatisch ueber das Topic `/battery_shutdown`, um unkontrolliertes Fahrverhalten zu verhindern.
* **System-Cutoff:** Ein System-Shutdown erfolgt bei 9,0 V und ein harter BMS-Disconnect bei 7,5 V. Das System muss vor Erreichen dieser Werte manuell heruntergefahren und der Akku geladen werden.
* **Ueberwachung:** Die aktuelle Akkuspannung wird mit 2 Hz auf dem Topic `/battery` publiziert.

Zur manuellen Abfrage der Batteriespannung waehrend des Betriebs:

```bash
./run.sh exec ros2 topic echo /battery
```

---

## 9. Wartung

### 9.1 Firmware-Update

Beim Update immer das Environment explizit angeben. Beide Knoten werden getrennt aktualisiert:

```bash
cd amr/mcu_firmware/drive_node/
pio run -e drive_node -t upload -t monitor

cd amr/mcu_firmware/sensor_node/
pio run -e sensor_node -t upload -t monitor
```

Nach dem Firmware-Upload den Docker-Container neu starten, damit der micro-ROS-Agent die neue Session aufbaut. Falls der Agent keine Session etabliert, den ESP32 manuell per DTR/RTS zuruecksetzen (siehe [build_and_deploy.md](build_and_deploy.md)).

### 9.2 Docker-Image aktualisieren

```bash
cd amr/docker/
docker compose build
./run.sh colcon build --packages-select my_bot --symlink-install
```

### 9.3 Abhaengigkeiten aktualisieren

Das Skript `update_dependencies.sh` aktualisiert npm, pip, PlatformIO, Docker und das ROS2-Base-Image:

```bash
./scripts/update_dependencies.sh
```

### 9.4 Systemwartung

Das Wartungsskript fuehrt Temperaturpruefung, Speicheranalyse, Service-Status, USB-Enumeration und EEPROM-Pruefung durch:

```bash
sudo ./scripts/rover_wartung.sh            # Vollstaendig mit apt-Updates
sudo ./scripts/rover_wartung.sh --check    # Nur Diagnose, keine Aenderungen
```

### 9.5 System herunterfahren

```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
```

---

## 10. Haeufige Fehlerbilder

### 10.1 `/odom` erscheint nicht

Moegliche Ursachen: micro-ROS-Agent laeuft nicht, serielle Schnittstelle ist belegt, Drive-Knoten traegt die falsche Firmware (`led_test`).

```bash
sudo fuser -v /dev/amr_drive
./run.sh exec ros2 topic list
```

Falls die falsche Firmware aktiv ist:

```bash
cd amr/mcu_firmware/drive_node/
pio run -e drive_node -t upload
```

### 10.2 Kanten-Sensor stoppt nicht

Moegliche Ursachen: Sensor-Knoten laeuft nicht, `/cliff` publiziert nicht, Sicherheitslogik ist deaktiviert (`use_cliff_safety:=False`).

```bash
./run.sh exec ros2 topic echo /cliff --qos-reliability best_effort
./run.sh exec ros2 topic hz /cliff
```

Hinweis: Der Cliff-Sensor (MH-B) erkennt dunkle und matte Oberflaechen schlecht. Fuer Tests auf dem Tisch weisses Papier als Boden-Ersatz verwenden.

### 10.3 Benutzeroberflaeche zeigt kein Kamerabild

Moegliche Ursachen: Kamera-Bridge laeuft nicht, MJPEG-Stream an Port 8082 ist nicht erreichbar, `host_hailo_runner` oder Kamerazugriff auf dem Host fehlen.

```bash
sudo systemctl is-active camera-v4l2-bridge.service
curl -s -o /dev/null -w "%{http_code}" https://amr.local:8082/stream
```

Falls die Kamera-Bridge nicht laeuft:

```bash
sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1
sudo systemctl restart camera-v4l2-bridge.service
```

### 10.4 Navigation startet nicht

Moegliche Ursachen: keine gueltige Karte vorhanden, TF-Kette unvollstaendig, Laserscan oder Odometrie fehlen.

```bash
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 run tf2_ros tf2_echo map odom
```

### 10.5 Odometrie / micro-ROS bricht ab

Moegliche Ursachen: Die serialisierte Odometrie-Nachricht (ca. 725 Bytes) ueberschreitet die XRCE-DDS MTU von 512 Bytes bei Best-Effort-Transport. ESP32 nach Neustart nicht zurueckgesetzt.

Pruefschritte:

* QoS-Profil im Subscriber pruefen — Odometrie erfordert Reliable (`rclc_publisher_init_default()`).
* DTR/RTS-Reset vor dem Containerstart ausfuehren (siehe ESP32-Reset in [build_and_deploy.md](build_and_deploy.md)).

### 10.6 IMU-Rate faellt unter 50 Hz

Moegliche Ursache: I2C-Bus-Contention auf dem Sensor-Knoten durch blockierende Lesezugriffe anderer Peripheriebausteine (Ist-Rate: 30 bis 35 Hz).

```bash
./run.sh exec ros2 topic hz /imu
```

Faellt die Rate dauerhaft unter 25 Hz, muessen die Publikationsraten der anderen I2C-Teilnehmer in `config_sensors.h` reduziert oder die I2C-Taktung (400 kHz) hardwareseitig ueberprueft werden.

### 10.7 Port-Konflikte bei Neustart

Moegliche Ursache: Alte Container oder Prozesse belegen Netzwerk-Ports oder serielle Schnittstellen.

```bash
fuser -k 8082/tcp 9090/tcp 5173/tcp 5174/tcp
docker stop $(docker ps -q) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
```

### 10.8 SLAM meldet Message Filter dropping message

Moegliche Ursache: Die TF-Transformation `odom -> base_link` fehlt (Drive-Knoten nicht verbunden).

```bash
./run.sh exec ros2 topic echo /odom --once --no-daemon
```

Erfolgsindikatoren im Launch-Log: `micro_ros_agent_drive: session established` und `slam_toolbox: Registering sensor`.

---

## 11. Kurzreferenz

| Aktion | Befehl |
|---|---|
| Vollstaendigen Stack starten | `./run.sh ros2 launch my_bot full_stack.launch.py use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True` |
| Headless starten | `./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True` |
| Nur Lokalisierung und Kartierung | `./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false` |
| Nur Navigation (ohne SLAM) | `./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False` |
| CAN-Bus aktivieren | `./run.sh ros2 launch my_bot full_stack.launch.py use_can:=True` |
| Sprachschnittstelle aktivieren | `./run.sh ros2 launch my_bot full_stack.launch.py use_respeaker:=True` |
| Karte speichern | `./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map` |
| Frequenzen pruefen | `./run.sh exec ros2 topic hz /odom` |
| TF pruefen | `./run.sh exec ros2 run tf2_ros tf2_echo odom base_link` |
| Batteriespannung abfragen | `./run.sh exec ros2 topic echo /battery` |
| ROS2-Workspace bauen | `./run.sh colcon build --packages-select my_bot --symlink-install` |
| Benutzeroberflaeche starten | `cd dashboard && npm run dev -- --host 0.0.0.0` |
| Ports freigeben | `fuser -k 8082/tcp 9090/tcp 5173/tcp` |
| Gesamt-Verifikation | `./verify.sh` |
| Firmware Drive flashen | `cd amr/mcu_firmware/drive_node && pio run -e drive_node -t upload` |
| Firmware Sensor flashen | `cd amr/mcu_firmware/sensor_node && pio run -e sensor_node -t upload` |
| System herunterfahren | `docker stop $(docker ps -q) && docker rm $(docker ps -aq)` |
