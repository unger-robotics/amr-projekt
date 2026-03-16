#!/bin/bash
# =============================================================================
# optimize_project_images.sh - PNG- und HEIC-Dateien im Zielordner optimieren
# =============================================================================
# Durchsucht alle Unterordner. Skaliert PNG/HEIC verlustbehaftet auf Max-Breite.
# Komprimiert PNGs zusätzlich verlustfrei. Keine JPG-Konvertierung.
# Kompatibel mit macOS bash 3.2
# =============================================================================

set -e

# Konfiguration
TARGET_DIR="hardware/media"
MAX_WIDTH=1920
DRY_RUN=true
BACKUP_DIR="${TARGET_DIR}/originals_backup"
MIN_SIZE_KB=500  # Nur Dateien > 500 KB optimieren

# Argumente
while [[ $# -gt 0 ]]; do
    case $1 in
        --run) DRY_RUN=false; shift ;;
        --max-width) MAX_WIDTH="$2"; shift 2 ;;
        -h|--help)
            echo "Verwendung: $0 [--run] [--max-width PIXEL]"
            echo ""
            echo "  --run           Wirklich ausführen (sonst nur Vorschau)"
            echo "  --max-width N   Maximale Breite (Standard: 1920)"
            exit 0
            ;;
        *) shift ;;
    esac
done

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Fehler: Zielordner '$TARGET_DIR' nicht gefunden."
    exit 1
fi

# Helfer
format_size() {
    local bytes=$(stat -f%z "$1" 2>/dev/null)
    if [[ $bytes -ge 1048576 ]]; then
        awk "BEGIN {printf \"%.1f MB\", $bytes / 1048576}"
    else
        awk "BEGIN {printf \"%.0f KB\", $bytes / 1024}"
    fi
}

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Bild-Optimierung (PNG & HEIC) für $TARGET_DIR"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Max. Breite:  ${MAX_WIDTH}px                                     ║"
echo "║  Min. Größe:   ${MIN_SIZE_KB} KB                                     ║"
if $DRY_RUN; then
echo "║  Modus:        VORSCHAU (--run zum Ausführen)             ║"
else
echo "║  Modus:        AUSFÜHREN                                  ║"
fi
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# oxipng prüfen
if command -v oxipng &>/dev/null; then
    echo "✓ oxipng installiert"
else
    echo "○ oxipng nicht installiert (nur Resize)"
fi
echo ""

echo "Suche PNG- und HEIC-Dateien in $TARGET_DIR..."
echo ""

tmp_file=$(mktemp)
tmp_all=$(mktemp)

# Alle PNG- und HEIC-Dateien im Zielordner sammeln
find "$TARGET_DIR" -type f \( -iname "*.png" -o -iname "*.heic" \) \
    ! -path "*/build/*" \
    ! -path "*/out/*" \
    ! -path "*/_site/*" \
    ! -path "$BACKUP_DIR/*" \
    2>/dev/null | sort > "$tmp_all"

printf "%-50s %10s %10s %s\n" "DATEI" "GRÖSSE" "BREITE" "AKTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while read -r file; do
    size_bytes=$(stat -f%z "$file" 2>/dev/null)
    size_kb=$((size_bytes / 1024))
    size_display=$(format_size "$file")
    width=$(sips -g pixelWidth "$file" 2>/dev/null | awk '/pixelWidth:/{print $2}')

    ext="${file##*.}"
    ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    # Entscheiden ob optimieren
    action="übersprungen"
    if [[ $size_kb -ge $MIN_SIZE_KB ]]; then
        if [[ $width -gt $MAX_WIDTH ]]; then
            if [[ "$ext_lower" == "png" ]]; then
                action="RESIZE+OXIPNG"
            else
                action="RESIZE (HEIC)"
            fi
            echo "$file" >> "$tmp_file"
        elif [[ "$ext_lower" == "png" ]]; then
            action="OXIPNG"
            echo "$file" >> "$tmp_file"
        fi
    fi

    # Kürzen des Pfads für Anzeige
    short_path="${file#./}"
    if [[ ${#short_path} -gt 48 ]]; then
        short_path="...${short_path: -45}"
    fi

    printf "%-50s %10s %8spx %s\n" "$short_path" "$size_display" "$width" "$action"
done < "$tmp_all"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total_files=$(wc -l < "$tmp_all" | tr -d ' ')
optimize_files=$(wc -l < "$tmp_file" 2>/dev/null | tr -d ' ')

total_size=0
while read -r file; do
    size=$(stat -f%z "$file" 2>/dev/null)
    total_size=$((total_size + size))
done < "$tmp_all"
total_size_mb=$(awk "BEGIN {printf \"%.1f\", $total_size / 1048576}")

echo "Gesamt: $total_files Dateien, ${total_size_mb} MB"
echo "Zu optimieren: $optimize_files Dateien"
echo ""

if [[ ! -s "$tmp_file" ]]; then
    echo "Keine Dateien zum Optimieren."
    rm -f "$tmp_file" "$tmp_all"
    exit 0
fi

if $DRY_RUN; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "VORSCHAU - Zum Ausführen: $0 --run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rm -f "$tmp_file" "$tmp_all"
    exit 0
fi

# Ausführen
echo "Erstelle Backup in $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

while read -r file; do
    filename=$(basename "$file")
    dirname=$(dirname "$file")

    ext="${file##*.}"
    ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    # Backup
    backup_name="${dirname//\//_}_${filename}"
    backup_name="${backup_name#._}"
    cp "$file" "$BACKUP_DIR/$backup_name"

    orig_size=$(format_size "$file")
    width=$(sips -g pixelWidth "$file" 2>/dev/null | awk '/pixelWidth:/{print $2}')

    echo ""
    echo "📄 $file"

    # Resize (für PNG und HEIC)
    if [[ $width -gt $MAX_WIDTH ]]; then
        echo "   Resize: ${width}px → ${MAX_WIDTH}px"
        sips --resampleWidth $MAX_WIDTH "$file" &>/dev/null
    fi

    # oxipng (ausschließlich für PNG)
    if [[ "$ext_lower" == "png" ]] && command -v oxipng &>/dev/null; then
        echo "   oxipng: Kompression optimieren..."
        oxipng -o 4 --strip safe "$file" 2>/dev/null
    fi

    new_size=$(format_size "$file")
    echo "   ✓ $orig_size → $new_size"

done < "$tmp_file"

rm -f "$tmp_file"

# Nachher berechnen
total_after=0
while read -r file; do
    [[ -f "$file" ]] && size=$(stat -f%z "$file" 2>/dev/null) && total_after=$((total_after + size))
done < "$tmp_all"
total_after_mb=$(awk "BEGIN {printf \"%.1f\", $total_after / 1048576}")

rm -f "$tmp_all"

saved=$((total_size - total_after))
saved_mb=$(awk "BEGIN {printf \"%.1f\", $saved / 1048576}")

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Zusammenfassung                                          ║"
echo "╠═══════════════════════════════════════════════════════════╣"
printf "║  Vorher:    %-10s                                  ║\n" "${total_size_mb} MB"
printf "║  Nachher:   %-10s                                  ║\n" "${total_after_mb} MB"
printf "║  Ersparnis: %-10s                                  ║\n" "${saved_mb} MB"
echo "║  Backup:    $BACKUP_DIR/         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Wiederherstellen: cp $BACKUP_DIR/[datei] [ziel]"
