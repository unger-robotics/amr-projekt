import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
# Du brauchst opencv-python und opencv-contrib-python für ArUco!
import cv2
import cv2.aruco as aruco
import numpy as np

class DockingNode(Node):
    def __init__(self):
        super().__init__('aruco_docking')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        # Hier Kamera-Topic einfügen (z.B. /camera/image_raw)
        # self.subscription = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.bridge = CvBridge()

        # PID Parameter für Zentrierung (aus Albarran)
        self.kp_angular = 0.5
        self.target_marker_id = 42 # ID deines Markers an der Wand

    def drive_to_marker(self, image):
        # 1. Bildverarbeitung
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        parameters = aruco.DetectorParameters_create()
        corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        cmd = Twist()

        if ids is not None and self.target_marker_id in ids:
            # 2. Marker gefunden -> Zentrum berechnen
            index = np.where(ids == self.target_marker_id)[0][0]
            c = corners[index][0]
            center_x = (c[0][0] + c[1][0] + c[2][0] + c[3][0]) / 4
            img_center_x = image.shape[1] / 2

            # 3. Fehler berechnen (Abweichung von Bildmitte)
            error_x = (center_x - img_center_x) / img_center_x # -1.0 bis 1.0

            # 4. Regelung (P-Regler)
            cmd.angular.z = -1.0 * error_x * self.kp_angular
            cmd.linear.x = 0.05 # Langsam vorwärts kriechen

            # Stoppen wenn Marker sehr groß (nahe) ist
            marker_width = c[1][0] - c[0][0]
            if marker_width > 150: # Pixel-Breite als Distanzmaß
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                self.get_logger().info("DOCKING COMPLETE")

        else:
            # Kein Marker -> Suchen (langsam drehen)
            cmd.angular.z = 0.2

        self.publisher_.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = DockingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
