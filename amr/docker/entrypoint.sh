#!/bin/bash
# =============================================================================
# Entrypoint fuer ROS2 Humble Docker Container
# Sourced ROS2, optionale Workspaces und fuehrt den uebergebenen Befehl aus.
# =============================================================================

set -e

# ROS2 Humble Basis
source /opt/ros/humble/setup.bash

# micro-ROS Agent Workspace (nur bei Source-Build vorhanden)
if [ -f /opt/microros_ws/install/setup.bash ]; then
    source /opt/microros_ws/install/setup.bash
fi

# Projekt-Workspace (nach colcon build)
if [ -f /ros2_ws/install/setup.bash ]; then
    source /ros2_ws/install/setup.bash
fi

exec "$@"
