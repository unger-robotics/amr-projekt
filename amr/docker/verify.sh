#!/bin/bash
# =============================================================================
# Verifikationsskript fuer das ROS2 Humble Docker-Setup
#
# Prueft: ROS2-Distribution, Pakete, Device-Zugriff, Workspace-Build, Nodes
# Verwendung: ./verify.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PASS=0
FAIL=0
WARN=0

pass() { echo "[PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "[FAIL] $1"; FAIL=$((FAIL + 1)); }
warn() { echo "[WARN] $1"; WARN=$((WARN + 1)); }

echo "=== ROS2 Humble Docker Verifikation ==="
echo ""

# ---------------------------------------------------------------------------
# 1. Image vorhanden?
# ---------------------------------------------------------------------------
echo "--- 1. Docker Image ---"
if docker images amr-ros2-humble:latest --format '{{.Repository}}' | grep -q amr-ros2-humble; then
    SIZE=$(docker images amr-ros2-humble:latest --format '{{.Size}}')
    pass "Image amr-ros2-humble:latest vorhanden ($SIZE)"
else
    fail "Image amr-ros2-humble:latest nicht gefunden. Erst 'docker compose build' ausfuehren."
    echo ""
    echo "=== Abbruch: Image fehlt ==="
    exit 1
fi
echo ""

# Hilfsfunktion: Befehl im Container ausfuehren
run_in_container() {
    docker compose run --rm -T amr "$@" 2>/dev/null
}

# ---------------------------------------------------------------------------
# 2. ROS2 Distribution
# ---------------------------------------------------------------------------
echo "--- 2. ROS2 Distribution ---"
DISTRO=$(run_in_container bash -c 'echo $ROS_DISTRO')
if [ "$DISTRO" = "humble" ]; then
    pass "ROS_DISTRO = humble"
else
    fail "ROS_DISTRO = '$DISTRO' (erwartet: humble)"
fi
echo ""

# ---------------------------------------------------------------------------
# 3. ROS2-Pakete pruefen
# ---------------------------------------------------------------------------
echo "--- 3. ROS2-Pakete ---"
PACKAGES="nav2_bringup slam_toolbox rplidar_ros cv_bridge micro_ros_agent"
COLCON_CHECK="colcon"

for PKG in $PACKAGES; do
    if run_in_container ros2 pkg prefix "$PKG" > /dev/null 2>&1; then
        pass "Paket '$PKG' installiert"
    else
        fail "Paket '$PKG' NICHT gefunden"
    fi
done

# colcon separat pruefen (kein ROS2-Paket)
if run_in_container which colcon > /dev/null 2>&1; then
    pass "colcon verfuegbar"
else
    fail "colcon NICHT gefunden"
fi
echo ""

# ---------------------------------------------------------------------------
# 4. Serial-Device Zugriff
# ---------------------------------------------------------------------------
echo "--- 4. Device-Zugriff ---"
if [ -e /dev/ttyACM0 ] || [ -e /dev/amr_esp32 ]; then
    DEV=$([ -e /dev/amr_esp32 ] && echo "/dev/amr_esp32" || echo "/dev/ttyACM0")
    if run_in_container test -r "$DEV" 2>/dev/null; then
        pass "Serial-Device $DEV lesbar im Container"
    else
        warn "Serial-Device $DEV existiert, aber Zugriff im Container unklar"
    fi
else
    warn "Kein ESP32 angeschlossen (/dev/ttyACM0 oder /dev/amr_esp32 nicht vorhanden)"
fi
echo ""

# ---------------------------------------------------------------------------
# 4b. Kamera-Bridge (optional)
# ---------------------------------------------------------------------------
echo "--- 4b. Kamera-Bridge ---"
if lsmod | grep -q v4l2loopback; then
    pass "v4l2loopback-Modul geladen"
else
    warn "v4l2loopback-Modul nicht geladen (Kamera-Bridge inaktiv)"
fi

if [ -e /dev/video10 ]; then
    pass "/dev/video10 vorhanden"
else
    warn "/dev/video10 nicht vorhanden (v4l2loopback nicht konfiguriert oder Modul nicht geladen)"
fi

if systemctl is-active --quiet camera-v4l2-bridge.service 2>/dev/null; then
    pass "camera-v4l2-bridge.service aktiv"
else
    warn "camera-v4l2-bridge.service nicht aktiv (Kamera-Stream laeuft nicht)"
fi

if [ -e /dev/video10 ]; then
    if run_in_container test -r /dev/video10 2>/dev/null; then
        pass "/dev/video10 im Container lesbar"
    else
        warn "/dev/video10 im Container nicht lesbar"
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# 5. Workspace bauen
# ---------------------------------------------------------------------------
echo "--- 5. Workspace Build ---"
echo "    Baue my_bot Paket (kann einige Sekunden dauern)..."
if run_in_container bash -c 'cd /ros2_ws && colcon build --packages-select my_bot --symlink-install' > /dev/null 2>&1; then
    pass "colcon build --packages-select my_bot erfolgreich"
else
    fail "colcon build fuer my_bot fehlgeschlagen"
fi
echo ""

# ---------------------------------------------------------------------------
# 6. Nodes pruefen
# ---------------------------------------------------------------------------
echo "--- 6. Paket-Executables ---"
NODES=$(run_in_container bash -c 'source /ros2_ws/install/setup.bash && ros2 pkg executables my_bot' 2>/dev/null)
NODE_COUNT=$(echo "$NODES" | grep -c "my_bot" || true)

if [ "$NODE_COUNT" -ge 9 ]; then
    pass "my_bot hat $NODE_COUNT Executables (erwartet: >= 9)"
    echo "$NODES" | sed 's/^/    /'
else
    fail "my_bot hat nur $NODE_COUNT Executables (erwartet: >= 9)"
    if [ -n "$NODES" ]; then
        echo "$NODES" | sed 's/^/    /'
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# Zusammenfassung
# ---------------------------------------------------------------------------
echo "==========================================="
echo "  PASS: $PASS | FAIL: $FAIL | WARN: $WARN"
echo "==========================================="

if [ "$FAIL" -gt 0 ]; then
    echo "Verifikation FEHLGESCHLAGEN ($FAIL Fehler)"
    exit 1
else
    echo "Verifikation BESTANDEN"
    exit 0
fi
