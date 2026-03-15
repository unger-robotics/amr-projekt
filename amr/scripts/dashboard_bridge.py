#!/usr/bin/env python3
"""ROS2-Node: WebSocket- und MJPEG-Bridge fuer das AMR Web-Dashboard.

Bruecke zwischen ROS2-Topics und Web-Clients:
  - WebSocket-Server (Port 9090): Telemetrie-JSON (10 Hz), LiDAR-Scans (2 Hz),
    cmd_vel-Empfang und Heartbeat
  - MJPEG-HTTP-Server (Port 8082): Kamera-Livestream als MJPEG

Sicherheitsmechanismen:
  - Geschwindigkeitsbegrenzung (0.4 m/s linear, 1.0 rad/s angular)
  - Deadman-Timer (300 ms ohne Heartbeat/cmd_vel -> Stopp)
  - Single-Controller (nur ein Client darf cmd_vel senden)
  - Client-Disconnect -> sofortiger Stopp

Verwendung:
  ros2 run my_bot dashboard_bridge
  ros2 launch my_bot full_stack.launch.py use_dashboard:=True
"""

import base64
import glob as globmod
import json
import math
import os
import socket
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import rclpy
from geometry_msgs.msg import Point, PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import BatteryState, Image, Imu, LaserScan, Range
from std_msgs.msg import Bool, Int32, String
from tf2_msgs.msg import TFMessage

try:
    import asyncio

    import websockets
except ImportError:
    websockets = None

try:
    import cv2
    from cv_bridge import CvBridge

    HAS_CAMERA = True
except ImportError:
    HAS_CAMERA = False

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
WS_PORT = 9090
MJPEG_PORT = 8082
TELEMETRY_HZ = 10.0
SCAN_BROADCAST_HZ = 2.0
DEADMAN_TIMEOUT_S = 0.3
MAX_LINEAR = 0.4  # m/s
MAX_ANGULAR = 1.0  # rad/s
JPEG_QUALITY = 70
HZ_WINDOW = 50  # Anzahl Timestamps fuer Hz-Berechnung
SYSTEM_BROADCAST_HZ = 1.0  # System-Metriken Broadcast-Rate
MAP_BROADCAST_HZ = 0.5  # Karten-Broadcast-Rate
MAP_PNG_QUALITY = 6  # PNG-Kompressionsgrad (0-9)
DETECTION_BROADCAST_HZ = 5.0  # Vision-Detektionen Broadcast-Rate
SEMANTICS_BROADCAST_HZ = 0.5  # Semantische Analyse Broadcast-Rate
NAV_STATUS_BROADCAST_HZ = 1.0  # Navigationsstatus Broadcast-Rate

# Batterie: OCV-SOC-Tabelle (3S Li-Ion, Samsung INR18650-35E)
BATTERY_CAPACITY_MAH = 3350.0
BATTERY_EMA_ALPHA = 0.05
OCV_SOC_TABLE = [
    (12.60, 100.0),
    (12.30, 90.0),
    (12.00, 80.0),
    (11.70, 65.0),
    (11.40, 50.0),
    (11.10, 35.0),
    (10.80, 20.0),
    (10.50, 10.0),
    (10.20, 5.0),
    (9.60, 2.0),
    (9.00, 0.0),
]


def ocv_to_soc(voltage):
    """OCV-Spannung -> SOC (%) via lineare Interpolation."""
    if voltage >= OCV_SOC_TABLE[0][0]:
        return OCV_SOC_TABLE[0][1]
    if voltage <= OCV_SOC_TABLE[-1][0]:
        return OCV_SOC_TABLE[-1][1]
    for i in range(len(OCV_SOC_TABLE) - 1):
        v_high, soc_high = OCV_SOC_TABLE[i]
        v_low, soc_low = OCV_SOC_TABLE[i + 1]
        if v_low <= voltage <= v_high:
            frac = (voltage - v_low) / (v_high - v_low)
            return soc_low + frac * (soc_high - soc_low)
    return 0.0


def quaternion_to_yaw(q):
    """Quaternion (x, y, z, w) -> Yaw-Winkel in Radiant."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def clamp(val, limit):
    """Begrenzt val auf [-limit, +limit]."""
    return max(min(val, limit), -limit)


# =========================================================================
# MJPEG HTTP Server
# =========================================================================
class MjpegHandler(BaseHTTPRequestHandler):
    """HTTP-Handler fuer MJPEG-Stream und einfache Testseite."""

    # Referenz auf den ROS2-Node (wird in start_mjpeg_server gesetzt)
    bridge_node = None

    def log_message(self, fmt, *args):
        """Unterdrueckt Standard-HTTP-Logging."""
        pass

    def do_GET(self):
        if self.path == "/stream":
            self._handle_stream()
        elif self.path == "/":
            self._handle_index()
        else:
            self.send_error(404)

    def _handle_index(self):
        html = (
            "<html><head><title>AMR Kamera</title></head>"
            '<body style="margin:0;background:#111;">'
            '<img src="/stream" style="width:100%;height:auto;" />'
            "</body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _handle_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        node = MjpegHandler.bridge_node
        if node is None:
            return
        while True:
            jpeg_bytes = node.get_latest_jpeg()
            if jpeg_bytes is None:
                time.sleep(0.1)
                continue
            try:
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(jpeg_bytes)}\r\n\r\n".encode())
                self.wfile.write(jpeg_bytes)
                self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                break


def start_mjpeg_server(node):
    """Startet den MJPEG-HTTP-Server in einem Daemon-Thread."""
    MjpegHandler.bridge_node = node
    server = ThreadingHTTPServer(("0.0.0.0", MJPEG_PORT), MjpegHandler)
    server.daemon_threads = True
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    node.get_logger().info(f"MJPEG-Server gestartet auf http://0.0.0.0:{MJPEG_PORT}/stream")


# =========================================================================
# WebSocket Server (asyncio)
# =========================================================================
class WebSocketServer:
    """Asyncio-basierter WebSocket-Server fuer Telemetrie und Steuerung."""

    def __init__(self, node):
        self.node = node
        self.clients = set()
        self.controller_ws = None  # Nur ein Client darf cmd_vel senden
        self.loop = None

    async def handler(self, ws):
        """Verbindungs-Handler fuer neue WebSocket-Clients."""
        self.clients.add(ws)
        self.node.get_logger().info(f"WebSocket-Client verbunden ({len(self.clients)} aktiv)")
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                self._handle_message(ws, msg)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(ws)
            if self.controller_ws is ws:
                self.controller_ws = None
                self.node.publish_stop()
                self.node.get_logger().info("Controller-Client getrennt -> Stopp gesendet")
            self.node.get_logger().info(f"WebSocket-Client getrennt ({len(self.clients)} aktiv)")

    def _handle_message(self, ws, msg):
        op = msg.get("op", "")
        if op == "cmd_vel":
            # Single-Controller: erster Client = Controller
            if self.controller_ws is None:
                self.controller_ws = ws
            if ws is not self.controller_ws:
                return  # Nicht der Controller
            lin_x = clamp(float(msg.get("linear_x", 0.0)), MAX_LINEAR)
            ang_z = clamp(float(msg.get("angular_z", 0.0)), MAX_ANGULAR)
            self.node.publish_cmd_vel(lin_x, ang_z)
        elif op == "servo_cmd":
            pan = float(msg.get("pan", 90.0))
            tilt = float(msg.get("tilt", 90.0))
            self.node.publish_servo_cmd(pan, tilt)
        elif op == "hardware_cmd":
            motor_limit = max(0.0, min(100.0, float(msg.get("motor_limit", 100.0))))
            servo_speed = max(1.0, min(10.0, float(msg.get("servo_speed", 5.0))))
            led_pwm = max(0.0, min(255.0, float(msg.get("led_pwm", 0.0))))
            self.node.publish_hardware_cmd(motor_limit, servo_speed, led_pwm)
        elif op == "heartbeat":
            self.node.record_heartbeat()
        elif op == "nav_goal":
            x = float(msg.get("x", 0.0))
            y = float(msg.get("y", 0.0))
            yaw = float(msg.get("yaw", 0.0))
            self.node.send_nav_goal(x, y, yaw)
        elif op == "nav_cancel":
            self.node.cancel_nav_goal()
        elif op == "audio_play":
            key = msg.get("sound_key", "")
            if key in ("cliff_alarm", "nav_start", "nav_reached", "startup"):
                self.node.publish_audio_play(key)
        elif op == "audio_volume":
            vol = max(0, min(100, int(msg.get("volume_percent", 80))))
            self.node.publish_audio_volume(vol)

    async def broadcast(self, data_str):
        """Sendet JSON-String an alle verbundenen Clients."""
        if not self.clients:
            return
        stale = set()
        for ws in list(self.clients):
            try:
                await ws.send(data_str)
            except (websockets.exceptions.ConnectionClosed, Exception):
                stale.add(ws)
        for ws in stale:
            self.clients.discard(ws)
            if self.controller_ws is ws:
                self.controller_ws = None
                self.node.publish_stop()

    async def _run(self):
        """Startet den WebSocket-Server und Broadcast-Loops."""
        async with websockets.serve(
            self.handler,
            "0.0.0.0",
            WS_PORT,
            ping_interval=20,
            ping_timeout=10,
        ):
            self.node.get_logger().info(f"WebSocket-Server gestartet auf ws://0.0.0.0:{WS_PORT}")
            # Telemetrie-, Scan-, System-, Map-, Vision- und Sensor-Broadcast parallel
            await asyncio.gather(
                self._telemetry_loop(),
                self._scan_loop(),
                self._system_loop(),
                self._map_loop(),
                self._detections_loop(),
                self._semantics_loop(),
                self._nav_status_loop(),
                self._sensor_status_loop(),
                self._audio_status_loop(),
            )

    async def _telemetry_loop(self):
        """Sendet Telemetrie-JSON mit 10 Hz."""
        interval = 1.0 / TELEMETRY_HZ
        while True:
            data = self.node.build_telemetry()
            await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _scan_loop(self):
        """Sendet LiDAR-Scans mit 2 Hz."""
        interval = 1.0 / SCAN_BROADCAST_HZ
        while True:
            data = self.node.build_scan_msg()
            if data is not None:
                await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _system_loop(self):
        """Sendet System-Metriken mit 1 Hz."""
        interval = 1.0 / SYSTEM_BROADCAST_HZ
        while True:
            data = self.node.build_system_msg()
            await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _map_loop(self):
        """Sendet SLAM-Karte mit 0.5 Hz."""
        interval = 1.0 / MAP_BROADCAST_HZ
        while True:
            data = self.node.build_map_msg()
            if data is not None:
                await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _detections_loop(self):
        """Sendet Vision-Detektionen mit 5 Hz."""
        interval = 1.0 / DETECTION_BROADCAST_HZ
        while True:
            data = self.node.build_detections_msg()
            if data is not None:
                await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _semantics_loop(self):
        """Sendet semantische Analyse mit 0.5 Hz."""
        interval = 1.0 / SEMANTICS_BROADCAST_HZ
        while True:
            data = self.node.build_semantics_msg()
            if data is not None:
                await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _nav_status_loop(self):
        """Sendet Navigationsstatus mit 1 Hz."""
        interval = 1.0 / NAV_STATUS_BROADCAST_HZ
        while True:
            data = self.node.build_nav_status_msg()
            if data is not None:
                await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _sensor_status_loop(self):
        """Sendet Sensor-Status mit 2 Hz."""
        while True:
            await asyncio.sleep(0.5)
            msg = self.node.build_sensor_status_msg()
            await self.broadcast(json.dumps(msg))

    async def _audio_status_loop(self):
        """Sendet Audio-Status mit 2 Hz."""
        while True:
            await asyncio.sleep(0.5)
            msg = self.node.build_audio_status_msg()
            await self.broadcast(json.dumps(msg))

    def start(self):
        """Startet die asyncio Event-Loop in einem Daemon-Thread."""

        def _run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run())

        t = threading.Thread(target=_run_loop, daemon=True)
        t.start()


# =========================================================================
# ROS2 Node
# =========================================================================
class DashboardBridge(Node):
    """ROS2-Node: Bruecke zwischen ROS2-Topics und Web-Dashboard."""

    def __init__(self):
        super().__init__("dashboard_bridge")

        # --- Shared State (geschuetzt durch Lock) ---
        self.lock = threading.Lock()
        self.latest_odom = None
        self.latest_imu = None
        self.latest_scan = None
        self.latest_jpeg = None
        self.odom_times = deque(maxlen=HZ_WINDOW)
        self.scan_times = deque(maxlen=HZ_WINDOW)
        self.odom_latencies = deque(maxlen=100)
        self.imu_latencies = deque(maxlen=100)
        self._last_latency_log = 0.0
        self.last_cmd_time = 0.0
        self.last_heartbeat_time = 0.0
        self.battery_data = None  # dict: voltage, current, power, percentage, runtime_min
        self.battery_ema_current_a = 0.0
        self.battery_ema_initialized = False
        self.servo_pan = 90.0  # Letzte Servo-Pan-Position (Grad)
        self.servo_tilt = 90.0  # Letzte Servo-Tilt-Position (Grad)
        self.hw_motor_limit = 100.0  # Motor-Limit 0-100%
        self.hw_servo_speed = 5.0  # Servo-Speed 1-10
        self.hw_led_pwm = 0.0  # LED-PWM 0-255 (0 = Auto-Heartbeat)
        self.prev_cpu_stats = None  # /proc/stat Vorheriger Zustand

        # --- Sensor-Status (Ultraschall, Cliff, IMU-Hz) ---
        self.ultrasonic_range = 0.0
        self.ultrasonic_times = deque(maxlen=HZ_WINDOW)
        self.cliff_detected = False
        self.cliff_times = deque(maxlen=HZ_WINDOW)
        self.imu_times = deque(maxlen=HZ_WINDOW)

        # --- Audio-Status (ReSpeaker, Spracherkennung) ---
        self.sound_direction = 0
        self.is_voice = False
        self._last_sound_dir_time = 0.0

        # --- CvBridge (Kamera) ---
        self.cv_bridge = CvBridge() if HAS_CAMERA else None

        # --- ROS2 Subscriptions ---
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.sub_odom = self.create_subscription(Odometry, "/odom", self._odom_cb, 10)
        self.sub_imu = self.create_subscription(Imu, "/imu", self._imu_cb, 10)
        self.sub_scan = self.create_subscription(LaserScan, "/scan", self._scan_cb, sensor_qos)
        if HAS_CAMERA:
            self.sub_image = self.create_subscription(
                Image, "/camera/image_raw", self._image_cb, sensor_qos
            )
        self.sub_map = self.create_subscription(
            OccupancyGrid,
            "/map",
            self._map_cb,
            QoSProfile(
                reliability=ReliabilityPolicy.RELIABLE,
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
            ),
        )
        self.sub_tf = self.create_subscription(TFMessage, "/tf", self._tf_cb, 10)
        self.sub_detections = self.create_subscription(
            String, "/vision/detections", self._detections_cb, 10
        )
        self.sub_semantics = self.create_subscription(
            String, "/vision/semantics", self._semantics_cb, 10
        )
        self.sub_battery = self.create_subscription(
            BatteryState, "/battery", self._battery_cb, sensor_qos
        )
        self.sub_range_front = self.create_subscription(
            Range, "/range/front", self._range_front_cb, sensor_qos
        )
        self.sub_cliff = self.create_subscription(Bool, "/cliff", self._cliff_cb, sensor_qos)
        self.sub_sound_dir = self.create_subscription(
            Int32, "/sound_direction", self._sound_dir_cb, 10
        )
        self.sub_is_voice = self.create_subscription(Bool, "/is_voice", self._is_voice_cb, 10)

        # --- Map / TF State (geschuetzt durch Lock) ---
        self.latest_map_png = None  # Base64 string
        self.map_metadata = None  # dict
        self.map_to_odom_tf = None  # dict

        # --- Vision State (geschuetzt durch Lock) ---
        self.latest_detections = None  # dict (geparster JSON)
        self.latest_semantics = None  # dict (geparster JSON)
        self.detection_times = deque(maxlen=HZ_WINDOW)
        self.camera_image_width = 1456
        self.camera_image_height = 1088

        # --- Navigation Action Client ---
        self.nav_client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.nav_goal_handle = None
        self.nav_status = "idle"  # idle, navigating, reached, failed, cancelled
        self.nav_goal_x = 0.0
        self.nav_goal_y = 0.0
        self.nav_goal_yaw = 0.0
        self.nav_remaining_m = 0.0

        # --- ROS2 Publisher ---
        self.pub_cmd_vel = self.create_publisher(Twist, "/cmd_vel", 10)
        self.pub_servo_cmd = self.create_publisher(Point, "/servo_cmd", 10)
        self.pub_hardware_cmd = self.create_publisher(Point, "/hardware_cmd", 10)
        self.pub_audio_play = self.create_publisher(String, "/audio/play", 10)
        self.pub_audio_volume = self.create_publisher(Int32, "/audio/volume", 10)
        self.audio_volume_pct = 80  # Default-Lautstaerke

        # --- Deadman-Timer (300 ms) ---
        self.deadman_timer = self.create_timer(DEADMAN_TIMEOUT_S, self._deadman_cb)

        # --- WebSocket-Server ---
        if websockets is None:
            self.get_logger().error(
                'Python-Paket "websockets" nicht installiert! WebSocket-Server deaktiviert.'
            )
            self.ws_server = None
        else:
            self.ws_server = WebSocketServer(self)
            self.ws_server.start()

        # --- MJPEG-Server ---
        if HAS_CAMERA:
            start_mjpeg_server(self)
        else:
            self.get_logger().warn("cv2/cv_bridge nicht verfuegbar -> MJPEG-Server deaktiviert")

        self.get_logger().info("DashboardBridge gestartet")

    # --- ROS2 Callbacks ---

    def _odom_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_odom = msg
            self.odom_times.append(now)
            stamp_s = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp_s > 1e9:
                latency_ms = (now - stamp_s) * 1000.0
                if -500.0 < latency_ms < 2000.0:
                    self.odom_latencies.append(latency_ms)

    def _imu_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_imu = msg
            self.imu_times.append(now)
            stamp_s = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp_s > 1e9:
                latency_ms = (now - stamp_s) * 1000.0
                if -500.0 < latency_ms < 2000.0:
                    self.imu_latencies.append(latency_ms)

    def _scan_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_scan = msg
            self.scan_times.append(now)

    def _image_cb(self, msg):
        if self.cv_bridge is None:
            return
        try:
            cv_img = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            h, w = cv_img.shape[:2]
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            ok, buf = cv2.imencode(".jpg", cv_img, encode_param)
            if ok:
                with self.lock:
                    self.latest_jpeg = buf.tobytes()
                    self.camera_image_width = w
                    self.camera_image_height = h
        except Exception as e:
            self.get_logger().warn(f"Bild-Konvertierung fehlgeschlagen: {e}")

    def _detections_cb(self, msg):
        """Parst /vision/detections JSON und normalisiert BBoxen."""
        now = time.time()
        try:
            data = json.loads(msg.data)
            detections = data.get("detections", [])
            inference_ms = data.get("inference_ms", 0.0)
            with self.lock:
                img_w = self.camera_image_width
                img_h = self.camera_image_height
                self.detection_times.append(now)
            # BBoxen normalisieren (Pixel -> 0.0-1.0)
            for det in detections:
                bbox = det.get("bbox", [0, 0, 0, 0])
                det["bbox_norm"] = [
                    bbox[0] / img_w,
                    bbox[1] / img_h,
                    bbox[2] / img_w,
                    bbox[3] / img_h,
                ]
            with self.lock:
                self.latest_detections = {
                    "detections": detections,
                    "inference_ms": inference_ms,
                }
        except (json.JSONDecodeError, Exception) as e:
            self.get_logger().warn(f"Detection-Parse fehlgeschlagen: {e}")

    def _semantics_cb(self, msg):
        """Parst /vision/semantics JSON."""
        try:
            data = json.loads(msg.data)
            with self.lock:
                self.latest_semantics = {
                    "analysis": data.get("semantic_analysis", ""),
                    "model": data.get("model", ""),
                }
        except (json.JSONDecodeError, Exception) as e:
            self.get_logger().warn(f"Semantics-Parse fehlgeschlagen: {e}")

    def _battery_cb(self, msg):
        """Speichert BatteryState-Daten (INA260) mit OCV-SOC und EMA-Laufzeit."""
        voltage = msg.voltage
        current_abs = abs(msg.current)

        # EMA-geglaetteter Strom
        if not self.battery_ema_initialized:
            self.battery_ema_current_a = current_abs
            self.battery_ema_initialized = True
        else:
            self.battery_ema_current_a = (
                BATTERY_EMA_ALPHA * current_abs
                + (1.0 - BATTERY_EMA_ALPHA) * self.battery_ema_current_a
            )

        # SOC aus OCV-Tabelle
        soc = ocv_to_soc(voltage)

        # Restlaufzeit: (Kapazitaet_mAh * SOC/100) / I_avg_mA * 60 [min]
        runtime_min = -1.0
        i_avg_ma = self.battery_ema_current_a * 1000.0
        if i_avg_ma > 50.0 and soc > 0.0:
            runtime_min = (BATTERY_CAPACITY_MAH * soc / 100.0) / i_avg_ma * 60.0

        with self.lock:
            self.battery_data = {
                "voltage": round(voltage, 3),
                "current": round(msg.current, 3),
                "power": round(voltage * msg.current, 3),
                "percentage": round(soc, 1),
                "runtime_min": round(runtime_min, 1),
            }

    def _range_front_cb(self, msg):
        """Speichert Ultraschall-Entfernung (Range)."""
        with self.lock:
            self.ultrasonic_range = msg.range
            self.ultrasonic_times.append(time.time())

    def _cliff_cb(self, msg):
        """Speichert Cliff-Erkennungsstatus (Bool)."""
        with self.lock:
            self.cliff_detected = msg.data
            self.cliff_times.append(time.time())

    def _sound_dir_cb(self, msg):
        """Speichert Schallrichtung (Int32, Grad)."""
        with self.lock:
            self.sound_direction = msg.data
            self._last_sound_dir_time = time.time()

    def _is_voice_cb(self, msg):
        """Speichert Spracherkennungsstatus (Bool)."""
        with self.lock:
            self.is_voice = msg.data

    def _map_cb(self, msg):
        """OccupancyGrid -> RGBA PNG -> Base64."""
        try:
            width = msg.info.width
            height = msg.info.height
            if width == 0 or height == 0:
                return
            grid = np.array(msg.data, dtype=np.int8).reshape((height, width))

            # RGBA-Bild erzeugen (Saugroboter-Stil)
            rgba = np.zeros((height, width, 4), dtype=np.uint8)
            # Unbekannt (-1): fast schwarz, opak
            unknown = grid == -1
            rgba[unknown] = [20, 24, 36, 255]
            # Frei (0): hellblau (befahrbare Flaeche)
            free = grid == 0
            rgba[free] = [106, 148, 191, 255]
            # Belegt (>50): dunkelgrau (Waende/Hindernisse)
            occupied = grid > 50
            rgba[occupied] = [45, 55, 72, 255]
            # Partial (1-50): Gradient blau → grau
            partial = (grid > 0) & (grid <= 50)
            if np.any(partial):
                vals = grid[partial].astype(np.float32) / 50.0
                rgba[partial, 0] = (106 + vals * (45 - 106)).astype(np.uint8)
                rgba[partial, 1] = (148 + vals * (55 - 148)).astype(np.uint8)
                rgba[partial, 2] = (191 + vals * (72 - 191)).astype(np.uint8)
                rgba[partial, 3] = 255

            # ROS Y-oben -> Bild Y-unten
            rgba = np.flipud(rgba)

            # BGRA fuer cv2 (OpenCV erwartet BGRA, nicht RGBA)
            bgra = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
            ok, buf = cv2.imencode(".png", bgra, [cv2.IMWRITE_PNG_COMPRESSION, MAP_PNG_QUALITY])
            if not ok:
                return
            png_b64 = base64.b64encode(buf.tobytes()).decode("ascii")
            metadata = {
                "width": width,
                "height": height,
                "resolution": msg.info.resolution,
                "origin_x": msg.info.origin.position.x,
                "origin_y": msg.info.origin.position.y,
            }
            with self.lock:
                self.latest_map_png = png_b64
                self.map_metadata = metadata
        except Exception as e:
            self.get_logger().warn(f"Map-Konvertierung fehlgeschlagen: {e}")

    def _tf_cb(self, msg):
        """Speichert map->odom Transform."""
        for tf in msg.transforms:
            if tf.header.frame_id == "map" and tf.child_frame_id == "odom":
                t = tf.transform.translation
                q = tf.transform.rotation
                yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
                with self.lock:
                    self.map_to_odom_tf = {
                        "x": t.x,
                        "y": t.y,
                        "yaw": yaw,
                    }

    def _get_host_ip(self):
        """Ermittelt die Host-IP-Adresse ueber UDP-Socket-Trick."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            pass
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

    # --- Deadman-Timer ---

    def _deadman_cb(self):
        now = time.time()
        with self.lock:
            last_cmd = self.last_cmd_time
            last_hb = self.last_heartbeat_time
        # Pruefen ob Steuerbefehle oder Heartbeat empfangen wurden
        last_activity = max(last_cmd, last_hb)
        if last_activity > 0.0 and (now - last_activity) > DEADMAN_TIMEOUT_S:
            self.publish_stop()

    # --- Publizier-Methoden (thread-safe) ---

    def publish_cmd_vel(self, linear_x, angular_z):
        """Publiziert Twist auf /cmd_vel mit Geschwindigkeitsbegrenzung."""
        twist = Twist()
        twist.linear.x = clamp(float(linear_x), MAX_LINEAR)
        twist.angular.z = clamp(float(angular_z), MAX_ANGULAR)
        self.pub_cmd_vel.publish(twist)
        with self.lock:
            self.last_cmd_time = time.time()

    def publish_stop(self):
        """Publiziert Twist(0,0,0) auf /cmd_vel."""
        self.pub_cmd_vel.publish(Twist())

    def publish_servo_cmd(self, pan, tilt):
        """Publiziert Servo-Kommando auf /servo_cmd (Point: x=pan, y=tilt, z=0)."""
        point = Point()
        point.x = float(pan)
        point.y = float(tilt)
        point.z = 0.0
        self.pub_servo_cmd.publish(point)
        with self.lock:
            self.servo_pan = float(pan)
            self.servo_tilt = float(tilt)

    def publish_hardware_cmd(self, motor_limit, servo_speed, led_pwm):
        """Publiziert Hardware-Parameter auf /hardware_cmd (Point: x=motor, y=servo_speed, z=led)."""
        msg = Point()
        msg.x = float(motor_limit)
        msg.y = float(servo_speed)
        msg.z = float(led_pwm)
        self.pub_hardware_cmd.publish(msg)
        with self.lock:
            self.hw_motor_limit = motor_limit
            self.hw_servo_speed = servo_speed
            self.hw_led_pwm = led_pwm

    def record_heartbeat(self):
        """Aktualisiert den Heartbeat-Zeitstempel."""
        with self.lock:
            self.last_heartbeat_time = time.time()

    def publish_audio_play(self, sound_key):
        """Publiziert Audio-Wiedergabe-Kommando auf /audio/play."""
        msg = String()
        msg.data = str(sound_key)
        self.pub_audio_play.publish(msg)

    def publish_audio_volume(self, volume_pct):
        """Publiziert Lautstaerke (0-100%) auf /audio/volume."""
        self.audio_volume_pct = volume_pct
        msg = Int32()
        msg.data = volume_pct
        self.pub_audio_volume.publish(msg)

    # --- Daten-Abfragen (thread-safe) ---

    def get_latest_jpeg(self):
        """Gibt das letzte JPEG-Bild als Bytes zurueck (oder None)."""
        with self.lock:
            return self.latest_jpeg

    def _compute_hz(self, timestamps):
        """Berechnet die Frequenz aus einer Timestamp-Deque (Lock muss gehalten werden)."""
        if len(timestamps) < 2:
            return 0.0
        dt = timestamps[-1] - timestamps[0]
        if dt <= 0.0:
            return 0.0
        return (len(timestamps) - 1) / dt

    def _compute_latency_stats(self, latencies):
        """Berechnet Latenz-Statistiken aus einer deque (Lock muss gehalten werden)."""
        if len(latencies) < 5:
            return None
        vals = sorted(latencies)
        return {
            "min_ms": round(vals[0], 1),
            "avg_ms": round(sum(vals) / len(vals), 1),
            "max_ms": round(vals[-1], 1),
            "p95_ms": round(vals[int(len(vals) * 0.95)], 1),
            "samples": len(vals),
        }

    def build_telemetry(self):
        """Erstellt das Telemetrie-JSON-Dictionary."""
        with self.lock:
            odom = self.latest_odom
            imu = self.latest_imu
            odom_hz = self._compute_hz(self.odom_times)
            scan_hz = self._compute_hz(self.scan_times)
            battery = self.battery_data
            servo_pan = self.servo_pan
            servo_tilt = self.servo_tilt
            hw_motor_limit = self.hw_motor_limit
            hw_servo_speed = self.hw_servo_speed
            hw_led_pwm = self.hw_led_pwm
            latency_stats = self._compute_latency_stats(self.odom_latencies)

        # Odom-Daten
        odom_data = {
            "x": 0.0,
            "y": 0.0,
            "yaw_deg": 0.0,
            "vel_linear": 0.0,
            "vel_angular": 0.0,
        }
        if odom is not None:
            yaw = quaternion_to_yaw(odom.pose.pose.orientation)
            odom_data = {
                "x": round(odom.pose.pose.position.x, 4),
                "y": round(odom.pose.pose.position.y, 4),
                "yaw_deg": round(math.degrees(yaw), 2),
                "vel_linear": round(odom.twist.twist.linear.x, 4),
                "vel_angular": round(odom.twist.twist.angular.z, 4),
            }

        # IMU-Daten
        imu_data = {"heading_deg": 0.0, "gz_deg_s": 0.0}
        if imu is not None:
            imu_yaw = quaternion_to_yaw(imu.orientation)
            imu_data = {
                "heading_deg": round(math.degrees(imu_yaw), 2),
                "gz_deg_s": round(math.degrees(imu.angular_velocity.z), 2),
            }

        # Verbindungsstatus
        esp32_active = odom_hz > 1.0

        # Periodisches Latenz-Logging
        now_log = time.time()
        if now_log - self._last_latency_log > 30.0:
            self._last_latency_log = now_log
            if latency_stats:
                self.get_logger().info(
                    f"Serial-Latenz: avg={latency_stats['avg_ms']:.1f} ms, "
                    f"p95={latency_stats['p95_ms']:.1f} ms, "
                    f"max={latency_stats['max_ms']:.1f} ms "
                    f"(n={latency_stats['samples']})"
                )

        return {
            "op": "telemetry",
            "ts": round(time.time(), 3),
            "odom": odom_data,
            "imu": imu_data,
            "battery": battery,
            "servo": {
                "pan": servo_pan,
                "tilt": servo_tilt,
            },
            "hardware": {
                "motor_limit": hw_motor_limit,
                "servo_speed": hw_servo_speed,
                "led_pwm": hw_led_pwm,
            },
            "connection": {
                "esp32_active": esp32_active,
                "odom_hz": round(odom_hz, 1),
                "scan_hz": round(scan_hz, 1),
                "latency": latency_stats,
            },
        }

    def build_scan_msg(self):
        """Erstellt das Scan-JSON-Dictionary (oder None)."""
        with self.lock:
            scan = self.latest_scan
        if scan is None:
            return None
        # NaN/Inf durch 0.0 ersetzen fuer JSON-Kompatibilitaet
        ranges = []
        for r in scan.ranges:
            if math.isnan(r) or math.isinf(r):
                ranges.append(0.0)
            else:
                ranges.append(round(r, 3))
        # NOTE: Scan-Daten werden im Sensor-Frame (laser) gesendet.
        # Der RPLidar ist 180° gedreht montiert (TF: base_link->laser, yaw=pi).
        # Die Winkelkorrektur erfolgt im Frontend (LidarView.tsx, SENSOR_YAW_OFFSET).
        return {
            "op": "scan",
            "angle_min": round(scan.angle_min, 4),
            "angle_max": round(scan.angle_max, 4),
            "angle_increment": round(scan.angle_increment, 6),
            "ranges": ranges,
        }

    def build_map_msg(self):
        """Erstellt das Map-JSON-Dictionary (oder None)."""
        with self.lock:
            png_b64 = self.latest_map_png
            metadata = self.map_metadata
            tf_data = self.map_to_odom_tf
            odom = self.latest_odom

        if png_b64 is None or metadata is None:
            return None

        # Roboterposition im Map-Frame
        robot_x, robot_y, robot_yaw = 0.0, 0.0, 0.0
        if odom is not None:
            ox = odom.pose.pose.position.x
            oy = odom.pose.pose.position.y
            o_yaw = quaternion_to_yaw(odom.pose.pose.orientation)
            if tf_data is not None:
                # P_map = T_map_odom * P_odom
                tf_yaw = tf_data["yaw"]
                cos_y = math.cos(tf_yaw)
                sin_y = math.sin(tf_yaw)
                robot_x = tf_data["x"] + cos_y * ox - sin_y * oy
                robot_y = tf_data["y"] + sin_y * ox + cos_y * oy
                robot_yaw = tf_yaw + o_yaw
            else:
                # Ohne TF: Odom direkt als Naeherung
                robot_x = ox
                robot_y = oy
                robot_yaw = o_yaw

        return {
            "op": "map",
            "ts": round(time.time(), 3),
            "png_b64": png_b64,
            "width": metadata["width"],
            "height": metadata["height"],
            "resolution": metadata["resolution"],
            "origin_x": metadata["origin_x"],
            "origin_y": metadata["origin_y"],
            "robot": {
                "x": round(robot_x, 4),
                "y": round(robot_y, 4),
                "yaw": round(robot_yaw, 4),
            },
        }

    def _read_proc_stat(self):
        """Liest /proc/stat -> dict {cpuN: (user, nice, system, idle, iowait, irq, softirq, steal)}."""
        result = {}
        try:
            with open("/proc/stat") as f:
                for line in f:
                    if line.startswith("cpu") and line[3] != " ":
                        parts = line.split()
                        name = parts[0]
                        vals = tuple(int(x) for x in parts[1:9])
                        result[name] = vals
        except (OSError, ValueError):
            pass
        return result

    def _compute_per_cpu_pct(self):
        """Berechnet Per-CPU-Auslastung in % als Delta zum vorherigen Reading."""
        cur = self._read_proc_stat()
        if not cur:
            return []
        if self.prev_cpu_stats is None:
            self.prev_cpu_stats = cur
            return []
        pcts = []
        for name in sorted(cur.keys()):
            if name not in self.prev_cpu_stats:
                continue
            prev = self.prev_cpu_stats[name]
            now = cur[name]
            idle_delta = (now[3] + now[4]) - (prev[3] + prev[4])
            total_delta = sum(now) - sum(prev)
            if total_delta > 0:
                pcts.append(round((1.0 - idle_delta / total_delta) * 100.0, 1))
            else:
                pcts.append(0.0)
        self.prev_cpu_stats = cur
        return pcts

    def build_system_msg(self):
        """Erstellt das System-Metriken-JSON-Dictionary."""
        # CPU-Temperatur
        cpu_temp = 0.0
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                cpu_temp = int(f.read().strip()) / 1000.0
        except (OSError, ValueError):
            pass

        # CPU-Load + Prozesse
        load_1m, load_5m, load_15m = 0.0, 0.0, 0.0
        proc_running, proc_total = 0, 0
        try:
            with open("/proc/loadavg") as f:
                parts = f.read().strip().split()
                load_1m = float(parts[0])
                load_5m = float(parts[1])
                load_15m = float(parts[2])
                if "/" in parts[3]:
                    r, t = parts[3].split("/")
                    proc_running = int(r)
                    proc_total = int(t)
        except (OSError, ValueError, IndexError):
            pass

        # Uptime
        uptime_s = 0.0
        try:
            with open("/proc/uptime") as f:
                uptime_s = float(f.read().strip().split()[0])
        except (OSError, ValueError, IndexError):
            pass

        # Per-CPU-Auslastung
        per_cpu_pct = self._compute_per_cpu_pct()

        # CPU-Frequenzen
        freq_mhz = []
        for path in sorted(globmod.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq")):
            try:
                with open(path) as f:
                    freq_mhz.append(int(f.read().strip()) // 1000)
            except (OSError, ValueError):
                pass

        # RAM
        ram_total, ram_avail = 0, 0
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        ram_total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        ram_avail = int(line.split()[1])
        except (OSError, ValueError):
            pass
        ram_total_mb = ram_total / 1024.0
        ram_used_mb = (ram_total - ram_avail) / 1024.0
        ram_pct = (ram_used_mb / ram_total_mb * 100.0) if ram_total_mb > 0 else 0.0

        # Disk
        disk_total_gb, disk_used_gb, disk_pct = 0.0, 0.0, 0.0
        try:
            st = os.statvfs("/")
            disk_total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
            disk_free_gb = (st.f_bfree * st.f_frsize) / (1024**3)
            disk_used_gb = disk_total_gb - disk_free_gb
            disk_pct = (disk_used_gb / disk_total_gb * 100.0) if disk_total_gb > 0 else 0.0
        except OSError:
            pass

        # Geraete-Status
        with self.lock:
            odom_hz = self._compute_hz(self.odom_times)
            scan_hz = self._compute_hz(self.scan_times)
            det_hz = self._compute_hz(self.detection_times)
            imu_hz = self._compute_hz(self.imu_times)
            has_jpeg = self.latest_jpeg is not None
            has_battery = self.battery_data is not None
            last_sound_dir_time = self._last_sound_dir_time

        return {
            "op": "system",
            "ts": round(time.time(), 3),
            "cpu": {
                "temp_c": round(cpu_temp, 1),
                "load_1m": round(load_1m, 2),
                "load_5m": round(load_5m, 2),
                "load_15m": round(load_15m, 2),
                "freq_mhz": freq_mhz,
                "per_cpu_pct": per_cpu_pct,
            },
            "ram": {
                "total_mb": round(ram_total_mb, 0),
                "used_mb": round(ram_used_mb, 0),
                "usage_pct": round(ram_pct, 1),
            },
            "disk": {
                "total_gb": round(disk_total_gb, 1),
                "used_gb": round(disk_used_gb, 1),
                "usage_pct": round(disk_pct, 1),
            },
            "devices": {
                "esp32": odom_hz > 1.0,
                "lidar": scan_hz > 1.0,
                "camera": has_jpeg,
                "hailo": det_hz > 0.5 or os.path.exists("/dev/hailo0"),
                "ina260": has_battery,
                "audio": bool(imu_hz > 0),
                "respeaker": bool(time.time() - last_sound_dir_time < 5.0),
            },
            "ip": self._get_host_ip(),
            "uptime_s": round(uptime_s, 0),
            "processes": {
                "running": proc_running,
                "total": proc_total,
            },
        }

    # --- Navigation ---

    def send_nav_goal(self, x, y, yaw):
        """Sendet ein Navigationsziel an Nav2."""
        if not self.nav_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn("Nav2-Server nicht verfuegbar")
            with self.lock:
                self.nav_status = "failed"
            return

        # Vorheriges Ziel abbrechen
        if self.nav_goal_handle is not None:
            self.cancel_nav_goal()

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0
        # Yaw -> Quaternion
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        with self.lock:
            self.nav_goal_x = x
            self.nav_goal_y = y
            self.nav_goal_yaw = yaw
            self.nav_status = "navigating"

        self.get_logger().info(
            f"Nav-Goal gesendet: x={x:.2f}, y={y:.2f}, yaw={math.degrees(yaw):.1f} deg"
        )

        future = self.nav_client.send_goal_async(goal_msg, feedback_callback=self._nav_feedback_cb)
        future.add_done_callback(self._nav_goal_response_cb)

    def cancel_nav_goal(self):
        """Bricht das aktuelle Navigationsziel ab."""
        if self.nav_goal_handle is not None:
            self.get_logger().info("Nav-Goal abgebrochen")
            self.nav_goal_handle.cancel_goal_async()
            self.nav_goal_handle = None
        with self.lock:
            self.nav_status = "cancelled"

    def _nav_goal_response_cb(self, future):
        """Callback fuer die Goal-Antwort von Nav2."""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Nav-Goal abgelehnt")
            with self.lock:
                self.nav_status = "failed"
            return
        self.nav_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._nav_result_cb)

    def _nav_feedback_cb(self, feedback_msg):
        """Callback fuer Nav2-Feedback (Restdistanz)."""
        fb = feedback_msg.feedback
        pos = fb.current_pose.pose.position
        with self.lock:
            dx = self.nav_goal_x - pos.x
            dy = self.nav_goal_y - pos.y
            self.nav_remaining_m = math.sqrt(dx * dx + dy * dy)

    def _nav_result_cb(self, future):
        """Callback fuer das Nav2-Ergebnis."""
        result = future.result()
        status = result.status
        self.nav_goal_handle = None
        # status 4 = SUCCEEDED, 5 = CANCELED, 6 = ABORTED
        with self.lock:
            if status == 4:
                self.nav_status = "reached"
                self.nav_remaining_m = 0.0
                self.get_logger().info("Nav-Goal erreicht")
            elif status == 5:
                self.nav_status = "cancelled"
                self.get_logger().info("Nav-Goal abgebrochen (Nav2)")
            else:
                self.nav_status = "failed"
                self.get_logger().warn(f"Nav-Goal fehlgeschlagen (Status {status})")

    def build_nav_status_msg(self):
        """Erstellt das Nav-Status-JSON-Dictionary."""
        with self.lock:
            status = self.nav_status
            goal_x = self.nav_goal_x
            goal_y = self.nav_goal_y
            goal_yaw = self.nav_goal_yaw
            remaining = self.nav_remaining_m
        return {
            "op": "nav_status",
            "ts": round(time.time(), 3),
            "status": status,
            "goal_x": round(goal_x, 3),
            "goal_y": round(goal_y, 3),
            "goal_yaw": round(goal_yaw, 3),
            "remaining_distance_m": round(remaining, 2),
        }

    def build_sensor_status_msg(self):
        """Erstellt das Sensor-Status-JSON-Dictionary."""
        with self.lock:
            return {
                "op": "sensor_status",
                "ts": round(time.time(), 3),
                "ultrasonic": {
                    "range_m": round(self.ultrasonic_range, 3),
                    "hz": round(self._compute_hz(self.ultrasonic_times), 1),
                },
                "cliff": {
                    "detected": self.cliff_detected,
                    "hz": round(self._compute_hz(self.cliff_times), 1),
                },
                "imu_hz": round(self._compute_hz(self.imu_times), 1),
                "sensor_node_active": bool(
                    self._compute_hz(self.imu_times) > 1.0 or self.battery_data is not None
                ),
            }

    def build_audio_status_msg(self):
        """Erstellt das Audio-Status-JSON-Dictionary."""
        with self.lock:
            return {
                "op": "audio_status",
                "ts": round(time.time(), 3),
                "direction_deg": self.sound_direction,
                "is_voice": self.is_voice,
                "volume_percent": self.audio_volume_pct,
            }

    def build_detections_msg(self):
        """Erstellt das Vision-Detections-JSON-Dictionary (oder None)."""
        with self.lock:
            data = self.latest_detections
            det_hz = self._compute_hz(self.detection_times)
        if data is None:
            return None
        return {
            "op": "vision_detections",
            "ts": round(time.time(), 3),
            "inference_ms": round(data.get("inference_ms", 0.0), 1),
            "detections": data.get("detections", []),
            "detection_hz": round(det_hz, 1),
        }

    def build_semantics_msg(self):
        """Erstellt das Vision-Semantics-JSON-Dictionary (oder None)."""
        with self.lock:
            data = self.latest_semantics
        if data is None:
            return None
        return {
            "op": "vision_semantics",
            "ts": round(time.time(), 3),
            "analysis": data.get("analysis", ""),
            "model": data.get("model", ""),
        }


# =========================================================================
# Entry Point
# =========================================================================
def main(args=None):
    rclpy.init(args=args)
    node = DashboardBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Beende DashboardBridge...")
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
