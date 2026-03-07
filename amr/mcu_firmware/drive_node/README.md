# ESP32 AMR Firmware

Echtzeit-Firmware fuer den Differentialantrieb eines autonomen mobilen Roboters (AMR). Empfaengt `cmd_vel` und publiziert Odometrie ueber micro-ROS/UART an einen Raspberry Pi 5.

## Hardware-Voraussetzungen

| Komponente | Typ |
|---|---|
| Mikrocontroller | Seeed Studio XIAO ESP32-S3 |
| Motortreiber | Cytron MDD3A (Dual-PWM-Modus) |
| Motoren | JGA25-370 DC-Getriebemotoren mit Quadratur-Encoder (Phase A+B, 2x-Zaehlung) |
| CAN-Transceiver | SN65HVD230 (3.3 V, GPIO43 TX / GPIO44 RX) |
| Verbindung zum Pi 5 | USB-CDC (micro-ROS) + CAN-Bus (TWAI, 500 kbit/s) |

Pin-Belegung, Encoder-Kalibrierung und alle weiteren Parameter sind in `include/config_drive.h` definiert.

## Build & Flash

[PlatformIO](https://platformio.org/) ist erforderlich. Umgebung: `seeed_xiao_esp32s3`.

```bash
pio run                       # Kompilieren
pio run -t upload             # Flashen (921600 Baud, /dev/amr_drive)
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

**Datenfluss:** `cmd_vel` --> Inverskinematik --> Beschleunigungsrampe --> PID (EMA-Filter) --> Cytron MDD3A (PWM, Dead-Band) --> Encoder-Feedback --> Vorwaertskinematik --> Odometrie-Publish

### Module (Header-only, `include/`)

| Datei | Aufgabe |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Subscriber/Publisher, Failsafe, Watchdog |
| `robot_hal.hpp` | GPIO-Init, Encoder-ISR (Quadratur A+B), PWM-Ansteuerung, Deadzone-Kompensation, LED-PWM |
| `pid_controller.hpp` | PID-Regler mit Anti-Windup, Ausgangsbereich [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik, Odometrie-Integration |
| `mpu6050.hpp` | MPU6050 I2C-Treiber (±2g Accel, ±250°/s Gyro), Bias-Kalibrierung, Complementary-Filter |
| `ina260.hpp` | TI INA260 I2C-Leistungsmonitor: Spannung, Strom, Leistung, Unterspannungs-Alert |
| `pca9685.hpp` | NXP PCA9685 I2C-Servo-PWM: `setTargetAngle()`, nicht-blockierende Rampe, `allOff()` Notaus |
| `twai_can.hpp` | TWAI CAN-Bus Treiber, Dual-Path Antriebs-Daten |

### Safety-Mechanismen

- **Failsafe**: Motoren stoppen nach 500 ms ohne `cmd_vel`
- **Inter-Core Watchdog**: Core 0 ueberwacht Heartbeat von Core 1, Notfall-Stopp bei Ausfall
- **Beschleunigungsrampe**: max. 5.0 rad/s^2 begrenzt Stromspitzen
- **Agent-Warten**: Firmware blockiert in `setup()` bis micro-ROS Agent erreichbar ist

### LED-Status (D10 ueber IRLZ24N MOSFET, LEDC-Kanal 4)

- **Langsames Blinken**: Agent-Suche (Firmware wartet auf micro-ROS Agent)
- **Schnelles Blinken**: Init-Fehler
- **Gedimmt**: Setup erfolgreich abgeschlossen
- **Heartbeat-Toggle**: `loop()` laeuft normal
- **Dauer-An**: Publish-Fehler
- **Manuell**: Duty-Cycle 0-255 via `/hardware_cmd` Topic (z=LED-PWM)

**Hinweis:** Die ESP32 Arduino Core 2.x LEDC-API ist kanalbasiert — `ledcWrite(channel, duty)`, nicht `ledcWrite(pin, duty)`. LED-PWM verwendet LEDC-Kanal `amr::pwm::led_channel` (Kanal 4, 5 kHz, 10-bit).

## Konfiguration (`include/config_drive.h`)

Alle Hardware-Parameter sind zentral in `include/config_drive.h` definiert (Single Source of Truth, eingebunden via `-I include` Build-Flag):

| Parameter | Wert | Beschreibung |
|---|---|---|
| `WHEEL_DIAMETER` | 65.67 mm | Raddurchmesser (kalibriert) |
| `WHEEL_BASE` | 178 mm | Spurbreite |
| `TICKS_PER_REV_LEFT/RIGHT` | ~748 | Encoder-Ticks pro Umdrehung (2x Quadratur, kalibriert) |
| `PWM_DEADZONE` | 35 | PWM-Schwelle unter der Motoren nicht anlaufen |
| `CONTROL_LOOP_HZ` | 50 Hz | PID-Regelfrequenz |
| `ODOM_PUBLISH_HZ` | 20 Hz | Odometrie-Publikationsrate |
| `FAILSAFE_TIMEOUT_MS` | 500 ms | Timeout bis Motorstopp |
| `IMU_PUBLISH_HZ` | 50 Hz | IMU-Publikationsrate |
| `IMU_COMPLEMENTARY_ALPHA` | 0.02 | Complementary-Filter Gewichtung (Accelerometer-Anteil) |

PID-Gains (Kp=0.4, Ki=0.1, Kd=0.0) sind in `config_drive.h` definiert (`amr::pid::kp/ki/kd`).

### Signalverarbeitung

- **EMA-Filter** (alpha=0.3) auf Encoder-Geschwindigkeit fuer PID-Eingang
- **Dead-Band** (0.08) in `driveMotor()` unterdrueckt PID-Rauschen nahe Null
- **Stillstand-Bypass** mit PID-Reset wenn beide Sollwerte < 0.01

## Hinweise

- **C++17**: Kompiliert mit `-std=gnu++17` (GCC 8.4.0). `std::clamp` und `inline constexpr` verfuegbar.
- **Kein Reconnect**: Nach Agent-Verlust muss der ESP32 per Reset neu verbunden werden.
- **Reliable QoS**: Odometrie wird mit Reliable QoS publiziert, da `nav_msgs/Odometry` (~725 Bytes) die XRCE-DDS MTU von 512 Bytes ueberschreitet und Fragmentierung erfordert.

### CAN-Bus (TWAI, parallel zu micro-ROS)

Antriebs-Daten werden zusaetzlich via CAN 2.0B (500 kbit/s) gesendet. CAN-Init-Fehler sind nicht fatal — die Firmware laeuft ohne Transceiver weiter.

| CAN-ID | Laenge | Inhalt | Rate |
|---|---|---|---|
| `0x200` | 8 B | Odom Position: x, y [2x float32 LE, m] | 20 Hz |
| `0x201` | 8 B | Odom Heading+Speed: theta, v [2x float32 LE] | 20 Hz |
| `0x210` | 8 B | Encoder: left, right [2x float32 LE, rad/s] | 10 Hz |
| `0x220` | 4 B | Motor-PWM: left, right [2x int16 LE, -255..+255] | 10 Hz |
| `0x2F0` | 2 B | Heartbeat: Flags [uint8] + Uptime [uint8 s%256] | 1 Hz |

## Lizenz

MIT -- siehe [`../LICENSE`](../LICENSE).
