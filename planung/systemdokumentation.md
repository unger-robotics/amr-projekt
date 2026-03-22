# Systemdokumentation: Autonomer mobiler Roboter (AMR)

## 1. Systemuebersicht und Architektur

Wie laesst sich eine deterministische Echtzeitregelung fuer den Antrieb eines autonomen mobilen Roboters (AMR) synchron mit rechenintensiver SLAM-Navigation betreiben?

Der Systementwurf loest diese Anforderung durch ein zweistufiges Echtzeitsystem. Die Architektur trennt die hardwarenahe Steuerung auf zwei Seeed Studio XIAO ESP32-S3 strikt von der Navigations- und Missionslogik auf einem Raspberry Pi 5.

Die Steuerung gliedert sich in drei Ebenen:

* **Ebene A (Fahrkern):** Der Fahrkern umfasst die gesamte Antriebsregelung, Sensorerfassung, Lokalisierung und Navigation. Der Drive-Knoten (ESP32-S3) regelt die Gleichstrommotoren mit PID-Reglern bei 50 Hz und publiziert die Odometrie. Der Sensor-Knoten (ESP32-S3) verarbeitet IMU, Kanten-Sensor, Ultraschall und Batterieueberwachung. Der RPLIDAR A1 ist direkt am Raspberry Pi 5 angeschlossen (/dev/ttyUSB0) und wird vom RPLIDAR-Knoten im ROS2-Container betrieben. Auf dem Raspberry Pi 5 laufen SLAM Toolbox, Nav2, EKF-Sensorfusion und die Cliff-Sicherheitslogik. Gemeinsam bilden diese Komponenten den vollstaendigen Fahrkern einschliesslich Sicherheitsmultiplexer.
* **Ebene B (Bedien- und Leitstandsebene):** Dashboard, Echtzeit-Telemetrie ueber WebSocket und MJPEG-Stream, Joystick-Fernsteuerung und Audio-Rueckmeldungen laufen auf dem Raspberry Pi 5.
* **Ebene C (Intelligente Interaktion):** Die Ebene umfasst Sprachschnittstelle, hybride Vision-Pipeline (Hailo-8L und Gemini-Cloud-Semantik), ArUco-Docking und semantische Interpretation auf dem Raspberry Pi 5.

Die Kommunikation zwischen ESP32-S3 und Raspberry Pi 5 erfolgt ueber micro-ROS per UART/USB-CDC ueber stabile udev-Symlinks (`/dev/amr_drive`, `/dev/amr_sensor`). Der Standard XRCE-DDS (eXtremely Resource Constrained Environments - Data Distribution Service) uebernimmt die Middleware-Funktion. Die Trennung der drei Ebenen sichert die deterministische Motorsteuerung und entkoppelt den Fahrkern von den rechenintensiven Navigationsalgorithmen.

## 2. Hardware-Komponenten

### 2.1 Antriebsstrang

Der Differentialantrieb nutzt zwei JGA25-370-Gleichstrommotoren mit integrierten Hall-Encodern. Ein Cytron MDD3A Dual-Motortreiber steuert die Motoren im Dual-PWM-Modus an. Die PWM-Frequenz betraegt 20 kHz bei einer Aufloesung von 8 Bit (Wertebereich 0 bis 255). Die empirisch ermittelte Anlaufschwelle (PWM-Deadzone) liegt bei 35. Unterhalb dieses Werts erzeugt der Antrieb kein ausreichendes Anlaufmoment.

Die kinematischen Parameter definieren das Bewegungsmodell. Der kalibrierte Raddurchmesser betraegt 65,67 mm. Grundlage bilden drei Bodentests mit Massbandvergleich und einem Korrekturfaktor von 98,5 / 97,55 gegenueber dem Nennwert von 65,0 mm. Die Spurbreite betraegt 178 mm. Die Encoder liefern im 2x-Quadraturmodus 748,6 (links) und 747,2 (rechts) Ticks pro Radumdrehung. Die Wegaufloesung betraegt demnach 0,276 mm pro Tick.

### 2.2 Sensorik

Der RPLIDAR A1 ist rueckwaerts auf dem Roboter montiert. Die Montage entspricht einer Yaw-Rotation von 180 Grad relativ zum Basis-Koordinatensystem (`base_link`). Der Scanner liefert Laserdaten mit 7,7 Hz ueber `/dev/ttyUSB0` bei 115200 Baud. Die maximale Reichweite betraegt 12 m.

Eine MPU6050-IMU (Inertial Measurement Unit) misst Beschleunigungen (+/- 2 g) und Drehraten (+/- 250 deg/s). Der I2C-Bus arbeitet im Fast-Mode (400 kHz). Ein Komplementaerfilter (Alpha = 0,98) fusioniert die Daten. Der Filter gewichtet das Gyroskop mit 98 Prozent und das aus den Encodern abgeleitete Heading mit 2 Prozent. Die Soll-Rate der Publikation auf `/imu` liegt bei 50 Hz. Die effektiv erreichte Rate sinkt auf 30 bis 35 Hz ab, da parallele I2C-Buszugriffe (Contention) am Sensor-Knoten Verzoegerungen verursachen.

Eine Sony-IMX296-Global-Shutter-Kamera ermoeglicht visuelles Docking. Die native Sensoraufloesung von 1456 x 1088 Pixeln bei 15 fps skaliert eine `v4l2loopback`-Bridge auf 640 x 480 Pixel herunter, um die Verarbeitungsaufloesung im Container zu reduzieren.

### 2.3 Recheneinheiten

Zwei ESP32-S3 arbeiten als echtzeitfaehige Steuerungseinheiten in einer Zwei-Knoten-Architektur. Das Dual-Core-Design (240 MHz) trennt Kommunikations- und Regelaufgaben. Die USB-CDC-Verbindung operiert mit 921600 Baud.

Der Raspberry Pi 5 (Debian Trixie, aarch64) uebernimmt als Teil des Fahrkerns (Ebene A) die Navigation, Lokalisierung und EKF-Sensorfusion sowie die Bedien- und Leitstandsebene (Ebene B). ROS 2 Humble laeuft containerisiert (`ros:humble-ros-base`), da Debian Trixie kein natives Paket bereitstellt. Der Container nutzt den Host-Network-Modus fuer DDS-Multicast.

## 3. Software-Architektur

### 3.1 Firmware auf dem ESP32-S3

Die Firmware nutzt FreeRTOS zur Aufgabentrennung auf zwei Kerne.

Core 0 betreibt den micro-ROS-Executor. Er empfaengt Geschwindigkeitsvorgaben (`/cmd_vel`) und publiziert Odometrie (`/odom`) mit 20 Hz Sollrate (gemessen: 18,3 Hz). Ein Inter-Core-Watchdog auf Core 0 ueberwacht den Heartbeat von Core 1 und loest bei mehr als 50 verpassten Zyklen einen Notfall-Stopp aus.

Core 1 fuehrt die PID-Regelschleife (Proportional-Integral-Derivative) mit 50 Hz aus. Der PID-Regler verwendet exponentiell geglaettete Encoder-Werte (Alpha = 0,3), um Quantisierungsrauschen zu mindern. Die Odometrie verwendet die ungefilterten Encoder-Rohdaten. Die Regelstrecke umfasst: Inverskinematik berechnen, Anti-Windup beruecksichtigen, Beschleunigungsrampe (max. 5,0 rad/s^2) anwenden und PWM ausgeben. Ein Failsafe-Timeout stoppt die Motoren nach 500 ms ohne eingehende Kommandos.

### 3.2 ROS-2-Stack auf dem Raspberry Pi 5 (Ebene A: Fahrkern)

Ein zentrales Launch-File (`full_stack.launch.py`) orchestriert den Stack. Da micro-ROS keinen TF-Broadcast (Transformation Framework) bereitstellt, konvertiert der Knoten `odom_to_tf` die `/odom`-Nachrichten mit 20 Hz in die dynamische TF-Transformation `odom -> base_link`.

Ein EKF-Knoten (Extended Kalman Filter) fusioniert die Rad-Odometrie mit den IMU-Daten des Sensor-Knotens. Die resultierende, geglaettete Pose erhoeht die Robustheit der Lokalisierung gegenueber Schlupf und Gyroskop-Drift.

`slam_toolbox` arbeitet im asynchronen Online-Modus und nutzt den Ceres-Solver zur nichtlinearen Optimierung der Pose. Der Knoten erzeugt eine Belegungskarte mit 5 cm Aufloesung. Loop Closure ist aktiv (Suchradius 8 m, Mindestkettenlaenge 10 Scans).

Nav2 stellt den Navigations-Stack bereit. AMCL (Adaptive Monte Carlo Localization) lokalisiert den Roboter mit 500 bis 2000 Partikeln. NavFn plant den globalen Pfad. Regulated Pure Pursuit fuehrt die lokale Bahnverfolgung mit maximal 0,15 m/s aus.

## 4. Kommunikationsarchitektur

### 4.1 micro-ROS / XRCE-DDS

Die Kommunikation nutzt XRCE-DDS. Die zulaessige Maximum Transmission Unit (MTU) von 512 Bytes ist fuer die Systemauslegung kritisch. Nachrichten oberhalb von 512 Bytes verwirft der Standard bei Best-Effort-QoS ohne Fehlermeldung. Da die serialisierte Odometrie-Nachricht 725 Bytes umfasst, erzwingt das System Reliable-QoS. Reliable Streams erlauben die Fragmentierung der Datenpakete bis zu 2048 Bytes.

### 4.2 ROS-2-Topics

Die Topic-Struktur trennt Fahrkommandos, Odometrie, IMU und Laserscan. Die strikte Trennung macht den Datenfluss zwischen Fahrkern, Sensorbasis und Navigation nachvollziehbar.

## 5. Navigations-Stack

Die Navigation erfolgt in drei Schritten. Zuerst erzeugt `slam_toolbox` eine Belegungskarte. Danach verfeinert AMCL die Pose und publiziert die Transformation `map -> odom`. Abschliessend berechnet NavFn einen globalen Pfad, waehrend Regulated Pure Pursuit die lokale Bahnverfolgung uebernimmt.

Die lokale Costmap (Kostenkarte zur Hindernisvermeidung) nutzt ein Rolling Window von 3x3 m. Sie kombiniert einen VoxelLayer (3D-Hinderniserfassung) und einen InflationLayer (Sicherheitsabstand) bei einem Inflationsradius von 25 cm. Der Goal Checker akzeptiert den Zielpunkt bei einer Positionstoleranz von 3 cm (0,03 m) und einer Yaw-Toleranz von 2,9 Grad (0,05 rad).

## 6. Schnittstellen und Parameter

Alle hardwarenahen Parameter liegen in den Headern `config_drive.h` und `config_sensors.h`. `static_assert`-Anweisungen sichern die Konfiguration zur Kompilierzeit ab. Die ESP32-S3 binden sich ueber die udev-Symlinks `/dev/amr_drive` und `/dev/amr_sensor` ein.

## 7. Erweiterte Module: Vision, Audio und Leitstandsebene

### 7.1 Hybride Vision-Pipeline

Lokale Objekterkennung beansprucht hohe Rechenleistung. Das System lagert die Inferenz daher auf einen Edge-Beschleuniger und einen Cloud-Dienst aus. `host_hailo_runner` liest den Videostream und fuehrt die Objekterkennung auf einem PCIe-angebundenen Hailo-8L-Chip aus. Die Inferenzzeit betraegt 34 ms pro Frame. Der Host sendet die Zielkoordinaten ueber UDP-Port 5005 in den ROS-2-Container. Anschliessend bewertet der `gemini_semantic_node` die Szene semantisch ueber die HTTPS-API eines externen Sprachmodells.

### 7.2 Audio und Leitstand

Der Knoten `audio_feedback_node` abonniert `/audio/play`. Nach Eingang einer Nachricht startet ein nicht blockierender Unterprozess, der direkt auf den I2S-Verstaerker (MAX98357A) zugreift. Die Prozessentkopplung verhindert Latenzen in der Echtzeitschleife.

Eine Vite-basierte Weboberflaeche uebertraegt den Videostream ueber TCP-Port 8082 und wickelt Telemetrie sowie manuelle Steuerbefehle ueber WebSocket auf TCP-Port 9090 ab.

## 8. Hardwarenahe Sicherheitslogik: Cliff-Sicherheitsmultiplexer

Die Kanten-Erkennung auf dem ESP32-S3 arbeitet zeitlich schneller als die Verarbeitung derselben Information im Nav2-Stack auf dem Raspberry Pi 5. Aus den gemessenen Latenzen folgt die Regel: Direkte Sensorsignale ueberstimmen algorithmisch berechnete Bewegungsbefehle stets.

Der Knoten `cliff_safety_node` fungiert als Befehlsmultiplexer. Der Sensor-Knoten publiziert den Status des Infrarot-Sensors mit 20 Hz auf `/cliff` und die Ultraschall-Distanz auf `/range/front`. Der Multiplexer leitet Bewegungsbefehle aus der Navigation im Normalbetrieb durch. Meldet `/cliff` eine Kante oder unterschreitet die Ultraschall-Distanz 80 mm, blockiert der Multiplexer die Navigation und erzeugt eigenstaendig einen harten Stopp (v = 0 m/s, w = 0 rad/s). Die Freigabe erfolgt erst bei einer Distanz ueber 120 mm (Hysterese). Die Anforderung fuer den ROS-2-Pfad (GPIO-Flanke am Sensor-Knoten bis Motorstopp-Befehl am Drive-Knoten) liegt bei weniger als 50 ms (SIA-01). Die Messung ergibt eine End-to-End-Latenz von 2,0 ms (Messprotokoll P2, cliff_latency_test).

Zusaetzlich uebermittelt der CAN-Bus ein redundantes Cliff-Signal direkt vom Sensor-Knoten an den Drive-Knoten, ohne den ROS-2-Stack zu durchlaufen. Die Anforderung fuer den CAN-Direktpfad liegt bei weniger als 20 ms (SIA-03).

Die Konsequenz aus beiden Pfaden ist eine lueckenlose Sicherheitslogik, die gegenueber Navigation und manueller Bedienung strikt uebergeordnet bleibt.

## 9. Schlussbetrachtung

Die Architektur sichert deterministische Regelkreise ab, erfordert aber die genaue Einhaltung serieller Bandbreitengrenzen (MTU 512 Bytes). Die Dreischicht-Architektur mit Fahrkern (Ebene A, einschliesslich Navigation und EKF-Sensorfusion auf dem Pi 5), Bedien- und Leitstandsebene (Ebene B) und intelligenter Interaktion (Ebene C) schliesst unkontrollierte Systemzustaende durch Sensorlatenzen oder Berechnungsengpaesse systematisch aus.

## Fachbegriffe

### 1. Robotik und Navigation

* **AMR (Autonomer mobiler Roboter):** Ein fahrerloses System, das sich ohne physische Leitlinien wie Schienen in seiner Umgebung orientiert und bewegt.
* **SLAM (Simultaneous Localization and Mapping):** Ein Verfahren, bei dem ein Roboter gleichzeitig eine Karte seiner unbekannten Umgebung erstellt und seine eigene Position darin fortlaufend berechnet.
* **Odometrie:** Die Schaetzung von Position und Orientierung anhand der Messdaten des eigenen Antriebssystems (hier: Radumdrehungen).
* **Kinematik / Inverskinematik:** Die Kinematik beschreibt die Geometrie der Bewegung. Die Inverskinematik berechnet aus einer gewuenschten Fahrgeschwindigkeit und Drehrichtung des Gesamtroboters die dafuer notwendigen Einzeldrehzahlen des linken und rechten Rades.
* **TF (Transformation Framework):** Ein Koordinatensystem-Verwaltungswerkzeug. Es verfolgt die raeumlichen Beziehungen zwischen verschiedenen Roboterteilen (z. B. Abstand zwischen Rad und Laserscanner) ueber die Zeit.
* **AMCL (Adaptive Monte Carlo Localization):** Ein probabilistischer Algorithmus, der Partikelfilterung nutzt, um die Roboterposition auf einer bereits vorhandenen Karte abzugleichen.
* **Costmap:** Eine zweidimensionale Kostenkarte zur Hindernisvermeidung. Der *VoxelLayer* repraesentiert 3D-Hindernisse raeumlich, der *InflationLayer* legt einen virtuellen Sicherheitsabstand um diese Hindernisse.

### 2. Regelungstechnik

* **PID-Regler (Proportional-Integral-Derivative):** Ein Regelkreis, der die Abweichung zwischen Soll- und Ist-Wert korrigiert. Er reagiert auf den aktuellen Fehler (proportional), die Summe der vergangenen Fehler (integral) und die Fehleraenderung (derivativ).
* **Anti-Windup:** Ein Schutzmechanismus im PID-Regler. Er verhindert, dass der Integralanteil bei einer physischen Blockade (z. B. Fahren gegen ein Hindernis) unendlich anwaechst und spaeter zu Fehlverhalten fuehrt.
* **Komplementaerfilter:** Ein Algorithmus zur Sensordatenfusion. Er gleicht die Schwaechen verschiedener Sensoren aus, indem er beispielsweise das Gyroskop fuer schnelle Rotationsaenderungen und Odometriedaten fuer langfristige Stabilitaet gewichtet.
* **EKF (Extended Kalman Filter):** Ein probabilistischer Schaetzalgorithmus, der mehrere verrauschte Sensorquellen (hier Rad-Odometrie und IMU) zu einer optimalen Positionsschaetzung fusioniert. Im Unterschied zum Komplementaerfilter auf dem ESP32-S3 laeuft der EKF auf dem Raspberry Pi 5 und nutzt ein vollstaendiges Zustandsmodell mit Kovarianzmatrix.
* **PWM (Pulsweitenmodulation):** Ein Verfahren zur Steuerung der Motorleistung. Die Versorgungsspannung wird in sehr schnellem Wechsel (20 kHz) ein- und ausgeschaltet.
* **Deadzone (Anlaufschwelle):** Der Mindestwert der PWM, der noetig ist, damit das elektromagnetische Feld die innere mechanische Reibung des Motors ueberwindet.

### 3. Hardware und Sensorik

* **LiDAR (Light Detection and Ranging):** Ein optischer Sensor, der Laserstrahlen aussendet und die Reflexionszeit misst, um Entfernungen zu umliegenden Objekten zu bestimmen.
* **IMU (Inertial Measurement Unit):** Ein Sensorbauteil, das lineare Beschleunigungen und Drehraten des Roboters im Raum misst.
* **Hall-Encoder:** Ein Sensor am Motor, der magnetische Umdrehungsimpulse in digitale Signale (Ticks) wandelt. Der *Quadraturmodus* verarbeitet zwei phasenverschobene Signale und ermoeglicht so die gleichzeitige Erkennung von Geschwindigkeit und Drehrichtung.
* **I2C / CAN-Bus:** Bussysteme zur Datenuebertragung. I2C verbindet Bauteile auf kurzen Distanzen direkt auf der Platine. CAN uebertraegt Daten robust in elektrisch stoeranfaelligen Umgebungen. *Contention* bezeichnet Konflikte, wenn mehrere Bauteile gleichzeitig senden wollen.
* **Global-Shutter:** Ein Kameratyp, der alle Pixel des Bildsensors exakt zum gleichen Zeitpunkt belichtet. Dies verhindert Bildverzerrungen bei schnellen Kamerabewegungen.

### 4. Software und Kommunikation

* **ROS 2 / micro-ROS:** Ein quelloffenes Software-Framework fuer die Roboterentwicklung. *micro-ROS* ist eine ressourcenschonende Variante, die speziell fuer Mikrocontroller (wie den ESP32-S3) konzipiert ist.
* **XRCE-DDS:** Der Datenuebertragungsstandard fuer ressourcenbeschraenkte Geraete. Er fungiert als *Middleware*, also als Vermittlerschicht zwischen verschiedenen Programmknoten.
* **MTU (Maximum Transmission Unit):** Die maximale Paketgroesse in Bytes, die ueber eine Schnittstelle am Stueck uebertragen werden kann.
* **QoS (Quality of Service):** Qualitaetsrichtlinien fuer Netzwerke. *Best-Effort* sendet Daten ohne Empfangsbestaetigung. *Reliable* stellt sicher, dass jedes Paket ankommt, und wiederholt fehlerhafte Sendungen.
* **FreeRTOS:** Ein Echtzeitbetriebssystem fuer Mikrocontroller. Es garantiert die strikte Einhaltung von Zeitvorgaben bei der Abarbeitung von Aufgaben (Tasks).
* **Inter-Core-Watchdog:** Ein Ueberwachungsmechanismus zwischen zwei Prozessorkernen. Meldet sich ein Kern nicht innerhalb einer definierten Zeitspanne (Heartbeat), versetzt der Watchdog das System automatisch in einen sicheren Zustand (Failsafe).
