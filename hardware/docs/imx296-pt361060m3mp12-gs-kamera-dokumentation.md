# Raspberry Pi Global Shutter Kamera – IMX296 mit PT361060M3MP12 CS-Mount-Objektiv

> **Technische Dokumentation** – Machine-Vision-Kamerasystem für eingebettete Robotik  
> Kameramodul: Raspberry Pi Global Shutter Camera (Sony IMX296LQR-C)  
> Objektiv: PT361060M3MP12, 6 mm, CS-Mount, F1.2  
> Quellen: [Raspberry Pi Camera Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html), [Raspberry Pi GS Camera Product Brief (PDF)](https://datasheets.raspberrypi.com/gs-camera/gs-camera-product-brief.pdf), [Sony IMX296 Pregius Flyer (PDF)](https://www.sony-semicon.com/files/62/flyer_industry/IMX273_287_296_297_Flyer.pdf), [Arducam IMX296 Wiki](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Global-Shutter/1.58MP-IMX296/)

---

## 1 Übersicht

Die Raspberry Pi Global Shutter Camera basiert auf dem Sony IMX296LQR-C Bildsensor der Pregius-Familie (2. Generation). Im Gegensatz zu Rolling-Shutter-Sensoren, die das Bild zeilenweise auslesen, erfasst ein Global Shutter alle Pixel gleichzeitig. Dadurch entfallen typische Artefakte wie Jello-Effekt, Focal-Plane-Verzerrung und Streifenbildung bei Blitzlicht – entscheidende Vorteile für Machine-Vision-Anwendungen auf mobilen Robotern.

**Warum Global Shutter für AMR?**

Die Kombination aus artefaktfreier Aufnahme schnell bewegter Szenen, kurzen Belichtungszeiten (bis 30 µs) und externer Trigger-Fähigkeit macht den IMX296 zur bevorzugten Wahl für Anwendungen wie Hinderniserkennung bei Fahrt, Barcode-/QR-Code-Erfassung, visuelle Odometrie und synchronisierte Stereo-Aufnahmen.

---

## 2 Komponentenspezifikationen

### 2.1 Bildsensor: Sony IMX296LQR-C

| Parameter | Wert | Bemerkung |
|---|---|---|
| **Hersteller** | Sony Semiconductor Solutions | Pregius 2. Generation |
| **Sensortyp** | CMOS Active Pixel, Global Shutter | Alle Pixel belichten gleichzeitig |
| **Variante** | IMX296LQR-C (Farbe), IMX296LLR (Mono) | Rpi GS Camera = Farbversion |
| **Effektive Pixel** | 1456 × 1088 (1,58 Megapixel) | 1.584.448 Pixel |
| **Optisches Format** | Type 1/2.9 (Diagonale 6,3 mm) | – |
| **Pixelgröße** | 3,45 µm × 3,45 µm | Quadratisch |
| **Aktive Fläche** | 5,02 mm × 3,75 mm | H × V |
| **Farbfilter** | Bayer-Muster (RGGB) | Farbversion; Mono ohne Filter |
| **ADC-Auflösung** | 10 Bit (RAW10) | – |
| **Max. Bildrate (Vollbild)** | 60 fps | 1456 × 1088, RAW10 |
| **Min. Belichtungszeit** | 30 µs | Bei ausreichend Licht |
| **Max. Belichtungszeit** | 15,5 s | Raspberry Pi Treiber-Limit |
| **Empfindlichkeit** | Hohe QE im sichtbaren Bereich | Pregius-Technologie |
| **NIR-Empfindlichkeit** | Moderat (geringer als Pregius S) | – |
| **Rauschverhalten** | Niedriger Dunkelstrom, niedriges Ausleserauschen | – |
| **Schnittstelle (Sensor)** | MIPI CSI-2 (2 Lanes) | Auf RPi GS Camera Board |
| **Versorgung (Sensor)** | Analog 3,3 V, Digital 1,2 V, Interface 1,8 V | Dreifach-Versorgung |
| **Trigger-Modi** | Free-Running, External Trigger (Fast Trigger) | Via XTR-Pin |
| **Synchronisation** | XVS (Vertical Sync), XHS (Horizontal Sync) | Für Multi-Kamera-Sync |
| **Gehäuse (Sensor-IC)** | 138-Pin LGA | – |

### 2.2 Raspberry Pi Global Shutter Camera Board

| Parameter | Wert |
|---|---|
| **Art.-Nr.** | SC0926 |
| **Sensormodul** | Sony IMX296LQR-C (Farbe) |
| **Auflösung** | 1456 × 1088 Pixel (1,58 MP) |
| **Ausgabeformat** | RAW10 (Bayer) → libcamera/Picamera2 verarbeitet zu YUV/RGB/JPEG |
| **IR-Sperrfilter** | Hoya CM500, integriert (entfernbar, irreversibel) |
| **Objektivanschluss** | CS-Mount (+ C-CS-Adapter im Lieferumfang) |
| **Back-Focal-Length** | Einstellbar: 12,5 … 22,4 mm |
| **Ribbon-Kabel** | 150 mm, 22-Pin FPC (Typ Raspberry Pi Camera) |
| **Externe Trigger-Pads** | XTR, GND (1,8 V Logik!) |
| **Sync-Pads** | XVS, XHS, MAS (für Multi-Kamera-Synchronisation) |
| **Stativgewinde** | 1/4"-20 UNC |
| **Zertifizierungen** | FCC Part 15 Class B, EMC 2014/30/EU, RoHS 2011/65/EU |
| **Produktionsende** | Mindestens Januar 2032 |
| **Lieferumfang** | Kameramodul, C-CS-Adapter, Schraubendreher, 150 mm FPC-Kabel, Schutzabdeckung |

### 2.3 Objektiv: PT361060M3MP12

| Parameter | Wert |
|---|---|
| **Bezeichnung** | PT361060M3MP12 (Raspberry Pi SC0124) |
| **Typ** | Weitwinkelobjektiv, manueller Fokus |
| **Brennweite** | 6 mm |
| **Auflösung** | 3 Megapixel (optisch) |
| **Bildformat** | 1/2" |
| **Blende** | F1.2 … F16 (manuell einstellbar) |
| **Bildwinkel (1/2" Sensor)** | 63° diagonal |
| **Naheinstellgrenze (MOD)** | 0,20 m |
| **Rückfokallänge (BFL)** | 7,53 mm |
| **Anschluss** | CS-Mount (Auflagemaß 12,526 mm) |
| **Abmessungen** | ∅ 30,0 × 34,0 mm |
| **Gewicht** | 53 g |
| **Bedienung** | Manueller Fokus, manuelle Blende, Feststellschrauben |

---

## 3 Global Shutter vs. Rolling Shutter

### 3.1 Funktionsprinzip

```
Rolling Shutter                    Global Shutter (IMX296)
┌────────────────────┐             ┌────────────────────┐
│ Zeile 0 ─── t₀    │             │                    │
│ Zeile 1 ─── t₁    │             │  ALLE Pixel        │
│ Zeile 2 ─── t₂    │             │  belichten         │
│   ...      ...     │             │  gleichzeitig      │
│ Zeile N ─── tₙ    │             │  (t₀ = t₁ = tₙ)   │
│                    │             │                    │
│ tₙ − t₀ = Readout │             │  → Readout         │
│ (Verzerrungsfenster)│             │  (nach Belichtung) │
└────────────────────┘             └────────────────────┘

→ Bewegte Objekte                  → Bewegte Objekte
  werden verzerrt                    bleiben formtreu
```

### 3.2 Vergleich

| Eigenschaft | Rolling Shutter (z. B. IMX219, IMX708) | Global Shutter (IMX296) |
|---|---|---|
| Belichtung | Zeilenweise, sequenziell | Alle Pixel gleichzeitig |
| Focal-Plane-Verzerrung | Ja (bei schneller Bewegung) | Nein |
| Blitz-Artefakte | Ja (Banding) | Nein |
| Auflösung (typisch) | 8–16 MP | 1,58 MP |
| Pixelgröße | 1,12–1,55 µm | 3,45 µm |
| Empfindlichkeit pro Pixel | Niedrig (kleine Pixel) | Hoch (große Pixel) |
| Anwendungsprofil | Allgemeine Fotografie, Video | Machine Vision, Hochgeschwindigkeit |
| Externe Trigger-Unterstützung | Begrenzt | Vollständig (XTR) |

**Fazit für AMR:** Die niedrigere Auflösung des IMX296 ist kein Nachteil – im Gegenteil. Für Machine-Vision-Inferenz (z. B. YOLO, TFLite) werden Bilder ohnehin auf 320×320 oder 640×640 Pixel skaliert. Die 1456×1088 Pixel des IMX296 liefern ausreichend Auflösung für Vorverarbeitung und Cropping, während die artefaktfreie Aufnahme die Inferenz-Qualität bei Fahrt erhöht.

---

## 4 Optische Berechnung – IMX296 + PT361060M3MP12

### 4.1 Sensorgeometrie

```
              5,02 mm
         ┌─────────────────┐
         │                 │
  3,75 mm│    1456 × 1088  │  Diagonale = 6,27 mm
         │     Pixel       │  (≈ Type 1/2.9)
         │                 │
         └─────────────────┘
```

### 4.2 Bildwinkel (Field of View, FOV)

Das Objektiv PT361060M3MP12 ist für das 1/2"-Format (6,4 mm Diagonale) spezifiziert. Der IMX296 hat ein 1/2.9"-Format (6,3 mm Diagonale) – etwas kleiner als das Bildkreis-Format des Objektivs. Daher wird der volle Bildkreis nicht ausgenutzt und der effektive Bildwinkel ist geringfügig kleiner als bei einem 1/2"-Sensor.

$$
\text{FOV} = 2 \times \arctan\!\left(\frac{d}{2 \times f}\right)
$$

Dabei ist $d$ die Sensorabmessung (horizontal, vertikal oder diagonal) und $f = 6\,\text{mm}$ die Brennweite.

| Richtung | Sensormaß $d$ | Berechneter FOV | Bemerkung |
|---|---|---|---|
| **Horizontal** | 5,02 mm | $2 \times \arctan\!\left(\frac{5{,}02}{12}\right) \approx 45{,}4°$ | HFOV |
| **Vertikal** | 3,75 mm | $2 \times \arctan\!\left(\frac{3{,}75}{12}\right) \approx 34{,}7°$ | VFOV |
| **Diagonal** | 6,27 mm | $2 \times \arctan\!\left(\frac{6{,}27}{12}\right) \approx 55{,}2°$ | DFOV |

**Anmerkung:** Die Herstellerangabe von 63° Bildwinkel bezieht sich auf den größeren 1/2"-Sensor. Mit dem 1/2.9"-Sensor des IMX296 ergibt sich ein effektiver diagonaler Bildwinkel von ca. 55°.

### 4.3 Bodenabdeckung (Ground Sample Distance, GSD)

Für die Navigation eines AMR ist die Bodenauflösung bei verschiedenen Montagehöhen relevant.

$$
\text{GSD} = \frac{\text{Pixelgröße} \times \text{Objektabstand}}{\text{Brennweite}} = \frac{3{,}45\,\mu\text{m} \times d_\text{obj}}{6\,\text{mm}}
$$

| Montagehöhe $d_\text{obj}$ | GSD | Horizontale Abdeckung |
|---|---|---|
| 0,3 m | 0,17 mm/px | 25 cm |
| 0,5 m | 0,29 mm/px | 42 cm |
| 1,0 m | 0,58 mm/px | 84 cm |
| 2,0 m | 1,15 mm/px | 167 cm |
| 5,0 m | 2,88 mm/px | 419 cm |

### 4.4 Schärfentiefe (Depth of Field)

Bei offener Blende F1.2 ist die Schärfentiefe gering. Für Machine Vision empfiehlt sich F4 … F8, was die Schärfentiefe deutlich erhöht, aber den Lichtdurchlass reduziert (kompensierbar durch längere Belichtung oder höheren Gain).

---

## 5 Hardwareübersicht – Kameraboard

### 5.1 Blockdiagramm

```
                                  Raspberry Pi GS Camera Board
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │   CS-Mount ──► Hoya CM500 ──► Sony IMX296LQR-C              │
    │   Objektiv      IR-Filter       (1456×1088, GS)             │
    │                                     │                        │
    │                               MIPI CSI-2                     │
    │                               (2 Lanes)                      │
    │                                     │                        │
    │                              22-Pin FPC ──────────► Raspberry Pi
    │                                                     (CSI-Connector)
    │   Testpunkte:                                                │
    │   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐              │
    │   │ XTR │  │ XVS │  │ XHS │  │ MAS │  │ GND │              │
    │   └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘              │
    │      │        │        │        │        │                   │
    │   Ext.     V-Sync    H-Sync   Master   Masse                │
    │   Trigger  (Out)     (Out)    Select                         │
    │   (1,8V!)  (1,8V)   (1,8V)                                  │
    └──────────────────────────────────────────────────────────────┘
```

### 5.2 Testpunkte und Signalpegel

| Pad | Signal | Richtung | Pegel | Funktion |
|---|---|---|---|---|
| **XTR** | External Trigger | Input | **1,8 V** | Externes Auslösen: Low-Puls = Belichtung |
| **XVS** | Vertical Sync | Output | 1,8 V | Frame-Start-Signal (pro Bild ein Puls) |
| **XHS** | Horizontal Sync | Output | 1,8 V | Zeilen-Sync (für Multi-Kamera) |
| **MAS** | Master Select | Config | – | Löt-Brücke: Sensor als Sync-Slave konfigurieren |
| **GND** | Masse | – | 0 V | Bezugspotential für Trigger-Signale |

> **WARNUNG:** Alle Signalpads arbeiten mit **1,8 V Logik**. Eine direkte Verbindung mit 3,3-V- oder 5-V-GPIOs kann den Sensor irreversibel beschädigen. Stets einen Spannungsteiler oder Pegelwandler verwenden.

### 5.3 Hinweis R11 / Q2

Einige Boardrevisionen haben den Transistor Q2 bestückt, der GP1 mit XTR verbindet. Für den externen Trigger-Modus muss der Widerstand R11 entfernt werden, da sonst der Sensor im Free-Running-Modus bleibt, unabhängig vom XTR-Signal.

---

## 6 Softwareeinrichtung (Raspberry Pi 5)

### 6.1 Betriebssystem-Voraussetzungen

- Raspberry Pi OS Bookworm (oder neuer)
- Kernel mit IMX296-Treiberunterstützung (ab August 2023)
- `libcamera` und `rpicam-apps` (in Bookworm vorinstalliert)
- `picamera2` Python-Bibliothek (ab Bookworm vorinstalliert)

### 6.2 Device Tree Overlay konfigurieren

```bash
sudo nano /boot/firmware/config.txt
```

Änderungen:

```ini
# Automatische Kameraerkennung deaktivieren:
camera_auto_detect=0

# Unter [all] hinzufügen:
[all]
dtoverlay=imx296
```

Für den CAM0-Port am Raspberry Pi 5:

```ini
dtoverlay=imx296,cam0
```

Nach dem Speichern neu starten:

```bash
sudo reboot
```

### 6.3 Kameraerkennung prüfen

```bash
# Kamera-Info anzeigen
rpicam-hello --list-cameras

# Erwartete Ausgabe (Auszug):
# 0 : imx296 [1456x1088 10-bit RGGB]
#     Modes: 'SRGGB10_CSI2P' : 1456x1088 [60.00 fps]
```

### 6.4 Erster Test

```bash
# Live-Vorschau (5 Sekunden)
rpicam-hello -t 5000

# Einzelbild aufnehmen
rpicam-still -o test.jpg

# Einzelbild mit fester Belichtung (1 ms) und Gain
rpicam-still -o test.jpg --shutter 1000 --gain 1.0

# Video aufnehmen (10 Sekunden, H.264)
rpicam-vid -t 10000 -o test.h264

# RAW-Aufnahme (DNG + JPEG)
rpicam-still -o test.jpg --raw
```

---

## 7 Belichtungssteuerung

### 7.1 Automatische Belichtung (AEC/AGC)

Im Standardmodus regelt der Algorithmus Belichtungszeit und analogen Gain automatisch. Für Machine Vision ist häufig eine manuelle oder eingeschränkte Steuerung vorteilhaft.

### 7.2 Manuelle Belichtung (rpicam-apps)

```bash
# Feste Belichtungszeit 500 µs, Gain 1.0 (kein Verstärken)
rpicam-still -o capture.jpg --shutter 500 --gain 1.0

# Kurze Belichtung für schnelle Objekte (100 µs)
rpicam-still -o fast.jpg --shutter 100 --gain 4.0

# Langzeitbelichtung (1 Sekunde)
rpicam-still -o long.jpg --shutter 1000000 --gain 1.0 --awbgains 1,1 --immediate
```

### 7.3 Manuelle Belichtung (Picamera2, Python)

```python
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_still_configuration()
picam2.configure(config)

# Feste Belichtung setzen BEVOR die Kamera startet
picam2.set_controls({
    "ExposureTime": 2000,      # 2000 µs = 2 ms
    "AnalogueGain": 1.0,       # Kein analoger Gain
    "AeEnable": False,         # Auto-Belichtung deaktivieren
    "AwbEnable": False,        # Auto-Weißabgleich deaktivieren
    "ColourGains": (1.5, 1.5), # Fester Weißabgleich (R, B)
})

picam2.start()
picam2.capture_file("capture.jpg")
picam2.stop()
```

### 7.4 Belichtungsmodus in Tuning-Datei begrenzen

Für AMR-Anwendungen, bei denen Motion Blur vermieden werden muss, kann die maximale Belichtungszeit in der Tuning-Datei eingeschränkt werden, während AGC weiterhin aktiv bleibt:

```json
"exposure_modes": {
    "short": {
        "shutter": [100, 500, 1000, 2000, 2500],
        "gain":    [1.0, 2.0, 4.0,  6.0,  8.0]
    }
}
```

Diese Konfiguration begrenzt die Belichtungszeit auf maximal 2,5 ms (1/400 s) und kompensiert bei schwachem Licht durch Gain-Erhöhung bis 8×.

---

## 8 Externer Trigger (XTR)

### 8.1 Funktionsprinzip

Im External-Trigger-Modus wartet der IMX296 auf ein externes Low-Signal am XTR-Pad. Die Belichtung beginnt bei der fallenden Flanke und endet bei der steigenden Flanke. Die effektive Belichtungszeit ergibt sich aus:

$$
t_\text{exp} = t_\text{Low-Puls} + 14{,}26\,\mu\text{s}
$$

Die Bildrate entspricht der PWM-Frequenz des Trigger-Signals.

### 8.2 Trigger-Modus aktivieren

```bash
# Kernel-Modul-Parameter setzen
sudo nano /etc/modprobe.d/imx296.conf
```

Inhalt:

```
options imx296 trigger_mode=1
```

Alternativ einmalig in der Kernel-Kommandozeile:

```bash
# In /boot/firmware/cmdline.txt anhängen (mit Leerzeichen davor):
imx296.trigger_mode=1
```

Nach Neustart: Der Sensor liefert keine Frames, bis ein Trigger-Signal anliegt.

### 8.3 Beschaltung (Spannungsteiler 3,3 V → 1,8 V)

```
    GPIO (3,3 V)
        │
       [1,5 kΩ]
        │
        ├──────── XTR (Kamera, 1,8 V Logik)
        │
       [1,8 kΩ]
        │
       GND ────── GND (Kamera)
```

Berechnung des Spannungsteilers:

$$
V_\text{XTR,high} = 3{,}3\,\text{V} \times \frac{1{,}8\,\text{k}\Omega}{1{,}5\,\text{k}\Omega + 1{,}8\,\text{k}\Omega} = 3{,}3\,\text{V} \times 0{,}545 \approx 1{,}8\,\text{V}
$$

### 8.4 Trigger-Signal mit Raspberry Pi Pico erzeugen

```python
# MicroPython auf Raspberry Pi Pico
from machine import Pin, PWM

pwm = PWM(Pin(28))

framerate = 30         # Bildrate in Hz
shutter = 6000         # Belichtungszeit in µs

frame_length = 1_000_000 / framerate  # µs pro Frame
# Low-Puls-Breite = Belichtungszeit - 14,26 µs
pwm.freq(framerate)
pwm.duty_u16(int((1 - (shutter - 14) / frame_length) * 65535))
```

### 8.5 Timing-Einschränkungen

Der XTR-Pin darf während der Frame-Readout-Phase nicht auf Low gezogen werden. Die Readout-Dauer beträgt im All-Pixel-Modus 1126 Zeilen. Die Sperrzeit berechnet sich aus:

$$
t_\text{Readout} = \frac{(\text{Bildbreite} + \text{HBLANK}) \times \text{Zeilenanzahl}}{\text{Pixel Rate}}
$$

Bei typischen Einstellungen beträgt die Sperrzeit ca. 15–20 ms. Ein Trigger-Signal mit $f \leq 50\,\text{Hz}$ (20 ms Periodendauer) und Belichtungszeiten unter 5 ms ist unkritisch.

---

## 9 Multi-Kamera-Synchronisation

### 9.1 Prinzip

Für Stereo-Vision oder Multi-Kamera-Setups können mehrere Global-Shutter-Kameras über die Sync-Pads synchronisiert werden. Eine Kamera arbeitet als Source (Master), die anderen als Sink (Slave).

### 9.2 Verdrahtung

| Verbindung | Beschreibung |
|---|---|
| XVS ↔ XVS | Vertical-Sync-Leitungen aller Kameras verbinden |
| XHS ↔ XHS | Horizontal-Sync-Leitungen aller Kameras verbinden (nur bei GS Camera) |
| GND ↔ GND | Gemeinsame Masse |
| **MAS-Pad brücken** | Auf jeder Slave-Kamera die MAS-Lötbrücke schließen |

Alternativ: Alle Kameras über ein gemeinsames XTR-Signal extern triggern (Abschnitt 8). In diesem Fall entfällt die Master/Slave-Konfiguration.

---

## 10 Raspberry Pi – Picamera2-Integration

### 10.1 Konfigurationsprofile

```python
from picamera2 import Picamera2

picam2 = Picamera2()

# --- Vorschau-Konfiguration (niedriger Overhead) ---
preview_config = picam2.create_preview_configuration(
    main={"size": (1456, 1088), "format": "RGB888"},
    controls={"FrameRate": 30}
)

# --- Einzelbild-Konfiguration (volle Qualität) ---
still_config = picam2.create_still_configuration(
    main={"size": (1456, 1088), "format": "RGB888"},
    raw={"size": (1456, 1088)},  # RAW parallel aufnehmen
)

# --- Video-Konfiguration ---
video_config = picam2.create_video_configuration(
    main={"size": (1456, 1088), "format": "YUV420"},
    controls={"FrameRate": 60}
)
```

### 10.2 Machine-Vision-Pipeline (NumPy-Array)

```python
import numpy as np
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (1456, 1088), "format": "RGB888"}
)
picam2.configure(config)
picam2.set_controls({
    "ExposureTime": 2000,
    "AnalogueGain": 1.0,
    "AeEnable": False,
})
picam2.start()

# Frame als NumPy-Array abrufen
frame = picam2.capture_array("main")
# frame.shape = (1088, 1456, 3), dtype = uint8

# Graustufenkonvertierung für Inferenz
gray = np.mean(frame, axis=2).astype(np.uint8)

picam2.stop()
```

### 10.3 Metadaten auslesen

```python
metadata = picam2.capture_metadata()
exposure_us = metadata["ExposureTime"]       # Tatsächliche Belichtungszeit (µs)
analogue_gain = metadata["AnalogueGain"]     # Analoger Gain
digital_gain = metadata["DigitalGain"]       # Digitaler Gain
colour_temp = metadata["ColourTemperature"]  # Farbtemperatur (K)
lux = metadata.get("Lux", None)             # Geschätzte Beleuchtungsstärke
```

---

## 11 ROS 2-Integration

### 11.1 Kamera-Node (camera_ros)

Für ROS 2 Humble auf dem Raspberry Pi 5 steht das Paket `camera_ros` zur Verfügung, das libcamera nativ nutzt.

```bash
# Installation
sudo apt install ros-humble-camera-ros

# Starten
ros2 run camera_ros camera_node --ros-args \
    -p width:=1456 \
    -p height:=1088 \
    -p format:="RGB888" \
    -p camera:=0
```

### 11.2 Publizierte Topics

| Topic | Nachrichtentyp | Inhalt |
|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | Rohbild (RGB/YUV) |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | Kameramatrix, Verzerrungskoeffizienten |
| `/camera/image_raw/compressed` | `sensor_msgs/CompressedImage` | JPEG-komprimiert |

### 11.3 Kamerakalibrierung

Für geometrisch korrekte Auswertung (visuelle Odometrie, SLAM) ist eine Kalibrierung notwendig:

```bash
# Schachbrettmuster verwenden (z. B. 9×6 innere Ecken, 25 mm Feldgröße)
ros2 run camera_calibration cameracalibrator \
    --size 9x6 \
    --square 0.025 \
    --ros-args -r image:=/camera/image_raw \
               -r camera:=/camera
```

Die Kalibrierung liefert die intrinsische Kameramatrix $K$ und Verzerrungskoeffizienten $(k_1, k_2, p_1, p_2, k_3)$ in einer YAML-Datei.

### 11.4 AMR-Systemarchitektur

```
Raspberry Pi 5 (ROS 2 Humble)
    │
    CSI-2 ──── IMX296 + PT361060M3MP12
    │
    ├── /camera/image_raw       → Objekterkennung (YOLO/TFLite)
    ├── /camera/camera_info     → Visuelle Odometrie (ORB-SLAM3)
    ├── /camera/image_compressed → Telemetrie / Logging
    │
    └── Optional:
        ESP32-S3 ──► XTR-Trigger (Synchronisation mit Sensorik)
```

---

## 12 Objektiv-Montage und Fokussierung

### 12.1 CS-Mount vs. C-Mount

| Eigenschaft | CS-Mount | C-Mount |
|---|---|---|
| Auflagemaß (Flange Distance) | 12,526 mm | 17,526 mm |
| Gewindemaß | 1"-32 UN 2A | 1"-32 UN 2A (identisch) |
| Adapter nötig? | Nein (direkt auf GS Camera) | Ja (C-CS-Adapter, +5 mm, im Lieferumfang) |

Das PT361060M3MP12 ist ein CS-Mount-Objektiv und wird direkt auf das Kameraboard geschraubt. Der beiliegende C-CS-Adapter ist nicht erforderlich.

### 12.2 Fokussierung

1. Objektiv auf das CS-Mount-Gewinde schrauben (leichtgängig, nicht verkanten).
2. Feststellschraube am Objektivring lösen.
3. Objekt in gewünschter Entfernung anvisieren (Vorschau mit `rpicam-hello -t 0`).
4. Fokusring drehen, bis das Bild scharf erscheint.
5. Feststellschraube anziehen, um den Fokus zu fixieren.
6. Blendenring auf gewünschte Blende einstellen (F1.2 = max. Licht, F8 = max. Schärfentiefe).

### 12.3 Back-Focus-Einstellung

Falls der Fokusbereich nicht ausreicht, kann der Back-Focus (Abstand zwischen Objektivflansch und Sensor) über die Stellschraube am Kameraboard justiert werden:

```bash
# Feineinstellung mit Live-Vorschau
rpicam-hello -t 0 --info-text "Focus: %focus"
```

---

## 13 IR-Filter

### 13.1 Hoya CM500

Der integrierte IR-Sperrfilter (Hoya CM500) blockiert Wellenlängen oberhalb von ca. 650 nm. Dadurch erscheinen Bilder im sichtbaren Spektrum natürlich.

### 13.2 Entfernung für NIR-Anwendungen

Für Nahinfrarot-Anwendungen (z. B. aktive IR-Beleuchtung bei 850 nm) kann der Filter entfernt werden. Dieser Vorgang ist **irreversibel** – der Filter ist verklebt und lässt sich nicht zerstörungsfrei ausbauen.

**Ohne IR-Filter:** Farbbilder erhalten einen Rotstich bei Tageslicht. Für Machine Vision mit aktiver NIR-Beleuchtung (z. B. Linienprojektion bei 850 nm) ist die Entfernung sinnvoll. Der IMX296 zeigt moderate NIR-Empfindlichkeit (geringer als Pregius-S-Sensoren).

---

## 14 Leistungsmerkmale und Grenzen

### 14.1 Bildrate vs. Auflösung

| Modus | Auflösung | Max. Bildrate | Bemerkung |
|---|---|---|---|
| Vollbild | 1456 × 1088 | 60 fps | RAW10, MIPI CSI-2, 2 Lanes |
| ROI / Crop | Abhängig von Crop | >60 fps | Durch reduzierten Readout |

### 14.2 Typische Leistungskennwerte (Raspberry Pi 5)

| Szenario | Bildrate | Belichtung | Bemerkung |
|---|---|---|---|
| Vorschau / Navigation | 30 fps | Auto | Standardbetrieb |
| Machine Vision (YOLO) | 15–30 fps | 1–5 ms | Abhängig von Inferenzlast |
| Hochgeschwindigkeitsvideo | 60 fps | ≤16 ms | Vollbild, H.264 |
| Externe Trigger-Sync | 1–50 fps | Variabel | Via XTR-Pin |
| Langzeitbelichtung | <1 fps | Bis 15,5 s | Für lichtschwache Szenen |

### 14.3 Grenzen

- **Auflösung:** 1,58 MP begrenzt die räumliche Detailtreue. Für Aufgaben, die hohe Auflösung erfordern (z. B. Texterkennung auf großer Distanz), ist ein Rolling-Shutter-Sensor mit höherer Pixelzahl besser geeignet.
- **Farbe vs. Mono:** Die Farbversion (LQR-C) hat durch das Bayer-Muster eine effektiv geringere Auflösung als die Mono-Version (LLR). Für reine Machine-Vision-Anwendungen ohne Farbinformation kann die Mono-Version vorteilhaft sein.
- **Dynamikumfang:** Der IMX296 bietet keinen nativen HDR-Modus. Bei extremen Kontrastszenen (z. B. Tunnelausfahrt) kann die Belichtung nicht alle Bildbereiche optimal abdecken.
- **NIR-Empfindlichkeit:** Geringer als bei neueren Pregius-S-Sensoren. Für Anwendungen mit 850-nm-Beleuchtung bieten Pregius-S-Sensoren (z. B. IMX548) nahezu doppelte Quanteneffizienz im NIR.

---

## 15 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| `ERROR: no cameras available` | Kabel nicht korrekt eingesteckt oder Overlay fehlt | FPC-Kabel prüfen (Kontakte Richtung Board), `dtoverlay=imx296` in config.txt |
| Bild komplett schwarz | Belichtungszeit zu kurz oder Objektivdeckel | `--shutter` erhöhen oder Deckel entfernen |
| Bild überbelichtet / weiß | Gain zu hoch oder Blende zu offen | Gain reduzieren, Blende schließen (F4–F8) |
| Unscharfes Bild | Fokus nicht eingestellt | Fokusring drehen, Back-Focus justieren |
| Motion Blur trotz Global Shutter | Belichtungszeit zu lang | Belichtung auf <2 ms reduzieren, Gain erhöhen |
| Jello-Effekt trotz GS Camera | Kein Jello, aber Vibrationsunschärfe | Kamera vibrationsfrei montieren (Gummidämpfer) |
| Ext. Trigger liefert keine Frames | `trigger_mode=1` nicht gesetzt oder R11 nicht entfernt | Kernel-Parameter prüfen, R11 entfernen (falls Q2 bestückt) |
| Ext. Trigger: 3,3 V am XTR | Überspannung → Sensorbeschädigung möglich | Sofort trennen, Spannungsteiler auf 1,8 V verwenden |
| Farben falsch / Rotstich | IR-Filter entfernt oder AWB deaktiviert | Filter einsetzen (irreversibel) oder AWB aktivieren |
| `rpicam-hello` nicht gefunden | Älteres OS (vor Bookworm) | `libcamera-hello` verwenden oder OS aktualisieren |
| Framerate unter Erwartung | USB-Kamera gleichzeitig aktiv oder CPU-Last | Andere Kameraquellen deaktivieren, CPU-Last prüfen |

---

## 16 Vergleich mit Raspberry Pi Kameramodulen

| Parameter | Camera Module v3 | HQ Camera (IMX477) | **GS Camera (IMX296)** |
|---|---|---|---|
| Sensor | IMX708 | IMX477 | **IMX296** |
| Auflösung | 11,9 MP | 12,3 MP | **1,58 MP** |
| Pixelgröße | 1,40 µm | 1,55 µm | **3,45 µm** |
| Shutter-Typ | Rolling | Rolling | **Global** |
| Max. Bildrate | 120 fps (640×480) | 120 fps (Crop) | **60 fps (Vollbild)** |
| Min. Belichtung | ~14 µs | ~31 µs | **30 µs** |
| Ext. Trigger | Nein | Nein (nur XVS-Sync) | **Ja (XTR)** |
| Multi-Kamera-Sync | Software | XVS | **XVS + XHS + XTR** |
| Objektivanschluss | M12 (fest) | C/CS-Mount | **C/CS-Mount** |
| IR-Filter | Integriert | Integriert (entfernbar) | **Integriert (entfernbar)** |
| HDR | Ja (Sensor-HDR) | Nein | **Nein** |
| Preis (ca.) | 25 € | 50 € | **50 €** |
| AMR-Eignung | Allgemein | Inspektion, Qualität | **Machine Vision, Navigation** |

---

## 17 Ressourcen

| Typ | Link |
|---|---|
| Raspberry Pi Camera Documentation | [raspberrypi.com/documentation/accessories/camera.html](https://www.raspberrypi.com/documentation/accessories/camera.html) |
| GS Camera Product Brief (PDF) | [datasheets.raspberrypi.com/gs-camera/gs-camera-product-brief.pdf](https://datasheets.raspberrypi.com/gs-camera/gs-camera-product-brief.pdf) |
| Sony IMX296 Pregius Flyer (PDF) | [sony-semicon.com/…/IMX273_287_296_297_Flyer.pdf](https://www.sony-semicon.com/files/62/flyer_industry/IMX273_287_296_297_Flyer.pdf) |
| Picamera2 Manual (PDF) | [datasheets.raspberrypi.com/camera/picamera2-manual.pdf](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf) |
| Arducam IMX296 Wiki | [docs.arducam.com/…/1.58MP-IMX296/](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Global-Shutter/1.58MP-IMX296/) |
| External Trigger Dokumentation | [github.com/raspberrypi/documentation/…/external_trigger.adoc](https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/accessories/camera/external_trigger.adoc) |
| libcamera Tuning Guide | [datasheets.raspberrypi.com/camera/raspberry-pi-camera-guide.pdf](https://datasheets.raspberrypi.com/camera/raspberry-pi-camera-guide.pdf) |
| FRAMOS IMX296 Sensor Module | [framos.com/products/sensors/…/imx296lqr-c](https://framos.com/products/sensors/area-sensors/imx296lqr-c-22545/) |
| ROS 2 camera_ros Paket | [github.com/christianrauch/camera_ros](https://github.com/christianrauch/camera_ros) |
| PT361060M3MP12 Datenblatt | Kiwi Electronics / Besomi Electronics (Abschnitt 2.3) |

---

## 18 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   Kamerasystem: IMX296 + PT361060M3MP12 – Kurzprofil                    │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   SENSOR                     │                                           │
│   Modell                     │ Sony IMX296LQR-C (Farbe)                  │
│   Shutter-Typ                │ Global Shutter (Pregius Gen 2)            │
│   Auflösung                  │ 1456 × 1088 (1,58 MP)                    │
│   Pixelgröße                 │ 3,45 µm × 3,45 µm                       │
│   Optisches Format           │ Type 1/2.9 (Diag. 6,3 mm)               │
│   ADC                        │ 10 Bit (RAW10)                           │
│   Max. Bildrate              │ 60 fps (Vollbild)                        │
│   Min. Belichtung            │ 30 µs                                    │
│   Schnittstelle              │ MIPI CSI-2, 2 Lanes                      │
│   IR-Filter                  │ Hoya CM500 (entfernbar, irreversibel)    │
│   Ext. Trigger               │ XTR-Pad, 1,8 V Logik (!)                │
│   Sync-Pads                  │ XVS, XHS, MAS                            │
│                              │                                           │
│   OBJEKTIV                   │                                           │
│   Modell                     │ PT361060M3MP12                            │
│   Brennweite                 │ 6 mm                                     │
│   Blende                     │ F1.2 … F16                               │
│   Anschluss                  │ CS-Mount                                  │
│   Auflösung (optisch)        │ 3 MP                                     │
│   Naheinstellgrenze          │ 0,20 m                                   │
│                              │                                           │
│   SYSTEMBERECHNUNG           │                                           │
│   HFOV (6 mm, IMX296)        │ ≈ 45°                                    │
│   VFOV (6 mm, IMX296)        │ ≈ 35°                                    │
│   DFOV (6 mm, IMX296)        │ ≈ 55°                                    │
│   GSD @ 1 m                  │ 0,58 mm/px                               │
│                              │                                           │
│   PLATTFORM                  │                                           │
│   Kompatibilität             │ Raspberry Pi 5/4/3/Zero/CM (CSI-2)       │
│   Software                   │ libcamera, rpicam-apps, Picamera2        │
│   ROS 2 Node                 │ camera_ros (sensor_msgs/Image)           │
│   Produktionsende             │ Mindestens Januar 2032                   │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: Raspberry Pi GS Camera Product Brief, Sony IMX296 Pregius Flyer, Raspberry Pi Camera Documentation, Picamera2 Manual, Arducam IMX296 Wiki, FRAMOS IMX296 Datenblatt, Raspberry Pi Forums (External Trigger Threads)*
