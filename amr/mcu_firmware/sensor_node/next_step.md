Skript scripts/udev_setup.sh ausarbeiten, um die USB-Enumeration des Raspberry Pi 5 für diese beiden Controller (Drive und Sensor) deterministisch zu fixieren


### Problem: Monolithische Firmware-Struktur

Die bisherige Ordnerstruktur kapselt die gesamte Mikrocontroller-Logik in einem einzigen Verzeichnis (`esp32_amr_firmware/`). Die Erweiterung um den AMR Sensor-Node (ESP32-S3 #2) erzeugt hier einen Konflikt: Beide Controller nutzen dieselbe Hardware-Architektur (Seeed XIAO ESP32-S3), erfordern aber separate C++-Routinen, unterschiedliche Loop-Frequenzen ($50\,\mathrm{Hz}$ für Antrieb vs. $10\,\mathrm{Hz}$ für Ultraschall) und kompilieren zu unterschiedlichen Binaries.

### Modell und Schlussfolgerung

Die Entwicklungsplattform PlatformIO bietet zwei Wege, diese Pluralität aufzulösen:

1. Ein einzelnes Projekt mit mehreren Build-Umgebungen (`[env:drive]`, `[env:sensor]`) in einer `platformio.ini` und Build-Filtern für die Quellcodes.
2. Ein übergeordnetes Verzeichnis mit vollständig isolierten PlatformIO-Projekten.

Wir betrachten die Abhängigkeiten: Die Integration von micro-ROS erzeugt statische Bibliotheken, die beim Kompilieren stark an die jeweilige Node-Konfiguration (Anzahl der Publisher/Subscriber, Timer) gebunden sind. Die Variante der isolierten Projekte verhindert gegenseitige Überschreibungen im `.pio`-Cache und hält externe Bibliotheken (wie Sensortreiber) strikt getrennt.

### Konsequenz 1: Verzeichnisstruktur (Monorepo)

Wir ersetzen den Ordner `esp32_amr_firmware` durch ein übergeordnetes Verzeichnis `mcu_firmware/`. Darin existieren beide Firmware-Projekte völlig autark.

```text
.
├── docker/
├── mcu_firmware/                ◄── NEU
│   ├── drive_node/              ◄── ESP32-S3 #1 (Antrieb)
│   │   ├── platformio.ini       (Bindet nur PID, Cytron, Encoder Libs ein)
│   │   ├── include/
│   │   │   └── config.h         (Beinhaltet D0-D10, 50 Hz Loop)
│   │   └── src/
│   │       └── main.cpp         (micro-ROS pub: /odom, sub: /cmd_vel)
│   └── sensor_node/             ◄── ESP32-S3 #2 (Sensoren)
│       ├── platformio.ini       (Ohne Motor-Libs, kompiliert schneller)
│       ├── include/
│       │   └── config_sensors.h (Beinhaltet D0-D2, 10/20 Hz Loop)
│       └── src/
│           └── main.cpp         (micro-ROS pub: /range/front, /cliff)
├── pi5/
└── scripts/
    ├── ...
    └── udev_setup.sh            ◄── NEU (Löst das USB-Port-Problem)

```

---

### Beobachtung: Das USB-Adressierungs-Problem

Beide Controller verbinden sich über USB-CDC mit dem Raspberry Pi 5. Das Linux-Hostsystem (Debian Trixie) weist ihnen generische Gerätedateien zu (z. B. `/dev/ttyACM0` und `/dev/ttyACM1`).

* **Daten:** Beide Seeed XIAO ESP32-S3 besitzen identische USB Vendor-IDs (VID) und Product-IDs (PID).
* **Regel:** Die Enumeration auf dem USB-Bus ist nicht deterministisch. Nach einem Neustart des Raspberry Pi kann der Antriebs-Controller `/dev/ttyACM1` sein, beim nächsten Mal `/dev/ttyACM0`. Starten die beiden micro-ROS-Agenten im Docker-Container auf den falschen Ports, sendet das System Geschwindigkeitsbefehle an den Ultraschallsensor.
* **Schluss:** Die Zuordnung im ROS 2 Startskript muss unabhängig vom Enumerationszeitpunkt fixiert werden.

### Konsequenz 2: Skript-Erweiterung (udev-Regeln)

Du erstellst im Ordner `scripts/` ein neues Skript `udev_setup.sh`. Dieses Skript liest die eindeutige Hardware-Seriennummer (Serial) der beiden ESP32-Chips aus und bindet sie an feste Symlinks.

**Anwendung:**
Schließt man den ersten ESP32 an, ermittelt man dessen Seriennummer (z. B. mit `udevadm info -a -n /dev/ttyACM0 | grep '{serial}'`). Das Skript schreibt dann folgende Regel in `/etc/udev/rules.d/99-amr-mcu.rules`:

```udev
# ESP32-S3 #1 (Antrieb)
SUBSYSTEM=="tty", ATTRS{idVendor}=="2886", ATTRS{idProduct}=="0056", ATTRS{serial}=="DEINE_SERIAL_1", SYMLINK+="amr_drive"

# ESP32-S3 #2 (Sensoren)
SUBSYSTEM=="tty", ATTRS{idVendor}=="2886", ATTRS{idProduct}=="0056", ATTRS{serial}=="DEINE_SERIAL_2", SYMLINK+="amr_sensor"

```

Dein Start-Skript (`docker/run.sh`) ruft den micro-ROS Agenten anschließend nicht mehr über generische Ports, sondern über die statischen Links `/dev/amr_drive` und `/dev/amr_sensor` auf.
