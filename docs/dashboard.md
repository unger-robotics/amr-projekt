# Dashboard

Das Dashboard ist die Weboberflaeche fuer Telemetrie, Kameraansicht, Kartenansicht und Fernsteuerung. Die ROS2-Anbindung erfolgt ueber den Node `dashboard_bridge`. Dieser Node stellt Telemetrie und Karte per WebSocket sowie den Kamerastream per MJPEG bereit.

### Ports

- WebSocket: `9090`
- MJPEG: `8082`
- Vite-Entwicklung: `5173`
- Hailo-UDP: `5005`

### Aufgaben des `dashboard_bridge`

- ROS2-Daten fuer den Browser aufbereiten
- MJPEG-Stream fuer Benutzeroberflaeche und Host-Runner bereitstellen
- Steuerbefehle aus dem Browser an ROS2 publizieren
- Telemetrie fuer Verbindung und Systemzustand aggregieren

### Entwicklungsmodus

Benutzeroberflaeche lokal starten:

```bash
cd ~/amr-projekt/dashboard
npm run dev -- --host
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

- Im Normalbetrieb leitet der Knoten empfangene Twist-Nachrichten von `/nav_cmd_vel` oder `/dashboard_cmd_vel` direkt an `/cmd_vel` weiter.
- Bei Cliff-Erkennung (`/cliff` = true) blockiert der Knoten alle Fahrbefehle und sendet stattdessen einen Null-Twist (20 Hz Timer) auf `/cmd_vel`.
- Einmalig wird ein Audio-Alarm ueber `/audio/play` ausgeloest (Topic `cliff_alarm`).
- Nach Aufhebung des Cliff-Zustands (`/cliff` = false) wird der Normalbetrieb wiederhergestellt.
- Beim Shutdown sendet der Knoten einen finalen Stopp-Befehl.

**QoS-Hinweis:** `/cliff` nutzt Best-Effort QoS. `/nav_cmd_vel`, `/dashboard_cmd_vel` und `/cmd_vel` nutzen Reliable QoS.

**Remapping:** Nav2 wird ueber `nav2_params.yaml` so konfiguriert, dass der `controller_server` auf `/nav_cmd_vel` publiziert (in ROS 2 Humble ist `SetRemap` im Launch-File nicht verfuegbar). Der `dashboard_bridge` publiziert Joystick-Befehle auf `/dashboard_cmd_vel`. Beide Pfade laufen durch den `cliff_safety_node`, der als einziger auf `/cmd_vel` publiziert.

### Abgrenzung

Diese Datei beschreibt das Dashboard als Teilsystem. Die vollstaendige Startreihenfolge fuer den kombinierten Live-Betrieb mit Dashboard, Kamera, Vision und SLAM steht in `docs/build_and_deploy.md` im Abschnitt `Live-Betrieb: Dashboard + Vision + SLAM`.
