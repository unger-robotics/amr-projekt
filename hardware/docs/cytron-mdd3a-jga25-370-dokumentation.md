# Motor-Treiber Cytron MDD3A + Antriebsmotoren JGA25-370 mit Hall-Encoder

> **Technische Dokumentation** – Antriebssystem für autonome mobile Robotik (AMR)  
> Motor-Treiber: Cytron MDD3A (Dual-Kanal, MOSFET-H-Brücke, 4–16 V, 3 A kontinuierlich)  
> Antriebsmotoren: 2× JGA25-370 (12 V DC, Metallgetriebe, Quadratur-Hall-Encoder, 11 CPR)  
> Steuerung: Seeed XIAO ESP32-S3 (3,3 V Logik) via micro-ROS  
> Quellen: [Cytron MDD3A Datasheet (PDF)](https://cdn.robotshop.com/media/c/cyt/rb-cyt-260/pdf/cytron-3a-4-16v-dual-channel-dc-motor-driver-datasheet.pdf), [Cytron Produktseite](https://www.cytron.io/p-3amp-4v-16v-dc-motor-driver-2-channels), [CytronMotorDriver (GitHub)](https://github.com/CytronTechnologies/CytronMotorDriver), [JGA25-370 Encoder Pinout (abra-electronics)](https://abra-electronics.com/electromechanical/motors/gear-motors/metal-gearmotors/jga25-370-series/jga25-370-e.html)

---

## 1 Systemübersicht

### 1.1 Antriebskonzept

Das AMR-Antriebssystem nutzt einen Differentialantrieb (Differential Drive) mit zwei unabhängig angesteuerten Gleichstrommotoren. Der Cytron MDD3A steuert beide Motoren über eine diskrete MOSFET-H-Brücke. Die integrierten Quadratur-Hall-Encoder der JGA25-370-Motoren liefern Drehzahl- und Richtungsinformation für die geschlossene Regelschleife (Closed-Loop Control).

```
3S-LiPo-Batterie (9,0 … 12,6 V)
        │
        ▼
┌───────────────────────────────────────────────────┐
│              Cytron MDD3A                         │
│         Dual-Kanal MOSFET-H-Brücke               │
│                                                   │
│  VB+ ──────────────────────────── VB-             │
│                                                   │
│  ┌──────────────┐    ┌──────────────┐             │
│  │   Kanal 1    │    │   Kanal 2    │             │
│  │  M1A ← PWM   │    │  M2A ← PWM   │             │
│  │  M1B ← PWM   │    │  M2B ← PWM   │             │
│  │              │    │              │             │
│  │  OUT1A ─┐    │    │  OUT2A ─┐    │             │
│  │  OUT1B ─┤    │    │  OUT2B ─┤    │             │
│  └─────────┤────┘    └─────────┤────┘             │
│            │                   │                  │
│  5VO (200 mA) ── GND                             │
└────────────┼───────────────────┼──────────────────┘
             │                   │
     ┌───────┴───────┐  ┌───────┴───────┐
     │  JGA25-370    │  │  JGA25-370    │
     │  Motor LINKS  │  │  Motor RECHTS │
     │               │  │               │
     │  Encoder A ───┼──┼── Encoder A   │
     │  Encoder B ───┼──┼── Encoder B   │
     └───────────────┘  └───────────────┘
             │                   │
             ▼                   ▼
     Seeed XIAO ESP32-S3 (GPIO-Interrupts)
```

### 1.2 Signalfluss

| Pfad | Richtung | Signal | Funktion |
|---|---|---|---|
| ESP32-S3 → MDD3A | Ausgang | PWM (3,3 V, ≤ 20 kHz) | Motordrehzahl und -richtung |
| Motor → ESP32-S3 | Eingang | Encoder A/B (3,3 V Rechteck) | Quadratur-Rückmeldung |
| MDD3A → ESP32-S3 | Ausgang | 5VO (max. 200 mA) | Optional: Encoder-Versorgung |
| Batterie → MDD3A | Leistung | 9,0 … 12,6 V DC | Motorversorgung |

---

## 2 Cytron MDD3A – Motor-Treiber

### 2.1 Technische Daten

| Parameter | Min | Typ | Max | Einheit |
|---|---|---|---|---|
| **Versorgungsspannung (V_in)** | 4 | 12 | 16 | V DC |
| **Motorstrom pro Kanal (kontinuierlich)** | – | – | 3 | A |
| **Motorstrom pro Kanal (Spitze, < 5 s)** | – | – | 5 | A |
| **Logik-Eingangsspannung (Low)** | 0 | – | 0,5 | V |
| **Logik-Eingangsspannung (High)** | 1,7 | 3,3 | 12 | V |
| **PWM-Frequenz** | DC | – | 20 | kHz |
| **5-V-Ausgang (5VO)** | – | 5,0 | – | V |
| **5-V-Ausgangsstrom (max.)** | – | – | 200 | mA |
| **Kanäle** | – | 2 | – | – |
| **H-Brücken-Topologie** | – | Diskrete MOSFETs | – | – |
| **Steuerungsmodi** | – | Lock-Antiphase + Sign-Magnitude | – | PWM |

> **Vorteil gegenüber L298N:** Die MOSFET-H-Brücke des MDD3A hat einen deutlich geringeren Spannungsabfall als die Bipolartransistoren des L298N (~0,3 V statt ~2,0 V bei 1 A). Bei 12-V-Betrieb stehen dem Motor somit ~11,7 V statt ~10 V zur Verfügung – ein Effizienzgewinn von ca. 15 %.

### 2.2 Schutzfunktionen

| Schutz | Beschreibung |
|---|---|
| **Verpolungsschutz (Eingang)** | Verhindert Schäden bei vertauschter Batteriepolarität |
| **Überstromschutz** | Strombegrenzung bei > 3 A kontinuierlich |
| **Thermische Abschaltung** | Automatische Abschaltung bei Übertemperatur |
| **Unterspannungssperre (UVLO)** | Abschaltung bei V_in < 4 V |

### 2.3 Pinbelegung

```
Signalleiste (6-Pin-Header):
┌─────────────────────────────────────┐
│  M1A   M1B   5VO   GND   M2A   M2B │
└──┬─────┬─────┬─────┬─────┬─────┬───┘
   │     │     │     │     │     │
   │     │     │     │     │     └─ PWM-Eingang B, Motor 2
   │     │     │     │     └─── PWM-Eingang A, Motor 2
   │     │     │     └───── Masse (gemeinsam)
   │     │     └─────── +5 V Ausgang (Buck-Boost, max. 200 mA)
   │     └───────── PWM-Eingang B, Motor 1
   └─────────── PWM-Eingang A, Motor 1

Motor-Klemmen:
┌─────────────┐          ┌─────────────┐
│  M1A   M1B  │          │  M2A   M2B  │
│  (Motor 1)  │          │  (Motor 2)  │
└─────────────┘          └─────────────┘

Leistungs-Klemmen:
┌─────────────┐
│  VB+   VB-  │
│ (Batterie)  │
└─────────────┘
```

### 2.4 Steuerungsprinzip

Der MDD3A verwendet ein **Locked-Antiphase-PWM-Verfahren**: Jeder Motorkanal besitzt zwei Eingänge (MxA, MxB). Geschwindigkeit und Richtung ergeben sich aus der Kombination der PWM-Signale an beiden Eingängen.

**Wahrheitstabelle:**

| Eingang A (MxA) | Eingang B (MxB) | Ausgang A | Ausgang B | Motorverhalten |
|---|---|---|---|---|
| Low | Low | Low | Low | **Bremse** (Kurzschluss) |
| High (PWM) | Low | High | Low | **Vorwärts** (Drehzahl ∝ Duty Cycle) |
| Low | High (PWM) | Low | High | **Rückwärts** (Drehzahl ∝ Duty Cycle) |
| High | High | High | High | **Bremse** (Kurzschluss) |

Für die AMR-Anwendung wird der **Sign-Magnitude-Modus** empfohlen: Ein Pin liefert das PWM-Signal (Geschwindigkeit), der andere bestimmt die Richtung (High/Low). Die Cytron-Arduino-Bibliothek implementiert diesen Modus direkt.

### 2.5 PWM-Frequenz und Motorgeräusch

| PWM-Frequenz | Hörbarkeit | Empfehlung |
|---|---|---|
| < 1 kHz | Deutlich hörbar (Pfeifen) | Nicht empfohlen |
| 1 … 5 kHz | Leises Summen | Bedingt geeignet |
| 5 … 10 kHz | Kaum hörbar | Guter Kompromiss |
| 10 … 20 kHz | Unhörbar (> menschliche Hörgrenze) | **Empfohlen für AMR** |

Der MDD3A gibt die Eingangs-PWM-Frequenz unverändert an den Motorausgang weiter. Die ESP32-S3-LEDC-Peripherie erzeugt PWM mit konfigurierbarer Frequenz bis zu mehreren MHz; für den MDD3A liegt das Optimum bei **10 … 20 kHz**.

### 2.6 Leistungsbilanz mit 3S-LiPo

| Betriebszustand | V_in | I_Motor (pro Kanal) | P_Motor (gesamt) | Bemerkung |
|---|---|---|---|---|
| Leerlauf (beide Motoren) | 12,0 V | ~0,15 A | ~3,6 W | JGA25-370 Leerlaufstrom |
| Normalfahrt (ebene Fläche) | 10,8 V | ~0,5 … 1,0 A | ~11 … 22 W | Abhängig von Last und Geschwindigkeit |
| Volllast / Steigung | 10,8 V | ~1,5 … 2,0 A | ~33 … 44 W | Getriebe-Stallstrom beachten |
| Blockiert (Stall) | 10,8 V | ~2,5 … 3,0 A | ~55 … 67 W | **Dauer < 5 s**, Thermoschutz des MDD3A |

> **Sicherheitshinweis:** Im Blockierzustand können die JGA25-370-Motoren bis zu ~3 A ziehen, was dem MDD3A-Dauerlimit entspricht. Ein softwareseitiger Strombegrenzungs-Timer (z. B. 2 s Stall-Erkennung → Motor aus) schützt Treiber und Motor vor thermischer Überlastung.

---

## 3 JGA25-370 – DC-Getriebemotor mit Hall-Encoder

### 3.1 Technische Daten Motor

| Parameter | Wert | Einheit |
|---|---|---|
| **Motortyp** | Bürstenmotor (Brushed DC) mit Metallgetriebe |
| **Nennspannung** | 12 | V DC |
| **Leistung** | ~3 | W |
| **Leerlaufdrehzahl** | abhängig vom Übersetzungsverhältnis (s. Tabelle) | RPM |
| **Leerlaufstrom** | ~0,15 | A |
| **Blockierdrehmoment (Stall)** | 9 … 20 (je nach Übersetzung) | kg·cm |
| **Blockierstrom (Stall)** | ~2,5 … 3,0 | A |
| **Getriebetyp** | Stirnrad (Spur Gear), Metallzahnräder |
| **Selbsthemmung** | Nein |
| **Wellendurchmesser** | 4 mm (mit D-Abflachung) |
| **Wellenlänge** | ~12 mm |
| **Gehäusedurchmesser** | 25 mm |
| **Gesamtlänge (mit Encoder)** | ~55 … 70 mm (je nach Getriebevariante) |
| **Gewicht** | ~90 … 120 g (je nach Getriebevariante) |
| **Betriebstemperatur** | −10 … +60 °C |
| **Anschluss** | 6-Pin JST-PH-Stecker (Kabellänge ~20 cm) |

### 3.2 Verfügbare Übersetzungsverhältnisse (12 V)

| Übersetzung | Leerlaufdrehzahl | Nenn-Drehmoment (ca.) | Stall-Drehmoment (ca.) | Encoder-Ticks/Umdrehung (Abtrieb) |
|---|---|---|---|---|
| 1:21 | ~620 RPM | ~1,5 kg·cm | ~9 kg·cm | 21 × 44 = 924 |
| 1:34 | ~350 RPM | ~2,5 kg·cm | ~12 kg·cm | 34 × 44 = 1.496 |
| 1:56 | ~210 RPM | ~4 kg·cm | ~15 kg·cm | 56 × 44 = 2.464 |
| **1:100** | **~130 RPM** | **~5 kg·cm** | **~16 kg·cm** | **100 × 44 = 4.400** |
| 1:150 | ~80 RPM | ~7 kg·cm | ~18 kg·cm | 150 × 44 = 6.600 |
| 1:226 | ~50 RPM | ~10 kg·cm | ~20 kg·cm | 226 × 44 = 9.944 |

> **Drehzahl-Toleranz:** Alle Leerlaufdrehzahlen haben eine herstellerseitige Toleranz von ±15 %. Für präzise Regelung ist daher der Encoder-Feedback-Pfad essenziell.

> **Empfehlung für AMR:** Die Variante mit **1:100** (≈ 130 RPM) bietet einen guten Kompromiss zwischen Fahrgeschwindigkeit und Drehmoment. Mit einem Raddurchmesser von 65 mm ergibt sich eine theoretische Maximalgeschwindigkeit von $v = \pi \times 0{,}065\,\text{m} \times 130/60 \approx 0{,}44\,\text{m/s}$.

### 3.3 Hall-Encoder

#### 3.3.1 Funktionsprinzip

Der Encoder besteht aus einem mehrpoligen Magnetscheibe (22 Pole, alternierend N/S), die direkt auf der **Motorwelle** (vor dem Getriebe) sitzt, und zwei um 90° versetzten Hall-Sensoren. Jeder Sensor erzeugt pro Motordrehung **11 Impulse** (Counts Per Revolution, CPR). Da sich die Signale A und B um 90° in der Phase unterscheiden (Quadratur-Encoder), ergibt sich bei Auswertung beider Flanken:

$$\text{Ticks pro Motorumdrehung} = 11\,\text{CPR} \times 4\,\text{(Quadratur)} = 44$$

Bezogen auf die **Abtriebswelle** (nach Getriebe) ergibt sich mit dem Übersetzungsverhältnis $i$:

$$\text{Ticks pro Abtriebsumdrehung} = 44 \times i$$

Für die Variante 1:100 bedeutet das: **4.400 Ticks pro Radumdrehung** – eine Auflösung, die für die Odometrie einer mobilen Plattform mehr als ausreichend ist.

#### 3.3.2 Quadratur-Signaldiagramm

```
Drehrichtung: VORWÄRTS (A führt vor B)

Encoder A  ──┐   ┌───┐   ┌───┐   ┌───┐   ┌───
             │   │   │   │   │   │   │   │
             └───┘   └───┘   └───┘   └───┘

Encoder B  ────┐   ┌───┐   ┌───┐   ┌───┐   ┌─
               │   │   │   │   │   │   │   │
               └───┘   └───┘   └───┘   └───┘
           ◄──── 90° Phasenversatz ────►

Drehrichtung: RÜCKWÄRTS (B führt vor A)

Encoder B  ──┐   ┌───┐   ┌───┐   ┌───
             │   │   │   │   │   │
             └───┘   └───┘   └───┘

Encoder A  ────┐   ┌───┐   ┌───┐   ┌─
               │   │   │   │   │   │
               └───┘   └───┘   └───┘
```

**Richtungserkennung:** Bei steigender Flanke von A gilt: Wenn B = Low → Vorwärts; wenn B = High → Rückwärts.

#### 3.3.3 Encoder-Spezifikationen

| Parameter | Wert |
|---|---|
| **Encodertyp** | Inkremental, magnetischer Quadratur-Hall-Encoder |
| **Magnetscheibe** | 22 Pole (11 Polpaare) |
| **Hall-Sensoren** | 2 (Phase A und Phase B, 90° Versatz) |
| **CPR (Counts Per Revolution)** | 11 (pro Kanal, auf Motorwelle) |
| **Quadratur-Ticks/Umdrehung** | 44 (bei 4× Dekodierung, Motorwelle) |
| **Versorgungsspannung** | 3,3 … 5,0 V DC |
| **Signalpegel Ausgang** | Digitales Rechtecksignal (Push-Pull) |
| **High-Pegel** | ≈ V_encoder (3,3 V oder 5 V) |
| **Low-Pegel** | ≈ 0 V |
| **Max. Impulsfrequenz** (Motorwelle @ 10.000 RPM) | ~1,8 kHz pro Kanal |

### 3.4 Kabelfarben und Anschluss (6-Pin JST-PH)

| Pin | Kabelfarbe | Funktion | Anschluss |
|---|---|---|---|
| 1 | **Rot** | Motor + (M+) | MDD3A: Motor-Ausgang A |
| 2 | **Weiß** | Motor − (M−) | MDD3A: Motor-Ausgang B |
| 3 | **Gelb** | Encoder Phase A | ESP32-S3: GPIO-Interrupt-Pin |
| 4 | **Grün** | Encoder Phase B | ESP32-S3: GPIO-Interrupt-Pin |
| 5 | **Blau** | Encoder V+ (3,3 … 5 V) | 3,3 V vom ESP32-S3 (oder 5VO vom MDD3A) |
| 6 | **Schwarz** | Encoder GND | Gemeinsame Masse (GND) |

> **Kabelfarben-Varianten:** Verschiedene Hersteller und Chargen können abweichende Farbkodierungen verwenden. Die obige Tabelle beschreibt die häufigste Belegung. **Vor dem Anschluss** sollte die Zuordnung mit einem Multimeter (Durchgangsprüfung Motor-Pins) und einem Oszilloskop/Logic-Analyzer (Encoder-Signale) verifiziert werden.

> **Encoder-Versorgung:** Bei Anschluss an 3,3 V liefert der Encoder 3,3-V-Logikpegel, die direkt ESP32-S3-kompatibel sind. Bei 5-V-Versorgung (über 5VO des MDD3A) liegt der High-Pegel bei ~5 V – dieser Pegel ist für den ESP32-S3 (max. 3,3 V an GPIO) **nicht zulässig** und erfordert einen Pegelwandler oder einen Spannungsteiler.

---

## 4 Verkabelung – Gesamtsystem

### 4.1 Anschlussplan

```
3S-LiPo (9,0 … 12,6 V)
    │  (+) ─────────────── VB+ ┐
    │  (−) ─────────────── VB- ┤ Cytron MDD3A
    │                          │
    │                     ┌────┴────────────────────────────┐
    │                     │  Signal-Header:                 │
    │                     │  M1A ◄── GPIO1 (D0) [PWM_L]   │
    │                     │  M1B ◄── GPIO2 (D1) [DIR_L]   │
    │                     │  5VO ──► (nicht verwendet)      │
    │                     │  GND ──► GND (gemeinsam)        │
    │                     │  M2A ◄── GPIO3 (D2) [PWM_R]   │
    │                     │  M2B ◄── GPIO4 (D3) [DIR_R]   │
    │                     └────┬────────────────────────────┘
    │                          │
    │         Motor-Klemmen:   │
    │    ┌─────────────────────┼─────────────────────┐
    │    │                     │                     │
    │  ┌─┴──────────┐       ┌─┴──────────┐         │
    │  │ Motor 1 (L) │       │ Motor 2 (R) │         │
    │  │ Rot ── OUT1A│       │ Rot ── OUT2A│         │
    │  │ Weiß── OUT1B│       │ Weiß── OUT2B│         │
    │  │             │       │             │         │
    │  │ Gelb ──► GPIO5 (D4) │ Gelb ──► GPIO7 (D6)  │
    │  │ Grün ──► GPIO6 (D5) │ Grün ──► GPIO8 (D7)  │ ← ESP32-S3
    │  │ Blau ──► 3V3        │ Blau ──► 3V3         │
    │  │ Schwarz► GND        │ Schwarz► GND         │
    │  └─────────────┘       └─────────────┘         │
    │                                                │
    └────────────────────────────────────────────────┘
                        GND (gemeinsam)
```

### 4.2 Pinzuordnung ESP32-S3 (XIAO)

| Funktion | XIAO-Pin | ESP32-S3 GPIO | Peripherie |
|---|---|---|---|
| PWM Motor Links | D0 | GPIO1 | LEDC Kanal 0 |
| DIR Motor Links | D1 | GPIO2 | Digital Output |
| PWM Motor Rechts | D2 | GPIO3 | LEDC Kanal 1 |
| DIR Motor Rechts | D3 | GPIO4 | Digital Output |
| Encoder L – Phase A | D4 | GPIO5 | Interrupt (RISING/CHANGE) |
| Encoder L – Phase B | D5 | GPIO6 | Interrupt (RISING/CHANGE) |
| Encoder R – Phase A | D6 | GPIO43 | Interrupt (RISING/CHANGE) |
| Encoder R – Phase B | D7 | GPIO44 | Interrupt (RISING/CHANGE) |

> **Strapping-Pins:** GPIO43 (D6) und GPIO44 (D7) sind Strapping-Pins (TX/RX des UART0). Da die USB-CDC-Schnittstelle für micro-ROS genutzt wird und UART0 nicht benötigt wird, können diese Pins für Encoder-Eingänge verwendet werden. Falls Konflikte auftreten, stehen D8 (GPIO7) und D9 (GPIO8) als Alternativen zur Verfügung.

### 4.3 Masseführung

Alle GND-Verbindungen – Batterie, MDD3A, ESP32-S3, Encoder – müssen auf einem gemeinsamen Massepotenzial liegen. Eine sternförmige Masseführung vom MDD3A-GND-Pin minimiert Störströme:

```
             MDD3A GND (Sternpunkt)
            ┌──────┼──────┐
            │      │      │
        Batterie  ESP32  Encoder
          GND     GND    GND (×2)
```

---

## 5 Firmware – ESP32-S3 (micro-ROS)

### 5.1 Motor-Steuerung (Sign-Magnitude PWM)

```cpp
// motor_driver.h
#pragma once
#include <Arduino.h>

// --- Pin-Definitionen ---
#define PIN_PWM_L   1   // D0 = GPIO1 → MDD3A M1A
#define PIN_DIR_L   2   // D1 = GPIO2 → MDD3A M1B
#define PIN_PWM_R   3   // D2 = GPIO3 → MDD3A M2A
#define PIN_DIR_R   4   // D3 = GPIO4 → MDD3A M2B

// --- PWM-Konfiguration (ESP32-S3 LEDC) ---
#define PWM_FREQ      10000   // 10 kHz (unhörbar, im MDD3A-Bereich)
#define PWM_RESOLUTION    8   // 8-bit → 0 … 255
#define PWM_CHANNEL_L     0
#define PWM_CHANNEL_R     1

class MotorDriver {
public:
    void begin() {
        // LEDC-PWM initialisieren
        ledcSetup(PWM_CHANNEL_L, PWM_FREQ, PWM_RESOLUTION);
        ledcSetup(PWM_CHANNEL_R, PWM_FREQ, PWM_RESOLUTION);
        ledcAttachPin(PIN_PWM_L, PWM_CHANNEL_L);
        ledcAttachPin(PIN_PWM_R, PWM_CHANNEL_R);

        // Richtungs-Pins
        pinMode(PIN_DIR_L, OUTPUT);
        pinMode(PIN_DIR_R, OUTPUT);

        // Motoren stoppen
        stop();
    }

    // Geschwindigkeit: -255 … +255 (negativ = rückwärts)
    void setMotorL(int16_t speed) {
        setMotor(PWM_CHANNEL_L, PIN_DIR_L, speed);
    }

    void setMotorR(int16_t speed) {
        setMotor(PWM_CHANNEL_R, PIN_DIR_R, speed);
    }

    void stop() {
        ledcWrite(PWM_CHANNEL_L, 0);
        ledcWrite(PWM_CHANNEL_R, 0);
        digitalWrite(PIN_DIR_L, LOW);
        digitalWrite(PIN_DIR_R, LOW);
    }

    // Bremse (aktive Kurzschlussbremse über H-Brücke)
    void brake() {
        // Beide Eingänge High → Motorausgang kurzgeschlossen
        ledcWrite(PWM_CHANNEL_L, 255);
        digitalWrite(PIN_DIR_L, HIGH);
        ledcWrite(PWM_CHANNEL_R, 255);
        digitalWrite(PIN_DIR_R, HIGH);
    }

private:
    void setMotor(uint8_t channel, uint8_t dirPin, int16_t speed) {
        speed = constrain(speed, -255, 255);
        if (speed >= 0) {
            digitalWrite(dirPin, LOW);        // Vorwärts: MxB = LOW
            ledcWrite(channel, speed);        // MxA = PWM
        } else {
            digitalWrite(dirPin, HIGH);       // Rückwärts: MxB = HIGH (PWM via MxA)
            ledcWrite(channel, -speed);       // MxA = PWM (Betrag)
        }
    }
};
```

> **Alternativer Steuerungsmodus (Lock-Antiphase):** Statt Sign-Magnitude kann auch Lock-Antiphase verwendet werden, bei dem beide Eingänge mit komplementären PWM-Signalen angesteuert werden. 50 % Duty Cycle = Stillstand, < 50 % = rückwärts, > 50 % = vorwärts. Dieser Modus ist für einfache Steuerung (ein PWM-Pin pro Motor) geeignet, erzeugt aber höheren Rippelstrom im Motor.

### 5.2 Encoder-Auswertung (Quadratur-Decoder)

```cpp
// encoder.h
#pragma once
#include <Arduino.h>

// --- Pin-Definitionen ---
#define PIN_ENC_L_A   5   // D4 = GPIO5
#define PIN_ENC_L_B   6   // D5 = GPIO6
#define PIN_ENC_R_A  43   // D6 = GPIO43
#define PIN_ENC_R_B  44   // D7 = GPIO44

class QuadratureEncoder {
public:
    // Encoder-Zähler (Interrupt-sicher via volatile)
    volatile int32_t ticks_left  = 0;
    volatile int32_t ticks_right = 0;

    void begin() {
        pinMode(PIN_ENC_L_A, INPUT_PULLUP);
        pinMode(PIN_ENC_L_B, INPUT_PULLUP);
        pinMode(PIN_ENC_R_A, INPUT_PULLUP);
        pinMode(PIN_ENC_R_B, INPUT_PULLUP);

        // Interrupts auf steigende Flanke von Phase A
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_L_A),
            std::bind(&QuadratureEncoder::isr_left, this), RISING);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_R_A),
            std::bind(&QuadratureEncoder::isr_right, this), RISING);
    }

    // Zähler auslesen und atomar zurücksetzen
    int32_t readAndResetLeft() {
        noInterrupts();
        int32_t val = ticks_left;
        ticks_left = 0;
        interrupts();
        return val;
    }

    int32_t readAndResetRight() {
        noInterrupts();
        int32_t val = ticks_right;
        ticks_right = 0;
        interrupts();
        return val;
    }

    // Drehzahl berechnen (RPM, bezogen auf Abtriebswelle)
    // dt_ms: Zeitintervall seit letzter Abfrage in Millisekunden
    // gear_ratio: Übersetzungsverhältnis (z. B. 100)
    float calcRPM(int32_t ticks, uint32_t dt_ms, uint16_t gear_ratio) {
        // Ticks pro Abtriebsumdrehung = 44 * gear_ratio
        float ticks_per_rev = 44.0f * gear_ratio;
        float revolutions = (float)ticks / ticks_per_rev;
        float minutes = (float)dt_ms / 60000.0f;
        return (minutes > 0) ? (revolutions / minutes) : 0.0f;
    }

private:
    void IRAM_ATTR isr_left() {
        if (digitalRead(PIN_ENC_L_B)) {
            ticks_left++;   // Vorwärts
        } else {
            ticks_left--;   // Rückwärts
        }
    }

    void IRAM_ATTR isr_right() {
        if (digitalRead(PIN_ENC_R_B)) {
            ticks_right++;
        } else {
            ticks_right--;
        }
    }
};
```

> **4× Dekodierung:** Das obige Beispiel nutzt nur die steigende Flanke von Kanal A (1× oder 2× Dekodierung, je nach Richtungslogik). Für die volle 4× Quadratur-Auflösung (44 Ticks/Motorumdrehung) müssen Interrupts auf **beide Flanken** (CHANGE) **beider Kanäle** (A und B) registriert werden. Dies vervierfacht die Interrupt-Last, ist aber bei den moderaten Impulsfrequenzen des JGA25-370 (max. ~1,8 kHz pro Kanal) für den Dual-Core ESP32-S3 unkritisch.

### 5.3 PID-Drehzahlregler

```cpp
// pid_controller.h
#pragma once

class PIDController {
public:
    float kp, ki, kd;
    float integral    = 0.0f;
    float prev_error  = 0.0f;
    float output_min  = -255.0f;
    float output_max  =  255.0f;

    PIDController(float p, float i, float d)
        : kp(p), ki(i), kd(d) {}

    float compute(float setpoint, float measurement, float dt_s) {
        float error = setpoint - measurement;

        // Proportional
        float p_term = kp * error;

        // Integral (mit Anti-Windup)
        integral += error * dt_s;
        integral = constrain(integral,
            output_min / (ki > 0 ? ki : 1.0f),
            output_max / (ki > 0 ? ki : 1.0f));
        float i_term = ki * integral;

        // Differential
        float derivative = (dt_s > 0) ? (error - prev_error) / dt_s : 0.0f;
        float d_term = kd * derivative;
        prev_error = error;

        // Ausgabe begrenzen
        float output = p_term + i_term + d_term;
        return constrain(output, output_min, output_max);
    }

    void reset() {
        integral   = 0.0f;
        prev_error = 0.0f;
    }
};
```

### 5.4 Integration: Closed-Loop-Motorsteuerung via micro-ROS

```cpp
// main.cpp – Vollständige Closed-Loop-Motorsteuerung
#include <Arduino.h>
#include <micro_ros_platformio.h>

#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <geometry_msgs/msg/twist.h>
#include <std_msgs/msg/float32_multi_array.h>

#include "motor_driver.h"
#include "encoder.h"
#include "pid_controller.h"

// --- Differentialantrieb-Parameter ---
#define WHEEL_RADIUS    0.0325f   // 65 mm Raddurchmesser → 32,5 mm Radius
#define WHEEL_BASE      0.15f     // 150 mm Achsabstand
#define GEAR_RATIO      100       // Übersetzung 1:100
#define TICKS_PER_REV   (44 * GEAR_RATIO)  // 4400 Ticks/Radumdrehung
#define CONTROL_FREQ_HZ 50        // 50 Hz Regelschleife (20 ms)

// --- Objekte ---
MotorDriver motors;
QuadratureEncoder encoders;
PIDController pid_left(2.0f, 5.0f, 0.1f);    // Startwerte, Tuning erforderlich
PIDController pid_right(2.0f, 5.0f, 0.1f);

// --- micro-ROS ---
rcl_subscription_t cmd_vel_sub;
rcl_publisher_t    odom_pub;
geometry_msgs__msg__Twist cmd_vel_msg;
std_msgs__msg__Float32MultiArray odom_msg;
float odom_data[4];  // [v_left, v_right, ticks_left, ticks_right]

rclc_executor_t executor;
rclc_support_t  support;
rcl_allocator_t allocator;
rcl_node_t      node;
rcl_timer_t     control_timer;

// --- Sollwerte (m/s) ---
float target_v_left  = 0.0f;
float target_v_right = 0.0f;

// --- Callbacks ---
void cmd_vel_callback(const void *msg_in) {
    const geometry_msgs__msg__Twist *twist =
        (const geometry_msgs__msg__Twist *)msg_in;

    float v = twist->linear.x;    // Lineargeschwindigkeit (m/s)
    float w = twist->angular.z;   // Winkelgeschwindigkeit (rad/s)

    // Differentialantrieb: Geschwindigkeit → Radgeschwindigkeiten
    target_v_left  = v - (w * WHEEL_BASE / 2.0f);
    target_v_right = v + (w * WHEEL_BASE / 2.0f);
}

void control_timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
    RCLC_UNUSED(last_call_time);
    if (timer == NULL) return;

    float dt_s = 1.0f / CONTROL_FREQ_HZ;

    // Encoder auslesen
    int32_t ticks_l = encoders.readAndResetLeft();
    int32_t ticks_r = encoders.readAndResetRight();

    // Ist-Geschwindigkeit berechnen (m/s)
    float v_left  = ((float)ticks_l / TICKS_PER_REV) *
                    (2.0f * PI * WHEEL_RADIUS) / dt_s;
    float v_right = ((float)ticks_r / TICKS_PER_REV) *
                    (2.0f * PI * WHEEL_RADIUS) / dt_s;

    // PID-Regler
    float pwm_left  = pid_left.compute(target_v_left, v_left, dt_s);
    float pwm_right = pid_right.compute(target_v_right, v_right, dt_s);

    // Motoren ansteuern
    motors.setMotorL((int16_t)pwm_left);
    motors.setMotorR((int16_t)pwm_right);

    // Odometrie-Daten publizieren
    odom_data[0] = v_left;
    odom_data[1] = v_right;
    odom_data[2] = (float)ticks_l;
    odom_data[3] = (float)ticks_r;
    odom_msg.data.data = odom_data;
    odom_msg.data.size = 4;
    odom_msg.data.capacity = 4;
    rcl_publish(&odom_pub, &odom_msg, NULL);
}

void setup() {
    // Hardware initialisieren
    motors.begin();
    encoders.begin();

    // micro-ROS Serial Transport
    Serial.begin(115200);
    set_microros_serial_transports(Serial);
    delay(2000);

    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "amr_drive_node", "", &support);

    // Subscriber: cmd_vel
    rclc_subscription_init_default(&cmd_vel_sub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
        "cmd_vel");

    // Publisher: Odometrie (Radgeschwindigkeiten + Ticks)
    rclc_publisher_init_default(&odom_pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32MultiArray),
        "mcu/wheel_odom");

    // Timer: Regelschleife @ 50 Hz
    rclc_timer_init_default(&control_timer, &support,
        RCL_MS_TO_NS(1000 / CONTROL_FREQ_HZ),
        control_timer_callback);

    // Executor: 1 Timer + 1 Subscriber = 2 Handles
    rclc_executor_init(&executor, &support.context, 2, &allocator);
    rclc_executor_add_timer(&executor, &control_timer);
    rclc_executor_add_subscription(&executor, &cmd_vel_sub,
        &cmd_vel_msg, &cmd_vel_callback, ON_NEW_DATA);
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
}
```

### 5.5 PID-Tuning

Die PID-Parameter ($K_p$, $K_i$, $K_d$) müssen empirisch am realen System bestimmt werden. Ein systematisches Vorgehen:

1. **$K_i = 0$, $K_d = 0$ setzen.** $K_p$ schrittweise erhöhen, bis der Motor bei Sollwert-Sprung schnell reagiert, aber noch nicht schwingt.
2. **$K_i$ langsam erhöhen,** bis der stationäre Regelfehler (Steady-State Error) verschwindet.
3. **$K_d$ vorsichtig hinzufügen,** um Überschwingen zu dämpfen.
4. Typische Startwerte für JGA25-370 @ 12 V mit 1:100 Getriebe: $K_p \approx 1{,}5 … 3{,}0$, $K_i \approx 3{,}0 … 8{,}0$, $K_d \approx 0{,}05 … 0{,}2$.

Über micro-ROS können die PID-Parameter zur Laufzeit als ROS-2-Parameter exponiert und per `ros2 param set` angepasst werden, ohne die Firmware neu flashen zu müssen.

---

## 6 Inbetriebnahme

### 6.1 Schritt-für-Schritt-Prüfung

```bash
# 1. MDD3A ohne MCU testen (Test-Tasten auf dem Board)
#    → Batterie anschließen (12 V)
#    → Power-LED leuchtet
#    → Taste M1A drücken → Motor 1 dreht vorwärts, LED M1A leuchtet
#    → Taste M1B drücken → Motor 1 dreht rückwärts, LED M1B leuchtet
#    → Gleiches für Motor 2 (M2A, M2B)

# 2. Encoder prüfen (Motor manuell drehen oder über Test-Tasten)
#    → Logic Analyzer oder Oszilloskop an Encoder A und B
#    → Rechtecksignale mit 90° Phasenversatz sichtbar?
#    → 11 Impulse pro Motorumdrehung?

# 3. Firmware flashen und micro-ROS Agent starten
pio run --target upload
docker run -it --rm -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:humble serial --dev /dev/ttyACM0 -v6

# 4. Topics prüfen
ros2 topic list
# /cmd_vel
# /mcu/wheel_odom

# 5. Motoren testen (langsam vorwärts: 0,1 m/s)
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.1}, angular: {z: 0.0}}"

# 6. Encoder-Rückmeldung prüfen
ros2 topic echo /mcu/wheel_odom
# data: [0.098, 0.102, 44.0, 45.0]
#         v_left v_right ticks_l ticks_r

# 7. Stoppen
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

### 6.2 Sicherheits-Checkliste

- [ ] Batteriepolarität VB+/VB− am MDD3A korrekt?
- [ ] Encoder-Versorgung 3,3 V (nicht 5 V!) an ESP32-S3?
- [ ] Gemeinsame Masse zwischen Batterie, MDD3A, ESP32-S3, Encoder?
- [ ] Motorkabel fest in Schraubklemmen des MDD3A?
- [ ] Software-Stall-Schutz implementiert (Timeout bei blockiertem Motor)?
- [ ] PWM-Frequenz ≤ 20 kHz (MDD3A-Limit)?
- [ ] Motoren drehen bei cmd_vel in die erwartete Richtung?
- [ ] Encoder-Ticks zählen in die richtige Richtung (positiv = vorwärts)?

---

## 7 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| Motor dreht nicht | Kein PWM-Signal am MDD3A | GPIO-Zuordnung prüfen; `ledcAttachPin` korrekt? |
| Motor dreht nicht | Batteriespannung < 4 V | Batterie laden; UVLO des MDD3A aktiv |
| Motor dreht nur in eine Richtung | DIR-Pin nicht korrekt geschaltet | Wahrheitstabelle prüfen; MxB-Anschluss kontrollieren |
| Motor dreht falsch herum | Motoranschluss vertauscht | Motor-Kabel (Rot/Weiß) an MDD3A-Klemme tauschen |
| Encoder zeigt keine Impulse | Encoder-Versorgung fehlt | 3,3 V und GND am Encoder prüfen |
| Encoder zeigt nur einen Kanal | Kabelbruch oder Pin-Fehler | Kabel durchmessen; GPIO-Zuordnung prüfen |
| Encoder zählt falsche Richtung | A/B vertauscht oder Polarität | Gelb und Grün tauschen oder Software-Vorzeichen invertieren |
| Regelung schwingt stark | PID-Parameter zu aggressiv | $K_p$ reduzieren; $K_d$ erhöhen |
| Stationärer Regelfehler | $K_i$ zu niedrig | $K_i$ schrittweise erhöhen |
| MDD3A wird heiß | Dauerhaft > 3 A Motorstrom | Last reduzieren; Stall-Erkennung implementieren |
| ESP32-S3 GPIO beschädigt | 5 V Encoder-Signal an 3,3-V-GPIO | Encoder auf 3,3 V versorgen oder Pegelwandler einsetzen |
| PWM-Pfeifen hörbar | Frequenz < 10 kHz | `PWM_FREQ` auf 15 … 20 kHz setzen |
| Encoder-Ticks springen / fehlen | Interrupt-Verlust bei hoher Last | Core-Pinning (ESP32-S3 Core 1 für ISRs); `IRAM_ATTR` prüfen |
| 5VO-Ausgang liefert keine Spannung | MDD3A nicht versorgt oder defekt | V_in am MDD3A messen; min. 4 V erforderlich |

---

## 8 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   AMR-Antriebssystem – Kurzprofil                                       │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   MOTOR-TREIBER (MDD3A)     │                                           │
│   Hersteller                 │ Cytron Technologies                       │
│   Topologie                  │ Diskrete MOSFET-H-Brücke (2 Kanäle)     │
│   Versorgungsspannung        │ 4 … 16 V DC                              │
│   Motorstrom (kontinuierlich)│ 3 A pro Kanal                            │
│   Motorstrom (Spitze, < 5 s)│ 5 A pro Kanal                            │
│   Logikpegel                 │ 1,7 … 12 V (High), kompatibel 3,3 V    │
│   PWM-Frequenz               │ DC … 20 kHz                              │
│   Steuerungsmodi             │ Sign-Magnitude, Lock-Antiphase           │
│   5-V-Ausgang                │ 200 mA (Buck-Boost ab V_in ≥ 4 V)      │
│   Schutzfunktionen           │ Verpolungsschutz, Überstrom, Thermisch  │
│                              │                                           │
│   MOTOREN (JGA25-370 × 2)   │                                           │
│   Typ                        │ Bürstenmotor + Metallgetriebe             │
│   Nennspannung               │ 12 V DC                                  │
│   Leistung                   │ ~3 W                                     │
│   Übersetzung (empfohlen)    │ 1:100                                    │
│   Leerlaufdrehzahl           │ ~130 RPM (±15 %)                        │
│   Stall-Drehmoment           │ ~16 kg·cm                                │
│   Stall-Strom                │ ~2,5 … 3,0 A                            │
│   Wellendurchmesser          │ 4 mm (D-Abflachung)                     │
│   Gehäusedurchmesser         │ 25 mm                                    │
│                              │                                           │
│   ENCODER (integriert × 2)   │                                           │
│   Typ                        │ Magnetischer Quadratur-Hall-Encoder      │
│   CPR (auf Motorwelle)       │ 11                                        │
│   Quadratur-Ticks/Motordrehung│ 44 (4× Dekodierung)                    │
│   Ticks/Abtriebsumdrehung    │ 4.400 (bei 1:100)                       │
│   Versorgungsspannung        │ 3,3 … 5 V                               │
│   Signalpegel                │ Push-Pull, V_encoder                     │
│   Anschluss                  │ 6-Pin JST-PH                             │
│                              │                                           │
│   AMR-KINEMATIK (Beispiel)   │                                           │
│   Raddurchmesser             │ 65 mm                                    │
│   Achsabstand                │ 150 mm                                   │
│   Max. Geschwindigkeit       │ ~0,44 m/s (bei 130 RPM)                 │
│   Encoder-Auflösung (Weg)    │ ~0,046 mm/Tick (bei 65 mm Rad)          │
│   Regelfrequenz              │ 50 Hz                                     │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: Cytron MDD3A Datasheet Rev 1.0 (März 2019), Cytron Produktseite, CytronMotorDriver Library (GitHub), JGA25-370 Encoder Pinout (abra-electronics), JGA25-370 Spezifikationen (PMD, LK Tronics, PixelElectric), ESP32-S3 Datasheet (Espressif)*
