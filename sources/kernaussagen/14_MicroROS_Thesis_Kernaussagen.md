# Micro-ROS for Mobile Robotics Systems

## Bibliografische Angaben

- **Autor:** Peter Nguyen
- **Institution:** Maelardalen University (MDU), School of Innovation Design and Engineering, Vaesteaas, Schweden
- **Datum:** 10. Juni 2022
- **Typ:** M.Sc. Thesis (30 ECTS), Engineering - Robotics
- **Betreuer:** Jonas Larsson (MDU), Jon Tjerngren (ABB Corporate Research)
- **Examiner:** Baran Cuerueklue (MDU)

## Zusammenfassung

Die Thesis untersucht die Quality-of-Service (QoS) und Leistungsfaehigkeit von micro-ROS in mobilen Robotik-Systemen am Beispiel von ABBs mobilem YuMi-Prototypen (mYuMi). Drei verschiedene Mikrocontroller werden getestet: STM32F767ZI (Cortex-M7), NodeMCU-32S (ESP32) und Arduino Due (Cortex-M3). Die Kommunikation zwischen micro-ROS und ROS2 wird mittels Ping-Pong-Latenzmessung ueber 2-Stunden-Sessions analysiert, wobei Tracealyzer, Ozone, ros2_tracing und Fast DDS Monitor als Analyse-Tools eingesetzt werden. Ein Prototyp demonstriert micro-ROS im praktischen Einsatz mit einem 1D-Entfernungssensor und einem RC-Servomotor. Die Ergebnisse zeigen, dass micro-ROS auf allen drei MCUs funktioniert, die Stabilitaet mit zunehmender Sendefrequenz steigt, und die RTT-Werte im Bereich von 100-300 ms liegen.

## Kernaussagen

### 1. Forschungsfragen und Ziele (S. 1-2)

Die Thesis verfolgt drei zentrale Forschungsfragen:
- **RQ1:** Welche Limitierungen bestehen bei der Kommunikationsanalyse zwischen micro-ROS und ROS2?
- **RQ2:** Kann aequivalente micro-ROS-Funktionalitaet auf STM32, ESP32 und Arduino-Boards deployed werden?
- **RQ3:** Kann micro-ROS in Bezug auf Stabilitaet und Delay mit ROS2 mithalten, wenn es gemeinsam im Sense-Plan-Act-Prototyp mit mYuMi eingesetzt wird?

### 2. Getestete Mikrocontroller und ihre Eigenschaften (S. 6, 10, 12-13)

| Eigenschaft | STM32F767ZI | NodeMCU-32S (ESP32) | Arduino Due |
|---|---|---|---|
| Prozessor | Cortex-M7 | Xtensa LX6 Dual-Core | Cortex-M3 (SAM3X8E) |
| micro-ROS Integration | STM32CubeMX Utilities | ESP-IDF Component (v4.3) | Arduino Library (PlatformIO) |
| Transport | UART (Serial) | Wi-Fi (UDP) | USB (Serial) |
| RTOS | FreeRTOS | FreeRTOS (optional) | Kein OS |
| Tracing | Tracealyzer (FreeRTOS) | Tracealyzer (FreeRTOS) | Ozone (bare-metal) |
| UDP-Unterstuetzung | Ethernet-Buchse, aber nicht in micro-ROS | Ja (nativ ueber Wi-Fi) | Nein |
| ROS2-Kompilierung | Ja | Ja | Nein |

**ESP32-spezifisch:**
- Verbindet sich ueber Wi-Fi mit UDP zum micro-ROS Agent (S. 13, 16)
- micro-ROS ESP-IDF Component bietet die am weitesten fortgeschrittene Integration (S. 10)
- Hat am wenigsten Hardware-Leistung der drei Boards, aber die meiste Konnektivitaet (S. 10)
- ESP-IDF v4.3 wurde verwendet, mit menuconfig-Konfiguration (S. 13)
- FreeRTOS muss auf Core 0 beschraenkt werden fuer Application Level Tracing (S. 18)

### 3. Testaufbau und Methodik (S. 13-14, 16-18)

**Ping-Pong-Kommunikationstest:**
- Initiator sendet Ping, Empfaenger antwortet mit Pong, Bestaetigung mit Peng
- Erlaubt Messung des Round-Trip-Time (RTT) von beiden Seiten
- Sendefrequenzen: 10 Hz, 12.5 Hz, 16.7 Hz
- Testdauer: 2 Stunden pro Szenario
- 9 verschiedene Szenarien: jede MCU-Kombination bei jeder Frequenz

**Systemarchitektur (S. 16):**
- MCUs verbunden per USB mit Desktop-PC
- Desktop-PC leitet via UDP (netcat + socat) an mYuMi-PC weiter
- mYuMi-PC laeuft ROS2 Galactic mit Ubuntu 20.04
- micro-ROS Agent vermittelt zwischen micro-ROS-Nodes und ROS2-Netzwerk
- QoS-Policy: Best Effort (Sensor-Data-Profil)

### 4. RTT-Messergebnisse: Tracealyzer und Ozone (S. 22, 25, Tabelle 1)

**Durchschnittliche RTT ueber alle Frequenzen (Tabelle 1):**

| MCU | Ping RTT | Pong RTT |
|---|---|---|
| F767ZI (STM32) | 0.245 s | 0.242 s |
| **32S (ESP32)** | **0.129 s** | **0.209 s** |
| Due (Arduino) | 0.234 s | 0.254 s |

**Wesentliche Beobachtungen:**
- **ESP32 (32S) hat die niedrigste Ping-RTT** und den zweitniedrigsten Pong-RTT
- Stabilitaet nimmt mit hoeherer Frequenz zu bei allen MCUs
- Durchschnittliche RTT sinkt mit steigender Frequenz
- F767ZI ist konsistent ueber alle Frequenzen als Sender und Empfaenger
- 32S zeigt stark verringerte Varianz bei hoeheren Frequenzen, sehr niedrige Sende-Durchschnitte
- Due zeigt aehnliche Ergebnisse wie F767ZI, aber ohne Bottleneck bei 16.7 Hz

### 5. ROS2-Subscription-Delay: ros2_tracing (S. 23, 25, Tabelle 2)

**Durchschnittliche Empfangs-Delays (Tabelle 2):**

| MCU | Ping RX | Pong RX | Peng RX |
|---|---|---|---|
| F767ZI | 0.168 s | 0.198 s | 0.153 s |
| 32S (ESP32) | 0.179 s | 0.189 s | 0.168 s |
| Due | 0.172 s | 0.205 s | 0.160 s |

- Peng-Delay ist konsistent am niedrigsten
- Ping-Delay am zweitniedrigsten
- Mehrere Ausreisser im Pong-Delay
- F767ZI zu 32S hat den geringsten kombinierten Subscription-Delay

### 6. DDS-Transmission-Delay: Fast DDS Monitor (S. 24, 25, Tabelle 3)

**Durchschnittliche Sende-Delays (Tabelle 3):**

| MCU | Ping TX | Pong TX | Peng TX |
|---|---|---|---|
| F767ZI | 0.130 s | 0.125 s | 0.123 s |
| 32S (ESP32) | 0.127 s | 0.134 s | 0.121 s |
| Due | 0.142 s | 0.128 s | 0.133 s |

- Ping-, Pong- und Peng-Delays sind sehr aehnlich bei den meisten Ergebnissen
- Frequenzerhoehung tendiert zur Senkung des Durchschnitts
- F767ZI zu 32S hat den niedrigsten Durchschnitt ueber alle Ergebnisse

### 7. Delay-Analyse und Limitierungen (S. 25-27)

Die theoretische Beziehung zwischen den Messwerten:
- `Ping_RTT = Ping_RX + Pong_TX + MCU_TX + MCU_RX + X`
- `Pong_RTT = Pong_RX + Peng_TX + MCU_TX + MCU_RX + X`

**Kritisches Ergebnis:** Die Summe der ROS2-Delays (ros2_tracing + Fast DDS Monitor) ist teilweise groesser als die RTT oder vernachlaessigbar kleiner. Dies deutet auf einen unbekannten Fehler im Messsystem hin, weshalb **keine exakten micro-ROS-Delay-Werte abgeleitet werden koennen** (S. 25).

**Jedoch:** Die RTT ist stabil, wenn die ROS2-Delays stabil sind, was impliziert, dass auch die micro-ROS-Delays stabil sein muessen (S. 25). Die Ergebnisse liefern eine **Obergrenze (Ceiling)** fuer moegliche micro-ROS-Delays.

### 8. micro-ROS Portabilitaet und Flexibilitaet (S. 27-28)

- Der gleiche micro-ROS-Grundaufbau wurde auf alle drei MCUs deployed
- Unterschiede liegen nur in der Transport-Initialisierung (UART, USB, Wi-Fi)
- micro-ROS ist portabel zwischen verschiedenen MCU-Plattformen
- Die meisten ROS2-Systeme mit Mikrocontrollern sollten micro-ROS integrieren koennen
- **Antwort auf RQ2:** Ja, aequivalente micro-ROS-Funktionalitaet laesst sich auf STM32, ESP32 und Arduino deployen, mit unterschiedlichen Transport-Layern

### 9. Prototyp: Sense-Plan-Act mit mYuMi (S. 19-21)

Der Prototyp demonstriert micro-ROS im praktischen Einsatz:
- **1D-Entfernungssensor (SRF04):** Misst Distanz zum Arbeitstisch (1-300 cm)
- **RC-Servomotor (HS-5495BH):** Proof-of-Concept fuer Aktuator-Steuerung ueber micro-ROS
- mYuMi faehrt zur Workstation, streckt Arm aus, passt Saeulenhhohe basierend auf Entfernungsmessung an
- Live-Analyse mit allen Tools waehrend des Prototyp-Betriebs
- **Ergebnis:** Prototyp funktioniert wie erwartet, Live-Analyse zeigt vergleichbare Delay- und Stabilitaetswerte wie die Testbank-Messungen (S. 21, 27)

### 10. Limitierungen von micro-ROS (S. 10, 27)

- Dokumentation fuer micro-ROS ist mangelhaft, wenige wissenschaftliche Arbeiten verfuegbar
- Kein direktes Analyse-Tool fuer micro-ROS verfuegbar - nur indirekte Messung ueber externe Tools
- ros2_tracing kann die DDS-Middleware (RMW) nicht messen
- Fast DDS Monitor misst auf DDS-Ebene, aber eingehende micro-ROS-Daten sind nicht sichtbar
- Sicherheitsfunktionen (DDS-Security, Logging, Parameter-Clients) fehlen in micro-ROS Galactic
- micro-ROS und ROS2 sind beide noch relativ frueh in der Entwicklung

### 11. Transport-Layer-Vergleich (S. 13, 16, 26)

| Transport | MCU | Vorteile | Nachteile |
|---|---|---|---|
| UART (Serial) | F767ZI | Deterministisch, zuverlaessig | Port-Forwarding noetig via netcat/socat |
| Wi-Fi (UDP) | 32S (ESP32) | Direkte Verbindung, kabellos | Variabilere Latenz |
| USB (Serial) | Due | Einfache Einrichtung | Port-Forwarding noetig, kein RTOS |

- F767ZI und Due benoetigen Port-Forwarding (Serial -> UDP -> mYuMi), was zusaetzliche Latenz einfuehrt
- 32S verbindet sich direkt per Wi-Fi zum micro-ROS Agent
- Port-Forwarding-Ergebnisse sind moeglicherweise nicht identisch mit Ethernet oder direktem Serial

## Relevanz fuer die Projektarbeit

### Direkte Relevanz

1. **ESP32 micro-ROS Performance:** Die Thesis liefert die einzige umfassende Latenzmessung fuer ESP32 mit micro-ROS. Die Ping-RTT von 129 ms (Durchschnitt ueber alle Frequenzen) gibt einen realistischen Referenzwert fuer die Kommunikationslatenz in der Projektarbeit. Die Projektarbeit verwendet UART-Transport statt Wi-Fi, was deterministischere Ergebnisse erwarten laesst.

2. **FreeRTOS + micro-ROS auf ESP32:** Die Thesis bestaetigt, dass FreeRTOS und micro-ROS auf dem ESP32 zusammenarbeiten (ESP-IDF v4.3). Die Projektarbeit nutzt ebenfalls FreeRTOS mit Dual-Core-Partitionierung (Core 0: micro-ROS, Core 1: PID-Regelung), was ueber den Ansatz der Thesis hinausgeht.

3. **micro-ROS Agent und Transport:** Die Thesis beschreibt detailliert den micro-ROS Agent als Vermittler zwischen micro-ROS-Nodes und dem ROS2-Netzwerk. Die Projektarbeit verwendet den gleichen Agent-Ansatz ueber UART/Serial Transport statt UDP.

4. **QoS-Einstellungen:** Die Thesis verwendet Best-Effort QoS (Sensor-Data-Profil), was auch fuer die Odometrie-Publikation der Projektarbeit sinnvoll ist, da nur die aktuellsten Daten relevant sind.

5. **Stabilitaet bei hoeheren Frequenzen:** Die Beobachtung, dass die Stabilitaet mit zunehmender Frequenz steigt, ist relevant fuer die 20-Hz-Odometrie-Publishrate der Projektarbeit (hoeher als die getesteten 10-16.7 Hz).

6. **Portabilitaet der micro-ROS-Integration:** Die Bestaetigung, dass micro-ROS auf verschiedenen MCU-Plattformen funktioniert, stuetzt die Wahl des ESP32 fuer die Projektarbeit.

### Indirekte Relevanz

7. **Vergleichsprojekt Phueakthong et al.:** Die Thesis referenziert ein aehnliches Projekt (Raspberry Pi 4 + Pico RP2040 + micro-ROS + Differentialantrieb), das SLAM mit Cartographer und Navigation mit Nav2 implementiert (S. 8). Dies ist ein direktes Vergleichsprojekt zur Projektarbeit.

8. **Analyse-Methodik:** Die Kombination aus MCU-Tracing (Tracealyzer/Ozone) und ROS2-Tracing (ros2_tracing) koennte fuer die Validierung der Projektarbeit uebernommen werden.

### Abgrenzung

- Die Thesis verwendet UDP/Wi-Fi-Transport fuer den ESP32, die Projektarbeit UART/Serial - UART ist deterministischer und hat weniger Overhead
- Die Thesis testet keine Dual-Core-Nutzung des ESP32, waehrend die Projektarbeit Core 0 und Core 1 gezielt partitioniert
- Die Ping-Pong-Messung ist ein synthetischer Benchmark; die Projektarbeit hat reale cmd_vel/Odometry-Kommunikation
- Die Testfrequenzen (10-16.7 Hz) sind niedriger als die 20-Hz-Odometrie und 50-Hz-PID-Regelung der Projektarbeit
- Die Thesis konnte keine exakten micro-ROS-Delay-Werte ableiten - nur Obergrenzen und Stabilitaetsaussagen
