# FT232_Adapter_USB-C (AZ-Delivery, FT232RL) – USB-TTL (UART) am Mac + XIAO ESP32-S3

## Randbedingungen

* TTL-Pegel: **$3{,}3 \, \mathrm{V}$** (ESP32-GPIOs)
* Adapter: **FT232RL**, Anschluss per **USB-C-Kabel**
* Adapter-Pins: **DTR, RX, TX, VCC, CTS, GND**
* Ziel: **USB-CDC** am XIAO für **Plot/Logs**, **UART (Serial1)** über FT232 für **Commands**

---

## Begriffe

* **UART (TTL):** serielle Schnittstelle mit Logikpegeln (hier $3{,}3 \, \mathrm{V}$).
* **USB-CDC:** „virtueller COM-Port“ über USB (XIAO direkt am Mac).

---

## Fähigkeiten (Use-Cases)

* **Zweiter Kanal parallel:** USB-CDC (Plot) + FT232-UART (Commands) gleichzeitig.
* **Debug/Console:** getrennte serielle Konsole unabhängig vom Plot-Stream.
* **UART-Module testen:** GPS/Modem/Displays usw.

---

## Stolperfallen

* **TTL-UART $\neq$ RS-232:** RS-232 hat andere Pegel (teils $\pm 12 \, \mathrm{V}$).
* **Pegel:** FT232 auf **$3{,}3 \, \mathrm{V}$** stellen.
* **VCC:** Wenn XIAO per USB versorgt ist, **FT232-VCC nicht verbinden**.
* **Port-Exklusivität:** Ein serieller Port kann immer nur **einmal** geöffnet werden (Plotter *oder* Monitor).

---

## Hardware-Anschluss (XIAO ESP32-S3)

**Regel (kreuzen):**

* FT232 **TX** → XIAO **RX** (**D7 / GPIO44**)
* FT232 **RX** → XIAO **TX** (**D6 / GPIO43**)
* FT232 **GND** → XIAO **GND**
* FT232 **VCC** → **nicht anschließen**

Optional:

* **CTS/DTR** nur bei Bedarf (Flow-Control/Auto-Reset), für Commands i. d. R. weglassen.

---

## macOS: Ports finden

```bash
ls -1 /dev/cu.* /dev/tty.* | egrep 'usbmodem|usbserial|SLAB|wch' || true
```

**Beispiel (dein System):**

* USB-CDC: `/dev/cu.usbmodem14501`
* FT232: `/dev/cu.usbserial-A5069RR4`

---

## PlatformIO: Default-Monitor auf FT232 legen (USB-CDC bleibt frei für Plotter)

`platformio.ini`:

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
framework = arduino

; Commands laufen über FT232 (PlatformIO Monitor)
monitor_port  = /dev/cu.usbserial-A5069RR4
monitor_speed = 115200

build_unflags = -std=gnu++11
build_flags =
  -std=gnu++17
  -DCORE_DEBUG_LEVEL=0
```

---

# Workflow: USB-CDC plotten (VS Code Serial Plotter) + FT232 Commands (PIO Monitor)

## 1) Ports setzen (optional)

```bash
CDC_PORT=/dev/cu.usbmodem14501
FTDI_PORT=/dev/cu.usbserial-A5069RR4

echo "USB-CDC : $CDC_PORT"
echo "FT232   : $FTDI_PORT"
```

---

## 2) Test-Firmware: Plot (Mario Zechner Format) + Ping/Pong

**Wichtig:** Mario Zechner Serial Plotter erwartet Zeilen mit:

* Prefix `>`
* `name:value`-Paare, getrennt mit `,`
* Zeilenende via `Serial.println(...)`

`src/main.cpp`:

```cpp
#include <Arduino.h>
#include <math.h>

static constexpr uint32_t PLOT_BAUD = 921600; // USB-CDC
static constexpr uint32_t CMD_BAUD  = 115200; // FT232 UART

static constexpr int CMD_RX_PIN = D7; // GPIO44
static constexpr int CMD_TX_PIN = D6; // GPIO43

static uint32_t t_plot = 0;

void setup() {
  Serial.begin(PLOT_BAUD);                               // Plot/Logs: USB-CDC
  Serial1.begin(CMD_BAUD, SERIAL_8N1, CMD_RX_PIN, CMD_TX_PIN); // Commands: FT232

  delay(200);

  Serial.println("# USB-CDC: plot ready (prefix '>' + name:value)");
  Serial1.println("# FT232: cmd ready (ping | help)");
}

void loop() {
  const uint32_t now = millis();

  // --- Plot: 50 Hz, zwei Signale 0..100 (gut sichtbar) ---
  if (now - t_plot >= 20) {
    t_plot = now;

    const float t = now / 1000.0f;
    const float s = 50.0f + 50.0f * sinf(2.0f * (float)M_PI * 0.5f * t); // 0..100
    const float ramp = fmodf(t * 10.0f, 100.0f);                         // 0..100

    Serial.print(">");
    Serial.print("sin:");
    Serial.print(s, 2);
    Serial.print(",ramp:");
    Serial.println(ramp, 2); // println => \r\n
  }

  // --- Commands: Ping/Pong über FT232 (Serial1) ---
  if (Serial1.available()) {
    String cmd = Serial1.readStringUntil('\n');
    cmd.trim();

    if (cmd.equalsIgnoreCase("ping")) {
      Serial1.println("pong");
    } else if (cmd.equalsIgnoreCase("help")) {
      Serial1.println("commands: ping | help");
    } else {
      Serial1.print("unknown: ");
      Serial1.println(cmd);
    }
  }
}
```

Upload:

```bash
pio run -t upload
```

---

## 3) Plot starten (VS Code: Mario Zechner Serial Plotter)

1. **Sicherstellen:** Niemand anderes nutzt `/dev/cu.usbmodem14501` (kein `pio device monitor`, kein `screen`).
2. VS Code: `Cmd + Shift + P` → **Serial Plotter: Open**
3. Port: `/dev/cu.usbmodem14501`
4. Baud: `921600`
5. **Start**

**Erwartung:** Variablen `sin` und `ramp` werden erkannt und geplottet.

---

## 4) Commands starten (Terminal oder VS Code Task)

Terminal:

```bash
pio device monitor -p /dev/cu.usbserial-A5069RR4 -b 115200
```

Test:

* `ping` → `pong`
* `help` → `commands: ping | help`
