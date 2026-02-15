---
title: "Hardware Setup - AMR Platform"
file: "hardware/docs/hardware-setup.md"
status: "active"
updated: "2025-12-19"
scope: "Projekt-Nachschlagewerk (Master-grade Design)"
---

# Hardware Setup - AMR Platform

Dieses Dokument beschreibt den **physischen Aufbau** (Stromversorgung, Verkabelung, Pin-Mapping, Inbetriebnahme-Messpunkte) fuer den AMR-Stack mit:

- **Raspberry Pi 5** (Host: ROS 2 in Docker)
- **Seeed XIAO ESP32-S3** (Motor/Encoder/Realtime, micro-ROS Client)
- **Cytron MDD3A** (Dual-Motor-Treiber, Dual-PWM)
- **JGA25-370 12 V + Hall-Encoder** (2x)
- **RPLIDAR A1** (USB, `/scan`)
- Optional: **Hailo-8L AI Kit (PCIe)**, **Global Shutter Camera (CSI)**, **Pan/Tilt (2x Servo)**

> Schaltplaene: `hardware/schaltplan.pdf` (Power-Topologie + XIAO/MDD3A Pinout + MOSFET Low-Side).

---

## 1) Systemuebersicht (Daten- & Leistungsfluss)

### 1.1 Blockdiagramm (logisch)

```mermaid
flowchart LR
  BAT[3S Li-Ion Pack\n11.1-12.6 V] --> BMS[BMS 3S 25 A\nBalancer]
  BMS --> FUSE[Hauptsicherung\n15 A]
  FUSE --> RAIL12[12 V Rail]

  RAIL12 --> MDD3A[Cytron MDD3A\nMotor Driver]
  MDD3A --> M1[JGA25-370 Motor L]
  MDD3A --> M2[JGA25-370 Motor R]

  RAIL12 --> BUCKPI[DC/DC USB-C\n5 V / 5 A (25 W)]
  BUCKPI --> PI[Raspberry Pi 5]

  RAIL12 --> BUCKSERVO[DC/DC (z.B. LM2596)\n5 V fuer Servos]
  BUCKSERVO --> SERVO[Pan/Tilt Servos (optional)]

  PI -->|USB| ESP[XIAO ESP32-S3]
  PI -->|USB| LIDAR[RPLIDAR A1]
  PI -->|CSI| CAM[Global Shutter Camera (optional)]
  PI -->|PCIe| HAILO[Hailo-8L (optional)]
```

### 1.2 Design-Regel (robust)

- **12 V Rail** fuer Motoren + ggf. LED/Lasten.
- **5 V Rail** **separat** (Pi via USB-C buck), damit Motorstromspitzen nicht den Pi zuruecksetzen.
- **Sternpunkt-Masse**: ein definierter Rueckstrompunkt fuer "Power-GND", von dort sternfoermig zu Pi-Buck, Servo-Buck, Motortreiber und ESP32.

---

## 2) Stromversorgung & Schutz

### 2.1 Spannungsbereiche (3S Li-Ion)

- Voll: ca. $12{,}6\,\mathrm{V}$` (3 x 4.2 V)
- Nenn: ca. $11{,}1\,\mathrm{V}$` (3 x 3.7 V)
- Unter Last: abhaengig von Innenwiderstand; BMS-Low-Voltage-Cutoff je nach Board.

### 2.2 Sicherung & Hauptschalter

- **Hauptsicherung** nahe Akku: **`15\,\mathrm{A}`** (aus Schaltplan)
- Hauptschalter in Serie zur 12-V-Rail (Mechanik/Bedienbarkeit: gut erreichbar).

### 2.3 DC/DC-Auslegung

**Pi 5:**

- Ziel: **`5\,\mathrm{V}`**, stabil, ausreichend fuer Pi 5 + USB-Peripherie.
- Richtwert: **`5\,\mathrm{A}`** (USB-C Buck 25 W).

**Servos (optional):**

- Eigener 5-V-Regler (LM2596 o.ae.), nicht aus dem Pi ziehen.
- Peakstroeme bei kleinen Servos sind kurzzeitig hoch; plane konservativ:

  - 2x MG90S: **`2\,\mathrm{A}`** Reserve sinnvoll (kurze Peaks).

### 2.4 Leitungsquerschnitte (aus Schaltplan als Richtwert)

- Akku -> 12-V-Verteiler/Motortreiber: **`1{,}5\,\mathrm{mm^2}`**
- 5-V-Servo-Zuleitung: **`0{,}75\,\mathrm{mm^2}`**
- Signalleitungen (PWM/Encoder/I2C): duenn, aber sauber gefuehrt (Twisted Pair bei Encoder hilfreich).

---

## 3) Verkabelung: "Single Source of Truth" = `hardware/config.h`

**Regel:** Hardwareverdrahtung und Firmware muessen 1:1 zusammenpassen.
Wenn du Pins aenderst: **erst config.h anpassen**, dann Kabel.

### 3.1 Pin-Mapping (XIAO ESP32-S3)

Aus `config.h`:

| Funktion        | XIAO Pin | Hinweis                             |
| --------------- | -------: | ----------------------------------- |
| Motor Left A    |       D0 | MDD3A M1A (Vorwaerts-PWM)           |
| Motor Left B    |       D1 | MDD3A M1B (Rueckwaerts-PWM)         |
| Motor Right A   |       D2 | MDD3A M2A (Vorwaerts-PWM)           |
| Motor Right B   |       D3 | MDD3A M2B (Rueckwaerts-PWM)         |
| I2C SDA         |       D4 | IMU optional (3.3 V)                |
| I2C SCL         |       D5 | IMU optional (3.3 V)                |
| Encoder Left A  |       D6 | Interrupt-faehig (A-only)           |
| Encoder Right A |       D7 | Interrupt-faehig (A-only)           |
| Servo Pan       |       D8 | nur Signal (Servo-Power extern 5 V) |
| Servo Tilt      |       D9 | nur Signal (Servo-Power extern 5 V) |
| LED/MOSFET Gate |      D10 | IRLZ24N Low-Side Switch             |

---

## 4) Motoren & Treiber (Cytron MDD3A, Dual-PWM)

### 4.1 Dual-PWM Prinzip (konsequent verdrahten)

**Regel pro Motor:**

- Vorwaerts: `PWM_A > 0`, `PWM_B = 0`
- Rueckwaerts: `PWM_A = 0`, `PWM_B > 0`

Damit brauchst du **keine DIR-Pins**, aber **2x PWM pro Motor** (D0-D3).

### 4.2 Kabelfarben (aus Schaltplan, empfehlenswerte Konvention)

| Signal                | XIAO Pin | Kabelfarbe (Signal) | Ziel am Treiber |
| --------------------- | -------: | ------------------- | --------------- |
| Motor Links Signal A  |       D0 | Rot                 | M1A             |
| Motor Links Signal B  |       D1 | Weiss               | M1B             |
| Motor Rechts Signal A |       D2 | Rot                 | M2A             |
| Motor Rechts Signal B |       D3 | Weiss               | M2B             |

> Praxis: Beschrifte beide Enden (Heatshrink-Label), nicht nur "Farben merken".

---

## 5) Encoder (A-only) - robust & einfach

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
- Hinweis: "Nur Gelb anschliessen! Gruen isolieren."

### 5.2 Encoder-Versorgung (entscheidend)

- Encoder braucht **VCC + GND** zusaetzlich zur Signalleitung.
- Ziel ist **sauberer Logikpegel** am ESP32 (3.3 V).

**Empfehlung:**

- Wenn Encoder mit **3.3 V** stabil funktioniert: VCC = 3.3 V.
- Falls Encoder **5 V** benoetigt: VCC = 5 V, dann **Pegelanpassung** fuers A-Signal (Level Shifter oder Spannungsteiler), um ESP32-Pins zu schuetzen.

---

## 6) I2C / IMU (optional in Phase 1, wichtig ab Phase 4)

- I2C liegt auf **D4 (SDA)** und **D5 (SCL)**.
- I2C-Versorgung **3.3 V** (Schaltplan-Hinweis).
- Leitungslaengen kurz halten; bei Stoerungen: 100 nF nahe IMU, ggf. 2.2-4.7 kOhm Pullups (nur einmal im Bus).

---

## 7) Servos (Pan/Tilt)

- **Signal**: D8 (Pan), D9 (Tilt)
- **Power**: externes **5 V** (eigener Buck), **nicht** aus ESP32 oder Pi-5V ziehen.
- Masse muss gemeinsam sein: Servo-GND an Sternpunkt-GND, Signal-GND referenziert.

---

## 8) LEDs / Zusatzlasten ueber MOSFET (Low-Side)

### 8.1 Schaltung (IRLZ24N, Low-Side)

- Last an **+12 V**, MOSFET schaltet **Masse** (Low-Side).
- Gate vom ESP32 (D10), **Pulldown** `100\,\mathrm{k\Omega}` auf GND (damit beim Boot aus).

### 8.2 Freilaufdiode (nur fuer induktive Lasten)

- Fuer DC-Motor / Relais / Spule: **Diode parallel zur Last** (z.B. 1N4007 im Schaltplan-Hinweis).
- Fuer reine LED-Last (ohne Induktivitaet): keine Freilaufdiode noetig.

---

## 9) Raspberry Pi 5: Peripherie & USB-Topologie

### 9.1 USB (empfohlen)

- ESP32-S3 per USB (CDC): `/dev/ttyACM*`
- RPLIDAR A1 per USB: haeufig `/dev/ttyUSB*` oder `/dev/ttyACM*` (adapterabhaengig)

**Regel:** Fuer Stabilitaet ueber Reboots:

- udev-Regeln verwenden (serielle Geraete per VID/PID/Serial auf Alias verlinken), z.B. `/dev/amr_esp32`, `/dev/amr_lidar`.

### 9.2 Optionale Module

- **Hailo-8L** via PCIe (AI Kit)
- **Global Shutter Camera** via CSI
- Achte auf mechanische Entlastung der Flachbandkabel (CSI) und ausreichende Kuehlung.

---

## 10) Inbetriebnahme: Messpunkte & Checkliste

### 10.1 Power-Checks (vor erstem Boot)

- [ ] Akku: $11{,}1\text{-}12{,}6\,\mathrm{V}$ am 12-V-Rail
- [ ] Sicherung sitzt nahe Akku, korrekt dimensioniert (15 A)
- [ ] Buck Pi: $5{,}1\pm 0{,}1\,\mathrm{V}$ **unter Last** (Pi bootet, USB steckt)
- [ ] Servo-Buck (optional): $5{,}0\pm 0{,}2\,\mathrm{V}$
- [ ] Gemeinsame Masse: Pi-GND, Buck-GND, Motortreiber-GND, ESP32-GND verbunden

### 10.2 Motor-Checks (ohne ROS)

- [ ] Motortreiber bekommt 12 V
- [ ] PWM-Pins korrekt (D0-D3)
- [ ] Drehrichtung plausibel (Vorwaerts = beide Raeder vorwaerts)

### 10.3 Encoder-Checks

- [ ] Encoder-VCC/GND vorhanden
- [ ] Phase A am richtigen Pin (D6/D7)
- [ ] Zaehlen stabil bei langsamer Drehung (keine "Spikes" bei Stillstand)

### 10.4 Lidar-Checks

- [ ] Geraet enumeriert am Pi (`lsusb`)
- [ ] `/scan` laesst sich erzeugen (Phase 3 Doku)
- [ ] Mechanische Lage: LiDAR hoch genug, keine Kabel im Scanbereich

---

## 11) Firmware-relevante Hardware-Parameter (aus `config.h`)

Diese Werte definieren indirekt Hardware-Annahmen (Tuning/Mechanik):

- Failsafe Timeout: `FAILSAFE_TIMEOUT_MS = 500`
- Control Loop: `CONTROL_LOOP_HZ = 50`
- Odom Publish: `ODOM_PUBLISH_HZ = 20`
- PWM Deadzone: `PWM_DEADZONE = 35`
- Wheel Diameter: `WHEEL_DIAMETER = 0.065`
- Wheel Base: `WHEEL_BASE = 0.178`
- Ticks/Rev (kalibriert):

  - `TICKS_PER_REV_LEFT = 374.3`
  - `TICKS_PER_REV_RIGHT = 373.6`

**Regel:** Wenn du Raeder, Getriebe oder Encoder-Setup aenderst -> diese Parameter neu kalibrieren.

---

## 12) Ablage im Repo (PR-freundlich)

Empfohlen:

- `hardware/docs/hardware-setup.md` (dieses Dokument)
- `hardware/schaltplan.pdf` (Schaltplan)
- `hardware/config.h` (Pin-Mapping + Parameter)
- `hardware/docs/kosten.md` (Kosten/Teileliste)

---

## Anhang A: Quick-Entscheidungen (fuer Zukunftssicherheit)

- **12 V Motor-Rail** (3S) beibehalten -> kompatibel zu vielen DC-Motoren/Peripherie.
- **Pi separat** ueber eigenen 5-V-Regler (USB-C, 5 A) -> stabiler ROS-Host.
- **A-only Encoder** ist ok zum Start; wenn spaeter Drift zu gross:

  - Phase B nachziehen (Quadratur) oder
  - bessere Odometrie (Radencoder hoeherer Aufloesung / mechanische Verbesserung).
