"""Gemeinsame Hilfsfunktionen und ANSI-Farbkonstanten fuer das Hardware-Info-Paket."""

import subprocess

# ===========================================================================
# ANSI-Farben und Formatierung
# ===========================================================================

COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def print_header(titel: str) -> None:
    """Gibt eine formatierte Sektions-Ueberschrift aus."""
    print()
    print(f"{COLOR_BOLD}{'=' * 60}")
    print(f"  {titel}")
    print(f"{'=' * 60}{COLOR_RESET}")


def print_info(text: str, value: str = "") -> None:
    """Gibt eine INFO-Zeile aus."""
    if value:
        print(f"  {COLOR_GREEN}[INFO]{COLOR_RESET} {text}: {COLOR_BOLD}{value}{COLOR_RESET}")
    else:
        print(f"  {COLOR_GREEN}[INFO]{COLOR_RESET} {text}")


def print_warn(text: str, value: str = "") -> None:
    """Gibt eine WARN-Zeile aus."""
    if value:
        print(f"  {COLOR_YELLOW}[WARN]{COLOR_RESET} {text}: {value}")
    else:
        print(f"  {COLOR_YELLOW}[WARN]{COLOR_RESET} {text}")


def print_fail(text: str, value: str = "") -> None:
    """Gibt eine FAIL-Zeile aus."""
    if value:
        print(f"  {COLOR_RED}[FAIL]{COLOR_RESET} {text}: {value}")
    else:
        print(f"  {COLOR_RED}[FAIL]{COLOR_RESET} {text}")


def run_cmd(cmd: str, timeout: int = 5) -> str | None:
    """Fuehrt ein Shell-Kommando aus und gibt stdout zurueck (oder None bei Fehler)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


__all__ = [
    "COLOR_GREEN",
    "COLOR_YELLOW",
    "COLOR_RED",
    "COLOR_CYAN",
    "COLOR_BOLD",
    "COLOR_RESET",
    "print_header",
    "print_info",
    "print_warn",
    "print_fail",
    "run_cmd",
]
