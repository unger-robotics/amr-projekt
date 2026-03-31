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
from sensor_msgs.msg import Range
from std_msgs.msg import Bool, String


class CliffSafetyNode(Node):
    """Sicherheitsknoten: blockiert Fahrbefehle bei Cliff-Erkennung."""

    def __init__(self):
        super().__init__("cliff_safety_node")

        # Zustand
        self._cliff_detected = False
        self._obstacle_too_close = False
        self._estop_active = False
        self._alarm_sent = False
        self._last_twist = Twist()

        # Ultraschall-Schwellen (Hysterese)
        self._obstacle_stop_m = 0.10  # Stopp bei < 100 mm
        self._obstacle_clear_m = 0.14  # Freigabe bei > 140 mm

        # QoS: Best-Effort fuer Sensor-Daten (Cliff), Reliable fuer cmd_vel
        qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        qos_reliable = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Subscriber
        self.create_subscription(Bool, "/cliff", self._cliff_callback, qos_sensor)
        self.create_subscription(Range, "/range/front", self._range_callback, qos_sensor)
        self.create_subscription(Twist, "/nav_cmd_vel", self._nav_cmd_vel_callback, qos_reliable)
        self.create_subscription(
            Twist, "/dashboard_cmd_vel", self._dashboard_cmd_vel_callback, qos_reliable
        )
        self.create_subscription(Bool, "/emergency_stop", self._estop_callback, 10)

        # Publisher
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self._audio_pub = self.create_publisher(String, "/audio/play", 10)

        # 20 Hz Timer fuer Null-Twist bei aktivem Cliff-Stopp
        self._safety_timer = self.create_timer(0.05, self._safety_timer_callback)

        # Shutdown-Handler
        self.context.on_shutdown(self._on_shutdown)

        self.get_logger().info(
            "Cliff-Safety-Node gestartet. Ueberwache /cliff und /range/front "
            f"(Stopp < {self._obstacle_stop_m * 1000:.0f} mm, "
            f"Freigabe > {self._obstacle_clear_m * 1000:.0f} mm)..."
        )

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

    def _range_callback(self, msg: Range):
        """Verarbeitet Ultraschall-Distanz (Hindernis in Fahrtrichtung)."""
        dist = msg.range
        if dist < self._obstacle_stop_m and not self._obstacle_too_close:
            self._obstacle_too_close = True
            self._cmd_vel_pub.publish(Twist())
            self.get_logger().warn(f"HINDERNIS bei {dist * 100:.1f} cm! Vorwaertsfahrt blockiert.")
        elif dist > self._obstacle_clear_m and self._obstacle_too_close:
            self._obstacle_too_close = False
            self.get_logger().info("Hindernis frei. Vorwaertsfahrt wieder freigegeben.")

    def _estop_callback(self, msg: Bool):
        """Verarbeitet /emergency_stop (Totmannschalter)."""
        if msg.data and not self._estop_active:
            self._estop_active = True
            self._cmd_vel_pub.publish(Twist())
            self.get_logger().warn("E-STOP aktiv! Alle Fahrbefehle blockiert.")
        elif not msg.data and self._estop_active:
            self._estop_active = False
            self.get_logger().info("E-Stop aufgehoben. Fahrbefehle wieder freigegeben.")

    @property
    def _hard_blocked(self) -> bool:
        """True wenn Cliff oder E-Stop aktiv (alle Richtungen blockiert)."""
        return self._cliff_detected or self._estop_active

    def _is_forward_blocked(self, twist: Twist) -> bool:
        """True wenn der Twist blockiert werden soll."""
        if self._hard_blocked:
            return True
        # Ultraschall: nur Vorwaertsfahrt blockieren, Rueckwaerts + Drehung erlaubt
        return self._obstacle_too_close and twist.linear.x > 0

    def _nav_cmd_vel_callback(self, msg: Twist):
        """Empfaengt Nav2-Geschwindigkeitsbefehle (remapped)."""
        self._last_twist = msg
        if not self._is_forward_blocked(msg):
            self._cmd_vel_pub.publish(msg)

    def _dashboard_cmd_vel_callback(self, msg: Twist):
        """Empfaengt Dashboard-Joystick-Befehle (remapped)."""
        self._last_twist = msg
        if not self._is_forward_blocked(msg):
            self._cmd_vel_pub.publish(msg)

    def _safety_timer_callback(self):
        """20 Hz Timer: Sendet Null-Twist bei Cliff oder E-Stop."""
        if self._hard_blocked:
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
