# Navigation und SLAM -- Kernaussagen

---

## Paper 1: Macenski et al. (2023) -- From the Desks of ROS Maintainers: A Survey of Modern & Capable Mobile Robotics Algorithms in the Robot Operating System 2

### Bibliografische Angaben
- **Autoren:** Steve Macenski, Tom Moore, David V. Lu, Alexey Merzlyakov, Michael Ferguson
- **Venue:** Robotics and Autonomous Systems 168, 104493 (arXiv:2307.15236v2)
- **Jahr:** 2023 (arXiv-Preprint 31. Juli 2023)
- **DOI/Link:** arXiv:2307.15236

### Zusammenfassung (Abstract)

Das Paper bietet eine umfassende Uebersicht ueber den Stand der Technik der mobilen Roboternavigation in ROS 2, verfasst von den Kernentwicklern und Maintainern des Nav2-Projekts. Es werden neue Systeme vorgestellt, die in ROS 1 oder anderen Frameworks keine Entsprechung haben. Die Autoren diskutieren aktuelle Forschungsprodukte und historisch bewaehrte Methoden, die unterschiedliche Verhaltensweisen und Unterstuetzung fuer nahezu jeden Robotertyp bieten. Einige der beschriebenen Implementierungen wurden erstmals in der Literatur dokumentiert und bisher nicht untereinander verglichen.

### Kernaussagen

#### 1. Nav2 Architektur und Designphilosophie
- Nav2 wurde von Grund auf neu entwickelt, um Innovationen bei Behavior Trees zu nutzen und aufgefrischte Algorithmen zu integrieren; es ist keine Portierung von move_base aus ROS 1 (S. 1)
- Nav2 unterstuetzt alle gaengigen Roboterformen: Differentialantrieb, omnidirektional, Ackermann, nicht-kreisfoermig und Vierbeiner-Plattformen (S. 1)
- Das Projekt haelt produktionsreife Qualitaetsstandards mit 90% Unit-Test-Abdeckung ein und zielt darauf ab, die Entwicklung zwischen Wissenschaft und Industrie zu buendeln (S. 1)
- Nav2 nutzt ein hybrides Planungsschema: Globale Planer finden eine akzeptable Route, lokale Trajectory-Planer folgen dieser unter Beruecksichtigung zusaetzlicher Systembedingungen (S. 5)
- Neue laufzeitkonfigurierbare Plugin-Schnittstellen wurden eingefuehrt, um Gemeinsamkeiten zwischen Controller-Implementierungen zu abstrahieren, z.B. dynamische Geschwindigkeitslimits, Zielabfrage und Fortschrittskontrolle (S. 5)

#### 2. Globale Pfadplaner
- Alle globalen Planer in Nav2 sind Erweiterungen von Dijkstras Algorithmus und kostenberuecksichtigend (cost-aware), d.h. sie beruecksichtigen Cost-Map-Risikowerte statt nur binaerer Hindernisse (S. 2)
- Suchbasierte Planer werden gegenueber samplingbasierten (z.B. RRT) bevorzugt, da sie in niedrigdimensionalen Zustandsraeumen schneller sind, wirklich optimale Pfade erzeugen und vorhersagbare Ausfuehrungszeiten bieten (S. 2)
- **Navigation Function (NavFn)**: Aeltester Algorithmus in Nav2, basiert auf der NF1-Funktion mit Dijkstra-Expansion. Nutzt eine quadratische Kernelfunktion statt reiner Distanzen, erzeugt glattere Potentialfelder und gleichmaessig verteilte Pfade. Typische Laufzeit 15--175 ms, produziert Pfade die designbedingt 5% laenger sind fuer bessere Sicherheitsmargen. Bleibt der Standard-Planer fuer allgemeine Anwendungen (S. 2--3)
- **Lazy Theta*-P**: Any-Angle-Pfadplaner basierend auf A* mit Line-of-Sight-Pruefungen (Bresenham-Algorithmus). Erzeugt die kuerzesten Pfade, hat aber die laengste Laufzeit. Besonders nuetzlich fuer nicht-achsenausgerichtete Karten und lange gerade Korridore in Bueros, Lagern und Einzelhandel (S. 3)
- **2D-A***: Einfachster holonomischer Ansatz im Smac Planner Framework. Moore-Nachbarschaft mit L2-Heuristik. Kostenberuecksichtigende Traversierungskosten nach Formel: cost_travel = d * (1.0 + w_cost * cost(x,y) / cost_max) (S. 3--4)
- **Hybrid-A***: Fuer Ackermann-/autoaehnliche Roboter entwickelt (Stanford, DARPA Urban Challenge). Nutzt Bewegungsprimitive mit kontinuierlichen Koordinaten (x, y, theta). Dubin- oder Reeds-Shepp-Modelle fuer Suchprimitive. Laufzeit 10--250 ms. Begrenzung der Pfadkruemmung verhindert Umkippen bei Hochgeschwindigkeitssystemen (S. 4--5)
- **State Lattice**: Erweiterung von A* auf einem strukturierten Lattice-Graphen mit offline berechneten Bewegungsprimitiven. Verarbeitet beliebige Antriebsmodelle. Smac-Optimierungen verbessern die Leistung um eine Groessenordnung gegenueber historischen SBPL-Bibliotheken auf 20--300 ms (S. 5)
- Benchmark-Vergleich (1.000 zufaellige Start-/Zielposen, 10.000 m^2 Karte, 20% belegt): NavFn 61 ms / 52.25 m; Lazy Theta* 94 ms / 50.28 m; 2D-A* 88 ms / 49.65 m; Hybrid-A* 38 ms / 50.78 m; State Lattice 39 ms / 50.51 m (Table I, S. 3)

#### 3. Lokale Trajectory-Planer (Controller)
- **Dynamic Window Approach (DWB)**: Aktueller Standard-Controller in Nav2. Abtastung machbarer Geschwindigkeitskommandos aus dem dynamischen Fenster, Bewertung ueber konfigurierbare Critic-Funktionen (Zielausrichtung, Hindernisdistanz, Vorwaertsgeschwindigkeit u.a.). Bis zu 250 Hz. Nachteil: Sehr viele zusammenhaengende Parameter muessen gestimmt werden; schlecht konfiguriertes DWB ist ein haeufiger Kritikpunkt in der ROS-Community (S. 6--7)
- **Model Predictive Path Integral (MPPI)**: MPC-Variante mit verrauschten Trajektorien-Samples statt numerischer Optimierung. Kostenfunktionen muessen nicht differenzierbar oder konvex sein. Nutzt Tensor-Repraesentationen fuer Batch-Verarbeitung. Empirisch gute Ergebnisse bei 1.000 Samples / 50 Hz oder 2.000 Samples / 30 Hz. Herausragend bei Reaktion auf dynamische Hindernisse; benoetigt selten aktive Recovery-Behaviors. Geplant als Nachfolger von DWB (S. 7--8)
- **Timed Elastic Band (TEB)**: Elastische Baender mit zeitlichen Einschraenkungen (Beschleunigung, Geschwindigkeitslimits), optimiert mittels g2o-Framework. Hochgradig konfigurierbar, aber als Soft-Constraint-Optimierung keine Garantie fuer Einhaltung kinematischer Beschraenkungen (S. 7)
- **Regulated Pure Pursuit (RPP)**: Variation des klassischen Pure-Pursuit-Algorithmus mit heuristischen Straffunktionen zur Geschwindigkeitsregulierung. Findet einen Lookahead-Punkt auf dem Referenzpfad und berechnet die Kruemmung kappa = 2y/L^2. Adaptive Pure Pursuit passt den Lookahead dynamisch an (L = v_t * l_t). RPP bremst den Roboter bei Naehe zu Hindernissen und bei hoher Kurvenkruemmung (Gleichung 3: v_curv und v_prox). Dies reduziert nachweislich Bremswege, Ueberschwingen und Unterschwingen bei scharfen Kurven, ohne die Zeit-zum-Ziel wesentlich zu erhoehen. Laeuft bei ueber 4.000 Hz mit minimalem Rechenaufwand. Besonders nuetzlich fuer exakte Pfadverfolgung in statischen Szenen, wo Abweichung nicht erlaubt ist (S. 8--9)
- **Graceful Controller**: Geometrischer Controller basierend auf archimedischen Spiralen, speziell fuer Differentialantriebe. Automatische Geschwindigkeitsreduktion bei enger Kruemmung. Bevorzugt finale Rotation am Ziel statt grosser Boegen (S. 9)
- **Rotation Shim**: Wiederverwendbare Komponente, die den Roboter vor Pfadverfolgung in-place zum Pfad-Heading dreht. Verhindert grosse Boegen oder 3-Punkt-Wenden bei DWB/MPPI (S. 9--10)
- Vergleich der Controller: MPPI bis 125 Hz, TEB 130 Hz, DWB 250 Hz, Graceful 1.800 Hz, RPP >4.000 Hz, Rotation Shim >>10.000 Hz (Table II, S. 6)

#### 4. Pfadglaettung (Smoother)
- **Simple Smoother**: Entfernt lokale Unvollkommenheiten wie Oszillation und Diskontinuitaeten mittels Gradientenabstieg. Laufzeit 1--6 ms. Minimiert Glaettungs- und Abweichungsterme (S. 10)
- **Constrained Smoother**: Nutzt Google Ceres zur Optimierung ueber Glaettheit, Kosten und Kruemmung. Erzeugt fahrbare Pfade mit reduzierten Kosten, aber deutlich rechenintensiver (bis mehrere Sekunden) (S. 10--11)
- **Savitzky-Golay Smoother**: Analytische Glaettung mit gleitendem Polynomfenster. Aendert den Pfadcharakter nicht wesentlich, entfernt nur Rauschen innerhalb eines 7-Punkte-Fensters. Laufzeit 0,06 ms (S. 11--12)
- Benchmark (Smac Hybrid-A*, unordentliche Heimumgebung): Constrained Smoother erzielt beste Glaettheit (87.85) und niedrigste Durchschnittskosten (6.88), Simple Smoother kuerzeste Pfade (1115 cm) (Table III, S. 11)

#### 5. Costmaps und Wahrnehmungsschichten
- Cost Maps reduzieren das Weltmodell auf ein 2D-Gitter mit Zellkosten von 0--255 (254 = belegt, 255 = unbekannt). In der Praxis sind 0,05 m x 0,05 m Zellen ueblich -- ausreichend fuer Genauigkeit, effizient fuer Berechnung (S. 12)
- Das **Layered Costmap**-System aktualisiert die Cost Map durch dynamisch geladene Schichten, jeweils fuer unterschiedliche Datenquellen/Algorithmen (S. 12)
- **Static Layer**: A-priori-Karte aus OccupancyGrid-Topic, Basisschicht fuer alle weiteren (S. 13)
- **Obstacle Layer**: 2D-Raytracing mit Bresenhams Algorithmus fuer Laserscanner; markiert Endpunkte als belegt, Strahl als frei. Ideal fuer planare Laserscanner (S. 13)
- **Voxel Layer**: Wie Obstacle Layer, aber 3D-Raytracing mit Voxel-Gitter. Fuer RGB-D, 3D-Lidar (S. 13)
- **Spatio-temporal Voxel Layer (STVL)**: Nutzt OpenVDB (sparse Voxel-Gitter), zeitliches Decay statt Raytracing fuer Freiraeumung. Ideal fuer hochdynamische Umgebungen (S. 13--14)
- **Range Layer**: Probabilistisches Modell fuer Infrarot-/Sonar-/Ultraschallsensoren (S. 14)
- **Inflation Layer**: Exponentielle Decay-Funktion um Hindernisse: cost(x,y) = (cost_lethal - 1) * e^(-w_scale*(d_o - r)). Fuer kreisfoermige Roboter wird der Konfigurationsraum direkt dargestellt; fuer nicht-kreisfoermige Roboter wird Inflation zur Optimierung der Kollisionspruefung genutzt (S. 14)
- **Keepout Layer**: Semantische Sperrzonen mit konfigurierbaren Kostenwerten ueber CostmapFilterInfo (S. 14)
- **Speed Layer**: Geschwindigkeitsbegrenzungszonen als Prozent- oder Absolutwerte in Filtermasken (S. 14)

#### 6. Behavior Trees
- Nav2 nutzt konfigurierbare Behavior Trees (BTs) anstelle von State Machines oder fest codierter Logik zur Orchestrierung von Navigation, Planung, Steuerung und Recovery (S. 14--15)
- Der **BT Navigator** ist die hoechste Komponente in Nav2 und verarbeitet Anfragen ueber das im XML definierte Verhalten. BTs werden zur Laufzeit dynamisch geladen (S. 14--15)
- Umfangreiche Bibliothek primitiver BT-Knoten: Action-Nodes (Navigate To Pose, Compute Path, Follow Path, Back Up, Spin, Wait, u.v.m.), Condition-Nodes (Goal Reached, Is Stuck, Is Path Valid, u.a.), Decorator-Nodes (Rate Controller, Speed Controller, u.a.) und Control-Nodes (Pipeline Sequence, Recovery, Round Robin) (Table IV, S. 15)
- Drei Hauptkategorien von BTs: Navigate-to-Pose (Punkt-zu-Punkt), Navigate-through-Poses (Via-Punkte), und aufgabenspezifische Anwendungen (S. 15)
- Recovery-Behaviors loesen die grosse Mehrheit der Fehler waehrend der Navigation in dynamischen Szenen: Context-spezifische Recoveries (Costmap loeschen) und globale System-Recovery. Fortgeschrittene BTs umfassen Mixed-Replanning und Goal Patience (S. 15--16)
- Algorithm-Selector-Knoten ermoeglichen es, als Recovery-Aktion einen alternativen Algorithmus (z.B. anderen Planer oder Controller) einzusetzen (S. 16)
- Dynamisches Replanning wird unter einem Rate Controller betrieben (typisch 5--30 s Intervall, BT-Tick-Rate 100 Hz) (S. 16)

#### 7. Zustandsschaetzung (State Estimation)
- REP 105 definiert die Koordinatenrahmen: odom->base_link (kontinuierlich, driftet) und map->base_link (global, korrigiert, aber mit Diskontinuitaeten) (S. 16)
- **robot_localization (r_l)**: Bietet EKF und UKF, unterstuetzt unbegrenzte Sensoranzahl (Odometry, IMU, PoseWithCovarianceStamped, TwistWithCovarianceStamped). 15-dimensionaler Zustandsvektor. Empfehlungen: two_d_mode=true fuer planare Umgebungen; fuer Differentialantrieb sind nur x_dot und theta_dot relevant (S. 17)
- **fuse**: Faktor-Graph-basiertes State-Estimation-Framework mit Plugin-Architektur (Variablen, Constraints, Sensormodelle, Bewegungsmodelle, Optimierer, Publisher). Nutzt Google Ceres. Flexibler und mit geringeren Linearisierungsfehlern als r_l, aber ca. 3,7x CPU-Verbrauch (S. 17--19)
- Benchmark-Vergleich (541 m Strecke, 25 Hz): r_l Fehler 0,78% der Strecke (4,25 m), fuse 0,52% (2,81 m). fuse war 1,44 m naeher an der Ground Truth (Table V, S. 19)

#### 8. Lokalisierung: AMCL
- **AMCL** (Adaptive Monte Carlo Localization): Partikelfilter-basierte Lokalisierung in bekannter Karte. Vollstaendig parametrisierbar: minimale/maximale Partikelanzahl, Resampling-Perioden, Bewegungs- und Sensormodellrauschen (S. 19--20)
- Zwei Sensormodelle: **Beam Model** (Raytracing mit vier Fehlerquellen: Messrauschen, Umgebungsaenderungen, Ausfall, Zufallsrauschen) und **Likelihood Field Model** (Gauss-Verteilung in Lookup-Grid, oft effizienter und robuster bei kleinen Occupancy-Grid-Eintraegen). Genauigkeit von 5 cm in praktischen Umgebungen erreichbar (S. 19--20)
- Zustandsprojektion ueber Bewegungsmodell unterstuetzt Differentialantrieb und holonomische Basen (S. 19)

#### 9. Kartierung: SLAM Toolbox und Cartographer
- **SLAM Toolbox**: Aufbauend auf OpenKarto. Pose-Graph-Optimierung mit Google Ceres. Scan-Matching ueber Korrelationsgitter (grob + fein). Loop Closure durch Kandidatensuche nahegelegener, nicht lokal verbundener Scans. Kann Raeume ueber 100.000 sq ft in Echtzeit kartieren, Multi-Session-Mapping, Serialisierung von Karten, manuelle Pose-Graph-Manipulation (S. 20--21)
- **Cartographer**: Echtzeit-SLAM in 2D/3D mit Pose-Graph-Optimierung und Submaps. Out-of-the-box-Ergebnisse typischerweise schlecht, erfordert umfangreiches professionelles Tuning. Maintenance von Google eingestellt, ROS-2-Support durch Community. Schwierig zu modifizieren und zu debuggen (S. 20)

#### 10. Wichtige Hilfswerkzeuge
- **Lifecycle Manager**: Orchestriert sicheres Hoch-/Herunterfahren aller Nav2-Knoten, haelt Verbindung zu jedem Server, kann nach Fehler reaktivieren (S. 21)
- **Collision Monitor**: Ueberprueft Sensordaten auf drohende Kollisionen und kann Roboter verlangsamen oder stoppen, unabhaengig vom Navigationsplaner. Unterstuetzt Stop-, Slowdown- und Approach-Polygone im Body-Frame (S. 21)
- **Velocity Smoother**: Glaettet Geschwindigkeitsausgaben durch dynamische Beschraenkungen, kann zwischen eingehenden Kommandos interpolieren fuer gleichmaessigere Hardware-Ansteuerung (S. 21)
- **Simple Commander**: Python3-API zur Steuerung von Nav2, ermoeglicht Erstellung autonomer Systeme ohne BT-Konfiguration (S. 21)
- **Waypoint Follower**: Server fuer Navigation durch mehrere Wegpunkte mit Task-Executor-Plugins an jedem Punkt (S. 21)

#### 11. Empfehlungen fuer Robotertypen (Appendix I)
- **Kreisfoermiger Differentialantrieb**: NavFn + MPPI empfohlen. Reg. Pure Pursuit fuer exakte Pfadverfolgung in statischen Szenen. DWB als Allround-Option in nicht-dynamischen Szenen. Path Smoother fuer kreisfoermige Differentialantrieb-Roboter in der Regel nicht notwendig (S. 24)
- **Nicht-kreisfoermiger Differentialantrieb**: Smac State Lattice + MPPI + Simple Smoother. Rotation Shim vor DWB/Graceful empfohlen (S. 24)
- **Omnidirektional**: Wie Differentialantrieb, aber RPP kann laterale Bewegungsfaehigkeiten nicht voll nutzen (S. 24)
- **Ackermann**: Smac Hybrid-A* + MPPI oder Smac Hybrid-A* + RPP + Constrained Smoother (S. 24--25)
- Zusammenfassende Algorithmenuebersicht in Table VI (S. 25)

#### 12. Smac Planner Framework (Appendix II)
- Einheitliches suchbasiertes Planungs-Framework mit gemeinsam genutztem, hoch optimiertem A*-Algorithmus. Algorithmusspezifisches Verhalten wird ueber templated Node Types realisiert (Heuristiken, Expansionsverhalten, Traversierungskosten). Neue Planer koennen mit nur 50 Zeilen Code (Durchschnitt ca. 200) hinzugefuegt werden (S. 25)

### Relevanz fuer die Bachelorarbeit

Das Paper ist die zentrale Referenz fuer die gesamte Navigationsarchitektur des AMR. Der in der Bachelorarbeit eingesetzte Regulated Pure Pursuit Controller wird detailliert beschrieben -- insbesondere die heuristischen Geschwindigkeitsregulierungen bei Hindernisnaehe und Kurvenkruemmung. Die Empfehlung NavFn + MPPI fuer kreisfoermige Differentialantrieb-Roboter liefert eine direkte Begruendung fuer die Planerwahl. Die Beschreibung der Costmap-Schichten, AMCL-Lokalisierung und Behavior Trees deckt alle im Projekt genutzten Nav2-Komponenten ab. Die Benchmark-Daten ermoeglichen eine Einordnung der Systemleistung.

---

## Paper 2: Macenski & Jambrecic (2021) -- SLAM Toolbox: SLAM for the dynamic world

### Bibliografische Angaben
- **Autoren:** Steve Macenski, Ivona Jambrecic
- **Venue:** Journal of Open Source Software, 6(61), 2783
- **Jahr:** 2021 (eingereicht 13. August 2020, veroeffentlicht 13. Mai 2021)
- **DOI/Link:** https://doi.org/10.21105/joss.02783
- **Lizenz:** CC BY 4.0 (Paper), LGPLv2.1 (Software)
- **Repository:** https://github.com/SteveMacenski/slam_toolbox.git

### Zusammenfassung (Abstract)

SLAM Toolbox ist ein vollstaendig quelloffenes ROS-Paket fuer Simultaneous Localization and Mapping (SLAM), das fuer dynamische und haeufig grossflaechige Einsatzumgebungen entwickelt wurde. Es baut auf dem Erbe von Open Karto auf und bietet neben praezisen Kartierungsalgorithmen eine Vielzahl von Werkzeugen und Verbesserungen: mehrere Kartierungsmodi (synchron/asynchron), kinematische Kartenzusammenfuehrung, Lokalisierungsmodus, Multi-Session-Mapping, verbesserte Graph-Optimierung mit Google Ceres, reduzierte Rechenzeit und Prototyp-Anwendungen fuer lebenslange und verteilte Kartierung.

### Kernaussagen

#### 1. Motivation und Problemstellung
- Einsatzgebiete autonomer mobiler Roboter (Einzelhandel, Krankenhaeuser, Lager, Strassen) sind dynamisch und haeufig sehr gross: Ein durchschnittlicher Walmart hat ueber 16.000 m^2, ein Chicagoer Stadtblock ueber 21.000 m^2 (S. 1)
- Laserscanner sind der am haeufigsten verwendete Wahrnehmungssensor fuer Lokalisierung und Kartierung in industriellen Umgebungen; Laserscanner-basierte SLAM-Methoden gelten als die robustesten bei dynamischen Hindernissen und sich aendernden Umgebungen (S. 1)
- Vor SLAM Toolbox konnten bestehende Open-Source-SLAM-Pakete (GMapping, Karto, Cartographer, Hector) keine grossen Raeume in Echtzeit auf typischer mobiler Roboterhardware zuverlaessig kartieren. Cartographer war die einzige Ausnahme, wurde aber von Google aufgegeben (S. 1)

#### 2. Vergleich mit existierenden SLAM-Methoden
- **GMapping**: Partikelfilter-basiert, seit 2007. Nicht geeignet fuer grosse Raeume, scheitert bei Loop Closure im industriellen Massstab, Filterbasierte Ansaetze koennen nicht ueber mehrere Sessions hinweg reinitialisiert werden (S. 2)
- **HectorSLAM**: EKF-basierte Zustandsschaetzung mit Lidar-Scan-Matching bei hoher Updaterate. Nutzt keine Odometrie, was bei niedriger Lidar-Rate oder in merkmalsarmen Raeumen zu ungenauen Posen fuehrt. Keine Loop-Closure-Faehigkeit (S. 2)
- **KartoSLAM**: Graph-basiert, nutzt Sparse Bundle Adjustment fuer Loop-Closure-Optimierung (S. 2--3)
- **Cartographer**: Graph-basiert mit Frontend (Scan Matching, Submaps) und Backend (Loop Closure via Google Ceres). Hat Wartung und Support von Google verloren, Community-maintained. Schwierig zu modifizieren, erfordert aussergewoehnliche Odometrie fuer gute Ergebnisse. Speichert nur verarbeitete Submaps, nicht den vollstaendigen Pose-Graph (S. 2--3)

#### 3. SLAM Toolbox Architektur und Features
- Baut auf der OpenKarto SLAM-Bibliothek auf, die erheblich ueberarbeitet wurde (S. 1, 5)
- Kann Raeume von ueber 100.000 ft^2 (ca. 9.300 m^2) in Echtzeit auf gaengigen mobilen Intel-CPUs kartieren, auch von ungelernten Technikern bedienbar (S. 3)
- Serialisierung speichert den vollstaendigen Roh-Daten- und Pose-Graph (nicht nur Submaps wie bei Cartographer), was neuartige Werkzeuge fuer Multi-Session-Mapping und manuelle Pose-Graph-Manipulation ermoeglicht (S. 3)
- Kinematische Kartenzusammenfuehrung (Kinematic Map Merging): Verschmelzen mehrerer serialisierter Karten zu einer Gesamtkarte (S. 3)
- Manuelle Pose-Graph-Manipulation: Nutzer kann Knoten und Daten manuell manipulieren, z.B. um bei schwieriger Loop Closure zu assistieren (S. 3)
- 3D-Visualizer-Plugin fuer RViz zur Nutzung der Werkzeuge und SLAM-Bibliothek (S. 3)

#### 4. Betriebsmodi
- **Synchrones Mapping**: Verarbeitet alle Messungen in einem Puffer; Karte kann hinter Echtzeit zurueckfallen, garantiert aber hoechste Kartenqualitaet. Auch fuer Offline-Verarbeitung geeignet (S. 4)
- **Asynchrones Mapping**: Verarbeitet neue Messungen nur wenn die vorherige fertig ist und neue Update-Kriterien erfuellt sind. Bleibt nie hinter Echtzeit zurueck, kann aber bei langen Loop Closures nicht alle Messungen einbeziehen. Vorteilhaft wenn Echtzeit-Lokalisierung besonders wichtig ist (S. 4)
- **Pure Localization Mode**: Nutzt einen Rolling Buffer aktueller Messungen und matched gegen den originalen Pose-Graph. Neue Messungen werden als Constraints hinzugefuegt, aeltere "verfallen" und werden entfernt (elastische Pose-Graph-Deformation). Kann Umgebungsaenderungen erfassen. Als Nebeneffekt auch als effektive Lidar-Odometrie ohne vorherige Kartierung nutzbar -- skaliert auf unendlich grosse Raeume (S. 4)
- Beide Mapping-Modi unterstuetzen Multi-Session-SLAM: Eine vorherige Session wird geladen und der Pose-Graph weiter verfeinert (S. 4)

#### 5. Technische Verbesserungen gegenueber OpenKarto
- Scan-Matching-Methoden fuer Multi-Threading umstrukturiert: 10-fache Geschwindigkeitssteigerung (S. 5)
- Sparse Bundle Adjustment durch Google Ceres als Graph-Optimierer ersetzt: schnellere und flexiblere Optimierungseinstellungen (S. 5)
- Optimierer-Schnittstelle als Runtime-Plugin gestaltet, sodass kuenftig neueste Optimierungstechnologien ohne Code-Aenderung integriert werden koennen (S. 5)
- Serialisierungs-/Deserialisierungssupport fuer Speichern und Laden von Mapping-Sessions (S. 5)
- Neue Verarbeitungsmodi und K-D-Tree-Suche fuer Lokalisierung und Multi-Session-Mapping (S. 5)

#### 6. Scan Matching und Loop Closure (ergaenzt aus Nav2-Paper)
- Scan Matching nutzt ein Korrelationsgitter: Eingehender Scan wird zunaechst bei grober halber Aufloesung, dann bei voller Aufloesung gegen den Puffer lokaler Messungen gematcht (Nav2-Paper S. 20--21)
- Loop Closure: Der korrigierte Scan wird gegen Kandidaten-Scans geprueft, die raeumlich nahe aber im Graph nicht lokal verbunden sind. Bei starker Uebereinstimmung auf grober und feiner Aufloesung wird ein Constraint hinzugefuegt und der Pose-Graph optimiert (Nav2-Paper S. 21)

#### 7. Verbreitung und Adoption
- Standard-SLAM-Anbieter in ROS 2, ersetzt GMapping als Default (S. 1)
- In die ROS 2 Navigation2 integriert fuer Echtzeit-Positionierung in dynamischen Umgebungen (S. 1)
- Eingesetzt bei: Simbe Robotics (Tally), ROBOTIS (TurtleBot3), Samsung Research, Rover Robotics, Pal Robotics (ARI), Intel Open Source Group, Queensland University of Technology, MT Robot AG, Magazino, 6 River Systems, u.a. (S. 5--6)

### Relevanz fuer die Bachelorarbeit

SLAM Toolbox ist das in der Bachelorarbeit eingesetzte Kartierungssystem. Die drei Betriebsmodi (synchron, asynchron, Pure Localization) entsprechen direkt den Konfigurationsparametern in mapper_params_online_async.yaml. Der asynchrone Modus ist fuer den Raspberry Pi 5 besonders relevant, da er Echtzeit-Lokalisierung garantiert, auch wenn komplexe Loop Closures laufen. Die Verwendung von Google Ceres als Solver bestaetigt die Konfiguration im Projekt. Die Serialisierungsfaehigkeit ermoeglicht die Wiederverwendung erstellter Karten fuer den Pure Localization Mode im Betrieb -- was fuer den Intralogistik-Einsatz (wiederholte Fahrten in bekannter Umgebung) zentral ist.
