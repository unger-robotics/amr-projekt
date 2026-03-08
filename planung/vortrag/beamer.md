---
title: "Effizienz auf der letzten Meile"
subtitle: "Konzeption und Validierung eines Navigationssystems für einen autonomen Kleinladungsträger-Transporter mit ROS 2"
author: "[Autor]"
date: "[Datum]"
institute: "[Hochschule / Fachbereich]"
theme: "metropolis"
---

## Gliederung

1. Motivation und Problemstellung
2. Zielsetzung und Forschungsfragen
3. Systemarchitektur
4. Hardware-Plattform
5. Software-Stack
6. Navigation und hybride Vision
7. Validierung und Ergebnisse
8. Live-Demo
9. Zusammenfassung und Ausblick

---

## Motivation und Problemstellung

**Ausgangslage: Intralogistik im Wandel**

- Industrie 4.0 erhöht die Anforderungen an flexible Materialflüsse.
- Der Transport von Kleinladungsträgern bindet Personal ohne direkte Wertschöpfung.
- Autonome mobile Roboter arbeiten ohne Leitlinien oder Reflektoren.

**Problemstellung**

- Industrielle AMR wie der MiR100 liegen bei mehr als $25\,000\,\mathrm{EUR}$ und sind für einfache KLT-Transporte oft überdimensioniert.
- Für kostengünstige Open-Source-Systeme fehlen belastbare Referenzarchitekturen.
- Die zentrale technische Herausforderung besteht in der Kopplung von echtzeitfähiger Antriebsregelung und autonomer Navigation auf kostengünstiger Hardware.

---

## Zielsetzung und Forschungsfragen

**Hauptziel**

Entwicklung und Validierung eines ROS-2-basierten Navigationssystems für einen kostengünstigen AMR mit Gesamtkosten von rund $500\,\mathrm{EUR}$.

**Forschungsfragen**

- **FF1 – Echtzeitarchitektur:** Wie lässt sich auf einer Dual-Knoten-Architektur mit zwei ESP32-S3 eine echtzeitfähige Regelung bei gleichzeitiger Sensorerfassung mit micro-ROS realisieren?
  - Entkopplung von Fahrkern und Sensor- und Sicherheitsbasis
  - serielle Kopplung über UART statt WLAN

- **FF2 – Navigationsgenauigkeit:** Welchen Einfluss haben UMBmark-Kalibrierung, IMU-Fusion und hardwarenahe Sicherheitslogik auf die Navigationsgenauigkeit?
  - Zielgröße: deutliche Reduktion systematischer Odometriefehler

- **FF3 – Visuelle Wahrnehmung und Docking:** Erreicht ein monokulares Kamerasystem mit Edge-Inferenz und Cloud-Semantik eine ausreichende Präzision und Kontextsensitivität?
  - Zielwerte: lateraler Fehler kleiner als $2\,\mathrm{cm}$, Orientierungsfehler kleiner als $5^\circ$

**Methodik**

V-Modell nach VDI 2206

---

## Systemarchitektur

**Verteilte Drei-Ebenen-Architektur**

```text
+--------------------+                  +---------------------------+
| Drive-Knoten ESP32 | <─ UART/DDS ───> | Raspberry Pi 5            |
| Core 1: PID 50 Hz  |                  | Bedien- und               |
| Core 0: /odom      |                  | Leitstandsebene           |
+--------------------+                  |                           |
                                        | - Lokalisierung und       |
+--------------------+                  |   Kartierung              |
| Sensor-Knoten      | <─ UART/DDS ───> | - Navigation              |
| ESP32              |                  | - Sicherheitslogik        |
| Core 1: I2C-Sensorik|                 | - Bedien- und             |
| Core 0: /cliff     |                  |   Leitstandsebene         |
+--------------------+                  +---------------------------+
                                                   |
                                         +---------------------------+
                                         | Intelligente Interaktion  |
                                         | - Hailo-8L Edge-Inferenz  |
                                         | - Gemini-Semantik         |
                                         +---------------------------+
```

- **Kommunikation:** micro-ROS über UART (USB-CDC) mit Reliable QoS
- **Synchronisation:** FreeRTOS-Mutex zwischen Core 0 und Core 1 auf beiden ESP32-S3

---

## Hardware-Plattform

**Komponenten mit Gesamtkosten von rund $500\,\mathrm{EUR}$**

| Komponente               | Funktion                                                      |
|--------------------------|---------------------------------------------------------------|
| Raspberry Pi 5           | Bedien- und Leitstandsebene                                   |
| Hailo-8L (PCIe)          | Edge-Inferenz für Objekterkennung                             |
| Drive-Knoten (ESP32-S3)  | Fahrkern: PID-Regelung und Rad-Odometrie                      |
| Sensor-Knoten (ESP32-S3) | Sensor- und Sicherheitsbasis: IMU, Batterie, Kanten-Erkennung |
| Cytron MDD3A             | Dual-Motortreiber im PWM-Betrieb                              |
| 2 × JGA25-370            | Getriebemotoren mit Hall-Encoder                              |
| RPLIDAR A1               | 2D-LiDAR für Lokalisierung und Kartierung                     |
| IMX296                   | Global-Shutter-Kamera                                         |

**Zentrale Parameter**

- Raddurchmesser: $65{,}67\,\mathrm{mm}$
- Spurbreite: $178\,\mathrm{mm}$
- Encoder: rund $748$ Ticks je Umdrehung im Quadraturbetrieb
- PID-Parameter: $K_p = 0{,}4$, $K_i = 0{,}1$
- Zielgeschwindigkeit: $0{,}4\,\mathrm{m/s}$
- Failsafe-Timeout: $500\,\mathrm{ms}$

---

## Software-Stack

**Firmware auf den ESP32-S3**

- Der Drive-Knoten führt die PID-Regelschleife mit $50\,\mathrm{Hz}$ aus und publiziert `/odom`.
- Der Sensor-Knoten erfasst IMU-, Batterie- und Kanten-Signale und publiziert `/imu` sowie `/cliff`.
- Ein Komplementärfilter fusioniert Gyro- und Encoder-Anteile für die Heading-Schätzung.

**ROS 2 auf dem Raspberry Pi 5**

- ROS 2 Humble läuft containerisiert in Docker.
- `ros:humble-ros-base` bildet die Basis für `arm64`.
- Der micro-ROS Agent wird aus dem Quellcode gebaut.
- `network_mode: host` und `privileged: true` sichern den Zugriff auf DDS, serielle Schnittstellen und Geräte.

**Zentrale ROS-2-Knoten**

- `micro_ros_agent` – serielle Brücke zwischen ESP32-S3 und ROS 2
- `cliff_safety_node` – hardwarenahe Sicherheitslogik für Kanten-Erkennung
- `dashboard_bridge` – WebSocket- und MJPEG-Anbindung für die Bedien- und Leitstandsebene
- `slam_toolbox` und `nav2` – Lokalisierung und Kartierung sowie Navigation

---

## Navigation und hybride Vision

**TF-Baum**

```text
map -> odom -> base_link -> laser
                         -> camera_link
                         -> ultrasonic_link
```

**Lokalisierung und Kartierung sowie Navigation**

- `slam_toolbox` arbeitet mit Ceres-Solver, Loop Closure und einer Rasterauflösung von $5\,\mathrm{cm}$.
- Nav2 führt die Zielanfahrt mit Regulated Pure Pursuit aus.
- Die Costmaps kombinieren `StaticLayer`, `ObstacleLayer` und `InflationLayer`.
- Recovery-Verhalten umfasst Drehen, Rücksetzen und Warten.

**Hybride Vision**

- `host_hailo_runner` erzeugt Bounding Boxes mit einer Inferenzlatenz von etwa $34\,\mathrm{ms}$.
- `gemini_semantic_node` ergänzt die Wahrnehmung um kontextbezogene Szenenanalyse.
- Das Docking nutzt ArUco-Marker, SolvePnP-Pose-Schätzung und einen P-Regler zur Feinpositionierung.

---

## Validierung und Ergebnisse

**Verifikation der Subsysteme**

| Test                 | Ergebnis                                               | Kriterium |
|----------------------|--------------------------------------------------------|-----------|
| PID-Regelfrequenz    | $50\,\mathrm{Hz}$, Jitter kleiner als $2\,\mathrm{ms}$ | erfüllt   |
| Kanten-Stopp-Latenz  | kleiner als $50\,\mathrm{ms}$                          | erfüllt   |
| Hailo-8L-Inferenz    | rund $34\,\mathrm{ms}$ je Frame                        | erfüllt   |
| Odometrie-Rate       | stabile $20\,\mathrm{Hz}$                              | erfüllt   |
| Geradeausfahrt-Drift | $1{,}5\,\mathrm{cm}$ mit IMU-Fusion                    | erfüllt   |

**Validierung der Navigation**

| Test                 | Ergebnis             | Kriterium                        |
|----------------------|----------------------|----------------------------------|
| ATE bei Kartierung   | $0{,}16\,\mathrm{m}$ | kleiner als $0{,}20\,\mathrm{m}$ |
| Positionsgenauigkeit | $6{,}4\,\mathrm{cm}$ | kleiner als $10\,\mathrm{cm}$    |
| Winkelgenauigkeit    | $4{,}2^\circ$         | kleiner als $8{,}6^\circ$        |

**Validierung des Dockings**

| Test                | Ergebnis                        | Kriterium                    |
|---------------------|---------------------------------|------------------------------|
| Lateraler Versatz   | $1{,}3\,\mathrm{cm}$            | kleiner als $2\,\mathrm{cm}$ |
| Orientierungsfehler | $2{,}8^\circ$                   | kleiner als $5^\circ$        |
| Erfolgsquote        | $80\,\%$ bei 8 von 10 Versuchen | erfüllt                      |

---

## Kernergebnisse

**FF1 bestätigt**

- Die Trennung in Drive-Knoten und Sensor-Knoten stabilisiert die Echtzeitfähigkeit.
- Fahrkern und Sensor- und Sicherheitsbasis blockieren sich nicht gegenseitig.
- Die serielle Kopplung über UART liefert deterministischere Laufzeiten als WLAN.

**FF2 bestätigt**

- Die UMBmark-Kalibrierung korrigiert den Raddurchmesser von $65{,}00\,\mathrm{mm}$ auf $65{,}67\,\mathrm{mm}$.
- Systematische Odometriefehler sinken um den Faktor 10 bis 20.
- Die Sicherheitslogik stoppt den Roboter zuverlässig, bevor die Navigation reagieren muss.

**FF3 bedingt bestätigt**

- Die hybride Vision erreicht beim Docking eine Erfolgsquote von $80\,\%$.
- Die Edge-Inferenz ist schnell genug für laufende Eingriffe in die Missionsausführung.
- Grenzen bestehen bei Beleuchtung, Sichtfeld und Marker-Sichtbarkeit.

**Status der Muss-Anforderungen**

Alle Muss-Anforderungen sind erfüllt.

---

## Live-Demo

**Demonstrationsszenario: KLT-Transport**

1. Lokalisierung und Kartierung der Umgebung
2. autonome Punkt-zu-Punkt-Navigation mit Objekterkennung
3. Reaktion der Sicherheitslogik auf eine simulierte Kante
4. ArUco-basiertes Docking an einer Ladestation

**Systemstart**

```bash
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_vision:=True use_audio:=True
```

**Beobachtbare Topics**

- `/odom` – Rad-Odometrie mit $20\,\mathrm{Hz}$
- `/cliff` – Kanten-Erkennung mit $20\,\mathrm{Hz}$
- `/map` – Belegungskarte aus `slam_toolbox`

---

## Zusammenfassung und Ausblick

**Zusammenfassung**

- vollständiger Entwicklungszyklus nach VDI 2206
- verteilte Drei-Ebenen-Architektur mit zwei ESP32-S3 und einem Raspberry Pi 5
- positive Beantwortung aller drei Forschungsfragen mit abgestuftem Ergebnis für FF3
- Erfüllung aller Muss-Anforderungen des Lastenhefts

**Ausblick**

- **Hardware:** eigene Leiterplatte statt freier Verdrahtung, robustes Gehäuse
- **Sensorfusion:** EKF-Integration mit `robot_localization`
- **Flottenmanagement:** Einbindung in Open-RMF
- **Sicherheit:** weitere Annäherung an Anforderungen aus ISO 3691-4 und CE-Konformität

## Schlussfolie

Fragen
