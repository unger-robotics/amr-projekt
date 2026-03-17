#!/bin/bash
# Zweck: Paralleles Dokumentationsaudit (Quelle: Code vs. Doku) mit der Gemini API
# Aufruf: ./scripts/audit_doku_gemini.sh
# Abhängigkeiten: curl, jq, Bash 4.0+
# Umgebung: Linux/macOS, Ausführung im Projekt-Stammverzeichnis

set -euo pipefail

MODEL_ID="gemini-3.1-pro-preview"
# Korrigierter Pfad zur Schlüsseldatei
API_KEY_FILE="scripts/.gemini_api.key"
REPORT_FILE="konsistenz_report_audit_doku.md"
TMPDIR_AUDIT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_AUDIT"' EXIT

FORMAT_HINT="Erstelle eine Markdown-Tabelle mit Spalten: 'Datei', 'Abweichung', 'Ist-Zustand laut Code', 'Soll-Zustand laut Doku'. Falls keine Abweichungen: schreibe 'Keine Abweichungen gefunden'."

# 1. Vorbedingungen prüfen
if ! command -v curl &> /dev/null || ! command -v jq &> /dev/null; then
    echo "FEHLER: 'curl' oder 'jq' fehlen. Bitte installieren."
    exit 1
fi

if [[ ! -f "$API_KEY_FILE" ]]; then
    echo "FEHLER: API-Key-Datei '$API_KEY_FILE' nicht gefunden."
    exit 1
fi
GEMINI_API_KEY=$(tr -d '\n' < "$API_KEY_FILE")

for dir in "amr" "dashboard"; do
    if [[ ! -d "$dir" ]]; then
        echo "FEHLER: Kritisches Referenzverzeichnis '$dir/' nicht gefunden. Abbruch."
        exit 1
    fi
done

# 2. Referenzcode einmalig einlesen (verhindert redundante I/O-Operationen)
echo "Lese Referenzcode aus amr/ und dashboard/ ein..."
CODE_CONTEXT=""
while IFS= read -r file; do
    CODE_CONTEXT+=$'\n'
    CODE_CONTEXT+="--- CODE-DATEI: $file ---"$'\n'
    CODE_CONTEXT+=$(cat "$file" 2>/dev/null || echo "")
done < <(find amr dashboard -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.cpp" -o -name "*.h" \) 2>/dev/null)

# 3. Ausführungslogik für die API
run_block() {
  local id="$1" title="$2" prompt="$3" doc_paths="$4"
  local outfile="$TMPDIR_AUDIT/block_${id}.md"

  echo "  [${id}/6] Starte: ${title} ..."

  # Ziel-Dokumentation für diesen Block einsammeln
  local doc_context=""
  for path in $doc_paths; do
      if [[ -d "$path" ]]; then
          while IFS= read -r file; do
              doc_context+=$'\n'"--- DOKU-DATEI: $file ---"$'\n'
              doc_context+=$(cat "$file" 2>/dev/null || echo "")
          done < <(find "$path" -type f -name "*.md" 2>/dev/null)
      elif [[ -f "$path" ]]; then
          doc_context+=$'\n'"--- DOKU-DATEI: $path ---"$'\n'
          doc_context+=$(cat "$path" 2>/dev/null || echo "")
      fi
  done

  # JSON Payload generieren
  local json_payload
  json_payload=$(jq -n \
    --arg prompt "$prompt" \
    --arg format "$FORMAT_HINT" \
    --arg code "$CODE_CONTEXT" \
    --arg docs "$doc_context" \
    '{
      "contents": [{
        "parts": [
          {"text": $prompt},
          {"text": "\n--- REFERENZ-CODE ---\n"},
          {"text": $code},
          {"text": "\n--- ZIEL-DOKUMENTATION ---\n"},
          {"text": $docs},
          {"text": $format}
        ]
      }]
    }')

  # API Aufruf
  local api_url="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent?key=${GEMINI_API_KEY}"
  local response
  response=$(curl -s -X POST "$api_url" -H 'Content-Type: application/json' -d "$json_payload")

  local error_msg
  error_msg=$(echo "$response" | jq -r '.error.message // empty')

  if [[ -n "$error_msg" ]]; then
      echo "  [${id}/6] FEHLER: API meldet: $error_msg"
      echo "_API Fehler: $error_msg_" > "$outfile"
  else
      echo "$response" | jq -r '.candidates[0].content.parts[0].text // "Keine Antwort generiert."' > "$outfile"
      echo "  [${id}/6] Fertig:  ${title}"
  fi
}

echo "Starte parallele Dokumentenpruefung (6 Bloecke) ..."
echo ""

# Aufrufe mit Angabe der spezifischen Pfade (Argument 4)
run_block 1 "Technische Dokumentation" \
  "Pruefe alle Markdown-Dateien im Verzeichnis docs/. Finde alle inhaltlichen Abweichungen (Architektur, Parameter) zwischen der Dokumentation und der Realitaet im Code." \
  "docs" &

run_block 2 "Meta-Dateien" \
  "Pruefe die zentralen READMEs und die CLAUDE.md. Kontrolliere auf inhaltliche Widersprueche zum tatsaechlichen Code." \
  "README.md CLAUDE.md amr/README.md dashboard/README.md" &

run_block 3 "Projektplanung" \
  "Pruefe alle Dokumente im Verzeichnis planung/. Kontrolliere, ob Systemarchitektur und Metriken exakt mit dem aktuellen Implementierungsstand uebereinstimmen." \
  "planung" &

run_block 4 "Projektarbeit Kap. 1-4" \
  "Pruefe in projektarbeit/ die Kapitel 1 bis 4. Stelle sicher, dass Hardware-Zuordnungen und das beschriebene Systemkonzept fehlerfrei dem tatsaechlichen Code entsprechen." \
  "projektarbeit/kapitel_01_einleitung.md projektarbeit/kapitel_02_grundlagen.md projektarbeit/kapitel_03_anforderungsanalyse.md projektarbeit/kapitel_04_systemkonzept.md" &

run_block 5 "Projektarbeit Kap. 5-7" \
  "Pruefe in projektarbeit/ die Kapitel 5 bis 7. Vergleiche jede Validierungsmetrik und jedes Implementierungsdetail exakt mit dem realen Code." \
  "projektarbeit/kapitel_05_implementierung.md projektarbeit/kapitel_06_validierung.md projektarbeit/kapitel_07_fazit.md" &

run_block 6 "Praesentationen" \
  "Pruefe alle Dateien im Verzeichnis vortrag/. Kontrolliere, ob die fuer das Publikum aufbereiteten Kennzahlen exakt dem aktuellen Implementierungsstand entsprechen." \
  "vortrag" &

wait
echo ""

# Report zusammenbauen
{
  echo "# Audit-Report: Globale Dokumentationskonsistenz (AMR)"
  echo "Datum: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "Referenzbasis: Quellcode in amr/ und dashboard/"
  echo "Modell: $MODEL_ID"
  echo "---"
  echo ""

  for i in 1 2 3 4 5 6; do
    case $i in
      1) echo "## 1. Technische Dokumentation (docs/)" ;;
      2) echo "## 2. Meta-Dateien (Projektweite READMEs und CLAUDE.md)" ;;
      3) echo "## 3. Projektplanung und Systemdokumentation (planung/)" ;;
      4) echo "## 4. Projektarbeit: Theorie und Konzept (Kapitel 1-4)" ;;
      5) echo "## 5. Projektarbeit: Implementierung und Validierung (Kapitel 5-7)" ;;
      6) echo "## 6. Praesentationen (vortrag/)" ;;
    esac
    echo ""
    cat "$TMPDIR_AUDIT/block_${i}.md"
    echo ""
  done
} > "$REPORT_FILE"

echo "Pruefung abgeschlossen. Ergebnisse in: $REPORT_FILE"
