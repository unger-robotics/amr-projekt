# Albarran et al. (2023) -- Differential-Drive Mobile Robot Controller with ROS 2 Support

## Bibliografische Angaben
- **Autoren:** Gustavo Albarran, Juan Nicolodi, Dante Ruiz, Diego Gonzalez-Dondo, Gonzalo Perez-Paina
- **Venue:** Revista elektron, Vol. 7, No. 2, S. 53--60
- **DOI/Link:** https://doi.org/10.37537/rev.elektron.7.2.184.2023
- **Institution:** Centro de Investigacion en Informatica para la Ingenieria (CIII), UTN-FRC, Cordoba, Argentinien
- **Eingereicht:** 02/10/2023, Akzeptiert: 06/12/2023

## Zusammenfassung (Abstract)

Autonome Mobile Roboter (AMRs) ersetzen zunehmend traditionelle AGVs in der Intralogistik verschiedener Industrie- und Produktionssektoren, da sie flexibler, sicherer und praeziser sind. Dieses Paper beschreibt die Entwicklung eines Controllers fuer einen Differentialantrieb-AMR mit ROS 2-Unterstuetzung durch micro-ROS auf einem eingebetteten System. Der Controller ist die Weiterentwicklung eines ueber 10 Jahre am CIII (UTN) eingesetzten Vorgaengerdesigns. Der Schwerpunkt liegt auf der Hardware-Entwicklung, wobei erste Software-Tests zur Verifikation des korrekten Betriebs durchgefuehrt wurden. Es werden die Designanforderungen definiert, ein Mikrocontroller mit nativer micro-ROS-Unterstuetzung ausgewaehlt und die einzelnen Stufen des Controllers (Spannungsversorgung, USB-Kommunikation, Batterieueberwachung, Debug-Port, PCB-Design) beschrieben.

## Kernaussagen

### 1. AMR vs. AGV -- Motivation und Kontext
- AGVs sind Schluesselkomponenten der internen Logistik in Flexible Manufacturing Systems (FMS), folgen aber vordefinierten Pfaden und koennen keine alternativen Routen waehlen (S. 53)
- AMRs sind flexibler als AGVs, da sie Technologien wie autonome Navigation, Computer Vision und SLAM nutzen, die bis vor kurzem der Forschung vorbehalten waren (S. 53)
- AMRs koennen sich sicher und ohne menschliches Eingreifen zwischen Orten bewegen und reduzieren die Kilometerlast des Personals bei der Produktverteilung in Fabriken (S. 54)
- Der industrielle AMR "Aimu" war drei Jahre lang bei Denso Manufacturing in Cordoba im produktiven Einsatz fuer den Transport von Teilen (S. 55)

### 2. ROS 2 und micro-ROS als Integrationsplattform
- ROS 1 hatte wesentliche Einschraenkungen: kein Produktionssoftware-Design, Probleme mit instabilen Netzwerken (WiFi), Single Point of Failure (ROS Master), keine native Unterstuetzung fuer eingebettete Systeme (S. 54)
- ROS 2 wurde unter Beruecksichtigung folgender Anwendungsfaelle entwickelt: Multi-Roboter-Teams, Echtzeitsysteme, nicht-ideale Netzwerke, Produktionsumgebungen und vorgeschriebene Architekturmuster (S. 54)
- ROS 2 nutzt den DDS-Standard (Data Distribution Service) anstelle eines eigenen Middlewares, was Sicherheit, Integritaet, Embedded-/Echtzeitsysteme, Multi-Roboter-Kommunikation und Betrieb in nicht-idealen Netzwerken ermoeglicht (S. 54)
- micro-ROS wurde entwickelt, um ROS 2 auf ressourcenbeschraenkte Mikrocontroller zu bringen, mit den Zielen: nahtlose Integration, einfache Portierbarkeit von ROS 2-Code und langfristige Wartbarkeit (S. 54)
- micro-ROS nutzt auf der Middleware-Ebene die Open-Source-Implementierung eProsima Micro XRCE-DDS und erweitert auf der Client-Bibliotheksebene die rcl (ROS 2 Client Library) mittels rclc-Paketen zu einer vollstaendigen Client-Bibliothek in C (S. 54)
- micro-ROS erlaubt es, Mikrocontroller als "First-Class Participants" in der ROS-Umgebung einzubinden, anstatt sie ueber einen Device-Driver anzusprechen -- die gleichen ROS-Konzepte wie auf leistungsstarken CPUs koennen verwendet werden (S. 54)

### 3. Vorgaenger-Controller und dessen Limitierungen
- Der bisherige Controller basierte auf dem NXP LPC2114 Mikrocontroller (32-bit ARM7TDMI-S), der fuer Neuentwicklungen nicht empfohlen wird und micro-ROS nicht unterstuetzt (S. 56)
- Die Hauptfunktionen des bisherigen Controllers waren: Kommunikation mit dem Onboard-PC fuer Geschwindigkeitsbefehle, Encoder-Auswertung, PID-Motorregelung und Odometrie-Berechnung (S. 55)
- Die bisherigen Roboter RoMAA-II und Aimu nutzen ROS ueber einen eigenen Treiber-Node [29], der als Device-Driver fungiert und High-Level-ROS-Messages in Low-Level-Befehle des eingebetteten Steuerungssystems uebersetzt (S. 56)

### 4. Differentialantrieb-Architektur
- Ein Differentialantrieb-Roboter (auch Unicycle genannt) hat zwei unabhaengig gesteuerte Antriebsraeder und ein oder mehrere nicht angetriebene Stuetzraeder (S. 55)
- Diese Architektur eignet sich besonders fuer Innenraeume, da der Roboter um sein odometrisches Zentrum rotieren kann -- also eine Orientierungsaenderung ohne Verschiebung moeglich ist (S. 55)
- Der Roboter wird ueber lineare Geschwindigkeit v und Winkelgeschwindigkeit omega in einem lokalen Koordinatensystem gesteuert; der interne Controller generiert daraus die Winkelgeschwindigkeiten der einzelnen Raeder (S. 55)
- Inkrementelle optische Encoder sind an die Antriebsraeder gekoppelt und liefern Informationen fuer die Odometrie-Berechnung -- die Schaetzung der Roboterpose (x, y, theta) basierend auf Radumdrehungen (S. 55)
- Blockdiagramm: Batterien -> 12/24V Energiebus -> Differentialantrieb-Controller -> H-Bruecken (links/rechts) -> Getriebemotoren, mit Encoder-Feedback; Onboard-Computer kommuniziert ueber Universal Serial Bus (S. 55)

### 5. Auswahl des ESP32-WROOM-32E
- Anforderungen an den Mikrocontroller: micro-ROS-Unterstuetzung, zwei PWM-Ausgaenge, Puls-Zaehlung fuer inkrementelle optische Encoder, ADC, USB oder UART-Kommunikation (S. 56)
- micro-ROS unterstuetzt einige 32-bit Mikrocontroller-Familien mittlerer Leistungsklasse; die Espressif-Familie wurde wegen Eignung und lokaler Verfuegbarkeit gewaehlt (S. 56)
- Ausgewaehltes Modell: ESP32-WROOM-32E mit SoC ESP32-D0WD-V3 (S. 56)
- Hauptmerkmale des ESP32-Moduls: Xtensa Dual-Core 32-bit LX6 mit bis zu 240 MHz, 448 KB ROM, 520 KB SRAM, 16 MB SPI Flash, 40 MHz Oszillator (S. 56)
- Peripherie: UART, SPI, I2C, PWM Motor, Pulse Counter, GPIO, ADC; WiFi und Bluetooth; integrierte PCB-Antenne (S. 56)

### 6. Hardware-Design des neuen Controllers (DDRC-ESP32)
- **Kompatibilitaet:** Gleiche PCB-Groesse und Stecker-Layout wie Vorgaenger fuer direkten Austausch (S. 56)
- **Verbesserungen gegenueber Vorgaenger:** Schaltnetzteil fuer hoehere Energieeffizienz, Batterie-Statuserkennung, allgemeine I/O-Ports, drahtlose Kommunikation via WiFi/Bluetooth (S. 57)
- **Spannungsversorgung:** LM2596-5 Step-Down-Schaltregler (bis 40V Eingang, 3A, 150 kHz Schaltfrequenz) fuer 5V; AMS1117-3.3 Linearregler fuer 3.3V (S. 57)
- **Gesamtstromverbrauch:** 294.32 mA im Worst-Case, davon ESP32-WROOM-32E allein 240 mA (S. 57)
- **USB-Kommunikation:** FT232RL USB-UART-Wandler (USB 2.0, bis 3 MBaud); ermoeglicht gleichzeitig Programmierung ueber Boot-Modus (GPIO0 auf 0V beim Reset) (S. 57)
- **Batterieueberwachung:** Zwei unabhaengige Eingaenge fuer bis zu 2x 12V-Batterien; 12-bit SAR-ADC mit V_Ref ca. 1100 mV; Signalkonditionierung durch zwei Operationsverstaerker (MPC6002) in Kaskade und Differenzkonfiguration mit Anti-Aliasing-Filter (S. 57)
- **PCB-Eigenschaften:** 105 mm x 75 mm, FR4 mit 1.6 mm Dicke, zweilagig mit metallisierten Durchkontaktierungen und Loetstopplack (S. 57)

### 7. Ein- und Ausgaenge des Controllers
- **Eingaenge:** Spannungsversorgung bis 40V DC (Klemmenblock), 2 inkrementelle optische Encoder (RJ14-Stecker), 2 analoge Eingaenge fuer Batteriespannung (S. 58)
- **Ausgaenge:** 2 PWM-Signale a 5V fuer H-Bruecken-Leistungsstufen (Molex), regulierter 5V-Ausgang fuer allgemeine Zwecke (Molex) (S. 58)
- **Bedienelemente:** Reset- und Boot-Taster, Power-LED, 2 USB-Status-LEDs, 3 Taster und 4 Allzweck-LEDs, Front-Panel-Anschluss (S. 58)
- **Kommunikation:** USB (Typ-B) zum Flashen und Kommunizieren, JTAG (Header) zum Debuggen (S. 58)

### 8. Software-Entwicklung und ESP-IDF/FreeRTOS
- Das ESP-IDF (IoT Development Framework) von Espressif basiert auf FreeRTOS, das die Programmierung von Applikationen fuer mehrere Kerne ermoeglicht (S. 58)
- Multi-Core-Anwendungen erschweren das Debugging aufgrund laufender Subprozesse -- JTAG ueber OpenOCD (von Espressif portiert fuer ESP32) wird empfohlen (S. 58--59)
- Der entwickelte Controller hat die notwendigen JTAG-Verbindungen und benoetigt einen JTAG-to-USB-Adapter mit OpenOCD-Unterstuetzung (z.B. ESP-Prog von Espressif) (S. 59)
- Das Software-Repository enthaelt: (1) eine ESP-IDF-basierte Testanwendung mit HTTP-Server zur Verifikation aller Controller-Komponenten, (2) Docker-Container-Dokumentation fuer ESP-IDF-Entwicklungsumgebung, (3) Dokumentation zur Installation der micro-ROS-Entwicklungsumgebung mit Docker (S. 58)
- Docker-Container werden sowohl fuer ESP-IDF als auch fuer micro-ROS verwendet, um Installation und Inbetriebnahme zu vereinfachen (S. 59)

### 9. Experimentelle Validierung
- Jede Schaltung des Controllers wurde zunaechst unabhaengig validiert, dann erfolgte die Integration und finale PCB-Fertigung (S. 59)
- Der Controller wurde auf der RoMAA-Roboter-Forschungsplattform montiert und getestet (S. 59)
- Eine Testanwendung mit HTTP-Server und WiFi ermoeglicht die Steuerung ueber Mobiltelefon/Webbrowser und bietet: Motoren einzeln ansteuern und Geschwindigkeiten einstellen, LEDs schalten, Pulszaehler der Encoder lesen, Batteriespannungen auslesen, Tasterstatus abfragen, WiFi-Kommunikation (S. 59)
- Die micro-ROS-Umgebung wurde erfolgreich getestet durch Bauen und Flashen eines Beispiel-ROS-Nodes auf dem ESP32: der Node publiziert eine Standardnachricht auf einem ROS-Topic und kommuniziert ueber WiFi; der korrekte Empfang wurde mit einem ROS 2-Agenten in einem Docker-Container auf einem entfernten PC verifiziert (S. 59)

### 10. Ergebnisse und zukuenftige Arbeit
- Das Endergebnis ist die Hardware eines Controllers fuer Differentialantrieb-Roboter, der ein ueber 10 Jahre genutztes Vorgaengerdesign ersetzt (S. 59)
- Der neue Controller basiert auf einem SoC mit nativer ROS 2-Unterstuetzung durch micro-ROS -- eine der Hauptdesignanforderungen (S. 59)
- Geplante zukuenftige Arbeiten: Anwendungen zur Evaluierung und Charakterisierung jeder Komponente (Raddrehzahlmessung mit Encodern, Batteriespannungsmessung), mit dem Ziel einer integrierten micro-ROS-basierten Robotersteuerungsanwendung (S. 59)
- Das Projekt ist Open Source und oeffentlich zugaenglich unter: https://github.com/ciiiutnfrc/ddrc_esp32 (S. 54, 60)

## Relevanz fuer die Projektarbeit

Dieses Paper ist direkt relevant, da es denselben Grundansatz verfolgt: einen ESP32-basierten Controller fuer einen Differentialantrieb-Roboter mit micro-ROS/ROS 2-Anbindung. Die Projektarbeit nutzt den ESP32-S3 (Dual-Core) mit FreeRTOS und micro-ROS ueber UART, waehrend Albarran et al. den ESP32-WROOM-32E (ebenfalls Dual-Core Xtensa LX6) verwenden. Besonders relevant sind die Designentscheidungen bezueglich micro-ROS-Integration, die Hardware-Architektur (Encoder-Eingaenge, H-Bruecken-PWM-Ausgaenge, Batterieueberwachung) und die Nutzung von FreeRTOS/ESP-IDF als Basis fuer die Multi-Core-Programmierung. Ein wesentlicher Unterschied: Die Projektarbeit geht deutlich weiter in der Software-Implementierung (PID-Regelung bei 50 Hz, Odometrie-Publishing bei 20 Hz, Kinematik-Module), waehrend Albarran et al. sich primaer auf das Hardware-Design konzentrieren und die vollstaendige micro-ROS-Robotersteuerung als zukuenftige Arbeit deklarieren.
