"""Sektion 3: Betriebssystem und Software."""

import platform
from pathlib import Path
from typing import Any

from utils import (
    COLOR_CYAN,
    COLOR_RESET,
    print_header,
    print_info,
    print_warn,
    run_cmd,
)

__all__ = ["collect_software", "print_software", "generate_software_markdown"]


def collect_software() -> dict[str, Any]:
    """Sammelt Betriebssystem- und Software-Informationen."""
    data: dict[str, Any] = {}

    # OS-Release
    try:
        os_release = platform.freedesktop_os_release()
        data["os_name"] = os_release.get("PRETTY_NAME", "Unbekannt")
        data["os_id"] = os_release.get("ID", "")
        data["os_version"] = os_release.get("VERSION_ID", "")
    except (AttributeError, OSError):
        # Fallback: /etc/os-release manuell lesen
        try:
            release_text = Path("/etc/os-release").read_text()
            for line in release_text.splitlines():
                if line.startswith("PRETTY_NAME="):
                    data["os_name"] = line.split("=", 1)[1].strip('"')
                elif line.startswith("ID="):
                    data["os_id"] = line.split("=", 1)[1].strip('"')
                elif line.startswith("VERSION_ID="):
                    data["os_version"] = line.split("=", 1)[1].strip('"')
        except FileNotFoundError:
            data["os_name"] = platform.platform()

    # Kernel
    data["kernel"] = platform.release()

    # Architektur
    data["arch"] = platform.machine()

    # Python
    data["python_version"] = platform.python_version()

    # Docker
    docker_ver = run_cmd("docker --version 2>/dev/null")
    data["docker_version"] = docker_ver if docker_ver else None

    compose_ver = run_cmd("docker compose version 2>/dev/null")
    data["docker_compose_version"] = compose_ver if compose_ver else None

    # Docker-Container
    containers: dict[str, Any] = {"running": [], "all": []}
    running_output = run_cmd("docker ps --format '{{.Names}}\\t{{.Status}}' 2>/dev/null")
    if running_output:
        for line in running_output.splitlines():
            parts = line.split("\\t", 1)
            containers["running"].append(
                {"name": parts[0], "status": parts[1] if len(parts) > 1 else "?"}
            )
    all_output = run_cmd("docker ps -a --format '{{.Names}}\\t{{.Status}}' 2>/dev/null")
    if all_output:
        for line in all_output.splitlines()[:10]:
            parts = line.split("\\t", 1)
            containers["all"].append(
                {"name": parts[0], "status": parts[1] if len(parts) > 1 else "?"}
            )
    data["docker_containers"] = containers

    # C/C++ Compiler (System)
    gcc_ver = run_cmd("gcc --version 2>/dev/null")
    if gcc_ver:
        data["gcc_version"] = gcc_ver.splitlines()[0]
    else:
        data["gcc_version"] = None

    # ESP32 Toolchain (PlatformIO xtensa-esp32s3)
    pio_ver = run_cmd("pio --version 2>/dev/null")
    data["platformio_version"] = pio_ver if pio_ver else None

    esp_gcc = None
    pio_home = Path.home() / ".platformio"
    toolchain_bins = sorted(
        pio_home.glob("packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-gcc")
    )
    if toolchain_bins:
        esp_gcc = run_cmd(f"{toolchain_bins[0]} --version 2>/dev/null")
        if esp_gcc:
            esp_gcc = esp_gcc.splitlines()[0]
    data["esp32_gcc_version"] = esp_gcc

    # Key-Pakete via dpkg
    packages = {
        "python3-opencv": "OpenCV (Computer Vision)",
        "python3-serial": "PySerial (Serial-Kommunikation)",
        "python3-numpy": "NumPy (Numerik)",
        "python3-hailort": "HailoRT (AI Accelerator)",
        "v4l2loopback-dkms": "v4l2loopback (Kamera-Bridge)",
        "rpicam-apps": "rpicam-apps (Kamera-Tools)",
    }
    pkg_status = {}
    for pkg, desc in packages.items():
        ver = run_cmd(f"dpkg-query -W -f='${{Version}}' {pkg} 2>/dev/null")
        pkg_status[pkg] = {"description": desc, "version": ver}
    data["packages"] = pkg_status

    # Pi-Modell
    try:
        model = Path("/proc/device-tree/model").read_text().rstrip("\x00").strip()
        data["pi_model"] = model
    except FileNotFoundError:
        data["pi_model"] = None

    # Uptime
    try:
        uptime_raw = Path("/proc/uptime").read_text().strip()
        uptime_secs = float(uptime_raw.split()[0])
        days = int(uptime_secs // 86400)
        hours = int((uptime_secs % 86400) // 3600)
        mins = int((uptime_secs % 3600) // 60)
        if days > 0:
            data["uptime"] = f"{days}d {hours}h {mins}m"
        elif hours > 0:
            data["uptime"] = f"{hours}h {mins}m"
        else:
            data["uptime"] = f"{mins}m"
        data["uptime_seconds"] = uptime_secs
    except (FileNotFoundError, ValueError):
        pass

    return data


def print_software(data: dict[str, Any]) -> None:
    """Gibt Sektion 3: Software-Informationen aus."""
    print_header("3. Betriebssystem und Software")

    # Pi-Modell
    model = data.get("pi_model")
    if model:
        print_info("Hardware", model)

    # Uptime
    uptime = data.get("uptime")
    if uptime:
        print_info("Uptime", uptime)

    # OS
    os_name = data.get("os_name")
    if os_name:
        print_info("OS", os_name)

    # Kernel
    print_info("Kernel", data.get("kernel", "?"))

    # Arch
    print_info("Architektur", data.get("arch", "?"))

    # Python
    print_info("Python", data.get("python_version", "?"))

    # Docker
    docker_ver = data.get("docker_version")
    if docker_ver:
        print_info("Docker", docker_ver)
    else:
        print_warn("Docker", "nicht installiert")

    compose_ver = data.get("docker_compose_version")
    if compose_ver:
        print_info("Docker Compose", compose_ver)
    else:
        print_warn("Docker Compose", "nicht installiert")

    # Docker-Container
    containers = data.get("docker_containers", {})
    running = containers.get("running", [])
    if running:
        print()
        print(f"  {COLOR_CYAN}--- Docker-Container ---{COLOR_RESET}")
        for c in running:
            print_info(f"  {c['name']}", c["status"])
    elif containers.get("all"):
        print()
        print_warn("Keine laufenden Docker-Container")

    # C/C++ Compiler
    gcc_ver = data.get("gcc_version")
    if gcc_ver:
        print_info("C/C++ (System)", gcc_ver)
    else:
        print_warn("C/C++ (System)", "gcc nicht installiert")

    # ESP32 Toolchain
    pio_ver = data.get("platformio_version")
    if pio_ver:
        print_info("PlatformIO", pio_ver)
    else:
        print_warn("PlatformIO", "nicht installiert")

    esp_gcc = data.get("esp32_gcc_version")
    if esp_gcc:
        print_info("ESP32-S3 Toolchain", esp_gcc)
    elif pio_ver:
        print_warn("ESP32-S3 Toolchain", "nicht gefunden (~/.platformio/packages/)")

    # Pakete
    packages = data.get("packages", {})
    if packages:
        print()
        print(f"  {COLOR_CYAN}Installierte Pakete:{COLOR_RESET}")
        for pkg, info in packages.items():
            ver = info.get("version")
            desc = info.get("description", "")
            if ver:
                print_info(f"  {pkg}", f"{ver} ({desc})")
            else:
                print_warn(f"  {pkg}", f"nicht installiert ({desc})")


def generate_software_markdown(data: dict[str, Any]) -> str:
    """Erzeugt Markdown fuer Sektion 3: Betriebssystem und Software."""
    lines = []
    lines.append("## 3. Betriebssystem und Software")
    lines.append("")
    lines.append("| Komponente | Version |")
    lines.append("|---|---|")
    lines.append(f"| OS | {data.get('os_name', '-')} |")
    lines.append(f"| Kernel | {data.get('kernel', '-')} |")
    lines.append(f"| Architektur | {data.get('arch', '-')} |")
    lines.append(f"| Python | {data.get('python_version', '-')} |")
    lines.append(f"| Docker | {data.get('docker_version', '-') or '-'} |")
    lines.append(f"| Docker Compose | {data.get('docker_compose_version', '-') or '-'} |")
    lines.append(f"| C/C++ (System) | {data.get('gcc_version', '-') or '-'} |")
    lines.append(f"| PlatformIO | {data.get('platformio_version', '-') or '-'} |")
    lines.append(f"| ESP32-S3 Toolchain | {data.get('esp32_gcc_version', '-') or '-'} |")

    # Docker-Container
    containers = data.get("docker_containers", {})
    running = containers.get("running", [])
    if running:
        lines.append("")
        lines.append("### Docker-Container")
        lines.append("")
        lines.append("| Name | Status |")
        lines.append("|---|---|")
        for c in running:
            lines.append(f"| {c['name']} | {c['status']} |")

    packages = data.get("packages", {})
    if packages:
        lines.append("")
        lines.append("### Pakete")
        lines.append("")
        lines.append("| Paket | Version | Beschreibung |")
        lines.append("|---|---|---|")
        for pkg, info in packages.items():
            ver = info.get("version") or "-"
            desc = info.get("description", "")
            lines.append(f"| {pkg} | {ver} | {desc} |")

    lines.append("")
    return "\n".join(lines)
