# Messprotokoll CAN-Bus-Validierung

Datum: 31.03.2026
Pruefer: ---
Testareal: Innenraum, Roboter stationaer
Akkuspannung: 12,34 V (94,6 %)
Firmware: Drive-Node v4.0.0, Sensor-Node v3.0.0
Hardware: 2x SN65HVD230 Transceiver, MCP2515 SPI-CAN-Controller (Pi 5)
Interface: SocketCAN can0, 1 Mbit/s, CAN 2.0B (11-Bit Standard-Frames)
Software: can_validation_test.py (python-can, standalone ohne ROS2)

---

## Testbedingungen

| Parameter | Wert |
|---|---|
| CAN-Bitrate | 1.000.000 bit/s |
| CAN-Controller Pi 5 | MCP2515 (SPI, dtoverlay) |
| CAN-Transceiver | 2x SN65HVD230 (3,3 V, Slope Mode) |
| Terminierung | 2x 120 Ohm (Bus-Enden) |
| Buslaenge | ca. 25 cm (Intra-Chassis) |
| CAN-State vor Test | ERROR-ACTIVE (Normalzustand) |
| Power-Cycle vor Test | Ja (Transceiver-Latch-up nach Error-Frames zurueckgesetzt) |

---

## Testfall CAN-1: Frame-Raten und Vollstaendigkeit

| Parameter | Wert |
|---|---|
| Skript | `can_validation_test.py --duration 30` |
| Aufnahmedauer | 30 s |
| Frames gesamt | 5604 |
| Durchschnittliche Busrate | 186,8 Frames/s |
| Empfangene CAN-IDs | 11 von 12 (0x141 BatShutdown nur bei Ereignis) |
| Fehlende IDs (periodisch) | keine |
| Error-Frames | 0 |

### Frame-Raten pro CAN-ID

| CAN-ID | Name | DLC | Soll (Hz) | Ist (Hz) | Count | Status |
|---|---|---|---|---|---|---|
| 0x130 | Sensor/IMU_Accel | 8 | 50 | 50,0 | 1501 | PASS |
| 0x131 | Sensor/IMU_Heading | 4 | 50 | 50,0 | 1500 | PASS |
| 0x120 | Sensor/Cliff | 1 | 20 | 20,0 | 600 | PASS |
| 0x200 | Drive/OdomPos | 8 | 20 | 16,1 | 483 | PASS |
| 0x201 | Drive/OdomHeading | 8 | 20 | 16,7 | 500 | PASS |
| 0x110 | Sensor/Range | 4 | 10 | 10,0 | 300 | PASS |
| 0x210 | Drive/Encoder | 8 | 10 | 10,0 | 300 | PASS |
| 0x220 | Drive/MotorPWM | 4 | 10 | 10,0 | 300 | PASS |
| 0x140 | Sensor/Battery | 6 | 2 | 2,0 | 60 | PASS |
| 0x1F0 | Sensor/Heartbeat | 2 | 1 | 1,0 | 30 | PASS |
| 0x2F0 | Drive/Heartbeat | 2 | 1 | 1,0 | 30 | PASS |
| 0x141 | Sensor/BatShutdown | 1 | 0 (Event) | 0,0 | 0 | OK |

Akzeptanzkriterium: Ist-Rate innerhalb +/- 25 % der Soll-Rate.

Bemerkung: OdomPos (16,1 Hz) und OdomHeading (16,7 Hz) liegen unter der Soll-Rate von 20 Hz, aber innerhalb der 25-%-Toleranz. Ursache: Die Drive-Node sendet Odom-CAN-Frames nach dem PID-Zyklus auf Core 1; micro-ROS-Overhead auf Core 0 beeinflusst das Timing leicht.

---

## Testfall CAN-2: Heartbeat-Dekodierung

### Drive-Node Heartbeat (0x2F0)

| Flag | Wert | Bedeutung |
|---|---|---|
| encoder_ok | true | Encoder-Hardware erkannt |
| motor_ok | true | Motortreiber aktiv |
| pid_active | false | Kein cmd_vel empfangen (Roboter steht) |
| bat_shutdown | false | Kein Batterie-Shutdown |
| core1_ok | true | FreeRTOS-Task auf Core 1 laeuft |
| failsafe | true | Failsafe aktiv (kein cmd_vel seit > 500 ms) |
| uptime_mod256 | 39 | Uptime-Zaehler (mod 256 s) |

### Sensor-Node Heartbeat (0x1F0)

| Flag | Wert | Bedeutung |
|---|---|---|
| imu_ok | true | MPU6050 I2C-Kommunikation ok |
| ina260_ok | true | INA260 Batteriemessung ok |
| pca9685_ok | true | PCA9685 Servo-Controller ok |
| bat_shutdown | false | Kein Batterie-Shutdown |
| core1_ok | true | FreeRTOS-Task auf Core 1 laeuft |
| uptime_mod256 | 38 | Uptime-Zaehler (mod 256 s) |

**Ergebnis:** Beide Nodes melden alle Peripherie-Subsysteme als funktionsfaehig.

---

## Testfall CAN-3: Datendekodierung (Stichproben)

| CAN-ID | Name | Dekodierte Werte | Plausibel |
|---|---|---|---|
| 0x110 | Sensor/Range | range_m = 1,204 | Ja (Wand in ca. 1,2 m) |
| 0x120 | Sensor/Cliff | cliff = false | Ja (ebener Boden) |
| 0x130 | Sensor/IMU_Accel | ax = 153 mg, ay = -198 mg, az = 9131 mg, gz = 0 | Ja (az nahe 1 g) |
| 0x131 | Sensor/IMU_Heading | heading_rad = 0,0004 | Ja (stationaer, nahe 0) |
| 0x140 | Sensor/Battery | 12.340 mV, 860 mA, 10.620 mW | Ja (3S LiPo, Leerlauf) |
| 0x200 | Drive/OdomPos | x = 0,0 m, y = 0,0 m | Ja (stationaer) |
| 0x201 | Drive/OdomHeading | theta = 0,0 rad, v = 0,0 m/s | Ja (stationaer) |
| 0x210 | Drive/Encoder | left = 0,0 rad/s, right = 0,0 rad/s | Ja (Motoren aus) |
| 0x220 | Drive/MotorPWM | left = 0, right = 0 | Ja (kein PWM-Signal) |

---

## Testfall CAN-4: Node-Vollstaendigkeit

| Node | Erwartete IDs | Empfangene IDs | Status |
|---|---|---|---|
| Drive-Node (0x200..0x2FF) | 5 | 5/5 | OK |
| Sensor-Node (0x110..0x1FF) | 7 | 6/7 | OK |

Sensor-Node 6/7: Die fehlende ID 0x141 (BatShutdown) wird nur als Event bei Unterspannung gesendet (kein periodischer Frame). Das ist korrektes Verhalten.

---

## Testfall CAN-5: CAN-Bridge ROS2-Integration

| Parameter | Wert |
|---|---|
| Launch-Parameter | `use_can:=True` |
| ROS2-Node | can_bridge_node |
| CAN-Frames nach 100 s | 18.699 |
| Sensor-Heartbeats | 100 (= 1 Hz x 100 s) |
| Drive-Heartbeats | 100 (= 1 Hz x 100 s) |
| CPU-Last can_bridge_node | ~8 % (select-basiert) |
| **Ergebnis** | **PASS** |

---

## CAN-Protokoll-Referenz

### Adressraum

| Bereich | Node | Definiert in |
|---|---|---|
| 0x110..0x1FF | Sensor-Node | `config_sensors.h` (`amr::can::`) |
| 0x200..0x2FF | Drive-Node | `config_drive.h` (`amr::can::`) |

### Dual-Path-Redundanz

| Prioritaet | Pfad | Bedingung |
|---|---|---|
| 1 | micro-ROS/UART (921600 Baud) | Normalzustand |
| 2 | CAN-Bus (1 Mbit/s) | UART-Timeout > 500 ms |
| 3 | Firmware-Stopp (tv=0, tw=0) | Beide Pfade ausgefallen, Pi 5 nicht erforderlich |

### Encoding

Alle Nutzdaten Little-Endian. Ganzzahlen als int16/uint16, Gleitkomma als float32 (IEEE 754).

---

## Bewertung

| Testfall | Beschreibung | Ergebnis |
|---|---|---|
| CAN-1 | Frame-Raten und Vollstaendigkeit | PASS |
| CAN-2 | Heartbeat-Dekodierung | PASS |
| CAN-3 | Datendekodierung (Plausibilitaet) | PASS |
| CAN-4 | Node-Vollstaendigkeit | PASS |
| CAN-5 | CAN-Bridge ROS2-Integration | PASS |

**Gesamtergebnis: PASS**

---

JSON-Ergebnisdatei: `messprotokoll_can_validation.json`
