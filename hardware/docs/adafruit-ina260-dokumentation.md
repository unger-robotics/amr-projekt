# Adafruit INA260 – Strom-, Spannungs- und Leistungssensor Breakout (I²C)

> **Technische Dokumentation** – Adafruit Industries, Art.-Nr. 4226  
> Sensor-IC: Texas Instruments INA260AIPWR (TSSOP-16)  
> Typ: Digitaler Hochpräzisions-Leistungsmonitor (Current/Voltage/Power Monitor) mit integriertem Shunt  
> Schnittstelle: I²C / SMBus, 16 programmierbare Adressen  
> Quellen: [Adafruit Produktseite](https://www.adafruit.com/product/4226), [TI INA260 Datenblatt Rev. C](https://www.ti.com/lit/ds/symlink/ina260.pdf), [Adafruit Learning Guide](https://learn.adafruit.com/adafruit-ina260-current-voltage-power-sensor-breakout)

---

## 1 Übersicht

Der INA260 von Texas Instruments ist ein digitaler Strom-, Spannungs- und Leistungssensor mit integriertem Präzisions-Shuntwiderstand (Shunt Resistor) und I²C-Schnittstelle. Das Adafruit Breakout-Board (Art.-Nr. 4226) macht den Sensor für Prototyping und Einbettung in eingebettete Systeme direkt zugänglich.

Die zentrale Eigenschaft des INA260 gegenüber vergleichbaren Sensoren wie dem INA219 liegt in der Integration des Shunt-Widerstands (2 mΩ, 0,1 % Toleranz-Äquivalent) direkt im IC-Gehäuse. Dadurch entfallen externe Shunt-Widerstände, Kelvin-Kontaktierung und Kalibrierung. Der interne Multiplikator liefert Strom in Ampere und Leistung in Watt als direkt auslesbare Registerwerte.

**Typische Anwendungen:** Batterie-Monitoring in mobilen Robotern (AMR), Energieprofiling eingebetteter Systeme, Überstromschutz, Leistungsmessung an Servomotoren, Labormesstechnik, Power-Management in Servern und Telekommunikation.

---

## 2 Spezifikationen – INA260 Sensor-IC

### 2.1 Elektrische Kenndaten

Alle Werte bei $T_A = 25\,°\text{C}$, $V_S = 3{,}3\,\text{V}$, $V_\text{IN+} = 12\,\text{V}$, sofern nicht anders angegeben. Quelle: TI INA260 Datenblatt SBOS656C, Rev. C.

| Parameter | Min. | Typ. | Max. | Einheit | Bemerkung |
|---|---|---|---|---|---|
| **Eingangsspannungsbereich (Common Mode)** | 0 | – | 36 | V | Unabhängig von $V_S$ |
| **Versorgungsspannung** $V_S$ | 2,7 | – | 5,5 | V | – |
| **Ruhestrom** $I_Q$ | – | 310 | 420 | µA | Aktiver Betrieb |
| **Ruhestrom (Shutdown)** | – | 0,5 | 2 | µA | Power-Down-Modus |
| **Integrierter Shunt-Widerstand** | – | 2 | – | mΩ | Kelvin-kontaktiert, intern |
| **Gesamter Paketwiderstand** (IN+ → IN−) | – | 4,5 | – | mΩ | Inkl. Bonddraht und Leiterbahn |
| **Maximaler Dauerstrom** | – | – | ±15 | A | $-40\,°\text{C}$ bis $+85\,°\text{C}$, 1 oz Cu |
| **Maximaler Dauerstrom (deratiert)** | – | – | ±10 | A | Bei $T_A = 125\,°\text{C}$ |
| **Stromrichtung** | – | bidirektional | – | – | High-Side oder Low-Side |
| **Systemgenauigkeit Strom** | – | 0,02 % | 0,15 % | – | $I = \pm 15\,\text{A}$, $T_A = 25\,°\text{C}$ |
| **Systemgenauigkeit Strom (Temp.)** | – | 0,2 % | 0,5 % | – | $I = \pm 10\,\text{A}$, $-40\,°\text{C}$ bis $+125\,°\text{C}$ |
| **Strom-Offset** $I_\text{OS}$ | – | ±1,25 | ±5 | mA | – |
| **Systemgenauigkeit Busspannung** | – | 0,02 % | 0,1 % | – | $V_\text{BUS} = 0\,\text{V}$ bis $36\,\text{V}$, $T_A = 25\,°\text{C}$ |
| **Busspannungs-Offset** $V_\text{OS}$ | – | ±1,25 | ±7,5 | mV | – |
| **ADC-Auflösung** | – | 16 | – | Bit | – |
| **Temperaturkoeff. Shunt** | – | 10 | – | ppm/°C | $0\,°\text{C}$ bis $+125\,°\text{C}$ |
| **Betriebstemperatur** | −40 | – | +125 | °C | – |
| **I²C-Taktfrequenz** | 0,001 | – | 2,94 | MHz | High-Speed-Modus |
| **ESD-Festigkeit (HBM)** | – | – | ±2000 | V | ANSI/ESDA/JEDEC JS-001 |
| **Gehäuse** | – | TSSOP-16 | – | – | 5,0 mm × 4,4 mm |

### 2.2 ADC-Auflösung (LSB-Schrittweiten)

| Register | Messgröße | LSB | Vollausschlag (Full Scale) |
|---|---|---|---|
| `0x01` Current | Strom | 1,25 mA | ±16.384 A (vorzeichenbehaftet) |
| `0x02` Bus Voltage | Busspannung | 1,25 mV | 40,96 V (positiv, Bit 15 = 0) |
| `0x03` Power | Leistung | 10 mW | 419,43 W (stets positiv) |

**Berechnungsbeispiel:** Registerwert `0x2710` (dezimal 10.000) im Stromregister ergibt:

$$
I = 10000 \times 1{,}25\,\text{mA} = 12{,}5\,\text{A}
$$

Negative Ströme (IN− → IN+) liegen im Zweierkomplement vor.

### 2.3 Wandlungszeiten und Mittelwertbildung

Der ADC bietet 8 konfigurierbare Wandlungszeiten (Conversion Time, CT) für jeweils Strom und Busspannung. Die Gesamtaktualisierungszeit ergibt sich aus:

$$
t_\text{update} = (\text{CT}_\text{Strom} + \text{CT}_\text{Spannung}) \times N_\text{AVG}
$$

| CT-Bits | Wandlungszeit (typ.) | CT-Bits | Wandlungszeit (typ.) |
|---|---|---|---|
| `000` | 140 µs | `100` | 1,1 ms |
| `001` | 204 µs | `101` | 2,116 ms |
| `010` | 332 µs | `110` | 4,156 ms |
| `011` | 588 µs | `111` | 8,244 ms |

| AVG-Bits | Mittelwerte | AVG-Bits | Mittelwerte |
|---|---|---|---|
| `000` | 1 (Standard) | `100` | 128 |
| `001` | 4 | `101` | 256 |
| `010` | 16 | `110` | 512 |
| `011` | 64 | `111` | 1024 |

**Beispiel:** CT = 1,1 ms für beide Kanäle, AVG = 4 ergibt $t_\text{update} = (1{,}1 + 1{,}1) \times 4 = 8{,}8\,\text{ms}$ ≈ 114 Messungen/s.

**Kompromiss:** Längere Wandlungszeiten und höhere Mittelwertbildung reduzieren Rauschen, verlängern jedoch die Aktualisierungszeit. Die Standardeinstellung (`0x6127`) nutzt CT = 1,1 ms für beide Kanäle, AVG = 1, MODE = kontinuierlich → Aktualisierung alle 2,2 ms.

---

## 3 Adafruit Breakout-Board – Pinbelegung und Aufbau

### 3.1 Pinbelegung

```
                    ┌──────────────────────────┐
                    │   Adafruit INA260 4226    │
                    │                          │
 Klemmenblock ──►  [Vin+]              [Vin-]  ◄── Klemmenblock
  (5,08 mm)         │                          │     (5,08 mm)
                    │     ┌────────────┐       │
                    │     │  INA260 IC │       │
                    │     └────────────┘       │
                    │                          │
   Stiftleiste:     │  Vcc  GND  SCL  SDA      │
                    │  Alert  A0  A1  VBus     │
                    └──────────────────────────┘
```

### 3.2 Pin-Beschreibung

| Pin | Funktion | Beschreibung |
|---|---|---|
| **Vcc** | Versorgung | 2,7 V … 5,5 V, entsprechend der Logikspannung des Mikrocontrollers |
| **GND** | Masse | Gemeinsame Masse für Versorgung und Logik |
| **SCL** | I²C-Takt | Mit 10 kΩ Pull-up auf Vcc bestückt |
| **SDA** | I²C-Daten | Mit 10 kΩ Pull-up auf Vcc bestückt, Open-Drain |
| **Vin+** | Stromeingang (+) | High-Side: an Versorgung; Low-Side: an Last-Masse |
| **Vin−** | Stromeingang (−) | High-Side: an Last; Low-Side: an Board-Masse |
| **Alert** | Alarmausgang | Open-Drain, konfigurierbar (Überstrom, Unterspannung, Conversion Ready) |
| **VBus** | Busspannung | Standardmäßig über Jumper VB mit Vin+ verbunden |
| **A0** | Adress-Jumper | Lötbrücke, Standard: GND |
| **A1** | Adress-Jumper | Lötbrücke, Standard: GND |

### 3.3 I²C-Adressen (Breakout-Konfiguration)

Das Breakout bietet vier Adressen über die Lötbrücken A0 und A1:

| A1 | A0 | I²C-Adresse (hex) | Binär |
|---|---|---|---|
| GND | GND | `0x40` | `1000000` **(Standard)** |
| GND | Vcc | `0x41` | `1000001` |
| Vcc | GND | `0x44` | `1000100` |
| Vcc | Vcc | `0x45` | `1000101` |

Der INA260-Chip selbst unterstützt 16 Adressen (A0/A1 jeweils GND, Vs, SDA, SCL), das Breakout beschränkt auf die vier oben genannten Kombinationen. Bis zu vier Sensoren können parallel am selben I²C-Bus betrieben werden.

### 3.4 VBus-Jumper (VB)

Ab Werk verbindet eine Lötbrücke (VB) den Pin Vin+ mit dem VBUS-Eingang des ICs. Diese Konfiguration eignet sich für **High-Side-Messung**, da die Busspannung direkt am positiven Eingang abgegriffen wird.

Für **Low-Side-Messung** muss die VB-Lötbrücke aufgetrennt und der VBus-Pin separat an die Versorgungsschiene angeschlossen werden, damit Spannungs- und Leistungsberechnung korrekte Werte liefern.

### 3.5 Mechanische Daten

| Parameter | Wert |
|---|---|
| Abmessungen (PCB) | ca. 25,4 mm × 17,8 mm (1,0" × 0,7") |
| Klemmenblock-Rastermaß | 5,08 mm |
| Stiftleisten-Rastermaß | 2,54 mm (Standard) |
| Befestigungsbohrungen | 2 × ∅ 2,5 mm |
| Gewicht | ca. 5 g (ohne Header/Klemme) |

---

## 4 Messprinzip und Topologien

### 4.1 Messprinzip

Der INA260 misst zwei Größen direkt und berechnet eine dritte:

1. **Strom:** Der ADC misst die Spannung über dem internen 2 mΩ-Shunt (Kelvin-Kontaktierung). Ein interner Multiplikator rechnet den Wert direkt in mA um (LSB = 1,25 mA).
2. **Busspannung:** Der ADC misst die Spannung am VBUS-Pin gegen GND (LSB = 1,25 mV).
3. **Leistung:** Der IC multipliziert intern $P = V_\text{BUS} \times I$ und stellt das Ergebnis in mW bereit (LSB = 10 mW).

### 4.2 High-Side-Messung (Standard)

Der Sensor sitzt zwischen Spannungsquelle und Last in der positiven Leitung. VBus ist über die VB-Brücke mit Vin+ verbunden.

```
V_Supply ── [Vin+] ──┤INA260├── [Vin-] ── Last ── GND
                      │      │
                      └─VBUS─┘  (VB-Jumper geschlossen)
```

**Vorteil:** Busspannung und Leistung sind direkt korrekt. Die Masseleitung der Last bleibt ungestört.

### 4.3 Low-Side-Messung

Der Sensor sitzt zwischen Last und Masse.

```
V_Supply ── Last ── [Vin+] ──┤INA260├── [Vin-] ── GND
                                          │
               V_Supply ──── [VBus]       │
                           (VB-Jumper aufgetrennt!)
```

**Hinweis:** Für korrekte Spannungs- und Leistungswerte muss die VB-Lötbrücke aufgetrennt und VBus separat an die Versorgungsschiene angeschlossen werden.

---

## 5 Registerstruktur

### 5.1 Registerübersicht

| Adresse | Name | Zugriff | Reset-Wert | Funktion |
|---|---|---|---|---|
| `0x00` | Configuration | R/W | `0x6127` | Betriebsmodus, Wandlungszeit, Mittelwertbildung |
| `0x01` | Current | R | `0x0000` | Stromwert (Zweierkomplement, LSB = 1,25 mA) |
| `0x02` | Bus Voltage | R | `0x0000` | Busspannung (LSB = 1,25 mV) |
| `0x03` | Power | R | `0x0000` | Leistung (LSB = 10 mW, stets positiv) |
| `0x06` | Mask/Enable | R/W | `0x0000` | Alert-Konfiguration und CVRF-Flag |
| `0x07` | Alert Limit | R/W | `0x0000` | Schwellenwert für Alert-Funktion |
| `0xFE` | Manufacturer ID | R | `0x5449` | „TI" in ASCII |
| `0xFF` | Die ID | R | `0x2270` | Chip-Identifikation |

### 5.2 Configuration Register (`0x00`) – Bitfeld

```
Bit:  15   14-12   11-9    8-6     5-3     2-0
      RST  [110]   AVG    VBUSCT  ISHCT   MODE
       0    110     000    100     100     111
```

| Bitfeld | Bits | Beschreibung | Standardwert |
|---|---|---|---|
| RST | 15 | Reset-Bit, selbstlöschend | 0 |
| – | 14–12 | Reserviert (fest `110`) | `110` |
| AVG | 11–9 | Mittelwertbildung (1 … 1024) | `000` (= 1) |
| VBUSCT | 8–6 | Wandlungszeit Busspannung | `100` (= 1,1 ms) |
| ISHCT | 5–3 | Wandlungszeit Strom (Shunt) | `100` (= 1,1 ms) |
| MODE | 2–0 | Betriebsmodus | `111` (= kontinuierlich, Strom + Spannung) |

### 5.3 Betriebsmodi (MODE-Bits)

| MODE | Modus |
|---|---|
| `000` | Power-Down (Shutdown) |
| `001` | Strom, einzeln ausgelöst (Triggered) |
| `010` | Spannung, einzeln ausgelöst |
| `011` | Strom + Spannung, einzeln ausgelöst |
| `100` | Power-Down (Shutdown) |
| `101` | Strom, kontinuierlich |
| `110` | Spannung, kontinuierlich |
| `111` | Strom + Spannung, kontinuierlich **(Standard)** |

### 5.4 Mask/Enable Register (`0x06`) – Alert-Funktionen

| Bit | Name | Funktion |
|---|---|---|
| 15 | OCL | Überstrom-Grenzwert (Over Current Limit) |
| 14 | UCL | Unterstrom-Grenzwert (Under Current Limit) |
| 13 | BOL | Busüberspannung (Bus Over-Voltage Limit) |
| 12 | BUL | Busunterspannung (Bus Under-Voltage Limit) |
| 11 | POL | Leistungsgrenzwert (Power Over-Limit) |
| 10 | CNVR | Wandlung abgeschlossen (Conversion Ready) |
| 4 | AFF | Alert Function Flag (nur lesen) |
| 3 | CVRF | Conversion Ready Flag (nur lesen) |
| 2 | OVF | Math Overflow Flag (Leistung > 419,43 W) |
| 1 | APOL | Alert-Polarität (0 = Active-Low, 1 = Active-High) |
| 0 | LEN | Alert Latch Enable (0 = Transparent, 1 = Latch) |

Es kann jeweils nur eine Alert-Funktion (Bit 15–11) gleichzeitig aktiv sein. Bei Mehrfachsetzung gilt die mit dem höchsten Bit.

---

## 6 Verdrahtung

### 6.1 High-Side-Messung am ESP32-S3 (3,3 V)

```
ESP32-S3                    Adafruit INA260 Breakout
─────────                   ────────────────────────
  3V3  ───────────────────── Vcc
  GND  ───────────────────── GND
  GPIO 8 (SCL) ──────────── SCL    (10 kΩ Pull-up auf Breakout)
  GPIO 9 (SDA) ──────────── SDA    (10 kΩ Pull-up auf Breakout)

                                    ┌── [Vin+]
  Batterie (+) ─────────────────────┘
                                        INA260
  Last (+) ─────────────────────────┐
                                    └── [Vin-]

  Batterie (−) ── Last (−) ── GND (gemeinsam)
```

**I²C-Pull-ups:** Das Breakout bringt 10 kΩ-Pull-up-Widerstände auf SCL und SDA mit. Zusätzliche externe Pull-ups sind nicht erforderlich, sofern keine ungewöhnlich langen Leitungen oder viele I²C-Geräte am Bus hängen.

### 6.2 Mehrere Sensoren am selben Bus

Bis zu vier INA260-Breakouts (Adressen `0x40` … `0x45`) können parallel an einem I²C-Bus betrieben werden, um verschiedene Verbraucher unabhängig zu überwachen. Bei mehr als einem Breakout empfiehlt sich das Deaktivieren redundanter Pull-ups (Auftrennen der Pull-up-Lötbrücken auf den zusätzlichen Boards).

---

## 7 Firmware-Integration (ESP32-S3, ESP-IDF)

### 7.1 I²C-Initialisierung und Registeroperationen

```c
#include "driver/i2c_master.h"
#include <string.h>

#define INA260_ADDR            0x40

/* Registeradressen */
#define INA260_REG_CONFIG      0x00
#define INA260_REG_CURRENT     0x01
#define INA260_REG_VOLTAGE     0x02
#define INA260_REG_POWER       0x03
#define INA260_REG_MASK_EN     0x06
#define INA260_REG_ALERT_LIM   0x07
#define INA260_REG_MFR_ID      0xFE
#define INA260_REG_DIE_ID      0xFF

/* LSB-Konstanten */
#define INA260_CURRENT_LSB_MA  1.25f    /* mA pro Bit */
#define INA260_VOLTAGE_LSB_MV  1.25f    /* mV pro Bit */
#define INA260_POWER_LSB_MW    10.0f    /* mW pro Bit */

static i2c_master_bus_handle_t i2c_bus;
static i2c_master_dev_handle_t ina260_dev;

esp_err_t ina260_init(gpio_num_t sda, gpio_num_t scl) {
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port   = I2C_NUM_0,
        .sda_io_num = sda,
        .scl_io_num = scl,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &i2c_bus));

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = INA260_ADDR,
        .scl_speed_hz    = 400000,  /* Fast Mode */
    };
    return i2c_master_bus_add_device(i2c_bus, &dev_cfg, &ina260_dev);
}
```

### 7.2 Register lesen und schreiben

```c
/* 16-Bit-Register lesen (Big-Endian) */
esp_err_t ina260_read_reg(uint8_t reg, uint16_t *value) {
    uint8_t buf[2];
    esp_err_t ret = i2c_master_transmit_receive(
        ina260_dev, &reg, 1, buf, 2, pdMS_TO_TICKS(100));
    if (ret == ESP_OK) {
        *value = ((uint16_t)buf[0] << 8) | buf[1];
    }
    return ret;
}

/* 16-Bit-Register schreiben (Big-Endian) */
esp_err_t ina260_write_reg(uint8_t reg, uint16_t value) {
    uint8_t buf[3] = { reg, (uint8_t)(value >> 8), (uint8_t)(value & 0xFF) };
    return i2c_master_transmit(ina260_dev, buf, 3, pdMS_TO_TICKS(100));
}
```

### 7.3 Messwerte auslesen

```c
/* Strom in mA (vorzeichenbehaftet) */
float ina260_read_current_mA(void) {
    uint16_t raw;
    ina260_read_reg(INA260_REG_CURRENT, &raw);
    int16_t signed_raw = (int16_t)raw;  /* Zweierkomplement */
    return (float)signed_raw * INA260_CURRENT_LSB_MA;
}

/* Busspannung in mV */
float ina260_read_voltage_mV(void) {
    uint16_t raw;
    ina260_read_reg(INA260_REG_VOLTAGE, &raw);
    return (float)raw * INA260_VOLTAGE_LSB_MV;
}

/* Leistung in mW (stets positiv) */
float ina260_read_power_mW(void) {
    uint16_t raw;
    ina260_read_reg(INA260_REG_POWER, &raw);
    return (float)raw * INA260_POWER_LSB_MW;
}
```

### 7.4 Konfigurationsbeispiele

```c
/* Standard: CT = 1,1 ms, AVG = 1, kontinuierlich Strom + Spannung */
void ina260_config_default(void) {
    ina260_write_reg(INA260_REG_CONFIG, 0x6127);
}

/* Hohe Genauigkeit: CT = 8,244 ms, AVG = 16, kontinuierlich */
/* Update-Rate: (8,244 + 8,244) × 16 ≈ 263,8 ms → ca. 3,8 Hz */
void ina260_config_high_accuracy(void) {
    uint16_t cfg = (0x6 << 12)    /* reserviert */
                 | (0x2 << 9)     /* AVG = 16 */
                 | (0x7 << 6)     /* VBUSCT = 8,244 ms */
                 | (0x7 << 3)     /* ISHCT = 8,244 ms */
                 | (0x7 << 0);    /* MODE = kontinuierlich beides */
    ina260_write_reg(INA260_REG_CONFIG, cfg);
}

/* Schnelle Messung: CT = 204 µs, AVG = 4, kontinuierlich */
/* Update-Rate: (0,204 + 0,204) × 4 ≈ 1,6 ms → ca. 610 Hz */
void ina260_config_fast(void) {
    uint16_t cfg = (0x6 << 12)
                 | (0x1 << 9)     /* AVG = 4 */
                 | (0x1 << 6)     /* VBUSCT = 204 µs */
                 | (0x1 << 3)     /* ISHCT = 204 µs */
                 | (0x7 << 0);
    ina260_write_reg(INA260_REG_CONFIG, cfg);
}

/* Software-Reset */
void ina260_reset(void) {
    ina260_write_reg(INA260_REG_CONFIG, 0xE127);  /* Bit 15 = 1 */
}
```

### 7.5 Alert-Funktion – Überstrom-Erkennung

```c
/* Überstrom-Alert bei > 5 A konfigurieren */
void ina260_config_overcurrent_alert(float limit_mA) {
    /* Alert-Limit-Register: Wert im Format des Stromregisters */
    int16_t limit_raw = (int16_t)(limit_mA / INA260_CURRENT_LSB_MA);
    ina260_write_reg(INA260_REG_ALERT_LIM, (uint16_t)limit_raw);

    /* Mask/Enable: OCL (Bit 15) aktivieren, Latch (Bit 0) aktivieren */
    ina260_write_reg(INA260_REG_MASK_EN, 0x8001);
}

/* Alert-Status prüfen */
bool ina260_check_alert(void) {
    uint16_t mask_en;
    ina260_read_reg(INA260_REG_MASK_EN, &mask_en);
    return (mask_en & (1 << 4)) != 0;  /* AFF-Bit (Alert Function Flag) */
}
```

### 7.6 Chip-Identifikation (Verbindungstest)

```c
bool ina260_verify_connection(void) {
    uint16_t mfr_id, die_id;
    if (ina260_read_reg(INA260_REG_MFR_ID, &mfr_id) != ESP_OK) return false;
    if (ina260_read_reg(INA260_REG_DIE_ID, &die_id) != ESP_OK) return false;
    /* Erwartete Werte: MFR = 0x5449 ("TI"), DIE = 0x2270 */
    return (mfr_id == 0x5449) && (die_id == 0x2270);
}
```

---

## 8 ROS 2-Integration (micro-ROS)

### 8.1 BatteryState-Publisher

Der INA260 liefert alle Größen für eine `sensor_msgs/msg/BatteryState`-Nachricht. Der folgende Codeausschnitt zeigt die Integration als micro-ROS-Publisher auf dem ESP32-S3.

```c
#include <sensor_msgs/msg/battery_state.h>

static sensor_msgs__msg__BatteryState battery_msg;
static rcl_publisher_t battery_pub;

void ina260_publish_battery_state(void) {
    float voltage_mV = ina260_read_voltage_mV();
    float current_mA = ina260_read_current_mA();
    float power_mW   = ina260_read_power_mW();

    battery_msg.voltage       = voltage_mV / 1000.0f;     /* V  */
    battery_msg.current       = current_mA / 1000.0f;     /* A  */
    battery_msg.charge        = NAN;
    battery_msg.capacity      = NAN;
    battery_msg.design_capacity = NAN;
    battery_msg.percentage    = NAN;  /* SoC hier ggf. aus Lookup-Tabelle */
    battery_msg.power_supply_status =
        sensor_msgs__msg__BatteryState__POWER_SUPPLY_STATUS_DISCHARGING;
    battery_msg.power_supply_technology =
        sensor_msgs__msg__BatteryState__POWER_SUPPLY_TECHNOLOGY_LION;
    battery_msg.present = true;

    rcl_publish(&battery_pub, &battery_msg, NULL);
}
```

### 8.2 Diagnose-Topic

Für ein dediziertes Power-Monitor-Topic kann alternativ ein `diagnostic_msgs/msg/DiagnosticStatus` oder ein eigenes Custom-Message mit den Feldern `voltage_mV`, `current_mA` und `power_mW` publiziert werden – ohne den Overhead der BatteryState-Nachricht.

---

## 9 Anwendungsbeispiel – AMR-Systemüberwachung

### 9.1 Systemarchitektur

Im Kontext des AMR-Projekts überwacht der INA260 den Gesamtstrom des 3S-Li-Ion-Akkupacks (Samsung INR18650-35E). Der Sensor sitzt High-Side zwischen Akkupack und dem Pololu D36V50F6 Spannungsregler.

```
3S-Akku (+12,6…9,0 V)
    │
   [Vin+] ── INA260 ── [Vin-]
    │                      │
    │               Pololu D36V50F6 → 6 V → Servos
    │               Buck → 5 V → RPi 5
    │               Buck → 3,3 V → ESP32-S3
    └──────── GND (gemeinsam)
```

### 9.2 Messbereich und Genauigkeit im AMR-Kontext

| Parameter | AMR-Betrieb | INA260-Bereich | Bemerkung |
|---|---|---|---|
| Busspannung | 9,0 V … 12,6 V | 0 V … 36 V | Weit innerhalb des Bereichs |
| Dauerstrom | 0,5 A … 3 A (typisch) | ±15 A | Auflösung: 1,25 mA, ausreichend |
| Spitzenstrom | bis 5 A (Motoranlauf) | ±15 A | Kurzzeitig bis 15 A zulässig |
| Leistung | 5 W … 35 W | 0 … 419 W | – |

### 9.3 Laufzeitberechnung mittels Coulomb-Zählung

Der INA260 eignet sich für eine vereinfachte Coulomb-Zählung (Stromintegration über die Zeit):

$$
Q_\text{verbraucht}(t) = \sum_{k=0}^{N} I_k \times \Delta t
$$

```c
static float consumed_mAh = 0.0f;
static int64_t last_time_us = 0;

void ina260_update_coulomb_counter(void) {
    int64_t now_us = esp_timer_get_time();
    float dt_h = (float)(now_us - last_time_us) / 3600e6f;
    last_time_us = now_us;

    float current_mA = ina260_read_current_mA();
    consumed_mAh += current_mA * dt_h;
}

float ina260_get_remaining_pct(float capacity_mAh) {
    float remaining = capacity_mAh - consumed_mAh;
    if (remaining < 0) remaining = 0;
    return (remaining / capacity_mAh) * 100.0f;
}
```

**Limitierung:** Eine reine Stromintegration driftet über die Zeit. Für höhere Genauigkeit empfiehlt sich eine periodische Korrektur anhand der OCV-SoC-Kennlinie (Open Circuit Voltage) des Akkupacks bei Lastpausen.

---

## 10 Induktive Lasten und Schutzmaßnahmen

**Warnung:** Bei der Überwachung induktiver Lasten (Motoren, Relais, Magnetventile) können Spannungsspitzen durch induktiven Rückstoß (Inductive Kickback) die Eingangsspannung des INA260 kurzzeitig weit über den Betriebsbereich von 36 V treiben und den Chip beschädigen.

Gegenmaßnahmen:

- Freilaufdioden (Flyback Diodes) direkt an der induktiven Last anbringen.
- TVS-Dioden (Transient Voltage Suppressors) am Eingang des INA260 platzieren.
- Snubber-Netzwerke (RC-Glied) bei schnell schaltenden Lasten.

Der INA260 kann kurzzeitige Überlastströme bis 100 A für weniger als 0,1 s überleben (laut Derating-Kurve), jedoch können Spannungsspitzen >40 V zu permanenten Schäden führen.

---

## 11 Vergleich mit verwandten Sensoren

| Parameter | INA260 | INA219 | INA226 |
|---|---|---|---|
| Integrierter Shunt | Ja (2 mΩ) | Nein (extern) | Nein (extern) |
| Kalibrierung nötig | Nein | Ja | Ja |
| Max. Busspannung | 36 V | 26 V | 36 V |
| Max. Dauerstrom | 15 A | Abhängig vom ext. Shunt | Abhängig vom ext. Shunt |
| Strom-LSB | 1,25 mA (fest) | Konfigurierbar (min. 0,1 mA) | Konfigurierbar |
| Spannungs-LSB | 1,25 mV | 4 mV | 1,25 mV |
| Leistungs-LSB | 10 mW (fest) | Konfigurierbar | Konfigurierbar |
| I²C-Adressen | 16 | 16 | 16 |
| Max. I²C-Takt | 2,94 MHz | 400 kHz | 2,94 MHz |
| Gehäuse | TSSOP-16 | SOT-23-8 | MSOP-10 |

**Konsequenz:** Der INA260 eignet sich besonders, wenn hohe Ströme (>1 A) bei minimaler PCB-Komplexität gemessen werden sollen. Der INA219 bietet bei kleinen Strömen (<1 A) mit geeignetem externem Shunt eine bessere Auflösung.

---

## 12 Sicherheitshinweise

- **Nur Gleichspannung (DC):** Der INA260 ist nicht für Wechselspannungsmessungen geeignet.
- **Maximale Eingangsspannung:** 36 V am Common-Mode-Eingang. Überspannungen >40 V verursachen permanente Schäden.
- **ESD-Schutz:** Der Chip ist empfindlich gegenüber elektrostatischer Entladung (HBM: ±2 kV, CDM: ±1 kV). ESD-Schutzmaßnahmen bei Handhabung und Einbau beachten.
- **Induktive Lasten:** Spannungsspitzen durch induktiven Rückstoß können den Chip zerstören. Schutzmaßnahmen gemäß Abschnitt 10 umsetzen.
- **Thermische Grenzen:** Bei 15 A Dauerstrom und $T_A = 85\,°\text{C}$ erreicht der Chip seine thermische Grenze. Ausreichende Kupferfläche (≥1 oz) auf der Platine sicherstellen.

---

## 13 Zusammenfassung der Schlüsselparameter

```
┌────────────────────────────────────────────────────────────────────┐
│   Adafruit INA260 Breakout (Art.-Nr. 4226) – Kurzprofil           │
├──────────────────────────┬─────────────────────────────────────────┤
│ Sensor-IC                │ TI INA260AIPWR (TSSOP-16)              │
│ Messgrössen              │ Strom, Spannung, Leistung (DC)         │
│ Integrierter Shunt       │ 2 mΩ, 0,1 % Toleranz-Äquivalent       │
│ Max. Busspannung         │ 36 V                                   │
│ Max. Dauerstrom          │ ±15 A (bis +85 °C)                     │
│ Strom-Auflösung          │ 1,25 mA / Bit                         │
│ Spannungs-Auflösung      │ 1,25 mV / Bit                         │
│ Leistungs-Auflösung      │ 10 mW / Bit                           │
│ Systemgenauigkeit Strom  │ 0,15 % (max., 25 °C)                  │
│ Systemgenauigkeit Spg.   │ 0,1 % (max., 25 °C)                   │
│ Strom-Offset             │ ±5 mA (max.)                           │
│ Schnittstelle            │ I²C / SMBus, bis 2,94 MHz              │
│ Adressen (Breakout)      │ 0x40, 0x41, 0x44, 0x45                │
│ Versorgungsspannung      │ 2,7 V … 5,5 V                         │
│ Ruhestrom                │ 310 µA (typ.), 0,5 µA (Shutdown)       │
│ Betriebstemperatur       │ −40 °C … +125 °C                       │
│ I²C-Pull-ups             │ 10 kΩ auf Breakout bestückt            │
│ Klemmenblock             │ 5,08 mm Rastermaß                      │
│ PCB-Abmessungen          │ ca. 25,4 mm × 17,8 mm                 │
└──────────────────────────┴─────────────────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2025-02-24 | Quellen: Texas Instruments INA260 Datenblatt SBOS656C Rev. C (Dezember 2016), Adafruit Learning Guide (Stand: März 2024), Adafruit Produktseite Art.-Nr. 4226*
