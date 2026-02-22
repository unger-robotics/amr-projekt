#!/usr/bin/env python3
"""ROS2-Node: Echtzeit-Objekterkennung mit Hailo-8 AI Accelerator.

Erste Stufe der hybriden KI-Pipeline: Lokale Inference auf dem
Hailo-8 Hardware-Beschleuniger mit einem vorkompilierten YOLOv8-Modell.

Subscriptions:
  /camera/image_raw (sensor_msgs/Image) - Kamerabild

Publications:
  /vision/detections (std_msgs/String) - JSON-kodierte Detektionen

JSON-Format pro Detection:
  {
    "timestamp": <float>,
    "detections": [
      {"class_id": <int>, "label": <str>, "confidence": <float>,
       "bbox": [x1, y1, x2, y2]}
    ]
  }

Verwendung:
  ros2 run my_bot hailo_inference_node
  ros2 run my_bot hailo_inference_node --ros-args -p model_path:=<pfad.hef>
"""

import json
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import String

try:
    from hailo_platform import (
        HEF,
        VDevice,
        HailoStreamInterface,
        InferVStreams,
        ConfigureParams,
        InputVStreamParams,
        OutputVStreamParams,
        FormatType,
    )
    HAS_HAILO = True
except ImportError:
    HAS_HAILO = False

# COCO-Klassen (YOLOv8 Default, 80 Klassen)
COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
    "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
]

# Eingabegroesse YOLOv8
INPUT_WIDTH = 640
INPUT_HEIGHT = 640


class HailoInferenceNode(Node):
    """ROS2-Node fuer Hailo-8 Objekterkennung."""

    def __init__(self):
        super().__init__('hailo_inference_node')

        # Parameter
        self.declare_parameter(
            'model_path', 'hardware/models/yolov8s.hef')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('inference_hz', 5.0)

        self.model_path = self.get_parameter(
            'model_path').get_parameter_value().string_value
        self.conf_threshold = self.get_parameter(
            'confidence_threshold').get_parameter_value().double_value
        self.target_period = 1.0 / self.get_parameter(
            'inference_hz').get_parameter_value().double_value

        self.bridge = CvBridge()
        self.latest_image = None
        self.last_inference_time = 0.0

        # Hailo-Inference-Kontext
        self.vdevice = None
        self.network_group = None
        self.infer_pipeline = None
        self.input_vstream_info = None
        self.output_vstream_info = None

        # Publisher / Subscriber
        self.det_pub = self.create_publisher(String, '/vision/detections', 10)
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self._image_cb, 10)

        # Hailo initialisieren
        if not HAS_HAILO:
            self.get_logger().error(
                'hailo_platform nicht installiert! '
                'pip3 install hailort oder HailoRT-SDK pruefen.')
            return

        if not self._init_hailo():
            return

        # Inference-Timer
        period_s = max(self.target_period, 0.05)
        self.create_timer(period_s, self._inference_tick)
        self.get_logger().info(
            f'Hailo Inference Node gestartet: {self.model_path} '
            f'@ {1.0/period_s:.1f} Hz, Threshold {self.conf_threshold}')

    def _init_hailo(self) -> bool:
        """HEF-Modell laden und Inference-Pipeline konfigurieren."""
        try:
            hef = HEF(self.model_path)
        except Exception as e:
            self.get_logger().error(f'HEF laden fehlgeschlagen: {e}')
            return False

        try:
            self.vdevice = VDevice()
            configure_params = ConfigureParams.create_from_hef(
                hef, interface=HailoStreamInterface.PCIe)
            self.network_group = self.vdevice.configure(
                hef, configure_params)[0]

            self.input_vstream_info = hef.get_input_vstream_infos()
            self.output_vstream_info = hef.get_output_vstream_infos()

            input_params = InputVStreamParams.make_from_network_group(
                self.network_group,
                quantized=False,
                format_type=FormatType.FLOAT32)
            output_params = OutputVStreamParams.make_from_network_group(
                self.network_group,
                quantized=False,
                format_type=FormatType.FLOAT32)

            self.infer_pipeline = InferVStreams(
                self.network_group, input_params, output_params)
            self.infer_pipeline.__enter__()

            self.get_logger().info(
                f'Hailo-8 initialisiert: '
                f'{len(self.input_vstream_info)} Input(s), '
                f'{len(self.output_vstream_info)} Output(s)')
            return True

        except Exception as e:
            self.get_logger().error(f'Hailo-Initialisierung fehlgeschlagen: {e}')
            return False

    def _image_cb(self, msg: Image):
        """Aktuellstes Kamerabild zwischenspeichern."""
        self.latest_image = msg

    def _preprocess(self, cv_image: np.ndarray) -> np.ndarray:
        """Bild auf Modell-Eingabegroesse skalieren und normalisieren."""
        resized = cv2.resize(cv_image, (INPUT_WIDTH, INPUT_HEIGHT))
        # BGR -> RGB, uint8 -> float32, normalisiert auf [0, 1]
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        return rgb.astype(np.float32) / 255.0

    def _postprocess(self, raw_output: dict,
                     orig_h: int, orig_w: int) -> list:
        """YOLOv8-Rohausgabe in Detektionsliste umwandeln."""
        detections = []

        # YOLOv8 HEF-Output: je nach Kompilierung unterschiedlich
        # Typisch: ein Output-Tensor [1, num_boxes, 4+num_classes]
        for name, data in raw_output.items():
            output = np.squeeze(data)

            if output.ndim != 2:
                continue

            num_predictions = output.shape[0]
            num_values = output.shape[1]

            # Format: [x_center, y_center, w, h, class_scores...]
            if num_values > 4:
                boxes = output[:, :4]
                scores = output[:, 4:]
            else:
                continue

            for i in range(num_predictions):
                class_id = int(np.argmax(scores[i]))
                confidence = float(scores[i, class_id])

                if confidence < self.conf_threshold:
                    continue

                # Normalisierte Koordinaten -> Pixel
                cx, cy, w, h = boxes[i]
                x1 = (cx - w / 2) * orig_w
                y1 = (cy - h / 2) * orig_h
                x2 = (cx + w / 2) * orig_w
                y2 = (cy + h / 2) * orig_h

                label = COCO_LABELS[class_id] if class_id < len(
                    COCO_LABELS) else f'class_{class_id}'

                detections.append({
                    'class_id': class_id,
                    'label': label,
                    'confidence': round(confidence, 3),
                    'bbox': [
                        round(float(x1), 1),
                        round(float(y1), 1),
                        round(float(x2), 1),
                        round(float(y2), 1),
                    ],
                })

        return detections

    def _inference_tick(self):
        """Periodische Inference auf dem aktuellsten Bild."""
        if self.latest_image is None or self.infer_pipeline is None:
            return

        now = time.monotonic()
        if now - self.last_inference_time < self.target_period:
            return
        self.last_inference_time = now

        try:
            cv_image = self.bridge.imgmsg_to_cv2(
                self.latest_image, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'Bildkonvertierung fehlgeschlagen: {e}')
            return

        orig_h, orig_w = cv_image.shape[:2]
        preprocessed = self._preprocess(cv_image)

        # Batch-Dimension hinzufuegen [1, H, W, 3]
        input_data = {
            self.input_vstream_info[0].name:
                np.expand_dims(preprocessed, axis=0)
        }

        try:
            t0 = time.monotonic()
            raw_output = self.infer_pipeline.infer(input_data)
            dt_ms = (time.monotonic() - t0) * 1000.0
        except Exception as e:
            self.get_logger().error(f'Hailo-Inference fehlgeschlagen: {e}')
            return

        detections = self._postprocess(raw_output, orig_h, orig_w)

        # JSON-Nachricht publizieren
        msg = String()
        msg.data = json.dumps({
            'timestamp': self.get_clock().now().nanoseconds / 1e9,
            'inference_ms': round(dt_ms, 1),
            'detections': detections,
        })
        self.det_pub.publish(msg)

        if detections:
            labels = [d['label'] for d in detections]
            self.get_logger().info(
                f'{len(detections)} Objekt(e) erkannt in {dt_ms:.1f} ms: '
                f'{", ".join(labels)}')

    def destroy_node(self):
        """Hailo-Ressourcen sauber freigeben."""
        if self.infer_pipeline is not None:
            try:
                self.infer_pipeline.__exit__(None, None, None)
            except Exception:
                pass
        if self.vdevice is not None:
            try:
                del self.vdevice
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HailoInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
