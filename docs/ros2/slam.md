---
title: SLAM
description: SLAM Toolbox Konfiguration fuer Lokalisierung und Kartierung.
---

# SLAM (Lokalisierung und Kartierung)

## SLAM Toolbox

Der AMR nutzt SLAM Toolbox im asynchronen Online-Modus (`use_slam:=True`):

- **Solver:** Ceres (SPARSE_NORMAL_CHOLESKY)
- **Aufloesung:** 0.05 m (Raster)
- **LiDAR-Reichweite:** 12 m (RPLidar A1)
- **Konfiguration:** `config/mapper_params_online_async.yaml`

## Kartierungsmodus

Dieser Modus erzeugt eine zweidimensionale Karte der Umgebung:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=False
```

Den Roboter langsam manuell durch die Umgebung bewegen (Joystick oder Teleoperation).

### Karte speichern

```bash
./run.sh exec ros2 run nav2_map_server map_saver_cli -f /ros2_ws/my_map
```

## Datenquellen

| Quelle | Topic | Rate | Beschreibung |
|--------|-------|------|-------------|
| RPLidar A1 | `/scan` | 7 Hz | 360-Grad-Laserscan |
| Radodometrie | `/odom` | 20 Hz | Drive-Knoten Encoder |
| TF | `odom` → `base_link` | 20 Hz | `odom_to_tf` Knoten |
| TF | `base_link` → `laser` | statisch | 180 Grad Yaw-Kompensation |

## Validierung

SLAM-Validierung (Phase 3):

```bash
./run.sh ros2 run my_bot slam_validation
```

Akzeptanzkriterium: Absolute Trajectory Error (ATE) < 0.20 m.

## Aufloesung und Speicher

Die SLAM- und Costmap-Aufloesung betraegt 0.05 m. Feinere Aufloesung erhoeht den RAM-Bedarf auf dem Pi 5, groebere Aufloesung verringert die Navigationsgenauigkeit.
