# Kernaussagen: Wang et al. 2024 -- Priority-Driven Chain-Aware Scheduling fuer micro-ROS

## Bibliografische Angaben

- **Titel**: Improving Real-Time Performance of Micro-ROS with Priority-Driven Chain-Aware Scheduling
- **Autoren**: Zilong Wang, Songran Liu, Dong Ji, Wang Yi
- **Institution**: School of Computer Science and Engineering, Northeastern University, Shenyang, China
- **Journal**: Electronics, 2024, 13, 1658
- **DOI**: https://doi.org/10.3390/electronics13091658
- **Datum**: Published 25 April 2024; Received 25 March 2024
- **Lizenz**: CC BY 4.0
- **Quelle**: /sources/20_Wang_2024_Scheduling.pdf

## Zusammenfassung

Die Autoren analysieren das Callback-Scheduling und das Kommunikationsmodul von micro-ROS und identifizieren drei kritische Designschwaechen, die die Echtzeitfaehigkeit beeintraechtigen: (1) Priority Inversion im Callback-Scheduling, (2) Ineffizienz bei synchroner Datenuebertragung und (3) Priority Inversion beim FIFO-basierten Datenempfang. Als Loesung wird PoDS (Priority-Driven Chain-Aware Scheduling System) vorgeschlagen, bestehend aus dem TIDE Executor, einem prioritaetsbasierten Datenverarbeitungsmechanismus und einem Communication Daemon. PoDS zeigt signifikant bessere und stabilere Echtzeitleistung als Standard-micro-ROS.

## Kernaussagen

### 1. micro-ROS Architektur und Rolle (S. 1-2)

- **micro-ROS** ueberbrueckt die Leistungsluecke zwischen ressourcenbeschraenkten Mikrocontrollern und leistungsstarken Computern in ROS-basierten Robotiksystemen (S. 1).
- Typische Aufgabenteilung: Mikrocontroller uebernehmen **Sensorik und Aktorik** (niedrige Latenz, Echtzeit), waehrend leistungsstaerkere Rechner **SLAM, Pfadplanung und Navigation** durchfuehren (S. 1).
- micro-ROS nutzt die ROS 2 Client Support Library (RCL) und eine neue RCLC (ROS 2 Client Library in C). Die Middleware-Schicht verwendet **Micro XRCE-DDS** von eProsima. Unterstuetzte RTOS: FreeRTOS, Zephyr, NuttX (S. 3).
- Kommunikation zwischen Micro XRCE-DDS Client und ROS 2 Agent erfolgt ueber **TCP, UDP oder serielle Schnittstellen** (S. 3).

### 2. Zentrale Konzepte: Callback, Chain, Executor (S. 3)

- **Callback**: Kleinste planbare Ausfuehrungseinheit in ROS 2 und micro-ROS. Vier Typen: Timer, Subscriptions, Services, Clients. Timer-Callbacks werden periodisch ausgeloest, regulaere Callbacks durch externe Events (z.B. Nachrichtenempfang) (S. 3).
- **Chain**: Eine Sammlung von Callbacks, die zusammen eine spezifische Anforderung erfuellen (z.B. Sensor lesen -> verarbeiten -> publizieren) (S. 3).
- **Executor**: Zentrale Komponente, die die Ausfuehrungsreihenfolge von Callbacks mit unterschiedlichen Prioritaeten koordiniert (S. 3).

### 3. RCLC Executor -- Standardverhalten in micro-ROS (S. 3-4)

- Der RCLC Executor arbeitet in zwei Phasen:
  - **Collection Phase**: Leert wait_set, sammelt abgelaufene Timer-Callbacks, verarbeitet das **erste** unbearbeitete Datenpaket vom ROS 2 Agent, sammelt zugehoerigen regulaeren Callback (S. 3).
  - **Execution Phase**: Prueft Trigger-Bedingung; wenn erfuellt, fuehrt alle ready Callbacks in wait_set aus (S. 3).
- Gegenueber dem RCLCPP Executor bietet der RCLC Executor zwei Extras: **Trigger Conditions** (ANY, ALL, ONE, User-defined) und **benutzerdefinierte Ausfuehrungsreihenfolge** (S. 3).
- Die implizite Prioritaet ergibt sich aus der Registrierungsreihenfolge: Frueher registrierte Callbacks werden zuerst ausgefuehrt (S. 3).

### 4. Kommunikationsmodell micro-ROS <-> ROS 2 Agent (S. 4)

- **Datenuebertragung**: Synchron -- Executor-Thread serialisiert Daten in Framing_Buffer, konfiguriert DMA-Kanal und **blockiert** (busy-wait) bis zur DMA-Fertigstellung. Im Reliable-Modus zusaetzlich Heartbeat + ACK mit erneuter Blockierung (S. 4).
- **Datenempfang**: Asynchron ueber DMA -- Pakete landen in DMA_Buffer. Pro Collection-Phase wird nur **ein** unverarbeitetes Paket nach **FIFO** verarbeitet (CRC-Pruefung, Kopie nach Static_Buffer_Memory) (S. 4).

### 5. Drei identifizierte Designprobleme (S. 2, 5-6)

- **(1) Low Determinism -- Priority Inversion im Callback-Scheduling**: Batch-basierte Strategie sammelt alle bereiten Callbacks in wait_set und fuehrt sie in Registrierungsreihenfolge aus. Ein hoch-priorisierter Callback muss warten, bis alle niedrig-priorisierten Callbacks der gleichen Batch abgearbeitet sind (S. 2, 5, Fig. 3).
- **(2) Inefficiency -- Synchrone Datenuebertragung**: Executor blockiert waehrend DMA-Uebertragung (busy-wait). Bei grossen Datenpaketen verzoegert sich die Ausfuehrung aller weiteren Callbacks erheblich (S. 2, 5).
- **(3) Priority Inversion beim Datenempfang**: FIFO-basierte Verarbeitung in DMA_Buffer ignoriert Callback-Prioritaeten. Niedrig-priorisierte Pakete werden vor hoch-priorisierten verarbeitet, wenn sie frueher eintrafen (S. 5-6, Fig. 4).

### 6. PoDS-Architektur -- Ueberblick (S. 6-7)

- **PoDS** (Priority-Driven Chain-Aware Scheduling System) besteht aus drei Komponenten:
  1. **TIDE Executor** (Timing-Deterministic and Efficient) fuer Callback-Scheduling
  2. **Priority-Based Data-Processing Mechanism** fuer Datenempfang
  3. **Communication Daemon** fuer Datenuebertragung (S. 7, Fig. 5)
- Kernprinzip: Jeder Callback wird **explizit mit einer Prioritaet** verknuepft. Alle Operationen (Scheduling, Uebertragung, Empfang) erfolgen prioritaetsbasiert (S. 7).

### 7. TIDE Executor -- Design (S. 7-8)

- Ersetzt das einheitliche wait_set durch **zwei prioritaetsgesteuerte Queues**:
  - **TimerList**: Ueberwacht Timer-Callbacks, sortiert nach next_call_time. Nur der Head muss geprueft werden (O(1) statt O(n)) (S. 7-8).
  - **ReadyList**: Prioritaets-Queue fuer ausfuehrungsbereite Callbacks. Der Callback mit hoechster Prioritaet ist immer am Head (S. 8).
- **Feingranulare Ausfuehrung**: Pro Runde wird nur **ein** Callback (der mit hoechster Prioritaet aus ReadyList) ausgefuehrt -- nicht mehr eine ganze Batch. Dadurch wird Priority Inversion eliminiert (S. 8, Fig. 6).

### 8. Priority-Based Data-Processing Mechanism (S. 8-9)

- Neue Funktion parst nur den **Datenpaket-Header** (~20 Bytes) um Callback-ID und Prioritaet zu ermitteln, ohne vollstaendige CRC-Pruefung und Payload-Kopie (S. 9).
- Preprocessing aller Pakete in DMA_Buffer ergibt Prioritaetsinformation; regulaere Callbacks werden dann **nach Prioritaet** statt FIFO gesammelt (S. 9, Fig. 8).
- Preprocessing findet nur einmal pro Paket statt, da die Ergebnisse gespeichert werden (S. 9).

### 9. Communication Daemon (S. 9-11)

- **Parallel Transmission Handler**: Entkoppelt Callback-Ausfuehrung und Datenuebertragung durch Nutzung eines **Data_Sending_Pool** mit drei Komponenten:
  - Data_Pool: Vorab-allokierte Buffer Nodes
  - Execution_Buffer: Prioritaets-Queue (absteigend nach Callback-Prioritaet)
  - Pending_Buffer: Prioritaets-Queue (aufsteigend nach Timestamp, fuer Reliable-Modus) (S. 10)
- DMA-Uebertragung erfolgt parallel zur Callback-Ausfuehrung; bei besetztem DMA-Kanal wird in Execution_Buffer eingereiht (S. 10, Fig. 9).
- **Interrupt-Based Data Reception Handler**: Unterscheidet regulaere Nachrichten (weitergeleitet an TIDE Executor) von ACK-Nachrichten (direkt im Interrupt verarbeitet). Eliminiert den Busy-Wait beim Warten auf ACKs im Reliable-Modus (S. 11).

### 10. Experimentelle Evaluation -- Setup (S. 11-12)

- **Hardware**: NUCLEO-F767ZI (ARM Cortex-M7, 216 MHz, 2 MB Flash, 512 KB SRAM) mit FreeRTOS (V202212.00) (S. 11-12).
- **ROS 2**: Humble auf Desktop-PC (Ubuntu 20.04.6, 14 Kerne, 16 GB RAM) (S. 12).
- **Kommunikation**: UART bei **115.200 bps** (serielle Schnittstelle) (S. 12).
- **Metrik**: End-to-End-Latenz einer Chain (Zeit vom Start des ersten Callbacks bis zur Fertigstellung des letzten) via `xTaskGetTickCount()` (FreeRTOS System Tick: 10 ns) (S. 12).

### 11. Experimentelle Ergebnisse -- Leistungsvergleich (S. 12-15)

- **Einfluss der Chain-Anzahl** (1-5 Chains, 500 ms Periode, 100 Byte Pakete, 10 ms Callback-Zeit):
  - Bei 1 Chain: PoDS und micro-ROS identisch (~37 ms) (S. 12).
  - Bei 5 Chains: PoDS ~41 ms vs. micro-ROS ~120 ms. Jede zusaetzliche niedrig-priorisierte Chain erhoeht die Latenz in micro-ROS um ~20 ms, waehrend PoDS nahezu konstant bleibt (S. 12-13, Fig. 10).

- **Einfluss der Datenpaketgroesse** (100-500 Bytes, 3 Chains, 500 ms Periode, 5 ms Callback-Zeit):
  - Linear wachsende Latenz bei beiden, aber micro-ROS waechst deutlich schneller (S. 13, Fig. 11).
  - Bei 500 Bytes: PoDS ~58 ms vs. micro-ROS ~158 ms (S. 13).
  - Bei PoDS ist die hoechstpriorisierte Chain nur von ihrer **eigenen** Uebertragungszeit betroffen; bei micro-ROS von der Uebertragungszeit **aller drei Chains** (S. 13).

- **Einfluss der Callback-Ausfuehrungszeit** (10-50 ms, 3 Chains, 500 ms Periode, 100 Byte Pakete):
  - Bei 50 ms Callback-Zeit: PoDS ~151 ms vs. micro-ROS ~222 ms. Latenzluecke waechst progressiv (S. 14, Fig. 12).
  - PoDS profitiert von paralleler DMA-Uebertragung: Wenn Uebertragungszeit < Callback-Zeit, wird sie komplett maskiert (S. 14).

- **Reliable Communication** (3 Chains, 500 ms Periode, 100 Byte, variable Success Probability 0-100%):
  - PoDS konsistent niedrigere und stabilere Latenz (S. 15, Fig. 13, Table 1).
  - STD von PoDS: 0.01-3.84 ms vs. micro-ROS: 0.33-14.70 ms (S. 16, Table 1).
  - Bei 0% Erfolgswahrscheinlichkeit: PoDS AVG 48.97 ms vs. micro-ROS AVG 115.09 ms (S. 16).

### 12. Fazit und Einordnung (S. 17)

- PoDS ist auf der bestehenden micro-ROS-Architektur aufgebaut und kompatibel mit allen unterstuetzten RTOS (S. 17).
- Der ROS 2 Agent beeinflusst die Echtzeitleistung signifikant, da er auf einem Remote-System laeuft (S. 17).
- Zukuenftige Arbeit: Integration von embeddedRTPS zur Eliminierung der ROS 2 Agent-Abhaengigkeit (S. 17).

## Relevanz fuer die Bachelorarbeit

| Aspekt | Relevanz |
|---|---|
| **micro-ROS Architektur** | Beschreibt genau den Software-Stack, der auf dem ESP32 des AMR laeuft: micro-ROS Client Library ueber RCLC mit FreeRTOS als RTOS. |
| **UART Serial Transport** | Der AMR verwendet identische Kommunikation (ESP32 <-> Raspberry Pi ueber UART/Serial). Die UART-Baudrate im Paper (115.200 bps) ist vergleichbar mit der Konfiguration des AMR (115.200 Baud, vgl. platformio.ini). |
| **Callback-Scheduling-Probleme** | Der AMR nutzt zwei FreeRTOS-Tasks auf den ESP32-Kernen (Core 0: micro-ROS, Core 1: PID-Regelung). Die beschriebene Priority Inversion im RCLC Executor betrifft direkt den micro-ROS-Task auf Core 0 (cmd_vel Subscriber + Odometrie Publisher). |
| **Synchrone DMA-Blockierung** | Erklaert potenzielle Latenzprobleme beim Publizieren von Odometrie-Nachrichten (Odometry ist ein grosser Nachrichtentyp > 288 Bytes bei PoseWithCovariance). Waehrend der Uebertragung blockiert der Executor. |
| **Dual-Core-Entkopplung des AMR** | Die Firmware-Architektur des AMR (micro-ROS auf Core 0, PID auf Core 1 mit Mutex) umgeht teilweise das Priority-Inversion-Problem, da die zeitkritische Regelschleife auf einem separaten Kern laeuft und nicht vom RCLC Executor betroffen ist. |
| **PoDS als moegliche Optimierung** | Bei kuenftiger Erweiterung des AMR (mehr Topics, hoehere Frequenzen) koennte PoDS oder ein aehnlicher Ansatz die Echtzeitleistung des micro-ROS-Tasks verbessern. |
| **End-to-End-Latenz-Messung** | Die Methodik (xTaskGetTickCount, Chain-Latenz) koennte zur Validierung der Timing-Anforderungen des AMR eingesetzt werden. |
