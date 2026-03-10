# De Giorgi et al. (2024) -- Online Odometry Calibration in Low Traction Conditions with Slippage

## Bibliografische Angaben
- **Autoren:** Carlo De Giorgi, Daniela De Palma, Gianfranco Parlangeli
- **Venue:** Robotics 2024, 13(1), 7 (MDPI)
- **DOI/Link:** https://doi.org/10.3390/robotics13010007
- **Eingereicht:** 31. Oktober 2023, Angenommen: 22. Dezember 2023, Publiziert: 27. Dezember 2023
- **Institution:** Department of Engineering for Innovation, University of Salento, Lecce, Italien

## Zusammenfassung (Abstract)

Das Paper stellt eine systematische Online-Kalibrierungsmethode fuer die Odometrie von Differentialantrieb-Robotern vor, die explizit Schlupf (Slippage) beruecksichtigt. Der Algorithmus nutzt die Sensorredundanz aus Encodern, Gyroskopen und IMU, um Schlupf fruehzeitig zu erkennen und dessen Einfluss auf die Odometrie zu kompensieren. Waehrend Schlupfphasen werden Encoder-Daten durch IMU-basierte Bewegungsrekonstruktion ersetzt. Die Methode wurde durch umfangreiche MATLAB-Simulationen validiert und reduziert den Positionierungsfehler um bis zu Faktor 35 gegenueber unkompensiertem Schlupf.

## Kernaussagen

### 1. Kinematisches Modell des Differentialantriebs
- Das Bewegungsmodell basiert auf der Standard-Differentialantrieb-Kinematik mit zwei angetriebenen Raedern und einem passiven Stuetzrad (S. 4)
- Die kinematische Matrix C = [[r_R/2, r_L/2], [r_R/b, -r_L/b]] beschreibt die Abbildung von Raddrehgeschwindigkeiten (omega_R, omega_L) auf Lineargeschwindigkeit v und Drehrate omega (S. 4)
- r_R, r_L sind die Radradien des rechten/linken Rades, b ist die Spurbreite (Abstand der Radmittelpunkte) (S. 4)
- Die Vorwaertskinematik wird durch Runge-Kutta 2. Ordnung integriert, wobei die halbe Winkelaenderung als Mittelwert-Orientierung genutzt wird (S. 4)

### 2. Kategorisierung von Odometrie-Fehlern
- **Systematische Fehler:** Entstehen durch Bias im kinematischen Modell, Radgroessen-Abweichungen und Fehlausrichtung zwischen Sensoren und Roboterkoerper (S. 1-2)
- **Nicht-systematische Fehler:** Unvorhersehbar, entstehen waehrend des Betriebs durch Schlupf auf Oberflaechen mit niedrigem Reibungskoeffizienten (S. 1-2)
- Beide Fehlertypen fuehren zur Akkumulation von Positionsfehlern ueber die Zeit -- die Kalibrierung zielt darauf ab, systematische Fehler zu minimieren (S. 2)

### 3. Drei Kategorien der Odometrie-Kalibrierung (Literaturueberblick)
- **(i) Offline-Einmal-Kalibrierung:** Vordefinierte Testpfade vor der Inbetriebnahme, z.B. UMBmark von Borenstein & Feng (1994) als Pioniermethode -- Quadratpfad mit kombinierten Rotationen und Translationen (S. 2)
- **(ii) Online-Kalibrierung separat:** Kalibrierung waehrend des Normalbetriebs, z.B. Least-Squares-Ansatz von Antonelli et al. (2005) mit mehreren Trajektorien (S. 2-3)
- **(iii) Online-Kalibrierung integriert in Lokalisierung:** Kontinuierliche Aktualisierung der Parameter durch Sensorfusion (z.B. Kalman-Filter mit Laser, DGPS, Inertialdaten), benoetigt aber oft externe Positionierungssysteme (S. 3)
- Offline-Methoden erfordern erheblichen Platz und unterbrechen den Roboterbetrieb; die Durchfuehrung auf verschiedenen Untergruenden/Umgebungen ist schwierig (S. 2)

### 4. UMBmark als Referenzmethode
- UMBmark [5] von Borenstein & Feng (1994) wird als Pioniermethode der Odometrie-Kalibrierung referenziert (S. 2)
- Die Pfadgroesse beeinflusst die Kalibrierungsgenauigkeit -- Lee et al. [6] schlugen einen 2x2 m Quadratpfad vor (S. 2)
- Alternative Pfaddesigns: rotationsbasierte Ansaetze [7], Drei-Punkte-Methode [8], bidirektionaler kreisfoermiger Pfadtest (BCPT) [9], vereinfachte Geradlinien- und 180-Grad-Drehungen [10] (S. 2)

### 5. Neuartiger Beitrag: Aktive Schlupfkompensation
- Der Algorithmus erkennt Schlupf in Echtzeit und trennt bei Detektion die Encoder-Daten von der Kalibrierung (S. 3)
- Bei Schlupf wird eine IMU-basierte Bewegungsrekonstruktion aktiviert, die die Positionsaenderung waehrend der Schlupfphase schaetzt (S. 3)
- Der Ansatz nutzt ausschliesslich propriozeptive Sensoren (Encoder, Gyroskop, IMU) -- keine externen Positionierungssysteme noetig (S. 3)
- Der Algorithmus kann auf beliebigen Pfaden ausgefuehrt werden, die der Roboter waehrend normaler Operationen faehrt -- keine speziellen Kalibrierungspfade erforderlich (S. 3)
- Periodische Ausfuehrung moeglich, um zeitliche Aenderungen der kinematischen Matrix zu erfassen (S. 3)

### 6. Schlupferkennung mittels IMU
- **Lateraler Schlupf:** Wird durch inkonsistente laterale Beschleunigung a_y erkannt -- bei reinem Rollen muss die laterale Beschleunigung (nach Abzug der Gravitation ueber die Rotationsmatrix) null sein (Gl. 7, S. 6)
- **Frontaler Schlupf (Bremsen/Beschleunigung):** Wird durch Vergleich der aus Encoder-Differenzen berechneten Beschleunigung mit der IMU-Laengsbeschleunigung erkannt (Gl. 8, S. 6)
- Toleranzschwellen epsilon_L^IMU und epsilon_F^IMU muessen basierend auf IMU-Datenblatt (Bias-Stabilitaet, Rauschen) gesetzt werden (Gl. 9-10, S. 6-7)
- Zur Vermeidung von Fehlalarmen durch Rauschen wird die Schlupfbedingung ueber mehrere aufeinanderfolgende Zeitschritte geprueft statt nur einmal (S. 7)

### 7. IMU-basierte Bewegungsrekonstruktion bei Schlupf
- Waehrend Schlupf gibt es keine Reibung zwischen Raedern und Boden -- das kinematische Radmodell ist ungueltig (S. 7)
- Die Orientierungsaenderung Delta-theta wird waehrend Schlupfphasen vom Gyroskop geliefert (Genauigkeit in der Groessenordnung 0,1 Grad) (S. 7)
- Die Positionsaenderung (Delta-x^s, Delta-y^s) wird durch ein gleichmaessig beschleunigtes Bewegungsmodell aus IMU-Beschleunigungsdaten rekonstruiert (Gl. 12-13, S. 7)
- Die Geschwindigkeit am Beginn des Schlupfsegments wird aus den letzten gultigen Encoder-Daten uebernommen (S. 7)

### 8. Least-Squares Parameterschaetzung
- Die vier Elemente c_11, c_12, c_21, c_22 der kinematischen Matrix C werden per Batch-Least-Squares aus P Trajektorien geschaetzt (S. 8-9, Appendix A)
- Statt die drei physikalischen Parameter (r_R, r_L, b) einzeln nichtlinear zu schaetzen, werden die vier Matrix-Elemente als unabhaengig behandelt -- dies fuehrt zu einem linearen Identifikationsproblem (S. 20)
- Die Regressoren Phi_xy und Phi_theta werden aus Encoder-Messungen und integrierten Orientierungen berechnet (Gl. 22-23, S. 9)
- Schlupf-Segmente werden durch IMU-rekonstruierte Verschiebungen (Delta-x^s, Delta-y^s, Delta-theta^s) ersetzt -- die korrigierten Endpositionen theta', x', y' werden als modifizierte Beobachtungen verwendet (Gl. 17, S. 8)
- Die physikalische Nebenbedingung c_11/c_12 = -c_21/c_22 (d.h. gleiche Radradien-Verhaeltnisse) wird in der Schaetzung nicht erzwungen, koennte aber nachtraeglich eingebaut werden (S. 21)

### 9. Simulationsparameter und -ergebnisse
- Simulation in MATLAB mit 50x40 m Gitterumgebung, RRT-Dubins und PRM Pfadplaner, P=12 Trajektorien (S. 10)
- Wahre kinematische Matrix: C = [[0.0750 m, 0.0750 m], [0.0833, -0.0833]] (entspricht r_R = r_L = 0.15 m, b = 0.6 m) (S. 11)
- Abtastperiode Delta_t = 0.1 s; Gyroskoprauschen SNR = 30 dB; Encoder-Rauschen SNR = 50 dB (S. 10-11)
- Schlupf wird durch Modifikation der Geschwindigkeiten simuliert: x-Geschwindigkeit mit Faktor alpha=2, y-Geschwindigkeit mit Faktor alpha=-0.2 (S. 10)
- Schlupfdauern T_s = 10 s, 6 s, 4 s getestet (S. 14)

### 10. Quantitative Ergebnisse: Fehlerreduktion
- **Ohne Schlupfkompensation (suc):** Parameterfehler c_11 in der Groessenordnung 5-6 x 10^-2 m (S. 11, Tabelle 1)
- **Mit Schlupfkompensation (sc):** Parameterfehler c_11 reduziert auf 1.7 x 10^-4 m -- fast so gut wie das schlupffreie Szenario (7.5 x 10^-4 m) (S. 11, Tabelle 1)
- Positionierungsfehler-Reduktion um Faktor 35.64 (PE_suc / PE_sc) bei T_s = 10 s, und um Faktor 13.46 bei T_s = 6 s (S. 18, Tabelle 8)
- Auch bei verrauschten Messungen: Fehlerreduktion um Faktor 23.04 (T_s=10 s) bzw. 15.71 (T_s=6 s) (S. 18, Tabelle 8)
- Der durchschnittliche Positionsfehler PE sinkt von >1.3 m (unkompensiert) auf <0.06 m (kompensiert) bei T_s = 10 s (S. 18, Tabelle 7)

### 11. Einfluss der Schlupfdauer
- Laengere Schlupfphasen (groesseres T_s) verschlechtern die Schaetzung, da die IMU-basierte Rekonstruktion ueber laengere Zeit integriert und Drift akkumuliert (S. 14, Tabelle 5)
- Dennoch: Selbst bei erheblichem Schlupf (T_s = 10 s) und verrauschten Sensoren bleibt die kompensierte Schaetzung nahe am realen Wert (S. 14)

### 12. Einfluss der Pfadplanerart
- RRT-Dubins-Pfade (gekruemmte Trajektorien) liefern leicht bessere Kalibrierungsergebnisse als PRM-Pfade (geradliniger mit abrupten Kurven) (S. 13)
- Bei Pfaden mit signifikanten Orientierungsaenderungen wird eine Verbesserung der Schaetzung beobachtet (S. 13)
- Mehr analysierte Pfade (groesseres P) verbessern die Schaetzung unabhaengig vom Planer (S. 13)

### 13. Robustheit gegen nicht-gausssches Rauschen
- Der Algorithmus wurde auch mit Heavy-Tailed-Rauschen (Cauchy-artig) und Unknown-But-Bounded (UBB) Rauschen auf dem IMU-Signal getestet (S. 16-17)
- Bei T_s = 6 s mit Heavy-Tailed-Rauschen: c_11 Fehler bei kompensiertem Szenario nur 0.0784 m vs. wahre 0.0750 m (S. 17, Tabelle 6)
- Der Algorithmus zeigt anhaltende Wirksamkeit auch bei nicht-idealem Rauschen (S. 16)

### 14. Sensitivitaetsanalyse der Rauschquellen
- Orientierungsrauschen (theta, vom Gyroskop) hat den groessten negativen Einfluss auf die Kalibrierungsgenauigkeit (S. 15)
- Schlupf-Verschiebungsrauschen (Delta_x^s, Delta_y^s, von Gyroskop und IMU) hat ebenfalls erheblichen Einfluss (S. 15)
- Rauschen auf einzelnen Radgeschwindigkeiten hat minimalen Einfluss auf die Kalibrierung (S. 15)

### 15. Validierung: Position und Orientierungsfehler
- Vier Fehlermetriken definiert: mittlerer Positionsfehler PE, Endpositionsfehler PE_n, mittlerer Orientierungsfehler OE, End-Orientierungsfehler OE_n (Gl. 25-28, S. 17)
- Kompensiertes Szenario (sc): PE = 0.0371 m, PE_n = 0.0675 m bei T_s = 10 s (S. 18, Tabelle 7)
- Unkompensiertes Szenario (suc): PE = 1.3226 m, PE_n = 1.7727 m -- ueber 1 m Positionsfehler! (S. 18, Tabelle 7)
- Orientierungsfehler steigt durch Kompensation leicht an (OE_sc = 7.97 x 10^-4 rad vs. OE_ns ~0), die Positionsverbesserung ueberwiegt jedoch deutlich (S. 18)

### 16. Limitationen und zukuenftige Arbeiten
- Die Validierung erfolgte ausschliesslich in Simulation -- experimentelle Tests mit echten Robotern stehen noch aus (S. 19)
- Die Methode benoetigt bekannte Anfangs- und Endposen (z.B. durch exteroceptive Sensoren) fuer jede Kalibrierungstrajektorie (Annahme A4, S. 5)
- Erweiterung auf andere Kinematiken geplant: Dreirad, omnidirektional, Ackermann-Lenkung (S. 19)
- Integration mit anderen Fehlererkennungs- und Kompensationsalgorithmen als zukuenftige Arbeit genannt (S. 19)

## Relevanz fuer die Projektarbeit

Die Projektarbeit nutzt die UMBmark-Methode (Offline-Einmal-Kalibrierung) fuer den Differentialantrieb-Roboter mit Radradius 32 mm und Spurbreite 145 mm. De Giorgi et al. liefern den theoretischen Rahmen fuer das kinematische Modell und die C-Matrix-Parametrisierung, die direkt der in der Firmware implementierten Vorwaerts-/Inverskinematik (diff_drive_kinematics.hpp) entspricht. Besonders relevant ist die Erkenntnis, dass Schlupf den groessten Stoerfaktor bei der Encoder-basierten Odometrie darstellt und dass die Kompensation den Positionsfehler um eine Groessenordnung reduzieren kann -- dies sollte bei der UMBmark-Auswertung (Kap. 5.4) und der Validierung im 10x10 m Testparcours (Kap. 6) diskutiert werden. Die Sensitivitaetsanalyse zeigt zudem, dass Gyroskoprauschen kritischer ist als Encoderrauschen, was fuer die Bewertung einer moeglichen Gyro-Fusion im Nav2-Stack (EKF) bedeutsam ist.
