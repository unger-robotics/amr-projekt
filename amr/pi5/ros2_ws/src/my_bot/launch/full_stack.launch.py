#!/usr/bin/env python3
"""
Kombiniertes ROS2 Launch-File fuer den vollstaendigen AMR-Stack.

Startet:
  1. micro-ROS Agent (Serial Transport, UART zu XIAO ESP32-S3)
  2. SLAM Toolbox (async Online-Modus)
  3. Nav2 Navigation Stack (RPP Controller, NavFn Planer)
  4. RViz2 (optional)

Verwendung:
  ros2 launch my_bot full_stack.launch.py
  ros2 launch my_bot full_stack.launch.py use_rviz:=False
  ros2 launch my_bot full_stack.launch.py serial_port:=/dev/ttyUSB0
  ros2 launch my_bot full_stack.launch.py use_slam:=False  # Nur Navigation mit bestehender Karte
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
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
        default_value="True",
        description="RViz2 Visualisierung starten",
    )
    declare_serial_port = DeclareLaunchArgument(
        "serial_port",
        default_value="/dev/ttyACM0",
        description="Serieller Port fuer micro-ROS Agent (USB-CDC zum XIAO ESP32-S3)",
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
            "0.05",
            "3.14159",
            "0.0",
            "0.0",
            "base_link",
            "laser",
        ],
    )

    # --- 1. micro-ROS Agent (Serial Transport) ---
    # Verbindet XIAO ESP32-S3 ueber UART/USB-CDC mit dem ROS2-Graphen.
    # Publiziert /odom, subscribt /cmd_vel.
    micro_ros_agent = ExecuteProcess(
        cmd=[
            "ros2",
            "run",
            "micro_ros_agent",
            "micro_ros_agent",
            "serial",
            "--dev",
            LaunchConfiguration("serial_port"),
            "-b",
            "115200",
        ],
        name="micro_ros_agent",
        output="screen",
    )

    # --- 1b. Odom-zu-TF Bridge ---
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
        parameters=[LaunchConfiguration("slam_params_file")],
        condition=IfCondition(LaunchConfiguration("use_slam")),
    )

    # --- 3. Nav2 Navigation Stack ---
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav2_bringup_share, "launch", "navigation_launch.py"])
        ),
        launch_arguments={
            "params_file": LaunchConfiguration("params_file"),
            "use_sim_time": "False",
        }.items(),
        condition=IfCondition(LaunchConfiguration("use_nav")),
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
                "camera_info_url": "",
            }
        ],
        remappings=[
            ("image_raw", "/camera/image_raw"),
            ("camera_info", "/camera/camera_info"),
        ],
        condition=IfCondition(LaunchConfiguration("use_camera")),
    )

    # --- 6. Statischer TF: base_link → camera_link ---
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

    # --- 7. Dashboard Bridge (WebSocket + MJPEG, optional) ---
    dashboard_node = Node(
        package="my_bot",
        executable="dashboard_bridge",
        name="dashboard_bridge",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_dashboard")),
    )

    # --- 8. Vision Pipeline (Hailo UDP Receiver + Gemini, optional) ---
    # Hailo-8 Inference laeuft auf dem Host (host_hailo_runner.py),
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

    return LaunchDescription(
        [
            # Launch Arguments
            declare_use_slam,
            declare_use_nav,
            declare_use_rviz,
            declare_serial_port,
            declare_params_file,
            declare_slam_params_file,
            declare_use_camera,
            declare_camera_device,
            declare_use_dashboard,
            declare_use_vision,
            # Nodes / Prozesse
            rplidar_node,
            laser_tf,
            micro_ros_agent,
            odom_to_tf_node,
            slam_toolbox_node,
            nav2_launch,
            rviz_node,
            camera_node,
            camera_tf,
            dashboard_node,
            hailo_udp_receiver_node,
            gemini_semantic_node,
        ]
    )
