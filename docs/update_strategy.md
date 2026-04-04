---
title: Update-Strategie
description: Vorgehen fuer System-, Docker- und Firmware-Updates des AMR ohne Bruch der validierten Funktionskette.
---

# AMR - Update-Strategie

**Leitfrage:** Wie laesst sich das AMR-System aktuell halten, ohne die validierte Funktionskette (ESP32-S3 → Pi5 ROS 2 → Hailo-8L) zu brechen?

## Annahmen und Randbedingungen

- Das System laeuft auf Debian 13 (trixie) — einer *Testing*-Distribution mit Rolling Updates, nicht dem stabilen Raspberry Pi OS. Das erhoeht das Risiko unerwarteter Paketaenderungen erheblich.
- ROS 2 Humble laeuft containerisiert (Docker), was es teilweise vom Host-System entkoppelt.
- Die Messwerte aus Kapitel 6 (Lateraldrift 2,1 cm, Heading Error 0,06° etc.) sind die Referenzbasis — jedes Update muss gegen diese Werte validiert werden.
- Der Kernel ist ein RPi-spezifischer Build mit Custom-Overlays (imx296, mcp2515-can0, hifiberry-dac), die bei Kernel-Updates brechen koennen.

## Risikobewertung der Komponenten

Die Abhaengigkeiten im Stack lassen sich in drei Risikokategorien einteilen:

**Hohes Risiko** (kann validierte Messwerte oder Hardwarezugriff brechen): Kernel-Updates betreffen direkt die Device-Tree-Overlays fuer CAN-Bus (mcp2515), Kamera (imx296) und Audio (hifiberry-dac). Ein neuer Kernel kann dazu fuehren, dass `/dev/can0`, die CSI-Kamera oder der HifiBerry-DAC nicht mehr erkannt werden. Ebenso kritisch ist HailoRT — Version 4.23.0 ist an den PCIe-Treiber im aktuellen Kernel gebunden. Ein Versionssprung erfordert, dass Kernel-Modul und Userspace-Library synchron bleiben. Python-Major-Updates (3.13 → 3.14) koennen OpenCV, NumPy und python3-hailort ueber ABI-Inkompatibilitaeten brechen.

**Mittleres Risiko** (kann Toolchain oder Workflow stoeren): Docker-Engine-Updates sind grundsaetzlich abwaertskompatibel, aber ein Major-Sprung kann das ROS-2-Image invalidieren. PlatformIO und die ESP32-Toolchain koennen bei Updates die `platformio.ini`-Konfiguration oder den Espressif-Framework-Build brechen. Die v4l2loopback-DKMS-Module werden bei Kernel-Updates neu kompiliert — wenn der Header-Match fehlt, faellt die Kamera-Bridge aus.

**Niedriges Risiko** (isoliert, unabhaengig vom Kernstack): Userspace-Tools wie `rpicam-apps`, Git, rsync und reine Python-Pakete innerhalb von virtualenvs.

## Strategie: Vier-Schichten-Update-Modell

Die Grundidee: Je tiefer die Schicht, desto seltener und kontrollierter wird aktualisiert.

### Schicht 1 — Kernel + Firmware (Freeze, manueller Trigger)

Kernel-Updates auf Debian trixie kommen haeufig und ungefragt. Die Empfehlung ist, den Kernel zu pinnen und nur gezielt zu aktualisieren:

```bash
# Aktuellen Kernel pinnen (apt hold) — Debian Trixie auf Pi 5
sudo apt-mark hold \
  linux-image-$(uname -r) \
  linux-image-rpi-2712 \
  linux-headers-$(uname -r) \
  linux-headers-rpi-2712 \
  linux-headers-rpi-v8 \
  linux-headers-6.12.62+rpt-rpi-v8 \
  linux-headers-6.12.62+rpt-common-rpi \
  linux-image-6.12.62+rpt-rpi-v8

# Status pruefen
apt-mark showhold

# Alte Kernel-Pakete entfernen
sudo apt autoremove
```

Ein Kernel-Update erfolgt nur, wenn ein konkreter Grund vorliegt (Sicherheitsluecke, neuer Treiber). Dann: auf einem separaten SD-Karten-Image testen, alle Overlays pruefen (`dtoverlay -l`), CAN-Bus-Frames senden/empfangen, Kamerabild verifizieren, Hailo-Inferenz laufen lassen.

Gepinnte Kernel-Pakete:

| Paket | Version |
|---|---|
| `linux-image-6.12.62+rpt-rpi-2712` | Laufender Kernel |
| `linux-image-6.12.62+rpt-rpi-v8` | v8-Variante |
| `linux-image-rpi-2712` | Meta-Paket |
| `linux-headers-*` (4 Pakete) | Passende Headers |

`apt upgrade` ueberspringt diese Pakete. Zum Entsperren bei Bedarf: `sudo apt-mark unhold <paket>`.

### Schicht 2 — Systemnahe Pakete (monatlich, selektiv)

HailoRT, v4l2loopback und Python-Systempakete bilden die zweite Schicht. Diese werden nicht per `apt upgrade` pauschal aktualisiert, sondern einzeln:

```bash
# HailoRT und v4l2loopback pinnen
sudo apt-mark hold \
  hailort \
  hailort-pcie-driver \
  python3-hailort \
  v4l2loopback-dkms

# Status pruefen
apt-mark showhold

# Gezielte Einzelupdates mit Dry-Run (vor tatsaechlichem Update)
sudo apt update
sudo apt install --dry-run python3-hailort python3-opencv

# Wenn Dry-Run OK → ohne --dry-run ausfuehren
```

Gepinnte Versionen:

| Paket | Version |
|---|---|
| `hailort` | 4.23.0 |
| `hailort-pcie-driver` | 4.23.0 |
| `python3-hailort` | 4.23.0-1 |
| `v4l2loopback-dkms` | 0.15.0-2 |

### Schicht 3 — Docker / ROS 2 (quartalsweise oder bei Bedarf)

Der ROS-2-Humble-Container ist die am besten isolierte Komponente. Updates erfolgen durch Rebuild des Docker-Images. Wichtig: Das aktuelle Image taggen, bevor ein neues gebaut wird:

```bash
# Aktuelles Image sichern
# Stand 03.04.2026: amr-ros2-humble:latest, 3.9 GB
docker tag amr-ros2-humble:latest amr-ros2-humble:backup-$(date +%Y%m%d)

# Neues Image bauen
cd ~/amr-projekt/amr/docker
docker compose build --no-cache

# Validierung
./run.sh ros2 launch my_bot full_stack.launch.py use_nav:=false
# Odometrie, SLAM, Sensoren pruefen
# Dann Nav2, Docking, Dashboard testen

# Bei Regression: Rollback
docker tag amr-ros2-humble:backup-YYYYMMDD amr-ros2-humble:latest
```

ROS 2 Humble erreicht EOL im Mai 2027 — ein Migrationspfad zu Jazzy sollte mittelfristig geplant werden, ist aber fuer die Projektarbeit nicht zeitkritisch.

### Schicht 4 — Toolchain / Entwicklungsumgebung (bei Bedarf)

PlatformIO und die ESP32-Toolchain werden nur aktualisiert, wenn ein Firmware-Feature es erfordert. Der aktuelle Stand (PlatformIO 6.1.19, espressif32 @ 6.13.0) ist stabil und fuer den ESP32-S3-Dual-Core-Build validiert.

```bash
# PlatformIO-Update (nur bewusst, nicht automatisch)
pio upgrade                     # PlatformIO Core
pio pkg update -g -p espressif32  # Platform global

# Projekt-Libraries aktualisieren (pro Projekt)
cd ~/amr-projekt/amr/mcu_firmware/drive_node && pio pkg update
cd ~/amr-projekt/amr/mcu_firmware/sensor_node && pio pkg update

# Validierung: beide Nodes kompilieren
cd ~/amr-projekt/amr/mcu_firmware/drive_node && pio run -e drive_node
cd ~/amr-projekt/amr/mcu_firmware/sensor_node && pio run -e sensor_node

# Dann flashen und gegen Kapitel-6-Referenzwerte testen
```

Nach jedem Toolchain-Update: `pio run -e drive_node && pio run -e sensor_node`, dann auf dem ESP32 flashen und gegen die Kapitel-6-Referenzwerte testen.

## Backup-Strategie (Voraussetzung fuer jedes Update)

Bevor ein Update aus Schicht 1 oder 2 durchgefuehrt wird: Dateisystem-Backup ueber Ethernet erstellen.

### Pi → Mac (Backup erstellen)

```bash
# tmux-Session starten (SSH-sicher)
sudo apt install -y tmux && tmux new -s backup

# Dateisystem-Snapshot ueber Ethernet (~25 GB, ca. 10-20 Min)
sudo rsync -avz \
  --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/swapfile","/lost+found"} \
  --exclude={"/var/cache/*","/var/tmp/*","/var/log/*"} \
  --exclude={"/home/pi/.cache/*","/home/pi/.local/share/Trash/*"} \
  --exclude={"*.img",".pio/",".venv/","__pycache__/","node_modules/",".docker/",".platformio/"} \
  --exclude={".claude.json.tmp.*",".vscode-server/",".hailo/","amr-projekt-backup.git"} \
  --exclude={"embedded_projekt/","selection-panel/"} \
  -e "ssh -i /home/pi/.ssh/id_ed25519" \
  / jan@192.168.1.210:~/amr-rootfs-$(date +%Y%m%d)/
```

tmux-Session trennen: `Ctrl+B`, dann `D`. Wieder verbinden: `tmux attach -t backup`.

### Backup pruefen (auf dem Mac)

```bash
du -sh ~/amr-rootfs-20260403/
```

### Mac → SD-Karte (Wiederherstellung)

SD-Karte aus dem Pi nehmen und in den Mac einlegen:

```bash
# 1. SD-Karte identifizieren
diskutil list
# Typisch: disk4s1 = boot (FAT32), disk4s2 = rootfs (ext4)

# 2. macOS kann kein ext4 schreiben — daher via Docker
docker run --rm -it --privileged \
  -v ~/amr-rootfs-20260403:/backup:ro \
  --pid=host \
  ubuntu bash

# 3. Im Container: Backup auf SD-Karte schreiben
apt-get update && apt-get install -y rsync
mkdir -p /mnt/rootfs
mount /dev/disk4s2 /mnt/rootfs
rsync -av --delete /backup/ /mnt/rootfs/
umount /mnt/rootfs
exit
```

**Hinweis:** `--delete` entfernt Dateien auf der SD-Karte, die nicht im Backup sind — damit wird der Zustand exakt wiederhergestellt. Device-Name (`disk4s2`) unbedingt mit `diskutil list` pruefen!

**Alternative mit Paragon extFS for Mac** (nativer ext4-Schreibzugriff):

```bash
rsync -av --delete ~/amr-rootfs-20260403/ /Volumes/rootfs/
```
