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

# Kamera-Bridge pruefen wenn use_camera:=True in den Argumenten
if echo "$*" | grep -qi 'use_camera:=true'; then
    if ! systemctl is-active --quiet camera-v4l2-bridge.service 2>/dev/null; then
        echo "WARNUNG: camera-v4l2-bridge.service laeuft nicht."
        echo "  Starte mit: sudo systemctl start camera-v4l2-bridge.service"
        if [ ! -e /dev/video10 ]; then
            echo "  /dev/video10 fehlt — Kamera-Node wird fehlschlagen."
            read -p "  Trotzdem fortfahren? [y/N] " -n 1 -r
            echo
            [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
        fi
    elif [ ! -e /dev/video10 ]; then
        echo "WARNUNG: camera-v4l2-bridge.service aktiv, aber /dev/video10 fehlt."
        echo "  Pruefen: journalctl -u camera-v4l2-bridge.service -f"
    else
        echo "Kamera-Bridge aktiv (/dev/video10 bereit)"
    fi
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

# --- Container sicherstellen (up -d statt run) ---
# docker compose up -d wendet devices:, device_cgroup_rules: und volumes: korrekt an.
# docker compose run ignoriert devices:-Mappings, was zu "Serial port not found" fuehrt.
# Belegte Ports freigeben (Dashboard, WebSocket, MJPEG)
_cleanup_ports() {
    for port in 5173 5174 8082 9090; do
        fuser -k "$port/tcp" 2>/dev/null || true
    done
}

_ensure_container() {
    if ! docker ps --format '{{.Names}}' | grep -q '^amr_ros2$'; then
        echo "Container amr_ros2 wird gestartet..."
        _cleanup_ports
        docker compose up -d
        # udev-Symlinks existieren im Container nicht — manuell anlegen
        sleep 1
        _setup_serial_symlinks
    fi
}

# Serielle Symlinks im Container anlegen (Host-udev greift dort nicht)
_setup_serial_symlinks() {
    for dev in /dev/amr_drive /dev/amr_sensor; do
        if [ -L "$dev" ]; then
            target=$(readlink -f "$dev")
            target_name=$(basename "$target")
            docker exec amr_ros2 ln -sf "/dev/$target_name" "$dev" 2>/dev/null || true
        fi
    done
}

# Normaler Modus: Container starten, Befehl ausfuehren
_ensure_container
# Symlinks bei jedem Aufruf aktualisieren (USB-Zuordnung kann sich aendern)
_setup_serial_symlinks

# ALSA-Devices synchronisieren (/dev/snd Bind-Mount erfasst spaet erkannte
# USB-Audio-Geraete wie den ReSpeaker nicht automatisch)
for snd_dev in /dev/snd/*; do
    name=$(basename "$snd_dev")
    if ! docker exec amr_ros2 test -e "/dev/snd/$name" 2>/dev/null; then
        major=$(stat -c '%t' "$snd_dev" 2>/dev/null) || continue
        minor=$(stat -c '%T' "$snd_dev" 2>/dev/null) || continue
        major_dec=$((16#$major))
        minor_dec=$((16#$minor))
        docker exec amr_ros2 mknod "/dev/snd/$name" c "$major_dec" "$minor_dec" 2>/dev/null
        docker exec amr_ros2 chmod 666 "/dev/snd/$name" 2>/dev/null
    fi
done

# TTY-Flags: -it nur wenn stdin ein Terminal ist
DOCKER_FLAGS="-i"
if [ -t 0 ]; then
    DOCKER_FLAGS="-it"
fi

if [ $# -eq 0 ]; then
    echo "Oeffne interaktive Shell im Container..."
    exec docker exec $DOCKER_FLAGS amr_ros2 /entrypoint.sh bash
else
    echo "Starte im Container: $*"
    exec docker exec $DOCKER_FLAGS amr_ros2 /entrypoint.sh "$@"
fi
