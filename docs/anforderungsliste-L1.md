---
description: >-
  VDI-2206-Anforderungsliste (L1) mit funktionalen und
  nicht-funktionalen Anforderungen.
---

# Anforderungsliste L1 – Autonomer Mobiler Roboter (AMR)

## Kopfbereich

| Feld               | Inhalt                                                              |
|---------------------|---------------------------------------------------------------------|
| Projekt             | Autonomer Mobiler Roboter (AMR) fuer Intralogistik mit KLT-Transport |
| Dokumenttyp         | Anforderungsliste nach VDI 2206, Stufe L1 (Lastenheft)             |
| Version             | 1.1 (Erweiterung K1, siehe Abschnitt 11)                            |
| Datum               | 2026-09-02 (Erstfassung 2026-03-22)                                 |
| Autor               | Jan                                                                 |
| VDI-2206-Stufe      | L1 – Anforderungen definieren                                      |
| Projektfragen       | PF1 (Echtzeitarchitektur), PF2 (Navigationsgenauigkeit), PF3 (Navigation und Bedien- und Leitstandsebene) |
| Firmware-Versionen  | config_drive.h v4.0.0, config_sensors.h v3.0.0                     |
| Nav2-Konfiguration  | nav2_params.yaml, mapper_params_online_async.yaml                   |

---

## Kfz-Analogie (Einordnung)

Die vorliegende Anforderungsliste orientiert sich an der Denkweise einer Kfz-Typgenehmigung (Homologation) nach europaeischem Recht. Im Automobilbereich definiert ISO 26262 die funktionale Sicherheit ueber ASIL-Stufen (Automotive Safety Integrity Level), wobei jedes Sicherheitsziel eine Fehlertoleranzzeit und eine Pruefvorschrift erhaelt. Das AMR-Projekt nutzt keine formale ASIL-Einstufung, uebertraegt jedoch die Struktur: Jede Anforderung benennt eine Funktion oder Gefaehrdung, einen messbaren Schwellwert und einen Nachweis. Die Spalte "Kfz-Pendant" ordnet jede AMR-Anforderung einem bekannten Automobilkonzept zu, damit der Leser die Parallele zwischen Roboter und Fahrzeug nachvollziehen kann. Wie bei einer Kfz-Einzelabnahme (HU/TUeV) erfordert jede Anforderung einen dokumentierten Nachweis — fehlt dieser, entspricht das einer fehlenden Bremswegmessung im Pruefbericht. Die Rueckverfolgbarkeitsmatrix am Ende dieses Dokuments ordnet jede Anforderung einer V-Modell-Pruefebene (Pruefstandtest, Fahrversuch, Typgenehmigung) zu, analog zu den drei Stufen einer Kfz-Zulassung.

---

## Einsatzszenario

Der AMR operiert in einer strukturierten Indoor-Umgebung (Buero, Labor, Lager) auf ebenem Boden mit bekannten, kartierbaren Strukturen. Diese Operational Design Domain (ODD) entspricht einem Level-4-Fahrzeug auf einem abgesperrten Betriebsgelaende: Der Roboter navigiert autonom innerhalb der definierten Umgebung, benoetigt jedoch keinen Betrieb auf oeffentlichen Strassen oder unter Witterungseinfluss.

| Merkmal              | Auspraegung                                          | Kfz-Vergleich                        |
|----------------------|------------------------------------------------------|--------------------------------------|
| Antriebskonzept      | Differentialantrieb, zwei Motoren JGA25-370 (1:34)   | Heckantrieb mit Differentialsperre   |
| Rechenarchitektur    | Raspberry Pi 5 (zentral) + 2x ESP32-S3 (dezentral)  | ADAS-Zentralrechner + ECU-Verbund    |
| Kommunikation        | micro-ROS/UART 921600 Baud + CAN-Bus 1 Mbit/s       | CAN-FD + Ethernet (Dual-Path)        |
| Sensorik             | LiDAR, IMU, Ultraschall, Cliff, Kamera + Hailo-8L   | Lidar, ESP, ABS, PDC, Frontkamera    |
| Geschwindigkeit      | 0,15 m/s autonom / 0,40 m/s manuell                 | v_max autonom (L4) / manuell (L0)    |
| Sicherheitskonzept   | Cliff-Safety-Knoten + CAN-Direktpfad + Failsafe     | AEB + redundanter Bremskreis + Watchdog |
| Benutzeroberflaeche  | React-Dashboard (WebSocket + MJPEG)                  | Kombiinstrument + Infotainment       |
| Sprachschnittstelle  | ReSpeaker + Gemini Audio-STT / faster-whisper Fallback → Intent → Missionskommando | Sprachsteuerung im Fahrzeuginnenraum (Cloud + Offline-Fallback) |

---

## 4 Funktionale Anforderungen (FA)

### 4.1 Ebene A – Fahrkern

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| FA-01 | PF2 | MUSS | SLAM Toolbox erzeugt konsistentes Occupancy Grid der Einsatzumgebung | Raumabdeckung, Kartenaufloesung | >= 95 % Abdeckung, 0,05 m Raster | HD-Karte | mapper_params (resolution: 0,05) | IT-04 (slam_validation) | Erfuellt |
| FA-02 | PF2 | MUSS | Lokalisierungsfehler bei Geradeausfahrt mit IMU-Korrektur | Lateralversatz, Heading-Fehler | <= 5 cm lateral, <= 5 Grad Heading (Ist: 2,1 cm / 0,06 Grad) | GPS-Genauigkeit | Messprotokoll P1/P2, config_drive.h | IT-03 (straight_drive_test) | Erfuellt |
| FA-03 | PF2 | MUSS | Zielpunktanfahrt mit definierter Genauigkeit | XY-Abweichung, Gier-Abweichung | <= 0,03 m xy, <= 0,05 rad yaw (Ist: 0,0101 m / 0,0339 rad) | Parkgenauigkeit APA | nav2_params (Goal Checker), Messprotokoll P4 | IT-06 (nav_square_test) | Erfuellt |
| FA-04 | PF2 | MUSS | Statische Hindernisse umfahren ohne Kontakt | Kollisionsereignisse, Inflationsradius | 0 Kollisionen, Inflation >= 0,25 m | Abstandswarnung | nav2_params (inflation_radius: 0,25) | IT-05 (nav_test) | Erfuellt |
| FA-05 | PF2 | SOLL | Dynamischen Hindernissen (Personen) ausweichen | Passierabstand | >= 12 cm (Ist: 12 cm, qualitativ) | AEB-Teilbremsung | Messung Kap. 6 (kein Protokoll, A-F02) | IT-05 (nav_test) | Teilweise erfuellt |
| FA-06 | PF1 | MUSS | Geradeausfahrt 1 m mit reproduzierbarem Ergebnis | Lateralversatz, Heading-Fehler | < 5 cm Drift, < 5 Grad Heading (Ist: 2,1 cm / 0,06 Grad mit IMU) | Spurhaltung LKA | Messprotokoll P1/P2, config_drive.h (wheel_diameter: 65,67 mm) | IT-03 (straight_drive_test) | Erfuellt |
| FA-07 | PF1 | MUSS | Rotation 360 Grad mit definierter Winkeltreue | Winkelfehler | < 5 Grad (Ist: 1,88 Grad) | Lenkwinkelkalibrierung | Messprotokoll P1/P2, config_drive.h (wheel_base: 178,0 mm) | IT-02 (rotation_test) | Erfuellt |
| FA-08 | ueberg. | MUSS | Teleop-Fernsteuerung ueber /cmd_vel im manuellen Modus | Maximalgeschwindigkeit | max 0,40 m/s (Joystick) | Manueller Fahrmodus L0 | Dashboard-Konfiguration | IT-09 (dashboard_latency_test) | Erfuellt |
| FA-09 | PF2 | SOLL | Gespeicherte Karte beim Neustart laden (map_server) | Kartenverfuegbarkeit | Karte nach Neustart nutzbar | Karten-Update Navi | SLAM Toolbox (Serialize/Deserialize) | IT-04 (slam_validation) | Offen |
| FA-10 | PF2 | MUSS | 10 Zielanfahrten ohne Kollision absolvieren | Kollisionsfreie Anfahrten | 10/10 kollisionsfrei (Ist: 4/4 WP + 10/10 Docking) | Typ-Fahrversuch | Messprotokoll P4, kapitel_03 (F04) | SV-01 | Erfuellt |
| FA-11 | PF2 | SOLL | Recovery-Verhalten loest Blockaden und Sackgassen | Recovery-Erfolgsquote | >= 80 % (Ist: 80 %, qualitativ) | Ausfallbehandlung | Messung Kap. 6 (kein Protokoll, A-F02) | IT-05 (nav_test) | Teilweise erfuellt |

### 4.2 Ebene B – Bedien- und Leitstandsebene

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| FA-12 | ueberg. | MUSS | Echtzeit-Telemetrie ueber WebSocket und MJPEG-Stream | Telemetrie-Rate, Ports | >= 4 Hz Telemetrie, WS 9090, MJPEG 8082 (Ist: 9,9 Hz) | Kombiinstrument | Messprotokoll P5 (Test 5.2), dashboard_bridge.py | SV-03 | Erfuellt |
| FA-13 | ueberg. | MUSS | Joystick-Fernsteuerung mit Deadman-Sicherung | Befehlslatenz, Deadman-Timeout | Latenz < 300 ms, Deadman < 500 ms (Ist: 5,9 ms / 251,6 ms) | Fernbedienung | Messprotokoll P5 (Test 5.1, 5.3) | IT-09 (dashboard_latency_test) | Erfuellt |
| FA-14 | ueberg. | SOLL | Validierungstab zeigt Phase-5-Testergebnisse an | Dargestellte Testfaelle | >= 5 Phase-5-Tests sichtbar | Diagnosemodus OBD | Messprotokoll P5, Dashboard TestPanel | SV-03 | Erfuellt |

### 4.3 Ebene C – Intelligente Interaktion

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| FA-15 | PF3 | SOLL | Kameraobjekterkennung ueber Hailo-8L und Gemini-Semantik | Inferenzzeit | < 50 ms (Ist: 34 ms) | ADAS-Objekterkennung | Messung Kap. 6 (kein eigenes Protokoll) | SV-02 | Erfuellt |
| FA-16 | PF3 | MUSS | ArUco-Docking mit reproduzierbarer Genauigkeit | Erfolgsquote, lateraler Versatz | >= 80 % Erfolg, < 2 cm Versatz (Ist: 100 % / 0,73 cm) | Einparken APA | Messprotokoll P4 (Test 4.2) | IT-07 (docking_test) | Erfuellt |
| FA-17 | PF3 | KANN | Sprachschnittstelle wandelt Sprache in Missionskommandos | Befehlsannahme | Intent-Erkennung und Missionsausloesung | Sprachsteuerung HMI | voice_command_node, kapitel_03 (F07) | SV-03 | Erfuellt |

### 4.4 Funktionskette automatisiertes Fahren (Erweiterung K1)

Die folgenden Anforderungen bilden die Kette Sensorvorverarbeitung,
Wahrnehmung, Lokalisierung, Umfeldmodell, Praediktion, Verhaltensentscheidung
und Trajektorienplanung ab. Sie sind zum Zeitpunkt der Aufnahme saemtlich
offen; die Umsetzung erfolgt in den Ausbaupaketen K7 bis K10.

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| FA-18 | PF2 | MUSS | Sensorvorverarbeitung liefert zeitsynchronisierte und plausibilisierte Sensordaten an die Wahrnehmung | Zeitstempelversatz der fusionierten Quellen | <= 50 ms | Sensor-Preprocessing-Steuergeraet | Ausbaupaket K8 | IT-12 | Offen |
| FA-19 | PF2 | MUSS | Umfeldmodell fuehrt LiDAR-Cluster, Ultraschall und Kameradetektionen zu einer Objektliste mit stabiler Verfolgungskennung zusammen | Konstanz der Verfolgungskennung bei statischem Objekt ueber 5 s | >= 90 % | Umfeldmodell (Sensorfusion) | Ausbaupaket K8 | IT-12 | Offen |
| FA-20 | PF2 | SOLL | Praediktion schaetzt Objekttrajektorien ueber einen definierten Horizont; der Nachweis erfolgt eigenstaendig gegen eine vermessene Referenztrajektorie | Prognosehorizont, Positionsfehler nach 1 s gegen die Referenztrajektorie, ausgewiesen als Mittelwert und 95-Prozent-Quantil ueber mindestens 30 Vorhersagen | Horizont >= 2 s, Fehler <= 0,25 m | Objektpraediktion ADAS | Ausbaupaket K9 | IT-15 | Offen |
| FA-21 | PF2 | MUSS | Verhaltensentscheidung waehlt aus Umfeldmodell und Praediktion ein Fahrmanoever | Anzahl Zustaende, Umschaltzeit | >= 5 Zustaende, Umschaltung <= 200 ms | Manoeverentscheidung SAE L3 | Ausbaupaket K9 | IT-13 | Offen |
| FA-22 | PF2 | MUSS | Trajektorienplanung erzeugt aus der Verhaltensvorgabe eine kollisionsfreie Solltrajektorie fuer die Fahrzeugbewegungsregelung | Kollisionsereignisse, Planungsrate | 0 Kollisionen bei 10 Zielanfahrten, >= 2 Hz | Trajektorienplaner | Ausbaupaket K9 | IT-14 | Offen |
| FA-23 | PF3 | KANN | Radarziele werden in das Umfeldmodell fusioniert; der Nachweis erfolgt in K7 mit simulierten und in K10 mit realen Zielen | Fusionsnachweis | Radar- und LiDAR-Detektion desselben Objekts ergeben eine gemeinsame Verfolgungskennung | Radarfusion ADAS | Ausbaupakete K7 und K10 | T-12, T-13 | Offen |

---

## 5 Nicht-funktionale Anforderungen (NFA)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| NFA-01 | PF1 | MUSS | PID-Regelfrequenz im Fahrkern deterministisch | Zyklusrate, Jitter | >= 50 Hz, Jitter < 2 ms (Ist: 50 Hz, < 2 ms) | ECU-Zykluszeit | config_drive.h (control_loop_hz: 50), Messprotokoll P1/P2 | T-01 (motor_test) | Erfuellt |
| NFA-02 | PF2 | MUSS | LiDAR-Scan-Rate genuegt fuer SLAM und Navigation | Scan-Frequenz | >= 5 Hz (Ist-Messwert: 7,7 Hz; Datenblatt: 5,5 Hz typ.) | Lidar-Scanrate | Datenblatt RPLIDAR A1, Messprotokoll P3 | T-06 (rplidar_test) | Erfuellt |
| NFA-03 | PF1 | MUSS | Odometrie-Publikationsrate genuegt fuer Regelkreis | Odometrie-Rate | >= 10 Hz (Soll: 20 Hz, Ist: 18,3–18,8 Hz) | ABS-Raddrehzahl-Zyklus | config_drive.h (odom_publish_hz: 20), Messprotokoll P3 | T-02 (encoder_test) | Erfuellt |
| NFA-04 | PF1 | MUSS | IMU-Abtastrate genuegt fuer Sensorfusion | IMU-Rate | >= 20 Hz (Soll: 50 Hz, Ist: 30–35 Hz) | ESP-Sensorrate | config_sensors.h (imu_sample_hz: 50), Messprotokoll P2 | T-04 (imu_test) | Erfuellt |
| NFA-05 | PF2 | MUSS | Autonome Maximalgeschwindigkeit (RPP-Regler) begrenzt | Lineargeschwindigkeit | <= 0,15 m/s | v_max autonom L4 | nav2_params.yaml (desired_linear_vel: 0,15) | IT-05 (nav_test) | Erfuellt |
| NFA-06 | ueberg. | MUSS | Manuelle Maximalgeschwindigkeit (Joystick) begrenzt | Lineargeschwindigkeit | <= 0,40 m/s | v_max manuell L0 | Dashboard-Konfiguration | IT-09 (dashboard_latency_test) | Erfuellt |
| NFA-07 | PF2 | MUSS | Maximale Drehrate begrenzt | Winkelgeschwindigkeit | <= 1,0 rad/s | Lenkgeschwindigkeit | nav2_params.yaml | IT-02 (rotation_test) | Erfuellt |
| NFA-08 | ueberg. | SOLL | Betriebsdauer unter Last genuegt fuer Validierungszyklus | Laufzeit | >= 30 min unter Last | Reichweite WLTP | Berechnung (Samsung INR18650-35E, 3,35 Ah, 3S1P) | — | Offen |
| NFA-09 | PF1 | SOLL | CPU-Last des Pi 5 laesst Headroom fuer Erweiterungen | CPU-Auslastung | < 80 % (Ist: < 80 %) | Rechenlast ADAS-ECU | Messung Kap. 6 (kein eigenes Protokoll) | SV-03 | Teilweise erfuellt |
| NFA-10 | PF1 | MUSS | Datenverlust auf micro-ROS-Strecke vernachlaessigbar | Paketverlustrate | < 0,1 % (Ist: < 0,1 %) | CAN-Frameverlust | Messprotokoll P1/P2 | T-08 (serial_latency_logger) | Erfuellt |
| NFA-11 | PF2 | MUSS | Absolute Trajectory Error (ATE) bei Pfadverfolgung | Mittlerer Positionsfehler | < 0,20 m (Ist: MAE 0,161 m / RMSE 0,190 m (T3.1), RMSE 0,030 m (T3.2)) | Pfadfolgefehler | Messprotokoll P3 (Achtung A-F04: ATE ≠ RMSE) | IT-04 (slam_validation) | Erfuellt |
| NFA-12 | PF1 | SOLL | RPP-Controller-Rate bietet genuegend Headroom | Controller-Ausfuehrungsrate | > 1000 Hz (Ist: > 2000 Hz) | Regler-Headroom | Messung Kap. 6 (kein eigenes Protokoll) | IT-05 (nav_test) | Teilweise erfuellt |

### 5.1 Nicht-funktionale Anforderungen der Steuergeraetearchitektur (Erweiterung K1)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| NFA-13 | PF1 | MUSS | CAN-Buslast laesst im Betriebsbus-Modus Reserve fuer Erweiterungen | Buslast bei 1 Mbit/s | <= 30 % | Buslastbudget CAN | Ausbaupakete K3 und K6 | T-10 | Offen |
| NFA-14 | PF1 | MUSS | Latenz eines Fahrbefehls vom Pi 5 bis zur Stellgroesse im Fahrkern ueber CAN | Ende-zu-Ende-Latenz, p95 | <= 40 ms | Antriebs-CAN-Latenz | Ausbaupaket K4 | T-11 | Offen |
| NFA-15 | PF1 | SOLL | Frame-Jitter periodischer CAN-Nachrichten bleibt begrenzt | Standardabweichung der Zwischenankunftszeit | <= 20 % der Nominalperiode | CAN-Zykluszeittreue | Ausbaupaket K3 | T-10 | Offen |
| NFA-16 | PF1 | MUSS | Transportgleichheit: ein ueber CAN uebertragener Messwert entspricht dem ueber den Referenzpfad uebertragenen Wert desselben Quellzyklus im Rahmen des jeweiligen Encodings | Wertabweichung je Signalklasse (siehe Abschnitt 12) | float32-Signale: 0; quantisierte Signale: <= 1 Quantisierungsstufe | Signalgleichheit redundanter Buspfade | Ausbaupakete K3 und K4, Abschnitt 12 | IT-10 | Offen |
| NFA-17 | PF2 | SOLL | Ende-zu-Ende-Latenz der Funktionskette von der Sensorzeitmarke bis zur Solltrajektorie | Latenz, p95 | <= 200 ms | ADAS-Verarbeitungskette | Ausbaupaket K9 | IT-14 | Offen |
| NFA-18 | PF1 | MUSS | Zeit vom Ausbleiben der aktiven Fahrbefehlsquelle bis zum sicheren Stillstand; ein selbsttaetiger Quellenwechsel findet dabei nicht statt | Zeit bis v = 0 und omega = 0 | <= 300 ms | Sollwert-Timeout Antriebssteuergeraet | Ausbaupaket K5, SIA-11 | IT-11 | Offen |
| NFA-19 | PF1 | MUSS | Frameverlust je periodischer CAN-Nachricht bleibt begrenzt | Anteil fehlender Frames je CAN-ID ueber 120 s | <= 1 % je ID | Uebertragungsguete CAN | Ausbaupaket K3, Gate vor K4 | T-10 | Offen (BA-01: 4,58 % auf 0x200) |
| NFA-20 | PF1 | MUSS | Zeitversatz zwischen der CAN-Uebertragung und dem Referenzpfad fuer dasselbe Messsignal | Median und 95-Prozent-Quantil des Zeitversatzes zugeordneter Wertepaare | Median <= 25 ms, 95-Prozent-Quantil <= 60 ms (Herleitung in Abschnitt 12.4) | Signallaufzeitunterschied redundanter Buspfade | Ausbaupakete K3 und K4, Abschnitt 12 | IT-10 | Offen |

---

## 6 Schnittstellenanforderungen (SA)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| SA-01 | PF1 | MUSS | Fahrkern-Knoten kommuniziert mit Pi 5 ueber micro-ROS/UART | Baudrate, Geraetepfad | 921600 Baud, /dev/amr_drive | CAN-FD ECU-Bus | config_drive.h, full_stack.launch.py | T-08 (serial_latency_logger) | Erfuellt |
| SA-02 | PF1 | MUSS | Sensor- und Sicherheitsbasis kommuniziert mit Pi 5 ueber micro-ROS/UART | Baudrate, Geraetepfad | 921600 Baud, /dev/amr_sensor | CAN-FD Sensor-Bus | config_sensors.h, full_stack.launch.py | T-08 (serial_latency_logger) | Erfuellt |
| SA-03 | PF1 | SOLL | CAN-Bus als redundanter Kommunikationspfad verfuegbar | Bitrate, Norm | 1 Mbit/s, ISO 11898, SN65HVD230 | Redundanter Bremskreis | config_drive.h (can::bitrate: 1000000) | IT-08 (can_validation_test) | Erfuellt |
| SA-04 | ueberg. | MUSS | ROS-2-Topics fuer Sensorik, Aktorik und Navigation definiert | Topic-Liste, QoS | /odom, /scan, /imu, /cmd_vel, /cliff, /battery, /range/front | Signalliste CAN-DB | full_stack.launch.py, nav2_params.yaml | SV-03 | Erfuellt |
| SA-05 | ueberg. | MUSS | TF-Baum bildet Sensorpositionen korrekt ab | TF-Transformationen | base_link→laser (z=0,235 m, yaw=pi), base_link→ultrasonic_link (x=0,15 m, z=0,05 m) | Sensoreinbaulage | full_stack.launch.py (Audit D-F01/D-F02) | IT-04 (slam_validation) | Erfuellt |
| SA-06 | PF1 | MUSS | I2C-Bus bedient IMU, Batteriemonitor und Servotreiber | Taktrate, Adressen | 400 kHz, MPU6050 0x68, INA260 0x40, PCA9685 0x41 | LIN-Bus | config_sensors.h (master_freq_hz: 400000) | T-05 (sensor_test) | Erfuellt |
| SA-07 | ueberg. | SOLL | Benutzeroberflaeche kommuniziert ueber WebSocket und MJPEG | Ports, Protokoll | WS 9090 (wss://), MJPEG 8082 (https://), Vite 5173 | Infotainment-Bus | dashboard_bridge.py, vite.config.ts | IT-09 (dashboard_latency_test) | Erfuellt |
| SA-08 | PF3 | SOLL | Vision-Pipeline verbindet Hailo-Host mit Docker-Container | Transportprotokoll | Hailo Host → UDP 5005 → Docker → Gemini Cloud | ADAS-Ethernet | host_hailo_runner.py, hailo_udp_receiver_node | SV-02 | Erfuellt |
| SA-09 | PF1 | MUSS | XRCE-DDS-Middleware haelt MTU-Grenzen ein | MTU, Nachrichtengroesse | MTU 512 Bytes, Odom-Nachricht 725 Bytes (fragmentiert) | SOME/IP Middleware | micro-ROS-Konfiguration | T-08 (serial_latency_logger) | Erfuellt |

### 6.1 Schnittstellenanforderungen der Steuergeraetearchitektur (Erweiterung K1)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| SA-10 | PF1 | MUSS | Die CAN-Signalmatrix liegt als versionierte Signaldatenbank vor und ist alleinige Quelle fuer Firmware-Konstanten und Pi-seitige Dekodierung | Abweichungen zwischen Signaldatenbank und abgeleiteten Artefakten | 0 Abweichungen | CAN-Datenbank (DBC) | Ausbaupaket K2 | T-09 | Offen |
| SA-11 | PF1 | MUSS | Das Fahrzeug-CAN-Gateway sendet den zuletzt gueltigen Fahrbefehl zyklisch mit 50 Hz, unabhaengig von der Aktualisierungsrate des ROS-2-Eingangstopics; ein neuer Sollwert aktualisiert den gehaltenen Wert. Zusaetzlich wird der Betriebsmodus uebertragen. | Sendefrequenz auf dem Bus bei beliebiger Eingangsrate, Nutzdatenlaenge | 50 Hz +/- 10 % auch bei ruhendem oder unregelmaessigem Eingangstopic, 8 Byte | Antriebs-CAN Sollwertuebertragung | Ausbaupaket K4, Abschnitt 13 | T-11, IT-11 | Offen |
| SA-12 | PF1 | MUSS | Genau ein ROS-2-Knoten kapselt den gesamten CAN-Zugriff des Pi 5 in Sende- und Empfangsrichtung | Anzahl Knoten mit SocketCAN-Zugriff | genau 1 | Zentrales Gateway-Steuergeraet | Ausbaupaket K6 | SV-04 | Offen |
| SA-13 | PF3 | SOLL | Radar-Abstraktionsschnittstelle mit Nachrichtendefinition, Koordinatensystem und abschaltbarem Simulationsmodus; die Abstraktion ist von der Datenquelle unabhaengig | Topic, Transformation, Publikationsrate im Simulationsmodus | `/radar/targets`, `base_link` nach `radar_link`, >= 10 Hz | Sensorabstraktion Restbussimulation | Ausbaupaket K7 | T-12 | Offen |
| SA-14 | PF2 | MUSS | Die Umfeldmodell-Schnittstelle ist als versionierte ROS-2-Nachricht definiert | Topic, Publikationsrate | `/environment/objects`, >= 5 Hz | Objektliste im Umfeldmodell | Ausbaupakete K7 und K8 | IT-12 | Offen |
| SA-15 | PF1 | SOLL | Der Gesundheitszustand des CAN-Busses wird nach ROS 2 publiziert | Topic, Publikationsrate, Inhalt | `/can/health`, >= 1 Hz, Busfehlerzustand und Frame-Alter je ID | Bus-Diagnose (OBD) | Ausbaupaket K3 | T-10 | Offen |
| SA-16 | PF1 | MUSS | Der USB-Pfad ist nach der Umstellung als Service-, Flash- und Debugpfad definiert und nicht mehr Betriebspfad | Rolle des USB-Pfads im Betrieb | keine Betriebsdaten ueber USB im CAN-Betriebsmodus | Diagnoseschnittstelle Werkstatt | Ausbaupaket K6 | SV-04 | Offen |
| SA-17 | PF3 | SOLL | Reale Anbindung des Radarsensors BGT60TR13C ueber SPI3 an den Pi 5; die Abstraktionsschnittstelle aus SA-13 bleibt dabei unveraendert | Publikationsrate aus der Hardware, Entfernungsfehler | >= 10 Hz, Entfernungsfehler < 5 cm im Bereich 0,5 bis 2,0 m | Radar-Nahbereichssensor | Ausbaupaket K10 | T-13 | Offen |
| SA-18 | PF1 | MUSS | Rohdatenstroeme der Umfeldsensorik (Radar, Kamera, LiDAR) werden nicht ueber den Classic-CAN-Bus uebertragen; sie sind direkt am Pi 5 angebunden | Anzahl Rohdaten-Nachrichten auf dem CAN-Bus | 0 | Trennung von Sensor- und Steuergeraetebus | Ausbaupakete K7 und K10, `docs/architecture/zielarchitektur.md` | T-12, T-13 | Offen |

---

## 7 Sicherheitsanforderungen (SIA)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| SIA-01 | PF1 | MUSS | Cliff-Erkennung stoppt Motoren innerhalb definierter Latenz | End-to-End-Latenz, Bremsweg | < 50 ms (Ist: 2,0 ms), Bremsweg 1,0 cm bei 0,2 m/s | AEB-Ansprechzeit | Messprotokoll P2 (Test 2.1), cliff_safety_node.py | T-07 (cliff_latency_test) | Erfuellt |
| SIA-02 | PF1 | MUSS | Ultraschall-Naeherungsstopp mit Hysterese gegen Flattern | Stopp-Schwelle, Freigabe-Schwelle | Stopp < 100 mm, Freigabe > 140 mm | AEB-Schwellen | cliff_safety_node.py (_obstacle_stop_m: 0,10) | T-05 (sensor_test) | Erfuellt |
| SIA-03 | PF1 | MUSS | CAN-Direktpfad leitet Cliff-Signal ohne ROS 2 an Fahrkern | CAN-Latenz | < 20 ms (ohne ROS 2) | Redundanter Bremskreis | config_sensors.h (id_cliff: 0x120), config_drive.h (id_cliff_rx: 0x120) | IT-08 (can_validation_test) | Erfuellt |
| SIA-04 | PF1 | MUSS | Failsafe-Timeout stoppt Motoren bei Verbindungsverlust | Timeout-Dauer | 500 ms → Motorenstopp (v=0, omega=0) | Watchdog-Timeout ECU | config_drive.h (failsafe_timeout_ms: 500) | T-01 (motor_test) | Erfuellt |
| SIA-05 | PF1 | MUSS | Watchdog-Alive-Counter erkennt Kommunikationsausfall | Fehlende Zyklen | 50 Zyklen → Verbindungsverlust | Alive-Counter CAN | config_drive.h (watchdog_miss_limit: 50) | T-01 (motor_test) | Erfuellt |
| SIA-06 | PF2 | MUSS | Costmap-Inflation haelt Sicherheitsabstand um Hindernisse | Inflationsradius | >= 0,25 m | Sicherheitsabstand StVO | nav2_params.yaml (inflation_radius: 0,25) | IT-05 (nav_test) | Erfuellt |
| SIA-07 | PF1 | MUSS | Firmware begrenzt Geschwindigkeit auf Hardware-Ebene | Geschwindigkeitslimit | Hardware-Limit im ESP32-Fahrkern | Geschwindigkeitsbegrenzer | config_drive.h (motor_max: 255, deadzone: 35) | T-01 (motor_test) | Erfuellt |
| SIA-08 | ueberg. | MUSS | Motor-Shutdown bei Unterspannung schuetzt Batterie | Abschaltspannung | < 9,5 V → Motorenstopp | Unterspannungsschutz BMS | config_sensors.h (threshold_motor_shutdown_v: 9,5) | T-05 (sensor_test) | Erfuellt |
| SIA-09 | ueberg. | MUSS | System- und BMS-Shutdown bei kritischer Unterspannung | Abschaltspannungen | < 9,0 V → System-Shutdown, < 7,5 V → BMS-Trennung | Tiefentlade-/Trennschutz | config_sensors.h (threshold_system_shutdown_v: 9,0 / threshold_bms_disconnect_v: 7,5) | T-05 (sensor_test) | Erfuellt |
| SIA-10 | ueberg. | MUSS | Hauptsicherung begrenzt maximalen Strom | Sicherungswert | 10 A (Audit P-F05: nicht 15 A) | Kfz-Sicherung | config_sensors.h (fuse_rating_a: 10,0) | — | Erfuellt |

### 7.1 Sicherheitsanforderungen der Steuergeraetearchitektur (Erweiterung K1)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| SIA-11 | PF1 | MUSS | Der Fahrkern arbeitet in genau einem explizit gesetzten Betriebsmodus. In jedem Modus ist genau eine Fahrbefehlsquelle aktiv; bei deren Ausbleiben geht der Fahrkern in den sicheren Stillstand und wechselt die Quelle **nicht** selbsttaetig. Ein Quellenwechsel erfolgt ausschliesslich durch expliziten Moduswechsel. | Anzahl gleichzeitig aktiver Quellen, Zustand nach Timeout, Ausloeser eines Quellenwechsels | genau 1 aktive Quelle; Timeout der aktiven Quelle fuehrt zu v = 0 und omega = 0; kein selbsttaetiger Wechsel | Betriebsartensteuerung Steuergeraet | Ausbaupaket K5, Abschnitt 13 | IT-11 | Offen |
| SIA-12 | PF1 | MUSS | Der Fahrkern erkennt das Ausbleiben des Kantensignals ueber CAN und sperrt die Vorwaertsfahrt; die Ueberwachung wird erst nach dem ersten empfangenen Kantenframe scharf geschaltet | Erkennungszeit, Verhalten ohne CAN-Verkabelung | Erkennung <= 200 ms, ohne CAN-Bus unveraendertes Verhalten | Signal-Timeout-Ueberwachung | Ausbaupaket K5 | IT-11 | Offen |
| SIA-13 | PF1 | MUSS | Ein Notstopp ueber CAN stoppt beide Steuergeraete ohne Mitwirkung von micro-ROS oder der Anwendungsschicht des Pi 5 | Reaktionszeit | <= 50 ms | Redundanter Notabschaltkreis | Ausbaupaket K5 | IT-11 | Offen |
| SIA-14 | PF1 | MUSS | Der Batterie-Abschaltframe wird unabhaengig vom micro-ROS-Agenten gesendet | Sendefaehigkeit ohne verbundenen Agenten | Frame erscheint auf dem Bus | Fail-safe ohne Zentralrechner | Ausbaupaket K5 | IT-11 | Offen |
| SIA-15 | PF2 | MUSS | Auf dem Fahrbefehls-Topic des Fahrkerns publiziert ausschliesslich die Sicherheitslogik; Verhaltensentscheidung und Trajektorienplanung wirken nur ueber deren Eingaenge | Anzahl Publisher auf dem Fahrbefehls-Topic | genau 1 | Sicherheitsgerichtete Priorisierung | Ausbaupaket K9 | IT-13 | Offen (BA-03: 2 Publisher im Ausgangszustand) |
| SIA-16 | PF1 | SOLL | Der Modus SERIAL_REFERENCE bleibt ohne erneutes Flashen der Firmware erreichbar | Mittel des Moduswechsels | Startparameter, kein Neubau und kein Flashvorgang | Rueckfallbetrieb Werkstattmodus | Ausbaupaket K6, Abschnitt 13 | SV-04 | Offen |
| SIA-17 | PF1 | MUSS | Die Raddrehzahlregelung haelt einen ausgebliebenen Fahrzeug-Sollwert nur bis zum Ablauf des Failsafe-Timeouts und geht danach in den Stillstand | Haltezeit ohne neuen Sollwert | <= 500 ms bis v = 0 und omega = 0 | Sollwert-Timeout Antriebssteuergeraet | config_drive.h (failsafe_timeout_ms), Ausbaupaket K5 | T-01, IT-11 | Erfuellt (Bestand, in K5 erneut nachzuweisen) |

---

## 8 Rueckverfolgbarkeitsmatrix

### 8.1 Testfall-Verzeichnis

Das Verzeichnis fuehrt **definierte Testfall-IDs**. Eine ID bedeutet nicht, dass
das zugehoerige Pruefmittel bereits vorliegt:

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| implementiert | 20 | Skript vorhanden und als Entry-Point in `setup.py` eingetragen |
| spezifiziert | 13 | in Ausbaupaket K1 definiert; das Pruefmittel entsteht erst im jeweils genannten Ausbaupaket |
| **Summe definierter IDs** | **33** | |

Die folgende Tabelle ordnet jedem Testfall eine V-Modell-Pruefebene und eine Kfz-Testkategorie zu. Die Entry-Points der implementierten Testfaelle stammen aus setup.py (30 Eintraege: 13 Runtime-Knoten + 17 Validierungsskripte).

| Testfall-ID | Skript (setup.py Entry-Point) | V-Modell | Kfz-Testkategorie |
|---|---|---|---|
| T-01 | motor_test | R1 (Komponente) | Pruefstandtest |
| T-02 | encoder_test | R1 (Komponente) | Pruefstandtest |
| T-03 | pid_tuning | R1 (Komponente) | Pruefstandtest |
| T-04 | imu_test | R1 (Komponente) | Pruefstandtest |
| T-05 | sensor_test | R1 (Komponente) | Pruefstandtest |
| T-06 | rplidar_test | R1 (Komponente) | Pruefstandtest |
| T-07 | cliff_latency_test | R1 (Komponente) | Pruefstandtest |
| T-08 | serial_latency_logger | R1 (Komponente) | Pruefstandtest |
| IT-01 | kinematic_test | R2 (Integration) | Fahrversuch |
| IT-02 | rotation_test | R2 (Integration) | Fahrversuch |
| IT-03 | straight_drive_test | R2 (Integration) | Fahrversuch |
| IT-04 | slam_validation | R2 (Integration) | Fahrversuch |
| IT-05 | nav_test | R2 (Integration) | Fahrversuch |
| IT-06 | nav_square_test | R2 (Integration) | Fahrversuch |
| IT-07 | docking_test | R2 (Integration) | Fahrversuch |
| IT-08 | can_validation_test | R2 (Integration) | Fahrversuch |
| IT-09 | dashboard_latency_test | R2 (Integration) | Fahrversuch |
| SV-01 | nav_square_test + Full Stack | R3 (System) | Typgenehmigung |
| SV-02 | docking_test + host_hailo_runner | R3 (System) | Typgenehmigung |
| SV-03 | Gesamtsystem (alle Phasen) | R3 (System) | Typgenehmigung |

Die folgenden 13 Testfall-IDs sind in Ausbaupaket K1 **spezifiziert, aber noch
nicht implementiert**. Das jeweilige Pruefmittel entsteht erst im genannten
Ausbaupaket; die Spalte nennt den vorgesehenen Entry-Point. In K1 wird keine
Testimplementierung vorgezogen.

| Testfall-ID | Skript (vorgesehener Entry-Point) | V-Modell | Kfz-Testkategorie | Angelegt in |
|---|---|---|---|---|
| T-09 | can_dbc_check | R1 (Komponente) | Pruefstandtest | K2 |
| T-10 | can_bus_load_test | R1 (Komponente) | Pruefstandtest | K3 |
| T-11 | can_cmd_latency_test | R1 (Komponente) | Pruefstandtest | K4 |
| T-12 | radar_sim_test | R1 (Komponente) | Pruefstandtest | K7 |
| T-13 | radar_hardware_test | R1 (Komponente) | Pruefstandtest | K10 |
| IT-10 | can_shadow_test | R2 (Integration) | Fahrversuch | K3, K4 |
| IT-11 | can_mode_test | R2 (Integration) | Fahrversuch | K5 |
| IT-12 | environment_model_test | R2 (Integration) | Fahrversuch | K8 |
| IT-13 | behavior_test | R2 (Integration) | Fahrversuch | K9 |
| IT-14 | trajectory_test | R2 (Integration) | Fahrversuch | K9 |
| IT-15 | prediction_test | R2 (Integration) | Fahrversuch | K9 |
| SV-04 | Gesamtsystem im CAN-Betriebsmodus | R3 (System) | Typgenehmigung | K6 |
| SV-05 | Gesamtsystem mit vollstaendiger Funktionskette | R3 (System) | Typgenehmigung | K9, K10 |

Bereits vorhanden und in K0 rein passiv ausgefuehrt: `baseline_snapshot`
(Referenzaufnahme, kein Abnahmetest) und `can_validation_test` (IT-08).

### 8.2 Kreuztabelle Anforderung → Testfall → Projektfrage

| Anforderung | Testfall-IDs | PF | Kfz-Testkategorie | Messprotokoll |
|---|---|---|---|---|
| FA-01 | IT-04 | PF2 | Fahrversuch | P3 |
| FA-02 | IT-03 | PF2 | Fahrversuch | P1/P2 |
| FA-03 | IT-06 | PF2 | Fahrversuch | P4 |
| FA-04 | IT-05 | PF2 | Fahrversuch | P4 |
| FA-05 | IT-05 | PF2 | Fahrversuch | Kap. 6 (A-F02) |
| FA-06 | IT-03, T-01 | PF1 | Fahrversuch | P1/P2 |
| FA-07 | IT-02 | PF1 | Fahrversuch | P1/P2 |
| FA-08 | IT-09 | ueberg. | Fahrversuch | P5 |
| FA-09 | IT-04 | PF2 | Fahrversuch | — |
| FA-10 | IT-06, IT-07, SV-01 | PF2 | Typgenehmigung | P4 |
| FA-11 | IT-05 | PF2 | Fahrversuch | Kap. 6 (A-F02) |
| FA-12 | SV-03 | ueberg. | Typgenehmigung | P5 |
| FA-13 | IT-09 | ueberg. | Fahrversuch | P5 |
| FA-14 | SV-03 | ueberg. | Typgenehmigung | P5 |
| FA-15 | SV-02 | PF3 | Typgenehmigung | Kap. 6 |
| FA-16 | IT-07 | PF3 | Fahrversuch | P4 |
| FA-17 | SV-03 | PF3 | Typgenehmigung | P5 |
| NFA-01 | T-01, T-08 | PF1 | Pruefstandtest | P1/P2 |
| NFA-02 | T-06 | PF2 | Pruefstandtest | P3 |
| NFA-03 | T-02, T-08 | PF1 | Pruefstandtest | P3 |
| NFA-04 | T-04 | PF1 | Pruefstandtest | P2 |
| NFA-05 | IT-05 | PF2 | Fahrversuch | nav2_params.yaml |
| NFA-06 | IT-09 | ueberg. | Fahrversuch | Dashboard-Config |
| NFA-07 | IT-02 | PF2 | Fahrversuch | nav2_params.yaml |
| NFA-08 | — | ueberg. | — | Berechnung |
| NFA-09 | SV-03 | PF1 | Typgenehmigung | Kap. 6 |
| NFA-10 | T-08 | PF1 | Pruefstandtest | P1/P2 |
| NFA-11 | IT-04 | PF2 | Fahrversuch | P3 (A-F04) |
| NFA-12 | IT-05 | PF1 | Fahrversuch | Kap. 6 |
| SA-01 | T-08 | PF1 | Pruefstandtest | config_drive.h |
| SA-02 | T-08 | PF1 | Pruefstandtest | config_sensors.h |
| SA-03 | IT-08 | PF1 | Fahrversuch | config_drive.h |
| SA-04 | SV-03 | ueberg. | Typgenehmigung | full_stack.launch.py |
| SA-05 | IT-04 | ueberg. | Fahrversuch | full_stack.launch.py |
| SA-06 | T-05 | PF1 | Pruefstandtest | config_sensors.h |
| SA-07 | IT-09 | ueberg. | Fahrversuch | dashboard_bridge.py |
| SA-08 | SV-02 | PF3 | Typgenehmigung | host_hailo_runner.py |
| SA-09 | T-08 | PF1 | Pruefstandtest | micro-ROS-Config |
| SIA-01 | T-07 | PF1 | Pruefstandtest | P2 |
| SIA-02 | T-05 | PF1 | Pruefstandtest | cliff_safety_node.py |
| SIA-03 | IT-08 | PF1 | Fahrversuch | config_sensors.h |
| SIA-04 | T-01 | PF1 | Pruefstandtest | config_drive.h |
| SIA-05 | T-01 | PF1 | Pruefstandtest | config_drive.h |
| SIA-06 | IT-05 | PF2 | Fahrversuch | nav2_params.yaml |
| SIA-07 | T-01 | PF1 | Pruefstandtest | config_drive.h |
| SIA-08 | T-05 | ueberg. | Pruefstandtest | config_sensors.h |
| SIA-09 | T-05 | ueberg. | Pruefstandtest | config_sensors.h |
| SIA-10 | — | ueberg. | — | config_sensors.h |

Erweiterung K1 (Umsetzung in K2 bis K10, alle Nachweise stehen aus):

| Anforderung | Testfall-IDs | PF | Kfz-Testkategorie | Messprotokoll | Ausbaupaket |
|---|---|---|---|---|---|
| FA-18 | IT-12 | PF2 | Fahrversuch | P-AD1 | K8 |
| FA-19 | IT-12 | PF2 | Fahrversuch | P-AD1 | K8 |
| FA-20 | IT-15 | PF2 | Fahrversuch | P-AD2 | K9 |
| FA-21 | IT-13 | PF2 | Fahrversuch | P-AD2 | K9 |
| FA-22 | IT-14, SV-05 | PF2 | Typgenehmigung | P-AD2 | K9 |
| FA-23 | T-12, T-13 | PF3 | Pruefstandtest | P-AD1, P-AD3 | K7, K10 |
| NFA-13 | T-10 | PF1 | Pruefstandtest | P-CAN2 | K3, K6 |
| NFA-14 | T-11 | PF1 | Pruefstandtest | P-CAN3 | K4 |
| NFA-15 | T-10 | PF1 | Pruefstandtest | P-CAN2 | K3 |
| NFA-16 | IT-10 | PF1 | Fahrversuch | P-CAN2, P-CAN3 | K3, K4 |
| NFA-20 | IT-10 | PF1 | Fahrversuch | P-CAN2, P-CAN3 | K3, K4 |
| NFA-17 | IT-14 | PF2 | Fahrversuch | P-AD2 | K9 |
| NFA-18 | IT-11 | PF1 | Fahrversuch | P-CAN3 | K5 |
| NFA-19 | T-10 | PF1 | Pruefstandtest | P-CAN2 | K3 (Gate vor K4) |
| SA-10 | T-09 | PF1 | Pruefstandtest | P-CAN2 | K2 |
| SA-11 | T-11, IT-11 | PF1 | Fahrversuch | P-CAN3 | K4 |
| SA-12 | SV-04 | PF1 | Typgenehmigung | P-CAN3 | K6 |
| SA-13 | T-12 | PF3 | Pruefstandtest | P-AD1 | K7 |
| SA-17 | T-13 | PF3 | Pruefstandtest | P-AD3 | K10 |
| SA-18 | T-12, T-13 | PF1 | Pruefstandtest | P-AD1, P-AD3 | K7, K10 |
| SA-14 | IT-12 | PF2 | Fahrversuch | P-AD1 | K7, K8 |
| SA-15 | T-10 | PF1 | Pruefstandtest | P-CAN2 | K3 |
| SA-16 | SV-04 | PF1 | Typgenehmigung | P-CAN3 | K6 |
| SIA-11 | IT-11 | PF1 | Fahrversuch | P-CAN3 | K5 |
| SIA-12 | IT-11 | PF1 | Fahrversuch | P-CAN3 | K5 |
| SIA-13 | IT-11 | PF1 | Fahrversuch | P-CAN3 | K5 |
| SIA-14 | IT-11 | PF1 | Fahrversuch | P-CAN3 | K5 |
| SIA-15 | IT-13 | PF2 | Fahrversuch | P-AD2 | K9 |
| SIA-16 | SV-04 | PF1 | Typgenehmigung | P-CAN3 | K6 |
| SIA-17 | T-01, IT-11 | PF1 | Pruefstandtest | P1/P2, P-CAN3 | Bestand, K5 |

Neue Messprotokolle: P-CAN2 (K2 und K3), P-CAN3 (K4 bis K6), P-AD1 (K7 und
K8), P-AD2 (K9), P-AD3 (K10).

### 8.3 Abdeckung nach Projektfrage

| Projektfrage | Anforderungen | Anzahl | Schwerpunkt |
|---|---|---|---|
| PF1 (Echtzeitarchitektur) | FA-06, FA-07, NFA-01, NFA-03, NFA-04, NFA-09, NFA-10, NFA-12 bis NFA-16, NFA-18 bis NFA-20, SA-01 bis SA-03, SA-06, SA-09 bis SA-12, SA-15, SA-16, SA-18, SIA-01 bis SIA-05, SIA-07, SIA-11 bis SIA-14, SIA-16, SIA-17 | 38 | Regelfrequenz, Kommunikation, Steuergeraetearchitektur, Sicherheit |
| PF2 (Navigationsgenauigkeit) | FA-01 bis FA-05, FA-09 bis FA-11, FA-18 bis FA-22, NFA-02, NFA-05, NFA-07, NFA-11, NFA-17, SA-14, SIA-06, SIA-15 | 21 | SLAM, Navigation, Pfadverfolgung, Funktionskette |
| PF3 (Navigation und Bedien- und Leitstandsebene) | FA-15 bis FA-17, FA-23, SA-08, SA-13, SA-17 | 7 | Vision, Docking, Sprachschnittstelle, Radar |
| Uebergreifend | FA-08, FA-12 bis FA-14, NFA-06, NFA-08, SA-04, SA-05, SA-07, SIA-08 bis SIA-10 | 12 | Bedienung, Batterie, Infrastruktur |

Gesamtzahl: 78 Anforderungen (23 FA, 20 NFA, 18 SA, 17 SIA). Von der
Erweiterung K1 stammen 30 (FA-18 bis FA-23, NFA-13 bis NFA-20, SA-10 bis SA-18,
SIA-11 bis SIA-17); davon ist eine im Bestand bereits erfuellt (SIA-17), 29 sind
offen.

---

## 9 Offene Punkte

### OP-01: Navigationsmesswerte ohne separates Messprotokoll (Audit A-F02)

Die Messwerte Positionsabweichung 6,4 cm und Winkelabweichung 4,2 Grad aus Kapitel 6 stammen aus einer Gesamtfahrt, nicht aus einem eigenstaendigen Messprotokoll. Ebenso fehlen separate Protokolle fuer Passierabstand (12 cm) und Recovery-Erfolgsquote (80 %). **Kfz-Analogie:** Eine Bremswegmessung fehlt im TUeV-Bericht — die Typgenehmigung erfordert einen eigenstaendigen Nachweis pro Pruefkriterium. **Massnahme:** Separates Messprotokoll (messprotokoll_phase3_nav.md) mit 10+ Einzelmessungen erstellen.

### OP-02: ATE-Kenngroesse mehrdeutig (Audit A-F04)

Kapitel 6 nennt ATE 0,16 m als mittleren Fehler (Mean Absolute Error) der ersten Fahrt und ATE 0,03 m als RMSE der zweiten Fahrt. Beide Groessen sind mathematisch verschieden und duerfen nicht verglichen werden. **Kfz-Analogie:** Kraftstoffverbrauchsangabe nach NEFZ vs. WLTP — der angewandte Pruefzyklus bestimmt den Referenzwert. **Massnahme:** Einheitlich RMSE als Leitgroesse fuer NFA-11 festlegen und beide Fahrten mit derselben Metrik auswerten.

### OP-03: Costmap-Aufloesung als Tradeoff (Architekturentscheidung)

Die SLAM- und Costmap-Aufloesung betraegt 0,05 m (config: mapper_params, nav2_params). Feinere Aufloesung erhoeht den RAM-Bedarf auf dem Pi 5, groebere Aufloesung verringert die Navigationsgenauigkeit. **Kfz-Analogie:** Die Rasterweite einer HD-Karte bestimmt den Speicherbedarf des Navigationsgeraets — hohe Aufloesung verbraucht mehr Onboard-Speicher. **Massnahme:** RAM-Verbrauch bei 0,05 m und 0,03 m Aufloesung messen und dokumentieren.

### OP-04: Fehlende Einzelprotokolle fuer Systemkenngroessen

Folgende Ist-Werte stammen aus Kapitel 6, besitzen jedoch kein eigenes Messprotokoll: CPU-Last (< 80 %), RPP-Controller-Rate (> 2000 Hz), Hailo-Inferenzzeit (34 ms), Docker-Anteil (~35 %). **Kfz-Analogie:** Die Einzelabnahme (Motorleistung, Bremskraft, Abgaswerte) fehlt im Pruefbericht — nur die Gesamtfahrt wurde dokumentiert. **Massnahme:** Kenngroessen in vorhandene Messprotokolle als Anhang aufnehmen oder separates Systemprotokoll erstellen.

### OP-05: Phase-5-Ergebnisse nicht in Kapitel 6 dokumentiert

Die fuenf Phase-5-Testfaelle (cmd_vel-Latenz, Telemetrie-Vollstaendigkeit, Deadman-Timer, Audio-Feedback, Notaus) wurden erfolgreich durchgefuehrt (Messprotokoll P5: 5/5 PASS), erscheinen jedoch nicht im Ergebniskapitel der Projektarbeit. **Kfz-Analogie:** Die HMI-Abnahme (Kombiinstrument, Warnleuchten, Sprachsteuerung) wurde durchgefuehrt, aber nicht im Pruefbericht erwaehnt. **Massnahme:** Phase-5-Ergebnisse in Kapitel 6 aufnehmen.

### OP-06: Sprachschnittstelle konsolidiert (1 Knoten statt geplante 5)

Die urspruenglich geplanten fuenf Einzelknoten (ReSpeaker DoA, VAD, STT, Intent-Parser, Missionslogik) wurden in einem konsolidierten voice_command_node zusammengefuehrt. Die funktionale Anforderung F07 (KANN) bleibt erfuellt, die Definition-of-Done der Roadmap muss angepasst werden. **Kfz-Analogie:** Konsolidierung von fuenf Steuergeraeten (Lenkung, ESP, ABS, ASR, Bremse) zu einem Zentralrechner — die Funktion bleibt identisch, die Komponentenstruktur aendert sich. **Massnahme:** Roadmap-DoD fuer Meilenstein M-08 aktualisieren.

### OP-07: Batterie-Laufzeit unbelegt (NFA-08)

Der Schwellwert >= 30 min unter Last basiert auf einer Berechnung (Samsung INR18650-35E, 3,35 Ah, 3S1P), nicht auf einer Messung unter realistischer Last (SLAM + Navigation + Dashboard + Vision). **Kfz-Analogie:** Die Reichweitenangabe erfolgt ohne WLTP-Messzyklus — nur die theoretische Berechnung aus Kapazitaet und Durchschnittsverbrauch liegt vor. **Massnahme:** Laufzeitmessung unter definierter Last (Full-Stack-Betrieb) durchfuehren und dokumentieren.

### OP-08: Dual-Path-Priorisierung dokumentiert, aber nicht implementiert

`planung/messprotokoll_can.md` und `README.md` beschreiben eine Priorisierung
micro-ROS vor CAN vor Firmware-Stopp. Diese Arbitrierung existiert im
Ausgangszustand nicht: Es gibt keine CAN-Nachricht fuer den Fahrbefehl, keinen
Empfangspfad im Fahrkern und keine Pfadumschaltung. **Kfz-Analogie:** Ein
Pruefbericht beschreibt einen redundanten Bremskreis, der im Fahrzeug nicht
verbaut ist. **Massnahme:** SIA-11 setzt die Arbitrierung in K5 um; danach sind
Dokument und Code deckungsgleich zu bringen.

### OP-09: Radar bis zur Beschaffung nur simuliert nachweisbar

SA-13 und FA-23 lassen sich bis zur Beschaffung des BGT60TR13C ausschliesslich
im Simulationsmodus nachweisen. **Kfz-Analogie:** Ein Sensorsteuergeraet wird
am Restbussimulator geprueft, bevor die Sensorhardware vorliegt.
**Massnahme:** Status bleibt bis K10 offen; T-12 weist den Simulationsmodus
nach, T-13 die Hardware.

### OP-10: CAN-Datenintegritaet offen (Blocker vor K4)

Die Baseline-Aufnahme K0 hat zwei Abweichungen ergeben: BA-01 (Frameverlust
4,58 % auf der Odometrie-Positionsnachricht, uebrige Nachrichten verlustfrei)
und BA-02 (Zaehler fuer Empfangsfehler steigt um 10,0 pro Sekunde, waehrend
saemtliche CAN-Protokollzaehler auf null bleiben). Die Ursachen sind nicht
ermittelt; genannte Erklaerungsansaetze sind ausdruecklich ungeprueft.
**Kfz-Analogie:** Sporadische Uebertragungsfehler auf dem Antriebs-CAN werden
vor der Freigabe des Steuergeraets geklaert, nicht danach. **Massnahme:**
Untersuchung in K3, Nachweis ueber NFA-19 und T-10. Das Freigabe-Gate vor K4
ist in `planung/baseline_k0_referenzwerte.md` Abschnitt 11.2 festgelegt.

### OP-11: Kantensignal waehrend der Baseline-Aufnahme dauerhaft aktiv

Waehrend beider K0-Messlaeufe meldete das Kantensignal durchgehend eine
erkannte Kante (BA-04). Die Sicherheitslogik sendete daraufhin ueber ihren
Sicherheitstimer dauerhaft Nullvektoren; es wurde kein Fahrbefehl erzeugt und
keine Bewegung ausgeloest. Die Ursache ist nicht ermittelt; Aufstellung,
Untergrund, Montage, Sensorik und Auswerteschwelle kommen infrage. Eine
Sensorursache wird ausdruecklich nicht angenommen. **Kfz-Analogie:** Eine
dauerhaft anliegende Warnmeldung wird vor der naechsten Messfahrt geklaert,
nicht wegkonfiguriert. **Massnahme:** Vor der naechsten Vergleichsmessung den
physischen Aufbau protokollieren und den Kantensensor bei definiertem
Untergrund gegen den Bestandswert aus Phase 2 pruefen (dort 0 Fehlalarme in 60
Messwerten).

### OP-12: Schwellwertdivergenz zwischen DoD-Checkliste und Anforderungsliste

`planung/DoD-checkliste-phasen.md` fordert fuer Phase 4 einen Zielradius von
10 cm und einen Gierfehler unter 0,15 rad, waehrend FA-03 hoechstens 0,03 m
und 0,05 rad fordert. Fuer Phase 5 fordert die DoD-Checkliste eine Latenz
unter 100 ms, FA-13 unter 300 ms. **Kfz-Analogie:** Pruefvorschrift und
Lastenheft nennen unterschiedliche Grenzwerte fuer dieselbe Groesse.
**Massnahme:** Bestandsbefund, nicht Teil des Ausbaus. Vor einer
Wiederholungsmessung der Phasen 4 und 5 ist der jeweils bindende Wert
festzulegen.

---

## 10 Abgrenzung von Anforderung, Baseline und Messergebnis

### 10.1 Grundsatz

Fuer jede quantitative Groesse werden vier Angaben strikt getrennt gefuehrt:

| Spalte | Bedeutung | Wer legt sie fest |
|---|---|---|
| **Anforderung** | Verbindliche Mindestanforderung. Aendert sich nur durch eine dokumentierte Anforderungsaenderung nach Abschnitt 11. | Anforderungsliste L1 |
| **K0-Baseline** | Gemessener Istwert des Ausgangszustands vor dem Ausbau. Beschreibt, nicht fordert. | `planung/baseline_k0_referenzwerte.md` |
| **Spaeteres Messergebnis** | Istwert einer spaeteren Messung, je Ausbaupaket im zugehoerigen Messprotokoll. | Messprotokolle |
| **Regressionstoleranz** | Zulaessige Verschlechterung gegenueber der K0-Baseline, unabhaengig von der Anforderung. | Anforderungsliste L1 |

**Eine Baseline-Messung ersetzt keine Anforderung.** Liegt ein Istwert unter
einer Anforderung, ist das ein Befund, keine Anforderungsaenderung. Liegt ein
Istwert deutlich ueber einer Anforderung, senkt das die Anforderung nicht, und
der hohe Istwert wird nicht stillschweigend zum neuen Sollwert.

Eine Anforderung darf nur aus fachlichen Gruenden geaendert werden, niemals
allein deshalb, weil eine Messung einen abweichenden Wert ergeben hat. Jede
Aenderung ist in Abschnitt 11 mit Begruendung nachzuweisen.

### 10.2 Matrix der laufend gemessenen Groessen

| Groesse | Anforderung | K0-Baseline (02.09.2026) | Spaeteres Messergebnis | Regressionstoleranz |
|---|---|---|---|---|
| Odometrie-Rate `/odom` | NFA-03: >= 10 Hz | 19,85 Hz | je Paket im Messprotokoll | >= 15 Hz und nicht mehr als 25 % unter der Baseline |
| IMU-Rate `/imu` | NFA-04: >= 20 Hz | 38,07 Hz | je Paket im Messprotokoll | >= 20 Hz und nicht mehr als 25 % unter der Baseline |
| LiDAR-Scanrate `/scan` | NFA-02: >= 5 Hz | 7,51 Hz | je Paket im Messprotokoll | >= 5 Hz |
| Kantensignal-Rate `/cliff` | keine eigene Anforderung; Firmware-Sollwert 20 Hz (`config_sensors.h`) | 15,86 Hz, aufgenommen unter dem ungeklaerten Zustand BA-04 | je Paket im Messprotokoll | **kein Abnahmekriterium ableitbar, solange OP-11 offen ist** |
| Ultraschall-Rate `/range/front` | DoD Phase 2: >= 7,0 Hz | 9,06 Hz | je Paket im Messprotokoll | >= 7,0 Hz |
| Batterie-Rate `/battery` | keine eigene Anforderung; Firmware-Sollwert 2 Hz | 2,00 Hz | je Paket im Messprotokoll | >= 1,5 Hz |
| Fahrbefehls-Rate auf dem Fahrkern-Topic | keine eigene Anforderung | 20,0 Hz, ausschliesslich Nullvektoren infolge BA-04 | je Paket im Messprotokoll | **kein Regressionsmassstab, solange OP-11 offen ist** |
| CAN-Buslast | NFA-13: <= 30 % | 193,1 Frames/s (rechnerisch rund 2,5 %) | T-10 je Paket | <= 30 % |
| CAN-Frameverlust je ID | NFA-19: <= 1 % je ID | 0,00 % auf zehn IDs, 4,58 % auf der Odometrie-Positionsnachricht | T-10 je Paket | <= 1 % je ID; die Baseline verletzt die Anforderung bereits (BA-01, OP-10) |
| CAN-Fehlerzustand | keine eigene Anforderung; Betriebszustand ERROR-ACTIVE | ERROR-ACTIVE, alle Protokollzaehler 0 | T-10 je Paket | ERROR-ACTIVE, Protokollzaehler bleiben 0 |
| Cliff-Latenz Ende-zu-Ende | SIA-01: < 50 ms | 2,0 ms (Phase 2, nicht in K0 wiederholt) | je Paket im Messprotokoll | < 50 ms und nicht mehr als Faktor 2 ueber dem Phase-2-Wert |
| Publisher auf dem Fahrkern-Topic | SIA-15: genau 1 | 2 (BA-03) | IT-13 in K9 | Anforderung im Ausgangszustand nicht erfuellt; Nachweis in K9 |

### 10.3 Anmerkungen zu einzelnen Zeilen

**IMU-Rate.** Die Baseline liegt mit 38,07 Hz deutlich ueber der Anforderung
NFA-04 von 20 Hz und ueber dem in Phase 2 gemessenen Bereich von 30,4 bis
35,2 Hz. Der hoehere Wert wird als Referenz gefuehrt und **nicht** zur
Anforderung erhoben. Massgeblich fuer die Abnahme bleibt NFA-04.

**Kantensignal-Rate.** Der Wert von 15,86 Hz wurde unter dem ungeklaerten
Zustand BA-04 aufgenommen. Aus ihm wird kein Abnahmekriterium abgeleitet.
Sobald OP-11 geklaert ist, ist die Messung unter definiertem Untergrund zu
wiederholen.

**Verworfene Schaetzwerte.** Im Planungsentwurf zu Ausbaupaket K6 waren
Zielwerte von 45 Hz fuer die IMU-Rate und 18 Hz fuer die Kantensignal-Rate
genannt. Diese Werte waren Schaetzungen ohne Anforderungsstatus, lagen ueber
den spaeter gemessenen Istwerten und werden hiermit verworfen. Fuer die
Abnahme von K6 gelten NFA-02, NFA-03 und NFA-04 sowie die Regressionstoleranzen
dieser Matrix.

---

## 11 Aenderungsverfolgung der Anforderungen

### 11.1 Verfahren

Eine bestehende Anforderung wird nur geaendert, wenn ein fachlicher Grund
vorliegt: eine geaenderte Systemgrenze, eine geaenderte Nutzungsanforderung,
eine widerlegte Annahme oder ein Sicherheitsbefund. Eine abweichende Messung
ist fuer sich genommen **kein** Aenderungsgrund.

Jede Aenderung wird in der Tabelle in Abschnitt 11.2 mit alter Fassung, neuer
Fassung, Begruendung, Datum und ausloesendem Ausbaupaket eingetragen. Die
Versionsnummer im Kopfbereich wird erhoeht.

### 11.2 Aenderungen

| Nr. | Anforderung | Alte Fassung | Neue Fassung | Begruendung | Datum | Paket |
|---|---|---|---|---|---|---|
| — | — | — | — | In der Erweiterung K1 wurde keine bestehende Anforderung geaendert. Es wurden ausschliesslich neue Anforderungen aufgenommen. | 2026-09-02 | K1 |

### 11.3 Aufnahmen in der Erweiterung K1

| Bereich | Neue IDs | Anzahl | Gegenstand |
|---|---|---|---|
| Funktional | FA-18 bis FA-23 | 6 | Funktionskette automatisiertes Fahren, Radarfusion |
| Nicht-funktional | NFA-13 bis NFA-20 | 8 | Buslast, Latenz, Jitter, Transportgleichheit, Kettenlatenz, Stillstandszeit, Frameverlust, Zeitversatz |
| Schnittstellen | SA-10 bis SA-18 | 9 | Signaldatenbank, CAN-Kommandopfad, Gateway, Radar-Abstraktion, Umfeldmodell, Busdiagnose, Servicepfad, reale Radaranbindung, Rohdatentrennung |
| Sicherheit | SIA-11 bis SIA-17 | 7 | Betriebsmodi, Zeitueberwachung, Notstopp, Abschaltframe, Publisher-Hoheit, Rueckfallbetrieb, Sollwert-Timeout |

Von diesen 30 Aufnahmen ist SIA-17 im Ausgangszustand bereits erfuellt
(Failsafe-Timeout der Firmware) und wird in K5 erneut nachgewiesen. Die
uebrigen 29 sind offen.

Zwei Aufnahmen halten Befunde der K0-Baseline als Anforderung fest:

- **NFA-19** (Frameverlust je Signal <= 1 Prozent) macht BA-01 pruefbar und ist
  Bestandteil des Freigabe-Gates vor K4.
- **SIA-15** (genau ein Publisher auf dem Fahrbefehls-Topic) macht BA-03
  pruefbar und ist dem Ausbaupaket K9 zugeordnet.

---

## 12 Transportgleichheit: Signalklassen und abgeleitete Schwellen

Grundlage von NFA-16 und NFA-20. Die Schwellen sind **nicht** geschaetzt, sondern
aus dem tatsaechlich implementierten Encoding abgeleitet
(`mcu_firmware/*/include/twai_can.hpp`, Stand v4.0.0 und v3.0.0).

### 12.1 Klasse A: unveraendert uebertragene Gleitkommazahl

Die Firmware haelt den Messwert als `float` und uebertraegt ihn per `memcpy`
unveraendert als 4 Byte. Derselbe `float` wird ueber den Referenzpfad in einem
`double`-Feld publiziert; die Erweiterung von `float` nach `double` ist exakt
und verlustfrei.

| Signal | CAN-Uebertragung | Referenzpfad | Zulaessige Abweichung |
|---|---|---|---|
| Abstand voraus | float32 | `sensor_msgs/Range.range` (float32) | 0 |
| Gierwinkel aus Komplementaerfilter | float32 | Orientierung in `sensor_msgs/Imu` | 0 |
| Odometrie x und y | float32 | `nav_msgs/Odometry.pose.position` (float64) | 0 |
| Odometrie Gierwinkel und Laengsgeschwindigkeit | float32 | `Odometry.twist.linear.x` (float64) | 0 |
| Raddrehzahl links und rechts | float32 | keine Entsprechung im Referenzpfad | entfaellt |

**Schwelle: exakte Wertgleichheit (Abweichung 0).** Eine von null verschiedene
Abweichung bedeutet, dass die verglichenen Werte aus verschiedenen Quellzyklen
stammen oder dass ein Uebertragungsfehler vorliegt; beides ist ein Befund.

### 12.2 Klasse B: quantisierte Ganzzahl

Die Firmware skaliert den `float` und schneidet auf eine Ganzzahl ab
(Trunkierung, keine Rundung). Die Abweichung liegt damit im Bereich von 0 bis
knapp unter einer Quantisierungsstufe, stets in Richtung Null.

| Signal | Skalierung im Code | Eine Quantisierungsstufe | Zulaessige Abweichung |
|---|---|---|---|
| Beschleunigung x, y, z | `(int16_t)(a * 1000.0f)` | 0,001 m/s^2 | <= 1 Stufe |
| Gierrate | `(int16_t)(gz * 100.0f)` | 0,01 rad/s | <= 1 Stufe |
| Batteriespannung | `(uint16_t)(voltage * 1000.0f)` | 0,001 V | <= 1 Stufe |
| Batteriestrom | `(int16_t)(current * 1000.0f)` | 0,001 A | <= 1 Stufe |
| Batterieleistung | `(uint16_t)(power * 1000.0f)` | 0,001 W | <= 1 Stufe, Saettigung ab 65,535 W beachten |
| Stellgroesse links und rechts | `int16_t` ohne Skalierung | 1 PWM-Schritt | <= 1 Stufe |

**Schwelle: hoechstens eine Quantisierungsstufe.** Groessere Abweichungen sind
nicht durch das Encoding erklaerbar.

### 12.3 Klasse C: Zustandssignal

| Signal | Uebertragung | Zulaessige Abweichung |
|---|---|---|
| Kantenerkennung | 1 Byte, 0x00 oder 0x01 | keine; Wertgleichheit gefordert |
| Batterie-Abschaltanforderung | 1 Byte, 0x00 oder 0x01 | keine; Wertgleichheit gefordert |

### 12.4 Zeitversatz (NFA-20)

Die beiden Pfade senden dasselbe Signal zu unterschiedlichen Zeitpunkten: Die
CAN-Uebertragung erfolgt aus den Echtzeit-Aufgaben auf Kern 1, die
Referenzuebertragung aus der Kommunikationsschleife auf Kern 0. Ein Vergleich
ohne Zeitzuordnung misst daher den Zeitversatz und nicht das Encoding.

Der Nachweis ordnet je Signal die zeitlich naechstgelegenen Wertepaare einander
zu und weist den verbleibenden Zeitversatz getrennt aus.

**Herleitung der Schwellen.** Massgeblich ist die langsamste in den Vergleich
einbezogene Nachricht: der Abstand voraus mit 10 Hz, also einer Nominalperiode
von **100 ms**. Beide Pfade senden unabhaengig voneinander mit dieser Periode.
Wird jedem Wert des einen Pfades der zeitlich naechstgelegene Wert des anderen
Pfades zugeordnet, betraegt der Zeitversatz hoechstens eine **halbe** Periode,
also 50 ms; ein groesserer Versatz bedeutet, dass ein naeher liegender Wert
existiert und stattdessen haette zugeordnet werden muessen.

| Kenngroesse | Wert | Herleitung |
|---|---|---|
| Nominalperiode der langsamsten verglichenen Nachricht | 100 ms | 10 Hz |
| Maximaler Versatz bei Zuordnung zum naechstgelegenen Wert | 50 ms | halbe Nominalperiode |
| Erwartungswert bei gleichverteiltem Versatz zwischen 0 und 50 ms | 25 ms | Mittel der Gleichverteilung; daraus die Medianschwelle |
| Schwelle fuer das 95-Prozent-Quantil | 60 ms | 50 ms zuzueglich 20 Prozent Reserve fuer Sendejitter beider Pfade |

Die Medianschwelle von 25 ms prueft damit, ob sich der Versatz wie erwartet
gleichverteilt verhaelt. Die Quantilschwelle von 60 ms laesst Raum fuer den
Jitter, den NFA-15 mit hoechstens 20 Prozent der Nominalperiode zulaesst,
schliesst aber eine systematische Verschiebung um eine ganze Periode aus.

**Wichtig:** NFA-16 gilt nur fuer Wertepaare, deren Zeitversatz die Schwelle von
NFA-20 einhaelt. Wertepaare mit groesserem Versatz werden aus der
Encoding-Bewertung ausgeschlossen und gesondert gezaehlt.

---

## 13 Betriebsmodi des Fahrbefehlspfads

Grundlage von SIA-11 und SIA-16. Der Fahrkern kennt fuenf Betriebsmodi. Zu
jedem Zeitpunkt ist genau einer aktiv, und in jedem Modus ist genau eine
Fahrbefehlsquelle wirksam.

**Es gibt keine selbsttaetige Umschaltung zwischen Quellen.** Bleibt die aktive
Quelle aus, geht der Fahrkern in den sicheren Stillstand. Er sucht sich keine
Ersatzquelle. Ein Quellenwechsel ist ausschliesslich ein expliziter
Moduswechsel, den der Pi 5 anfordert.

### 13.1 Die fuenf Modi

| Modus | Aktive Fahrbefehlsquelle | CAN-Fahrbefehl | Verwendung |
|---|---|---|---|
| `SERIAL_REFERENCE` | Referenzpfad ueber micro-ROS und USB | wird ignoriert | Ausgangszustand und Rueckfallbetrieb; entspricht dem heutigen Verhalten |
| `CAN_SHADOW` | Referenzpfad ueber micro-ROS und USB | wird empfangen, protokolliert und **nicht** auf den Stellpfad gegeben | Nachweis von Uebertragung, Latenz und Transportgleichheit ohne Wirkung (K4) |
| `CAN_PRIMARY` | CAN-Fahrbefehl | wirksam | Regelbetrieb nach der Umstellung (K6) |
| `SERVICE` | keine | wird ignoriert | Flashen, Diagnose, Pruefstand; Antrieb bleibt gesperrt |
| `FAILSAFE` | keine | wird ignoriert | Zustand nach Timeout, Notstopp, Kanten- oder Batterieereignis |

### 13.2 Zulaessige Uebergaenge

```text
SERIAL_REFERENCE  <-->  CAN_SHADOW  <-->  CAN_PRIMARY
        |                   |                  |
        +-------------------+------------------+
                            |
                    (Ereignis, nicht anforderbar)
                            v
                        FAILSAFE
                            |
                 (expliziter Moduswechsel
                  nach Wegfall der Ursache)
                            v
                  SERIAL_REFERENCE / CAN_SHADOW / CAN_PRIMARY

SERVICE  <-->  SERIAL_REFERENCE       (nur im Stillstand)
```

* Wechsel zwischen `SERIAL_REFERENCE`, `CAN_SHADOW` und `CAN_PRIMARY` erfolgen
  ausschliesslich auf ausdrueckliche Anforderung des Pi 5.
* `FAILSAFE` wird **nicht** angefordert, sondern durch ein Ereignis erreicht:
  Timeout der aktiven Quelle, Notstopp, Kantensignal oder Batterieabschaltung.
* Das Verlassen von `FAILSAFE` erfordert einen expliziten Moduswechsel, nachdem
  die Ursache entfallen ist. Ein selbsttaetiges Fortsetzen der Fahrt findet
  nicht statt.
* `SERVICE` ist nur im Stillstand erreichbar und sperrt den Antrieb.

### 13.3 Zeitueberwachung je Modus

| Modus | Ueberwachte Quelle | Timeout | Reaktion |
|---|---|---|---|
| `SERIAL_REFERENCE` | Fahrbefehl ueber micro-ROS | 500 ms (`failsafe_timeout_ms`) | `FAILSAFE`, v = 0 und omega = 0 |
| `CAN_SHADOW` | Fahrbefehl ueber micro-ROS | 500 ms | `FAILSAFE`; der CAN-Fahrbefehl bleibt auch dann wirkungslos |
| `CAN_PRIMARY` | Fahrbefehl ueber CAN | 300 ms | `FAILSAFE`, v = 0 und omega = 0 |
| alle Modi | Kantensignal ueber CAN, sofern scharf geschaltet | 200 ms | Sperrung der Vorwaertsfahrt (SIA-12) |

Der Zeitrahmen von 300 ms im Modus `CAN_PRIMARY` ergibt sich aus der
Sendefrequenz des Fahrbefehls von 50 Hz: 15 ausbleibende Nachrichten in Folge
gelten als Ausfall der Quelle.

Voraussetzung dafuer ist, dass das Gateway **zyklisch** sendet und nicht nur
bei Aenderung: Es haelt den zuletzt gueltigen Fahrbefehl und uebertraegt ihn
mit 50 Hz weiter, auch wenn das ROS-2-Eingangstopic langsamer, unregelmaessig
oder gar nicht publiziert (SA-11). Ein ausbleibender Frame ist damit ein
belastbares Ausfallkriterium und nicht nur ein Hinweis darauf, dass sich der
Sollwert nicht geaendert hat. Der Wert liegt unterhalb des bestehenden
Failsafe-Timeouts von 500 ms, damit der schnellere Pfad auch schneller
abgesichert ist.

### 13.4 Abgrenzung zum urspruenglichen Entwurf

Ein frueherer Entwurf sah eine selbsttaetige Arbitrierung vor: Bei Ausbleiben
des Referenzpfads sollte der Fahrkern eigenstaendig auf den CAN-Pfad wechseln.
Dieser Ansatz wird **nicht** weiterverfolgt. Begruendung:

1. Eine selbsttaetige Umschaltung macht den wirksamen Fahrbefehlspfad vom
   Zeitverhalten zweier Busse abhaengig und damit im Fehlerfall schwer
   vorhersagbar.
2. Der Zustand nach einer Umschaltung waere von aussen nicht eindeutig
   bestimmbar, was die Nachweisfuehrung erschwert.
3. Ein sicherer Stillstand ist die belastbarere Reaktion auf den Ausfall der
   aktiven Quelle als der Wechsel auf einen Pfad, dessen Zustand im selben
   Moment unbekannt ist.

Der Rueckfallbetrieb bleibt vollstaendig erhalten, ist aber ein bewusster
Moduswechsel und kein Automatismus (SIA-16).

---

## Anhang: Zusammenfassung der Firmware-Referenzwerte

Die folgenden kanonischen Parameter stammen aus den Firmware-Konfigurationsdateien und bilden die Grundlage fuer die quantitativen Schwellwerte dieser Anforderungsliste.

### A.1 Fahrkern (config_drive.h v4.0.0)

| Parameter | Wert | Einheit | Kfz-Pendant |
|---|---|---|---|
| wheel_diameter | 65,67 | mm (kalibriert) | Reifenumfang |
| wheel_base | 178,0 | mm (kalibriert) | Radstand |
| ticks_per_rev_left | 748,6 | Ticks/U | Inkrementalgeber-Aufloesung |
| ticks_per_rev_right | 747,2 | Ticks/U | Inkrementalgeber-Aufloesung |
| control_loop_hz | 50 | Hz | ECU-Regelfrequenz |
| odom_publish_hz | 20 | Hz | CAN-Zykluszeit Radsensor |
| kp / ki / kd | 0,4 / 0,1 / 0,0 | PID-Koeffizienten | Motorsteller-Regelung |
| ema_alpha | 0,3 | Filterkoeffizient | Signalglaettung |
| max_accel_rad_s2 | 5,0 | rad/s^2 | Beschleunigungsbegrenzung |
| deadzone | 35 | PWM (0–255) | Totbereich Stellglied |
| motor_freq_hz | 20000 | Hz | PWM-Frequenz Inverter |
| failsafe_timeout_ms | 500 | ms | Watchdog-Timeout ECU |
| watchdog_miss_limit | 50 | Zyklen | Alive-Counter CAN |

### A.2 Sensor- und Sicherheitsbasis (config_sensors.h v3.0.0)

| Parameter | Wert | Einheit | Kfz-Pendant |
|---|---|---|---|
| imu_sample_hz | 50 (eff. 30–35) | Hz | Abtastrate Beschleunigungssensor |
| cliff_publish_hz | 20 | Hz | Zykluszeit Kantenerkennung |
| us_publish_hz | 10 | Hz | PDC-Abtastrate |
| battery_publish_hz | 2 | Hz | BMS-Telemetrie |
| complementary_alpha | 0,98 | Gyro-Gewicht | Sensorfusionsfilter |
| threshold_motor_shutdown_v | 9,5 | V | Unterspannungs-Abschaltung |
| threshold_system_shutdown_v | 9,0 | V | System-Notabschaltung |
| threshold_bms_disconnect_v | 7,5 | V | BMS-Trennschuetz |
| pack_charge_max_v | 12,60 | V | Ladeschlussspannung |
| fuse_rating_a | 10,0 | A | Kfz-Hauptsicherung |

---

*Erstellt nach VDI 2206, Stufe L1 (Lastenheft). Alle Schwellwerte gegen config_drive.h v4.0.0, config_sensors.h v3.0.0, nav2_params.yaml und Messprotokolle Phase 1–5 verifiziert. Kfz-Analogien dienen der didaktischen Einordnung und ersetzen keine formale ASIL-Einstufung nach ISO 26262.*
