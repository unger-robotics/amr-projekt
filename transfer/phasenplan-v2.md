# Phasenplan v2.2 – Ausbau nach VDI 2206 in zwei Makrozyklen

## Kopfbereich

| Feld | Inhalt |
| --- | --- |
| Projekt | Autonomer Mobiler Roboter (AMR) – Lernplattform fuer autonomes Fahren (Kfz) |
| Dokumenttyp | Phasenplan (Ausbauplan) nach VDI 2206, zwei Makrozyklen |
| Version | 2.2 (Entwurf) |
| Datum | 2026-09-03 |
| Autor | Jan (Entwurf erstellt mit KI-Assistent, Freigabe offen) |
| Ersetzt | Phasenplan v2.1 und v2.0 (beide 2026-09-03) und Phasenplan v1 (linearer Ausbauplan K0–K10, Stand nach K1) |
| Bezugsdokumente | Anforderungsliste L1 v1.0 (2026-03-22), docs/architecture/communication.md, docs/architecture/signalbedarf.md (K1), planung/roadmap.md, docs/plan/arbeitsplan-k0-k2-s-a.md, validation/P-CAN2/ (Teil A, 2026-09-03) |
| Projektfragen | PF1 (Echtzeitarchitektur), PF2 (Navigationsgenauigkeit), PF3 (Bedien- und Leitstandsebene, intelligente Interaktion); Zuordnung fuer Makrozyklus 2 offen (D-04) |

## 1 Ziel und Abgrenzung

Der Plan dient zwei gleichrangigen Zielen:

- **Z1 – Realistische Fahrzeug-E/E-Architektur.** Raspberry Pi 5 als ADAS-Zentralrechner, Fahrkern (Drive-ECU) und Sensor- und Sicherheitsbasis (Sensor-ECU) als ECUs am CAN-Bus (1 Mbit/s). CAN wird Runtime-Pfad, micro-ROS/UART bleibt Service-Pfad (Flash, Debug).
- **Z2 – Lernplattform autonomes Fahren mit Winner-Funktionskette.** Environment → Sensors → Sensor Preprocessing → Perception → Localization → Environment Model → Prediction → Behavior → Trajectory Planning → Trajectory Control → Actuators → Vehicle (Rueckkopplung).

**Daten.** Plan v1 ordnet 7 von 11 Paketen (K0–K6) dem Ziel Z1 zu und 4 Pakete (K7–K10) dem Ziel Z2. K8 und K9 buendeln je zwei bis drei Winner-Stufen. K7 haengt in v1 hinter K6.

**Regel.** Nach VDI 2206 wird jeder Entwicklungsdurchlauf als eigener Makrozyklus mit eigenen Anforderungen, Systementwurf, Integration und Eigenschaftsabsicherung gefuehrt. Ein Ergebnis ist verteidigbar, wenn sein Makrozyklus geschlossen ist.

**Schluss.** Z2 ist in v1 ein Anhaengsel von Z1: Es startet erst, wenn die Kommunikation vollstaendig umgebaut ist, obwohl die Winner-Kette vollstaendig auf dem Pi 5 laeuft und nur den Kommandovertrag aus K2 benoetigt.

**Konsequenz.** v2 fuehrt zwei Makrozyklen, die ab K2 parallel laufen. K-Nummern aus v1 bleiben erhalten (Rueckverfolgbarkeit zu K1). Ergaenzungen erhalten Suffixe (K8a, K8b), Untersuchungen ohne Umbau erhalten S-Nummern (Spike).

Nicht Teil dieses Dokuments: Ergebnisse von K0 und K1 (unveraendert gueltig), Inhalt der DBC (K2-Liefergegenstand), Zeitplanung in Kalenderwochen.

### 1.1 Aenderungen gegenueber v1

| Nr. | v1 | v2 | Grund |
| --- | --- | --- | --- |
| 1 | Ein linearer Strang K0–K10 | Zwei Makrozyklen: MZ1 (E/E-Architektur, K0–K6) und MZ2 (Winner-Kette, K7–K10) | Jeder Zyklus ist einzeln abschliessbar und verteidigbar |
| 2 | K7 nach K6 | K7 nach K2 (Vertrag), parallel zu K3–K6 | Winner-Kette liegt vollstaendig auf dem Pi 5; keine technische Abhaengigkeit von CAN |
| 3 | K8, K9 als je ein Paket | K8a/K8b, K9a/K9b/K9c | Umfang je Winner-Stufe groesser als ein CAN-Paket |
| 4 | BA-01/BA-02 als Gate vor K4 | Diagnose S-A sofort (parallel K2), Behebung als Gate G1 vor K4 | Ursache kann Physical Layer aendern und damit das DBC-Layout; Diagnose verletzt die Baseline nicht |
| 5 | BA-03 ohne Zuordnung | BA-03 → K3 (FA-19, genau eine Kommandoquelle) | Voraussetzung fuer Shadow Mode und fuer den Ketten-Ausgang in MZ2 |
| 6 | K10 am Ende ohne Vorlauf | S-B (Radar-Rohdaten) parallel zu K3 | Hoechstes Hardware-Risiko frueh sichtbar; klaert Grenze Sensor Preprocessing (ECU) vs. Perception (Pi) |
| 7 | VCU_DRIVE_COMMAND mit alive_counter | zusaetzlich crc8, Sendeoffsets je Nachricht | E2E-Schutz nach Kfz-Muster; Burst-Vermeidung ist DBC-Auslegung, nicht Firmware |
| 8 | Abnahmekriterien qualitativ | Schwellwerte je Paket (Tabellen unten) | Anforderungsliste L1 verlangt Messgroesse + Schwellwert + Nachweis |

### 1.2 Aenderungen v2.0 → v2.1 (Entscheidungen vom 2026-09-03)

| Nr. | v2.0 | v2.1 | Grund |
| --- | --- | --- | --- |
| 1 | D-01 offen (vier Optionen inkl. CAN FD) | Entschieden: MCP2518FD-Breakout am Pi 5, klassisches CAN 2.0B | Radar-Objektliste ist ein Burst von bis zu 8 Frames; MCP2515 mit 2 RX-Puffern strukturell zu klein. CAN FD entfaellt: TWAI auf dem ESP32-S3 spricht nur CAN 2.0 |
| 2 | D-02 offen (Sensor-ECU oder Pi) | Entschieden: dritter XIAO ESP32-S3 als Radar-ECU, reiner CAN-Knoten | Drive-ECU 11/11 Pins belegt, Sensor-ECU mindestens 7/11; SPI + IRQ fuer den BGT60TR13C brauchen 5. Kein USB-Port noetig |
| 3 | HAT-Formfaktor moeglich | Nur Breakout-Module an Jumper-Leitungen | Hailo-8L belegt M.2/PCIe; alle vier USB-Ports belegt |
| 4 | S-A entscheidet D-01 | S-A = Beweissicherung vorher/nachher (P-CAN2) | Vorher-Nachher-Nachweis fuer BA-01/BA-02 statt Vermutung |
| 5 | G0 mit Layout-Vorbehalt | G0 = T-09 + dokumentierte Vorher-Messung | Kein Physical-Layer-Wechsel mehr offen |
| 6 | Ein Kommandoframe (VCU_DRIVE_COMMAND) | Zweiter Kommandoframe VCU_SENSOR_COMMAND (Pan, Tilt, Servo-Speed) | /servo_cmd laeuft heute ueber micro-ROS; nach K6 sonst ohne Pfad |
| 7 | — | BA-05 Steuerungsverlust bei aktiver Objekterkennung; NFA-15, SIA-15 | Alive-Counter darf nicht aus der Bedien- und Leitstandsebene kommen |
| 8 | FA-24 Rate >= 10 Hz | >= 5 Hz | RPLIDAR A1 liefert 7,7 Hz (NFA-02) — 10 Hz waren nicht erreichbar |
| 9 | — | Abschnitt 2.4 Hardware-Einsatzpunkte | Start ohne Radar und dritten ESP32 moeglich; MCP2518FD ist die einzige Beschaffung vor G1 |

### 1.3 Aenderungen v2.1 → v2.2 (Messergebnis S-A vorher, 2026-09-03)

| Nr. | v2.1 | v2.2 | Grund |
| --- | --- | --- | --- |
| 1 | D-01 entschieden, Nachweis offen | D-01 durch S-A vorher bestaetigt (Fall 1) | rx_over_errors Delta 6674/6001 je 10 min, bus_error 0, Verlust auf dem dritten Frame im Burst |
| 2 | BA-01 = 4,58 % (K0) | BA-01 = 21,5 % (A1) / 27,4 % (A2) auf 0x200; K0-Wert war untererfasst | Messung am Bus statt ueber ROS; Referenz fuer den Nachher-Nachweis ist jetzt Teil A |
| 3 | BA-02 = "steigende rx_errors" | BA-02 = RX-Ueberlauf (rx_errors == rx_over_errors); mit BA-01 ein Befund | Zaehler identisch, Bus-Fehler 0 |
| 4 | Zykluszeit 0x200/0x201 = 50 ms | 40 ms (2 Ticks des 50-Hz-Reglers, 25 Hz) | Fahrkern sendet tick-quantisiert im 40/60-ms-Wechsel; 50 ms sind 2,5 Ticks und nicht einhaltbar |
| 5 | — | Regel: Zykluszeiten in der DBC sind ganzzahlige Vielfache des Sender-Ticks; T-09 prueft das | DBC darf keinen Takt versprechen, den die Firmware nicht halten kann |
| 6 | MCP2518FD "zu beschaffen" | 1 Modul, nur am Pi; ESP32 bleiben bei TWAI + SN65HVD230 | Ueberlauf nur am Pi-Empfaenger; Pinbudget und Bestandsfirmware verbieten SPI-Controller an den ECUs |

## 2 Begriffe, Annahmen, Randbedingungen

### 2.1 Begriffe

| Begriff | Bedeutung in diesem Dokument |
| --- | --- |
| Makrozyklus (MZ) | Ein vollstaendiger V-Durchlauf nach VDI 2206: Anforderungen → Entwurf → Integration → Eigenschaftsabsicherung |
| Paket (K) | Abgeschlossenes Arbeitspaket mit Eingangsbedingung, Liefergegenstand, Anforderungen, Testfaellen und Ausgangsbedingung |
| Spike (S) | Zeitlich begrenzte Untersuchung ohne Aenderung am Fahrbetrieb; Ergebnis ist eine Entscheidung (D-xx), kein Produktcode |
| Gate (G) | Pruefpunkt mit messbarem Kriterium; nicht bestanden = naechstes Paket blockiert |
| Vertrag | amr_vehicle.dbc plus dokumentierte Semantik von VCU_DRIVE_COMMAND und VCU_SENSOR_COMMAND (Einheiten, Wertebereiche, Timeout, Degraded Mode). Einzige Schnittstelle zwischen MZ1 und MZ2 |
| Shadow Mode | Neuer Pfad laeuft mit, wird verglichen, greift nicht in den Fahrbetrieb ein |
| Umschaltpunkt | Zeitpunkt, an dem MZ2 seinen Ausgang von micro-ROS/cmd_vel auf VCU_DRIVE_COMMAND ueber CAN umstellt (= Abschluss K5) |
| Tick | Ein Regelzyklus des Fahrkerns: 20 ms bei 50 Hz (NFA-01) |
| E2E | Ende-zu-Ende-Schutz einer Botschaft nach Muster AUTOSAR E2E Profil 1: CRC-8, Alive Counter (4 Bit), Data-ID |

### 2.2 Annahmen (zu pruefen beim Merge)

| ID | Annahme | Folge bei Nichtzutreffen |
| --- | --- | --- |
| A1 | docs/architecture/signalbedarf.md (K1) enthaelt Signalliste, Betriebsmodi und Safety-Regeln, aber keine numerischen Latenz- und Timeout-Vorgaben fuer den CAN-Kommandopfad | Falls vorhanden: Werte aus K1 ersetzen die Vorschlagswerte in Abschnitt 4 |
| A2 | P-CAN1 = passive CAN-Messung aus K0, P-CAN2 = naechstes Messprotokoll der CAN-Reihe (Plan v1: "P-CAN2 vorbereiten") | Protokoll-IDs anpassen |
| A3 | Neue Anforderungs- und Testfall-IDs setzen die Reihen der Anforderungsliste L1 fort (FA-18 ff., NFA-13 ff., SA-10 ff., SIA-11 ff., T-09 ff., IT-10 ff., SV-04 ff.). T-09 = can_dbc_check ist aus Plan v1 bekannt und passt in die Reihe | Hat K1 bereits IDs vergeben, gelten die K1-IDs; hier vergebene IDs werden umbenannt (D-06) |
| A4 | Winner-Funktionskette nach Winner et al., Handbuch Assistiertes und Automatisiertes Fahren, 4. Aufl. 2024. Kapitelzuordnung nicht verifiziert (Volltext lag bei Erstellung nicht vor) | Kapitelangaben beim Exzerpt nachtragen |
| A5 | MCP2518FD-Tausch am Pi 5 erfolgt in K3 nach der S-A-Vorher-Messung; Verdrahtung wie bisher an SPI0 | Verschiebt sich der Tausch, verschiebt sich G1 |
| A6 | Pinbelegung der beiden XIAO wie in 2.4 gezaehlt (Funktionszaehlung aus der Doku; exakte GPIO-Nummern stehen in config_drive.h / config_sensors.h) | Freie Pins auf der Sensor-ECU aendern nichts an D-02 — die Radar-ECU bleibt eigener Knoten |

### 2.3 Randbedingungen (aus Anforderungsliste L1, unveraendert gueltig)

- NFA-01: Fahrkern 50 Hz, Jitter < 2 ms.
- NFA-03: Odometrie >= 10 Hz (Soll 20 Hz).
- NFA-10: Datenverlust auf micro-ROS-Strecke < 0,1 % — Schwellwert wird fuer CAN uebernommen (NFA-13).
- SA-03: CAN 1 Mbit/s, ISO 11898, SN65HVD230.
- SIA-03: CAN-Direktpfad Cliff < 20 ms ohne ROS 2 — bleibt in allen Paketen unangetastet.
- SIA-04: Failsafe-Timeout 500 ms → Motorenstopp — bleibt uebergeordneter Failsafe.
- SIA-05: Watchdog-Alive-Counter, 50 Zyklen → Verbindungsverlust.
- Keine Fahrbewegung in K2 und in allen Spikes.
- Alle vier USB-Ports des Pi 5 sind belegt (RPLIDAR A1, ReSpeaker, 2x XIAO). Kein weiterer USB-Knoten.
- Hailo-8L belegt M.2/PCIe; HAT-Formfaktor am Pi 5 nicht nutzbar. CAN-Controller als Breakout an SPI0 (Jumper-Leitungen), wie bisher der MCP2515.
- TWAI (ESP32-S3) spricht ausschliesslich CAN 2.0; CAN FD ist keine Option.
- Servos MG996R haben eine eigene Versorgung; der Servoausfall BA-05 ist kein Stromproblem.

### 2.4 Hardware-Einsatzpunkte

Frage: Womit kann gestartet werden, was wird wann gebraucht?

| Hardware | Status | Benoetigt ab | Fuer | Ohne sie moeglich |
| --- | --- | --- | --- | --- |
| Bestand (Pi 5, 2x XIAO, MCP2515, 2x SN65HVD230) | vorhanden | — | K2, S-A vorher, K7 | — |
| MCP2518FD-Breakout (z. B. Soldered 333020, Transceiver ATA6563) — genau 1 Stueck, nur am Pi | bestaetigt durch S-A vorher (Fall 1); zu beschaffen, ca. 16–23 EUR; Transceiver 3,3-V-tauglich und Quarzfrequenz vor Kauf pruefen | K3 (Vorher-Messung liegt vor), spaetestens G1 | S-A nachher, NFA-13, K4–K6, Radar-Bursts in K10 | K2, K7, S-A vorher |
| 5-V-Abgriff fuer die XIAOs (statt Pi-USB) | zu verdrahten | K6 | USB nur Service | K2–K5 |
| Dritter XIAO ESP32-S3 + SN65HVD230 | zu beschaffen, ca. 10 EUR | S-B | Radar-ECU | K2–K9 komplett |
| BGT60TR13C-Shield (SHIELDBGT60TR13CTOBO1) | offen; vor Kauf AN600 lesen: Board-to-Board-Stecker fuer Baseboard MCU7, Versorgungsfreigabe, IO-Pegel; Alternative DEMO-Kit mit Baseboard und Radar Fusion GUI | S-B | K10 | K2–K9 komplett; Kette laeuft mit Radar-Simulator |
| Eigene Servoversorgung | vorhanden | — | — | — |

Pinbudget XIAO ESP32-S3 (11 GPIO am Header, Funktionszaehlung aus der Doku, A6):

| Knoten | Belegung | Pins |
| --- | --- | --- |
| Fahrkern (Drive-ECU) | MDD3A 2x PWM + 2x DIR, 2 Encoder A/B, TWAI TX/RX, LED-MOSFET | 11/11 |
| Sensor- und Sicherheitsbasis (Sensor-ECU) | I2C SDA/SCL (MPU6050, INA260, PCA9685 → 2x MG996R), HC-SR04 Trig/Echo, MH-B Cliff, TWAI TX/RX | >= 7/11 |
| Radar-ECU (neu) | SPI SCK/MISO/MOSI/CS + IRQ, TWAI TX/RX, optional Debug-UART TX/RX (D-08) | 7/11 (9 mit UART) |

Schluss: K2, S-A (vorher) und K7 starten mit dem Bestand. Der MCP2518FD ist die einzige Beschaffung vor G1. Radar und dritter XIAO werden erst fuer S-B/K10 gebraucht; MZ1 und K7–K9 laufen vollstaendig ohne sie.

## 3 Gesamtbild

```
MZ1 E/E-Architektur (Z1)          MZ2 Winner-Funktionskette (Z2)
------------------------------    ------------------------------
K0 Baseline                 [x]
K1 Anforderungen/Architektur[x]
K2 DBC (4 Nodes) + E2E  ----+---> Vertrag: amr_vehicle.dbc +
 |- S-A vorher (MCP2515)    |     VCU_DRIVE/SENSOR_COMMAND-Semantik
 G0 T-09 + S-A vorher       |
K3 Sensor-ECU ueber CAN     |     K7  Ketten-Skelett (Anforderungen,
 |- MCP2518FD-Tausch        |         Schnittstellen, Simulator,
 |- S-A nachher, Abtastpunkt|         Durchstich, Latenzbudget)
 |- BA-03 Arbiter           |     K8a Perception
 |- BA-04 Bodenkontakt      |     K8b Environment Model
 |- BA-05 Gateway-Prozess   |     K9a Prediction
 G1 NFA-13 + NFA-15               K9b Behavior
K4 Shadow Mode                    K9c Trajectory Planning/Control (Nav2)
 G2 Shadow bestanden
K5 CAN_PRIMARY  ==================> Umschaltpunkt: MZ2-Ausgang USB -> CAN
 G3 Regression ueber CAN
K6 CAN = Runtime, USB = Service   S-B Radar-Spike (3. XIAO, jederzeit)
 SV-04 Typgenehmigung ueber CAN   K10 Radar-ECU (3. CAN-Knoten, G4)
```

MZ2 laeuft bis zum Umschaltpunkt ueber den bestehenden micro-ROS-Pfad; der Ketten-Ausgang wird als eigene Kommandoquelle in den Arbiter (FA-19) eingespeist. Nach K5 wechselt nur die Transportschicht; die Kette kennt ausschliesslich den Vertrag.

## 4 Makrozyklus 1 – E/E-Architektur (K0–K6)

Spalten der Anforderungstabellen entsprechen der Anforderungsliste L1. Werte mit Kennzeichnung *(Vorschlag)* sind hergeleitet, nicht aus K1 uebernommen (A1). Pruefebenen: R1 Komponente (Pruefstandtest, T-xx), R2 Integration (Fahrversuch, IT-xx), R3 System (Typgenehmigung, SV-xx).

### K0 – Baseline (abgeschlossen)

| Feld | Inhalt |
| --- | --- |
| Liefergegenstand | USB/micro-ROS-Referenzpfad dokumentiert; ROS-2-Topic-Raten und TF-Baum erfasst; CAN passiv vermessen (P-CAN1, A2); Werkzeug baseline_snapshot |
| Befunde | BA-01 0x200-Frameverlust: 4,58 % (K0); S-A vorher 2026-09-03: 21,5 % (A1) / 27,4 % (A2), dt max 640 ms — K0-Wert untererfasst; BA-02 rx_errors == rx_over_errors (Delta 6674/6001 je 10 min), bus_error 0 → RX-Ueberlauf MCP2515, mit BA-01 ein Befund; BA-03 zwei /cmd_vel-Publisher; BA-04 /cliff waehrend K0 dauerhaft true; BA-05 (nachgetragen 2026-09-03) Steuerungsverlust (Servo, ggf. Fahrbetrieb) bei aktiver Objekterkennung in der Bedien- und Leitstandsebene — Servoversorgung eigenstaendig, Ursache im Pi-Pfad vermutet (D-09) |
| Zuordnung der Befunde in v2 | BA-01/BA-02 → S-A (Vorher-Nachher-Nachweis), G1 (NFA-13); BA-03 → K3 (FA-19); BA-04 → K3 (Pruefung mit Bodenkontakt, T-05); BA-05 → K3 (NFA-15), K4 (SIA-15), G1 |

### K1 – Anforderungen und Zielarchitektur (abgeschlossen)

| Feld | Inhalt |
| --- | --- |
| Liefergegenstand | Zielarchitektur (Pi 5 – Vehicle CAN Gateway – CAN 1 Mbit/s – Drive-ECU/Sensor-ECU); Funktionsverteilung; Betriebsmodi; Safety-Regeln; Signalbedarf (signalbedarf.md); Zuordnung Anforderung ↔ Test |
| In v2 ergaenzt | Nichts an K1 selbst. K7 wiederholt den K1-Schritt fuer MZ2 (Anforderungen und Schnittstellen der Winner-Kette) |

### K2 – DBC (vier Nodes), E2E, Sendeoffsets, cantools

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | signalbedarf.md liegt vor; K0-Snapshot reproduzierbar |
| Leitfrage | Wie werden die in K1 definierten Fahrzeugsignale eindeutig und maschinenlesbar auf CAN abgebildet? |
| Liefergegenstand | amr_vehicle.dbc (Single Source of Truth) mit vier Nodes PI_VCU, DRIVE_ECU, SENSOR_ECU, RADAR_ECU: alle 13 Bestands-IDs (0x110, 0x120, 0x130, 0x131, 0x140, 0x141, 0x150, 0x1F0, 0x200, 0x201, 0x210, 0x220, 0x2F0) mit Sender, Empfaenger, Bitposition, Datentyp, Skalierung, Einheit, Zykluszeit (GenMsgCycleTime) und Sendeoffset (GenMsgStartDelayTime) — Zykluszeiten als ganzzahlige Vielfache des Sender-Ticks (DRIVE_ECU 20 ms): 0x200/0x201 = 40 ms (25 Hz, erfuellt NFA-03 Soll 20 Hz) statt nominell 50 ms, Begruendung S-A vorher; VCU_DRIVE_COMMAND (target_velocity, target_yaw_rate, enable, operating_mode, alive_counter, crc8) und VCU_SENSOR_COMMAND (pan, tilt, servo_speed, alive_counter, crc8) spezifiziert (IDs aus K1/Bestand), noch nicht wirksam; Radar-Bereich 0x300–0x3F0 reserviert (Objektframe je Objekt: range uint16 mm, angle int16 0,01 Grad, v_radial int16 cm/s, amplitude uint8, object_id uint8; 0x3F0 Heartbeat) *(Vorschlag, folgt dem Bestandsschema 0x1xx/0x2xx)*; ID-Regel: Kommandoframes numerisch ueber 0x120 und 0x141, damit Cliff und Shutdown die Arbitrierung gewinnen; cantools-Integration; generierte Definitionen fuer ESP32/C++ und Pi/Python; T-09 can_dbc_check; P-CAN2 vorbereitet. Kuer: Bestandsframes von float32 auf skalierte Integer umpacken (Kfz-Praxis, weniger Frames je Tick) — mit MCP2518FD nicht mehr erforderlich |
| Noch nicht | Fahrbefehle ueber CAN aktivieren; USB abschalten; Firmwarelogik aendern; Fahrbewegung; Hardwarezustaende annehmen |
| Ausgangsbedingung | T-09 bestanden; S-A-Vorher-Messung dokumentiert (G0) → DBC-Freeze mit Git-Tag |

Anforderungen K2:

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SA-10 (neu) | PF1 | MUSS | amr_vehicle.dbc bildet alle CAN-Nachrichten des Bestands, beide Kommandoframes und die Radar-Reservierung vollstaendig ab (vier Nodes) | Anzahl abgebildeter IDs, Roundtrip | 13/13 Bestands-IDs + 2 Kommandos + Radar-Platzhalter 0x300/0x3F0; Encode→Decode ohne Abweichung; keine Bitueberlappung | CAN-Datenbank (DBC) des OEM | signalbedarf.md, config_drive.h, config_sensors.h | T-09 (can_dbc_check) |
| SA-11 (neu) | PF1 | MUSS | VCU_DRIVE_COMMAND traegt target_velocity, target_yaw_rate, enable, operating_mode, alive_counter, crc8 | Signalliste, Wertebereiche | Einheiten m/s und rad/s mit Skalierung aus signalbedarf.md; alive_counter 4 Bit; crc8 ueber Nutzdaten + Data-ID | E2E-Protection (AUTOSAR E2E Profil 1) | signalbedarf.md | T-09 |
| SA-15 (neu) | PF1 | MUSS | VCU_SENSOR_COMMAND traegt pan, tilt, servo_speed, alive_counter, crc8 (Ersatz fuer /servo_cmd und den Servo-Anteil von /hardware_cmd nach K6) | Signalliste, Wertebereiche | Winkel 0–180 Grad in 0,1-Grad-Schritten *(Vorschlag)*; E2E wie SA-11 | Karosserie-Steuergeraete-Kommando (LIN/CAN) | robot_parameters.md (amr::servo), SA-11 | T-09 |
| SA-12 (neu) | PF1 | SOLL | Jede zyklische Nachricht hat Zykluszeit und Sendeoffset in der DBC | Frames je Sender je Zeitfenster | Ein Sender sendet je Tick maximal 2 Frames back-to-back *(Vorschlag; wirkt nur innerhalb eines Senders — die ECU-Takte sind unsynchronisiert)* | Netzwerkauslegung (Sendeplan) | S-A, Datenblaetter MCP2515 (2 RX-Puffer) und MCP2518FD (31 FIFOs) | T-09 (Pruefung Attribute), IT-08 (erweitert) |
| NFA-14 (neu) | PF1 | SOLL | Buslast laesst Reserve fuer Objektlisten aus MZ2 | Buslast bei 1 Mbit/s | < 30 % *(Auslegungs-Faustregel klassisches CAN, keine Norm)* | Buslast-Auslegung CAN | Berechnung aus DBC (Frames/s x Bits/Frame, 111–135 Bit je 8-Byte-Frame) | T-09 (Berechnung), IT-08 (Messung) |

T-09 can_dbc_check (R1, Pruefstandtest): DBC syntaktisch gueltig (cantools load); alle erwarteten IDs vorhanden; Encode→Decode-Roundtrip je Nachricht; keine Bitueberlappung; Skalierungen/Offsets korrekt; DBC und generierte Softwaredefinitionen konsistent; Zykluszeit und Sendeoffset je zyklischer Nachricht gesetzt; Zykluszeit jeder DRIVE_ECU-Nachricht ganzzahliges Vielfaches von 20 ms; rechnerische Buslast ausgegeben.

### S-A – Beweissicherung BA-01/BA-02 (Spike: vorher in K2, nachher in K3)

| Feld | Inhalt |
| --- | --- |
| Zweck | Vorher-Nachher-Nachweis fuer den Controllertausch am Pi 5. Keine Entscheidung mehr (D-01 ist entschieden), sondern Messprotokoll P-CAN2 |
| Vorher (MCP2515, parallel zu K2) | (1) /sys/class/net/can0/statistics/rx_over_errors und ip -details -statistics link show can0 (Bus-Error-Zaehler, Zustand) ueber 10 min bei Bestandslast; (2) candump mit Zeitstempeln, Abstandsverteilung der Frames je Sender (Burst 0x130/0x131 gegen 0x200/0x201?); (3) Widerstand CAN_H–CAN_L stromlos: Soll 60 Ohm (genau zwei Abschluesse); (4) Abtastpunkt Pi-Seite lesen (ip -details): Linux-Default bei 1 Mbit/s 75 %, TWAI_TIMING_CONFIG_1MBITS 80 % |
| Regel | rx_over_errors steigt, Bus-Error-Zaehler nicht → Empfaengerseite (2 RX-Puffer, Host-Latenz); Bus-Error-Zaehler steigt → physikalische Schicht (Abschluss, Abtastpunkt, Leitung). Beides wird protokolliert |
| Ergebnis vorher (2026-09-03, P-CAN2 Teil A) | Profil A1 (ohne Objekterkennung): rx_over_errors Delta 6674 = rx_errors Delta, bus_error 0, arbitration_lost 0; Verlust 0x200 21,51 %, 0x220 6,33 %, 0x131 0,77 %, 0x210 0,48 %, uebrige 0 %; 0x200 dt max 640 ms. Profil A2 (mit Objekterkennung): rx_over_errors Delta 6001, bus_error 0; Verlust 0x200 27,35 %, uebrige 0 %. Gesamtverlust 3221 bzw. 3282 von 116 400 Frames; Buslast 1,75 %; Bursts >= 3 Frames/1000 us: 16 101 bzw. 13 833, Verlust auf dem jeweils dritten Frame (0x200 hinter 0x130/0x131 bzw. 0x210/0x220). Schluss: Fall 1 — RX-Ueberlauf des MCP2515 am Pi, physikalische Schicht sauber. Host-Last verschiebt den Verlust nur (A2: alles auf 0x200), aendert die Summe nicht. Nebenbefund: 0x200/0x201 kommen tick-quantisiert im 40/60-ms-Wechsel (Median 59,5 ms bei 12 000 Frames/600 s) statt mit 50 ms. Offen im Protokoll: V4 (Widerstand CAN_H–CAN_L), Bit-Timing aus meta.txt |
| Nachher (MCP2518FD, in K3) | Identische Messung (1)–(2) nach dem Tausch, Profile A1 und A2, Abtastpunkt auf 80 % gesetzt (sample-point 0.8). Abnahme NFA-13: 0x200 < 0,1 % in beiden Profilen, rx_over_errors Delta 0, bus_error Delta 0 |
| Ergebnis | P-CAN2 mit beiden Messreihen; Eingang fuer NFA-13 (G1) |
| Nicht erlaubt | Firmware-Aenderung, Fahrbewegung; Verkabelung nur beim Controllertausch selbst |

### G0 – K2-Freeze

DBC wird getaggt, sobald T-09 bestanden ist und die S-A-Vorher-Messung im P-CAN2 dokumentiert ist. Kein Layout-Vorbehalt: D-01 ist entschieden (MCP2518FD, klassisches CAN 2.0B), CAN FD ist mit TWAI auf dem ESP32-S3 nicht moeglich. Der Tag wartet nicht auf den Controllertausch.

### K3 – Sensor-ECU ueber CAN, Controllertausch, Back-to-Back, Kommandoquelle, BA-05

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | G0 bestanden |
| Liefergegenstand | MCP2518FD-Breakout am Pi 5 an SPI0 (dieselben sieben Leitungen wie der MCP2515; config.txt: dtoverlay=mcp251xfd,spi0-0,interrupt=<GPIO>,oscillator=<Hz vom Modul>; ip link set can0 up type can bitrate 1000000 sample-point 0.8; Terminierungs-Jumper nur am physischen Busende); S-A-Nachher-Messung; Knoten vehicle_can_gateway (Pi 5, SocketCAN → ROS 2) als eigener Prozess mit erhoehter Prioritaet (nice/chrt) fuer die Empfangsrichtung Sensor-ECU; Back-to-Back-Vergleich CAN vs. micro-ROS je Signal; Heartbeat-Ueberwachung 0x1F0/0x2F0 am Pi; Arbiter fuer /cmd_vel (twist_mux, ROS 2 Humble) mit Prioritaeten Sicherheitslogik > Joystick > Nav2 > automatisierte Kette; Pruefung BA-04 mit Raedern am Boden; BA-05 mit der Diagnoseleiter unten eingegrenzt und behoben |
| Noch nicht | Fahrbefehle ueber CAN; micro-ROS als Sensorpfad abschalten |
| Ausgangsbedingung | IT-10, IT-11 und IT-09 (erweitert) bestanden; BA-04 geklaert; S-A nachher im P-CAN2 |

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-18 (neu) | PF1 | MUSS | Alle Signale der Sensor- und Sicherheitsbasis (0x110–0x1F0) erreichen den Pi 5 ueber CAN und stimmen mit dem micro-ROS-Pfad ueberein | Wertabweichung, Zeitversatz je Signal | Abweichung <= 1 Quantisierungsschritt der DBC-Skalierung; Zeitversatz <= 1 Sendezyklus der jeweiligen Nachricht | Sensor-ECU am Fahrzeugbus | amr_vehicle.dbc, vehicle_can_gateway | IT-10 (neu, can_b2b_sensor_test) |
| FA-19 (neu) | PF1 | MUSS | Zur Laufzeit existiert genau eine wirksame Kommandoquelle fuer den Fahrkern (Arbiter) | Anzahl Publisher auf dem Arbiter-Ausgang; Prioritaetsverhalten | 1 Publisher; Sicherheitslogik setzt sich in 100/100 Faellen gegen Joystick und Nav2 durch | Gateway-Arbitrierung / Fahrpedal vs. ACC | BA-03, twist_mux-Konfiguration | IT-11 (neu, cmd_source_test) |
| SIA-11 (neu) | PF1 | MUSS | Pi 5 erkennt Heartbeat-Ausfall einer ECU | Fehlende Heartbeat-Zyklen bis Meldung | <= 3 Zyklen *(Vorschlag; Zykluszeit aus DBC)* → Zustand ECU_LOST im Gateway | Steuergeraete-Ausfallerkennung | 0x1F0, 0x2F0, amr_vehicle.dbc | IT-10 |
| NFA-15 (neu) | PF1 | MUSS | Steuerpfad (Joystick, Servo, Deadman) haelt die FA-13-Schwellwerte auch unter Volllast der Bedien- und Leitstandsebene (Objekterkennung, MJPEG mit Overlay, Gemini) | Befehlslatenz, Deadman-Rate, /servo_cmd-Ankunftsrate an der MCU | Latenz < 300 ms; Deadman >= 5 Hz ohne Luecke > 500 ms; /servo_cmd 10/10 Hz ueber 10 min bei aktiver Detektion (BA-05) | Trennung Infotainment / Fahrzeugbus | BA-05, FA-13, NFA-09 | IT-09 (dashboard_latency_test, erweitert um Lastprofil Objekterkennung) |
| BA-04 | PF1 | — | /cliff mit Bodenkontakt false, ohne Bodenkontakt true | Cliff-Status | 0 Fehlalarme in 10 min Standbetrieb mit Bodenkontakt | AEB-Fehlausloesung | T-05 (sensor_test) | T-05 |

BA-05 – Diagnoseleiter (Fehler mit aktiver Objekterkennung provozieren, dann messen; Ergebnis entscheidet D-09):

1. `ros2 topic hz /servo_cmd` — kommt es mit ca. 10 Hz an, liegt die Ursache hinter der Bridge (Agent, Seriell, MCU); bleibt es stehen, davor (Bridge, WebSocket, Browser).
2. `ros2 topic hz /imu` und parallel `candump can0,1F0:7FF` — bricht /imu ein, waehrend der CAN-Heartbeat weiterlaeuft, ist die micro-ROS-Session gestoert und die MCU lebt.
3. `top -H` am Host: CPU je Thread fuer hailo_runner, micro_ros_agent, dashboard_bridge; Rate des Deadman-Topics — unter 5 Hz erklaert die SIA-04-Ausloesung.

Behebung je Befund: blockierender Callback (z. B. synchroner Gemini-Aufruf) → eigener Thread/Async, MultiThreadedExecutor, Heartbeat auf eigenem Timer in eigenem Prozess; Scheduling → micro-ROS-Agents und Bridge mit nice/chrt, Hailo-Runner per taskset begrenzen, MJPEG bei aktiver Detektion drosseln.

### S-B – Radar-Spike auf der Radar-ECU (jederzeit, optional bis K10)

| Feld | Inhalt |
| --- | --- |
| Voraussetzung | Dritter XIAO ESP32-S3 + SN65HVD230 + BGT60TR13C-Shield (2.4). Kein Eingriff in Bestandsfirmware, kein USB-Port am Pi (Flashen am Laptop oder ueber das Service-Kabel der Sensor-ECU) |
| Frage | Liefert der Sensor ueber SPI stabile Rohframes, und reicht das Objektlisten-Format aus K2? |
| Vorgehen | (1) IO-Spannung des Shields pruefen (1,8 V oder 3,3 V) — vor dem ersten Anschluss; (2) Treiberbasis: Infineon sensor-xensiv-bgt60trxx (C, plattformunabhaengige SPI/GPIO-Schicht) auf ESP-IDF/PlatformIO portieren; (3) Rohframes lesen: Frame-Rate, Bytes je Frame, FIFO-Verhalten; (4) Konfiguration festlegen — Vorschlag 128 Chirps x 64 Samples x 3 RX, Chirpdauer 0,5 ms: v_res = lambda/(2 x T_frame) = 5 mm/(2 x 64 ms) = 0,039 m/s, v_max = lambda/(4 x T_chirp) = 2,5 m/s, ca. 37 KB je Frame, 10 Hz; (5) Range-FFT auf einem Frame mit ESP-DSP als Laufzeitprobe |
| Ergebnis | Testfall T-13 (radar_spi_test, R1); Radar-Konfiguration als Parameter der Radar-ECU; Bestaetigung oder Aenderung des Objektframes in der DBC |
| Nicht erlaubt | Aenderung an Bestandsfirmware oder an DBC-IDs; Fahrbewegung |

### G1 – Gate BA-01/BA-02/BA-05 (vor K4)

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFA-13 (neu) | PF1 | MUSS | CAN-Frameverlust am Pi 5 bei Volllast aller Sender vernachlaessigbar | Frameverlustrate je ID, rx_errors-Zuwachs | < 0,1 % je ID ueber 10 min (uebernommen aus NFA-10); rx_over_errors und Bus-Error-Zaehler Delta = 0 ueber 10 min | CAN-Frameverlust | BA-01, BA-02, S-A (P-CAN2) | IT-08 (can_validation_test, erweitert um Verlust- und Zaehlerauswertung) |

G1 umfasst NFA-13 und NFA-15 (BA-05, Tabelle K3): Ein Shadow Mode gegen ein Referenzsystem, das unter Last zeitweise nicht steuert, ist kein Nachweis. Konsequenz bei Nichtbestehen: K4 blockiert, MZ2 laeuft weiter (ueber micro-ROS).

### K4 – Drive-CAN im Shadow Mode

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | G1 bestanden; FA-19 erfuellt |
| Liefergegenstand | Pi 5 sendet VCU_DRIVE_COMMAND aus dem Gateway-Prozess (alive_counter und crc8 entstehen dort, nicht in der Bedien- und Leitstandsebene; Sollwert aus dem Arbiter-Ausgang) ueber CAN; Fahrkern dekodiert, prueft E2E, vergleicht mit micro-ROS-Sollwert, faehrt weiterhin nach micro-ROS; Vergleichszaehler und Abweichungsstatistik als Diagnosenachricht |
| Noch nicht | CAN als wirksame Kommandoquelle |
| Ausgangsbedingung | G2: IT-12, T-10, T-11 bestanden |

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-20 (neu) | PF1 | MUSS | CAN-Kommandopfad liefert im Shadow Mode dieselben Sollwerte wie der micro-ROS-Pfad | Sollwertabweichung nach Skalierung, Versatz | Abweichung 0 Quantisierungsschritte in >= 99,9 % der Ticks; Versatz <= 1 Tick (20 ms); Frameverlust < 0,1 % | Schattenbetrieb neuer Funktion vor Freigabe | amr_vehicle.dbc, NFA-01; Hardware-Zeitstempel des MCP2518FD nutzen (Treiberstand mcp251xfd pruefen) | IT-12 (neu, drive_shadow_test) |
| SIA-12 (neu) | PF1 | MUSS | E2E-Fehler (CRC, Counter-Sprung, Wiederholung) werden erkannt; im Shadow Mode nur gezaehlt, keine Fahrreaktion | Erkennungsrate bei Fehlerinjektion | 100/100 injizierte Fehler erkannt; 0 Fahrreaktionen | E2E-Fehlererkennung | SA-11 | T-10 (neu, can_e2e_test) |
| SIA-13 (neu) | PF1 | MUSS | Kommando-Timeout auf CAN: kein gueltiges VCU_DRIVE_COMMAND fuer t_timeout → Degraded Mode (v=0, omega=0, Stopp-Rampe) | t_timeout, Reaktionszeit | t_timeout = 3 Ticks = 60 ms *(Vorschlag, D-05)*; SIA-04 (500 ms) bleibt uebergeordnet | Steuergeraete-Notlauf / E2E-Timeout | NFA-01, SIA-04, SIA-05 | T-11 (neu, can_cmd_timeout_test) |
| SIA-15 (neu) | PF1 | MUSS | alive_counter und crc8 der Kommandoframes werden ausschliesslich im Gateway-Prozess (vehicle_can_gateway, erhoehte Prioritaet) erzeugt; die Bedien- und Leitstandsebene liefert nur Sollwerte | Herkunft des Zaehlers; Verhalten bei blockierter Bridge | Bei kuenstlich blockierter dashboard_bridge (5 s) laeuft der alive_counter lueckenlos weiter; der Fahrkern haelt den letzten gueltigen Sollwert oder geht nach SIA-13 in Degraded Mode — keine SIA-04-Ausloesung durch UI-Last | Gateway-/VCU-Alive-Counter statt Infotainment | BA-05, SA-11, SA-15 | T-10, IT-12 |

### K5 – CAN_PRIMARY

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | G2 bestanden |
| Liefergegenstand | Fahrkern nimmt Fahrbefehle aus VCU_DRIVE_COMMAND; micro-ROS-/cmd_vel nur in Betriebsart SERVICE (Werte gemaess K1-Betriebsmodi); Umschaltung per Parameter mit Rueckfall auf micro-ROS; Umschaltpunkt fuer MZ2 |
| Ausgangsbedingung | G3: IT-02, IT-03, IT-06 ueber CAN bestanden mit unveraenderten L1-Schwellwerten |

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-21 (neu) | PF1 | MUSS | Fahrbetrieb ueber CAN erfuellt die Fahrkern- und Navigationsanforderungen der L1 unveraendert | Ergebnisse IT-02, IT-03, IT-06 | Rotation < 5 Grad (FA-07); Geradeausfahrt < 5 cm / < 5 Grad (FA-06); Zielanfahrt <= 0,03 m / <= 0,05 rad (FA-03) | Regressionsnachweis nach Steuergeraete-Update | FA-03, FA-06, FA-07 | IT-02, IT-03, IT-06 (Wiederholung ueber CAN) |
| SIA-14 (neu) | PF1 | MUSS | Rueckfall auf micro-ROS ohne Firmware-Neuflash moeglich | Umschaltzeit | <= 1 Neustart des Fahrkerns | Rollback-Faehigkeit | Betriebsmodi K1 | T-11 |

### K6 – CAN = Runtime, USB = Service

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | G3 bestanden |
| Liefergegenstand | Runtime-Kommunikation Pi 5 ↔ ECUs ausschliesslich ueber CAN; micro-ROS/UART nur in Betriebsart SERVICE (Flash, Debug, Parametrierung); Dokumentation communication.md aktualisiert (Primaer/Sekundaer getauscht); VCU_SENSOR_COMMAND wirksam (Pan/Tilt/Servo-Speed ueber CAN, /servo_cmd nur SERVICE); XIAOs aus der 5-V-Rail versorgt, USB-Kabel nur Service; SA-01 und SA-02 auf Status "ersetzt durch SA-13" |
| Ausgangsbedingung | SV-04 bestanden → MZ1 geschlossen |

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SA-13 (neu) | PF1 | MUSS | Runtime-Pfad Pi 5 ↔ Fahrkern und Sensor- und Sicherheitsbasis ist CAN; micro-ROS/UART nur in SERVICE | Aktive Transportpfade je Betriebsart | AUTONOM/MANUELL: 0 micro-ROS-Runtime-Topics aktiv; SERVICE: micro-ROS aktiv | Fahrzeugbus vs. Diagnoseschnittstelle (OBD) | SA-01, SA-02 (ersetzt), communication.md | SV-04 |
| FA-10 | PF2 | MUSS | 10 Zielanfahrten ohne Kollision — Wiederholung ueber CAN | Kollisionsfreie Anfahrten | 10/10 | Typ-Fahrversuch | FA-10 (L1) | SV-04 (neu, Gesamtsystem ueber CAN, R3) |
| FA-29 (neu) | PF3 | MUSS | Pan/Tilt-Steuerung ueber CAN erfuellt die Latenzanforderung der Bedien- und Leitstandsebene | Befehlslatenz Kommando → Servo | < 300 ms (FA-13) | Karosserie-Funktion ueber Fahrzeugbus | SA-15, FA-13 | IT-09 (Wiederholung ueber CAN) |

## 5 Makrozyklus 2 – Winner-Funktionskette (K7–K10)

MZ2 beginnt nach G0 (Vertrag liegt vor) und laeuft parallel zu K3–K6. Bis zum Umschaltpunkt (K5) speist die Kette ihren Ausgang als Kommandoquelle "automatisiert" in den Arbiter (FA-19) ein; danach sendet sie VCU_DRIVE_COMMAND ueber das Gateway. Schwellwerte in MZ2 sind Platzhalter fuer K7 und dort herzuleiten; sie stehen hier, damit kein Paket ohne Messgroesse startet.

### Zuordnung Winner-Kette → Plattform

| Winner-Stufe | Ort | Bestand / Neu | Paket |
| --- | --- | --- | --- |
| Environment, Sensors | Sensor- und Sicherheitsbasis, LiDAR, IMU, Radar | Bestand (Radar neu) | K3, K10 |
| Sensor Preprocessing | Radar-ECU (Objektliste ueber CAN, D-02) | Neu | S-B, K10 |
| Perception | Pi 5 | Neu | K8a |
| Localization | Pi 5 (SLAM Toolbox, IMU-Fusion) | Bestand (FA-01, FA-02) | — |
| Environment Model | Pi 5 | Neu | K8b |
| Prediction | Pi 5 | Neu | K9a |
| Behavior | Pi 5 (Nav2 Behavior Tree als Ausgangspunkt) | Erweiterung | K9b |
| Trajectory Planning, Trajectory Control | Pi 5 (Nav2 Planner, RPP-Controller) | Bestand in Winner-Terminologie | K9c |
| Actuators, Vehicle | Fahrkern (PID 50 Hz), Motoren | Bestand | MZ1 |
| Rueckkopplung | Odometrie 0x200/0x201, IMU 0x130 | Bestand | K3 |

### K7 – Ketten-Skelett (Anforderungen, Schnittstellen, Durchstich)

K7 ist fuer MZ2, was K1 fuer MZ1 war: linke Seite des V.

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | G0 bestanden (Vertrag) |
| Liefergegenstand | (1) Ergaenzung der Anforderungsliste L1 um die Winner-Kette (Ebene gemaess D-03, PF gemaess D-04); (2) ROS-2-Schnittstellen je Stufe: genau ein Eingangs- und ein Ausgangs-Topic, Nachrichten mit header.stamp = Sensorzeit und Quell-ID; (3) Radar-Simulator-Knoten (Objektliste mit konfigurierbarer Szene); (4) Durchstich Simulator → Stubs aller Stufen → Kommandoquelle "automatisiert"; (5) gemessenes Latenzbudget je Stufe |
| Noch nicht | Echte Perception; echte Sensordaten in der Kette |
| Ausgangsbedingung | T-12 bestanden; Anforderungen fuer K8–K10 mit Schwellwerten festgelegt |

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SA-14 (neu) | D-04 | MUSS | Jede Winner-Stufe ist ein Knoten mit definierter Ein-/Ausgangsnachricht, Zeitstempel und Quell-ID | Schnittstellenliste | 1 Eingang, 1 Ausgang je Stufe; Zeitstempel = Sensorzeit | Funktionsarchitektur ADAS (Signalschnittstellen) | Winner et al. 2024 (A4) | T-12 (neu, chain_latency_test) |
| FA-22 (neu) | D-04 | MUSS | Durchstich Simulator-Ereignis → Fahrbefehl | Ende-zu-Ende-Latenz | < 100 ms *(Vorschlag: 5 Ticks; entspricht 1,5 cm Weg bei 0,15 m/s nach NFA-05)* | Reaktionszeit ADAS-Funktionskette | NFA-01, NFA-05 | T-12 |

### K8a – Perception

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-23 (neu) | D-04 | MUSS | LiDAR (und Radar-Simulator) → Objektliste (Position, Ausdehnung, Klasse statisch/dynamisch) | Erkennungsrate, Falschalarme | >= 95 % Erkennung statischer Hindernisse >= 0,1 m in 2 m Abstand ueber 100 Frames; <= 1 Falschalarm je 100 Frames *(Vorschlag)* | Umfeldsensorik-Objekterkennung | K7-Schnittstellen | IT-13 (neu, perception_test) |

### K8b – Environment Model

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-24 (neu) | D-04 | MUSS | Fusion Objektliste + Karte + Ego-Zustand zu einem zeitgestempelten Umfeldmodell mit stabilen Track-IDs | Track-Kontinuitaet, Aktualisierungsrate | >= 90 % ID-Stabilitaet ueber 5 s je Objekt; Rate >= 5 Hz (NFA-02: RPLIDAR A1 Ist 7,7 Hz; in v2.1 korrigiert) | Umfeldmodell / Objektfusion | FA-01, FA-02, FA-23 | IT-14 (neu, env_model_test) |

### K9a – Prediction

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-25 (neu) | D-04 | SOLL | Bewegungspraediktion dynamischer Objekte (CV- oder CTRV-Modell), Horizont 2 s | Praediktionsfehler bei 1 s | < 0,2 m *(Vorschlag)* | Objektpraediktion (ACC/AEB) | FA-24 | IT-15 (neu, prediction_test) |

### K9b – Behavior

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-26 (neu) | D-04 | MUSS | Zustandsautomat (Folgen, Anhalten, Ausweichen, Warten) auf Basis Umfeldmodell + Praediktion; Sicherheitslogik (SIA) bleibt vorrangig | Deterministische Uebergaenge; Vorrangtest | 100/100 definierte Szenarien mit erwartetem Zustand; Sicherheitslogik setzt sich 100/100 durch (FA-19) | Fahrstrategie / Manoeverplanung | FA-19, SIA-01–SIA-03 | IT-16 (neu, behavior_test) |

### K9c – Trajectory Planning und Trajectory Control

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-27 (neu) | PF2 | MUSS | Nav2 Planner und RPP-Controller als Trajectory Planning/Control der Kette; keine Verschlechterung gegenueber L1 | ATE, Zielanfahrt | NFA-11 < 0,20 m und FA-03 <= 0,03 m / <= 0,05 rad bleiben erfuellt bei aktiver Kette | Trajektorienregelung | NFA-11, FA-03 | IT-04, IT-06 (Wiederholung mit aktiver Kette) |

### K10 – Radar-ECU als dritter CAN-Knoten

| Feld | Inhalt |
| --- | --- |
| Eingangsbedingung | G4: T-13 bestanden, K8a und K6 abgeschlossen (CAN = Runtime) |
| Liefergegenstand | XIAO ESP32-S3 Nr. 3 als RADAR_ECU: BGT60TR13C an SPI (SCK, MISO, MOSI, CS, IRQ), TWAI an SN65HVD230, Versorgung 5-V-Rail, Flashen am Laptop oder ueber Service-Kabel, optional Debug-UART an die GPIO-UART des Pi 5 (Pin 8/10, D-08); Sensor Preprocessing auf der ECU: Fenster → Range-FFT → Doppler-FFT → CFAR → Winkel aus RX-Phasendifferenz → Objektliste (ESP-DSP); Objektframes 0x300 ff. und Heartbeat 0x3F0 gemaess DBC; Simulator aus K7 durch reale Objektliste ersetzt; Buslast gegen NFA-14 gemessen |
| Bekannte Grenze | 1 TX / 3 RX schaetzt den Winkel eines dominanten Ziels je Range-Doppler-Zelle, trennt aber keine zwei Ziele gleicher Entfernung und Geschwindigkeit; Indoor-Mehrwege erzeugen Geisterziele. Konsequenz: Radar liefert Geschwindigkeit und Bestaetigung, LiDAR die laterale Position — die Fusion in K8b ist Pflicht, nicht Kuer |
| Ausgangsbedingung | IT-17 bestanden; FA-28 erfuellt |

| ID | PF | Prio | Beschreibung | Messgroesse | Schwellwert | Kfz-Pendant | Referenz | Testfall-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FA-28 (neu) | D-04 | MUSS | Reales Radar liefert Objektliste an Perception; Ergebnisse von FA-23 bleiben mit realem Radar erfuellt | Erkennungsrate, Latenz Sensor → Objektliste | FA-23-Schwellwerte; Latenz < 50 ms *(Vorschlag)* | Radar-Steuergeraet mit Objektliste | S-B, D-02 | T-13, IT-17 (neu, radar_test) |

## 6 Rueckverfolgbarkeitsmatrix

### 6.1 Neue Testfaelle

| Testfall-ID | Skript (geplant) | V-Modell | Kfz-Testkategorie | Paket |
| --- | --- | --- | --- | --- |
| T-09 | can_dbc_check | R1 (Komponente) | Pruefstandtest | K2 |
| T-10 | can_e2e_test | R1 (Komponente) | Pruefstandtest | K4 |
| T-11 | can_cmd_timeout_test | R1 (Komponente) | Pruefstandtest | K4, K5 |
| T-12 | chain_latency_test | R1 (Komponente, Simulator) | Pruefstandtest | K7 |
| T-13 | radar_spi_test | R1 (Komponente) | Pruefstandtest | S-B, K10 |
| IT-08 (erw.) | can_validation_test | R2 (Integration) | Fahrversuch | G1, K2 |
| IT-09 (erw.) | dashboard_latency_test | R2 (Integration) | Fahrversuch | K3 (Lastprofil Objekterkennung), K6 (ueber CAN) |
| IT-10 | can_b2b_sensor_test | R2 (Integration) | Fahrversuch | K3 |
| IT-11 | cmd_source_test | R2 (Integration) | Fahrversuch | K3 |
| IT-12 | drive_shadow_test | R2 (Integration) | Fahrversuch | K4 |
| IT-13 | perception_test | R2 (Integration) | Fahrversuch | K8a |
| IT-14 | env_model_test | R2 (Integration) | Fahrversuch | K8b |
| IT-15 | prediction_test | R2 (Integration) | Fahrversuch | K9a |
| IT-16 | behavior_test | R2 (Integration) | Fahrversuch | K9b |
| IT-17 | radar_test | R2 (Integration) | Fahrversuch | K10 |
| SV-04 | Gesamtsystem ueber CAN | R3 (System) | Typgenehmigung | K6 |

### 6.2 Kreuztabelle Anforderung → Testfall → Paket

| Anforderung | Testfall-IDs | PF | Kfz-Testkategorie | Paket | Messprotokoll |
| --- | --- | --- | --- | --- | --- |
| SA-10 | T-09 | PF1 | Pruefstandtest | K2 | — |
| SA-11 | T-09, T-10 | PF1 | Pruefstandtest | K2, K4 | — |
| SA-15 | T-09 | PF1 | Pruefstandtest | K2 | — |
| SA-12 | T-09, IT-08 | PF1 | Fahrversuch | K2 | P-CAN2 |
| NFA-14 | T-09, IT-08 | PF1 | Fahrversuch | K2 | P-CAN2 |
| FA-18 | IT-10 | PF1 | Fahrversuch | K3 | P-CAN2 |
| FA-19 | IT-11 | PF1 | Fahrversuch | K3 | — |
| SIA-11 | IT-10 | PF1 | Fahrversuch | K3 | P-CAN2 |
| NFA-15 | IT-09 (erw.) | PF1 | Fahrversuch | K3, G1 | — |
| NFA-13 | IT-08 | PF1 | Fahrversuch | G1 | P-CAN2 |
| FA-20 | IT-12 | PF1 | Fahrversuch | K4 | P-CAN3 (A2) |
| SIA-12 | T-10 | PF1 | Pruefstandtest | K4 | — |
| SIA-13 | T-11 | PF1 | Pruefstandtest | K4 | — |
| SIA-15 | T-10, IT-12 | PF1 | Fahrversuch | K4 | — |
| FA-21 | IT-02, IT-03, IT-06 | PF1 | Fahrversuch | K5 | P1/P2, P4 (Wiederholung) |
| SIA-14 | T-11 | PF1 | Pruefstandtest | K5 | — |
| SA-13 | SV-04 | PF1 | Typgenehmigung | K6 | — |
| FA-10 (Wdh.) | SV-04 | PF2 | Typgenehmigung | K6 | P4 (Wiederholung) |
| FA-29 | IT-09 (Wdh. ueber CAN) | PF3 | Fahrversuch | K6 | P5 (Wiederholung) |
| SA-14 | T-12 | D-04 | Pruefstandtest | K7 | — |
| FA-22 | T-12 | D-04 | Pruefstandtest | K7 | — |
| FA-23 | IT-13 | D-04 | Fahrversuch | K8a | — |
| FA-24 | IT-14 | D-04 | Fahrversuch | K8b | — |
| FA-25 | IT-15 | D-04 | Fahrversuch | K9a | — |
| FA-26 | IT-16 | D-04 | Fahrversuch | K9b | — |
| FA-27 | IT-04, IT-06 | PF2 | Fahrversuch | K9c | P3, P4 (Wiederholung) |
| FA-28 | T-13, IT-17 | D-04 | Fahrversuch | K10 | — |

### 6.3 Von v2 beruehrte Bestandsanforderungen

| Anforderung (L1) | Aenderung | Ab Paket |
| --- | --- | --- |
| SA-01, SA-02 | Status "ersetzt durch SA-13" (micro-ROS/UART nur noch SERVICE) | K6 |
| SA-03 | CAN wird von "redundanter Pfad" zu Runtime-Pfad; Prio SOLL → MUSS | K5 |
| SA-04 | Kfz-Pendant "Signalliste CAN-DB" wird durch SA-10 konkret erfuellt | K2 |
| NFA-10 | Schwellwert < 0,1 % wird fuer CAN als NFA-13 uebernommen | G1 |
| SIA-04, SIA-05 | Bleiben gueltig; SIA-13 ergaenzt schnelleren CAN-Kommando-Timeout | K4 |
| FA-13, NFA-09 | Werden unter Volllast der Bedien- und Leitstandsebene pruefpflichtig (NFA-15, BA-05) | K3 |
| SA-09 | micro-ROS-MTU-Grenze verliert nach K6 die Runtime-Relevanz (nur SERVICE) | K6 |

## 7 Gates und verteidigbare Zwischenstaende

| Gate | Vor Paket | Kriterium | Bei Nichtbestehen |
| --- | --- | --- | --- |
| G0 | K2-Freeze | T-09 bestanden; S-A-Vorher-Messung im P-CAN2 | DBC bleibt Entwurf ohne Tag; MZ2 startet trotzdem gegen den Entwurf |
| G1 | K4 | NFA-13 (IT-08 erweitert) und NFA-15 (IT-09 erweitert) erfuellt | K4 blockiert; K3-Ergebnisse und MZ2 unberuehrt |
| G2 | K5 | IT-12, T-10, T-11 bestanden; FA-19 erfuellt | K5 blockiert; Shadow Mode bleibt aktiv zur Datensammlung |
| G3 | K6 | IT-02, IT-03, IT-06 ueber CAN mit L1-Schwellwerten | Rueckfall auf micro-ROS (SIA-14); Ursachenanalyse |
| G4 | K10 | T-13 bestanden; K8a und K6 abgeschlossen | K10 verschoben; Kette laeuft weiter mit Simulator |

Verteidigbare Zwischenstaende (jeder mit geschlossenem Nachweis):

1. Nach K2: CAN-Signalkatalog als DBC (Kfz-Pendant: OEM-Signaldatenbank), T-09.
2. Nach K6: MZ1 geschlossen — Fahrzeug faehrt ueber CAN, micro-ROS ist Diagnosepfad, SV-04.
3. Nach K7: MZ2-Architektur steht — Kette als Skelett mit Latenzbudget, T-12.
4. Nach jedem weiteren Paket: eine Winner-Stufe real, Rest Simulator/Stub.

## 8 Entscheidungen

### 8.1 Entschieden (2026-09-03)

| ID | Entscheidung | Begruendung (Daten → Regel → Schluss) | Wirkung |
| --- | --- | --- | --- |
| D-01 | MCP2518FD-Breakout an SPI0 des Pi 5 (kein HAT), klassisches CAN 2.0B, 1 Mbit/s, Abtastpunkt 80 % auf allen Knoten | Radar-Objektliste = Burst bis 8 Frames (ca. 1 ms); MCP2515 hat 2 RX-Puffer und verlangt Abholung alle ca. 260 us; MCP2518FD hat 31 FIFOs und Hardware-Zeitstempel. Buslast (2 %) war nie das Problem. CAN FD scheidet aus, weil TWAI nur CAN 2.0 spricht; HAT scheidet aus wegen Hailo-8L/M.2. **Bestaetigt durch S-A vorher 2026-09-03 (Fall 1):** rx_over_errors Delta 6674 (A1) / 6001 (A2) je 10 min, bus_error 0, Verlust auf dem dritten Frame im Burst, 0x200 21,5 / 27,4 %. Umfang: genau 1 Modul am Pi; ESP32 behalten TWAI (Pinbudget +3 je Knoten nicht vorhanden, Bestandsfirmware inkl. Notstopppfad bliebe sonst nicht unangetastet) | G0, S-A, K3; SA-12 nur noch innerhalb eines Senders |
| D-02 | Dritter XIAO ESP32-S3 als Radar-ECU, reiner CAN-Knoten, Objektliste ueber CAN | Drive-ECU 11/11 Pins, Sensor-ECU >= 7/11; Radar braucht 5. Alle USB-Ports belegt → Knoten ohne USB, Versorgung aus 5-V-Rail, Flashen am Laptop. Entspricht dem Kfz-Muster Radarsteuergeraet mit Objektliste | K2 (Node RADAR_ECU, 0x300 ff.), S-B, K10 |

### 8.2 Offen

| ID | Frage | Optionen | Entscheidet | Wirkung auf |
| --- | --- | --- | --- | --- |
| D-03 | Ebene der Winner-Kette in der Anforderungsliste | (a) neue Ebene D "Automatisiertes Fahren"; (b) Erweiterung Ebene A und C | K7 | Anforderungsliste, Terminologie-Norm |
| D-04 | Projektfrage fuer MZ2 | (a) Zuordnung zu PF1–PF3; (b) neue Projektfrage | K7 | Abdeckungstabelle 8.3 der L1 |
| D-05 | t_timeout CAN-Kommando | (a) 60 ms (3 Ticks); (b) 500 ms wie SIA-04; (c) anderer Wert aus K1 | K4 | SIA-13, T-11 |
| D-06 | ID-Vergabe | Abgleich der hier vergebenen IDs (FA-18 ff., SA-10 ff., SIA-11 ff., NFA-13 ff., T-09 ff., IT-10 ff., SV-04) mit K1 | Merge | Alle Tabellen |
| D-07 | Schnitt der Kommandoframes | (a) VCU_DRIVE_COMMAND + VCU_SENSOR_COMMAND wie hier; (b) zusaetzlich VCU_HARDWARE_COMMAND fuer LED-PWM und Motor-Limit (heute /hardware_cmd an beide Knoten) | K2 | DBC, SA-11, SA-15 |
| D-08 | Debug-UART der Radar-ECU an die GPIO-UART des Pi 5 | (a) ja (9/11 Pins); (b) nein, Diagnose nur ueber 0x3F0 | S-B | K10 |
| D-09 | Ursache BA-05 | (a) blockierender Callback (Gemini synchron); (b) Scheduling/CPU-Last; (c) Browser/WebSocket | Diagnoseleiter in K3 | NFA-15, Behebung in K3 |

## 9 Bezugsdokumente und Quellen

| Kuerzel | Quelle | Verwendung |
| --- | --- | --- |
| L1 | Anforderungsliste L1 v1.0, 2026-03-22 (docs/anforderungsliste-L1.md) | ID-Schema, Spalten, Randbedingungen, Bestandsschwellwerte |
| COMM | docs/architecture/communication.md | Dual-Path-Bestand, CAN-Notstopp 0x120/0x141, Latenz < 20 ms |
| K1 | docs/architecture/signalbedarf.md | Signalbedarf, Betriebsmodi, Safety-Regeln (A1) |
| PLAN-v1 | Ausbauplan K0–K10, Gesamtueberblick nach K0 und K1 | Paketinhalte, Befunde BA-01–BA-04, T-09, P-CAN2 |
| STYLE | docs/projektarbeit_style.md | Terminologie-Norm, keine UTF-8-Umlaute |
| VDI 2206 | VDI 2206:2021-11, Entwicklung mechatronischer und cyber-physischer Systeme | Makrozyklus, V-Modell, Eigenschaftsabsicherung |
| ISO 11898 | ISO 11898-1/-2 | CAN-Rahmenformat, 111–135 Bit je 8-Byte-Standardrahmen |
| E2E | AUTOSAR E2E Protocol Specification, Profil 1 | CRC-8, Alive Counter 4 Bit, Data-ID |
| MCP2515 | Microchip MCP2515 Datenblatt | 2 Empfangspuffer (RXB0, RXB1) |
| MCP2518FD | Microchip MCP2518FD Datenblatt | FIFO-basierter Empfang, 2 KB Nachrichten-RAM |
| twist_mux | ROS 2 Humble, Paket twist_mux | Arbiter FA-19 |
| MCP2518FD-BO | Soldered CAN-Bus Breakout MCP2518FD (Art. 333020), Datenblatt | Breakout-Formfaktor, Terminierungs-Jumper, 2,7–5 V |
| XENSIV | Infineon, sensor-xensiv-bgt60trxx (GitHub); Datenblatt BGT60TR13C | Treiberbasis Radar-ECU; Band 58–63,5 GHz, 1 TX / 3 RX |
| ESP-DSP | Espressif ESP-DSP | FFT-Laufzeitprobe in S-B |
| FW-DOC | docs/firmware/sensors-actuators.md, docs/robot_parameters.md, docs/systemdokumentation.md | CAN-Frame-Raten des Bestands, I2C-Belegung, Servo-Parameter, Pinzaehlung (A6) |
| WINNER | Winner et al., Handbuch Assistiertes und Automatisiertes Fahren, 4. Aufl. 2024 | Funktionskette (A4, Kapitel nicht verifiziert) |

Nicht aus Quellen, sondern Vorschlag dieses Dokuments: Schwellwerte mit Kennzeichnung *(Vorschlag)*, die Faustregel 30 % Buslast, die Gate-Struktur G0–G4, die Radar-Konfiguration in S-B, das Objektframe-Layout und die BA-05-Hypothese (D-09).

---

Ohne Zwiebel-/Bloch-/Nguyen-Kim-Modul erstellt (Minimal-Set: Ehrlichkeit + Quellen-Traceability).
