# KI-Beschleuniger Hailo-8L (PCIe)

> **Technische Dokumentation** – Neuronaler Netzwerk-Beschleuniger (Neural Processing Unit, NPU) für autonome mobile Robotik (AMR)
> Chip: Hailo-8L (13 TOPS, INT8, PCIe Gen 3.0 ×1)
> Formfaktor: M.2 2242 Key B+M (im Raspberry Pi AI Kit / AI HAT+)
> Host: Raspberry Pi 5 (PCIe 2.0 ×1, optional Gen 3.0)
> Software: HailoRT, TAPPAS Core, GStreamer-Pipelines, Python-API
> Anwendung: Echtzeit-Objekterkennung (YOLOv8), Hindernisklassifizierung, Personenerkennung
> Quellen: [Hailo-8L Produktseite](https://hailo.ai/products/ai-accelerators/hailo-8l-m-2-ai-acceleration-module-for-ai-light-applications/), [Raspberry Pi AI Kit Dokumentation](https://www.raspberrypi.com/documentation/accessories/ai-kit.html), [Raspberry Pi AI Software](https://www.raspberrypi.com/documentation/computers/ai.html), [hailo-rpi5-examples (GitHub)](https://github.com/hailo-ai/hailo-rpi5-examples), [Hailo Community Benchmarks](https://community.hailo.ai/t/raspberry-pi-5-with-hailo-8l-benchmark/746)

---

## 1 Systemübersicht

### 1.1 Funktion im AMR-System

Der Hailo-8L KI-Beschleuniger ermöglicht die Echtzeit-Inferenz neuronaler Netze direkt auf dem Raspberry Pi 5, ohne Cloud-Anbindung. Im AMR-System übernimmt er die kamerbasierte Umgebungswahrnehmung: Objekterkennung (Hindernisse, Personen, Gegenstände), Segmentierung und optional Tiefenschätzung (Depth Estimation). Die Inferenz-Ergebnisse fließen als ROS-2-Topics in die Navigations- und Entscheidungslogik ein.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Raspberry Pi 5 – ROS 2 Humble                                         │
│                                                                         │
│  ┌──────────────────┐    ┌────────────────┐    ┌────────────────────┐  │
│  │  Nav2 / Planner   │◄──│ Detektions-    │◄───│  Hailo-8L NPU     │  │
│  │  (Kostenkarte)    │   │ Node (ROS 2)   │    │  (13 TOPS)        │  │
│  │                   │   │                │    │                    │  │
│  │  /detected_objects│   │  GStreamer /    │    │  M.2 HAT+         │  │
│  └──────────────────┘   │  Python-API    │    │  PCIe Gen 3 ×1    │  │
│                          └───────┬────────┘    └────────┬───────────┘  │
│                                  │                      │  PCIe FPC    │
│                          ┌───────▼────────┐             │              │
│                          │  Kamera         │             │              │
│                          │  (CSI / USB)    │             │              │
│                          │  RPi Cam v3     │             │              │
│                          └────────────────┘             │              │
│                                                          │              │
│  Weitere Sensoren:                                       │              │
│    /scan        ← RPLIDAR A1 (USB)                      │              │
│    /imu         ← MPU6050 (I²C via ESP32-S3)            │              │
│    /wheel_odom  ← Encoder (micro-ROS)                   │              │
└──────────────────────────────────────────────────────────┼──────────────┘
                                                           │
                                             Raspberry Pi M.2 HAT+
                                             mit Hailo-8L Modul
```

### 1.2 Warum ein dedizierter KI-Beschleuniger?

| Ansatz                              | Rechenleistung (INT8) | Leistungsaufnahme | YOLOv8s (FPS) | Eignung AMR              |
|-------------------------------------|-----------------------|-------------------|---------------|--------------------------|
| **Raspberry Pi 5 CPU** (Cortex-A76) | ~2 TOPS (geschätzt)   | 5 … 12 W (gesamt) | ~3 … 5        | Ungeeignet für Echtzeit  |
| **Hailo-8L** (NPU, PCIe)            | **13 TOPS**           | **~1,5 W** (NPU)  | **~30 … 55**  | **Sehr gut**             |
| Hailo-8 (NPU, PCIe)                 | 26 TOPS               | ~2,5 W (NPU)      | ~55 … 100     | Sehr gut (Premiumklasse) |
| Google Coral (USB TPU)              | 4 TOPS                | ~2 W              | ~10 … 15      | Begrenzt                 |
| Nvidia Jetson Orin Nano             | 40 TOPS               | 7 … 15 W          | ~80 … 120     | Überdimensioniert        |

> **Vorteil des Hailo-8L:** Die NPU entlastet die vier Cortex-A76-Kerne des Pi 5 vollständig von der KI-Inferenz. Die CPU bleibt für ROS 2, Navigation, Motorsteuerung und Kommunikation verfügbar. Die Leistungsaufnahme von ~1,5 W für die NPU ist für batteriebetriebene AMR-Systeme ideal.

---

## 2 Hailo-8L – Technische Daten

### 2.1 Chip-Spezifikationen

| Parameter                       | Wert                                      | Einheit |
|---------------------------------|-------------------------------------------|---------|
| **Hersteller**                  | Hailo (Tel Aviv, Israel)                  | –       |
| **Chip-Bezeichnung**            | Hailo-8L                                  | –       |
| **Architektur**                 | Dataflow Architecture (Proprietär)        | –       |
| **Rechenleistung (INT8)**       | 13                                        | TOPS    |
| **Energieeffizienz**            | ~8                                        | TOPS/W  |
| **Leistungsaufnahme (typisch)** | ~1,5                                      | W       |
| **Unterstützte Datentypen**     | INT8, INT16 (quantisiert)                 | –       |
| **On-Chip-Speicher**            | Verteilter SRAM (Dataflow)                | –       |
| **Externen DRAM**               | Nicht erforderlich (Dataflow-Architektur) | –       |
| **Max. gleichzeitige Modelle**  | Mehrere (Multi-Context Switching)         | –       |
| **Betriebstemperatur**          | −40 … +85                                 | °C      |

### 2.2 Dataflow-Architektur

Die Hailo-8L-Architektur unterscheidet sich grundlegend von GPU- oder CPU-basierten KI-Beschleunigern. Anstatt Daten zwischen einem zentralen Speicher und Recheneinheiten hin- und herzuschieben, fließen die Daten in einem **Datenstrom (Dataflow)** durch das Netzwerk von Rechenknoten. Jeder Layer des neuronalen Netzes wird auf dedizierte Hardware-Blöcke abgebildet, die parallel und pipelined arbeiten.

```
Klassische Architektur (GPU/CPU):        Hailo Dataflow-Architektur:

  ┌──────────┐                              Eingabe
  │  DRAM     │◄──────┐                       │
  └──────────┘       │                       ▼
       │              │                  ┌──────────┐
       ▼              │                  │ Layer 1   │──► direkt
  ┌──────────┐  ┌──────────┐            │ (HW-Block)│    weiter
  │ Rechen-  │  │ Rechen-  │            └──────────┘
  │ einheit  │  │ einheit  │                 │
  └──────────┘  └──────────┘                 ▼
       │              │                  ┌──────────┐
       └──────►───────┘                  │ Layer 2   │──► direkt
            │                            │ (HW-Block)│    weiter
            ▼                            └──────────┘
        Zurück zum DRAM                      │
        (Bandbreiten-Engpass)                ▼
                                         ┌──────────┐
                                         │ Layer N   │
                                         │ (HW-Block)│
                                         └──────────┘
                                              │
                                              ▼
                                           Ausgabe

Vorteil: Kein DRAM-Engpass, minimale Latenz, hohe Energieeffizienz
```

### 2.3 M.2-Modul

| Parameter                 | Wert                                                        |
|---------------------------|-------------------------------------------------------------|
| **Formfaktor**            | M.2 2242 (22 × 42 mm)                                       |
| **Key**                   | B+M (im AI Kit) oder A+E                                    |
| **PCIe-Schnittstelle**    | Gen 3.0 ×2 (Modul-seitig)                                   |
| **Anbindung am Pi 5**     | PCIe Gen 2.0 ×1 (Standard) oder Gen 3.0 ×1 (konfigurierbar) |
| **Bandbreite (Gen 3 ×1)** | ~985 MB/s (unidirektional)                                  |
| **Bandbreite (Gen 2 ×1)** | ~500 MB/s (unidirektional)                                  |
| **Versorgungsspannung**   | 3,3 V (über M.2-Slot)                                       |
| **Geräte-Datei**          | `/dev/hailo0`                                               |
| **PCIe Vendor/Device-ID** | `1e60:2864`                                                 |

> **PCIe Gen 3 vs. Gen 2:** Der Raspberry Pi 5 nutzt standardmäßig PCIe Gen 2.0 ×1. Für die volle Leistung des Hailo-8L empfiehlt sich die Aktivierung von Gen 3.0 (Abschnitt 4.2). Bei Gen 2 ist die Inferenzleistung um ca. 30–50 % reduziert, da die PCIe-Bandbreite zum Engpass wird.

### 2.4 Unterstützte Modelltypen

| Aufgabe                   | Beispielmodelle                                         | Typische FPS (Hailo-8L, Pi 5, Gen 3) |
|---------------------------|---------------------------------------------------------|--------------------------------------|
| **Objekterkennung**       | YOLOv5s/n, YOLOv6n, YOLOv8s/n, YOLOX-s, SSD-MobileNetV2 | 100 … 350                            |
| **Pose Estimation**       | YOLOv8s-Pose                                            | ~120                                 |
| **Instanz-Segmentierung** | YOLOv5n-Seg                                             | ~100                                 |
| **Tiefenschätzung**       | Fast-Depth, StereoNet                                   | ~50 … 80                             |
| **Gesichtserkennung**     | YOLOv5s-PersonFace                                      | ~150                                 |
| **Klassifizierung**       | EfficientNet, ResNet-50, MobileNetV3                    | ~200 … 500                           |

> **Benchmark-Referenz (Hailo Community):** YOLOv8s bei 640 × 640, INT8, Batch 8 auf Pi 5 + Hailo-8L (Gen 3): ~128 FPS reine Inferenz. In einer realen GStreamer-Pipeline mit Kameraeingang und Overlay liegt die End-to-End-Leistung bei ~30 … 40 FPS, begrenzt durch Kamera-Framerate und CPU-seitige Vorverarbeitung.

### 2.5 Modellformat: HEF (Hailo Executable Format)

Neuronale Netze werden nicht direkt auf dem Hailo-8L ausgeführt, sondern müssen zuvor mit dem **Hailo Dataflow Compiler (DFC)** in das proprietäre HEF-Format kompiliert werden. Dieser Schritt umfasst Quantisierung (FP32 → INT8), Layer-Fusion und Hardware-Mapping.

```
Modell-Pipeline:

  TensorFlow / PyTorch / ONNX / Keras
                │
                ▼
  ┌──────────────────────┐
  │  Hailo Dataflow       │    ← Auf x86-Entwicklungsrechner
  │  Compiler (DFC)       │       oder Hailo Model Zoo
  │                       │
  │  1. Parsing (ONNX)    │
  │  2. Optimierung       │
  │  3. Quantisierung     │
  │     (FP32 → INT8)     │
  │  4. HW-Mapping        │
  │  5. Kompilierung      │
  └───────────┬───────────┘
              │
              ▼
        model.hef          ← Hailo Executable Format
              │
              ▼
  ┌───────────────────────┐
  │  HailoRT (Runtime)    │    ← Auf Raspberry Pi 5
  │  Inferenz auf NPU     │
  └───────────────────────┘
```

Hailo stellt über den **Hailo Model Zoo** vorkompilierte HEF-Dateien für gängige Modelle bereit. Für eigene Modelle muss der DFC auf einem x86-Rechner mit Ubuntu ausgeführt werden.

---

## 3 Hardware-Aufbau

### 3.1 Raspberry Pi AI Kit (Empfehlung)

Das offizielle Raspberry Pi AI Kit enthält:

| Komponente                     | Beschreibung                            |
|--------------------------------|-----------------------------------------|
| **Raspberry Pi M.2 HAT+**      | Adapterplatine PCIe FPC → M.2 Key M/B+M |
| **Hailo-8L M.2 Modul**         | Vorinstalliert auf dem HAT+             |
| **Thermal Pad**                | Wärmeleitpad zwischen Modul und HAT+    |
| **PCIe-Flachbandkabel (FPC)**  | Verbindung Pi 5 → HAT+                  |
| **Abstandshalter + Schrauben** | Montage über den GPIO-Header            |
| **GPIO-Stacking-Header**       | 16 mm, zum Durchschleifen der GPIOs     |

### 3.2 Montage

```
Seitenansicht (Raspberry Pi 5 + AI Kit):

  ┌─────────────────────────────────┐
  │   M.2 HAT+ mit Hailo-8L        │  ← Oberste Ebene
  │   ┌───────────────────────┐     │
  │   │  Hailo-8L (M.2 2242)  │     │
  │   │  [Thermal Pad]        │     │
  │   └───────────────────────┘     │
  │                                  │
  └─────────┬───────────────┬───────┘
            │ Abstandshalter│ (11 mm)
            │  + GPIO-      │
            │  Stacking-    │
            │  Header       │
  ┌─────────┴───────────────┴───────┐
  │   Raspberry Pi 5                 │
  │                                  │
  │   ┌──── PCIe FPC ────┐          │
  │   │  (Flachbandkabel) │          │
  │   └───────────────────┘          │
  │                                  │
  │   [Active Cooler empfohlen]      │
  └──────────────────────────────────┘
```

| Schritt | Aktion                                                                                     |
|---------|--------------------------------------------------------------------------------------------|
| 1       | Pi 5 stromlos; Active Cooler montieren                                                     |
| 2       | Vier Abstandshalter in die gelben Löcher des Pi 5 schrauben                                |
| 3       | GPIO-Stacking-Header aufstecken                                                            |
| 4       | PCIe-FPC-Kabel am Pi-5-PCIe-Anschluss einstecken (Kontakte nach innen, Richtung USB-Ports) |
| 5       | M.2 HAT+ auf Abstandshalter setzen, mit kurzen Schrauben fixieren                          |
| 6       | FPC-Kabel am HAT+ einstecken                                                               |
| 7       | Thermal Pad zwischen Hailo-8L und HAT+ prüfen (Wärmeleitung)                               |

> **Kühlung:** Der Hailo-8L erzeugt unter Last ~1,5 W Abwärme. Das Thermal Pad leitet die Wärme an die HAT+-Platine ab. In geschlossenen Gehäusen empfiehlt sich ein zusätzlicher Kühlkörper oder Lüfter auf dem HAT+. Der Pi 5 selbst benötigt den Active Cooler (insbesondere bei gleichzeitiger CPU-Last durch ROS 2).

> **Stromversorgung:** Das offizielle 27-W-USB-C-Netzteil (5,1 V / 5 A) wird empfohlen. Bei Unterspannung kann der Pi 5 die PCIe-Leistung drosseln und die Hailo-Inferenz wird instabil.

---

## 4 Software-Installation

### 4.1 Betriebssystem

Die Hailo-Software-Pakete werden offiziell für **Raspberry Pi OS (Bookworm/Trixie, 64 Bit)** bereitgestellt. Ubuntu 22.04 auf dem Pi 5 erfordert zusätzliche manuelle Schritte und Docker-Workarounds (Abschnitt 4.6).

```bash
# System aktualisieren (Raspberry Pi OS, 64 Bit)
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

### 4.2 PCIe Gen 3.0 aktivieren

```bash
# /boot/firmware/config.txt ergänzen:
dtparam=pciex1
dtparam=pciex1_gen=3

# Neustart
sudo reboot

# Prüfung: PCIe-Link-Geschwindigkeit
sudo lspci -vv | grep -i "lnksta"
# LnkSta: Speed 8GT/s, Width x1   ← Gen 3.0 bestätigt
# (Gen 2.0 wäre: Speed 5GT/s)
```

> **Hinweis zum AI HAT+ vs. M.2 HAT+:** Der AI HAT+ (integriertes Hailo-Modul) wird automatisch als Gen 3 erkannt. Beim M.2 HAT+ (separates Modul) muss Gen 3 manuell konfiguriert werden. Nicht alle Pi-5-Exemplare sind Gen-3-stabil; bei Instabilität auf Gen 2 zurückfallen.

### 4.3 Hailo-Software-Stack

```bash
# Alle Hailo-Pakete installieren (Raspberry Pi OS)
sudo apt install hailo-all
sudo reboot
```

Das Metapaket `hailo-all` installiert:

| Paket                           | Beschreibung                                       |
|---------------------------------|----------------------------------------------------|
| `hailort`                       | HailoRT Runtime (Treiber, CLI-Tools, C/C++ API)    |
| `hailo-dkms`                    | Kernel-Modul für PCIe-Kommunikation                |
| `python3-hailort`               | Python-Bindings für HailoRT                        |
| `hailo-tappas-core`             | GStreamer-Elemente und Nachverarbeitungsfunktionen |
| `rpicam-apps-hailo-postprocess` | Hailo-Postprocessing für rpicam-apps               |

### 4.4 Hardware-Verifizierung

```bash
# 1. PCIe-Gerät prüfen
lspci | grep Hailo
# 0000:01:00.0 Co-processor: Hailo Technologies Ltd. Hailo-8 AI Processor (rev 01)

# 2. Kernel-Modul prüfen
lsmod | grep hailo
# hailo_pci   ...

# 3. Geräte-Datei prüfen
ls -la /dev/hailo0
# crw------- 1 root root 511, 0 ... /dev/hailo0

# 4. Firmware-Version und Geräte-Info
hailortcli fw-control identify
# Executing on device: 0000:01:00.0
# Identifying board
# Control Protocol Version: 2
# Firmware Version: 4.19.0 (release,app,extended context switch buffer)
# Board Name: Hailo-8
# Device Architecture: HAILO8L
# Serial Number: HLDDLBB...
# Product Name: HAILO-8L AI ACC M.2 B+M KEY MODULE EXT TMP

# 5. GStreamer-Plugins prüfen
gst-inspect-1.0 hailotools
# hailonet, hailofilter, hailooverlay, ...
```

### 4.5 Versionskonsistenz

Die Hailo-Software erfordert exakte Versionsübereinstimmung zwischen HailoRT, TAPPAS Core, Kernel-Modul und Firmware. Ein Mismatch führt zu Fehlern wie `HAILO_UNSUPPORTED_FW_VERSION`.

```bash
# Versionen prüfen
dpkg -l | grep hailo
# hailort              4.19.0
# hailo-dkms           4.19.0
# hailo-tappas-core    3.30.0
# python3-hailort      4.19.0

# Bei Versionskonflikten: bestimmte Version erzwingen
sudo apt install hailort=4.19.0-3 hailo-dkms=4.19.0-1 \
    hailo-tappas-core=3.30.0-1 python3-hailort=4.19.0-2
```

### 4.6 Docker-Integration (Ubuntu 22.04 auf Pi 5)

Auf dem AMR-Raspberry-Pi-5 mit Ubuntu 22.04 (Docker-basiertes ROS-2-Setup) ist die Hailo-Integration komplexer. Der empfohlene Ansatz: HailoRT und Kernel-Modul auf dem Host installieren, GStreamer-Pipelines im Docker-Container ausführen.

```yaml
# docker-compose.yml – Hailo-Zugriff im Container
services:
  ai_perception:
    image: amr-ros2:humble
    network_mode: host
    privileged: true
    devices:
      - /dev/hailo0:/dev/hailo0
      - /dev/video0:/dev/video0    # Kamera
    volumes:
      - /lib/firmware/hailo:/lib/firmware/hailo:ro
      - /usr/lib/aarch64-linux-gnu/libhailort*:/usr/lib/aarch64-linux-gnu/:ro
    environment:
      - HAILO_DEVICE=/dev/hailo0
```

---

## 5 Inferenz-Pipelines

### 5.1 Kamera-Demo (rpicam-apps)

Die schnellste Methode zum Testen des Hailo-8L nutzt die integrierten rpicam-apps:

```bash
# Objekterkennung (YOLOv6)
rpicam-hello -t 0 \
    --post-process-file /usr/share/rpi-camera-assets/hailo_yolov6_inference.json \
    --lores-width 640 --lores-height 640

# Objekterkennung (YOLOv8)
rpicam-hello -t 0 \
    --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
    --lores-width 640 --lores-height 640

# Pose Estimation (YOLOv8-Pose, 17-Punkt-Skelett)
rpicam-hello -t 0 \
    --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_pose.json \
    --lores-width 640 --lores-height 640

# Instanz-Segmentierung
rpicam-hello -t 0 \
    --post-process-file /usr/share/rpi-camera-assets/hailo_yolov5_segmentation.json \
    --lores-width 640 --lores-height 640 --framerate 20
```

### 5.2 GStreamer-Pipeline (fortgeschritten)

Für die Integration in ROS 2 oder benutzerdefinierte Anwendungen bietet GStreamer direkte Kontrolle:

```bash
# GStreamer-Pipeline: Kamera → Hailo-8L → Overlay → Display
gst-launch-1.0 \
    libcamerasrc ! \
    video/x-raw,width=640,height=640,framerate=30/1 ! \
    queue ! \
    videoconvert ! \
    hailonet hef-path=/path/to/yolov8s.hef \
        batch-size=1 \
        nms-score-threshold=0.5 \
        nms-iou-threshold=0.45 ! \
    queue ! \
    hailooverlay ! \
    videoconvert ! \
    autovideosink
```

### 5.3 Python-API (HailoRT)

```python
#!/usr/bin/env python3
"""Hailo-8L Inferenz-Beispiel mit HailoRT Python-API."""

from hailo_platform import (
    HEF, VDevice, HailoStreamInterface,
    InferVStreams, ConfigureParams,
    InputVStreamParams, OutputVStreamParams,
    FormatType
)
import numpy as np

# HEF-Modell laden
hef = HEF("/path/to/yolov8s.hef")

# Virtuelles Gerät erstellen (automatische Geräteerkennung)
with VDevice() as device:
    # Netzwerk konfigurieren
    configure_params = ConfigureParams.create_from_hef(
        hef=hef,
        interface=HailoStreamInterface.PCIe
    )
    network_group = device.configure(hef, configure_params)[0]

    # Stream-Parameter
    input_params = InputVStreamParams.make(
        network_group,
        format_type=FormatType.UINT8
    )
    output_params = OutputVStreamParams.make(
        network_group,
        format_type=FormatType.FLOAT32
    )

    # Inferenz ausführen
    with InferVStreams(network_group, input_params, output_params) as pipeline:
        # Eingabebild vorbereiten (640 × 640 × 3, UINT8)
        input_data = {
            pipeline.get_input_vstream_infos()[0].name:
                np.random.randint(0, 255, (1, 640, 640, 3), dtype=np.uint8)
        }

        # Inferenz
        results = pipeline.infer(input_data)

        # Ergebnisse verarbeiten
        for name, output in results.items():
            print(f"Output '{name}': Shape {output.shape}, "
                  f"Typ {output.dtype}")
```

### 5.4 Benchmark-Tool

```bash
# Reine Inferenzgeschwindigkeit messen (ohne Vor-/Nachverarbeitung)
hailortcli run /path/to/yolov8s.hef

# Beispielausgabe (Hailo-8L, Pi 5, Gen 3, Batch 8):
# Network yolov8s/yolov8s: 127.85 FPS
```

---

## 6 ROS-2-Integration

### 6.1 Detektions-Node (Konzept)

Ein ROS-2-Node auf dem Raspberry Pi 5 kombiniert Kameradaten mit der Hailo-Inferenz und publiziert erkannte Objekte:

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  Kamera       │────►│  Hailo Detektions-   │────►│  /detected_objects│
│  /image_raw   │     │  Node               │     │  vision_msgs/     │
│               │     │                      │     │  Detection2DArray │
│               │     │  1. Bild empfangen   │     └──────────────────┘
│               │     │  2. Resize + Preproc │
│               │     │  3. Hailo Inferenz   │     ┌──────────────────┐
│               │     │  4. NMS + Postproc   │────►│  /image_annotated │
│               │     │  5. Publizieren      │     │  sensor_msgs/     │
└──────────────┘     └──────────────────────┘     │  Image            │
                                                   └──────────────────┘
```

### 6.2 Beispiel: ROS-2-Detektions-Node (Python)

```python
#!/usr/bin/env python3
"""ROS 2 Node: Objekterkennung mit Hailo-8L NPU."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import cv2
import numpy as np

from hailo_platform import HEF, VDevice, InferVStreams
from hailo_platform import (
    InputVStreamParams, OutputVStreamParams,
    ConfigureParams, HailoStreamInterface, FormatType
)

# COCO-Klassennamen (Auszug)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant",
    "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    # ... (80 Klassen insgesamt)
]

class HailoDetectionNode(Node):
    def __init__(self):
        super().__init__('hailo_detection_node')

        # Parameter
        self.declare_parameter('hef_path', '/path/to/yolov8s.hef')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('input_size', 640)

        hef_path = self.get_parameter('hef_path').value
        self.conf_thresh = self.get_parameter('confidence_threshold').value
        self.input_size = self.get_parameter('input_size').value

        # Hailo initialisieren
        self.hef = HEF(hef_path)
        self.device = VDevice()
        configure_params = ConfigureParams.create_from_hef(
            hef=self.hef, interface=HailoStreamInterface.PCIe)
        self.network_group = self.device.configure(self.hef, configure_params)[0]

        self.input_params = InputVStreamParams.make(
            self.network_group, format_type=FormatType.UINT8)
        self.output_params = OutputVStreamParams.make(
            self.network_group, format_type=FormatType.FLOAT32)

        self.pipeline = InferVStreams(
            self.network_group, self.input_params, self.output_params)
        self.pipeline.__enter__()

        self.input_name = self.pipeline.get_input_vstream_infos()[0].name

        # ROS 2
        self.bridge = CvBridge()
        self.sub_image = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.pub_detections = self.create_publisher(
            Detection2DArray, '/detected_objects', 10)

        self.get_logger().info(
            f'Hailo Detection Node gestartet (Modell: {hef_path})')

    def image_callback(self, msg: Image):
        # Bild konvertieren
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        h_orig, w_orig = frame.shape[:2]

        # Vorverarbeitung: Resize auf Modell-Eingabegröße
        resized = cv2.resize(frame, (self.input_size, self.input_size))
        input_data = {self.input_name:
            np.expand_dims(resized, axis=0).astype(np.uint8)}

        # Hailo-Inferenz
        results = self.pipeline.infer(input_data)

        # Nachverarbeitung und ROS-2-Message erstellen
        det_array = Detection2DArray()
        det_array.header = msg.header

        # (Modellspezifische Ausgabe-Dekodierung hier)
        # Ergebnisse als Detection2D publizieren
        self.pub_detections.publish(det_array)

    def destroy_node(self):
        self.pipeline.__exit__(None, None, None)
        self.device.release()
        super().destroy_node()


def main():
    rclpy.init()
    node = HailoDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 6.3 AMR-Anwendungsfälle

| Anwendung                    | Modell           | Nutzen für AMR                          |
|------------------------------|------------------|-----------------------------------------|
| **Personenerkennung**        | YOLOv8s (COCO)   | Sicherheitsabstand, Social Navigation   |
| **Hindernisklassifizierung** | YOLOv8n (Custom) | Unterscheidung: Stuhl, Tisch, Wand, Tür |
| **Türerkennung**             | Custom Detection | Autonomes Durchfahren von Türen         |
| **Bodenbeschaffenheit**      | Segmentierung    | Befahrbare Fläche erkennen              |
| **Gestenerkennung**          | Pose Estimation  | Mensch-Roboter-Interaktion              |

---

## 7 Leistungsoptimierung

### 7.1 PCIe-Bandbreite

| Konfiguration            | Bandbreite    | Auswirkung                  |
|--------------------------|---------------|-----------------------------|
| PCIe Gen 2 ×1 (Standard) | ~500 MB/s     | Inferenz ~30–50 % langsamer |
| **PCIe Gen 3 ×1**        | **~985 MB/s** | **Volle Hailo-8L-Leistung** |

### 7.2 Batch-Size

Die Batch-Größe bestimmt, wie viele Bilder gleichzeitig durch die NPU verarbeitet werden. Höhere Batch-Werte verbessern den Durchsatz, erhöhen aber die Latenz.

| Batch-Size | Durchsatz (YOLOv8s) | Latenz pro Bild | Empfehlung                          |
|------------|---------------------|-----------------|-------------------------------------|
| 1          | ~30 FPS             | ~33 ms          | Niedrigste Latenz (AMR Echtzeit)    |
| 4          | ~80 FPS             | ~50 ms          | Guter Kompromiss                    |
| **8**      | **~128 FPS**        | ~62 ms          | **Maximaler Durchsatz (Benchmark)** |

> **Empfehlung für AMR:** Batch-Size **1** für minimale Latenz (Echtzeit-Hinderniserkennung). Bei Multi-Stream-Anwendungen (z. B. mehrere Kameras) kann Batch 4–8 sinnvoll sein.

### 7.3 Modellwahl

| Modell          | Eingabe   | Parameter | Hailo-8L FPS   | Genauigkeit (mAP50) |
|-----------------|-----------|-----------|----------------|---------------------|
| **YOLOv8n**     | 640 × 640 | 3,2 M     | **~200 … 350** | ~37 %               |
| **YOLOv8s**     | 640 × 640 | 11,2 M    | **~55 … 128**  | ~45 %               |
| YOLOv8m         | 640 × 640 | 25,9 M    | ~30 … 60       | ~50 %               |
| YOLOv6n         | 640 × 640 | 4,7 M     | ~300 … 350     | ~36 %               |
| SSD-MobileNetV2 | 300 × 300 | 3,4 M     | ~145           | ~22 %               |

> **Empfehlung für AMR:** **YOLOv8n** (Nano) bietet die beste Balance aus Geschwindigkeit und Genauigkeit für die AMR-Personenerkennung. YOLOv8s als Alternative, wenn höhere Erkennungsgenauigkeit gefordert ist.

### 7.4 Thermische Überwachung

```bash
# Hailo-Chip-Temperatur abfragen
hailortcli fw-control identify | grep -i temp
# oder
hailortcli measure-power

# Raspberry Pi 5 CPU-Temperatur
vcgencmd measure_temp
# temp=55.0'C
```

Die Hailo-8L-Spezifikation erlaubt bis +85 °C. In der Praxis sollte die Chip-Temperatur unter 70 °C bleiben, um thermisches Throttling zu vermeiden.


---

## 9 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   Hailo-8L NPU – Kurzprofil für AMR-Integration                        │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   CHIP                       │                                           │
│   Bezeichnung                │ Hailo-8L (Entry-Level AI Accelerator)    │
│   Architektur                │ Dataflow Architecture (proprietär)       │
│   Rechenleistung             │ 13 TOPS (INT8)                           │
│   Energieeffizienz           │ ~8 TOPS/W                                │
│   Leistungsaufnahme          │ ~1,5 W (typisch)                         │
│   Betriebstemperatur         │ −40 … +85 °C                            │
│                              │                                           │
│   MODUL                      │                                           │
│   Formfaktor                 │ M.2 2242 Key B+M                        │
│   Schnittstelle (Modul)      │ PCIe Gen 3.0 ×2                         │
│   Schnittstelle (Pi 5)       │ PCIe Gen 3.0 ×1 (konfigurierbar)       │
│   Geräte-Datei               │ /dev/hailo0                              │
│   PCIe Vendor/Device-ID      │ 1e60:2864                                │
│   Versorgung                 │ 3,3 V via M.2-Slot                      │
│                              │                                           │
│   LEISTUNG (Pi 5, Gen 3)    │                                           │
│   YOLOv8n (640², Batch 1)   │ ~200 … 350 FPS (reine Inferenz)         │
│   YOLOv8s (640², Batch 8)   │ ~128 FPS (reine Inferenz)               │
│   YOLOv8s (End-to-End)      │ ~30 … 40 FPS (mit Kamera + Overlay)     │
│   YOLOv8s-Pose              │ ~123 FPS (reine Inferenz)                │
│                              │                                           │
│   SOFTWARE-STACK             │                                           │
│   Runtime                    │ HailoRT (hailort)                        │
│   GStreamer-Plugins          │ hailo-tappas-core (hailonet, hailofilter)│
│   Python-API                 │ python3-hailort (hailo_platform)         │
│   Modellformat               │ HEF (Hailo Executable Format)           │
│   Modell-Compiler            │ Hailo Dataflow Compiler (DFC, x86)      │
│   Vorkompilierte Modelle     │ Hailo Model Zoo                          │
│   Kamera-Integration         │ rpicam-apps (Bookworm/Trixie)           │
│   Beispiel-Repository        │ hailo-rpi5-examples / hailo-apps        │
│                              │                                           │
│   FRAMEWORKS (Quell-Modelle) │                                           │
│   Unterstützt                │ TensorFlow, TF Lite, ONNX, Keras,       │
│                              │ PyTorch                                   │
│   Quantisierung              │ FP32 → INT8 (im DFC, automatisch)       │
│                              │                                           │
│   AMR-INTEGRATION            │                                           │
│   Hauptanwendung             │ Echtzeit-Objekterkennung (YOLOv8n/s)    │
│   ROS-2-Topic                │ /detected_objects                        │
│   Nachrichtentyp             │ vision_msgs/Detection2DArray             │
│   Empfohlenes Modell         │ YOLOv8n (Geschwindigkeit)               │
│                              │ YOLOv8s (Genauigkeit)                    │
│   Empfohlene Batch-Size      │ 1 (AMR Echtzeit, min. Latenz)           │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 10 Quellen

| Quelle                                            | URL                                                                                                                           |
|---------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Hailo-8L M.2 Modul – Produktseite                 | [hailo.ai/products](https://hailo.ai/products/ai-accelerators/hailo-8l-m-2-ai-acceleration-module-for-ai-light-applications/) |
| Raspberry Pi AI Kit – Dokumentation               | [raspberrypi.com (AI Kit)](https://www.raspberrypi.com/documentation/accessories/ai-kit.html)                                 |
| Raspberry Pi AI Software – Installationsanleitung | [raspberrypi.com (AI Software)](https://www.raspberrypi.com/documentation/computers/ai.html)                                  |
| hailo-rpi5-examples (GitHub)                      | [github.com/hailo-ai/hailo-rpi5-examples](https://github.com/hailo-ai/hailo-rpi5-examples)                                    |
| hailo-apps (GitHub, aktuell)                      | [github.com/hailo-ai/hailo-apps](https://github.com/hailo-ai/hailo-apps)                                                      |
| Hailo-8L Benchmark (Hailo Community)              | [community.hailo.ai (Benchmark)](https://community.hailo.ai/t/raspberry-pi-5-with-hailo-8l-benchmark/746)                     |
| Hailo Model Zoo / Model Explorer                  | [hailo.ai/model-zoo](https://hailo.ai/developer-zone/model-zoo/)                                                              |
| HailoRT Python API Dokumentation                  | [hailo.ai/developer-zone](https://hailo.ai/developer-zone/)                                                                   |
| RPi 5 AI Kit Setup Guide (Dataroot Labs)          | [datarootlabs.com](https://datarootlabs.com/blog/hailo-ai-kit-raspberry-pi-5-setup-and-computer-vision-pipelines)             |
| Ubuntu Hacker's Guide (Canonical)                 | [ubuntu.com/blog](https://ubuntu.com/blog/hackers-guide-to-the-raspberry-pi-ai-kit-on-ubuntu)                                 |
| Raspberry Pi PCIe Database (Jeff Geerling)        | [pipci.jeffgeerling.com](https://pipci.jeffgeerling.com/cards_m2/hailo-8l-ai-module.html)                                     |

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: Hailo-8L Produktspezifikation, Raspberry Pi AI Kit/AI HAT+ Dokumentation, Hailo Community Benchmarks, hailo-rpi5-examples GitHub, HailoRT API Dokumentation*
