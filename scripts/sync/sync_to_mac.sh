#!/usr/bin/env bash
# Synchronisiert grosse Binaerdateien vom Pi5 zu einem oder mehreren Zielen.
# Erfasst automatisch alle Binaries im gesamten Projektbaum.
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

sync_to_host() {
    local host="$1"
    echo ""
    echo "=== AMR Medien-Sync: Pi5 -> ${host} ==="

    if ! ssh -o ConnectTimeout=5 "${host}" "echo OK" &>/dev/null; then
        echo "  WARNUNG: ${host} nicht erreichbar, uebersprungen."
        return 1
    fi

    # Regelreihenfolge: rsync wertet von oben nach unten aus,
    # erster Treffer entscheidet.
    rsync -avz --progress \
        --exclude='.git/' \
        --exclude='node_modules/' \
        --exclude='__pycache__/' \
        --exclude='.pio/' \
        --exclude='dashboard/dist/' \
        --exclude='.DS_Store' \
        --include='*/' \
        --include='*.pdf' \
        --include='*.PDF' \
        --include='*.png' \
        --include='*.PNG' \
        --include='*.jpg' \
        --include='*.HEIC' \
        --include='*.heic' \
        --include='*.mp4' \
        --include='*.mov' \
        --include='*.MOV' \
        --include='*.avi' \
        --include='*.mp3' \
        --include='*.wav' \
        --include='*.svg' \
        --include='*.hef' \
        --include='*.pem' \
        --exclude='*' \
        "${PROJECT_DIR}/" "${host}:${REMOTE_BASE}/"

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
