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

# ALSA-softvol-Konfiguration fuer Software-Lautstaerkeregelung (MAX98357A hat keinen HW-Mixer)
if [ ! -f /etc/asound.conf ]; then
    cat > /etc/asound.conf <<'ALSA_EOF'
pcm.softvol {
    type softvol
    slave.pcm "plughw:CARD=sndrpihifiberry"
    control.name "SoftMaster"
    control.card 0
}

pcm.!default {
    type plug
    slave.pcm "softvol"
}

ctl.!default {
    type hw
    card 0
}
ALSA_EOF
fi

exec "$@"
