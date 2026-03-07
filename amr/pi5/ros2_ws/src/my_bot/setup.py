import os
from glob import glob

from setuptools import setup

package_name = "my_bot"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "sounds"), glob("sounds/*.wav")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Jan",
    maintainer_email="student@university.de",
    description="AMR navigation and control package",
    license="MIT",
    entry_points={
        "console_scripts": [
            "aruco_docking = my_bot.aruco_docking:main",
            "encoder_test = my_bot.encoder_test:main",
            "motor_test = my_bot.motor_test:main",
            "pid_tuning = my_bot.pid_tuning:main",
            "kinematic_test = my_bot.kinematic_test:main",
            "slam_validation = my_bot.slam_validation:main",
            "nav_test = my_bot.nav_test:main",
            "docking_test = my_bot.docking_test:main",
            "imu_test = my_bot.imu_test:main",
            "rotation_test = my_bot.rotation_test:main",
            "straight_drive_test = my_bot.straight_drive_test:main",
            "rplidar_test = my_bot.rplidar_test:main",
            "serial_latency_logger = my_bot.serial_latency_logger:main",
            "odom_to_tf = my_bot.odom_to_tf:main",
            "dashboard_bridge = my_bot.dashboard_bridge:main",
            "hailo_inference_node = my_bot.hailo_inference_node:main",
            "hailo_udp_receiver_node = my_bot.hailo_udp_receiver_node:main",
            "gemini_semantic_node = my_bot.gemini_semantic_node:main",
            "cliff_safety_node = my_bot.cliff_safety_node:main",
            "audio_feedback_node = my_bot.audio_feedback_node:main",
            "can_bridge_node = my_bot.can_bridge_node:main",
            "can_validation_test = my_bot.can_validation_test:main",
            "respeaker_doa_node = my_bot.respeaker_doa_node:main",
        ],
    },
)
