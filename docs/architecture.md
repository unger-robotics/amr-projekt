# Architektur

## Zielbild

Der AMR besteht aus einem Raspberry Pi 5 als zentralem ROS2-Rechner und zwei ESP32-S3-Knoten fuer echtzeitnahe I/O- und Regelaufgaben.

## Drei-Ebenen-Modell

| Ebene | Bezeichnung | Komponenten | Aufgabe |
|-------|-------------|-------------|---------|
| A | Fahrkern sowie Sensor- und Sicherheitsbasis | Drive-Knoten, Sensor-Knoten (ESP32-S3) | Echtzeit-Regelung, Sensorerfassung, Sicherheits-Basisfunktionen |
| B | Bedien- und Leitstandsebene | Pi 5 (ROS2, Nav2, SLAM), Benutzeroberflaeche (React) | Koordination, Kartierung, Navigation, Fernsteuerung |
| C | Intelligente Interaktion | Hailo-8L, Gemini Cloud, gTTS, ReSpeaker | Objekterkennung, Sprachausgabe, semantische Beschreibung |

Ebene A arbeitet autonom — der CAN-Notstopp funktioniert ohne Pi 5. Ebene B setzt auf micro-ROS-Kommunikation mit A auf. Ebene C ist vollstaendig optional und ueber Launch-Argumente zuschaltbar.

## Hauptkomponenten

- Pi 5: ROS2, SLAM, Navigation, Dashboard-Bridge, optionale Vision, Audio-Feedback und TTS-Sprachausgabe (MAX98357A I2S)
- Drive-Knoten: Motoransteuerung, Encoder, PID, Odometrie, LED
- Sensor-Knoten: Ultraschall, Cliff, IMU, Batterie, Servo (PCA9685 PWM)
- LiDAR, Kamera, optionale Hailo-/Gemini-Pipeline

## Vollstaendiges Systemdiagramm

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
│  [Browser: Benutzeroberflaeche React/Vite]  HTTPS:5173                                    │
│    Zustand Store ◄──► useWebSocket ◄──WSS:9090──► dashboard_bridge              │
│    Joystick → cmd_vel 10 Hz, Heartbeat 5 Hz                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Ebene A — Fahrkern                                                             │
│                                                                                 │
│  [Drive-Knoten ESP32-S3]              [Sensor-Knoten ESP32-S3]                      │
│    Core 0: micro-ROS Executor         Core 0: micro-ROS Executor                │
│      Sub: /cmd_vel, /hardware           Sub: /servo_cmd, /hardware              │
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

## Kommunikationspfade (Dual-Path)

Die MCU-Knoten kommunizieren ueber zwei parallele Kanaele mit dem Pi 5:

- **micro-ROS/UART** (primaer): ROS2-Topics via Serial Transport, Subscriber/Publisher fuer Steuerung und Telemetrie
- **CAN-Bus** (sekundaer): 1 Mbit/s, MCP2515/SocketCAN auf Pi 5, TWAI auf ESP32-S3, Fire-and-forget Diagnostik

CAN-Sends laufen in den Core-1-Tasks (`controlTask`/`sensorTask`), damit sie unabhaengig vom micro-ROS Agent funktionieren. Hardware-Dokumentation: `hardware/can-bus/CAN-Bus.md`.

## Sicherheitsarchitektur

Der AMR implementiert sechs gestaffelte Sicherheitsebenen. Die ersten vier liegen auf Ebene A (MCU), die fuenfte auf Ebene B (ROS2), die sechste auf Ebene B (Benutzeroberflaeche):

| Ebene | Mechanismus | Ausloeser | Latenz | Abhaengigkeit |
|-------|-------------|-----------|--------|---------------|
| 1 | MCU Failsafe-Timer | Kein `/cmd_vel` > 500 ms | < 520 ms | Keine (lokal auf Fahrkern) |
| 2 | Batterie-Unterspannung | < 9.5 V (Hysterese +0.3 V) | Sofort | Sensor- und Sicherheitsbasis, INA260 |
| 3 | CAN-Notstopp | Cliff (0x120) oder Battery-Shutdown (0x141) | < 20 ms | CAN-Bus, kein Pi 5 noetig |
| 4 | Inter-Core-Watchdog | 50 Zyklen (~1 s) ohne Core-1-Heartbeat | ~1 s | Lokal auf Fahrkern |
| 5 | Cliff-Safety-Knoten (ROS2) | `/cliff` OR `/range/front` < 80 mm | ~50 ms | Pi 5, Docker, micro-ROS |
| 6 | Dashboard Deadman-Timer | Kein Heartbeat > 300 ms | 300 ms | Netzwerk, Browser |

Zusaetzliche MCU-Schutzmechanismen:
- **Hard-Stop**: Bei |tv| < 0.01 wird die PID-Rampe umgangen — sofortiger Stillstand (< 20 ms)
- **PID-Stillstandserkennung**: Sollwert nahe Null → PID umgehen, PWM = 0

Die Ebenen sind redundant: Faellt Ebene B aus, schuetzen Ebenen 1-4 auf MCU-Ebene.

## CAN-Notstopp-Redundanzpfad

Der Drive-Knoten empfaengt Cliff- (0x120) und Battery-Shutdown-Signale (0x141) vom Sensor-Knoten ueber CAN-Bus und stoppt die Motoren direkt — unabhaengig von Pi 5 und micro-ROS.

### Datenfluss

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

### Eigenschaften

- **Latenz**: < 20 ms (ein controlTask-Zyklus bei 50 Hz)
- **Unabhaengigkeit**: Funktioniert ohne laufenden Pi 5, Docker-Container oder micro-ROS Agent
- **Nicht-latched**: Cliff-Stop folgt dem aktuellen Sensor-Zustand und reset sich automatisch
- **Non-blocking**: `twai_receive()` mit `pdMS_TO_TICKS(0)` blockiert den PID-Loop nicht
- **Redundanz**: Ergaenzt den bestehenden ROS2-Pfad (`/cliff` → `cliff_safety_node` → `/cmd_vel`)

## Dual-Core-Pattern (ESP32-S3)

Beide MCU-Knoten nutzen FreeRTOS mit fester Core-Zuordnung:

**Drive-Knoten:**
- Core 0: micro-ROS Executor — Subscriber (`/cmd_vel`, `/hardware`, `/battery_shutdown`), Publisher (`/odom` 20 Hz), LED-Steuerung
- Core 1: `controlTask` 50 Hz — PID-Regelschleife, Encoder-Auswertung, CAN-Send und -Empfang

**Sensor-Knoten:**
- Core 0: micro-ROS Executor — Subscriber (`/servo_cmd`, `/hardware`), Publisher (`/range` 10 Hz, `/cliff` 20 Hz, `/imu` 50 Hz, `/battery` 2 Hz), Servo-I2C 5 Hz
- Core 1: `sensorTask` — Cliff 20 Hz, Ultraschall 10 Hz, IMU 50 Hz, Batterie 2 Hz, CAN-Sends

**Synchronisation:** `SharedData`-Struct mit Mutex zwischen den Cores. Sensor-Knoten zusaetzlich `i2c_mutex` (5 ms Timeout) fuer MPU6050 (0x68), INA260 (0x40) und PCA9685 (0x41).

**micro-ROS QoS:** Grosse Publisher (`/odom`, `/imu`, `/battery`) nutzen Reliable QoS, da Odom (~725 B) und IMU (~550 B) die XRCE-DDS MTU von 512 B ueberschreiten und Fragmentierung erfordern. Kleine Nachrichten (`/cliff`, `/range/front`) verwenden ebenfalls Reliable (`rclc_publisher_init_default`).

Details: `amr/mcu_firmware/CLAUDE.md`

## Vision-Pipeline

```
[Host: host_hailo_runner.py]          Hailo-8L, YOLOv8, 5 Hz, HTTPS MJPEG
         │ UDP:5005
         ▼
[Docker: hailo_udp_receiver_node]     100 Hz Poll, /vision/detections
         │
         ▼
[Docker: gemini_semantic_node]        Gemini 3.1 flash-lite, Rate-Limit 4 s
         │                            Max 256 Tokens, Deutsch
         ▼
/vision/semantics ──► [tts_speak_node]   gTTS Cloud, Rate-Limit 10 s
                       Gate: /vision/enable (Dashboard AI-Schalter)
                       mpg123 → MAX98357A I2S
```

Der Hailo-Runner laeuft auf dem Host (Python 3.13), da die Hailo-SDK nicht im Docker-Container verfuegbar ist. Die Verbindung erfolgt per UDP innerhalb von `localhost` (network_mode: host).

Der Dashboard-AI-Schalter steuert sowohl das Broadcast-Gate in der Bridge (keine Weiterleitung an Browser wenn aus) als auch `/vision/enable` fuer die TTS-Sprachausgabe.

## Audio-Pipeline

```
Trigger-Quellen:
  cliff_safety_node → "cliff_alarm"
  dashboard_bridge  → "nav_start", "nav_reached"
         │
         ▼ /audio/play (String)
[audio_feedback_node]
  SOUND_MAP → WAV-Dateien
  aplay -q -D default → /dev/snd (MAX98357A I2S)

Lautstaerke: /audio/volume (Int32 0-100) → amixer sset SoftMaster
```

- **softvol-Init**: 1 s Stille beim Start fuer ALSA-Control-Erstellung
- **Prioritaet**: `cliff_alarm` terminiert laufende Sounds sofort
- Volume-Steuerung ueber Dashboard (Rate-Limit 5 Hz)

### Sprachsteuerung (optional, `use_voice:=True`)

```
[respeaker_doa_node] → /is_voice (VAD-Gate)
       │
       ▼
[voice_command_node]
  arecord → WAV (16 kHz, mono) → Gemini Flash (STT + Intent)
  → /voice/command → dashboard_bridge → _handle_command → Aktorik
  → /voice/text → Dashboard (Transkriptions-Anzeige)
```

- Erfordert `use_respeaker:=True` und `GEMINI_API_KEY`
- Barge-In-Schutz: 2 s Aufnahme-Sperre nach eigener TTS-Ausgabe
- Rate-Limit: min. 2 s zwischen Gemini-Calls, 429-Backoff 300 s

## Dashboard-Anbindung

### Datenfluss

```
ROS2 Topics → dashboard_bridge.py → WSS:9090 → useWebSocket → Zustand Store → React-Komponenten
Browser-Events → useJoystick → Rate-Limiting → WSS:9090 → dashboard_bridge → ROS2 Publish
MJPEG: /image_raw → MJPEG-Server :8082 → <img> Tag
```

### Server→Client (abonnierte Topics)

| Nachricht | Rate | Inhalt |
|-----------|------|--------|
| telemetry | 10 Hz | Odometrie, Geschwindigkeit |
| scan | 2 Hz | LiDAR-Daten |
| system | 1 Hz | CPU, RAM, Temperatur |
| map | 0.5 Hz | SLAM-Kartendaten |
| nav_status | 1 Hz | Navigationszustand |
| vision_detections | 5 Hz | YOLO-Erkennungen |
| vision_semantics | 0.5 Hz | Gemini-Beschreibungen |
| sensor_status | 2 Hz | Cliff, Ultraschall, IMU |
| audio_status | 2 Hz | Wiedergabe-Status |

### Client→Server (gesendete Kommandos)

| Nachricht | Rate | Inhalt |
|-----------|------|--------|
| cmd_vel | 10 Hz | Joystick-Steuerung |
| heartbeat | 5 Hz | Deadman-Signal |
| servo_cmd | 10 Hz | Servo-Position |
| hardware_cmd | 10 Hz | x=Motor-Limit, y=Servo-Speed, z=LED-PWM |
| nav_goal | Einmalig | Navigationsziel |
| audio_volume | 5 Hz | Lautstaerke |
| vision_control | Einmalig | AI-Schalter |

### Sicherheit

- **Deadman-Timer**: 300 ms Server-seitig, 200 ms Client-Heartbeat
- **Single-Controller**: Nur ein Client darf `cmd_vel` senden
- **Geschwindigkeitsbegrenzung**: 0.4 m/s linear, 1.0 rad/s angular (Client + Server doppelt geprueft)
- **E-Stop**: 5x Zero-Velocity, `navigator.vibrate(200)`
- **Joystick-Release**: Sofort-Stopp + Deadman-Backup nach 300 ms
- **HTTPS/TLS**: mkcert-Zertifikate, Fallback auf HTTP/WS ohne Zertifikate

Details: `docs/dashboard.md`

## Docker-Container-Grenzen

```
┌── Docker-Container (ros:humble-ros-base, arm64) ─────────────────────┐
│                                                                       │
│  ROS2 Nodes: micro-ROS Agents, SLAM, Nav2, cliff_safety,             │
│              dashboard_bridge, audio_feedback, can_bridge,            │
│              hailo_udp_receiver, gemini_semantic, tts_speak,          │
│              odom_to_tf, aruco_docking                                │
│                                                                       │
│  Devices:  /dev/amr_drive, /dev/amr_sensor, /dev/ttyUSB0, /dev/snd   │
│  Volumes:  my_bot (rw), scripts (ro), dashboard (ro, TLS-Certs),     │
│            hardware (ro), asound.conf, X11, Named (build/install/log) │
│  Network:  host (kein Bridge-Netzwerk)                                │
│  Privileged: true                                                     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

┌── Host (Raspberry Pi 5, Debian Trixie) ────────────────────────────┐
│  host_hailo_runner.py (Python 3.13, Hailo-8L SDK)                     │
│  Dashboard Dev-Server (npm run dev, :5173)                            │
│  mkcert-Zertifikate                                                   │
└───────────────────────────────────────────────────────────────────────┘
```

Der Container laeuft mit `network_mode: host` und `privileged: true`, um Zugriff auf serielle Geraete, Audio-Hardware und SocketCAN zu ermoeglichen. Host-only-Prozesse (Hailo-Runner, Dashboard-Dev-Server) kommunizieren ueber localhost-Ports.

## Datenfluss Ende-zu-Ende

Beispiel: Cliff-Erkennung bis Dashboard-Anzeige und Motorstopp:

```
1. Sensor-Knoten Core 1 (sensorTask, 20 Hz)
   IR-Sensor → cliff_detected = true
        │
        ├──► SharedData.cliff (Mutex) → Core 0 micro-ROS Pub /cliff
        │                                      │
        │                                      ▼
        │                               micro-ROS Agent (UART 921600)
        │                                      │
        │                                      ▼
        │                               cliff_safety_node
        │                                 /cmd_vel = Zero-Twist (20 Hz)
        │                                 /audio/play = "cliff_alarm"
        │                                      │
        │                                      ├──► dashboard_bridge → WSS → Browser
        │                                      │     sensor_status (event)
        │                                      │
        │                                      └──► audio_feedback_node
        │                                            aplay → MAX98357A
        │
        └──► CAN 0x120 (1 Byte: 0x01) ──► Drive-Knoten Core 1
                                            can_cliff_stop = true
                                            tv=0, tw=0 (< 20 ms)
```

Zwei parallele Pfade: ROS2 (ueber Pi 5, ~50 ms) und CAN (direkt MCU-zu-MCU, < 20 ms). Der CAN-Pfad ist die Rueckfallebene bei Ausfall von Pi 5 oder micro-ROS.

## Architekturregel

Zeitkritische Low-Level-Funktionen bleiben auf den MCU-Knoten. Koordination, Kartierung und Navigation bleiben auf dem Pi 5.

## TF-Baum

```
odom → base_link              (dynamisch, odom_to_tf, 20 Hz)
  ├── laser                   (statisch, x=0.10, z=0.235, yaw=pi)
  ├── camera_link             (statisch, x=0.10, z=0.08, use_camera)
  └── ultrasonic_link         (statisch, x=0.15, z=0.05, use_sensors)
```

Der LiDAR ist 180° gedreht montiert — die TF-Transformation (`yaw=pi`) kompensiert dies.

## Weitergehende Details

| Bereich | Dokument |
|---------|----------|
| Firmware (Drive-Knoten, Sensor-Knoten) | `amr/mcu_firmware/CLAUDE.md` |
| ROS2-System (Topics, Launch, Nodes) | `docs/ros2_system.md` |
| Dashboard (Komponenten, API) | `docs/dashboard.md` |
| Vision-Pipeline | `docs/vision_pipeline.md` |
| Hardware und Schaltplan | `hardware/docs/hardware-setup.md` |
| CAN-Bus Spezifikation | `hardware/can-bus/CAN-Bus.md` |
| Serielle Ports und udev | `docs/serial_port_management.md` |
| Roboter-Parameter | `docs/robot_parameters.md` |
| Build und Deployment | `docs/build_and_deploy.md` |
| Systemdokumentation | `docs/systemdokumentation.md` |
| Benutzerhandbuch | `docs/benutzerhandbuch.md` |
