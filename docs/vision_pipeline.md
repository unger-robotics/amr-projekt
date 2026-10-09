---
description: >-
  Hybrid-UDP-Architektur fuer Kamera, Hailo-8L-Inferenz und
  semantische Auswertung mit Gemini Cloud.
---

# Vision-Pipeline

## Zweck

Dokumentation fuer Kamera, optionale Hailo-Inferenz und semantische Auswertung.

## Architektur: Hybride UDP-Bruecke

Die Vision-Pipeline nutzt eine UDP-Bruecke, weil der host-seitig installierte NPU-Treiber (`hailort`) an die Python-3.13-Umgebung von Raspberry Pi OS Trixie gebunden ist und sich nicht in den Docker-Container (Python 3.10, ROS2 Humble) uebertragen laesst. Daher laeuft die Inferenz auf dem Host und die ROS2-Integration im Docker-Container. Der Hailo-8L verbraucht typisch 1,5 W (maximal 6,6 W); die Stromversorgung erfolgt ueber das M.2 HAT+.

## Datenfluss

```
Host (camera-v4l2-bridge.service):
  IMX296 (CSI) -> rpicam-vid (MJPEG, 640x480, 15 fps) -> ffmpeg
      |
      v  /dev/video10 (v4l2loopback, YUYV422)

Docker (Python 3.10, ROS2 Humble):
  v4l2_camera_node (use_camera)
      |
      v  /camera/image_raw (ROS2 Topic)
      |
      v
  dashboard_bridge (use_dashboard)
      |
      v  MJPEG-Stream https://127.0.0.1:8082/stream (ohne Zertifikate HTTP)

Host (Python 3.13):
  host_hailo_runner.py (Hailo-8L YOLOv8 @ 5 Hz)
      |
      v  UDP 127.0.0.1:5005 (JSON-Detektionen)

Docker (Python 3.10, ROS2 Humble):
  hailo_udp_receiver_node (empfaengt UDP:5005, use_vision)
      |
      v  /vision/detections (ROS2 Topic)
      |
      v
  gemini_semantic_node (Gemini Cloud API, Standard gemini-2.5-flash)
      + /range/front (Ultraschall, optional)
      + /scan (LiDAR 360°, optional)
      |
      v  /vision/semantics (ROS2 Topic, inkl. sensor_fusion Metadaten)
      |
      v
  tts_speak_node (gTTS Cloud → mpg123 → MAX98357A Lautsprecher, optional)
```

## Komponenten

| Komponente | Laufzeitumgebung | Aufgabe |
|---|---|---|
| `camera-v4l2-bridge.service` | Host (systemd) | Liest die CSI-Kamera IMX296 mit `rpicam-vid` und schreibt die Bilder ueber `ffmpeg` nach `/dev/video10` (v4l2loopback) |
| `v4l2_camera_node` | Docker (ROS2) | Liest `/dev/video10`, publiziert `/camera/image_raw` |
| `dashboard_bridge` | Docker (ROS2) | MJPEG-Stream auf Port 8082 (HTTPS, ohne Zertifikate HTTP) |
| `host_hailo_runner.py` | Host (Python 3.13) | YOLOv8-Inferenz via Hailo-8L NPU, sendet Detektionen per UDP |
| `hailo_udp_receiver_node` | Docker (ROS2) | Empfaengt UDP-JSON, publiziert `/vision/detections` |
| `gemini_semantic_node` | Docker (ROS2) | Semantische Auswertung via Gemini Cloud mit Sensorfusion (Ultraschall + LiDAR), publiziert `/vision/semantics` |
| `tts_speak_node` | Docker (ROS2) | Spricht Gemini-Semantik via gTTS (Cloud, Deutsch) + mpg123 ueber MAX98357A Lautsprecher |

## Ports

| Port | Protokoll | Zweck |
|---|---|---|
| 5005 | UDP | Hailo-Detektionen (Host → Docker) |
| 8082 | HTTPS (ohne Zertifikate HTTP) | MJPEG-Kamerastream |
| 9090 | WSS (ohne Zertifikate WS) | Dashboard-Telemetrie |
| 5173 | HTTPS (mkcert, ohne Zertifikate kein Start) | Vite-Entwicklungsserver (Dashboard) |

`dashboard_bridge` nutzt die mkcert-Zertifikate aus `dashboard/` und faellt ohne sie auf HTTP bzw. WS zurueck.

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

## Detektions-JSON

`host_hailo_runner.py` sendet je verarbeitetem Bild ein JSON-Paket per UDP. `hailo_udp_receiver_node` publiziert es mit allen Feldern als `std_msgs/String` auf `/vision/detections`. Die Nachricht hat keinen Header; eine typisierte Nachricht folgt in K7 mit `amr_chain_msgs`.

| Feld | Typ, Einheit | Bedeutung | Vorhanden |
|---|---|---|---|
| `timestamp` | float, s | Host-Uhr (`time.time()`) beim Versand, nach Inferenz und Nachverarbeitung | immer |
| `capture_time` | float, s | Host-Uhr direkt nach `cap.read()`, also Entnahme des Bildes im Runner | Hailo-Modus (seit K7-V) |
| `seq` | int | Laufende Nummer der gesendeten Pakete, ab 0 je Start des Runners | Hailo- und Fallback-Modus (seit K7-V) |
| `inference_ms` | float, ms | Dauer der Hailo-Inferenz; im Fallback-Modus 0,0 | immer |
| `detections` | Liste | Je Objekt `class_id`, `label` (deutsch), `confidence` und `bbox` [x1, y1, x2, y2] in Pixeln des um 180° gedrehten Bildes; optional `reclassified` und `original_labels` | immer |

`timestamp - capture_time` ist die Verarbeitungszeit im Runner. `capture_time` ist dagegen keine Sensorzeit:

- Der Runner liest den MJPEG-Strom mit hoechstens 5 Hz und ohne Puffersteuerung; der Server sendet ungedrosselt. `cap.read()` liefert deshalb das aelteste gepufferte Bild.
- Die Stempel von `/camera/image_raw` gehen beim JPEG-Schritt der `dashboard_bridge` verloren.
- `capture_time` ist damit eine Obergrenze des Bildzeitpunkts (Phase-0-Bericht K7-V, B-V7).

Die Konsumenten werten die neuen Felder nicht aus: `dashboard_bridge` uebernimmt nur `detections` und `inference_ms`, `gemini_semantic_node` nur `detections`. `hailo_inference_node` (nicht im Launch) liefert nur `timestamp`, und zwar in ROS-Zeit. Die Auswertung von `capture_time` und `seq` in Aufnahmen uebernimmt `bag_check` (siehe [Referenzaufnahmen](ros2/referenz-bags.md)).

## TTS-Sprachausgabe (optional)

Der `tts_speak_node` subscribt `/vision/semantics` und spricht die Gemini-Analyse ueber den Lautsprecher (MAX98357A I2S) aus. Die Synthese erfolgt via Google Text-to-Speech (gTTS, Cloud) auf Deutsch mit Wiedergabe ueber mpg123. Rate-Limiting: maximal alle 10 Sekunden.

Aktivierung:

```bash
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_camera:=True use_vision:=True use_audio:=True use_tts:=True
```

Abhaengigkeiten im Docker-Image: `gTTS` (pip), `mpg123` (apt). Internetzugang erforderlich fuer gTTS-Cloud-Synthese.

## Gemini-Modell

Der `gemini_semantic_node` verwendet standardmaessig das Modell `gemini-2.5-flash`. Die Umgebungsvariable `GEMINI_VISION_MODEL` aus der Host-Umgebung oder aus `amr/docker/.env` legt einen anderen Standardwert fest; der ROS2-Parameter `model` ueberschreibt ihn:

```bash
ros2 run my_bot gemini_semantic_node --ros-args -p model:=gemini-2.5-flash
```

Die Kontingente des Free-Tiers (Anfragen pro Minute und pro Tag) haengen vom Modell ab.

Die Umgebungsvariable `GEMINI_API_KEY` muss gesetzt sein (wird ueber `docker-compose.yml` an den Container durchgereicht).

## Sensorfusion

Der `gemini_semantic_node` bezieht optional Ultraschall- und LiDAR-Daten in die Gemini-Anfrage ein:

| Topic | Typ | Quelle | Verwendung |
|---|---|---|---|
| `/range/front` | `sensor_msgs/Range` | Sensor-Node (micro-ROS) | Frontale Distanz im Prompt |
| `/scan` | `sensor_msgs/LaserScan` | RPLiDAR A1 | 4-Sektor-Zusammenfassung (vorne/links/rechts/hinten) im Prompt |

Die Subscriptions nutzen Best-Effort QoS (depth=1). Sensordaten aelter als 5 Sekunden werden als veraltet verworfen. Falls die Topics nicht publiziert werden, arbeitet der Knoten ohne Fusion weiter.

Die Antwort auf `/vision/semantics` enthaelt ein `sensor_fusion`-Objekt mit:
- `sources`: Liste aktiver Quellen (z.B. `["kamera", "hailo", "ultraschall", "lidar"]`)
- `ultrasonic_m`: Frontale Ultraschall-Distanz in Metern (oder `null`)
- `lidar_sectors`: Naechstes Hindernis pro Sektor (`min_m`, `frei`-Flag)

Das Dashboard zeigt die aktiven Fusionsquellen als Tags und die Sensorwerte im Semantik-Panel an.
