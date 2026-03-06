# Adafruit MAX98357A I2S-Verstärker und ADA3351 Mono-Gehäuselautsprecher

> **Technische Dokumentation** – Audiosystem für eingebettete Projekte  
> Verstärker: Adafruit I2S 3W Class D Amplifier Breakout (Art.-Nr. 3006)  
> Lautsprecher: Adafruit Mono Enclosed Speaker 3 W / 4 Ω (Art.-Nr. 3351)  
> Verstärker-IC: Maxim (Analog Devices) MAX98357A  
> Quellen: [Adafruit Learning Guide](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp), [MAX98357A Datenblatt](https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf), [Adafruit Produktseite 3006](https://www.adafruit.com/product/3006), [Adafruit Produktseite 3351](https://www.adafruit.com/product/3351)

---

## 1 Übersicht

Das Adafruit MAX98357A Breakout kombiniert einen I²S-DAC (Digital-Analog-Wandler) und einen Class-D-Leistungsverstärker in einem einzigen Modul. Der Chip empfängt digitale Audiodaten im I²S-Format und treibt direkt einen Lautsprecher an – ohne externen DAC oder analogen Vorverstärker. In Verbindung mit dem Gehäuselautsprecher ADA3351 (3 W, 4 Ω) ergibt sich ein kompaktes, kostengünstiges Audiosystem für Sprachausgabe, Warntöne und Medienwiedergabe in eingebetteten Systemen.

**Schlüsseleigenschaften des Gesamtsystems:**

- Rein digitale Signalkette: I²S-Daten → DAC → Class-D-Verstärker → Lautsprecher
- Kein MCLK-Signal erforderlich – vereinfacht die Anbindung an Mikrocontroller
- Plug-and-Play mit ESP32-S3, Raspberry Pi und anderen I²S-fähigen Plattformen
- Automatische Erkennung von bis zu 35 verschiedenen PCM/TDM-Taktschemen
- Integrierter Überstrom- und Übertemperaturschutz
- Gesamtkosten unter 10 € (Verstärker + Lautsprecher)

---

## 2 Komponentenspezifikationen

### 2.1 Verstärker-IC: MAX98357A

| Parameter | Wert | Bedingung |
|---|---|---|
| **Hersteller** | Maxim Integrated (jetzt Analog Devices) | – |
| **Typ** | PCM-Input Class-D Audio-Leistungsverstärker | – |
| **Versorgungsspannung** $V_\text{DD}$ | 2,5 … 5,5 V | Einzelversorgung |
| **Ausgangsleistung (4 Ω)** | 3,2 W | $V_\text{DD} = 5\,\text{V}$, THD+N = 10 % |
| **Ausgangsleistung (4 Ω)** | 2,5 W | $V_\text{DD} = 5\,\text{V}$, THD+N = 1 % |
| **Ausgangsleistung (8 Ω)** | 1,8 W | $V_\text{DD} = 5\,\text{V}$, THD+N = 10 % |
| **Ausgangsleistung (8 Ω)** | 1,4 W | $V_\text{DD} = 5\,\text{V}$, THD+N = 1 % |
| **Ausgangsleistung (4 Ω)** | 1,3 W | $V_\text{DD} = 3{,}3\,\text{V}$, THD+N = 10 % |
| **Ausgangsleistung (4 Ω)** | 1,0 W | $V_\text{DD} = 3{,}3\,\text{V}$, THD+N = 1 % |
| **THD+N** | 0,02 % | $f = 1\,\text{kHz}$, $P_\text{out} = 1\,\text{W}$, 4 Ω |
| **THD+N** | 0,013 % | $f = 1\,\text{kHz}$, $P_\text{out} = 0{,}5\,\text{W}$, 8 Ω |
| **Dynamikumfang** | 105 dB | A-bewertet, 24/32-Bit-Daten |
| **Ausgangsrauschen** | 25 µV (RMS) | A-bewertet, 24/32-Bit-Daten |
| **PSRR** | 77 dB (typ.) | $f = 1\,\text{kHz}$ |
| **Wirkungsgrad** | 92 % | 8 Ω, THD+N = 10 %, 12 dB Gain |
| **Abtastraten** | 8 … 96 kHz | Automatische Erkennung |
| **Bitauflösung** | 16 / 32 Bit | – |
| **Audio-Interface** | I²S (MAX98357A) / Left-Justified (MAX98357B) | + 8-Kanal-TDM |
| **MCLK** | Nicht erforderlich | – |
| **Ruhestrom** $I_\text{Q}$ | 2,4 mA (typ.) | – |
| **Shutdown-Strom** | 10 µA (typ.) | SD\_MODE = Low |
| **Class-D-Schaltfrequenz** | 330 kHz | Spread Spectrum ±12,5 kHz |
| **Ausgangsart** | BTL (Bridge-Tied Load) | Filterloser Ausgang, ~300 kHz PWM |
| **Click/Pop-Unterdrückung** | Integriert | – |
| **Schutzfunktionen** | Thermischer Shutdown + Überstromschutz + Kurzschlussschutz | – |
| **Logikpegel (Eingänge)** | 3,3 V oder 5 V | – |
| **Gehäuse (IC)** | 9-bump WLP / TQFN | – |
| **Betriebstemperatur** | −40 … +85 °C | – |

### 2.2 Adafruit Breakout-Board (Art.-Nr. 3006)

| Parameter | Wert |
|---|---|
| **PCB-Abmessungen** | ca. 27 × 18 mm (1,05" × 0,7") |
| **Anschlüsse** | 7-Pin Header + 2-Pin Schraubklemme (3,5 mm) |
| **Vorkonfiguriert** | SD\_MODE: 1 MΩ Pullup zu Vin → Stereo-Mix (L+R)/2 bei 5 V |
| **Gain-Voreinstellung** | 9 dB (GAIN-Pin offen) |
| **Lieferumfang** | Bestücktes Board, Stiftleiste (optional), Schraubklemme (vorgelötet) |

### 2.3 Lautsprecher: ADA3351

| Parameter | Wert |
|---|---|
| **Hersteller** | Adafruit Industries |
| **Art.-Nr.** | 3351 |
| **Impedanz** | 4 Ω |
| **Belastbarkeit** | 3 W (max.) |
| **Bauform** | Gehäuselautsprecher (enclosed), oval |
| **Abmessungen** | 70 × 30 × 17 mm (2,8" × 1,2" × 0,7") |
| **Gewicht** | 26,4 g |
| **Anschluss** | JST-PH 2-Pin (2,0 mm Rastermaß), Kabellänge ca. 57 cm |
| **Befestigung** | 2 × Bohrungen ∅ 3,4 mm (±20 %) |
| **Anwendung** | Sprachausgabe, Warntöne, Medienwiedergabe |

---

## 3 I²S-Protokoll – Grundlagen

### 3.1 Signalüberblick

I²S (Inter-IC Sound) ist ein serielles, synchrones Protokoll zur Übertragung digitaler Audiodaten zwischen integrierten Schaltungen. Der MAX98357A arbeitet als I²S-Slave und empfängt drei Signale vom Host-Controller (Master):

```
                I²S-Master                       I²S-Slave
              (ESP32-S3)                       (MAX98357A)
            ┌────────────┐                   ┌────────────┐
            │            │── BCLK ──────────►│            │
            │            │── LRCLK (WS) ────►│            │── OUTP ──┐
            │    I²S     │── DIN ───────────►│   DAC +    │          ├── Lautsprecher
            │    TX      │                   │   Class D  │── OUTN ──┘
            │            │                   │            │
            └────────────┘                   └────────────┘
```

| Signal | Alternativname | Funktion |
|---|---|---|
| **BCLK** | SCK, Bit Clock | Taktsignal für jedes Datenbit |
| **LRCLK** | WS, Word Select | Kanalauswahl: Low = linker Kanal, High = rechter Kanal |
| **DIN** | SD, Serial Data | Serieller Datenstrom, MSB first |

### 3.2 Taktbeziehung

$$
f_\text{BCLK} = f_\text{LRCLK} \times \text{Bits pro Kanal} \times 2\;\text{Kanäle}
$$

Beispiel bei 16 Bit, 44,1 kHz:

$$
f_\text{BCLK} = 44{.}100 \times 16 \times 2 = 1{,}4112\,\text{MHz}
$$

Der MAX98357A erkennt automatisch bis zu 35 verschiedene Kombinationen aus Abtastrate und Bittiefe. Ein MCLK-Signal wird nicht benötigt – der Chip leitet den internen Takt ausschließlich aus BCLK und LRCLK ab.

---

## 4 Pinbelegung (Breakout-Board)

### 4.1 Pinbeschreibung

| Pin | Funktion | Beschreibung |
|---|---|---|
| **Vin** | Versorgung | 2,5 … 5,5 V DC. 5 V empfohlen für maximale Ausgangsleistung |
| **GND** | Masse | Gemeinsame Masse mit Host-System |
| **BCLK** | Bit Clock | I²S-Bittakt vom Master. 3,3 V oder 5 V Logik |
| **LRC** | Left/Right Clock | I²S-Kanalauswahl (LRCLK / WS). 3,3 V oder 5 V Logik |
| **DIN** | Data In | I²S-Seriendaten. 3,3 V oder 5 V Logik |
| **GAIN** | Verstärkungseinstellung | Siehe Abschnitt 5.1 |
| **SD** | Shutdown / Mode | Siehe Abschnitt 5.2 |
| **+** / **−** | Lautsprecherausgang | BTL-Ausgang, über Schraubklemme (3,5 mm Raster) |

### 4.2 Bestückung und Anschlüsse

```
    Header-Seite (7 Pins)          Schraubklemme (2 Pins)
    ┌─────────────────┐            ┌─────────────┐
    │ Vin              │            │ Speaker +   │
    │ GND              │            │ Speaker −   │
    │ SD               │            └─────────────┘
    │ GAIN             │
    │ DIN              │
    │ BCLK             │
    │ LRC              │
    └─────────────────┘
```

---

## 5 Konfiguration

### 5.1 Verstärkung (GAIN-Pin)

Die Verstärkung wird über den Pegel am GAIN-Pin bei Einschalten oder Reset konfiguriert. Im Betrieb bleibt der Wert latched. Die Verstärkung bezieht sich auf den Referenzpegel von 2,1 dBV.

| GAIN-Pin-Beschaltung | Verstärkung | Hinweis |
|---|---|---|
| 100 kΩ nach GND | 15 dB | Maximale Verstärkung |
| Direkt an GND | 12 dB | – |
| **Offen (unbeschaltet)** | **9 dB** | **Standardeinstellung des Breakout-Boards** |
| Direkt an Vin | 6 dB | – |
| 100 kΩ nach Vin | 3 dB | Minimale Verstärkung |

**Dimensionierung:** Bei 4-Ω-Last und 5-V-Versorgung liefert die Standardeinstellung (9 dB) ausreichend Pegel für die meisten Sprachanwendungen. Für Roboterplattformen mit Umgebungsgeräuschen kann 12 dB (GAIN → GND) die Sprachverständlichkeit verbessern. Bei 15 dB besteht Clipping-Gefahr, wenn der digitale Pegel bereits hoch ist.

### 5.2 Kanalauswahl und Shutdown (SD-Pin)

Der SD-Pin hat eine Doppelfunktion: Kanalauswahl und Shutdown-Steuerung. Ein interner 100-kΩ-Pulldown beeinflusst die effektive Spannung.

| Spannung am SD-Pin | Funktion | Ausgangskanal |
|---|---|---|
| < 0,16 V (GND) | **Shutdown** | Verstärker abgeschaltet ($I_\text{Q} ≈ 10\,\mu\text{A}$) |
| 0,16 … 0,77 V | Aktiv | **(L + R) / 2** → Stereo-Mix (Mono-Ausgabe) |
| 0,77 … 1,4 V | Aktiv | Nur **rechter Kanal** |
| > 1,4 V | Aktiv | Nur **linker Kanal** |

**Breakout-Board-Konfiguration:** Ein 1-MΩ-Widerstand zwischen SD und Vin erzeugt bei 5 V Versorgung einen Spannungsteiler mit dem internen 100-kΩ-Pulldown. Die resultierende Spannung beträgt:

$$
V_\text{SD} = 5\,\text{V} \times \frac{100\,\text{k}\Omega}{100\,\text{k}\Omega + 1\,\text{M}\Omega} \approx 0{,}45\,\text{V}
$$

Dieser Wert liegt im Bereich 0,16 … 0,77 V → Standard-Stereo-Mix (L+R)/2.

**Shutdown per GPIO:** Den SD-Pin über einen GPIO (Open-Drain oder Push-Pull mit Spannungsteiler) auf GND ziehen, um den Verstärker in den stromsparenden Shutdown-Modus zu versetzen. Im AMR-Kontext lässt sich so die Audioausgabe deaktivieren, wenn der Roboter in den Standby-Modus wechselt.

---

## 6 Ausgangscharakteristik

### 6.1 Bridge-Tied Load (BTL)

Der MAX98357A arbeitet als BTL-Verstärker: Beide Ausgangspins (OUTP, OUTN) treiben alternierend den Lautsprecher, ohne Bezug zur Masse. Die effektive Ausgangsspannung verdoppelt sich gegenüber einer Single-Ended-Konfiguration.

```
    OUTP ──────┐
               │  ┌──────────┐
               ├──┤ Speaker  ├──┐
               │  │ 4 Ω      │  │
    OUTN ──────┘  └──────────┘  │
                                │
    (kein GND-Anschluss am Lautsprecher!)
```

**Filterloser Betrieb:** Das Ausgangssignal ist ein PWM-Signal mit ca. 330 kHz Schaltfrequenz. Die Induktivität der Lautsprecherspule dient als Tiefpassfilter und mittelt die Hochfrequenzkomponenten. Daher den Ausgang nicht an einen weiteren Verstärker oder an kapazitive Lasten anschließen.

### 6.2 Ausgangsleistung – Übersicht

| $V_\text{DD}$ | Last | $P_\text{max}$ (10 % THD) | $P_\text{max}$ (1 % THD) |
|---|---|---|---|
| 5,0 V | 4 Ω | 3,2 W | 2,5 W |
| 5,0 V | 8 Ω | 1,8 W | 1,4 W |
| 3,3 V | 4 Ω | 1,3 W | 1,0 W |
| 3,3 V | 8 Ω | 0,8 W | 0,6 W |

### 6.3 Stromaufnahme

Bei Vollaussteuerung in den ADA3351 (4 Ω, 5 V) kann der Spitzenstrom über 650 mA erreichen. Die Versorgung muss entsprechend dimensioniert sein.

| Betriebszustand | Typischer Strom | Bemerkung |
|---|---|---|
| Shutdown (SD = Low) | 10 µA | SD-Pin < 0,16 V |
| Ruhe (kein Signal) | 2,4 mA | Kein Audio-Input |
| Mittlere Lautstärke | 200 … 400 mA | Abhängig von Signal und Gain |
| Vollaussteuerung (4 Ω, 5 V) | bis 650 mA | Versorgung ≥ 800 mA empfohlen |

---

## 7 Verdrahtung

### 7.1 Anschlussdiagramm (ESP32-S3)

```
    ESP32-S3                         MAX98357A Breakout
    ┌──────────┐                     ┌───────────────────┐
    │          │                     │                   │
    │   5V  ───┼─────────────────────┤ Vin               │
    │   GND ───┼─────────────────────┤ GND               │
    │          │                     │                   │        ADA3351
    │ GPIO12 ──┼── BCLK ────────────►│ BCLK              │      ┌──────────┐
    │ GPIO11 ──┼── LRCLK ───────────►│ LRC               │   ┌──┤ Speaker  │
    │ GPIO10 ──┼── DIN ─────────────►│ DIN               │   │  │ 4Ω / 3W  │
    │          │                     │           + (out) ├───┘  └──────────┘
    │          │                     │           − (out) ├──────────┘
    │ (GPIO13)─┼─ optional ─────────►│ SD (Shutdown)     │
    │          │                     │                   │
    │          │                     │ GAIN (offen=9dB)  │
    └──────────┘                     └───────────────────┘
```

**Hinweise zur Pin-Wahl:**

- Die GPIO-Nummern sind ein Vorschlag. Der ESP32-S3 ermöglicht flexible I²S-Pin-Zuordnung über die GPIO-Matrix.
- Die I²S-Datenleitungen arbeiten mit 3,3 V Logik – der MAX98357A akzeptiert 3,3 V und 5 V, daher ist keine Pegelwandlung nötig.
- Vin mit 5 V versorgen (z. B. direkt vom USB-VBUS des ESP32-S3-Boards), um die volle Ausgangsleistung zu erreichen.
- Der JST-PH-Stecker des ADA3351 passt nicht direkt auf die Schraubklemme. Entweder die Kabelenden abisolieren und in die Schraubklemme einführen oder einen JST-PH-Gegenstecker verlöten.

### 7.2 Anschlussdiagramm (Raspberry Pi 5)

| MAX98357A Pin | Raspberry Pi Pin | GPIO |
|---|---|---|
| Vin | Pin 2 oder 4 | 5 V |
| GND | Pin 6 | GND |
| BCLK | Pin 12 | GPIO 18 |
| LRC | Pin 35 | GPIO 19 |
| DIN | Pin 40 | GPIO 21 |

---

## 8 Firmware-Integration (ESP32-S3, ESP-IDF v5.x)

### 8.1 I²S-Treiber-Initialisierung (neue API)

Die ESP-IDF ab Version 5.0 verwendet die neue I²S-Treiber-API mit getrennten TX/RX-Kanälen. Die Legacy-API (`i2s_driver_install()`) ist veraltet und sollte nicht mehr verwendet werden.

```c
#include "driver/i2s_std.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "audio_out";

/* GPIO-Zuordnung (anpassbar) */
#define I2S_BCLK_PIN    GPIO_NUM_12
#define I2S_LRCLK_PIN   GPIO_NUM_11
#define I2S_DOUT_PIN    GPIO_NUM_10

static i2s_chan_handle_t tx_handle = NULL;

/**
 * I²S-TX-Kanal für MAX98357A initialisieren.
 *
 * @param sample_rate  Abtastrate in Hz (8000 … 96000)
 * @return ESP_OK bei Erfolg
 */
esp_err_t audio_out_init(uint32_t sample_rate)
{
    /* --- Kanal anlegen --- */
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(
        I2S_NUM_0, I2S_ROLE_MASTER);
    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, &tx_handle, NULL));

    /* --- Standard-Modus (Philips I²S) konfigurieren --- */
    i2s_std_config_t std_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(sample_rate),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(
                        I2S_DATA_BIT_WIDTH_16BIT,
                        I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,   /* MAX98357A benötigt kein MCLK */
            .bclk = I2S_BCLK_PIN,
            .ws   = I2S_LRCLK_PIN,
            .dout = I2S_DOUT_PIN,
            .din  = I2S_GPIO_UNUSED,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv   = false,
            },
        },
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(tx_handle, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_enable(tx_handle));

    ESP_LOGI(TAG, "I2S TX initialisiert: %lu Hz, 16 Bit, Mono", sample_rate);
    return ESP_OK;
}
```

### 8.2 Audiodaten senden

```c
/**
 * PCM-Daten an den MAX98357A senden.
 *
 * @param data        Zeiger auf 16-Bit-PCM-Samples (Signed Little-Endian)
 * @param len_bytes   Größe der Daten in Bytes
 * @param timeout_ms  Timeout in Millisekunden
 * @return Anzahl der geschriebenen Bytes
 */
size_t audio_out_write(const int16_t *data, size_t len_bytes, uint32_t timeout_ms)
{
    size_t bytes_written = 0;
    esp_err_t err = i2s_channel_write(tx_handle, data, len_bytes,
                                      &bytes_written,
                                      pdMS_TO_TICKS(timeout_ms));
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "I2S write Fehler: %s", esp_err_to_name(err));
    }
    return bytes_written;
}
```

### 8.3 Sinuston-Generator (Testfunktion)

```c
#include <math.h>

#define SAMPLE_RATE     16000
#define TONE_FREQ_HZ    440
#define TONE_DURATION_S 2
#define AMPLITUDE        8000   /* max. 32767 für 16 Bit */

void audio_test_sine(void)
{
    audio_out_init(SAMPLE_RATE);

    const int total_samples = SAMPLE_RATE * TONE_DURATION_S;
    int16_t buf[256];

    for (int i = 0; i < total_samples; i += 256) {
        int chunk = (total_samples - i < 256) ? (total_samples - i) : 256;
        for (int j = 0; j < chunk; j++) {
            float t = (float)(i + j) / SAMPLE_RATE;
            buf[j] = (int16_t)(AMPLITUDE * sinf(2.0f * M_PI * TONE_FREQ_HZ * t));
        }
        audio_out_write(buf, chunk * sizeof(int16_t), 1000);
    }

    ESP_LOGI(TAG, "Sinuston 440 Hz beendet");
}
```

### 8.4 Shutdown-Steuerung per GPIO

```c
#define AUDIO_SD_PIN    GPIO_NUM_13

void audio_shutdown_init(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << AUDIO_SD_PIN),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
    };
    gpio_config(&io_conf);
    gpio_set_level(AUDIO_SD_PIN, 1);  /* Verstärker aktiv */
}

void audio_shutdown(bool shutdown)
{
    /* Low = Shutdown (<0,16 V), High = Aktiv */
    gpio_set_level(AUDIO_SD_PIN, shutdown ? 0 : 1);
    ESP_LOGI(TAG, "Audio %s", shutdown ? "Shutdown" : "Aktiv");
}
```

### 8.5 CMake-Integration

```cmake
# In der Komponenten-CMakeLists.txt:
idf_component_register(
    SRCS "audio_out.c"
    INCLUDE_DIRS "include"
    REQUIRES driver
)
```

---

## 9 Raspberry Pi-Integration

### 9.1 Treiberinstallation

Der Raspberry Pi (ab Modell B+ mit 2×20-Pin-Header) unterstützt I²S-Audio über ein Device Tree Overlay.

```bash
# Automatische Installation (empfohlen)
sudo apt install -y wget python3-venv
python3 -m venv env --system-site-packages
source env/bin/activate
pip3 install adafruit-python-shell
wget https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/raw/main/i2samp.py
sudo -E env PATH=$PATH python3 i2samp.py
```

Nach dem Neustart fügt das Skript das Overlay `dtoverlay=max98357a` in `/boot/firmware/config.txt` ein und konfiguriert ALSA.

### 9.2 Manuelle Konfiguration

```bash
# In /boot/firmware/config.txt:
# dtparam=audio=on    ← Zeile auskommentieren
dtoverlay=max98357a
dtoverlay=i2s-mmap    # Optional: dmixer-Unterstützung
```

### 9.3 ALSA-Konfiguration (/etc/asound.conf)

```
pcm.speakerbonnet {
    type hw card 0
}

pcm.dmixer {
    type dmix
    ipc_key 1024
    ipc_perm 0666
    slave {
        pcm "speakerbonnet"
        period_time 0
        period_size 1024
        buffer_size 8192
        rate 44100
        channels 2
    }
}

ctl.dmixer {
    type hw card 0
}

pcm.softvol {
    type softvol
    slave.pcm "dmixer"
    control.name "PCM"
    control.card 0
}

ctl.softvol {
    type hw card 0
}

pcm.!default {
    type plug
    slave.pcm "softvol"
}
```

### 9.4 Audiotests

```bash
# Weißes Rauschen (Stereo, alternierend L/R)
speaker-test -c2

# WAV-Datei
speaker-test -c2 --test=wav -w /usr/share/sounds/alsa/Front_Center.wav

# MP3-Wiedergabe
sudo apt install -y mpg123
mpg123 http://ice1.somafm.com/u80s-128-mp3

# Lautstärke anpassen
alsamixer
```

**Wichtig:** Der Raspberry Pi I²S-Treiber unterstützt nur Stereo-Ausgabe. Mono-Dateien müssen vor der Wiedergabe in Stereo konvertiert werden. Der MAX98357A mischt (L+R)/2 automatisch auf den Mono-Ausgang.

---

## 10 ROS 2-Integration (Sprachausgabe im AMR)

### 10.1 Systemarchitektur

Im AMR-Projekt kann die Sprachausgabe über den I²S-Pfad des ESP32-S3 oder direkt über den Raspberry Pi 5 erfolgen.

**Variante A – Audio über Raspberry Pi 5 (empfohlen für TTS):**

```
Raspberry Pi 5 (ROS 2 Humble)
    │
    I²S (GPIO 18/19/21) ──── MAX98357A ──── ADA3351
    │
    ├── /audio_play (Action) ← WAV/MP3-Wiedergabe
    ├── /tts (Service)       ← Text-to-Speech (piper, espeak-ng)
    └── /diagnostic_beep     ← Warntöne, Statusmeldungen
```

**Variante B – Audio über ESP32-S3 (für einfache Warntöne):**

```
ESP32-S3 (micro-ROS)
    │
    I²S (GPIO 10/11/12) ──── MAX98357A ──── ADA3351
    │
    └── /audio_cmd (Subscriber) ← Ton-ID vom ROS-Netzwerk
```

### 10.2 Beispiel: TTS-Ausgabe (Raspberry Pi)

```bash
# piper TTS installieren
pip3 install piper-tts

# Sprachausgabe über ALSA
echo "Batterie bei 20 Prozent" | piper --model de_DE-thorsten-medium \
    --output-raw | aplay -r 22050 -f S16_LE -c 1 -D plughw:0,0
```

---

## 11 Leistungsberechnung und Kompatibilität

### 11.1 Kompatibilitätsprüfung Verstärker ↔ Lautsprecher

Der ADA3351 verträgt maximal 3 W bei 4 Ω Impedanz. Die maximale Ausgangsleistung des MAX98357A bei 5 V und 4 Ω beträgt 3,2 W (bei 10 % THD) – der Lautsprecher liegt also knapp an der Leistungsgrenze. Bei 1 % THD liefert der Verstärker 2,5 W, was innerhalb der sicheren Belastung liegt.

**Empfehlung:** Für Dauerbetrieb den digitalen Pegel auf maximal 80 % (−2 dB) beschränken oder die Verstärkung auf 6 dB reduzieren (GAIN → Vin), um den Lautsprecher nicht dauerhaft an der Belastungsgrenze zu betreiben.

### 11.2 Spitzenstrom bei 3 W / 4 Ω

$$
I_\text{peak} = \frac{P}{V_\text{DD}} = \frac{3{,}2\,\text{W}}{5\,\text{V}} = 640\,\text{mA}
$$

Tatsächlich liegt der Spitzenstrom aufgrund von Verlusten und Class-D-Effizienz bei ca. 700 mA. Die 5-V-Versorgung muss mindestens 800 mA liefern können, um Spannungseinbrüche und Audioverzerrungen zu vermeiden.

### 11.3 Betrieb bei 3,3 V

Bei 3,3-V-Versorgung sinkt die maximale Ausgangsleistung auf 1,3 W (4 Ω). Diese Konfiguration schont den Lautsprecher und eignet sich für Sprachausgabe, bei der keine hohe Lautstärke erforderlich ist. Der Spitzenstrom reduziert sich auf ca. 400 mA.

---

## 12 Designhinweise

### 12.1 Versorgungsentkopplung

Einen 10 µF Keramikkondensator (MLCC, X5R/X7R) und einen 100 nF Keramikkondensator möglichst nah am Vin-Pin des Breakout-Boards platzieren. Die on-board Kapazitäten sind für die meisten Anwendungen ausreichend, aber bei langen Versorgungsleitungen (>10 cm) oder gemeinsamer Versorgung mit Motoren können zusätzliche Kondensatoren Störgeräusche reduzieren.

### 12.2 Leitungsführung

Die I²S-Signalleitungen (BCLK, LRCLK, DIN) möglichst kurz halten (<20 cm). Bei längeren Leitungen können Signalreflexionen und Übersprechen zu Audiostörungen führen. Für Roboterplattformen genügen typischerweise 5–10 cm Verbindungslänge.

### 12.3 EMV

Die Class-D-Schaltfrequenz von 330 kHz (±12,5 kHz Spread Spectrum) kann Störungen im Mittelwellenbereich erzeugen. Die Lautsprecherkabel möglichst kurz und verdrillt verlegen. Nicht parallel zu empfindlichen Analogsignalen oder Antennenleitungen führen.

### 12.4 Thermische Aspekte

Der MAX98357A hat einen integrierten Thermoschutz mit automatischem Shutdown. Bei 3 W Dauerleistung in 4 Ω erwärmt sich das Breakout-Board merklich, bleibt aber im sicheren Bereich. Für Dauerbetrieb bei hoher Lautstärke auf ausreichende Konvektion achten.

### 12.5 Click-/Pop-Minimierung

Der MAX98357A integriert eine Click/Pop-Unterdrückung beim Ein- und Ausschalten. Auf dem Raspberry Pi kann ein zusätzlicher Software-Workaround (`/dev/zero`-Playback im Hintergrund) restliche Pops beim Starten und Stoppen der Wiedergabe eliminieren. Das Adafruit-Installationsskript bietet diese Option an.

---

## 13 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| Kein Ton | SD-Pin auf GND (Shutdown) | SD-Pin prüfen, ggf. 1 MΩ Pullup zu Vin |
| Kein Ton | BCLK und LRCLK vertauscht | Häufigster Verdrahtungsfehler – Pins tauschen |
| Kein Ton | I²S nicht aktiviert (Pi) | `dtoverlay=max98357a` in config.txt prüfen |
| Verzerrtes Audio | Lautstärke zu hoch | `alsamixer` auf 50 % reduzieren, Gain-Pin anpassen |
| Verzerrtes Audio | Versorgungsspannung bricht ein | Netzteil ≥ 800 mA verwenden, Entkopplung prüfen |
| Knacken/Popping | ALSA-Abtastratenwechsel | dmixer mit fester Rate (44100 Hz) konfigurieren |
| Brummen / Störgeräusche | Masse-Schleife mit Motortreiber | Separate Versorgung oder LC-Filter für Audio-Vin |
| Nur ein Kanal hörbar | SD-Pin-Spannung im Bereich L oder R | SD-Widerstand anpassen (Abschnitt 5.2) |
| ESP32: `i2s_channel_write()` blockiert | DMA-Puffer zu klein | `dma_buf_count` und `dma_buf_len` erhöhen |

---

## 14 Vergleich mit alternativen Audiolösungen

| Parameter | MAX98357A (I²S) | PAM8302 (Analog) | UDA1334A (I²S DAC) + ext. Amp |
|---|---|---|---|
| Eingangstyp | Digital (I²S) | Analog | Digital (I²S) |
| DAC integriert | Ja | Nein | Ja (nur Line-Out) |
| Verstärker integriert | Ja (Class D, 3,2 W) | Ja (Class D, 2,5 W) | Nein (ext. Amp nötig) |
| Lautsprecheranschluss | Direkt (BTL) | Direkt (BTL) | Via ext. Amp |
| Komponentenanzahl | 1 Board | 1 Board + DAC | 2 Boards |
| Rein digitale Kette | Ja | Nein | Teilweise |
| THD+N | 0,02 % | 0,03 % (typ.) | Abhängig von ext. Amp |
| Shutdown-Funktion | Ja (SD-Pin) | Ja | Abhängig von ext. Amp |
| Preis (Adafruit) | ~5,50 USD | ~3,95 USD | ~7,95 USD + Amp |

Für das AMR-Projekt bietet der MAX98357A den besten Kompromiss: minimale Komponentenzahl, rein digitale Signalkette und direkter Lautsprecherantrieb.

---

## 15 Ressourcen

| Typ | Link |
|---|---|
| Adafruit Learning Guide | [learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp) |
| MAX98357A Datenblatt (PDF) | [analog.com/media/…/max98357a-max98357b.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf) |
| Adafruit Produktseite (3006) | [adafruit.com/product/3006](https://www.adafruit.com/product/3006) |
| Adafruit Produktseite (3351) | [adafruit.com/product/3351](https://www.adafruit.com/product/3351) |
| EagleCAD PCB-Dateien | [GitHub – adafruit/Adafruit-MAX98357-I2S-Class-D-Mono-Amp-PCB](https://github.com/adafruit/Adafruit-MAX98357-I2S-Class-D-Mono-Amp-PCB) |
| Pi Installer-Skript | [GitHub – adafruit/Raspberry-Pi-Installer-Scripts](https://github.com/adafruit/Raspberry-Pi-Installer-Scripts) |
| ESP-IDF I²S-Dokumentation | [docs.espressif.com/…/esp32s3/…/i2s.html](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) |
| ROS Audio Common | [GitHub – ros-drivers/audio_common](https://github.com/ros-drivers/audio_common) |

---

## 16 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   Audiosystem: MAX98357A Breakout + ADA3351 – Kurzprofil                │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   VERSTÄRKER (Art.-Nr. 3006)│                                           │
│   IC                         │ Maxim/ADI MAX98357A                       │
│   Typ                        │ I²S-DAC + Class-D-Verstärker (BTL)        │
│   Versorgung                 │ 2,5 … 5,5 V DC                           │
│   Max. Ausgangsleistung      │ 3,2 W (4 Ω, 5 V, 10 % THD)              │
│   THD+N                      │ 0,02 % (1 kHz, 1 W, 4 Ω)                │
│   Dynamikumfang              │ 105 dB(A)                                │
│   Abtastraten                │ 8 … 96 kHz (automatisch)                 │
│   Bittiefe                   │ 16 / 32 Bit                              │
│   Gain (konfigurierbar)      │ 3 / 6 / 9 / 12 / 15 dB                  │
│   MCLK                       │ Nicht erforderlich                        │
│   Shutdown-Strom             │ 10 µA                                    │
│   Schutz                     │ Thermisch + Überstrom + Kurzschluss       │
│   PCB-Abmessungen            │ ca. 27 × 18 mm                           │
│                              │                                           │
│   LAUTSPRECHER (Art.-Nr. 3351)│                                          │
│   Impedanz                   │ 4 Ω                                      │
│   Belastbarkeit              │ 3 W (max.)                               │
│   Bauform                    │ Gehäuselautsprecher, oval                 │
│   Abmessungen                │ 70 × 30 × 17 mm                          │
│   Gewicht                    │ 26,4 g                                   │
│   Anschluss                  │ JST-PH 2-Pin, Kabel ca. 57 cm            │
│                              │                                           │
│   SYSTEM                     │                                           │
│   Signalkette                │ I²S → DAC → Class D → BTL → Lautsprecher │
│   Empfohlene Versorgung      │ 5 V / ≥ 800 mA                          │
│   Betriebstemperatur         │ −40 … +85 °C (IC)                        │
│   Plattformen                │ ESP32-S3, Raspberry Pi, Arduino (SAMD)    │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: MAX98357A Datenblatt (Analog Devices), Adafruit Learning Guide (Stand: Juli 2025), ESP-IDF v5.x I²S-Dokumentation (Espressif), Adafruit Produktseiten 3006 und 3351*
