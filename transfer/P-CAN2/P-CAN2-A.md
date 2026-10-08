# Messprotokoll P-CAN2 Teil A: S-A vorher (Bestand, MCP2515)

Vorlage nach `docs/plan/arbeitsplan-k0-k2-s-a.md`, Abschnitt 4.6. Zwei Lastprofile
(A1 ohne, A2 mit Objekterkennung), je 10 min, System unveraendert. Keine Fahrbewegung,
kein CAN-TX durch die Messwerkzeuge.

Felder mit "Stand 03.09.2026" sind bei der Uebernahme der Vorlage aus dem laufenden
System gelesen worden und bei der Messung zu bestaetigen (Skript schreibt sie erneut in
`meta.txt`).

## Ablauf je Profil

```bash
# Zaehler vorher zur Kontrolle (macht das Skript auch)
ip -details -statistics link show can0

# Messlauf 600 s, ohne sudo; Ergebnis: validation/P-CAN2/<datum>_A1/
./validation/P-CAN2/s_a_vorher.sh A1 600

# Auswertung (Markdown auf stdout, Tabellen unten eintragen)
python3 validation/P-CAN2/s_a_analyse.py validation/P-CAN2/<datum>_A1
```

## Protokoll

| Feld | Wert |
| --- | --- |
| Datum / Uhrzeit | 2026-09-03, A1 19:56-20:06, A2 20:14-20:24 |
| Pruefer | Jan Unger (Messlauf ausgefuehrt mit Claude Code) |
| Firmware-Commit Drive / Sensor (geflashter Stand, K0.1) | |
| Versionsstrings im Repo (`@version`) | config_drive.h 4.0.0, config_sensors.h 3.0.0, Commit 18cc7bb (Stand 03.09.2026) |
| Overlay-Zeile config.txt | `dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25,spimaxfrequency=1000000` (Stand 03.09.2026) |
| Bit-Timing (`ip -details`): bitrate, sample-point, tq, prop-seg, phase-seg1/2, sjw | 1000000, 0.750, 125, 2, 3/2, 1 (Stand 03.09.2026) |
| Widerstand CAN_H-CAN_L stromlos [Ohm] (Soll 60) | ca. 60 (Multimeter, vor dem Start gemessen) |
| Profil A1: Launch-Argumente | `full_stack.launch.py use_dashboard:=True use_rviz:=False` (SLAM, Nav2, Cliff-Safety, Dashboard-Bridge; kein Browser-Client verbunden); Fahrzeug aufgebockt, Raeder frei, kein /cmd_vel; Host-Last 1,2-3,2 (load avg 1 min), CPU 10-25 % |
| Profil A1: rx_packets, rx_errors, rx_over_errors, bus_error, restarts (Delta) | 113179, 6674, 6674, 0, 0 (600 s; alle uebrigen Buszaehler 0, Zustand ERROR-ACTIVE) |
| Profil A1: Verlust je ID [%] (Tabelle aus s_a_analyse.py) | 0x200 21,51; 0x220 6,33; 0x131 0,77; 0x210 0,48; alle uebrigen 0,00 (Tabelle unten) |
| Profil A1: Burst-Fenster (>= 3 Frames / 1000 us) und IDs als 3. Frame | 16101 Fenster; 3. Frame: 0x131 7915, 0x201 6805, 0x200 4839, 0x210 1656, 0x220 1203 |
| Profil A1: Ueberlauf-Error-Frames im Log und Daten-ID davor | 6674 (= Delta rx_over_errors); davor 0x220 3351, 0x201 2401, 0x200 471, 0x131 340, 0x210 108 |
| Profil A2: Launch-Argumente | `full_stack.launch.py use_dashboard:=True use_camera:=True use_vision:=True use_rviz:=False`; zusaetzlich `host_hailo_runner.py` (Host, 5 Hz Detektionen) und Vite-Dev-Server; ein Browser-Client (Mac) mit Kamerabild und AI-Schalter an, Gemini-Analysen (gemini-2.5-flash) durchgehend; Fahrzeug aufgebockt, kein /cmd_vel; Host-Last 2,1-3,2 (load avg 1 min), CPU 13-40 % |
| Profil A2: rx_packets, rx_errors, rx_over_errors, bus_error, restarts (Delta) | 113124, 6001, 6001, 0, 0 (600 s; `error_warning` und `error_passive` stehen absolut auf 1, Delta 0: je ein Ereignis zwischen A1 und A2 waehrend Stack-Neustart und DTR/RTS-Reset der ESP32) |
| Profil A2: Verlust je ID [%] | 0x200 27,35; alle uebrigen zehn periodischen IDs 0,00 (Tabelle unten) |
| Profil A2: Burst-Fenster (>= 3 Frames / 1000 us) und IDs als 3. Frame | 13833 Fenster; 3. Frame: 0x131 7812, 0x201 6000, 0x200 2718 |
| Profil A2: Ueberlauf-Error-Frames im Log und Daten-ID davor | 6000 (Delta rx_over_errors 6001); davor 0x220 4394, 0x201 1606 |
| Fall nach Arbeitsplan 4.5 | **Fall 1** (MCP2515): `rx_over_errors` steigt in beiden Profilen um ca. 10/s, `bus-error` bleibt 0, alle Ueberlauf-Error-Frames tragen CAN_ERR_CRTL_RX_OVERFLOW und folgen unmittelbar auf 0x220 bzw. 0x201, der Verlust konzentriert sich auf 0x200 als 3. Frame des 100-ms-Bursts 0x210, 0x220, 0x200, 0x201 des Fahrkerns. Fall 2 ausgeschlossen (60 Ohm, 0 Busfehler). Fall 5 nicht erfuellt: Gesamtverlust A2 (3282 Frames) entspricht A1 (3221 Frames); in A2 liegt er vollstaendig auf 0x200, in A1 verteilt auf 0x200, 0x220, 0x131, 0x210 |
| Entscheidung (Tauschzeitpunkt D-01, K2-Umpacken ja/nein) | D-01 bestaetigt: Tausch auf MCP2518FD in K3, kein Schieben. Umpacken der Bestandsframes bleibt Kuer. Zusaetzlich: die Sendeoffsets aus Arbeitsplan 3.4 (0x210/0x220 gegen 0x200/0x201 versetzt) entschaerfen den 4-Frame-Burst unabhaengig vom Controller und gehoeren in K4. Eintrag in Phasenplan 8.1 steht aus (Phasenplan noch nicht im Repository) |
| Unterschrift / Freigabe | offen |

## Vorbefund (03.09.2026, vor der Messung, nur lesend)

| Groesse | Wert |
| --- | --- |
| `rx_errors` / `rx_over_errors` absolut (seit Interface-Start) | 15419 / 15419, wenige Minuten spaeter 17262 / 17262 (ca. 10/s) |
| `bus-errors`, `error-warn`, `error-pass`, `bus-off`, `re-started` | 0, 0, 0, 0, 0; Zustand ERROR-ACTIVE |
| Treiberregel mcp251x (Kernel rpi-6.12.y) | `rx_errors` wird ausschliesslich zusammen mit `rx_over_errors` bei EFLG RX0OVR/RX1OVR erhoeht; dabei Error-Frame mit CAN_ERR_CRTL_RX_OVERFLOW |

Schluss aus dem Vorbefund: BA-02 (steigende `rx_errors` bei null Busfehlern) ist ein
RX-Pufferueberlauf des MCP2515. Ob der Ueberlauf den Verlust auf 0x200 (BA-01) erklaert,
klaert erst die Zuordnung Ueberlauf-Frame zu Burst-ID aus dieser Messung.

## Ergebnisse (Ausgabe von s_a_analyse.py einfuegen)

### Profil A1

Rohdaten: `20260903_1956_A1/` (stats_before/after, meta.txt, hostlast.txt; candump.log lokal, nicht versioniert).

Datenframes gesamt: 113179, Messdauer aus Log: 600.0 s, mittlere Rate: 188.6 Frames/s

## Zaehler-Deltas (nachher - vorher)

| Zaehler | vorher | nachher | Delta |
| --- | --- | --- | --- |
| rx_packets | 2306544 | 2419723 | 113179 |
| rx_errors | 129299 | 135973 | 6674 |
| rx_over_errors | 129299 | 135973 | 6674 |
| rx_fifo_errors | 0 | 0 | 0 |
| rx_missed_errors | 0 | 0 | 0 |
| rx_dropped | 2267223 | 2267223 | 0 |
| bus_error | 0 | 0 | 0 |
| arbitration_lost | 0 | 0 | 0 |
| error_warning | 0 | 0 | 0 |
| error_passive | 0 | 0 | 0 |
| bus_off | 0 | 0 | 0 |
| restarts | 0 | 0 | 0 |

## Je ID: Empfang, Verlust, Zwischenankunftszeit

| ID | Soll [Hz] | erwartet | empfangen | Verlust [%] | dt Median [ms] | dt p99 [ms] | dt max [ms] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0x110 | 10 | 6000 | 6000 | 0.00 | 100.0 | 110.0 | 110.1 |
| 0x120 | 20 | 12000 | 12000 | 0.00 | 50.0 | 50.1 | 50.1 |
| 0x130 | 50 | 29999 | 30001 | 0.00 | 20.0 | 20.2 | 20.3 |
| 0x131 | 50 | 29999 | 29768 | 0.77 | 20.0 | 20.2 | 40.3 |
| 0x140 | 2 | 1200 | 1200 | 0.00 | 500.0 | 500.3 | 500.5 |
| 0x1F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.3 | 1000.7 |
| 0x200 | 20 | 12000 | 9419 | 21.51 | 59.5 | 100.1 | 640.3 |
| 0x201 | 20 | 12000 | 12000 | 0.00 | 59.3 | 59.8 | 60.0 |
| 0x210 | 10 | 6000 | 5971 | 0.48 | 100.0 | 100.2 | 400.2 |
| 0x220 | 10 | 6000 | 5620 | 6.33 | 100.0 | 300.0 | 1700.0 |
| 0x2F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.2 | 1000.3 |

Rechnerische Buslast (ohne Stuffing): 1.75 % bei 1 Mbit/s

## Burst-Fenster (>= 3 Frames innerhalb Fenster)

| Fenster [us] | Anzahl |
| --- | --- |
| 300 | 0 |
| 500 | 5099 |
| 1000 | 16101 |
| 2000 | 19146 |

| ID als 3. oder spaeterer Frame im Burst (1000 us) | Anzahl |
| --- | --- |
| 0x131 | 7915 |
| 0x201 | 6805 |
| 0x200 | 4839 |
| 0x210 | 1656 |
| 0x220 | 1203 |
| 0x2F0 | 199 |
| 0x140 | 26 |
| 0x1F0 | 10 |

## Error-Frames im Log: 6674, davon RX-Ueberlauf (CAN_ERR_CRTL_RX_OVERFLOW): 6674

| Daten-ID unmittelbar vor dem Ueberlauf-Frame | Anzahl |
| --- | --- |
| 0x220 | 3351 |
| 0x201 | 2401 |
| 0x200 | 471 |
| 0x131 | 340 |
| 0x210 | 108 |
| 0x2F0 | 2 |
| 0x130 | 1 |

Lesart: Faellt der Verlust genau auf die IDs, die im Burst als 3. Frame ankommen, und steigt rx_over_errors (Ueberlauf-Error-Frames im Log), ist es Fall 1 (MCP2515). Steigt bus_error, Fall 2. Beides 0 bei Verlust > 0,1 %: Fall 3.

### Profil A2

Rohdaten: `20260903_2014_A2/` (stats_before/after, meta.txt, hostlast.txt; candump.log lokal, nicht versioniert).

Datenframes gesamt: 113118, Messdauer aus Log: 600.0 s, mittlere Rate: 188.5 Frames/s

## Zaehler-Deltas (nachher - vorher)

| Zaehler | vorher | nachher | Delta |
| --- | --- | --- | --- |
| rx_packets | 2507679 | 2620803 | 113124 |
| rx_errors | 140601 | 146602 | 6001 |
| rx_over_errors | 140601 | 146602 | 6001 |
| rx_fifo_errors | 0 | 0 | 0 |
| rx_missed_errors | 0 | 0 | 0 |
| rx_dropped | 2267223 | 2267223 | 0 |
| bus_error | 0 | 0 | 0 |
| arbitration_lost | 0 | 0 | 0 |
| error_warning | 1 | 1 | 0 |
| error_passive | 1 | 1 | 0 |
| bus_off | 0 | 0 | 0 |
| restarts | 0 | 0 | 0 |

## Je ID: Empfang, Verlust, Zwischenankunftszeit

| ID | Soll [Hz] | erwartet | empfangen | Verlust [%] | dt Median [ms] | dt p99 [ms] | dt max [ms] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0x110 | 10 | 6000 | 6000 | 0.00 | 100.0 | 110.1 | 120.0 |
| 0x120 | 20 | 12000 | 12000 | 0.00 | 50.0 | 50.1 | 50.3 |
| 0x130 | 50 | 29999 | 30000 | 0.00 | 20.0 | 20.2 | 20.4 |
| 0x131 | 50 | 29999 | 30000 | 0.00 | 20.0 | 20.2 | 20.4 |
| 0x140 | 2 | 1200 | 1200 | 0.00 | 500.0 | 500.4 | 500.6 |
| 0x1F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.4 | 1000.7 |
| 0x200 | 20 | 12000 | 8718 | 27.35 | 59.6 | 100.1 | 100.3 |
| 0x201 | 20 | 12000 | 12000 | 0.00 | 59.3 | 59.8 | 60.1 |
| 0x210 | 10 | 6000 | 6000 | 0.00 | 100.0 | 100.1 | 100.3 |
| 0x220 | 10 | 6000 | 6000 | 0.00 | 100.0 | 100.1 | 100.3 |
| 0x2F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.0 | 1000.1 |

Rechnerische Buslast (ohne Stuffing): 1.75 % bei 1 Mbit/s

## Burst-Fenster (>= 3 Frames innerhalb Fenster)

| Fenster [us] | Anzahl |
| --- | --- |
| 300 | 0 |
| 500 | 2999 |
| 1000 | 13833 |
| 2000 | 13930 |

| ID als 3. oder spaeterer Frame im Burst (1000 us) | Anzahl |
| --- | --- |
| 0x131 | 7812 |
| 0x201 | 6000 |
| 0x200 | 2718 |
| 0x140 | 24 |
| 0x1F0 | 14 |

## Error-Frames im Log: 6000, davon RX-Ueberlauf (CAN_ERR_CRTL_RX_OVERFLOW): 6000

| Daten-ID unmittelbar vor dem Ueberlauf-Frame | Anzahl |
| --- | --- |
| 0x220 | 4394 |
| 0x201 | 1606 |

Lesart: Faellt der Verlust genau auf die IDs, die im Burst als 3. Frame ankommen, und steigt rx_over_errors (Ueberlauf-Error-Frames im Log), ist es Fall 1 (MCP2515). Steigt bus_error, Fall 2. Beides 0 bei Verlust > 0,1 %: Fall 3.

## Bemerkungen

1. **Verlust deutlich hoeher als in K0** (4,58 % auf 0x200 in 120 s, 02.09.2026): hier 21,5 % (A1) und 27,4 % (A2). Beide Messungen sitzen am selben SocketCAN-Empfaenger; der Ueberlauf entsteht im MCP2515 vor dem Socket und ist vom Leseprozess unabhaengig. Die Differenz zu K0 ist nicht geklaert (Host-Zustand, Interrupt-Latenz); sie aendert die Zuordnung zu Fall 1 nicht, verschaerft aber NFA-19 (<= 1 % je Signal) als Gate vor K4.
2. **Zaehlersemantik:** Je Profil rund 6000 Ueberlauf-Ereignisse gegenueber rund 3200 fehlenden Frames. Der Treiber zaehlt RX0OVR und RX1OVR getrennt je Interrupt; ein verlorener Frame kann daher mehrfach gezaehlt werden. Das entspricht Hypothese 3 aus `planung/baseline_k0_referenzwerte.md` (BA-02) und erklaert das Verhaeltnis 1200 : 107 aus K0 qualitativ.
3. **Sensor-Bursts** (0x130, 0x131 alle 20 ms) verlieren in A1 231 Frames auf 0x131, in A2 keinen; der Fahrkern-Burst (4 Frames) verliert in beiden Profilen systematisch.
4. **Ultraschall:** `/range/front` wechselt im aufgebockten Zustand zwischen 0,001 m und 4,01 m (10 Hz). Die Cliff-Safety loggt dadurch im 100-ms-Takt Blockieren und Freigeben. Fuer die CAN-Messung ohne Bedeutung, als Befund fuer die Sensorbasis notiert (Echo-Timeout-Behandlung im Firmware-Pfad pruefen).
5. **BA-03** (zwei Publisher auf /cmd_vel) unveraendert beobachtet (`ros2 topic info /cmd_vel`: Publisher count 2).
6. Messwerkzeug: `s_a_vorher.sh` / `s_a_analyse.py` in dieser Version; Zeitstempel sind Host-Lesezeiten, Burst-Fenster 1000 us.
