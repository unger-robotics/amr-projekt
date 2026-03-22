#!/usr/bin/env bash
# Synchronisiert grosse Binaerdateien von einem Ziel zurueck zum Pi5.
# Nur fuer Restore-Faelle oder wenn auf dem Ziel neue Dateien hinzugefuegt wurden.
#
# Verwendung: ./scripts/sync/sync_from_mac.sh [QUELLE]
#   QUELLE: mac, book (Standard: mac)
#
# Hosts (aus ~/.ssh/config):
#   mac  = 192.168.1.210 (iMac)
#   book = 192.168.1.163 (MacBook)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_BASE="/Users/jan/daten/projekts/amr-projekt"

SYNC_DIRS=(
    "sources/"
    "hardware/schaltplan/"
    "hardware/datasheet/"
    "hardware/can-bus/"
    "hardware/media/"
    "hardware/akku/"
)

SOURCE="${1:-mac}"

case "${SOURCE}" in
    mac|book) ;;
    *)
        echo "Unbekannte Quelle: ${SOURCE}"
        echo "Verwendung: $0 [mac|book]"
        exit 1
        ;;
esac

echo "=== AMR Medien-Sync: ${SOURCE} -> Pi5 ==="

if ! ssh -o ConnectTimeout=5 "${SOURCE}" "echo OK" &>/dev/null; then
    echo "FEHLER: ${SOURCE} nicht erreichbar."
    exit 1
fi

for dir in "${SYNC_DIRS[@]}"; do
    local_dir="${PROJECT_DIR}/${dir}"
    mkdir -p "${local_dir}"
    echo "--- Sync: ${dir}"
    rsync -avz --progress \
        --include='*.pdf' \
        --include='*.PDF' \
        --include='*.png' \
        --include='*.PNG' \
        --include='*.HEIC' \
        --include='*.heic' \
        --include='*.mp4' \
        --include='*.MOV' \
        --include='*.mov' \
        --include='*.svg' \
        --include='*/' \
        --exclude='*' \
        "${SOURCE}:${REMOTE_BASE}/${dir}" "${local_dir}" 2>/dev/null || \
        echo "  (Verzeichnis nicht auf ${SOURCE} vorhanden, uebersprungen)"
done

echo ""
echo "=== Sync abgeschlossen ==="
