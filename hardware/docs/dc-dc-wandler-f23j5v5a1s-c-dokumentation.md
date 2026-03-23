# DC/DC-Abwärtswandler F23J5V5A1S-C (B0DRRMM71M) – 12 V/24 V → 5 V @ 5 A

> **Technische Dokumentation** – Vergossener Schaltregler (Buck Converter) für mobile Robotik
> Modell: F23J5V5A1S-C | Handels-ID: B0DRRMM71M
> Eingang: 8 … 32 V DC | Ausgang: 5 V DC / 5 A (25 W) | Schutzart: IP68
> Ausgangsanschluss: USB Type-C
> Quellen: [Amazon UK Produktseite (B0DRRMM71M)](https://www.amazon.co.uk/Converter-Step-down-Charging-Adapter-Voltage/dp/B0DRRMM71M), [Amazon US (B0DYDFX72K, baugleich)](https://www.amazon.com/Converter-Step-Down-Charging-Waterproof-Electronics/dp/B0DYDFX72K), [Raspberry Pi 5 Power Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html), [Raspberry Pi Forums – DC-DC Power Supply](https://forums.raspberrypi.com/viewtopic.php?t=358576)

---

## 1 Übersicht

Der F23J5V5A1S-C ist ein vergossener (Silikon-versiegelter) DC/DC-Abwärtswandler (Buck Converter), der Eingangsspannungen von 8 … 32 V DC auf stabile 5 V DC bei maximal 5 A (25 W) konvertiert. Der Ausgang erfolgt über einen USB-Type-C-Stecker mit festem Kabel. Die Vergussmasse gewährleistet Schutzart IP68 (staub- und wasserdicht, dauerhaftes Untertauchen). Der Wandler eignet sich damit für den Einsatz auf mobilen Plattformen, in Fahrzeugen und in Außenanwendungen.

**Primärer Einsatzzweck im AMR-Kontext:** Versorgung des Raspberry Pi 5 über USB-C aus dem 3S-Lithium-Ionen-Akkupack (nominell 10,8 V, Bereich 9,0 … 12,6 V). Zusätzlich können weitere 5-V-Verbraucher (Kamera, Sensoren) über den Raspberry Pi versorgt werden, sofern die Gesamtstromentnahme 5 A nicht übersteigt.

---

## 2 Spezifikationen

### 2.1 Elektrische Kenndaten

| Parameter                           | Wert                             | Bemerkung                                  |
|-------------------------------------|----------------------------------|--------------------------------------------|
| **Modellbezeichnung**               | F23J5V5A1S-C                     | Herstellerinterne Bezeichnung              |
| **Handels-ID (Amazon)**             | B0DRRMM71M                       | –                                          |
| **Wandlertyp**                      | Synchroner Abwärtswandler (Buck) | Schaltregler, nicht linear                 |
| **Eingangsspannung (nominal)**      | 12 V / 24 V DC                   | Typische Bordsysteme                       |
| **Eingangsspannung (Bereich)**      | **8 … 32 V DC**                  | Min. 8 V für stabile Regelung              |
| **Ausgangsspannung**                | **5,0 V DC**                     | Fest, nicht einstellbar                    |
| **Ausgangsstrom (max.)**            | **5 A**                          | Kurzzeitig; Dauerlast abhängig von Kühlung |
| **Ausgangsleistung (max.)**         | **25 W**                         | $5\,\text{V} \times 5\,\text{A}$           |
| **Spannungsregelung (Line)**        | ±1 %                             | Über gesamten Eingangsspannungsbereich     |
| **Lastregelung (Load)**             | ±5 %                             | 0 … 100 % Last                             |
| **Restwelligkeit (Ripple & Noise)** | 30 mV~pp~                        | Peak-to-Peak, typisch                      |
| **Wirkungsgrad**                    | bis 96 %                         | Abhängig von V~in~ und I~out~              |
| **Leerlaufverluste**                | 0,15 W                           | Ohne Last                                  |
| **Einschaltstrombegrenzung**        | Ja                               | Soft-Start integriert                      |

### 2.2 Schutzfunktionen

| Schutz                          | Beschreibung                                |
|---------------------------------|---------------------------------------------|
| **Verpolungsschutz (Eingang)**  | Schutz gegen vertauschte Eingangspolarität  |
| **Überlastschutz**              | Strombegrenzung bei >5 A                    |
| **Überstromschutz**             | Abschaltung bei Kurzschluss am Ausgang      |
| **Kurzschlussschutz (Ausgang)** | Automatische Abschaltung, selbstrücksetzend |
| **Unterspannungsschutz**        | Abschaltung bei V~in~ < 8 V (UVLO)          |
| **Übertemperaturschutz**        | Thermische Abschaltung bei Überhitzung      |

### 2.3 Mechanische und Umgebungsdaten

| Parameter                    | Wert                                            |
|------------------------------|-------------------------------------------------|
| **Schutzart**                | **IP68** (staubdicht, dauerhaftes Untertauchen) |
| **Vergussmaterial**          | Silikon (vollvergossen)                         |
| **Abmessungen (Gehäuse)**    | 46 × 27 × 14 mm                                 |
| **Abmessungen (mit Kabeln)** | 63 × 27 × 14 mm                                 |
| **Gewicht**                  | 45 g                                            |
| **Betriebstemperatur**       | −25 … +80 °C                                    |
| **Eingangsanschluss**        | Offene Litzen, AWG 20 (rot = V+, schwarz = GND) |
| **Ausgangskabel**            | Fest montiert, USB Type-C Stecker               |
| **Kabellänge (Ausgang)**     | ca. 15 … 20 cm (je nach Charge)                 |
| **Zertifizierungen**         | CE, RoHS                                        |

### 2.4 USB-Funktionalität

| Merkmal                        | Beschreibung                                         |
|--------------------------------|------------------------------------------------------|
| **Steckertyp**                 | USB Type-C (Stecker, männlich)                       |
| **USB-PD-Unterstützung**       | **Nein** – kein Power-Delivery-Protokoll             |
| **USB-Daten**                  | **Nein** – nur Stromversorgung, keine Datenleitungen |
| **Ladeprotokoll-Erkennung**    | Ja – automatische Geräteidentifikation               |
| **Maximaler Strom über USB-C** | 5 A (proprietär, nicht PD-konform)                   |

> **Kritischer Hinweis:** Dieser Wandler implementiert **kein USB Power Delivery (PD)**. Der Raspberry Pi 5 erkennt das Netzteil daher als Non-PD-Quelle und beschränkt den USB-Portstrom auf 600 mA. Abschnitt 5 beschreibt die notwendige Software-Konfiguration, um diese Einschränkung zu umgehen.

---

## 3 Funktionsprinzip

### 3.1 Schaltregler-Topologie (Buck Converter)

Der Abwärtswandler (Step-Down Converter) arbeitet nach dem Prinzip der getakteten Energieumwandlung. Ein Leistungs-MOSFET schaltet die Eingangsspannung periodisch auf eine LC-Filterstruktur, deren Tiefpasscharakteristik die geglättete Ausgangsspannung erzeugt.

```
    V_in (8...32V)                                     V_out (5V)
        │                                                  │
        │    ┌──────┐     L                                │
        ├────┤ Q_HS ├────┤├───────────────┬────────────────┤
        │    └──┬───┘                     │                │
        │       │                       ┌─┴─┐              │
        │    ┌──┴───┐                   │   │ C_out     ┌──┴──┐
        │    │ Q_LS │                   │   │           │ Last│
        │    └──┬───┘                   └─┬─┘           └──┬──┘
        │       │                         │                │
       GND─────┴─────────────────────────┴────────────────GND

    Q_HS = High-Side MOSFET (Schalter)
    Q_LS = Low-Side MOSFET (synchrone Gleichrichtung)
    L    = Speicherdrossel
    C_out= Ausgangskondensator
```

Die Ausgangsspannung ergibt sich aus dem Tastverhältnis $D$ (Duty Cycle):

$$
V_\text{out} = D \times V_\text{in} \quad \Rightarrow \quad D = \frac{V_\text{out}}{V_\text{in}} = \frac{5\,\text{V}}{V_\text{in}}
$$

| Eingangsspannung V~in~ | Tastverhältnis $D$ | Wirkungsgrad (typisch) |
|------------------------|--------------------|------------------------|
| 8 V (Minimum)          | 62,5 %             | ~90 %                  |
| 12 V (3S-Akku nominal) | 41,7 %             | ~94 %                  |
| 12,6 V (3S-Akku voll)  | 39,7 %             | ~95 %                  |
| 24 V (Kfz-Bordnetz)    | 20,8 %             | ~96 %                  |
| 32 V (Maximum)         | 15,6 %             | ~96 %                  |

### 3.2 Wirkungsgrad und Verlustleistung

Die Verlustleistung im Wandler berechnet sich aus:

$$
P_\text{Verlust} = P_\text{out} \times \left(\frac{1}{\eta} - 1\right)
$$

Bei typischem Betrieb mit 3S-Akku (12 V) und 3 A Last am Raspberry Pi 5:

$$
P_\text{Verlust} = 15\,\text{W} \times \left(\frac{1}{0{,}94} - 1\right) \approx 0{,}96\,\text{W}
$$

Diese Verlustleistung wird über das Silikongehäuse an die Umgebung abgegeben. Die natürliche Konvektion reicht bei Umgebungstemperaturen bis +40 °C und Lastströmen bis 3 A aus. Bei Dauerbetrieb mit 5 A und hoher Umgebungstemperatur kann die interne Temperatur den Abschaltpunkt erreichen – Abschnitt 7 behandelt die thermische Auslegung.

---

## 4 Integration im AMR-System

### 4.1 Systemkontext

```
3S-Akkupack (Samsung INR18650-35E)
    │
    │  9,0 V (entladen) ... 12,6 V (voll)
    │
    ├──────── BMS ──────── Hauptschalter
    │                          │
    │                     Leistungspfad
    │                          │
    │              ┌───────────┼───────────────┐
    │              │           │               │
    │        ┌─────┴─────┐    │         ┌─────┴─────┐
    │        │ F23J5V5A1S│    │         │ Motor-    │
    │        │ DC/DC     │    │         │ treiber   │
    │        │ 5V / 5A   │    │         │ (ESP32-S3)│
    │        └─────┬─────┘    │         └───────────┘
    │              │ USB-C    │
    │              │          │
    │        ┌─────┴─────┐    │
    │        │ Raspberry  │    │
    │        │ Pi 5       │    │
    │        │            │    │
    │        │ ├─ Kamera  │    │
    │        │ ├─ NVMe    │    │
    │        │ └─ Sensoren│    │
    │        └────────────┘    │
    │                          │
   GND ───────────────────────GND
```

### 4.2 Eingangsspannungsbereich vs. 3S-Akku

Das 3S-Akkupack mit Samsung INR18650-35E durchläuft folgenden Spannungsbereich:

| Akkuzustand                | Zellenspannung | Packspannung (3S) | Im Bereich?   |
|----------------------------|----------------|-------------------|---------------|
| Voll geladen               | 4,20 V         | 12,60 V           | ✓ (8 … 32 V)  |
| Nominal (50 % SoC)         | 3,70 V         | 11,10 V           | ✓             |
| Entladeschwelle (20 % SoC) | 3,40 V         | 10,20 V           | ✓             |
| BMS-Abschaltung            | 3,00 V         | 9,00 V            | ✓             |
| Tiefentladung (Notfall)    | 2,65 V         | 7,95 V            | **✗** (< 8 V) |

Die BMS-Unterspannungsabschaltung bei 9,0 V (3,0 V/Zelle) liegt sicher oberhalb der minimalen Eingangsspannung von 8 V. Damit ist der Wandler über den gesamten nutzbaren Entladebereich des 3S-Packs betriebsfähig. Die UVLO-Schwelle (Under-Voltage Lock-Out) des Wandlers bei 8 V bietet eine zusätzliche Schutzebene: Selbst bei BMS-Fehlfunktion schaltet der Wandler ab, bevor die Zellen tiefentladen werden.

### 4.3 Leistungsbilanz (Raspberry Pi 5 auf AMR)

| Verbraucher               | Typischer Strom @ 5 V | Leistung    |
|---------------------------|-----------------------|-------------|
| Raspberry Pi 5 (Idle)     | 0,8 … 1,0 A           | 4 … 5 W     |
| Raspberry Pi 5 (Volllast) | 2,0 … 2,4 A           | 10 … 12 W   |
| IMX296 GS-Kamera (CSI)    | 0,2 … 0,3 A           | 1 … 1,5 W   |
| NVMe SSD (via PCIe/USB)   | 0,3 … 0,8 A           | 1,5 … 4 W   |
| USB-Peripherie (Sensoren) | 0,1 … 0,3 A           | 0,5 … 1,5 W |
| **Summe (typisch)**       | **~2,5 A**            | **~12,5 W** |
| **Summe (Worst Case)**    | **~3,8 A**            | **~19 W**   |

Die maximale Ausgangsleistung von 25 W (5 A) bietet eine Reserve von ca. 30 % gegenüber dem Worst-Case-Szenario. Dauerhafter Betrieb bei >4 A erfordert Aufmerksamkeit bezüglich der thermischen Verhältnisse (Abschnitt 7).

---

## 5 Raspberry Pi 5 – Konfiguration für Non-PD-Versorgung

### 5.1 Problem: Fehlende USB-PD-Aushandlung

Der Raspberry Pi 5 prüft beim Booten über USB Power Delivery, ob die angeschlossene Stromquelle 5 V bei 5 A liefern kann. Ohne PD-Aushandlung nimmt das PMIC (Power Management IC) des Pi an, dass maximal 3 A verfügbar sind, und schränkt den USB-Portstrom auf 600 mA ein. Die Meldung lautet:

> *"This power supply is not capable of supplying 5A. Power to peripherals will be restricted."*

Da der F23J5V5A1S-C kein PD implementiert, tritt diese Meldung grundsätzlich auf – obwohl der Wandler tatsächlich 5 A liefern kann.

### 5.2 Lösung 1: config.txt (empfohlen)

In der Datei `/boot/firmware/config.txt` wird die PD-Prüfung übersteuert:

```bash
sudo nano /boot/firmware/config.txt
```

Eintrag unter `[all]`:

```ini
[all]
# Non-PD-Netzteil: USB-Strombegrenzung aufheben
usb_max_current_enable=1
```

Nach dem Speichern ist ein Neustart erforderlich. Der Pi erlaubt danach bis zu 1,6 A Gesamtstrom über die USB-Ports, unabhängig von der PD-Aushandlung.

### 5.3 Lösung 2: EEPROM-Konfiguration (für SSD-Boot)

Beim Booten von einem USB-Datenträger (NVMe, SSD) wird `config.txt` erst gelesen, nachdem der Bootloader den Datenträger anspricht. Der Bootloader benötigt daher die Information bereits in der EEPROM-Konfiguration:

```bash
sudo rpi-eeprom-config --edit
```

Folgende Zeilen hinzufügen:

```ini
PSU_MAX_CURRENT=5000

[config.txt]
[all]
usb_max_current_enable=1
```

Die erste Zeile (`PSU_MAX_CURRENT=5000`) teilt dem Bootloader mit, dass die Stromquelle 5000 mA (5 A) liefern kann. Die `[config.txt]`-Sektion wird vom Bootloader wie ein Anhang an die gelesene `config.txt` behandelt.

### 5.4 Verifikation

```bash
# Bootloader-Log prüfen (nach Neustart)
vcgencmd bootloader_config | grep PSU

# Stromversorgung prüfen
vcgencmd pmic_read_adc
# Relevante Zeile: EXT5V_V → sollte ≥4,8 V zeigen

# USB-Portstrom prüfen (sollte "1600 mA" zeigen, nicht "600 mA")
cat /sys/devices/platform/axi/1000120000.usb/xhci-hcd.1/usb3/3-1/bMaxPower
```

> **Warnung:** `usb_max_current_enable=1` setzt voraus, dass die Stromquelle tatsächlich 5 A liefern kann. Bei unterdimensionierter Versorgung führt dies zu Spannungseinbrüchen, Datenverlust auf USB-Datenträgern und instabilem Betrieb. Der F23J5V5A1S-C mit 5 A Nennstrom erfüllt diese Anforderung.

---

## 6 Verdrahtung

### 6.1 Anschlussschema (AMR)

```
3S-Akkupack  ──────┐
(9,0 ... 12,6 V)   │
                    │  Rot (+) ─────── Rot (+) Eingang
                    │                  ┌─────────────────┐
                    │                  │ F23J5V5A1S-C    │
                    │                  │                 │     USB-C
                    │                  │  DC/DC 5V/5A   ├────→ Raspberry Pi 5
                    │                  │                 │
                    │  Schwarz (−) ─── │ GND             │
                    │                  └─────────────────┘
                   GND
                    │
                    └─── gemeinsame Masse zum Gesamtsystem
```

### 6.2 Eingangsverdrahtung

| Litze | Farbe   | Funktion                       | Querschnitt       |
|-------|---------|--------------------------------|-------------------|
| V+    | Rot     | Positive Versorgung (8 … 32 V) | AWG 20 (~0,5 mm²) |
| GND   | Schwarz | Masse                          | AWG 20 (~0,5 mm²) |

**Anschlusshinweise:**

1. Die offenen Litzenenden müssen mit Aderendhülsen oder Lötzinn versehen werden, um Einzeldrähte vor dem Lösen zu schützen.
2. Zwischen Akkupack und Wandler-Eingang gehört eine Sicherung (6 A, Schmelzsicherung oder rücksetzbare PTC). Obwohl der Wandler Eingangsschutz besitzt, bietet eine externe Sicherung zusätzlichen Schutz bei Kabelfehlern.
3. Der Kabelquerschnitt AWG 20 ist für 5 A Ausgangsstrom bei 12 V Eingang ausreichend (Eingangsstrom bei 12 V: $I_\text{in} = 25\,\text{W} / (12\,\text{V} \times 0{,}94) \approx 2{,}2\,\text{A}$). Bei Kabellängen >30 cm empfiehlt sich AWG 18 (~0,75 mm²).

### 6.3 USB-C-Ausgang

Das Ausgangskabel mit USB-C-Stecker ist fest vergossen und nicht austauschbar. Der Stecker wird direkt in den USB-C-Port des Raspberry Pi 5 eingesteckt. Da keine Datenleitungen vorhanden sind und kein PD-Controller verbaut ist, dient der USB-C-Stecker ausschließlich der Stromzuführung über die VBUS- und GND-Pins.

> **Hinweis:** Der feste USB-C-Stecker kann bei mechanischer Belastung (Vibrationen auf dem AMR) das Risiko eines Kontaktverlusts darstellen. Eine Zugentlastung am Kabel oder ein USB-C-Winkeladapter reduziert die mechanische Belastung der Buchse am Raspberry Pi.

---

## 7 Thermische Auslegung

### 7.1 Verlustleistung in Abhängigkeit von Last und Eingangsspannung

$$
P_\text{Verlust} = P_\text{out} \times \left(\frac{1}{\eta} - 1\right) = V_\text{out} \times I_\text{out} \times \left(\frac{1}{\eta} - 1\right)
$$

| Szenario                         | V~in~  | I~out~ | P~out~ | η (geschätzt) | P~Verlust~ |
|----------------------------------|--------|--------|--------|---------------|------------|
| Idle (Pi 5 Leerlauf)             | 10,8 V | 1,0 A  | 5 W    | 92 %          | 0,43 W     |
| Typischer AMR-Betrieb            | 10,8 V | 2,5 A  | 12,5 W | 94 %          | 0,80 W     |
| Hohe Last (Pi 5 + NVMe + Kamera) | 10,8 V | 3,8 A  | 19 W   | 93 %          | 1,43 W     |
| Maximallast                      | 10,8 V | 5,0 A  | 25 W   | 92 %          | 2,17 W     |
| Maximallast bei 24 V             | 24 V   | 5,0 A  | 25 W   | 96 %          | 1,04 W     |

### 7.2 Thermische Grenzen

Das vergossene Silikongehäuse leitet Wärme über seine Oberfläche (ca. 46 × 27 mm ≈ 12,4 cm²) ab. Der thermische Widerstand liegt schätzungsweise bei $R_\text{th,JA} \approx 30 … 50\,\text{K/W}$ (natürliche Konvektion, kein Kühlkörper).

| Verlustleistung | Temperaturerhöhung (geschätzt) | Grenze bei T~amb~ = 40 °C          |
|-----------------|--------------------------------|------------------------------------|
| 0,5 W           | 15 … 25 K                      | unkritisch                         |
| 1,0 W           | 30 … 50 K                      | grenzwertig bei hoher T~amb~       |
| 2,0 W           | 60 … 100 K                     | **thermische Abschaltung möglich** |

**Empfehlung für AMR:** Dauerlast auf 3 … 4 A begrenzen. Bei voller Auslastung (5 A) den Wandler auf einer Metallfläche (Aluminiumchassis) montieren, um den thermischen Widerstand zu senken. Der Übertemperaturschutz verhindert Schäden, führt aber zum unkontrollierten Abschalten des Raspberry Pi.

### 7.3 Montage

Das IP68-Gehäuse hat keine Befestigungslöcher. Fixierung durch:

- **Kabelbinder** (einfach, vibrationsfest mit Unterlage)
- **Klettverschluss** (flexibel, gut für Prototypen)
- **Wärmeleitkleber** auf Metallfläche (optimal für thermische Anbindung)
- **3D-gedruckte Halterung** (maßgenau, vibrationsdämpfend mit TPU-Einlage)

---

## 8 Signalintegrität und EMV

### 8.1 Restwelligkeit (Ripple)

Die spezifizierte Restwelligkeit von 30 mV~pp~ bezieht sich auf den Ausgang unter Nennlast. Für den Raspberry Pi 5 ist dieser Wert unkritisch – das interne PMIC (RP1 und BCM2712 Spannungsregler) toleriert Eingangs-Ripple bis ca. 100 mV~pp~.

### 8.2 Schaltfrequenz und EMV

Schaltregler erzeugen Emissionen bei ihrer Schaltfrequenz (typisch 300 kHz … 1 MHz) und deren Harmonischen. Für den AMR-Betrieb relevante Maßnahmen:

- **Eingangskondensator:** Falls der Wandler über längere Kabel (>30 cm) an den Akku angeschlossen wird, einen zusätzlichen 100 µF / 25 V Elektrolytkondensator parallel zu den Eingangslitzen platzieren.
- **Ferritkern:** Ein Klappferrit auf dem USB-C-Kabel (nahe am Wandler) kann hochfrequente Störungen auf der 5-V-Leitung reduzieren.
- **Kabelführung:** Eingangskabel nicht parallel zu I²C-, SPI- oder empfindlichen Analogsignalen verlegen.

---

## 9 Alternative Versorgungspfade (Vergleich)

| Lösung                            | V~in~      | V~out~ / I~max~ | PD-Konform? | IP-Schutz | USB-Boot ohne Config? | Preis (ca.) |
|-----------------------------------|------------|-----------------|-------------|-----------|-----------------------|-------------|
| **F23J5V5A1S-C (dieses Modul)**   | 8 … 32 V   | 5 V / 5 A       | Nein        | IP68      | Nein (config.txt)     | 8 … 12 €    |
| Offizielles RPi 27W PSU           | 230 V AC   | 5,1 V / 5 A     | Ja          | –         | Ja                    | 15 €        |
| Pololu 5V 5A Step-Down (D36V50F5) | 6 … 50 V   | 5 V / 5 A       | –           | –         | – (kein USB-C)        | 20 €        |
| GPIO-Pin-Versorgung (5V/GND)      | 5 V direkt | 5 V / begrenzt  | –           | –         | Nein                  | 0 €         |
| PoE+ HAT                          | 48 V PoE   | 5 V / 5 A       | Ja (intern) | –         | Ja (mit HAT)          | 25 … 40 €   |

> **GPIO-Pin-Versorgung:** Einspeisung über die 5V-Pins (Pin 2/4) des 40-Pin-Headers umgeht den Überspannungsschutz des Raspberry Pi 5. Bei Spannungsspitzen >5,5 V am Eingang besteht die Gefahr irreversibler Schäden. Für Akku-betriebene Systeme mit definiertem DC/DC-Wandler ist die USB-C-Einspeisung mit `usb_max_current_enable=1` die sicherere Variante.

---

## 10 Inbetriebnahme – Schritt für Schritt

### 10.1 Vor der ersten Inbetriebnahme

1. **Spannung prüfen:** Eingangsspannung mit Multimeter am Akku/Netzteil messen. Der Wert muss im Bereich 8 … 32 V liegen.
2. **Polarität prüfen:** Rotes Kabel = V+, schwarzes Kabel = GND. Trotz Verpolungsschutz: bewusste Verpolung vermeiden.
3. **Ausgangsspannung messen:** Wandler ohne Last einschalten, USB-C-Stecker in USB-C-Breakout-Board oder Messadapter stecken. Erwarteter Wert: 5,0 V ±0,05 V.
4. **Wandler nicht belasten** solange die Raspberry-Pi-Konfiguration nicht angepasst wurde (Abschnitt 5).

### 10.2 Raspberry Pi 5 konfigurieren

```bash
# 1. Pi mit offiziellem Netzteil oder anderem PD-Netzteil starten

# 2. config.txt bearbeiten
sudo nano /boot/firmware/config.txt

# 3. Folgenden Eintrag unter [all] hinzufügen:
#    usb_max_current_enable=1

# 4. Für SSD/NVMe-Boot zusätzlich EEPROM konfigurieren:
sudo rpi-eeprom-config --edit
# PSU_MAX_CURRENT=5000 eintragen

# 5. Herunterfahren
sudo shutdown -h now

# 6. Offizielles Netzteil trennen, F23J5V5A1S-C anschließen

# 7. Pi startet ohne PD-Warnmeldung
```

### 10.3 Funktionsprüfung nach Umstellung

```bash
# Versorgungsspannung am PMIC prüfen
vcgencmd pmic_read_adc
# EXT5V_V ≥ 4,8 V → OK
# EXT5V_V < 4,6 V → Kabel zu dünn oder Wandler überlastet

# USB-Portstrom prüfen
dmesg | grep -i "power"
# Sollte keine "under-voltage" Meldungen zeigen

# Langzeittest unter Last
stress-ng --cpu 4 --timeout 300 &
# Während des Tests: vcgencmd pmic_read_adc periodisch prüfen
```

---

## 12 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   DC/DC-Wandler F23J5V5A1S-C (B0DRRMM71M) – Kurzprofil                │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   EINGANG                    │                                           │
│   Spannungsbereich           │ 8 … 32 V DC                              │
│   Nominell                   │ 12 V / 24 V DC                           │
│   3S-LiIon-Kompatibilität   │ ✓ (9,0 … 12,6 V im nutzbaren Bereich)   │
│   Strom bei 12 V, 5 A Last  │ ca. 2,2 A (bei η = 94 %)                │
│   Verpolungsschutz           │ Ja                                        │
│   Anschluss                  │ Offene Litzen, AWG 20                    │
│                              │                                           │
│   AUSGANG                    │                                           │
│   Spannung                   │ 5,0 V DC (±1 %)                          │
│   Maximalstrom               │ 5 A (25 W)                               │
│   Ripple                     │ 30 mV_pp                                 │
│   Wirkungsgrad               │ bis 96 %                                 │
│   Anschluss                  │ USB Type-C (fest, nur Strom)             │
│   USB-PD                     │ Nein                                      │
│                              │                                           │
│   SCHUTZ                     │                                           │
│   Funktionen                 │ Verpolung, Überlast, Kurzschluss,       │
│                              │ Unterspannung (UVLO), Übertemperatur     │
│   Schutzart                  │ IP68 (vollvergossen, Silikon)            │
│                              │                                           │
│   MECHANIK                   │                                           │
│   Abmessungen                │ 46 (63) × 27 × 14 mm                    │
│   Gewicht                    │ 45 g                                      │
│   Betriebstemperatur         │ −25 … +80 °C                             │
│   Zertifizierungen           │ CE, RoHS                                 │
│                              │                                           │
│   AMR-INTEGRATION            │                                           │
│   Raspberry Pi 5 Config      │ usb_max_current_enable=1                 │
│   EEPROM (SSD-Boot)          │ PSU_MAX_CURRENT=5000                     │
│   Typische Last (Pi 5 + Cam) │ ~2,5 A (~12,5 W)                        │
│   Leistungsreserve           │ ~50 % bei typischer Last                 │
│   Thermisch unkritisch bis   │ ~3,5 A Dauerlast bei T_amb ≤ 40 °C      │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 13 Ressourcen

| Typ                                  | Link                                                                                                                                |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| Produktseite (Amazon UK, B0DRRMM71M) | [amazon.co.uk/…/B0DRRMM71M](https://www.amazon.co.uk/Converter-Step-down-Charging-Adapter-Voltage/dp/B0DRRMM71M)                    |
| Baugleiche Variante (Amazon US)      | [amazon.com/…/B0DYDFX72K](https://www.amazon.com/Converter-Step-Down-Charging-Waterproof-Electronics/dp/B0DYDFX72K)                 |
| Raspberry Pi 5 Power Documentation   | [raspberrypi.com/documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)                              |
| RPi 5 Stromversorgung (Guide)        | [bret.dk/how-to-power-the-raspberry-pi-5](https://bret.dk/how-to-power-the-raspberry-pi-5-a-complete-guide/)                        |
| RPi Forum – DC-DC für Pi 5           | [forums.raspberrypi.com/…/t=358576](https://forums.raspberrypi.com/viewtopic.php?t=358576)                                          |
| RPi Forum – Non-PD Power Supply      | [forums.raspberrypi.com/…/t=361206](https://forums.raspberrypi.com/viewtopic.php?t=361206)                                          |
| RPi EEPROM Config                    | [github.com/raspberrypi/rpi-eeprom](https://github.com/raspberrypi/rpi-eeprom)                                                      |
| DIY Robot Lawn Mower – DC Source     | [diy-robot-lawn-mower.com](https://www.diy-robot-lawn-mower.com/threads/the-way-of-powering-the-raspberry-pi-5-from-dc-source.218/) |
| The Pi Hut – Pi 5 PSU Guide          | [support.thepihut.com](https://support.thepihut.com/hc/en-us/articles/13852538984221)                                               |

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: Amazon UK/US Produktseiten (F23J5V5A1S-C), Raspberry Pi 5 Dokumentation, Raspberry Pi Forums (Power Supply Threads), bret.dk Pi 5 Power Guide, element14 Pi 5 FAQ, The Pi Hut PSU Guide*
