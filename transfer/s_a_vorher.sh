#!/usr/bin/env bash
# S-A vorher / nachher: CAN-Zaehler vor und nach einem Messlauf sichern,
# candump mit Zeitstempeln aufzeichnen. Keine Aenderung am System, kein CAN-TX.
#
# Aufruf:   ./s_a_vorher.sh <Label> [Dauer_s] [Interface]
# Beispiel: ./s_a_vorher.sh A1 600 can0
# Ohne sudo aufrufen: candump und das Lesen von /sys benoetigen keine Root-Rechte;
# mit sudo wuerden die Ergebnisdateien root gehoeren.
#
# Ergebnis: validation/P-CAN2/<YYYYMMDD_HHMM>_<Label>/ (neben diesem Skript, unabhaengig
#           vom Aufrufverzeichnis)
#           stats_before.txt/.json, stats_after.txt/.json, candump.log, meta.txt
#
# candump.log enthaelt neben den Datenframes auch CAN-Error-Frames (Kennung mit
# gesetztem Bit 0x20000000, z. B. 20000004#...): Der Fehlerfilter "#FFFFFFFF" gibt
# sie frei. Der mcp251x-Treiber meldet einen RX-Pufferueberlauf als Error-Frame mit
# CAN_ERR_CRTL (0x04) und Datenbyte 1 = CAN_ERR_CRTL_RX_OVERFLOW (0x01).
set -euo pipefail

LABEL="${1:?Label fehlt (z. B. A1, A2, B1)}"
DUR="${2:-600}"
IF="${3:-can0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT="$SCRIPT_DIR/$(date +%Y%m%d_%H%M)_${LABEL}"
mkdir -p "$OUT"

for tool in candump ip; do
  command -v "$tool" >/dev/null || { echo "fehlt: $tool"; exit 1; }
done
ip link show "$IF" >/dev/null || { echo "Interface $IF nicht vorhanden"; exit 1; }

# Textform (Nachweis) und JSON (maschinell auswertbar: stats64.rx.*, info_xstats.*)
dump_stats() {
  {
    echo "### $(date -Is)"
    ip -details -statistics link show "$IF"
    for f in rx_packets rx_bytes rx_errors rx_over_errors rx_fifo_errors \
             rx_missed_errors rx_dropped tx_packets tx_errors; do
      printf '%s=%s\n' "$f" "$(cat "/sys/class/net/$IF/statistics/$f")"
    done
  } | sed 's/[[:space:]]*$//' > "$1.txt"   # ip-Ausgabe hat Leerzeichen am Zeilenende (pre-commit)
  ip -json -details -statistics link show "$IF" > "$1.json"
}

# @version-Zeile einer Firmware-Konfiguration (belegt den Repo-Stand, nicht den
# geflashten Stand; K0.1 bleibt eine manuelle Pruefung)
fw_version() {
  grep -oE '@version[[:space:]]+[0-9.]+' "$1" 2>/dev/null | awk '{print $2}' || echo unbekannt
}

{
  echo "label=$LABEL"
  echo "interface=$IF"
  echo "duration_s=$DUR"
  echo "host=$(hostname)"
  echo "kernel=$(uname -r)"
  echo "driver=$(basename "$(readlink -f /sys/class/net/$IF/device/driver 2>/dev/null || echo unbekannt)")"
  echo "overlay=$(grep -hE 'dtoverlay=(mcp2515|mcp251xfd)' /boot/firmware/config.txt /boot/config.txt 2>/dev/null | tr '\n' ' ')"
  echo "bittiming=$(ip -details link show "$IF" | grep -E 'bitrate|sample-point|tq ' | tr -s ' ' | tr '\n' ' ')"
  echo "git_commit=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unbekannt)"
  echo "git_describe=$(git -C "$REPO_ROOT" describe --tags --always --dirty 2>/dev/null || echo unbekannt)"
  echo "config_drive_version=$(fw_version "$REPO_ROOT/amr/mcu_firmware/drive_node/include/config_drive.h")"
  echo "config_sensors_version=$(fw_version "$REPO_ROOT/amr/mcu_firmware/sensor_node/include/config_sensors.h")"
  echo "start=$(date -Is)"
} | sed 's/[[:space:]]*$//' > "$OUT/meta.txt"

dump_stats "$OUT/stats_before"
echo "Messlauf $LABEL: $DUR s auf $IF -> $OUT"
# -L: Log-Format mit absolutem Zeitstempel (Sekunden.Mikrosekunden)
# "$IF,0:0,#FFFFFFFF": alle Datenframes plus alle Error-Frames
timeout "$DUR" candump -L "$IF,0:0,#FFFFFFFF" > "$OUT/candump.log" || true
dump_stats "$OUT/stats_after"
echo "end=$(date -Is)" >> "$OUT/meta.txt"

echo "fertig: $(wc -l < "$OUT/candump.log") Zeilen (Daten- und Error-Frames)"
echo "Auswertung: python3 $SCRIPT_DIR/s_a_analyse.py $OUT"
