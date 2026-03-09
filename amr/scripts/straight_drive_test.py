#!/usr/bin/env python3
"""Geradeausfahrt-Test mit optionaler IMU-Heading-Korrektur.

Faehrt exakt 1m geradeaus (Closed-Loop auf Odom-Distanz) und vergleicht
die Ergebnisse mit und ohne IMU-basierter Heading-Korrektur.

Vor dem Fahrtstart wird 2s Gyro-Bias gemessen (Roboter muss stillstehen).

Verwendung:
    ros2 run my_bot straight_drive_test              # Beide Tests
    ros2 run my_bot straight_drive_test corrected     # Nur mit Korrektur
    ros2 run my_bot straight_drive_test uncorrected   # Nur ohne Korrektur
"""

import math
import os
import sys
import time
from datetime import datetime

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu

try:
    from amr_utils import ANSI_BOLD, ANSI_CYAN, ANSI_GREEN, ANSI_RED, ANSI_RESET, save_json
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

        def save_json(data, dateiname, verzeichnis=None):
            """Fallback wenn amr_utils nicht verfuegbar."""
            import json

            if verzeichnis is None:
                verzeichnis = os.path.dirname(os.path.abspath(__file__))
            pfad = os.path.join(verzeichnis, dateiname)
            with open(pfad, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return pfad


# Akzeptanzkriterien
AKZEPTANZ_DRIFT_CM = 5.0  # Lateraldrift < 5 cm
AKZEPTANZ_HEADING_DEG = 5.0  # Heading-Fehler < 5 Grad


def quaternion_to_yaw(q):
    """Quaternion zu Yaw-Winkel (rad)."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class StraightDriveTest(Node):
    def __init__(self, use_correction=True):
        super().__init__("straight_drive_test")

        self.use_correction = use_correction

        # Fahrparameter
        self.target_speed = 0.1  # m/s
        self.target_distance = 1.0  # m (Closed-Loop auf Odom)
        self.timeout = 20.0  # Sekunden Safety-Timeout

        # Heading-Korrektur P-Regler
        self.heading_kp = 0.5
        self.max_correction = 0.05  # rad/s max Korrektur

        # Gyro-Bias-Kalibrierung (3s statisch)
        self.calibrating = True
        self.cal_samples = []
        self.cal_duration = 3.0
        self.gyro_bias = 0.0
        self.max_acceptable_bias = math.radians(7.0)  # > 7 deg/s = Warnung

        # Zustand — Gyro-Integration (bias-korrigiert)
        self.gyro_heading = 0.0
        self.last_imu_stamp = None

        # Odom-Zustand
        self.start_x = None
        self.start_y = None
        self.start_yaw = None
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.forward_distance = 0.0

        # Ergebnis
        self.result = None

        # Steuerung
        self.running = False
        self.done = False
        self.settling = False
        self.stop_time = 0.0
        self.start_time = None
        self.last_log_sec = -1
        self.prev_forward = 0.0
        self.stable_count = 0

        # ROS2
        self.pub_cmd = self.create_publisher(Twist, "/cmd_vel", 10)
        self.sub_imu = self.create_subscription(Imu, "/imu", self.imu_callback, 10)
        self.sub_odom = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)

        mode = "MIT" if use_correction else "OHNE"
        self.get_logger().info(f"Geradeausfahrt 1m {mode} IMU-Heading-Korrektur")
        self.get_logger().info("Gyro-Kalibrierung (3s still stehen)...")

    def imu_callback(self, msg):
        now = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        gz = msg.angular_velocity.z

        if self.last_imu_stamp is None:
            self.last_imu_stamp = now
            return

        dt = now - self.last_imu_stamp
        self.last_imu_stamp = now

        if dt <= 0 or dt > 0.5:
            return

        # Phase 1: Gyro-Bias-Kalibrierung
        if self.calibrating:
            self.cal_samples.append(gz)
            if len(self.cal_samples) >= int(self.cal_duration * 20):
                self.gyro_bias = sum(self.cal_samples) / len(self.cal_samples)
                bias_dps = math.degrees(self.gyro_bias)
                self.calibrating = False
                self.get_logger().info(
                    f"Gyro-Bias: {bias_dps:+.3f} deg/s ({len(self.cal_samples)} Samples)"
                )
                if abs(self.gyro_bias) > self.max_acceptable_bias:
                    self.get_logger().warn(
                        "Gyro-Bias zu hoch! Roboter stand nicht still. Wiederhole Kalibrierung..."
                    )
                    self.cal_samples.clear()
                    self.calibrating = True
                    return
                self.get_logger().info("Warte auf /odom...")
            return

        if not self.running or self.done or self.settling:
            return

        if self.start_time is None or self.start_yaw is None:
            return

        # Gyro-Integration (bias-korrigiert)
        self.gyro_heading += (gz - self.gyro_bias) * dt

        # Geschwindigkeit: Bremsrampe ab 95% der Zielstrecke
        remaining = self.target_distance - self.forward_distance
        decel_zone = self.target_distance * 0.05  # letzte 5% = 5cm
        if remaining < decel_zone and decel_zone > 0:
            # Linear von target_speed auf min_speed (30%)
            speed = self.target_speed * (0.3 + 0.7 * remaining / decel_zone)
        else:
            speed = self.target_speed

        twist = Twist()
        twist.linear.x = speed

        if self.use_correction:
            corr = -self.heading_kp * self.gyro_heading
            corr = max(-self.max_correction, min(corr, self.max_correction))
            twist.angular.z = corr

        self.pub_cmd.publish(twist)

        # Status alle 2s
        elapsed = time.time() - self.start_time
        sec = int(elapsed)
        if sec % 2 == 0 and sec != self.last_log_sec and sec > 0:
            self.last_log_sec = sec
            heading_deg = math.degrees(self.gyro_heading)
            corr_val = twist.angular.z if self.use_correction else 0.0
            self.get_logger().info(
                f"  {elapsed:.0f}s | Dist: {self.forward_distance:.3f}m "
                f"| Heading: {heading_deg:+.2f} Grad "
                f"| Korrektur: {corr_val:+.3f} rad/s"
            )

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        self.current_yaw = quaternion_to_yaw(msg.pose.pose.orientation)

        if self.start_x is None:
            self.start_x = self.current_x
            self.start_y = self.current_y
            self.start_yaw = self.current_yaw

        # Starte Fahrt sobald Kalibrierung fertig
        if not self.running and not self.calibrating:
            self.running = True
            self.gyro_heading = 0.0
            self.start_x = self.current_x
            self.start_y = self.current_y
            self.start_yaw = self.current_yaw
            self.start_time = time.time()
            mode = "MIT" if self.use_correction else "OHNE"
            self.get_logger().info(f"Fahrt gestartet! ({mode} Korrektur)")
            return

        if self.done:
            return

        # Nach Stopp: warten bis Odom sich nicht mehr aendert
        if self.settling:
            if (
                self.start_x is None
                or self.start_y is None
                or self.start_yaw is None
                or self.start_time is None
            ):
                return
            dx = self.current_x - self.start_x
            dy = self.current_y - self.start_y
            self.forward_distance = dx * math.cos(self.start_yaw) + dy * math.sin(self.start_yaw)
            elapsed = time.time() - self.start_time

            # Stillstand: Odom-Aenderung < 0.5mm fuer 5 Zyklen (~250ms)
            if abs(self.forward_distance - self.prev_forward) < 0.0005:
                self.stable_count += 1
            else:
                self.stable_count = 0
            self.prev_forward = self.forward_distance

            if self.stable_count >= 5 or elapsed - self.stop_time >= 2.0:
                self.done = True
                self.print_result(elapsed)
            return

        if not self.running:
            return

        if (
            self.start_x is None
            or self.start_y is None
            or self.start_yaw is None
            or self.start_time is None
        ):
            return

        # Vorwaertsstrecke im Roboter-Koerperkoordinatensystem
        dx = self.current_x - self.start_x
        dy = self.current_y - self.start_y
        self.forward_distance = dx * math.cos(self.start_yaw) + dy * math.sin(self.start_yaw)

        elapsed = time.time() - self.start_time

        # Ziel erreicht?
        if self.forward_distance >= self.target_distance:
            self.stop_robot()
            self.stop_time = elapsed
            self.settling = True  # Warte auf finale Odom nach Ausrollen
            return

        # Timeout?
        if elapsed >= self.timeout:
            self.stop_robot()
            self.done = True
            self.get_logger().warn(f"Timeout nach {self.timeout:.0f}s!")
            self.print_result(elapsed)

    def stop_robot(self):
        # Phase 1: Aktives Bremsen (kurzer Rueckwaerts-Impuls)
        brake = Twist()
        brake.linear.x = -0.03
        for _ in range(4):  # 80ms
            self.pub_cmd.publish(brake)
            time.sleep(0.02)
        # Phase 2: Motoren aus
        stop = Twist()
        for _ in range(10):  # 200ms
            self.pub_cmd.publish(stop)
            time.sleep(0.02)

    def print_result(self, elapsed):
        if self.start_x is None or self.start_y is None or self.start_yaw is None:
            return
        dx = self.current_x - self.start_x
        dy = self.current_y - self.start_y
        distance = math.sqrt(dx * dx + dy * dy)

        cos_yaw = math.cos(self.start_yaw)
        sin_yaw = math.sin(self.start_yaw)
        forward = dx * cos_yaw + dy * sin_yaw
        lateral = -dx * sin_yaw + dy * cos_yaw

        lateral_drift = abs(lateral) * 100.0
        heading_odom = math.degrees(self.current_yaw - self.start_yaw)
        heading_gyro = math.degrees(self.gyro_heading)
        bias_dps = math.degrees(self.gyro_bias)

        mode = "MIT" if self.use_correction else "OHNE"

        print()
        print("=" * 60)
        print(f"  {ANSI_BOLD}Geradeausfahrt {mode} IMU-Korrektur{ANSI_RESET}")
        print("=" * 60)
        print(f"  Soll-Strecke:     {self.target_distance:.3f} m")
        print(
            f"  Odom-Strecke:     {distance:.3f} m "
            f"(Fehler: {abs(self.target_distance - distance) * 100:.1f}%)"
        )
        print(f"  Vorwaerts:        {forward:.4f} m")
        print(f"  Lateral:          {lateral:.4f} m")
        print(f"  Lateral-Drift:    {lateral_drift:.1f} cm")
        print(f"  Heading (Odom):   {heading_odom:+.2f} Grad")
        print(f"  Heading (Gyro):   {heading_gyro:+.2f} Grad")
        print(f"  Gyro-Bias:        {bias_dps:+.3f} deg/s")
        print(f"  Dauer:            {elapsed:.1f}s")

        # PASS/FAIL-Bewertung
        passed_drift = lateral_drift < AKZEPTANZ_DRIFT_CM
        passed_heading = abs(heading_gyro) < AKZEPTANZ_HEADING_DEG
        passed = passed_drift and passed_heading

        if passed:
            print(f"  {ANSI_GREEN}{ANSI_BOLD}PASS{ANSI_RESET}")
        else:
            print(f"  {ANSI_RED}{ANSI_BOLD}FAIL{ANSI_RESET}")
        print("=" * 60)

        # Ergebnis-Dictionary fuer JSON-Export
        self.result = {
            "test_name": f"geradeausfahrt_{'mit' if self.use_correction else 'ohne'}_imu",
            "result": "PASS" if passed else "FAIL",
            "metrics": {
                "soll_strecke_m": self.target_distance,
                "odom_strecke_m": round(distance, 4),
                "vorwaerts_m": round(forward, 4),
                "lateral_m": round(lateral, 4),
                "lateral_drift_cm": round(lateral_drift, 1),
                "heading_odom_deg": round(heading_odom, 2),
                "heading_gyro_deg": round(heading_gyro, 2),
                "gyro_bias_dps": round(bias_dps, 3),
                "dauer_s": round(elapsed, 1),
            },
            "kriterien": {
                "lateral_drift_cm_max": AKZEPTANZ_DRIFT_CM,
                "heading_deg_max": AKZEPTANZ_HEADING_DEG,
            },
            "timestamp": datetime.now().isoformat(),
        }


def run_single_test(use_correction):
    """Einen einzelnen Test ausfuehren."""
    node = StraightDriveTest(use_correction=use_correction)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        node.stop_robot()
    finally:
        result = node.result
        node.destroy_node()
    return result


def main(args=None):
    rclpy.init(args=args)

    mode = "both"
    for arg in sys.argv[1:]:
        if arg.startswith("--ros-args"):
            break
        if "uncorrect" in arg.lower():
            mode = "uncorrected"
        elif "correct" in arg.lower():
            mode = "corrected"

    print()
    print("*" * 60)
    print(f"  {ANSI_BOLD}AMR Geradeausfahrt-Test mit IMU-Korrektur{ANSI_RESET}")
    print("*" * 60)

    results = []

    if mode in ("both", "uncorrected"):
        print(f"\n{ANSI_CYAN}>>> Test 1: OHNE IMU-Korrektur{ANSI_RESET}")
        print("    Roboter faehrt 1m geradeaus (Closed-Loop auf Odom-Distanz)")
        if mode == "both":
            print("    Bitte Roboter zurueckstellen nach diesem Test!")
        r = run_single_test(use_correction=False)
        if r:
            results.append(r)

    if mode == "both":
        print(f"\n{ANSI_CYAN}Roboter zurueckstellen!{ANSI_RESET}")
        input("    Enter druecken wenn bereit...")

    if mode in ("both", "corrected"):
        print(f"\n{ANSI_CYAN}>>> Test 2: MIT IMU-Korrektur{ANSI_RESET}")
        print("    Roboter faehrt 1m geradeaus mit Heading-Stabilisierung")
        r = run_single_test(use_correction=True)
        if r:
            results.append(r)

    if results:
        pfad = save_json({"tests": results}, "straight_drive_results.json")
        print(f"\n  Ergebnisse: {pfad}")

    print()
    print("*" * 60)
    print(f"  {ANSI_BOLD}Tests abgeschlossen{ANSI_RESET}")
    print("*" * 60)

    rclpy.shutdown()


if __name__ == "__main__":
    main()
