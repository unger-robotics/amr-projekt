 # Exposé-Gliederung und Literaturstrategie für eine AMR-Bachelorarbeit mit ROS 2

## Zusammenfassung

Dieses Dokument liefert zwei konkrete Arbeitsergebnisse für eine ingenieurwissenschaftlich anwendungsorientierte Bachelorarbeit (B.Sc.) über eine autonome mobile Roboterplattform (AMR) mit dem Hardware-Stack ESP32-S3 (Dual-Core, FreeRTOS, micro-ROS) + Raspberry Pi 5 (ROS 2 Humble) + Differentialantrieb.

**Ergebnis 1** definiert eine vollständige, am VDI 2206 V-Modell ausgerichtete Gliederung (Exposé) mit Seitenproportionierung.

**Ergebnis 2** bildet die gesamte Literaturlandschaft über vier Themenfelder ab — SLAM & Navigation, Sensorfusion, micro-ROS/ESP32 und Kinematik & Regelung — mit identifizierten Quellen, datenbankspezifischen Suchstrings und einer priorisierten Lesereihenfolge von Masterquellen zu Satellitenquellen.

---

## Ergebnis 1: Exposé-Gliederung nach VDI 2206

### Arbeitstitel

> **Effizienz auf der letzten Meile**
> Konzeption und Validierung eines Navigationssystems für einen autonomen Kleinladungsträger-Transporter unter Nutzung von ROS 2

### Methodischer Rahmen

Das V-Modell nach VDI 2206 (Entwicklungsmethodik für mechatronische Systeme) strukturiert die Arbeit in die Phasen Anforderungserhebung → Systemarchitektur & Entwurf → Implementierung → Systemintegration → Verifikation & Validierung. Jede Phase bildet ein eigenes Kapitel, sodass der „rote Faden" zwischen Anforderung und Nachweis durchgehend sichtbar bleibt.

### Empfohlene Kapitelstruktur

**Titel:** Effizienz auf der letzten Meile: Konzeption und Validierung eines Navigationssystems für einen autonomen Kleinladungsträger-Transporter unter Nutzung von ROS 2

Abstract
Autonome Mobile Roboter (AMR) sind eine Schlüsseltechnologie für die Flexibilisierung innerbetrieblicher Materialflüsse (Intralogistik). Insbesondere für kleine und mittlere Unternehmen (KMU) stellen die hohen Investitionskosten industrieller Lösungen jedoch oft eine Hürde dar. Diese Arbeit entwickelt und validiert ein kosteneffizientes, modulares Navigationssystem für den Transport von Kleinladungsträgern (KLT), basierend auf dem Robot Operating System 2 (ROS 2 Humble).

Der Entwicklungsprozess folgt der VDI-Richtlinie 2206 für mechatronische Systeme. Das Systemkonzept basiert auf einer verteilten Rechenarchitektur: Ein Raspberry Pi 5 übernimmt als High-Level-Controller die rechenintensive Pfadplanung und Kartierung (SLAM), während ein ESP32-Mikrocontroller die echtzeitkritische Motorregelung und Odometrie-Erfassung ausführt. Zur Gewährleistung harter Echtzeitanforderungen wird eine **Dual-Core-Partitionierung** auf dem ESP32 implementiert, die die Kommunikation (micro-ROS Agent) strikt vom Regelkreis (PID) trennt.

Die Navigation erfolgt mittels 2D-LiDAR-Sensorik und dem **Nav2-Stack**, konfiguriert mit einem *Regulated Pure Pursuit* Controller für präzise Pfadverfolgung. Um die systematischen Fehler der Odometrie zu minimieren, wird das kinematische Modell mittels der **UMBmark-Methode** kalibriert. Als Erweiterung zum Standard-Stack wird ein visuelles Docking-System implementiert, das mittels einer monokularen Kamera und **ArUco-Markern** eine zentimetergenaue Positionierung an der Ladestation ermöglicht.

Die Validierung bestätigt die Robustheit des Systems: Nach der Kalibrierung konnte die Odometrie-Abweichung signifikant reduziert werden. Das System erreicht in realen Testszenarien eine Navigationsgenauigkeit von  **[X]** cm und eine erfolgreiche Docking-Rate von **[Y]** %. Die Arbeit zeigt somit, dass sich mit aktueller Open-Source-Software und Low-Cost-Hardware leistungsfähige Intralogistik-Lösungen realisieren lassen, sofern Echtzeit-Constraints und Kalibrierung methodisch berücksichtigt werden.

---

Inhaltsverzeichnis
Abkürzungsverzeichnis

---

1. Einleitung

#### 1.1 Ausgangssituation und Problemstellung

* **Der "Trichter"-Einstieg:**
* *Makro-Ebene:* Industrie 4.0 und der Wandel der Intralogistik (Flexibilisierung statt starrer Förderbänder).
* *Meso-Ebene:* Der Fachkräftemangel zwingt KMUs zur Automatisierung von "Low-Value"-Aufgaben wie dem KLT-Transport (Kleinladungsträger).
* *Mikro-Ebene (Das Problem):* Industrielle AMRs (z. B. MiR100) sind für einfache KLT-Aufgaben oft „over-engineered“ und zu teuer (> 20.000 €).
* *Die Lücke:* Es fehlt an validierten Referenzarchitekturen für kostengünstige, offene Systeme auf Basis moderner Middleware (ROS 2), die dennoch echtzeitfähig sind.



#### 1.2 Zielsetzung und Forschungsfragen

* **Hauptziel:** Entwicklung und Validierung eines ROS 2-basierten Navigationssystems für einen Low-Cost-AMR, das Industrienormen (Echtzeit, Genauigkeit) annähert.
* **Scope (Abgrenzung):**
* *In Scope:* Indoor-Navigation, ebener Boden, KLT-Format, Prototyping.
* *Out of Scope:* Serienzuteilung (CE-Kennzeichnung), Außeneinsatz, Schwerlast > 20 kg.


* **Forschungsfragen (FF):** Hier definieren wir 3 Fragen, die du im Fazit (Kap. 7) beantwortest:
* **FF1 (Architektur):** Wie lässt sich auf einem ESP32-Mikrocontroller eine echtzeitfähige Regelung unter Nutzung von micro-ROS realisieren, ohne dass WLAN-Latenzen die Motorsteuerung destabilisieren? *[Bezug: Woche 3/Dual-Core]*
* **FF2 (Präzision):** Welchen Einfluss hat eine systematische Odometrie-Kalibrierung (UMBmark) auf die absolute Navigationsgenauigkeit eines Low-Cost-Differentialantriebs? *[Bezug: Woche 4/DeGiorgi]*
* **FF3 (Funktionalität):** Ist ein monokulares Kamerasystem mit ArUco-Markern hinreichend robust, um einen mechanischen Ladekontakt ( cm) autonom zu treffen? *[Bezug: Woche 4/Docking]*



#### 1.3 Vorgehensweise und Methodik

* Begründung der Wahl von **VDI 2206** (V-Modell für mechatronische Systeme) als Rahmenwerk.
* Erklärung der Adaption: Nutzung des "linken Schenkels" für den Entwurf und des "rechten Schenkels" für die Validierung.
* Hinweis auf iterative Elemente (agile Softwareentwicklung mit ROS 2) innerhalb der Phasen.

#### 1.4 Aufbau der Arbeit

* Kurzer "Reiseführer" durch die Kapitel: *"Nach den theoretischen Grundlagen in Kapitel 2 folgt..."*

---


2. Grundlagen und Stand der Technik

**2.1 AMR in der Intralogistik und Entwicklungsmethodik**

* Abgrenzung: AMR vs. FTS (AGV) vs. Mobile Roboter.
* Anwendungsfall: KLT-Transport (Kleinladungsträger).
* **VDI 2206:** Das V-Modell für mechatronische Systeme (Systemdesign  Modellbildung  Integration).

**2.2 Mathematische Modellierung mobiler Roboter**

* **Kinematik des Differentialantriebs:** Vorwärts- und inverse Kinematik (Siegwart).
* **Odometrie-Fehlermodelle:** Systematische vs. nicht-systematische Fehler (DeGiorgi Paper).
* **Regelungstechnik:** PID-Regler, Anti-Windup und Kaskadierung auf Mikrocontrollern (Albarran Paper).

**2.3 Sensorik und Aktorik**

* Umgebungserfassung: 2D-LiDAR (Funktionsprinzip TOF/Triangulation).
* Propriozeption: Inkrementalgeber (Quadratursignale) und IMU (Sensorfusion).
* **Visuelle Marker:** ArUco-Erkennung und Pose-Estimation (Grundlage für Docking).

**2.4 Software-Architektur und Middleware**

* **ROS 2:** Das Node-Konzept, DDS (Data Distribution Service) und QoS (Quality of Service) (Macenski Paper).
* **micro-ROS:** Einbindung von Mikrocontrollern (XRCE-DDS), Executor-Konzepte und Echtzeitanforderungen (Staschulat/Yordanov Papers).
* Architektur-Pattern: Partitionierung (Dual-Core ESP32) und Lifecycle-Management.

**2.5 Kartierung und Lokalisierung (SLAM)**

* Graph-based SLAM vs. Filter-based SLAM (Vergleich Gmapping vs. SLAM Toolbox).
* Loop Closure Detection und Pose-Graph-Optimierung (Macenski/MDPI Comparison).
* Probabilistische Lokalisierung: AMCL (Adaptive Monte Carlo Localization).

**2.6 Autonome Navigation (Nav2)**

* **Behavior Trees:** Entscheidungslogik statt State Machines.
* **Planung:** Global Planner (A*/NavFn) vs. Local Controller (DWA vs. Regulated Pure Pursuit).
* Costmaps: Layer-Konzept (Static, Obstacle, Inflation).

---

3. Anforderungsanalyse [≙ VDI 2206: Anforderungserhebung]

**3.1 Szenariobeschreibung und Prozessanalyse**

* Beschreibung des "KLT-Transport"-Szenarios (Start  Abholen  Ziel  Docking).
* Ableitung der Systemgrenzen (Was macht der Roboter, was macht der Mensch?).

**3.2 Technische Randbedingungen und Restriktionen**

* **Hardware-Vorgaben:** Nutzung von Raspberry Pi 5 (High-Level) und ESP32 (Low-Level).
* **Software-Stack:** Zwingende Nutzung von ROS 2 (Humble/Jazzy) und micro-ROS.
* **Kostenrahmen:** Low-Cost-Ansatz (Verzicht auf Industrie-Laserscanner > 1000€).

**3.3 Funktionale Anforderungen**

* **F01 Navigation:** Kartierung (SLAM) und autonome Pfadplanung (A*/Nav2).
* **F02 Lokalisierung:** Globale (AMCL) und lokale (Odometrie) Positionsbestimmung.
* **F03 Docking:** Präzises Anfahren einer Ladestation mittels visueller Marker (ArUco). *<-- Wichtig für Woche 4!*
* **F04 Sicherheit:** Not-Halt bei Hinderniserkennung (Lidar-Schutzfeld).

**3.4 Nicht-funktionale Anforderungen**

* **N01 Echtzeitfähigkeit:** Regelzyklus der Motorsteuerung (50 Hz,  20ms Jitter) *[Ref: Staschulat/Yordanov]*.
* **N02 Genauigkeit:**
* Navigation:  10 cm (Nav2).
* Docking:  2 cm (ArUco) *[Ref: MDPI Docking Paper]*.


* **N03 Robustheit:** Wiederanlauf nach WLAN-Verlust (Recovery Behaviors).

**3.5 Anforderungsliste (Lastenheft)**

* Tabellarische Auflistung nach MoSCoW-Prinzip (Must / Should / Could / Won't).

---

4. Systemkonzept und Entwurf [≙ VDI 2206: Systemarchitektur & Entwurf]

**4.1 Morphologischer Kasten und Konzeptauswahl**

* Gegenüberstellung von Lösungsalternativen (z. B. Recheneinheit: RPi vs. Jetson vs. NUC).
* **Nutzwertanalyse:** Bewertung und Auswahlentscheidung (Warum RPi 5 + ESP32?  Kosten/Nutzen, Verfügbarkeit). *[Hierhin verschoben!]*

**4.2 Gesamtsystemarchitektur**

* Blockschaltbild der Kommunikation (High-Level vs. Low-Level).
* Schnittstellendefinition: USB-Serial Transport (micro-ROS) und Protokoll-Design.

**4.3 Mechanischer und Elektronischer Entwurf**

* **Mechanik:** Chassis-Layout und Sensorplatzierung (Lidar Field-of-View, Achsabstand für Odometrie).
* **Elektronik:** Schaltplan-Entwurf.
* Spannungsversorgung (Buck-Converter für RPi 5 und Motoren).
* Pegelanpassung (3.3V Logik ESP32 vs. 5V Sensoren).
* Verkabelungsplan (Encoder-Pins, PWM-Pins).



**4.4 Software-Architektur und Partitionierung**

* **ROS 2 Node-Graph:** Visualisierung der Topics (`/cmd_vel`, `/odom`, `/scan`) und TFs (`map` -> `odom` -> `base_link`).
* **ESP32-Design:** Dual-Core Partitionierung (Core 0: Comm, Core 1: Control) *[Ref: Yordanov Paper]*.
* **Containerisierung:** Docker-Setup für den micro-ROS Agent auf dem Pi.

**4.5 Entwurf der Regelung und Navigation**

* **Regler-Entwurf:** Kaskadierte PID-Struktur und Anti-Windup-Strategie *[Ref: Albarran Paper]*.
* **Nav2-Konfiguration:** Entwurf des Behavior Trees und Wahl des Controllers (Regulated Pure Pursuit).
* **Docking-Algorithmus:** Ablaufdiagramm des ArUco-Visual-Servoing.

---

5. Implementierung [≙ VDI 2206: Implementierung]

**5.1 Hardwareaufbau und elektrische Inbetriebnahme**

* Verdrahtung der Sensoren (Lidar, Encoder, Kamera).
* Aufbau der Spannungsversorgung (Power-Management RPi/Motoren).

**5.2 Firmware-Entwicklung auf dem ESP32**

* **Kinematik & Regelung:** Implementierung der `DiffDrive`-Klasse und des PID-Reglers *[Ref: Code Woche 1 & 3]*.
* **Echtzeit-Tasking:** Umsetzung der Dual-Core-Architektur (Core 0 vs. Core 1) *[Ref: Yordanov Paper]*.
* **Schnittstellen-Treiber:** Interrupt-basiertes Encoder-Auslesen und PWM-Erzeugung (20 kHz).

**5.3 ROS 2 Systemintegration und Treiber**

* **URDF-Modellierung:** Definition der TF-Kette (`base_link`  `laser`  `camera`).
* **micro-ROS Agent:** Einrichtung des Docker-Containers und der Seriellen Bridge.
* **Zeit-Synchronisation:** Implementierung des Time-Sync-Handshakes *[Ref: Abaza Paper]*.

**5.4 Kalibrierung und Mapping (SLAM)**

* **Odometrie-Kalibrierung:** Durchführung des UMBmark-Tests zur Korrektur von Spurbreite und Raddurchmesser *[Ref: DeGiorgi Paper]*. <-- *WICHTIG für Note!*
* **SLAM-Konfiguration:** Parametrierung der `slam_toolbox` und Erstellung der Umgebungskarte.

**5.5 Navigation und Applikationslogik**

* **Nav2-Setup:** Konfiguration des *Regulated Pure Pursuit* Controllers für den Pi 5.
* **Docking-Implementierung:** Entwicklung des Python-Nodes für ArUco-basiertes Visual Servoing *[Ref: MDPI Docking Paper]*. <-- *Dein Highlight aus Woche 4!*

**5.6 Systemtest und Validierung**

* Integrationstests: Zusammenspiel von Navigation, Hindernisvermeidung und Docking.

---

6. Validierung und Testergebnisse [≙ VDI 2206: Verifikation & Validierung]

**6.1 Testkonzept und Versuchsaufbau**

* Definition der Testumgebung (Test-Parcours, Bodenbelag, Lichtverhältnisse für Kamera).
* Messmittel (Maßband, `rqt_plot`, CPU-Monitor `htop`).

**6.2 Verifikation der Subsysteme (Low-Level)**

* **Regelgüte:** Auswertung der Sprungantworten des PID-Reglers (Soll vs. Ist Geschwindigkeit) *[Beweis für Albarran-Paper]*.
* **Odometrie-Genauigkeit:** Ergebnisse des UMBmark-Tests (Abweichung vor vs. nach Kalibrierung) *[Beweis für DeGiorgi-Paper]*.
* **Echtzeitfähigkeit:** Messung von Jitter und Latenz der micro-ROS Kommunikation (Vergleich: QoS Best Effort vs. Reliable) *[Beweis für Abaza/Yordanov]*.

**6.3 Validierung der Navigation (High-Level)**

* **Kartierungsqualität:** Vergleich der SLAM-Karte mit dem realen Grundriss (Metrische Genauigkeit der Wände).
* **Navigationsgenauigkeit:** Wiederholgenauigkeit beim Anfahren von Zielpunkten (Abweichung in ).
* **Dynamische Hindernisvermeidung:** Reaktionszeit und Pfadplanung bei plötzlich auftretenden Hindernissen.

**6.4 Validierung des Docking-Systems**

* **Erfolgsquote:** Wie oft klappt das Andocken bei 10 Versuchen?
* **Präzision:** Messung des lateralen Versatzes an der Ladestation (mm-Bereich). *<-- Das ist dein Highlight aus Woche 4!*

**6.5 Ressourcenverbrauch und Systemlast**

* CPU- und RAM-Auslastung auf dem Raspberry Pi 5 und ESP32 (Nachweis der Effizienz der Architektur).

**6.6 Diskussion der Ergebnisse und Soll-Ist-Vergleich**

* Bewertung der Ergebnisse gegenüber dem Lastenheft (Kapitel 3).
* Analyse von Fehlerquellen (z. B. Radschlupf auf Teppich, Lichtreflexionen bei ArUco).

---

7. Fazit und Ausblick

**7.1 Zusammenfassung der Ergebnisse**

* Kurzer Rückblick auf die Zielsetzung (aus Kap. 1) und den Lösungsweg.
* Hervorhebung der **Kern-Ergebnisse**:
* Erfolgreiche Integration der Dual-Core-Architektur (Echtzeitfähigkeit).
* Nachweis der Navigationsgenauigkeit ( X cm) und Docking-Zuverlässigkeit.
* Einhaltung des Kostenrahmens (Low-Cost vs. Industrie-Standard).



**7.2 Kritische Würdigung und Limitationen**

* **Technisch:** Wo stößt das System an Grenzen? (z. B. WLAN-Abdeckung in großen Hallen, Rechenleistung bei 3D-SLAM, Schlupf auf glatten Böden).
* **Methodisch (Reflexion VDI 2206):** Eignung des V-Modells für cyber-physische Systeme mit hohem Software-Anteil (Vorteile der Struktur vs. Nachteile bei Iterationen).
* **Wirtschaftlich:** Kosten-Nutzen-Analyse (Eigenbau vs. Kauf eines MiR100/TurtleBot).

**7.3 Ausblick und Weiterentwicklung**

* **Hardware-Optimierung:** Entwicklung einer eigenen Platine (PCB) statt fliegender Verdrahtung, Gehäuse-Design (IP-Schutzklasse).
* **Software-Erweiterung:**
* Integration in **Open-RMF** (Flottenmanagement) *[Das ist der Fachbegriff für "Flottenmanagement" in ROS 2]*.
* Web-Interface zur Steuerung ohne Terminal.


* **Sicherheit und Zertifizierung:** Notwendige Schritte zur CE-Konformität und Beachtung der **ISO 3691-4** (Sicherheitsanforderungen für fahrerlose Flurförderzeuge).

---

Literaturverzeichnis
Anhang (Glossar, Anforderungsliste, ROS 2 Parameter-YAML, Datenblätter, Rohdaten)

---

### Zuordnung: VDI 2206 → Kapitel → Ergebnis

| VDI 2206-Phase              | Kapitel        | Kernergebnis                                      |
|-----------------------------|----------------|---------------------------------------------------|
| Anforderungserhebung        | Kap. 3         | Lastenheft mit MUSS/SOLL/KANN-Kriterien           |
| Systemarchitektur & Entwurf | Kap. 4         | Systemblockbild, Node-Graph, Schnittstellenmatrix |
| Implementierung             | Kap. 5         | Lauffähiger Prototyp                              |
| Systemintegration           | Kap. 5.6 + 6.2 | Integrationstests, Einzelfunktionsnachweise       |
| Verifikation & Validierung  | Kap. 6.3       | SOLL-IST-Vergleich gegen Anforderungsliste        |

### Seitenproportionierung (60–80 Seiten)

| Kapitel                 | Richtwert | Begründung                                       |
|-------------------------|-----------|--------------------------------------------------|
| 1 – Einleitung          | 5–8 S.    | Problemraum abstecken, Methodik einordnen        |
| 2 – Grundlagen          | 15–20 S.  | Vier Themenfelder theoretisch fundieren          |
| 3 – Anforderungsanalyse | 5–8 S.    | Lastenheft als Referenz für Kap. 6               |
| 4 – Konzept & Entwurf   | 10–15 S.  | Architektur- und Auswahlentscheidungen begründen |
| 5 – Implementierung     | 10–15 S.  | Firmware, Software, Integration dokumentieren    |
| 6 – Validierung         | 8–12 S.   | Messdaten, Statistik, SOLL-IST                   |
| 7 – Fazit & Ausblick    | 3–5 S.    | Ergebnisse verdichten, offene Punkte benennen    |

---

## Ergebnis 2: Literaturstrategie (2023–2026)

Jedes der vier Themenfelder enthält: (1) die **Masterquelle** — ein Survey oder kanonisches Referenzwerk als Einstieg, (2) **Satellitenquellen** — spezifische Arbeiten nach Relevanz geordnet, und (3) **datenbankspezifische Suchstrings**.

---

### Themenfeld 1: SLAM und Navigation mit ROS 2

Der Nav2-Stack bildet die zentrale Software-Komponente der Arbeit. Die Literatur stützt sich auf einen Survey der Nav2-Maintainer selbst — die mit Abstand wichtigste Einzelquelle für die gesamte Arbeit.

**Masterquelle:**

Macenski, S., Moore, T., Lu, D.V., Merzlyakov, A., Ferguson, M. (2023). *From the Desks of ROS Maintainers: A Survey of Modern & Capable Mobile Robotics Algorithms in the Robot Operating System 2.* Robotics and Autonomous Systems, 168, 104493.
→ Behandelt sämtliche Nav2-Komponenten: SLAM Toolbox, AMCL, NavFn, Smac Planner, DWB, RPP, MPPI, Costmaps und Behavior Trees. Enthält Benchmarks und Maintainer-Empfehlungen.

**Satellitenquellen (nach Lesepriorität geordnet):**

| Nr. | Autoren / Jahr                 | Titel                                                                                                  | Venue                         | Relevanz                                                                                   |
|-----|--------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------|--------------------------------------------------------------------------------------------|
| 1   | Macenski, Foote et al. (2022)  | Robot Operating System 2: Design, Architecture, and Uses in the Wild                                   | Science Robotics 7(66)        | Kanonische ROS 2-Architekturpublikation; DDS, QoS, Lifecycle                               |
| 2   | Macenski & Jambrecic (2021)    | SLAM Toolbox: SLAM for the Dynamic World                                                               | JOSS 6(61), 2783              | Primärreferenz für SLAM Toolbox — der Standard-2D-SLAM in Nav2                             |
| 3   | Hess, Kohler et al. (2016)     | Real-Time Loop Closure in 2D LiDAR SLAM                                                                | IEEE ICRA                     | Google-Cartographer-Originalpaper — Vergleichsbasis                                        |
| 4   | MDPI Electronics (2025)        | From Simulation to Reality: Comparative Performance Analysis of SLAM Toolbox and Cartographer in ROS 2 | Electronics 14(24), 4822      | Direkter Vergleich SLAM Toolbox vs. Cartographer auf Diff-Drive-Roboter mit 2D-LiDAR + IMU |
| 5   | Macenski, Martín et al. (2020) | The Marathon 2: A Navigation System                                                                    | IEEE/RSJ IROS                 | Grundlegendes Nav2-Architekturpaper                                                        |
| 6   | Fox, Burgard, Thrun (1997)     | The Dynamic Window Approach to Collision Avoidance                                                     | IEEE RAM 4(1)                 | Original-DWA-Algorithmus — Basis des DWB-Controllers                                       |
| 7   | Macenski, Singh et al. (2023)  | Regulated Pure Pursuit for Robot Path Tracking                                                         | Autonomous Robots             | RPP-Controller — Alternative zu DWB für enge Räume                                         |
| 8   | López (2023)                   | Mobile Robot Navigation in ROS 2: Motion Controllers Comparison                                        | Nobleo Technology White Paper | Praktischer Benchmark: DWB vs. TEB vs. RPP auf realen Robotern                             |

**Zentrale Beobachtung:** Es existiert noch keine peer-reviewte Publikation, die SLAM oder Nav2 spezifisch auf dem **Raspberry Pi 5** benchmarkt. Die Arbeit kann hier einen genuinen Beitrag leisten.

---

### Themenfeld 2: Sensorfusion für Indoor-Mobilroboter

Die Arbeit fusioniert 2D-LiDAR + IMU + Rad-Encoder über einen EKF (`robot_localization`-Paket), ergänzt um ArUco-Marker für das Andocken. Eine Veröffentlichung — Abaza (2025) — verwendet den **exakt gleichen Hardware-/Software-Stack** (ESP32 + Raspberry Pi + ROS 2 + `diff_drive` + `robot_localization` EKF).

**Masterquelle:**

Moore, T. & Stouch, D. (2014). *A Generalized Extended Kalman Filter Implementation for the Robot Operating System.* Proc. IAS-13, Springer AISC 302, S. 335–348.
→ Grundlagenpaper für das `robot_localization`-Paket (441+ Zitierungen). Beschreibt die 15-Zustands-EKF-Implementierung, die in der Arbeit direkt zum Einsatz kommt.

**Satellitenquellen:**

| Nr. | Autoren / Jahr                  | Titel                                                                             | Venue                       | Relevanz                                                                                        |
|-----|---------------------------------|-----------------------------------------------------------------------------------|-----------------------------|-------------------------------------------------------------------------------------------------|
| 1   | Abaza, B.F. (2025)              | AI-Driven Dynamic Covariance for ROS 2 Mobile Robot Localization                  | Sensors 25(10), 3026        | **Exakte Stack-Übereinstimmung:** ESP32 + RPi + ROS 2 + diff_drive + robot_localization EKF     |
| 2   | arXiv 2404.07644 (2024)         | 2DLIW-SLAM: 2D LiDAR-Inertial-Wheel Odometry with Real-Time Loop Closure          | arXiv-Preprint              | Eng gekoppelter 2D-LiDAR + IMU + Rad-Encoder SLAM für Indoor-Roboter                            |
| 3   | Yang, L. et al. (2025)          | LiDAR-Inertial SLAM Integrated with Visual QR Codes for Indoor Mobile Robots      | Scientific Reports (Nature) | Brücke zwischen LiDAR-IMU-Fusion und Fiducial-Markern — direkt relevant für ArUco-Ansatz        |
| 4   | Sensors (2025)                  | Regression-Based Docking System for AMRs Using Monocular Camera and ArUco Markers | Sensors 25(12), 3742        | ArUco-Andocken: mittlere Distanzabweichung $1{,}18\,\mathrm{cm}$, Orientierungsfehler $3{,}11°$ |
| 5   | Pulloquinga, J.L. et al. (2024) | Experimental Analysis of Pose Estimation Based on ArUco Markers                   | Springer LNME (ICIENG)      | Systematische ArUco-Genauigkeitsanalyse gegen OptiTrack-Ground-Truth                            |
| 6   | Sensors (2024)                  | Multi-Sensor Fusion Using Fuzzification-Assisted IESKF                            | Sensors 24(23), 7619        | Rad-Inertial-Visuelle Odometrie zur Driftkompensation bei Diff-Drive Indoor-Robotern            |

---

### Themenfeld 3: micro-ROS und ESP32-Integration

Die akademische Literatur zu micro-ROS ist noch jung, wächst aber schnell. Das Buchkapitel von Belsare et al. (2023) ist die offiziell empfohlene Zitationsreferenz des micro-ROS-Projekts.

**Masterquelle:**

Belsare, K. et al. (2023). *Micro-ROS.* In: Koubaa, A. (Hrsg.) Robot Operating System (ROS): The Complete Reference (Band 7), Springer, S. 3–55.
→ Verfasst vom Bosch/eProsima/PIAP-Team, das micro-ROS entwickelt hat. Behandelt die gesamte Architektur: `rclc`, Micro XRCE-DDS, rclc Executor, Lifecycle-Management, unterstützte RTOSe (FreeRTOS, Zephyr, NuttX) und unterstützte MCUs einschließlich ESP32.

**Satellitenquellen:**

| Nr. | Autoren / Jahr                       | Titel                                                                                    | Venue                               | Relevanz                                                                                  |
|-----|--------------------------------------|------------------------------------------------------------------------------------------|-------------------------------------|-------------------------------------------------------------------------------------------|
| 1   | Staschulat, Lütkebohle, Lange (2020) | The rclc Executor: Domain-Specific Deterministic Scheduling for ROS on Microcontrollers  | EMSOFT 2020 (IEEE)                  | Einführung des deterministischen Callback-Schedulers in micro-ROS                         |
| 2   | Wang, Liu et al. (2024)              | Improving Real-Time Performance of Micro-ROS with Priority-Driven Chain-Aware Scheduling | Electronics 13(9), 1658             | Identifiziert und behebt Scheduling-Schwächen; getestet auf **ESP32-Hardware**            |
| 3   | Albarran, Nicolodi et al. (2023)     | Differential-Drive Mobile Robot Controller with ROS 2 Support                            | Revista Elektron 7(2), S. 53–60     | **Direkt relevant:** ESP32-WROOM-32E + micro-ROS für Diff-Drive; Motorsteuerung + Encoder |
| 4   | Yordanov, Schäfer et al. (2025)      | Integrated Wheel Sensor Communication using ESP32                                        | arXiv 2509.04061 (RWTH Aachen)      | **Dual-Core-ESP32-Partitionierung:** Core 0 → WiFi, Core 1 → micro-ROS/Datenerfassung     |
| 5   | Casini, D. et al. (2025)             | A Survey of Real-Time Support, Analysis, and Advancements in ROS 2                       | arXiv 2601.10722                    | Umfassender Survey: ROS 2 Echtzeit, Executors, DDS, micro-ROS                             |
| 6   | Nguyen, P. (2022)                    | Micro-ROS for Mobile Robotics Systems                                                    | M.Sc.-Thesis, Mälardalen University | Testet micro-ROS auf STM32, ESP32, Arduino Due; Latenz-/Jitter-Messungen                  |

**Offizielle Dokumentation (als Software-Dokumentation zu zitieren):**

- micro-ROS-Projektseite: https://micro.ros.org (Architektur, Tutorials, ESP32-Port)
- Micro XRCE-DDS: eProsima GitHub + OMG DDS-XRCE-Spezifikation v1.0
- `micro_ros_espidf_component`: offizielle ESP-IDF-Integrationsrepository
- micro-ROS vs. rosserial: https://micro.ros.org/docs/concepts/middleware/rosserial/
- `linorobot/linorobot2_hardware`: ausgereifteste Open-Source-Diff-Drive-Firmware mit micro-ROS auf ESP32

---

### Themenfeld 4: Kinematik und Regelung des Differentialantriebs

Dieses Themenfeld besitzt die tiefsten Lehrbuch-Wurzeln. Die Masterquelle ist das universell zitierte Lehrbuch von Siegwart & Nourbakhsh, ergänzt durch die klassischen Borenstein-Odometriekalibrierungsmethoden.

**Masterquelle:**

Siegwart, R., Nourbakhsh, I.R. & Scaramuzza, D. (2011). *Introduction to Autonomous Mobile Robots*, 2. Aufl. MIT Press.
→ Kapitel 3 (Lokomotion/Kinematik) liefert das vollständige Vorwärts-/Inverskinematik-Modell des Differentialantriebs. Kapitel 5 behandelt Odometrie und Wahrnehmung. Meistzitiertes Lehrbuch im AMR-Bereich.

**Grundlegende Referenzwerke (Pflicht-Zitationen):**

| Nr. | Autoren / Jahr                          | Titel                                                          | Venue                   | Relevanz                                                           |
|-----|-----------------------------------------|----------------------------------------------------------------|-------------------------|--------------------------------------------------------------------|
| T1  | Siegwart, Nourbakhsh, Scaramuzza (2011) | Introduction to Autonomous Mobile Robots, 2. Aufl.             | MIT Press               | **Masterquelle** — Herleitung der Diff-Drive-Kinematik             |
| T2  | Siciliano, Sciavicco et al. (2009)      | Robotics: Modelling, Planning and Control                      | Springer                | Regelungstheoretische Grundlagen, Lyapunov-Stabilität              |
| T3  | Corke, P. (2023)                        | Robotics, Vision and Control, 3. Aufl.                         | Springer                | Aktualisierte Algorithmen in MATLAB/Python                         |
| T4  | Thrun, Burgard, Fox (2005)              | Probabilistic Robotics                                         | MIT Press               | Odometrie-Fehlermodelle, probabilistische Bewegungsmodelle, EKF    |
| O1  | Borenstein, Everett, Feng (1996)        | Where Am I? — Sensors and Methods for Mobile Robot Positioning | U. Michigan Tech Report | Definition systematischer vs. nicht-systematischer Odometriefehler |
| O2  | Borenstein & Feng (1996)                | UMBmark: A Method for Measuring Dead-Reckoning Errors          | IEEE T-RA               | Standard-Odometrie-Kalibrierungsbenchmark                          |

**Aktuelle Satellitenquellen:**

| Nr. | Autoren / Jahr                         | Titel                                                                          | Venue             | Relevanz                                                       |
|-----|----------------------------------------|--------------------------------------------------------------------------------|-------------------|----------------------------------------------------------------|
| 1   | IEEE 10716137 (2024)                   | Fine Tuning Mobility: PID Driven Velocity Control for Differential Drive Robot | IEEE Conference   | PID + EKF zur Encoder-Rauschbehandlung                         |
| 2   | Naragani, Gariya, Singhal (2024)       | Unified Dual-Wheel PID Control for Differential Drive Robot                    | IEEE Conference   | Neuartiger UDW-PID mit getrennten Fehlerfunktionen pro Rad     |
| 3   | De Giorgi, De Palma, Parlangeli (2024) | Online Odometry Calibration in Low Traction Conditions with Slippage           | Robotics 13(1), 7 | Online-Kalibrierung mit Encoder + Gyro + IMU; Schlupferkennung |

**ROS 2 `ros2_control`-Dokumentation:**

- `diff_drive_controller` — Humble-Dokumentation auf control.ros.org (`wheel_separation`, `wheel_radius`, Geschwindigkeitsgrenzen, Odometrie-Kovarianz)
- DiffBot-Beispiel (`ros2_control_demos` example_2) — Referenz-URDF und Hardware-Interface-Implementierung

---

## Suchstrings nach Datenbank

### Google Scholar (Datumsfilter 2023–2026)

```
"SLAM" AND "ROS 2" AND "indoor"
"Nav2" AND "autonomous mobile robot"
"SLAM Toolbox" AND "2D LiDAR"
"sensor fusion" "mobile robot" "ROS 2" localization
"robot_localization" "ROS 2" EKF
"ArUco marker" docking robot pose estimation
"micro-ROS" "ESP32"
"micro-ROS" "FreeRTOS"
"embedded" "ROS 2" "real-time control"
"differential drive" "kinematics" "PID"
"odometry" "encoder" "mobile robot" differential drive
"UMBmark" odometry calibration
"ros2_control" "differential drive"
```

### IEEE Xplore (Feld: „All Metadata")

```
("SLAM") AND ("ROS 2")                                   → Filter: 2023–2026
("Nav2") AND ("autonomous mobile robot")
("indoor navigation") AND ("differential drive")
("sensor fusion" AND "mobile robot" AND "ROS 2")
("Extended Kalman Filter" AND "differential drive" AND "odometry")
("micro-ROS" AND "ESP32")
("embedded" AND "ROS 2" AND "real-time control")
("PID control" AND "trajectory tracking" AND "differential drive")
("ArUco" AND "docking" AND "mobile robot")
```

### arXiv (Felder: `ti:` für Titel, `abs:` für Abstract, `cat:cs.RO` für Robotik)

```
ti:"SLAM" AND abs:"ROS 2" AND cat:cs.RO
abs:"Nav2" AND abs:"autonomous mobile robot"
abs:"micro-ROS" AND abs:"ESP32"
abs:"micro-ROS" AND abs:"FreeRTOS"
ti:"sensor fusion" AND abs:"mobile robot" AND abs:"indoor"
ti:"differential drive" AND abs:"kinematics"
abs:"robot_localization" AND abs:"EKF"
```

### Springer (link.springer.com)

```
"sensor fusion" "mobile robot" "indoor" localization     → Filter: 2023–2026
"ROS 2" "mobile robot" navigation survey
"differential drive" kinematics odometry "mobile robot"
"ArUco marker" "pose estimation" robot
```

---

## Priorisierte Lesereihenfolge

Die folgende Sequenz baut Verständnis vom allgemeinen ROS 2-Ökosystem bis zu implementierungsspezifischen Quellen auf. Fett markierte Einträge sind die vier Masterquellen.

### Woche 1 — Architektonische Grundlagen

1. **Macenski et al. (2022) — ROS 2-Architektur** (Science Robotics) ★
2. **Macenski et al. (2023) — Nav2-Survey** (Robotics and Autonomous Systems) ★
3. **Belsare et al. (2023) — micro-ROS** (Springer-Buchkapitel) ★
4. **Siegwart, Nourbakhsh, Scaramuzza (2011) — Mobilroboter-Kinematik** (MIT Press) ★

### Woche 2 — Kernalgorithmen

5. Macenski & Jambrecic (2021) — SLAM Toolbox (JOSS)
6. Hess et al. (2016) — Cartographer (ICRA)
7. **Moore & Stouch (2014) — `robot_localization` EKF** (Springer IAS-13) ★
8. Fox, Burgard, Thrun (1997) — DWA (IEEE RAM)
9. Borenstein et al. (1996) — „Where Am I?" + UMBmark

### Woche 3 — Hardware-spezifisch und angewandt

10. Abaza (2025) — ESP32 + RPi + ROS 2 + EKF (Sensors) — **exakte Stack-Übereinstimmung**
11. Albarran et al. (2023) — ESP32-Diff-Drive mit micro-ROS (Elektron)
12. Yordanov et al. (2025) — Dual-Core-ESP32-Partitionierung (arXiv, RWTH Aachen)
13. MDPI Electronics (2025) — SLAM Toolbox vs. Cartographer-Vergleich
14. Staschulat et al. (2020) — rclc Executor (EMSOFT)

### Woche 4 — Spezialisierung

15. ArUco-Docking-Paper (Sensors 2025) — monokulares Kamera-Andocksystem
16. 2DLIW-SLAM (arXiv 2024) — 2D-LiDAR + IMU + Rad, eng gekoppelt
17. Naragani et al. (2024) — Unified Dual-Wheel PID
18. De Giorgi et al. (2024) — Online-Odometriekalibrierung mit Schlupf
19. Nguyen (2022) — M.Sc.-Thesis zu micro-ROS für Mobilrobotik (Mälardalen University)

---

## Lücken und Beitragspotenzial der Arbeit

Drei Bereiche, in denen die Arbeit genuines angewandtes Wissen beitragen kann:

1. **Raspberry Pi 5 als SLAM-/Nav2-Plattform:** Es existiert keine peer-reviewte Publikation, die SLAM- oder Nav2-Performance auf dem Pi 5 (Release Oktober 2023) quantitativ benchmarkt. Messdaten zur Rechenzeit, CPU-/RAM-Auslastung und Kartenqualität füllen eine nachweisbare Lücke.

2. **ESP32-S3 mit micro-ROS:** Die akademische Literatur referenziert fast ausschließlich den ESP32-WROOM oder STM32. Eine Dokumentation der Dual-Core-FreeRTOS-Taskpartitionierung auf dem ESP32-S3 (Core 0: WiFi/micro-ROS-Transport, Core 1: PID-Regelung/Sensorerfassung) wäre ein konkreter Beitrag.

3. **Gesamtsystem-Kombination:** Die Verbindung von micro-ROS auf ESP32-S3 als Echtzeit-Motorcontroller mit Nav2 auf Raspberry Pi 5 für KLT-Intralogistik besitzt kein direktes Vorbild in der Literatur. Die nächste Übereinstimmung ist Abaza (2025), jedoch ohne KLT-Logistikkontext und ohne Nav2-Integration.

---

## Hinweise zur Quellenqualität und Zitierpraxis

- **Tier-1-Quellen:** IEEE Xplore-Konferenzbeiträge, Springer-Journale, Science Robotics.
- **MDPI-Journale** (Sensors, Electronics): Open-Access und peer-reviewed, aber mit variablem Impact-Faktor. Zitierungszahlen vor Übernahme als Hauptquelle prüfen.
- **arXiv-Preprints** von etablierten Gruppen (Bosch, RWTH Aachen, Scuola Superiore Sant'Anna): In der Regel zuverlässig, aber als nicht-peer-reviewed kennzeichnen.
- **ROS 2- und micro-ROS-Dokumentation:** Als Software-Dokumentation mit Zugriffsdatum zitieren.
- **GitHub-Repositories** (`linorobot2_hardware`, `micro_ros_espidf_component`): Graue Literatur, aber für die Reproduzierbarkeit der Implementierung essenziell. Als technische Referenzen zitieren.
- **Borenstein „Where Am I?":** Formell ein University-Tech-Report, mit 4.700+ Zitierungen aber im Fachgebiet universell akzeptiert.
- **KI-Einsatz dokumentieren:** Sämtliche Prompts und KI-generierte Textpassagen gehören ins Hilfsmittelverzeichnis (WBH-Vorgabe).
