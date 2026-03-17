# ESP32 AMR Drive-Node

Echtzeit-Firmware fuer den Differentialantrieb eines autonomen mobilen Roboters (AMR). Empfaengt `/cmd_vel` und publiziert Odometrie ueber micro-ROS/UART an einen Raspberry Pi 5. Kein I2C — alle Sensoren und Aktoren liegen auf dem Sensor-Node.

## Hardware-Voraussetzungen

| Komponente | Typ | Anschluss |
|---|---|---|
| Mikrocontroller | Seeed Studio XIAO ESP32-S3 | USB-CDC (micro-ROS) |
| Motortreiber | Cytron MDD3A (Dual-PWM-Modus) | GPIO 1-4 (D0-D3) |
| Motoren | JGA25-370 DC-Getriebemotoren (1:34) | Quadratur-Encoder Phase A+B |
| Encoder | Hall-Encoder 11 CPR (2x-Zaehlung, ~748 Ticks/Umdrehung) | GPIO 5-8 (D4-D9) |
| LED-Streifen | SMD 5050 via IRLZ24N Low-Side MOSFET | GPIO 9 (D10), LEDC-Kanal 4 |
| CAN-Transceiver | SN65HVD230 (3.3 V) | GPIO 43 TX / GPIO 44 RX |

Pin-Belegung, Encoder-Kalibrierung und alle weiteren Parameter sind in `include/config_drive.h` definiert.

## Build & Flash

[PlatformIO](https://platformio.org/) ist erforderlich. **Wichtig:** Immer `-e <environment>` angeben — ohne `-e` flasht PlatformIO ALLE Environments, das letzte ueberschreibt die vorherigen.

```bash
pio run -e drive_node                       # Kompilieren
pio run -e drive_node -t upload -t monitor  # Upload + Monitor (921600 Baud, /dev/amr_drive)
pio run -e led_test -t upload -t monitor    # LED/MOSFET-Diagnose (ohne micro-ROS, ~5 s)
```

Der erste Build laedt und kompiliert die micro-ROS-Libraries (~15 Min). Folgebuilds sind gecached.

## Architektur

Die Firmware nutzt beide ESP32-Kerne fuer deterministische Regelung:

```
Core 0 (loop)                           Core 1 (controlTask, 50 Hz)
  micro-ROS Executor                      Encoder-Auswertung (Quadratur A+B)
  /cmd_vel Subscriber               -->   EMA-Filter (alpha=0.3)
  /hardware_cmd Subscriber                Failsafe + Batterie-Check
  /battery_shutdown Subscriber            Inverskinematik
  Odometrie Publisher (20 Hz)        <--  Beschleunigungsrampe (5 rad/s^2)
  LED-Heartbeat / Manual Override         PID-Regelung (Kp=0.4, Ki=0.1)
  Inter-Core Watchdog                     Vorwaertskinematik + Odometrie
  CAN-RX (Cliff/Battery vom             CAN-TX (Odom, Encoder, PWM, Heartbeat)
    Sensor-Node, Notstopp)
                     \                /
                      SharedData (Mutex, 10 ms Timeout)
```

**Datenfluss-Pipeline (Core 1, 50 Hz):**

`cmd_vel` --> Inverskinematik --> Motor-Limit (0-100%) --> Hard-Stop-Gate --> Beschleunigungsrampe --> PID (EMA-gefiltert) --> Cytron MDD3A (PWM, Deadzone 35) --> Encoder-Feedback --> Vorwaertskinematik --> Odometrie

### Module (Header-only, `include/`)

| Datei | Namespace | Aufgabe |
|---|---|---|
| `config_drive.h` | `amr::*` | Zentrale Konfiguration: HAL-Pins, Kinematik, PID, PWM, Timing, CAN |
| `robot_hal.hpp` | `amr::hardware` | GPIO-Init, Encoder-ISR (Quadratur A+B, IRAM_ATTR), PWM-Ansteuerung, Deadzone-Kompensation, LED-PWM (LEDC 10-bit) |
| `pid_controller.hpp` | `amr::control` | PID-Regler mit Anti-Windup, D-Term Low-Pass-Filter (tau=0.02 s), Ausgangsbereich [-1.0, 1.0] |
| `diff_drive_kinematics.hpp` | `amr::kinematics` | Vorwaerts-/Inverskinematik, Odometrie-Integration, Heading-Normierung [-pi, pi] |
| `twai_can.hpp` | `amr::drivers` | TWAI CAN-Bus: Odom/Encoder/PWM-Sends + Cliff/Battery-Empfang (Notstopp-Redundanzpfad) |

### Safety-Mechanismen

| Mechanismus | Beschreibung |
|---|---|
| **Failsafe-Timeout** | Motoren stoppen nach 500 ms ohne `/cmd_vel` |
| **Batterie-Shutdown** | `/battery_shutdown` Topic (Sensor-Node) setzt Motor-Sperre |
| **CAN-Notstopp** | Cliff (0x120) und Battery-Shutdown (0x141) via CAN als Hardware-Redundanzpfad |
| **Inter-Core Watchdog** | Core 0 ueberwacht `core1_heartbeat`, Notfall-Stopp bei 50 Misses (1 s) |
| **Beschleunigungsrampe** | Max. 5.0 rad/s^2, Hard-Stop-Bypass bei Ziel Null |
| **Motor-Limit** | 0-100% Skalierung via `/hardware_cmd` (x-Feld) |
| **PID-Stillstand** | PID-Reset bei Sollwert < 0.01 rad/s (verhindert Integral-Drift) |

### LED-Status

Zwei LEDs: Externe LED (D10, MOSFET-geschaltet, LEDC 10-bit) und interne Onboard-LED (GPIO 21, Active Low).

| Zustand | Externe LED | Interne LED | Bedeutung |
|---|---|---|---|
| Agent-Suche | Aus | Langsames Blinken (100/900 ms) | Firmware wartet auf micro-ROS Agent |
| Init-Fehler | Aus | Schnelles Blinken (200/200 ms) | micro-ROS Init fehlgeschlagen |
| Boot-Test | Ramp 0%-->100%-->0% | — | LEDC + MOSFET Verifikation (~3 s) |
| Normal (auto) | Aus | Heartbeat-Toggle (~400 ms) | `loop()` laeuft |
| Manuell | Duty 0-255 | Aus | `/hardware_cmd` z=LED-PWM |
| Publish-Fehler | — | Dauer-An | `rcl_publish` Rueckgabefehler |
| Watchdog-Alarm | — | — | Core 1 Heartbeat verloren, Motoren gestoppt |

**Hinweis:** Die ESP32 Arduino Core 2.x LEDC-API ist kanalbasiert — `ledcWrite(channel, duty)`, nicht `ledcWrite(pin, duty)`. LED-PWM verwendet LEDC-Kanal `amr::pwm::led_channel` (Kanal 4, 5 kHz, 10-bit).

## ROS2-Topics

| Topic | Typ | Richtung | Rate | Beschreibung |
|---|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | Publish | 20 Hz | Pose (x, y, theta) + Twist (v, omega), Reliable QoS |
| `/cmd_vel` | `geometry_msgs/Twist` | Subscribe | — | Soll-Geschwindigkeit (linear.x, angular.z) |
| `/hardware_cmd` | `geometry_msgs/Point` | Subscribe | — | x=Motor-Limit (0-100%), z=LED-PWM (0-255) |
| `/battery_shutdown` | `std_msgs/Bool` | Subscribe | — | Unterspannungs-Notaus vom Sensor-Node |

**Reliable QoS** fuer `/odom`: `nav_msgs/Odometry` (~725 Bytes) ueberschreitet die XRCE-DDS MTU (512 Bytes) und erfordert Fragmentierung, die nur mit Reliable QoS (`rclc_publisher_init_default()`) funktioniert.

## Konfiguration (`include/config_drive.h`)

Alle Hardware-Parameter sind zentral in `include/config_drive.h` definiert (Single Source of Truth). Namespaces mit `inline constexpr` und `static_assert` Compile-Time-Validierung.

### Kinematik (kalibrierte Werte)

| Parameter | Namespace | Wert | Beschreibung |
|---|---|---|---|
| `wheel_diameter` | `amr::kinematics` | 65.67 mm | Raddurchmesser |
| `wheel_base` | `amr::kinematics` | 178 mm | Spurbreite Mitte-Mitte |
| `ticks_per_rev_left` | `amr::kinematics` | 748.6 | Encoder-Ticks/Umdrehung links |
| `ticks_per_rev_right` | `amr::kinematics` | 747.2 | Encoder-Ticks/Umdrehung rechts |

### Regelung

| Parameter | Namespace | Wert | Beschreibung |
|---|---|---|---|
| `kp` / `ki` / `kd` | `amr::pid` | 0.4 / 0.1 / 0.0 | PID-Gains |
| `ema_alpha` | `amr::pid` | 0.3 | Encoder-Geschwindigkeitsfilter |
| `max_accel_rad_s2` | `amr::pid` | 5.0 | Beschleunigungsrampe |
| `deadzone` | `amr::pwm` | 35 | PWM-Anlaufschwelle (von 255) |
| `motor_freq_hz` | `amr::pwm` | 20 kHz | Motor-PWM-Frequenz |
| `control_loop_hz` | `amr::timing` | 50 Hz | PID-Regelfrequenz |
| `odom_publish_hz` | `amr::timing` | 20 Hz | Odometrie-Publikationsrate |
| `failsafe_timeout_ms` | `amr::timing` | 500 ms | Timeout bis Motorstopp |

### Signalverarbeitung

- **EMA-Filter** (alpha=0.3) auf Encoder-Geschwindigkeit fuer PID-Eingang
- **Deadzone** (0.08) in `driveMotor()` unterdrueckt PID-Rauschen nahe Null
- **Stillstand-Bypass** mit PID-Reset wenn beide Sollwerte < 0.01

## CAN-Bus (TWAI, parallel zu micro-ROS)

Antriebs-Daten werden zusaetzlich via CAN 2.0B (1 Mbit/s, SN65HVD230) gesendet. CAN-Init-Fehler sind nicht fatal — die Firmware laeuft ohne Transceiver weiter. Alle CAN-Sends laufen auf Core 1 (`controlTask`), damit sie unabhaengig vom micro-ROS-Verbindungsstatus arbeiten.

### Senden (Drive-Node --> Pi 5, 0x200-0x2FF)

| CAN-ID | Laenge | Inhalt | Rate |
|---|---|---|---|
| `0x200` | 8 B | Odom Position: x, y [2x float32 LE, m] | 20 Hz |
| `0x201` | 8 B | Odom Heading+Speed: theta, v [2x float32 LE] | 20 Hz |
| `0x210` | 8 B | Encoder: left, right [2x float32 LE, rad/s] | 10 Hz |
| `0x220` | 4 B | Motor-PWM: left, right [2x int16 LE, -255..+255] | 10 Hz |
| `0x2F0` | 2 B | Heartbeat: Flags [uint8] + Uptime [uint8 s%256] | 1 Hz |

### Empfangen (Sensor-Node --> Drive-Node, Notstopp-Redundanzpfad)

| CAN-ID | Laenge | Inhalt | Aktion |
|---|---|---|---|
| `0x120` | 1 B | Cliff-Status (0x01=Cliff) | `can_cliff_stop` --> Motoren stoppen |
| `0x141` | 1 B | Battery-Shutdown (0x01=Shutdown) | `can_battery_stop` --> Motoren stoppen |

## Diagnose-Environment: `led_test`

Minimales Testprogramm (`src/led_ramp_test.cpp`) ohne micro-ROS fuer MOSFET-Diagnose:

1. `digitalWrite` Test (An/Aus)
2. LEDC Ramp (0-->1023)
3. Feste Duty-Stufen (25%, 50%, 75%, 100%)
4. Blink-Test

Baut in ~30 s (ohne micro-ROS). Diagnostiziert Floating Gate, Kurzschluesse und fehlende Versorgung.

## Hinweise

- **C++17**: Kompiliert mit `-std=gnu++17` (GCC 8.4.0). `std::clamp` und `inline constexpr` verfuegbar.
- **Kein Reconnect**: Nach Agent-Verlust muss der ESP32 per Reset neu verbunden werden.
- **USB-CDC**: `-DARDUINO_USB_CDC_ON_BOOT=1` — Serial ist USB, nicht UART0.
- **ISR**: Encoder-Interrupts mit `IRAM_ATTR` im globalen Scope, `portMUX` fuer atomare Zaehler-Reads.
- **Kein I2C**: Alle I2C-Geraete (IMU, Batterie, Servo) liegen auf dem Sensor-Node.

## Lizenz

MIT -- siehe [`../LICENSE`](../LICENSE).
