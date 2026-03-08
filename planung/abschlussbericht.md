# Abschlussbericht: Autonomer mobiler Roboter für die Intralogistik

## 1. Einleitung

Die Flexibilisierung industrieller Fertigungsprozesse im Kontext von Industrie 4.0 erhöht die Anforderungen an die innerbetriebliche Logistik. Autonome mobile Roboter (AMR) adressieren diese Anforderung, weil sie ohne äußere Führungsinfrastruktur wie Leitlinien oder Reflektoren zwischen definierten Orten fahren können.

Die Arbeit entwickelt einen kostengünstigen AMR-Prototypen mit Differentialantrieb für den Transport von Kleinladungsträgern in intralogistischen Szenarien. Der Systementwurf kombiniert Open-Source-Komponenten mit einer verteilten Architektur. Zwei dedizierte ESP32-S3 übernehmen den Fahrkern sowie die Sensor- und Sicherheitsbasis. Ein Raspberry Pi 5 übernimmt Lokalisierung und Kartierung, Navigation, die Bedien- und Leitstandsebene sowie eine hybride Vision-Pipeline.

Die Arbeit beantwortet drei Forschungsfragen:

- **Forschungsfrage 1 (FF1):** Wie lässt sich eine echtzeitfähige Antriebsregelung und Sensorerfassung auf einer Dual-Knoten-Architektur mit Mikrocontrollern realisieren?
- **Forschungsfrage 2 (FF2):** Welchen Einfluss haben systematische Odometrie-Kalibrierung, IMU-Fusion und hardwarenahe Sicherheitslogik auf die Navigationsgenauigkeit?
- **Forschungsfrage 3 (FF3):** Erreicht ein monokulares Kamerasystem in Kombination mit Edge-KI und Cloud-Semantik eine ausreichend präzise Umgebungswahrnehmung für komplexe Innenräume und zentimetergenaues Docking?

## 2. Projektorganisation

Die Arbeit entstand als Einzelprojekt im Rahmen einer Bachelorarbeit unter Betreuung durch die Hochschule. Der Entwicklungszeitraum umfasste vier Monate von der Anforderungsanalyse bis zur Systemvalidierung.

Zum Einsatz kamen PlatformIO für die Firmware-Entwicklung, ROS 2 Humble in einer Docker-Umgebung für den Navigations-Stack, Git für die Versionskontrolle sowie Python für Validierungsskripte und Messauswertung. Der Entwicklungsprozess folgte einem iterativen Vorgehen mit frühen Hardware- und Integrationstests. Quantitative Akzeptanzkriterien übernahmen die Rolle zentraler Nachweise für die Abnahme.

## 3. Vorgehen im Projekt

Das methodische Vorgehen orientierte sich am V-Modell nach VDI 2206. Das Modell gliedert den Entwicklungsprozess in Entwurfs- und Verifikationsphasen mit klarer Zuordnung von Anforderungen, Systementwurf, Detailentwurf, Integration und Validierung.

Die Anforderungsphase definierte funktionale Anforderungen wie autonome Navigation, Hindernisvermeidung und präzises Docking. Zusätzlich spezifizierte die Anforderungsphase nichtfunktionale Anforderungen an Positionsgenauigkeit, Echtzeitverhalten, Reproduzierbarkeit und Systemstabilität.

Der Systementwurf zerlegte das Gesamtsystem in drei funktionale Ebenen:

1. **Drive-Knoten (ESP32-S3):** steuert die Motoren, regelt die Raddrehzahl und publiziert die Odometrie.
2. **Sensor-Knoten (ESP32-S3):** erfasst IMU-Daten, Batterieinformationen und Signale der Kanten-Erkennung.
3. **Bedien- und Leitstandsebene (Raspberry Pi 5):** übernimmt Lokalisierung und Kartierung, Navigation, Vision, Audio sowie Diagnosefunktionen.

Die Kommunikationsarchitektur nutzt micro-ROS über UART als deterministische Schnittstelle zwischen Mikrocontrollern und Host-Rechner. Diese Struktur entkoppelt die Echtzeit-Regelschleife des Fahrkerns von den rechenintensiven Verfahren für Kartierung, Planung und semantische Auswertung.

Die Implementierungsphase realisierte zunächst die hardwarenahen Funktionen, anschließend die Kartierung und Navigation und zuletzt die erweiterten Module für Vision, Audio und Docking. Die Verifikationsphase validierte zunächst einzelne Teilsysteme und anschließend das integrierte Gesamtsystem anhand definierter Akzeptanzkriterien.

## 4. Technische Lösung

Der Roboter nutzt einen Differentialantrieb mit zwei angetriebenen Rädern und einem frei drehbaren Stützrad. Der kalibrierte Raddurchmesser beträgt $65{,}67\,\mathrm{mm}$, die Spurbreite $178\,\mathrm{mm}$. Zwei JGA25-370-Getriebemotoren mit integrierten Hall-Encodern liefern im 2x-Quadraturmodus rund 748 Ticks pro Radumdrehung. Diese Messwerte bilden die Grundlage der Odometrie. Ein Cytron MDD3A-Motortreiber arbeitet im Dual-PWM-Modus und steuert beide Motoren separat an.

Zwei XIAO ESP32-S3 bilden die hardwarenahe Rechenebene:

- Der **Drive-Knoten** führt die PID-Regelschleife deterministisch mit $50\,\mathrm{Hz}$ aus und publiziert Odometrie mit $20\,\mathrm{Hz}$.
- Der **Sensor-Knoten** erfasst Sensordaten über I2C und publiziert IMU-, Batterie- und Kanten-Signale mit $20\,\mathrm{Hz}$.

Die Anbindung an den Raspberry Pi 5 erfolgt über UART mit $115200\,\mathrm{Bd}$. Die serielle Kopplung vermeidet zusätzliche Latenzen und Störeinflüsse drahtloser Verbindungen im Regelpfad.

Die Sensorik umfasst einen RPLIDAR A1 mit $360^\circ$-Abdeckung und einer nominellen Reichweite von $12\,\mathrm{m}$ für Lokalisierung und Kartierung. Eine Sony-IMX296-Global-Shutter-Kamera ergänzt die Sensorausstattung für visuelle Aufgaben. Ein Hailo-8L-Beschleuniger unterstützt die lokale Bildverarbeitung. Die Spannungsversorgung trennt die Versorgung der Logik- und Rechenebene von der Motorversorgung und nutzt dafür Buck-Converter für $5\,\mathrm{V}$ sowie eine direkte Akkuspeisung des Antriebs.

## 5. Softwarelösung

Die Firmware auf den ESP32-S3 trennt Kommunikations-, Regel- und Messaufgaben in klar definierte FreeRTOS-Tasks. Der Drive-Knoten verarbeitet eingehende `/cmd_vel`-Kommandos, berechnet Sollradgeschwindigkeiten über Inverskinematik und regelt die Motoren deterministisch mit $50\,\mathrm{Hz}$. Die Firmware kapselt Hardware-Abstraktion, Regelung und Kinematik in modularen Klassen. Der Sensor-Knoten erfasst IMU-, Batterie- und Kanten-Signale und publiziert die Daten über micro-ROS.

Der Raspberry Pi 5 betreibt ROS 2 Humble containerisiert in Docker, weil Debian Trixie keine native Paketbasis für ROS 2 Humble bereitstellt. Der ROS-2-Stack gliedert sich in vier Funktionsblöcke:

- **Lokalisierung und Kartierung:** `slam_toolbox` erzeugt Online-Karten mit einer Auflösung von $5\,\mathrm{cm}$. Der Knoten `odom_to_tf` wandelt Odometrie-Nachrichten in TF-Transformationen um.
- **Navigation:** Nav2 plant globale Pfade und führt die lokale Bahnverfolgung mit dem Regulated-Pure-Pursuit-Controller aus. Die Zielgeschwindigkeit beträgt $0{,}4\,\mathrm{m/s}$.
- **Sicherheitslogik:** Der Knoten `cliff_safety_node` priorisiert Signale der Kanten-Erkennung gegenüber Fahrkommandos aus Navigation und Bedienebene. Im Auslösefall sendet der Knoten einen sofortigen Stopp mit $v = 0\,\mathrm{m/s}$ und $\omega = 0\,\mathrm{rad/s}$ an den Drive-Knoten.
- **Hybride Vision-Pipeline:** Der Host-Knoten `host_hailo_runner` führt lokale Objekterkennung auf Edge-Hardware aus. Der Knoten `gemini_semantic_node` ergänzt die Wahrnehmung durch asynchrone semantische Auswertung über eine Cloud-Schnittstelle.

Die zentrale Launch-Datei koordiniert alle ROS-2-Komponenten über konfigurierbare Argumente. Python-Skripte validieren Encoder-Kalibrierung, PID-Sprungantwort, Kinematik, Lokalisierung und Kartierung sowie Navigation systematisch.

```text
┌─────────────────────────────────────────────────────────────┐
│                       Systemarchitektur                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────┐            ┌──────────────────────┐ │
│  │ Drive-Knoten ESP32 │ <─UART/DDS→│    Raspberry Pi 5    │ │
│  │ (Fahrkern)         │            │ Bedien- und          │ │
│  │                    │            │ Leitstandsebene      │ │
│  └────────────────────┘            │                      │ │
│                                    │ - Navigation         │ │
│  ┌────────────────────┐            │ - Kartierung         │ │
│  │ Sensor-Knoten ESP32│ <─UART/DDS→│ - Sicherheitslogik   │ │
│  │ (Sensor- und       │            │ - Bedien- und        │ │
│  │ Sicherheitsbasis)  │            │   Leitstandsebene    │ │
│  └────────────────────┘            │ - Audio              │ │
│                                    └──────────────────────┘ │
│                                             │         │      │
│                                       UDP 5005   HTTPS API   │
│                                             │         │      │
│                                      ┌──────────┐ ┌────────┐ │
│                                      │ Hailo-8L │ │ Gemini │ │
│                                      │   Edge   │ │ Cloud  │ │
│                                      └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 6. Ergebnisse und Bewertung

Die experimentelle Validierung beantwortet alle drei Forschungsfragen mit belastbaren Messwerten.

**Forschungsfrage 1:**
Die Trennung in Drive-Knoten und Sensor-Knoten ermöglicht eine echtzeitfähige Motorregelung mit $50\,\mathrm{Hz}$. Die Architektur hält den Regelpfad frei von blockierenden Sensorabfragen und Kommunikationslast. Die gemessene Jitter-Breite liegt unter $2\,\mathrm{ms}$.

**Forschungsfrage 2:**
Die systematische UMBmark-Kalibrierung reduzierte die systematischen Odometriefehler um etwa den Faktor 10. Die Kalibrierung bildet zusammen mit IMU-Fusion und hardwarenaher Sicherheitslogik die Grundlage für reproduzierbare Lokalisierung und Kartierung. Der Absolute Trajectory Error beträgt $0{,}16\,\mathrm{m}$ und bleibt damit unter dem Akzeptanzkriterium von $0{,}20\,\mathrm{m}$.

**Forschungsfrage 3 (bedingt bestätigt):**
Die hybride Vision-Pipeline kombiniert lokale Objekterkennung mit semantischer Auswertung. Die lokale Edge-Inferenz erreicht eine Latenz von etwa $34\,\mathrm{ms}$ und bleibt damit schnell genug für eine laufende Anpassung der Navigation. Das ArUco-basierte Docking arbeitet präzise genug für den Ladekontakt mit einer Erfolgsquote von $80\,\%$ bei 10 Versuchen. Die mittlere Navigationsgenauigkeit beträgt über zehn Testfahrten $6{,}4\,\mathrm{cm}$ in der Ebene und $4{,}2^\circ$ in der Gier. Grenzen bestehen bei ungünstiger Beleuchtung, eingeschränktem Sichtfeld und verdeckter Marker-Sichtbarkeit.

## 7. Fazit

Der entwickelte Prototyp zeigt, dass ein kostengünstiges AMR-System mit verteilter Architektur, Open-Source-Software und handelsnahen Komponenten belastbare Ergebnisse in einem intralogistischen Anwendungsszenario liefern kann. Das V-Modell nach VDI 2206 strukturierte die Entwicklungsarbeit sinnvoll, auch wenn die lineare Grundform des Modells iterative Softwarezyklen nur eingeschränkt abbildet.

Die technischen Grenzen liegen vor allem in der Schlupfempfindlichkeit der Rad-Odometrie auf rauem Untergrund und in der Latenz externer Cloud-Dienste für semantische Auswertung. Der Prototyp kostet mit rund $513\,\mathrm{EUR}$ etwa ein Drittel eines TurtleBot 4, erreicht aber nicht den Sicherheits- und Reifegrad industrieller Systeme mit redundanter Sensorik und normativer Absicherung, etwa nach ISO 3691-4.

Weiterführende Arbeiten sollten Multi-Roboter-Koordination, robustere Docking-Strategien, industrielle Härtung der Mechanik und eine stärkere Entkopplung cloudbasierter Funktionen adressieren. Damit lässt sich die Lücke zwischen Forschungsprototyp und produktionsnahem System weiter schließen.
