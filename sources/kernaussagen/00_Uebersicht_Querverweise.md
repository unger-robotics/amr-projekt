# Uebersicht: 15 Kernaussagen-Dateien mit Querverweisen

> Erstellt als Querverweis-Index fuer die Projektarbeit "Autonomer Mobiler Roboter fuer Intralogistik"
> 15 Quellen, 4 Themenfelder, geordnet nach Literaturstrategie

---

## Dateiindex

| Nr. | Datei | Quelle(n) | Themenfeld |
|-----|-------|-----------|------------|
| 01 | [01_ROS2_Architektur_Kernaussagen.md](01_ROS2_Architektur_Kernaussagen.md) | Macenski et al. 2022 -- Science Robotics | Uebergreifend (Plattform) |
| 02 | [02_Nav2_SLAM_Kernaussagen.md](02_Nav2_SLAM_Kernaussagen.md) | Macenski et al. 2023 (Nav2) + Macenski et al. 2021 (SLAM Toolbox) | SLAM & Navigation |
| 03 | [03_EKF_Sensorfusion_Kernaussagen.md](03_EKF_Sensorfusion_Kernaussagen.md) | Moore & Stouch 2014 -- robot_localization | Sensorfusion & Lokalisierung |
| 04 | [04_ESP32_MicroROS_Kernaussagen.md](04_ESP32_MicroROS_Kernaussagen.md) | Albarran et al. 2023 -- Revista elektron | micro-ROS & ESP32 |
| 05 | [05_Abaza_ESP32_Stack_Kernaussagen.md](05_Abaza_ESP32_Stack_Kernaussagen.md) | Abaza 2025 -- Sensors (MDPI) | micro-ROS & ESP32 / Sensorfusion |
| 06 | [06_DualCore_Executor_Kernaussagen.md](06_DualCore_Executor_Kernaussagen.md) | Yordanov et al. 2025 + Staschulat et al. 2020 | micro-ROS & ESP32 |
| 07 | [07_Cartographer_Kernaussagen.md](07_Cartographer_Kernaussagen.md) | Hess et al. 2016 -- ICRA (Google) | SLAM & Navigation |
| 08 | [08_Odometrie_Kalibrierung_Kernaussagen.md](08_Odometrie_Kalibrierung_Kernaussagen.md) | De Giorgi et al. 2024 -- Robotics (MDPI) | Kinematik & Regelung |
| 09 | [09_Siegwart_Kinematik_Kernaussagen.md](09_Siegwart_Kinematik_Kernaussagen.md) | Siegwart & Nourbakhsh 2004 -- Lehrbuch | Kinematik & Regelung |
| 10 | [10_Borenstein_Odometrie_Kernaussagen.md](10_Borenstein_Odometrie_Kernaussagen.md) | Borenstein et al. 1996 -- Where Am I? | Kinematik & Regelung |
| 11 | [11_SLAM_Vergleich_Kernaussagen.md](11_SLAM_Vergleich_Kernaussagen.md) | Ince et al. 2025 -- Electronics (MDPI) | SLAM & Navigation |
| 12 | [12_ArUco_Docking_Kernaussagen.md](12_ArUco_Docking_Kernaussagen.md) | Oh & Kim 2025 -- Sensors (MDPI) | Navigation (Docking) |
| 13 | [13_2DLIW_SLAM_Kernaussagen.md](13_2DLIW_SLAM_Kernaussagen.md) | Zhang et al. 2024 -- arXiv | SLAM & Navigation |
| 14 | [14_MicroROS_Thesis_Kernaussagen.md](14_MicroROS_Thesis_Kernaussagen.md) | Nguyen 2022 -- M.Sc. Thesis (MDU) | micro-ROS & ESP32 |
| 15 | [15_Scheduling_Kernaussagen.md](15_Scheduling_Kernaussagen.md) | Wang et al. 2024 -- Electronics (MDPI) | micro-ROS & ESP32 |

---

## Themenfeld 1: SLAM & Navigation

### Beteiligte Dateien
- **02** Nav2 + SLAM Toolbox (Macenski 2023/2021)
- **07** Google Cartographer (Hess 2016)
- **11** SLAM Toolbox vs. Cartographer Vergleich (Ince 2025)
- **13** 2DLIW-SLAM (Zhang 2024)

### Querverweise

| Verbindung | Beschreibung |
|------------|-------------|
| **02 <-> 07** | SLAM Toolbox (02) und Cartographer (07) sind die beiden SLAM-Systeme, die in Nav2 integriert sind. Beide nutzen Pose-Graph-Optimierung, aber Cartographer arbeitet Submap-basiert mit Ceres-Solver, waehrend SLAM Toolbox auf Karto-basiertem Scan-Matching aufbaut. |
| **02 <-> 11** | Die SLAM-Vergleichsstudie (11) evaluiert exakt die in 02 beschriebenen Algorithmen (SLAM Toolbox + Cartographer) unter ROS 2 Humble -- quantifiziert die in 02 qualitativ beschriebenen Unterschiede mit ATE-Metriken. |
| **07 <-> 11** | Cartographer (07) erreicht in der Vergleichsstudie (11) ATE 0.28 m real-world vs. SLAM Toolbox 0.17 m. In der Simulation ist Cartographer jedoch ueberlegen (ATE 0.034 m vs. 0.061 m). Die in 07 beschriebene Submap-Architektur erklaert die bessere Simulationsleistung bei rauschfreien Daten. |
| **07 <-> 13** | 2DLIW-SLAM (13) uebertrifft Cartographer (07) auf dem OpenLORIS-Datensatz -- insbesondere bei geometrisch aehnlichen Umgebungen (Korridore), wo Cartographers Scan-Matching degeneriert. Die enge Sensor-Kopplung (LiDAR+IMU+Wheel) in 13 kompensiert die Schwaeche des reinen LiDAR-Matchings in 07. |
| **11 <-> 13** | Beide Studien vergleichen SLAM-Algorithmen, aber mit unterschiedlichem Fokus: 11 vergleicht SLAM Toolbox vs. Cartographer unter identischen ROS 2-Bedingungen, 13 stellt einen neuen Algorithmus (2DLIW-SLAM) gegen Cartographer und Gmapping. Gemeinsame Erkenntnis: Cartographer ist empfindlich bei verrauschter Odometrie. |
| **11 <-> 03** | Die SLAM-Vergleichsstudie (11) nutzt den EKF aus robot_localization (03) als externe Odometrie-Quelle fuer SLAM Toolbox. SLAM Toolbox ist stark abhaengig von der EKF-Qualitaet; mit gestoerter Odometrie kollabiert es (11, S. 18). Dies unterstreicht die zentrale Rolle von 03. |
| **02 <-> 12** | Nav2 (02) definiert den Navigationsstack, der den Roboter zum ArUco-Docking (12) fuehrt. Nav2 liefert die grobe Positionierung, ArUco-Docking uebernimmt die Feinpositionierung (~2 cm Genauigkeit). |

---

## Themenfeld 2: Sensorfusion & Lokalisierung

### Beteiligte Dateien
- **03** robot_localization EKF (Moore 2014)
- **05** Abaza 2025 -- AI-Driven Dynamic Covariance
- **08** Online-Odometrie-Kalibrierung (De Giorgi 2024)

### Querverweise

| Verbindung | Beschreibung |
|------------|-------------|
| **03 <-> 05** | Abaza (05) baut direkt auf robot_localization (03) auf -- identisches EKF-Paket mit 12D-Zustandsvektor. 05 erweitert 03 um KI-gestuetzte dynamische Kovarianzanpassung via Random Forest. Beide nutzen die gleiche Sensor-Fusion-Architektur (Odometrie + IMU). |
| **03 <-> 08** | robot_localization (03) fusioniert Odometrie-Daten, deren Qualitaet direkt von der Kalibrierung (08) abhaengt. Die C-Matrix-Parametrisierung in 08 (r_R, r_L, b) definiert die systematischen Fehler, die in den Kovarianzmatrizen von 03 modelliert werden muessen. |
| **03 <-> 11** | Die SLAM-Vergleichsstudie (11) nutzt robot_localization (03) als EKF-Fusionsschicht. SLAM Toolbox ist abhaengig von der EKF-Qualitaet aus 03, Cartographer nicht. |
| **05 <-> 08** | Beide behandeln Odometrie-Fehler bei Differentialantrieb: 05 nutzt dynamische Kovarianz zur Laufzeit, 08 kalibriert die kinematischen Parameter offline/online. 08 liefert die Grundlage (korrekte r_R, r_L, b), auf der 05 aufbaut (adaptive Kovarianz fuer den EKF). |
| **03 <-> 13** | 2DLIW-SLAM (13) integriert Rad-Odometrie als Beobachtungsmodell in die enge Kopplung, waehrend robot_localization (03) Odometrie als lose gekoppelten EKF-Input verarbeitet. Zwei verschiedene Fusionsansaetze fuer die gleichen Sensordaten. |

---

## Themenfeld 3: micro-ROS & ESP32

### Beteiligte Dateien
- **04** Albarran 2023 -- ESP32 Diff-Drive Hardware
- **05** Abaza 2025 -- ESP32 + RPi Stack
- **06** Dual-Core Partitionierung + rclc Executor
- **14** Nguyen 2022 -- micro-ROS Performance-Messung
- **15** Wang 2024 -- micro-ROS Scheduling (PoDS)

### Querverweise

| Verbindung | Beschreibung |
|------------|-------------|
| **04 <-> 05** | Beide beschreiben ESP32-basierte Differentialantrieb-AMRs mit ROS 2. Hauptunterschied: 04 nutzt micro-ROS ueber WiFi, 05 nutzt ros2_control + diff_drive_controller ueber serielle Bridge. Die BA kombiniert Elemente beider Ansaetze (micro-ROS wie 04, aber UART-Transport wie die serielle Verbindung in 05). |
| **06 <-> 04/05** | Die Dual-Core-Partitionierung (06, Yordanov) validiert das Architekturmuster, das auch die BA nutzt: zeitkritische Tasks auf einem Kern, Kommunikation auf dem anderen. 04 und 05 nutzen den ESP32 ohne explizite Dual-Core-Partitionierung. |
| **06 <-> 15** | Der rclc Executor (06, Staschulat) definiert das Standard-Callback-Scheduling, dessen Schwaechen in 15 (Wang) identifiziert werden: Priority Inversion, synchrone DMA-Blockierung, FIFO-basierter Empfang. PoDS (15) loest diese Probleme durch TIDE Executor und Communication Daemon. |
| **14 <-> 15** | Beide untersuchen micro-ROS-Performance auf Mikrocontrollern. 14 (Nguyen) misst RTT von 129 ms (ESP32, WiFi/UDP), 15 (Wang) zeigt End-to-End-Latenz von 37-120 ms (STM32, UART). Die Latenzwerte sind vergleichbar und bestaetigen die Groessenordnung der micro-ROS-Kommunikationskosten. |
| **14 <-> 04** | Beide verwenden ESP32 mit FreeRTOS und micro-ROS. 14 (Nguyen) liefert die Latenzmessungen, die in 04 (Albarran) nicht vorhanden sind. 14 nutzt WiFi/UDP-Transport wie 04. |
| **15 <-> 06** | Wang (15) beschreibt den RCLC Executor identisch wie Staschulat (06): Collection Phase + Execution Phase, Trigger Conditions, Registrierungsreihenfolge als implizite Prioritaet. 15 geht weiter mit der PoDS-Loesung. |
| **05 <-> 03** | Abaza (05) nutzt exakt das robot_localization-Paket aus 03 mit EKF-Konfiguration: odom0 (differential=true), imu0 (differential=false), 50 Hz Update-Rate. |

---

## Themenfeld 4: Kinematik & Regelung

### Beteiligte Dateien
- **08** Online-Odometrie-Kalibrierung (De Giorgi 2024)
- **09** Siegwart & Nourbakhsh 2004 -- Lehrbuch
- **10** Borenstein et al. 1996 -- Where Am I?

### Querverweise

| Verbindung | Beschreibung |
|------------|-------------|
| **09 <-> 10** | Siegwart (09) und Borenstein (10) liefern komplementaere Grundlagen: 09 formalisiert die Vorwaertskinematik (Gl. 3.9, ICR-Konzept, Freiheitsgrade delta_M=2), 10 definiert die Fehlerklassifikation (E_d, E_b) und das UMBmark-Kalibrierungsverfahren. Zusammen bilden sie die vollstaendige theoretische Basis fuer die Odometrie-Implementierung der BA. |
| **10 <-> 08** | De Giorgi (08) referenziert Borenstein & Feng (10) als Pioniermethode der Offline-Kalibrierung (UMBmark). 08 erweitert den Ansatz um Online-Kalibrierung mit Schlupferkennung via IMU. Die C-Matrix in 08 parametrisiert die gleichen Fehlerquellen (r_R, r_L, b), die Borenstein als E_d und E_b definiert. |
| **09 <-> 08** | Die Kovarianz-Propagation (09, Gl. 5.9) modelliert die Fehlerfortpflanzung, die durch die Kalibrierung in 08 minimiert wird. Siegwarts stochastisches Fehlermodell ist die theoretische Grundlage fuer die Kovarianzmatrizen, die De Giorgi online anpasst. |
| **09 <-> 04/05** | Die Differentialantrieb-Gleichungen aus Siegwart (09, Kap. 3) sind direkt in den Firmware-Implementierungen von 04 und 05 umgesetzt (v = (v_R+v_L)/2, omega = (v_R-v_L)/b). |

---

## Uebergreifende Querverweise (Themenfeld-uebergreifend)

### ROS 2 Plattform als Verbindungsglied

| Verbindung | Beschreibung |
|------------|-------------|
| **01 <-> alle** | Macenski 2022 (01) definiert die ROS 2-Architektur (DDS, QoS, Lifecycle Nodes), auf der alle anderen Arbeiten aufbauen. Die Fallstudie zu OTTO Motors (01, S. 5) beschreibt exakt das Intralogistik-Szenario der BA. |
| **01 <-> 04/06** | micro-ROS (01, S. 3) als Embedded-Integration wird in 04 (Hardware) und 06 (Executor/Scheduling) detailliert umgesetzt. |
| **01 <-> 02** | Macenski ist Erstautor beider Arbeiten. 01 beschreibt die ROS 2-Plattform, 02 den darauf aufbauenden Navigationsstack Nav2. Zusammen bilden sie die Referenzarchitektur. |

### Odometrie als Kernproblem (alle Themenfelder)

| Verbindung | Beschreibung |
|------------|-------------|
| **09/10 -> 08 -> 03 -> 11** | Kette der Odometrie-Qualitaet: Kinematische Grundlagen (09/10) -> Kalibrierung (08) -> EKF-Fusion (03) -> SLAM-Eingangsqualitaet (11). Die Vergleichsstudie (11) zeigt: SLAM Toolbox kollabiert bei schlechter Odometrie, Cartographer ist robuster. |
| **09/10 -> 05** | Abaza (05) implementiert die Differentialantrieb-Kinematik (09) auf ESP32, nutzt aber ros2_control statt direkter Gleichungen. Die Kalibrierparameter (10) werden indirekt ueber die URDF und den diff_drive_controller eingestellt. |

### Differentialantrieb als gemeinsame Plattform

| Verbindung | Beschreibung |
|------------|-------------|
| **04 + 05 + 09 + 10 + 08** | Alle fuenf Quellen behandeln den Differentialantrieb: 09 (Theorie), 10 (Kalibrierung), 08 (Online-Korrektur), 04/05 (ESP32-Implementierung). Die BA vereint diese Stränge in einer einzigen Plattform. |
| **12 <-> 02** | ArUco-Docking (12) ergaenzt die Nav2-Navigation (02): Nav2 bringt den Roboter in die Naehe der Docking-Station, ArUco-Visual-Servoing uebernimmt die Feinpositionierung. Die Praezision von ~2 cm (12) liegt innerhalb der 10-cm-Positionstoleranz der BA. |

### Echtzeit-Kommunikation (ESP32 <-> ROS 2)

| Verbindung | Beschreibung |
|------------|-------------|
| **14 + 15 -> 06** | Die micro-ROS-Performance (14: 129 ms RTT, 15: 37-120 ms Latenz) bestimmt die erreichbare Regelguete. Der rclc Executor (06) definiert, wie Callbacks gescheduled werden; PoDS (15) zeigt, dass das Standard-Scheduling bis zu 3x langsamer ist als optimiert. |
| **06 <-> BA-Firmware** | Die Dual-Core-Partitionierung des AMR (Core 0: micro-ROS, Core 1: PID bei 50 Hz) folgt dem Muster aus 06 (Yordanov), umgeht aber die Priority-Inversion-Probleme aus 15 (Wang) durch physische Kern-Trennung statt Software-Scheduling. |

---

## Thematische Cluster-Karte

```
                    ┌─────────────────────────────────┐
                    │  01 ROS 2 Architektur (Macenski) │
                    │         Plattform-Basis          │
                    └──────────┬──────────────┬────────┘
                               │              │
              ┌────────────────▼──┐     ┌─────▼──────────────────┐
              │ SLAM & Navigation │     │   micro-ROS & ESP32    │
              │                   │     │                        │
              │ 02 Nav2 + SLAM TB │     │ 04 ESP32 Hardware      │
              │ 07 Cartographer   │◄───►│ 05 ESP32+RPi Stack     │
              │ 11 SLAM Vergleich │     │ 06 Dual-Core + rclc    │
              │ 13 2DLIW-SLAM    │     │ 14 micro-ROS Latenz    │
              │ 12 ArUco Docking  │     │ 15 Scheduling (PoDS)   │
              └────────┬─────────┘     └──────────┬─────────────┘
                       │                          │
                       │    ┌─────────────────┐   │
                       └───►│  Sensorfusion   │◄──┘
                            │                 │
                            │ 03 EKF (Moore)  │
                            │ 05 Dyn. Kovarianz│
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │ Kinematik &     │
                            │ Regelung        │
                            │                 │
                            │ 08 Online-Kalib.│
                            │ 09 Siegwart LB  │
                            │ 10 Borenstein   │
                            └─────────────────┘
```

---

## Haeufigste Zitationsverbindungen

| Quelle | Wird referenziert von | Thema |
|--------|----------------------|-------|
| **03 Moore (EKF)** | 05, 11, 13 | EKF-Paket als Fusionsschicht |
| **09 Siegwart (Kinematik)** | 04, 05, 08, 10 | Differentialantrieb-Gleichungen |
| **10 Borenstein (UMBmark)** | 08, 09 | Odometrie-Kalibrierung |
| **07 Cartographer** | 11, 13 | SLAM-Benchmark-Vergleich |
| **02 Nav2/SLAM Toolbox** | 11, 12 | Navigationsstack-Architektur |
| **06 rclc Executor** | 15 | Callback-Scheduling-Basis |
| **01 ROS 2** | 02, 04, 05, 06, 14, 15 | Plattform-Referenz |

---

## Zuordnung zu Projektarbeit-Kapiteln

| BA-Kapitel | Primaerquellen | Sekundaerquellen |
|------------|---------------|------------------|
| Kap. 2 -- Stand der Technik: ROS 2 | 01 | 02 |
| Kap. 2 -- Stand der Technik: micro-ROS | 04, 06 | 14, 15 |
| Kap. 3 -- Systemarchitektur | 01, 05 | 06 |
| Kap. 4 -- ESP32 Firmware | 04, 06, 09 | 05, 15 |
| Kap. 4.1 -- Kinematik | 09, 10 | 08 |
| Kap. 4.2 -- PID-Regelung | 04 | 05 |
| Kap. 4.3 -- micro-ROS Kommunikation | 06, 14, 15 | 01, 04 |
| Kap. 5.1 -- SLAM | 02, 07 | 11, 13 |
| Kap. 5.2 -- Lokalisierung (EKF) | 03 | 05, 08 |
| Kap. 5.3 -- Navigation (Nav2) | 02 | 12 |
| Kap. 5.5 -- ArUco Docking | 12 | -- |
| Kap. 6.1 -- Odometrie-Validierung (UMBmark) | 10 | 08 |
| Kap. 6.4 -- Diskussion | 08, 11, 13 | 14, 15 |
