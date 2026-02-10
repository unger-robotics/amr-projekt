# Moore & Stouch (2014) -- A Generalized Extended Kalman Filter Implementation for the Robot Operating System

## Bibliografische Angaben
- **Autoren:** Thomas Moore, Daniel Stouch
- **Institution:** Sensor Processing and Networking Division, Charles River Analytics, Inc., Cambridge, Massachusetts, USA
- **Venue:** Proc. 13th International Conference on Intelligent Autonomous Systems (IAS-13), Springer AISC 302, S. 335--348
- **Jahr:** 2014
- **Keywords:** Sensor Fusion, Extended Kalman Filter, Localization, Robot Operating System

## Zusammenfassung (Abstract)

Genaue Zustandsschaetzung fuer mobile Roboter erfordert die Fusion von Daten aus mehreren Sensoren. Diese Arbeit stellt das Softwarepaket *robot_localization* fuer das Robot Operating System (ROS) vor, das eine Implementierung eines Extended Kalman Filters (EKF) enthaelt. Das Paket kann eine unbegrenzte Anzahl von Eingaben aus verschiedenen Sensortypen verarbeiten und erlaubt Nutzern, pro Sensor individuell zu konfigurieren, welche Datenfelder mit dem aktuellen Zustandsschaetzwert fusioniert werden. Die Autoren erlaeutern ihre Designentscheidungen, diskutieren Implementierungsdetails und praesentieren Ergebnisse aus realen Tests.

## Kernaussagen

### 1. Motivation und Limitierungen bestehender Pakete
- Bestehende ROS-Pakete zur Zustandsschaetzung weisen vier zentrale Limitierungen auf (S. 1):
  - **Begrenzte Sensoreingaenge**: Roboter werden mit immer mehr Sensoren ausgestattet, aber existierende Pakete erfordern viel Aufwand zur Integration aller Datenquellen.
  - **Beschraenkung auf 2D-Schaetzung**: Viele Pakete schaetzen nur den 2D-Zustand, was fuer UAVs, UUVs und Outdoor-UGVs unzureichend ist.
  - **Begrenzte ROS-Message-Unterstuetzung**: Sensordaten stammen oft aus Hardware-Treibern, deren Nachrichtentypen der Nutzer nicht kontrolliert. Wird ein bestimmter Typ nicht unterstuetzt, muss ein Zwischenknoten erstellt werden.
  - **Fehlende Kontrolle ueber Sensordaten**: Genaue Schaetzungen erfordern oft nur eine Teilmenge der verfuegbaren Sensorfelder; fehlerhafte Sensoren oder unvollstaendige Kovarianzwerte erfordern manuelle Nachbearbeitung.
- Das *robot_localization*-Paket wurde von Grund auf entwickelt, um diese Limitierungen zu ueberwinden (S. 1).

### 2. EKF-Zustandsvektor und Systemmodell
- Der Zustandsvektor **x** ist 12-dimensional und umfasst die vollstaendige 3D-Pose (x, y, z), die 3D-Orientierung (roll, pitch, yaw) und deren jeweilige Geschwindigkeiten (S. 2).
- Rotationswerte werden als Euler-Winkel dargestellt (S. 2).
- Das Systemmodell basiert auf einem nichtlinearen dynamischen System: **x_k = f(x_{k-1}) + w_{k-1}**, wobei f die nichtlineare Zustandsuebergangsfunktion und w das normalverteilte Prozessrauschen ist (S. 2, Gl. 1).
- Das Messmodell lautet: **z_k = h(x_k) + v_k**, wobei h die nichtlineare Sensorabbildung und v das normalverteilte Messrauschen ist (S. 2, Gl. 2).
- Die Zustandsuebergangsfunktion f basiert auf einem kinematischen 3D-Standardmodell aus der Newtonschen Mechanik (S. 2).

### 3. EKF-Algorithmus: Praediktion und Korrektur
- **Praediktionsschritt** (S. 2, Gl. 3--4):
  - Zustandspraediktion: x_hat_k = f(x_{k-1})
  - Kovarianzpraediktion: P_hat_k = F * P_{k-1} * F^T + Q, wobei F die Jacobi-Matrix von f und Q die Prozessrauschkovarianz ist.
- **Korrekturschritt** (S. 2, Gl. 5--7):
  - Kalman-Gain: K = P_hat_k * H^T * (H * P_hat_k * H^T + R)^{-1}
  - Zustandsupdate: x_k = x_hat_k + K * (z - H * x_hat_k)
  - Kovarianzupdate nach Joseph-Form: P_k = (I - K*H) * P_hat_k * (I - K*H)^T + K*R*K^T
- Die Joseph-Form-Kovarianzaktualisierung (Gl. 7) wird verwendet, um die numerische Stabilitaet zu gewaehrleisten und sicherzustellen, dass P_k positiv semi-definit bleibt (S. 2).

### 4. Beobachtungsmatrix und partielle Zustandsupdates
- Die Standard-EKF-Formulierung erfordert, dass H die Jacobi-Matrix der Messfunktion h ist. Um eine breite Palette von Sensoren zu unterstuetzen, wird angenommen, dass jeder Sensor Messungen der Zustandsvariablen liefert. Somit ist H einfach die Einheitsmatrix (S. 2).
- **Partielle Updates** sind ein Kernmerkmal: Wenn ein Sensor nur m von 12 Variablen misst, wird H zu einer m x 12 Matrix mit Einsen nur in den Spalten der gemessenen Variablen (S. 2). Dies erlaubt es, pro Sensor genau zu definieren, welche Zustandskomponenten fusioniert werden.
- Diese Faehigkeit ist kritisch fuer die Verarbeitung von Sensordaten, die nicht alle Zustandsvariablen messen -- was fast immer der Fall ist (S. 2).

### 5. Prozessrauschkovarianz Q als abstimmbarer Parameter
- Die Prozessrauschkovarianz Q ist schwierig fuer eine gegebene Anwendung zu bestimmen. Daher stellt *ekf_localization_node* diese Matrix als konfigurierbaren Parameter bereit, um Nutzern eine zusaetzliche Anpassungsmoeglichkeit zu geben (S. 2).

### 6. Konfigurationsvektor pro Sensor
- Jeder Sensor wird ueber einen booleschen Konfigurationsvektor gesteuert, der bestimmt, welche der 12 Zustandsvariablen (x, y, z, roll, pitch, yaw, x', y', z', roll', pitch', yaw') fusioniert werden (S. 3, Tabelle I).
- Beispiel: Odometrie liefert x'-, y'- und yaw'-Geschwindigkeiten; eine IMU liefert roll, pitch, yaw und deren Aenderungsraten; ein GPS liefert x-, y-, z-Position (S. 3, Tabelle I).
- Die Konfiguration kann auch genutzt werden, um mit bekannten fehlerhaften Sensoren umzugehen: z.B. kann eine IMU mit defektem Gyroskop nur fuer Orientierung genutzt werden, waehrend eine zweite IMU Orientierung und Orientierungsgeschwindigkeit liefert (S. 6).

### 7. GPS-Integration ueber Koordinatentransformation
- Fuer GPS-Sensoren wird eine Transformation T definiert, die das Weltkoordinatensystem des Roboters (odom-Frame, Ursprung am Startpunkt) in UTM-Koordinaten umrechnet (S. 2--3, Gl. 8--9).
- Die initiale Transformation berechnet sich aus der Anfangsorientierung (roll, pitch, yaw) und der ersten GPS-Position (x_UTM_0, y_UTM_0, z_UTM_0) (S. 2, Gl. 8).
- Jede nachfolgende GPS-Messung wird mittels der inversen Transformation T^{-1} in das odom-Frame ueberfuehrt und dann unabhaengig pro GPS fusioniert (S. 3).

### 8. Experimentelle Validierung: Loop-Closure-Genauigkeit
- Testplattform: MobileRobots Pioneer 3 mit Rad-Encodern, zwei Microstrain 3DM-GX2 IMUs und zwei Garmin GPS 18x Einheiten auf einem speziellen Sensortraeger (S. 2--3).
- Testumgebung: Parkplatz, ca. 110 m maximale Distanz vom Ursprung, Gesamtdauer ca. 777 Sekunden. Der Roboter wurde per Joystick gesteuert und kehrte zum Ausgangspunkt zurueck (S. 3).
- Die Daten wurden mit ROS *rosbag* aufgezeichnet und wiederholt abgespielt, um verschiedene Sensorkonfigurationen zu testen (S. 3).
- **Ergebnisse** (S. 3, Tabelle II):
  - Nur Odometrie (Dead Reckoning): Loop-Closure-Fehler 69,65 m / 160,33 m (x/y), geschaetzte Standardabweichung 593,09 m / 359,08 m -- Filterinstabilitaet.
  - Odometrie + eine IMU: Fehler 10,23 m / 47,09 m, Std.-Abw. 5,25 m / 5,25 m.
  - Odometrie + zwei IMUs: Fehler 12,90 m / 40,72 m, Std.-Abw. 5,23 m / 5,24 m (zweite IMU fiel nach ca. 45% der Sammlung aus).
  - Odometrie + zwei IMUs + ein GPS: Fehler 1,21 m / 0,26 m, Std.-Abw. 0,64 m / 0,40 m.
  - Odometrie + zwei IMUs + zwei GPS: Fehler 0,79 m / 0,58 m, Std.-Abw. 0,54 m / 0,34 m.
- Mehr Sensoren fuehren zu konsistent besserer Zustandsschaetzung (S. 3--5).

### 9. Robustheit bei seltenen absoluten Messungen
- Ein zweites Experiment untersuchte das Filterverhalten bei seltenen GPS-Updates (alle 120 Sekunden) mit Odometrie + zwei IMUs + einem GPS (S. 5).
- GPS-Fixes fuehren zu sichtbaren Spruengen in der Zustandsschaetzung, aber der Kalman-Gain gewichtet die neue Position so, dass die Schaetzung glaettet und die Kovarianzmatrix stabil bleibt (S. 5).
- Trotz grosser Differenzen zwischen Schaetzung und Messung nimmt die Varianz in x und y stetig ab, was die numerische Stabilitaet des Filters belegt (S. 5, Fig. 8b).
- Loop-Closure-Fehler bei seltenen GPS-Updates: 12,06 m / 0,52 m (S. 5).

### 10. Bedeutung der IMU fuer die Orientierungsschaetzung
- Ohne absolute Orientierungsmessung (nur Dead Reckoning) waechst die Kovarianzmatrix rapide, die Korrelation zwischen Yaw und (x,y)-Position fuehrt zu Filterinstabilitaet (S. 5).
- Die Hinzunahme einer IMU loest dieses Problem durch eine um Groessenordnungen bessere Yaw-Geschwindigkeitsmessung gegenueber der Rad-Odometrie sowie durch die Fusion der absoluten Orientierung (S. 5).
- Elektromagnetische Stoerungen koennen die Magnetometer-basierte Heading-Schaetzung der IMU verschlechtern (S. 5).

### 11. Nutzung kinematischer Constraints als implizite Messungen
- Obwohl die Odometrie nur x-Geschwindigkeit und Yaw-Geschwindigkeit misst, koennen durch kinematische Plattform-Constraints zusaetzliche Informationen gewonnen werden: Ein bodengebundener, nicht-holonomer Roboter hat keine z- oder y-Geschwindigkeit. Diese Nullwerte koennen als Messwerte fusioniert werden, sofern die Kovarianzen korrekt gesetzt sind (S. 5, Tabelle I).
- Allgemein gilt: Wenn eine Messung durch kinematische Constraints impliziert wird, sollte sie als tatsaechlicher Messwert behandelt werden (S. 5).

### 12. Erweiterbarkeit auf heterogene Sensortypen
- Das Softwaredesign erlaubt die Integration exterorezeptiver Sensoren wie Laserscanner oder Kameras, sofern diese unterstuetzte ROS-Nachrichtentypen (nav_msgs/Odometry, sensor_msgs/Imu, geometry_msgs/PoseWithCovarianceStamped, geometry_msgs/TwistWithCovarianceStamped) erzeugen (S. 5).
- Beispielsweise koennte der Iterative Closest Point (ICP)-Algorithmus mit RGBD-Sensordaten (z.B. Microsoft Kinect) als zusaetzliche Odometriequelle dienen (S. 5--6).
- Das Paket wurde auch erfolgreich auf eine Parrot AR.Drone 2.0 (Quadcopter) angewendet, mit kamerabasierter Geschwindigkeitsmessung, Barometer-basierter Hoehenbestimmung, IMU und GPS (S. 6).

### 13. Feinkoernige Sensorkontrolle und Fehlerbehandlung
- Die pro-Sensor-Konfiguration erlaubt den Umgang mit bekannten fehlerhaften Sensoren: Einzelne Messdimensionen koennen pro Sensor ein- oder ausgeschaltet werden (S. 6).
- Im Experiment ueberstand die Sensorfusion den Ausfall einer IMU (die nach ca. 45% der Datensammlung keine Daten mehr lieferte), was die Robustheit der Mehrsensorfusion demonstriert (S. 5).

### 14. Geplante Erweiterungen (Future Work)
- **Covariance Override**: Einige Sensortreiber setzen beliebige Kovarianzwerte; kuenftig soll es moeglich sein, diese Werte parametrisierbar zu ueberschreiben, anstatt sie automatisch auf einen kleinen Wert zu setzen (S. 6).
- **Lineare Beschleunigung im Zustandsmodell**: Derzeit wird lineare Beschleunigung nicht im kinematischen Modell beruecksichtigt. Die Integration wuerde die Filtergenauigkeit erhoehen (S. 6).
- **Weitere Zustandsschaetzungsknoten**: Geplant sind ein Unscented Kalman Filter (UKF) und ein Partikelfilter als zusaetzliche Knoten im *robot_localization*-Paket (S. 6).

## Relevanz fuer die Bachelorarbeit

Dieses Paper ist die Primaerquelle fuer das *robot_localization*-Paket, das im AMR-Projekt zur Sensorfusion von Rad-Encoder-Odometrie (ESP32) und IMU-Daten auf dem Raspberry Pi 5 eingesetzt wird. Die detaillierte Beschreibung des 12-dimensionalen EKF-Zustandsvektors, der partiellen Zustandsupdates und der pro-Sensor-Konfiguration ueber boolesche Vektoren ist direkt anwendbar auf die Konfiguration des EKF-Knotens im ROS 2 Navigation Stack. Besonders relevant ist die Erkenntnis, dass kinematische Constraints (z.B. keine laterale Geschwindigkeit beim Differentialantrieb) als implizite Nullmessungen fusioniert werden sollten, sowie die Bedeutung der IMU fuer eine stabile Yaw-Schaetzung, ohne die der EKF bei reiner Rad-Odometrie instabil wird. Die Joseph-Form-Kovarianzaktualisierung und die Moeglichkeit, die Prozessrauschkovarianz Q als Parameter zu exponieren, sind wichtige Implementierungsdetails fuer das Tuning des Filters im realen Einsatz.
