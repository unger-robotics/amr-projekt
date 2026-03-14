# Validierung

## Zweck

Beschreibung von Testablaeufen, Validierungsskripten und Nachweisen.

## Inhalte

- Standalone-Skripte
- ROS2-Testknoten
- Hardware-in-the-loop-Pruefungen
- Messgroessen, Kriterien und Ergebnisablage

## CAN-Bus Validierung

`amr/scripts/can_validation_test.py` — Standalone (kein ROS2 noetig), nutzt `python-can` auf SocketCAN.

```bash
python3 amr/scripts/can_validation_test.py --duration 30
```

Prueft 12 CAN-IDs (5 Drive, 7 Sensor), Frame-Raten, Heartbeat-Dekodierung, Daten-Plausibilitaet. Ergebnis: `can_results.json`.

## Sensor-Validierung (Ultraschall + Cliff)

`amr/scripts/sensor_test.py` — ROS2-Knoten, subscribt `/range/front` und `/cliff`.

```bash
ros2 run my_bot sensor_test
```

8 Tests: US-Konnektivitaet (>= 7 Hz), statische Messung (< 5% Fehler, interaktiv), Bereichstest (min/max/fov), Wiederholgenauigkeit (Std < 15 mm), Cliff-Konnektivitaet (>= 15 Hz), Cliff-Boden (0 Fehlalarme), Cliff-Erkennung (interaktiv), Temperaturkorrektur (optional). Ergebnis: `sensor_results.json`.

**Hinweis:** `/cliff` nutzt Best-Effort QoS. Cliff-Sensor (MH-B) erkennt dunkle/matte Oberflaechen schlecht — weisses Papier als Boden-Ersatz beim Test auf dem Tisch verwenden.

## Validierungsskripte (Entry-Points aus setup.py)

Alle Skripte werden im Docker-Container ausgefuehrt:

```bash
cd ~/amr-projekt/amr/docker
./run.sh ros2 run my_bot <skriptname>
```

| Entry-Point | Zweck |
|---|---|
| `motor_test` | Einzelmotoransteuerung, PWM-Rampen und Richtungspruefung |
| `encoder_test` | Encoder-Tick-Zaehlung, CPR-Kalibrierung und Richtungserkennung |
| `pid_tuning` | Interaktives PID-Tuning mit Live-Sollwert/Istwert-Vergleich |
| `kinematic_test` | Differentialkinematik-Pruefung (Geradeaus, Drehung, Bogen) |
| `straight_drive_test` | Geradeausfahrt-Genauigkeit mit IMU-Korrektur |
| `rotation_test` | 360-Grad-Drehung, Winkelgenauigkeit (Open-Loop und Closed-Loop) |
| `imu_test` | IMU-Konnektivitaet, Gyro-Drift und Bias-Messung |
| `rplidar_test` | RPLidar-Rate, Aufloesung, Noise und Scan-Qualitaet |
| `slam_validation` | SLAM-Genauigkeit: Odom-Drift vs. SLAM-korrigierte Pose |
| `nav_test` | Nav2-Wegplanung und Zielpunktanfahrt |
| `docking_test` | ArUco-Marker-Erkennung und Docking-Anfahrt |
| `sensor_test` | Ultraschall- und Cliff-Validierung (siehe oben) |
| `cliff_latency_test` | Cliff-Latenztest (Kanten-Stopp End-to-End) |
| `can_validation_test` | CAN-Bus Frame-Raten und Plausibilitaet (Standalone) |
| `serial_latency_logger` | Messung der seriellen Latenz (USB-CDC) |
| `aruco_docking` | ArUco-Marker-basiertes Docking (Runtime-Node fuer Ladestation) |
| `validation_report` | Aggregiert JSON-Ergebnisse aller Validierungsskripte zu einem Gesamtbericht (Standalone-Skript, kein ROS2-Entry-Point) |

### Ergebnisformat

Jedes Validierungsskript erzeugt eine JSON-Datei (`<name>_results.json`). Der `validation_report` aggregiert alle Einzelergebnisse:

```bash
python3 amr/scripts/validation_report.py
```

## SLAM-Validierung (Phase 3)

`amr/scripts/slam_validation.py` — ROS2-Knoten, berechnet den Absolute Trajectory Error (ATE) zwischen SLAM-korrigierter Pose und reiner Odometrie.

```bash
./run.sh bash -c "cd /amr_scripts && python3 slam_validation.py --live --duration 180 --output /ros2_ws/build/my_bot/my_bot/"
```

Akzeptanzkriterien:
- ATE (RMSE) < 0.20 m
- TF-Rate map->odom >= 1.5 Hz
- TF-Rate odom->base_link >= 15 Hz

Testanleitung: `planung/testanleitung_phase3.md`, Messprotokoll: `planung/messprotokoll_phase3.md`.

## Navigationstest (Phase 4)

`amr/scripts/nav_test.py` — ROS2-Knoten, sendet Waypoints (1 m x 1 m Rechteck) ueber den Nav2 NavigateToPose Action-Server.

```bash
./run.sh ros2 run my_bot nav_test
```

Akzeptanzkriterien:
- Positionsfehler (xy): < 0.10 m
- Orientierungsfehler (yaw): < 0.15 rad (~8.6 Grad)

## Docking-Test (Phase 4)

`amr/scripts/docking_test.py` — ROS2-Knoten, fuehrt 10 Docking-Versuche mit ArUco-Marker durch.

```bash
./run.sh ros2 run my_bot docking_test
```

Ergebnis: Erfolgsquote, lateraler Versatz und Orientierungsfehler. Export als `docking_results.json`.

Testanleitung: `planung/testanleitung_phase4.md`, Messprotokoll: `planung/messprotokoll_phase4.md`.

## Testanleitungen (Uebersicht)

| Phase | Funktionsbereich | Testanleitung | Messprotokoll |
|---|---|---|---|
| 1+2 | Fahrkern + Sensor- und Sicherheitsbasis | `planung/testanleitung_phase1_phase2.md` | `planung/messprotokoll_phase1_phase2.md` |
| 3 | Lokalisierung und Kartierung | `planung/testanleitung_phase3.md` | `planung/messprotokoll_phase3.md` |
| 4 | Navigation | `planung/testanleitung_phase4.md` | `planung/messprotokoll_phase4.md` |

## Regel

Messkriterien vor Bewertung nennen: Messgroesse -> Kriterium -> Schluss -> Konsequenz.
