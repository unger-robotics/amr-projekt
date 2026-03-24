---
description: >-
  Hybrid-UDP-Architektur fuer Kamera, Hailo-8L-Inferenz und
  semantische Auswertung mit Gemini Cloud.
---

# Vision-Pipeline

## Zweck

Dokumentation fuer Kamera, optionale Hailo-Inferenz und semantische Auswertung.

## Architektur: Hybride UDP-Bruecke

Die Vision-Pipeline nutzt eine UDP-Bruecke, weil der Hailo-8L NPU-Treiber (`hailort`) nur mit Host-Python 3.13 kompatibel ist, waehrend der ROS2-Container Python 3.10 (Humble) verwendet. Daher laeuft die Inferenz auf dem Host und die ROS2-Integration im Docker-Container.

## Datenfluss

```
Host (Python 3.13):
  v4l2_camera_node (ROS2, Docker)
      |
      v
  MJPEG-Stream (Port 8082, bereitgestellt von dashboard_bridge)
      |
      v
  host_hailo_runner.py (Host-Python, Hailo-8L YOLOv8 @ 5 Hz)
      |
      v  UDP 127.0.0.1:5005 (JSON-Detektionen)

Docker (Python 3.10, ROS2 Humble):
  hailo_udp_receiver_node (empfaengt UDP:5005)
      |
      v  /vision/detections (ROS2 Topic)
      |
      v
  gemini_semantic_node (Gemini Cloud API, gemini-3.1-flash-lite-preview)
      |
      v  /vision/semantics (ROS2 Topic)
      |
      v
  tts_speak_node (gTTS Cloud → mpg123 → MAX98357A Lautsprecher, optional)
```

## Komponenten

| Komponente | Laufzeitumgebung | Aufgabe |
|---|---|---|
| `v4l2_camera_node` | Docker (ROS2) | USB-Kamera-Treiber, publiziert `/camera/image_raw` |
| `dashboard_bridge` | Docker (ROS2) | MJPEG-Stream auf Port 8082 |
| `host_hailo_runner.py` | Host (Python 3.13) | YOLOv8-Inferenz via Hailo-8L NPU, sendet Detektionen per UDP |
| `hailo_udp_receiver_node` | Docker (ROS2) | Empfaengt UDP-JSON, publiziert `/vision/detections` |
| `gemini_semantic_node` | Docker (ROS2) | Semantische Auswertung via Gemini Cloud, publiziert `/vision/semantics` |
| `tts_speak_node` | Docker (ROS2) | Spricht Gemini-Semantik via gTTS (Cloud, Deutsch) + mpg123 ueber MAX98357A Lautsprecher |

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
python3 amr/scripts/host_hailo_runner.py --model hardware/models/yolov8s.hef
```

Argumente des Host-Runners:

| Argument | Standard | Beschreibung |
|---|---|---|
| `--model` | `hardware/models/yolov8s.hef` | Pfad zum HEF-Modell |
| `--threshold` | `0.35` | Confidence-Schwellwert fuer Detektionen |
| `--fallback` | (Flag) | Dummy-Detektionen ohne Hailo-Hardware senden |

## Fallback-Modus

Der Host-Runner unterstuetzt einen `--fallback`-Modus, der Dummy-Detektionen ohne Hailo-Hardware sendet. Dies ermoeglicht die Entwicklung und Tests der nachgelagerten Pipeline (UDP-Receiver, Gemini-Node, Dashboard) ohne physische NPU.

```bash
python3 amr/scripts/host_hailo_runner.py --fallback
```

Ohne Hailo-8L NPU oder bei deaktivierter Vision (`use_vision:=False`) laufen Kamera und Dashboard-Stream weiterhin. Die Topics `/vision/detections` und `/vision/semantics` werden dann nicht publiziert. Navigation und SLAM sind davon unabhaengig.

## TTS-Sprachausgabe (optional)

Der `tts_speak_node` subscribt `/vision/semantics` und spricht die Gemini-Analyse ueber den Lautsprecher (MAX98357A I2S) aus. Die Synthese erfolgt via Google Text-to-Speech (gTTS, Cloud) auf Deutsch mit Wiedergabe ueber mpg123. Rate-Limiting: maximal alle 10 Sekunden.

Aktivierung:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_camera:=True use_vision:=True use_audio:=True use_tts:=True
```

Abhaengigkeiten im Docker-Image: `gTTS` (pip), `mpg123` (apt). Internetzugang erforderlich fuer gTTS-Cloud-Synthese.

## Gemini-Modell

Der `gemini_semantic_node` verwendet standardmaessig das Modell `gemini-3.1-flash-lite-preview`. Das Modell kann per ROS2-Parameter geaendert werden:

```bash
ros2 run my_bot gemini_semantic_node --ros-args -p model:=gemini-2.0-flash
```

Die Umgebungsvariable `GEMINI_API_KEY` muss gesetzt sein (wird ueber `docker-compose.yml` an den Container durchgereicht).
