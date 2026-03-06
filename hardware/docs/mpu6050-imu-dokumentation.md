# IMU-Sensor MPU6050 – 6-Achsen Beschleunigungsmesser und Gyroskop

> **Technische Dokumentation** – Inertialmesseinheit (Inertial Measurement Unit, IMU) für autonome mobile Robotik (AMR)  
> Sensor: InvenSense MPU-6050 (3-Achsen-Gyroskop + 3-Achsen-Beschleunigungsmesser, DMP, I²C)  
> Breakout-Board: GY-521 (integrierter Spannungsregler, Pull-Up-Widerstände)  
> Steuerung: Seeed XIAO ESP32-S3 via I²C, micro-ROS `sensor_msgs/Imu`  
> Quellen: [MPU-6050 Product Specification (PDF)](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf), [MPU-6050 Register Map (PDF)](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf), [I2Cdevlib MPU6050](https://www.i2cdevlib.com/docs/html/class_m_p_u6050.html)

---

## 1 Systemübersicht

### 1.1 Funktion im AMR-System

Die IMU liefert Drehrate (Gyroskop) und Translationsbeschleunigung (Beschleunigungsmesser, Accelerometer) in drei Raumachsen. In Kombination mit der Rad-Odometrie (Encoder) ermöglicht der Sensor eine robustere Lageerkennung: Das Gyroskop korrigiert Schlupf-Fehler der Encoder, während die Encoder den Gyroskop-Drift kompensieren. Diese Sensorfusion (Extended Kalman Filter, EKF) erfolgt typischerweise auf dem Raspberry Pi 5 im ROS-2-Node `robot_localization`.

```
┌─────────────────────────────────────────────────────┐
│  Raspberry Pi 5 – ROS 2 Humble (Docker)             │
│                                                     │
│  ┌─────────────────┐     ┌────────────────────┐    │
│  │ robot_localization│◄───│ micro-ROS Agent     │    │
│  │ (EKF)            │    │ (Serial / UDP)      │    │
│  │                  │    └─────────┬──────────┘    │
│  │  /odom (Encoder) │             │                │
│  │  /imu  (MPU6050) │             │                │
│  └─────────────────┘             │                │
└───────────────────────────────────┼────────────────┘
                                    │ USB-Serial / WiFi
                                    │
┌───────────────────────────────────┼────────────────┐
│  Seeed XIAO ESP32-S3 (micro-ROS Client)            │
│                                                     │
│  ┌──────────┐    I²C (400 kHz)   ┌──────────┐     │
│  │ Encoder  │    SDA ◄──────────►│ MPU6050  │     │
│  │ Auswertung│    SCL ◄──────────►│ (GY-521) │     │
│  │ + PID    │                    │          │     │
│  └──────────┘                    │ INT ─────┼──► GPIO │
│                                  └──────────┘     │
│  Publisher:                                        │
│    /imu             → sensor_msgs/Imu              │
│    /mcu/wheel_odom  → std_msgs/Float32MultiArray   │
└────────────────────────────────────────────────────┘
```

### 1.2 Achsendefinition und Orientierung

Der MPU6050 definiert sein Koordinatensystem im Gehäuse wie folgt (Blick von oben auf die Bauteilseite des GY-521-Boards):

```
        +Y (Pitch)
         ▲
         │
         │    Bauteilseite (Chip oben)
         │    ┌───────────────┐
         │    │   ●           │
         │    │  MPU6050      │
         │    │               │
         └────┤               ├────► +X (Roll)
              │               │
              │   GY-521      │
              └───────┬───────┘
                      │
                      ▼ +Z (Yaw, zeigt nach unten!)

Gyroskop: Rechte-Hand-Regel um die jeweilige Achse
Beschleunigung im Ruhezustand: az ≈ +1 g (bei Chip oben)
```

> **ROS-2-Konvention (REP 103):** Das ROS-Koordinatensystem verwendet x = vorwärts, y = links, z = oben. Die Orientierung des MPU6050 auf dem Roboter und die Achsentransformation in der Firmware müssen aufeinander abgestimmt werden. Abschnitt 6.3 beschreibt die Transformationsmatrix.

---

## 2 MPU6050 – Technische Daten

### 2.1 Allgemeine Spezifikationen

| Parameter | Wert | Einheit |
|---|---|---|
| **Hersteller** | InvenSense (TDK) | – |
| **Bezeichnung** | MPU-6050 | – |
| **Sensortyp** | MEMS 3-Achsen-Gyroskop + 3-Achsen-Beschleunigungsmesser |
| **Digitaler Bewegungsprozessor (DMP)** | Integriert (9-Achsen-Sensorfusion mit ext. Magnetometer) |
| **ADC-Auflösung** | 16 Bit (pro Achse, Zweierkomplement) |
| **Gehäuse** | QFN, 4 × 4 × 0,9 mm |
| **Schockfestigkeit** | 10.000 g |
| **Betriebstemperatur** | −40 … +85 °C |

### 2.2 Elektrische Daten

| Parameter | Min | Typ | Max | Einheit |
|---|---|---|---|---|
| **Versorgungsspannung (VDD)** | 2,375 | 3,3 | 3,46 | V |
| **Logikpegel (VLOGIC)** | 1,71 | – | VDD | V |
| **Stromaufnahme (Gyro + Accel aktiv)** | – | 3,9 | – | mA |
| **Stromaufnahme (nur Accel, Low Power, 1,25 Hz)** | – | 10 | – | µA |
| **Stromaufnahme (Sleep)** | – | 5 | – | µA |
| **I²C-Taktfrequenz** | – | 400 | 400 | kHz |
| **I²C-Adresse (AD0 = LOW)** | – | `0x68` | – | – |
| **I²C-Adresse (AD0 = HIGH)** | – | `0x69` | – | – |

### 2.3 Gyroskop

| Parameter | Wert | Einheit |
|---|---|---|
| **Messachsen** | 3 (X, Y, Z) |
| **Wählbare Messbereiche** | ±250, ±500, ±1000, ±2000 | °/s |
| **ADC-Auflösung** | 16 Bit | – |
| **Nullpunkt-Drift (Zero-Rate Output, ZRO)** | ±20 | °/s |
| **Nullpunkt-Drift über Temperatur** | ±20 | °/s (von −40 bis +85 °C) |
| **Rausch-Bandbreite (Noise Spectral Density)** | 0,005 | °/s/√Hz |
| **Nichtlinearität** | 0,2 | % FS |
| **Kreuzachsen-Empfindlichkeit** | ±2 | % |

**Empfindlichkeitstabelle (Sensitivity Scale Factor):**

| Messbereich (FS_SEL) | Register-Wert | Empfindlichkeit | Einheit |
|---|---|---|---|
| ±250 °/s | `0` | 131,0 | LSB/(°/s) |
| ±500 °/s | `1` | 65,5 | LSB/(°/s) |
| ±1000 °/s | `2` | 32,8 | LSB/(°/s) |
| **±2000 °/s** | **`3`** | **16,4** | **LSB/(°/s)** |

> **Empfehlung für AMR:** Der Messbereich **±500 °/s** bietet einen guten Kompromiss: Die maximale Drehrate eines typischen Differentialantriebs liegt bei ~180 °/s; ±500 °/s bietet ausreichend Headroom bei gleichzeitig guter Auflösung (65,5 LSB/(°/s)).

### 2.4 Beschleunigungsmesser (Accelerometer)

| Parameter | Wert | Einheit |
|---|---|---|
| **Messachsen** | 3 (X, Y, Z) |
| **Wählbare Messbereiche** | ±2, ±4, ±8, ±16 | g |
| **ADC-Auflösung** | 16 Bit | – |
| **Nullpunkt-Fehler (Zero-g Output)** | ±80 | mg |
| **Rausch-Bandbreite (Noise Spectral Density)** | 400 | µg/√Hz |
| **Nichtlinearität** | 0,5 | % FS |
| **Kreuzachsen-Empfindlichkeit** | ±2 | % |

**Empfindlichkeitstabelle:**

| Messbereich (AFS_SEL) | Register-Wert | Empfindlichkeit | Einheit |
|---|---|---|---|
| **±2 g** | **`0`** | **16.384** | **LSB/g** |
| ±4 g | `1` | 8.192 | LSB/g |
| ±8 g | `2` | 4.096 | LSB/g |
| ±16 g | `3` | 2.048 | LSB/g |

> **Empfehlung für AMR:** Für die Neigungserkennung und Komplementärfilter-Berechnung reicht **±2 g** (höchste Auflösung). Nur bei Fahrzeugen mit starker Beschleunigung oder Vibration empfiehlt sich ±4 g oder ±8 g.

### 2.5 Integrierter Temperatursensor

| Parameter | Wert | Einheit |
|---|---|---|
| **Messbereich** | −40 … +85 | °C |
| **Empfindlichkeit** | 340 | LSB/°C |
| **Offset bei 35 °C** | −521 | LSB |
| **Genauigkeit** | ±1 | °C (typisch) |

**Umrechnungsformel:**

$$T\,[°\text{C}] = \frac{\text{TEMP\_OUT}}{340{,}0} + 36{,}53$$

Der Temperatursensor dient primär zur internen Drift-Kompensation des Gyroskops, kann aber auch für die Überwachung der Boardtemperatur genutzt werden.

### 2.6 Digitaler Tiefpassfilter (DLPF)

Das Register `CONFIG` (0x1A) steuert den integrierten DLPF (Digital Low-Pass Filter), der sowohl Gyroskop als auch Beschleunigungsmesser beeinflusst.

| DLPF_CFG | Accel-Bandbreite | Gyro-Bandbreite | Abtastrate Gyro | Verzögerung (Accel) |
|---|---|---|---|---|
| `0` | 260 Hz | 256 Hz | 8 kHz | 0 ms |
| `1` | 184 Hz | 188 Hz | 1 kHz | 2,0 ms |
| `2` | 94 Hz | 98 Hz | 1 kHz | 3,0 ms |
| **`3`** | **44 Hz** | **42 Hz** | **1 kHz** | **4,9 ms** |
| `4` | 21 Hz | 20 Hz | 1 kHz | 8,5 ms |
| `5` | 10 Hz | 10 Hz | 1 kHz | 13,8 ms |
| `6` | 5 Hz | 5 Hz | 1 kHz | 19,0 ms |

> **Empfehlung für AMR:** DLPF_CFG = `3` (Bandbreite ~42 Hz) unterdrückt Motor- und Fahrbahnvibrationen effektiv, ohne die Dynamik der Roboterbewegung (< 10 Hz) zu beeinträchtigen. Die Abtastrate ergibt sich dann aus: $f_\text{sample} = \frac{1000}{1 + \text{SMPLRT\_DIV}}\,\text{Hz}$. Für 50 Hz: `SMPLRT_DIV` = 19.

---

## 3 GY-521 Breakout-Board

### 3.1 Schaltung und Pinbelegung

Das GY-521-Board integriert einen 3,3-V-Spannungsregler (LDO) und I²C-Pull-Up-Widerstände (4,7 kΩ auf SDA/SCL). Dadurch kann das Board direkt an 3,3 V oder 5 V versorgt werden.

```
GY-521 Breakout-Board – Pinbelegung:

    ┌───────────────────────────────────┐
    │            GY-521                 │
    │   ┌─────────────────────┐        │
    │   │      MPU-6050       │        │
    │   │   (4 × 4 × 0,9 mm) │        │
    │   └─────────────────────┘        │
    │                                   │
    │  VCC  GND  SCL  SDA  XDA  XCL  AD0  INT │
    └───┬───┬───┬───┬───┬───┬───┬───┬──┘
        │   │   │   │   │   │   │   │
        │   │   │   │   │   │   │   └─ Interrupt (Active High,
        │   │   │   │   │   │   │       Open-Drain oder Push-Pull)
        │   │   │   │   │   │   │
        │   │   │   │   │   │   └──── I²C-Adresswahl:
        │   │   │   │   │   │         LOW/offen = 0x68
        │   │   │   │   │   │         HIGH = 0x69
        │   │   │   │   │   │
        │   │   │   │   │   └──────── Hilfs-I²C Clock
        │   │   │   │   │             (für ext. Magnetometer)
        │   │   │   │   │
        │   │   │   │   └──────────── Hilfs-I²C Data
        │   │   │   │                 (für ext. Magnetometer)
        │   │   │   │
        │   │   │   └──────────────── I²C Daten (SDA)
        │   │   │
        │   │   └──────────────────── I²C Takt (SCL)
        │   │
        │   └──────────────────────── Masse (GND)
        │
        └──────────────────────────── Versorgung:
                                      3,3 V oder 5 V
                                      (Board hat LDO-Regler)
```

### 3.2 Board-Spezifikationen

| Parameter | Wert |
|---|---|
| **Eingangs-Spannung (VCC)** | 3,3 … 5,0 V (LDO reguliert auf 3,3 V) |
| **Logikpegel (SCL, SDA)** | 3,3 V (direkt ESP32-S3-kompatibel) |
| **I²C-Pull-Up-Widerstände** | 4,7 kΩ (auf dem Board, nach 3,3 V) |
| **Boardabmessungen** | ~20 × 16 mm |
| **Befestigungsbohrung** | 1× ∅ 3 mm |

> **3,3-V-Betrieb am ESP32-S3:** Bei Versorgung des GY-521 über den 3,3-V-Pin des XIAO ESP32-S3 liegen die I²C-Pegel direkt bei 3,3 V. Kein Pegelwandler erforderlich. Die Board-internen Pull-Ups (4,7 kΩ) sind für 400 kHz I²C bei kurzen Leitungslängen (< 30 cm) ausreichend.

---

## 4 Register-Referenz

### 4.1 Initialisierungsregister

| Register | Adresse | R/W | Beschreibung | Startwert |
|---|---|---|---|---|
| `PWR_MGMT_1` | `0x6B` | R/W | Energieverwaltung, Taktquelle, Sleep | `0x40` (Sleep) |
| `PWR_MGMT_2` | `0x6C` | R/W | Standby einzelner Achsen | `0x00` |
| `CONFIG` | `0x1A` | R/W | DLPF-Konfiguration, FSYNC | `0x00` |
| `GYRO_CONFIG` | `0x1B` | R/W | Gyroskop-Messbereich (FS_SEL) | `0x00` (±250 °/s) |
| `ACCEL_CONFIG` | `0x1C` | R/W | Accel-Messbereich (AFS_SEL) | `0x00` (±2 g) |
| `SMPLRT_DIV` | `0x19` | R/W | Abtastteiler: $f = 1000/(1+\text{Wert})$ | `0x00` (1 kHz) |
| `INT_PIN_CFG` | `0x37` | R/W | Interrupt-Pin-Konfiguration | `0x00` |
| `INT_ENABLE` | `0x38` | R/W | Interrupt-Freigabe | `0x00` |
| `WHO_AM_I` | `0x75` | R | Geräte-ID (Antwort: `0x68`) | `0x68` |

### 4.2 Sensordaten-Register (Burst-Read ab 0x3B)

Ein einzelner I²C-Burst-Read ab Register `0x3B` liefert 14 Byte (Beschleunigung + Temperatur + Gyroskop):

| Register | Adresse | Daten |
|---|---|---|
| `ACCEL_XOUT_H` | `0x3B` | Beschleunigung X, High-Byte |
| `ACCEL_XOUT_L` | `0x3C` | Beschleunigung X, Low-Byte |
| `ACCEL_YOUT_H` | `0x3D` | Beschleunigung Y, High-Byte |
| `ACCEL_YOUT_L` | `0x3E` | Beschleunigung Y, Low-Byte |
| `ACCEL_ZOUT_H` | `0x3F` | Beschleunigung Z, High-Byte |
| `ACCEL_ZOUT_L` | `0x40` | Beschleunigung Z, Low-Byte |
| `TEMP_OUT_H` | `0x41` | Temperatur, High-Byte |
| `TEMP_OUT_L` | `0x42` | Temperatur, Low-Byte |
| `GYRO_XOUT_H` | `0x43` | Drehrate X, High-Byte |
| `GYRO_XOUT_L` | `0x44` | Drehrate X, Low-Byte |
| `GYRO_YOUT_H` | `0x45` | Drehrate Y, High-Byte |
| `GYRO_YOUT_L` | `0x46` | Drehrate Y, Low-Byte |
| `GYRO_ZOUT_H` | `0x47` | Drehrate Z, High-Byte |
| `GYRO_ZOUT_L` | `0x48` | Drehrate Z, Low-Byte |

Alle Sensorwerte sind 16-Bit-Zweierkomplement-Werte (Wertebereich: −32.768 … +32.767).

### 4.3 Umrechnungsformeln

**Beschleunigung → SI-Einheit (m/s²):**

$$a\,[\text{m/s}^2] = \frac{\text{RAW\_ACCEL}}{\text{ACCEL\_SENSITIVITY}} \times 9{,}80665$$

**Drehrate → SI-Einheit (rad/s):**

$$\omega\,[\text{rad/s}] = \frac{\text{RAW\_GYRO}}{\text{GYRO\_SENSITIVITY}} \times \frac{\pi}{180}$$

**Beispielrechnung (±2 g, ±500 °/s):** Ein Rohwert `ACCEL_Z = 16384` entspricht $16384 / 16384 \times 9{,}807 = 9{,}807\,\text{m/s}^2$ (= 1 g, Erdbeschleunigung). Ein Rohwert `GYRO_Z = 655` entspricht $655 / 65{,}5 \times \pi/180 = 0{,}1745\,\text{rad/s}$ (= 10 °/s).

### 4.4 PWR_MGMT_1 – Taktquellenwahl

| Bit 2:0 (CLKSEL) | Taktquelle | Empfehlung |
|---|---|---|
| `0` | Interner 8-MHz-Oszillator | Nicht empfohlen (ungenauer) |
| **`1`** | **PLL mit X-Achsen-Gyroskop-Referenz** | **Empfohlen** |
| `2` | PLL mit Y-Achsen-Gyroskop-Referenz | Alternativ |
| `3` | PLL mit Z-Achsen-Gyroskop-Referenz | Alternativ |

Die Gyroskop-PLL liefert eine stabilere Taktfrequenz als der interne RC-Oszillator und verbessert die Genauigkeit der Drehratenmessung.

---

## 5 Verkabelung

### 5.1 Anschluss an XIAO ESP32-S3

| GY-521-Pin | Verbindung | XIAO-Pin | ESP32-S3 GPIO | Bemerkung |
|---|---|---|---|---|
| VCC | 3,3 V | 3V3 | – | Board-interner LDO |
| GND | Masse | GND | – | Gemeinsame Masse |
| SCL | I²C-Takt | D5 | GPIO6 | Wire.begin(SDA, SCL) |
| SDA | I²C-Daten | D4 | GPIO5 | Standard-I²C-Pins |
| INT | Interrupt | D3 | GPIO4 | Optional (Data-Ready) |
| AD0 | Adresswahl | GND oder offen | – | LOW → 0x68 |
| XCL | Hilfs-I²C | – | – | Nicht verbunden |
| XDA | Hilfs-I²C | – | – | Nicht verbunden |

> **Pin-Koordination mit Motorsteuerung:** Falls die Standard-I²C-Pins (D4/D5) bereits für die Encoder-Auswertung der JGA25-370-Motoren belegt sind (vgl. Motor-Treiber-Dokumentation), können alternative Pins per Software-I²C zugewiesen werden. Der ESP32-S3 unterstützt die Neuzuordnung der I²C-Peripherie auf beliebige GPIOs: `Wire.begin(SDA_PIN, SCL_PIN)`. Mögliche Alternativen: D8 (GPIO7) für SDA und D9 (GPIO8) für SCL.

### 5.2 Anschlussdiagramm

```
XIAO ESP32-S3                        GY-521 (MPU6050)
┌──────────────┐                     ┌──────────────┐
│              │                     │              │
│     3V3 ─────┼─────────────────────┼── VCC        │
│              │                     │              │
│     GND ─────┼─────────────────────┼── GND        │
│              │                     │              │
│  D5 (GPIO6) ─┼──────── 4,7 kΩ ────┼── SCL        │
│              │         (auf Board) │              │
│  D4 (GPIO5) ─┼──────── 4,7 kΩ ────┼── SDA        │
│              │         (auf Board) │              │
│  D3 (GPIO4) ─┼─────────────────────┼── INT        │
│              │                     │              │
│              │              GND ───┼── AD0        │
│              │                     │              │
└──────────────┘                     └──────────────┘

I²C-Bus (400 kHz):
  ┌─────────────────────────────────────┐
  │                                     │
  │  3,3 V                              │
  │   │        │                        │
  │  4,7 kΩ  4,7 kΩ  (auf GY-521)     │
  │   │        │                        │
  │   ├── SCL ─┤                        │
  │   │        ├── SDA                  │
  │   │        │                        │
  │  ESP32    MPU6050                   │
  │  (Master)  (Slave 0x68)            │
  └─────────────────────────────────────┘
```

### 5.3 Montagehinweise für AMR

Die Platzierung der IMU auf dem Roboter beeinflusst die Messqualität erheblich:

| Kriterium | Empfehlung |
|---|---|
| **Position** | Möglichst nahe am Drehzentrum (Mitte der Achse) |
| **Orientierung** | Achsen parallel zum Roboter-Koordinatensystem ausrichten |
| **Vibrationsentkopplung** | Doppelseitiges Schaumstoffklebeband oder Gummipuffer |
| **Abstand zu Motoren** | Mindestens 3 cm (elektromagnetische Störungen) |
| **Kabel** | Geschirmte oder verdrillte I²C-Leitungen (< 20 cm) |
| **Befestigung** | Fest, aber vibrationsentkoppelt (kein hartes Verschrauben auf Chassis) |

---

## 6 Firmware – ESP32-S3 (micro-ROS)

### 6.1 MPU6050-Treiber (Register-Level)

```cpp
// mpu6050.h – Low-Level-Treiber für MPU6050 via I²C
#pragma once
#include <Arduino.h>
#include <Wire.h>

// --- I²C-Adresse ---
#define MPU6050_ADDR        0x68

// --- Register-Adressen ---
#define REG_SMPLRT_DIV      0x19
#define REG_CONFIG          0x1A
#define REG_GYRO_CONFIG     0x1B
#define REG_ACCEL_CONFIG    0x1C
#define REG_INT_PIN_CFG     0x37
#define REG_INT_ENABLE      0x38
#define REG_INT_STATUS      0x3A
#define REG_ACCEL_XOUT_H    0x3B   // Beginn 14-Byte Burst-Read
#define REG_TEMP_OUT_H      0x41
#define REG_GYRO_XOUT_H     0x43
#define REG_PWR_MGMT_1      0x6B
#define REG_PWR_MGMT_2      0x6C
#define REG_WHO_AM_I        0x75

// --- Empfindlichkeiten (abhängig von Messbereich) ---
#define ACCEL_SENSITIVITY_2G   16384.0f  // LSB/g
#define ACCEL_SENSITIVITY_4G    8192.0f
#define ACCEL_SENSITIVITY_8G    4096.0f
#define ACCEL_SENSITIVITY_16G   2048.0f

#define GYRO_SENSITIVITY_250    131.0f   // LSB/(°/s)
#define GYRO_SENSITIVITY_500     65.5f
#define GYRO_SENSITIVITY_1000    32.8f
#define GYRO_SENSITIVITY_2000    16.4f

// --- Physikalische Konstanten ---
#define GRAVITY_MS2   9.80665f
#define DEG_TO_RAD    0.017453293f   // π / 180

struct IMUData {
    float ax, ay, az;    // Beschleunigung [m/s²]
    float gx, gy, gz;    // Drehrate [rad/s]
    float temp;          // Temperatur [°C]
};

class MPU6050 {
public:
    float accel_scale = ACCEL_SENSITIVITY_2G;
    float gyro_scale  = GYRO_SENSITIVITY_500;

    // Kalibrierungs-Offsets (werden beim Start bestimmt)
    float gyro_offset_x = 0.0f, gyro_offset_y = 0.0f, gyro_offset_z = 0.0f;
    float accel_offset_x = 0.0f, accel_offset_y = 0.0f, accel_offset_z = 0.0f;

    bool begin(uint8_t sda_pin = 5, uint8_t scl_pin = 6) {
        Wire.begin(sda_pin, scl_pin);
        Wire.setClock(400000);  // 400 kHz Fast-Mode

        // WHO_AM_I prüfen
        if (readByte(REG_WHO_AM_I) != 0x68) {
            return false;
        }

        // Aus Sleep-Modus aufwecken, PLL mit X-Gyro als Taktquelle
        writeByte(REG_PWR_MGMT_1, 0x01);  // CLKSEL = 1
        delay(100);

        // Alle Achsen aktivieren
        writeByte(REG_PWR_MGMT_2, 0x00);

        // DLPF konfigurieren (42 Hz Bandbreite)
        writeByte(REG_CONFIG, 0x03);       // DLPF_CFG = 3

        // Abtastrate: 1000 / (1 + 19) = 50 Hz
        writeByte(REG_SMPLRT_DIV, 19);

        // Gyroskop: ±500 °/s
        writeByte(REG_GYRO_CONFIG, 0x08);  // FS_SEL = 1
        gyro_scale = GYRO_SENSITIVITY_500;

        // Beschleunigung: ±2 g
        writeByte(REG_ACCEL_CONFIG, 0x00); // AFS_SEL = 0
        accel_scale = ACCEL_SENSITIVITY_2G;

        // Data-Ready-Interrupt aktivieren (optional)
        writeByte(REG_INT_PIN_CFG, 0x20);  // INT_RD_CLEAR = 1
        writeByte(REG_INT_ENABLE, 0x01);   // DATA_RDY_EN = 1

        delay(50);
        return true;
    }

    // Kalibrierung: Sensor muss plan und ruhig liegen (Z nach oben)
    void calibrate(uint16_t samples = 500) {
        float sum_gx = 0, sum_gy = 0, sum_gz = 0;
        float sum_ax = 0, sum_ay = 0, sum_az = 0;
        int16_t raw[7];

        for (uint16_t i = 0; i < samples; i++) {
            readRaw(raw);
            sum_ax += (float)raw[0] / accel_scale;
            sum_ay += (float)raw[1] / accel_scale;
            sum_az += (float)raw[2] / accel_scale;
            sum_gx += (float)raw[4] / gyro_scale;
            sum_gy += (float)raw[5] / gyro_scale;
            sum_gz += (float)raw[6] / gyro_scale;
            delay(2);
        }

        // Gyroskop-Offsets: Mittelwert im Ruhezustand ≈ 0
        gyro_offset_x = sum_gx / samples;
        gyro_offset_y = sum_gy / samples;
        gyro_offset_z = sum_gz / samples;

        // Beschleunigungs-Offsets: X, Y ≈ 0; Z ≈ 1 g
        accel_offset_x = sum_ax / samples;
        accel_offset_y = sum_ay / samples;
        accel_offset_z = sum_az / samples - 1.0f;  // 1 g abziehen
    }

    // Kalibrierte Sensordaten lesen
    IMUData read() {
        int16_t raw[7];
        readRaw(raw);

        IMUData data;

        // Beschleunigung [m/s²]
        data.ax = ((float)raw[0] / accel_scale - accel_offset_x) * GRAVITY_MS2;
        data.ay = ((float)raw[1] / accel_scale - accel_offset_y) * GRAVITY_MS2;
        data.az = ((float)raw[2] / accel_scale - accel_offset_z) * GRAVITY_MS2;

        // Temperatur [°C]
        data.temp = (float)raw[3] / 340.0f + 36.53f;

        // Drehrate [rad/s]
        data.gx = ((float)raw[4] / gyro_scale - gyro_offset_x) * DEG_TO_RAD;
        data.gy = ((float)raw[5] / gyro_scale - gyro_offset_y) * DEG_TO_RAD;
        data.gz = ((float)raw[6] / gyro_scale - gyro_offset_z) * DEG_TO_RAD;

        return data;
    }

    // Data-Ready-Status abfragen
    bool dataReady() {
        return (readByte(REG_INT_STATUS) & 0x01) != 0;
    }

private:
    // 14-Byte Burst-Read: Accel(6) + Temp(2) + Gyro(6)
    void readRaw(int16_t *dest) {
        uint8_t buf[14];
        Wire.beginTransmission(MPU6050_ADDR);
        Wire.write(REG_ACCEL_XOUT_H);
        Wire.endTransmission(false);  // Repeated Start
        Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)14, (uint8_t)true);

        for (uint8_t i = 0; i < 14; i++) {
            buf[i] = Wire.read();
        }

        // High-Byte << 8 | Low-Byte → 16-Bit Zweierkomplement
        for (uint8_t i = 0; i < 7; i++) {
            dest[i] = (int16_t)(buf[i * 2] << 8 | buf[i * 2 + 1]);
        }
    }

    void writeByte(uint8_t reg, uint8_t value) {
        Wire.beginTransmission(MPU6050_ADDR);
        Wire.write(reg);
        Wire.write(value);
        Wire.endTransmission(true);
    }

    uint8_t readByte(uint8_t reg) {
        Wire.beginTransmission(MPU6050_ADDR);
        Wire.write(reg);
        Wire.endTransmission(false);
        Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)1, (uint8_t)true);
        return Wire.read();
    }
};
```

### 6.2 Komplementärfilter (Complementary Filter)

Der Komplementärfilter kombiniert Gyroskop-Integration (schnelle Dynamik, aber Drift) mit Beschleunigungsmesser-Neigung (rauschig, aber driftfrei). Da der MPU6050 kein Magnetometer besitzt, können nur **Roll** und **Pitch** zuverlässig bestimmt werden; der **Yaw**-Winkel driftet unvermeidlich.

```cpp
// complementary_filter.h
#pragma once
#include <math.h>

class ComplementaryFilter {
public:
    float roll  = 0.0f;    // [rad]
    float pitch = 0.0f;    // [rad]
    float yaw   = 0.0f;    // [rad] – nur Gyro-Integration, driftet!
    float alpha;            // Filterkoeffizient (typisch 0,96 … 0,98)

    ComplementaryFilter(float filter_coeff = 0.98f)
        : alpha(filter_coeff) {}

    // Initialisierung aus Beschleunigungsdaten (Sensor in Ruhe)
    void init(float ax, float ay, float az) {
        roll  = atan2f(ay, az);
        pitch = atan2f(-ax, sqrtf(ay * ay + az * az));
        yaw   = 0.0f;
    }

    // Update-Schritt (dt in Sekunden)
    void update(float ax, float ay, float az,
                float gx, float gy, float gz, float dt) {
        // Neigungswinkel aus Beschleunigungsmesser [rad]
        float accel_roll  = atan2f(ay, az);
        float accel_pitch = atan2f(-ax, sqrtf(ay * ay + az * az));

        // Komplementärfilter: Gyro-Integration + Accel-Korrektur
        roll  = alpha * (roll  + gx * dt) + (1.0f - alpha) * accel_roll;
        pitch = alpha * (pitch + gy * dt) + (1.0f - alpha) * accel_pitch;

        // Yaw: nur Gyro-Integration (driftet ohne Magnetometer!)
        yaw  += gz * dt;
    }
};
```

**Erklärung des Filterkoeffizienten α:**

| α | Verhalten | Anwendung |
|---|---|---|
| 0,90 | Stärkere Accel-Gewichtung, schnellere Drift-Korrektur | Vibrationsarme Umgebung |
| **0,98** | **Ausgewogen** | **AMR Standardwert** |
| 0,995 | Stärkere Gyro-Gewichtung, langsamere Drift-Korrektur | Hochdynamisch |

> **Yaw-Drift ohne Magnetometer:** Der MPU6050 besitzt keinen Magnetometer (Kompass). Der Yaw-Winkel wird ausschließlich durch Gyro-Integration bestimmt und driftet typisch mit 1 … 5 °/min. Für die AMR-Anwendung wird der Yaw-Winkel aus der Rad-Odometrie (Differentialantrieb) gewonnen und im EKF mit dem Gyroskop fusioniert. Ein alternatives Upgrade ist der BNO055 (9-Achsen-IMU mit integriertem Fusionsalgorithmus).

### 6.3 Achsentransformation (Sensor → ROS)

Die Orientierung des MPU6050 auf dem Roboter bestimmt die nötige Koordinatentransformation. Der folgende Code zeigt die Transformation für die häufigste Einbaulage: **GY-521-Board flach auf dem Roboter, Bauteilseite oben, Steckerleiste nach hinten.**

```cpp
// axis_transform.h – Achsentransformation MPU6050 → ROS (REP 103)
#pragma once
#include "mpu6050.h"

// Einbaulage: GY-521 flach, Chip oben, X-Achse des Sensors = Vorwärts
// Sensor:  X = vorwärts, Y = links,  Z = oben (zufällig REP-103-konform)
// ROS:     X = vorwärts, Y = links,  Z = oben
// → Keine Transformation nötig bei dieser Einbaulage.

// Für andere Einbaulagen die Vorzeichen und Achsenzuordnung anpassen:
//
// Beispiel: Sensor um 90° gedreht (Y zeigt vorwärts)
//   ros_ax =  sensor_ay;   ros_gx =  sensor_gy;
//   ros_ay = -sensor_ax;   ros_gy = -sensor_gx;
//   ros_az =  sensor_az;   ros_gz =  sensor_gz;

inline void transformToROS(IMUData &data) {
    // Standardfall: Keine Transformation bei X-vorwärts-Einbau
    // Bei abweichender Montage hier Achsen tauschen/invertieren
    (void)data;  // Platzhalter
}
```

### 6.4 micro-ROS IMU-Publisher

```cpp
// imu_publisher.h – IMU-Daten als sensor_msgs/Imu über micro-ROS
#pragma once

#include <micro_ros_platformio.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <sensor_msgs/msg/imu.h>

#include "mpu6050.h"
#include "complementary_filter.h"
#include "axis_transform.h"

class IMUPublisher {
public:
    rcl_publisher_t publisher;
    sensor_msgs__msg__Imu imu_msg;

    MPU6050 mpu;
    ComplementaryFilter filter;
    uint32_t last_update_us = 0;

    bool begin(rcl_node_t *node) {
        // Publisher initialisieren
        rclc_publisher_init_default(
            &publisher, node,
            ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu),
            "imu");

        // MPU6050 starten
        if (!mpu.begin()) {
            return false;
        }

        // Kalibrierung (Sensor muss ruhig und plan liegen)
        mpu.calibrate(500);

        // Komplementärfilter initialisieren
        IMUData init_data = mpu.read();
        filter.init(init_data.ax, init_data.ay, init_data.az);

        // Frame-ID setzen
        imu_msg.header.frame_id.data = (char *)"imu_link";
        imu_msg.header.frame_id.size = 8;
        imu_msg.header.frame_id.capacity = 9;

        // Kovarianzmatrizen setzen (Diagonale)
        // Orientierung: unbekannt (MPU6050 liefert keine Quaternion)
        imu_msg.orientation_covariance[0] = -1.0;  // Unbekannt

        // Drehrate: σ² ≈ (0,005 °/s/√Hz × √42Hz × π/180)²
        double gyro_var = 0.0001;  // (rad/s)² – empirisch anpassen
        imu_msg.angular_velocity_covariance[0] = gyro_var;
        imu_msg.angular_velocity_covariance[4] = gyro_var;
        imu_msg.angular_velocity_covariance[8] = gyro_var;

        // Beschleunigung: σ² ≈ (400 µg/√Hz × √42Hz × 9,81)²
        double accel_var = 0.006;  // (m/s²)² – empirisch anpassen
        imu_msg.linear_acceleration_covariance[0] = accel_var;
        imu_msg.linear_acceleration_covariance[4] = accel_var;
        imu_msg.linear_acceleration_covariance[8] = accel_var;

        last_update_us = micros();
        return true;
    }

    void update() {
        IMUData data = mpu.read();
        transformToROS(data);

        // Zeitschritt berechnen
        uint32_t now_us = micros();
        float dt = (float)(now_us - last_update_us) / 1000000.0f;
        last_update_us = now_us;

        // Komplementärfilter aktualisieren
        filter.update(data.ax, data.ay, data.az,
                      data.gx, data.gy, data.gz, dt);

        // Timestamp setzen
        imu_msg.header.stamp.sec = (int32_t)(millis() / 1000);
        imu_msg.header.stamp.nanosec =
            (uint32_t)((millis() % 1000) * 1000000);

        // Drehrate [rad/s]
        imu_msg.angular_velocity.x = data.gx;
        imu_msg.angular_velocity.y = data.gy;
        imu_msg.angular_velocity.z = data.gz;

        // Beschleunigung [m/s²]
        imu_msg.linear_acceleration.x = data.ax;
        imu_msg.linear_acceleration.y = data.ay;
        imu_msg.linear_acceleration.z = data.az;

        // Orientierung als Quaternion (aus Roll/Pitch)
        // Yaw wird auf 0 gesetzt (driftet ohne Magnetometer)
        float cr = cosf(filter.roll  * 0.5f);
        float sr = sinf(filter.roll  * 0.5f);
        float cp = cosf(filter.pitch * 0.5f);
        float sp = sinf(filter.pitch * 0.5f);
        float cy = cosf(filter.yaw   * 0.5f);
        float sy = sinf(filter.yaw   * 0.5f);

        imu_msg.orientation.w = cr * cp * cy + sr * sp * sy;
        imu_msg.orientation.x = sr * cp * cy - cr * sp * sy;
        imu_msg.orientation.y = cr * sp * cy + sr * cp * sy;
        imu_msg.orientation.z = cr * cp * sy - sr * sp * cy;

        // Publizieren
        rcl_publish(&publisher, &imu_msg, NULL);
    }
};
```

### 6.5 Integration in main.cpp

```cpp
// main.cpp – Auszug: IMU-Integration in bestehende Motor-Firmware
#include <Arduino.h>
#include <micro_ros_platformio.h>

#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include "imu_publisher.h"
// #include "motor_driver.h"    // Aus Motor-Treiber-Dokumentation
// #include "encoder.h"          // Aus Motor-Treiber-Dokumentation

// --- Objekte ---
IMUPublisher imu_pub;

// micro-ROS Infrastruktur
rclc_executor_t executor;
rclc_support_t  support;
rcl_allocator_t allocator;
rcl_node_t      node;
rcl_timer_t     imu_timer;

// --- Timer-Callback: IMU bei 50 Hz ---
void imu_timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
    RCLC_UNUSED(last_call_time);
    if (timer == NULL) return;
    imu_pub.update();
}

void setup() {
    Serial.begin(115200);
    set_microros_serial_transports(Serial);
    delay(2000);

    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "amr_sensor_node", "", &support);

    // IMU Publisher starten
    if (!imu_pub.begin(&node)) {
        // Fehlerbehandlung: WHO_AM_I fehlgeschlagen
        while (true) { delay(100); }
    }

    // Timer: IMU @ 50 Hz (passend zu SMPLRT_DIV = 19)
    rclc_timer_init_default(&imu_timer, &support,
        RCL_MS_TO_NS(20),  // 20 ms = 50 Hz
        imu_timer_callback);

    // Executor: Timer + ggf. weitere Handles (Motor, Encoder)
    rclc_executor_init(&executor, &support.context, 2, &allocator);
    rclc_executor_add_timer(&executor, &imu_timer);
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
}
```

### 6.6 PlatformIO-Konfiguration

```ini
; platformio.ini – Ergänzung für MPU6050
[env:seeed_xiao_esp32s3]
platform  = espressif32
board     = seeed_xiao_esp32s3
framework = arduino
lib_deps  =
    https://github.com/micro-ROS/micro_ros_platformio
board_microros_distro   = humble
board_microros_transport = serial

; Wire-Bibliothek ist im Arduino-Framework enthalten
; Keine zusätzliche MPU6050-Bibliothek nötig (Register-Level-Treiber)
```

---

## 7 ROS 2 – Integration und Test

### 7.1 Topic-Struktur

| Topic | Nachrichtentyp | Frequenz | Quelle |
|---|---|---|---|
| `/imu` | `sensor_msgs/msg/Imu` | 50 Hz | ESP32-S3 (micro-ROS) |
| `/mcu/wheel_odom` | `std_msgs/msg/Float32MultiArray` | 50 Hz | ESP32-S3 (micro-ROS) |
| `/odom` | `nav_msgs/msg/Odometry` | 50 Hz | Pi 5 (`robot_localization`) |

### 7.2 sensor_msgs/Imu – Nachrichtenstruktur

```yaml
# sensor_msgs/msg/Imu
header:
  stamp:
    sec: 1234567890
    nanosec: 123456789
  frame_id: "imu_link"

orientation:             # Quaternion (w, x, y, z)
  w: 0.999               # Aus Komplementärfilter (Roll, Pitch)
  x: 0.01                # Yaw = 0 oder driftig
  y: 0.02
  z: 0.0
orientation_covariance: [-1, 0, 0, 0, 0, 0, 0, 0, 0]
# -1 im ersten Element: Orientierung unbekannt / nicht vertrauenswürdig

angular_velocity:        # [rad/s]
  x: 0.001
  y: -0.002
  z: 0.015
angular_velocity_covariance: [0.0001, 0, 0, 0, 0.0001, 0, 0, 0, 0.0001]

linear_acceleration:     # [m/s²]
  x: 0.05
  y: -0.02
  z: 9.81
linear_acceleration_covariance: [0.006, 0, 0, 0, 0.006, 0, 0, 0, 0.006]
```

### 7.3 Inbetriebnahme und Diagnose

```bash
# 1. micro-ROS Agent starten
docker run -it --rm -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:humble serial --dev /dev/ttyACM0 -v6

# 2. I²C-Verbindung prüfen (auf dem ESP32 via Serial-Monitor)
#    → Meldung "MPU6050 initialization successful" erwartet
#    → Falls "WHO_AM_I failed": Verkabelung und Adresse prüfen

# 3. Topics auflisten
ros2 topic list
# /imu
# /mcu/wheel_odom

# 4. IMU-Daten live anzeigen
ros2 topic echo /imu

# 5. Frequenz prüfen (Soll: ~50 Hz)
ros2 topic hz /imu
# average rate: 50.02

# 6. Bandbreite prüfen
ros2 topic bw /imu
# ~12 kB/s (typisch für 50 Hz Imu-Messages)

# 7. Schnelltest: Roboter um Z-Achse drehen
ros2 topic echo /imu --field angular_velocity.z
# Erwartung: positiver Wert bei Gegenuhrzeigersinn-Drehung (REP 103)

# 8. Kalibrierungsprüfung (Sensor in Ruhe, plan):
#    angular_velocity: alle Achsen ≈ 0 (< 0,01 rad/s)
#    linear_acceleration: x ≈ 0, y ≈ 0, z ≈ 9,81 m/s²
```

### 7.4 Sensorfusion mit robot_localization

Der EKF-Node `robot_localization` fusioniert IMU- und Odometrie-Daten. Konfigurationsbeispiel für den AMR:

```yaml
# ekf.yaml – robot_localization Konfiguration
ekf_filter_node:
  ros__parameters:
    frequency: 50.0
    two_d_mode: true          # AMR fährt auf ebenem Boden
    publish_tf: true

    # Odometrie-Quelle (aus Encoder)
    odom0: /wheel_odom
    odom0_config: [true,  true,  false,  # x, y, z
                   false, false, true,   # roll, pitch, yaw
                   false, false, false,  # vx, vy, vz
                   false, false, false,  # vroll, vpitch, vyaw
                   false, false, false]  # ax, ay, az

    # IMU-Quelle
    imu0: /imu
    imu0_config: [false, false, false,   # x, y, z
                  true,  true,  false,   # roll, pitch, yaw (Yaw → false bei Drift)
                  false, false, false,   # vx, vy, vz
                  false, false, true,    # vroll, vpitch, vyaw (Z-Gyro nutzen)
                  true,  true,  false]   # ax, ay, az
    imu0_remove_gravitational_acceleration: true
```

> **Yaw-Strategie:** Da der MPU6050 keinen Magnetometer besitzt, wird der Yaw-Winkel aus der Orientierung **nicht** für den EKF genutzt (`imu0_config`: yaw = false). Stattdessen liefert die Gyroskop-Drehrate um die Z-Achse (`vyaw = true`) die Drehinformation, die der EKF mit dem Yaw aus der Rad-Odometrie fusioniert.

---

## 8 Kalibrierung

### 8.1 Gyroskop-Offset-Kalibrierung

Das Gyroskop des MPU6050 hat einen herstellerseitigen Nullpunkt-Fehler (Zero-Rate Output) von bis zu ±20 °/s. Ohne Kalibrierung würde dieser Offset bei Integration schnell zu großen Winkelfehlern führen.

**Verfahren:** Beim Einschalten sammelt die Firmware 500 Messwerte bei ruhendem Sensor und bildet den Mittelwert. Dieser Offset wird von allen späteren Messungen subtrahiert.

| Voraussetzung | Beschreibung |
|---|---|
| Sensor plan und ruhig | GY-521 auf ebener Fläche, Z-Achse nach oben |
| Kein Vibrationseinfluss | Motoren aus, keine externe Erschütterung |
| Wartezeit nach Power-On | Mindestens 100 ms (thermische Stabilisierung) |
| Dauer | ~1 s (500 Samples × 2 ms) |

### 8.2 Beschleunigungsmesser-Offset-Kalibrierung

Der Beschleunigungsmesser hat einen Nullpunkt-Fehler von ±80 mg. Die Kalibrierung bestimmt die Abweichung jeder Achse vom erwarteten Wert (X = 0 g, Y = 0 g, Z = +1 g bei horizontaler Lage).

### 8.3 Temperatur-Drift-Kompensation (optional)

Für höhere Genauigkeit kann die temperaturabhängige Gyroskop-Drift über eine Lookup-Tabelle oder lineare Regression kompensiert werden:

1. Sensor bei verschiedenen Temperaturen (z. B. 20 °C, 30 °C, 40 °C, 50 °C) kalibrieren.
2. Offset pro Achse als Funktion der Temperatur speichern.
3. Zur Laufzeit den aktuellen Temperaturwert des integrierten Sensors lesen und den Offset interpolieren.

Diese Kompensation ist für AMR-Indoor-Anwendungen (stabile Raumtemperatur ~20 … 25 °C) in der Regel nicht erforderlich.

---

## 9 Limitierungen und Alternativen

### 9.1 Bekannte Einschränkungen des MPU6050

| Einschränkung | Auswirkung | Gegenmaßnahme |
|---|---|---|
| **Kein Magnetometer** | Yaw-Drift (~1 … 5 °/min) | Rad-Odometrie für Yaw; EKF-Fusion |
| **Gyroskop-Drift über Temperatur** | Offset variiert mit Temperatur | Startup-Kalibrierung; ggf. Temp-Kompensation |
| **Beschleunigungsmesser-Rauschen** | 400 µg/√Hz (relativ hoch) | DLPF-Filterung; Komplementärfilter |
| **Keine absolute Orientierung** | Nur relative Drehrate und Beschleunigung | Sensorfusion mit weiteren Quellen |
| **End-of-Life (EOL)** | MPU6050 wird von InvenSense/TDK nicht mehr aktiv beworben | ICM-20948 oder BNO055 als Nachfolger |

### 9.2 Alternativen

| Sensor | Achsen | Magnetometer | On-Chip Fusion | I²C-Adresse | Bemerkung |
|---|---|---|---|---|---|
| **MPU6050** | 6 (3G + 3A) | Nein | DMP (limitiert) | 0x68/0x69 | Günstig, weit verbreitet |
| **MPU9250** | 9 (3G + 3A + 3M) | Ja (AK8963) | DMP | 0x68/0x69 | Nachfolger, Yaw stabil |
| **ICM-20948** | 9 (3G + 3A + 3M) | Ja (AK09916) | DMP 3.0 | 0x68/0x69 | Aktueller TDK-Sensor |
| **BNO055** | 9 (3G + 3A + 3M) | Ja | ARM Cortex-M0+ | 0x28/0x29 | Quaternion-Ausgabe, einfach |

> **Upgrade-Pfad:** Der BNO055 liefert direkt kalibrierte Quaternionen, benötigt keinen Komplementärfilter und hat keinen Yaw-Drift. Für anspruchsvolle AMR-Anwendungen ist er die bevorzugte Alternative. Der I²C-Anschluss bleibt identisch; nur der Treiber muss angepasst werden.

---

## 10 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| `WHO_AM_I` liefert nicht `0x68` | I²C-Verbindung unterbrochen | SDA/SCL-Verkabelung und Lötstellen prüfen |
| `WHO_AM_I` liefert `0x98` oder `0x19` | Klon-Chip (MPU6886 o. ä.) | Register-Kompatibilität prüfen; ggf. Treiber anpassen |
| Alle Sensorwerte = 0 | Sensor im Sleep-Modus | `PWR_MGMT_1` auf `0x01` setzen (Bit 6 = Sleep) |
| I²C-Fehler (NACK) | Adresse falsch oder AD0 offen | AD0 explizit auf GND ziehen; Adresse `0x68` prüfen |
| I²C-Fehler bei 400 kHz | Leitungen zu lang / Pull-Ups fehlen | Leitungen kürzen (< 20 cm); ggf. externe 2,2-kΩ-Pull-Ups |
| Beschleunigung Z ≠ 9,81 m/s² | Sensor nicht kalibriert oder nicht plan | Kalibrierung wiederholen; Sensor horizontal ausrichten |
| Gyroskop driftet stark | Kein Offset-Abzug oder Temperaturänderung | `calibrate()` nach jedem Einschalten aufrufen |
| Yaw driftet > 5 °/min | Normal für 6-Achsen-IMU ohne Magnetometer | EKF mit Rad-Odometrie kombinieren |
| Werte springen / verrauscht | DLPF zu breit oder Vibration | `DLPF_CFG` auf 3 oder 4 setzen; Vibrationsentkopplung |
| I²C kollidiert mit anderem Sensor | Adresskonflikt | AD0 = HIGH → 0x69; oder I²C-Multiplexer (TCA9548A) |
| ESP32-S3 hängt bei Wire.requestFrom | I²C-Bus blockiert | Timeout in Wire implementieren; SDA-Recovery-Sequenz |
| DMP-Daten unzuverlässig | DMP-Firmware-Upload komplex | Register-Level-Treiber (wie oben) statt DMP verwenden |

---

## 11 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   MPU6050 IMU – Kurzprofil für AMR-Integration                          │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   SENSOR                     │                                           │
│   Bezeichnung                │ InvenSense MPU-6050 (MEMS)               │
│   Breakout-Board             │ GY-521                                    │
│   Sensorachsen               │ 6 (3× Gyro + 3× Accel)                  │
│   ADC-Auflösung              │ 16 Bit pro Achse                         │
│   Kommunikation              │ I²C, 400 kHz, Adresse 0x68              │
│   Versorgung (Board)         │ 3,3 … 5,0 V (LDO auf GY-521)           │
│   Stromaufnahme              │ 3,9 mA (aktiv)                           │
│                              │                                           │
│   GYROSKOP                   │                                           │
│   Messbereich (AMR)          │ ±500 °/s (FS_SEL = 1)                   │
│   Empfindlichkeit            │ 65,5 LSB/(°/s)                           │
│   Rausch-Bandbreite          │ 0,005 °/s/√Hz                            │
│   Nullpunkt-Drift            │ ±20 °/s (vor Kalibrierung)              │
│                              │                                           │
│   BESCHLEUNIGUNGSMESSER      │                                           │
│   Messbereich (AMR)          │ ±2 g (AFS_SEL = 0)                      │
│   Empfindlichkeit            │ 16.384 LSB/g                              │
│   Rausch-Bandbreite          │ 400 µg/√Hz                               │
│                              │                                           │
│   KONFIGURATION              │                                           │
│   DLPF-Bandbreite            │ 42 Hz (DLPF_CFG = 3)                    │
│   Abtastrate                 │ 50 Hz (SMPLRT_DIV = 19)                  │
│   Taktquelle                 │ PLL X-Gyro (CLKSEL = 1)                  │
│   Kalibrierung               │ 500 Samples bei Startup                  │
│   Komplementärfilter (α)     │ 0,98                                      │
│                              │                                           │
│   ROS-2-INTEGRATION          │                                           │
│   Topic                      │ /imu                                      │
│   Nachrichtentyp             │ sensor_msgs/msg/Imu                      │
│   Frame-ID                   │ imu_link                                  │
│   Publizierfrequenz          │ 50 Hz                                     │
│   Sensorfusion               │ robot_localization (EKF, 2D)             │
│                              │                                           │
│   VERKABELUNG (ESP32-S3)     │                                           │
│   SDA                        │ D4 (GPIO5)                                │
│   SCL                        │ D5 (GPIO6)                                │
│   INT                        │ D3 (GPIO4) – optional                    │
│   VCC                        │ 3,3 V                                     │
│   GND                        │ Gemeinsame Masse                         │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 12 Quellen

| Quelle | URL |
|---|---|
| MPU-6050 Product Specification (Datasheet) | [invensense.tdk.com (PDF)](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf) |
| MPU-6050 Register Map and Descriptions | [invensense.tdk.com (PDF)](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf) |
| I2Cdevlib MPU6050 Referenz | [i2cdevlib.com](https://www.i2cdevlib.com/docs/html/class_m_p_u6050.html) |
| ROS 2 MPU6050 Driver (C++) | [github.com/kimsniper/ros2_mpu6050](https://github.com/kimsniper/ros2_mpu6050) |
| ROS 2 MPU6050 Driver (Python) | [github.com/hiwad-aziz/ros2_mpu6050_driver](https://github.com/hiwad-aziz/ros2_mpu6050_driver) |
| ESP32 + MPU6050 I²C Tutorial | [tutorialspoint.com](https://www.tutorialspoint.com/esp32_for_iot/interfacing_esp32_with_mpu6050.htm) |
| IMU + ROS 2 Lessons Learned (BNO055 vs. MPU6050) | [robofoundry.medium.com](https://robofoundry.medium.com/lessons-learned-while-working-with-imu-sensor-ros2-and-raspberry-pi-a4fec18a7c7) |
| robot_localization (ROS 2) | [docs.ros.org](https://docs.ros.org/en/humble/p/robot_localization/) |
| REP 103 – Standard Units of Measure | [ros.org/reps/rep-0103](https://www.ros.org/reps/rep-0103.html) |

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: MPU-6050 Datasheet Rev 3.4, MPU-6050 Register Map Rev 4.2 (InvenSense/TDK), GY-521 Schaltplan, I2Cdevlib, ROS 2 sensor_msgs/Imu Spezifikation*
