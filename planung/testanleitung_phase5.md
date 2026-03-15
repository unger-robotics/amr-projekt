# Testanleitung Phase 5: Bedien- und Leitstandsebene

Anleitung zur Wiederholung der Dashboard- und Telemetrietests (F05).

---

## Voraussetzungen

- Roboter auf ebenem Hartboden (Laminat, Fliesen, Beton)
- Kein Hindernis im Bereich < 80 mm vor dem Ultraschall-Sensor
- Akkuspannung > 10 V
- Beide ESP32-S3 (Drive + Sensor) geflasht und per USB angeschlossen
- Docker-Image gebaut (`docker compose build`)
- Workspace gebaut (`./run.sh colcon build --packages-select my_bot --symlink-install`)
- Lautsprecher angeschlossen (fuer Audio-Test 5.4)

## Grundprozedur: Stack starten (Dashboard-Modus)

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

# 3. Stack starten mit Dashboard und Audio
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=True use_nav:=True use_rviz:=False \
  use_dashboard:=True use_cliff_safety:=True use_audio:=True

# 4. Warten (15-20 s), dann in zweitem Terminal pruefen:
./run.sh bash -c "timeout 5 ros2 topic hz /odom --window 30 2>&1 | tail -3"  # Soll: ~19 Hz
./run.sh bash -c "timeout 5 ros2 topic hz /scan --window 10 2>&1 | tail -3"  # Soll: ~7 Hz
./run.sh bash -c "timeout 5 ros2 topic hz /imu  --window 30 2>&1 | tail -3"  # Soll: ~30 Hz
```

Falls `/odom` oder `/scan` nicht erscheinen: Reset-Taster auf den
XIAO ESP32-S3 Boards druecken und Launch neu starten.

## Dashboard-Frontend starten (separates Terminal)

```bash
cd dashboard/
npm run dev -- --host 0.0.0.0
# Erreichbar unter http://<Pi-IP>:5173/
```

**Hinweis:** Der ROS2-Node `dashboard_bridge` wird automatisch durch
`use_dashboard:=True` im Stack gestartet. Das Frontend muss separat
gestartet werden.

---

## Phase 5: Bedien- und Leitstandsebene (F05)

Alle 5 Testfaelle werden durch ein einziges Skript ausgefuehrt.
Das Skript oeffnet einen eigenen WebSocket-Client und misst die
End-to-End-Kette innerhalb des ROS2-Systems.

### Testausfuehrung

```bash
cd amr/docker/

# Alle 5 Tests ausfuehren:
./run.sh bash -c "cd /amr_scripts && python3 dashboard_latency_test.py \
  --output /ros2_ws/build/my_bot/my_bot/"
```

**Optionale Parameter:**

| Parameter | Default | Beschreibung |
|---|---|---|
| `--samples N` | 100 | Anzahl Latenz-Messungen (Test 5.1) |
| `--ws-url URL` | `ws://localhost:9090` | WebSocket-URL |
| `--output DIR` | Skript-Verzeichnis | Ausgabeverzeichnis fuer JSON |

### Testfall 5.1: cmd_vel-Latenz (automatisiert)

**Messprinzip:** WebSocket-Client sendet 100x `cmd_vel(0.05, 0)` mit
10 Hz. ROS2-Subscriber auf `/cmd_vel` misst die Ankunftszeit. Die Latenz
ist die Differenz zwischen Sende- und Empfangszeitpunkt (`time.monotonic`).

**Datenpfad:** WebSocket → dashboard_bridge → /dashboard_cmd_vel →
cliff_safety_node → /cmd_vel → Subscriber

**Akzeptanzkriterien:**
- p95 < 100 ms
- avg < 50 ms

### Testfall 5.2: Telemetrie-Vollstaendigkeit (automatisiert)

**Messprinzip:** WebSocket-Client empfaengt 30 Sekunden lang alle
Server-Broadcasts und zaehlt pro op-Typ die Haeufigkeit.

**Pflicht-Broadcasts (muessen vorhanden sein):**
- `telemetry` (Soll 10 Hz, Minimum 4 Hz)
- `system` (Soll 1 Hz, Minimum 0.25 Hz)
- `nav_status` (Soll 1 Hz, Minimum 0.25 Hz)
- `sensor_status` (Soll 2 Hz, Minimum 0.5 Hz)
- `audio_status` (Soll 2 Hz, Minimum 0.5 Hz)

**Optionale Broadcasts (kein Fehler wenn fehlend):**
- `scan`, `map`, `vision_detections`, `vision_semantics`

**Akzeptanzkriterium:** Alle 5 Pflicht-Typen empfangen mit >= 50% der Soll-Rate.

### Testfall 5.3: Deadman-Timer (automatisiert)

**Messprinzip:** WebSocket-Client sendet 3 Sekunden lang cmd_vel + Heartbeat,
stoppt dann beides abrupt. Der ROS2-Subscriber auf `/cmd_vel` wartet auf
den ersten Null-Twist (vom Deadman-Timer des dashboard_bridge).

**Akzeptanzkriterium:** Stopp innerhalb 500 ms (300 ms Deadman-Timeout + Verarbeitungspuffer).

### Testfall 5.4: Audio-Feedback (automatisiert + akustische Pruefung)

**Messprinzip:** WebSocket-Client sendet 4 `audio_play`-Befehle
(startup, nav_start, nav_reached, cliff_alarm). ROS2-Subscriber auf
`/audio/play` prueft den Empfang jedes Keys.

**Manuelle Pruefung:** Waehrend des Tests auf akustische Ausgabe achten.
Die Sounds werden mit 2,5 s Abstand abgespielt.

**Akzeptanzkriterium:** 4/4 Sound-Keys auf `/audio/play` empfangen.

### Testfall 5.5: Notaus (automatisiert)

**Messprinzip:** WebSocket-Client sendet cmd_vel(0.05, 0) fuer 2 Sekunden,
dann 5x cmd_vel(0, 0) (EmergencyStop-Pattern aus dem Dashboard-Frontend).
Subscriber prueft die Zeit bis zum Null-Twist auf `/cmd_vel`.

**Akzeptanzkriterium:** Stopp innerhalb 100 ms.

---

## Reihenfolge (empfohlen)

1. Dashboard-Frontend starten (`cd dashboard/ && npm run dev -- --host 0.0.0.0`)
2. Stack starten mit `use_dashboard:=True use_cliff_safety:=True use_audio:=True` (ESP32-Reset)
3. Warten (15-20 s), Topic-Raten pruefen
4. `dashboard_latency_test.py` ausfuehren (alle 5 Tests automatisch)
5. Akustische Rueckmeldung bei Test 5.4 manuell verifizieren

## JSON-Ergebnisse auslesen

```bash
cd amr/docker/
./run.sh bash -c "cat /ros2_ws/build/my_bot/my_bot/dashboard_results.json"
```

**dashboard_results.json** — Enthaltene Felder: `timestamp`, `all_passed`,
`tests[]` mit `name`, `result` (PASS/FAIL), `metrics` (testspezifisch),
`kriterien` (Schwellwerte).

## Gesamtbericht generieren

```bash
cd amr/docker/
./run.sh python3 /amr_scripts/validation_report.py
```
