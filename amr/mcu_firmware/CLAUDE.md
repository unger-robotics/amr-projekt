# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kontext

Monorepo fuer zwei ESP32-S3 Mikrocontroller (beide Seeed Studio XIAO ESP32-S3) eines autonomen mobilen Roboters (AMR). Kommunikation mit Raspberry Pi 5 ueber micro-ROS/UART (Serial Transport, Humble). Uebergeordnete Projektdokumentation in `../../CLAUDE.md`.

## Zwei-Node-Architektur

Die Firmware ist in zwei isolierte PlatformIO-Projekte aufgeteilt, da micro-ROS statische Libraries erzeugt, die an die Node-Konfiguration gebunden sind. Geteilte `.pio`-Caches wuerden sich gegenseitig ueberschreiben.

| Node | Verzeichnis | udev-Symlink | Funktion | Regelfrequenz |
|---|---|---|---|---|
| **Drive-Node** (#1) | `drive_node/` | `/dev/amr_drive` | Antrieb, PID, Odometrie, LED | 50 Hz |
| **Sensor-Node** (#2) | `sensor_node/` | `/dev/amr_sensor` | Ultraschall, Cliff, IMU (MPU6050), Batterie (INA260), Servo (PCA9685) | 50 Hz (IMU), 10/20 Hz (Sonar/Cliff), 2 Hz (Bat) |

Beide Nodes nutzen dasselbe Dual-Core-Pattern: Core 0 = micro-ROS Executor (Publisher/Subscriber), Core 1 = Echtzeit-Datenerfassung (FreeRTOS Task, Mutex-geschuetzt). Inter-Core-Watchdog in beiden Nodes (Core 0 prueft `core1_heartbeat`).

## Verzeichnisstruktur

```
mcu_firmware/
  drive_node/
    include/          # Header: config_drive.h, 4 hpp-Module (robot_hal, pid_controller, diff_drive_kinematics, twai_can)
    src/              # main.cpp, led_ramp_test.cpp
    platformio.ini
  sensor_node/
    include/          # Header: config_sensors.h, 6 hpp-Module (range_sensor, cliff_sensor, mpu6050, ina260, pca9685, twai_can)
    src/              # main.cpp
    platformio.ini
```

## Build-Befehle

```bash
# Drive-Node (Antrieb):
cd drive_node && pio run                      # Kompilieren
cd drive_node && pio run -t upload -t monitor # Upload + Monitor
cd drive_node && pio run -e led_test -t upload -t monitor  # MOSFET-Diagnose (ohne micro-ROS, ~5s)

# Sensor-Node (Ultraschall + Cliff):
cd sensor_node && pio run                      # Kompilieren
cd sensor_node && pio run -t upload -t monitor # Upload + Monitor
```

Erster Build pro Node dauert ~15 Min (micro-ROS aus Source). Folgebuilds gecached. Es gibt keine Unit-Tests.

## Konfiguration

Jeder Node hat seine eigene Config im lokalen `include/`-Ordner (eingebunden via `-I include`):

- `drive_node/include/config_drive.h` (v4.1.0): HAL-Pins (`amr::hal::`), Antrieb, PID, Kinematik, LED, CAN-Bus (`amr::can::`) — kein I2C
- `sensor_node/include/config_sensors.h` (v3.1.0): HAL-Pins (`amr::hal::`), Ultraschall-Timing, Cliff, Sensorphysik, IMU (`amr::imu::`), Batterie (`amr::battery::`), Servo (`amr::servo::`), I2C-Bus (`amr::i2c::`, `amr::ina260::`), CAN-Bus (`amr::can::`)

Beide Configs verwenden `inline constexpr` in `amr::`-Namespaces mit `static_assert` Compile-Time-Validierung. Keine `#define`-Makros fuer Pins oder PWM-Kanaele — alle in `amr::hal::` als typisierte Konstanten.

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
| `/imu` | `sensor_msgs/Imu` | Sensor | 50 Hz |
| `/battery` | `sensor_msgs/BatteryState` | Sensor (INA260) | 2 Hz |
| `/cmd_vel` | `geometry_msgs/Twist` | Drive (Sub) | — |
| `/servo_cmd` | `geometry_msgs/Point` | Sensor (Sub) | — |
| `/hardware_cmd` | `geometry_msgs/Point` | Drive (Sub: x=Motor-Limit, z=LED-PWM), Sensor (Sub: y=Servo-Speed) | — |
| `/battery_shutdown` | `std_msgs/Bool` | Sensor (Pub) → Drive (Sub), Unterspannungs-Notaus | — |
| `/range/front` | `sensor_msgs/Range` | Sensor | 10 Hz |
| `/cliff` | `std_msgs/Bool` | Sensor | 20 Hz |

### CAN-Bus (TWAI, parallel zu micro-ROS, beide Nodes)

Sensor- und Antriebs-Daten werden zusaetzlich via CAN 2.0B (500 kbit/s, SN65HVD230 → SBC-CAN01) gesendet. CAN-Fehler sind nicht fatal. Hardware: `../../hardware/can-bus/CAN-Bus.md`.

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
| `0x110` | Range [float32 m] | 10 Hz |
| `0x120` | Cliff [1 B] | 20 Hz |
| `0x130` | IMU Accel+GyroZ [8 B] | 50 Hz |
| `0x131` | IMU Heading [float32 rad] | 50 Hz |
| `0x140` | Batterie V/I/P [6 B] | 2 Hz |
| `0x141` | Battery Shutdown [1 B] | Event |
| `0x1F0` | Heartbeat [2 B] | 1 Hz |

## Firmware-Constraints

- **C++17** (`-std=gnu++17`, GCC 8.4.0), `std::clamp` und `inline constexpr` verfuegbar
- **Typen**: `int32_t`/`uint8_t`/`int16_t` statt `int`/`long`, Encoder-Zaehler `volatile int32_t`
- **ISR**: Alle ISR-Funktionen mit `IRAM_ATTR` markieren, globaler Scope (kein Namespace)
- **Speicher**: Keine dynamische Allokation zur Laufzeit
- **I2C in Callbacks**: Wire-Operationen schlagen STILL FEHL in `rclc_executor_spin_some()` — Deferred-Pattern verwenden (Sensor-Node betroffen: MPU6050, INA260, PCA9685 via `i2c_mutex`)
- **micro-ROS QoS**: `rclc_publisher_init_default()` (Reliable) fuer Nachrichten > 512 Bytes (XRCE-DDS MTU), da Best-Effort keine Fragmentierung unterstuetzt

## Detaillierte Dokumentation

- `drive_node/README.md`: Hardware, Architektur, Module, LED-Status, Konfiguration
- `sensor_node/README.md`: Hardware, Architektur, Module, Topics
