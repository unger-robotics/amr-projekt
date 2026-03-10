# Testanleitung Phase 1 + Phase 2

Anleitung zur Wiederholung aller Validierungstests fuer Fahrkern (F01)
und Sensor- und Sicherheitsbasis (F02).

---

## Voraussetzungen

- Roboter auf ebenem Hartboden (Laminat, Fliesen, Beton)
- Akkuspannung > 10 V
- Beide ESP32-S3 (Drive + Sensor) geflasht und per USB angeschlossen
- Docker-Image gebaut (`docker compose build`)
- Workspace gebaut (`./run.sh colcon build --packages-select my_bot --symlink-install`)

## Grundprozedur: Stack starten

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

# 3. Stack starten (Parameter je nach Testfall anpassen)
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=False use_nav:=False use_rviz:=False use_cliff_safety:=False

# 4. Warten (5-10 s), dann in zweitem Terminal pruefen:
./run.sh ros2 topic hz /odom    # Soll: ~19 Hz
./run.sh ros2 topic hz /imu     # Soll: ~30-35 Hz
```

Falls `/odom` oder `/imu` nicht erscheinen: Reset-Taster auf den
XIAO ESP32-S3 Boards druecken und Launch neu starten.

---

## Phase 1: Fahrkern (F01)

### Test 1.1 + 1.2: Geradeausfahrt (mit + ohne IMU)

**Platzbedarf:** 1.5 m Laenge, 30 cm Breite
**Stack:** `use_cliff_safety:=False`

```bash
./run.sh ros2 run my_bot straight_drive_test
```

**Ablauf:**
1. Gyro-Kalibrierung (3 s still stehen)
2. Test 1: Faehrt 1 m OHNE IMU-Korrektur (0.1 m/s, ca. 12 s)
3. Ergebnis wird angezeigt
4. "Enter druecken wenn bereit" — Roboter zurueckstellen
5. Gyro-Kalibrierung (3 s still stehen)
6. Test 2: Faehrt 1 m MIT IMU-Korrektur
7. JSON gespeichert als `straight_drive_results.json`

**Einzeln ausfuehren:**
```bash
./run.sh ros2 run my_bot straight_drive_test corrected    # Nur mit IMU
./run.sh ros2 run my_bot straight_drive_test uncorrected  # Nur ohne IMU
```

**Akzeptanzkriterien:**
- Lateraldrift < 5 cm
- Heading-Fehler (Gyro) < 5 Grad

### Test 1.3: Rotation 360 Grad

**Platzbedarf:** 50 x 50 cm (dreht auf der Stelle)
**Stack:** `use_cliff_safety:=False`

```bash
./run.sh ros2 run my_bot rotation_test
```

**Ablauf:**
1. Gyro-Kalibrierung (3 s still stehen)
2. Dreht 360 Grad gegen den Uhrzeigersinn (ca. 15 s)
3. Stoppt bei < 2 Grad Restfehler
4. JSON gespeichert als `rotation_results.json`

**Andere Winkel:**
```bash
./run.sh ros2 run my_bot rotation_test 90      # 90 Grad
./run.sh ros2 run my_bot rotation_test 180     # 180 Grad
./run.sh ros2 run my_bot rotation_test -- -90  # -90 Grad (rueckwaerts)
```

**Akzeptanzkriterium:** Winkelfehler < 5 Grad

---

## Phase 2: Sensor- und Sicherheitsbasis (F02)

### Test 2.1: Cliff-Safety Latenz

**Platzbedarf:** Tischkante oder erhoehte Flaeche mit Kante
**Stack:** `use_cliff_safety:=True` (WICHTIG!)
**Sicherheit:** Auffangsicherung bereithalten!

```bash
# Stack mit cliff_safety starten:
./run.sh ros2 launch my_bot full_stack.launch.py \
  use_slam:=False use_nav:=False use_rviz:=False use_cliff_safety:=True

# Test starten:
./run.sh ros2 run my_bot cliff_latency_test
```

**Ablauf:**
1. "Enter druecken wenn bereit"
2. Roboter faehrt mit 0.2 m/s vorwaerts
3. Bei Tischkante: Cliff-Sensor erkennt Kante
4. cliff_safety_node stoppt Motoren
5. Latenz und Bremsweg werden gemessen
6. JSON gespeichert als `cliff_latency_results.json`

**Akzeptanzkriterium:** Latenz < 50 ms

**Hinweis:** Der MH-B Cliff-Sensor erkennt dunkle/matte Oberflaechen
nicht zuverlaessig. Helle Tischplatte verwenden.

### Test 2.2: IMU 90-Grad-Rotation

**Platzbedarf:** 50 x 50 cm
**Stack:** `use_cliff_safety:=False`

```bash
./run.sh ros2 run my_bot rotation_test 90
```

**Akzeptanzkriterium:** Winkelfehler < 2 Grad

### Test 2.3 + 2.4: Sensor-Suite (Ultraschall + Cliff)

**Stack:** `use_cliff_safety:=False`
**Vorbereitung:** Objekt in bekanntem Abstand (z.B. 23 cm) fuer US-Test 2

```bash
./run.sh ros2 run my_bot sensor_test
```

**Interaktive Schritte:**
- Test 2: Soll-Distanz eingeben (z.B. `0.23`)
- Test 7: Cliff-Sensor abdecken oder ueber Kante halten, dann Enter
- Test 8: Raumtemperatur eingeben oder leer lassen (optional)

**JSON:** `sensor_results.json`

### Test 2.5: IMU-Suite

**Stack:** `use_cliff_safety:=False`
**WICHTIG:** Diesen Test VOR dem Rotationstest ausfuehren (oder nach
ESP32-Reset), damit Odom und IMU bei 0 Grad starten (Test 4 vergleicht
Heading-Referenzen).

```bash
./run.sh ros2 run my_bot imu_test
```

**Ablauf:**
- Test 1: Automatisch (3 s)
- Test 2: 60 s stillstehen! Nicht beruehren!
- Test 3: 5 s stillstehen
- Test 4: 5 s stillstehen

**JSON:** `imu_results.json`

---

## Reihenfolge (empfohlen)

Fuer saubere Ergebnisse ohne Offset-Probleme:

1. Stack starten (mit ESP32-Reset)
2. `imu_test` (braucht frische Odom bei 0 Grad)
3. `sensor_test`
4. `straight_drive_test`
5. `rotation_test` (360 Grad)
6. `rotation_test 90`
7. Stack neu starten mit `use_cliff_safety:=True` (ESP32-Reset!)
8. `cliff_latency_test`

## JSON-Ergebnisse auslesen

Die JSON-Dateien werden im Container gespeichert:

```bash
./run.sh cat /ros2_ws/build/my_bot/my_bot/straight_drive_results.json
./run.sh cat /ros2_ws/build/my_bot/my_bot/rotation_results.json
./run.sh cat /ros2_ws/build/my_bot/my_bot/cliff_latency_results.json
./run.sh cat /ros2_ws/build/my_bot/my_bot/sensor_results.json
./run.sh cat /ros2_ws/build/my_bot/my_bot/imu_results.json
```

## Gesamtbericht generieren

```bash
./run.sh python3 /amr_scripts/validation_report.py
```
