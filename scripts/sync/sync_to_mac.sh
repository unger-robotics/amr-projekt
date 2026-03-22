#!/usr/bin/env bash
# Synchronisiert grosse Binaerdateien vom Pi5 zu einem oder mehreren Zielen.
#
# Verwendung: ./scripts/sync/sync_to_mac.sh [ZIEL]
#   ZIEL: mac, book, all (Standard: all)
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

sync_to_host() {
    local host="$1"
    echo ""
    echo "=== AMR Medien-Sync: Pi5 -> ${host} ==="

    if ! ssh -o ConnectTimeout=5 "${host}" "echo OK" &>/dev/null; then
        echo "  WARNUNG: ${host} nicht erreichbar, uebersprungen."
        return 1
    fi

    for dir in "${SYNC_DIRS[@]}"; do
        src="${PROJECT_DIR}/${dir}"
        if [ -d "${src}" ]; then
            echo "--- Sync: ${dir}"
            ssh "${host}" "mkdir -p '${REMOTE_BASE}/${dir}'"
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
                "${src}" "${host}:${REMOTE_BASE}/${dir}"
        fi
    done

    echo "=== ${host}: Sync abgeschlossen ==="
}

TARGET="${1:-all}"

case "${TARGET}" in
    mac|book)
        sync_to_host "${TARGET}"
        ;;
    all)
        sync_to_host "mac"
        sync_to_host "book"
        ;;
    *)
        echo "Unbekanntes Ziel: ${TARGET}"
        echo "Verwendung: $0 [mac|book|all]"
        exit 1
        ;;
esac
