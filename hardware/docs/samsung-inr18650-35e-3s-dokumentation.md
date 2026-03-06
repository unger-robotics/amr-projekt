# Samsung INR18650-35E – Li-Ionen-Zelle und 3S-Akkupack

> **Technische Dokumentation** – Samsung SDI Spec. No. INR18650-35E, Version 1.1  
> Zellchemie: LiNiCoAlO₂ (NCA) | Bauform: 18650 (zylindrisch)  
> Quelle: [Samsung SDI Datenblatt](https://www.orbtronic.com/content/samsung-35e-datasheet-inr18650-35e.pdf)

---

## 1 Übersicht

Die Samsung INR18650-35E ist eine zylindrische Lithium-Ionen-Zelle im weit verbreiteten 18650-Format (18 mm Durchmesser, 65 mm Höhe). Die Zelle basiert auf einer NCA-Kathode (Nickel-Cobalt-Aluminium-Oxid) und gehört mit einer Minimalkapazität von 3.350 mAh zu den energiedichtesten 18650-Zellen auf dem Markt. Der maximale Dauerstrom von 8 A positioniert die 35E als Hochkapazitätszelle mit moderater Strombelastbarkeit – die Zelle eignet sich daher primär für Anwendungen, in denen Laufzeit gegenüber Spitzenleistung priorisiert wird.

**Typische Anwendungen:**

- Akkupacks für mobile Roboter (AMR), E-Bikes und Elektrowerkzeuge
- Powerbanks und portable Energiespeicher
- Beleuchtungssysteme und Taschenlampen
- USV-Systeme (Unterbrechungsfreie Stromversorgung, USV/UPS) und stationäre Speicher

---

## 2 Zellenspezifikationen (Einzelzelle)

### 2.1 Elektrische Kenndaten

| Parameter | Wert | Bemerkung |
|---|---|---|
| Nennspannung | 3,60 V | Bei 0,2C Entladung |
| Ladeschlussspannung | 4,20 V | CC-CV-Verfahren |
| Entladeschlussspannung | 2,65 V | Laut Datenblatt; BMS-Empfehlung: 2,50 V |
| Minimalkapazität | 3.350 mAh | Bei 0,2C (680 mA) Entladung, $23\,°\text{C}$ |
| Typische Kapazität | 3.450 mAh … 3.500 mAh | Herstellerangabe (technischer Bericht) |
| Nennkapazität bei 1C | ≥ 3.250 mAh | 97 % der Standardkapazität |
| Nennenergie (Einzelzelle) | 12,06 Wh … 12,60 Wh | $3{,}60\,\text{V} \times 3{,}35\,\text{Ah}$ bis $3{,}60\,\text{V} \times 3{,}50\,\text{Ah}$ |
| 1C-Rate | 3.400 mA | Referenzwert für C-Raten-Angaben |

### 2.2 Lade- und Entladeparameter

| Parameter | Wert | Bemerkung |
|---|---|---|
| Ladeverfahren | CC-CV | Konstantstrom gefolgt von Konstantspannung |
| Standard-Ladestrom | 1.700 mA (0,5C) | Für Zyklenlebensdauer: 1.020 mA (0,3C) |
| Max. Ladestrom | 2.000 mA (≈ 0,59C) | Nicht für Zyklenlebensdauer empfohlen |
| Abschaltkriterium (Cut-off) | 68 mA (0,02C) bei 4,20 V | Ladung gilt als abgeschlossen |
| Standard-Ladezeit | ca. 4 Stunden | Bei 0,5C / 4,20 V / 0,02C Cut-off |
| Max. Dauerentladestrom | 8.000 mA (≈ 2,35C) | Kontinuierlich |
| Max. Impulsentladestrom | 13.000 mA (≈ 3,82C) | Nicht für Dauerentladung |
| Entladeschlussspannung | 2,65 V | Weitere Entladung führt zu Kapazitätsverlust |

### 2.3 Entladeratenverhalten

Die Kapazität sinkt mit steigendem Entladestrom. Bezugsgröße: Standardkapazität 3.350 mAh = 100 %.

| Entladestrom | C-Rate | Relative Kapazität |
|---|---|---|
| 680 mA | 0,2C | 100 % |
| 3.400 mA | 1,0C | 97 % |
| 6.800 mA | 2,0C | 95 % |
| 8.000 mA | 2,35C | 92 % |

**Beobachtung:** Selbst beim maximalen Dauerstrom von 8 A bleiben 92 % der Nennkapazität nutzbar. Dies bestätigt die gute Eignung der 35E für Lasten im Bereich von 1 A bis 5 A.

### 2.4 Temperaturverhalten

#### Entladekapazität in Abhängigkeit von der Temperatur

Ladung bei $23\,°\text{C}$ (Standard), Entladung bei 1C (3.400 mA), Bezugsgröße: 3.350 mAh = 100 %.

| Entladetemperatur | Relative Kapazität |
|---|---|
| −10 °C | 40 % |
| +23 °C | 97 % |
| +40 °C | 97 % |

#### Ladekapazität in Abhängigkeit von der Temperatur

Entladung bei $23\,°\text{C}$ (0,2C), Ladung bei verschiedenen Temperaturen, Bezugsgröße: 3.350 mAh = 100 %.

| Ladetemperatur | Relative Kapazität |
|---|---|
| 0 °C | 60 % |
| 23 °C | 100 % |
| 45 °C | 100 % |

**Konsequenz:** Bei Umgebungstemperaturen unter $0\,°\text{C}$ darf nicht geladen werden (Lithium-Plating-Gefahr). Die Entladekapazität reduziert sich bei $-10\,°\text{C}$ auf ca. 40 % – ein kritischer Faktor für Außenanwendungen im Winter.

### 2.5 Betriebstemperaturbereiche

| Betriebsart | Temperaturbereich (Zelloberfläche) |
|---|---|
| Ladung | 0 °C … +45 °C |
| Entladung | −10 °C … +60 °C |
| Lagerung (1 Jahr) | −20 °C … +25 °C |
| Lagerung (3 Monate) | −20 °C … +45 °C |
| Lagerung (1 Monat) | −20 °C … +60 °C |

Lagerbedingung: Ab-Werk-Zustand bei ca. 30 % SoC (State of Charge). Kapazitätsrückgewinnung nach Langzeitlagerung: ≥ 80 %.

### 2.6 Mechanische Daten

| Parameter | Wert |
|---|---|
| Durchmesser | max. 18,55 mm |
| Höhe | max. 65,25 mm |
| Gewicht | max. 50 g |
| Pluspol | Flachkopf (Flat Top) |
| Zellchemie (Kathode) | LiNiCoAlO₂ (NCA) |
| Herstellungsland | Korea |

### 2.7 Innenwiderstand und Zyklenlebensdauer

| Parameter | Wert | Bedingung |
|---|---|---|
| Innenimpedanz (initial) | ≤ 35 mΩ | AC 1 kHz, nach Standardladung |
| Zyklenlebensdauer | ≥ 500 Zyklen | Bei ≥ 60 % Restkapazität (2.010 mAh) |
| Zyklusbedingung | Ladung 0,3C (1.020 mA), 0,1C Cut-off; Entladung 1C (3.400 mA), 2,65 V Cut-off | $23\,°\text{C}$ |
| Lagerkapazität (20 Tage, 60 °C) | ≥ 95 % (3.183 mAh) | Nach Standard-Vollladung |

**Hinweis:** Die Zyklenangabe von 500 Zyklen bei 60 % Restkapazität ist konservativ. In der Praxis erreichen viele 35E-Zellen deutlich mehr Zyklen bei moderater Nutzung (0,5C Ladung, 0,5C Entladung). Samsung gibt für E-Bike-/ESS-Anwendungen eine reduzierte Ladeschlussspannung von 4,10 V an, was die Zyklenlebensdauer signifikant verlängert.

### 2.8 Sicherheitsmerkmale (Zellebene)

| Test | Bedingung | Kriterium |
|---|---|---|
| Überladung | 12 V / 3C (10,2 A), 7 h (UL 1642) | Kein Feuer, keine Explosion |
| Externer Kurzschluss | ≤ 80 ± 20 mΩ, 3 h | Kein Feuer, keine Explosion |
| Verpolung | 3.400 mA, 1,5 h | Kein Feuer, keine Explosion |
| Erhitzung | 5 °C/min bis 130 °C, 10 min Halten | Kein Feuer, keine Explosion |
| Falltest | 3× aus 1 m auf Beton (IEC 62133) | Kein Feuer, keine Explosion |
| Vibration | UN 38.3: 7–200 Hz, 8g, 3 h | Kein Leck, OCV-Abfall < 10 mV |

> **Warnung:** Die Zelle besitzt keinen integrierten Schutz (ungeschützt / unprotected). Ein Battery Management System (BMS) mit PTC-Element und Schutzschaltung (PCM, Protection Circuit Module) ist für den sicheren Betrieb im Akkupack zwingend erforderlich.

---

## 3 Spannungskennlinie und Ladezustandsschätzung

### 3.1 Spannungsverlauf über SoC

Die Leerlaufspannung (OCV, Open Circuit Voltage) einer NCA-Zelle zeigt einen charakteristischen nichtlinearen Verlauf über dem Ladezustand. Die folgende Tabelle gibt Orientierungswerte für die INR18650-35E:

| SoC (%) | OCV (ca.) | Zustand |
|---|---|---|
| 100 | 4,20 V | Vollgeladen |
| 90 | 4,08 V | – |
| 80 | 3,97 V | – |
| 70 | 3,88 V | – |
| 60 | 3,80 V | – |
| 50 | 3,73 V | Nennspannung (Bereich) |
| 40 | 3,65 V | – |
| 30 | 3,58 V | – |
| 20 | 3,48 V | – |
| 10 | 3,30 V | Bald entladen |
| 5 | 3,10 V | Tiefentladung vermeiden |
| 0 | 2,65 V | Entladeschlussspannung |

**Limitierung:** OCV-Werte gelten im Ruhezustand (nach ≥ 30 min Relaxation). Unter Last liegt die Klemmenspannung aufgrund des Innenwiderstands tiefer: $V_\text{Klemme} = V_\text{OCV} - I \cdot R_i$.

### 3.2 SoC-Schätzung per Spannungsmessung

Im mittleren SoC-Bereich (20 % … 80 %) verläuft die Spannungskurve relativ flach (ca. 3,50 V … 3,97 V). Eine rein spannungsbasierte SoC-Schätzung ist daher in diesem Bereich ungenau. Für präzisere Ergebnisse empfiehlt sich eine Kombination aus Coulomb-Counting (Ladungsintegration) und OCV-Korrektur im Ruhezustand.

---

## 4 3S-Konfiguration (Reihenschaltung)

### 4.1 Grundlagen der 3S-Verschaltung

Drei Zellen in Reihe (3S1P) addieren ihre Spannungen bei gleicher Kapazität. Die Gesamtparameter ergeben sich wie folgt:

```
┌──────────┐   ┌──────────┐   ┌──────────┐
│  Zelle 1 │───│  Zelle 2 │───│  Zelle 3 │
│ INR18650 │   │ INR18650 │   │ INR18650 │
│   -35E   │   │   -35E   │   │   -35E   │
└──────────┘   └──────────┘   └──────────┘
  +  3,6 V -     +  3,6 V -     +  3,6 V -
├──────────────────────────────────────────┤
              3 × 3,6 V = 10,8 V
```

### 4.2 Elektrische Kenndaten des 3S1P-Packs

| Parameter | Einzelzelle | 3S1P-Pack | Berechnung |
|---|---|---|---|
| Nennspannung | 3,60 V | 10,80 V | $3 \times 3{,}60\,\text{V}$ |
| Ladeschlussspannung | 4,20 V | 12,60 V | $3 \times 4{,}20\,\text{V}$ |
| Entladeschlussspannung | 2,65 V | 7,95 V | $3 \times 2{,}65\,\text{V}$ |
| Empf. BMS-Abschaltung | 3,00 V | 9,00 V | $3 \times 3{,}00\,\text{V}$ (konservativ) |
| Nennkapazität | 3.350 mAh | 3.350 mAh | Unverändert bei Reihenschaltung |
| Nennenergie | 12,06 Wh | 36,18 Wh | $10{,}80\,\text{V} \times 3{,}35\,\text{Ah}$ |
| Max. Dauerstrom | 8 A | 8 A | Unverändert bei Reihenschaltung |
| Max. Impulsstrom | 13 A | 13 A | Unverändert bei Reihenschaltung |
| Max. Dauerleistung | – | 86,4 W | $10{,}80\,\text{V} \times 8\,\text{A}$ |
| Gewicht (nur Zellen) | 50 g | 150 g | $3 \times 50\,\text{g}$ |

### 4.3 Spannungsbereiche im Betrieb

| Zustand | Packspannung | Einzelzellspannung |
|---|---|---|
| Vollgeladen | 12,60 V | 4,20 V |
| Nennspannung | 10,80 V | 3,60 V |
| 20 % SoC | ≈ 10,44 V | ≈ 3,48 V |
| 10 % SoC | ≈ 9,90 V | ≈ 3,30 V |
| BMS-Abschaltung (empf.) | 9,00 V … 9,50 V | 3,00 V … 3,17 V |
| Entladeschlussspannung | 7,95 V | 2,65 V |
| BMS-Tiefentladeschutz | 7,50 V | 2,50 V |
| BMS-Shutdown | 6,00 V | 2,00 V |

### 4.4 Laufzeitabschätzung

Die nutzbare Laufzeit $t$ berechnet sich aus:

$$
t = \frac{C_\text{nutzbar}}{I_\text{mittel}}
$$

Dabei berücksichtigt $C_\text{nutzbar}$ den nutzbaren SoC-Bereich. Bei einer Begrenzung auf 10 % … 90 % SoC (80 % der Nennkapazität):

$$
C_\text{nutzbar} = 0{,}80 \times 3{,}35\,\text{Ah} = 2{,}68\,\text{Ah}
$$

| Last (Durchschnitt) | Laufzeit (ca.) | Anwendungsbeispiel |
|---|---|---|
| 500 mA | 5 h 22 min | Raspberry Pi 5 (Leerlauf) |
| 1,0 A | 2 h 41 min | Sensorik + Steuerung |
| 2,0 A | 1 h 20 min | AMR mit leichten Motoren |
| 4,0 A | 40 min | AMR mit Servos unter Last |

**Limitierung:** Diese Berechnung nimmt einen konstanten mittleren Strom an. Reale Lastprofile sind dynamisch; die tatsächliche Laufzeit weicht je nach Lastspitzen und Temperaturbedingungen ab.

---

## 5 BMS-Anforderungen (Battery Management System)

### 5.1 Pflichtfunktionen

Samsung SDI schreibt für Akkupacks ein BMS mit folgenden Schutzfunktionen vor:

| Schutzfunktion | Schwellwert (pro Zelle) | Bemerkung |
|---|---|---|
| Überspannung (OVP) | 4,25 V … 4,35 V | Je nach Anwendungskategorie |
| Unterspannung (UVP) | 2,50 V | Harter Tiefentladeschutz |
| Entlade-Endschwelle (soft) | 3,00 V | Abschalten der Last durch Steuerung |
| Überstrom (OCP) | ≤ 8 A (Dauer) | Sicherung oder MOSFET-Abschaltung |
| Kurzschlussschutz (SCP) | Sofortige Abschaltung | Reaktionszeit < 1 ms |
| Übertemperatur (OTP) | ≥ 60 °C (Entladung), ≥ 45 °C (Ladung) | NTC-Sensor erforderlich |
| Balancing | ΔV ≤ 50 mV zwischen Zellen | Passiv oder aktiv |
| BMS-Shutdown-Spannung | 2,00 V pro Zelle | System vollständig abschalten |

### 5.2 Samsung Pack Design Guidelines – Anwendungskategorien

Samsung differenziert die BMS-Auslegung nach Anwendungskategorie. Relevante Parameter für die 4,20 V-Zellvariante:

| Parameter | Portable IT | E-Bike / E-Scooter | ESS / UPS |
|---|---|---|---|
| Standard-Ladespannung | 4,20 V | 4,10 V | 4,00 V (4,05 V) |
| Wiederauflade-Schwelle | 4,10 V | 4,05 V | 4,00 V (4,05 V) |
| Entlade-Endspannung | 3,00 V | 3,00 V | 3,00 V |
| UVP-Schwelle | 2,50 V | 2,50 V | 2,50 V |
| Full-Charge Cut-off | 0,05C | 0,025C | 0,025C |

**Konsequenz:** Für Robotikanwendungen (AMR) orientiert sich die BMS-Auslegung sinnvoll an der Kategorie „E-Bike/E-Scooter" mit reduzierter Ladeschlussspannung von 4,10 V pro Zelle (12,30 V für 3S). Dies verlängert die Zyklenlebensdauer erheblich auf Kosten von ca. 10 %–15 % nutzbarer Kapazität.

### 5.3 Vorladung (Pre-Charge)

Wenn die Zellspannung unter 3,00 V gefallen ist (aber über 1,00 V liegt), muss die Ladung mit einem reduzierten Vorladen-Strom (Pre-Charge) von 0,1C … 0,5C beginnen. Unterhalb von 1,00 V darf die Zelle nicht mehr geladen werden – sie gilt als irreversibel geschädigt.

---

## 6 Hardwareintegration – Spannungsmessung

### 6.1 ADC-Messung der Packspannung

Die Packspannung von bis zu 12,60 V liegt weit oberhalb des ADC-Eingangsbereichs typischer Mikrocontroller (z. B. ESP32-S3: 0 V … 3,3 V). Ein resistiver Spannungsteiler skaliert die Messspannung herunter.

**Dimensionierung:** Teilerverhältnis so wählen, dass bei maximaler Packspannung (12,60 V) die ADC-Referenzspannung nicht überschritten wird:

$$
V_\text{ADC} = V_\text{Pack} \times \frac{R_2}{R_1 + R_2} \leq V_\text{ref}
$$

Mit Sicherheitsmarge (Ziel: $V_\text{ADC,max} \approx 2{,}8\,\text{V}$ bei $V_\text{ref} = 3{,}3\,\text{V}$):

$$
\frac{R_2}{R_1 + R_2} = \frac{2{,}8\,\text{V}}{12{,}6\,\text{V}} \approx 0{,}222
$$

**Wahl:** $R_1 = 100\,\text{k}\Omega$, $R_2 = 27\,\text{k}\Omega$ → Teilerverhältnis $27 / 127 = 0{,}2126$

$$
V_\text{ADC,max} = 12{,}6\,\text{V} \times 0{,}2126 = 2{,}679\,\text{V} \quad \checkmark
$$

**Rückrechnung im Code:**

$$
V_\text{Pack} = V_\text{ADC} \times \frac{R_1 + R_2}{R_2} = V_\text{ADC} \times \frac{127}{27} \approx V_\text{ADC} \times 4{,}7037
$$

### 6.2 Firmware-Beispiel (ESP32-S3, ESP-IDF)

```c
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"

#define BATTERY_ADC_CHANNEL    ADC_CHANNEL_3    // GPIO4
#define VOLTAGE_DIVIDER_RATIO  4.7037f          // (R1 + R2) / R2 = 127k / 27k
#define ADC_SAMPLES            16               // Mittelwertbildung

// Spannungsteiler: R1 = 100 kΩ (Pack → ADC), R2 = 27 kΩ (ADC → GND)

static adc_oneshot_unit_handle_t adc_handle;
static adc_cali_handle_t         cali_handle;

esp_err_t battery_adc_init(void) {
    // ADC-Unit konfigurieren
    adc_oneshot_unit_init_cfg_t unit_cfg = {
        .unit_id  = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &adc_handle));

    // Kanal konfigurieren: 12 Bit, 11 dB Abschwächung (bis ca. 3,1 V)
    adc_oneshot_chan_cfg_t chan_cfg = {
        .atten    = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_handle, BATTERY_ADC_CHANNEL, &chan_cfg));

    // Kalibrierung (Curve Fitting für ESP32-S3)
    adc_cali_curve_fitting_config_t cali_cfg = {
        .unit_id  = ADC_UNIT_1,
        .chan     = BATTERY_ADC_CHANNEL,
        .atten   = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    return adc_cali_create_scheme_curve_fitting(&cali_cfg, &cali_handle);
}

float battery_read_voltage(void) {
    int32_t voltage_sum = 0;

    for (int i = 0; i < ADC_SAMPLES; i++) {
        int raw = 0;
        int voltage_mv = 0;
        adc_oneshot_read(adc_handle, BATTERY_ADC_CHANNEL, &raw);
        adc_cali_raw_to_voltage(cali_handle, raw, &voltage_mv);
        voltage_sum += voltage_mv;
    }

    float v_adc = (float)voltage_sum / (ADC_SAMPLES * 1000.0f);  // in Volt
    float v_pack = v_adc * VOLTAGE_DIVIDER_RATIO;

    return v_pack;  // Packspannung in Volt
}
```

### 6.3 SoC-Abschätzung per Lookup-Tabelle

```c
typedef struct {
    float voltage;  // Packspannung [V] (3S)
    uint8_t soc;    // Ladezustand [%]
} soc_lut_entry_t;

// Lookup-Tabelle: OCV → SoC (3S-Pack, Ruhezustand)
static const soc_lut_entry_t soc_lut[] = {
    { 12.60f, 100 },
    { 12.24f,  90 },
    { 11.91f,  80 },
    { 11.64f,  70 },
    { 11.40f,  60 },
    { 11.19f,  50 },
    { 10.95f,  40 },
    { 10.74f,  30 },
    { 10.44f,  20 },
    {  9.90f,  10 },
    {  9.30f,   5 },
    {  7.95f,   0 },
};

#define SOC_LUT_SIZE  (sizeof(soc_lut) / sizeof(soc_lut[0]))

uint8_t battery_estimate_soc(float pack_voltage) {
    if (pack_voltage >= soc_lut[0].voltage) return 100;
    if (pack_voltage <= soc_lut[SOC_LUT_SIZE - 1].voltage) return 0;

    // Lineare Interpolation zwischen Stützstellen
    for (size_t i = 0; i < SOC_LUT_SIZE - 1; i++) {
        if (pack_voltage >= soc_lut[i + 1].voltage) {
            float v_high = soc_lut[i].voltage;
            float v_low  = soc_lut[i + 1].voltage;
            float ratio  = (pack_voltage - v_low) / (v_high - v_low);
            float soc    = soc_lut[i + 1].soc + ratio * (soc_lut[i].soc - soc_lut[i + 1].soc);
            return (uint8_t)(soc + 0.5f);
        }
    }
    return 0;
}
```

**Limitierung der Spannungsmethode:** Die OCV-Tabelle liefert nur dann zuverlässige Ergebnisse, wenn die Messung im Ruhezustand (mindestens 30 Minuten nach Lastabwurf) erfolgt. Unter Last verschiebt der Spannungsabfall am Innenwiderstand ($\Delta V = I \times R_i$) die Messung. Für dynamische Anwendungen empfiehlt sich Coulomb-Counting als ergänzende Methode.

---

## 7 ROS 2-Integration – BatteryState-Nachricht

### 7.1 Nachrichtenformat

Das Standardformat für Batteriedaten in ROS 2 ist `sensor_msgs/msg/BatteryState`. Die wichtigsten Felder:

```c
// sensor_msgs/msg/BatteryState (Auszug)
float32 voltage              // Packspannung [V]
float32 current              // Strom [A] (negativ = Entladung)
float32 charge               // Aktuelle Ladung [Ah]
float32 capacity             // Nennkapazität [Ah]
float32 design_capacity      // Designkapazität [Ah]
float32 percentage           // SoC [0.0 .. 1.0]
uint8   power_supply_status  // CHARGING / DISCHARGING / NOT_CHARGING / FULL
uint8   power_supply_health  // GOOD / OVERHEAT / OVERVOLTAGE / ...
uint8   power_supply_technology // LION = 2
bool    present              // Batterie vorhanden
float32[] cell_voltage       // Einzelzellspannungen [V]
float32[] cell_temperature   // Zellentemperaturen [°C]
```

### 7.2 Publisher-Beispiel (micro-ROS, C)

```c
#include <sensor_msgs/msg/battery_state.h>

#define PACK_DESIGN_CAPACITY   3.35f   // [Ah]
#define PACK_CELLS             3
#define BATTERY_TECH_LION      2

void battery_publish(
    rcl_publisher_t *publisher,
    float pack_voltage,
    float current,
    float soc_percent,
    float cell_voltages[PACK_CELLS])
{
    sensor_msgs__msg__BatteryState msg;
    sensor_msgs__msg__BatteryState__init(&msg);

    msg.voltage                = pack_voltage;
    msg.current                = current;
    msg.percentage             = soc_percent / 100.0f;  // 0.0 .. 1.0
    msg.capacity               = PACK_DESIGN_CAPACITY;
    msg.design_capacity        = PACK_DESIGN_CAPACITY;
    msg.charge                 = PACK_DESIGN_CAPACITY * (soc_percent / 100.0f);
    msg.power_supply_technology = BATTERY_TECH_LION;
    msg.present                = true;

    // Einzelzellspannungen
    msg.cell_voltage.size = PACK_CELLS;
    msg.cell_voltage.data = cell_voltages;

    // Status bestimmen
    if (current > 0.05f) {
        msg.power_supply_status = sensor_msgs__msg__BatteryState__POWER_SUPPLY_STATUS_CHARGING;
    } else if (current < -0.05f) {
        msg.power_supply_status = sensor_msgs__msg__BatteryState__POWER_SUPPLY_STATUS_DISCHARGING;
    } else if (soc_percent > 99.0f) {
        msg.power_supply_status = sensor_msgs__msg__BatteryState__POWER_SUPPLY_STATUS_FULL;
    } else {
        msg.power_supply_status = sensor_msgs__msg__BatteryState__POWER_SUPPLY_STATUS_NOT_CHARGING;
    }

    // Health bestimmen
    if (pack_voltage > 12.60f) {
        msg.power_supply_health = sensor_msgs__msg__BatteryState__POWER_SUPPLY_HEALTH_OVERVOLTAGE;
    } else if (pack_voltage < 9.00f) {
        msg.power_supply_health = sensor_msgs__msg__BatteryState__POWER_SUPPLY_HEALTH_DEAD;
    } else {
        msg.power_supply_health = sensor_msgs__msg__BatteryState__POWER_SUPPLY_HEALTH_GOOD;
    }

    rcl_publish(publisher, &msg, NULL);
}
```

---

## 8 Sicherheitsabschaltung – Schwellwertlogik

### 8.1 Mehrstufiges Schutzkonzept

Ein robustes Batteriesystem implementiert mehrere Schutzstufen:

```
Stufe 1 – Soft-Warnung (Software):
    Pack ≤ 10,0 V  →  Warnung an Operator / ROS-Topic
    Maßnahme: Leistungsreduktion, Status-LED gelb

Stufe 2 – Motor-Abschaltung (Software):
    Pack ≤ 9,5 V   →  Motoren abschalten, Sensorik aktiv
    Maßnahme: Graceful Shutdown einleiten

Stufe 3 – System-Shutdown (Software):
    Pack ≤ 9,0 V   →  Geordneter System-Shutdown
    Maßnahme: Dateisystem sicher unmounten, Pi herunterfahren

Stufe 4 – Hardware-Abschaltung (BMS):
    Zelle ≤ 2,50 V →  BMS trennt Last (MOSFET öffnet)
    Maßnahme: Letzte Schutzebene, rein hardwarebasiert
```

### 8.2 Firmware-Implementierung

```c
typedef enum {
    BAT_STATE_OK,
    BAT_STATE_WARNING,
    BAT_STATE_MOTOR_SHUTDOWN,
    BAT_STATE_SYSTEM_SHUTDOWN,
    BAT_STATE_CRITICAL
} battery_state_t;

#define THRESHOLD_WARNING         10.0f   // [V] Pack
#define THRESHOLD_MOTOR_SHUTDOWN   9.5f
#define THRESHOLD_SYSTEM_SHUTDOWN  9.0f
#define THRESHOLD_CRITICAL         7.5f   // BMS-Bereich
#define HYSTERESIS                 0.3f   // [V] Rücksetz-Hysterese

battery_state_t battery_evaluate(float pack_voltage, battery_state_t current_state) {
    // Abwärts: sofort bei Unterschreiten
    if (pack_voltage <= THRESHOLD_CRITICAL)        return BAT_STATE_CRITICAL;
    if (pack_voltage <= THRESHOLD_SYSTEM_SHUTDOWN)  return BAT_STATE_SYSTEM_SHUTDOWN;
    if (pack_voltage <= THRESHOLD_MOTOR_SHUTDOWN)   return BAT_STATE_MOTOR_SHUTDOWN;
    if (pack_voltage <= THRESHOLD_WARNING)          return BAT_STATE_WARNING;

    // Aufwärts: nur mit Hysterese zurücksetzen
    if (current_state == BAT_STATE_WARNING &&
        pack_voltage > THRESHOLD_WARNING + HYSTERESIS) {
        return BAT_STATE_OK;
    }

    // Im Zweifelsfall aktuellen Zustand beibehalten
    return (pack_voltage > THRESHOLD_WARNING) ? BAT_STATE_OK : current_state;
}
```

---

## 9 Energieberechnung und Laufzeitplanung

### 9.1 Energieinhalt des 3S1P-Packs

| Betriebsmodus | Kapazität | Energie | Berechnung |
|---|---|---|---|
| Volle Kapazität (100 % → 0 %) | 3,35 Ah | 36,18 Wh | $10{,}80\,\text{V} \times 3{,}35\,\text{Ah}$ |
| Nutzbare Kapazität (90 % → 10 %) | 2,68 Ah | 28,94 Wh | $10{,}80\,\text{V} \times 2{,}68\,\text{Ah}$ |
| E-Bike-Modus (4,10 V → 3,00 V/Zelle) | ≈ 2,85 Ah | ≈ 30,78 Wh | Reduzierte Ladespannung |

### 9.2 Beispielhafte Leistungsaufnahme eines AMR-Systems

| Subsystem | Spannung | Strom (typ.) | Leistung |
|---|---|---|---|
| Raspberry Pi 5 (aktiv) | 5 V (via Regler) | 800 mA | 4,0 W |
| ESP32-S3 (aktiv) | 3,3 V (via Regler) | 150 mA | 0,5 W |
| 4× Servomotor (Durchschnitt) | 6 V (via D36V50F6) | 2.000 mA | 12,0 W |
| Sensorik (LiDAR, IMU, Kamera) | diverse | – | 3,0 W |
| Reglerverluste (geschätzt) | – | – | 2,5 W |
| **Gesamt (aktiver Betrieb)** | – | – | **22,0 W** |
| **Gesamt (Standby)** | – | – | **≈ 6,0 W** |

### 9.3 Resultierende Laufzeiten

$$
t = \frac{E_\text{nutzbar}}{P_\text{mittel}}
$$

| Betriebsmodus | Mittlere Leistung | Laufzeit (ca.) |
|---|---|---|
| Standby (Pi + ESP32 + Sensorik) | 6 W | 4 h 49 min |
| Leichtbetrieb (gelegentliches Fahren) | 12 W | 2 h 25 min |
| Aktiver Betrieb (kontinuierlich) | 22 W | 1 h 19 min |
| Maximallast (alle Servos + Compute) | 30 W | 58 min |

---

## 10 Ladegerät-Spezifikation

### 10.1 Anforderungen für 3S CC-CV-Ladung

| Parameter | Wert |
|---|---|
| Ladeschlussspannung (Pack) | 12,60 V (3 × 4,20 V) |
| Ladeschlussspannung (Zyklus-optimiert) | 12,30 V (3 × 4,10 V) |
| Standard-Ladestrom | 1,7 A (0,5C) |
| Max. Ladestrom | 2,0 A |
| CV-Abschaltstrom | 68 mA (0,02C) |
| Max. Ladezeit (Sicherheits-Timer) | 4 h |
| Balancing | Erforderlich (passiv oder aktiv) |

### 10.2 Ladeprofil

```
Strom [A]
  2,0 ┤ ┌──────────────────────┐
      │ │     CC-Phase         │
  1,7 ┤ │  (Konstantstrom)     │
      │ │                      └────────┐  CV-Phase
  1,0 ┤ │                               │  (Konstantspannung)
      │ │                               │
  0,5 ┤ │                               └───────┐
      │ │                                       └──────┐
 0,07 ┤ │                                              └── Cut-off
      └─┴──────────────────────────────────────────────────── Zeit
      0          ~1,5 h              ~3 h          ~4 h

Spannung [V]
 12,6 ┤                        ┌────────────────────────────
      │                     ╱  
 11,5 ┤                  ╱
      │              ╱
 10,5 ┤           ╱
      └─────────╱──────────────────────────────────── Zeit
```

**Regel:** In der CC-Phase steigt die Packspannung kontinuierlich, bis 12,60 V (bzw. 12,30 V bei zyklenoptimierter Ladung) erreicht sind. Anschließend hält die CV-Phase die Spannung konstant, während der Strom exponentiell abfällt. Die Ladung gilt als abgeschlossen, wenn der Strom unter 68 mA fällt.

---

## 11 Lagerung und Transport

### 11.1 Lagerempfehlungen

| Bedingung | Empfehlung |
|---|---|
| Lagerspannung (Einzelzelle) | 3,49 V … 3,69 V (Ab-Werk-Zustand, ca. 30 % SoC) |
| Lagerspannung (3S-Pack) | 10,47 V … 11,07 V |
| Temperatur (Langzeit) | −20 °C … +25 °C |
| Luftfeuchtigkeit | Niedrig, trocken |
| Inspektionsintervall | Alle 3 Monate Spannung prüfen, ggf. nachladen |

### 11.2 Transportvorschriften

Lithium-Ionen-Zellen und -Akkupacks unterliegen den Gefahrgutvorschriften gemäß UN 38.3. Für den Versand gelten insbesondere folgende Anforderungen: Zellen müssen den UN-38.3-Transporttest bestanden haben (was für die INR18650-35E der Fall ist), die Verpackung muss gegen Kurzschluss schützen, und der SoC sollte maximal 30 % betragen.

---

## 12 Zusammenfassung der Schlüsselparameter

```
┌────────────────────────────────────────────────────────────────┐
│         Samsung INR18650-35E – 3S1P Kurzprofil                 │
├─────────────────────────┬──────────────────────────────────────┤
│ Zellchemie              │ NCA (LiNiCoAlO₂)                    │
│ Bauform                 │ 18650, Flat Top, ungeschützt         │
│ Einzelzelle – Nennwerte │ 3,60 V / 3.350 mAh / 12,06 Wh      │
│ 3S1P-Pack – Nennwerte   │ 10,80 V / 3.350 mAh / 36,18 Wh     │
│ Spannungsbereich (Pack) │ 7,95 V … 12,60 V                    │
│ Max. Dauerstrom         │ 8 A (kontinuierlich)                 │
│ Max. Impulsstrom        │ 13 A (kurzzeitig)                    │
│ Innenwiderstand         │ ≤ 35 mΩ (pro Zelle, initial)        │
│ Zyklenlebensdauer       │ ≥ 500 Zyklen @ 60 % Restkapazität   │
│ Ladetemperatur          │ 0 °C … +45 °C                       │
│ Entladetemperatur       │ −10 °C … +60 °C                     │
│ Gewicht (3 Zellen)      │ ≤ 150 g                              │
│ BMS-Abschaltung (empf.) │ 9,0 V (Pack) / 3,0 V (Zelle)       │
└─────────────────────────┴──────────────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2025-02-24 | Datenquelle: Samsung SDI Spec. INR18650-35E, Version 1.1 (Juli 2015)*
