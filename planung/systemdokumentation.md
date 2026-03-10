# Systemdokumentation: Autonomer mobiler Roboter (AMR)

## 1. Systemuebersicht und Architektur

Der autonome mobile Roboter ist als zweistufiges Echtzeitsystem aufgebaut. Das System verbindet einen Differentialantrieb mit SLAM-basierter Navigation. Die Architektur trennt die hardwarenahe Steuerung auf zwei Seeed Studio XIAO ESP32-S3 strikt von der Navigations- und Missionslogik auf einem Raspberry Pi 5. Der Drive-Knoten und der Sensor-Knoten bilden die hardwarenahe Ebene. Der Raspberry Pi 5 bildet die Bedien- und Leitstandsebene. Die Kommunikation zwischen beiden Ebenen erfolgt ueber micro-ROS per UART/USB-CDC ueber stabile udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`). XRCE-DDS uebernimmt die Middleware-Funktion.

Die Steuerung gliedert sich in drei Ebenen. Der Fahrkern (Ebene A) regelt die Gleichstrommotoren mit PID-Reglern bei 50 Hz auf dem ESP32-S3. Die Sensor- und Sicherheitsbasis (Ebene A) verarbeitet Sensordaten aus Odometrie, IMU und Laserscanner. Lokalisierung und Kartierung sowie Navigation mit SLAM Toolbox und Nav2 gehoeren ebenfalls zu Ebene A und laufen auf dem Raspberry Pi 5. Die Bedien- und Leitstandsebene (Ebene B) umfasst Dashboard, Telemetrie, manuelle Kommandos und Audio-Rueckmeldungen auf dem Raspberry Pi 5. Die intelligente Interaktion (Ebene C) umfasst Sprachschnittstelle, Vision und semantische Interpretation auf dem Raspberry Pi 5 mit optionalem Beschleuniger. Diese Struktur sichert deterministische Motorsteuerung und entkoppelt sie von den rechenintensiven Navigationsalgorithmen.

## 2. Hardware-Komponenten

### 2.1 Antriebsstrang

Der Differentialantrieb basiert auf zwei JGA25-370-Gleichstrommotoren mit integrierten Hall-Encodern. Ein Cytron MDD3A Dual-Motortreiber steuert die Motoren im Dual-PWM-Modus an. Die PWM-Frequenz betraegt 20 kHz bei einer Aufloesung von 8 Bit mit einem Wertebereich von 0 bis 255. Die empirisch ermittelte PWM-Deadzone liegt bei 35. Unterhalb dieses Werts erzeugt der Antrieb kein ausreichendes Anlaufmoment.

Die kinematischen Parameter sind in `mcu_firmware/drive_node/include/config_drive.h` definiert. Der kalibrierte Raddurchmesser betraegt 65,67 mm. Grundlage bilden drei Bodentests mit Massbandvergleich und einem Korrekturfaktor von 98,5 / 97,55 gegenueber einem Nennwert von 65,0 mm. Die Spurbreite betraegt 178 mm. Die Encoder liefern im 2x-Quadraturmodus rund 748 Ticks pro Radumdrehung, links 748,6 und rechts 747,2. Daraus ergibt sich eine Wegaufloesung von etwa 0,276 mm pro Tick.

### 2.2 Sensorik

Der RPLIDAR A1 ist rueckwaerts auf dem Roboter montiert. Die Montage entspricht einer Yaw-Rotation von 180 Grad relativ zu `base_link`. Der Scanner liefert Laserdaten mit etwa 7,5 Hz ueber `/dev/ttyUSB0` bei 115200 Baud. Die maximale Reichweite betraegt 12 m.

Eine MPU6050-IMU ist ueber I2C an den ESP32-S3 angebunden. Der Bus nutzt SDA an D4, SCL an D5 und arbeitet mit 400 kHz im Fast-Mode. Die IMU misst im Bereich von +/- 2 g fuer die Beschleunigung und +/- 250 deg/s fuer die Drehrate. Beim Systemstart kalibriert die Firmware den Gyro-Bias ueber 500 Samples. Ein Komplementaerfilter mit Alpha = 0,98 fusioniert die Daten. Der Filter gewichtet das Gyroskop mit 98 Prozent und das aus den Encodern abgeleitete Heading mit 2 Prozent. Der Knoten publiziert die IMU-Daten mit einer Soll-Rate von 50 Hz auf `/imu`. Die effektiv erreichte Rate liegt bei 30–35 Hz aufgrund von I2C-Bus-Contention am Sensor-Knoten.

Optional steht eine Sony-IMX296-Global-Shutter-Kamera fuer ArUco-basiertes visuelles Docking bereit. Die Kamera arbeitet ueber CSI mit 1456 x 1088 Pixeln bei 15 fps. Die v4l2-Bridge uebertraegt das Bild mit 640 x 480 Pixeln in den Container; die native Sensoraufloesung entspricht nicht der Verarbeitungsaufloesung. Eine `v4l2loopback`-Bridge uebertraegt das Bildsignal per `rpicam-vid`, `ffmpeg` und `/dev/video10` in den Container.

### 2.3 Recheneinheiten

Zwei Seeed Studio XIAO ESP32-S3 arbeiten als echtzeitfaehige Steuerungseinheiten in einer Zwei-Knoten-Architektur. Der Drive-Knoten an `/dev/amr_drive` uebernimmt Antrieb, PID-Regelung und Odometrie. Der Sensor-Knoten an `/dev/amr_sensor` uebernimmt IMU, Batterieueberwachung und Servo-Steuerung. Das Dual-Core-Design mit bis zu 240 MHz erlaubt die Trennung von Kommunikations- und Regelaufgaben. Die Verbindung zum Raspberry Pi erfolgt ueber USB-CDC mit 921600 Baud.

Der Raspberry Pi 5 mit Debian Trixie und `aarch64` uebernimmt Lokalisierung und Kartierung, Navigation sowie die Bedien- und Leitstandsebene. ROS 2 Humble laeuft in einem Docker-Container auf Basis von `ros:humble-ros-base` fuer `arm64`, da Debian Trixie kein natives Humble-Paket bereitstellt. Der Container nutzt den Host-Network-Modus fuer DDS-Multicast und einen privilegierten Modus fuer den Zugriff auf serielle Schnittstellen und Kamerageraete.

## 3. Software-Architektur

### 3.1 Firmware auf dem ESP32-S3

Die Firmware ist modular aufgebaut und verwendet das FreeRTOS-Betriebssystem des ESP32-S3 zur Trennung der Aufgaben auf zwei Kerne.

**Core 0** betreibt den micro-ROS-Executor. Er empfaengt `geometry_msgs/Twist` auf `/cmd_vel` und publiziert `nav_msgs/Odometry` auf `/odom` mit 20 Hz. Zusaetzlich ueberwacht Core 0 den Heartbeat von Core 1. Der Sensor-Knoten publiziert `sensor_msgs/Imu` auf `/imu` mit 50 Hz. Faellt der Heartbeat aus, loest Core 0 einen Notfall-Stopp der Motoren aus. Ein Failsafe stoppt die Motoren ausserdem nach 500 ms ohne eingehende Geschwindigkeitskommandos.

**Core 1** fuehrt die PID-Regelschleife mit 50 Hz aus. Die Kette lautet: Encoder lesen, Radgeschwindigkeiten per EMA mit Alpha = 0,3 filtern, Differentialkinematik berechnen, PID-Regelung mit Kp = 0,4, Ki = 0,1 und Kd = 0,0 anwenden, Anti-Windup beruecksichtigen, Beschleunigungsrampe mit maximal 5,0 rad/s^2 anwenden und schliesslich die PWM mit Deadzone-Kompensation ausgeben. Die Odometrie verwendet die ungefilterten Encoder-Rohdaten. Der PID-Regler verwendet gefilterte Werte, um Quantisierungsrauschen zu mindern.

Ein FreeRTOS-Mutex schuetzt die gemeinsam genutzten Daten in der `SharedData`-Struktur. Die Encoder-Interrupts dekodieren das Quadratur-Signal per CHANGE-Interrupt auf Phase A und Richtungsbestimmung ueber XOR mit Phase B. Das Attribut `IRAM_ATTR` legt die ISR im schnellen Speicher ab.

Die Vorwaertskinematik berechnet die Robotergeschwindigkeit aus den Radgeschwindigkeiten:

$$v = \frac{r}{2} \cdot (\omega_r + \omega_l)$$

$$\omega = \frac{r}{L} \cdot (\omega_r - \omega_l)$$

Die Inverskinematik berechnet die Sollgeschwindigkeiten der Raeder:

$$\omega_l = \frac{v - \omega \cdot \frac{L}{2}}{r}$$

$$\omega_r = \frac{v + \omega \cdot \frac{L}{2}}{r}$$

Dabei bezeichnet $r$ den Radradius von 32,835 mm, $L$ die Spurbreite von 178 mm, $v$ die Translationsgeschwindigkeit und $\omega$ die Rotationsgeschwindigkeit des Roboters.

Die Firmware enthaelt mehrere Schutzmechanismen. Ein Failsafe-Timeout stoppt die Motoren nach 500 ms ohne eingehende `cmd_vel`-Nachrichten. Ein Inter-Core-Watchdog auf Core 0 ueberwacht den Heartbeat von Core 1 und loest bei mehr als 50 verpassten Zyklen einen Notfall-Stopp aus. Eine Status-LED an Pin D10, geschaltet ueber einen IRLZ24N-MOSFET, signalisiert den Systemzustand mit verschiedenen Blinkmustern.

### 3.2 ROS-2-Stack fuer Lokalisierung und Kartierung sowie Navigation

Das Launch-File `full_stack.launch.py` orchestriert den ROS-2-Stack. Der micro-ROS Agent bildet die Bruecke zwischen XRCE-DDS auf dem ESP32-S3 und dem DDS-Graphen auf dem Raspberry Pi. Da micro-ROS keinen TF-Broadcast bereitstellt, konvertiert der Knoten `odom_to_tf` die `/odom`-Nachrichten in die dynamische TF-Transformation `odom -> base_link` und publiziert sie mit 20 Hz.

`slam_toolbox` arbeitet im asynchronen Online-Modus mit dem Ceres-Solver. Die Konfiguration nutzt `SPARSE_NORMAL_CHOLESKY` und die Levenberg-Marquardt-Strategie. Der Knoten erzeugt eine Belegungskarte mit einer Aufloesung von 5 cm. Loop Closure ist aktiv. Der Suchradius betraegt 8 m bei einer minimalen Kettenlaenge von 10 Scans.

Nav2 stellt den vollstaendigen Navigations-Stack bereit. AMCL lokalisiert den Roboter mit einem Differential-Bewegungsmodell, 500 bis 2000 Partikeln und einem Likelihood-Field-Sensormodell. NavFn plant den globalen Pfad mit Dijkstra oder A*. Regulated Pure Pursuit fuehrt die lokale Bahnverfolgung mit einer maximalen Geschwindigkeit von 0,4 m/s aus. Behavior-Tree-basiertes Recovery-Verhalten ergaenzt die Zielanfahrt durch Drehen, Warten und Rueckwaertsfahren.

Der TF-Baum hat folgende Struktur:

```text
map -> odom -> base_link -> laser
                         -> camera_link
                         -> ultrasonic_link

```

Die statischen Transformationen definieren `static_transform_publisher`-Knoten. Der Laser sitzt 10 cm vor und 5 cm ueber `base_link`. Die Kamera sitzt 10 cm vor und 8 cm ueber `base_link`.

### 3.3 Docker-Umgebung

Die Container-Umgebung basiert auf `ros:humble-ros-base` fuer `arm64`. Sie enthaelt die benoetigten ROS-2-Pakete fuer Nav2, `slam_toolbox`, `rplidar_ros` und `cv_bridge`. Der micro-ROS Agent wird aus dem Quellcode gebaut, da kein `arm64`-APT-Paket verfuegbar ist. `docker-compose.yml` setzt das Projekt-Root als Build-Kontext, damit alle Quelldateien erreichbar bleiben. Docker-Volumes halten Build-Artefakte persistent. `entrypoint.sh` sourced automatisch alle ROS-2-Workspaces.

## 4. Kommunikationsarchitektur

### 4.1 micro-ROS / XRCE-DDS

Die Kommunikation zwischen ESP32-S3 und Raspberry Pi nutzt XRCE-DDS mit einer MTU von 512 Bytes. Diese Grenze ist fuer die Systemauslegung kritisch. Nachrichten oberhalb von 512 Bytes werden bei Best-Effort-QoS ohne Fehlermeldung verworfen. Die serialisierte `nav_msgs/Odometry`-Nachricht umfasst etwa 725 Bytes, vor allem wegen der beiden 6x6-Kovarianzmatrizen mit insgesamt 576 Bytes. Deshalb muessen die Publisher mit Reliable-QoS initialisiert werden, etwa ueber `rclc_publisher_init_default()`. Reliable Streams erlauben Fragmentierung bis zu 2048 Bytes bei einer Stream-History von 4.

### 4.2 ROS-2-Topics

Die vollstaendige Topic-Struktur ist im normativen Referenzdokument `docs/ros2_system.md` definiert. Sie trennt Fahrkommandos, Odometrie, IMU, Laserscan und Kameradaten klar. Damit laesst sich der Datenfluss zwischen Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung sowie Navigation sauber nachvollziehen.

## 5. Navigations-Stack

Die Navigation folgt drei Schritten. Zuerst erzeugt `slam_toolbox` eine konsistente Belegungskarte durch Scan-Matching der LiDAR-Daten mit der aktuellen Odometrie-Schaetzung. Danach verfeinert AMCL im Lokalisierungsmodus die Pose des Roboters und publiziert die Transformation `map -> odom`. Anschliessend berechnet NavFn einen globalen Pfad auf der Costmap, waehrend Regulated Pure Pursuit die lokale Bahnverfolgung mit dynamischer Geschwindigkeitsregelung in Hindernisnaehe uebernimmt. Die maximale Geschwindigkeit betraegt 0,4 m/s.

Das Recovery-Verhalten umfasst Drehen, Warten und Rueckwaertsfahren bei blockierter Navigation. Die Costmaps arbeiten mit einer Aufloesung von 5 cm und einem Roboterradius von 15 cm. Die lokale Costmap nutzt ein Rolling Window von 3x3 m mit `VoxelLayer` und `InflationLayer` bei einem Inflationsradius von 35 cm. Die globale Costmap kombiniert `StaticLayer`, `ObstacleLayer` und `InflationLayer`. Der Goal Checker verwendet eine Positionstoleranz von 10 cm und eine Yaw-Toleranz von 0,15 rad, also etwa 8,6 Grad.

Fuer optionales ArUco-Docking steht `aruco_docking.py` bereit. Der Knoten implementiert eine Zustandsmaschine mit `SEARCHING`, `APPROACHING` und `DOCKED`. Ein P-Regler mit Kp = 0,5 uebernimmt die laterale Zentrierung bei einer Anfahrtsgeschwindigkeit von 0,05 m/s. Die Erkennung verwendet `cv2.aruco.ArucoDetector` ab OpenCV 4.7.

## 6. Schnittstellen und Parameter

### 6.1 Zentrale Konfigurationsparameter

Alle hardwarenahen Parameter der Steuerungsebene werden verbindlich und redundanzfrei im zentralen Referenzdokument `docs/robot_parameters.md` gepflegt. Die Quellcode-Ablage erfolgt in `mcu_firmware/drive_node/include/config_drive.h` und `mcu_firmware/sensor_node/include/config_sensors.h`. `static_assert` sichert die Konfiguration zur Kompilierzeit ab.

### 6.2 Serielle Schnittstellen

Die ESP32-S3 sind ueber stabile udev-Symlinks angebunden: `/dev/amr_drive` fuer den Drive-Knoten und `/dev/amr_sensor` fuer den Sensor-Knoten, jeweils ueber USB-CDC mit 921600 Baud. Der RPLIDAR A1 ist ueber `/dev/amr_lidar` mit 115200 Baud erreichbar. Vor dem Start der micro-ROS Agents muessen konkurrierende Dienste gestoppt werden.

### 6.3 Launch-Argumente

Saemtliche Launch-Argumente zur Steuerung von `full_stack.launch.py` sind abschliessend in der Referenz `docs/ros2_system.md` dokumentiert.

## 7. Erweiterte Module: Vision, Audio und Bedien- und Leitstandsebene

### 7.1 Hybride Vision-Pipeline

Lokale Objekterkennung benoetigt hohe Rechenleistung. Eine synchrone Ausfuehrung im ROS-2-Graphen des Raspberry Pi 5 wuerde den Navigations-Stack belasten. Deshalb trennt das System die Bildverarbeitung in eine Edge- und eine Cloud-Komponente. Ein Hardware-Beschleuniger uebernimmt die schnelle raeumliche Erkennung. Eine externe API ergaenzt die semantische Analyse asynchron. Dadurch bleibt die Echtzeitfaehigkeit der Navigation erhalten, waehrend die Latenz der Objekterkennung sinkt.

Der Datenfluss verlaeuft in fuenf Schritten.
Erstens erfasst `v4l2_camera_node` den YUYV-Videostream ueber `/dev/video10`.
Zweitens konvertiert `dashboard_bridge` die Bilder und exportiert sie als MJPEG-Stream ueber TCP-Port 8082.
Drittens liest `host_hailo_runner` auf dem Host-System den MJPEG-Stream und fuehrt die Objekterkennung auf dem PCIe-angebundenen Hailo-8L aus. Die Inferenzzeit betraegt etwa 34 ms pro Frame.
Viertens sendet der Host die Koordinaten der Bounding Boxes ueber UDP-Port 5005 in den Container, wo `hailo_udp_receiver` die Daten in den ROS-2-Graphen einspeist.
Fuenftens bewertet `gemini_semantic_node` die Szene semantisch und asynchron ueber die HTTPS-API eines externen Sprachmodells.

### 7.2 Audio-Rueckmeldung

Der Roboter signalisiert Systemzustaende akustisch, etwa erfolgreiches Docking oder Warnungen. Der `audio_feedback_node` abonniert dafuer `/audio/play`. Nach Eingang einer Nachricht startet der Knoten einen nicht blockierenden Unterprozess. Dieser greift ueber ALSA und `/dev/snd` direkt auf den I2S-Audio-DAC PCM5102A (HifiBerry DAC) zu. Die Prozessentkopplung verhindert, dass die ROS-2-Echtzeitschleife waehrend Dekodierung oder Wiedergabe stockt.

### 7.3 Bedien- und Leitstandsebene

Das System stellt eine webbasierte Benutzeroberflaeche auf Basis von Vite bereit. Die Benutzeroberflaeche laeuft auf dem Host unter TCP-Port 5173. Zwei getrennte Kanaele koppeln die Bedien- und Leitstandsebene an den ROS-2-Container an.
TCP-Port 8082 uebertraegt ausschliesslich den MJPEG-Videostream.
TCP-Port 9090 transportiert ueber WebSocket Telemetrie, semantische Ergebnisse und manuelle Steuerbefehle.

## 8. Hardwarenahe Sicherheitslogik: Cliff-Sicherheitsmultiplexer

Die Kanten-Erkennung auf dem ESP32-S3 arbeitet deutlich schneller als die Verarbeitung derselben Information im Nav2-Stack auf dem Raspberry Pi 5. Aus dieser Zeitdifferenz folgt eine feste Prioritaetsregel: Direkte Sensorsignale ueberstimmen stets algorithmisch berechnete Bewegungsbefehle.

Der `cliff_safety_node` setzt diese Regel als Befehlsmultiplexer um. Der Sensor-Knoten erfasst den Status des Infrarot-Kanten-Sensors MH-B und publiziert ihn mit 20 Hz auf `/cliff`. Der Multiplexer verarbeitet die Bewegungsbefehle aus `/nav_cmd_vel` und `/dashboard_cmd_vel`. Meldet `/cliff` eine Kante, blockiert der Multiplexer innerhalb von weniger als 50 ms alle eingehenden Kommandos. Die gemessene End-to-End-Latenz ueber den ROS-2-Pfad (Sensor → /cliff → cliff_safety_node → /cmd_vel) betraegt 2,0 ms. Anschliessend erzeugt er eigenstaendig einen harten Stopp mit v = 0 m/s und w = 0 rad/s und sendet den Befehl ueber `/cmd_vel` an den Drive-Knoten. Damit bleibt die Sicherheitslogik gegenueber Navigation und Bedienung uebergeordnet.

### 8.1 CAN-Notstopp-Redundanzpfad

Zusaetzlich zum ROS-2-basierten Cliff-Multiplexer existiert ein hardwarenaher Redundanzpfad ueber den CAN-Bus. Der Sensor-Knoten sendet Cliff-Signale (CAN-ID 0x120, 20 Hz) und Battery-Shutdown-Signale (CAN-ID 0x141, eventbasiert) direkt an den Drive-Knoten. Dieser empfaengt die Frames im `controlTask` auf Core 1 per non-blocking `twai_receive()` und setzt bei Cliff- oder Unterspannungsereignissen die Sollgeschwindigkeiten auf null. Der Pfad arbeitet unabhaengig vom Raspberry Pi, Docker-Container und micro-ROS Agent. Die Reaktionszeit betraegt weniger als 20 ms entsprechend einem Zyklus der Regelschleife bei 50 Hz. Damit verfuegt das System ueber zwei unabhaengige Sicherheitspfade: den ROS-2-Pfad ueber `cliff_safety_node` und den direkten CAN-Pfad zwischen den Mikrocontrollern.
