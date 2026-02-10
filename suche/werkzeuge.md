# Werkzeuge für wissenschaftliches Arbeiten – angewendet auf das AMR-Projekt

Die Dokumente gliedern den Tool-Stack in vier Phasen. Für eine anwendungsorientierte Arbeit (Prototyp-Entwicklung und Validierung) verschieben sich die Gewichte im Vergleich zu einer rein empirischen Sozialforschung erheblich.

### Phase 1: Literaturrecherche

Hier gelten dieselben Qualitätsanforderungen wie bei jeder wissenschaftlichen Arbeit – auch wenn das Ergebnis ein funktionierender Roboter und kein Hypothesentest ist.

**Datenbanken und ihre Rolle:**

- **Web of Science / Scopus:** Primärquelle für peer-reviewte Fachartikel. Für das AMR-Thema relevante Suchfelder: Robotik, Navigation, SLAM, Sensorfusion. Der Peer-Review-Status sichert die methodische Qualität der Quellen.
- **Google Scholar:** Einstiegspunkt, um Volltexte und Preprints zu finden (etwa über ResearchGate). Besonders nützlich für ROS-2-bezogene Konferenzpaper (z. B. IROS, ICRA).
- **SpringerLink:** Über den WBH-Online-Campus zugänglich. Liefert Fachbücher zu Regelungstechnik, Kinematik und Robotik als theoretische Basis.

**Suchstrategie – das „Masterquellen"-Prinzip:**

Das Dokument zur Literaturrecherche empfiehlt, zunächst einen aktuellen Review-Artikel zu identifizieren, der das Themenfeld überblickt. Für das AMR-Projekt wäre ein sinnvoller Einstieg:

- Suchbegriffe: `"autonomous mobile robot" AND "ROS 2" AND "navigation" AND Review`
- Ergänzend: `"SLAM" AND "differential drive" AND "indoor"`, `"Nav2" AND "evaluation"`
- Boolesche Operatoren (`AND`, `OR`, `NOT`) grenzen die Treffermenge systematisch ein.

Aus dem Literaturverzeichnis dieser Masterquelle lassen sich dann gezielte Satellitenquellen ableiten – etwa zu spezifischen Algorithmen (Cartographer, DWA) oder zur Odometrie-Fehlermodellierung.

**Qualitätsprüfung:** Jede Quelle durchläuft zwei Filter: (1) Ist die Zeitschrift in einem anerkannten Index gelistet? (2) Liegt ein Peer-Review-Verfahren vor? Wikipedia und nicht-begutachtete Blogposts dienen allenfalls der ersten Orientierung, nicht als zitierfähige Belege.

**Effizientes Sichten:** Das Abstract-Scanning spart Zeit – erst wenn Methode, Stichprobe/Versuchsaufbau und Hauptergebnis zur eigenen Fragestellung passen, lohnt sich die Volltextlektüre.

### Phase 2: Datenerhebung

Bei einer anwendungsorientierten Arbeit ersetzt der **Versuchsaufbau** die klassische Befragung. Das Exposé-Dokument definiert bereits konkret:

- Testparcours ($10 \times 10\,\mathrm{m}$), statische und dynamische Hindernisse
- Messgrößen: Positioniergenauigkeit ($\Delta x, \Delta y$), Wiederholgenauigkeit (Erfolgsrate über $N$ Versuche)

Die Erhebungswerkzeuge sind hier ROS-2-eigene Logging-Mechanismen (`rosbag2`), Encoder-Daten und ggf. ein externes Referenzmesssystem (Maßband, Laserdistanzmesser) als Ground Truth.

### Phase 3: Datenauswertung

Für die Validierungsdaten (Positionsabweichungen, Erfolgsraten) reichen deskriptive Statistiken – Mittelwert, Standardabweichung, ggf. Konfidenzintervall. Die Dokumente empfehlen:

- **PSPP oder R** statt Excel für nachvollziehbare Auswertungen
- Darstellung: Messwert → Kriterium (Anforderung aus dem Lastenheft) → Einordnung (erfüllt/nicht erfüllt)

### Phase 4: Textproduktion

- **LaTeX** passt gut zu dem bereits bestehenden Workflow und liefert typografisch korrekte Formeln und Einheiten.
- **KI-Einsatz** (z. B. Claude): Erlaubt, aber dokumentationspflichtig. Prompts und generierte Passagen gehören ins Hilfsmittelverzeichnis – das Verschweigen gilt als Täuschungsversuch.

---

## Dokumentation der Suchstrategie

Für die Nachvollziehbarkeit (ein zentrales Gütekriterium) muss die Recherche protokolliert werden:

1. **Datenbanken:** Welche wurden durchsucht?
2. **Suchbegriffe und Zeitraum:** z. B. „autonomous mobile robot" AND „ROS 2", Erscheinungsjahr 2018–2025
3. **Inklusions-/Exklusionskriterien:** z. B. nur englischsprachig, nur mit empirischer Validierung, keine reinen Simulationsstudien ohne Hardwaretests

---

## Einordnung: Wissenschaftlichkeit der anwendungsorientierten Arbeit

Das Differenzierungs-Dokument stellt klar: Die Arbeit generiert kein neues Grundlagenwissen, sondern transferiert bestehende Theorie (Kinematik, Regelungstechnik, SLAM-Algorithmen) auf ein konkretes Problem (KLT-Transport). Die Wissenschaftlichkeit entsteht durch die **methodische Sauberkeit** – Komponentenauswahl anhand von Datenblättern statt Bauchgefühl, Validierung durch Messung statt Demonstration, und transparente Dokumentation aller Entscheidungen.

