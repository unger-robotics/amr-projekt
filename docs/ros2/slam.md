---
title: SLAM
description: SLAM Toolbox Konfiguration fuer Lokalisierung und Kartierung.
---

# SLAM (Lokalisierung und Kartierung)

## SLAM Toolbox

Der AMR nutzt SLAM Toolbox im asynchronen Online-Modus (`use_slam:=True`):

- **Solver:** Ceres (SPARSE_NORMAL_CHOLESKY, Preconditioner: SCHUR_JACOBI)
- **Trust-Strategie:** Levenberg-Marquardt
- **Aufloesung:** 0.05 m (Raster)
- **LiDAR-Reichweite:** 0.2–12.0 m (RPLidar A1)
- **Konfiguration:** `config/mapper_params_online_async.yaml`

### Konfigurationsparameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| `resolution` | 0.05 m | Rasteraufloesung der Karte |
| `max_laser_range` | 12.0 m | Maximale LiDAR-Reichweite |
| `minimum_laser_range` | 0.2 m | Minimale LiDAR-Reichweite |
| `minimum_travel_distance` | 0.3 m | Mindestfahrstrecke vor neuem Scan-Matching |
| `do_loop_closing` | true | Automatische Schleifenerkennung |
| `loop_search_maximum_distance` | 8.0 m | Suchradius fuer Loop Closure |
| `loop_match_minimum_chain_size` | 10 | Mindestanzahl Scans fuer Loop-Match |
| `map_update_interval` | 0.5 s | Kartenaktualisierungsintervall |

## Kartierungsmodus

Dieser Modus erzeugt eine zweidimensionale Karte der Umgebung:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=False
```

Den Roboter langsam manuell durch die Umgebung bewegen (Joystick oder Teleoperation). Optimale Kartiergeschwindigkeit: circa 0,10–0,15 m/s.

### Karte speichern

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map
```

## Datenquellen

| Quelle | Topic | Rate | Beschreibung |
|--------|-------|------|-------------|
| RPLidar A1 | `/scan` | 7 Hz (konfiguriert; Datenblatt: 5,5 Hz typ.) | 360-Grad-Laserscan |
| Radodometrie | `/odom` | 20 Hz | Drive-Knoten Encoder |
| TF | `odom` → `base_link` | 20 Hz | `odom_to_tf` Knoten |
| TF | `base_link` → `laser` | statisch | 180 Grad Yaw-Kompensation |

## Loop Closure

Die SLAM Toolbox erkennt bereits besuchte Bereiche automatisch (`do_loop_closing: true`) und korrigiert die Karte. Voraussetzungen fuer zuverlaessigen Loop Closure:

- Ausreichend geometrische Features in der Umgebung (Waende, Moebel)
- Langsame Fahrt, damit genug Scans pro Bereich erfasst werden
- `loop_match_minimum_chain_size: 10` — mindestens 10 aufeinanderfolgende Scans muessen uebereinstimmen

## Haeufige Fehlerquellen

- **Zu schnelle Fahrt:** Bei > 0,20 m/s koennen Scan-Matching-Fehler auftreten (insbesondere in engen Raeumen)
- **Featurearme Umgebung:** Lange, glatte Waende ohne Ecken oder Moebel fuehren zu Drift
- **Odometrie-Drift:** Bei laengeren Kartierungsfahrten akkumuliert die Radodometrie Fehler — Loop Closure kompensiert dies

## Validierung

SLAM-Validierung (Phase 3):

```bash
./run.sh ros2 run my_bot slam_validation
```

Akzeptanzkriterium: Absolute Trajectory Error (ATE) < 0.20 m.

Gemessene Werte (Messprotokoll Phase 3, 10.03.2026):

| Testfall | ATE (RMSE) | /scan Rate | Ergebnis |
|----------|------------|------------|----------|
| 3.1 Loop-Closure-Kartenqualitaet | 0.190 m | 7.7 Hz | PASS |
| 3.2 ATE-Wiederholung | 0.030 m | 7.8 Hz | PASS |

## Aufloesung und Speicher

Die SLAM- und Costmap-Aufloesung betraegt 0.05 m. Feinere Aufloesung erhoeht den RAM-Bedarf auf dem Pi 5, groebere Aufloesung verringert die Navigationsgenauigkeit.
