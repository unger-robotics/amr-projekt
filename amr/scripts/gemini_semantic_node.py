#!/usr/bin/env python3
"""ROS2-Node: Semantische Bildanalyse via Google Gemini API.

Zweite Stufe der hybriden KI-Pipeline: Cloud-basierte semantische
Interpretation der lokal erkannten Objekte.

Subscriptions:
  /camera/image_raw (sensor_msgs/Image) - Kamerabild
  /vision/detections (std_msgs/String) - JSON-Detektionen aus Hailo-Stufe

Publications:
  /vision/semantics (std_msgs/String) - Gemini-Analyse als JSON

Umgebungsvariable:
  GEMINI_API_KEY - Google AI API-Schluessel (erforderlich)

Verwendung:
  ros2 run my_bot gemini_semantic_node
  ros2 run my_bot gemini_semantic_node --ros-args -p model:=gemini-2.0-flash
"""

import json
import os
import threading
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import String

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

SYSTEM_PROMPT = (
    "Analysiere dieses Bild aus der Perspektive eines autonomen "
    "Transportroboters. Beschreibe praegnant das detektierte Objekt "
    "(z.B. Farbe, Form, Zustand). Antworte auf Deutsch in maximal "
    "2-3 Saetzen."
)

# Rate-Limiting: Mindestabstand zwischen API-Aufrufen
MIN_REQUEST_INTERVAL_S = 2.0


class GeminiSemanticNode(Node):
    """ROS2-Node fuer semantische Bildanalyse via Gemini."""

    def __init__(self):
        super().__init__('gemini_semantic_node')

        # Parameter
        self.declare_parameter('model', 'gemini-3.1-pro-preview')
        self.declare_parameter('max_tokens', 256)

        model_name = self.get_parameter(
            'model').get_parameter_value().string_value
        self.max_tokens = self.get_parameter(
            'max_tokens').get_parameter_value().integer_value

        self.bridge = CvBridge()
        self.latest_image = None
        self.latest_image_lock = threading.Lock()
        self.last_request_time = 0.0
        self.pending_request = False

        # Gemini konfigurieren
        if not HAS_GENAI:
            self.get_logger().error(
                'google-generativeai nicht installiert! '
                'pip3 install google-generativeai')
            return

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.get_logger().error(
                'GEMINI_API_KEY Umgebungsvariable nicht gesetzt! '
                'Export oder docker-compose.yml pruefen.')
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.get_logger().info(f'Gemini-Modell konfiguriert: {model_name}')

        # Publisher / Subscriber
        self.sem_pub = self.create_publisher(
            String, '/vision/semantics', 10)
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self._image_cb, 10)
        self.det_sub = self.create_subscription(
            String, '/vision/detections', self._detection_cb, 10)

        self.get_logger().info('Gemini Semantic Node gestartet')

    def _image_cb(self, msg: Image):
        """Aktuellstes Kamerabild zwischenspeichern."""
        with self.latest_image_lock:
            self.latest_image = msg

    def _detection_cb(self, msg: String):
        """Bei neuer Detection: Bild an Gemini senden."""
        if self.pending_request:
            return

        now = time.monotonic()
        if now - self.last_request_time < MIN_REQUEST_INTERVAL_S:
            return

        try:
            det_data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warn('Ungueltige Detection-JSON empfangen')
            return

        detections = det_data.get('detections', [])
        if not detections:
            return

        with self.latest_image_lock:
            if self.latest_image is None:
                return
            image_msg = self.latest_image

        try:
            cv_image = self.bridge.imgmsg_to_cv2(
                image_msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'Bildkonvertierung fehlgeschlagen: {e}')
            return

        # Asynchron an Gemini senden
        self.pending_request = True
        self.last_request_time = now

        thread = threading.Thread(
            target=self._send_to_gemini,
            args=(cv_image, detections),
            daemon=True)
        thread.start()

    def _send_to_gemini(self, cv_image: np.ndarray, detections: list):
        """Bild und Detektionen asynchron an Gemini API senden."""
        try:
            # Bild als JPEG kodieren fuer API-Transfer
            _, jpeg_buf = cv2.imencode(
                '.jpg', cv_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            jpeg_bytes = jpeg_buf.tobytes()

            # Detektions-Kontext als Textprompt
            det_summary = ', '.join(
                f"{d['label']} ({d['confidence']:.0%})"
                for d in detections[:5])
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Erkannte Objekte (Hailo-8): {det_summary}"
            )

            # Gemini API-Aufruf mit Bild
            image_part = {
                'mime_type': 'image/jpeg',
                'data': jpeg_bytes,
            }
            response = self.model.generate_content(
                [prompt, image_part],
                generation_config={'max_output_tokens': self.max_tokens})

            if response and response.text:
                result = {
                    'timestamp': time.time(),
                    'detections_input': detections[:5],
                    'semantic_analysis': response.text.strip(),
                    'model': self.model.model_name,
                }

                msg = String()
                msg.data = json.dumps(result, ensure_ascii=False)
                self.sem_pub.publish(msg)

                self.get_logger().info(
                    f'Gemini-Analyse: {response.text.strip()[:120]}')
            else:
                self.get_logger().warn('Gemini: Leere Antwort erhalten')

        except Exception as e:
            self.get_logger().error(f'Gemini-API-Fehler: {e}')

        finally:
            self.pending_request = False


def main(args=None):
    rclpy.init(args=args)
    node = GeminiSemanticNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
