# Hess et al. (2016) -- Real-Time Loop Closure in 2D LIDAR SLAM

## Bibliografische Angaben
- **Autoren:** Wolfgang Hess, Damon Kohler, Holger Rapp, Daniel Andor (alle Google)
- **Titel:** Real-Time Loop Closure in 2D LIDAR SLAM
- **Venue:** IEEE International Conference on Robotics and Automation (ICRA) 2016
- **Seiten:** 8 Seiten
- **Kontext:** Beschreibung des Google Cartographer Systems fuer Echtzeit-2D-SLAM mit Schwerpunkt auf effizienter Loop Closure

## Zusammenfassung (Abstract)
Portable Laserscanner (LIDAR) und SLAM sind effiziente Methoden zur Erstellung von Gebaeudeplaenen. Die Echtzeit-Generierung und Visualisierung von Grundrissen hilft dem Bediener, Qualitaet und Abdeckung der Erfassung zu beurteilen. Die Autoren praesentieren einen Backpack-basierten Kartierungsansatz, der Echtzeit-Mapping und Loop Closure bei 5 cm Aufloesung erreicht. Der Kernbeitrag ist ein Branch-and-Bound-Verfahren zur Berechnung von Scan-to-Submap-Matches als Loop-Closure-Constraints. Experimentelle Ergebnisse zeigen, dass der Ansatz qualitativ mit etablierten Verfahren konkurrenzfaehig ist. (S. 1)

## Kernaussagen

### 1. Systemarchitektur und Gesamtkonzept
- Cartographer ist eine Echtzeit-Loesung fuer Indoor-Mapping in Form eines sensorbestueckten Rucksacks, der 2D-Gitterkarten mit r = 5 cm Aufloesung erzeugt (S. 1)
- Der Bediener kann die Karte waehrend der Erstellung live sehen -- dies ermoeglicht sofortige Qualitaetskontrolle (S. 1)
- Das System verwendet bewusst keinen Partikelfilter, um mit bescheidenen Hardware-Anforderungen gute Leistung zu erzielen (S. 1)
- Der Ansatz kombiniert zwei Ebenen: lokales SLAM (Scan-to-Submap-Matching) und globale Optimierung (Pose-Graph mit Loop Closure) (S. 2)

### 2. Submap-Konzept (Local SLAM)
- Jeder aufeinanderfolgende Scan wird gegen einen kleinen Weltausschnitt, die sogenannte Submap M, gematcht (S. 2)
- Submaps bestehen aus Probability Grids: Gitterkarten der Aufloesung r, die diskrete Gitterpunkte auf Wahrscheinlichkeitswerte [p_min, p_max] abbilden (S. 2)
- Wenige aufeinanderfolgende Scans bauen eine Submap auf; bei nur wenigen Dutzend Scans bleibt der akkumulierte Fehler klein (S. 3)
- Groessere Raeume werden durch viele kleine Submaps abgedeckt, was den lokalen Drift begrenzt (S. 3)
- Sobald eine Submap fertiggestellt ist (keine neuen Scans mehr), nimmt sie an der Loop-Closure-Erkennung teil (S. 1)

### 3. Probability Grid und Scan-Einfuegung
- Fuer jeden Scan werden Hits (Treffer, Hindernispunkte) und Misses (freie Bereiche entlang der Strahlen) berechnet (S. 2)
- Jeder zuvor unbeobachtete Gitterpunkt erhaelt eine Wahrscheinlichkeit p_hit oder p_miss, je nachdem ob er in der Hit- oder Miss-Menge liegt (S. 2)
- Bereits beobachtete Gitterpunkte werden ueber Odds-Aktualisierung inkrementell verfeinert: M_new(x) = clamp(odds^{-1}(odds(M_old(x)) * odds(p_hit))) (S. 2)
- Dieses Verfahren ist ein Occupancy-Grid-Update, das effizient inkrementell arbeitet (S. 2)

### 4. Ceres-basiertes Scan Matching
- Vor dem Einfuegen in eine Submap wird die Scan-Pose xi mittels des Ceres-Solvers [14] optimiert (S. 2)
- Das Scan Matching wird als nichtlineares Kleinste-Quadrate-Problem formuliert: argmin_xi sum(1 - M_smooth(T_xi * h_k))^2 (S. 2)
- M_smooth ist eine bikubisch interpolierte, glatte Version der Probability Grid -- dies ermoeglicht subpixelgenaue Optimierung (S. 2-3)
- Da es sich um eine lokale Optimierung handelt, sind gute Anfangsschaetzungen erforderlich; eine IMU kann die Rotationskomponente liefern (S. 3)
- Ohne IMU kann eine hoehere Scan-Frequenz oder pixelgenaues Scan Matching als Alternative dienen (S. 3)

### 5. Pose-Graph-Optimierung (Closing Loops)
- Die Loop-Closure-Optimierung folgt dem Sparse Pose Adjustment (SPA) Ansatz [2] (S. 3)
- Sowohl Submap-Posen Xi^m als auch Scan-Posen Xi^s werden in der Welt optimiert, verbunden durch Constraints mit Kovarianzmatrizen (S. 3)
- Die Optimierung wird als nichtlineares Kleinste-Quadrate-Problem mit Huber Loss formuliert: argmin 1/2 * sum(rho(E^2(...))) (S. 3)
- Die Huber-Loss-Funktion reduziert den Einfluss von Ausreissern -- wichtig bei lokal symmetrischen Umgebungen wie Buerofluren (S. 3)
- Die Optimierung wird alle paar Sekunden mit Ceres [14] berechnet, sodass Schleifen sofort geschlossen werden, wenn ein Ort erneut besucht wird (S. 2)

### 6. Branch-and-Bound Scan Matching (Kernbeitrag)
- Ziel ist das optimale, pixelgenaue Match eines Scans gegen eine Submap: xi* = argmax sum(M_nearest(T_xi * h_k)) (S. 3)
- Ein naiver Brute-Force-Ansatz ueber das gesamte Suchfenster W waere zu langsam (S. 3)
- Stattdessen wird ein Branch-and-Bound-Verfahren eingesetzt, das den Suchraum als Baum darstellt (S. 3-4)
- **Node Selection:** Tiefensuche (DFS) als Standardstrategie -- bewertet schnell viele Blattknoten und findet frueh gute Loesungen (S. 4)
- **Branching Rule:** Jeder Knoten wird durch ein Tupel (c_x, c_y, c_theta, c_h) beschrieben; Knoten der Hoehe c_h umfassen 2^{c_h} x 2^{c_h} moegliche Translationen bei fester Rotation (S. 4)
- **Upper Bounds:** Effiziente Berechnung ueber vorberechnete Gitter (Precomputed Grids): M_precomp^h speichert das Maximum ueber 2^h x 2^h Pixelboxen (S. 4-5)
- Die Vorberechnung der Gitter erfolgt in O(n), wobei n die Pixelanzahl ist (S. 5)
- Ein Score-Threshold wird eingefuehrt, um schlechte Matches als Loop-Closure-Constraints auszuschliessen (S. 4)
- Die Echtzeit-Anforderung wird als "weiche" Bedingung formuliert: Loop-Closure-Scan-Matching muss schneller sein als neue Scans hinzukommen, sonst faellt das System merklich zurueck (S. 2)

### 7. Suchfenster-Parametrierung
- Typische lineare Suchfenstergroessen: W_x = W_y = 7 m, W_theta = 30 Grad (S. 3)
- Der Winkelschritt delta_theta wird so gewaehlt, dass Scanpunkte bei maximaler Entfernung nicht mehr als einen Pixel (Aufloesung r) wandern (S. 3)
- Dies fuehrt zu einer grossen, aber endlichen Menge diskreter Kandidatenposen W (S. 3)

### 8. Experimentelle Validierung: Deutsches Museum
- Datensatz: 1.913 s Sensordaten bzw. 2.253 m Trajektorie auf dem 2. Stockwerk des Deutschen Museums in Muenchen (S. 5)
- Hardware: Intel Xeon E5-1650 @ 3.2 GHz Workstation (S. 5)
- Ergebnis: 1.018 s CPU-Zeit, bis zu 2,2 GB Speicher, bis zu 4 Hintergrund-Threads fuer Loop Closure (S. 5)
- Wanduhrzeit: 360 s -- das entspricht 5,3-facher Echtzeitgeschwindigkeit (S. 5)
- Erzeugter Graph: 11.456 Knoten und 35.300 Kanten; typische SPA-Loesung: ca. 3 Iterationen in 0,3 s (S. 5)

### 9. Validierung mit preiswerter Hardware (Neato Revo LDS)
- Der Neato Revo LDS ist ein Laserscanner fuer unter 30 USD aus Staubsaugerrobotern (S. 6)
- Scans bei ca. 2 Hz ueber Debug-Verbindung, 5 cm Kartenaufloesung (S. 6)
- Vermessung von 5 geraden Strecken: Abweichungen im Bereich von -0,01 bis +0,11 m gegenueber Laser-Bandmass, relative Fehler -0,2% bis +0,8% (S. 6, Tabelle I)
- Dies zeigt, dass der Algorithmus auch mit preiswerter, niederfrequenter Sensorik funktioniert (S. 6)

### 10. Quantitativer Vergleich mit anderen Verfahren (Radish-Datensatz)
- Benchmark nach Kuemmerle et al. [21]: Vergleich relativer Posen-Aenderungen mit manuell verifizierten Ground-Truth-Relationen (S. 6)
- Verglichen mit Graph Mapping (GM) [21]: Cartographer ist in den meisten Metriken und Datensaetzen ueberlegen (S. 6-7, Tabelle II)
- Verglichen mit Graph FLIRT [9]: Cartographer schneidet bei Freiburg-Datensaetzen besser ab, beim Intel-Datensatz etwas schlechter (S. 7, Tabelle III)
- MIT CSAIL: Cartographer deutlich schlechter als Graph Mapping bei diesem Datensatz (S. 7)
- Fazit: Cartographer ist durchweg konkurrenzfaehig, uebertrifft beide Referenzverfahren in den meisten Faellen (S. 7)

### 11. Loop-Closure-Precision
- Precision-Analyse (Tabelle IV): True Positives definiert als Constraints, die nach SPA-Optimierung weniger als 20 cm oder 1 Grad verletzt werden (S. 7)
- Ergebnisse: Aces 98,1%, Intel 97,2%, MIT Killian Court 93,4%, MIT CSAIL 94,1%, Freiburg bldg 79: 99,8%, Freiburg hospital: 77,3% (S. 7)
- Das Scan-to-Submap-Matching erzeugt False Positives, die jedoch durch die Huber-Loss-Funktion in der SPA-Optimierung robust behandelt werden (S. 7)
- Beim Freiburger Krankenhaus fuehrt die niedrige Aufloesung und ein niedriger Mindest-Score zu vergleichsweise vielen False Positives (S. 7)

### 12. Rechenzeit-Performance
- Alle Datensaetze wurden schneller als Echtzeit verarbeitet (Tabelle V) (S. 7)
- Beispiele: Aces 1366 s Daten in 41 s Wanduhr, Intel 2691 s in 179 s, MIT CSAIL 424 s in 35 s (S. 7)
- Die Parameter waren nicht auf CPU-Performance optimiert, sondern auf Kartenqualitaet (S. 7)

### 13. Design-Entscheidungen und Besonderheiten
- Kein Partikelfilter: Vermeidung des Problems, dass bei gitterbasierten SLAM-Ansaetzen mit Partikelfiltern der Speicherbedarf mit der Kartengroesse explodiert (z.B. 22.000 m^2 bei 3 km Trajektorie) (S. 1)
- Deterministische Scan-to-Submap-Zuordnung statt stochastischer Partikelgewichtung (S. 1)
- GPU-beschleunigte Vorschau: Die finale Karte wird als GPU-beschleunigte Kombination aus fertigen Submaps und der aktuellen Submap dargestellt (S. 7)
- Anpassung an verschiedene Sensoren erfordert nur Tuning der Algorithmus-Parameter an die Sensorkonfiguration, nicht an die spezifische Umgebung (S. 6)

## Relevanz fuer die Bachelorarbeit
Google Cartographer und SLAM Toolbox (in der Bachelorarbeit eingesetzt) sind beide graphbasierte 2D-LiDAR-SLAM-Systeme mit Pose-Graph-Optimierung und nutzen den Ceres-Solver fuer Scan Matching. Der zentrale Unterschied liegt im Loop-Closure-Ansatz: Cartographer verwendet ein Submap-basiertes Branch-and-Bound-Verfahren fuer pixelgenaues Scan-to-Submap-Matching, waehrend SLAM Toolbox auf Scan-to-Scan-Matching und eine flexiblere, serialisierbare Kartenrepraesentation setzt. Cartographers Submap-Konzept begrenzt lokalen Drift durch kleine, abgeschlossene Karteneinheiten -- ein Designprinzip, das sich auch in SLAM Toolboxs Ansatz der inkrementellen Graphkonstruktion wiederfindet. Fuer den AMR der Bachelorarbeit mit begrenzter Rechenleistung (Raspberry Pi 5) ist relevant, dass Cartographer selbst auf preiswerter Sensorik (2 Hz LDS) und mit moderater CPU funktioniert, wobei SLAM Toolbox speziell fuer ressourcenbeschraenkte Robotik-Plattformen und lebenslange Kartierung optimiert wurde.
