# 05 -- Firmware-Migrationsplan

**Dokumenttyp:** Migrationsplan (IST → SOLL)
**Stand:** 2026-02-11
**Source of Truth:** `hardware/config.h` (v1.0.0, 2025-12-12), `hardware/hardware-setup.md`
**Betroffene Firmware:** `technische_umsetzung/esp32_amr_firmware/`

---

## 1. Uebersicht der Diskrepanzen

Die bestehende ESP32-Firmware (`technische_umsetzung/esp32_amr_firmware/`) wurde fuer einen anderen Roboter entwickelt als den tatsaechlich aufgebauten AMR. Saemtliche Hardware-Annahmen in der Firmware -- MCU-Typ, Pin-Zuordnungen, kinematische Parameter, Encoder-Konfiguration und Motortreiber-Ansteuerung -- weichen von der realen Verdrahtung ab. Eine direkte Ausfuehrung der aktuellen Firmware auf der verbauten Hardware wuerde zu Fehlfunktionen fuehren: falsche GPIO-Pins wuerden angesprochen, die Odometrie waere um Faktor ~3,8 falsch skaliert, und die kinematischen Berechnungen wuerden fehlerhafte Trajektorien erzeugen.

### 1.1 Diskrepanz-Tabelle

| Parameter | Firmware (IST / FALSCH) | Hardware (SOLL / KORREKT) | Auswirkung |
|---|---|---|---|
| MCU / Board | ESP32 (LX6), `esp32dev` | XIAO ESP32-S3 (LX7), `seeed_xiao_esp32s3` | Kompilierung fuer falsche Architektur |
| Raddurchmesser | 64 mm (r = 32,0 mm) | 65 mm (r = 32,5 mm) | Odometrie-Fehler ~1,6 % |
| Spurbreite | 145 mm | 178 mm | Drehwinkel-Fehler ~22,7 % |
| Encoder Ticks/Rev | 1440 (Quadratur A+B) | 374,3 / 373,6 (A-only) | Geschwindigkeitsberechnung Faktor ~3,85 falsch |
| Encoder-Typ | Quadratur (A+B, Richtungserkennung) | A-only (nur Phase A, B isoliert) | ISR-Logik inkompatibel |
| GPIO-Pins Motor | 25, 26, 32, 33 (ESP32 GPIO) | D0, D1, D2, D3 (XIAO-Pinout) | Falsche Pins angesprochen |
| GPIO-Pins Encoder | 18, 19, 22, 23 (A+B) | D6, D7 (nur A) | Falsche Pins, 4 statt 2 Pins |
| PWM-Kanaele | 0, 1, 2, 3 (sequenziell) | 1, 0, 3, 2 (getauscht) + CH4 LED | Drehrichtung invertiert |
| PWM-Kanaele Motor | 2 Kanaele (IN1/IN2 pro Motor) | 2 Kanaele (A/B pro Motor, Dual-PWM) | Logik kompatibel, Zuordnung falsch |
| Motortreiber-Typ | Generische H-Bruecke (DIR+PWM) | Cytron MDD3A (Dual-PWM) | Ansteuerungslogik anpassen |
| Motor-Deadzone | Nicht vorhanden | PWM_DEADZONE = 35 | Motoren laufen bei niedrigem PWM nicht an |
| LED-Steuerung | Nicht vorhanden | LEDC CH4 auf D10 (IRLZ24N) | Feature fehlt |
| I2C (IMU) | Nicht vorhanden | D4 (SDA), D5 (SCL), Adresse 0x68 | Feature fehlt |
| Servo-Pins | Nicht vorhanden | D8 (Pan), D9 (Tilt) | Feature fehlt |
| micro-ROS Transport | Serial (generisch) | USB CDC (ESP32-S3 nativ) | Transport-Konfiguration anpassen |
| Failsafe-Timeout | Nicht vorhanden | 1000 ms | Sicherheitsfunktion fehlt |

### 1.2 Schweregrad-Bewertung

| Schweregrad | Betroffene Dateien | Beschreibung |
|---|---|---|
| **Kritisch** | `platformio.ini` | Falsches Board -- Firmware kompiliert nicht fuer die Ziel-MCU |
| **Kritisch** | `robot_hal.hpp` | Alle GPIO-Pins und Encoder-ISR-Logik falsch |
| **Kritisch** | `main.cpp` | Kinematische Parameter und Encoder-Skalierung falsch |
| **Hoch** | `diff_drive_kinematics.hpp` | Parameter werden von main.cpp uebergeben, Modul selbst korrekt |
| **Niedrig** | `pid_controller.hpp` | Keine Hardware-Abhaengigkeiten, keine Aenderung noetig |

---

## 2. Aenderungen pro Firmware-Datei

### 2.1 `platformio.ini` -- Board-Konfiguration

**Datei:** `technische_umsetzung/esp32_amr_firmware/platformio.ini`

#### IST-Zustand (Zeile 1-3)

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
```

#### SOLL-Zustand

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
```

#### Aenderungsbeschreibung

1. **Environment-Name** aendern: `esp32dev` → `seeed_xiao_esp32s3`
2. **Board** aendern: `esp32dev` → `seeed_xiao_esp32s3` -- dies konfiguriert automatisch den korrekten LX7-Compiler, die Flash-Groesse und die USB-CDC-Unterstuetzung des ESP32-S3
3. **config.h einbinden**: Neuen Build-Flag hinzufuegen, damit `config.h` aus `hardware/` als zentrale Konfiguration referenziert wird (siehe Abschnitt 3)
4. **USB CDC aktivieren**: Der ESP32-S3 nutzt nativen USB fuer Serial, daher muss ggf. `build_flags = -DARDUINO_USB_CDC_ON_BOOT=1` ergaenzt werden

#### Vollstaendiger SOLL-Zustand der Datei

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

---

### 2.2 `robot_hal.hpp` -- Hardware-Abstraktionsschicht

**Datei:** `technische_umsetzung/esp32_amr_firmware/src/robot_hal.hpp`

Dies ist die Datei mit den gravierendsten Abweichungen. Nahezu jede Zeile enthaelt Hardware-spezifische Definitionen, die vollstaendig ersetzt werden muessen.

#### 2.2.1 Pin-Definitionen

**IST-Zustand (Zeilen 4-13):**

```cpp
#define ENC_LEFT_A 18
#define ENC_LEFT_B 19
#define ENC_RIGHT_A 22
#define ENC_RIGHT_B 23

#define MOT_LEFT_IN1 25
#define MOT_LEFT_IN2 26
#define MOT_RIGHT_IN1 32
#define MOT_RIGHT_IN2 33
```

**SOLL-Zustand (aus config.h):**

```cpp
// Wird durch #include "config.h" ersetzt:
// PIN_MOTOR_LEFT_A   = D0  (GPIO1)
// PIN_MOTOR_LEFT_B   = D1  (GPIO2)
// PIN_MOTOR_RIGHT_A  = D2  (GPIO3)
// PIN_MOTOR_RIGHT_B  = D3  (GPIO4)
// PIN_ENC_LEFT_A     = D6  (GPIO43)
// PIN_ENC_RIGHT_A    = D7  (GPIO44)
```

**Aenderung:** Alle `#define`-Zeilen fuer Pins entfernen und stattdessen `#include "config.h"` verwenden. Die Encoder-Pins B (19, 23) entfallen vollstaendig, da nur A-only verwendet wird.

#### 2.2.2 PWM-Konfiguration

**IST-Zustand (Zeilen 15-18):**

```cpp
#define PWM_FREQ 20000
#define PWM_RES 8
#define PWM_CH_L 0
#define PWM_CH_R 1
```

**SOLL-Zustand (aus config.h):**

```cpp
// Wird durch config.h bereitgestellt:
// MOTOR_PWM_FREQ  = 20000
// MOTOR_PWM_BITS  = 8
// PWM_CH_LEFT_A   = 1  (getauscht)
// PWM_CH_LEFT_B   = 0  (getauscht)
// PWM_CH_RIGHT_A  = 3  (getauscht)
// PWM_CH_RIGHT_B  = 2  (getauscht)
```

**Aenderung:** Die Firmware verwendet derzeit 2 PWM-Kanaele pro Motor (IN1/IN2, Kanaele 0-3). Dies ist konzeptionell kompatibel mit dem Dual-PWM-Modus des Cytron MDD3A, jedoch muessen die Kanalzuordnungen auf die getauschten Werte aus config.h umgestellt werden. Die bisherigen Defines `PWM_CH_L` und `PWM_CH_R` muessen durch die vier separaten Kanaele `PWM_CH_LEFT_A`, `PWM_CH_LEFT_B`, `PWM_CH_RIGHT_A`, `PWM_CH_RIGHT_B` ersetzt werden.

#### 2.2.3 Encoder-ISR (Interrupt Service Routines)

**IST-Zustand (Zeilen 23-35):**

```cpp
void IRAM_ATTR isr_enc_left() {
    if (digitalRead(ENC_LEFT_B) == digitalRead(ENC_LEFT_A))
        encoder_left_count++;
    else
        encoder_left_count--;
}

void IRAM_ATTR isr_enc_right() {
    if (digitalRead(ENC_RIGHT_B) == digitalRead(ENC_RIGHT_A))
        encoder_right_count++;
    else
        encoder_right_count--;
}
```

**Problem:** Die aktuelle ISR nutzt Quadratur-Dekodierung (vergleicht Phase A mit Phase B zur Richtungserkennung). Im realen Aufbau ist Phase B nicht angeschlossen (isoliert). Ein `digitalRead()` auf einen nicht angeschlossenen Pin liefert undefinierte Werte.

**SOLL-Zustand (A-only mit richtungsabhaengigem Zaehlen):**

```cpp
// Drehrichtung wird aus der PWM-Ansteuerung abgeleitet,
// nicht aus dem Encoder-Signal.
volatile int8_t enc_left_dir = 1;   // +1 vorwaerts, -1 rueckwaerts
volatile int8_t enc_right_dir = 1;

void IRAM_ATTR isr_enc_left() {
    encoder_left_count += enc_left_dir;
}

void IRAM_ATTR isr_enc_right() {
    encoder_right_count += enc_right_dir;
}
```

**Aenderung:**
- Quadratur-Logik (A/B-Vergleich) entfernen
- Richtungsvariablen einfuehren, die von der Motoransteuerung gesetzt werden
- `digitalRead(ENC_LEFT_B)` und `digitalRead(ENC_RIGHT_B)` entfernen
- Pins B (19, 23) werden weder konfiguriert noch gelesen

#### 2.2.4 `init()`-Methode

**IST-Zustand (Zeilen 53-71):**

```cpp
void init() {
    pinMode(ENC_LEFT_A, INPUT_PULLUP);
    pinMode(ENC_LEFT_B, INPUT_PULLUP);
    pinMode(ENC_RIGHT_A, INPUT_PULLUP);
    pinMode(ENC_RIGHT_B, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ENC_LEFT_A), isr_enc_left, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC_RIGHT_A), isr_enc_right, CHANGE);

    ledcSetup(0, PWM_FREQ, PWM_RES);
    ledcSetup(1, PWM_FREQ, PWM_RES);
    ledcSetup(2, PWM_FREQ, PWM_RES);
    ledcSetup(3, PWM_FREQ, PWM_RES);
    ledcAttachPin(MOT_LEFT_IN1, 0);
    ledcAttachPin(MOT_LEFT_IN2, 1);
    ledcAttachPin(MOT_RIGHT_IN1, 2);
    ledcAttachPin(MOT_RIGHT_IN2, 3);
}
```

**SOLL-Zustand:**

```cpp
void init() {
    // Encoder: nur Phase A, Pins aus config.h
    pinMode(PIN_ENC_LEFT_A, INPUT_PULLUP);
    pinMode(PIN_ENC_RIGHT_A, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_ENC_LEFT_A), isr_enc_left, RISING);
    attachInterrupt(digitalPinToInterrupt(PIN_ENC_RIGHT_A), isr_enc_right, RISING);

    // Motor-PWM: 4 Kanaele mit getauschter Zuordnung aus config.h
    ledcSetup(PWM_CH_LEFT_A, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
    ledcSetup(PWM_CH_LEFT_B, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
    ledcSetup(PWM_CH_RIGHT_A, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
    ledcSetup(PWM_CH_RIGHT_B, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
    ledcAttachPin(PIN_MOTOR_LEFT_A, PWM_CH_LEFT_A);
    ledcAttachPin(PIN_MOTOR_LEFT_B, PWM_CH_LEFT_B);
    ledcAttachPin(PIN_MOTOR_RIGHT_A, PWM_CH_RIGHT_A);
    ledcAttachPin(PIN_MOTOR_RIGHT_B, PWM_CH_RIGHT_B);

    // LED-PWM: Kanal 4 auf D10
    ledcSetup(LED_PWM_CHANNEL, LED_PWM_FREQ, LED_PWM_BITS);
    ledcAttachPin(PIN_LED_MOSFET, LED_PWM_CHANNEL);
}
```

**Aenderungen im Detail:**
- `ENC_LEFT_B` und `ENC_RIGHT_B` komplett entfernen (keine `pinMode`, kein `attachInterrupt`)
- Interrupt-Modus von `CHANGE` auf `RISING` aendern (A-only zaehlt nur steigende Flanken)
- Alle Pin-Referenzen durch config.h-Defines ersetzen
- PWM-Kanalzuordnungen gemaess config.h (getauschte A/B-Kanaele) verwenden
- LED-PWM-Kanal (CH4 auf D10) hinzufuegen

#### 2.2.5 `driveMotor()`-Methode

**IST-Zustand (Zeilen 41-49):**

```cpp
void driveMotor(int ch_in1, int ch_in2, float speed) {
    int duty = constrain(abs(speed) * 255, 0, 255);
    if (speed > 0) {
        ledcWrite(ch_in1, duty);
        ledcWrite(ch_in2, 0);
    } else {
        ledcWrite(ch_in1, 0);
        ledcWrite(ch_in2, duty);
    }
}
```

**SOLL-Zustand (mit Deadzone-Kompensation):**

```cpp
void driveMotor(int ch_a, int ch_b, float speed, volatile int8_t &dir) {
    int duty = constrain(abs(speed) * MOTOR_PWM_MAX, 0, MOTOR_PWM_MAX);
    // Deadzone-Kompensation: Werte unter PWM_DEADZONE erzeugen keine Bewegung
    if (duty > 0 && duty < PWM_DEADZONE) {
        duty = PWM_DEADZONE;
    }
    if (speed > 0) {
        dir = 1;
        ledcWrite(ch_a, duty);
        ledcWrite(ch_b, 0);
    } else if (speed < 0) {
        dir = -1;
        ledcWrite(ch_a, 0);
        ledcWrite(ch_b, duty);
    } else {
        ledcWrite(ch_a, 0);
        ledcWrite(ch_b, 0);
    }
}
```

**Aenderungen:**
- `PWM_DEADZONE`-Kompensation hinzufuegen (Wert 35 aus config.h)
- Richtungsvariable `dir` setzen, die von der Encoder-ISR verwendet wird
- Magic Number `255` durch `MOTOR_PWM_MAX` ersetzen
- Expliziter Stillstands-Fall (`speed == 0`)

#### 2.2.6 `setMotors()`-Methode

**IST-Zustand (Zeilen 80-83):**

```cpp
void setMotors(float pwm_l, float pwm_r) {
    driveMotor(0, 1, pwm_l);
    driveMotor(2, 3, pwm_r);
}
```

**SOLL-Zustand:**

```cpp
void setMotors(float pwm_l, float pwm_r) {
    driveMotor(PWM_CH_LEFT_A, PWM_CH_LEFT_B, pwm_l, enc_left_dir);
    driveMotor(PWM_CH_RIGHT_A, PWM_CH_RIGHT_B, pwm_r, enc_right_dir);
}
```

**Aenderung:** Hardcodierte Kanalnummern (0, 1, 2, 3) durch config.h-Defines ersetzen. Richtungsvariablen fuer Encoder-ISR uebergeben.

---

### 2.3 `main.cpp` -- Hauptprogramm und Regelschleife

**Datei:** `technische_umsetzung/esp32_amr_firmware/src/main.cpp`

#### 2.3.1 Kinematische Parameter

**IST-Zustand (Zeilen 17-18):**

```cpp
DiffDriveKinematics kinematics(0.032,
                               0.145); // <-- HIER DEINE WERTE (Radius, Spur)
```

**SOLL-Zustand:**

```cpp
DiffDriveKinematics kinematics(WHEEL_RADIUS, WHEEL_BASE);
```

**Aenderung:** Hardcodierte Werte `0.032` (Radradius) und `0.145` (Spurbreite) durch config.h-Defines ersetzen. Die korrekten Werte sind:
- `WHEEL_RADIUS` = 0,0325 m (statt 0,032 m -- Differenz 0,5 mm)
- `WHEEL_BASE` = 0,178 m (statt 0,145 m -- Differenz 33 mm)

Die Spurbreiten-Abweichung von 22,7 % wuerde zu erheblichen Fehlern bei Drehbewegungen fuehren.

#### 2.3.2 Encoder-Tick-Umrechnung (Regelschleife)

**IST-Zustand (Zeilen 44-46):**

```cpp
float ml =
    ((tl - ptl) / 1440.0) * 2 * PI / 0.02; // 1440 Ticks/Rev anpassen!
float mr = ((tr - ptr) / 1440.0) * 2 * PI / 0.02;
```

**Problem:** Der Divisor `1440.0` entspricht der Quadratur-Encoder-Aufloesung (360 Pulse * 4 Flanken = 1440). Die reale Hardware hat nur ~374 Ticks pro Umdrehung (A-only, steigende Flanke). Die berechnete Winkelgeschwindigkeit waere um Faktor ~3,85 zu niedrig.

**SOLL-Zustand:**

```cpp
float ml =
    ((tl - ptl) / TICKS_PER_REV_LEFT) * 2 * PI / 0.02;
float mr =
    ((tr - ptr) / TICKS_PER_REV_RIGHT) * 2 * PI / 0.02;
```

**Aenderung:** Hardcodierte `1440.0` durch `TICKS_PER_REV_LEFT` (374,3) bzw. `TICKS_PER_REV_RIGHT` (373,6) aus config.h ersetzen. Dabei werden bewusst asymmetrische Werte fuer Links/Rechts verwendet, da die realen Encoder geringfuegig unterschiedliche Aufloesung aufweisen.

#### 2.3.3 Odometrie-Berechnung (Geschwindigkeit)

**IST-Zustand (Zeilen 83-84):**

```cpp
shared.ov = (ml + mr) * 0.032 / 2;
shared.ow = (mr - ml) * 0.032 / 0.145;
```

**SOLL-Zustand:**

```cpp
shared.ov = (ml + mr) * WHEEL_RADIUS / 2;
shared.ow = (mr - ml) * WHEEL_RADIUS / WHEEL_BASE;
```

**Aenderung:** Hardcodierte Werte `0.032` und `0.145` durch `WHEEL_RADIUS` (0,0325) und `WHEEL_BASE` (0,178) ersetzen. Diese Berechnung ist redundant zur `DiffDriveKinematics::updateOdometry()` und koennte langfristig durch Nutzung des `RobotState`-Rueckgabewerts ersetzt werden.

#### 2.3.4 Regelschleifenfrequenz

**IST-Zustand (Zeile 87):**

```cpp
vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(20)); // 50 Hz
```

**SOLL-Zustand:** Der Wert `20` ms (50 Hz) weicht von der `LOOP_RATE_HZ = 100` in config.h ab (100 Hz = 10 ms). Da config.h keinen `LOOP_RATE_HZ`-Define enthaelt, muss dieser entweder in config.h ergaenzt werden oder der bestehende Wert beibehalten werden. Die Bachelorarbeit beschreibt 50 Hz (20 ms) als Regelfrequenz.

**Empfehlung:** Den Wert bei 20 ms (50 Hz) belassen, sofern die PID-Regelung bei dieser Rate stabil funktioniert. Die Zykluszeit `0.02` in den Berechnungen (Zeilen 45, 46, 60, 75, 76, 77) muss konsistent bleiben.

#### 2.3.5 config.h einbinden

**Neue Zeile am Anfang der Datei einfuegen:**

```cpp
#include "config.h"
```

Dies muss vor den anderen Includes stehen, damit alle Defines in den nachfolgenden Headern verfuegbar sind.

---

### 2.4 `diff_drive_kinematics.hpp` -- Kinematik-Modul

**Datei:** `technische_umsetzung/esp32_amr_firmware/src/diff_drive_kinematics.hpp`

#### Analyse

Das Modul selbst enthaelt keine hardcodierten Werte. Radradius (`r`) und Spurbreite (`l`) werden als Konstruktorparameter uebergeben (Zeile 20-21):

```cpp
DiffDriveKinematics(float wheel_radius, float wheel_sep)
    : r(wheel_radius), l(wheel_sep), odom{0, 0, 0} {}
```

Die Berechnung der inversen und Vorwaertskinematik (Zeilen 23-39) ist mathematisch korrekt und nicht von der Hardware abhaengig.

#### Aenderungsbedarf

**Keine direkte Aenderung noetig.** Die korrekten Parameter werden bereits durch die Aenderung in `main.cpp` (Abschnitt 2.3.1) ueber `WHEEL_RADIUS` und `WHEEL_BASE` uebergeben.

---

### 2.5 `pid_controller.hpp` -- PID-Regler

**Datei:** `technische_umsetzung/esp32_amr_firmware/src/pid_controller.hpp`

#### Analyse

Der PID-Regler ist ein reines Software-Modul ohne Hardware-Abhaengigkeiten. Die Klasse erhaelt Verstaerkungsfaktoren (`kp`, `ki`, `kd`) und Ausgangsgrenzen (`min_out`, `max_out`) als Konstruktorparameter.

**IST-Zustand in main.cpp (Zeilen 19-20):**

```cpp
PidController pid_l(1.5, 0.5, 0.0, -1.0, 1.0);
PidController pid_r(1.5, 0.5, 0.0, -1.0, 1.0);
```

#### Aenderungsbedarf

**Keine Aenderung am Modul noetig.** Die PID-Parameter (Kp=1,5, Ki=0,5, Kd=0,0) muessen jedoch nach der Migration **neu abgestimmt** werden, da sich durch die geaenderte Encoder-Aufloesung (374 statt 1440 Ticks) und die Deadzone-Kompensation das Regelverhalten grundlegend aendert. Die Abstimmung erfolgt experimentell nach der Inbetriebnahme.

---

## 3. Integration von config.h in den Firmware-Build

### 3.1 Aktuelle Situation

Die Datei `config.h` liegt unter `hardware/config.h` und ist nicht in den Firmware-Build-Prozess eingebunden. Saemtliche Hardware-Parameter sind stattdessen als Literalwerte direkt in den Firmware-Quelldateien hardcodiert.

### 3.2 Ziel-Architektur

`config.h` wird zur zentralen, einzigen Quelle aller Hardware-Parameter (Single Source of Truth). Alle Firmware-Dateien referenzieren ausschliesslich Defines aus `config.h`.

### 3.3 Umsetzung

**Schritt 1 -- Include-Pfad in platformio.ini:**

Der Build-Flag `-I../../hardware` (relativ zum `src/`-Verzeichnis, aufgeloest relativ zum Projekt-Root) fuegt den Ordner `hardware/` als Include-Verzeichnis hinzu:

```ini
build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1
    -I../../hardware
```

**Hinweis:** Der Include-Pfad muss relativ zum Projekt-Root der PlatformIO-Umgebung angegeben werden. Da `platformio.ini` in `technische_umsetzung/esp32_amr_firmware/` liegt und `config.h` in `hardware/`, ist der relative Pfad `../../hardware`.

**Schritt 2 -- Include in Quelldateien:**

In `main.cpp` und `robot_hal.hpp` wird am Anfang eingefuegt:

```cpp
#include "config.h"
```

**Schritt 3 -- Hardcodierte Werte entfernen:**

Alle lokalen `#define`-Anweisungen fuer Pins, PWM-Konfiguration und kinematische Parameter in `robot_hal.hpp` werden entfernt. Sie werden durch die Defines in `config.h` ersetzt.

### 3.4 Fehlende Defines in config.h

Die folgenden Parameter werden in der Firmware verwendet, sind aber aktuell nicht in `config.h` definiert und sollten ergaenzt werden:

| Parameter | Vorgeschlagener Define | Wert | Begruendung |
|---|---|---|---|
| Failsafe-Timeout | `FAILSAFE_TIMEOUT_MS` | 1000 | Motoren stoppen, wenn kein cmd_vel empfangen |
| Regelschleifenrate | `CONTROL_LOOP_HZ` | 50 | Frequenz der PID-Regelschleife |
| Odometrie-Publishrate | `ODOM_PUBLISH_HZ` | 20 | Frequenz der Odometrie-Veroeffentlichung |
| Maximale Beschleunigung | `MAX_ACCEL_RAD_S2` | 5.0 | Rampe fuer Soll-Geschwindigkeit |

---

## 4. Reihenfolge der Aenderungen

Die Migration muss in einer definierten Reihenfolge durchgefuehrt werden, da Abhaengigkeiten zwischen den Dateien bestehen. Ein falsches Vorgehen kann zu einem nicht-kompilierbaren Zustand fuehren.

### Phase 1: Build-Infrastruktur (Voraussetzung fuer alles weitere)

| Schritt | Datei | Aenderung | Validierung |
|---|---|---|---|
| 1.1 | `platformio.ini` | Board auf `seeed_xiao_esp32s3` aendern, USB-CDC-Flag setzen | `pio run` kompiliert ohne Board-Fehler |
| 1.2 | `platformio.ini` | Include-Pfad `-I../../hardware` hinzufuegen | `#include "config.h"` in Quelldateien aufloesbar |
| 1.3 | `config.h` | Fehlende Defines ergaenzen (FAILSAFE_TIMEOUT_MS etc.) | Header ist vollstaendig |

### Phase 2: Hardware-Abstraktionsschicht

| Schritt | Datei | Aenderung | Validierung |
|---|---|---|---|
| 2.1 | `robot_hal.hpp` | `#include "config.h"` hinzufuegen | Kompilierung erfolgreich |
| 2.2 | `robot_hal.hpp` | Alle lokalen Pin-Defines entfernen | Keine Doppeldefinitionen |
| 2.3 | `robot_hal.hpp` | Encoder-ISR auf A-only umstellen | Kompilierung erfolgreich |
| 2.4 | `robot_hal.hpp` | `init()` mit korrekten Pins und Kanaelen | Kompilierung erfolgreich |
| 2.5 | `robot_hal.hpp` | `driveMotor()` mit Deadzone und Richtung | Kompilierung erfolgreich |
| 2.6 | `robot_hal.hpp` | `setMotors()` mit config.h-Kanaelen | Kompilierung erfolgreich |

### Phase 3: Hauptprogramm

| Schritt | Datei | Aenderung | Validierung |
|---|---|---|---|
| 3.1 | `main.cpp` | `#include "config.h"` hinzufuegen | Kompilierung erfolgreich |
| 3.2 | `main.cpp` | Kinematik-Parameter durch Defines ersetzen | Kompilierung erfolgreich |
| 3.3 | `main.cpp` | Encoder-Ticks-Skalierung anpassen | Kompilierung erfolgreich |
| 3.4 | `main.cpp` | Odometrie-Berechnung mit Defines | Kompilierung erfolgreich |

### Phase 4: Inbetriebnahme und Kalibrierung

| Schritt | Aktion | Validierung |
|---|---|---|
| 4.1 | Firmware auf XIAO ESP32-S3 flashen | Upload erfolgreich (USB CDC) |
| 4.2 | Serieller Monitor pruefen | Boot-Meldung sichtbar |
| 4.3 | Encoder-Test: Raeder von Hand drehen | Ticks zaehlen in korrekter Richtung |
| 4.4 | Motor-Test: Einzelmotoren ansteuern | Drehrichtung korrekt (Vorwaerts/Rueckwaerts) |
| 4.5 | Deadzone pruefen | Motoren laufen bei PWM >= 35 an |
| 4.6 | Odometrie-Test: Geradeausfahrt 1 m | Gemessene Strecke entspricht ~1 m |
| 4.7 | PID-Abstimmung | Kp, Ki, Kd experimentell anpassen |
| 4.8 | micro-ROS Verbindung testen | cmd_vel empfangen, odom publiziert |
| 4.9 | UMBmark-Kalibrierung | Encoder-Ticks und Spurbreite fein abgleichen |

---

## 5. Risiken und Fallstricke

### 5.1 Kritische Risiken

| Risiko | Beschreibung | Gegenmassnahme |
|---|---|---|
| **GPIO-Konflikte ESP32-S3** | D6 (GPIO43) und D7 (GPIO44) sind auf dem XIAO ESP32-S3 die UART0-TX/RX-Pins. Die Nutzung als Encoder-Interrupt kann mit dem USB-CDC-Modus kollidieren, wenn UART0 nicht deaktiviert wird. | Pruefen, ob der ESP32-S3 im USB-CDC-Modus UART0 freigibt. Falls nicht: alternative Pins oder PCNT-Peripherie verwenden. |
| **micro-ROS Kompatibilitaet** | Die micro_ros_platformio-Bibliothek muss den ESP32-S3 (LX7) unterstuetzen. Aeltere Versionen unterstuetzen moeglicherweise nur den ESP32 (LX6). | Aktuelle Version der Bibliothek verwenden; ggf. auf ESP32-S3-Branch pruefen. |
| **USB CDC statt UART** | Der ESP32-S3 nutzt nativen USB fuer Serial, waehrend der ESP32 UART-ueber-USB-Bridge (CP2102) verwendet. Die `set_microros_serial_transports(Serial)` Funktion muss mit USB CDC kompatibel sein. | Transport-Konfiguration verifizieren; ggf. `HWCDC` statt `Serial` verwenden. |

### 5.2 Mittlere Risiken

| Risiko | Beschreibung | Gegenmassnahme |
|---|---|---|
| **Encoder-Richtung ohne Quadratur** | Bei A-only Encoder wird die Drehrichtung aus der PWM-Ansteuerung abgeleitet. Bei externen Kraeften (Schieben des Roboters) wird die Richtung falsch erfasst. | Fuer den aktuellen Einsatzzweck (motorgetriebene Fahrt) akzeptabel. Langfristig Phase B nachruesten. |
| **PID-Instabilitaet** | Durch die geaenderte Encoder-Aufloesung (374 statt 1440 Ticks) liefert der Ist-Wert gröbere Schritte. Die bestehenden PID-Parameter (Kp=1,5, Ki=0,5) muessen neu abgestimmt werden. | Zunaechst mit konservativen Werten starten (Kp=0,5, Ki=0,1, Kd=0,0) und schrittweise erhoehen. |
| **Deadzone-Sprung** | Die PWM-Deadzone von 35 erzeugt einen Unstetigkeitssprung (PWM springt von 0 direkt auf 35). Dies kann bei sehr niedrigen Geschwindigkeiten zu ruckartiger Bewegung fuehren. | Deadzone-Kompensation nur aktivieren, wenn tatsaechlich Bewegung gewuenscht ist (speed != 0). |

### 5.3 Niedrige Risiken

| Risiko | Beschreibung | Gegenmassnahme |
|---|---|---|
| **LEDC-API-Unterschiede** | Die Arduino-Core-Version fuer den ESP32-S3 kann eine aktualisierte LEDC-API haben (z.B. `ledcAttach()` statt `ledcSetup()` + `ledcAttachPin()`). | Arduino-Core-Version in platformio.ini pruefen und ggf. API-Aufrufe anpassen. |
| **Include-Pfad relativ** | Der relative Include-Pfad `-I../../hardware` funktioniert nur, wenn das PlatformIO-Projekt aus dem korrekten Verzeichnis gebaut wird. | Alternativer absoluter Pfad oder symbolischer Link als Fallback. |
| **Odometrie-Redundanz** | Die Geschwindigkeitsberechnung in `main.cpp` (Zeilen 83-84) und in `DiffDriveKinematics::updateOdometry()` ist redundant. | Langfristig die redundante Berechnung in main.cpp durch Nutzung des RobotState-Rueckgabewerts ersetzen. |

---

## 6. Zusammenfassung der Aenderungen

### 6.1 Aenderungsmatrix

| Datei | Aenderungsumfang | Zeilen betroffen | Prioritaet |
|---|---|---|---|
| `platformio.ini` | Board + Flags aendern | 3 von 15 | Kritisch (Phase 1) |
| `robot_hal.hpp` | Vollstaendige Ueberarbeitung | ~80 von 84 | Kritisch (Phase 2) |
| `main.cpp` | Parameter und Skalierung ersetzen | ~12 von 155 | Kritisch (Phase 3) |
| `diff_drive_kinematics.hpp` | Keine Aenderung | 0 von 40 | Keine |
| `pid_controller.hpp` | Keine Aenderung | 0 von 22 | Keine |
| `config.h` | Fehlende Defines ergaenzen | ~8 neue Zeilen | Hoch (Phase 1) |

### 6.2 Abhaengigkeitsgraph

```
platformio.ini (Board + Include-Pfad)
    |
    v
config.h (erweitert um fehlende Defines)
    |
    +---> robot_hal.hpp (Pins, PWM, ISR, Deadzone)
    |         |
    |         v
    +---> main.cpp (Kinematik, Encoder-Skalierung, Odometrie)
              |
              v
         Inbetriebnahme + PID-Tuning + UMBmark
```

---

*Quellen: config.h v1.0.0 (2025-12-12), hardware-setup.md (2025-12-19), Firmware-Quelldateien in technische_umsetzung/esp32_amr_firmware/src/, Hardware-Dokumentation 01-04*
