# Technische Systemdokumentation: Autonomer Mobiler Roboter (AMR)

## 1. Systemuebersicht und Architektur

Der autonome mobile Roboter (AMR) ist als zweistufiges Echtzeitsystem konzipiert, das einen Differentialantrieb mit SLAM-basierter Navigation verbindet. Die Systemarchitektur folgt dem Prinzip der strikten Aufgabentrennung zwischen einer Low-Level-Steuerungsebene auf einem Seeed Studio XIAO ESP32-S3 Mikrocontroller und einer High-Level-Navigationsebene auf einem Raspberry Pi 5 Einplatinencomputer. Die Kommunikation zwischen beiden Ebenen erfolgt ueber das micro-ROS-Framework mittels UART/USB-CDC-Verbindung, wobei das XRCE-DDS-Protokoll als Middleware-Schicht dient.

![Systemarchitektur: Datenfluss zwischen ESP32-S3 und Raspberry Pi 5](bilder/systemarchitektur.png)

Die Steuerungshierarchie gliedert sich in drei Ebenen: Die unterste Ebene umfasst die Regelung der Gleichstrommotoren durch PID-Regler bei 50 Hz auf dem ESP32-S3. Die mittlere Ebene bildet die Sensordatenverarbeitung mit Odometrie, IMU-Fusion und Laserscanning. Die oberste Ebene realisiert die autonome Navigation mittels SLAM Toolbox und Nav2 auf dem Raspberry Pi 5. Dieser hierarchische Aufbau gewaehrleistet deterministische Motorsteuerung auf der untersten Ebene bei gleichzeitiger Flexibilitaet der Navigationsalgorithmen auf der obersten Ebene.

## 2. Hardware-Komponenten

### 2.1 Antriebsstrang

Der Differentialantrieb basiert auf zwei JGA25-370-Gleichstrommotoren mit integrierten Hall-Encodern. Die Motoren werden ueber einen Cytron MDD3A Dual-Motortreiber im Dual-PWM-Modus angesteuert. Die PWM-Frequenz betraegt 20 kHz bei 8-bit Aufloesung (0-255), wodurch eine unhoerbare Ansteuerung gewaehrleistet wird. Die empirisch ermittelte PWM-Deadzone liegt bei einem Wert von 35, unterhalb derer kein Anlaufdrehmoment erzeugt wird.

Die kinematischen Parameter des Roboters sind zentral in der Datei `hardware/config.h` definiert. Der Raddurchmesser betraegt 65,67 mm nach Kalibrierung durch drei Bodentests mit Massbandvergleich (Korrekturfaktor 98,5/97,55 gegenueber dem Nennwert von 65,0 mm). Die Spurbreite liegt bei 178 mm. Die Encoder liefern im 2x-Quadraturmodus rund 748 Ticks pro Radumdrehung (links: 748,6; rechts: 747,2), ermittelt durch einen 10-Umdrehungen-Kalibriertest. Daraus ergibt sich eine Wegaufloesung von ca. 0,276 mm pro Tick.

### 2.2 Sensorik

Der RPLIDAR A1 2D-Laserscanner ist rueckwaertsgerichtet auf dem Roboter montiert (180 Grad Yaw-Rotation relativ zu `base_link`) und liefert Scandaten bei ca. 7,6 Hz ueber eine serielle Schnittstelle (`/dev/ttyUSB0`, 115200 Baud). Die maximale Reichweite betraegt 12 m.

Eine InvenSense MPU6050 Inertialmesseinheit (IMU) ist ueber den I2C-Bus (SDA: D4, SCL: D5, 400 kHz Fast Mode) an den ESP32-S3 angebunden. Sie misst im Bereich von plusminus 2 g (Beschleunigung) und plusminus 250 Grad/s (Drehrate). Beim Systemstart erfolgt eine Gyro-Bias-Kalibrierung ueber 500 Samples. Die IMU-Daten werden durch einen Complementary-Filter (alpha = 0,02, d.h. 98 % Gyro, 2 % Encoder-Heading) fusioniert und mit 20 Hz auf dem ROS2-Topic `/imu` publiziert.

Optional steht eine Sony IMX296 Global-Shutter-Kamera (CSI-Anbindung, 1456x1088 Pixel bei 15 fps) fuer ArUco-Marker-basiertes visuelles Docking zur Verfuegung. Die Kamerabilder werden ueber eine v4l2loopback-Bridge (`rpicam-vid` -> `ffmpeg` -> `/dev/video10`) in den Docker-Container uebertragen.

### 2.3 Recheneinheiten

Der **Seeed Studio XIAO ESP32-S3** dient als Echtzeit-Steuerungseinheit. Sein Dual-Core-Design (240 MHz Xtensa LX7) erlaubt die Partitionierung der Firmware auf zwei Kerne fuer deterministische Regelung. Die Kommunikation mit dem Raspberry Pi erfolgt ueber USB-CDC bei 115200 Baud.

Der **Raspberry Pi 5** (Debian Trixie, aarch64) uebernimmt die gesamte Navigationslogik. Da ROS2 Humble nativ auf Debian Trixie nicht verfuegbar ist, erfolgt die Ausfuehrung innerhalb eines Docker-Containers auf Basis des Images `ros:humble-ros-base` (arm64). Der Container laeuft im Host-Network-Modus fuer DDS-Multicast und im privilegierten Modus fuer den Zugriff auf serielle Schnittstellen und Kamerageraete.

## 3. Software-Architektur

### 3.1 Firmware (ESP32-S3)

Die Firmware ist modular als Sammlung von Header-only-Klassen implementiert und nutzt das FreeRTOS-Betriebssystem des ESP32 fuer die Dual-Core-Partitionierung:

**Core 0** (`loop()`, Prioritaet: Standard) beherbergt den micro-ROS-Executor. Dieser empfaengt `geometry_msgs/Twist`-Nachrichten auf dem Topic `/cmd_vel`, publiziert `nav_msgs/Odometry` auf `/odom` mit 20 Hz und `sensor_msgs/Imu` auf `/imu` mit 20 Hz. Zusaetzlich implementiert Core 0 einen Inter-Core-Watchdog, der den Heartbeat von Core 1 ueberwacht und bei Ausfall einen Notfall-Motorstopp ausloest. Ein Failsafe-Mechanismus stoppt die Motoren nach 500 ms ohne eingehende Geschwindigkeitskommandos.

**Core 1** (`controlTask`, Prioritaet 1, pinned) fuehrt die PID-Regelschleife bei 50 Hz aus. Der Regelkreis umfasst: Encoder-Auslesen -> EMA-Filterung (alpha = 0,3) der Radgeschwindigkeiten -> Differentialkinematik-Berechnung -> PID-Regelung (Kp = 0,4; Ki = 0,1; Kd = 0,0) mit Anti-Windup -> Beschleunigungsrampe (MAX_ACCEL = 5,0 rad/s^2) -> PWM-Ausgabe mit Deadzone-Kompensation. Die Odometrie wird mit den ungefilterten Encoder-Rohdaten berechnet, waehrend der PID-Regler die gefilterten Werte verwendet, um Quantisierungsrauschen zu unterdruecken.

Die Thread-Sicherheit zwischen den Kernen wird durch einen FreeRTOS-Mutex (`SharedData`-Struktur mit `xSemaphoreTake`/`xSemaphoreGive`) gewaehrleistet. Die Encoder-Interrupts sind als Quadratur-Dekodierung implementiert (CHANGE-Interrupt auf Phase A, Richtungsbestimmung ueber XOR mit Phase B) und mit dem `IRAM_ATTR`-Attribut im schnellen RAM platziert.

Die Vorwaertskinematik berechnet die Robotergeschwindigkeiten aus den Radgeschwindigkeiten gemaess:

```
v = (r / 2) * (omega_r + omega_l)
omega = (r / L) * (omega_r - omega_l)
```

Die Inverskinematik berechnet die Sollgeschwindigkeiten der Raeder:

```
omega_l = (v - omega * L / 2) / r
omega_r = (v + omega * L / 2) / r
```

Hierbei bezeichnen `r` den Radradius (32,835 mm), `L` die Spurbreite (178 mm), `v` die Translationsgeschwindigkeit und `omega` die Rotationsgeschwindigkeit des Roboters.

Die Firmware implementiert mehrere Safety-Mechanismen: Ein Failsafe-Timeout stoppt die Motoren nach 500 ms ohne eingehende `cmd_vel`-Nachrichten. Ein Inter-Core-Watchdog auf Core 0 ueberprueft den Heartbeat von Core 1 und loest bei mehr als 50 verpassten Zyklen einen Notfall-Motorstopp aus. Der LED-Status am Pin D10 (ueber IRLZ24N-MOSFET) signalisiert den Systemzustand: langsames Blinken waehrend der Agent-Suche, schnelles Blinken bei Initialisierungsfehlern, gedimmtes Leuchten nach erfolgreichem Setup und Heartbeat-Toggle im Normalbetrieb.

### 3.2 ROS2-Navigationsstack

Der ROS2-Stack wird durch ein kombiniertes Launch-File (`full_stack.launch.py`) orchestriert und umfasst folgende Nodes:

Der **micro-ROS Agent** (`micro_ros_agent`, Serial Transport) bildet die Bruecke zwischen dem XRCE-DDS-Protokoll des ESP32 und dem DDS-Graphen auf dem Raspberry Pi. Da micro-ROS keinen TF-Broadcast unterstuetzt, uebernimmt der Node **odom_to_tf** die Konvertierung der `/odom`-Nachrichten in den dynamischen TF `odom -> base_link`.

**SLAM Toolbox** arbeitet im asynchronen Online-Modus mit dem Ceres-Solver (SPARSE_NORMAL_CHOLESKY, Levenberg-Marquardt-Strategie) und erzeugt eine Belegungskarte mit 5 cm Aufloesung. Loop Closure ist aktiviert mit einem Suchradius von 8 m und einer minimalen Kettenlaenge von 10 Scans.

**Nav2** bildet den vollstaendigen Navigationsstack mit AMCL-Lokalisierung (Differential-Bewegungsmodell, 500-2000 Partikel, Likelihood-Field-Sensormodell), NavFn-Pfadplaner (Dijkstra/A*), Regulated Pure Pursuit Controller (maximale Geschwindigkeit 0,4 m/s) und Behavior-Tree-basiertem Recovery-Verhalten (Spin, Wait, Backup).

Der **TF-Baum** ist wie folgt aufgebaut:

```
map -> odom -> base_link -> laser (statisch, 180 Grad Yaw)
                         -> camera_link (statisch, optional)
```

Die statischen Transformationen werden durch `static_transform_publisher`-Nodes definiert. Der Laser ist 10 cm vor und 5 cm ueber `base_link` montiert, die Kamera 10 cm vor und 8 cm ueber `base_link`.

### 3.3 Docker-Umgebung

Die Container-Umgebung basiert auf `ros:humble-ros-base` (arm64) und beinhaltet alle erforderlichen ROS2-Pakete (nav2, slam_toolbox, rplidar_ros, cv_bridge). Der micro-ROS Agent wird aus dem Quellcode gebaut, da kein arm64-apt-Paket verfuegbar ist. Der Build-Kontext in `docker-compose.yml` ist das Projekt-Root (`../..`), um Zugriff auf alle Quelldateien zu gewaehrleisten. Build-Artefakte werden in Docker-Volumes persistiert, sodass nur der initiale Build ca. 15-20 Minuten dauert. Die `entrypoint.sh` sourced automatisch alle ROS2-Workspaces.

## 4. Kommunikationsarchitektur

### 4.1 micro-ROS / XRCE-DDS

Die Kommunikation zwischen ESP32-S3 und Raspberry Pi erfolgt ueber das XRCE-DDS-Protokoll (eXtremely Resource Constrained Environments DDS) mit einer MTU von 512 Bytes. Diese MTU-Begrenzung ist fuer die Systemauslegung kritisch: Bei Best-Effort-QoS werden Nachrichten, die 512 Bytes ueberschreiten, ohne Fehlermeldung verworfen. Da die serialisierte `nav_msgs/Odometry`-Nachricht ca. 725 Bytes umfasst (hauptsaechlich durch die beiden 6x6-Kovarianzmatrizen mit 576 Bytes), muessen alle Publisher mit Reliable-QoS initialisiert werden (`rclc_publisher_init_default()`). Reliable Streams unterstuetzen Fragmentierung bis zu 2048 Bytes (MTU x Stream-History von 4).

### 4.2 ROS2-Topics

| Topic | Typ | Rate | Quelle | Beschreibung |
|---|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | variabel | Nav2 / Teleop | Geschwindigkeitskommandos |
| `/odom` | `nav_msgs/Odometry` | 20 Hz | ESP32-S3 | Rad-Odometrie mit Quaternion |
| `/imu` | `sensor_msgs/Imu` | 20 Hz | ESP32-S3 | Beschleunigung, Drehrate, fusionierte Orientierung |
| `/scan` | `sensor_msgs/LaserScan` | ~7,6 Hz | RPLIDAR A1 | 2D-Laserscandaten |
| `/camera/image_raw` | `sensor_msgs/Image` | 15 Hz | v4l2_camera_node | Kamerabild (optional) |

## 5. Navigations-Stack

Die Navigation folgt einem dreistufigen Ablauf: Zunaechst erzeugt SLAM Toolbox eine konsistente Belegungskarte durch Scan-Matching der RPLIDAR-Daten mit der aktuellen Odometrie-Schaetzung. Im Lokalisierungsmodus verfeinert AMCL die Roboterpose mittels Partikelfilter und publiziert die Transformation `map -> odom`. Der NavFn-Pfadplaner berechnet darauf aufbauend einen globalen Pfad auf der Costmap, waehrend der Regulated Pure Pursuit Controller die lokale Bahnverfolgung mit einer maximalen Geschwindigkeit von 0,4 m/s und dynamischer Geschwindigkeitsregulierung in der Naehe von Hindernissen uebernimmt.

Das Recovery-Verhalten ist als Behavior Tree implementiert und umfasst automatisches Drehen (Spin), Warten (Wait) und Rueckwaertsfahren (Backup) bei blockierter Navigation. Die Costmaps arbeiten mit einer Aufloesung von 5 cm und einem Roboterradius von 15 cm. Die lokale Costmap nutzt ein 3x3 m Rolling Window mit VoxelLayer und InflationLayer (35 cm Inflationsradius), waehrend die globale Costmap StaticLayer, ObstacleLayer und InflationLayer kombiniert. Die Positionstoleranz des Goal Checkers betraegt 10 cm (xy) bei einer Yaw-Toleranz von 0,15 rad (ca. 8,6 Grad).

Fuer das optionale ArUco-Marker-Docking steht ein Visual-Servoing-Node (`aruco_docking.py`) zur Verfuegung, der eine Zustandsmaschine (SEARCHING -> APPROACHING -> DOCKED) mit P-Regler-basierter lateraler Zentrierung (Kp = 0,5) bei einer Anfahrtsgeschwindigkeit von 0,05 m/s implementiert. Die Marker-Erkennung nutzt die OpenCV-API `cv2.aruco.ArucoDetector` (ab Version 4.7).

## 6. Schnittstellen und Parameter

### 6.1 Zentrale Konfigurationsparameter

Alle hardwarenahen Parameter sind zentral in `hardware/config.h` definiert (Single Source of Truth) und durch `static_assert`-Pruefungen zur Kompilierzeit abgesichert:

| Parameter | Wert | Einheit | Beschreibung |
|---|---|---|---|
| Raddurchmesser | 65,67 | mm | Kalibriert durch Bodentest |
| Spurbreite | 178 | mm | Achsabstand der Raeder |
| Encoder-Ticks/Umdrehung | ~748 | Ticks | 2x-Quadratur (links: 748,6; rechts: 747,2) |
| PID-Gains | 0,4 / 0,1 / 0,0 | - | Kp / Ki / Kd |
| Regelfrequenz | 50 | Hz | Core 1 |
| Odometrie-Rate | 20 | Hz | Core 0 |
| IMU-Rate | 20 | Hz | Core 0 |
| Failsafe-Timeout | 500 | ms | Motorstopp bei Verbindungsverlust |
| PWM-Deadzone | 35 | PWM-Wert | Minimaler Anlauf-PWM |
| Max. Beschleunigung | 5,0 | rad/s^2 | Sollwertrampe |
| Zielgeschwindigkeit Nav2 | 0,4 | m/s | Regulated Pure Pursuit |

### 6.2 Serielle Schnittstellen

Der ESP32-S3 ist ueber `/dev/ttyACM0` (USB-CDC, 115200 Baud) angebunden, der RPLIDAR A1 ueber `/dev/ttyUSB0` (UART, 115200 Baud). Da drei Anwendungen den ESP32-Port teilen (Selection Panel, Embedded Bridge, AMR Docker), wird ein flock-basierter Sperrmechanismus (`/var/lock/esp32-serial.lock`) eingesetzt. Vor dem Start des micro-ROS Agents muessen konkurrierende Dienste gestoppt werden.

### 6.3 Launch-Argumente

Das Launch-File `full_stack.launch.py` unterstuetzt folgende Konfigurationsoptionen: `use_slam` (Standard: True), `use_nav` (Standard: True), `use_rviz` (Standard: True), `use_camera` (Standard: False), `serial_port` (Standard: `/dev/ttyACM0`), `camera_device` (Standard: `/dev/video10`). Durch die Kombination dieser Argumente lassen sich verschiedene Betriebsmodi realisieren, von reinem SLAM-Mapping ueber kartenlokalisierte Navigation bis hin zum vollstaendigen Stack mit Kamera-gestuetztem Docking.
