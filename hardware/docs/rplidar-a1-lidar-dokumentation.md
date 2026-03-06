# 2D-Lidar-Scanner RPLIDAR A1 (USB)

> **Technische Dokumentation** – 360°-Laserscanner für autonome mobile Robotik (AMR)  
> Scanner: Slamtec RPLIDAR A1M8 (Laser-Triangulation, 360°, 12 m Reichweite, 8.000 Samples/s)  
> Schnittstelle: USB (CP2102 UART-zu-USB-Adapter) am Raspberry Pi 5  
> ROS 2: `rplidar_ros` / `sllidar_ros2` → Topic `/scan` (sensor_msgs/LaserScan)  
> Anwendung: SLAM (slam_toolbox), Navigation (Nav2), Hinderniserkennung  
> Quellen: [Slamtec RPLIDAR A1 Spec](https://www.slamtec.com/en/lidar/a1spec), [RPLIDAR A1 Datasheet (PDF)](https://www.generationrobots.com/media/rplidar-a1m8-360-degree-laser-scanner-development-kit-datasheet-1.pdf), [RPLIDAR A1 User Manual (PDF)](http://bucket.download.slamtec.com/e680b4e2d99c4349c019553820904f28c7e6ec32/LM108_SLAMTEC_rplidarkit_usermaunal_A1M8_v1.0_en.pdf), [rplidar_ros (ROS 2)](https://docs.ros.org/en/humble/p/rplidar_ros/), [Slamtec rplidar_ros (GitHub)](https://github.com/Slamtec/rplidar_ros)

---

## 1 Systemübersicht

### 1.1 Funktion im AMR-System

Der RPLIDAR A1 ist ein 2D-Laserscanner, der eine 360°-Umgebungsabtastung in einer Ebene liefert. Im AMR-System übernimmt er zwei Kernaufgaben: die **Kartenerstellung (SLAM)** und die **Echtzeit-Hinderniserkennung** für die Navigation. Der Scanner wird direkt per USB an den Raspberry Pi 5 angeschlossen und läuft als eigenständiger ROS-2-Node im Docker-Container.

```
┌────────────────────────────────────────────────────────────────────┐
│  Raspberry Pi 5 – ROS 2 Humble (Docker)                           │
│                                                                    │
│  ┌─────────────────┐     ┌────────────────┐     ┌──────────────┐ │
│  │  slam_toolbox    │◄───│ rplidar_node   │◄────│  /dev/ttyUSB0│ │
│  │  (Async SLAM)    │    │ (rplidar_ros)  │     │  (CP2102 USB)│ │
│  │                  │    │                │     └──────┬───────┘ │
│  │  /map            │    │  /scan         │            │         │
│  └────────┬─────────┘    └────────────────┘            │         │
│           │                                            │         │
│  ┌────────▼─────────┐                                  │         │
│  │  Nav2             │                                  │         │
│  │  (Navigation)     │                                  │         │
│  │  Costmap, Planner │                                  │         │
│  └──────────────────┘                                  │         │
└────────────────────────────────────────────────────────┼─────────┘
                                                         │ USB
                                                         │
                                               ┌─────────┴─────────┐
                                               │   RPLIDAR A1      │
                                               │   (A1M8-R6)       │
                                               │                   │
                                               │   ┌───────────┐   │
                                               │   │  Scan-    │   │
                                               │   │  Kopf     │   │
                                               │   │  (dreht   │   │
                                               │   │   CW)     │   │
                                               │   └───────────┘   │
                                               │                   │
                                               │  USB-Adapter      │
                                               │  (CP2102)         │
                                               └───────────────────┘
```

### 1.2 Messprinzip

Der RPLIDAR A1 verwendet **Laser-Triangulation**: Ein modulierter Infrarotlaser (785 nm) sendet einen Puls aus, der von Oberflächen reflektiert wird. Ein CMOS-Bildsensor erfasst die Position des reflektierten Punktes. Aus dem Winkel zwischen Sender und Empfänger berechnet die interne Optik die Entfernung. Der rotierende Scankopf (OPTMAG-Technologie mit kontaktloser Energie- und Datenübertragung) ermöglicht die 360°-Abtastung.

| Eigenschaft | Laser-Triangulation (A1) | Time-of-Flight (ToF) |
|---|---|---|
| Typische Reichweite | 0,15 … 12 m | 0,1 … 40 m |
| Genauigkeit (Nahbereich) | Sehr gut (< 1 % bei ≤ 3 m) | Gut |
| Genauigkeit (Fernbereich) | Abnehmend (> 2,5 % bei > 5 m) | Konstant |
| Sonnenlichempfindlichkeit | Eingeschränkt (kein direktes Sonnenlicht) | Besser |
| Kosten | Niedrig | Mittel bis hoch |
| **Eignung AMR Indoor** | **Sehr gut** | Gut bis sehr gut |

---

## 2 RPLIDAR A1 – Technische Daten

### 2.1 Leistungsdaten

| Parameter | Wert | Einheit |
|---|---|---|
| **Hersteller** | Slamtec (Shanghai) | – |
| **Modell** | RPLIDAR A1M8 (Revision R6) | – |
| **Messprinzip** | Laser-Triangulation | – |
| **Messbereich** | 0,15 … 12 | m |
| **Abtastfrequenz (Sample Rate)** | 8.000 | Samples/s |
| **Rotationsfrequenz (Scan Rate)** | 1 … 10 (typ. 5,5) | Hz |
| **Messpunkte pro Umlauf** | ~1.450 (bei 5,5 Hz) | – |
| **Winkelbereich** | 360 | ° |
| **Winkelauflösung** | ≤ 1 | ° |
| **Entfernungsauflösung** | < 0,5 | mm |
| **Lasersicherheitsklasse** | Klasse 1 (augensicher) | IEC 60825-1 |
| **Laserwellenlänge** | 785 | nm (Infrarot) |

### 2.2 Genauigkeit (Accuracy)

| Entfernungsbereich | Genauigkeit |
|---|---|
| ≤ 3 m | 1 % der Entfernung |
| 3 … 5 m | 2 % der Entfernung |
| 5 … 12 m | 2,5 % der Entfernung |
| 12 … 16 m | ≤ 2 % der Entfernung (eingeschränkt, nicht garantiert) |

> **Praxisbeispiel:** Bei einer Wandentfernung von 2,0 m beträgt die Messabweichung maximal $2{,}0 \times 0{,}01 = \pm 20\,\text{mm}$. Bei 5,0 m sind es $5{,}0 \times 0{,}025 = \pm 125\,\text{mm}$. Für SLAM-Kartierung in typischen Innenräumen (Wände in 1 … 5 m Entfernung) ist diese Genauigkeit ausreichend.

### 2.3 Elektrische Daten

| Parameter | Min | Typ | Max | Einheit |
|---|---|---|---|---|
| **Systemspannung** | 4,9 | 5,0 | 5,5 | V DC |
| **Systemstrom (Scanner + Motor)** | – | 100 | – | mA |
| **Leistungsaufnahme** | – | 0,5 | – | W |
| **UART-Baudrate (intern)** | – | 115.200 | – | Baud |
| **UART-Signalpegel** | – | 3,3 | – | V TTL |
| **USB-Adapter-Chip** | – | CP2102 (Silicon Labs) | – | – |
| **USB-Schnittstelle** | – | Micro-USB (am Adapter) | – | – |

> **Stromversorgung:** Der RPLIDAR A1 wird über den USB-Adapter mit 5 V versorgt (USB-Port des Raspberry Pi 5). Der Gesamtstrom von ~100 mA ist für den Pi-5-USB-Port unkritisch (max. 1,2 A pro Port bei USB 3.0).

### 2.4 Mechanische Daten

| Parameter | Wert | Einheit |
|---|---|---|
| **Abmessungen (∅ × H)** | 96,8 × 70,3 × 55 | mm |
| **Gewicht (Scanner)** | 170 | g |
| **Drehrichtung** | Uhrzeigersinn (von oben betrachtet) | – |
| **Montage** | Unterseite, Schrauben M2,5 oder M3 | – |
| **Betriebstemperatur** | 0 … +40 | °C |
| **Lagertemperatur** | −10 … +60 | °C |
| **Lebensdauer (OPTMAG)** | > 10.000 | Betriebsstunden |

### 2.5 Scan-Frequenz und Punktdichte

Die Rotationsfrequenz bestimmt die Anzahl der Messpunkte pro Umlauf. Bei konstanter Abtastfrequenz (8.000 Hz) gilt:

$$N_\text{Punkte} = \frac{f_\text{Sample}}{f_\text{Rotation}} = \frac{8000}{f_\text{Rot}}$$

| Rotationsfrequenz | Punkte pro Umlauf | Winkelauflösung (Ø) | Empfehlung |
|---|---|---|---|
| 2 Hz | 4.000 | 0,09° | Maximale Punktdichte, langsam |
| **5,5 Hz** | **~1.450** | **~0,25°** | **Standardwert (SLAM)** |
| 7 Hz | ~1.140 | ~0,32° | Schnellere Aktualisierung |
| 10 Hz | 800 | 0,45° | Höchste Scan-Rate, geringste Dichte |

> **Empfehlung für AMR:** Der Standardwert **5,5 Hz** bietet die beste Balance aus Kartierungsqualität und Aktualisierungsrate für SLAM in Innenräumen. Für schnelle Roboter (> 0,5 m/s) kann eine Erhöhung auf 7 … 10 Hz sinnvoll sein, um Bewegungsartefakte zu reduzieren.

---

## 3 Hardware – Development Kit

### 3.1 Lieferumfang (Typisch)

| Komponente | Beschreibung |
|---|---|
| RPLIDAR A1M8 | Scanner-Einheit mit Scankopf und Basisplatte |
| USB-Adapter | UART-zu-USB-Brücke (CP2102), Micro-USB-Anschluss |
| Verbindungskabel | 7-poliges Flachkabel (Scanner → Adapter) |
| Micro-USB-Kabel | Adapter → PC/Pi (Daten + Stromversorgung) |

### 3.2 Schnittstellenbelegung (Scanner, 7-Pin)

```
RPLIDAR A1 – Stecker (Unterseite, 2,5 mm Pitch):

Pin  Signal     Beschreibung
─────────────────────────────────────────────────
 1   GND        Masse
 2   RX         UART-Eingang (3,3 V TTL) – Kommandos vom Host
 3   TX         UART-Ausgang (3,3 V TTL) – Scandaten zum Host
 4   V5.0       5-V-Versorgung Scan-Core
 5   GND        Masse
 6   MOTOCTL    Motor-Steuerung (PWM oder High = maximale Drehzahl)
 7   VMOTO      5-V-Versorgung Motor
```

> **USB-Adapter:** Bei Verwendung des mitgelieferten USB-Adapters entfällt die manuelle Pin-Zuordnung. Der Adapter verbindet UART, Motor-Steuerung und Stromversorgung über ein einzelnes Micro-USB-Kabel. Der MOTOCTL-Pin des Adapters liegt fest auf High, sodass der Motor mit maximaler Drehzahl (~5,5 Hz) läuft.

### 3.3 USB-Adapter (CP2102)

| Parameter | Wert |
|---|---|
| **UART-zu-USB-Chip** | Silicon Labs CP2102 |
| **Baudrate** | 115.200 Baud (fest) |
| **USB-Typ** | Micro-USB |
| **Treiber (Linux)** | `cp210x` (im Kernel enthalten, kein manueller Treiber nötig) |
| **Geräte-Datei** | `/dev/ttyUSB0` (typisch) |
| **Vendor-ID** | `10c4` (Silicon Labs) |
| **Product-ID** | `ea60` (CP2102) |

### 3.4 Montage auf dem AMR

```
Seitenansicht (AMR-Chassis):

                ┌───────────────────────┐
                │     RPLIDAR A1        │
                │   ┌───────────────┐   │
                │   │   Scankopf    │   │ ← 360° freie Sicht
                │   │   (dreht CW)  │   │
                │   └───────────────┘   │
                │   Basisplatte         │  55 mm Höhe
                └───┬───────────────┬───┘
                    │ M2,5 / M3     │
     ───────────────┴───────────────┴──────────── Chassis-Oberkante
```

| Kriterium | Empfehlung |
|---|---|
| **Position** | Möglichst zentral auf dem Chassis, höchster Punkt |
| **Freie Sicht** | 360° ohne Obstruktion durch Aufbauten |
| **Höhe über Boden** | ≥ 15 cm (Tisch-, Stuhlbeine erkennen) |
| **Neigung** | Exakt horizontal (±1°), Scan-Ebene parallel zum Boden |
| **Vibrationsentkopplung** | Gummidämpfer zwischen Basisplatte und Chassis |
| **Kabel** | USB-Kabel sicher verlegen (kein Kontakt mit Scankopf) |

---

## 4 Software-Integration (Raspberry Pi 5)

### 4.1 USB-Geräteerkennung

Nach dem Anschluss des RPLIDAR A1 per USB erkennt Linux das Gerät automatisch:

```bash
# Gerät prüfen
lsusb | grep -i "cp210"
# Bus 001 Device 003: ID 10c4:ea60 Silicon Labs CP210x UART Bridge

# Serielle Schnittstelle prüfen
ls -la /dev/ttyUSB*
# crw-rw---- 1 root dialout 188, 0 Feb 24 12:00 /dev/ttyUSB0

# Berechtigungen setzen (einmalig)
sudo usermod -aG dialout $USER
# ODER
sudo chmod 666 /dev/ttyUSB0
```

### 4.2 udev-Regel (stabiler Gerätename)

Wenn mehrere USB-Geräte angeschlossen sind (z. B. XIAO ESP32-S3 + RPLIDAR), kann sich `/dev/ttyUSB0` bei jedem Neustart ändern. Eine udev-Regel erzeugt einen stabilen Symlink:

```bash
# /etc/udev/rules.d/99-rplidar.rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
    SYMLINK+="ttyRPLIDAR", MODE="0666"
```

```bash
# Regel aktivieren
sudo udevadm control --reload-rules
sudo udevadm trigger

# Prüfung
ls -la /dev/ttyRPLIDAR
# lrwxrwxrwx 1 root root 7 Feb 24 12:00 /dev/ttyRPLIDAR -> ttyUSB0
```

### 4.3 rplidar_ros – ROS-2-Treiber

Slamtec stellt den offiziellen ROS-2-Treiber `rplidar_ros` (bzw. `sllidar_ros2`) bereit. Der Node liest die Scandaten über die serielle Schnittstelle und publiziert sie als `sensor_msgs/LaserScan`.

#### 4.3.1 Installation im Docker-Container

```dockerfile
# Ergänzung im Dockerfile.amr-ros2 (aus Pi-5-Dokumentation)
# Nach der Basis-Image-Definition:

# rplidar_ros aus Quellcode bauen
RUN mkdir -p /home/ros/lidar_ws/src && \
    cd /home/ros/lidar_ws/src && \
    git clone -b ros2 https://github.com/Slamtec/rplidar_ros.git && \
    cd /home/ros/lidar_ws && \
    . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install && \
    echo "source /home/ros/lidar_ws/install/setup.bash" >> ~/.bashrc
```

#### 4.3.2 Launch-Datei (RPLIDAR A1)

```bash
# Starten des RPLIDAR A1 Nodes
ros2 launch rplidar_ros rplidar_a1_launch.py \
    serial_port:=/dev/ttyRPLIDAR \
    serial_baudrate:=115200 \
    frame_id:=laser \
    angle_compensate:=true \
    scan_mode:=Standard
```

#### 4.3.3 Konfigurationsparameter

| Parameter | Standardwert | Beschreibung |
|---|---|---|
| `serial_port` | `/dev/ttyUSB0` | Serielle Schnittstelle (→ `/dev/ttyRPLIDAR`) |
| `serial_baudrate` | `115200` | Baudrate (A1 immer 115.200) |
| `frame_id` | `laser` | TF-Frame-Name für den Scan |
| `inverted` | `false` | Scan-Daten invertieren (Montage kopfüber) |
| `angle_compensate` | `true` | Winkelkompensation für gleichmäßige Verteilung |
| `scan_mode` | `Standard` | Scan-Modus (A1: nur Standard) |

#### 4.3.4 Docker-Compose-Service

```yaml
# docker-compose.yml – Ergänzung für RPLIDAR A1
services:
  rplidar:
    image: amr-ros2:humble    # Eigenes Image mit rplidar_ros
    network_mode: host
    privileged: true
    devices:
      - /dev/ttyRPLIDAR:/dev/ttyUSB0
    volumes:
      - /dev:/dev
    command: >
      bash -c "source /opt/ros/humble/setup.bash &&
               source /home/ros/lidar_ws/install/setup.bash &&
               ros2 launch rplidar_ros rplidar_a1_launch.py
               serial_port:=/dev/ttyUSB0
               frame_id:=laser
               angle_compensate:=true"
    restart: unless-stopped
```

### 4.4 sensor_msgs/LaserScan – Nachrichtenstruktur

Der `rplidar_node` publiziert auf dem Topic `/scan` mit folgendem Aufbau:

```yaml
# sensor_msgs/msg/LaserScan
header:
  stamp:
    sec: 1234567890
    nanosec: 500000000
  frame_id: "laser"

angle_min: -3.14159        # -π rad (180° links)
angle_max:  3.14159        #  π rad (180° rechts)
angle_increment: 0.004363  # ~0,25° bei 1450 Punkten
time_increment: 0.000125   # 1/8000 s
scan_time: 0.181818        # 1/5,5 Hz ≈ 182 ms

range_min: 0.15            # 150 mm Mindestentfernung
range_max: 12.0            # 12 m Maximalentfernung

ranges: [1.234, 1.256, ...]        # Entfernungen [m] pro Winkelschritt
intensities: [47.0, 52.0, ...]     # Signalstärke (optional)
```

**Wichtige Felder für SLAM und Navigation:**

| Feld | Bedeutung für Nav2/SLAM |
|---|---|
| `ranges[]` | Entfernungswerte in Meter; `inf` = kein Echo, `0` = ungültig |
| `angle_min/max` | Definiert den Scan-Bereich (360° = −π … +π) |
| `range_min/max` | Gültigkeitsbereich; Werte außerhalb werden ignoriert |
| `frame_id` | Referenz-Frame für TF-Transformation zur Roboter-Basis |

---

## 5 TF-Transformation (laser → base_link)

### 5.1 Koordinatensystem

Der RPLIDAR A1 definiert sein Koordinatensystem wie folgt (Blick von oben):

```
RPLIDAR A1 – Koordinatensystem (Draufsicht):

          +X (vorwärts, 0°)
           ▲
           │
           │      Scan-Richtung: CW
    +Y ◄───┼─── (90°)        (von oben)
   (90°)   │
           │
           ▼ -X (180°)
```

Dieses System entspricht direkt der ROS-Konvention (REP 103: X = vorwärts, Y = links). Die Orientierung des Scanners auf dem Roboter bestimmt die statische TF-Transformation `laser` → `base_link`.

### 5.2 Statische TF-Transformation

Die Transformation beschreibt die Position und Orientierung des Laserscanner-Frames relativ zum Roboter-Mittelpunkt (`base_link`). Für einen RPLIDAR A1, der **zentral** auf dem Chassis montiert ist, **10 cm** über der Basis:

```bash
# Statische TF publizieren (in Launch-Datei oder separat)
ros2 run tf2_ros static_transform_publisher \
    --x 0.0 --y 0.0 --z 0.10 \
    --roll 0.0 --pitch 0.0 --yaw 0.0 \
    --frame-id base_link \
    --child-frame-id laser
```

| Parameter | Wert | Beschreibung |
|---|---|---|
| `x` | 0,0 m | Scanner mittig (kein Vor-/Rückversatz) |
| `y` | 0,0 m | Scanner mittig (kein Seitversatz) |
| `z` | 0,10 m | Scanner 10 cm über `base_link` |
| `yaw` | 0,0 rad | Scanner-Vorderseite = Roboter-Vorderseite |

> **Nicht-zentrierte Montage:** Wenn der Scanner z. B. 5 cm vor der Achsmitte montiert ist, muss `x = 0.05` gesetzt werden. Eine falsche TF-Transformation führt zu verzerrten SLAM-Karten.

---

## 6 SLAM – Kartenerstellung

### 6.1 slam_toolbox (Async SLAM)

Das ROS-2-Paket `slam_toolbox` nutzt die Scandaten des RPLIDAR A1 in Kombination mit der Odometrie, um eine 2D-Belegungskarte (Occupancy Grid) zu erstellen.

```bash
# slam_toolbox starten
ros2 launch slam_toolbox online_async_launch.py \
    use_sim_time:=false
```

### 6.2 Konfiguration für RPLIDAR A1

```yaml
# slam_toolbox_params.yaml
slam_toolbox:
  ros__parameters:
    # Solver
    solver_plugin: solver_plugins::CeresSolver
    ceres_linear_solver: SPARSE_NORMAL_CHOLESKY
    ceres_preconditioner: SCHUR_JACOBI
    ceres_trust_strategy: LEVENBERG_MARQUARDT

    # Scan-Verarbeitung
    resolution: 0.05                    # 5 cm Kartenauflösung
    max_laser_range: 12.0               # RPLIDAR A1 Maximalreichweite
    minimum_travel_distance: 0.1        # Min. 10 cm Fahrweg für neuen Scan
    minimum_travel_heading: 0.17        # Min. ~10° Drehung für neuen Scan

    # Loop Closure
    do_loop_closing: true
    loop_search_maximum_distance: 3.0   # Maximaler Suchabstand für Schleifen

    # Frames
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /scan

    # Modus
    mode: mapping                       # 'mapping' oder 'localization'

    # Scan-Matching
    use_scan_matching: true
    use_scan_barycenter: true
    minimum_time_interval: 0.5          # Min. 0,5 s zwischen Scans

    # Transformation
    transform_publish_period: 0.02      # 50 Hz TF-Veröffentlichung
    tf_buffer_duration: 30.0
```

### 6.3 Karte speichern und laden

```bash
# Karte speichern (nach vollständiger Erkundung)
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_room

# Erzeugt:
#   ~/maps/my_room.pgm    – Rasterbild (grau: unbekannt, weiß: frei, schwarz: belegt)
#   ~/maps/my_room.yaml   – Metadaten (Auflösung, Ursprung)

# Karte laden (für Navigation ohne erneutes Mapping)
ros2 run nav2_map_server map_server --ros-args \
    -p yaml_filename:=~/maps/my_room.yaml \
    -p use_sim_time:=false
```

### 6.4 Kartenqualität und RPLIDAR-A1-Einfluss

| Faktor | Einfluss auf Kartenqualität | Optimierung |
|---|---|---|
| Scan-Frequenz (5,5 Hz) | Zu langsam bei schneller Fahrt → Artefakte | Geschwindigkeit ≤ 0,3 m/s beim Kartieren |
| Messreichweite (12 m) | Große Räume vollständig abgedeckt | Ausreichend für Innenräume |
| Genauigkeit (1–2,5 %) | Wandkonturen leicht verrauscht | `resolution: 0.05` glättet Rauschen |
| Winkelauflösung (~0,25°) | Details an Ecken gut sichtbar | Standardwert ausreichend |
| Sonnenlicht (direkt) | Fehlmessungen möglich | Fenster mit Vorhängen abdecken |

---

## 7 Navigation (Nav2)

### 7.1 Costmap-Konfiguration

Nav2 verwendet die Scandaten des RPLIDAR A1 für die lokale und globale Costmap (Hinderniskarte):

```yaml
# nav2_costmap_params.yaml (Auszug)
local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0         # Passend zur Scan-Rate
      publish_frequency: 2.0
      width: 3.0                     # 3 × 3 m lokales Fenster
      height: 3.0
      resolution: 0.05
      robot_radius: 0.15            # AMR-Radius
      plugins: ["obstacle_layer", "inflation_layer"]

      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        observation_sources: scan
        scan:
          topic: /scan
          data_type: LaserScan
          max_obstacle_height: 2.0
          min_obstacle_height: 0.0
          obstacle_range: 3.0       # Hindernisse bis 3 m berücksichtigen
          raytrace_range: 3.5       # Freiraum bis 3,5 m
          clearing: true
          marking: true

      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.30      # 30 cm Sicherheitszone
```

### 7.2 Motor-Start/Stopp über ROS-Service

Der `rplidar_node` bietet Services zum Ein- und Ausschalten des Scannermotors:

```bash
# Motor stoppen (Energiesparen bei Stillstand)
ros2 service call /stop_motor std_srvs/srv/Empty

# Motor starten
ros2 service call /start_motor std_srvs/srv/Empty
```

---

## 8 Inbetriebnahme

### 8.1 Schritt-für-Schritt-Prüfung

```bash
# 1. RPLIDAR per USB anschließen
#    → Motor beginnt zu drehen (LED an der Unterseite leuchtet)

# 2. USB-Gerät prüfen
lsusb | grep "10c4:ea60"
ls -la /dev/ttyUSB0
# Falls /dev/ttyRPLIDAR existiert (udev-Regel):
ls -la /dev/ttyRPLIDAR

# 3. Berechtigungen prüfen
groups | grep dialout
# Falls nicht: sudo usermod -aG dialout $USER && logout/login

# 4. rplidar_node starten (im Docker-Container)
ros2 launch rplidar_ros rplidar_a1_launch.py \
    serial_port:=/dev/ttyRPLIDAR

# 5. Topic prüfen
ros2 topic list
# /scan
# /start_motor
# /stop_motor

# 6. Scan-Daten empfangen
ros2 topic echo /scan --once
# header:
#   frame_id: "laser"
# angle_min: -3.14159...
# ranges: [1.23, 1.25, ...]

# 7. Frequenz prüfen (Soll: ~5,5 Hz)
ros2 topic hz /scan
# average rate: 5.51

# 8. Bandbreite prüfen
ros2 topic bw /scan
# ~35 kB/s (typisch für ~1450 Punkte × 5,5 Hz)

# 9. Schnelltest: Scan in RViz2 visualisieren (auf Desktop-PC)
rviz2 &
# → Add → By topic → /scan → LaserScan
# → Fixed Frame: "laser"
# → 360°-Scan der Umgebung sichtbar
```

### 8.2 Aufwärmphase

Der Scanner benötigt eine Aufwärmphase von **ca. 2 Minuten** nach dem Einschalten, um stabile Messwerte zu liefern. Während dieser Phase kann die Entfernungsauflösung leicht schwanken. Für SLAM-Kartierung den Scanner daher vor Beginn der Erkundungsfahrt 2 Minuten im Leerlauf rotieren lassen.

---

## 9 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| Kein `/dev/ttyUSB0` vorhanden | USB-Adapter nicht erkannt | USB-Kabel wechseln; `lsusb` prüfen; anderen USB-Port testen |
| Fehlercode `80008004` | Kommunikation fehlgeschlagen | Baudrate prüfen (115.200); serielle Schnittstelle korrekt? |
| Motor dreht nicht | Stromversorgung unzureichend | USB-Hub mit eigener Stromversorgung verwenden; Kabel < 1 m |
| Motor dreht, aber keine Daten | UART-Verbindung unterbrochen | Verbindungskabel (7-Pin) fest eingesteckt? |
| `/scan` hat nur `inf`-Werte | Linse verschmutzt oder Raum zu groß | Linse reinigen; Testmessung in kleinerem Raum (< 6 m) |
| Scan zeigt Artefakte / Löcher | Direktes Sonnenlicht | Vorhänge schließen; Scanner nicht neben Fenster |
| Scan zeigt Artefakte | Reflexion an Glasflächen | Glas/Spiegel sind für Laser-Triangulation problematisch |
| Scan-Rate < 5 Hz | USB-Bandbreite oder CPU-Last | Andere USB-Geräte entfernen; Docker-Container CPU-Limit prüfen |
| TF-Warnung: `laser frame not found` | Statische TF-Transformation fehlt | `static_transform_publisher` starten (Abschnitt 5.2) |
| SLAM-Karte verzerrt | Odometrie-Fehler oder falsche TF | Rad-Encoder kalibrieren; TF-Position des Scanners prüfen |
| Docker: `Permission denied /dev/ttyUSB0` | Container ohne Device-Zugriff | `--device /dev/ttyUSB0` oder `--privileged` im Docker-Run |
| Scan dreht sich in falsche Richtung in RViz | `inverted`-Parameter falsch | `inverted:=true` setzen (bei Montage kopfüber) |

---

## 10 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   RPLIDAR A1 – Kurzprofil für AMR-Integration                          │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   SCANNER                    │                                           │
│   Hersteller                 │ Slamtec (Shanghai)                       │
│   Modell                     │ RPLIDAR A1M8 (Rev. R6)                   │
│   Messprinzip                │ Laser-Triangulation (785 nm IR)          │
│   Lasersicherheit            │ Klasse 1 (IEC 60825-1, augensicher)     │
│   Messbereich                │ 0,15 … 12 m                              │
│   Abtastrate                 │ 8.000 Samples/s                          │
│   Rotationsfrequenz          │ 5,5 Hz (Standard), 1 … 10 Hz            │
│   Punkte pro Umlauf          │ ~1.450 (bei 5,5 Hz)                     │
│   Winkelauflösung            │ ≤ 1° (typ. ~0,25°)                      │
│   Genauigkeit (≤ 3 m)       │ 1 % der Entfernung                       │
│   Genauigkeit (3 … 12 m)    │ 2 … 2,5 % der Entfernung               │
│   Abmessungen               │ 96,8 × 70,3 × 55 mm                     │
│   Gewicht                    │ 170 g                                     │
│                              │                                           │
│   SCHNITTSTELLE              │                                           │
│   Intern                     │ UART 3,3 V TTL, 115.200 Baud            │
│   Extern (Kit)               │ USB (CP2102 Adapter, Micro-USB)         │
│   Geräte-Datei               │ /dev/ttyUSB0 (→ /dev/ttyRPLIDAR)       │
│   Vendor/Product-ID          │ 10c4:ea60 (Silicon Labs)                 │
│   Stromversorgung            │ 5 V DC via USB (~100 mA, ~0,5 W)       │
│                              │                                           │
│   ROS-2-INTEGRATION          │                                           │
│   Treiber-Paket              │ rplidar_ros (Slamtec, GitHub)            │
│   Launch-Datei               │ rplidar_a1_launch.py                     │
│   Topic                      │ /scan                                     │
│   Nachrichtentyp             │ sensor_msgs/msg/LaserScan                │
│   Frame-ID                   │ laser                                     │
│   Services                   │ /start_motor, /stop_motor                │
│   Scan-Rate (Topic)          │ ~5,5 Hz                                   │
│                              │                                           │
│   AMR-INTEGRATION            │                                           │
│   SLAM                       │ slam_toolbox (online_async)              │
│   Navigation                 │ Nav2 (Costmap: ObstacleLayer + Inflation)│
│   TF-Frame                   │ laser → base_link (static)              │
│   Kartenauflösung            │ 0,05 m (5 cm)                            │
│   Max. Kartiergeschwindigkeit│ ~0,3 m/s (empfohlen)                    │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 11 Quellen

| Quelle | URL |
|---|---|
| Slamtec RPLIDAR A1 – Übersicht | [slamtec.com/en/Lidar/A1](https://www.slamtec.com/en/Lidar/A1/) |
| Slamtec RPLIDAR A1 – Spezifikationen | [slamtec.com/en/lidar/a1spec](https://www.slamtec.com/en/lidar/a1spec) |
| RPLIDAR A1 Datasheet (PDF) | [generationrobots.com (PDF)](https://www.generationrobots.com/media/rplidar-a1m8-360-degree-laser-scanner-development-kit-datasheet-1.pdf) |
| RPLIDAR A1 User Manual (PDF) | [slamtec.com (PDF)](http://bucket.download.slamtec.com/e680b4e2d99c4349c019553820904f28c7e6ec32/LM108_SLAMTEC_rplidarkit_usermaunal_A1M8_v1.0_en.pdf) |
| rplidar_ros – ROS 2 Paket (GitHub) | [github.com/Slamtec/rplidar_ros](https://github.com/Slamtec/rplidar_ros) |
| rplidar_ros – ROS 2 Humble Docs | [docs.ros.org/en/humble/p/rplidar_ros](https://docs.ros.org/en/humble/p/rplidar_ros/) |
| slam_toolbox (ROS 2) | [github.com/SteveMacenski/slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) |
| Nav2 – Costmap Configuration | [docs.nav2.org](https://docs.nav2.org/) |
| RPLidar in ROS 2 Docker (Tutorial) | [medium.com/@jiayi.hoffman](https://medium.com/@jiayi.hoffman/prlidar-in-ros-2-docker-on-raspberry-pi-06086e968564) |
| RPLIDAR FAQ (Slamtec Wiki) | [wiki.slamtec.com](https://wiki.slamtec.com/display/SD/RPLIDAR+FAQ) |
| CP2102 Treiber (Silicon Labs) | [silabs.com](https://www.silabs.com/interface/usb-bridges/classic/device.cp2102) |

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: Slamtec RPLIDAR A1 Datasheet, RPLIDAR A1 User Manual, Slamtec Spezifikationsseite, rplidar_ros ROS 2 Package, slam_toolbox Dokumentation*
