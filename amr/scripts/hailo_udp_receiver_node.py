#!/usr/bin/env python3
"""ROS2-Node: Empfaengt Hailo-8 Detektionen via UDP.

UDP-Bruecke fuer die Vision-Pipeline: Der host_hailo_runner.py fuehrt
die Hailo-8 Inference nativ auf dem Pi 5 aus (Python 3.13 + hailort)
und sendet die Ergebnisse als JSON via UDP an diesen Container-Node.

Empfaengt:
  UDP 0.0.0.0:5005 - JSON-Pakete mit Detektionen

Publications:
  /vision/detections (std_msgs/String) - JSON-kodierte Detektionen

JSON-Format (identisch zu hailo_inference_node):
  {
    "timestamp": <float>,
    "inference_ms": <float>,
    "detections": [
      {"class_id": <int>, "label": <str>, "confidence": <float>,
       "bbox": [x1, y1, x2, y2]}
    ]
  }

Verwendung:
  ros2 run my_bot hailo_udp_receiver_node
"""

import json
import socket

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

UDP_PORT = 5005
UDP_ADDR = '0.0.0.0'
RECV_BUFFER = 65535


class HailoUdpReceiverNode(Node):
    """ROS2-Node: Empfaengt Hailo-Detektionen via UDP und publiziert sie."""

    def __init__(self):
        super().__init__('hailo_udp_receiver')

        self.det_pub = self.create_publisher(String, '/vision/detections', 10)

        # Non-blocking UDP-Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((UDP_ADDR, UDP_PORT))
        self.sock.setblocking(False)

        # 100 Hz Poll-Timer
        self.create_timer(0.01, self._poll_udp)

        self.msg_count = 0
        self.get_logger().info(
            f'Hailo UDP Receiver gestartet auf {UDP_ADDR}:{UDP_PORT} '
            f'- warte auf host_hailo_runner.py ...')

    def _poll_udp(self):
        """Socket pollen und empfangene JSON-Pakete publizieren."""
        while True:
            try:
                data, _ = self.sock.recvfrom(RECV_BUFFER)
            except BlockingIOError:
                break

            try:
                payload = json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.get_logger().warn(f'Ungueltige JSON-Daten: {e}')
                continue

            if 'detections' not in payload:
                self.get_logger().warn('JSON ohne "detections"-Feld verworfen')
                continue

            msg = String()
            msg.data = json.dumps(payload)
            self.det_pub.publish(msg)

            self.msg_count += 1
            if self.msg_count == 1:
                self.get_logger().info('Erste Detektion empfangen!')

            dets = payload['detections']
            if dets:
                labels = [d.get('label', '?') for d in dets]
                inf_ms = payload.get('inference_ms', 0)
                self.get_logger().info(
                    f'{len(dets)} Objekt(e) in {inf_ms:.1f} ms: '
                    f'{", ".join(labels)}',
                    throttle_duration_sec=2.0)

    def destroy_node(self):
        """Socket sauber schliessen."""
        if self.sock:
            self.sock.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HailoUdpReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
