#!/usr/bin/env python3
"""
Pre-Flight-Checkliste fuer den AMR-Roboter.
Interaktives Skript zur Pruefung aller Subsysteme vor Inbetriebnahme.
Laeuft auf Raspberry Pi 5, kein ROS2 erforderlich.

Prueft: USB-Enumeration, Spannungsversorgung, Pin-Belegung, Firmware-Upload.
Erzeugt: Markdown-Protokoll mit Timestamp und Pass/Fail pro Pruefpunkt.
"""

import datetime
import glob
import os
import sys

# ===========================================================================
# Konfiguration (aus hardware/config.h)
# ===========================================================================

PIN_MAPPING = {
    "PIN_MOTOR_LEFT_A": ("D0", "GPIO1", "MDD3A M1A (Vorwaerts-PWM)"),
    "PIN_MOTOR_LEFT_B": ("D1", "GPIO2", "MDD3A M1B (Rueckwaerts-PWM)"),
    "PIN_MOTOR_RIGHT_A": ("D2", "GPIO3", "MDD3A M2A (Vorwaerts-PWM)"),
    "PIN_MOTOR_RIGHT_B": ("D3", "GPIO4", "MDD3A M2B (Rueckwaerts-PWM)"),
    "PIN_ENC_LEFT_A": ("D6", "GPIO43", "Encoder Links (Hall, Interrupt)"),
    "PIN_ENC_RIGHT_A": ("D7", "GPIO44", "Encoder Rechts (Hall, Interrupt)"),
    "PIN_SERVO_PAN": ("D8", "GPIO7", "Servo Pan (Signal, Power extern 5V)"),
    "PIN_SERVO_TILT": ("D9", "GPIO8", "Servo Tilt (Signal, Power extern 5V)"),
    "PIN_LED_MOSFET": ("D10", "GPIO9", "IRLZ24N Low-Side MOSFET"),
    "PIN_I2C_SDA": ("D4", "GPIO5", "I2C SDA (MPU6050, optional)"),
    "PIN_I2C_SCL": ("D5", "GPIO6", "I2C SCL (MPU6050, optional)"),
}

VOLTAGE_SPECS = {
    "3S Li-Ion Akku": ("11.1 - 12.6 V", "Messung am Akku-Connector"),
    "DC/DC USB-C 5V/5A (25W)": ("5.0 - 5.2 V", "Ausgang Buck-Converter, RPi5-Versorgung"),
    "MDD3A VM": ("11.1 - 12.6 V", "Direkt vom Akku, Motortreiber-Eingang"),
    "ESP32-S3 3.3V Rail": ("3.2 - 3.4 V", "Onboard LDO, Logik-Versorgung"),
}

# ===========================================================================
# Ergebnis-Tracking
# ===========================================================================


class CheckResult:
    """Sammelt alle Pruefergebnisse fuer das Protokoll."""

    def __init__(self):
        self.items = []
        self.start_time = datetime.datetime.now()

    def add(self, kategorie, pruefpunkt, status, kommentar=""):
        """Fuegt ein Pruefergebnis hinzu. status: True=PASS, False=FAIL, None=SKIP."""
        self.items.append(
            {
                "kategorie": kategorie,
                "pruefpunkt": pruefpunkt,
                "status": status,
                "kommentar": kommentar,
            }
        )

    def count_pass(self):
        return sum(1 for i in self.items if i["status"] is True)

    def count_fail(self):
        return sum(1 for i in self.items if i["status"] is False)

    def count_skip(self):
        return sum(1 for i in self.items if i["status"] is None)

    def all_passed(self):
        return self.count_fail() == 0


# ===========================================================================
# Hilfsfunktionen
# ===========================================================================


def ask_yes_no(frage):
    """Interaktive Ja/Nein-Abfrage. Gibt True/False/None (Skip) zurueck."""
    while True:
        antwort = input(f"  {frage} [j/n/s(kip)]: ").strip().lower()
        if antwort in ("j", "ja", "y", "yes"):
            return True
        if antwort in ("n", "nein", "no"):
            return False
        if antwort in ("s", "skip", "ueberspringen"):
            return None
        print("    Bitte 'j' (ja), 'n' (nein) oder 's' (skip) eingeben.")


def ask_value(frage, einheit=""):
    """Fragt einen Messwert ab (optional). Gibt String oder leeren String zurueck."""
    suffix = f" [{einheit}]" if einheit else ""
    return input(f"  {frage}{suffix} (Enter=uebersprungen): ").strip()


def print_header(titel):
    """Gibt eine formatierte Ueberschrift aus."""
    print()
    print("=" * 60)
    print(f"  {titel}")
    print("=" * 60)


def print_result_line(status, text):
    """Zeigt ein Ergebnis farbig an (ANSI-Codes)."""
    if status is True:
        tag = "\033[32m[PASS]\033[0m"
    elif status is False:
        tag = "\033[31m[FAIL]\033[0m"
    else:
        tag = "\033[33m[SKIP]\033[0m"
    print(f"  {tag} {text}")


# ===========================================================================
# Pruef-Abschnitte
# ===========================================================================


def check_usb_enumeration(result):
    """Prueft ob der ESP32-S3 als USB-CDC erkannt wird."""
    print_header("1. USB-Enumeration")

    # Automatisch nach /dev/ttyACM* suchen
    acm_devices = sorted(glob.glob("/dev/ttyACM*"))

    if acm_devices:
        print(f"  Gefundene USB-CDC-Geraete: {', '.join(acm_devices)}")
        status = True
        kommentar = ", ".join(acm_devices)
    else:
        print("  WARNUNG: Kein /dev/ttyACM* gefunden.")
        print("  Moegliche Ursachen:")
        print("    - USB-C Kabel nicht angeschlossen")
        print("    - ESP32-S3 nicht gestartet / im Bootloader-Modus")
        print("    - USB-CDC nicht aktiviert (menuconfig)")
        status = False
        kommentar = "Kein /dev/ttyACM* gefunden"

        # Zusaetzlich /dev/ttyUSB* pruefen (alternative UART-Bridges)
        usb_devices = sorted(glob.glob("/dev/ttyUSB*"))
        if usb_devices:
            print(f"  Hinweis: /dev/ttyUSB* gefunden: {', '.join(usb_devices)}")
            kommentar += f"; ttyUSB: {', '.join(usb_devices)}"

    print_result_line(status, "USB-CDC Enumeration")
    result.add("USB", "USB-CDC Enumeration (/dev/ttyACM*)", status, kommentar)
    return acm_devices


def check_spannungsversorgung(result):
    """Interaktive Pruefung der Spannungsversorgung."""
    print_header("2. Spannungsversorgung")
    print("  Bitte mit Multimeter messen und Werte eingeben.")
    print()

    for name, (soll_bereich, hinweis) in VOLTAGE_SPECS.items():
        print(f"  --- {name} ---")
        print(f"  Soll-Bereich: {soll_bereich}")
        print(f"  Messpunkt: {hinweis}")
        messwert = ask_value(f"Gemessene Spannung fuer '{name}'", "V")

        if messwert:
            ok = ask_yes_no(f"Liegt {messwert} V im Soll-Bereich {soll_bereich}?")
            kommentar = f"Gemessen: {messwert} V (Soll: {soll_bereich})"
        else:
            ok = None
            kommentar = "Nicht gemessen"

        print_result_line(ok, name)
        result.add("Spannung", name, ok, kommentar)
        print()

    # Zusaetzliche Pruefpunkte: Sicherung und Masse
    print("  --- Hauptsicherung 15 A ---")
    print("  Visuell pruefen: Sicherung nahe Akku vorhanden und korrekt dimensioniert (15 A).")
    fuse_ok = ask_yes_no("Hauptsicherung 15 A vorhanden und korrekt?")
    print_result_line(fuse_ok, "Hauptsicherung 15 A")
    result.add("Spannung", "Hauptsicherung 15 A", fuse_ok, "Visuelle Pruefung nahe Akku")
    print()

    print("  --- Gemeinsame Masse / Sternpunkt-GND ---")
    print("  Pruefen: Pi-GND, Buck-GND, Motortreiber-GND, ESP32-GND an einem Punkt verbunden.")
    gnd_ok = ask_yes_no("Sternpunkt-GND korrekt verdrahtet?")
    print_result_line(gnd_ok, "Gemeinsame Masse / Sternpunkt-GND")
    result.add(
        "Spannung",
        "Gemeinsame Masse / Sternpunkt-GND",
        gnd_ok,
        "Pi-GND, Buck-GND, MDD3A-GND, ESP32-GND verbunden",
    )
    print()


def check_pin_belegung(result):
    """Interaktive Pruefung der Pin-Belegung gegen config.h."""
    print_header("3. Pin-Belegung (gegen config.h)")
    print("  Bitte physische Verdrahtung mit Soll-Belegung vergleichen.")
    print()

    for define_name, (dx_pin, gpio, funktion) in PIN_MAPPING.items():
        print(f"  {define_name}: {dx_pin} ({gpio}) -> {funktion}")

    print()
    ok = ask_yes_no("Stimmt die physische Verdrahtung mit der Tabelle ueberein?")
    kommentar = "Visuelle Inspektion" if ok else "Abweichung festgestellt"

    # Kritische Motor-Pins einzeln abfragen bei Fail
    if ok is False:
        print("  Bitte einzelne Pins pruefen:")
        for define_name, (dx_pin, gpio, funktion) in PIN_MAPPING.items():
            pin_ok = ask_yes_no(f"{define_name} = {dx_pin} ({gpio}) -> {funktion}?")
            pin_kommentar = f"{dx_pin} ({gpio}) -> {funktion}"
            print_result_line(pin_ok, f"{define_name}")
            result.add("Pins", define_name, pin_ok, pin_kommentar)
        return

    print_result_line(ok, "Pin-Belegung gesamt")
    result.add("Pins", "Pin-Belegung (alle Pins)", ok, kommentar)

    # Encoder-Versorgung separat pruefen
    print()
    print("  --- Encoder VCC/GND Anschluss ---")
    print("  Beide Hall-Encoder (Links + Rechts) benoetigen VCC und GND zusaetzlich")
    print("  zur Signalleitung (Phase A). VCC = 3.3 V oder 5 V (mit Pegelanpassung).")
    enc_pwr_ok = ask_yes_no("Encoder VCC und GND an beiden Motoren angeschlossen?")
    print_result_line(enc_pwr_ok, "Encoder VCC/GND Anschluss")
    result.add(
        "Pins",
        "Encoder VCC/GND Anschluss",
        enc_pwr_ok,
        "VCC + GND fuer Hall-Encoder Links und Rechts",
    )


def check_firmware(result):
    """Pruefung Firmware-Upload und Boot-Meldung."""
    print_header("4. Firmware")
    print("  Pruefung ob Firmware hochgeladen und gestartet ist.")
    print()

    # 4a: Firmware-Upload
    print("  4a) Firmware-Upload")
    print("  Kommando: cd amr/esp32_amr_firmware/ && pio run -t upload")
    upload_ok = ask_yes_no("Wurde die Firmware erfolgreich hochgeladen (SUCCESS)?")
    kommentar_upload = "pio run -t upload"
    if upload_ok is False:
        fehler = input("  Fehlermeldung (kurz): ").strip()
        kommentar_upload += f" -> Fehler: {fehler}"

    print_result_line(upload_ok, "Firmware-Upload")
    result.add("Firmware", "PlatformIO Upload", upload_ok, kommentar_upload)

    # 4b: Serial Monitor Boot-Meldung
    print()
    print("  4b) Serial Monitor Boot-Meldung")
    print("  Kommando: pio run -t monitor (115200 Baud)")
    print("  Erwartete Ausgabe: micro-ROS Initialisierung, PID-Start")
    boot_ok = ask_yes_no("Zeigt der Serial Monitor eine korrekte Boot-Meldung?")
    kommentar_boot = "115200 Baud, Boot-Log"
    if boot_ok is False:
        fehler = input("  Symptom (kurz): ").strip()
        kommentar_boot += f" -> Problem: {fehler}"

    print_result_line(boot_ok, "Boot-Meldung")
    result.add("Firmware", "Serial Monitor Boot-Meldung", boot_ok, kommentar_boot)


def check_micro_ros(result):
    """Prueft micro-ROS Verbindung (optional, falls Agent laeuft)."""
    print_header("5. micro-ROS Verbindung (optional)")
    print("  Nur pruefbar, wenn micro-ROS Agent auf RPi5 laeuft.")
    print("  Kommando: ros2 topic list")
    print()

    pruefen = ask_yes_no("micro-ROS Agent laeuft und soll geprueft werden?")
    if pruefen is None or pruefen is False:
        result.add("micro-ROS", "micro-ROS Agent", None, "Uebersprungen")
        print_result_line(None, "micro-ROS (uebersprungen)")
        return

    odom_ok = ask_yes_no("/odom Topic sichtbar (ros2 topic list)?")
    result.add("micro-ROS", "/odom Topic", odom_ok, "ros2 topic list | grep odom")
    print_result_line(odom_ok, "/odom Topic")

    cmd_ok = ask_yes_no("/cmd_vel Topic sichtbar?")
    result.add("micro-ROS", "/cmd_vel Topic", cmd_ok, "ros2 topic list | grep cmd_vel")
    print_result_line(cmd_ok, "/cmd_vel Topic")


def check_sensoren(result):
    """Pruefung der angeschlossenen Sensoren."""
    print_header("6. Sensoren")

    # LiDAR
    print("  6a) RPLIDAR A1")
    lidar_devices = sorted(glob.glob("/dev/ttyUSB*"))
    if lidar_devices:
        print(f"  Gefundene ttyUSB-Geraete: {', '.join(lidar_devices)}")
    else:
        print("  Kein /dev/ttyUSB* gefunden (RPLIDAR nicht angeschlossen?)")

    lidar_ok = ask_yes_no("RPLIDAR A1 angeschlossen und sichtbar?")
    kommentar_lidar = f"Geraete: {', '.join(lidar_devices)}" if lidar_devices else "Kein ttyUSB"
    print_result_line(lidar_ok, "RPLIDAR A1")
    result.add("Sensoren", "RPLIDAR A1", lidar_ok, kommentar_lidar)

    # Kamera
    print()
    print("  6b) Raspberry Pi Global Shutter Camera (CSI)")
    cam_devices = sorted(glob.glob("/dev/video*"))
    if cam_devices:
        print(f"  Gefundene Video-Geraete: {', '.join(cam_devices)}")
    else:
        print("  Kein /dev/video* gefunden.")

    cam_ok = ask_yes_no("Kamera angeschlossen und erkannt?")
    kommentar_cam = f"Geraete: {', '.join(cam_devices)}" if cam_devices else "Kein video device"
    print_result_line(cam_ok, "Kamera (CSI)")
    result.add("Sensoren", "RPi Global Shutter Camera (CSI)", cam_ok, kommentar_cam)


# ===========================================================================
# Protokoll-Erzeugung
# ===========================================================================


def generate_markdown(result):
    """Erzeugt Markdown-Protokoll als String."""
    ts = result.start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = len(result.items)
    passed = result.count_pass()
    failed = result.count_fail()
    skipped = result.count_skip()
    gesamtergebnis = "PASS" if result.all_passed() else "FAIL"

    lines = []
    lines.append("# Pre-Flight Checkliste AMR")
    lines.append("")
    lines.append("| Feld | Wert |")
    lines.append("|---|---|")
    lines.append(f"| Datum/Start | {ts} |")
    lines.append(f"| Datum/Ende | {end_time} |")
    lines.append(f"| Gesamtergebnis | **{gesamtergebnis}** |")
    lines.append(f"| Gesamt | {total} Pruefpunkte |")
    lines.append(f"| Bestanden | {passed} |")
    lines.append(f"| Fehlgeschlagen | {failed} |")
    lines.append(f"| Uebersprungen | {skipped} |")
    lines.append("")

    # Nach Kategorie gruppieren
    kategorien = []
    seen = set()
    for item in result.items:
        k = item["kategorie"]
        if k not in seen:
            kategorien.append(k)
            seen.add(k)

    for kat in kategorien:
        lines.append(f"## {kat}")
        lines.append("")
        lines.append("| Pruefpunkt | Ergebnis | Kommentar |")
        lines.append("|---|---|---|")
        for item in result.items:
            if item["kategorie"] != kat:
                continue
            if item["status"] is True:
                status_str = "PASS"
            elif item["status"] is False:
                status_str = "**FAIL**"
            else:
                status_str = "SKIP"
            lines.append(f"| {item['pruefpunkt']} | {status_str} | {item['kommentar']} |")
        lines.append("")

    return "\n".join(lines)


def save_protocol(markdown_content):
    """Speichert Protokoll als Datei im aktuellen Verzeichnis."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pre_flight_{ts}.md"

    # Versuche ins scripts-Verzeichnis zu speichern, sonst aktuelles Verzeichnis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return filepath


# ===========================================================================
# Hauptprogramm
# ===========================================================================


def main():
    print()
    print("*" * 60)
    print("  AMR Pre-Flight Checkliste")
    print("  XIAO ESP32-S3 + Cytron MDD3A + JGA25-370")
    print(f"  Zeitpunkt: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("*" * 60)
    print()
    print("  Dieses Skript fuehrt durch alle Pruefschritte vor der")
    print("  Inbetriebnahme des AMR-Roboters. Fuer jede Pruefung")
    print("  wird eine interaktive Bestaetigung abgefragt.")
    print("  Antworten: j=ja, n=nein, s=ueberspringen")
    print()

    result = CheckResult()

    try:
        check_usb_enumeration(result)
        check_spannungsversorgung(result)
        check_pin_belegung(result)
        check_firmware(result)
        check_micro_ros(result)
        check_sensoren(result)
    except KeyboardInterrupt:
        print("\n\n  Abgebrochen durch Benutzer (Ctrl+C).")
        print("  Bisherige Ergebnisse werden gespeichert.\n")

    # Zusammenfassung
    print_header("ZUSAMMENFASSUNG")
    total = len(result.items)
    passed = result.count_pass()
    failed = result.count_fail()
    skipped = result.count_skip()

    print(f"  Gesamt:          {total} Pruefpunkte")
    print(f"  \033[32mBestanden:       {passed}\033[0m")
    print(f"  \033[31mFehlgeschlagen:  {failed}\033[0m")
    print(f"  \033[33mUebersprungen:   {skipped}\033[0m")
    print()

    if result.all_passed():
        print("  \033[32m>>> ERGEBNIS: PASS - Roboter ist einsatzbereit <<<\033[0m")
    else:
        print("  \033[31m>>> ERGEBNIS: FAIL - Probleme muessen behoben werden <<<\033[0m")

    # Protokoll speichern
    md = generate_markdown(result)
    filepath = save_protocol(md)
    print(f"\n  Protokoll gespeichert: {filepath}")
    print()

    return 0 if result.all_passed() else 1


if __name__ == "__main__":
    sys.exit(main())
