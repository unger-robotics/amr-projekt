# 08 -- Validierungsplan nach Hardware-Migration

**Dokumenttyp:** Testplan und Validierungsprotokoll
**Stand:** 2025-12-19
**Bezugsdokumente:** `hardware/config.h`, `hardware/hardware-setup.md`, `hardware/docs/01-04`, `bachelorarbeit/kapitel_06_validierung.md`

---

## Uebersicht

Dieser Validierungsplan definiert die systematische Pruefung aller Subsysteme nach der Migration der ESP32-Firmware auf die neue Hardware-Plattform (XIAO ESP32-S3) mit geaenderten kinematischen Parametern. Die Migration umfasst folgende Parameteraenderungen:

| Parameter | ALT (Bachelorarbeit Kap. 6) | NEU (config.h) | Aenderung |
|---|---|---|---|
| MCU | ESP32 (generisch) | XIAO ESP32-S3 (Dual-Core LX7, 240 MHz) | Plattformwechsel |
| Raddurchmesser | 64 mm (r=32 mm) | 65 mm (r=32,5 mm) | +1 mm |
| Spurbreite | 145 mm | 178 mm | +33 mm |
| Encoder Ticks/Rev | 1440 | ~374 (links 374,3 / rechts 373,6) | -74 % |
| Encoder-Modus | Quadratur (A+B) | A-only (Phase B isoliert) | Modusaenderung |
| Motortreiber-Modus | DIR+PWM | Dual-PWM (Cytron MDD3A) | Ansteuerungsaenderung |
| PWM-Deadzone | nicht dokumentiert | 35 | Neu definiert |
| Konversionsfaktor | ~0,140 mm/Tick | ~0,546 mm/Tick | ~3,9x groeber |

**WICHTIGER HINWEIS:** Saemtliche Testergebnisse in Kapitel 6 der Bachelorarbeit basieren auf den alten Parametern und sind nach der Migration **nicht mehr gueltig**. Alle quantitativen Tests muessen vollstaendig neu erhoben werden.

---

## 1) Pre-Flash Checkliste

Vor dem ersten Firmware-Upload auf den XIAO ESP32-S3 muessen folgende Voraussetzungen erfuellt sein.

### 1.1 PlatformIO Board-Konfiguration

- [ ] `platformio.ini`: Board auf `seeed_xiao_esp32s3` gesetzt
- [ ] Framework: `arduino` konfiguriert
- [ ] Upload-Geschwindigkeit: 921600 Baud
- [ ] Monitor-Geschwindigkeit: 115200 Baud
- [ ] micro-ROS-Bibliothek kompatibel mit ESP32-S3 (Humble)
- [ ] Kompilierung erfolgreich (`pio run` ohne Fehler)

### 1.2 Pin-Belegung physisch verifizieren

Jeder Pin muss gegen die Tabelle in `config.h` und `hardware/docs/04_systemintegration_stueckliste.md` geprueft werden:

- [ ] D0 (GPIO1) -> MDD3A M1A (Motor Links Vorwaerts-PWM), Kabel Rot
- [ ] D1 (GPIO2) -> MDD3A M1B (Motor Links Rueckwaerts-PWM), Kabel Weiss
- [ ] D2 (GPIO3) -> MDD3A M2A (Motor Rechts Vorwaerts-PWM), Kabel Rot
- [ ] D3 (GPIO4) -> MDD3A M2B (Motor Rechts Rueckwaerts-PWM), Kabel Weiss
- [ ] D4 (GPIO5) -> I2C SDA (MPU6050, optional)
- [ ] D5 (GPIO6) -> I2C SCL (MPU6050, optional)
- [ ] D6 (GPIO43) -> Encoder Links Phase A, Kabel Gelb
- [ ] D7 (GPIO44) -> Encoder Rechts Phase A, Kabel Gelb
- [ ] D8 (GPIO7) -> Servo Pan Signal (optional)
- [ ] D9 (GPIO8) -> Servo Tilt Signal (optional)
- [ ] D10 (GPIO9) -> LED/MOSFET IRLZ24N Gate
- [ ] Encoder Phase B (Gruen) an beiden Motoren **isoliert** (nicht angeschlossen)

### 1.3 Spannungsversorgung pruefen

- [ ] 4S LiFePO4 Akkupack geladen: 12,8 -- 14,6 V am 12-V-Rail messen
- [ ] Hauptsicherung 15 A korrekt eingesetzt
- [ ] Buck-Converter #1 (FZJ5V5A1S-C): 5,1 V +/- 0,1 V **unter Last** (Pi bootet)
- [ ] Sternpunkt-Masse: Pi-GND, Buck-GND, MDD3A-GND, ESP32-GND alle verbunden
- [ ] MDD3A erhaelt 12 V ueber Schraubklemmen VB+/VB-
- [ ] MDD3A Power-LED leuchtet
- [ ] ESP32-S3 3,3-V-Rail stabil (Encoder-Versorgung)

### 1.4 USB-C Verbindung zum XIAO

- [ ] USB-C-Datenkabel verwendet (nicht nur Ladekabel)
- [ ] ESP32-S3 enumeriert am Pi als `/dev/ttyACM*`
- [ ] Firmware-Upload erfolgreich (`pio run -t upload`)
- [ ] Serieller Monitor zeigt Boot-Meldung (`pio run -t monitor`)

---

## 2) Encoder-Validierung

Die Encoder-Kalibrierung ist eine kritische Voraussetzung fuer alle nachfolgenden Tests. Die aktuellen Werte in `config.h` (374,3 / 373,6 Ticks/Rev) sind als vorlaeufig markiert.

### 2.1 Tick-Count pro voller Radumdrehung

**Methode: 10-Umdrehungen-Test**

Jedes Rad wird exakt 10 Umdrehungen von Hand gedreht. Die Gesamtzahl der Ticks wird durch 10 geteilt, um den Mittelwert pro Umdrehung zu erhalten.

- [ ] Testprogramm auf ESP32 flashen: Tick-Zaehler ueber seriellen Monitor ausgeben
- [ ] Motor Links: 10 Umdrehungen vorwaerts drehen, Ticks ablesen
- [ ] Motor Links: 10 Umdrehungen rueckwaerts drehen, Ticks ablesen
- [ ] Motor Rechts: 10 Umdrehungen vorwaerts drehen, Ticks ablesen
- [ ] Motor Rechts: 10 Umdrehungen rueckwaerts drehen, Ticks ablesen
- [ ] Test 3x wiederholen und Mittelwert bilden

**Protokolltabelle:**

| Durchgang | Links Vorw. | Links Rueckw. | Rechts Vorw. | Rechts Rueckw. |
|---|---|---|---|---|
| 1 | ______ | ______ | ______ | ______ |
| 2 | ______ | ______ | ______ | ______ |
| 3 | ______ | ______ | ______ | ______ |
| **Mittelwert/10** | ______ | ______ | ______ | ______ |

**SOLL-Wert:** ~374 Ticks/Rev (A-only Hall-Encoder)

**Akzeptanzkriterium:** Abweichung zwischen Durchgaengen < 2 Ticks/Rev. Abweichung zwischen Vorwaerts/Rueckwaerts < 1 %.

### 2.2 Richtungserkennung

Da nur Phase A angeschlossen ist (B-Kanal isoliert), wird die Drehrichtung aus der PWM-Ansteuerung abgeleitet, nicht aus dem Encoder selbst.

- [ ] Vorwaerts-PWM auf Motor Links: Ticks zaehlen **positiv** (aufwaerts)
- [ ] Rueckwaerts-PWM auf Motor Links: Ticks zaehlen **negativ** (abwaerts)
- [ ] Vorwaerts-PWM auf Motor Rechts: Ticks zaehlen **positiv** (aufwaerts)
- [ ] Rueckwaerts-PWM auf Motor Rechts: Ticks zaehlen **negativ** (abwaerts)
- [ ] Firmware-Logik: Vorzeichen der Ticks stimmt mit PWM-Richtung ueberein

### 2.3 Geschwindigkeitsberechnung bei bekannter Drehzahl

- [ ] Motor bei konstantem PWM (z.B. 128 = 50 %) laufen lassen
- [ ] Ticks pro Sekunde zaehlen (ueber seriellen Monitor, 5 Sekunden mitteln)
- [ ] Drehzahl berechnen: n = Ticks/s / TICKS_PER_REV [Rev/s]
- [ ] Lineargeschwindigkeit berechnen: v = n * WHEEL_CIRCUMFERENCE [m/s]
- [ ] Plausibilitaet: v sollte bei 50 % PWM unter 0,4 m/s liegen

### 2.4 Asymmetrie links/rechts quantifizieren

- [ ] Beide Motoren mit identischem PWM-Wert (128) gleichzeitig betreiben
- [ ] Ticks pro Sekunde fuer Links und Rechts getrennt erfassen (10 Sekunden)
- [ ] Asymmetrie berechnen: Differenz = |Ticks_L - Ticks_R| / Mittelwert * 100 %
- [ ] Dokumentieren: Asymmetrie < 5 % ist akzeptabel fuer PID-Kompensation

---

## 3) Motorsteuerungs-Tests

### 3.1 Deadzone-Verifikation

Die PWM-Deadzone (`PWM_DEADZONE = 35`) definiert den Minimalwert, ab dem die Motoren anlaufen.

- [ ] PWM schrittweise von 0 bis 50 erhoehen (Schrittweite 5)
- [ ] Motor Links: Anlauf-PWM dokumentieren: ______
- [ ] Motor Rechts: Anlauf-PWM dokumentieren: ______
- [ ] Beide Motoren laufen bei PWM <= 35 **nicht** an
- [ ] Beide Motoren laufen bei PWM = 40 zuverlaessig an

**Akzeptanzkriterium:** Tatsaechlicher Anlauf-PWM liegt im Bereich 30-40. `PWM_DEADZONE` in `config.h` bei Abweichung anpassen.

### 3.2 PWM-Kanal-Zuordnung

Die LEDC-Kanaele sind in `config.h` getauscht (A/B invertiert fuer korrekte Richtung).

- [ ] PWM auf D0 (LEDC CH 1, Motor Links A): Motor Links dreht **vorwaerts**
- [ ] PWM auf D1 (LEDC CH 0, Motor Links B): Motor Links dreht **rueckwaerts**
- [ ] PWM auf D2 (LEDC CH 3, Motor Rechts A): Motor Rechts dreht **vorwaerts**
- [ ] PWM auf D3 (LEDC CH 2, Motor Rechts B): Motor Rechts dreht **rueckwaerts**
- [ ] Vorwaertsfahrt beider Motoren gleichzeitig: Roboter faehrt geradeaus (nicht kurvenfahrend)
- [ ] Falls Richtung falsch: Motoranschluesse am MDD3A tauschen, **nicht** die config.h-Zuordnung

### 3.3 Rampen-Test

- [ ] cmd_vel mit v_linear = 0,4 m/s senden
- [ ] Beobachten: Motoren fahren graduell hoch (nicht sprunghaft)
- [ ] Firmware-Rampe (`MAX_ACCEL = 5.0 rad/s^2`) aktiv
- [ ] Kein Durchdrehen der Raeder beim Anfahren

### 3.4 Notaus-Verhalten

- [ ] Waehrend Fahrt: Hauptschalter betaetigen -> Motoren stoppen sofort
- [ ] Waehrend Fahrt: USB-Kabel zum ESP32 trennen -> Motoren stoppen (kein `cmd_vel`)
- [ ] Failsafe-Timeout: Nach 1000 ms ohne `cmd_vel` muessen Motoren auf PWM 0 gehen
- [ ] MDD3A-Testtaster: Manuelle Motorbetaetigung funktioniert ohne Firmware

---

## 4) Kinematik-Validierung

Die kinematischen Parameter in `config.h` (`WHEEL_RADIUS = 0,0325 m`, `WHEEL_BASE = 0,178 m`) muessen experimentell validiert werden.

**ACHTUNG:** Die Firmware `main.cpp` enthaelt noch hartcodierte alte Werte:
- Zeile 17-18: `DiffDriveKinematics kinematics(0.032, 0.145)` -- MUSS auf `(0.0325, 0.178)` geaendert werden
- Zeile 45: `1440.0` (alte Ticks/Rev) -- MUSS auf `TICKS_PER_REV` aus `config.h` geaendert werden
- Zeile 83-84: `0.032` und `0.145` (alte Kinematik-Konstanten) -- MUSS auf `WHEEL_RADIUS` und `WHEEL_BASE` geaendert werden

### 4.1 Geradeausfahrt (1 m)

- [ ] Roboter auf Startmarkierung positionieren
- [ ] cmd_vel: v_linear = 0,2 m/s, omega = 0,0 fuer definierte Zeit senden
- [ ] Tatsaechlich zurueckgelegte Strecke mit Massband messen
- [ ] Laterale Abweichung (Drift nach links/rechts) messen
- [ ] 5x wiederholen

**Protokolltabelle:**

| Durchgang | SOLL [m] | IST [m] | Laterale Abweichung [cm] |
|---|---|---|---|
| 1 | 1,00 | ______ | ______ |
| 2 | 1,00 | ______ | ______ |
| 3 | 1,00 | ______ | ______ |
| 4 | 1,00 | ______ | ______ |
| 5 | 1,00 | ______ | ______ |
| **Mittelwert** | | ______ | ______ |
| **Std.-Abw.** | | ______ | ______ |

**Akzeptanzkriterium:** Streckenabweichung < 5 %, laterale Abweichung < 5 cm auf 1 m.

### 4.2 90-Grad-Drehung

- [ ] Roboter auf Startmarkierung positionieren, Ausrichtung markieren
- [ ] cmd_vel: v_linear = 0,0, omega = 0,5 rad/s fuer berechnete Zeit senden
- [ ] Tatsaechlichen Drehwinkel mit Winkelmesser/Bodenmarkierung messen
- [ ] 5x im Uhrzeigersinn (CW), 5x gegen Uhrzeigersinn (CCW) wiederholen

**Protokolltabelle:**

| Durchgang | Richtung | SOLL [Grad] | IST [Grad] | Abweichung [Grad] |
|---|---|---|---|---|
| 1 | CW | 90 | ______ | ______ |
| 2 | CW | 90 | ______ | ______ |
| 3 | CW | 90 | ______ | ______ |
| 4 | CW | 90 | ______ | ______ |
| 5 | CW | 90 | ______ | ______ |
| 6 | CCW | 90 | ______ | ______ |
| 7 | CCW | 90 | ______ | ______ |
| 8 | CCW | 90 | ______ | ______ |
| 9 | CCW | 90 | ______ | ______ |
| 10 | CCW | 90 | ______ | ______ |

**Akzeptanzkriterium:** Winkelabweichung < 5 Grad. Asymmetrie CW vs. CCW < 3 Grad.

### 4.3 Kreisfahrt

- [ ] cmd_vel: v_linear = 0,2 m/s, omega = 0,5 rad/s (Radius = v/omega = 0,4 m)
- [ ] Nach einer vollen Umdrehung: Endposition relativ zum Startpunkt messen
- [ ] Radius-Abweichung bestimmen
- [ ] 3x wiederholen

**Akzeptanzkriterium:** Endposition weicht maximal 10 cm vom Startpunkt ab.

### 4.4 Odometrie vs. Ground Truth

- [ ] Definierte Strecke fahren (z.B. 2 m geradeaus, 90 Grad rechts, 2 m geradeaus)
- [ ] Odometrie-Endposition aus `/odom` Topic ablesen
- [ ] Tatsaechliche Endposition mit Massband messen
- [ ] Euklidischen Abstand berechnen
- [ ] 5x wiederholen

**Akzeptanzkriterium:** Positionsabweichung < 15 cm auf dem L-foermigen 4-m-Pfad (vor UMBmark-Kalibrierung).

---

## 5) UMBmark-Neukalibrierung

**PFLICHT nach jedem Parameterwechsel.** Die UMBmark-Kalibrierung nach Borenstein et al. (1996) ist die primaere Methode zur Reduktion systematischer Odometriefehler.

### 5.1 Testprotokoll

**Testfeld:** 4 m x 4 m Quadrat, Ecken mit Bodenmarkierungen versehen.

**Ablauf pro Lauf:**
1. Roboter auf Startposition stellen (Markierung)
2. Autonome Quadratfahrt: 4 m vorwaerts, 90 Grad rechts, 4 m vorwaerts, 90 Grad rechts, 4 m vorwaerts, 90 Grad rechts, 4 m vorwaerts
3. Endposition relativ zum Startpunkt messen (x- und y-Abweichung getrennt)

**Durchfuehrung:**
- [ ] 5 Laeufe im Uhrzeigersinn (CW)
- [ ] 5 Laeufe gegen den Uhrzeigersinn (CCW)
- [ ] Jede Endposition (x_i, y_i) dokumentieren

**Protokolltabelle CW:**

| Lauf | x_end [mm] | y_end [mm] |
|---|---|---|
| CW-1 | ______ | ______ |
| CW-2 | ______ | ______ |
| CW-3 | ______ | ______ |
| CW-4 | ______ | ______ |
| CW-5 | ______ | ______ |
| **Schwerpunkt** | x_CW = ______ | y_CW = ______ |

**Protokolltabelle CCW:**

| Lauf | x_end [mm] | y_end [mm] |
|---|---|---|
| CCW-1 | ______ | ______ |
| CCW-2 | ______ | ______ |
| CCW-3 | ______ | ______ |
| CCW-4 | ______ | ______ |
| CCW-5 | ______ | ______ |
| **Schwerpunkt** | x_CCW = ______ | y_CCW = ______ |

### 5.2 Korrekturfaktoren berechnen

Nach Borenstein et al. (1996, S. 141-142, Gl. 5.9-5.15):

```
1. Schwerpunkte (x_CW, y_CW) und (x_CCW, y_CCW) berechnen

2. Alpha- und Beta-Winkel:
   alpha_CW  = atan2(y_CW, x_CW)    [Orientierungsfehler CW]
   alpha_CCW = atan2(y_CCW, x_CCW)   [Orientierungsfehler CCW]

3. Raddurchmesser-Verhaeltnis E_d:
   R_CW  = (L / 2) * (1 / sin(alpha_CW / 4))     [L = 4*4m = 16m Gesamtpfad]
   R_CCW = (L / 2) * (1 / sin(alpha_CCW / 4))
   E_d   = (R_CW + L/2) / (R_CW - L/2)   (oder aus CCW analog)

4. Effektive Spurbreite E_b:
   beta  = (alpha_CW + alpha_CCW) / 2    [mittlerer Orientierungsfehler]
   E_b   = (beta / (2*pi)) * WHEEL_BASE_nominal + WHEEL_BASE_nominal

5. Korrigierte Parameter:
   WHEEL_RADIUS_LEFT  = WHEEL_RADIUS * (2 / (E_d + 1))
   WHEEL_RADIUS_RIGHT = WHEEL_RADIUS * (2*E_d / (E_d + 1))
   WHEEL_BASE_korrigiert = E_b
```

### 5.3 Korrekturfaktoren anwenden

- [ ] E_d berechnet: ______
- [ ] E_b berechnet: ______
- [ ] Korrigierte Werte in `config.h` eintragen
- [ ] Firmware neu kompilieren und flashen
- [ ] Verifikationsfahrt: 5x CW, 5x CCW auf gleichem Testfeld
- [ ] Schwerpunktabweichung nach Kalibrierung < 10 mm (Faktor >= 10 Verbesserung)

**Akzeptanzkriterium (aus Bachelorarbeit F05):** Reduktion der systematischen Odometriefehler um mindestens Faktor 10 gegenueber dem unkalibrierten Zustand.

**Referenz:** Borenstein, J., Feng, L. (1996): "Measurement and Correction of Systematic Odometry Errors in Mobile Robots", S. 130-145.

---

## 6) PID-Re-Tuning

Die PID-Parameter muessen nach dem Hardwarewechsel neu evaluiert werden, da sich die Encoder-Aufloesung (374 vs. 1440 Ticks/Rev) und das Motorverhalten geaendert haben.

### 6.1 Ausgangswerte

Aus der aktuellen Firmware (`main.cpp`, Zeile 19-20):

| Parameter | Links | Rechts | Bemerkung |
|---|---|---|---|
| Kp | 1,5 | 1,5 | Proportionalanteil |
| Ki | 0,5 | 0,5 | Integralanteil |
| Kd | 0,0 | 0,0 | Differentialanteil (deaktiviert) |
| Anti-Windup | [-1,0; 1,0] | [-1,0; 1,0] | Integral-Begrenzung |

**Hinweis zur reduzierten Encoder-Aufloesung:** Mit 374 statt 1440 Ticks/Rev ist die Geschwindigkeitsmessung ~3,9x groeber. Dies kann zu hoeherem Messrauschen fuehren und erfordert moeglicherweise eine Anpassung der PID-Verstaerkungen.

### 6.2 Sprungantwort-Messung

- [ ] Soll-Geschwindigkeit sprunghaft von 0 auf 0,4 m/s setzen
- [ ] `/odom` Topic mit `rqt_plot` oder rosbag aufzeichnen (mind. 10 Sekunden)
- [ ] Anstiegszeit messen: Zeit bis 90 % des Sollwerts
- [ ] Ueberschwingen messen: Maximale Abweichung ueber Sollwert in %
- [ ] Einschwingzeit messen: Zeit bis Ist-Wert innerhalb +/- 5 % des Sollwerts bleibt
- [ ] Stationaerer Regelfehler bestimmen
- [ ] Test fuer beide Raeder separat durchfuehren

### 6.3 Tuning-Verfahren

**Option A: Manuelles Tuning (empfohlen bei moderater Abweichung)**
1. Mit aktuellem Kp = 1,5 beginnen
2. Wenn zu traege: Kp erhoehen (z.B. auf 2,0)
3. Wenn Schwingung: Kp reduzieren (z.B. auf 1,0)
4. Ki anpassen: Bei bleibendem stationaerem Fehler erhoehen

**Option B: Ziegler-Nichols (bei starker Abweichung)**
1. Ki = 0, Kd = 0 setzen
2. Kp erhoehen bis Dauerschwingung auftritt (K_krit)
3. Schwingperiode T_krit messen
4. PID-Parameter: Kp = 0,6 * K_krit, Ki = 2 * Kp / T_krit, Kd = Kp * T_krit / 8

### 6.4 Akzeptanzkriterien

| Kriterium | Grenzwert |
|---|---|
| Anstiegszeit (0-90 %) | < 500 ms |
| Ueberschwingen | < 15 % |
| Stationaerer Regelfehler | < 5 % |
| Einschwingzeit | < 1 s |
| Symmetrie (Links vs. Rechts) | Differenz < 10 % |
| Regelfrequenz (50 Hz) | Jitter < 2 ms |

---

## 7) micro-ROS Kommunikationstest

### 7.1 UART-Verbindung ESP32-S3 <-> RPi5

- [ ] ESP32-S3 ueber USB-C mit RPi5 verbunden
- [ ] Device enumeriert als `/dev/ttyACM*`
- [ ] udev-Regel fuer `/dev/amr_esp32` eingerichtet
- [ ] micro-ROS Agent Docker-Container gestartet
- [ ] Agent erkennt ESP32-S3 Client (Session aufgebaut)
- [ ] Session-Aufbauzeit dokumentieren: ______ Sekunden

### 7.2 Topic-Verifikation

- [ ] `/odom` wird vom ESP32 publiziert: `ros2 topic list | grep odom`
- [ ] `/cmd_vel` wird vom ESP32 empfangen: `ros2 topic list | grep cmd_vel`
- [ ] Odometrie-Nachricht korrekt formatiert: `ros2 topic echo /odom --once`
- [ ] Frame IDs korrekt: `header.frame_id = "odom"`, `child_frame_id = "base_link"`
- [ ] Odometrie-Werte plausibel bei Stillstand (x, y, theta nahe 0)
- [ ] Odometrie-Werte aendern sich bei manueller Raddrehung

### 7.3 Publikationsrate und Latenz

- [ ] Odometrie-Rate messen: `ros2 topic hz /odom` (SOLL: 20 Hz, Toleranz: +/- 2 Hz)
- [ ] Rate ueber 5 Minuten stabil (keine Aussetzer)
- [ ] Regelschleifenfrequenz pruefen: 50 Hz auf Core 1 (per Firmware-Diagnose oder Timing-Pin)

**Protokoll:**

| Messung | Rate [Hz] | Std.-Abw. [Hz] | Bemerkung |
|---|---|---|---|
| /odom (1 min) | ______ | ______ | ______ |
| /odom (5 min) | ______ | ______ | ______ |

### 7.4 Paketverlust

- [ ] Nachrichten zaehlen: `ros2 topic hz /odom -w 1000` ueber 60 Sekunden
- [ ] Erwartete Nachrichten: 20 Hz * 60 s = 1200
- [ ] Empfangene Nachrichten: ______
- [ ] Verlustrate berechnen: (1 - empfangen/erwartet) * 100 %
- [ ] Verlustrate dokumentieren: ______ %

**Akzeptanzkriterium:** Paketverlust < 0,1 % (aus Bachelorarbeit N01).

### 7.5 Failsafe-Test

- [ ] Waehrend Fahrt: micro-ROS Agent stoppen
- [ ] Motoren muessen innerhalb von `FAILSAFE_TIMEOUT_MS = 1000 ms` stoppen
- [ ] Agent neu starten: Session wird automatisch wiederhergestellt
- [ ] Motoren reagieren wieder auf cmd_vel

---

## 8) Regressionstests

### 8.1 Testmatrix aus Kapitel 6 als Referenz

Die folgende Testmatrix basiert auf den Validierungstests der Bachelorarbeit (Kapitel 6). Alle Tests muessen mit den neuen Parametern wiederholt werden.

**KRITISCHER HINWEIS:** Die in Kapitel 6 dokumentierten Ergebnisse basieren auf:
- Radradius: 32 mm (NEU: 32,5 mm)
- Spurbreite: 145 mm (NEU: 178 mm)
- Encoder: 1440 Ticks/Rev Quadratur (NEU: ~374 Ticks/Rev A-only)
- MCU: generischer ESP32 (NEU: XIAO ESP32-S3)

Alle numerischen Ergebnisse sind nach Migration **ungueltig** und muessen neu erhoben werden.

### 8.2 Subsystem-Verifikation (Abschnitt 6.2)

| Test | Kapitel-6-Referenz | Neuer Status | Ergebnis |
|---|---|---|---|
| PID-Regelguete (Sprungantwort) | Kp=1,5, Ki=0,5 erfuellt | - [ ] Neu testen | ______ |
| Regelschleifenfrequenz (50 Hz) | Jitter < 2 ms erfuellt | - [ ] Neu testen | ______ |
| Odometrie unkalibriert | Systematischer Versatz gemessen | - [ ] Neu testen | ______ |
| UMBmark-Kalibrierung | Faktor >= 10 Verbesserung | - [ ] Neu testen | ______ |
| micro-ROS Publikationsrate | 20 Hz stabil | - [ ] Neu testen | ______ |
| micro-ROS Paketverlust | < 0,1 % | - [ ] Neu testen | ______ |

### 8.3 Navigations-Validierung (Abschnitt 6.3)

| Test | Kapitel-6-Referenz | Neuer Status | Ergebnis |
|---|---|---|---|
| Kartierungsqualitaet (ATE) | ATE = 0,16 m (< 0,20 m) | - [ ] Neu testen | ______ |
| Navigationsgenauigkeit (xy) | 6,4 cm +/- 2,1 cm | - [ ] Neu testen | ______ |
| Navigationsgenauigkeit (Gier) | 4,2 Grad +/- 1,8 Grad | - [ ] Neu testen | ______ |
| Statische Hindernisvermeidung | 0 Kollisionen in 15 Begegnungen | - [ ] Neu testen | ______ |
| Dynamische Hindernisvermeidung | 8/10 unmittelbar ausgewichen | - [ ] Neu testen | ______ |
| Recovery Behaviors | 8/10 Blockaden aufgeloest | - [ ] Neu testen | ______ |

### 8.4 Docking-Validierung (Abschnitt 6.4)

| Test | Kapitel-6-Referenz | Neuer Status | Ergebnis |
|---|---|---|---|
| Docking-Erfolgsquote | 8/10 Versuche | - [ ] Neu testen | ______ |
| Lateraler Versatz | 1,3 cm +/- 0,5 cm | - [ ] Neu testen | ______ |
| Orientierungsfehler | 2,8 Grad +/- 1,2 Grad | - [ ] Neu testen | ______ |

### 8.5 Ressourcenverbrauch (Abschnitt 6.5)

| Test | Kapitel-6-Referenz | Neuer Status | Ergebnis |
|---|---|---|---|
| RPi5 CPU (SLAM + Nav) | ~35 % (Spitze ~45 %) | - [ ] Neu testen | ______ |
| RPi5 RAM | ~1,8 GB / 8 GB | - [ ] Neu testen | ______ |
| ESP32 Flash | ~1,6 MB / 4 MB | - [ ] Neu testen | ______ |
| ESP32 RAM | ~180 KB / 520 KB (~35 %) | - [ ] Neu testen | ______ |
| RPP-Controller Frequenz | > 2000 Hz (> 100 Hz gefordert) | - [ ] Neu testen | ______ |

### 8.6 Erwartete Abweichungen durch Parameterwechsel

Die folgenden Auswirkungen werden durch die Parameteraenderungen erwartet:

| Aenderung | Erwartete Auswirkung | Kritikalitaet |
|---|---|---|
| Encoder 374 statt 1440 Ticks/Rev | Groebere Geschwindigkeitsmessung, hoehere Quantisierung. Moegliches PID-Rauschen bei niedrigen Geschwindigkeiten. | Hoch |
| A-only statt Quadratur | Keine hardware-basierte Richtungserkennung ueber Encoder. Richtung muss aus PWM-Ansteuerung abgeleitet werden. Bei Rutschen/Schieben falsche Ticks moeglich. | Mittel |
| Spurbreite 178 statt 145 mm | Groesserer Wenderadius. Geringere Empfindlichkeit gegenueber Orientierungsfehlern (positiv fuer Odometrie-Genauigkeit). | Gering (positiv) |
| Radradius 32,5 statt 32 mm | Minimal hoehere Lineargeschwindigkeit pro Tick. Vernachlaessigbar. | Gering |
| Dual-PWM statt DIR+PWM | Anderes Brems-/Auslaufverhalten. MDD3A bremst bei PWM_A=0, PWM_B=0 (Kurzschlussbremse). | Mittel |
| XIAO ESP32-S3 statt generischer ESP32 | Andere GPIO-Nummern (D0-D10 Mapping). USB-C statt Micro-USB. ESP32-S3 LX7-Cores statt LX6. | Gering |

---

## 9) Abnahmekriterien

### 9.1 Pass/Fail Kriterien pro Testbereich

| Testbereich | Pass-Kriterium | Fail-Kriterium |
|---|---|---|
| **Pre-Flash** | Alle Checklisten-Punkte abgehakt. Firmware kompiliert und startet. | Kompilierungsfehler, fehlendes USB-Device, falsche Spannungen. |
| **Encoder** | Ticks/Rev innerhalb 370-380. Reproduzierbar ueber 3 Durchgaenge (Abweichung < 2). | Ticks/Rev ausserhalb 350-400. Sporadische Ticks bei Stillstand. Nicht reproduzierbar. |
| **Motorsteuerung** | Korrekte Drehrichtung. Deadzone 30-40. Notaus funktional. | Falsche Drehrichtung. Motoren laufen bei PWM < 30 nicht an oder laufen bei PWM 0 weiter. |
| **Kinematik** | Geradeausfahrt 1 m: Abweichung < 5 %. Drehung 90 Grad: Abweichung < 5 Grad. | Abweichung > 10 % oder > 10 Grad. Starker systematischer Drift. |
| **UMBmark** | Faktor >= 10 Fehlerreduktion nach Kalibrierung. | Faktor < 5 Fehlerreduktion. Keine Konvergenz der Cluster. |
| **PID** | Einschwingzeit < 1 s. Ueberschwingen < 15 %. Stationaerer Fehler < 5 %. | Dauerschwingung. Ueberschwingen > 30 %. Stationaerer Fehler > 10 %. |
| **micro-ROS** | 20 Hz stabil. Paketverlust < 0,1 %. Session-Aufbau < 10 s. | Rate < 15 Hz. Paketverlust > 1 %. Kein Session-Aufbau. |
| **Navigation** | ATE < 0,20 m. Positionsabweichung < 10 cm (xy), < 8 Grad (Gier). | ATE > 0,30 m. Positionsabweichung > 15 cm. Karte unbrauchbar. |
| **Docking** | Erfolgsquote >= 8/10. Lateraler Versatz < 2 cm. Orientierung < 5 Grad. | Erfolgsquote < 6/10. Versatz > 3 cm. |
| **Ressourcen** | RPi5 CPU < 80 %. RPP > 100 Hz. | RPi5 CPU > 80 %. RPP < 100 Hz. System instabil. |

### 9.2 Toleranzen und Grenzwerte (zusammengefasst)

| Parameter | Akzeptanzgrenze | Quelle |
|---|---|---|
| Positionstoleranz (Navigation) | 10 cm (xy), 8 Grad (Gier) | Bachelorarbeit N02 |
| Docking-Praezision | 2 cm lateral, 5 Grad Orientierung | Bachelorarbeit F03 |
| Regelschleifenfrequenz | 50 Hz, Jitter < 2 ms | Bachelorarbeit N01 |
| Odometrie-Publikation | 20 Hz +/- 2 Hz | Firmware-Konfiguration |
| Paketverlust micro-ROS | < 0,1 % | Bachelorarbeit N01 |
| CPU-Auslastung RPi5 | < 80 % im Normalbetrieb | Bachelorarbeit N05 |
| RPP-Controller Frequenz | > 100 Hz | Bachelorarbeit N05 |
| UMBmark Fehlerreduktion | Faktor >= 10 | Bachelorarbeit F05 |
| ATE Kartierung | < 0,20 m | Bachelorarbeit F01 |
| Docking-Erfolgsrate | >= 80 % (8/10) | Bachelorarbeit F03 |
| Recovery-Behavior Erfolg | >= 80 % | Bachelorarbeit F04 |
| PWM-Deadzone | 30-40 | config.h: PWM_DEADZONE = 35 |
| Encoder Ticks/Rev | 370-380 | config.h: ~374 |
| Failsafe-Timeout | 1000 ms | config.h: FAILSAFE_TIMEOUT_MS |

### 9.3 Gesamtabnahme

Die Gesamtabnahme gilt als bestanden, wenn:

- [ ] Alle Pre-Flash-Checks bestanden
- [ ] Encoder-Validierung bestanden
- [ ] Motorsteuerungs-Tests bestanden
- [ ] Kinematik-Validierung bestanden (Geradeaus + Drehung)
- [ ] UMBmark-Kalibrierung durchgefuehrt und Faktor >= 10 erreicht
- [ ] PID-Regelguete innerhalb Akzeptanzkriterien
- [ ] micro-ROS Kommunikation stabil (20 Hz, < 0,1 % Verlust)
- [ ] Navigation funktional (ATE < 0,20 m, Zieltoleranzen eingehalten)
- [ ] Docking funktional (>= 8/10 Erfolgsrate)
- [ ] Ressourcenverbrauch innerhalb Grenzen (CPU < 80 %, RPP > 100 Hz)

**Reihenfolge der Durchfuehrung:** Die Tests sind sequentiell abzuarbeiten, da jeder Bereich auf den vorherigen aufbaut (Encoder -> Motoren -> Kinematik -> UMBmark -> PID -> micro-ROS -> Navigation -> Docking).

---

*Erstellt: 2025-12-19 | Projekt: AMR Bachelor-Thesis | Quellen: config.h v1.0.0, hardware-setup.md, Bachelorarbeit Kapitel 6, Borenstein et al. 1996*
