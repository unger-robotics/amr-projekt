# Dashboard

Das Dashboard ist die Weboberflaeche fuer Telemetrie, Kameraansicht, Kartenansicht und Fernsteuerung. Die ROS2-Anbindung erfolgt ueber den Node `dashboard_bridge`. Dieser Node stellt Telemetrie und Karte per WebSocket sowie den Kamerastream per MJPEG bereit.

### Ports

- WebSocket: `9090`
- MJPEG: `8082`
- Vite-Entwicklung: `5173`
- Hailo-UDP: `5005`

### Aufgaben des `dashboard_bridge`

- ROS2-Daten fuer den Browser aufbereiten
- MJPEG-Stream fuer Frontend und Host-Runner bereitstellen
- Steuerbefehle aus dem Browser an ROS2 publizieren
- Telemetrie fuer Verbindung und Systemzustand aggregieren

### Entwicklungsmodus

Frontend lokal starten:

```bash
cd ~/AMR-Bachelorarbeit/dashboard
npm run dev -- --host
```

### Statischer Produktivmodus

```bash
cd ~/AMR-Bachelorarbeit/dashboard
npm run build
python3 -m http.server 3000 -d dist/
```

### Backend-Aktivierung

Das Dashboard-Backend wird im ROS2-Launch ueber `use_dashboard:=True` aktiviert.

Beispiel:

```bash
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_rviz:=False
```

### Abgrenzung

Diese Datei beschreibt das Dashboard als Teilsystem. Die vollstaendige Startreihenfolge fuer den kombinierten Live-Betrieb mit Dashboard, Kamera, Vision und SLAM steht in `docs/build_and_deploy.md` im Abschnitt `Live-Betrieb: Dashboard + Vision + SLAM`.
