# Baseline K0 - Referenzwerte fuer die Regressionspruefung

Git-Tag: `baseline-k0` (Commit `dad529a`)
Firmware: `config_drive.h` v4.0.0, `config_sensors.h` v3.0.0

Diese Tabelle fasst alle belegten Ist-Messwerte des Ausgangszustands zusammen.
Jedes Ausbaupaket K1 bis K10 weist nach, dass es die hier genannten Werte
reproduziert. Eine Abweichung ueber die angegebene Toleranz hinaus gilt als
Regression und blockiert die Definition of Done des jeweiligen Pakets.

Alle Werte stammen aus den Messprotokollen im selben Verzeichnis. Es wurden
keine Werte geschaetzt oder uebernommen, die dort nicht dokumentiert sind.

---

## 1 Fahrkern (Quelle: messprotokoll_phase1_phase2.md)

| Kenngroesse | Ist-Wert | Akzeptanz | Regressionstoleranz | Test |
|---|---|---|---|---|
| Geradeausfahrt 1 m, Lateraldrift (mit IMU) | 2,1 cm | < 5 cm | Kriterium muss weiter erfuellt sein | IT-03 `straight_drive_test corrected` |
| Geradeausfahrt 1 m, Heading-Fehler (mit IMU) | 0,06 Grad | < 5 Grad | Kriterium muss weiter erfuellt sein | IT-03 |
| Geradeausfahrt 1 m, Odom-Streckenfehler (mit IMU) | 0,3 % | - | < 1,0 % | IT-03 |
| Geradeausfahrt 1 m, Lateraldrift (ohne IMU) | 3,6 cm | < 5 cm | Kriterium muss weiter erfuellt sein | IT-03 `uncorrected` |
| Geradeausfahrt 1 m, Heading-Fehler (ohne IMU) | 5,57 Grad | < 5 Grad (FAIL im Bestand) | darf sich nicht verschlechtern | IT-03 `uncorrected` |
| Rotation 360 Grad, Winkelfehler | 1,88 Grad | < 5 Grad | Kriterium muss weiter erfuellt sein | IT-02 `rotation_test` |
| PID-Regelfrequenz | 50 Hz, Jitter < 2 ms | >= 50 Hz | Kriterium muss weiter erfuellt sein | T-01 `motor_test` |

Hinweis: Testfall 1.1 (ohne IMU-Korrektur) ist im Bestand mit FAIL bewertet
(Heading 5,57 > 5,00 Grad). Dieser Zustand wird als Baseline uebernommen und
nicht im Rahmen des Ausbaus korrigiert.

## 2 Sensor- und Sicherheitsbasis (Quelle: messprotokoll_phase1_phase2.md)

| Kenngroesse | Ist-Wert | Akzeptanz | Regressionstoleranz | Test |
|---|---|---|---|---|
| Cliff-Latenz Ende-zu-Ende | 2,0 ms | < 50 ms | < 50 ms, Anstieg < Faktor 2 | T-07 `cliff_latency_test` |
| Ultraschall-Publikationsrate | 9,2 Hz | >= 7,0 Hz | >= 7,0 Hz | T-05 `sensor_test` |
| Ultraschall-Genauigkeit bei 23 cm | 0,8 % Fehler | < 5,0 % | < 5,0 % | T-05 |
| Ultraschall-Wiederholgenauigkeit | 1,6 mm Std | < 15 mm | < 15 mm | T-05 |
| Cliff-Publikationsrate | 16,8 Hz | >= 15,0 Hz | >= 15,0 Hz | T-05 |
| Cliff-Fehlalarme auf ebenem Boden | 0 von 60 Samples | 0 | 0 | T-05 |
| IMU-Publikationsrate | 30,4 bis 35,2 Hz | >= 15 Hz | >= 15 Hz | T-04 `imu_test` |
| Gyro-Drift ueber 60 s | 0,463 deg/min | < 1,0 deg/min | < 1,0 deg/min | T-04 |
| Accel-Bias | 0,43 m/s^2 | < 0,6 m/s^2 | < 0,6 m/s^2 | T-04 |
| Heading-Vergleich IMU gegen Odometrie | 0,01 Grad | < 5,0 Grad | < 5,0 Grad | T-04 |

## 3 Lokalisierung und Kartierung (Quelle: messprotokoll_phase3.md)

| Kenngroesse | Ist-Wert (T3.1) | Ist-Wert (T3.2) | Akzeptanz | Test |
|---|---|---|---|---|
| TF-Rate `map` nach `odom` | 7,7 Hz | 7,7 Hz | >= 1,5 Hz | IT-04 `slam_validation` |
| TF-Rate `odom` nach `base_link` | 18,5 Hz | 18,8 Hz | >= 10 Hz | IT-04 |
| Topic-Rate `/odom` | 18,6 Hz | 18,8 Hz | >= 10 Hz | IT-04 |
| Topic-Rate `/scan` | 7,7 Hz | 7,8 Hz | >= 5 Hz | T-06 `rplidar_test` |
| Topic-Rate `/imu` | 30,1 Hz | 29,0 Hz | >= 20 Hz | IT-04 |
| Mittlerer Positionsfehler (MAE) | 0,1608 m | - | < 0,20 m | IT-04 |
| Maximaler Positionsfehler | 0,3583 m | - | - | IT-04 |
| RMSE | 0,190 m | 0,030 m | < 0,20 m | IT-04 |

## 4 Navigation (Quelle: messprotokoll_phase4.md)

| Kenngroesse | Ist-Wert | Akzeptanz | Test |
|---|---|---|---|
| Mittlerer xy-Fehler ueber 4 Wegpunkte | 0,0101 m | < 0,10 m | IT-06 `nav_square_test` |
| Maximaler xy-Fehler | 0,0217 m | < 0,10 m | IT-06 |
| Mittlerer Gier-Fehler | 0,0339 rad | < 0,15 rad | IT-06 |
| Maximaler Gier-Fehler | 0,0366 rad | < 0,15 rad | IT-06 |
| ArUco-Docking Erfolgsquote | 100 % | >= 80 % | IT-07 `docking_test` |
| ArUco-Docking lateraler Versatz | 0,73 cm | < 2 cm | IT-07 |

## 5 Bedien- und Leitstandsebene (Quelle: messprotokoll_phase5.md)

| Kenngroesse | Ist-Wert | Akzeptanz | Test |
|---|---|---|---|
| cmd_vel-Latenz Minimum | 1,0 ms | - | IT-09 `dashboard_latency_test` |
| cmd_vel-Latenz Mittelwert | 5,9 ms | < 50 ms | IT-09 |
| cmd_vel-Latenz p95 | 2,7 ms | < 100 ms | IT-09 |
| cmd_vel-Latenz Maximum | 435,0 ms | - | IT-09 |
| Telemetrie-Rate | 9,9 Hz | >= 4 Hz | IT-09 |
| System-Rate | 1,0 Hz | >= 0,25 Hz | IT-09 |
| Sensor-Status-Rate | 2,0 Hz | >= 0,5 Hz | IT-09 |
| Deadman-Stopplatenz | 251,6 ms | < 500 ms | IT-09 |
| Notaus-Stopplatenz | 2,1 ms | < 100 ms | IT-09 |

## 6 ROS-2-Referenzpfad, Lauf A (Quelle: baseline_k0_a.json, 120 s)

Aufnahme am unveraenderten Ist-Zustand mit `use_can:=False`, also
ausschliesslich ueber USB/micro-ROS. Nav2 und SLAM liefen; es wurde kein Ziel
und kein Fahrbefehl gesendet.

| Topic | Publisher | Nachrichten | Rate (Hz) |
|---|---|---|---|
| `/battery` | 1 | 256 | 2.0 |
| `/cliff` | 1 | 2028 | 15.86 |
| `/imu` | 1 | 4866 | 38.07 |
| `/map` | 1 | 254 | 1.99 |
| `/odom` | 1 | 2536 | 19.85 |
| `/range/front` | 1 | 1157 | 9.06 |
| `/scan` | 1 | 959 | 7.51 |
| `/tf` | 3 | 5079 | 39.77 |
| `/tf_static` | 2 | 2 | 0.02 |

Beobachtete TF-Kanten: `base_link` nach `laser`, `base_link` nach
`ultrasonic_link`, `map` nach `odom`, `odom` nach `base_link`.

**Diese Werte sind Baseline-Istwerte, keine Anforderungen.** Sie beschreiben,
was das System im Ausgangszustand geleistet hat, und dienen dem spaeteren
Regressionsvergleich. Sie ersetzen keine Mindestanforderung und begruenden
fuer sich genommen kein Abnahmekriterium.

Die geltenden Mindestanforderungen stehen in `docs/anforderungsliste-L1.md`
(NFA-03 Odometrie >= 10 Hz, NFA-04 IMU >= 20 Hz, NFA-02 LiDAR >= 5 Hz). Sie
werden durch eine Baseline-Messung nicht veraendert. Die Abgrenzung von
Anforderung, Baseline, spaeterem Messergebnis und Regressionstoleranz fuehrt
Abschnitt 10 der Anforderungsliste.

## 7 CAN-Bus, Lauf B (Quelle: baseline_k0_b.json, 120 s)

Passives Mithoeren auf `can0`, CAN war nicht als ROS-Topic-Quelle aktiv.

| CAN-ID | DLC | Soll (Hz) | Ist (Hz) | Erwartet | Empfangen | Verlust |
|---|---|---|---|---|---|---|
| 0x110 | 4 | 10 | 10,00 | 1200 | 1200 | 0,00 % |
| 0x120 | 1 | 20 | 20,01 | 2400 | 2401 | 0,00 % |
| 0x130 | 8 | 50 | 50,00 | 6000 | 6001 | 0,00 % |
| 0x131 | 4 | 50 | 50,00 | 6000 | 6001 | 0,00 % |
| 0x140 | 6 | 2 | 2,00 | 240 | 240 | 0,00 % |
| 0x141 | 1 | Event | 0,00 | - | 0 | ereignisgesteuert |
| 0x1F0 | 8 | 1 | 1,00 | 120 | 120 | 0,00 % |
| 0x200 | 8 | 20 | 19,08 | 2400 | 2290 | **4,58 %** |
| 0x201 | 8 | 20 | 20,00 | 2400 | 2400 | 0,00 % |
| 0x210 | 8 | 10 | 10,00 | 1200 | 1200 | 0,00 % |
| 0x220 | 4 | 10 | 10,00 | 1200 | 1200 | 0,00 % |
| 0x2F0 | 2 | 1 | 1,00 | 120 | 120 | 0,00 % |

| Kenngroesse | Ist-Wert | Regressionstoleranz |
|---|---|---|
| Frames gesamt ueber 120 s | 23.173 | > 22.000 |
| Durchschnittliche Busrate | 193,1 Frames/s | 150 bis 250 Frames/s |
| Empfangene CAN-IDs | 11 von 12 (0x141 nur bei Ereignis) | 11 von 12 |
| Effektiver Frameverlust gesamt | 0,46 % | < 1 % |
| CAN-Zustand | ERROR-ACTIVE | ERROR-ACTIVE |
| `bus_errors`, `error_warning`, `error_passive`, `bus_off`, `restarts` | je 0 | je 0 |
| `rx_errors` im Messfenster | 1200 (10,0/s) | offen, siehe BA-02 |
| Bitrate / Sample-Point | 1.000.000 / 0,750 | unveraendert |

Der DLC von 0x1F0 betraegt real 8 (Firmware-Ist laut
`sensor_node/include/twai_can.hpp`). Die Angabe "2 Byte" in
`hardware/can-bus/CAN-Bus.md` ist veraltet und wird in Paket K2 korrigiert.

## 8 Verhaeltnis zu den historischen CAN-Messungen

Fuer den CAN-Bus existieren drei aeltere Messlaeufe mit abweichenden Werten.
Massgeblich fuer alle Regressionspruefungen ist ab sofort die K0-Messung aus
Abschnitt 7; die frueheren Laeufe bleiben als Historie erhalten:

| Quelle | Datum | Dauer | Frames | 0x200 | 0x201 | Rolle |
|---|---|---|---|---|---|---|
| `hardware/can-bus/CAN-Bus.md` | 07.03.2026 | 30 s | 5559 | ca. 16 Hz | ca. 16 Hz | historisch |
| `planung/messprotokoll_can.md` | 31.03.2026 | 30 s | 5604 | 16,1 Hz | 16,7 Hz | historisch (zuvor kanonisch) |
| `dashboard/can_results.json` | 03.04.2026 | 30 s | 5809 | 19,6 Hz | 20,0 Hz | historisch |
| **`planung/baseline_k0_b.json`** | **02.09.2026** | **120 s** | **23.173** | **19,08 Hz** | **20,00 Hz** | **K0-Baseline** |

Die Odometrie-Frames erreichen heute nahezu die Soll-Rate von 20 Hz, waehrend
die beiden aeltesten Laeufe rund 16 Hz zeigten. Die K0-Messung ist mit 120 s
zudem viermal so lang wie alle frueheren Laeufe und damit statistisch
belastbarer. Die Aussage in `messprotokoll_can.md`, OdomPos und OdomHeading
laegen unter der Soll-Rate, trifft auf den heutigen Stand nicht mehr zu.

## 9 Weitere Systemkenngroessen

| Kenngroesse | Ist-Wert | Quelle | Regressionstoleranz |
|---|---|---|---|
| Hailo-8L Inferenzzeit | 34 ms | Kapitel 6 (kein eigenes Protokoll) | < 50 ms |
| Datenverlust micro-ROS | < 0,1 % | messprotokoll_phase1_phase2.md | < 0,1 % |
| CPU-Last Pi 5 im Vollbetrieb | < 80 % | Kapitel 6 (kein eigenes Protokoll) | < 80 % |
| RPP-Controller-Rate | > 2000 Hz | Kapitel 6 (kein eigenes Protokoll) | > 1000 Hz |

---

## 10 Baseline-Abweichungen

Die folgenden vier Punkte sind im Ausgangszustand messbar vorhanden. Sie werden
als Baseline-Abweichungen gefuehrt, damit sie spaeter nicht faelschlich den
Ausbaupaketen K2 bis K5 zugerechnet werden.

Fuer jeden Punkt sind Beobachtung und Deutung strikt getrennt. Als Ursache gilt
nur, was gemessen wurde. Alles andere ist ausdruecklich als Hypothese
gekennzeichnet und bis zur Pruefung ohne Beweiskraft.

---

### BA-01: Frameverlust auf CAN-ID 0x200 (Drive/OdomPos)

**Beobachtung (gemessen, Lauf B, 120 s)**

| Groesse | Wert |
|---|---|
| Erwartete Frames bei 20 Hz Soll-Rate | 2400 |
| Empfangene Frames | 2290 |
| Fehlende Frames | 110 |
| Verlustanteil auf 0x200 | 4,58 % |
| Verlustanteil ueber alle IDs | 0,46 % (107 von 23.280) |
| Verlust auf den uebrigen zehn periodischen IDs | 0 |

**Was nicht bekannt ist:** Ob die Frames am Sendeknoten (Drive-ECU) gar nicht
erst erzeugt, auf dem Bus gestoert, oder am Empfaenger (MCP2515 bzw.
SocketCAN) verworfen wurden. Die Messung findet ausschliesslich am
Empfangsende statt und kann diese drei Faelle nicht unterscheiden.

**Einordnung:** Blocker vor K4. Siehe Abschnitt 11.

---

### BA-02: Steigende `rx_errors` bei gleichzeitig null CAN-Busfehlern

**Beobachtung (gemessen, Lauf B, 120 s)**

| Groesse | Wert |
|---|---|
| `rx_errors` im Messfenster | 1200 |
| Daraus abgeleitete Rate | 10,0 pro Sekunde |
| `rx_packets` im Messfenster | 23.175 |
| `bus_errors` | 0 |
| `error_warning` | 0 |
| `error_passive` | 0 |
| `bus_off` | 0 |
| `restarts` | 0 |
| CAN-Zustand ueber die gesamte Messung | ERROR-ACTIVE |
| Vom Skript gezaehlte CAN-Error-Frames | 0 |

Die Zaehlrate von 10,0 pro Sekunde entspricht zahlenmaessig der Frame-Rate der
10-Hz-Nachrichten (0x110, 0x210, 0x220). Dieser Zusammenhang ist eine
Beobachtung zur Zahlengleichheit, kein nachgewiesener Kausalzusammenhang.

**Widerspruch:** Ein Zaehler fuer Empfangsfehler steigt kontinuierlich,
waehrend saemtliche Zaehler des CAN-Protokollzustands auf null bleiben und der
Bus durchgehend ERROR-ACTIVE meldet. Auf Protokollebene ist der Bus damit
fehlerfrei; der Fehler wird unterhalb oder oberhalb der Protokollebene
gezaehlt.

**Hypothesen (nicht geprueft, nicht belegt, ausdruecklich keine Feststellung)**

1. *Hypothese Pufferueberlauf:* Der MCP2515 besitzt zwei RX-Puffer. Treffen im
   100-ms-Raster mehrere periodische Frames dicht aufeinander, koennte ein
   Ueberlauf gemeldet werden, den der Treiber als `rx_errors` zaehlt.
2. *Hypothese SPI-Durchsatz:* Der in `/boot/firmware/config.txt` gesetzte
   `spimaxfrequency=1000000` (1 MHz) koennte das Auslesen der Puffer
   begrenzen.
3. *Hypothese Zaehlersemantik:* Der `mcp251x`-Treiber koennte unter
   `rx_errors` Ereignisse fuehren, die keinen Frameverlust bedeuten.

Ob BA-01 und BA-02 dieselbe Ursache haben, ist offen. Gegen einen einfachen
Zusammenhang spricht, dass 1200 gezaehlte Fehler nur 107 tatsaechlich
fehlenden Frames gegenueberstehen.

**Zu klaerender Pruefweg (in K3 als Messpunkt in T-10 aufzunehmen):**
Zaehlerentwicklung bei veraenderter SPI-Taktrate, Vergleich mit einem zweiten
CAN-Empfaenger am selben Bus, Auswertung der MCP2515-Fehlerregister (EFLG),
sowie Gegenprobe mit reduzierter Buslast.

**Einordnung:** Blocker vor K4. Siehe Abschnitt 11.

---

### BA-03: Zwei Publisher auf `/cmd_vel`

**Beobachtung (gemessen, Lauf A)**

| Groesse | Wert |
|---|---|
| Publisher auf `/cmd_vel` | 2 |
| Knoten 1 | `cliff_safety_node` |
| Knoten 2 | `velocity_smoother` (Nav2) |
| Subscriber auf `/cmd_vel` | `esp32_bot` |
| Nachrichten auf `/cmd_vel` im Messfenster | 2558 (20,0 Hz) |
| Publisher auf `/nav_cmd_vel` | 5 |
| Nachrichten auf `/nav_cmd_vel` | 0 |

Beleg: `ros2 topic info /cmd_vel --verbose`. Das Remapping
`SetRemap("/cmd_vel" -> "/nav_cmd_vel")` in `full_stack.launch.py` Zeile 249
bis 273 wirkt auf die Nav2-GroupAction; der `velocity_smoother` erscheint
dennoch als Publisher auf `/cmd_vel`.

**Bedeutung:** Der Fahrbefehlspfad hat im Bestand zwei Quellen, von denen nur
eine die Sicherheitslogik ist. Die geplante Anforderung SIA-15 fordert genau
einen Publisher auf `/cmd_vel` und ist damit im Ausgangszustand nicht erfuellt.

**Nicht gepruefte Frage:** Ob und unter welchen Bedingungen der
`velocity_smoother` tatsaechlich Fahrbefehle sendet. Im Messfenster wurden auf
`/nav_cmd_vel` null Nachrichten beobachtet, waehrend Nav2 ohne Zielvorgabe
lief. Ein Nachweis unter aktiver Navigation steht aus und erfordert einen
Fahrversuch.

**Einordnung:** Architekturpunkt der Ausbaustufe Winner-Funktionskette und
Trajektorienregelung (K9, Nachweis SIA-15). **Im Rahmen von K0 bis K8 wird
hieran nichts geaendert.** Der Punkt ist dort als eigenstaendige Aufgabe zu
fuehren, nicht als Nebenwirkung eines anderen Pakets.

---

### BA-04: `/cliff` waehrend beider Messlaeufe dauerhaft `true`

**Beobachtung (gemessen)**

| Groesse | Wert |
|---|---|
| `/cliff` (ROS 2, Lauf A) | durchgehend `true` |
| CAN 0x120 (Lauf B, letzter Wert) | `cliff = True` |
| Nachrichten auf `/cmd_vel` | 2558 in 128 s, 20,0 Hz |
| Rate des Sicherheitstimers in `cliff_safety_node` | 20 Hz |
| `/range/front` waehrend der Messung | 0,555 bis 0,563 m |

Die `/cmd_vel`-Rate von 20,0 Hz entspricht exakt der Timer-Rate des
Sicherheitstimers, der bei blockiertem Zustand Null-Twists sendet. Der Inhalt
dieser Nachrichten ist ein Nullvektor; es wurde kein Fahrbefehl gesendet und
keine Bewegung ausgeloest.

**Was nicht bekannt ist:** Warum der Kantensensor ausloest. Der Zustand kann
seine Ursache in der Aufstellung des Roboters, im Untergrund, in der
Sensormontage, in der Sensorik selbst oder in der Auswerteschwelle haben.
Waehrend der Messung wurde der physische Aufbau nicht protokolliert, und es
wurde keine Pruefung am Sensor durchgefuehrt. **Es wird ausdruecklich keine
Ursache angenommen.**

**Einordnung:** Zu klaerender Hardware- beziehungsweise Umgebungszustand.
Vor der naechsten Vergleichsmessung ist der physische Aufbau zu
protokollieren und der Kantensensor bei definiertem Untergrund gegen den
Bestandswert aus Abschnitt 2 zu pruefen (dort: 0 Fehlalarme in 60 Samples auf
ebenem Boden). Bis dahin ist unklar, ob der Zustand aufbaubedingt oder
sensorbedingt ist.

**Auswirkung auf die Baseline:** Die in Abschnitt 6 dokumentierte
`/cmd_vel`-Rate von 20,0 Hz gilt nur unter diesem Zustand. Sie ist kein
Regressionsmassstab, solange BA-04 offen ist.

---

### BA-05: Weitere Bestandsbefunde ohne Blockerwirkung

| Befund | Beleg | Behandlung |
|---|---|---|
| Testfall 1.1 (Geradeausfahrt ohne IMU) mit FAIL bewertet | messprotokoll_phase1_phase2.md Zeile 31 | Baseline, keine Korrektur im Ausbau |
| `mypy` meldet zwei Typfehler in `can_validation_test.py` (`can.interface.Bus` als Typ, `recv`-Attribut) | `mypy --config-file mypy.ini` | Baseline; Behebung optional in K3 |
| `messprotokoll_phase4.md` Testfall 4.1 Schritt 1 unausgefuellt (`___`) | messprotokoll_phase4.md Zeilen 23 bis 30 | Baseline, nicht Teil des Ausbaus |
| `rx_dropped` bei 907.769 absolut, Delta im Messfenster 0 | `/sys/class/net/can0/statistics` | historisch angefallen; im Messfenster kein Zuwachs |
| Im Planungsentwurf genannte K6-Zielwerte (`/imu` >= 45 Hz, `/cliff` >= 18 Hz) waren Schaetzungen ohne Anforderungsstatus und liegen ueber den K0-Istwerten | Abschnitt 6 | In K1 als Schaetzung verworfen. Es gelten weiterhin NFA-02, NFA-03 und NFA-04; die K0-Istwerte bleiben reine Referenz |
| DoD Phase 6 beschreibt eine 4-Knoten-Sprachschnittstelle, real ist ein konsolidierter Knoten | OP-06 | Angleichung in K1 |
| `can_validation_test` fuehrt 0x1F0 mit DLC 2, real ist DLC 8; 0x150 fehlt in `EXPECTED` | `can_validation_test.py` Zeilen 76 bis 175 | Korrektur in K2 |

---

## 11 K0-Status und Freigabe-Gates

### 11.1 Status des Pakets K0

K0 ist **nicht** als vollstaendig bestanden zu fuehren. Der Referenzzustand
wurde erfolgreich erfasst; dabei sind bekannte Abweichungen sichtbar geworden.

| Pruefpunkt | Status | Beleg |
|---|---|---|
| Messaufnahme | PASS | baseline_k0_a.json, baseline_k0_b.json |
| Drive-Firmware Build (ohne Upload) | PASS | `pio run -e drive_node` |
| Sensor-Firmware Build (ohne Upload) | PASS | `pio run -e sensor_node` |
| ROS-2-Build | PASS | `colcon build --packages-select my_bot` |
| USB/micro-ROS-Referenzpfad | PASS | Lauf A, 78 Topics, 4 TF-Kanten |
| CAN physikalischer Zustand | PASS | ERROR-ACTIVE, alle Protokollzaehler 0 |
| CAN-Datenintegritaet | **OFFEN** | BA-01, BA-02 |
| Cliff-Zustand | **OFFEN** | BA-04 |
| `/cmd_vel`-Architektur | **OFFEN, spaeter** | BA-03, Zuordnung K9 |
| Fahrtest | NICHT AUSGEFUEHRT | keine Freigabe erteilt, in K0 nicht vorgesehen |

Gesamtbewertung: **Referenzzustand erfolgreich erfasst, offene Befunde
vorhanden.** Nicht: alles fehlerfrei.

Diese Bewertung ist im V-Modell die belastbarere: Die Abweichungen sind vor dem
Umbau dokumentiert und koennen spaeter nicht faelschlich den Paketen K2 bis K5
angelastet werden.

### 11.2 Freigabe-Gate vor K4

K1 und K2 sind Anforderungs-, Architektur- und Entwurfsarbeit und werden durch
die offenen Befunde nicht blockiert. K3 bindet die Sensor- und
Sicherheitsbasis Pi-seitig an und aendert den Fahrbefehlspfad nicht.

Vor K4 gilt ein verbindliches Gate:

```
K1 Anforderungen und Architektur
        |
K2 DBC und Signalmodell
        |
K3 Sensor-ECU ueber CAN
        |
------------------ GATE ------------------
 (1) CAN-Empfang ueber 120 s stabil?
 (2) Frameverlust auf 0x200 geklaert?
 (3) rx_errors geklaert?
------------------------------------------
        |
K4 Drive-CAN Shadow Mode
        |
K5 Drive-CAN aktiv (CAN uebernimmt Fahrbefehle)
```

**Gate-Kriterien**

| Nr. | Kriterium | Nachweis |
|---|---|---|
| 1 | Ueber 120 s werden alle periodischen CAN-IDs innerhalb der Toleranz aus Abschnitt 7 empfangen | T-10 `can_bus_load_test` |
| 2 | Der Frameverlust auf 0x200 ist entweder auf unter 1 % gesenkt oder seine Ursache ist benannt und die Auswirkung auf den Fahrbefehlspfad ist bewertet | BA-01, Messprotokoll CAN2 |
| 3 | Der Anstieg von `rx_errors` ist erklaert und es ist belegt, dass er keinen Verlust sicherheitsrelevanter Frames verursacht | BA-02, Messprotokoll CAN2 |

**Begruendung:** K4 und K5 verlegen den Fahrbefehlspfad auf den CAN-Bus. Ein
ungeklaerter Empfangsfehler auf genau diesem Bus darf nicht erst danach
untersucht werden. Die Reihenfolge im V-Modell lautet: erst messen, dann die
Ursache verstehen, dann den sicherheitsrelevanten Kanal umstellen.

---

*Erstellt im Rahmen von Ausbaupaket K0 (Baseline), Stand 02.09.2026.*

*Die Werte der Abschnitte 1 bis 5 sind gegen die Messprotokolle Phase 1 bis 5
verifiziert. Die Werte der Abschnitte 6 und 7 stammen aus zwei eigenen passiven
Messlaeufen von je 120 s am Git-Tag `baseline-k0` (Commit `dad529a`). Es wurde
keine Firmware geaendert, nichts geflasht und kein Fahrbefehl gesendet.*

*K0-Bewertung: Referenzzustand erfolgreich erfasst, offene Befunde vorhanden
(BA-01 bis BA-04). Freigabe-Gate vor K4: Abschnitt 11.2.*
