# AMR Kalibrierung & Validierung — Anleitung

## Status Phase A-C (abgeschlossen)

Die Software-Integration ist abgeschlossen:

| Task | Status | Ergebnis |
|------|--------|----------|
| Launch-File (RPLIDAR + Laser-TF) | erledigt | `rplidar_node` + `base_link->laser` (180 deg Yaw) |
| Script-Symlinks (9 entry_points) | erledigt | 9 Executables in `my_bot` |
| Services gestoppt | erledigt | `/dev/ttyACM0` frei |
| Workspace gebaut + verify.sh | erledigt | 14 PASS, 0 FAIL |
| micro-ROS UART-Verbindung | erledigt | ~19 Hz, Std < 1.3 ms |
| TF-Baum (odom->base_link->laser) | erledigt | `odom_to_tf` Bridge-Node erstellt |

**Entdeckte und behobene Probleme:**

- `odom_to_tf` Node war noetig (ESP32 publiziert nur `/odom`, keinen TF)
- ESP32-Firmware hat **keine Reconnection-Logik** — nach Agent-Kill muss ESP32 per DTR/RTS-Sequenz resettet werden
- Alte `docker compose run` Container blockieren den Serial-Port — immer mit `docker ps -a` pruefen

---

## Voraussetzungen fuer Kalibrierung

### Hardware-Checkliste

- [ ] **RPLIDAR A1** an USB angeschlossen (`/dev/ttyUSB0` muss existieren)
- [ ] **ESP32 (XIAO ESP32-S3)** an USB angeschlossen (`/dev/ttyACM0`)
- [ ] **ArUco-Marker ID 42** (DICT_4X4_50) ausgedruckt (fuer Docking-Test)
- [ ] **Kamera-Bridge** aktiv: `sudo systemctl status camera-v4l2-bridge.service`
- [ ] **2-5 m freie Bodenflaeche** (glatt, ohne Hindernisse)
- [ ] **Massband** (fuer UMBmark-Messungen)
- [ ] **Akku geladen** oder Netzteil angeschlossen

### Hardware pruefen

```bash
# Devices vorhanden?
ls -la /dev/ttyACM0 /dev/ttyUSB0 /dev/video10

# Kein anderer Prozess auf ESP32-Port?
sudo fuser -v /dev/ttyACM0
sudo systemctl stop embedded-bridge.service

# Kamera-Bridge laeuft?
sudo systemctl status camera-v4l2-bridge.service
```

### ESP32 Reset-Prozedur (vor jedem Neustart noetig!)

Die ESP32-Firmware hat keine Reconnection-Logik. Nach jedem Agent-Stopp muss die ESP32 resettet werden:

```bash
# Option A: DTR/RTS-Sequenz (remote, zuverlaessig)
python3 << 'EOF'
import serial, time
s = serial.Serial('/dev/ttyACM0', 115200)
s.setDTR(False); s.setRTS(True); time.sleep(0.1)
s.setDTR(True); s.setRTS(False); time.sleep(0.05)
s.setDTR(False); s.close()
print('ESP32 Reset OK')
EOF
sleep 4

# Option B: Reset-Knopf am XIAO ESP32-S3 druecken (physisch)

# Option C: USB-Stecker kurz abziehen und wieder einstecken
```

### Container und Agent starten

```bash
cd ~/AMR-Bachelorarbeit/amr/docker

# ESP32 resetten (siehe oben), dann sofort:
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=false use_nav:=false use_rviz:=False

# Zweites Terminal (im laufenden Container):
./run.sh exec bash
```

---

## Phase D: Kalibrierung (Tasks 11-17)

Die Kalibrierung folgt dem V-Modell und baut aufeinander auf. Jeder Schritt muss bestanden werden, bevor der naechste beginnt.

```
Encoder -> Kinematik -> UMBmark -> PID -> SLAM -> Navigation -> Docking -> Report
                         |                  |
                    config.h           main.cpp
                    aendern            anpassen
                         |                  |
                    ESP32 neu          ESP32 neu
                     flashen            flashen
```

---

### Task 11: Kinematik-Validierung (V-Modell Phase 4)

**Ziel:** Grundlegende Fahr-Kinematik verifizieren (Geradeausfahrt, Drehung, Kreisfahrt).

**Vorbereitung:**
- Roboter auf glattem Boden, mindestens 2 m freie Flaeche in Fahrtrichtung
- Stack: `use_slam:=false use_nav:=false` (nur micro-ROS + Odometrie)
- Raeder muessen Bodenkontakt haben

**Durchfuehrung:**

```bash
# Terminal 1: Stack starten (nach ESP32-Reset!)
cd ~/AMR-Bachelorarbeit/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=false use_nav:=false use_rviz:=False

# Terminal 2: Kinematik-Test
./run.sh exec ros2 run my_bot kinematic_test
# Oder einzelne Tests:
./run.sh exec ros2 run my_bot kinematic_test gerade    # Nur Geradeausfahrt
./run.sh exec ros2 run my_bot kinematic_test drehung   # Nur 90-Grad-Drehungen
./run.sh exec ros2 run my_bot kinematic_test kreis     # Nur Kreisfahrt
```

**Tests:**

| Test | Beschreibung | Parameter | Dauer |
|------|-------------|-----------|-------|
| A: Geradeausfahrt | 1 m geradeaus | v=0.2 m/s, 5 s | ~8 s |
| B: 90-Grad-Drehung | 5x CW + 5x CCW | omega=pi/2 rad/s, 1 s | ~60 s |
| C: Kreisfahrt | 1 volle Umdrehung | v=0.2 m/s, omega=0.5 rad/s | ~15 s |

**Akzeptanzkriterien:**

| Kenngr. | Akzeptanz | Beschreibung |
|---------|-----------|-------------|
| Streckenabweichung | < 5 % | Geradeausfahrt: Soll vs. Ist |
| Laterale Drift | < 50 mm | Seitliche Abweichung bei Geradeausfahrt |
| Winkelabweichung | < 5 deg | 90-Grad-Drehung: Mittelwert CW/CCW |

**Ergebnis:** `amr/scripts/kinematic_results.json`

**Falls NICHT BESTANDEN:**
- Streckenabweichung > 5 %: Encoder-Kalibrierung pruefen (`ros2 run my_bot encoder_test`)
- Laterale Drift > 50 mm: Spurbreite (WHEEL_BASE) in `hardware/config.h` pruefen
- Winkelabweichung > 5 deg: UMBmark-Kalibrierung (naechster Schritt) wird dies korrigieren

---

### Task 12: UMBmark-Kalibrierung (V-Modell Phase 5)

**Ziel:** Systematische Odometrie-Fehler nach Borenstein & Feng 1996 bestimmen und korrigieren.

**Vorbereitung:**
- Mindestens 5x5 m freie Flaeche
- Massband und Stift zum Markieren
- Startposition markieren (Klebeband-Kreuz am Boden)
- 4x4 m Quadrat auf dem Boden markieren (optional, als Referenz)

**Durchfuehrung:**

Der Roboter faehrt 10 Mal ein 4x4 m Quadrat (5x im Uhrzeigersinn, 5x gegen Uhrzeigersinn). Nach jedem Lauf wird die Endposition gemessen.

```bash
# Schritt 1: 10 Quadratfahrten durchfuehren (manuell gesteuert oder per Skript)
# Fuer jeden Lauf:
#   - Roboter exakt auf Startposition setzen
#   - Quadrat fahren lassen (4 Seiten a 4 m mit 90-Grad-Drehungen)
#   - Endposition relativ zur Startposition messen (x, y in mm)
#   - Notieren: CW Lauf 1-5, CCW Lauf 1-5

# Schritt 2: Auswertung (KEIN ROS2 noetig, laeuft auf dem Pi direkt)
python3 ~/AMR-Bachelorarbeit/amr/scripts/umbmark_analysis.py
# Interaktive Eingabe: 5 CW-Endpositionen (x y in mm), dann 5 CCW-Endpositionen

# Oder aus vorbereiteter JSON-Datei:
python3 ~/AMR-Bachelorarbeit/amr/scripts/umbmark_analysis.py messdaten.json
```

**JSON-Eingabeformat:**

```json
{
  "cw": [[x1,y1], [x2,y2], [x3,y3], [x4,y4], [x5,y5]],
  "ccw": [[x1,y1], [x2,y2], [x3,y3], [x4,y4], [x5,y5]]
}
```

Alle Werte in **Millimeter** relativ zur Startposition.

**Ausgabe:**

Das Skript berechnet:
- **E_d** (Raddurchmesser-Verhaeltnis): Korrigiert unterschiedliche Radgroessen
- **E_b** (Spurbreite-Korrektor): Korrigiert die effektive Spurbreite
- Korrigierte Werte fuer `WHEEL_BASE`, `TICKS_PER_REV_LEFT`, `TICKS_PER_REV_RIGHT`
- Scatterplot der Endpositionen (`umbmark_results.png`)

**Nach der Auswertung — config.h anpassen:**

Die UMBmark-Korrekturfaktoren werden ueber angepasste `TICKS_PER_REV_LEFT` und `TICKS_PER_REV_RIGHT` in `config.h` umgesetzt. `WHEEL_DIAMETER` bleibt symmetrisch.

```bash
# Ausgabe des Skripts enthaelt Copy-Paste-Werte:
# #define WHEEL_BASE           0.XXXXXX  // [m] UMBmark-korrigiert
# #define TICKS_PER_REV_LEFT   XXX.Xf    // UMBmark-korrigiert
# #define TICKS_PER_REV_RIGHT  XXX.Xf    // UMBmark-korrigiert

# Datei bearbeiten:
nano ~/AMR-Bachelorarbeit/hardware/config.h

# ESP32 neu flashen (PlatformIO):
cd ~/AMR-Bachelorarbeit/amr/esp32_amr_firmware
pio run -t upload
```

**Akzeptanzkriterien:**

| Kenngr. | Akzeptanz |
|---------|-----------|
| E_max,syst (vor Kalibrierung) | Wird gemessen (Referenzwert) |
| Reduktionsfaktor (nach Kalibrierung) | >= 10x |

**Ergebnis:** `amr/scripts/umbmark_results.json` + `umbmark_results.png`

**Hinweis:** Nach dem Flashen der neuen config.h-Werte sollte der Kinematik-Test (Task 11) wiederholt werden, um die Verbesserung zu verifizieren.

---

### Task 13: PID-Re-Tuning (V-Modell Phase 6)

**Ziel:** PID-Regler-Performance nach UMBmark-Korrekturen verifizieren und ggf. nachstellen.

**Vorbereitung:**
- **Roboter aufbocken** (Raeder muessen frei drehen!)
- Stack: `use_slam:=false use_nav:=false`
- Aktuelle PID-Werte: Kp=1.5, Ki=0.5, Kd=0.0 (in `main.cpp`)

**Durchfuehrung:**

```bash
# Terminal 1: Stack starten (nach ESP32-Reset!)
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=false use_nav:=false use_rviz:=False

# Terminal 2: PID-Sprungantwort (Live-Modus)
./run.sh exec ros2 run my_bot pid_tuning live
```

Das Skript:
1. Wartet 2 s auf Odometrie-Verbindung
2. Sendet Sprung: cmd_vel v=0.4 m/s (Soll-Geschwindigkeit)
3. Zeichnet 10 s Odometrie auf
4. Sendet Stopp
5. Berechnet Kenngroessen und gibt Tuning-Empfehlungen

**Akzeptanzkriterien:**

| Kenngr. | Akzeptanz | Beschreibung |
|---------|-----------|-------------|
| Anstiegszeit (10%-90%) | < 500 ms | Zeit von 10% auf 90% des Sollwerts |
| Ueberschwingen | < 15 % | Maximale Ueberschreitung des Sollwerts |
| Einschwingzeit (+/-5%) | < 1.0 s | Zeit bis dauerhaft im 5%-Band |
| Stationaerer Regelfehler | < 5 % | Verbleibende Abweichung nach Einschwingen |

**Ergebnis:** `amr/scripts/pid_results.json` + `pid_sprungantwort.png` (Diagramm mit Markierungen)

**Falls Tuning noetig:**

Das Skript gibt automatische Empfehlungen:
- Anstiegszeit zu langsam: Kp erhoehen
- Ueberschwingen zu hoch: Kp reduzieren, Kd > 0
- Einschwingzeit zu lang: Kd erhoehen
- Stationaerer Fehler zu gross: Ki erhoehen

```bash
# PID-Werte anpassen in main.cpp (Zeile 19-20):
nano ~/AMR-Bachelorarbeit/amr/esp32_amr_firmware/src/main.cpp
# Zeilen: PidController pid_l(Kp, Ki, Kd, -1.0, 1.0);
#         PidController pid_r(Kp, Ki, Kd, -1.0, 1.0);

# ESP32 neu flashen:
cd ~/AMR-Bachelorarbeit/amr/esp32_amr_firmware
pio run -t upload

# PID-Test wiederholen bis Akzeptanzkriterien erfuellt
```

---

### Task 14: SLAM-Validierung (V-Modell Phase 8)

**Ziel:** SLAM Toolbox mit RPLIDAR A1 testen. Absolute Trajectory Error (ATE) messen.

**Vorbereitung:**
- **RPLIDAR A1 muss angeschlossen sein** (`/dev/ttyUSB0`)
- Stack: `use_nav:=false` (SLAM aktiv, Navigation aus)
- Raum mit Waenden/Moebeln (RPLIDAR braucht Landmarken)
- Roboter auf Boden

**Durchfuehrung:**

```bash
# Terminal 1: Stack mit SLAM starten (nach ESP32-Reset!)
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false use_rviz:=False

# Terminal 2: SLAM-Validierung (2 Minuten Aufzeichnung)
./run.sh exec ros2 run my_bot slam_validation -- --live --duration 120
```

**Waehrend der Aufzeichnung:**
- Roboter manuell durch den Raum fahren (Teleop oder physisch schieben)
- Verschiedene Bereiche abfahren (Schleifen, Korridore)
- Mindestens einmal zum Startpunkt zurueckkehren (Loop Closure testen)

**Alternativ mit Teleop:**

```bash
# Terminal 3: Teleop-Steuerung
./run.sh exec ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Akzeptanzkriterien:**

| Kenngr. | Akzeptanz |
|---------|-----------|
| ATE (RMSE) | < 0.20 m |
| TF-Kette map->odom->base_link->laser | Vollstaendig |

**Ergebnis:** `amr/scripts/slam_results.json` + `slam_validation_plot.png`

**Falls NICHT BESTANDEN:**
- ATE > 0.20 m: SLAM-Parameter pruefen (`mapper_params_online_async.yaml`)
- TF-Kette unvollstaendig: Nodes pruefen (`ros2 node list`, `ros2 topic list`)
- Wenig Loop Closure: Raum hat zu wenige Landmarken

---

### Task 15: Navigations-Validierung (V-Modell Phase 8)

**Ziel:** Nav2 Waypoint-Navigation testen. Positionsgenauigkeit an 4 Waypoints messen.

**Vorbereitung:**
- Stack: Voll (SLAM + Nav2 aktiv)
- **Erst eine Karte erstellen** (SLAM-Modus) oder bestehende Karte laden
- Mindestens 2x2 m freie Flaeche
- Roboter auf Boden, Startposition = (0, 0)

**Durchfuehrung:**

```bash
# Terminal 1: Voller Stack (nach ESP32-Reset!)
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False

# Warten bis Nav2 "Lifecycle nodes active" meldet (~10-15 s)

# Terminal 2: Navigationstest
./run.sh exec ros2 run my_bot nav_test
# Optional: --timeout 90 (laengerer Timeout pro Waypoint)
```

**Waypoint-Parcours (2x2 m Rechteck):**

```
WP3 (0,2) -------- WP2 (2,2)
    |                    |
    |    2m x 2m         |
    |                    |
WP4 (0,0) -------- WP1 (2,0)
  Start
```

| Waypoint | X [m] | Y [m] | Yaw [rad] |
|----------|-------|-------|-----------|
| WP1 | 2.0 | 0.0 | 0.0 |
| WP2 | 2.0 | 2.0 | 1.571 |
| WP3 | 0.0 | 2.0 | 3.142 |
| WP4 | 0.0 | 0.0 | 0.0 |

**Akzeptanzkriterien:**

| Kenngr. | Akzeptanz |
|---------|-----------|
| Positionsfehler (xy) | < 10 cm pro Waypoint |
| Orientierungsfehler (yaw) | < 8 deg (~0.15 rad) |
| Alle 4 Waypoints erreicht | Ja |

**Ergebnis:** `amr/scripts/nav_results.json`

**Falls NICHT BESTANDEN:**
- Positionsfehler > 10 cm: Nav2-Parameter pruefen (`nav2_params.yaml`, RPP Controller Toleranzen)
- Waypoint nicht erreicht (Timeout): Costmap-Konfiguration pruefen, Hindernisse im Weg?
- Orientierungsfehler: RPP Controller `max_angular_vel` und `goal_checker` anpassen

---

### Task 16: Docking-Validierung (V-Modell Phase 9)

**Ziel:** ArUco-Marker-basiertes Docking verifizieren. 10 Versuche, Erfolgsquote >= 80%.

**Vorbereitung:**
- Stack: `use_camera:=True` (Kamera-Node aktiv)
- **Kamera-Bridge muss laufen:** `sudo systemctl start camera-v4l2-bridge.service`
- ArUco-Marker ID 42 (DICT_4X4_50) an der Docking-Station befestigen
- Marker muss frontal zur Kamera zeigen, gut beleuchtet

**Durchfuehrung:**

```bash
# Terminal 1: Stack mit Kamera (nach ESP32-Reset!)
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_rviz:=False

# Terminal 2: Docking-Test (interaktiv)
./run.sh exec ros2 run my_bot docking_test
```

**Ablauf pro Versuch (10x wiederholen):**

1. Roboter manuell ca. 1.5 m vor den ArUco-Marker positionieren
2. Im Terminal `s` + Enter druecken
3. Roboter sucht Marker (dreht sich), faehrt an, dockt an
4. Ergebnis wird angezeigt (ERFOLG/FEHLSCHLAG, Dauer, Versatz)
5. Roboter faehrt 3 s rueckwaerts automatisch
6. Fuer naechsten Versuch Roboter neu positionieren

**Abbruch:** `q` + Enter beendet vorzeitig und zeigt Auswertung.

**Akzeptanzkriterien:**

| Kenngr. | Akzeptanz |
|---------|-----------|
| Erfolgsquote | >= 80 % (8/10 Versuche) |
| Timeout pro Versuch | 60 s |

**Ergebnis:** `amr/scripts/docking_results.json`

**Falls NICHT BESTANDEN:**
- Marker nicht erkannt: Beleuchtung pruefen, Kamera-Fokus, Marker-Groesse
- Marker verloren waehrend Annaeherung: `kp_angular` in `docking_test.py` anpassen
- Timeout: `approach_vel` erhoehen oder `docking_threshold` reduzieren

---

### Task 17: Gesamt-Validierungsbericht

**Ziel:** Alle Testergebnisse aggregieren und Gesamtbewertung erstellen.

**Vorbereitung:**
- Alle vorherigen Tests (Tasks 11-16) muessen durchgelaufen sein
- JSON-Ergebnisdateien muessen in `amr/scripts/` liegen

**Durchfuehrung:**

```bash
# Kein ROS2 noetig — reines Python-Skript
python3 ~/AMR-Bachelorarbeit/amr/scripts/validation_report.py
```

**Erwartete JSON-Dateien:**

| Datei | Test | Erstellt durch |
|-------|------|----------------|
| `encoder_results.json` | Encoder-Kalibrierung | `encoder_test` |
| `motor_results.json` | Motor-Deadzone | `motor_test` |
| `umbmark_results.json` | UMBmark | `umbmark_analysis.py` |
| `pid_results.json` | PID-Tuning | `pid_tuning` |
| `kinematic_results.json` | Kinematik | `kinematic_test` |
| `slam_results.json` | SLAM | `slam_validation` |
| `nav_results.json` | Navigation | `nav_test` |
| `docking_results.json` | Docking | `docking_test` |

**Ergebnis:** `validation_report_YYYYMMDD.md`

Der Report enthaelt:
- Tabelle aller Kriterien mit PASS/FAIL/AUSSTEHEND
- Zuordnung zu den 3 Forschungsfragen (FF1: Echtzeit, FF2: Praezision, FF3: Docking)
- Gesamtbewertung: BESTANDEN / NICHT BESTANDEN / UNVOLLSTAENDIG

---

## Naechste Schritte

### 1. RPLIDAR A1 anschliessen

Der RPLIDAR ist die wichtigste fehlende Hardware. Ohne ihn kein `/scan` Topic und kein SLAM.

```bash
# Nach Anschliessen pruefen:
ls -la /dev/ttyUSB0
lsusb | grep -i silicon   # CP2102 USB-UART Bridge
```

### 2. Empfohlene Reihenfolge

```
1. RPLIDAR anschliessen
2. Kinematik-Test (Task 11)
3. UMBmark (Task 12) — zeitintensivster manueller Schritt (~30 Min)
4. ESP32 flashen mit neuen config.h-Werten
5. Kinematik-Test wiederholen (Verbesserung verifizieren)
6. PID-Tuning (Task 13) — Raeder aufbocken!
7. SLAM-Validierung (Task 14) — 2 Min durch Raum fahren
8. Navigations-Validierung (Task 15) — 2x2 m Parcours
9. Docking-Validierung (Task 16) — 10 Versuche, ~15 Min
10. Gesamt-Report (Task 17)
```

### 3. Zeitaufwand (geschaetzt)

| Phase | Aufwand | Manuell? |
|-------|---------|----------|
| Kinematik-Test | ~5 Min | Roboter auf Boden stellen |
| UMBmark | ~30 Min | 10 Quadratfahrten manuell messen |
| ESP32 Flashen | ~2 Min | — |
| PID-Tuning | ~5 Min | Raeder aufbocken |
| SLAM-Validierung | ~5 Min | 2 Min durch Raum fahren |
| Navigation | ~10 Min | Freie Flaeche sichern |
| Docking | ~15 Min | 10x Roboter positionieren |
| Report | ~1 Min | — |

### 4. Quick-Start Befehle

```bash
# Vorbereitung (einmalig pro Session)
cd ~/AMR-Bachelorarbeit/amr/docker
sudo systemctl stop embedded-bridge.service

# ESP32 Reset (VOR JEDEM Stack-Start!)
python3 -c "
import serial, time
s = serial.Serial('/dev/ttyACM0', 115200)
s.setDTR(False); s.setRTS(True); time.sleep(0.1)
s.setDTR(True); s.setRTS(False); time.sleep(0.05)
s.setDTR(False); s.close()
print('ESP32 Reset OK')
"
sleep 4

# Stack starten (je nach Test)
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=false use_nav:=false use_rviz:=False  # Kinematik/PID
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false use_rviz:=False                  # SLAM
./run.sh ros2 launch my_bot full_stack.launch.py use_rviz:=False                                  # Navigation
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_rviz:=False                 # Docking

# Zweites Terminal oeffnen
./run.sh exec bash

# Tests ausfuehren
ros2 run my_bot kinematic_test
ros2 run my_bot pid_tuning live
ros2 run my_bot slam_validation -- --live --duration 120
ros2 run my_bot nav_test
ros2 run my_bot docking_test
```

---

## Troubleshooting

| Problem | Ursache | Loesung |
|---------|---------|---------|
| `/odom` Topic leer nach Agent-Start | ESP32 nicht resettet | DTR/RTS-Reset-Sequenz ausfuehren |
| RPLIDAR "operation time out" | Nicht angeschlossen oder falscher Port | `ls /dev/ttyUSB0`, USB-Kabel pruefen |
| `/scan` Topic fehlt | RPLIDAR-Node gestuerzt | `rplidar_node` Logs pruefen, Device-Permissions |
| SLAM "no scan data" | Kein `/scan` oder falscher Frame | TF `base_link->laser` pruefen |
| Nav2 "Goal rejected" | SLAM nicht gestartet oder keine Karte | Erst SLAM-Karte erstellen |
| Kamera "no frames" | Bridge nicht aktiv | `sudo systemctl restart camera-v4l2-bridge.service` |
| ArUco-Marker nicht erkannt | Zu dunkel, zu weit, falsches Dictionary | ID 42 / DICT_4X4_50, Beleuchtung, < 2 m |
| Container haengt | Alter Container blockiert Port | `docker ps -a`, stoppen, `docker rm` |
| PID schwingt stark | Kp zu hoch | Kp um 30% reduzieren, Kd=0.1 testen |
| ESP32 LED blinkt schnell | Firmware-Init fehlgeschlagen | Agent muss VOR ESP32-Boot laufen |
