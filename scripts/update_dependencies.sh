#!/bin/bash
# Speicherort: /home/pi/amr-projekt/scripts/update_dependencies.sh

PROJECT_DIR="/home/pi/amr-projekt"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

echo "=== Interaktive Projekt-Aktualisierung: ${DATE} ==="

# 1. Node.js (Dashboard)
echo "--- [1/6] Node.js Paketprüfung (npm) ---"
if [ -d "${PROJECT_DIR}/dashboard" ]; then
    cd "${PROJECT_DIR}/dashboard" || exit
    npm outdated
    read -p "Sollen die Node.js-Pakete aktualisiert werden? (y/j/n): " choice_npm
    if [[ "$choice_npm" == "y" || "$choice_npm" == "j" ]]; then
        echo "> Führe Aktualisierung (npm update & audit fix) aus..."
        npm update
        npm audit fix
    else
        echo "> Node.js-Aktualisierung übersprungen."
    fi
else
    echo "Fehler: Verzeichnis dashboard nicht gefunden."
fi

# 2. Python (Werkzeuge + esptool)
echo "--- [2/6] Python Paketprüfung (pip) ---"
pip list --outdated --break-system-packages 2>/dev/null | grep -E 'mypy|ruff|esptool' || echo "Keine veralteten Python-Pakete (mypy, ruff, esptool) gefunden."
if command -v esptool &>/dev/null; then
    ESPTOOL_VER=$(esptool version 2>&1 | grep -oP 'v\S+' | head -1)
    echo "esptool: ${ESPTOOL_VER}"
fi
read -p "Sollen mypy, ruff und esptool aktualisiert werden? (y/j/n): " choice_pip
if [[ "$choice_pip" == "y" || "$choice_pip" == "j" ]]; then
    echo "> Führe Python-Aktualisierung aus..."
    pip install --upgrade --break-system-packages ruff mypy esptool
else
    echo "> Python-Aktualisierung übersprungen."
fi

# 3. PlatformIO / ESP32-S3 Toolchain
echo "--- [3/6] PlatformIO / ESP32-S3 Toolchain ---"
if command -v pio &>/dev/null; then
    echo "PlatformIO Core: $(pio --version 2>&1 | grep -oP '[0-9]+\.[0-9]+\.[0-9]+')"
    echo ""
    echo "Drive-Node:"
    cd "${PROJECT_DIR}/amr/mcu_firmware/drive_node" && pio pkg outdated 2>&1 | tail -5
    echo ""
    echo "Sensor-Node:"
    cd "${PROJECT_DIR}/amr/mcu_firmware/sensor_node" && pio pkg outdated 2>&1 | tail -5
    echo ""
    read -p "Sollen PlatformIO-Pakete (Plattform, Toolchain, Frameworks) aktualisiert werden? (y/j/n): " choice_pio
    if [[ "$choice_pio" == "y" || "$choice_pio" == "j" ]]; then
        echo "> Aktualisiere Drive-Node..."
        cd "${PROJECT_DIR}/amr/mcu_firmware/drive_node" && pio pkg update
        echo "> Aktualisiere Sensor-Node..."
        cd "${PROJECT_DIR}/amr/mcu_firmware/sensor_node" && pio pkg update
        echo "> Aktualisiere PlatformIO Core..."
        pio upgrade
    else
        echo "> PlatformIO-Aktualisierung übersprungen."
    fi
else
    echo "PlatformIO ist nicht installiert."
fi

# 4. Docker Engine und Compose
echo "--- [4/6] Docker Versionsprüfung ---"
if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version 2>&1)
    echo "Installiert: ${DOCKER_VER}"
    read -p "Soll Docker aktualisiert werden (apt upgrade)? (y/j/n): " choice_docker
    if [[ "$choice_docker" == "y" || "$choice_docker" == "j" ]]; then
        echo "> Führe Docker-Aktualisierung aus..."
        sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        echo "> Docker-Aktualisierung übersprungen."
    fi
else
    echo "Docker ist nicht installiert."
fi

# 5. ROS2 Docker-Image neu bauen
echo "--- [5/6] ROS2 Docker-Image (amr-ros2-humble) ---"
if [ -d "${PROJECT_DIR}/amr/docker" ]; then
    CURRENT_IMAGE=$(docker images amr-ros2-humble:latest --format '{{.CreatedSince}}' 2>/dev/null)
    if [ -n "${CURRENT_IMAGE}" ]; then
        echo "Aktuelles Image erstellt: ${CURRENT_IMAGE}"
    else
        echo "Kein lokales Image vorhanden."
    fi
    read -p "Soll das ROS2-Image neu gebaut werden (docker compose build --pull)? (y/j/n): " choice_image
    if [[ "$choice_image" == "y" || "$choice_image" == "j" ]]; then
        echo "> Baue ROS2-Image mit aktuellem Basis-Image neu (kann 15-20 Min dauern)..."
        cd "${PROJECT_DIR}/amr/docker" || exit
        docker compose build --pull
    else
        echo "> Docker-Image-Build übersprungen."
    fi
else
    echo "Fehler: Verzeichnis amr/docker nicht gefunden."
fi

# 6. Zusammenfassung
echo "--- [6/6] Versionszusammenfassung ---"
echo "Node.js:     $(node --version 2>/dev/null || echo 'nicht installiert')"
echo "npm:         $(npm --version 2>/dev/null || echo 'nicht installiert')"
echo "Python:      $(python3 --version 2>/dev/null)"
echo "ruff:        $(ruff version 2>/dev/null || echo 'nicht installiert')"
echo "mypy:        $(mypy --version 2>/dev/null || echo 'nicht installiert')"
echo "esptool:     $(esptool version 2>&1 | grep -oP 'v\S+' | head -1 || echo 'nicht installiert')"
echo "PlatformIO:  $(pio --version 2>&1 | grep -oP '[0-9]+\.[0-9]+\.[0-9]+' || echo 'nicht installiert')"
echo "espressif32: $(pio pkg list -d "${PROJECT_DIR}/amr/mcu_firmware/drive_node" 2>/dev/null | grep espressif32 | awk '{print $2}')"
echo "Docker:      $(docker --version 2>/dev/null | grep -oP '[0-9]+\.[0-9]+\.[0-9]+')"
echo "ROS2-Image:  $(docker images amr-ros2-humble:latest --format '{{.CreatedSince}}' 2>/dev/null || echo 'nicht vorhanden')"

echo "=== Aktualisierungslauf beendet ==="
