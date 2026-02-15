---
title: "Hardware Setup – AMR Platform"
file: "docs/hardware-setup.md"
status: "active"
updated: "2025-12-19"
scope: "Projekt-Nachschlagewerk (Master-grade Design)"
---

# Hardware Setup – AMR Platform

Dieses Dokument beschreibt den **physischen Aufbau** (Stromversorgung, Verkabelung, Pin-Mapping, Inbetriebnahme-Messpunkte) für den AMR-Stack mit:

- **Raspberry Pi 5** (Host: ROS 2 in Docker)
- **Seeed XIAO ESP32-S3** (Motor/Encoder/Realtime, micro-ROS Client)
- **Cytron MDD3A** (Dual-Motor-Treiber, Dual-PWM)
- **JGA25-370 12 V + Hall-Encoder** (2×)
- **RPLidar A1** (USB, `/scan`)
- Optional: **Hailo-8L AI Kit (PCIe)**, **Global Shutter Camera (CSI)**, **Pan/Tilt (2× Servo)**

> Schaltpläne: `docs/schaltplan.pdf` (Power-Topologie + XIAO/MDD3A Pinout + MOSFET Low-Side).

---

## 1) Systemübersicht (Daten- & Leistungsfluss)

### 1.1 Blockdiagramm (logisch)

```mermaid
flowchart LR
  BAT[3S Li-Ion Pack\n11.1–12.6 V] --> BMS[BMS 3S 25 A\nBalancer]
  BMS --> FUSE[Hauptsicherung\n15 A]
  FUSE --> RAIL12[12 V Rail]

  RAIL12 --> MDD3A[Cytron MDD3A\nMotor Driver]
  MDD3A --> M1[JGA25-370 Motor L]
  MDD3A --> M2[JGA25-370 Motor R]

  RAIL12 --> BUCKPI[DC/DC USB-C\n5 V / 5 A (25 W)]
  BUCKPI --> PI[Raspberry Pi 5]

  RAIL12 --> BUCKSERVO[DC/DC (z.B. LM2596)\n5 V für Servos]
  BUCKSERVO --> SERVO[Pan/Tilt Servos (optional)]

  PI -->|USB| ESP[XIAO ESP32-S3]
  PI -->|USB| LIDAR[RPLidar A1]
  PI -->|CSI| CAM[Global Shutter Camera (optional)]
  PI -->|PCIe| HAILO[Hailo-8L (optional)]
```

### 1.2 Design-Regel (robust)

- **12 V Rail** für Motoren + ggf. LED/Lasten.
- **5 V Rail** **separat** (Pi via USB-C buck), damit Motorstromspitzen nicht den Pi resetten.
- **Sternpunkt-Masse**: ein definierter Rückstrompunkt für „Power-GND“, von dort sternförmig zu Pi-Buck, Servo-Buck, Motortreiber und ESP32.

---

## 2) Stromversorgung & Schutz

### 2.1 Spannungsbereiche (3S Li-Ion)

- Voll: ca. $12{,}6\,\mathrm{V}$` (3 × 4.2 V)
- Nenn: ca. $11{,}1\,\mathrm{V}$` (3 × 3.7 V)
- Unter Last: abhängig von Innenwiderstand; BMS-Low-Voltage-Cutoff je nach Board.

### 2.2 Sicherung & Hauptschalter

- **Hauptsicherung** nahe Akku: **`15\,\mathrm{A}`** (aus Schaltplan)
- Hauptschalter in Serie zur 12-V-Rail (Mechanik/Bedienbarkeit: gut erreichbar).

### 2.3 DC/DC-Auslegung

**Pi 5:**

- Ziel: **`5\,\mathrm{V}`**, stabil, ausreichend für Pi 5 + USB-Peripherie.
- Richtwert: **`5\,\mathrm{A}`** (USB-C Buck 25 W).

**Servos (optional):**

- Eigener 5-V-Regler (LM2596 o.ä.), nicht aus dem Pi ziehen.
- Peakströme bei kleinen Servos sind kurzzeitig hoch; plane konservativ:

  - 2× MG90S: **`2\,\mathrm{A}`** Reserve sinnvoll (kurze Peaks).

### 2.4 Leitungsquerschnitte (aus Schaltplan als Richtwert)

- Akku → 12-V-Verteiler/Motortreiber: **`1{,}5\,\mathrm{mm^2}`**
- 5-V-Servo-Zuleitung: **`0{,}75\,\mathrm{mm^2}`**
- Signalleitungen (PWM/Encoder/I2C): dünn, aber sauber geführt (Twisted Pair bei Encoder hilfreich).

---

## 3) Verkabelung: „Single Source of Truth“ = `firmware/include/config.h`

**Regel:** Hardwareverdrahtung und Firmware müssen 1:1 zusammenpassen.
Wenn du Pins änderst: **erst config.h anpassen**, dann Kabel.

### 3.1 Pin-Mapping (XIAO ESP32-S3)

Aus `config.h`:

| Funktion        | XIAO Pin | Hinweis                             |
| --------------- | -------: | ----------------------------------- |
| Motor Left A    |       D0 | MDD3A M1A (Vorwärts-PWM)            |
| Motor Left B    |       D1 | MDD3A M1B (Rückwärts-PWM)           |
| Motor Right A   |       D2 | MDD3A M2A (Vorwärts-PWM)            |
| Motor Right B   |       D3 | MDD3A M2B (Rückwärts-PWM)           |
| I2C SDA         |       D4 | IMU optional (3.3 V)                |
| I2C SCL         |       D5 | IMU optional (3.3 V)                |
| Encoder Left A  |       D6 | Interrupt-fähig (A-only)            |
| Encoder Right A |       D7 | Interrupt-fähig (A-only)            |
| Servo Pan       |       D8 | nur Signal (Servo-Power extern 5 V) |
| Servo Tilt      |       D9 | nur Signal (Servo-Power extern 5 V) |
| LED/MOSFET Gate |      D10 | IRLZ24N Low-Side Switch             |

---

## 4) Motoren & Treiber (Cytron MDD3A, Dual-PWM)

### 4.1 Dual-PWM Prinzip (konsequent verdrahten)

**Regel pro Motor:**

- Vorwärts: `PWM_A > 0`, `PWM_B = 0`
- Rückwärts: `PWM_A = 0`, `PWM_B > 0`

Damit brauchst du **keine DIR-Pins**, aber **2× PWM pro Motor** (D0–D3).

### 4.2 Kabelfarben (aus Schaltplan, empfehlenswerte Konvention)

| Signal                | XIAO Pin | Kabelfarbe (Signal) | Ziel am Treiber |
| --------------------- | -------: | ------------------- | --------------- |
| Motor Links Signal A  |       D0 | Rot                 | M1A             |
| Motor Links Signal B  |       D1 | Weiß                | M1B             |
| Motor Rechts Signal A |       D2 | Rot                 | M2A             |
| Motor Rechts Signal B |       D3 | Weiß                | M2B             |

> Praxis: Beschrifte beide Enden (Heatshrink-Lable), nicht nur „Farben merken“.

---

## 5) Encoder (A-only) – robust & einfach

### 5.1 Encoder-Wiring (6-adrig Motor+Encoder typisch)

Bei JGA25-370 mit Hall-Encoder sind typischerweise:

- 2 Leitungen Motor
- 4 Leitungen Encoder (VCC, GND, A, B)

**A-only-Konzept (dein Phase-1/4-Design):**

- Verbinde **nur Phase A** zu D6/D7.
- **Phase B** bleibt ungenutzt (isolieren).

Aus Schaltplan-Tabelle:

- Encoder Phase A (Links): **D6**, **Gelb**
- Encoder Phase A (Rechts): **D7**, **Gelb**
- Hinweis: „Nur Gelb anschließen! Grün isolieren.“

### 5.2 Encoder-Versorgung (entscheidend)

- Encoder braucht **VCC + GND** zusätzlich zur Signalleitung.
- Ziel ist **sauberer Logikpegel** am ESP32 (3.3 V).

**Empfehlung:**

- Wenn Encoder mit **3.3 V** stabil funktioniert: VCC = 3.3 V.
- Falls Encoder **5 V** benötigt: VCC = 5 V, dann **Pegelanpassung** fürs A-Signal (Level Shifter oder Spannungsteiler), um ESP32-Pins zu schützen.

---

## 6) I2C / IMU (optional in Phase 1, wichtig ab Phase 4)

- I2C liegt auf **D4 (SDA)** und **D5 (SCL)**.
- I2C-Versorgung **3.3 V** (Schaltplan-Hinweis).
- Leitungslängen kurz halten; bei Störungen: 100 nF nahe IMU, ggf. 2.2–4.7 kΩ Pullups (nur einmal im Bus).

---

## 7) Servos (Pan/Tilt)

- **Signal**: D8 (Pan), D9 (Tilt)
- **Power**: externes **5 V** (eigener Buck), **nicht** aus ESP32 oder Pi-5V ziehen.
- Masse muss gemeinsam sein: Servo-GND an Sternpunkt-GND, Signal-GND referenziert.

---

## 8) LEDs / Zusatzlasten über MOSFET (Low-Side)

### 8.1 Schaltung (IRLZ24N, Low-Side)

- Last an **+12 V**, MOSFET schaltet **Masse** (Low-Side).
- Gate vom ESP32 (D10), **Pulldown** `100\,\mathrm{k\Omega}` auf GND (damit beim Boot aus).

### 8.2 Freilaufdiode (nur für induktive Lasten)

- Für DC-Motor / Relais / Spule: **Diode parallel zur Last** (z.B. 1N4007 im Schaltplan-Hinweis).
- Für reine LED-Last (ohne Induktivität): keine Freilaufdiode nötig.

---

## 9) Raspberry Pi 5: Peripherie & USB-Topologie

### 9.1 USB (empfohlen)

- ESP32-S3 per USB (CDC): `/dev/ttyACM*`
- RPLidar A1 per USB: häufig `/dev/ttyUSB*` oder `/dev/ttyACM*` (adapterabhängig)

**Regel:** Für Stabilität über Reboots:

- udev-Regeln verwenden (serielle Geräte per VID/PID/Serial auf Alias verlinken), z.B. `/dev/amr_esp32`, `/dev/amr_lidar`.

### 9.2 Optionale Module

- **Hailo-8L** via PCIe (AI Kit)
- **Global Shutter Camera** via CSI
- Achte auf mechanische Entlastung der Flachbandkabel (CSI) und ausreichende Kühlung.

---

## 10) Inbetriebnahme: Messpunkte & Checkliste

### 10.1 Power-Checks (vor erstem Boot)

- [ ] Akku: $11{,}1\text{–}12{,}6\,\mathrm{V}$ am 12-V-Rail
- [ ] Sicherung sitzt nahe Akku, korrekt dimensioniert (15 A)
- [ ] Buck Pi: $5{,}1\pm 0{,}1\,\mathrm{V}$ **unter Last** (Pi bootet, USB steckt)
- [ ] Servo-Buck (optional): $5{,}0\pm 0{,}2\,\mathrm{V}$
- [ ] Gemeinsame Masse: Pi-GND, Buck-GND, Motortreiber-GND, ESP32-GND verbunden

### 10.2 Motor-Checks (ohne ROS)

- [ ] Motortreiber bekommt 12 V
- [ ] PWM-Pins korrekt (D0–D3)
- [ ] Drehrichtung plausibel (Vorwärts = beide Räder vorwärts)

### 10.3 Encoder-Checks

- [ ] Encoder-VCC/GND vorhanden
- [ ] Phase A am richtigen Pin (D6/D7)
- [ ] Zählen stabil bei langsamer Drehung (keine „Spikes“ bei Stillstand)

### 10.4 Lidar-Checks

- [ ] Gerät enumeriert am Pi (`lsusb`)
- [ ] `/scan` lässt sich erzeugen (Phase 3 Doku)
- [ ] Mechanische Lage: LiDAR hoch genug, keine Kabel im Scanbereich

---

## 11) Firmware-relevante Hardware-Parameter (aus `config.h`)

Diese Werte definieren indirekt Hardware-Annahmen (Tuning/Mechanik):

- Failsafe Timeout: `FAILSAFE_TIMEOUT_MS = 1000`
- Loop Rate: `LOOP_RATE_HZ = 100`
- PWM Deadzone: `PWM_DEADZONE = 35`
- Wheel Diameter: `WHEEL_DIAMETER = 0.065`
- Wheel Base: `WHEEL_BASE = 0.178`
- Ticks/Rev (kalibriert):

  - `TICKS_PER_REV_LEFT = 374.3`
  - `TICKS_PER_REV_RIGHT = 373.6`

**Regel:** Wenn du Räder, Getriebe oder Encoder-Setup änderst → diese Parameter neu kalibrieren.

---

## 12) Ablage im Repo (PR-freundlich)

Empfohlen:

- `docs/hardware-setup.md` (dieses Dokument)
- `docs/schaltplan.pdf` (Schaltplan)
- `firmware/include/config.h` (Pin-Mapping + Parameter)
- `docs/kosten.md` (Kosten/Teileliste)

---

## Anhang A: Quick-Entscheidungen (für Zukunftssicherheit)

- **12 V Motor-Rail** (3S) beibehalten → kompatibel zu vielen DC-Motoren/Peripherie.
- **Pi separat** über eigenen 5-V-Regler (USB-C, 5 A) → stabiler ROS-Host.
- **A-only Encoder** ist ok zum Start; wenn später Drift zu groß:

  - Phase B nachziehen (Quadratur) oder
  - bessere Odometrie (Radencoder höherer Auflösung / mechanische Verbesserung).
