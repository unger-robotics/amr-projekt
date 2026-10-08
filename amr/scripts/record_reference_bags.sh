#!/bin/bash
# =============================================================================
# Referenzaufnahme (rosbag2) fuer K7-V auf dem Pi 5 aufnehmen und pruefen
#
# Laeuft auf dem Host, nicht im Container. Voraussetzung: Der Stack laeuft im
# Container amr_ros2 mit den Launch-Argumenten der Szene
# (my_bot/config/reference_bags.yaml). Das Skript startet und stoppt den Stack
# nicht und sendet nichts: ros2 bag record abonniert nur.
#
# Verwendung:
#   amr/scripts/record_reference_bags.sh <szene> <dauer_s> [--no-check] [--force]
#     szene       a_stand | b_nav2 | c_person | probe
#     dauer_s     Aufnahmedauer in Sekunden (1 bis 3600)
#     --no-check  bag_check nach der Aufnahme nicht aufrufen
#     --force     trotz abweichender Launch-Argumente oder fehlender Topics aufnehmen
#
# Ablage:  ~/amr_bags/<JJJJMMTT_HHMM>_<szene>/ (im Container /amr_bags/...),
#          dazu metadata_amr.yaml ohne Umgebungsvariablen und ohne Schluessel
# Bericht: validation/P-AD1/<JJJJMMTT_HHMM>_<szene>/ mit bag_check.md und einer
#          Kopie von metadata_amr.yaml
# Ctrl+C:  beendet die Aufnahme sauber (SIGINT an den Recorder im Container)
# =============================================================================

set -euo pipefail

CONTAINER="amr_ros2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BAG_ROOT_HOST="${HOME}/amr_bags"
BAG_ROOT_CONTAINER="/amr_bags"
QOS_CONTAINER="/ros2_ws/src/my_bot/config/reference_bags_qos.yaml"
BAG_CHECK_CONTAINER="/scripts/bag_check.py"
KILL_AFTER_S=15

usage() {
    echo "Verwendung: $0 <szene> <dauer_s> [--no-check] [--force]"
    echo "  szene: a_stand | b_nav2 | c_person | probe   dauer_s: 1 bis 3600"
    exit "${1:-2}"
}

in_container() {
    docker exec "$CONTAINER" /entrypoint.sh "$@"
}

# --- Argumente ---------------------------------------------------------------
SZENE=""
DAUER=""
CHECK=1
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --no-check) CHECK=0 ;;
        --force) FORCE=1 ;;
        -h | --help) usage 0 ;;
        -*)
            echo "FEHLER: unbekannte Option $arg" >&2
            usage 2
            ;;
        *)
            if [ -z "$SZENE" ]; then
                SZENE=$arg
            elif [ -z "$DAUER" ]; then
                DAUER=$arg
            else
                echo "FEHLER: zu viele Argumente" >&2
                usage 2
            fi
            ;;
    esac
done
if [ -z "$SZENE" ] || [ -z "$DAUER" ]; then
    usage 2
fi
if ! [[ "$DAUER" =~ ^[0-9]+$ ]] || [ "$DAUER" -lt 1 ] || [ "$DAUER" -gt 3600 ]; then
    echo "FEHLER: dauer_s muss eine ganze Zahl von 1 bis 3600 sein" >&2
    exit 2
fi

# --- Vorpruefungen -----------------------------------------------------------
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "FEHLER: Container $CONTAINER laeuft nicht; zuerst den Stack starten." >&2
    exit 1
fi

# /amr_bags muss auf ~/amr_bags zeigen, sonst landet die Aufnahme im Container
MOUNT_QUELLE=$(docker inspect "$CONTAINER" \
    --format '{{range .Mounts}}{{if eq .Destination "/amr_bags"}}{{.Source}}{{end}}{{end}}')
if [ "$MOUNT_QUELLE" != "$BAG_ROOT_HOST" ]; then
    echo "FEHLER: /amr_bags im Container ist nicht $BAG_ROOT_HOST (ist: '${MOUNT_QUELLE:-kein Mount}')." >&2
    echo "  Container mit aktueller docker-compose.yml neu anlegen (amr/docker/README.md)." >&2
    exit 1
fi

LAUNCH_ZEILE=$(docker exec "$CONTAINER" pgrep -af -- "ros2 launch my_bot full_stack.launch.py" |
    head -n 1 | sed -E 's/^[0-9]+ //; s/^.*(ros2 launch )/\1/' || true)
if [ -z "$LAUNCH_ZEILE" ]; then
    echo "FEHLER: kein laufendes 'ros2 launch my_bot full_stack.launch.py' in $CONTAINER." >&2
    exit 1
fi

PLAN=$(in_container python3 "$BAG_CHECK_CONTAINER" --szene-plan "$SZENE" \
    --launch-zeile "$LAUNCH_ZEILE") || {
    echo "FEHLER: Szenenplan fuer '$SZENE' nicht lesbar." >&2
    exit 1
}
BESCHREIBUNG=""
TOPICS=()
ERWARTET=()
ABWEICHUNGEN=()
while IFS= read -r zeile; do
    schluessel=${zeile%% *}
    wert=${zeile#* }
    case "$schluessel" in
        BESCHREIBUNG) BESCHREIBUNG=$wert ;;
        TOPIC) TOPICS+=("$wert") ;;
        ERWARTET) ERWARTET+=("$wert") ;;
        ABWEICHUNG) ABWEICHUNGEN+=("$wert") ;;
    esac
done <<<"$PLAN"
if [ "${#TOPICS[@]}" -eq 0 ]; then
    echo "FEHLER: Topicliste leer." >&2
    exit 1
fi

VORHANDEN=$(in_container ros2 topic list 2>/dev/null || true)
FEHLEND=()
for t in "${ERWARTET[@]}"; do
    grep -qx -- "$t" <<<"$VORHANDEN" || FEHLEND+=("$t")
done

echo "Szene:  $SZENE ($BESCHREIBUNG)"
echo "Launch: $LAUNCH_ZEILE"
if [ "${#ABWEICHUNGEN[@]}" -gt 0 ] || [ "${#FEHLEND[@]}" -gt 0 ]; then
    for a in "${ABWEICHUNGEN[@]}"; do echo "ABWEICHUNG: $a" >&2; done
    for t in "${FEHLEND[@]}"; do echo "FEHLENDES TOPIC: $t" >&2; done
    if [ "$FORCE" -ne 1 ]; then
        echo "Abbruch ohne Aufnahme: Stack mit den Argumenten der Szene starten oder --force setzen." >&2
        exit 1
    fi
    echo "WARNUNG: --force gesetzt, Aufnahme trotz Abweichung." >&2
fi

NAME="$(date +%Y%m%d_%H%M)_${SZENE}"
BAG_HOST="$BAG_ROOT_HOST/$NAME"
BAG_CONTAINER="$BAG_ROOT_CONTAINER/$NAME"
if [ -e "$BAG_HOST" ]; then
    echo "FEHLER: $BAG_HOST existiert bereits (Aufnahme in derselben Minute); eine Minute warten." >&2
    exit 1
fi

GIT_COMMIT=$(git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null || echo unbekannt)
# Berichte dieses Werkzeugs zaehlen nicht als Aenderung des Arbeitsbaums
mapfile -t GIT_AENDERUNGEN < <(git -C "$REPO_DIR" status --porcelain -- . \
    ':(exclude)validation/P-AD1' 2>/dev/null | cut -c4- | head -n 30)
GIT_DIRTY=false
if [ "${#GIT_AENDERUNGEN[@]}" -gt 0 ]; then
    GIT_DIRTY=true
fi
IMAGE_ID=$(docker inspect "$CONTAINER" --format '{{.Image}}')

# --- Aufnahme ----------------------------------------------------------------
# docker exec reicht Signale nicht in den Container weiter. Bei Ctrl+C geht
# SIGINT deshalb gezielt an timeout, das es einmal an den Recorder weiterleitet;
# nur so schreibt rosbag2 eine vollstaendige metadata.yaml.
MUSTER="^timeout -s INT --kill-after=${KILL_AFTER_S} [0-9]+ ros2 bag record .* -o ${BAG_CONTAINER} "
ABGEBROCHEN=0
abbruch() {
    ABGEBROCHEN=1
    echo "" >&2
    echo "Abbruch: beende die Aufnahme sauber ..." >&2
    docker exec "$CONTAINER" pkill -INT -f "$MUSTER" 2>/dev/null || true
}
trap abbruch INT TERM

START_ISO=$(date -Iseconds)
echo "Aufnahme: $BAG_HOST (${DAUER} s, ${#TOPICS[@]} Topics)"
# Im Hintergrund, damit 'wait' bei Ctrl+C sofort zur Abbruchbehandlung kehrt;
# Hintergrundbefehle ignorieren SIGINT, docker exec laeuft also bis zum Ende.
docker exec "$CONTAINER" /entrypoint.sh timeout -s INT --kill-after="${KILL_AFTER_S}" "$DAUER" \
    ros2 bag record -s sqlite3 --qos-profile-overrides-path "$QOS_CONTAINER" \
    -o "$BAG_CONTAINER" "${TOPICS[@]}" &
REC_PID=$!
RC=0
while :; do
    set +e
    wait "$REC_PID"
    RC=$?
    set -e
    kill -0 "$REC_PID" 2>/dev/null || break
done
trap - INT TERM

# --- Nachbereitung -------------------------------------------------------------
if ! docker exec "$CONTAINER" test -f "$BAG_CONTAINER/metadata.yaml"; then
    echo "FEHLER: Aufnahme unvollstaendig, metadata.yaml fehlt (Exit $RC)." >&2
    docker exec "$CONTAINER" chown -R "$(id -u):$(id -g)" "$BAG_CONTAINER" 2>/dev/null || true
    exit 1
fi
case "$RC" in
    0 | 124 | 130) ;; # 124: Dauer erreicht; 0 oder 130: Ende nach SIGINT
    *) echo "WARNUNG: Recorder endete mit Exit $RC; metadata.yaml liegt vor." >&2 ;;
esac

META_ARGS=(--metadaten "$BAG_CONTAINER" --szene "$SZENE" --launch-zeile "$LAUNCH_ZEILE"
    --start "$START_ISO" --dauer "$DAUER" --host "$(hostname)" --git-commit "$GIT_COMMIT"
    --git-dirty "$GIT_DIRTY" --image-id "$IMAGE_ID")
for pfad in "${GIT_AENDERUNGEN[@]}"; do
    META_ARGS+=("--git-aenderung=$pfad")
done
if [ "$ABGEBROCHEN" -eq 1 ]; then
    META_ARGS+=(--abgebrochen)
fi
in_container python3 "$BAG_CHECK_CONTAINER" "${META_ARGS[@]}"

CRC=0
if [ "$CHECK" -eq 1 ]; then
    set +e
    in_container python3 "$BAG_CHECK_CONTAINER" "$BAG_CONTAINER" -o "$BAG_CONTAINER/bag_check.md"
    CRC=$?
    set -e
fi
docker exec "$CONTAINER" chown -R "$(id -u):$(id -g)" "$BAG_CONTAINER"

if [ "$CHECK" -eq 1 ] && [ -f "$BAG_HOST/bag_check.md" ]; then
    ZIEL="$REPO_DIR/validation/P-AD1/$NAME"
    mkdir -p "$ZIEL"
    cp "$BAG_HOST/bag_check.md" "$BAG_HOST/metadata_amr.yaml" "$ZIEL/"
    echo "Bericht: $ZIEL/bag_check.md"
fi
case "$CRC" in
    0) [ "$CHECK" -eq 1 ] && echo "bag_check: ohne Befund" ;;
    1) echo "bag_check: Befund, siehe Bericht" >&2 ;;
    *) echo "bag_check: Fehler (Exit $CRC)" >&2 ;;
esac
echo "Fertig: $BAG_HOST ($(du -sh "$BAG_HOST" | cut -f1))"
