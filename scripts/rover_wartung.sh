#!/bin/bash
# Speicherort: /home/pi/amr-projekt/scripts/rover_wartung.sh
# AMR-spezifische Systemwartung und Diagnose fuer Raspberry Pi 5
#
# Verwendung:
#   sudo ./scripts/rover_wartung.sh          # Vollstaendiger Wartungslauf
#   sudo ./scripts/rover_wartung.sh --check  # Nur Pruefungen, keine Aenderungen

PROJECT_DIR="/home/pi/amr-projekt"
LOG_FILE="/var/log/rover-wartung.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")
CHECK_ONLY=false

if [[ "$1" == "--check" ]]; then
    CHECK_ONLY=true
fi

log() {
    echo "$1" | tee -a "${LOG_FILE}"
}

log "=== Wartungslauf gestartet: ${DATE} ==="

# -------------------------------------------------------------------------
# 1. Systemuebersicht
# -------------------------------------------------------------------------
log "--- [1/10] Systemuebersicht ---"
log "Hostname:  $(hostname)"
log "Modell:    $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')"
log "Kernel:    $(uname -r)"
log "OS:        $(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME}")"
log "Uptime:    $(uptime -p)"
log "Datum:     ${DATE}"

# -------------------------------------------------------------------------
# 2. EEPROM/Bootloader-Pruefung
# -------------------------------------------------------------------------
log "--- [2/10] EEPROM/Bootloader ---"
EEPROM_OUT=$(rpi-eeprom-update 2>/dev/null)
EEPROM_STATUS=$(echo "$EEPROM_OUT" | head -1)
EEPROM_CURRENT=$(echo "$EEPROM_OUT" | grep "CURRENT" | awk '{print $2, $3, $4, $5, $6, $7}')
EEPROM_LATEST=$(echo "$EEPROM_OUT" | grep "LATEST" | awk '{print $2, $3, $4, $5, $6, $7}')
log "Status:   ${EEPROM_STATUS}"
log "Aktuell:  ${EEPROM_CURRENT}"
log "Neueste:  ${EEPROM_LATEST}"
if echo "$EEPROM_STATUS" | grep -qi "update available"; then
    log "HINWEIS: EEPROM-Update verfuegbar. Ausfuehren mit: sudo rpi-eeprom-update -a && sudo reboot"
fi

# -------------------------------------------------------------------------
# 3. System-Updates (apt)
# -------------------------------------------------------------------------
log "--- [3/10] Systempaket-Aktualisierung ---"
if [ "$CHECK_ONLY" = false ]; then
    apt-get update -y 2>&1 | tail -5 | tee -a "${LOG_FILE}"
    apt-get upgrade -y 2>&1 | tail -5 | tee -a "${LOG_FILE}"
    apt-get autoremove -y 2>&1 | tail -3 | tee -a "${LOG_FILE}"
    apt-get clean
else
    apt-get update -y 2>&1 | tail -5 | tee -a "${LOG_FILE}"
    apt-get -s upgrade 2>&1 | grep -E "upgraded|kept back" | tee -a "${LOG_FILE}"
fi

# -------------------------------------------------------------------------
# 4. Neustart-Pruefung
# -------------------------------------------------------------------------
log "--- [4/10] Neustart-Pruefung ---"
if [ -f /var/run/reboot-required ]; then
    log "ACHTUNG: Ein Systemneustart ist zwingend erforderlich!"
else
    log "OK: Kein Systemneustart notwendig."
fi

# -------------------------------------------------------------------------
# 5. Hardware-Zustand (Temperatur, Throttling, Spannung, Takt)
# -------------------------------------------------------------------------
log "--- [5/10] Hardware-Zustand ---"
TEMP=$(vcgencmd measure_temp 2>/dev/null | grep -oP '[0-9.]+')
THROTTLED=$(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)
CPU_FREQ=$(vcgencmd measure_clock arm 2>/dev/null | awk -F= '{printf "%.0f", $2/1000000}')
GPU_MEM=$(vcgencmd get_mem gpu 2>/dev/null | cut -d= -f2)
VOLT=$(vcgencmd measure_volts core 2>/dev/null | grep -oP '[0-9.]+')

log "CPU-Temperatur: ${TEMP} C"
log "CPU-Takt:       ${CPU_FREQ} MHz"
log "GPU-Speicher:   ${GPU_MEM}"
log "Core-Spannung:  ${VOLT} V"

if [ "$THROTTLED" = "0x0" ]; then
    log "OK: Kein Throttling erkannt."
else
    log "WARNUNG: Throttling-Flags aktiv: ${THROTTLED}"
    # Bit-Dekodierung
    THROTTLE_DEC=$((THROTTLED))
    [ $((THROTTLE_DEC & 0x1)) -ne 0 ]     && log "  - Aktuell unterspannt"
    [ $((THROTTLE_DEC & 0x2)) -ne 0 ]     && log "  - Aktuell ARM-Frequenz begrenzt"
    [ $((THROTTLE_DEC & 0x4)) -ne 0 ]     && log "  - Aktuell gedrosselt"
    [ $((THROTTLE_DEC & 0x10000)) -ne 0 ]  && log "  - Unterspannung aufgetreten (seit Boot)"
    [ $((THROTTLE_DEC & 0x20000)) -ne 0 ]  && log "  - ARM-Frequenzbegrenzung aufgetreten (seit Boot)"
    [ $((THROTTLE_DEC & 0x40000)) -ne 0 ]  && log "  - Drosselung aufgetreten (seit Boot)"
fi

# -------------------------------------------------------------------------
# 6. Speicher (Disk + RAM)
# -------------------------------------------------------------------------
log "--- [6/10] Speicher ---"
DISK_USAGE=$(df / --output=pcent | tail -1 | tr -d ' %')
log "SD-Karte: $(df -h / --output=used,size,pcent | tail -1 | xargs)"
log "Boot:     $(df -h /boot/firmware --output=used,size,pcent | tail -1 | xargs)"
log "RAM:      $(free -h | awk '/^Mem:/{print $3 " / " $2 " (" int($3/$2*100) "%)"}')"
log "Swap:     $(free -h | awk '/^Swap:/{print $3 " / " $2}')"

if [ "$DISK_USAGE" -gt 85 ]; then
    log "WARNUNG: SD-Karte zu ${DISK_USAGE}% belegt!"
fi

# -------------------------------------------------------------------------
# 7. Docker-Zustand
# -------------------------------------------------------------------------
log "--- [7/10] Docker ---"
if command -v docker &>/dev/null; then
    log "Docker: $(docker --version | grep -oP '[0-9]+\.[0-9]+\.[0-9]+')"
    log "Container:"
    docker ps -a --format '  {{.Names}}: {{.Status}}' 2>/dev/null | tee -a "${LOG_FILE}"

    DOCKER_DISK=$(docker system df --format '{{.Type}}\t{{.Size}}\t{{.Reclaimable}}' 2>/dev/null)
    log "Docker-Speicher:"
    echo "${DOCKER_DISK}" | sed 's/^/  /' | tee -a "${LOG_FILE}"

    RECLAIMABLE=$(docker system df --format '{{.Reclaimable}}' 2>/dev/null | head -1 | grep -oP '[0-9.]+')
    if [ -n "$RECLAIMABLE" ] && [ "$(echo "$RECLAIMABLE > 5" | bc 2>/dev/null)" = "1" ]; then
        log "HINWEIS: >5 GB rueckgewinnbar. Aufraeumen mit: docker system prune"
    fi
else
    log "Docker nicht installiert."
fi

# -------------------------------------------------------------------------
# 8. AMR-Services
# -------------------------------------------------------------------------
log "--- [8/10] AMR-Services ---"
SERVICES=(
    "docker.service:Docker Engine"
    "camera-v4l2-bridge.service:Kamera-Bridge (rpicam → /dev/video10)"
    "hailort.service:Hailo-8L NPU Runtime"
)

for entry in "${SERVICES[@]}"; do
    SVC="${entry%%:*}"
    DESC="${entry##*:}"
    STATUS=$(systemctl is-active "$SVC" 2>/dev/null)
    if [ "$STATUS" = "active" ]; then
        log "  OK: ${DESC} (${SVC})"
    else
        log "  FEHLER: ${DESC} (${SVC}) — Status: ${STATUS}"
    fi
done

# -------------------------------------------------------------------------
# 9. USB/Seriell (ESP32-S3 Geraete)
# -------------------------------------------------------------------------
log "--- [9/10] USB/Seriell ---"
for DEV in /dev/amr_drive /dev/amr_sensor /dev/ttyUSB0; do
    if [ -e "$DEV" ]; then
        log "  OK: ${DEV} vorhanden"
    else
        log "  FEHLT: ${DEV} nicht gefunden"
    fi
done

# -------------------------------------------------------------------------
# 10. Journal-Fehler (letzte 24 Stunden)
# -------------------------------------------------------------------------
log "--- [10/10] Kritische Fehler (letzte 24h) ---"
ERRORS=$(journalctl -p 0..3 --since "24 hours ago" --no-pager 2>/dev/null | grep -v "^-- ")
if [ -n "$ERRORS" ]; then
    echo "$ERRORS" | tee -a "${LOG_FILE}"
else
    log "OK: Keine kritischen Fehler."
fi

log "=== Wartungslauf beendet ==="
echo "----------------------------------------" >> "${LOG_FILE}"
