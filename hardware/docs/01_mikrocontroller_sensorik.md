# 01 - Mikrocontroller und Sensorik

Dieses Dokument beschreibt saemtliche Mikrocontroller, Einplatinencomputer und Sensoren des AMR-Systems. Die technischen Daten wurden aus den jeweiligen Herstellerdatenblaettern extrahiert.

---

## 1. Seeed Studio XIAO ESP32-S3

Der Seeed Studio XIAO ESP32-S3 dient als Low-Level-Steuereinheit des AMR. Er uebernimmt die Echtzeit-Motorregelung (PID bei 50 Hz auf Core 1) und die micro-ROS-Kommunikation mit dem Raspberry Pi 5 (auf Core 0) ueber UART. Durch die FreeRTOS-basierte Dual-Core-Partitionierung werden deterministische Regelzyklen gewaehrleistet.

![Seeed Studio XIAO ESP32-S3](../datasheet/images/Seeed%20Studio%20XIAO%20ESP32-S3.png)

### 1.1 ESP32-S3 SoC - Kernspezifikationen

| Parameter | Wert |
|---|---|
| Hersteller | Espressif Systems |
| SoC-Bezeichnung | ESP32-S3 |
| CPU-Architektur | Xtensa 32-bit LX7 Dual-Core |
| Max. Taktfrequenz | 240 MHz |
| CoreMark (1 Core, 240 MHz) | 613,86 CoreMark (2,56 CoreMark/MHz) |
| CoreMark (2 Cores, 240 MHz) | 1181,60 CoreMark (4,92 CoreMark/MHz) |
| Datenbus-Breite | 128 Bit (SIMD-Befehle) |
| ROM | 384 KB |
| SRAM | 512 KB |
| RTC SRAM | 16 KB |
| Wi-Fi | IEEE 802.11 b/g/n, 2,4 GHz, bis 150 Mbps |
| Bluetooth | Bluetooth 5 (LE), Bluetooth Mesh |
| USB | 1x Full-Speed USB OTG |

### 1.2 Betriebsspannung und Stromaufnahme

| Parameter | Min | Typ | Max | Einheit |
|---|---|---|---|---|
| Eingangsspannung (VDDA, VDD3P3) | 3,0 | 3,3 | 3,6 | V |
| Max. IO-Ausgangsstrom (kumulativ) | -- | -- | 1500 | mA |
| Lagertemperatur | -40 | -- | 150 | C |
| Active Mode (Wi-Fi TX, 802.11n) | -- | 283 | 286 | mA |
| Active Mode (Wi-Fi RX) | -- | 88 | 91 | mA |
| Modem-sleep (240 MHz, Dual-Core) | -- | 91,7 | 107,9 | mA |
| Modem-sleep (80 MHz, Dual-Core) | -- | 18,7 | 24,4 | mA |
| Modem-sleep (WAITI, 80 MHz) | -- | 22,0 | 36,1 | mA |
| Light-sleep | -- | 240 | -- | uA |
| Deep-sleep (RTC + Peripherie) | -- | 8 | -- | uA |
| Deep-sleep (nur RTC-Speicher) | -- | 7 | -- | uA |
| Power Off | -- | 1 | -- | uA |

### 1.3 DC-Charakteristik (3,3 V, 25 C)

| Symbol | Parameter | Min | Typ | Max | Einheit |
|---|---|---|---|---|---|
| V_IH | High-Level Eingangsspannung | 0,75 x VDD | -- | VDD + 0,3 | V |
| V_IL | Low-Level Eingangsspannung | -0,3 | -- | 0,25 x VDD | V |
| V_OH | High-Level Ausgangsspannung | 0,8 x VDD | -- | -- | V |
| V_OL | Low-Level Ausgangsspannung | -- | -- | 0,1 x VDD | V |
| I_OH | High-Level Quellenstrom | -- | 40 | -- | mA |
| I_OL | Low-Level Senkenstrom | -- | 28 | -- | mA |
| R_PU | Interner Pull-up-Widerstand | -- | 45 | -- | kOhm |
| R_PD | Interner Pull-down-Widerstand | -- | 45 | -- | kOhm |
| C_IN | Pin-Kapazitaet | -- | 2 | -- | pF |

### 1.4 Peripherie-Schnittstellen

| Schnittstelle | Anzahl | Bemerkung |
|---|---|---|
| Programmierbare GPIOs | 45 | Ueber IO MUX / GPIO-Matrix |
| UART | 3 | Inkl. Hardware-Flusskontrolle |
| I2C | 2 | Master/Slave |
| SPI | 4 | SPI, Dual SPI, Quad SPI, Octal SPI, QPI, OPI |
| I2S | 2 | Fuer Audio |
| LED PWM | 8 Kanaele | Fuer Motor-/LED-Ansteuerung |
| MCPWM | 2 | Motor Control PWM (ideal fuer Motortreiber) |
| ADC | 2x 12-Bit SAR | Bis zu 20 Kanaele, max. 100 kSPS |
| Touch-Sensing | 14 Kanaele | Kapazitiv |
| Temperatursensor | 1 | Intern |
| TWAI (CAN) | 1 | ISO 11898-1 kompatibel |
| USB OTG | 1 | Full-Speed |
| USB Serial/JTAG | 1 | Fuer Debugging und Programmierung |
| SDIO Host | 1 | 2 Slots |
| RMT | 1 | TX/RX (Fernbedienung/NeoPixel) |
| LCD Interface | 1 | 8-Bit bis 16-Bit parallel |
| Kamera-Interface | 1 | DVP 8-Bit bis 16-Bit |
| Pulse Counter | 1 | Fuer Encoder-Auswertung |
| Timer (General Purpose) | 4 | 54-Bit |
| System Timer | 1 | 52-Bit |
| Watchdog Timer | 3 | Systemueberwachung |

### 1.5 XIAO-Board Pinout (D0-D10 Mapping)

Das Seeed Studio XIAO ESP32-S3 Board bricht die ESP32-S3-GPIOs auf ein kompaktes 11-Pin-Layout (D0-D10) heraus. Die Pinbelegung im AMR-Projekt ist wie folgt:

![ESP32-S3 Blockdiagramm](../datasheet/images/ESP32S3.png)

| XIAO Pin | ESP32-S3 GPIO | Funktion | Alternativ-Funktionen |
|---|---|---|---|
| D0 | GPIO1 | Motor Links Signal A | TOUCH1, ADC1_CH0 |
| D1 | GPIO2 | Motor Links Signal B | TOUCH2, ADC1_CH1 |
| D2 | GPIO3 | Motor Rechts Signal A | TOUCH3, ADC1_CH2 |
| D3 | GPIO4 | Motor Rechts Signal B | TOUCH4, ADC1_CH3 |
| D4 (SDA) | GPIO5 | I2C SDA (IMU) | TOUCH5, ADC1_CH4 |
| D5 (SCL) | GPIO6 | I2C SCL (IMU) | TOUCH6, ADC1_CH5 |
| D6 (TX) | GPIO43 | Encoder Links Phase A | U0TXD |
| D7 (RX) | GPIO44 | Encoder Rechts Phase A | U0RXD |
| D8 | GPIO7 | Gimbal Servo 1 (Pan) | TOUCH7, ADC1_CH6 |
| D9 | GPIO8 | Gimbal Servo 2 (Tilt) | TOUCH8, ADC1_CH7 |
| D10 | GPIO9 | Reserve (LED/Taster) | TOUCH9, ADC1_CH8 |
| 5V | -- | Versorgung 5 V | -- |
| GND | -- | Masse | -- |
| 3V3 | -- | Versorgung 3,3 V | -- |

### 1.6 Sicherheits-Features

| Feature | Beschreibung |
|---|---|
| Secure Boot | Verifikation der Firmware beim Start |
| Flash Encryption | Verschluesselung des externen Flash-Speichers |
| OTP (eFuse) | 4 KBit, bis zu 1792 Bit fuer Anwenderdaten |
| Kryptographie-Hardware | AES-128/256, SHA, RSA, HMAC, RNG |
| ESD-Schutz | HBM: 2 kV, CDM: 1 kV |

### 1.7 Relevanz fuer das AMR-Projekt

Der ESP32-S3 wird im AMR-Projekt spezifisch fuer folgende Aufgaben eingesetzt:

- **Core 0**: micro-ROS Agent - empfaengt `cmd_vel` (Twist-Messages), publiziert Odometrie-Daten (20 Hz) ueber UART zum Raspberry Pi 5
- **Core 1**: Echtzeit-Regelschleife - PID-Motorregelung bei 50 Hz (20 ms Takt)
- **FreeRTOS-Mutex**: Schutz geteilter Daten (Soll-Geschwindigkeiten, Odometrie) zwischen den Cores
- **MCPWM**: Ansteuerung der DC-Getriebemotoren ueber den MDD3A-Motortreiber
- **Pulse Counter / GPIO-Interrupts**: Auswertung der Encoder-Signale
- **I2C**: Kommunikation mit der MPU6050-IMU

---

## 2. MPU6050 IMU (GY-521 Breakout-Board)

Die MPU6050 IMU (Inertial Measurement Unit) von InvenSense/TDK erfasst Beschleunigungen und Drehraten in drei Achsen. Im AMR-System liefert sie Gyroskopdaten fuer die Odometrie-Fusion mittels Extended Kalman Filter (EKF) auf dem Raspberry Pi 5. Das verwendete Breakout-Board ist das AZ-Delivery GY-521 Modul.

### 2.1 Allgemeine Spezifikationen

| Parameter | Wert |
|---|---|
| Hersteller IC | InvenSense (TDK) |
| Breakout-Board | AZ-Delivery GY-521 |
| Sensortyp | 6-Achsen IMU (3-Achsen Gyro + 3-Achsen Beschleunigung) |
| Kommunikation | I2C (bis 400 kHz) |
| I2C-Adresse | 0x68 (AD0=LOW) / 0x69 (AD0=HIGH) |
| Versorgungsspannung V_DD | 2,375 - 3,46 V |
| V_LOGIC (MPU-6050) | 1,8 V +/- 5% oder V_DD |
| Betriebstemperatur | -40 C bis +105 C |
| Lagertemperatur | -40 C bis +125 C |
| ESD-Schutz | HBM: 2 kV, MM: 200 V |
| ADC-Aufloesung | 16 Bit (Gyro und Beschleunigung) |

### 2.2 Gyroskop-Spezifikationen

| Parameter | Wert | Einheit |
|---|---|---|
| Messachsen | X, Y, Z | -- |
| Messbereiche (einstellbar) | +/-250, +/-500, +/-1000, +/-2000 | Grad/s |
| Empfindlichkeit (FS_SEL=0, +/-250) | 131 | LSB/(Grad/s) |
| Empfindlichkeit (FS_SEL=1, +/-500) | 65,5 | LSB/(Grad/s) |
| Empfindlichkeit (FS_SEL=2, +/-1000) | 32,8 | LSB/(Grad/s) |
| Empfindlichkeit (FS_SEL=3, +/-2000) | 16,4 | LSB/(Grad/s) |
| Empfindlichkeitstoleranz | +/-3 | % |
| Nullpunkt-Drift (Initial ZRO) bei 25 C | +/-20 | Grad/s |
| ZRO Temperaturvariation (-40 bis +85 C) | +/-20 | Grad/s |
| Nichtlinearitaet | 0,2 | % |
| Kreuzachsen-Empfindlichkeit | +/-2 | % |
| Rauschspektraldichte (10 Hz) | 0,005 | Grad/s/Wurzel(Hz) |
| Tiefpass-Filter (programmierbar) | 5 - 256 | Hz |
| Ausgangsdatenrate (programmierbar) | 4 - 8000 | Hz |
| Startzeit (ZRO Settling) | 30 | ms |
| Betriebsstrom (Gyroskop) | 3,6 | mA |

### 2.3 Beschleunigungssensor-Spezifikationen

| Parameter | Wert | Einheit |
|---|---|---|
| Messachsen | X, Y, Z | -- |
| Messbereiche (einstellbar) | +/-2, +/-4, +/-8, +/-16 | g |
| Empfindlichkeit (AFS_SEL=0, +/-2g) | 16.384 | LSB/g |
| Empfindlichkeit (AFS_SEL=1, +/-4g) | 8.192 | LSB/g |
| Empfindlichkeit (AFS_SEL=2, +/-8g) | 4.096 | LSB/g |
| Empfindlichkeit (AFS_SEL=3, +/-16g) | 2.048 | LSB/g |
| Kalibrierungstoleranz | +/-3 | % |
| Temperaturabhaengigkeit | +/-0,02 | %/C |
| Nichtlinearitaet | 0,5 | % |
| Kreuzachsen-Empfindlichkeit | +/-2 | % |
| Nullpunkt-Toleranz (X, Y) | +/-50 | mg |
| Nullpunkt-Toleranz (Z) | +/-80 | mg |
| Rauschspektraldichte (10 Hz) | 400 | ug/Wurzel(Hz) |
| Tiefpass-Filter (programmierbar) | 5 - 260 | Hz |
| Ausgangsdatenrate (programmierbar) | 4 - 1000 | Hz |
| Betriebsstrom (Beschleunigungssensor) | 500 | uA |
| Standby-Strom | 5 | uA |

### 2.4 GY-521 Board Pinbelegung

| Pin | Funktion | Beschreibung |
|---|---|---|
| VCC | Stromversorgung | 3,3 V - 5 V (Onboard-Regler) |
| GND | Masse | Gemeinsame Masse |
| SCL | I2C Clock | Serieller Takt (an ESP32-S3 D5 / GPIO6) |
| SDA | I2C Data | Serielle Daten (an ESP32-S3 D4 / GPIO5) |
| XDA | Auxiliary Data | Fuer externen Magnetometer (nicht verwendet) |
| XCL | Auxiliary Clock | Fuer externen Magnetometer (nicht verwendet) |
| AD0 | Adresswahl | LOW = 0x68, HIGH = 0x69 |
| INT | Interrupt | Digitaler Interrupt-Ausgang |

### 2.5 Relevanz fuer das AMR-Projekt

- **Odometrie-Fusion**: Die Gyroskopdaten (Gierrate, Z-Achse) werden ueber den Extended Kalman Filter (robot_localization / EKF) mit den Rad-Encoder-Daten fusioniert, um die Orientierungsschaetzung zu verbessern.
- **Drift-Kompensation**: Die Gyro-Drift von +/-20 Grad/s erfordert eine Kalibrierung beim Systemstart (Bias-Bestimmung im Ruhezustand).
- **Messbereich**: Fuer den AMR mit max. 0,4 m/s Zielgeschwindigkeit ist der +/-250 Grad/s-Bereich mit hoechster Empfindlichkeit (131 LSB/(Grad/s)) ausreichend.
- **Abtastrate**: Typischerweise 100-200 Hz fuer die Roboter-Odometrie konfiguriert.

---

## 3. RPLIDAR A1 (SLAMTEC)

Der RPLIDAR A1 ist ein kostenguenstiger 360-Grad-2D-Laserscanner (LiDAR) von SLAMTEC. Er bildet den primaeren Umgebungssensor fuer SLAM (Simultaneous Localization and Mapping) und die Hinderniserkennung im Nav2-Navigationsstack.

### 3.1 Technische Spezifikationen

| Parameter | Wert |
|---|---|
| Hersteller | SLAMTEC |
| Modell | RPLIDAR A1M8 |
| Messprinzip | Laser-Triangulation (OPTMAG-Design) |
| Laserklasse | Klasse 1 (augensicher) |
| Wellenlaenge | 785 nm (Infrarot) |
| Abmessungen | 98,5 x 70 x 60 mm |
| Gewicht | 170 g (ohne Kabel) |

### 3.2 Messleistung

| Parameter | Wert | Einheit |
|---|---|---|
| Reichweite (weisse Objekte) | 0,15 - 12 | m |
| Winkelbereich | 0 - 360 | Grad |
| Winkelaufloesung | ca. 1 | Grad |
| Distanzaufloesung | < 0,5 | mm |
| Sample-Frequenz | 2000 - 2010 (typ. 8000) | Messungen/s |
| Sample-Dauer | 0,5 | ms |
| Scan-Rate (konfigurierbar) | 1 - 10 (typ. 5,5) | Hz |

### 3.3 Schnittstelle und Anschluss

| Parameter | Wert |
|---|---|
| Kommunikation | UART (ueber USB-Adapter) |
| Anschluss am Raspberry Pi | USB (Plug and Play) |
| Stromversorgung | 5 V (ueber USB) |
| Lieferumfang | RPLIDAR A1, USB-Adapter, Kommunikationskabel |

### 3.4 Relevanz fuer das AMR-Projekt

- **SLAM**: Der RPLIDAR A1 liefert 2D-Laserscan-Daten fuer die SLAM Toolbox (async_slam_toolbox) auf dem Raspberry Pi 5. Die Kartenaufloesung betraegt 5 cm.
- **Navigation**: Die Scan-Daten fliessen in die Costmaps des Nav2-Stacks ein (Globale und Lokale Costmap) fuer Pfadplanung und Hinderniserkennung.
- **ROS2-Topic**: Der RPLIDAR-Treiber publiziert LaserScan-Messages auf `/scan`.
- **Einschraenkungen**: Die maximale Reichweite von 12 m und die Scan-Rate von 5,5 Hz sind fuer den indoor-Einsatz im 10 m x 10 m Testparcours ausreichend. Transparente Objekte (Glas) werden nicht zuverlaessig erkannt.

---

## 4. Raspberry Pi Global Shutter Camera

Die Raspberry Pi Global Shutter Camera wird fuer die visuelle Erkennung von ArUco-Markern verwendet, die zur praezisen Andockung an die Ladestation dienen (Visual Servoing). Der Global-Shutter-Sensor vermeidet Bewegungsartefakte, die bei Rolling-Shutter-Kameras bei schnellen Bewegungen auftreten.

![Global Shutter Camera](../datasheet/images/Global%20Shutter%20Camera.png)

### 4.1 Kamera-Spezifikationen

| Parameter | Wert |
|---|---|
| Hersteller | Raspberry Pi Ltd |
| Sensor | Sony IMX296LQR-C |
| Aufloesung | 1,58 Megapixel (Farbe) |
| Sensorgroesse | 6,3 mm diagonal |
| Pixelgroesse | 3,45 um x 3,45 um |
| Shutter-Typ | Global Shutter |
| Ausgabeformat | RAW10 |
| Min. Belichtungszeit | 30 us |
| IR-Sperrfilter | Integriert (entfernbar) |
| Objektivanschluss | CS-Mount (C-CS Adapter inkl.) |
| Formfaktor | 38 x 38 x 19,8 mm (29,5 mm mit Adapter und Staubkappe) |
| Gewicht | 34 g (41 g mit Adapter und Staubkappe) |
| Anschluss | MIPI CSI-2 (15-Pin Flachbandkabel, 150 mm) |
| Stativgewinde | 1/4"-20 |
| Betriebstemperatur | 0 - 50 C |
| Produktionsende (min.) | Januar 2032 |

### 4.2 Backfokus und Objektivkompatibilitaet

| Parameter | Wert |
|---|---|
| Backfokus-Laenge | Einstellbar 12,5 - 22,4 mm |
| Unterstuetzte Objektivstandards | CS-Mount, C-Mount (mit Adapter) |

### 4.3 CS-Mount Objektiv (PT361060M3MP12)

Fuer die ArUco-Marker-Erkennung wird ein 6 mm CS-Mount-Objektiv verwendet.

| Parameter | Wert |
|---|---|
| Modell | PT361060M3MP12 |
| Bildformat | 1/2" |
| Brennweite | 6 mm |
| Aufloesung | 3 Megapixel |
| Blendenoeffnung | F1.2 |
| Anschluss | CS-Mount |
| Bildwinkel (Diagonal x Horizontal x Vertikal) | 63 Grad |
| Naheinstellgrenze (M.O.D.) | 0,2 m |
| Hinterer Arbeitsabstand (Back Focal Length) | 7,53 mm |
| Abmessungen | 30 mm (Durchmesser) x 34 mm (Laenge) |
| Gewicht | 53 g |
| Blendenbedienung | Manuell |

### 4.4 Relevanz fuer das AMR-Projekt

- **ArUco-Docking**: Die Kamera erkennt ArUco-Marker an der Ladestation fuer praezises Andocken mittels Visual Servoing (OpenCV, `aruco_docking.py`).
- **Global Shutter**: Eliminiert Rolling-Shutter-Verzerrungen waehrend der Fahrt, was die Zuverlaessigkeit der Marker-Erkennung deutlich verbessert.
- **Brennweite 6 mm**: Bietet ein 63-Grad-Sichtfeld und einen minimalen Arbeitsabstand von 20 cm - geeignet fuer Marker-Erkennung im Nahbereich.
- **Geringe Aufloesung (1,6 MP)**: Bewusst gewaehlt, da geringere Aufloesung schnellere Verarbeitung in Echtzeit ermoeglicht (Machine Vision Anwendung).

---

## 5. Raspberry Pi 5

Der Raspberry Pi 5 dient als High-Level-Steuereinheit des AMR. Er fuehrt den gesamten ROS2-Navigationsstack aus: SLAM Toolbox, Nav2 (Pfadplanung, Lokalisierung, Costmaps), EKF-Sensorfusion und die ArUco-Marker-Erkennung.

![Raspberry Pi 5](../datasheet/images/RASPBERRY%20PI.png)

### 5.1 Prozessor und Speicher

| Parameter | Wert |
|---|---|
| Hersteller | Raspberry Pi Ltd |
| SoC | Broadcom BCM2712 |
| CPU | Quad-Core 64-Bit ARM Cortex-A76 |
| Taktfrequenz | 2,4 GHz |
| CPU-Cache | 512 KB L2 pro Core, 2 MB Shared L3 |
| Kryptographie-Erweiterung | Ja |
| GPU | VideoCore VII, 800 MHz |
| OpenGL | ES 3.1 |
| Vulkan | 1.2 |
| Arbeitsspeicher | LPDDR4X-4267 SDRAM (2 / 4 / 8 / 16 GB) |
| Video-Dekodierung | 4Kp60 HEVC |
| Leistungssteigerung vs. Pi 4 | 2-3x CPU-Performance |

### 5.2 Konnektivitaet

| Schnittstelle | Spezifikation |
|---|---|
| Wi-Fi | Dual-Band 802.11ac (2,4 / 5 GHz) |
| Bluetooth | 5.0 / BLE |
| Ethernet | Gigabit (mit PoE+-Unterstuetzung via HAT) |
| USB 3.0 | 2x (simultane 5 Gbps) |
| USB 2.0 | 2x |
| HDMI | 2x Micro-HDMI (4Kp60, HDR) |
| MIPI CSI/DSI | 2x 4-Lane Transceiver (Kamera/Display) |
| PCIe | 1x PCIe 2.0 x1 (via M.2 HAT) |
| microSD | SDR104 High-Speed |
| GPIO | 40-Pin Standard-Header |
| Stromversorgung | 5 V / 5 A ueber USB-C (Power Delivery) |
| RTC | Ja (externer Batterieanschluss) |
| Power Button | Ja |

### 5.3 RP1 Southbridge (Peripherie-Controller)

Der RP1 ist ein eigenstaendiger Peripherie-Controller, der ueber PCIe 2.0 x4 mit dem BCM2712-Applikationsprozessor verbunden ist. Er stellt die gesamte I/O-Peripherie des Raspberry Pi 5 bereit.

| RP1-Peripherie | Anzahl / Spezifikation |
|---|---|
| ARM-Prozessorkerne | 2x Cortex-M3 (Konfiguration/Management) |
| Shared SRAM | 64 KB |
| USB (XHCI) | 2x Host-Controller (1x USB 3.0 PHY + 1x USB 2.0 PHY) |
| MIPI CSI-2 | 2x Kamera-Controller (mit ISP) |
| MIPI DSI | 2x Display-Controller |
| Ethernet MAC | 1x Gigabit (RGMII) |
| GPIO | 28 Pins (40-Pin-Header) |
| UART | 6x |
| I2C | 7x |
| SPI | 9x (inkl. spi8) |
| PWM | 2x |
| I2S | 3x |
| SDIO | 2x |
| ADC | 12-Bit, 500 kSPS, 4 externe Eingaenge + 1 Temperatursensor |
| DMA | 8-Kanal DMAC |
| PLLs | 3 (2x Fractional-N + 1x Integer) |

### 5.4 Raspberry Pi 5 GPIO-Header (40-Pin)

| Pin | Funktion | Pin | Funktion |
|---|---|---|---|
| 1 | 3,3 V | 2 | 5 V |
| 3 | GPIO2 (I2C SDA) | 4 | 5 V |
| 5 | GPIO3 (I2C SCL) | 6 | GND |
| 7 | GPIO4 | 8 | GPIO14 (UART TX) |
| 9 | GND | 10 | GPIO15 (UART RX) |
| 11 | GPIO17 | 12 | GPIO18 (PCM CLK / PWM0) |
| 13 | GPIO27 | 14 | GND |
| 15 | GPIO22 | 16 | GPIO23 |
| 17 | 3,3 V | 18 | GPIO24 |
| 19 | GPIO10 (SPI MOSI) | 20 | GND |
| 21 | GPIO9 (SPI MISO) | 22 | GPIO25 |
| 23 | GPIO11 (SPI SCLK) | 24 | GPIO8 (SPI CE0) |
| 25 | GND | 26 | GPIO7 (SPI CE1) |
| 27 | GPIO0 (I2C ID EEPROM) | 28 | GPIO1 (I2C ID EEPROM) |
| 29 | GPIO5 | 30 | GND |
| 31 | GPIO6 | 32 | GPIO12 (PWM0) |
| 33 | GPIO13 (PWM1) | 34 | GND |
| 35 | GPIO19 (PCM FS) | 36 | GPIO16 |
| 37 | GPIO26 | 38 | GPIO20 (PCM DIN) |
| 39 | GND | 40 | GPIO21 (PCM DOUT) |

### 5.5 Physische Abmessungen

| Parameter | Wert |
|---|---|
| Boardabmessungen | 85 x 56 mm |
| Befestigungsloecher | 4x (M2,5, Lochabstand 58 x 49 mm) |
| MTBF (Ground Benign) | 93.800 Stunden |
| Produktionsende (min.) | Januar 2036 |

### 5.6 Relevanz fuer das AMR-Projekt

- **ROS2 Navigation Stack**: Fuehrt den vollstaendigen Nav2-Stack aus (AMCL, Regulated Pure Pursuit Controller, Navfn-Planer, Costmaps, Recovery Behaviors).
- **SLAM**: SLAM Toolbox (async) mit Ceres-Solver, 5 cm Kartenaufloesung, Loop Closure.
- **Sensorfusion**: EKF (robot_localization) fusioniert Rad-Odometrie und IMU-Daten.
- **micro-ROS Bridge**: Kommuniziert ueber UART (GPIO14/GPIO15) mit dem ESP32-S3 via micro-ROS.
- **RPLIDAR**: Angeschlossen ueber USB 2.0 fuer LaserScan-Daten.
- **Kamera**: Global Shutter Camera ueber MIPI CSI-2 fuer ArUco-Marker-Erkennung.
- **AI-Erweiterung**: Hailo-8L AI Kit ueber PCIe fuer zukuenftige KI-basierte Objekterkennung.

![Raspberry Pi 5 Bundle](../datasheet/images/Raspi%20Bundle.png)

---

## 6. Zusammenfassung der Kommunikationsarchitektur

Die folgende Tabelle zeigt die Kommunikationsbeziehungen zwischen den Komponenten:

| Verbindung | Schnittstelle | Protokoll | Datenrate / Takt |
|---|---|---|---|
| ESP32-S3 <-> Raspberry Pi 5 | UART (GPIO14/15 Pi, D6/D7 ESP) | micro-ROS Serial Transport | 115200 Baud |
| ESP32-S3 <-> MPU6050 | I2C (D4=SDA, D5=SCL) | I2C Fast Mode | 400 kHz |
| ESP32-S3 <-> Motortreiber MDD3A | GPIO (D0-D3) | PWM / Richtungssignale | 20 kHz PWM |
| ESP32-S3 <-> Encoder | GPIO-Interrupt (D6, D7) | Pulserfassung | -- |
| Raspberry Pi 5 <-> RPLIDAR A1 | USB 2.0 | UART ueber USB-Adapter | Scan-Rate 5,5 Hz |
| Raspberry Pi 5 <-> GS Camera | MIPI CSI-2 | Kamera-Interface | -- |
| Raspberry Pi 5 <-> Hailo-8L | PCIe 2.0 x1 | PCIe | 5 Gbps |

---

*Quelldokumente: esp32-s3_datasheet.pdf (Espressif, v1.6, 2023), SG ESP32-S3 Pinout.pdf (Seeed Studio), MPU6050.pdf (AZ-Delivery / InvenSense), Seeed RPLIDAR A1.pdf (BerryBase / SLAMTEC), Raspberry Pi Global Shutter Camera.pdf (Raspberry Pi Ltd, 2023), objektiv.pdf (PT361060M3MP12), raspberry-pi-5-product-brief.pdf (Raspberry Pi Ltd, 2025), rp1-peripherals.pdf (Raspberry Pi Ltd, 2023)*
