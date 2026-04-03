---
title: Aufbau und Ersteinrichtung
description: Schritt-fuer-Schritt Ersteinrichtung der AMR-Plattform.
---

# Aufbau und Ersteinrichtung

## Voraussetzungen

### Software

- Docker ab Version 20.x
- Docker Compose ab Version 2.x
- PlatformIO CLI (`pip install platformio`)
- Node.js 20+ (fuer das Dashboard)
- mkcert (HTTPS-Zertifikate)
- `GEMINI_API_KEY` in der Host-Umgebung (fuer Vision und TTS; nicht fuer Sprachsteuerung)

### Gruppenzugehoerigkeit

Das Benutzerkonto muss Mitglied der Gruppen `docker`, `dialout`, `video` und `audio` sein:

```bash
id -nG   # Ausgabe muss docker, dialout, video, audio enthalten
```

## 1. Host-Setup

Das Host-Setup richtet udev-Regeln, Gruppenzugehoerigkeiten, X11-Zugriff, CAN-Service und die Kamera-Bridge ein:

```bash
cd amr/docker/
sudo bash host_setup.sh
```

Nach Abschluss Benutzerkonto neu anmelden (Gruppenaenderungen wirksam machen).

## 2. Docker-Image bauen

```bash
cd amr/docker/
docker compose build    # ~15–20 Min auf Pi 5
```

## 3. Setup verifizieren

```bash
cd amr/docker/
./verify.sh
```

Die Ausgabe `Verifikation BESTANDEN` mit `0 FAIL` bestaetigt ein vollstaendiges Setup.

## 4. Firmware flashen

!!! warning "Immer `-e` angeben"
    `pio run -t upload` ohne `-e` flasht ALLE Environments.

### Drive-Knoten

```bash
cd amr/mcu_firmware/drive_node/
pio run -e drive_node -t upload -t monitor
```

### Sensor-Knoten

```bash
cd amr/mcu_firmware/sensor_node/
pio run -e sensor_node -t upload -t monitor
```

Erster Build pro Knoten: ~15 Min (micro-ROS aus Source). Die Status-LED am Drive-Knoten signalisiert:

- **Langsames Blinken:** Suche nach micro-ROS-Agent (normal vor Container-Start)
- **Schnelles Blinken:** Initialisierungsfehler
- **Gedimmtes Heartbeat:** Betriebsbereit

## 5. ROS2-Workspace bauen

```bash
cd amr/docker/
./run.sh colcon build --packages-select my_bot --symlink-install
```

## 6. Inbetriebnahme

### Serielle Schnittstellen freigeben

```bash
sudo fuser -v /dev/amr_drive /dev/amr_sensor    # Keine aktiven Prozesse
```

### Roboter einschalten

1. Akkupack anschliessen, Hauptsicherung pruefen
2. USB-C-Verbindungen beider ESP32-S3 pruefen
3. RPLIDAR A1 per USB anschliessen
4. Warten bis Status-LED langsam blinkt

### ROS2-Stack starten

```bash
cd amr/docker/
./run.sh ros2 launch my_bot full_stack.launch.py
```

### Verbindung pruefen

```bash
./run.sh exec ros2 topic hz /odom    # ~18–22 Hz
./run.sh exec ros2 topic hz /cliff   # ~20 Hz
./run.sh exec ros2 topic hz /scan    # ~7–8 Hz
```
