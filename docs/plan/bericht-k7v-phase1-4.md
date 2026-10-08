# Bericht K7-V Phase 1–4 – Umsetzung und Nachweise

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Abschlussbericht zum Claude-Code-Auftrag K7-V (`transfer/auftrag-k7v.md`, Version 1.0), Phase 1 bis 4 |
| Version | 1.0 |
| Datum | 2026-10-08 |
| Autor | Jan (Bericht erstellt mit Claude Code) |
| Bezug | `docs/plan/bericht-k7v-phase0.md` (Phase 0, Befunde B-V1 bis B-V11), `docs/plan/phasenplan-v2.md` (v2.2, K7), `docs/anforderungsliste-L1.md` (v1.1) |
| Freigaben | J2 am 2026-10-08, ohne Streichungen. Auf Rueckfrage festgelegt: B-V9 erst messen; ein gemeinsamer Stacklauf fuer den Phase-2-Nachweis und die Probeaufnahme. Stacklauf am 2026-10-08, 23:32 bis 23:36 MESZ, Roboter aufgebockt, keine Fahrbefehle |
| Status | Phase 1–4 umgesetzt, geprueft und in vier Commits abgelegt (Abschnitt 2.6). Offen sind J3 (Mac/iMac), J5 (Szenen a bis c) und J6 (Review, Tag `k7v-refbags-v1`) |

## 1 Kurzfassung

- **Entwicklungsumgebung (Phase 1):** `amr/docker/docker-compose.dev.yml` laeuft ohne Geraete und isoliert. Auf dem Pi ist sie ohne Neubau geprueft: Paketbau, Aufnahme, `bag info` und `bag play`. Die Pi-Compose-Datei bindet jetzt `src/` und `~/amr_bags` ein; `verify.sh` liefert davor und danach dieselbe Ausgabe.
- **Erfassungszeit (Phase 2):** `capture_time <= timestamp` gilt in 100 % der Pakete (297 von 297). `timestamp - capture_time` liegt im Median bei 38,0 ms, P95 bei 40,4 ms. `seq` laeuft ohne Luecke und ohne Ruecksprung.
- **Referenz-Bags (Phase 3):** `record_reference_bags.sh` und `bag_check` sind fertig. Beide Probeaufnahmen (60 s und 10 s) sind ohne Befund. NFA-02 (`/scan` 7,57 Hz) und NFA-03 (`/odom` 20,00 Hz) sind erfuellt, alle Regressionstoleranzen nach L1 Abschnitt 10.2 eingehalten.
- **B-V9 korrigiert:** BuildKit uebertraegt nur die Quellen der COPY-Befehle (gemessen 99 B bzw. 2,72 kB bei 2,2 GB Repo). `.env` gelangt nie in den Build. Keine Dateiaenderung.
- **Neuer Befund B-V12:** Die Sensor- und Sicherheitsbasis setzte in 60 s zwoelfmal fuer 0,2 bis 0,4 s gleichzeitig auf `/imu`, `/cliff` und `/range/front` aus. Der Fahrkern ist nicht betroffen.

## 2 Nachweise nach Abschnitt 3 des Auftrags

### 2.1 Phase-0-Bericht a–g

Er liegt in `docs/plan/bericht-k7v-phase0.md` (Commit 73b0198). J2 ist erteilt, der Kopf des Berichts ist nachgetragen.

### 2.2 Aenderungen je Datei

| Datei | Phase | Befund | Aenderung |
| --- | --- | --- | --- |
| `amr/docker/docker-compose.dev.yml` (neu) | 1 | B-V4 | Gleiches Image, Projekt `amr-dev`, Container `amr_ros2_dev`. Keine Geraete, kein `privileged`, Bridge-Netz, `ROS_DOMAIN_ID=42`, `ROS_LOCALHOST_ONLY=1`. Mounts: `src/` (rw), `scripts/` (ro), `~/amr_bags` (ro); eigene Build-Volumes |
| `amr/docker/docker-compose.yml` | 1 | B-V4 | `../pi5/ros2_ws/src:/ros2_ws/src:rw` statt `src/my_bot`; neu `${HOME}/amr_bags:/amr_bags:rw` |
| `amr/docker/README.md` | 1 | B-V4 | Volume-Tabelle nachgezogen (mit dem bisher fehlenden `mcu_firmware`); Abschnitt "Entwicklung ohne Roboter" mit Sicherheitsregel |
| `docs/ros2_system.md`, `docs/architecture.md`, `docs/architecture/system-overview.md`, `docs/systemdokumentation.md` | 1, 4 | B-V4 | Mount-Doku nachgezogen; Zahl der Executables 31 statt 29 |
| `amr/scripts/host_hailo_runner.py` | 2 | B-V1, B-V7 | `capture_time` direkt nach `cap.read()`, `seq` ab 0 je Start; der Fallback liefert nur `seq`; `timestamp` unveraendert; Docstring |
| `amr/scripts/hailo_udp_receiver_node.py` | 2 | B-V2 | Nur der Docstring; Code, Topic, Typ und QoS unveraendert |
| `my_bot/config/reference_bags.yaml` (neu) | 3 | B-V6, B-V10 | Topicliste (17 Topics), Szenen `a_stand`, `b_nav2`, `c_person`, `probe`, Bewertung nach L1 Abschnitt 10.2 |
| `my_bot/config/reference_bags_qos.yaml` (neu) | 3 | B-V6 | `/tf_static` und `/map` als transient_local |
| `amr/scripts/record_reference_bags.sh` (neu) | 3 | B-V10, B-V11 | Vorpruefungen (Container, Mount, Launch-Argumente woertlich, Topics), Aufnahme mit sqlite3, sauberer Abbruch, `metadata_amr.yaml`, bag_check |
| `amr/scripts/bag_check.py` (neu), Symlink in `my_bot/my_bot/`, `setup.py` | 3 | B-V5, B-V6 | Auswertung und Bericht; Hilfsmodi fuer das Aufnahmeskript |
| `validation/P-AD1/` (neu) | 3 | – | `README.md` und die Berichte der beiden Probeaufnahmen |
| `tests/test_bag_check.py` (neu) | 4 | – | 18 Tests (17 bestanden; die Katalogpruefung uebersprungen, weil `.venv` kein PyYAML hat; im Container separat geprueft) |
| `docs/ros2/referenz-bags.md` (neu), `mkdocs.yml` | 4 | B-V3, B-V7 | Seite "Referenzaufnahmen" unter "ROS 2 (Raspberry Pi 5)" |
| `docs/vision_pipeline.md` | 4 | B-V1, B-V2, B-V7 | Abschnitt "Detektions-JSON" mit Feldtabelle |
| `docs/plan/phasenplan-v2.md` | 4 | B-V3, B-V8 | Unter K7 ergaenzt: Stand K7-V, offener Punkt Zeitbasis, ID-Kollision |
| `docs/plan/bericht-k7v-phase0.md` | 4 | – | Kopf: J2 erteilt |
| `.gitignore` | 4 | – | `*.mcap`, `*.db3-*`, `amr_bags/` |
| `mypy.ini` | 4 | – | `[mypy-yaml.*]` fuer den mypy-Hook von pre-commit |
| `CLAUDE.md` | 4 | – | Fallstrick: Referenzaufnahmen nur im dev-Container abspielen |

### 2.3 Nachweis Phase 2 (Erfassungszeit und Sequenznummer)

Die Werte stammen aus der Aufnahme `20261008_2334_probe` (60 s, aktive Objekterkennung mit Hailo-8L, Inferenz etwa 35 ms). Ausgewertet hat `bag_check`.

| Kenngroesse | Wert |
| --- | --- |
| Pakete mit `capture_time` und `seq` | 297 von 297 (davon 56 mit Objekten) |
| `capture_time <= timestamp` | 100,0 % (297/297) |
| `timestamp - capture_time` (Verarbeitung im Runner) | Median 38,0 ms, P95 40,4 ms, Max 68,9 ms |
| Aufnahmezeit minus `timestamp` (UDP und ROS) | Median 5,8 ms, P95 10,2 ms, Max 12,1 ms |
| Aufnahmezeit minus `capture_time` (gesamt ab Entnahme) | Median 44,1 ms, P95 48,9 ms, Max 74,5 ms |
| `seq` | 136 bis 432; 0 fehlend, 0 Ruecksprunge |

Die 10-s-Aufnahme bestaetigt das: 39 von 39, Median 37,9 ms, P95 39,8 ms, `seq` lueckenlos.

**Einordnung:**

- `capture_time` ist die Entnahme im Runner. Wegen des gepufferten MJPEG-Stroms ist sie nur eine Obergrenze des Bildzeitpunkts und keine Sensorzeit (B-V7).
- Das Alter des Bildes vor `cap.read()` ist nicht gemessen.
- Eine typisierte Nachricht gibt es in K7-V nicht, weil `vision_msgs` im Image fehlt (B-V6). Sie kommt mit `amr_chain_msgs` in K7.

### 2.4 bag_check-Bericht der Probeaufnahme

Die vollstaendigen Berichte liegen in `validation/P-AD1/20261008_2335_probe/bag_check.md` (10 s) und `validation/P-AD1/20261008_2334_probe/bag_check.md` (60 s).

**Ergebnis:**

- Beide Aufnahmen haben keine fehlenden erwarteten Topics und keine Typabweichungen.
- Damit sind auch die Typen von `/pose` (PoseWithCovarianceStamped) und `/lookahead_point` (PointStamped) bestaetigt. Beide tragen im Stand erwartungsgemaess keine Nachrichten.
- Der Bericht entsteht auf dem Pi und im dev-Container byteweise gleich.

**Bewertung nach L1 v1.1, Abschnitt 10.2** (60 s, mittlere Rate):

| Groesse | Anforderung | K0-Baseline | Messwert | Ergebnis |
| --- | --- | --- | --- | --- |
| `/odom` | NFA-03: >= 10 Hz | 19,85 Hz | 20,00 Hz | erfuellt; Toleranz eingehalten (Grenze 15,00 Hz) |
| `/scan` | NFA-02: >= 5 Hz | 7,51 Hz | 7,57 Hz | erfuellt; Toleranz eingehalten (Grenze 5,00 Hz) |
| `/imu` | NFA-04: >= 20 Hz | 38,07 Hz | 38,86 Hz | erfuellt; Toleranz eingehalten (Grenze 28,55 Hz) |
| `/range/front` | DoD Phase 2: >= 7,0 Hz | 9,06 Hz | 9,07 Hz | erfuellt; Toleranz eingehalten (Grenze 7,00 Hz) |
| `/battery` | keine eigene | 2,00 Hz | 2,00 Hz | Toleranz eingehalten (Grenze 1,50 Hz) |
| `/cliff` | keine eigene | 15,86 Hz | 16,14 Hz | kein Kriterium (OP-11) |
| `/cmd_vel` | keine eigene | 20,00 Hz | 21,45 Hz | kein Kriterium (OP-11) |

**Groessen:**

- 60 s ergeben 9,72 MB; die Speicherschaetzung aus Phase 0 f (12 bis 29 MB) war damit zu hoch angesetzt.
- Den Hauptanteil haben `/scan` mit 5,21 MB und `/map` mit 1,17 MB (Karte 9,8 kB je Nachricht).

### 2.5 Abweichungen vom Auftrag

Mit J2 freigegeben sind die Punkte 1 bis 9 und 11 aus Abschnitt 5 des Phase-0-Berichts. Hinzu kommen:

1. **B-V9:** gemessen statt behoben, auf Rueckfrage (Abschnitt 4).
2. **Phase-2-Nachweis:** Ihn liefert `bag_check` im gemeinsamen Stacklauf nach Phase 3 (Rueckfrage). Ein Reset der ESP32 statt zwei.
3. **Probeszene:** Sie laeuft mit den Argumenten von Szene a, damit `/vision/detections` mitgeprueft wird. Statt einer Probeaufnahme gibt es zwei, 60 s und 10 s.
4. **Wiedergaberegel:** Sie ist strenger als im Phase-0-Bericht und kennt keinen Ausweg per Remap. Grund: `/nav_cmd_vel` und `/dashboard_cmd_vel` werden im laufenden Stack auf `/cmd_vel` weitergeleitet.
5. **Aufnahmeskript, Abbruch bei Abweichung:** Weichen die Launch-Argumente ab oder fehlen Topics, bricht das Skript ab, statt nur zu warnen. `--force` uebergeht das; die Abweichungen stehen dann in `metadata_amr.yaml`.
6. **Aufnahmeskript, Bericht:** Das Skript ruft `bag_check` gleich mit auf und legt den Bericht in `validation/P-AD1/` ab.
7. **Folgeaenderungen:** In der Doku sind Mounts und die Zahl der Executables nachgezogen, dazu kommen `validation/P-AD1/README.md`, die Zeile in `CLAUDE.md` und `[mypy-yaml.*]` in `mypy.ini`.
8. **`amr_ros2`:** Der Container wurde in Phase 1 neu angelegt, aber nicht gestartet. Die ROS-Logs des alten Containers liegen in `~/amr_logs/amr_ros2_bis_20261008/`; darin ist das Launch-Protokoll zu B-V11.
9. **Phasenplan:** Er nennt "Stand" statt "erledigt", weil die Referenz-Bags a bis c (J5) und der Tag (J6) noch offen sind.
10. **`/tf`:** Sollrate und Luecken werden je Kante bewertet, nicht auf Topic-Ebene, weil auf `/tf` zwei Publisher senden.

### 2.6 Commits und Tag

Auf Anweisung vom 2026-10-08 sind vier Commits angelegt, je einer pro Phase:

1. `feat(docker): Entwicklungsumgebung ohne Roboter (K7-V Phase 1)` mit den Compose-Dateien, der README und der Mount-Doku.
2. `feat(vision): Erfassungszeit und Sequenznummer im Detektions-JSON (K7-V Phase 2)` mit Runner, Empfaenger und `mypy.ini`. Der Abschnitt `[mypy-yaml.*]` ist vorgezogen, weil der mypy-Hook alle Dateien prueft, also auch das zu diesem Zeitpunkt noch nicht committete `bag_check.py`.
3. `feat(bags): Referenzaufnahmen und bag_check (K7-V Phase 3)` mit Katalog, Skripten, Entry-Point, `validation/P-AD1/` und Tests.
4. `docs(k7v): Doku und Abschlussbericht Phase 1-4 (K7-V Phase 4)` mit den uebrigen Doku-Dateien, `.gitignore` und `CLAUDE.md`.

Den Tag `k7v-refbags-v1` setzt Jan erst nach J5/J6, also nach den Szenen a bis c und dem Review.

## 3 Messwerte: Stempelabstand je Sensor

Gemessen wurde die Aufnahmezeit minus Stempel in ms, Aufnahme `20261008_2334_probe`, 60 s, etwa 1 min nach dem Zeitsync. Die Werte sind der Eingang fuer das Latenzbudget von K7.

| Topic / Kante | Zeitbasis | N | Min | Median | P95 | Max |
| --- | --- | --- | --- | --- | --- | --- |
| `/scan` | Pi (rplidar_node) | 450 | 118,8 | 134,7 | 136,3 | 138,8 |
| `/odom` | MCU Fahrkern | 1189 | -3,7 | -1,8 | -0,4 | 27,5 |
| `/tf odom->base_link` | MCU Fahrkern (aus /odom) | 1189 | -2,5 | -0,6 | 1,4 | 28,4 |
| `/imu` | MCU Sensor- und Sicherheitsbasis | 2240 | -3,3 | -1,6 | -0,3 | 99,4 |
| `/range/front` | MCU Sensor- und Sicherheitsbasis | 523 | -3,4 | -2,1 | -0,6 | 96,3 |
| `/battery` | MCU Sensor- und Sicherheitsbasis | 115 | -3,4 | -2,2 | -0,9 | 96,9 |
| `/map` | Pi (slam_toolbox) | 120 | 129,2 | 202,1 | 262,1 | 354,6 |
| `/tf map->odom` | Pi (slam_toolbox) | 1189 | -376,8 | -301,9 | -242,2 | -228,5 |

Die Werte stimmen mit Phase 0 c ueberein (`/scan` 135,1 ms, map->odom -302,1 ms). Die MCU-Stempel liegen nach frischem Sync etwa 2 ms vor der Empfangszeit. Ungesyncte Stempel kamen nicht vor.

## 4 Befunde

| Nr. | Ergebnis | Beleg |
| --- | --- | --- |
| B-V9 (korrigiert) | **Folgenlos beim Bau mit BuildKit.** BuildKit uebertraegt nur die Quellen der COPY-Befehle. Probe-Build ohne Image (`FROM scratch`, lokale Ausgabe): 99 B fuer `entrypoint.sh` (im Cache), 2,72 kB fuer eine neue Datei mit 2605 B, bei 2,2 GB Repo. Ein Kontext von 2,2 GB einschliesslich `.env` faellt nur beim Legacy-Builder an (`DOCKER_BUILDKIT=0`). `amr/docker/.dockerignore` bleibt wirkungslos, aber ohne Folgen | Probe-Build am 2026-10-08 im Scratchpad, kein Image erzeugt |
| B-V11 (bestaetigt) | Nach SIGINT an `ros2 launch` liefen beide `micro_ros_agent` weiter; erst `docker stop` beendete sie (Exit 137). **Vor dem naechsten Stackstart ist ein ESP32-Reset (T1) noetig** | `ps` im Container, 23:36 |
| B-V12 (neu) | **Aussetzer der Sensor- und Sicherheitsbasis.** In 60 s traten zwoelf Luecken von 0,2 bis 0,4 s auf, jeweils innerhalb von etwa 100 ms auf `/imu`, `/cliff` und `/range/front` zugleich, groesste 404 ms. Der Fahrkern (`/odom`, groesster Abstand 75 ms) ist nicht betroffen. Die Nachrichten nach einer Luecke sind hoechstens etwa 100 ms alt (Stempelabstand); waehrend der Luecke wurde also nicht publiziert. Ein verzoegerter Transport zeigte dagegen grosse Stempelabstaende. Ursache offen; fuer das Latenzbudget in K7 ist das relevant (IMU-Mindestrate 2,5 Hz statt 38 Hz) | Ad-hoc-Auswertung der Aufnahme `20261008_2334_probe` (Abstaende > 200 ms je Topic) |

**Nebenbefunde:**

- **`/range/front`:** Aufgebockt springt der Wert zwischen 0,1 cm und frei; `cliff_safety_node` meldet abwechselnd "HINDERNIS bei 0.1 cm" und "frei". Das ist bekannt aus S-A (0,001 m und 4,01 m). `/cliff` ist aufgebockt dauerhaft true (BA-04).
- **`/cmd_vel`:** 21,45 Hz statt 20 Hz. Es gibt zwei Publisher (BA-03), und `velocity_smoother` sendet auch ohne Nav2-Ziel.
- **Gemini:** `gemini_semantic_node` wartet auf `/vision/enable`, den AI-Schalter der Benutzeroberflaeche. Ohne ihn gab es im Stacklauf keine Gemini-Anfragen.
- **Pruefwerkzeuge:**
  - `pre-commit run --all-files` scheitert bereits am Stand HEAD: `end-of-file-fixer` will in `transfer/info.md` zwei Leerzeilen am Ende entfernen. Die Datei wurde nach dem Lauf auf HEAD zurueckgesetzt und ist nicht Teil von K7-V.
  - Das System-mypy (python-can 4.6.1) meldet zwei Altfehler in `amr/scripts/can_validation_test.py`; der mypy-Hook von pre-commit ist gruen.
- **rosbag2:** `bag_size` zaehlt in Humble den ganzen Ordner mit, also auch `bag_check.md` und `metadata_amr.yaml`. bag_check summiert deshalb nur die db3-Dateien.
- **Runner:** Der Systemdienst `hailort_service` lief, behinderte den Runner aber nicht.

## 5 Offene Schritte (Jan)

| Nr. | Schritt | Hinweis |
| --- | --- | --- |
| J3 | dev-Compose auf Mac (arm64) und iMac (x86_64): `build`, `up -d`, `colcon build`, `ros2 bag info` | Bedienung in `amr/docker/README.md`. Der Selbsttest braucht keine Aufnahme vom Pi; alternativ eine Probeaufnahme per `rsync` holen. Auf dem iMac nach Commit und Push per `git pull`, das MacBook ist eine rsync-Kopie |
| J5 | Szenen a, b und c mit `amr/scripts/record_reference_bags.sh <szene> 60` | Vorher ESP32-Reset (B-V11). Launch-Argumente genau wie im Katalog; a und c mit `use_camera:=True use_dashboard:=True use_vision:=True`, b mit Standardargumenten. Das Nav2-Ziel in b setzt Jan selbst |
| J6 | Berichte in `validation/P-AD1/` pruefen, Abweichungen markieren, Tag `k7v-refbags-v1` setzen | Dann im Phasenplan "Stand" zu "erledigt" aendern |

## Anhang A – Pruefprotokoll

| Pruefung | Ergebnis |
| --- | --- |
| `./verify.sh` vor und nach dem Mount-Wechsel | identische Ausgabe: PASS 14, FAIL 0, WARN 2 (die beiden WARN betreffen die udev-Symlinks im Einmal-Container, wie bisher) |
| dev-Compose auf dem Pi (`up -d --no-build`) | `Privileged=false`, 0 Devices, Netz `amr-dev_default`, Domain 42, localhost only, kein API-Schluessel; `colcon build`; 49 Nachrichten aufgenommen; `bag play` mit Exit 0; `/amr_bags` nur lesbar |
| `bag_check` gegen synthetische Aufnahme (dev-Container) | bekannte Eingaben richtig erkannt: `/scan` -120 ms, map->odom +0,3 s, ungesyncte Stempel, latched `/tf_static` und `/map`, JSON 80 ms |
| Abbruch des Aufnahmeskripts (Mechanik im dev-Container nachgestellt) | SIGINT nach 7 s; Aufnahme endet nach 1 s mit `metadata.yaml` (6,1 s, 62 Nachrichten) |
| Fallback-Modus des Runners (offline, UDP-Empfaenger im Scratchpad) | `seq` 0 bis 10 lueckenlos, `timestamp` vorhanden, kein `capture_time` |
| `ruff check amr/`, `ruff format --check amr/` | gruen (ruff 0.15.6 und pre-commit-ruff 0.9.10) |
| `mypy --config-file mypy.ini` | gruen bis auf die zwei Altfehler in `can_validation_test.py`; pre-commit-Hook gruen |
| `pre-commit run` auf den geaenderten Dateien | alle Hooks gruen |
| `.venv/bin/python -m pytest tests/` | 82 bestanden, 1 uebersprungen |
| `mkdocs build --strict` | gruen |
