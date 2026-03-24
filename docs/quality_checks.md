---
description: >-
  Statische Qualitaetspruefungen fuer Python, C++, TypeScript
  via pre-commit und CI.
robots: noindex, nofollow
---

# Qualitaetssicherung

## Zweck

Sammlung aller statischen und halbautomatischen Pruefungen fuer Python, C++, TypeScript und allgemeine Dateihygiene.

## Ausfuehrung

Alle Pruefungen auf einmal:

```bash
pre-commit run --all-files
```

Installation (einmalig):

```bash
pip3 install pre-commit
pre-commit install
```

## Pre-commit Hooks (11 Hooks)

| # | Hook | Quelle | Aufgabe |
|---|---|---|---|
| 1 | `ruff` | astral-sh/ruff-pre-commit v0.9.10 | Python-Linting (pycodestyle, Pyflakes, isort, pyupgrade, bugbear, comprehensions, simplify, McCabe) |
| 2 | `ruff-format` | astral-sh/ruff-pre-commit v0.9.10 | Python-Formatierungspruefung (`--check`) |
| 3 | `mypy` | pre-commit/mirrors-mypy v1.15.0 | Python Type-Checking (moderater Modus) |
| 4 | `clang-format` | pre-commit/mirrors-clang-format v19.1.7 | C++-Formatierung (`--dry-run --Werror`) |
| 5 | `eslint-dashboard` | lokal | TypeScript-Linting fuer Dashboard (`npm run lint`) |
| 6 | `trailing-whitespace` | pre-commit/pre-commit-hooks v5.0.0 | Entfernt nachgestellte Leerzeichen |
| 7 | `end-of-file-fixer` | pre-commit/pre-commit-hooks v5.0.0 | Stellt Zeilenende am Dateiende sicher |
| 8 | `check-yaml` | pre-commit/pre-commit-hooks v5.0.0 | YAML-Syntax (`--allow-multiple-documents`) |
| 9 | `check-added-large-files` | pre-commit/pre-commit-hooks v5.0.0 | Warnt bei Dateien > 500 kB |
| 10 | `check-merge-conflict` | pre-commit/pre-commit-hooks v5.0.0 | Erkennt Merge-Konfliktmarker |
| 11 | `check-symlinks` | pre-commit/pre-commit-hooks v5.0.0 | Prueft defekte Symlinks |

## Ruff-Konfiguration (ruff.toml)

- **Zielversion:** Python 3.10 (Container-Skripte). Host-Only-Skripte wie `host_hailo_runner.py` laufen unter Python 3.13 (Debian Trixie).
- **Zeilenlaenge:** 100
- **Regelsets:** E/W (pycodestyle), F (Pyflakes), I (isort), UP (pyupgrade), B (bugbear), C4 (comprehensions), SIM (simplify), C90 (McCabe)
- **McCabe max-complexity:** 15
- **Ignoriert:** E501 (Zeilenlaenge vom Formatter), E741 (mehrdeutige Variablennamen), SIM108 (Ternary), B008 (Funktionsaufruf in Default-Argument)
- **Ausgeschlossene Verzeichnisse:** `my_bot/my_bot` (Symlink-Verzeichnis), `.venv`, `.pio`, `node_modules`, `dashboard`, `build`, `install`, `log`, `suche`, `sources`, `projektarbeit`
- **Per-file-ignores:** C901-Ausnahmen fuer `dashboard_bridge.py`, `hailo_inference_node.py`, `host_hailo_runner.py`, `hardware_info.py`, `hardware_info/*.py`, `scripts/md_to_html_converter.py`; F401 fuer Import-Fallback-Pattern (`dashboard_bridge.py`, `gemini_semantic_node.py`, `hailo_inference_node.py`, `host_hailo_runner.py`); SIM115 fuer `serial_latency_logger.py`; E501 fuer Launch-Dateien und `setup.py`
- **Format:** Double quotes, Space indent

## mypy-Konfiguration (mypy.ini)

- **Python-Version:** 3.10
- **Gepruefte Dateien:** `amr/scripts/`, `scripts/`, `odom_to_tf.py`
- **Modus:** Moderat (< 10% Type-Hints vorhanden)
  - `disallow_untyped_defs = false`
  - `check_untyped_defs = true`
  - `warn_no_return = true`
  - `warn_redundant_casts = true`
  - `warn_unused_ignores = true`
  - `warn_unreachable = true`
  - `no_implicit_optional = true`
  - `namespace_packages = true`
  - `ignore_missing_imports = true` (global)
- **ignore_missing_imports:** Zusaetzlich per-Modul aktiviert fuer alle ROS2-Pakete (rclpy, geometry_msgs, nav_msgs, sensor_msgs, std_msgs, tf2_ros, launch, launch_ros), cv_bridge, OpenCV, numpy, websockets, google, hailort, matplotlib

## clang-format (.clang-format)

- **Basis-Stil:** LLVM
- **Standard:** C++17
- **Einrueckung:** 4 Spaces (kein Tab)
- **Zeilenlaenge:** 100
- **Klammern:** Attach (K&R-Stil)
- **Namespace-Einrueckung:** None
- **Pointer-Ausrichtung:** Right (`int *p`)
- **SortIncludes:** Never (Reihenfolge beibehalten, Arduino.h-Makro-Konflikte vermeiden)
- **Kurzformen:** Nur Inline-Funktionen einzeilig erlaubt
- **Geltungsbereich:** `drive_node/src/*.cpp`, `drive_node/include/*.hpp`, `sensor_node/src/*.cpp`, `sensor_node/include/*.hpp`

## Manuelle Einzelpruefungen

```bash
# Python
ruff check amr/
ruff format --check amr/
mypy --config-file mypy.ini

# C++
clang-format --dry-run --Werror \
    amr/mcu_firmware/drive_node/src/*.cpp \
    amr/mcu_firmware/drive_node/include/*.hpp \
    amr/mcu_firmware/sensor_node/src/*.cpp \
    amr/mcu_firmware/sensor_node/include/*.hpp

# TypeScript (Dashboard)
cd dashboard && npx tsc --noEmit
cd dashboard && npm run lint
```

## Grenzen

- **clang-tidy:** Auf Xtensa-Toolchain (ESP32) nicht verfuegbar. Statische C++-Analyse beschraenkt sich auf `clang-format`.
- **Unit-Tests:** Keine automatisierten Unit-Tests vorhanden. Validierung erfolgt experimentell ueber ROS2-Knoten (V-Modell-Phasenplan).
