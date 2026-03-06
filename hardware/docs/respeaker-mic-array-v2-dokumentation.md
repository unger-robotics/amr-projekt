# ReSpeaker Mic Array v2.0 – USB-Mikrofonarray mit Sprachalgorithmen

> **Technische Dokumentation** – Seeed Studio, Art.-Nr. 107990053  
> DSP-Prozessor: XMOS XVF-3000  
> Mikrofone: 4 × ST MP34DT01-M (PDM, MEMS, omnidirektional)  
> Schnittstelle: USB Audio Class 1.0 (UAC 1.0), Plug-and-Play  
> Quellen: [Seeed Studio Wiki](https://wiki.seeedstudio.com/ReSpeaker_Mic_Array_v2.0/), [Product Brief](https://files.seeedstudio.com/wiki/ReSpeaker_Mic_Array_V2/res/ReSpeaker%20MicArray%20v2.0%20Product%20Brief.pdf), [XVF-3000 Datenblatt](https://files.seeedstudio.com/wiki/ReSpeaker_Mic_Array_V2/res/XVF3000-3100-TQ128-Datasheet_1.0.pdf)

---

## 1 Übersicht

Das ReSpeaker Mic Array v2.0 ist ein USB-Mikrofonarray mit vier digitalen MEMS-Mikrofonen und integrierter Sprachverarbeitung auf dem XMOS XVF-3000. Das Board arbeitet als standardkonformes USB-Audiogerät (UAC 1.0) und benötigt unter Windows, macOS und Linux keine zusätzlichen Treiber für die Audioaufnahme und -wiedergabe.

Die Sprachalgorithmen – akustische Echounterdrückung (Acoustic Echo Cancellation, AEC), Beamforming (BF), Rauschunterdrückung (Noise Suppression, NS), Nachhallreduzierung (Dereverberation) und Sprachaktivitätserkennung (Voice Activity Detection, VAD) – laufen vollständig auf dem XVF-3000 und erfordern keine Rechenleistung des Host-Systems.

**Typische Anwendungen:** Sprachsteuerung in Robotersystemen (AMR), Smart Speaker, Sprachassistenten (Alexa, Google Assistant), Konferenzsysteme, Sprachaufzeichnung, Sprachinteraktion in Fahrzeugen.

---

## 2 Spezifikationen

### 2.1 Systemkenndaten

| Parameter | Wert | Bemerkung |
|---|---|---|
| **DSP-Prozessor** | XMOS XVF-3000 | Multicore-xCORE-Architektur |
| **Mikrofone** | 4 × ST MP34DT01-M | Digitale MEMS, PDM-Ausgang |
| **USB-Standard** | USB Audio Class 1.0 (UAC 1.0) | Plug-and-Play, treiberlos |
| **Audioausgang** | 3,5 mm Klinkenbuchse | Über WM8960 Stereo-Codec |
| **Audio-Codec** | Wolfson WM8960 | Class-D-Verstärker, 1 W/8 Ω |
| **RGB-LEDs** | 12 × programmierbar | Steuerung über USB Vendor Interface |
| **Abtastrate** | max. 16 kHz | – |
| **Bittiefe** | 16 Bit | Signed Integer (S16\_LE) |
| **Fernfeld-Reichweite** | bis 5 m | Herstellerangabe, abhängig von Umgebung |
| **Spannungsversorgung** | 5 V DC | Über Micro-USB oder Expansion Header |
| **Stromaufnahme** | 180 mA (LEDs an) / 170 mA (LEDs aus) | Bei 5 V |
| **Leistungsaufnahme** | ca. 0,9 W | $5\,\text{V} \times 180\,\text{mA}$ |
| **Bauform** | Kreisplatine, ∅ 70 mm | – |
| **Betriebssysteme** | Windows, macOS, Linux, Android | UAC 1.0-kompatibel |
| **USB Vendor ID / Product ID** | `0x2886` / `0x0018` | Seeed Studio |

### 2.2 Mikrofon-Kennwerte (ST MP34DT01-M)

| Parameter | Min. | Typ. | Max. | Einheit |
|---|---|---|---|---|
| Versorgungsspannung $V_\text{dd}$ | 1,64 | 1,8 | 3,6 | V |
| Stromaufnahme (Normalbetrieb) | – | 0,6 | – | mA |
| Empfindlichkeit (Sensitivity) | −29 | −26 | −23 | dBFS |
| Signal-Rausch-Verhältnis (SNR) | – | 61 | – | dB(A) |
| Akustischer Übersteuerungspunkt (AOP) | – | 120 | – | dBSPL |
| Frequenzbereich | 20 | – | 20.000 | Hz |
| Richtcharakteristik | – | Omnidirektional | – | – |
| Ausgangsformat | – | PDM | – | – |
| Taktfrequenz (Clock) | 1,0 | 2,4 | 3,25 | MHz |
| Gehäuse | – | HCLGA | – | 3 × 4 × 1,06 mm |
| Betriebstemperatur | −40 | – | +85 | °C |

### 2.3 Integrierte Sprachalgorithmen (XVF-3000)

| Algorithmus | Abkürzung | Funktion |
|---|---|---|
| Akustische Echounterdrückung | AEC | Eliminiert Echo vom Lautsprecherausgang, ermöglicht Vollduplex-Betrieb |
| Beamforming | BF | Richtet die Empfindlichkeit auf die erkannte Sprachrichtung aus |
| Rauschunterdrückung (stationär) | NS | Unterdrückt gleichmäßige Hintergrundgeräusche (Lüfter, Klimaanlage) |
| Rauschunterdrückung (nicht-stationär) | NNS | Unterdrückt wechselnde Störgeräusche (Gespräche, Musik) |
| Nachhallreduzierung | Derev | Reduziert Raumreflexionen für klarere Sprachaufnahme |
| Sprachaktivitätserkennung | VAD | Erkennt Sprachsegmente und unterscheidet sie von Stille/Rauschen |
| Einfallsrichtungserkennung | DoA | Bestimmt den Winkel (0° … 359°) der Schallquelle relativ zum Array |
| Automatische Verstärkungsregelung | AGC | Normalisiert den Ausgangspegel auf einen Zielwert |
| Hochpassfilter | HPF | Konfigurierbarer Hochpass (70 Hz, 125 Hz oder 180 Hz Grenzfrequenz) |

---

## 3 Hardwareaufbau

### 3.1 Blockdiagramm

```
                        ┌───────────────────────────────────┐
                        │      ReSpeaker Mic Array v2.0      │
                        │                                   │
  Micro-USB ─── USB ────┤   ┌──────────┐                    │
  (5 V + Daten)         │   │ XMOS     │◄── MIC-DATA[3:0] ──┤── 4× MP34DT01-M
                        │   │ XVF-3000 │                    │   (PDM MEMS)
                        │   │ (DSP)    │── SPI ──┤          │
                        │   └──────────┘         │          │
                        │        │            12× RGB-LED    │
                        │        │ I²S                       │
                        │   ┌──────────┐                    │
                        │   │ WM8960   │── HP ──────────────┤── 3,5 mm Klinke
                        │   │ (Codec)  │                    │   (Kopfhörer/Lautsprecher)
                        │   └──────────┘                    │
                        └───────────────────────────────────┘
```

### 3.2 Komponentenbeschreibung

| Nr. | Komponente | Funktion |
|---|---|---|
| ① | XMOS XVF-3000 | DSP-Prozessor: Sprachalgorithmen, USB-Interface, LED-Steuerung |
| ② | 4 × ST MP34DT01-M | Digitale MEMS-Mikrofone, PDM-Ausgang, gleichmäßig im 90°-Abstand auf der Kreisplatine verteilt |
| ③ | 12 × RGB-LED | Programmierbarer LED-Ring für DoA-Anzeige, VAD-Status, benutzerdefinierte Muster |
| ④ | Micro-USB-Buchse | Stromversorgung (5 V) und USB-Datenverbindung zum Host |
| ⑤ | 3,5 mm Klinkenbuchse | Analoger Audioausgang (Kopfhörer oder aktive Lautsprecher) |
| ⑥ | Wolfson WM8960 | Stereo-Codec mit Class-D-Verstärker, I²S-Anbindung an XVF-3000 |

### 3.3 Mikrofonanordnung und DoA-Referenz

Die vier Mikrofone sind im 90°-Abstand auf der Kreisplatine angeordnet. Die DoA-Winkelreferenz (0° … 359°) bezieht sich auf die Draufsicht des Boards:

```
              MIC 1 (0°)
                 │
                 │
    MIC 4 ───────┼─────── MIC 2
    (270°)       │        (90°)
                 │
                 │
              MIC 3 (180°)

    (USB-Anschluss zeigt Richtung 180°)
```

Die grüne LED des LED-Rings markiert die erkannte Einfallsrichtung.

### 3.4 Mechanische Daten

| Parameter | Wert |
|---|---|
| Bauform | Kreisplatine |
| Durchmesser | 70 mm |
| Höhe (ohne Anschlüsse) | ca. 7 mm |
| Befestigung | 3 × M3-Bohrungen (gleichmäßig verteilt) |
| Anschlüsse | Micro-USB (Daten + Versorgung), 3,5 mm Klinke (Audio-Out) |
| Gewicht | ca. 15 g |

---

## 4 Firmware

### 4.1 Verfügbare Firmware-Versionen

| Firmware-Datei | Kanäle | Beschreibung |
|---|---|---|
| `1_channel_firmware.bin` | 1 | Nur verarbeitetes Audio (Kanal 0) für ASR |
| `6_channels_firmware.bin` | 6 | Werksfirmware, voller Zugriff auf alle Kanäle |

### 4.2 Kanalbelegung (6-Kanal-Firmware)

| Kanal | Inhalt | Verwendung |
|---|---|---|
| 0 | Verarbeitetes Audio | Spracherkennung (ASR), nach BF + AEC + NS |
| 1 | MIC 1 Rohdaten | Unverarbeitete Aufnahme, Diagnose |
| 2 | MIC 2 Rohdaten | Unverarbeitete Aufnahme, Diagnose |
| 3 | MIC 3 Rohdaten | Unverarbeitete Aufnahme, Diagnose |
| 4 | MIC 4 Rohdaten | Unverarbeitete Aufnahme, Diagnose |
| 5 | Wiedergabe-Referenz (Playback) | AEC-Referenzsignal vom Lautsprecherausgang |

**Kanal 0** enthält das akustisch optimierte Signal: Beamforming richtet den Empfangsstrahl auf die erkannte Sprachrichtung aus, AEC entfernt das Lautsprechersignal, und Rauschunterdrückung minimiert Hintergrundgeräusche. Für Spracherkennung (ASR) ist ausschließlich Kanal 0 relevant.

### 4.3 Firmware-Update (Linux via USB DFU)

```bash
sudo apt-get update
sudo pip install pyusb click
git clone https://github.com/respeaker/usb_4_mic_array.git
cd usb_4_mic_array

# 6-Kanal-Firmware (Werkszustand)
sudo python dfu.py --download 6_channels_firmware.bin

# 1-Kanal-Firmware (nur verarbeitetes Audio)
sudo python dfu.py --download 1_channel_firmware.bin
```

Der Firmware-Update-Vorgang dauert wenige Sekunden. Das Board meldet sich nach dem Update automatisch als USB-Audiogerät zurück.

---

## 5 DSP-Parameter (Tuning)

### 5.1 Parameterübersicht

Die DSP-Algorithmen des XVF-3000 sind über USB Vendor Control Transfer konfigurierbar. Das Python-Werkzeug `tuning.py` aus dem Repository `usb_4_mic_array` ermöglicht Lesen und Schreiben der Parameter.

```bash
cd usb_4_mic_array
python tuning.py -p          # Alle Parameter auflisten
python tuning.py DOAANGLE    # DoA-Winkel lesen (Read-Only)
python tuning.py AGCONOFF 0  # AGC deaktivieren (Write)
```

### 5.2 Wichtige DSP-Parameter

| Parameter | Typ | Bereich | R/W | Beschreibung |
|---|---|---|---|---|
| `DOAANGLE` | int | 0 … 359 | R | Einfallsrichtung in Grad |
| `SPEECHDETECTED` | int | 0 / 1 | R | Spracherkennung aktiv (1 = Sprache erkannt) |
| `VOICEACTIVITY` | int | 0 / 1 | R | VAD-Status |
| `RT60` | float | 0,25 … 0,9 | R | Geschätzte Nachhallzeit in Sekunden |
| `AGCONOFF` | int | 0 / 1 | R/W | AGC ein/aus |
| `AGCGAIN` | float | 1 … 1000 | R/W | AGC-Verstärkungsfaktor (0 … 60 dB) |
| `AGCMAXGAIN` | float | 1 … 1000 | R/W | Max. AGC-Verstärkung (Standard: 30 dB) |
| `AGCDESIREDLEVEL` | float | 1e−8 … 0,99 | R/W | Ziel-Ausgangspegel (Standard: −23 dBov) |
| `ECHOONOFF` | int | 0 / 1 | R/W | Echo-Unterdrückung ein/aus |
| `AECFREEZEONOFF` | int | 0 / 1 | R/W | AEC-Adaption einfrieren |
| `AECSILENCELEVEL` | float | 1e−9 … 1 | R/W | Schwellenwert Stille-Erkennung (Standard: −80 dBov) |
| `FREEZEONOFF` | int | 0 / 1 | R/W | Beamformer-Adaption einfrieren |
| `HPFONOFF` | int | 0 … 3 | R/W | Hochpass: 0 = aus, 1 = 70 Hz, 2 = 125 Hz, 3 = 180 Hz |
| `GAMMAVAD_SR` | float | 0 … 1000 | R/W | VAD-Schwellenwert (Standard: 3,5 dB) |
| `STATNOISEONOFF` | int | 0 / 1 | R/W | Stationäre Rauschunterdrückung ein/aus |
| `NONSTATNOISEONOFF` | int | 0 / 1 | R/W | Nicht-stationäre Rauschunterdrückung ein/aus |
| `NLATTENONOFF` | int | 0 / 1 | R/W | Nichtlineare Echo-Dämpfung ein/aus |
| `TRANSIENTONOFF` | int | 0 / 1 | R/W | Transiente Echo-Unterdrückung ein/aus |
| `CNIONOFF` | int | 0 / 1 | R/W | Komfortrauschen (Comfort Noise Insertion) ein/aus |

### 5.3 Empfehlungen für AMR-Einsatz

Für den Einsatz auf einer mobilen Roboterplattform mit Motorengeräuschen und wechselnden Raumbedingungen empfehlen sich folgende Einstellungen:

| Parameter | Empfohlener Wert | Begründung |
|---|---|---|
| `HPFONOFF` | 3 (180 Hz) | Unterdrückt tieffrequente Motorgeräusche |
| `STATNOISEONOFF` | 1 | Motorlüfter, Servosummen |
| `NONSTATNOISEONOFF` | 1 | Wechselnde Umgebungsgeräusche |
| `ECHOONOFF` | 1 | Falls Lautsprecherausgang genutzt wird |
| `AGCONOFF` | 1 | Automatische Pegelanpassung bei wechselnden Abständen |
| `GAMMAVAD_SR` | 5,0 | Höherer Schwellenwert, um Motorgeräusche nicht als Sprache zu erkennen |

---

## 6 LED-Ring-Steuerung

### 6.1 Steuerungsprinzip

Die 12 RGB-LEDs werden über ein USB Vendor Specific Class Interface gesteuert. Die Python-Bibliothek `pixel_ring` abstrahiert die USB Control Transfers.

### 6.2 LED-Befehle

| Befehl | Daten | API | Funktion |
|---|---|---|---|
| `0x00` | `[0]` | `pixel_ring.trace()` | Trace-Modus: LEDs reagieren auf VAD und DoA |
| `0x01` | `[r, g, b, 0]` | `pixel_ring.mono()` | Alle LEDs auf eine Farbe setzen |
| `0x02` | `[0]` | `pixel_ring.listen()` | Zuhör-Modus (ähnlich Trace, LEDs bleiben an) |
| `0x03` | `[0]` | `pixel_ring.speak()` | Wartemodus-Animation |
| `0x04` | `[0]` | `pixel_ring.think()` | Denk-Animation |
| `0x05` | `[0]` | `pixel_ring.spin()` | Rotationsanimation |
| `0x06` | `[r,g,b,0] × 12` | `pixel_ring.customize()` | Jede LED individuell setzen |
| `0x20` | `[brightness]` | `pixel_ring.set_brightness()` | Helligkeit (0x00 … 0x1F) |
| `0x21` | `[r1,g1,b1,0,r2,g2,b2,0]` | `pixel_ring.set_color_palette()` | Farbpalette für Animationen |
| `0x22` | `[vad_led]` | `pixel_ring.set_vad_led()` | Zentrale LED: 0 = aus, 1 = an, sonst = VAD-abhängig |
| `0x23` | `[volume]` | `pixel_ring.set_volume()` | Lautstärkeanzeige (0 … 12) |
| `0x24` | `[pattern]` | `pixel_ring.change_pattern()` | 0 = Google Home, sonst = Echo-Muster |

### 6.3 LED-Steuerung (Python-Beispiel)

```python
import time
from pixel_ring import pixel_ring

pixel_ring.change_pattern('echo')

while True:
    try:
        pixel_ring.wakeup()     # Aufwach-Animation
        time.sleep(3)
        pixel_ring.think()      # Verarbeitungs-Animation
        time.sleep(3)
        pixel_ring.speak()      # Sprechen-Animation
        time.sleep(6)
        pixel_ring.off()        # LEDs aus
        time.sleep(3)
    except KeyboardInterrupt:
        break

pixel_ring.off()
```

**Installation:**

```bash
git clone https://github.com/respeaker/pixel_ring.git
cd pixel_ring
sudo python setup.py install
```

**Hinweis (Windows):** Für LED-Steuerung und DSP-Parameter unter Windows muss der Treiber `libusb-win32` über das Werkzeug [Zadig](https://zadig.akeo.ie/) für die USB-Geräte „SEEED DFU" und „SEEED Control" installiert werden. Die Audio-Funktion selbst benötigt keinen speziellen Treiber.

---

## 7 Integration (Linux / Raspberry Pi)

### 7.1 Geräteerkennung

Nach dem Anschließen an einen USB-Port meldet sich das Board als ALSA-Audiogerät:

```bash
$ arecord -l
**** Liste der Hardware-Geräte (CAPTURE) ****
Karte 1: ArrayUAC10 [ReSpeaker 4 Mic Array (UAC1.0)], Gerät 0: USB Audio [USB Audio]
  Sub-Geräte: 1/1
  Sub-Gerät #0: subdevice #0
```

### 7.2 Aufnahme und Wiedergabe (ALSA)

```bash
# Aufnahme (16 kHz, 16 Bit, 6 Kanäle)
arecord -D plughw:1,0 -f cd -r 16000 -c 6 test.wav

# Wiedergabe über 3,5 mm Klinke
aplay -D plughw:1,0 -f cd test.wav

# Gleichzeitige Aufnahme und Wiedergabe (Monitoring)
arecord -D plughw:1,0 -f cd | aplay -D plughw:1,0 -f cd
```

### 7.3 Audioaufnahme mit PyAudio (Python)

```python
import pyaudio
import wave

RESPEAKER_RATE    = 16000
RESPEAKER_CHANNELS = 6      # 6 bei 6_channels_firmware, 1 bei 1_channel_firmware
RESPEAKER_WIDTH   = 2       # 16 Bit = 2 Bytes
RESPEAKER_INDEX   = 2       # Geräteindex, über get_index.py ermitteln
CHUNK             = 1024
RECORD_SECONDS    = 5

p = pyaudio.PyAudio()

stream = p.open(
    rate=RESPEAKER_RATE,
    format=p.get_format_from_width(RESPEAKER_WIDTH),
    channels=RESPEAKER_CHANNELS,
    input=True,
    input_device_index=RESPEAKER_INDEX,
)

print("* Aufnahme läuft...")
frames = []
for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)
print("* Aufnahme beendet.")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open("output.wav", 'wb')
wf.setnchannels(RESPEAKER_CHANNELS)
wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
wf.setframerate(RESPEAKER_RATE)
wf.writeframes(b''.join(frames))
wf.close()
```

### 7.4 Einzelkanal extrahieren (Kanal 0 = verarbeitetes Audio)

```python
import numpy as np

# Innerhalb der Aufnahme-Schleife:
data = stream.read(CHUNK)
# Kanal 0 aus 6-Kanal-Interleaved-Stream extrahieren:
channel_0 = np.frombuffer(data, dtype=np.int16)[0::6]
# Für Kanal X: [X::6]
```

### 7.5 DoA-Abfrage (Python)

```python
from tuning import Tuning
import usb.core
import time

dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)

if dev:
    mic_tuning = Tuning(dev)
    while True:
        try:
            angle = mic_tuning.direction
            is_voice = mic_tuning.is_voice()
            print(f"DoA: {angle}°, Sprache: {'ja' if is_voice else 'nein'}")
            time.sleep(0.5)
        except KeyboardInterrupt:
            break
```

---

## 8 ROS 2-Integration

### 8.1 ROS-Paket

Das Paket [`respeaker_ros`](https://github.com/furushchev/respeaker_ros) von Yuki Furuta stellt ROS-Topics für DoA, VAD und Audio bereit. Es nutzt die `pyusb`- und `pixel_ring`-Bibliotheken intern.

**Publizierte Topics (Auswahl):**

| Topic | Nachrichtentyp | Inhalt |
|---|---|---|
| `/sound_direction` | `std_msgs/Int32` | DoA-Winkel (0 … 359°) |
| `/sound_localization` | `geometry_msgs/PoseStamped` | Schallquellen-Pose im Roboter-Frame |
| `/is_speeching` | `std_msgs/Bool` | VAD-Status |
| `/audio` | `audio_common_msgs/AudioData` | PCM-Audiostrom |
| `/speech_audio` | `audio_common_msgs/AudioData` | Nur Sprachsegmente (VAD-gefiltert) |

### 8.2 Integration in das AMR-System

Auf dem Raspberry Pi 5 des AMR-Projekts kann das ReSpeaker Mic Array v2.0 über USB angeschlossen und als ROS 2-Knoten betrieben werden. Der DoA-Wert lässt sich für die Ausrichtung des Roboters auf den Sprecher verwenden.

```
Raspberry Pi 5 (ROS 2 Humble)
    │
    USB ──── ReSpeaker Mic Array v2.0
    │
    ├── /sound_direction → Navigation / Kopfdrehung
    ├── /is_speeching → Spracherkennungs-Trigger
    └── /audio → Whisper / Vosk / Google STT
```

### 8.3 Installationsschritte (ROS 2 Humble, Ubuntu 22.04)

```bash
# Abhängigkeiten
sudo apt install python3-pyaudio portaudio19-dev
sudo pip3 install pyusb pixel-ring

# ROS-Paket (ggf. für ROS 2 portiert)
cd ~/ros2_ws/src
git clone https://github.com/furushchev/respeaker_ros.git
cd ~/ros2_ws
colcon build --packages-select respeaker_ros
source install/setup.bash

# Starten
ros2 launch respeaker_ros respeaker.launch.py
```

---

## 9 Treiberanforderungen

| Betriebssystem | Audio (UAC 1.0) | LED-/DSP-Steuerung | Bemerkung |
|---|---|---|---|
| **Linux** | Treiberlos | `pyusb` (via `libusb`) | `sudo pip install pyusb` |
| **macOS** | Treiberlos | `pyusb` (via `libusb`) | – |
| **Windows** | Treiberlos | `libusb-win32` via Zadig | Für „SEEED DFU" und „SEEED Control" |
| **Android** | Treiberlos | Nicht unterstützt | Getestet mit emteria.OS 7.1 |

---

## 10 Elektrischer Anschluss und Erweiterung

### 10.1 USB-Versorgung

Das Board bezieht 5 V und max. 180 mA über den Micro-USB-Anschluss. Die meisten USB-2.0-Ports (500 mA-Budget) versorgen das Board problemlos.

### 10.2 Expansion Header

Das Board verfügt über einen Expansion Header, über den alternativ 5 V extern zugeführt werden können. Dieser Header ermöglicht auch die Stapelung mit dem ReSpeaker Core oder anderen Erweiterungsboards (z. B. Grove-Breakout).

### 10.3 Audioausgang (3,5 mm Klinke)

Der Wolfson WM8960-Codec wandelt den I²S-Datenstrom vom XVF-3000 in ein analoges Audiosignal um. Der integrierte Class-D-Verstärker liefert bis zu 1 W an 8 Ω. Kopfhörer und aktive Lautsprecher können direkt angeschlossen werden. Das Wiedergabesignal dient gleichzeitig als AEC-Referenz (Kanal 5).

---

## 11 Vergleich mit dem Vorgänger und Alternativen

| Parameter | Mic Array v1.0 | Mic Array v2.0 | Mic Array v3.0 |
|---|---|---|---|
| DSP-Chip | XVSM-2000 | XVF-3000 | XVF-3000 |
| Mikrofone | 7 × PDM | 4 × PDM (MP34DT01-M) | 4 × PDM |
| USB-Standard | UAC 1.0 | UAC 1.0 | UAC 1.0 |
| AEC | Ja | Ja (verbessert, Vollduplex) | Ja |
| Bauform | Kreisplatine | Kreisplatine ∅ 70 mm | Gehäuse mit Akustikstruktur |
| Audioausgang | – | 3,5 mm Klinke (WM8960) | 3,5 mm Klinke |
| LEDs | 12 × RGB | 12 × RGB | 12 × RGB |
| Status | Abgekündigt | Aktiv | Aktiv (Gehäuseversion) |

---

## 12 Fehlerbehebung

| Problem | Ursache | Lösung |
|---|---|---|
| Kein Audiogerät erkannt | USB-Kabel defekt / nur Ladekabel | Datenfähiges USB-Kabel verwenden |
| `ImportError: No module named usb.core` | `pyusb` nicht installiert | `sudo pip install pyusb` |
| LED-Steuerung gibt `None` zurück (Windows) | Falscher USB-Treiber | `libusb-win32` über Zadig installieren (nicht WinUSB oder libusbK) |
| DoA-Winkel springt zufällig | Keine Sprachquelle / zu viel Rauschen | `GAMMAVAD_SR` erhöhen, HPF aktivieren |
| Verarbeitetes Audio (Kanal 0) klingt dumpf | Rauschunterdrückung zu aggressiv | `GAMMA_NS_SR` und `MIN_NS_SR` reduzieren |
| AEC funktioniert nicht | 1-Kanal-Firmware geladen | 6-Kanal-Firmware flashen (AEC benötigt Kanal 5 als Referenz) |
| Firmware-Update schlägt fehl | Berechtigungen | `sudo python dfu.py ...` ausführen |

---

## 13 Sicherheits- und Betriebshinweise

- **Spannungsversorgung:** Ausschließlich 5 V DC über USB. Keine externe Spannung >5,5 V anlegen.
- **ESD:** Das Board enthält empfindliche MEMS-Sensoren. ESD-Schutzmaßnahmen bei Handhabung beachten.
- **Akustik-Ports:** Die Mikrofonöffnungen (Top-Port) nicht verdecken oder verschmutzen. Verschmutzung der MEMS-Membranen beeinträchtigt Empfindlichkeit und Richtcharakteristik.
- **Montageposition:** Für optimale DoA- und Beamforming-Leistung das Board horizontal und frei von schallreflektierenden Oberflächen montieren. Ein Mindestabstand von 5 mm zwischen Mikrofonöffnung und Montageoberfläche verbessert die Akustik.
- **Keine Feuchtigkeitsexposition:** Die MEMS-Mikrofone besitzen keine IP-Schutzklassifizierung. Nur in trockenen Umgebungen einsetzen.

---

## 14 Ressourcen

| Typ | Link |
|---|---|
| Seeed Wiki | [wiki.seeedstudio.com/ReSpeaker_Mic_Array_v2.0](https://wiki.seeedstudio.com/ReSpeaker_Mic_Array_v2.0/) |
| GitHub – USB 4 Mic Array | [github.com/respeaker/usb_4_mic_array](https://github.com/respeaker/usb_4_mic_array) |
| GitHub – Pixel Ring | [github.com/respeaker/pixel_ring](https://github.com/respeaker/pixel_ring) |
| GitHub – ROS-Integration | [github.com/furushchev/respeaker_ros](https://github.com/furushchev/respeaker_ros) |
| Schaltplan (PDF) | [ReSpeaker MicArray v2.0 Schematic](https://files.seeedstudio.com/products/107990053/ReSpeakerMicArrayv2.0.1Schematic.zip) |
| Product Brief (PDF) | [ReSpeaker MicArray v2.0 Product Brief](https://files.seeedstudio.com/wiki/ReSpeaker_Mic_Array_V2/res/ReSpeaker%20MicArray%20v2.0%20Product%20Brief.pdf) |
| XVF-3000 Datenblatt (PDF) | [XVF3000 Datasheet](https://files.seeedstudio.com/wiki/ReSpeaker_Mic_Array_V2/res/XVF3000-3100-TQ128-Datasheet_1.0.pdf) |
| 3D-Modell (STP) | [ReSpeaker MicArray v2.0 3D Model](https://files.seeedstudio.com/wiki/ReSpeaker_Mic_Array_V2/res/RESPEAKER%20MIC-3D%20v2.0.stp.zip) |

---

## 15 Zusammenfassung der Schlüsselparameter

```
┌────────────────────────────────────────────────────────────────────┐
│   ReSpeaker Mic Array v2.0 (Art.-Nr. 107990053) – Kurzprofil      │
├──────────────────────────┬─────────────────────────────────────────┤
│ DSP-Prozessor            │ XMOS XVF-3000                          │
│ Mikrofone                │ 4 × ST MP34DT01-M (MEMS, PDM)         │
│ Richtcharakteristik      │ Omnidirektional (einzeln), BF (Array)  │
│ Empfindlichkeit          │ −26 dBFS (typ.)                        │
│ SNR                      │ 61 dB(A)                               │
│ AOP                      │ 120 dBSPL                              │
│ Abtastrate               │ 16 kHz                                 │
│ Bittiefe                 │ 16 Bit                                 │
│ Kanäle (6-Ch-FW)         │ 1× verarbeitet + 4× Roh + 1× Playback │
│ Fernfeld-Reichweite      │ bis 5 m                                │
│ USB-Standard             │ UAC 1.0 (Plug-and-Play)                │
│ USB VID:PID              │ 0x2886:0x0018                          │
│ Audioausgang             │ 3,5 mm Klinke (WM8960 Codec)           │
│ LED-Ring                 │ 12 × RGB, programmierbar               │
│ Sprachalgorithmen        │ AEC, BF, NS, Derev, VAD, DoA, AGC     │
│ Versorgung               │ 5 V DC / 180 mA (über USB)             │
│ Bauform                  │ Kreisplatine, ∅ 70 mm                  │
│ Betriebstemperatur       │ −40 °C … +85 °C (Mikrofone)            │
│ Betriebssysteme          │ Windows, macOS, Linux, Android          │
│ ROS-Unterstützung        │ respeaker_ros (DoA, VAD, Audio Topics) │
└──────────────────────────┴─────────────────────────────────────────┘
```

---

*Dokumentversion: 1.0 | Datum: 2025-02-24 | Quellen: Seeed Studio Wiki (Stand: Januar 2023), ReSpeaker MicArray v2.0 Product Brief, XMOS XVF-3000 Datenblatt v1.0, ST MP34DT01-M Datenblatt Rev. 3*
