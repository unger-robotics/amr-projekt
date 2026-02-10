# Siegwart, Nourbakhsh (2004) -- Introduction to Autonomous Mobile Robots

## Bibliografische Angaben
- **Autoren:** Roland Siegwart, Illah R. Nourbakhsh
- **Venue:** MIT Press (A Bradford Book), 1. Auflage, 2004
- **ISBN:** 0-262-19502-X
- **Hinweis:** 2. Auflage (2011) mit Davide Scaramuzza als Ko-Autor; Kinematik-Kapitel (Kap. 3) und Odometrie-Abschnitte (Kap. 5.2) weitgehend identisch

## Kernaussagen aus Kapitel 3: Mobile Robot Kinematics

### 1. Positionsrepraesentation im 2D-Raum
- Ein mobiler Roboter wird als starrer Koerper auf einer horizontalen Ebene modelliert. Seine Pose hat drei Dimensionen: zwei fuer die Position (x, y) und eine fuer die Orientierung (theta) (S. 48).
- Die Pose wird als Vektor dargestellt: xi_I = [x, y, theta]^T im globalen Referenzrahmen {X_I, Y_I} (Gl. 3.1, S. 49).
- Die Abbildung zwischen globalem und lokalem (roboterfestem) Referenzrahmen erfolgt ueber die **orthogonale Rotationsmatrix** R(theta) (Gl. 3.2, S. 50):
  ```
  R(theta) = [cos(theta)  sin(theta)  0]
              [-sin(theta) cos(theta)  0]
              [0           0           1]
  ```
- Diese Matrix ist orthogonal, daher gilt: R(theta)^(-1) = R(theta)^T (S. 53).

### 2. Vorwaertskinematik des Differentialantriebs
- Fuer einen Differentialantrieb mit zwei Raedern (Radius r, Abstand 2l zum Mittelpunkt P) wird die Vorwaertskinematik aus den Einzelbeitraegen beider Raeder im lokalen Referenzrahmen hergeleitet (S. 51-52).
- Translationsgeschwindigkeit entlang X_R (Vorwaertsrichtung): Jedes Rad traegt (1/2) * r * phi_dot bei. In Summe: x_R_dot = (r * phi_1_dot)/2 + (r * phi_2_dot)/2 (S. 52).
- Seitliche Geschwindigkeit entlang Y_R ist immer Null (keine laterale Bewegung moeglich) -- dies ist die **nichtholonome Zwangsbedingung** (S. 52).
- Rotationsgeschwindigkeit um P: omega_1 = r * phi_1_dot / (2l) fuer das rechte Rad (Gegenuhrzeigersinn), omega_2 = -r * phi_2_dot / (2l) fuer das linke Rad (S. 52).
- Zusammengefasstes kinematisches Modell (Gl. 3.9, S. 52):
  ```
  xi_I_dot = R(theta)^(-1) * [r*phi_1_dot/2 + r*phi_2_dot/2]
                               [0                              ]
                               [r*phi_1_dot/(2l) - r*phi_2_dot/(2l)]
  ```
- **Fuer die Bachelorarbeit:** Mit Radradius r = 32 mm und Spurbreite b = 2l = 145 mm ergeben sich die konkreten Kinematik-Gleichungen direkt aus dieser allgemeinen Form.

### 3. Rad-Zwangsbedingungen (Rolling und Sliding Constraints)
- Jeder Radtyp bringt zwei kinematische Zwangsbedingungen ein (S. 53-54):
  1. **Rolling Constraint** (Rollbedingung): Alle Bewegung entlang der Radebene muss durch Raddrehung realisiert werden -- reines Abrollen am Kontaktpunkt (Gl. 3.12).
  2. **Sliding Constraint** (Gleitbedingung): Keine laterale Bewegung orthogonal zur Radebene (Gl. 3.13).
- Vier Radtypen werden unterschieden: Fixed Standard Wheel, Steered Standard Wheel, Castor Wheel, Swedish Wheel. Nur die ersten beiden bringen **echte kinematische Zwangsbedingungen** fuer das Roboter-Chassis ein (S. 61).
- Castor-, Swedish- und Kugelraeder erzwingen **keine** Beschraenkungen der Chassis-Bewegung, da ihre internen Freiheitsgrade jede Chassis-Geschwindigkeit erlauben (S. 61).

### 4. Differentialantrieb als Constraint-Beispiel
- Die beiden Antriebsraeder des Diff-Drive sind Fixed Standard Wheels mit paralleler Achse. Zusammen mit der Castor-Stuetzrolle ergibt sich (Gl. 3.28-3.30, S. 63-64):
  ```
  [1  0   l ] [J_2 * phi]
  [1  0  -l ] R(theta) * xi_I_dot = [        ]
  [0  1   0 ]                       [   0    ]
  ```
- Invertierung liefert das **vollstaendige kinematische Modell** (Gl. 3.30, S. 64):
  ```
  xi_I_dot = R(theta)^(-1) * [1/2   1/2   0] * [J_2 * phi]
                               [0     0     1]   [   0     ]
                               [1/(2l) -1/(2l) 0]
  ```

### 5. Instantaneous Center of Rotation (ICR)
- Jedes Standard-Rad definiert eine **Zero Motion Line** senkrecht zur Radebene. Die Gleitbedingung erzwingt, dass keine Bewegung entlang dieser Linie stattfindet (S. 67-68).
- Der **ICR** (Instantaneous Center of Rotation) ist der Punkt, an dem sich alle Zero Motion Lines schneiden. Er beschreibt den momentanen Drehpunkt der Roboterbewegung (S. 67-68).
- Beim Differentialantrieb liegt der ICR immer auf der Verlangerlinie der gemeinsamen Radachse. Durch Variation der Radgeschwindigkeiten wird der ICR auf dieser Linie verschoben (S. 68-69):
  - Gleiche Geschwindigkeit beider Raeder: ICR im Unendlichen -> Geradeausfahrt
  - Gegenlaeufige gleiche Geschwindigkeit: ICR in der Mitte -> Drehung auf der Stelle
  - Unterschiedliche Geschwindigkeiten: ICR zwischen Mitte und Unendlich -> Kurvenfahrt

### 6. Mobilitaet, Lenkbarkeit und Manoevrierfaehigkeit
- **Degree of Mobility** delta_m = dimN[C_1(beta_s)] = 3 - rank[C_1(beta_s)] (Gl. 3.40, S. 71). Gibt die Anzahl der Freiheitsgrade an, die direkt ueber Radgeschwindigkeiten steuerbar sind.
- **Degree of Steerability** delta_s = rank[C_1s(beta_s)] (Gl. 3.41, S. 71). Gibt die Anzahl unabhaengig lenkbarer Raeder an.
- **Degree of Maneuverability** delta_M = delta_m + delta_s (Gl. 3.42, S. 72). Gesamte Steuerfreiheitsgrade.
- **Differentialantrieb:** delta_m = 2, delta_s = 0, delta_M = 2. Beide Raeder teilen eine Achse, daher rank[C_1(beta_s)] = 1. Der Roboter kann Vorwaerts-/Rueckwaertsgeschwindigkeit und Orientierungsaenderung direkt steuern (S. 71).
- Fuenf grundlegende Konfigurationstypen (Fig. 3.14, S. 73):
  - Omnidirectional: delta_M = 3, delta_m = 3, delta_s = 0
  - **Differential Drive: delta_M = 2, delta_m = 2, delta_s = 0**
  - Omni-Steer: delta_M = 3, delta_m = 2, delta_s = 1
  - Tricycle: delta_M = 2, delta_m = 1, delta_s = 1
  - Two-Steer: delta_M = 3, delta_m = 1, delta_s = 2

### 7. Holonomie und nichtholonome Zwangsbedingungen
- Ein **holonomischer Roboter** hat keine nichtholonomen Zwangsbedingungen, d.h. DDOF = DOF. Er kann jede Pose direkt erreichen (S. 75-77).
- Ein **nichtholonomischer Roboter** (wie der Differentialantrieb) hat DDOF < DOF: Er hat 2 differenzielle Freiheitsgrade (DDOF = delta_m = 2), kann aber trotzdem jede Pose im 3D-Workspace (DOF = 3) erreichen -- allerdings nicht auf beliebigen Pfaden (S. 75).
- Die Gleitbedingung ist eine nichtholonome Zwangsbedingung, da sie von der Ableitung der Pose (xi_dot) abhaengt und nicht integrierbar ist (S. 76).
- **Konsequenz fuer die Bachelorarbeit:** Der Differentialantrieb ist nichtholonom. Er kann jede (x, y, theta)-Pose erreichen, benoetigt aber Manoever (z.B. auf der Stelle drehen) fuer laterale Bewegung.

### 8. Motion Control (Kinematische Regelung)
- **Open-Loop Control:** Trajektorie wird in Geraden- und Kreissegmente zerlegt. Nachteil: Keine Fehlerkorrektur, unstetiges Beschleunigungsprofil an Segmentuebergaengen (S. 81-82).
- **Feedback Control:** Zustandsregler minimiert den Posefehler e = [x, y, theta]^T im Roboterrahmen. Steuervariablen sind Translationsgeschwindigkeit v(t) und Rotationsgeschwindigkeit omega(t) (Gl. 3.45-3.46, S. 83).
- Fuer die Regleranwendung genuegt ein Unicycle-Modell des Differentialantriebs mit den Eingaengen v und omega (Fig. 3.17, S. 81).

## Kernaussagen aus Kapitel 5: Mobile Robot Localization

### 1. Die vier Bausteine der Navigation
- Erfolgreiche Navigation erfordert: **Perception** (Sensorinterpretation), **Localization** (Positionsbestimmung), **Cognition** (Entscheidungsfindung) und **Motion Control** (Motoransteuerung) (S. 181).
- Lokalisierung hat die groesste Forschungsaufmerksamkeit erhalten und umfasst die allgemeine Schleife: Encoder -> Odometrie-Praediktion -> Abgleich mit Sensorbeobachtungen -> Positions-Update (Fig. 5.2, S. 182).

### 2. Rauschquellen: Sensor Noise, Sensor Aliasing, Effector Noise
- **Sensor Noise:** Zufaellige Schwankungen in Sensormessungen (z.B. Beleuchtungsaenderungen bei Kameras, Multipath-Interferenz bei Sonar). Loesung: Temporale Fusion, Multisensor-Fusion (S. 183-184).
- **Sensor Aliasing:** Verschiedene Umgebungszustaende erzeugen identische Sensorwerte -- das Mapping Umwelt->Sensordaten ist nicht injektiv. Ein einzelner Messwert reicht nie zur Lokalisierung (S. 184).
- **Effector Noise:** Roboterbewegungen sind nicht deterministisch. Ursachen: Bodenbeschaffenheit, Radschlupf, externe Stoerungen. Aus Robotersicht aeussert sich dies als Odometriefehler (S. 185).

### 3. Odometrie-Fehlerquellen (Differentialantrieb)
- Fehlerquellen bei der Odometrie (S. 185-186):
  - Begrenzte Integrationsaufloesung (Zeitinkrement, Messaufloesung)
  - **Fehlausrichtung der Raeder** (deterministisch/systematisch)
  - **Unsicherheit im Raddurchmesser**, insbesondere ungleiche Raddurchmesser (deterministisch)
  - Variation des Kontaktpunkts am Rad
  - **Ungleicher Bodenkontakt** (Schlupf, nicht-planare Oberflaeche)
- Einteilung in **deterministische (systematische)** Fehler (durch Kalibrierung eliminierbar) und **nichtdeterministische (zufaellige)** Fehler (S. 186).

### 4. Drei geometrische Fehlertypen
- Aus geometrischer Sicht lassen sich Odometriefehler in drei Typen klassifizieren (S. 186):
  1. **Range Error (Wegfehler):** Fehler in der integrierten Pfadlaenge -> Summe der Radbewegungen
  2. **Turn Error (Drehfehler):** Aehnlich dem Wegfehler, aber fuer Drehungen -> Differenz der Radbewegungen
  3. **Drift Error:** Differenz der Radfehler fuehrt zu Orientierungsfehler
- **Orientierungsfehler dominieren langfristig:** Ein Winkelfehler Delta_theta nach d Metern Fahrt erzeugt einen lateralen Positionsfehler von d * sin(Delta_theta). Da der Winkelfehler kumuliert, waechst der Positionsfehler ueberproportional (S. 186).

### 5. Odometrie-Positionsfortschreibung (Dead Reckoning)
- Die diskrete Positionsfortschreibung fuer den Differentialantrieb lautet (Gl. 5.2-5.6, S. 186-187):
  ```
  Delta_theta = (Delta_s_r - Delta_s_l) / b
  Delta_s     = (Delta_s_r + Delta_s_l) / 2

  x' = x + Delta_s * cos(theta + Delta_theta/2)
  y' = y + Delta_s * sin(theta + Delta_theta/2)
  theta' = theta + Delta_theta
  ```
  Dabei sind Delta_s_r, Delta_s_l die Wegstrecken des rechten/linken Rades und b der Radabstand (Spurbreite).
- **Fuer die Bachelorarbeit:** Diese Gleichungen entsprechen exakt der Implementierung in `diff_drive_kinematics.hpp` mit b = 145 mm.

### 6. Fehlerfortpflanzungsmodell (Kovarianzmatrix)
- Die Kovarianzmatrix der Odometrie-Schaetzung wird ueber Fehlerfortpflanzung (Linearisierung erster Ordnung / Taylor-Entwicklung) berechnet (Gl. 5.9, S. 189):
  ```
  Sigma_p' = F_p * Sigma_p * F_p^T + F_Delta_rl * Sigma_Delta * F_Delta_rl^T
  ```
- **Kovarianzmatrix der Radbewegungen** (Gl. 5.8, S. 188):
  ```
  Sigma_Delta = [k_r * |Delta_s_r|   0                ]
                [0                    k_l * |Delta_s_l|]
  ```
  Die Fehlerkonstanten k_r, k_l repraesentieren die nichtdeterministischen Parameter der Motor-Boden-Interaktion. Deren Varianz ist proportional zur zurueckgelegten Distanz.
- **Jacobi-Matrizen** (Gl. 5.10-5.11, S. 189):
  - F_p = Jacobi nach der Pose p: Beschreibt, wie bestehende Poseunsicherheit propagiert
  - F_Delta_rl = Jacobi nach den Radinkrements: Beschreibt, wie neue Bewegungsunsicherheit einfliesst
- **Ergebnis** (Fig. 5.4-5.5, S. 190-191): Die Unsicherheitsellipsen wachsen **senkrecht zur Fahrtrichtung schneller** als in Fahrtrichtung, weil der Orientierungsfehler den lateralen Positionsfehler dominiert. Bei Kurvenfahrt rotiert die Hauptachse der Ellipse mit.

### 7. Lokalisierung erfordert externe Referenzen
- Reine Odometrie (Dead Reckoning) ist als alleinige Lokalisierungsmethode unzureichend, da der Positionsfehler unbeschraenkt waechst (S. 188, 191).
- Fuer langfristig stabile Lokalisierung sind externe Referenzmechanismen noetig, z.B. kartenbasierte Lokalisierung (AMCL), SLAM oder Landmarken (S. 191).
- **Fuer die Bachelorarbeit:** Deshalb wird Odometrie nur als Praediktion im Nav2-Stack (AMCL) verwendet, waehrend SLAM Toolbox und LiDAR-basierte Korrekturen die Drift kompensieren.

## Relevanz fuer die Bachelorarbeit

1. **Kinematik-Herleitung (Kap. 3):** Siegwart liefert die theoretische Grundlage fuer die Differentialantrieb-Kinematik in `diff_drive_kinematics.hpp`. Die Vorwaertskinematik (Encoder -> Odometrie) und Inverskinematik (cmd_vel -> Radgeschwindigkeiten) sind direkt aus den Gleichungen 3.9 und 3.30 ableitbar.

2. **Nichtholonomie (Kap. 3):** Die nichtholonome Eigenschaft des Differentialantriebs (delta_M = 2, DOF = 3) begruendet, warum der Roboter spezielle Pfadplanungsalgorithmen benoetigt (Regulated Pure Pursuit in Nav2), die die Bewegungseinschraenkungen beruecksichtigen.

3. **ICR-Konzept (Kap. 3):** Das ICR-Konzept erklaert geometrisch, wie der Roboter Kurven faehrt und warum die Spurbreite b = 145 mm ein zentraler Parameter in der Kinematik ist.

4. **Odometrie-Fehlermodell (Kap. 5):** Die Fehlerfortpflanzung aus Gleichung 5.9 begruendet theoretisch, warum die Odometrie allein fuer Navigation unzureichend ist und Sensorfusion (LiDAR-SLAM) benoetigt wird.

5. **Systematische vs. zufaellige Fehler (Kap. 5):** Die Unterscheidung zwischen deterministischen (durch UMBmark-Kalibrierung eliminierbaren) und nichtdeterministischen Fehlern liefert die Motivation fuer das Kalibrierungsverfahren im Testparcours.

6. **Fehlertypen (Kap. 5):** Die Erkenntnis, dass Orientierungsfehler (Drift Error) den dominierenden Beitrag zum Gesamtfehler liefern, erklaert die besondere Bedeutung der exakten Spurbreiten-Kalibrierung (b = 145 mm) im UMBmark-Verfahren.
