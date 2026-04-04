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
| Version             | 1.0                                                                 |
| Datum               | 2026-03-22                                                          |
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

---

## 8 Rueckverfolgbarkeitsmatrix

### 8.1 Testfall-Verzeichnis

Die folgende Tabelle ordnet jedem Testfall eine V-Modell-Pruefebene und eine Kfz-Testkategorie zu. Die Entry-Points stammen aus setup.py (30 Eintraege: 12 Runtime-Knoten + 18 Validierungsskripte).

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

### 8.3 Abdeckung nach Projektfrage

| Projektfrage | Anforderungen | Anzahl | Schwerpunkt |
|---|---|---|---|
| PF1 (Echtzeitarchitektur) | FA-06, FA-07, NFA-01, NFA-03, NFA-04, NFA-09, NFA-10, NFA-12, SA-01, SA-02, SA-03, SA-06, SA-09, SIA-01–SIA-05, SIA-07 | 19 | Regelfrequenz, Kommunikation, Sicherheit |
| PF2 (Navigationsgenauigkeit) | FA-01–FA-05, FA-09–FA-11, NFA-02, NFA-05, NFA-07, NFA-11, SIA-06 | 13 | SLAM, Navigation, Pfadverfolgung |
| PF3 (Navigation und Bedien- und Leitstandsebene) | FA-15, FA-16, FA-17, SA-08 | 4 | Vision, Docking, Sprachschnittstelle |
| Uebergreifend | FA-08, FA-12–FA-14, NFA-06, NFA-08, SA-04, SA-05, SA-07, SIA-08–SIA-10 | 11 | Bedienung, Batterie, Infrastruktur |

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
