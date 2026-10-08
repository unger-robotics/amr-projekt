# Arbeitsplan K0–K2 und S-A (vorher)

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Arbeitsplan zu Phasenplan v2.1 (Pakete K0, K1, K2; Spike S-A Teil A) |
| Version | 1.1 (Entwurf) — nach S-A vorher (2026-09-03): D-01 bestaetigt, BA-01/BA-02 aktualisiert, Zykluszeit 0x200/0x201 = 40 ms |
| Datum | 2026-09-03 |
| Autor | Jan (Entwurf erstellt mit KI-Assistent, Freigabe offen) |
| Bezug | docs/plan/phasenplan-v2.md (v2.1), Anforderungsliste L1 v1.0, docs/firmware/sensors-actuators.md, docs/architecture/signalbedarf.md (K1) |
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
| BA-01 | 0x200-Frameverlust: 4,58 % (K0); S-A vorher: 21,5 % (A1) / 27,4 % (A2), dt max 640 ms — K0-Wert untererfasst | Ursache geklaert (Fall 1, MCP2515-RX-Ueberlauf); Behebung K3/G1 | P-CAN2 Teil A erledigt, Teil B in K3, NFA-13 |
| BA-02 | rx_errors == rx_over_errors (Delta 6674/6001 je 10 min), bus_error 0 → derselbe Befund wie BA-01 | erledigt (S-A vorher) | P-CAN2 Teil A |
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
| K2.4 | Zykluszeit und Sendeoffset je zyklischer Nachricht (Abschnitt 3.4) — **nur Spezifikation**, Firmware setzt sie erst in K3/K4 um | Sendeplan in der DBC | T-09 Schritt 4 |
| K2.5 | Radar-Reservierung 0x300–0x3F0 als Platzhalter (Abschnitt 3.5) | Bereich belegt, keine Ueberlappung | T-09 Schritt 2 |
| K2.6 | cantools-Integration: Python-Zugriff (Pi), C-Codegenerierung (ESP32) in mcu_firmware/common/can/ — generierte Dateien nicht handeditieren | Header/Sourcen aus DBC | T-09 Schritt 5 |
| K2.7 | T-09 can_dbc_check als pytest (Abschnitt 3.6) | gruener Lauf in CI/lokal | — |
| K2.8 | P-CAN2 vorbereitet: Protokollvorlage + Skripte (Abschnitt 4) liegen unter validation/ | Vorlage, s_a_vorher.sh, s_a_analyse.py | Probelauf 60 s |
| K2.9 | Doku: docs/architecture/can-signalkatalog.md aus der DBC generiert (cantools dump) | Seite in mkdocs | Review |

Nicht in K2: Firmwarelogik aendern, Fahrbefehle ueber CAN aktivieren, USB abschalten, Fahrbewegung, Hardwarezustaende annehmen, Controllertausch.

### 3.2 Bestandsnachrichten (Quelle: docs/firmware/sensors-actuators.md; Layout-Details aus config_*.h bestaetigen)

Byte-Order: Intel (Little Endian) laut Firmware-Doku ("float32 LE"). Werte mit "?" sind aus config_*.h zu bestaetigen.

| ID | Name (Vorschlag) | Sender | Rate | DLC | Signale (Typ, Einheit) |
| --- | --- | --- | --- | --- | --- |
| 0x110 | SENSOR_RANGE | SENSOR_ECU | 10 Hz | 4 | range float32 m |
| 0x120 | SENSOR_CLIFF | SENSOR_ECU | 20 Hz | 1 | cliff uint8 (0 OK, 1 Cliff) |
| 0x130 | SENSOR_IMU_ACC | SENSOR_ECU | 50 Hz | 8 | ax, ay, az int16 mg; gz int16 (Einheit ?) |
| 0x131 | SENSOR_IMU_HEADING | SENSOR_ECU | 50 Hz | 4 | heading float32 (rad ?) |
| 0x140 | SENSOR_BATTERY | SENSOR_ECU | 2 Hz | 6 | voltage uint16 mV; current int16 mA; power uint16 mW |
| 0x141 | SENSOR_BATTERY_SHUTDOWN | SENSOR_ECU | Event | 1 | shutdown uint8 (0 OK, 1 Shutdown) |
| 0x150 | SENSOR_SERVO_STATUS | SENSOR_ECU | ? | ? | pan, tilt (? — K1.7) |
| 0x1F0 | SENSOR_HEARTBEAT | SENSOR_ECU | 1 Hz | 8 | flags, uptime, I2C-/Servo-Diagnostik (Bitbelegung ?) |
| 0x200 | DRIVE_ODOM_XY | DRIVE_ECU | 20 Hz nominell; Ist 40/60-ms-Wechsel (tick-quantisiert) → DBC 40 ms | 8 | x, y float32 m |
| 0x201 | DRIVE_ODOM_HEADING_SPEED | DRIVE_ECU | 20 Hz nominell; Ist wie 0x200 → DBC 40 ms | 8 | yaw float32 rad; v_linear float32 m/s |
| 0x210 | DRIVE_WHEEL_SPEED | DRIVE_ECU | 10 Hz | 8 | wheel_l, wheel_r float32 rad/s |
| 0x220 | DRIVE_MOTOR_PWM | DRIVE_ECU | 10 Hz | 4 | pwm_l, pwm_r int16 |
| 0x2F0 | DRIVE_HEARTBEAT | DRIVE_ECU | 1 Hz | 2 | flags uint8; uptime_mod256 uint8 |

Zykluszeit-Regel (aus S-A vorher): Zykluszeiten in der DBC sind ganzzahlige Vielfache des Sender-Ticks. Der Fahrkern arbeitet mit 20 ms; 50 ms (2,5 Ticks) fuehren zum gemessenen 40/60-ms-Wechsel (Median 59,5 ms bei 12 000 Frames/600 s). 0x200/0x201 werden daher mit 40 ms (25 Hz) spezifiziert — erfuellt NFA-03 Soll 20 Hz. Umsetzung in der Drive-Firmware in K4; bis dahin dokumentiert die DBC den Sollwert, T-09 prueft die Regel.

Rechnerische Buslast des Bestands (ohne Stuffing, 11-Bit-ID): ca. 18 kbit/s = 1,8 % bei 1 Mbit/s; 194 Frames/s (gemessen: 1,75 %, 188,6 Frames/s). Mit beiden Kommandoframes (50 Hz, 10 Hz) ca. 2,5 %. T-09 rechnet das aus der DBC nach.

Hinweis Codegenerierung: Falls der cantools-C-Generator float32-Signale (SIG_VALTYPE_) nicht unterstuetzt, werden die Bestandsframes in K2 zusaetzlich als uint32-Rohsignale mit Kommentar modelliert; das Umpacken auf skalierte Integer (Kuer laut Phasenplan) wuerde dann fuer die Codegenerierung Pflicht. Vor K2.6 pruefen.

### 3.3 Kommandoframes (Vorschlag, falls K1 nichts vorgibt)

ID-Regel: numerisch ueber 0x120 und 0x141, damit Cliff und Shutdown die Arbitrierung gewinnen. Vorschlag: eigener PI_VCU-Bereich 0x400–0x4F0 (niedrigste Prioritaet auf dem Bus — bei 2 % Buslast ohne praktische Auswirkung, Kfz-Lehre: Notstopp vor Kommando).

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

Offen (D-07): LED-PWM und Motor-Limit aus /hardware_cmd — in VCU_DRIVE_COMMAND reserved-Bits oder eigener Frame 0x420.

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
| DRIVE_ECU | 0x200 | 40 ms (2 Ticks) | 0 ms |
| DRIVE_ECU | 0x201 | 40 ms (2 Ticks) | 0 ms — gleicher Tick wie 0x200, damit x/y und yaw/v zusammengehoeren; 2 Frames back-to-back sind erlaubt |
| DRIVE_ECU | 0x210 | 80 ms (4 Ticks) *(Vorschlag; 12,5 Hz statt 10 Hz)* | 20 ms — ungerader Tick, trifft nie auf das Odom-Paar |
| DRIVE_ECU | 0x220 | 80 ms (4 Ticks) *(Vorschlag)* | 60 ms — ungerader Tick |
| DRIVE_ECU | 0x2F0 | 1000 ms (50 Ticks) | 60 ms — ungerader Tick |
| PI_VCU | 0x400 | 20 ms | 0 ms |
| PI_VCU | 0x410 | 100 ms | 5 ms |

Alternative zu 80 ms fuer 0x210/0x220: 100 ms beibehalten und den dann jeden zweiten Zyklus entstehenden 4-Frame-Burst dem MCP2518FD ueberlassen; die Regel "max. 2 Frames je Tick" waere dann eine Soll-, keine Muss-Regel. Entscheidung in K2 mit K1 abgleichen (D-07-Umfeld).

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
| 8 | ID-Regel: alle PI_VCU-IDs numerisch > 0x141 | wahr |
| 9 | Tick-Regel: GenMsgCycleTime jeder DRIVE_ECU-Nachricht ist ganzzahliges Vielfaches von 20 ms; 0x200/0x201 == 40 ms | wahr |

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
- Zykluszeiten als ganzzahlige Vielfache des Sender-Ticks (DRIVE_ECU 20 ms):
  0x200/0x201 = 40 ms, nicht 50 ms (Begruendung: S-A vorher, Arbeitsplan 3.2/3.4);
  Sendeoffsets nur spezifizieren, nicht in Firmware umsetzen
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
| V7 | Skripte vorhanden | validation/P-CAN2/s_a_vorher.sh, s_a_analyse.py |

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

# 2. Messlauf 600 s (Profil A1 oder A2 als Label)
sudo ./s_a_vorher.sh A1 600
# Ergebnis: validation/P-CAN2/<datum>_A1/{stats_before.txt,stats_after.txt,candump.log,meta.txt}

# 3. Auswertung
python3 s_a_analyse.py validation/P-CAN2/<datum>_A1
```

Das Skript zeichnet `candump -L can0` (Zeitstempel in us) auf, liest die Zaehler vor und nach dem Lauf und legt die Overlay-/Bit-Timing-Angaben in meta.txt ab. Die Analyse liefert je ID: erwartete Frames (Rate x Dauer), empfangene Frames, Verlust in %, Zwischenankunftszeiten (Median, p99, max), und die Zahl der Fenster, in denen 3 oder mehr Frames innerhalb 300 us am Pi ankamen (Burst-Kandidaten fuer den 2-Puffer-Ueberlauf).

### 4.5 Entscheidungstabelle (nach beiden Profilen)

| Fall | Beobachtung | Schluss | Konsequenz |
| --- | --- | --- | --- |
| 1 | `rx_over_errors` steigt (Delta > 0), `bus-error` bleibt 0; Verlust konzentriert auf IDs, die in Bursts als 3. Frame ankommen (0x200/0x201 hinter 0x130/0x131) | MCP2515 ist das Problem (2 RX-Puffer, Host-Latenz) | Tausch auf MCP2518FD in K3, wie geplant. Kein Schieben. D-01 bestaetigt |
| 2 | `rx_over_errors` bleibt 0, `bus-error` steigt; Verlust ueber IDs gleichverteilt; V4 nicht 60 Ohm oder Abtastpunkt 75 % vs. 80 % | Physikalische Schicht: Terminierung oder Abtastpunkt | Terminierung korrigieren, `sample-point 0.8`, Messung wiederholen. MCP2515 unschuldig: Tausch darf bis vor SV-04 (K6) geschoben werden, nicht weiter; K2 packt die Bestandsframes um (Kuer wird Pflicht), damit NFA-13 an G1 haelt |
| 3 | beide Zaehler 0, Verlust auf 0x200 trotzdem > 0,1 % | Dritte Ursache: Sender (TWAI-TX-Queue der Drive-ECU voll, Task-Timing), Messwerkzeug (candump-Puffer), oder Zaehlfehler in K0 | Erst finden, dann Hardware kaufen: TWAI-Alerts (TX-Fehler, Bus-Off) am Fahrkern loggen; candump mit groesserem Socket-Puffer; K0-Zaehlmethode gegen candump-Zaehlung pruefen |
| 4 | beide Zaehler steigen | Zwei Ursachen ueberlagert | Erst Fall 2 beheben, Messung wiederholen, dann Fall 1 bewerten |
| 5 | A2 deutlich schlechter als A1 | Host-Latenz unter Last ist beteiligt | Verstaerkt Fall 1; zusaetzlich Eingang fuer BA-05/NFA-15 |

Schwelle fuer "steigt": Delta >= 10 ueber 600 s. Schwelle fuer "Verlust": > 0,1 % je ID (NFA-13-Niveau); BA-01 lag bei 4,58 % auf 0x200 (erwartet: ca. 550 von 12 000 Frames in 10 min).

### 4.6 Protokollvorlage (validation/P-CAN2/P-CAN2-A.md)

| Feld | Wert |
| --- | --- |
| Datum / Uhrzeit | |
| Firmware-Commit Drive / Sensor | |
| Overlay-Zeile config.txt | |
| Bit-Timing (ip -details): bitrate, sample-point, tq, prop-seg, phase-seg1/2, sjw | |
| Widerstand CAN_H–CAN_L stromlos [Ohm] | |
| Profil A1: rx_packets, rx_errors, rx_over_errors, bus-error (Delta) | |
| Profil A1: Verlust je ID [%] (Tabelle aus s_a_analyse.py) | |
| Profil A1: Burst-Fenster (>= 3 Frames / 300 us) | |
| Profil A2: dieselben Felder | |
| Fall nach 4.5 | |
| Entscheidung (Tauschzeitpunkt, K2-Umpacken ja/nein) | |
| Unterschrift / Freigabe | |

### 4.7 Ergebnis Teil A (2026-09-03) — erledigt

| Feld | A1 (ohne Objekterkennung) | A2 (mit Objekterkennung) |
| --- | --- | --- |
| Datenframes / 600 s | 113 179 (188,6/s) | 113 118 (188,5/s) |
| rx_over_errors Delta | 6674 (== rx_errors Delta) | 6001 (== rx_errors Delta) |
| bus_error, arbitration_lost, error_passive Delta | 0 / 0 / 0 | 0 / 0 / 0 |
| Verlust 0x200 | 21,51 % (dt max 640 ms) | 27,35 % (dt max 100 ms) |
| Verlust uebrige IDs | 0x220 6,33 %, 0x131 0,77 %, 0x210 0,48 %, Rest 0 | alle 0 |
| Gesamtverlust von 116 400 erwarteten Frames | 3221 | 3282 |
| Bursts >= 3 Frames / 1000 us | 16 101 | 13 833 |
| Datenframe unmittelbar vor Overflow-Frame | 0x220 3351, 0x201 2401, 0x200 471 | 0x220 4394, 0x201 1606 |
| Buslast (rechnerisch) | 1,75 % | 1,75 % |
| Fall nach 4.5 | 1 (mit 5: Host-Last verschiebt, aendert Summe nicht) | 1 |
| Entscheidung | MCP2518FD in K3, kein Schieben; K2-Umpacken bleibt Kuer; Zykluszeit 0x200/0x201 = 40 ms | — |
| Noch nachzutragen | V4 Widerstand CAN_H–CAN_L stromlos; Bit-Timing-Zeile aus meta.txt beider Laeufe | — |

Hinweise zur Lesart: rx_over_errors zaehlt etwa doppelt so oft wie Frames verloren gehen (Treiber zaehlt vermutlich RX0OVR und RX1OVR getrennt) — Referenzgroesse fuer den Nachher-Vergleich ist der Verlust je ID aus dem candump, nicht der Zaehler. rx_dropped (2 267 223) ist ohne Delta und Altlast.

### 4.8 Nach der Messung

1. Protokoll unter validation/P-CAN2/ ablegen (Auswertungen A1/A2 liegen vor); V4 und Bit-Timing nachtragen. Phasenplan Abschnitt 8.1 (D-01): erledigt in v2.2.
2. K2-Tag k2-dbc-v1 setzen (G0 erfuellt).
3. Fall 2 ist nicht eingetreten: K2-Arbeitspaket "Umpacken" bleibt Kuer.
4. Teil B (nachher, MCP2518FD) laeuft in K3 mit demselben Skript und denselben Profilen.

---

Ohne Zwiebel-/Bloch-/Nguyen-Kim-Modul erstellt (Minimal-Set: Ehrlichkeit + Quellen-Traceability). Werte mit *(Vorschlag)* sind nicht aus K1 uebernommen.
