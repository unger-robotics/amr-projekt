---
title: CAN-Signalkatalog
description: Aus der Signaldatenbank amr_vehicle.dbc erzeugte Uebersicht aller CAN-Nachrichten, Signale, Zykluszeiten und Sendeoffsets.
---

# CAN-Signalkatalog

!!! info "Erzeugte Datei"
    Diese Seite wird aus `hardware/can-bus/amr_vehicle.dbc` erzeugt
    (`./scripts/can_generate.sh`). Aenderungen erfolgen ausschliesslich in der
    Signaldatenbank, nicht in dieser Datei. Der Abgleich wird mit Testfall
    T-09 (`tests/test_can_dbc_check.py`, Schritt 5) geprueft.

Die Signaldatenbank ist die alleinige Quelle fuer Kennungen, Nutzdatenlaengen,
Bitlagen, Skalierungen und Zykluszeiten (SA-10). Byte-Order ist durchgehend
Intel (Little Endian); float32-Signale entsprechen dem `memcpy` der Firmware.

| Kennwert | Wert |
| --- | --- |
| Bitrate | 1000000 bit/s |
| Nachrichten | 28 |
| Knoten | PI_VCU, DRIVE_ECU, SENSOR_ECU, RADAR_ECU |
| Rechnerische Buslast | 3.94 Prozent (ohne Bitstopfen) |

## Uebersicht

| Kennung | Name | Sender | Empfaenger | DLC | Zyklus [ms] | Offset [ms] | Sendeart |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0x110 | SENSOR_RANGE | SENSOR_ECU | PI_VCU | 4 | 100 | 15 | cyclic |
| 0x120 | SENSOR_CLIFF | SENSOR_ECU | DRIVE_ECU, PI_VCU | 1 | 50 | 5 | cyclic |
| 0x130 | SENSOR_IMU_ACC | SENSOR_ECU | PI_VCU | 8 | 20 | 0 | cyclic |
| 0x131 | SENSOR_IMU_HEADING | SENSOR_ECU | PI_VCU | 4 | 20 | 10 | cyclic |
| 0x140 | SENSOR_BATTERY | SENSOR_ECU | PI_VCU | 6 | 500 | 25 | cyclic |
| 0x141 | SENSOR_BATTERY_SHUTDOWN | SENSOR_ECU | DRIVE_ECU, PI_VCU | 1 | 1000 | 45 | cyclicAndEvent |
| 0x150 | VCU_SERVO_COMMAND_LEGACY | PI_VCU | SENSOR_ECU | 4 | - | 0 | event |
| 0x160 | VCU_EMERGENCY_STOP | PI_VCU | DRIVE_ECU, SENSOR_ECU | 4 | 100 | 0 | cyclicAndEvent |
| 0x170 | VCU_HEARTBEAT | PI_VCU | DRIVE_ECU, SENSOR_ECU | 8 | 100 | 5 | cyclic |
| 0x1F0 | SENSOR_HEARTBEAT | SENSOR_ECU | PI_VCU | 8 | 1000 | 35 | cyclic |
| 0x200 | DRIVE_ODOM_XY | DRIVE_ECU | PI_VCU | 8 | 40 | 0 | cyclic |
| 0x201 | DRIVE_ODOM_HEADING_SPEED | DRIVE_ECU | PI_VCU | 8 | 40 | 0 | cyclic |
| 0x210 | DRIVE_WHEEL_SPEED | DRIVE_ECU | PI_VCU | 8 | 80 | 20 | cyclic |
| 0x220 | DRIVE_MOTOR_PWM | DRIVE_ECU | PI_VCU | 4 | 80 | 60 | cyclic |
| 0x230 | DRIVE_PATH_STATUS | DRIVE_ECU | PI_VCU | 8 | 200 | 40 | cyclic |
| 0x2F0 | DRIVE_HEARTBEAT | DRIVE_ECU | PI_VCU | 2 | 1000 | 60 | cyclic |
| 0x300 | RADAR_LIST_HEADER | RADAR_ECU | PI_VCU | 4 | 100 | 0 | cyclic |
| 0x301 | RADAR_OBJECT_1 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x302 | RADAR_OBJECT_2 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x303 | RADAR_OBJECT_3 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x304 | RADAR_OBJECT_4 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x305 | RADAR_OBJECT_5 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x306 | RADAR_OBJECT_6 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x307 | RADAR_OBJECT_7 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x308 | RADAR_OBJECT_8 | RADAR_ECU | PI_VCU | 8 | 100 | 0 | cyclic |
| 0x3F0 | RADAR_HEARTBEAT | RADAR_ECU | PI_VCU | 8 | 1000 | 50 | cyclic |
| 0x400 | VCU_DRIVE_COMMAND | PI_VCU | DRIVE_ECU | 8 | 20 | 0 | cyclic |
| 0x410 | VCU_SENSOR_COMMAND | PI_VCU | SENSOR_ECU | 8 | 100 | 5 | cyclic |

## Sendeplan je Steuergeraet

Die Offsets gelten innerhalb eines Senders; die Takte der Steuergeraete sind
nicht synchronisiert. Zykluszeiten sind ganzzahlige Vielfache des Sendertakts
(Fahrkern 20 ms, Sensorbasis 10 ms).

### PI_VCU

| Kennung | Name | Zyklus [ms] | Offset [ms] | Rate [Hz] |
| --- | --- | --- | --- | --- |
| 0x150 | VCU_SERVO_COMMAND_LEGACY | - | 0 | 10.0 |
| 0x160 | VCU_EMERGENCY_STOP | 100 | 0 | 10.0 |
| 0x170 | VCU_HEARTBEAT | 100 | 5 | 10.0 |
| 0x400 | VCU_DRIVE_COMMAND | 20 | 0 | 50.0 |
| 0x410 | VCU_SENSOR_COMMAND | 100 | 5 | 10.0 |

### DRIVE_ECU (Takt 20 ms)

| Kennung | Name | Zyklus [ms] | Offset [ms] | Rate [Hz] |
| --- | --- | --- | --- | --- |
| 0x200 | DRIVE_ODOM_XY | 40 | 0 | 25.0 |
| 0x201 | DRIVE_ODOM_HEADING_SPEED | 40 | 0 | 25.0 |
| 0x210 | DRIVE_WHEEL_SPEED | 80 | 20 | 12.5 |
| 0x220 | DRIVE_MOTOR_PWM | 80 | 60 | 12.5 |
| 0x230 | DRIVE_PATH_STATUS | 200 | 40 | 5.0 |
| 0x2F0 | DRIVE_HEARTBEAT | 1000 | 60 | 1.0 |

### SENSOR_ECU (Takt 10 ms)

| Kennung | Name | Zyklus [ms] | Offset [ms] | Rate [Hz] |
| --- | --- | --- | --- | --- |
| 0x110 | SENSOR_RANGE | 100 | 15 | 10.0 |
| 0x120 | SENSOR_CLIFF | 50 | 5 | 20.0 |
| 0x130 | SENSOR_IMU_ACC | 20 | 0 | 50.0 |
| 0x131 | SENSOR_IMU_HEADING | 20 | 10 | 50.0 |
| 0x140 | SENSOR_BATTERY | 500 | 25 | 2.0 |
| 0x141 | SENSOR_BATTERY_SHUTDOWN | 1000 | 45 | 1.0 |
| 0x1F0 | SENSOR_HEARTBEAT | 1000 | 35 | 1.0 |

### RADAR_ECU

| Kennung | Name | Zyklus [ms] | Offset [ms] | Rate [Hz] |
| --- | --- | --- | --- | --- |
| 0x300 | RADAR_LIST_HEADER | 100 | 0 | 10.0 |
| 0x301 | RADAR_OBJECT_1 | 100 | 0 | 10.0 |
| 0x302 | RADAR_OBJECT_2 | 100 | 0 | 10.0 |
| 0x303 | RADAR_OBJECT_3 | 100 | 0 | 10.0 |
| 0x304 | RADAR_OBJECT_4 | 100 | 0 | 10.0 |
| 0x305 | RADAR_OBJECT_5 | 100 | 0 | 10.0 |
| 0x306 | RADAR_OBJECT_6 | 100 | 0 | 10.0 |
| 0x307 | RADAR_OBJECT_7 | 100 | 0 | 10.0 |
| 0x308 | RADAR_OBJECT_8 | 100 | 0 | 10.0 |
| 0x3F0 | RADAR_HEARTBEAT | 1000 | 50 | 1.0 |

## Nachrichten im Einzelnen

### 0x110 SENSOR_RANGE

S-03 Abstand voraus. Sendebedingung: jede erfolgreiche Ultraschallmessung im 100-ms-Raster.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| range_front | 0 | 32 | float32 | 1 | 0 | 0 bis 4 | m |

### 0x120 SENSOR_CLIFF

S-01 Kantenerkennung. Wird zusaetzlich vom Fahrkern empfangen (Sicherheitspfad ohne Zentralrechner, id_cliff_rx).

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cliff_detected | 0 | 8 | uint8 | 1 | 0 | 0 bis 1 | - |

Wertetabelle `cliff_detected`: 0 NO_CLIFF, 1 CLIFF

### 0x130 SENSOR_IMU_ACC

S-04 Beschleunigung und Gierrate. Skalierung nach Firmware: Beschleunigung Faktor 0,001, Gierrate Faktor 0,01.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accel_x | 0 | 16 | int16 | 0.001 | 0 | -32.768 bis 32.767 | m/s^2 |
| accel_y | 16 | 16 | int16 | 0.001 | 0 | -32.768 bis 32.767 | m/s^2 |
| accel_z | 32 | 16 | int16 | 0.001 | 0 | -32.768 bis 32.767 | m/s^2 |
| gyro_z | 48 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | rad/s |

### 0x131 SENSOR_IMU_HEADING

S-05 Gierwinkel aus dem Komplementaerfilter der Sensorbasis.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| heading | 0 | 32 | float32 | 1 | 0 | -3.2 bis 3.2 | rad |

### 0x140 SENSOR_BATTERY

S-06 Batteriespannung, Strom und Leistung. Die Leistung saettigt bei 65,535 W, der Betriebspunkt liegt bei rund 60 W; die Erweiterung des Wertebereichs erfordert eine Layoutaenderung und ist fuer K3 vorgemerkt.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| battery_voltage | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | V |
| battery_current | 16 | 16 | int16 | 0.001 | 0 | -32.768 bis 32.767 | A |
| battery_power | 32 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | W |

Hinweis `battery_power`: Saettigt bei 65,535 W (S-06).

### 0x141 SENSOR_BATTERY_SHUTDOWN

S-02 Batterie-Abschaltanforderung. Wird zusaetzlich vom Fahrkern empfangen (id_battery_shutdown_rx). K1 fordert zusaetzlich zur Ereignismeldung eine zyklische Wiederholung mit 1 Hz; die Firmware sendet heute nur ereignisgesteuert, die Umsetzung erfolgt in K3.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| battery_shutdown | 0 | 8 | uint8 | 1 | 0 | 0 bis 1 | - |

Wertetabelle `battery_shutdown`: 0 OK, 1 SHUTDOWN

### 0x150 VCU_SERVO_COMMAND_LEGACY

P-07 Servosollwert im Ist-Zustand. Bestehendes Kommando des Zentralrechners an die Sensorbasis, ohne E2E-Absicherung. Bleibt unveraendert bestehen, damit aeltere Firmware betriebsfaehig bleibt; die Ablloesung durch VCU_SENSOR_COMMAND erfolgt in K5.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| servo_pan_legacy | 0 | 16 | int16 | 0.1 | 0 | -180 bis 180 | deg |
| servo_tilt_legacy | 16 | 16 | int16 | 0.1 | 0 | -180 bis 180 | deg |

### 0x160 VCU_EMERGENCY_STOP

P-05 Notstopp-Anforderung an beide Steuergeraete. Kennung unterhalb der Diagnosebereiche, damit die Anforderung die Arbitrierung gegen Diagnoseverkehr gewinnt; Kantenerkennung und Batterieabschaltung bleiben hoeher priorisiert.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| estop_request | 0 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| estop_source | 1 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| estop_counter | 8 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| estop_alive_counter | 16 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| estop_crc8 | 24 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

Wertetabelle `estop_source`: 0 NONE, 1 DASHBOARD, 2 VOICE, 3 SAFETY_NODE, 4 NAVIGATION, 5 WATCHDOG

Hinweis `estop_counter`: Fortlaufender Zaehler nach P-05; macht ein verlorenes Ereignis erkennbar.

Hinweis `estop_crc8`: CRC-8 nach SAE J1850 ueber Byte 0 bis 2 zuzueglich der Data-ID 0x60.

### 0x170 VCU_HEARTBEAT

P-06 Lebenszeichen des Gateways. Erlaubt den Steuergeraeten, den Ausfall des Zentralrechners zu erkennen, ohne auf das Ausbleiben von Fahrbefehlen zu warten.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vcu_hb_counter | 0 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| vcu_state | 8 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| vcu_uptime | 16 | 32 | uint32 | 1 | 0 | 0 bis 4294967295 | s |
| vcu_hb_alive_counter | 48 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| vcu_hb_crc8 | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

Wertetabelle `vcu_state`: 0 SERIAL_REFERENCE, 1 CAN_SHADOW, 2 CAN_PRIMARY, 3 SERVICE, 4 FAILSAFE

Hinweis `vcu_hb_crc8`: CRC-8 nach SAE J1850 ueber Byte 0 bis 6 zuzueglich der Data-ID 0x70.

### 0x1F0 SENSOR_HEARTBEAT

S-07 Lebenszeichen der Sensorbasis mit Fehlerzaehlern.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sensor_imu_ok | 0 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| sensor_ina260_ok | 1 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| sensor_pca9685_ok | 2 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| sensor_bat_shutdown_flag | 3 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| sensor_core1_ok | 4 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| sensor_uptime_mod256 | 8 | 8 | uint8 | 1 | 0 | 0 bis 255 | s |
| sensor_i2c_err | 16 | 16 | uint16 | 1 | 0 | 0 bis 65535 | - |
| sensor_servo_err | 32 | 16 | uint16 | 1 | 0 | 0 bis 65535 | - |
| sensor_servo_ok | 48 | 16 | uint16 | 1 | 0 | 0 bis 65535 | - |

### 0x200 DRIVE_ODOM_XY

D-01 Odometrie-Position.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| odom_x | 0 | 32 | float32 | 1 | 0 | -100 bis 100 | m |
| odom_y | 32 | 32 | float32 | 1 | 0 | -100 bis 100 | m |

### 0x201 DRIVE_ODOM_HEADING_SPEED

D-02 Odometrie-Gierwinkel und Laengsgeschwindigkeit. Wird im selben Sendertakt wie DRIVE_ODOM_XY uebertragen, damit die Werte zusammengehoeren.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| odom_theta | 0 | 32 | float32 | 1 | 0 | -3.2 bis 3.2 | rad |
| odom_v_linear | 32 | 32 | float32 | 1 | 0 | -1 bis 1 | m/s |

### 0x210 DRIVE_WHEEL_SPEED

D-03 Raddrehzahl links und rechts.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wheel_speed_left | 0 | 32 | float32 | 1 | 0 | -50 bis 50 | rad/s |
| wheel_speed_right | 32 | 32 | float32 | 1 | 0 | -50 bis 50 | rad/s |

### 0x220 DRIVE_MOTOR_PWM

D-04 Stellgroesse links und rechts, ganzzahlig im Bereich -255 bis 255.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| motor_pwm_left | 0 | 16 | int16 | 1 | 0 | -255 bis 255 | - |
| motor_pwm_right | 16 | 16 | int16 | 1 | 0 | -255 bis 255 | - |

### 0x230 DRIVE_PATH_STATUS

D-05 Status des aktiven Fahrbefehlspfads. Macht die Arbitrierung von aussen beobachtbar und ist Nachweisgrundlage fuer das Failover.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| path_active_source | 0 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| path_operating_mode | 4 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| path_age_serial | 8 | 16 | uint16 | 1 | 0 | 0 bis 65535 | ms |
| path_age_can | 24 | 16 | uint16 | 1 | 0 | 0 bis 65535 | ms |
| path_cliff_armed | 40 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| path_cliff_timeout | 41 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| path_estop_latched | 42 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| path_vcu_hb_timeout | 43 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| path_alive_counter | 48 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| path_crc8 | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

Wertetabelle `path_active_source`: 0 NONE, 1 SERIAL_REFERENCE, 2 CAN

Wertetabelle `path_operating_mode`: 0 SERIAL_REFERENCE, 1 CAN_SHADOW, 2 CAN_PRIMARY, 3 SERVICE, 4 FAILSAFE

Hinweis `path_crc8`: CRC-8 nach SAE J1850 ueber Byte 0 bis 6 zuzueglich der Data-ID 0x30.

### 0x2F0 DRIVE_HEARTBEAT

D-06 Lebenszeichen des Fahrkerns. Die Bits drive_encoder_ok, drive_motor_ok und drive_core1_ok sind in der heutigen Firmware fest auf 1 gesetzt und fuehren noch keinen echten Zustand; die Behebung ist Bestandteil von K3.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| drive_encoder_ok | 0 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| drive_motor_ok | 1 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| drive_pid_active | 2 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| drive_bat_shutdown | 3 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| drive_core1_ok | 4 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| drive_failsafe_active | 5 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| drive_uptime_mod256 | 8 | 8 | uint8 | 1 | 0 | 0 bis 255 | s |

### 0x300 RADAR_LIST_HEADER

Radar-Platzhalter: Kopf der Objektliste. Layout in Spike S-B zu bestaetigen.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_frame_counter | 0 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_object_count | 8 | 8 | uint8 | 1 | 0 | 0 bis 8 | - |
| radar_status | 16 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x301 RADAR_OBJECT_1

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_1_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_1_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_1_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_1_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_1_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x302 RADAR_OBJECT_2

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_2_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_2_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_2_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_2_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_2_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x303 RADAR_OBJECT_3

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_3_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_3_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_3_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_3_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_3_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x304 RADAR_OBJECT_4

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_4_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_4_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_4_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_4_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_4_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x305 RADAR_OBJECT_5

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_5_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_5_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_5_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_5_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_5_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x306 RADAR_OBJECT_6

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_6_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_6_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_6_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_6_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_6_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x307 RADAR_OBJECT_7

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_7_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_7_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_7_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_7_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_7_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x308 RADAR_OBJECT_8

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_8_range | 0 | 16 | uint16 | 0.001 | 0 | 0 bis 65.535 | m |
| radar_8_angle | 16 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | deg |
| radar_8_v_radial | 32 | 16 | int16 | 0.01 | 0 | -327.68 bis 327.67 | m/s |
| radar_8_amplitude | 48 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_8_object_id | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

### 0x3F0 RADAR_HEARTBEAT

Radar-Platzhalter: Lebenszeichen. Layout in Spike S-B zu bestaetigen.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radar_hb_flags | 0 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| radar_hb_uptime_mod256 | 8 | 8 | uint8 | 1 | 0 | 0 bis 255 | s |
| radar_hb_sensor_err | 16 | 16 | uint16 | 1 | 0 | 0 bis 65535 | - |
| radar_hb_spi_err | 32 | 16 | uint16 | 1 | 0 | 0 bis 65535 | - |

### 0x400 VCU_DRIVE_COMMAND

P-01, P-02, P-03 und P-04 in einem Rahmen. Bleibt ohne gueltiges Kommando die Zeitueberwachung von 300 ms im Modus CAN_PRIMARY unerfuellt, geht der Fahrkern in FAILSAFE mit v gleich null und omega gleich null; ein selbsttaetiger Quellenwechsel findet nicht statt. Im Modus CAN_SHADOW werden E2E-Fehler nur gezaehlt. Die Begrenzungen nach NFA-05, NFA-06 und NFA-07 wirken im Steuergeraet, nicht im Wertebereich dieses Signals.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| target_velocity | 0 | 16 | int16 | 0.001 | 0 | -32.768 bis 32.767 | m/s |
| target_yaw_rate | 16 | 16 | int16 | 0.001 | 0 | -32.768 bis 32.767 | rad/s |
| drive_cmd_enable | 32 | 1 | uint1 | 1 | 0 | 0 bis 1 | - |
| operating_mode | 33 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| motor_limit_percent | 37 | 7 | uint7 | 1 | 0 | 0 bis 100 | % |
| drive_cmd_alive_counter | 52 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| drive_cmd_crc8 | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

Wertetabelle `operating_mode`: 0 SERIAL_REFERENCE, 1 CAN_SHADOW, 2 CAN_PRIMARY, 3 SERVICE, 4 FAILSAFE

Hinweis `motor_limit_percent`: P-04 Begrenzung der Stellgroesse in Prozent; ersetzt den heutigen Weg ueber hardware_cmd.

Hinweis `drive_cmd_crc8`: CRC-8 nach SAE J1850 ueber Byte 0 bis 6 zuzueglich der Data-ID 0x00 (unteres Byte der Kennung 0x400).

### 0x410 VCU_SENSOR_COMMAND

P-07 Servosollwert mit E2E-Absicherung. Nachfolger von VCU_SERVO_COMMAND_LEGACY; die Umstellung erfolgt in K5, bis dahin ist diese Nachricht spezifiziert und ohne Wirkung.

| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| servo_pan | 0 | 16 | uint16 | 0.1 | 0 | 0 bis 180 | deg |
| servo_tilt | 16 | 16 | uint16 | 0.1 | 0 | 0 bis 180 | deg |
| servo_speed | 32 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |
| sensor_cmd_alive_counter | 52 | 4 | uint4 | 1 | 0 | 0 bis 15 | - |
| sensor_cmd_crc8 | 56 | 8 | uint8 | 1 | 0 | 0 bis 255 | - |

Hinweis `sensor_cmd_crc8`: CRC-8 nach SAE J1850 ueber Byte 0 bis 6 zuzueglich der Data-ID 0x10 (unteres Byte der Kennung 0x410).

## Herkunft der Festlegungen

Wortlaut des datenbankweiten Kommentars in `amr_vehicle.dbc`:

```text
Signaldatenbank des AMR (Ausbaupaket K2, Phasenplan v2.1).
Alleinige Quelle fuer Kennungen, Nutzdatenlaengen, Bitlagen, Skalierungen und
Zykluszeiten (SA-10). Firmware-Konstanten und die Pi-seitige Dekodierung werden
hieraus abgeleitet, nicht parallel gepflegt.

Byte-Order durchgehend Intel (Little Endian). Die float32-Signale sind ueber
SIG_VALTYPE_ als IEEE-754-Gleitkomma gekennzeichnet und entsprechen dem memcpy
der Firmware.

AUS K1 UEBERNOMMEN
- Betriebsmodi SERIAL_REFERENCE, CAN_SHADOW, CAN_PRIMARY, SERVICE, FAILSAFE
  (anforderungsliste-L1.md, Abschnitt 13.1)
- Zeitueberwachung des CAN-Kommandopfads 300 ms im Modus CAN_PRIMARY
  (anforderungsliste-L1.md, Abschnitt 13.3); SIA-17 mit 500 ms bleibt uebergeordnet
- Pflichtumfang der Signale P-01 bis P-07, D-01 bis D-06, S-01 bis S-07
  (signalbedarf.md); jede Nachricht dieser Datenbank ist einer Zeile zugeordnet
- Ablageort hardware/can-bus/ (signalbedarf.md, Einleitung)
- Sicherheitsrelevante Signale erhalten hoehere Buspriorisierung als
  Diagnosesignale (signalbedarf.md, Abschnitt 7.4)
- Bestehende Kennungen bleiben unveraendert, neue Signale belegen freie Bereiche
  (signalbedarf.md, Abschnitt 7.3)

AUS DER FIRMWARE UEBERNOMMEN (Ist-Zustand, unveraendert)
- Die dreizehn Bestandskennungen 0x110 bis 0x2F0 mit Bitlagen, Skalierungen und
  Nutzdatenlaengen nach twai_can.hpp beider Knoten
  (arbeitsplan-k0-k2-s-a.md, Anhang A.3)

IN K2 VORGESCHLAGEN (nicht aus K1 uebernommen)
- Kennungen 0x160 Notstopp, 0x170 Gateway-Lebenszeichen, 0x230 Pfadstatus,
  0x400 Fahrbefehl, 0x410 Servokommando
- Zahlenwerte des Betriebsmodus-Enums (0 bis 4) und des Notstopp-Quellen-Enums
- Bitlagen, Skalierungen und Nutzdatenlaengen der fuenf neuen Nachrichten
- E2E-Absicherung: alive_counter mit 4 Bit und CRC-8 nach SAE J1850
  (Polynom 0x1D, Startwert 0xFF, Endverknuepfung 0xFF) ueber Byte 0 bis 6
  zuzueglich der Data-ID
- Zykluszeiten 0x200 und 0x201 mit 40 ms sowie 0x210 und 0x220 mit 80 ms
  (Tick-Regel: ganzzahlige Vielfache des Sendertakts von 20 ms; Begruendung
  Messung S-A vorher, arbeitsplan-k0-k2-s-a.md, Abschnitte 3.2 und 3.4)
- Sendeoffsets je Sender (GenMsgStartDelayTime)
- Radar-Reservierung 0x300 bis 0x3F0; Layout in Spike S-B zu bestaetigen

WIRKSAMKEIT
Die fuenf neuen Nachrichten und die geaenderten Zykluszeiten sind in K2
ausschliesslich spezifiziert. Die Firmware sendet weiterhin nach dem Ist-Zustand;
die Umsetzung erfolgt fuer die Sensorbasis in K3 und fuer den Fahrkern in K4.
```
