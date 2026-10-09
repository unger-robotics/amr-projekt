# Testanleitung K7-V J5: Referenzaufnahmen a bis c

Anleitung fuer die Aufnahme der Referenzszenen a, b und c auf dem Pi 5 (Schritt J5 aus `transfer/auftrag-k7v.md`). Szenenkatalog, Topicliste und Werkzeuge stehen in `docs/ros2/referenz-bags.md`, Stand und Befunde in `docs/plan/bericht-k7v-phase1-4.md`.

---

## Ueberblick

- Drei Aufnahmen zu je 60 s in zwei Stack-Durchgaengen, Zeitbedarf ca. 45 min.
- Ergebnis: drei Ordner unter `~/amr_bags/<JJJJMMTT_HHMM>_<szene>/` und drei Berichte unter `validation/P-AD1/`.
- Zweck: Ab K7 wird die Funktionskette gegen diese Aufnahmen entwickelt, ohne dass der Roboter laeuft. Die Szenen werden spaeter gleich aufgebaut wiederholt (Vorher-Nachher-Vergleich); der Aufbau muss deshalb reproduzierbar sein.
- Stackstart und Fahrversuch fuehrt der Bediener aus; Claude Code loest keine Fahrbewegung aus (Freigaberegeln in `CLAUDE.md`).

## Voraussetzungen

- Pi 5 mit aktuellem Repo-Stand (`git pull`, `git status` ohne Aenderungen), `~/amr_bags` vorhanden
- Akku geladen
- Beide ESP32-S3 per USB angeschlossen, Kamera-Bridge aktiv (`camera-v4l2-bridge.service`)
- Material: Hindernis fuer Szene a, Klebeband, Massband, Kamera oder Handy fuer Fotos
- Fuer Szene b: freie, ebene Strecke von mindestens 2,5 m ohne Kanten und Stufen

## Szenen

| Szene | Zweck | Aufbau | Ablauf in den 60 s | Launch-Argumente zusaetzlich zum Standard |
|---|---|---|---|---|
| `a_stand` | Grundrauschen der Sensoren, Falschalarme, Existenz eines ruhenden Objekts (Winner 20.2.2) | Roboter auf dem Boden, Hindernis frontal in 1,0 m, niemand im Raum | nichts; der Bediener verlaesst den Raum | `use_camera:=True use_dashboard:=True use_vision:=True` |
| `c_person` | Tracking, ID-Stabilitaet, Praediktion (Winner 20.2.3, ACDC S3) | wie a, aber ohne Hindernis | eine Person quert dreimal in 1,5 m Abstand das Kamerabild, normales Gehtempo | wie a |
| `b_nav2` | Lokalisierung Odometrie gegen SLAM (ACDC S2b), Folgefehler von Regulated Pure Pursuit (ACDC S4, Winner Gl. 34.13) | freie Strecke, Start- und Zielmarke im Abstand von 2 m | Nav2-Ziel 2 m geradeaus, Fahrt ca. 15 s, danach Stand | keine |

### Szene a: Stand, statisch

- Roboter auf dem Boden, nicht aufgebockt. Aufgebockt meldet `/cliff` dauerhaft true, und `/range/front` springt (Probeaufnahmen vom 2026-10-08).
- Hindernis mindestens ca. 30 cm hoch und 30 cm breit, damit es alle Sensoren erfassen. Die LiDAR-Ebene liegt bei 23,5 cm, der Ultraschall bei 5 cm; sein Oeffnungswinkel von 0,26 rad ist in 1 m Abstand ca. 26 cm breit.
- Empfehlung: ein Objekt, das die Objekterkennung kennt (COCO-Klasse, z. B. Koffer). Dann erfassen LiDAR, Ultraschall und Kamera dasselbe Objekt.
- Abstand ab Roboterfront messen, Position von Roboter und Hindernis mit Klebeband markieren.
- Konstantes Licht. Niemand im Raum, denn der LiDAR erfasst den ganzen Raum.

### Szene c: Person quert

- Roboter wie in Szene a, Hindernis entfernen, weil es die Person verdecken wuerde.
- Weg quer vor dem Roboter in 1,5 m Abstand markieren. Anfang und Ende liegen seitlich ausserhalb des Kamerabilds.
- Drei Durchgaenge bei ca. 10 s, 25 s und 40 s nach Aufnahmestart, abwechselnd von links nach rechts und zurueck. Zwischen den Durchgaengen ausserhalb des Kamerabilds warten.
- Der Bediener kann selbst gehen: Skript starten, dann laufen.

### Szene b: Nav2-Fahrt

- Start- und Zielmarke im Abstand von 2 m mit Klebeband markieren. Roboter auf die Startmarke stellen, Front entlang der Strecke.
- Nach dem Stackstart den Roboter nicht mehr beruehren. Die Karte beginnt an der Startpose; das Ziel `x = 2,0` liegt damit 2 m geradeaus.
- Fahrgeschwindigkeit 0,15 m/s (`desired_linear_vel`), Fahrt ca. 15 s.

**Sicherheit:** Waehrend der Nav2-Fahrt wirkt die Sicherheitslogik nicht zuverlaessig. Neben `cliff_safety_node` publiziert auch `velocity_smoother` auf `/cmd_vel` (BA-03, SIA-15 offen bis K9). Deshalb:

- Strecke frei von Hindernissen, Kanten und Stufen; niemand im Fahrweg.
- Abbruch: Ctrl+C im Terminal mit dem Fahrziel (T5) bricht das Ziel ab.
- Bereit sein, von Hand einzugreifen.

### Aufbau dokumentieren

Je Szene ein Foto und kurze Notizen: Objekt, Abstaende, Weg, Boden, Licht. Die Notizen gehen bei J6 in den Bericht ein und machen spaetere Wiederholungen vergleichbar.

## Durchgang 1: Szenen a und c

### Stack starten

```bash
# T1: ESP32-Reset (die seriellen Ports muessen frei sein, kein micro_ros_agent darf laufen)
cd ~/amr-projekt
python3 -c "import serial,time;[exec('s=serial.Serial(p,921600);s.dtr=False;s.rts=True;time.sleep(0.1);s.dtr=True;s.rts=False;s.close()') for p in ['/dev/amr_drive','/dev/amr_sensor']]"

# T2: Stack mit den Argumenten der Szenen a und c (woertlich, mit grossem T)
cd ~/amr-projekt/amr/docker
./run.sh ros2 launch my_bot full_stack.launch.py use_camera:=True use_dashboard:=True use_vision:=True

# T3: Hailo-Runner auf dem Host, erst wenn T2 laeuft
cd ~/amr-projekt && python3 amr/scripts/host_hailo_runner.py
```

### Kurzpruefung vor der ersten Aufnahme

```bash
# T4
cd ~/amr-projekt/amr/docker && ./run.sh exec bash
ros2 topic hz /vision/detections   # ca. 5 Hz, mit Ctrl+C beenden
ros2 topic hz /imu                 # ca. 38 Hz, mit Ctrl+C beenden
exit
```

Fehlen `/imu` oder `/range/front`, ist die Sensor- und Sicherheitsbasis nicht verbunden: ESP32-Reset bei laufendem Stack wiederholen.

### Szene a

Hindernis aufstellen, dann:

```bash
cd ~/amr-projekt && amr/scripts/record_reference_bags.sh a_stand 60
```

Die Aufnahme beginnt ohne Countdown mit der Zeile `Aufnahme: ...`. Danach den Raum verlassen und nach ca. 80 s zurueckkommen.

### Szene c

Hindernis entfernen, dann:

```bash
amr/scripts/record_reference_bags.sh c_person 60
```

Ab der Zeile `Aufnahme: ...` zaehlen und bei ca. 10, 25 und 40 s queren.

### Durchgang beenden

Zuerst T3 mit Ctrl+C beenden, sonst bleibt `/dev/hailo0` gesperrt. Danach T2 mit Ctrl+C beenden und pruefen:

```bash
docker exec amr_ros2 pgrep -a micro_ros_agent   # Ausgabe muss leer sein
```

Laeuft noch ein Agent (B-V11), ihn mit `docker exec amr_ros2 pkill -INT -f micro_ros_agent` beenden.

## Durchgang 2: Szene b

Roboter auf die Startmarke stellen.

```bash
# T1: ESP32-Reset wie in Durchgang 1 (nach jedem Stopp noetig, micro-ROS verbindet nicht neu)

# T2: Stack mit Standardargumenten
cd ~/amr-projekt/amr/docker && ./run.sh ros2 launch my_bot full_stack.launch.py
```

In T2 auf `Managed nodes are active` warten; dann ist Nav2 bereit. Den Roboter ab jetzt nicht mehr beruehren.

```bash
# T5: Shell fuer das Fahrziel vorbereiten
cd ~/amr-projekt/amr/docker && ./run.sh exec bash

# T4: Aufnahme starten
cd ~/amr-projekt && amr/scripts/record_reference_bags.sh b_nav2 60

# T5: innerhalb von ca. 5 s nach der Zeile "Aufnahme: ..." das Ziel setzen
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0}, orientation: {w: 1.0}}}}"
```

Erwartet in T5: `Goal accepted` und nach ca. 15 s `Goal finished with status: SUCCEEDED`. Nach dem Ende der Aufnahme T2 mit Ctrl+C beenden.

Muss Szene b wiederholt werden, den Stack mit ESP32-Reset neu starten und den Roboter vorher auf die Startmarke zurueckstellen.

## Ergebnis pruefen

Das Skript endet mit diesen Zeilen:

```
Bericht: .../validation/P-AD1/<JJJJMMTT_HHMM>_<szene>/bag_check.md
bag_check: ohne Befund
Fertig: /home/pi/amr_bags/<JJJJMMTT_HHMM>_<szene> (... MB)
```

Bei `bag_check: Befund` den Bericht oeffnen; unter "Fehlende erwartete Topics" steht, was fehlt.

| Meldung | Ursache | Abhilfe |
|---|---|---|
| `ABWEICHUNG: use_...` (vor der Aufnahme) | Launch-Argument abweichend, z. B. `true` statt `True` | Stack mit den Argumenten der Szene neu starten |
| `FEHLENDES TOPIC: /imu`, `/range/front` ... | Sensor- und Sicherheitsbasis nicht verbunden | ESP32-Reset bei laufendem Stack |
| `FEHLENDES TOPIC: /plan`, `/lookahead_point` | Nav2 noch nicht aktiv | kurz warten, Skript erneut starten |
| `/vision/detections (0 Nachrichten)` | Hailo-Runner lief nicht | T3 starten, Szene wiederholen |
| Szene b: `/plan`, `/nav_cmd_vel` oder `/pose` mit 0 Nachrichten | Ziel zu spaet oder nicht gesetzt | Stack neu starten (mit ESP32-Reset), Roboter auf die Startmarke, Szene wiederholen |
| `... existiert bereits` | dieselbe Szene zweimal in derselben Minute | eine Minute warten |

Fehlversuche und abgebrochene Aufnahmen (Ctrl+C, `abgebrochen: true` in `metadata_amr.yaml`) nicht committen: den Ordner unter `validation/P-AD1/` loeschen und die Szene wiederholen.

Im Bericht zusaetzlich pruefen:

- Bewertung nach L1 v1.1, Abschnitt 10.2: `/odom` >= 10 Hz (NFA-03), `/scan` >= 5 Hz (NFA-02), `/imu` >= 20 Hz (NFA-04) und `/range/front` >= 7 Hz, jeweils mit eingehaltener Regressionstoleranz
- Szenen a und c: `capture_time <= timestamp` in 100 % der Pakete, `seq` ohne Luecken und ohne Ruecksprung
- Szene b: `/plan`, `/nav_cmd_vel`, `/lookahead_point` und `/pose` mit Nachrichten

## Optional: Messung zu B-V12

Waehrend Szene a in einem weiteren Terminal den CAN-Bus passiv mitschreiben; `candump` sendet nichts:

```bash
candump -t A can0 > ~/amr_bags/candump_a_stand.log   # nach der Aufnahme mit Ctrl+C beenden
```

Bezug: Messvorschlag 1 in `docs/plan/bericht-k7v-phase1-4.md`, Anhang C.2.

## Abschluss

```bash
cd ~/amr-projekt
git add validation/P-AD1/
git commit -m "test(k7v): Referenzaufnahmen a bis c (J5)"
git push
```

Danach folgt J6: Berichte pruefen, Abweichungen markieren, Aufbau-Notizen uebernehmen, Tag `k7v-refbags-v1` setzen und im Phasenplan "Stand" auf "erledigt" aendern.
