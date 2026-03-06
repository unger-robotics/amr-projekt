### AMR Hardware-Spezifikationen und Anschlussplan

**Leitfrage:** Wie ist die Hardware-Architektur des Autonomous Mobile Robot (AMR) aufgebaut, und wie sind die Kommunikations- sowie Stromversorgungsschnittstellen verschaltet?

Die Kommunikation zwischen dem Raspberry Pi 5, dem ESP32-S3 #1 (Drive-Knoten) und dem ESP32-S3 #2 (Sensor-Knoten) erfolgt über USB-CDC. Die skizzierte CAN-Topologie dient der Hardwareplanung und Verdrahtung zur Vorbereitung einer späteren Umstellung. Die USB-Verbindung bleibt bis zur finalen Inbetriebnahme der CAN-Software aktiv.

---

### 1 Komponentenübersicht

Die Hardware-Architektur gliedert sich in zwei funktionale Ebenen:

* **Mikrocontroller-Ebene:** Zwei ESP32-S3 bilden den Fahrkern sowie die Sensor- und Sicherheitsbasis.
* **Host-Ebene:** Ein Raspberry Pi 5 übernimmt Navigation, Lokalisierung, Kartierung, Bedien- und Leitstandsfunktionen sowie die Verwaltung erweiterter Peripherie.

| Komponente                   | Funktion / Subsystem             | Technische Daten                                                               | Schnittstelle / Bus                     | Quelle |
|------------------------------|----------------------------------|--------------------------------------------------------------------------------|-----------------------------------------|--------|
| **Raspberry Pi 5**           | Host-Ebene                       | ROS 2 Humble in Docker, Debian Trixie, bis **15 W**                            | I²C B, I2S, USB, PCIe, CSI, SPI (CAN)   |        |
| **Seeed XIAO ESP32-S3 #1**   | Fahrkern / Antrieb               | micro-ROS, Regelschleife mit **50 Hz**                                         | PWM, Interrupts, TWAI (CAN), USB-CDC    |        |
| **Seeed XIAO ESP32-S3 #2**   | Sensor- und Sicherheitsbasis     | micro-ROS, Sensorerfassung und Aktorik                                         | I²C A, GPIO, TWAI (CAN), USB-CDC        |        |
| **3S Li-Ion Pack**           | Hauptenergiequelle               | Samsung INR18650-35E 3S1P, **10.8 V** nominal, Dauer **8 A**, maximal **13 A** | DC-Hauptpfad                            |        |
| **BMS 3S 25 A**              | Zellschutz / Balancing           | Über- und Unterspannungsschutz, aktuell ungenutzt                              | Zwischen Zellen und Pack-Ausgang        |        |
| **Hauptsicherung 10 A**      | Kurzschlussschutz                | KFZ-Flachsicherung                                                             | DC-Hauptpfad nach BMS                   |        |
| **Hauptschalter**            | System-Ein/Aus                   | Kippschalter                                                                   | DC-Hauptpfad nach Sicherung             |        |
| **Pololu D36V50F6**          | Servoversorgung                  | **12 V** auf **6 V**, maximal **5.5 A**, synchroner Buck-Wandler               | Schraubklemme V+ am PCA9685             |        |
| **INA260**                   | Leistungsmonitor                 | **0 V** bis **36 V**, **±15 A**, Shunt **2 mΩ**                                | I²C A (`0x40`) am Sensor-Knoten         |        |
| **IRLZ24N**                  | LED-MOSFET in Low-Side-Schaltung | N-Kanal, $V_{DS} = 55\text{ V}$, Logic Level                                   | D10 (GPIO9) am Drive-Knoten             |        |
| **Cytron MDD3A**             | Motor-Treiber                    | Dual-H-Brücke, **4 V** bis **16 V**, **3 A** Dauerstrom                        | PWM D0 bis D3 am Drive-Knoten           |        |
| **JGA25-370 (2×)**           | Antriebsmotoren                  | **12 V** DC, Getriebe **1:34**, Encoder **11 CPR**                             | Encoder D4/D5 und D8/D9 am Drive-Knoten |        |
| **MPU6050 (GY-521)**         | IMU                              | 6-Achsen-MEMS, **±500°/s**, **±2 g**, **50 Hz**                                | I²C A (`0x68`) am Sensor-Knoten         |        |
| **PCA9685**                  | Servo-PWM-Treiber                | 16 Kanäle, 12 Bit, **50 Hz**                                                   | I²C A (`0x41`) am Sensor-Knoten         |        |
| **MG996R (2×)**              | Pan-Tilt-Kamerakopf              | **11 kg·cm** bei **6 V**, Blockierstrom **2.5 A**                              | PWM vom PCA9685, CH0/CH1                |        |
| **HC-SR04**                  | Front-Ultraschall                | Messbereich **2 cm** bis **400 cm**, Stromaufnahme **15 mA**                   | D0/D1 am Sensor-Knoten                  |        |
| **MH-B (YL-63)**             | Kanten-Erkennung                 | Reichweite **2 cm** bis **30 cm**                                              | D2 am Sensor-Knoten                     |        |
| **MCP2515**                  | CAN-Controller der Host-Ebene    | SPI nach CAN, integrierter TJA1050 mit **5 V**                                 | SPI0 am Raspberry Pi 5                  |        |
| **SN65HVD230 (2×)**          | CAN-Transceiver der MCU-Ebene    | Logikpegel **3.3 V**, differenzieller CAN-Bus                                  | D6/D7 an ESP32-S3 #1 und #2             |        |
| **RPLIDAR A1**               | 2D-LiDAR                         | Lokalisierung und Kartierung, Navigation                                       | USB `/dev/ttyUSB0` am Pi 5              |        |
| **IMX296**                   | Global-Shutter-Kamera            | Objekterfassung, CS-Mount **6 mm**                                             | CSI am Raspberry Pi 5                   |        |
| **Hailo-8L**                 | KI-Beschleuniger                 | Objekterkennung, **13 TOPS**                                                   | PCIe Gen 2/3 am Pi 5                    |        |
| **MAX98357A**                | I2S-Audioverstärker              | Class-D, **3.2 W** an **4 Ω**, Gain **9 dB**                                   | I2S Pins 12/35/40 am Pi 5               |        |
| **ADA3351**                  | Lautsprecher                     | **3 W**, **4 Ω**, Mono                                                         | Analog vom MAX98357A                    |        |
| **ReSpeaker Mic Array v2.0** | Sprachschnittstelle              | 4 Mikrofone                                                                    | USB am Raspberry Pi 5                   |        |

---

### 2 Raspberry Pi 5

| Ziel-Komponente              | Schnittstelle / Pin | GPIO   | Signal / Bemerkung                                  | Quelle |
|------------------------------|---------------------|--------|-----------------------------------------------------|--------|
| **DC/DC-Wandler**            | USB-C Power         | –      | **5 V** Haupteinspeisung, bis **5 A**               |        |
| **MAX98357A (BCLK)**         | Pin 12              | GPIO18 | I2S Bit-Clock                                       |        |
| **MAX98357A (DIN)**          | Pin 40              | GPIO21 | I2S Daten-Eingang                                   |        |
| **MAX98357A (GND)**          | Pin 6               | –      | gemeinsame Audiomasse                               |        |
| **MAX98357A (LRC)**          | Pin 35              | GPIO19 | I2S Word-Select / Left-Right-Clock                  |        |
| **MAX98357A (VIN)**          | Pin 2               | –      | **5 V** Versorgung des Audioverstärkers             |        |
| **Hailo-8L**                 | PCIe (FFC)          | –      | Datenanbindung KI-Beschleuniger, M.2 / PCIe Gen 2/3 |        |
| **ReSpeaker Mic Array v2.0** | USB-A, Port 2       | –      | Audio-Eingabe der Sprachschnittstelle               |        |
| **RPLIDAR A1**               | USB-A, Port 1       | –      | serielle Daten über `/dev/ttyUSB0`                  |        |
| **MCP2515-CAN01 (CS)**       | Pin 24              | GPIO8  | SPI0 CE0, Chip Select                               |        |
| **MCP2515-CAN01 (GND)**      | Pin 9               | –      | gemeinsame CAN-Masse                                |        |
| **MCP2515-CAN01 (INT)**      | Pin 22              | GPIO25 | Hardware-Interrupt für CAN-Empfang                  |        |
| **MCP2515-CAN01 (SCK)**      | Pin 23              | GPIO11 | SPI0 Serial Clock                                   |        |
| **MCP2515-CAN01 (SI)**       | Pin 19              | GPIO10 | SPI0 MOSI, Daten zum CAN-Modul                      |        |
| **MCP2515-CAN01 (SO)**       | Pin 21              | GPIO9  | SPI0 MISO, Daten zum Host                           |        |
| **MCP2515-CAN01 (VCC)**      | Pin 1               | –      | **3.3 V** Logikspannung für SPI-Pegelanpassung      |        |
| **MCP2515-CAN01 (VCC1)**     | Pin 4               | –      | **5 V** Versorgung des CAN-Transceivers             |        |
| **Seeed XIAO ESP32-S3 #1**   | USB-A, Port 3       | –      | USB-CDC-Verbindung zum Drive-Knoten                 |        |
| **Seeed XIAO ESP32-S3 #2**   | USB-A, Port 4       | –      | USB-CDC-Verbindung zum Sensor-Knoten                |        |
| **Sony IMX296**              | CSI (FFC)           | –      | Videodatenstrom der Global-Shutter-Kamera           |        |

Pin 2 am MAX98357A ist zusätzlich mit dem SD-Pin des Verstärkers verbunden, wodurch der Shutdown-Modus dauerhaft deaktiviert wird.

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

| Ziel-Komponente      | XIAO-Pin | GPIO   | Richtung | Anschluss / Signal    | Spezifikation / Bemerkung                             | Quelle |
|----------------------|----------|--------|----------|-----------------------|-------------------------------------------------------|--------|
| **Cytron MDD3A**     | **D0**   | GPIO1  | OUT      | M1A                   | PWM Motor links A, **20 kHz**                         |        |
| **Cytron MDD3A**     | **D1**   | GPIO2  | OUT      | M1B                   | PWM Motor links B, **20 kHz**                         |        |
| **Cytron MDD3A**     | **D2**   | GPIO3  | OUT      | M2A                   | PWM Motor rechts A, **20 kHz**                        |        |
| **Cytron MDD3A**     | **D3**   | GPIO4  | OUT      | M2B                   | PWM Motor rechts B, **20 kHz**                        |        |
| **IRLZ24N**          | **D10**  | GPIO9  | OUT      | Gate                  | LED-PWM mit **5 kHz**, Gate über **100 Ω** Widerstand |        |
| **JGA25-370 links**  | **D4**   | GPIO5  | IN       | Encoder Phase A, gelb | interruptfähig                                        |        |
| **JGA25-370 links**  | **D8**   | GPIO7  | IN       | Encoder Phase B, grün | Richtungserkennung                                    |        |
| **JGA25-370 rechts** | **D5**   | GPIO6  | IN       | Encoder Phase A, gelb | interruptfähig                                        |        |
| **JGA25-370 rechts** | **D9**   | GPIO8  | IN       | Encoder Phase B, grün | Richtungserkennung                                    |        |
| **SN65HVD230**       | **D6**   | GPIO43 | OUT      | TX                    | TWAI TX, Hardware-UART                                |        |
| **SN65HVD230**       | **D7**   | GPIO44 | IN       | RX                    | TWAI RX, Hardware-UART                                |        |

#### 3.1 Spannungsversorgung und Masseführung

* **12-V-Hauptpfad:** Der Cytron MDD3A an VB+ und der Pluspol des LED-Streifens werden direkt aus dem **12 V**-Versorgungspfad hinter der Sicherung und dem INA260 gespeist.
* **3.3-V-Logikpfad:** Der SN65HVD230 erfordert eine Versorgung mit **3.3 V** an VCC. Die Speisung erfolgt über den 3V3-Ausgang des XIAO ESP32-S3.
* **Masseführung:** ESP32-S3, Cytron MDD3A, SN65HVD230, die Source des IRLZ24N und die Encoder-Masse erfordern ein gemeinsames, durchgängiges GND-Bezugspotenzial für stabile Signalpegel.

---

### 4 Seeed XIAO ESP32-S3 #2 (Sensor-Knoten)

| Ziel-Komponente  | XIAO-Pin | GPIO   | Richtung | Anschluss / Signal | Spezifikation / Bemerkung                                                                | Quelle |
|------------------|----------|--------|----------|--------------------|------------------------------------------------------------------------------------------|--------|
| **HC-SR04**      | **D0**   | GPIO1  | OUT      | Trigger            | Ultraschall-Trigger, Pulsdauer **10 µs**                                                 |        |
| **HC-SR04**      | **D1**   | GPIO2  | IN       | Echo               | Echo-Signal über Spannungsteiler (**1 kΩ** und **2 kΩ**) für **5 V → 3.3 V**             |        |
| **I²C-Sensoren** | **D4**   | GPIO5  | I/O      | SDA                | Datenleitung für INA260, PCA9685 und MPU6050, Fast-Mode **400 kHz**, Pull-up **2.42 kΩ** |        |
| **I²C-Sensoren** | **D5**   | GPIO6  | I/O      | SCL                | Taktleitung für INA260, PCA9685 und MPU6050, Fast-Mode **400 kHz**, Pull-up **2.42 kΩ**  |        |
| **MH-B (YL-63)** | **D2**   | GPIO3  | IN       | OUT                | Kanten-Erkennung, LOW = Boden erkannt                                                    |        |
| **SN65HVD230**   | **D6**   | GPIO43 | OUT      | TX                 | TWAI TX, Hardware-UART                                                                   |        |
| **SN65HVD230**   | **D7**   | GPIO44 | IN       | RX                 | TWAI RX, Hardware-UART                                                                   |        |

Die Pins D3, D8, D9 und D10 bleiben als Reserve unbelegt.

#### 4.1 Spannungsversorgung und Signalpegel

* **5-V-Pfad:** Der HC-SR04 erfordert eine Versorgung mit **5 V**, welche über den 5-V-Pin des XIAO erfolgt und die USB-Spannung des Raspberry Pi 5 weiterführt.
* **3.3-V-Pfad:** INA260, die Logik des PCA9685, MPU6050, MH-B und SN65HVD230 arbeiten mit **3.3 V**. Die Versorgung erfolgt über den internen LDO am 3V3-Pin des XIAO bei einer Nennlast von bis zu **75 mA**.
* **Trennung der Aktorik:** Die beiden MG996R-Servomotoren sind strikt vom Logikpfad getrennt. Der Pololu D36V50F6 senkt die Batteriespannung auf **6 V** bei maximal **5.5 A** und speist den V+-Anschluss des PCA9685 direkt.

#### 4.2 Pegelanpassung für das Echo-Signal des HC-SR04

Der Spannungsteiler besteht aus zwei Widerständen ($R_1 = 1\text{ k}\Omega$ und $R_2 = 2\text{ k}\Omega$). $R_1$ liegt seriell in der Datenleitung, $R_2$ liegt gegen Masse.

Die resultierende Ausgangsspannung errechnet sich durch:


$$V_\mathrm{out} = V_\mathrm{in} \cdot \frac{R_2}{R_1 + R_2} = 5\mathrm{V} \cdot \frac{2\mathrm{k\Omega}}{1\mathrm{k\Omega} + 2\mathrm{k\Omega}} \approx 3.33\mathrm{V}$$

Dieser Pegel liegt im zulässigen Bereich des ESP32-S3.

---

### 5 CAN-Topologie und Terminierung

#### 5.1 Host-Ebene: Raspberry Pi 5 ↔ MCP2515

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

Der Jumper für den **120 Ω**-Abschlusswiderstand auf dem MCP2515-Modul ist gesteckt, da der Raspberry Pi 5 ein physisches Ende des Busses bildet.

#### 5.2 Mikrocontroller-Ebene: ESP32-S3 #1 und #2 ↔ SN65HVD230

| SN65HVD230-Pin | Anschluss am ESP32-S3 | Signal / Funktion   | Bemerkung                          | Quelle |
|----------------|-----------------------|---------------------|------------------------------------|--------|
| **3V3**        | **3V3**-Pin           | Spannungsversorgung | Direkte Logikspannung des ESP32-S3 |        |
| **GND**        | **GND**-Pin           | Masse               | Gemeinsames Bezugspotenzial        |        |
| **TX**         | **D6** (GPIO43)       | TWAI TX             | Hardware-UART Sendepfad            |        |
| **RX**         | **D7** (GPIO44)       | TWAI RX             | Hardware-UART Empfangspfad         |        |

Am Drive-Knoten in der Mitte des Busses bleibt der Widerstands-Jumper offen. Am Sensor-Knoten am Ende des Busses ist der Jumper gesteckt.

```text
Raspberry Pi 5 (120 Ω gesteckt) ─── ESP32-S3 #1 Drive-Knoten (Jumper offen) ─── ESP32-S3 #2 Sensor-Knoten (120 Ω gesteckt)

```

---

### 6 I²C-Bus A des Sensor-Knotens bei 400 kHz

Der komplette I²C-Bus A wird vom Sensor-Knoten geführt.

| Adresse | Gerät                        | Funktion                    | Pull-up auf dem Board | Quelle |
|---------|------------------------------|-----------------------------|-----------------------|--------|
| `0x40`  | INA260 (Adafruit #4226)      | Leistungsmonitor, High-Side | **10 kΩ** nach VCC    |        |
| `0x41`  | PCA9685 (A0 gebrückt)        | Servo-PWM, 16 Kanäle        | **10 kΩ** nach VCC    |        |
| `0x68`  | MPU6050 / GY-521 (AD0 = GND) | IMU, 6 Achsen               | **4.7 kΩ** nach VCC   |        |

Die Parallelschaltung erzeugt einen resultierenden Pull-up von **10 kΩ || 10 kΩ || 4.7 kΩ ≈ 2.42 kΩ**. Die internen Pull-ups des ESP32 bleiben deaktiviert.

---

### 7 Spannungs- und Datenarchitektur

```text
3× Samsung INR18650-35E, 12-V-Batteriepfad
    │
    └── Hauptsicherung 10 A
        │
        └── Hauptschalter
            │
            └── INA260 (High-Side-Monitoring)
                │
                ├── Cytron MDD3A ─ 2× JGA25-370
                │
                ├── Pololu D36V50F6 ─ 12 V / 6 V bei 5,5 A ─ PCA9685 ─ 2× MG996R
                │
                ├── DC/DC 12 V / 5 V bei 5 A mit USB-C ─ Raspberry Pi 5
                │      ├── Hailo-8L (PCIe)
                │      ├── RPLIDAR A1 (USB)
                │      ├── ReSpeaker Mic Array v2.0 (USB)
                │      ├── IMX296 (CSI)
                │      ├── MAX98357A (I2S) ─ ADA3351
                │      ├── MCP2515 CAN-Modul (SPI0)
                │      │    │
                │      │    └── CAN-Bus (CANH / CANL)
                │      │         ├── SN65HVD230 ─ ESP32-S3 #1 Drive-Knoten
                │      │         └── SN65HVD230 ─ ESP32-S3 #2 Sensor-Knoten
                │      │
                │      ├── ESP32-S3 #2 über USB-CDC für micro-ROS
                │      │    ├── I²C: INA260, PCA9685, MPU6050
                │      │    ├── HC-SR04 mit 5 V
                │      │    └── MH-B mit 3,3 V
                │      │
                │      └── ESP32-S3 #1 über USB-CDC für micro-ROS
                │           ├── PWM: MDD3A an D0 bis D3
                │           ├── Encoder: JGA25-370 an D4, D5, D8, D9
                │           └── LED-PWM: IRLZ24N an D10
                │
                └── LED-Streifen mit 12 V ─ IRLZ24N an D10

```

---

### 8 Analyse des I²C-Pull-ups von 2.42 kΩ bei 400 kHz Fast-Mode

Ziel ist die Prüfung, ob die Hardware am Sensor-Knoten den I²C-Fast-Mode mit **400 kHz** zuverlässig einhält.

#### Daten: Herleitung des effektiven Widerstands

Der effektive Pull-up-Widerstand ergibt sich durch die Parallelschaltung der fest bestückten SMD-Widerstände auf den drei Breakout-Boards:


$$R_\mathrm{eff} = \left( \frac{1}{10000\Omega} + \frac{1}{10000\Omega} + \frac{1}{4700\Omega} \right)^{-1} \approx 2.42\mathrm{k\Omega}$$

#### Regel 1: Prüfung der Senkenstromgrenze

Der I²C-Treiber zieht die Leitung auf Masse. Für den Low-Pegel gilt $V_\mathrm{OL} \leq 0.4\text{ V}$ bei maximal $I_\mathrm{OL} = 3\text{ mA}$.


$$R_\mathrm{min} = \frac{3.3\mathrm{V} - 0.4\mathrm{V}}{0.003\mathrm{A}} \approx 1.0\mathrm{k\Omega}$$

**Schluss 1:** Der Pull-up von **2.42 kΩ** liegt über der Untergrenze von **1.0 kΩ**. Es resultiert ein Strom von ca. **1.2 mA**. Der Bus arbeitet innerhalb des zulässigen Bereichs.

#### Regel 2: Prüfung der Anstiegszeit

Die Anstiegszeit im I²C-Fast-Mode ist auf maximal **300 ns** limitiert. Bei einer geschätzten parasitären Buskapazität von **75 pF** folgt:


$$t_r = 0.8473 \cdot 2420\Omega \cdot 75 \cdot 10^{-12}\mathrm{F} \approx 154\mathrm{ns}$$

**Schluss 2:** Die Anstiegszeit von **154 ns** unterschreitet die Grenze von **300 ns**.

#### Konsequenz / Fazit

Der Widerstand von **2.42 kΩ** garantiert auf dem kurzen I²C-Bus des Sensor-Knotens den sicheren Betrieb bei **400 kHz**, da Senkenstrom und Flankensteilheit die Spezifikation des Fast-Modes erfüllen.
