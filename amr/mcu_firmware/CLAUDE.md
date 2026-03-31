# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kontext

Monorepo fuer zwei ESP32-S3 Mikrocontroller (beide Seeed Studio XIAO ESP32-S3) eines autonomen mobilen Roboters (AMR). Kommunikation mit Raspberry Pi 5 ueber micro-ROS/UART (Serial Transport, Humble). Uebergeordnete Projektdokumentation in `../../CLAUDE.md`.

## Zwei-Knoten-Architektur

Die Firmware ist in zwei isolierte PlatformIO-Projekte aufgeteilt, da micro-ROS statische Libraries erzeugt, die an die Knoten-Konfiguration gebunden sind. Geteilte `.pio`-Caches wuerden sich gegenseitig ueberschreiben.

| Node | Verzeichnis | udev-Symlink | Funktion | Regelfrequenz |
|---|---|---|---|---|
| **Drive-Node** (#1) | `drive_node/` | `/dev/amr_drive` | Antrieb, PID, Odometrie, LED | 50 Hz |
| **Sensor-Node** (#2) | `sensor_node/` | `/dev/amr_sensor` | Ultraschall, Cliff, IMU (MPU6050), Batterie (INA260), Servo (PCA9685) | 50 Hz (IMU), 10/20 Hz (Sonar/Cliff), 2 Hz (Bat) |

Beide Knoten nutzen dasselbe Dual-Core-Pattern: Core 0 = micro-ROS Executor (Publisher/Subscriber), Core 1 = Echtzeit-Datenerfassung + CAN-Bus-Sends (FreeRTOS Task, Mutex-geschuetzt). CAN-Sends laufen in Core 1, damit sie unabhaengig vom micro-ROS Agent funktionieren (`setup()` blockiert bis Agent verbunden). Inter-Core-Watchdog in beiden Knoten (Core 0 prueft `core1_heartbeat`).

**I2C-Aufteilung Sensor-Node**: Lese-Operationen (MPU6050 IMU, INA260 Batterie) auf Core 1 (`sensorTask`), Schreib-Operationen (PCA9685 Servo) auf Core 0 (`loop()`, 5 Hz Polling). Beide ueber `i2c_mutex`. PCA9685 muss VOR IMU/INA260 initialisiert werden (benoetigt sauberen I2C-Bus, `delay(2000)` vor `Wire.begin()`). GPIO-Sensoren (Ultraschall-ISR, Cliff) erst NACH I2C-Init.

### Sensor-Node: ISR-basierter Ultraschall + I2C-Contention-Fixes

- **Ultraschall**: ISR-basiert (nicht blockierend), `trigger()` + `tryRead()` Pattern statt `pulseIn()`
- **ISR**: Volatile Globals in `main.cpp` (nicht im Namespace — IRAM_ATTR Linker-Constraint), GPIO-Register-Zugriff `(GPIO.in >> pin) & 0x1`
- **I2C-Contention**: Alle I2C-Reads (MPU6050, INA260) laufen in Core 1 (`sensorTask`), Core 0 liest nur aus `SharedSensorData` via `mutex`
- **Batterie**: `SharedSensorData` enthaelt `bat_voltage/bat_current/bat_power/bat_read_ok`, Core 0 kopiert und publiziert
- **Servo-Ramp**: Rate-limitiert auf 20 Hz mit `needsRamp()` Early-Return (I2C-freie Pruefung vor Mutex-Acquire)
- **UART-Baudrate**: 921600 Baud (micro-ROS Agent + Firmware)

## Verzeichnisstruktur

```
mcu_firmware/
  drive_node/
    include/          # Header: config_drive.h, 4 hpp-Module (robot_hal, pid_controller, diff_drive_kinematics, twai_can)
    src/              # main.cpp, led_ramp_test.cpp
    platformio.ini
  sensor_node/
    include/          # Header: config_sensors.h, 6 hpp-Module (range_sensor, cliff_sensor, mpu6050, ina260, pca9685, twai_can)
    src/              # main.cpp, servo_test.cpp
    platformio.ini
```

## Build-Befehle

**Wichtig:** Beim Upload immer `-e <environment>` angeben! `pio run -t upload` ohne `-e` flasht ALLE Environments — das letzte ueberschreibt die vorherigen.

```bash
# Drive-Node (Antrieb):
cd drive_node && pio run -e drive_node                      # Kompilieren
cd drive_node && pio run -e drive_node -t upload -t monitor # Upload + Monitor
cd drive_node && pio run -e led_test -t upload -t monitor   # LED/MOSFET-Diagnose (ohne micro-ROS, ~5s)

# Sensor-Node (Ultraschall + Cliff):
cd sensor_node && pio run -e sensor_node                      # Kompilieren
cd sensor_node && pio run -e sensor_node -t upload -t monitor # Upload + Monitor
cd sensor_node && pio run -e servo_test -t upload -t monitor  # Servo-Kalibrierung (Pan/Tilt)
```

Erster Build pro Knoten dauert ~15 Min (micro-ROS aus Source). Folgebuilds gecached. Es gibt keine Unit-Tests.

## Konfiguration

Jeder Knoten hat seine eigene Config im lokalen `include/`-Ordner (eingebunden via `-I include`):

- `drive_node/include/config_drive.h` (v4.0.0): HAL-Pins (`amr::hal::`), Antrieb, PID, Kinematik, LED, CAN-Bus (`amr::can::`) — kein I2C
- `sensor_node/include/config_sensors.h` (v3.0.0): HAL-Pins (`amr::hal::`), Ultraschall-Timing, Cliff, Sensorphysik, IMU (`amr::imu::`), Batterie (`amr::battery::`), Servo (`amr::servo::`), I2C-Bus (`amr::i2c::`, `amr::ina260::`), CAN-Bus (`amr::can::`)

Beide Configs verwenden `inline constexpr` in `amr::`-Namespaces mit `static_assert` Compile-Time-Validierung. Keine `#define`-Makros fuer Pins oder PWM-Kanaele — alle in `amr::hal::` als typisierte Konstanten.

## Library-Abhaengigkeiten

- **Drive-Node**: Nur micro-ROS (keine I2C-Libraries)
- **Sensor-Node**: micro-ROS + Adafruit BusIO/INA260/MPU6050/PWM Servo/Unified Sensor als PlatformIO-Abhaengigkeiten. Die Adafruit-Libraries dienen als transitive Abhaengigkeit — die eigentlichen I2C-Treiber sind eigene Header-Only-Implementierungen in `include/` (`mpu6050.hpp`, `ina260.hpp`, `pca9685.hpp`)

## Namespace-Konvention

Beide Nodes nutzen konsistente C++-Namespaces:

| Namespace | Verwendung | Node |
|---|---|---|
| `amr::hal` | GPIO-Pins, PWM-Kanaele, Richtungsfaktoren | Beide |
| `amr::hardware` | Sensor-/Aktor-Klassen (RobotHAL, RangeSensor, CliffSensor) | Beide |
| `amr::control` | PidController | Drive |
| `amr::kinematics` | DiffDriveKinematics, WheelTargets, RobotState | Drive |
| `amr::drivers` | I2C-Treiber (MPU6050, INA260, PCA9685), TWAI CAN-Bus (TwaiCan) | Beide |
| `amr::pid`, `amr::pwm`, `amr::timing` | Regelparameter | Drive |
| `amr::imu` | IMU-Parameter | Sensor |
| `amr::battery`, `amr::servo`, `amr::i2c`, `amr::ina260` | Geraeteparameter | Sensor |
| `amr::safety`, `amr::regulator` | Sicherheitsschwellen | Drive |
| `amr::sensor` | Physikalische Sensorparameter (Schall, Bereiche) | Sensor |
| `amr::can` | CAN-Bus Konfiguration (IDs, Bitrate, Heartbeat) | Beide |

`main.cpp` beider Nodes verwendet `using`-Deklarationen fuer Klassen aus diesen Namespaces.

## USB-Port-Zuordnung

Beide ESP32-S3 haben identische USB VID/PID — die Linux-Enumeration (`/dev/ttyACM0` vs `/dev/ttyACM1`) ist nicht-deterministisch. Loesung: udev-Regeln basierend auf der Hardware-Seriennummer (`ATTRS{serial}`), die stabile Symlinks `/dev/amr_drive` und `/dev/amr_sensor` erzeugen. Setup via `../../scripts/udev_setup.sh`. Die `platformio.ini` beider Nodes verwenden diese Symlinks als `upload_port`/`monitor_port`.

## ROS2-Topics

| Topic | Typ | Node | Rate |
|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | Drive (Pub), Sensor (Sub fuer Heading-Fusion) | 20 Hz |
| `/imu` | `sensor_msgs/Imu` | Sensor | 50 Hz (real ~33 Hz, I2C-limitiert) |
| `/battery` | `sensor_msgs/BatteryState` | Sensor (INA260) | 2 Hz |
| `/cmd_vel` | `geometry_msgs/Twist` | Drive (Sub) | — |
| `/servo_cmd` | `geometry_msgs/Point` | Sensor (Sub) | — |
| `/hardware_cmd` | `geometry_msgs/Point` | Drive (Sub: x=Motor-Limit, z=LED-PWM), Sensor (Sub: y=Servo-Speed) | — |
| `/battery_shutdown` | `std_msgs/Bool` | Sensor (Pub) → Drive (Sub), Unterspannungs-Notaus | — |
| `/range/front` | `sensor_msgs/Range` | Sensor | 10 Hz |
| `/cliff` | `std_msgs/Bool` | Sensor | 20 Hz |

### CAN-Bus (TWAI, parallel zu micro-ROS, beide Nodes)

Sensor- und Antriebs-Daten werden zusaetzlich via CAN 2.0B (1 Mbit/s, SN65HVD230 → SBC-CAN01) gesendet. CAN-Fehler sind nicht fatal. Hardware: `../../hardware/can-bus/CAN-Bus.md`.

**Drive-Node (0x200-0x2FF):**

| CAN-ID | Inhalt | Rate |
|---|---|---|
| `0x200` | Odom Position x,y [2x float32] | 20 Hz |
| `0x201` | Odom Heading+Speed [2x float32] | 20 Hz |
| `0x210` | Encoder L/R [2x float32 rad/s] | 10 Hz |
| `0x220` | Motor-PWM L/R [2x int16] | 10 Hz |
| `0x2F0` | Heartbeat [2 B] | 1 Hz |

**Sensor-Node (0x110-0x1F0):**

| CAN-ID | Inhalt | Rate |
|---|---|---|
| `0x110` | Range [float32 m] | 10 Hz (gemessen: 10,0 Hz) |
| `0x120` | Cliff [1 B] | 20 Hz (gemessen: 20,0 Hz) |
| `0x130` | IMU Accel+GyroZ [8 B] | 50 Hz (gemessen: 50,0 Hz) |
| `0x131` | IMU Heading [float32 rad] | 50 Hz (gemessen: 50,0 Hz) |
| `0x140` | Batterie V/I/P [6 B] | 2 Hz (gemessen: 2,0 Hz) |
| `0x141` | Battery Shutdown [1 B] | Event |
| `0x1F0` | Heartbeat [2 B] | 1 Hz |

## Firmware-Constraints

- **C++17** (`-std=gnu++17`, GCC 8.4.0), `std::clamp` und `inline constexpr` verfuegbar
- **Typen**: `int32_t`/`uint8_t`/`int16_t` statt `int`/`long`, Encoder-Zaehler `volatile int32_t`
- **ISR**: Alle ISR-Funktionen mit `IRAM_ATTR` markieren, globaler Scope (kein Namespace). Volatile ISR-Variablen als Globals in `main.cpp` (nicht `inline constexpr` im Header — verursacht "dangerous relocation: l32r" Linker-Fehler). GPIO-Pin-Zustand via `GPIO.in >> pin & 0x1` lesen (nicht `digitalRead()` in ISR)
- **Speicher**: Keine dynamische Allokation zur Laufzeit
- **I2C in Callbacks**: Keine Wire-Operationen in `rclc_executor_spin_some()` Callbacks — Deferred-Pattern verwenden (Callback schreibt in volatile RAM-Struct, loop()/sensorTask fuehrt I2C aus). Sensor-Node: I2C-Reads auf Core 1, I2C-Writes (PCA9685) auf Core 0
- **micro-ROS QoS**: `rclc_publisher_init_default()` (Reliable) fuer Nachrichten > 512 Bytes (XRCE-DDS MTU), da Best-Effort keine Fragmentierung unterstuetzt
- **Kein Reconnect**: Verlust der micro-ROS-Agent-Verbindung erfordert ESP32 Power-Cycle (kein automatisches Wiederverbinden)
- **USB-CDC**: `-DARDUINO_USB_CDC_ON_BOOT=1` in beiden `platformio.ini` (Serial = USB, nicht UART0)
- **TWAI CAN-Bus**: `TWAI_GENERAL_CONFIG_DEFAULT` setzt `intr_flags = ESP_INTR_FLAG_LEVEL1`, der auf ESP32-S3 mit USB-CDC kollidieren kann (`ESP_ERR_NOT_FOUND` → `abort()`). Fix: `g_config.intr_flags = 0` fuer automatische Interrupt-Auswahl. In beiden `twai_can.hpp` angewendet
- **Boot-Reihenfolge**: `setup()` blockiert bei `rmw_uros_ping_agent()` bis der micro-ROS Agent den seriellen Port geoeffnet hat. Sensor-Node braucht nach Container-Start ggf. einen DTR/RTS-Reset

## Detaillierte Dokumentation

- `drive_node/README.md`: Hardware, Architektur, Module, LED-Status, Konfiguration
- `sensor_node/README.md`: Hardware, Architektur, Module, Topics
