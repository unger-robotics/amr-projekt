# Wie verändert sich die Laufzeit des Roboters bei einer zyklenoptimierten Ladeschlussspannung von 4,10 V/Zelle?

**Daten:** Die Nennenergie des 3S1P-Packs (Samsung INR18650-35E) beträgt exakt 36,18 Wh (10,8 V bei 3,35 Ah). Das zyklenoptimierte Ladeprofil mit 4,10 V/Zelle begrenzt die Maximalladung auf einen Bereich von 85 % bis 90 % der Nennkapazität. Die untere Entladegrenze zur Vermeidung von Degradation liegt bei einem SoC von 10 %.

**Regel:** Die nutzbare Energie ergibt sich aus dem nutzbaren Entladefenster. Wird der konservativere Wert von 85 % Ladezustand (SoC) bei Ladeschluss angenommen und die Zelle bis zum Limit von 10 % SoC entladen, resultiert ein nutzbares Entladefenster von 75 % der nominalen Gesamtenergie.

**Schluss:** Die zyklenoptimierte nutzbare Energie ($E_{\mathrm{nutz}}$) berechnet sich zu:

$$E_{\mathrm{nutz}} = 36{,}18\,\mathrm{Wh} \cdot 0{,}75 = 27{,}14\,\mathrm{Wh}$$

Im Vergleich zur ursprünglichen Berechnung (80 % Entladefenster, 28,94 Wh) reduziert sich die verfügbare Energiemenge um 1,80 Wh.

**Konsequenz:** Der Quotient aus der reduzierten Nutzenergie und der jeweiligen mittleren Systemleistung ($t = E_{\mathrm{nutz}} / P_{\mathrm{sys}}$) verkürzt die berechneten Laufzeiten in allen Betriebsmodi um durchschnittlich 6,2 %.

---

### Zyklenoptimierte Laufzeitberechnung

Die folgende Tabelle ordnet den dokumentierten Leistungsaufnahmen die neuen, zyklenoptimierten Laufzeiten zu:

| Betriebsmodus                                   | Mittlere Leistung | Laufzeit (zyklenoptimiert) | Laufzeitverlust |
|-------------------------------------------------|-------------------|----------------------------|-----------------|
| **Standby** (Pi + ESP32 + Sensorik, kein Hailo) | 6 W               | **4 h 31 min**             | - 18 min        |
| **Stillstand** (volle Pipeline, kein Antrieb)   | 12 W              | **2 h 16 min**             | - 9 min         |
| **Fahrbetrieb** (0,4 m/s, Navigation aktiv)     | 16 W              | **1 h 42 min**             | - 7 min         |
| **Maximallast** (Servos + Antrieb + Compute)    | 22 W              | **1 h 14 min**             | - 5 min         |

Die Reduktion der Ladeschlussspannung auf 12,30 V kostet im praxisrelevanten Fahrbetrieb rund 7 Minuten Laufzeit. Dieser marginale Laufzeitverlust steht der deutlich verlängerten Zyklenlebensdauer des Akkupacks gegenüber.
