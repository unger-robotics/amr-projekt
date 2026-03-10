# 1. Einleitung

## 1.1 Ausgangssituation und Problemstellung

Die zentrale Leitfrage dieser Arbeit lautet: Wie laesst sich ein kostenguenstiges autonomes mobiles Robotersystem so auslegen, dass Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene reproduzierbar zusammenarbeiten?

Autonome Mobile Roboter (AMR) uebernehmen in der Intralogistik Transportaufgaben ohne fest installierte Leitlinien oder Reflektoren. Diese Eigenschaft ist insbesondere fuer den Transport von Kleinladungstraegern (KLT) in Umgebungen mit wechselnden Layouts relevant. In solchen Umgebungen stossen starre Foerdersysteme an Grenzen, weil sie Anpassungen an neue Materialfluesse, Arbeitsplaetze oder Montagestationen nur mit zusaetzlichem technischem und organisatorischem Aufwand zulassen.

Fuer kleine und mittlere Unternehmen entsteht daraus ein Zielkonflikt. Einerseits besteht Bedarf an flexiblen Transportsystemen. Andererseits liegen kommerzielle AMR-Plattformen haeufig deutlich ueber dem technisch und wirtschaftlich angemessenen Umfang einfacher KLT-Transportaufgaben. Open-Source-Komponenten und verfuegbare Einplatinenrechner senken zwar die Eintrittsschwelle, liefern aber noch keine belastbare Referenz dafuer, wie ein kostenguenstiges Gesamtsystem mit klarer Aufgabenverteilung, reproduzierbarer Navigation und nachvollziehbarer Sicherheitslogik aufgebaut werden kann.

Die technische Herausforderung liegt nicht in einem einzelnen Modul, sondern in der systematischen Kopplung mehrerer Ebenen. Der Fahrkern umfasst Antrieb, Odometrie und Grundbewegung. Die Sensor- und Sicherheitsbasis liefert IMU-, Batterie-, Ultraschall- und Kanteninformationen fuer den sicheren Betrieb. Lokalisierung und Kartierung erzeugen die raeumliche Grundlage fuer die Orientierung im Innenraum. Die Navigation plant und verfolgt Zielanfahrten. Die Bedien- und Leitstandsebene stellt Telemetrie, manuelle Eingriffe, Audio-Rueckmeldungen und Diagnosefunktionen bereit. Zusaetzlich muss die Architektur Erweiterungen wie eine Sprachschnittstelle so aufnehmen, dass keine direkte Umgehung der Sicherheitslogik entsteht.

Die vorliegende Arbeit adressiert diese Herausforderung durch den Entwurf und die Validierung eines verteilten AMR-Prototyps auf Basis von ROS 2 und micro-ROS. Zwei ESP32-S3-Mikrocontroller uebernehmen hardwarenahe Aufgaben im Fahrkern sowie in der Sensor- und Sicherheitsbasis. Ein Raspberry Pi 5 fuehrt Lokalisierung und Kartierung, Navigation sowie Funktionen der Bedien- und Leitstandsebene aus. Die Systemarchitektur trennt damit zeitkritische Regelungsaufgaben von rechenintensiven Host-Funktionen und schafft eine Grundlage fuer spaetere Erweiterungen wie visuelle Assistenz und Sprachschnittstelle.

---

## 1.2 Zielsetzung und Projektfragen

Das Ziel dieser Arbeit besteht darin, ein kostenguenstiges AMR-System fuer den KLT-Transport so zu entwickeln und experimentell zu validieren, dass die Kernfunktionen des Gesamtsystems aufeinander abgestimmt, sicher gekoppelt und reproduzierbar nachweisbar sind. Im Mittelpunkt stehen nicht einzelne Demonstrationsfunktionen, sondern das belastbare Zusammenwirken der Systemebenen.

Daraus ergeben sich drei Projektfragen.

* **PF1 — Echtzeitarchitektur:** Wie laesst sich eine echtzeitfaehige Antriebsregelung und Sensorerfassung auf einer Dual-Knoten-Architektur mit Mikrocontrollern realisieren?
  * *Einordnung:* Der Fahrkern bildet die Voraussetzung fuer jede weitere Systemfunktion. Instabile Regeltakte, Kommunikationsjitter oder konkurrierende Sensorzugriffe verschlechtern unmittelbar die Bewegungsqualitaet und damit alle nachgelagerten Funktionen.
* **PF2 — Navigationsgenauigkeit:** Welchen Einfluss haben systematische Odometrie-Kalibrierung, IMU-Fusion und hardwarenahe Sicherheitslogik auf die Navigationsgenauigkeit?
  * *Einordnung:* Navigation erfordert eine raeumlich konsistente Pose-Schaetzung. Gleichzeitig muss die Sicherheitslogik sicherheitsnahe Signale priorisieren und Bewegungen stoppen koennen, bevor unsichere Zustaende entstehen.
* **PF3 — Wahrnehmung und Docking:** Erreicht ein monokulares Kamerasystem in Kombination mit Edge-KI und Cloud-Semantik eine ausreichend praezise Umgebungswahrnehmung fuer komplexe Innenraeume und zentimetergenaues Docking?
  * *Einordnung:* Ein Missionskommando bezeichnet in dieser Arbeit ein freigegebenes Ziel- oder Moduskommando oberhalb roher Fahrbefehle. Die Freigabelogik entscheidet, welche Kommandos zulaessig sind, blockiert oder in sichere Systemreaktionen ueberfuehrt werden.

Die Arbeit konzentriert sich damit auf die Kernarchitektur eines AMR fuer Innenraeume. Erweiterungen wie visuelle Semantik, Docking-Hilfen oder eine Sprachschnittstelle mit ReSpeaker Mic Array v2.0 werden als anschlussfaehige Ausbaustufen der Bedien- und Leitstandsebene betrachtet, sind aber nicht der primaere Bewertungsmassstab der Kernvalidierung.

---

## 1.3 Vorgehensweise und methodischer Rahmen

Die Arbeit folgt einem mechatronischen Entwicklungsansatz nach VDI 2206 und ordnet die Umsetzung in aufeinander aufbauende Systemphasen. Diese Phasen reduzieren die Komplexitaet auf wenige Kerngroessen und schaffen fuer jede Ebene eigene Bewertungsmassstaebe.

1. **Fahrkern quantitativ absichern:** Zunaechst wird die Grundbewegung des Differentialantriebs ausgelegt, implementiert und ueber Regelguete, Geradeauslauf, Winkelfehler und Stoppverhalten bewertet.
2. **Sensor- und Sicherheitsbasis aufbauen:** Anschliessend werden IMU, Batterieueberwachung, Ultraschall und Kanten-Erkennung integriert. Ziel ist eine belastbare Signalkette fuer sicherheitsnahe und zustandsbezogene Informationen.
3. **Lokalisierung und Kartierung herstellen:** Danach werden Odometrie, TF-Struktur, LiDAR und SLAM so gekoppelt, dass wiederholbare Karten und eine konsistente Re-Lokalisierung im Innenraum entstehen.
4. **Navigation mit Missionslogik koppeln:** Auf Grundlage der Karte werden Zielanfahrten, Recovery-Verhalten und sichere Bewegungsfreigaben untersucht. Bewertet werden Zielerreichung, Fehlfahrten, Kollisionen und nachvollziehbare Systemreaktionen.
5. **Bedien- und Leitstandsebene integrieren:** Abschliessend werden Telemetrie, webbasierte Benutzeroberflaeche, manuelle Eingriffe und Audio-Rueckmeldungen als Betriebswerkzeug zusammengefuehrt.

Die methodische Umsetzung in den folgenden Kapiteln orientiert sich an dieser Struktur. Kapitel 2 erlaeutert die fachlichen Grundlagen. Kapitel 3 leitet Anforderungen und Randbedingungen ab. Kapitel 4 beschreibt das Systemkonzept. Kapitel 5 dokumentiert die Implementierung der Systemebenen. Kapitel 6 bewertet die Ergebnisse anhand messbarer Kriterien. Kapitel 7 verdichtet die Resultate, benennt Limitationen und leitet anschlussfaehige Erweiterungen wie Sprachschnittstelle und weiterfuehrende Multimodalitaet ab.
