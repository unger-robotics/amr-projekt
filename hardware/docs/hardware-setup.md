---
title: "Hardware Setup - AMR Platform"
file: "hardware/docs/hardware-setup.md"
status: "active"
updated: "2026-02-15"
scope: "Projekt-Nachschlagewerk (Master-grade Design)"
---

# Hardware Setup - AMR Platform

Dieses Dokument beschreibt den **physischen Aufbau** (Stromversorgung, Verkabelung, Pin-Mapping, Inbetriebnahme-Messpunkte) fuer den AMR-Stack mit:

- **Raspberry Pi 5** (Host: ROS 2 in Docker)
- **Seeed XIAO ESP32-S3** (Motor/Encoder/Realtime, micro-ROS Client)
- **Cytron MDD3A** (Dual-Motor-Treiber, Dual-PWM)
- **JGA25-370 12 V + Hall-Encoder** (2x)
- **RPLIDAR A1** (USB CP210x, `/dev/ttyUSB0`, `/scan`)
- **IMX296 Global Shutter Camera** (CSI, v4l2loopback-Bridge nach `/dev/video10`)
- **Hailo-8L AI Kit** (PCIe, HailoRT 4.23.0)
- ~~Pan/Tilt (2x Servo)~~: D8/D9 durch Encoder Phase B belegt

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

  RAIL12 --> BUCKSERVO[DC/DC LM2596\n5 V Peripherie]
  BUCKSERVO --> SERVO[Servos (nicht aktiv)]

  PI -->|USB| ESP[XIAO ESP32-S3]
  PI -->|USB| LIDAR[RPLIDAR A1]
  PI -->|CSI| CAM[IMX296 Global Shutter\nCamera]
  PI -->|PCIe| HAILO[Hailo-8L AI Kit]
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
| Encoder Left A  |       D6 | Interrupt (CHANGE)                  |
| Encoder Right A |       D7 | Interrupt (CHANGE)                  |
| Encoder Left B  |       D8 | Quadratur-Richtung                  |
| Encoder Right B |       D9 | Quadratur-Richtung                  |
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

## 5) Encoder (Quadratur A+B) - Richtungserkennung aus Phasenversatz

### 5.1 Encoder-Wiring (6-adrig Motor+Encoder typisch)

Bei JGA25-370 mit Hall-Encoder sind typischerweise:

- 2 Leitungen Motor
- 4 Leitungen Encoder (VCC, GND, A, B)

**Quadratur-Konzept (A+B, 2x-Zaehlung):**

- Verbinde **Phase A** (Interrupt, CHANGE) und **Phase B** (Richtungserkennung) zu den jeweiligen Pins.
- Die Richtung wird aus dem Phasenversatz zwischen A und B bestimmt (nicht aus der PWM-Ansteuerung).

Aus Schaltplan-Tabelle:

- Encoder Phase A (Links): **D6**, **Gelb**
- Encoder Phase B (Links): **D8**, **Gruen**
- Encoder Phase A (Rechts): **D7**, **Gelb**
- Encoder Phase B (Rechts): **D9**, **Gruen**
- Hinweis: "Beide Phasen (Gelb=A, Gruen=B) anschliessen."

### 5.2 Encoder-Versorgung (entscheidend)

- Encoder braucht **VCC + GND** zusaetzlich zur Signalleitung.
- Ziel ist **sauberer Logikpegel** am ESP32 (3.3 V).

**Empfehlung:**

- Wenn Encoder mit **3.3 V** stabil funktioniert: VCC = 3.3 V (aktueller Betriebsmodus).
- Falls Encoder **5 V** benoetigt: VCC = 5 V, dann **Pegelanpassung** fuer A- und B-Signal (Level Shifter oder Spannungsteiler), um ESP32-Pins zu schuetzen.
- Bei Quadratur muessen **beide Phasen** saubere Pegel liefern — Twisted-Pair-Fuehrung fuer Encoder-Leitungen empfohlen.

---

## 6) I2C / IMU (optional in Phase 1, wichtig ab Phase 4)

- I2C liegt auf **D4 (SDA)** und **D5 (SCL)**.
- I2C-Versorgung **3.3 V** (Schaltplan-Hinweis).
- Leitungslaengen kurz halten; bei Stoerungen: 100 nF nahe IMU, ggf. 2.2-4.7 kOhm Pullups (nur einmal im Bus).

---

## 7) Servos (Pan/Tilt) — nicht aktiv

> **Status:** D8/D9 werden fuer Encoder Phase B (Quadratur) genutzt. Servos sind nicht anschliessbar, solange Quadratur-Encoder aktiv sind. Fuer Servo-Betrieb muessten die Encoder auf A-only zurueckgestellt und die Firmware angepasst werden.

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

### 9.1 Pi-5-Spezifikation (verifiziert 2026-02-15)

| Parameter | Wert |
|---|---|
| Modell | Raspberry Pi 5 Model B Rev 1.1 |
| CPU | 4 Kerne @ 2400 MHz (BCM2712) |
| RAM | 8 GB |
| OS | Debian GNU/Linux 13 (Trixie), Kernel 6.12 |
| Disk | 128 GB microSD |

### 9.2 USB-Geraete (verifiziert)

| Geraet | VID:PID | Device-Node | Hinweis |
|---|---|---|---|
| XIAO ESP32-S3 | `303a:1001` | `/dev/ttyACM0` | USB-CDC JTAG/Serial |
| RPLIDAR A1 (CP210x) | `10c4:ea60` | `/dev/ttyUSB0` | USB-Serial Adapter |

**Regel:** Fuer Stabilitaet ueber Reboots:

- udev-Regeln verwenden (serielle Geraete per VID/PID/Serial auf Alias verlinken), z.B. `/dev/amr_esp32`, `/dev/amr_lidar`.
- Stabiler Pfad fuer ESP32: `/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_...-if00`

**Achtung Serial-Port-Konflikt:** `embedded-bridge.service` (Port 8081) belegt `/dev/ttyACM0`. Vor micro-ROS-Agent-Start stoppen: `sudo systemctl stop embedded-bridge.service`.

### 9.3 Kamera (IMX296 Global Shutter, CSI)

- Erkannt via `rpicam-hello` (Debian Trixie: `rpicam-hello`, nicht `libcamera-hello`)
- v4l2loopback-Bridge: `camera-v4l2-bridge.service` (systemd, active) → `/dev/video10`
- Aufloesung: 1456x1088 @ 15fps (MJPEG → YUYV)
- CSI-Anschluss: 22-pin Mini-CSI (Pi 5), ggf. 22-auf-15-pin Adapter fuer aeltere Kameras
- `dtoverlay=imx296` in `/boot/firmware/config.txt` erforderlich (`camera_auto_detect=1` erkennt IMX296 nicht)

### 9.4 Hailo-8L (PCIe AI Accelerator)

- Erkannt via PCIe
- HailoRT: v4.23.0
- Aktuell nicht in der AMR-Pipeline genutzt (Potenzial fuer Objekterkennung/Hindernisvermeidung)

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
- [ ] Phase B am richtigen Pin (D8/D9)
- [ ] Richtungserkennung korrekt (Vorwaerts = positive Ticks bei beiden Raedern)
- [ ] Zaehlen stabil bei langsamer Drehung (keine "Spikes" bei Stillstand)

### 10.4 Lidar-Checks

- [ ] Geraet enumeriert am Pi (`lsusb`)
- [ ] `/scan` laesst sich erzeugen (Phase 3 Doku)
- [ ] Mechanische Lage: LiDAR hoch genug, keine Kabel im Scanbereich

---

## 11) Firmware-relevante Hardware-Parameter (aus `config.h` und `main.cpp`)

Diese Werte definieren indirekt Hardware-Annahmen (Tuning/Mechanik).

### 11.1 Kinematik & Odometrie

- Wheel Diameter: `WHEEL_DIAMETER = 0.065` [m]
- Wheel Base: `WHEEL_BASE = 0.178` [m]
- Ticks/Rev (kalibriert, 10-Umdrehungen-Test, 2x Quadratur-Zaehlung):

  - `TICKS_PER_REV_LEFT = 748.6`
  - `TICKS_PER_REV_RIGHT = 747.2`

### 11.2 PWM-Konfiguration (Motor)

- Frequenz: `MOTOR_PWM_FREQ = 20000` (20 kHz, unhoerbar)
- Aufloesung: `MOTOR_PWM_BITS = 8` (8-bit, 0-255)
- Maximum: `MOTOR_PWM_MAX = 255`
- Deadzone: `PWM_DEADZONE = 35` (PWM unter dem Motor nicht anlaeuft)

### 11.3 PWM-Kanal-Zuordnung (ESP32 LEDC)

Die A/B-Kanaele sind bewusst getauscht, damit die Drehrichtung korrekt ist:

- Motor Links A: Kanal 1 (`PWM_CH_LEFT_A = 1`)
- Motor Links B: Kanal 0 (`PWM_CH_LEFT_B = 0`)
- Motor Rechts A: Kanal 3 (`PWM_CH_RIGHT_A = 3`)
- Motor Rechts B: Kanal 2 (`PWM_CH_RIGHT_B = 2`)

### 11.4 LED/MOSFET-PWM

- Kanal: `LED_PWM_CHANNEL = 4`
- Frequenz: `LED_PWM_FREQ = 5000` (5 kHz)
- Aufloesung: `LED_PWM_BITS = 8`

### 11.5 PID-Gains (in `main.cpp` hardcoded)

- Kp = 1.5
- Ki = 0.5
- Kd = 0.0
- Ausgang begrenzt auf [-1.0, 1.0]

### 11.6 Beschleunigungsrampe (in `main.cpp` hardcoded)

- `MAX_ACCEL = 5.0` [rad/s^2]
- Maximale Aenderung pro Regelzyklus: `MAX_ACCEL * 0.02 = 0.1` rad/s

### 11.7 Timing & Safety

- Failsafe Timeout: `FAILSAFE_TIMEOUT_MS = 500` (Motoren stoppen nach 500 ms ohne `cmd_vel`)
- Control Loop: `CONTROL_LOOP_HZ = 50` (20 ms Takt, Core 1)
- Odom Publish: `ODOM_PUBLISH_HZ = 20` (50 ms Takt, Core 0)

### 11.8 I2C / IMU

- I2C-Adresse: `IMU_I2C_ADDR = 0x68` (MPU6050, optional)

### 11.9 Firmware-Kommunikation (aus `platformio.ini`)

- Serial (Monitor): 115200 Baud
- Upload: 921600 Baud
- Upload-Port: `/dev/ttyACM0` (USB-CDC)
- micro-ROS Transport: `serial`
- ROS-Distribution: `humble`

**Regel:** Wenn du Raeder, Getriebe oder Encoder-Setup aenderst -> diese Parameter neu kalibrieren. PID-Gains und Beschleunigungsrampe erfordern nach Hardware-Aenderungen ebenfalls eine Neuabstimmung.

---

## 12) Software-Stack (verifiziert 2026-02-15)

Quelle: `amr/scripts/hardware_info.py` → `hardware_info_20260215_180556.md`

### 12.1 Toolchain & Laufzeit

| Komponente | Version | Hinweis |
|---|---|---|
| PlatformIO Core | 6.1.19 | Platform `espressif32` (6.12.0) |
| ESP32-S3 Toolchain | xtensa-esp32s3-elf-gcc **8.4.0** | crosstool-NG esp-2021r2-patch5 |
| C++-Standard | C++11 (`-std=gnu++11`) | Siehe `hardware/docs/toolchain_analyse.md` |
| Docker | 29.2.1 | `docker compose` v5.0.2 |
| System-GCC (Host) | 14.2.0 | Debian Trixie, nur fuer Host-Tools |
| Python (Host) | 3.13.5 | Fuer Validierungsskripte |

### 12.2 Relevante Host-Pakete

| Paket | Version | Verwendung |
|---|---|---|
| python3-opencv | 4.10.0 | ArUco-Docking (via Docker/cv_bridge) |
| python3-numpy | 2.2.4 | UMBmark-Analyse, Validierung |
| python3-serial | 3.5 | ESP32-Reset-Skripte |
| python3-hailort | 4.23.0 | Hailo-8L AI Accelerator |
| v4l2loopback-dkms | 0.15.0 | Kamera-Bridge (`/dev/video10`) |
| rpicam-apps | 1.10.1 | `rpicam-vid` fuer Kamera-Bridge |

---

## 13) Ablage im Repo (PR-freundlich)

Empfohlen:

- `hardware/docs/hardware-setup.md` (dieses Dokument)
- `hardware/schaltplan.pdf` (Schaltplan)
- `hardware/config.h` (Pin-Mapping + Parameter)
- `hardware/docs/kosten.md` (Kosten/Teileliste)

---

## Anhang A: Entscheidungen (fuer Zukunftssicherheit)

- **12 V Motor-Rail** (3S) beibehalten -> kompatibel zu vielen DC-Motoren/Peripherie.
- **Pi separat** ueber eigenen 5-V-Regler (USB-C, 5 A) -> stabiler ROS-Host.
- **Quadratur-Encoder (A+B)** aktiv: Phase B wurde nachgezogen, Richtungserkennung erfolgt aus Phasenversatz statt PWM-Ansteuerung. 2x-Zaehlung (~748 Ticks/Rev) verdoppelt die Aufloesung gegenueber dem urspruenglichen A-only-Design.
