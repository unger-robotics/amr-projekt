# PCA9685 PWM-Servo-Treiber mit MG996R Servomotoren

> **Technische Dokumentation** – 16-Kanal-Servo-Steuerung für eingebettete Robotik  
> Treiber: NXP PCA9685 (16 Kanäle, 12-Bit-PWM, I²C)  
> Servomotor: TowerPro MG996R (Metallgetriebe, 2× im Einsatz)  
> Quellen: [NXP PCA9685 Datenblatt (PDF)](https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf), [TowerPro MG996R Spezifikation](https://towerpro.com.tw/product/mg996r/), [DigiKey MG996R Datasheet](https://www.digikey.com/en/htmldatasheets/production/5014637/0/0/1/mg996r), [Adafruit PCA9685 Breakout](https://www.adafruit.com/product/815)

---

## 1 Übersicht

Der PCA9685 ist ein I²C-gesteuerter 16-Kanal-PWM-Controller von NXP Semiconductors mit 12-Bit-Auflösung (4096 Stufen). Ursprünglich für LED-Dimmsteuerung entwickelt, eignet sich der Baustein durch seine programmierbare Ausgangsfrequenz (24 … 1526 Hz) hervorragend für die Ansteuerung von RC-Servomotoren bei 50 Hz. Für Servo-Anwendungen entlastet der PCA9685 den Host-Controller vollständig von der PWM-Erzeugung – nach einmaliger I²C-Konfiguration generiert der interne Oszillator die Signale autonom.

**Systemkonstellation in dieser Dokumentation:**

- **Treiber:** PCA9685-Breakout-Board (Adafruit-kompatibel)
- **Servos:** 2× TowerPro MG996R (Metallgetriebe, Hochdrehmoment)
- **Host-Controller:** ESP32-S3 (I²C-Master) oder Raspberry Pi 5
- **Anwendung:** Pan/Tilt-Einheit, Greifer oder Sensorplattform auf AMR

---

## 2 Komponentenspezifikationen

### 2.1 PCA9685 – PWM-Controller-IC

| Parameter | Wert | Bemerkung |
|---|---|---|
| **Hersteller** | NXP Semiconductors | Datenblatt Rev. 4, April 2015 |
| **Gehäuse** | TSSOP-28 / HVQFN-28 | – |
| **Versorgungsspannung (V~DD~)** | 2,3 … 5,5 V | IC-Logikversorgung |
| **I²C-Schnittstelle** | Fast-mode Plus (Fm+), bis 1 MHz | 5,5 V-tolerante Eingänge |
| **PWM-Kanäle** | 16 | Individuell programmierbar |
| **PWM-Auflösung** | 12 Bit (4096 Stufen) | Pro Kanal: ON- und OFF-Zähler |
| **PWM-Frequenzbereich** | 24 … 1526 Hz | Alle Kanäle gemeinsame Frequenz |
| **Interner Oszillator** | 25 MHz | Externer Takt bis 50 MHz möglich |
| **Ausgangstreiber (Totem-Pole)** | Sink: 25 mA, Source: 10 mA @ 5 V | Steuerstrom, nicht Servoleistung |
| **Open-Drain-Modus** | Optional (per Register) | – |
| **Output Enable (OE)** | Active Low | Globales Abschalten aller Ausgänge |
| **I²C-Basisadresse** | 0x40 | 6 Adresspins → bis 62 Boards kaskadierbar |
| **Adressbereich** | 0x40 … 0x7F | 62 nutzbare Adressen, 992 Kanäle |
| **POR-Zustand** | Alle Ausgänge LOW, Oszillator aus (Sleep) | – |
| **Ruhestrom (Sleep)** | Typisch 17 µA | Oszillator deaktiviert |
| **Betriebsstrom** | Typisch 10 mA | Ohne Last an den Ausgängen |
| **Betriebstemperatur** | −40 … +85 °C | Industriebereich |

### 2.2 PCA9685-Breakout-Board (Adafruit-kompatibel)

| Parameter | Wert |
|---|---|
| **IC** | PCA9685PW (TSSOP-28) |
| **Logikversorgung (V~DD~)** | 2,3 … 5,5 V (über I²C-Header) |
| **Servo-Versorgung (V+)** | Extern, über Schraubklemme (max. 6 V für Servos) |
| **I²C-Pullup-Widerstände** | 10 kΩ (on-board, per Jumper deaktivierbar) |
| **Schutzwiderstände** | 220 Ω in Serie an jedem PWM-Ausgang |
| **Stützkondensator V+** | Elektrolytkondensator (typisch 1000 µF) |
| **Servo-Anschlüsse** | 16× 3-Pin-Header (Signal, V+, GND) in 4er-Gruppen |
| **Adress-Jumper** | A0 … A5 (6 Lötpads) |
| **Kaskadierung** | I²C-Header auf beiden Seiten (Daisy-Chain) |
| **Abmessungen** | ca. 62,5 × 25,4 × 3 mm (ohne Header) |
| **Gewicht** | ca. 10 g (mit Headern und Schraubklemme) |

### 2.3 MG996R Servomotor (TowerPro Original)

| Parameter | @ 4,8 V | @ 6,0 V | Bemerkung |
|---|---|---|---|
| **Hersteller** | TowerPro | TowerPro | MG995-Nachfolger |
| **Typ** | Digital, Metallgetriebe | Digital, Metallgetriebe | 5× Metallzahnräder |
| **Blockiermoment (Stall Torque)** | 9,4 kg·cm | 11 kg·cm | Max. statisches Moment |
| **Leerlauf-Drehgeschwindigkeit** | 0,19 s / 60° | 0,15 s / 60° | Ohne Last |
| **Betriebsspannung** | 4,8 … 7,2 V | 4,8 … 7,2 V | Empfohlen: 5 … 6 V |
| **Leerlaufstrom** | ~10 mA | ~10 mA | Im Stillstand |
| **Betriebsstrom (Last)** | ~500 mA | ~900 mA | Typische Bewegung |
| **Blockierstrom (Stall)** | ~1,8 A | **~2,5 A** | **Kritisch für Versorgung!** |
| **Totband (Dead Band)** | 5 µs | 5 µs | Minimale Pulsänderung für Reaktion |
| **Stellbereich** | ~180° | ~180° | 90° in jede Richtung |
| **PWM-Frequenz** | 50 Hz | 50 Hz | Periodendauer 20 ms |
| **Pulsbreite (Neutralstellung)** | 1500 µs | 1500 µs | 0° / Mittelposition |
| **Pulsbreite (Bereich)** | 500 … 2500 µs | 500 … 2500 µs | −90° … +90° |
| **Kabelfarben** | Orange = PWM, Rot = V+, Braun = GND | | Universalstecker |
| **Lager** | Doppelkugellager | Doppelkugellager | Stoßfest |
| **Abmessungen** | 40,7 × 19,7 × 42,9 mm | | Standardgröße |
| **Gewicht** | 55 g | | Mit Kabel |
| **Kabellänge** | ca. 30 cm | | 3-Pin-Stecker (Futaba/JR kompatibel) |
| **Betriebstemperatur** | 0 … 55 °C | | – |

> **Hinweis Drehmoment-Angaben:** Im Markt existieren MG996R-Varianten mit abweichenden Spezifikationen (bis 15 kg·cm bei 6 V). Die Werte in dieser Dokumentation beziehen sich auf das TowerPro-Original. Klone können in Drehmoment, Strombedarf und Lebensdauer erheblich abweichen.

---

## 3 Servo-PWM-Grundlagen

### 3.1 Signalformat

Standard-RC-Servos erwarten ein pulsbreitenmoduliertes Signal mit 50 Hz Wiederholrate (20 ms Periodendauer). Die Position des Servohebels wird ausschließlich durch die Pulsbreite bestimmt, nicht durch das Tastverhältnis.

```
         Pulsbreite                     Pulsbreite
        ┌──────┐                       ┌──────────────┐
        │      │                       │              │
   ─────┘      └───────────────────────┘              └────────────
        │← t →│                        │←    t     →│
        │      │                       │              │
   ←────────── 20 ms ────────────────→ ←──── 20 ms ──────────────→
                (50 Hz)                        (50 Hz)

   t = 500 µs  →  −90° (links)       t = 2500 µs  →  +90° (rechts)
   t = 1500 µs →    0° (Mitte)
```

### 3.2 Pulsbreite ↔ Winkel (MG996R)

| Pulsbreite | Winkel | Tastverhältnis @ 50 Hz |
|---|---|---|
| 500 µs | −90° (ganz links) | 2,5 % |
| 1000 µs | −45° | 5,0 % |
| 1500 µs | 0° (Mittelstellung) | 7,5 % |
| 2000 µs | +45° | 10,0 % |
| 2500 µs | +90° (ganz rechts) | 12,5 % |

> **Praxishinweis:** Die mechanischen Endanschläge variieren von Exemplar zu Exemplar. Ein sicherer Bereich ist 600 … 2400 µs. Pulsbreiten jenseits der Endanschläge erzeugen ein Brummen (der Motor arbeitet gegen den Anschlag) und verkürzen die Lebensdauer erheblich.

### 3.3 Drehmoment-Hebelarm-Beziehung

Das Drehmoment $M$ des MG996R bezieht sich auf den Abstand von der Drehachse:

$$
F = \frac{M}{r}
$$

| Hebelarm $r$ | Tragkraft @ 4,8 V ($M = 9{,}4\,\text{kg·cm}$) | Tragkraft @ 6 V ($M = 11\,\text{kg·cm}$) |
|---|---|---|
| 1 cm | 9,4 kg | 11,0 kg |
| 2 cm | 4,7 kg | 5,5 kg |
| 3 cm | 3,1 kg | 3,7 kg |
| 5 cm | 1,9 kg | 2,2 kg |
| 10 cm | 0,94 kg | 1,1 kg |

---

## 4 PCA9685 – Registerarchitektur

### 4.1 PRE_SCALE-Register (Adresse 0xFE)

Der Prescaler bestimmt die PWM-Frequenz für alle 16 Kanäle. Die Berechnung basiert auf dem internen 25-MHz-Oszillator:

$$
\text{PRE\_SCALE} = \text{round}\!\left(\frac{f_\text{osc}}{4096 \times f_\text{PWM}}\right) - 1 = \text{round}\!\left(\frac{25\,000\,000}{4096 \times f_\text{PWM}}\right) - 1
$$

Für Servo-Betrieb mit $f_\text{PWM} = 50\,\text{Hz}$:

$$
\text{PRE\_SCALE} = \text{round}\!\left(\frac{25\,000\,000}{4096 \times 50}\right) - 1 = \text{round}(122{,}07) - 1 = 121
$$

| Zielfrequenz | PRE_SCALE | Tatsächliche Frequenz | Periodendauer |
|---|---|---|---|
| 50 Hz (Servos) | 121 (0x79) | 50,08 Hz | 19,97 ms |
| 60 Hz | 100 (0x64) | 60,27 Hz | 16,59 ms |
| 200 Hz (Default) | 29 (0x1D) | 210,5 Hz | 4,75 ms |
| 1000 Hz (LEDs) | 5 (0x05) | 1017 Hz | 0,98 ms |
| 1526 Hz (Max.) | 3 (0x03) | 1526 Hz | 0,66 ms |

> **Wichtig:** Der PRE_SCALE-Wert darf nur geschrieben werden, wenn das SLEEP-Bit in MODE1 gesetzt ist (Oszillator aus). Nach dem Schreiben muss der Oszillator wieder aktiviert und mindestens 500 µs gewartet werden, bevor PWM-Signale valide sind.

### 4.2 Kanal-Register (LEDn_ON / LEDn_OFF)

Jeder der 16 Kanäle besitzt vier Register (Adresse = 0x06 + 4 × n):

| Register | Adresse (Kanal 0) | Funktion |
|---|---|---|
| `LED0_ON_L` | 0x06 | Low-Byte: PWM-Zählerstand bei steigender Flanke |
| `LED0_ON_H` | 0x07 | High-Byte (Bits 0–3) + Full-ON (Bit 4) |
| `LED0_OFF_L` | 0x08 | Low-Byte: PWM-Zählerstand bei fallender Flanke |
| `LED0_OFF_H` | 0x09 | High-Byte (Bits 0–3) + Full-OFF (Bit 4) |

Der PCA9685 zählt bei jedem PWM-Zyklus von 0 bis 4095. Der Ausgang geht bei Erreichen von ON-Count auf HIGH und bei Erreichen von OFF-Count auf LOW. Für Servo-Ansteuerung setzt man typisch ON = 0 und variiert nur den OFF-Wert.

### 4.3 Pulsbreite ↔ Tick-Berechnung

Bei 50 Hz beträgt eine PWM-Periode 20 ms. Die 12-Bit-Auflösung (4096 Ticks) ergibt eine Zeitauflösung pro Tick von:

$$
t_\text{Tick} = \frac{20\,\text{ms}}{4096} \approx 4{,}88\,\mu\text{s}
$$

Umrechnung Pulsbreite → Tick-Wert (OFF-Register, bei ON = 0):

$$
\text{Ticks} = \text{round}\!\left(\frac{\text{Pulsbreite}}{t_\text{Tick}}\right) = \text{round}\!\left(\frac{\text{Pulsbreite (µs)} \times 4096}{20\,000}\right)
$$

| Pulsbreite | Ticks (OFF-Wert) | Winkel (MG996R) |
|---|---|---|
| 500 µs | 102 | −90° |
| 1000 µs | 205 | −45° |
| 1500 µs | 307 | 0° |
| 2000 µs | 410 | +45° |
| 2500 µs | 512 | +90° |

---

## 5 I²C-Adressierung und Kaskadierung

### 5.1 Adressschema

Die 7-Bit-I²C-Adresse setzt sich zusammen aus der festen Basis `1 0 0 0` und den sechs konfigurierbaren Bits A5 … A0:

```
  Bit:   6    5    4    3    2    1    0
       ┌────┬────┬────┬────┬────┬────┬────┐
       │  1 │  A5│  A4│  A3│  A2│  A1│  A0│
       └────┴────┴────┴────┴────┴────┴────┘
        fest  ← Lötpads auf Breakout-Board →
```

| Konfiguration | A5…A0 | Adresse (hex) |
|---|---|---|
| Alle offen (Default) | 000000 | 0x40 |
| A0 gebrückt | 000001 | 0x41 |
| A1 gebrückt | 000010 | 0x42 |
| A0 + A1 gebrückt | 000011 | 0x43 |
| Alle gebrückt | 111111 | 0x7F |

### 5.2 Reservierte Adressen

| Adresse | Funktion |
|---|---|
| 0x00 (General Call) | Software-Reset (SWRST) |
| 0x70 (All Call, Default) | Alle PCA9685 gleichzeitig ansprechen |
| 0x71, 0x72, 0x74 | Sub-Call-Adressen (programmierbar) |

---

## 6 Verdrahtung

### 6.1 ESP32-S3 → PCA9685 → 2× MG996R

```
                                                    Externes Netzteil
                                                    6 V / ≥ 5 A
                                                        │
ESP32-S3                PCA9685 Breakout                │
┌──────────┐           ┌───────────────────────┐        │
│          │           │                       │     ┌──┴──┐
│  3,3 V ──┼───────────┤ VCC (Logik)           │     │ V+  │ ← Schraubklemme
│   GND  ──┼─────┬─────┤ GND                   │     │ GND │
│          │     │     │                       │     └──┬──┘
│ GPIO 8 ──┼─────┼─SDA─┤ SDA        CH0 (PWM) ├──→ MG996R #1 (Orange)
│ GPIO 9 ──┼─────┼─SCL─┤ SCL        CH0 (V+)  ├──→ MG996R #1 (Rot)
│          │     │     │           CH0 (GND) ├──→ MG996R #1 (Braun)
│          │     │     │                       │
│          │     │     │           CH1 (PWM) ├──→ MG996R #2 (Orange)
│          │     │     │           CH1 (V+)  ├──→ MG996R #2 (Rot)
│          │     │     │           CH1 (GND) ├──→ MG996R #2 (Braun)
│          │     │     │                       │
│          │     │     │           OE ─────────┤ → GND (oder GPIO für Disable)
└──────────┘     │     └───────────────────────┘
                 │
                GND (gemeinsame Masse!)
```

### 6.2 Raspberry Pi 5 → PCA9685

| PCA9685 Pin | Raspberry Pi Pin | Signal |
|---|---|---|
| VCC | Pin 1 | 3,3 V (Logik) |
| GND | Pin 6 | GND |
| SDA | Pin 3 | GPIO 2 (I2C1 SDA) |
| SCL | Pin 5 | GPIO 3 (I2C1 SCL) |
| V+ (Klemme) | – | Externes Netzteil 6 V |
| GND (Klemme) | – | Externes Netzteil GND + Pi GND |

### 6.3 Kritische Verdrahtungsregeln

1. **Separate Servo-Versorgung zwingend erforderlich.** Die MG996R-Servos dürfen nicht über den 5-V-Pin des Mikrocontrollers versorgt werden. Zwei MG996R im Blockierzustand ziehen bis zu 5 A – das übersteigt die Belastbarkeit jedes Entwicklerboards.

2. **Gemeinsame Masse (GND).** Das externe Netzteil, der PCA9685 und der Mikrocontroller müssen eine gemeinsame Masseleitung teilen. Fehlende GND-Verbindung führt zu undefiniertem Verhalten bis hin zur Zerstörung des PCA9685.

3. **OE-Pin.** Der Output-Enable-Pin ist Active-Low. Standardmäßig auf GND (= Ausgänge aktiv). Für Not-Aus kann der Pin über einen GPIO auf HIGH gezogen werden, um alle 16 Kanäle sofort abzuschalten.

---

## 7 Stromversorgung – Dimensionierung

### 7.1 Worst-Case-Berechnung (2× MG996R @ 6 V)

| Zustand | Strom pro Servo | 2× Servos | Bemerkung |
|---|---|---|---|
| Leerlauf (idle, gehalten) | ~10 mA | ~20 mA | Servo hält Position |
| Typische Bewegung | ~500 mA | ~1 A | Normale Last |
| Hohe Last | ~900 mA | ~1,8 A | Nahe Blockierung |
| **Blockierung (Stall)** | **~2,5 A** | **~5 A** | **Dimensionierungsbasis** |

### 7.2 Netzteil-Anforderungen

$$
P_\text{max} = 2 \times I_\text{Stall} \times V = 2 \times 2{,}5\,\text{A} \times 6\,\text{V} = 30\,\text{W}
$$

**Empfohlenes Netzteil:** 6 V / 5 A (30 W), stabilisiert, mit ausreichender Stromreserve. Bei Akku-Betrieb eignet sich ein 2S-LiPo (7,4 V nominal) mit einem 6-V-BEC (Battery Eliminator Circuit) oder Schaltregler.

### 7.3 Stützkondensatoren

Das PCA9685-Breakout-Board enthält einen Elektrolytkondensator am V+-Anschluss. Für den Betrieb mit Hochdrehmoment-Servos empfiehlt sich zusätzlich:

- **1000 µF / 10 V Elektrolyt** direkt an der V+-Schraubklemme (bereits on-board bei den meisten Boards)
- **100 nF Keramik** nahe an jedem Servoanteil (bei langen Kabeln)

Ohne ausreichende Pufferung verursachen die Stromschwankungen der Servos Spannungseinbrüche, die zu Servo-Jitter, I²C-Kommunikationsfehlern und Mikrocontroller-Resets führen können.

---

## 8 Firmware – ESP32-S3 (ESP-IDF v5.x)

### 8.1 I²C-Master-Initialisierung

```c
#include "driver/i2c_master.h"
#include "esp_log.h"

#define I2C_SDA_PIN         GPIO_NUM_8
#define I2C_SCL_PIN         GPIO_NUM_9
#define PCA9685_ADDR        0x40
#define PCA9685_FREQ_HZ     50

/* Register */
#define PCA9685_MODE1       0x00
#define PCA9685_PRESCALE    0xFE
#define PCA9685_LED0_ON_L   0x06

static i2c_master_bus_handle_t  bus_handle;
static i2c_master_dev_handle_t  pca_handle;

esp_err_t pca9685_i2c_init(void)
{
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port   = I2C_NUM_0,
        .sda_io_num = I2C_SDA_PIN,
        .scl_io_num = I2C_SCL_PIN,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus_handle));

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = PCA9685_ADDR,
        .scl_speed_hz    = 400000,  /* 400 kHz Fast-mode */
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &pca_handle));
    return ESP_OK;
}
```

### 8.2 Register-Zugriff (Helfer)

```c
static esp_err_t pca9685_write_reg(uint8_t reg, uint8_t value)
{
    uint8_t buf[2] = { reg, value };
    return i2c_master_transmit(pca_handle, buf, 2, 100);
}

static esp_err_t pca9685_read_reg(uint8_t reg, uint8_t *value)
{
    esp_err_t err = i2c_master_transmit(pca_handle, &reg, 1, 100);
    if (err != ESP_OK) return err;
    return i2c_master_receive(pca_handle, value, 1, 100);
}
```

### 8.3 PCA9685-Initialisierung (50 Hz)

```c
esp_err_t pca9685_init(void)
{
    /* Reset */
    pca9685_write_reg(PCA9685_MODE1, 0x00);
    vTaskDelay(pdMS_TO_TICKS(5));

    /* Sleep-Modus aktivieren (Prescaler nur im Sleep beschreibbar) */
    uint8_t mode1;
    pca9685_read_reg(PCA9685_MODE1, &mode1);
    pca9685_write_reg(PCA9685_MODE1, (mode1 & 0x7F) | 0x10);  /* SLEEP = 1 */

    /* Prescaler für 50 Hz setzen:
       PRE_SCALE = round(25.000.000 / (4096 × 50)) − 1 = 121 */
    pca9685_write_reg(PCA9685_PRESCALE, 121);

    /* Sleep beenden */
    pca9685_write_reg(PCA9685_MODE1, mode1);
    vTaskDelay(pdMS_TO_TICKS(1));  /* ≥500 µs warten */

    /* Auto-Increment aktivieren, RESTART */
    pca9685_write_reg(PCA9685_MODE1, mode1 | 0xA0);
    return ESP_OK;
}
```

### 8.4 Servo-Position setzen

```c
/**
 * @brief Setzt einen Servo-Kanal auf die angegebene Pulsbreite.
 *
 * @param channel  Kanal 0 … 15
 * @param pulse_us Pulsbreite in Mikrosekunden (500 … 2500)
 */
esp_err_t pca9685_set_servo(uint8_t channel, uint16_t pulse_us)
{
    if (channel > 15 || pulse_us < 500 || pulse_us > 2500) {
        return ESP_ERR_INVALID_ARG;
    }

    /* Ticks berechnen: ticks = pulse_us × 4096 / 20000 */
    uint16_t ticks = (uint16_t)((uint32_t)pulse_us * 4096 / 20000);

    uint8_t reg = PCA9685_LED0_ON_L + 4 * channel;
    uint8_t buf[5] = {
        reg,
        0x00,                    /* ON_L  = 0 */
        0x00,                    /* ON_H  = 0 */
        (uint8_t)(ticks & 0xFF), /* OFF_L */
        (uint8_t)(ticks >> 8),   /* OFF_H */
    };
    return i2c_master_transmit(pca_handle, buf, 5, 100);
}

/**
 * @brief Setzt einen Servo-Kanal auf den angegebenen Winkel.
 *
 * @param channel  Kanal 0 … 15
 * @param angle    Winkel in Grad (0 … 180)
 */
esp_err_t pca9685_set_angle(uint8_t channel, float angle)
{
    if (angle < 0.0f) angle = 0.0f;
    if (angle > 180.0f) angle = 180.0f;
    uint16_t pulse_us = (uint16_t)(500.0f + (angle / 180.0f) * 2000.0f);
    return pca9685_set_servo(channel, pulse_us);
}
```

### 8.5 Alle Servos abschalten (Strom sparen)

```c
esp_err_t pca9685_all_off(void)
{
    /* ALL_LED_OFF_H (0xFD), Bit 4 = 1 → alle Kanäle sofort aus */
    return pca9685_write_reg(0xFD, 0x10);
}
```

### 8.6 Anwendungsbeispiel (Pan/Tilt)

```c
#define PAN_CHANNEL   0
#define TILT_CHANNEL  1

void servo_demo_task(void *arg)
{
    pca9685_i2c_init();
    pca9685_init();

    /* Beide Servos in Mittelstellung */
    pca9685_set_angle(PAN_CHANNEL, 90.0f);
    pca9685_set_angle(TILT_CHANNEL, 90.0f);
    vTaskDelay(pdMS_TO_TICKS(1000));

    /* Sweep Pan-Servo */
    for (float angle = 0; angle <= 180; angle += 1.0f) {
        pca9685_set_angle(PAN_CHANNEL, angle);
        vTaskDelay(pdMS_TO_TICKS(20));  /* 20 ms = ein PWM-Zyklus */
    }

    /* Tilt auf 45° */
    pca9685_set_angle(TILT_CHANNEL, 45.0f);

    /* Servos abschalten (Strom sparen) */
    vTaskDelay(pdMS_TO_TICKS(2000));
    pca9685_all_off();

    vTaskDelete(NULL);
}
```

---

## 9 Firmware – Raspberry Pi 5 (Python)

### 9.1 Installation

```bash
# I2C aktivieren (falls nicht bereits geschehen)
sudo raspi-config  # → Interface Options → I2C → Enable

# Bibliotheken installieren
pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit \
    --break-system-packages
```

### 9.2 I²C-Gerät prüfen

```bash
sudo i2cdetect -y 1
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

### 9.3 Servo-Steuerung mit ServoKit

```python
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

# Pulsbreiten-Bereich kalibrieren (MG996R)
kit.servo[0].set_pulse_width_range(500, 2500)
kit.servo[1].set_pulse_width_range(500, 2500)

# Winkel setzen (0 … 180)
kit.servo[0].angle = 90   # Pan: Mittelstellung
kit.servo[1].angle = 45   # Tilt: 45°

# Auf bestimmte Pulsbreite setzen
kit.servo[0].angle = None  # Servo deaktivieren (kein PWM-Signal)
```

### 9.4 Low-Level-Zugriff (PCA9685 direkt)

```python
import board
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50  # Hz

# Kanal 0: Pulsbreite 1500 µs (Mittelstellung)
# duty_cycle = pulse_us / 20000 * 0xFFFF
pca.channels[0].duty_cycle = int(1500 / 20000 * 0xFFFF)

# Alle Kanäle aus
pca.reset()
pca.deinit()
```

---

## 10 ROS 2-Integration

### 10.1 Systemarchitektur

```
Raspberry Pi 5 (ROS 2 Humble)
    │
    I²C (GPIO 2/3) ──── PCA9685 ──┬── CH0: MG996R (Pan)
    │                              └── CH1: MG996R (Tilt)
    │
    ├── /servo/pan   (std_msgs/Float64)  → Pan-Winkel (0 … 180)
    ├── /servo/tilt  (std_msgs/Float64)  → Tilt-Winkel (0 … 180)
    └── /servo/cmd   (sensor_msgs/JointState) → Mehrkanal-Steuerung
```

### 10.2 Servo-Node (Python-Beispiel)

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from adafruit_servokit import ServoKit


class ServoDriverNode(Node):
    def __init__(self):
        super().__init__('servo_driver')
        self.kit = ServoKit(channels=16)
        self.kit.servo[0].set_pulse_width_range(500, 2500)
        self.kit.servo[1].set_pulse_width_range(500, 2500)

        self.create_subscription(Float64, '/servo/pan',  self.pan_cb,  10)
        self.create_subscription(Float64, '/servo/tilt', self.tilt_cb, 10)
        self.get_logger().info('Servo driver ready (PCA9685 @ 0x40)')

    def pan_cb(self, msg):
        angle = max(0.0, min(180.0, msg.data))
        self.kit.servo[0].angle = angle

    def tilt_cb(self, msg):
        angle = max(0.0, min(180.0, msg.data))
        self.kit.servo[1].angle = angle


def main():
    rclpy.init()
    node = ServoDriverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### 10.3 Test

```bash
# Pan auf 90°
ros2 topic pub --once /servo/pan std_msgs/Float64 "{data: 90.0}"

# Tilt auf 45°
ros2 topic pub --once /servo/tilt std_msgs/Float64 "{data: 45.0}"
```

---

## 11 Kalibrierung

### 11.1 Pulsbreiten-Kalibrierung (MG996R)

Die theoretischen Werte 500 … 2500 µs stimmen nicht bei jedem Exemplar exakt. Eine empirische Kalibrierung verbessert die Positioniergenauigkeit.

**Vorgehen:**

1. Servo auf 1500 µs setzen → Hebel muss exakt in der Mitte stehen.
2. Pulsbreite schrittweise reduzieren (ab 600 µs), bis der Servo den mechanischen Anschlag bei −90° erreicht (leises Summen/Brummen). Diesen Wert als `PULSE_MIN` notieren.
3. Pulsbreite schrittweise erhöhen (ab 2400 µs), bis der Servo den Anschlag bei +90° erreicht. Diesen Wert als `PULSE_MAX` notieren.
4. 20 … 30 µs Sicherheitsabstand zu beiden Endanschlägen einhalten.

### 11.2 Oszillator-Kalibrierung (PCA9685)

Der interne 25-MHz-Oszillator des PCA9685 hat eine Toleranz von ±3 %. Bei einem Exemplar kann die tatsächliche Frequenz z. B. 25,3 MHz betragen, was die PWM-Frequenz leicht verfälscht. Für präzise Servo-Steuerung kann die tatsächliche Oszillatorfrequenz gemessen und in der Software kompensiert werden.

**Messung mit Oszilloskop:**

1. PCA9685 auf 50 Hz konfigurieren (PRE_SCALE = 121).
2. Frequenz an einem Ausgangskanal mit dem Oszilloskop messen.
3. Falls die gemessene Frequenz $f_\text{ist}$ ≠ 50 Hz: Korrektur-Oszillatorfrequenz berechnen.

$$
f_\text{osc,real} = f_\text{osc,nominal} \times \frac{f_\text{ist}}{f_\text{soll}} = 25\,000\,000 \times \frac{f_\text{ist}}{50}
$$

In der Adafruit-Python-Bibliothek:

```python
pca = PCA9685(i2c, reference_clock_speed=25_300_000)  # Korrigiert
```

---

## 12 Design-Richtlinien

### 12.1 Spannungsversorgung

- Servo-V+ und Logik-VCC stets von getrennten Quellen speisen oder zumindest mit LC-Filter entkoppeln.
- Kabelquerschnitt für Servo-Versorgung: mindestens 0,5 mm² (AWG 20) bei Kabellängen >20 cm.
- Spannungseinbrüche >0,5 V an V+ führen zu Servo-Jitter. Stützkondensatoren (1000 µF + 100 nF) nahe am PCA9685-Board platzieren.

### 12.2 I²C-Bus

- Pullup-Widerstände: 4,7 kΩ bei 3,3-V-Logik, 2,2 kΩ bei langen Leitungen (>30 cm).
- Kabellänge für zuverlässigen I²C-Betrieb: maximal 1 m (bei 100 kHz), maximal 30 cm (bei 400 kHz).
- Bei mehreren I²C-Geräten: Gesamtkapazität des Bus beachten (max. 400 pF für Fm+).

### 12.3 Servo-Lebensdauer

- Dauerbetrieb unter Blockierbedingungen vermeidet der MG996R durch keinen eingebauten Schutz. Der Stall-Strom fließt unbegrenzt und überhitzt Motor und Getriebe.
- Software-seitiges Timeout implementieren: Falls ein Servo seine Zielposition nach 2 Sekunden nicht erreicht, PWM abschalten (`pca9685_all_off()`).
- Bewegungen mit Rampen (sanftes Anfahren/Bremsen) reduzieren mechanische Belastung und Stromspitzen.

### 12.4 EMV

- Servo-Motoren erzeugen hochfrequente Störungen durch die interne H-Brücke. Keramik-Abblockkondensatoren (100 nF) direkt am Motorgehäuse können das Rauschen reduzieren.
- I²C-Leitungen nicht parallel zu Servo-Versorgungsleitungen führen.

---

## 13 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| `i2cdetect` zeigt keine Adresse | Kabel vertauscht oder lose | SDA/SCL prüfen, Pullups verifizieren |
| PCA9685 auf 0x70 statt 0x40 | All-Call-Adresse wird erkannt | Normal – 0x40 ist die Geräteadresse |
| Servos bewegen sich nicht | V+ nicht angeschlossen | Externe Stromversorgung an Schraubklemme |
| Servos bewegen sich nicht | OE-Pin auf HIGH | OE mit GND verbinden |
| Servos bewegen sich nicht | PRE_SCALE nicht gesetzt (noch 200 Hz) | Initialisierung prüfen (Sleep → Prescale → Wake) |
| Servo zittert (Jitter) | Spannungseinbrüche an V+ | Stützkondensatoren, dickere Kabel, stärkeres Netzteil |
| Servo zittert | I²C-Störungen | SDA/SCL von Motorleitungen räumlich trennen |
| Servo brummt am Endanschlag | Pulsbreite jenseits des mechanischen Bereichs | `PULSE_MIN` / `PULSE_MAX` kalibrieren |
| Servo bewegt sich ruckartig | Zu große Winkelsprünge | Rampen-Funktion implementieren (1°/20 ms) |
| Servo wird heiß | Dauerhafter Blockierzustand | Software-Timeout, Last reduzieren, Servo-Off |
| I²C-Kommunikation bricht ab | Servo-Stromspitzen stören I²C | Separate Masse-Rückführung, Ferritkerne auf I²C |
| PWM-Frequenz stimmt nicht | Oszillator-Toleranz (±3 %) | Mit Oszilloskop messen, `reference_clock_speed` anpassen |
| Adresse kollidiert bei Kaskade | Gleiche Adress-Jumper auf zwei Boards | Eindeutige A0–A5-Konfiguration pro Board |

---

## 14 Vergleich mit alternativen Servo-Treibern

| Parameter | PCA9685 (I²C) | ESP32-S3 LEDC (direkt) | TB6612 + PWM | MCP23017 + SW-PWM |
|---|---|---|---|---|
| Kanäle | 16 | 8 (LEDC-Timer) | 2 (H-Brücke) | 16 (GPIO, kein HW-PWM) |
| PWM-Auflösung | 12 Bit (4096) | 14 Bit (16384) | Abhängig von PWM-Quelle | Software, instabil |
| Servo-taugliche PWM | Ja (50 Hz, autonom) | Ja, aber belegt GPIOs | Nein (für DC-Motoren) | Nein |
| I²C-Steuerung | Ja | Nein (direkte GPIO) | Nein | Ja (aber kein HW-PWM) |
| Kaskadierung | Bis 62 Boards (992 Kanäle) | Nicht kaskadierbar | Nicht kaskadierbar | Bis 8 Boards |
| CPU-Last | Keine (autonom nach Config) | Gering (LEDC-Hardware) | Gering | Hoch (Software-Timing) |
| Jitter | < 1 µs (HW-Oszillator) | < 1 µs (HW-Timer) | N/A | 10–100 µs (SW) |
| Preis (Board) | ~3–6 € | Inklusive (ESP32-S3) | ~2–4 € | ~2–4 € |

**Für AMR-Anwendungen mit >2 Servos** bietet der PCA9685 den besten Kompromiss: autonome PWM-Erzeugung, keine GPIO-Belegung, einfache Kaskadierung und geringste CPU-Last.

---

## 15 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   Servo-System: PCA9685 + 2× MG996R – Kurzprofil                       │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   PWM-TREIBER (PCA9685)      │                                           │
│   Hersteller / IC            │ NXP PCA9685PW                             │
│   Kanäle                     │ 16                                        │
│   PWM-Auflösung              │ 12 Bit (4096 Stufen)                     │
│   Frequenzbereich            │ 24 … 1526 Hz                             │
│   Servo-Frequenz             │ 50 Hz (PRE_SCALE = 121)                  │
│   Zeitauflösung @ 50 Hz     │ 4,88 µs / Tick                           │
│   Oszillator                 │ 25 MHz intern (±3 %)                     │
│   I²C-Adresse (Default)     │ 0x40                                      │
│   I²C-Geschwindigkeit        │ Bis 1 MHz (Fm+)                          │
│   Logikversorgung            │ 2,3 … 5,5 V                             │
│   Kaskadierung               │ Bis 62 Boards (992 Kanäle)              │
│                              │                                           │
│   SERVOMOTOR (MG996R × 2)    │                                           │
│   Hersteller                 │ TowerPro                                  │
│   Blockiermoment             │ 9,4 kg·cm (4,8 V) / 11 kg·cm (6 V)     │
│   Geschwindigkeit            │ 0,19 s/60° (4,8 V) / 0,15 s/60° (6 V)  │
│   Stellbereich               │ ~180°                                    │
│   Pulsbreite                 │ 500 … 2500 µs (50 Hz)                   │
│   Blockierstrom              │ 2,5 A @ 6 V (pro Servo!)                │
│   Getriebe                   │ 5× Metallzahnräder, Doppelkugellager    │
│   Abmessungen                │ 40,7 × 19,7 × 42,9 mm, 55 g            │
│                              │                                           │
│   SYSTEM                     │                                           │
│   Versorgung (2× Servo)      │ 6 V / ≥ 5 A (extern, stabilisiert)     │
│   Max. Leistung (Stall)      │ 30 W (2× 2,5 A × 6 V)                  │
│   Plattformen                │ ESP32-S3, Raspberry Pi, Arduino          │
│   ROS 2 Integration          │ /servo/pan, /servo/tilt Topics           │
│   Kalibrierung               │ Empirisch (Pulsbreite + Oszillator)     │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 16 Ressourcen

| Typ | Link |
|---|---|
| NXP PCA9685 Datenblatt (PDF, Rev. 4) | [cdn-shop.adafruit.com/datasheets/PCA9685.pdf](https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf) |
| TowerPro MG996R Produktseite | [towerpro.com.tw/product/mg996r/](https://towerpro.com.tw/product/mg996r/) |
| DigiKey MG996R Datasheet | [digikey.com/…/mg996r](https://www.digikey.com/en/htmldatasheets/production/5014637/0/0/1/mg996r) |
| Adafruit PCA9685 Breakout | [adafruit.com/product/815](https://www.adafruit.com/product/815) |
| Adafruit CircuitPython PCA9685 Library | [github.com/adafruit/Adafruit_CircuitPython_PCA9685](https://github.com/adafruit/Adafruit_CircuitPython_PCA9685) |
| Adafruit PWM Servo Driver Library (Arduino) | [github.com/adafruit/Adafruit-PWM-Servo-Driver-Library](https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library) |
| ESP-IDF PCA9685 Beispiel (kimsniper) | [github.com/kimsniper/PCA9685](https://github.com/kimsniper/PCA9685) |
| ESP32 PCA9685 Library (brainelectronics) | [github.com/brainelectronics/esp32-pca9685](https://github.com/brainelectronics/esp32-pca9685) |
| DroneBot Workshop: ESP32 + Servo | [dronebotworkshop.com/esp32-servo/](https://dronebotworkshop.com/esp32-servo/) |
| Components101: MG996R | [components101.com/motors/mg996r-servo-motor-datasheet](https://components101.com/motors/mg996r-servo-motor-datasheet) |

---

*Dokumentversion: 1.1 | Datum: 2026-02-27 | Änderung: Stellzeiten auf TowerPro-Originalwerte korrigiert (0,19/0,15 s statt 0,17/0,14 s) | Quellen: NXP PCA9685 Datasheet Rev. 4 (2015), TowerPro MG996R Spezifikation (towerpro.com.tw), DigiKey MG996R Datasheet, Adafruit PCA9685 Breakout Dokumentation, Adafruit CircuitPython PCA9685/ServoKit Libraries, ESP-IDF I²C Master API, DroneBot Workshop ESP32 Servo Tutorial*
