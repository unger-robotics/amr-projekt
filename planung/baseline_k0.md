# Baseline K0 - Ist-Zustand vor dem Umbau

Git-Commit: dad529a
Git-Tag: baseline-k0
Zusammengefuehrt: 2026-09-02T21:03:56

Die Aufnahme erfolgte in zwei getrennten passiven Laeufen. Damit ist die
Herkunft jedes ROS-Topics eindeutig: Lauf A misst ausschliesslich den
heutigen USB/micro-ROS-Referenzpfad, Lauf B ausschliesslich den
bestehenden CAN-Bus. Weder wurde Firmware geaendert oder geflasht, noch
wurde ein Fahrbefehl gesendet.

| Lauf | Gegenstand | Konfiguration | Dauer |
|---|---|---|---|
| A | ROS-2-Topics und TF-Baum | `use_can:=False`, USB/micro-ROS | 120.0 s |
| B | CAN-Frames und Fehlerstatus | passives Mithoeren, CAN nicht als ROS-Quelle | 120.0 s |

---

## Lauf A - ROS-2-Referenzpfad (USB/micro-ROS)

Aufnahmedatum: 2026-09-02T18:58:59 | Dauer: 120.0 s

| Topic | Typ | Pub | Sub | Nachrichten | Beobachtet (s) | Rate (Hz) |
|---|---|---|---|---|---|---|
| `/audio/play` | `std_msgs/msg/String` | 1 | 0 | 0 | 128.0 | 0.0 |
| `/backup/_action/feedback` | `nav2_msgs/action/BackUp_FeedbackMessage` | 1 | 2 | 0 | 128.0 | 0.0 |
| `/backup/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 2 | 0 | 128.0 | 0.0 |
| `/battery` | `sensor_msgs/msg/BatteryState` | 1 | 0 | 256 | 127.9 | 2.0 |
| `/battery_shutdown` | `std_msgs/msg/Bool` | 1 | 1 | 0 | 127.9 | 0.0 |
| `/behavior_server/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.9 | 0.0 |
| `/behavior_tree_log` | `nav2_msgs/msg/BehaviorTreeLog` | 2 | 0 | 0 | 127.7 | 0.0 |
| `/bond` | `bond/msg/Status` | 14 | 14 | 17823 | 127.9 | 139.34 |
| `/bt_navigator/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/cliff` | `std_msgs/msg/Bool` | 1 | 1 | 2028 | 127.9 | 15.86 |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 2 | 1 | 2558 | 127.9 | 20.0 |
| `/compute_path_through_poses/_action/feedback` | `nav2_msgs/action/ComputePathThroughPoses_FeedbackMessage` | 1 | 1 | 0 | 127.9 | 0.0 |
| `/compute_path_through_poses/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 1 | 0 | 127.9 | 0.0 |
| `/compute_path_to_pose/_action/feedback` | `nav2_msgs/action/ComputePathToPose_FeedbackMessage` | 1 | 1 | 0 | 127.9 | 0.0 |
| `/compute_path_to_pose/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 1 | 0 | 127.9 | 0.0 |
| `/controller_server/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.9 | 0.0 |
| `/dashboard_cmd_vel` | `geometry_msgs/msg/Twist` | 0 | 1 | 0 | 127.9 | 0.0 |
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | 1 | 0 | 127 | 127.9 | 0.99 |
| `/drive_on_heading/_action/feedback` | `nav2_msgs/action/DriveOnHeading_FeedbackMessage` | 1 | 0 | 0 | 127.9 | 0.0 |
| `/drive_on_heading/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 0 | 0 | 127.9 | 0.0 |
| `/emergency_stop` | `std_msgs/msg/Bool` | 0 | 1 | 0 | 127.9 | 0.0 |
| `/follow_path/_action/feedback` | `nav2_msgs/action/FollowPath_FeedbackMessage` | 1 | 2 | 0 | 127.9 | 0.0 |
| `/follow_path/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 2 | 0 | 127.9 | 0.0 |
| `/follow_waypoints/_action/feedback` | `nav2_msgs/action/FollowWaypoints_FeedbackMessage` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/follow_waypoints/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/global_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/global_costmap/costmap_raw` | `nav2_msgs/msg/Costmap` | 1 | 1 | 81 | 127.8 | 0.63 |
| `/global_costmap/costmap_updates` | `map_msgs/msg/OccupancyGridUpdate` | 1 | 0 | 81 | 127.8 | 0.63 |
| `/global_costmap/footprint` | `geometry_msgs/msg/Polygon` | 0 | 1 | 0 | 127.2 | 0.0 |
| `/global_costmap/global_costmap/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/global_costmap/published_footprint` | `geometry_msgs/msg/PolygonStamped` | 1 | 1 | 127 | 127.8 | 0.99 |
| `/goal_pose` | `geometry_msgs/msg/PoseStamped` | 0 | 1 | 0 | 127.8 | 0.0 |
| `/hardware_cmd` | `geometry_msgs/msg/Point` | 0 | 2 | 0 | 127.8 | 0.0 |
| `/imu` | `sensor_msgs/msg/Imu` | 1 | 0 | 4866 | 127.8 | 38.07 |
| `/local_costmap/clearing_endpoints` | `sensor_msgs/msg/PointCloud2` | 1 | 0 | 633 | 127.8 | 4.95 |
| `/local_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/local_costmap/costmap_raw` | `nav2_msgs/msg/Costmap` | 1 | 1 | 211 | 127.8 | 1.65 |
| `/local_costmap/costmap_updates` | `map_msgs/msg/OccupancyGridUpdate` | 1 | 0 | 211 | 127.8 | 1.65 |
| `/local_costmap/footprint` | `geometry_msgs/msg/Polygon` | 0 | 1 | 0 | 127.2 | 0.0 |
| `/local_costmap/local_costmap/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/local_costmap/published_footprint` | `geometry_msgs/msg/PolygonStamped` | 1 | 1 | 632 | 127.8 | 4.95 |
| `/local_costmap/voxel_grid` | `nav2_msgs/msg/VoxelGrid` | 1 | 0 | 632 | 127.8 | 4.95 |
| `/lookahead_collision_arc` | `nav_msgs/msg/Path` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/lookahead_point` | `geometry_msgs/msg/PointStamped` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/map` | `nav_msgs/msg/OccupancyGrid` | 1 | 2 | 254 | 127.8 | 1.99 |
| `/map_metadata` | `nav_msgs/msg/MapMetaData` | 1 | 0 | 254 | 127.8 | 1.99 |
| `/nav_cmd_vel` | `geometry_msgs/msg/Twist` | 5 | 2 | 0 | 127.8 | 0.0 |
| `/navigate_through_poses/_action/feedback` | `nav2_msgs/action/NavigateThroughPoses_FeedbackMessage` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/navigate_through_poses/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/navigate_to_pose/_action/feedback` | `nav2_msgs/action/NavigateToPose_FeedbackMessage` | 1 | 2 | 0 | 127.8 | 0.0 |
| `/navigate_to_pose/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 2 | 0 | 127.8 | 0.0 |
| `/odom` | `nav_msgs/msg/Odometry` | 1 | 4 | 2536 | 127.8 | 19.85 |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | 20 | 21 | 0 | 127.8 | 0.0 |
| `/plan` | `nav_msgs/msg/Path` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/plan_smoothed` | `nav_msgs/msg/Path` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/planner_server/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/range/front` | `sensor_msgs/msg/Range` | 1 | 3 | 1157 | 127.8 | 9.06 |
| `/received_global_plan` | `nav_msgs/msg/Path` | 1 | 0 | 0 | 127.8 | 0.0 |
| `/rosout` | `rcl_interfaces/msg/Log` | 25 | 0 | 6 | 127.8 | 0.05 |
| `/scan` | `sensor_msgs/msg/LaserScan` | 1 | 3 | 959 | 127.7 | 7.51 |
| `/servo_cmd` | `geometry_msgs/msg/Point` | 0 | 1 | 0 | 127.7 | 0.0 |
| `/slam_toolbox/feedback` | `visualization_msgs/msg/InteractiveMarkerFeedback` | 0 | 1 | 0 | 127.7 | 0.0 |
| `/slam_toolbox/graph_visualization` | `visualization_msgs/msg/MarkerArray` | 1 | 0 | 254 | 127.7 | 1.99 |
| `/slam_toolbox/scan_visualization` | `sensor_msgs/msg/LaserScan` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/slam_toolbox/update` | `visualization_msgs/msg/InteractiveMarkerUpdate` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/smooth_path/_action/feedback` | `nav2_msgs/action/SmoothPath_FeedbackMessage` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/smooth_path/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/smoother_server/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/speed_limit` | `nav2_msgs/msg/SpeedLimit` | 0 | 1 | 0 | 127.2 | 0.0 |
| `/spin/_action/feedback` | `nav2_msgs/action/Spin_FeedbackMessage` | 1 | 2 | 0 | 127.7 | 0.0 |
| `/spin/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 2 | 0 | 127.7 | 0.0 |
| `/tf` | `tf2_msgs/msg/TFMessage` | 3 | 6 | 5079 | 127.7 | 39.77 |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 2 | 6 | 2 | 127.7 | 0.02 |
| `/velocity_smoother/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.7 | 0.0 |
| `/wait/_action/feedback` | `nav2_msgs/action/Wait_FeedbackMessage` | 1 | 2 | 0 | 127.7 | 0.0 |
| `/wait/_action/status` | `action_msgs/msg/GoalStatusArray` | 1 | 2 | 0 | 127.7 | 0.0 |
| `/waypoint_follower/transition_event` | `lifecycle_msgs/msg/TransitionEvent` | 1 | 0 | 0 | 127.7 | 0.0 |

### TF-Baum (beobachtete Kanten)

| Parent | Child |
|---|---|
| `base_link` | `laser` |
| `base_link` | `ultrasonic_link` |
| `map` | `odom` |
| `odom` | `base_link` |

## Lauf B - CAN-Bus (passiv)

Aufnahmedatum: 2026-09-02T21:03:08 | Dauer: 120.0 s

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

---

Regressionsschwellen und belegte Messwerte der Phasen 1 bis 5:
`planung/baseline_k0_referenzwerte.md`.
