# Arbeitsplan K0–K2 und S-A (vorher)

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Arbeitsplan zu Phasenplan v2.1 (Pakete K0, K1, K2; Spike S-A Teil A) |
| Version | 1.2 (Entwurf; 1.1 um die Ergebnisse von S-A vorher ergaenzt: Tick-Regel und Zykluszeit 0x200/0x201 = 40 ms, T-09 Schritte 9 und 10, Umsetzungsstand K2 in Anhang A.8) |
| Datum | 2026-09-03 |
| Autor | Jan (Entwurf erstellt mit KI-Assistent, Freigabe offen) |
| Bezug | docs/plan/phasenplan-v2.md (v2.1), Anforderungsliste L1 v1.1 (docs/anforderungsliste-L1.md), docs/firmware/sensors-actuators.md, docs/architecture/signalbedarf.md (K1), amr/mcu_firmware/*/include/twai_can.hpp (Bestandslayout) |
| Zweck | Was liegt vor (K0, K1), was ist vor K2 zu pruefen, was liefert K2 in welcher Reihenfolge, wie wird S-A vorher gemessen und ausgewertet |

Reihenfolge der Arbeit: **S-A vorher zuerst** (10 min je Lastprofil, Bestand unveraendert), dann K2. Grund: S-A misst das System, wie es heute ist; jede K2-Aenderung an Firmware oder Verdrahtung wuerde die Vorher-Messung entwerten. K2 aendert weder Firmware noch Verdrahtung, kann also parallel beginnen — aber der Messlauf laeuft vor dem ersten Commit.

## 1 K0 – Baseline (abgeschlossen): Bestaetigung vor K2

K0 ist fertig. Vor K2 wird nur geprueft, dass die Baseline noch die Baseline ist.

| Nr. | Pruefung | Nachweis | Status |
| --- | --- | --- | --- |
| K0.1 | Firmware unveraendert gegenueber Baseline | git-Tag/Commit der Baseline-Firmware = Commit auf beiden XIAO (config_drive.h, config_sensors.h Versionsstrings) | offen |
| K0.2 | baseline_snapshot reproduzierbar | Erneuter Lauf; Topic-Raten und TF-Baum innerhalb der K0-Toleranz | offen |
| K0.3 | CAN-Anbindung Pi unveraendert | MCP2515, Overlay-Zeile in config.txt (Oszillator, Interrupt-GPIO) notiert | offen |
| K0.4 | Befundliste vollstaendig | BA-01 bis BA-05 mit Zuordnung (siehe unten) | erledigt mit v2.1 |

Befunde und Besitzer:

| Befund | Inhalt | Wird geklaert in | Nachweis |
| --- | --- | --- | --- |
| BA-01 | 0x200: 4,58 % Frameverlust (K0, MCP2515) | S-A vorher (Ursache), G1 (Behebung) | P-CAN2 Teil A/B, NFA-13 |
| BA-02 | steigende CAN-rx_errors | S-A vorher | P-CAN2 Teil A |
| BA-03 | zwei /cmd_vel-Publisher | K3 (Arbiter, FA-19) | IT-11 |
| BA-04 | /cliff waehrend K0 dauerhaft true | K3 (Bodenkontakt) | T-05 |
| BA-05 | Steuerungsverlust bei aktiver Objekterkennung | K3 (Diagnoseleiter, NFA-15) | IT-09 erweitert |

S-A vorher misst bewusst mit und ohne Objekterkennung (Lastprofile A1/A2, Abschnitt 4): BA-01/BA-02 und BA-05 koennten dieselbe Ursache haben (Host-Latenz unter Last).

## 2 K1 – Anforderungen und Zielarchitektur (abgeschlossen): Eingangspruefung fuer K2

K1 ist fertig. K2 braucht aus signalbedarf.md konkrete Antworten. Was fehlt, legt K2 als *Vorschlag* fest und markiert es (D-05, D-06, D-07).

| Nr. | Frage an signalbedarf.md | Wenn vorhanden | Wenn nicht vorhanden |
| --- | --- | --- | --- |
| K1.1 | Signalliste mit Einheit, Skalierung, Wertebereich je Signal | uebernehmen | aus config_*.h und Firmware-Doku ableiten (Abschnitt 3.2) |
| K1.2 | Enum der Betriebsmodi (Werte fuer operating_mode) | uebernehmen | Vorschlag: 0 OFF, 1 SERVICE, 2 MANUAL, 3 AUTONOMOUS, 4 DEGRADED — *(Vorschlag)* |
| K1.3 | IDs fuer Pi-Frames (Kommandos) | uebernehmen | Vorschlag Bereich 0x400–0x4F0 (Abschnitt 3.3) |
| K1.4 | Timeout-/Degraded-Regeln fuer den CAN-Kommandopfad | uebernehmen | D-05 (60 ms oder 500 ms), in DBC als Kommentar |
| K1.5 | Zuordnung Anforderung ↔ Test mit ID-Reihen ab FA-18/SA-10/T-09 | IDs des Phasenplans daran ausrichten (D-06) | Phasenplan-IDs gelten vorlaeufig |
| K1.6 | Servo-/Hardware-Kommandos (Pan, Tilt, Speed, LED, Motor-Limit) als Signalbedarf gelistet | uebernehmen | SA-15 wie im Phasenplan; LED/Motor-Limit → D-07 |
| K1.7 | Layout von 0x150 (Servo-Status, in Plan v1 gelistet, in sensors-actuators.md nicht) | uebernehmen | aus config_sensors.h lesen; sonst als Platzhalter mit Kommentar "Layout zu bestaetigen" |

Ausgang der Eingangspruefung: eine kurze Liste "aus K1 uebernommen" / "in K2 vorgeschlagen" am Kopf der DBC (als Kommentarblock) — das ist die Traceability K1 → K2.

## 3 K2 – DBC (vier Nodes), E2E, Sendeoffsets, cantools

### 3.1 Arbeitspakete in Reihenfolge

| Nr. | Arbeitspaket | Ergebnis | Abnahme |
| --- | --- | --- | --- |
| K2.1 | DBC-Geruest: Nodes PI_VCU, DRIVE_ECU, SENSOR_ECU, RADAR_ECU; Attribute GenMsgCycleTime, GenMsgStartDelayTime, GenMsgSendType definieren | amr_vehicle.dbc laedt mit cantools (strict=True) | T-09 Schritt 1 |
| K2.2 | 13 Bestandsnachrichten exakt nach Firmware (Abschnitt 3.2); Byte-Order Intel (LE); float32 als SIG_VALTYPE_ | Roundtrip je Nachricht | T-09 Schritt 2–3 |
| K2.3 | Kommandoframes VCU_DRIVE_COMMAND, VCU_SENSOR_COMMAND (Abschnitt 3.3) mit alive_counter und crc8; Semantik als Kommentar (Einheit, Timeout, Degraded) | Vertrag fuer MZ2 | T-09 Schritt 2–3, Review |
| K2.3a | Restlicher Signalbedarf aus K1 (Vorrang vor Abschnitt 3.3): Notstopp P-05, Gateway-Lebenszeichen P-06, Pfadstatus D-05, zyklische Wiederholung der Batterieabschaltung S-02, Stellgroessenbegrenzung P-04 | jede Zeile des Signalbedarfs abgedeckt (SA-10) | T-09 Schritt 10 |
| K2.4 | Zykluszeit und Sendeoffset je zyklischer Nachricht (Abschnitt 3.4) — **nur Spezifikation**, Firmware setzt sie erst in K3/K4 um | Sendeplan in der DBC | T-09 Schritt 4 |
| K2.5 | Radar-Reservierung 0x300–0x3F0 als Platzhalter (Abschnitt 3.5) | Bereich belegt, keine Ueberlappung | T-09 Schritt 2 |
| K2.6 | cantools-Integration: Python-Zugriff (Pi), C-Codegenerierung (ESP32) in mcu_firmware/common/can/ — generierte Dateien nicht handeditieren | Header/Sourcen aus DBC | T-09 Schritt 5 |
| K2.7 | T-09 can_dbc_check als pytest (Abschnitt 3.6) | gruener Lauf in CI/lokal | — |
| K2.8 | P-CAN2 vorbereitet: Protokollvorlage + Skripte (Abschnitt 4) liegen unter validation/ | Vorlage, s_a_vorher.sh, s_a_analyse.py | Probelauf 60 s |
| K2.9 | Doku: docs/architecture/can-signalkatalog.md aus der DBC generiert | Seite in mkdocs | Review |
| K2.10 | Doku-Abweichungen des Ist-Zustands bereinigen (signalbedarf.md 7.6): Servosollwert 0x150, Kennzeichnung der vom Fahrkern empfangenen Sicherheitssignale, DLC von 0x1F0 | hardware/can-bus/CAN-Bus.md korrigiert | Review |

Nicht in K2: Firmwarelogik aendern, Fahrbefehle ueber CAN aktivieren, USB abschalten, Fahrbewegung, Hardwarezustaende annehmen, Controllertausch.

### 3.2 Bestandsnachrichten (Quelle: docs/firmware/sensors-actuators.md; Layout-Details aus config_*.h bestaetigen)

Byte-Order: Intel (Little Endian); alle Mehrbyte-Werte werden in der Firmware per `memcpy` gepackt (twai_can.hpp beider Knoten). Layouts am 2026-09-03 aus dem Code bestaetigt (Anhang A.3); Skalierungen entsprechen den Signalklassen in NFA-16.

| ID | Name (Vorschlag) | Sender | Rate | DLC | Signale (Typ, Einheit) |
| --- | --- | --- | --- | --- | --- |
| 0x110 | SENSOR_RANGE | SENSOR_ECU | 10 Hz | 4 | range float32 m |
| 0x120 | SENSOR_CLIFF | SENSOR_ECU | 20 Hz | 1 | cliff uint8 (0 OK, 1 Cliff) |
| 0x130 | SENSOR_IMU_ACC | SENSOR_ECU | 50 Hz | 8 | ax, ay, az int16, Faktor 0,001 m/s^2 (Code-Kommentar "mg approx"); gz int16, Faktor 0,01 rad/s |
| 0x131 | SENSOR_IMU_HEADING | SENSOR_ECU | 50 Hz | 4 | heading float32 rad (Komplementaerfilter) |
| 0x140 | SENSOR_BATTERY | SENSOR_ECU | 2 Hz | 6 | voltage uint16 mV; current int16 mA; power uint16 mW (Saettigung 65,535 W, S-06) |
| 0x141 | SENSOR_BATTERY_SHUTDOWN | SENSOR_ECU | Event | 1 | shutdown uint8 (0 OK, 1 Shutdown) |
| 0x150 | VCU_SERVO_COMMAND_LEGACY *(Name Vorschlag)* | **PI_VCU → SENSOR_ECU** | Event, max. 10 Hz | 4 | pan int16 0,1 Grad; tilt int16 0,1 Grad. Kein Statusframe: Empfangs-ID `id_servo_cmd_rx` der Sensor-Firmware (K1.7 geklaert, Anhang A.3). Verhaeltnis zu 0x410 in K2 entscheiden |
| 0x1F0 | SENSOR_HEARTBEAT | SENSOR_ECU | 1 Hz | 8 | [0] flags: bit0 imu_ok, bit1 ina260_ok, bit2 pca9685_ok, bit3 bat_shutdown, bit4 core1_ok; [1] uptime_s mod 256; [2-3] i2c_err uint16; [4-5] servo_err uint16; [6-7] servo_ok uint16 (Zaehler saturiert bei 65535) |
| 0x200 | DRIVE_ODOM_XY | DRIVE_ECU | 20 Hz nominell; Ist 40/60-ms-Wechsel (tick-quantisiert) -> DBC 40 ms | 8 | x, y float32 m |
| 0x201 | DRIVE_ODOM_HEADING_SPEED | DRIVE_ECU | 20 Hz nominell; Ist wie 0x200 -> DBC 40 ms | 8 | yaw float32 rad; v_linear float32 m/s |
| 0x210 | DRIVE_WHEEL_SPEED | DRIVE_ECU | 10 Hz; DBC 80 ms (12,5 Hz) | 8 | wheel_l, wheel_r float32 rad/s |
| 0x220 | DRIVE_MOTOR_PWM | DRIVE_ECU | 10 Hz; DBC 80 ms (12,5 Hz) | 4 | pwm_l, pwm_r int16 |
| 0x2F0 | DRIVE_HEARTBEAT | DRIVE_ECU | 1 Hz | 2 | [0] flags: bit0 encoder_ok, bit1 motor_ok, bit2 pid_active, bit3 bat_shutdown, bit4 core1_ok, bit5 failsafe (bit0/1/4 heute fest 1, D-06); [1] uptime_s mod 256 |

Zykluszeit-Regel (aus S-A vorher): Zykluszeiten in der DBC sind ganzzahlige Vielfache des Sender-Ticks. Der Fahrkern arbeitet mit 20 ms; 50 ms (2,5 Ticks) fuehren zum gemessenen 40/60-ms-Wechsel (Median 59,5 ms bei 12 000 erwarteten Frames in 600 s). 0x200/0x201 werden daher mit 40 ms (25 Hz) spezifiziert -- das erfuellt NFA-03 (Soll 20 Hz) mit Reserve. Die Sensorbasis arbeitet mit 10 ms; ihre Zykluszeiten sind bereits Vielfache davon. Umsetzung in der Firmware in K3 (Sensorbasis) und K4 (Fahrkern); bis dahin dokumentiert die DBC den Sollwert, T-09 Schritt 9 prueft die Regel.

Rechnerische Buslast des Bestands (ohne Stuffing, 11-Bit-ID): ca. 18 kbit/s = 1,8 % bei 1 Mbit/s; 194 Frames/s (gemessen: 1,75 %, 188,6 Frames/s). Mit beiden Kommandoframes (50 Hz, 10 Hz) ca. 2,5 %. T-09 rechnet das aus der DBC nach.

Hinweis Codegenerierung: Der cantools-C-Generator unterstuetzt float32-Signale (SIG_VALTYPE_): Probelauf mit cantools 43.0.2 am 2026-09-03 erzeugt `float`-Strukturfelder, packt per `memcpy` in uint32 und Little-Endian-Bytes, Encode/Decode als Cast; Python-Roundtrip exakt (Anhang A.4). Das Umpacken auf skalierte Integer bleibt Kuer.

### 3.3 Kommandoframes (Vorschlag, falls K1 nichts vorgibt)

ID-Regel: numerisch ueber 0x120 und 0x141, damit Cliff und Shutdown die Arbitrierung gewinnen. Bestehende Pi-Kommando-ID im Sensorbereich: 0x150 (Servo, Abschnitt 3.2); sie bleibt unveraendert, bis K2 ihr Verhaeltnis zu 0x410 festlegt. Vorschlag: eigener PI_VCU-Bereich 0x400–0x4F0 (niedrigste Prioritaet auf dem Bus — bei 2 % Buslast ohne praktische Auswirkung, Kfz-Lehre: Notstopp vor Kommando).

Entscheidung in K2 (Abweichung vom Vorschlag): signalbedarf.md 7.4 fordert fuer sicherheitsrelevante Signale eine hoehere Buspriorisierung als fuer Diagnosesignale. Der Notstopp (P-05) und das Gateway-Lebenszeichen (P-06) erhalten deshalb 0x160 und 0x170 — numerisch ueber 0x141, damit Kantenerkennung und Batterieabschaltung weiterhin gewinnen, aber vor der gesamten 0x2xx-Diagnosereihe. Fahrbefehl und Servokommando bleiben im Bereich 0x400. Der Pfadstatus (D-05) ist ein Frame der Drive-ECU und liegt bei 0x230. Alle drei Nachrichten sind unten spezifiziert.

VCU_DRIVE_COMMAND, 0x400, PI_VCU → DRIVE_ECU, 50 Hz (Tick des Fahrkerns), DLC 8:

| Signal | Bits | Typ | Skalierung | Bereich | Bemerkung |
| --- | --- | --- | --- | --- | --- |
| target_velocity | 0–15 | int16 | 0,001 m/s | ±32,767 m/s | NFA-05/NFA-06 begrenzen auf 0,15 / 0,40 m/s in der ECU |
| target_yaw_rate | 16–31 | int16 | 0,001 rad/s | ±32,767 rad/s | NFA-07 begrenzt auf 1,0 rad/s in der ECU |
| enable | 32 | bool | — | 0/1 | 0 = Sollwert ignorieren, Stopp-Rampe |
| operating_mode | 33–36 | uint4 | Enum K1.2 | 0–15 | |
| reserved | 37–51 | — | — | — | 0 |
| alive_counter | 52–55 | uint4 | — | 0–15, rollierend | E2E Profil-1-Muster |
| crc8 | 56–63 | uint8 | — | — | CRC-8 SAE J1850 (0x1D) ueber Byte 0–6 + Data-ID (0x400 low byte) |

VCU_SENSOR_COMMAND, 0x410, PI_VCU → SENSOR_ECU, 10 Hz (heute /servo_cmd-Rate), DLC 8:

| Signal | Bits | Typ | Skalierung | Bereich | Bemerkung |
| --- | --- | --- | --- | --- | --- |
| pan | 0–15 | uint16 | 0,1 Grad | 0–180 Grad | mechanisch 0–159 Grad lt. Datenblatt (robot_parameters.md) |
| tilt | 16–31 | uint16 | 0,1 Grad | 0–180 Grad | |
| servo_speed | 32–39 | uint8 | — | 0–255 | wie /hardware_cmd heute |
| reserved | 40–51 | — | — | — | 0 |
| alive_counter | 52–55 | uint4 | — | 0–15 | |
| crc8 | 56–63 | uint8 | — | — | wie oben, Data-ID 0x10 |

Semantik (als Kommentar in die DBC): Timeout t_timeout (D-05) ohne gueltiges Kommando → Degraded Mode (v = 0, omega = 0, Stopp-Rampe); SIA-04 (500 ms) bleibt uebergeordnet. Im Shadow Mode (K4) werden E2E-Fehler nur gezaehlt.

Motor-Limit (P-04) liegt in VCU_DRIVE_COMMAND als `motor_limit_percent` (7 Bit, 0-100 %). Offen (D-07): LED-PWM aus /hardware_cmd — in K1 nicht als Signalbedarf gelistet; entweder reservierte Bits in VCU_DRIVE_COMMAND oder ein eigener Frame 0x420. In K2 nicht vergeben.

Weitere Nachrichten aus dem Signalbedarf (K1 hat Vorrang vor diesem Abschnitt):

VCU_EMERGENCY_STOP, 0x160, PI_VCU → DRIVE_ECU und SENSOR_ECU, 10 Hz, DLC 4 (P-05):

| Signal | Bits | Typ | Bemerkung |
| --- | --- | --- | --- |
| estop_request | 0 | bool | 0 = kein Notstopp, 1 = Notstopp |
| estop_source | 1–4 | uint4 | 0 NONE, 1 DASHBOARD, 2 VOICE, 3 SAFETY_NODE, 4 NAVIGATION, 5 WATCHDOG |
| estop_counter | 8–15 | uint8 | fortlaufend; macht ein verlorenes Ereignis erkennbar |
| alive_counter | 16–19 | uint4 | E2E |
| crc8 | 24–31 | uint8 | ueber Byte 0–2 + Data-ID 0x60 |

VCU_HEARTBEAT, 0x170, PI_VCU → DRIVE_ECU und SENSOR_ECU, 10 Hz, DLC 8 (P-06): hb_counter uint8, vcu_state uint4 (Enum wie operating_mode), uptime_s uint32, alive_counter uint4, crc8 (Data-ID 0x70).

DRIVE_PATH_STATUS, 0x230, DRIVE_ECU → PI_VCU, 5 Hz, DLC 8 (D-05): active_source uint4 (0 NONE, 1 SERIAL_REFERENCE, 2 CAN), operating_mode uint4, age_serial_ms uint16, age_can_ms uint16, Statusbits (cliff_armed, cliff_timeout, estop_latched, vcu_hb_timeout), alive_counter uint4, crc8 (Data-ID 0x30).

S-02 (zyklische Wiederholung der Batterieabschaltung) benoetigt keine neue Kennung: 0x141 erhaelt in der DBC GenMsgSendType `cyclicAndEvent` mit 1000 ms. Die Firmware sendet heute nur ereignisgesteuert; die Umsetzung erfolgt in K3.

Betriebsmodus-Enum (K1, Anforderungsliste Abschnitt 13.1; Zahlenwerte in K2 vergeben): 0 SERIAL_REFERENCE, 1 CAN_SHADOW, 2 CAN_PRIMARY, 3 SERVICE, 4 FAILSAFE. Zeitueberwachung im Modus CAN_PRIMARY: 300 ms (D-05 des Phasenplans damit entschieden).

Verhaeltnis 0x150 zu 0x410: 0x410 ersetzt 0x150 **nicht** in K2. 0x150 bleibt unveraendert in Betrieb, damit aeltere Firmware betriebsfaehig bleibt (signalbedarf.md 7.3); die Umstellung auf 0x410 erfolgt in K5.

### 3.4 Zykluszeiten und Sendeoffsets (Spezifikation; Umsetzung Sensor-ECU in K3, Drive-ECU in K4)

Ziel: Je Sender maximal 2 Frames back-to-back je Tick. Offsets gelten innerhalb eines Senders; die ECU-Takte sind nicht synchronisiert.

| Sender | Nachricht | Zyklus | Offset (Vorschlag) |
| --- | --- | --- | --- |
| SENSOR_ECU | 0x130 | 20 ms | 0 ms |
| SENSOR_ECU | 0x131 | 20 ms | 10 ms |
| SENSOR_ECU | 0x120 | 50 ms | 5 ms |
| SENSOR_ECU | 0x110 | 100 ms | 15 ms |
| SENSOR_ECU | 0x140 | 500 ms | 25 ms |
| SENSOR_ECU | 0x1F0 | 1000 ms | 35 ms |
| SENSOR_ECU | 0x141 | 1000 ms (Wiederholung zusaetzlich zum Ereignis, S-02) | 45 ms |
| DRIVE_ECU | 0x200 | 40 ms (2 Ticks) | 0 ms |
| DRIVE_ECU | 0x201 | 40 ms (2 Ticks) | 0 ms -- gleicher Tick wie 0x200, damit x/y und yaw/v zusammengehoeren; 2 Frames back-to-back sind erlaubt |
| DRIVE_ECU | 0x210 | 80 ms (4 Ticks) *(Vorschlag; 12,5 Hz statt 10 Hz)* | 20 ms -- ungerader Tick, trifft nie auf das Odom-Paar |
| DRIVE_ECU | 0x220 | 80 ms (4 Ticks) *(Vorschlag)* | 60 ms -- ungerader Tick |
| DRIVE_ECU | 0x230 | 200 ms (10 Ticks) | 40 ms |
| DRIVE_ECU | 0x2F0 | 1000 ms (50 Ticks) | 60 ms -- ungerader Tick |
| PI_VCU | 0x160 | 100 ms | 0 ms |
| PI_VCU | 0x170 | 100 ms | 5 ms |
| PI_VCU | 0x400 | 20 ms | 0 ms |
| PI_VCU | 0x410 | 100 ms | 5 ms |

Alternative zu 80 ms fuer 0x210/0x220: 100 ms beibehalten und den dann jeden zweiten Zyklus entstehenden 4-Frame-Burst dem MCP2518FD ueberlassen; die Regel "max. 2 Frames je Tick" waere dann eine Soll-, keine Muss-Regel. In K2 wurde die 80-ms-Variante gewaehlt, weil sie den in S-A vorher gemessenen Burst ohne zusaetzliche Hardware entschaerft.

Wichtig fuer S-A: Die Vorher-Messung (Teil A, erledigt) zeigt das heutige Sendeverhalten (0x130/0x131 und 0x200/0x201 back-to-back, Odom im 40/60-ms-Wechsel). Die Offsets und die 40-ms-Zykluszeit wirken erst nach K3/K4 und sind Teil der Nachher-Bewertung.

### 3.5 Radar-Reservierung (Platzhalter, RADAR_ECU, Layout in S-B zu bestaetigen)

| ID | Name | Rate | DLC | Inhalt |
| --- | --- | --- | --- | --- |
| 0x300 | RADAR_LIST_HEADER | 10 Hz | 4 | frame_counter uint8; n_objects uint8; status uint8; reserved |
| 0x301–0x308 | RADAR_OBJECT_1..8 | 10 Hz | 8 | range uint16 mm; angle int16 0,01 Grad; v_radial int16 cm/s; amplitude uint8; object_id uint8 |
| 0x3F0 | RADAR_HEARTBEAT | 1 Hz | 8 | flags, uptime, Diagnostik (wie 0x1F0) |

Buslast Radar: 9 Frames x 10 Hz = 90 Frames/s = ca. 1 % — Burst von 9 Frames alle 100 ms (Grund fuer D-01).

### 3.6 T-09 can_dbc_check (R1, Pruefstandtest) — Testplan

Testtyp: Komponententest ohne Hardware (pytest, laeuft in CI). Abdeckungsziel: jede Nachricht, jedes Signal, jedes Attribut.

| Schritt | Test | Erwartung |
| --- | --- | --- |
| 1 | cantools.database.load_file(dbc, strict=True) | laedt ohne Fehler (strict prueft Ueberlappung und Signalgrenzen) |
| 2 | Menge der Frame-IDs == erwartete Menge (13 Bestand + 2 Kommandos + 10 Radar-Platzhalter) | Gleichheit, keine Zusatz-IDs |
| 3 | Roundtrip je Nachricht: encode(min), encode(max), encode(Zufall) → decode | Abweichung <= 1 Quantisierungsschritt; float32 exakt |
| 4 | Attribute: jede zyklische Nachricht hat GenMsgCycleTime > 0 und GenMsgStartDelayTime gesetzt; Event-Nachrichten (0x141) GenMsgSendType = Event | vollstaendig |
| 5 | Codegenerierung: generierte C-Header aus DBC neu erzeugen und mit eingecheckten vergleichen | diff leer |
| 6 | Buslast: Summe(Rate x Bits) / 1e6 ausgeben; Bits je Frame = 47 + 8 x DLC (ohne Stuffing) | < 30 % (NFA-14); Wert im Testprotokoll |
| 7 | E2E: crc8-Berechnung gegen drei bekannte Vektoren (Referenzimplementierung in Python) | Gleichheit |
| 8 | ID-Regel: alle PI_VCU-IDs numerisch > 0x141; zusaetzlich Sicherheit vor Diagnose (0x160/0x170 vor der 0x2xx-Reihe) | wahr |
| 9 | Tick-Regel: GenMsgCycleTime jeder DRIVE_ECU-Nachricht ist ganzzahliges Vielfaches von 20 ms und jeder SENSOR_ECU-Nachricht von 10 ms; 0x200/0x201 == 40 ms | wahr |
| 10 | Abdeckung: jede Zeile des Signalbedarfs (P-01 bis P-07, D-01 bis D-06, S-01 bis S-07) ist genau einer Nachricht und einem Signal zugeordnet; keine Nachricht ausser den Radar-Platzhaltern ohne Zeile im Signalbedarf (SA-10) | vollstaendig |

Beispiel-Testfall (Schritt 3):

```python
def test_roundtrip_drive_command(db):
    msg = db.get_message_by_name("VCU_DRIVE_COMMAND")
    data = {"target_velocity": 0.15, "target_yaw_rate": -1.0, "enable": 1,
            "operating_mode": 3, "alive_counter": 7, "crc8": 0}
    frame = msg.encode(data, strict=True)
    back = msg.decode(frame)
    assert abs(back["target_velocity"] - 0.15) <= 0.001
    assert back["alive_counter"] == 7
```

### 3.7 Claude-Code-Auftrag K2 (aktualisiert gegenueber Plan v1)

```
Implementiere ausschliesslich Ausbaupaket K2 gemaess Phasenplan v2.1 und
Arbeitsplan K0–K2 (docs/plan/). Ergebnisse aus K1 (signalbedarf.md) haben
Vorrang vor den Vorschlaegen des Arbeitsplans; jede Abweichung im
DBC-Kommentarblock "K1 uebernommen / K2 vorgeschlagen" dokumentieren.

Ziel:
amr_vehicle.dbc als Single Source of Truth mit vier Nodes (PI_VCU,
DRIVE_ECU, SENSOR_ECU, RADAR_ECU), 13 Bestandsnachrichten exakt nach
Firmware, VCU_DRIVE_COMMAND und VCU_SENSOR_COMMAND mit alive_counter und
crc8, Zykluszeit und Sendeoffset je zyklischer Nachricht, Radar-Bereich
0x300–0x3F0 als Platzhalter; cantools-Integration (Python + C-Generierung);
T-09 can_dbc_check als pytest; P-CAN2-Vorlage und Skripte unter validation/.

Wichtig:
- bestehende CAN-IDs und Layouts nicht aendern; Layouts aus config_*.h
  lesen, nicht aus der Doku raten (0x150 und 0x1F0 pruefen)
- Kommando-IDs numerisch ueber 0x141
- Zykluszeiten als ganzzahlige Vielfache des Sender-Ticks (DRIVE_ECU 20 ms,
  SENSOR_ECU 10 ms): 0x200/0x201 = 40 ms, nicht 50 ms (Begruendung: S-A vorher,
  Arbeitsplan 3.2/3.4); Sendeoffsets nur spezifizieren, nicht in Firmware umsetzen
- keine Firmwarelogik aendern, keine Fahrbefehle ueber CAN, USB unveraendert,
  keine Fahrbewegung, keine Hardwarezustaende annehmen, kein Controllertausch
- generierte Dateien nicht handeditieren; Generator-Aufruf in Makefile/Skript
- Build/Lint/Tests ausfuehren; bei Fehlern stoppen
- Doku: docs/architecture/can-signalkatalog.md aus der DBC erzeugen,
  Stilregeln beachten (keine UTF-8-Umlaute in Markdown)

Zeige vor dem Commit:
1. finale DBC-Nachrichten und Signale (cantools dump),
2. Aenderungen gegenueber dem bisherigen CAN-Layout (erwartet: keine),
3. Ergebnisse von T-09 inkl. Buslast und Tick-Regel,
4. Liste "K1 uebernommen / K2 vorgeschlagen",
5. Diff-Zusammenfassung,
6. geplanten K2-Commit.
Noch nicht committen. Noch nicht taggen: der Tag k2-dbc-v1 wird erst nach
dokumentierter S-A-Vorher-Messung gesetzt (G0).
```

### 3.8 Ausgangsbedingung K2 (G0)

- T-09 gruen (alle 8 Schritte).
- P-CAN2 Teil A (S-A vorher) ausgefuellt und abgelegt unter validation/P-CAN2/.
- Git-Tag k2-dbc-v1.
- Entscheidung aus S-A (Abschnitt 4.5) im Phasenplan eingetragen (D-01 bestaetigt oder Tauschzeitpunkt verschoben).

## 4 S-A vorher – Messprotokoll P-CAN2 Teil A (10 min je Lastprofil, jetzt, mit Bestand)

### 4.1 Zweck und Regel

Zweck: Vorher-Messung fuer den Controllertausch (D-01) und Ursachenklaerung BA-01/BA-02 — Empfaengerseite (MCP2515: 2 RX-Puffer, Host-Latenz) oder physikalische Schicht (Abschluss, Abtastpunkt, Leitung). Keine Aenderung am System.

Regel (mcp251x-Treiber): Ein RX-Ueberlauf im MCP2515 (EFLG RX0OVR/RX1OVR) erhoeht `rx_over_errors` und `rx_errors`. Bus-Fehler (Stuffing, CRC, Form, ACK, Bit) erscheinen als CAN-Error-Frames und im `bus-error`-Zaehler von `ip -details -statistics`. Die beiden Zaehler trennen die Ursachen.

### 4.2 Voraussetzungen (Checkliste, alles Bestand)

| Nr. | Bedingung | Wie pruefen |
| --- | --- | --- |
| V1 | Firmware = Baseline-Commit auf beiden XIAO | Versionsstring im Heartbeat/Log, git tag |
| V2 | MCP2515 wie in K0 verdrahtet; Overlay-Zeile notiert | `grep mcp2515 /boot/firmware/config.txt` (Oszillator, Interrupt-GPIO) |
| V3 | can0 up, 1 Mbit/s, Abtastpunkt und Bit-Timing notiert | `ip -details link show can0` |
| V4 | Terminierung: Widerstand CAN_H–CAN_L stromlos | Multimeter, Soll 60 Ohm (zwei 120-Ohm-Abschluesse); 40 Ohm = drei Abschluesse, 120 Ohm = einer |
| V5 | Keine Fahrbewegung; Raeder frei oder am Boden, aber Motoren aus | Fahrkern im Failsafe (kein /cmd_vel) |
| V6 | candump/ip verfuegbar | `which candump ip` (can-utils, iproute2) |
| V7 | Skripte und Vorlage vorhanden | validation/P-CAN2/s_a_vorher.sh, s_a_analyse.py, P-CAN2-A.md (Aufruf ohne sudo) |

### 4.3 Lastprofile

| Profil | Pi-5-Last | Dauer | Zweck |
| --- | --- | --- | --- |
| A1 | Full Stack ohne Objekterkennung, Dashboard ohne Kamera-Overlay | 10 min | Referenz: Host-Latenz bei Normalbetrieb |
| A2 | Full Stack mit Objekterkennung (Hailo, Gemini, MJPEG-Overlay) aktiv im Dashboard | 10 min | Worst Case; Bezug zu BA-05 |

Beide Profile mit identischem CAN-Verkehr (Bestand: 194 Frames/s). Unterscheiden sich A1 und A2 im Verlust, ist die Host-Latenz beteiligt — unabhaengig vom Bus.

### 4.4 Ablauf je Profil

```
# 1. Zaehler vorher (macht das Skript, hier zur Kontrolle)
ip -details -statistics link show can0
cat /sys/class/net/can0/statistics/{rx_packets,rx_errors,rx_over_errors,rx_fifo_errors,rx_missed_errors,rx_dropped}

# 2. Messlauf 600 s (Profil A1 oder A2 als Label), ohne sudo, aus beliebigem Verzeichnis
./validation/P-CAN2/s_a_vorher.sh A1 600
# Ergebnis: validation/P-CAN2/<datum>_A1/{stats_before,stats_after}.{txt,json}, candump.log, meta.txt
# (candump.log ist per .gitignore vom Commit ausgenommen)

# 3. Auswertung
python3 validation/P-CAN2/s_a_analyse.py validation/P-CAN2/<datum>_A1
```

Das Skript zeichnet `candump -L "can0,0:0,#FFFFFFFF"` auf (Zeitstempel in us, Daten- und Error-Frames), liest die Zaehler vor und nach dem Lauf als Text und JSON und legt Overlay, Bit-Timing, Git-Commit und die `@version`-Strings der Firmware-Konfigurationen in meta.txt ab. Die Analyse liefert je ID: erwartete Frames (Rate x Dauer), empfangene Frames, Verlust in %, Zwischenankunftszeiten (Median, p99, max); die Zahl der Fenster mit 3 oder mehr Frames fuer die Fenster 300, 500, 1000 und 2000 us (Burst-Kandidaten fuer den 2-Puffer-Ueberlauf; Standardfenster 1000 us, weil die Zeitstempel Host-Lesezeiten sind und mindestens ca. 140 us auseinanderliegen); und die Zahl der Ueberlauf-Error-Frames (CAN_ERR_CRTL_RX_OVERFLOW) mit der Daten-ID, die unmittelbar davor ankam.

### 4.5 Entscheidungstabelle (nach beiden Profilen)

| Fall | Beobachtung | Schluss | Konsequenz |
| --- | --- | --- | --- |
| 1 | `rx_over_errors` steigt (Delta > 0), `bus-error` bleibt 0; Verlust konzentriert auf IDs, die in Bursts als 3. Frame ankommen (im Bestand vor allem 0x200 als 3. Frame des 100-ms-Bursts 0x210, 0x220, 0x200, 0x201 des Fahrkerns; daneben 0x200/0x201 hinter 0x130/0x131, wenn beide Sender zusammenfallen, Anhang A.2) | MCP2515 ist das Problem (2 RX-Puffer, Host-Latenz) | Tausch auf MCP2518FD in K3, wie geplant. Kein Schieben. D-01 bestaetigt |
| 2 | `rx_over_errors` bleibt 0, `bus-error` steigt; Verlust ueber IDs gleichverteilt; V4 nicht 60 Ohm oder Abtastpunkt 75 % vs. 80 % | Physikalische Schicht: Terminierung oder Abtastpunkt | Terminierung korrigieren, `sample-point 0.8`, Messung wiederholen. MCP2515 unschuldig: Tausch darf bis vor SV-04 (K6) geschoben werden, nicht weiter; K2 packt die Bestandsframes um (Kuer wird Pflicht), damit NFA-13 an G1 haelt |
| 3 | beide Zaehler 0, Verlust auf 0x200 trotzdem > 0,1 % | Dritte Ursache: Sender (TWAI-TX-Queue der Drive-ECU voll, Task-Timing), Messwerkzeug (candump-Puffer), oder Zaehlfehler in K0 | Erst finden, dann Hardware kaufen: TWAI-Alerts (TX-Fehler, Bus-Off) am Fahrkern loggen; candump mit groesserem Socket-Puffer; K0-Zaehlmethode gegen candump-Zaehlung pruefen |
| 4 | beide Zaehler steigen | Zwei Ursachen ueberlagert | Erst Fall 2 beheben, Messung wiederholen, dann Fall 1 bewerten |
| 5 | A2 deutlich schlechter als A1 | Host-Latenz unter Last ist beteiligt | Verstaerkt Fall 1; zusaetzlich Eingang fuer BA-05/NFA-15 |

Schwelle fuer "steigt": Delta >= 10 ueber 600 s. Schwelle fuer "Verlust": > 0,1 % je ID (NFA-13-Niveau); BA-01 lag bei 4,58 % auf 0x200 (erwartet: ca. 550 von 12 000 Frames in 10 min).

### 4.6 Protokollvorlage (validation/P-CAN2/P-CAN2-A.md)

Die Vorlage liegt unter validation/P-CAN2/P-CAN2-A.md; statische Felder (Overlay, Bit-Timing, Versionsstrings) sind mit Stand 2026-09-03 vorbelegt und bei der Messung zu bestaetigen.

| Feld | Wert |
| --- | --- |
| Datum / Uhrzeit | |
| Firmware-Commit Drive / Sensor | |
| Overlay-Zeile config.txt | |
| Bit-Timing (ip -details): bitrate, sample-point, tq, prop-seg, phase-seg1/2, sjw | |
| Widerstand CAN_H–CAN_L stromlos [Ohm] | |
| Profil A1: rx_packets, rx_errors, rx_over_errors, bus-error (Delta) | |
| Profil A1: Verlust je ID [%] (Tabelle aus s_a_analyse.py) | |
| Profil A1: Burst-Fenster (>= 3 Frames / 1000 us) | |
| Profil A2: dieselben Felder | |
| Fall nach 4.5 | |
| Entscheidung (Tauschzeitpunkt, K2-Umpacken ja/nein) | |
| Unterschrift / Freigabe | |

### 4.7 Nach der Messung

1. Protokoll unter validation/P-CAN2/ ablegen, im Phasenplan Abschnitt 8.1 (D-01) das Ergebnis eintragen.
2. K2-Tag k2-dbc-v1 setzen (G0 erfuellt).
3. Bei Fall 2: K2-Arbeitspaket "Umpacken" von Kuer auf Pflicht setzen, bevor der Tag gesetzt wird.
4. Teil B (nachher, MCP2518FD) laeuft in K3 mit demselben Skript und denselben Profilen.

---

Ohne Zwiebel-/Bloch-/Nguyen-Kim-Modul erstellt (Minimal-Set: Ehrlichkeit + Quellen-Traceability). Werte mit *(Vorschlag)* sind nicht aus K1 uebernommen.

## Anhang A: Befunde bei Uebernahme ins Repository (2026-09-03)

Alle Angaben nur lesend erhoben (git, Firmware-Quelltext, `ip`, `/sys`, passives `candump`). Keine Aenderung an Firmware, Verdrahtung oder Laufzeit; kein Flash, keine Fahrbewegung, kein CAN-TX.

### A.1 Zaehler und Treiberregel (Vorbefund zu BA-02, Regel 4.1)

| Groesse | Wert |
| --- | --- |
| `rx_errors` / `rx_over_errors` absolut auf can0 (seit Interface-Start) | 15419 / 15419; wenige Minuten spaeter 17262 / 17262; im Probelauf (A.2) 118838 -> 119038 in 20 s (10,0/s) |
| `bus-errors`, `arbit-lost`, `error-warn`, `error-pass`, `bus-off`, `re-started` | 0, 0, 0, 0, 0, 0; Zustand ERROR-ACTIVE |
| mcp251x-Treiber (raspberrypi/linux rpi-6.12.y, drivers/net/can/spi/mcp251x.c) | `rx_errors` wird ausschliesslich zusammen mit `rx_over_errors` bei EFLG RX0OVR / RX1OVR erhoeht; dabei Error-Frame mit `CAN_ERR_CRTL` und `CAN_ERR_CRTL_RX_OVERFLOW`; kein `rx_errors`-Inkrement fuer Busfehler (MERRF) |

Schluss: Die Regel in 4.1 ist belegt. BA-02 ist ein RX-Pufferueberlauf des MCP2515. Die Rate von 10/s entspricht der Rate des 100-ms-Bursts des Fahrkerns (A.2). Die Zuordnung zum Verlust auf 0x200 (BA-01) ist Gegenstand der 10-min-Messung, nicht dieses Vorbefunds.

### A.2 Sendemuster im Bestand und Probelauf

Quellen: `amr/mcu_firmware/drive_node/src/main.cpp:222-262` (controlTask, 20-ms-Takt), `amr/mcu_firmware/sensor_node/src/main.cpp:236-312` (sensorTask, 10-ms-Takt).

| Sender | Muster (aus dem Code) |
| --- | --- |
| DRIVE_ECU | alle 100 ms hintereinander 0x210, 0x220, 0x200, 0x201 (vier Frames back-to-back); dazwischen alle 50 ms 0x200, 0x201; 1 Hz zusaetzlich 0x2F0 |
| SENSOR_ECU | alle 20 ms 0x130, 0x131 back-to-back; 0x120 alle 50 ms; 0x110 alle 100 ms; 0x140 alle 500 ms; 0x1F0 1 Hz |
| beide | `twai_transmit`-Rueckgabe wird nicht ausgewertet (fire-and-forget), TWAI-Queues Standard (5 TX / 5 RX), tx_timeout 10 ms (Drive) / 3 ms (Sensor) |

Der deterministische Burst liegt damit **innerhalb** des Fahrkerns; die ECU-Takte sind nicht synchronisiert, ein Zusammenfallen mit 0x130/0x131 ist zufaellig. Fall 1 in 4.5 wurde entsprechend praezisiert.

Probelauf mit `s_a_vorher.sh PROBE 20` (20 s, kein Full-Stack, Host parallel unter Last durch andere Prozesse; **kein Messlauf im Sinne von 4.3**, Ordner geloescht):

| Beobachtung | Wert |
| --- | --- |
| Datenframes / mittlere Rate | 3754 / 188,0 Frames/s |
| Verlust je ID | 0x200: 30,58 % (277 von 399); alle uebrigen zehn periodischen IDs 0,00 % |
| Ueberlauf-Error-Frames im Log | 200 (= Delta `rx_over_errors`); Daten-ID unmittelbar davor: 0x220 171x, 0x201 29x |
| Nach 0x220 folgt | 0x200 78x, 0x201 122x (0x200 fehlt) |
| Zwischenankunft aufeinanderfolgender Frames am Host | min 141 us, p10 196 us, Median 531 us |
| Burst-Fenster >= 3 Frames | 300 us: 0; 500 us: 79; 1000 us: 467; 2000 us: 467 |

Der Ueberlauf trifft den dritten Frame des Fahrkern-Bursts (0x200 hinter 0x210, 0x220), waehrend 0x201 als vierter Frame nach dem Auslesen wieder Platz findet. Der Verlust liegt weit ueber den 4,58 % aus K0; ob das an der Host-Last des Probelaufs liegt (Fall 5), klaeren A1/A2. Die Zeitstempel sind Host-Lesezeiten ueber SPI (1 MHz), deshalb sind Bursts im 300-us-Fenster unsichtbar; das Auswerteskript nutzt 1000 us als Standard und gibt mehrere Fenster aus.

### A.3 Firmware-Layout (K1.1, K1.7; Quelle fuer Tabelle 3.2)

Quellen: `amr/mcu_firmware/sensor_node/include/twai_can.hpp:52-147`, `.../config_sensors.h:147-157`; `amr/mcu_firmware/drive_node/include/twai_can.hpp:48-112`, `.../config_drive.h:143-155`; `amr/scripts/can_bridge_node.py:278-287`.

| ID | Richtung | DLC | Belegung (alle Mehrbyte-Werte Little Endian per `memcpy`) |
| --- | --- | --- | --- |
| 0x110 | SENSOR → PI | 4 | range float32 m |
| 0x120 | SENSOR → PI, DRIVE (RX `id_cliff_rx`) | 1 | cliff uint8 0/1 |
| 0x130 | SENSOR → PI | 8 | ax, ay, az int16 x 0,001 m/s^2 (`ax * 1000.0f`, Kommentar "m/s^2 → mg (approx)"); gz int16 x 0,01 rad/s (`gz * 100.0f`) |
| 0x131 | SENSOR → PI | 4 | heading float32 rad |
| 0x140 | SENSOR → PI | 6 | voltage uint16 mV; current int16 mA; power uint16 mW |
| 0x141 | SENSOR → PI, DRIVE (RX `id_battery_shutdown_rx`) | 1 | shutdown uint8 0/1, Event |
| 0x150 | **PI → SENSOR** (`id_servo_cmd_rx`, `sensor_node/src/main.cpp:370-384`) | 4 | pan int16 x 0,1 Grad; tilt int16 x 0,1 Grad; Bridge begrenzt auf +/-1800, Firmware clampt auf `amr::servo::pan/tilt_limit_*`; Event, max. 10 Hz |
| 0x1F0 | SENSOR → PI | 8 | [0] flags bit0 imu_ok, bit1 ina260_ok, bit2 pca9685_ok, bit3 bat_shutdown, bit4 core1_ok; [1] uptime_s mod 256; [2-3] i2c_err, [4-5] servo_err, [6-7] servo_ok (uint16, saturiert 65535) |
| 0x200 | DRIVE → PI | 8 | x, y float32 m |
| 0x201 | DRIVE → PI | 8 | theta float32 rad; v_linear float32 m/s |
| 0x210 | DRIVE → PI | 8 | left, right float32 rad/s |
| 0x220 | DRIVE → PI | 4 | left, right int16 -255..255 |
| 0x2F0 | DRIVE → PI | 2 | [0] flags bit0 encoder_ok (fest 1), bit1 motor_ok (fest 1), bit2 pid_active, bit3 bat_shutdown oder can_battery_stop, bit4 core1_ok (fest 1), bit5 failsafe oder can_cliff_stop; [1] uptime_s mod 256 |

Abweichung zur Annahme in Version 1.0: 0x150 ist kein Servo-Status des Sensor-ECU, sondern das bestehende Servo-Kommando des Pi 5 (Redundanzpfad zu `/servo_cmd`). Damit existiert bereits eine Pi-Kommando-ID unterhalb von 0x400; K2 legt fest, ob 0x410 sie ersetzt oder ergaenzt (Abschnitt 3.3).

### A.4 cantools und float32 (Hinweis in 3.2)

Probelauf in einer temporaeren Umgebung (kein Repo-Eingriff): cantools 43.0.2, Mini-DBC mit drei float32-Signalen (`SIG_VALTYPE_ ... : 1`). `load_file(strict=True)` laedt; Python-Roundtrip `{x: 1.5, y: -2.25}` exakt (`0000c03f000010c0`). `cantools generate_c_source` erzeugt Strukturfelder vom Typ `float`, `..._encode(double) -> float` und `..._decode(float) -> double` als Cast, Pack/Unpack per `memcpy` in `uint32_t` und byteweise Little-Endian-Ablage. Das entspricht dem Firmware-`memcpy`. Ergebnis: Rohsignale als uint32 sind nicht noetig; Umpacken bleibt Kuer.

### A.5 Eingangspruefung K1 (Abschnitt 2, Stand signalbedarf.md und anforderungsliste-L1.md v1.1)

| Nr. | Ergebnis |
| --- | --- |
| K1.1 | Signalliste mit Rate, Genauigkeit, Wertebereich vorhanden (P-01..P-07, D-01..D-06, S-01..S-07); Skalierung und Bits bewusst nicht festgelegt → aus Firmware (A.3) |
| K1.2 | **In K1 vorhanden** (Abschnitt 13 der Anforderungsliste, SIA-11): SERIAL_REFERENCE, CAN_SHADOW, CAN_PRIMARY, SERVICE, FAILSAFE. Der Vorschlag "OFF/SERVICE/MANUAL/AUTONOMOUS/DEGRADED" entfaellt; Enum-Werte in K2 festlegen (P-03 nennt drei Werte fuer den Fahrbefehlspfad: Ruhe, Referenzpfad fuehrend, CAN-Pfad fuehrend) |
| K1.3 | Nicht vorhanden → Vorschlag 0x400-0x4F0 bleibt *(Vorschlag)* |
| K1.4 | **In K1 vorhanden**: Timeout CAN_PRIMARY 300 ms (15 ausbleibende Nachrichten bei 50 Hz), Reaktion FAILSAFE ohne Quellenwechsel; SIA-17 500 ms uebergeordnet. D-05 ("60 ms oder 500 ms") ist damit entschieden: 300 ms |
| K1.5 | Zuordnung vorhanden: SA-10 ↔ T-09 (K2), NFA-13/15/19 und SA-15 ↔ T-10 (K3), NFA-16/20 ↔ IT-10, SA-11/NFA-14 ↔ T-11, SIA-11..14/NFA-18 ↔ IT-11 (`can_mode_test`, nicht `can_failover_test`) |
| K1.6 | Vorhanden: P-07 Servo (bei Aenderung, max. 10 Hz, 0,1 Grad); P-04 Stellgroessenbegrenzung 0-100 % (1 Hz und bei Aenderung); LED-PWM ist in K1 **nicht** als Signalbedarf gelistet → D-07 bleibt offen. Zusaetzlich fordert K1 P-03 Betriebsmodus, P-05 Notstopp (10 Hz, Quellenkennung, Zaehler), P-06 Gateway-Lebenszeichen (10 Hz), D-05 Pfadstatus (5 Hz) und S-02 zyklische Wiederholung der Batterieabschaltung; die Kommandoframes in 3.3 decken nur P-01, P-02 und P-07 ab. K2 muss die uebrigen ergaenzen |
| K1.7 | Geklaert (A.3): 0x150 ist Pi → Sensor-ECU, DLC 4, pan/tilt int16 0,1 Grad |

### A.6 Anpassungen der Skripte gegenueber dem Entwurf

| Skript | Aenderung | Grund |
| --- | --- | --- |
| s_a_vorher.sh | Ergebnisordner neben dem Skript, unabhaengig vom Aufrufort; ohne sudo | Ergebnisse sonst root-eigen; candump und `/sys` benoetigen keine Root-Rechte |
| s_a_vorher.sh | `candump -L "can0,0:0,#FFFFFFFF"` | `-L` und `-e` schliessen sich aus; Fehlerfilter als Interface-Argument liefert die Ueberlauf-Error-Frames ins Log |
| s_a_vorher.sh | zusaetzlich `ip -json -details -statistics` als `stats_*.json`; meta.txt mit Git-Commit und `@version`-Strings | `bus-errors`/`re-started` stehen im Text in einer Kopf- und einer Wertezeile; der Regex des Entwurfs traf nie |
| s_a_analyse.py | Error-Frames getrennt gezaehlt, Ueberlauf-Frames der vorangehenden Daten-ID zugeordnet; Zaehler aus JSON mit Text-Fallback; Burst-Fenster 300/500/1000/2000 us, Standard 1000 us; ruff-konform | siehe A.2 |
| P-CAN2-A.md | Vorlage angelegt, statische Felder mit Stand 2026-09-03 vorbelegt | K2.8, V7 |
| .gitignore | `*/candump.log` | ca. 6 MB je 10-min-Lauf, pre-commit-Limit 500 kB |

### A.7 Ergebnis S-A vorher (2026-09-03, Protokoll validation/P-CAN2/P-CAN2-A.md)

| Profil | rx_over_errors (600 s) | bus_error | Verlust 0x200 | Verlust uebrige IDs | Host-Last (load avg) |
| --- | --- | --- | --- | --- | --- |
| A1 (ohne Objekterkennung) | 6674 | 0 | 21,51 % | 0x220 6,33 %, 0x131 0,77 %, 0x210 0,48 %, sonst 0 | 1,2-3,2 |
| A2 (mit Hailo, Gemini, Overlay) | 6001 | 0 | 27,35 % | alle 0 | 2,1-3,2 |

**Fall 1 bestaetigt** (4.5): Ueberlauf-Error-Frames folgen unmittelbar auf 0x220 bzw. 0x201, Verlust trifft 0x200 als 3. Frame des Fahrkern-Bursts; Terminierung 60 Ohm, keine Busfehler. Fall 5 nicht erfuellt (Gesamtverlust A1 3221, A2 3282 Frames). **Entscheidung D-01: Tausch auf MCP2518FD in K3, kein Schieben; Umpacken bleibt Kuer.** Die Sendeoffsets aus 3.4 gehoeren unabhaengig davon in K4. Offen: Verlust liegt weit ueber K0 (4,58 %), Ursache der Differenz nicht geklaert. Der Eintrag in Phasenplan 8.1 (D-01) liegt mit Phasenplan v2.2 vor (docs/plan/phasenplan-v2.md).

Ausgangsbedingung G0 (3.8): P-CAN2 Teil A abgelegt, Entscheidung getroffen, T-09 gruen (Anhang A.8); offen ist allein der Tag k2-dbc-v1.

### A.8 Umsetzungsstand K2 (2026-09-03)

Alle Artefakte sind erstellt; Firmware, CAN-Bruecke, Launch-Dateien, Docker-Image
und Verdrahtung sind unveraendert. Kein Flash, kein CAN-TX, keine Fahrbewegung.

| Artefakt | Pfad | Bemerkung |
| --- | --- | --- |
| Signaldatenbank | `hardware/can-bus/amr_vehicle.dbc` | 28 Nachrichten: 13 Bestand, 5 neu, 10 Radar-Platzhalter; vier Knoten |
| Generierter C-Code | `amr/mcu_firmware/common/can/amr_vehicle.{h,c}` | aus der DBC erzeugt, nicht handeditiert; Firmware nutzt ihn erst ab K3/K4 |
| Generator | `scripts/can_generate.sh`, `scripts/can_signalkatalog.py`, `scripts/can_model.py` | `--check` vergleicht Generat gegen eingecheckten Stand |
| E2E-Referenz | `amr/scripts/can_e2e.py` | CRC-8 SAE J1850 und Alive-Counter |
| T-09 | `tests/test_can_dbc_check.py`, `tests/conftest.py` | 65 Testfaelle, zehn Schritte |
| Signalkatalog | `docs/architecture/can-signalkatalog.md` | erzeugt, in mkdocs eingehaengt |
| Werkzeuge | `requirements-dev.txt` | cantools 43.0.2, pytest; Host-venv, Docker-Image unveraendert |

Ergebnisse: Buslast rechnerisch 3,94 % bei 1 Mbit/s (NFA-14 Grenze 30 %);
Tick-Regel erfuellt (0x200/0x201 = 40 ms); alle Bestandslayouts unveraendert
gegenueber Anhang A.3; jede Zeile des Signalbedarfs ist genau einer Nachricht
zugeordnet (SA-10).

Abweichungen vom Entwurf dieses Arbeitsplans, jeweils mit K1 begruendet:

| Punkt | Entwurf | Umsetzung | Grund |
| --- | --- | --- | --- |
| Umfang | zwei Kommandoframes | zusaetzlich 0x160, 0x170, 0x230 und 0x141 zyklisch | K1 hat Vorrang; SA-10 fordert vollstaendige Abdeckung des Signalbedarfs |
| Kennungen Notstopp und Lebenszeichen | Bereich 0x400–0x4F0 | 0x160 und 0x170 | signalbedarf.md 7.4: Sicherheit vor Diagnose |
| Betriebsmodus-Enum | OFF/SERVICE/MANUAL/AUTONOMOUS/DEGRADED | K1-Modi mit Werten 0 bis 4 | Anforderungsliste Abschnitt 13.1 |
| t_timeout (D-05 des Phasenplans) | 60 ms oder 500 ms | 300 ms | Anforderungsliste Abschnitt 13.3 |
| T-09 | acht Schritte | zehn Schritte (Tick-Regel, K1-Abdeckung) | Ergebnis S-A vorher und SA-10 |
| Motor-Limit | offen (D-07) | `motor_limit_percent` in 0x400 | K1 P-04 |
| LED-PWM | offen (D-07) | weiterhin offen, keine Kennung vergeben | in K1 nicht als Signalbedarf gelistet |

Offen zu G0: allein der Tag `k2-dbc-v1` (nach Freigabe). T-09 ist gruen, P-CAN2
Teil A liegt unter `validation/P-CAN2/`, und die D-01-Entscheidung steht in
Phasenplan v2.2 Abschnitt 8.1.
