#!/usr/bin/env bash
# Synchronisiert grosse Binaerdateien vom Mac zurueck zum Pi5.
# Nur fuer Restore-Faelle oder wenn auf dem Mac neue Dateien hinzugefuegt wurden.
#
# Verwendung: ./scripts/sync/sync_from_mac.sh [MAC_HOST]
set -euo pipefail

MAC_HOST="${1:-mac}"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_BASE="/Users/jan/daten/projekts/amr-projekt"

echo "=== AMR Medien-Sync: Mac ($MAC_HOST) -> Pi5 ==="

SYNC_DIRS=(
    "sources/"
    "hardware/schaltplan/"
    "hardware/datasheet/"
    "hardware/can-bus/"
    "hardware/media/"
    "hardware/akku/"
)

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
        "${MAC_HOST}:${REMOTE_BASE}/${dir}" "${local_dir}" 2>/dev/null || \
        echo "  (Verzeichnis nicht auf Mac vorhanden, uebersprungen)"
done

echo ""
echo "=== Sync abgeschlossen ==="
