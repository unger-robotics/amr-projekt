#!/bin/bash
# ==============================================================================
# AMR udev-Regel Setup
# Bietet deterministisches USB-Mapping fuer ESP32-S3 Controller via Seriennummer.
#
# Erstellt stabile Device-Symlinks:
#   /dev/amr_drive  -> Drive-Node (Motoren, PID, Odometrie, IMU, Batterie, Servo)
#   /dev/amr_sensor -> Sensor-Node (Ultraschall HC-SR04, Cliff-Erkennung MH-B)
#   /dev/amr_lidar  -> RPLIDAR A1
#
# Verwendung:
#   sudo bash udev_setup.sh
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
  echo "Fehler: Fehlende Rechte. Bitte mit sudo ausfuehren: sudo ./udev_setup.sh"
  exit 1
fi

UDEV_FILE="/etc/udev/rules.d/99-amr-mcu.rules"

echo "=== AMR udev-Regel Generator ==="
echo "Wir binden die Controller an /dev/amr_drive und /dev/amr_sensor."
echo "------------------------------------------------------------------"

# 1. Nullzustand herstellen
echo "Schritt 1: Bitte ALLE ESP32-Controller vom Raspberry Pi TRENNEN."
read -p "Druecke ENTER, wenn alle USB-Kabel abgezogen sind..."

# 2. Drive Node isolieren
echo ""
echo "Schritt 2: Bitte NUR den DRIVE-NODE (ESP32-S3 #1 - Antrieb) einstecken."
read -p "Druecke ENTER, sobald das Geraet verbunden ist..."
sleep 2 # Puffer fuer udev-Geraetebaumerstellung

DRIVE_DEV=$(ls /dev/ttyACM* 2>/dev/null | head -n1)
if [ -z "$DRIVE_DEV" ]; then
  echo "Fehler: Kein ttyACM-Geraet gefunden. Kabel pruefen und Skript neu starten."
  exit 1
fi

# Extrahiere die Seriennummer aus dem udev-Baum
DRIVE_SERIAL=$(udevadm info -a -n "$DRIVE_DEV" | grep '{serial}' | head -n1 | awk -F'"' '{print $2}')
if [ -z "$DRIVE_SERIAL" ]; then
  echo "Fehler: Konnte Seriennummer fuer $DRIVE_DEV nicht ermitteln."
  exit 1
fi
echo "Erkannt: Drive-Node an $DRIVE_DEV (Serial: $DRIVE_SERIAL)"

# 3. Sensor Node isolieren
echo ""
echo "Schritt 3: Bitte jetzt ZUSAETZLICH den SENSOR-NODE (ESP32-S3 #2) einstecken."
read -p "Druecke ENTER, sobald das Geraet verbunden ist..."
sleep 2

SENSOR_DEV=$(ls /dev/ttyACM* 2>/dev/null | grep -v "$DRIVE_DEV" | head -n1)
if [ -z "$SENSOR_DEV" ]; then
  echo "Fehler: Zweites ttyACM-Geraet nicht gefunden. Skript wird abgebrochen."
  exit 1
fi

SENSOR_SERIAL=$(udevadm info -a -n "$SENSOR_DEV" | grep '{serial}' | head -n1 | awk -F'"' '{print $2}')
if [ -z "$SENSOR_SERIAL" ]; then
  echo "Fehler: Konnte Seriennummer fuer $SENSOR_DEV nicht ermitteln."
  exit 1
fi
echo "Erkannt: Sensor-Node an $SENSOR_DEV (Serial: $SENSOR_SERIAL)"

# 4. Regeldatei generieren
echo ""
echo "Schritt 4: Schreibe $UDEV_FILE ..."

cat > "$UDEV_FILE" << EOF
# AMR ESP32-S3 Controller Mapping (Automatisch generiert von udev_setup.sh)

# ESP32-S3 #1 Drive-Node (Motoren, PID, Odometrie, IMU, Batterie, Servo)
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", ATTRS{serial}=="$DRIVE_SERIAL", SYMLINK+="amr_drive", MODE="0666"

# ESP32-S3 #2 Sensor-Node (Ultraschall HC-SR04, Cliff-Erkennung MH-B)
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", ATTRS{serial}=="$SENSOR_SERIAL", SYMLINK+="amr_sensor", MODE="0666"

# RPLIDAR A1 (CP2102 USB-Serial)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="amr_lidar", MODE="0666"
EOF

# 5. Udev-Subsystem aktualisieren
echo "Lade udev-Regeln neu..."
udevadm control --reload-rules
udevadm trigger

sleep 1
echo "------------------------------------------------------------------"
echo "Erfolgreich! Die Geraete sind nun wie folgt gemappt:"
ls -l /dev/amr_drive /dev/amr_sensor /dev/amr_lidar 2>/dev/null || echo "(Symlinks erscheinen nach erneutem Einstecken)"
