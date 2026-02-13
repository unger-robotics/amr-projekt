# Aktueller Stand

```bash
# rsync mac -> pi5
rsync -avz --delete --exclude='__pycache__/' --exclude='*.pyc' --exclude='.git/' /Users/jan/daten/IoT/projekt_beamer/AMR-Bachelorarbeit/amr/ pi@rover:~/amr




# pi5
pi@rover:~ $ ls
amr  embedded_projekt  selection-panel
pi@rover:~ $ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/mmcblk0p2  117G   16G   97G  15% /
pi@rover:~ $ ls
amr  embedded_projekt  selection-panel
pi@rover:~ $ cd amr/scripts/
pi@rover:~/amr/scripts $ python3 pre_flight_check.py

************************************************************
  AMR Pre-Flight Checkliste
  XIAO ESP32-S3 + Cytron MDD3A + JGA25-370
  Zeitpunkt: 2026-02-13 16:08:56
************************************************************

  Dieses Skript fuehrt durch alle Pruefschritte vor der
  Inbetriebnahme des AMR-Roboters. Fuer jede Pruefung
  wird eine interaktive Bestaetigung abgefragt.
  Antworten: j=ja, n=nein, s=ueberspringen


============================================================
  1. USB-Enumeration
============================================================
  Gefundene USB-CDC-Geraete: /dev/ttyACM0
  [PASS] USB-CDC Enumeration

============================================================
  2. Spannungsversorgung
============================================================
  Bitte mit Multimeter messen und Werte eingeben.

  --- 4S LiFePO4 Akku ---
  Soll-Bereich: 12.8 - 14.6 V
  Messpunkt: Messung am Akku-Connector
  Gemessene Spannung fuer '4S LiFePO4 Akku' [V] (Enter=uebersprungen): s
  Liegt s V im Soll-Bereich 12.8 - 14.6 V? [j/n/s(kip)]: s
  [SKIP] 4S LiFePO4 Akku

  --- Buck FZJ5V5A1S-C ---
  Soll-Bereich: 5.0 - 5.2 V
  Messpunkt: Ausgang Buck-Converter, RPi5-Versorgung
  Gemessene Spannung fuer 'Buck FZJ5V5A1S-C' [V] (Enter=uebersprungen): s
  Liegt s V im Soll-Bereich 5.0 - 5.2 V? [j/n/s(kip)]: s
  [SKIP] Buck FZJ5V5A1S-C

  --- MDD3A VM ---
  Soll-Bereich: 12.8 - 14.6 V
  Messpunkt: Direkt vom Akku, Motortreiber-Eingang
  Gemessene Spannung fuer 'MDD3A VM' [V] (Enter=uebersprungen): s
  Liegt s V im Soll-Bereich 12.8 - 14.6 V? [j/n/s(kip)]: s
  [SKIP] MDD3A VM

  --- ESP32-S3 3.3V Rail ---
  Soll-Bereich: 3.2 - 3.4 V
  Messpunkt: Onboard LDO, Logik-Versorgung
  Gemessene Spannung fuer 'ESP32-S3 3.3V Rail' [V] (Enter=uebersprungen): s
  Liegt s V im Soll-Bereich 3.2 - 3.4 V? [j/n/s(kip)]: s
  [SKIP] ESP32-S3 3.3V Rail


============================================================
  3. Pin-Belegung (gegen config.h)
============================================================
  Bitte physische Verdrahtung mit Soll-Belegung vergleichen.

  PIN_MOTOR_LEFT_A: D0 (GPIO1) -> MDD3A M1A (Vorwaerts-PWM)
  PIN_MOTOR_LEFT_B: D1 (GPIO2) -> MDD3A M1B (Rueckwaerts-PWM)
  PIN_MOTOR_RIGHT_A: D2 (GPIO3) -> MDD3A M2A (Vorwaerts-PWM)
  PIN_MOTOR_RIGHT_B: D3 (GPIO4) -> MDD3A M2B (Rueckwaerts-PWM)
  PIN_ENC_LEFT_A: D6 (GPIO43) -> Encoder Links (Hall, Interrupt)
  PIN_ENC_RIGHT_A: D7 (GPIO44) -> Encoder Rechts (Hall, Interrupt)
  PIN_LED_MOSFET: D10 (GPIO9) -> IRLZ24N Low-Side MOSFET
  PIN_I2C_SDA: D4 (GPIO5) -> I2C SDA (MPU6050, optional)
  PIN_I2C_SCL: D5 (GPIO6) -> I2C SCL (MPU6050, optional)

  Stimmt die physische Verdrahtung mit der Tabelle ueberein? [j/n/s(kip)]: s
  [SKIP] Pin-Belegung gesamt

============================================================
  4. Firmware
============================================================
  Pruefung ob Firmware hochgeladen und gestartet ist.

  4a) Firmware-Upload
  Kommando: cd technische_umsetzung/esp32_amr_firmware/ && pio run -t upload
  Wurde die Firmware erfolgreich hochgeladen (SUCCESS)? [j/n/s(kip)]: j
  [PASS] Firmware-Upload

  4b) Serial Monitor Boot-Meldung
  Kommando: pio run -t monitor (115200 Baud)
  Erwartete Ausgabe: micro-ROS Initialisierung, PID-Start
  Zeigt der Serial Monitor eine korrekte Boot-Meldung? [j/n/s(kip)]: j
  [PASS] Boot-Meldung

============================================================
  5. micro-ROS Verbindung (optional)
============================================================
  Nur pruefbar, wenn micro-ROS Agent auf RPi5 laeuft.
  Kommando: ros2 topic list

  micro-ROS Agent laeuft und soll geprueft werden? [j/n/s(kip)]: n
  [SKIP] micro-ROS (uebersprungen)

============================================================
  6. Sensoren
============================================================
  6a) RPLIDAR A1
  Kein /dev/ttyUSB* gefunden (RPLIDAR nicht angeschlossen?)
  RPLIDAR A1 angeschlossen und sichtbar? [j/n/s(kip)]: n
  [FAIL] RPLIDAR A1

  6b) Raspberry Pi Global Shutter Camera (CSI)
  Gefundene Video-Geraete: /dev/video19, /dev/video20, /dev/video21, /dev/video22, /dev/video23, /dev/video24, /dev/video25, /dev/video26, /dev/video27, /dev/video28, /dev/video29, /dev/video30, /dev/video31, /dev/video32, /dev/video33, /dev/video34, /dev/video35
  Kamera angeschlossen und erkannt? [j/n/s(kip)]: n
  [FAIL] Kamera (CSI)

============================================================
  ZUSAMMENFASSUNG
============================================================
  Gesamt:          11 Pruefpunkte
  Bestanden:       3
  Fehlgeschlagen:  2
  Uebersprungen:   6

  >>> ERGEBNIS: FAIL - Probleme muessen behoben werden <<<

  Protokoll gespeichert: /home/pi/amr/scripts/pre_flight_20260213_161057.md

pi@rover:~/amr/scripts $ cd
pi@rover:~ $ sudo apt update && sudo apt install -y curl gnupg lsb-release
Hit:1 http://deb.debian.org/debian trixie InRelease
Get:2 http://deb.debian.org/debian trixie-updates InRelease [47.3 kB]
Get:3 http://archive.raspberrypi.com/debian trixie InRelease [54.8 kB]
Get:4 http://deb.debian.org/debian-security trixie-security InRelease [43.4 kB]
Get:5 https://download.docker.com/linux/debian trixie InRelease [32.5 kB]
Get:6 http://deb.debian.org/debian-security trixie-security/main armhf Packages [102 kB]
Get:7 https://download.docker.com/linux/debian trixie/stable arm64 Packages [26.2 kB]
Get:8 http://archive.raspberrypi.com/debian trixie/main arm64 Packages [377 kB]
Get:9 http://deb.debian.org/debian-security trixie-security/main arm64 Packages [108 kB]
Get:10 http://deb.debian.org/debian-security trixie-security/main Translation-en [69.9 kB]
Get:11 http://archive.raspberrypi.com/debian trixie/main armhf Packages [373 kB]
Fetched 1,235 kB in 1s (2,113 kB/s)
91 packages can be upgraded. Run 'apt list --upgradable' to see them.
curl is already the newest version (8.14.1-2+deb13u2).
lsb-release is already the newest version (12.1-1).
lsb-release set to manually installed.
Upgrading:
  dirmngr  gnupg  gnupg-l10n  gnupg-utils  gpg  gpg-agent  gpg-wks-client  gpgconf  gpgsm  gpgv

Summary:
  Upgrading: 10, Installing: 0, Removing: 0, Not Upgrading: 81
  Download size: 3,230 kB
  Space needed: 0 B / 103 GB available

Get:1 http://deb.debian.org/debian trixie/main arm64 gpgsm arm64 2.4.7-21+deb13u1+b1 [252 kB]
Get:2 http://deb.debian.org/debian trixie/main arm64 gnupg-utils arm64 2.4.7-21+deb13u1+b1 [182 kB]
Get:3 http://deb.debian.org/debian trixie/main arm64 gpg-wks-client arm64 2.4.7-21+deb13u1+b1 [102 kB]
Get:4 http://deb.debian.org/debian trixie/main arm64 gpg arm64 2.4.7-21+deb13u1+b1 [579 kB]
Get:5 http://deb.debian.org/debian trixie/main arm64 dirmngr arm64 2.4.7-21+deb13u1+b1 [359 kB]
Get:6 http://deb.debian.org/debian trixie/main arm64 gnupg all 2.4.7-21+deb13u1 [417 kB]
Get:7 http://deb.debian.org/debian trixie/main arm64 gpgconf arm64 2.4.7-21+deb13u1+b1 [122 kB]
Get:8 http://deb.debian.org/debian trixie/main arm64 gpg-agent arm64 2.4.7-21+deb13u1+b1 [249 kB]
Get:9 http://deb.debian.org/debian trixie/main arm64 gnupg-l10n all 2.4.7-21+deb13u1 [749 kB]
Get:10 http://deb.debian.org/debian trixie/main arm64 gpgv arm64 2.4.7-21+deb13u1+b1 [221 kB]
Fetched 3,230 kB in 1s (2,600 kB/s)
apt-listchanges: Reading changelogs...
(Reading database ... 111808 files and directories currently installed.)
Preparing to unpack .../0-gpgsm_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gpgsm (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../1-gnupg-utils_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gnupg-utils (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../2-gpg-wks-client_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gpg-wks-client (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../3-gpg_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gpg (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../4-dirmngr_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking dirmngr (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../5-gnupg_2.4.7-21+deb13u1_all.deb ...
Unpacking gnupg (2.4.7-21+deb13u1) over (2.4.7-21) ...
Preparing to unpack .../6-gpgconf_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gpgconf (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../7-gpg-agent_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gpg-agent (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Preparing to unpack .../8-gnupg-l10n_2.4.7-21+deb13u1_all.deb ...
Unpacking gnupg-l10n (2.4.7-21+deb13u1) over (2.4.7-21) ...
Preparing to unpack .../9-gpgv_2.4.7-21+deb13u1+b1_arm64.deb ...
Unpacking gpgv (2.4.7-21+deb13u1+b1) over (2.4.7-21+b3) ...
Setting up gnupg-l10n (2.4.7-21+deb13u1) ...
Setting up gpgv (2.4.7-21+deb13u1+b1) ...
Setting up gpgconf (2.4.7-21+deb13u1+b1) ...
Setting up gpg (2.4.7-21+deb13u1+b1) ...
Setting up gnupg-utils (2.4.7-21+deb13u1+b1) ...
Setting up gpg-agent (2.4.7-21+deb13u1+b1) ...
Setting up gpgsm (2.4.7-21+deb13u1+b1) ...
Setting up dirmngr (2.4.7-21+deb13u1+b1) ...
Setting up gnupg (2.4.7-21+deb13u1) ...
Setting up gpg-wks-client (2.4.7-21+deb13u1+b1) ...
Processing triggers for man-db (2.13.1-1) ...
pi@rover:~ $ sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
pi@rover:~ $ echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
pi@rover:~ $ sudo apt update
Error: Malformed entry 1 in list file /etc/apt/sources.list.d/ros2.list (Component)
Error: The list of sources could not be read.
pi@rover:~ $ sudo rm /etc/apt/sources.list.d/ros2.list
pi@rover:~ $ sudo apt update
Hit:1 http://deb.debian.org/debian trixie InRelease
Hit:2 http://archive.raspberrypi.com/debian trixie InRelease
Hit:3 http://deb.debian.org/debian trixie-updates InRelease
Hit:4 http://deb.debian.org/debian-security trixie-security InRelease
Hit:5 https://download.docker.com/linux/debian trixie InRelease
81 packages can be upgraded. Run 'apt list --upgradable' to see them.
pi@rover:~ $ sudo apt install -y ros-humble-desktop
Error: Unable to locate package ros-humble-desktop
pi@rover:~ $ ls
amr  embedded_projekt  selection-panel
pi@rover:~ $ cd amr/
pi@rover:~/amr $ vim Dockerfile
pi@rover:~/amr $ vim Dockerfile
pi@rover:~/amr $ docker build -t amr-ros2-env .
[+] Building 144.3s (3/8)                                                                                                                          docker:default
 => [internal] load build definition from Dockerfile                                                                                                         0.1s
 => => transferring dockerfile: 980B                                                                                                                         0.0s
 => [internal] load metadata for docker.io/osrf/ros:humble-desktop                                                                                           2.6s
 => [internal] load .dockerignore                                                                                                                            0.1s
 => => transferring context: 2B                                                                                                                              0.0s
 => [1/5] FROM docker.io/osrf/ros:humble-desktop@sha256:6dfbf5213dc893c1f8ea6d573102e9ea2dfa1bdbf2f13dcb26bcca2c730e9908                                   141.5s
 => => resolve docker.io/osrf/ros:humble-desktop@sha256:6dfbf5213dc893c1f8ea6d573102e9ea2dfa1bdbf2f13dcb26bcca2c730e9908                                     0.0s
 => => sha256:3c1550f451c47aecc9feaebbcb8667811862a6790dbd0d71fd3a1a5549a3810c 190.84MB / 810.98MB                                                         141.0s
 => => sha256:d89d0b0792ec60ed6744e3a288f76caa6009884e44c6cd98add8055465bd325c 23.32MB / 23.32MB                                                            33.8s
 => => sha256:f3c9c540e89d0a29bced540968ac923c8677aab6a43d85b536f173a4e668d7a7 2.53kB / 2.53kB                                                               0.9s
 => => sha256:d7e9ae4043d817eb2f5f8b33584b61dd9859d8733be7d8c069ae9efe648e3d28 383.08kB / 383.08kB                                                           1.6s
 => => sha256:58aaf05f7e4717206bdef277969fefae295f0aeb84ad86377ce147c6e467ce29 97.96MB / 97.96MB                                                           104.5s
 => => sha256:72dabda1f44ba2f0c461142f451ba75451f7348aa265fbe6a04dd0ff2654448d 195B / 195B                                                                   0.5s
 => => sha256:5a1e1824e50f15537f4e31add7722621bc890f927e27f1505e54da0b51bc4c1b 104.70MB / 104.70MB                                                         10[+] Building 144.4s (3/8)                                                                                                                      docker:default
 => [internal] load build definition from Dockerfile                                                                                                     0.1s => => transferring dockerfile: 980B                                                                                                                     0.0s
 => [internal] load metadata for docker.io/osrf/ros:humble-desktop                                                                                       2.6s => [internal] load .dockerignore                                                                                                                        0.1s
 => => transferring context: 2B                                                                                                                          0.0s => [1/5] FROM docker.io/osrf/ros:humble-desktop@sha256:6dfbf5213dc893c1f8ea6d573102e9ea2dfa1bdbf2f13dcb26bcca2c730e9908                               141.7s
 => => resolve docker.io/osrf/ros:humble-desktop@sha256:6dfbf5213dc893c1f8ea6d573102e9ea2dfa1bdbf2f13dcb26bcca2c730e9908                                 0.0s => => sha256:3c1550f451c47aecc9feaebbcb8667811862a6790dbd0d71fd3a1a5549a3810c 190.84MB / 810.98MB                                                     141.2s
 => => sha256:d89d0b0792ec60ed6744e3a288f76caa6009884e44c6cd98add8055465bd325c 23.32MB / 23.32MB                                                        33.8[+] Building 215.8s (3/8)                                                                                                                    docker:default. => [internal] load build definition from Dockerfile                                                                                                   0.1s
 => => transferring dockerfile: 980B                                                                                                                   0.0s6 => [internal] load metadata for docker.io/osrf/ros:humble-desktop                                                                                     2.6s. => [internal] load .dockerignore                                                                                                                      0.1s
 => => transferring context: 2B                                                                                                                        0.0s5 => [1/5] FROM docker.io/osrf/ros:humble-desktop@sha256:6dfbf5213dc893c1f8ea6d573102e9ea2dfa1bdbf2f13dcb26bcca2c730e9908                             213.1s. => => resolve docker.io/osrf/ros:humble-desktop@sha256:6dfbf5213dc893c1f8ea6d573102e9ea2dfa1bdbf2f13dcb26bcca2c730e9908                               0.0s
 => => sha256:3c1550f451c47aecc9feaebbcb8667811862a6790dbd0d71fd3a1a5549a3810c 419.43MB / 810.98MB                                                   212.6s6 => => sha256:d89d0b0792ec60ed6744e3a288f76caa6009884e44c6cd98add8055465bd325c 23.32MB / 23.32MB                                                      33.8s. => => sha256:f3c9c540e89d0a29bced540968ac923c8677aab6a43d85b536f173a4e668d7a7 2.53kB / 2.53kB                                                         0.9s
 => => sha256:d7e9ae4043d817eb2f5f8b33584b61dd9859d8733be7d8c069ae9efe648e3d28 383.08kB / 383.08kB                                                     1.6s8 => => sha256:58aaf05f7e4717206bdef277969fefae295f0aeb84ad86377ce147c6e467ce29 97.96MB / 97.96MB                                                     104.5s. => => sha256:72dabda1f44ba2f0c461142f451ba75451f7348aa265fbe6a04dd0ff2654448d 195B / 195B                                                             0.5s
 => => sha256:5a1e1824e50f15537f4e31add7722621bc890f927e27f1505e54da0b51bc4c1b 104.70MB / 104.70MB                                                   108.6s7 => => sha256:ecd839ce83db999d5035a7a3825b0dfa72a58cb764b8a8ea0c500fbed89b583b 97.22kB / 97.22kB                                                       0.6s. => => sha256:5b3b6a798b5088fee7bc0bfb188bdd445113b407842d17edf502e09f2fc1b536 5.99MB / 5.99MB                                                         8.0s
 => => sha256:3f147c465ef3441f6a6fadaa4bf3dd1b68d753988b404893e8e575a24a013be1 1.21MB / 1.21MB                                                         1.8s2 => => sha256:6f4ebca3e823b18dac366f72e537b1772bc3522a5c7ae299d6491fb17378410e 29.54MB / 29.54MB                                                      36.1s. => => extracting sha256:6f4ebca3e823b18dac366f72e537b1772bc3522a5c7ae299d6491fb17378410e                                                              0.7s
 => => extracting sha256:3f147c465ef3441f6a6fadaa4bf3dd1b68d753988b404893e8e575a24a013be1                                                              0.2s7 => => extracting sha256:5b3b6a798b5088fee7bc0bfb188bdd445113b407842d17edf502e09f2fc1b536                                                              0.2s. => => extracting sha256:ecd839ce83db999d5035a7a3825b0dfa72a58cb764b8a8ea0c500fbed89b583b                                                              0.1s
 => => extracting sha256:5a1e1824e50f15537f4e31add7722621bc890f927e27f1505e54da0b51bc4c1b                                                              3.7s9 => => extracting sha256:72dabda1f44ba2f0c461142f451ba75451f7348aa265fbe6a04dd0ff2654448d                                                              0.5s. => => extracting sha256:58aaf05f7e4717206bdef277969fefae295f0aeb84ad86377ce147c6e467ce29                                                              1.9s
 => => extracting sha256:d7e9ae4043d817eb2f5f8b33584b61dd9859d8733be7d8c069ae9efe648e3d28                                                              0.7s4 => => extracting sha256:f3c9c540e89d0a29bced540968ac923c8677aab6a43d85b536f173a4e668d7a7                                                              0.4s. => => extracting sha256:d89d0b0792ec60ed6744e3a288f76caa6009884e44c6cd98add8055465bd325c                                                              1.1s
```

---


```bash
# Dockerfile
# 1. Fundament: Ubuntu 22.04 + ROS 2 Humble Desktop (inkl. RViz2)
FROM osrf/ros:humble-desktop

# 2. Pakete: Die geforderten AMR-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    ros-humble-rplidar-ros \
    ros-humble-cv-bridge \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# 3. Initialisierung: rosdep konfigurieren (wie im Dokument gefordert)
RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then rosdep init; fi \
    && rosdep update

# 4. Umgebung: Setup-Skript in der bashrc verankern
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

# 5. Startbedingung: Terminal öffnen
CMD ["/bin/bash"]
```


### Problem

Du möchtest aus dem erstellten Text-Bauplan (`Dockerfile`) das ausführbare Docker-Image für deinen AMR-Stack generieren.

### Modell und Randbedingungen

Das Werkzeug `docker build` liest das Skript im aktuellen Verzeichnis sequenziell ein. Jede Instruktion (`FROM`, `RUN`, `CMD`) erzeugt eine neue, schreibgeschützte Datenschicht (Layer) auf der SD-Karte des Raspberry Pi.

* **Zeitbedarf:** Der initiale Bauprozess dauert abhängig von der Netzwerkbandbreite **10 bis 20 Minuten**. Das System lädt zunächst das rund **3 GB** große Basis-Image herunter und installiert anschließend die über `apt` definierten ROS-Abhängigkeiten.
* **Caching-Verhalten:** Docker speichert jeden erfolgreich abgeschlossenen Layer zwischen. Bricht der Prozess aufgrund eines Netzwerkfehlers ab, setzt ein erneuter Aufruf des Befehls exakt beim letzten erfolgreichen Schritt an, anstatt alle Daten neu zu laden.

### Schluss und Anwendung

Wir weisen die Docker-Engine an, den Bauprozess zu starten. Der Parameter `-t` (Tag) vergibt einen eindeutigen Namen für das resultierende Image. Der zwingend erforderliche Punkt (`.`) am Ende des Befehls definiert das aktuelle Verzeichnis als Build-Kontext, in dem das System das `Dockerfile` sucht.

Stelle sicher, dass du dich im Verzeichnis `~/amr` befindest, und führe folgenden Befehl auf dem Raspberry Pi aus:

```bash
docker build -t amr-ros2-env .

```

### Konsequenz

Das Terminal protokolliert jeden Bau-Schritt einzeln (z. B. `Step 1/5`, `Step 2/5`). Nach erfolgreichem Abschluss der Installation meldet das System `Successfully tagged amr-ros2-env:latest`. Das Image liegt nun als statische Vorlage lokal bereit. Deine Host-Umgebung (Debian Trixie) bleibt davon physisch vollständig unberührt.

---




