# Kernaussagen: From Simulation to Reality -- Comparative Performance Analysis of SLAM Toolbox and Cartographer in ROS 2

## Bibliografische Angaben

- **Autoren:** Ibrahim Ince, Derya Yiltas-Kaplan, Fatih Keles
- **Titel:** From Simulation to Reality: Comparative Performance Analysis of SLAM Toolbox and Cartographer in ROS 2
- **Journal:** Electronics (MDPI), 2025, 14, 4822
- **DOI:** https://doi.org/10.3390/electronics14244822
- **Veröffentlicht:** 8. Dezember 2025
- **Typ:** Peer-reviewed Journalartikel (Open Access, CC BY)

---

## Zusammenfassung

Die Studie vergleicht SLAM Toolbox und Cartographer unter identischen Bedingungen in ROS 2 Humble Hawksbill -- sowohl in einer Gazebo-Simulation als auch auf einem physischen Differentialantrieb-Roboter mit 2D-LiDAR, IMU und Rad-Encodern. Bewertet werden Absolute Trajectory Error (ATE), CPU-/RAM-Verbrauch, Kartierungsqualitaet, Startzeit und Echtzeitverhalten. Ergebnis: SLAM Toolbox liefert stabilere Karten und niedrigeren ATE dank externer EKF-Odometrie, waehrend Cartographer in der realen Welt schneller kartiert und weniger CPU benoetigt, aber empfindlicher auf Parametertuning und rauschfreie Simulation reagiert.

---

## Kernaussagen

### 1. Algorithmische Grundarchitektur (S. 3, 6)

- **SLAM Toolbox** basiert auf Pose-Graph-Optimierung und ist stark abhaengig von extern bereitgestellter, EKF-fusionierter Odometrie (Encoder + IMU). Es fuehrt Scan-to-Map-Matching und Loop Closure durch. (S. 6)
- **Cartographer** nutzt Submap-basierte Optimierung mit integriertem Ceres-Solver fuer Echtzeit-Scan-Matching, IMU-gestuetzte Bewegungsfilterung und globale Pose-Graph-Optimierung mit Loop Closure. Cartographer kann ohne externe Odometrie arbeiten. (S. 6)
- Dieser fundamentale Architekturunterschied -- externe vs. interne Odometrie -- erklaert die meisten beobachteten Leistungsunterschiede. (S. 18-19)

### 2. Sensorarchitektur und TF-Baum (S. 6, 12-13)

- Der Roboter nutzt 360-Grad-LiDAR, IMU und Rad-Encoder, fusioniert via EKF aus dem `robot_localization`-Paket. (S. 6)
- Korrekte TF-Hierarchie ist essenziell: `map -> odom -> base_footprint -> base_link -> laser_frame`. Fehlkonfigurationen fuehren zu stark verzerrten Karten. (S. 6, 12-14)
- Die TF-Kette umfasst statische Frames (`/base_link`, `/base_footprint`) und dynamische Frames (`/odom`, `/laser`). (S. 12)

### 3. Simulationsergebnisse -- Benchmark-Tabelle (S. 17, Table 6)

| Metrik | SLAM Toolbox | Cartographer |
|---|---|---|
| CPU-Auslastung (%) | 70 | 80 |
| Peak RAM (MB) | 293 | 299 |
| Kartierungsgeschwindigkeit | Schnell | Langsamer |
| Kartenqualitaet | Hoch | Moderat |
| **ATE (m)** | **0.13** | **0.21** |
| Echtzeitverhalten | Stabil | Gelegentliche Verzoegerungen |
| System Lag/Freezing | Keines | Ja |
| Startzeit (s) | 5.2 | 7.8 |

- SLAM Toolbox erreicht in der Simulation deutlich besseren ATE (0.13 m vs. 0.21 m), da Gazebo ideale, rauschfreie Encoder-/IMU-Signale liefert, die der EKF optimal nutzt. (S. 17-18)
- Cartographer leidet in rauschfreier Simulation, weil sein Ceres-basierter Scan-Matcher auf natuerliche Scan-Variationen angewiesen ist. Ohne Sensorrauschen wird die Optimierung instabil. (S. 4-5, 10, 18)

### 4. Real-World-Ergebnisse -- Benchmark-Tabelle (S. 17, Table 7)

| Metrik | SLAM Toolbox | Cartographer |
|---|---|---|
| CPU-Auslastung (%) | 81.9 | 72.3 |
| Peak RAM (MB) | 793 | 560 |
| Kartierungsgeschwindigkeit | Langsamer | Schnell |
| Kartenqualitaet | Hoch | Moderat |
| **ATE (m)** | **0.17** | **0.28** |
| Echtzeitverhalten | Stabil | Gelegentliche Verzoegerungen |
| System Lag/Freezing | Keines | Ja |
| Startzeit (s) | 7.4 | 3.2 |

- In der realen Welt verbessert sich Cartographer relativ zur Simulation, da reales Sensorrauschen dem Scan-Matcher hilft. Cartographer zeigt niedrigere CPU-Last (72.3% vs. 81.9%) und deutlich weniger RAM-Verbrauch (560 MB vs. 793 MB). (S. 17-18)
- SLAM Toolbox behaelt den ATE-Vorteil (0.17 m vs. 0.28 m) und hohe Kartenqualitaet, benoetigt aber mehr Ressourcen. (S. 17)
- Cartographer startet schneller (3.2 s vs. 7.4 s) und kartiert schneller in der realen Welt. (S. 17)

### 5. Kartenqualitaetsmetriken (S. 18, Table 8)

| Metrik | SLAM Toolbox | Cartographer | Interpretation |
|---|---|---|---|
| Map Coverage (%) | 94.7 | 92.3 | Toolbox erfasst groesseren Anteil |
| Structural Consistency (0-1) | 0.87 | 0.82 | Toolbox bewahrt Wand-/Korridorgeometrie besser |
| Revisit Accuracy (m) | 0.06 | 0.09 | Toolbox zeigt geringeren Drift bei Loop Closure |

- Beide Algorithmen erreichen hohe und praktisch nutzbare Kartenqualitaet. SLAM Toolbox hat leichte Vorteile in allen drei Metriken. (S. 18)

### 6. Odometrie-Stoerungstest (S. 15)

- Bei absichtlich gestoerter Rad-Odometrie (simulierter Radschlupf, Driftinjektion) bricht die SLAM-Toolbox-Karte sofort zusammen -- stark verzerrte, unbrauchbare Karte. (S. 15, Fig. 11)
- Nach Wiederherstellung korrekter EKF-Odometrie funktioniert SLAM Toolbox sofort wieder einwandfrei. (S. 15, Fig. 12)
- Dies bestaetigt die starke Abhaengigkeit von SLAM Toolbox von qualitativ hochwertiger externer Odometrie. (S. 15, 19)

### 7. Cartographer-Parameterempfindlichkeit und Tuning (S. 6-8)

- Cartographer hat ueber 40 konfigurierbare Parameter in der Lua-Datei. (S. 6-7, Table 2)
- Die Studie identifiziert hochsensitive Parameter: `translation_weight`, `rotation_weight`, `num_accumulated_range_data`, `motion_filter.max_time_seconds`, `voxel_filter_size`, `huber_scale`, `min_range`/`max_range`, `submap_resolution`. (S. 7)
- Systematisches Tuning-Protokoll: Coarse Grid Search (+/-40%), dann Fine Grid Search (+/-10%) um bestes Ergebnis. Abbruchkriterium: <2% Verbesserung in ATE oder Map Alignment. (S. 7-8, Table 3)
- Falsche Parametrierung oder LiDAR-Frequenz fuehren zu Artefakten in den Karten. (S. 15, Fig. 13)

### 8. SLAM Toolbox Modi (S. 8, Table 4)

- Online Asynchronous (`mapper_params_online_async.yaml`): Echtzeit-Mapping in dynamischen Umgebungen mit asynchroner Sensorverarbeitung.
- Online Synchronous (`mapper_params_online_sync.yaml`): Echtzeit-Mapping mit synchronisierter Sensorverarbeitung fuer stabile Umgebungen.
- Offline Mapping (`mapper_params_offline.yaml`): Nachverarbeitung aufgezeichneter Daten fuer hoechste Kartenqualitaet.

### 9. Trade-off-Zusammenfassung und Empfehlungen (S. 19)

- **SLAM Toolbox empfohlen** fuer: Indoor-Mobile-Roboter mit zuverlaessiger fusionierter Odometrie, dynamische Umgebungen, wenn hohe Kartengenauigkeit und Loop-Closure-Stabilitaet Prioritaet haben. Nachteil: Hoeherer CPU-/RAM-Verbrauch, langsamere Kartierung. (S. 19)
- **Cartographer empfohlen** fuer: Szenarien mit begrenzten Rechenressourcen, wenn schnelle Kartierung gebraucht wird, oder wenn keine externe Odometrie verfuegbar ist. Nachteil: Empfindlicher gegenueber Parametrierung und Sensormisalignment. (S. 19)
- Die Algorithmenauswahl sollte sich am operationellen Kontext orientieren, nicht an einem pauschalen "besser/schlechter". (S. 19)

### 10. Hardwareplattform und Limitationen (S. 12, 19)

- Physischer Roboter basiert auf Raspberry Pi 4, was die CPU-/RAM-Messungen beeinflusst. (S. 19)
- Nur eine Indoor-Umgebung und ein LiDAR-Modell getestet -- Generalisierbarkeit eingeschraenkt. (S. 19)
- Keine dynamischen Hindernisse und keine Outdoor-Szenarien evaluiert. (S. 19)

---

## Relevanz fuer die Projektarbeit

### Direkt anwendbar (Kap. 2.5 -- SLAM, Kap. 6.3 -- Diskussion)

1. **Begruendung der SLAM-Toolbox-Wahl:** Die Projektarbeit nutzt SLAM Toolbox im async-Modus. Die Studie liefert quantitative Evidenz, dass SLAM Toolbox bei verfuegbarer EKF-Odometrie (wie im BA-Roboter: ESP32-Encoder + IMU via micro-ROS) den niedrigeren Trajektorienfehler und stabilere Karten produziert (ATE 0.13 m Simulation, 0.17 m real-world).

2. **EKF-Odometrie als Schluesselanforderung:** Der Odometrie-Stoerungstest (S. 15) unterstreicht, wie kritisch die korrekte EKF-Fusion fuer SLAM Toolbox ist -- direkt relevant fuer die Odometrie-Kalibrierung via UMBmark in der BA (Kap. 4.4).

3. **TF-Baum-Konfiguration:** Die dokumentierte TF-Hierarchie (`map -> odom -> base_footprint -> base_link -> laser_frame`) und die Warnung vor Fehlkonfigurationen (Fig. 11/12) ist direkt auf den BA-Roboter uebertragbar.

4. **Ressourcenverbrauch auf Raspberry Pi:** Die Real-World-Daten (Table 7) auf Raspberry Pi 4 geben realistische Benchmark-Werte fuer die aehnliche Plattform der BA (Raspberry Pi 5).

5. **Cartographer als Alternative:** Die Studie bietet eine fundierte Diskussionsgrundlage, warum Cartographer trotz schnellerer Kartierung und geringerer CPU-Last nicht gewaehlt wurde (hoeherer ATE, Parameterempfindlichkeit, Abhaengigkeit von natuerlichem Sensorrauschen).

6. **Kartenqualitaetsmetriken:** Map Coverage, Structural Consistency und Revisit Accuracy (Table 8) koennen als Referenzwerte fuer die Validierung der BA-Ergebnisse herangezogen werden.
