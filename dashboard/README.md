# AMR Dashboard

Benutzeroberflaeche (Bedien- und Leitstandsebene) fuer den Autonomen Mobilen Roboter. Sci-Fi-HUD-Design mit Echtzeit-Telemetrie ueber WebSocket.

## Tech-Stack

| Bereich | Technologie |
|---|---|
| Framework | React 19 + TypeScript 5.9 |
| Build | Vite 7 |
| Styling | Tailwind CSS 4 (HUD-Theme, JetBrains Mono) |
| State | Zustand 5 (flacher Store, 60+ Properties) |
| Joystick | nipplejs |

## Voraussetzungen

- Node.js 20+
- mkcert-Zertifikate im Projektverzeichnis (`amr.local+5.pem`, `amr.local+5-key.pem`) fuer HTTPS
- Laufendes ROS2-Backend mit `use_dashboard:=True` (startet `dashboard_bridge.py`)

## Entwicklung

```bash
npm install
npm run dev -- --host 0.0.0.0    # https://amr.local:5173
npm run build                     # Produktion (tsc + vite build)
npm run lint                      # ESLint
```

Das Dashboard benoetigt parallel den ROS2-Stack:

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_rviz:=False
```

## Seiten

### Steuerung (Standardansicht)

```
[Sidebar 320px]  [Kamera]      [SLAM-Karte]  [LiDAR]
  Status           MJPEG +       Klick-Nav     360-Grad
  System           AI-Overlay    + Pfad-Trail  Polar-Scan
  Kommandofeld   [Joystick]    [Servo + Hardware-Steuerung]
```

- **Kamera:** MJPEG-Livestream (Port 8082) mit Hailo-8L-Bounding-Boxen und AI-Toggle
- **SLAM-Karte:** Canvas-basiert, Roboter-Position, Fahrpfad-Trail, Navigationsziel per Klick
- **LiDAR:** Farbkodierte Entfernungswerte im Polardiagramm
- **Joystick:** 0,4 m/s linear, 1,0 rad/s angular, Deadman-Timer (300 ms)
- **Kommandofeld:** Freitext-REPL ("fahre 1 m vorwaerts", "drehe 90 grad links", "nav 1.0 0.5")

### Details

- **Aktive Geraete:** Status und Hz-Raten (ESP32 Drive/Sensor, RPLidar, Kamera, Hailo, INA260)
- **Sensordetails:** Ultraschall-Distanz, Cliff-Erkennung, IMU-Rate
- **Audio:** ReSpeaker-Richtungskompass, Lautstaerke, Sound-Buttons
- **Roboter-Info:** Netzwerk-IP, Seitenansicht-SVG, Spezifikationen

## Kommunikation

| Kanal | Port | Protokoll | Richtung |
|---|---|---|---|
| Telemetrie/Steuerung | 9090 | WebSocket (wss) | bidirektional |
| Kamerastream | 8082 | HTTPS MJPEG | Server → Client |

### WebSocket-Nachrichten (Server → Client)

| `op` | Rate | Inhalt |
|---|---|---|
| `telemetry` | 10 Hz | Odometrie, IMU, Batterie, Servo, Hardware |
| `scan` | 2 Hz | LiDAR-Ranges |
| `system` | 1 Hz | CPU, RAM, Disk, Geraete-Status |
| `map` | 0,5 Hz | SLAM-Karte (PNG base64) + Roboter-Pose |
| `vision_detections` | 5 Hz | Hailo-Objekterkennung |
| `nav_status` | 1 Hz | Navigationsstatus |
| `sensor_status` | 2 Hz | Ultraschall, Cliff, IMU |

### WebSocket-Nachrichten (Client → Server)

| `op` | Throttle | Inhalt |
|---|---|---|
| `cmd_vel` | 10 Hz | Geschwindigkeitskommando (linear_x, angular_z) |
| `heartbeat` | 5 Hz | Deadman-Switch |
| `servo_cmd` | 10 Hz | Pan/Tilt-Winkel |
| `hardware_cmd` | 10 Hz | Motor-Limit, Servo-Speed, LED-PWM |
| `nav_goal` | — | Kartenkoordinaten (x, y, yaw) |
| `command` | — | Freitext-Kommando |

Vollstaendige Typdefinitionen: `src/types/ros.ts`

## Verzeichnisstruktur

```
src/
├── components/       # 15 React-Komponenten (eine Datei pro Komponente)
├── hooks/            # useWebSocket, useJoystick, useImageFit
├── store/            # telemetryStore (Zustand, flacher State)
├── types/            # ros.ts (WebSocket-Protokoll-Interfaces)
├── App.tsx           # Root (Tab-Navigation: Steuerung/Details)
└── index.css         # Tailwind + HUD-Theme (--color-hud-*)
```

## Sicherheitsmechanismen

- **Deadman-Timer:** 300 ms ohne Heartbeat → automatischer Stopp
- **Notaus-Button:** Sendet 5× Zero-Velocity (Redundanz bei Paketverlust)
- **Geschwindigkeitsbegrenzung:** 0,4 m/s / 1,0 rad/s (Benutzeroberflaeche + Backend)
- **Cliff-Safety:** Backend-seitiger Multiplexer blockiert Fahrbefehle bei Kantenerkennung
