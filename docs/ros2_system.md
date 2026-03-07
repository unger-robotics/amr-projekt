# ROS2-System

## Zweck

Dokumentation von Launch-Dateien, Nodes, Topics, TF-Baum und Betriebsmodi.

## Inhalte

- Full-Stack-, SLAM-, Navigation- und Kamera-Launches
- Node-Uebersicht
- Topic-Liste
- TF-Baum
- Debug- und Diagnosekommandos

## Regel

Topic-Tabellen und TF-Details gehoeren nur in diese Datei.

## ReSpeaker DoA/VAD-Node (optional)

Der `respeaker_doa_node` pollt Direction-of-Arrival und Voice Activity Detection vom ReSpeaker Mic Array v2.0 (XMOS XVF-3000) via USB Vendor Control Transfers (pyusb) mit 10 Hz.

**Topics:**
- `/sound_direction` (`std_msgs/Int32`) — Azimut 0-359 Grad
- `/is_voice` (`std_msgs/Bool`) — Sprache erkannt (VAD)

**Parameter:**
- `poll_rate_hz` (float, default 10.0) — Abfragerate

**Start:**
```bash
ros2 launch my_bot full_stack.launch.py use_respeaker:=True
```

**Voraussetzungen:**
- ReSpeaker per USB angeschlossen (Vendor 2886, Product 0018)
- udev-Regel via `host_setup.sh` installiert (USB-Zugriff ohne sudo)
- `pyusb` im Docker-Image (wird automatisch installiert)
