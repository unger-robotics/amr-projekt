# Dashboard

Das Dashboard ist die Weboberflaeche fuer Telemetrie, Kameraansicht, Kartenansicht und Fernsteuerung. Die ROS2-Anbindung erfolgt ueber den Node `dashboard_bridge`. Dieser Node stellt Telemetrie und Karte per WebSocket sowie den Kamerastream per MJPEG bereit.

### Ports

- WebSocket: `9090`
- MJPEG: `8082`
- Vite-Entwicklung: `5173`
- Hailo-UDP: `5005`

### Aufgaben des `dashboard_bridge`

- ROS2-Daten fuer den Browser aufbereiten (Telemetrie 10 Hz, LiDAR 2 Hz, Karte 0,5 Hz, System 1 Hz)
- MJPEG-Stream fuer Benutzeroberflaeche und Host-Runner bereitstellen
- Steuerbefehle aus dem Browser an ROS2 publizieren
- Telemetrie fuer Verbindung und Systemzustand aggregieren
- Navigationsziele an Nav2 senden und Status zurueckmelden (ActionClient fuer `NavigateToPose`)
- Vision-Detektionen (5 Hz) und semantische Analysen (0,5 Hz) an Clients weiterleiten

### WebSocket-Operationen

Vom Client empfangene Nachrichten (`op`-Feld):

| Operation | Beschreibung |
|---|---|
| `cmd_vel` | Fahrbefehle (`linear_x`, `angular_z`). Single-Controller: nur ein Client darf senden. |
| `servo_cmd` | Servo-Steuerung (`pan`, `tilt`) |
| `hardware_cmd` | Hardware-Parameter (`motor_limit`, `servo_speed`, `led_pwm`) |
| `heartbeat` | Deadman-Timer zuruecksetzen (300 ms Timeout) |
| `nav_goal` | Navigationsziel senden (`x`, `y`, `yaw` in Map-Koordinaten) |
| `nav_cancel` | Laufendes Navigationsziel abbrechen |

Vom Server gesendete Nachrichten:

| Operation | Rate | Beschreibung |
|---|---|---|
| `telemetry` | 10 Hz | Odometrie, IMU, Batterie, Ultraschall, Hz-Raten |
| `scan` | 2 Hz | LiDAR-Scan (komprimiert) |
| `map` | 0,5 Hz | Belegungskarte (PNG-kodiert) |
| `system` | 1 Hz | CPU, Temperatur, Speicher |
| `nav_status` | 1 Hz | Navigationsstatus (`idle`, `navigating`, `reached`, `failed`, `cancelled`) mit Zielkoordinaten und Restdistanz |
| `detections` | 5 Hz | Vision-Detektionen (Hailo) |
| `semantics` | 0,5 Hz | Semantische Analyse (Gemini) |

### Entwicklungsmodus

Benutzeroberflaeche lokal starten:

```bash
cd ~/amr-projekt/dashboard
npm run dev -- --host 0.0.0.0
```

### Statischer Produktivmodus

```bash
cd ~/amr-projekt/dashboard
npm run build
python3 -m http.server 3000 -d dist/
```

### Backend-Aktivierung

Das Dashboard-Backend wird im ROS2-Launch ueber `use_dashboard:=True` aktiviert.

Beispiel:

```bash
cd ~/amr-projekt/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_rviz:=False
```

### Sicherheitsmechanismen

- **Geschwindigkeitsbegrenzung:** 0,4 m/s linear, 1,0 rad/s angular (hart im Bridge-Node)
- **Deadman-Timer:** 300 ms ohne Heartbeat oder cmd_vel fuehrt zu automatischem Stopp
- **Single-Controller:** Nur ein WebSocket-Client darf cmd_vel senden (erster Client wird Controller)
- **Client-Disconnect:** Sofortiger Stopp bei Verbindungsverlust des Controllers

### cmd_vel-Routing und Cliff-Safety

Der `cliff_safety_node` arbeitet als Multiplexer zwischen Navigations- und Dashboard-Befehlen mit integriertem Cliff-Veto.

**Datenfluss:**

```
Nav2 ──► /nav_cmd_vel ──┐
                        ├──► cliff_safety_node ──► /cmd_vel ──► Drive-Knoten
Dashboard ──► /dashboard_cmd_vel ──┘       │
                                           │
Sensor-Knoten ──► /cliff (Bool, Best-Effort, 20 Hz) ──┘
```

**Funktionsweise:**

- Im Normalbetrieb leitet der Knoten empfangene Twist-Nachrichten direkt an `/cmd_vel` weiter.
- Bei Cliff-Erkennung (`/cliff` = true) blockiert der Knoten alle Fahrbefehle und sendet stattdessen einen Null-Twist (20 Hz Timer) auf `/cmd_vel`.
- Einmalig wird ein Audio-Alarm ueber `/audio/play` ausgeloest (Topic `cliff_alarm`).
- Nach Aufhebung des Cliff-Zustands (`/cliff` = false) wird der Normalbetrieb wiederhergestellt.
- Beim Shutdown sendet der Knoten einen finalen Stopp-Befehl.

**QoS-Hinweis:** `/cliff` nutzt Best-Effort QoS. `/cmd_vel` und `/dashboard_cmd_vel` nutzen Reliable QoS.

**Remapping:** Der `dashboard_bridge` wird im Launch-File mit Remapping `/cmd_vel` auf `/dashboard_cmd_vel` gestartet, wenn `use_cliff_safety:=True` (Standard). Der `cliff_safety_node` subscribt `/nav_cmd_vel` und `/dashboard_cmd_vel` und publiziert als einziger auf `/cmd_vel`.

### Navigationsziel via Dashboard

Ein Klick auf die SLAM-Karte im Dashboard sendet ein `nav_goal` per WebSocket. Der `dashboard_bridge` nutzt einen `ActionClient` fuer die Nav2-Action `NavigateToPose`, um das Ziel weiterzuleiten. Der Navigationsstatus (`navigating`, `reached`, `failed`, `cancelled`) wird per `nav_status`-Nachricht mit 1 Hz an alle Clients zurueckgesendet. Ein laufendes Ziel kann per `nav_cancel` abgebrochen werden.

### Abgrenzung

Diese Datei beschreibt das Dashboard als Teilsystem. Die vollstaendige Startreihenfolge fuer den kombinierten Live-Betrieb mit Dashboard, Kamera, Vision und SLAM steht in `docs/build_and_deploy.md` im Abschnitt `Live-Betrieb: Dashboard + Vision + SLAM`.
