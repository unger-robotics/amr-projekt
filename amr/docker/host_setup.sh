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
# 4. Kamera-Setup (v4l2loopback-Bridge fuer IMX296 Global Shutter)
# ---------------------------------------------------------------------------
echo "--- Kamera-Setup (v4l2loopback-Bridge) ---"

# 4a. v4l2loopback-dkms installieren
if dpkg -l v4l2loopback-dkms 2>/dev/null | grep -q '^ii'; then
    echo "[OK] v4l2loopback-dkms bereits installiert"
else
    echo "Installiere v4l2loopback-dkms..."
    sudo apt-get update
    sudo apt-get install -y v4l2loopback-dkms
    echo "[OK] v4l2loopback-dkms installiert"
fi

# 4b. ffmpeg installieren (fuer die Bridge-Pipeline)
if command -v ffmpeg &> /dev/null; then
    echo "[OK] ffmpeg bereits vorhanden"
else
    echo "Installiere ffmpeg..."
    sudo apt-get install -y ffmpeg
    echo "[OK] ffmpeg installiert"
fi

# 4c. Modprobe-Konfiguration (video_nr=10 vermeidet Kollision mit rp1-cfe 19-35)
MODPROBE_CONF="/etc/modprobe.d/v4l2loopback.conf"
if [ -f "$MODPROBE_CONF" ]; then
    echo "[OK] modprobe-Config existiert: $MODPROBE_CONF"
else
    echo "Erstelle $MODPROBE_CONF ..."
    sudo tee "$MODPROBE_CONF" > /dev/null << 'MODPROBE_EOF'
options v4l2loopback video_nr=10 card_label="AMR_Camera" exclusive_caps=1
MODPROBE_EOF
    echo "[OK] modprobe-Config erstellt"
fi

# 4d. Boot-Laden sicherstellen
MODULES_CONF="/etc/modules-load.d/v4l2loopback.conf"
if [ -f "$MODULES_CONF" ]; then
    echo "[OK] Boot-Laden konfiguriert: $MODULES_CONF"
else
    echo "Erstelle $MODULES_CONF ..."
    echo "v4l2loopback" | sudo tee "$MODULES_CONF" > /dev/null
    echo "[OK] v4l2loopback wird beim Boot geladen"
fi

# 4e. Modul sofort laden falls nicht geladen
if lsmod | grep -q v4l2loopback; then
    echo "[OK] v4l2loopback-Modul geladen"
else
    echo "Lade v4l2loopback-Modul..."
    sudo modprobe v4l2loopback video_nr=10 card_label="AMR_Camera" exclusive_caps=1
    echo "[OK] v4l2loopback-Modul geladen"
fi

# 4f. /dev/video10 pruefen
if [ -e /dev/video10 ]; then
    echo "[OK] /dev/video10 vorhanden"
else
    echo "[WARNUNG] /dev/video10 nicht vorhanden — Modul evtl. mit anderen Optionen geladen."
    echo "  Fix: sudo modprobe -r v4l2loopback && sudo modprobe v4l2loopback video_nr=10 card_label=AMR_Camera exclusive_caps=1"
fi

# 4g. IMX296 Kamera-Erkennung pruefen
echo ""
echo "--- IMX296 Kamera-Erkennung ---"
RPICAM_CMD=""
if command -v rpicam-hello &> /dev/null; then
    RPICAM_CMD="rpicam-hello"
elif command -v libcamera-hello &> /dev/null; then
    RPICAM_CMD="libcamera-hello"
fi

if [ -n "$RPICAM_CMD" ]; then
    if $RPICAM_CMD --list-cameras 2>&1 | grep -qi "imx296"; then
        echo "[OK] IMX296 Kamera erkannt"
    else
        echo "[WARNUNG] IMX296 Kamera NICHT erkannt."
        echo "  Troubleshooting:"
        echo "    1. CSI-Kabel pruefen (22-pin Mini → 15-pin Adapter, fest eingesteckt)"
        echo "    2. dtoverlay=imx296 in /boot/firmware/config.txt unter [all] eintragen"
        echo "    3. sudo reboot"
        echo "    4. I2C-Error -121 = Kabel-/Kontaktproblem"
    fi
else
    echo "[INFO] Weder rpicam-hello noch libcamera-hello gefunden."
fi

# 4h. systemd-Service fuer die Kamera-Bridge installieren
echo ""
echo "--- Kamera-Bridge Service ---"
SERVICE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/camera-v4l2-bridge.service"
SERVICE_DST="/etc/systemd/system/camera-v4l2-bridge.service"

if [ -f "$SERVICE_SRC" ]; then
    if [ -f "$SERVICE_DST" ] && cmp -s "$SERVICE_SRC" "$SERVICE_DST"; then
        echo "[OK] Service-Datei bereits installiert und aktuell"
    else
        sudo cp "$SERVICE_SRC" "$SERVICE_DST"
        sudo systemctl daemon-reload
        echo "[OK] Service-Datei installiert: $SERVICE_DST"
    fi
    sudo systemctl enable camera-v4l2-bridge.service 2>/dev/null
    echo "[OK] camera-v4l2-bridge.service aktiviert (Start beim Boot)"
    echo "[INFO] Service manuell starten: sudo systemctl start camera-v4l2-bridge.service"
    echo "[INFO] Service-Status: sudo systemctl status camera-v4l2-bridge.service"
else
    echo "[WARNUNG] Service-Datei nicht gefunden: $SERVICE_SRC"
    echo "  Erwartet im selben Verzeichnis wie host_setup.sh"
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
