# 07 -- Hardware-Firmware-Mapping

Dieses Dokument bildet die vollstaendige Zuordnung zwischen der physischen Hardware des AMR, der ESP32-Firmware und dem ROS2-Navigationsstack auf dem Raspberry Pi 5 ab. Es dient als zentrale Referenz fuer Debugging, Wartung und Weiterentwicklung. Alle Angaben basieren auf `config.h` (Source of Truth), den Firmware-Quelldateien und den ROS2-Konfigurationsdateien.

**Stand:** 2026-02-11
**Bezugsdokumente:** `hardware/config.h`, `robot_hal.hpp`, `main.cpp`, `diff_drive_kinematics.hpp`, `platformio.ini`, `nav2_params.yaml`, `mapper_params_online_async.yaml`

---

## A) Pin-Mapping-Tabelle

Die folgende Tabelle dokumentiert die vollstaendige Zuordnung von physischem Board-Pin ueber die ESP32-S3-GPIO-Nummer bis hin zur Firmware-Verwendung. Die XIAO-Board-Pins (D0-D10) sind das primaere Referenzsystem fuer die Verdrahtung.

### A.1 Vollstaendiges Pin-Mapping (XIAO ESP32-S3)

| XIAO Pin | ESP32-S3 GPIO | config.h Define | robot_hal.hpp Variable | Signaltyp | Funktion | Zielkomponente |
|----------|---------------|-----------------|------------------------|-----------|----------|----------------|
| D0 | GPIO1 | `PIN_MOTOR_LEFT_A` | `MOT_LEFT_IN1` (GPIO 25*) | PWM | Motor Links Vorwaerts | Cytron MDD3A M1A |
| D1 | GPIO2 | `PIN_MOTOR_LEFT_B` | `MOT_LEFT_IN2` (GPIO 26*) | PWM | Motor Links Rueckwaerts | Cytron MDD3A M1B |
| D2 | GPIO3 | `PIN_MOTOR_RIGHT_A` | `MOT_RIGHT_IN1` (GPIO 32*) | PWM | Motor Rechts Vorwaerts | Cytron MDD3A M2A |
| D3 | GPIO4 | `PIN_MOTOR_RIGHT_B` | `MOT_RIGHT_IN2` (GPIO 33*) | PWM | Motor Rechts Rueckwaerts | Cytron MDD3A M2B |
| D4 | GPIO5 | `PIN_I2C_SDA` | -- | I2C | SDA (IMU) | MPU6050 (0x68) |
| D5 | GPIO6 | `PIN_I2C_SCL` | -- | I2C | SCL (IMU) | MPU6050 (0x68) |
| D6 | GPIO43 | `PIN_ENC_LEFT_A` | `ENC_LEFT_A` (GPIO 18*) | Interrupt | Encoder Links Phase A | Hall-Encoder JGA25-370 |
| D7 | GPIO44 | `PIN_ENC_RIGHT_A` | `ENC_RIGHT_A` (GPIO 22*) | Interrupt | Encoder Rechts Phase A | Hall-Encoder JGA25-370 |
| D8 | GPIO7 | `PIN_SERVO_PAN` | -- | PWM | Servo Pan (horizontal) | MG90S (optional) |
| D9 | GPIO8 | `PIN_SERVO_TILT` | -- | PWM | Servo Tilt (vertikal) | MG90S (optional) |
| D10 | GPIO9 | `PIN_LED_MOSFET` | -- | PWM/Digital | LED-Streifen Gate | IRLZ24N MOSFET |

**Wichtiger Hinweis zur Diskrepanz (*):** Die aktuelle `robot_hal.hpp` verwendet noch hardcodierte GPIO-Nummern (18, 19, 22, 23, 25, 26, 32, 33) eines generischen ESP32-DevKit-Boards. Diese stimmen **nicht** mit dem XIAO ESP32-S3 ueberein. Die `config.h` enthaelt die korrekten XIAO-Pin-Defines (D0-D10), die in der migrierten Firmware verwendet werden muessen. Siehe Dokument `05_firmware_migrationsplan.md` fuer den detaillierten Migrationsplan.

### A.2 Nicht belegte XIAO-Pins

Alle 11 verfuegbaren XIAO-Pins (D0-D10) sind im Design belegt. Zusaetzlich stehen die Versorgungspins zur Verfuegung:

| Pin | Funktion |
|-----|----------|
| 5V | USB-Versorgung (vom Raspberry Pi ueber USB) |
| GND | Masse (Sternpunkt-GND) |
| 3V3 | 3,3 V Ausgang (fuer Encoder-VCC, I2C Pull-Ups) |

---

## B) PWM-Kanal-Zuordnung

Der ESP32-S3 nutzt das LEDC-Peripheriemodul (LED Control) fuer die PWM-Erzeugung. Insgesamt werden 5 LEDC-Kanaele konfiguriert.

### B.1 LEDC-Kanal-Tabelle

| LEDC-Kanal | config.h Define | Zugeordneter Pin | GPIO | Funktion | Frequenz | Aufloesung |
|------------|-----------------|------------------|------|----------|----------|------------|
| CH 0 | `PWM_CH_LEFT_B` | D1 | GPIO2 | Motor Links Rueckwaerts | 20 kHz | 8 Bit (0-255) |
| CH 1 | `PWM_CH_LEFT_A` | D0 | GPIO1 | Motor Links Vorwaerts | 20 kHz | 8 Bit (0-255) |
| CH 2 | `PWM_CH_RIGHT_B` | D3 | GPIO4 | Motor Rechts Rueckwaerts | 20 kHz | 8 Bit (0-255) |
| CH 3 | `PWM_CH_RIGHT_A` | D2 | GPIO3 | Motor Rechts Vorwaerts | 20 kHz | 8 Bit (0-255) |
| CH 4 | `LED_PWM_CHANNEL` | D10 | GPIO9 | LED-Streifen (MOSFET) | 5 kHz | 8 Bit (0-255) |

### B.2 Erklaerung der getauschten Kanalzuordnung

In `config.h` sind die LEDC-Kanaele A und B pro Motor **vertauscht** gegenueber der naheliegenden sequentiellen Zuordnung:

```c
// config.h -- Tatsaechliche Zuordnung
#define PWM_CH_LEFT_A  1  // war 0 -- getauscht
#define PWM_CH_LEFT_B  0  // war 1 -- getauscht
#define PWM_CH_RIGHT_A 3  // war 2 -- getauscht
#define PWM_CH_RIGHT_B 2  // war 3 -- getauscht
```

**Grund:** Die Motordrehrichtung haengt von der physischen Verdrahtung (Motorleitungen am MDD3A) ab. Anstatt die physische Verkabelung zu aendern, wurde in der Software eine Kanalvertauschung vorgenommen. Der Effekt: Wenn die Firmware `PWM_CH_LEFT_A` mit einem Duty-Cycle beschreibt, wird Kanal 1 angesteuert, der an Pin D0 (M1A am MDD3A) liegt. Da die LEDC-Kanaele in `robot_hal.hpp` ueber die Funktion `driveMotor(ch_in1, ch_in2, speed)` als Paar angesprochen werden, muss das getauschte Paar (1,0) statt (0,1) uebergeben werden, damit die Vorwaertsrichtung korrekt ist.

**Zusammenfassung:** Es handelt sich um eine reine Software-Korrektur. Die physische Verdrahtung (D0→M1A, D1→M1B, D2→M2A, D3→M2B) bleibt unveraendert.

### B.3 PWM-Parameter

| Parameter | Motor-PWM | LED-PWM | config.h Define |
|-----------|-----------|---------|-----------------|
| Frequenz | 20.000 Hz | 5.000 Hz | `MOTOR_PWM_FREQ` / `LED_PWM_FREQ` |
| Aufloesung | 8 Bit | 8 Bit | `MOTOR_PWM_BITS` / `LED_PWM_BITS` |
| Max. Duty | 255 | 255 | `MOTOR_PWM_MAX` |
| Deadzone | 35 | -- | `PWM_DEADZONE` |

Die Motor-PWM-Frequenz von 20 kHz liegt oberhalb der menschlichen Hoerschwelle und erzeugt kein hoerbares Pfeifen an den Buerstenmotoren. Die LED-PWM-Frequenz von 5 kHz ist ausreichend fuer flimmerfreie Dimmung.

---

## C) Kinematische Parameter-Kette

Dieser Abschnitt dokumentiert den Datenfluss der kinematischen Parameter von der Hardware-Konfiguration (`config.h`) ueber die Firmware-Module bis hin zu den ROS2-Parametern auf dem Raspberry Pi.

### C.1 Geometrische Parameter

| Parameter | config.h Define | config.h Wert | main.cpp Wert | diff_drive_kinematics.hpp | nav2_params.yaml | Einheit |
|-----------|-----------------|---------------|---------------|---------------------------|------------------|---------|
| Raddurchmesser | `WHEEL_DIAMETER` | 0,065 | -- | -- | -- | m |
| Radradius | `WHEEL_RADIUS` | 0,0325 (berechnet) | 0,032 (hardcodiert) | `r` (Konstruktor) | -- | m |
| Spurbreite | `WHEEL_BASE` | 0,178 | 0,145 (hardcodiert) | `l` (Konstruktor) | -- | m |
| Radumfang | `WHEEL_CIRCUMFERENCE` | 0,20420 (berechnet) | -- | -- | -- | m |
| Roboterradius | -- | -- | -- | -- | `robot_radius: 0.15` | m |

**Diskrepanz Radradius:** `config.h` definiert 0,0325 m (32,5 mm), waehrend `main.cpp` den Wert 0,032 m (32 mm) hardcodiert uebergibt. Differenz: 0,5 mm bzw. 1,5 %. Die `config.h`-Werte sind die gemessenen Werte und sollten als Source of Truth gelten.

**Diskrepanz Spurbreite:** `config.h` definiert 0,178 m (178 mm), waehrend `main.cpp` den Wert 0,145 m (145 mm) hardcodiert. Differenz: 33 mm bzw. 18,5 %. Diese erhebliche Abweichung beeinflusst die Odometrie-Berechnung und die inverse Kinematik massiv. Der `config.h`-Wert (178 mm) ist der am Chassis gemessene Wert.

### C.2 Encoder-Parameter

| Parameter | config.h Define | Wert Links | Wert Rechts | main.cpp | Einheit |
|-----------|-----------------|------------|-------------|----------|---------|
| Ticks pro Umdrehung | `TICKS_PER_REV_LEFT` / `_RIGHT` | 374,3 | 373,6 | 1440,0 (hardcodiert) | Ticks/Rev |
| Mittlerer Wert | `TICKS_PER_REV` | 374,0 | -- | -- | Ticks/Rev |
| Meter pro Tick (links) | `METERS_PER_TICK_LEFT` | 0,000546 | -- | -- | m/Tick |
| Meter pro Tick (rechts) | `METERS_PER_TICK_RIGHT` | -- | 0,000547 | -- | m/Tick |

**Diskrepanz Ticks/Rev:** `config.h` definiert ca. 374 Ticks/Rev (aus 10-Umdrehungen-Test), waehrend `main.cpp` den Wert 1440 hardcodiert. Diese Differenz muss bei der Firmware-Migration behoben werden. Die `config.h`-Werte haben Vorrang.

### C.3 Geschwindigkeitsparameter

| Parameter | Quelle | Wert | Einheit | Verwendung |
|-----------|--------|------|---------|------------|
| Zielgeschwindigkeit | nav2_params.yaml (`desired_linear_vel`) | 0,4 | m/s | Regulated Pure Pursuit Controller |
| Min. Annaeherungsgeschwindigkeit | nav2_params.yaml (`min_approach_linear_velocity`) | 0,05 | m/s | Verlangsamung am Ziel |
| Drehgeschwindigkeit | nav2_params.yaml (`rotate_to_heading_angular_vel`) | 1,0 | rad/s | Drehen auf der Stelle |
| Max. Winkelbeschleunigung | nav2_params.yaml (`max_angular_accel`) | 2,0 | rad/s^2 | Begrenzt Drehdynamik |
| Max. Linearbeschleunigung | nav2_params.yaml (`max_linear_accel`) | 1,5 | m/s^2 | Begrenzt Fahrdynamik |
| Beschleunigungsrampe (Firmware) | main.cpp (`MAX_ACCEL`) | 5,0 | rad/s^2 | Motorbeschleunigungsrampe |

### C.4 Navigations-Toleranzen

| Parameter | Quelle | Wert | Einheit |
|-----------|--------|------|---------|
| Positionstoleranz (xy) | nav2_params.yaml (`xy_goal_tolerance`) | 0,10 | m (10 cm) |
| Giertoleranz | nav2_params.yaml (`yaw_goal_tolerance`) | 0,15 | rad (~8,6 Grad) |
| Kartenaufloesung | mapper_params.yaml (`resolution`) | 0,05 | m (5 cm) |
| Costmap-Aufloesung | nav2_params.yaml (`resolution`) | 0,05 | m (5 cm) |
| Max. LiDAR-Reichweite | mapper_params.yaml (`max_laser_range`) | 12,0 | m |

### C.5 PID-Regelparameter

Die PID-Parameter sind ausschliesslich in der Firmware (`main.cpp`) definiert und haben keine ROS2-Entsprechung:

| Parameter | Wert Links | Wert Rechts | Einheit |
|-----------|------------|-------------|---------|
| Kp | 1,5 | 1,5 | -- |
| Ki | 0,5 | 0,5 | -- |
| Kd | 0,0 | 0,0 | -- |
| Ausgangsbereich | [-1,0 , 1,0] | [-1,0 , 1,0] | normiert |
| Regelfrequenz | 50 Hz (20 ms Takt) | 50 Hz (20 ms Takt) | Hz |

---

## D) Sensor-Mapping

### D.1 Sensoren im Gesamtsystem

| Sensor | Modell | Physischer Anschluss | Angeschlossen an | ROS2 Topic | ROS2 Message-Typ | TF Frame |
|--------|--------|---------------------|-------------------|------------|-------------------|----------|
| 2D-LiDAR | RPLIDAR A1M8 | USB (UART-Adapter) | Raspberry Pi 5 USB | `/scan` | `sensor_msgs/LaserScan` | `laser` |
| Kamera | RPi Global Shutter (IMX296) | CSI-2 Flachbandkabel | Raspberry Pi 5 CSI | `/camera/image_raw` | `sensor_msgs/Image` | `camera_link` |
| Encoder Links | Hall-Encoder (JGA25-370) | D6 (GPIO43), Interrupt | XIAO ESP32-S3 | (intern) | -- | -- |
| Encoder Rechts | Hall-Encoder (JGA25-370) | D7 (GPIO44), Interrupt | XIAO ESP32-S3 | (intern) | -- | -- |
| IMU | MPU6050 (GY-521) | I2C (D4=SDA, D5=SCL) | XIAO ESP32-S3 | (geplant) | `sensor_msgs/Imu` | `imu_link` |
| KI-Beschleuniger | Hailo-8L | PCIe 2.0 x1 (M.2 HAT) | Raspberry Pi 5 | (optional) | -- | -- |

### D.2 Odometrie (abgeleiteter Sensor)

Die Rad-Odometrie wird auf dem ESP32 aus den Encoder-Daten berechnet und als ROS2-Topic publiziert:

| Parameter | Wert |
|-----------|------|
| ROS2 Topic | `/odom` |
| Message-Typ | `nav_msgs/Odometry` |
| Publishrate | 20 Hz (alle 50 ms in `loop()`) |
| Frame ID | `odom` |
| Child Frame ID | `base_link` |
| Inhalt Pose | Position (x, y), Orientierung (Quaternion aus theta) |
| Inhalt Twist | Lineargeschwindigkeit (v), Winkelgeschwindigkeit (omega) |

### D.3 ArUco-Marker-Erkennung

Das ArUco-Docking-System (`aruco_docking.py`) nutzt die Global-Shutter-Kamera:

| Parameter | Wert |
|-----------|------|
| ROS2 Node | `aruco_docking` |
| Dictionary | `DICT_4X4_50` |
| Ziel-Marker-ID | 42 |
| Regelung | P-Regler (`kp_angular = 0.5`) |
| Annaeherungsgeschwindigkeit | 0,05 m/s |
| Docking-Kriterium | Marker-Breite > 150 Pixel |
| Ausgabe-Topic | `/cmd_vel` |

---

## E) Kommunikationspfade

### E.1 Kommunikationsmatrix

| Verbindung | Schnittstelle | Protokoll | Pins / Port | Baudrate / Takt | Richtung |
|------------|---------------|-----------|-------------|-----------------|----------|
| ESP32 <-> RPi5 | USB (CDC) | micro-ROS Serial Transport | USB-C (ESP32) <-> USB-A (Pi) | 115200 Baud | Bidirektional |
| ESP32 <-> MDD3A | GPIO (PWM) | Dual-PWM Steuerung | D0-D3 (GPIO1-4) | 20 kHz PWM | ESP32 -> MDD3A |
| ESP32 <-> Encoder | GPIO (Interrupt) | Pulserfassung (A-only) | D6 (GPIO43), D7 (GPIO44) | Ereignisgesteuert | Encoder -> ESP32 |
| ESP32 <-> IMU | I2C | I2C Fast Mode | D4=SDA (GPIO5), D5=SCL (GPIO6) | 400 kHz | Bidirektional |
| ESP32 <-> LED | GPIO (PWM) | LEDC PWM | D10 (GPIO9) | 5 kHz PWM | ESP32 -> MOSFET |
| RPi5 <-> LiDAR | USB | UART ueber USB-Adapter | USB-A Port | 115200 Baud | LiDAR -> Pi |
| RPi5 <-> Kamera | CSI-2 | MIPI CSI-2 | CSI-Connector | -- | Kamera -> Pi |
| RPi5 <-> Hailo | PCIe | PCIe 2.0 x1 | M.2 (via HAT) | 5 Gbps | Bidirektional |

### E.2 micro-ROS Transportschicht (Detail)

| Parameter | Wert | Quelle |
|-----------|------|--------|
| Transport | Serial (USB CDC) | `platformio.ini`: `board_microros_transport = serial` |
| ROS-Distribution | Humble | `platformio.ini`: `board_microros_distro = humble` |
| Initialisierung | `set_microros_serial_transports(Serial)` | `main.cpp` Zeile 102 |
| Serial-Baudrate | 115200 | `main.cpp` Zeile 101: `Serial.begin(115200)` |
| Node-Name | `esp32_bot` | `main.cpp` Zeile 110 |
| Agent-Seite | Raspberry Pi 5 (Docker-Container) | Laufzeitkonfiguration |
| Client-Seite | XIAO ESP32-S3 | `platformio.ini`: `board = esp32dev` |
| QoS (Odometrie) | `rmw_qos_profile_sensor_data` | `main.cpp` Zeile 118 |
| Zeitsynchronisation | `rmw_uros_sync_session(1000)` | `main.cpp` Zeile 122 |

### E.3 ROS2 Topics und Frames

| Topic | Message-Typ | Publisher | Subscriber | QoS |
|-------|-------------|-----------|------------|-----|
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 Controller / ArUco Docking | ESP32 (micro-ROS) | Default |
| `/odom` | `nav_msgs/Odometry` | ESP32 (micro-ROS) | Nav2, AMCL, SLAM Toolbox | Sensor Data |
| `/scan` | `sensor_msgs/LaserScan` | RPLidar Node | SLAM Toolbox, Nav2 Costmaps | Default |

### E.4 TF-Frame-Hierarchie

```
map
 └── odom                    (AMCL / SLAM Toolbox)
      └── base_link          (Odometrie, ESP32)
           ├── laser         (LiDAR-Montageposition)
           ├── camera_link   (Global Shutter Camera)
           └── imu_link      (MPU6050, geplant)
```

Die Frame-Bezeichnungen in den Konfigurationsdateien:

| Frame | Verwendung in | Konfigurationsparameter |
|-------|---------------|------------------------|
| `map` | SLAM Toolbox, Nav2 Global Costmap | `mapper_params.yaml: map_frame`, `nav2_params.yaml: global_frame` |
| `odom` | AMCL, SLAM Toolbox, Nav2 Local Costmap | `mapper_params.yaml: odom_frame`, `nav2_params.yaml: odom_frame_id` |
| `base_link` | AMCL, Costmaps, Odometrie | `mapper_params.yaml: base_frame`, `nav2_params.yaml: base_frame_id` |

### E.5 Datenfluss-Diagramm (Gesamtsystem)

```
+------------------------------------------------------------------+
|                    RASPBERRY PI 5 (Navigation)                    |
|                                                                  |
|  +-----------+    +------------+    +-----------+                |
|  | SLAM      |<---| /scan      |<---| RPLidar   |<-- USB        |
|  | Toolbox   |    +------------+    | A1 Node   |               |
|  +-----------+                      +-----------+                |
|       |                                                          |
|       | map + pose                                               |
|       v                                                          |
|  +-----------+    +-----------+    +------------+                |
|  | Nav2      |--->| /cmd_vel  |--->| micro-ROS  |--- USB-CDC --> |
|  | Stack     |    +-----------+    | Agent      |                |
|  +-----------+                     +------------+                |
|       ^                                 ^                        |
|       |                                 |                        |
|  +-----------+    +------------+        |                        |
|  | AMCL      |<---| /odom      |<-------+                       |
|  +-----------+    +------------+                                 |
|                                                                  |
|  +-----------+    +------------+                                 |
|  | ArUco     |--->| /cmd_vel   |  (Docking-Modus)               |
|  | Docking   |    +------------+                                 |
|  +-----------+                                                   |
|       ^                                                          |
|       |  CSI-2                                                   |
|  +-----------+                                                   |
|  | GS Camera |                                                   |
|  +-----------+                                                   |
+------------------------------------------------------------------+
          |  USB-CDC (115200 Baud, micro-ROS Humble)
          v
+------------------------------------------------------------------+
|                XIAO ESP32-S3 (Echtzeit-Regelung)                 |
|                                                                  |
|  Core 0 (micro-ROS)              Core 1 (Regelschleife)         |
|  +------------------+            +---------------------+         |
|  | cmd_vel          |  Mutex     | Inverse Kinematik   |         |
|  | Subscriber       |---------->| v,omega -> wl,wr    |         |
|  |                  |            |                     |         |
|  | Odometrie        |  Mutex     | PID-Regler (50 Hz)  |         |
|  | Publisher (20Hz) |<----------| Soll vs. Ist        |         |
|  +------------------+            +---------------------+         |
|                                       |           ^              |
|                                  PWM (D0-D3)  ISR (D6,D7)       |
|                                       v           |              |
|                                  +----------+ +----------+      |
|                                  | MDD3A    | | Encoder  |      |
|                                  | Motor    | | Hall     |      |
|                                  | Treiber  | | Sensoren |      |
|                                  +----------+ +----------+      |
|                                       |           |              |
|                                       v           |              |
|                                  +---------------------+         |
|                                  | JGA25-370 Motoren   |         |
|                                  | Links + Rechts      |         |
|                                  +---------------------+         |
+------------------------------------------------------------------+
```

### E.6 FreeRTOS Dual-Core-Partitionierung

| Core | Aufgabe | Task-Name | Prioritaet | Zykluszeit | Firmware-Funktion |
|------|---------|-----------|------------|------------|-------------------|
| Core 0 | micro-ROS Spin + Odometrie-Publish | Arduino `loop()` | Standard | 50 ms (Odom), 10 ms (Spin) | `loop()` |
| Core 1 | PID-Regelschleife + Encoder-Auswertung | `Ctrl` | 1 | 20 ms (50 Hz) | `controlTask()` |

Die Thread-Sicherheit zwischen den Cores wird durch einen **FreeRTOS Mutex** (`xSemaphoreCreateMutex()`) gewaehrleistet. Geteilte Daten im `SharedData`-Struct:

| Feld | Richtung | Beschreibung |
|------|----------|-------------|
| `tv`, `tw` | Core 0 -> Core 1 | Soll-Geschwindigkeiten (linear, angular) aus `cmd_vel` |
| `ox`, `oy`, `oth` | Core 1 -> Core 0 | Odometrie-Position (x, y, theta) |
| `ov`, `ow` | Core 1 -> Core 0 | Odometrie-Geschwindigkeiten (linear, angular) |

---

## Zusammenfassung der Diskrepanzen

Die folgende Tabelle fasst alle identifizierten Abweichungen zwischen `config.h` (Source of Truth), der aktuellen Firmware und den ROS2-Parametern zusammen:

| Parameter | config.h (Soll) | main.cpp (Ist) | Abweichung | Auswirkung |
|-----------|-----------------|----------------|------------|------------|
| Radradius | 0,0325 m | 0,032 m | -0,5 mm (1,5 %) | Geringe Odometrie-Drift |
| Spurbreite | 0,178 m | 0,145 m | -33 mm (18,5 %) | Erhebliche Fehler bei Drehungen |
| Ticks/Rev | 374 | 1440 | Faktor 3,85x | Geschwindigkeitsberechnung voellig falsch |
| Motor-Pins | D0-D3 (GPIO1-4) | GPIO 25,26,32,33 | Falsches Board | Motoren funktionieren nicht auf XIAO |
| Encoder-Pins | D6,D7 (GPIO43,44) | GPIO 18,19,22,23 | Falsches Board | Encoder funktionieren nicht auf XIAO |
| Encoder-Kanaele | A-only (1 Pin) | A+B (2 Pins) | Quadratur vs. Single | Unterschiedliche Auswertungslogik |
| Board-Typ | XIAO ESP32-S3 | `esp32dev` | Falsches Board in platformio.ini | Falsche Pin-Zuordnungen |

Diese Diskrepanzen resultieren daraus, dass die Firmware (`main.cpp`, `robot_hal.hpp`) noch fuer ein generisches ESP32-DevKit geschrieben wurde und noch nicht auf das XIAO ESP32-S3 Board und die Werte aus `config.h` migriert wurde.

---

*Dokument erstellt: 2026-02-11 | Projekt: AMR Bachelor-Thesis | Quellen: config.h v1.0.0, robot_hal.hpp, main.cpp, diff_drive_kinematics.hpp, platformio.ini, nav2_params.yaml, mapper_params_online_async.yaml, aruco_docking.py*
