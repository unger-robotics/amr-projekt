# Pololu D36V50F6 – Abwärtsspannungsregler 6 V / 5,5 A

> **Technische Dokumentation** – Pololu Item #4092  
> Produktfamilie: D36V50Fx | Topologie: Synchroner Buck-Konverter (Step-Down Converter)  
> Quelle: [Pololu Produktseite](https://www.pololu.com/product/4092)

---

## 1 Übersicht und Einsatzzweck

Der D36V50F6 ist ein synchroner Abwärtsspannungsregler (Buck Converter), der Eingangsspannungen bis 50 V auf eine feste Ausgangsspannung von 6 V herunterregelt. Im Gegensatz zu linearen Reglern arbeitet der D36V50F6 als Schaltregler (Switched-Mode Power Supply, SMPS) und erreicht dabei typische Wirkungsgrade zwischen 80 % und 95 %. Der Effizienzvorteil gegenüber Linearreglern wächst mit steigender Differenz zwischen Eingangs- und Ausgangsspannung.

**Typische Anwendungen:**

- Servo- und Motorversorgung in mobilen Robotern (z. B. AMR-Plattformen)
- Spannungsversorgung für Einplatinencomputer und Sensorik aus Akkupacks
- Industrielle Steuerungen mit weitem Eingangsspannungsbereich
- Batteriebetriebene Systeme mit 2S- bis 12S-Lithium-Ionen- oder Bleiakkus

---

## 2 Technische Spezifikationen

### 2.1 Elektrische Kenndaten

| Parameter | Wert | Bemerkung |
|---|---|---|
| Ausgangsspannung | 6,0 V | Fest, ±4 % Genauigkeit |
| Eingangsspannung | 6,5 V … 50 V | Minimum abhängig von Dropout-Spannung (siehe Abschnitt 4) |
| Absoluter VIN-Bereich | 4,5 V … 50 V | Unterhalb $V_\text{OUT} + V_\text{Dropout}$ keine Regelung garantiert |
| Max. Dauerstrom (typisch) | 5,5 A | Bei $V_\text{IN} = 36\,\text{V}$, Raumtemperatur, ohne Kühlkörper |
| Strombereich (lastabhängig) | 3,3 A … 8 A | Je nach Eingangsspannung (siehe Abschnitt 5) |
| Schaltfrequenz | ca. 500 kHz | Unter hoher Last |
| Wirkungsgrad | 80 % … 95 % | Abhängig von $V_\text{IN}$, $V_\text{OUT}$ und Last |
| Ruhestrom (Quiescent Current) | 2 mA … 4 mA | Aktiviert, ohne Last |
| Ruhestrom im Schlafmodus | 10 µA … 20 µA pro Volt an VIN | EN-Pin auf Low |
| Ausgangstyp | Fest 6 V | Nicht einstellbar |

### 2.2 Mechanische Daten

| Parameter | Wert |
|---|---|
| Abmessungen (L × B × H) | 25,4 mm × 25,4 mm × 9,5 mm (1″ × 1″ × 0,375″) |
| Gewicht | 7,0 g (ohne Header) |
| Rastermaß | 2,54 mm (0,1″), Breadboard-kompatibel |
| Befestigung | 3 × Bohrungen für M2-Schrauben (Ø 2,18 mm / #2) |
| Mitgeliefertes Zubehör | 1×12 Stiftleiste (gerade, 2,54 mm Raster) |
| PCB-Kennung | `reg24d` / `0J12574` |

### 2.3 Schutzfunktionen

| Schutzfunktion | Details |
|---|---|
| Verpolungsschutz (Reverse Voltage Protection) | Bis −40 V am Eingang; oberhalb von 40 V in Sperrrichtung → Zerstörung |
| Unterspannungsschutz (Output Undervoltage) | PG-Signal geht auf Low, wenn $V_\text{OUT}$ mehr als 10 % unter Nennwert fällt |
| Überspannungsschutz (Output Overvoltage) | PG-Signal geht auf Low, wenn $V_\text{OUT}$ mehr als 20 % über Nennwert steigt |
| Überstromschutz (Overcurrent Protection) | Integriert |
| Kurzschlussschutz (Short-Circuit Protection) | Integriert |
| Thermische Abschaltung (Thermal Shutdown) | Automatisch bei Übertemperatur |
| Sanftanlauf (Soft-Start) | Begrenzt Einschaltstrom, rampt Ausgangsspannung graduell hoch |

> **Warnung:** Im Normalbetrieb unter hoher Last kann die Platine Temperaturen erreichen, die Verbrennungen verursachen. Angemessener Abstand oder Kühlmaßnahmen sind erforderlich.

---

## 3 Pinbelegung und Anschlüsse

### 3.1 Funktionale Beschreibung

Der Regler besitzt sechs logische Anschlüsse, von denen die Leistungspins (VIN, VRP, VOUT, GND) jeweils doppelt vorhanden sind:

```
Ansicht von oben (Pin-Reihen):

  Reihe A (Rand):  GND  GND  VOUT  VOUT  VRP  VIN  VIN  EN
  Reihe B (innen): GND  GND  VOUT  VOUT  VRP  VIN  VIN  PG

  Hinweis: PG liegt nur auf Reihe B, EN nur auf Reihe A.
  → Bei Breadboard-Montage: PG-Pin NICHT bestücken, um Kurzschluss
    zwischen EN und PG zu vermeiden!
```

### 3.2 Pinbeschreibung

| Pin | Bezeichnung | Funktion |
|---|---|---|
| **VIN** | Eingangsspannung | Versorgung des Reglers, 4,5 V … 50 V (effektiv $\geq V_\text{OUT} + V_\text{Dropout}$) |
| **VRP** | Eingang nach Verpolungsschutz | Zugang zur Eingangsspannung hinter dem Schutz-MOSFET; alternativ als Eingang nutzbar, um den Verpolungsschutz zu umgehen |
| **VOUT** | Ausgangsspannung | Geregelte 6 V |
| **GND** | Masse | Gemeinsame Bezugsmasse für Ein- und Ausgang |
| **EN** | Enable (Freigabe) | Aktiv-High mit internem 100 kΩ Pull-up nach VIN; $< 1{,}2\,\text{V}$ → Schlafmodus (Sleep), $> 1{,}35\,\text{V}$ → aktiv |
| **PG** | Power Good | Open-Drain-Ausgang; Low bei Über-/Unterspannung am Ausgang; externer Pull-up-Widerstand erforderlich |

### 3.3 Strombelastbarkeit der Anschlüsse

Jeder einzelne Stiftleisten-Pin ist für maximal 3 A spezifiziert. Durch die Doppelbelegung der Leistungspins ergibt sich ein kombiniertes Maximum von 6 A pro Anschluss. Für höhere Ströme müssen dicke Leitungen direkt an die Platine gelötet werden. Steckbretter (Breadboards) sind in der Regel nicht für Ströme über wenige Ampere ausgelegt.

---

## 4 Dropout-Spannung

Die Dropout-Spannung (Dropout Voltage) bezeichnet die minimale Differenz zwischen Eingangs- und Ausgangsspannung, die der Regler zur Aufrechterhaltung der Regelung benötigt. Der Zusammenhang ist näherungsweise linear mit dem Laststrom.

**Regel:** $V_\text{IN,min} = V_\text{OUT} + V_\text{Dropout}(I_\text{Last})$

**Beispielhafte Richtwerte für den D36V50F6 (6 V Ausgang):**

| Laststrom | Dropout-Spannung (ca.) | Minimale Eingangsspannung |
|---|---|---|
| 1 A | ≈ 0,3 V | ≈ 6,3 V |
| 3 A | ≈ 0,5 V | ≈ 6,5 V |
| 5 A | ≈ 0,8 V | ≈ 6,8 V |

> **Hinweis:** Die exakten Werte sind den Dropout-Voltage-Diagrammen auf der Pololu-Produktseite zu entnehmen. Die Angaben hier dienen der Orientierung.

**Konsequenz für batteriebetriebene Systeme:** Bei einem 3S-Li-Ion-Akkupack (Samsung INR18650-35E) mit einer Entladeschlussspannung von 9,0 V … 9,5 V ist die Dropout-Bedingung komfortabel erfüllt ($9{,}0\,\text{V} \gg 6{,}8\,\text{V}$).

---

## 5 Maximaler Dauerstrom

Der maximal entnehmbare Dauerstrom hängt primär von der Eingangsspannung ab und wird durch die thermische Verlustleistung begrenzt. Folgende Richtwerte gelten bei Raumtemperatur (ca. $25\,°\text{C}$), ruhender Luft und ohne zusätzliche Kühlung:

| Eingangsspannung | Max. Dauerstrom (ca.) |
|---|---|
| 7 V | ≈ 8 A |
| 12 V | ≈ 7 A |
| 24 V | ≈ 6 A |
| 36 V | ≈ 5,5 A |
| 50 V | ≈ 3,3 A |

**Beobachtung:** Der verfügbare Strom sinkt mit steigender Eingangsspannung, da die Schaltverluste proportional zur Spannung zunehmen.

**Konsequenz:** Bei hohen Eingangsspannungen (z. B. 48 V Industriebus) muss die Lastauslegung konservativer erfolgen. Aktive Kühlung oder ein Kühlkörper können den nutzbaren Strom erhöhen.

---

## 6 Wirkungsgrad und Verlustleistung

### 6.1 Wirkungsgrad

Der Wirkungsgrad $\eta$ definiert sich als:

$$
\eta = \frac{P_\text{out}}{P_\text{in}} = \frac{V_\text{OUT} \cdot I_\text{OUT}}{V_\text{IN} \cdot I_\text{IN}}
$$

Typische Werte liegen zwischen 80 % und 95 %, abhängig von Eingangsspannung und Laststrom. Der Wirkungsgrad ist bei mittleren Lasten (ca. 1 A … 4 A) am höchsten und fällt sowohl bei sehr kleinen als auch bei sehr hohen Lasten ab.

### 6.2 Energiesparmodus (Power-Save Mode)

Bei geringer Last reduziert der Regler die Schaltfrequenz automatisch, um die Effizienz zu steigern. Die Schaltfrequenz bleibt dabei stets oberhalb des hörbaren Bereichs (> 20 kHz, „Ultrasonic Operation"). Dies verhindert akustische Störgeräusche, die bei manchen PWM-Reglern unter Schwachlast auftreten.

### 6.3 Verlustleistungsabschätzung

Die im Regler dissipierte Verlustleistung ergibt sich aus:

$$
P_\text{Verlust} = P_\text{in} - P_\text{out} = P_\text{out} \cdot \left(\frac{1}{\eta} - 1\right)
$$

**Beispiel:** Bei $V_\text{IN} = 12\,\text{V}$, $V_\text{OUT} = 6\,\text{V}$, $I_\text{OUT} = 3\,\text{A}$ und $\eta = 92\,\%$:

$$
P_\text{out} = 6\,\text{V} \cdot 3\,\text{A} = 18\,\text{W}
$$
$$
P_\text{Verlust} = 18\,\text{W} \cdot \left(\frac{1}{0{,}92} - 1\right) \approx 1{,}57\,\text{W}
$$

Diese Verlustleistung wird als Wärme über die Platine abgegeben und bestimmt die thermische Belastung.

---

## 7 Enable-Pin (EN) – Unterspannungsabschaltung

### 7.1 Funktionsprinzip

Der EN-Pin verfügt über einen internen Pull-up-Widerstand von 100 kΩ nach VIN. Ohne externe Beschaltung ist der Regler daher standardmäßig aktiv. Durch Ziehen des EN-Pins unter 1,2 V wechselt der Regler in den Schlafmodus; oberhalb von 1,35 V wird er wieder aktiviert. Die Hysterese von ca. 150 mV verhindert Oszillationen an der Schaltschwelle.

### 7.2 Anwendung: Batterieunterspannungsschutz (Low-Voltage Cutoff)

Die enge Toleranz der EN-Schwelle ermöglicht die Realisierung einer präzisen Unterspannungsabschaltung mittels eines externen Spannungsteilers am Eingang. Diese Funktion schützt Lithium-Ionen-Akkus vor Tiefentladung.

**Schaltungsbeispiel – Spannungsteiler für Abschaltung bei $V_\text{IN} < 9{,}5\,\text{V}$:**

```
VIN ──┬── R1 ──┬── R2 ──┬── GND
      │        │        │
      │       EN        │
      │  (Schwelle      │
      │   1,2 V)        │
```

Die Bedingung lautet:

$$
V_\text{EN} = V_\text{IN} \cdot \frac{R_2}{R_1 + R_2} \stackrel{!}{=} 1{,}2\,\text{V}
$$

Bei gewünschter Abschaltschwelle $V_\text{cutoff} = 9{,}5\,\text{V}$:

$$
\frac{R_2}{R_1 + R_2} = \frac{1{,}2\,\text{V}}{9{,}5\,\text{V}} \approx 0{,}1263
$$

**Wahl:** $R_1 = 68\,\text{k}\Omega$, $R_2 = 10\,\text{k}\Omega$ ergibt ein Teilerverhältnis von $10 / 78 \approx 0{,}1282$, was einer Abschaltschwelle von ca. $9{,}36\,\text{V}$ entspricht.

> **Limitierung:** Der interne 100 kΩ Pull-up nach VIN beeinflusst den Spannungsteiler. Für präzise Schwellenwerte muss der Pull-up als Parallelwiderstand zu $R_1$ berücksichtigt werden: $R_1' = R_1 \| 100\,\text{k}\Omega$.

---

## 8 Power-Good-Ausgang (PG)

Der PG-Pin ist ein Open-Drain-Ausgang. Er signalisiert einen Fehlerzustand (Low-Pegel), wenn die Ausgangsspannung um mehr als 10 % unter oder um mehr als 20 % über den Nennwert abweicht. Im Normalbetrieb ist PG hochohmig.

**Beschaltung:** Ein externer Pull-up-Widerstand (typisch 10 kΩ … 100 kΩ) nach VOUT oder einer separaten Logikversorgung ist erforderlich. Der PG-Ausgang eignet sich zur Überwachung durch einen Mikrocontroller (GPIO-Eingang).

**Beispiel – Anbindung an ESP32-S3:**

```c
// GPIO-Pin als Eingang mit Pull-up konfigurieren
#define PIN_PG  GPIO_NUM_4

void power_good_init(void) {
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << PIN_PG),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,   // alternativ: externer Pull-up
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_NEGEDGE      // Interrupt bei Fehler
    };
    gpio_config(&io_conf);
}

bool is_power_good(void) {
    return gpio_get_level(PIN_PG) == 1;  // High = Spannung OK
}
```

---

## 9 Integrationsleitfaden

### 9.1 Empfohlene Verdrahtung

```
Batterie (+) ───── VIN  ┌──────────┐  VOUT ───── Last (+)
                        │ D36V50F6 │
Batterie (−) ───── GND  └──────────┘  GND  ───── Last (−)

Optional:
  - EN  ← Spannungsteiler für Unterspannungsabschaltung
  - PG  → µC GPIO (mit Pull-up) für Überwachung
  - VRP → Externer Verbraucher vor Regelung (ungeregelt, verpolungsgeschützt)
```

### 9.2 Layout-Empfehlungen

- Eingangskondensator (Keramik, ≥ 10 µF, spannungsfest) möglichst nah an VIN und GND platzieren, sofern die Zuleitung länger als 10 cm ist oder induktive Quellen (Kabelbaum) vorhanden sind.
- Massefläche durchgehend und niederohmig gestalten.
- Leiterbahnbreite für Leistungspfade entsprechend dem maximalen Strom dimensionieren (Richtwert: ca. 1 mm Breite pro 1 A bei 35 µm Kupfer, 1 oz/ft²).
- Thermische Anbindung: Die Unterseite der Platine kann als Kühlfläche dienen. Für Dauerlasten oberhalb von 4 A empfiehlt sich zusätzliche Kühlung.

### 9.3 Eingangskondensator-Dimensionierung

Der Regler enthält bereits Eingangs- und Ausgangskondensatoren auf der Platine. Bei langen Zuleitungen oder instabilen Quellen kann ein zusätzlicher Elektrolyt- oder Keramikkondensator am Eingang die Spannungsspitzen reduzieren. Typische Werte: 22 µF … 100 µF Keramik (X5R/X7R) oder 100 µF … 470 µF Elektrolyt, jeweils mit ausreichender Spannungsfestigkeit ($\geq 1{,}5 \times V_\text{IN,max}$).

---

## 10 Anwendungsbeispiel: Servospannung im AMR-System

### 10.1 Systemkontext

Ein autonomer mobiler Roboter (AMR) nutzt einen 3S-Li-Ion-Akkupack (3 × Samsung INR18650-35E, nominell 10,8 V, Bereich 9,0 V … 12,6 V) als Energiequelle. Mehrere Servomotoren benötigen eine stabile 6 V-Versorgung.

### 10.2 Auslegung

| Parameter | Wert |
|---|---|
| Eingangsspannung (Bereich) | 9,0 V … 12,6 V |
| Ausgangsspannung | 6,0 V |
| Erwarteter Spitzenstrom (4 Servos) | ca. 4 A |
| Erwarteter Durchschnittsstrom | ca. 1,5 A |

**Prüfung der Rahmenbedingungen:**

- Dropout bei 4 A: ca. 0,6 V → minimale Eingangsspannung ≈ 6,6 V ✓ (Akku liefert mindestens 9,0 V)
- Maximaler Dauerstrom bei 12 V Eingang: ca. 7 A ✓ (4 A Spitzenstrom liegt deutlich darunter)
- Verlustleistung bei 12 V / 4 A / 90 % Effizienz: ca. 2,7 W → Kühlung beobachten

### 10.3 Unterspannungsabschaltung

Die EN-Pin-Beschaltung aus Abschnitt 7.2 schützt den Akkupack vor Tiefentladung bei einer Schwelle von ca. 9,5 V. Alternativ übernimmt die übergeordnete Steuerung (ESP32-S3) die Abschaltung über ein MOSFET-Schaltglied, gesteuert durch die ADC-basierte Batteriespannungsmessung.

---

## 11 Verwandte Produkte der D36V50Fx-Familie

| Modell | Ausgangsspannung | Max. Dauerstrom (bei 36 V) | Pololu-Nr. |
|---|---|---|---|
| D36V50F3 | 3,3 V | 6,5 A | #4090 |
| D36V50F5 | 5,0 V | 5,5 A | #4091 |
| **D36V50F6** | **6,0 V** | **5,5 A** | **#4092** |
| D36V50F7 | 7,5 V | 5,0 A | #4093 |
| D36V50F9 | 9,0 V | 5,0 A | #4094 |
| D36V50F12 | 12,0 V | 4,5 A | #4095 |

Für geringeren Strombedarf (bis 4 A) bietet Pololu die pinkompatible D36V28Fx-Familie als kompaktere Alternative an.

---

## 12 Ressourcen und Dateien

| Ressource | Format | Quelle |
|---|---|---|
| Maßzeichnung | PDF (312 kB) | [pololu.com – Dimensions](https://www.pololu.com/file/0J1732/d36v50fx-step-down-voltage-regulator-dimensions.pdf) |
| 3D-Modell | STEP (5 MB) | [pololu.com – 3D Model](https://www.pololu.com/file/0J1733/d36v50fx-step-down-voltage-regulator.step) |
| Bohrbild | DXF (52 kB) | [pololu.com – Drill Guide](https://www.pololu.com/file/0J1734/reg24d-drill.dxf) |
| Produktseite | Web | [pololu.com/product/4092](https://www.pololu.com/product/4092) |

---

## 13 Zusammenfassung der Schlüsselparameter

```
┌─────────────────────────────────────────────────────┐
│              Pololu D36V50F6 – Kurzprofil            │
├──────────────────────┬──────────────────────────────┤
│ Topologie            │ Synchroner Buck-Konverter    │
│ V_OUT                │ 6,0 V (fest, ±4 %)          │
│ V_IN                 │ 6,5 V … 50 V                │
│ I_OUT (max., typ.)   │ 5,5 A @ 36 V Eingang        │
│ Wirkungsgrad         │ 80 % … 95 %                 │
│ Schaltfrequenz       │ ~500 kHz (Power-Save: >20 kHz)│
│ Schutzfunktionen     │ Verpolung, OVP, UVP, OCP,   │
│                      │ Kurzschluss, Thermisch       │
│ Abmessungen          │ 25,4 × 25,4 × 9,5 mm       │
│ Masse                │ 7,0 g                        │
└──────────────────────┴──────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2025-02-24 | Quelle: Pololu Corporation, pololu.com*
