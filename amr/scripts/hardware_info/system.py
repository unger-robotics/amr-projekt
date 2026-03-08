"""Sektion 1: Systemressourcen und thermischer Zustand."""

import contextlib
import os
from pathlib import Path
from typing import Any

from utils import print_fail, print_header, print_info, print_warn, run_cmd

__all__ = ["collect_system_resources", "print_system_resources", "generate_system_markdown"]


# ===========================================================================
# Datensammlung
# ===========================================================================


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
    from glob import glob

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


# ===========================================================================
# Markdown-Export
# ===========================================================================


def generate_system_markdown(data, pi_model=None, uptime=None):
    """Erzeugt den Markdown-Abschnitt fuer Sektion 1: Systemressourcen.

    Args:
        data: Dictionary aus collect_system_resources().
        pi_model: Optionaler Pi-Modellname (aus collect_software()).
        uptime: Optionaler Uptime-String (aus collect_software()).

    Returns:
        Markdown-String fuer Sektion 1.
    """
    lines = []
    lines.append("## 1. Systemressourcen und thermischer Zustand")
    lines.append("")
    lines.append("| Parameter | Wert |")
    lines.append("|---|---|")

    if pi_model:
        lines.append(f"| Hardware | {pi_model} |")

    temp = data.get("temperature_c")
    lines.append(f"| CPU-Temperatur | {temp:.1f} degC |" if temp else "| CPU-Temperatur | - |")

    throttle = data.get("throttle_hex", "-")
    lines.append(f"| Throttle-Status | {throttle} |")

    cpu_count = data.get("cpu_count", "?")
    freqs = data.get("cpu_freq_mhz", [])
    avg_freq = f"{sum(freqs) / len(freqs):.0f} MHz" if freqs else "-"
    lines.append(f"| CPU | {cpu_count} Kerne @ {avg_freq} |")

    load_1 = data.get("load_1m")
    if load_1 is not None:
        lines.append(
            f"| Load Average | {data['load_1m']:.2f} / {data['load_5m']:.2f} / {data['load_15m']:.2f} |"
        )

    ram = data.get("ram_total_mb")
    if ram:
        lines.append(f"| RAM | {data['ram_used_mb']} / {ram} MB ({data['ram_usage_pct']}%) |")

    disk = data.get("disk_total_gb")
    if disk:
        lines.append(
            f"| Disk (/) | {data['disk_used_gb']} / {disk} GB ({data['disk_usage_pct']}%) |"
        )

    if uptime:
        lines.append(f"| Uptime | {uptime} |")

    lines.append("")

    return "\n".join(lines)
