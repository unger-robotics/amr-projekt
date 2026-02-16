#!/usr/bin/env python3
"""
IMU-Validierungstool fuer den AMR-Roboter.
ROS2-Node: subscribt /imu und /odom, fuehrt 4 Tests durch:

  1. Konnektivitaet: Prueft ob IMU-Daten ankommen und misst Sample-Rate
  2. Gyro-Drift: 60s statisch, misst kumulative Drift in deg/min
  3. Accel-Bias: 5s Mittelung von az, Abweichung von 9.81 m/s²
  4. Heading-Vergleich: Vergleicht IMU-Yaw mit Odom-Yaw bei Stillstand

Ergebnis: Terminal-Ausgabe mit PASS/FAIL + JSON-Protokoll.
"""

import sys
import os
import math
import time
import datetime

try:
    from amr_utils import (
        quaternion_to_yaw, save_json, normalize_angle,
        COLOR_GREEN, COLOR_RED, COLOR_CYAN, COLOR_BOLD, COLOR_RESET,
        IMU_PUBLISH_HZ, IMU_GYRO_DRIFT_MAX, IMU_ACCEL_BIAS_MAX,
    )
except ImportError:
    from my_bot.amr_utils import (
        quaternion_to_yaw, save_json, normalize_angle,
        COLOR_GREEN, COLOR_RED, COLOR_CYAN, COLOR_BOLD, COLOR_RESET,
        IMU_PUBLISH_HZ, IMU_GYRO_DRIFT_MAX, IMU_ACCEL_BIAS_MAX,
    )

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry


# ===========================================================================
# Konstanten
# ===========================================================================

GRAVITY = 9.81  # [m/s²]
HEADING_DIFF_MAX = 5.0  # [deg] Akzeptanzgrenze fuer Heading-Vergleich


# ===========================================================================
# ROS2-Node
# ===========================================================================

class ImuTestNode(Node):
    """ROS2-Node fuer IMU-Validierung via /imu und /odom."""

    def __init__(self):
        super().__init__("imu_test_node")

        # Subscriber
        self.imu_sub = self.create_subscription(
            Imu, "/imu", self._imu_callback, 10)
        self.odom_sub = self.create_subscription(
            Odometry, "/odom", self._odom_callback, 10)

        # IMU-Daten
        self.imu_received = False
        self.imu_timestamps = []
        self.gyro_z_samples = []
        self.accel_z_samples = []
        self.imu_yaw = None

        # Odom-Daten
        self.odom_received = False
        self.odom_yaw = None

        # Steuerung
        self.collecting_rate = False
        self.collecting_gyro = False
        self.collecting_accel = False
        self.collecting_heading = False

        self.get_logger().info("IMU-Test-Node gestartet. Warte auf /imu...")

    def _imu_callback(self, msg):
        """Verarbeitet IMU-Nachrichten."""
        self.imu_received = True

        if self.collecting_rate:
            self.imu_timestamps.append(time.time())

        if self.collecting_gyro:
            self.gyro_z_samples.append(msg.angular_velocity.z)

        if self.collecting_accel:
            self.accel_z_samples.append(msg.linear_acceleration.z)

        if self.collecting_heading:
            self.imu_yaw = quaternion_to_yaw(msg.orientation)

    def _odom_callback(self, msg):
        """Verarbeitet Odometrie-Nachrichten."""
        self.odom_received = True

        if self.collecting_heading:
            self.odom_yaw = quaternion_to_yaw(msg.pose.pose.orientation)

    def wait_for_imu(self, timeout_s=5.0):
        """Wartet bis erste IMU-Nachricht empfangen wird."""
        start = time.time()
        while not self.imu_received:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start > timeout_s:
                return False
        return True

    def reset_collections(self):
        """Setzt alle Sammel-Listen zurueck."""
        self.imu_timestamps = []
        self.gyro_z_samples = []
        self.accel_z_samples = []
        self.imu_yaw = None
        self.odom_yaw = None


# ===========================================================================
# Test 1: Konnektivitaet
# ===========================================================================

def test_connectivity(node):
    """Prueft ob IMU-Daten ankommen und misst die Sample-Rate."""
    print(f"\n{COLOR_BOLD}--- Test 1: Konnektivitaet ---{COLOR_RESET}")
    print("  Warte auf /imu Daten (max. 5s)...")

    if not node.wait_for_imu(timeout_s=5.0):
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(keine IMU-Daten innerhalb 5s)")
        return {"pass": False, "rate_hz": 0.0, "reason": "timeout"}

    print("  /imu empfangen. Messe Sample-Rate (3s)...")

    node.reset_collections()
    node.collecting_rate = True

    start = time.time()
    while time.time() - start < 3.0:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.collecting_rate = False

    n_samples = len(node.imu_timestamps)
    if n_samples < 2:
        rate_hz = 0.0
    else:
        duration = node.imu_timestamps[-1] - node.imu_timestamps[0]
        rate_hz = (n_samples - 1) / duration if duration > 0 else 0.0

    passed = rate_hz >= 15.0
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"
    print(f"  Samples: {n_samples}, Rate: {rate_hz:.1f} Hz (Soll: >= 15 Hz)")
    print(f"  Ergebnis: {status}")

    return {"pass": passed, "rate_hz": round(rate_hz, 1), "samples": n_samples}


# ===========================================================================
# Test 2: Gyro-Drift
# ===========================================================================

def test_gyro_drift(node):
    """Misst kumulative Gyro-Drift bei Stillstand ueber 60 Sekunden."""
    print(f"\n{COLOR_BOLD}--- Test 2: Gyro-Drift (60s statisch) ---{COLOR_RESET}")
    print("  Roboter muss STILLSTEHEN. Nicht beruehren!")
    print("  Sammle angular_velocity.z fuer 60 Sekunden...\n")

    node.reset_collections()
    node.collecting_gyro = True

    duration_s = 60
    start = time.time()
    last_print = 0

    while True:
        rclpy.spin_once(node, timeout_sec=0.05)
        elapsed = time.time() - start
        remaining = duration_s - elapsed

        if remaining <= 0:
            break

        # Countdown alle 10 Sekunden
        elapsed_int = int(elapsed)
        if elapsed_int >= last_print + 10:
            last_print = elapsed_int
            print(f"  {COLOR_CYAN}[{int(remaining)}s verbleibend]{COLOR_RESET} "
                  f"Samples: {len(node.gyro_z_samples)}")

    node.collecting_gyro = False

    if len(node.gyro_z_samples) < 10:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(zu wenige Samples: {len(node.gyro_z_samples)})")
        return {"pass": False, "drift_deg_per_min": 0.0,
                "reason": "insufficient_samples",
                "samples": len(node.gyro_z_samples)}

    # Kumulative Drift berechnen: Summe(gz * dt) in rad, dann in deg/min
    # Bei gleichmaessiger Abtastrate: Summe(gz) * dt_avg
    total_samples = len(node.gyro_z_samples)
    dt_avg = duration_s / total_samples
    cumulative_rad = sum(node.gyro_z_samples) * dt_avg
    drift_deg = abs(math.degrees(cumulative_rad))
    drift_deg_per_min = drift_deg  # 60s = 1 Minute

    mean_gz = sum(node.gyro_z_samples) / total_samples
    std_gz = math.sqrt(
        sum((g - mean_gz) ** 2 for g in node.gyro_z_samples) / total_samples
    )

    passed = drift_deg_per_min < IMU_GYRO_DRIFT_MAX
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"\n  Samples: {total_samples}")
    print(f"  Mittlerer gz: {mean_gz:.6f} rad/s (Std: {std_gz:.6f})")
    print(f"  Kumulative Drift: {drift_deg_per_min:.3f} deg/min "
          f"(Grenze: < {IMU_GYRO_DRIFT_MAX} deg/min)")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "drift_deg_per_min": round(drift_deg_per_min, 3),
        "mean_gz_rad_s": round(mean_gz, 6),
        "std_gz_rad_s": round(std_gz, 6),
        "samples": total_samples,
    }


# ===========================================================================
# Test 3: Accelerometer-Bias
# ===========================================================================

def test_accel_bias(node):
    """Misst Abweichung von az gegenueber Schwerkraft bei Stillstand."""
    print(f"\n{COLOR_BOLD}--- Test 3: Accelerometer-Bias (5s) ---{COLOR_RESET}")
    print("  Roboter muss STILLSTEHEN. az sollte ~9.81 m/s² sein.")
    print("  Mittele ueber 5 Sekunden...\n")

    node.reset_collections()
    node.collecting_accel = True

    start = time.time()
    while time.time() - start < 5.0:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.collecting_accel = False

    if len(node.accel_z_samples) < 10:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(zu wenige Samples: {len(node.accel_z_samples)})")
        return {"pass": False, "bias_m_s2": 0.0,
                "reason": "insufficient_samples",
                "samples": len(node.accel_z_samples)}

    mean_az = sum(node.accel_z_samples) / len(node.accel_z_samples)
    bias = abs(mean_az - GRAVITY)

    std_az = math.sqrt(
        sum((a - mean_az) ** 2 for a in node.accel_z_samples)
        / len(node.accel_z_samples)
    )

    passed = bias < IMU_ACCEL_BIAS_MAX
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"  Samples: {len(node.accel_z_samples)}")
    print(f"  Mittlerer az: {mean_az:.4f} m/s² (Std: {std_az:.4f})")
    print(f"  Bias: |{mean_az:.4f} - {GRAVITY}| = {bias:.4f} m/s² "
          f"(Grenze: < {IMU_ACCEL_BIAS_MAX} m/s²)")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "mean_az_m_s2": round(mean_az, 4),
        "bias_m_s2": round(bias, 4),
        "std_az_m_s2": round(std_az, 4),
        "samples": len(node.accel_z_samples),
    }


# ===========================================================================
# Test 4: Heading-Vergleich
# ===========================================================================

def test_heading_comparison(node):
    """Vergleicht IMU-Yaw mit Odom-Yaw bei Stillstand."""
    print(f"\n{COLOR_BOLD}--- Test 4: Heading-Vergleich (5s) ---{COLOR_RESET}")
    print("  Vergleicht IMU-Orientation mit Odom-Orientation bei Stillstand.")

    if not node.odom_received:
        print("  Warte auf /odom (max. 5s)...")
        start = time.time()
        while not node.odom_received:
            rclpy.spin_once(node, timeout_sec=0.1)
            if time.time() - start > 5.0:
                print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
                      f"(keine /odom Daten)")
                return {"pass": False, "reason": "no_odom"}

    print("  Sammle Heading-Daten (5s)...\n")

    node.reset_collections()
    node.collecting_heading = True

    imu_yaws = []
    odom_yaws = []

    start = time.time()
    while time.time() - start < 5.0:
        rclpy.spin_once(node, timeout_sec=0.05)
        if node.imu_yaw is not None and node.odom_yaw is not None:
            imu_yaws.append(node.imu_yaw)
            odom_yaws.append(node.odom_yaw)

    node.collecting_heading = False

    if len(imu_yaws) < 10:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} "
              f"(zu wenige Samples: {len(imu_yaws)})")
        return {"pass": False, "reason": "insufficient_samples",
                "samples": len(imu_yaws)}

    mean_imu_yaw = sum(imu_yaws) / len(imu_yaws)
    mean_odom_yaw = sum(odom_yaws) / len(odom_yaws)

    diff_rad = normalize_angle(mean_imu_yaw - mean_odom_yaw)
    diff_deg = abs(math.degrees(diff_rad))

    passed = diff_deg < HEADING_DIFF_MAX
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"  Samples: {len(imu_yaws)}")
    print(f"  IMU-Yaw (Mittel): {math.degrees(mean_imu_yaw):.2f} deg")
    print(f"  Odom-Yaw (Mittel): {math.degrees(mean_odom_yaw):.2f} deg")
    print(f"  Differenz: {diff_deg:.2f} deg (Grenze: < {HEADING_DIFF_MAX} deg)")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "imu_yaw_deg": round(math.degrees(mean_imu_yaw), 2),
        "odom_yaw_deg": round(math.degrees(mean_odom_yaw), 2),
        "diff_deg": round(diff_deg, 2),
        "samples": len(imu_yaws),
    }


# ===========================================================================
# Hauptprogramm
# ===========================================================================

def main(args=None):
    rclpy.init(args=args)

    print()
    print("*" * 60)
    print("  AMR IMU-Validierungstool")
    print("  ROS2-Node: imu_test_node")
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"  Zeitpunkt: {ts}")
    print("*" * 60)

    node = ImuTestNode()

    # Test 1: Konnektivitaet
    result_conn = test_connectivity(node)
    if not result_conn["pass"]:
        print(f"\n{COLOR_RED}ABBRUCH: IMU nicht erreichbar. "
              f"Weitere Tests uebersprungen.{COLOR_RESET}")
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "connectivity": result_conn,
            "gyro_drift": {"pass": False, "reason": "skipped"},
            "accel_bias": {"pass": False, "reason": "skipped"},
            "heading_comparison": {"pass": False, "reason": "skipped"},
            "overall_pass": False,
        }
        pfad = save_json(results, "imu_results.json")
        print(f"\n  Ergebnisse gespeichert: {pfad}")
        node.destroy_node()
        rclpy.shutdown()
        return 1

    # Test 2: Gyro-Drift
    result_gyro = test_gyro_drift(node)

    # Test 3: Accel-Bias
    result_accel = test_accel_bias(node)

    # Test 4: Heading-Vergleich
    result_heading = test_heading_comparison(node)

    # Gesamtergebnis
    all_passed = all([
        result_conn["pass"],
        result_gyro["pass"],
        result_accel["pass"],
        result_heading["pass"],
    ])

    print("\n" + "=" * 60)
    if all_passed:
        print(f"  {COLOR_GREEN}{COLOR_BOLD}GESAMTERGEBNIS: BESTANDEN "
              f"(4/4 Tests){COLOR_RESET}")
    else:
        n_pass = sum(1 for r in [result_conn, result_gyro,
                                  result_accel, result_heading] if r["pass"])
        print(f"  {COLOR_RED}{COLOR_BOLD}GESAMTERGEBNIS: NICHT BESTANDEN "
              f"({n_pass}/4 Tests){COLOR_RESET}")
    print("=" * 60)

    # JSON speichern
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "connectivity": result_conn,
        "gyro_drift": result_gyro,
        "accel_bias": result_accel,
        "heading_comparison": result_heading,
        "overall_pass": all_passed,
    }
    pfad = save_json(results, "imu_results.json")
    print(f"\n  Ergebnisse gespeichert: {pfad}")

    node.destroy_node()
    rclpy.shutdown()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
