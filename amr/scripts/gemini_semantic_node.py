#!/usr/bin/env python3
"""ROS2-Node: Semantische Bildanalyse via Google Gemini API mit Sensorfusion.

Zweite Stufe der hybriden KI-Pipeline: Cloud-basierte semantische
Interpretation der lokal erkannten Objekte, erweitert um Ultraschall-
und LiDAR-Umgebungsdaten fuer kontextreichere Szenenanalysen.

Subscriptions:
  /camera/image_raw  (sensor_msgs/Image)     - Kamerabild
  /vision/detections (std_msgs/String)        - JSON-Detektionen aus Hailo-Stufe
  /vision/enable     (std_msgs/Bool)          - Dashboard-Toggle (API-Calls nur wenn True)
  /range/front       (sensor_msgs/Range)      - Ultraschall-Entfernung (optional)
  /scan              (sensor_msgs/LaserScan)  - LiDAR-360°-Scan (optional)

Publications:
  /vision/semantics (std_msgs/String) - Gemini-Analyse als JSON (inkl. sensor_fusion)

Umgebungsvariable:
  GEMINI_API_KEY - Google AI API-Schluessel (erforderlich)

Verwendung:
  ros2 run my_bot gemini_semantic_node
  ros2 run my_bot gemini_semantic_node --ros-args -p model:=gemini-2.0-flash-lite
"""

import json
import os
import threading
import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image, LaserScan, Range
from std_msgs.msg import Bool, String

try:
    from google import genai
    from google.genai import types

    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

SYSTEM_PROMPT = (
    "Roboter-Sichtsystem mit Sensorfusion. Antworte AUF DEUTSCH mit Schluesselwoertern. "
    "KEIN Englisch, KEINE ganzen Saetze. "
    "Format: Marke Produkt, Farbe Material, weitere Objekte. "
    "Beispiel: Gerolsteiner Medium, gruene Glasflasche, Brille daneben. "
    "Lies Etiketten ab. Nenne weitere sichtbare Objekte. "
    "Wenn Sensordaten vorhanden: Beruecksichtige Ultraschall-Distanz und "
    "LiDAR-Umgebung. Hinweise auf Hindernisse oder freien Raum sind relevant."
)

# RPLiDAR ist 180° gedreht montiert (TF yaw=pi) — Scan-Winkel muessen verschoben werden
LIDAR_YAW_OFFSET = 3.14159265358979

# Sektor gilt als "frei" wenn minimale Distanz ueber diesem Schwellwert liegt
LIDAR_FREE_THRESHOLD_M = 1.5

# Rate-Limiting: Mindestabstand zwischen API-Aufrufen
# gemini-2.0-flash-lite Free-Tier: 30 RPM → 8s Intervall = ~7.5 RPM (sicherer Puffer)
MIN_REQUEST_INTERVAL_S = 8.0

# Backoff bei Quota-Erschoepfung (429): 60s Pause, dann erneut versuchen
QUOTA_BACKOFF_S = 60.0

# Sensordaten gelten als veraltet nach diesem Zeitfenster (Sekunden)
SENSOR_STALE_S = 5.0

# Maximale Bildgroesse fuer Gemini (laengste Seite in Pixel)
MAX_IMAGE_DIM = 640


class GeminiSemanticNode(Node):
    """ROS2-Node fuer semantische Bildanalyse via Gemini."""

    def __init__(self):
        super().__init__("gemini_semantic_node")

        # Parameter
        self.declare_parameter("model", "gemini-2.0-flash-lite")
        self.declare_parameter("max_tokens", 256)

        model_name = self.get_parameter("model").get_parameter_value().string_value
        self.max_tokens = self.get_parameter("max_tokens").get_parameter_value().integer_value

        self.bridge = CvBridge()
        self.latest_image = None
        self.latest_image_lock = threading.Lock()
        self.last_request_time = 0.0
        self.pending_request = False
        self._vision_enabled = False

        # Sensordaten fuer Fusion (optional, Thread-sicher, mit Zeitstempel)
        self._ultrasonic_range = None
        self._ultrasonic_ts = 0.0
        self._ultrasonic_lock = threading.Lock()
        self._lidar_sectors = None
        self._lidar_ts = 0.0
        self._lidar_lock = threading.Lock()

        # Gemini konfigurieren
        if not HAS_GENAI:
            self.get_logger().error("google-genai nicht installiert! pip3 install google-genai")
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.get_logger().error(
                "GEMINI_API_KEY Umgebungsvariable nicht gesetzt! "
                "Export oder docker-compose.yml pruefen."
            )
            return

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.get_logger().info(f"Gemini-Modell konfiguriert: {model_name}")

        # Publisher / Subscriber
        self.sem_pub = self.create_publisher(String, "/vision/semantics", 10)
        self.image_sub = self.create_subscription(Image, "/camera/image_raw", self._image_cb, 10)
        self.det_sub = self.create_subscription(
            String, "/vision/detections", self._detection_cb, 10
        )
        self.create_subscription(Bool, "/vision/enable", self._vision_enable_cb, 10)

        # Sensor-Subscriptions fuer Fusion (optional — graceful wenn Topics nicht da)
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(Range, "/range/front", self._range_cb, sensor_qos)
        self.create_subscription(LaserScan, "/scan", self._scan_cb, sensor_qos)

        self.get_logger().info(
            "Gemini Semantic Node gestartet — Sensorfusion aktiv (wartet auf /vision/enable)"
        )

    def _vision_enable_cb(self, msg: Bool) -> None:
        """Callback fuer /vision/enable — aktiviert/deaktiviert Gemini-Analyse."""
        was = self._vision_enabled
        self._vision_enabled = msg.data
        if was != msg.data:
            self.get_logger().info(f"Gemini-Analyse {'aktiviert' if msg.data else 'deaktiviert'}")

    def _range_cb(self, msg: Range) -> None:
        """Speichert aktuelle Ultraschall-Entfernung mit Zeitstempel."""
        with self._ultrasonic_lock:
            self._ultrasonic_range = msg.range
            self._ultrasonic_ts = time.monotonic()

    def _scan_cb(self, msg: LaserScan) -> None:
        """Fasst LiDAR-Scan in 4 Sektoren zusammen mit Zeitstempel."""
        sectors = self._summarize_lidar(msg)
        with self._lidar_lock:
            self._lidar_sectors = sectors
            self._lidar_ts = time.monotonic()

    @staticmethod
    def _summarize_lidar(msg: LaserScan) -> dict:
        """Fasst LaserScan in 4 Sektoren zusammen: naechstes Hindernis pro Richtung.

        Sektoren (bezogen auf Roboter-Blickrichtung, nach Yaw-Korrektur):
          vorne:  -45° bis +45°
          links:  +45° bis +135°
          hinten: ±135° bis ±180°
          rechts: -135° bis -45°
        """
        import math

        sector_ranges: dict[str, list[float]] = {
            "vorne": [],
            "links": [],
            "hinten": [],
            "rechts": [],
        }

        for i, r in enumerate(msg.ranges):
            if r <= msg.range_min or r >= msg.range_max or math.isinf(r) or math.isnan(r):
                continue
            # Winkel im Sensor-Frame + 180°-Korrektur fuer gedrehte Montage
            angle = msg.angle_min + i * msg.angle_increment + LIDAR_YAW_OFFSET
            # Normalisiere auf [-pi, pi]
            angle = math.atan2(math.sin(angle), math.cos(angle))

            if -math.pi / 4 <= angle <= math.pi / 4:
                sector_ranges["vorne"].append(r)
            elif math.pi / 4 < angle <= 3 * math.pi / 4:
                sector_ranges["links"].append(r)
            elif -3 * math.pi / 4 <= angle < -math.pi / 4:
                sector_ranges["rechts"].append(r)
            else:
                sector_ranges["hinten"].append(r)

        result: dict[str, dict] = {}
        for name, ranges in sector_ranges.items():
            if ranges:
                min_r = min(ranges)
                result[name] = {
                    "min_m": round(min_r, 2),
                    "frei": min_r > LIDAR_FREE_THRESHOLD_M,
                }
            else:
                result[name] = {"min_m": None, "frei": True}
        return result

    def _image_cb(self, msg: Image):
        """Aktuellstes Kamerabild zwischenspeichern."""
        with self.latest_image_lock:
            self.latest_image = msg

    def _detection_cb(self, msg: String):
        """Bei neuer Detection: Bild an Gemini senden (nur wenn aktiviert)."""
        if not self._vision_enabled:
            return

        if self.pending_request:
            return

        now = time.monotonic()
        if now - self.last_request_time < MIN_REQUEST_INTERVAL_S:
            return

        try:
            det_data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warn("Ungueltige Detection-JSON empfangen")
            return

        detections = det_data.get("detections", [])
        if not detections:
            return

        with self.latest_image_lock:
            if self.latest_image is None:
                return
            image_msg = self.latest_image

        try:
            cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().warn(f"Bildkonvertierung fehlgeschlagen: {e}")
            return

        # Asynchron an Gemini senden
        self.pending_request = True
        self.last_request_time = now

        thread = threading.Thread(
            target=self._send_to_gemini, args=(cv_image, detections), daemon=True
        )
        thread.start()

    def _send_to_gemini(self, cv_image: np.ndarray, detections: list):
        """Bild und Detektionen asynchron an Gemini API senden."""
        try:
            # Kamera ist 180° gedreht montiert — Bild vor Analyse drehen
            cv_image = cv2.rotate(cv_image, cv2.ROTATE_180)

            # Bild verkleinern fuer weniger Image-Tokens
            h, w = cv_image.shape[:2]
            if max(h, w) > MAX_IMAGE_DIM:
                scale = MAX_IMAGE_DIM / max(h, w)
                cv_image = cv2.resize(
                    cv_image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
                )

            # Bild als JPEG kodieren fuer API-Transfer
            _, jpeg_buf = cv2.imencode(".jpg", cv_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
            jpeg_bytes = jpeg_buf.tobytes()

            # Detektions-Kontext als Textprompt
            det_summary = ", ".join(f"{d['label']} ({d['confidence']:.0%})" for d in detections[:5])
            prompt_parts = [SYSTEM_PROMPT, f"\nErkannte Objekte (Hailo-8): {det_summary}"]

            # Ultraschall-Distanz einbeziehen (nur wenn frisch)
            now_mono = time.monotonic()
            with self._ultrasonic_lock:
                us_range = self._ultrasonic_range
                us_fresh = (now_mono - self._ultrasonic_ts) < SENSOR_STALE_S
            if not us_fresh:
                us_range = None
            if us_range is not None:
                prompt_parts.append(f"Frontaler Ultraschall: {us_range:.2f} m")

            # LiDAR-Sektoren einbeziehen (nur wenn frisch)
            with self._lidar_lock:
                lidar = self._lidar_sectors
                lidar_fresh = (now_mono - self._lidar_ts) < SENSOR_STALE_S
            if not lidar_fresh:
                lidar = None
            if lidar is not None:
                lidar_lines = []
                for sektor, data in lidar.items():
                    if data["min_m"] is not None:
                        status = "frei" if data["frei"] else f"Hindernis bei {data['min_m']} m"
                        lidar_lines.append(f"  {sektor}: {status}")
                    else:
                        lidar_lines.append(f"  {sektor}: keine Messung")
                prompt_parts.append("LiDAR-Umgebung:\n" + "\n".join(lidar_lines))

            prompt = "\n".join(prompt_parts)

            # Gemini API-Aufruf mit Bild
            image_part = types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(max_output_tokens=self.max_tokens),
            )

            if response and response.text:
                # Sensorfusion-Metadaten
                sensor_sources = ["kamera", "hailo"]
                if us_range is not None:
                    sensor_sources.append("ultraschall")
                if lidar is not None:
                    sensor_sources.append("lidar")

                result = {
                    "timestamp": time.time(),
                    "detections_input": detections[:5],
                    "semantic_analysis": response.text.strip(),
                    "model": self.model_name,
                    "sensor_fusion": {
                        "sources": sensor_sources,
                        "ultrasonic_m": round(us_range, 2) if us_range is not None else None,
                        "lidar_sectors": lidar,
                    },
                }

                msg = String()
                msg.data = json.dumps(result, ensure_ascii=False)
                self.sem_pub.publish(msg)

                self.get_logger().info(f"Gemini-Analyse: {response.text.strip()[:120]}")
            else:
                self.get_logger().warn("Gemini: Leere Antwort erhalten")

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                self.last_request_time = time.monotonic() + QUOTA_BACKOFF_S - MIN_REQUEST_INTERVAL_S
                self.get_logger().warn(
                    f"Gemini-Quota erschoepft — pausiere {QUOTA_BACKOFF_S:.0f}s. {err_str[:120]}"
                )
            else:
                self.get_logger().error(f"Gemini-API-Fehler: {e}")

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


if __name__ == "__main__":
    main()
