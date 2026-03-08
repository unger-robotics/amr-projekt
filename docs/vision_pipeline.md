# Vision-Pipeline

## Zweck

Dokumentation fuer Kamera, optionale Hailo-Inferenz und semantische Auswertung.

## Architektur: Hybride UDP-Bruecke

Die Vision-Pipeline nutzt eine UDP-Bruecke, weil der Hailo-8 NPU-Treiber (`hailort`) nur mit Host-Python 3.13 kompatibel ist, waehrend der ROS2-Container Python 3.10 (Humble) verwendet. Daher laeuft die Inferenz auf dem Host und die ROS2-Integration im Docker-Container.

## Datenfluss

```
Host (Python 3.13):
  v4l2_camera_node (ROS2, Docker)
      |
      v
  MJPEG-Stream (Port 8082, bereitgestellt von dashboard_bridge)
      |
      v
  host_hailo_runner.py (Host-Python, Hailo-8 YOLOv8 @ 5 Hz)
      |
      v  UDP 127.0.0.1:5005 (JSON-Detektionen)

Docker (Python 3.10, ROS2 Humble):
  hailo_udp_receiver_node (empfaengt UDP:5005)
      |
      v  /vision/detections (ROS2 Topic)
      |
      v
  gemini_semantic_node (Gemini Cloud API)
      |
      v  /vision/semantics (ROS2 Topic)
```

## Komponenten

| Komponente | Laufzeitumgebung | Aufgabe |
|---|---|---|
| `v4l2_camera_node` | Docker (ROS2) | USB-Kamera-Treiber, publiziert `/image_raw` |
| `dashboard_bridge` | Docker (ROS2) | MJPEG-Stream auf Port 8082 |
| `host_hailo_runner.py` | Host (Python 3.13) | YOLOv8-Inferenz via Hailo-8 NPU, sendet Detektionen per UDP |
| `hailo_udp_receiver_node` | Docker (ROS2) | Empfaengt UDP-JSON, publiziert `/vision/detections` |
| `gemini_semantic_node` | Docker (ROS2) | Semantische Auswertung via Gemini Cloud, publiziert `/vision/semantics` |

## Ports

| Port | Protokoll | Zweck |
|---|---|---|
| 5005 | UDP | Hailo-Detektionen (Host → Docker) |
| 8082 | HTTP | MJPEG-Kamerastream |
| 9090 | WebSocket | Dashboard-Telemetrie |
| 5173 | HTTP | Vite-Entwicklungsserver (Dashboard) |

## Aktivierung

Vision-Komponenten sind standardmaessig deaktiviert. Aktivierung ueber Launch-Parameter:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_camera:=True use_vision:=True use_dashboard:=True
```

Den Host-Runner separat starten:

```bash
python3 amr/scripts/host_hailo_runner.py
```

## Fallback-Modus

Ohne Hailo-8 NPU oder bei deaktivierter Vision (`use_vision:=False`) laufen Kamera und Dashboard-Stream weiterhin. Die Topics `/vision/detections` und `/vision/semantics` werden dann nicht publiziert. Navigation und SLAM sind davon unabhaengig.
