# Hardware

bearbeitet am 24-2-26

- [x] Pan-Tilt Kamerakopf: 2 Sets Pan Tilt Servo (Video: <https://bit.ly/46t1qeC>)
- [x] PWM Servo-Treiber: PCA9685 PWM 16 Kanaele, 12-Bit Aufloesung (I2C) und Servo: MG996R (2x)(Metallgetriebe) 15 kg/cm Drehmoment, 6V@2,5 A Blockierstrom
- [x] Global Shutter Kamera: IMX296 (CSI) mit Objektiv PT361060M3MP12 (CS-Mount 6mm)
- [x] Audiosystem für Sprachausgabe: I2S Audio-Verstaerker: Adafruit MAX98357A 3,2W@4Ohm (I2S) und Adafruit Mono-Lautsprecher: ADA3351 , 3W/4Ohm
- [x] Mikrofon-Array: Seeed ReSpeaker Mic Array v2.0 (USB)
- [x] Stromsensor: Adafruit INA260 12V@15A (I2C)
- [x] DC/DC Wandler: Pololu D36V50F6 12V/6V@5.5A
- [x] DC/DC Wandler: B0DRRMM71M 12V/5V@5A (IP68, USB-C)
- [x] 3S Li-Ion Akkupack: Samsung INR18650-35E 12V@8A.  (10 A Sicherung)
- [x] Longlife Strip 12V LED Streifen 5M 7,2W/m 30LED/m 10mm und IRLZ24N (Low-Side MOSFET)
- [x] Raspberry Pi 5 (8 GB), ROS 2 Humble (Docker), Debian Trixie und Seeed XIAO ESP32-S3, micro-ROS Client
- [x] Motor-Treiber: Cytron MDD3A PWM 12V@3A und Antriebsmotoren: JGA25-370 (2x) 12V Quadratur Hall-Encoder
- [x] IMU: MPU6050 6-Achsen Beschleunigung und Gyroskop (I2C)
- [x] 2D Lidar Scanner: RPLIDAR A1 (USB)
- [x] KI-Beschleuniger: Hailo-8L (PCIe)

## Strom, Querschnitte und Widerstand

| Strom (I) | PCB-Breite (1 oz) | Querschnitt (metrisch) | AWG (ca.) | Widerstand bei 20 °C | Anwendung/Referenz            |
|-----------|-------------------|------------------------|-----------|----------------------|-------------------------------|
| **20 A**  | 12,3 mm           | 4,0 mm²                | 11 – 12   | **4,45 mΩ/m**        | Hohe thermische Last          |
| **15 A**  | 8,3 mm            | 2,5 mm²                | 13 – 14   | **7,12 mΩ/m**        | Standard für Hausinstallation |
| **13 A**  | 6,8 mm            | 1,5 mm²                | 15 – 16   | **11,87 mΩ/m**       | Absicherung meist 16 A        |
| **10 A**  | 4,7 mm            | 1,0 mm²                | 17 – 18   | **17,80 mΩ/m**       | Typisch für Kaltgerätekabel   |
| **8 A**   | 3,5 mm            | 0,75 mm²               | 18 – 19   | **23,73 mΩ/m**       | Kleingeräteleitungen          |
| **5 A**   | 1,8 mm            | 0,5 mm²                | 20        | **35,60 mΩ/m**       | Signal- und Steuerleitungen   |
| **1 A**   | 0,2 mm            | 0,14 mm²               | 26        | **127,14 mΩ/m**      | Datenleitungen                |

---

**PCB**: Die Werte basieren auf der IPC-2221 (Standard für Designrichtlinien von Leiterplatten). Angenommene Randbedingungen: Außenlage, zulässige Erwärmung $\Delta T$ = 20 K.

**Kabel**: Die Querschnitte orientieren sich an der DIN VDE 0298-4 (Verwendung von Kabeln und isolierten Leitungen) sowie der IEC 60228 (Leiterklassen).
