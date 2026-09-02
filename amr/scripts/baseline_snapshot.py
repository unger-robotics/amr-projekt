#!/usr/bin/env python3
"""Passive Bestandsaufnahme fuer die K0-Baseline.

Erfasst den Ist-Zustand als Referenz fuer alle Regressionspruefungen der
Ausbaupakete K1 bis K10. Die Aufnahme erfolgt bewusst in zwei getrennten
Laeufen, damit die Herkunft jedes ROS-Topics eindeutig bleibt:

* **Lauf A (`--mode ros`)**: heutiger USB/micro-ROS-Referenzpfad bei
  ``use_can:=False``. Erfasst ROS-2-Topics (Name, Typ, Publisher, Subscriber,
  Rate) und den TF-Baum aus /tf und /tf_static.
* **Lauf B (`--mode can`)**: bestehender CAN-Bus, rein passiv mitgehoert.
  Erfasst CAN-IDs, DLC, Frame-Raten, Error-Frames und die Kernelzaehler des
  Interfaces. CAN wird dabei **nicht** als ROS-Topic-Quelle aktiviert.
* **Zusammenfuehrung (`--merge`)**: schreibt beide Laeufe als gemeinsame
  K0-Baseline nach baseline_k0.json und baseline_k0.md.

Wuerden beide Quellen gleichzeitig laufen, waere bei mehrfach belegten Topics
(/imu, /cliff, /range/front, /battery) nicht unterscheidbar, welche Quelle die
gemessene Rate erzeugt hat. Die Trennung macht den spaeteren Vergleich
"USB-Referenz gegen CAN-Runtime" eindeutig.

Das Skript ist strikt passiv: es legt keinen Publisher an, sendet keinen
CAN-Frame und loest keine Bewegung aus.

Aufruf::

    ./run.sh ros2 run my_bot baseline_snapshot --mode ros --duration 120 --name baseline_k0_a
    ./run.sh ros2 run my_bot baseline_snapshot --mode can --duration 120 --name baseline_k0_b
    ./run.sh ros2 run my_bot baseline_snapshot --merge baseline_k0_a.json baseline_k0_b.json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import socket
import struct
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# rclpy ist nur fuer Lauf A (--mode ros) noetig. Lauf B (--mode can) laeuft
# bewusst ohne ROS, damit er auch auf dem Host ausgefuehrt werden kann, wo
# "ip" fuer den CAN-Fehlerzustand verfuegbar ist.
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import (
        QoSDurabilityPolicy,
        QoSHistoryPolicy,
        QoSProfile,
        QoSReliabilityPolicy,
    )
    from rosidl_runtime_py.utilities import get_message

    HAS_RCLPY = True
except ImportError:  # pragma: no cover - Host-Umgebung ohne ROS 2
    HAS_RCLPY = False
    # rclpy fehlt: Node dient nur als Platzhalter fuer die Klassendefinition.
    # BaselineSnapshot wird in diesem Fall nie instanziiert (Guard in _record).
    Node = object

CAN_FRAME_FMT = "=IB3x8s"
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)
CAN_EFF_MASK = 0x1FFFFFFF


def _repo_candidates() -> list[Path]:
    """Moegliche Repository-Wurzeln, robust gegen Symlink- und Container-Pfade.

    Auf dem Host liegt das Skript unter ``amr/scripts/``; im Container loest der
    Symlink je nach Aufrufweg auf ``/scripts`` oder ``/amr_scripts`` auf, sodass
    ``parents[2]`` nicht existieren muss.
    """
    here = Path(__file__).resolve()
    candidates = [here.parents[i] for i in range(min(3, len(here.parents)))]
    candidates += [Path("/ros2_ws/src/my_bot"), Path("/home/pi/amr-projekt")]
    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique


REPO_CANDIDATES = _repo_candidates()


def _find_repo_file(relative: str) -> Path | None:
    """Erste existierende Fundstelle einer Repository-Datei zurueckgeben."""
    for root in REPO_CANDIDATES:
        candidate = root / relative
        if candidate.exists():
            return candidate
    # Fallback: Launch- und setup-Dateien liegen im Container unter /ros2_ws
    tail = Path(relative).name
    for root in (Path("/ros2_ws/src/my_bot"), Path("/scripts"), Path("/amr_scripts")):
        if not root.exists():
            continue
        for found in root.rglob(tail):
            return found
    return None


def parse_launch_arguments() -> list[dict]:
    """Launch-Argumente aus full_stack.launch.py extrahieren."""
    path = _find_repo_file("amr/pi5/ros2_ws/src/my_bot/launch/full_stack.launch.py")
    if path is None:
        return []
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'DeclareLaunchArgument\(\s*"(?P<name>[^"]+)"\s*,\s*default_value=(?P<default>[^,)]+)',
        re.MULTILINE,
    )
    arguments = []
    for match in pattern.finditer(text):
        default = match.group("default").strip()
        # Literale entklammern, Ausdruecke (z. B. Pfadvariablen) unveraendert lassen
        if len(default) >= 2 and default[0] == default[-1] and default[0] in "\"'":
            default = default[1:-1]
        arguments.append({"name": match.group("name"), "default": default})
    return arguments


def parse_entry_points() -> list[str]:
    """console_scripts aus setup.py extrahieren."""
    path = _find_repo_file("amr/pi5/ros2_ws/src/my_bot/setup.py")
    if path is None:
        return []
    text = path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"^\s*\"(\w+) = my_bot\.", text, re.MULTILINE)))


def parse_firmware_versions() -> dict[str, str]:
    """@version-Angaben der beiden Firmware-Konfigurationen lesen."""
    versions: dict[str, str] = {}
    for name, relative, mounted in (
        (
            "config_drive.h",
            "amr/mcu_firmware/drive_node/include/config_drive.h",
            "/mcu_firmware/drive_node/include/config_drive.h",
        ),
        (
            "config_sensors.h",
            "amr/mcu_firmware/sensor_node/include/config_sensors.h",
            "/mcu_firmware/sensor_node/include/config_sensors.h",
        ),
    ):
        path = _find_repo_file(relative)
        if path is None and Path(mounted).exists():
            path = Path(mounted)
        if path is None:
            continue
        match = re.search(r"@version\s+([0-9.]+)", path.read_text(encoding="utf-8"))
        versions[name] = match.group(1) if match else "unbekannt"
    return versions


class CanListener:
    """Passives Mithoeren auf SocketCAN. Zaehlt Frames je ID, sendet nichts."""

    def __init__(self, interface: str) -> None:
        self.interface = interface
        self.counts: dict[int, int] = defaultdict(int)
        self.dlcs: dict[int, int] = {}
        self.error_frames = 0
        self.available = False
        self._stop = threading.Event()
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        try:
            sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
            sock.bind((self.interface,))
            sock.settimeout(1.0)
        except OSError:
            return
        self._socket = sock
        self.available = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        assert self._socket is not None
        while not self._stop.is_set():
            try:
                frame = self._socket.recv(CAN_FRAME_SIZE)
            except TimeoutError:
                continue
            except OSError:
                return
            if len(frame) < CAN_FRAME_SIZE:
                continue
            raw_id, dlc, _ = struct.unpack(CAN_FRAME_FMT, frame)
            if raw_id & socket.CAN_ERR_FLAG:
                self.error_frames += 1
                continue
            can_id = raw_id & CAN_EFF_MASK
            self.counts[can_id] += 1
            self.dlcs[can_id] = dlc

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._socket is not None:
            with contextlib.suppress(OSError):
                self._socket.close()

    def link_state(self) -> dict[str, str]:
        """Bitrate und CAN-Fehlerzustand aus `ip -details link show` lesen.

        Rein lesend. Liefert den ERROR-ACTIVE/PASSIVE/BUS-OFF-Zustand und die
        Fehlerzaehler, die `can_validation_test` nicht erfasst.
        """
        import subprocess

        try:
            output = subprocess.run(
                ["ip", "-details", "-statistics", "link", "show", self.interface],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            output = ""
        state: dict[str, str] = self._sysfs_link_state()
        if not output:
            return state
        match = re.search(r"can state (\S+)", output)
        if match:
            state["can_state"] = match.group(1)
        match = re.search(r"bitrate (\d+)", output)
        if match:
            state["bitrate"] = match.group(1)
        match = re.search(r"sample-point ([\d.]+)", output)
        if match:
            state["sample_point"] = match.group(1)
        # Zeile "re-started bus-errors arbit-lost error-warn error-pass bus-off"
        # gefolgt von der zugehoerigen Zahlenzeile
        counters = re.search(
            r"re-started\s+bus-errors\s+arbit-lost\s+error-warn\s+error-pass\s+bus-off\s*\n"
            r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            output,
        )
        if counters:
            for key, value in zip(
                (
                    "restarts",
                    "bus_errors",
                    "arbitration_lost",
                    "error_warning",
                    "error_passive",
                    "bus_off",
                ),
                counters.groups(),
                strict=True,
            ):
                state[key] = value
        return state

    def _sysfs_link_state(self) -> dict[str, str]:
        """Bitrate und Betriebszustand aus sysfs lesen (Fallback ohne "ip")."""
        state: dict[str, str] = {}
        base = Path("/sys/class/net") / self.interface
        for key, relative in (
            ("bitrate", "can_bittiming/bitrate"),
            ("sample_point", "can_bittiming/sample_point"),
            ("operstate", "operstate"),
        ):
            path = base / relative
            if path.exists():
                with contextlib.suppress(OSError):
                    state[key] = path.read_text().strip()
        return state

    def bus_statistics(self) -> dict[str, int]:
        """Kernelzaehler des CAN-Interfaces auslesen (rein lesend)."""
        stats: dict[str, int] = {}
        base = Path("/sys/class/net") / self.interface / "statistics"
        for key in ("rx_packets", "tx_packets", "rx_errors", "tx_errors", "rx_dropped"):
            path = base / key
            if path.exists():
                with contextlib.suppress(ValueError, OSError):
                    stats[key] = int(path.read_text().strip())
        return stats


class BaselineSnapshot(Node):
    """Abonniert alle sichtbaren Topics generisch und zaehlt die Nachrichten."""

    def __init__(self, skip_prefixes: tuple[str, ...]) -> None:
        super().__init__("baseline_snapshot")
        self._counts: dict[str, int] = defaultdict(int)
        self._types: dict[str, str] = {}
        self._tf_edges: set[tuple[str, str]] = set()
        self._skip_prefixes = skip_prefixes
        self._subs: list = []
        # Beobachtungsbeginn je Topic: Topics, die erst spaeter im DDS-Graph
        # auftauchen, werden sonst mit einer zu niedrigen Rate bewertet.
        self._sub_since: dict[str, float] = {}

    def discover_and_subscribe(self) -> int:
        """Alle Topics generisch abonnieren (BEST_EFFORT: maximal kompatibel)."""
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )
        tf_static_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )
        count = 0
        for name, type_names in self.get_topic_names_and_types():
            if not type_names or name.startswith(self._skip_prefixes):
                continue
            if name in self._types:
                continue  # bereits abonniert
            type_name = type_names[0]
            try:
                message_class = get_message(type_name)
            except (ImportError, ValueError, AttributeError):
                self.get_logger().warn(f"Typ nicht ladbar, uebersprungen: {name} ({type_name})")
                continue
            self._types[name] = type_name
            self._sub_since[name] = time.monotonic()
            profile = tf_static_qos if name == "/tf_static" else qos
            self._subs.append(
                self.create_subscription(message_class, name, self._make_callback(name), profile)
            )
            count += 1
        return count

    def _make_callback(self, topic: str):
        def callback(msg) -> None:
            self._counts[topic] += 1
            if topic in ("/tf", "/tf_static"):
                for transform in getattr(msg, "transforms", []):
                    self._tf_edges.add((transform.header.frame_id, transform.child_frame_id))

        return callback

    def result(self, duration_s: float) -> dict:
        now = time.monotonic()
        topics = []
        for name, type_name in sorted(self._types.items()):
            count = self._counts.get(name, 0)
            observed = now - self._sub_since.get(name, now - duration_s)
            observed = max(observed, 1e-6)
            topics.append(
                {
                    "name": name,
                    "type": type_name,
                    "publishers": self.count_publishers(name),
                    # Der Snapshot-Knoten selbst ist Subscriber und wird abgezogen
                    "subscribers": max(self.count_subscribers(name) - 1, 0),
                    "messages": count,
                    "observed_s": round(observed, 1),
                    "rate_hz": round(count / observed, 2),
                }
            )
        tf_edges = [{"parent": parent, "child": child} for parent, child in sorted(self._tf_edges)]
        return {"topics": topics, "tf_edges": tf_edges}


def _render_ros_section(data: dict) -> list[str]:
    """Topic- und TF-Tabellen eines ROS-Laufs rendern."""
    lines = [
        "| Topic | Typ | Pub | Sub | Nachrichten | Beobachtet (s) | Rate (Hz) |",
        "|---|---|---|---|---|---|---|",
    ]
    for topic in data.get("topics", []):
        lines.append(
            f"| `{topic['name']}` | `{topic['type']}` | {topic['publishers']} | "
            f"{topic['subscribers']} | {topic.get('messages', 0)} | "
            f"{topic.get('observed_s', '-')} | {topic['rate_hz']} |"
        )
    lines += ["", "### TF-Baum (beobachtete Kanten)", "", "| Parent | Child |", "|---|---|"]
    edges = data.get("tf_edges", [])
    for edge in edges:
        lines.append(f"| `{edge['parent']}` | `{edge['child']}` |")
    if not edges:
        lines.append("| - | - |")
    return lines


def _render_can_section(can: dict) -> list[str]:
    """CAN-Frame-, Error- und Kernelzaehler-Tabellen rendern."""
    if not can.get("available"):
        return [f"Interface `{can.get('interface', '?')}` nicht verfuegbar - keine Aufzeichnung."]
    lines = [
        f"Interface: `{can['interface']}` | Error-Frames: {can['error_frames']}",
        "",
        "| CAN-ID | DLC | Frames | Rate (Hz) |",
        "|---|---|---|---|",
    ]
    total = 0
    for frame in can["frames"]:
        total += frame["count"]
        lines.append(
            f"| `0x{frame['id']:03X}` | {frame['dlc']} | {frame['count']} | {frame['rate_hz']} |"
        )
    lines += ["", f"Frames gesamt: {total} | Verschiedene IDs: {len(can['frames'])}"]
    link = can.get("link_state")
    if link:
        lines += ["", "| Interface-Zustand | Wert |", "|---|---|"]
        for key, value in link.items():
            lines.append(f"| {key} | {value} |")
    if can.get("statistics"):
        delta = can.get("statistics_delta", {})
        lines += [
            "",
            "| Kernelzaehler | Absolut (seit Interface-Start) | Delta im Messfenster |",
            "|---|---|---|",
        ]
        for key, value in sorted(can["statistics"].items()):
            lines.append(f"| {key} | {value} | {delta.get(key, '-')} |")
        lines += [
            "",
            "`rx_dropped` waechst, solange kein Prozess die Frames aus der",
            "SocketCAN-Queue abholt; das ist erwartetes Verhalten und kein Busfehler.",
            "Massgeblich fuer die Busqualitaet sind `rx_errors`, `bus_errors` und der",
            "CAN-Zustand.",
        ]
    return lines


def _render_metadata_section(data: dict) -> list[str]:
    """Firmware-Versionen, Launch-Argumente und Entry-Points rendern."""
    lines = ["| Konfiguration | Version |", "|---|---|"]
    for name, version in sorted(data.get("firmware_versions", {}).items()):
        lines.append(f"| `{name}` | {version} |")
    lines += [
        "",
        "### Launch-Argumente (full_stack.launch.py)",
        "",
        "| Argument | Default |",
        "|---|---|",
    ]
    for argument in data.get("launch_arguments", []):
        lines.append(f"| `{argument['name']}` | `{argument['default']}` |")
    entry_points = data.get("entry_points", [])
    lines += [
        "",
        "### Entry-Points (setup.py)",
        "",
        f"Anzahl: {len(entry_points)}",
        "",
        ", ".join(f"`{name}`" for name in entry_points),
    ]
    return lines


def render_markdown(data: dict) -> str:
    """Protokoll eines Einzellaufs erzeugen (ASCII, ohne Umlaute)."""
    mode = data.get("mode", "full")
    title = {
        "ros": "Baseline K0 - Lauf A: ROS-2-Referenzpfad (USB/micro-ROS)",
        "can": "Baseline K0 - Lauf B: CAN-Bus (passiv)",
    }.get(mode, "Baseline K0 - Referenzstand vor dem Ausbau")
    lines = [
        f"# {title}",
        "",
        f"Aufnahmedatum: {data['timestamp']}",
        f"Messdauer: {data['duration_s']} s",
        f"Modus: {mode}",
        f"Git-Commit: {data['git_commit']}",
        f"Git-Tag: {data['git_tag']}",
        "",
        "Rein passiv aufgezeichnet: kein Publisher, kein CAN-Sendevorgang, keine",
        "Bewegung.",
        "",
        "---",
        "",
    ]
    if mode in ("ros", "full"):
        lines += ["## ROS-2-Topics", ""] + _render_ros_section(data) + [""]
    if mode in ("can", "full"):
        lines += ["## CAN-Frames", ""] + _render_can_section(data["can"]) + [""]
    lines += ["## Systemstand", ""] + _render_metadata_section(data) + [""]
    return "\n".join(lines)


def render_merged_markdown(merged: dict) -> str:
    """Gemeinsames K0-Baseline-Protokoll aus Lauf A und Lauf B erzeugen."""
    run_a = merged.get("run_a_ros_reference")
    run_b = merged.get("run_b_can_baseline")
    meta = merged["metadata"]
    lines = [
        "# Baseline K0 - Ist-Zustand vor dem Umbau",
        "",
        f"Git-Commit: {meta['git_commit']}",
        f"Git-Tag: {meta['git_tag']}",
        f"Zusammengefuehrt: {meta['merged_at']}",
        "",
        "Die Aufnahme erfolgte in zwei getrennten passiven Laeufen. Damit ist die",
        "Herkunft jedes ROS-Topics eindeutig: Lauf A misst ausschliesslich den",
        "heutigen USB/micro-ROS-Referenzpfad, Lauf B ausschliesslich den",
        "bestehenden CAN-Bus. Weder wurde Firmware geaendert oder geflasht, noch",
        "wurde ein Fahrbefehl gesendet.",
        "",
        "| Lauf | Gegenstand | Konfiguration | Dauer |",
        "|---|---|---|---|",
    ]
    if run_a:
        lines.append(
            f"| A | ROS-2-Topics und TF-Baum | `use_can:=False`, USB/micro-ROS | "
            f"{run_a['duration_s']} s |"
        )
    if run_b:
        lines.append(
            f"| B | CAN-Frames und Fehlerstatus | passives Mithoeren, CAN nicht als "
            f"ROS-Quelle | {run_b['duration_s']} s |"
        )
    lines += ["", "---", ""]

    if run_a:
        lines += [
            "## Lauf A - ROS-2-Referenzpfad (USB/micro-ROS)",
            "",
            f"Aufnahmedatum: {run_a['timestamp']} | Dauer: {run_a['duration_s']} s",
            "",
        ]
        lines += _render_ros_section(run_a)
        lines.append("")

    if run_b:
        lines += [
            "## Lauf B - CAN-Bus (passiv)",
            "",
            f"Aufnahmedatum: {run_b['timestamp']} | Dauer: {run_b['duration_s']} s",
            "",
        ]
        lines += _render_can_section(run_b["can"])
        lines.append("")

    source = run_a or run_b
    if source:
        lines += ["## Systemstand", ""] + _render_metadata_section(source) + [""]

    lines += [
        "---",
        "",
        "Regressionsschwellen und belegte Messwerte der Phasen 1 bis 5:",
        "`planung/baseline_k0_referenzwerte.md`.",
        "",
    ]
    return "\n".join(lines)


def _git_info() -> tuple[str, str]:
    import subprocess

    def run(args: list[str]) -> str:
        try:
            return subprocess.run(
                args, capture_output=True, text=True, timeout=5, check=False
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return "unbekannt"

    repo = _find_repo_file("README.md")
    cwd = str(repo.parent) if repo else "."
    commit = run(["git", "-C", cwd, "rev-parse", "--short", "HEAD"]) or "unbekannt"
    tag = run(["git", "-C", cwd, "describe", "--tags", "--abbrev=0"]) or "unbekannt"
    return commit, tag


def _resolve_output_dir(explicit: Path | None) -> Path:
    """Beschreibbares Zielverzeichnis bestimmen und anlegen.

    Im Container sind mehrere Repository-Pfade read-only gemountet. Daher wird
    nur ein Verzeichnis gewaehlt, in das auch tatsaechlich geschrieben werden
    kann; andernfalls faellt die Wahl auf das Arbeitsverzeichnis.
    """
    if explicit is not None:
        explicit.mkdir(parents=True, exist_ok=True)
        return explicit
    for root in REPO_CANDIDATES:
        candidate = root / "planung"
        if candidate.is_dir() and os.access(candidate, os.W_OK):
            return candidate
    return Path.cwd()


def _record(args, ros_args: list[str]) -> dict:
    """Einen Messlauf durchfuehren und das Ergebnis als dict zurueckgeben."""
    record_ros = args.mode in ("ros", "full")
    record_can = args.mode in ("can", "full")

    if record_ros and not HAS_RCLPY:
        raise SystemExit(
            f"Modus '{args.mode}' benoetigt rclpy. Im Container ausfuehren "
            "(./run.sh ros2 run my_bot baseline_snapshot ...) oder --mode can verwenden."
        )

    can = CanListener(args.can_interface)
    statistics_before: dict[str, int] = {}
    if record_can:
        statistics_before = can.bus_statistics()
        can.start()

    node = None
    if record_ros:
        rclpy.init(args=ros_args)
        node = BaselineSnapshot(skip_prefixes=("/baseline_snapshot",))
        # DDS-Discovery braucht einige Sekunden, bis der Graph vollstaendig ist.
        # Ohne diese Wartezeit sieht der Knoten nur seine eigenen Topics.
        discovery_end = time.monotonic() + args.discovery_wait
        while time.monotonic() < discovery_end and rclpy.ok():
            node.discover_and_subscribe()
            rclpy.spin_once(node, timeout_sec=0.2)
        subscribed = node.discover_and_subscribe()
        node.get_logger().info(
            f"Lauf '{args.mode}': {len(node._types)} Topics nach "
            f"{args.discovery_wait:.0f} s Discovery (davon {subscribed} zuletzt ergaenzt), "
            f"CAN {'aktiv' if can.available else 'inaktiv'}, {args.duration:.0f} s (passiv)"
        )
    else:
        print(
            f"Lauf '{args.mode}': nur CAN "
            f"({'aktiv' if can.available else 'nicht verfuegbar'}), "
            f"{args.duration:.0f} s (passiv)"
        )

    start = time.monotonic()
    next_rediscovery = start + 10.0
    try:
        while (time.monotonic() - start) < args.duration:
            if node is not None:
                if not rclpy.ok():
                    break
                rclpy.spin_once(node, timeout_sec=0.1)
                # Spaet startende Knoten (z. B. Nav2-Lifecycle) nachtragen
                if time.monotonic() >= next_rediscovery:
                    node.discover_and_subscribe()
                    next_rediscovery += 10.0
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Abbruch durch Benutzer - Teilergebnis wird geschrieben")
    duration = time.monotonic() - start
    can.stop()

    commit, tag = _git_info()
    data: dict = {"topics": [], "tf_edges": []}
    if node is not None:
        data = node.result(duration)
        node.destroy_node()
        rclpy.shutdown()

    data.update(
        {
            "mode": args.mode,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "duration_s": round(duration, 1),
            "git_commit": args.git_commit or commit,
            "git_tag": args.git_tag or tag,
            "firmware_versions": parse_firmware_versions(),
            "launch_arguments": parse_launch_arguments(),
            "entry_points": parse_entry_points(),
            "can": {
                "interface": args.can_interface,
                "recorded": record_can,
                "available": can.available if record_can else False,
                "error_frames": can.error_frames,
                "link_state": can.link_state() if record_can else {},
                "statistics": can.bus_statistics() if record_can else {},
                "statistics_delta": (
                    {
                        key: value - statistics_before.get(key, 0)
                        for key, value in can.bus_statistics().items()
                    }
                    if record_can
                    else {}
                ),
                "frames": [
                    {
                        "id": can_id,
                        "dlc": can.dlcs.get(can_id, 0),
                        "count": count,
                        "rate_hz": round(count / duration, 2) if duration > 0 else 0.0,
                    }
                    for can_id, count in sorted(can.counts.items())
                ],
            },
        }
    )
    return data


def _merge_runs(paths: list[str], output_dir: Path) -> int:
    """Ergebnisdateien der Einzellaeufe zur gemeinsamen K0-Baseline verbinden."""
    merged: dict = {"run_a_ros_reference": None, "run_b_can_baseline": None}
    for raw in paths:
        path = Path(raw)
        if not path.is_absolute():
            path = output_dir / path
        if not path.exists():
            print(f"FEHLER: Ergebnisdatei nicht gefunden: {path}", file=sys.stderr)
            return 1
        run = json.loads(path.read_text(encoding="utf-8"))
        mode = run.get("mode", "full")
        key = "run_b_can_baseline" if mode == "can" else "run_a_ros_reference"
        if merged[key] is not None:
            print(f"FEHLER: mehr als ein Lauf im Modus '{mode}'", file=sys.stderr)
            return 1
        merged[key] = run
        print(f"Gelesen: {path.name} (Modus {mode}, {run['duration_s']} s)")

    if merged["run_a_ros_reference"] is None and merged["run_b_can_baseline"] is None:
        print("FEHLER: keine verwertbaren Laeufe", file=sys.stderr)
        return 1

    source = merged["run_a_ros_reference"] or merged["run_b_can_baseline"]
    merged["metadata"] = {
        "git_commit": source["git_commit"],
        "git_tag": source["git_tag"],
        "merged_at": datetime.now().isoformat(timespec="seconds"),
        "firmware_versions": source["firmware_versions"],
    }

    json_path = output_dir / "baseline_k0.json"
    md_path = output_dir / "baseline_k0.md"
    json_path.write_text(json.dumps(merged, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    md_path.write_text(render_merged_markdown(merged), encoding="utf-8")
    print(f"Geschrieben: {json_path}")
    print(f"Geschrieben: {md_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Passive Baseline-Aufnahme des AMR")
    parser.add_argument(
        "--mode",
        choices=("ros", "can", "full"),
        default="full",
        help="ros = Lauf A (nur ROS-2), can = Lauf B (nur CAN), full = beides",
    )
    parser.add_argument("--duration", type=float, default=60.0, help="Messdauer in Sekunden")
    parser.add_argument(
        "--discovery-wait",
        type=float,
        default=8.0,
        help="Wartezeit fuer die DDS-Discovery vor Messbeginn (Sekunden)",
    )
    parser.add_argument("--can-interface", default="can0", help="SocketCAN-Interface")
    parser.add_argument(
        "--name",
        default="baseline_k0",
        help="Basisname der Ausgabedateien ohne Endung",
    )
    parser.add_argument(
        "--merge",
        nargs="+",
        metavar="JSON",
        default=None,
        help="Ergebnisdateien der Einzellaeufe zur gemeinsamen K0-Baseline zusammenfuehren",
    )
    parser.add_argument(
        "--git-commit",
        default=None,
        help="Git-Commit des Referenzstands (im Container nicht ermittelbar)",
    )
    parser.add_argument(
        "--git-tag",
        default=None,
        help="Git-Tag des Referenzstands (im Container nicht ermittelbar)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Zielverzeichnis fuer baseline_k0.json und baseline_k0.md",
    )
    args, ros_args = parser.parse_known_args(argv)
    output_dir = _resolve_output_dir(args.output_dir)

    if args.merge:
        return _merge_runs(args.merge, output_dir)

    data = _record(args, ros_args)

    json_path = output_dir / f"{args.name}.json"
    md_path = output_dir / f"{args.name}.md"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(data), encoding="utf-8")

    if args.mode in ("ros", "full"):
        print(f"Topics:      {len(data['topics'])}")
        print(f"TF-Kanten:   {len(data['tf_edges'])}")
    if args.mode in ("can", "full"):
        print(f"CAN-IDs:     {len(data['can']['frames'])}")
        print(f"Error-Frames:{data['can']['error_frames']:>4}")
    print(f"Geschrieben: {json_path}")
    print(f"Geschrieben: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
