#!/usr/bin/env python3
"""
Quadrat-Navigationstest (1 m x 1 m) via /cmd_vel mit Vektornavigation.

Vektorbasierte Steuerung: Vor jedem Segment wird der Soll-Vektor (Laenge +
Richtung) vom aktuellen Standort zum Ziel berechnet. Dadurch werden
akkumulierte Positionsfehler aus vorherigen Segmenten kompensiert.

Sensorfusion:
  - Odom (Encoder): Regelschleife 20 Hz, Heading-Lock + Distanz
  - IMU  (Gyro-Z):  PD-Daempfung waehrend Fahrt
  - Map  (SLAM/TF): Heading-Korrektur vor/nach Segmenten

Bewertung: Odom-Frame (Soll vs. Ist), Segment-Vektoren (Odom vs. Map).
"""

import argparse
import json
import math
import os
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu
from tf2_ros import Buffer, TransformListener

from amr_utils import normalize_angle, quaternion_to_yaw

XY_TOLERANCE = 0.05
YAW_TOLERANCE = 0.10


class NavSquareTestNode(Node):
    def __init__(self, output_dir, linear_vel=0.10, angular_vel=0.3):
        super().__init__("nav_square_test")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.linear_vel = linear_vel
        self.angular_vel = angular_vel

        self.cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.odom_sub = self.create_subscription(Odometry, "/odom", self._odom_cb, 10)
        imu_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.imu_sub = self.create_subscription(Imu, "/imu", self._imu_cb, imu_qos)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.odom_x = self.odom_y = self.odom_yaw = 0.0
        self.odom_received = False
        self.imu_gyro_z = 0.0
        self.imu_heading = 0.0
        self._imu_t = None
        self._imu_active = False
        self.imu_received = False
        self.waypoint_results = []

        self.use_map_correction = True
        self.get_logger().info(
            f"Quadrat-Test bereit. v={linear_vel} m/s, omega={angular_vel} rad/s"
        )

    def _odom_cb(self, msg):
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y
        self.odom_yaw = quaternion_to_yaw(msg.pose.pose.orientation)
        self.odom_received = True

    def _imu_cb(self, msg):
        self.imu_gyro_z = msg.angular_velocity.z
        now = time.time()
        if self._imu_active and self._imu_t is not None:
            dt = now - self._imu_t
            if 0.0 < dt < 0.2:
                self.imu_heading = normalize_angle(self.imu_heading + self.imu_gyro_z * dt)
        self._imu_t = now
        self.imu_received = True

    def reset_imu_heading(self):
        self.imu_heading = 0.0
        self._imu_active = True
        self._imu_t = time.time()

    def stop_robot(self):
        cmd = Twist()
        for _ in range(5):
            self.cmd_pub.publish(cmd)
            rclpy.spin_once(self, timeout_sec=0.05)
        time.sleep(0.5)

    def spin_ms(self, duration=0.5):
        t_end = time.time() + duration
        while time.time() < t_end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def get_map_pose(self):
        for _ in range(10):
            rclpy.spin_once(self, timeout_sec=0.1)
            try:
                t = self.tf_buffer.lookup_transform(
                    "map",
                    "base_link",
                    rclpy.time.Time(),
                    timeout=rclpy.duration.Duration(seconds=0.5),
                )
                return (
                    t.transform.translation.x,
                    t.transform.translation.y,
                    quaternion_to_yaw(t.transform.rotation),
                )
            except Exception:
                pass
        return None

    def take_snapshot(self, label):
        self.spin_ms(0.5)
        odom = {"x": self.odom_x, "y": self.odom_y, "yaw": self.odom_yaw}
        imu = {"heading": self.imu_heading, "gyro_z": self.imu_gyro_z}
        mp = self.get_map_pose()
        map_d = (
            {"x": mp[0], "y": mp[1], "yaw": mp[2]}
            if mp
            else {"x": float("nan"), "y": float("nan"), "yaw": float("nan")}
        )

        self.get_logger().info(f"  [{label}]")
        self.get_logger().info(
            f"    Odom: ({odom['x']:.3f}, {odom['y']:.3f}, {math.degrees(odom['yaw']):.1f} deg)"
        )
        self.get_logger().info(
            f"    IMU:  hdg={math.degrees(imu['heading']):.1f} deg  gz={imu['gyro_z']:.3f} rad/s"
        )
        self.get_logger().info(
            f"    Map:  ({map_d['x']:.3f}, {map_d['y']:.3f}, {math.degrees(map_d['yaw']):.1f} deg)"
        )
        return {"label": label, "odom": odom, "imu": imu, "map": map_d}

    # ------------------------------------------------------------------ Aktorik

    def drive_straight(self, distance_m):
        """Geradeausfahrt mit Odom-Heading-Lock + IMU-Gyro-Daempfung + Bremsrampe."""
        start_x, start_y = self.odom_x, self.odom_y
        target_yaw = self.odom_yaw
        self.get_logger().info(
            f"  Fahre {distance_m:.3f} m (Lock {math.degrees(target_yaw):.1f} deg)..."
        )

        cmd = Twist()
        kp, kd, max_c = 1.0, 0.1, 0.2
        ramp_dist = 0.15
        min_vel = 0.03

        while True:
            rclpy.spin_once(self, timeout_sec=0.01)
            dx = self.odom_x - start_x
            dy = self.odom_y - start_y
            traveled = math.sqrt(dx * dx + dy * dy)
            remaining = distance_m - traveled
            if remaining <= 0.0:
                break
            if remaining < ramp_dist:
                vel = max(min_vel, self.linear_vel * (remaining / ramp_dist))
            else:
                vel = self.linear_vel
            cmd.linear.x = vel
            err = normalize_angle(target_yaw - self.odom_yaw)
            cmd.angular.z = max(-max_c, min(max_c, kp * err - kd * self.imu_gyro_z))
            self.cmd_pub.publish(cmd)
            time.sleep(0.05)

        self.stop_robot()

    def turn_to_heading(self, target_yaw_odom):
        """P-geregelte Drehung auf absoluten Odom-Heading mit IMU-Daempfung.

        Proportionalregler bremst sanft zum Ziel-Heading ab.
        IMU-Gyro-z dient als D-Anteil (Daempfung gegen Ueberschwingen).
        Nach dem Stopp: Nachkorrektur bei Restfehler > 1 deg (max 2 Versuche).
        """
        kp, kd = 1.5, 0.15
        min_omega = 0.08
        tolerance = math.radians(0.8)
        settle_tol = math.radians(1.0)
        max_corrections = 2
        cmd = Twist()

        error = normalize_angle(target_yaw_odom - self.odom_yaw)
        if abs(error) < tolerance:
            self.get_logger().info(f"  Heading OK ({math.degrees(error):+.1f} deg)")
            return

        self.get_logger().info(
            f"  Drehe auf {math.degrees(target_yaw_odom):.1f} deg "
            f"(Fehler: {math.degrees(error):+.1f} deg)..."
        )

        for attempt in range(1 + max_corrections):
            timeout = time.time() + 30.0
            while time.time() < timeout:
                rclpy.spin_once(self, timeout_sec=0.02)
                error = normalize_angle(target_yaw_odom - self.odom_yaw)
                if abs(error) < tolerance:
                    break
                omega = kp * error - kd * self.imu_gyro_z
                if 0 < abs(omega) < min_omega:
                    omega = min_omega * (1.0 if error > 0 else -1.0)
                omega = max(-self.angular_vel, min(self.angular_vel, omega))
                cmd.angular.z = omega
                self.cmd_pub.publish(cmd)
                time.sleep(0.05)

            self.stop_robot()
            self.spin_ms(0.3)
            final_err = normalize_angle(target_yaw_odom - self.odom_yaw)

            if abs(final_err) <= settle_tol or attempt == max_corrections:
                break
            self.get_logger().info(
                f"  Nachkorrektur {attempt}: Restfehler {math.degrees(final_err):+.1f} deg"
            )

        self.get_logger().info(
            f"  Drehung: Soll={math.degrees(target_yaw_odom):.1f} "
            f"Ist={math.degrees(self.odom_yaw):.1f} "
            f"Fehler={math.degrees(final_err):+.1f} deg"
        )

    def turn_by_angle(self, angle_rad):
        """Dreht um relativen Winkel (Wrapper fuer turn_to_heading)."""
        target = normalize_angle(self.odom_yaw + angle_rad)
        self.turn_to_heading(target)

    def correct_heading_map(self, target_yaw_map):
        """Map-Heading-Korrektur. Schwelle 2 deg."""
        mp = self.get_map_pose()
        if not mp:
            return
        error = normalize_angle(target_yaw_map - mp[2])
        if abs(error) < math.radians(2.0):
            self.get_logger().info(f"  Map-Korrektur: {math.degrees(error):+.1f} deg < 2 deg, OK")
            return
        self.get_logger().info(f"  Map-Korrektur: {math.degrees(error):+.1f} deg -> korrigiere")
        self.turn_by_angle(error)

    # ------------------------------------------------------------------ Vektorberechnung

    @staticmethod
    def compute_vector(x1, y1, x2, y2):
        """Berechnet Verschiebungsvektor: (laenge, winkel_rad)."""
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy), math.atan2(dy, dx)

    # ------------------------------------------------------------------ Testablauf

    def _wait_for_sensors(self):
        """Wartet auf Odom, TF (map->base_link) und IMU. Gibt False bei Timeout."""
        self.get_logger().info("Warte auf Odometrie + Map (TF) + IMU (max 30 s)...")
        t_end = time.time() + 30.0
        tf_ok = False
        next_st = time.time() + 5.0

        while time.time() < t_end:
            rclpy.spin_once(self, timeout_sec=0.1)
            if not tf_ok:
                try:
                    self.tf_buffer.lookup_transform(
                        "map",
                        "base_link",
                        rclpy.time.Time(),
                        timeout=rclpy.duration.Duration(seconds=0.2),
                    )
                    tf_ok = True
                except Exception:
                    pass
            if self.odom_received and tf_ok and self.imu_received:
                self.get_logger().info("  Odom: OK | Map (TF): OK | IMU: OK")
                return True
            if time.time() >= next_st:
                el = int(30.0 - (t_end - time.time()))
                self.get_logger().info(
                    f"  Odom: {'OK' if self.odom_received else 'WARTET'} | "
                    f"Map: {'OK' if tf_ok else 'WARTET'} | "
                    f"IMU: {'OK' if self.imu_received else 'WARTET'} ({el}/30 s)"
                )
                next_st = time.time() + 5.0

        if not self.odom_received:
            self.get_logger().error("Keine Odometrie!")
        elif not tf_ok:
            self.get_logger().error("Kein TF!")
        return False

    def _print_summary(self, total_duration):
        """Gibt die Ergebnis-Tabellen auf dem Logger aus."""
        self.get_logger().info("")
        self.get_logger().info("=" * 75)
        self.get_logger().info("ERGEBNIS")
        self.get_logger().info("=" * 75)
        self.get_logger().info("")
        self.get_logger().info(
            "| WP   | xy-Err  | yaw-Err  | Soll |d| | Odom |d| | Map |d|  | Pass |"
        )
        self.get_logger().info(
            "|------|---------|----------|---------|---------|----------|------|"
        )
        for r in self.waypoint_results:
            sv = r["soll_vector"]
            ov = r["odom_vector"]
            mv = r["map_vector"]
            self.get_logger().info(
                f"| {r['waypoint']:<4} | {r['xy_error']:>5.3f} m | "
                f"{r['yaw_error']:>6.4f} r | {sv['dist']:>5.3f} m | "
                f"{ov['dist']:>5.3f} m | {mv['dist']:>6.3f} m | "
                f"{'Ja' if r['passed'] else 'NEIN':>4} |"
            )

        self.get_logger().info("")
        self.get_logger().info("| WP   | Soll dir | Odom dir | Map dir  | IMU hdg  |")
        self.get_logger().info("|------|----------|----------|----------|----------|")
        for r in self.waypoint_results:
            sv = r["soll_vector"]
            ov = r["odom_vector"]
            mv = r["map_vector"]
            self.get_logger().info(
                f"| {r['waypoint']:<4} | {math.degrees(sv['dir']):>6.1f} d | "
                f"{math.degrees(ov['dir']):>6.1f} d | {math.degrees(mv['dir']):>6.1f} d | "
                f"{math.degrees(r['imu_heading']):>6.1f} d |"
            )

        self.get_logger().info("")
        self.get_logger().info("Drehungs-Analyse (Soll-Heading aus WP-Koordinaten):")
        self.get_logger().info("| WP   | Dreh-Soll | Odom vor | Odom nach | Dreh-Err | Map-Ref  |")
        self.get_logger().info("|------|-----------|----------|-----------|----------|----------|")
        for r in self.waypoint_results:
            tr = r["turn_ref"]
            dreh_err = normalize_angle(tr["target"] - tr["odom_after"])
            self.get_logger().info(
                f"| {r['waypoint']:<4} | {math.degrees(tr['target']):>7.1f} d | "
                f"{math.degrees(tr['odom_before']):>6.1f} d | "
                f"{math.degrees(tr['odom_after']):>7.1f} d | "
                f"{math.degrees(dreh_err):>+6.1f} d | "
                f"{math.degrees(tr['map_ref']):>6.1f} d |"
            )

        all_passed = all(r["passed"] for r in self.waypoint_results)
        n_pass = sum(1 for r in self.waypoint_results if r["passed"])
        self.get_logger().info("")
        self.get_logger().info(
            f"ERGEBNIS: {'BESTANDEN' if all_passed else 'NICHT BESTANDEN'} "
            f"({n_pass}/{len(self.waypoint_results)} WP)"
        )
        self.get_logger().info(f"Gesamtdauer: {total_duration:.1f} s")
        return all_passed

    def run_test(self):
        if not self._wait_for_sensors():
            return

        # --- Referenz ---
        sx, sy, syaw = self.odom_x, self.odom_y, self.odom_yaw
        cos_s, sin_s = math.cos(syaw), math.sin(syaw)
        start_map = self.get_map_pose()
        if not start_map:
            self.get_logger().error("Keine Map-Pose!")
            return
        start_map_yaw = start_map[2]
        self.reset_imu_heading()

        self.get_logger().info("=" * 60)
        self.get_logger().info("QUADRAT-TEST START (Vektornavigation)")
        start_snap = self.take_snapshot("Start")

        # Soll-Positionen (Odom-Frame)
        rel_wps = [
            (1, 0, 0, "WP1"),
            (1, 1, math.pi / 2, "WP2"),
            (0, 1, math.pi, "WP3"),
            (0, 0, -math.pi / 2, "WP4"),
        ]
        soll_poses = []
        for rx, ry, ryaw, name in rel_wps:
            soll_poses.append(
                {
                    "name": name,
                    "x": sx + cos_s * rx - sin_s * ry,
                    "y": sy + sin_s * rx + cos_s * ry,
                    "yaw": normalize_angle(syaw + ryaw),
                }
            )

        t_start = time.time()
        prev_odom = start_snap["odom"]
        prev_map = start_snap["map"]

        for i, soll in enumerate(soll_poses):
            self.get_logger().info("")
            self.get_logger().info(f"{'=' * 35} {soll['name']} {'=' * 35}")

            # --- Soll-Vektor: vom aktuellen Standort zum Ziel ---
            soll_dist, soll_dir = self.compute_vector(
                self.odom_x, self.odom_y, soll["x"], soll["y"]
            )
            self.get_logger().info(
                f"  Soll-Vektor: {soll_dist:.3f} m @ {math.degrees(soll_dir):.1f} deg (Odom)"
            )

            # --- Heading-Korrektur: Odom-Richtung drehen, optional Map feinjustieren ---
            self.turn_to_heading(soll_dir)
            if self.use_map_correction:
                seg_heading_map = normalize_angle(start_map_yaw + i * math.pi / 2)
                self.correct_heading_map(seg_heading_map)

            # --- Fahrt mit berechneter Distanz ---
            self.drive_straight(soll_dist)

            # --- Snapshot ---
            snap = self.take_snapshot(f"{soll['name']} nach Fahrt")

            # --- Ist-Vektoren berechnen ---
            odom_dist, odom_dir = self.compute_vector(
                prev_odom["x"], prev_odom["y"], snap["odom"]["x"], snap["odom"]["y"]
            )
            map_dist, map_dir = self.compute_vector(
                prev_map["x"], prev_map["y"], snap["map"]["x"], snap["map"]["y"]
            )

            # --- Odom-Fehler (PASS/FAIL) ---
            dx = soll["x"] - snap["odom"]["x"]
            dy = soll["y"] - snap["odom"]["y"]
            xy_err = math.sqrt(dx * dx + dy * dy)
            yaw_err = abs(normalize_angle(soll["yaw"] - snap["odom"]["yaw"]))
            xy_ok = xy_err < XY_TOLERANCE
            yaw_ok = yaw_err < YAW_TOLERANCE
            passed = xy_ok and yaw_ok

            # --- Log: Vektorvergleich ---
            self.get_logger().info(
                f"  Soll-Vektor:  |d|={soll_dist:.3f} m  dir={math.degrees(soll_dir):.1f} deg"
            )
            self.get_logger().info(
                f"  Odom-Vektor:  |d|={odom_dist:.3f} m  dir={math.degrees(odom_dir):.1f} deg  "
                f"(d_err={abs(odom_dist - soll_dist):.3f} m  "
                f"a_err={math.degrees(abs(normalize_angle(odom_dir - soll_dir))):.1f} deg)"
            )
            self.get_logger().info(
                f"  Map-Vektor:   |d|={map_dist:.3f} m  dir={math.degrees(map_dir):.1f} deg  "
                f"(d_err={abs(map_dist - soll_dist):.3f} m  "
                f"a_err={math.degrees(abs(normalize_angle(map_dir - soll_dir))):.1f} deg)"
            )
            self.get_logger().info(f"  IMU-Heading:  {math.degrees(self.imu_heading):.1f} deg")
            self.get_logger().info(
                f"  Positions-Fehler: xy={xy_err:.4f} m ({'OK' if xy_ok else 'FAIL'}) | "
                f"yaw={yaw_err:.4f} rad ({'OK' if yaw_ok else 'FAIL'})"
            )

            # --- Soll-Heading aus WP-Koordinaten berechnen ---
            self.get_logger().info("")
            if i < len(soll_poses) - 1:
                next_wp = soll_poses[i + 1]
                turn_target = math.atan2(next_wp["y"] - self.odom_y, next_wp["x"] - self.odom_x)
                self.get_logger().info(
                    f"  Dreh-Referenz: Richtung WP{i + 2} aus Ist-Position "
                    f"-> {math.degrees(turn_target):.1f} deg"
                )
            else:
                turn_target = syaw
                self.get_logger().info(
                    f"  Dreh-Referenz: Start-Heading -> {math.degrees(turn_target):.1f} deg"
                )

            mp_pre = self.get_map_pose()
            self.get_logger().info(
                f"  Istwerte VOR Drehung: Odom={math.degrees(self.odom_yaw):.1f}, "
                f"IMU={math.degrees(self.imu_heading):.1f}"
                + (f", Map={math.degrees(mp_pre[2]):.1f}" if mp_pre else "")
            )

            self.turn_to_heading(turn_target)
            next_h = normalize_angle(start_map_yaw + (i + 1) * math.pi / 2)
            if self.use_map_correction:
                self.correct_heading_map(next_h)

            snap_turn = self.take_snapshot(f"{soll['name']} nach Drehung")

            turn_err = normalize_angle(turn_target - snap_turn["odom"]["yaw"])
            self.get_logger().info(
                f"  Dreh-Ergebnis: Soll={math.degrees(turn_target):.1f} "
                f"Ist={math.degrees(snap_turn['odom']['yaw']):.1f} "
                f"Fehler={math.degrees(turn_err):+.1f} deg"
            )

            self.waypoint_results.append(
                {
                    "waypoint": soll["name"],
                    "soll": soll,
                    "soll_vector": {"dist": soll_dist, "dir": soll_dir},
                    "odom_vector": {"dist": odom_dist, "dir": odom_dir},
                    "map_vector": {"dist": map_dist, "dir": map_dir},
                    "imu_heading": self.imu_heading,
                    "turn_ref": {
                        "target": turn_target,
                        "odom_before": snap["odom"]["yaw"],
                        "odom_after": snap_turn["odom"]["yaw"],
                        "map_ref": next_h,
                    },
                    "after_drive": snap,
                    "after_turn": snap_turn,
                    "xy_error": xy_err,
                    "yaw_error": yaw_err,
                    "passed": passed,
                }
            )
            prev_odom = snap["odom"]
            prev_map = snap["map"]

        total_duration = time.time() - t_start
        all_passed = self._print_summary(total_duration)

        export = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "test": "nav_square_cmd_vel",
            "evaluation_frame": "odom",
            "all_passed": all_passed,
            "total_duration_s": round(total_duration, 1),
            "linear_vel": self.linear_vel,
            "angular_vel": self.angular_vel,
            "start_odom": {"x": sx, "y": sy, "yaw": syaw},
            "start_map": {"x": start_map[0], "y": start_map[1], "yaw": start_map[2]},
            "start": start_snap,
            "waypoints": self.waypoint_results,
        }
        json_pfad = self.output_dir / "nav_square_results.json"
        with open(json_pfad, "w") as f:
            json.dump(export, f, indent=2, default=str)
        self.get_logger().info(f"Ergebnisse: {json_pfad}")
        self.get_logger().info("=" * 75)


def main(args=None):
    parser = argparse.ArgumentParser(description="Quadrat-Navigationstest mit Vektornavigation")
    parser.add_argument("--output", default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--speed", type=float, default=0.10)
    parser.add_argument(
        "--no-map-correction",
        action="store_true",
        help="Map-Heading-Korrektur deaktivieren (nur Odom+IMU)",
    )
    parsed = parser.parse_args()

    rclpy.init(args=args)
    node = NavSquareTestNode(output_dir=parsed.output, linear_vel=parsed.speed)
    node.use_map_correction = not parsed.no_map_correction
    try:
        node.run_test()
    except KeyboardInterrupt:
        node.get_logger().info("Test abgebrochen.")
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
