#!/usr/bin/env python3
"""Phase-5-Validierung: Bedien- und Leitstandsebene.

Automatisierte Tests fuer Dashboard-Latenz, Telemetrie-Vollstaendigkeit,
Deadman-Timer, Audio-Feedback und Notaus.

Voraussetzung:
  - Stack mit use_dashboard:=True use_cliff_safety:=True use_audio:=True
  - Roboter auf ebenem Boden, kein Hindernis < 80 mm

Verwendung:
    cd /amr_scripts && python3 dashboard_latency_test.py --output /ros2_ws/build/my_bot/my_bot/
"""

import argparse
import asyncio
import json
import math
import os
import queue
import statistics
import threading
import time
from datetime import datetime

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String

try:
    from amr_utils import (
        ANSI_BOLD,
        ANSI_CYAN,
        ANSI_GREEN,
        ANSI_RED,
        ANSI_RESET,
        save_json,
    )
except ImportError:
    try:
        from my_bot.amr_utils import (
            ANSI_BOLD,
            ANSI_CYAN,
            ANSI_GREEN,
            ANSI_RED,
            ANSI_RESET,
            save_json,
        )
    except ImportError:
        ANSI_GREEN = "\033[32m"
        ANSI_RED = "\033[31m"
        ANSI_BOLD = "\033[1m"
        ANSI_RESET = "\033[0m"
        ANSI_CYAN = "\033[36m"
        save_json = None  # type: ignore[assignment]

try:
    import websockets
except ImportError:
    websockets = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Akzeptanzkriterien
# ---------------------------------------------------------------------------
LATENZ_P95_MAX_MS = 100.0
LATENZ_AVG_MAX_MS = 50.0
DEADMAN_STOPP_MAX_MS = 500.0
NOTAUS_STOPP_MAX_MS = 100.0
AUDIO_KEYS = ["startup", "nav_start", "nav_reached", "cliff_alarm"]
PFLICHT_BROADCASTS = {
    "telemetry": 8.0,
    "system": 0.5,
    "nav_status": 0.5,
    "sensor_status": 1.0,
    "audio_status": 1.0,
}
TELEMETRIE_DAUER_S = 30
CMD_VEL_SPEED = 0.05  # m/s — kleiner Wert, sicher fuer Innenraum


class DashboardTestNode(Node):
    """ROS2-Node mit Subscribern fuer /cmd_vel und /audio/play."""

    def __init__(self):
        super().__init__("dashboard_latency_test")
        self.cmd_vel_queue = queue.Queue()
        self.audio_received = []
        self.audio_lock = threading.Lock()

        self.sub_cmd_vel = self.create_subscription(Twist, "/cmd_vel", self._cmd_vel_cb, 10)
        self.sub_audio = self.create_subscription(String, "/audio/play", self._audio_cb, 10)

    def _cmd_vel_cb(self, msg):
        self.cmd_vel_queue.put((time.monotonic(), msg.linear.x, msg.angular.z))

    def _audio_cb(self, msg):
        with self.audio_lock:
            self.audio_received.append(msg.data)


def _percentile(data, pct):
    """Berechnet das Perzentil (0-100) einer sortierten Liste."""
    if not data:
        return 0.0
    k = (len(data) - 1) * pct / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    return data[f] * (c - k) + data[c] * (k - f)


async def test_cmd_vel_latenz(ws_url, node, samples=100):
    """Test 5.1: cmd_vel End-to-End-Latenz."""
    node.get_logger().info(f"Test 5.1: cmd_vel-Latenz ({samples} Samples)...")

    # Queue leeren
    while not node.cmd_vel_queue.empty():
        try:
            node.cmd_vel_queue.get_nowait()
        except queue.Empty:
            break

    latencies = []
    async with websockets.connect(ws_url) as ws:
        # Heartbeat senden, Controller-Registrierung
        await ws.send(json.dumps({"op": "heartbeat"}))
        await ws.send(json.dumps({"op": "cmd_vel", "linear_x": 0.0, "angular_z": 0.0}))
        await asyncio.sleep(0.5)

        # Queue nochmal leeren
        while not node.cmd_vel_queue.empty():
            try:
                node.cmd_vel_queue.get_nowait()
            except queue.Empty:
                break

        for i in range(samples):
            t_send = time.monotonic()
            await ws.send(
                json.dumps(
                    {
                        "op": "cmd_vel",
                        "linear_x": CMD_VEL_SPEED,
                        "angular_z": 0.0,
                    }
                )
            )
            await ws.send(json.dumps({"op": "heartbeat"}))

            # Warte auf passenden /cmd_vel mit linear_x > 0.01
            deadline = t_send + 0.5
            found = False
            while time.monotonic() < deadline:
                try:
                    t_recv, lin_x, ang_z = node.cmd_vel_queue.get(timeout=0.01)
                    if lin_x > 0.01 and t_recv >= t_send:
                        latencies.append((t_recv - t_send) * 1000.0)
                        found = True
                        break
                except queue.Empty:
                    pass

            if not found:
                node.get_logger().warn(f"  Sample {i + 1}: Timeout (kein /cmd_vel empfangen)")

            await asyncio.sleep(0.1)  # 10 Hz

        # Stopp senden
        await ws.send(json.dumps({"op": "cmd_vel", "linear_x": 0.0, "angular_z": 0.0}))

    if not latencies:
        return {
            "name": "cmd_vel_latenz",
            "result": "FAIL",
            "metrics": {"samples": 0, "fehler": "Keine Antworten empfangen"},
            "kriterien": {"p95_ms_max": LATENZ_P95_MAX_MS, "avg_ms_max": LATENZ_AVG_MAX_MS},
        }

    latencies.sort()
    avg_ms = statistics.mean(latencies)
    p95_ms = _percentile(latencies, 95)
    max_ms = max(latencies)
    min_ms = min(latencies)

    passed = p95_ms < LATENZ_P95_MAX_MS and avg_ms < LATENZ_AVG_MAX_MS
    result_str = "PASS" if passed else "FAIL"

    node.get_logger().info(
        f"  Latenz: avg={avg_ms:.1f} ms, p95={p95_ms:.1f} ms, "
        f"max={max_ms:.1f} ms, min={min_ms:.1f} ms ({len(latencies)}/{samples}) -> {result_str}"
    )

    return {
        "name": "cmd_vel_latenz",
        "result": result_str,
        "metrics": {
            "avg_ms": round(avg_ms, 1),
            "p95_ms": round(p95_ms, 1),
            "max_ms": round(max_ms, 1),
            "min_ms": round(min_ms, 1),
            "samples": len(latencies),
        },
        "kriterien": {"p95_ms_max": LATENZ_P95_MAX_MS, "avg_ms_max": LATENZ_AVG_MAX_MS},
    }


async def test_telemetrie_vollstaendigkeit(ws_url, node):
    """Test 5.2: Telemetrie-Vollstaendigkeit (alle Pflicht-Broadcasts)."""
    node.get_logger().info(f"Test 5.2: Telemetrie-Vollstaendigkeit ({TELEMETRIE_DAUER_S} s)...")

    op_counts = {}
    op_first_time = {}

    async with websockets.connect(ws_url) as ws:
        t_start = time.monotonic()
        deadline = t_start + TELEMETRIE_DAUER_S

        while time.monotonic() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                msg = json.loads(raw)
                op = msg.get("op", "unknown")
                now = time.monotonic()
                op_counts[op] = op_counts.get(op, 0) + 1
                if op not in op_first_time:
                    op_first_time[op] = now
            except asyncio.TimeoutError:
                continue

    elapsed = time.monotonic() - t_start if "t_start" in dir() else TELEMETRIE_DAUER_S
    elapsed = max(elapsed, 1.0)

    # Raten berechnen
    raten = {}
    for op, count in op_counts.items():
        raten[f"{op}_hz"] = round(count / elapsed, 1)

    # Pflicht-Typen pruefen
    empfangen = 0
    details = {}
    for pflicht_op, min_hz in PFLICHT_BROADCASTS.items():
        count = op_counts.get(pflicht_op, 0)
        hz = count / elapsed
        ok = hz >= min_hz * 0.5  # 50% des Soll-Werts als Minimum
        if ok:
            empfangen += 1
        details[pflicht_op] = {"count": count, "hz": round(hz, 1), "min_hz": min_hz, "ok": ok}

    erwartet = len(PFLICHT_BROADCASTS)
    passed = empfangen >= erwartet
    result_str = "PASS" if passed else "FAIL"

    node.get_logger().info(
        f"  Pflicht-Broadcasts: {empfangen}/{erwartet}, "
        f"Gesamt-Typen: {len(op_counts)} -> {result_str}"
    )
    for op, d in details.items():
        status = "OK" if d["ok"] else "FEHLT"
        node.get_logger().info(f"    {op}: {d['hz']} Hz (min {d['min_hz']} Hz) [{status}]")

    return {
        "name": "telemetrie_vollstaendigkeit",
        "result": result_str,
        "metrics": {
            "empfangen": empfangen,
            "erwartet": erwartet,
            "raten": raten,
            "details": details,
        },
        "kriterien": {"pflicht_typen": erwartet},
    }


async def test_deadman_timer(ws_url, node):
    """Test 5.3: Deadman-Timer — Stopp nach Heartbeat-Abbruch."""
    node.get_logger().info("Test 5.3: Deadman-Timer...")

    # Queue leeren
    while not node.cmd_vel_queue.empty():
        try:
            node.cmd_vel_queue.get_nowait()
        except queue.Empty:
            break

    async with websockets.connect(ws_url) as ws:
        # 3 s lang cmd_vel + Heartbeat senden
        t_end_drive = time.monotonic() + 3.0
        while time.monotonic() < t_end_drive:
            await ws.send(
                json.dumps(
                    {
                        "op": "cmd_vel",
                        "linear_x": CMD_VEL_SPEED,
                        "angular_z": 0.0,
                    }
                )
            )
            await ws.send(json.dumps({"op": "heartbeat"}))
            await asyncio.sleep(0.1)

        # Queue leeren — nur ab jetzt zaehlt
        while not node.cmd_vel_queue.empty():
            try:
                node.cmd_vel_queue.get_nowait()
            except queue.Empty:
                break

        # Stopp: Nichts mehr senden. Deadman-Timer (300 ms) soll Null-Twist erzeugen
        t_stop = time.monotonic()

        # Warte auf Null-Twist
        deadline = t_stop + 2.0
        stopp_ms = None
        while time.monotonic() < deadline:
            try:
                t_recv, lin_x, ang_z = node.cmd_vel_queue.get(timeout=0.01)
                if abs(lin_x) < 0.001 and abs(ang_z) < 0.001 and t_recv > t_stop:
                    stopp_ms = (t_recv - t_stop) * 1000.0
                    break
            except queue.Empty:
                pass

    if stopp_ms is None:
        result = {
            "name": "deadman_timer",
            "result": "FAIL",
            "metrics": {"fehler": "Kein Stopp-Twist empfangen"},
            "kriterien": {"stopp_ms_max": DEADMAN_STOPP_MAX_MS},
        }
    else:
        passed = stopp_ms < DEADMAN_STOPP_MAX_MS
        result = {
            "name": "deadman_timer",
            "result": "PASS" if passed else "FAIL",
            "metrics": {"stopp_ms": round(stopp_ms, 1)},
            "kriterien": {"stopp_ms_max": DEADMAN_STOPP_MAX_MS},
        }

    node.get_logger().info(
        f"  Deadman-Stopp: {stopp_ms:.1f} ms -> {result['result']}"
        if stopp_ms
        else "  Deadman-Stopp: TIMEOUT -> FAIL"
    )
    return result


async def test_audio_feedback(ws_url, node):
    """Test 5.4: Audio-Feedback — 4 Sound-Keys auf /audio/play."""
    node.get_logger().info("Test 5.4: Audio-Feedback...")

    with node.audio_lock:
        node.audio_received.clear()

    async with websockets.connect(ws_url) as ws:
        for key in AUDIO_KEYS:
            await ws.send(json.dumps({"op": "audio_play", "sound_key": key}))
            node.get_logger().info(f"  Sende: {key}")
            await asyncio.sleep(2.5)  # Warten auf Wiedergabe

    # Pruefen
    await asyncio.sleep(0.5)
    with node.audio_lock:
        received = list(node.audio_received)

    empfangen_keys = [k for k in AUDIO_KEYS if k in received]
    empfangen = len(empfangen_keys)
    passed = empfangen >= len(AUDIO_KEYS)
    result_str = "PASS" if passed else "FAIL"

    node.get_logger().info(f"  Audio-Keys empfangen: {empfangen}/{len(AUDIO_KEYS)} -> {result_str}")

    return {
        "name": "audio_feedback",
        "result": result_str,
        "metrics": {
            "empfangen": empfangen,
            "erwartet": len(AUDIO_KEYS),
            "keys": empfangen_keys,
        },
        "kriterien": {"keys_min": len(AUDIO_KEYS)},
    }


async def test_notaus(ws_url, node):
    """Test 5.5: Notaus — sofortiger Stopp durch 5x Null-Twist."""
    node.get_logger().info("Test 5.5: Notaus...")

    # Queue leeren
    while not node.cmd_vel_queue.empty():
        try:
            node.cmd_vel_queue.get_nowait()
        except queue.Empty:
            break

    async with websockets.connect(ws_url) as ws:
        # Fahrt starten
        for _ in range(20):  # 2 s bei 10 Hz
            await ws.send(
                json.dumps(
                    {
                        "op": "cmd_vel",
                        "linear_x": CMD_VEL_SPEED,
                        "angular_z": 0.0,
                    }
                )
            )
            await ws.send(json.dumps({"op": "heartbeat"}))
            await asyncio.sleep(0.1)

        # Queue leeren — nur ab jetzt zaehlt
        while not node.cmd_vel_queue.empty():
            try:
                node.cmd_vel_queue.get_nowait()
            except queue.Empty:
                break

        # Notaus: 5x Null-Twist (EmergencyStop-Pattern)
        t_notaus = time.monotonic()
        for _ in range(5):
            await ws.send(json.dumps({"op": "cmd_vel", "linear_x": 0.0, "angular_z": 0.0}))
            await ws.send(json.dumps({"op": "heartbeat"}))

        # Warte auf Null-Twist auf /cmd_vel
        deadline = t_notaus + 1.0
        stopp_ms = None
        while time.monotonic() < deadline:
            try:
                t_recv, lin_x, ang_z = node.cmd_vel_queue.get(timeout=0.01)
                if abs(lin_x) < 0.001 and abs(ang_z) < 0.001 and t_recv >= t_notaus:
                    stopp_ms = (t_recv - t_notaus) * 1000.0
                    break
            except queue.Empty:
                pass

    if stopp_ms is None:
        result = {
            "name": "notaus",
            "result": "FAIL",
            "metrics": {"fehler": "Kein Stopp-Twist empfangen"},
            "kriterien": {"stopp_ms_max": NOTAUS_STOPP_MAX_MS},
        }
    else:
        passed = stopp_ms < NOTAUS_STOPP_MAX_MS
        result = {
            "name": "notaus",
            "result": "PASS" if passed else "FAIL",
            "metrics": {"stopp_ms": round(stopp_ms, 1)},
            "kriterien": {"stopp_ms_max": NOTAUS_STOPP_MAX_MS},
        }

    node.get_logger().info(
        f"  Notaus-Stopp: {stopp_ms:.1f} ms -> {result['result']}"
        if stopp_ms
        else "  Notaus-Stopp: TIMEOUT -> FAIL"
    )
    return result


async def run_all_tests(ws_url, node, samples):
    """Fuehrt alle 5 Tests sequenziell aus."""
    tests = []

    tests.append(await test_cmd_vel_latenz(ws_url, node, samples))
    await asyncio.sleep(2.0)

    tests.append(await test_telemetrie_vollstaendigkeit(ws_url, node))
    await asyncio.sleep(2.0)

    tests.append(await test_deadman_timer(ws_url, node))
    await asyncio.sleep(2.0)

    tests.append(await test_audio_feedback(ws_url, node))
    await asyncio.sleep(2.0)

    tests.append(await test_notaus(ws_url, node))

    return tests


def print_summary(tests):
    """Druckt Zusammenfassung aller Tests."""
    all_passed = all(t["result"] == "PASS" for t in tests)

    print()
    print("=" * 60)
    print(f"  {ANSI_BOLD}Phase 5: Bedien- und Leitstandsebene{ANSI_RESET}")
    print("=" * 60)
    for t in tests:
        name = t["name"]
        result = t["result"]
        color = ANSI_GREEN if result == "PASS" else ANSI_RED
        metrics_str = ""
        m = t.get("metrics", {})
        if "avg_ms" in m:
            metrics_str = f"avg={m['avg_ms']} ms, p95={m['p95_ms']} ms"
        elif "stopp_ms" in m:
            metrics_str = f"{m['stopp_ms']} ms"
        elif "empfangen" in m and "erwartet" in m:
            metrics_str = f"{m['empfangen']}/{m['erwartet']}"
        print(f"  {name:30s} {color}{ANSI_BOLD}{result}{ANSI_RESET}  {metrics_str}")
    print("=" * 60)
    if all_passed:
        print(f"  {ANSI_GREEN}{ANSI_BOLD}PHASE 5: PASS{ANSI_RESET}")
    else:
        print(f"  {ANSI_RED}{ANSI_BOLD}PHASE 5: FAIL{ANSI_RESET}")
    print("=" * 60)


def main():
    if websockets is None:
        print(
            f"{ANSI_RED}Fehler: 'websockets' nicht installiert (pip install websockets){ANSI_RESET}"
        )
        return

    parser = argparse.ArgumentParser(
        description="Phase-5-Validierung: Dashboard-Latenz und Telemetrie"
    )
    parser.add_argument("--output", default=None, help="Ausgabeverzeichnis fuer JSON")
    parser.add_argument("--ws-url", default="ws://localhost:9090", help="WebSocket-URL")
    parser.add_argument("--samples", type=int, default=100, help="Anzahl Latenz-Messungen")
    args = parser.parse_args()

    print()
    print("*" * 60)
    print(f"  {ANSI_BOLD}AMR Phase 5: Bedien- und Leitstandsebene{ANSI_RESET}")
    print("*" * 60)
    print(
        f"\n{ANSI_CYAN}  Voraussetzung: use_dashboard:=True use_cliff_safety:=True use_audio:=True{ANSI_RESET}"
    )
    print(f"{ANSI_CYAN}  Roboter auf ebenem Boden, kein Hindernis < 80 mm{ANSI_RESET}\n")

    rclpy.init()
    node = DashboardTestNode()

    # ROS2 Spin in separatem Thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    # Kurz warten auf Subscriber-Verbindung
    time.sleep(1.0)

    try:
        loop = asyncio.new_event_loop()
        tests = loop.run_until_complete(run_all_tests(args.ws_url, node, args.samples))
        loop.close()
    except KeyboardInterrupt:
        node.get_logger().warn("Abgebrochen.")
        tests = []
    except Exception as e:
        node.get_logger().error(f"Fehler: {e}")
        tests = []
    finally:
        rclpy.shutdown()

    if not tests:
        print(f"\n{ANSI_RED}Keine Testergebnisse.{ANSI_RESET}")
        return

    print_summary(tests)

    # JSON speichern
    all_passed = all(t["result"] == "PASS" for t in tests)
    report = {
        "test_name": "dashboard_phase5",
        "timestamp": datetime.now().isoformat(),
        "tests": tests,
        "all_passed": all_passed,
    }

    if save_json is not None:
        pfad = save_json(report, "dashboard_results.json", args.output)
        print(f"\n  Ergebnisse: {pfad}")
    else:
        # Fallback ohne amr_utils
        out_dir = args.output or os.path.dirname(os.path.abspath(__file__))
        pfad = os.path.join(out_dir, "dashboard_results.json")
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  Ergebnisse: {pfad}")


if __name__ == "__main__":
    main()
