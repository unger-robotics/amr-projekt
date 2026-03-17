# AMR — Autonomer Mobiler Roboter fuer Intralogistik

Projektarbeit: Roboter mit Differentialantrieb fuer den Transport von Kleinladungstraegern (KLT) in der Intralogistik.

![AMR Draufsicht](hardware/media/amr-draufsicht_web.png)

## Systemarchitektur

```
                        ┌─────────────────────────────────────────────────┐
                        │          Raspberry Pi 5 (Docker)                │
                        │   ROS2 Humble · Nav2 · SLAM Toolbox · RViz2     │
                        │   micro-ROS Agents · Dashboard Bridge           │
                        │   Vision · Audio · CAN Bridge (optional)        │
                        └────────┬──────────────────┬─────────────────────┘
                     UART 921600 │                  │ UART 921600
                   /dev/amr_drive│                  │/dev/amr_sensor
                        ┌────────┴────────┐  ┌─────┴──────────────┐
                        │  Drive-Node     │  │  Sensor-Node       │
                        │  ESP32-S3       │  │  ESP32-S3          │
                        │                 │  │                    │
                        │  Motorregelung  │  │  IMU (MPU6050)     │
                        │  PID 50 Hz      │  │  Batterie (INA260) │
                        │  Odometrie      │  │  Ultraschall       │
                        │  LED-Steuerung  │  │  Cliff-Sensoren    │
                        │                 │  │  Servo (PCA9685)   │
                        └────────┬────────┘  └─────┬──────────────┘
                                 │  CAN-Bus 1 Mbit/s (optional)  │
                                 └───────────────────────────────┘
```

**Drei Ebenen:**
- **A — Fahrkern:** Zwei ESP32-S3 MCUs fuer Antrieb und Sensorik (micro-ROS, Dual-Core)
- **B — Bedien- und Leitstandsebene:** Pi 5 mit Nav2, SLAM, Dashboard (React/Vite)
- **C — Intelligente Interaktion:** Hailo-8L Objekterkennung, Gemini Semantik, Sprachausgabe

## Schnellstart

### Voraussetzungen

- Raspberry Pi 5 (Debian Trixie) mit Docker und docker-compose
- PlatformIO CLI (MCU-Firmware)
- Node.js 20+ (Dashboard)
- mkcert (HTTPS-Zertifikate fuer Dashboard)

### 1. MCU-Firmware flashen

```bash
# Drive-Node
cd amr/mcu_firmware/drive_node
pio run -e drive_node -t upload -t monitor

# Sensor-Node
cd amr/mcu_firmware/sensor_node
pio run -e sensor_node -t upload -t monitor
```

> **Wichtig:** Immer `-e <environment>` angeben! Ohne `-e` werden alle Environments geflasht.
> Erster Build: ~15 Min (micro-ROS aus Source). Folgebuilds gecached.

### 2. ROS2-Container starten

```bash
cd amr/docker/
sudo bash host_setup.sh          # Einmalig: udev, Gruppen, Kamera
docker compose build              # Image bauen (~15-20 Min)
./run.sh colcon build --packages-select my_bot --symlink-install
./run.sh ros2 launch my_bot full_stack.launch.py
```

### 3. Dashboard starten (optional)

Erfordert zwei parallele Prozesse:

```bash
# Terminal 1: ROS2 mit Dashboard-Bridge
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_rviz:=False

# Terminal 2: Vite Dev-Server
cd dashboard/
npm install && npm run dev -- --host 0.0.0.0   # https://amr.local:5173
```

### 4. System verifizieren

```bash
cd amr/docker/
./verify.sh
```

## Launch-Argumente

```bash
./run.sh ros2 launch my_bot full_stack.launch.py [use_<name>:=True/False]
```

| Argument           | Default | Beschreibung                          |
|--------------------|---------|---------------------------------------|
| `use_slam`         | True    | SLAM Toolbox (Kartierung)             |
| `use_nav`          | True    | Nav2 (Navigation)                     |
| `use_rviz`         | True    | RViz2 (Visualisierung)                |
| `use_sensors`      | True    | Sensor-Node micro-ROS Agent           |
| `use_cliff_safety` | True    | Cliff- + Ultraschall-Sicherheitslogik |
| `use_camera`       | False   | v4l2 Kamera-Knoten                    |
| `use_dashboard`    | False   | WebSocket/MJPEG Bridge                |
| `use_vision`       | False   | Hailo UDP Receiver + Gemini           |
| `use_audio`        | False   | Audio-Feedback (WAV via aplay)        |
| `use_can`          | False   | CAN-Bus Bridge (Dual-Path)            |
| `use_tts`          | False   | TTS-Sprachausgabe (gTTS)              |
| `use_respeaker`    | False   | ReSpeaker DoA-Mikrofon                |

## Hardware

| Komponente       | Typ                          | Funktion                            |
|------------------|------------------------------|-------------------------------------|
| Rechner          | Raspberry Pi 5               | ROS2, SLAM, Navigation, Docker      |
| MCU (2x)         | XIAO ESP32-S3                | Antrieb + Sensorik (micro-ROS)      |
| Motoren          | JGA25-370 (1:34)             | Differentialantrieb, 11 CPR Encoder |
| Motortreiber     | Cytron MDD3A                 | Dual-H-Bruecke, PWM 20 kHz          |
| LiDAR            | RPLiDAR A1                   | 360° Laserscanner (SLAM)            |
| IMU              | MPU6050                      | 6-Achsen, 50 Hz                     |
| Batterie         | Samsung INR18650-35E 3S      | 12V Li-Ion, INA260 Monitoring       |
| KI-Beschleuniger | Hailo-8L                     | YOLOv8 Objekterkennung              |
| Kamera           | IMX296 Global Shutter        | Vision-Pipeline                     |
| Servos           | MG996R via PCA9685           | Greifer-Steuerung                   |
| Audio            | MAX98357A I2S + Lautsprecher | Sprachausgabe                       |
| Mikrofon         | ReSpeaker Mic Array v2.0     | Richtungserkennung                  |

Raddurchmesser: 65,67 mm · Spurbreite: 178,0 mm · PID: Kp=0,4 Ki=0,1 Kd=0,0

## Projektstruktur

```
amr-projekt/
├── amr/                            Technischer Kern
│   ├── mcu_firmware/
│   │   ├── drive_node/             PlatformIO: Antrieb, PID, Odometrie, LED
│   │   └── sensor_node/            PlatformIO: IMU, Batterie, Cliff, Servo
│   ├── pi5/ros2_ws/src/my_bot/     ROS2-Paket (Launch, Config, Knoten)
│   ├── docker/                     Dockerfile, run.sh, verify.sh
│   └── scripts/                    Validierung, Runtime-Knoten, Utilities
├── dashboard/                      React/Vite/TypeScript Benutzeroberflaeche
├── docs/                           Architektur-, System- und Validierungsdoku
├── hardware/                       Spezifikationen, Schaltplaene, Datenblaetter
├── projektarbeit/                  Projektarbeit (Markdown + LaTeX)
├── planung/                        Roadmap, Testanleitungen, Messprotokolle
└── scripts/                        Wartung (update_dependencies.sh, rover_wartung.sh)
```

Detaillierte Entwicklerdokumentation in `CLAUDE.md` (Root), `amr/CLAUDE.md`, `amr/mcu_firmware/CLAUDE.md` und `dashboard/CLAUDE.md`.

## Linting und Code-Qualitaet

```bash
# Python
ruff check amr/                    # Lint (Zeilenlaenge 100, Python 3.10)
ruff format --check amr/           # Format
mypy --config-file mypy.ini        # Type-Check

# C++
clang-format --dry-run --Werror amr/mcu_firmware/drive_node/src/*.cpp \
  amr/mcu_firmware/drive_node/include/*.hpp \
  amr/mcu_firmware/sensor_node/src/*.cpp \
  amr/mcu_firmware/sensor_node/include/*.hpp

# Dashboard
cd dashboard && npm run lint

# Alles
pre-commit run --all-files
```

Einmalig: `pip3 install pre-commit && pre-commit install`

## Dokumentation

| Dokument                         | Inhalt                                   |
|----------------------------------|------------------------------------------|
| `docs/architecture.md`           | Systemarchitektur, Komponentenuebersicht |
| `docs/ros2_system.md`            | Topics, TF-Baum, QoS-Konfiguration       |
| `docs/firmware.md`               | MCU-Firmware, Dual-Core, micro-ROS       |
| `docs/robot_parameters.md`       | Kinematik, PID, PWM, Timing              |
| `docs/dashboard.md`              | WebSocket-Protokoll, MJPEG-Server        |
| `docs/vision_pipeline.md`        | Hailo/Gemini Pipeline                    |
| `docs/serial_port_management.md` | udev-Regeln, Seriennummern               |
| `docs/build_and_deploy.md`       | Build- und Deployment-Prozesse           |
| `docs/validation.md`             | Validierungskonzept (V-Modell)           |
| `planung/benutzerhandbuch.md`    | Einrichtung und Betrieb                  |

## Lizenz

MIT — siehe [LICENSE](amr/LICENSE)

Copyright (c) 2026 unger-robotics
