# 7. Fazit und Ausblick

## 7.1 Beantwortung der Leitfrage und der Projektfragen

Die Leitfrage dieser Arbeit lautet, ob sich ein kostenguenstiges autonomes mobiles Robotersystem so auslegen laesst, dass Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene im Innenraum reproduzierbar zusammenarbeiten. Die Ergebnisse aus Kapitel 6 beantworten diese Leitfrage im Kern positiv. Der Prototyp erreicht eine funktionsfaehige und sicher priorisierte Innenraum-Mobilitaet auf Basis einer verteilten Architektur aus zwei ESP32-S3-Mikrocontrollern und einem Raspberry Pi 5. Gleichzeitig zeigt die Validierung, dass nicht alle Akzeptanzkriterien in gleicher Tiefe nachgewiesen sind und dass erweiterte Funktionen nicht mit dem gleichen Reifegrad vorliegen wie der fahrkritische Kern.

Die Arbeit zielt damit nicht auf den vollstaendigen Nachweis industrieller Serienreife, sondern auf den belastbaren Nachweis einer tragfaehigen Systemarchitektur fuer einen kostenguenstigen Innenraum-AMR. Diese Einordnung entspricht auch der Roadmap: Zuerst muessen Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene belastbar arbeiten. Erst danach folgen Erweiterungen wie Vision oder Sprachschnittstelle.

### PF1 — Fahrkern und verteilte Echtzeitarchitektur

Die erste Projektfrage untersucht, ob sich ein Fahrkern auf Basis einer verteilten ESP32-S3-Architektur so realisieren laesst, dass Motorregelung, Odometrie und die Verarbeitung von Geschwindigkeitskommandos deterministisch arbeiten. Die Validierung zeigt fuer die PID-Regelschleife einen Regeltakt von $50\,\mathrm{Hz}$ bei einem Jitter von unter $2\,\mathrm{ms}$. Der Datenverlust der micro-ROS-Kommunikation blieb unter $0{,}1\,\%$. Diese Messwerte belegen, dass die Trennung von Drive-Knoten und Sensor-Knoten blockierende Peripheriezugriffe vom Fahrkern fernhaelt und damit die zentrale Architekturabsicht erfuellt.

PF1 ist damit positiv beantwortet. Eine verteilte Echtzeitarchitektur mit UART-basierter micro-ROS-Anbindung kann den Fahrkern fuer einen kostenguenstigen Innenraum-AMR deterministisch stabil betreiben, sofern die Aufgabenteilung zwischen Motorregelung und Sensorverarbeitung physisch getrennt bleibt.

### PF2 — Sensor- und Sicherheitsbasis sowie Lokalisierung und Kartierung

Die zweite Projektfrage untersucht, welchen Beitrag Odometrie-Kalibrierung, IMU-Integration, Kanten-Erkennung und LiDAR-basierte Kartierung zur belastbaren Zustands- und Umgebungsbasis leisten. Die Validierung zeigt drei zentrale Ergebnisse. Erstens reduzierte die UMBmark-Kalibrierung den systematischen Odometriefehler um den Faktor $10$ bis $20$. Zweitens sank der laterale Drift auf einer Referenzfahrt ueber $1{,}0\,\mathrm{m}$ mit IMU-Korrektur von $3{,}6\,\mathrm{cm}$ auf $2{,}1\,\mathrm{cm}$, waehrend der Gierfehler von $5{,}57^\circ$ auf $0{,}06^\circ$ sank. Drittens erreichte die Kartierung einen mittleren Absolute Trajectory Error von $0{,}16\,\mathrm{m}$ und blieb damit unter dem Akzeptanzkriterium von $0{,}20\,\mathrm{m}$. Zusaetzlich reagierte die Sicherheitskette bei einem Kantenereignis in unter $45\,\mathrm{ms}$.

PF2 ist damit weitgehend positiv beantwortet. Odometrie-Kalibrierung, IMU-Stuetzung, LiDAR-basierte Kartierung und priorisierte Sicherheitslogik bilden gemeinsam eine belastbare Grundlage fuer den Innenraumbetrieb. Die Einschraenkung liegt in der noch unvollstaendigen Einzelbewertung einzelner Sensorpfade wie Ultraschall, Batterieueberwachung und IMU-Plausibilisierung ueber alle Betriebszustaende.

### PF3 — Navigation sowie Bedien- und Leitstandsebene

Die dritte Projektfrage untersucht, ob sich auf dieser Basis eine Systemarchitektur aufbauen laesst, die Zielanfahrten, Recovery-Verhalten, Telemetrie, manuelle Eingriffe und Audio-Rueckmeldungen zusammenfuehrt, ohne die Freigabelogik zu unterlaufen. Die Validierung zeigt fuer die Navigation eine mittlere Positionsabweichung von $6{,}4\,\mathrm{cm}$ und eine mittlere Winkelabweichung von $4{,}2^\circ$. Der Nav2-Stack umfuhr statische Hindernisse mit einem minimalen Passierabstand von $12\,\mathrm{cm}$. Die Recovery-Verfahren loesten $80\,\%$ der Blockaden eigenstaendig. In einer gezielt erzeugten Konfliktsituation ueberstimmte die Sicherheitslogik die gueltige Bewegungsplanung, und das System kam $3\,\mathrm{cm}$ vor einer Absturzkante zum Stillstand. Diese Messwerte belegen, dass die Navigation funktional arbeitet und dass der sichere Zustand Vorrang vor dem zuletzt berechneten Bewegungsziel hat.

Fuer die Bedien- und Leitstandsebene liegt der Nachweis vor allem auf technischer Ebene vor. Telemetrie, Video und Diagnosefunktionen lassen sich betreiben, ohne den Fahrkern strukturell zu destabilisieren. Eine eigenstaendige Messreihe zur Bedienqualitaet, zur Verstaendlichkeit von Zustandsanzeigen oder zur Wirksamkeit von Audio-Rueckmeldungen wurde jedoch nicht durchgefuehrt. PF3 ist deshalb im Kern positiv, in Bezug auf die Benutzerqualitaet jedoch nur teilweise beantwortet. Die Freigabelogik ist architektonisch richtig eingeordnet, aber noch nicht ueber alle Kommandoklassen systematisch vermessen.

### Kernaussage der Arbeit

Die Arbeit zeigt, dass eine kostenguenstige AMR-Architektur fuer strukturierte Innenraeume technisch tragfaehig ist, wenn der Fahrkern deterministisch ausgelegt, die Sensor- und Sicherheitsbasis priorisiert behandelt und die Bedien- und Leitstandsebene klar von der fahrkritischen Kette getrennt wird. Der belastbare Erkenntnisgewinn liegt damit weniger in einer einzelnen Demonstrationsfunktion als in der hierarchischen Kopplung der Systemebenen.

## 7.2 Kritische Wuerdigung und Limitationen

### Vollstaendigkeit des Nachweises

Die Validierung bestaetigt den fahrkritischen Kern, aber nicht alle Anforderungen mit gleicher Tiefe. Fuer den Fahrkern fehlt noch eine vollstaendige Messreihe zu reproduzierbaren $360^\circ$-Rotationen und zum Nachlauf nach dem Stopp. In der Sensor- und Sicherheitsbasis ist die Kanten-Erkennung belastbar nachgewiesen, waehrend Ultraschall, Batterieueberwachung und IMU-Plausibilisierung noch nicht mit derselben systematischen Tiefe ausgewertet sind. Fuer die Bedien- und Leitstandsebene fehlt eine eigenstaendige Untersuchung der Bedienqualitaet. Die Sprachschnittstelle ist in der Roadmap als Erweiterung beschrieben, gehoert aber nicht zum validierten Kernumfang dieser Arbeit.

### Technische Grenzen des Prototyps

Die Kalibrierung reduziert systematische Odometriefehler deutlich, kompensiert aber keinen Schlupf auf wechselnden oder unebenen Untergruenden. Das Recovery-Verhalten erhoeht die Robustheit der Navigation, beseitigt jedoch nicht alle Blockadesituationen. Die Vision-Pipeline erreicht mit dem Hailo-8L eine mittlere Inferenzzeit von rund $34\,\mathrm{ms}$ pro Bild und ist damit technisch leistungsfaehig, bleibt jedoch ausserhalb des sicherheitskritischen Kerns. Das Docking erreichte eine Erfolgsquote von $80\,\%$ und zeigte damit technische Machbarkeit, aber noch keine hinreichende Robustheit fuer eine Kernfunktion. Beleuchtungsartefakte und unguenstige Ankunftsposen wirken sich weiterhin deutlich auf die monokulare Bildauswertung aus.

### Methodische Grenzen

Das Vorgehen nach VDI 2206 strukturiert die Entwicklung des mechatronischen Gesamtsystems klar. Fuer die Softwareentwicklung mit wiederholten Anpassungen an ROS-2-Konfiguration, Recovery-Verhalten und Knotenstruktur entsteht jedoch ein iterativer Arbeitsmodus, der im linearen Bild des V-Modells nur eingeschraenkt sichtbar wird. Die UMBmark-Kalibrierung fuehrte beispielsweise zu einer Korrektur der Kinematikparameter in der Drive-Firmware, was einem Iterationszyklus zwischen Eigenschaftsabsicherung und domaenenspezifischem Entwurf entspricht. Die Arbeit bestaetigt damit die Eignung des V-Modells als Ordnungsrahmen, nicht jedoch als vollstaendige Beschreibung realer Softwareiteration.

### Uebertragbarkeit und wirtschaftliche Einordnung

Die Ergebnisse gelten fuer strukturierte Innenraeume mit kontrollierbaren Randbedingungen. Eine direkte Uebertragung auf industrielle Daueranwendung, Mischverkehr mit Personen oder zertifizierungspflichtige Flurfoerderzeuge ist nicht zulaessig. Dafuer fehlen unter anderem redundante Sicherheitssensorik, formale Sicherheitsnachweise und eine robuste Hardwareintegration. Wirtschaftlich zeigt der Prototyp dennoch einen relevanten Punkt: Mit Consumer-Hardware und Open-Source-Software laesst sich ein funktional ueberzeugender Innenraum-AMR zu deutlich geringeren Kosten aufbauen als ein industrielles Serienprodukt. Die Differenz in Preis und Reifegrad markiert zugleich die Grenze zwischen Laborprototyp und industrieller Loesung.

## 7.3 Ausblick und Weiterentwicklung

### Kernpfad der Roadmap vervollstaendigen

Der naechste Entwicklungsschritt sollte nicht mit zusaetzlichen Demonstrationsfunktionen beginnen, sondern mit der vollstaendigen Schliessung des Kernpfads. Dazu gehoeren eine vollstaendige Messreihe fuer den Fahrkern, eine systematische Einzelbewertung von Ultraschall, Batterieueberwachung und IMU-Plausibilisierung sowie eine formale Pruefung aller relevanten Zustandsuebergaenge der Freigabelogik. Fuer die Navigation ist insbesondere das Recovery-Verhalten weiter zu verbessern, bis Fehlfahrten, Sackgassen und lokale Blockaden reproduzierbar beherrscht werden. Diese Reihenfolge entspricht der Roadmap-Logik, in der quantitative Stabilitaet vor zusaetzlicher Systemkomplexitaet steht.

### Bedien- und Leitstandsebene systematisch ausbauen

Die Bedien- und Leitstandsebene ist technisch vorhanden, sollte aber als Betriebswerkzeug systematischer bewertet werden. Dafuer sind Messgroessen fuer Telemetrie-Verzoegerung, Zustandstransparenz, Eingriffszeit, Audio-Rueckmeldungen und Fehlerdiagnose festzulegen. Ziel ist eine Benutzeroberflaeche, die nicht nur funktioniert, sondern Betriebszustaende eindeutig und belastbar vermittelt. Die Trennung zwischen Bedienung und Fahrlogik bleibt dabei unveraendert, weil genau diese Trennung die Stabilitaet des Gesamtsystems absichert.

### Sprachschnittstelle als sichere Erweiterung integrieren

Die Roadmap beschreibt die Sprachschnittstelle ausdruecklich als Erweiterung oberhalb des fahrkritischen Kerns. Diese Einordnung ist technisch zwingend. Sprachbefehle duerfen nicht direkt in rohe Geschwindigkeitsbefehle uebergehen, sondern muessen ueber Intent-Erkennung, Freigabelogik und Missionskommando auf Navigation, Leitstand oder Audio wirken. Fuer die naechste Ausbaustufe bietet sich daher eine Architektur mit ReSpeaker Mic Array v2.0, `voice_input_node`, `speech_to_text_node`, `voice_intent_node`, `voice_command_mux` und `text_to_speech_node` an. Der erste validierbare Funktionsumfang sollte auf einen kleinen Wortschatz mit priorisiertem „Stopp“, Moduswechseln und wenigen freigegebenen Missionskommandos begrenzt bleiben.

### Hardware- und Sicherheitsreife erhoehen

Fuer einen robusteren Dauerbetrieb sind eine eigene Leiterplatine, definierte Steckverbinder, verbesserte elektromagnetische Vertraeglichkeit und eine mechanisch stabilere Sensorintegration naheliegende naechste Schritte. Zusaetzlich sollte die Sicherheitskette um weitere Schutzpfade wie Bumper oder ueberwachte Not-Halt-Funktionen ergaenzt werden. Fuer jeden Schritt in Richtung realer Betriebsumgebung steigt die Bedeutung normativer Anforderungen, insbesondere im Hinblick auf CE-Konformitaet und auf sicherheitsgerichtete Sensorik.

## 7.4 Schluss

Die Arbeit liefert den Nachweis, dass ein kostenguenstiger Innenraum-AMR auf Basis einer verteilten Open-Source-Architektur technisch tragfaehig aufgebaut und in seinen Kernfunktionen experimentell belegt werden kann. Der Fahrkern arbeitet deterministisch, die Sensor- und Sicherheitsbasis priorisiert sichere Zustaende, Lokalisierung und Kartierung schaffen eine belastbare Umgebungsreferenz, und die Navigation erreicht eine praxistaugliche Zielanfahrt im Innenraum. Offene Punkte liegen vor allem in der vollstaendigen Abdeckung aller Akzeptanzkriterien und in der Robustheit erweiterter Interaktionsfunktionen. Genau daraus folgt der weitere Entwicklungsweg: zuerst den Kernpfad vollstaendig schliessen, danach multimodale Erweiterungen wie Vision und Sprachschnittstelle kontrolliert und freigabelogisch abgesichert integrieren.
