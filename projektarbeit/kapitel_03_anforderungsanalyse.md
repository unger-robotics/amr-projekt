# 3. Anforderungsanalyse

## 3.1 Leitfrage, Einsatzszenario und Systemgrenze

Die Leitfrage dieses Kapitels lautet: Welche Anforderungen muss ein kostengünstiges autonomes mobiles Robotersystem erfüllen, damit Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene in einem Innenraum belastbar zusammenarbeiten?

Das Einsatzszenario dieser Arbeit ist der autonome Transport kleiner Nutzlasten zwischen definierten Zielpunkten in einem strukturierten Innenraum. Die Referenzumgebung entspricht einer wohnungs- oder laborähnlichen Fläche mit Engstellen, Möbeln, Wänden und wechselnden Hindernissen. Damit verlagert sich der Schwerpunkt gegenüber einem klassischen Industrie-Szenario: Nicht maximaler Materialdurchsatz, sondern reproduzierbare Navigation, sichere Bewegungsfreigabe und nachvollziehbare Systemreaktionen stehen im Vordergrund.

Der Anwendungsfall gliedert sich in fünf aufeinanderfolgende Schritte. Zunächst erzeugt das System eine Karte oder nutzt eine vorhandene Karte zur Re-Lokalisierung. Anschließend nimmt die Bedien- und Leitstandsebene ein Missionskommando entgegen, etwa eine Zielanfahrt zu einem definierten Punkt. Danach plant die Navigation einen globalen Pfad und übergibt Sollgrößen an den Fahrkern. Während der Fahrt überwacht die Sensor- und Sicherheitsbasis den Nahbereich, den Energiezustand und sicherheitsnahe Ereignisse. Nach Erreichen des Zielpunkts meldet die Benutzeroberfläche das Ergebnis und erlaubt einen Folgeauftrag oder einen sicheren Halt.

Für die Anforderungsableitung ist die Systemgrenze entscheidend. Bestandteil der Kernarchitektur sind Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation, Sicherheitslogik, Freigabelogik sowie die Bedien- und Leitstandsebene. Eine Sprachschnittstelle gehört zur geplanten Ausbauarchitektur. Sie darf nur freigegebene Missionskommandos erzeugen und keine rohe Motoransteuerung auslösen. Nicht Gegenstand der Kernvalidierung sind Außenbetrieb, Treppenfahrt, freies semantisches Weltmodell oder vollautomatisches Greifen.

---

## 3.2 Technische Randbedingungen und Restriktionen

### 3.2.1 Hardware- und Plattformrandbedingungen

Die Systemarchitektur folgt einer verteilten Aufteilung zwischen Host-Ebene und Mikrocontroller-Ebene. Der Raspberry Pi 5 übernimmt hostseitige Funktionen wie Lokalisierung und Kartierung, Navigation, Benutzeroberfläche, Telemetrie, Audio-Rückmeldung und spätere Sprachverarbeitung. Zwei XIAO-ESP32-S3-Mikrocontroller übernehmen hardwarenahe Aufgaben. Der Drive-Knoten bildet den Fahrkern mit Motoransteuerung, Encoder-Auswertung und Odometrie. Der Sensor-Knoten bildet die Sensor- und Sicherheitsbasis mit IMU, Ultraschall, Kanten-Erkennung und Batterieüberwachung. Diese Rollenverteilung entspricht der Roadmap-Terminologie und trennt zeitkritische Regelung von blockierenden Sensorzugriffen. fileciteturn4file0

Als Sensorik dienen ein LiDAR für die 2D-Umgebungserfassung, eine inertiale Messeinheit für Drehraten- und Beschleunigungsdaten, ein Ultraschallsensor für den Nahbereich, ein Cliff-Sensor für Kanten und eine Batterieüberwachung für den Energiezustand. Die Referenz-Roadmap ordnet diese Komponenten explizit den Phasen Fahrkern, Sensor- und Sicherheitsbasis sowie Lokalisierung und Kartierung zu. fileciteturn4file5turn4file14

### 3.2.2 Software- und Kommunikationsrandbedingungen

Die Host-Software basiert auf ROS 2 Humble. Da das Zielsystem Debian Trixie nutzt, läuft der ROS-2-Stack in einer Container-Umgebung. Die Mikrocontroller werden über micro-ROS als ROS-2-Teilnehmer eingebunden. Für die Kommunikation zwischen Host und Mikrocontrollern kommt eine serielle UART-Verbindung über USB-CDC zum Einsatz. Die Anforderung folgt nicht aus Bequemlichkeit, sondern aus dem Bedarf an reproduzierbaren Laufzeiten. Eine drahtlose Verbindung würde die zeitliche Streuung der Kommandokette erhöhen und die Bewertung des Fahrkerns erschweren. Die bisherige Fassung von Kapitel 3 setzt für den Regelkreis einen Arbeitstakt von $50\,\mathrm{Hz}$ an. fileciteturn4file3turn4file1

Die Softwarearchitektur trennt Interaktion, Freigabelogik, Missionskommando, Navigation und Fahrkern. Daraus folgt eine verbindliche Befehlskette:

$$
\text{Interaktion} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation} \rightarrow \text{Fahrkern}
$$

Jede Anforderung, die Kommandos erzeugt oder verarbeitet, muss diese Kette einhalten.

### 3.2.3 Umgebungs- und Sicherheitsrandbedingungen

Die Arbeit betrachtet einen ebenen Innenraum mit bekannten oder kartierbaren Strukturen. Zulässig sind Wände, Möbel, Türen, Engstellen und bewegliche Hindernisse wie Personen. Nicht zulässig sind Außenflächen, nasse Untergründe, starke Steigungen oder ungesicherte Treppenfahrten. Eine erkannte Kante ist kein zu passierendes Hindernis, sondern ein Abbruchkriterium für die Bewegung.

Die Zielgeschwindigkeit beträgt $0{,}4\,\mathrm{m/s}$. Dieser Wert begrenzt die maximale Dynamik und reduziert zugleich die Anforderungen an Sensorreichweite, Bremsweg und Kollisionsvermeidung. Für Zielanfahrten gelten als Orientierungswerte eine laterale Zielabweichung von höchstens $0{,}10\,\mathrm{m}$ und ein Orientierungsfehler von höchstens $8^\circ$. Diese Größen dienen im weiteren Verlauf als Referenz für funktionale Anforderungen und Akzeptanzkriterien. fileciteturn4file1turn4file6

---

## 3.3 Funktionale Anforderungen

### F01 — Fahrkern mit reproduzierbarer Grundbewegung

Der Fahrkern muss lineare und rotatorische Bewegung reproduzierbar ausführen. Dazu gehören Motoransteuerung, Encoder-Auswertung, Odometrie und die Umsetzung von Geschwindigkeitskommandos. Der Fahrkern muss eine Geradeausfahrt über $1\,\mathrm{m}$ mit kleinem Seitenfehler, eine Rotation um $360^\circ$ mit reproduzierbarem Winkelfehler und einen sicheren Stopp ohne ungewolltes Nachlaufen unterstützen. Diese Forderung leitet sich direkt aus Phase 1 der Roadmap ab. fileciteturn4file5

### F02 — Sensor- und Sicherheitsbasis mit priorisierten Schutzfunktionen

Die Sensor- und Sicherheitsbasis muss IMU-Daten, Nahbereichsdaten, Batteriedaten und Kanteninformationen in definierter Form bereitstellen. Sicherheitsnahe Signale müssen gegenüber Komfort- oder Diagnosefunktionen priorisiert werden. Eine erkannte Kante muss die Bewegungsfreigabe sperren und einen sicheren Halt auslösen. Die Batterieüberwachung muss einen kritischen Energiezustand melden, bevor die Fahrfunktion unkontrolliert ausfällt. Diese Forderung leitet sich aus Phase 2 der Roadmap ab. fileciteturn4file14

### F03 — Lokalisierung und Kartierung für den Innenraum

Das System muss aus LiDAR-Daten, Odometrie und Transformationsbeziehungen eine konsistente Karte erzeugen und sich nach einem Neustart in dieser Karte wieder lokalisieren können. Der TF-Baum muss widerspruchsfrei bleiben. Die Kartenauflösung beträgt als Zielwert $5\,\mathrm{cm}$. Wiederholte Kartierungen desselben Raums dürfen keine ausgeprägten Doppelkonturen erzeugen. Diese Forderung leitet sich aus Phase 3 der Roadmap ab. fileciteturn4file14

### F04 — Navigation mit Missionslogik und Recovery-Verhalten

Die Navigation muss definierte Zielpunkte sicher anfahren. Dazu gehören globale Pfadplanung, lokale Bahnverfolgung, Hindernisberücksichtigung und nachvollziehbares Recovery-Verhalten. Die Navigation darf nur freigegebene Missionskommandos ausführen. Einzelne Benutzereingaben oder experimentelle Zusatzmodule dürfen keine direkte Umgehung der Sicherheitslogik erzeugen. Für die Kernvalidierung gilt als Zielwert die erfolgreiche Durchführung von $10$ definierten Zielanfahrten ohne Kollision. Diese Forderung leitet sich aus Phase 4 der Roadmap ab. fileciteturn4file14

### F05 — Bedien- und Leitstandsebene als Betriebswerkzeug

Die Bedien- und Leitstandsebene muss Zustände sichtbar machen und definierte Eingriffe erlauben. Dazu gehören Telemetrie, Statusanzeigen, Kamerabild oder Videostream, manuelle Kommandos in freigegebenen Betriebsarten und Audio-Rückmeldungen. Die Benutzeroberfläche dient nicht nur der Bedienung, sondern auch der Diagnose und Versuchsdokumentation. Die vorhandenen Schnittstellen `/cmd_vel`, `/servo_cmd`, `/hardware_cmd` und `/audio/play` bilden dafür die technische Grundlage. Diese Forderung leitet sich aus Ebene B und Phase 5 der Roadmap ab. fileciteturn4file0turn4file14

### F06 — Freigabelogik mit sicheren Zustandsübergängen

Die Freigabelogik muss festlegen, welche Kommandos im jeweiligen Betriebszustand zulässig sind. Sie muss Kommandos freigeben, blockieren oder in sichere Reaktionen umsetzen. Ein Stopp-Kommando hat Vorrang vor allen Fahr- und Missionskommandos. Bedienkommandos dürfen Navigation und Fahrkern beeinflussen, aber nicht die Schutzmechanismen umgehen. Diese Forderung ergibt sich aus der Terminologie-Norm der Roadmap mit den Begriffen Sicherheitslogik, Freigabelogik und Missionskommando. fileciteturn4file0

### F07 — Sprachschnittstelle als anschlussfähige Erweiterung

Die Sprachschnittstelle soll Sprachsignale in definierte Intents überführen und daraus freigegebene Missionskommandos ableiten. Die Sprachschnittstelle darf keine rohen Geschwindigkeitsbefehle direkt an den Fahrkern senden. Sichere Sofortkommandos wie „Stopp“ dürfen ausschließlich einen sicheren Halt anfordern. Diese Forderung gehört nicht zur Kernvalidierung, aber zur thematischen Erweiterung der Projektarbeit. Die Roadmap ordnet das ReSpeaker Mic Array v2.0, Sprach-zu-Text-Verarbeitung, Intent-Erkennung und Text-zu-Sprache der Ebene der intelligenten Interaktion zu. fileciteturn4file0

---

## 3.4 Nichtfunktionale Anforderungen

### N01 — Deterministische Verarbeitung im Fahrkern

Der Fahrkern muss Sollwerte und Messwerte mit hinreichend konstanter Zykluszeit verarbeiten. Für die Motorregelung gilt ein Arbeitstakt von $50\,\mathrm{Hz}$. Die zeitliche Streuung darf den Regelkreis nicht instabil machen. Blockierende I2C-Zugriffe oder nicht deterministische Nebenaufgaben dürfen den Fahrkern nicht unterbrechen. Die bisherige Ausgangsfassung fordert hierfür einen Jitter von weniger als $2\,\mathrm{ms}$. fileciteturn4file11

### N02 — Modulare und wartbare Systemstruktur

Die Architektur muss Funktionen in getrennten ROS-2-Knoten, Topics und Launch-Dateien abbilden. Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene müssen fachlich getrennt bleiben. Diese Modularität erleichtert Fehlersuche, Erweiterung und Wiederverwendung.

### N03 — Robuste Kommunikation und Fehlerbehandlung

Die serielle micro-ROS-Kommunikation muss Verbindungsabbrüche erkennen und einen definierten Wiederanlauf unterstützen. Kommunikationsfehler dürfen nicht zu unkontrollierter Weiterfahrt führen. Stattdessen muss das System in einen sicheren Zustand wechseln oder auf einen sicheren Halt zurückfallen. Die Ausgangsfassung von Kapitel 3 nennt den automatischen Wiederanlauf der UART-Kommunikation ausdrücklich als nichtfunktionale Anforderung. fileciteturn4file11

### N04 — Beobachtbarkeit und Nachvollziehbarkeit

Zustände, Sensordaten, Betriebsarten und Fehlerereignisse müssen so bereitgestellt werden, dass Versuche reproduzierbar ausgewertet werden können. Dazu gehören Telemetrie, Protokollierung und eine klar strukturierte Benutzeroberfläche. Eine Bewertung ohne sichtbare Mess- und Zustandsbasis ist nicht belastbar.

### N05 — Erweiterbarkeit der Interaktionsschicht

Die Architektur muss spätere Erweiterungen wie Sprachschnittstelle, Audio-Rückmeldung oder zusätzliche semantische Module aufnehmen können, ohne die Kernlogik des Fahrkerns zu verändern. Erweiterbarkeit bedeutet in diesem Kontext nicht beliebige Offenheit, sondern kontrollierte Kopplung über Freigabelogik und Missionskommandos.

---

## 3.5 Priorisierte Anforderungsliste nach MoSCoW

| ID  | Anforderung                                                     | Typ | Priorität | Akzeptanzkriterium                                                                                                                                                       |
|-----|-----------------------------------------------------------------|-----|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| F01 | Fahrkern mit reproduzierbarer Grundbewegung                     | F   | M         | Geradeausfahrt über $1\,\mathrm{m}$ reproduzierbar; Rotation um $360^\circ$ reproduzierbar; kein ungewolltes Nachlaufen nach Stopp.                                      |
| F02 | Sensor- und Sicherheitsbasis mit priorisierten Schutzfunktionen | F   | M         | IMU, Ultraschall, Kanten-Erkennung und Batterieüberwachung liefern nutzbare Signale; erkannte Kante führt reproduzierbar zum sicheren Halt.                              |
| F03 | Lokalisierung und Kartierung für den Innenraum                  | F   | M         | Karte mit Zielauflösung von $5\,\mathrm{cm}$ erzeugbar; Re-Lokalisierung nach Neustart möglich; keine ausgeprägten Doppelkonturen.                                       |
| F04 | Navigation mit Missionslogik und Recovery-Verhalten             | F   | M         | $10$ definierte Zielanfahrten ohne Kollision; Zielradius dokumentiert; Fehlfahrten und Recovery-Verhalten nachvollziehbar protokolliert.                                 |
| F05 | Bedien- und Leitstandsebene als Betriebswerkzeug                | F   | M         | Telemetrie, Statusanzeige, manuelle Kommandos und Audio-Rückmeldung sind verfügbar; Zustände sind über die Benutzeroberfläche nachvollziehbar.                           |
| F06 | Freigabelogik mit sicheren Zustandsübergängen                   | F   | M         | Nicht freigegebene Kommandos werden blockiert; Stopp hat Vorrang; Kommandokette folgt dem Schema Interaktion $\rightarrow$ Freigabelogik $\rightarrow$ Missionskommando. |
| F07 | Sprachschnittstelle als anschlussfähige Erweiterung             | F   | C         | Sprachbefehl wird in Intent und Missionskommando überführt; direkte rohe Motoransteuerung aus Sprache ist ausgeschlossen.                                                |
| N01 | Deterministische Verarbeitung im Fahrkern                       | NF  | M         | Regelzyklus mit $50\,\mathrm{Hz}$; Jitter kleiner als $2\,\mathrm{ms}$; Sensorzugriffe blockieren die Motorregelung nicht dauerhaft.                                     |
| N02 | Modulare und wartbare Systemstruktur                            | NF  | S         | Funktionen sind in getrennten ROS-2-Knoten und Launch-Dateien organisiert; fachliche Ebenen bleiben entkoppelt.                                                          |
| N03 | Robuste Kommunikation und Fehlerbehandlung                      | NF  | M         | Kommunikationsausfall wird erkannt; System fällt in sicheren Zustand; Wiederanlauf der UART-basierten micro-ROS-Kette ist möglich.                                       |
| N04 | Beobachtbarkeit und Nachvollziehbarkeit                         | NF  | S         | Zustände, Sensordaten und Fehlerereignisse sind protokollierbar und über die Benutzeroberfläche zugänglich.                                                              |
| N05 | Erweiterbarkeit der Interaktionsschicht                         | NF  | S         | Audio- und Sprachfunktionen lassen sich ergänzen, ohne Fahrkern oder Sicherheitslogik strukturell umzubauen.                                                             |

Die MoSCoW-Priorisierung folgt einer klaren Regel. Must-Anforderungen bilden die Kernvalidierung der Arbeit. Should-Anforderungen verbessern Wartbarkeit, Diagnose und spätere Systemqualität. Could-Anforderungen markieren geplante Erweiterungen, insbesondere an der Interaktionsschicht. Damit entsteht eine Anforderungsbasis, die die Roadmap-Themen in eine projektarbeitstaugliche Form überführt und zugleich die spätere Validierung in Kapitel 6 vorbereitet. fileciteturn4file0turn4file1
