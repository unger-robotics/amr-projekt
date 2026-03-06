# LED-Streifen 12 V – SMD 5050 Warmweiß 3000 K (2 × 3 LEDs)

> **Technische Dokumentation** – LongLife LED, Art.-Nr. 1845 (zugeschnitten)  
> Typ: Einfarbiger Konstantspannungs-LED-Streifen (Constant Voltage LED Strip)  
> Konfiguration: 2 Segmente à 3 LEDs = 6 LEDs gesamt  
> Quelle: [LongLife LED Produktseite](https://www.longlife-led.de/Strip-12V-LED-Streifen-5M-7-2W-m-30LED-m-10mm-Lichtfarbe-Warmweiss-3000K-Schutzart-IP20/1845)

---

## 1 Übersicht

Die vorliegende Dokumentation beschreibt den Einsatz von zwei zugeschnittenen LED-Segmenten aus dem LED-Streifen Art.-Nr. 1845 von LongLife LED. Jedes Segment enthält 3 SMD-5050-LEDs und wird an der Schnittmarke nach 100 mm vom Originalstreifen getrennt. Die zwei Segmente bilden zusammen ein kompaktes Beleuchtungssystem mit 6 LEDs und einer Gesamtleistung von lediglich 1,44 W.

**Typische Anwendungen:** Statusbeleuchtung an Roboterplattformen (AMR), Akzentbeleuchtung in Gehäusen, Indikatorleuchten, Vitrinen- und Regalbeleuchtung auf kleinstem Raum.

---

## 2 Spezifikationen – Einzelsegment (3 LEDs / 100 mm)

### 2.1 Elektrische und lichttechnische Kenndaten

| Parameter | Wert | Bemerkung |
|---|---|---|
| Betriebsspannung | 12 V DC | Konstantspannungsbetrieb (Constant Voltage, CV) |
| LEDs pro Segment | 3 | SMD 5050, in Reihe mit Vorwiderstand |
| Segmentlänge | 100 mm | Kleinste kürzbare Einheit |
| Leistungsaufnahme pro Segment | 0,72 W | $7{,}2\,\text{W/m} \div 10\,\text{Segmente/m}$ |
| Stromaufnahme pro Segment | 60 mA | $0{,}72\,\text{W} \div 12\,\text{V}$ |
| LED-Typ | SMD 5050 | 5,0 mm × 5,0 mm, 3-Chip-Aufbau |
| Farbtemperatur (CCT) | 3000 K | Warmweiß |
| Farbwiedergabeindex (CRI) | > 80 Ra | – |
| Lichtstrom pro Segment (geschätzt) | ca. 40 … 50 lm | Ca. 13 … 17 lm pro LED |
| Abstrahlwinkel | 120° | – |
| Lebensdauer | ca. 25.000 Stunden | Herstellerangabe |
| Dimmbar | Ja | Per PWM |

### 2.2 Mechanische Daten

| Parameter | Wert |
|---|---|
| Segmentlänge | 100 mm |
| Breite | 10 mm |
| Dicke (FPCB + LED) | ca. 2 mm |
| Befestigung | Rückseitiger Klebestreifen (selbstklebend) |
| Schutzart | IP20 (nur trockener Innenbereich) |
| Anschluss | 2 Lötpads pro Segment (+12 V / GND) |

---

## 3 Gesamtsystem – 2 Segmente

### 3.1 Systemkennwerte

| Parameter | 1 Segment | 2 Segmente gesamt |
|---|---|---|
| Anzahl LEDs | 3 | 6 |
| Gesamtlänge (LED-bestückt) | 100 mm | 200 mm |
| Leistungsaufnahme | 0,72 W | 1,44 W |
| Stromaufnahme bei 12 V | 60 mA | 120 mA |
| Lichtstrom (geschätzt) | 40 … 50 lm | 80 … 100 lm |

### 3.2 Parallelschaltung der zwei Segmente

Die beiden Segmente werden parallel an die 12 V-Versorgung angeschlossen. Jedes Segment ist intern eigenständig (3 LEDs + Vorwiderstand), sodass beide Segmente unabhängig voneinander funktionieren.

```
          +12 V DC
             │
        ┌────┴────┐
        │         │
   ┌────┴────┐  ┌─┴──────┐
   │Segment 1│  │Segment 2│
   │ 3 LEDs  │  │ 3 LEDs  │
   │ 60 mA   │  │ 60 mA   │
   └────┬────┘  └─┬──────┘
        │         │
        └────┬────┘
             │
            GND
```

---

## 4 Interner Aufbau – Segmentschaltung

### 4.1 Schaltungsprinzip eines Segments

Jedes 100 mm-Segment enthält 3 SMD-5050-LEDs in Reihe mit einem Strombegrenzungswiderstand. Diese Konfiguration bildet die kleinste funktionsfähige Einheit des Streifens.

```
+12 V ──── LED 1 ──── LED 2 ──── LED 3 ──── R_Vor ──── GND
           3,0 V      3,0 V      3,0 V      ~47 Ω
         ←─────── ~9,0…9,6 V ──────────→  ←~2,4…3,0 V→
```

### 4.2 Elektrische Analyse

| Parameter | Wert | Berechnung |
|---|---|---|
| Flussspannung pro LED (typ.) | ca. 3,0 V … 3,2 V | SMD 5050, warmweiß |
| Flussspannung, 3 LEDs in Reihe | ca. 9,0 V … 9,6 V | $3 \times V_f$ |
| Spannung am Vorwiderstand | ca. 2,4 V … 3,0 V | $12\,\text{V} - 3 \times V_f$ |
| Strom durch das Segment | 60 mA | Durch Vorwiderstand bestimmt |
| Vorwiderstand (geschätzt) | ca. 43 Ω … 47 Ω | $V_R / I \approx 2{,}7\,\text{V} / 0{,}06\,\text{A}$ |
| Verlustleistung am Widerstand | ca. 0,16 W | $I^2 \times R$ |
| Verlustleistung an den LEDs | ca. 0,56 W | $3 \times V_f \times I$ |
| Segmentwirkungsgrad (elektr.) | ca. 78 % | $P_\text{LEDs} / P_\text{gesamt}$ |

---

## 5 Spannungsversorgung

### 5.1 Anforderungen

Bei einer Gesamtlast von nur 1,44 W / 120 mA sind die Anforderungen an die Spannungsversorgung gering.

| Parameter | Mindestanforderung |
|---|---|
| Ausgangsspannung | 12 V DC (stabilisiert) |
| Ausgangsstrom | ≥ 150 mA (mit Reserve) |
| Ausgangsleistung | ≥ 2 W |

### 5.2 Versorgungsoptionen

| Quelle | Eignung | Bemerkung |
|---|---|---|
| 12 V Steckernetzteil (z. B. 12 V / 1 A) | Sehr gut | Gängig, kostengünstig, weit überdimensioniert |
| Pololu D36V50F12 (12 V Buck-Regler) | Gut | Falls bereits im System vorhanden (AMR) |
| 3S-Li-Ion-Akkupack (10,8 V nom.) | Bedingt | Nennspannung liegt unter 12 V; Segmente leuchten schwächer, funktionieren aber ab ca. 9,5 V |
| Labornetzteil | Testbetrieb | Spannung einstellbar, ideal zur Charakterisierung |

### 5.3 Direktbetrieb am 3S-Li-Ion-Akkupack

Bei Betrieb am 3S-Pack (Samsung INR18650-35E, 9,0 V … 12,6 V) ergeben sich folgende Betriebspunkte:

| Packspannung | Zustand | LED-Strom (ca.) | Helligkeit |
|---|---|---|---|
| 12,6 V | Vollgeladen | ~70 mA | Leicht über Nennhelligkeit |
| 10,8 V | Nennspannung | ~40 mA | Reduziert (~65 %) |
| 9,5 V | Fast entladen | ~15 mA | Deutlich gedimmt |
| 9,0 V | Entladegrenze | ~5 mA | Kaum sichtbar |

**Beobachtung:** Da der Vorwiderstand den Strom linear mit der Eingangsspannung variiert, ändert sich die Helligkeit über den Entladezyklus merklich. Bei Nennspannung (10,8 V) liegt der Strom bereits ca. 35 % unter dem Nennwert bei 12 V.

**Konsequenz:** Für konstante Helligkeit am Akkupack empfiehlt sich ein 12 V-Aufwärts-/Abwärtsregler (Buck-Boost) oder der D36V50F12 (12 V-Variante der D36V50Fx-Familie). Alternativ genügt die variable Helligkeit als grobe Ladezustandsanzeige.

### 5.4 Strombelastung des Akkupacks

Mit 120 mA Gesamtstrom belasten die LED-Segmente den 3S-Pack (3.350 mAh) kaum:

$$
t_\text{LED} = \frac{3{,}35\,\text{Ah}}{0{,}12\,\text{A}} \approx 27{,}9\,\text{h}
$$

Die LEDs allein würden den Akku rechnerisch ca. 28 Stunden betreiben – ein vernachlässigbarer Beitrag zum Gesamtenergieverbrauch im AMR-System.

---

## 6 Dimmen per PWM

### 6.1 MOSFET-Dimensionierung

Bei nur 120 mA Gesamtstrom genügt ein kleiner Logic-Level-N-Kanal-MOSFET im Low-Side-Schaltbetrieb.

```
ESP32-S3 GPIO ── R_Gate (100 Ω) ──── Gate
                                       │
                +12 V ── Strip (+)     │   N-MOSFET
                         Strip (−) ── Drain
                                       │
                                    Source ── GND
```

| Parameter | Anforderung | Bemerkung |
|---|---|---|
| $V_\text{DS}$ (max.) | > 12 V | – |
| $I_D$ (Dauerstrom) | > 120 mA | Weit unterkritisch für jeden diskreten MOSFET |
| $V_\text{GS(th)}$ | < 3,3 V | Logic Level, ansteuerbar durch ESP32-S3 GPIO |

**Geeignete MOSFETs (Auswahl):**

| Typ | $V_\text{DS}$ | $I_D$ | $R_\text{DS(on)}$ | Bauform |
|---|---|---|---|---|
| 2N7002 | 60 V | 300 mA | 2,5 Ω | SOT-23 |
| IRLML6344 | 30 V | 5 A | 29 mΩ | SOT-23 |
| BSS138 | 50 V | 200 mA | 3,5 Ω | SOT-23 |
| IRLZ44N | 55 V | 47 A | 22 mΩ | TO-220 |

Bei 120 mA und $R_\text{DS(on)} = 2{,}5\,\Omega$ (2N7002) beträgt die Verlustleistung:

$$
P_\text{MOSFET} = I^2 \times R_\text{DS(on)} = 0{,}12^2 \times 2{,}5 = 0{,}036\,\text{W} = 36\,\text{mW}
$$

Kein Kühlkörper erforderlich. Selbst der kleinste SOT-23-MOSFET ist ausreichend.

### 6.2 PWM-Frequenz

| Frequenz | Bewertung |
|---|---|
| 1 kHz … 5 kHz | Guter Kompromiss, kein sichtbares Flackern |
| > 20 kHz | Ideal für Video-/Kameraumgebungen (kein Stroboskopeffekt) |

### 6.3 Firmware-Beispiel (ESP32-S3, ESP-IDF, LEDC)

```c
#include "driver/ledc.h"
#include <math.h>

#define LED_STRIP_GPIO       GPIO_NUM_5
#define LED_STRIP_CHANNEL    LEDC_CHANNEL_0
#define LED_STRIP_TIMER      LEDC_TIMER_0
#define PWM_FREQUENCY        5000               // 5 kHz
#define PWM_RESOLUTION       LEDC_TIMER_13_BIT  // 0 … 8191
#define PWM_MAX_DUTY         ((1 << 13) - 1)    // 8191
#define GAMMA                2.2f

esp_err_t led_strip_pwm_init(void) {
    ledc_timer_config_t timer_cfg = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,
        .duty_resolution = PWM_RESOLUTION,
        .timer_num       = LED_STRIP_TIMER,
        .freq_hz         = PWM_FREQUENCY,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer_cfg));

    ledc_channel_config_t ch_cfg = {
        .gpio_num   = LED_STRIP_GPIO,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel    = LED_STRIP_CHANNEL,
        .timer_sel  = LED_STRIP_TIMER,
        .duty       = 0,
        .hpoint     = 0,
    };
    return ledc_channel_config(&ch_cfg);
}

// brightness: 0.0 (aus) … 1.0 (volle Helligkeit)
void led_strip_set_brightness(float brightness) {
    if (brightness < 0.0f) brightness = 0.0f;
    if (brightness > 1.0f) brightness = 1.0f;

    // Gamma-Korrektur für lineares Helligkeitsempfinden
    float corrected = powf(brightness, GAMMA);
    uint32_t duty = (uint32_t)(corrected * PWM_MAX_DUTY);

    ledc_set_duty(LEDC_LOW_SPEED_MODE, LED_STRIP_CHANNEL, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LED_STRIP_CHANNEL);
}
```

### 6.4 Individuelle Steuerung beider Segmente

Wenn die zwei Segmente unabhängig gedimmt werden sollen (z. B. links/rechts am Roboter), werden zwei separate MOSFET-Kanäle und LEDC-Kanäle benötigt:

```c
#define LED_LEFT_GPIO    GPIO_NUM_5
#define LED_RIGHT_GPIO   GPIO_NUM_6
#define LED_LEFT_CH      LEDC_CHANNEL_0
#define LED_RIGHT_CH     LEDC_CHANNEL_1
```

```
+12 V ──┬───── Segment 1 (−) ── Drain ── MOSFET_L ── GND
        │                                   Gate ← GPIO_5
        │
        └───── Segment 2 (−) ── Drain ── MOSFET_R ── GND
                                            Gate ← GPIO_6
```

Damit lassen sich Effekte wie alternierdes Blinken, Lauflicht oder asymmetrisches Dimmen realisieren.

---

## 7 Verdrahtung und Anschluss

### 7.1 Zuschnitt

Der Streifen wird an den Schnittmarken (Scherensymbol) nach jeweils 100 mm getrennt. Jeder Schnitt erzeugt ein eigenständiges Segment mit freiliegenden Kupfer-Lötpads auf beiden Seiten.

```
  Schnittmarke              Schnittmarke
       ↓                         ↓
──✂──┤ LED  LED  LED  R ┝──✂──┤ LED  LED  LED  R ┝──✂──
     │←──── 100 mm ────→│     │←──── 100 mm ────→│
          Segment 1                 Segment 2

     (+)                (−)   (+)                (−)
     Lötpad             Lötpad  Lötpad           Lötpad
```

### 7.2 Löten der Anschlussdrähte

| Parameter | Empfehlung |
|---|---|
| Lötkolbentemperatur | max. 350 °C |
| Lötdauer pro Pad | max. 3 Sekunden |
| Litzenquerschnitt | 0,25 mm² … 0,50 mm² (ausreichend für 60 mA) |
| Lötzinn | bleifreies Lot (Sn96,5Ag3Cu0,5) oder verbleites Sn60Pb40 |

### 7.3 Steckverbinder-Alternative

Für lösbare Verbindungen eignen sich 2-polige JST-PH- oder JST-XH-Steckverbinder. Bei nur 60 mA pro Segment ist jeder gängige Kleinsignal-Steckverbinder ausreichend dimensioniert.

---

## 8 Montage

### 8.1 Befestigungsoptionen

| Methode | Eignung | Bemerkung |
|---|---|---|
| Rückseitiger Klebestreifen | Gut | Ab Werk vorhanden, glatte Oberfläche erforderlich |
| Aluminiumprofil | Ideal | Wärmeabfuhr, mechanischer Schutz, saubere Optik |
| Kabelbinder / Klettband | Provisorisch | Für Prototypen und Testaufbauten |
| Heißkleber | Bedingt | Hitze kann FPCB beschädigen, bei LEDs vermeiden |

### 8.2 Thermisches Management

Bei nur 0,72 W pro Segment ist die Wärmeentwicklung minimal (Gesamtverlustleistung < 1,5 W). Ein Aluminiumprofil ist bei dieser geringen Last nicht zwingend erforderlich, erhöht jedoch die Lebensdauer und schützt die LEDs vor mechanischer Beschädigung.

---

## 9 Energieverbrauch

### 9.1 Verbrauchsübersicht

| Betriebsmodus | Leistung | Strom |
|---|---|---|
| 100 % Helligkeit | 1,44 W | 120 mA |
| 50 % Helligkeit (PWM) | 0,72 W | 60 mA (Mittelwert) |
| Aus (PWM Duty = 0) | 0 W | 0 mA (MOSFET sperrt) |

### 9.2 Anteil am AMR-Gesamtverbrauch

Im Kontext eines AMR-Systems mit typisch 15 W … 25 W Gesamtverbrauch (Raspberry Pi 5, ESP32-S3, Sensorik, Motoren) stellen die LED-Segmente mit 1,44 W einen Anteil von ca. 6 % … 10 % dar – vernachlässigbar für die Laufzeitplanung.

$$
\frac{P_\text{LED}}{P_\text{AMR}} = \frac{1{,}44\,\text{W}}{22\,\text{W}} \approx 6{,}5\,\%
$$

---

## 10 Sicherheitshinweise

- **Schutzkleinspannung (SELV):** Der Betrieb erfolgt bei 12 V DC. Bei Netzteileinsatz muss das Netzteil galvanisch vom 230 V-Netz getrennt sein (EN 61558). Die 230 V-seitige Installation erfolgt durch eine Elektrofachkraft.
- **IP20:** Ausschließlich für den trockenen Innenbereich. Kein Einsatz in Feuchträumen oder im Freien.
- **Brandschutz:** Bei < 1,5 W Gesamtleistung unkritisch. Dennoch nicht auf leicht entflammbaren Materialien ohne Unterlage montieren.
- **Kurzschlussschutz:** Bei Akkubetrieb (3S-Pack) eine Sicherung (z. B. 500 mA flink) in die Zuleitung integrieren, um im Fehlerfall den Akkupack zu schützen.

---

## 11 Zusammenfassung der Schlüsselparameter

```
┌────────────────────────────────────────────────────────────────┐
│   LED-Segmente LongLife LED Art.-Nr. 1845 – Kurzprofil         │
├─────────────────────────┬──────────────────────────────────────┤
│ Konfiguration           │ 2 Segmente à 3 LEDs (parallel)      │
│ LED-Typ                 │ SMD 5050 (3-Chip), warmweiß          │
│ Betriebsspannung        │ 12 V DC (funktional ab ~9,5 V)      │
│ Gesamtleistung          │ 1,44 W                              │
│ Gesamtstrom             │ 120 mA                              │
│ Strom pro Segment       │ 60 mA                               │
│ Farbtemperatur          │ 3000 K (Warmweiß)                   │
│ CRI                     │ > 80 Ra                             │
│ Lichtstrom (geschätzt)  │ 80 … 100 lm (gesamt)               │
│ Abstrahlwinkel          │ 120°                                │
│ Abmessungen pro Segment │ 100 mm × 10 mm × 2 mm              │
│ Lebensdauer             │ ca. 25.000 h                        │
│ Dimmbar                 │ Ja (PWM, MOSFET Low-Side)           │
│ Schutzart               │ IP20                                │
│ MOSFET-Empfehlung       │ 2N7002 / BSS138 (SOT-23)           │
│ Sicherung (bei Akku)    │ 500 mA flink                       │
└─────────────────────────┴──────────────────────────────────────┘
```

---

*Dokumentversion: 2.0 | Datum: 2025-02-24 | Quelle: LongLife LED, longlife-led.de, Art.-Nr. 1845*
