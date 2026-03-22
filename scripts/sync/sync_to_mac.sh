#!/usr/bin/env bash
# Synchronisiert grosse Binaerdateien vom Pi5 zum Mac via rsync.
# Mac = alleiniger Langzeitspeicher fuer PDFs, Datenblaetter, Schaltplaene, Medien.
#
# Verwendung: ./scripts/sync/sync_to_mac.sh [MAC_HOST]
# Standard-Host: mac (aus ~/.ssh/config)
set -euo pipefail

MAC_HOST="${1:-mac}"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_BASE="/Users/jan/daten/projekts/amr-projekt"

echo "=== AMR Medien-Sync: Pi5 -> Mac ($MAC_HOST) ==="

SYNC_DIRS=(
    "sources/"
    "hardware/schaltplan/"
    "hardware/datasheet/"
    "hardware/can-bus/"
    "hardware/media/"
    "hardware/akku/"
)

for dir in "${SYNC_DIRS[@]}"; do
    src="${PROJECT_DIR}/${dir}"
    if [ -d "${src}" ]; then
        echo "--- Sync: ${dir}"
        ssh "${MAC_HOST}" "mkdir -p '${REMOTE_BASE}/${dir}'"
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
            --exclude='*.md' \
            --exclude='*.py' \
            --exclude='*.sh' \
            --exclude='.DS_Store' \
            "${src}" "${MAC_HOST}:${REMOTE_BASE}/${dir}"
    fi
done

echo ""
echo "=== Sync abgeschlossen ==="
