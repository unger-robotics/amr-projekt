# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kontext

ESP32-Firmware fuer einen autonomen mobilen Roboter (AMR) mit Differentialantrieb. Kommuniziert ueber micro-ROS/UART (Serial Transport, Humble) mit einem Raspberry Pi 5. Teil eines groesseren Projekts — uebergeordnete Projektdokumentation in `../../CLAUDE.md`.

## Build-Befehle

```bash
pio run                       # Kompilieren (Env: seeed_xiao_esp32s3)
pio run -t upload             # Flashen (921600 Baud, /dev/ttyACM0)
pio run -t monitor            # Serieller Monitor (115200 Baud)
pio run -t upload -t monitor  # Upload + Monitor kombiniert

# MOSFET-Diagnose ohne micro-ROS (schnellerer Build, 4 Phasen):
pio run -e led_test -t upload -t monitor
```

Erster Build dauert ~15 Min (micro-ROS-Libraries werden aus Source kompiliert und gecached). Die `led_test`-Umgebung kompiliert nur `led_ramp_test.cpp` (ohne micro-ROS, ~5s Build). `platformio.ini` verwendet `build_src_filter` um Doppel-Kompilierung zu vermeiden: Haupt-Env schliesst `led_ramp_test.cpp` aus, `led_test`-Env kompiliert nur diese Datei. Es gibt keine Unit-Tests — Validierung erfolgt experimentell ueber ROS2-Skripte auf dem Pi 5.

## Architektur

### Dual-Core Partitionierung

- **Core 0** (`loop()`): micro-ROS Executor — empfaengt `/cmd_vel`, `/servo_cmd`, `/hardware_cmd`; publiziert `/odom` (20 Hz), `/imu` (50 Hz), `/battery` (2 Hz); Watchdog; Deferred I2C (Servo-Rampe)
- **Core 1** (`controlTask`, FreeRTOS): 50 Hz PID-Regelschleife, Encoder-Auswertung, IMU-Read, Odometrie-Berechnung

### Thread-Safety

Zwei FreeRTOS-Mutexe:
- `mutex`: Schuetzt `SharedData` struct zwischen den Cores (Odometrie, IMU, Batterie, Sollwerte)
- `i2c_mutex` (5 ms Timeout): Schuetzt ALLE I2C-Bus-Zugriffe Cross-Core — Arduino Wire ist NICHT thread-safe

**Kritisch:** Kein I2C in Subscriber-Callbacks ausfuehren! Wire-Operationen schlagen STILL FEHL innerhalb von `rclc_executor_spin_some()`. Stattdessen Deferred-Pattern verwenden: Callback speichert Werte in volatile struct (RAM), `loop()` fuehrt I2C nach `spin_some()` aus.

### Module (`src/`)

| Datei | Verantwortung |
|---|---|
| `main.cpp` | FreeRTOS-Tasks, micro-ROS Setup, Publisher/Subscriber, Batterie-Shutdown, Motor-Limit |
| `robot_hal.hpp` | GPIO, Encoder-ISR (Quadratur A+B, `IRAM_ATTR`), PWM (Cytron MDD3A Dual-PWM), LED-MOSFET |
| `pid_controller.hpp` | PID mit Anti-Windup und D-Term-Tiefpass, Ausgang [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | Vorwaerts-/Inverskinematik, Odometrie-Integration |
| `mpu6050.hpp` | MPU6050 I2C-Treiber, Gyro-Bias-Kalibrierung, Komplementaerfilter |
| `ina260.hpp` | TI INA260 Leistungsmonitor (Spannung/Strom/Leistung), Unterspannungs-Alert |
| `pca9685.hpp` | NXP PCA9685 Servo-PWM, `setTargetAngle()` + `updateRamp()` (nicht-blockierend), `allOff()` Notaus |
| `led_ramp_test.cpp` | MOSFET-Diagnose (4 Phasen: digitalWrite, LEDC-Rampe, Stufen, Blinken), nur in `led_test`-Env |

### Konfiguration

Alle Parameter zentral in `../../hardware/config.h` (eingebunden via `-I../../hardware` Build-Flag). C++-Namespaces: `amr::pid::`, `amr::pwm::`, `amr::kinematics::`, `amr::timing::`, `amr::imu::`, `amr::battery::`, `amr::servo::`, `amr::i2c::`, `amr::ina260::`, `amr::safety::`, `amr::regulator::`. Compile-Time-Validierung via `static_assert` am Ende von `config.h`.

## Firmware-Constraints

- **C++17**: Kompiliert mit `-std=gnu++17` (GCC 8.4.0). `std::clamp` aus `<algorithm>` verfuegbar. `inline constexpr` fuer Header-Konstanten.
- **Typen**: `int32_t`/`uint8_t`/`int16_t` statt `int`/`long`. Encoder-Zaehler sind `volatile int32_t`
- **ISR**: Alle ISR-Funktionen mit `IRAM_ATTR` markieren
- **Speicher**: Keine dynamische Allokation zur Laufzeit (nur beim Startup)
- **micro-ROS QoS**: `rclc_publisher_init_default()` (Reliable) verwenden, da `nav_msgs/Odometry` (~725 Bytes) die XRCE-DDS MTU (512 Bytes) ueberschreitet — Best-Effort hat KEINE Fragmentierung

## Datenfluss

```
cmd_vel → Inverskinematik → Motor-Limit-Skalierung → Beschleunigungsrampe
  → PID (EMA-gefilterter Encoder-Input) → Deadzone/Dead-Band → Cytron MDD3A (Dual-PWM)
  → Encoder-Feedback (Quadratur, 2x-Zaehlung) → Vorwaertskinematik → Odometrie-Publish
```

Servo-Pfad (Deferred-I2C + Rampe):
```
servo_cmd (Point) → Callback speichert in ServoCommand struct (RAM)
  → loop() nach spin_some() → pca9685.setTargetAngle() (RAM)
  → pca9685.updateRamp() (I2C, in i2c_mutex, 1 Schritt pro Zyklus)
```

## I2C-Bus (400 kHz)

| Adresse | Device | Zugriff |
|---|---|---|
| 0x40 | INA260 (Leistungsmonitor) | Core 0, in `i2c_mutex` |
| 0x41 | PCA9685 (Servo-PWM) | Core 0, in `i2c_mutex` |
| 0x68 | MPU6050 (IMU) | Core 1, in `i2c_mutex` |

## LED-Statusanzeige (D10/GPIO9, IRLZ24N MOSFET, LEDC-Kanal 4, 5 kHz, 10-bit)

- Langsames Blinken = Agent-Suche
- Schnelles Blinken = Init-Fehler
- Gedimmt (64/1023) = Setup OK
- Heartbeat-Toggle = `loop()` laeuft
- Dauer-An (1023) = Publish-Fehler (nur bei `led_pwm=0`, Auto-Modus)
- Bei `led_pwm > 0`: Manueller Duty-Cycle via `/hardware_cmd`

**LEDC-API (ESP32 Arduino Core 2.x, kanalbasiert):** `ledcWrite()` erwartet den **LEDC-Kanal** als erstes Argument, NICHT den GPIO-Pin. Korrekt: `ledcWrite(amr::pwm::led_channel, duty)`. Der Kanal wird in `robot_hal.hpp` via `ledcSetup(LEDC_CH, freq, bits)` + `ledcAttachPin(pin, LEDC_CH)` konfiguriert. Motor-PWM in `robot_hal.hpp` verwendet dasselbe Pattern (`ledcWrite(PWM_CH_*, duty)`). Verifiziert mit 4-Phasen-Diagnose (`led_ramp_test.cpp`): digitalWrite, LEDC-Rampe, Helligkeitsstufen, Blinken.

## Pin-Mapping (XIAO ESP32-S3)

Die Arduino-Dx-Bezeichnungen weichen von den ESP32-GPIO-Nummern ab. Referenz: `variants/XIAO_ESP32S3/pins_arduino.h`.

| Board-Pin | GPIO | Funktion |
|---|---|---|
| D0 | 1 | Motor Links A |
| D1 | 2 | Motor Links B |
| D2 | 3 | Motor Rechts A |
| D3 | 4 | Motor Rechts B |
| D4 | 5 | I2C SDA |
| D5 | 6 | I2C SCL |
| D6 | 43 | Encoder Links Phase A (TX) |
| D7 | 44 | Encoder Rechts Phase A (RX) |
| D8 | 7 | Encoder Links Phase B |
| D9 | 8 | Encoder Rechts Phase B |
| D10 | 9 | LED-MOSFET (IRLZ24N Gate) |
