---
description: >-
  Referenzdokumentation fuer die MCU-Firmware auf beiden ESP32-S3-Knoten
  mit Modulen und Konfiguration.
---

# Firmware

## Zweck

Referenz fuer die MCU-Firmware auf den beiden ESP32-S3-Knoten (Drive-Node und Sensor-Node). Beschreibt Architektur, Module, Konfiguration, Kommunikation und Constraints.

## Regel

Firmware-spezifische Details (Dual-Core-Pattern, ISR, I2C, CAN-IDs) gehoeren in die Unterseiten. Topic-Definitionen und QoS stehen in `docs/ros2_system.md`.

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
