# ESP32-S3 via CAN-Bus

## Zentrale Randbedingung

Alle 11 GPIOs am XIAO ESP32-S3 #1 (Haupt-Controller) sind belegt. Damit scheidet eine direkte CAN-Verbindung ESP32 ↔ ESP32 aus – es fehlen zwei Pins für CAN_TX und CAN_RX. Die beiden vorhandenen CAN-Transceiver-Module eröffnen stattdessen den Weg **ESP32-S3 #2 ↔ Pi 5 über CAN**.

## Architektur

```
ESP32-S3 #2 (Sensor-Controller)          Raspberry Pi 5
┌──────────────────────────┐             ┌──────────────────────────┐
│  TWAI (integriert)       │             │  MCP2515 (SPI0)          │
│  CAN_TX (GPIO) ──► D    │   Twisted   │  MCP2562 Transceiver     │
│  CAN_RX (GPIO) ◄── R    │   Pair      │                          │
│         SN65HVD230       │─────────────│  SBC-CAN01 Modul         │
│  CANH ──────────────────────────────── CANH                       │
│  CANL ──────────────────────────────── CANL                       │
│  120 Ω (Terminierung)   │             │  120 Ω (Jumper P1 = ON)  │
└──────────────────────────┘             └──────────────────────────┘
   3,3 V Logik                              SPI: 3,3 V Logik
   VCC = 3,3 V                              VCC = 3,3 V / VCC1 = 5 V
   RS = GND (High-Speed)                    SocketCAN → ROS 2 Node
```

## ESP32-S3 #2 – Verdrahtung

Der ESP32-S3 enthält einen TWAI-Controller (Two-Wire Automotive Interface, kompatibel mit CAN 2.0B). Dieser benötigt keinen externen CAN-Controller wie den MCP2515 – lediglich den physischen Transceiver SN65HVD230.

### SN65HVD230 am ESP32-S3 #2

| SN65HVD230-Pin   | Anschluss                      | Signal                                |
|:-----------------|:-------------------------------|:--------------------------------------|
| **VCC** (Pin 3)  | ESP32-S3 3,3 V                 | Versorgung                            |
| **GND** (Pin 2)  | Gemeinsame Masse               | Pflicht                               |
| **D** (Pin 1)    | ESP32-S3 GPIO_X (frei wählbar) | CAN_TX → Treiber-Eingang              |
| **R** (Pin 4)    | ESP32-S3 GPIO_Y (frei wählbar) | CAN_RX ← Empfänger-Ausgang            |
| **RS** (Pin 8)   | GND                            | High-Speed-Modus (kein Slope Control) |
| **CANH** (Pin 7) | Twisted Pair → Pi 5 CANH       | Differenzielle Busleitung             |
| **CANL** (Pin 6) | Twisted Pair → Pi 5 CANL       | Differenzielle Busleitung             |
| **Vref** (Pin 5) | – (offen)                      | Nicht benötigt                        |

Laut Datenblatt (SLOS346G, S. 6) arbeitet der SN65HVD230 mit $V_\mathrm{CC} = 3{,}0$–$3{,}6\,\mathrm{V}$ und liefert bei $R_S = 0\,\mathrm{V}$ (GND) den High-Speed-Modus mit bis zu $1\,\mathrm{Mbit/s}$. Die Busenden erfordern jeweils $120\,\Omega$ Terminierung zwischen CANH und CANL.

### Pin-Vorschlag für ESP32-S3 #2 (XIAO-Format)

Da der zweite ESP32-S3 ausschließlich Sensorik betreibt, sind reichlich GPIOs verfügbar. Beispiel-Belegung:

| Pin | GPIO   | Funktion                    |
|:----|:-------|:----------------------------|
| D0  | GPIO1  | CAN_TX → SN65HVD230 D       |
| D1  | GPIO2  | CAN_RX ← SN65HVD230 R       |
| D2  | GPIO3  | VL53L1X XSHUT #1            |
| D3  | GPIO4  | VL53L1X XSHUT #2            |
| D4  | GPIO5  | I²C SDA (VL53L1X, MB1242)   |
| D5  | GPIO6  | I²C SCL                     |
| D6  | GPIO7  | HC-SR04 Trigger             |
| D7  | GPIO8  | HC-SR04 Echo                |
| D8  | GPIO9  | Sharp GP2Y0A21 (ADC, Cliff) |
| D9  | GPIO10 | Sharp GP2Y0A21 (ADC, Front) |
| D10 | GPIO21 | Status-LED                  |

## Raspberry Pi 5 – SBC-CAN01 (MCP2515 + MCP2562)

Laut der Joy-IT-Anleitung (SBC-CAN01, S. 7) wird das Modul über SPI an den Raspberry Pi angeschlossen. Der MCP2562-Transceiver auf dem Board übernimmt die physische CAN-Schicht.

### Verdrahtung Pi 5 ↔ SBC-CAN01

| SBC-CAN01-Pin | Pi 5 Header-Pin  | Funktion                      |
|:--------------|:-----------------|:------------------------------|
| **INT**       | Pin 22 (GPIO 25) | Interrupt                     |
| **SCK**       | Pin 23 (SCLK)    | SPI-Takt                      |
| **SI**        | Pin 19 (MOSI)    | SPI-Daten zum Modul           |
| **SO**        | Pin 21 (MISO)    | SPI-Daten vom Modul           |
| **CS**        | Pin 24 (CE0)     | Chip Select                   |
| **GND**       | Pin 6 (GND)      | Masse                         |
| **VCC1**      | Pin 2 (5 V)      | MCP2515/2562 Betriebsspannung |
| **VCC**       | Pin 1 (3,3 V)    | SPI-Logikpegel (Pi-seitig)    |

**Wichtig:** VCC1 und VCC getrennt verdrahten. VCC1 versorgt den MCP2515 und MCP2562 mit 5 V, während VCC die SPI-Logikpegel auf 3,3 V hält (Pi-GPIO-Schutz).

### Terminierung

Jumper P1 auf dem SBC-CAN01 auf **ON** setzen – damit ist der $120\,\Omega$ Abschlusswiderstand aktiviert. Am ESP32-S3-Ende muss ein externer $120\,\Omega$ Widerstand zwischen CANH und CANL gelötet werden (oder ein zweites SN65HVD230-Board mit Terminierung verwenden).

## Software-Konfiguration

### Pi 5: SocketCAN aktivieren

In `/boot/firmware/config.txt` (Pi 5 mit Debian Trixie):

```ini
# SPI aktivieren
dtparam=spi=on

# MCP2515 CAN-Controller (16 MHz Quarz auf SBC-CAN01)
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25

# SPI Chip Select
dtoverlay=spi0-1cs
```

Nach Neustart das CAN-Interface konfigurieren:

```bash
# Interface starten (500 kbit/s, passend zur ESP32-Konfiguration)
sudo ip link set can0 up type can bitrate 500000

# Empfangstest
candump can0

# Sendetest
cansend can0 127#DEADBEEF
```

### ESP32-S3 #2: TWAI-Firmware

```c
#include <driver/twai.h>

// TWAI-Konfiguration (CAN 2.0B, 500 kbit/s)
static const twai_general_config_t g_config =
    TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_1, GPIO_NUM_2, TWAI_MODE_NORMAL);
    //                         CAN_TX (D0)  CAN_RX (D1)

static const twai_timing_config_t t_config = TWAI_TIMING_CONFIG_500KBITS();
static const twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

void setup() {
    // TWAI-Treiber installieren und starten
    ESP_ERROR_CHECK(twai_driver_install(&g_config, &t_config, &f_config));
    ESP_ERROR_CHECK(twai_start());
}

// Sensordaten senden (Beispiel: VL53L1X Distanz)
void sendRangeData(uint16_t range_mm, uint8_t sensor_id) {
    twai_message_t msg;
    msg.identifier = 0x100 + sensor_id;  // z. B. 0x100 = Front, 0x101 = Cliff
    msg.data_length_code = 2;
    msg.data[0] = (range_mm >> 8) & 0xFF;
    msg.data[1] = range_mm & 0xFF;
    msg.flags = 0;  // Standard-Frame, kein RTR

    twai_transmit(&msg, pdMS_TO_TICKS(10));
}
```

### CAN-Nachrichtenprotokoll

Ein einfaches Schema für die Sensor-Telegramme:

| CAN-ID  | Länge   | Inhalt                              | Sensor              |
|:--------|:--------|:------------------------------------|:--------------------|
| `0x100` | 2 Bytes | Distanz [mm], Big-Endian            | VL53L1X Front       |
| `0x101` | 2 Bytes | Distanz [mm]                        | VL53L1X Cliff       |
| `0x110` | 2 Bytes | Distanz [mm]                        | HC-SR04 Ultraschall |
| `0x120` | 2 Bytes | ADC-Rohwert (12-bit)                | Sharp IR Front      |
| `0x121` | 2 Bytes | ADC-Rohwert (12-bit)                | Sharp IR Cliff      |
| `0x1F0` | 1 Byte  | Statusflags (Bit 0–4: Sensorstatus) | Heartbeat           |

### Pi 5: ROS 2 CAN-Bridge Node

Ein Python-Node liest die SocketCAN-Frames und publiziert `sensor_msgs/Range`:

```python
#!/usr/bin/env python3
"""CAN-Sensor-Bridge: Liest CAN-Frames und publiziert Range-Topics."""
import struct
import can
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range

class CanSensorBridge(Node):
    def __init__(self):
        super().__init__('can_sensor_bridge')
        self.bus = can.interface.Bus(channel='can0', interface='socketcan')

        # Publisher für jeden Sensor
        self.pub_front = self.create_publisher(Range, '/range/front', 10)
        self.pub_cliff = self.create_publisher(Range, '/range/cliff', 10)
        self.pub_us    = self.create_publisher(Range, '/range/ultrasonic', 10)

        # Timer: CAN-Frames pollen (100 Hz)
        self.create_timer(0.01, self.poll_can)

    def poll_can(self):
        msg = self.bus.recv(timeout=0.001)
        if msg is None:
            return

        range_msg = Range()
        range_msg.header.stamp = self.get_clock().now().to_msg()
        range_msg.header.frame_id = 'base_link'
        range_msg.field_of_view = 0.44  # ~25° (anpassen pro Sensor)
        range_msg.min_range = 0.02
        range_msg.max_range = 4.0

        if msg.arbitration_id == 0x100:  # VL53L1X Front
            dist_mm = struct.unpack('>H', bytes(msg.data[:2]))[0]
            range_msg.range = dist_mm / 1000.0
            range_msg.radiation_type = Range.INFRARED
            self.pub_front.publish(range_msg)

        elif msg.arbitration_id == 0x101:  # VL53L1X Cliff
            dist_mm = struct.unpack('>H', bytes(msg.data[:2]))[0]
            range_msg.range = dist_mm / 1000.0
            range_msg.radiation_type = Range.INFRARED
            range_msg.header.frame_id = 'cliff_sensor'
            self.pub_cliff.publish(range_msg)

        elif msg.arbitration_id == 0x110:  # HC-SR04
            dist_mm = struct.unpack('>H', bytes(msg.data[:2]))[0]
            range_msg.range = dist_mm / 1000.0
            range_msg.radiation_type = Range.ULTRASOUND
            range_msg.max_range = 4.0
            self.pub_us.publish(range_msg)
```

## Alternative: USB statt CAN

Falls die CAN-Integration zu aufwendig erscheint, gibt es einen deutlich einfacheren Weg: Der zweite ESP32-S3 wird wie der erste per USB-CDC an den Pi 5 angeschlossen und betreibt einen eigenen micro-ROS-Agent.

```bash
# Zweiter micro-ROS Agent auf separatem Port
ros2 run micro_ros_agent micro_ros_agent serial \
    --dev /dev/ttyACM1 -b 921600
```

Der Vorteil: Die bestehende Firmware-Architektur (FreeRTOS, micro-ROS, `sensor_msgs/Range`) kann 1:1 wiederverwendet werden. Kein CAN-Protokoll, kein MCP2515-Treiber, keine SocketCAN-Konfiguration.

Der Nachteil: Kein echtes Bussystem – bei späterem Ausbau auf mehr als zwei Controller wird die Anzahl der USB-Ports zum Engpass.

## Bewertung

| Kriterium            | CAN-Bus (SN65HVD230 + MCP2515)              | USB (micro-ROS)                         |
|:---------------------|:--------------------------------------------|:----------------------------------------|
| Verdrahtungsaufwand  | Hoch (SPI + CAN-Transceiver + Terminierung) | Gering (1× USB-C)                       |
| Firmware-Komplexität | TWAI-Treiber + eigenes Protokoll            | micro-ROS (bewährt)                     |
| Erweiterbarkeit      | Bis 120 Knoten auf einem Bus                | 1 USB-Port pro Controller               |
| Latenz               | < 1 ms (deterministisch)                    | 2–5 ms (USB-CDC, nicht deterministisch) |
| Thesis-Relevanz      | CAN-Bus ist industrieller Standard für AMR  | Einfacher, aber weniger lehrreich       |

Für die Bachelorarbeit hat die CAN-Variante den Vorteil, dass sie industrielle Relevanz demonstriert (ISO 11898, fahrzeugnahe Bussysteme). Die vorhandene Hardware – SN65HVD230-Board und SBC-CAN01 – deckt beide Busenden ab. Die USB-Variante wäre dagegen der pragmatische Weg, wenn die Sensorerweiterung schnell produktiv sein soll.
