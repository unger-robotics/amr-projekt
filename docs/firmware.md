---
description: >-
  Referenzdokumentation fuer die MCU-Firmware auf beiden ESP32-S3-Knoten
  mit Modulen und Konfiguration.
---

# Firmware

## Zweck

Referenz fuer die MCU-Firmware auf den beiden ESP32-S3-Knoten (Drive-Node und Sensor-Node). Beschreibt Architektur, Module, Konfiguration, Kommunikation und Constraints.

## Regel

Firmware-spezifische Details (Dual-Core-Pattern, ISR, I2C, CAN-IDs) gehoeren nur in diese Datei. Topic-Definitionen und QoS stehen in `docs/ros2_system.md`.

---

## 1. Zwei-Node-Architektur

Die Firmware besteht aus zwei getrennten PlatformIO-Projekten. Jeder ESP32-S3 erhaelt eine eigene micro-ROS-Library (statisch kompiliert).

| Eigenschaft | Drive-Node | Sensor-Node |
|---|---|---|
| **Verzeichnis** | `amr/mcu_firmware/drive_node/` | `amr/mcu_firmware/sensor_node/` |
| **Konfiguration** | `include/config_drive.h` (v4.0.0) | `include/config_sensors.h` (v3.0.0) |
| **udev-Symlink** | `/dev/amr_drive` | `/dev/amr_sensor` |
| **Baudrate** | 921600 (micro-ROS UART) | 921600 (micro-ROS UART) |
| **Funktion** | Motoren, PID, Encoder, Odometrie, LED | IMU, Ultraschall, Cliff, Batterie, Servo |
| **CAN-ID-Bereich** | 0x200–0x2FF | 0x110–0x1F0 |

Detaillierte Firmware-Architektur: `amr/mcu_firmware/CLAUDE.md`.

---

## 2. Dual-Core-Pattern (FreeRTOS)

Beide Knoten verwenden dasselbe Pattern:

```
Core 0 (App-Core, loop()):
  - micro-ROS Executor: spin_some() fuer Publisher und Subscriber
  - Servo-I2C-Writes (nur Sensor-Node, PCA9685)
  - ~500 Hz Zyklusrate

Core 1 (FreeRTOS Task):
  - Drive-Node: PID-Regelung (50 Hz), Encoder-Polling, CAN-Sends
  - Sensor-Node: IMU-Reads (50 Hz), Ultraschall (10 Hz), Cliff (20 Hz), Batterie (2 Hz), CAN-Sends
  - Inter-Core Heartbeat-Check (Watchdog)
```

### Synchronisation

- **`mutex`** (SemaphoreHandle_t): Schuetzt `SharedData`-Struct zwischen Core 0 und Core 1
- **`i2c_mutex`** (nur Sensor-Node): Schuetzt I2C-Bus, 5 ms Timeout mit `xSemaphoreTake()`
- I2C-Aufteilung Sensor-Node: Reads (MPU6050, INA260) auf Core 1, Writes (PCA9685) auf Core 0

### Watchdog

Core 0 prueft periodisch `core1_heartbeat` (Zeitstempel von Core 1). Bei Ausbleiben > Timeout wird ein Fehler gemeldet.

---

## 3. Module Drive-Node

| Datei | Klasse/Funktion | Beschreibung |
|---|---|---|
| `src/main.cpp` | — | Setup, loop(), ISR-Globals (volatile), FreeRTOS Task |
| `include/config_drive.h` | `amr::hal::`, `amr::pid::`, `amr::pwm::`, `amr::kinematics::`, `amr::timing::`, `amr::can::` | Zentrale Konfiguration als `inline constexpr` mit `static_assert` |
| `include/robot_hal.hpp` | `RobotHAL` | Motorsteuerung (Cytron MDD3A), PWM (LEDC), Encoder-ISR (Quadratur-Dekoder) |
| `include/pid_controller.hpp` | `PidController` (Template) | PID-Regler mit Anti-Windup, konfigurierbar ueber `amr::pid::` |
| `include/diff_drive_kinematics.hpp` | `DiffDriveKinematics`, `WheelTargets`, `RobotState` | Zweiradfahr-Kinematik: (v, w) → (v_l, v_r), Odometrie-Integration |
| `include/twai_can.hpp` | `TwaiCan` | CAN 2.0B Sender (TWAI, 1 Mbit/s), IDs 0x200–0x2FF |

### PID-Regelung (50 Hz, Core 1)

```
Encoder-Ticks → Ist-Geschwindigkeit (m/s) → PID → PWM-Duty → Motor
                                                ↑
                                      Soll-Geschwindigkeit (aus /cmd_vel)
```

Parameter (`amr::pid::`): Kp, Ki, Kd, Anti-Windup-Grenzen, Deadzone-Kompensation.

### LED-Steuerung (MOSFET-PWM)

SMD 5050 LED-Streifen via IRLZ24N MOSFET, LEDC Kanal 4, konfigurierbar ueber `/hardware_cmd` (z-Feld = LED-PWM 0–255). Statusanzeige: Idle (Cyan pulsierend), Fahrt (Gruen), Fehler (Rot blinkend).

---

## 4. Module Sensor-Node

| Datei | Klasse/Funktion | Beschreibung |
|---|---|---|
| `src/main.cpp` | — | Setup, loop(), ISR-Globals, FreeRTOS Task, I2C-Init |
| `include/config_sensors.h` | `amr::hal::`, `amr::sensor::`, `amr::imu::`, `amr::battery::`, `amr::servo::`, `amr::i2c::`, `amr::ina260::`, `amr::can::` | Zentrale Konfiguration |
| `include/range_sensor.hpp` | `RangeSensor` | HC-SR04 Ultraschall, ISR-basiert (Trigger/tryRead-Pattern) |
| `include/cliff_sensor.hpp` | `CliffSensor` | MH-B IR Cliff-Sensor, GPIO-Poll |
| `include/mpu6050.hpp` | `MPU6050` | 6-Achsen IMU (I2C, Addr 0x68), Gyro + Accel, Komplementaerfilter (alpha=0.98 Gyro) |
| `include/ina260.hpp` | `INA260` | Leistungs-Monitor (I2C, Addr 0x40), Spannung/Strom/Power |
| `include/pca9685.hpp` | `PCA9685` | 16-Kanal PWM Servo-Controller (I2C, Addr 0x41), Pan/Tilt |
| `include/twai_can.hpp` | `TwaiCan` | CAN 2.0B Sender (TWAI, 1 Mbit/s), IDs 0x110–0x1F0 |

### I2C-Bus (Wire, 400 kHz)

Drei Geraete teilen sich den I2C-Bus:

| Geraet | Adresse | Zugriff | Core |
|---|---|---|---|
| MPU6050 | 0x68 | Read (50 Hz) | Core 1 |
| INA260 | 0x40 | Read (2 Hz) | Core 1 |
| PCA9685 | 0x41 | Write (bei Aenderung) | Core 0 |

**Init-Reihenfolge:** PCA9685 vor MPU6050 und INA260 initialisieren (sauberer I2C-Bus). `delay(2000)` vor `Wire.begin()`.

### Batterie-Ueberwachung (INA260)

- Spannung, Strom, Leistung mit 2 Hz
- Unterspannungsschutz: < 9.5 V → `/battery_shutdown` (Event) an Drive-Node
- Prozentberechnung: Lineare Interpolation 9.0–12.6 V (3S Li-Ion)

---

## 5. CAN-Bus (Optional, TWAI 1 Mbit/s)

Hardware: SN65HVD230 CAN-Transceiver auf beiden Knoten + MCP2515/SocketCAN auf Pi 5.

### Drive-Node CAN-Frames (0x200–0x2FF)

| ID | Inhalt | Rate | Bytes |
|---|---|---|---|
| `0x200` | Odom Position (x, y als float32 LE) | 20 Hz | 8 |
| `0x201` | Odom Heading + Speed (yaw, v_linear als float32 LE) | 20 Hz | 8 |
| `0x210` | Rad-Geschwindigkeit (L, R als float32 rad/s) | 10 Hz | 8 |
| `0x220` | Motor-PWM (L, R als int16) | 10 Hz | 4 |
| `0x2F0` | Heartbeat (flags uint8 + uptime_mod256 uint8) | 1 Hz | 2 |

### Sensor-Node CAN-Frames (0x110–0x1F0)

| ID | Inhalt | Rate | Bytes |
|---|---|---|---|
| `0x110` | Ultraschall Range (float32 LE, Meter) | 10 Hz | 4 |
| `0x120` | Cliff (uint8: 0=OK, 1=Cliff) | 20 Hz | 1 |
| `0x130` | IMU ax, ay, az (mg) + gz (0.01 rad/s) (4x int16) | 50 Hz | 8 |
| `0x131` | IMU Heading (float als float32) | 50 Hz | 4 |
| `0x140` | Batterie V/I/P (uint16 mV + int16 mA + uint16 mW) | 2 Hz | 6 |
| `0x141` | Battery Shutdown (uint8: 0=OK, 1=Shutdown) | Event | 1 |
| `0x1F0` | Heartbeat (flags uint8 + uptime_mod256 uint8) | 1 Hz | 2 |

### CAN-Notstopp-Redundanzpfad

Drive-Node empfaengt Cliff (0x120) und Battery-Shutdown (0x141) vom Sensor-Node ueber CAN und stoppt Motoren direkt — unabhaengig von Pi 5 und micro-ROS. Details: `docs/architecture.md`.

---

## 6. Build-Befehle

```bash
# Drive-Node
cd amr/mcu_firmware/drive_node
pio run -e drive_node                      # Kompilieren
pio run -e drive_node -t upload -t monitor # Upload + Serial Monitor
pio run -e led_test -t upload -t monitor   # LED/MOSFET-Diagnose (ohne micro-ROS)

# Sensor-Node
cd amr/mcu_firmware/sensor_node
pio run -e sensor_node                      # Kompilieren
pio run -e sensor_node -t upload -t monitor # Upload + Serial Monitor
pio run -e servo_test -t upload -t monitor  # Servo-Kalibrierung (Pan/Tilt)
```

**Wichtig:** Immer `-e <environment>` angeben! Ohne `-e` flasht PlatformIO alle Environments — das letzte ueberschreibt die vorherigen.

Erster Build pro Knoten: ~15 Min (micro-ROS aus Source). Folgebuilds gecacht.

---

## 7. Code-Stil und Linting

- **Sprache:** C++17 (`-std=gnu++17`, GCC 8.4.0)
- **Zeilenlaenge:** 100 Zeichen
- **Einrueckung:** 4 Spaces
- **Klammern:** Attach (K&R)
- **Benennung:** `CamelCase` Klassen, `camelBack` Methoden, `lower_case` Funktionen/Variablen/Parameter
- **Konfiguration:** `.clang-format` (LLVM-basiert)

```bash
clang-format --dry-run --Werror \
    amr/mcu_firmware/drive_node/src/*.cpp \
    amr/mcu_firmware/drive_node/include/*.hpp \
    amr/mcu_firmware/sensor_node/src/*.cpp \
    amr/mcu_firmware/sensor_node/include/*.hpp
```

---

## 8. Harte Constraints

- **Typen:** `int32_t`/`uint8_t`/`int16_t` statt `int`/`long`. Encoder-Zaehler: `volatile int32_t`.
- **ISR:** `IRAM_ATTR`, globaler Scope (kein Namespace), volatile Globals in `main.cpp`. GPIO-Register: `(GPIO.in >> pin) & 0x1`.
- **Speicher:** Keine dynamische Allokation zur Laufzeit.
- **I2C in Callbacks:** Verboten. Deferred-Pattern: Callback → RAM-Struct → loop()/sensorTask → I2C.
- **micro-ROS QoS:** `rclc_publisher_init_default()` (Reliable) fuer Nachrichten > 512 Bytes (XRCE-DDS MTU).
- **Keine `#define`-Makros** fuer Pins oder PWM — `amr::hal::` Namespace mit typisierten Konstanten.
- **Getrennte Projekte:** Drive-Node und Sensor-Node werden immer getrennt gebaut, geflasht und betrieben.

---

## 9. Abgrenzung

- Topic-Definitionen, QoS und TF-Baum: `docs/ros2_system.md`
- CAN-Notstopp-Architektur: `docs/architecture.md`
- Serielle Port-Zuordnung (udev): `docs/serial_port_management.md`
- Hardware-Spezifikationen: `hardware/docs/`
- Detaillierte Firmware-Referenz: `amr/mcu_firmware/CLAUDE.md`
