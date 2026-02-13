# Umsetzungsanleitung: AMR Inbetriebnahme

## Dokumentinformationen

| Eigenschaft | Wert                                                               |
|-------------|--------------------------------------------------------------------|
| Projekt     | Autonomer Mobiler Roboter (AMR) fuer Intralogistik                 |
| Version     | 1.0                                                                |
| Datum       | 2026-02                                                            |
| Bezug       | V-Modell Validierungsplan (`hardware/docs/08_validierungsplan.md`) |

Diese Anleitung beschreibt die schrittweise Inbetriebnahme des AMR-Prototyps vom ersten Firmware-Upload bis zur vollstaendigen Navigationsvalidierung. Der Aufbau folgt dem V-Modell-Phasenplan und gliedert sich in vier Teile: Teil 1 behandelt die ESP32-S3 Firmware (Phasen 1-3, Kompilierung, Encoder- und Motor-Validierung), Teil 2 die ROS2-Umgebung auf dem Raspberry Pi 5, Teil 3 die Integration beider Subsysteme ueber micro-ROS, und Teil 4 die Kalibrierung und Systemvalidierung. Jede Phase baut auf der vorhergehenden auf -- ein Ueberspringen einzelner Schritte ist nicht vorgesehen, da spaetere Phasen auf korrekt validierte Vorstufen angewiesen sind.

---

## Teil 1: ESP32-S3 Firmware (Phasen 1-3)

### 1.1 Voraussetzungen und Werkzeuge

Bevor die Firmware auf den XIAO ESP32-S3 uebertragen werden kann, muessen die folgenden Werkzeuge und Hardware-Komponenten bereitstehen.

**Software-Voraussetzungen:**

PlatformIO ist das zentrale Build-System fuer die ESP32-Firmware. Es kann entweder als CLI-Tool oder als VSCode-Extension installiert werden. Die CLI-Variante eignet sich besonders fuer den Einsatz auf dem Raspberry Pi, waehrend die VSCode-Extension auf dem Entwicklungsrechner eine komfortablere Arbeitsumgebung bietet.

```bash
# PlatformIO CLI installieren (falls nicht vorhanden)
pip install platformio

# Version pruefen
pio --version
```

**Hardware-Voraussetzungen:**

Die folgende Hardware muss vor dem ersten Firmware-Upload physisch aufgebaut und verkabelt sein. Eine detaillierte Verdrahtungsanleitung findet sich in `hardware/hardware-setup.md`.

- **Seeed Studio XIAO ESP32-S3**: Der Mikrocontroller bildet die Low-Level-Steuerungseinheit. Er muss ueber ein USB-C-Datenkabel (nicht nur Ladekabel) mit dem Entwicklungsrechner oder dem Raspberry Pi verbunden sein.
- **Cytron MDD3A Motortreiber**: Der Dual-Motor-Treiber arbeitet im Dual-PWM-Modus. Er benoetigt eine 12-V-Versorgung ueber die Schraubklemmen VB+/VB- und muss mit vier Signalleitungen (D0-D3) an den XIAO angeschlossen sein.
- **JGA25-370 Motoren mit Hall-Encoder (2x)**: Die Motoren verfuegen jeweils ueber einen Hall-Encoder mit Phase A und Phase B. Im aktuellen Design wird nur Phase A verwendet (A-only-Betrieb), Phase B bleibt isoliert. Die Encoder-Signalleitungen (gelb) muessen an D6 (links) und D7 (rechts) angeschlossen sein.
- **3S1P Lithium-Ionen Samsung INR18650-35E 3500 mAh 8A Akkupack**: Akku Ladeschlussspannung 12,6 V und Entladeschlussspannung 7,95 V (Bereich 10,8 - 11,1 V) und versorgt ueber einen Buck-Converter den Raspberry Pi mit 5 V sowie den Motortreiber direkt mit 12 V.
- **USB-C-Datenkabel**: Wichtig ist, dass das Kabel Datenleitungen besitzt. Reine Ladekabel (2-adrig) koennen den ESP32 zwar mit Strom versorgen, erlauben aber keinen Firmware-Upload und keine serielle Kommunikation.

**Hardware-Checkliste (Kurzfassung):**

Vor dem Fortfahren sollte die interaktive Hardware-Checkliste `pre_flight_check.py` durchgefuehrt werden (siehe Abschnitt 1.5). Die wichtigsten Pruefpunkte vorab:

- MDD3A Power-LED leuchtet (12 V anliegt)
- ESP32-S3 enumeriert am Rechner als `/dev/ttyACM*` (Linux/macOS) bzw. als COM-Port (Windows)
- Sternpunkt-Masse: Pi-GND, Buck-GND, MDD3A-GND und ESP32-GND sind verbunden
- Encoder-VCC und -GND korrekt angeschlossen (3,3 V vom ESP32 oder 5 V mit Pegelanpassung)

### 1.2 PlatformIO-Projekt konfigurieren

Das PlatformIO-Projekt befindet sich im Verzeichnis `amr/esp32_amr_firmware/`. Die zentrale Konfigurationsdatei `platformio.ini` definiert Board, Framework, Build-Flags und Abhaengigkeiten.

**Verzeichnisstruktur:**

```text
amr/esp32_amr_firmware/
  platformio.ini              # Build-Konfiguration
  src/
    main.cpp                  # FreeRTOS-Tasks, micro-ROS, Safety
    robot_hal.hpp             # Hardware-Abstraktion (GPIO, Encoder, PWM)
    pid_controller.hpp        # PID-Regler mit Anti-Windup
    diff_drive_kinematics.hpp # Vorwaerts-/Inverskinematik

hardware/
  config.h                    # Zentrale Parameter (Single Source of Truth)
```

**platformio.ini im Detail:**

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
framework = arduino
monitor_speed = 115200
upload_speed = 921600

build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1
    -I../../hardware

; micro-ROS Konfiguration
board_microros_transport = serial
board_microros_distro = humble

lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio
```

Die einzelnen Konfigurationsparameter haben folgende Bedeutung:

- `board = seeed_xiao_esp32s3`: Definiert die Zielplattform als Seeed Studio XIAO ESP32-S3 mit Dual-Core LX7 Prozessor bei 240 MHz.
- `framework = arduino`: Verwendet das Arduino-Framework, das die ESP-IDF-Funktionalitaet ueber eine vereinfachte API bereitstellt.
- `monitor_speed = 115200`: Baudrate fuer den seriellen Monitor. Diese Einstellung ist relevant fuer die Diagnose, obwohl der serielle Port im Normalbetrieb von micro-ROS belegt wird (siehe Abschnitt 1.4).
- `upload_speed = 921600`: Maximale Upload-Geschwindigkeit fuer den Firmware-Flash. Bei Problemen kann dieser Wert auf 460800 oder 115200 reduziert werden.
- `-DARDUINO_USB_CDC_ON_BOOT=1`: Aktiviert die USB-CDC-Schnittstelle (Communication Device Class) beim Boot. Dies ist zwingend erforderlich, damit der ESP32-S3 als serielles Geraet erkannt wird, da er im Gegensatz zu aelteren ESP32-Varianten keinen separaten USB-UART-Chip besitzt.
- `-I../../hardware`: Fuegt das `hardware/`-Verzeichnis zum Include-Pfad hinzu, damit `config.h` als `#include "config.h"` referenziert werden kann. Dieser relative Pfad bezieht sich auf das `src/`-Verzeichnis.
- `board_microros_transport = serial`: Konfiguriert micro-ROS fuer den seriellen Transport (UART ueber USB-CDC).
- `board_microros_distro = humble`: Legt die ROS2-Distribution auf Humble Hawksbill fest, passend zum ROS2-Stack auf dem Raspberry Pi.
- `lib_deps`: Bindet die micro-ROS-Bibliothek fuer PlatformIO ein. Beim ersten Build wird diese automatisch heruntergeladen und kompiliert, was mehrere Minuten dauern kann.

### 1.3 Firmware kompilieren und flashen (Phase 1)

Der erste Schritt der Inbetriebnahme ist die erfolgreiche Kompilierung und der Upload der Firmware auf den XIAO ESP32-S3. Dieser Vorgang validiert gleichzeitig die korrekte PlatformIO-Installation, die Build-Konfiguration und die USB-Verbindung.

**Firmware kompilieren:**

```bash
cd amr/esp32_amr_firmware/
pio run
```

Beim ersten Durchlauf laedt PlatformIO die ESP32-S3-Toolchain und die micro-ROS-Bibliothek herunter. Dieser Vorgang dauert je nach Internetverbindung 5-15 Minuten. Nachfolgende Builds sind deutlich schneller (typisch 15-30 Sekunden).

**Erwartete Ausgabe bei Erfolg:**

```text
Processing seeed_xiao_esp32s3 (platform: espressif32; board: seeed_xiao_esp32s3; framework: arduino)
...
Compiling .pio/build/seeed_xiao_esp32s3/src/main.cpp.o
...
Linking .pio/build/seeed_xiao_esp32s3/firmware.elf
Building .pio/build/seeed_xiao_esp32s3/firmware.bin
...
========================= [SUCCESS] Took XX.XXs =========================
```

**Firmware flashen:**

```bash
pio run -t upload
```

Der Upload verwendet die in `platformio.ini` konfigurierte Geschwindigkeit von 921600 Baud. Der XIAO ESP32-S3 wird automatisch in den Bootloader-Modus versetzt (sofern die USB-CDC-Verbindung steht).

**Erwartete Ausgabe bei Erfolg:**

```text
Uploading .pio/build/seeed_xiao_esp32s3/firmware.bin
...
Writing at 0x00010000... (100 %)
...
========================= [SUCCESS] Took XX.XXs =========================
```

**Kompilierung und Upload kombiniert:**

```bash
pio run -t upload -t monitor
```

Dieser Befehl kompiliert bei Bedarf, flasht die Firmware und oeffnet anschliessend den seriellen Monitor. Fuer die taegliche Entwicklung ist dies der empfohlene Workflow.

### 1.4 Serieller Monitor und Boot-Verifikation

Nach dem erfolgreichen Flash startet die Firmware automatisch. Die Verifikation erfordert ein Verstaendnis der Dual-Core-Architektur und der Tatsache, dass der serielle Port von micro-ROS belegt wird.

**Dual-Core-Architektur:**

Der XIAO ESP32-S3 verfuegt ueber zwei LX7-Kerne, die von der Firmware wie folgt genutzt werden:

- **Core 0** (`loop()` in `main.cpp`): Fuehrt den micro-ROS Agent aus. Er empfaengt `cmd_vel`-Nachrichten (Typ `geometry_msgs/msg/Twist`) und publiziert Odometrie-Daten (Typ `nav_msgs/msg/Odometry`) mit 20 Hz. Zusaetzlich ueberwacht er den Heartbeat von Core 1 als Inter-Core-Watchdog.
- **Core 1** (`controlTask` in `main.cpp`): Fuehrt die PID-Regelschleife mit exakt 50 Hz (20 ms Takt) aus. Diese Frequenz wird durch `vTaskDelayUntil` garantiert, was eine deterministische Regelung sicherstellt. Die Regelschleife liest die Encoder-Werte, berechnet die Radgeschwindigkeiten, fuehrt die PID-Regelung durch und setzt die Motor-PWM-Werte.

Die Thread-Sicherheit zwischen beiden Cores wird durch einen FreeRTOS-Mutex (`SharedData`-Struktur in `main.cpp`) gewaehrleistet. Gemeinsam genutzte Variablen (Soll-Geschwindigkeiten, Odometrie-Zustand) werden nur unter Mutex-Schutz gelesen und geschrieben.

**Serieller Monitor -- Wichtiger Hinweis:**

Der Befehl `pio run -t monitor` (oder `pio device monitor`) oeffnet den seriellen Monitor auf 115200 Baud. Da der serielle Port jedoch von micro-ROS fuer die Kommunikation mit dem Raspberry Pi belegt wird (`set_microros_serial_transports(Serial)` in `main.cpp`, Zeile 115), zeigt der Monitor im Normalbetrieb **binaere Daten (micro-ROS-Pakete)** statt lesbarem Text. Dies ist kein Fehler, sondern erwartetes Verhalten.

```bash
# Seriellen Monitor starten (zeigt binaere Daten)
pio run -t monitor
```

```text
# Typische Ausgabe: unleserliche Binaerdaten
??^@^@^@^B^@^@^@...
```

**Boot-Verifikation ohne seriellen Monitor:**

Da der serielle Port nicht fuer Debug-Ausgaben zur Verfuegung steht, erfolgt die Boot-Verifikation ueber die Status-LED an Pin D10 (GPIO 21):

- **LED blinkt schnell (200 ms an/aus)**: Ein Fehler bei der micro-ROS-Initialisierung ist aufgetreten. Moegliche Ursachen: micro-ROS Agent auf dem Raspberry Pi laeuft nicht, Inkompatibilitaet der ROS2-Distribution, oder fehlerhafte Firmware. In `main.cpp` (Zeilen 149-157) loest jeder fehlgeschlagene `rclc_*`-Aufruf dieses Blinksignal aus.
- **LED leuchtet nicht / zeigt normales Verhalten**: Die Firmware ist korrekt gestartet. Die LED wird im Normalbetrieb ueber den MOSFET-Kanal (LEDC-Kanal 4) angesteuert.

Fuer eine vollstaendige Verifikation der micro-ROS-Kommunikation muss der micro-ROS Agent auf dem Raspberry Pi laufen (siehe Teil 3).

### 1.5 Encoder-Validierung (Phase 2)

Die Encoder-Kalibrierung ist die wichtigste Voraussetzung fuer alle nachfolgenden Tests. Die aktuellen Werte in `config.h` (`TICKS_PER_REV_LEFT = 374.3f`, `TICKS_PER_REV_RIGHT = 373.6f`) sind mit dem Kommentar "noch nicht Kalibriert" markiert und muessen experimentell bestimmt werden.

**Vorbedingung: Pre-Flight-Checkliste**

Vor der Encoder-Validierung sollte die interaktive Hardware-Checkliste durchgefuehrt werden. Das Skript `pre_flight_check.py` prueft USB-Enumeration, Spannungsversorgung, Pin-Belegung und Firmware-Upload in einer gefuehrten Sequenz und erzeugt ein Markdown-Protokoll mit Timestamp und Pass/Fail-Bewertung pro Pruefpunkt.

```bash
# Auf dem Raspberry Pi ausfuehren (kein ROS2 erforderlich)
cd amr/scripts/
python3 pre_flight_check.py
```

Das Skript fuehrt durch sechs Pruefkategorien:

1. USB-Enumeration (`/dev/ttyACM*` automatisch gesucht)
2. Spannungsversorgung (interaktive Messwert-Eingabe fuer 3S1P Lithium-Ionen Samsung INR18650-35E 3500 mAh 8A, Buck-Converter, MDD3A, ESP32 3,3 V)
3. Pin-Belegung (visuelle Inspektion gegen `config.h`)
4. Firmware-Upload und Boot-Meldung
5. micro-ROS-Verbindung (optional, falls Agent laeuft)
6. Sensoren (RPLIDAR A1, Kamera)

Das Ergebnis wird als Markdown-Datei im Skript-Verzeichnis gespeichert (z.B. `pre_flight_20260215_143022.md`).

**Encoder-Kalibrierung mit encoder_test.py:**

Das Encoder-Kalibrierungs-Tool ist ein ROS2-Node, der `/odom`-Nachrichten subscribt und die Encoder-Ticks zurueckrechnet. Der micro-ROS Agent muss dafuer aktiv sein.

```bash
# micro-ROS Agent starten (in einem separaten Terminal)
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0

# Encoder-Test starten
ros2 run my_bot encoder_test.py
```

Das Skript bietet vier Modi ueber ein interaktives Menue:

1. **10-Umdrehungen-Test (Kalibrierung)**: Ein Rad wird manuell exakt 10 Umdrehungen gedreht. Das Skript zaehlt die Ticks ueber die Odometrie und berechnet den Mittelwert pro Umdrehung. Drei Durchgaenge pro Rad werden durchgefuehrt. Das Akzeptanzkriterium verlangt, dass der Wert zwischen 370 und 380 Ticks/Rev liegt und die Abweichung zwischen Durchgaengen kleiner als 2 Ticks betraegt.
2. **Richtungstest**: Prueft die Vorzeichenkonvention (vorwaerts = positiv, rueckwaerts = negativ). Da der Encoder im A-only-Modus betrieben wird, wird die Drehrichtung aus der PWM-Ansteuerung abgeleitet (`enc_left_dir` / `enc_right_dir` in `robot_hal.hpp`), nicht aus dem Encoder-Signal selbst.
3. **Asymmetrie-Test**: Vergleicht die Tick-Raten beider Raeder bei gleicher Ansteuerung. Eine Asymmetrie unter 5 % gilt als gut, 5-10 % als akzeptabel (wird durch PID kompensiert), ueber 10 % deutet auf ein mechanisches Problem hin.
4. **Live-Anzeige**: Zeigt aktuelle Geschwindigkeiten und Tick-Raten in Echtzeit an.

**config.h aktualisieren:**

Nach der Kalibrierung muessen die gemessenen Werte in `hardware/config.h` eingetragen werden. Die relevanten Zeilen befinden sich im Abschnitt "2.1 ENCODER-KALIBRIERUNG":

```c
// Vor Kalibrierung (Platzhalter):
#define TICKS_PER_REV_LEFT 374.3f  // noch nicht Kalibriert
#define TICKS_PER_REV_RIGHT 373.6f // noch nicht Kalibriert

// Nach Kalibrierung (Beispielwerte):
#define TICKS_PER_REV_LEFT 375.2f  // Kalibriert am 2026-02-15
#define TICKS_PER_REV_RIGHT 374.8f // Kalibriert am 2026-02-15
```

Nach der Aenderung muss die Firmware neu kompiliert und geflasht werden:

```bash
cd amr/esp32_amr_firmware/
pio run -t upload
```

Die abgeleiteten Konstanten `METERS_PER_TICK_LEFT` und `METERS_PER_TICK_RIGHT` werden automatisch neu berechnet, da sie ueber Praeprozessor-Makros aus `TICKS_PER_REV_LEFT/RIGHT` und `WHEEL_CIRCUMFERENCE` abgeleitet werden.

### 1.6 Motor-Validierung (Phase 3)

Die Motor-Validierung prueft die korrekte Ansteuerung, die Deadzone-Kompensation, das Failsafe-Verhalten und die Rampen-Beschleunigung. Das Test-Tool `motor_test.py` ist ein ROS2-Node, der `/cmd_vel` publiziert und `/odom` fuer Feedback subscribt.

```bash
# Motor-Test starten (micro-ROS Agent muss laufen)
ros2 run my_bot motor_test.py
```

**Sicherheitshinweis:** Der Roboter muss waehrend der Motor-Tests entweder auf Bloecken stehen (Raeder frei drehend) oder sich in einer sicheren Umgebung befinden. Ein Druck auf Ctrl+C sendet sofort `cmd_vel = 0` (Stopp-Befehl, 5-fach wiederholt fuer Zuverlaessigkeit).

Das Skript bietet vier Test-Modi:

**a) Deadzone-Test:**

Dieser Test erhoeht `cmd_vel` von 0,0 auf 0,2 m/s in 0,01er-Schritten und wartet jeweils 2 Sekunden pro Schritt. Er prueft ueber die Odometrie, ab welcher Geschwindigkeit die Motoren tatsaechlich anlaufen. In der Firmware (`robot_hal.hpp`, Zeilen 32-34) ist eine Deadzone-Kompensation implementiert: PWM-Werte groesser als 0 aber kleiner als `PWM_DEADZONE` (35) werden automatisch auf 35 angehoben. Dadurch wird sichergestellt, dass bei jedem Nicht-Null-Befehl ausreichend PWM anliegt, um die Motoren zu starten.

Der in `config.h` definierte Wert `PWM_DEADZONE = 35` sollte nach dem Deadzone-Test ueberprueft werden. Falls die Motoren erst bei einem deutlich hoeheren PWM-Wert anlaufen, muss der Deadzone-Wert in `config.h` entsprechend angepasst werden. Das Akzeptanzkriterium verlangt einen tatsaechlichen Anlauf-PWM im Bereich 30-40.

**b) Richtungstest:**

Der Richtungstest steuert einzelne Raeder und Kombinationen in alle Richtungen an (je 3 Sekunden). Er nutzt die Differentialkinematik, um ueber `linear.x` und `angular.z` einzelne Raeder gezielt anzusprechen. Getestet werden: links vorwaerts, links rueckwaerts, rechts vorwaerts, rechts rueckwaerts, beide vorwaerts, beide rueckwaerts.

Falls die Drehrichtung eines Motors nicht stimmt, sollten die Motoranschluesse am MDD3A physisch getauscht werden. Die Kanalzuordnung in `config.h` (PWM_CH_LEFT_A/B, PWM_CH_RIGHT_A/B) ist bereits fuer die korrekte Richtung konfiguriert und sollte nicht veraendert werden.

**c) Failsafe-Test:**

Der Failsafe-Test prueft das Timeout-Verhalten der Firmware. Er sendet `cmd_vel = 0,2 m/s` fuer 3 Sekunden und stoppt dann das Senden. Die Firmware (`main.cpp`, Zeilen 62-65) prueft in der Regelschleife auf Core 1, ob seit der letzten `cmd_vel`-Nachricht mehr als `FAILSAFE_TIMEOUT_MS` (500 ms, definiert in `config.h`) vergangen sind, und setzt in diesem Fall die Soll-Geschwindigkeiten auf Null.

Der Test misst die Zeit zwischen dem letzten gesendeten `cmd_vel` und dem Stillstand der Raeder (erkannt ueber Odometrie). Die erwartete Zeit betraegt ca. 500 ms mit einer Toleranz von +/- 200 ms.

**Hinweis zum Validierungsplan:** Der Validierungsplan (`hardware/docs/08_validierungsplan.md`, Abschnitt 7.5) nennt an einer Stelle 1000 ms als Failsafe-Timeout. Der autoritative Wert ist `FAILSAFE_TIMEOUT_MS = 500` aus `config.h` (Zeile 89). Der Validierungsplan enthaelt dort einen veralteten Wert.

**d) Rampen-Test:**

Der Rampen-Test beschleunigt den Roboter linear von 0 auf 0,4 m/s ueber 5 Sekunden und haelt dann die Zielgeschwindigkeit fuer 2 Sekunden. Er prueft, ob die Firmware-interne Beschleunigungsrampe (`MAX_ACCEL = 5.0 rad/s^2` in `main.cpp`, Zeile 16) korrekt arbeitet und die Raeder nicht durchdrehen.

### 1.7 Troubleshooting ESP32

Die folgenden Probleme treten am haeufigsten bei der Erstinbetriebnahme des XIAO ESP32-S3 auf.

**Problem:** Upload schlaegt fehl mit "Failed to connect to ESP32-S3" oder "No serial data received".

**Loesung:** Das USB-C-Kabel ist haeufig die Ursache. Reine Ladekabel haben nur 2 Adern (VCC + GND) und koennen keine Daten uebertragen. Ein Datenkabel mit 4 oder mehr Adern ist erforderlich. Zum Testen: Das Geraet muss unter `/dev/ttyACM*` (Linux/macOS) enumerieren. Falls nicht, ein anderes Kabel versuchen.

**Problem:** ESP32-S3 enumeriert nicht als `/dev/ttyACM*`.

**Loesung:** Den Boot-Button (GPIO 0) am XIAO gedrueckt halten, waehrend das USB-Kabel eingesteckt wird. Dies versetzt den ESP32 in den Bootloader-Modus, in dem er als USB-DFU-Geraet erscheint. Nach dem Flashen im Bootloader-Modus den ESP32 per Reset oder USB-Abstecken/-Anstecken neu starten.

**Problem:** Kompilierungsfehler bei `ledcSetup` / `ledcAttachPin` / `ledcWrite`.

**Loesung:** Die ESP32-S3-Variante verwendet eine neuere Version der LEDC-API. In aelteren ESP32-Arduino-Versionen existierten `ledcSetup()` und `ledcAttachPin()` als separate Funktionen, in neueren Versionen (ab Arduino-ESP32 v3.x) wurde dies zu `ledcAttach()` zusammengefasst. Die aktuelle Firmware verwendet die aeltere API (getestet mit espressif32 Plattform v6.x). Falls ein Upgrade der Plattform-Version noetig ist, muessen die LEDC-Aufrufe in `robot_hal.hpp` (Zeilen 60-71) angepasst werden.

**Problem:** Firmware startet, aber LED D10 blinkt schnell.

**Loesung:** Die schnell blinkende LED signalisiert einen Fehler bei der micro-ROS-Initialisierung (`main.cpp`, Zeilen 149-157). Moegliche Ursachen: Der micro-ROS Agent auf dem Raspberry Pi laeuft nicht, oder die ROS2-Distribution (Humble) stimmt nicht mit der Firmware-Konfiguration ueberein. Der Agent muss vor dem ESP32-Neustart gestartet werden, damit die Session aufgebaut werden kann.

**Problem:** Encoder zeigen sporadische Ticks bei Stillstand.

**Loesung:** Die Encoder-Versorgungsspannung pruefen. Die Hall-Encoder benoetigen eine stabile VCC (3,3 V vom ESP32-S3 oder 5 V mit Pegelanpassung). Elektromagnetische Stoerungen durch die Motor-PWM koennen falsche Interrupts ausloesen. Abhilfe: Encoder-Leitungen als Twisted Pair fuehren, ggf. 100 nF Kondensator nahe am Encoder-Eingang (D6/D7) gegen GND schalten. Die Interrupt-Service-Routinen in `robot_hal.hpp` (Zeilen 17-23) sind mit `IRAM_ATTR` markiert und reagieren auf `RISING`-Flanken.

**Problem:** PID-Regelung schwingt oder Motoren brummen bei niedrigen Geschwindigkeiten.

**Loesung:** Mit 374 statt 1440 Ticks/Rev ist die Geschwindigkeitsmessung ca. 3,9-fach groeber. Dies kann zu hoeherem Quantisierungsrauschen fuehren, das die PID-Regelung verstaerkt. Die PID-Gains (Kp=1,5, Ki=0,5, Kd=0,0 in `main.cpp`, Zeile 19-20) muessen nach der Encoder-Kalibrierung ggf. angepasst werden (siehe Teil 4, Abschnitt PID-Tuning).

---

## Teil 2: Raspberry Pi 5 ROS2-Umgebung

Dieses Kapitel beschreibt die Einrichtung des Raspberry Pi 5 als zentralen Navigationsrechner des AMR. Der Pi uebernimmt SLAM, Pfadplanung und die Kommunikation mit dem ESP32-S3 ueber micro-ROS.

### 2.1 Voraussetzungen und ROS2-Installation

Der Raspberry Pi 5 muss mit Raspberry Pi OS (64-bit, Bookworm) betrieben werden. ROS2 Humble ist die Zieldistribution und wird ueber die offiziellen apt-Repositories installiert.

Zunaechst werden die ROS2-apt-Quellen hinzugefuegt:

```bash
sudo apt update && sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

Anschliessend wird ROS2 Humble Desktop installiert. Die Desktop-Variante enthaelt RViz2 fuer die Visualisierung:

```bash
sudo apt update
sudo apt install -y ros-humble-desktop
```

Nach der Installation muss das ROS2-Setup in jeder neuen Shell geladen werden. Es empfiehlt sich, dies in die `.bashrc` einzutragen:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Folgende zusaetzliche ROS2-Pakete werden fuer den AMR-Stack benoetigt:

```bash
sudo apt install -y \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-rplidar-ros \
  ros-humble-cv-bridge \
  python3-colcon-common-extensions \
  python3-rosdep
```

Falls `rosdep` noch nicht initialisiert wurde:

```bash
sudo rosdep init
rosdep update
```

### 2.2 ROS2-Paket my_bot vervollstaendigen

Das ROS2-Paket `my_bot` liegt unter `amr/pi5/ros2_ws/src/my_bot/`. Im Repository befinden sich bereits die funktionalen Dateien (Launch-File, YAML-Konfigurationen, Python-Skripte), jedoch fehlen die fuer `colcon build` zwingend erforderlichen Paket-Metadateien. Ohne diese Dateien erkennt `colcon` das Verzeichnis nicht als gueltiges ROS2-Paket.

Die folgenden vier Dateien muessen erstellt werden.

#### 2.2.1 package.xml

Die `package.xml` definiert den Paketnamen, die Version und alle Abhaengigkeiten. Das Format 3 (`ament_python`) wird verwendet, da das Paket ausschliesslich Python-Code enthaelt:

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd"
  schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_bot</name>
  <version>0.1.0</version>
  <description>AMR navigation and control package for differential-drive
    robot with XIAO ESP32-S3 and Raspberry Pi 5</description>
  <maintainer email="student@university.de">Jan</maintainer>
  <license>MIT</license>

  <buildtool_depend>ament_python</buildtool_depend>

  <!-- Runtime-Abhaengigkeiten -->
  <exec_depend>rclpy</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>geometry_msgs</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>nav_msgs</exec_depend>
  <exec_depend>tf2_ros</exec_depend>
  <exec_depend>cv_bridge</exec_depend>

  <!-- Navigation und SLAM -->
  <exec_depend>nav2_bringup</exec_depend>
  <exec_depend>slam_toolbox</exec_depend>

  <!-- Hardware-Treiber -->
  <exec_depend>micro_ros_agent</exec_depend>
  <exec_depend>rplidar_ros</exec_depend>

  <!-- Launch -->
  <exec_depend>launch</exec_depend>
  <exec_depend>launch_ros</exec_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

Die `exec_depend`-Eintraege stellen sicher, dass `rosdep` alle notwendigen Pakete automatisch installieren kann. Die Abhaengigkeiten wurden aus dem Launch-File (`full_stack.launch.py`) und den Python-Skripten abgeleitet.

#### 2.2.2 setup.py

Die `setup.py` definiert, welche Dateien wohin installiert werden und welche Python-Skripte als ROS2-Nodes aufrufbar sein sollen:

```python
import os
from glob import glob
from setuptools import setup

package_name = 'my_bot'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jan',
    maintainer_email='student@university.de',
    description='AMR navigation and control package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'aruco_docking = my_bot.aruco_docking:main',
            'encoder_test = my_bot.encoder_test:main',
            'motor_test = my_bot.motor_test:main',
            'pid_tuning = my_bot.pid_tuning:main',
            'kinematic_test = my_bot.kinematic_test:main',
            'slam_validation = my_bot.slam_validation:main',
            'nav_test = my_bot.nav_test:main',
            'docking_test = my_bot.docking_test:main',
        ],
    },
)
```

Die `data_files`-Liste sorgt dafuer, dass YAML-Konfigurationen und das Launch-File in den `share`-Ordner des Workspaces installiert werden. Dadurch kann `FindPackageShare('my_bot')` im Launch-File die Dateien zur Laufzeit finden.

Die `entry_points` registrieren die Python-Skripte als ausfuehrbare ROS2-Nodes. Nach dem Build koennen sie mit `ros2 run my_bot <node_name>` gestartet werden.

#### 2.2.3 setup.cfg

Die `setup.cfg` legt fest, wohin `colcon` die ausfuehrbaren Skripte installiert:

```ini
[develop]
script_dir=$base/lib/my_bot
[install]
install_scripts=$base/lib/my_bot
```

Dies ist die Standard-Konfiguration fuer ament_python-Pakete und stellt sicher, dass `ros2 run` die Nodes findet.

#### 2.2.4 resource/my_bot und my_bot/__init__.py

Zwei weitere Dateien werden benoetigt:

Die Datei `resource/my_bot` ist eine leere Marker-Datei fuer den ament Resource Index. Ohne diese Datei kann `ros2 pkg list` das Paket nicht finden:

```bash
mkdir -p amr/pi5/ros2_ws/src/my_bot/resource
touch amr/pi5/ros2_ws/src/my_bot/resource/my_bot
```

Die Datei `my_bot/__init__.py` macht das Verzeichnis zu einem Python-Paket. Auch diese Datei bleibt leer:

```bash
mkdir -p amr/pi5/ros2_ws/src/my_bot/my_bot
touch amr/pi5/ros2_ws/src/my_bot/my_bot/__init__.py
```

#### 2.2.5 Skripte verlinken

Die Python-Skripte liegen im `scripts/`-Verzeichnis, muessen aber als Modul im `my_bot/`-Paketverzeichnis erreichbar sein. Dafuer werden symbolische Links erstellt:

```bash
cd amr/pi5/ros2_ws/src/my_bot/my_bot/
ln -s ../scripts/aruco_docking.py aruco_docking.py
ln -s ../scripts/encoder_test.py encoder_test.py
ln -s ../scripts/motor_test.py motor_test.py
ln -s ../scripts/pid_tuning.py pid_tuning.py
ln -s ../scripts/kinematic_test.py kinematic_test.py
ln -s ../scripts/slam_validation.py slam_validation.py
ln -s ../scripts/nav_test.py nav_test.py
ln -s ../scripts/docking_test.py docking_test.py
```

Alternativ koennen die Skripte auch direkt in das `my_bot/`-Verzeichnis kopiert werden. Die Symlink-Variante hat den Vorteil, dass Aenderungen an den Skripten automatisch auch im Paket wirksam werden.

Nach dem Erstellen aller Dateien sollte die Verzeichnisstruktur wie folgt aussehen:

```text
amr/pi5/ros2_ws/src/my_bot/
  package.xml
  setup.py
  setup.cfg
  resource/
    my_bot              (leere Marker-Datei)
  my_bot/
    __init__.py         (leere Datei)
    aruco_docking.py -> ../scripts/aruco_docking.py
    encoder_test.py  -> ../scripts/encoder_test.py
    ...
  config/
    nav2_params.yaml
    mapper_params_online_async.yaml
  launch/
    full_stack.launch.py
  scripts/
    aruco_docking.py
    encoder_test.py
    motor_test.py
    ...
```

### 2.3 Workspace bauen

Der ROS2-Workspace wird mit `colcon` gebaut. Es empfiehlt sich, nur das eigene Paket zu bauen, um Bauzeit zu sparen:

```bash
cd amr/pi5/ros2_ws/
colcon build --packages-select my_bot --symlink-install
```

Das Flag `--symlink-install` erstellt symbolische Links statt Kopien. Dadurch werden Aenderungen an Python-Skripten und Konfigurationsdateien sofort wirksam, ohne erneut bauen zu muessen.

Nach erfolgreichem Build muss das Workspace-Setup geladen werden:

```bash
source install/setup.bash
```

Fuer dauerhafte Verfuegbarkeit kann dies in die `.bashrc` eingetragen werden:

```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

Die Installation kann mit folgenden Befehlen verifiziert werden:

```bash
ros2 pkg list | grep my_bot
```

Erwartete Ausgabe:

```text
my_bot
```

Und die verfuegbaren Nodes pruefen:

```bash
ros2 pkg executables my_bot
```

Erwartete Ausgabe:

```text
my_bot aruco_docking
my_bot docking_test
my_bot encoder_test
my_bot kinematic_test
my_bot motor_test
my_bot nav_test
my_bot pid_tuning
my_bot slam_validation
```

### 2.4 RPLIDAR A1 einrichten

Der RPLIDAR A1 wird ueber USB an den Raspberry Pi angeschlossen. Der ROS2-Treiber wurde bereits in Abschnitt 2.1 installiert (`ros-humble-rplidar-ros`).

Zunaechst wird der LiDAR physisch angeschlossen und geprueft, ob er als serielles Geraet erkannt wird:

```bash
ls /dev/ttyUSB*
```

Erwartete Ausgabe:

```text
/dev/ttyUSB0
```

Der RPLIDAR A1 nutzt einen CP2102-USB-Seriell-Wandler. Falls das Geraet nicht erscheint, fehlt moeglicherweise der Treiber oder die USB-Verbindung ist fehlerhaft.

Berechtigungen fuer den seriellen Port setzen:

```bash
sudo chmod 666 /dev/ttyUSB0
```

Fuer eine dauerhafte Loesung werden udev-Regeln in Abschnitt 2.6 eingerichtet.

Test des LiDAR mit dem Standard-Launch-File:

```bash
ros2 launch rplidar_ros rplidar_a1_launch.py
```

In einem zweiten Terminal kann das `/scan`-Topic ueberprueft werden:

```bash
ros2 topic echo /scan --once
```

Es sollte eine `sensor_msgs/LaserScan`-Nachricht mit Entfernungswerten erscheinen. Die Reichweite des RPLIDAR A1 betraegt bis zu 12 m.

### 2.5 Kamera einrichten

Der AMR verwendet eine Raspberry Pi Global Shutter Camera (Sony IMX296, 1456x1088 Pixel) mit einem 6 mm CS-Mount-Objektiv. Die Kamera wird ueber das CSI-Flachbandkabel mit dem Raspberry Pi verbunden.

Verbindung pruefen:

```bash
libcamera-hello --list-cameras
```

Erwartete Ausgabe (Auszug):

```text
Available cameras
-----------------
0 : imx296 [1456x1088] (/base/soc/i2c0mux/i2c@1/imx296@1a)
```

Testbild aufnehmen:

```bash
libcamera-hello -t 3000
```

Fuer die Verwendung mit ROS2 und OpenCV muss die Kamera ueber das V4L2-Interface angesprochen werden. Falls noetig, das V4L2-Modul laden:

```bash
sudo modprobe bcm2835-v4l2
```

Pruefen, ob das Kamerageraet vorhanden ist:

```bash
ls /dev/video*
```

Die Kamera wird vom ArUco-Docking-Node ueber das Topic `/camera/image_raw` verwendet. Dafuer wird ein Kamera-Publisher-Node benoetigt, beispielsweise `v4l2_camera`:

```bash
sudo apt install -y ros-humble-v4l2-camera
ros2 run v4l2_camera v4l2_camera_node --ros-args -p video_device:="/dev/video0"
```

### 2.6 udev-Regeln

Ohne udev-Regeln koennen sich die Geraetedateien (`/dev/ttyUSB0`, `/dev/ttyACM0`) bei jedem Neustart oder bei veraenderter USB-Reihenfolge aendern. Mit udev-Regeln werden stabile, symbolische Geraetepfade erstellt.

Zunaechst die Vendor- und Product-IDs der USB-Geraete ermitteln:

```bash
# ESP32-S3 (USB-CDC)
udevadm info -a -n /dev/ttyACM0 | grep -E "idVendor|idProduct|serial"

# RPLIDAR A1 (CP2102)
udevadm info -a -n /dev/ttyUSB0 | grep -E "idVendor|idProduct|serial"
```

Typische Werte:
- XIAO ESP32-S3: `idVendor=303a`, `idProduct=1001`
- RPLIDAR A1 (CP2102): `idVendor=10c4`, `idProduct=ea60`

Die udev-Regeldatei erstellen:

```bash
sudo nano /etc/udev/rules.d/99-amr-devices.rules
```

Inhalt der Regeldatei:

```text
# XIAO ESP32-S3 (micro-ROS, USB-CDC)
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", \
  SYMLINK+="amr_esp32", MODE="0666"

# RPLIDAR A1 (CP2102 USB-Serial)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
  SYMLINK+="amr_lidar", MODE="0666"
```

Regeln aktivieren (ohne Neustart):

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Pruefen, ob die Symlinks erstellt wurden:

```bash
ls -la /dev/amr_*
```

Erwartete Ausgabe:

```text
lrwxrwxrwx 1 root root 7 ... /dev/amr_esp32 -> ttyACM0
lrwxrwxrwx 1 root root 7 ... /dev/amr_lidar -> ttyUSB0
```

Ab sofort koennen die stabilen Pfade `/dev/amr_esp32` und `/dev/amr_lidar` in Launch-Files und Konfigurationen verwendet werden:

```bash
ros2 launch my_bot full_stack.launch.py serial_port:=/dev/amr_esp32
```

### 2.7 micro-ROS Agent installieren

Der micro-ROS Agent ist die Bruecke zwischen dem XIAO ESP32-S3 (micro-ROS Client) und dem ROS2-Graphen auf dem Raspberry Pi. Er uebersetzt DDS-XRCE-Nachrichten vom seriellen Port in Standard-ROS2-Topics.

Installation ueber apt (empfohlen):

```bash
sudo apt install -y ros-humble-micro-ros-agent
```

Falls das Paket nicht ueber apt verfuegbar ist, kann der Agent aus dem Quellcode gebaut werden:

```bash
mkdir -p ~/microros_ws/src
cd ~/microros_ws
git clone -b humble https://github.com/micro-ROS/micro-ROS-Agent.git src/micro-ROS-Agent
rosdep install --from-paths src --ignore-src -y
colcon build --packages-select micro_ros_agent
source install/setup.bash
```

Test der Verbindung zum ESP32-S3:

```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/amr_esp32 -b 115200
```

Erwartete Ausgabe bei erfolgreicher Verbindung:

```text
[info] [micro_ros_agent] Serial agent running on /dev/amr_esp32 at 115200 baud
[info] [micro_ros_agent] Client connected
```

In einem zweiten Terminal die Topics pruefen:

```bash
ros2 topic list
```

Nach erfolgreicher Verbindung sollten mindestens diese Topics erscheinen:

```text
/cmd_vel
/odom
/parameter_events
/rosout
```

Die Odometrie-Daten vom ESP32 anzeigen:

```bash
ros2 topic echo /odom --once
```

Es sollte eine `nav_msgs/Odometry`-Nachricht mit Position und Geschwindigkeit erscheinen. Die Publikationsrate betraegt 20 Hz (konfiguriert in `config.h` als `ODOM_PUBLISH_HZ`).

### 2.8 Troubleshooting Raspberry Pi

#### Serial-Port-Berechtigungen

**Problem:** `ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0` schlaegt fehl mit `Permission denied`.

**Loesung:** Den Benutzer zur `dialout`-Gruppe hinzufuegen und ab-/anmelden:

```bash
sudo usermod -aG dialout $USER
# Abmelden und neu anmelden, damit die Gruppenrechte wirksam werden
```

Alternativ fuer sofortigen Test ohne Neuanmeldung:

```bash
sudo chmod 666 /dev/ttyACM0
```

Die dauerhafte Loesung sind die udev-Regeln aus Abschnitt 2.6, die `MODE="0666"` setzen.

#### ESP32 wird nicht als serielles Geraet erkannt

**Problem:** Nach dem Anschliessen des XIAO ESP32-S3 erscheint kein `/dev/ttyACM0`.

**Loesung:** Pruefen, ob der USB-CDC-Treiber geladen ist:

```bash
dmesg | tail -20
```

Der XIAO ESP32-S3 nutzt den nativen USB-CDC des ESP32-S3 (kein externer USB-Seriell-Wandler). Falls `cdc_acm` nicht geladen ist:

```bash
sudo modprobe cdc_acm
```

Falls das Geraet weiterhin nicht erscheint, den ESP32 in den Bootloader-Modus versetzen: Boot-Taste halten, Reset druecken, Boot loslassen.

#### colcon build schlaegt fehl

**Problem:** `colcon build` meldet `package 'my_bot' not found` oder `SetuptoolsDeprecationWarning`.

**Loesung:** Sicherstellen, dass alle vier Paketdateien vorhanden sind (`package.xml`, `setup.py`, `setup.cfg`, `resource/my_bot`). Die Verzeichnisstruktur pruefen:

```bash
ls amr/pi5/ros2_ws/src/my_bot/package.xml
ls amr/pi5/ros2_ws/src/my_bot/setup.py
ls amr/pi5/ros2_ws/src/my_bot/setup.cfg
ls amr/pi5/ros2_ws/src/my_bot/resource/my_bot
ls amr/pi5/ros2_ws/src/my_bot/my_bot/__init__.py
```

Falls `SetuptoolsDeprecationWarning` erscheint, eine kompatible Version installieren:

```bash
pip install setuptools==58.2.0
```

#### micro-ROS Agent verbindet sich nicht

**Problem:** Der Agent startet, aber meldet keinen `Client connected`.

**Loesung:** Folgende Punkte pruefen:

1. Baudrate stimmt (muss 115200 sein, passend zur Firmware).
2. Der ESP32 ist korrekt geflasht und laeuft (LED-Status beachten).
3. Der richtige Port wird verwendet. Pruefen mit:

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

4. Kein anderer Prozess belegt den Port:

```bash
sudo fuser /dev/ttyACM0
```

Falls ein Prozess den Port belegt, diesen beenden oder einen anderen Port verwenden.

#### RPLIDAR dreht nicht

**Problem:** Der RPLIDAR A1 wird erkannt, aber der Motor dreht nicht und es kommen keine Scan-Daten.

**Loesung:** Der RPLIDAR A1 benoetigt 5V-Versorgung ueber USB. Pruefen, ob der USB-Port genuegend Strom liefert. Bei Verwendung eines USB-Hubs muss dieser aktiv (mit eigenem Netzteil) sein. Alternativ den LiDAR direkt an den Raspberry Pi anschliessen.

Falls der Motor dreht aber keine Daten kommen, den Topic-Status pruefen:

```bash
ros2 topic hz /scan
```

Die erwartete Rate liegt bei ca. 5-10 Hz (abhaengig von der Drehzahl).

#### Kamera wird nicht erkannt

**Problem:** `libcamera-hello --list-cameras` zeigt keine Kamera.

**Loesung:** Das CSI-Flachbandkabel pruefen. Die Kontaktseite muss zur Platine zeigen (blaue Markierung nach aussen). Ausserdem in der `/boot/config.txt` sicherstellen, dass die Kamera aktiviert ist:

```bash
sudo raspi-config
# Interface Options -> Camera -> Enable
```

Nach der Aenderung ist ein Neustart erforderlich.

#### RViz2 zeigt kein Bild auf dem Pi

**Problem:** RViz2 startet, aber das Fenster bleibt schwarz oder stuerzt ab.

**Loesung:** RViz2 auf dem Raspberry Pi 5 benoetigt OpenGL-Unterstuetzung. Falls Probleme auftreten, den Software-Renderer verwenden:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch my_bot full_stack.launch.py
```

Alternativ kann RViz2 auf dem Entwicklungsrechner ausgefuehrt werden, waehrend der Navigation-Stack headless auf dem Pi laeuft:

```bash
# Auf dem Pi (ohne RViz2):
ros2 launch my_bot full_stack.launch.py use_rviz:=False

# Auf dem Entwicklungsrechner (mit ROS2 und Netzwerkverbindung):
ros2 launch nav2_bringup rviz_launch.py
```

Dafuer muessen beide Rechner im selben ROS2-DDS-Domain sein (Standard: `ROS_DOMAIN_ID=0`) und Multicast-Netzwerkverkehr erlaubt sein.

---

## Teil 3: Zusammenspiel ESP32 <-> Pi5 (Phase 7)

Die Integration der ESP32-S3 Firmware mit dem ROS2-Stack auf dem Raspberry Pi 5 bildet die entscheidende Schnittstelle des Gesamtsystems. In Phase 7 wird die Kommunikation ueber micro-ROS verifiziert und das Full-Stack-Launch getestet. Alle folgenden Schritte setzen voraus, dass die Firmware erfolgreich geflasht wurde (Teil 1) und die ROS2-Umgebung funktionsfaehig ist (Teil 2).

### 3.1 micro-ROS UART-Verbindung

Der micro-ROS Agent stellt die Bruecke zwischen dem ESP32-S3 und dem ROS2-Graphen auf dem Raspberry Pi her. Die Kommunikation erfolgt ueber USB-CDC (virtuelle serielle Schnittstelle) mit 115200 Baud. Der ESP32-S3 belegt den seriellen Port vollstaendig fuer micro-ROS -- ein gleichzeitiger Debug-Zugriff ueber den Serial Monitor ist daher nicht moeglich.

Der Agent wird wie folgt gestartet:

```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 115200
```

Nach dem Start wartet der Agent auf eine Verbindungsanfrage vom ESP32-S3. Der Verbindungsaufbau (Session-Establishment) dauert typischerweise 2-5 Sekunden. Die Reihenfolge ist dabei unkritisch: Der ESP32 kann vor oder nach dem Agent gestartet werden. Falls der ESP32 zuerst laeuft, wartet er auf den Agent. Falls der Agent zuerst laeuft, wartet er auf den Client.

Waehrend des Verbindungsaufbaus durchlaeuft der ESP32-S3 folgende Phasen, die ueber die LED am D10-Pin (MOSFET-gesteuert) signalisiert werden:

1. **Boot**: Die Firmware initialisiert FreeRTOS-Tasks und micro-ROS (2 Sekunden Startup-Delay in `setup()`).
2. **Verbindungsversuch**: `rclc_support_init()` versucht die Session mit dem Agent aufzubauen.
3. **Verbunden**: Node `esp32_bot` ist im ROS2-Graphen sichtbar. Odometrie wird publiziert.
4. **Fehler**: Bei fehlgeschlagener Initialisierung blinkt die LED schnell (200 ms Intervall) als Fehlersignal.

Die Zeitsynchronisation zwischen ESP32-S3 und dem ROS2-Host erfolgt ueber `rmw_uros_sync_session(1000)` am Ende von `setup()`. Dadurch stimmen die Timestamps in den Odometrie-Nachrichten mit der ROS2-Clock ueberein.

### 3.2 Topic-Verifikation

Sobald die micro-ROS-Session aufgebaut ist, muessen zwei Topics im ROS2-Graphen sichtbar sein. Die Verifikation erfolgt ueber die Kommandozeile:

```bash
ros2 topic list
```

Erwartete Ausgabe (mindestens):

```text
/cmd_vel
/odom
/parameter_events
/rosout
```

Die Topics `/cmd_vel` und `/odom` werden vom ESP32-S3 bereitgestellt. Der ESP32-S3 subscribt auf `/cmd_vel` (Typ `geometry_msgs/msg/Twist`) und publiziert `/odom` (Typ `nav_msgs/msg/Odometry`).

Die Odometrie-Nachricht kann wie folgt inspiziert werden:

```bash
ros2 topic echo /odom --once
```

Erwartete Ausgabe (bei stehendem Roboter):

```text
header:
  stamp:
    sec: 1234567890
    nanosec: 123456789
  frame_id: "odom"
child_frame_id: "base_link"
pose:
  pose:
    position:
      x: 0.0
      y: 0.0
      z: 0.0
    orientation:
      x: 0.0
      y: 0.0
      z: 0.0
      w: 1.0
twist:
  twist:
    linear:
      x: 0.0
    angular:
      z: 0.0
```

Besonders wichtig sind die Frame-IDs: `header.frame_id` muss `"odom"` sein und `child_frame_id` muss `"base_link"` lauten. Diese Frame-Zuordnung ist in `main.cpp` (Zeilen 192-195) hardcoded und stellt die korrekte TF-Kette sicher, die SLAM und Navigation benoetigen.

Bei manueller Raddrehung muessen sich die Odometrie-Werte (`pose.pose.position.x`, `twist.twist.linear.x`) sichtbar aendern. Falls sie bei Null bleiben, liegt ein Encoder- oder Firmware-Problem vor (siehe Abschnitt 3.7).

### 3.3 Publikationsrate und Latenz

Die Odometrie-Publikationsrate ist in `config.h` als `ODOM_PUBLISH_PERIOD_MS = 50` definiert, was einer Soll-Rate von 20 Hz entspricht. Die Regelschleife auf Core 1 laeuft unabhaengig davon bei 50 Hz (`CONTROL_LOOP_PERIOD_MS = 20`).

Die Rate wird wie folgt gemessen:

```bash
ros2 topic hz /odom
```

Erwartete Ausgabe (nach einigen Sekunden Mittelung):

```text
average rate: 19.98
	min: 0.048s max: 0.053s std dev: 0.00142s window: 100
```

Die Rate sollte im Bereich 18-22 Hz liegen. Eine stabile Rate zeigt an, dass die micro-ROS-Kommunikation und das Timing auf Core 0 korrekt funktionieren.

Fuer eine laengere Stabilitaetsmessung (5 Minuten) kann die Fenstergroesse vergroessert werden:

```bash
ros2 topic hz /odom -w 6000
```

Das Akzeptanzkriterium fuer den Paketverlust liegt bei < 0.1 %. Bei 20 Hz ueber 60 Sekunden werden 1200 Nachrichten erwartet. Die Anzahl empfangener Nachrichten kann ueber die Fenstergroesse von `ros2 topic hz` abgeleitet werden.

### 3.4 Failsafe-Test

Die Firmware implementiert einen Failsafe-Mechanismus: Wenn Core 1 laenger als `FAILSAFE_TIMEOUT_MS = 500` (definiert in `config.h`, Zeile 89) keine neuen `cmd_vel`-Nachrichten erhaelt, werden die Motoren automatisch gestoppt. Dieser Mechanismus schuetzt gegen Kommunikationsausfaelle und Agent-Abstuerze.

Der Failsafe wird in `controlTask()` (Zeile 62-65 in `main.cpp`) geprueft:

```cpp
if (millis() - last_cmd_time > FAILSAFE_TIMEOUT_MS) {
    tv = 0;
    tw = 0;
}
```

Der Test erfolgt in zwei Schritten:

Zuerst wird der Roboter auf Geschwindigkeit gebracht (Raeder angehoben oder Roboter in sicherer Umgebung):

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}" --rate 10
```

Die Raeder drehen sich. Anschliessend wird der `ros2 topic pub`-Befehl mit Ctrl+C beendet. Die Motoren muessen innerhalb von 500 ms zum Stillstand kommen.

Alternativ kann der gesamte micro-ROS Agent gestoppt werden:

```bash
# Agent-Prozess finden und beenden
pkill -f micro_ros_agent
```

Auch in diesem Fall muessen die Motoren innerhalb des Failsafe-Timeouts stoppen. Nach dem Neustart des Agents wird die Session automatisch wiederhergestellt und der ESP32-S3 reagiert erneut auf `cmd_vel`-Nachrichten.

Zusaetzlich zum cmd_vel-Failsafe ueberwacht Core 0 in `loop()` (Zeilen 163-174) den Heartbeat von Core 1. Wenn der `core1_heartbeat`-Zaehler 50 Zyklen lang nicht inkrementiert wird, fuehrt Core 0 einen Notfall-Stopp der Motoren durch (`hal.setMotors(0, 0)`).

### 3.5 Full-Stack Launch

Das kombinierte Launch-File `full_stack.launch.py` startet alle Komponenten des ROS2-Stacks in einem einzigen Befehl. Es befindet sich unter `amr/pi5/ros2_ws/src/my_bot/launch/` und startet vier Subsysteme: micro-ROS Agent, SLAM Toolbox, Nav2 Navigation Stack und RViz2.

Der Standard-Start mit allen Komponenten:

```bash
ros2 launch my_bot full_stack.launch.py
```

Das Launch-File unterstuetzt sechs konfigurierbare Argumente, die verschiedene Betriebsmodi ermoeglichen:

**Nur SLAM (ohne Navigation)** -- nuetzlich fuer die initiale Kartenerstellung:

```bash
ros2 launch my_bot full_stack.launch.py use_nav:=false
```

In diesem Modus wird nur die SLAM Toolbox gestartet. Der Roboter kann manuell (per `ros2 topic pub /cmd_vel ...` oder Teleop) gesteuert werden, waehrend die Karte aufgebaut wird.

**Headless-Betrieb (ohne RViz2)** -- fuer den Einsatz ohne angeschlossenen Monitor:

```bash
ros2 launch my_bot full_stack.launch.py use_rviz:=False
```

Dies spart CPU- und GPU-Ressourcen auf dem Raspberry Pi 5.

**Nur Navigation mit bestehender Karte (ohne SLAM)** -- fuer den Produktivbetrieb:

```bash
ros2 launch my_bot full_stack.launch.py use_slam:=False
```

Voraussetzung: Eine zuvor mit SLAM Toolbox erstellte Karte muss in der Nav2-Konfiguration referenziert sein.

**Alternativer serieller Port** -- falls der ESP32-S3 nicht unter `/dev/ttyACM0` enumeriert:

```bash
ros2 launch my_bot full_stack.launch.py serial_port:=/dev/ttyUSB0
```

Der Standard-Port ist `/dev/ttyACM0` (USB-CDC des XIAO ESP32-S3). Falls eine udev-Regel eingerichtet wurde (z.B. fuer `/dev/amr_esp32`), kann dieser Symlink verwendet werden.

**Kombination mehrerer Argumente** -- alle Argumente koennen frei kombiniert werden:

```bash
ros2 launch my_bot full_stack.launch.py use_nav:=false use_rviz:=False serial_port:=/dev/ttyUSB0
```

Die SLAM Toolbox verwendet die Konfiguration aus `config/mapper_params_online_async.yaml` (Ceres-Solver, 5 cm Aufloesung, Loop Closure aktiviert). Der Nav2-Stack wird mit `config/nav2_params.yaml` parametriert (AMCL-Lokalisierung, Regulated Pure Pursuit Controller mit 0.4 m/s Maximalgeschwindigkeit, Navfn-Planer, Recovery Behaviors).

### 3.6 TF-Baum-Verifikation

Der Navigations-Stack benoetigt eine vollstaendige TF-Kette (Transform-Baum) von `map` bis zu den Sensor-Frames. Die erwartete Kette lautet:

```text
map -> odom -> base_link -> laser
                          -> camera_link
```

Die Transformation `odom -> base_link` wird vom ESP32-S3 ueber die Odometrie-Nachricht bereitgestellt. Die Transformation `map -> odom` wird von der SLAM Toolbox (oder AMCL bei reiner Navigation) berechnet. Die statischen Transformationen `base_link -> laser` und `base_link -> camera_link` muessen im URDF oder ueber `static_transform_publisher`-Nodes definiert sein.

Der TF-Baum kann als PDF-Datei exportiert werden:

```bash
ros2 run tf2_tools view_frames
```

Dieser Befehl zeichnet 5 Sekunden lang TF-Daten auf und erstellt eine Datei `frames_YYYY-MM-DD_HH.MM.SS.pdf` im aktuellen Verzeichnis. Die PDF zeigt den vollstaendigen Baum mit allen Frame-Beziehungen und ihren Publikationsraten.

Einzelne Transformationen koennen auch ueber die Kommandozeile geprueft werden:

```bash
ros2 topic echo /tf --once
```

Fuer eine spezifische Transformation (z.B. `map -> base_link`):

```bash
ros2 run tf2_ros tf2_echo map base_link
```

Erwartete Ausgabe (bei stehendem Roboter an Position 0,0):

```text
At time ...
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion [0.000, 0.000, 0.000, 1.000]
```

Falls eine Transformation fehlt (z.B. `map -> odom`), wurde die SLAM Toolbox noch nicht korrekt gestartet oder hat noch keine Scan-Daten empfangen.

### 3.7 Troubleshooting Kommunikation

**Problem:** Agent findet den ESP32-S3 nicht -- keine Session wird aufgebaut.

**Loesung:** Das USB-CDC-Geraet muss als `/dev/ttyACM*` enumeriert sein. Mit `ls /dev/ttyACM*` pruefen. Falls kein Geraet erscheint: USB-C-Kabel pruefen (Datenkabel, nicht nur Ladekabel), ESP32-S3 neu starten (Reset-Taster), oder den ESP32-S3 in den Bootloader-Modus versetzen und Firmware erneut flashen. Falls `/dev/ttyUSB*` statt `/dev/ttyACM*` erscheint, wird ein externer USB-UART-Adapter verwendet -- der Parameter `serial_port` muss entsprechend angepasst werden.

**Problem:** `ros2 topic list` zeigt `/cmd_vel` und `/odom` nicht an.

**Loesung:** Die micro-ROS-Session ist nicht aufgebaut. Im Agent-Terminal auf Fehlerausgaben pruefen. Haeufige Ursache: Die ROS2-Domain-ID (`ROS_DOMAIN_ID`) stimmt zwischen Agent und ROS2-Shell nicht ueberein. Beide muessen denselben Wert verwenden (Standard: 0). Mit `echo $ROS_DOMAIN_ID` in beiden Terminals pruefen.

**Problem:** Falsche Baudrate -- Agent meldet Verbindungsfehler oder Zeichensalat.

**Loesung:** Die Baudrate muss auf beiden Seiten 115200 betragen. In der Firmware ist dies in `setup()` ueber `Serial.begin(115200)` festgelegt. Der Agent muss mit `-b 115200` gestartet werden. Eine abweichende Baudrate fuehrt zu verstaendigungsunfaehiger Kommunikation und aeussert sich durch fehlende Topics.

**Problem:** `Permission denied` beim Zugriff auf `/dev/ttyACM0`.

**Loesung:** Der Benutzer muss Mitglied der Gruppe `dialout` sein:

```bash
sudo usermod -a -G dialout $USER
```

Nach dem Hinzufuegen zur Gruppe ist ein Neuanmelden (Logout/Login) oder Neustart erforderlich. Alternativ kann der Zugriff temporaer mit `sudo chmod 666 /dev/ttyACM0` freigeschaltet werden. Fuer eine dauerhafte Loesung empfiehlt sich eine udev-Regel.

**Problem:** LED blinkt schnell nach dem Booten des ESP32-S3.

**Loesung:** Das schnelle LED-Blinken (200 ms Intervall) signalisiert einen Fehler bei der micro-ROS-Initialisierung. Moegliche Ursachen: micro-ROS-Bibliothek nicht kompatibel mit ESP32-S3, Flash-Speicher voll, oder der micro-ROS Agent laeuft nicht. Die Firmware stoppt in einer Endlosschleife (Zeilen 149-157 in `main.cpp`) und publiziert keine Daten. Firmware-Version und micro-ROS-Bibliothek pruefen, ggf. PlatformIO-Dependencies aktualisieren.

**Problem:** Odometrie-Werte aendern sich nicht bei Raddrehung.

**Loesung:** Die Encoder-Pins pruefen: D6 (GPIO43) fuer den linken Encoder und D7 (GPIO44) fuer den rechten Encoder. Phase B (gruenes Kabel) muss an beiden Motoren isoliert und nicht angeschlossen sein. Falls die Encoder-ISR nicht ausloest, die Verdrahtung der Encoder-Versorgung (3.3 V, GND) und des Signalkabels (gelb, Phase A) ueberpruefen. Die Encoder-Ticks koennen ueber den Validierungsskript `encoder_test.py` geprueft werden.

**Problem:** Motoren reagieren nicht auf `cmd_vel`, obwohl Topics sichtbar sind.

**Loesung:** Die Firmware-Rampe (`MAX_ACCEL = 5.0 rad/s^2` in `main.cpp`) begrenzt die Beschleunigung. Bei sehr kleinen `cmd_vel`-Werten kann die PWM-Deadzone (`PWM_DEADZONE = 35` in `config.h`) dazu fuehren, dass die Motoren nicht anlaufen. Geschwindigkeiten ab ca. 0.05 m/s sollten eine sichtbare Reaktion erzeugen. Zusaetzlich pruefen, ob der Failsafe-Timeout bereits greift -- `cmd_vel` muss mindestens alle 500 ms erneut gesendet werden.

---

## Teil 4: Kalibrierung und Validierung (Phasen 4-6, 8-9)

Die vorherigen Teile haben die Firmware auf dem ESP32-S3, die ROS2-Umgebung auf dem Raspberry Pi 5 und die Integration beider Systeme behandelt. In diesem Teil wird das Gesamtsystem systematisch kalibriert und validiert. Die Validierung folgt dem V-Modell nach VDI 2206: Jede Phase baut auf der vorherigen auf, daher ist die Reihenfolge strikt einzuhalten. Alle Validierungsskripte speichern ihre Ergebnisse als JSON-Dateien, die am Ende zu einem Gesamt-Report aggregiert werden (siehe Abschnitt 4.7).

**Voraussetzungen fuer alle Validierungsschritte:**

- ESP32-Firmware laeuft (LED blinkt, serieller Monitor zeigt Boot-Meldung)
- micro-ROS Agent verbindet sich erfolgreich mit dem ESP32
- `/odom`-Topic wird publiziert, `/cmd_vel` wird empfangen
- Der Roboter steht auf ebenem, griffigem Untergrund
- Massband (mindestens 5 m), Winkelmesser und Klebeband fuer Bodenmarkierungen liegen bereit

---

### 4.1 Kinematik-Validierung (Phase 4)

Die Kinematik-Validierung prueft, ob die in `hardware/config.h` definierten Parameter (Raddurchmesser 65 mm, Spurbreite 178 mm, ~374 Ticks/Rev) korrekt umgesetzt sind. Drei Tests werden nacheinander durchgefuehrt: Geradeausfahrt, 90-Grad-Drehung und Kreisfahrt.

**Voraussetzung:** Der Full-Stack muss laufen (micro-ROS Agent + Firmware). SLAM und Navigation sind fuer diesen Test nicht erforderlich, aber der micro-ROS Agent muss aktiv sein.

```bash
# Full-Stack starten (auf dem Pi5)
ros2 launch my_bot full_stack.launch.py use_slam:=false use_nav:=false
```

**Alle drei Tests ausfuehren:**

```bash
ros2 run my_bot kinematic_test.py
```

Alternativ koennen einzelne Tests separat ausgefuehrt werden:

```bash
ros2 run my_bot kinematic_test.py gerade     # Nur Geradeausfahrt
ros2 run my_bot kinematic_test.py drehung    # Nur 90-Grad-Drehungen
ros2 run my_bot kinematic_test.py kreis      # Nur Kreisfahrt
```

#### Test A: Geradeausfahrt (2 m)

Der Roboter faehrt mit 0,2 m/s fuer 5 Sekunden geradeaus (Soll-Strecke: 1 m). Das Skript berechnet automatisch die Streckenabweichung und die laterale Drift. Die Strecke wird im Startkoordinatensystem des Roboters gemessen, sodass auch eine schraege Anfangsausrichtung korrekt beruecksichtigt wird.

**Akzeptanzkriterien:**
- Streckenabweichung: < 5 %
- Laterale Drift: < 5 cm

**Interpretation:** Eine systematische Streckenabweichung deutet auf einen falschen Raddurchmesser in `config.h` hin. Laterale Drift zeigt eine Asymmetrie zwischen den Raedern an, die durch die UMBmark-Kalibrierung (Phase 5) korrigiert wird.

#### Test B: 90-Grad-Drehung

Der Roboter fuehrt 5 Drehungen im Uhrzeigersinn (CW) und 5 Drehungen gegen den Uhrzeigersinn (CCW) mit omega = pi/2 rad/s fuer jeweils 1 Sekunde aus. Nach jeder Drehung wird eine 3-Sekunden-Pause eingelegt.

**Akzeptanzkriterien:**
- Winkelabweichung: < 5 Grad
- Asymmetrie zwischen CW und CCW: < 3 Grad

**Interpretation:** Systematische Winkelabweichungen deuten auf eine falsche Spurbreite (`WHEEL_BASE`) hin. Eine Asymmetrie zwischen CW und CCW zeigt unterschiedliche Raddurchmesser an.

#### Test C: Kreisfahrt

Der Roboter faehrt einen vollstaendigen Kreis mit v = 0,2 m/s und omega = 0,5 rad/s (Radius 0,4 m). Nach einer vollen Umdrehung wird die Abweichung der Endposition von der Startposition gemessen.

**Akzeptanzkriterium:**
- Endposition weicht maximal 10 cm vom Startpunkt ab

#### JSON-Ausgabe

Die Ergebnisse werden automatisch in `amr/scripts/kinematik_ergebnis.json` gespeichert. Beispiel fuer eine erfolgreiche Messung:

```text
Kinematik-Verifikationstest
  WHEEL_RADIUS = 0.0325 m
  WHEEL_BASE = 0.178 m

Warte auf Odometrie...
Odometrie empfangen. Tests starten.

============================================================
Test A: Geradeausfahrt 1 m
============================================================
  Start: x=0.0000 m, y=0.0000 m, yaw=0.00 deg
  Fahre: v=0.2 m/s, omega=0, Dauer=5.0 s
  Ende:  x=0.9821 m, y=0.0034 m, yaw=0.12 deg

  Vorwaerts-Strecke: 0.9821 m (Soll: 1.0 m, Fehler: 1.79%)
  Laterale Drift:    0.0034 m (Akzeptanz: < 0.05 m)
  Bewertung: Strecke OK, Drift OK
```

---

### 4.2 UMBmark-Kalibrierung (Phase 5)

Die UMBmark-Kalibrierung nach Borenstein und Feng (1996) ist das primaere Verfahren zur Reduktion systematischer Odometriefehler. Sie quantifiziert und korrigiert zwei Fehlerquellen: unterschiedliche effektive Raddurchmesser (Typ-B-Fehler, Korrekturfaktor E_d) und eine falsche effektive Spurbreite (Typ-A-Fehler, Korrekturfaktor E_b).

#### Physisches Setup

Fuer den UMBmark-Test wird ein 4x4-Meter-Quadrat benoetigt:

1. Ein freier Bereich von mindestens 5x5 Metern auf ebenem Boden
2. Vier Ecken mit Klebeband markieren (4 m Seitenlaenge)
3. Startposition an einer Ecke markieren (Position und Ausrichtung)
4. Massband in der Naehe der Startposition auslegen (fuer Endpositions-Messung)

#### Testdurchfuehrung

Der Test besteht aus 5 Fahrten im Uhrzeigersinn (CW) und 5 Fahrten gegen den Uhrzeigersinn (CCW). Jede Fahrt ist eine vollstaendige Quadratfahrt: 4 m geradeaus, 90 Grad Drehung, 4 m geradeaus, 90 Grad Drehung, 4 m geradeaus, 90 Grad Drehung, 4 m geradeaus. Gesamt pro Lauf: 16 m Pfadlaenge.

**Ablauf pro Lauf:**

1. Roboter exakt auf die Startmarkierung stellen (Position und Orientierung)
2. Quadratfahrt-Programm starten (vier Geradeaus-Segmente mit je 90-Grad-Drehung dazwischen)
3. Nach Abschluss: Endposition relativ zum Startpunkt messen (x- und y-Abweichung in mm)
4. Beide Abweichungen notieren

Die Endpositionen werden als JSON-Datei vorbereitet:

```json
{
    "cw": [[12, -8], [15, -6], [10, -9], [14, -7], [11, -8]],
    "ccw": [[-5, 10], [-3, 12], [-6, 9], [-4, 11], [-5, 10]]
}
```

Dabei sind die Werte (x, y) in Millimetern angegeben -- positive x-Werte bedeuten Abweichung nach vorne, positive y-Werte nach links.

#### Auswertung

Das Auswertungsskript berechnet die Korrekturfaktoren:

```bash
python3 amr/scripts/umbmark_analysis.py daten.json
```

Oder interaktiv (die Werte werden manuell eingegeben):

```bash
python3 amr/scripts/umbmark_analysis.py
```

Das Skript fuehrt folgende Berechnungen durch (nach Borenstein 1996, Gl. 5.9-5.15):

1. Schwerpunkte der CW- und CCW-Endpositionen berechnen
2. Fehlerwinkel alpha (Typ-A, Spurbreite) und beta (Typ-B, Raddurchmesser) bestimmen
3. Korrekturfaktor E_d (Raddurchmesser-Verhaeltnis) und E_b (Spurbreite-Korrektur) berechnen
4. Korrigierte Werte fuer `WHEEL_BASE`, `WHEEL_RADIUS_LEFT` und `WHEEL_RADIUS_RIGHT` ausgeben

#### Ergebnis anwenden

Das Skript gibt fertige config.h-Definitionen aus:

```text
### Korrigierte config.h-Werte (Copy-Paste)

#define WHEEL_BASE          0.179234f  // [m] UMBmark-korrigiert
#define WHEEL_RADIUS_LEFT   0.032412f  // [m] UMBmark-korrigiert
#define WHEEL_RADIUS_RIGHT  0.032588f  // [m] UMBmark-korrigiert
```

Diese Werte muessen in `hardware/config.h` eingetragen werden. Danach die Firmware neu kompilieren und flashen:

```bash
cd amr/esp32_amr_firmware
pio run -t upload
```

**Akzeptanzkriterium:** Nach der Kalibrierung muessen 5 weitere CW- und 5 CCW-Laeufe durchgefuehrt werden. Die Schwerpunktabweichung muss sich um mindestens Faktor 10 gegenueber dem unkalibrierten Zustand verbessert haben.

Das Skript erzeugt zusaetzlich einen Scatterplot (`umbmark_ergebnis.png`) und eine JSON-Exportdatei (`umbmark_ergebnis.json`).

---

### 4.3 PID-Re-Tuning (Phase 6)

Die PID-Regelung steuert die Radgeschwindigkeiten des Roboters. Nach der UMBmark-Kalibrierung oder bei Aenderungen an der Mechanik (Untergrund, Zuladung) kann ein Re-Tuning erforderlich sein. Die aktuellen PID-Werte sind in `amr/esp32_amr_firmware/src/main.cpp` hardcoded:

- Kp = 1,5 (Proportionalanteil)
- Ki = 0,5 (Integralanteil)
- Kd = 0,0 (Differentialanteil, deaktiviert)

#### Sprungantwort aufnehmen

Das PID-Tuning-Skript sendet einen Geschwindigkeitssprung von 0 auf 0,4 m/s und zeichnet die Ist-Geschwindigkeit ueber 10 Sekunden auf:

```bash
ros2 run my_bot pid_tuning.py live
```

Alternativ kann eine bestehende rosbag2-Aufzeichnung ausgewertet werden:

```bash
ros2 run my_bot pid_tuning.py bag /pfad/zur/rosbag
```

#### Bewertungskriterien

Das Skript berechnet vier Kenngroessen und bewertet sie gegen die Akzeptanzkriterien:

| Kenngroesse              | Akzeptanzgrenze | Bedeutung                                                         |
|--------------------------|-----------------|-------------------------------------------------------------------|
| Anstiegszeit (10%-90%)   | < 500 ms        | Zeit bis der Ist-Wert 90% des Sollwerts erreicht                  |
| Ueberschwingen           | < 15 %          | Maximale Abweichung ueber den Sollwert                            |
| Einschwingzeit (+/- 5%)  | < 1,0 s         | Zeit bis der Ist-Wert dauerhaft innerhalb 5% des Sollwerts bleibt |
| Stationaerer Regelfehler | < 5 %           | Verbleibende Abweichung im eingeschwungenen Zustand               |

Zusaetzlich erkennt das Skript Oszillationen (mehr als 6 Nulldurchgaenge um den Sollwert) und gibt gezielte Tuning-Empfehlungen aus.

#### Beispielausgabe

```text
======================================================================
PID-Sprungantwort-Analyse
======================================================================

### Kenngroessen der Sprungantwort

| Kenngroesse            | Wert    | Akzeptanz | Bewertung |
|:-----------------------|:--------|:----------|:----------|
| Anstiegszeit (10%-90%) | 0.312 s | < 0.5 s   | OK        |
| Ueberschwingen         | 8.3 %   | < 15 %    | OK        |
| Einschwingzeit (+/-5%) | 0.743 s | < 1.0 s   | OK        |
| Stationaerer Fehler    | 2.1 %   | < 5 %     | OK        |

### Tuning-Empfehlungen

Aktuelle PID-Werte: Kp = 1.5, Ki = 0.5, Kd = 0.0

- Alle Kenngroessen innerhalb der Akzeptanzkriterien.
- Keine Aenderung erforderlich.
```

#### PID-Werte anpassen

Falls die Kenngroessen ausserhalb der Akzeptanzgrenzen liegen, muessen die PID-Werte in `amr/esp32_amr_firmware/src/main.cpp` angepasst werden. Die Datei enthaelt die Zeilen:

```cpp
PIDController pid_left(1.5, 0.5, 0.0);   // Kp, Ki, Kd
PIDController pid_right(1.5, 0.5, 0.0);  // Kp, Ki, Kd
```

**Tuning-Strategie (manuell):**

1. Wenn die Anstiegszeit zu langsam ist: Kp erhoehen (z.B. auf 2,0)
2. Wenn das Ueberschwingen zu hoch ist: Kp reduzieren (z.B. auf 1,0) und/oder Kd > 0 setzen (z.B. 0,01)
3. Wenn der stationaere Fehler zu gross ist: Ki erhoehen (z.B. auf 0,8)
4. Wenn Oszillationen auftreten: Kp deutlich reduzieren

Nach jeder Aenderung: Firmware neu kompilieren und flashen (`pio run -t upload`), dann erneut `pid_tuning.py live` ausfuehren.

Das Skript speichert einen Sprungantwort-Plot als `pid_sprungantwort.png` im Skript-Verzeichnis.

---

### 4.4 SLAM-Validierung (Phase 8)

Die SLAM-Validierung prueft die Kartierungsqualitaet durch Berechnung des Absolute Trajectory Error (ATE). Da kein externes Motion-Capture-System vorhanden ist, wird der Drift zwischen der SLAM-korrigierten Position (map -> base_link) und der reinen Odometrie (odom -> base_link) als Qualitaetsmass verwendet.

**Voraussetzung:** Der Full-Stack muss mit SLAM laufen:

```bash
ros2 launch my_bot full_stack.launch.py use_nav:=false
```

Der Roboter sollte waehrend der Messung manuell (z.B. per Teleop) durch die Umgebung gefahren werden, damit SLAM eine Karte aufbauen kann.

#### Test ausfuehren

```bash
ros2 run my_bot slam_validation.py --live --duration 120
```

Das Skript fuehrt drei Pruefungen durch:

1. **TF-Ketten-Verifikation:** Prueft ob die Transformationen map -> odom -> base_link -> laser verfuegbar sind. Fehlende Frames deuten auf ein Konfigurationsproblem hin.

2. **ATE-Berechnung:** Alle 200 ms wird die SLAM-korrigierte Pose (aus TF map -> base_link) abgefragt und mit der zeitgleichen Odometrie-Pose verglichen. Der RMSE ueber alle Zeitpunkte ergibt den ATE.

3. **Report-Generierung:** Ein Markdown-Report (`slam_validation_report.md`) und ein Trajektorien-Plot (`slam_validation_plot.png`) werden gespeichert.

Alternativ kann eine existierende rosbag2-Aufzeichnung ausgewertet werden:

```bash
ros2 run my_bot slam_validation.py --bag /pfad/zur/rosbag2_db
```

Fuer die rosbag2-Aufzeichnung waehrend einer Live-Session:

```bash
ros2 bag record /odom /tf /tf_static /scan -o slam_session
```

**Akzeptanzkriterium:** ATE (RMSE) < 0,20 m

```text
--- Ergebnis ---
Odom-Posen:  2400
SLAM-Posen:  600
ATE (RMSE):  0.1423 m

SLAM-Validierung BESTANDEN (ATE < 0.20 m)
```

---

### 4.5 Navigations-Validierung (Phase 8)

Die Navigations-Validierung testet das Zusammenspiel von SLAM, Lokalisierung (AMCL) und dem Regulated Pure Pursuit Controller (RPP). Das Skript sendet Waypoints ueber den Nav2 NavigateToPose Action-Server und misst die Positionsgenauigkeit am Zielpunkt.

**Voraussetzung:** Der Full-Stack muss vollstaendig laufen (inklusive Navigation):

```bash
ros2 launch my_bot full_stack.launch.py
```

Falls eine bestehende Karte verwendet wird (empfohlen fuer reproduzierbare Tests):

```bash
ros2 launch my_bot full_stack.launch.py use_slam:=False
```

#### Test ausfuehren

```bash
ros2 run my_bot nav_test.py
```

Mit angepasstem Timeout und Ausgabeverzeichnis:

```bash
ros2 run my_bot nav_test.py --timeout 90 --output /tmp/nav_results
```

Das Skript navigiert den Roboter durch ein 2x2-Meter-Rechteck mit vier Waypoints:

1. WP1: 2 m geradeaus (x=2, y=0, yaw=0)
2. WP2: 2 m links (x=2, y=2, yaw=pi/2)
3. WP3: zurueck in x-Richtung (x=0, y=2, yaw=pi)
4. WP4: zurueck zum Start (x=0, y=0, yaw=0)

An jedem Waypoint wird die Ist-Position aus der Odometrie abgelesen und der euklidische Positionsfehler (xy) sowie der Orientierungsfehler (yaw) berechnet. Der Regulated Pure Pursuit Controller faehrt mit maximal 0,4 m/s (konfiguriert in `nav2_params.yaml`).

**Akzeptanzkriterien:**
- Positionsfehler (xy): < 10 cm (konfiguriert als `xy_goal_tolerance: 0.10` in nav2_params.yaml)
- Orientierungsfehler (yaw): < 8 Grad (konfiguriert als `yaw_goal_tolerance: 0.15` rad)

#### Ausgabe

Das Skript erzeugt einen Markdown-Report (`nav_test_report.md`) und eine JSON-Ergebnisdatei (`nav_test_results.json`):

```text
============================================================
NAVIGATIONSTEST: BESTANDEN
Waypoints: 4/4 bestanden
============================================================
```

---

### 4.6 Docking-Validierung (Phase 9)

Die Docking-Validierung prueft die ArUco-Marker-basierte Endanfahrt an die Ladestation. Das Visual-Servoing-System erkennt einen ArUco-Marker (ID 42, Dictionary 4x4_50) ueber die Kamera, zentriert den Roboter lateral und faehrt langsam auf den Marker zu, bis ein Schwellwert fuer die Marker-Breite im Bild erreicht wird.

**Voraussetzung:** Kamera-Topic `/camera/image_raw` wird publiziert und der ArUco-Marker (ID 42) ist an der Ladestation befestigt. Der micro-ROS Agent muss aktiv sein.

#### Test ausfuehren

```bash
ros2 run my_bot docking_test.py
```

Der Test ist interaktiv: Der Benutzer positioniert den Roboter manuell ca. 1,5 m vor dem ArUco-Marker und startet jeden Versuch mit der Eingabe "s" + Enter. Insgesamt werden 10 Versuche durchgefuehrt.

**Ablauf pro Versuch:**

1. Benutzer positioniert Roboter und drueckt "s"
2. **SEARCHING-Phase:** Roboter dreht sich langsam (0,2 rad/s), bis der Marker erkannt wird
3. **APPROACHING-Phase:** Roboter faehrt mit 0,05 m/s auf den Marker zu, waehrend die Kameraausrichtung proportional korrigiert wird (Kp = 0,5)
4. **DOCKED-State:** Marker-Breite ueberschreitet 150 Pixel -- Roboter stoppt
5. Roboter faehrt 3 Sekunden rueckwaerts zur Ausgangsposition
6. Timeout bei 60 Sekunden ohne erfolgreichen Dock

Eingabe "q" + Enter bricht den Test vorzeitig ab und wertet die bisherigen Versuche aus.

**Akzeptanzkriterium:** Erfolgsquote >= 8 von 10 Versuchen (80 %)

#### Ausgabe

```text
===========================================================
DOCKING-VALIDIERUNG: ERGEBNISSE
===========================================================

| Versuch | Erfolg | Dauer [s] | Lat. Versatz [px] | Orient. [deg] |
|---------|--------|-----------|-------------------|---------------|
| 1       | Ja     | 12.3      | -3.2              | -1.4          |
| 2       | Ja     | 10.8      | 2.1               | 0.8           |
| ...     | ...    | ...       | ...               | ...           |

Erfolgsquote: 9/10 (90%)
Erfolgsquote >= 80%: PASS
```

Die Ergebnisse werden in `amr/scripts/docking_results.json` gespeichert.

---

### 4.7 Gesamt-Validierungsbericht

Nach Abschluss aller Validierungsphasen aggregiert das Report-Skript alle JSON-Ergebnisse zu einem Gesamt-Validierungsbericht. Das Skript ist ein Standalone-Python-Programm ohne ROS2-Abhaengigkeit.

```bash
python3 amr/scripts/validation_report.py
```

Optional kann ein anderes Verzeichnis fuer die JSON-Dateien angegeben werden:

```bash
python3 amr/scripts/validation_report.py /pfad/zu/ergebnissen/
```

#### Erwartete JSON-Dateien

Das Skript sucht nach folgenden Dateien im angegebenen Verzeichnis:

| Datei                    | Testbereich                                      |
|--------------------------|--------------------------------------------------|
| `encoder_results.json`   | Encoder-Ticks/Rev, Odom-Rate, Paketverlust       |
| `motor_results.json`     | Deadzone, Failsafe                               |
| `umbmark_results.json`   | UMBmark-Fehlerreduktion                          |
| `pid_results.json`       | Anstiegszeit, Ueberschwingen                     |
| `kinematic_results.json` | Kinematik-Verifikation                           |
| `slam_results.json`      | ATE                                              |
| `nav_results.json`       | xy-Genauigkeit, Gier-Genauigkeit, CPU-Auslastung |
| `docking_results.json`   | Erfolgsquote, lateraler Versatz                  |

Fehlende Dateien werden als "AUSSTEHEND" markiert, nicht als Fehler gewertet.

#### Beispielausgabe

```text
Ergebnis-Verzeichnis: amr/scripts
Suche JSON-Dateien...

  encoder_results.json               gefunden
  motor_results.json                 gefunden
  umbmark_results.json               gefunden
  pid_results.json                   gefunden
  kinematic_results.json             gefunden
  slam_results.json                  gefunden
  nav_results.json                   gefunden
  docking_results.json               gefunden

# AMR Validierungsbericht

**Datum:** 2026-02-12 14:30
**Hardware:** XIAO ESP32-S3 + RPi5 + Cytron MDD3A
**Roboter:** AMR Differentialantrieb, 65 mm Raeder, 178 mm Spurbreite

## Zusammenfassung

Bestanden: 13/14 Kriterien
Fehlgeschlagen: 0
Ausstehend: 1

## Detailergebnisse

| Testbereich | Kriterium    | Anforderung | Ergebnis | Status |
|-------------|--------------|-------------|----------|--------|
| Encoder     | Ticks/Rev    | 370-380     | 374.3    | PASS   |
| Motor       | Deadzone     | 30-40       | 35       | PASS   |
| PID         | Anstiegszeit | < 500 ms    | 312      | PASS   |
| ...         | ...          | ...         | ...      | ...    |

## Forschungsfragen-Zuordnung

- **FF1 (Echtzeit):** PASS
- **FF2 (Praezision):** PASS
- **FF3 (Docking):** PASS

## Gesamtbewertung: BESTANDEN
```

Der Report ordnet die Ergebnisse den drei Forschungsfragen zu:

- **FF1 (Echtzeit):** PID-Regelguete, micro-ROS-Kommunikation, Failsafe
- **FF2 (Praezision):** UMBmark, SLAM-ATE, Navigationsgenauigkeit, Encoder
- **FF3 (Docking):** ArUco-Docking-Erfolgsquote und Praezision

Der Report wird als `validation_report_YYYYMMDD.md` im Skript-Verzeichnis gespeichert.

---

### 4.8 Troubleshooting Validierung

**Problem:** `kinematic_test.py` meldet "Keine Odometrie empfangen".
**Loesung:** Der micro-ROS Agent laeuft nicht oder hat keine Verbindung zum ESP32. Pruefen: `ros2 topic list | grep odom` -- fehlt `/odom` in der Liste, den Agent neu starten (siehe Teil 3). Seriellen Monitor pruefen, ob die Firmware gestartet ist.

**Problem:** Geradeausfahrt zeigt starke laterale Drift (> 10 cm auf 1 m).
**Loesung:** Haeufigste Ursache: unterschiedliche Raddurchmesser links/rechts. Die UMBmark-Kalibrierung (Abschnitt 4.2) berechnet den exakten Korrekturfaktor E_d. Vorlaeufig: Pruefen ob beide Raeder frei drehen und der Boden gleichmaessig griffig ist.

**Problem:** 90-Grad-Drehung ergibt systematisch zu viel oder zu wenig Grad.
**Loesung:** Der Wert `WHEEL_BASE` in `config.h` stimmt nicht mit der tatsaechlichen Spurbreite ueberein. Die physische Spurbreite (Mitte-zu-Mitte der Radaufstandspunkte) nachmessen und in config.h korrigieren. Firmware neu flashen.

**Problem:** UMBmark-Endpositionen streuen stark (Standardabweichung > 50 mm).
**Loesung:** Starke Streuung deutet auf nicht-systematische (zufaellige) Fehler hin, die durch UMBmark nicht korrigierbar sind. Moegliche Ursachen: Radschlupf (Boden zu glatt), lockere Radnaben, ungleichmaessiger Untergrund. Auf griffigem, ebenem Boden wiederholen.

**Problem:** PID-Sprungantwort zeigt Dauerschwingung.
**Loesung:** Kp ist zu hoch fuer die reduzierte Encoder-Aufloesung (374 statt 1440 Ticks/Rev). Kp schrittweise reduzieren (z.B. auf 1,0, dann 0,8) bis die Schwingung verschwindet. Bei Bedarf Kd leicht erhoehen (z.B. 0,01) fuer zusaetzliche Daempfung.

**Problem:** SLAM-Validierung zeigt ATE > 0,20 m.
**Loesung:** Moegliche Ursachen: (1) Odometrie-Kalibrierung nicht durchgefuehrt -- UMBmark zuerst abschliessen. (2) LiDAR-Daten von schlechter Qualitaet -- `ros2 topic echo /scan --once` pruefen ob plausible Messwerte kommen. (3) Umgebung zu strukturarm (lange Gaenge ohne Landmarken) -- in strukturierter Umgebung testen. (4) SLAM-Toolbox-Parameter nicht optimal -- `loop_search_maximum_distance` in mapper_params erhoehen falls Loop Closure fehlt.

**Problem:** Navigation erreicht Waypoints nicht (Timeout).
**Loesung:** (1) Costmap pruefen: `ros2 topic echo /local_costmap/costmap_raw` -- ist der Pfad frei? (2) AMCL-Lokalisierung pruefen: In RViz2 die Partikelwolke visualisieren -- wenn sie divergiert, AMCL mit "2D Pose Estimate" manuell initialisieren. (3) Controller-Frequenz pruefen: `ros2 topic hz /cmd_vel` -- sollte 10 Hz sein.

**Problem:** Docking-Test erkennt den ArUco-Marker nicht.
**Loesung:** (1) Kamera-Topic pruefen: `ros2 topic echo /camera/image_raw --once` -- kommt ein Bild? (2) Beleuchtung: ArUco-Marker braucht gleichmaessige Beleuchtung, kein Gegenlicht. (3) Marker-ID pruefen: Das Skript sucht nach ID 42 aus dem 4x4_50-Dictionary. (4) OpenCV-Version: `python3 -c "import cv2; print(cv2.__version__)"` muss >= 4.7 sein fuer die `ArucoDetector`-API.

**Problem:** `validation_report.py` zeigt alle Kriterien als "AUSSTEHEND".
**Loesung:** Die JSON-Ergebnisdateien liegen nicht im erwarteten Verzeichnis. Standardmaessig sucht das Skript im eigenen Verzeichnis (`amr/scripts/`). Pruefen ob die Dateinamen exakt uebereinstimmen (z.B. `docking_results.json`, nicht `docking_ergebnis.json`).

---

## Anhang A: Akzeptanzkriterien

Die folgende Tabelle fasst alle Akzeptanzkriterien des Validierungsplans zusammen. Die Kriterien basieren auf dem V-Modell-Phasenplan (siehe `hardware/docs/08_validierungsplan.md`) und den Anforderungen der Bachelorarbeit.

| Nr.   | Phase | Testbereich | Kriterium                         | Schwellwert                                    | Messmethode                                           |
|-------|-------|-------------|-----------------------------------|------------------------------------------------|-------------------------------------------------------|
| AK-01 | 2     | Encoder     | Wiederholgenauigkeit Ticks/Rev    | Abweichung zwischen Durchgaengen < 2 Ticks/Rev | 10-Umdrehungen-Test (encoder_test.py), 3x wiederholen |
| AK-02 | 2     | Encoder     | Ticks/Rev im Sollbereich          | 370-380 Ticks/Rev (A-only Hall)                | 10-Umdrehungen-Test, Mittelwert aus 3 Durchgaengen    |
| AK-03 | 2     | Encoder     | Links/Rechts-Asymmetrie           | < 5 %                                          | Identischer PWM-Wert, 10 s Laufzeit, Tick-Vergleich   |
| AK-04 | 3     | Motor       | PWM-Deadzone                      | Anlauf-PWM im Bereich 30-40                    | motor_test.py, schrittweise PWM-Erhoehung             |
| AK-05 | 3     | Motor       | Failsafe-Timeout                  | Motoren stoppen innerhalb 500 ms ohne cmd_vel  | cmd_vel unterbrechen, Stoppzeit messen                |
| AK-06 | 4     | Kinematik   | Geradeausfahrt Streckenabweichung | < 5 % auf 1 m                                  | kinematic_test.py, Geradeausfahrt-Test                |
| AK-07 | 4     | Kinematik   | Geradeausfahrt laterale Drift     | < 5 cm auf 1 m                                 | kinematic_test.py, Geradeausfahrt-Test                |
| AK-08 | 4     | Kinematik   | 90-Grad-Drehung Winkelabweichung  | < 5 Grad                                       | kinematic_test.py, 5x CW + 5x CCW                     |
| AK-09 | 5     | UMBmark     | Fehlerreduktion nach Kalibrierung | Faktor >= 10                                   | umbmark_analysis.py, Vergleich vor/nach               |
| AK-10 | 6     | PID         | Anstiegszeit (10%-90%)            | < 500 ms                                       | pid_tuning.py, Sprungantwort 0 -> 0,4 m/s             |
| AK-11 | 6     | PID         | Ueberschwingen                    | < 15 %                                         | pid_tuning.py, Sprungantwort-Analyse                  |
| AK-12 | 6     | PID         | Einschwingzeit (+/- 5%)           | < 1,0 s                                        | pid_tuning.py, Sprungantwort-Analyse                  |
| AK-13 | 6     | PID         | Stationaerer Regelfehler          | < 5 %                                          | pid_tuning.py, letzte 20% der Messdaten               |
| AK-14 | 7     | micro-ROS   | Odometrie-Publikationsrate        | 20 Hz +/- 2 Hz                                 | ros2 topic hz /odom, 5 min Messung                    |
| AK-15 | 7     | micro-ROS   | Paketverlust                      | < 0,1 %                                        | ros2 topic hz /odom -w 1000, 60 s Messung             |
| AK-16 | 8     | SLAM        | Absolute Trajectory Error (ATE)   | < 0,20 m (RMSE)                                | slam_validation.py, Live-Modus 120 s                  |
| AK-17 | 8     | Navigation  | Positionsfehler xy                | < 10 cm                                        | nav_test.py, 4-Waypoint-Parcours                      |
| AK-18 | 8     | Navigation  | Orientierungsfehler Gier          | < 8 Grad (0,15 rad)                            | nav_test.py, 4-Waypoint-Parcours                      |
| AK-19 | 9     | Docking     | Erfolgsquote                      | >= 80 % (8/10 Versuche)                        | docking_test.py, 10 Versuche                          |

---

## Anhang B: Referenztabelle Validierungsskripte

Die folgende Tabelle listet alle 10 Validierungsskripte des Projekts mit ihren zugehoerigen Validierungsphasen, Abhaengigkeiten und Akzeptanzkriterien. Die Skripte befinden sich im Verzeichnis `amr/scripts/` und sind im V-Modell-Validierungsplan (`hardware/docs/08_validierungsplan.md`) dokumentiert. Die Phasen muessen sequentiell abgearbeitet werden, da jeder Testbereich auf den vorherigen aufbaut.

| Skript                 | Phase          | ROS2 noetig               | Aufruf                                                                                   | Beschreibung                                                                                                                                                                                                                                                                                                                                                                           | Akzeptanzkriterium                                                                                     |
|------------------------|----------------|---------------------------|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `pre_flight_check.py`  | 1 (Pre-Flash)  | Nein                      | `python3 pre_flight_check.py`                                                            | Interaktive Hardware-Checkliste: USB-Enumeration, Spannungsversorgung (3S1P Lithium-Ionen Samsung INR18650-35E 3500 mAh 8A, Buck-Converter 5.1 V), Pin-Belegung gegen config.h, Firmware-Upload, Sensor-Erkennung (RPLIDAR, Kamera). Erzeugt Markdown-Protokoll mit PASS/FAIL/SKIP pro Pruefpunkt.                                                                                     | Alle Checks bestanden (0 FAIL)                                                                         |
| `encoder_test.py`      | 2 (Encoder)    | Ja                        | `ros2 run my_bot encoder_test.py`                                                        | ROS2-Node mit 4 Modi: (1) 10-Umdrehungen-Test zur TICKS_PER_REV-Bestimmung (3 Durchgaenge pro Rad), (2) Richtungstest (Vorzeichenkonvention), (3) Asymmetrie-Test (Links vs. Rechts), (4) Live-Anzeige. Subscribt /odom und rechnet Encoder-Ticks zurueck. Gibt empfohlene config.h-Werte und JSON-Protokoll aus.                                                                      | Ticks/Rev: 370-380, Reproduzierbarkeit < 2 Ticks zwischen Durchgaengen, Asymmetrie < 5 %               |
| `motor_test.py`        | 3 (Motoren)    | Ja                        | `ros2 run my_bot motor_test.py`                                                          | ROS2-Node mit 4 Modi: (a) Deadzone-Test (cmd_vel 0.0-0.2 in 0.01-Schritten), (b) Richtungstest (Einzelrad-Ansteuerung ueber Differentialkinematik), (c) Failsafe-Test (misst Timeout nach cmd_vel-Stopp, erwartet ~500 ms), (d) Rampen-Test (0 auf 0.4 m/s in 5 s). Publiziert /cmd_vel, subscribt /odom. Notaus per Ctrl+C. JSON- und Markdown-Export.                                | Deadzone 30-40, Failsafe 500 ms +/- 200 ms, Tracking-Error < 50 mm/s bei Zielgeschwindigkeit           |
| `pid_tuning.py`        | 4 (PID)        | Ja (Live) / Nein (Rosbag) | `ros2 run my_bot pid_tuning.py live` oder `python3 pid_tuning.py bag /pfad/rosbag`       | PID-Sprungantwort-Analyse: Sendet Sprung von 0 auf 0.4 m/s, zeichnet /odom 10 s auf. Berechnet Anstiegszeit (10%-90%), Ueberschwingen, Einschwingzeit (+/- 5%), stationaeren Regelfehler. Gibt Tuning-Empfehlungen und Matplotlib-Plot (pid_sprungantwort.png) aus. Erkennt Oszillationen ueber Nulldurchgangs-Analyse.                                                                | Anstiegszeit < 500 ms, Ueberschwingen < 15 %, Einschwingzeit < 1 s, Regelfehler < 5 %                  |
| `kinematic_test.py`    | 4 (Kinematik)  | Ja                        | `ros2 run my_bot kinematic_test.py`                                                      | ROS2-Node mit 3 Tests: (a) Geradeausfahrt 1 m (v=0.2 m/s, 5 s), (b) 90-Grad-Drehung (5x CW, 5x CCW, omega=pi/2 rad/s), (c) Kreisfahrt (v=0.2 m/s, omega=0.5 rad/s, R=0.4 m). Berechnet Strecken- und Winkelabweichungen in lokalen Koordinaten. JSON- und Markdown-Export. Einzelne Tests per Argument auswaehlbar (gerade/drehung/kreis).                                             | Streckenabweichung < 5 %, laterale Drift < 5 cm, Winkelabweichung < 5 Grad, CW/CCW-Asymmetrie < 3 Grad |
| `umbmark_analysis.py`  | 5 (UMBmark)    | Nein                      | `python3 umbmark_analysis.py` oder `python3 umbmark_analysis.py data.json`               | Standalone UMBmark-Auswertung nach Borenstein & Feng 1996 (Gl. 5.9-5.15): Eingabe von 5x CW und 5x CCW Endpositionen (x,y in mm) nach 4x4 m Quadratfahrt. Berechnet Schwerpunkte, Fehlerwinkel alpha/beta, Korrekturfaktoren E_d (Raddurchmesser-Verhaeltnis) und E_b (Spurbreite-Korrektor), korrigierte WHEEL_BASE/WHEEL_RADIUS. Gibt Copy-Paste config.h-Werte und Scatterplot aus. | E_max,syst-Reduktion >= Faktor 10 nach Kalibrierung                                                    |
| `slam_validation.py`   | 6 (SLAM)       | Ja                        | `ros2 run my_bot slam_validation.py --live --duration 120` oder `--bag /pfad/rosbag`     | ATE-Berechnung (Absolute Trajectory Error) zwischen SLAM-korrigierter Pose (map->base_link via TF) und reiner Odometrie (/odom). TF-Ketten-Verifikation (map->odom->base_link->laser). Live-Modus: Subscribt /odom und TF fuer konfigurierbare Dauer. Erzeugt Markdown-Report, Trajektorien-Vergleichsplot und ATE-ueber-Zeit-Plot.                                                    | ATE (RMSE) < 0.20 m                                                                                    |
| `nav_test.py`          | 6 (Navigation) | Ja                        | `ros2 run my_bot nav_test.py`                                                            | Automatisierter Waypoint-Navigationstest: Sendet 4 Waypoints (2x2 m Rechteck) ueber Nav2 NavigateToPose Action-Server. Misst Positionsfehler (xy) und Orientierungsfehler (yaw) pro Waypoint. Configurable Timeout pro Waypoint (Standard: 60 s). Erzeugt Markdown-Report und JSON-Export mit Soll/Ist-Vergleich.                                                                      | xy-Fehler < 10 cm, Gier-Fehler < 0.15 rad (~8.6 Grad) pro Waypoint                                     |
| `docking_test.py`      | 6 (Docking)    | Ja                        | `ros2 run my_bot docking_test.py`                                                        | 10-Versuch ArUco-Docking-Test: Interaktiver Ablauf -- Benutzer positioniert Roboter ~1.5 m vor Marker (ID 42, DICT_4X4_50), Skript steuert Suche/Annaeherung/Docking. Zustandsmaschine (SEARCHING->APPROACHING->DOCKED/TIMEOUT). Visual Servoing mit Kp-Regelung auf Marker-Zentrierung. 3 s Rueckwaertsfahrt nach jedem Versuch. Timeout 60 s pro Versuch.                            | Erfolgsquote >= 80 % (8/10 Versuche)                                                                   |
| `validation_report.py` | 9 (Report)     | Nein                      | `python3 validation_report.py` oder `python3 validation_report.py /pfad/zu/ergebnissen/` | Gesamt-Validierungsbericht-Generator: Liest JSON-Ergebnisdateien aller vorherigen Tests, bewertet 14 Einzelkriterien gegen definierte Akzeptanzgrenzen, ordnet Ergebnisse den drei Forschungsfragen (FF1: Echtzeit, FF2: Praezision, FF3: Docking) zu. Gibt Markdown-Report mit PASS/FAIL/AUSSTEHEND-Status pro Kriterium und Gesamtbewertung aus.                                     | Alle 14 Kriterien PASS, keine AUSSTEHEND                                                               |

---

## Anhang C: Referenztabelle Quelldateien

Die folgende Tabelle listet alle relevanten Dateien des AMR-Projekts mit ihren Pfaden (relativ zum Projekt-Root) und einer Kurzbeschreibung.

### C.1 ESP32 Firmware

| Datei                     | Pfad                                                   | Beschreibung                                                                                                         |
|---------------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| main.cpp                  | `amr/esp32_amr_firmware/src/main.cpp`                  | FreeRTOS-Tasks (Core 0: micro-ROS, Core 1: PID 50 Hz), Subscriber/Publisher, Safety-Mechanismen (Failsafe, Watchdog) |
| robot_hal.hpp             | `amr/esp32_amr_firmware/src/robot_hal.hpp`             | Hardware-Abstraktion: GPIO-Init, Encoder-ISR (A-only, IRAM_ATTR), PWM-Steuerung (Dual-PWM), Deadzone-Kompensation    |
| pid_controller.hpp        | `amr/esp32_amr_firmware/src/pid_controller.hpp`        | PID-Regler mit Anti-Windup, Ausgang begrenzt auf [-1.0, 1.0]                                                         |
| diff_drive_kinematics.hpp | `amr/esp32_amr_firmware/src/diff_drive_kinematics.hpp` | Vorwaerts- und Inverskinematik fuer Differentialantrieb, Odometrie-Update mit Winkel-Normalisierung                  |
| platformio.ini            | `amr/esp32_amr_firmware/platformio.ini`                | Build-Konfiguration: Board, Framework, Build-Flags, micro-ROS-Bibliothek                                             |

### C.2 Zentrale Konfiguration

| Datei    | Pfad                | Beschreibung                                                                                                                                                                                                                              |
|----------|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| config.h | `hardware/config.h` | Single Source of Truth: Pin-Mapping, kinematische Parameter (Raddurchmesser 65 mm, Spurbreite 178 mm), Encoder-Kalibrierung, PWM-Konfiguration (20 kHz, 8-bit), Safety-Timing (Failsafe 500 ms), Compile-Time-Validierung (static_assert) |

### C.3 Hardware-Dokumentation

| Datei                  | Pfad                                   | Beschreibung                                                                                                                     |
|------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| hardware-setup.md      | `hardware/hardware-setup.md`           | Physischer Aufbau: Stromversorgung, Verkabelung, Pin-Mapping, Inbetriebnahme-Messpunkte                                          |
| 08_validierungsplan.md | `hardware/docs/08_validierungsplan.md` | V-Modell Validierungsplan: Pre-Flash-Checkliste, Encoder-, Motor-, Kinematik-, UMBmark-, PID-, micro-ROS-Tests, Abnahmekriterien |

### C.4 ROS2-Paket (Raspberry Pi)

| Datei                           | Pfad                                                                | Beschreibung                                                                                                                                              |
|---------------------------------|---------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| nav2_params.yaml                | `amr/pi5/ros2_ws/src/my_bot/config/nav2_params.yaml`                | Nav2-Stack-Konfiguration: AMCL, Regulated Pure Pursuit Controller (0,4 m/s), Navfn-Planer, Costmaps, Recovery-Behaviors                                   |
| mapper_params_online_async.yaml | `amr/pi5/ros2_ws/src/my_bot/config/mapper_params_online_async.yaml` | SLAM Toolbox: Ceres-Solver, 5 cm Aufloesung, Loop Closure                                                                                                 |
| full_stack.launch.py            | `amr/pi5/ros2_ws/src/my_bot/launch/full_stack.launch.py`            | Kombiniertes Launch-File: micro-ROS Agent + SLAM Toolbox + Nav2 + RViz2, konfigurierbar ueber Launch-Parameter (use_nav, use_rviz, use_slam, serial_port) |
| aruco_docking.py                | `amr/pi5/ros2_ws/src/my_bot/scripts/aruco_docking.py`               | Visual Servoing mit ArUco-Markern (OpenCV cv2.aruco.ArucoDetector API >= 4.7) fuer mechanischen Ladekontakt                                               |

### C.5 Validierungsskripte

| Datei                | Pfad                               | ROS2 erforderlich | Beschreibung                                                                                                      |
|----------------------|------------------------------------|-------------------|-------------------------------------------------------------------------------------------------------------------|
| pre_flight_check.py  | `amr/scripts/pre_flight_check.py`  | Nein              | Interaktive Hardware-Checkliste: USB, Spannung, Pins, Firmware. Erzeugt Markdown-Protokoll                        |
| encoder_test.py      | `amr/scripts/encoder_test.py`      | Ja                | 10-Umdrehungen-Test, Richtungstest, Asymmetrie-Test, Live-Anzeige. Erzeugt JSON-Protokoll                         |
| motor_test.py        | `amr/scripts/motor_test.py`        | Ja                | Deadzone-, Richtungs-, Failsafe- und Rampen-Test. Erzeugt JSON + Markdown                                         |
| pid_tuning.py        | `amr/scripts/pid_tuning.py`        | Ja                | PID-Sprungantwort-Analyse: Anstiegszeit, Ueberschwingen, Einschwingzeit                                           |
| kinematic_test.py    | `amr/scripts/kinematic_test.py`    | Ja                | Geradeaus-, Dreh- und Kreisfahrt-Verifikation                                                                     |
| umbmark_analysis.py  | `amr/scripts/umbmark_analysis.py`  | Nein              | UMBmark-Auswertung nach Borenstein (1996): Korrekturfaktoren E_d und E_b berechnen (Standalone, numpy/matplotlib) |
| slam_validation.py   | `amr/scripts/slam_validation.py`   | Ja                | Absolute Trajectory Error (ATE) und TF-Ketten-Pruefung                                                            |
| nav_test.py          | `amr/scripts/nav_test.py`          | Ja                | Waypoint-Navigation mit Positionsfehler-Messung (xy und Gier)                                                     |
| docking_test.py      | `amr/scripts/docking_test.py`      | Ja                | 10-Versuch ArUco-Docking-Test: Erfolgsquote, lateraler Versatz, Orientierungsfehler                               |
| validation_report.py | `amr/scripts/validation_report.py` | Nein              | Gesamt-Report aus JSON-Ergebnissen aller Validierungsskripte (Standalone)                                         |
