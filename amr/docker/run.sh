#!/bin/bash
# =============================================================================
# Convenience-Wrapper fuer den ROS2 Docker Container
#
# Verwendung:
#   ./run.sh                     # Interaktive Shell
#   ./run.sh bash                # Interaktive Shell (explizit)
#   ./run.sh ros2 topic list     # Einzelbefehl ausfuehren
#   ./run.sh ros2 launch my_bot full_stack.launch.py
#   ./run.sh colcon build --packages-select my_bot --symlink-install
#
# Zweites Terminal in laufendem Container:
#   ./run.sh exec bash
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# X11-Zugriff fuer Docker erlauben (falls Display vorhanden)
if [ -n "$DISPLAY" ]; then
    xhost +local:docker 2>/dev/null || true
fi

# Sonderfall: "exec" oeffnet eine Shell im bereits laufenden Container
if [ "$1" = "exec" ]; then
    shift
    if [ $# -eq 0 ]; then
        set -- bash
    fi
    echo "Oeffne Shell im laufenden Container..."
    exec docker exec -it amr_ros2 /entrypoint.sh "$@"
fi

# Normaler Modus: Container starten mit uebergebenem Befehl
if [ $# -eq 0 ]; then
    echo "Starte ROS2 Humble Container (interaktive Shell)..."
    exec docker compose run --rm amr
else
    echo "Starte ROS2 Humble Container: $*"
    exec docker compose run --rm amr "$@"
fi
