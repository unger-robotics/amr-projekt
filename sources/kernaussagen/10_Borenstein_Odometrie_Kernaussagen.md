# Kernaussagen: Borenstein et al. 1996 -- "Where Am I?"

## Bibliografische Angaben

- **Titel**: Where Am I? Sensors and Methods for Mobile Robot Positioning
- **Autoren**: J. Borenstein, H. R. Everett, L. Feng
- **Herausgeber/Institution**: University of Michigan, Mobile Robotics Laboratory
- **Jahr**: April 1996
- **Typ**: Technischer Bericht (282 Seiten), erstellt fuer Oak Ridge National Lab (ORNL) D&D Program und U.S. Department of Energy
- **Quelle**: /sources/09_Borenstein_1996_Where_Am_I.pdf

## Zusammenfassung

Dieser umfassende technische Bericht ist das Standardwerk zur Positionierung mobiler Roboter. Er behandelt in zwei Hauptteilen (Part I: Sensoren, Part II: Systeme und Methoden) das gesamte Spektrum von Dead Reckoning ueber Heading-Sensoren, GPS, Range-Sensoren bis hin zu Map-Based und Vision-Based Positioning. Fuer die Projektarbeit besonders relevant sind Kapitel 1 (Sensoren fuer Dead Reckoning, insbesondere Differential Drive und Odometrie-Gleichungen) und Kapitel 5 (Odometrie-Fehlerklassifikation, UMBmark-Testverfahren und systematische Kalibrierung).

## Kernaussagen

### 1. Grundlagen der Odometrie und Dead Reckoning (Kap. 1, S. 13-20)

- **Dead Reckoning** ist die einfachste und am weitesten verbreitete Methode zur Positionsbestimmung mobiler Roboter. Der Begriff leitet sich von "deduced reckoning" aus der Seefahrt ab (S. 13).
- Fuer mobile Roboter sind **inkrementelle optische Encoder** der bevorzugte Sensortyp. Phasenquadratur-Encoder mit zwei um 90 Grad versetzten Kanaelen ermoeglichen die Richtungserkennung und eine Ververfachung der Aufloesung (S. 14).
- Der **Konversionsfaktor** c_m, der Encoder-Pulse in lineare Raddistanz umrechnet, ist definiert als: `c_m = pi * D_n / (n * C_e)`, wobei D_n der nominale Raddurchmesser, C_e die Encoder-Aufloesung (Pulse/Umdrehung) und n das Getriebeuebersetzungsverhaeltnis ist (Gl. 1.2, S. 20).

### 2. Odometrie-Gleichungen fuer Differentialantrieb (Kap. 1, S. 19-20)

- Die **inkrementelle Fahrstrecke** jedes Rades berechnet sich aus: `Delta_U_L/R = c_m * N_L/R` (Gl. 1.3, S. 20).
- Die **lineare Verschiebung** des Roboter-Mittelpunkts: `Delta_U = (Delta_U_R + Delta_U_L) / 2` (Gl. 1.4, S. 20).
- Die **inkrementelle Orientierungsaenderung**: `Delta_theta = (Delta_U_R - Delta_U_L) / b`, wobei b die Spurbreite (Wheelbase) ist -- idealerweise der Abstand der Radaufstandspunkte (Gl. 1.5, S. 20).
- Die **Positionsaktualisierung**: `x_i = x_(i-1) + Delta_U * cos(theta_i)` und `y_i = y_(i-1) + Delta_U * sin(theta_i)` (Gl. 1.7a/b, S. 20).
- Diese Gleichungen sind identisch mit der Vorwaertskinematik, die in der ESP32-Firmware des AMR implementiert ist.

### 3. Kinematischer Einfluss auf Odometrie-Genauigkeit (Kap. 1, S. 19-28)

- Die **Genauigkeit der Odometrie** haengt stark vom kinematischen Design des Fahrzeugs ab. Man muss das kinematische Design sorgfaeltig betrachten, bevor man die Dead-Reckoning-Genauigkeit verbessern kann (S. 19).
- Der **Differentialantrieb** ist die einfachste Konfiguration: Zwei Antriebsraeder mit Encodern an den Motoren ermoeglichen die Positionsberechnung ueber einfache geometrische Gleichungen (S. 19).
- **Kettenfahrzeuge** (Tracked Vehicles) liefern aufgrund der hohen Schlupfanteile beim Lenken grundsaetzlich schlechte Odometrie-Daten und sind fuer Dead Reckoning ungeeignet (S. 28).

### 4. Klassifikation der Odometriefehler (Kap. 5, S. 130-131)

- Odometrie ist die am weitesten verbreitete Navigationsmethode, bietet gute kurzfristige Genauigkeit, ist kostenguenstig und erlaubt hohe Abtastraten. Der fundamentale Nachteil: Die Integration inkrementeller Bewegungsinformation fuehrt unvermeidlich zur Fehlerakkumulation (S. 130).
- **Systematische Fehler** (konstant, kalibrierbar):
  - Ungleiche Raddurchmesser (E_d)
  - Abweichung des mittleren Raddurchmessers vom Nennwert
  - Abweichung der effektiven Spurbreite vom Nennwert (E_b)
  - Radfehlausrichtung
  - Endliche Encoder-Aufloesung und Abtastrate (S. 130-131)
- **Nicht-systematische Fehler** (unvorhersehbar, nicht kalibrierbar):
  - Fahrt ueber unebene Boeden
  - Radschlupf durch glatte Boeden, Ueberbeschleunigung, schnelle Kurven, externe Kraefte, Castor-Raeder
  - Nicht-punktfoermiger Radkontakt (S. 131)
- Auf glatten Innenboeden dominieren **systematische Fehler**; auf rauen Boeden ueberwiegen nicht-systematische Fehler (S. 131).

### 5. Fehlerparameter E_d und E_b (Kap. 5, S. 132)

- Das vereinfachte Fehlermodell von Borenstein und Feng reduziert die systematischen Fehler auf **zwei dominante Parameter**:
  - **E_d = D_R / D_L**: Verhaeltnis der tatsaechlichen Raddurchmesser (rechts/links). Verursacht gekruemmte statt gerader Bahnen (Typ-B-Fehler) (Gl. 5.1, S. 132).
  - **E_b = b_actual / b_nominal**: Verhaeltnis der tatsaechlichen zur nominalen Spurbreite. Verursacht Ueber-/Unterdrehen in Kurven (Typ-A-Fehler) (Gl. 5.2, S. 132).

### 6. Unidirektionaler Square-Path Test -- Problematik (Kap. 5, S. 132-134)

- Der **unidirektionale Quadratpfad-Test** (4x4 m Quadrat in einer Richtung) ist ein gaengiger, aber **ungeeigneter Benchmark** fuer Differentialantrieb-Roboter (S. 132).
- Das Problem: Die beiden systematischen Fehler E_d und E_b koennen sich bei einseitiger Fahrt **gegenseitig kompensieren** und so eine falsche Genauigkeit vortaeuschen. Korrigiert man nur einen der beiden Fehler, verschlechtert sich die Leistung moeglicherweise sogar (S. 133-134).

### 7. UMBmark -- Bidirektionaler Square-Path Test (Kap. 5, S. 134-136)

- Der **UMBmark** (University of Michigan Benchmark) ist der korrekte Teststandard fuer Differential-Drive-Odometrie. Er erfordert die Durchfuehrung des Quadratpfad-Experiments in **beiden Richtungen** (CW und CCW) (S. 134).
- Der Roboter faehrt ein 4x4 m Quadrat mindestens **5 Mal in jeder Richtung** (CW und CCW). Start nahe einer Wandecke, die als Referenz dient (S. 132, 134).
- Die Endpositionen bilden **zwei separate Cluster** (CW und CCW). Die Verteilung innerhalb der Cluster spiegelt nicht-systematische Fehler wider; der systematische Fehler zeigt sich im Offset der Cluster-Schwerpunkte vom Ursprung (S. 135).
- Der **Schwerpunkt** jedes Clusters wird berechnet als: `x_c.g. = (1/n) * Summe(epsilon_x)` (Gl. 5.4, S. 135).
- Die **Metrik E_max,syst**: Das Maximum der euklidischen Abstaende der Cluster-Schwerpunkte vom Ursprung: `E_max,syst = max(r_c.g.,cw ; r_c.g.,ccw)` (Gl. 5.6, S. 135).

### 8. Berechnung der Korrekturfaktoren aus UMBmark-Daten (Kap. 5, S. 139-142)

- Borenstein und Feng definieren **Typ-A- und Typ-B-Fehler** im Kontext des UMBmark:
  - **Typ A** (verursacht durch E_b): Reduziert oder erhoeht die Gesamtrotation in **beiden** Richtungen gleichsinnig (S. 139-140).
  - **Typ B** (verursacht durch E_d): Erhoeht die Rotation in einer Richtung, reduziert sie in der anderen (S. 140-141).
- Aus den Schwerpunkt-Koordinaten werden die Winkel **alpha** und **beta** berechnet:
  - `alpha = [(x_c.g.,cw + x_c.g.,ccw) / (-4L)] * (180/pi)` (Gl. 5.9, S. 141) -- repraesentiert Typ-A-Fehler
  - `beta = [(x_c.g.,cw - x_c.g.,ccw) / (-4L)] * (180/pi)` (Gl. 5.10, S. 141) -- repraesentiert Typ-B-Fehler
- Daraus der **Kruemmungsradius** R: `R = L/2 / sin(beta/2)` (Gl. 5.11, S. 141).
- Berechnung des **Raddurchmesser-Korrekturfaktors**: `E_d = D_R/D_L = (R + b/2) / (R - b/2)` (Gl. 5.12, S. 141).
- Berechnung des **Spurbreiten-Korrekturfaktors**: `E_b = 90 / (90 - alpha)` (Gl. 5.15, S. 142), bzw. `b_actual = [90 / (90 - alpha)] * b_nominal` (Gl. 5.14, S. 142).
- **Ergebnis der Kalibrierung**: Eine 10- bis 20-fache Reduktion der systematischen Fehler (S. 142).
- Beispiel aus dem Bericht: Vor Kalibrierung b = 340.00 mm, D_R/D_L = 1.00000; nach Kalibrierung b = 336.17 mm, D_R/D_L = 1.00084 (S. 142, Fig. 5.10).

### 9. Praktische Kalibrierungs-Hinweise (Kap. 5, S. 137-143)

- Die UMBmark-Kalibrierung kann mit einem **einfachen Massband** durchgefuehrt werden. Die gesamte Prozedur dauert etwa **zwei Stunden** (S. 143).
- Fahrzeuge mit **kleiner Spurbreite** sind anfaelliger fuer Orientierungsfehler als solche mit grosser Spurbreite (S. 137-138).
- Castor-Raeder, die einen signifikanten Anteil des Gewichts tragen, verursachen Schlupf beim Richtungswechsel ("Shopping-Cart-Effekt") (S. 138).
- Ideale Odometrie-Raeder waeren duenn ("knife-edge"), aus Aluminium, mit duenner Gummi-Auflage fuer bessere Traktion (S. 138).
- Geschwindigkeitsbegrenzung waehrend Kurven und Beschleunigungslimits reduzieren schlupfbedingte Fehler (S. 138).

### 10. Messung nicht-systematischer Fehler (Kap. 5, S. 136-137)

- Der **Extended UMBmark** fuegt kuenstliche Bodenunebenheiten (10 Kabelueberfahrten) hinzu, um die Empfindlichkeit gegenueber nicht-systematischen Fehlern zu quantifizieren (S. 136).
- Der **Orientierungsfehler epsilon_theta** ist ein besserer Indikator als der Positionsfehler, da er unabhaengig von der exakten Position der Stoerung ist (S. 136-137).

### 11. Positionierungsmethoden -- Ueberblick (Introduction, S. 10-12)

- Es gibt keine universelle Loesung fuer die Roboterpositionierung. Die Methoden gliedern sich in **relative** (Odometrie, Inertialnavigation) und **absolute** (Beacons, Landmarks, GPS, Map Matching) Verfahren (S. 10-11).
- Die meisten praktischen Systeme kombinieren zwei Methoden: eine relative und eine absolute. Odometrie dient als "Backbone" zwischen absoluten Positionsfixes (S. 10).

## Relevanz fuer die Projektarbeit

| Aspekt | Relevanz |
|---|---|
| **Odometrie-Gleichungen (Gl. 1.2-1.7)** | Direkt implementiert in `diff_drive_kinematics.hpp` der ESP32-Firmware. Die Gleichungen fuer c_m, Delta_U, Delta_theta und Positionsaktualisierung sind identisch. |
| **UMBmark-Testprotokoll** | Wird als Validierungsmethode in der Projektarbeit eingesetzt (4x4 m Quadrat, 5 Laeufe CW/CCW). |
| **Fehlerparameter E_d und E_b** | Zentrale Kalibrierungsgroessen. E_d (Raddurchmesser-Verhaeltnis) und E_b (effektive Spurbreite) werden aus UMBmark-Daten berechnet und als Korrekturfaktoren in der Firmware hinterlegt. |
| **Korrekturfaktor-Berechnung (Gl. 5.9-5.15)** | Liefert die mathematische Grundlage fuer die Odometrie-Kalibrierung des AMR. |
| **Systematische vs. nicht-systematische Fehler** | Begruendet, warum auf glatten Hallenboeden (Intralogistik-Szenario) die Kalibrierung besonders wirksam ist. |
| **Roboter-Parameter** | Der AMR hat Radradius 32 mm und Spurbreite 145 mm -- eine relativ kleine Spurbreite, daher besonders empfindlich fuer Orientierungsfehler (vgl. Borenstein S. 137-138). |
| **Differential Drive** | Der AMR verwendet denselben Aufbau wie die LabMate-Referenzplattform von Borenstein (zwei Antriebsraeder + Castor). |
