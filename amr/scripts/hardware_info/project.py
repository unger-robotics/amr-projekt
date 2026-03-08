"""Sektion 4: Projekt und Reproduzierbarkeit."""

import contextlib
import datetime
import os
import re
from pathlib import Path
from typing import Any

from utils import COLOR_CYAN, COLOR_RESET, print_header, print_info, print_warn, run_cmd

__all__ = ["collect_project_info", "print_project_info", "generate_project_markdown"]


def _find_config_h():
    """Sucht config_drive.h relativ zum Skript-Verzeichnis oder im Projektbaum."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir
        / "../../mcu_firmware/drive_node/include/config_drive.h",  # hardware_info/ -> amr/mcu_firmware/
        script_dir
        / "../../../mcu_firmware/drive_node/include/config_drive.h",  # my_bot/my_bot/hardware_info/ -> amr/mcu_firmware/
        Path.home() / "AMR-Bachelorarbeit/amr/mcu_firmware/drive_node/include/config_drive.h",
    ]
    for c in candidates:
        resolved = c.resolve()
        if resolved.is_file():
            return resolved
    return None


def _find_config_sensors_h():
    """Sucht config_sensors.h in bekannten Pfaden."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(
            script_dir, "..", "mcu_firmware", "sensor_node", "include", "config_sensors.h"
        ),
        os.path.join(
            script_dir,
            "..",
            "..",
            "amr",
            "mcu_firmware",
            "sensor_node",
            "include",
            "config_sensors.h",
        ),
    ]
    for c in candidates:
        p = os.path.normpath(c)
        if os.path.isfile(p):
            return p
    return None


def _find_firmware_dir():
    """Sucht das Drive-Node Firmware-Verzeichnis (mit platformio.ini)."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir
        / "../../mcu_firmware/drive_node",  # hardware_info/ -> amr/mcu_firmware/drive_node/
        script_dir
        / "../../../amr/mcu_firmware/drive_node",  # my_bot/my_bot/hardware_info/ -> amr/mcu_firmware/drive_node/
        Path.home() / "AMR-Bachelorarbeit/amr/mcu_firmware/drive_node",
    ]
    for c in candidates:
        resolved = c.resolve()
        if (resolved / "platformio.ini").is_file():
            return resolved
    return None


def collect_project_info() -> dict[str, Any]:
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

    # --- config_drive.h Parameter (Single Source of Truth) ---
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

    # --- config_sensors.h Parameter ---
    sensor_config_path = _find_config_sensors_h()
    sensor_params = {}
    if sensor_config_path:
        with contextlib.suppress(Exception):
            content = Path(sensor_config_path).read_text()
            patterns = {
                "imu_sample_hz": r"imu_sample_hz\s*=\s*(\d+)",
                "cliff_publish_hz": r"cliff_publish_hz\s*=\s*(\d+)",
                "range_publish_hz": r"range_publish_hz\s*=\s*(\d+)",
                "battery_publish_hz": r"battery_publish_hz\s*=\s*(\d+)",
                "addr_ina260": r"addr_ina260\s*=\s*(0x[0-9a-fA-F]+)",
                "addr_pca9685": r"addr_pca9685\s*=\s*(0x[0-9a-fA-F]+)",
                "addr_mpu6050": r"addr_mpu6050\s*=\s*(0x[0-9a-fA-F]+)",
                "motor_cutoff_voltage": r"motor_cutoff_voltage\s*=\s*([0-9.]+)",
                "cutoff_hysteresis": r"cutoff_hysteresis\s*=\s*([0-9.]+)",
            }
            for key, pattern in patterns.items():
                m = re.search(pattern, content)
                if m:
                    sensor_params[key] = m.group(1)
    data["config_sensors"] = sensor_params

    # --- Firmware-Build-Timestamps ---
    firmware_builds = {}
    fw_dir = _find_firmware_dir()
    if fw_dir:
        for node_name in ["drive_node", "sensor_node"]:
            elf_path = os.path.join(
                str(fw_dir), "..", node_name, ".pio", "build", node_name, "firmware.elf"
            )
            if os.path.isfile(elf_path):
                mtime = os.path.getmtime(elf_path)
                firmware_builds[node_name] = datetime.datetime.fromtimestamp(mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
    data["firmware_builds"] = firmware_builds

    return data


def print_project_info(data: dict[str, Any]) -> None:
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

    # config_drive.h
    params = data.get("config_h_params", {})
    if params:
        print()
        print(f"  {COLOR_CYAN}Firmware-Parameter (config_drive.h):{COLOR_RESET}")
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
        print_warn("config_drive.h", "nicht gefunden")

    # config_sensors.h
    sensor_cfg = data.get("config_sensors", {})
    if sensor_cfg:
        print()
        print(f"  {COLOR_CYAN}--- config_sensors.h ---{COLOR_RESET}")
        for key, val in sensor_cfg.items():
            print_info(f"  {key}", val)

    # Firmware-Build-Timestamps
    fw_builds = data.get("firmware_builds", {})
    if fw_builds:
        print()
        print(f"  {COLOR_CYAN}--- Firmware-Builds ---{COLOR_RESET}")
        for node, ts in fw_builds.items():
            print_info(f"  {node}", ts)


def generate_project_markdown(data: dict[str, Any]) -> str:
    """Erzeugt Markdown fuer Sektion 4: Projekt und Reproduzierbarkeit."""
    lines = []
    lines.append("## 4. Projekt und Reproduzierbarkeit")
    lines.append("")

    # Git
    commit = data.get("git_commit")
    if commit:
        branch = data.get("git_branch", "?")
        dirty = " (uncommitted)" if data.get("git_dirty") else ""
        lines.append(f"**Git:** `{branch}` @ `{commit}`{dirty}")
        commit_date = data.get("git_commit_date")
        if commit_date:
            lines.append(f"**Commit-Datum:** {commit_date}")
        lines.append("")

    # Docker-Image
    docker_img = data.get("docker_image_info")
    if docker_img:
        lines.append(f"**Docker-Image:** {docker_img}")
        lines.append("")

    # ROS2-Pakete
    ros2_pkgs = data.get("ros2_packages", {})
    if ros2_pkgs:
        lines.append("### ROS2-Pakete im Container")
        lines.append("")
        lines.append("| Paket | Version |")
        lines.append("|---|---|")
        for pkg, ver in sorted(ros2_pkgs.items()):
            lines.append(f"| {pkg} | {ver} |")
        lines.append("")

    # PlatformIO
    pio_plat = data.get("pio_platform")
    if pio_plat:
        lines.append(f"**PlatformIO-Plattform:** {pio_plat}")
    esptool = data.get("esptool_version")
    if esptool:
        lines.append(f"**esptool:** {esptool}")
    if pio_plat or esptool:
        lines.append("")

    # Boot-Config
    overlays = data.get("boot_overlays", [])
    if overlays:
        lines.append("### Boot-Konfiguration")
        lines.append("")
        lines.append("```")
        for ov in overlays:
            lines.append(ov)
        lines.append("```")
        lines.append("")

    # config_drive.h
    params = data.get("config_h_params", {})
    if params:
        lines.append("### Firmware-Parameter (config_drive.h)")
        lines.append("")
        lines.append("| Parameter | Wert |")
        lines.append("|---|---|")
        for key, val in params.items():
            lines.append(f"| {key} | {val} |")
        lines.append("")

    # config_sensors.h
    sensor_cfg = data.get("config_sensors", {})
    if sensor_cfg:
        lines.append("### Sensor-Parameter (config_sensors.h)")
        lines.append("")
        lines.append("| Parameter | Wert |")
        lines.append("|---|---|")
        for key, val in sensor_cfg.items():
            lines.append(f"| {key} | {val} |")
        lines.append("")

    # Firmware-Build-Timestamps
    fw_builds = data.get("firmware_builds", {})
    if fw_builds:
        lines.append("### Firmware-Builds")
        lines.append("")
        lines.append("| Node | Letzter Build |")
        lines.append("|---|---|")
        for node, ts in fw_builds.items():
            lines.append(f"| {node} | {ts} |")
        lines.append("")

    return "\n".join(lines)
