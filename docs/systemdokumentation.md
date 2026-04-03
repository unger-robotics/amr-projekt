---
description: >-
  Systemdokumentation mit Anforderungen, Architektur, Datenfluessen
  und Validierungsplan nach VDI 2206.
---

# Systemdokumentation: Autonomer mobiler Roboter (AMR)

## 1. Systemuebersicht und Architektur

Wie laesst sich eine deterministische Echtzeitregelung fuer den Antrieb eines autonomen mobilen Roboters (AMR) synchron mit rechenintensiver Lokalisierung und Kartierung sowie Navigation betreiben?

Der Systementwurf loest diese Anforderung durch ein zweistufiges Echtzeitsystem. Die Architektur trennt die hardwarenahe Steuerung auf zwei Seeed Studio XIAO ESP32-S3 strikt von der Navigations- und Missionslogik auf einem Raspberry Pi 5. Die physische Trennung in Fahrkern, Sensor- und Sicherheitsbasis sowie Bedien- und Leitstandsebene schliesst unkontrollierte Systemzustaende durch Sensorlatenzen oder Berechnungsengpaesse systematisch aus.

### 1.1 Drei-Ebenen-Modell

Die Steuerung gliedert sich in drei Ebenen:

| Ebene | Bezeichnung | Komponenten | Aufgabe |
|-------|-------------|-------------|---------|
| A | Fahrkern sowie Sensor- und Sicherheitsbasis | Drive-Knoten, Sensor-Knoten (ESP32-S3) | Echtzeit-Regelung, Sensorerfassung, Sicherheits-Basisfunktionen |
| B | Bedien- und Leitstandsebene | Pi 5 (ROS2, Nav2, SLAM Toolbox), Benutzeroberflaeche (React) | Koordination, Kartierung, Navigation, Fernsteuerung |
| C | Intelligente Interaktion | Hailo-8L, Gemini Cloud, gTTS, ReSpeaker | Objekterkennung, Sprachausgabe, semantische Beschreibung |

Ebene A arbeitet autonom — der CAN-Notstopp funktioniert ohne Pi 5. Ebene B setzt auf die micro-ROS-Kommunikation mit Ebene A auf. Ebene C ist vollstaendig optional und ueber Launch-Argumente zuschaltbar.

### 1.2 Kommunikationspfade (Dual-Path)

Die MCU-Knoten kommunizieren ueber zwei parallele Kanaele mit dem Pi 5:

- **micro-ROS/UART (primaer):** ROS2-Topics via Serial Transport (XRCE-DDS) bei 921600 Baud. Subscriber und Publisher uebertragen Steuerkommandos und Telemetrie. Die Anbindung erfolgt ueber stabile udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`).
- **CAN-Bus (sekundaer):** 1 Mbit/s (ISO 11898), SN65HVD230-Transceiver auf den ESP32-S3-Knoten, MCP2515/SocketCAN auf dem Pi 5. Fire-and-forget-Diagnostik und sicherheitskritische Signale (Cliff, Batterie-Shutdown).

CAN-Sends laufen auf Core 1 der jeweiligen MCU-Knoten (`controlTask` bzw. `sensorTask`), damit sie unabhaengig vom micro-ROS Agent funktionieren. Zwei parallele Pfade sichern die Zuverlaessigkeit ab: Der ROS2-Pfad ueber den Pi 5 reagiert in circa 50 ms, der CAN-Pfad direkt zwischen den Knoten in weniger als 20 ms.

### 1.3 Vollstaendiges Systemdiagramm

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Ebene C — Intelligente Interaktion (optional)                                  │
│                                                                                 │
│  [Host: Hailo-8L Runner]──UDP:5005──>[Docker: hailo_udp_receiver]               │
│       YOLOv8 5 Hz                       │                                       │
│                                         ▼                                       │
│                                  /vision/detections                             │
│                                         │                                       │
│                                         ▼                                       │
│                              [gemini_semantic_node]──>/vision/semantics          │
│                               Gemini 3.1 flash-lite         │                   │
│                                                             ▼                   │
│                                                      [tts_speak_node]           │
│                                                       gTTS → mpg123            │
│  [ReSpeaker DoA]──>/sound_direction                    → MAX98357A I2S          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Ebene B — Bedien- und Leitstandsebene                                          │
│                                                                                 │
│  ┌── Docker-Container (ros:humble, network_mode:host, privileged) ───────────┐  │
│  │                                                                           │  │
│  │  [micro-ROS Agent x2]   [SLAM Toolbox]   [Nav2]   [odom_to_tf]           │  │
│  │    /dev/amr_drive          /map            /cmd_vel   odom→base_link      │  │
│  │    /dev/amr_sensor         /scan                                          │  │
│  │                                                                           │  │
│  │  [cliff_safety_node]   [audio_feedback_node]   [can_bridge_node]          │  │
│  │    /nav_cmd_vel →          /audio/play →          SocketCAN →             │  │
│  │    /cmd_vel                aplay → /dev/snd       Queue 512, 100 Hz       │  │
│  │                                                                           │  │
│  │  [dashboard_bridge]                                                       │  │
│  │    WSS:9090 ◄──► ROS2 Topics                                             │  │
│  │    MJPEG:8082 ← /image_raw                                               │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  [Browser: Benutzeroberflaeche React/Vite]  HTTPS:5173                          │
│    Zustand Store ◄──► useWebSocket ◄──WSS:9090──► dashboard_bridge              │
│    Joystick → cmd_vel 10 Hz, Heartbeat 5 Hz                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Ebene A — Fahrkern                                                             │
│                                                                                 │
│  [Drive-Knoten ESP32-S3]              [Sensor-Knoten ESP32-S3]                  │
│    Core 0: micro-ROS Executor         Core 0: micro-ROS Executor                │
│      Sub: /cmd_vel, /hardware_cmd       Sub: /servo_cmd, /hardware_cmd          │
│      Pub: /odom 20 Hz                   Pub: /range, /cliff, /imu, /battery     │
│    Core 1: PID 50 Hz, Encoder,        Core 1: Sensorerfassung                   │
│      CAN TX/RX                          (Cliff 20 Hz, US 10 Hz,                │
│                                          IMU 50 Hz, Batt 2 Hz), CAN TX         │
│         │          ▲                       │          ▲                          │
│         │ UART     │ UART                  │ UART     │ UART                    │
│         │ 921600   │ 921600                │ 921600   │ 921600                  │
│         ▼          │                       ▼          │                          │
│      [Pi 5 /dev/amr_drive]          [Pi 5 /dev/amr_sensor]                      │
│                                                                                 │
│  ───── CAN-Bus 1 Mbit/s (MCP2515/TWAI) ─────                                   │
│    Drive ◄──0x120 Cliff──► Sensor                                               │
│    Drive ◄──0x141 Battery──► Sensor                                             │
│    + Diagnostik-Frames (bidirektional)                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Hardware-Komponenten

### 2.1 Antriebsstrang

Der Differentialantrieb nutzt zwei JGA25-370-Gleichstrommotoren mit integrierten Hall-Encodern (11 CPR, Uebersetzung 1:34). Ein Cytron MDD3A Dual-Motortreiber steuert die Motoren im Dual-PWM-Modus an. Die PWM-Frequenz betraegt 20 kHz bei einer Aufloesung von 8 Bit (Wertebereich 0 bis 255). Die empirisch ermittelte Anlaufschwelle (PWM-Deadzone) liegt bei 35. Unterhalb dieses Werts erzeugt der Antrieb kein ausreichendes Anlaufmoment.

Die kinematischen Parameter definieren das Bewegungsmodell. Der kalibrierte Raddurchmesser betraegt 65,67 mm. Die Spurbreite betraegt 178 mm. Die Encoder liefern im 2x-Quadraturmodus 748,6 (links) und 747,2 (rechts) Ticks pro Radumdrehung. Die Wegaufloesung betraegt demnach 0,276 mm pro Tick.

Details zu allen Parametern siehe [robot_parameters.md](robot_parameters.md).

### 2.2 Sensorik

**LiDAR:** Der RPLIDAR A1 ist rueckwaerts auf dem Roboter montiert. Die Montage entspricht einer Yaw-Rotation von 180 Grad relativ zum Basis-Koordinatensystem (`base_link`). Der Scanner liefert Laserdaten mit 7,0 Hz (konfiguriert; Messwert: 7,7 Hz, Datenblatt: 5,5 Hz typisch) ueber `/dev/ttyUSB0` bei 115200 Baud. Die maximale Reichweite betraegt 12 m.

**IMU:** Eine MPU6050 (Inertial Measurement Unit) misst Beschleunigungen (+/- 2 g) und Drehraten (+/- 250 deg/s) am I2C-Bus (400 kHz, Adresse 0x68). Ein Komplementaerfilter (Alpha = 0,98) fusioniert Gyroskop-Integration (98 %) und Encoder-Heading (2 %). Die Soll-Rate der Publikation auf `/imu` liegt bei 50 Hz.

**Cliff-Sensor:** Ein MH-B-Infrarotsensor erkennt Kanten per GPIO-Poll mit 20 Hz. Der Sensor-Knoten publiziert den Status auf `/cliff`.

**Ultraschall:** Ein HC-SR04 misst Distanzen mit 10 Hz per ISR-basiertem Trigger/tryRead-Pattern. Die Reichweite liegt zwischen 0,02 und 4,00 m.

**Kamera:** Eine Sony-IMX296-Global-Shutter-Kamera ermoeglicht visuelles Docking. Die native Sensoraufloesung von 1456 x 1088 Pixeln (1440 x 1088 effektiv) bei 15 fps skaliert eine `v4l2loopback`-Bridge auf 640 x 480 Pixel herunter.

**Leistungsmonitor:** Ein INA260 (I2C, Adresse 0x40) erfasst Spannung, Strom und Leistung des Akkupacks mit 2 Hz.

### 2.3 Recheneinheiten

Zwei Seeed Studio XIAO ESP32-S3 arbeiten als echtzeitfaehige Steuerungseinheiten. Das Dual-Core-Design (240 MHz) trennt Kommunikations- und Regelaufgaben. Die USB-CDC-Verbindung operiert mit 921600 Baud.

Der Raspberry Pi 5 (Debian Trixie, aarch64) uebernimmt Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene. ROS 2 Humble laeuft containerisiert (`ros:humble-ros-base`), da das Betriebssystem kein natives Paket bereitstellt. Der Container nutzt den Host-Network-Modus fuer DDS-Multicast und laeuft mit `privileged: true` fuer den Zugriff auf serielle Geraete, Audio-Hardware und SocketCAN.

### 2.4 Stromversorgung und Batteriemanagement

Das Akkupack besteht aus Samsung INR18650-35E Zellen in 3S1P-Konfiguration (NCA, 10,80 V / 3,35 Ah min / 3,5 Ah nom). Die Spannungsbereiche erstrecken sich von 12,60 V (voll geladen) bis zur Entladeschlussspannung. Firmware-Schwellen: 9,0 V System-Shutdown, 7,5 V BMS-Disconnect (config_sensors.h:83-84). 7,95 V ist die Samsung-Zell-Entladeschlussspannung (3 x 2,65 V), kein Firmware-Wert.

Die Batterieueberwachung erfolgt ueber den INA260-Leistungsmonitor am Sensor-Knoten. Bei Unterschreitung von 9,5 V loest der Knoten ein `/battery_shutdown`-Event an den Drive-Knoten aus. Die Hysterese betraegt 0,3 V, sodass die Wiederfreigabe erst bei 9,8 V erfolgt. Zusaetzlich sendet der Sensor-Knoten ein CAN-Frame (0x141) als redundanten Abschaltpfad.

Die Prozentberechnung verwendet lineare Interpolation im Bereich 9,0 bis 12,6 V.

Details zu allen Batterie- und INA260-Registerwerten siehe [robot_parameters.md](robot_parameters.md).

## 3. Firmware (ESP32-S3)

### 3.1 Zwei-Knoten-Architektur

Die Firmware besteht aus zwei getrennten PlatformIO-Projekten. Jeder ESP32-S3 erhaelt eine eigene micro-ROS-Library (statisch kompiliert).

| Eigenschaft | Drive-Knoten (Fahrkern) | Sensor-Knoten (Sensor- und Sicherheitsbasis) |
|---|---|---|
| Verzeichnis | `amr/mcu_firmware/drive_node/` | `amr/mcu_firmware/sensor_node/` |
| Konfiguration | `include/config_drive.h` (v4.0.0) | `include/config_sensors.h` (v3.0.0) |
| udev-Symlink | `/dev/amr_drive` | `/dev/amr_sensor` |
| Baudrate | 921600 (micro-ROS UART) | 921600 (micro-ROS UART) |
| Funktion | Motoren, PID, Encoder, Odometrie, LED | IMU, Ultraschall, Cliff, Batterie, Servo |
| CAN-ID-Bereich | 0x200–0x2FF | 0x110–0x1F0 |

Beide Projekte verwenden `static_assert`-Anweisungen zur Kompilierzeit-Absicherung der Konfiguration. Pins und PWM-Parameter liegen in typisierten `inline constexpr`-Konstanten im `amr::`-Namespace — keine `#define`-Makros.

### 3.2 Dual-Core-Pattern (FreeRTOS)

Beide Knoten verwenden dasselbe Dual-Core-Pattern mit fester Core-Zuordnung:

**Core 0 (Arduino `loop()`):**
- micro-ROS Executor: `spin_some()` fuer Publisher und Subscriber
- Servo-I2C-Writes (nur Sensor-Knoten, PCA9685)
- Zyklusrate circa 500 Hz

**Core 1 (FreeRTOS Task):**
- Drive-Knoten: PID-Regelung (50 Hz), Encoder-Polling, CAN-Send und -Empfang
- Sensor-Knoten: IMU-Reads (50 Hz), Ultraschall (10 Hz), Cliff (20 Hz), Batterie (2 Hz), CAN-Sends

**Synchronisation:** Ein `SharedData`-Struct mit Mutex (`SemaphoreHandle_t`) schuetzt den Datenaustausch zwischen Core 0 und Core 1. Der Sensor-Knoten sichert zusaetzlich den I2C-Bus mit einem `i2c_mutex` (5 ms Timeout). Die I2C-Zugriffe sind nach Core aufgeteilt: Reads (MPU6050, INA260) auf Core 1, Writes (PCA9685) auf Core 0.

**Inter-Core-Watchdog:** Core 0 prueft periodisch den Zeitstempel `core1_heartbeat` von Core 1. Bei Ausbleiben ueber 50 Zyklen (circa 1 s) versetzt der Watchdog das System in einen sicheren Zustand (Failsafe-Stopp).

### 3.3 Drive-Knoten: PID-Regelung und Odometrie

Die Regelschleife auf Core 1 laeuft mit 50 Hz:

```
Encoder-Ticks → Ist-Geschwindigkeit (m/s) → PID → PWM-Duty → Motor
                                                ↑
                                      Soll-Geschwindigkeit (aus /cmd_vel)
```

Der PID-Regler verwendet exponentiell geglaettete Encoder-Werte (EMA, Alpha = 0,3), um Quantisierungsrauschen zu mindern. Die Odometrie hingegen verwendet die ungefilterten Encoder-Rohdaten. Die Regelstrecke umfasst: Inverskinematik berechnen, Anti-Windup beruecksichtigen, Beschleunigungsrampe (max. 5,0 rad/s^2) anwenden und PWM ausgeben.

Sicherheitsmechanismen im Fahrkern:
- **Failsafe-Timeout:** Motoren stoppen nach 500 ms ohne eingehende `/cmd_vel`-Kommandos
- **Hard-Stop:** Bei |tv| < 0,01 wird die PID-Rampe umgangen — sofortiger Stillstand in unter 20 ms
- **Stillstandserkennung:** Sollwert nahe Null fuehrt zur PID-Umgehung, PWM wird direkt auf 0 gesetzt

Die Odometrie-Publikation auf `/odom` erfolgt mit 20 Hz. Da micro-ROS keinen TF-Broadcast bereitstellt, konvertiert der Knoten `odom_to_tf` auf dem Pi 5 die Nachrichten in die dynamische TF-Transformation `odom → base_link`.

Details zu PID-Parametern und Timing siehe [robot_parameters.md](robot_parameters.md).

### 3.4 Sensor-Knoten: Sensorerfassung und I2C-Bus

Der Sensor-Knoten erfasst alle externen Sensordaten und publiziert sie ueber micro-ROS:

| Sensor | Rate | Topic | Beschreibung |
|---|---|---|---|
| Cliff (MH-B IR) | 20 Hz | `/cliff` | Kantenerkennung per GPIO-Poll |
| Ultraschall (HC-SR04) | 10 Hz | `/range/front` | Distanzmessung per ISR |
| IMU (MPU6050) | 50 Hz | `/imu` | Beschleunigung und Drehrate |
| Batterie (INA260) | 2 Hz | `/battery` | Spannung, Strom, Leistung |

Drei Geraete teilen sich den I2C-Bus (Wire, 400 kHz Fast-Mode):

| Geraet | Adresse | Zugriff | Core |
|---|---|---|---|
| MPU6050 | 0x68 | Read (50 Hz) | Core 1 |
| INA260 | 0x40 | Read (2 Hz) | Core 1 |
| PCA9685 | 0x41 (A0-Loetbruecke) | Write (bei Aenderung) | Core 0 |

Die Init-Reihenfolge ist relevant: PCA9685 vor MPU6050 und INA260 initialisieren, um einen sauberen I2C-Bus sicherzustellen. Ein `delay(2000)` vor `Wire.begin()` ist erforderlich.

Alle I2C-Zugriffe in Callbacks sind verboten. Stattdessen gilt das Deferred-Pattern: Callback setzt RAM-Struct, `loop()` oder `sensorTask` fuehrt den I2C-Zugriff aus.

### 3.5 LED-Steuerung

Der Drive-Knoten steuert einen SMD 5050 LED-Streifen via IRLZ24N-MOSFET, LEDC PWM 5 kHz. Die Konfiguration erfolgt ueber das `/hardware_cmd`-Topic (z-Feld = LED-PWM 0–255). Drei Betriebsmodi signalisieren den Systemzustand:

- **Idle:** Cyan pulsierend
- **Fahrt:** Gruen
- **Fehler:** Rot blinkend

## 4. CAN-Bus

### 4.1 Hardware und Topologie

Der CAN-Bus verbindet die beiden ESP32-S3-Knoten direkt miteinander. Optional empfaengt der Pi 5 ueber einen MCP2515/SocketCAN-Adapter die Frames fuer Diagnose und Protokollierung.

- **Bitrate:** 1 Mbit/s (ISO 11898)
- **Transceiver:** SN65HVD230 auf beiden ESP32-S3-Knoten
- **ESP32-S3-Treiber:** TWAI (Two-Wire Automotive Interface)
- **Pi 5-Treiber:** MCP2515 ueber SPI, SocketCAN-Kernel-Modul
- **TX-Timeout:** 10 ms (Drive-Knoten) / 3 ms (Sensor-Knoten)

### 4.2 Frame-Definitionen

**Drive-Knoten CAN-Frames (0x200–0x2FF):**

| ID | Inhalt | Rate | Bytes |
|---|---|---|---|
| 0x200 | Odom Position (x, y als 2x float32 LE) | 20 Hz | 8 |
| 0x201 | Odom Heading + Speed (yaw, v_linear als 2x float32 LE) | 20 Hz | 8 |
| 0x210 | Rad-Geschwindigkeit (L, R als 2x float32 rad/s) | 10 Hz | 8 |
| 0x220 | Motor-PWM (L, R als int16) | 10 Hz | 4 |
| 0x2F0 | Heartbeat (flags uint8 + uptime_mod256 uint8) | 1 Hz | 2 |

**Sensor-Knoten CAN-Frames (0x110–0x1F0):**

| ID | Inhalt | Rate | Bytes |
|---|---|---|---|
| 0x110 | Ultraschall Range (float32 LE, Meter) | 10 Hz | 4 |
| 0x120 | Cliff (uint8: 0=OK, 1=Cliff) | 20 Hz | 1 |
| 0x130 | IMU ax, ay, az (mg) + gz (0.01 rad/s) (4x int16) | 50 Hz | 8 |
| 0x131 | IMU Heading (float als float32) | 50 Hz | 4 |
| 0x140 | Batterie V/I/P (uint16 mV + int16 mA + uint16 mW) | 2 Hz | 6 |
| 0x141 | Battery Shutdown (uint8: 0=OK, 1=Shutdown) | Event | 1 |
| 0x1F0 | Heartbeat (flags uint8 + uptime_mod256 uint8) | 1 Hz | 2 |

Reservierter ID-Bereich: 0x110–0x1F0.

### 4.3 CAN-Notstopp-Redundanzpfad

Der Drive-Knoten empfaengt Cliff-Signale (0x120) und Battery-Shutdown-Signale (0x141) vom Sensor-Knoten ueber den CAN-Bus und stoppt die Motoren direkt — unabhaengig von Pi 5 und micro-ROS.

**Datenfluss:**

```
Sensor-Knoten (Core 1, sensorTask)
  ├── CAN 0x120 (Cliff, 20 Hz, 1 Byte: 0x00=OK, 0x01=Cliff)
  └── CAN 0x141 (Battery Shutdown, Event, 1 Byte: 0x00=OK, 0x01=Shutdown)
        │
        ▼
Drive-Knoten (Core 1, controlTask, non-blocking receive)
  → can_cliff_stop / can_battery_stop Flags
  → tv=0, tw=0 (Motoren stoppen)
```

**Eigenschaften des Redundanzpfads:**

- **Latenz:** Weniger als 20 ms (ein `controlTask`-Zyklus bei 50 Hz)
- **Unabhaengigkeit:** Funktioniert ohne laufenden Pi 5, Docker-Container oder micro-ROS Agent
- **Nicht-latched:** Der Cliff-Stop folgt dem aktuellen Sensor-Zustand und setzt sich automatisch zurueck
- **Non-blocking:** `twai_receive()` mit `pdMS_TO_TICKS(0)` blockiert die PID-Schleife nicht
- **Redundanz:** Ergaenzt den bestehenden ROS2-Pfad (`/cliff` → `cliff_safety_node` → `/cmd_vel`)

Dieser CAN-Pfad bildet die Rueckfallebene fuer den Fall, dass der Pi 5, der Docker-Container oder die micro-ROS-Verbindung ausfallen. Zusammen mit dem Failsafe-Timer (500 ms) und dem Inter-Core-Watchdog entsteht eine gestaffelte Sicherheitsarchitektur, die auf MCU-Ebene autonom agiert.

---

## 5. ROS2-Stack

### 5.1 Docker-Container und Laufzeitumgebung

ROS 2 Humble laeuft auf dem Raspberry Pi 5 in einem Docker-Container auf Basis des Images `ros:humble-ros-base` (Ubuntu 22.04, arm64). Debian Trixie auf dem Host stellt kein natives ROS2-Paket bereit (Trixie ist in REP-2000 nicht als unterstuetzte Plattform fuer ROS 2 Humble gelistet), weshalb die Containerisierung zwingend erforderlich ist. Der Container arbeitet im Host-Network-Modus (`network_mode: host`), um DDS-Multicast ohne Netzwerkbruecke zu ermoeglichen. Der privilegierte Modus gewaehrleistet den Zugriff auf serielle Geraete, Audio-Hardware und SocketCAN.

Die Container-Konfiguration in `docker-compose.yml` bindet die seriellen Geraete (`/dev/amr_drive`, `/dev/amr_sensor`, `/dev/ttyUSB0`) sowie das Audio-Device (`/dev/snd`) als Devices ein. Das ROS2-Paket `my_bot` wird als Volume im Lese-Schreib-Modus gemountet, die Skripte doppelt (`/amr_scripts` und `/scripts`), damit Symlinks in beiden Kontexten aufgeloest werden. Benannte Volumes (`ros2_build`, `ros2_install`) cachen die Build-Artefakte.

Der Convenience-Wrapper `run.sh` verwaltet den Container-Lebenszyklus. Er startet den Container bei Bedarf ueber `docker compose up -d`, legt udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`) im Container an und prueft die Kamera-Bridge bei aktivierter Kamera. Ein Rebuild erfolgt ueber:

```
./run.sh colcon build --packages-select my_bot --symlink-install
```

Die Skripte in `amr/scripts/` werden als Symlinks in `my_bot/my_bot/` referenziert und ueber `setup.py` entry_points als `ros2 run my_bot <name>` ausfuehrbar gemacht. Insgesamt stehen 29 Executables bereit: 11 Runtime-Knoten und 18 Validierungstests. Umgebungsvariablen (`ROS_DOMAIN_ID`, `GEMINI_API_KEY`) werden ueber `docker-compose.yml` an den Container durchgereicht.

### 5.2 Knoten-Uebersicht

Das zentrale Launch-File `full_stack.launch.py` orchestriert alle ROS2-Knoten. Vier Basisknoten (RPLidar, Laser-TF, micro-ROS-Agent Drive, odom_to_tf) sind immer aktiv. Zwoelf optionale Knoten (SLAM, Nav2, Cliff-Safety, Dashboard, Vision, Audio, CAN, TTS, ReSpeaker, Voice) werden ueber boolesche Launch-Parameter gesteuert. Insgesamt stehen 29 Executables bereit: 11 Runtime-Knoten und 18 Validierungstests.

Vollstaendige Knotenliste mit allen Parametern: [ros2_system.md](ros2_system.md)

### 5.3 Topic-Architektur und QoS

Die Topic-Struktur trennt Fahrkommandos, Odometrie, Sensorik und Navigationsdaten. Die MCU-Knoten publizieren ueber micro-ROS: Der Fahrkern sendet Odometrie (`/odom`, 20 Hz, Reliable) und empfaengt Geschwindigkeitsvorgaben (`/cmd_vel`). Die Sensor- und Sicherheitsbasis publiziert IMU (`/imu`, 50 Hz Soll), Batterie (`/battery`, 2 Hz), Ultraschall (`/range/front`, 10 Hz) und Cliff-Status (`/cliff`, 20 Hz, Best-Effort).

Auf Pi-5-Seite liefert der RPLidar-Knoten Laserscandaten (`/scan`, 7,0 Hz). Der Cliff-Safety-Knoten empfaengt `/nav_cmd_vel` und `/dashboard_cmd_vel` und leitet sie gefiltert an `/cmd_vel` weiter. Die Vision-Pipeline publiziert Erkennungen (`/vision/detections`, 5 Hz) und semantische Beschreibungen (`/vision/semantics`).

Die QoS-Konfiguration folgt den Einschraenkungen von XRCE-DDS: Die maximale MTU betraegt 512 Bytes. Nachrichten oberhalb dieser Grenze — insbesondere `/odom` (ca. 725 Bytes) und `/imu` (ca. 550 Bytes) — erfordern Reliable-QoS mit Fragmentierung bis 2048 Bytes. Kleine Nachrichten wie `/cliff` verwenden Best-Effort-QoS. Auf Subscriber-Seite muss die QoS-Policy uebereinstimmen, andernfalls gehen Nachrichten verloren.

Vollstaendige Topic-Tabelle: [ros2_system.md](ros2_system.md)

### 5.4 TF-Baum

Der Transformationsbaum folgt der Kette `odom → base_link → laser/camera_link/ultrasonic_link`. Da micro-ROS keinen TF-Broadcast bereitstellt, konvertiert der Knoten `odom_to_tf` die `/odom`-Nachrichten mit 20 Hz in die dynamische Transformation `odom` → `base_link`. Der LiDAR ist 180 Grad gedreht montiert; die statische TF-Transformation (`yaw=pi`) kompensiert diese Orientierung.

Vollstaendiger TF-Baum mit Frame-Offsets: [ros2_system.md](ros2_system.md)

### 5.5 Launch-System

`full_stack.launch.py` steuert alle Knoten ueber 13 boolesche Launch-Argumente (`use_<name>:=True/False`). Die Standardkonfiguration aktiviert SLAM, Navigation und Cliff-Safety. Optionale Teilsysteme (Dashboard, Kamera, Vision, Audio, CAN, TTS, ReSpeaker) sind standardmaessig deaktiviert.

Bei aktivierter Cliff-Safety (`use_cliff_safety:=True`, Standard) wird die `dashboard_bridge` per Launch-Remapping von `/cmd_vel` auf `/dashboard_cmd_vel` umgeleitet. Nav2 publiziert separat auf `/nav_cmd_vel`. Beide Kanaele laufen ueber den Cliff-Safety-Multiplexer, bevor sie den Fahrkern erreichen.

Vollstaendige Launch-Parameter und Startkombinationen: [build_and_deploy.md](build_and_deploy.md)

---

## 6. Lokalisierung und Kartierung sowie Navigation

### 6.1 SLAM Toolbox

`slam_toolbox` arbeitet im asynchronen Online-Modus und nutzt den Ceres-Solver (SPARSE_NORMAL_CHOLESKY) zur nichtlinearen Optimierung der Pose. Der Knoten erzeugt eine Belegungskarte mit 5 cm Aufloesung und einer maximalen LiDAR-Reichweite von 12 m. Loop Closure ist aktiv mit einem Suchradius von 8 m und einer Mindestkettenlenge von 10 Scans.

Der SLAM-Knoten abonniert `/scan` und `/tf` und publiziert die Belegungskarte auf `/map`. Die Kartenaktualisierung erfolgt asynchron, um die CPU-Last auf dem Raspberry Pi 5 zu begrenzen. Die Parameter liegen in `config/mapper_params_online_async.yaml`.

### 6.2 Nav2 (AMCL, NavFn, Regulated Pure Pursuit)

Die Navigation erfolgt in drei Schritten. Zuerst erzeugt `slam_toolbox` die Belegungskarte. Danach verfeinert AMCL (Adaptive Monte Carlo Localization) die Pose mit 500 bis 2000 Partikeln im Differentialantriebs-Modell und publiziert die Transformation `map` → `odom`. Abschliessend berechnet NavFn mit 10 Hz einen globalen Pfad, waehrend Regulated Pure Pursuit mit 20 Hz die lokale Bahnverfolgung bei maximal 0,15 m/s ausfuehrt.

Der Goal Checker akzeptiert den Zielpunkt bei einer Positionstoleranz von 3 cm (0,03 m) und einer Yaw-Toleranz von 0,05 rad (2,9 Grad). Die Nav2-Parameter liegen in `config/nav2_params.yaml`.

### 6.3 Costmaps

Die lokale Costmap (Kostenkarte zur Hindernisvermeidung) nutzt ein Rolling Window von 3 x 3 m. Sie kombiniert einen VoxelLayer fuer die 3D-Hinderniserfassung und einen InflationLayer fuer den Sicherheitsabstand bei einem Inflationsradius von 25 cm. Die globale Costmap verwendet die statische Belegungskarte aus dem SLAM-Prozess und erweitert diese ebenfalls um einen InflationLayer.

Die Costmap-Konfiguration stellt sicher, dass der Roboter ausreichend Abstand zu Hindernissen haelt, ohne die nutzbaren Fahrwege uebermassig einzuschraenken. Der Inflationsradius von 25 cm entspricht dabei dem halben Roboterdurchmesser zuzueglich eines Sicherheitszuschlags.

---

## 7. Bedien- und Leitstandsebene

### 7.1 Dashboard-Architektur (React/Vite)

Die Benutzeroberflaeche basiert auf React 19 mit TypeScript, Vite als Build-Tool und Tailwind CSS fuer das Styling. Das State Management erfolgt ueber Zustand mit einem zentralen Store (`telemetryStore.ts`, 60+ Properties). Die Joystick-Steuerung basiert auf nipplejs und sendet Fahrbefehle mit 10 Hz. Ein Heartbeat-Signal wird parallel mit 5 Hz gesendet. Die Anwendung gliedert sich in zwei Seiten:

**Steuerung (Standardansicht):** 6er-Grid-Layout mit Sidebar (Status, Systemmetriken, Kommandofeld), Kamerastream mit Detection-Overlay, SLAM-Karte mit Klick-Navigation, LiDAR-Polaransicht, Joystick (nipplejs) und Servo-/Hardware-Steuerung.

**Details:** 2-Spalten-Grid mit ActiveDevicesPanel (6 Geraete-Status mit Hz-Raten), SensorDetailPanel (IMU, Ultraschall, Cliff), AudioPanel (ReSpeaker DoA, Voice Activity, Sounds) und RobotInfoPanel (Position, Yaw, Servo, Hardware-Grenzen).

Die HTTPS-Verschluesselung erfolgt ueber mkcert-Zertifikate (`amr.local+5.pem`, `amr.local+5-key.pem`). Ohne Zertifikate greift ein Fallback auf unverschluesseltes HTTP/WS. Das visuelle Design folgt einem SciFi-HUD-Theme mit dunklem Hintergrund, Cyan-Akzenten und der Monospace-Schrift JetBrains Mono.

Die Entwicklung des Dashboards erfordert zwei parallele Prozesse: den ROS2-Launch mit `use_dashboard:=True` im Container und den Vite-Entwicklungsserver (`npm run dev -- --host 0.0.0.0`) auf dem Host. Die Benutzeroberflaeche ist dann unter `https://amr.local:5173` erreichbar.

Detaillierte Komponentenbeschreibung: [dashboard.md](dashboard.md)

### 7.2 WebSocket-Protokoll

Die Kommunikation zwischen Benutzeroberflaeche und `dashboard_bridge` erfolgt ueber WebSocket auf Port 9090 (`wss://amr.local:9090` bei HTTPS, `ws://localhost:9090` als Fallback). Der Auto-Reconnect arbeitet mit exponentieller Verzoegerung (1 s, 2 s, 4 s, 8 s). Die Latenz wird clientseitig ueber `Date.now() - msg.ts * 1000` gemessen und im StatusPanel angezeigt.

**Vom Server empfangene Nachrichten:**

| Operation | Rate | Beschreibung |
|---|---|---|
| `telemetry` | 10 Hz | Odometrie, IMU, Batterie, Servo, Hardware-Status |
| `scan` | 2 Hz | LiDAR-Ranges (komprimiert) |
| `system` | 1 Hz | CPU, RAM, Disk, Geraete-Status, Netzwerk |
| `map` | ~0,5 Hz | SLAM-Karte (PNG Base64), Roboter-Position |
| `vision_detections` | 5 Hz | Hailo-8L Erkennungen (BBox, Label, Confidence) |
| `vision_semantics` | ~0,5 Hz | Gemini-Szenenbeschreibung |
| `nav_status` | 1 Hz | Navigationsstatus, Ziel, Restdistanz |
| `sensor_status` | 2 Hz | Ultraschall, Cliff, IMU-Hz |
| `audio_status` | 2 Hz | ReSpeaker DoA, Voice Activity |
| `command_response` | — | Antwort auf Freitext-Kommando |

**Vom Client gesendete Nachrichten:**

| Operation | Rate | Beschreibung |
|---|---|---|
| `cmd_vel` | 10 Hz | Fahrbefehl (linear_x, angular_z) |
| `heartbeat` | 5 Hz | Deadman-Signal |
| `servo_cmd` | 10 Hz | Pan/Tilt-Position (throttled) |
| `hardware_cmd` | 10 Hz | Motor-Limit, Servo-Speed, LED-PWM (throttled) |
| `nav_goal` | — | Navigationsziel (x, y, yaw) |
| `nav_cancel` | — | Navigationsziel abbrechen |
| `audio_play` | — | Sound-Wiedergabe (sound_key) |
| `audio_volume` | 5 Hz | Lautstaerke 0–100 % (throttled) |
| `vision_control` | — | Vision ein/aus |
| `command` | — | Freitext-Kommando |

### 7.3 MJPEG-Kamerastream

Der Kamerastream wird ueber HTTPS auf Port 8082 bereitgestellt (`https://amr.local:8082/stream`). Die `dashboard_bridge` konvertiert die ROS2-Bilddaten (`/camera/image_raw`) in einen MJPEG-Stream, der direkt in ein HTML-`<img>`-Tag eingebunden wird. Beide Server (WebSocket und MJPEG) nutzen dieselben mkcert-Zertifikate. Die Zertifikate werden ueber einen Volume-Mount (`/dashboard:ro`) im Container bereitgestellt.

Ein Klick auf die SLAM-Karte in der Benutzeroberflaeche sendet ein `nav_goal` per WebSocket an die `dashboard_bridge`, die daraufhin ein Nav2 `NavigateToPose` Action Goal absetzt. Der Navigationsstatus wird per `nav_status` (1 Hz) an den Client zurueckgemeldet. Ein laufendes Ziel laesst sich per `nav_cancel` abbrechen.

---

## 8. Vision-Pipeline und Audio

### 8.1 Hybride Vision-Pipeline (Hailo-8L + Gemini)

Die Vision-Pipeline ueberbrueckt eine Kompatibilitaetsluecke: Der host-seitig installierte NPU-Treiber (`hailort`) ist an die Python-3.13-Umgebung von Raspberry Pi OS Trixie gebunden und laesst sich nicht in den Docker-Container (Python 3.10) uebertragen. Die Loesung ist eine UDP-Bruecke innerhalb von localhost. Der Hailo-8L verbraucht typisch 1,5 W (maximal 6,6 W am PCIe-Bus).

Die verwendeten Netzwerkports sind:

| Port | Protokoll | Zweck |
|---|---|---|
| 5005 | UDP | Hailo-Detektionen (Host → Docker) |
| 8082 | HTTPS | MJPEG-Kamerastream |
| 9090 | WSS | Dashboard-Telemetrie |
| 5173 | HTTPS | Vite-Entwicklungsserver (Benutzeroberflaeche) |

Der Datenfluss gliedert sich in drei Stufen:

1. **Lokale Inferenz:** `host_hailo_runner.py` liest den MJPEG-Stream (Port 8082) und fuehrt YOLOv8-Objekterkennung auf dem PCIe-angebundenen Hailo-8L aus (Inferenzzeit ca. 34 ms, 5 Hz). Die Detektionen werden als JSON-Pakete ueber UDP-Port 5005 an den Container gesendet.

2. **ROS2-Integration:** `hailo_udp_receiver_node` empfaengt die UDP-Pakete und publiziert sie auf `/vision/detections`. `gemini_semantic_node` bewertet die Szene semantisch ueber die Gemini-Cloud-API (Modell `gemini-2.0-flash-lite`, Rate-Limit 8 s, max. 256 Tokens) und publiziert auf `/vision/semantics`.

3. **Sprachausgabe (optional):** `tts_speak_node` spricht die semantische Analyse ueber gTTS (Cloud, Deutsch) und mpg123 auf dem MAX98357A-Lautsprecher aus (Rate-Limit 10 s). Der Dashboard-AI-Schalter steuert sowohl das Broadcast-Gate in der Bridge als auch das Topic `/vision/enable` fuer die TTS-Ausgabe.

Ein Fallback-Modus (`--fallback`) sendet Dummy-Detektionen ohne Hailo-Hardware fuer Entwicklung und Tests. Ohne Hailo-8L oder bei deaktivierter Vision (`use_vision:=False`) laufen Kamera und Dashboard-Stream weiterhin. Die Topics `/vision/detections` und `/vision/semantics` werden dann nicht publiziert. Navigation und Lokalisierung sind davon unabhaengig.

Die Umgebungsvariable `GEMINI_API_KEY` muss gesetzt sein und wird ueber `docker-compose.yml` an den Container durchgereicht. Der Host-Runner wird separat gestartet und unterstuetzt die Argumente `--model` (Pfad zum HEF-Modell), `--threshold` (Confidence-Schwellwert, Standard 0,35) und `--fallback`.

Detaillierte Pipeline-Dokumentation: [vision_pipeline.md](vision_pipeline.md)

Die Aktivierung der vollstaendigen Vision-Pipeline erfordert folgende Launch-Argumente:

```
ros2 launch my_bot full_stack.launch.py \
    use_camera:=True use_vision:=True use_audio:=True use_tts:=True
```

### 8.2 Audio-Feedback und TTS-Sprachausgabe

Der Knoten `audio_feedback_node` abonniert `/audio/play` und startet einen nicht blockierenden Unterprozess, der WAV-Dateien ueber `aplay` auf dem I2S-Verstaerker (MAX98357A) wiedergibt. Die Prozessentkopplung verhindert Latenzen in der ROS2-Echtzeitschleife.

Trigger-Quellen umfassen den Cliff-Safety-Knoten (`cliff_alarm`) und die Dashboard-Bridge (`nav_start`, `nav_reached`). Der Alarm `cliff_alarm` besitzt hoechste Prioritaet und terminiert laufende Sounds sofort. Die Lautstaerke wird ueber `/audio/volume` (0–100 %) gesteuert und per `amixer sset SoftMaster` angewendet. Beim Start erzeugt der Knoten 1 s Stille fuer die ALSA-Control-Erstellung (softvol-Initialisierung).

### 8.3 ReSpeaker DoA/VAD

Der Knoten `respeaker_doa_node` pollt Direction-of-Arrival und Voice Activity Detection vom ReSpeaker Mic Array v2.0 (XMOS XVF-3000) ueber USB Vendor Control Transfers (pyusb) mit 10 Hz. Er publiziert den Azimut (0–359 Grad) auf `/sound_direction` und den Spracherkennungsstatus auf `/is_voice`. Der Knoten erfordert eine udev-Regel (eingerichtet ueber `host_setup.sh`) und das Python-Paket `pyusb` im Docker-Image. Die Daten werden in der Detailseite der Benutzeroberflaeche im AudioPanel visualisiert.

---

## 9. Sicherheitsarchitektur

### 9.1 Gestaffelte Sicherheitsebenen

Der AMR implementiert sechs gestaffelte Sicherheitsebenen. Die Ebenen 1–4 liegen auf Ebene A (MCU), Ebene 5 auf Ebene B (ROS2) und Ebene 6 auf Ebene B (Benutzeroberflaeche). Die Redundanz stellt sicher, dass bei Ausfall von Ebene B die MCU-eigenen Mechanismen den Roboter schuetzen.

| Ebene | Mechanismus | Ausloeser | Latenz | Abhaengigkeit |
|---|---|---|---|---|
| 1 | MCU Failsafe-Timer | Kein `/cmd_vel` > 500 ms | < 520 ms | Keine (lokal auf Fahrkern) |
| 2 | Batterie-Unterspannung | < 9,5 V (Hysterese +0,3 V) | Sofort | Sensor- und Sicherheitsbasis, INA260 |
| 3 | CAN-Notstopp | Cliff (0x120) oder Battery-Shutdown (0x141) | < 20 ms | CAN-Bus, kein Pi 5 noetig |
| 4 | Inter-Core-Watchdog | 50 Zyklen (~1 s) ohne Core-0-Heartbeat | ~1 s | Lokal auf Fahrkern |
| 5 | Cliff-Safety-Knoten (ROS2) | `/cliff` ODER `/range/front` < 80 mm | ~50 ms | Pi 5, Docker, micro-ROS |
| 6 | Dashboard Deadman-Timer | Kein Heartbeat > 300 ms | 300 ms | Netzwerk, Browser |

Zusaetzliche MCU-Schutzmechanismen ergaenzen die gestaffelten Ebenen:

- **Hard-Stop:** Bei Zielgeschwindigkeit nahe Null (|tv| < 0,01) umgeht das System die PID-Rampe und erzeugt sofortigen Stillstand (< 20 ms).
- **PID-Stillstandserkennung:** Bei Sollwert nahe Null wird der PID-Regler umgangen und die PWM direkt auf 0 gesetzt.
- **Beschleunigungsrampe:** Die maximale Beschleunigung ist auf 5,0 rad/s^2 begrenzt, um unkontrollierte Beschleunigungsvorgaenge zu verhindern.

Die Ebenen sind redundant ausgelegt: Faellt Ebene B (Pi 5, Docker, ROS2) vollstaendig aus, schuetzen die Ebenen 1 bis 4 auf MCU-Ebene den Roboter autonom.

### 9.2 Cliff-Safety-Multiplexer

Der Knoten `cliff_safety_node` fungiert als Befehlsmultiplexer zwischen Navigation, Dashboard-Steuerung und Fahrkern. Im Normalbetrieb leitet er Twist-Nachrichten von `/nav_cmd_vel` und `/dashboard_cmd_vel` an `/cmd_vel` weiter. Bei Cliff-Erkennung (`/cliff` = true) oder Unterschreitung der Ultraschall-Distanz von 80 mm blockiert der Multiplexer alle Fahrbefehle und erzeugt einen harten Stopp (v = 0 m/s, w = 0 rad/s) mit 20 Hz. Die Freigabe erfolgt erst bei einer Distanz ueber 120 mm (Hysterese). Ein einmaliger Audio-Alarm (`cliff_alarm`) wird bei Blockierung ausgeloest.

Der CAN-Bus liefert parallel ein redundantes Cliff-Signal direkt vom Sensor-Knoten an den Fahrkern. Der Sensor-Knoten sendet den Cliff-Status auf CAN-ID 0x120 (20 Hz, 1 Byte: 0x00=OK, 0x01=Cliff) und das Batterie-Shutdown-Signal auf CAN-ID 0x141 (Event, 1 Byte). Der Fahrkern empfaengt diese Frames nicht blockierend in seinem Core-1-Task und setzt die Motoren bei positivem Signal direkt auf Null. Die Reaktionszeit des CAN-Pfads betraegt weniger als 20 ms (ein `controlTask`-Zyklus bei 50 Hz). Dieser Pfad funktioniert ohne laufenden Pi 5, Docker-Container oder micro-ROS-Agent.

Die Konsequenz aus beiden Pfaden (ROS2 und CAN) ist eine lueckenlose Sicherheitslogik, die gegenueber Navigation und manueller Bedienung strikt uebergeordnet bleibt.

### 9.3 Deadman-Timer und Dashboard-Sicherheit

Die Benutzeroberflaeche implementiert mehrere Sicherheitsmechanismen:

- **Deadman-Timer:** Die `dashboard_bridge` erwartet alle 300 ms ein Heartbeat-Signal vom Client. Bei Ausbleiben stoppt sie automatisch den Roboter.
- **Single-Controller:** Nur ein WebSocket-Client darf gleichzeitig Fahrbefehle senden.
- **Geschwindigkeitsbegrenzung:** 0,4 m/s linear, 1,0 rad/s angular — doppelt geprueft auf Client- und Server-Seite.
- **E-Stop:** Sendet fuenfmal Zero-Velocity bei Betaetigung.
- **Client-Disconnect:** Sofortiger Stopp bei Verbindungsverlust des steuernden Clients.
- **Joystick-Release:** Sofort-Stopp bei Loslassen, Deadman-Backup nach 300 ms.

---

## 10. Glossar

### 10.1 Robotik und Navigation

- **AMR (Autonomer mobiler Roboter):** Ein fahrerloses System, das sich ohne physische Leitlinien wie Schienen in seiner Umgebung orientiert und bewegt.
- **SLAM (Simultaneous Localization and Mapping):** Ein Verfahren, bei dem ein Roboter gleichzeitig eine Karte seiner unbekannten Umgebung erstellt und seine eigene Position darin fortlaufend berechnet.
- **Odometrie:** Die Schaetzung von Position und Orientierung anhand der Messdaten des eigenen Antriebssystems (hier: Radumdrehungen).
- **Kinematik / Inverskinematik:** Die Kinematik beschreibt die Geometrie der Bewegung. Die Inverskinematik berechnet aus einer gewuenschten Fahrgeschwindigkeit und Drehrichtung des Gesamtroboters die dafuer notwendigen Einzeldrehzahlen des linken und rechten Rades.
- **TF (Transformation Framework):** Ein Koordinatensystem-Verwaltungswerkzeug. Es verfolgt die raeumlichen Beziehungen zwischen verschiedenen Roboterteilen (z. B. Abstand zwischen Rad und Laserscanner) ueber die Zeit.
- **AMCL (Adaptive Monte Carlo Localization):** Ein probabilistischer Algorithmus, der Partikelfilterung nutzt, um die Roboterposition auf einer bereits vorhandenen Karte abzugleichen.
- **Costmap:** Eine zweidimensionale Kostenkarte zur Hindernisvermeidung. Der *VoxelLayer* repraesentiert 3D-Hindernisse raeumlich, der *InflationLayer* legt einen virtuellen Sicherheitsabstand um diese Hindernisse.

### 10.2 Regelungstechnik

- **PID-Regler (Proportional-Integral-Derivative):** Ein Regelkreis, der die Abweichung zwischen Soll- und Ist-Wert korrigiert. Er reagiert auf den aktuellen Fehler (proportional), die Summe der vergangenen Fehler (integral) und die Fehleraenderung (derivativ).
- **Anti-Windup:** Ein Schutzmechanismus im PID-Regler. Er verhindert, dass der Integralanteil bei einer physischen Blockade (z. B. Fahren gegen ein Hindernis) unendlich anwaechst und spaeter zu Fehlverhalten fuehrt.
- **Komplementaerfilter:** Ein Algorithmus zur Sensordatenfusion. Er gleicht die Schwaechen verschiedener Sensoren aus, indem er beispielsweise das Gyroskop fuer schnelle Rotationsaenderungen und Odometriedaten fuer langfristige Stabilitaet gewichtet.
- **PWM (Pulsweitenmodulation):** Ein Verfahren zur Steuerung der Motorleistung. Die Versorgungsspannung wird in sehr schnellem Wechsel (20 kHz) ein- und ausgeschaltet.
- **Deadzone (Anlaufschwelle):** Der Mindestwert der PWM, der noetig ist, damit das elektromagnetische Feld die innere mechanische Reibung des Motors ueberwindet.

### 10.3 Hardware und Sensorik

- **LiDAR (Light Detection and Ranging):** Ein optischer Sensor, der Laserstrahlen aussendet und die Reflexionszeit misst, um Entfernungen zu umliegenden Objekten zu bestimmen.
- **IMU (Inertial Measurement Unit):** Ein Sensorbauteil, das lineare Beschleunigungen und Drehraten des Roboters im Raum misst.
- **Hall-Encoder:** Ein Sensor am Motor, der magnetische Umdrehungsimpulse in digitale Signale (Ticks) wandelt. Der *Quadraturmodus* verarbeitet zwei phasenverschobene Signale und ermoeglicht so die gleichzeitige Erkennung von Geschwindigkeit und Drehrichtung.
- **I2C / CAN-Bus:** Bussysteme zur Datenuebertragung. I2C verbindet Bauteile auf kurzen Distanzen direkt auf der Platine. CAN uebertraegt Daten robust in elektrisch stoeranfaelligen Umgebungen. *Contention* bezeichnet Konflikte, wenn mehrere Bauteile gleichzeitig senden wollen.
- **Global-Shutter:** Ein Kameratyp, der alle Pixel des Bildsensors exakt zum gleichen Zeitpunkt belichtet. Dies verhindert Bildverzerrungen bei schnellen Kamerabewegungen.

### 10.4 Software und Kommunikation

- **ROS 2 / micro-ROS:** Ein quelloffenes Software-Framework fuer die Roboterentwicklung. *micro-ROS* ist eine ressourcenschonende Variante, die speziell fuer Mikrocontroller (wie den ESP32-S3) konzipiert ist.
- **XRCE-DDS:** Der Datenuebertragungsstandard fuer ressourcenbeschraenkte Geraete. Er fungiert als *Middleware*, also als Vermittlerschicht zwischen verschiedenen Programmknoten.
- **MTU (Maximum Transmission Unit):** Die maximale Paketgroesse in Bytes, die ueber eine Schnittstelle am Stueck uebertragen werden kann.
- **QoS (Quality of Service):** Qualitaetsrichtlinien fuer Netzwerke. *Best-Effort* sendet Daten ohne Empfangsbestaetigung. *Reliable* stellt sicher, dass jedes Paket ankommt, und wiederholt fehlerhafte Sendungen.
- **FreeRTOS:** Ein Echtzeitbetriebssystem fuer Mikrocontroller. Es garantiert die strikte Einhaltung von Zeitvorgaben bei der Abarbeitung von Aufgaben (Tasks).
- **Inter-Core-Watchdog:** Ein Ueberwachungsmechanismus zwischen zwei Prozessorkernen. Meldet sich ein Kern nicht innerhalb einer definierten Zeitspanne (Heartbeat), versetzt der Watchdog das System automatisch in einen sicheren Zustand (Failsafe).
