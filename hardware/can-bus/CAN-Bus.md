# CAN-Bus im AMR

## Leitfrage

Wie wird der interne CAN-Bus des AMR mit einem Raspberry Pi 5 als Zentralknoten und zwei ESP32-S3-Knoten als Drive- und Sensor-Controller technisch sauber aufgebaut, konfiguriert und getestet?

## Zielbild

Der AMR verwendet einen linearen 3-Knoten-CAN-Bus mit klassischem High-Speed-CAN nach CAN 2.0B. Der Raspberry Pi 5 bindet den Bus ueber ein SBC-CAN01-Modul mit MCP2515 und MCP2562 an SocketCAN an. Die beiden ESP32-S3-Knoten verwenden den integrierten TWAI-Controller und je einen SN65HVD230-Transceiver.

### Betriebsparameter

- CAN-Bitrate: 1 Mbit/s
- Topologie: Linie
- Abschlusswiderstand: nur an beiden Busenden
- Segmentlaenge: ca. 30 cm je Abschnitt
- Gesamtlaenge: ca. 0,6 m

## Architektur

```text
Raspberry Pi 5                ESP32-S3 Drive-Knoten           ESP32-S3 Sensor-Knoten
(SBC-CAN01)                   (SN65HVD230)                    (SN65HVD230)
┌──────────────────────┐      ┌──────────────────────┐        ┌──────────────────────┐
│ MCP2515 + MCP2562    │      │ TWAI + Transceiver   │        │ TWAI + Transceiver   │
│ SocketCAN / ROS 2    │──────│ Drive-CAN-Node       │────────│ Sensor-CAN-Node      │
│ 120 Ω aktiv          │      │ keine Terminierung    │        │ 120 Ω aktiv          │
└──────────────────────┘      └──────────────────────┘        └──────────────────────┘
       Busende                         Mittelknoten                    Busende
```

## Randbedingungen

### Topologie

Der Bus ist als Linie auszufuehren:

```text
Pi 5 ── 30 cm ── Drive-Knoten ── 30 cm ── Sensor-Knoten
```

Der Drive-Knoten sitzt in der Mitte und erhaelt **keine** Terminierung. Der Raspberry Pi 5 und der Sensor-Knoten bilden die beiden Busenden.

### Terminierung

* Raspberry Pi 5 / SBC-CAN01: **120 Ohm** aktiv
* Drive-Knoten: **keine** Terminierung
* Sensor-Knoten: **120 Ohm** aktiv


**Hardwareanpassung:** Das SN65HVD230-Board des Drive-Knotens besass ab Werk einen festen Abschlusswiderstand von ca. \(120\,\Omega\) zwischen CANH und CANL. Da der Drive-Knoten als Mittelknoten arbeitet, wurde dieser Widerstand entfernt. Der Drive-Knoten ist damit busseitig hochohmig (gemessen ca. \(72\,\mathrm{k\Omega}\)); der Gesamtbus misst stromlos ca. \(59\,\Omega\) zwischen CANH und CANL. Damit terminieren nur noch die beiden Busenden korrekt mit je \(120\,\Omega\).

### Spannungsversorgung

Am SBC-CAN01 muessen **zwei Spannungen getrennt** verdrahtet werden:

* **VCC1 = 5 V**: Versorgung fuer MCP2515/MCP2562
* **VCC = 3,3 V**: Logikpegel zur Pi-SPI-Schnittstelle

## Raspberry Pi 5 – SBC-CAN01 (MCP2515 + MCP2562)

Das SBC-CAN01 verwendet einen MCP2515 als CAN-Controller und einen MCP2562 als CAN-Transceiver. Der Anschluss erfolgt ueber SPI0 des Raspberry Pi 5.

### Verdrahtung Pi 5 ↔ SBC-CAN01

| SBC-CAN01-Pin | Pi 5 Header-Pin | Signal / Funktion |
|:--------------|:----------------|:------------------|
| **INT**       | Pin 22          | GPIO25, Interrupt |
| **SCK**       | Pin 23          | SPI0 SCLK         |
| **SI**        | Pin 19          | SPI0 MOSI         |
| **SO**        | Pin 21          | SPI0 MISO         |
| **CS**        | Pin 24          | SPI0 CE0          |
| **GND**       | Pin 6           | Masse             |
| **VCC1**      | Pin 2           | 5 V               |
| **VCC**       | Pin 1           | 3,3 V             |

### Terminierung am SBC-CAN01

Jumper **P1** auf **ON** setzen. Damit wird der integrierte Abschlusswiderstand von 120 Ohm aktiviert.

## ESP32-S3 – SN65HVD230

Die beiden ESP32-S3-Knoten verwenden den integrierten **TWAI-Controller** und je einen **SN65HVD230** als physikalischen CAN-Transceiver.

### Grundverdrahtung SN65HVD230 ↔ ESP32-S3

| SN65HVD230-Pin | Anschluss am ESP32-S3 | Funktion                  |
|:---------------|:----------------------|:--------------------------|
| **VCC**        | 3,3 V                 | Versorgung                |
| **GND**        | GND                   | Masse                     |
| **D**          | CAN_TX                | TX zum Transceiver        |
| **R**          | CAN_RX                | RX vom Transceiver        |
| **RS**         | GND                   | High-Speed-Modus          |
| **CANH**       | CANH                  | Differentielle Busleitung |
| **CANL**       | CANL                  | Differentielle Busleitung |
| **Vref**       | offen                 | nicht benoetigt           |

### Beispiel-Pinbelegung fuer XIAO ESP32-S3

| Funktion | XIAO-Pin | GPIO   |
|:---------|:---------|:-------|
| CAN_TX   | D6       | GPIO43 |
| CAN_RX   | D7       | GPIO44 |

## Software-Konfiguration

## Pi 5: `/boot/firmware/config.txt`

Fuer den CAN-Betrieb genuegt am Pi 5 die folgende CAN-relevante Konfiguration:

```ini
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25,spimaxfrequency=1000000
```

### Bedeutung der Parameter

* `oscillator=16000000` beschreibt den Quarz des MCP2515 auf dem SBC-CAN01.
* `interrupt=25` bindet den Interrupt auf GPIO25.
* `spimaxfrequency=1000000` begrenzt den **SPI-Takt** zwischen Pi 5 und MCP2515 auf 1 MHz.
* `spimaxfrequency` ist **nicht** die CAN-Bitrate.

## CAN-Interface unter Linux

Nach dem Neustart wird das Interface `can0` angelegt. Die eigentliche CAN-Bitrate wird anschliessend mit `ip link` gesetzt.

### Interface mit 1 Mbit/s aktivieren

```bash
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 1000000
ip -details -statistics link show can0
```

### Erwarteter Zustand

* `state UP`
* `can state ERROR-ACTIVE`
* `bitrate 1000000`
* Fehlerzaehler bei 0

## ESP32-S3: TWAI-Konfiguration fuer 1 Mbit/s

Alle ESP32-S3-Knoten auf dem Bus muessen mit derselben Bitrate arbeiten.

```c
#include <driver/twai.h>

static const twai_general_config_t g_config =
    TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_1, GPIO_NUM_2, TWAI_MODE_NORMAL);
//                                 CAN_TX      CAN_RX

static const twai_timing_config_t t_config =
    TWAI_TIMING_CONFIG_1MBITS();

static const twai_filter_config_t f_config =
    TWAI_FILTER_CONFIG_ACCEPT_ALL();

void can_init(void)
{
    ESP_ERROR_CHECK(twai_driver_install(&g_config, &t_config, &f_config));
    ESP_ERROR_CHECK(twai_start());
}
```

## Beispiel fuer Sensor-Telegramme

### Nachrichtenmodell

**Sensor-Node (0x110-0x1F0):**

| CAN-ID  | DLC    | Inhalt                                | Frequenz |
|:--------|:-------|:--------------------------------------|:---------|
| `0x110` | 4 Byte | Range (float32, m)                    | 10 Hz    |
| `0x120` | 1 Byte | Cliff (0x00=OK, 0x01=Cliff)           | 20 Hz    |
| `0x130` | 8 Byte | IMU Accel+GyroZ (3x int16 + 1x int16) | 50 Hz    |
| `0x131` | 4 Byte | IMU Heading (float32, rad)            | 50 Hz    |
| `0x140` | 6 Byte | Batterie (V mV, I mA, P mW)           | 2 Hz     |
| `0x141` | 1 Byte | Battery Shutdown Flag                 | Event    |
| `0x1F0` | 2 Byte | Heartbeat (Flags + Uptime mod 256)    | 1 Hz     |

**Drive-Node (0x200-0x2F0):**

| CAN-ID  | DLC    | Inhalt                               | Frequenz |
|:--------|:-------|:-------------------------------------|:---------|
| `0x200` | 8 Byte | Odom Position x,y (2x float32)       | 20 Hz    |
| `0x201` | 8 Byte | Odom Heading+Speed (2x float32)      | 20 Hz    |
| `0x210` | 8 Byte | Encoder L/R (2x float32, rad/s)      | 10 Hz    |
| `0x220` | 4 Byte | Motor-PWM L/R (2x int16, -255..+255) | 10 Hz    |
| `0x2F0` | 2 Byte | Heartbeat (Flags + Uptime mod 256)   | 1 Hz     |

### Sende-Implementierung

Die tatsaechliche CAN-Sende-Implementierung befindet sich in den `twai_can.hpp`-Dateien der jeweiligen Firmware-Projekte:

- Drive-Node: `amr/mcu_firmware/drive_node/include/twai_can.hpp`
- Sensor-Node: `amr/mcu_firmware/sensor_node/include/twai_can.hpp`

Beide nutzen die Klasse `amr::drivers::TwaiCan` mit Fire-and-forget-Semantik (CAN-Fehler sind nicht fatal, micro-ROS bleibt primaer). Datenformat: Little-Endian via `memcpy`.

## Funktionstest

## Empfang auf dem Pi 5

```bash
candump can0
```

## Senden vom Pi 5

```bash
cansend can0 123#1122334455667788
```

## Fehlerzaehler beobachten

```bash
watch -n 0.5 "ip -details -statistics link show can0"
```

### Bewertungskriterium

Der Aufbau gilt als stabil, wenn unter realem Verkehr:

* `state UP` bestehen bleibt,
* `error-warn`, `error-pass` und `bus-off` bei 0 bleiben,
* keine dauerhaft steigenden TX- oder RX-Fehlerzaehler auftreten.

## ROS-2-Bridge auf dem Pi 5

Der `can_bridge_node` liest CAN-Frames von SocketCAN und publiziert sie als `diagnostic_msgs/DiagnosticArray` auf `/diagnostics/can`. Er dient als reiner Monitoring- und Diagnosekanal und dupliziert keine micro-ROS-Daten.

- Implementierung: `amr/scripts/can_bridge_node.py`
- Start via Launch: `ros2 launch my_bot full_stack.launch.py use_can:=True`
- Start direkt: `ros2 run my_bot can_bridge_node`

Der Node dekodiert Heartbeats (Flags, Uptime), Sensordaten (Float-Werte) und Motor-PWM (Int16) strukturiert in die `DiagnosticStatus.values`-Liste.

## Validierungsskript

```bash
# Standalone (ohne ROS2/Docker):
python3 amr/scripts/can_validation_test.py --duration 30

# Als ROS2-Node (im Docker):
ros2 run my_bot can_validation_test
```

Ergebnis: `can_results.json` mit Frame-Raten, Heartbeat-Dekodierung, Sample-Werten und PASS/FAIL-Status.

## Testergebnisse (2026-03-07)

| Pruefpunkt               | Ergebnis | Bemerkung                         |
|:-------------------------|:---------|:----------------------------------|
| can0 Interface           | PASS     | ERROR-ACTIVE, 0 Bus-Errors        |
| MCP2515 Init             | PASS     | dmesg: "successfully initialized" |
| can0.service             | PASS     | aktiv, enabled, txqueuelen=1000   |
| Drive 0x200 OdomPos      | PASS     | ~16 Hz (Core 1, 50-Hz-Zyklus)     |
| Drive 0x201 OdomHeading  | PASS     | ~16 Hz                            |
| Drive 0x210 Encoder      | PASS     | 9.9 Hz                            |
| Drive 0x220 MotorPWM     | PASS     | 9.9 Hz                            |
| Drive 0x2F0 Heartbeat    | PASS     | 1.0 Hz, alle Flags korrekt        |
| Sensor 0x110 Range       | PASS     | 9.9 Hz                            |
| Sensor 0x120 Cliff       | PASS     | 19.9 Hz                           |
| Sensor 0x130 IMU Accel   | PASS     | 49.8 Hz                           |
| Sensor 0x131 IMU Heading | PASS     | 49.7 Hz                           |
| Sensor 0x140 Battery     | PASS     | 2.0 Hz, 12.39V/781mA              |
| Sensor 0x141 BatShutdown | n/a      | Event-basiert, kein Dauersignal   |
| Sensor 0x1F0 Heartbeat   | PASS     | 1.0 Hz, alle Flags korrekt        |
| Gesamt (30s)             | **PASS** | 5559 Frames, 11/12 IDs            |

Odom-Rate (~16 Hz statt 20 Hz): CAN-Sends laufen in `controlTask` (50 Hz), der Odom-Timer (50 ms) wird durch den Task-Scheduling-Jitter leicht gedehnt. Fuer Diagnostik-Zwecke akzeptabel.

## Troubleshooting-Checkliste

### Kein Frame von einem Node

1. Transceiver angeschlossen? 3.3V am SN65HVD230 VCC pruefen
2. Richtige Pins? GPIO43 (TX) und GPIO44 (RX) fuer beide Nodes
3. Firmware aktuell? `git log --oneline -1 amr/mcu_firmware/<node>/`
4. CAN-Init erfolgreich? Serielle Ausgabe beim Boot pruefen (`can_ok`)
5. Bus-Terminierung? 120 Ohm an beiden Enden, NICHT am Drive-Node
6. CANH/CANL vertauscht? Zwischen beiden Transceivern konsistent

### Frames kommen, aber nicht alle IDs

1. CAN-Sends fuer Cliff/Range/IMU/Heartbeat laufen in Core 1 (`sensorTask`/`controlTask`)
2. Battery-CAN-Send laeuft ebenfalls in `sensorTask` (seit v2.1.0)
3. BatShutdown (0x141) kommt nur bei Unterspannung (<9.5V)
4. `can_ok` Guards: Alle Sends pruefen `if (can_ok)`, Init-Fehler → nichts gesendet

### Bus-Errors steigen

1. Bitrate: Alle 3 Knoten muessen exakt 1 Mbit/s verwenden
2. Kabellaenge: Maximal ~0.6 m Gesamtlaenge bei 1 Mbit/s
3. Terminierung: Genau 2x 120 Ohm, Messung: CANH-CANL ~60 Ohm bei Busruhe
4. GND-Verbindung: Alle Knoten gemeinsame Masse
5. ERROR-PASSIVE: `sudo ip link set can0 down && up` zum Zuruecksetzen

### Diagnostik-Befehle

```bash
# Bus-Statistiken (live)
watch -n 1 "ip -details -statistics link show can0"

# Frame-Dump mit absolutem Timestamp
candump can0 -t A

# Nur bestimmte IDs filtern
candump can0,110:7FF,1F0:7FF

# Frame-Rate pro ID (10s Aufnahme)
timeout 10 candump can0 -t A > /tmp/can.log
awk '{print $4}' /tmp/can.log | sort | uniq -c | sort -rn
```

## Fazit

Der AMR verwendet einen technisch sauberen 3-Knoten-CAN-Bus mit Raspberry Pi 5 als SocketCAN-Knoten und zwei ESP32-S3-Knoten als verteilte Steuergeraete. Bei einer linearen Topologie mit ca. 0,6 m Gesamtlaenge, Terminierung nur an beiden Busenden und sauberer Verdrahtung ist 1 Mbit/s fuer diesen internen Aufbau fachlich plausibel. Alle 11 periodischen CAN-IDs werden zuverlaessig empfangen (validiert 2026-03-07).
