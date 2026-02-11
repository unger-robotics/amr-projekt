# 02 -- Antriebsstrang & Leistungselektronik

Dieses Dokument beschreibt saemtliche Komponenten des Antriebsstrangs und der Leistungselektronik des AMR-Projekts. Es umfasst den Dual-Motortreiber, die DC-Getriebemotoren mit Hall-Encodern, die MOSFET-Schaltstufen sowie die zugehoerige PWM-Konfiguration und kinematischen Parameter. Alle technischen Daten wurden aus den jeweiligen Datenblaettern und der Firmware-Konfiguration (`config.h`) extrahiert.

---

## 1. Cytron MDD3A -- Dual-Motortreiber

### 1.1 Uebersicht

Der Cytron MDD3A ist ein kompakter Dual-Kanal-DC-Motortreiber fuer buerstenbehaftete Gleichstrommotoren. Er wird im AMR im **Dual-PWM-Modus** betrieben, bei dem pro Motorkanal zwei PWM-Eingaenge (A und B) die Drehrichtung und Geschwindigkeit bestimmen. Dadurch entfaellt ein separater Richtungspin (DIR), was die Ansteuerung vereinfacht.

![Antriebsaufbau](../datasheet/images/Antrieb.png)

### 1.2 Technische Spezifikationen

| Parameter | Min | Max | Einheit | Bemerkung |
|---|---|---|---|---|
| Eingangsspannung (V_in) | 4 | 16 | VDC | Betrieb am 3S Li-Ion: 11,1--12,6 V |
| Dauerstrom pro Kanal | -- | 3 | A | Kontinuierlich |
| Spitzenstrom pro Kanal (< 5 s) | -- | 5 | A | Kurzzeitig |
| Logikpegel Low (M1A/M1B/M2A/M2B) | 0 | 0,5 | V | |
| Logikpegel High (M1A/M1B/M2A/M2B) | 1,7 | 12 | V | ESP32-S3 GPIO: 3,3 V (kompatibel) |
| PWM-Frequenz | DC | 20 | kHz | Ausgangsfrequenz = Eingangsfrequenz |
| 5V-Ausgang (5VO) | -- | 200 | mA | Zum Versorgen des Mikrocontrollers |
| Abmessungen (L x B) | -- | -- | mm | 48,26 x 43,18 (Bohrungen: 41,66 x 36,58) |
| Befestigungsbohrungen | -- | -- | mm | 4x, Durchmesser 3 mm |

### 1.3 Dual-PWM Betriebsmodus (Wahrheitstabelle)

Im Dual-PWM-Modus wird jeder Motor ueber zwei PWM-Signale gesteuert. Die Drehrichtung ergibt sich aus der Kombination der Eingaenge:

| Input A (M1A/M2A) | Input B (M1B/M2B) | Output A | Output B | Motorverhalten |
|---|---|---|---|---|
| Low | Low | Low | Low | Bremse (Kurzschluss) |
| High (PWM) | Low | High | Low | Vorwaerts* |
| Low | High (PWM) | Low | High | Rueckwaerts* |
| High | High | High | High | Bremse (Kurzschluss) |

*Die tatsaechliche Drehrichtung haengt von der Motorverdrahtung ab. Ein Tausch der Motoranschluesse kehrt die Richtung um.

### 1.4 Anschlussbelegung im AMR

**Signaleingaenge (Header-Stiftleiste):**

| Pin am MDD3A | Funktion | XIAO-Pin | LEDC-Kanal | Kabelfarbe |
|---|---|---|---|---|
| M1A | Motor Links Vorwaerts-PWM | D0 | 1 (getauscht) | Rot |
| M1B | Motor Links Rueckwaerts-PWM | D1 | 0 (getauscht) | Weiss |
| M2A | Motor Rechts Vorwaerts-PWM | D2 | 3 (getauscht) | Rot |
| M2B | Motor Rechts Rueckwaerts-PWM | D3 | 2 (getauscht) | Weiss |
| 5VO | +5 V Ausgang (max. 200 mA) | -- | -- | -- |
| GND | Masse | GND | -- | Schwarz |

**Hinweis:** Die LEDC-Kanalzuordnung in `config.h` ist gegenueber der physischen Verdrahtung A/B getauscht, um die korrekte Drehrichtung sicherzustellen.

**Leistungsanschluesse (Schraubklemmen):**

| Klemme | Funktion | Kabelquerschnitt |
|---|---|---|
| VB+ | +12 V (Batterie ueber BMS/Sicherung) | 1,5 mm² |
| VB- | GND (Sternpunkt-Masse) | 1,5 mm² |
| Motor 1 (M1A/M1B) | Motor Links Ausgang | abhaengig vom Motor |
| Motor 2 (M2A/M2B) | Motor Rechts Ausgang | abhaengig vom Motor |

### 1.5 Schutzfunktionen

Der MDD3A verfuegt ueber einen integrierten **Verpolungsschutz** am Leistungseingang (VB+/VB-). Wird die Batterie falsch gepolt angeschlossen, nimmt der Treiber keinen Schaden. Dieser Schutz ist besonders bei der Erstinbetriebnahme und beim Batteriewechsel relevant.

### 1.6 Zusatzfunktionen auf dem Board

Der MDD3A bietet pro Kanal:

- **2 Status-LEDs**: M1A/M2A leuchtet bei Vorwaertsfahrt, M1B/M2B bei Rueckwaertsfahrt
- **2 Testtaster**: Ermoeglichen manuellen Motortest mit voller Geschwindigkeit ohne Mikrocontroller
- **Power-LED**: Zeigt an, dass der Treiber mit Spannung versorgt wird

Die Testtaster sind besonders bei der Erstinbetriebnahme nuetzlich, um Motoranschluss und Drehrichtung vor der Firmware-Integration zu pruefen.

---

## 2. JGA25-370 DC-Getriebemotoren

### 2.1 Uebersicht

Die JGA25-370 sind kompakte 12-V-DC-Getriebemotoren mit integriertem Hall-Encoder. Sie werden paarweise als Differentialantrieb des AMR eingesetzt. Der Motor verfuegt ueber ein Metallgetriebe und einen 6-adrigen Anschluss (2x Motor, 4x Encoder).

![JGA25-370 Getriebemotor](../datasheet/images/JGA25-370 DC-Getriebemotoren.png)

![JGA25-370 Abmessungen](../datasheet/images/JGA25-370 DC-Getriebemotoren_2.png)

### 2.2 Technische Spezifikationen

| Parameter | Wert | Einheit | Bemerkung |
|---|---|---|---|
| Nennspannung | 12 | V | Betrieb am 3S Li-Ion (11,1--12,6 V) |
| Leerlaufdrehzahl | 130 | RPM | Laut Schaltplan-Beschriftung |
| Leerlaufstrom | 35,5 | mA | Aus Schaltplan (ca. 0,5 A Nennstrom) |
| Getriebeuebersetzung | -- | -- | Metallgetriebe, integriert |
| Anschlussleitungen | 6 | Stueck | 2x Motor + 4x Encoder |
| Encoder-Typ | Hall-Effekt | -- | Inkremental, A- und B-Kanal |

### 2.3 Motorkabel-Belegung (6-adrig)

Aus dem Schaltplan lassen sich folgende Adern identifizieren:

| Ader | Farbe | Funktion | Anschluss |
|---|---|---|---|
| 1 | Rot | Motor (+) | MDD3A Motor-Ausgang A |
| 2 | Schwarz | Masse (Motor) | MDD3A Motor-Ausgang B |
| 3 | Gelb | Encoder Phase A (Speed) | XIAO D6 (Links) / D7 (Rechts) |
| 4 | Gruen | Encoder Phase B (nicht verwendet) | Isoliert (A-only Betrieb) |
| 5 | Blau | Encoder VCC | +3,3 V |
| 6 | Weiss | Encoder GND | GND |

**Wichtig:** Im aktuellen Design (Phase 1/4) wird nur **Phase A** (Gelb) angeschlossen. Phase B (Gruen) wird isoliert und nicht verwendet. Dies reicht fuer die Drehzahlmessung aus, ermoeglicht jedoch keine Quadratur-Dekodierung zur Richtungserkennung ueber den Encoder allein. Die Drehrichtung wird stattdessen aus der PWM-Ansteuerung abgeleitet.

### 2.4 Hall-Encoder Spezifikationen

| Parameter | Links | Rechts | Einheit | Bemerkung |
|---|---|---|---|---|
| Ticks pro Umdrehung | 374,3 | 373,6 | Ticks/Rev | Noch nicht endgueltig kalibriert |
| Mittlerer Wert | 374,0 | -- | Ticks/Rev | Durchschnitt beider Raeder |
| Meter pro Tick (links) | 0,000546 | -- | m/Tick | Berechnet: Radumfang / Ticks |
| Meter pro Tick (rechts) | 0,000547 | -- | m/Tick | Berechnet: Radumfang / Ticks |
| Anschluss-Pins | D6 | D7 | -- | Interrupt-faehige GPIO-Pins |
| Encoder-Versorgung | 3,3 V | 3,3 V | V | Ueber ESP32-S3 3,3-V-Rail |

**Berechnung Meter pro Tick:**

```
Radumfang = pi * Raddurchmesser = 3,14159 * 0,065 m = 0,20420 m
Meter/Tick_links  = 0,20420 m / 374,3 = 0,000546 m/Tick
Meter/Tick_rechts = 0,20420 m / 373,6 = 0,000547 m/Tick
```

**Kalibrierungsmethode:** Die Ticks-pro-Umdrehung-Werte wurden mittels 10-Umdrehungen-Test ermittelt (Vermerk in `config.h`: „noch nicht kalibriert"). Fuer die endgueltige Kalibrierung wird der UMBmark-Test empfohlen (siehe Kapitel Validierung der Bachelorarbeit).

### 2.5 Encoder-Versorgung und Pegelanpassung

Die Hall-Encoder benoetigen eine separate Versorgungsspannung (VCC + GND) zusaetzlich zur Signalleitung. Im AMR wird die Encoder-Versorgung mit **3,3 V** aus dem ESP32-S3 realisiert. Dies hat den Vorteil, dass keine Pegelanpassung (Level Shifter) am Signalausgang erforderlich ist, da die Encoder-Ausgaenge direkt mit dem 3,3-V-Logikpegel des ESP32-S3 kompatibel sind.

Sollten die Encoder bei 3,3 V nicht stabil arbeiten, muss auf 5-V-Versorgung umgestellt werden. In diesem Fall ist ein **Spannungsteiler** oder **Level Shifter** am Phase-A-Signal zwingend erforderlich, um die ESP32-S3-Eingaenge (max. 3,3 V) zu schuetzen.

---

## 3. MOSFET-Schaltstufen

### 3.1 IRLZ24N -- Low-Side-Schalter fuer LED-Streifen

#### 3.1.1 Uebersicht

Der IRLZ24N ist ein N-Kanal Logic-Level Power MOSFET im TO-220AB-Gehaeuse von International Rectifier. Er dient im AMR als **Low-Side-Schalter** zum Schalten eines 12-V-LED-Streifens ueber den ESP32-S3 GPIO-Pin D10. Dank der niedrigen Gate-Threshold-Spannung (1,0--2,0 V) laesst er sich direkt mit 3,3-V-Logikpegeln ansteuern.

#### 3.1.2 Technische Spezifikationen (Absolute Maximum Ratings)

| Parameter | Symbol | Min | Typ | Max | Einheit | Bemerkung |
|---|---|---|---|---|---|---|
| Drain-Source-Spannung | V_DSS | -- | -- | 55 | V | Ausreichend fuer 12 V Rail |
| Dauerstrom (T_C = 25 C) | I_D | -- | -- | 18 | A | Weit ueberdimensioniert |
| Dauerstrom (T_C = 100 C) | I_D | -- | -- | 13 | A | |
| Impulsstrom | I_DM | -- | -- | 72 | A | |
| Verlustleistung (T_C = 25 C) | P_D | -- | -- | 45 | W | |
| Gate-Source-Spannung | V_GS | -- | -- | +-16 | V | |
| Betriebstemperatur | T_J | -55 | -- | +175 | C | |

#### 3.1.3 Elektrische Kennwerte (T_J = 25 C)

| Parameter | Symbol | Min | Typ | Max | Einheit | Bedingungen |
|---|---|---|---|---|---|---|
| Gate-Threshold-Spannung | V_GS(th) | 1,0 | -- | 2,0 | V | V_DS = V_GS, I_D = 250 uA |
| R_DS(on) bei V_GS = 10 V | R_DS(on) | -- | -- | 0,060 | Ohm | I_D = 11 A |
| R_DS(on) bei V_GS = 5 V | R_DS(on) | -- | -- | 0,075 | Ohm | I_D = 11 A |
| R_DS(on) bei V_GS = 4 V | R_DS(on) | -- | -- | 0,105 | Ohm | I_D = 9 A |
| Einschaltverzoegerung | t_d(on) | -- | 7,1 | -- | ns | V_DD = 28 V, I_D = 11 A |
| Anstiegszeit | t_r | -- | 74 | -- | ns | |
| Ausschaltverzoegerung | t_d(off) | -- | 20 | -- | ns | R_G = 12 Ohm, V_GS = 5 V |
| Abfallzeit | t_f | -- | 29 | -- | ns | |

#### 3.1.4 Thermische Kennwerte

| Parameter | Symbol | Typ | Max | Einheit |
|---|---|---|---|---|
| Waermewiderstand Junction-Case | R_thJC | -- | 3,3 | C/W |
| Waermewiderstand Case-Sink | R_thCS | 0,50 | -- | C/W |
| Waermewiderstand Junction-Ambient | R_thJA | -- | 62 | C/W |

#### 3.1.5 Schaltung im AMR

Aus dem handschriftlichen Schaltplan ergibt sich folgende Beschaltung:

```
       +12 V Rail
          |
     [LED-Streifen]
          |
       Drain (D)
          |
    IRLZ24N (TO-220)
          |
       Source (S)
          |
         GND

Gate (G) <--- D10 (ESP32-S3)
   |
 [100 kOhm]
   |
  GND
```

**Funktionsprinzip:**

- Der ESP32-S3 steuert das Gate ueber Pin D10 mit einem PWM-Signal (5 kHz, 8-Bit) an
- Ein **100-kOhm-Pulldown-Widerstand** am Gate stellt sicher, dass der MOSFET beim Booten des ESP32 (undefinierte GPIO-Zustaende) zuverlaessig sperrt
- Der MOSFET schaltet die Masse-Seite des LED-Streifens (Low-Side-Topologie)
- Bei V_GS = 3,3 V liegt der IRLZ24N sicher oberhalb der Threshold-Spannung (max. 2,0 V) und schaltet voll durch

**PWM-Konfiguration fuer LED-Steuerung (aus `config.h`):**

| Parameter | Wert | Einheit |
|---|---|---|
| PWM-Frequenz | 5.000 | Hz |
| Aufloesung | 8 | Bit (0--255) |
| LEDC-Kanal | 4 | -- |
| GPIO-Pin | D10 | -- |

**Hinweis zur Freilaufdiode:** Da der LED-Streifen eine rein ohmsche bzw. kapazitive Last darstellt (keine Induktivitaet), ist **keine Freilaufdiode** erforderlich. Bei einem spaeteren Anschluss induktiver Lasten (Relais, Magnetventile) muss eine Freilaufdiode (z. B. 1N4007) parallel zur Last geschaltet werden.

### 3.2 2N7000 -- Logic-Level Kleinsignal-MOSFET

#### 3.2.1 Uebersicht

Der 2N7000 ist ein N-Kanal Enhancement-Mode MOSFET im TO-92-Gehaeuse. Er ist fuer Kleinsignal-Schaltanwendungen bei niedrigen Spannungen und Stroemen ausgelegt. Im AMR-Kontext steht er als optionales Schaltelement fuer Low-Power-Lasten oder als Gate-Treiber zur Verfuegung.

#### 3.2.2 Technische Spezifikationen (Absolute Maximum Ratings)

| Parameter | Symbol | Wert | Einheit | Bemerkung |
|---|---|---|---|---|
| Drain-Source-Spannung | V_DSS | 60 | V | |
| Gate-Source-Spannung (Dauer) | V_GS | +-20 | V | |
| Dauerstrom | I_D | 115 | mA | Deutlich niedriger als IRLZ24N |
| Impulsstrom | I_DM | 800 | mA | |
| Verlustleistung | P_D | 400 | mW | |
| Betriebstemperatur | T_J | -55 bis +150 | C | |

#### 3.2.3 Elektrische Kennwerte (T_a = 25 C)

| Parameter | Symbol | Min | Typ | Max | Einheit | Bedingungen |
|---|---|---|---|---|---|---|
| Gate-Threshold-Spannung | V_GS(th) | 1,0 | 2,1 | 2,5 | V | V_DS = V_GS, I_D = 250 uA |
| R_DS(on) bei V_GS = 10 V | R_DS(on) | -- | 1,2 | 7,5 | Ohm | I_D = 500 mA |
| R_DS(on) bei V_GS = 5 V | R_DS(on) | -- | 1,7 | 7,5 | Ohm | I_D = 50 mA |
| Drain-Source-Durchbruchspannung | BV_DSS | 60 | -- | -- | V | |
| Einschaltzeit | t_ON | -- | -- | 20 | ns | |
| Ausschaltzeit | t_OFF | -- | -- | 20 | ns | |

#### 3.2.4 Pinbelegung (TO-92, von vorne betrachtet)

| Pin | Funktion |
|---|---|
| 1 | Source (S) |
| 2 | Gate (G) |
| 3 | Drain (D) |

#### 3.2.5 Vergleich IRLZ24N vs. 2N7000

| Eigenschaft | IRLZ24N | 2N7000 | Einheit |
|---|---|---|---|
| Gehaeuse | TO-220AB | TO-92 | -- |
| V_DSS | 55 | 60 | V |
| I_D (Dauer) | 18.000 | 115 | mA |
| R_DS(on) (V_GS = 5 V) | 0,075 | 1,7 (typ.) | Ohm |
| V_GS(th) | 1,0--2,0 | 1,0--2,5 | V |
| Verlustleistung | 45.000 | 400 | mW |
| Einsatz im AMR | LED-Streifen (12 V, Leistung) | Kleinsignal / Reserve | -- |

Der IRLZ24N ist fuer leistungsbehaftete Schaltaufgaben (LED-Streifen, ggf. weitere 12-V-Lasten) vorgesehen, waehrend der 2N7000 fuer Kleinsignalanwendungen mit Stroemen unter 100 mA geeignet ist. Beide MOSFETs sind Logic-Level-Typen und koennen direkt mit 3,3 V des ESP32-S3 angesteuert werden.

---

## 4. PWM-Konfiguration (Firmware)

### 4.1 Uebersicht der PWM-Kanaele

Der ESP32-S3 verwendet das LEDC-Peripheriemodul (LED Control) fuer die PWM-Erzeugung. Insgesamt werden **5 LEDC-Kanaele** konfiguriert:

| LEDC-Kanal | GPIO-Pin | Funktion | Frequenz | Aufloesung | Bemerkung |
|---|---|---|---|---|---|
| 0 | D1 | Motor Links B (Rueckwaerts) | 20 kHz | 8 Bit | Getauscht mit Kanal 1 |
| 1 | D0 | Motor Links A (Vorwaerts) | 20 kHz | 8 Bit | Getauscht mit Kanal 0 |
| 2 | D3 | Motor Rechts B (Rueckwaerts) | 20 kHz | 8 Bit | Getauscht mit Kanal 3 |
| 3 | D2 | Motor Rechts A (Vorwaerts) | 20 kHz | 8 Bit | Getauscht mit Kanal 2 |
| 4 | D10 | LED-Streifen (IRLZ24N Gate) | 5 kHz | 8 Bit | Separate Frequenz |

### 4.2 Motor-PWM (20 kHz)

| Parameter | Wert | Bemerkung |
|---|---|---|
| Frequenz | 20.000 Hz | Oberhalb der menschlichen Hoerschwelle (unhoerbar) |
| Aufloesung | 8 Bit | Wertebereich: 0--255 |
| Maximaler PWM-Wert | 255 | Volle Geschwindigkeit |
| Deadzone | 35 | PWM-Wert, unterhalb dessen der Motor nicht anlaeuft |

**Deadzone-Kompensation:** Die `PWM_DEADZONE` von 35 (aus `config.h`) definiert den minimalen PWM-Wert, ab dem der Motor tatsaechlich anlaeuft. PWM-Werte unterhalb dieses Schwellwerts ueberwinden die Haftreibung und die Gegen-EMK des Motors nicht. Die PID-Regelschleife muss diese Deadzone beruecksichtigen, um ein sauberes Anlaufverhalten zu gewaehrleisten.

**Frequenzwahl:** Die 20-kHz-PWM-Frequenz wurde gewaehlt, um stoerende Geraeusche zu vermeiden. Buerstenmotoren erzeugen bei PWM-Frequenzen im hoerbaren Bereich (< 20 kHz) ein charakteristisches Pfeifen. Der MDD3A unterstuetzt PWM-Frequenzen von DC bis 20 kHz, wobei die Ausgangsfrequenz der Eingangsfrequenz entspricht.

### 4.3 LED-PWM (5 kHz)

| Parameter | Wert | Bemerkung |
|---|---|---|
| Frequenz | 5.000 Hz | Ausreichend fuer flimmerfreie LED-Dimmung |
| Aufloesung | 8 Bit | 256 Helligkeitsstufen |
| LEDC-Kanal | 4 | Separater Kanal, unabhaengig von Motoren |
| GPIO-Pin | D10 | Ueber IRLZ24N Low-Side-Schalter |

### 4.4 Getauschte Kanalzuordnung

In `config.h` sind die LEDC-Kanaele A und B pro Motor **vertauscht** gegenueber der physischen Zuordnung:

```c
#define PWM_CH_LEFT_A 1  // war 0 -- getauscht fuer korrekte Richtung
#define PWM_CH_LEFT_B 0  // war 1
#define PWM_CH_RIGHT_A 3 // war 2 -- getauscht fuer korrekte Richtung
#define PWM_CH_RIGHT_B 2 // war 3
```

Dies ist eine Software-Korrektur, um die tatsaechliche Drehrichtung der Motoren an die erwartete Konvention (PWM_A = Vorwaerts) anzupassen, ohne die physische Verdrahtung zu aendern.

---

## 5. Kinematische Parameter

### 5.1 Differentialantrieb-Geometrie

Der AMR verwendet einen **Differentialantrieb** (Differential Drive) mit zwei unabhaengig angetriebenen Raedern. Die kinematischen Parameter definieren die Beziehung zwischen Radgeschwindigkeiten und Roboterbewegung.

| Parameter | Symbol | Wert | Einheit | Quelle |
|---|---|---|---|---|
| Raddurchmesser | d | 0,065 | m (65 mm) | `config.h`: WHEEL_DIAMETER |
| Radradius | r | 0,0325 | m (32,5 mm) | Berechnet: d / 2 |
| Spurbreite (Achsabstand) | L | 0,178 | m (178 mm) | `config.h`: WHEEL_BASE |
| Radumfang | U | 0,20420 | m | Berechnet: pi * d |

**Hinweis:** Die CLAUDE.md der Bachelorarbeit nennt Radradius 32 mm und Spurbreite 145 mm. Die Werte in `config.h` (32,5 mm bzw. 178 mm) sind die aktuellen, gemessenen Werte und haben Vorrang.

### 5.2 Odometrie-Berechnung

Die Odometrie-Berechnung basiert auf der Vorwaertskinematik des Differentialantriebs:

```
v_links  = delta_ticks_links  * METERS_PER_TICK_LEFT  / delta_t
v_rechts = delta_ticks_rechts * METERS_PER_TICK_RIGHT / delta_t

v_linear  = (v_rechts + v_links) / 2
omega     = (v_rechts - v_links) / WHEEL_BASE

delta_x     = v_linear * cos(theta) * delta_t
delta_y     = v_linear * sin(theta) * delta_t
delta_theta = omega * delta_t
```

### 5.3 Mechanische Anmerkungen

Aus dem Schaltplan sind zusaetzlich folgende mechanische Daten ersichtlich:

| Parameter | Wert | Einheit |
|---|---|---|
| Gesamtgewicht (Roboter) | ca. 1.534 | g |
| Spurweite (mechanisch, Schaltplan) | 23 | mm |

**Hinweis:** Die im Schaltplan notierte „Spurweite 23 mm" bezieht sich vermutlich auf eine mechanische Abmessung des Chassis (Achsbreite oder Radaufstandsflaeche), nicht auf die kinematische Spurbreite (Radmitte zu Radmitte = 178 mm), die in `config.h` definiert ist.

---

## 6. Servo-System (Pan/Tilt) -- Optional

### 6.1 Uebersicht

Das optionale Pan/Tilt-System verwendet zwei MG90S-Mikroservos zur Ausrichtung einer Kamera (Global Shutter Camera). Die Servos werden ueber PWM-Signale vom ESP32-S3 gesteuert, erhalten ihre Leistungsversorgung jedoch von einem **separaten 5-V-Buck-Konverter** (LM2596), nicht vom ESP32 oder Raspberry Pi.

![MG90S Servos](../datasheet/images/MG90S Servos.png)

### 6.2 Anschlussbelegung

| Servo | Funktion | XIAO-Pin | PWM-Signal | Stromversorgung |
|---|---|---|---|---|
| Servo 1 | Pan (Drehen, horizontal) | D8 | PWM-Signal (3,3 V) | Extern 5 V (LM2596) |
| Servo 2 | Tilt (Neigen, vertikal) | D9 | PWM-Signal (3,3 V) | Extern 5 V (LM2596) |

### 6.3 Verkabelung (3-adrig pro Servo)

| Ader | Farbe (typisch) | Funktion |
|---|---|---|
| Signal | Orange | PWM-Eingang (vom ESP32-S3) |
| VCC | Rot | +5 V (vom separaten Buck-Konverter) |
| GND | Braun/Schwarz | Masse (Sternpunkt-GND) |

**Wichtig:** Die Servo-Masse muss mit dem gemeinsamen Sternpunkt-GND verbunden sein, damit das PWM-Signal korrekt referenziert wird. Die 5-V-Versorgung darf **nicht** aus dem ESP32 oder dem Pi-5V-Rail gezogen werden, da die Servo-Stromspitzen (kurzzeitig bis 2 A fuer zwei MG90S) die Logik-Versorgung stoeren koennten.

---

## 7. Zusammenfassung der Leistungselektronik-Topologie

### 7.1 Signalfluss Antriebsstrang

```
ROS2 cmd_vel (Raspberry Pi)
      |
      | micro-ROS / UART
      v
ESP32-S3 (Regelschleife, Core 1, 50 Hz)
      |
      | Inverse Kinematik: v_linear, omega --> v_links, v_rechts
      | PID-Regler: Soll vs. Ist (Encoder-Feedback)
      v
PWM-Ausgaenge D0--D3 (20 kHz, 8-Bit)
      |
      v
Cytron MDD3A (Dual-PWM-Modus)
      |
      v
JGA25-370 Motoren (Links + Rechts)
      |
      | Hall-Encoder Phase A (Interrupt)
      v
ESP32-S3 Encoder-Eingaenge D6/D7
      |
      | Vorwaertskinematik: Ticks --> Odometrie
      v
Odometrie-Publish (Core 0, 20 Hz) --> ROS2
```

### 7.2 Strombudget Antriebsstrang

| Verbraucher | Spannung | Strom (typ.) | Strom (max.) | Bemerkung |
|---|---|---|---|---|
| Motor Links (JGA25-370) | 12 V | 0,035 A (Leerlauf) | 3 A (MDD3A-Limit) | Stall-Strom muss < 3 A sein |
| Motor Rechts (JGA25-370) | 12 V | 0,035 A (Leerlauf) | 3 A (MDD3A-Limit) | Stall-Strom muss < 3 A sein |
| LED-Streifen (via IRLZ24N) | 12 V | abhaengig | abhaengig | Last spezifisch dimensionieren |
| Servos (2x MG90S, optional) | 5 V | 0,1 A | 2 A (Peak) | Separater Buck-Konverter |
| MDD3A Eigenverbrauch | 12 V | gering | -- | Vernachlaessigbar |
| Encoder (2x Hall) | 3,3 V | < 10 mA | -- | Aus ESP32-S3 3,3 V Rail |

---

## 8. Inbetriebnahme-Checkliste Antriebsstrang

### 8.1 Vor dem ersten Einschalten

- [ ] MDD3A: VB+ und VB- korrekt an 12-V-Rail angeschlossen (Polaritaet pruefen, obwohl Verpolungsschutz vorhanden)
- [ ] MDD3A: Power-LED leuchtet nach Einschalten
- [ ] Motoren: Anschluesse an Motor-Ausgangsklemmen fest verschraubt
- [ ] Signal-Header: M1A/M1B/M2A/M2B korrekt mit D0--D3 verbunden
- [ ] GND: MDD3A-GND, ESP32-GND und Batterie-GND am Sternpunkt verbunden

### 8.2 Motor-Funktionstest (ohne Firmware)

- [ ] Testtaster M1A/M2A druecken: Beide Raeder drehen vorwaerts
- [ ] Testtaster M1B/M2B druecken: Beide Raeder drehen rueckwaerts
- [ ] Drehrichtung pruefen: Bei Vorwaertsfahrt muessen beide Raeder den Roboter vorwaerts bewegen
- [ ] Falls Richtung falsch: Motoranschluesse am MDD3A tauschen (nicht die Signalleitungen)

### 8.3 Encoder-Funktionstest

- [ ] Encoder-VCC (3,3 V) und GND angeschlossen
- [ ] Phase A (Gelb) an D6 (Links) und D7 (Rechts)
- [ ] Phase B (Gruen) isoliert
- [ ] Testprogramm: Rad von Hand drehen, Tick-Zaehler im seriellen Monitor beobachten
- [ ] Keine Spikes oder Sprungwerte bei Stillstand

### 8.4 LED-MOSFET-Test

- [ ] LED-Streifen an 12 V (Plus) und Drain des IRLZ24N angeschlossen
- [ ] 100-kOhm-Pulldown am Gate vorhanden
- [ ] Beim ESP32-Boot: LED bleibt aus (MOSFET sperrt)
- [ ] PWM-Test: LED laesst sich stufenlos dimmen (0--255)

---

*Quellen: Cytron MDD3A Datasheet Rev 1.0 (March 2019), International Rectifier IRLZ24N PD-91357C, UTC 2N7000 QW-R502-059.B, Projekt-Schaltplan (handschriftlich), config.h v1.0.0 (2025-12-12)*
