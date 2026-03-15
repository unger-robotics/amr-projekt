---
title: "AMR Showcase: Edge-KI trifft Intralogistik"
subtitle: "Vom physischen Sensorwert zur semantischen Cloud-Entscheidung"
author: "Jan Unger"
date: "10. Maerz 2026"
theme: "metropolis"
---

## Das Ziel: Ein Low-Cost AMR fuer KLT-Transporte

**Wie laesst sich ein fahrerloses Transportsystem fuer Kleinladungstraeger kosteneffizient und echtzeitfaehig realisieren?**

* **Problem:** Industrielle Flotten kosten oft ueber $25.000$ EUR und sind fuer leichte Transporte ueberdimensioniert. Reine Software-Stacks auf Raspberry Pis scheitern haeufig an den harten Echtzeitanforderungen der Motorregelung.
* **Loesung:** Ein modularer ROS-2-Stack mit einer verteilten Hardware-Architektur entkoppelt die Motorik von der Kuentslichen Intelligenz.
* **Evidenz:** Das System arbeitet mit Hardwarekosten von rund $513$ EUR und haelt strenge Latenz- sowie Genauigkeitsvorgaben ein.

---

## Physischer Systemaufbau

Die Hardware-Basis bildet ein Differentialantrieb mit umfassender Sensor-Suite:

{width=35%}

* **Antrieb:** Zwei JGA25-370-Gleichstrommotoren mit integrierten Hall-Encodern ($748$ Ticks pro Umdrehung).
* **Sensorik:** RPLIDAR A1 ($12\,\mathrm{m}$ Reichweite), MPU6050-IMU und MH-B Kanten-Sensor.
* **Energieversorgung:** 3S1P-Li-Ion-Akkupack mit einem harten System-Cutoff bei $7{,}95\,\mathrm{V}$ zum Schutz vor Tiefenentladung.

---

## Die Systemarchitektur in drei Ebenen

Die Architektur trennt High-Level-Navigation strikt von der Low-Level-Motorik:

{width=45%}

* **Ebene A (Fahrkern & Sensorbasis):** Zwei ESP32-S3 uebernehmen die deterministische Steuerung und Datenerfassung bei $50\,\mathrm{Hz}$.
* **Ebene B (Leitstandsebene):** Ein Raspberry Pi 5 betreibt die Navigation (Nav2) und das webbasierte Dashboard.
* **Ebene C (Interaktion):** Beinhaltet die Sprachschnittstelle und die Cloud-Semantik ueber die Gemini API.

---

## Datenfluss und Kommunikation

Der Datenfluss erfolgt deterministisch ueber dedizierte Bus-Systeme:

{width=45%}

* **XRCE-DDS (micro-ROS):** Koppelt die Mikrocontroller ueber serielle UART-Verbindungen ($921\,600$ Baud) stabil an den ROS-2-Graphen an.
* **I2C & GPIO:** Binden lokale Peripherie (wie IMU und Encoder) direkt an die ESP32-S3 an.
* **MTU-Limit:** Datenpakete duerfen den Wert von $512$ Bytes nicht ueberschreiten, was die Fragmentierung groesserer Nachrichten wie der Odometrie erzwingt.

---

## Aktorik: Der Dual-Core Mikrocontroller

Die Motorregelung erfordert harte Echtzeit, die ein Standard-Betriebssystem wie Linux nicht garantiert:

{width=30%}

* **Core 0:** Managt ausschliesslich den micro-ROS-Datenstrom.
* **Core 1:** Fuehrt exklusiv und jitterfrei ($< 2\,\mathrm{ms}$) die PID-Regelschleife und die Inverskinematik aus.
* **CAN-Redundanz:** Ein direkter CAN-Bus vom Sensor-Knoten stoppt die Motoren bei erkannten Abgruenden in $< 20\,\mathrm{ms}$ – komplett unabhaengig vom Host-System.

---

## Edge-KI: Die Navigations-Pipeline

Die lokale Ebene reagiert in Millisekunden auf dynamische Hindernisse:

{width=35%}

* **Lokalisierung:** `slam_toolbox` und AMCL generieren eine 2D-Gitterkarte mit $5\,\mathrm{cm}$ Aufloesung.
* **Bahnverfolgung:** Der Regulated Pure Pursuit Controller faehrt geplante Pfade mit bis zu $0{,}4\,\mathrm{m/s}$ ab.
* **Edge-Vision:** Der Hailo-8L-Beschleuniger erkennt per YOLOv8 Hindernisse im Videostream bei ${\sim}34\,\mathrm{ms}$ Latenz, ohne die CPU des Raspberry Pi zu blockieren.

---

## Software-Architektur und Koordinatensysteme

Die raeumliche Berechnung erfordert eine durchgaengige Koordinaten-Transformation:

{width=45%}

* **TF-Kette:** Transformiert von `map` ueber `odom` zu `base_link` und weiter zu den Sensoren (`laser`, `camera_link`).
* **Dynamik:** Die Odometrie-Publikation ($20\,\mathrm{Hz}$) schaetzt die relative Fortbewegung kontinuierlich, waehrend der SLAM-Knoten die absolute Position im Raum iterativ korrigiert.

---

## Die semantische Cloud-Entscheidung

**Was passiert, wenn die lokale Navigation (Nav2) feststeckt?**

* Der Roboter stoppt zunaechst vor einem unbekannten, blockierenden Hindernis.
* Das System uebergibt das lokal erkannte YOLO-Label (z. B. "Mensch") sowie Telemetriedaten als JSON an die externe Gemini API.
* Die Sprachmodell-Logik bewertet die Situation kontextbasiert:
* Handelt es sich um ein statisches Objekt? $\rightarrow$ *Ausloesen von Recovery-Verhalten und Neuplanung zur Umfahrung.*
* Handelt es sich um einen Menschen im Gang? $\rightarrow$ *Warten und Ausgabe einer Sprachwarnung ueber den Audio-DAC.*



---

## Eigenschaftsabsicherung und Evidenz

Systematische Messdaten validieren den Architekturansatz:

* **Sicherheitslogik:** Die End-to-End-Latenz vom Ausloesen des Kanten-Sensors bis zum Motorstopp betraegt gemessene $2{,}0\,\mathrm{ms}$.
* **Regelungs-Jitter:** Die Architektur haelt die $50\,\mathrm{Hz}$-Regelschleife stabil und drueckt den Jitter auf unter $2\,\mathrm{ms}$.
* **Navigationsgenauigkeit:** Der Absolute Trajectory Error (ATE) liegt nach SLAM-Korrektur bei $0{,}16\,\mathrm{m}$.
* **Docking:** Die Erkennung von ArUco-Markern ermoeglicht eine erfolgreiche Zielanfahrt mit einer Quote von $100\,\%$ (10/10, Dreifach-Bedingung bei $0{,}30\,\mathrm{m}$).

---

## Live-Demo

**Szenario:** Punkt-zu-Punkt Navigation mit Hinderniserkennung und Dashboard-Interaktion.

```bash
# Gesamten ROS-2-Stack inklusive Dashboard und Vision starten
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_vision:=True

```
