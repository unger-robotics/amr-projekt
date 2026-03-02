#!/usr/bin/env python3
"""Closed-Loop Rotation mit IMU-Gyro-Feedback.

Dreht den Roboter um einen exakten Winkel, gesteuert durch
einen P-Regler auf den integrierten Gyro-Winkel. Nutzt
angular_velocity.z direkt (kein Quaternion-Wrapping-Problem).

Verwendung:
    ros2 run my_bot rotation_test              # 360 Grad
    ros2 run my_bot rotation_test 180          # 180 Grad
    ros2 run my_bot rotation_test -- -90       # -90 Grad (rueckwaerts)
"""

import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Imu

try:
    from amr_utils import ANSI_BOLD, ANSI_GREEN, ANSI_RED, ANSI_RESET
except ImportError:
    try:
        from my_bot.amr_utils import ANSI_BOLD, ANSI_GREEN, ANSI_RED, ANSI_RESET
    except ImportError:
        ANSI_GREEN = "\033[32m"
        ANSI_RED = "\033[31m"
        ANSI_BOLD = "\033[1m"
        ANSI_RESET = "\033[0m"


class RotationController(Node):
    def __init__(self, target_deg=360.0):
        super().__init__("rotation_controller")

        self.target_rad = math.radians(target_deg)
        self.target_deg = target_deg

        # Controller-Parameter
        self.kp = 2.0
        self.max_vel = 0.5  # max Drehgeschwindigkeit [rad/s]
        self.min_vel = 0.10  # min (ueberwindet Dead-Band)
        self.tolerance = math.radians(2.0)  # 2 Grad Toleranz
        self.timeout = 45.0  # Sekunden

        # Zustand — direkte Gyro-Integration (kein Wrapping)
        self.accumulated_rad = 0.0
        self.last_stamp = None
        self.running = False
        self.done = False
        self.start_time = None
        self.last_log_sec = -1

        # ROS2
        self.pub_cmd = self.create_publisher(Twist, "/cmd_vel", 10)
        self.sub_imu = self.create_subscription(Imu, "/imu", self.imu_callback, 10)

        self.get_logger().info(f"Ziel: {target_deg:.1f} Grad Drehung mit IMU-Gyro-Feedback")
        self.get_logger().info("Warte auf /imu...")

    def imu_callback(self, msg):
        now = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        if self.last_stamp is None:
            self.last_stamp = now
            self.running = True
            self.start_time = time.time()
            self.get_logger().info("IMU empfangen -- Drehung gestartet!")
            return

        # Gyro-Integration: gz [rad/s] * dt [s] = Winkelaenderung [rad]
        dt = now - self.last_stamp
        self.last_stamp = now

        if dt <= 0 or dt > 0.5:
            return

        gz = msg.angular_velocity.z
        self.accumulated_rad += gz * dt

        if self.done:
            return

        error = self.target_rad - self.accumulated_rad
        elapsed = time.time() - self.start_time

        # Timeout
        if elapsed > self.timeout:
            self.stop_robot()
            self.done = True
            self.get_logger().warn(f"Timeout nach {self.timeout:.0f}s!")
            self.print_result(elapsed)
            return

        # Ziel erreicht?
        if abs(error) < self.tolerance:
            self.stop_robot()
            self.done = True
            self.print_result(elapsed)
            return

        # P-Regler mit Saettigung
        cmd_vel = self.kp * error
        sign = 1.0 if cmd_vel > 0 else -1.0
        cmd_vel = sign * max(self.min_vel, min(abs(cmd_vel), self.max_vel))

        twist = Twist()
        twist.angular.z = cmd_vel
        self.pub_cmd.publish(twist)

        # Status alle 2s
        sec = int(elapsed)
        if sec % 2 == 0 and sec != self.last_log_sec and sec > 0:
            self.last_log_sec = sec
            self.get_logger().info(
                f"  {math.degrees(self.accumulated_rad):.1f} / "
                f"{self.target_deg:.1f} Grad | "
                f"vel: {cmd_vel:.2f} rad/s | {elapsed:.0f}s"
            )

    def stop_robot(self):
        twist = Twist()
        for _ in range(10):
            self.pub_cmd.publish(twist)
            time.sleep(0.02)

    def print_result(self, elapsed):
        achieved = math.degrees(self.accumulated_rad)
        error_deg = self.target_deg - achieved
        tol_deg = math.degrees(self.tolerance)
        passed = abs(error_deg) < tol_deg

        print()
        print("=" * 60)
        print(f"  {ANSI_BOLD}Closed-Loop Rotation Ergebnis{ANSI_RESET}")
        print("=" * 60)
        print(f"  Ziel:        {self.target_deg:.1f} Grad")
        print(f"  Erreicht:    {achieved:.1f} Grad")
        print(f"  Fehler:      {error_deg:.2f} Grad")
        print(f"  Dauer:       {elapsed:.1f}s")
        print(f"  Toleranz:    +/- {tol_deg:.1f} Grad")
        print("=" * 60)

        if passed:
            print(f"  {ANSI_GREEN}{ANSI_BOLD}PASS - Ziel erreicht!{ANSI_RESET}")
        else:
            print(f"  {ANSI_RED}{ANSI_BOLD}FAIL - Timeout{ANSI_RESET}")
        print("=" * 60)


def main(args=None):
    rclpy.init(args=args)

    target = 360.0
    for arg in sys.argv[1:]:
        stripped = arg.lstrip("-")
        if stripped.replace(".", "", 1).isdigit():
            try:
                target = float(arg)
                break
            except ValueError:
                pass

    node = RotationController(target)

    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        node.stop_robot()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
