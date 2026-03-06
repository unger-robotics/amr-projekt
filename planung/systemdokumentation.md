# Systemdokumentation: Autonomer mobiler Roboter (AMR)

## 1. Systemübersicht und Architektur

Der autonome mobile Roboter ist als zweistufiges Echtzeitsystem aufgebaut. Das System verbindet einen Differentialantrieb mit SLAM-basierter Navigation. Die Architektur trennt die hardwarenahe Steuerung auf zwei Seeed Studio XIAO ESP32-S3 strikt von der Navigations- und Missionslogik auf einem Raspberry Pi 5. Der Drive-Knoten und der Sensor-Knoten bilden die hardwarenahe Ebene. Der Raspberry Pi 5 bildet die Navigations- und Leitstandsebene. Die Kommunikation zwischen beiden Ebenen erfolgt über micro-ROS per UART/USB-CDC über stabile udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`). XRCE-DDS übernimmt die Middleware-Funktion.

Die Steuerung gliedert sich in drei Ebenen. Die untere Ebene regelt die Gleichstrommotoren mit PID-Reglern bei $50,\mathrm{Hz}$ auf dem ESP32-S3. Die mittlere Ebene verarbeitet Sensordaten aus Odometrie, IMU und Laserscanner. Die obere Ebene realisiert Lokalisierung, Kartierung und Navigation mit SLAM Toolbox und Nav2 auf dem Raspberry Pi 5. Diese Struktur sichert deterministische Motorsteuerung und entkoppelt sie von den rechenintensiven Navigationsalgorithmen.

## 2. Hardware-Komponenten

### 2.1 Antriebsstrang

Der Differentialantrieb basiert auf zwei JGA25-370-Gleichstrommotoren mit integrierten Hall-Encodern. Ein Cytron MDD3A Dual-Motortreiber steuert die Motoren im Dual-PWM-Modus an. Die PWM-Frequenz beträgt $20,\mathrm{kHz}$ bei einer Auflösung von $8,\mathrm{bit}$ mit einem Wertebereich von 0 bis 255. Die empirisch ermittelte PWM-Deadzone liegt bei 35. Unterhalb dieses Werts erzeugt der Antrieb kein ausreichendes Anlaufmoment.

Die kinematischen Parameter sind in `mcu_firmware/drive_node/include/config.h` definiert. Der kalibrierte Raddurchmesser beträgt $65{,}67,\mathrm{mm}$. Grundlage bilden drei Bodentests mit Maßbandvergleich und einem Korrekturfaktor von $98{,}5 / 97{,}55$ gegenüber einem Nennwert von $65{,}0,\mathrm{mm}$. Die Spurbreite beträgt $178,\mathrm{mm}$. Die Encoder liefern im 2x-Quadraturmodus rund 748 Ticks pro Radumdrehung, links $748{,}6$ und rechts $747{,}2$. Daraus ergibt sich eine Wegauflösung von etwa $0{,}276,\mathrm{mm}$ pro Tick.

### 2.2 Sensorik

Der RPLIDAR A1 ist rückwärts auf dem Roboter montiert. Die Montage entspricht einer Yaw-Rotation von $180^\circ$ relativ zu `base_link`. Der Scanner liefert Laserdaten mit etwa $7{,}6,\mathrm{Hz}$ über `/dev/ttyUSB0` bei $115200,\mathrm{Bd}`. Die maximale Reichweite beträgt $12,\mathrm{m}$.

Eine MPU6050-IMU ist über I2C an den ESP32-S3 angebunden. Der Bus nutzt SDA an D4, SCL an D5 und arbeitet mit $400,\mathrm{kHz}`im Fast-Mode. Die IMU misst im Bereich von $\pm 2\,g$ für die Beschleunigung und $\pm 250\,^\circ/\mathrm{s}$ für die Drehrate. Beim Systemstart kalibriert die Firmware den Gyro-Bias über 500 Samples. Ein Komplementärfilter mit $\alpha = 0{,}02$ fusioniert die Daten. Der Filter gewichtet das Gyroskop mit 98 Prozent und das aus den Encodern abgeleitete Heading mit 2 Prozent. Der Knoten publiziert die IMU-Daten mit $20\,\mathrm{Hz}$ auf`/imu`.

Optional steht eine Sony-IMX296-Global-Shutter-Kamera für ArUco-basiertes visuelles Docking bereit. Die Kamera arbeitet über CSI mit $1456 \times 1088$ Pixeln bei $15,\mathrm{fps}`. Eine `v4l2loopback`-Bridge überträgt das Bildsignal per `rpicam-vid`, `ffmpeg`und`/dev/video10` in den Container.

### 2.3 Recheneinheiten

Zwei Seeed Studio XIAO ESP32-S3 arbeiten als echtzeitfähige Steuerungseinheiten in einer Zwei-Knoten-Architektur. Der Drive-Knoten an `/dev/amr_drive` übernimmt Antrieb, PID-Regelung und Odometrie. Der Sensor-Knoten an `/dev/amr_sensor` übernimmt IMU, Batterieüberwachung und Servo-Steuerung. Das Dual-Core-Design mit bis zu $240,\mathrm{MHz}$ erlaubt die Trennung von Kommunikations- und Regelaufgaben. Die Verbindung zum Raspberry Pi erfolgt über USB-CDC mit $115200,\mathrm{Bd}`.

Der Raspberry Pi 5 mit Debian Trixie und `aarch64` übernimmt Lokalisierung, Kartierung, Navigation und Leitstanddienste. ROS 2 Humble läuft in einem Docker-Container auf Basis von `ros:humble-ros-base` für `arm64`, da Debian Trixie kein natives Humble-Paket bereitstellt. Der Container nutzt den Host-Network-Modus für DDS-Multicast und einen privilegierten Modus für den Zugriff auf serielle Schnittstellen und Kamerageräte.

## 3. Software-Architektur

### 3.1 Firmware auf dem ESP32-S3

Die Firmware ist modular aufgebaut und verwendet das FreeRTOS-Betriebssystem des ESP32-S3 zur Trennung der Aufgaben auf zwei Kerne.

**Core 0** betreibt den micro-ROS-Executor. Er empfängt `geometry_msgs/Twist` auf `/cmd_vel`, publiziert `nav_msgs/Odometry` auf `/odom` mit $20,\mathrm{Hz}$ und `sensor_msgs/Imu` auf `/imu` mit $20,\mathrm{Hz}`. Zusätzlich überwacht Core 0 den Heartbeat von Core 1. Fällt der Heartbeat aus, löst Core 0 einen Notfall-Stopp der Motoren aus. Ein Failsafe stoppt die Motoren außerdem nach $500,\mathrm{ms}$ ohne eingehende Geschwindigkeitskommandos.

**Core 1** führt die PID-Regelschleife mit $50,\mathrm{Hz}$ aus. Die Kette lautet: Encoder lesen, Radgeschwindigkeiten per EMA mit $\alpha = 0{,}3$ filtern, Differentialkinematik berechnen, PID-Regelung mit $K_p = 0{,}4$, $K_i = 0{,}1$ und $K_d = 0{,}0$ anwenden, Anti-Windup berücksichtigen, Beschleunigungsrampe mit `MAX_ACCEL = 5{,}0\,\mathrm{rad/s^2}` anwenden und schließlich die PWM mit Deadzone-Kompensation ausgeben. Die Odometrie verwendet die ungefilterten Encoder-Rohdaten. Der PID-Regler verwendet gefilterte Werte, um Quantisierungsrauschen zu mindern.

Ein FreeRTOS-Mutex schützt die gemeinsam genutzten Daten in der `SharedData`-Struktur. Die Encoder-Interrupts dekodieren das Quadratur-Signal per CHANGE-Interrupt auf Phase A und Richtungsbestimmung über XOR mit Phase B. Das Attribut `IRAM_ATTR` legt die ISR im schnellen Speicher ab.

Die Vorwärtskinematik berechnet die Robotergeschwindigkeit aus den Radgeschwindigkeiten:

$$v = \frac{r}{2} \cdot (\omega_r + \omega_l)$$

$$\omega = \frac{r}{L} \cdot (\omega_r - \omega_l)$$

Die Inverskinematik berechnet die Sollgeschwindigkeiten der Räder:

$$\omega_l = \frac{v - \omega \cdot \frac{L}{2}}{r}$$

$$\omega_r = \frac{v + \omega \cdot \frac{L}{2}}{r}$$

Dabei bezeichnet $r$ den Radradius von $32{,}835,\mathrm{mm}$, $L$ die Spurbreite von $178,\mathrm{mm}$, $v$ die Translationsgeschwindigkeit und $\omega$ die Rotationsgeschwindigkeit des Roboters.

Die Firmware enthält mehrere Schutzmechanismen. Ein Failsafe-Timeout stoppt die Motoren nach $500,\mathrm{ms}$ ohne eingehende `cmd_vel`-Nachrichten. Ein Inter-Core-Watchdog auf Core 0 überwacht den Heartbeat von Core 1 und löst bei mehr als 50 verpassten Zyklen einen Notfall-Stopp aus. Eine Status-LED an Pin D10, geschaltet über einen IRLZ24N-MOSFET, signalisiert den Systemzustand mit verschiedenen Blinkmustern.

### 3.2 ROS-2-Stack für Lokalisierung, Kartierung und Navigation

Das Launch-File `full_stack.launch.py` orchestriert den ROS-2-Stack. Der micro-ROS Agent bildet die Brücke zwischen XRCE-DDS auf dem ESP32-S3 und dem DDS-Graphen auf dem Raspberry Pi. Da micro-ROS keinen TF-Broadcast bereitstellt, konvertiert der Knoten `odom_to_tf` die `/odom`-Nachrichten in die dynamische TF-Transformation `odom -> base_link`.

`slam_toolbox` arbeitet im asynchronen Online-Modus mit dem Ceres-Solver. Die Konfiguration nutzt `SPARSE_NORMAL_CHOLESKY` und die Levenberg-Marquardt-Strategie. Der Knoten erzeugt eine Belegungskarte mit einer Auflösung von $5,\mathrm{cm}`. Loop Closure ist aktiv. Der Suchradius beträgt $8\,\mathrm{m}` bei einer minimalen Kettenlänge von 10 Scans.

Nav2 stellt den vollständigen Navigations-Stack bereit. AMCL lokalisiert den Roboter mit einem Differential-Bewegungsmodell, 500 bis 2000 Partikeln und einem Likelihood-Field-Sensormodell. NavFn plant den globalen Pfad mit Dijkstra oder A*. Regulated Pure Pursuit führt die lokale Bahnverfolgung mit einer maximalen Geschwindigkeit von $0{,}4,\mathrm{m/s}` aus. Behavior-Tree-basiertes Recovery-Verhalten ergänzt die Zielanfahrt durch Drehen, Warten und Rückwärtsfahren.

Der TF-Baum hat folgende Struktur:

```text
map -> odom -> base_link -> laser
                         -> camera_link
```

Die statischen Transformationen definieren `static_transform_publisher`-Knoten. Der Laser sitzt $10,\mathrm{cm}$ vor und $5,\mathrm{cm}$ über `base_link`. Die Kamera sitzt $10,\mathrm{cm}$ vor und $8,\mathrm{cm}$ über `base_link`.

### 3.3 Docker-Umgebung

Die Container-Umgebung basiert auf `ros:humble-ros-base` für `arm64`. Sie enthält die benötigten ROS-2-Pakete für Nav2, `slam_toolbox`, `rplidar_ros` und `cv_bridge`. Der micro-ROS Agent wird aus dem Quellcode gebaut, da kein `arm64`-APT-Paket verfügbar ist. `docker-compose.yml` setzt das Projekt-Root als Build-Kontext, damit alle Quelldateien erreichbar bleiben. Docker-Volumes halten Build-Artefakte persistent. `entrypoint.sh` sourced automatisch alle ROS-2-Workspaces.

## 4. Kommunikationsarchitektur

### 4.1 micro-ROS / XRCE-DDS

Die Kommunikation zwischen ESP32-S3 und Raspberry Pi nutzt XRCE-DDS mit einer MTU von 512 Bytes. Diese Grenze ist für die Systemauslegung kritisch. Nachrichten oberhalb von 512 Bytes werden bei Best-Effort-QoS ohne Fehlermeldung verworfen. Die serialisierte `nav_msgs/Odometry`-Nachricht umfasst etwa 725 Bytes, vor allem wegen der beiden $6 \times 6$-Kovarianzmatrizen mit insgesamt 576 Bytes. Deshalb müssen die Publisher mit Reliable-QoS initialisiert werden, etwa über `rclc_publisher_init_default()`. Reliable Streams erlauben Fragmentierung bis zu 2048 Bytes bei einer Stream-History von 4.

### 4.2 ROS-2-Topics

| Topic               | Typ                     |                    Rate | Quelle               | Beschreibung                                       |
|---------------------|-------------------------|------------------------:|----------------------|----------------------------------------------------|
| `/cmd_vel`          | `geometry_msgs/Twist`   |                variabel | Nav2 / Teleoperation | Geschwindigkeitskommandos                          |
| `/odom`             | `nav_msgs/Odometry`     |        $20,\mathrm{Hz}$ | ESP32-S3             | Rad-Odometrie mit Quaternion                       |
| `/imu`              | `sensor_msgs/Imu`       |        $20,\mathrm{Hz}$ | ESP32-S3             | Beschleunigung, Drehrate, fusionierte Orientierung |
| `/scan`             | `sensor_msgs/LaserScan` | ca. $7{,}6,\mathrm{Hz}$ | RPLIDAR A1           | 2D-Laserscandaten                                  |
| `/camera/image_raw` | `sensor_msgs/Image`     |        $15,\mathrm{Hz}$ | `v4l2_camera_node`   | Kamerabild, optional                               |

Die Topic-Struktur trennt Fahrkommandos, Odometrie, IMU, Laserscan und Kameradaten klar. Damit lässt sich der Datenfluss zwischen Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung sowie Navigation sauber nachvollziehen.

## 5. Navigations-Stack

Die Navigation folgt drei Schritten. Zuerst erzeugt `slam_toolbox` eine konsistente Belegungskarte durch Scan-Matching der LiDAR-Daten mit der aktuellen Odometrie-Schätzung. Danach verfeinert AMCL im Lokalisierungsmodus die Pose des Roboters und publiziert die Transformation `map -> odom`. Anschließend berechnet NavFn einen globalen Pfad auf der Costmap, während Regulated Pure Pursuit die lokale Bahnverfolgung mit dynamischer Geschwindigkeitsregelung in Hindernisnähe übernimmt. Die maximale Geschwindigkeit beträgt $0{,}4,\mathrm{m/s}`.

Das Recovery-Verhalten umfasst Drehen, Warten und Rückwärtsfahren bei blockierter Navigation. Die Costmaps arbeiten mit einer Auflösung von $5,\mathrm{cm}` und einem Roboterradius von $15\,\mathrm{cm}`. Die lokale Costmap nutzt ein Rolling Window von $3 \times 3,\mathrm{m}`mit`VoxelLayer`und`InflationLayer` bei einem Inflationsradius von $35\,\mathrm{cm}`. Die globale Costmap kombiniert `StaticLayer`, `ObstacleLayer` und `InflationLayer`. Der Goal Checker verwendet eine Positionstoleranz von $10,\mathrm{cm}` und eine Yaw-Toleranz von $0{,}15\,\mathrm{rad}`, also etwa $8{,}6^\circ`.

Für optionales ArUco-Docking steht `aruco_docking.py` bereit. Der Knoten implementiert eine Zustandsmaschine mit `SEARCHING`, `APPROACHING` und `DOCKED`. Ein P-Regler mit $K_p = 0{,}5$ übernimmt die laterale Zentrierung bei einer Anfahrtsgeschwindigkeit von $0{,}05,\mathrm{m/s}`. Die Erkennung verwendet `cv2.aruco.ArucoDetector` ab OpenCV 4.7.

## 6. Schnittstellen und Parameter

### 6.1 Zentrale Konfigurationsparameter

Die hardwarenahen Parameter liegen in `mcu_firmware/drive_node/include/config.h` und `mcu_firmware/sensor_node/include/config.h`. `static_assert` sichert die Konfiguration zur Kompilierzeit ab.

| Parameter                  |            Wert | Einheit  | Beschreibung                      |
|----------------------------|----------------:|----------|-----------------------------------|
| Raddurchmesser             |           65,67 | mm       | kalibriert durch Bodentest        |
| Spurbreite                 |             178 | mm       | Achsabstand der Räder             |
| Encoder-Ticks je Umdrehung |         ca. 748 | Ticks    | 2x-Quadratur                      |
| PID-Parameter              | 0,4 / 0,1 / 0,0 | –        | $K_p / K_i / K_d$                 |
| Regelfrequenz              |              50 | Hz       | Core 1                            |
| Odometrie-Rate             |              20 | Hz       | Core 0                            |
| IMU-Rate                   |              20 | Hz       | Core 0                            |
| Failsafe-Timeout           |             500 | ms       | Motorstopp bei Verbindungsverlust |
| PWM-Deadzone               |              35 | PWM-Wert | minimale Anlauf-PWM               |
| maximale Beschleunigung    |             5,0 | rad/s²   | Sollwertrampe                     |
| Zielgeschwindigkeit Nav2   |             0,4 | m/s      | Regulated Pure Pursuit            |

### 6.2 Serielle Schnittstellen

Die ESP32-S3 sind über stabile udev-Symlinks angebunden: `/dev/amr_drive` für den Drive-Knoten und `/dev/amr_sensor` für den Sensor-Knoten, jeweils über USB-CDC mit $115200,\mathrm{Bd}`. Der RPLIDAR A1 ist über `/dev/amr_lidar`mit derselben Baudrate erreichbar. Ein`flock`-basierter Sperrmechanismus unter `/var/lock/esp32-serial.lock` verhindert parallelen Zugriff konkurrierender Anwendungen. Vor dem Start der micro-ROS Agents müssen konkurrierende Dienste gestoppt werden.

### 6.3 Launch-Argumente

`full_stack.launch.py` unterstützt die Argumente `use_slam`, `use_nav`, `use_rviz`, `use_camera`, `serial_port`, `sensor_serial_port` und `camera_device`. Standardwerte sind `True` für `use_slam`, `use_nav` und `use_rviz`, `False` für `use_camera`, `/dev/amr_drive` für `serial_port`, `/dev/amr_sensor` für `sensor_serial_port` und `/dev/video10` für `camera_device`. Damit lassen sich Betriebsarten vom reinen Mapping bis zum vollständigen Stack mit kameragestütztem Docking konfigurieren.

## 7. Erweiterte Module: Vision, Audio und Bedien- und Leitstandsebene

### 7.1 Hybride Vision-Pipeline

Lokale Objekterkennung benötigt hohe Rechenleistung. Eine synchrone Ausführung im ROS-2-Graphen des Raspberry Pi 5 würde den Navigations-Stack belasten. Deshalb trennt das System die Bildverarbeitung in eine Edge- und eine Cloud-Komponente. Ein Hardware-Beschleuniger übernimmt die schnelle räumliche Erkennung. Eine externe API ergänzt die semantische Analyse asynchron. Dadurch bleibt die Echtzeitfähigkeit der Navigation erhalten, während die Latenz der Objekterkennung sinkt.

Der Datenfluss verläuft in fünf Schritten.
Erstens erfasst `v4l2_camera_node` den YUYV-Videostream über `/dev/video10`.
Zweitens konvertiert `dashboard_bridge` die Bilder und exportiert sie als MJPEG-Stream über TCP-Port 8082.
Drittens liest `host_hailo_runner` auf dem Host-System den MJPEG-Stream und führt die Objekterkennung auf dem PCIe-angebundenen Hailo-8L aus. Die Inferenzzeit beträgt etwa $34,\mathrm{ms}$ pro Frame.
Viertens sendet der Host die Koordinaten der Bounding Boxes über UDP-Port 5005 in den Container, wo `hailo_udp_receiver` die Daten in den ROS-2-Graphen einspeist.
Fünftens bewertet `gemini_semantic_node` die Szene semantisch und asynchron über die HTTPS-API des Modells `gemini-3-flash-preview`.

### 7.2 Audio-Rückmeldung

Der Roboter signalisiert Systemzustände akustisch, etwa erfolgreiches Docking oder Warnungen. `audio_feedback_node` abonniert dafür `/audio/play`. Nach Eingang einer Nachricht startet der Knoten einen nicht blockierenden Unterprozess. Dieser greift über ALSA und `/dev/snd` direkt auf den I2S-Verstärker MAX98357A zu. Die Prozessentkopplung verhindert, dass die ROS-2-Echtzeitschleife während Dekodierung oder Wiedergabe stockt.

### 7.3 Bedien- und Leitstandsebene

Das System stellt eine webbasierte Benutzeroberfläche auf Basis von Vite bereit. Die Benutzeroberfläche läuft auf dem Host unter TCP-Port 5173. Zwei getrennte Kanäle koppeln die Bedien- und Leitstandsebene an den ROS-2-Container an.
TCP-Port 8082 überträgt ausschließlich den MJPEG-Videostream.
TCP-Port 9090 transportiert über WebSocket Telemetrie, semantische Ergebnisse und manuelle Steuerbefehle.

## 8. Hardwarenahe Sicherheitslogik: Cliff-Sicherheitsmultiplexer

Die Kanten-Erkennung auf dem ESP32-S3 arbeitet deutlich schneller als die Verarbeitung derselben Information im Nav2-Stack auf dem Raspberry Pi 5. Aus dieser Zeitdifferenz folgt eine feste Prioritätsregel: Direkte Sensorsignale überstimmen stets algorithmisch berechnete Bewegungsbefehle.

Der `cliff_safety_node` setzt diese Regel als Befehlsmultiplexer um. Der Sensor-Knoten erfasst den Status des Infrarot-Kanten-Sensors MH-B und publiziert ihn mit $20,\mathrm{Hz}$ auf `/cliff`. Der Multiplexer verarbeitet die Bewegungsbefehle aus `/nav_cmd_vel` und `/dashboard_cmd_vel`. Meldet `/cliff` eine Kante, blockiert der Multiplexer sofort alle eingehenden Kommandos. Anschließend erzeugt er eigenständig einen harten Stopp mit $v = 0,\mathrm{m/s}$ und $\omega = 0,\mathrm{rad/s}`und sendet den Befehl über`/cmd_vel` an den Drive-Knoten. Damit bleibt die Sicherheitslogik gegenüber Navigation und Bedienung übergeordnet.
