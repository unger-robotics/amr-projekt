# 2DLIW-SLAM: 2D LiDAR-Inertial-Wheel Odometry with Real-Time Loop Closure

## Bibliografische Angaben

- **Autoren:** Bin Zhang, Zexin Peng, Bi Zeng, Junjie Lu
- **Institution:** Guangdong University of Technology, Guangzhou, China
- **Datum:** April 2024
- **Quelle:** arXiv:2404.07644v5 [cs.RO]
- **Typ:** Konferenzbeitrag / Preprint

## Zusammenfassung

Das Paper praesentiert 2DLIW-SLAM, ein kostenguenstiges Multi-Sensor-SLAM-System fuer Indoor-Mobilroboter, das 2D-LiDAR, IMU und Rad-Odometrie eng gekoppelt fusioniert. Das Front-End extrahiert Punkt- und Linienmerkmale aus 2D-LiDAR-Daten, nutzt IMU-Praeintegration und Rad-Odometrie-Beobachtungsmodelle, und optimiert alle Sensorinformationen gemeinsam (Joint Optimization). Das Back-End implementiert eine neuartige globale Feature-Point-basierte Loop-Closure-Erkennung mit Pose-Graph-Optimierung. Evaluiert auf dem OpenLORIS-Scene-Datensatz uebertrifft 2DLIW-SLAM Cartographer und Gmapping hinsichtlich Trajektorienfehler und Robustheit, insbesondere bei Degenerationsproblemen (geometrisch aehnliche Umgebungen wie lange Korridore).

## Kernaussagen

### 1. Enge Kopplung von drei Sensoren im Front-End (S. 4-6)

Das Front-End koppelt 2D-LiDAR, IMU und Rad-Odometrie eng in einer gemeinsamen Optimierung (Joint Optimization, Gl. 14). Dies unterscheidet sich fundamental von lose gekoppelten Ansaetzen wie Cartographer, die Sensordaten unabhaengig verarbeiten. Die enge Kopplung nutzt:
- **LiDAR-Linienmerkmale:** Line-to-Line Alignment Constraints zwischen aktuellem und Referenz-Frame (Gl. 6)
- **IMU-Praeintegration:** Standardverfahren nach VINS-Mono zur Vermeidung wiederholter Integration (Gl. 7-8)
- **Rad-Odometrie-Beobachtungsmodell:** Inkrementelle Verschiebung, Richtungsaenderung und Pose-Variation (Gl. 9-10)
- **Ground Constraint:** Beschraenkt die Bewegung auf 3-DoF (x, y, Gier), was der Realitaet von Indoor-Robotern entspricht (Gl. 13)

### 2. Punkt-Linien-Feature-Extraktion aus 2D-LiDAR (S. 4-5)

Eine neuartige Methode extrahiert sowohl Linien als auch Eckpunkte aus 2D-LiDAR-Scandaten:
- Scans werden anhand der Distanz zwischen Nachbarpunkten in kontinuierliche Punktmengen unterteilt
- Winkelbasierte Segmentierung mit Non-Maximum Suppression (NMS) identifiziert Liniensegmente
- Least-Squares-Fitting (A^T * P = 0) bestimmt die Liniengleichung (Gl. 3)
- Stabile Eckpunkte werden aus dem Schnittpunkt benachbarter Linien gewonnen
- Linien dienen dem Front-End-Tracking, Eckpunkte der Loop-Closure-Erkennung

### 3. Referenz-Frame-Verwaltung mit Sliding Window (S. 7)

Ein duales Referenz-Frame-System (aktuelles + Backup) verwaltet die Kartendaten:
- Liniendaten des aktuellen Frames werden auf das Referenz-Frame projiziert
- Bei 50% Fuellstand wird das Backup synchron aktualisiert
- Bei vollem Referenz-Frame wird das Backup zum neuen Referenz-Frame
- Dieses Vorgehen adressiert das Problem unzureichender Daten in einzelnen Scans

### 4. Globale Feature-Point-basierte Loop-Closure-Erkennung (S. 7-8)

Anstelle gaengiger visueller Deskriptoren (ORB, SIFT), die fuer texturarme 2D-Scans ungeeignet sind, wird ein geometrischer Ansatz verwendet:
- Eckpunkte werden als globale Feature-Punkte genutzt
- Deskriptoren basieren auf Distanz- und Winkelbeziehungen zwischen Eckpunkten (Gl. 16-17)
- Diskretisierung mit Distanz- und Winkelaufloesung (d_res, a_res) fuer Rauschrobustheit
- **Randomisierte Matching-Strategie** reduziert die Komplexitaet um mindestens 75% (bei p=0.95, m=20, c=10) gegenueber vollstaendigem Matching (Gl. 18-19)
- Das Matching liefert Punktpaare fuer eine nichtlineare Least-Squares-Optimierung zur Relativpose (Gl. 20)

### 5. Experimentelle Ergebnisse: Ueberlegenheit gegenueber Cartographer und Gmapping (S. 9-11)

Evaluation auf dem OpenLORIS-Scene-Datensatz (Office, Home, Cafe, Corridor):

**Absolute Pose Error (APE) RMSE (Tabelle 2):**
| Methode | Office | Home | Cafe | Corridor |
|---|---|---|---|---|
| Gmapping | 0.063 | 0.111 | 0.174 | 0.145 |
| Cartographer | 0.096 | 0.114 | 0.176 | 0.129 |
| 2DLIW-SLAM | **0.060** | **0.115** | **0.170** | **0.126** |

**Relative Pose Error (RPE) RMSE (Tabelle 3):**
| Methode | Office | Home | Cafe | Corridor |
|---|---|---|---|---|
| Gmapping | 0.026 | 0.040 | 0.049 | 0.108 |
| Cartographer | 0.027 | 0.027 | 0.040 | 0.027 |
| 2DLIW-SLAM | **0.020** | **0.023** | **0.032** | **0.026** |

2DLIW-SLAM erzielt in allen Szenen den niedrigsten RPE und uebertrifft auch visuelle SLAM-Systeme (ORB-SLAM3, VINS-Fusion) deutlich.

### 6. Robustheit bei Degenerationsproblemen (S. 10)

Bei eingeschraenkter LiDAR-Reichweite (3 m) im Korridor-Szenario (Simulation langer Flure):
- 2DLIW-SLAM: RPE RMSE = **0.027** (niedrigster Wert)
- Cartographer: RPE RMSE = 0.042
- Gmapping: RPE RMSE = 0.094
- Die enge Kopplung mit Rad-Odometrie staerkt die Widerstandsfaehigkeit des Front-Ends erheblich
- Bei begrenzter LiDAR-Reichweite (3 m) hat die Loop-Closure-Erkennung ueber Eckpunkte Schwierigkeiten, was zu Drift fuehrt

### 7. Echtzeit-Performance (S. 11, Tabelle 7)

Das Tracking-System erfuellt Echtzeitanforderungen fuer Indoor-Roboter:
- Bei Sliding-Window-Groesse 5 werden durchschnittlich >60 Frames/s erreicht
- Typische Indoor-Roboter benoetigen 20-30 Frames/s
- Linienextraktion: 42-65 Linien pro Frame
- Linien-Matching: 26-38 Matches pro Frame
- Tracking-Zeit: 9-15 ms pro Frame

### 8. Loop-Closure-Performance und globale Lokalisierung (S. 9, 11, Tabelle 4, 6)

**Globale Lokalisierung auf Deutsches-Museum-Datensatz (Tabelle 4):**
- 2DLIW-SLAM: **8.99 ms** Matching-Zeit (vs. AMCL: 661 ms, Cartographer: 1021 ms)
- Translation Error: 0.07 m, Rotation Error: 0.74 Grad (vergleichbar mit Cartographer)
- Zwei Groessenordnungen schneller als andere Methoden

**Feature-Point-Matching (Tabelle 6):**
- 15-40 Feature Points pro Frame in der Praxis
- Descriptor Matching: 0.03-1.98 us
- Frame-to-Frame Matching: 39-395 us
- Translation Error: 0.03-0.42 m, Rotation Error: 0.30-0.75 Grad

### 9. Bedeutung der Rad-Odometrie fuer Indoor-SLAM (S. 2)

Die Autoren argumentieren, dass Rad-Odometrie gegenueber IMU bei Indoor-Robotern Vorteile bietet:
- Indoor-Roboter bewegen sich langsam mit haeufigen Stopps - IMU-Performance leidet bei niedrigen Geschwindigkeiten
- Rad-Odometrie zeigt ueberlegene Performance bei stationaerem Roboter (kein Drift)
- Radstatus kann direkt aus Encoder-Informationen abgeleitet werden
- Fusion von 2D-LiDAR und Rad-Odometrie ist bisher wenig erforscht
- Die Dreierkombination LiDAR + IMU + Rad-Odometrie bietet die beste Kosten-Nutzen-Relation

## Relevanz fuer die Projektarbeit

### Direkte Relevanz

1. **Sensorfusion-Architektur:** Das Paper zeigt, wie Rad-Odometrie (Encoder) als dritter Sensor neben LiDAR und IMU den SLAM-Prozess verbessert. Dies validiert den Ansatz der Projektarbeit, Encoder-basierte Odometrie vom ESP32 an den Raspberry Pi fuer SLAM zu senden.

2. **Ground Constraint (3-DoF-Reduktion):** Die Beschraenkung auf 3-DoF (x, y, Gier) durch Ground Constraints ist direkt auf den Differentialantrieb-Roboter der Projektarbeit uebertragbar und erhoet die Robustheit der Zustandsschaetzung.

3. **Vergleich mit Cartographer:** Die Projektarbeit nutzt SLAM Toolbox (basierend auf aehnlichen Prinzipien wie Cartographer). Die quantitativen Ergebnisse zeigen, dass eng gekoppelte Ansaetze die Genauigkeit verbessern - relevant fuer die Diskussion der SLAM-Leistung.

4. **Degenerationsprobleme in Korridoren:** Die Analyse zeigt, dass lange Korridore (geometrisch aehnliche Umgebungen) ein Hauptproblem fuer 2D-LiDAR-SLAM sind. Die Rad-Odometrie hilft, dies abzumildern - ein Argument fuer zuverlaessige Encoder-Odometrie in der Projektarbeit.

### Indirekte Relevanz

5. **Echtzeit-Anforderungen:** Die Tracking-Zeiten von 9-15 ms pro Frame bestaetigen, dass die 50-Hz-Regelschleife (20 ms) des ESP32 der Projektarbeit im typischen Bereich fuer Indoor-SLAM liegt.

6. **Kartenaufloesung:** Die 5-cm-Kartenaufloesung der Projektarbeit entspricht dem Standard fuer 2D-Grid-Maps in der SLAM-Literatur.

### Abgrenzung

- 2DLIW-SLAM nutzt ein eigenes SLAM-Framework mit Joint Optimization, waehrend die Projektarbeit auf bestehende ROS2-Pakete (SLAM Toolbox, Nav2) setzt
- Die LiDAR-Eingabe bei 20-40 Hz ist hoeher als bei vielen kostenguenstigen LiDAR-Sensoren
- Die enge Kopplung erfordert erheblich mehr Implementierungsaufwand als die lose Kopplung ueber separate ROS2-Nodes
