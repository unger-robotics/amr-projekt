# 3. Anforderungsanalyse

## 3.1 Leitfrage, Einsatzszenario und Systemgrenze

Die Leitfrage dieses Kapitels lautet: Welche Anforderungen muss ein kostenguenstiges autonomes mobiles Robotersystem erfuellen, damit Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene in einem Innenraum belastbar zusammenarbeiten?

Das Einsatzszenario dieser Arbeit ist der autonome Transport kleiner Nutzlasten zwischen definierten Zielpunkten in einem strukturierten Innenraum. Die Referenzumgebung entspricht einer wohnungs- oder laboraehnlichen Flaeche mit Engstellen, Moebeln, Waenden und wechselnden Hindernissen. Damit verlagert sich der Schwerpunkt gegenueber einem klassischen Industrie-Szenario: Nicht maximaler Materialdurchsatz, sondern reproduzierbare Navigation, sichere Bewegungsfreigabe und nachvollziehbare Systemreaktionen stehen im Vordergrund.

Der Anwendungsfall gliedert sich in fuenf aufeinanderfolgende Schritte. Zunaechst erzeugt das System eine Karte oder nutzt eine vorhandene Karte zur Re-Lokalisierung. Anschliessend nimmt die Bedien- und Leitstandsebene ein Missionskommando entgegen, etwa eine Zielanfahrt zu einem definierten Punkt. Danach plant die Navigation einen globalen Pfad und uebergibt Sollgroessen an den Fahrkern. Waehrend der Fahrt ueberwacht die Sensor- und Sicherheitsbasis den Nahbereich, den Energiezustand und sicherheitsnahe Ereignisse. Nach Erreichen des Zielpunkts meldet die Benutzeroberflaeche das Ergebnis und erlaubt einen Folgeauftrag oder einen sicheren Halt.

Fuer die Anforderungsableitung ist die Systemgrenze entscheidend. Bestandteil der Kernarchitektur sind Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation, Sicherheitslogik, Freigabelogik sowie die Bedien- und Leitstandsebene. Eine Sprachschnittstelle gehoert zur geplanten Ausbauarchitektur. Sie darf nur freigegebene Missionskommandos erzeugen und keine rohe Motoransteuerung ausloesen. Nicht Gegenstand der Kernvalidierung sind Aussenbetrieb, Treppenfahrt, freies semantisches Weltmodell oder vollautomatisches Greifen.

---

## 3.2 Technische Randbedingungen und Restriktionen

### 3.2.1 Hardware- und Plattformrandbedingungen

Die Systemarchitektur folgt einer verteilten Aufteilung zwischen Host-Ebene und Mikrocontroller-Ebene. Der Raspberry Pi 5 uebernimmt hostseitige Funktionen wie Lokalisierung und Kartierung, Navigation, Benutzeroberflaeche, Telemetrie, Audio-Rueckmeldung und spaetere Sprachverarbeitung. Zwei XIAO-ESP32-S3-Mikrocontroller uebernehmen hardwarenahe Aufgaben. Der Drive-Knoten bildet den Fahrkern mit Motoransteuerung, Encoder-Auswertung und Odometrie. Der Sensor-Knoten bildet die Sensor- und Sicherheitsbasis mit IMU, Ultraschall, Kanten-Erkennung und Batterieueberwachung. Diese Rollenverteilung entspricht der Roadmap-Terminologie und trennt zeitkritische Regelung von blockierenden Sensorzugriffen. fileciteturn4file0

Als Sensorik dienen ein LiDAR fuer die 2D-Umgebungserfassung, eine inertiale Messeinheit fuer Drehraten- und Beschleunigungsdaten, ein Ultraschallsensor fuer den Nahbereich, ein Cliff-Sensor fuer Kanten und eine Batterieueberwachung fuer den Energiezustand. Die Referenz-Roadmap ordnet diese Komponenten explizit den Phasen Fahrkern, Sensor- und Sicherheitsbasis sowie Lokalisierung und Kartierung zu. fileciteturn4file5turn4file14

### 3.2.2 Software- und Kommunikationsrandbedingungen

Die Host-Software basiert auf ROS 2 Humble. Da das Zielsystem Debian Trixie nutzt, laeuft der ROS-2-Stack in einer Container-Umgebung. Die Mikrocontroller werden ueber micro-ROS als ROS-2-Teilnehmer eingebunden. Fuer die Kommunikation zwischen Host und Mikrocontrollern kommt eine serielle UART-Verbindung ueber USB-CDC zum Einsatz. Die Anforderung folgt nicht aus Bequemlichkeit, sondern aus dem Bedarf an reproduzierbaren Laufzeiten. Eine drahtlose Verbindung wuerde die zeitliche Streuung der Kommandokette erhoehen und die Bewertung des Fahrkerns erschweren. Die bisherige Fassung von Kapitel 3 setzt fuer den Regelkreis einen Arbeitstakt von $50\,\mathrm{Hz}$ an. fileciteturn4file3turn4file1

Die Softwarearchitektur trennt Interaktion, Freigabelogik, Missionskommando, Navigation und Fahrkern. Daraus folgt eine verbindliche Befehlskette:

$$
\text{Interaktion} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation} \rightarrow \text{Fahrkern}
$$

Jede Anforderung, die Kommandos erzeugt oder verarbeitet, muss diese Kette einhalten.

### 3.2.3 Umgebungs- und Sicherheitsrandbedingungen

Die Arbeit betrachtet einen ebenen Innenraum mit bekannten oder kartierbaren Strukturen. Zulaessig sind Waende, Moebel, Tueren, Engstellen und bewegliche Hindernisse wie Personen. Nicht zulaessig sind Aussenflaechen, nasse Untergruende, starke Steigungen oder ungesicherte Treppenfahrten. Eine erkannte Kante ist kein zu passierendes Hindernis, sondern ein Abbruchkriterium fuer die Bewegung.

Die Zielgeschwindigkeit betraegt $0{,}4\,\mathrm{m/s}$. Dieser Wert begrenzt die maximale Dynamik und reduziert zugleich die Anforderungen an Sensorreichweite, Bremsweg und Kollisionsvermeidung. Fuer Zielanfahrten gelten als Orientierungswerte eine laterale Zielabweichung von hoechstens $0{,}10\,\mathrm{m}$ und ein Orientierungsfehler von hoechstens $8^\circ$. Diese Groessen dienen im weiteren Verlauf als Referenz fuer funktionale Anforderungen und Akzeptanzkriterien. fileciteturn4file1turn4file6

---

## 3.3 Funktionale Anforderungen

### F01 — Fahrkern mit reproduzierbarer Grundbewegung

Der Fahrkern muss lineare und rotatorische Bewegung reproduzierbar ausfuehren. Dazu gehoeren Motoransteuerung, Encoder-Auswertung, Odometrie und die Umsetzung von Geschwindigkeitskommandos. Der Fahrkern muss eine Geradeausfahrt ueber $1\,\mathrm{m}$ mit kleinem Seitenfehler, eine Rotation um $360^\circ$ mit reproduzierbarem Winkelfehler und einen sicheren Stopp ohne ungewolltes Nachlaufen unterstuetzen. Diese Forderung leitet sich direkt aus Phase 1 der Roadmap ab. fileciteturn4file5

### F02 — Sensor- und Sicherheitsbasis mit priorisierten Schutzfunktionen

Die Sensor- und Sicherheitsbasis muss IMU-Daten, Nahbereichsdaten, Batteriedaten und Kanteninformationen in definierter Form bereitstellen. Sicherheitsnahe Signale muessen gegenueber Komfort- oder Diagnosefunktionen priorisiert werden. Eine erkannte Kante muss die Bewegungsfreigabe sperren und einen sicheren Halt ausloesen. Die Batterieueberwachung muss einen kritischen Energiezustand melden, bevor die Fahrfunktion unkontrolliert ausfaellt. Diese Forderung leitet sich aus Phase 2 der Roadmap ab. fileciteturn4file14

### F03 — Lokalisierung und Kartierung fuer den Innenraum

Das System muss aus LiDAR-Daten, Odometrie und Transformationsbeziehungen eine konsistente Karte erzeugen und sich nach einem Neustart in dieser Karte wieder lokalisieren koennen. Der TF-Baum muss widerspruchsfrei bleiben. Die Kartenaufloesung betraegt als Zielwert $5\,\mathrm{cm}$. Wiederholte Kartierungen desselben Raums duerfen keine ausgepraegten Doppelkonturen erzeugen. Diese Forderung leitet sich aus Phase 3 der Roadmap ab. fileciteturn4file14

### F04 — Navigation mit Missionslogik und Recovery-Verhalten

Die Navigation muss definierte Zielpunkte sicher anfahren. Dazu gehoeren globale Pfadplanung, lokale Bahnverfolgung, Hindernisberuecksichtigung und nachvollziehbares Recovery-Verhalten. Die Navigation darf nur freigegebene Missionskommandos ausfuehren. Einzelne Benutzereingaben oder experimentelle Zusatzmodule duerfen keine direkte Umgehung der Sicherheitslogik erzeugen. Fuer die Kernvalidierung gilt als Zielwert die erfolgreiche Durchfuehrung von $10$ definierten Zielanfahrten ohne Kollision. Diese Forderung leitet sich aus Phase 4 der Roadmap ab. fileciteturn4file14

### F05 — Bedien- und Leitstandsebene als Betriebswerkzeug

Die Bedien- und Leitstandsebene muss Zustaende sichtbar machen und definierte Eingriffe erlauben. Dazu gehoeren Telemetrie, Statusanzeigen, Kamerabild oder Videostream, manuelle Kommandos in freigegebenen Betriebsarten und Audio-Rueckmeldungen. Die Benutzeroberflaeche dient nicht nur der Bedienung, sondern auch der Diagnose und Versuchsdokumentation. Die vorhandenen Schnittstellen `/cmd_vel`, `/servo_cmd`, `/hardware_cmd` und `/audio/play` bilden dafuer die technische Grundlage. Diese Forderung leitet sich aus Ebene B und Phase 5 der Roadmap ab. fileciteturn4file0turn4file14

### F06 — Freigabelogik mit sicheren Zustandsuebergaengen

Die Freigabelogik muss festlegen, welche Kommandos im jeweiligen Betriebszustand zulaessig sind. Sie muss Kommandos freigeben, blockieren oder in sichere Reaktionen umsetzen. Ein Stopp-Kommando hat Vorrang vor allen Fahr- und Missionskommandos. Bedienkommandos duerfen Navigation und Fahrkern beeinflussen, aber nicht die Schutzmechanismen umgehen. Diese Forderung ergibt sich aus der Terminologie-Norm der Roadmap mit den Begriffen Sicherheitslogik, Freigabelogik und Missionskommando. fileciteturn4file0

### F07 — Sprachschnittstelle als anschlussfaehige Erweiterung

Die Sprachschnittstelle soll Sprachsignale in definierte Intents ueberfuehren und daraus freigegebene Missionskommandos ableiten. Die Sprachschnittstelle darf keine rohen Geschwindigkeitsbefehle direkt an den Fahrkern senden. Sichere Sofortkommandos wie „Stopp“ duerfen ausschliesslich einen sicheren Halt anfordern. Diese Forderung gehoert nicht zur Kernvalidierung, aber zur thematischen Erweiterung der Projektarbeit. Die Roadmap ordnet das ReSpeaker Mic Array v2.0, Sprach-zu-Text-Verarbeitung, Intent-Erkennung und Text-zu-Sprache der Ebene der intelligenten Interaktion zu. fileciteturn4file0

---

## 3.4 Nichtfunktionale Anforderungen

### N01 — Deterministische Verarbeitung im Fahrkern

Der Fahrkern muss Sollwerte und Messwerte mit hinreichend konstanter Zykluszeit verarbeiten. Fuer die Motorregelung gilt ein Arbeitstakt von $50\,\mathrm{Hz}$. Die zeitliche Streuung darf den Regelkreis nicht instabil machen. Blockierende I2C-Zugriffe oder nicht deterministische Nebenaufgaben duerfen den Fahrkern nicht unterbrechen. Die bisherige Ausgangsfassung fordert hierfuer einen Jitter von weniger als $2\,\mathrm{ms}$. fileciteturn4file11

### N02 — Modulare und wartbare Systemstruktur

Die Architektur muss Funktionen in getrennten ROS-2-Knoten, Topics und Launch-Dateien abbilden. Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene muessen fachlich getrennt bleiben. Diese Modularitaet erleichtert Fehlersuche, Erweiterung und Wiederverwendung.

### N03 — Robuste Kommunikation und Fehlerbehandlung

Die serielle micro-ROS-Kommunikation muss Verbindungsabbrueche erkennen und einen definierten Wiederanlauf unterstuetzen. Kommunikationsfehler duerfen nicht zu unkontrollierter Weiterfahrt fuehren. Stattdessen muss das System in einen sicheren Zustand wechseln oder auf einen sicheren Halt zurueckfallen. Die Ausgangsfassung von Kapitel 3 nennt den automatischen Wiederanlauf der UART-Kommunikation ausdruecklich als nichtfunktionale Anforderung. fileciteturn4file11

### N04 — Beobachtbarkeit und Nachvollziehbarkeit

Zustaende, Sensordaten, Betriebsarten und Fehlerereignisse muessen so bereitgestellt werden, dass Versuche reproduzierbar ausgewertet werden koennen. Dazu gehoeren Telemetrie, Protokollierung und eine klar strukturierte Benutzeroberflaeche. Eine Bewertung ohne sichtbare Mess- und Zustandsbasis ist nicht belastbar.

### N05 — Erweiterbarkeit der Interaktionsschicht

Die Architektur muss spaetere Erweiterungen wie Sprachschnittstelle, Audio-Rueckmeldung oder zusaetzliche semantische Module aufnehmen koennen, ohne die Kernlogik des Fahrkerns zu veraendern. Erweiterbarkeit bedeutet in diesem Kontext nicht beliebige Offenheit, sondern kontrollierte Kopplung ueber Freigabelogik und Missionskommandos.

---

## 3.5 Priorisierte Anforderungsliste nach MoSCoW

| ID  | Anforderung                                                     | Typ | Prioritaet | Akzeptanzkriterium                                                                                                                                                       |
|-----|-----------------------------------------------------------------|-----|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| F01 | Fahrkern mit reproduzierbarer Grundbewegung                     | F   | M         | Geradeausfahrt ueber $1\,\mathrm{m}$ reproduzierbar; Rotation um $360^\circ$ reproduzierbar; kein ungewolltes Nachlaufen nach Stopp.                                      |
| F02 | Sensor- und Sicherheitsbasis mit priorisierten Schutzfunktionen | F   | M         | IMU, Ultraschall, Kanten-Erkennung und Batterieueberwachung liefern nutzbare Signale; erkannte Kante fuehrt reproduzierbar zum sicheren Halt.                              |
| F03 | Lokalisierung und Kartierung fuer den Innenraum                  | F   | M         | Karte mit Zielaufloesung von $5\,\mathrm{cm}$ erzeugbar; Re-Lokalisierung nach Neustart moeglich; keine ausgepraegten Doppelkonturen.                                       |
| F04 | Navigation mit Missionslogik und Recovery-Verhalten             | F   | M         | $10$ definierte Zielanfahrten ohne Kollision; Zielradius dokumentiert; Fehlfahrten und Recovery-Verhalten nachvollziehbar protokolliert.                                 |
| F05 | Bedien- und Leitstandsebene als Betriebswerkzeug                | F   | M         | Telemetrie, Statusanzeige, manuelle Kommandos und Audio-Rueckmeldung sind verfuegbar; Zustaende sind ueber die Benutzeroberflaeche nachvollziehbar.                           |
| F06 | Freigabelogik mit sicheren Zustandsuebergaengen                   | F   | M         | Nicht freigegebene Kommandos werden blockiert; Stopp hat Vorrang; Kommandokette folgt dem Schema Interaktion $\rightarrow$ Freigabelogik $\rightarrow$ Missionskommando. |
| F07 | Sprachschnittstelle als anschlussfaehige Erweiterung             | F   | C         | Sprachbefehl wird in Intent und Missionskommando ueberfuehrt; direkte rohe Motoransteuerung aus Sprache ist ausgeschlossen.                                                |
| N01 | Deterministische Verarbeitung im Fahrkern                       | NF  | M         | Regelzyklus mit $50\,\mathrm{Hz}$; Jitter kleiner als $2\,\mathrm{ms}$; Sensorzugriffe blockieren die Motorregelung nicht dauerhaft.                                     |
| N02 | Modulare und wartbare Systemstruktur                            | NF  | S         | Funktionen sind in getrennten ROS-2-Knoten und Launch-Dateien organisiert; fachliche Ebenen bleiben entkoppelt.                                                          |
| N03 | Robuste Kommunikation und Fehlerbehandlung                      | NF  | M         | Kommunikationsausfall wird erkannt; System faellt in sicheren Zustand; Wiederanlauf der UART-basierten micro-ROS-Kette ist moeglich.                                       |
| N04 | Beobachtbarkeit und Nachvollziehbarkeit                         | NF  | S         | Zustaende, Sensordaten und Fehlerereignisse sind protokollierbar und ueber die Benutzeroberflaeche zugaenglich.                                                              |
| N05 | Erweiterbarkeit der Interaktionsschicht                         | NF  | S         | Audio- und Sprachfunktionen lassen sich ergaenzen, ohne Fahrkern oder Sicherheitslogik strukturell umzubauen.                                                             |

Die MoSCoW-Priorisierung folgt einer klaren Regel. Must-Anforderungen bilden die Kernvalidierung der Arbeit. Should-Anforderungen verbessern Wartbarkeit, Diagnose und spaetere Systemqualitaet. Could-Anforderungen markieren geplante Erweiterungen, insbesondere an der Interaktionsschicht. Damit entsteht eine Anforderungsbasis, die die Roadmap-Themen in eine projektarbeitstaugliche Form ueberfuehrt und zugleich die spaetere Validierung in Kapitel 6 vorbereitet. fileciteturn4file0turn4file1
