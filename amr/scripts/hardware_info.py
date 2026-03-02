#!/usr/bin/env python3
"""
Hardware-Info-Skript fuer Raspberry Pi 5 und AMR-Peripherie.
Erfasst den Hardware-Zustand aller Komponenten und gibt einen
formatierten Report aus. Kein ROS2 erforderlich.
pip3 install esptool
Ausgabe: Terminal (farbkodiert), optional Markdown (--save) oder JSON (--json).

Erfasste Daten:
  1. Systemressourcen (CPU, RAM, Disk, Temperatur, Throttling)
  2. AMR-Peripherie (ESP32, RPLIDAR, Kamera, Hailo, Serial-Ports)
  3. Betriebssystem und Software (OS, Docker, PlatformIO, Toolchains)
  4. Projekt-Info (Git, Docker-Image, PlatformIO-Plattform, Boot-Config, config.h)
"""

import argparse
import contextlib
import datetime
import json
import os
import platform
import re
import subprocess
import sys
from glob import glob
from pathlib import Path
from typing import Any

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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


# ===========================================================================
# Datensammlung
# ===========================================================================


def get_esp32_chip_data(port="/dev/ttyACM0", baudrate=115200):
    """
    Fragt hardwarenahe Daten des ESP32 ueber den ROM-Bootloader ab.
    Gibt ein Dictionary mit den geparsten Parametern zurueck.
    """
    cmd = ["esptool", "--port", port, "--baud", str(baudrate), "flash_id"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout

        if result.returncode != 0:
            # Pruefung auf fehlende Berechtigungen oder blockierten Port
            if "Permission denied" in result.stderr:
                return {"error": f"Zugriff verweigert auf {port}. 'dialout' Gruppe pruefen."}
            return {"error": "esptool fehlgeschlagen (Port blockiert oder Modul offline)."}

        chip_info = {
            "port": port,
            "chip_type": None,
            "mac_address": None,
            "features": None,
            "flash_size": None,
        }

        patterns = {
            "chip_type": r"Detecting chip type\.\.\.\s*(.+)",
            "mac_address": r"MAC:\s*([0-9a-fA-F:]+)",
            "features": r"Features:\s*(.+)",
            "flash_size": r"Detected flash size:\s*(.+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                chip_info[key] = match.group(1).strip()

        return chip_info

    except FileNotFoundError:
        return {"error": "esptool.py nicht gefunden. Installation via 'pip install esptool'."}
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout an Port {port}. Chip antwortet nicht."}


def collect_system_resources():
    """Sammelt Systemressourcen und thermischen Zustand."""
    data: dict[str, Any] = {}

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
                with contextlib.suppress(ValueError):
                    mem[key.strip()] = int(val)
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
        data["disk_total_gb"] = round(total_bytes / (1024**3), 1)
        data["disk_used_gb"] = round(used_bytes / (1024**3), 1)
        data["disk_free_gb"] = round(free_bytes / (1024**3), 1)
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
    data: dict[str, Any] = {}

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

    data["esp32_found"] = any(d.get("vid_pid") == "303a:1001" for d in usb_devices)
    data["rplidar_found"] = any(d.get("vid_pid") == "10c4:ea60" for d in usb_devices)

    # Serial-Devices
    acm_devices = sorted(glob("/dev/ttyACM*"))
    usb_serial = sorted(glob("/dev/ttyUSB*"))
    data["tty_acm"] = acm_devices
    data["tty_usb"] = usb_serial

    # Hardwarenahe ESP32 Daten via esptool auslesen
    data["esp32_chip_info"] = None
    if data["esp32_found"] and acm_devices:
        target_port = acm_devices[0]  # Nutze ersten ACM-Port als Annahme
        data["esp32_chip_info"] = get_esp32_chip_data(target_port)

    # udev-Symlinks (stabile Geraete-Pfade)
    serial_by_id = sorted(glob("/dev/serial/by-id/*"))
    data["serial_by_id"] = serial_by_id

    # Kamera (rpicam-hello / libcamera-hello)
    cam_data: dict[str, Any] = {"detected": False, "sensors": []}
    for cam_cmd in ["rpicam-hello --list-cameras", "libcamera-hello --list-cameras"]:
        cam_output = run_cmd(cam_cmd, timeout=10)
        if cam_output:
            cam_data["detected"] = True
            cam_data["tool"] = cam_cmd.split()[0]
            # Sensor-Info parsen
            for line in cam_output.splitlines():
                stripped = line.strip()
                if (
                    stripped
                    and (":" in stripped)
                    and any(s in stripped.lower() for s in ["imx", "ov", "sensor", "mode"])
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


def collect_project_info():
    """Sammelt Projekt- und Reproduzierbarkeitsinformationen."""
    data: dict[str, Any] = {}

    # --- Git-Info ---
    git_hash = run_cmd("git rev-parse --short HEAD 2>/dev/null")
    data["git_commit"] = git_hash
    data["git_branch"] = run_cmd("git rev-parse --abbrev-ref HEAD 2>/dev/null")
    data["git_dirty"] = run_cmd("git status --porcelain 2>/dev/null") not in (None, "")
    if git_hash:
        data["git_commit_date"] = run_cmd(f"git log -1 --format=%ci {git_hash} 2>/dev/null")

    # --- Docker-Image-Info ---
    docker_image = run_cmd(
        "docker images amr-ros2-humble --format '{{.Repository}}:{{.Tag}}  {{.Size}}  {{.CreatedAt}}' 2>/dev/null"
    )
    if docker_image:
        data["docker_image_info"] = docker_image.splitlines()[0].strip()
    else:
        data["docker_image_info"] = None

    # ROS2-Pakete im Docker-Container (nur wenn Container laeuft)
    ros2_pkgs_raw = run_cmd(
        "docker exec amr-docker-ros2-humble-1 "
        "bash -c 'dpkg -l ros-humble-* 2>/dev/null | grep ^ii' 2>/dev/null",
        timeout=10,
    )
    ros2_packages = {}
    if ros2_pkgs_raw:
        key_packages = [
            "nav2-bringup",
            "nav2-regulated-pure-pursuit-controller",
            "slam-toolbox",
            "rplidar-ros",
            "cv-bridge",
            "v4l2-camera",
        ]
        for line in ros2_pkgs_raw.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                pkg_name = parts[1].replace("ros-humble-", "")
                pkg_ver = parts[2]
                if any(k in pkg_name for k in key_packages):
                    ros2_packages[pkg_name] = pkg_ver
    data["ros2_packages"] = ros2_packages

    # --- PlatformIO-Plattform-Details ---
    # pio pkg list muss im Firmware-Verzeichnis (mit platformio.ini) laufen
    firmware_dir = _find_firmware_dir()
    if firmware_dir:
        pio_pkg_raw = run_cmd(
            f"cd {firmware_dir} && pio pkg list --only-platforms 2>/dev/null", timeout=15
        )
        if pio_pkg_raw:
            for line in pio_pkg_raw.splitlines():
                if "espressif32" in line.lower() and "@" in line:
                    data["pio_platform"] = line.strip()
                    break
            else:
                data["pio_platform"] = None
        else:
            data["pio_platform"] = None
    else:
        data["pio_platform"] = None

    # esptool Version
    esptool_ver = run_cmd("esptool version 2>/dev/null")
    if esptool_ver:
        for line in esptool_ver.splitlines():
            if "esptool" in line.lower() and ("v" in line or "." in line):
                data["esptool_version"] = line.strip()
                break
        else:
            data["esptool_version"] = None
    else:
        data["esptool_version"] = None

    # --- Boot-Config (dtoverlay) ---
    boot_overlays = []
    try:
        config_txt = Path("/boot/firmware/config.txt").read_text()
        for line in config_txt.splitlines():
            stripped = line.strip()
            if stripped.startswith("dtoverlay=") or stripped.startswith("dtparam="):
                boot_overlays.append(stripped)
    except FileNotFoundError:
        pass
    data["boot_overlays"] = boot_overlays

    # --- config.h Parameter (Single Source of Truth) ---
    config_h_params = {}
    config_h_path = _find_config_h()
    data["config_h_path"] = str(config_h_path) if config_h_path else None
    if config_h_path:
        try:
            content = config_h_path.read_text()
            # Key #define Werte extrahieren
            define_patterns = {
                "WHEEL_DIAMETER": r"#define\s+WHEEL_DIAMETER\s+([\d.]+f?)",
                "WHEEL_BASE": r"#define\s+WHEEL_BASE\s+([\d.]+f?)",
                "TICKS_PER_REV_LEFT": r"#define\s+TICKS_PER_REV_LEFT\s+([\d.]+f?)",
                "TICKS_PER_REV_RIGHT": r"#define\s+TICKS_PER_REV_RIGHT\s+([\d.]+f?)",
                "PWM_DEADZONE": r"#define\s+PWM_DEADZONE\s+(\d+)",
                "FAILSAFE_TIMEOUT_MS": r"#define\s+FAILSAFE_TIMEOUT_MS\s+(\d+)",
                "CONTROL_LOOP_HZ": r"#define\s+CONTROL_LOOP_HZ\s+(\d+)",
                "ODOM_PUBLISH_HZ": r"#define\s+ODOM_PUBLISH_HZ\s+(\d+)",
                "IMU_PUBLISH_HZ": r"#define\s+IMU_PUBLISH_HZ\s+(\d+)",
                "IMU_CALIBRATION_SAMPLES": r"#define\s+IMU_CALIBRATION_SAMPLES\s+(\d+)",
                "IMU_COMPLEMENTARY_ALPHA": r"#define\s+IMU_COMPLEMENTARY_ALPHA\s+([\d.]+f?)",
            }
            for key, pattern in define_patterns.items():
                match = re.search(pattern, content)
                if match:
                    config_h_params[key] = match.group(1).rstrip("f")
        except (FileNotFoundError, PermissionError):
            pass
    data["config_h_params"] = config_h_params

    return data


def _find_config_h():
    """Sucht config.h relativ zum Skript-Verzeichnis oder im Projektbaum."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "../../hardware/config.h",  # amr/scripts/ -> hardware/
        script_dir / "../../../hardware/config.h",  # my_bot/my_bot/ -> hardware/
        Path.home() / "AMR-Bachelorarbeit/hardware/config.h",
    ]
    for c in candidates:
        resolved = c.resolve()
        if resolved.is_file():
            return resolved
    return None


def _find_firmware_dir():
    """Sucht das ESP32-Firmware-Verzeichnis (mit platformio.ini)."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "../esp32_amr_firmware",  # amr/scripts/ -> amr/esp32_amr_firmware/
        script_dir / "../../amr/esp32_amr_firmware",  # my_bot/my_bot/ -> amr/esp32_amr_firmware/
        Path.home() / "AMR-Bachelorarbeit/amr/esp32_amr_firmware",
    ]
    for c in candidates:
        resolved = c.resolve()
        if (resolved / "platformio.ini").is_file():
            return resolved
    return None


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
        chip_info = data.get("esp32_chip_info")
        if chip_info:
            if "error" in chip_info:
                print_warn("ESP32 Chip-Daten", chip_info["error"])
            else:
                print_info("  MAC-Adresse", chip_info.get("mac_address", "?"))
                print_info("  Flash-Speicher", chip_info.get("flash_size", "?"))
                print_info("  Features", chip_info.get("features", "?"))
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


def print_project_info(data):
    """Gibt Sektion 4: Projekt- und Reproduzierbarkeitsinformationen aus."""
    print_header("4. Projekt und Reproduzierbarkeit")

    # Git
    commit = data.get("git_commit")
    if commit:
        branch = data.get("git_branch", "?")
        dirty = " (uncommitted changes)" if data.get("git_dirty") else ""
        print_info("Git", f"{branch} @ {commit}{dirty}")
        commit_date = data.get("git_commit_date")
        if commit_date:
            print_info("  Commit-Datum", commit_date)
    else:
        print_warn("Git", "kein Repository erkannt")

    # Docker-Image
    docker_img = data.get("docker_image_info")
    if docker_img:
        print_info("Docker-Image", docker_img)
    else:
        print_warn("Docker-Image", "amr-ros2-humble nicht gefunden")

    # ROS2-Pakete
    ros2_pkgs = data.get("ros2_packages", {})
    if ros2_pkgs:
        print()
        print(f"  {COLOR_CYAN}ROS2-Pakete im Container:{COLOR_RESET}")
        for pkg, ver in sorted(ros2_pkgs.items()):
            print_info(f"  {pkg}", ver)
    else:
        print_warn("ROS2-Pakete", "Container nicht aktiv oder nicht erreichbar")

    # PlatformIO-Plattform
    pio_plat = data.get("pio_platform")
    if pio_plat:
        print_info("PlatformIO-Plattform", pio_plat)

    esptool = data.get("esptool_version")
    if esptool:
        print_info("esptool", esptool)

    # Boot-Config
    overlays = data.get("boot_overlays", [])
    if overlays:
        print()
        print(f"  {COLOR_CYAN}Boot-Konfiguration:{COLOR_RESET}")
        for ov in overlays:
            print_info(f"  {ov}")
    else:
        print_warn("Boot-Konfiguration", "/boot/firmware/config.txt nicht lesbar")

    # config.h
    params = data.get("config_h_params", {})
    if params:
        print()
        print(f"  {COLOR_CYAN}Firmware-Parameter (config.h):{COLOR_RESET}")
        # Formatierte Ausgabe der wichtigsten Parameter
        param_labels = {
            "WHEEL_DIAMETER": ("Raddurchmesser", "m"),
            "WHEEL_BASE": ("Spurbreite", "m"),
            "TICKS_PER_REV_LEFT": ("Ticks/Rev links", ""),
            "TICKS_PER_REV_RIGHT": ("Ticks/Rev rechts", ""),
            "PWM_DEADZONE": ("PWM-Deadzone", ""),
            "FAILSAFE_TIMEOUT_MS": ("Failsafe-Timeout", "ms"),
            "CONTROL_LOOP_HZ": ("Regelfrequenz", "Hz"),
            "ODOM_PUBLISH_HZ": ("Odom-Rate", "Hz"),
            "IMU_PUBLISH_HZ": ("IMU-Rate", "Hz"),
            "IMU_CALIBRATION_SAMPLES": ("IMU-Kalibr.-Samples", ""),
            "IMU_COMPLEMENTARY_ALPHA": ("Complementary alpha", ""),
        }
        for key, (label, unit) in param_labels.items():
            val = params.get(key)
            if val:
                suffix = f" {unit}" if unit else ""
                print_info(f"  {label}", f"{val}{suffix}")
    else:
        print_warn("config.h", "nicht gefunden")


# ===========================================================================
# Export-Formate
# ===========================================================================


def generate_markdown(system, peripherals, software, project=None):
    """Erzeugt einen Markdown-Report."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# AMR Hardware-Info Report")
    lines.append("")
    lines.append(f"**Zeitpunkt:** {ts}")
    lines.append("")

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
    avg_freq = f"{sum(freqs) / len(freqs):.0f} MHz" if freqs else "-"
    lines.append(f"| CPU | {cpu_count} Kerne @ {avg_freq} |")

    load_1 = system.get("load_1m")
    if load_1 is not None:
        lines.append(
            f"| Load Average | {system['load_1m']:.2f} / {system['load_5m']:.2f} / {system['load_15m']:.2f} |"
        )

    ram = system.get("ram_total_mb")
    if ram:
        lines.append(f"| RAM | {system['ram_used_mb']} / {ram} MB ({system['ram_usage_pct']}%) |")

    disk = system.get("disk_total_gb")
    if disk:
        lines.append(
            f"| Disk (/) | {system['disk_used_gb']} / {disk} GB ({system['disk_usage_pct']}%) |"
        )

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

    # Chip Info formatieren
    chip_details = ""
    chip_info = peripherals.get("esp32_chip_info")
    if chip_info and "error" not in chip_info:
        mac = chip_info.get("mac_address", "?")
        flash = chip_info.get("flash_size", "?")
        chip_details = f" (MAC: {mac}, Flash: {flash})"

    lines.append(
        f"| ESP32-S3 (303a:1001) | {esp_status}{chip_details} | {', '.join(peripherals.get('tty_acm', ['-']))} |"
    )

    rp_status = "erkannt" if peripherals.get("rplidar_found") else "nicht erkannt"
    lines.append(
        f"| RPLIDAR CP210x (10c4:ea60) | {rp_status} | {', '.join(peripherals.get('tty_usb', ['-']))} |"
    )

    cam = peripherals.get("camera", {})
    cam_status = "erkannt" if cam.get("detected") else "nicht erkannt"
    lines.append(f"| CSI-Kamera | {cam_status} | {cam.get('tool', '-')} |")

    v4l2 = "vorhanden" if peripherals.get("v4l2loopback_present") else "nicht vorhanden"
    lines.append(f"| /dev/video10 (v4l2loopback) | {v4l2} | - |")

    bridge = peripherals.get("camera_bridge_active")
    bridge_str = (
        "active" if bridge is True else ("inactive" if bridge is False else "nicht installiert")
    )
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

    # Sektion 4: Projekt und Reproduzierbarkeit
    if project:
        lines.append("## 4. Projekt und Reproduzierbarkeit")
        lines.append("")

        # Git
        commit = project.get("git_commit")
        if commit:
            branch = project.get("git_branch", "?")
            dirty = " (uncommitted)" if project.get("git_dirty") else ""
            lines.append(f"**Git:** `{branch}` @ `{commit}`{dirty}")
            commit_date = project.get("git_commit_date")
            if commit_date:
                lines.append(f"**Commit-Datum:** {commit_date}")
            lines.append("")

        # Docker-Image
        docker_img = project.get("docker_image_info")
        if docker_img:
            lines.append(f"**Docker-Image:** {docker_img}")
            lines.append("")

        # ROS2-Pakete
        ros2_pkgs = project.get("ros2_packages", {})
        if ros2_pkgs:
            lines.append("### ROS2-Pakete im Container")
            lines.append("")
            lines.append("| Paket | Version |")
            lines.append("|---|---|")
            for pkg, ver in sorted(ros2_pkgs.items()):
                lines.append(f"| {pkg} | {ver} |")
            lines.append("")

        # PlatformIO
        pio_plat = project.get("pio_platform")
        if pio_plat:
            lines.append(f"**PlatformIO-Plattform:** {pio_plat}")
        esptool = project.get("esptool_version")
        if esptool:
            lines.append(f"**esptool:** {esptool}")
        if pio_plat or esptool:
            lines.append("")

        # Boot-Config
        overlays = project.get("boot_overlays", [])
        if overlays:
            lines.append("### Boot-Konfiguration")
            lines.append("")
            lines.append("```")
            for ov in overlays:
                lines.append(ov)
            lines.append("```")
            lines.append("")

        # config.h
        params = project.get("config_h_params", {})
        if params:
            lines.append("### Firmware-Parameter (config.h)")
            lines.append("")
            lines.append("| Parameter | Wert |")
            lines.append("|---|---|")
            for key, val in params.items():
                lines.append(f"| {key} | {val} |")
            lines.append("")

    return "\n".join(lines)


def generate_json(system, peripherals, software, project=None):
    """Erzeugt JSON-Report."""
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system_resources": system,
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


# ===========================================================================
# Hauptprogramm
# ===========================================================================


def main():
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
