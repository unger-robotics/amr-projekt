# 7. Fazit und Ausblick

## 7.1 Beantwortung der Leitfrage und der Projektfragen

Die Leitfrage dieser Arbeit lautet, ob sich ein kostenguenstiges autonomes mobiles Robotersystem so auslegen laesst, dass Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene im Innenraum reproduzierbar zusammenarbeiten. Die Ergebnisse aus Kapitel 6 beantworten diese Leitfrage im Kern positiv. Der Prototyp erreicht eine funktionsfaehige und sicher priorisierte Innenraum-Mobilitaet auf Basis einer verteilten Architektur aus zwei ESP32-S3-Mikrocontrollern und einem Raspberry Pi 5. Gleichzeitig zeigt die Validierung, dass nicht alle Akzeptanzkriterien in gleicher Tiefe nachgewiesen sind und dass erweiterte Funktionen nicht mit dem gleichen Reifegrad vorliegen wie der fahrkritische Kern.

Die Arbeit zielt damit nicht auf den vollstaendigen Nachweis industrieller Serienreife, sondern auf den belastbaren Nachweis einer tragfaehigen Systemarchitektur fuer einen kostenguenstigen Innenraum-AMR. Diese Einordnung entspricht auch der Roadmap: Zuerst muessen Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene belastbar arbeiten. Erst danach folgen Erweiterungen wie Vision oder Sprachschnittstelle.

### PF1 — Fahrkern und verteilte Echtzeitarchitektur

Die erste Projektfrage untersucht, ob sich ein Fahrkern auf Basis einer verteilten ESP32-S3-Architektur so realisieren laesst, dass Motorregelung, Odometrie und die Verarbeitung von Geschwindigkeitskommandos deterministisch arbeiten. Die Validierung zeigt fuer die PID-Regelschleife einen Regeltakt von $50\,\mathrm{Hz}$ bei einem Jitter von unter $2\,\mathrm{ms}$. Der Datenverlust der micro-ROS-Kommunikation blieb unter $0{,}1\,\%$. Diese Messwerte belegen, dass die Trennung von Drive-Knoten und Sensor-Knoten blockierende Peripheriezugriffe vom Fahrkern fernhaelt und damit die zentrale Architekturabsicht erfuellt.

PF1 ist damit positiv beantwortet. Eine verteilte Echtzeitarchitektur mit UART-basierter micro-ROS-Anbindung kann den Fahrkern fuer einen kostenguenstigen Innenraum-AMR deterministisch stabil betreiben, sofern die Aufgabenteilung zwischen Motorregelung und Sensorverarbeitung physisch getrennt bleibt.

### PF2 — Sensor- und Sicherheitsbasis sowie Lokalisierung und Kartierung

Die zweite Projektfrage untersucht, welchen Beitrag Odometrie-Kalibrierung, IMU-Integration, Kanten-Erkennung und LiDAR-basierte Kartierung zur belastbaren Zustands- und Umgebungsbasis leisten. Die Validierung zeigt drei zentrale Ergebnisse. Erstens reduzierte die UMBmark-Kalibrierung den systematischen Odometriefehler um den Faktor $10$ bis $20$. Zweitens sank der laterale Drift auf einer Referenzfahrt ueber $1{,}0\,\mathrm{m}$ mit IMU-Korrektur von $3{,}6\,\mathrm{cm}$ auf $2{,}1\,\mathrm{cm}$, waehrend der Gierfehler von $5{,}57^\circ$ auf $0{,}06^\circ$ sank. Drittens erreichte die Kartierung in T3.1 einen ATE (RMSE) von $0{,}190\,\mathrm{m}$ und einen ATE (MAE) von $0{,}161\,\mathrm{m}$; in T3.2 sank der ATE (RMSE) auf $0{,}030\,\mathrm{m}$. Beide Testfaelle blieben damit unter dem Akzeptanzkriterium von $0{,}20\,\mathrm{m}$. Zusaetzlich reagierte die Sicherheitskette bei einem Kantenereignis in $2{,}0\,\mathrm{ms}$ End-to-End-Latenz und unterschritt damit das Akzeptanzkriterium von $50\,\mathrm{ms}$ um mehr als eine Groessenordnung.

PF2 ist damit positiv beantwortet. Odometrie-Kalibrierung, IMU-Stuetzung, LiDAR-basierte Kartierung und priorisierte Sicherheitslogik bilden gemeinsam eine belastbare Grundlage fuer den Innenraumbetrieb. Die Einzelbewertung aller Sensorgruppen ist mit $11/11$ bestandenen Testfaellen vollstaendig abgeschlossen.

### PF3 — Navigation und Bedien- und Leitstandsebene

Die dritte Projektfrage untersucht, ob sich auf dieser Basis eine Systemarchitektur aufbauen laesst, die Zielanfahrten, Recovery-Verhalten, Telemetrie, manuelle Eingriffe und Audio-Rueckmeldungen zusammenfuehrt, ohne die Freigabelogik zu unterlaufen. Die Validierung zeigt fuer die Navigation eine mittlere Positionsabweichung von $1{,}01\,\mathrm{cm}$ und eine mittlere Winkelabweichung von $1{,}94^\circ$ (Messprotokoll Phase 4, T4.1). Der Nav2-Stack umfuhr statische Hindernisse mit einem minimalen Passierabstand von $12\,\mathrm{cm}$. Die Recovery-Verfahren loesten $80\,\%$ der Blockaden eigenstaendig. In einer gezielt erzeugten Konfliktsituation ueberstimmte die Sicherheitslogik die gueltige Bewegungsplanung, und das System kam $3\,\mathrm{cm}$ vor einer Absturzkante zum Stillstand. Diese Messwerte belegen, dass die Navigation funktional arbeitet und dass der sichere Zustand Vorrang vor dem zuletzt berechneten Bewegungsziel hat.

Fuer die Bedien- und Leitstandsebene belegen die Testfaelle T5.1-T5.5 (Messprotokoll Phase 5) die cmd\_vel-Latenz, Telemetrie-Vollstaendigkeit, Deadman-Timer, Audio-Feedback und Notaus. Alle fuenf Testfaelle wurden bestanden. PF3 ist damit positiv beantwortet. Die Freigabelogik ist architektonisch richtig eingeordnet, aber noch nicht ueber alle Kommandoklassen systematisch vermessen.

### Kernaussage der Arbeit

Die Arbeit zeigt, dass eine kostenguenstige AMR-Architektur fuer strukturierte Innenraeume technisch tragfaehig ist, wenn der Fahrkern deterministisch ausgelegt, die Sensor- und Sicherheitsbasis priorisiert behandelt und die Bedien- und Leitstandsebene klar von der fahrkritischen Kette getrennt wird. Der belastbare Erkenntnisgewinn liegt damit weniger in einer einzelnen Demonstrationsfunktion als in der hierarchischen Kopplung der Systemebenen.

## 7.2 Kritische Wuerdigung und Limitationen

### Vollstaendigkeit des Nachweises

Die Validierung bestaetigt den fahrkritischen Kern, aber nicht alle Anforderungen mit gleicher Tiefe. Fuer den Fahrkern wurde die $360^\circ$-Rotation mit einem Ergebnis von $358{,}1^\circ$ (Restfehler $1{,}88^\circ$) erfolgreich validiert. Eine systematische Vermessung des Nachlaufs nach dem Stopp steht hingegen noch aus. In der Sensor- und Sicherheitsbasis sind alle $11/11$ Sensorik-Testfaelle bestanden, einschliesslich Ultraschall, Cliff-Sensor, IMU-Drift, IMU-Bias und Rotationsgenauigkeit. Die Bedien- und Leitstandsebene ist mit fuenf bestandenen Testfaellen (T5.1-T5.5) funktional validiert; eine vertiefte Untersuchung der Bedienqualitaet im Sinne einer Usability-Studie steht noch aus. Die Sprachschnittstelle ist in der Roadmap als Erweiterung beschrieben, gehoert aber nicht zum validierten Kernumfang dieser Arbeit.

### Technische Grenzen des Prototyps

Die Kalibrierung reduziert systematische Odometriefehler deutlich, kompensiert aber keinen Schlupf auf wechselnden oder unebenen Untergruenden. Das Recovery-Verhalten erhoeht die Robustheit der Navigation, beseitigt jedoch nicht alle Blockadesituationen. Die Vision-Pipeline erreicht mit dem Hailo-8L eine mittlere Inferenzzeit von rund $34\,\mathrm{ms}$ pro Bild und ist damit technisch leistungsfaehig, bleibt jedoch ausserhalb des sicherheitskritischen Kerns. Das Docking erreichte nach Optimierung der Dreifach-Bedingung eine Erfolgsquote von $100\,\%$ ($10/10$) und zeigte damit technische Machbarkeit als Erweiterungsfunktion. Beleuchtungsartefakte und unguenstige Ankunftsposen wirken sich weiterhin deutlich auf die monokulare Bildauswertung aus.

### Methodische Grenzen

Das Vorgehen nach VDI 2206 strukturiert die Entwicklung des mechatronischen Gesamtsystems klar. Fuer die Softwareentwicklung mit wiederholten Anpassungen an ROS-2-Konfiguration, Recovery-Verhalten und Knotenstruktur entsteht jedoch ein iterativer Arbeitsmodus, der im linearen Bild des V-Modells nur eingeschraenkt sichtbar wird. Die UMBmark-Kalibrierung fuehrte beispielsweise zu einer Korrektur der Kinematikparameter in der Drive-Firmware, was einem Iterationszyklus zwischen Eigenschaftsabsicherung und domaenenspezifischem Entwurf entspricht. Die Arbeit bestaetigt damit die Eignung des V-Modells als Ordnungsrahmen, nicht jedoch als vollstaendige Beschreibung realer Softwareiteration.

### Uebertragbarkeit und wirtschaftliche Einordnung

Die Ergebnisse gelten fuer strukturierte Innenraeume mit kontrollierbaren Randbedingungen. Eine direkte Uebertragung auf industrielle Daueranwendung, Mischverkehr mit Personen oder zertifizierungspflichtige Flurfoerderzeuge ist nicht zulaessig. Dafuer fehlen unter anderem redundante Sicherheitssensorik, formale Sicherheitsnachweise und eine robuste Hardwareintegration. Wirtschaftlich zeigt der Prototyp dennoch einen relevanten Punkt: Mit Consumer-Hardware und Open-Source-Software laesst sich ein funktional ueberzeugender Innenraum-AMR zu deutlich geringeren Kosten aufbauen als ein industrielles Serienprodukt. Die Differenz in Preis und Reifegrad markiert zugleich die Grenze zwischen Laborprototyp und industrieller Loesung.

## 7.3 Ausblick und Weiterentwicklung

### Kernpfad der Roadmap vervollstaendigen

Der naechste Entwicklungsschritt sollte nicht mit zusaetzlichen Demonstrationsfunktionen beginnen, sondern mit der vollstaendigen Schliessung des Kernpfads. Dazu gehoeren eine systematische Vermessung des Nachlaufverhaltens im Fahrkern sowie eine formale Pruefung aller relevanten Zustandsuebergaenge der Freigabelogik. Fuer die Navigation ist insbesondere das Recovery-Verhalten weiter zu verbessern, bis Fehlfahrten, Sackgassen und lokale Blockaden reproduzierbar beherrscht werden. Diese Reihenfolge entspricht der Roadmap-Logik, in der quantitative Stabilitaet vor zusaetzlicher Systemkomplexitaet steht.

### Bedien- und Leitstandsebene systematisch ausbauen

Die Bedien- und Leitstandsebene ist technisch vorhanden, sollte aber als Betriebswerkzeug systematischer bewertet werden. Dafuer sind Messgroessen fuer Telemetrie-Verzoegerung, Zustandstransparenz, Eingriffszeit, Audio-Rueckmeldungen und Fehlerdiagnose festzulegen. Ziel ist eine Benutzeroberflaeche, die nicht nur funktioniert, sondern Betriebszustaende eindeutig und belastbar vermittelt. Die Trennung zwischen Bedienung und Fahrlogik bleibt dabei unveraendert, weil genau diese Trennung die Stabilitaet des Gesamtsystems absichert.

### Sprachschnittstelle als sichere Erweiterung integrieren

Die Roadmap beschreibt die Sprachschnittstelle ausdruecklich als Erweiterung oberhalb des fahrkritischen Kerns. Diese Einordnung ist technisch zwingend. Sprachbefehle duerfen nicht direkt in rohe Geschwindigkeitsbefehle uebergehen, sondern muessen ueber Intent-Erkennung, Freigabelogik und Missionskommando auf Navigation, Leitstand oder Audio wirken. Fuer die naechste Ausbaustufe bietet sich daher eine Architektur mit ReSpeaker Mic Array v2.0, `voice_input_node`, `speech_to_text_node`, `voice_intent_node`, `voice_command_mux` und `text_to_speech_node` an. Der erste validierbare Funktionsumfang sollte auf einen kleinen Wortschatz mit priorisiertem „Stopp“, Moduswechseln und wenigen freigegebenen Missionskommandos begrenzt bleiben.

### Hardware- und Sicherheitsreife erhoehen

Fuer einen robusteren Dauerbetrieb sind eine eigene Leiterplatine, definierte Steckverbinder, verbesserte elektromagnetische Vertraeglichkeit und eine mechanisch stabilere Sensorintegration naheliegende naechste Schritte. Zusaetzlich sollte die Sicherheitskette um weitere Schutzpfade wie Bumper oder ueberwachte Not-Halt-Funktionen ergaenzt werden. Fuer jeden Schritt in Richtung realer Betriebsumgebung steigt die Bedeutung normativer Anforderungen, insbesondere im Hinblick auf CE-Konformitaet und auf sicherheitsgerichtete Sensorik.

## 7.4 Schluss

Die Arbeit liefert den Nachweis, dass ein kostenguenstiger Innenraum-AMR auf Basis einer verteilten Open-Source-Architektur technisch tragfaehig aufgebaut und in seinen Kernfunktionen experimentell belegt werden kann. Der Fahrkern arbeitet deterministisch, die Sensor- und Sicherheitsbasis priorisiert sichere Zustaende, Lokalisierung und Kartierung schaffen eine belastbare Umgebungsreferenz, und die Navigation erreicht eine praxistaugliche Zielanfahrt im Innenraum. Offene Punkte liegen vor allem in der vollstaendigen Abdeckung aller Akzeptanzkriterien und in der Robustheit erweiterter Interaktionsfunktionen. Genau daraus folgt der weitere Entwicklungsweg: zuerst den Kernpfad vollstaendig schliessen, danach multimodale Erweiterungen wie Vision und Sprachschnittstelle kontrolliert und freigabelogisch abgesichert integrieren.
