# ESP32 AMR Firmware

Echtzeit-Firmware fuer den Differentialantrieb eines autonomen mobilen Roboters (AMR). Empfaengt `cmd_vel` und publiziert Odometrie ueber micro-ROS/UART an einen Raspberry Pi 5.

## Hardware-Voraussetzungen

| Komponente | Typ |
|---|---|
| Mikrocontroller | Seeed Studio XIAO ESP32-S3 |
| Motortreiber | Cytron MDD3A (Dual-PWM-Modus) |
| Motoren | JGA25-370 DC-Getriebemotoren mit Hall-Encoder (A-only) |
| Verbindung zum Pi 5 | USB-CDC (Serial Transport, micro-ROS Humble) |

Pin-Belegung, Encoder-Kalibrierung und alle weiteren Parameter sind in `../../hardware/config.h` definiert.

## Build & Flash

[PlatformIO](https://platformio.org/) ist erforderlich. Umgebung: `seeed_xiao_esp32s3`.

```bash
pio run                       # Kompilieren
pio run -t upload             # Flashen (921600 Baud, /dev/ttyACM0)
pio run -t monitor            # Serieller Monitor (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor
```

Der erste Build laedt und kompiliert die micro-ROS-Libraries (~15 Min). Folgebuilds sind gecached.

## Architektur

Die Firmware nutzt beide ESP32-Kerne fuer deterministische Regelung:

```
Core 0 (loop)                      Core 1 (controlTask)
  micro-ROS Executor                 50 Hz PID-Regelschleife
  cmd_vel Subscriber          <-->   Inverse Kinematik
  Odometrie Publisher (20 Hz)        Encoder-Auswertung
  Inter-Core Watchdog                Vorwaertskinematik
                    \                /
                     SharedData (Mutex)
```

**Datenfluss:** `cmd_vel` --> Inverskinematik --> Beschleunigungsrampe --> PID --> Cytron MDD3A (PWM) --> Encoder-Feedback --> Vorwaertskinematik --> Odometrie-Publish

### Module (Header-only, `src/`)

| Datei | Aufgabe |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Subscriber/Publisher, Failsafe, Watchdog |
| `robot_hal.hpp` | GPIO-Init, Encoder-ISR (A-only mit Richtung aus PWM), PWM-Ansteuerung, Deadzone-Kompensation |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup, Ausgangsbereich [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik, Odometrie-Integration |

### Safety-Mechanismen

- **Failsafe**: Motoren stoppen nach 500 ms ohne `cmd_vel`
- **Inter-Core Watchdog**: Core 0 ueberwacht Heartbeat von Core 1, Notfall-Stopp bei Ausfall
- **Beschleunigungsrampe**: max. 5.0 rad/s^2 begrenzt Stromspitzen
- **Agent-Warten**: Firmware blockiert in `setup()` bis micro-ROS Agent erreichbar ist

## Konfiguration (`hardware/config.h`)

Alle Hardware-Parameter sind zentral in `../../hardware/config.h` definiert (Single Source of Truth, eingebunden via `-I../../hardware` Build-Flag):

| Parameter | Wert | Beschreibung |
|---|---|---|
| `WHEEL_DIAMETER` | 65 mm | Raddurchmesser |
| `WHEEL_BASE` | 178 mm | Spurbreite |
| `TICKS_PER_REV_LEFT/RIGHT` | ~374 | Encoder-Ticks pro Umdrehung (kalibriert) |
| `PWM_DEADZONE` | 35 | PWM-Schwelle unter der Motoren nicht anlaufen |
| `CONTROL_LOOP_HZ` | 50 Hz | PID-Regelfrequenz |
| `ODOM_PUBLISH_HZ` | 20 Hz | Odometrie-Publikationsrate |
| `FAILSAFE_TIMEOUT_MS` | 500 ms | Timeout bis Motorstopp |

PID-Gains (Kp=1.5, Ki=0.5, Kd=0.0) sind in `main.cpp` hardcoded.

## Hinweise

- **C++11**: Die ESP32-Arduino-Toolchain kompiliert mit C++11. Kein `std::clamp` verfuegbar.
- **Kein Reconnect**: Nach Agent-Verlust muss der ESP32 per Reset neu verbunden werden.
- **Reliable QoS**: Odometrie wird mit Reliable QoS publiziert, da `nav_msgs/Odometry` (~725 Bytes) die XRCE-DDS MTU von 512 Bytes ueberschreitet und Fragmentierung erfordert.

## Lizenz

MIT -- siehe [`../LICENSE`](../LICENSE).
