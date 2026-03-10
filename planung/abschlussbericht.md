# Abschlussbericht: Autonomer mobiler Roboter fuer die Intralogistik

## 1. Einleitung

Die Flexibilisierung industrieller Fertigungsprozesse im Kontext von Industrie 4.0 erhoeht die Anforderungen an die innerbetriebliche Logistik. Autonome mobile Roboter (AMR) adressieren diese Anforderung, weil sie ohne aeussere Fuehrungsinfrastruktur wie Leitlinien oder Reflektoren zwischen definierten Orten fahren koennen.

Die Arbeit entwickelt einen kostenguenstigen AMR-Prototypen mit Differentialantrieb fuer den Transport von Kleinladungstraegern in intralogistischen Szenarien. Der Systementwurf kombiniert Open-Source-Komponenten mit einer verteilten Architektur. Zwei dedizierte ESP32-S3 uebernehmen den Fahrkern sowie die Sensor- und Sicherheitsbasis. Ein Raspberry Pi 5 uebernimmt Lokalisierung und Kartierung, Navigation, die Bedien- und Leitstandsebene sowie eine hybride Vision-Pipeline.

Die Arbeit beantwortet drei Projektfragen:

- **Projektfrage 1 (PF1):** Wie laesst sich eine echtzeitfaehige Antriebsregelung und Sensorerfassung auf einer Dual-Knoten-Architektur mit Mikrocontrollern realisieren?
- **Projektfrage 2 (PF2):** Welchen Einfluss haben systematische Odometrie-Kalibrierung, IMU-Fusion und hardwarenahe Sicherheitslogik auf die Navigationsgenauigkeit?
- **Projektfrage 3 (PF3):** Erreicht ein monokulares Kamerasystem in Kombination mit Edge-KI und Cloud-Semantik eine ausreichend praezise Umgebungswahrnehmung fuer komplexe Innenraeume und zentimetergenaues Docking?

## 2. Projektorganisation

Die Arbeit entstand als Einzelprojekt im Rahmen einer Projektarbeit unter Betreuung durch die Hochschule. Der Entwicklungszeitraum umfasste vier Monate von der Anforderungsanalyse bis zur Systemvalidierung.

Zum Einsatz kamen PlatformIO fuer die Firmware-Entwicklung, ROS 2 Humble in einer Docker-Umgebung fuer den Navigations-Stack, Git fuer die Versionskontrolle sowie Python fuer Validierungsskripte und Messauswertung. Der Entwicklungsprozess folgte einem iterativen Vorgehen mit fruehen Hardware- und Integrationstests. Quantitative Akzeptanzkriterien uebernahmen die Rolle zentraler Nachweise fuer die Abnahme.

## 3. Vorgehen im Projekt

Das methodische Vorgehen orientierte sich am V-Modell nach VDI 2206 fuer die Entwicklung mechatronischer Systeme. Das Modell gliedert den Entwicklungsprozess mit klarer Zuordnung von Anforderungsdefinition, Systementwurf, domaenenspezifischem Entwurf, Integration und Eigenschaftsabsicherung.

Die Anforderungsdefinition spezifizierte funktionale Anforderungen wie autonome Navigation, Hindernisvermeidung und praezises Docking. Zusaetzlich definierte sie nichtfunktionale Anforderungen an Positionsgenauigkeit, Echtzeitverhalten, Reproduzierbarkeit und Systemstabilitaet.

Der Systementwurf zerlegte das Gesamtsystem in drei funktionale Ebenen:

1. **Drive-Knoten (ESP32-S3):** steuert die Motoren, regelt die Raddrehzahl und publiziert die Odometrie.
2. **Sensor-Knoten (ESP32-S3):** erfasst IMU-Daten, Batterieinformationen und Signale der Kanten-Erkennung.
3. **Bedien- und Leitstandsebene (Raspberry Pi 5):** uebernimmt Lokalisierung und Kartierung, Navigation, Vision, Audio sowie Diagnosefunktionen.

Die Kommunikationsarchitektur nutzt micro-ROS ueber UART als deterministische Schnittstelle zwischen Mikrocontrollern und Host-Rechner. Diese Struktur entkoppelt die Echtzeit-Regelschleife des Fahrkerns von den rechenintensiven Verfahren fuer Kartierung, Planung und semantische Auswertung.

Die Prinziploesung legte drei zentrale Entwurfsentscheidungen fest. Erstens faellt die Wahl des Antriebskonzepts auf einen Differentialantrieb, weil dieser mit zwei Motoren und einem Stuetzrad kinematisch einfach, kostenguenstig und fuer Innenraeume wendig genug ist. Zweitens setzt die Architektur auf eine verteilte Zwei-Knoten-MCU-Struktur mit getrenntem Drive-Knoten und Sensor-Knoten, um die deterministische Regelschleife von blockierenden I2C-Sensorabfragen zu entkoppeln. Drittens erfolgt die Anbindung an ROS 2 ueber micro-ROS statt nativem DDS, da die ESP32-S3 den Ressourcenbedarf eines vollstaendigen DDS-Stacks nicht tragen.

Die Implementierungsphase realisierte zunaechst die hardwarenahen Funktionen, anschliessend die Kartierung und Navigation und zuletzt die erweiterten Module fuer Vision, Audio und Docking. Die Eigenschaftsabsicherung integrierte und validierte zunaechst einzelne Teilsysteme und im Anschluss das Gesamtsystem anhand quantitativer Akzeptanzkriterien.

Die funktionale Phasenstruktur bildet die domaenenspezifischen Entwuerfe der VDI 2206 implizit ab. Phase 1 adressiert die Domaenen Elektronik (Motoransteuerung, Encoder-Anbindung), Regelungstechnik (PID, Inverskinematik) und Software (FreeRTOS-Firmware, micro-ROS-Integration). Phase 2 erweitert dies um die Sensordomaene (I2C-Peripherie, Signalverarbeitung). Die Phasen 3 und 4 liegen vollstaendig in der Softwaredomaene auf dem Raspberry Pi 5.

Der Entwicklungsprozess durchlief mehrere Iterationsschleifen ueber die Arme des V-Modells. Die UMBmark-Kalibrierung in Phase 2 fuehrte zu einer Korrektur der Kinematikparameter in config_drive.h und erforderte einen Ruecksprung in den domaenenspezifischen Entwurf von Phase 1. Ebenso fuehrte die Cliff-Sensor-Latenzvalidierung zu einer Anpassung der Abtastrate und der Interrupt-Logik im Sensor-Knoten. Diese Rueckspruenge entsprechen den von der VDI 2206 (Ausgabe 2021) vorgesehenen Iterationszyklen zwischen Eigenschaftsabsicherung und domaenenspezifischem Entwurf.

## 4. Technische Loesung

Der Roboter nutzt einen Differentialantrieb mit zwei angetriebenen Raedern und einem frei drehbaren Stuetzrad. Der kalibrierte Raddurchmesser betraegt 65,67 mm, die Spurbreite 178 mm. Zwei JGA25-370-Getriebemotoren mit integrierten Hall-Encodern liefern im 2x-Quadraturmodus rund 748 Ticks pro Radumdrehung. Diese Messwerte bilden die Grundlage der Odometrie. Ein Cytron MDD3A-Motortreiber arbeitet im Dual-PWM-Modus und steuert beide Motoren separat an.

Zwei XIAO ESP32-S3 bilden die hardwarenahe Rechenebene:

- Der **Drive-Knoten** fuehrt die PID-Regelschleife deterministisch mit 50 Hz aus und publiziert Odometrie mit 20 Hz.
- Der **Sensor-Knoten** erfasst Sensordaten ueber I2C und publiziert IMU-, Batterie- und Kanten-Signale mit 20 Hz.

Die Anbindung an den Raspberry Pi 5 erfolgt ueber UART mit 921600 Baud. Die serielle Kopplung vermeidet zusaetzliche Latenzen und Stoereinfluesse drahtloser Verbindungen im Regelpfad.

Die Sensorik umfasst einen RPLIDAR A1 mit 360-Grad-Abdeckung und einer nominellen Reichweite von 12 m fuer Lokalisierung und Kartierung. Eine Sony-IMX296-Global-Shutter-Kamera ergaenzt die Sensorausstattung fuer visuelle Aufgaben. Ein Hailo-8L-Beschleuniger unterstuetzt die lokale Bildverarbeitung. Die Spannungsversorgung trennt die Versorgung der Logik- und Rechenebene von der Motorversorgung und nutzt dafuer Buck-Converter fuer 5 V sowie eine direkte Akkuspeisung des Antriebs.

## 5. Softwareloesung

Die Firmware auf den ESP32-S3 trennt Kommunikations-, Regel- und Messaufgaben in klar definierte FreeRTOS-Tasks. Der Drive-Knoten verarbeitet eingehende `/cmd_vel`-Kommandos, berechnet Sollradgeschwindigkeiten ueber Inverskinematik und regelt die Motoren deterministisch mit 50 Hz. Die Firmware kapselt Hardware-Abstraktion, Regelung und Kinematik in modularen Klassen. Der Sensor-Knoten erfasst IMU-, Batterie- und Kanten-Signale und publiziert die Daten ueber micro-ROS.

Der Raspberry Pi 5 betreibt ROS 2 Humble containerisiert in Docker, weil Debian Trixie keine native Paketbasis fuer ROS 2 Humble bereitstellt. Der ROS-2-Stack gliedert sich in vier Funktionsbloecke:

- **Lokalisierung und Kartierung:** `slam_toolbox` erzeugt Online-Karten mit einer Aufloesung von 5 cm. Der Knoten `odom_to_tf` wandelt Odometrie-Nachrichten in TF-Transformationen um.
- **Navigation:** Nav2 plant globale Pfade und fuehrt die lokale Bahnverfolgung mit dem Regulated-Pure-Pursuit-Controller aus. Die Zielgeschwindigkeit betraegt 0,4 m/s.
- **Sicherheitslogik:** Der Knoten `cliff_safety_node` priorisiert Signale der Kanten-Erkennung gegenueber Fahrkommandos aus Navigation und Bedienebene. Im Ausloesefall sendet der Knoten einen sofortigen Stopp mit v = 0 m/s und w = 0 rad/s an den Drive-Knoten.
- **Hybride Vision-Pipeline:** Der Host-Knoten `host_hailo_runner` fuehrt lokale Objekterkennung auf Edge-Hardware aus. Der Knoten `gemini_semantic_node` ergaenzt die Wahrnehmung durch asynchrone semantische Auswertung ueber eine Cloud-Schnittstelle.

Die zentrale Launch-Datei koordiniert alle ROS-2-Komponenten ueber konfigurierbare Argumente. Python-Skripte validieren Encoder-Kalibrierung, PID-Sprungantwort, Kinematik, Lokalisierung und Kartierung sowie Navigation systematisch.

```text
┌─────────────────────────────────────────────────────────────┐
│                       Systemarchitektur                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────┐            ┌──────────────────────┐ │
│  │ Drive-Knoten ESP32 │ <─UART/DDS→│    Raspberry Pi 5    │ │
│  │ (Fahrkern)         │            │ Bedien- und          │ │
│  └─▲──────────────────┘            │ Leitstandsebene      │ │
│    │ CAN-Notstopp                  │                      │ │
│  ┌─▼──────────────────┐            │ - Navigation         │ │
│  │ Sensor-Knoten ESP32│ <─UART/DDS→│ - Kartierung         │ │
│  │ (Sensor- und       │            │ - Sicherheitslogik   │ │
│  │ Sicherheitsbasis)  │            │ - Bedien- und        │ │
│  └────────────────────┘            │   Leitstandsebene    │ │
│                                    │ - Audio              │ │
│                                    └──────────────────────┘ │
│                                             │         │     │
│                                       UDP 5005   HTTPS API  │
│                                             │         │     │
│                                      ┌──────────┐ ┌───────┐ │
│                                      │ Hailo-8L │ │ Cloud │ │
│                                      │   Edge   │ │ LLM   │ │
│                                      └──────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────┘

```

## 6. Ergebnisse und Bewertung

Die experimentelle Validierung beantwortet alle drei Projektfragen mit belastbaren Messwerten.

**Projektfrage 1:**
Die Trennung in Drive-Knoten und Sensor-Knoten ermoeglicht eine echtzeitfaehige Motorregelung mit 50 Hz. Die Architektur haelt den Regelpfad frei von blockierenden Sensorabfragen und Kommunikationslast. Die gemessene Jitter-Breite liegt unter 2 ms.

**Projektfrage 2:**
Die systematische UMBmark-Kalibrierung reduzierte die systematischen Odometriefehler um etwa den Faktor 10. Die Kalibrierung bildet zusammen mit IMU-Fusion und hardwarenaher Sicherheitslogik die Grundlage fuer reproduzierbare Lokalisierung und Kartierung. Der Absolute Trajectory Error betraegt 0,16 m und bleibt damit unter dem Akzeptanzkriterium von 0,20 m.

**Projektfrage 3 (bedingt bestaetigt):**
Die hybride Vision-Pipeline kombiniert lokale Objekterkennung mit semantischer Auswertung. Die lokale Edge-Inferenz erreicht eine Latenz von etwa 34 ms und bleibt damit schnell genug fuer eine laufende Anpassung der Navigation. Das ArUco-basierte Docking arbeitet praezise genug fuer den Ladekontakt mit einer Erfolgsquote von 80 Prozent bei 10 Versuchen. Die mittlere Navigationsgenauigkeit betraegt ueber zehn Testfahrten 6,4 cm in der Ebene und 4,2 Grad in der Gier. Grenzen bestehen bei unguenstiger Beleuchtung, eingeschraenktem Sichtfeld und verdeckter Marker-Sichtbarkeit.

## 7. Fazit

Der entwickelte Prototyp zeigt, dass ein kostenguenstiges AMR-System mit verteilter Architektur, Open-Source-Software und handelsnahen Komponenten belastbare Ergebnisse in einem intralogistischen Anwendungsszenario liefern kann. Das V-Modell nach VDI 2206 strukturierte die Entwicklungsarbeit sinnvoll, auch wenn die lineare Grundform des Modells iterative Softwarezyklen nur eingeschraenkt abbildet.

Die technischen Grenzen liegen vor allem in der Schlupfempfindlichkeit der Rad-Odometrie auf rauem Untergrund und in der Latenz externer Cloud-Dienste fuer semantische Auswertung. Der Prototyp kostet mit rund 513 EUR etwa ein Drittel eines TurtleBot 4, erreicht aber nicht den Sicherheits- und Reifegrad industrieller Systeme mit redundanter Sensorik und normativer Absicherung, etwa nach ISO 3691-4.

Weiterfuehrende Arbeiten sollten Multi-Roboter-Koordination, robustere Docking-Strategien, industrielle Haertung der Mechanik und eine staerkere Entkopplung cloudbasierter Funktionen adressieren. Damit laesst sich die Luecke zwischen Forschungsprototyp und produktionsnahem System weiter schliessen.
