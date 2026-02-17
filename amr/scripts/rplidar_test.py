#!/usr/bin/env python3
"""
RPLidar-Validierungstool fuer den AMR-Roboter.
ROS2-Node: subscribt /scan und prueft TF, fuehrt 4 Tests durch:

  1. Konnektivitaet: Prueft ob Scan-Daten ankommen, misst Rate, prueft frame_id
  2. Scan-Rate-Stabilitaet: 300s Langzeittest mit 30s-Fenster-Analyse
  3. Datenqualitaet: Winkelaufloesung, gueltige Punkte, Rausch-Standardabweichung
  4. Statischer TF: Prueft base_link->laser Transformation gegen Sollwerte

Ergebnis: Terminal-Ausgabe mit PASS/FAIL + JSON-Protokoll.
"""

import sys
import os
import math
import time
import datetime
import statistics

try:
    from amr_utils import (
        quaternion_to_yaw, save_json,
        COLOR_GREEN, COLOR_RED, COLOR_CYAN, COLOR_BOLD, COLOR_RESET,
    )
except ImportError:
    from my_bot.amr_utils import (
        quaternion_to_yaw, save_json,
        COLOR_GREEN, COLOR_RED, COLOR_CYAN, COLOR_BOLD, COLOR_RESET,
    )

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
import tf2_ros


# ===========================================================================
# Konstanten
# ===========================================================================

SCAN_RATE_MIN_HZ = 5.0          # [Hz] Minimale Scan-Rate (RPLidar A1: ~7 Hz)
SCAN_RATE_DURATION_S = 300       # [s] Dauer des Langzeit-Rate-Tests
RANGE_MIN_M = 0.15              # [m] Minimale RPLidar-Reichweite
RANGE_MAX_M = 12.0              # [m] Maximale RPLidar-Reichweite
ANGULAR_RES_MAX_DEG = 1.5       # [deg] Maximale Winkelaufloesung
NOISE_STDDEV_MAX_M = 0.03       # [m] Maximale Rausch-Std auf statischen Zielen

# Erwartete statische TF base_link -> laser
EXPECTED_TF_X = 0.10            # [m] nach vorne
EXPECTED_TF_Y = 0.0             # [m] seitlich
EXPECTED_TF_Z = 0.05            # [m] nach oben
EXPECTED_TF_YAW = math.pi       # [rad] 180 Grad gedreht
TF_POS_TOL = 0.01               # [m] Positionstoleranz
TF_YAW_TOL_DEG = 3.0            # [deg] Yaw-Toleranz


# ===========================================================================
# ROS2-Node
# ===========================================================================

class RplidarTestNode(Node):
    """ROS2-Node fuer RPLidar-Validierung via /scan und TF."""

    def __init__(self):
        super().__init__("rplidar_test_node")

        # Subscriber
        self.scan_sub = self.create_subscription(
            LaserScan, "/scan", self._scan_callback, 10)

        # TF2
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Scan-Daten
        self.scan_received = False
        self.scan_timestamps = []
        self.scan_ranges = []       # Liste von Listen (pro Scan alle Ranges)
        self.angle_increment = None
        self.frame_id = None

        # Steuerung
        self.collecting_rate = False
        self.collecting_quality = False

        self.get_logger().info("RPLidar-Test-Node gestartet. Warte auf /scan...")

    def _scan_callback(self, msg):
        """Verarbeitet LaserScan-Nachrichten."""
        self.scan_received = True
        self.angle_increment = msg.angle_increment
        self.frame_id = msg.header.frame_id

        if self.collecting_rate:
            self.scan_timestamps.append(time.time())

        if self.collecting_quality:
            self.scan_timestamps.append(time.time())
            self.scan_ranges.append(list(msg.ranges))

    def wait_for_scan(self, timeout_s=10.0):
        """Wartet bis erste Scan-Nachricht empfangen wird."""
        start = time.time()
        while not self.scan_received:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start > timeout_s:
                return False
        return True

    def reset_collections(self):
        """Setzt alle Sammel-Listen zurueck."""
        self.scan_timestamps = []
        self.scan_ranges = []
        self.scan_received = False
        self.angle_increment = None
        self.frame_id = None


# ===========================================================================
# Test 1: Konnektivitaet
# ===========================================================================

def test_connectivity(node):
    """Prueft ob Scan-Daten ankommen, misst Rate und prueft frame_id."""
    print(f"\n{COLOR_BOLD}--- Test 1: Konnektivitaet ---{COLOR_RESET}")
    print("  Warte auf /scan Daten (max. 10s)...")

    if not node.wait_for_scan(timeout_s=10.0):
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(keine Scan-Daten innerhalb 10s)")
        return {"pass": False, "rate_hz": 0.0, "frame_id": None,
                "samples": 0, "reason": "timeout"}

    detected_frame = node.frame_id
    print(f"  /scan empfangen (frame_id: \"{detected_frame}\"). "
          f"Messe Scan-Rate (5s)...")

    node.scan_timestamps = []
    node.collecting_rate = True

    start = time.time()
    while time.time() - start < 5.0:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.collecting_rate = False

    n_samples = len(node.scan_timestamps)
    if n_samples < 2:
        rate_hz = 0.0
    else:
        duration = node.scan_timestamps[-1] - node.scan_timestamps[0]
        rate_hz = (n_samples - 1) / duration if duration > 0 else 0.0

    frame_ok = detected_frame == "laser"
    rate_ok = rate_hz >= SCAN_RATE_MIN_HZ
    passed = rate_ok and frame_ok

    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"
    print(f"  Samples: {n_samples}, Rate: {rate_hz:.1f} Hz "
          f"(Soll: >= {SCAN_RATE_MIN_HZ} Hz)")
    print(f"  frame_id: \"{detected_frame}\" "
          f"({'OK' if frame_ok else 'ERWARTET: laser'})")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "rate_hz": round(rate_hz, 1),
        "frame_id": detected_frame,
        "samples": n_samples,
    }


# ===========================================================================
# Test 2: Scan-Rate-Stabilitaet (300s Langzeittest)
# ===========================================================================

def test_scan_rate_stability(node):
    """300s Langzeittest: Scan-Rate in 30s-Fenstern analysieren."""
    print(f"\n{COLOR_BOLD}--- Test 2: Scan-Rate-Stabilitaet "
          f"({SCAN_RATE_DURATION_S}s) ---{COLOR_RESET}")
    print(f"  Sammle Scan-Timestamps fuer {SCAN_RATE_DURATION_S} Sekunden...")
    print(f"  Analyse in 30s-Fenstern. RPLidar darf nicht bewegt werden.\n")

    node.scan_timestamps = []
    node.collecting_rate = True

    start = time.time()
    last_print = 0

    while True:
        rclpy.spin_once(node, timeout_sec=0.05)
        elapsed = time.time() - start
        remaining = SCAN_RATE_DURATION_S - elapsed

        if remaining <= 0:
            break

        # Countdown alle 30 Sekunden
        elapsed_int = int(elapsed)
        if elapsed_int >= last_print + 30:
            last_print = elapsed_int
            print(f"  {COLOR_CYAN}[{int(remaining)}s verbleibend]{COLOR_RESET} "
                  f"Scans bisher: {len(node.scan_timestamps)}")

    node.collecting_rate = False

    timestamps = node.scan_timestamps
    total_scans = len(timestamps)

    if total_scans < 20:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(zu wenige Scans: {total_scans})")
        return {"pass": False, "mean_rate_hz": 0.0,
                "reason": "insufficient_scans", "total_scans": total_scans}

    # Intervalle berechnen
    intervals = [timestamps[i+1] - timestamps[i]
                 for i in range(len(timestamps) - 1)]
    std_interval_ms = statistics.stdev(intervals) * 1000.0 if len(intervals) > 1 else 0.0

    # Gesamt-Rate
    total_duration = timestamps[-1] - timestamps[0]
    mean_rate_hz = (total_scans - 1) / total_duration if total_duration > 0 else 0.0

    # 30s-Fenster-Analyse
    window_size = 30.0
    window_rates = []
    t0 = timestamps[0]

    window_start_idx = 0
    for window_num in range(int(total_duration / window_size)):
        w_start = t0 + window_num * window_size
        w_end = w_start + window_size

        # Scans in diesem Fenster zaehlen
        count = sum(1 for t in timestamps if w_start <= t < w_end)
        if count >= 2:
            window_rates.append(count / window_size)

    if not window_rates:
        # Fallback: Gesamtrate als einziges Fenster
        window_rates = [mean_rate_hz]

    min_window = min(window_rates)
    max_window = max(window_rates)

    passed = mean_rate_hz >= SCAN_RATE_MIN_HZ and min_window >= SCAN_RATE_MIN_HZ
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"\n  Gesamtdauer: {total_duration:.1f}s, Scans: {total_scans}")
    print(f"  Mittlere Rate: {mean_rate_hz:.2f} Hz "
          f"(Soll: >= {SCAN_RATE_MIN_HZ} Hz)")
    print(f"  Fenster-Raten (30s): min={min_window:.2f} Hz, "
          f"max={max_window:.2f} Hz ({len(window_rates)} Fenster)")
    print(f"  Intervall-Std: {std_interval_ms:.2f} ms")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "mean_rate_hz": round(mean_rate_hz, 2),
        "min_window_rate_hz": round(min_window, 2),
        "max_window_rate_hz": round(max_window, 2),
        "std_interval_ms": round(std_interval_ms, 2),
        "duration_s": round(total_duration, 1),
        "total_scans": total_scans,
    }


# ===========================================================================
# Test 3: Datenqualitaet
# ===========================================================================

def test_data_quality(node):
    """Prueft Winkelaufloesung, gueltige Punkte und Rausch-Standardabweichung."""
    print(f"\n{COLOR_BOLD}--- Test 3: Datenqualitaet (30s) ---{COLOR_RESET}")
    print("  RPLidar muss stillstehen. Sammle 30s Scan-Daten...\n")

    node.scan_timestamps = []
    node.scan_ranges = []
    node.collecting_quality = True

    start = time.time()
    last_print = 0

    while True:
        rclpy.spin_once(node, timeout_sec=0.05)
        elapsed = time.time() - start
        remaining = 30.0 - elapsed

        if remaining <= 0:
            break

        elapsed_int = int(elapsed)
        if elapsed_int >= last_print + 10:
            last_print = elapsed_int
            print(f"  {COLOR_CYAN}[{int(remaining)}s verbleibend]{COLOR_RESET} "
                  f"Scans: {len(node.scan_ranges)}")

    node.collecting_quality = False

    n_scans = len(node.scan_ranges)
    if n_scans < 5:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(zu wenige Scans: {n_scans})")
        return {"pass": False, "reason": "insufficient_scans", "samples": n_scans}

    # Winkelaufloesung
    angular_res_deg = math.degrees(node.angle_increment) if node.angle_increment else 0.0

    # Gueltige Punkte: Anteil der nicht-inf/nan Werte im letzten Scan
    all_valid_pcts = []
    for ranges in node.scan_ranges:
        total = len(ranges)
        if total == 0:
            continue
        valid = sum(1 for r in ranges
                    if math.isfinite(r) and RANGE_MIN_M <= r <= RANGE_MAX_M)
        all_valid_pcts.append(100.0 * valid / total)

    valid_pct = statistics.mean(all_valid_pcts) if all_valid_pcts else 0.0

    # Noise: Pro Winkel-Index die Standardabweichung berechnen
    # Nur Bins mit >= 80% gueltigen Werten einbeziehen
    n_bins = len(node.scan_ranges[0]) if node.scan_ranges else 0
    bin_stddevs = []
    min_valid_ratio = 0.80

    for i in range(n_bins):
        values = []
        for ranges in node.scan_ranges:
            if i < len(ranges):
                r = ranges[i]
                if math.isfinite(r) and RANGE_MIN_M <= r <= RANGE_MAX_M:
                    values.append(r)

        if len(values) >= n_scans * min_valid_ratio and len(values) >= 2:
            bin_stddevs.append(statistics.stdev(values))

    # Median der Bin-Standardabweichungen als Rausch-Mass
    if bin_stddevs:
        noise_stddev = statistics.median(bin_stddevs)
    else:
        noise_stddev = float('inf')

    res_ok = angular_res_deg <= ANGULAR_RES_MAX_DEG
    noise_ok = noise_stddev <= NOISE_STDDEV_MAX_M
    passed = res_ok and noise_ok

    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"\n  Scans: {n_scans}, Bins pro Scan: {n_bins}")
    print(f"  Winkelaufloesung: {angular_res_deg:.3f} deg "
          f"(Soll: <= {ANGULAR_RES_MAX_DEG} deg) "
          f"{'OK' if res_ok else 'FAIL'}")
    print(f"  Gueltige Punkte: {valid_pct:.1f}%")
    print(f"  Rausch-Std (Median): {noise_stddev:.4f} m "
          f"(Soll: <= {NOISE_STDDEV_MAX_M} m) "
          f"{'OK' if noise_ok else 'FAIL'}")
    print(f"  Bins fuer Noise-Analyse: {len(bin_stddevs)}/{n_bins}")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "angular_resolution_deg": round(angular_res_deg, 3),
        "valid_points_pct": round(valid_pct, 1),
        "noise_stddev_m": round(noise_stddev, 4) if math.isfinite(noise_stddev) else None,
        "samples": n_scans,
    }


# ===========================================================================
# Test 4: Statischer TF (base_link -> laser)
# ===========================================================================

def test_static_tf(node):
    """Prueft die statische Transformation base_link -> laser."""
    print(f"\n{COLOR_BOLD}--- Test 4: Statischer TF (base_link -> laser) ---{COLOR_RESET}")
    print("  Pruefe TF-Baum...")

    # Kurz warten damit TF-Buffer gefuellt ist
    for _ in range(20):
        rclpy.spin_once(node, timeout_sec=0.1)

    try:
        trans = node.tf_buffer.lookup_transform(
            "base_link", "laser", Time())
    except (tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException) as e:
        print(f"  TF-Lookup fehlgeschlagen: {e}")
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET}")
        return {"pass": False, "reason": f"tf_error: {e}"}

    tx = trans.transform.translation.x
    ty = trans.transform.translation.y
    tz = trans.transform.translation.z
    yaw = quaternion_to_yaw(trans.transform.rotation)
    yaw_deg = math.degrees(yaw)

    # Fehler berechnen
    dx = tx - EXPECTED_TF_X
    dy = ty - EXPECTED_TF_Y
    dz = tz - EXPECTED_TF_Z
    translation_error = math.sqrt(dx*dx + dy*dy + dz*dz)

    # Yaw-Fehler: Differenz normalisieren
    yaw_diff = yaw - EXPECTED_TF_YAW
    while yaw_diff > math.pi:
        yaw_diff -= 2.0 * math.pi
    while yaw_diff < -math.pi:
        yaw_diff += 2.0 * math.pi
    yaw_error_deg = abs(math.degrees(yaw_diff))

    pos_ok = translation_error < TF_POS_TOL
    yaw_ok = yaw_error_deg < TF_YAW_TOL_DEG
    passed = pos_ok and yaw_ok

    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"  Translation: x={tx:.3f}, y={ty:.3f}, z={tz:.3f} m")
    print(f"  Erwartet:    x={EXPECTED_TF_X:.3f}, y={EXPECTED_TF_Y:.3f}, "
          f"z={EXPECTED_TF_Z:.3f} m")
    print(f"  Translationsfehler: {translation_error:.4f} m "
          f"(Soll: < {TF_POS_TOL} m) "
          f"{'OK' if pos_ok else 'FAIL'}")
    print(f"  Yaw: {yaw_deg:.1f} deg (Erwartet: {math.degrees(EXPECTED_TF_YAW):.1f} deg)")
    print(f"  Yaw-Fehler: {yaw_error_deg:.2f} deg "
          f"(Soll: < {TF_YAW_TOL_DEG} deg) "
          f"{'OK' if yaw_ok else 'FAIL'}")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "translation": {
            "x": round(tx, 3),
            "y": round(ty, 3),
            "z": round(tz, 3),
        },
        "yaw_deg": round(yaw_deg, 1),
        "translation_error_m": round(translation_error, 4),
        "yaw_error_deg": round(yaw_error_deg, 2),
    }


# ===========================================================================
# Hauptprogramm
# ===========================================================================

def main(args=None):
    rclpy.init(args=args)

    print()
    print("*" * 60)
    print("  AMR RPLidar-Validierungstool")
    print("  ROS2-Node: rplidar_test_node")
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"  Zeitpunkt: {ts}")
    print("*" * 60)

    node = RplidarTestNode()

    # Test 1: Konnektivitaet (Abbruch bei FAIL)
    result_conn = test_connectivity(node)
    if not result_conn["pass"]:
        print(f"\n{COLOR_RED}ABBRUCH: RPLidar nicht erreichbar. "
              f"Weitere Tests uebersprungen.{COLOR_RESET}")
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "connectivity": result_conn,
            "scan_rate_stability": {"pass": False, "reason": "skipped"},
            "data_quality": {"pass": False, "reason": "skipped"},
            "static_tf": {"pass": False, "reason": "skipped"},
            "overall_pass": False,
        }
        pfad = save_json(results, "rplidar_results.json")
        print(f"\n  Ergebnisse gespeichert: {pfad}")
        node.destroy_node()
        rclpy.shutdown()
        return 1

    # Test 2: Scan-Rate-Stabilitaet
    result_rate = test_scan_rate_stability(node)

    # Test 3: Datenqualitaet
    result_quality = test_data_quality(node)

    # Test 4: Statischer TF
    result_tf = test_static_tf(node)

    # Gesamtergebnis
    all_passed = all([
        result_conn["pass"],
        result_rate["pass"],
        result_quality["pass"],
        result_tf["pass"],
    ])

    print("\n" + "=" * 60)
    if all_passed:
        print(f"  {COLOR_GREEN}{COLOR_BOLD}GESAMTERGEBNIS: BESTANDEN "
              f"(4/4 Tests){COLOR_RESET}")
    else:
        n_pass = sum(1 for r in [result_conn, result_rate,
                                  result_quality, result_tf] if r["pass"])
        print(f"  {COLOR_RED}{COLOR_BOLD}GESAMTERGEBNIS: NICHT BESTANDEN "
              f"({n_pass}/4 Tests){COLOR_RESET}")
    print("=" * 60)

    # JSON speichern
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "connectivity": result_conn,
        "scan_rate_stability": result_rate,
        "data_quality": result_quality,
        "static_tf": result_tf,
        "overall_pass": all_passed,
    }
    pfad = save_json(results, "rplidar_results.json")
    print(f"\n  Ergebnisse gespeichert: {pfad}")

    node.destroy_node()
    rclpy.shutdown()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
