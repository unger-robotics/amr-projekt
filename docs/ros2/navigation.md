---
title: Navigation (Nav2)
description: Nav2-Stack, Cliff-Safety-Multiplexer und Betriebsmodi.
---

# Navigation (Nav2)

## Nav2-Stack

Der Nav2-Stack (`use_nav:=True`) stellt autonome Zielnavigation bereit:

- **Controller:** Regulated Pure Pursuit (RPP), 20 Hz, desired_linear_vel: 0.15 m/s
- **Planer:** NavFn (Dijkstra), 10 Hz
- **Costmap:** 2D, 0.05 m Aufloesung
- **Konfiguration:** `config/nav2_params.yaml`

Zielpunkte koennen ueber RViz2 (`2D Nav Goal`), per Kartenklick in der Benutzeroberflaeche oder programmatisch gesetzt werden.

## Cliff-Safety-Multiplexer

Der `cliff_safety_node` (`use_cliff_safety:=True`) multiplext alle Fahrbefehle:

```
Nav2 controller_server ──→ /nav_cmd_vel ──→ cliff_safety_node ──→ /cmd_vel
Dashboard Joystick ──→ /dashboard_cmd_vel ──→ cliff_safety_node ──→ /cmd_vel
Sensor-Knoten ──→ /cliff ──→ cliff_safety_node (blockiert bei true)
Sensor-Knoten ──→ /range/front ──→ cliff_safety_node (Stopp < 80 mm)
```

### Blockierungslogik

- **Cliff** (`/cliff` = true): Blockiert alle Fahrbefehle, sendet Null-Twist (20 Hz)
- **Ultraschall** (< 80 mm): Blockiert, Freigabe erst > 120 mm (Hysterese)
- **Audio-Alarm:** `cliff_alarm` einmalig bei Blockierung

### Remapping

- `dashboard_bridge`: `/cmd_vel` → `/dashboard_cmd_vel` (bei `use_cliff_safety:=True`)
- Nav2: publiziert auf `/nav_cmd_vel`
- Ohne Cliff-Safety: Nav2 und Dashboard publizieren direkt auf `/cmd_vel`

## Betriebsmodi

### Nur Navigation (ohne SLAM)

Nutzt eine vorhandene Karte fuer autonome Zielanfahrt:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_slam:=False
```

### Mit Benutzeroberflaeche

Navigationsziele per Kartenklick setzen. Waehrend der Navigation zeigt ein Overlay den Status und die verbleibende Distanz:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py use_dashboard:=True
```

### Manuelles Fahren

```bash
./run.sh exec ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --rate 10
```

Der Failsafe stoppt die Motoren automatisch nach 500 ms ohne neue Kommandos.
