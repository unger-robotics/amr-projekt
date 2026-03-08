#!/usr/bin/env python3
"""
Hardware-Info-Skript fuer Raspberry Pi 5 und AMR-Peripherie.
Erfasst den Hardware-Zustand aller Komponenten und gibt einen
formatierten Report aus. Kein ROS2 erforderlich.

Aufruf: python3 amr/scripts/hardware_info [--save] [--json]

Erfasste Daten:
  1. Systemressourcen (CPU, RAM, Disk, Temperatur, Throttling)
  2. AMR-Peripherie (ESP32, RPLIDAR, Kamera, Hailo, Netzwerk, CAN, Audio)
  3. Betriebssystem und Software (OS, Docker, PlatformIO, Toolchains)
  4. Projekt-Info (Git, Docker-Image, Configs, Boot, Firmware-Builds)
"""

import argparse
import datetime
import json
import os
import sys

# Package-Dir in sys.path, damit Aufruf als python3 amr/scripts/hardware_info funktioniert
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from peripherals import (  # noqa: E402
    collect_peripherals,
    generate_peripherals_markdown,
    print_peripherals,
)
from project import (  # noqa: E402
    collect_project_info,
    generate_project_markdown,
    print_project_info,
)
from software import collect_software, generate_software_markdown, print_software  # noqa: E402
from system import (  # noqa: E402
    collect_system_resources,
    generate_system_markdown,
    print_system_resources,
)
from utils import COLOR_BOLD, COLOR_RESET, print_info  # noqa: E402


def generate_markdown(
    system: dict,
    peripherals: dict,
    software: dict,
    project: dict | None = None,
) -> str:
    """Erzeugt einen vollstaendigen Markdown-Report aus allen Sektionen."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []

    # Header
    lines.append("# AMR Hardware-Info Report")
    lines.append("")
    lines.append(f"**Zeitpunkt:** {ts}")
    lines.append("")

    # Teil-Markdowns zusammenfuegen
    lines.append(generate_system_markdown(system, software))
    lines.append(generate_peripherals_markdown(peripherals))
    lines.append(generate_software_markdown(software))

    if project:
        lines.append(generate_project_markdown(project))

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(
        f"*Generiert mit `hardware_info` am {ts} auf {software.get('pi_model', 'Raspberry Pi')}*"
    )
    lines.append("")

    return "\n".join(lines)


def generate_json(
    system: dict,
    peripherals: dict,
    software: dict,
    project: dict | None = None,
) -> str:
    """Erzeugt JSON-Report aus allen Sektionen."""
    report: dict = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system": system,
        "peripherals": peripherals,
        "software": software,
    }
    if project:
        report["project"] = project

    # raw_output kann sehr lang sein, rausnehmen
    if "camera" in report["peripherals"]:
        report["peripherals"]["camera"].pop("raw_output", None)
    # USB raw-Eintraege bereinigen
    for dev in report["peripherals"].get("usb_devices", []):
        dev.pop("raw", None)
    for dev in report["peripherals"].get("pcie_devices", []):
        dev.pop("raw", None)

    return json.dumps(report, indent=2, ensure_ascii=False)


def main() -> int:
    """Haupteinstiegspunkt: Argumente parsen, Daten sammeln, Report ausgeben."""
    parser = argparse.ArgumentParser(
        description="Hardware-Info fuer Raspberry Pi 5 und AMR-Peripherie"
    )
    parser.add_argument("--save", action="store_true", help="Markdown-Report als Datei speichern")
    parser.add_argument("--json", action="store_true", help="JSON-Ausgabe statt Terminal-Report")
    args = parser.parse_args()

    # Daten sammeln
    system = collect_system_resources()
    peripherals = collect_peripherals()
    software = collect_software()
    project = collect_project_info()

    # JSON-Modus
    if args.json:
        print(generate_json(system, peripherals, software, project))
        return 0

    # Terminal-Ausgabe
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print(f"{COLOR_BOLD}{'*' * 60}")
    print("  AMR Hardware-Info Report")
    print("  Raspberry Pi 5 + ESP32-S3 + RPLIDAR + IMX296")
    print(f"  {ts}")
    print(f"{'*' * 60}{COLOR_RESET}")

    print_system_resources(system)
    print_peripherals(peripherals)
    print_software(software)
    print_project_info(project)

    print()

    # Markdown speichern
    if args.save:
        md = generate_markdown(system, peripherals, software, project)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = f"hardware_info_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(script_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print_info("Report gespeichert", filepath)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
