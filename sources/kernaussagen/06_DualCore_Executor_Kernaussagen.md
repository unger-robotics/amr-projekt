# Dual-Core ESP32 Partitionierung und rclc Executor -- Kernaussagen

---

## Paper 1: Yordanov et al. (2025) -- Integrated Wheel Sensor Communication using ESP32

### Bibliografische Angaben
- **Titel**: Integrated Wheel Sensor Communication using ESP32 -- A Contribution towards a Digital Twin of the Road System
- **Autoren**: Ventseslav Yordanov, Simon Schaefer, Alexander Mann, Stefan Kowalewski, Bassam Alrifaee, Lutz Eckstein
- **Jahr**: 2025
- **Quelle**: arXiv:2509.04061v1 [cs.RO], eingereicht beim IEEE
- **Institutionen**: Institute for Automotive Engineering (ika) und Chair of Embedded Software, RWTH Aachen; Department of Aerospace Engineering, Universitaet der Bundeswehr Muenchen
- **Foerderung**: DFG Collaborative Research Center / Transregio 339

### Kernaussagen

#### 1. Dual-Core-Partitionierung des ESP32 fuer Echtzeit-Sensorkommunikation
Die Autoren nutzen gezielt die Dual-Core-Architektur des ESP32, um Aufgaben nach Echtzeitanforderungen auf die beiden Kerne zu verteilen. **Core 1** uebernimmt die Wi-Fi-Kommunikation (Wi-Fi Task) und die Kommandoverarbeitung (Command Task). **Core 2** fuehrt die Micro-ROS-Task sowie alle Sensor-Datenakquisitions-Tasks aus (Akustik-, IMU-, Temperatur/Druck- und Batterie-Ueberwachung). Diese Trennung stellt sicher, dass die Netzwerkkommunikation die zeitkritische Sensorerfassung nicht blockiert. (S. 4-5, Table IV)

#### 2. FreeRTOS als Echtzeitbetriebssystem mit 1000 Hz Tick-Rate
Als Betriebssystem wird die Espressif-Adaption von FreeRTOS eingesetzt. Die Tick-Rate wurde auf **1000 Hz** konfiguriert (1 ms Aufloesung), um schnelles Context-Switching fuer zeitkritische Tasks zu ermoeglichen. FreeRTOS bietet einen **Fixed-Priority Preemptive Scheduler** mit Round-Robin Time-Slicing fuer Tasks gleicher Prioritaet. Die ESP32-Version unterstuetzt **Core Affinity**, um Tasks fest an bestimmte Kerne zu binden. (S. 4)

#### 3. Priorisierte Task-Hierarchie mit definierten Periodizitaeten
Die Tasks sind strikt nach Prioritaet geordnet: Micro-ROS Task (Prio 1, 4 ms), Akustik-Task (Prio 2, 7 ms), IMU-Task (Prio 3, 10 ms), Temperatur/Druck-Task (Prio 4, 200 ms), Batterie-Task (Prio 5, 1 s). Die hoechste Prioritaet liegt bei der Kommunikationsschicht (Micro-ROS), gefolgt von den Sensoren nach absteigender Abtastrate. (S. 5, Table IV)

#### 4. Kombination von Micro-ROS mit DDS/EmbeddedRTPS auf dem ESP32
Die Autoren verwenden **Micro-ROS** als ROS2-kompatible Middleware auf dem ESP32, aufbauend auf **EmbeddedRTPS** als DDS-Implementierung. EmbeddedRTPS ermoeglicht es Mikrocontrollern, als vollwertige DDS-Teilnehmer ohne Intermediary zu agieren. Fuer die Netzwerkkommunikation wird Espressifs **LwIP** (Lightweight IP) Stack verwendet. (S. 4)

#### 5. Technologieauswahl: Wi-Fi und DDS als optimale Kombination
Nach systematischem Vergleich von acht drahtlosen Technologien (Wi-Fi, Bluetooth, UWB, BLE, LR-WPAN, Z-Wave, LoRa, LTE-M, NB-IoT) wird **Wi-Fi** gewaehlt wegen: hoechster Datenrate (600 Mbit/s), niedrigster Latenz (0.6 ms) und einfacher Skalierbarkeit. Bluetooth wurde wegen notwendiger Intermediaries verworfen. (S. 3, Table II)

#### 6. DDS als Applikationsprotokoll statt MQTT oder AMQP
Fuenf Applikationsprotokolle wurden verglichen: AMQP (360 ms), CoAP (400 ms), DDS (2 ms), MQTT (130 ms), XMPP (600 ms). **DDS** wurde gewaehlt wegen der niedrigsten Latenz (2 ms fuer 1024-Byte-Payloads), der Peer-to-Peer-Faehigkeit ohne zentralen Broker und der konfigurierbaren QoS-Einstellungen. (S. 4, Table III)

#### 7. Thread-Safety durch FreeRTOS-Mechanismen
Fuer die Inter-Task- und Inter-Core-Kommunikation werden **Event Bits** und **Queues** eingesetzt. Queues sind Thread-sichere FIFO-Strukturen, die Datenueberschreibungen verhindern. Zusaetzlich bietet FreeRTOS **Mutexe** zur Vermeidung von Deadlocks. Event Bits koennen in Event Groups zusammengefasst werden, um Race Conditions zu vermeiden. (S. 4)

#### 8. Sensor-Datenraten bis 32 kHz bei minimalem Datenverlust
Das Prototypsystem erfasst Daten von einem Akustikmodul (32 kHz, 1024 kbit/s), einer IMU (562.5 Hz, 54 kbit/s), einem Temperatur-/Drucksensor (5 Hz) und einem Batteriemonitor (1 Hz). Die Gesamt-Mindestdatenrate betraegt **1078 kbit/s**. Im Experiment betrug der Datenverlust nur **0.1%**, und dieser trat nur bei Festplattenspeicherung auf, nicht im RAM-Cache. (S. 3, 5, Table I, Table V)

#### 9. Experimentelle Validierung auf Reifenpruefstand
Die Kommunikationsleistung wurde auf einem Trommel-Reifenpruefstand bei vier Vertikallasten (2628 N bis 9198 N) und Geschwindigkeiten bis 100 km/h validiert. Die **mittleren Nachrichtenabstaende** entsprachen exakt den erwarteten Periodizitaeten (z.B. AM: erwartet 7 ms, gemessen 6.999 ms; IMU: erwartet 10 ms, gemessen 10.001 ms). Waehrend der Messungen traten **keine Nachrichtenverluste** auf. (S. 5, Table V)

#### 10. Publish-Subscribe-Architektur mit einer konsolidierten Nachricht
Um den Speicherverbrauch auf dem ESP32 zu begrenzen, wird fuer alle Sensordaten **eine einzige konsolidierte DDS-Nachricht** verwendet. Dies reduziert die Anzahl der EmbeddedRTPS-Endpoints (Writer/Reader) und damit den RAM-Bedarf, da jeder Writer Proxies aller verbundenen Reader vorhalten muss. (S. 4)

### Relevanz fuer die Projektarbeit
Yordanov et al. validieren das **exakt gleiche Architekturmuster**, das in der Projektarbeit verwendet wird: Dual-Core-Partitionierung des ESP32 mit FreeRTOS und Micro-ROS. Die Projektarbeit partitioniert Core 0 fuer micro-ROS-Kommunikation und Core 1 fuer die PID-Regelschleife -- analog zur Trennung von Kommunikations- und Datenakquisitions-Tasks bei Yordanov. Die experimentell nachgewiesene Zuverlaessigkeit (0.1% Datenverlust, exakte Einhaltung der Periodizitaeten) stuetzt die Designentscheidung der Projektarbeit. Besonders relevant ist die Bestätigung, dass FreeRTOS mit 1000 Hz Tick-Rate und Core Affinity deterministische Echtzeitgarantien auf dem ESP32 bieten kann. Die Wahl von DDS/EmbeddedRTPS als Middleware wird durch den Latenzvergleich (2 ms vs. 130 ms MQTT) untermauert -- in der Projektarbeit wird zwar UART statt Wi-Fi verwendet, doch die DDS-basierte Micro-ROS-Schicht ist identisch.

---

## Paper 2: Staschulat et al. (2020) -- The rclc Executor

### Bibliografische Angaben
- **Titel**: The rclc Executor: Domain-specific deterministic scheduling mechanisms for ROS applications on microcontrollers: work-in-progress
- **Autoren**: Jan Staschulat, Ingo Luetkebohle, Ralph Lange
- **Jahr**: 2020
- **Quelle**: IEEE (Permission from IEEE for personal use)
- **Institution**: Corporate Research, Robert Bosch GmbH, Renningen, Germany
- **Foerderung**: EU-Projekt OFERA (micro-ROS) unter Grant Nr. 780785

### Kernaussagen

#### 1. Der Standard-ROS2-Executor ist weder echtzeitfaehig noch deterministisch
Der zentrale Befund des Papers: Der **Standard ROS 2 Executor**, verantwortlich fuer die Verarbeitung von Timern und eingehenden Nachrichten, ist in allen ROS 2 Releases (bis einschliesslich "Foxy") **weder echtzeitfaehig noch deterministisch**. Domaenenspezifische Anforderungen mobiler Roboter, wie Sense-Plan-Act-Regelschleifen, koennen mit dem Standard-Executor nicht adressiert werden. (S. 1)

#### 2. micro-ROS-Architektur: Drei zentrale Aenderungen gegenueber Standard-ROS2
micro-ROS unterscheidet sich in drei Punkten von Standard-ROS2: (1) Verwendung eines **RTOS** (Zephyr, FreeRTOS, NuttX) statt eines Desktop-Betriebssystems, (2) Einsatz von **DDS-XRCE** statt normalem DDS als Middleware, (3) Erweiterung der **ROS Client Support Library rcl** durch das **rclc-Paket** zur vollstaendigen C-API mit deterministischer Ausfuehrung. Trotz dieser Aenderungen stehen Standard-ROS2-Konzepte wie Topics, Services, Parameter, Lifecycle und Actions ueber dieselbe API zur Verfuegung. (S. 1, Figure 1)

#### 3. micro-ROS fuer Mikrocontroller ab ca. 100 KB RAM
Das micro-ROS-Projekt hat den Standard-ROS2-Stack auf **mittelgrosse Mikrocontroller (~100 KB RAM)** portiert. Dies ermoeglicht ROS2-Features wie Quality of Service und Security auf ressourcenbeschraenkten Geraeten. Die Portierung ist deutlich leichtgewichtiger als Alternativen wie mROS (400 MHz MCU, 10 MB RAM erforderlich). (S. 1)

#### 4. Domaenenspezifische Anforderungen: Sense-Plan-Act-Schleifen
Mobile Roboter haben spezifische Anforderungen, die vom Standard-Executor nicht erfuellt werden: (1) **Sense-Plan-Act-Regelschleifen** mit phasenweiser Ausfuehrung (erst alle Sensordaten verarbeiten, dann Planung, dann Aktion), (2) **Synchronisation von Sensordaten** unterschiedlicher Raten (z.B. Laser bei 10 Hz und IMU bei anderer Rate), (3) **Priorisierte Verarbeitung** fuer sichere Hinderniserkennung. (S. 2, Figure 2)

#### 5. Sensor-Datensynchronisation durch Trigger-Mechanismus
Die deterministische Synchronisation von Sensordaten unterschiedlicher Raten ist durch Latenz-Jitter und Clock Drift schwierig. Der rclc Executor loest dies durch einen **Trigger-Mechanismus**: Ein Sensor (z.B. Laser) triggert den Verarbeitungszyklus, woraufhin alle anderen Sensoren (z.B. IMU) explizit abgefragt werden, bevor die Verarbeitung beginnt. Dies erfordert eine **vordefinierte Verarbeitungsreihenfolge** der Callbacks. (S. 2, Figure 3)

#### 6. Zwei Hauptfeatures des rclc Executors: Sequenzielle Ordnung und Trigger
Der rclc Executor bietet zwei zentrale Features: (1) **Sequenzielle Verarbeitungsreihenfolge** aller Callbacks -- der Nutzer definiert explizit die Reihenfolge, in der Callbacks fuer eingehende Nachrichten, Timer-Events oder Hardware-Events verarbeitet werden. (2) **Trigger-Bedingungen** -- vordefinierte Bedingungen (one, any, all) bestimmen, wann die Verarbeitung startet. "One" triggert bei einem bestimmten Callback, "any" bei mindestens einem bereiten Callback, "all" wenn alle Callbacks bereit sind. Zusaetzlich koennen **benutzerdefinierte Trigger** implementiert werden. (S. 2)

#### 7. Statische Speicherallokation fuer Determinismus
Da Speicher auf Mikrocontrollern begrenzt ist, allokiert der rclc Executor dynamischen Speicher **ausschliesslich beim Start**. Waehrend der Laufzeit finden keine Speicherallokationen statt. Diese **statische Scheduling-Strategie** mit sequenzieller Verarbeitung erzeugt minimalen Performance-Overhead -- deutlich weniger als der aktuelle Standard-ROS2-Executor. (S. 2)

#### 8. Fixed-Size Messages zur Vermeidung dynamischer Allokation
micro-ROS verwendet **Fixed-Size Messages** als Einschraenkung gegenueber Standard-ROS2, um dynamische Speicherallokation zur Laufzeit zu vermeiden. Dies ist eine bewusste Designentscheidung fuer Echtzeitfaehigkeit auf Mikrocontrollern. (S. 1)

#### 9. DDS-XRCE als leichtgewichtige Middleware mit Client-Agent-Pattern
micro-ROS nutzt **DDS-XRCE (DDS for eXtremely Resource Constrained Environments)** als Middleware. Im Gegensatz zu EmbeddedRTPS, das einen vollstaendig verteilten Ansatz verfolgt, verwendet XRCE ein **Client-Agent-Pattern**: Der Mikrocontroller ist ein leichtgewichtiger Client, der ueber einen Agent auf einem leistungsfaehigeren System (z.B. Raspberry Pi) mit dem DDS-Netzwerk kommuniziert. Als Alternative steht EmbeddedRTPS fuer direkte DDS-Teilnahme zur Verfuegung. (S. 1)

#### 10. Proof-of-Concept: Kobuki-Roboter mit STM32F4
Der rclc Executor wurde auf dem **micro-ROS Kobuki Demo** demonstriert -- einem Turtlebot-2-basierten Roboter. Anstelle des ueblichen Laptops mit ROS2 wurde ein **STM32F4-Mikrocontroller** eingesetzt, der den micro-ROS-Stack und den Kobuki-Treiber ausfuehrt. Der STM32F4 kommuniziert die Sensordaten ueber DDS-XRCE per UDP an einen entfernten Laptop mit Standard-ROS2. Gleichzeitig kann der Roboter ferngesteuert werden. Der Demonstrator benoetigt **weniger als 100 KB RAM**. (S. 2, Figure 4)

### Relevanz fuer die Projektarbeit
Der rclc Executor ist eine **Kernkomponente** der in der Projektarbeit verwendeten micro-ROS-Implementierung auf dem ESP32. Die Projektarbeit nutzt micro-ROS auf Core 0 des ESP32 fuer die Kommunikation mit dem Raspberry Pi -- der rclc Executor ist dabei der Scheduler, der die Verarbeitung der `cmd_vel`-Subscriber-Callbacks und die `Odometry`-Publisher-Timer deterministisch steuert. Die im Paper beschriebene **Sense-Plan-Act-Architektur** spiegelt sich direkt im Datenfluss der Projektarbeit wider: Empfang von `cmd_vel` (Sense) -> inverse Kinematik/PID (Plan) -> PWM-Ausgabe (Act) -> Odometrie-Publish. Die **Trigger-Mechanismen** (one, any, all) ermoeglichen es, den `cmd_vel`-Callback als Trigger fuer den Regelzyklus zu verwenden. Die **statische Speicherallokation** beim Start ist besonders relevant fuer die ESP32-Firmware, da dynamische Allokation zur Laufzeit auf dem ESP32-S3 mit begrenztem RAM (512 KB) Fragmentierung und nicht-deterministisches Verhalten verursachen wuerde. Die Bestätigung, dass micro-ROS auf Mikrocontrollern ab ~100 KB RAM laeuft, validiert die Hardwarewahl der Projektarbeit.
