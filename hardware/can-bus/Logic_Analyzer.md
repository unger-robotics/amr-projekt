# FT232RL USB-TTL Adapter, UART und Logic Analyzer am ESP32-S3 (Seeed XIAO)

## FT232RL: Was ist das und wofür nutzt du ihn?

Der **FT232RL USB-TTL Adapter** ist eine **UART-Brücke** zwischen PC und Mikrocontroller/Modul. Am PC erscheint ein **serieller Port** (z. B. `/dev/cu.usbserial…`), darüber sendest/empfängst du UART-Daten.

### 1) UART-Konsole für Debug/Logs

**Regel:** FT232 verbindet **PC ⇄ UART-Pins** (TX/RX) für Terminal-Ausgaben, Shells und Debug-Logs.
**Beispiel:** Firmware schreibt Logs → du liest sie im Terminal.
**Anwendung:**

* Verdrahtung: **TX(FT232) → RX(MCU)**, **RX(FT232) → TX(MCU)**, **GND → GND**
* Baudrate passend einstellen (z. B. `115200`)

### 2) Module direkt am PC testen

**Regel:** Alles, was UART spricht (z. B. GPS), kannst du direkt am PC beobachten.
**Beispiel:** GPS an FT232, Terminal auf `9600` → NMEA-Sätze laufen.
**Anwendung:** Schnellcheck „spricht das Modul?“ / „Baudrate passt?“.

### 3) Controller ohne USB-Interface programmieren (je nach Setup)

FT232 liefert die serielle Schnittstelle für Bootloader/Flash-Tools (abhängig von Chip und Boot-Beschaltung).

### Pegel: $3{,}3,\mathrm{V}$ vs. $5,\mathrm{V}$

**Regel:** Logik-Level und Versorgung trennen.

* **ESP32/ESP8266:** fast immer **$3{,}3,\mathrm{V}$**
* **$5,\mathrm{V}$** nur, wenn Ziel-Hardware wirklich **$5,\mathrm{V}$-tolerant** ist
* **VCC** nur verbinden, wenn du das Ziel bewusst über den Adapter versorgen willst; **GND** ist immer Pflicht

---

## UART: Kommunikationsprotokoll (Kurzmodell)

### Leitungen

* **TX** (Transmit): sendet Daten
* **RX** (Receive): empfängt Daten
* **GND**: Bezugspotential

**Asynchron** bedeutet: kein separater Clock-Pin; beide Seiten müssen Parameter identisch einstellen.

### Frame (typisch)

Ein Byte läuft als Frame über die Leitung:

* **Startbit**: `0` (Low)
* **Datenbits**: meist 8 Bit (LSB zuerst)
* **optional Parität**
* **Stopbit(s)**: `1` (High)

Typische Einstellung: **8N1**
[
\Rightarrow \text{8 Datenbits, keine Parität, 1 Stopbit}
]

### Parameter, die passen müssen

1. **Baudrate**, z. B. $115200,\mathrm{Bd}$
2. **Frame-Format**, z. B. 8N1
3. **Pegel**, z. B. $3{,}3,\mathrm{V}$
4. **Verdrahtung**, TX↔RX gekreuzt + gemeinsame Masse

Wenn Baudrate oder Format falsch sind, siehst du im Terminal „Zeichensalat“.

---

## UART am ESP32-S3 (Seeed XIAO) mit Logs + Modul parallel

### Zielbild

* **USB-CDC** für Logs mit `921600` auf `/dev/cu.usbmodem…`
* **UART über FT232** als `Serial1` mit `115200` auf `/dev/cu.usbserial…`

Damit gilt: **USB = Debug/Logs**, **Serial1 = Modul-Link**.

### Anschluss (FT232 ↔ ESP32-S3)

* FT232 auf **$3{,}3,\mathrm{V}$** stellen
* **TX(FT232) → RX(ESP32)**
* **RX(FT232) → TX(ESP32)**
* **GND → GND**
* **VCC** meist weglassen (ESP32 separat versorgen)

### Mini-Checkliste „Warum geht’s nicht?“

1. GND fehlt
2. TX/TX statt TX/RX
3. FT232 steht auf $5,\mathrm{V}$
4. Baudrate/8N1 falsch
5. Falsche UART-Pins/Port in der Firmware

---

## Logic Analyzer (AZ-Delivery 8CH/24 MSps) unter macOS mit Logic 2

### Installation (kurz)

* Per ZIP von Saleae installieren **oder**
* Homebrew:

  ```bash
  brew install --cask saleae-logic
  ```

### Verkabelung für UART-Analyse (Modul-Link)

* Logic Analyzer **GND → GND** (ESP32/Modul)
* **D0 → TX (ESP32 → Modul)**
* **D1 → RX (Modul → ESP32)**
* Optional: **D2 → MARKER-GPIO** (Firmware toggelt zur Zeitmarke)

### Sample-Rate wählen

Faustregel: mindestens **$10\times$** Baudrate.

* `115200` → z. B. $2\ldots 10,\mathrm{MS/s}$
* `921600` → z. B. $10\ldots 24,\mathrm{MS/s}$

### UART-Decoder in Logic 2

1. **Analyzers** → **Async Serial / UART**
2. Für **D0** Decoder anlegen (`115200`, 8N1)
3. Für **D1** Decoder anlegen (`115200`, 8N1)
4. **Invert** nur aktivieren, wenn das Decoding trotz korrekter Baudrate offensichtlich „invertiert“ wirkt

### Marker-Pin (Logs ↔ Leitung korrelieren)

Ein Marker-GPIO macht die Zeitkorrelation eindeutig:

```cpp
digitalWrite(MARKER_PIN, HIGH);   // vor UART write
Serial1.write(buf, len);
Serial1.flush();
digitalWrite(MARKER_PIN, LOW);    // nach UART
```

In Logic 2 siehst du dann **MARKER + TX/RX** im selben Zeitfenster.

### Trigger-Ideen

* Trigger auf **fallende Flanke** am TX (Startbit)
* Trigger auf **Pulsbreite** am Marker (definierter Marker-Puls)

---

## Typische Fehlerbilder beim Logic-Analyzer-Capture

1. **Decoder zeigt falsche Zeichen** → Baudrate/8N1 prüfen, Sample-Rate erhöhen, ggf. Invert testen
2. **Nur eine Richtung sichtbar** → falsche Leitung erwischt, RX/TX verwechselt, GND fehlt
3. **Glitches/doppelte Flanken** → Leitungen kürzen, GND näher abgreifen, saubere Masseführung
