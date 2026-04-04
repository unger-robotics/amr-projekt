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
  /scan              (sensor_msgs/LaserScan)  - LiDAR-360-Scan (optional)

Publications:
  /vision/semantics (std_msgs/String) - Gemini-Analyse als JSON (inkl. sensor_fusion)

Umgebungsvariablen:
  GEMINI_API_KEY          - Google AI API-Schluessel (erforderlich)
  GEMINI_VISION_MODEL     - Modellname (Default: gemini-2.5-flash)
  GEMINI_THINKING_BUDGET  - Thinking-Token-Budget (Default: 0 = aus)
  GEMINI_REQUEST_INTERVAL - Min. Sekunden zwischen API-Calls (Default: 8.0)

Verwendung:
  ros2 run my_bot gemini_semantic_node
  ros2 run my_bot gemini_semantic_node --ros-args -p model:=gemini-2.5-flash
"""

from __future__ import annotations

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

ROBOTICS_PROMPT = (
    "Du bist das Vision-System eines autonomen mobilen Roboters (AMR).\n"
    "Analysiere das Kamerabild und identifiziere alle sichtbaren Objekte.\n"
    "\n"
    "Die vorgeschaltete Echtzeit-Erkennung (YOLOv8s, COCO-80) meldet:\n"
    "{hailo_detections}\n"
    "\n"
    "Deine Aufgabe:\n"
    "1. Bestaetige korrekte Hailo-Detektionen (Label uebernehmen).\n"
    "2. Korrigiere falsche Klassifikationen — COCO-80 kennt NUR 80 Alltags-\n"
    "   objekte. Werkzeuge, Messgeraete, Elektronik, Laborequipment werden\n"
    "   haeufig als visuell aehnliche COCO-Objekte fehlklassifiziert.\n"
    "   Benenne sie korrekt.\n"
    "3. Ergaenze Objekte, die Hailo nicht erkannt hat.\n"
    "\n"
    "Antworte ausschliesslich als JSON-Array:\n"
    '[{{"label": "<Objektname DE>", "box_2d": [ymin, xmin, ymax, xmax], '
    '"source": "<hailo|corrected|new>"}}]\n'
    "\n"
    "Koordinaten normalisiert 0-1000. Feld source:\n"
    '- "hailo"     = Hailo-Label bestaetigt\n'
    '- "corrected" = Hailo-Label korrigiert\n'
    '- "new"       = Objekt von Hailo nicht erkannt\n'
    "\n"
    "Kein Markdown, keine Erklaerung, nur das JSON-Array."
)

# RPLiDAR ist 180 Grad gedreht montiert (TF yaw=pi) — Scan-Winkel muessen verschoben werden
LIDAR_YAW_OFFSET = 3.14159265358979

# Sektor gilt als "frei" wenn minimale Distanz ueber diesem Schwellwert liegt
LIDAR_FREE_THRESHOLD_M = 1.5

# Rate-Limiting: Mindestabstand zwischen API-Aufrufen (Default, konfigurierbar)
# Tier 1: 150+ RPM → 8s Intervall ist konservativ (~7.5 RPM)
DEFAULT_REQUEST_INTERVAL_S = 8.0

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

        # Modell: GEMINI_VISION_MODEL > GEMINI_MODEL > ROS-Parameter > Default
        env_model = os.environ.get("GEMINI_VISION_MODEL", os.environ.get("GEMINI_MODEL"))
        self.declare_parameter("model", env_model or "gemini-2.5-flash")
        self.declare_parameter("max_tokens", 4096)
        self.declare_parameter(
            "thinking_budget",
            int(os.environ.get("GEMINI_THINKING_BUDGET") or "0"),
        )
        self.declare_parameter(
            "request_interval",
            float(os.environ.get("GEMINI_REQUEST_INTERVAL") or str(DEFAULT_REQUEST_INTERVAL_S)),
        )

        model_name = self.get_parameter("model").get_parameter_value().string_value
        self.max_tokens = self.get_parameter("max_tokens").get_parameter_value().integer_value
        self.thinking_budget = (
            self.get_parameter("thinking_budget").get_parameter_value().integer_value
        )
        self.min_request_interval = (
            self.get_parameter("request_interval").get_parameter_value().double_value
        )

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
        if self.thinking_budget > 0:
            self.get_logger().info(f"Thinking-Budget: {self.thinking_budget} Tokens")

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
            state = "aktiviert" if msg.data else "deaktiviert"
            self.get_logger().info(f"Gemini-Analyse {state}")

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
          vorne:  -45 bis +45 Grad
          links:  +45 bis +135 Grad
          hinten: +/-135 bis +/-180 Grad
          rechts: -135 bis -45 Grad
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
            # Winkel im Sensor-Frame + 180-Korrektur fuer gedrehte Montage
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
        if now - self.last_request_time < self.min_request_interval:
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
                self.get_logger().warn(
                    "Kein Kamerabild verfuegbar — /camera/image_raw fehlt "
                    "oder v4l2_camera_node nicht aktiv. Semantische Analyse "
                    "uebersprungen.",
                    throttle_duration_sec=10.0,
                )
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
            target=self._send_to_gemini,
            args=(cv_image, detections),
            daemon=True,
        )
        thread.start()

    def _parse_robotics_response(self, response_text: str) -> list[dict] | None:
        """Parst JSON-Antwort des Robotik-VLM. None bei Fehler.

        Tolerant gegenueber abgeschnittenen Antworten: Extrahiert alle
        vollstaendigen JSON-Objekte aus einem unvollstaendigen Array.
        """
        text = response_text.strip()
        # Markdown-Codeblock-Wrapper entfernen
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            self.get_logger().warn(f"Gemini: Kein Array: {type(parsed)}")
            return None
        except json.JSONDecodeError:
            # Toleranter Parser: vollstaendige Objekte aus abgeschnittenem Array retten
            recovered = self._recover_partial_json(text)
            if recovered:
                self.get_logger().info(
                    f"Gemini-JSON repariert: {len(recovered)} Objekt(e) aus "
                    f"abgeschnittener Antwort ({len(text)} Zeichen)"
                )
                return recovered
            self.get_logger().warn(f"Gemini-JSON nicht reparierbar — {text[:200]}")
            return None

    @staticmethod
    def _recover_partial_json(text: str) -> list[dict] | None:
        """Extrahiert vollstaendige JSON-Objekte aus abgeschnittenem Array."""
        # Trailing-Comma entfernen und Array schliessen
        stripped = text.rstrip().rstrip(",").rstrip()
        if stripped.endswith("}"):
            candidate = stripped + "]"
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list) and parsed:
                    return parsed
            except json.JSONDecodeError:
                pass

        # Letztes unvollstaendiges Objekt abschneiden
        last_close = text.rfind("}")
        if last_close > 0:
            candidate = text[: last_close + 1].rstrip().rstrip(",").rstrip() + "]"
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list) and parsed:
                    return parsed
            except json.JSONDecodeError:
                pass

        return None

    def _build_sensor_context(self):
        """Liest Sensordaten und gibt (prompt_parts, us_range, lidar) zurueck."""
        prompt_parts = []
        now_mono = time.monotonic()

        # Ultraschall-Distanz einbeziehen (nur wenn frisch)
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

        return prompt_parts, us_range, lidar

    def _build_sensor_fusion_meta(self, us_range, lidar):
        """Baut sensor_fusion-Dict fuer die Ausgabe."""
        sensor_sources = ["kamera", "hailo"]
        if us_range is not None:
            sensor_sources.append("ultraschall")
        if lidar is not None:
            sensor_sources.append("lidar")
        return {
            "sources": sensor_sources,
            "ultrasonic_m": (round(us_range, 2) if us_range is not None else None),
            "lidar_sectors": lidar,
        }

    def _publish_hailo_fallback(self, detections: list) -> None:
        """Publiziert Hailo-Detektionen als Fallback auf /vision/semantics."""
        sensor_parts, us_range, lidar = self._build_sensor_context()
        labels = [d.get("label", "?") for d in detections[:5]]
        speech_text = f"Hailo: {', '.join(labels)}"

        result = {
            "timestamp": time.time(),
            "detections_input": detections[:5],
            "semantic_analysis": speech_text,
            "structured_detections": None,
            "model": "hailo-fallback",
            "sensor_fusion": self._build_sensor_fusion_meta(us_range, lidar),
        }

        msg = String()
        msg.data = json.dumps(result, ensure_ascii=False)
        self.sem_pub.publish(msg)
        self.get_logger().info(f"Hailo-Fallback: {speech_text[:120]}")

    def _send_to_gemini(self, cv_image: np.ndarray, detections: list):
        """Bild und Detektionen asynchron an Gemini API senden."""
        try:
            # Kamera ist 180 Grad gedreht montiert — Bild vor Analyse drehen
            cv_image = cv2.rotate(cv_image, cv2.ROTATE_180)

            # Bild verkleinern fuer weniger Image-Tokens
            h, w = cv_image.shape[:2]
            if max(h, w) > MAX_IMAGE_DIM:
                scale = MAX_IMAGE_DIM / max(h, w)
                cv_image = cv2.resize(
                    cv_image,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )

            # Bild als JPEG kodieren fuer API-Transfer
            _, jpeg_buf = cv2.imencode(".jpg", cv_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
            jpeg_bytes = jpeg_buf.tobytes()

            # Detektions-Kontext fuer Prompt formatieren
            det_lines = []
            for d in detections[:5]:
                if d.get("reclassified"):
                    orig = d.get("original_labels", [])
                    det_lines.append(
                        f"- UNBEKANNT (aus {', '.join(orig)}, Conf. {d['confidence']:.0%})"
                    )
                else:
                    det_lines.append(f"- {d['label']} (Conf. {d['confidence']:.0%})")
            hailo_text = "\n".join(det_lines) if det_lines else "Keine Objekte erkannt."

            # Prompt zusammenbauen: Robotik-Prompt + Sensorfusion
            prompt_parts = [ROBOTICS_PROMPT.format(hailo_detections=hailo_text)]

            # Sensordaten anfuegen (Ultraschall + LiDAR)
            sensor_parts, us_range, lidar = self._build_sensor_context()
            prompt_parts.extend(sensor_parts)

            prompt = "\n".join(prompt_parts)

            # Gemini API-Aufruf mit Bild
            image_part = types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")

            # GenerateContentConfig mit JSON-Modus und optionalem Thinking-Budget
            config_kwargs = {
                "max_output_tokens": self.max_tokens,
                "response_mime_type": "application/json",
            }
            if self.thinking_budget > 0:
                try:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(
                        thinking_budget=self.thinking_budget
                    )
                except (AttributeError, TypeError):
                    self.get_logger().warn(
                        "ThinkingConfig nicht verfuegbar — google-genai Version zu alt?",
                        throttle_duration_sec=60.0,
                    )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(**config_kwargs),
            )

            # Finish-Reason pruefen (MAX_TOKENS = Antwort abgeschnitten)
            if response and response.candidates:
                fr = response.candidates[0].finish_reason
                if fr and str(fr) not in ("STOP", "FinishReason.STOP", "0"):
                    self.get_logger().warn(
                        f"Gemini finish_reason={fr} — Antwort moeglicherweise abgeschnitten",
                        throttle_duration_sec=30.0,
                    )

            if response and response.text:
                # JSON-Antwort parsen
                structured = self._parse_robotics_response(response.text)

                if structured is not None:
                    labels = [d.get("label", "?") for d in structured]
                    corrected = [d for d in structured if d.get("source") == "corrected"]
                    new_objs = [d for d in structured if d.get("source") == "new"]

                    speech_parts = [f"Ich sehe: {', '.join(labels)}"]
                    if corrected:
                        speech_parts.append(
                            "Korrigiert: " + ", ".join(d["label"] for d in corrected)
                        )
                    if new_objs:
                        speech_parts.append("Neu: " + ", ".join(d["label"] for d in new_objs))
                    speech_text = ". ".join(speech_parts)

                    result = {
                        "timestamp": time.time(),
                        "detections_input": detections[:5],
                        "semantic_analysis": speech_text,
                        "structured_detections": structured,
                        "model": self.model_name,
                        "sensor_fusion": self._build_sensor_fusion_meta(us_range, lidar),
                    }

                    msg = String()
                    msg.data = json.dumps(result, ensure_ascii=False)
                    self.sem_pub.publish(msg)

                    self.get_logger().info(f"Gemini-Analyse: {speech_text[:120]}")
                else:
                    # JSON-Parse fehlgeschlagen — Hailo-Fallback statt rohem JSON
                    self._publish_hailo_fallback(detections)
            else:
                self.get_logger().warn("Gemini: Leere Antwort erhalten")
                self._publish_hailo_fallback(detections)

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                self.last_request_time = (
                    time.monotonic() + QUOTA_BACKOFF_S - self.min_request_interval
                )
                self.get_logger().warn(
                    f"Gemini-Quota erschoepft — pausiere {QUOTA_BACKOFF_S:.0f}s. {err_str[:120]}"
                )
            else:
                self.get_logger().error(f"Gemini-API-Fehler: {e}")
            # Immer Fallback publizieren bei Fehler
            self._publish_hailo_fallback(detections)

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
