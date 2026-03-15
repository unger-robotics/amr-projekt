# Roboterparameter

## Zweck

Zentrale Ablage fachlich relevanter Parameter. Alle Werte stammen aus `config_drive.h` (v4.0.0) und `config_sensors.h` (v3.0.0).

## Kinematik (amr::kinematics)

| Parameter | Wert | Einheit | Quelle |
|---|---|---|---|
| Raddurchmesser | 65.67 | mm | kalibriert |
| Radradius | 32.835 | mm | berechnet |
| Spurbreite (Mitte-Mitte) | 178.0 | mm | config_drive.h |
| Ticks/Umdrehung links | 748.6 | — | kalibriert |
| Ticks/Umdrehung rechts | 747.2 | — | kalibriert |

Encoder: Hall-Encoder JGA25-370 (11 CPR, Uebersetzung 1:34).

## PID-Regelung (amr::pid)

| Parameter | Wert |
|---|---|
| Kp | 0.4 |
| Ki | 0.1 |
| Kd | 0.0 |
| Anti-Windup (i_min / i_max) | -1.0 / 1.0 |
| Ausgangsbereich (output_min / output_max) | -1.0 / 1.0 |
| D-Filter Tau | 0.02 s |
| EMA-Alpha (Encoder-Filter) | 0.3 |
| Beschleunigungsrampe | 5.0 rad/s² |
| Totzone-Schwelle | 0.08 |
| Hard-Stop-Schwelle | 0.01 |
| Stillstand-Schwelle | 0.01 |

## PWM-Konfiguration (amr::pwm)

| Parameter | Wert |
|---|---|
| Motor-Frequenz | 20 kHz |
| Motor-Aufloesung | 8 Bit (0-255) |
| Anlauf-Deadzone | 35 |
| LED-Frequenz | 5 kHz |
| LED-Aufloesung | 10 Bit (0-1023) |
| LED-Kanal (LEDC) | 4 |

## Timing (amr::timing)

### Drive-Knoten

| Parameter | Wert |
|---|---|
| Regelschleife | 50 Hz (20 ms) |
| Odometrie-Publish | 20 Hz (50 ms) |
| Failsafe-Timeout | 500 ms |
| Watchdog-Limit | 50 Zyklen |

### Sensor-Knoten

| Parameter | Wert |
|---|---|
| Ultraschall-Publish | 10 Hz (100 ms) |
| Cliff-Publish | 20 Hz (50 ms) |
| IMU-Abtastung | 50 Hz (20 ms) |
| Batterie-Publish | 2 Hz (500 ms) |
| US-Timeout | 20.000 µs (~3.4 m) |
| Watchdog-Limit | 50 Zyklen |

## I2C-Bus (amr::i2c, nur Sensor-Knoten)

| Geraet | Adresse | Funktion |
|---|---|---|
| INA260 | 0x40 | Leistungsmonitor (Batterie) |
| PCA9685 | 0x41 | Servo-PWM (Loetbruecke A0) |
| MPU6050 | 0x68 | IMU (AD0=GND) |

Bus-Frequenz: 400 kHz (Fast-mode). Alle I2C-Zugriffe ueber globalen `i2c_mutex` (5 ms Timeout) geschuetzt.

## IMU-Parameter (amr::imu)

| Parameter | Wert |
|---|---|
| Komplementaerfilter Alpha | 0.98 (Yaw-Fusion: 98 % Gyro-Integration, 2 % Encoder-Heading) |
| Gyro-Empfindlichkeit | 131.0 LSB/(°/s) |
| Beschleunigungs-Empfindlichkeit | 16384.0 LSB/g |
| Kalibrierproben | 500 |

## Batterie-Parameter (amr::battery)

Akkupack: Samsung INR18650-35E 3S1P (NCA, 10.80 V / 3.35 Ah).

| Parameter | Wert |
|---|---|
| Motor-Abschaltung | < 9.5 V |
| Hysterese | 0.3 V |
| Voll geladen | 12.60 V |
| Tiefentladeschutz (Cutoff) | 7.95 V |
| Nennkapazitaet | 3.35 Ah |

### INA260-Register (amr::ina260)

| Parameter | Wert |
|---|---|
| Config-Register | 0x6527 |
| Alert-Spannungsgrenze | 7600 mV |
| Strom-LSB | 1.25 mA |
| Spannungs-LSB | 1.25 mV |
| Leistungs-LSB | 10.0 mW |

## Servo-Parameter (amr::servo)

Ansteuerung ueber PCA9685 (I2C-PWM-Treiber).

| Parameter | Wert |
|---|---|
| Pan-Kanal | 0 |
| Tilt-Kanal | 1 |
| Winkelbereich (PWM-Hardware) | 0-180° |
| Pan-Schwenkbereich (kalibriert) | 45-135° (Offset +8°) |
| Tilt-Schwenkbereich (kalibriert) | 80-135° (Offset +1°) |
| PWM-Ticks (min/max) | 123 / 492 |
| PCA-Prescale | 121 |
| Rampe | 2.0 °/Schritt |

## CAN-Bus (amr::can)

Bitrate: 1 Mbit/s (ISO 11898), Transceiver: SN65HVD230, TX-Timeout: 10 ms (Drive-Knoten) / 3 ms (Sensor-Knoten).

Drive-Knoten CAN-IDs: 0x200-0x2FF. Sensor-Knoten CAN-IDs: 0x110-0x1FF. Heartbeat-Periode: 1000 ms (beide Knoten).

## Sensorik (amr::sensor)

| Parameter | Wert |
|---|---|
| Schallgeschwindigkeit | 343.2 m/s (20 °C) |
| US-Mindestreichweite | 0.02 m |
| US-Maximalreichweite | 4.00 m |

## Regel

Parameterlisten und Einheiten nur hier pflegen.
