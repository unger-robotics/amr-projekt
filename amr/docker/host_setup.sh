#!/bin/bash
# =============================================================================
# Host-Setup fuer ROS2 Docker auf Raspberry Pi 5 (Debian Trixie)
# Einmalig ausfuehren, dann Neustart oder Re-Login.
# =============================================================================

set -e

echo "=== AMR Docker Host-Setup ==="
echo ""

# ---------------------------------------------------------------------------
# 1. Gruppen-Checks
# ---------------------------------------------------------------------------
echo "--- Gruppen-Zugehoerigkeit pruefen ---"
MISSING_GROUPS=""

for GROUP in docker dialout video; do
    if id -nG "$USER" | grep -qw "$GROUP"; then
        echo "[OK] $USER ist in Gruppe '$GROUP'"
    else
        echo "[FEHLT] $USER ist NICHT in Gruppe '$GROUP'"
        MISSING_GROUPS="$MISSING_GROUPS $GROUP"
    fi
done

if [ -n "$MISSING_GROUPS" ]; then
    echo ""
    echo "Fehlende Gruppen hinzufuegen:"
    for GROUP in $MISSING_GROUPS; do
        echo "  sudo usermod -aG $GROUP $USER"
        sudo usermod -aG "$GROUP" "$USER"
    done
    echo ""
    echo "WICHTIG: Nach dem Hinzufuegen ab- und wieder anmelden (oder 'newgrp docker')."
fi
echo ""

# ---------------------------------------------------------------------------
# 2. udev-Regeln fuer stabile Device-Pfade
# ---------------------------------------------------------------------------
echo "--- udev-Regeln einrichten ---"
UDEV_FILE="/etc/udev/rules.d/99-amr-devices.rules"

if [ -f "$UDEV_FILE" ]; then
    echo "[OK] udev-Regeln existieren bereits: $UDEV_FILE"
else
    echo "Erstelle $UDEV_FILE ..."
    sudo tee "$UDEV_FILE" > /dev/null << 'UDEV_EOF'
# XIAO ESP32-S3 (micro-ROS, USB-CDC)
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", \
  SYMLINK+="amr_esp32", MODE="0666"

# RPLIDAR A1 (CP2102 USB-Serial)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
  SYMLINK+="amr_lidar", MODE="0666"
UDEV_EOF

    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "[OK] udev-Regeln erstellt und aktiviert"
fi
echo ""

# ---------------------------------------------------------------------------
# 3. X11-Display fuer RViz2 im Container
# ---------------------------------------------------------------------------
echo "--- X11-Setup pruefen ---"

# Pruefe ob X11-Server-Pakete vorhanden sind
if ! command -v xauth &> /dev/null; then
    echo "Installiere X11-Pakete (xauth, xhost)..."
    sudo apt-get update
    sudo apt-get install -y x11-xserver-utils xauth
    echo "[OK] X11-Pakete installiert"
else
    echo "[OK] xauth bereits vorhanden"
fi

# Docker-Container Zugriff auf X11 erlauben (nur wenn Display vorhanden)
if [ -n "$DISPLAY" ]; then
    xhost +local:docker 2>/dev/null && \
        echo "[OK] xhost: Docker hat X11-Zugriff" || \
        echo "[WARNUNG] xhost konnte nicht gesetzt werden"
else
    echo "[INFO] Kein DISPLAY gesetzt (TTY-Modus). X11 fuer RViz2 spaeter konfigurieren:"
    echo "  export DISPLAY=:0 && xhost +local:docker"
fi
echo ""

# ---------------------------------------------------------------------------
# 4. Kamera-Modul laden
# ---------------------------------------------------------------------------
echo "--- Kamera-Setup ---"

# bcm2835-v4l2 wird auf neueren Pi-Kernels nicht mehr benoetigt,
# libcamera/v4l2 ist direkt verfuegbar. Trotzdem pruefen.
if ls /dev/video* &> /dev/null; then
    echo "[OK] Kamera-Devices vorhanden:"
    ls -la /dev/video*
else
    echo "[INFO] Keine /dev/video* Devices gefunden."
    echo "  Pruefen: 'rpicam-hello' oder 'libcamera-hello'"
    echo "  Falls noetig: sudo modprobe bcm2835-v4l2"
fi
echo ""

# ---------------------------------------------------------------------------
# 5. Docker pruefen
# ---------------------------------------------------------------------------
echo "--- Docker pruefen ---"
if command -v docker &> /dev/null; then
    echo "[OK] Docker: $(docker --version)"
else
    echo "[FEHLER] Docker nicht installiert!"
    exit 1
fi

if command -v docker compose &> /dev/null 2>&1; then
    echo "[OK] Docker Compose: $(docker compose version)"
else
    echo "[FEHLER] Docker Compose nicht verfuegbar!"
    exit 1
fi

# Pruefe ob Docker-Daemon laeuft
if docker info &> /dev/null; then
    echo "[OK] Docker-Daemon laeuft"
else
    echo "[FEHLER] Docker-Daemon nicht erreichbar. Ist der User in der 'docker'-Gruppe?"
    exit 1
fi
echo ""

# ---------------------------------------------------------------------------
# Zusammenfassung
# ---------------------------------------------------------------------------
echo "=== Host-Setup abgeschlossen ==="
echo ""
echo "Naechste Schritte:"
echo "  cd amr/docker/"
echo "  docker compose build     # Image bauen (~15-20 Min)"
echo "  ./run.sh                 # Container-Shell starten"
if [ -n "$MISSING_GROUPS" ]; then
    echo ""
    echo "ACHTUNG: Bitte zuerst ab- und wieder anmelden (Gruppenrechte)!"
fi
