#!/usr/bin/env python3
"""
Kombiniertes ROS2 Launch-File fuer den vollstaendigen AMR-Stack.

Zwei-Node-Architektur: Drive-Node (Motoren, Odometrie, PID, LED)
und Sensor-Node (Ultraschall HC-SR04, Cliff-Erkennung MH-B, IMU MPU6050, Batterie INA260, Servo PCA9685) auf separaten ESP32-S3.

Startet:
  1. micro-ROS Agent Drive (Serial Transport, UART zu Drive ESP32-S3)
  2. micro-ROS Agent Sensor (Serial Transport, UART zu Sensor ESP32-S3, optional)
  3. SLAM Toolbox (async Online-Modus)
  4. Nav2 Navigation Stack (RPP Controller, NavFn Planer)
  5. RViz2 (optional)

Verwendung:
  ros2 launch my_bot full_stack.launch.py
  ros2 launch my_bot full_stack.launch.py use_rviz:=False
  ros2 launch my_bot full_stack.launch.py drive_serial_port:=/dev/ttyACM0
  ros2 launch my_bot full_stack.launch.py use_sensors:=False  # Ohne Sensor-Node
  ros2 launch my_bot full_stack.launch.py use_slam:=False  # Nur Navigation mit bestehender Karte
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node, SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # --- Paket-Pfade ---
    my_bot_share = FindPackageShare("my_bot")
    nav2_bringup_share = FindPackageShare("nav2_bringup")

    # --- Konfigurations-Dateien ---
    default_nav2_params = PathJoinSubstitution([my_bot_share, "config", "nav2_params.yaml"])
    default_slam_params = PathJoinSubstitution(
        [my_bot_share, "config", "mapper_params_online_async.yaml"]
    )

    # --- Launch Arguments ---
    declare_use_slam = DeclareLaunchArgument(
        "use_slam",
        default_value="True",
        description="SLAM Toolbox starten (async Modus)",
    )
    declare_use_nav = DeclareLaunchArgument(
        "use_nav",
        default_value="True",
        description="Nav2 Navigation Stack starten",
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz",
        default_value="False",
        description="RViz2 Visualisierung starten (erfordert X11-Display)",
    )
    declare_drive_serial_port = DeclareLaunchArgument(
        "drive_serial_port",
        default_value="/dev/amr_drive",
        description="Serieller Port fuer micro-ROS Agent Drive-Node (USB-CDC zum XIAO ESP32-S3)",
    )
    declare_sensor_serial_port = DeclareLaunchArgument(
        "sensor_serial_port",
        default_value="/dev/amr_sensor",
        description="Serieller Port fuer micro-ROS Agent Sensor-Node (USB-CDC zum XIAO ESP32-S3)",
    )
    declare_use_sensors = DeclareLaunchArgument(
        "use_sensors",
        default_value="True",
        description="Sensor-Node ESP32-S3 (Ultraschall HC-SR04, Cliff MH-B) starten",
    )
    declare_params_file = DeclareLaunchArgument(
        "params_file",
        default_value=default_nav2_params,
        description="Pfad zur Nav2 Parameter-YAML-Datei",
    )
    declare_slam_params_file = DeclareLaunchArgument(
        "slam_params_file",
        default_value=default_slam_params,
        description="Pfad zur SLAM Toolbox Parameter-YAML-Datei",
    )
    declare_use_camera = DeclareLaunchArgument(
        "use_camera",
        default_value="False",
        description="Kamera-Node starten (v4l2_camera_node fuer ArUco-Docking)",
    )
    declare_camera_device = DeclareLaunchArgument(
        "camera_device",
        default_value="/dev/video10",
        description="Video-Device fuer die Kamera (v4l2loopback-Bridge)",
    )
    declare_use_dashboard = DeclareLaunchArgument(
        "use_dashboard",
        default_value="False",
        description="Web-Dashboard starten (WebSocket :9090, MJPEG :8082)",
    )
    declare_use_vision = DeclareLaunchArgument(
        "use_vision",
        default_value="False",
        description="Vision-Pipeline starten (Hailo UDP Receiver + Gemini Semantik). "
        "host_hailo_runner.py separat auf dem Host starten!",
    )
    declare_use_cliff_safety = DeclareLaunchArgument(
        "use_cliff_safety",
        default_value="True",
        description="Cliff-Safety cmd_vel-Multiplexer",
    )
    declare_use_audio = DeclareLaunchArgument(
        "use_audio",
        default_value="False",
        description="Audio-Feedback-Node (MAX98357A I2S-Verstaerker)",
    )
    declare_use_can = DeclareLaunchArgument(
        "use_can",
        default_value="False",
        description="CAN-to-ROS2 Bridge: Sensor-Topics via SocketCAN statt micro-ROS "
        "(IMU 50 Hz, kein XRCE-DDS Overhead). Erfordert Sensor-Node CAN-Transceiver.",
    )
    declare_use_respeaker = DeclareLaunchArgument(
        "use_respeaker",
        default_value="False",
        description="ReSpeaker Mic Array v2.0 DoA/VAD-Node (USB, pyusb)",
    )
    declare_use_tts = DeclareLaunchArgument(
        "use_tts",
        default_value="False",
        description="TTS-Sprachausgabe fuer Gemini-Semantik (gTTS + mpg123)",
    )
    declare_use_voice = DeclareLaunchArgument(
        "use_voice",
        default_value="False",
        description="Sprachsteuerung via ReSpeaker + lokales Whisper STT "
        "(erfordert use_respeaker:=True)",
    )

    # --- 0a. RPLIDAR A1 (immer aktiv) ---
    rplidar_node = Node(
        package="rplidar_ros",
        executable="rplidar_node",
        name="rplidar_node",
        output="screen",
        parameters=[
            {
                "serial_port": "/dev/ttyUSB0",
                "serial_baudrate": 115200,
                "frame_id": "laser",
                "inverted": False,
                "angle_compensate": True,
                "scan_frequency": 7.0,
            }
        ],
    )

    # --- 0b. Statischer TF: base_link → laser (180° Yaw) ---
    laser_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="laser_tf_publisher",
        arguments=[
            "0.10",
            "0.0",
            "0.235",
            "3.14159",
            "0.0",
            "0.0",
            "base_link",
            "laser",
        ],
    )

    # --- 1a. micro-ROS Agent Drive (Serial Transport) ---
    # Verbindet Drive ESP32-S3 ueber UART/USB-CDC mit dem ROS2-Graphen.
    # Publiziert /odom. Subscribt /cmd_vel, /hardware_cmd (x=Motor-Limit, z=LED-PWM).
    micro_ros_agent_drive = ExecuteProcess(
        cmd=[
            "ros2",
            "run",
            "micro_ros_agent",
            "micro_ros_agent",
            "serial",
            "--dev",
            LaunchConfiguration("drive_serial_port"),
            "-b",
            "921600",
        ],
        name="micro_ros_agent_drive",
        output="screen",
    )

    # --- 1b. micro-ROS Agent Sensor (Serial Transport, optional) ---
    # Verbindet Sensor ESP32-S3 ueber UART/USB-CDC mit dem ROS2-Graphen.
    # Publiziert /range/front, /cliff, /imu, /battery. Subscribt /servo_cmd, /hardware_cmd (y=Servo-Speed).
    micro_ros_agent_sensor = ExecuteProcess(
        cmd=[
            "ros2",
            "run",
            "micro_ros_agent",
            "micro_ros_agent",
            "serial",
            "--dev",
            LaunchConfiguration("sensor_serial_port"),
            "-b",
            "921600",
        ],
        name="micro_ros_agent_sensor",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_sensors")),
    )

    # --- 1c. Odom-zu-TF Bridge ---
    # micro-ROS publiziert nur /odom (Odometry), aber keinen TF.
    # Dieser Node erzeugt den dynamischen TF odom -> base_link.
    odom_to_tf_node = Node(
        package="my_bot",
        executable="odom_to_tf",
        name="odom_to_tf",
        output="screen",
    )

    # --- 2. SLAM Toolbox (async Online-Modus) ---
    slam_toolbox_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[LaunchConfiguration("slam_params_file"), {"minimum_laser_range": 0.2}],
        condition=IfCondition(LaunchConfiguration("use_slam")),
    )

    # --- 3. Nav2 Navigation Stack ---
    # Nav2 MIT Cliff-Safety: SetRemap lenkt /cmd_vel -> /nav_cmd_vel um.
    # cliff_safety_node subscribt /nav_cmd_vel + /dashboard_cmd_vel und
    # publiziert gefilterte Befehle auf /cmd_vel.
    nav2_with_remap = GroupAction(
        actions=[
            SetRemap(src="/cmd_vel", dst="/nav_cmd_vel"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([nav2_bringup_share, "launch", "navigation_launch.py"])
                ),
                launch_arguments={
                    "params_file": LaunchConfiguration("params_file"),
                    "use_sim_time": "False",
                }.items(),
            ),
        ],
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("use_cliff_safety"),
                    "' == 'True' and '",
                    LaunchConfiguration("use_nav"),
                    "' == 'True'",
                ]
            )
        ),
    )

    # Nav2 OHNE Remap (Rueckwaertskompatibel)
    nav2_without_remap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav2_bringup_share, "launch", "navigation_launch.py"])
        ),
        launch_arguments={
            "params_file": LaunchConfiguration("params_file"),
            "use_sim_time": "False",
        }.items(),
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("use_cliff_safety"),
                    "' == 'False' and '",
                    LaunchConfiguration("use_nav"),
                    "' == 'True'",
                ]
            )
        ),
    )

    # --- 4. RViz2 (optional) ---
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            PathJoinSubstitution([nav2_bringup_share, "rviz", "nav2_default_view.rviz"]),
        ],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )

    # --- 5. Kamera (v4l2_camera_node, optional) ---
    camera_node = Node(
        package="v4l2_camera",
        executable="v4l2_camera_node",
        name="v4l2_camera_node",
        output="screen",
        parameters=[
            {
                "video_device": LaunchConfiguration("camera_device"),
                "image_size": [640, 480],
                "pixel_format": "YUYV",
                "output_encoding": "bgr8",
                "camera_frame_id": "camera_link",
                "camera_info_url": "file:///ros2_ws/src/my_bot/config/amr_camera.yaml",
            }
        ],
        remappings=[
            ("image_raw", "/camera/image_raw"),
            ("camera_info", "/camera/camera_info"),
        ],
        condition=IfCondition(LaunchConfiguration("use_camera")),
    )

    # --- 6a. Statischer TF: base_link → camera_link ---
    camera_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="camera_tf_publisher",
        arguments=[
            "0.10",
            "0.0",
            "0.08",
            "0.0",
            "0.0",
            "0.0",
            "base_link",
            "camera_link",
        ],
        condition=IfCondition(LaunchConfiguration("use_camera")),
    )

    # --- 6b. Statischer TF: base_link → ultrasonic_link ---
    ultrasonic_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="ultrasonic_tf_publisher",
        arguments=[
            "0.15",
            "0.0",
            "0.05",
            "0.0",
            "0.0",
            "0.0",
            "base_link",
            "ultrasonic_link",
        ],
        condition=IfCondition(LaunchConfiguration("use_sensors")),
    )

    # --- 7. Dashboard Bridge (WebSocket + MJPEG, optional) ---
    # Dashboard MIT Cliff-Safety Remapping (cmd_vel → dashboard_cmd_vel)
    dashboard_node_with_remap = Node(
        package="my_bot",
        executable="dashboard_bridge",
        name="dashboard_bridge",
        output="screen",
        remappings=[("/cmd_vel", "/dashboard_cmd_vel")],
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("use_cliff_safety"),
                    "' == 'True' and '",
                    LaunchConfiguration("use_dashboard"),
                    "' == 'True'",
                ]
            )
        ),
    )

    # Dashboard OHNE Remap
    dashboard_node_without_remap = Node(
        package="my_bot",
        executable="dashboard_bridge",
        name="dashboard_bridge",
        output="screen",
        condition=IfCondition(
            PythonExpression(
                [
                    "'",
                    LaunchConfiguration("use_cliff_safety"),
                    "' == 'False' and '",
                    LaunchConfiguration("use_dashboard"),
                    "' == 'True'",
                ]
            )
        ),
    )

    # --- 8. Vision Pipeline (Hailo-8L UDP Receiver + Gemini, optional) ---
    # Hailo-8L Inference laeuft auf dem Host (host_hailo_runner.py),
    # Ergebnisse kommen via UDP 127.0.0.1:5005 in den Container.
    hailo_udp_receiver_node = Node(
        package="my_bot",
        executable="hailo_udp_receiver_node",
        name="hailo_udp_receiver",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_vision")),
    )
    gemini_semantic_node = Node(
        package="my_bot",
        executable="gemini_semantic_node",
        name="gemini_semantic_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_vision")),
    )

    # --- 9. Cliff-Safety Multiplexer (optional, default an) ---
    cliff_safety_node = Node(
        package="my_bot",
        executable="cliff_safety_node",
        name="cliff_safety_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_cliff_safety")),
    )

    # --- 10. Audio-Feedback (MAX98357A I2S-Verstaerker, optional) ---
    audio_feedback_node = Node(
        package="my_bot",
        executable="audio_feedback_node",
        name="audio_feedback_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_audio")),
    )

    # --- 11. CAN-to-ROS2 Bridge (SocketCAN, optional) ---
    # Publiziert Sensor-Topics (/imu, /cliff, /range/front, /battery,
    # /battery_shutdown) via CAN statt micro-ROS Serial.
    # micro-ROS Sensor-Agent bleibt aktiv fuer Subscriber
    # (/servo_cmd, /hardware_cmd, /odom).
    can_bridge_node = Node(
        package="my_bot",
        executable="can_bridge_node",
        name="can_bridge_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_can")),
    )

    # --- 12. TTS-Sprachausgabe (gTTS + mpg123, optional) ---
    tts_speak_node = Node(
        package="my_bot",
        executable="tts_speak_node",
        name="tts_speak_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_tts")),
    )

    # --- 13. ReSpeaker DoA/VAD (USB Mic Array, optional) ---
    respeaker_doa_node = Node(
        package="my_bot",
        executable="respeaker_doa_node",
        name="respeaker_doa_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_respeaker")),
    )

    # --- 14. Sprachsteuerung (ReSpeaker + lokales Whisper STT, optional) ---
    # audio_device explizit setzen, da /proc/asound im Container den
    # ReSpeaker nicht enumeriert (Device-Node via Bind-Mount vorhanden)
    voice_command_node = Node(
        package="my_bot",
        executable="voice_command_node",
        name="voice_command_node",
        output="screen",
        parameters=[
            {
                "audio_device": "plughw:CARD=ArrayUAC10,DEV=0",
                "whisper_model": "base",
                "use_wakeword": True,
                "wakeword_model": "hey_jarvis_v0.1",
                "wakeword_threshold": 0.5,
            }
        ],
        condition=IfCondition(LaunchConfiguration("use_voice")),
    )

    return LaunchDescription(
        [
            # Launch Arguments
            declare_use_slam,
            declare_use_nav,
            declare_use_rviz,
            declare_drive_serial_port,
            declare_sensor_serial_port,
            declare_use_sensors,
            declare_params_file,
            declare_slam_params_file,
            declare_use_camera,
            declare_camera_device,
            declare_use_dashboard,
            declare_use_vision,
            declare_use_cliff_safety,
            declare_use_audio,
            declare_use_can,
            declare_use_tts,
            declare_use_respeaker,
            declare_use_voice,
            # Nodes / Prozesse
            rplidar_node,
            laser_tf,
            micro_ros_agent_drive,
            micro_ros_agent_sensor,
            odom_to_tf_node,
            slam_toolbox_node,
            nav2_with_remap,
            nav2_without_remap,
            rviz_node,
            camera_node,
            camera_tf,
            ultrasonic_tf,
            dashboard_node_with_remap,
            dashboard_node_without_remap,
            hailo_udp_receiver_node,
            gemini_semantic_node,
            cliff_safety_node,
            audio_feedback_node,
            can_bridge_node,
            tts_speak_node,
            respeaker_doa_node,
            voice_command_node,
        ]
    )
