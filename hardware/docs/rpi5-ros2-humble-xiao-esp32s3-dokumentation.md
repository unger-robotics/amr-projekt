# Raspberry Pi 5 + ROS 2 Humble (Docker) + Seeed XIAO ESP32-S3 (micro-ROS)

> **Technische Dokumentation** – Systemintegration für autonome mobile Robotik (AMR)
> Host: Raspberry Pi 5 (8 GB) | OS: Raspberry Pi OS Trixie (Debian 13, aarch64)
> ROS 2: Humble Hawksbill via Docker (Ubuntu 22.04 arm64)
> MCU: Seeed Studio XIAO ESP32-S3 | Firmware: micro-ROS Client (FreeRTOS)
> Kommunikation: USB-Serial oder WiFi-UDP über micro-ROS Agent
> Quellen: [ROS 2 Humble Dokumentation](https://docs.ros.org/en/humble/), [micro-ROS](https://micro.ros.org/), [Seeed Studio Wiki XIAO ESP32S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/), [Raspberry Pi OS Trixie Ankündigung](https://www.raspberrypi.com/news/trixie-the-new-version-of-raspberry-pi-os/), [micro_ros_espidf_component (GitHub)](https://github.com/micro-ROS/micro_ros_espidf_component)

---

## 1 Systemübersicht

### 1.1 Architektur

Das System besteht aus zwei Ebenen: einem leistungsfähigen Einplatinencomputer (Raspberry Pi 5) als ROS-2-Host und einem ressourcenbeschränkten Mikrocontroller (Seeed XIAO ESP32-S3) als Echtzeit-Sensorik- und Aktorik-Knoten. Die Kopplung erfolgt über das micro-ROS-Framework, das den Mikrocontroller als vollwertigen ROS-2-Teilnehmer in den DDS-Graphen (Data Distribution Service) einbindet.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROS 2 DDS-Domäne                             │
│                                                                 │
│  ┌──────────────────────────────────────────────┐               │
│  │  Docker-Container (Ubuntu 22.04 arm64)       │               │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐ │               │
│  │  │ Nav2     │  │ SLAM     │  │ Eigene     │ │               │
│  │  │ Stack    │  │ Toolbox  │  │ Nodes      │ │               │
│  │  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │               │
│  │       │              │              │        │               │
│  │  ─────┴──────────────┴──────────────┴─────── │               │
│  │              ROS 2 Humble (DDS)              │               │
│  │  ────────────────────┬─────────────────────  │               │
│  │                      │                       │               │
│  │              ┌───────┴────────┐              │               │
│  │              │ micro-ROS      │              │               │
│  │              │ Agent          │              │               │
│  │              └───────┬────────┘              │               │
│  └──────────────────────┼───────────────────────┘               │
│                         │                                       │
│  Raspberry Pi 5 (Host)  │  USB-Serial (/dev/ttyACM0)           │
│  Debian Trixie (aarch64)│  oder WiFi-UDP (Port 8888)           │
└─────────────────────────┼───────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │ Micro XRCE-DDS Client │
              │                       │
              │ Seeed XIAO ESP32-S3   │
              │ FreeRTOS + micro-ROS  │
              │                       │
              │ ├─ IMU (I²C)          │
              │ ├─ Motortreiber (PWM) │
              │ ├─ Encoder (GPIO)     │
              │ └─ Batterie-ADC       │
              └───────────────────────┘
```

### 1.2 Kommunikationspfad

Der micro-ROS Agent fungiert als Brücke zwischen dem DDS-Netzwerk (ROS 2) und dem Micro-XRCE-DDS-Protokoll (eXtremely Resource Constrained Environment) auf dem Mikrocontroller. Zwei Transportwege stehen zur Verfügung:

| Transport      | Protokoll          | Latenz (typisch) | Vorteile                        | Nachteile                      |
|----------------|--------------------|------------------|---------------------------------|--------------------------------|
| **USB-Serial** | UART über USB-CDC  | < 1 ms           | Deterministisch, kein Paketloss | Kabelgebunden, ein Port belegt |
| **WiFi-UDP**   | UDP/IPv4 über WLAN | 2 … 20 ms        | Kabellos, flexibel              | Jitter, möglicher Paketverlust |

Für den AMR-Einsatz eignet sich USB-Serial als primärer Kanal (deterministische Motorsteuerung), WiFi-UDP als Alternative für Debugging oder als Backup.

---

## 2 Hardware-Spezifikationen

### 2.1 Raspberry Pi 5 (8 GB)

| Parameter             | Wert                                                    |
|-----------------------|---------------------------------------------------------|
| **SoC**               | Broadcom BCM2712, Quad-Core Arm Cortex-A76, 2,4 GHz     |
| **GPU**               | VideoCore VII, OpenGL ES 3.1, Vulkan 1.2                |
| **RAM**               | 8 GB LPDDR4X-4267                                       |
| **Speicher**          | microSD / NVMe SSD (via PCIe 2.0 ×1)                    |
| **USB**               | 2× USB 3.0 (5 Gbps), 2× USB 2.0                         |
| **GPIO**              | 40-Pin-Header (kompatibel zu Pi 4)                      |
| **Netzwerk**          | Gigabit Ethernet, Wi-Fi 5 (802.11ac), Bluetooth 5.0/BLE |
| **Kamera**            | 2× 4-Lane MIPI CSI-2                                    |
| **Video-Ausgang**     | 2× Micro-HDMI (bis 4Kp60)                               |
| **Stromversorgung**   | USB-C, 5 V / 5 A (27 W) empfohlen                       |
| **Leistungsaufnahme** | ~4 W (Idle), ~12 W (Volllast)                           |
| **Betriebssystem**    | Raspberry Pi OS Trixie (Debian 13), aarch64             |
| **Kernel**            | Linux 6.12 LTS (RPi-Patch)                              |
| **Abmessungen**       | 85 × 56 × 17 mm                                         |

### 2.2 Seeed Studio XIAO ESP32-S3

| Parameter                   | Wert                                                        |
|-----------------------------|-------------------------------------------------------------|
| **SoC**                     | Espressif ESP32-S3R8                                        |
| **Architektur**             | Xtensa® 32-bit LX7, Dual-Core                               |
| **Taktfrequenz**            | bis 240 MHz                                                 |
| **SRAM**                    | 512 KB (on-chip)                                            |
| **PSRAM**                   | 8 MB (extern, OPI)                                          |
| **Flash**                   | 8 MB (extern, QSPI)                                         |
| **WLAN**                    | 802.11 b/g/n, 2,4 GHz                                       |
| **Bluetooth**               | BLE 5.0                                                     |
| **USB**                     | USB 2.0 OTG (Type-C, nativ)                                 |
| **GPIO**                    | 11 nutzbare Pins (D0 … D10)                                 |
| **ADC**                     | 9 Kanäle, 12-bit SAR                                        |
| **PWM**                     | Alle GPIO-Pins (LEDC, 8 Timer)                              |
| **I²C**                     | Bis zu 2 Busse (konfigurierbar)                             |
| **SPI**                     | 1× verfügbar (+ 1 intern für Flash/PSRAM)                   |
| **UART**                    | Bis zu 2 (UART0 für USB-CDC, UART1 konfigurierbar)          |
| **Betriebsspannung**        | 3,3 V (Logik), 5 V (USB-Eingang)                            |
| **3,3-V-Ausgang**           | max. 700 mA (On-Board-Regler)                               |
| **Deep-Sleep-Strom**        | 14 µA                                                       |
| **Batterie-Lademanagement** | Ja (LiPo 3,7 V, On-Board)                                   |
| **Antenne**                 | U.FL-Anschluss (externe 2,4-GHz-Antenne, Reichweite >100 m) |
| **Abmessungen**             | 21 × 17,5 mm                                                |
| **Gewicht**                 | ~3 g                                                        |
| **Programmierung**          | Arduino IDE, PlatformIO, ESP-IDF v5.x                       |
| **Hersteller**              | Seeed Studio (Produkt-ID: 113991114)                        |

### 2.3 Pinbelegung XIAO ESP32-S3 (AMR-relevant)

```
         USB-C (oben)
        ┌───────────┐
   D0  ─┤ 1      14 ├─ D10
   D1  ─┤ 2      13 ├─ D9
   D2  ─┤ 3      12 ├─ D8
   D3  ─┤ 4      11 ├─ D7
   D4  ─┤ 5      10 ├─ D6
   D5  ─┤ 6       9 ├─ D5 (nicht doppelt, Nummerierung)
  5V  ─┤ 7       8 ├─ 3V3
  GND ─┤           ├─ GND
        └───────────┘

Pin-Zuordnung (ESP32-S3 GPIO):
  D0  = GPIO1  (A0, ADC)       D6  = GPIO43 (TX, Strapping!)
  D1  = GPIO2  (A1, ADC)       D7  = GPIO44 (RX, Strapping!)
  D2  = GPIO3  (A2, Strapping) D8  = GPIO7  (SCK, SPI)
  D3  = GPIO4  (A3, ADC)       D9  = GPIO8  (MISO, SPI)
  D4  = GPIO5  (A4, SDA, I²C)  D10 = GPIO9  (MOSI, SPI)
  D5  = GPIO6  (A5, SCL, I²C)
```

> **Strapping-Pins:** GPIO0, GPIO3, GPIO43, GPIO44 haben beim Bootvorgang definierte Zustände. Nach dem Start funktionieren sie als reguläre I/O-Pins, sollten aber bei externer Beschaltung mit Vorsicht eingesetzt werden.

### 2.4 Funktionszuordnung im AMR-System

| Funktion                | Pin(s)             | Protokoll      | Bemerkung                           |
|-------------------------|--------------------|----------------|-------------------------------------|
| micro-ROS (Serial)      | USB-C (nativ)      | USB-CDC        | Primärer Kommunikationskanal zum Pi |
| I²C-Bus (IMU, Sensoren) | D4 (SDA), D5 (SCL) | I²C @ 400 kHz  | GPIO5/GPIO6 als Standard-I²C        |
| Motor-PWM               | D0, D1             | LEDC PWM       | 2 Kanäle für H-Brücke               |
| Encoder A/B             | D2, D3             | GPIO-Interrupt | Quadratur-Decoder                   |
| Batterie-ADC            | D8 (A8)            | ADC1, 12-bit   | Spannungsteiler-Eingang             |
| Status-LED              | On-Board (GPIO21)  | Digital        | Programmierbare LED                 |

---

## 3 Raspberry Pi OS Trixie (Debian 13)

### 3.1 Überblick

Raspberry Pi OS Trixie basiert auf Debian 13 „Trixie" und wurde im Dezember 2025 offiziell veröffentlicht. Es löst die Bookworm-basierte Version (Debian 12) ab und bringt aktualisierte Kernkomponenten mit:

| Komponente    | Trixie (Debian 13) | Bookworm (Debian 12)    |
|---------------|--------------------|-------------------------|
| Linux-Kernel  | 6.12 LTS           | 6.1 LTS                 |
| GCC           | 14.x               | 12.x                    |
| Python        | 3.12               | 3.11                    |
| Docker Engine | 26.x+ (via apt)    | 24.x                    |
| systemd       | 256+               | 252                     |
| Desktop       | labwc (Wayland)    | labwc/Wayfire (Wayland) |

### 3.2 Installation (Neuinstallation empfohlen)

Die Raspberry Pi Foundation empfiehlt eine Neuinstallation anstelle eines In-Place-Upgrades von Bookworm. Für den AMR-Einsatz ist die **Lite-Variante** (ohne Desktop) ausreichend:

```bash
# 1. Image herunterladen (Raspberry Pi Imager oder manuell)
#    → Raspberry Pi OS (64-bit) Lite – Trixie
#    Datei: 2025-xx-xx-raspios-trixie-arm64-lite.img

# 2. Mit Raspberry Pi Imager auf NVMe SSD / microSD flashen
#    → Hostname: rover
#    → SSH aktivieren
#    → Benutzer: pi (oder eigener)
#    → WLAN konfigurieren (optional)

# 3. Erster Boot und System aktualisieren
sudo apt update && sudo apt full-upgrade -y
sudo reboot

# 4. Systeminfo prüfen
uname -a
# Linux rover 6.12.x+rpt-rpi-2712 ... aarch64 GNU/Linux

cat /etc/os-release | grep VERSION_CODENAME
# VERSION_CODENAME=trixie
```

### 3.3 Grundkonfiguration für AMR

```bash
# Notwendige Pakete
sudo apt install -y \
    git curl wget \
    python3-pip python3-venv \
    i2c-tools \
    udev \
    htop tmux

# I²C und SPI aktivieren
sudo raspi-config
# → Interface Options → I2C → Enable
# → Interface Options → SPI → Enable

# USB-Geräte-Berechtigungen für Docker
sudo usermod -aG dialout $USER
sudo usermod -aG docker $USER

# Non-PD-Netzteil konfigurieren (falls DC/DC-Wandler ohne USB-PD)
sudo nano /boot/firmware/config.txt
# Unter [all] einfügen:
# usb_max_current_enable=1
```

---

## 4 Docker-Installation und ROS 2 Humble

### 4.1 Warum Docker?

ROS 2 Humble Hawksbill (Mai 2022, EOL Mai 2027) ist offiziell für **Ubuntu 22.04 Jammy** paketiert. Raspberry Pi OS basiert auf Debian, das nur Tier-3-Support erhält (Kompilierung aus Quellcode erforderlich). Docker löst dieses Problem: Der ROS-2-Stack läuft in einem Ubuntu-22.04-Container auf dem Debian-Trixie-Host, mit vollem Tier-1-Support und binären Paketen.

| Aspekt               | Nativ auf Debian       | Docker (Ubuntu 22.04)           |
|----------------------|------------------------|---------------------------------|
| ROS-2-Support-Tier   | Tier 3 (Quellcode)     | **Tier 1 (Binärpakete)**        |
| Installationsaufwand | Stunden (colcon build) | **Minuten (docker pull)**       |
| Reproduzierbarkeit   | Abhängig von Host      | **Dockerfile = deklarativ**     |
| Hardware-Zugriff     | Direkt                 | Via `--privileged` / `--device` |
| Overhead             | Keiner                 | ~50 … 100 MB RAM, ~1 % CPU      |

### 4.2 Docker installieren

```bash
# Docker über offizielle Debian-Repos (Trixie)
sudo apt install -y docker.io docker-compose

# Alternativ: Docker CE (neueste Version)
curl -fsSL https://get.docker.com | sh

# Benutzer zur docker-Gruppe hinzufügen
sudo usermod -aG docker $USER
newgrp docker

# Verifikation
docker --version
# Docker version 26.x.x
docker run --rm hello-world
```

### 4.3 ROS 2 Humble Docker-Image

Docker erkennt automatisch die ARM64-Architektur des Raspberry Pi 5 und zieht das passende Image:

```bash
# Basis-Image (ros-base enthält Core + grundlegende Pakete)
docker pull ros:humble-ros-base

# Alternativ: Nur ROS-Core (minimal)
docker pull ros:humble-ros-core

# Image-Größe prüfen
docker images | grep humble
# ros    humble-ros-base    ...    ~800 MB (arm64)
```

### 4.4 Benutzerdefiniertes Dockerfile (AMR-Projekt)

Das folgende Dockerfile erweitert das Basis-Image um den micro-ROS Agent und projektspezifische Abhängigkeiten:

```dockerfile
# Datei: Dockerfile.amr-ros2
FROM ros:humble-ros-base

# Umgebungsvariablen
ENV ROS_DOMAIN_ID=0
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-humble-rmw-fastrtps-cpp \
    ros-humble-diagnostic-updater \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-xacro \
    git cmake build-essential \
    && rm -rf /var/lib/apt/lists/*

# micro-ROS Agent aus Quellcode bauen
WORKDIR /microros_ws
RUN mkdir -p src && \
    git clone --depth 1 --branch humble \
        https://github.com/micro-ROS/micro-ROS-Agent.git src/micro-ROS-Agent && \
    . /opt/ros/humble/setup.sh && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -y && \
    apt-get update && apt-get install -y ros-humble-fastcdr && \
    colcon build --symlink-install && \
    rm -rf /var/lib/apt/lists/* log/ build/

# AMR Workspace
WORKDIR /amr_ws
COPY src/ src/

# Automatisches Sourcing
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /microros_ws/install/setup.bash" >> ~/.bashrc

# Standardmäßig bash starten
CMD ["bash"]
```

### 4.5 Docker-Image bauen und starten

```bash
# Image bauen (auf dem Pi 5, dauert ca. 15-30 Minuten)
cd ~/amr-platform
docker build -t amr-ros2:humble -f Dockerfile.amr-ros2 .

# Alternativ: Vorgefertigtes micro-ROS Agent Image verwenden
docker pull microros/micro-ros-agent:humble

# Container starten (mit Hardware-Zugriff)
docker run -it --rm \
    --name=ros2_humble \
    --net=host \
    --privileged \
    -v /dev:/dev \
    -v ~/amr-platform/src:/amr_ws/src \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    -e ROS_DOMAIN_ID=0 \
    amr-ros2:humble \
    bash
```

**Erklärung der Docker-Flags:**

| Flag                     | Funktion                                           |
|--------------------------|----------------------------------------------------|
| `--net=host`             | Container teilt Host-Netzwerk (DDS-Discovery, UDP) |
| `--privileged`           | Voller Zugriff auf `/dev`-Geräte (USB, I²C, SPI)   |
| `-v /dev:/dev`           | Geräte-Dateien in Container einbinden              |
| `-v ~/…/src:/amr_ws/src` | Quellcode-Mount (Host ↔ Container)                 |
| `-e ROS_DOMAIN_ID=0`     | ROS-2-Domäne festlegen                             |

### 4.6 Docker-Compose (empfohlen für Produktion)

```yaml
# Datei: docker-compose.yml
version: '3.8'

services:
  ros2-base:
    image: amr-ros2:humble
    container_name: ros2_base
    network_mode: host
    privileged: true
    volumes:
      - /dev:/dev
      - ./src:/amr_ws/src
      - ./config:/amr_ws/config
    environment:
      - ROS_DOMAIN_ID=0
      - RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    command: >
      bash -c "source /opt/ros/humble/setup.bash &&
               source /microros_ws/install/setup.bash &&
               bash"
    stdin_open: true
    tty: true
    restart: unless-stopped

  microros-agent-serial:
    image: microros/micro-ros-agent:humble
    container_name: microros_agent
    network_mode: host
    privileged: true
    volumes:
      - /dev:/dev
    command: serial --dev /dev/ttyACM0 -b 115200 -v6
    restart: unless-stopped
    depends_on:
      - ros2-base

  microros-agent-udp:
    image: microros/micro-ros-agent:humble
    container_name: microros_agent_udp
    network_mode: host
    command: udp4 --port 8888 -v6
    restart: unless-stopped
    profiles:
      - wifi  # Nur mit --profile wifi starten
```

Starten:

```bash
# Serial-Agent + ROS 2 Base
docker compose up -d

# Mit WiFi-UDP-Agent zusätzlich
docker compose --profile wifi up -d

# Logs anzeigen
docker compose logs -f microros-agent-serial

# Alle Container stoppen
docker compose down
```

---

## 5 micro-ROS Agent

### 5.1 Rolle im System

Der micro-ROS Agent ist der zentrale Vermittler zwischen dem Micro-XRCE-DDS-Client auf dem ESP32-S3 und dem vollständigen DDS-Netzwerk von ROS 2. Der Agent:

1. Empfängt serialisierte Nachrichten vom ESP32-S3 (über Serial oder UDP)
2. Deserialisiert sie und veröffentlicht sie im DDS-Graphen
3. Empfängt Subscriptions aus dem DDS-Graphen und leitet sie an den ESP32-S3 weiter
4. Verwaltet die Lifecycle-Zustände der micro-ROS-Nodes

```
ESP32-S3                    micro-ROS Agent              ROS 2 DDS
┌──────────┐   XRCE-DDS    ┌──────────────┐   DDS      ┌──────────┐
│ Publisher ├───────────────┤              ├────────────┤ Subscriber│
│          │  (Serial/UDP)  │   Proxy /    │  (FastDDS) │          │
│ Subscriber├───────────────┤   Bridge     ├────────────┤ Publisher │
│          │                │              │            │          │
│ Service  ├───────────────┤              ├────────────┤ Service  │
│  Server  │                │              │            │  Client  │
└──────────┘                └──────────────┘            └──────────┘
```

### 5.2 Starten des Agents

**Variante A: Docker-Image (empfohlen)**

```bash
# Serial-Transport (USB)
docker run -it --rm \
    -v /dev:/dev \
    --privileged \
    --net=host \
    microros/micro-ros-agent:humble \
    serial --dev /dev/ttyACM0 -b 115200 -v6

# UDP-Transport (WiFi)
docker run -it --rm \
    --net=host \
    microros/micro-ros-agent:humble \
    udp4 --port 8888 -v6
```

**Variante B: Aus Quellcode (im ROS-2-Container)**

```bash
source /opt/ros/humble/setup.bash
source /microros_ws/install/setup.bash

# Serial
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 115200 -v6

# UDP
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888 -v6
```

### 5.3 USB-Geräte-Erkennung (udev-Regeln)

Der XIAO ESP32-S3 meldet sich am USB-Bus als CDC-ACM-Gerät. Die Gerätebezeichnung (`/dev/ttyACM0`, `/dev/ttyACM1` …) ist nicht determiniert und kann sich bei jedem Einstecken ändern. Eine udev-Regel schafft einen stabilen Symlink:

```bash
# Geräteinformationen ermitteln (XIAO einstecken, dann:)
udevadm info -a -n /dev/ttyACM0 | grep -E 'idVendor|idProduct|serial'
# idVendor: 303a (Espressif)
# idProduct: 1001 (USB JTAG/serial debug unit)

# udev-Regel erstellen
sudo tee /etc/udev/rules.d/99-xiao-esp32s3.rules << 'EOF'
# Seeed XIAO ESP32-S3 (Espressif USB-CDC)
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", \
    SYMLINK+="ttyXIAO", MODE="0666"
EOF

# Regeln neu laden
sudo udevadm control --reload-rules
sudo udevadm trigger

# Prüfung: XIAO einstecken
ls -la /dev/ttyXIAO
# lrwxrwxrwx 1 root root 7 ... /dev/ttyXIAO -> ttyACM0
```

Im Docker-Compose oder Docker-Run kann dann `/dev/ttyXIAO` als stabiler Gerätepfad verwendet werden.

---

## 6 Seeed XIAO ESP32-S3 – micro-ROS Client

### 6.1 Entwicklungsumgebung

Für die Firmware-Entwicklung auf dem XIAO ESP32-S3 stehen drei Toolchains zur Verfügung:

| Toolchain               | micro-ROS-Bibliothek         | Empfehlung                                    |
|-------------------------|------------------------------|-----------------------------------------------|
| **PlatformIO** (VSCode) | `micro_ros_platformio`       | **Empfohlen** – einfachste Integration        |
| Arduino IDE             | `micro_ros_arduino`          | Einsteigerfreundlich, begrenzte Konfiguration |
| ESP-IDF v5.x            | `micro_ros_espidf_component` | Maximale Kontrolle, FreeRTOS nativ            |

### 6.2 PlatformIO-Projekt (empfohlen)

**Projektstruktur:**

```
xiao-esp32s3-microros/
├── platformio.ini
├── src/
│   └── main.cpp
└── include/
    └── config.h
```

**`platformio.ini`:**

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
framework = arduino
monitor_speed = 115200

; micro-ROS für Humble
lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio

; micro-ROS Konfiguration
board_microros_distro = humble
board_microros_transport = serial

; ESP32-S3 spezifisch
board_build.mcu = esp32s3
board_build.f_cpu = 240000000L
board_build.arduino.memory_type = qio_opi
build_flags =
    -DBOARD_HAS_PSRAM
    -DARDUINO_USB_CDC_ON_BOOT=1
    -DARDUINO_USB_MODE=1
```

> **Hinweis zur ESP32-S3 micro-ROS-Bibliothek:** Die vorkompilierte Bibliothek enthält möglicherweise nur das `esp32`-Verzeichnis. Für den ESP32-S3 muss das Verzeichnis kopiert werden: `cp -r esp32 esp32s3` im Bibliotheks-Ordner `src/`.

### 6.3 micro-ROS Client – Serial-Transport (Minimal-Beispiel)

```cpp
// Datei: src/main.cpp
// micro-ROS Publisher über USB-Serial (XIAO ESP32-S3)

#include <Arduino.h>
#include <micro_ros_platformio.h>

#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/int32.h>

// --- micro-ROS Objekte ---
rcl_publisher_t publisher;
std_msgs__msg__Int32 msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

// --- Fehlermakros ---
#define RCCHECK(fn)  { rcl_ret_t rc = (fn); \
    if (rc != RCL_RET_OK) { error_loop(); } }
#define RCSOFTCHECK(fn) { rcl_ret_t rc = (fn); \
    if (rc != RCL_RET_OK) { /* Soft-Fehler, fortfahren */ } }

void error_loop() {
    while (1) {
        // Fehler-LED blinken (On-Board LED = GPIO21)
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        delay(100);
    }
}

void timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
    RCLC_UNUSED(last_call_time);
    if (timer != NULL) {
        RCSOFTCHECK(rcl_publish(&publisher, &msg, NULL));
        msg.data++;
    }
}

void setup() {
    // LED als Statusanzeige
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    // Serial für micro-ROS Transport
    Serial.begin(115200);
    set_microros_serial_transports(Serial);
    delay(2000);

    // Allocator und Support initialisieren
    allocator = rcl_get_default_allocator();
    RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));

    // Node erstellen
    RCCHECK(rclc_node_init_default(
        &node, "xiao_esp32s3_node", "", &support));

    // Publisher erstellen (Topic: /mcu/heartbeat)
    RCCHECK(rclc_publisher_init_default(
        &publisher, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "mcu/heartbeat"));

    // Timer: 100 ms Intervall (10 Hz)
    const unsigned int timer_period_ms = 100;
    RCCHECK(rclc_timer_init_default(
        &timer, &support,
        RCL_MS_TO_NS(timer_period_ms),
        timer_callback));

    // Executor mit 1 Timer-Handle
    RCCHECK(rclc_executor_init(
        &executor, &support.context, 1, &allocator));
    RCCHECK(rclc_executor_add_timer(&executor, &timer));

    // Initialisierung erfolgreich → LED aus
    msg.data = 0;
    digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
    // Executor verarbeitet Callbacks
    RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10)));
}
```

### 6.4 micro-ROS Client – WiFi-UDP-Transport

```cpp
// Datei: src/main.cpp (WiFi-Variante)
// Nur setup()-Änderung gegenüber Serial-Variante

#include <Arduino.h>
#include <micro_ros_platformio.h>
#include <WiFi.h>

// WiFi- und Agent-Konfiguration
#define WIFI_SSID     "AMR-Network"
#define WIFI_PASS     "sicheresPasswort"
#define AGENT_IP      "192.168.1.100"   // IP des Raspberry Pi 5
#define AGENT_PORT    8888

// ... (gleiche Includes und Variablen wie Serial-Variante)

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(115200);

    // WiFi-UDP Transport konfigurieren
    IPAddress agent_ip;
    agent_ip.fromString(AGENT_IP);
    set_microros_wifi_transports(
        WIFI_SSID, WIFI_PASS,
        agent_ip, AGENT_PORT);

    delay(2000);

    // ... (Rest identisch: Allocator, Node, Publisher, Timer, Executor)
}
```

### 6.5 Erweitert: Publisher + Subscriber (Bidirektional)

```cpp
// Bidirektionale Kommunikation: Publisher (Encoder) + Subscriber (Motor-PWM)

#include <Arduino.h>
#include <micro_ros_platformio.h>

#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/int32.h>
#include <geometry_msgs/msg/twist.h>

// --- Hardware-Pins ---
#define PIN_MOTOR_L   1   // D0 = GPIO1
#define PIN_MOTOR_R   2   // D1 = GPIO2
#define PIN_ENC_A     3   // D2 = GPIO3
#define PIN_ENC_B     4   // D3 = GPIO4

// --- micro-ROS Objekte ---
rcl_publisher_t encoder_pub;
rcl_subscription_t cmd_vel_sub;
std_msgs__msg__Int32 encoder_msg;
geometry_msgs__msg__Twist cmd_vel_msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

// --- Encoder-Zähler (Interrupt-sicher) ---
volatile int32_t encoder_ticks = 0;

void IRAM_ATTR encoder_isr() {
    if (digitalRead(PIN_ENC_B)) {
        encoder_ticks++;
    } else {
        encoder_ticks--;
    }
}

// --- Callbacks ---
void timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
    RCLC_UNUSED(last_call_time);
    if (timer != NULL) {
        encoder_msg.data = encoder_ticks;
        rcl_publish(&encoder_pub, &encoder_msg, NULL);
    }
}

void cmd_vel_callback(const void *msg_in) {
    const geometry_msgs__msg__Twist *twist =
        (const geometry_msgs__msg__Twist *)msg_in;

    float linear  = twist->linear.x;   // m/s
    float angular = twist->angular.z;   // rad/s

    // Differentialantrieb: Geschwindigkeit → PWM
    int pwm_left  = constrain((int)((linear - angular) * 255), -255, 255);
    int pwm_right = constrain((int)((linear + angular) * 255), -255, 255);

    // PWM an Motortreiber ausgeben
    analogWrite(PIN_MOTOR_L, abs(pwm_left));
    analogWrite(PIN_MOTOR_R, abs(pwm_right));
}

void setup() {
    // Hardware
    pinMode(PIN_MOTOR_L, OUTPUT);
    pinMode(PIN_MOTOR_R, OUTPUT);
    pinMode(PIN_ENC_A, INPUT_PULLUP);
    pinMode(PIN_ENC_B, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_ENC_A), encoder_isr, RISING);

    // micro-ROS Serial Transport
    Serial.begin(115200);
    set_microros_serial_transports(Serial);
    delay(2000);

    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);

    rclc_node_init_default(&node, "xiao_motor_node", "", &support);

    // Publisher: Encoder-Ticks (50 Hz)
    rclc_publisher_init_default(&encoder_pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "mcu/encoder_ticks");

    // Subscriber: cmd_vel (Geschwindigkeitsbefehle)
    rclc_subscription_init_default(&cmd_vel_sub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
        "cmd_vel");

    // Timer: 20 ms (50 Hz Encoder-Publish)
    rclc_timer_init_default(&timer, &support,
        RCL_MS_TO_NS(20), timer_callback);

    // Executor: 1 Timer + 1 Subscriber
    rclc_executor_init(&executor, &support.context, 2, &allocator);
    rclc_executor_add_timer(&executor, &timer);
    rclc_executor_add_subscription(
        &executor, &cmd_vel_sub, &cmd_vel_msg,
        &cmd_vel_callback, ON_NEW_DATA);
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
}
```

### 6.6 Firmware flashen

```bash
# PlatformIO (Terminal oder VSCode)
cd xiao-esp32s3-microros/

# Kompilieren
pio run

# Flashen (XIAO über USB-C verbunden)
pio run --target upload

# Serial Monitor (zum Debuggen)
pio device monitor --baud 115200
```

> **Boot-Modus:** Falls der XIAO ESP32-S3 nicht erkannt wird, Boot-Taste gedrückt halten → Reset-Taste drücken und loslassen → Boot-Taste loslassen. Das Gerät befindet sich dann im Download-Modus.

---

## 7 Systemtest und Verifikation

### 7.1 Schritt-für-Schritt-Test

```bash
# 1. XIAO ESP32-S3 mit geflashter Firmware über USB-C an Pi 5 anschließen
#    Prüfen:
ls -la /dev/ttyACM0    # oder /dev/ttyXIAO (mit udev-Regel)

# 2. micro-ROS Agent starten (in Terminal 1)
docker run -it --rm \
    -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:humble \
    serial --dev /dev/ttyACM0 -b 115200 -v6

# Erwartete Ausgabe nach ESP32-S3 Reset:
# [info] | TermiosAgentLinux.cpp | init     | running...
# [info] | Root.cpp             | create_client | session established
# [info] | SessionManager.hpp   | establish_session | session established

# 3. ROS 2 Container starten (in Terminal 2)
docker run -it --rm --net=host ros:humble-ros-base bash
source /opt/ros/humble/setup.bash

# 4. Topics auflisten
ros2 topic list
# /mcu/heartbeat
# /mcu/encoder_ticks
# /parameter_events
# /rosout

# 5. Nachrichten empfangen
ros2 topic echo /mcu/heartbeat
# data: 42
# ---
# data: 43
# ---

# 6. Nachrichten senden (cmd_vel)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

### 7.2 Diagnose-Befehle

```bash
# Topic-Frequenz messen
ros2 topic hz /mcu/encoder_ticks
# average rate: 50.012
# min: 0.019s max: 0.021s

# Topic-Bandbreite
ros2 topic bw /mcu/encoder_ticks

# Node-Informationen
ros2 node list
# /xiao_motor_node

ros2 node info /xiao_motor_node
# Publishers:
#   /mcu/encoder_ticks: std_msgs/msg/Int32
# Subscribers:
#   /cmd_vel: geometry_msgs/msg/Twist

# Gesamten ROS-2-Graphen visualisieren
ros2 run rqt_graph rqt_graph
```

---

## 8 Erweiterte Konfiguration

### 8.1 DDS-Domäne und Quality of Service (QoS)

```bash
# Alle Container und Nodes müssen die gleiche Domain-ID verwenden
export ROS_DOMAIN_ID=0

# In docker-compose.yml:
environment:
    - ROS_DOMAIN_ID=0
    - RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Für die micro-ROS-Client-Seite kann die QoS über `rclc_publisher_init_best_effort` (statt `_default`) angepasst werden. Best-Effort eignet sich für hochfrequente Sensor-Daten (Encoder, IMU), Reliable für sicherheitskritische Befehle (Motor-Stopp).

### 8.2 Mehrere XIAO ESP32-S3 betreiben

Jeder micro-ROS Client benötigt einen eigenen Agent-Kanal. Bei mehreren MCUs über USB-Serial müssen die Gerätenamen unterscheidbar sein:

```bash
# udev-Regeln mit Serial-Nummer differenzieren
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{serial}=="ABC123", \
    SYMLINK+="ttyXIAO_MOTOR"
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{serial}=="DEF456", \
    SYMLINK+="ttyXIAO_SENSOR"

# Zwei Agent-Instanzen starten
docker run -d --rm --privileged -v /dev:/dev --net=host \
    microros/micro-ros-agent:humble serial --dev /dev/ttyXIAO_MOTOR -v4

docker run -d --rm --privileged -v /dev:/dev --net=host \
    microros/micro-ros-agent:humble serial --dev /dev/ttyXIAO_SENSOR -v4
```

### 8.3 Autostart (systemd-Service)

```bash
# Datei: /etc/systemd/system/microros-agent.service
sudo tee /etc/systemd/system/microros-agent.service << 'EOF'
[Unit]
Description=micro-ROS Agent (Serial)
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=5
ExecStartPre=-/usr/bin/docker rm -f microros_agent
ExecStart=/usr/bin/docker run --rm \
    --name microros_agent \
    --privileged \
    -v /dev:/dev \
    --net=host \
    microros/micro-ros-agent:humble \
    serial --dev /dev/ttyXIAO -b 115200 -v4
ExecStop=/usr/bin/docker stop microros_agent

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable microros-agent
sudo systemctl start microros-agent
sudo systemctl status microros-agent
```

---

## 10 Zusammenfassung der Schlüsselparameter

```
┌──────────────────────────────────────────────────────────────────────────┐
│   AMR-System: RPi 5 + ROS 2 Humble + XIAO ESP32-S3 – Kurzprofil       │
├──────────────────────────────┬───────────────────────────────────────────┤
│                              │                                           │
│   HOST (Raspberry Pi 5)      │                                           │
│   SoC                        │ BCM2712, 4× Cortex-A76 @ 2,4 GHz        │
│   RAM                        │ 8 GB LPDDR4X                             │
│   OS                         │ Raspberry Pi OS Trixie (Debian 13)       │
│   Kernel                     │ Linux 6.12 LTS (aarch64)                 │
│   ROS 2                      │ Humble Hawksbill (Docker, Ubuntu 22.04)  │
│   DDS-Middleware              │ Fast-DDS (rmw_fastrtps_cpp)              │
│   Docker-Image               │ ros:humble-ros-base (~800 MB, arm64)     │
│   Stromversorgung            │ 5 V / 5 A (USB-C oder DC/DC + config)   │
│                              │                                           │
│   MCU (XIAO ESP32-S3)       │                                           │
│   SoC                        │ ESP32-S3R8, 2× Xtensa LX7 @ 240 MHz    │
│   Speicher                   │ 512 KB SRAM + 8 MB PSRAM + 8 MB Flash   │
│   Funk                       │ WiFi 802.11 b/g/n + BLE 5.0             │
│   USB                        │ USB 2.0 OTG (nativ, CDC-ACM)            │
│   GPIO                       │ 11 Pins (ADC, PWM, I²C, SPI, UART)     │
│   Firmware                   │ micro-ROS + FreeRTOS (PlatformIO)       │
│   Abmessungen                │ 21 × 17,5 mm, ~3 g                      │
│   Stromverbrauch             │ ~100 mA aktiv, 14 µA Deep Sleep         │
│                              │                                           │
│   KOMMUNIKATION              │                                           │
│   Primär                     │ USB-Serial (CDC-ACM, 115200 Baud)       │
│   Sekundär                   │ WiFi-UDP (Port 8888)                    │
│   Protokoll                  │ Micro XRCE-DDS (über micro-ROS Agent)   │
│   Agent-Image                │ microros/micro-ros-agent:humble          │
│   Latenz (Serial)            │ < 1 ms                                   │
│   Latenz (WiFi-UDP)          │ 2 … 20 ms                               │
│                              │                                           │
│   TOOLCHAIN                  │                                           │
│   ESP32-S3 Entwicklung       │ PlatformIO + Arduino-Framework           │
│   micro-ROS Distro           │ Humble                                   │
│   ESP-IDF (Basis)            │ v5.x (via PlatformIO espressif32)       │
│   ROS-2-Build                │ colcon (im Docker-Container)            │
│   Versionskontrolle          │ Git (ju1-eu/amr-platform)               │
└──────────────────────────────┴───────────────────────────────────────────┘
```

---

## 11 Ressourcen

| Typ                                    | Link                                                                                                                                                                           |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ROS 2 Humble Dokumentation             | [docs.ros.org/en/humble](https://docs.ros.org/en/humble/)                                                                                                                      |
| ROS 2 auf Raspberry Pi (offiziell)     | [docs.ros.org/…/Installing-on-Raspberry-Pi](https://docs.ros.org/en/humble/How-To-Guides/Installing-on-Raspberry-Pi.html)                                                      |
| micro-ROS Projekt                      | [micro.ros.org](https://micro.ros.org/)                                                                                                                                        |
| micro-ROS Agent (Docker)               | [hub.docker.com/r/microros/micro-ros-agent](https://hub.docker.com/r/microros/micro-ros-agent)                                                                                 |
| micro_ros_espidf_component (GitHub)    | [github.com/micro-ROS/micro_ros_espidf_component](https://github.com/micro-ROS/micro_ros_espidf_component)                                                                     |
| micro_ros_platformio (GitHub)          | [github.com/micro-ROS/micro_ros_platformio](https://github.com/micro-ROS/micro_ros_platformio)                                                                                 |
| micro_ros_arduino (GitHub)             | [github.com/micro-ROS/micro_ros_arduino](https://github.com/micro-ROS/micro_ros_arduino)                                                                                       |
| Seeed XIAO ESP32S3 Wiki                | [wiki.seeedstudio.com/xiao_esp32s3_getting_started](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)                                                                |
| Seeed XIAO ESP32S3 Schaltplan          | [Seeed Studio Files](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/)                                                                                         |
| ESP32-S3 Datasheet (Espressif)         | [espressif.com/…/esp32-s3_datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)                                                    |
| PlatformIO ESP32-S3 Board              | [docs.platformio.org/…/seeed_xiao_esp32s3](https://docs.platformio.org/en/latest/boards/espressif32/seeed_xiao_esp32s3.html)                                                   |
| Raspberry Pi OS Trixie                 | [raspberrypi.com/news/trixie](https://www.raspberrypi.com/news/trixie-the-new-version-of-raspberry-pi-os/)                                                                     |
| Docker ROS Images (OSRF)               | [hub.docker.com/_/ros](https://hub.docker.com/_/ros)                                                                                                                           |
| ROS 2 Humble + Pi 5 + ESP32 (Tutorial) | [Medium – Antonio Consiglio](https://medium.com/@antonioconsiglio/how-to-install-ros2-humble-on-raspberry-pi-5-and-enable-communication-with-esp32-via-micro-ros-2d30dfcf2111) |
| ESP32 micro-ROS WiFi/UDP (Tutorial)    | [RoboFoundry (Medium)](https://robofoundry.medium.com/esp32-micro-ros-actually-working-over-wifi-and-udp-transport-519a8ad52f65)                                               |
| micro-ROS on ESP32 Tutorial            | [Technologie Hub Wien](https://technologiehub.at/project-posts/micro-ros-on-esp32-tutorial/)                                                                                   |
| Pi 5 Stromversorgung (Guide)           | [bret.dk/how-to-power-the-raspberry-pi-5](https://bret.dk/how-to-power-the-raspberry-pi-5-a-complete-guide/)                                                                   |

---

*Dokumentversion: 1.0 | Datum: 2026-02-24 | Quellen: ROS 2 Humble Dokumentation, micro-ROS Projekt, Seeed Studio Wiki, Raspberry Pi OS Trixie Release Notes, Espressif ESP32-S3 Datasheet, Raspberry Pi Forums, Community-Tutorials (Medium, Technologie Hub Wien, Hackster.io)*
