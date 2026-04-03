#!/usr/bin/env python3
"""End-to-End Cliff-Safety-Latenztest.

Faehrt den Roboter mit 0.2 m/s vorwaerts und misst die Zeit
von der Cliff-Erkennung bis zum Motorstopp durch den cliff_safety_node.

Voraussetzung: Stack mit use_cliff_safety:=True gestartet.
Der Roboter muss auf eine Tischkante zufahren (Auffangsicherung bereithalten!).

Verwendung:
    ros2 run my_bot cliff_latency_test
"""

import math
import time
from datetime import datetime

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool

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

# Akzeptanzkriterium
AKZEPTANZ_LATENZ_MS = 50.0

# Fahrgeschwindigkeit
DRIVE_SPEED = 0.2  # m/s


class CliffLatencyTest(Node):
    """Misst End-to-End-Latenz: Cliff-Erkennung bis Motorstopp."""

    def __init__(self):
        super().__init__("cliff_latency_test")

        # Zustand
        self.phase = "wait_odom"  # wait_odom → driving → cliff_detected → settling → done
        self.done = False
        self.result = None

        # Zeitstempel
        self.drive_start_time = None
        self.cliff_time = None  # ROS-Timestamp des ersten cliff=true
        self.stop_time = None  # ROS-Timestamp des ersten cmd_vel=0 nach cliff
        self.last_cliff_false_time = None  # Letzter cliff=false Timestamp

        # Odometrie
        self.odom_at_cliff = None  # (x, y) bei Cliff-Erkennung
        self.odom_current = (0.0, 0.0)
        self.odom_prev = (0.0, 0.0)
        self.stable_count = 0

        # QoS
        qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)

        # Publisher auf /nav_cmd_vel (cliff_safety_node leitet an /cmd_vel weiter)
        self.pub_nav = self.create_publisher(Twist, "/nav_cmd_vel", 10)

        # Subscriber
        self.sub_cliff = self.create_subscription(Bool, "/cliff", self.cliff_callback, qos_sensor)
        self.sub_cmd_vel = self.create_subscription(Twist, "/cmd_vel", self.cmd_vel_callback, 10)
        self.sub_odom = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)

        # Safety-Timeout
        self.timeout = 30.0

        self.get_logger().info("Cliff-Latenz-Test gestartet")
        self.get_logger().info("Warte auf /odom und /cliff...")

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.odom_current = (x, y)

        if self.phase == "wait_odom":
            self.phase = "driving"
            self.drive_start_time = time.time()
            self.get_logger().info(
                f"Fahre mit {DRIVE_SPEED} m/s vorwaerts. Roboter auf Tischkante zusteuern lassen!"
            )

        # Nach Cliff: Stillstand erkennen
        if self.phase == "settling":
            dx = abs(x - self.odom_prev[0])
            dy = abs(y - self.odom_prev[1])
            if math.sqrt(dx * dx + dy * dy) < 0.0005:
                self.stable_count += 1
            else:
                self.stable_count = 0
            self.odom_prev = (x, y)

            if self.stable_count >= 5:
                self.phase = "done"
                self.done = True
                self.print_result()

        # Waehrend Fahrt: cmd_vel publizieren
        if self.phase == "driving":
            twist = Twist()
            twist.linear.x = DRIVE_SPEED
            self.pub_nav.publish(twist)

            # Timeout
            if self.drive_start_time and time.time() - self.drive_start_time > self.timeout:
                self.get_logger().warn("Timeout! Kein Cliff erkannt.")
                self.stop_robot()
                self.done = True

    def cliff_callback(self, msg):
        now = time.monotonic()

        if not msg.data:
            self.last_cliff_false_time = now
            return

        # Cliff erkannt!
        if self.phase == "driving" and msg.data:
            self.cliff_time = now
            self.odom_at_cliff = self.odom_current
            self.phase = "cliff_detected"
            self.get_logger().warn("CLIFF ERKANNT! Messe Latenz...")

            # Sofort aufhoeren zu publishen auf /nav_cmd_vel
            self.pub_nav.publish(Twist())

    def cmd_vel_callback(self, msg):
        if self.phase != "cliff_detected":
            return

        # Warte auf den ersten Null-Twist von cliff_safety_node
        if abs(msg.linear.x) < 0.001 and abs(msg.angular.z) < 0.001:
            self.stop_time = time.monotonic()
            self.phase = "settling"
            self.odom_prev = self.odom_current

            if self.cliff_time:
                latency_ms = (self.stop_time - self.cliff_time) * 1000.0
                self.get_logger().info(f"Stopp erkannt! Latenz: {latency_ms:.1f} ms")

    def stop_robot(self):
        twist = Twist()
        for _ in range(10):
            self.pub_nav.publish(twist)
            time.sleep(0.02)

    def print_result(self):
        if not self.cliff_time or not self.stop_time:
            self.get_logger().error("Keine vollstaendige Messung moeglich.")
            return

        latency_ms = (self.stop_time - self.cliff_time) * 1000.0

        # Bremsweg berechnen
        braking_distance = 0.0
        if self.odom_at_cliff:
            dx = self.odom_current[0] - self.odom_at_cliff[0]
            dy = self.odom_current[1] - self.odom_at_cliff[1]
            braking_distance = math.sqrt(dx * dx + dy * dy)

        # Sensor-Intervall (letztes false → erstes true)
        sensor_interval_ms = 0.0
        if self.last_cliff_false_time and self.cliff_time:
            sensor_interval_ms = (self.cliff_time - self.last_cliff_false_time) * 1000.0

        passed = latency_ms < AKZEPTANZ_LATENZ_MS

        print()
        print("=" * 60)
        print(f"  {ANSI_BOLD}Cliff-Safety End-to-End Latenztest{ANSI_RESET}")
        print("=" * 60)
        print(f"  Fahrgeschwindigkeit:  {DRIVE_SPEED} m/s")
        print(f"  Latenz (Cliff→Stopp): {latency_ms:.1f} ms")
        print(f"  Sensor-Intervall:     {sensor_interval_ms:.1f} ms")
        print(f"  Bremsweg:             {braking_distance * 100:.1f} cm")
        print(f"  Akzeptanz:            < {AKZEPTANZ_LATENZ_MS:.0f} ms")
        print("=" * 60)

        if passed:
            print(f"  {ANSI_GREEN}{ANSI_BOLD}PASS{ANSI_RESET}")
        else:
            print(f"  {ANSI_RED}{ANSI_BOLD}FAIL{ANSI_RESET}")
        print("=" * 60)

        self.result = {
            "test_name": "cliff_latency_end_to_end",
            "result": "PASS" if passed else "FAIL",
            "metrics": {
                "fahrgeschwindigkeit_m_s": DRIVE_SPEED,
                "latenz_ms": round(latency_ms, 1),
                "sensor_intervall_ms": round(sensor_interval_ms, 1),
                "bremsweg_cm": round(braking_distance * 100, 1),
            },
            "kriterien": {
                "latenz_ms_max": AKZEPTANZ_LATENZ_MS,
            },
            "timestamp": datetime.now().isoformat(),
        }


def main(args=None):
    rclpy.init(args=args)

    print()
    print("*" * 60)
    print(f"  {ANSI_BOLD}AMR Cliff-Safety Latenztest{ANSI_RESET}")
    print("*" * 60)
    print(f"\n{ANSI_CYAN}  Voraussetzung: use_cliff_safety:=True{ANSI_RESET}")
    print(f"{ANSI_CYAN}  Roboter faehrt mit {DRIVE_SPEED} m/s auf Tischkante zu.{ANSI_RESET}")
    print(f"{ANSI_CYAN}  Auffangsicherung bereithalten!{ANSI_RESET}\n")

    input("    Enter druecken wenn bereit...")

    node = CliffLatencyTest()

    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        node.stop_robot()
    finally:
        if node.result and save_json is not None:
            pfad = save_json({"tests": [node.result]}, "cliff_latency_results.json")
            print(f"\n  Ergebnisse: {pfad}")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
