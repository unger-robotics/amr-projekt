# AMR Scripts

Alle Skripte werden via Symlinks aus `my_bot/my_bot/` referenziert und sind als `ros2 run my_bot <name>` ausfuehrbar (sofern ROS2-Nodes). Dateien NICHT verschieben — Symlinks und Docker-Dual-Mount haengen von der flachen Struktur ab.

## Runtime-Nodes (via full_stack.launch.py)

| Datei | Beschreibung |
|---|---|
| `dashboard_bridge.py` | WebSocket (9090) + MJPEG (8082) Bridge fuer Web-Dashboard |
| `hailo_udp_receiver_node.py` | UDP-Empfaenger fuer Hailo-8 YOLOv8-Detektionen (Port 5005) |
| `gemini_semantic_node.py` | Gemini Cloud semantische Analyse (`/vision/semantics`) |
| `hailo_inference_node.py` | (Legacy) Direkter Hailo-8 Zugriff, ersetzt durch UDP-Pattern |
| `cliff_safety_node.py` | cmd_vel-Multiplexer mit Cliff-Notbremse (subscribt /cliff, muxed Nav2+Dashboard) |
| `audio_feedback_node.py` | WAV-Wiedergabe via aplay/MAX98357A (subscribt /audio/play) |
| `can_bridge_node.py` | CAN-Bus Diagnostik-Bridge (MCP2515/SocketCAN → /diagnostics/can) |
| `respeaker_doa_node.py` | ReSpeaker DoA/VAD (USB, `/sound_direction`, `/is_voice`) |

## Validierungstests (ros2 run my_bot \<name\>)

| Datei | Beschreibung |
|---|---|
| `encoder_test.py` | Encoder-Kalibrierung (10-Umdrehungen-Test) |
| `motor_test.py` | Motor-Deadzone und Richtungstest |
| `pid_tuning.py` | PID-Sprungantwort-Analyse |
| `kinematic_test.py` | Geradeaus-/Dreh-/Kreisfahrt-Verifikation |
| `imu_test.py` | Gyro-Drift und Accelerometer-Bias (60s statisch) |
| `rotation_test.py` | Closed-Loop 360-Grad-Drehung mit IMU-Feedback |
| `straight_drive_test.py` | Geradeausfahrt mit IMU-Heading-Korrektur |
| `slam_validation.py` | ATE-Berechnung und TF-Ketten-Check |
| `rplidar_test.py` | RPLidar A1 Scan-Rate, Datenqualitaet, TF-Check (5 min) |
| `nav_test.py` | 4-Waypoint-Navigation mit Positionsfehler-Messung |
| `docking_test.py` | 10-Versuch ArUco-Docking-Test |
| `serial_latency_logger.py` | Serial-Transport-Latenz ESP32-Pi (CSV-Export) |
| `can_validation_test.py` | CAN-Bus Frame-Rate, Heartbeat, Daten-Dekodierung (30s, JSON) |

## Standalone-Utilities (kein ROS2 erforderlich)

| Datei | Beschreibung |
|---|---|
| `amr_utils.py` | Shared-Modul: Kinematik-Konstanten, Quaternionen, Farbcodes |
| `hardware_info.py` | Hardware-Report-Generator (Zeitstempel-Markdown) |
| `pre_flight_check.py` | Interaktive Hardware-Checkliste vor Testfahrt |
| `umbmark_analysis.py` | UMBmark-Auswertung (numpy/matplotlib) |
| `validation_report.py` | Gesamt-Report aus JSON-Ergebnissen aggregieren |

## Host-Only (ausserhalb Docker, Python 3.13)

| Datei | Beschreibung |
|---|---|
| `host_hailo_runner.py` | Hailo-8 YOLOv8-Inference, sendet Detektionen via UDP an Container |
