---
description: >-
  Referenzdokumentation fuer die MCU-Firmware auf beiden ESP32-S3-Knoten
  mit Modulen und Konfiguration.
---

# Firmware

## Ueberblick

Die MCU-Firmware laeuft auf zwei Seeed Studio XIAO ESP32-S3 (Dual-Core Xtensa LX7, 240 MHz, 8 MB Flash, 8 MB PSRAM). Jeder Knoten ist ein eigenstaendiges PlatformIO-Projekt mit statisch kompilierter micro-ROS-Library. Kommunikation mit dem Raspberry Pi 5 ueber micro-ROS/UART (921600 Baud).

| Knoten | Verzeichnis | Funktion | Regelfrequenz |
|--------|-------------|----------|---------------|
| **Drive-Knoten** | `amr/mcu_firmware/drive_node/` | Antrieb, PID, Encoder, Odometrie, LED | 50 Hz |
| **Sensor-Knoten** | `amr/mcu_firmware/sensor_node/` | IMU, Ultraschall, Cliff, Batterie, Servo | 10–50 Hz |

## Dual-Core-Pattern (FreeRTOS)

Beide Knoten verwenden dasselbe Dual-Core-Pattern:

- **Core 0** (Arduino `loop()`): micro-ROS Executor (`spin_some()`), Servo-I2C-Writes (nur Sensor-Knoten), circa 500 Hz Zyklusrate
- **Core 1** (FreeRTOS Task): Echtzeit-Datenerfassung und CAN-Bus-Sends, Mutex-geschuetzt

CAN-Sends laufen auf Core 1, damit sie unabhaengig vom micro-ROS Agent funktionieren. Ein Inter-Core-Watchdog auf Core 0 prueft den Heartbeat von Core 1 und loest bei Ausbleiben einen Failsafe-Stopp aus.

## Schluesselmodule

**Drive-Knoten** (kein I2C):

- `robot_hal.hpp` — Motorsteuerung (Cytron MDD3A), PWM (LEDC), Encoder-ISR (Quadratur)
- `pid_controller.hpp` — PID-Regler mit Anti-Windup (Kp=0,4, Ki=0,1, Kd=0,0)
- `diff_drive_kinematics.hpp` — Inverskinematik (v, w) → (v_l, v_r), Odometrie-Integration

**Sensor-Knoten** (I2C-Bus 400 kHz: MPU6050 0x68, INA260 0x40, PCA9685 0x41 via A0-Loetbruecke):

- `mpu6050.hpp` — 6-Achsen IMU, Komplementaerfilter (alpha=0,98)
- `range_sensor.hpp` — HC-SR04 Ultraschall, ISR-basiert (nicht-blockierend)
- `cliff_sensor.hpp` — MH-B IR Cliff-Sensor, GPIO-Poll
- `ina260.hpp` — Batterieueberwachung (Spannung, Strom, Leistung)
- `pca9685.hpp` — 16-Kanal PWM Servo-Controller, Pan/Tilt

Beide Knoten: `twai_can.hpp` — CAN 2.0B Sender (TWAI, 1 Mbit/s). Drive-Knoten IDs 0x200–0x2FF, Sensor-Knoten IDs 0x110–0x1F0.

## Build-Einschraenkungen

- **C++17** (`-std=gnu++17`), `inline constexpr` Konfiguration mit `static_assert`
- **Keine dynamische Allokation** zur Laufzeit
- **ISR:** `IRAM_ATTR`, globaler Scope, volatile Globals
- **Kein I2C in Callbacks:** Deferred-Pattern (Callback → RAM-Struct → `loop()`/`sensorTask` → I2C)
- **micro-ROS QoS:** Reliable fuer Nachrichten > 512 Bytes (XRCE-DDS MTU, keine Best-Effort-Fragmentierung)

---

## Unterseiten

Die Firmware-Dokumentation ist in drei Fachseiten gegliedert:

- [FreeRTOS-Architektur](firmware/freertos.md) — Dual-Core-Pattern, Core-Zuordnung, Synchronisation, Watchdog, I2C-Bus
- [micro-ROS-Integration](firmware/micro-ros.md) — Zwei-Node-Architektur, Serial Transport, Build-Befehle, harte Constraints
- [Sensorik und Aktorik](firmware/sensors-actuators.md) — Module beider Knoten (Drive + Sensor), PID, LED, I2C-Geraete, CAN-Bus-Frames

---

## Code-Stil und Linting

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

## Abgrenzung

| Bereich | Dokument |
|---------|----------|
| Topic-Definitionen, QoS, TF-Baum | [Topics und TF-Baum](ros2_system.md) |
| CAN-Notstopp-Architektur | [Kommunikation](architecture/communication.md) |
| Serielle Port-Zuordnung (udev) | [Serielle Schnittstellen](serial_port_management.md) |
| Hardware-Spezifikationen | `hardware/docs/` |
| Detaillierte Firmware-Referenz | `amr/mcu_firmware/CLAUDE.md` |
