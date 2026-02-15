# Abschlussbericht: Autonomer Mobiler Roboter fuer die Intralogistik

![AMR-Seitenansicht](hardware/media/amr-seitenansicht.png)

## 1. Einleitung

Die fortschreitende Flexibilisierung industrieller Fertigungsprozesse im Kontext von Industrie 4.0 verlangt neuartige Loesungen fuer die innerbetriebliche Logistik. Autonome mobile Roboter (AMR) bieten einen vielversprechenden Ansatz, da sie sich ohne externe Infrastruktur wie Leitlinien oder Reflektoren zwischen Orten bewegen koennen. Die vorliegende Bachelorarbeit entwickelt einen kostenguenstigen AMR-Prototypen mit Differentialantrieb fuer den Transport von Kleinladungstraegern (KLT) in der Intralogistik. Das System basiert auf Open-Source-Komponenten: Ein ESP32-Mikrocontroller uebernimmt die Echtzeit-Motorsteuerung, waehrend ein Raspberry Pi 5 die autonome Navigation mittels ROS 2 realisiert. Die Arbeit adressiert drei Forschungsfragen: Wie eine echtzeitfaehige Antriebsregelung auf einem Dual-Core-Mikrocontroller realisiert werden kann (FF1), welchen Einfluss eine systematische Odometrie-Kalibrierung auf die Navigationsgenauigkeit besitzt (FF2) und ob ein monokulares Kamerasystem mit ArUco-Markern hinreichend praezise ist, um einen Ladekontakt mit Zentimetergenauigkeit autonom zu treffen (FF3).

## 2. Projektorganisation

Die Arbeit wurde als Einzelprojekt im Rahmen einer Bachelorarbeit durchgefuehrt und durch die betreuende Hochschule begleitet. Der Entwicklungszeitraum erstreckte sich ueber vier Monate von der Anforderungsanalyse bis zur Systemvalidierung. Als Werkzeuge kamen PlatformIO fuer die Firmware-Entwicklung, ROS 2 Humble mit Docker fuer die Navigation, Git zur Versionskontrolle und Python fuer Validierungsskripte zum Einsatz. Die Entwicklung folgte einem iterativen Ansatz mit fruehen Hardware-Tests, wobei experimentelle Validierung anhand quantitativer Akzeptanzkriterien die klassischen Unit-Tests ersetzte.

## 3. Vorgehen beim Projekt

Das methodische Vorgehen orientierte sich am V-Modell nach VDI 2206, das den Entwicklungsprozess in symmetrische Entwurfs- und Verifikationsphasen gliedert. Der linke Schenkel umfasste Anforderungsdefinition, Systementwurf und Detailentwurf. Die Anforderungsphase definierte funktionale Spezifikationen wie autonome Navigation, Hindernisvermeidung und praezises Docking sowie nichtfunktionale Anforderungen hinsichtlich Positionsgenauigkeit und Echtzeitfaehigkeit. Der Systementwurf zerlegte diese in eine Zwei-Rechner-Architektur: Der ESP32 steuert die Motoren und publiziert Odometrie, waehrend der Raspberry Pi SLAM-Kartierung und Pfadplanung uebernimmt. Die Verbindung ueber micro-ROS und UART als deterministische Kommunikationsschicht stellte sicher, dass die Echtzeit-Regelschleife nicht durch Netzwerklatenzen gestoert wird. An der Spitze des V erfolgte die Implementierung, der rechte Schenkel begann mit Integrationstests der Teilsysteme und schloss mit der Abnahmevalidierung aller Anforderungen.

## 4. Beschreibung der technischen Loesung

Der Roboter basiert auf einem Differentialantrieb mit zwei angetriebenen Raedern von 65,67 mm Durchmesser (kalibriert) bei 178 mm Spurbreite, ergaenzt durch ein frei drehbares Stuetzrad. Die JGA25-370-Getriebemotoren mit integrierten Hall-Encodern liefern durch Quadratur-Dekodierung etwa 748 Ticks pro Radumdrehung als Odometrie-Grundlage. Ein Cytron MDD3A-Motortreiber im Dual-PWM-Modus steuert beide Motoren separat an.

Als zentrale Recheneinheit agiert ein XIAO ESP32-S3 mit Dual-Core-Architektur: Core 1 fuehrt die PID-Regelschleife deterministisch bei 50 Hz aus, waehrend Core 0 die micro-ROS-Kommunikation mit 20 Hz Odometrie-Publikation betreibt. Die Synchronisation erfolgt ueber FreeRTOS-Mutex-geschuetzte Datenstrukturen. Die Anbindung an den Raspberry Pi 5 als Navigationsrechner nutzt UART bei 115200 Baud, um Latenzen einer WiFi-Verbindung zu vermeiden.

Die Sensorik umfasst einen RPLIDAR A1 (360-Grad-Scan, 12 m Reichweite) fuer SLAM sowie eine Sony IMX296 Global Shutter Kamera fuer ArUco-Marker-Erkennung beim Docking. Die Spannungsversorgung erfolgt mehrstufig ueber Buck-Converter (5 V fuer Pi) und direkte Akkuspeisung der Motoren.

![Roboter-Draufsicht mit Komponentenanordnung](hardware/media/amr-draufsicht.png)

## 5. Beschreibung der Softwareloesung

Die ESP32-Firmware partitioniert die Aufgaben auf zwei FreeRTOS-Tasks mit hardwarebasierter Entkopplung. Core 0 verarbeitet eingehende `/cmd_vel`-Befehle und publiziert Odometrie auf `/odom`, Core 1 fuehrt exklusiv die PID-Regelung mit Inverskinematik und Vorwaertskinematik aus. Drei Header-Only-Module (`robot_hal.hpp`, `pid_controller.hpp`, `diff_drive_kinematics.hpp`) kapseln Hardware-Abstraktion, Regelung und Kinematik.

Der Raspberry Pi 5 betreibt ROS 2 Humble containerisiert ueber Docker, da Debian Trixie keine native ROS2-Unterstuetzung bietet. Der Stack integriert SLAM Toolbox fuer Online-Kartierung mit 5 cm Aufloesung und den Nav2-Stack mit Regulated Pure Pursuit Controller bei 0,4 m/s Zielgeschwindigkeit. Ein dedizierter `odom_to_tf`-Node konvertiert Odometrie-Nachrichten in TF-Transformationen, da micro-ROS keine TF-Broadcasts unterstuetzt. Die zentrale Launch-Datei orchestriert alle Komponenten mit konfigurierbaren Argumenten fuer SLAM, Navigation und optionale Kameraintegration. Zwoelf Python-Validierungsskripte decken systematisch Encoder-Kalibrierung, PID-Sprungantwort, kinematische Verifikation sowie SLAM- und Navigationsvalidierung ab.

```
┌──────────────────────────────────────────────────────────┐
│                    Systemarchitektur                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  UART (115200)  ┌───────────────┐ │
│  │  XIAO ESP32-S3   │ <────────────> │ Raspberry Pi 5 │ │
│  │                  │  micro-ROS      │ (Docker/ROS2)  │ │
│  ├──────────────────┤                 ├───────────────┤ │
│  │ Core 0:          │                 │ micro-ROS     │ │
│  │  - /cmd_vel Sub  │                 │ SLAM Toolbox  │ │
│  │  - /odom Pub     │                 │ Nav2 Stack    │ │
│  │ Core 1:          │                 │ odom_to_tf    │ │
│  │  - PID 50 Hz     │                 │ RViz2         │ │
│  │  - Kinematics    │                 └───────────────┘ │
│  └──────────────────┘                        │          │
│         │                                    │          │
│         └──> Cytron MDD3A ──> Motoren   DDS Network    │
│                                              │          │
│                           RPLidar A1 ────────┘          │
│                           IMX296 Kamera (optional)      │
└──────────────────────────────────────────────────────────┘
```

## 6. Fazit

Die experimentelle Validierung bestaetigt die Beantwortung aller drei Forschungsfragen. Die Dual-Core-Architektur des ESP32 ermoeglicht eine echtzeitfaehige Motorregelung bei 50 Hz mit Jitter unter 2 ms trotz paralleler micro-ROS-Kommunikation (FF1). Die systematische UMBmark-Kalibrierung reduzierte die systematischen Odometrie-Fehler um Faktor 10 und bildete die Grundlage fuer die SLAM-Kartierung mit einem Absolute Trajectory Error von 0,16 m, deutlich unter dem Akzeptanzkriterium von 0,20 m (FF2). Das ArUco-basierte Docking erreichte eine Erfolgsquote von 80 Prozent mit 1,3 cm lateralem Versatz, wobei die Fehlversuche die Beleuchtungsempfindlichkeit des monokularen Systems offenbarten (FF3). Die Navigationsgenauigkeit betrug im Mittel 6,4 cm (xy) und 4,2 Grad (Gier) ueber zehn Testfahrten.

Das V-Modell nach VDI 2206 erwies sich als angemessener methodischer Rahmen, obgleich dessen Linearitaet iterative Softwareentwicklungszyklen erschwerte. Die technischen Grenzen liegen primaer in der fehlenden IMU-Fusion, der Schlupfempfindlichkeit der Rad-Odometrie auf rauem Untergrund sowie der Beleuchtungsabhaengigkeit des Docking-Systems. Der Prototyp kostet mit rund 513 Euro etwa ein Drittel eines TurtleBot 4, implementiert jedoch keine industriellen Merkmale wie redundante Sicherheitssensorik nach ISO 3691-4. Zukuenftige Arbeiten koennten Multi-Robot-Koordination, IMU-Sensor-Fusion und industrielle Haertung adressieren, um die Luecke zwischen Forschungsprototyp und Produktivsystem zu schliessen.
