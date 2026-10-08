---
title: Referenzaufnahmen
description: Referenzaufnahmen (rosbag2) fuer die Entwicklung der Winner-Kette ohne Roboter, Szenen, Topicliste, Pruefung mit bag_check und Grenzen der Zeitstempel.
---

# Referenzaufnahmen (rosbag2)

## Zweck

Ab K7 wird die Winner-Funktionskette gegen Aufzeichnungen entwickelt, ohne dass der Roboter laeuft. Dafuer gibt es einen festen Satz Referenzaufnahmen. Die Topicliste bleibt gleich, damit spaetere Wiederholungen Vorher-Nachher-Vergleiche erlauben. Jede Aufnahme wird mit `bag_check` maschinell geprueft.

Grundlage sind der Auftrag K7-V (`transfer/auftrag-k7v.md`) und der Phase-0-Bericht (`docs/plan/bericht-k7v-phase0.md`).

## Szenen

| Szene | Ablauf | Dauer | Launch-Argumente zusaetzlich zum Standard |
|---|---|---|---|
| `a_stand` | Roboter steht, Hindernis ca. 1 m frontal, niemand im Raum | 60 s | `use_camera:=True use_dashboard:=True use_vision:=True` |
| `b_nav2` | Nav2-Ziel ca. 2 m geradeaus, danach Stand; das Ziel setzt der Bediener | 60 s | keine |
| `c_person` | Roboter steht, eine Person geht in ca. 1,5 m dreimal quer durchs Sichtfeld | 60 s | wie `a_stand` |
| `probe` | Selbsttest der Werkzeuge, Roboter steht | 10 s | wie `a_stand` |

- Detektionen brauchen `use_dashboard:=True`, weil der Host-Runner den MJPEG-Strom der `dashboard_bridge` liest.
- Launch-Argumente genau so schreiben (`True`, `False`). Die Bedingungen fuer Nav2 und die Benutzeroberflaeche vergleichen woertlich; `use_nav:=true` startet kein Nav2.
- `use_can` bleibt aus, damit `/imu`, `/cliff`, `/range/front` und `/battery` nur eine Quelle haben.

## Topicliste

Die Liste steht in `amr/pi5/ros2_ws/src/my_bot/config/reference_bags.yaml` und gilt fuer alle Szenen.

| Topic | Typ | Sollrate | Zeitbasis des Stempels |
|---|---|---|---|
| `/scan` | sensor_msgs/LaserScan | 7 Hz | Pi, Beginn des Umlaufs |
| `/odom` | nav_msgs/Odometry | 20 Hz | MCU Fahrkern |
| `/tf` | tf2_msgs/TFMessage | je Kante 20 Hz | odom->base_link: MCU Fahrkern; map->odom: Pi |
| `/tf_static` | tf2_msgs/TFMessage | latched | Pi |
| `/imu` | sensor_msgs/Imu | 50 Hz | MCU Sensor- und Sicherheitsbasis |
| `/range/front` | sensor_msgs/Range | 10 Hz | MCU Sensor- und Sicherheitsbasis |
| `/cliff` | std_msgs/Bool | 20 Hz | ohne Stempel |
| `/battery` | sensor_msgs/BatteryState | 2 Hz | MCU Sensor- und Sicherheitsbasis |
| `/vision/detections` | std_msgs/String (JSON) | 5 Hz | Host-Uhr des Runners, im JSON |
| `/map` | nav_msgs/OccupancyGrid | 2 Hz, latched | Pi |
| `/pose` | geometry_msgs/PoseWithCovarianceStamped | nach verarbeiteten Scans | Pi |
| `/plan` | nav_msgs/Path | ereignisgetrieben | Pi |
| `/lookahead_point` | geometry_msgs/PointStamped | waehrend einer Fahrt | Pi |
| `/cmd_vel` | geometry_msgs/Twist | 20 Hz | ohne Stempel; wirksamer Fahrbefehl mit zwei Publishern |
| `/nav_cmd_vel`, `/dashboard_cmd_vel` | geometry_msgs/Twist | ereignisgetrieben | ohne Stempel |
| `/emergency_stop` | std_msgs/Bool | ereignisgetrieben | ohne Stempel |

Rohbilder (`/camera/image_raw`) sind bewusst nicht enthalten, sie kaemen auf ca. 830 MB/min. `/tf_static` und `/map` werden mit den QoS-Overrides aus `reference_bags_qos.yaml` als transient_local aufgenommen. Damit erfasst die Aufnahme auch Nachrichten, die vor ihrem Start gesendet wurden.

## Aufnahme auf dem Pi

Voraussetzung: Der Stack laeuft mit den Argumenten der Szene, und `~/amr_bags` existiert.

```bash
cd ~/amr-projekt
amr/scripts/record_reference_bags.sh a_stand 60
```

Das Skript arbeitet in fuenf Schritten:

1. Es prueft Container, laufenden Launch und dessen Argumente gegen den Szenenkatalog. Bei einer Abweichung bricht es ohne Aufnahme ab; `--force` uebergeht das.
2. Es prueft, ob die erwarteten Topics vorhanden sind.
3. Es nimmt mit `ros2 bag record -s sqlite3` nach `~/amr_bags/<JJJJMMTT_HHMM>_<szene>/` auf. Ctrl+C beendet die Aufnahme sauber.
4. Es schreibt `metadata_amr.yaml` mit Szene, Git-Commit, Launch-Argumenten und Image-ID, aber ohne Umgebungsvariablen und Schluessel.
5. Es ruft `bag_check` auf und legt Bericht und Metadaten unter `validation/P-AD1/<name>/` ab; `--no-check` uebergeht das.

Das Skript sendet nichts und startet oder stoppt den Stack nicht.

## Pruefung mit bag_check

```bash
# im Container amr_ros2 oder amr_ros2_dev
ros2 run my_bot bag_check /amr_bags/<JJJJMMTT_HHMM>_<szene> -o bag_check.md
```

`bag_check` wertet aus:

- **je Topic:** Anzahl, mittlere und minimale Rate, Luecken groesser als 2 Sollperioden und Nachrichtengroesse; dazu fehlende erwartete Topics und abweichende Typen;
- **je Kante von `/tf`:** Rate und Luecken;
- **Stempelabstand:** Aufnahmezeit minus `header.stamp` als Median, P95 und Max. Ungesyncte MCU-Stempel (sec < 1e9) werden getrennt gezaehlt;
- **`/vision/detections`:** Anteil `capture_time <= timestamp`, Abstand `timestamp - capture_time`, Luecken und Ruecksprunge in `seq`;
- **Bewertung nach Anforderungsliste L1 v1.1, Abschnitt 10.2:** Anforderung, K0-Baseline, Messwert und Regressionstoleranz getrennt.

Der Exit-Code ist 0 ohne Befund, 1, wenn ein erwartetes Topic fehlt oder ein Typ abweicht, und 2 bei einem Bedien- oder Lesefehler.

## Wiedergabe ohne Roboter

Aufnahmen werden nur im dev-Container (`amr/docker/docker-compose.dev.yml`) abgespielt, auch auf dem Pi. Die Bedienung beschreibt `amr/docker/README.md`, Abschnitt "Entwicklung ohne Roboter".

```bash
cd amr/docker
docker compose -f docker-compose.dev.yml up -d           # auf dem Pi: up -d --no-build
docker compose -f docker-compose.dev.yml exec amr-dev /entrypoint.sh bash
ros2 bag play /amr_bags/<JJJJMMTT_HHMM>_<szene> --clock
```

!!! warning "Nie im Pi-Container abspielen"
    Der Pi-Container `amr_ros2` laeuft im Host-Netz mit `ROS_DOMAIN_ID=0`. Ein dort abgespieltes `/cmd_vel` erreicht den Fahrkern; `/nav_cmd_vel` und `/dashboard_cmd_vel` werden im laufenden Stack auf `/cmd_vel` weitergeleitet. Der dev-Container ist dagegen durch Bridge-Netz, `ROS_DOMAIN_ID=42` und `ROS_LOCALHOST_ONLY=1` isoliert.

## Grenzen der Zeitstempel

Die folgenden Punkte stammen aus dem Phase-0-Bericht K7-V, Abschnitte c bis e, mit Messung vom 2026-10-08.

- **Drei Zeitbasen:** Pi-Uhr (`/scan`, map->odom), MCU-Zeit des Fahrkerns (`/odom`, odom->base_link) und MCU-Zeit der Sensor- und Sicherheitsbasis (`/imu`, `/range/front`, `/battery`). Die MCU-Zeit wird einmal beim Boot mit dem micro-ROS-Agenten synchronisiert, ein Re-Sync fehlt. Die gemessene Drift lag bei etwa 15 bis 20 ppm, die MCU lief vor.
- **Publizierzeit statt Messzeit:** Die MCU-Knoten stempeln beim Publizieren, nicht bei der Messung. Das Messalter steckt deshalb nicht im Stempelabstand.
- **`/scan`:** Der Stempel markiert den Beginn des Umlaufs; beim Empfang ist ein Scan etwa 135 ms alt.
- **map->odom:** Die Kante ist um etwa 0,3 s in die Zukunft datiert (`transform_timeout`).
- **odom->base_link:** Der TF traegt bereits die MCU-Zeit aus `/odom` (Korrektur zu B-V3). Fuer K7 offen ist die Zeitbasis selbst: periodischer Re-Sync oder Stempelung auf der Pi-Seite.
- **Detektionen:** `capture_time` ist die Entnahme im Runner und eine Obergrenze des Bildzeitpunkts, keine Sensorzeit (B-V7, siehe [Vision-Pipeline](../vision_pipeline.md#detektions-json)).
- **Aufnahmezeit:** Sie ist der Empfang beim Recorder (Systemuhr des Pi), keine Sensorzeit.
