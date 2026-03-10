# 1. Einleitung

## 1.1 Ausgangssituation und Problemstellung

Die zentrale Leitfrage dieser Arbeit lautet: Wie lässt sich ein kostengünstiges autonomes mobiles Robotersystem so auslegen, dass Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene reproduzierbar zusammenarbeiten?

Autonome Mobile Roboter (AMR) übernehmen in der Intralogistik Transportaufgaben ohne fest installierte Leitlinien oder Reflektoren. Diese Eigenschaft ist insbesondere für den Transport von Kleinladungsträgern (KLT) in Umgebungen mit wechselnden Layouts relevant. In solchen Umgebungen stoßen starre Fördersysteme an Grenzen, weil sie Anpassungen an neue Materialflüsse, Arbeitsplätze oder Montagestationen nur mit zusätzlichem technischem und organisatorischem Aufwand zulassen.

Für kleine und mittlere Unternehmen entsteht daraus ein Zielkonflikt. Einerseits besteht Bedarf an flexiblen Transportsystemen. Andererseits liegen kommerzielle AMR-Plattformen häufig deutlich über dem technisch und wirtschaftlich angemessenen Umfang einfacher KLT-Transportaufgaben. Open-Source-Komponenten und verfügbare Einplatinenrechner senken zwar die Eintrittsschwelle, liefern aber noch keine belastbare Referenz dafür, wie ein kostengünstiges Gesamtsystem mit klarer Aufgabenverteilung, reproduzierbarer Navigation und nachvollziehbarer Sicherheitslogik aufgebaut werden kann.

Die technische Herausforderung liegt nicht in einem einzelnen Modul, sondern in der systematischen Kopplung mehrerer Ebenen. Der Fahrkern umfasst Antrieb, Odometrie und Grundbewegung. Die Sensor- und Sicherheitsbasis liefert IMU-, Batterie-, Ultraschall- und Kanteninformationen für den sicheren Betrieb. Lokalisierung und Kartierung erzeugen die räumliche Grundlage für die Orientierung im Innenraum. Die Navigation plant und verfolgt Zielanfahrten. Die Bedien- und Leitstandsebene stellt Telemetrie, manuelle Eingriffe, Audio-Rückmeldungen und Diagnosefunktionen bereit. Zusätzlich muss die Architektur Erweiterungen wie eine Sprachschnittstelle so aufnehmen, dass keine direkte Umgehung der Sicherheitslogik entsteht.

Die vorliegende Arbeit adressiert diese Herausforderung durch den Entwurf und die Validierung eines verteilten AMR-Prototyps auf Basis von ROS 2 und micro-ROS. Zwei ESP32-S3-Mikrocontroller übernehmen hardwarenahe Aufgaben im Fahrkern sowie in der Sensor- und Sicherheitsbasis. Ein Raspberry Pi 5 führt Lokalisierung und Kartierung, Navigation sowie Funktionen der Bedien- und Leitstandsebene aus. Die Systemarchitektur trennt damit zeitkritische Regelungsaufgaben von rechenintensiven Host-Funktionen und schafft eine Grundlage für spätere Erweiterungen wie visuelle Assistenz und Sprachschnittstelle.

---

## 1.2 Zielsetzung und Projektfragen

Das Ziel dieser Arbeit besteht darin, ein kostengünstiges AMR-System für den KLT-Transport so zu entwickeln und experimentell zu validieren, dass die Kernfunktionen des Gesamtsystems aufeinander abgestimmt, sicher gekoppelt und reproduzierbar nachweisbar sind. Im Mittelpunkt stehen nicht einzelne Demonstrationsfunktionen, sondern das belastbare Zusammenwirken der Systemebenen.

Daraus ergeben sich drei Projektfragen.

* **PF1 — Fahrkern und verteilte Echtzeitarchitektur:** Wie lässt sich ein Fahrkern auf Basis einer verteilten ESP32-S3-Architektur so realisieren, dass Motorregelung, Odometrie und die Verarbeitung von Geschwindigkeitskommandos deterministisch arbeiten und nicht durch blockierende Peripheriezugriffe beeinträchtigt werden?
  * *Einordnung:* Der Fahrkern bildet die Voraussetzung für jede weitere Systemfunktion. Instabile Regeltakte, Kommunikationsjitter oder konkurrierende Sensorzugriffe verschlechtern unmittelbar die Bewegungsqualität und damit alle nachgelagerten Funktionen.
* **PF2 — Sensor- und Sicherheitsbasis sowie Lokalisierung und Kartierung:** Welchen Beitrag leisten Odometrie-Kalibrierung, IMU-Integration, Kanten-Erkennung und die Kopplung mit LiDAR-basierter Kartierung dazu, eine belastbare Zustands- und Umgebungsbasis für den Innenraumbetrieb bereitzustellen?
  * *Einordnung:* Navigation erfordert eine räumlich konsistente Pose-Schätzung. Gleichzeitig muss die Sicherheitslogik sicherheitsnahe Signale priorisieren und Bewegungen stoppen können, bevor unsichere Zustände entstehen.
* **PF3 — Navigation und Bedien- und Leitstandsebene:** Wie lässt sich auf dieser Basis eine Systemarchitektur aufbauen, die Zielanfahrten, Recovery-Verhalten, Telemetrie, manuelle Eingriffe und Audio-Rückmeldungen in einer gemeinsamen Bedien- und Leitstandsebene zusammenführt, ohne die Freigabelogik zu unterlaufen?
  * *Einordnung:* Ein Missionskommando bezeichnet in dieser Arbeit ein freigegebenes Ziel- oder Moduskommando oberhalb roher Fahrbefehle. Die Freigabelogik entscheidet, welche Kommandos zulässig sind, blockiert oder in sichere Systemreaktionen überführt werden.

Die Arbeit konzentriert sich damit auf die Kernarchitektur eines AMR für Innenräume. Erweiterungen wie visuelle Semantik, Docking-Hilfen oder eine Sprachschnittstelle mit ReSpeaker Mic Array v2.0 werden als anschlussfähige Ausbaustufen der Bedien- und Leitstandsebene betrachtet, sind aber nicht der primäre Bewertungsmaßstab der Kernvalidierung.

---

## 1.3 Vorgehensweise und methodischer Rahmen

Die Arbeit folgt einem mechatronischen Entwicklungsansatz nach VDI 2206 und ordnet die Umsetzung in aufeinander aufbauende Systemphasen. Diese Phasen reduzieren die Komplexität auf wenige Kerngrößen und schaffen für jede Ebene eigene Bewertungsmaßstäbe.

1. **Fahrkern quantitativ absichern:** Zunächst wird die Grundbewegung des Differentialantriebs ausgelegt, implementiert und über Regelgüte, Geradeauslauf, Winkelfehler und Stoppverhalten bewertet.
2. **Sensor- und Sicherheitsbasis aufbauen:** Anschließend werden IMU, Batterieüberwachung, Ultraschall und Kanten-Erkennung integriert. Ziel ist eine belastbare Signalkette für sicherheitsnahe und zustandsbezogene Informationen.
3. **Lokalisierung und Kartierung herstellen:** Danach werden Odometrie, TF-Struktur, LiDAR und SLAM so gekoppelt, dass wiederholbare Karten und eine konsistente Re-Lokalisierung im Innenraum entstehen.
4. **Navigation mit Missionslogik koppeln:** Auf Grundlage der Karte werden Zielanfahrten, Recovery-Verhalten und sichere Bewegungsfreigaben untersucht. Bewertet werden Zielerreichung, Fehlfahrten, Kollisionen und nachvollziehbare Systemreaktionen.
5. **Bedien- und Leitstandsebene integrieren:** Abschließend werden Telemetrie, webbasierte Benutzeroberfläche, manuelle Eingriffe und Audio-Rückmeldungen als Betriebswerkzeug zusammengeführt.

Die methodische Umsetzung in den folgenden Kapiteln orientiert sich an dieser Struktur. Kapitel 2 erläutert die fachlichen Grundlagen. Kapitel 3 leitet Anforderungen und Randbedingungen ab. Kapitel 4 beschreibt das Systemkonzept. Kapitel 5 dokumentiert die Implementierung der Systemebenen. Kapitel 6 bewertet die Ergebnisse anhand messbarer Kriterien. Kapitel 7 verdichtet die Resultate, benennt Limitationen und leitet anschlussfähige Erweiterungen wie Sprachschnittstelle und weiterführende Multimodalität ab.
