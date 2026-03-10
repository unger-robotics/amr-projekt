# AMR Hardware-Spezifikationen und Anschlussplan

**Leitfrage:** Wie ist die Hardware-Architektur des Autonomous Mobile Robot (AMR) aufgebaut, und wie sind die Kommunikations- sowie Stromversorgungsschnittstellen verschaltet?

Die Kommunikation zwischen dem Raspberry Pi 5, dem ESP32-S3 #1 (Drive-Knoten) und dem ESP32-S3 #2 (Sensor-Knoten) erfolgt ueber USB-CDC. Die skizzierte CAN-Topologie dient der Hardwareplanung und Verdrahtung zur Vorbereitung einer spaeteren Umstellung. Die USB-Verbindung bleibt bis zur finalen Inbetriebnahme der CAN-Software aktiv.

---

### 1 Komponentenuebersicht

Die Hardware-Architektur gliedert sich in zwei funktionale Ebenen:

* **Mikrocontroller-Ebene:** Zwei ESP32-S3 bilden den Fahrkern sowie die Sensor- und Sicherheitsbasis.
* **Host-Ebene:** Ein Raspberry Pi 5 uebernimmt Navigation, Lokalisierung, Kartierung, Bedien- und Leitstandsfunktionen sowie die Verwaltung erweiterter Peripherie.

| Komponente                   | Funktion / Subsystem             | Technische Daten                                                               | Schnittstelle / Bus                     | Quelle |
|------------------------------|----------------------------------|--------------------------------------------------------------------------------|-----------------------------------------|--------|
| **Raspberry Pi 5**           | Host-Ebene                       | ROS 2 Humble in Docker, Debian Trixie, bis **15 W**                            | I2C B, I2S, USB, PCIe, CSI, SPI (CAN)   |        |
| **Seeed XIAO ESP32-S3 #1**   | Fahrkern / Antrieb               | micro-ROS, Regelschleife mit **50 Hz**                                         | PWM, Interrupts, TWAI (CAN), USB-CDC    |        |
| **Seeed XIAO ESP32-S3 #2**   | Sensor- und Sicherheitsbasis     | micro-ROS, Sensorerfassung und Aktorik                                         | I2C A, GPIO, TWAI (CAN), USB-CDC        |        |
| **3S Li-Ion Pack**           | Hauptenergiequelle               | Samsung INR18650-35E 3S1P, **10.8 V** nominal, Dauer **8 A**, maximal **13 A** | DC-Hauptpfad                            |        |
| **BMS 3S 25 A**              | Zellschutz / Balancing           | Ueber- und Unterspannungsschutz, aktuell ungenutzt                             | Zwischen Zellen und Pack-Ausgang        |        |
| **Hauptsicherung 10 A**      | Kurzschlussschutz                | KFZ-Flachsicherung                                                             | DC-Hauptpfad nach BMS                   |        |
| **Hauptschalter**            | System-Ein/Aus                   | Kippschalter                                                                   | DC-Hauptpfad nach Sicherung             |        |
| **Pololu D36V50F6**          | Servoversorgung                  | **12 V** auf **6 V**, maximal **5.5 A**, synchroner Buck-Wandler               | Schraubklemme V+ am PCA9685             |        |
| **INA260**                   | Leistungsmonitor                 | **0 V** bis **36 V**, **+/-15 A**, Shunt **2 mOhm**                            | I2C A (`0x40`) am Sensor-Knoten         |        |
| **IRLZ24N**                  | LED-MOSFET in Low-Side-Schaltung | N-Kanal, V_DS = 55 V, Logic Level                                              | D10 (GPIO9) am Drive-Knoten             |        |
| **Cytron MDD3A**             | Motor-Treiber                    | Dual-H-Bruecke, **4 V** bis **16 V**, **3 A** Dauerstrom                       | PWM D0 bis D3 am Drive-Knoten           |        |
| **JGA25-370 (2x)**           | Antriebsmotoren                  | **12 V** DC, Getriebe **1:34**, Encoder **11 CPR**                             | Encoder D4/D5 und D8/D9 am Drive-Knoten |        |
| **MPU6050 (GY-521)**         | IMU                              | 6-Achsen-MEMS, **+/-250 deg/s**, **+/-2 g**, **50 Hz**                         | I2C A (`0x68`) am Sensor-Knoten         |        |
| **PCA9685**                  | Servo-PWM-Treiber                | 16 Kanaele, 12 Bit, **50 Hz**                                                  | I2C A (`0x41`) am Sensor-Knoten         |        |
| **MG996R (2x)**              | Pan-Tilt-Kamerakopf              | **11 kg*cm** bei **6 V**, Blockierstrom **2.5 A**                              | PWM vom PCA9685, CH0/CH1                |        |
| **HC-SR04**                  | Front-Ultraschall                | Messbereich **2 cm** bis **400 cm**, Stromaufnahme **15 mA**                   | D0/D1 am Sensor-Knoten                  |        |
| **MH-B (YL-63)**             | Kanten-Erkennung                 | Reichweite **2 cm** bis **30 cm**                                              | D2 am Sensor-Knoten                     |        |
| **MCP2515**                  | CAN-Controller der Host-Ebene    | SPI nach CAN, integrierter TJA1050 mit **5 V**                                 | SPI0 am Raspberry Pi 5                  |        |
| **SN65HVD230 (2x)**          | CAN-Transceiver der MCU-Ebene    | Logikpegel **3.3 V**, differenzieller CAN-Bus                                  | D6/D7 an ESP32-S3 #1 und #2             |        |
| **RPLIDAR A1**               | 2D-LiDAR                         | Lokalisierung und Kartierung, Navigation                                       | USB `/dev/ttyUSB0` am Pi 5              |        |
| **IMX296**                   | Global-Shutter-Kamera            | Objekterfassung, CS-Mount **6 mm**                                             | CSI am Raspberry Pi 5                   |        |
| **Hailo-8L**                 | KI-Beschleuniger                 | Objekterkennung, **13 TOPS**                                                   | PCIe Gen 2/3 am Pi 5                    |        |
| **PCM5102A (HifiBerry DAC)** | I2S-Audio-DAC                    | 32-Bit, 384 kHz, 112 dB SNR                                                    | I2S Pins 12/35/40 am Pi 5               |        |
| **ADA3351**                  | Lautsprecher                     | **3 W**, **4 Ohm**, Mono                                                       | Analog vom PCM5102A                     |        |
| **ReSpeaker Mic Array v2.0** | Sprachschnittstelle              | 4 Mikrofone                                                                    | USB am Raspberry Pi 5                   |        |

---

### 2 Raspberry Pi 5

| Ziel-Komponente              | Schnittstelle / Pin | GPIO   | Signal / Bemerkung                                  | Quelle |
|------------------------------|---------------------|--------|-----------------------------------------------------|--------|
| **DC/DC-Wandler**            | USB-C Power         | –      | **5 V** Haupteinspeisung, bis **5 A**               |        |
| **PCM5102A (BCLK)**          | Pin 12              | GPIO18 | I2S Bit-Clock                                       |        |
| **PCM5102A (DIN)**           | Pin 40              | GPIO21 | I2S Daten-Eingang                                   |        |
| **PCM5102A (GND)**           | Pin 6               | –      | gemeinsame Audiomasse                               |        |
| **PCM5102A (LRC)**           | Pin 35              | GPIO19 | I2S Word-Select / Left-Right-Clock                  |        |
| **PCM5102A (VIN)**           | Pin 2               | –      | **5 V** Versorgung des DAC                          |        |
| **Hailo-8L**                 | PCIe (FFC)          | –      | Datenanbindung KI-Beschleuniger, M.2 / PCIe Gen 2/3 |        |
| **ReSpeaker Mic Array v2.0** | USB-A, Port 2       | –      | Audio-Eingabe der Sprachschnittstelle               |        |
| **RPLIDAR A1**               | USB-A, Port 1       | –      | serielle Daten ueber `/dev/ttyUSB0`                 |        |
| **MCP2515-CAN01 (CS)**       | Pin 24              | GPIO8  | SPI0 CE0, Chip Select                               |        |
| **MCP2515-CAN01 (GND)**      | Pin 9               | –      | gemeinsame CAN-Masse                                |        |
| **MCP2515-CAN01 (INT)**      | Pin 22              | GPIO25 | Hardware-Interrupt fuer CAN-Empfang                 |        |
| **MCP2515-CAN01 (SCK)**      | Pin 23              | GPIO11 | SPI0 Serial Clock                                   |        |
| **MCP2515-CAN01 (SI)**       | Pin 19              | GPIO10 | SPI0 MOSI, Daten zum CAN-Modul                      |        |
| **MCP2515-CAN01 (SO)**       | Pin 21              | GPIO9  | SPI0 MISO, Daten zum Host                           |        |
| **MCP2515-CAN01 (VCC)**      | Pin 1               | –      | **3.3 V** Logikspannung fuer SPI-Pegelanpassung     |        |
| **MCP2515-CAN01 (VCC1)**     | Pin 4               | –      | **5 V** Versorgung des CAN-Transceivers             |        |
| **Seeed XIAO ESP32-S3 #1**   | USB-A, Port 3       | –      | USB-CDC-Verbindung zum Drive-Knoten                 |        |
| **Seeed XIAO ESP32-S3 #2**   | USB-A, Port 4       | –      | USB-CDC-Verbindung zum Sensor-Knoten                |        |
| **Sony IMX296**              | CSI (FFC)           | –      | Videodatenstrom der Global-Shutter-Kamera           |        |

#### 2.1 Systemintegration per Device-Tree-Overlay

Das Entwicklerboard des MCP2515 nutzt einen Quarzoszillator mit **16 MHz**. Damit Debian Trixie das Modul korrekt initialisiert und als Netzwerkinterface `can0` bereitstellt, erfordert die Datei `/boot/firmware/config.txt` folgende Konfiguration am Ende:

```ini
# SPI-Bus aktivieren
dtparam=spi=on

# MCP2515 laden: 16 MHz Takt, Interrupt auf GPIO25
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25

```

---

### 3 Seeed XIAO ESP32-S3 #1 (Drive-Knoten)

| Ziel-Komponente      | XIAO-Pin | GPIO   | Richtung | Anschluss / Signal     | Spezifikation / Bemerkung                                | Quelle |
|----------------------|----------|--------|----------|------------------------|----------------------------------------------------------|--------|
| **Cytron MDD3A**     | **D0**   | GPIO1  | OUT      | M1A                    | PWM Motor links A, **20 kHz**                            |        |
| **Cytron MDD3A**     | **D1**   | GPIO2  | OUT      | M1B                    | PWM Motor links B, **20 kHz**                            |        |
| **Cytron MDD3A**     | **D2**   | GPIO3  | OUT      | M2A                    | PWM Motor rechts A, **20 kHz**                           |        |
| **Cytron MDD3A**     | **D3**   | GPIO4  | OUT      | M2B                    | PWM Motor rechts B, **20 kHz**                           |        |
| **IRLZ24N**          | **D10**  | GPIO9  | OUT      | Gate                   | LED-PWM mit **5 kHz**, Gate ueber **100 Ohm** Widerstand |        |
| **JGA25-370 links**  | **D4**   | GPIO5  | IN       | Encoder Phase A, gelb  | interruptfaehig                                          |        |
| **JGA25-370 links**  | **D8**   | GPIO7  | IN       | Encoder Phase B, gruen | Richtungserkennung                                       |        |
| **JGA25-370 rechts** | **D5**   | GPIO6  | IN       | Encoder Phase A, gelb  | interruptfaehig                                          |        |
| **JGA25-370 rechts** | **D9**   | GPIO8  | IN       | Encoder Phase B, gruen | Richtungserkennung                                       |        |
| **SN65HVD230**       | **D6**   | GPIO43 | OUT      | TX                     | TWAI TX, Hardware-UART                                   |        |
| **SN65HVD230**       | **D7**   | GPIO44 | IN       | RX                     | TWAI RX, Hardware-UART                                   |        |

#### 3.1 Spannungsversorgung und Massefuehrung

* **12-V-Hauptpfad:** Der Cytron MDD3A an VB+ und der Pluspol des LED-Streifens werden direkt aus dem **12 V**-Versorgungspfad hinter der Sicherung und dem INA260 gespeist.
* **3.3-V-Logikpfad:** Der SN65HVD230 erfordert eine Versorgung mit **3.3 V** an VCC. Die Speisung erfolgt ueber den 3V3-Ausgang des XIAO ESP32-S3.
* **Massefuehrung:** ESP32-S3, Cytron MDD3A, SN65HVD230, die Source des IRLZ24N und die Encoder-Masse erfordern ein gemeinsames, durchgaengiges GND-Bezugspotenzial fuer stabile Signalpegel.

---

### 4 Seeed XIAO ESP32-S3 #2 (Sensor-Knoten)

| Ziel-Komponente  | XIAO-Pin | GPIO   | Richtung | Anschluss / Signal | Spezifikation / Bemerkung                                                                   | Quelle |
|------------------|----------|--------|----------|--------------------|---------------------------------------------------------------------------------------------|--------|
| **HC-SR04**      | **D0**   | GPIO1  | OUT      | Trigger            | Ultraschall-Trigger, Pulsdauer **10 us**                                                    |        |
| **HC-SR04**      | **D1**   | GPIO2  | IN       | Echo               | Echo-Signal ueber Spannungsteiler (**1 kOhm** und **2 kOhm**) fuer **5 V -> 3.3 V**         |        |
| **I2C-Sensoren** | **D4**   | GPIO5  | I/O      | SDA                | Datenleitung fuer INA260, PCA9685 und MPU6050, Fast-Mode **400 kHz**, Pull-up **2.42 kOhm** |        |
| **I2C-Sensoren** | **D5**   | GPIO6  | I/O      | SCL                | Taktleitung fuer INA260, PCA9685 und MPU6050, Fast-Mode **400 kHz**, Pull-up **2.42 kOhm**  |        |
| **MH-B (YL-63)** | **D2**   | GPIO3  | IN       | OUT                | Kanten-Erkennung, LOW = Boden erkannt                                                       |        |
| **SN65HVD230**   | **D6**   | GPIO43 | OUT      | TX                 | TWAI TX, Hardware-UART                                                                      |        |
| **SN65HVD230**   | **D7**   | GPIO44 | IN       | RX                 | TWAI RX, Hardware-UART                                                                      |        |

Die Pins D3, D8, D9 und D10 bleiben als Reserve unbelegt.

#### 4.1 Spannungsversorgung und Signalpegel

* **5-V-Pfad:** Der HC-SR04 erfordert eine Versorgung mit **5 V**, welche ueber den 5-V-Pin des XIAO erfolgt und die USB-Spannung des Raspberry Pi 5 weiterfuehrt.
* **3.3-V-Pfad:** INA260, die Logik des PCA9685, MPU6050, MH-B und SN65HVD230 arbeiten mit **3.3 V**. Die Versorgung erfolgt ueber den internen LDO am 3V3-Pin des XIAO bei einer Nennlast von bis zu **75 mA**.
* **Trennung der Aktorik:** Die beiden MG996R-Servomotoren sind strikt vom Logikpfad getrennt. Der Pololu D36V50F6 senkt die Batteriespannung auf **6 V** bei maximal **5.5 A** und speist den V+-Anschluss des PCA9685 direkt.

#### 4.2 Pegelanpassung fuer das Echo-Signal des HC-SR04

Der Spannungsteiler besteht aus zwei Widerstaenden (R1 = 1 kOhm und R2 = 2 kOhm). R1 liegt seriell in der Datenleitung, R2 liegt gegen Masse.

Die resultierende Ausgangsspannung errechnet sich durch:

V_out = V_in * (R2 / (R1 + R2)) = 5 V * (2 kOhm / (1 kOhm + 2 kOhm)) = 3.33 V

Dieser Pegel liegt im zulaessigen Bereich des ESP32-S3.

---

### 5 CAN-Topologie und Terminierung

#### 5.1 Host-Ebene: Raspberry Pi 5 <-> MCP2515

| MCP2515-Pin | Anschluss am Pi 5 | Signal / Funktion        | Bemerkung                                  | Quelle |
|-------------|-------------------|--------------------------|--------------------------------------------|--------|
| **VCC1**    | Pin 2 (**5 V**)   | Versorgung Transceiver   | Speist den integrierten CAN-Transceiver    |        |
| **VCC**     | Pin 1 (**3.3 V**) | Logikspannung Controller | Passt die SPI-Pegel an den Raspberry Pi an |        |
| **GND**     | Pin 6 (GND)       | Masse                    | Gemeinsames Bezugspotenzial                |        |
| **CS**      | Pin 24 (GPIO8)    | SPI0 CE0                 | Chip Select                                |        |
| **SI**      | Pin 19 (GPIO10)   | SPI0 MOSI                | Daten zum Modul                            |        |
| **SO**      | Pin 21 (GPIO9)    | SPI0 MISO                | Daten zum Host, direkte Verbindung         |        |
| **SCK**     | Pin 23 (GPIO11)   | SPI0 SCLK                | Taktleitung                                |        |
| **INT**     | Pin 22 (GPIO25)   | Hardware-Interrupt       | Meldet eingehende Nachrichten ohne Polling |        |

Der Jumper fuer den **120 Ohm**-Abschlusswiderstand auf dem MCP2515-Modul ist gesteckt, da der Raspberry Pi 5 ein physisches Ende des Busses bildet.

#### 5.2 Mikrocontroller-Ebene: ESP32-S3 #1 und #2 <-> SN65HVD230

| SN65HVD230-Pin | Anschluss am ESP32-S3 | Signal / Funktion   | Bemerkung                          | Quelle |
|----------------|-----------------------|---------------------|------------------------------------|--------|
| **3V3**        | **3V3**-Pin           | Spannungsversorgung | Direkte Logikspannung des ESP32-S3 |        |
| **GND**        | **GND**-Pin           | Masse               | Gemeinsames Bezugspotenzial        |        |
| **TX**         | **D6** (GPIO43)       | TWAI TX             | Hardware-UART Sendepfad            |        |
| **RX**         | **D7** (GPIO44)       | TWAI RX             | Hardware-UART Empfangspfad         |        |

Am Drive-Knoten in der Mitte des Busses bleibt der Widerstands-Jumper offen. Am Sensor-Knoten am Ende des Busses ist der Jumper gesteckt.

```text
Raspberry Pi 5 (120 Ohm gesteckt) --- ESP32-S3 #1 Drive-Knoten (Jumper offen) --- ESP32-S3 #2 Sensor-Knoten (120 Ohm gesteckt)

```

---

### 6 I2C-Bus A des Sensor-Knotens bei 400 kHz

Der komplette I2C-Bus A wird vom Sensor-Knoten gefuehrt.

| Adresse | Geraet                       | Funktion                    | Pull-up auf dem Board | Quelle |
|---------|------------------------------|-----------------------------|-----------------------|--------|
| `0x40`  | INA260 (Adafruit #4226)      | Leistungsmonitor, High-Side | **10 kOhm** nach VCC  |        |
| `0x41`  | PCA9685 (A0 gebrueckt)       | Servo-PWM, 16 Kanaele       | **10 kOhm** nach VCC  |        |
| `0x68`  | MPU6050 / GY-521 (AD0 = GND) | IMU, 6 Achsen               | **4.7 kOhm** nach VCC |        |

Die Parallelschaltung erzeugt einen resultierenden Pull-up von **10 kOhm || 10 kOhm || 4.7 kOhm = 2.42 kOhm**. Die internen Pull-ups des ESP32 bleiben deaktiviert.

---

### 7 Spannungs- und Datenarchitektur

```text
3x Samsung INR18650-35E, 12-V-Batteriepfad
    │
    └── Hauptsicherung 10 A
        │
        └── Hauptschalter
            │
            └── INA260 (High-Side-Monitoring)
                │
                ├── Cytron MDD3A ─ 2x JGA25-370
                │
                ├── Pololu D36V50F6 ─ 12 V / 6 V bei 5,5 A ─ PCA9685 ─ 2x MG996R
                │
                ├── DC/DC 12 V / 5 V bei 5 A mit USB-C ─ Raspberry Pi 5
                │      ├── Hailo-8L (PCIe)
                │      ├── RPLIDAR A1 (USB)
                │      ├── ReSpeaker Mic Array v2.0 (USB)
                │      ├── IMX296 (CSI)
                │      ├── PCM5102A HifiBerry DAC (I2S) ─ ADA3351
                │      ├── MCP2515 CAN-Modul (SPI0)
                │      │    │
                │      │    └── CAN-Bus (CANH / CANL)
                │      │         ├── SN65HVD230 ─ ESP32-S3 #1 Drive-Knoten
                │      │         └── SN65HVD230 ─ ESP32-S3 #2 Sensor-Knoten
                │      │
                │      ├── ESP32-S3 #2 ueber USB-CDC fuer micro-ROS
                │      │    ├── I2C: INA260, PCA9685, MPU6050
                │      │    ├── HC-SR04 mit 5 V
                │      │    └── MH-B mit 3,3 V
                │      │
                │      └── ESP32-S3 #1 ueber USB-CDC fuer micro-ROS
                │           ├── PWM: MDD3A an D0 bis D3
                │           ├── Encoder: JGA25-370 an D4, D5, D8, D9
                │           └── LED-PWM: IRLZ24N an D10
                │
                └── LED-Streifen mit 12 V ─ IRLZ24N an D10

```

---

### 8 Analyse des I2C-Pull-ups von 2.42 kOhm bei 400 kHz Fast-Mode

Ziel ist die Pruefung, ob die Hardware am Sensor-Knoten den I2C-Fast-Mode mit **400 kHz** zuverlaessig einhaelt.

#### Daten: Herleitung des effektiven Widerstands

Der effektive Pull-up-Widerstand ergibt sich durch die Parallelschaltung der fest bestueckten SMD-Widerstaende auf den drei Breakout-Boards:

R_eff = (1/10000 Ohm + 1/10000 Ohm + 1/4700 Ohm)^(-1) = 2.42 kOhm

#### Regel 1: Pruefung der Senkenstromgrenze

Der I2C-Treiber zieht die Leitung auf Masse. Fuer den Low-Pegel gilt V_OL <= 0.4 V bei maximal I_OL = 3 mA.

R_min = (3.3 V - 0.4 V) / 0.003 A = 1.0 kOhm

**Schluss 1:** Der Pull-up von **2.42 kOhm** liegt ueber der Untergrenze von **1.0 kOhm**. Es resultiert ein Strom von ca. **1.2 mA**. Der Bus arbeitet innerhalb des zulaessigen Bereichs.

#### Regel 2: Pruefung der Anstiegszeit

Die Anstiegszeit im I2C-Fast-Mode ist auf maximal **300 ns** limitiert. Bei einer geschaetzten parasitaeren Buskapazitaet von **75 pF** folgt:

t_r = 0.8473 * 2420 Ohm * 75 * 10^-12 F = 154 ns

**Schluss 2:** Die Anstiegszeit von **154 ns** unterschreitet die Grenze von **300 ns**.

#### Konsequenz / Fazit

Der Widerstand von **2.42 kOhm** garantiert auf dem kurzen I2C-Bus des Sensor-Knotens den sicheren Betrieb bei **400 kHz**, da Senkenstrom und Flankensteilheit die Spezifikation des Fast-Modes erfuellen.
