---
title: "Effizienz auf der letzten Meile"
subtitle: "Konzeption und Validierung eines Navigationssystems fuer einen autonomen Kleinladungstraeger-Transporter unter Nutzung von ROS 2"
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
6. Navigation und SLAM
7. Validierung und Ergebnisse
8. Live-Demo
9. Zusammenfassung und Ausblick

---

## Motivation und Problemstellung

**Ausgangslage: Intralogistik im Wandel**

- Industrie 4.0: Flexible Fertigung erfordert flexible Materialfluesse
- KLT-Transport (Kleinladungstraeger) bindet personelle Ressourcen ohne Wertschoepfung
- AMR statt FTS: Navigation ohne Leitlinien oder Reflektoren

**Das Problem**

- Industrielle AMR (z.B. MiR100): > 25.000 EUR -- fuer einfache KLT-Aufgaben ueberdimensioniert
- Fehlende validierte Referenzarchitekturen fuer kostenguenstige Open-Source-Systeme
- Herausforderung: Echtzeit-Regelung + autonome Navigation auf Low-Cost-Hardware

<!-- Bild-Platzhalter: Foto des AMR-Prototyps oder Intralogistik-Szenario -->

---

## Zielsetzung und Forschungsfragen

**Hauptziel:** Entwicklung und Validierung eines ROS-2-basierten Navigationssystems fuer einen Low-Cost-AMR (~500 EUR)

**Drei Forschungsfragen:**

- **FF1 -- Echtzeitarchitektur:** Wie laesst sich auf einem ESP32 eine echtzeitfaehige Regelung mit micro-ROS realisieren?
  - Dual-Core-Partitionierung, UART statt WLAN

- **FF2 -- Odometrie-Kalibrierung:** Welchen Einfluss hat die UMBmark-Kalibrierung auf die Navigationsgenauigkeit?
  - Systematische Fehlerreduktion um Faktor 10--20

- **FF3 -- Visuelles Docking:** Ist ArUco-basiertes Andocken mit monokularer Kamera hinreichend praezise?
  - Ziel: < 2 cm lateral, < 5 Grad Orientierung

**Methodik:** V-Modell nach VDI 2206

---

## Systemarchitektur

**Verteilte Dual-Rechner-Architektur**

```
+------------------+    micro-ROS/UART    +------------------+
|   ESP32-S3       | <------------------> |  Raspberry Pi 5  |
|   (Low-Level)    |    /cmd_vel, /odom   |  (High-Level)    |
|                  |    /imu              |                  |
| Core 0: micro-ROS|                      | SLAM Toolbox     |
| Core 1: PID 50Hz |                      | Nav2 Stack       |
| Encoder + IMU    |                      | AMCL             |
+------------------+                      +------------------+
        |                                         |
   Cytron MDD3A                              RPLidar A1
   2x JGA25-370                              IMX296 Kamera
```

- **Kommunikation:** micro-ROS ueber UART (USB-CDC), Reliable QoS
- **Thread-Safety:** FreeRTOS-Mutex zwischen Core 0 und Core 1

<!-- Bild-Platzhalter: Systemblockbild / Node-Graph -->

---

## Hardware-Plattform

**Komponenten (~500 EUR Gesamtkosten)**

| Komponente | Funktion |
|---|---|
| Raspberry Pi 5 | High-Level: SLAM, Nav2, RViz2 |
| XIAO ESP32-S3 | Low-Level: PID, Odometrie, IMU |
| Cytron MDD3A | Dual-Motortreiber (PWM) |
| 2x JGA25-370 | Getriebemotoren mit Hall-Encoder |
| RPLIDAR A1 | 2D-LiDAR (12m Reichweite) |
| MPU6050 | 6-Achsen IMU (Gyro + Beschleunigung) |
| IMX296 | Global-Shutter-Kamera (ArUco-Docking) |

**Roboter-Parameter:**

- Raddurchmesser: 65,67 mm (kalibriert), Spurbreite: 178 mm
- Encoder: ~748 Ticks/Rev (Quadratur), PID: Kp=0,4, Ki=0,1
- Zielgeschwindigkeit: 0,4 m/s, Failsafe-Timeout: 500 ms

<!-- Bild-Platzhalter: Foto des Roboters mit beschrifteten Komponenten -->

---

## Software-Stack

**ESP32 Firmware (C++, FreeRTOS, PlatformIO)**

- Dual-Core: Core 0 = micro-ROS Executor, Core 1 = PID @ 50 Hz
- Header-only Module: `robot_hal.hpp`, `pid_controller.hpp`, `diff_drive_kinematics.hpp`, `mpu6050.hpp`
- Complementary-Filter: 98% Gyro + 2% Encoder fuer Heading-Fusion

**Raspberry Pi 5 (ROS 2 Humble via Docker)**

- `ros:humble-ros-base` (arm64) + manuell installierte Pakete
- micro-ROS Agent aus Source gebaut (kein apt fuer arm64)
- Docker: `network_mode: host`, `privileged: true`

**ROS 2 Nodes:**

- `micro_ros_agent` -- Serial-Bridge ESP32 <-> ROS 2
- `odom_to_tf` -- Odometrie -> TF-Baum
- `rplidar_node` -- 2D-Laserscan
- `slam_toolbox` -- Async SLAM, 5 cm Aufloesung
- `nav2` -- Regulated Pure Pursuit, AMCL, Costmaps

---

## Navigation und SLAM

**TF-Baum**

```
map -> odom -> base_link -> laser (statisch, 180 Grad Yaw)
                         -> camera_link (optional)
```

**SLAM Toolbox (Async)**

- Ceres-Solver, Loop Closure, 5 cm Rasteraufloesung
- Kartierung bei 0,15 m/s, LiDAR @ 7,6 Hz

**Nav2 Stack**

- Regulated Pure Pursuit Controller (0,4 m/s max)
- NavFn Global Planner (A*)
- Costmaps: Static + Obstacle + Inflation Layer
- Recovery Behaviors: Spin, Back-Up, Wait

**ArUco-Docking**

- Visual Servoing mit OpenCV `ArucoDetector`
- SolvePnP-Pose-Schaetzung + P-Regler Feinpositionierung
- Aktiv bei `use_camera:=True`

<!-- Bild-Platzhalter: SLAM-Karte oder RViz2-Screenshot -->

---

## Validierung und Ergebnisse

**Subsystem-Verifikation (Kap. 6.2)**

| Test | Ergebnis | Kriterium |
|---|---|---|
| PID-Regelfrequenz | 50 Hz, Jitter < 2 ms | PASS |
| Odometrie (UMBmark) | Fehlerreduktion > 10x | PASS |
| micro-ROS Datenverlust | < 0,1% | PASS |
| Odom-Publikationsrate | 20 Hz stabil | PASS |
| IMU Gyro-Drift | 0,218 Grad/min (< 1,0) | PASS |
| Geradeausfahrt-Drift | 1,5 cm (mit IMU, vorher 3,5 cm) | PASS |

**Navigationsvalidierung (Kap. 6.3)**

| Test | Ergebnis | Kriterium |
|---|---|---|
| ATE Kartierung | 0,16 m (< 0,20 m) | PASS |
| Positionsgenauigkeit | 6,4 cm (< 10 cm) | PASS |
| Orientierungsgenauigkeit | 4,2 Grad (< 8 Grad) | PASS |

**Docking-Validierung (Kap. 6.4)**

| Test | Ergebnis | Kriterium |
|---|---|---|
| Lateraler Versatz | 1,3 cm (< 2 cm) | PASS |
| Orientierungsfehler | 2,8 Grad (< 5 Grad) | PASS |
| Erfolgsquote | 80% (8/10 Versuche) | PASS |

---

## Validierung -- Kernergebnisse

**FF1 bestaetigt:** Dual-Core-Partitionierung loest Echtzeit-Problem

- Core 1: PID @ 50 Hz deterministisch, unabhaengig von micro-ROS
- UART statt WLAN: deterministische Latenz (vs. 129 ms WiFi-RTT)

**FF2 bestaetigt:** UMBmark-Kalibrierung ist unverzichtbar

- Raddurchmesser: 65,00 mm -> 65,67 mm (kalibriert)
- Systematische Odometriefehler um Faktor 10--20 reduziert
- ATE nach Kalibrierung: 0,16 m (Referenz SLAM Toolbox: 0,17 m)

**FF3 bedingt bestaetigt:** ArUco-Docking funktioniert unter Bedingungen

- 80% Erfolgsrate, 1,3 cm Positionsfehler
- Einschraenkungen: Beleuchtungsabhaengigkeit, Sichtfeld-Limitierung
- Verbesserungspotenzial: Tiefenkamera, Regressionsansatz

**Alle Must-have-Anforderungen erfuellt**

---

## Live-Demo

**Demonstrationsszenario: KLT-Transport**

1. Roboter kartiert Umgebung (SLAM)
2. Autonome Punkt-zu-Punkt-Navigation mit Hindernisvermeidung
3. ArUco-basiertes Andocken an Ladestation

**Systemstart:**

```bash
# Docker-Container mit Full-Stack starten:
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_camera:=True use_rviz:=False
```

**Beobachtbare Topics:**

- `/odom` -- Rad-Odometrie @ 20 Hz
- `/scan` -- 2D-LiDAR-Daten
- `/imu` -- IMU-Daten @ ~18 Hz
- `/map` -- Occupancy Grid (SLAM)

<!-- Bild-Platzhalter: Foto des Roboters im Testareal -->

---

## Zusammenfassung und Ausblick

**Zusammenfassung**

- Vollstaendiger Entwicklungszyklus nach V-Modell (VDI 2206) durchlaufen
- Dual-Rechner-Architektur: ESP32 (Echtzeit) + RPi 5 (Navigation)
- Gesamtkosten: ~500 EUR (vs. > 25.000 EUR industriell)
- Alle drei Forschungsfragen positiv beantwortet
- Alle Must-have-Anforderungen des Lastenhefts erfuellt

**Ausblick**

- **Hardware:** Eigene PCB statt fliegende Verdrahtung, IP-Gehaeuse
- **Sensorfusion:** EKF-Integration (robot_localization) mit IMU + Encoder
- **Online-Kalibrierung:** Schlupfkompensation nach De Giorgi et al.
- **Flottenmanagement:** Integration in Open-RMF
- **Docking:** Tiefenkamera, regressionsbasierter Ansatz (Oh und Kim)
- **Sicherheit:** ISO 3691-4, CE-Konformitaet, Safety-LiDAR

**Vielen Dank fuer die Aufmerksamkeit!**

<!-- Bild-Platzhalter: Abschlussfoto des Roboters -->
