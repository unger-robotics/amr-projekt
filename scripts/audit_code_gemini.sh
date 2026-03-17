#!/bin/bash
# Zweck: Paralleles, systemuebergreifendes Code-Audit mit spezialisierten Gemini-Agenten
# Aufruf: ./scripts/audit_code_gemini.sh
# Abhaengigkeiten: curl, jq, Bash 4.0+
# Umgebung: Linux/macOS, Ausfuehrung im Projekt-Stammverzeichnis amr-projekt/
# Einschraenkungen: Token-Limit des Modells, API-Rate-Limits bei parallelen Aufrufen

set -euo pipefail

MODEL_ID="gemini-3.1-pro-preview"
API_KEY_FILE="scripts/.gemini_api.key"
REPORT_FILE="konsistenz_report_audit_code.md"
TMPDIR_AUDIT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_AUDIT"' EXIT

declare -a TARGET_DIRS=(
    "amr/pi5"
    "dashboard"
    "amr/scripts"
    "amr/mcu_firmware"
    "amr/docker"
)

FORMAT_HINT="Erstelle eine Markdown-Tabelle mit den Spalten: 'Schnittstelle/Komponente', 'Beteiligte Subsysteme', 'Identifizierter Konflikt', 'Erforderliche Massnahme'. Falls keine Abweichungen vorliegen, schreibe exakt 'Keine Inkonsistenzen gefunden'."

# 1. API-Key pruefen
if [[ ! -f "$API_KEY_FILE" ]]; then
    echo "FEHLER: API-Key-Datei '$API_KEY_FILE' nicht gefunden."
    exit 1
fi
GEMINI_API_KEY=$(tr -d '\n' < "$API_KEY_FILE")

# 2. Verzeichnisse validieren
for dir in "${TARGET_DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
        echo "FEHLER: Verzeichnis '$dir' existiert nicht. Abbruch."
        exit 1
    fi
done

echo "Lese Quellcode aus den Zielverzeichnissen ein (einmaliger Vorgang)..."

# 3. Code zentral einsammeln
CODE_CONTENT=""
for dir in "${TARGET_DIRS[@]}"; do
    while IFS= read -r file; do
        CODE_CONTENT+=$'\n'
        CODE_CONTENT+="--- DATEI: $file ---"$'\n'
        CODE_CONTENT+=$(cat "$file" 2>/dev/null || echo "Fehler beim Lesen")$'\n'
    done < <(find "$dir" -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.cpp" -o -name "*.h" -o -name "*.md" -o -name "Dockerfile*" \) 2>/dev/null)
done

# 4. Definition der Ausfuehrungslogik fuer einen Agenten
run_agent() {
  local id="$1" title="$2" focus_prompt="$3"
  local outfile="$TMPDIR_AUDIT/agent_${id}.md"

  echo "  [Agent ${id}/3] Starte Analyse: ${title} ..."

  local json_payload
  json_payload=$(jq -n \
    --arg prompt "$focus_prompt" \
    --arg format "$FORMAT_HINT" \
    --arg code "$CODE_CONTENT" \
    '{
      "contents": [{
        "parts": [
          {"text": $prompt},
          {"text": "\n--- GESAMTER QUELLCODE ---\n"},
          {"text": $code},
          {"text": "\n--- AUSGABEFORMAT ---\n"},
          {"text": $format}
        ]
      }]
    }')

  local api_url="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent?key=${GEMINI_API_KEY}"
  local response
  response=$(curl -s -X POST "$api_url" -H 'Content-Type: application/json' -d "$json_payload")

  local error_msg
  error_msg=$(echo "$response" | jq -r '.error.message // empty')

  if [[ -n "$error_msg" ]]; then
      echo "  [Agent ${id}/3] FEHLER: API meldet: $error_msg"
      echo "_API Fehler: $error_msg_" > "$outfile"
  else
      echo "$response" | jq -r '.candidates[0].content.parts[0].text // "Keine Antwort generiert."' > "$outfile"
      echo "  [Agent ${id}/3] Fertig:  ${title}"
  fi
}

echo "Starte parallele Code-Pruefung durch spezialisierte Agenten ..."
echo ""

# 5. Agenten parallel starten
run_agent 1 "Netzwerk & API" \
  "Pruefe ausschliesslich auf inhaltliche und technische Abweichungen bei API-Routen, REST-Endpunkten, WebSockets und Datenschemata zwischen dem Hauptrechner (amr/pi5) und dem Frontend (dashboard)." &

run_agent 2 "Hardware & Firmware" \
  "Pruefe ausschliesslich auf inhaltliche und technische Abweichungen bei CAN-Bus-Nachrichten (IDs, Frequenzen), Hardware-Pin-Zuweisungen und SPI/I2C-Kommunikation zwischen dem Hauptrechner (amr/pi5) und der Mikrocontroller-Firmware (amr/mcu_firmware)." &

run_agent 3 "Infrastruktur & Middleware" \
  "Pruefe ausschliesslich auf inhaltliche und technische Abweichungen bei ROS-Topics, Umgebungsvariablen und Start-Parametern zwischen der Container-Infrastruktur (amr/docker), den Hilfsskripten (amr/scripts) und dem Hauptrechner (amr/pi5)." &

# Warten auf alle Prozesse
wait
echo ""

# 6. Report zusammenbauen
{
  echo "# Audit-Report: Systemuebergreifende Code-Konsistenz (AMR)"
  echo "Datum: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "Gepruefte Zielverzeichnisse: ${TARGET_DIRS[*]}"
  echo "Modell: $MODEL_ID"
  echo "---"
  echo ""

  echo "## Agent 1: Netzwerk & API (Backend <-> Frontend)"
  cat "$TMPDIR_AUDIT/agent_1.md"
  echo ""

  echo "## Agent 2: Hardware & Firmware (Pi5 <-> MCU)"
  cat "$TMPDIR_AUDIT/agent_2.md"
  echo ""

  echo "## Agent 3: Infrastruktur & Middleware (Docker <-> ROS <-> Skripte)"
  cat "$TMPDIR_AUDIT/agent_3.md"
  echo ""
} > "$REPORT_FILE"

echo "Pruefung abgeschlossen. Ergebnisse in: $REPORT_FILE"
