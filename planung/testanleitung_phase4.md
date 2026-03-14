# Testanleitung Phase 4: Navigation

Anleitung zur Wiederholung der Navigationstests (F04).

---

## Voraussetzungen

- Roboter auf ebenem Hartboden (Laminat, Fliesen, Beton)
- Akkuspannung > 10 V
- Beide ESP32-S3 (Drive + Sensor) geflasht und per USB angeschlossen
- Docker-Image gebaut (`docker compose build`)
- Workspace gebaut (`./run.sh colcon build --packages-select my_bot --symlink-install`)
- RPLidar A1 angeschlossen und funktionsfaehig
- SLAM-Karte vorhanden oder SLAM aktiv (Karte wird waehrend des Tests aufgebaut)
- Testraum mit freier Flaeche >= 1,5 m x 1,5 m im kartierten Bereich
- Fuer Test 4.2: Kamera angeschlossen, ArUco-Marker ID 0 (DICT_4X4_50, 10 cm) montiert

## Grundprozedur: Stack starten (Navigationsmodus)

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

# 3. Stack starten mit Navigation
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=True use_nav:=True use_rviz:=False \
  use_cliff_safety:=True

# 4. Warten (15-20 s), dann in zweitem Terminal pruefen:
./run.sh bash -c "timeout 5 ros2 topic hz /odom --window 30 2>&1 | tail -3"  # Soll: ~19 Hz
./run.sh bash -c "timeout 5 ros2 topic hz /scan --window 10 2>&1 | tail -3"  # Soll: ~7 Hz
./run.sh bash -c "timeout 5 ros2 topic hz /imu  --window 30 2>&1 | tail -3"  # Soll: ~30 Hz
```

Falls `/odom` oder `/scan` nicht erscheinen: Reset-Taster auf den
XIAO ESP32-S3 Boards druecken und Launch neu starten.

Nav2 benoetigt 15-20 s nach dem Start fuer die Lifecycle-Aktivierung.
Die Bereitschaft erkennt man an: `[controller_server]: Activating`.

## Dashboard starten (separates Terminal)

Die manuelle Steuerung des Roboters erfolgt ueber das Dashboard.
Das Dashboard-Frontend laeuft ausserhalb des Docker-Containers:

```bash
cd dashboard/
npm run dev -- --host 0.0.0.0
# Erreichbar unter http://<Pi-IP>:5173/
```

**Hinweis:** Der ROS2-Node `dashboard_bridge` wird automatisch durch
`use_dashboard:=True` im Stack gestartet. Das Frontend muss separat
gestartet werden.

---

## Phase 4: Navigation (F04)

### Testfall 4.1: Waypoint-Navigation (1 m x 1 m Rechteck)

**Platzbedarf:** Freie Flaeche >= 1,5 m x 1,5 m im kartierten Raum
**Stack:** `use_slam:=True use_nav:=True use_cliff_safety:=True`
**Steuerung:** Automatisch via `nav_test.py`

**Wichtig:** Das Skript muss direkt aus `/amr_scripts` im Container
aufgerufen werden (nicht ueber `ros2 run`), da das `amr_utils`-Modul
nur dort im PYTHONPATH liegt. Die Ausgabe wird in ein beschreibbares
Verzeichnis umgeleitet.

```bash
cd amr/docker/

# Navigationstest starten (4 Waypoints, 60 s Timeout pro Waypoint):
./run.sh bash -c "cd /amr_scripts && python3 nav_test.py \
  --timeout 60 \
  --output /ros2_ws/build/my_bot/my_bot/"
```

**Ablauf:**
1. Stack mit Navigation starten (ESP32-Reset, 15-20 s warten)
2. Roboter in der Mitte der freien Flaeche positionieren (Startpose)
3. `nav_test.py` starten (siehe oben)
4. Roboter faehrt automatisch 4 Waypoints (1 m Rechteck):
   - WP1: 1 m geradeaus
   - WP2: 1 m links
   - WP3: 1 m zurueck (x-Richtung)
   - WP4: Startpunkt
5. Pro Waypoint: Pose-Abweichung wird via TF (map->base_link) gemessen
6. Visuell pruefen: keine physische Kollision waehrend der Fahrt
7. Bei blockiertem Pfad: Recovery-Verhalten beobachten (Spin/Backup/Wait)
8. Ergebnisse werden als JSON + Markdown-Report gespeichert

**Akzeptanzkriterien:**
- Alle 4 Waypoints erreicht (Status: ERREICHT)
- xy-Fehler < 0,10 m pro Waypoint
- Gier-Fehler < 0,15 rad (~8,6 Grad) pro Waypoint
- Keine physische Kollision (visuell, manuell)
- Cliff-Safety aktiv (kein Kantensturz)

### Testfall 4.2: ArUco-Docking (10 Versuche)

**Platzbedarf:** Freie Flaeche >= 2 m vor ArUco-Marker ID 0
**Stack:** `use_slam:=True use_nav:=True use_camera:=True use_dashboard:=True use_cliff_safety:=True`
**Steuerung:** Halbautomatisch (Benutzer positioniert, Skript faehrt)

**Vorbereitung:**
- ArUco-Marker ID 0 (DICT_4X4_50, 10 cm Seitenlaenge) auf Wandhoehe
  der Kamera anbringen (~8 cm ueber Boden)
- Marker-Generator: <https://chev.me/arucogen/> (Dictionary: 4x4, ID: 0)

```bash
cd amr/docker/

# 1. Stack stoppen, ESP32-Reset
docker compose down
# [ESP32-Reset wie oben]

# 2. Stack mit Kamera und Dashboard starten
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=True use_nav:=True use_camera:=True \
  use_dashboard:=True use_cliff_safety:=True

# 3. Warten (15-20 s), Kamera-Topic pruefen:
./run.sh bash -c "timeout 5 ros2 topic hz /camera/image_raw --window 10 2>&1 | tail -3"

# 4. Docking-Test starten (10 Versuche):
./run.sh bash -c "cd /amr_scripts && python3 docking_test.py \
  --output /ros2_ws/build/my_bot/my_bot/"
```

**Ablauf:**
1. Stack mit Kamera und Dashboard starten (ESP32-Reset)
2. `docking_test.py` starten
3. Fuer jeden der 10 Versuche:
   a. Roboter manuell ca. 1,5-2 m vor Marker positionieren (Marker sichtbar)
   b. `s` + Enter druecken
   c. Kamera erfasst Marker und steuert Roboter darauf zu (0,08 m/s)
   d. Andocken gilt als abgeschlossen (DOCKED), sobald der
      Ultraschallsensor einen Abstand von <= 60 cm misst und der
      Marker innerhalb der letzten 2 s sichtbar war
   e. Roboter stoppt, Ergebnis wird protokolliert
4. Benutzer positioniert Roboter manuell fuer naechsten Versuch
5. Nach 10 Versuchen: Auswertung + JSON-Export
6. Eingabe `q` + Enter bricht den Test vorzeitig ab (mit Teilauswertung)

**Zustaende:**
- SEARCHING: Marker nicht sichtbar, Roboter dreht sich suchend
- APPROACHING: Marker sichtbar, Kamera steuert Richtung, Roboter faehrt vor.
  Bei kurzem Marker-Verlust (< 3 s): geradeaus weiterfahren.
- DOCKED: Ultraschall <= 0,60 m und Marker kuerzlich sichtbar, Roboter stoppt (Erfolg)
- TIMEOUT: 60 s ohne Docking (Fehlschlag)

**Sensorik:**
- Kamera (ArUco-Erkennung): Richtungssteuerung via Proportionalregler (kp=0,3)
- Ultraschall (`/range/front`): Distanzmessung fuer Docking-Entscheidung
- Odometrie (`/odom`): Orientierungsmessung fuer Ergebnisprotokoll
- Lateraler Versatz via solvePnP mit kalibrierter Kameramatrix

**Akzeptanzkriterien:**
- Erfolgsquote >= 80 % (mindestens 8 von 10 Versuchen)
- Mittlerer lateraler Versatz < 2 cm (nur erfolgreiche Versuche)

---

## Reihenfolge (empfohlen)

Fuer saubere Ergebnisse:

1. Dashboard-Frontend starten (`cd dashboard/ && npm run dev -- --host 0.0.0.0`)
2. Stack starten mit `use_slam:=True use_nav:=True use_cliff_safety:=True` (ESP32-Reset)
3. Test 4.1: Waypoint-Navigation
4. Stack stoppen, ESP32-Reset
5. Stack neu starten mit `use_camera:=True use_dashboard:=True`
6. Test 4.2: ArUco-Docking (10 Versuche)

## JSON-Ergebnisse auslesen

Die JSON-Dateien werden im Container gespeichert:

```bash
cd amr/docker/
./run.sh bash -c "cat /ros2_ws/build/my_bot/my_bot/nav_results.json"
./run.sh bash -c "cat /ros2_ws/build/my_bot/my_bot/docking_results.json"
```

**nav_results.json** — Enthaltene Felder: `timestamp`, `all_passed`, `total_duration_s`,
`waypoints[]` mit `waypoint` (Name), `status`, `soll`/`ist` (Pose), `xy_error`,
`yaw_error`, `duration`, `passed`.

**docking_results.json** — Enthaltene Felder: `versuche[]` mit `erfolg`, `dauer_s`,
`lat_versatz_cm`, `orient_fehler_deg`, `ultraschall_m`; `statistik` mit `erfolgsquote_pct`,
`mittlerer_versatz_cm`.

## Gesamtbericht generieren

```bash
cd amr/docker/
./run.sh python3 /amr_scripts/validation_report.py
```
