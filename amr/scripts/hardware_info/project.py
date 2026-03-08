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
    """Sucht config_sensors.h relativ zum Skript-Verzeichnis oder im Projektbaum."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir
        / "../../mcu_firmware/sensor_node/include/config_sensors.h",  # hardware_info/ -> amr/mcu_firmware/
        Path.home() / "AMR-Bachelorarbeit/amr/mcu_firmware/sensor_node/include/config_sensors.h",
    ]
    for c in candidates:
        resolved = c.resolve()
        if resolved.is_file():
            return resolved
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
            # inline constexpr Werte extrahieren (config_drive.h v4.0.0)
            define_patterns = {
                "wheel_diameter": r"constexpr\s+float\s+wheel_diameter\s*=\s*([\d.]+)f?",
                "wheel_base": r"constexpr\s+float\s+wheel_base\s*=\s*([\d.]+)f?",
                "ticks_per_rev_left": r"constexpr\s+float\s+ticks_per_rev_left\s*=\s*([\d.]+)f?",
                "ticks_per_rev_right": r"constexpr\s+float\s+ticks_per_rev_right\s*=\s*([\d.]+)f?",
                "deadzone": r"constexpr\s+uint32_t\s+deadzone\s*=\s*(\d+)",
                "failsafe_timeout_ms": r"constexpr\s+uint32_t\s+failsafe_timeout_ms\s*=\s*(\d+)",
                "control_loop_hz": r"constexpr\s+uint32_t\s+control_loop_hz\s*=\s*(\d+)",
                "odom_publish_hz": r"constexpr\s+uint32_t\s+odom_publish_hz\s*=\s*(\d+)",
                "kp": r"constexpr\s+float\s+kp\s*=\s*([\d.]+)f?",
                "ki": r"constexpr\s+float\s+ki\s*=\s*([\d.]+)f?",
                "kd": r"constexpr\s+float\s+kd\s*=\s*([\d.]+)f?",
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
                "us_publish_hz": r"us_publish_hz\s*=\s*(\d+)",
                "battery_publish_hz": r"battery_publish_hz\s*=\s*(\d+)",
                "addr_ina260": r"addr_ina260\s*=\s*(0x[0-9a-fA-F]+)",
                "addr_pca9685": r"addr_pca9685\s*=\s*(0x[0-9a-fA-F]+)",
                "addr_mpu6050": r"addr_mpu6050\s*=\s*(0x[0-9a-fA-F]+)",
                "threshold_motor_shutdown_v": r"threshold_motor_shutdown_v\s*=\s*([\d.]+)f?",
                "pack_cutoff_v": r"pack_cutoff_v\s*=\s*([\d.]+)f?",
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
            "wheel_diameter": ("Raddurchmesser", "m"),
            "wheel_base": ("Spurbreite", "m"),
            "ticks_per_rev_left": ("Ticks/Rev links", ""),
            "ticks_per_rev_right": ("Ticks/Rev rechts", ""),
            "deadzone": ("PWM-Deadzone", ""),
            "failsafe_timeout_ms": ("Failsafe-Timeout", "ms"),
            "control_loop_hz": ("Regelfrequenz", "Hz"),
            "odom_publish_hz": ("Odom-Rate", "Hz"),
            "kp": ("PID Kp", ""),
            "ki": ("PID Ki", ""),
            "kd": ("PID Kd", ""),
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
