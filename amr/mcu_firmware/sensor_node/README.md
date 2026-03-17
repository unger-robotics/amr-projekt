# ESP32 AMR Sensor-Node

Echtzeit-Firmware fuer die Umgebungssensorik, IMU, Batterieueberwachung und Servo-Steuerung eines autonomen mobilen Roboters (AMR). Publiziert Ultraschall, Cliff, IMU, Batteriestatus und Battery-Shutdown ueber micro-ROS/UART an einen Raspberry Pi 5.

## Hardware-Voraussetzungen

| Komponente | Typ | Anschluss |
|---|---|---|
| Mikrocontroller | Seeed Studio XIAO ESP32-S3 | USB-CDC (micro-ROS) |
| Ultraschall-Sensor | HC-SR04 | Trigger GPIO 1 (D0), Echo GPIO 2 (D1, Spannungsteiler 5 V --> 3.3 V) |
| Cliff-Sensor | MH-B (YL-63) IR-Reflexionssensor | GPIO 3 (D2), HIGH = Abgrund |
| IMU | MPU6050 (GY-521) | I2C 0x68 (AD0=GND) |
| Leistungsmonitor | INA260 | I2C 0x40 (A0=GND, A1=GND) |
| Servo-PWM | PCA9685 (16-Kanal) | I2C 0x41 (A0-Loetbruecke geschlossen) |
| Servos | MG996R (Pan, Kanal 0) + MG90S (Tilt, Kanal 1) | PCA9685 PWM-Ausgaenge |
| CAN-Transceiver | SN65HVD230 (3.3 V) | GPIO 43 TX / GPIO 44 RX |
| Akku | Samsung INR18650-35E 3S1P (10.8 V nom., 3.35 Ah) | Ueberwacht via INA260 |

Pin-Belegung und alle Sensorparameter sind in `include/config_sensors.h` definiert.

### I2C-Bus (400 kHz Fast-mode, GPIO 5 SDA / GPIO 6 SCL)

| Adresse | Geraet | Zugriff |
|---|---|---|
| `0x40` | INA260 (Batterie) | Core 1: Read (2 Hz) |
| `0x41` | PCA9685 (Servo-PWM) | Core 0: Write (5 Hz Polling) |
| `0x68` | MPU6050 (IMU) | Core 1: Read (50 Hz) |

Alle I2C-Zugriffe ueber `i2c_mutex` (5-10 ms Timeout). Keine I2C-Kollisionen durch strikte Core-Aufteilung: Reads auf Core 1 (`sensorTask`), Writes auf Core 0 (`loop()`).

## Build & Flash

[PlatformIO](https://platformio.org/) ist erforderlich. **Wichtig:** Immer `-e <environment>` angeben — ohne `-e` flasht PlatformIO ALLE Environments, das letzte ueberschreibt die vorherigen.

```bash
pio run -e sensor_node                       # Kompilieren
pio run -e sensor_node -t upload -t monitor  # Upload + Monitor (921600 Baud, /dev/amr_sensor)
pio run -e servo_test -t upload -t monitor   # Servo-Kalibrierung Pan/Tilt (ohne micro-ROS)
```

Der erste Build laedt und kompiliert die micro-ROS-Libraries (~15 Min). Folgebuilds sind gecached.

### Library-Abhaengigkeiten

| Library | Version | Verwendung |
|---|---|---|
| micro-ROS (GitHub) | Humble | Serial Transport, ROS2 Client |
| Adafruit BusIO | ^1.14.1 | I2C-Abstraktion (transitive Abhaengigkeit) |
| Adafruit INA260 | ^1.5.0 | Transitive Abh. — eigener Header-Only-Treiber `ina260.hpp` |
| Adafruit MPU6050 | ^2.2.6 | Transitive Abh. — eigener Header-Only-Treiber `mpu6050.hpp` |
| Adafruit PWM Servo | ^3.0.2 | Transitive Abh. — eigener Header-Only-Treiber `pca9685.hpp` |
| Adafruit Unified Sensor | ^1.1.13 | Transitive Abhaengigkeit |

Die Adafruit-Libraries sind als PlatformIO-Abhaengigkeiten deklariert, die eigentlichen Treiber sind eigene Header-Only-Implementierungen in `include/`.

## Architektur

Dual-Core-Partitionierung mit strikter I2C-Aufteilung (identisches Pattern wie Drive-Node):

```
Core 0 (loop)                               Core 1 (sensorTask, 10 ms Basistakt)
  micro-ROS Executor                          Cliff-Read (20 Hz, digitalRead)
  5 Publisher, 3 Subscriber                   Ultraschall (10 Hz, ISR-basiert)
  Servo I2C Write (5 Hz, i2c_mutex)     <--   IMU I2C Read (50 Hz, i2c_mutex)
  Batterie-Publish (2 Hz, aus SharedData)     Batterie I2C Read (2 Hz, i2c_mutex)
  Cliff-Publish (20 Hz)                      Deferred Servo-Power (allOff/clearAllOff)
  Range-Publish (10 Hz)                      CAN-TX (Range, Cliff, IMU, Battery, Heartbeat)
  IMU-Publish (50 Hz)
  Batterie-Unterspannungs-Logik
  LED-Heartbeat
  Inter-Core Watchdog
                      \                  /
                SharedSensorData (mutex, 5 ms) + i2c_mutex (5-10 ms)
```

### Initialisierungs-Reihenfolge

Die Init-Reihenfolge ist kritisch fuer I2C-Stabilitaet:

1. `delay(2000)` — USB-CDC + I2C-Bus Stabilisierung
2. `Wire.begin()` — I2C-Bus starten (400 kHz)
3. **PCA9685 init** (bis zu 3 Versuche) — muss VOR IMU/INA260 (braucht sauberen Bus)
4. **MPU6050 init** + Gyro-Kalibrierung (500 Samples)
5. **INA260 init**
6. GPIO-Sensoren (Ultraschall-ISR, Cliff) — NACH I2C, da ISR den Bus stoeren kann
7. CAN-Bus (TWAI) — fehlschlag nicht fatal
8. FreeRTOS `sensorTask` auf Core 1 starten
9. micro-ROS Agent-Verbindung (blockiert mit LED-Blinken)

### Deferred-Pattern (kein I2C in Callbacks)

Subscriber-Callbacks schreiben nur in volatile RAM-Structs:

- **ServoCommand**: `/servo_cmd` --> `servo_cmd.pan/tilt` (RAM) --> `loop()` fuehrt I2C aus (5 Hz)
- **HardwareCommand**: `/hardware_cmd` --> `hw_cmd.servo_speed` (RAM) --> `loop()` wendet an
- **deferred_servo_power**: Batterie-Logik (Core 0) setzt Flag --> Core 1 fuehrt `allOff()`/`clearAllOff()` aus

### ISR-basierter Ultraschall (HC-SR04)

Nicht-blockierend, ersetzt frueheres `pulseIn()`:

```
sonar.trigger()  -->  10 µs Puls auf Trigger-Pin (kehrt sofort zurueck)
                      Echo-Pin ISR (IRAM_ATTR, GPIO-Register-Zugriff):
                        Rising Edge: us_echo_start = micros()
                        Falling Edge: us_echo_end = micros(), us_meas_ready = true
sonar.tryRead()  -->  Prueft us_meas_ready, berechnet Distanz oder Timeout
```

ISR-Variablen sind volatile Globals in `main.cpp` (nicht im Namespace — IRAM_ATTR Linker-Constraint). GPIO-Zustand via `(GPIO.in >> pin) & 0x1` (kein `digitalRead()` in ISR).

### Module (Header-only, `include/`)

| Datei | Namespace | Aufgabe |
|---|---|---|
| `config_sensors.h` | `amr::*` | Zentrale Konfiguration: HAL-Pins, I2C, Timing, Sensorik, Batterie, Servo, CAN |
| `range_sensor.hpp` | `amr::hardware` | HC-SR04 non-blocking Trigger/Echo mit ISR-Integration, `trigger()` + `tryRead()` |
| `cliff_sensor.hpp` | `amr::hardware` | MH-B IR-Reflexionssensor, `isCliffDetected()` (HIGH = Abgrund) |
| `mpu6050.hpp` | `amr::drivers` | MPU6050 I2C-Treiber: ±2g Accel, ±250 deg/s Gyro, Bias-Kalibrierung, Komplementaerfilter (98% Gyro / 2% Encoder) |
| `ina260.hpp` | `amr::drivers` | TI INA260 I2C-Leistungsmonitor: Spannung (1.25 mV LSB), Strom (1.25 mA LSB), Leistung (10 mW LSB), Unterspannungs-Alert |
| `pca9685.hpp` | `amr::drivers` | NXP PCA9685 I2C-Servo-PWM: `setAngle()` (direkt), `setTargetAngle()` + `updateRamp()` (nicht-blockierend), `allOff()` Notaus |
| `twai_can.hpp` | `amr::drivers` | TWAI CAN-Bus: Range, Cliff, IMU, Battery, Heartbeat Sends |

## ROS2-Topics

### Publisher

| Topic | Typ | Rate | QoS | Beschreibung |
|---|---|---|---|---|
| `/range/front` | `sensor_msgs/Range` | 10 Hz | Reliable | Ultraschall-Entfernung (0.02-4.0 m), Frame: `ultrasonic_link` |
| `/cliff` | `std_msgs/Bool` | 20 Hz | Reliable | Cliff-Erkennung (true = Abgrund) |
| `/imu` | `sensor_msgs/Imu` | 50 Hz | Reliable | Accel + Gyro + fusioniertes Heading, Frame: `base_link` |
| `/battery` | `sensor_msgs/BatteryState` | 2 Hz | Reliable | Spannung, Strom, SOC (lineare Schaetzung), Frame: `base_link` |
| `/battery_shutdown` | `std_msgs/Bool` | 2 Hz / Event | Reliable | true bei Unterspannung < 9.5 V, false bei Erholung > 9.8 V |

### Subscriber

| Topic | Typ | Beschreibung |
|---|---|---|
| `/servo_cmd` | `geometry_msgs/Point` | x=Pan-Winkel (45-135 deg), y=Tilt-Winkel (80-135 deg) |
| `/hardware_cmd` | `geometry_msgs/Point` | y=Servo-Ramp-Speed (1.0-10.0 deg/Step) |
| `/odom` | `nav_msgs/Odometry` | Encoder-Heading fuer IMU-Komplementaerfilter (2% Gewichtung) |

## Konfiguration (`include/config_sensors.h`)

Alle Parameter in C++-Namespaces mit `inline constexpr` und `static_assert` Compile-Time-Validierung.

### Ultraschall (HC-SR04)

| Parameter | Namespace | Wert | Beschreibung |
|---|---|---|---|
| `speed_of_sound_m_s` | `amr::sensor` | 343.2 m/s | Bei 20 Grad C, trockene Luft |
| `us_min_range_m` | `amr::sensor` | 0.02 m | Minimale Messdistanz |
| `us_max_range_m` | `amr::sensor` | 4.0 m | Maximale Messdistanz |
| `us_timeout_us` | `amr::timing` | 20000 µs | Echo-Timeout (~3.4 m Hin+Rueck) |
| `us_publish_hz` | `amr::timing` | 10 Hz | Trigger- und Publish-Rate |

### IMU (MPU6050)

| Parameter | Namespace | Wert | Beschreibung |
|---|---|---|---|
| `complementary_alpha` | `amr::imu` | 0.98 | 98% Gyro + 2% Encoder-Heading |
| `gyro_sensitivity` | `amr::imu` | 131.0 LSB/(deg/s) | ±250 deg/s Bereich |
| `accel_sensitivity` | `amr::imu` | 16384.0 LSB/g | ±2g Bereich |
| `calibration_samples` | `amr::imu` | 500 | Gyro-Bias beim Start |
| `imu_sample_hz` | `amr::timing` | 50 Hz | Abtastrate (real ~33 Hz, I2C-limitiert) |

### Batterie (INA260 + Samsung INR18650-35E 3S1P)

| Parameter | Namespace | Wert | Beschreibung |
|---|---|---|---|
| `pack_charge_max_v` | `amr::battery` | 12.60 V | 3S Ladeschlussspannung |
| `threshold_warning_v` | `amr::battery` | 10.0 V | Stufe 1: Soft-Warnung |
| `threshold_motor_shutdown_v` | `amr::battery` | 9.5 V | Stufe 2: Motoren + Servos aus |
| `threshold_system_shutdown_v` | `amr::battery` | 9.0 V | Stufe 3: System-Shutdown |
| `threshold_bms_disconnect_v` | `amr::battery` | 7.5 V | Stufe 4: BMS trennt Last |
| `threshold_hysteresis_v` | `amr::battery` | 0.3 V | Wiedereinschalt-Hysterese |
| `capacity_design_ah` | `amr::battery` | 3.35 Ah | Design-Kapazitaet |
| `fuse_rating_a` | `amr::battery` | 10 A | KFZ-Flachsicherung |

SOC-Schaetzung via linearer Interpolation zwischen BMS-Disconnect (0%) und Ladeschluss (100%).

Unterspannungs-Kaskade: Bei < 9.5 V werden `/battery_shutdown` (true) publiziert und Servos via `allOff()` abgeschaltet. Erholung bei > 9.8 V (Hysterese 0.3 V) reaktiviert Servos via `clearAllOff()`.

### Servo (PCA9685 + MG996R/MG90S)

| Parameter | Namespace | Wert | Beschreibung |
|---|---|---|---|
| `ch_pan` / `ch_tilt` | `amr::servo` | 0 / 1 | PCA9685-Kanaele |
| `ticks_min` / `ticks_max` | `amr::servo` | 123 / 492 | PWM-Bereich fuer 0-180 deg |
| `pca_prescale` | `amr::servo` | 121 | ~50 Hz PWM-Frequenz |
| `ramp_deg_per_step` | `amr::servo` | 2.0 deg | Standard-Ramp-Geschwindigkeit |
| `pan_offset_deg` | `amr::servo` | +8 deg | Kalibrierung (90 deg = geradeaus) |
| `tilt_offset_deg` | `amr::servo` | +1 deg | Kalibrierung |
| Pan-Bereich | `amr::servo` | 45-135 deg | Logisch, vor Offset |
| Tilt-Bereich | `amr::servo` | 80-135 deg | Logisch, vor Offset |

Servo-I2C-Writes laufen auf Core 0 (`loop()`, 5 Hz Polling). `setAngle()` wird direkt aufgerufen (keine Ramp im aktuellen Code). Ramp-Speed konfigurierbar via `/hardware_cmd` (y-Feld, 1-10 deg/Step).

## Safety-Mechanismen

| Mechanismus | Beschreibung |
|---|---|
| **Inter-Core Watchdog** | Core 0 ueberwacht `core1_heartbeat`, LED Dauer-An bei 50 Misses |
| **Batterie-Kaskade** | 4-stufig: Warnung --> Motor-Shutdown --> System-Shutdown --> BMS-Disconnect |
| **Servo-Notaus** | `allOff()` bei Unterspannung (via `deferred_servo_power` Cross-Core) |
| **I2C-Contention-Zaehler** | Zaehlt fehlgeschlagene Mutex-Acquires fuer Diagnose |
| **ISR-Timeout** | Ultraschall-Echo > 20 ms --> max_range + 0.01 m (ungueltig) |

### LED-Status (Interne Onboard-LED, GPIO 21, Active Low)

| Zustand | Pattern | Bedeutung |
|---|---|---|
| Agent-Suche | Langsames Blinken (100/900 ms) | Firmware wartet auf micro-ROS Agent |
| Init-Fehler | Schnelles Blinken (200/200 ms) | micro-ROS Init fehlgeschlagen |
| Normal | Heartbeat-Toggle (~400 ms) | `loop()` laeuft |
| Watchdog-Alarm | Dauer-An | Core 1 blockiert |
| Publish-Fehler | Dauer-An | `rcl_publish` Rueckgabefehler |

## CAN-Bus (TWAI, parallel zu micro-ROS)

Alle Sensor-Daten werden zusaetzlich via CAN 2.0B (1 Mbit/s, SN65HVD230) gesendet. CAN-Init-Fehler sind nicht fatal — die Firmware laeuft ohne Transceiver weiter. Alle CAN-Sends laufen auf Core 1 (`sensorTask`), damit sie unabhaengig vom micro-ROS-Verbindungsstatus arbeiten.

| CAN-ID | Laenge | Inhalt | Soll-Rate | Gemessen |
|---|---|---|---|---|
| `0x110` | 4 B | HC-SR04 Distanz [float32 LE, m] | 10 Hz | ~5.6 Hz |
| `0x120` | 1 B | Cliff-Status (0x00=OK, 0x01=Cliff) | 20 Hz | ~11 Hz |
| `0x130` | 8 B | IMU: ax,ay,az [int16 mg] + gz [int16 0.01 rad/s] | 50 Hz | ~26 Hz |
| `0x131` | 4 B | IMU Heading [float32 LE, rad] | 50 Hz | ~26 Hz |
| `0x140` | 6 B | Batterie: V [uint16 mV] + I [int16 mA] + P [uint16 mW] | 2 Hz | ~1.1 Hz |
| `0x141` | 1 B | Battery Shutdown (0x00=OK, 0x01=Shutdown) | Event | Event |
| `0x1F0` | 2 B | Heartbeat: Flags [uint8] + Uptime [uint8 s%256] | 1 Hz | 1 Hz |

Gemessene Raten liegen unter den Soll-Raten, da I2C-Zugriffe und Mutex-Contention die effektiven Zykluszeiten verlaengern.

## Diagnose-Environment: `servo_test`

Interaktives Servo-Kalibrierungsprogramm (`src/servo_test.cpp`) ohne micro-ROS:

| Befehl | Aktion |
|---|---|
| `p` / `t` | Achse waehlen (Pan / Tilt) |
| `+` / `-` | ±1 deg |
| `f` / `b` | ±0.5 deg (Feineinstellung) |
| Zahl + Enter | Direkte Winkelposition (z.B. `92`) |
| `c` | Aktuelle Neutralposition ausgeben |

Gibt rohe PWM-Tick-Werte fuer Kalibrierung aus. Baut schnell (~30 s, ohne micro-ROS). Initialisiert I2C mit demselben `delay(2000)` + PCA9685-Retry-Pattern wie die Hauptfirmware.

## Hinweise

- **C++17**: Kompiliert mit `-std=gnu++17` (GCC 8.4.0). `std::clamp` und `inline constexpr` verfuegbar.
- **Kein Reconnect**: Nach Agent-Verlust muss der ESP32 per Reset neu verbunden werden.
- **USB-CDC**: `-DARDUINO_USB_CDC_ON_BOOT=1` — Serial ist USB, nicht UART0.
- **I2C in Callbacks**: Verboten. Deferred-Pattern (Callback --> RAM-Struct --> loop()/sensorTask --> I2C) ist Pflicht.
- **ISR-Constraint**: `IRAM_ATTR`-Funktionen muessen im globalen Scope liegen (kein Namespace). Volatile ISR-Variablen als Globals in `main.cpp`.

## Lizenz

MIT -- siehe [`../LICENSE`](../LICENSE).
