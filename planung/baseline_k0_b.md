# Baseline K0 - Lauf B: CAN-Bus (passiv)

Aufnahmedatum: 2026-09-02T21:03:08
Messdauer: 120.0 s
Modus: can
Git-Commit: dad529a
Git-Tag: baseline-k0

Rein passiv aufgezeichnet: kein Publisher, kein CAN-Sendevorgang, keine
Bewegung.

---

## CAN-Frames

Interface: `can0` | Error-Frames: 0

| CAN-ID | DLC | Frames | Rate (Hz) |
|---|---|---|---|
| `0x110` | 4 | 1200 | 10.0 |
| `0x120` | 1 | 2401 | 20.01 |
| `0x130` | 8 | 6001 | 50.0 |
| `0x131` | 4 | 6001 | 50.0 |
| `0x140` | 6 | 240 | 2.0 |
| `0x1F0` | 8 | 120 | 1.0 |
| `0x200` | 8 | 2290 | 19.08 |
| `0x201` | 8 | 2400 | 20.0 |
| `0x210` | 8 | 1200 | 10.0 |
| `0x220` | 4 | 1200 | 10.0 |
| `0x2F0` | 2 | 120 | 1.0 |

Frames gesamt: 23173 | Verschiedene IDs: 11

| Interface-Zustand | Wert |
|---|---|
| operstate | up |
| can_state | ERROR-ACTIVE |
| bitrate | 1000000 |
| sample_point | 0.750 |
| restarts | 0 |
| bus_errors | 0 |
| arbitration_lost | 0 |
| error_warning | 0 |
| error_passive | 0 |
| bus_off | 0 |

| Kernelzaehler | Absolut (seit Interface-Start) | Delta im Messfenster |
|---|---|---|
| rx_dropped | 907769 | 0 |
| rx_errors | 63374 | 1200 |
| rx_packets | 1138484 | 23175 |
| tx_errors | 0 | 0 |
| tx_packets | 0 | 0 |

`rx_dropped` waechst, solange kein Prozess die Frames aus der
SocketCAN-Queue abholt; das ist erwartetes Verhalten und kein Busfehler.
Massgeblich fuer die Busqualitaet sind `rx_errors`, `bus_errors` und der
CAN-Zustand.

## Systemstand

| Konfiguration | Version |
|---|---|
| `config_drive.h` | 4.0.0 |
| `config_sensors.h` | 3.0.0 |

### Launch-Argumente (full_stack.launch.py)

| Argument | Default |
|---|---|
| `use_slam` | `True` |
| `use_nav` | `True` |
| `use_rviz` | `False` |
| `drive_serial_port` | `/dev/amr_drive` |
| `sensor_serial_port` | `/dev/amr_sensor` |
| `use_sensors` | `True` |
| `params_file` | `default_nav2_params` |
| `slam_params_file` | `default_slam_params` |
| `use_camera` | `False` |
| `camera_device` | `/dev/video10` |
| `use_dashboard` | `False` |
| `use_vision` | `False` |
| `use_cliff_safety` | `True` |
| `use_audio` | `False` |
| `use_can` | `False` |
| `use_respeaker` | `False` |
| `use_tts` | `False` |
| `use_voice` | `False` |

### Entry-Points (setup.py)

Anzahl: 30

`aruco_docking`, `audio_feedback_node`, `baseline_snapshot`, `can_bridge_node`, `can_validation_test`, `cliff_latency_test`, `cliff_safety_node`, `dashboard_bridge`, `dashboard_latency_test`, `docking_test`, `encoder_test`, `gemini_semantic_node`, `hailo_inference_node`, `hailo_udp_receiver_node`, `imu_test`, `kinematic_test`, `motor_test`, `nav_square_test`, `nav_test`, `odom_to_tf`, `pid_tuning`, `respeaker_doa_node`, `rotation_test`, `rplidar_test`, `sensor_test`, `serial_latency_logger`, `slam_validation`, `straight_drive_test`, `tts_speak_node`, `voice_command_node`
