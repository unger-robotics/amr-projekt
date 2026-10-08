# Auftrag K7-V – Vorbereitung MZ2: Entwicklungsumgebung, Erfassungszeitstempel, Referenz-Bags

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Claude-Code-Auftrag und Ablauf fuer die Vorbereitung von K7 (Phasenplan v2.2, Abschnitt 5, Paket K7) |
| Version | 1.0 (Entwurf) |
| Datum | 2026-10-08 |
| Ablageort | transfer/auftrag-k7v.md (wie auftrag-k3.md) |
| Bezug Lernplan | Transferpaket T1 in Verzahnung-Winner-AMR.md (ACDC S1 "ROS Bags"; Winner 20.2.5, 47.3.1) |
| Eingangsbedingung | G0 erfuellt (Tag k2-dbc-v1); K2-Stand auf GitHub gepusht |
| Ausgangsbedingung | Phase-0-Bericht freigegeben; docker-compose.dev.yml laeuft auf Mac/iMac ohne Hardware; /vision/detections traegt Erfassungszeit und Sequenznummer; Referenz-Bags (a), (b), (c) aufgenommen und mit bag_check geprueft; Tag k7v-refbags-v1 |

## 0 Zweck

K7 verlangt Schnittstellen mit Zeitstempel = Sensorzeit (SA-14) und ein gemessenes Latenzbudget (FA-22, T-12). Dafuer fehlen heute drei Dinge:

- eine Umgebung, in der die Kette ohne Roboter laeuft (Bag-Wiedergabe auf Mac/iMac),
- die Erfassungszeit der Kamera-Detektionen,
- ein fester Satz Referenzaufnahmen.

K7-V liefert genau das und aendert nichts am Fahrbetrieb.

Bekannte Befunde aus der Code-Durchsicht (in Phase 0 zu bestaetigen):

| Nr. | Befund | Fundstelle |
| --- | --- | --- |
| B-V1 | `timestamp` im Detektions-JSON wird mit `time.time()` erst nach Inferenz und Nachverarbeitung gesetzt, also Versandzeit | amr/scripts/host_hailo_runner.py (Hauptschleife, `payload`) |
| B-V2 | /vision/detections ist std_msgs/String ohne header.stamp und ohne Sequenznummer | hailo_udp_receiver_node.py |
| B-V3 | odom_to_tf.py stempelt den TF mit `get_clock().now()` statt mit dem Stempel der Odometrie | amr/scripts/odom_to_tf.py, Zeile 34 |
| B-V4 | docker-compose.yml bindet nur src/my_bot ein; Geraetepfade machen die Datei Pi-gebunden | amr/docker/docker-compose.yml |
| B-V5 | Die MCU-Knoten synchronisieren die Zeit (rmw_uros_sync_session) und stempeln /odom, /range/front, /imu mit Epoch-Zeit | drive_node/src/main.cpp, sensor_node/src/main.cpp |
| B-V6 | vision_msgs und das MCAP-Storage-Plugin sind nicht im Image; rosbag2 nutzt sqlite3 (Humble-Standard) | amr/docker/Dockerfile |

## 1 Reihenfolge – wer macht was

```
Jan                                    Claude Code
---------------------------------      ---------------------------------
1  K2-Stand pushen (O6)                Phase 0  Bestandsaufnahme (read-only)
2  Phase-0-Bericht freigeben                    -> Bericht a-g, STOPP
3  Mac/iMac: dev-Compose bauen         Phase 1  docker-compose.dev.yml,
   und Probelauf (J3)                           Mount src/ statt src/my_bot
4  Pi: Image neu bauen nur falls       Phase 2  Erfassungszeit + Sequenznummer
   Phase 2 das Dockerfile aendert               im Detektions-JSON
5  Referenz-Bags (a), (b), (c)         Phase 3  record_reference_bags.sh,
   aufnehmen (J5)                               bag_check.py
6  bag_check-Berichte pruefen,         Phase 4  Doku, Lint, Tests, Bericht
   Review, Tag k7v-refbags-v1
```

Phase 0 und 1 koennen sofort starten. Phase 2 aendert nur den Host-Runner und den Empfaengerknoten, nicht die Firmware. Phase 3 braucht Phase 2, weil Szene (c) die Erfassungszeit enthalten soll.

## 2 Jans Schritte im Detail

| Nr. | Schritt | Nachweis |
| --- | --- | --- |
| J1 | K2-Stand (Commit 7dd12bf, Tag k2-dbc-v1, amr_vehicle.dbc) nach GitHub pushen | `git log origin/main` zeigt den Tag |
| J2 | Phase-0-Bericht lesen, Freigabe fuer Phase 1-4 geben oder Punkte streichen | Freigabe im Chat |
| J3 | Auf Mac (arm64) und iMac (x86_64): `docker compose -f docker-compose.dev.yml build`, dann `colcon build --packages-select my_bot` und `ros2 bag info` auf einer Test-Aufnahme | Konsolenausgabe beider Rechner |
| J4 | Nur falls Phase 2 das Dockerfile aendert: `docker compose build` auf dem Pi (ca. 15-20 min), danach `./verify.sh` | verify.sh gruen |
| J5 | Referenzszenen auf dem Pi aufnehmen (Abschnitt 4). Szene (b) faehrt Jan selbst per Nav2-Ziel; Claude Code loest keine Fahrbewegung aus | drei Bag-Ordner unter ~/amr_bags/ |
| J6 | bag_check-Berichte pruefen, Abweichungen markieren, Tag setzen | bag_check-Berichte im Protokollordner |

## 3 Claude-Code-Auftrag K7-V

```
Implementiere ausschliesslich die Vorbereitung K7-V gemaess transfer/auftrag-k7v.md.
Phasenplan v2.2 und Anforderungsliste L1 haben Vorrang; jede Abweichung im
Bericht markieren. Keine Anforderungs-IDs erfinden; neue Pruefschritte nur als
Vorschlag mit "ID offen" fuehren (D-06).

Ziel:
Die Winner-Kette kann ohne Roboter gegen Aufzeichnungen entwickelt werden.
Kamera-Detektionen tragen ihre Erfassungszeit. Drei Referenzaufnahmen liegen
vor und sind maschinell geprueft. Der Fahrbetrieb bleibt unveraendert.

Arbeite in fuenf Phasen. Phase 0 ist read-only und endet mit einem Bericht
und STOPP - keine Aenderung vor meiner Freigabe.

Phase 0 - Bestandsaufnahme (nur lesen, nichts aendern):
 a) Docker: Welche Teile von Dockerfile und docker-compose.yml setzen Pi-
    Hardware voraus (devices, privileged, cgroup-Regeln, micro-ROS-Agent-
    Build, Audio, X11)? Baut das Image auf arm64 (Mac) und x86_64 (iMac)
    ohne Aenderung? Was bricht ohne /dev/amr_*? Vorschlag fuer eine
    docker-compose.dev.yml mit Begruendung.
 b) Topics fuer die Aufnahme: Name, Typ, QoS (insb. transient_local fuer
    /map, /tf_static), Sollrate und frame_id von /scan, /odom, /tf,
    /tf_static, /imu, /range/front, /cliff, /vision/detections, /map, dem
    Nav2-Globalpfad (/plan?) und dem wirksamen Fahrbefehl (/cmd_vel nach
    cliff_safety_node?). Wer publiziert was (Knotenname)?
 c) Zeitbasis: Bestaetige B-V5 (MCU-Zeitsync). Wie gross ist der Abstand
    header.stamp zu Empfangszeit fuer /odom, /imu, /range/front, /scan
    (kurze Messung im laufenden Stack, je 30 s, read-only)?
 d) Vision-Pfad: Bestaetige B-V1/B-V2. Wo entsteht das Kamerabild (v4l2-
    Knoten oder dashboard_bridge), welche Stempel traegt es, und wie alt
    ist ein Bild beim cap.read() im Host-Runner schaetzungsweise (MJPEG-
    Puffer)? Nur beschreiben, nicht messen, wenn dafuer Code noetig waere.
 e) TF: Bestaetige B-V3. Welche Knoten (SLAM Toolbox, Nav2) haengen am
    TF odom->base_link, und was wuerde ein Stempel aus msg.header.stamp
    aendern? Nur bewerten, nicht aendern.
 f) Rosbag: Ist rosbag2 mit sqlite3 im Image? Freier Speicher auf dem Pi
    fuer 3 x 60 s Aufnahme (Schaetzung je Topic)? Wie liest
    slam_validation.py heute Bags (Storage-ID)?
 g) Verzeichnisse: Wo sollen Bags liegen (ausserhalb des Repos, z. B.
    ~/amr_bags/), wo die bag_check-Berichte (Vorschlag planung/ oder
    docs/)? .gitignore-Ergaenzung vorschlagen.
 -> Bericht a-g, dann STOPP.

Phase 1 - Entwicklungsumgebung (A1, A4):
 - amr/docker/docker-compose.dev.yml: gleiches Image, KEINE devices, KEIN
   privileged, keine Audio- und Kamera-Mounts; ROS_DOMAIN_ID=42 und
   ROS_LOCALHOST_ONLY=1, damit nichts mit dem Roboter im Netz spricht;
   Volume fuer ~/amr_bags (read-only) und fuer src/.
 - In docker-compose.yml und docker-compose.dev.yml ../pi5/ros2_ws/src
   statt ../pi5/ros2_ws/src/my_bot einbinden (Vorbereitung neuer Pakete in
   K7). Auf dem Pi danach ./verify.sh - Verhalten muss gleich bleiben.
 - amr/docker/README.md: Abschnitt "Entwicklung ohne Roboter" (Build,
   Start, colcon build, ros2 bag play).
 - run.sh NICHT aendern.

Phase 2 - Erfassungszeit und Sequenznummer (A3, B-V1/B-V2):
 - host_hailo_runner.py: t_capture = time.time() unmittelbar nach
   cap.read(); im JSON zusaetzlich "capture_time" und "seq" (fortlaufend
   ab Start). "timestamp" bleibt unveraendert (Abwaertskompatibilitaet
   fuer Dashboard und Gemini-Knoten).
 - hailo_udp_receiver_node.py: Felder durchreichen, Docstring
   aktualisieren. Topic, Typ und bestehende Felder unveraendert.
 - Keine typisierte Nachricht in K7-V (vision_msgs fehlt im Image); das
   kommt mit amr_chain_msgs in K7. Im Bericht festhalten.
 - Nachweis: 60 s Lauf mit aktiver Objekterkennung; capture_time <=
   timestamp in 100 % der Pakete; Differenz (Median, P95) berichten;
   Luecken in seq zaehlen.

Phase 3 - Aufnahme und Pruefung (T1):
 - amr/scripts/record_reference_bags.sh <szene> <dauer_s>: Topicliste aus
   einer YAML-Datei (Phase 0b), Ablage ~/amr_bags/<datum>_<szene>/,
   Storage sqlite3, dazu metadata_amr.yaml mit Szene, Beschreibung,
   Git-Commit, aktiven Launch-Argumenten.
 - amr/scripts/bag_check.py <bagordner>: liest mit rosbag2_py; je Topic
   Anzahl, Rate (Mittel, Min), Luecken > 2 Sollperioden; fuer gestempelte
   Nachrichten Abstand header.stamp zu Aufnahmezeit (Median, P95, Max);
   fuer /vision/detections capture_time zu timestamp und seq-Luecken.
   Ausgabe als Markdown-Bericht. Vergleich mit NFA-02 (/scan 7,7 Hz Ist)
   und NFA-03 (Odometrie >= 10 Hz) ausweisen.
 - Als ros2-Einstiegspunkt nach dem Symlink-Muster aus CLAUDE.md
   (bag_check) eintragen.
 - Mit einer kurzen Probeaufnahme (Stand, 10 s) selbst testen.

Phase 4 - Doku, Pruefungen, Bericht:
 - docs/ros2/referenz-bags.md: Zweck, Szenen, Topicliste, Bedienung,
   Grenzen (B-V3 offen); in mkdocs.yml unter "ROS 2 (Raspberry Pi 5)".
 - docs/vision_pipeline.md: JSON-Felder capture_time und seq.
 - Phasenplan v2.2 nur ergaenzen: unter K7 Hinweis "Vorbereitung K7-V
   erledigt (Referenz-Bags, Erfassungszeit)"; B-V3 als offener Punkt
   fuer K7 (Entscheidung, keine Aenderung).
 - ruff, mypy, pre-commit, mkdocs build --strict; bei Fehlern stoppen.

Wichtig:
 - Keine Fahrbewegung durch Claude Code. Keine Firmwareaenderung, kein
   Flash. micro-ROS, CAN-Pfad, Nav2- und SLAM-Parameter unveraendert.
 - B-V3 (TF-Stempel) NICHT aendern; nur bewerten. Eine Aenderung wirkt
   auf SLAM und Nav2 und gehoert in K7 mit eigenem Test.
 - Bags nicht ins Repo. Keine API-Schluessel in metadata_amr.yaml.
 - Keine ACDC-Kursloesungen ins Repo uebernehmen.
 - Stilregeln: keine UTF-8-Umlaute in Markdown, Terminologie-Norm
   (Knoten, Bedien- und Leitstandsebene, Sicherheitslogik).

Zeige vor jedem Commit:
 1. Phase-0-Bericht a-g (vor allem anderen),
 2. Aenderungen je Datei mit Bezug auf Phase und Befund B-V1 bis B-V6,
 3. Nachweis Phase 2 (capture_time <= timestamp, Median/P95, seq-Luecken),
 4. bag_check-Bericht der Probeaufnahme,
 5. Liste der Abweichungen von diesem Auftrag,
 6. geplanten Commit und Tag k7v-refbags-v1.
Noch nicht committen.
```

## 4 Referenzszenen (Jan, auf dem Pi)

| Szene | Ablauf | Dauer | Launch-Argumente | Zweck |
| --- | --- | --- | --- | --- |
| (a) Stand, statisch | Roboter steht, Hindernis ca. 1 m frontal, niemand im Raum | 60 s | Standard, use_vision:=True, use_camera:=True | Grundrauschen, Falschalarme, Existenz (Winner 20.2.2) |
| (b) Nav2-Fahrt | Nav2-Ziel ca. 2 m geradeaus, danach Stand | 60 s | Standard, use_nav:=True | Lokalisierung Odometrie vs. SLAM (ACDC S2b), Folgefehler RPP (ACDC S4, Winner Gl. 34.13) |
| (c) Person quert | Roboter steht, Person geht in ca. 1,5 m dreimal quer durchs Sichtfeld, Tempo normal | 60 s | Standard, use_vision:=True, use_camera:=True | Tracking, ID-Stabilitaet, Praediktion (ACDC S3, Winner 20.2.3) |

Die Szenen werden spaeter mit derselben Topicliste wiederholt, damit Vorher-Nachher-Vergleiche moeglich sind.

## 5 Abnahme K7-V

| Nachweis | Kriterium | Quelle |
| --- | --- | --- |
| Phase-0-Bericht | a-g beantwortet, Freigabe erteilt | Abschnitt 3 |
| dev-Compose | Build und `ros2 bag play` auf Mac und iMac ohne Hardware | J3 |
| Pi unveraendert | ./verify.sh gruen nach dem Mount-Wechsel | Phase 1 |
| Erfassungszeit | capture_time <= timestamp in 100 % der Pakete; Median und P95 berichtet | B-V1, Winner 20.2.5 |
| Referenz-Bags | (a), (b), (c) vorhanden; bag_check ohne fehlende Topics; /scan-Rate gegen NFA-02, Odometrie gegen NFA-03 ausgewiesen | T1, SA-14 (Vorbereitung) |
| Latenzwerte | header.stamp zu Aufnahmezeit je Sensor (Median, P95) | Eingang fuer das Latenzbudget K7 (FA-22) |
| Offene Punkte | B-V3 bewertet, nicht geaendert | Phase 0e |

K7-V ist abgeschlossen, wenn alle Zeilen erfuellt sind. Dann K7 (amr_chain_msgs, Ketten-Skelett, Radar-Simulator).

---

Quellen: Winner et al. (Hrsg.), Handbuch Assistiertes und Automatisiertes Fahren, 4. Aufl. 2024, Abschn. 20.2.5 (S. 492-493) und 47.3.1 (S. 1297-1304); ACDC-Wiki, Section 1 "ROS Bags".
