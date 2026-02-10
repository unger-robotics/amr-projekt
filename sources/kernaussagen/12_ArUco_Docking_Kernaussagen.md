# Kernaussagen: Regression-Based Docking System for Autonomous Mobile Robots Using a Monocular Camera and ArUco Markers

## Bibliografische Angaben

- **Autoren:** Jun Seok Oh, Min Young Kim
- **Titel:** Regression-Based Docking System for Autonomous Mobile Robots Using a Monocular Camera and ArUco Markers
- **Journal:** Sensors (MDPI), 2025, 25, 3742
- **DOI:** https://doi.org/10.3390/s25123742
- **Veröffentlicht:** 15. Juni 2025
- **Typ:** Peer-reviewed Journalartikel (Open Access, CC BY)

---

## Zusammenfassung

Die Studie stellt ein kostenguenstiges autonomes Docking-System fuer AMRs vor, das ausschliesslich eine monokulare Kamera und ArUco-Marker nutzt. Statt der konventionellen SolvePnP-Methode wird ein regressionsbasierter Ansatz vorgeschlagen, der die geometrischen Veraenderungen der ArUco-Marker (Groesse und Form) in Kamerabildern nutzt, um Tiefe (Distanz), Orientierung und lateralen Versatz zu schaetzen. Das Training erfolgt mit LiDAR-Ground-Truth-Daten, die Inferenz arbeitet nur mit der Kamera. Die Methode erreicht einen mittleren Distanzfehler von 1.18 cm und einen Orientierungsfehler von 3.11 Grad -- deutlich besser als SolvePnP (58.54 cm / 6.64 Grad). Im realen Docking-Test wird eine Positionsgenauigkeit von ca. 2 cm und ein Orientierungsfehler von 3.07 Grad erreicht.

---

## Kernaussagen

### 1. Problemstellung: Limitationen von SolvePnP (S. 2, 11)

- SolvePnP ist der Standardansatz fuer Pose-Schaetzung mit ArUco-Markern, zeigt aber erhebliche Schwaechen: (S. 2)
  - Tiefenschaetzung verschlechtert sich stark mit zunehmender Distanz
  - Perspektivische Verzerrung bei schraegen Blickwinkeln reduziert die Orientierungsgenauigkeit
  - Empfindlichkeit gegenueber Beleuchtungsschwankungen und Bildrauschen
  - Geometrische Tiefenschaetzung statt direkter Messung -- kleine Kalibrierungsfehler haben grosse Auswirkungen
- SolvePnP funktioniert bei kurzen Distanzen (<1.0 m) akzeptabel, produziert aber bei typischen Docking-Distanzen (1.0-2.0 m) Fehler ueber 0.6 m. (S. 12-13)

### 2. Regressionsbasierter Ansatz -- Konzept (S. 3-5)

- **Tiefenschaetzung:** Die beobachtete Groesse des ArUco-Markers im Bild (in Pixeln) aendert sich nichtlinear mit der Distanz. Ein Regressionsmodell lernt diesen Zusammenhang. Ein einziges globales Modell fuer den gesamten Tiefenbereich (25-250 cm). (S. 4)
- **Orientierungsschaetzung:** Die Formverzerrung des Markers (Differenz zwischen gegenueberliegenden Kanten) aendert sich mit dem Blickwinkel. (S. 4, Fig. 4)
- **Segmentierte Regression fuer Orientierung:** Gleiche Winkelveraenderung erzeugt unterschiedliche Verzerrungen bei verschiedenen Tiefen. Loesung: Tiefenbereich in 5-cm-Intervalle segmentieren, fuer jedes Intervall ein eigenes Orientierungsmodell trainieren. Insgesamt 45 Segmente, je 7 Modelle evaluiert = 315 Modelle. (S. 5, 7, Fig. 6)
- **Lateraler Versatz:** Berechnung via Triangulation aus geschaetzter Tiefe und Pixel-Versatz des Markerzentrums zur Bildmitte mittels Pinhole-Kameramodell: K = (Z * P) / f. (S. 15, Gl. 6)

### 3. Training und Modellauswahl (S. 6-9)

- **Ground-Truth-Akquisition:** Monokulare Kamera und 2D-LiDAR synchronisiert. LiDAR-Daten werden via extrinsische Kalibrierung (Schachbrettmuster, 8x6) auf die Bildebene projiziert, um praezise Distanz- und Orientierungs-Labels zu erhalten. (S. 6, Fig. 7)
- **Sieben Regressionsmodelle evaluiert:** Linear Regression, Ridge Regression, Lasso Regression, Decision Tree, Random Forest, SVR, Gradient Boosting. (S. 7)
- **Bestes Tiefenmodell: Random Forest** mit MSE = 0.0009 und R-Quadrat = 0.9937 (S. 7-8, Table 1)
- **Orientierung: Wechselnde beste Modelle je Segment** -- Random Forest dominiert bei mittleren/grossen Distanzen, Gradient Boosting bei kurzen Distanzen, Decision Tree bei einzelnen Intervallen. Durchschnitt: MSE = 1.5185, R-Quadrat = 0.915 ueber alle 45 Segmente. (S. 8-9, Table 2)

### 4. Vergleich mit SolvePnP -- Distanzschaetzung (S. 12-13, Table 4, Fig. 12)

| Metrik | Vorgeschlagenes System | SolvePnP |
|---|---|---|
| **Mittlerer Distanzfehler** | **1.18 cm** | **58.54 cm** |

- SolvePnP zeigt bei Distanzen >1.0 m Fehler von ueber 0.6 m, teilweise bis 3.34 m. (S. 12, Table 4)
- Das vorgeschlagene System haelt einen stabilen mittleren Fehler von ca. 1 cm ueber den gesamten Distanzbereich. (S. 12-13)
- Der Faktor der Verbesserung betraegt ca. 50x (1.18 cm vs. 58.54 cm). (S. 12, Fig. 12b)

### 5. Vergleich mit SolvePnP -- Orientierungsschaetzung (S. 13-15, Table 5, Fig. 13)

| Metrik | Vorgeschlagenes System | SolvePnP |
|---|---|---|
| **Mittlerer Orientierungsfehler** | **3.11 Grad** | **6.64 Grad** |

- SolvePnP zeigt grosse Streuung: einzelne Abweichungen >10 Grad, teils >15 Grad (z.B. Index 3: 28.37 Grad, Index 10: 19.59 Grad). (S. 14, Table 5)
- Das vorgeschlagene System haelt die meisten Fehler unter +/-5 Grad. (S. 15)
- Verbesserung um ca. Faktor 2 im Mittelwert, deutlich stabiler in der Streuung. (S. 14, Fig. 13b)

### 6. Reales Docking-Ergebnis (S. 16, Fig. 16)

- **Docking-Ablauf in 3 Schritten:** (S. 16)
  1. Distanz- und Orientierungsschaetzung zum Marker
  2. Drehung des Roboters zur senkrechten Ausrichtung
  3. P-Regler (Proportional Control) fuer Feinpositionierung
- **8 vordefinierte Docking-Strategien** je nach relativer Pose zum Marker. (S. 15-16, Fig. 15)
- **Gemessener Docking-Fehler:** 19 cm Distanzfehler roh, davon 17 cm durch Kamera-Offset zum Roboterrand erklaert -> **korrigierter Positionsfehler: ca. 2 cm**, Orientierungsfehler: 3.07 Grad. (S. 16)
- Praezision genuegt fuer industrielle Logistik- und Ladeanwendungen. (S. 17)

### 7. Laterale Distanzberechnung (S. 15, Fig. 14)

- ArUco Marker 2 wird mittig an der Docking-Station platziert. (S. 15)
- Laterale Distanz K berechnet sich aus: K = (Z * P) / f, wobei Z die geschaetzte Tiefe, P der Pixel-Versatz und f die Brennweite ist. (S. 15, Gl. 6)
- Diese Information ist essentiell fuer die Wahl der Docking-Strategie (links/rechts-Korrektur). (S. 15)

### 8. Systemvorteile und Einschraenkungen (S. 17)

**Vorteile:**
- Nur monokulare Kamera zur Laufzeit noetig -- kostengünstig und skalierbar. (S. 17)
- LiDAR nur fuer Training erforderlich, nicht fuer den Betrieb. (S. 3, 17)
- Leistung vergleichbar mit LiDAR-basierten Systemen bei Docking-Praezision (~2 cm). (S. 17)
- Robust gegenueber Distanzvariation und schraegen Blickwinkeln (anders als SolvePnP). (S. 17)

**Einschraenkungen:**
- Erfordert praezise Kamera-Sensorkalibrierung. (S. 17)
- Stabile Beleuchtung notwendig -- variierende Lichtverhaeltnisse koennen Leistung beeintraechtigen. (S. 17)
- Training mit LiDAR-Ground-Truth setzt initialen Kalibrierungsaufwand voraus. (S. 6)

---

## Relevanz fuer die Bachelorarbeit

### Direkt anwendbar (Kap. 5.5 -- Docking, Kap. 6.4 -- Diskussion)

1. **Validation des ArUco-Docking-Konzepts:** Die BA implementiert ein ArUco-Marker-basiertes Docking-System (`aruco_docking.py` mit OpenCV). Die Studie liefert quantitative Evidenz, dass ArUco-basiertes Docking mit monokularer Kamera industrietaugliche Praezision (~2 cm Positionsfehler, ~3 Grad Orientierungsfehler) erreichen kann.

2. **Benchmark-Werte als Referenz:** Der mittlere Distanzfehler von 1.18 cm und Orientierungsfehler von 3.11 Grad koennen als Vergleichswerte fuer die eigene Docking-Implementierung herangezogen werden.

3. **SolvePnP-Limitationen dokumentiert:** Falls die BA SolvePnP nutzt (OpenCV-Standard fuer ArUco-Pose-Schaetzung), sind die dokumentierten Schwaechen (58.54 cm mittlerer Fehler bei typischen Docking-Distanzen) relevant fuer die Diskussion und Fehleranalyse.

4. **Segmentierter Regressionsansatz als Alternative:** Die Idee, den Tiefenbereich in 5-cm-Intervalle zu segmentieren und je Segment optimale Modelle zu waehlen, koennte als Verbesserungsvorschlag in der Diskussion der BA erwaehnt werden.

5. **Docking-Strategie mit Fallunterscheidung:** Die 8 vordefinierten Docking-Cases (Fig. 15) und der 3-Schritt-Ablauf (Schaetzung -> Drehung -> P-Regler-Feinpositionierung) bieten eine strukturierte Methodik, die mit dem Visual-Servoing-Ansatz der BA verglichen werden kann.

6. **Hardware-Kostenargument:** Die Studie unterstreicht, dass monokulare Kamera + ArUco eine kostenguenstige Alternative zu LiDAR-basiertem Docking ist -- relevant fuer die Begruendung der Sensorauswahl in der BA.

7. **Laterale Distanzberechnung:** Die Triangulations-Formel K = (Z * P) / f (Gl. 6) fuer den lateralen Versatz ist direkt fuer die BA-Implementierung nutzbar oder als Vergleichsmethode zitierfaehig.
