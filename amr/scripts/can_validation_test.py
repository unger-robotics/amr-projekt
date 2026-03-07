#!/usr/bin/env python3
"""CAN-Bus Validierungstest fuer AMR.

Automatisierte Pruefung aller CAN-Frames beider ESP32-Nodes.
Standalone ohne ROS2, nutzt python-can direkt auf SocketCAN.

Verwendung:
    python3 can_validation_test.py
    python3 can_validation_test.py --duration 60
    python3 can_validation_test.py --interface can0
"""

import argparse
import json
import struct
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import can
except ImportError:
    print("FEHLER: python-can nicht installiert (pip install python-can)")
    sys.exit(1)


# --- Hilfsfunktionen fuer Little-Endian-Dekodierung ---


def sf(data: bytes, offset: int) -> float:
    """float32 LE aus Bytes."""
    return struct.unpack_from("<f", data, offset)[0]


def sh(data: bytes, offset: int) -> int:
    """int16 LE aus Bytes."""
    return struct.unpack_from("<h", data, offset)[0]


def su(data: bytes, offset: int) -> int:
    """uint16 LE aus Bytes."""
    return struct.unpack_from("<H", data, offset)[0]


def decode_drive_heartbeat(data: bytes) -> dict:
    flags = data[0]
    return {
        "encoder_ok": bool(flags & 0x01),
        "motor_ok": bool(flags & 0x02),
        "pid_active": bool(flags & 0x04),
        "bat_shutdown": bool(flags & 0x08),
        "core1_ok": bool(flags & 0x10),
        "failsafe": bool(flags & 0x20),
        "uptime_mod256": data[1],
    }


def decode_sensor_heartbeat(data: bytes) -> dict:
    flags = data[0]
    return {
        "imu_ok": bool(flags & 0x01),
        "ina260_ok": bool(flags & 0x02),
        "pca9685_ok": bool(flags & 0x04),
        "bat_shutdown": bool(flags & 0x08),
        "core1_ok": bool(flags & 0x10),
        "uptime_mod256": data[1],
    }


# --- Erwartete CAN-IDs ---

EXPECTED: dict[int, dict[str, Any]] = {
    0x200: {
        "name": "Drive/OdomPos",
        "dlc": 8,
        "rate_hz": 20,
        "node": "drive",
        "decode": lambda d: {"x_m": round(sf(d, 0), 4), "y_m": round(sf(d, 4), 4)},
    },
    0x201: {
        "name": "Drive/OdomHeading",
        "dlc": 8,
        "rate_hz": 20,
        "node": "drive",
        "decode": lambda d: {
            "theta_rad": round(sf(d, 0), 4),
            "v_ms": round(sf(d, 4), 4),
        },
    },
    0x210: {
        "name": "Drive/Encoder",
        "dlc": 8,
        "rate_hz": 10,
        "node": "drive",
        "decode": lambda d: {
            "left_rads": round(sf(d, 0), 3),
            "right_rads": round(sf(d, 4), 3),
        },
    },
    0x220: {
        "name": "Drive/MotorPWM",
        "dlc": 4,
        "rate_hz": 10,
        "node": "drive",
        "decode": lambda d: {"left": sh(d, 0), "right": sh(d, 2)},
    },
    0x2F0: {
        "name": "Drive/Heartbeat",
        "dlc": 2,
        "rate_hz": 1,
        "node": "drive",
        "decode": decode_drive_heartbeat,
    },
    0x110: {
        "name": "Sensor/Range",
        "dlc": 4,
        "rate_hz": 10,
        "node": "sensor",
        "decode": lambda d: {"range_m": round(sf(d, 0), 3)},
    },
    0x120: {
        "name": "Sensor/Cliff",
        "dlc": 1,
        "rate_hz": 20,
        "node": "sensor",
        "decode": lambda d: {"cliff": bool(d[0])},
    },
    0x130: {
        "name": "Sensor/IMU_Accel",
        "dlc": 8,
        "rate_hz": 50,
        "node": "sensor",
        "decode": lambda d: {
            "ax_mg": sh(d, 0),
            "ay_mg": sh(d, 2),
            "az_mg": sh(d, 4),
            "gz_001rads": sh(d, 6),
        },
    },
    0x131: {
        "name": "Sensor/IMU_Heading",
        "dlc": 4,
        "rate_hz": 50,
        "node": "sensor",
        "decode": lambda d: {"heading_rad": round(sf(d, 0), 4)},
    },
    0x140: {
        "name": "Sensor/Battery",
        "dlc": 6,
        "rate_hz": 2,
        "node": "sensor",
        "decode": lambda d: {
            "voltage_mv": su(d, 0),
            "current_ma": sh(d, 2),
            "power_mw": su(d, 4),
        },
    },
    0x141: {
        "name": "Sensor/BatShutdown",
        "dlc": 1,
        "rate_hz": 0,
        "node": "sensor",
        "decode": lambda d: {"shutdown": bool(d[0])},
    },
    0x1F0: {
        "name": "Sensor/Heartbeat",
        "dlc": 2,
        "rate_hz": 1,
        "node": "sensor",
        "decode": decode_sensor_heartbeat,
    },
}


def collect_frames(
    bus: can.Bus, duration_s: int
) -> tuple[dict[int, list[float]], dict[int, bytes], int]:
    """Sammelt CAN-Frames fuer die angegebene Dauer."""
    frames: dict[int, list[float]] = defaultdict(list)
    last_data: dict[int, bytes] = {}
    t_start = time.monotonic()
    t_next_status = t_start + 5

    print(f"Aufnahme laeuft ({duration_s}s)...")
    while True:
        elapsed = time.monotonic() - t_start
        if elapsed >= duration_s:
            break
        if time.monotonic() >= t_next_status:
            total = sum(len(v) for v in frames.values())
            ids = len(frames)
            print(f"  {elapsed:.0f}s: {total} Frames, {ids} IDs")
            t_next_status += 5

        msg = bus.recv(timeout=0.1)
        if msg and not msg.is_error_frame:
            frames[msg.arbitration_id].append(time.monotonic())
            last_data[msg.arbitration_id] = bytes(msg.data[: msg.dlc])

    total = sum(len(v) for v in frames.values())
    print(f"Aufnahme beendet: {total} Frames, {len(frames)} IDs\n")
    return frames, last_data, duration_s


def _rate_status(count: int, rate_hz: int, actual_hz: float) -> str:
    """Bestimmt PASS/WARN/FAIL fuer eine Frame-Rate."""
    if rate_hz == 0:
        return "OK"
    if count == 0:
        return "FAIL"
    if abs(actual_hz - rate_hz) <= rate_hz * 0.25:
        return "PASS"
    return "WARN"


def _decode_sample(spec: dict, data: bytes, can_id: int, results: dict) -> None:
    """Dekodiert einen Frame und speichert Wert + Heartbeat."""
    id_hex = f"0x{can_id:03X}"
    try:
        decoded = spec["decode"](data)
        results["sample_values"][id_hex] = decoded
        if can_id == 0x2F0:
            results["heartbeats"]["drive"] = decoded
        elif can_id == 0x1F0:
            results["heartbeats"]["sensor"] = decoded
    except Exception as e:
        results["sample_values"][id_hex] = {"error": str(e)}


def analyze(frames: dict[int, list[float]], last_data: dict[int, bytes], duration_s: int) -> dict:
    """Analysiert Frame-Raten, dekodiert Daten, prueft Vollstaendigkeit."""
    results: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test": "can_validation",
        "duration_s": duration_s,
        "total_frames": sum(len(v) for v in frames.values()),
        "frame_rates": {},
        "heartbeats": {"drive": None, "sensor": None},
        "sample_values": {},
        "missing_ids": [],
        "nodes": {
            "drive": {"ids_expected": 5, "ids_received": 0, "status": "MISSING"},
            "sensor": {"ids_expected": 7, "ids_received": 0, "status": "MISSING"},
        },
        "overall_status": "PASS",
    }

    for can_id, spec in EXPECTED.items():
        id_hex = f"0x{can_id:03X}"
        count = len(frames.get(can_id, []))
        rate_hz: int = spec["rate_hz"]
        actual_hz = count / duration_s if duration_s > 0 else 0.0
        status = _rate_status(count, rate_hz, actual_hz)

        results["frame_rates"][id_hex] = {
            "name": spec["name"],
            "expected_hz": rate_hz,
            "actual_hz": round(actual_hz, 1),
            "count": count,
            "status": status,
        }

        if count > 0:
            results["nodes"][spec["node"]]["ids_received"] += 1
        if count == 0 and rate_hz > 0:
            results["missing_ids"].append(id_hex)
        if can_id in last_data:
            _decode_sample(spec, last_data[can_id], can_id, results)

    # Node-Status bestimmen
    for _node_name, node_info in results["nodes"].items():
        received = node_info["ids_received"]
        expected = node_info["ids_expected"]
        if received == 0:
            node_info["status"] = "MISSING"
        elif received < expected - 1:
            node_info["status"] = "PARTIAL"
        else:
            node_info["status"] = "OK"

    if results["missing_ids"]:
        results["overall_status"] = "FAIL"
    elif any(r["status"] == "WARN" for r in results["frame_rates"].values()):
        results["overall_status"] = "WARN"

    return results


def print_report(results):
    """Gibt den Testbericht auf der Konsole aus."""
    print("=" * 70)
    print("CAN-Bus Validierungsbericht")
    print(f"Zeitpunkt: {results['timestamp']}")
    print(f"Dauer: {results['duration_s']}s, Gesamt: {results['total_frames']} Frames")
    print("=" * 70)

    # Frame-Raten-Tabelle
    print(f"\n{'ID':<8} {'Name':<22} {'Soll':>6} {'Ist':>6} {'Count':>6} {'Status':>6}")
    print("-" * 58)
    for id_hex, info in sorted(results["frame_rates"].items()):
        marker = {
            "PASS": " OK",
            "WARN": " !!",
            "FAIL": " XX",
            "OK": " --",
        }.get(info["status"], "")
        print(
            f"{id_hex:<8} {info['name']:<22} {info['expected_hz']:>5}Hz "
            f"{info['actual_hz']:>5}Hz {info['count']:>5} {marker}"
        )

    # Heartbeats
    print("\n--- Heartbeats ---")
    for node_name in ["drive", "sensor"]:
        hb = results["heartbeats"].get(node_name)
        if hb:
            print(f"  {node_name.capitalize()}: {hb}")
        else:
            print(f"  {node_name.capitalize()}: NICHT EMPFANGEN")

    # Node-Status
    print("\n--- Node-Status ---")
    for node_name, info in results["nodes"].items():
        print(
            f"  {node_name.capitalize()}: {info['status']} "
            f"({info['ids_received']}/{info['ids_expected']} IDs)"
        )

    # Sample-Werte
    if results["sample_values"]:
        print("\n--- Letzte Werte ---")
        for id_hex, vals in sorted(results["sample_values"].items()):
            if id_hex not in ("0x2F0", "0x1F0"):  # Heartbeats schon oben
                print(f"  {id_hex}: {vals}")

    # Fehlende IDs
    if results["missing_ids"]:
        print(f"\n--- FEHLEND: {', '.join(results['missing_ids'])} ---")

    # Gesamtergebnis
    status = results["overall_status"]
    print(f"\n{'=' * 70}")
    print(f"ERGEBNIS: {status}")
    print(f"{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(description="CAN-Bus Validierungstest (AMR)")
    parser.add_argument(
        "--duration", type=int, default=30, help="Aufnahmedauer in Sekunden (default: 30)"
    )
    parser.add_argument(
        "--interface", type=str, default="can0", help="SocketCAN Interface (default: can0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="can_results.json",
        help="JSON-Ausgabedatei (default: can_results.json)",
    )
    args = parser.parse_args()

    try:
        bus = can.Bus(interface="socketcan", channel=args.interface)
    except OSError as e:
        print(f"FEHLER: {e}")
        print("Prueftipps:")
        print("  - dtoverlay=mcp2515-can0 in /boot/firmware/config.txt?")
        print("  - sudo ip link set can0 up type can bitrate 1000000")
        sys.exit(1)

    try:
        frames, last_data, duration = collect_frames(bus, args.duration)
        results = analyze(frames, last_data, duration)
        print_report(results)

        # JSON speichern
        out_path = Path(args.output)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\nJSON gespeichert: {out_path.resolve()}")
    finally:
        bus.shutdown()

    sys.exit(0 if results["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
