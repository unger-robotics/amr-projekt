#!/usr/bin/env python3
"""
Hardware-Info-Skript fuer Raspberry Pi 5 und AMR-Peripherie.
Erfasst den Hardware-Zustand aller Komponenten und gibt einen
formatierten Report aus. Kein ROS2 erforderlich.

Ausgabe: Terminal (farbkodiert), optional Markdown (--save) oder JSON (--json).
"""

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
from glob import glob
from pathlib import Path


# ===========================================================================
# ANSI-Farben und Formatierung
# ===========================================================================

COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def print_header(titel):
    """Gibt eine formatierte Sektions-Ueberschrift aus."""
    print()
    print(f"{COLOR_BOLD}{'=' * 60}")
    print(f"  {titel}")
    print(f"{'=' * 60}{COLOR_RESET}")


def print_info(text, value=""):
    """Gibt eine INFO-Zeile aus."""
    if value:
        print(f"  {COLOR_GREEN}[INFO]{COLOR_RESET} {text}: {COLOR_BOLD}{value}{COLOR_RESET}")
    else:
        print(f"  {COLOR_GREEN}[INFO]{COLOR_RESET} {text}")


def print_warn(text, value=""):
    """Gibt eine WARN-Zeile aus."""
    if value:
        print(f"  {COLOR_YELLOW}[WARN]{COLOR_RESET} {text}: {value}")
    else:
        print(f"  {COLOR_YELLOW}[WARN]{COLOR_RESET} {text}")


def print_fail(text, value=""):
    """Gibt eine FAIL-Zeile aus."""
    if value:
        print(f"  {COLOR_RED}[FAIL]{COLOR_RESET} {text}: {value}")
    else:
        print(f"  {COLOR_RED}[FAIL]{COLOR_RESET} {text}")


def run_cmd(cmd, timeout=5):
    """Fuehrt ein Shell-Kommando aus und gibt stdout zurueck (oder None bei Fehler)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


# ===========================================================================
# Datensammlung
# ===========================================================================

def collect_system_resources():
    """Sammelt Systemressourcen und thermischen Zustand."""
    data = {}

    # Temperatur
    try:
        temp_raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        temp_c = int(temp_raw) / 1000.0
        data["temperature_c"] = temp_c
    except (FileNotFoundError, ValueError):
        data["temperature_c"] = None

    # CPU-Frequenzen
    freq_files = sorted(glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"))
    freqs = []
    for f in freq_files:
        try:
            freq_khz = int(Path(f).read_text().strip())
            freqs.append(freq_khz / 1000.0)  # MHz
        except (ValueError, FileNotFoundError):
            pass
    data["cpu_freq_mhz"] = freqs
    data["cpu_count"] = len(freq_files) if freq_files else os.cpu_count()

    # CPU-Modell
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text()
        for line in cpuinfo.splitlines():
            if line.startswith("model name") or line.startswith("Model"):
                data["cpu_model"] = line.split(":", 1)[1].strip()
                break
    except FileNotFoundError:
        pass

    # Load Average
    try:
        loadavg = Path("/proc/loadavg").read_text().strip()
        parts = loadavg.split()
        data["load_1m"] = float(parts[0])
        data["load_5m"] = float(parts[1])
        data["load_15m"] = float(parts[2])
    except (FileNotFoundError, ValueError, IndexError):
        pass

    # RAM
    try:
        meminfo = Path("/proc/meminfo").read_text()
        mem = {}
        for line in meminfo.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip().replace(" kB", "")
                try:
                    mem[key.strip()] = int(val)
                except ValueError:
                    pass
        total_kb = mem.get("MemTotal", 0)
        avail_kb = mem.get("MemAvailable", 0)
        used_kb = total_kb - avail_kb
        data["ram_total_mb"] = round(total_kb / 1024)
        data["ram_used_mb"] = round(used_kb / 1024)
        data["ram_available_mb"] = round(avail_kb / 1024)
        data["ram_usage_pct"] = round(used_kb / total_kb * 100, 1) if total_kb else 0
    except FileNotFoundError:
        pass

    # Disk
    try:
        st = os.statvfs("/")
        total_bytes = st.f_frsize * st.f_blocks
        free_bytes = st.f_frsize * st.f_bavail
        used_bytes = total_bytes - free_bytes
        data["disk_total_gb"] = round(total_bytes / (1024 ** 3), 1)
        data["disk_used_gb"] = round(used_bytes / (1024 ** 3), 1)
        data["disk_free_gb"] = round(free_bytes / (1024 ** 3), 1)
        data["disk_usage_pct"] = round(used_bytes / total_bytes * 100, 1) if total_bytes else 0
    except OSError:
        pass

    # Throttling (Pi-spezifisch)
    throttle_output = run_cmd("vcgencmd get_throttled 2>/dev/null")
    if throttle_output and "=" in throttle_output:
        throttle_hex = throttle_output.split("=", 1)[1].strip()
        data["throttle_hex"] = throttle_hex
        try:
            throttle_val = int(throttle_hex, 16)
            flags = []
            if throttle_val & 0x1:
                flags.append("Under-voltage detected")
            if throttle_val & 0x2:
                flags.append("ARM frequency capped")
            if throttle_val & 0x4:
                flags.append("Currently throttled")
            if throttle_val & 0x8:
                flags.append("Soft temperature limit active")
            if throttle_val & 0x10000:
                flags.append("Under-voltage has occurred")
            if throttle_val & 0x20000:
                flags.append("ARM frequency capping has occurred")
            if throttle_val & 0x40000:
                flags.append("Throttling has occurred")
            if throttle_val & 0x80000:
                flags.append("Soft temperature limit has occurred")
            data["throttle_flags"] = flags
        except ValueError:
            data["throttle_flags"] = []
    else:
        data["throttle_hex"] = None
        data["throttle_flags"] = []

    return data


def collect_peripherals():
    """Sammelt AMR-Peripherie und Schnittstellen."""
    data = {}

    # USB-Geraete via lsusb
    usb_devices = []
    lsusb_output = run_cmd("lsusb")
    if lsusb_output:
        known_devices = {
            "303a:1001": "Espressif ESP32-S3 (USB JTAG/serial)",
            "10c4:ea60": "Silicon Labs CP210x (RPLIDAR)",
        }
        for line in lsusb_output.splitlines():
            entry = {"raw": line.strip()}
            for vid_pid, desc in known_devices.items():
                if vid_pid in line.lower():
                    entry["identified"] = desc
                    entry["vid_pid"] = vid_pid
            usb_devices.append(entry)
    data["usb_devices"] = usb_devices

    # Bekannte Geraete extrahieren
    data["esp32_found"] = any(d.get("vid_pid") == "303a:1001" for d in usb_devices)
    data["rplidar_found"] = any(d.get("vid_pid") == "10c4:ea60" for d in usb_devices)

    # Serial-Devices
    acm_devices = sorted(glob("/dev/ttyACM*"))
    usb_serial = sorted(glob("/dev/ttyUSB*"))
    data["tty_acm"] = acm_devices
    data["tty_usb"] = usb_serial

    # udev-Symlinks (stabile Geraete-Pfade)
    serial_by_id = sorted(glob("/dev/serial/by-id/*"))
    data["serial_by_id"] = serial_by_id

    # Kamera (rpicam-hello / libcamera-hello)
    cam_data = {"detected": False, "sensors": []}
    for cam_cmd in ["rpicam-hello --list-cameras", "libcamera-hello --list-cameras"]:
        cam_output = run_cmd(cam_cmd, timeout=10)
        if cam_output:
            cam_data["detected"] = True
            cam_data["tool"] = cam_cmd.split()[0]
            # Sensor-Info parsen
            for line in cam_output.splitlines():
                stripped = line.strip()
                if stripped and (":" in stripped) and any(
                    s in stripped.lower() for s in ["imx", "ov", "sensor", "mode"]
                ):
                    cam_data["sensors"].append(stripped)
            # Gesamtausgabe fuer Details
            cam_data["raw_output"] = cam_output
            break
    data["camera"] = cam_data

    # Video-Devices
    video_devices = sorted(glob("/dev/video*"))
    data["video_devices"] = video_devices

    # v4l2loopback (/dev/video10)
    data["v4l2loopback_present"] = os.path.exists("/dev/video10")

    # camera-v4l2-bridge Service
    bridge_status = run_cmd("systemctl is-active camera-v4l2-bridge.service 2>/dev/null")
    data["camera_bridge_active"] = bridge_status == "active" if bridge_status else None

    # PCIe (Hailo-8 etc.)
    pcie_devices = []
    lspci_output = run_cmd("lspci 2>/dev/null")
    if lspci_output:
        for line in lspci_output.splitlines():
            entry = {"raw": line.strip()}
            if "hailo" in line.lower():
                entry["identified"] = "Hailo-8 AI Accelerator"
            pcie_devices.append(entry)
    data["pcie_devices"] = pcie_devices
    data["hailo_found"] = any("identified" in d for d in pcie_devices)

    # embedded-bridge.service (Serial-Port-Konflikt)
    eb_status = run_cmd("systemctl is-active embedded-bridge.service 2>/dev/null")
    data["embedded_bridge_active"] = eb_status == "active" if eb_status else None

    # Serial-Port-Lock
    lock_file = "/var/lock/esp32-serial.lock"
    data["serial_lock_exists"] = os.path.exists(lock_file)

    return data


def collect_software():
    """Sammelt Betriebssystem- und Software-Informationen."""
    data = {}

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
    toolchain_bins = sorted(pio_home.glob(
        "packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-gcc"
    ))
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


# ===========================================================================
# Terminal-Ausgabe
# ===========================================================================

def print_system_resources(data):
    """Gibt Sektion 1: Systemressourcen aus."""
    print_header("1. Systemressourcen und thermischer Zustand")

    # Temperatur
    temp = data.get("temperature_c")
    if temp is not None:
        if temp >= 80:
            print_fail("CPU-Temperatur", f"{temp:.1f} degC (KRITISCH)")
        elif temp >= 70:
            print_warn("CPU-Temperatur", f"{temp:.1f} degC (hoch)")
        else:
            print_info("CPU-Temperatur", f"{temp:.1f} degC")
    else:
        print_warn("CPU-Temperatur", "nicht lesbar")

    # Throttling
    throttle = data.get("throttle_hex")
    if throttle is not None:
        if throttle == "0x0":
            print_info("Throttle-Status", f"{throttle} (keine Einschraenkungen)")
        else:
            flags = data.get("throttle_flags", [])
            print_warn("Throttle-Status", f"{throttle}")
            for flag in flags:
                print_warn(f"  -> {flag}")
    else:
        print_warn("Throttle-Status", "vcgencmd nicht verfuegbar")

    # CPU
    freqs = data.get("cpu_freq_mhz", [])
    cpu_count = data.get("cpu_count", "?")
    if freqs:
        avg_freq = sum(freqs) / len(freqs)
        print_info("CPU", f"{cpu_count} Kerne @ {avg_freq:.0f} MHz (aktuell)")
    else:
        print_info("CPU", f"{cpu_count} Kerne")

    model = data.get("cpu_model")
    if model:
        print_info("CPU-Modell", model)

    # Load
    load_1 = data.get("load_1m")
    if load_1 is not None:
        load_str = f"{data['load_1m']:.2f} / {data['load_5m']:.2f} / {data['load_15m']:.2f}"
        if load_1 > cpu_count if isinstance(cpu_count, int) else False:
            print_warn("Load Average (1/5/15 min)", load_str)
        else:
            print_info("Load Average (1/5/15 min)", load_str)

    # RAM
    ram_total = data.get("ram_total_mb")
    if ram_total:
        ram_used = data.get("ram_used_mb", 0)
        ram_pct = data.get("ram_usage_pct", 0)
        if ram_pct >= 90:
            print_warn("RAM", f"{ram_used} / {ram_total} MB ({ram_pct}%)")
        else:
            print_info("RAM", f"{ram_used} / {ram_total} MB ({ram_pct}%)")

    # Disk
    disk_total = data.get("disk_total_gb")
    if disk_total:
        disk_used = data.get("disk_used_gb", 0)
        disk_pct = data.get("disk_usage_pct", 0)
        if disk_pct >= 90:
            print_warn("Disk (/)", f"{disk_used} / {disk_total} GB ({disk_pct}%)")
        else:
            print_info("Disk (/)", f"{disk_used} / {disk_total} GB ({disk_pct}%)")


def print_peripherals(data):
    """Gibt Sektion 2: AMR-Peripherie aus."""
    print_header("2. AMR-Peripherie und Schnittstellen")

    # ESP32
    if data.get("esp32_found"):
        print_info("ESP32-S3", "erkannt (303a:1001)")
    else:
        print_fail("ESP32-S3", "NICHT erkannt (303a:1001)")

    # RPLIDAR
    if data.get("rplidar_found"):
        print_info("RPLIDAR (CP210x)", "erkannt (10c4:ea60)")
    else:
        print_warn("RPLIDAR (CP210x)", "nicht erkannt (10c4:ea60)")

    # Serial-Devices
    acm = data.get("tty_acm", [])
    usb = data.get("tty_usb", [])
    if acm:
        print_info("Serial ttyACM", ", ".join(acm))
    else:
        print_warn("Serial ttyACM", "keine Geraete")
    if usb:
        print_info("Serial ttyUSB", ", ".join(usb))

    # udev-Symlinks
    by_id = data.get("serial_by_id", [])
    if by_id:
        for link in by_id:
            target = os.path.realpath(link)
            name = os.path.basename(link)
            print_info(f"  {name}", f"-> {target}")

    # Kamera
    cam = data.get("camera", {})
    if cam.get("detected"):
        print_info("CSI-Kamera", f"erkannt ({cam.get('tool', '?')})")
        for sensor_line in cam.get("sensors", [])[:5]:
            print_info(f"  {sensor_line}")
    else:
        print_warn("CSI-Kamera", "nicht erkannt")

    # v4l2loopback
    if data.get("v4l2loopback_present"):
        print_info("/dev/video10 (v4l2loopback)", "vorhanden")
    else:
        print_warn("/dev/video10 (v4l2loopback)", "nicht vorhanden")

    # Camera-Bridge
    bridge = data.get("camera_bridge_active")
    if bridge is True:
        print_info("camera-v4l2-bridge.service", "active")
    elif bridge is False:
        print_warn("camera-v4l2-bridge.service", "inactive")
    else:
        print_warn("camera-v4l2-bridge.service", "nicht installiert")

    # PCIe / Hailo
    if data.get("hailo_found"):
        for d in data.get("pcie_devices", []):
            if "identified" in d:
                print_info("Hailo-8 (PCIe)", d["raw"])
    else:
        hailo_found_via_pcie = False
        for d in data.get("pcie_devices", []):
            if "hailo" in d.get("raw", "").lower():
                hailo_found_via_pcie = True
        if not hailo_found_via_pcie:
            print_warn("Hailo-8 (PCIe)", "nicht erkannt")

    # Serial-Port-Konflikte
    eb = data.get("embedded_bridge_active")
    if eb is True:
        print_warn("embedded-bridge.service", "AKTIV (blockiert Serial-Port fuer micro-ROS!)")
    elif eb is False:
        print_info("embedded-bridge.service", "inactive (OK)")
    # Lock
    if data.get("serial_lock_exists"):
        print_warn("Serial-Lock", "/var/lock/esp32-serial.lock existiert")


def print_software(data):
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


# ===========================================================================
# Export-Formate
# ===========================================================================

def generate_markdown(system, peripherals, software):
    """Erzeugt einen Markdown-Report."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# AMR Hardware-Info Report")
    lines.append(f"")
    lines.append(f"**Zeitpunkt:** {ts}")
    lines.append(f"")

    # Sektion 1
    lines.append("## 1. Systemressourcen und thermischer Zustand")
    lines.append("")
    lines.append("| Parameter | Wert |")
    lines.append("|---|---|")

    model = software.get("pi_model", "-")
    if model:
        lines.append(f"| Hardware | {model} |")

    temp = system.get("temperature_c")
    lines.append(f"| CPU-Temperatur | {temp:.1f} degC |" if temp else "| CPU-Temperatur | - |")

    throttle = system.get("throttle_hex", "-")
    lines.append(f"| Throttle-Status | {throttle} |")

    cpu_count = system.get("cpu_count", "?")
    freqs = system.get("cpu_freq_mhz", [])
    avg_freq = f"{sum(freqs)/len(freqs):.0f} MHz" if freqs else "-"
    lines.append(f"| CPU | {cpu_count} Kerne @ {avg_freq} |")

    load_1 = system.get("load_1m")
    if load_1 is not None:
        lines.append(f"| Load Average | {system['load_1m']:.2f} / {system['load_5m']:.2f} / {system['load_15m']:.2f} |")

    ram = system.get("ram_total_mb")
    if ram:
        lines.append(f"| RAM | {system['ram_used_mb']} / {ram} MB ({system['ram_usage_pct']}%) |")

    disk = system.get("disk_total_gb")
    if disk:
        lines.append(f"| Disk (/) | {system['disk_used_gb']} / {disk} GB ({system['disk_usage_pct']}%) |")

    uptime = software.get("uptime")
    if uptime:
        lines.append(f"| Uptime | {uptime} |")

    lines.append("")

    # Sektion 2
    lines.append("## 2. AMR-Peripherie und Schnittstellen")
    lines.append("")
    lines.append("| Komponente | Status | Details |")
    lines.append("|---|---|---|")

    esp_status = "erkannt" if peripherals.get("esp32_found") else "NICHT erkannt"
    lines.append(f"| ESP32-S3 (303a:1001) | {esp_status} | {', '.join(peripherals.get('tty_acm', ['-']))} |")

    rp_status = "erkannt" if peripherals.get("rplidar_found") else "nicht erkannt"
    lines.append(f"| RPLIDAR CP210x (10c4:ea60) | {rp_status} | {', '.join(peripherals.get('tty_usb', ['-']))} |")

    cam = peripherals.get("camera", {})
    cam_status = "erkannt" if cam.get("detected") else "nicht erkannt"
    lines.append(f"| CSI-Kamera | {cam_status} | {cam.get('tool', '-')} |")

    v4l2 = "vorhanden" if peripherals.get("v4l2loopback_present") else "nicht vorhanden"
    lines.append(f"| /dev/video10 (v4l2loopback) | {v4l2} | - |")

    bridge = peripherals.get("camera_bridge_active")
    bridge_str = "active" if bridge is True else ("inactive" if bridge is False else "nicht installiert")
    lines.append(f"| camera-v4l2-bridge | {bridge_str} | systemd service |")

    hailo = "erkannt" if peripherals.get("hailo_found") else "nicht erkannt"
    lines.append(f"| Hailo-8 (PCIe) | {hailo} | - |")

    eb = peripherals.get("embedded_bridge_active")
    eb_str = "AKTIV (Konflikt!)" if eb is True else ("inactive" if eb is False else "-")
    lines.append(f"| embedded-bridge.service | {eb_str} | Serial-Port-Konflikt |")

    lines.append("")

    # Sektion 3
    lines.append("## 3. Betriebssystem und Software")
    lines.append("")
    lines.append("| Komponente | Version |")
    lines.append("|---|---|")
    lines.append(f"| OS | {software.get('os_name', '-')} |")
    lines.append(f"| Kernel | {software.get('kernel', '-')} |")
    lines.append(f"| Architektur | {software.get('arch', '-')} |")
    lines.append(f"| Python | {software.get('python_version', '-')} |")
    lines.append(f"| Docker | {software.get('docker_version', '-') or '-'} |")
    lines.append(f"| Docker Compose | {software.get('docker_compose_version', '-') or '-'} |")
    lines.append(f"| C/C++ (System) | {software.get('gcc_version', '-') or '-'} |")
    lines.append(f"| PlatformIO | {software.get('platformio_version', '-') or '-'} |")
    lines.append(f"| ESP32-S3 Toolchain | {software.get('esp32_gcc_version', '-') or '-'} |")

    packages = software.get("packages", {})
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


def generate_json(system, peripherals, software):
    """Erzeugt JSON-Report."""
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system_resources": system,
        "peripherals": peripherals,
        "software": software,
    }
    # raw_output kann sehr lang sein, rausnehmen
    if "camera" in report["peripherals"]:
        report["peripherals"]["camera"].pop("raw_output", None)
    # USB raw-Eintraege bereinigen
    for dev in report["peripherals"].get("usb_devices", []):
        dev.pop("raw", None)
    for dev in report["peripherals"].get("pcie_devices", []):
        dev.pop("raw", None)
    return json.dumps(report, indent=2, ensure_ascii=False)


# ===========================================================================
# Hauptprogramm
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Hardware-Info fuer Raspberry Pi 5 und AMR-Peripherie"
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Markdown-Report als Datei speichern"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="JSON-Ausgabe statt Terminal-Report"
    )
    args = parser.parse_args()

    # Daten sammeln
    system = collect_system_resources()
    peripherals = collect_peripherals()
    software = collect_software()

    # JSON-Modus
    if args.json:
        print(generate_json(system, peripherals, software))
        return 0

    # Terminal-Ausgabe
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print(f"{COLOR_BOLD}{'*' * 60}")
    print(f"  AMR Hardware-Info Report")
    print(f"  Raspberry Pi 5 + ESP32-S3 + RPLIDAR + IMX296")
    print(f"  {ts}")
    print(f"{'*' * 60}{COLOR_RESET}")

    print_system_resources(system)
    print_peripherals(peripherals)
    print_software(software)

    print()

    # Markdown speichern
    if args.save:
        md = generate_markdown(system, peripherals, software)
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
