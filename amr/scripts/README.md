# AMR Scripts

Alle Skripte werden via Symlinks aus `my_bot/my_bot/` referenziert und sind als `ros2 run my_bot <name>` ausfuehrbar (sofern ROS2-Knoten). Dateien NICHT verschieben — Symlinks und Docker-Dual-Mount haengen von der flachen Struktur ab.

## Runtime-Knoten (via full_stack.launch.py)

| Datei | Beschreibung |
|---|---|
| `odom_to_tf.py` | Bruecke /odom → TF (odom → base_link) |
| `dashboard_bridge.py` | WebSocket (9090) + MJPEG (8082) Bridge fuer Dashboard |
| `hailo_udp_receiver_node.py` | UDP-Empfaenger fuer Hailo-8 YOLOv8-Detektionen (Port 5005) |
| `gemini_semantic_node.py` | Gemini Cloud semantische Analyse mit Sensorfusion (Ultraschall + LiDAR + Kamera, `/vision/semantics`, nur bei `/vision/enable`=True) |
| `hailo_inference_node.py` | (Legacy) Direkter Hailo-8 Zugriff, ersetzt durch UDP-Pattern |
| `cliff_safety_node.py` | cmd_vel-Multiplexer mit Cliff-Notbremse (subscribt /cliff, muxed Nav2+Dashboard) |
| `audio_feedback_node.py` | WAV-Wiedergabe via aplay/MAX98357A (subscribt /audio/play) |
| `can_bridge_node.py` | CAN-Bus Bridge: Empfaengt CAN-Frames und publiziert auf Standard-Sensor-Topics (/imu, /range/front, /cliff, /battery), fensterbasierte Heartbeat-Drift-Erkennung (30 s) |
| `respeaker_doa_node.py` | ReSpeaker DoA/VAD (USB, `/sound_direction`, `/is_voice`) |
| `tts_speak_node.py` | Text-to-Speech Sprachausgabe fuer Gemini-Semantik (gTTS + mpg123, Rate-Limiting 10 s) |
| `voice_command_node.py` | Sprachsteuerung: ReSpeaker VAD → lokales faster-whisper STT → Regex-Intent-Parsing → `/voice/command` + `/voice/text` (offline, Wake-Word, Energy-Gate) |
| `aruco_docking.py` | ArUco-Marker-Detektion + Docking-Navigation (erfordert `use_camera:=True`) |

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
| `sensor_test.py` | Ultraschall (HC-SR04) + Cliff (MH-B) Konnektivitaet, Genauigkeit, Sicherheit |
| `nav_square_test.py` | Quadrat-Navigationstest (1 m x 1 m) via /cmd_vel mit Vektornavigation und Sensorfusion (Odom/IMU/Map) |
| `cliff_latency_test.py` | End-to-End Cliff-Safety-Latenztest (0.2 m/s Vorwaertsfahrt, misst Zeit bis Motorstopp) |
| `dashboard_latency_test.py` | Phase-5-Validierung: Dashboard-Latenz, Telemetrie-Vollstaendigkeit, Deadman-Timer, Audio, Notaus |

## Standalone-Utilities (kein ROS2 erforderlich)

| Datei | Beschreibung |
|---|---|
| `amr_utils.py` | Shared-Modul: Kinematik-Konstanten, Quaternionen, Farbcodes |
| `hardware_info/` | Hardware-Report-Paket (aufrufbar via `python -m hardware_info`): System, Peripherie, Software, Projekt-Info |
| `pre_flight_check.py` | Interaktive Hardware-Checkliste vor Testfahrt |
| `umbmark_analysis.py` | UMBmark-Auswertung (numpy/matplotlib) |
| `validation_report.py` | Gesamt-Report aus JSON-Ergebnissen aggregieren |
| `camera_calibration.py` | Kamerakalibrierung ueber MJPEG-Stream mit Schachbrettmuster (OpenCV, ROS2-YAML-Export) |
| `generate_checkerboard.py` | Schachbrettmuster-Generator als PNG fuer Kamerakalibrierung (9x6, A4-optimiert) |

## Host-Only (ausserhalb Docker, Python 3.13)

| Datei | Beschreibung |
|---|---|
| `host_hailo_runner.py` | Hailo-8 YOLOv8-Inference, sendet Detektionen via UDP an Container |
