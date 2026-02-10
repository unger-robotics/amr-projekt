# Macenski et al. (2022) -- Robot Operating System 2: Design, Architecture, and Uses in the Wild

## Bibliografische Angaben
- **Autoren:** Steve Macenski, Tully Foote, Brian Gerkey, Chris Lalancette, William Woodall
- **Venue:** Science Robotics 7(66), 2022
- **DOI/Link:** https://www.science.org/doi/10.1126/scirobotics.abm6074
- **arXiv:** arXiv:2211.07752v1 [cs.RO], 14. November 2022

## Zusammenfassung (Abstract)

Das Paper ist ein umfassender Review-Artikel ueber ROS 2, die zweite Generation des Robot Operating System. Die Autoren beschreiben die philosophischen und architektonischen Veraenderungen, die ROS 2 gegenueber ROS 1 auszeichnen. ROS 1 war nicht fuer produktionsreife Anforderungen wie Sicherheit, Netzwerktopologie und Systemverfuegbarkeit ausgelegt. ROS 2 wurde von Grund auf neu entworfen, um moderne Robotersysteme in neuen und explorativen Domaenen auf allen Skalen zu unterstuetzen. Anhand von fuenf Fallstudien (Land, See, Luft, Weltraum, Grossserie) wird gezeigt, wie ROS 2 die Bereitstellung realer Robotersysteme in anspruchsvollen Umgebungen beschleunigt hat.

## Kernaussagen

### 1. Motivation und Limitierungen von ROS 1
- ROS 1 wurde durch den Robotik-Inkubator Willow Garage populaer gemacht, wobei Qualitaet und Performanz priorisiert wurden, aber Sicherheit, Netzwerktopologie und Systemverfuegbarkeit nicht (S. 1)
- ROS 1 basierte auf einem zentralen Name-Server (`roscore`), was einen Single Point of Failure darstellte (S. 2, Tabelle I)
- ROS 1 nutzte ein proprietaeres Protokoll auf TCP/UDP, waehrend ROS 2 auf den existierenden DDS-Standard setzt (S. 2, Tabelle I)
- ROS 1 hatte keine eingebauten Sicherheitsmechanismen und nur minimale Unterstuetzung fuer Embedded Systems (S. 2, Tabelle I)
- ROS 1 unterstuetzte nur Linux, waehrend ROS 2 auch Windows und macOS unterstuetzt (S. 2, Tabelle I)
- Die Limitierungen von ROS 1 zeigten sich besonders, als Forschungsplattformen zu kommerziellen Produkten uebergingen und Zuverlaessigkeit in nicht-traditionellen Umgebungen erforderlich wurde (S. 1)

### 2. ROS 2 als Software-Plattform
- ROS 2 ist Open Source unter der Apache 2.0 Lizenz, die breite Rechte zur Modifikation und Weiterverteilung ohne Rueckgabepflicht gewaehrt (S. 2)
- ROS 2 basiert auf einem foederierten Oekosystem, in dem Beitragende ermutigt werden, eigene Software zu erstellen und zu veroeffentlichen (S. 2)
- Das Software-Oekosystem gliedert sich in drei Kategorien: Middleware (Kommunikation), Algorithmen (Perception, SLAM, Planning) und Entwicklerwerkzeuge (CLI, GUI, Simulation, Logging) (S. 2-3)

### 3. Design-Prinzipien von ROS 2
- **Distribution:** Probleme in der Robotik werden am besten mit einem verteilten Systemansatz bewaeltigt. Anforderungen werden in funktional unabhaengige Komponenten getrennt (Hardwaretreiber, Wahrnehmungssysteme, Steuerungssysteme, Executives). Zur Laufzeit haben diese Komponenten eigene Ausfuehrungskontexte und teilen Daten ueber explizite Kommunikation (S. 3)
- **Abstraktion:** Kommunikations-Schnittstellenspezifikationen definieren die Semantik der ausgetauschten Daten. Eine gute Abstraktion fuehrt zu einem Oekosystem interoperabler Komponenten, die von spezifischen Hardware- oder Softwareanbietern abstrahiert sind (S. 3)
- **Asynchronitaet:** Nachrichten werden asynchron zwischen Komponenten kommuniziert, was ein ereignisbasiertes System erzeugt. Dies ermoeglicht die Arbeit ueber mehrere Zeitdomaenen hinweg (S. 3)
- **Modularitaet:** Nach dem UNIX-Designziel "mache jedes Programm gut in einer Sache". Modularitaet wird auf mehreren Ebenen durchgesetzt: Library-APIs, Nachrichtendefinitionen, CLI-Tools und das Software-Oekosystem selbst (S. 3)

### 4. Design-Anforderungen von ROS 2
- **Sicherheit:** ROS 2 integriert Authentifizierung, Verschluesselung und Zugriffskontrolle. Designer koennen ueber Access-Control-Policies definieren, wer worauf zugreifen darf (S. 3)
- **Embedded Systems:** Ein voller ROS 2-Stack laeuft nicht auf kleinen Embedded-Geraeten, aber ROS 2 soll die standardisierte Integration von CPUs und Mikrocontrollern erleichtern. *Micro-ROS* ermoeglicht die Nutzung von ROS 2 auf Embedded Systems (S. 3)
- **Diverse Netzwerke:** Roboter operieren in unterschiedlichsten Netzwerkumgebungen. ROS 2 bietet Quality of Service (QoS), um Datenfluesse an die Netzwerkbedingungen anzupassen (S. 3)
- **Echtzeit-Computing:** ROS 2 bietet APIs fuer Entwickler von Echtzeitsystemen, um anwendungsspezifische Zeitbeschraenkungen durchzusetzen (S. 3)
- **Produktreife:** ROS 2 zielt darauf ab, Produktanforderungen zu erfuellen. Apex.AI hat eine funktionale Sicherheitszertifizierung (ISO 26262) fuer ihre ROS 2-basierte autonome Fahrzeugsoftware erhalten (S. 3)

### 5. Kommunikationsmuster
- **Topics:** Das haeufigste Kommunikationsmuster -- ein asynchrones Message-Passing-Framework mit Publish-Subscribe-Funktionalitaet ueber stark typisierte Schnittstellen. Organisiert unter dem Konzept eines *Node* als Recheneinheit in einem Computational Graph (S. 3-4)
- **Services:** Ein Request-Response-Muster fuer synchrone Kommunikation. Der Service-Client wird waehrend eines Aufrufs nicht blockiert. Services sind unter einem Node organisiert fuer Systemdiagnose (S. 4)
- **Actions:** Ein einzigartiges Kommunikationsmuster fuer zielorientierte, asynchrone Schnittstellen mit Request, Response, periodischem Feedback und Abbruchmoeglichkeit. Geeignet fuer lang laufende Aufgaben wie autonome Navigation oder Manipulation (S. 4)

### 6. Middleware-Architektur und Abstraktionsschichten
- ROS 2 besteht aus mehreren entkoppelten Abstraktionsschichten, die ueber viele Pakete verteilt sind (S. 4)
- **Client Libraries** (rclcpp, rclpy, rcljava): Zugeschnitten auf jede Programmiersprache, bieten Zugang zu den Kern-Kommunikations-APIs. Kommunikation ist agnostisch gegenueber der Compute-Verteilung -- ob im gleichen Prozess, verschiedenen Prozessen oder verschiedenen Computern (S. 4)
- **rcl (ROS Client Library):** Eine in C geschriebene Zwischenschicht, die gemeinsame Funktionalitaet fuer alle Client Libraries bereitstellt (Actions, Parameter, Time, Console Logging, Node Lifecycle) (S. 4-5)
- **rmw (ROS MiddleWare):** Die Middleware-Abstraktionsschicht, die die essentiellen Kommunikationsschnittstellen bereitstellt. Verschiedene DDS-Implementierungen (Cyclone DDS, Fast DDS, Connext DDS) sind austauschbar ohne Code-Aenderungen (S. 4-5)
- Netzwerk-Interfaces werden mit *Message Types* ueber eine Interface Description Language (IDL) definiert (.msg oder .idl Dateien). Interface-Definitionen werden zur Compile-Zeit generiert (S. 5)

### 7. Architektonische Node-Patterns
- **Lifecycle Nodes:** Ein Pattern zur Verwaltung des Lebenszyklus von Nodes ueber eine State Machine mit den Zustaenden Unconfigured, Inactive, Active und Finalized. Ermoeglicht Systemintegratoren die Kontrolle, wann bestimmte Nodes aktiv sind -- ein wichtiges Werkzeug zur Koordinierung verteilter asynchroner Systeme (S. 5)
- **Component Nodes:** Nodes werden als *Components* geschrieben und koennen beliebigen Prozessen als Konfiguration zugewiesen werden. Mehrere Nodes koennen sich einen Prozess teilen, um Systemressourcen zu schonen oder Latenz zu reduzieren (S. 5)

### 8. Softwarequalitaet
- **Design-Dokumentation:** Vor groesseren Ergaenzungen muss eine schriftliche Design-Begruendung erstellt werden (Design Article oder ROS Enhancement Proposal/REP). Zum Zeitpunkt des Papers existierten 44 Design-Artikel und 7 REPs (S. 5)
- **Testing:** Jedes Feature erfordert Tests, die regelmaessig in Continuous Integration ausgefuehrt werden. Es werden 32.000-33.000 Tests auf ROS 2 ausgefuehrt, inklusive 13 Linter (S. 5)
- **Quality Declaration:** Eine mehrstufige Qualitaetspolitik definiert Anforderungen fuer jede Qualitaetsstufe (Entwicklungspraktiken, Testabdeckung, Sicherheit). 45 ROS 2-Pakete haben die hoechste Stufe (Quality Level 1) erreicht (S. 5-6)

### 9. Performance und Zuverlaessigkeit
- ROS 2 nutzt DDS mit UDP-Transport anstelle von TCP/IP. DDS entscheidet selbst, wann und wie Daten erneut uebertragen werden, und fuehrt Quality-of-Service (QoS) ein (S. 6)
- **QoS-Reliability:** "Best-effort" versucht eine einmalige Zustellung (gut fuer Sensordaten, die schnell veralten); "reliable" sendet weiter bis der Empfaenger den Empfang bestaetigt (S. 6)
- **QoS-Durability:** "Volatile" -- Nachrichten werden nach dem Senden vergessen; "transient-local" -- speichert und sendet Daten an spaet beitretende Subscriber (S. 6)
- **QoS-History:** "keep-all" speichert alle Daten; "keep-last" haelt eine feste Queue und ueberschreibt die aeltesten Eintraege. Weitere Einstellungen: deadline, lifespan, liveliness, lease duration (S. 6)
- **Performance-Benchmarks:** Intra-Process-Kommunikation ist am effizientesten mit <1 ms Latenz (95. Perzentil) fuer Nachrichten unter 8 MB. Single-Process ebenfalls <1 ms bei <8 MB. Multi-Process hat die hoechste Latenz und CPU-Auslastung, ist aber am flexibelsten (S. 6)
- Alle Mechanismen koennen zuverlaessig mit ueber 1 kHz fuer kleine Nachrichten publizieren (S. 6)
- **Paketverlust-Resilienz:** Bei moderatem Paketverlust (10%) kann ROS 2 Daten effektiv ueber das Netzwerk liefern. Bei 20% Verlust sinkt die Performance signifikant (S. 6-7)

### 10. Sicherheit (SROS2)
- ROS 2 stuetzt sich auf den DDS-Security-Standard und bietet zusaetzlich die SROS2-Toolsuite (S. 7)
- **Authentifizierung:** Digitale Signaturen mittels Public-Key-Kryptographie zur Identitaetsfeststellung (S. 7)
- **Zugriffskontrolle:** Fein-granulare Policies fuer authentifizierte Netzwerkteilnehmer -- nur genehmigte Teilnehmer und Interfaces (S. 7)
- **Verschluesselung:** AES-GCM symmetrische Verschluesselung verhindert Abhoeren und Replay-Angriffe (S. 7)

### 11. Fallstudie: Ghost Robotics (Land)
- Ghost Robotics setzt ROS 2 auf Nvidia Jetson Xavier fuer vierbeinige Roboter ein (~90% der Software nutzt ROS 2) (S. 7-8)
- Lifecycle Nodes und Component Nodes werden intensiv genutzt: Lifecycle Nodes aktivieren/deaktivieren Features dynamisch je nach Missionsbedarf (z.B. Umschalten zwischen GPS- und VIO-Lokalisierung); Component Nodes ermoeglichen parallele Entwicklung durch unabhaengige Teams (S. 7-8)
- ROS 2 als "Equalizer": Ghost konnte mit nur 23 Mitarbeitern (2021) ein wettbewerbsfaehiges Produkt schaffen und den Vision-60 mit ca. 30 Ingenieurjahren ausliefern -- dank Wiederverwendung von ROS 2-Komponenten (S. 8)
- Waehrend COVID-19 ermoeglichte der Gazebo-Simulator die vollstaendige Entwicklung einer USAF-Demonstration ohne Zugang zu physischen Robotern (S. 8)

### 12. Fallstudie: Mission Robotics (See)
- Mission Robotics nutzt ROS 2 als gemeinsame Datenschnittstelle fuer marine Roboter. Kunden koennen eigene Erweiterungen erstellen und Hardware modular integrieren (S. 8-9)
- Sensortreiber werden in Docker-Containern bereitgestellt, was sie vom Rest des Fahrzeugs isoliert (S. 9)
- ROS 2 fungiert als Industriestandard und Beschleuniger: Einheitliche Nachrichten, APIs und Tools beschleunigen die gesamte Marine-Robotik-Branche. rosbag fuer Datenlogging oeffnet die Tuer zur Zusammenarbeit (S. 9)

### 13. Fallstudie: Auterion Systems (Luft)
- Auterion integriert ROS 2 in Drohnensysteme neben dem PX4 Autopilot fuer hoehere Autonomiefunktionen (S. 9)
- Logging, Introspektion und Debugging (insbesondere rosbag2) sind zentral fuer die Drohnenentwicklung, da Umweltfaktoren wie Wind schwer reproduzierbar sind (S. 9)
- rviz2 fuer 3D-Visualisierung und Gazebo fuer Simulation sind entscheidende Werkzeuge. Auterion flog ca. 22.000 Stunden in Gazebo (2021), was 12 Vollzeit-Ingenieure fuer Tests ersetzte (S. 9-10)
- Gazebo wird in der CI-Pipeline fuer automatisierte End-to-End-Tests eingesetzt (S. 10)

### 14. Fallstudie: NASA VIPER (Weltraum)
- VIPER (Volatiles Investigating Polar Exploration Rover) nutzt ROS 2 fuer erdbasierte Operationstools, Rechenmodule und High-Fidelity-Simulationen (S. 10)
- Die Bodenstation empfaengt Telemetrie ueber Satellitenlink und verarbeitet sie in einem ROS 2-Netzwerk (Pointclouds, visuelle Odometrie, Terrain-Registrierung, Pose-Korrekturen) (S. 10)
- Gazebo-Simulation ist essentiell, da Mondumgebung (Beleuchtung, Gravitation) auf der Erde nicht testbar ist. NASA simulierte bis auf Hardware-Level herunter (S. 10)
- VIPER wiederverwendete 284.500 signifikante Codezeilen (SLOC) aus Gazebo ohne Modifikation (<1% Aenderung). Die geschaetzte Entwicklungsrate lag bei 116 SLOC pro Arbeitsmonat (S. 10)
- NASA waehlte DDS auch fuer Satellitenlinks wegen der Faehigkeit, hohe Latenz, niedrige Bandbreite und geringe Zuverlaessigkeit zu bewaeltigen (S. 10)

### 15. Fallstudie: OTTO Motors (Grossserie/Intralogistik)
- OTTO Motors ist ein Clearpath-Robotics-Spinoff fuer autonome Lager- und Fabriklogistik mit Tausenden von Robotern weltweit und ueber 100 Robotern pro Anlage (S. 10-11)
- ROS 1 skalierte nur bis ca. 25 Roboter im gleichen Netzwerk (Custom Multi-Master). Nach Migration auf ROS 2 konnte auf 100+ Roboter skaliert werden dank DDS-basierter Peer-to-Peer-Kommunikation und QoS fuer Bandbreiten-Management (S. 11)
- OTTO schaetzt Einsparungen von $1M-$5M ueber 5 Jahre durch ROS 2 und zusaetzlich Hunderte von eingesparten Ingenieurstunden (S. 11)
- ROS 2 als Enabler fuer das Geschaeftsmodell: "Haette ROS in grossem Massstab nicht existiert, waere das gesamte Geschaeft moeglicherweise nicht realisierbar gewesen" (CTO Ryan Gariepy) (S. 11)
- Die ROS 2-APIs ermoeglichen externen Partnern, auf OTTOs Autonomie-Faehigkeiten aufzubauen, ohne proprietary Libraries lernen zu muessen (S. 11)

### 16. Uebergreifende Erkenntnisse aus den Fallstudien
- **Software-Wiederverwendung:** Alle Unternehmen nutzen ROS 2-Community-Komponenten extensiv -- von Low-Level-Treibern bis zu High-Level-Algorithmen (S. 11-12)
- **Kollaboration:** ROS 2-Interfaces und Composition Nodes ermoeglichen parallele Entwicklung durch Teams, die sich nicht mit den Details anderer Systemteile befassen muessen (S. 12)
- **Trusted Platforms:** Alle Unternehmen verkaufen ihre Plattformen als vertrauenswuerdige Grundlage, auf der andere aufbauen koennen. Die freie Verfuegbarkeit von ROS hat es zum de-facto-Standard gemacht (S. 12)
- Diese emergenten Themen korrelieren stark mit den Design-Prinzipien Distribution, Abstraktion und Modularitaet (S. 12)

### 17. Schlussfolgerungen
- ROS 2 wurde von Grund auf neu entworfen, basierend auf durchdachten Prinzipien, modernen Robotik-Anforderungen und umfangreicher Anpassungsmoeglichkeit (S. 12)
- Basierend auf DDS ist ROS 2 ein zuverlaessiges, qualitativ hochwertiges Robotik-Framework, das eine breite Palette von Anwendungen unterstuetzen kann (S. 12)
- ROS 2 ist ein Enabler, ein Equalizer und ein Beschleuniger fuer die Robotik-Industrie und treibt die naechste Welle der Robotik-Revolution voran (S. 12)

## Relevanz fuer die Bachelorarbeit

Dieses Paper ist eine Kernreferenz fuer die Bachelorarbeit, da es die gesamte ROS 2-Architektur beschreibt, die auf dem Raspberry Pi 5 fuer Navigation und SLAM eingesetzt wird. Besonders relevant sind: (1) Die Beschreibung von micro-ROS als Bruecke zwischen Mikrocontrollern (ESP32) und dem ROS 2-Netzwerk (S. 3), was direkt dem Kommunikationsansatz der Bachelorarbeit entspricht; (2) Die QoS-Mechanismen (Reliability, Durability, History) fuer die Konfiguration der `cmd_vel`- und Odometrie-Topics ueber UART; (3) Die OTTO Motors-Fallstudie als direktes Beispiel fuer AMR-Intralogistik mit ROS 2, einschliesslich Skalierbarkeit und Flottenmanagement; (4) Die Lifecycle-Node-Patterns, die im Nav2-Stack der Bachelorarbeit genutzt werden, sowie die Component-Node-Architektur fuer ressourceneffiziente Ausfuehrung auf dem Raspberry Pi 5.
