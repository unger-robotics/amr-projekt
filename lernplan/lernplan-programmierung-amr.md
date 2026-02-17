# Lernplan: Systematische Programmierausbildung Autonome Mobile Robotik

**Zielgruppe:** Embedded-Entwickler mit C/C++-Praxis (ESP32, FreeRTOS, micro-ROS)
**Methodik:** Theorie → Übung → Anwendung (je Themenblock)


---

## Übersicht der Module

| Modul | Thema                                     | Dauer    | Voraussetzung                     |
|-------|-------------------------------------------|----------|-----------------------------------|
| M1    | Modernes C++ (C++17/20) & Design Patterns | 8 Wochen | C/C++-Grundlagen                  |
| M2    | Python für Robotik & Datenanalyse         | 6 Wochen | Grundlegende Programmiererfahrung |
| M3    | Algorithmik & Datenstrukturen             | 8 Wochen | M1 oder M2 abgeschlossen          |
| M4    | Software-Architektur & Clean Code         | 6 Wochen | M1 + M3 empfohlen                 |

Module M1 und M2 lassen sich parallel bearbeiten. M3 und M4 bauen auf den
ersten beiden auf.

```
Zeitachse (Wochen):
M1: C++17/20      ████████████████░░░░░░░░░░░░░░░░░░░░  (W01–W08)
M2: Python         ░░░░████████████████░░░░░░░░░░░░░░░░  (W03–W08)
M3: Algorithmen    ░░░░░░░░░░░░░░░░████████████████░░░░  (W09–W16)
M4: Architektur    ░░░░░░░░░░░░░░░░░░░░░░░░████████████  (W17–W22)
                   |       |       |       |       |
                   W01     W06     W11     W16     W22
```

---

## M1 — Modernes C++ (C++17/20) & Design Patterns

### Lernziele

Nach Abschluss von M1 kann der Lernende moderne C++-Sprachmittel
gezielt in Embedded- und ROS-2-Projekten einsetzen und gängige
Design Patterns erkennen, bewerten und anwenden.

### Woche 1–2: Fundament — Move-Semantik & Speicherverwaltung

**Theorie:**

- Wertekategorien (lvalue, rvalue, xvalue) und deren Bedeutung für
  Ressourcenübertragung
- Move-Konstruktor und Move-Zuweisungsoperator: Wann erzeugt der
  Compiler sie automatisch (Rule of Zero/Five)?
- Smart Pointer im Detail: `std::unique_ptr` (exklusiver Besitz),
  `std::shared_ptr` (geteilter Besitz mit Referenzzählung),
  `std::weak_ptr` (zyklische Referenzen vermeiden)
- RAII-Prinzip (Resource Acquisition Is Initialization): Ressourcen
  an Objektlebenszeit binden

**Übung:**

1. Implementiere eine `SensorBuffer`-Klasse mit dynamischem Speicher.
   Schreibe explizit Move-Konstruktor und Move-Zuweisung. Miss die
   Performance gegenüber der Kopier-Variante mit `std::chrono`.
2. Refaktoriere eine bestehende Klasse mit rohen Pointern (`new`/`delete`)
   auf `std::unique_ptr`. Überprüfe mit Valgrind oder AddressSanitizer,
   dass keine Leaks auftreten.
3. Baue eine `SharedConfig`-Klasse, die über `std::shared_ptr` von
   mehreren FreeRTOS-Tasks gelesen wird. Analysiere, wann der
   Destruktor aufgerufen wird.

**Anwendung (AMR-Bezug):**

- Ersetze im AMR-Projekt rohe Pointer in der Sensor-Abstraktionsschicht
  durch Smart Pointer. Dokumentiere die Änderung als Git-Commit mit
  Vorher-Nachher-Vergleich der Speichernutzung.

---

### Woche 3–4: Templates, `constexpr` & Compile-Time-Berechnung

**Theorie:**

- Funktions- und Klassen-Templates: Typdeduktion, SFINAE-Grundlagen
- `constexpr`-Funktionen und `constexpr if` (C++17): Berechnungen zur
  Kompilierzeit verlagern — relevant für Embedded, wo Laufzeit-Overhead
  kritisch ist
- Variadic Templates und Fold Expressions (C++17)
- `auto`-Rückgabetypen und Structured Bindings (`auto [x, y] = ...`)

**Übung:**

1. Schreibe ein generisches `RingBuffer<T, N>`-Template mit fester
   Größe (`constexpr N`). Teste mit `int`, `float` und einer eigenen
   `SensorReading`-Struktur.
2. Implementiere eine `constexpr`-Funktion zur CRC-8-Berechnung.
   Verifiziere, dass der Compiler das Ergebnis zur Kompilierzeit
   einsetzt (Assembler-Output prüfen mit `objdump` oder Compiler
   Explorer).
3. Nutze Structured Bindings, um Rückgabewerte einer Funktion
   `parseSensorFrame()` zu entpacken, die Status und Messwert liefert.

**Anwendung (AMR-Bezug):**

- Erstelle ein generisches `Publisher<MsgType>`-Template für micro-ROS,
  das verschiedene Nachrichtentypen (LaserScan, Odometrie, TF) mit
  einheitlicher Fehlerbehandlung publiziert.

---

### Woche 5–6: Standardbibliothek & funktionale Elemente

**Theorie:**

- STL-Container für Embedded: `std::array` (Stack), `std::vector`
  (Heap, vorsichtig auf MCU), `std::optional` (C++17, Fehlerfall
  ohne Exceptions)
- Algorithmen: `std::transform`, `std::accumulate`, `std::find_if` —
  deklarativer Stil statt manueller Schleifen
- Lambda-Ausdrücke: Capture-Semantik (`[=]`, `[&]`, `[this]`),
  generische Lambdas (`auto`-Parameter)
- `std::variant` und `std::visit` (C++17): Typsichere Unions als
  Alternative zu `switch`-Kaskaden

**Übung:**

1. Refaktoriere eine Schleife, die Sensorwerte filtert und
   transformiert, mit `std::transform` + Lambda.
2. Modelliere einen Zustandsautomaten (Idle, Moving, Error) mit
   `std::variant<IdleState, MovingState, ErrorState>` und
   `std::visit`. Vergleiche mit einer klassischen `enum + switch`-
   Implementierung hinsichtlich Erweiterbarkeit.
3. Nutze `std::optional<float>` als Rückgabetyp für eine Funktion,
   die einen Sensorwert liest — `std::nullopt` signalisiert einen
   Timeout.

**Anwendung (AMR-Bezug):**

- Implementiere den AMR-Betriebszustand (Init → Ready → Running →
  Error) als `std::variant`-basierte State Machine mit dokumentierten
  Übergangsbedingungen.

---

### Woche 7–8: Design Patterns für Embedded & ROS 2

**Theorie:**

- **Observer Pattern:** Entkopplung von Sensor-Produzenten und
  Konsumenten — Analogie zum ROS-2-Topic-Modell
- **Strategy Pattern:** Austauschbare Algorithmen (z. B. verschiedene
  Regler: PID, Fuzzy) hinter einheitlicher Schnittstelle
- **State Pattern:** Zustandsabhängiges Verhalten ohne `if`-Kaskaden
- **Singleton (kritisch betrachtet):** Warum Singletons in
  Multithread-Umgebungen (FreeRTOS) problematisch sind;
  Alternative: Dependency Injection
- **SOLID-Prinzipien** als Bewertungsrahmen für Pattern-Auswahl

**Übung:**

1. Implementiere ein Observer Pattern: `SensorPublisher` benachrichtigt
   registrierte `SensorListener`-Objekte bei neuen Messwerten.
   Vergleiche mit der ROS-2-Subscriber-Mechanik.
2. Baue ein Strategy Pattern für Motorsteuerung: `MotorController`
   akzeptiert austauschbare `SpeedStrategy`-Objekte (konstant, rampe,
   PID-geregelt).
3. Refaktoriere ein bestehendes `switch`-Statement in ein State Pattern.
   Bewerte den Mehraufwand gegenüber dem Gewinn an Erweiterbarkeit.

**Anwendung (AMR-Bezug):**

- Entwirf eine `NavigationStrategy`-Schnittstelle für den AMR, die
  zwischen Wandfolge, Wegpunktnavigation und SLAM-basierter Planung
  umschalten kann — ohne die Hauptschleife zu ändern.

---

## M2 — Python für Robotik & Datenanalyse

### Lernziele

Nach Abschluss von M2 kann der Lernende Python-Skripte für
Datenauswertung, Visualisierung und ROS-2-Nodes schreiben und
weiß, wann Python gegenüber C/C++ die geeignete Wahl ist.

### Woche 1–2: Python-Grundlagen (Crashkurs für C-Entwickler)

**Theorie:**

- Typsystem: Dynamisch typisiert, aber `type hints` (PEP 484) für
  Lesbarkeit und statische Analyse (mypy)
- Datenstrukturen: `list`, `dict`, `tuple`, `set` — Komplexitätsklassen
  kennen (z. B. `dict`-Lookup ist O(1) im Mittel)
- Kontrollfluss: List Comprehensions, Generatoren (`yield`),
  Context Manager (`with`)
- Unterschiede zu C: Garbage Collection statt RAII, keine Pointer,
  Indentation als Syntax, alles ist ein Objekt
- Virtuelle Umgebungen (`venv`) und Paketverwaltung (`pip`)

**Übung:**

1. Lies eine CSV-Datei mit Sensordaten ein (ohne externe Bibliothek,
   nur `csv`-Modul). Berechne Mittelwert, Standardabweichung und
   filtere Ausreißer (> 3σ).
2. Schreibe einen Generator, der fortlaufend simulierte IMU-Daten
   liefert. Konsumiere ihn mit einer `for`-Schleife.
3. Implementiere eine einfache Klasse `Pose2D(x, y, theta)` mit
   `__repr__`, `__eq__` und einer Methode `transform(dx, dy, dtheta)`.
   Nutze Type Hints durchgehend.

**Anwendung:**

- Schreibe ein Skript, das die AMR-Logdateien (`/var/log/amr/`)
  einliest, Zeitstempel parst und eine Übersicht der Fehlerhäufigkeit
  pro Modul ausgibt.

---

### Woche 3–4: NumPy, Matplotlib & Datenanalyse

**Theorie:**

- NumPy: ndarray-Konzept, Vektorisierung vs. Python-Schleifen
  (Performance-Faktor typisch 10–100×), Broadcasting-Regeln
- Matplotlib: Figure/Axes-API (objektorientiert, nicht `pyplot`-Stil),
  Subplots, Beschriftung nach wissenschaftlichem Standard
- Pandas (Grundlagen): DataFrame für tabellarische Daten,
  Zeitreihenindizierung, Gruppierung (`groupby`)

**Übung:**

1. Erzeuge ein simuliertes Lidar-Scan-Array (360 Werte, Winkel 0–359°).
   Plotte als Polardiagramm mit Matplotlib. Markiere Bereiche unter
   einem Schwellenwert farblich.
2. Lade eine reale ROS-2-Bag-Datei (oder exportierte CSV) mit
   Odometriedaten. Plotte die Trajektorie (x, y) und berechne die
   Gesamtfahrstrecke mit NumPy.
3. Analysiere die Latenzverteilung der micro-ROS-Kommunikation:
   Histogramm, Median, 95. Perzentil.

**Anwendung (AMR-Bezug):**

- Erstelle ein Python-Skript, das die TF-Tree-Daten des AMR aus einer
  Bag-Datei extrahiert, die Transformationskette visualisiert und
  Zeitversätze zwischen Frames quantifiziert.

---

### Woche 5–6: Python in ROS 2 & Automatisierung

**Theorie:**

- ROS-2-Python-API (`rclpy`): Node-Erstellung, Publisher, Subscriber,
  Services, Parameter
- Launch-Dateien in Python: Aufbau, Parameterübergabe, Konditionale
- Wann Python, wann C++? Faustregel: Python für Prototyping,
  Konfiguration, Datenanalyse, Tooling; C++ für zeitkritische
  Echtzeit-Nodes (Regelung, Sensorverarbeitung)
- Testframeworks: `pytest` für Unit-Tests, `launch_testing` für
  Integrationstests in ROS 2

**Übung:**

1. Schreibe einen ROS-2-Node in Python, der `/scan`-Daten subscribt
   und den minimalen Abstand als `/min_distance` (Float64) publiziert.
2. Erstelle eine Python-Launch-Datei, die den C++-micro-ROS-Agent und
   einen Python-Monitoring-Node gemeinsam startet.
3. Schreibe `pytest`-Tests für die `Pose2D`-Klasse aus Woche 1–2.

**Anwendung (AMR-Bezug):**

- Entwickle ein Python-basiertes Diagnose-Dashboard-Backend, das per
  ROS-2-Service den Systemstatus des AMR abfragt und als JSON über
  eine REST-API bereitstellt (Flask oder FastAPI).

---

## M3 — Algorithmik & Datenstrukturen

### Lernziele

Nach Abschluss von M3 kann der Lernende Algorithmen hinsichtlich
Zeitkomplexität (O-Notation) analysieren, passende Datenstrukturen
für gegebene Probleme auswählen und klassische Algorithmen in C++
und Python implementieren.

### Woche 1–2: Komplexitätsanalyse & grundlegende Datenstrukturen

**Theorie:**

- O-Notation: O(1), O(log n), O(n), O(n log n), O(n²) — Intuition
  und formale Definition. Unterschied zwischen Best, Average und
  Worst Case.
- Arrays vs. verkettete Listen: Zugriffszeit, Einfügekosten,
  Cache-Verhalten (Cache Locality ist auf Embedded besonders relevant)
- Stack und Queue: LIFO/FIFO-Prinzip, Implementierung mit Array
  (Ringpuffer) und verketteter Liste
- Hash-Tabellen: Hashfunktionen, Kollisionsstrategien (Chaining,
  Open Addressing), amortisierte O(1)-Suche

**Übung:**

1. Implementiere einen Ringpuffer (Queue) in C++ mit fester Größe.
   Vergleiche die Performance mit `std::queue<T, std::deque<T>>`.
2. Baue eine einfache Hash-Map in C++ mit Chaining. Messe die
   Kollisionsrate bei verschiedenen Hashfunktionen.
3. Implementiere dieselbe Hash-Map in Python. Vergleiche die
   Performance mit dem eingebauten `dict`.

**Anwendung (AMR-Bezug):**

- Der Sensor-Ringpuffer im AMR-Projekt: Analysiere die aktuelle
  Implementierung hinsichtlich Komplexität und Thread-Sicherheit.
  Dokumentiere Verbesserungspotenzial.

---

### Woche 3–4: Sortier- & Suchalgorithmen

**Theorie:**

- Vergleichsbasiertes Sortieren: Insertion Sort (O(n²), aber gut für
  kleine/fast sortierte Daten), Merge Sort (O(n log n), stabil),
  Quick Sort (O(n log n) im Mittel, in-place)
- Untere Schranke: Ω(n log n) für vergleichsbasiertes Sortieren —
  warum kein allgemeiner Algorithmus schneller sein kann
- Binäre Suche: Voraussetzung (sortierte Daten), Varianten
  (Lower/Upper Bound), Anwendung auf monotone Funktionen
- Lineare Suchalgorithmen und deren Berechtigung auf kleinen
  Datenmengen (Embedded-Kontext: n < 100)

**Übung:**

1. Implementiere Merge Sort und Quick Sort in C++. Benchmarke mit
   `std::sort` für verschiedene Eingabegrößen (100, 10.000,
   1.000.000 Elemente).
2. Schreibe eine binäre Suche, die in einem sortierten Array von
   Lidar-Distanzwerten den nächsten Wert zu einem Schwellenwert findet.
3. Analysiere, ab welcher Arraygröße sich binäre Suche gegenüber
   linearer Suche auf dem ESP32-S3 lohnt (Messung mit
   `esp_timer_get_time()`).

**Anwendung (AMR-Bezug):**

- Optimiere die Hindernis-Erkennung: Sortiere Lidar-Scanpunkte nach
  Distanz und nutze binäre Suche für Schwellenwert-Prüfungen statt
  linearer Iteration.

---

### Woche 5–6: Bäume & Graphen

**Theorie:**

- Binäre Suchbäume (BST): Einfügen, Suchen, Löschen — O(h) mit
  Baumhöhe h. Degenerierter Fall: h = n (verkettete Liste)
- Balancierte Bäume: AVL-Baum oder Red-Black-Tree — Garantie
  h = O(log n). `std::map` und `std::set` nutzen intern Red-Black-Trees
- Graphen: Darstellung als Adjazenzliste vs. Adjazenzmatrix.
  Speicherbedarf: O(V + E) vs. O(V²)
- Graph-Traversierung: BFS (Breitensuche, kürzester Pfad in
  ungewichteten Graphen), DFS (Tiefensuche, Zykluserkennung)

**Übung:**

1. Implementiere einen BST in C++ mit Einfügen, Suchen und
   In-Order-Traversierung. Teste mit zufälligen und sortierten Daten.
2. Implementiere BFS und DFS auf einem Graphen (Adjazenzliste).
   Visualisiere die Traversierungsreihenfolge.
3. Modelliere eine einfache Gitterkarte (Occupancy Grid) als Graph.
   Finde mit BFS den kürzesten Weg von Start zu Ziel.

**Anwendung (AMR-Bezug):**

- Implementiere einen einfachen Pfadplanungs-Prototyp: Die SLAM-
  generierte Occupancy Grid Map als Graph modellieren, BFS für
  kürzeste Pfade.

---

### Woche 7–8: Fortgeschrittene Algorithmen & Robotik-Bezug

**Theorie:**

- Dijkstra-Algorithmus: Kürzester Pfad in gewichteten Graphen,
  O((V + E) log V) mit Priority Queue
- A*-Algorithmus: Heuristisch geführte Suche, Zulässigkeits-
  bedingung der Heuristik (Unterschätzung), Optimalität
- Priority Queue / Heap: Implementierung, O(log n) für Einfügen
  und Entfernen des Minimums
- Dynamische Programmierung: Prinzip der optimalen Teilstruktur,
  Memoization vs. Bottom-Up

**Übung:**

1. Implementiere Dijkstra in C++ mit `std::priority_queue`.
   Teste auf einem gewichteten Gittergraphen.
2. Erweitere zu A* mit euklidischer Distanz als Heuristik.
   Vergleiche die Anzahl besuchter Knoten mit Dijkstra.
3. Löse das „Minimum-Cost-Path"-Problem auf einer Costmap mit
   dynamischer Programmierung. Vergleiche mit A*.

**Anwendung (AMR-Bezug):**

- Integriere den A*-Algorithmus als ROS-2-Node (C++ oder Python):
  Subscribt die Costmap, berechnet den Pfad, publiziert als
  `nav_msgs/Path`. Benchmarke die Rechenzeit auf dem Raspberry Pi 5.

---

## M4 — Software-Architektur & Clean Code

### Lernziele

Nach Abschluss von M4 kann der Lernende Code systematisch
strukturieren, technische Schuld erkennen und begründete
Architekturentscheidungen für mittelgroße Projekte treffen.

### Woche 1–2: Clean-Code-Prinzipien

**Theorie:**

- Namensgebung: Intention offenlegen, Kontextinformation im Namen
  tragen (`distanceMm` statt `d`), konsistente Konventionen
  (snake_case für C, CamelCase für Klassen)
- Funktionen: Eine Aufgabe pro Funktion, maximal 3 Parameter
  (darüber hinaus → Strukturen/Objekte), keine Seiteneffekte
  ohne Dokumentation
- Kommentare: Code soll sich selbst erklären; Kommentare für
  *Warum*, nicht für *Was*. Doxygen-Format für API-Dokumentation.
- DRY (Don't Repeat Yourself) vs. WET (Write Everything Twice):
  Wann Abstraktion gerechtfertigt ist und wann vorzeitige
  Abstraktion schadet (Rule of Three)

**Übung:**

1. Nimm 200 Zeilen aus dem AMR-Projekt und refaktoriere:
   Variablen umbenennen, Funktionen extrahieren, Kommentare
   überarbeiten. Erstelle ein Vorher-Nachher-Diff.
2. Schreibe eine Funktion mit mehr als 5 Parametern um:
   Führe eine Konfigurationsstruktur ein.
3. Identifiziere drei DRY-Verletzungen im eigenen Code.
   Entscheide begründet, welche sich lohnen zu beheben.

**Anwendung (AMR-Bezug):**

- Erstelle einen Coding-Standard (1–2 Seiten) für das AMR-Projekt:
  Namenskonventionen, Kommentarformat, Funktionslänge, Error-Handling.

---

### Woche 3–4: Architektur-Prinzipien & Modularisierung

**Theorie:**

- SOLID-Prinzipien im Detail:
  - **S**ingle Responsibility: Eine Klasse, ein Änderungsgrund
  - **O**pen/Closed: Erweiterbar ohne Modifikation (Strategy Pattern)
  - **L**iskov Substitution: Subtypen müssen Verträge einhalten
  - **I**nterface Segregation: Schlanke, spezifische Schnittstellen
  - **D**ependency Inversion: Abhängigkeit von Abstraktionen, nicht
    von Implementierungen
- Schichtenarchitektur (Layered Architecture): HAL → Treiber →
  Middleware → Applikation — Abhängigkeitsrichtung nur nach unten
- Kopplung vs. Kohäsion: Metriken und Heuristiken zur Bewertung

**Übung:**

1. Zeichne die aktuelle Architektur des AMR-Projekts als
   Komponentendiagramm. Identifiziere Zyklen in den Abhängigkeiten.
2. Refaktoriere eine Komponente, die gegen das Single-Responsibility-
   Prinzip verstößt, in zwei getrennte Module.
3. Führe ein Interface (`abstract class` in C++) für die
   Sensorabstraktion ein, sodass Lidar und Ultraschall austauschbar
   werden.

**Anwendung (AMR-Bezug):**

- Dokumentiere die AMR-Architektur nach dem V-Modell (VDI 2206):
  Systemanforderungen → Komponentenentwurf → Implementierung →
  Integrationstest. Erstelle ein Architecture Decision Record (ADR)
  für die Dual-Core-Aufteilung (ESP32-S3 Core 0/1).

---

### Woche 5–6: Testen, Fehlerbehandlung & technische Schuld

**Theorie:**

- Testpyramide: Unit-Tests (Basis, schnell, isoliert) →
  Integrationstests → Systemtests. Abdeckungsziele: Pfad- vs.
  Anweisungsüberdeckung
- Unit-Testing in C++: Google Test (gtest), Mocking mit Google Mock.
  In Python: pytest, fixtures, parametrisierte Tests
- Fehlerbehandlung in Embedded: Return Codes vs. Exceptions
  (auf ESP32 i. d. R. keine Exceptions) vs. `std::expected` (C++23)
  vs. `std::optional` (C++17)
- Technische Schuld: Identifizieren (Code Smells), Priorisieren
  (Impact × Likelihood), systematisch abbauen (Boy-Scout-Rule)

**Übung:**

1. Schreibe Unit-Tests (gtest) für drei Kernfunktionen des AMR-
   Projekts. Erreiche mindestens 80 % Branchabdeckung.
2. Implementiere eine konsistente Fehlerbehandlungsstrategie:
   Definiere Error-Codes als `enum class`, schreibe eine
   `ErrorHandler`-Klasse, die Fehler loggt und Wiederherstellungs-
   maßnahmen einleitet.
3. Erstelle eine technische Schulden-Liste für das AMR-Projekt.
   Priorisiere nach Risiko und Aufwand (2×2-Matrix).

**Anwendung (AMR-Bezug):**

- Richte eine CI-Pipeline ein (GitHub Actions), die bei jedem Push
  automatisch kompiliert, Unit-Tests ausführt und die Code-Abdeckung
  reportet.

---

## Empfohlene Ressourcen

### Bücher

| Thema       | Titel                                          | Autor                            |
|-------------|------------------------------------------------|----------------------------------|
| C++         | *Effective Modern C++*                         | Scott Meyers                     |
| C++         | *C++ Templates: The Complete Guide* (2. Aufl.) | Vandevoorde, Josuttis, Gregor    |
| Patterns    | *Design Patterns* (GoF)                        | Gamma, Helm, Johnson, Vlissides  |
| Python      | *Fluent Python* (2. Aufl.)                     | Luciano Ramalho                  |
| Algorithmen | *Introduction to Algorithms* (CLRS)            | Cormen, Leiserson, Rivest, Stein |
| Algorithmen | *Algorithms* (4. Aufl.)                        | Sedgewick, Wayne                 |
| Clean Code  | *Clean Code*                                   | Robert C. Martin                 |
| Architektur | *Clean Architecture*                           | Robert C. Martin                 |
| Embedded    | *Making Embedded Systems* (2. Aufl.)           | Elecia White                     |

### Online-Plattformen

| Plattform                                                        | Fokus                                                |
|------------------------------------------------------------------|------------------------------------------------------|
| [Compiler Explorer](https://godbolt.org)                         | C++-Assembler-Output, Template-Instanziierung prüfen |
| [LeetCode](https://leetcode.com)                                 | Algorithmik-Übungen (Schwerpunkt: Medium-Level)      |
| [CppReference](https://en.cppreference.com)                      | C++-Standardbibliothek-Referenz                      |
| [ROS 2 Tutorials](https://docs.ros.org/en/humble/Tutorials.html) | ROS 2 Humble Dokumentation                           |
| [The Algorithms](https://the-algorithms.com)                     | Algorithmen in verschiedenen Sprachen                |

---

## Fortschrittskontrolle

Jedes Modul schließt mit einer Selbstbewertung ab:

| Kriterium                                    | Bewertung (1–5) |
|----------------------------------------------|-----------------|
| Theorie verstanden und erklärbar             | ☐               |
| Alle Übungen eigenständig gelöst             | ☐               |
| Anwendungsaufgabe im AMR-Projekt umgesetzt   | ☐               |
| Code-Review durch Claude oder Peer bestanden | ☐               |
| Erkenntnisse dokumentiert (Lerntagebuch)     | ☐               |

**Ziel:** Mindestens 4/5 in jedem Kriterium, bevor das nächste Modul
beginnt.

---

*Erstellt: Februar 2026 | Methodik: Bloch+Akademisch | Version: 1.0*
