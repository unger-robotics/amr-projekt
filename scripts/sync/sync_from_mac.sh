#!/usr/bin/env bash
# Synchronisiert grosse Binaerdateien von einem Ziel zurueck zum Pi5.
# Nur fuer Restore-Faelle oder wenn auf dem Ziel neue Dateien hinzugefuegt wurden.
#
# Verwendung: ./scripts/sync/sync_from_mac.sh [QUELLE]
#   QUELLE: mac, book (alias mbp) (Standard: mac)
#
# Hosts (aus ~/.ssh/config):
#   mac         = 192.168.1.210 (iMac)
#   book / mbp  = mbp.local (MacBook, Bonjour-Name statt fester IP)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_BASE="/Users/jan/daten/projekts/amr-projekt"

SOURCE="${1:-mac}"

case "${SOURCE}" in
    mac|book) ;;
    # mbp ist derselbe Host wie book; beide Namen stehen in ~/.ssh/config
    mbp) SOURCE="book" ;;
    *)
        echo "Unbekannte Quelle: ${SOURCE}"
        echo "Verwendung: $0 [mac|book|mbp]"
        exit 1
        ;;
esac

echo "=== AMR Medien-Sync: ${SOURCE} -> Pi5 ==="

if ! ssh -o ConnectTimeout=5 "${SOURCE}" "echo OK" &>/dev/null; then
    echo "FEHLER: ${SOURCE} nicht erreichbar."
    exit 1
fi

# Regelreihenfolge: rsync wertet von oben nach unten aus,
# erster Treffer entscheidet.
rsync -avz --progress \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='.pio/' \
    --exclude='dashboard/dist/' \
    --exclude='site/' \
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
    "${SOURCE}:${REMOTE_BASE}/" "${PROJECT_DIR}/"

echo ""
echo "=== Sync abgeschlossen ==="
