#!/usr/bin/env python3
"""
Quadrat-Navigationstest (1 m x 1 m) via /cmd_vel mit Sensorfusion-Vergleich.

Faehrt ein 1x1 m Quadrat rein ueber Geschwindigkeitsbefehle.
An jedem Wegpunkt: Stopp, Sensorfusion-Snapshot (Odometrie, IMU, Map/SLAM),
dann 90-Grad-Drehung, erneuter Snapshot.

Ablauf pro Seite:
  1. Geradeaus 1 m (Odometrie-gesteuert)
  2. STOPP -> Snapshot: Odom-Pose, IMU-Yaw, Map-Pose (SLAM)
  3. 90 deg links drehen (Odometrie-gesteuert)
  4. STOPP -> Snapshot: Odom-Yaw, IMU-Yaw, Map-Yaw

Topics:
  - Subscribes: /odom, /imu
  - Publishes:  /cmd_vel
  - TF:         map -> base_link (via SLAM)
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

# Akzeptanzkriterien (odom-basiert)
XY_TOLERANCE = 0.10  # 10 cm
YAW_TOLERANCE = 0.15  # ~8.6 Grad


class NavSquareTestNode(Node):
    """Faehrt ein 1x1 m Quadrat via /cmd_vel mit Sensorfusion-Logging."""

    def __init__(self, output_dir, linear_vel=0.10, angular_vel=0.3):
        super().__init__("nav_square_test")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.linear_vel = linear_vel
        self.angular_vel = angular_vel

        # Publisher / Subscriber
        self.cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.odom_sub = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)
        # BestEffort QoS: kompatibel mit Reliable UND BestEffort Publishern
        imu_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.imu_sub = self.create_subscription(Imu, "/imu", self.imu_callback, imu_qos)

        # TF fuer Map-Pose (SLAM)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Odometrie-Zustand
        self.odom_x = 0.0
        self.odom_y = 0.0
        self.odom_yaw = 0.0
        self.odom_received = False

        # IMU-Zustand
        self.imu_yaw = 0.0
        self.imu_received = False

        # Ergebnisse
        self.waypoint_results = []

        self.get_logger().info(
            f"Quadrat-Test bereit. v={linear_vel} m/s, omega={angular_vel} rad/s"
        )

    def odom_callback(self, msg):
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y
        self.odom_yaw = quaternion_to_yaw(msg.pose.pose.orientation)
        self.odom_received = True

    def imu_callback(self, msg):
        self.imu_yaw = quaternion_to_yaw(msg.orientation)
        self.imu_received = True

    def stop_robot(self):
        """Sendet Null-Twist und wartet bis Roboter steht."""
        cmd = Twist()
        for _ in range(5):
            self.cmd_pub.publish(cmd)
            rclpy.spin_once(self, timeout_sec=0.05)
        time.sleep(0.5)

    def settle_and_spin(self, duration=1.0):
        """Wartet und spinnt um aktuelle Sensor-Daten zu erhalten."""
        t_end = time.time() + duration
        while time.time() < t_end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def get_map_pose(self):
        """Liest aktuelle Pose im map-Frame via TF."""
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
        """Nimmt Sensorfusion-Snapshot: Odom, IMU, Map."""
        self.settle_and_spin(0.5)

        odom = {"x": self.odom_x, "y": self.odom_y, "yaw": self.odom_yaw}
        imu = {"yaw": self.imu_yaw, "available": self.imu_received}

        map_pose = self.get_map_pose()
        if map_pose:
            map_data = {"x": map_pose[0], "y": map_pose[1], "yaw": map_pose[2]}
        else:
            map_data = {"x": float("nan"), "y": float("nan"), "yaw": float("nan")}

        # Yaw-Differenzen
        odom_imu_diff = (
            normalize_angle(odom["yaw"] - imu["yaw"]) if imu["available"] else float("nan")
        )
        odom_map_diff = normalize_angle(odom["yaw"] - map_data["yaw"])

        snapshot = {
            "label": label,
            "odom": odom,
            "imu": imu,
            "map": map_data,
            "yaw_diff_odom_imu_deg": math.degrees(odom_imu_diff)
            if not math.isnan(odom_imu_diff)
            else None,
            "yaw_diff_odom_map_deg": math.degrees(odom_map_diff)
            if not math.isnan(odom_map_diff)
            else None,
        }

        # Log
        self.get_logger().info(f"  [{label}]")
        self.get_logger().info(
            f"    Odom: ({odom['x']:.3f}, {odom['y']:.3f}, {math.degrees(odom['yaw']):.1f} deg)"
        )
        if imu["available"]:
            self.get_logger().info(
                f"    IMU:  yaw={math.degrees(imu['yaw']):.1f} deg "
                f"(Odom-IMU: {snapshot['yaw_diff_odom_imu_deg']:+.1f} deg)"
            )
        self.get_logger().info(
            f"    Map:  ({map_data['x']:.3f}, {map_data['y']:.3f}, "
            f"{math.degrees(map_data['yaw']):.1f} deg) "
            f"(Odom-Map: {snapshot['yaw_diff_odom_map_deg']:+.1f} deg)"
        )

        return snapshot

    def drive_straight(self, distance_m):
        """Faehrt geradeaus bis Odometrie-Distanz erreicht ist."""
        start_x = self.odom_x
        start_y = self.odom_y

        self.get_logger().info(f"  Fahre {distance_m:.2f} m geradeaus...")

        cmd = Twist()
        cmd.linear.x = self.linear_vel

        rate_hz = 20.0
        while True:
            rclpy.spin_once(self, timeout_sec=0.01)
            dx = self.odom_x - start_x
            dy = self.odom_y - start_y
            driven = math.sqrt(dx * dx + dy * dy)

            if driven >= distance_m:
                break

            self.cmd_pub.publish(cmd)
            time.sleep(1.0 / rate_hz)

        self.stop_robot()
        self.get_logger().info(f"  Gefahren: {driven:.3f} m")

    def turn_by_angle(self, angle_rad):
        """Dreht um angle_rad via Odometrie (positiv=links, negativ=rechts)."""
        direction = 1.0 if angle_rad > 0 else -1.0
        target = abs(angle_rad)

        self.get_logger().info(
            f"  Drehe {math.degrees(angle_rad):.1f} deg ({'links' if direction > 0 else 'rechts'})..."
        )

        cmd = Twist()
        cmd.angular.z = self.angular_vel * direction

        rate_hz = 20.0
        timeout = time.time() + 30.0
        turned_acc = 0.0
        last_yaw = self.odom_yaw

        while time.time() < timeout:
            rclpy.spin_once(self, timeout_sec=0.02)
            current_yaw = self.odom_yaw
            delta = normalize_angle(current_yaw - last_yaw)
            turned_acc += delta * direction  # immer positiv zaehlen
            last_yaw = current_yaw

            if turned_acc >= target:
                break

            self.cmd_pub.publish(cmd)
            time.sleep(1.0 / rate_hz)

        self.stop_robot()
        self.get_logger().info(f"  Gedreht: {math.degrees(turned_acc * direction):.1f} deg")

    def turn_left(self, angle_rad):
        """Dreht links um angle_rad via Odometrie."""
        self.turn_by_angle(angle_rad)

    def correct_heading(self, target_yaw):
        """Korrigiert Heading auf Soll-Richtung per Map-Pose (SLAM).

        Liest die aktuelle Map-Pose, berechnet den Heading-Fehler zum
        Soll-Yaw und dreht korrigierend. Schwelle: 2 deg.
        """
        map_pose = self.get_map_pose()
        if map_pose is None:
            self.get_logger().warn("  Heading-Korrektur: Keine Map-Pose verfuegbar")
            return

        map_yaw = map_pose[2]
        error = normalize_angle(target_yaw - map_yaw)
        error_deg = math.degrees(error)

        if abs(error_deg) < 2.0:
            self.get_logger().info(
                f"  Heading-Korrektur: Fehler {error_deg:+.1f} deg < 2 deg, keine Korrektur"
            )
            return

        self.get_logger().info(
            f"  Heading-Korrektur: Map-Yaw={math.degrees(map_yaw):.1f} deg, "
            f"Soll={math.degrees(target_yaw):.1f} deg, "
            f"Fehler={error_deg:+.1f} deg -> korrigiere"
        )
        self.turn_by_angle(error)

    def run_test(self):
        """Fuehrt den Quadrat-Test mit Sensorfusion-Snapshots durch."""
        # --- Warte auf alle drei Quellen: Odom + Map + IMU ---
        self.get_logger().info("Warte auf Odometrie + Map (TF) + IMU (max 30 s)...")
        t_wait_end = time.time() + 30.0
        tf_ok = False
        next_status = time.time() + 5.0

        while time.time() < t_wait_end:
            rclpy.spin_once(self, timeout_sec=0.1)

            # TF pruefen falls noch nicht ok
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

            # Alle drei bereit?
            if self.odom_received and tf_ok and self.imu_received:
                self.get_logger().info("  Odom: OK | Map (TF): OK | IMU: OK")
                break

            # Status alle 5 Sekunden
            if time.time() >= next_status:
                elapsed = int(30.0 - (t_wait_end - time.time()))
                self.get_logger().info(
                    f"  Odom: {'OK' if self.odom_received else 'WARTET'} | "
                    f"Map: {'OK' if tf_ok else 'WARTET'} | "
                    f"IMU: {'OK' if self.imu_received else 'WARTET'} "
                    f"({elapsed}/30 s)"
                )
                next_status = time.time() + 5.0
        else:
            # Timeout — pruefen was fehlt
            if not self.odom_received:
                self.get_logger().error("Keine Odometrie nach 30 s!")
                return
            if not tf_ok:
                self.get_logger().error("Kein TF map -> base_link nach 30 s!")
                return
            if not self.imu_received:
                self.get_logger().warn("Keine IMU-Daten nach 30 s — fahre ohne IMU fort")

        # Startpose (odom-basiert fuer Soll-Berechnung)
        sx, sy, syaw = self.odom_x, self.odom_y, self.odom_yaw
        cos_s = math.cos(syaw)
        sin_s = math.sin(syaw)

        self.get_logger().info("=" * 60)
        self.get_logger().info("QUADRAT-TEST START")
        start_snap = self.take_snapshot("Start")

        # Soll-Waypoints (odom-Frame, relativ zur Startpose)
        rel_wps: list[tuple[float, float, float, str]] = [
            (1.0, 0.0, 0.0, "WP1"),
            (1.0, 1.0, math.pi / 2, "WP2"),
            (0.0, 1.0, math.pi, "WP3"),
            (0.0, 0.0, -math.pi / 2, "WP4"),
        ]

        soll_poses = []
        for rx, ry, ryaw, name in rel_wps:
            ox = sx + cos_s * rx - sin_s * ry
            oy = sy + sin_s * rx + cos_s * ry
            oyaw = normalize_angle(syaw + ryaw)
            soll_poses.append({"x": ox, "y": oy, "yaw": oyaw, "name": name})

        t_start = time.time()

        for i, soll in enumerate(soll_poses):
            self.get_logger().info("")
            self.get_logger().info(f"{'=' * 40} {soll['name']} {'=' * 40}")

            # --- Geradeaus fahren ---
            self.drive_straight(1.0)

            # --- Snapshot nach Fahrt ---
            snap_drive = self.take_snapshot(f"{soll['name']} nach Fahrt")

            # Odom-Fehler berechnen
            dx = soll["x"] - snap_drive["odom"]["x"]
            dy = soll["y"] - snap_drive["odom"]["y"]
            xy_error = math.sqrt(dx * dx + dy * dy)
            yaw_error_odom = abs(normalize_angle(soll["yaw"] - snap_drive["odom"]["yaw"]))

            xy_ok = xy_error < XY_TOLERANCE
            yaw_ok = yaw_error_odom < YAW_TOLERANCE
            passed = xy_ok and yaw_ok

            self.get_logger().info(
                f"  Soll (odom): ({soll['x']:.3f}, {soll['y']:.3f}, "
                f"{math.degrees(soll['yaw']):.1f} deg)"
            )
            self.get_logger().info(
                f"  Odom-Fehler: xy={xy_error:.4f} m ({'OK' if xy_ok else 'FAIL'}) | "
                f"yaw={yaw_error_odom:.4f} rad ({'OK' if yaw_ok else 'FAIL'})"
            )

            # --- Heading-Korrektur vor Drehung (Map-basiert) ---
            # Soll-Heading waehrend der Fahrt = Richtung dieses Segments
            segment_heading = normalize_angle(syaw + i * math.pi / 2)
            self.correct_heading(segment_heading)

            # --- 90 Grad links drehen ---
            self.get_logger().info("")
            self.turn_left(math.pi / 2)

            # --- Snapshot nach Drehung ---
            snap_turn = self.take_snapshot(f"{soll['name']} nach Drehung")

            # Soll-Yaw nach Drehung = Soll-Yaw + 90 deg
            soll_yaw_after_turn = normalize_angle(soll["yaw"] + math.pi / 2)
            yaw_err_after = abs(normalize_angle(soll_yaw_after_turn - snap_turn["odom"]["yaw"]))
            self.get_logger().info(
                f"  Soll-Yaw nach Drehung: {math.degrees(soll_yaw_after_turn):.1f} deg | "
                f"Odom-Yaw-Fehler: {math.degrees(yaw_err_after):.1f} deg"
            )

            # Ergebnis speichern
            self.waypoint_results.append(
                {
                    "waypoint": soll["name"],
                    "soll": {"x": soll["x"], "y": soll["y"], "yaw": soll["yaw"]},
                    "after_drive": snap_drive,
                    "after_turn": snap_turn,
                    "xy_error": xy_error,
                    "yaw_error": yaw_error_odom,
                    "yaw_error_after_turn": yaw_err_after,
                    "passed": passed,
                }
            )

        total_duration = time.time() - t_start

        # --- Zusammenfassung ---
        self.get_logger().info("")
        self.get_logger().info("=" * 60)
        self.get_logger().info("SENSORFUSION-VERGLEICH")
        self.get_logger().info("=" * 60)
        self.get_logger().info("")
        self.get_logger().info(
            "| WP   | Odom xy-Err | Odom yaw-Err | IMU yaw  | Map yaw  | Odom-IMU | Odom-Map | Pass |"
        )
        self.get_logger().info(
            "|------|-------------|--------------|----------|----------|----------|----------|------|"
        )

        for r in self.waypoint_results:
            snap = r["after_drive"]
            imu_yaw_deg = (
                math.degrees(snap["imu"]["yaw"]) if snap["imu"]["available"] else float("nan")
            )
            map_yaw_deg = math.degrees(snap["map"]["yaw"])
            oi_diff = snap["yaw_diff_odom_imu_deg"]
            om_diff = snap["yaw_diff_odom_map_deg"]
            oi_str = f"{oi_diff:+6.1f}" if oi_diff is not None else "   N/A"
            om_str = f"{om_diff:+6.1f}" if om_diff is not None else "   N/A"

            self.get_logger().info(
                f"| {r['waypoint']:<4} | {r['xy_error']:>9.4f} m | "
                f"{r['yaw_error']:>10.4f} rad | "
                f"{imu_yaw_deg:>6.1f} d | {map_yaw_deg:>6.1f} d | "
                f"{oi_str} d | {om_str} d | "
                f"{'Ja' if r['passed'] else 'NEIN':>4} |"
            )

        all_passed = all(r["passed"] for r in self.waypoint_results)
        passed_count = sum(1 for r in self.waypoint_results if r["passed"])
        self.get_logger().info("")
        self.get_logger().info(
            f"ERGEBNIS: {'BESTANDEN' if all_passed else 'NICHT BESTANDEN'} "
            f"({passed_count}/{len(self.waypoint_results)} WP)"
        )
        self.get_logger().info(f"Gesamtdauer: {total_duration:.1f} s")

        # JSON-Export
        export = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "test": "nav_square_cmd_vel",
            "all_passed": all_passed,
            "total_duration_s": round(total_duration, 1),
            "linear_vel": self.linear_vel,
            "angular_vel": self.angular_vel,
            "start": start_snap,
            "waypoints": self.waypoint_results,
        }

        json_pfad = self.output_dir / "nav_square_results.json"
        with open(json_pfad, "w") as f:
            json.dump(export, f, indent=2, default=str)
        self.get_logger().info(f"Ergebnisse gespeichert: {json_pfad}")
        self.get_logger().info("=" * 60)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Quadrat-Navigationstest (1x1 m) via /cmd_vel mit Sensorfusion"
    )
    parser.add_argument(
        "--output",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Ausgabeverzeichnis fuer JSON-Ergebnisse",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.10,
        help="Vorwaertsgeschwindigkeit in m/s (Standard: 0.10)",
    )
    parsed = parser.parse_args()

    rclpy.init(args=args)
    node = NavSquareTestNode(
        output_dir=parsed.output,
        linear_vel=parsed.speed,
    )

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
