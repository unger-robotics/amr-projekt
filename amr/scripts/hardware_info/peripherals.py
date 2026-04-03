"""Sektion 2: AMR-Peripherie und Schnittstellen."""

import contextlib
import os
import re
import subprocess
from glob import glob
from pathlib import Path
from typing import Any

from utils import (
    COLOR_CYAN,
    COLOR_RESET,
    print_fail,
    print_header,
    print_info,
    print_warn,
    run_cmd,
)

__all__ = [
    "get_esp32_chip_data",
    "collect_peripherals",
    "print_peripherals",
    "generate_peripherals_markdown",
]


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
            "2886:0018": "ReSpeaker Mic Array v2.0 (XMOS XVF-3000)",
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
    data["respeaker_found"] = any(d.get("vid_pid") == "2886:0018" for d in usb_devices)

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

    # udev-Symlinks (stabile Geraete-Pfade, Zwei-Node-Architektur)
    serial_by_id = sorted(glob("/dev/serial/by-id/*"))
    data["serial_by_id"] = serial_by_id
    data["amr_drive_found"] = os.path.exists("/dev/amr_drive")
    data["amr_sensor_found"] = os.path.exists("/dev/amr_sensor")

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

    # Hailo-8 Details (wenn erkannt)
    hailo_details: dict[str, Any] = {}
    if data["hailo_found"]:
        fw_output = run_cmd("hailortcli fw-control identify 2>/dev/null", timeout=10)
        if fw_output:
            hailo_details["fw_info"] = fw_output.strip()
        hailort_ver = run_cmd(
            'python3 -c "import hailo_platform; print(hailo_platform.__version__)" 2>/dev/null'
        )
        if hailort_ver:
            hailo_details["hailort_version"] = hailort_ver.strip()
    data["hailo_details"] = hailo_details

    # Netzwerk-Interfaces
    network_info: dict[str, Any] = {"interfaces": [], "hostname": ""}
    hostname_output = run_cmd("hostname -I")
    if hostname_output:
        network_info["hostname"] = hostname_output.strip()

    ip_output = run_cmd("ip -4 -o addr show")
    if ip_output:
        for line in ip_output.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                iface = parts[1]
                # Parse "inet x.x.x.x/mask"
                for i, p in enumerate(parts):
                    if p == "inet" and i + 1 < len(parts):
                        ip_cidr = parts[i + 1]
                        network_info["interfaces"].append({"name": iface, "ip": ip_cidr})

    # WiFi-Info (optional)
    wifi_output = run_cmd("iwconfig wlan0 2>/dev/null")
    if wifi_output:
        ssid_match = re.search(r'ESSID:"([^"]*)"', wifi_output)
        signal_match = re.search(r"Signal level=(-?\d+)", wifi_output)
        network_info["wifi_ssid"] = ssid_match.group(1) if ssid_match else None
        network_info["wifi_signal_dbm"] = int(signal_match.group(1)) if signal_match else None

    data["network"] = network_info

    # CAN-Bus (SocketCAN)
    can_info: dict[str, Any] = {"available": False}
    can_link = run_cmd("ip link show can0 2>/dev/null")
    if can_link:
        can_info["available"] = True
        can_info["up"] = "UP" in can_link and "DOWN" not in can_link
        bitrate_match = re.search(r"bitrate (\d+)", can_link)
        if bitrate_match:
            can_info["bitrate"] = int(bitrate_match.group(1))
        # Statistiken
        for stat_name in [
            "rx_frames",
            "tx_frames",
            "rx_errors",
            "tx_errors",
            "bus_errors",
        ]:
            stat_path = f"/sys/class/net/can0/statistics/{stat_name}"
            with contextlib.suppress(Exception):
                can_info[stat_name] = int(Path(stat_path).read_text().strip())
    data["can_bus"] = can_info

    # Audio (ALSA)
    audio_info: dict[str, Any] = {"cards": []}
    aplay_output = run_cmd("aplay -l 2>/dev/null")
    if aplay_output:
        for line in aplay_output.splitlines():
            if line.startswith("card "):
                audio_info["cards"].append(line.strip())
    data["audio"] = audio_info

    # embedded-bridge.service (Serial-Port-Konflikt)
    eb_status = run_cmd("systemctl is-active embedded-bridge.service 2>/dev/null")
    data["embedded_bridge_active"] = eb_status == "active" if eb_status else None

    # Serial-Port-Lock
    lock_file = "/var/lock/esp32-serial.lock"
    data["serial_lock_exists"] = os.path.exists(lock_file)

    return data


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

    # udev-Symlinks (Zwei-Node-Architektur)
    if data.get("amr_drive_found"):
        print_info("/dev/amr_drive", f"-> {os.path.realpath('/dev/amr_drive')}")
    else:
        print_warn("/dev/amr_drive", "nicht vorhanden (udev-Regel konfiguriert?)")
    if data.get("amr_sensor_found"):
        print_info("/dev/amr_sensor", f"-> {os.path.realpath('/dev/amr_sensor')}")
    else:
        print_warn("/dev/amr_sensor", "nicht vorhanden (udev-Regel konfiguriert?)")

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

    # Hailo-8 Details
    hailo_det = data.get("hailo_details", {})
    if hailo_det.get("hailort_version"):
        print_info("  HailoRT Version", hailo_det["hailort_version"])
    if hailo_det.get("fw_info"):
        for line in hailo_det["fw_info"].splitlines()[:3]:
            print_info(f"  {line.strip()}")

    # Netzwerk
    net = data.get("network", {})
    interfaces = net.get("interfaces", [])
    if interfaces:
        print()
        print(f"  {COLOR_CYAN}--- Netzwerk ---{COLOR_RESET}")
        for iface in interfaces:
            print_info(f"  {iface['name']}", iface["ip"])
        wifi_ssid = net.get("wifi_ssid")
        if wifi_ssid:
            signal = net.get("wifi_signal_dbm", "?")
            print_info("  WiFi SSID", f"{wifi_ssid} ({signal} dBm)")
    elif net.get("hostname"):
        print()
        print_info("IP-Adressen", net["hostname"])

    # CAN-Bus
    can = data.get("can_bus", {})
    if can.get("available"):
        print()
        print(f"  {COLOR_CYAN}--- CAN-Bus ---{COLOR_RESET}")
        status = "UP" if can.get("up") else "DOWN"
        bitrate = can.get("bitrate", "?")
        print_info("can0 Status", f"{status}, {bitrate} bit/s")
        rx = can.get("rx_frames", 0)
        tx = can.get("tx_frames", 0)
        errors = can.get("bus_errors", 0)
        print_info("Frames", f"RX={rx}, TX={tx}, Bus-Errors={errors}")

    # ReSpeaker
    if data.get("respeaker_found"):
        print_info("ReSpeaker Mic Array v2.0", "erkannt (USB 2886:0018)")

    # Audio
    audio = data.get("audio", {})
    audio_cards = audio.get("cards", [])
    if audio_cards:
        print()
        print(f"  {COLOR_CYAN}--- Audio ---{COLOR_RESET}")
        for card in audio_cards:
            print_info(f"  {card}")

    # Serial-Port-Konflikte
    eb = data.get("embedded_bridge_active")
    if eb is True:
        print_warn("embedded-bridge.service", "AKTIV (blockiert Serial-Port fuer micro-ROS!)")
    elif eb is False:
        print_info("embedded-bridge.service", "inactive (OK)")
    # Lock
    if data.get("serial_lock_exists"):
        print_warn("Serial-Lock", "/var/lock/esp32-serial.lock existiert")


def generate_peripherals_markdown(data):
    """Erzeugt Sektion-2-Markdown fuer AMR-Peripherie und Schnittstellen."""
    lines = []
    lines.append("## 2. AMR-Peripherie und Schnittstellen")
    lines.append("")
    lines.append("| Komponente | Status | Details |")
    lines.append("|---|---|---|")

    esp_status = "erkannt" if data.get("esp32_found") else "NICHT erkannt"

    # Chip Info formatieren
    chip_details = ""
    chip_info = data.get("esp32_chip_info")
    if chip_info and "error" not in chip_info:
        mac = chip_info.get("mac_address", "?")
        flash = chip_info.get("flash_size", "?")
        chip_details = f" (MAC: {mac}, Flash: {flash})"

    lines.append(
        f"| ESP32-S3 (303a:1001) | {esp_status}{chip_details} | {', '.join(data.get('tty_acm', ['-']))} |"
    )

    rp_status = "erkannt" if data.get("rplidar_found") else "nicht erkannt"
    lines.append(
        f"| RPLIDAR CP210x (10c4:ea60) | {rp_status} | {', '.join(data.get('tty_usb', ['-']))} |"
    )

    cam = data.get("camera", {})
    cam_status = "erkannt" if cam.get("detected") else "nicht erkannt"
    lines.append(f"| CSI-Kamera | {cam_status} | {cam.get('tool', '-')} |")

    v4l2 = "vorhanden" if data.get("v4l2loopback_present") else "nicht vorhanden"
    lines.append(f"| /dev/video10 (v4l2loopback) | {v4l2} | - |")

    bridge = data.get("camera_bridge_active")
    bridge_str = (
        "active" if bridge is True else ("inactive" if bridge is False else "nicht installiert")
    )
    lines.append(f"| camera-v4l2-bridge | {bridge_str} | systemd service |")

    hailo = "erkannt" if data.get("hailo_found") else "nicht erkannt"
    lines.append(f"| Hailo-8 (PCIe) | {hailo} | - |")

    # Hailo-8 Details
    hailo_det = data.get("hailo_details", {})
    hailo_detail_parts = []
    if hailo_det.get("hailort_version"):
        hailo_detail_parts.append(f"HailoRT {hailo_det['hailort_version']}")
    if hailo_det.get("fw_info"):
        fw_first_line = hailo_det["fw_info"].splitlines()[0].strip()
        hailo_detail_parts.append(fw_first_line)
    if hailo_detail_parts:
        lines.append(f"| Hailo-8 Details | {' / '.join(hailo_detail_parts)} | - |")

    # Netzwerk-Tabelle
    net = data.get("network", {})
    net_interfaces = net.get("interfaces", [])
    if net_interfaces:
        lines.append("")
        lines.append("### Netzwerk")
        lines.append("")
        lines.append("| Interface | IP-Adresse |")
        lines.append("|-----------|-----------|")
        for iface in net_interfaces:
            lines.append(f"| {iface['name']} | {iface['ip']} |")
        wifi_ssid = net.get("wifi_ssid")
        if wifi_ssid:
            signal = net.get("wifi_signal_dbm", "?")
            lines.append("")
            lines.append(f"WiFi: {wifi_ssid} ({signal} dBm)")
        lines.append("")

    # CAN-Bus
    can = data.get("can_bus", {})
    if can.get("available"):
        lines.append("### CAN-Bus")
        lines.append("")
        can_status = "UP" if can.get("up") else "DOWN"
        can_bitrate = can.get("bitrate", "?")
        lines.append(f"- Status: {can_status}, {can_bitrate} bit/s")
        rx = can.get("rx_frames", 0)
        tx = can.get("tx_frames", 0)
        errors = can.get("bus_errors", 0)
        lines.append(f"- Frames: RX={rx}, TX={tx}, Bus-Errors={errors}")
        lines.append("")

    # ReSpeaker
    if data.get("respeaker_found"):
        lines.append("| ReSpeaker Mic Array v2.0 | erkannt | USB 2886:0018 (XMOS XVF-3000) |")

    # Audio
    audio = data.get("audio", {})
    audio_cards = audio.get("cards", [])
    if audio_cards:
        lines.append("")
        lines.append("### Audio")
        lines.append("")
        for card in audio_cards:
            lines.append(f"- {card}")
        lines.append("")

    eb = data.get("embedded_bridge_active")
    eb_str = "AKTIV (Konflikt!)" if eb is True else ("inactive" if eb is False else "-")
    lines.append(f"| embedded-bridge.service | {eb_str} | Serial-Port-Konflikt |")

    lines.append("")

    return "\n".join(lines)
