# 6. Validierung und Bewertung der Ergebnisse

## 6.1 Leitfrage, Pruefumfang und Datengrundlage

Die Leitfrage dieses Kapitels lautet: In welchem Mass erfuellt das implementierte System die Kernanforderungen an Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Sicherheitslogik unter den Randbedingungen eines Innenraums?

Die Validierung stuetzt sich auf projektinterne Messdaten aus einem Testareal von $10\,\mathrm{m} \times 10\,\mathrm{m}$ Gesamtflaeche (mehrere Raeume) mit statischen und dynamischen Hindernissen. Die Referenzpositionen wurden mit einem Laserdistanzmessgeraet erfasst. Fuer die Offline-Analyse zeichnete `rosbag2` die Topics `/odom`, `/scan`, `/cmd_vel` und `/tf` auf. Die Datengrundlage verbindet damit Bewegungsdaten des Fahrkerns mit Zustandsdaten aus Lokalisierung und Kartierung sowie der Navigation.

Der Pruefumfang gliedert sich in drei Ebenen. Die erste Ebene verifiziert den Fahrkern sowie die Sensor- und Sicherheitsbasis. Die zweite Ebene validiert Lokalisierung und Kartierung, Navigation und Sicherheitslogik im Gesamtsystem. Die dritte Ebene betrachtet erweiterte Funktionen wie Vision und Docking. Diese dritte Ebene gehoert nicht zum zwingenden Kern der Roadmap, ist fuer die technische Einordnung des Prototyps jedoch relevant.

Tabelle 6.1 ordnet die Messgroessen den Kernzielen der Arbeit zu.

| Pruefbereich                  | Messgroesse                                          | Kriterium                                                       |
|------------------------------|----------------------------------------------------|-----------------------------------------------------------------|
| Fahrkern                     | Regeltakt, Jitter, Odometriefehler                 | reproduzierbare Grundbewegung und deterministische Verarbeitung |
| Sensor- und Sicherheitsbasis | Kantenreaktionszeit, Sensorkette                   | sicherer Halt bei erkannter Gefahr                              |
| Lokalisierung und Kartierung | Absolute Trajectory Error, Kartenqualitaet          | belastbare Karte und Re-Lokalisierungsfaehigkeit                 |
| Navigation                   | Zielabweichung, Recovery-Verhalten, Passierabstand | sichere Zielanfahrt auf Kartenbasis                             |
| Sicherheitslogik             | Uebersteuerung konkurrierender Kommandos            | Vorrang des sicheren Zustands                                   |
| Erweiterungsfunktionen       | Inferenzzeit, Docking-Toleranz, Erfolgsquote       | Einordnung von Vision und Docking ausserhalb des Kernpfads       |

## 6.2 Verifikation von Fahrkern sowie Sensor- und Sicherheitsbasis

### 6.2.1 Deterministische Verarbeitung des Fahrkerns

Der Fahrkern muss Bewegungsbefehle mit konstantem Zeitverhalten umsetzen. Gemessen wurde deshalb der Regelzyklus der PID-Schleife auf dem Drive-Knoten. Die Schleife hielt einen Takt von $50\,\mathrm{Hz}$ bei einem Jitter von unter $2\,\mathrm{ms}$ ein. Der Datenverlust der micro-ROS-Kommunikation lag unter $0{,}1\,\%$.

Das Ergebnis belegt eine hinreichend deterministische Verarbeitung fuer den Fahrkern. Die Trennung zwischen Drive-Knoten und Sensor-Knoten erfuellt damit die zentrale Architekturabsicht, blockierende Sensorzugriffe von der Motorregelung fernzuhalten. Das Ergebnis stuetzt insbesondere die nichtfunktionale Anforderung N01.

### 6.2.2 Odometrie und Kalibrierung

Die Grundbewegung des Fahrkerns wurde ueber das UMBmark-Verfahren und eine distanzbasierte Referenzfahrt geprueft. Zehn bidirektionale Testlaeufe zeigten vor der Kalibrierung deutliche Drift-Cluster. Nach der Kalibrierung mit einem effektiven Raddurchmesser von $65{,}67\,\mathrm{mm}$ und angepasster Spurbreite sank der systematische Fehler um den Faktor $10$ bis $20$.

Eine Geradeausfahrt ueber $1{,}0\,\mathrm{m}$ wurde jeweils ohne und mit aktivierter IMU-Heading-Korrektur durchgefuehrt. Ohne IMU-Korrektur betrug die Odometrie-Strecke $1{,}005\,\mathrm{m}$ (Fehler $0{,}5\,\%$), die Lateraldrift $3{,}6\,\mathrm{cm}$ und der Gyro-Heading $+5{,}57^\circ$. Der Heading-Grenzwert von $5^\circ$ wurde damit knapp ueberschritten. Mit aktivierter IMU-Korrektur sank die Lateraldrift auf $2{,}1\,\mathrm{cm}$ und der Gyro-Heading auf $+0{,}06^\circ$. Die Odometrie-Strecke betrug $1{,}003\,\mathrm{m}$ (Fehler $0{,}3\,\%$). Der verbleibende Gyro-Bias lag bei $-0{,}004\,\mathrm{deg/s}$ gegenueber $+0{,}040\,\mathrm{deg/s}$ ohne Korrektur.

Ergaenzend wurde eine geschlossene $360^\circ$-Rotation geprueft. Der Roboter erreichte $358{,}1^\circ$, was einem Winkelfehler von $1{,}88^\circ$ entspricht. Das Akzeptanzkriterium von $5^\circ$ wurde damit deutlich unterschritten. Der Gyro-Bias waehrend der Rotation betrug $-0{,}012\,\mathrm{deg/s}$.

Das Ergebnis belegt zwei Punkte. Erstens ist die IMU-Heading-Korrektur fuer eine reproduzierbare Geradeausfahrt notwendig, nicht optional: Ohne sie ueberschreitet der Heading-Fehler den Grenzwert. Zweitens erreicht der Fahrkern nach Kalibrierung sowohl bei linearer Fahrt als auch bei Rotation die geforderten Akzeptanzkriterien (Lateraldrift $<5\,\mathrm{cm}$, Heading-Fehler $<5^\circ$, Winkelfehler Rotation $<5^\circ$). Fuer die Zielgroesse einer belastbaren Innenraum-Navigation ist die Kalibrierung einschliesslich IMU-Korrektur damit Voraussetzung.

### 6.2.3 Reaktionszeit der Sicherheitskette

Die Sicherheitskette wurde mit einem dedizierten Latenztest (`cliff_latency_test`) unter realistischen Fahrbedingungen geprueft. Der Roboter fuhr mit $0{,}2\,\mathrm{m/s}$ auf eine Tischkante zu. Gemessen wurde die vollstaendige Signalkette von der Detektion am Kanten-Sensor ueber das Topic `/cliff`, die Verarbeitung im `cliff_safety_node` und den daraus resultierenden Stoppbefehl an den Drive-Knoten. Die End-to-End-Latenz betrug $2{,}0\,\mathrm{ms}$ bei einem Sensor-Intervall von $59{,}2\,\mathrm{ms}$. Der resultierende Bremsweg lag bei $1{,}0\,\mathrm{cm}$. Das Akzeptanzkriterium von $50\,\mathrm{ms}$ wurde damit um mehr als eine Groessenordnung unterschritten.

Das Ergebnis erfuellt die zentrale Forderung der Sensor- und Sicherheitsbasis: Ein erkannter Gefahrenzustand fuehrt reproduzierbar in einen sicheren Halt. Die gemessene Latenz von $2{,}0\,\mathrm{ms}$ zeigt, dass die signalverarbeitende Kette nach der Detektion nahezu verzoegerungsfrei reagiert. Der begrenzende Faktor ist das Sensor-Intervall, nicht die Verarbeitungszeit. Die Sicherheitslogik reagiert damit deutlich schneller als ein regulaerer Replanning-Zyklus der Navigation. Fuer Kantenereignisse greift der Schutzpfad vor dem Komfortpfad.

### 6.2.4 Einzelbewertung der Sensorik

Die Sensor- und Sicherheitsbasis umfasst vier Sensorgruppen: Ultraschall, Cliff-Sensor, IMU und Batteriemonitoring. Jede Gruppe wurde einzeln gegen ihre Akzeptanzkriterien geprueft. Die Messungen erfolgten am 09.03.2026 mit dem Validierungsskript `sensor_test.py`.

**Ultraschall (HC-SR04).** Der Ultraschallsensor erreichte eine Rate von $9{,}2\,\mathrm{Hz}$ (Soll $\geq 7{,}0\,\mathrm{Hz}$). Bei einer Referenzdistanz von $0{,}230\,\mathrm{m}$ betrug der gemessene Wert $0{,}232\,\mathrm{m}$, was einem Fehler von $0{,}8\,\%$ entspricht (Soll $< 5\,\%$). Die Wiederholbarkeit lag bei einer Standardabweichung von $1{,}6\,\mathrm{mm}$ (Soll $< 15\,\mathrm{mm}$). Der Messbereich erstreckt sich von $0{,}020\,\mathrm{m}$ bis $4{,}000\,\mathrm{m}$ bei einem Oeffnungswinkel von $0{,}260\,\mathrm{rad}$. Alle vier Ultraschall-Kriterien sind erfuellt.

**Cliff-Sensor (MH-B IR).** Der Cliff-Sensor erreichte eine Rate von $16{,}8\,\mathrm{Hz}$ (Soll $\geq 15{,}0\,\mathrm{Hz}$). Bei $60$ Bodenproben traten $0$ Fehlalarme auf. Die Erkennungsreaktionszeit bei tatsaechlicher Kante betrug $1\,\mathrm{ms}$. Alle drei Cliff-Kriterien sind erfuellt.

**IMU (MPU-6050).** Die IMU-Rate lag zwischen $30{,}4\,\mathrm{Hz}$ und $35{,}2\,\mathrm{Hz}$ (Soll $\geq 15\,\mathrm{Hz}$). Die Gyro-Drift betrug $0{,}463\,\mathrm{deg/min}$ (Soll $< 1{,}0\,\mathrm{deg/min}$). Der Beschleunigungsmesser-Bias lag bei $0{,}43\,\mathrm{m/s^2}$ (Soll $< 0{,}6\,\mathrm{m/s^2}$). Eine motorgetriebene $90^\circ$-Rotation erreichte $88{,}5^\circ$ bei einem Fehler von $1{,}45^\circ$ (Soll $< 2^\circ$) und einem Gyro-Bias von $+0{,}037\,\mathrm{deg/s}$ ueber $4{,}4\,\mathrm{s}$ Dauer. Der Heading-Vergleich zwischen Odometrie und Gyroskop zeigte eine Differenz von $0{,}01^\circ$ (Soll $< 5^\circ$). Alle vier IMU-Kriterien sind erfuellt.

**Batteriemonitoring (INA260).** Der Spannungs- und Stromsensor wird mit $2\,\mathrm{Hz}$ ueber I2C abgefragt. Die Unterspannungsabschaltung bei $< 9{,}5\,\mathrm{V}$ mit $0{,}3\,\mathrm{V}$ Hysterese ist firmware-seitig konfiguriert. Eine separate Vermessung der Abschaltschwelle unter Last wurde nicht durchgefuehrt, da ein kontrolliertes Tiefentladen des Akkus das Testsystem gefaehrden wuerde. Der Funktionsnachweis ergibt sich aus der kontinuierlichen Telemetrie waehrend aller Testlaeufe.

**Zusammenfassung.** Alle sieben Sensor-Testfaelle und alle vier IMU-Testfaelle bestehen ihre jeweiligen Akzeptanzkriterien ($11/11$ PASS). Die Sensor- und Sicherheitsbasis erfuellt damit sowohl die Schutzfunktion (Cliff-Latenz, Fehlalarmfreiheit) als auch die Zustandserfassung (Ultraschall-Genauigkeit, IMU-Drift, Rotationsgenauigkeit). Die IMU-Plausibilisierung ist ueber Drift, Bias und Rotationsgenauigkeit belegt.

## 6.3 Validierung von Lokalisierung, Kartierung und Navigation

### 6.3.1 Lokalisierung und Kartierung im Innenraum

Lokalisierung und Kartierung wurden ueber den Absolute Trajectory Error, kurz ATE, und die Wiederholbarkeit der erzeugten Karte bewertet. Der mittlere ATE der `slam_toolbox` betrug $0{,}16\,\mathrm{m}$. Das Akzeptanzkriterium lag bei $0{,}20\,\mathrm{m}$.

Der gemessene ATE unterschreitet das Akzeptanzkriterium um $0{,}04\,\mathrm{m}$. Fuer einen kostenguenstigen Innenraum-Prototyp ist das Ergebnis ausreichend, um Ziele auf Kartenbasis anzufahren und nach einem Neustart wieder zu lokalisieren. Die Kernanforderung an Lokalisierung und Kartierung gilt damit auf Basis der vorliegenden Messdaten als erfuellt.

### 6.3.2 Zielanfahrt und Bahnverfolgung

Die Qualitaet der Zielanfahrt wurde ueber Punkt-zu-Punkt-Fahrten bewertet. Die mittlere Positionsabweichung betrug $6{,}4\,\mathrm{cm}$, die mittlere Winkelabweichung $4{,}2^\circ$.

Diese Werte zeigen eine fuer die Innenraumanwendung brauchbare Zielgenauigkeit. Die Abweichungen liegen in einer Groessenordnung, die eine zuverlaessige Navigation zwischen definierten Zielpunkten erlaubt. Die Zielanfahrt bestaetigt zugleich, dass die zuvor kalibrierte Odometrie, die IMU-Korrektur und die globale Kartenreferenz im Betrieb zusammenwirken.

### 6.3.3 Hindernisvermeidung und Recovery-Verhalten

Die Navigation musste nicht nur Zielpunkte erreichen, sondern auf Stoerungen geordnet reagieren. Der Nav2-Stack umfuhr statische Hindernisse mit einem minimalen Passierabstand von $12\,\mathrm{cm}$. In Situationen ohne gueltigen Pfad loesten die Recovery-Verfahren `Spin`, `BackUp` und `Wait` insgesamt $80\,\%$ der Blockaden eigenstaendig auf.

Das Ergebnis zeigt zwei Punkte. Erstens arbeitet die lokale Bahnverfolgung auch in Engstellen noch kontrolliert. Zweitens beseitigt das Recovery-Verhalten einen grossen Teil typischer Sackgassen, jedoch nicht alle. Die Navigation erreicht damit ein belastbares, aber noch nicht vollstaendiges Robustheitsniveau.

### 6.3.4 Vorrang des sicheren Zustands

Die Sicherheitslogik wurde in einer gezielt erzeugten Konfliktsituation geprueft. Die Navigation plante einen formal gueltigen Pfad ueber eine geoeffnete Bodenluke. Sobald der Kanten-Sensor am Sensor-Knoten ausloeste, ueberstimmte der `cliff_safety_node` die anliegenden Navigationskommandos. Das Fahrzeug kam $3\,\mathrm{cm}$ vor der Absturzkante zum Stillstand.

Die Messung belegt den Vorrang des sicheren Zustands vor einer weiterhin gueltigen Bewegungsplanung. Fuer die Architektur ist dieses Ergebnis zentral: Nicht das zuletzt berechnete Bewegungsziel entscheidet ueber die Aktorik, sondern die Sicherheitslogik mit hoeherer Prioritaet. Damit bestaetigt der Versuch die vorgesehene Hierarchie aus Navigation, Sicherheitslogik und Fahrkern.

## 6.4 Einordnung der Bedien- und Leitstandsebene sowie der Systemlast

Die Bedien- und Leitstandsebene bildet das Betriebswerkzeug des Systems. Fuer die Validierung relevant sind Beobachtbarkeit, Zustandsdarstellung und die Trennung zwischen fahrkritischem Kern und benutzerseitiger Interaktion. Die Datengrundlage dieses Kapitels enthaelt dafuer keine eigenstaendige Usability-Messreihe, wohl aber Last- und Betriebsdaten.

Der Raspberry Pi 5 blieb im regulaeren Betrieb unter $80\,\%$ CPU-Last. Der Docker-Container fuer ROS-2-Integration und MJPEG-Stream lag im Mittel bei etwa $35\,\%$ Auslastung. Der hardwarebeschleunigte Vision-Prozess `host_hailo_runner.py` lief nativ auf dem Host und band den PCIe-Beschleuniger ohne erhebliche Zusatzlast fuer die CPU ein. Auf Mikrocontroller-Ebene beanspruchte die Firmware des Drive-Knotens auf Core 1 weniger als $40\,\%$ der verfuegbaren Rechenkapazitaet. Der Regulated Pure Pursuit Controller auf dem Raspberry Pi erreichte Rechenraten von mehr als $2{.}000\,\mathrm{Hz}$ bei einem geforderten Minimum von $100\,\mathrm{Hz}$.

Diese Messdaten belegen keine Benutzerqualitaet im engeren Sinn, sie belegen jedoch die technische Tragfaehigkeit der Ebenentrennung. Telemetrie, Video und erweiterte Vision belasten den Fahrkern nicht in kritischem Mass. Fuer die Bedien- und Leitstandsebene bedeutet das: Die Beobachtung des Systems bleibt moeglich, ohne die fahrkritische Kette strukturell zu destabilisieren.

## 6.5 Explorative Bewertung von Vision und Docking

### 6.5.1 Vision-Pipeline

Die Vision-Pipeline gehoert zur erweiterten Interaktions- und Wahrnehmungsebene oberhalb des Fahrkerns. Die gemessene Inferenzzeit des Hailo-8L mit dem Modell `yolov8s` betrug im Mittel rund $34\,\mathrm{ms}$ pro Bild. Das Projektkriterium lag bei weniger als $50\,\mathrm{ms}$ pro Bild.

Damit erfuellt die lokale Bildverarbeitung das vorgegebene Zeitkriterium. Das Ergebnis rechtfertigt die Einordnung der Vision-Pipeline als echtzeitnahe Erweiterung. Gleichwohl bleibt die Funktion ausserhalb des zwingenden Sicherheits- und Navigationskerns, da aus der Objekterkennung keine direkte, unueberwachte Motoransteuerung folgt.

### 6.5.2 Docking als Erweiterungsfunktion

Das Docking-Verfahren verbindet ArUco-Marker-Erkennung mit der Vision-Pipeline. Nach Optimierung der Dreifach-Bedingung (Ultraschall $\leq 0{,}30\,\mathrm{m}$, Marker sichtbar, lateraler Versatz $\leq 5\,\mathrm{cm}$) erreichten alle $10$ Docking-Versuche die vorgegebene Toleranz. Der mittlere laterale Versatz betrug $0{,}73\,\mathrm{cm}$, der mittlere Orientierungsfehler $14{,}1^\circ$.

Die verbesserte Erfolgsquote von $100\,\%$ gegenueber der initialen Messung ($80\,\%$) resultiert aus der Verkuerzung der Docking-Distanz von $0{,}60\,\mathrm{m}$ auf $0{,}30\,\mathrm{m}$ und der Einfuehrung einer Fehlausrichtungs-Recovery mit Rueckwaertsfahrt und Neuausrichtung. Die hoehere Orientierungsstreuung ($14{,}1^\circ$ gegenueber $2{,}8^\circ$) deutet darauf hin, dass die engere Distanz den lateralen Versatz auf Kosten der Winkelgenauigkeit verbessert. Als Erweiterungsfunktion ist das Ergebnis aussagekraeftig, weil es die Grenzen monokularer Bildauswertung unter variabler Beleuchtung offenlegt.

## 6.6 Soll-Ist-Vergleich der Anforderungen

Tabelle 6.2 fasst die Anforderungen aus Kapitel 3 mit dem Stand der vorliegenden Messdaten zusammen. Die Bewertung unterscheidet bewusst zwischen „erfuellt", „teilweise erfuellt" und „nicht geprueft". Diese Unterscheidung trennt belegte Ergebnisse von plausiblen, aber noch unvollstaendig vermessenen Annahmen.

| ID  | Anforderung                                                     | Bewertung         | Begruendung                                                                                                                                                                                                     |
|-----|-----------------------------------------------------------------|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| F01 | Fahrkern mit reproduzierbarer Grundbewegung                     | erfuellt           | Geradeausfahrt mit IMU-Korrektur ($2{,}1\,\mathrm{cm}$ Drift, $0{,}06^\circ$ Heading) und $360^\circ$-Rotation ($1{,}88^\circ$ Fehler) erfuellen alle drei Akzeptanzkriterien.                                |
| F02 | Sensor- und Sicherheitsbasis mit priorisierten Schutzfunktionen | erfuellt           | Kanten-Reaktionszeit $2{,}0\,\mathrm{ms}$ (End-to-End), Ultraschall $0{,}8\,\%$ Fehler, IMU-Drift $0{,}463\,\mathrm{deg/min}$, $90^\circ$-Rotation $1{,}45^\circ$ Fehler, $0$ Cliff-Fehlalarme. Alle $11/11$ Sensorik-Testfaelle bestanden. |
| F03 | Lokalisierung und Kartierung fuer den Innenraum                  | erfuellt           | Der mittlere ATE von $0{,}16\,\mathrm{m}$ unterschreitet das Kriterium von $0{,}20\,\mathrm{m}$.                                                                                                               |
| F04 | Navigation mit Missionslogik und Recovery-Verhalten             | teilweise erfuellt | Zielanfahrt, Hindernisvermeidung und Recovery-Verhalten sind belegt. Die Recovery-Verfahren loesen $80\,\%$ der Blockaden, aber nicht alle.                                                                     |
| F05 | Bedien- und Leitstandsebene als Betriebswerkzeug                | teilweise erfuellt | Lastdaten und Betriebsfaehigkeit stuetzen die technische Umsetzbarkeit. Eine eigenstaendige Messreihe zur Bedienqualitaet wurde nicht durchgefuehrt.                                                                |
| F06 | Freigabelogik mit sicheren Zustandsuebergaengen                   | teilweise erfuellt | Der Vorrang des sicheren Zustands ist ueber den Cliff-Versuch belegt. Eine vollstaendige Pruefung aller Kommandoklassen liegt nicht vor.                                                                          |
| F07 | Sprachschnittstelle als anschlussfaehige Erweiterung             | nicht geprueft     | Die Sprachschnittstelle ist architektonisch vorbereitet, aber nicht Gegenstand der Kernvalidierung.                                                                                                            |
| N01 | Deterministische Verarbeitung im Fahrkern                       | erfuellt           | $50\,\mathrm{Hz}$ Regeltakt, Jitter unter $2\,\mathrm{ms}$, geringe Paketverluste.                                                                                                                             |
| N02 | Modulare und wartbare Systemstruktur                            | nicht geprueft     | Die Architektur ist umgesetzt, wurde in diesem Kapitel aber nicht mit einem separaten Wartbarkeitskriterium vermessen.                                                                                         |
| N03 | Robuste Kommunikation und Fehlerbehandlung                      | teilweise erfuellt | Geringer Datenverlust ist belegt. Ein vollstaendiger Wiederanlauftest der Kommunikationskette wird in diesem Kapitel nicht dokumentiert.                                                                        |
| N04 | Beobachtbarkeit und Nachvollziehbarkeit                         | teilweise erfuellt | `rosbag2`, Telemetrie und Lastdaten zeigen Beobachtbarkeit. Ein explizites Diagnosekriterium wurde nicht separat vermessen.                                                                                    |
| N05 | Erweiterbarkeit der Interaktionsschicht                         | nicht geprueft     | Die Architektur erlaubt Vision, Audio und Sprachschnittstelle, wurde dafuer aber nicht mit einem formalen Kriterium getestet.                                                                                   |

## 6.7 Schlussfolgerung aus der Validierung

Die Validierung zeigt ein klares Gesamtbild. Der Prototyp erfuellt die Kernziele fuer Lokalisierung und Kartierung, fuer die sichere Navigation auf Kartenbasis und fuer die deterministische Verarbeitung im Fahrkern. Die Sicherheitslogik greift im Konfliktfall zuverlaessig vor der Navigation ein. Damit ist die zentrale Architekturentscheidung der Arbeit technisch bestaetigt.

Gleichzeitig zeigt die Validierung die offenen Punkte praezise. Die Grundbewegung des Fahrkerns ist nach Kalibrierung und IMU-Korrektur ueber alle drei Akzeptanzkriterien belegt. Die Sensor- und Sicherheitsbasis ist vollstaendig validiert: Alle $11$ Sensorik-Testfaelle bestehen ihre Akzeptanzkriterien, die Kanten-Reaktionszeit liegt bei $2{,}0\,\mathrm{ms}$ und die IMU-Plausibilisierung ist ueber Drift, Bias und Rotationsgenauigkeit belegt. Die Bedien- und Leitstandsebene ist technisch tragfaehig, aber nicht mit einer eigenstaendigen Messreihe zur Bedienqualitaet bewertet. Die Sprachschnittstelle bleibt eine vorbereitete Erweiterung und gehoert folgerichtig nicht zum belegten Kernumfang.

Fuer die Projektarbeit folgt daraus ein belastbarer Schluss: Das System erreicht eine funktionsfaehige und sicher priorisierte Innenraum-Mobilitaet auf Basis einer verteilten, kostenguenstigen Architektur. Der Fahrkern erfuellt nach Kalibrierung und IMU-Korrektur saemtliche Akzeptanzkriterien fuer Grundbewegung und Rotation. Die Sensor- und Sicherheitsbasis ist mit der Einzelbewertung aller Sensorgruppen vollstaendig belegt. Die groessten Verbesserungshebel liegen nicht mehr im Fahrkern, in der Sensorik oder im Grundprinzip der Architektur, sondern in der Robustheit des Recovery-Verhaltens und in der systematischen Vermessung der erweiterten Interaktionsschicht.
