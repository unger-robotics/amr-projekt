---
title: "AMR Showcase: Edge-KI trifft Intralogistik"
subtitle: "Vom physischen Sensorwert zur semantischen Cloud-Entscheidung"
author: "Jan Unger"
date: "10. Maerz 2026"
theme: "metropolis"
---

## Das Ziel: Ein Low-Cost AMR fuer KLT-Transporte

**Das Problem**
* Industrielle Flotten (z. B. MiR100) kosten $> 25.000$ EUR.
* Fuer leichte Transporte (KLT) ist das massiv ueberdimensioniert.
* Reine Software-Stacks auf Raspberry Pis scheitern oft an harter Echtzeit (Motor-Jitter).

**Die Loesung**
* Ein modularer Stack auf Basis von ROS 2 Humble.
* Hardwarekosten: **~513 EUR**.
* Strikte Trennung von High-Level KI und Low-Level Motorik.

---

## Die 4 Saeulen der Systemarchitektur

Der Datenfluss verlaeuft deterministisch von links nach rechts:

![Architektur und Datenfluss des AMR](amr_datenfluss.pdf){width=30%}

1.  **Sensorik:** LiDAR, Kamera, IMU, Encoder.
2.  **Edge-KI:** Raspberry Pi 5 + Hailo-8L NPU fuer SLAM und Objekterkennung.
3.  **Cloud-KI:** Gemini API loest logische Blockaden auf Basis von Semantik.
4.  **Aktorik:** ESP32-S3 uebernimmt die 50 Hz Echtzeit-PID-Regelung.

---

## Edge-KI: Die Navigations-Pipeline

Die lokale Ebene reagiert in Millisekunden auf dynamische Hindernisse:

![Navigations-Pipeline (ROS 2 Nav2 Stack)](amr_nav2_pipeline.pdf){width=30%}

* **SLAM Toolbox:** Generiert eine 2D-Gitterkarte ($5\,\mathrm{cm}$ Aufloesung).
* **Nav2:** Plant globale Pfade und faehrt sie per Regulated Pure Pursuit ($0{,}4\,\mathrm{m/s}$) ab.
* **Hailo-8L:** Erkennt per YOLOv8 parallel Hindernisse im Videostream bei ${\sim}\,34\,\mathrm{ms}$ Latenz, ohne die RPi-CPU zu blockieren.

---

## Aktorik: Der Dual-Core Mikrocontroller

Waehrend ROS 2 die Pfade plant, sorgt der ESP32-S3 fuer die sichere Umsetzung:

![Dual-Core Architektur ESP32-S3](amr_esp32_dualcore.pdf){width=30%}

* **Core 0:** Managt den XRCE-DDS (micro-ROS) Stream bei $921\,600$ Baud.
* **Core 1:** Fuehrt exklusiv und jitterfrei ($< 2\,\mathrm{ms}$) die Regelschleife aus.
* **Hardware-Redundanz:** Ein direkter CAN-Bus vom Sensor-Node blockiert die Motoren bei erkannten Abgruenden ($< 20\,\mathrm{ms}$ Reaktionszeit) – unabhaengig von ROS 2.

---

## Die semantische Cloud-Entscheidung

**Was passiert, wenn Nav2 feststeckt?**

* Der Roboter stoppt vor einem unbekannten, blockierenden Hindernis.
* Das System uebergibt das erkannte YOLO-Label (z. B. "Mensch") sowie Telemetriedaten als JSON an die **Gemini API**.
* Die LLM-Logik entscheidet kontextbasiert:
  * Handelt es sich um ein statisches Objekt? $\rightarrow$ *Recovery-Verhalten und Umfahrung.*
  * Handelt es sich um einen Menschen im Gang? $\rightarrow$ *Warten und Sprachwarnung ueber den PCM5102A-DAC ausgeben.*

---

## Live-Demo

**Szenario:** Punkt-zu-Punkt Navigation mit Hinderniserkennung.

```bash
# Gesamten ROS 2 Stack inklusive Dashboard und Vision starten
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py \
    use_dashboard:=True use_vision:=True
```
