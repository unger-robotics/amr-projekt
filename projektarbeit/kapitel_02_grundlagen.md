# 2. Grundlagen und Stand der Technik

Dieses Kapitel klaert die technische Leitfrage der Arbeit: Welche Grundlagen tragen einen autonomen mobilen Roboter fuer den Transport von Kleinladungstraegern in einer veraenderlichen Innenraumumgebung, und wie lassen sich diese Grundlagen in eine belastbare Systemarchitektur ueberfuehren? Die Darstellung folgt der Terminologie der Roadmap. Im Mittelpunkt stehen der Fahrkern, die Sensor- und Sicherheitsbasis, die verteilte ROS-2-Architektur, die Verfahren fuer Lokalisierung und Kartierung, die Navigation sowie die Interaktionsschichten fuer Bedienung und Sprache. Damit entsteht ein fachlicher Rahmen fuer die spaeteren Kapitel zur Anforderungsanalyse, zum Systemkonzept, zur Implementierung und zur Validierung.

## 2.1 Autonome mobile Roboter in der Intralogistik

Autonome mobile Roboter uebernehmen Transportaufgaben in Umgebungen, deren Wege, Belegungen und Hindernisse nicht dauerhaft fest vorgegeben sind. Diese Eigenschaft unterscheidet sie von fahrerlosen Transportsystemen, die typischerweise an Leitlinien, Magnetbaender oder andere externe Fuehrungsstrukturen gebunden sind. Fuer den Transport von Kleinladungstraegern in Werkstatt-, Labor- oder Wohnungsumgebungen ist diese Unterscheidung grundlegend, weil die Nutzbarkeit nicht nur von der Fahrfunktion, sondern vor allem von der Anpassungsfaehigkeit an wechselnde Randbedingungen abhaengt.

Der fachliche Kern eines AMR liegt deshalb nicht in einem einzelnen Sensor oder in einer einzelnen Softwarebibliothek, sondern in der Kopplung mehrerer Funktionen: Bewegungserzeugung, Zustandsschaetzung, Umgebungswahrnehmung, Pfadplanung, Bahnverfolgung und Sicherheitsreaktion. Die Roadmap ordnet diese Funktionen dem Fahrkern, der Sensor- und Sicherheitsbasis, der Lokalisierung und Kartierung sowie der Navigation zu. Bedienung, Telemetrie und Sprachsteuerung bilden davon getrennte Interaktionsschichten. Diese Trennung reduziert Komplexitaet und verhindert, dass Bedienfunktionen unkontrolliert in sicherheits- oder fahrkritische Ablaeufe eingreifen.

Referenzplattformen aus Forschung und Lehre zeigen regelmaessig eine hierarchische Architektur. Mikrocontroller uebernehmen hardwarenahe und zeitkritische Aufgaben, waehrend leistungsfaehigere Rechner Kartierung, Lokalisierung und Navigation ausfuehren. Die vorliegende Arbeit folgt diesem Grundmuster, verschaerft jedoch die funktionale Trennung: Der Fahrkern und die Sensor- und Sicherheitsbasis laufen auf getrennten ESP32-S3-Knoten, waehrend der Raspberry Pi 5 die hostseitigen ROS-2-Funktionen traegt. Diese Aufteilung dient nicht primaer der Funktionsvielfalt, sondern der Entkopplung zeitkritischer Ablaeufe von blockierenden Sensor- oder Kommunikationszugriffen.

## 2.2 Fahrkern: Differentialantrieb, Kinematik und Odometrie

Der Fahrkern umfasst Antrieb, Odometrie und Grundbewegung. Fuer die vorliegende Plattform ist ein Differentialantrieb relevant. Zwei unabhaengig angetriebene Raeder erzeugen Translation und Rotation, indem sich ihre Winkelgeschwindigkeiten gezielt unterscheiden. Das Modell ist einfach genug fuer eine echtzeitfaehige Regelung und zugleich hinreichend aussagekraeftig fuer die Anbindung an Lokalisierung und Navigation.

Die Vorwaertskinematik beschreibt, wie aus den gemessenen Radwinkelgeschwindigkeiten $\omega_R$ und $\omega_L$ die translatorische Geschwindigkeit $v$ und die Giergeschwindigkeit $\omega$ des Roboters entstehen. Mit dem Radradius $r$ und der Spurbreite $b$ gilt:

$$
v = \frac{r}{2} \left(\omega_R + \omega_L\right)
$$

$$
\omega = \frac{r}{b} \left(\omega_R - \omega_L\right)
$$

Die Inverskinematik bildet den umgekehrten Weg ab. Sie wandelt eine Sollvorgabe aus dem Navigationssystem in Sollwerte fuer linkes und rechtes Rad um:

$$
\omega_L = \frac{v - \omega \cdot \frac{b}{2}}{r}
$$

$$
\omega_R = \frac{v + \omega \cdot \frac{b}{2}}{r}
$$

Diese Gleichungen koppeln den hostseitigen Navigationsstack direkt an die hardwarenahe Antriebsregelung. Damit aus dieser Kopplung reproduzierbare Bewegung entsteht, muss der Fahrkern systematische Fehler begrenzen. Besonders relevant sind Abweichungen im effektiven Raddurchmesser, in der Spurbreite, im Schlupfverhalten und in Totzonen der Motoransteuerung. Die Roadmap formuliert deshalb quantitative Kriterien fuer Geradeausfahrt, Rotation, Stoppverhalten und Wiederholbarkeit. Erst ein charakterisierter Fahrkern kann als belastbare Grundlage fuer die nachfolgenden Ebenen dienen.

Die Odometrie integriert Radbewegungen ueber die Zeit und liefert damit eine lokale Schaetzung der Eigenbewegung. Ihr Vorteil liegt in der hohen Aktualisierungsrate und der unmittelbaren Verfuegbarkeit. Ihre Schwaeche liegt in der Fehlerakkumulation. Systematische Anteile, etwa das Verhaeltnis der effektiven Raddurchmesser $E_d$ und die effektive Spurbreite $E_b$, wirken ueber laengere Fahrstrecken direkt auf die Positions- und Winkelschaetzung. Die UMBmark-Kalibrierung adressiert genau diese Fehlerquellen durch definierte quadratische Fahrmanoever in beiden Drehrichtungen. Das Verfahren reduziert systematische Odometriefehler deutlich und schafft damit eine bessere Ausgangsbasis fuer Sensorfusion und Kartierung.

## 2.3 Sensor- und Sicherheitsbasis

Die Sensor- und Sicherheitsbasis umfasst alle Signale, die den Fahrkern stabilisieren, Gefaehrdungen frueh erkennen oder den Energiezustand ueberwachen. In der Roadmap zaehlen dazu insbesondere IMU, Ultraschallsensor, Cliff-Sensor und Batterieueberwachung. Diese Ebene ergaenzt den Fahrkern um Messgroessen, die aus den Radencodern allein nicht hervorgehen. Gleichzeitig bildet sie die erste technische Schutzschicht gegen unsichere Zustaende.

Die inertiale Messeinheit erfasst Drehraten und Beschleunigungen. Fuer mobile Robotik ist vor allem die Drehrate um die Hochachse relevant, weil sie kurzfristige Orientierungsaenderungen auch dann abbildet, wenn Radschlupf die encoderbasierte Schaetzung verfaelscht. Dem steht eine typische Schwaeche inertialer Sensoren gegenueber: Bias, Drift und temperaturabhaengige Abweichungen verschieben die Schaetzung ueber die Zeit. Deshalb genuegt eine IMU nicht als alleinige Quelle der Pose. Sie gewinnt ihren Wert erst in der Fusion mit Odometrie und gegebenenfalls weiteren absoluten Referenzen.

Der Front-Ultraschallsensor bildet den Nahbereich ab und ergaenzt die flaechige Umgebungswahrnehmung um eine einfache Distanzinformation im direkten Vorfeld. Die Batterieueberwachung erfasst Spannung und Strom, damit Unterspannung frueh erkannt und Schutzreaktionen ausgeloest werden koennen. Beide Funktionen sind fuer einen reproduzierbaren Betrieb wichtiger als ihre vergleichsweise einfache Sensorik vermuten laesst: Ohne Energieueberwachung verliert jede Bewegungsbewertung an Vergleichbarkeit, und ohne Nahbereichserfassung steigt das Risiko, dass kurzreichweitige Hindernisse oder Betriebsgrenzen zu spaet erkannt werden.

Eine besondere Rolle uebernimmt die hardwarenahe Kantenerkennung. Der Cliff-Sensor adressiert eine Gefaehrdung, bei der die Reaktionszeit entscheidend ist. Rein softwarebasierte Navigationsalgorithmen arbeiten mit Verarbeitungsketten, Scheduling und Kommunikationswegen, die zwar im Normalbetrieb ausreichen, aber keinen unmittelbaren Schutz gegen abrupte Kanten garantieren. Deshalb ordnet die Architektur das Signal des Cliff-Sensors einer Sicherheitslogik zu, die Bewegungsfreigaben sofort sperren und eine Notbremsung ausloesen kann. Im Systemkontext handelt es sich nicht um Komfortfunktion, sondern um eine uebergeordnete Schutzmassnahme.

## 2.4 Verteilte Software-Architektur mit ROS 2 und micro-ROS

ROS 2 bildet die Middleware der hostseitigen Systemebene. Das Modell basiert auf ROS-2-Knoten, Topics, Diensten, Aktionen und Launch-Dateien. Der fachliche Nutzen dieser Struktur liegt in der klaren Trennung von Funktionen. Ein Knoten verarbeitet genau abgegrenzte Aufgaben, veroeffentlicht Zustaende oder Messwerte ueber Topics und laesst sich mit anderen Knoten ueber standardisierte Schnittstellen koppeln. Dadurch bleibt das Gesamtsystem erweiterbar, obwohl Wahrnehmung, Lokalisierung, Navigation, Bedienung und Audio parallel laufen.

micro-ROS erweitert diesen Ansatz auf Mikrocontroller. Die beiden ESP32-S3-Knoten treten damit nicht als isolierte Hilfscontroller auf, sondern als eingebundene Teile der Gesamtarchitektur. Fuer die Arbeit ist diese Eigenschaft wesentlich, weil der Fahrkern und die Sensor- und Sicherheitsbasis Zustaende direkt in das ROS-2-System einspeisen, ohne dass eine proprietaere Nebenarchitektur entstehen muss. Die Kommunikation erfolgt ueber serielle UART-Verbindungen beziehungsweise USB-CDC. Gegenueber drahtlosen Verbindungen bietet diese Kette reproduzierbarere Laufzeiten und eine geringere Stoeranfaelligkeit. Fuer einen Regelkreis mit $50\,\mathrm{Hz}$ ist diese Entscheidung keine Nebenbedingung, sondern ein Stabilitaetsfaktor.

Die verteilte Aufteilung folgt einem klaren Architekturprinzip. Der Drive-Knoten verarbeitet Antriebsregelung und encodernahe Funktionen. Der Sensor-Knoten verarbeitet I2C-basierte Sensorik, Batteriedaten und sicherheitsnahe Signale. Der Raspberry Pi 5 uebernimmt Kartierung, Lokalisierung, Navigation, Benutzeroberflaeche und hoehere Interaktionsfunktionen. Damit trennt die Architektur zeitkritische Ablaeufe von rechen- und kommunikationsintensiven Hostaufgaben. Gleichzeitig verhindert die physische Aufteilung, dass langsame Sensorzugriffe die Motorregelung blockieren. Diese Entkopplung ist ein direkter Beitrag zur Robustheit des Fahrkerns.

## 2.5 Lokalisierung und Kartierung

Lokalisierung und Kartierung beantworten zwei eng gekoppelte Fragen: Wo befindet sich der Roboter, und wie sieht die Umgebung aus? Fuer ein AMR mit veraenderlicher Einsatzumgebung genuegt weder reine Odometrie noch eine einmalig eingemessene Infrastruktur. Erforderlich ist eine Karten- und Transformationskette, die Sensordaten raeumlich einordnet, Drift begrenzt und Wiederanlauf nach Neustart ermoeglicht. Die Roadmap ordnet diese Aufgaben der Ebene „Lokalisierung und Kartierung“ zu. Zu dieser Ebene gehoeren LiDAR, TF-Baum, SLAM-Verfahren, Kartenrepraesentation und Re-Lokalisierung.

Der LiDAR liefert Distanzmessungen in einer Ebene und erzeugt daraus einen Scan der Umgebung. Die geometrische Nutzbarkeit dieses Scans haengt nicht nur vom Sensor selbst ab, sondern auch von den zugehoerigen Koordinatensystemen. Der TF-Baum verknuepft Basisrahmen, Sensorraeume und Weltbezug. Fehler in diesen Transformationen erzeugen keine kleinen Schoenheitsfehler, sondern systematische Kartenverzerrungen, instabile Re-Lokalisierung oder Spruenge zwischen Bezugssystemen. Deshalb gehoert die Extrinsik des Sensors fachlich zur Kartierungsgrundlage und nicht erst zur spaeteren Optimierung.

Fuer die simultane Lokalisierung und Kartierung kommt ein SLAM-Verfahren zum Einsatz. Die SLAM Toolbox kombiniert Scan-Matching mit einer graphbasierten Optimierung und erzeugt daraus eine konsistente Karte, obwohl Odometrie und Einzelmessungen fehlerbehaftet sind. Der fachliche Wert eines solchen Verfahrens liegt nicht nur in der Kartenerzeugung, sondern in der Korrektur lokaler Schaetzfehler durch globale Konsistenzbedingungen. Das Ergebnis ist eine wiederverwendbare Karte, auf deren Basis spaetere Zielanfahrten ueberhaupt erst reproduzierbar werden.

## 2.6 Navigation, Sicherheitslogik und Missionslogik

Navigation beginnt erst dann sinnvoll, wenn Fahrkern sowie Lokalisierung und Kartierung hinreichend belastbar arbeiten. Fachlich umfasst die Navigation die globale Pfadplanung, die lokale Bahnverfolgung, die Hindernisberuecksichtigung und das Recovery-Verhalten. In der Roadmap ist diese Ebene explizit von der Bedienung getrennt. Diese Trennung verhindert, dass einzelne Bedienereignisse oder Sensoreffekte ungefiltert in Fahrbefehle muenden.

Nav2 stellt dafuer einen modularen Navigationsstack bereit. Ein globaler Planer erzeugt einen Weg durch die Karte. Ein lokaler Regler verfolgt diesen Weg unter Beruecksichtigung der Fahrzeugkinematik und der aktuellen Hindernissituation. Costmaps bilden statische und dynamische Hindernisse als Kostenfelder ab. Behavior Trees koordinieren diese Funktionsbloecke und verknuepfen Standardverhalten mit Fehlerreaktionen wie Anhalten, Ruecksetzen oder Neuversuch. Gegenueber starren Zustandsmaschinen bietet diese Struktur eine bessere Erweiterbarkeit bei gleichzeitig klaren Entscheidungswegen.

Fuer die vorliegende Arbeit reicht reine Navigation jedoch nicht aus. Zwischen Interaktion und Bewegungsfreigabe ist eine Freigabelogik erforderlich. Sie bewertet, ob ein Befehl zulaessig ist, in welchem Betriebsmodus sich das System befindet und ob Sicherheitsbedingungen erfuellt sind. Erst danach entsteht ein Missionskommando, etwa eine Zielanfahrt oder ein definierter Betriebswechsel. Die eigentliche Bewegungsausgabe bleibt weiterhin an Navigation, Fahrkern und Sicherheitslogik gebunden. Damit gilt als Architekturregel:

$$
\text{Interaktion} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation} \rightarrow \text{Fahrkern}
$$

Diese Kette begrenzt das Risiko unsicherer Direktansteuerung und macht Entscheidungswege nachvollziehbar. Sie ist damit nicht nur ein Softwaremuster, sondern ein Sicherheitsprinzip.

## 2.7 Bedien- und Leitstandsebene

Die Bedien- und Leitstandsebene stellt Beobachtbarkeit und Eingriffsmoeglichkeiten bereit, ohne die innere Fahrlogik aufzuloesen. In der Roadmap gehoeren dazu Dashboard, Telemetrie, manuelle Kommandos, Audio-Rueckmeldungen und weitere Betriebsanzeigen. Fachlich entspricht diese Ebene einem Leitstandkonzept: Zustaende werden sichtbar, Diagnoseinformationen werden gesammelt, Bedienhandlungen werden protokollierbar und Betriebsarten werden nachvollziehbar umgeschaltet.

Fuer ein MINT-orientiertes Entwicklungsprojekt hat diese Ebene einen doppelten Nutzen. Erstens verbessert sie den Betrieb, weil Akkuzustand, Sensordaten, Kamerabilder, Fahrzustaende und Fehlermeldungen zentral beobachtbar werden. Zweitens verbessert sie die Validierung, weil Versuche reproduzierbarer dokumentiert und Fehlersituationen klarer zugeordnet werden koennen. Eine Benutzeroberflaeche ist damit kein Zusatzmodul am Rand, sondern ein Werkzeug zur technischen Beherrschung des Gesamtsystems. Die Roadmap nennt dafuer bereits konkrete Schnittstellen wie `/cmd_vel`, `/servo_cmd`, `/hardware_cmd` und `/audio/play`. Im Architekturkontext gilt jedoch auch hier: Bedienung darf Fahrfunktionen ausloesen, aber sie darf die Sicherheitslogik nicht umgehen.

## 2.8 Sprachschnittstelle als sichere Interaktionsschicht

Die Sprachschnittstelle erweitert die Bedien- und Leitstandsebene um natuerliche Eingaben. Sie ersetzt weder Navigation noch Sicherheitslogik. Ihr fachlicher Zweck besteht darin, Sprachsignale in klar definierte Befehlsabsichten zu ueberfuehren und nur freigegebene Operationen an die uebrige Systemarchitektur weiterzugeben. Die Roadmap ordnet dafuer das ReSpeaker Mic Array v2.0, Sprach-zu-Text-Verarbeitung, Intent-Erkennung, Befehlsmultiplexing und Sprachrueckmeldung einer eigenen Teilarchitektur zu.

Das Sicherheitsprinzip dieser Ebene lautet: Kein Sprachbefehl darf direkt in eine rohe Motoransteuerung uebersetzt werden. Zulaessig ist nur die Kette aus Sprachbefehl, Intent, Freigabelogik und Missionskommando. Sichere Sofortkommandos wie „Stopp“ oder „Halt“ duerfen ausschliesslich einen sicheren Halt ausloesen. Betriebsmodus-Kommandos duerfen Zustaende wechseln, aber keine direkten Geschwindigkeiten setzen. Missionskommandos duerfen Zielpunkte oder Aktionen anfordern, nicht jedoch die Schutzlogik ausser Kraft setzen. Informationskommandos dienen der Zustandsabfrage und unterstuetzen die Bedienung bei geringem Risiko. Damit bleibt die Sprachschnittstelle eine Interaktionsschicht und wird nicht zu einem unsicheren Parallelpfad in den Fahrkern.

## 2.9 Zusammenfassung

Der Stand der Technik zeigt kein einzelnes Schluesselmodul, sondern eine funktional geschichtete Architektur. Der Fahrkern erzeugt reproduzierbare Grundbewegung. Die Sensor- und Sicherheitsbasis ergaenzt den Fahrkern um robuste Mess- und Schutzfunktionen. ROS 2 und micro-ROS koppeln Host- und Mikrocontroller-Ebene in einer verteilten Struktur. Lokalisierung und Kartierung schaffen den raeumlichen Bezug. Navigation ueberfuehrt Kartenwissen in sichere Zielanfahrten. Bedien- und Leitstandsebene sowie Sprachschnittstelle erweitern das System um beobachtbare und kontrollierte Interaktion, ohne die Sicherheitslogik zu unterlaufen. Aus dieser Schichtung folgt die zentrale Konsequenz fuer die weitere Arbeit: Zusaetzliche Funktionen erhoehen nur dann den Systemwert, wenn der Fahrkern, die Sicherheitslogik und die Freigabelogik zuvor belastbar geschlossen sind.
