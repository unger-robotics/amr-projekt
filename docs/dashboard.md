# Dashboard

## Zweck

Referenz fuer die AMR-Benutzeroberflaeche (Bedien- und Leitstandsebene, Ebene B). Beschreibt Tech-Stack, Architektur, Komponenten, State Management, Kommunikation und Entwicklungsprozess.

## Regel

Dashboard-spezifische Details (Komponenten, Hooks, Store, Theme) gehoeren in diese Datei. WebSocket-Protokoll und ROS2-Anbindung werden hier beschrieben, Topic-Definitionen stehen in `docs/ros2_system.md`.

---

## 1. Tech-Stack

| Bereich | Technologie | Version |
|---|---|---|
| Framework | React | 19.2.0 |
| Sprache | TypeScript | ~5.9.3 |
| Build-Tool | Vite | 7.3.1 |
| CSS-Framework | Tailwind CSS | 4.2.0 |
| State Management | Zustand | 5.0.11 |
| Joystick | nipplejs | 0.10.2 |
| Linting | ESLint (Flat Config) | 9.39.1 |
| Type-Check | TypeScript strict mode | — |

---

## 2. Verzeichnisstruktur

```
dashboard/
├── src/
│   ├── components/              # 16 React-Komponenten
│   │   ├── Dashboard.tsx        # Hauptseite Steuerung (4-Spalten-Grid)
│   │   ├── DetailPage.tsx       # Detailseite (4er-Grid)
│   │   ├── StatusPanel.tsx      # Verbindung, Odometrie, IMU, Latenz
│   │   ├── SystemMetrics.tsx    # CPU, RAM, Disk, Batterie, Netzwerk
│   │   ├── CameraView.tsx       # MJPEG-Stream + Vision-BBox-Overlay
│   │   ├── MapView.tsx          # SLAM-Karte (Canvas, Pfad-Trail, Ziel-Marker)
│   │   ├── LidarView.tsx        # Polar-LiDAR-Visualisierung (360 Grad)
│   │   ├── Joystick.tsx         # nipplejs-basiert (2D-Steuerung)
│   │   ├── ServoControl.tsx     # Pan/Tilt-Regler (PCA9685)
│   │   ├── HardwareControl.tsx  # Motor-Limit, Servo-Speed, LED-PWM
│   │   ├── CommandInput.tsx     # Freitext-Kommando + Verlauf (15 Eintraege)
│   │   ├── ActiveDevicesPanel.tsx  # 6 Geraete-Status mit Hz-Raten
│   │   ├── SensorDetailPanel.tsx   # IMU, Ultraschall, Cliff
│   │   ├── AudioPanel.tsx       # ReSpeaker DoA, Voice Activity, Sounds
│   │   ├── RobotInfoPanel.tsx   # Roboter-Metadaten
│   │   └── EmergencyStop.tsx    # E-Stop-Button (5x Zero-Velocity)
│   ├── hooks/
│   │   ├── useWebSocket.ts      # WebSocket-Verbindung (auto-reconnect)
│   │   ├── useJoystick.ts       # Joystick-Logik (rate-limited, Heartbeat)
│   │   └── useImageFit.ts       # Bildausstattungs-Berechnung
│   ├── store/
│   │   └── telemetryStore.ts    # Zustand Store (60+ Properties)
│   ├── types/
│   │   └── ros.ts               # Type-Definitionen fuer WebSocket-Messages
│   ├── App.tsx                  # Root (Tab-Navigation: Steuerung/Details)
│   ├── main.tsx                 # React-Einstiegspunkt
│   └── index.css                # Tailwind + HUD-Theme
├── vite.config.ts               # HTTPS via mkcert
├── eslint.config.js             # ESLint Flat Config
├── tsconfig.json                # TypeScript-Konfiguration
└── package.json                 # Abhaengigkeiten und Scripts
```

---

## 3. Seiten und Layout

### Steuerung (Standardansicht, `Dashboard.tsx`)

4er-Grid-Layout (Desktop, responsive auf Mobile):

```
[Sidebar 320px]  [Kamera]      [SLAM-Karte]  [LiDAR]
[alle 6 Zeilen]  [Joystick]    [Servo + Hardware-Steuerung]
```

- **Sidebar:** StatusPanel + SystemMetrics + CommandInput
- **Kamera:** MJPEG-Stream (`https://amr.local:8082/stream`) + Detection-BBox-Overlay (farbig nach Confidence)
- **SLAM-Karte:** Canvas-basiert, Roboter-Position (Dreieck + Glow), Pfad-Trail (max 500 Punkte, dedupliziert < 2 cm), Klick-Navigation (sendet `nav_goal`)
- **LiDAR:** Polar-Scan-Visualisierung (360 Grad)
- **Joystick:** nipplejs (statisch, 140px kompakt), Linear + Angular Velocity
- **Servo:** Pan/Tilt-Slider (Pan: 45–135 Grad, Tilt: 80–135 Grad), Center-Button, 10 Hz throttled
- **Hardware:** Motor-Limit (0–100%), Servo-Speed (1–10), LED-PWM (0–255)

### Details (Detailansicht, `DetailPage.tsx`)

2-Spalten-Grid (Desktop, 1 Spalte Mobile):

- **ActiveDevicesPanel:** 6 Geraete-Status (Drive, Sensor, LiDAR, Kamera, Hailo, INA260) mit Hz-Raten
- **SensorDetailPanel:** IMU-Hz, Ultraschall-Range, Cliff-Detection, Sensor-Node-Status
- **AudioPanel:** ReSpeaker DoA (Azimut), Voice Activity, Sound-Wiedergabe, Lautstaerke-Slider
- **RobotInfoPanel:** Position, Yaw, Servo-Position, Hardware-Grenzen

---

## 4. State Management (Zustand)

Zentraler Store in `src/store/telemetryStore.ts` mit 60+ Properties:

| Gruppe | Properties (Auswahl) | Quelle |
|---|---|---|
| Odometrie | x, y, yawDeg, velLinear, velAngular | `telemetry` (10 Hz) |
| IMU | headingDeg, gzDegS | `telemetry` (10 Hz) |
| LiDAR | scanRanges[], scanAngleMin/Max/Increment | `scan` (2 Hz) |
| System | cpuTempC, cpuLoad, ramUsedMb, diskUsagePct, hostIp | `system` (1 Hz) |
| SLAM-Karte | mapPngB64, mapWidth/Height, mapResolution, robotMapX/Y/Yaw | `map` (~0.5 Hz) |
| Vision | visionDetections[], inferenceMs, semanticAnalysis | `vision_detections` (5 Hz), `vision_semantics` (~0.5 Hz) |
| Batterie | batteryVoltage, batteryCurrent, batteryPower, batteryPercentage | `telemetry` (10 Hz) |
| Navigation | navStatus, navGoalX/Y/Yaw, navRemainingM | `nav_status` (1 Hz) |
| Sensoren | imuHz, ultrasonicHz, cliffHz, ultrasonicRange, cliffDetected | `sensor_status` (2 Hz) |
| Audio | soundDirection, isVoiceActive, audioVolume | `audio_status` (2 Hz) |
| Geraete | esp32Active, lidarActive, cameraActive, hailoDetected, ina260Active | `system` (1 Hz) |

**Pattern:** Inkrementelle Updates pro Message-Typ, Shallow Merging, Selectors pro Komponente.

---

## 5. Kommunikation

### WebSocket (Port 9090)

- **URL:** `wss://amr.local:9090` (HTTPS) oder `ws://localhost:9090` (HTTP-Fallback)
- **Auto-Reconnect:** Exponentiell (1s, 2s, 4s, 8s)
- **Latenz-Tracking:** `Date.now() - msg.ts * 1000`

#### Vom Server empfangene Nachrichten

| Operation | Rate | Beschreibung |
|---|---|---|
| `telemetry` | 10 Hz | Odometrie, IMU, Batterie, Servo, Hardware-Status |
| `scan` | 2 Hz | LiDAR-Ranges (komprimiert) |
| `system` | 1 Hz | CPU, RAM, Disk, Geraete-Status, Netzwerk |
| `map` | ~0.5 Hz | SLAM-Karte (PNG Base64), Roboter-Position |
| `vision_detections` | 5 Hz | Hailo-8 Erkennungen (BBox, Label, Confidence) |
| `vision_semantics` | ~0.5 Hz | Gemini-Szenenbeschreibung |
| `nav_status` | 1 Hz | Navigationsstatus + Ziel + Restdistanz |
| `sensor_status` | 2 Hz | Ultraschall, Cliff, IMU-Hz |
| `audio_status` | 2 Hz | ReSpeaker DoA, Voice Activity |
| `command_response` | — | Antwort auf Freitext-Kommando |

#### Vom Client gesendete Nachrichten

| Operation | Rate | Beschreibung |
|---|---|---|
| `cmd_vel` | 10 Hz | Fahrbefehl (linear_x, angular_z) |
| `heartbeat` | 5 Hz | Deadman-Switch |
| `servo_cmd` | 10 Hz | Pan, Tilt (throttled) |
| `hardware_cmd` | 10 Hz | Motor-Limit, Servo-Speed, LED-PWM (throttled) |
| `nav_goal` | — | Navigationsziel (x, y, yaw) |
| `nav_cancel` | — | Navigationsziel abbrechen |
| `audio_play` | — | Sound-Wiedergabe (sound_key) |
| `audio_volume` | 5 Hz | Lautstaerke (0–100%, throttled) |
| `vision_control` | — | Vision ein/aus |
| `command` | — | Freitext-Kommando |

### MJPEG-Stream (Port 8082)

- **URL:** `https://amr.local:8082/stream`
- Direkt in `<img src=...>` Tag eingebunden
- HTTPS via mkcert-Zertifikate (selbe wie WebSocket)

### Sicherheitsmechanismen

- **Geschwindigkeitsbegrenzung:** 0.4 m/s linear, 1.0 rad/s angular (hart im Bridge-Node)
- **Deadman-Timer:** 300 ms ohne Heartbeat → automatischer Stopp
- **Single-Controller:** Nur ein WebSocket-Client darf `cmd_vel` senden
- **Client-Disconnect:** Sofortiger Stopp bei Verbindungsverlust des Controllers
- **E-Stop:** Sendet 5x Zero-Velocity bei Betaetigung

---

## 6. Datenfluss

```
Server → Client:
  WebSocket.onmessage → JSON.parse → App.tsx onMessage → Zustand Store → React Re-render

Client → Server:
  UI Event → Hook (useJoystick/useWebSocket) → Rate-Limiting/Throttling → WebSocket.send
```

### Rate-Limiting

| Nachricht | Max-Rate | Intervall |
|---|---|---|
| `cmd_vel` | 10 Hz | 100 ms |
| `heartbeat` | 5 Hz | 200 ms |
| `servo_cmd` | 10 Hz | 100 ms |
| `hardware_cmd` | 10 Hz | 100 ms |
| `audio_volume` | 5 Hz | 200 ms |

### Joystick-Parameter (`useJoystick.ts`)

```
MAX_LINEAR  = 0.4 m/s   (aus nav2_params.yaml)
MAX_ANGULAR = 1.0 rad/s
SEND_INTERVAL_MS = 100   (10 Hz cmd_vel)
HEARTBEAT_INTERVAL_MS = 200  (5 Hz heartbeat)
```

---

## 7. HUD-Theme

SciFi-Look mit dunklem Hintergrund, definiert in `src/index.css`:

| Variable | Wert | Verwendung |
|---|---|---|
| `--color-hud-bg` | `#0a0e17` | Hintergrund |
| `--color-hud-panel` | `#0d1321` | Panel-Hintergrund |
| `--color-hud-border` | `rgba(0, 229, 255, 0.2)` | Rahmen (Cyan, durchsichtig) |
| `--color-hud-cyan` | `#00e5ff` | Hauptfarbe |
| `--color-hud-amber` | `#ffab00` | Warnung |
| `--color-hud-red` | `#ff1744` | Fehler |
| `--color-hud-green` | `#00e676` | OK |
| `--color-hud-text` | `#e0f7fa` | Text |
| `--font-mono` | JetBrains Mono | Schriftart |

Custom Utilities: `.hud-glow` (Box-Shadow Glow), `.hud-scanline` (CRT-Effekt).

---

## 8. cmd_vel-Routing und Cliff-Safety

```
Nav2 ──► /nav_cmd_vel ──┐
                        ├──► cliff_safety_node ──► /cmd_vel ──► Drive-Knoten
Dashboard ──► /dashboard_cmd_vel ──┘       │
                                           │
Sensor-Knoten ──► /cliff (Bool, Best-Effort, 20 Hz) ──┘
              ──► /range/front (Range, 10 Hz) ──┘
```

- Bei `use_cliff_safety:=True` (Standard): `dashboard_bridge` wird per Launch-Remapping von `/cmd_vel` auf `/dashboard_cmd_vel` umgeleitet
- Bei `use_cliff_safety:=False`: `dashboard_bridge` publiziert direkt auf `/cmd_vel`
- Cliff-Safety blockiert bei Cliff (`/cliff` = true) ODER Ultraschall < 80 mm (Freigabe > 120 mm, Hysterese)

---

## 9. Navigationsziel via Dashboard

Klick auf SLAM-Karte → `nav_goal` per WebSocket → `dashboard_bridge` → Nav2 `NavigateToPose` ActionClient → Status-Rueckmeldung per `nav_status` (1 Hz).

Laufendes Ziel per `nav_cancel` abbrechbar.

---

## 10. Build und Entwicklung

```bash
cd dashboard/
npm install                    # Abhaengigkeiten installieren
npm run dev                    # Entwicklungsserver (https://amr.local:5173)
npm run dev -- --host 0.0.0.0  # Extern erreichbar
npm run build                  # Produktion (tsc + vite build)
npm run lint                   # ESLint
npx tsc --noEmit               # TypeScript Type-Check
```

### Entwicklungsmodus (zwei Prozesse noetig)

1. ROS2-Launch: `./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True use_rviz:=False`
2. Vite-Dev: `cd dashboard && npm run dev -- --host 0.0.0.0`

### HTTPS-Zertifikate (mkcert)

- `amr.local+5.pem` und `amr.local+5-key.pem` in `dashboard/`
- Vite, WebSocket-Server und MJPEG-Server nutzen dieselben Zertifikate
- Ohne Zertifikate: Fallback auf HTTP/WS (unverschluesselt)
- Setup-Dokumentation: `planung/https-setup-amr-dashboard.md`

### TypeScript-Konfiguration

- `strict: true`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`
- Target: ES2022, Module: ESNext, JSX: react-jsx

---

## 11. Responsive Design

- **Desktop (lg, >= 1024px):** 4er-Grid, Sidebar + 3 Haupt-Panels + 2 Kontroll-Panels
- **Mobile/Tablet:** Vertikaler Stack, Sidebar versteckt (Toggle-Button), Touch-freundlich

---

## 12. Abgrenzung

- ROS2-Topics, QoS, TF-Baum: `docs/ros2_system.md`
- Vision-Pipeline (Hailo, Gemini): `docs/vision_pipeline.md`
- HTTPS-Setup: `planung/https-setup-amr-dashboard.md`
- Backend-Node (`dashboard_bridge`): `amr/scripts/dashboard_bridge.py`
