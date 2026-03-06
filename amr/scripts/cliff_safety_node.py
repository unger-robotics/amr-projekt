#!/usr/bin/env python3
"""
Cliff-Safety-Node fuer den AMR-Roboter.

Ueberwacht das /cliff Topic (Sensor-Node ESP32, 20 Hz) und blockiert
Fahrbefehle bei erkanntem Abgrund. Leitet ansonsten Geschwindigkeitsbefehle
von Nav2 (/nav_cmd_vel) und Dashboard (/dashboard_cmd_vel) an /cmd_vel weiter.

Sicherheitsverhalten:
  - Cliff erkannt (true):  Null-Twist auf /cmd_vel (20 Hz Timer), Audio-Alarm einmalig
  - Cliff frei (false):    Normaler Betrieb, letzter empfangener Twist wird weitergeleitet
  - Shutdown:              Finaler Null-Twist auf /cmd_vel
"""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String


class CliffSafetyNode(Node):
    """Sicherheitsknoten: blockiert Fahrbefehle bei Cliff-Erkennung."""

    def __init__(self):
        super().__init__("cliff_safety_node")

        # Zustand
        self._cliff_detected = False
        self._alarm_sent = False
        self._last_twist = Twist()

        # QoS: Best-Effort fuer Sensor-Daten (Cliff), Reliable fuer cmd_vel
        qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        qos_reliable = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Subscriber
        self.create_subscription(Bool, "/cliff", self._cliff_callback, qos_sensor)
        self.create_subscription(Twist, "/nav_cmd_vel", self._nav_cmd_vel_callback, qos_reliable)
        self.create_subscription(
            Twist, "/dashboard_cmd_vel", self._dashboard_cmd_vel_callback, qos_reliable
        )

        # Publisher
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self._audio_pub = self.create_publisher(String, "/audio/play", 10)

        # 20 Hz Timer fuer Null-Twist bei aktivem Cliff-Stopp
        self._safety_timer = self.create_timer(0.05, self._safety_timer_callback)

        # Shutdown-Handler
        self.context.on_shutdown(self._on_shutdown)

        self.get_logger().info("Cliff-Safety-Node gestartet. Ueberwache /cliff...")

    def _cliff_callback(self, msg: Bool):
        """Verarbeitet Cliff-Sensordaten (true = Abgrund erkannt)."""
        if msg.data and not self._cliff_detected:
            # Cliff neu erkannt
            self._cliff_detected = True
            self.get_logger().warn("CLIFF ERKANNT! Fahrbefehle blockiert.")

            # Sofort Null-Twist senden
            self._cmd_vel_pub.publish(Twist())

            # Einmalig Audio-Alarm ausloesen
            if not self._alarm_sent:
                alarm_msg = String()
                alarm_msg.data = "cliff_alarm"
                self._audio_pub.publish(alarm_msg)
                self._alarm_sent = True
                self.get_logger().info("Audio-Alarm 'cliff_alarm' gesendet.")

        elif not msg.data and self._cliff_detected:
            # Cliff aufgehoben
            self._cliff_detected = False
            self._alarm_sent = False
            self.get_logger().info("Cliff aufgehoben. Fahrbefehle wieder freigegeben.")

    def _nav_cmd_vel_callback(self, msg: Twist):
        """Empfaengt Nav2-Geschwindigkeitsbefehle (remapped)."""
        self._last_twist = msg
        if not self._cliff_detected:
            self._cmd_vel_pub.publish(msg)

    def _dashboard_cmd_vel_callback(self, msg: Twist):
        """Empfaengt Dashboard-Joystick-Befehle (remapped)."""
        self._last_twist = msg
        if not self._cliff_detected:
            self._cmd_vel_pub.publish(msg)

    def _safety_timer_callback(self):
        """20 Hz Timer: Sendet Null-Twist solange Cliff aktiv ist."""
        if self._cliff_detected:
            self._cmd_vel_pub.publish(Twist())

    def _on_shutdown(self):
        """Finaler Null-Twist beim Herunterfahren."""
        self.get_logger().info("Shutdown: Sende finalen Stopp-Befehl.")
        self._cmd_vel_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = CliffSafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
