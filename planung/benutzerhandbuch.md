# Benutzerhandbuch: Autonomer mobiler Roboter (AMR)

## 1. Voraussetzungen

### 1.1 Hardware

Für den Betrieb werden die folgenden Hardware-Komponenten benötigt:

* Raspberry Pi 5 mit 8 GB RAM und Debian Trixie.
* Zwei XIAO ESP32-S3 als Drive-Knoten und Sensor-Knoten, jeweils per USB-C mit dem Raspberry Pi verbunden.
* Cytron MDD3A Motortreiber mit zwei JGA25-370-Gleichstrommotoren inklusive Hall-Encoder.
* RPLIDAR A1, per USB mit dem Raspberry Pi verbunden.
* 3S1P-Li-Ion-Akkupack mit 10,8 bis 12,6 V und 10 A Sicherung.
* Raspberry Pi Global Shutter Camera IMX296 mit CSI-Adapter von 22-polig Mini auf 15-polig.
* MPU6050-IMU, per I2C an D4 und D5 des Sensor-Knotens angebunden.
* Hailo-8L PCIe-KI-Beschleuniger über M.2-Anbindung am Raspberry Pi 5.
* PCM5102A-I2S-DAC (HifiBerry DAC) mit Lautsprecher an den I2S-Pins des Raspberry Pi 5.
* Infrarot-Kanten-Sensor MH-B an den GPIOs des Sensor-Knotens.

### 1.2 Software

Für den Betrieb werden die folgenden Software-Komponenten benötigt:

* Docker ab Version 20.x.
* Docker Compose ab Version 2.x.
* PlatformIO CLI, installiert über `pip install platformio`.
* Zwei Firmware-Verzeichnisse unter `mcu_firmware/drive_node/` und `mcu_firmware/sensor_node/`.
* Ein gültiger Gemini-API-Schlüssel als Umgebungsvariable `GEMINI_API_KEY`.

Das Benutzerkonto muss Mitglied der Gruppen `docker`, `dialout`, `video` und `audio` sein.

Gruppenzugehörigkeit prüfen:

```bash
id -nG

```

Die Ausgabe muss `docker`, `dialout`, `video` und `audio` enthalten.

---

## 2. Ersteinrichtung

Die Ersteinrichtung ist nur einmal erforderlich. Danach genügt der Schnellstart aus Abschnitt 3.

### 2.1 Host-Setup ausführen

Das Host-Setup richtet udev-Regeln, Gruppenzugehörigkeiten, X11-Zugriff und die Kamera-Bridge ein.

```bash
cd amr/docker/
sudo bash host_setup.sh

```

Nach Abschluss müssen Benutzerkonto und Sitzung neu angemeldet werden, damit Gruppenänderungen wirksam werden.

### 2.2 Docker-Image bauen

```bash
cd amr/docker/
docker compose build

```

Der erste Build benötigt deutlich mehr Zeit als spätere, gecachte Builds.

### 2.3 Setup verifizieren

```bash
cd amr/docker/
./verify.sh

```

Die Ausgabe `Verifikation BESTANDEN` mit `0 FAIL` bestätigt ein vollständiges Setup.

### 2.4 Firmware der ESP32-S3 flashen

Die Firmware muss auf beiden Knoten vorhanden sein. Updates werden getrennt für Drive-Knoten und Sensor-Knoten eingespielt.

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

Die Upload-Geschwindigkeit beträgt 921600 Baud.

Die Status-LED an D10 des Drive-Knotens signalisiert den Betriebszustand:

* langsames Blinken: Suche nach dem micro-ROS-Agenten, normal vor dem Container-Start.
* schnelles Blinken: Initialisierungsfehler, Agent-Konfiguration prüfen.
* gedimmtes Heartbeat-Muster: Betriebsbereitschaft.

### 2.5 ROS-2-Workspace bauen

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install

```

---

## 3. Inbetriebnahme (Schnellstart)

### 3.1 Serielle Schnittstellen freigeben

Vor dem Start müssen die seriellen Schnittstellen frei sein. Andere Dienste dürfen die Geräte `/dev/amr_drive` und `/dev/amr_sensor` nicht belegen.

```bash
sudo systemctl stop embedded-bridge.service
sudo fuser -v /dev/amr_drive /dev/amr_sensor

```

Die Ausgabe von `fuser` darf keine aktiven Prozesse für beide Geräte zeigen.

### 3.2 Roboter einschalten

Die Inbetriebnahme erfolgt in vier Schritten:

1. Akkupack anschließen und Hauptsicherung prüfen.
2. USB-C-Verbindungen zwischen beiden ESP32-S3-Knoten und dem Raspberry Pi prüfen.
3. RPLIDAR A1 per USB anschließen.
4. Warten, bis die Status-LED des Drive-Knotens langsam blinkt.

### 3.3 ROS-2-Stack starten

Vollständigen Stack mit Lokalisierung und Kartierung, Navigation, Bedien- und Leitstandsebene, Vision und Audio starten:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True

```

Headless-Betrieb ohne RViz2 starten:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False use_sensors:=True use_dashboard:=True use_vision:=True use_audio:=True

```

Der Host-Prozess `host_hailo_runner` muss separat auf dem Host-System laufen, damit die hardwarebeschleunigte Bildverarbeitung verfügbar ist.

### 3.4 Verbindung prüfen

In einem zweiten Terminal die verfügbaren Topics und Frequenzen prüfen:

```bash
cd amr/docker/
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /cliff

```

Erwartete Werte:

* `/odom`: etwa 18 bis 22 Hz.
* `/cliff`: etwa 20 Hz.

---

## 4. Betriebsmodi

### 4.1 Modus für Lokalisierung und Kartierung

Dieser Modus erzeugt eine zweidimensionale Karte der Umgebung mit `slam_toolbox`.

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false

```

Für den Kartenaufbau den Roboter langsam manuell durch die Umgebung bewegen, zum Beispiel per Teleoperation oder Fernsteuerung.

Karte speichern:

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map

```

### 4.2 Navigationsmodus

Dieser Modus nutzt eine vorhandene Karte für autonome Zielanfahrt.

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False

```

Zielpunkte können über RViz2 mit `2D Nav Goal` oder programmatisch gesetzt werden. Der Regulated-Pure-Pursuit-Controller begrenzt die Fahrgeschwindigkeit auf maximal 0,4 m/s.

### 4.3 Bedien- und Leitstandsebene mit Vision

Dieser Modus stellt Dashboard, Kamerabild und Vision-Pipeline bereit.

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_vision:=True use_camera:=True

```

Ablauf:

1. Benutzeroberfläche im Browser unter `http://<IP-des-Raspberry-Pi>:5173` öffnen.
2. Live-Bild über den MJPEG-Stream an Port 8082 prüfen.
3. Lokale Objekterkennung über Hailo-8L und semantische Auswertung über externes Sprachmodell als Overlay über WebSocket an Port 9090 prüfen.

### 4.4 Manuelles Fahren

Geschwindigkeitskommando direkt an den Fahrkern senden:

```bash
./run.sh exec ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --rate 10

```

Das Beenden mit `Ctrl+C` stoppt die Kommandoübertragung. Zusätzlich stoppt der Failsafe die Motoren automatisch nach 500 ms ohne neue Geschwindigkeitskommandos.

---

## 5. Validierung und Diagnose

### 5.1 Pre-Flight-Checkliste

Die Pre-Flight-Prüfung arbeitet ohne laufenden ROS-2-Stack.

```bash
python3 amr/scripts/pre_flight_check.py

```

Das Skript prüft USB-Enumeration, Spannungsversorgung, Pin-Belegung, Firmware-Status und Sensorik.

### 5.2 Hardware-Report

```bash
python3 amr/scripts/hardware_info.py

```

Das Skript erzeugt einen zeitgestempelten Markdown-Report mit System- und Hardware-Informationen.

### 5.3 Validierungsskripte im ROS-2-Betrieb

Für alle Befehle in diesem Abschnitt müssen die micro-ROS-Agenten laufen.

* `./run.sh exec ros2 run my_bot encoder_test`: Encoder-Kalibrierung mit 10-Umdrehungen-Test.
* `./run.sh exec ros2 run my_bot motor_test`: Prüfung von Motor-Deadzone, Drehrichtung und Failsafe.
* `./run.sh exec ros2 run my_bot pid_tuning`: Analyse der PID-Sprungantwort.
* `./run.sh exec ros2 run my_bot kinematic_test`: Prüfung von Geradeausfahrt, Drehfahrt und Kreisfahrt.
* `./run.sh exec ros2 run my_bot imu_test`: Prüfung von Gyro-Drift und Beschleunigungs-Bias bei 60 s Stillstand.
* `./run.sh exec ros2 run my_bot slam_validation`: Berechnung des Absolute Trajectory Error und Prüfung der TF-Kette.
* `./run.sh exec ros2 run my_bot nav_test`: Navigationstest mit vier Wegpunkten und Fehlermessung.
* `./run.sh exec ros2 run my_bot docking_test`: ArUco-Docking-Test mit 10 Versuchen.
* `./run.sh exec ros2 run my_bot cliff_test`: Prüfung des Kanten-Notstopps über die Sicherheitslogik.

Gesamt-Report aus allen JSON-Ergebnissen erzeugen:

```bash
python3 amr/scripts/validation_report.py

```

### 5.4 Diagnosebefehle

Topics und Frequenzen prüfen:

```bash
./run.sh exec ros2 topic list
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /cliff

```

TF-Kette prüfen:

```bash
./run.sh exec ros2 run tf2_ros tf2_echo odom base_link
./run.sh exec ros2 run tf2_ros tf2_echo base_link ultrasonic_link

```

---

## 6. Betriebslogik und Sicherheitslogik

### 6.1 Rollen der Knoten

Der Drive-Knoten bildet den Fahrkern. Der Knoten verarbeitet Geschwindigkeitskommandos, regelt die Motoren und publiziert Odometrie.

Der Sensor-Knoten bildet die Sensor- und Sicherheitsbasis. Der Knoten verarbeitet IMU, Batterieüberwachung, Kanten-Sensor und weitere hardwarenahe Signale.

Der Raspberry Pi 5 übernimmt Lokalisierung und Kartierung, Navigation, Bedien- und Leitstandsebene, Vision und Audio.

### 6.2 Priorität der Sicherheitslogik

Die Sicherheitslogik hat stets Vorrang vor Navigation und manueller Bedienung. Meldet der Kanten-Sensor eine kritische Situation, blockiert die Sicherheitslogik eingehende Bewegungsbefehle und erzeugt ein Stop-Kommando mit Nullgeschwindigkeit.

### 6.3 Freigabelogik für spätere Sprachschnittstelle

Eine spätere Sprachschnittstelle darf keine direkte Motoransteuerung auslösen. Zulässig ist nur die Kette aus Sprachbefehl, Intent, Freigabelogik und freigegebenem Missionskommando.

---

## 7. Häufige Fehlerbilder

### 7.1 `/odom` erscheint nicht

Mögliche Ursachen:

* micro-ROS-Agent läuft nicht.
* serielle Schnittstelle ist belegt.
* Drive-Knoten wurde nicht korrekt geflasht.

Prüfschritte:

```bash
sudo fuser -v /dev/amr_drive
./run.sh exec ros2 topic list

```

### 7.2 Kanten-Sensor stoppt nicht

Mögliche Ursachen:

* Sensor-Knoten läuft nicht.
* Topic `/cliff` publiziert nicht.
* Sicherheitslogik ist nicht gestartet.

Prüfschritte:

```bash
./run.sh exec ros2 topic echo /cliff
./run.sh exec ros2 topic hz /cliff

```

### 7.3 Dashboard zeigt kein Kamerabild

Mögliche Ursachen:

* Kamera-Bridge läuft nicht.
* MJPEG-Stream an Port 8082 ist nicht erreichbar.
* `host_hailo_runner` oder Kamerazugriff auf dem Host fehlen.

Prüfschritte:

```bash
./run.sh exec ros2 topic list
curl http://127.0.0.1:8082

```

### 7.4 Navigation startet nicht

Mögliche Ursachen:

* keine gültige Karte vorhanden.
* TF-Kette ist unvollständig.
* Laserscan oder Odometrie fehlen.

Prüfschritte:

```bash
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 run tf2_ros tf2_echo map odom

```

### 7.5 Odometrie publiziert nicht / micro-ROS bricht ab

Mögliche Ursachen:

* Die serialisierte Odometrie-Nachricht (`nav_msgs/Odometry`) überschreitet die Maximum Transmission Unit (MTU) von 512 Bytes.
* Der Transport ist auf "Best-Effort" statt "Reliable" konfiguriert, wodurch Pakete über 512 Bytes kommentarlos verworfen werden.

Prüfschritte:

* QoS-Profil (Quality of Service) im Subscriber auf dem Host prüfen.
* Sicherstellen, dass die micro-ROS-Initialisierung `rclc_publisher_init_default()` (Reliable) verwendet.

### 7.6 IMU-Rate fällt deutlich unter 50 Hz

Mögliche Ursachen:

* I2C-Bus-Contention auf dem Sensor-Knoten. Blockierende Lesezugriffe anderer Peripheriebausteine stören das Timing der MPU6050-IMU, was zu einem messbaren Abfall der Publikationsrate auf 30 bis 35 Hz führt.

Prüfschritte:

```bash
./run.sh exec ros2 topic hz /imu

```

* Fällt die Rate dauerhaft unter 25 Hz, müssen die Publikationsraten der anderen I2C-Teilnehmer in `config_sensors.h` reduziert oder die I2C-Taktung (400 kHz) hardwareseitig überprüft werden.

---

## 8. Kurzreferenz

### 8.1 Vollständigen Stack starten

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

### 8.4 Frequenzen prüfen

```bash
./run.sh exec ros2 topic hz /odom
./run.sh exec ros2 topic hz /scan
./run.sh exec ros2 topic hz /cliff

```

---

## 9. Batteriemanagement und Stromversorgung

Wie wird das System vor einer schädlichen Tiefenentladung geschützt? Die Stromversorgung basiert auf einem 3S1P-Li-Ion-Akkupack. Der Sensor-Knoten überwacht die Zellspannung kontinuierlich über den INA260-Sensor.

* **Betriebsgrenzen:** Die maximale Ladespannung beträgt 12,60 V.
* **Sicherheitsabschaltung (Motor-Shutdown):** Fällt die Spannung unter den Schwellenwert von 9,5 V, stoppt der Drive-Knoten die Motorversorgung automatisch, um unkontrolliertes Fahrverhalten zu verhindern.
* **System-Cutoff:** Ein harter Cutoff erfolgt bei 7,95 V. Das System muss vor Erreichen dieses Wertes manuell heruntergefahren und der Akku geladen werden.
* **Überwachung:** Die aktuelle Akkuspannung wird mit 2 Hz auf dem Topic `/battery` publiziert.

Zur manuellen Abfrage der Batteriespannung während des Betriebs:

```bash
./run.sh exec ros2 topic echo /battery

```

---

## 10. Sprachschnittstelle (ReSpeaker Mic Array)

Das System verfügt über eine Sprachschnittstelle für die freihändige Bedienung der Leitstandsebene, ohne dabei die primäre Navigations- oder Sicherheitslogik auszuhebeln.

Die Aktivierung erfolgt über ein dediziertes Launch-Argument:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_respeaker:=True

```

Das ReSpeaker Mic Array v2.0 erfasst die Audiobefehle. Die Sprachverarbeitung arbeitet intent-basiert: Sprachbefehle werden nicht direkt in Motorbewegungen umgesetzt, sondern durch einen Multiplexer (`voice_command_mux`) in definierte Missionskommandos übersetzt.

* Ein Befehl wie "Notstopp" erzwingt einen sofortigen Halt.
* Ein Befehl wie "Fahre zur Ladestation" triggert eine ROS-2-Aktion für den Nav2-Stack, ohne direkte PWM-Werte zu senden.

---

## 11. CAN-Bus-Redundanz aktivieren

Der reguläre Datenfluss zwischen Sensorik und dem Host-Rechner erfolgt über micro-ROS via UART. Zur Entlastung der seriellen Verbindung und für eine hardwarenahe Signalführung lässt sich die CAN-to-ROS2-Bridge aktivieren.

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_can:=True

```

Bei aktiviertem Launch-Argument `use_can` publiziert der Sensor-Knoten die Topics `/imu`, `/cliff`, `/range/front` und `/battery` direkt über den CAN-Bus. Der Host-Knoten `can_bridge_node` empfängt diese via SocketCAN und speist sie in den ROS-2-Graphen ein, wodurch der Overhead des eXtremely Resource Constrained Environments - Data Distribution Service (XRCE-DDS) umgangen wird.
