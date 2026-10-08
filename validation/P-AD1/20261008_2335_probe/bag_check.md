# bag_check: 20261008_2335_probe

| Feld | Inhalt |
| --- | --- |
| Aufnahme | `/amr_bags/20261008_2335_probe` |
| Szene | probe: Probeaufnahme (Selbsttest K7-V): Roboter steht, Launch-Argumente wie Szene a |
| Start (Systemuhr) | 2026-10-08 21:35:26 +0000 |
| Dauer | 9,3 s |
| Nachrichten | 1399 |
| Groesse | 1,49 MB |
| Speicher | sqlite3, rosbag2 0.15.16-1jammy.20260326.140657 |
| Git-Commit | 73b01989c6c36a8b6c1ed418afa3b48b5c05f883 (Arbeitsbaum mit Aenderungen) |
| Launch | `ros2 launch my_bot full_stack.launch.py use_camera:=True use_dashboard:=True use_vision:=True` |
| Abweichungen Launch | keine |

## 1 Ergebnis

- Fehlende erwartete Topics: keine
- Typabweichungen gegen den Katalog: keine

## 2 Topics

| Topic | Typ | Anzahl | Rate Mittel [Hz] | Rate Min [Hz] | Soll [Hz] | Luecken > 2 T | groesster Abstand [ms] | Groesse Mittel [B] | Summe [MB] | frame_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/scan` | sensor_msgs/msg/LaserScan | 69 | 7,57 | 7,15 | 7,0 | 0 | 140,0 | 11580 | 0,80 | laser |
| `/odom` | nav_msgs/msg/Odometry | 138 | 20,01 | 13,29 | 20,0 | 0 | 75,2 | 724 | 0,10 | odom |
| `/tf` | tf2_msgs/msg/TFMessage | 369 | 40,08 | 21,46 | – | – | 46,6 | 96 | 0,04 | – |
| `/tf_static` | tf2_msgs/msg/TFMessage | 3 | – | – | – | – | – | 105 | 0,00 | – |
| `/imu` | sensor_msgs/msg/Imu | 321 | 34,75 | 3,19 | 50,0 | 25 | 313,9 | 324 | 0,10 | base_link |
| `/range/front` | sensor_msgs/msg/Range | 80 | 8,66 | 2,54 | 10,0 | 6 | 393,0 | 52 | 0,00 | ultrasonic_link |
| `/cliff` | std_msgs/msg/Bool | 139 | 15,20 | 3,05 | 20,0 | 23 | 328,0 | 8 | 0,00 | – |
| `/battery` | sensor_msgs/msg/BatteryState | 18 | 2,04 | 1,39 | 2,0 | 0 | 718,0 | 84 | 0,00 | base_link |
| `/vision/detections` | std_msgs/msg/String | 39 | 5,00 | 4,55 | 5,0 | 0 | 219,7 | 132 | 0,01 | – |
| `/map` | nav_msgs/msg/OccupancyGrid | 19 | 2,02 | 1,98 | 2,0 | 0 | 504,8 | 9776 | 0,19 | map |
| `/pose` | geometry_msgs/msg/PoseWithCovarianceStamped | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/plan` | nav_msgs/msg/Path | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/lookahead_point` | geometry_msgs/msg/PointStamped | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/cmd_vel` | geometry_msgs/msg/Twist | 204 | 21,96 | 15,05 | 20,0 | 0 | 66,4 | 52 | 0,01 | – |
| `/nav_cmd_vel` | geometry_msgs/msg/Twist | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/dashboard_cmd_vel` | geometry_msgs/msg/Twist | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/emergency_stop` | std_msgs/msg/Bool | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |

## 3 TF-Kanten

| /tf-Kante | Anzahl | Rate Mittel [Hz] | Rate Min [Hz] | Soll [Hz] | Luecken > 2 T | groesster Abstand [ms] |
| --- | --- | --- | --- | --- | --- | --- |
| `map->odom` | 184 | 20,01 | 18,39 | 20,0 | 0 | 54,4 |
| `odom->base_link` | 185 | 20,04 | 13,24 | 20,0 | 0 | 75,5 |

Statische Kanten (/tf_static): base_link->camera_link, base_link->laser, base_link->ultrasonic_link

## 4 Stempelabstand: Aufnahmezeit minus Stempel [ms]

Positive Werte: Stempel liegt vor dem Empfang beim Recorder. Ungesyncte Stempel (sec < 1e9) sind nur gezaehlt.

| Topic / Kante | Zeitbasis | N | ungesynct | Min | Median | P95 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/scan` | Pi (rplidar_node) | 69 | 0 | 120,2 | 134,6 | 136,7 | 140,0 |
| `/odom` | MCU Fahrkern | 138 | 0 | -4,4 | -3,2 | -1,7 | 21,9 |
| `/imu` | MCU Sensor- und Sicherheitsbasis | 321 | 0 | -4,1 | -2,9 | -1,6 | 96,7 |
| `/range/front` | MCU Sensor- und Sicherheitsbasis | 80 | 0 | -4,2 | -3,6 | -1,2 | 78,4 |
| `/battery` | MCU Sensor- und Sicherheitsbasis | 18 | 0 | -4,2 | -3,8 | -3,3 | -1,6 |
| `/map` | Pi (slam_toolbox) | 19 | 0 | 136,7 | 200,6 | 251,6 | 256,7 |
| `/tf map->odom` | Pi (slam_toolbox) | 184 | 0 | -376,2 | -302,4 | -243,8 | -226,5 |
| `/tf odom->base_link` | MCU Fahrkern (aus /odom) | 185 | 0 | -3,4 | -1,6 | 2,4 | 23,4 |

## 5 Detektionen (/vision/detections)

| Kenngroesse | Wert |
| --- | --- |
| Pakete (davon ungueltiges JSON) | 39 (0) |
| Pakete mit Objekten | 0 |
| mit capture_time / mit seq | 39 / 39 |
| capture_time <= timestamp | 100,0 % (39/39) |
| timestamp - capture_time [ms] (Runner) | Median 37,9, P95 39,8, Max 47,5 |
| Aufnahmezeit - timestamp [ms] (UDP und ROS) | Median 3,7, P95 6,0, Max 9,3 |
| Aufnahmezeit - capture_time [ms] (gesamt) | Median 41,8, P95 43,6, Max 51,4 |
| seq | 522 bis 560, fehlend 0, Ruecksprunge 0 |

timestamp und capture_time sind Host-Uhr des Runners; die Aufnahmezeit ist Systemuhr desselben Pi. capture_time ist die Entnahme des Bildes im Runner und eine Obergrenze des Bildzeitpunkts (B-V7), keine Sensorzeit.

## 6 Bewertung nach L1 v1.1, Abschnitt 10.2

Anforderung, K0-Baseline, Messwert und Regressionstoleranz sind getrennt (L1 Abschnitt 10.1). Messwert: mittlere Rate ueber die Aufnahme.

| Groesse | Anforderung | K0-Baseline | Messwert | Regressionstoleranz | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| Odometrie-Rate (`/odom`) | NFA-03: >= 10 Hz | 19,85 Hz | 20,01 Hz | >= 15 Hz und nicht mehr als 25 % unter der Baseline | Anforderung erfuellt; Toleranz eingehalten (Grenze 15,00 Hz) |
| LiDAR-Scanrate (`/scan`) | NFA-02: >= 5 Hz | 7,51 Hz | 7,57 Hz | >= 5 Hz | Anforderung erfuellt; Toleranz eingehalten (Grenze 5,00 Hz) |
| IMU-Rate (`/imu`) | NFA-04: >= 20 Hz | 38,07 Hz | 34,75 Hz | >= 20 Hz und nicht mehr als 25 % unter der Baseline | Anforderung erfuellt; Toleranz eingehalten (Grenze 28,55 Hz) |
| Ultraschall-Rate (`/range/front`) | DoD Phase 2: >= 7,0 Hz | 9,06 Hz | 8,66 Hz | >= 7,0 Hz | Anforderung erfuellt; Toleranz eingehalten (Grenze 7,00 Hz) |
| Batterie-Rate (`/battery`) | keine eigene Anforderung (Firmware-Sollwert 2 Hz) | 2,00 Hz | 2,04 Hz | >= 1,5 Hz | Toleranz eingehalten (Grenze 1,50 Hz) |
| Kantensignal-Rate (`/cliff`) | keine eigene Anforderung (Firmware-Sollwert 20 Hz) | 15,86 Hz | 15,20 Hz | kein Abnahmekriterium ableitbar, solange OP-11 offen ist | kein Kriterium |
| Fahrbefehls-Rate auf dem Fahrkern-Topic (`/cmd_vel`) | keine eigene Anforderung | 20,00 Hz | 21,96 Hz | kein Regressionsmassstab, solange OP-11 offen ist | kein Kriterium |

## 7 Hinweise

- Aufnahmezeit = Empfang beim Recorder (Systemuhr). MCU-Stempel sind Publizierzeit, nicht Messzeit; das Messalter steckt nicht im Stempelabstand.
- /scan ist am Beginn des Umlaufs gestempelt, map->odom liegt um transform_timeout in der Zukunft (Phase-0-Bericht, Abschnitt c).
- Median und P95 nach naechstem Rang. Luecke: Abstand > 2 Sollperioden.
- Erzeugt mit amr/scripts/bag_check.py (K7-V).
