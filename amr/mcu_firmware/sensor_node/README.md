# ESP32 AMR Sensor-Node

Echtzeit-Firmware fuer die Umgebungssensorik eines autonomen mobilen Roboters (AMR). Publiziert Ultraschall-Entfernung und Cliff-Erkennung ueber micro-ROS/UART an einen Raspberry Pi 5.

## Hardware-Voraussetzungen

| Komponente | Typ |
|---|---|
| Mikrocontroller | Seeed Studio XIAO ESP32-S3 |
| Ultraschall-Sensor | HC-SR04 (Spannungsteiler an Echo-Pin, 5 V → 3.3 V) |
| Cliff-Sensor | MH-B (YL-63) IR-Reflexionssensor |
| CAN-Transceiver | SN65HVD230 (3.3 V, GPIO43 TX / GPIO44 RX) |
| Verbindung zum Pi 5 | USB-CDC (micro-ROS) + CAN-Bus (TWAI, 500 kbit/s) |

Pin-Belegung und Sensorparameter sind in `include/config_sensors.h` definiert.

## Build & Flash

[PlatformIO](https://platformio.org/) ist erforderlich. Umgebung: `seeed_xiao_esp32s3`.

```bash
pio run                       # Kompilieren
pio run -t upload             # Flashen (921600 Baud, /dev/amr_sensor)
pio run -t monitor            # Serieller Monitor (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor
```

Der erste Build laedt und kompiliert die micro-ROS-Libraries (~15 Min). Folgebuilds sind gecached.

## Architektur

Dual-Core-Partitionierung (identisches Pattern wie Drive-Node):

```
Core 0 (loop)                      Core 1 (sensorTask)
  micro-ROS Executor                 Ultraschall-Messung (10 Hz)
  /range/front Publisher (10 Hz)     Cliff-Erkennung (20 Hz)
  /cliff Publisher (20 Hz)  <-->     pulseIn (blocking, max 25 ms)
                    \                /
                     SharedData (Mutex)
```

### Module (Header-only, `include/`)

| Datei | Namespace | Aufgabe |
|---|---|---|
| `main.cpp` | — | FreeRTOS-Tasks, micro-ROS Setup, Publisher |
| `range_sensor.hpp` | `amr::hardware` | HC-SR04 Trigger/Echo, Distanzberechnung |
| `cliff_sensor.hpp` | `amr::hardware` | MH-B IR-Reflexionssensor, Bodenerkennung |
| `twai_can.hpp` | `amr::drivers` | TWAI CAN-Bus Treiber, Dual-Path Sensor-Daten |

### Konfiguration (`include/config_sensors.h`)

Alle Parameter in C++-Namespaces: `amr::hal::` (Pins), `amr::timing::` (Raten), `amr::sensor::` (Physik). Compile-Time-Validierung via `static_assert`.

### ROS2 Topics

| Topic | Typ | Rate | Beschreibung |
|---|---|---|---|
| `/range/front` | `sensor_msgs/Range` | 10 Hz | Ultraschall-Entfernung (0.02-4.0 m) |
| `/cliff` | `std_msgs/Bool` | 20 Hz | Cliff-Erkennung (true = Abgrund) |

### CAN-Bus (TWAI, parallel zu micro-ROS)

Alle Sensor-Daten werden zusaetzlich via CAN 2.0B (500 kbit/s) gesendet. CAN-Init-Fehler sind nicht fatal — die Firmware laeuft ohne Transceiver weiter.

| CAN-ID | Laenge | Inhalt | Rate |
|---|---|---|---|
| `0x110` | 4 B | HC-SR04 Distanz [float32 LE, m] | 10 Hz |
| `0x120` | 1 B | Cliff-Status (0x00=OK, 0x01=Cliff) | 20 Hz |
| `0x130` | 8 B | IMU: ax,ay,az [int16 mg] + gz [int16 0.01 rad/s] | 50 Hz |
| `0x131` | 4 B | IMU Heading [float32 LE, rad] | 50 Hz |
| `0x140` | 6 B | Batterie: V [uint16 mV] + I [int16 mA] + P [uint16 mW] | 2 Hz |
| `0x141` | 1 B | Battery Shutdown (0x00=OK, 0x01=Shutdown) | Event |
| `0x1F0` | 2 B | Heartbeat: Flags [uint8] + Uptime [uint8 s%256] | 1 Hz |

## Lizenz

MIT -- siehe [`../LICENSE`](../LICENSE).
