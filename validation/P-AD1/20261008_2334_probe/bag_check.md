# bag_check: 20261008_2334_probe

| Feld | Inhalt |
| --- | --- |
| Aufnahme | `/amr_bags/20261008_2334_probe` |
| Szene | probe: Probeaufnahme (Selbsttest K7-V): Roboter steht, Launch-Argumente wie Szene a |
| Start (Systemuhr) | 2026-10-08 21:34:10 +0000 |
| Dauer | 59,5 s |
| Nachrichten | 9502 |
| Groesse | 9,72 MB |
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
| `/scan` | sensor_msgs/msg/LaserScan | 450 | 7,57 | 7,19 | 7,0 | 0 | 139,1 | 11580 | 5,21 | laser |
| `/odom` | nav_msgs/msg/Odometry | 1189 | 20,00 | 13,30 | 20,0 | 0 | 75,2 | 724 | 0,86 | odom |
| `/tf` | tf2_msgs/msg/TFMessage | 2378 | 40,00 | 21,47 | – | – | 46,6 | 96 | 0,23 | – |
| `/tf_static` | tf2_msgs/msg/TFMessage | 3 | – | – | – | – | – | 105 | 0,00 | – |
| `/imu` | sensor_msgs/msg/Imu | 2240 | 38,86 | 2,51 | 50,0 | 97 | 398,1 | 324 | 0,73 | base_link |
| `/range/front` | sensor_msgs/msg/Range | 523 | 9,07 | 2,48 | 10,0 | 25 | 403,6 | 52 | 0,03 | ultrasonic_link |
| `/cliff` | std_msgs/msg/Bool | 930 | 16,14 | 2,50 | 20,0 | 99 | 400,8 | 8 | 0,01 | – |
| `/battery` | sensor_msgs/msg/BatteryState | 115 | 2,00 | 1,34 | 2,0 | 0 | 745,4 | 84 | 0,01 | base_link |
| `/vision/detections` | std_msgs/msg/String | 297 | 5,00 | 4,16 | 5,0 | 0 | 240,5 | 148 | 0,04 | – |
| `/map` | nav_msgs/msg/OccupancyGrid | 120 | 2,01 | 1,95 | 2,0 | 0 | 512,4 | 9776 | 1,17 | map |
| `/pose` | geometry_msgs/msg/PoseWithCovarianceStamped | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/plan` | nav_msgs/msg/Path | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/lookahead_point` | geometry_msgs/msg/PointStamped | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/cmd_vel` | geometry_msgs/msg/Twist | 1257 | 21,45 | 17,07 | 20,0 | 0 | 58,6 | 52 | 0,07 | – |
| `/nav_cmd_vel` | geometry_msgs/msg/Twist | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/dashboard_cmd_vel` | geometry_msgs/msg/Twist | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |
| `/emergency_stop` | std_msgs/msg/Bool | 0 | n/a | n/a | – | – | n/a | n/a | 0,00 | – |

## 3 TF-Kanten

| /tf-Kante | Anzahl | Rate Mittel [Hz] | Rate Min [Hz] | Soll [Hz] | Luecken > 2 T | groesster Abstand [ms] |
| --- | --- | --- | --- | --- | --- | --- |
| `map->odom` | 1189 | 20,00 | 17,89 | 20,0 | 0 | 55,9 |
| `odom->base_link` | 1189 | 20,00 | 13,22 | 20,0 | 0 | 75,7 |

Statische Kanten (/tf_static): base_link->camera_link, base_link->laser, base_link->ultrasonic_link

## 4 Stempelabstand: Aufnahmezeit minus Stempel [ms]

Positive Werte: Stempel liegt vor dem Empfang beim Recorder. Ungesyncte Stempel (sec < 1e9) sind nur gezaehlt.

| Topic / Kante | Zeitbasis | N | ungesynct | Min | Median | P95 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/scan` | Pi (rplidar_node) | 450 | 0 | 118,8 | 134,7 | 136,3 | 138,8 |
| `/odom` | MCU Fahrkern | 1189 | 0 | -3,7 | -1,8 | -0,4 | 27,5 |
| `/imu` | MCU Sensor- und Sicherheitsbasis | 2240 | 0 | -3,3 | -1,6 | -0,3 | 99,4 |
| `/range/front` | MCU Sensor- und Sicherheitsbasis | 523 | 0 | -3,4 | -2,1 | -0,6 | 96,3 |
| `/battery` | MCU Sensor- und Sicherheitsbasis | 115 | 0 | -3,4 | -2,2 | -0,9 | 96,9 |
| `/map` | Pi (slam_toolbox) | 120 | 0 | 129,2 | 202,1 | 262,1 | 354,6 |
| `/tf map->odom` | Pi (slam_toolbox) | 1189 | 0 | -376,8 | -301,9 | -242,2 | -228,5 |
| `/tf odom->base_link` | MCU Fahrkern (aus /odom) | 1189 | 0 | -2,5 | -0,6 | 1,4 | 28,4 |

## 5 Detektionen (/vision/detections)

| Kenngroesse | Wert |
| --- | --- |
| Pakete (davon ungueltiges JSON) | 297 (0) |
| Pakete mit Objekten | 56 |
| mit capture_time / mit seq | 297 / 297 |
| capture_time <= timestamp | 100,0 % (297/297) |
| timestamp - capture_time [ms] (Runner) | Median 38,0, P95 40,4, Max 68,9 |
| Aufnahmezeit - timestamp [ms] (UDP und ROS) | Median 5,8, P95 10,2, Max 12,1 |
| Aufnahmezeit - capture_time [ms] (gesamt) | Median 44,1, P95 48,9, Max 74,5 |
| seq | 136 bis 432, fehlend 0, Ruecksprunge 0 |

timestamp und capture_time sind Host-Uhr des Runners; die Aufnahmezeit ist Systemuhr desselben Pi. capture_time ist die Entnahme des Bildes im Runner und eine Obergrenze des Bildzeitpunkts (B-V7), keine Sensorzeit.

## 6 Bewertung nach L1 v1.1, Abschnitt 10.2

Anforderung, K0-Baseline, Messwert und Regressionstoleranz sind getrennt (L1 Abschnitt 10.1). Messwert: mittlere Rate ueber die Aufnahme.

| Groesse | Anforderung | K0-Baseline | Messwert | Regressionstoleranz | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| Odometrie-Rate (`/odom`) | NFA-03: >= 10 Hz | 19,85 Hz | 20,00 Hz | >= 15 Hz und nicht mehr als 25 % unter der Baseline | Anforderung erfuellt; Toleranz eingehalten (Grenze 15,00 Hz) |
| LiDAR-Scanrate (`/scan`) | NFA-02: >= 5 Hz | 7,51 Hz | 7,57 Hz | >= 5 Hz | Anforderung erfuellt; Toleranz eingehalten (Grenze 5,00 Hz) |
| IMU-Rate (`/imu`) | NFA-04: >= 20 Hz | 38,07 Hz | 38,86 Hz | >= 20 Hz und nicht mehr als 25 % unter der Baseline | Anforderung erfuellt; Toleranz eingehalten (Grenze 28,55 Hz) |
| Ultraschall-Rate (`/range/front`) | DoD Phase 2: >= 7,0 Hz | 9,06 Hz | 9,07 Hz | >= 7,0 Hz | Anforderung erfuellt; Toleranz eingehalten (Grenze 7,00 Hz) |
| Batterie-Rate (`/battery`) | keine eigene Anforderung (Firmware-Sollwert 2 Hz) | 2,00 Hz | 2,00 Hz | >= 1,5 Hz | Toleranz eingehalten (Grenze 1,50 Hz) |
| Kantensignal-Rate (`/cliff`) | keine eigene Anforderung (Firmware-Sollwert 20 Hz) | 15,86 Hz | 16,14 Hz | kein Abnahmekriterium ableitbar, solange OP-11 offen ist | kein Kriterium |
| Fahrbefehls-Rate auf dem Fahrkern-Topic (`/cmd_vel`) | keine eigene Anforderung | 20,00 Hz | 21,45 Hz | kein Regressionsmassstab, solange OP-11 offen ist | kein Kriterium |

## 7 Hinweise

- Aufnahmezeit = Empfang beim Recorder (Systemuhr). MCU-Stempel sind Publizierzeit, nicht Messzeit; das Messalter steckt nicht im Stempelabstand.
- /scan ist am Beginn des Umlaufs gestempelt, map->odom liegt um transform_timeout in der Zukunft (Phase-0-Bericht, Abschnitt c).
- Median und P95 nach naechstem Rang. Luecke: Abstand > 2 Sollperioden.
- Erzeugt mit amr/scripts/bag_check.py (K7-V).
