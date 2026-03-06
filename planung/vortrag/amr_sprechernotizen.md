# Sprechernotizen: Architektur und Datenfluss eines KI-gestützten AMR

Diese Notizen dienen dir als roter Faden während der Präsentation. Sie verknüpfen die Abbildungen der Folien mit den zugrundeliegenden technischen Spezifikationen und Messwerten.

---

## Folie 1: Architektur und Datenfluss eines KI-gestützten AMR

* **Begrüßung:** Heiße das Publikum willkommen und nenne das Thema.
* **Fokus:** Betone, dass wir heute nicht nur Code betrachten, sondern den kompletten Datenfluss vom physischen Sensorwert bis zur strategischen Cloud-Entscheidung verfolgen.
* **Ziel:** Die Präsentation zeigt auf, wie komplexe Logistikaufgaben mit einer stark partitionierten Hardware-Architektur gelöst werden können.

---

## Folie 2: Problemstellung und Lösungsmodell

* **Ausgangslage:** Industrielle AMR kosten oft über 25.000 EUR und sind für einfache Aufgaben überdimensioniert.
* **Unser Modell:** Wir realisieren einen Prototypen für rund 513 EUR Materialkosten.
* **Die Herausforderung:** Diese Kostenreduktion erfordert eine strikte Systemtrennung. Die harte Echtzeit für die Motorregelung und die rechenintensive SLAM-Navigation dürfen sich nicht gegenseitig blockieren.
* **Überleitung:** Das beiliegende Diagramm zeigt genau diese Aufgabentrennung.

---

## Folie 3: Das Gesamtsystem im Überblick

* **Bildführung:** Führe das Publikum von links nach rechts durch das Diagramm.
* **Kernelement:** Erkläre den Datenfluss: Sensorik $\rightarrow$ Bildverarbeitung (Hailo) $\rightarrow$ Strategie (Cloud AI) $\rightarrow$ Handlung (ESP32/Servos).
* **Abgrenzung:** Mach deutlich, dass zeitkritische Notfallreaktionen (wie ein Stopp vor der Wand) lokal auf dem Raspberry Pi 5 bleiben, während semantische Entscheidungen an die Cloud gehen.

---

## Folie 4: 1. Sensorik: Die Eingabe-Ebene

* **RPLIDAR A1:** Dieser Sensor tastet die Umgebung in 360° ab und liefert Scandaten bei 7,6 Hz bis zu 12 m Reichweite. Dies ist die Basis für das SLAM.
* **IMX296 Kamera:** Liefert die optischen Daten für das ArUco-Docking und die YOLOv8-Erkennung. Sie ist über eine v4l2loopback-Bridge angebunden.
* **Encoder:** Die Motoren besitzen Hall-Encoder, die im Quadraturmodus rund 748 Ticks pro Radumdrehung auflösen.
* **Zwischenfazit:** Hier entsteht die reine Rohdaten-Grundlage ohne jegliche Interpretation.

---

## Folie 5: 2. Lokale Verarbeitung: RPi 5 und Hailo

* **ROS 2 auf dem Pi 5:** Der Raspberry Pi arbeitet als High-Level-Navigationsrechner und lässt ROS 2 Humble containerisiert über Docker laufen.
* **Nav2 und SLAM:** Hier entsteht die 5 cm genaue Occupancy Grid Map.
* **Hailo-8L:** Erkläre, warum die NPU zwingend ist. Die Objekterkennung (YOLOv8) würde die CPU des Pi 5 blockieren. Der PCIe-Beschleuniger verarbeitet den Videostream der IMX296 Kamera latenzfrei.

---

## Folie 6: 3. Strategische Entscheidung: Cloud AI

* **Die Schnittstelle:** Das System sendet vorverarbeitete JSON-Pakete an die Gemini API oder Claude AI.
* **Beispiel für die Anwendung:** Der LiDAR meldet ein Hindernis (lokale Ebene stoppt den Roboter). Die Kamera und der Hailo-Chip erkennen das Hindernis als "Mensch". Die Cloud-KI entscheidet nun strategisch: Der Roboter nutzt den Speaker, um eine Warnung auszugeben, anstatt sofort eine neue Route zu planen.
* **Datenreduktion:** Betone, dass keine rohen Videostreams in die Cloud gesendet werden, sondern nur die semantischen Metadaten.

---

## Folie 7: 4. Aktoren: Die physische Ausführung

* **ESP32-S3:** Core 1 führt die PID-Regelschleife deterministisch bei 50 Hz aus.
* **Kommunikation:** Core 0 verarbeitet parallel die micro-ROS-Kommunikation über UART bei 115200 Baud. Das verhindert Latenzen, die bei einer WLAN-Verbindung auftreten würden.
* **Motortreiber:** Der Cytron MDD3A steuert die Motoren über ein 20 kHz PWM-Signal an.
* **Zusatz-Aktoren:** Die Servos richten die Kamera aus, der Speaker gibt die generierten Handlungsanweisungen akustisch aus.

---

## Folie 8: Berechnungsgrundlage der Aktorik

* **Herleitung:** Wir berechnen die individuellen Radgeschwindigkeiten über die Inverskinematik.
* **Parameter:** Nenne die gemessenen Werte. Der kalibrierte Raddurchmesser beträgt 65,67 mm. Die gemessene Spurbreite liegt bei 178 mm.
* **Bedeutung:** Ohne diese exakten, empirisch ermittelten Werte produziert der Nav2-Stack fehlerhafte Befehle, da Translation und Rotation physikalisch falsch auf die Räder abgebildet werden.

---

## Folie 9: Validierung und Limitierungen

* **Evidenz:** Die systematische UMBmark-Kalibrierung hat die systematischen Odometriefehler um den Faktor 10 bis 20 reduziert. Dies belegt, dass präzise Mechanik-Messungen essenziell sind.
* **Netzwerk-Flaschenhals:** Erkläre die micro-ROS Limitierungen. Die MTU ist auf 512 Bytes begrenzt. Wir nutzen Reliable QoS, um Fragmentierung bis 2048 Bytes zu ermöglichen, was für die großen Odometrie-Nachrichten zwingend erforderlich ist.
* **Ausblick:** Schließe mit dem Hinweis, dass künftige Iterationen eine Sensorfusion (IMU + Encoder) via EKF integrieren sollten, um den Schlupf auf unebenem Terrain besser zu kompensieren.

---
