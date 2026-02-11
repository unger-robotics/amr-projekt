#!/usr/bin/env python3
"""
ArUco-Marker Docking-Node fuer AMR Ladestation.

Nutzt P-Regler fuer laterale Zentrierung und konstante Annaeherungsgeschwindigkeit.
Moderne OpenCV ArUco-API (>= 4.7) mit cv2.aruco.ArucoDetector.

States: SEARCHING -> APPROACHING -> DOCKED / TIMEOUT

Topics:
  - Subscribes: /camera/image_raw (sensor_msgs/Image)
  - Publishes:  /cmd_vel (geometry_msgs/Twist)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import time


class DockingNode(Node):
    """Docking-Node mit State-Machine und Watchdog-Timer."""

    # Zustaende
    SEARCHING = 'SEARCHING'
    APPROACHING = 'APPROACHING'
    DOCKED = 'DOCKED'
    TIMEOUT = 'TIMEOUT'

    def __init__(self):
        super().__init__('aruco_docking')

        # Publisher / Subscriber
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)

        # Parameter
        self.bridge = CvBridge()
        self.kp_angular = 0.5           # P-Regler Verstaerkung lateral
        self.approach_vel = 0.05         # Annaeherungsgeschwindigkeit [m/s]
        self.search_vel = 0.2            # Suchgeschwindigkeit [rad/s]
        self.target_marker_id = 42       # ArUco-Marker-ID an der Ladestation
        self.docking_threshold = 150     # Marker-Breite [px] fuer Docking-Erkennung
        self.timeout_sec = 60.0          # Gesamt-Timeout [s]

        # Zustand
        self.state = self.SEARCHING
        self.start_time = time.time()
        self.last_marker_time = 0.0
        self.marker_lost_timeout = 3.0   # Marker verloren nach 3 s

        # Letzter Marker-Zustand (fuer Ergebnis-Auswertung)
        self.last_marker_center_x = None
        self.last_marker_width = None
        self.image_width = None

        # ArUco Detector (moderne API, OpenCV >= 4.7)
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(dictionary, parameters)

        # Watchdog-Timer (10 Hz)
        self.timer = self.create_timer(0.1, self.watchdog_callback)

        # Shutdown-Hook: Roboter anhalten
        self.get_logger().info(
            f'Docking-Node gestartet. Suche Marker ID {self.target_marker_id}.')

    def image_callback(self, msg):
        """Verarbeitet Kamerabild: Marker-Detektion und Regelung."""
        # Nicht reagieren wenn bereits gedockt oder Timeout
        if self.state in (self.DOCKED, self.TIMEOUT):
            return

        # ROS Image -> OpenCV BGR
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'CvBridge Fehler: {e}')
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.image_width = frame.shape[1]
        img_center_x = self.image_width / 2.0

        # Marker-Detektion (moderne API)
        corners, ids, _rejected = self.detector.detectMarkers(gray)

        cmd = Twist()

        if ids is not None and self.target_marker_id in ids.flatten():
            # Marker gefunden
            index = np.where(ids.flatten() == self.target_marker_id)[0][0]
            c = corners[index][0]

            # Marker-Zentrum und -Breite
            center_x = np.mean(c[:, 0])
            marker_width = np.max(c[:, 0]) - np.min(c[:, 0])

            self.last_marker_center_x = center_x
            self.last_marker_width = marker_width
            self.last_marker_time = time.time()

            # Normierter Fehler [-1.0, 1.0]
            error_x = (center_x - img_center_x) / img_center_x

            # Zustandsuebergang SEARCHING -> APPROACHING
            if self.state == self.SEARCHING:
                self.state = self.APPROACHING
                self.get_logger().info('Marker erkannt. State: APPROACHING')

            # Docking-Erkennung: Marker gross genug (nah genug)
            if marker_width > self.docking_threshold:
                self.state = self.DOCKED
                self.get_logger().info(
                    f'DOCKING COMPLETE. Marker-Breite: {marker_width:.0f} px')
                self.stop_robot()
                return

            # P-Regler: laterale Zentrierung + konstante Vorwaertsfahrt
            cmd.angular.z = -1.0 * error_x * self.kp_angular
            cmd.linear.x = self.approach_vel

        else:
            # Kein Marker sichtbar -> Suchverhalten (langsam drehen)
            cmd.angular.z = self.search_vel

        self.cmd_pub.publish(cmd)

    def watchdog_callback(self):
        """Ueberwacht Timeout und Marker-Verlust."""
        if self.state in (self.DOCKED, self.TIMEOUT):
            return

        now = time.time()

        # Gesamt-Timeout pruefen
        if (now - self.start_time) > self.timeout_sec:
            self.state = self.TIMEOUT
            self.get_logger().warn(
                f'TIMEOUT nach {self.timeout_sec:.0f} s. Docking abgebrochen.')
            self.stop_robot()
            return

        # Marker-Verlust: zurueck zu SEARCHING
        if self.state == self.APPROACHING:
            if self.last_marker_time > 0 and \
               (now - self.last_marker_time) > self.marker_lost_timeout:
                self.state = self.SEARCHING
                self.get_logger().warn(
                    f'Marker verloren (>{self.marker_lost_timeout:.1f} s). '
                    'State: SEARCHING')

    def stop_robot(self):
        """Sendet Null-Twist um Roboter zu stoppen."""
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def get_result(self):
        """Gibt Ergebnis-Dictionary zurueck (fuer docking_test.py)."""
        lateral_offset_px = None
        if self.last_marker_center_x is not None and self.image_width is not None:
            lateral_offset_px = self.last_marker_center_x - (self.image_width / 2.0)

        return {
            'state': self.state,
            'duration_sec': time.time() - self.start_time,
            'lateral_offset_px': lateral_offset_px,
            'marker_width_px': self.last_marker_width,
        }


def main(args=None):
    rclpy.init(args=args)
    node = DockingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutdown durch Benutzer.')
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
