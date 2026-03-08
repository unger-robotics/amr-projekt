#!/bin/bash
set -euo pipefail

REPORT_FILE="konsistenz_report_gesamt.md"
TMPDIR_AUDIT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_AUDIT"' EXIT

# Gemeinsames Ausgabeformat fuer alle Bloecke
FORMAT_HINT="Erstelle eine Markdown-Tabelle mit Spalten: 'Datei', 'Abweichung', 'Ist-Zustand laut Code', 'Soll-Zustand laut Doku'. Falls keine Abweichungen: schreibe 'Keine Abweichungen gefunden'."

# --- Block-Definitionen ---
run_block() {
  local id="$1" title="$2" prompt="$3"
  local outfile="$TMPDIR_AUDIT/block_${id}.md"
  echo "  [${id}/4] Starte: ${title} ..."
  if claude -p "${prompt} ${FORMAT_HINT}" > "$outfile" 2>"$TMPDIR_AUDIT/err_${id}.log"; then
    echo "  [${id}/4] Fertig:  ${title}"
  else
    echo "  [${id}/4] FEHLER: ${title} (Exit $?)"
    echo "_Fehler bei der Auswertung. Siehe err_${id}.log._" > "$outfile"
  fi
}

echo "Starte parallele Dokumentenpruefung (4 Bloecke) ..."
echo ""

# Block 1-4 parallel starten
run_block 1 "Technische Dokumentation (docs/)" \
  "Lese CLAUDE.md und analysiere den Quellcode in amr/. Pruefe alle Markdown-Dateien im Verzeichnis docs/. Finde alle inhaltlichen Abweichungen (Architektur, Hardware-Parameter, QoS, Testverfahren, CAN-Bus-Nutzung) zwischen der Dokumentation und der Realitaet im Code." &

run_block 2 "Projektplanung (planung/)" \
  "Analysiere die Kernkonfigurationen und den Code in amr/. Pruefe alle Dokumente im Verzeichnis planung/ (insbesondere systemdokumentation.md, roadmap.md, DoD-checkliste-phasen.md). Kontrolliere, ob die Systemarchitektur (die 3 Ebenen), Metriken (z. B. 50 ms Latenz, Topic-Raten) und Terminologien exakt mit dem aktuellen Implementierungsstand in amr/ uebereinstimmen. Dokumentiere alle Diskrepanzen." &

run_block 3 "Bachelorarbeit Kap. 1-4 (Theorie)" \
  "Lese CLAUDE.md und die Code-Struktur in amr/. Pruefe in bachelorarbeit/ die Dateien kapitel_01_einleitung.md, kapitel_02_grundlagen.md, kapitel_03_anforderungsanalyse.md und kapitel_04_systemkonzept.md. Stelle sicher, dass Hardware-Zuordnungen, Terminologie-Normen (z. B. 'Fahrkern', 'Intent') und das beschriebene Systemkonzept fehlerfrei dem tatsaechlichen Code in amr/ entsprechen." &

run_block 4 "Bachelorarbeit Kap. 5-7 (Implementierung)" \
  "Analysiere den finalen Code und die Test-Ergebnisse in amr/. Pruefe in bachelorarbeit/ die Dateien kapitel_05_implementierung.md, kapitel_06_validierung.md, kapitel_07_fazit.md sowie das Sammeldokument latex/kap1-7.tex. Vergleiche jede genannte Zahl, Validierungsmetrik (z. B. CAN vs. USB Raten, 921600 Baudrate) und jedes Implementierungsdetail exakt mit dem realen Code. Fuehre alle gefundenen Widersprueche auf." &

# Warten bis alle 4 fertig sind
wait
echo ""

# Report zusammenbauen (Reihenfolge garantiert)
{
  echo "# Audit-Report: Globale Dokumentationskonsistenz (AMR)"
  echo "Datum: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "Referenzbasis: Quellcode und Konfigurationen in amr/ sowie CLAUDE.md"
  echo "Pruefziele: docs/, planung/, bachelorarbeit/"
  echo "---"
  echo ""

  for i in 1 2 3 4; do
    case $i in
      1) echo "## 1. Technische Dokumentation (docs/)" ;;
      2) echo "## 2. Projektplanung und Systemdokumentation (planung/)" ;;
      3) echo "## 3. Bachelorarbeit: Theorie und Konzept (Kapitel 1-4)" ;;
      4) echo "## 4. Bachelorarbeit: Implementierung und Validierung (Kapitel 5-7)" ;;
    esac
    echo ""
    cat "$TMPDIR_AUDIT/block_${i}.md"
    echo ""
  done
} > "$REPORT_FILE"

echo "Pruefung abgeschlossen. Ergebnisse in: $REPORT_FILE"
