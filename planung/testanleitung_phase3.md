# Testanleitung Phase 3: Lokalisierung und Kartierung

Anleitung zur Wiederholung der SLAM-Validierungstests (F03).

---

## Voraussetzungen

- Roboter auf ebenem Hartboden (Laminat, Fliesen, Beton)
- Akkuspannung > 10 V
- Beide ESP32-S3 (Drive + Sensor) geflasht und per USB angeschlossen
- Docker-Image gebaut (`docker compose build`)
- Workspace gebaut (`./run.sh colcon build --packages-select my_bot --symlink-install`)
- RPLidar A1 angeschlossen und funktionsfaehig (rplidar_test bestanden)
- Testraum mit ca. 15 m^2 Grundflaeche, Waende und markante Strukturen

## Grundprozedur: Stack starten (SLAM-Modus)

Bei jedem Neustart des Stacks muessen die ESP32s resettet werden,
da die Firmware keine Reconnection-Logik hat.

```bash
cd amr/docker/

# 1. Alte Container stoppen
docker compose down

# 2. ESP32s resetten (Ports muessen frei sein!)
python3 -c "
import serial, time
for port in ['/dev/amr_drive', '/dev/amr_sensor']:
    try:
        s = serial.Serial(port)
        s.setDTR(False); s.setRTS(True); time.sleep(0.1)
        s.setDTR(True); s.setRTS(False); time.sleep(0.05)
        s.setDTR(False); s.close()
        print(f'{port} reset OK')
    except Exception as e:
        print(f'{port}: {e}')
"

# 3. Stack starten mit SLAM und Dashboard (ohne Navigation fuer Test 3.1)
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=True use_nav:=False use_rviz:=False \
  use_cliff_safety:=True use_dashboard:=True

# 4. Warten (10-15 s), dann in zweitem Terminal pruefen:
./run.sh bash -c "timeout 5 ros2 topic hz /odom --window 30 2>&1 | tail -3"  # Soll: ~19 Hz
./run.sh bash -c "timeout 5 ros2 topic hz /scan --window 10 2>&1 | tail -3"  # Soll: ~7 Hz
./run.sh bash -c "timeout 5 ros2 topic hz /imu  --window 30 2>&1 | tail -3"  # Soll: ~30 Hz
```

Falls `/odom` oder `/scan` nicht erscheinen: Reset-Taster auf den
XIAO ESP32-S3 Boards druecken und Launch neu starten.

## Dashboard starten (separates Terminal)

Die manuelle Steuerung des Roboters erfolgt ueber das Dashboard.
Das Dashboard-Frontend laeuft ausserhalb des Docker-Containers:

```bash
cd dashboard/
npm run dev -- --host 0.0.0.0
# Erreichbar unter https://<Pi-IP>:5173/
```

**Hinweis:** Der ROS2-Node `dashboard_bridge` wird automatisch durch
`use_dashboard:=True` im Stack gestartet. Das Frontend muss separat
gestartet werden.

---

## Phase 3: Lokalisierung und Kartierung (F03)

### Testfall 3.1: Loop-Closure-Kartenqualitaet

**Platzbedarf:** Raum ca. 15 m^2 mit geschlossenem Rundweg
**Stack:** `use_slam:=True use_nav:=False use_dashboard:=True`
**Steuerung:** Dashboard (https://<Pi-IP>:5173/)

**Wichtig:** Das Skript muss direkt aus `/amr_scripts` im Container
aufgerufen werden (nicht ueber `ros2 run`), da das `amr_utils`-Modul
nur dort im PYTHONPATH liegt. Die Ausgabe wird in ein beschreibbares
Verzeichnis umgeleitet.

```bash
cd amr/docker/

# SLAM-Validierung starten (3 Minuten Aufzeichnung):
./run.sh bash -c "cd /amr_scripts && python3 slam_validation.py \
  --live --duration 180 \
  --output /ros2_ws/build/my_bot/my_bot/"
```

**Ablauf:**
1. Stack starten mit Dashboard (neue Karte, kein gespeicherter Map-State)
2. Dashboard im Browser oeffnen
3. SLAM-Validierung starten (siehe oben) — ab jetzt laeuft die Aufzeichnung
4. Roboter per Dashboard durch den Raum fahren (geschlossene Runde)
5. Zurueck zum Startpunkt fahren (Loop Closure)
6. Warten bis die 180 s abgelaufen sind
7. TF-Raten, Topic-Raten und ATE werden automatisch gemessen
8. Kartenqualitaet visuell pruefen (RViz2 oder Dashboard-Karte):
   - Keine doppelten Wandlinien nach Loop Closure
   - Waende schliessen am Startpunkt sauber

**Akzeptanzkriterien:**
- Kartenqualitaet: Keine verdoppelten Waende (visuell, manuell)
- TF-Rate map->odom: >= 1.5 Hz (automatisch)
- TF-Rate odom->base_link: >= 15 Hz (automatisch)
- Topic-Rate /odom: >= 15 Hz
- Topic-Rate /scan: >= 5 Hz
- Topic-Rate /imu: >= 25 Hz

### Testfall 3.2: ATE (Absolute Trajectory Error)

**Platzbedarf:** Gemappter Raum (Karte aus Test 3.1 oder gespeichert)
**Stack:** `use_slam:=True use_nav:=True use_dashboard:=True`

```bash
cd amr/docker/

# Stack mit Navigation neu starten (ESP32-Reset noetig!):
docker compose down
# [ESP32-Reset wie oben]
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=True use_nav:=True use_rviz:=False \
  use_cliff_safety:=True use_dashboard:=True

# Warten (15-20 s) bis Nav2 bereit, dann:
./run.sh bash -c "cd /amr_scripts && python3 slam_validation.py \
  --live --duration 120 \
  --output /ros2_ws/build/my_bot/my_bot/"
```

**Ablauf:**
1. Stack mit Navigation starten
2. SLAM-Validierung starten (siehe oben)
3. Navigation-Goal per Dashboard oder RViz2 setzen (Rundfahrt)
4. Roboter faehrt autonom, kehrt zum Startpunkt zurueck
5. slam_validation.py berechnet ATE automatisch
6. JSON, Markdown-Report und Plot werden gespeichert

**Akzeptanzkriterium:** ATE (RMSE) < 0.20 m

---

## Reihenfolge (empfohlen)

Fuer saubere Ergebnisse:

1. Dashboard-Frontend starten (`cd dashboard/ && npm run dev -- --host 0.0.0.0`)
2. Stack starten mit SLAM + Dashboard (ESP32-Reset)
3. Test 3.1: Manuelle Rundfahrt mit Loop Closure (180 s)
4. Stack stoppen, ESP32-Reset
5. Stack neu starten mit `use_nav:=True use_dashboard:=True`
6. Test 3.2: Autonome Rundfahrt mit ATE-Messung (120 s)

## JSON-Ergebnisse auslesen

Die JSON-Datei wird im Container gespeichert:

```bash
cd amr/docker/
./run.sh bash -c "cat /ros2_ws/build/my_bot/my_bot/slam_results.json"
```

Enthaltene Felder: `ate_m`, `max_error_m`, `mean_error_m`, `duration_s`,
`num_samples`, `tf_rate_map_odom_hz`, `tf_rate_odom_base_hz`,
`topic_rate_odom_hz`, `topic_rate_scan_hz`, `topic_rate_imu_hz`.

## Gesamtbericht generieren

```bash
cd amr/docker/
./run.sh ros2 run my_bot validation_report
```
