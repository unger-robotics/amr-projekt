# Bericht K7-V Phase 0 – Bestandsaufnahme a–g

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Phase-0-Bericht zum Claude-Code-Auftrag K7-V (`transfer/auftrag-k7v.md`, Version 1.0) |
| Version | 1.0 |
| Datum | 2026-10-08 |
| Autor | Jan (Bericht erstellt mit Claude Code, Freigabe J2 offen) |
| Bezug | `docs/plan/phasenplan-v2.md` (v2.2, Abschnitt 5, Paket K7), `docs/anforderungsliste-L1.md` (v1.1), `transfer/auftrag-k7v.md` |
| Eingangsbedingung | J1 erfuellt: Tag `k2-dbc-v1` liegt auf GitHub (zeigt auf `7dd12bf`), `main` = `origin/main` |
| Status | Phase 0 abgeschlossen: read-only, dazu eine passive Messung nach Freigabe des Stack-Starts. Phase 1–4 beginnen erst nach Freigabe J2 |
| Aenderungen am Bestand | Keine. Repo unveraendert, Container `amr_ros2` nach der Messung wieder gestoppt |

## 1 Kurzfassung

- B-V1, B-V2, B-V4, B-V5 und B-V6 sind bestaetigt.
- **B-V3 trifft in der genannten Form nicht zu.** `odom_to_tf` stempelt den laufenden TF odom->base_link bereits mit `msg.header.stamp`, also mit MCU-Zeit. `now()` gilt nur fuer den Identity-TF vor der ersten /odom. Der offene Punkt fuer K7 lautet damit: Zeitbasis bzw. Re-Sync.
- **ID-Kollision (B-V8):** Die Anforderungs-IDs SA-14, FA-22 und T-12 des Auftrags stammen aus Phasenplan v2.2. In L1 v1.1 (Erweiterung K1) sind sie mit anderer Bedeutung vergeben. D-06 ist offen; nach Annahme A3 des Phasenplans gelten die L1-IDs.
- **Messung vom 2026-10-08:**
  - Nach frischem Sync liegen die MCU-Stempel im Median etwa 1 ms neben der Empfangszeit.
  - Sie laufen der Pi-Uhr jedoch um etwa 15–20 ppm voraus, also etwa 55–70 ms pro Stunde.
  - /scan ist beim Empfang etwa 135 ms alt, weil der Stempel den Beginn des Umlaufs markiert.
- **Erfassungszeit (B-V7):** Die Erfassungszeit im Host-Runner (Phase 2) ist der Zeitpunkt, zu dem das Bild aus einem gepufferten MJPEG-Strom entnommen wird. Eine Sensorzeit ist sie nicht.
- **Szenen (a) und (c):** Fuer Detektionen ist zusaetzlich `use_dashboard:=True` noetig (B-V10).

## 2 Befundliste

Die Befunde B-V1 bis B-V6 sind dem Auftrag entnommen und hier bestaetigt oder korrigiert. B-V7 bis B-V11 sind neu.

| Nr. | Ergebnis | Beleg |
| --- | --- | --- |
| B-V1 | **Bestaetigt.** `"timestamp": time.time()` steht nach `cap.read()`, Drehung, Vorverarbeitung, Inferenz, Nachverarbeitung und Reklassifizierung, ist also die Versandzeit. | `amr/scripts/host_hailo_runner.py:470` (`cap.read()`), `:502` (`timestamp`) |
| B-V2 | **Bestaetigt.** `/vision/detections` ist `std_msgs/String` ohne Header und ohne Sequenznummer. Der Knoten serialisiert das gesamte JSON-Objekt neu (`json.dumps(payload)`); neue Felder kommen deshalb ohne Codeaenderung durch. | `amr/scripts/hailo_udp_receiver_node.py:46, 81-83` |
| B-V3 | **Nicht bestaetigt in der genannten Form.** Zeile 34 stempelt nur den Identity-TF, der bis zur ersten /odom mit 2 Hz gesendet wird. Im Betrieb kopiert Zeile 45 `t.header = msg.header`, der TF traegt also die MCU-Zeit aus /odom. | `amr/scripts/odom_to_tf.py:34, 45` |
| B-V4 | **Bestaetigt.** Eingebunden ist nur `src/my_bot`. Die `devices:` `/dev/amr_drive`, `/dev/amr_sensor`, `/dev/ttyUSB0` und `/dev/snd` binden die Datei an den Pi. | `amr/docker/docker-compose.yml:32-36, 40` |
| B-V5 | **Bestaetigt, mit Praezisierung.** `rmw_uros_sync_session(1000)` laeuft genau einmal in `setup()`; der Rueckgabewert wird ignoriert, ein Re-Sync fehlt. Gestempelt wird beim Publizieren auf Core 0, nicht bei der Messung auf Core 1. `/cliff` (Bool) hat keinen Header. | `drive_node/src/main.cpp:415, 499`; `sensor_node/src/main.cpp:579, 694, 724, 797` |
| B-V6 | **Bestaetigt.** Im Image sind rosbag2 0.15.16 mit sqlite3-Plugin und `rosbag2_py` (Python 3.10.12) vorhanden. `vision_msgs` und `rosbag2_storage_mcap` fehlen. | Image `amr-ros2-humble:latest` vom 2026-04-03, read-only geprueft |
| B-V7 (neu) | **Rueckstau im MJPEG-Strom.** Der MJPEG-Server schreibt das jeweils neueste JPEG ohne Pause und ohne Pruefung auf ein neues Bild. Der Runner liest ohne Puffersteuerung (kein `CAP_PROP_BUFFERSIZE`, kein Leerlesen) mit hoechstens 5 Hz. `cap.read()` liefert deshalb das aelteste gepufferte Bild. | `amr/scripts/dashboard_bridge.py:194-206`; `amr/scripts/host_hailo_runner.py:441, 470, 522-526` |
| B-V8 (neu) | **ID-Kollision zwischen Phasenplan v2.2 und L1 v1.1.** In L1 bedeuten die IDs etwas anderes: SA-14 ist die Umfeldmodell-Schnittstelle, FA-22 die Trajektorienplanung, T-12 der `radar_sim_test`. D-06 ist offen. | `docs/plan/phasenplan-v2.md:338-339, 393`; `docs/anforderungsliste-L1.md:95, 154, 239` |
| B-V9 (neu) | **`amr/docker/.dockerignore` wirkt nicht.** Der Build-Kontext ist die Repo-Wurzel (`context: ../..`). Docker liest `.dockerignore` aber nur an der Kontextwurzel oder als `Dockerfile.dockerignore`. Der Kontext umfasst damit etwa 2,2 GB, einschliesslich `amr/docker/.env`. Ins Image gelangt per `COPY` nur `entrypoint.sh`. | `amr/docker/docker-compose.yml:12-14`; `amr/docker/Dockerfile:129` |
| B-V10 (neu) | **Szenen (a) und (c) ohne `use_dashboard:=True`.** Der Runner liest den MJPEG-Strom der `dashboard_bridge`; ohne ihn gibt es keine Detektionen. Zudem vergleichen die Bedingungen fuer Nav2 und die Benutzeroberflaeche woertlich mit `'True'`/`'False'`. `use_nav:=true` (klein geschrieben) startet deshalb **kein** Nav2, ebenso `use_cliff_safety:=true`; der `cliff_safety_node` selbst startet dabei aber. | `amr/scripts/host_hailo_runner.py:210, 437-460`; `full_stack.launch.py:262-294, 393-419, 449` |
| B-V11 (neu) | **Stack-Stopp.** Nach SIGINT an `ros2 launch` enden die `ros2 run`-Huellen mit Exit -15, die beiden `micro_ros_agent`-Prozesse laufen aber weiter und halten die seriellen Ports. Erst `docker stop amr_ros2` beendet sie. Danach sind die micro-ROS-Sitzungen der ESP32 verloren; vor dem naechsten Start ist ein Reset (T1) noetig. | Launch-Protokoll und `pgrep` im Container, 2026-10-08 |

## 3 Bestandsaufnahme

### a) Docker

**Pi-Bindung in `docker-compose.yml`:**

- `devices:` mit `/dev/amr_drive`, `/dev/amr_sensor`, `/dev/ttyUSB0` und `/dev/snd`. Fehlt ein Geraet, bricht `docker compose up` beim Anlegen des Containers ab ("error gathering device information").
- `privileged: true` und `device_cgroup_rules` (166, 188, 81, 116). Sie laufen auch auf Docker Desktop, sind dort aber unnoetig.
- `network_mode: host` fuer die DDS-Discovery mit dem Roboter.
- Mounts fuer X11 (`/tmp/.X11-unix`), ALSA (`asound.conf`), Zertifikate der Benutzeroberflaeche und Firmware.
- API-Schluessel kommen aus `.env` bzw. aus der Host-Umgebung.

**Dockerfile:**

- Keine Geraetebindung. Die Basis `ros:humble-ros-base` gibt es fuer amd64 und arm64.
- Der micro-ROS-Agent wird per apt versucht und sonst aus Source gebaut. Auf dem Pi ist er nachweislich aus Source gebaut (`/opt/microros_ws`).
- Audio-, X11- und Kamerapakete werden mitinstalliert; ohne Hardware stoeren sie nicht.
- `entrypoint.sh` legt ohne Mount eine `/etc/asound.conf` an (harmlos) und laedt fehlende openwakeword-Modelle nach.

**Baut das Image auf arm64 (Mac) und x86_64 (iMac) ohne Aenderung?** Das ist zu erwarten, aber nicht geprueft; den Nachweis liefert J3.

- Alle apt-Pakete existieren fuer beide Architekturen. Auf arm64 laeuft wie auf dem Pi voraussichtlich der Source-Build des Agents (zusaetzlich etwa 10–30 min), auf x86_64 voraussichtlich der apt-Zweig.
- Die pip-Pakete (onnxruntime 1.23.2, ctranslate2 4.7.1 u. a.) haben Wheels fuer aarch64 und x86_64.
- Der Build braucht Internet (rosdep, pip, openwakeword-Modelle).
- Ausser `numpy<2` und `openwakeword==0.6.0` sind die pip-Pakete nicht gepinnt. Ein Neubau im Oktober 2026 weicht deshalb vom Pi-Image (April 2026) ab. Fuer die Bag-Wiedergabe ist das unkritisch, weil Humble-CDR und sqlite3 gleich bleiben.

**Was ohne `/dev/amr_*` bricht:**

- `docker compose up` und damit `run.sh`. `run.sh` nutzt ausserdem `fuser`, `xhost`, `systemctl` und `mknod` auf dem Host und ist nur fuer den Pi gedacht.
- `verify.sh`: Die Laeufe mit `docker compose run` scheitern an `devices:`.
- Im Launch die micro-ROS-Agents und `rplidar_node`.

**Vorschlag `amr/docker/docker-compose.dev.yml`** (Umsetzung in Phase 1):

```yaml
name: amr-dev                      # eigener Projektname: sonst uebernimmt Compose den Pi-Container
services:
  amr-dev:
    build:
      context: ../..
      dockerfile: amr/docker/Dockerfile
    image: amr-ros2-humble:latest  # gleiches Image; auf dem Pi nicht ueber diese Datei bauen
    container_name: amr_ros2_dev   # run.sh erkennt Container am Namen amr_ros2
    environment:
      - ROS_DOMAIN_ID=42
      - ROS_LOCALHOST_ONLY=1
    volumes:
      - ../pi5/ros2_ws/src:/ros2_ws/src:rw
      - ../scripts:/amr_scripts:ro
      - ../scripts:/scripts:ro     # Pflicht: Symlinks in my_bot/my_bot/ zeigen auf /scripts
      - ${HOME}/amr_bags:/amr_bags:ro
      - dev_build:/ros2_ws/build
      - dev_install:/ros2_ws/install
      - dev_log:/ros2_ws/log
    stdin_open: true
    tty: true
volumes:
  dev_build:
  dev_install:
  dev_log:
```

Begruendung:

- Die Datei hat keine `devices`, kein `privileged`, keine Audio-, Kamera-, X11- oder Zertifikat-Mounts und keine API-Schluessel. Fuer die Wiedergabe ist nichts davon noetig, und so entstehen keine Cloud-Aufrufe und keine Schluessel auf Fremdrechnern.
- **Sicherheitsrelevant:** Bags enthalten `/cmd_vel`. Bridge-Netz, `ROS_DOMAIN_ID=42` und `ROS_LOCALHOST_ONLY=1` isolieren dreifach, sodass eine Wiedergabe den Fahrkern nie erreicht.

### b) Topics fuer die Aufnahme

QoS und Publisher-Knoten sind zur Laufzeit geprueft (`ros2 topic info -v`, 2026-10-08, Standardargumente). Die History-Tiefe liefert die Discovery nicht ("UNKNOWN"). Werte mit [S] sind Upstream-Standardwerte, die nicht im Repo stehen.

| Topic | Typ | Publisher-Knoten | QoS | Sollrate (K0-Ist) | frame_id |
| --- | --- | --- | --- | --- | --- |
| /scan | sensor_msgs/LaserScan | `rplidar_node` (apt 2.1.4) | Rel/Vol | `scan_frequency` 7.0 (7,51 Hz); 1440 Punkte je Scan | `laser` |
| /odom | nav_msgs/Odometry | `esp32_bot` (Fahrkern) ueber `micro_ros_agent_drive` | Rel/Vol, Tiefe 10 | 20 Hz (19,85 Hz) | `odom`, child `base_link` |
| /tf | tf2_msgs/TFMessage | `odom_to_tf` (odom->base_link), zwei Endpunkte von `slam_toolbox` (map->odom) | Rel/Vol | ca. 40 Hz gesamt (39,77 Hz) | – |
| /tf_static | tf2_msgs/TFMessage | `laser_tf_publisher`, `ultrasonic_tf_publisher` (`use_sensors`), `camera_tf_publisher` (`use_camera`) | Rel/TL | latched | – |
| /imu | sensor_msgs/Imu | `esp32_sensors` (Sensor- und Sicherheitsbasis) | Rel/Vol, Tiefe 10 | 50 Hz (38,07 Hz) | `base_link` |
| /range/front | sensor_msgs/Range | `esp32_sensors` | Rel/Vol, Tiefe 10 | 10 Hz (9,06 Hz) | `ultrasonic_link` |
| /cliff | std_msgs/Bool | `esp32_sensors` | Rel/Vol, Tiefe 10 | 20 Hz (15,86 Hz, BA-04) | – (kein Header) |
| /vision/detections | std_msgs/String (JSON) | `hailo_udp_receiver` | Rel/Vol, Tiefe 10 | 5 Hz | – (nur JSON-Feld `timestamp`) |
| /map | nav_msgs/OccupancyGrid | `slam_toolbox` | Rel/TL | 2 Hz (1,99 Hz) | `map` |
| /plan (Nav2-Globalpfad) | nav_msgs/Path | `planner_server` (NavFn) | Rel/Vol | ereignisgetrieben; waehrend der Fahrt ca. 1 Hz [S] | `map` |
| /cmd_vel (wirksam) | geometry_msgs/Twist | zwei Publisher (BA-03): `cliff_safety_node` und `velocity_smoother`, letzterer umgeht die Sicherheitslogik; ein Subscriber (`esp32_bot`) | Rel/Vol | 20 Hz | – |

**Kette der Fahrbefehle:**

- Nav2 wird per `SetRemap /cmd_vel -> /nav_cmd_vel` eingebunden. Auf `/nav_cmd_vel` publizieren `controller_server` und vier Endpunkte von `behavior_server`, insgesamt 5 Publisher. Abnehmer sind `cliff_safety_node` und `velocity_smoother`.
- Die Bedien- und Leitstandsebene publiziert auf `/dashboard_cmd_vel`, Abnehmer ist `cliff_safety_node`.
- `cliff_safety_node` und `velocity_smoother` schreiben beide auf `/cmd_vel`. Am Fahrkern gilt die jeweils letzte Nachricht.
- Humble-Bags speichern nicht, welcher Publisher eine Nachricht gesendet hat.

**Vorschlag:** Die Kernliste des Auftrags um kleine Topics ergaenzen, zusammen unter 1 MB je Szene:

- `/nav_cmd_vel`, `/dashboard_cmd_vel` und `/emergency_stop`, damit die Herkunft des wirksamen Befehls nachvollziehbar bleibt;
- `/pose` (SLAM Toolbox) fuer Szene (b), Vergleich Odometrie gegen SLAM;
- `/lookahead_point` (RPP, Folgefehler) und `/battery`.

Die Liste wird mit den Referenzszenen festgeschrieben, damit spaetere Wiederholungen vergleichbar bleiben.

### c) Zeitbasis

**B-V5 im Detail:**

- Die Synchronisation ist ein einzelner NTP-aehnlicher Austausch mit dem Agenten beim Boot. Referenz ist die Pi-Uhr, denn der Container teilt die Host-Uhr.
- Ein Re-Sync fehlt.
- Schlaegt der Sync fehl, faellt das nicht auf: Die Stempel sind dann Zeit seit dem MCU-Boot (sec < 1e9). `serial_latency_logger.py:80` und `dashboard_bridge.py:1384` filtern solche Stempel bereits aus.

**Drei Zeitbasen im System:**

- Pi-Uhr: /scan, map->odom und der CAN-Pfad.
- MCU-Zeit des Fahrkerns: /odom und der TF odom->base_link.
- MCU-Zeit der Sensor- und Sicherheitsbasis: /imu, /range/front und /battery.

**Messung (passiv, nach Freigabe des Stack-Starts):**

- Standardargumente, keine Fahrbefehle, `/cliff` = true.
- M1 am 2026-10-08 um 22:13:12 MESZ, etwa 50 s nach dem Stack-Start; M2 75 s spaeter; je 30 s.
- Kenngroesse: Empfangszeit minus `header.stamp` in ms. Ungesyncte Stempel: 0.
- Verfahren in Anhang A.

| Topic / Kante | Zeitbasis | Rate M1 / M2 [Hz] | Median M1 -> M2 | P95 M1 / M2 | Max M1 / M2 |
| --- | --- | --- | --- | --- | --- |
| /odom | MCU Fahrkern | 20,01 / 20,00 | 1,1 -> 0,0 | 2,3 / 1,3 | 23,6 / 15,1 |
| /tf odom->base_link | MCU Fahrkern (aus /odom) | 20,02 / 19,99 | 2,0 -> 1,0 | 3,4 / 2,2 | 30,3 / 16,3 |
| /imu | MCU Sensor- und Sicherheitsbasis | 39,67 / 41,41 | 0,4 -> -1,0 | 1,4 / 0,0 | **293,9** / 98,4 |
| /range/front | MCU Sensor- und Sicherheitsbasis | 9,53 / 9,47 | -0,2 -> -1,6 | 2,4 / -0,7 | **1005,1** / 98,9 |
| /scan | Pi (`rplidar_node`) | 7,60 / 7,61 | 135,1 -> 135,2 | 136,2 / 136,3 | 138,3 / 137,9 |
| /tf map->odom | Pi (`slam_toolbox`) | 20,01 / 20,00 | -302,1 -> -304,3 | -243,9 / -244,3 | -230,1 / -233,0 |

**Auswertung:**

1. **Sync frisch gut.** Der Median liegt bei etwa 1 ms. Negative Werte bedeuten, dass der Stempel vor der Empfangszeit liegt; das entspricht einem Sync-Fehler von etwa 1–2 ms.
2. **Publizierzeit statt Messzeit.** Die MCU-Stempel geben den Zeitpunkt des Publizierens an, nicht den der Messung. Das Messalter (/odom und /imu 0–20 ms, /range/front 0–100 ms) steckt deshalb nicht in dieser Kenngroesse und laesst sich aus den Stempeln nicht bestimmen.
3. **Drift.**
   - Zwischen M1 und M2 sinkt der Median bei der Sensor- und Sicherheitsbasis um etwa 1,4 ms, beim Fahrkern um etwa 1,1 ms.
   - Die MCU-Stempel laufen der Pi-Uhr also um etwa 15–20 ppm voraus, etwa 55–70 ms pro Stunde. Die Unsicherheit liegt bei etwa ±5 ppm, da nur zwei Messpunkte vorliegen.
   - Ob die Ursache der ESP32-Quarz ist oder die Frequenznachfuehrung der Pi-Uhr durch systemd-timesyncd, laesst sich nicht trennen.
4. **/scan.**
   - 1440 Punkte, `scan_time` 121,1 ms, `time_increment` 84,2 us.
   - Der kleinste Abstand (121,2 ms) entspricht genau `scan_time`. Der Stempel markiert also den Beginn des Umlaufs.
   - Empfangen wird etwa 14 ms nach dem Ende des Umlaufs.
5. **map->odom.**
   - Die Kante ist etwa 0,3 s in die Zukunft datiert (`transform_timeout` 0,5 s minus Scan-Alter).
   - Die Rate von 20 Hz bestaetigt den Upstream-Standardwert `transform_publish_period` = 0,05 s.
6. **Ausreisser.**
   - M1 (etwa 50 s nach dem Start): einzelne Ausreisser von 294 ms (/imu) und 1005 ms (/range/front).
   - M2: etwa 99 ms auf beiden Topics der Sensor- und Sicherheitsbasis.
   - P95 bleibt hoechstens bei 2,4 ms. Die Ursache ist offen; vermutet werden Wiederholungen im zuverlaessigen XRCE-Strom.
   - Fuer das Latenzbudget in K7 zaehlt der Auslauf der Verteilung, deshalb weist bag_check den Maximalwert aus.
7. **Raten.** Alle Raten liegen im Rahmen von K0 bzw. L1 Abschnitt 10.2: /odom 20,0 (K0 19,85), /imu 39,7–41,4 (K0 38,07), /range/front 9,5 (K0 9,06), /scan 7,6 (K0 7,51).

### d) Vision-Pfad

```
IMX296 (CSI)
  -> rpicam-vid (MJPEG, 640x480, 15 fps)          [Host, camera-v4l2-bridge.service]
  -> ffmpeg -> /dev/video10 (v4l2loopback, YUYV)
  -> v4l2_camera_node -> /camera/image_raw        [Container, use_camera, bgr8, camera_link]
  -> dashboard_bridge (JPEG Q70, ein Speicherplatz latest_jpeg)   [use_dashboard]
  -> MJPEG-Server https://127.0.0.1:8082/stream
  -> host_hailo_runner.py: cap.read() (FFmpeg)
```

**Stempel:**

- Den `header.stamp` von `/camera/image_raw` setzt der apt-Treiber `v4l2_camera`; im Repo ist das nicht pruefbar (laut Upstream `now()` beim Dequeue).
- Spaetestens beim JPEG-Schritt geht der Stempel verloren: Die Multipart-Teile tragen nur `Content-Type` und `Content-Length`. Beim Runner kommt also keine Zeit von vorgelagerten Stufen an.

**Alter eines Bildes bei `cap.read()`** (nur beschrieben, nicht gemessen):

- Der Server sendet das jeweils neueste JPEG ohne Pause und ohne Pruefung auf ein neues Bild, so schnell der Socket es abnimmt.
- Der Runner liest hoechstens 5 Bilder pro Sekunde. Dadurch fuellen sich die TCP-Puffer, der TLS-Puffer und der FFmpeg-Puffer mit wartenden Bildern.
- `cap.read()` liefert das aelteste davon. Sein Alter betraegt etwa die Zahl der gepufferten Bilder mal 200 ms und ueberwiegt voraussichtlich alle vorgelagerten Anteile.
- Hinzu kommen die Erfassung mit 15 fps, die doppelte JPEG-Kodierung und die Wartezeit im Single-Thread-Executor der Bridge.
- Steht die Kamera, liefert der Server das letzte Bild endlos weiter; der Runner bemerkt das nicht.

**Folge fuer K7:**

- `capture_time` aus Phase 2 ist die Erfassungszeit im Runner. Sie ist eine Obergrenze des Bildzeitpunkts und keine Sensorzeit im Sinne von Phasenplan v2.2, K7 (SA-14).
- Vorschlag fuer K7, nicht fuer K7-V: Bilder im Runner per Grabber-Thread leerlesen oder den Stempel durch die Kette reichen.

**Konsumenten:**

- `dashboard_bridge` verwirft `timestamp` und alle unbekannten Felder der obersten Ebene.
- `gemini_semantic_node` liest `timestamp` nicht; seine 5-s-Frischepruefung gilt nur fuer /range/front und /scan.
- Die Benutzeroberflaeche validiert zur Laufzeit nicht.
- Ergebnis: `capture_time` und `seq` stoeren keinen Konsumenten.
- `hailo_inference_node` (nicht im Launch) und der Fallback-Modus des Runners liefern die neuen Felder nicht; bag_check behandelt sie deshalb als optional.

### e) TF

**Baum:**

- `map` -> `odom`: `slam_toolbox`, Pi-Uhr, Stempel des letzten Scans plus `transform_timeout`.
- `odom` -> `base_link`: `odom_to_tf`, MCU-Zeit des Fahrkerns.
- Statisch an `base_link`: `laser`, `ultrasonic_link` und `camera_link`.
- Es gibt kein URDF und keinen `robot_state_publisher`.

**Von odom->base_link haengen ab:**

- SLAM Toolbox: Lookup beim Scan-Stempel, `transform_timeout` 0,5 s, `tf_buffer_duration` 30 s.
- Nav2: RPP mit `transform_tolerance` 0,1 s; Costmaps mit Standardtoleranz [S]; die Obstacle-, Voxel- und RangeSensor-Layer arbeiten mit den Stempeln von /scan bzw. /range/front.
- Testskripte, die mit `Time()` den juengsten Stand nachschlagen.
- Ohne TF-Bezug sind `cliff_safety_node` und `dashboard_bridge` (liest /tf roh).

**Bewertung des Ist-Zustands** (TF-Stempel = /odom-Stempel, so ist es heute schon):

- **Vorteil:** /odom und TF passen zusammen, und der Stempel liegt naeher an der Sensorzeit (keine Transportlatenz).
- **Risiko:** Alles haengt am einmaligen, ungeprueften Sync.
  - Laeuft die MCU-Uhr nach, wartet SLAM auf neuere Odometrie und verwirft Scans.
  - Laeuft sie vor, werden Scans der falschen Pose zugeordnet. Lookups der Roboterpose im Map-Frame muessten dann in die Zukunft extrapolieren, sobald der Vorlauf den Vorsprung von map->odom uebersteigt (gemessen 0,23–0,30 s).
  - Bei der gemessenen Drift ist das nach etwa 3,5–5,5 h MCU-Laufzeit ohne Neustart zu erwarten (Abschaetzung).
  - Scheitert der Sync (Stempel um 1970), verwirft tf2 die echten TFs als veraltet gegenueber dem Identity-TF in Pi-Zeit; odom->base_link bleibt dann auf Identity stehen.
- **Alternative `now()`:** Sie entkoppelt vom Sync, verschiebt aber jede Pose um die Transportlatenz und loest den TF-Stempel vom /odom-Stempel.

**Vorschlag fuer den offenen Punkt in K7** (Entscheidung, keine Aenderung in K7-V): Zeitbasis der MCU-Stempel festlegen, entweder durch periodischen Re-Sync mit Pruefung von `rmw_uros_epoch_synchronized()` in der Firmware oder durch Stempelung auf der Pi-Seite, jeweils mit eigenem Test. Die Messwerte aus c) sind die Ausgangslage.

### f) Rosbag und Speicher

**Werkzeuge:**

- rosbag2 (Humble 0.15.16) mit sqlite3 ist im Image (B-V6).
- `ros2 bag record -d` teilt Dateien auf, beendet die Aufnahme aber nicht. Fuer eine feste Dauer ist `timeout -s INT` noetig; nur dann wird `metadata.yaml` sauber geschrieben.
- `--qos-profile-overrides-path` ist verfuegbar; damit lassen sich /tf_static und /map als transient_local aufnehmen.
- `slam_validation.py:529` liest mit `StorageOptions(uri, storage_id="sqlite3")` und CDR. Der Bag-Modus ist nur ein Geruest (TODO: TF-Replay fehlt).

**Speicherschaetzung je 60-s-Szene:**

| Topic | Rechnung | Groesse |
| --- | --- | --- |
| /scan | 1440 Punkte (gemessen) x 8 B x 7,6 Hz | ca. 5,3 MB |
| /map | 2 Hz x (200 x 200 bis 400 x 400) B | 4,8–19 MB, dominiert |
| /odom | 725 B x 20 Hz | ca. 0,9 MB |
| /imu | ca. 330 B x 38 Hz | ca. 0,75 MB |
| /tf | ca. 120 B x 40 Hz | ca. 0,3 MB |
| /vision/detections | 0,3–2 kB x 5 Hz | 0,1–0,6 MB |
| /plan | – | bis 0,4 MB |
| uebrige | – | unter 0,2 MB |

- Summe: etwa 12–29 MB je Szene, fuer drei Szenen unter 100 MB.
- Frei sind 77 GB, der Speicher ist also unkritisch. bag_check misst die tatsaechlichen Groessen.
- Rohbilder sind bewusst nicht in der Liste (etwa 830 MB/min).

### g) Verzeichnisse und .gitignore

**Ablage:**

- **Bags** auf dem Pi unter `~/amr_bags/<JJJJMMTT_HHMM>_<szene>/`, also ausserhalb des Repos. Datum mit Uhrzeit wie bei P-CAN2, damit Wiederholungen am selben Tag nicht kollidieren.
- **bag_check-Berichte** unter `validation/P-AD1/<bagname>/bag_check.md`, dazu eine Kopie von `metadata_amr.yaml`.
  - L1 Abschnitt 8.2 legt P-AD1 als Messprotokoll fuer K7/K8 fest; `validation/P-CAN2/` ist das Muster.
  - Der Auftrag nennt `planung/` oder `docs/`. `docs/` wird jedoch auf GitHub Pages veroeffentlicht, und `planung/` enthaelt von Hand gefuehrte Protokolle.

**.gitignore:**

- `*.db3` und `metadata.yaml` sind bereits ausgeschlossen.
- Die bestehende Regel `*_report.md` wuerde einen Bericht namens `bag_check_report.md` ausschliessen. Der Dateiname ist deshalb `bag_check.md`.
- Ergaenzung (vorbeugend):

```
# rosbag2-Aufnahmen liegen ausserhalb des Repos (~/amr_bags/, K7-V)
*.mcap
*.db3-*
amr_bags/
```

## 4 Vorschlag fuer Phase 1–4 (Freigabe J2 offen)

**Grundsaetze:**

- Keine Fahrbewegung durch Claude Code, keine Firmwareaenderung, kein Flash.
- micro-ROS, CAN-Pfad sowie Nav2- und SLAM-Parameter bleiben unveraendert; `run.sh` wird nicht geaendert.
- Jeder Stack-Lauf erhaelt eine eigene Freigabe mit Benennung des Aufbaus.
- Commits erst auf Anweisung, mit den sechs Nachweisen aus Abschnitt 3 des Auftrags.

| Phase | Datei | Aenderung |
| --- | --- | --- |
| 1 | `amr/docker/docker-compose.dev.yml` (neu) | wie in a) |
| 1 | `amr/docker/docker-compose.yml` | `../pi5/ros2_ws/src:/ros2_ws/src:rw` statt `src/my_bot`; **zusaetzlich** `${HOME}/amr_bags:/amr_bags:rw` (fuer Phase 3 noetig) |
| 1 | `amr/docker/README.md` | Abschnitt "Entwicklung ohne Roboter" mit Sicherheitshinweis: Bags nie im Container `amr_ros2` abspielen, oder nur mit `/cmd_vel:=/bag/cmd_vel` |
| 2 | `amr/scripts/host_hailo_runner.py` | `t_capture = time.time()` direkt nach `cap.read()`; im JSON zusaetzlich `capture_time` und `seq` (0-basiert, gesendete Pakete); `timestamp` bleibt; der Fallback-Modus erhaelt nur `seq` |
| 2 | `amr/scripts/hailo_udp_receiver_node.py` | nur der Docstring (Felder werden bereits durchgereicht) |
| 3 | `my_bot/config/reference_bags.yaml`, `reference_bags_qos.yaml` (neu) | Topicliste mit Sollraten, Szenenkatalog (a, b, c, probe) mit erwarteten Launch-Argumenten und Topics; QoS-Overrides fuer /tf_static und /map |
| 3 | `amr/scripts/record_reference_bags.sh` (neu, Host) | prueft Stack und Launch-Argumente; Aufnahme per `timeout -s INT ... ros2 bag record -s sqlite3`; Abbruch mit Ctrl+C sauber; `chown`; `metadata_amr.yaml` ohne Umgebungsvariablen und ohne Schluessel |
| 3 | `amr/scripts/bag_check.py` (neu) plus Entry-Point | Raten, Luecken groesser 2 Sollperioden, Nachrichtengroessen, Stempelabstand (Median, P95, Max), Pruefung von `capture_time`/`seq`, fehlende erwartete Topics, Tabelle nach L1 Abschnitt 10.1 (NFA-02, NFA-03 mit K0-Baseline und Regressionstoleranz); Statistikfunktionen ohne ROS-Import |
| 4 | `docs/ros2/referenz-bags.md` (neu), `mkdocs.yml` | Zweck, Szenen, Topicliste, Bedienung, Sicherheitshinweis, Grenzen (B-V3 korrigiert, B-V7) |
| 4 | `docs/vision_pipeline.md` | Abschnitt "Detektions-JSON" mit vollstaendiger Feldtabelle, die bisher fehlt |
| 4 | `docs/plan/phasenplan-v2.md` | nur ergaenzen unter K7: Hinweis "Vorbereitung K7-V erledigt", offener Punkt Zeitbasis, ID-Kollision (B-V8) |
| 4 | `.gitignore`, `tests/test_bag_check.py` (neu) | Ergaenzung nach g); pytest fuer die Statistikfunktionen |

**Nachweise:**

- Phase 1: `verify.sh` liefert auf dem Pi dasselbe Ergebnis wie vorher; die dev-Datei laeuft auf dem Pi ohne Geraete.
- Phase 2: 60 s mit aktiver Objekterkennung (eigene Freigabe); `capture_time <= timestamp` in 100 % der Pakete, Median und P95 der Differenz, Luecken in `seq`.
- Phase 3: Probeaufnahme 10 s (eigene Freigabe), bag_check ohne fehlende Topics.
- Phase 4: ruff, mypy, pre-commit, pytest und `mkdocs build --strict` gruen.

## 5 Abweichungen vom Auftrag

1. B-V3 ist korrigiert: Der TF traegt bereits MCU-Zeit. Der offene Punkt fuer K7 lautet "Zeitbasis bzw. Re-Sync".
2. **IDs:**
   - In den Artefakten von K7-V werden IDs immer mit Quelle genannt (L1 v1.1 bzw. Phasenplan v2.2); neue IDs werden nicht vergeben.
   - Die Kennungen O6, A1/A3/A4 und T1 des Auftrags stammen aus dem Lernplan `Verzahnung-Winner-AMR.md`, der nicht im Repo liegt.
   - Sie kollidieren mit Repo-Kennungen: A1–A6 sind Annahmen im Phasenplan, T1 ist das Terminal 1 in `CLAUDE.md`. In Repo-Dateien erscheinen sie deshalb nur mit dem Zusatz "Lernplan".
3. Mount `~/amr_bags` in der Pi-Compose-Datei (fuer Phase 3 noetig).
4. Berichte unter `validation/P-AD1/` statt `planung/` oder `docs/`.
5. Szenen (a) und (c) mit `use_dashboard:=True` (B-V10).
6. Zusaetzliche kleine Topics in der Aufnahmeliste (b).
7. Ordnername `<JJJJMMTT_HHMM>_<szene>` statt `<datum>_<szene>`.
8. Fallback-Modus des Runners: nur `seq`, kein `capture_time`.
9. Neu `tests/test_bag_check.py`.
10. Optional, nicht im Auftrag: B-V9 beheben (`Dockerfile.dockerignore`, aendert den Image-Inhalt nicht).
11. Die Abnahmezeile "NFA-02 (/scan 7,7 Hz Ist)" vermischt Anforderung (>= 5 Hz) und Istwert. bag_check trennt nach L1 Abschnitt 10.1 Anforderung, K0-Baseline (7,51 Hz), Messwert und Regressionstoleranz.

## 6 Nebenbefunde ausserhalb von K7-V

**Doku und Code:**

- `docs/vision_pipeline.md`:
  - `v4l2_camera_node` steht im Block "Host"; als "USB-Kamera-Treiber" bezeichnet, obwohl es eine CSI-Kamera IMX296 ueber v4l2loopback ist.
  - Port 8082 als HTTP angegeben, mit Zertifikaten ist es HTTPS.
  - Gemini-Modell `gemini-2.0-flash-lite` statt des Code-Standards `gemini-2.5-flash`.
- `docs/ros2_system.md`: Im TF-Baum fehlt map->odom.
- `planung/DoD-checkliste-phasen.md:52-53`: nennt `amcl` und `/local_plan`. Keins von beiden existiert im aktuellen Stack.

**Repo:**

- Die Tags `baseline-k0` und `k0-complete` existieren nur lokal, nicht auf GitHub.

## Anhang A – Messverfahren zu c)

- Ausgefuehrt per `docker exec -i amr_ros2 /entrypoint.sh python3 - < k7v_phase0_stamp_probe.py` im laufenden Container. Das Skript war nur fuer diesen Lauf gedacht und ist kein Repo-Werkzeug; die Kenngroesse uebernimmt kuenftig bag_check.
- Die Abonnements sind passiv: Reliable fuer /odom, /imu, /range/front und /tf, Sensor-Data-QoS fuer /scan, Transient Local fuer /tf_static. Das Skript publiziert nichts und schreibt keine Dateien.
- Die Zeitangabe im Container ist UTC.

```python
#!/usr/bin/env python3
"""K7-V Phase 0c: passive Messung header.stamp gegen Empfangszeit (nur lesen)."""

import time

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Imu, LaserScan, Range
from tf2_msgs.msg import TFMessage

DUR_S = 30.0
NS = 1_000_000_000
data: dict[str, list[tuple[int, int]]] = {}


def rec(key, stamp, t_rx):
    data.setdefault(key, []).append((t_rx, stamp.sec * NS + stamp.nanosec))


def pct(vals, p):
    k = min(len(vals) - 1, max(0, int(round(p * (len(vals) - 1)))))
    return vals[k]


def main():
    rclpy.init()
    node = Node("k7v_phase0_stamp_probe")
    rel = QoSProfile(depth=50, reliability=ReliabilityPolicy.RELIABLE)
    tf_static_qos = QoSProfile(
        depth=20,
        history=HistoryPolicy.KEEP_LAST,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )

    def mk(topic):
        return lambda msg: rec(topic, msg.header.stamp, time.time_ns())

    node.create_subscription(Odometry, "/odom", mk("/odom"), rel)
    node.create_subscription(Imu, "/imu", mk("/imu"), rel)
    node.create_subscription(Range, "/range/front", mk("/range/front"), rel)
    node.create_subscription(LaserScan, "/scan", mk("/scan"), qos_profile_sensor_data)

    def tf_cb(prefix):
        def cb(msg):
            t_rx = time.time_ns()
            for tr in msg.transforms:
                rec(f"{prefix} {tr.header.frame_id}->{tr.child_frame_id}", tr.header.stamp, t_rx)
        return cb

    node.create_subscription(TFMessage, "/tf", tf_cb("/tf"), QoSProfile(depth=200))
    node.create_subscription(TFMessage, "/tf_static", tf_cb("/tf_static"), tf_static_qos)

    t_end = time.monotonic() + DUR_S
    while time.monotonic() < t_end:
        rclpy.spin_once(node, timeout_sec=0.05)

    for key in sorted(data):
        vals = data[key]
        n = len(vals)
        span = (vals[-1][0] - vals[0][0]) / NS
        rate = (n - 1) / span if n > 1 and span > 0 else float("nan")
        unsynced = sum(1 for _, st in vals if st < 10**9 * NS)
        offs = sorted((t_rx - st) / 1e6 for t_rx, st in vals if st >= 10**9 * NS)
        if offs:
            print(f"{key} N={n} rate={rate:.2f} unsynced={unsynced} min={offs[0]:.1f} "
                  f"median={pct(offs, 0.5):.1f} p95={pct(offs, 0.95):.1f} max={offs[-1]:.1f}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

Gegenueber der ausgefuehrten Fassung ist das Listing gekuerzt. Weggelassen sind die Ausgabe der Mediane der ersten und letzten 5 s je Lauf sowie die Zusatzangaben der ersten Nachricht (frame_id, Zahl der Scanpunkte, `scan_time`, `time_increment`). Die Kenngroessen sind identisch.
