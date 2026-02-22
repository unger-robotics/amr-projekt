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
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry, OccupancyGrid
from sensor_msgs.msg import Imu, LaserScan, Image
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
MAX_LINEAR = 0.4       # m/s
MAX_ANGULAR = 1.0      # rad/s
JPEG_QUALITY = 70
HZ_WINDOW = 50         # Anzahl Timestamps fuer Hz-Berechnung
SYSTEM_BROADCAST_HZ = 1.0  # System-Metriken Broadcast-Rate
MAP_BROADCAST_HZ = 0.5    # Karten-Broadcast-Rate
MAP_PNG_QUALITY = 6        # PNG-Kompressionsgrad (0-9)


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
        if self.path == '/stream':
            self._handle_stream()
        elif self.path == '/':
            self._handle_index()
        else:
            self.send_error(404)

    def _handle_index(self):
        html = (
            '<html><head><title>AMR Kamera</title></head>'
            '<body style="margin:0;background:#111;">'
            '<img src="/stream" style="width:100%;height:auto;" />'
            '</body></html>'
        )
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _handle_stream(self):
        self.send_response(200)
        self.send_header('Content-Type',
                         'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Access-Control-Allow-Origin', '*')
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
                self.wfile.write(b'--frame\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n')
                self.wfile.write(
                    ('Content-Length: %d\r\n\r\n' % len(jpeg_bytes)).encode()
                )
                self.wfile.write(jpeg_bytes)
                self.wfile.write(b'\r\n')
            except (BrokenPipeError, ConnectionResetError):
                break


def start_mjpeg_server(node):
    """Startet den MJPEG-HTTP-Server in einem Daemon-Thread."""
    MjpegHandler.bridge_node = node
    server = HTTPServer(('0.0.0.0', MJPEG_PORT), MjpegHandler)
    server.daemon_threads = True
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    node.get_logger().info(
        'MJPEG-Server gestartet auf http://0.0.0.0:%d/stream' % MJPEG_PORT
    )


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
        self.node.get_logger().info(
            'WebSocket-Client verbunden (%d aktiv)' % len(self.clients)
        )
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
                self.node.get_logger().info(
                    'Controller-Client getrennt -> Stopp gesendet'
                )
            self.node.get_logger().info(
                'WebSocket-Client getrennt (%d aktiv)' % len(self.clients)
            )

    def _handle_message(self, ws, msg):
        op = msg.get('op', '')
        if op == 'cmd_vel':
            # Single-Controller: erster Client = Controller
            if self.controller_ws is None:
                self.controller_ws = ws
            if ws is not self.controller_ws:
                return  # Nicht der Controller
            lin_x = clamp(float(msg.get('linear_x', 0.0)), MAX_LINEAR)
            ang_z = clamp(float(msg.get('angular_z', 0.0)), MAX_ANGULAR)
            self.node.publish_cmd_vel(lin_x, ang_z)
        elif op == 'heartbeat':
            self.node.record_heartbeat()

    async def broadcast(self, data_str):
        """Sendet JSON-String an alle verbundenen Clients."""
        if not self.clients:
            return
        stale = set()
        for ws in self.clients:
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
            self.handler, '0.0.0.0', WS_PORT,
            ping_interval=20, ping_timeout=10,
        ):
            self.node.get_logger().info(
                'WebSocket-Server gestartet auf ws://0.0.0.0:%d' % WS_PORT
            )
            # Telemetrie-, Scan-, System- und Map-Broadcast parallel
            await asyncio.gather(
                self._telemetry_loop(),
                self._scan_loop(),
                self._system_loop(),
                self._map_loop(),
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
        super().__init__('dashboard_bridge')

        # --- Shared State (geschuetzt durch Lock) ---
        self.lock = threading.Lock()
        self.latest_odom = None
        self.latest_imu = None
        self.latest_scan = None
        self.latest_jpeg = None
        self.odom_times = deque(maxlen=HZ_WINDOW)
        self.scan_times = deque(maxlen=HZ_WINDOW)
        self.last_cmd_time = 0.0
        self.last_heartbeat_time = 0.0

        # --- CvBridge (Kamera) ---
        self.cv_bridge = CvBridge() if HAS_CAMERA else None

        # --- ROS2 Subscriptions ---
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.sub_odom = self.create_subscription(
            Odometry, '/odom', self._odom_cb, 10
        )
        self.sub_imu = self.create_subscription(
            Imu, '/imu', self._imu_cb, 10
        )
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self._scan_cb, sensor_qos
        )
        if HAS_CAMERA:
            self.sub_image = self.create_subscription(
                Image, '/camera/image_raw', self._image_cb, sensor_qos
            )
        self.sub_map = self.create_subscription(
            OccupancyGrid, '/map', self._map_cb,
            QoSProfile(
                reliability=ReliabilityPolicy.RELIABLE,
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
            )
        )
        self.sub_tf = self.create_subscription(TFMessage, '/tf', self._tf_cb, 10)

        # --- Map / TF State (geschuetzt durch Lock) ---
        self.latest_map_png = None      # Base64 string
        self.map_metadata = None        # dict
        self.map_to_odom_tf = None      # dict

        # --- ROS2 Publisher ---
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # --- Deadman-Timer (300 ms) ---
        self.deadman_timer = self.create_timer(
            DEADMAN_TIMEOUT_S, self._deadman_cb
        )

        # --- WebSocket-Server ---
        if websockets is None:
            self.get_logger().error(
                'Python-Paket "websockets" nicht installiert! '
                'WebSocket-Server deaktiviert.'
            )
            self.ws_server = None
        else:
            self.ws_server = WebSocketServer(self)
            self.ws_server.start()

        # --- MJPEG-Server ---
        if HAS_CAMERA:
            start_mjpeg_server(self)
        else:
            self.get_logger().warn(
                'cv2/cv_bridge nicht verfuegbar -> MJPEG-Server deaktiviert'
            )

        self.get_logger().info('DashboardBridge gestartet')

    # --- ROS2 Callbacks ---

    def _odom_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_odom = msg
            self.odom_times.append(now)

    def _imu_cb(self, msg):
        with self.lock:
            self.latest_imu = msg

    def _scan_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_scan = msg
            self.scan_times.append(now)

    def _image_cb(self, msg):
        if self.cv_bridge is None:
            return
        try:
            cv_img = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            ok, buf = cv2.imencode('.jpg', cv_img, encode_param)
            if ok:
                with self.lock:
                    self.latest_jpeg = buf.tobytes()
        except Exception as e:
            self.get_logger().warn('Bild-Konvertierung fehlgeschlagen: %s' % e)

    def _map_cb(self, msg):
        """OccupancyGrid -> RGBA PNG -> Base64."""
        try:
            width = msg.info.width
            height = msg.info.height
            if width == 0 or height == 0:
                return
            grid = np.array(msg.data, dtype=np.int8).reshape((height, width))

            # RGBA-Bild erzeugen
            rgba = np.zeros((height, width, 4), dtype=np.uint8)
            # Unbekannt (-1): dunkelblau, halbtransparent
            unknown = grid == -1
            rgba[unknown] = [15, 21, 33, 100]
            # Frei (0): sehr dunkel, leicht transparent
            free = grid == 0
            rgba[free] = [10, 14, 23, 180]
            # Belegt (>50): Cyan (Theme-Farbe), voll opak
            occupied = grid > 50
            rgba[occupied] = [0, 229, 255, 255]
            # Partial (1-50): abgestuft
            partial = (grid > 0) & (grid <= 50)
            if np.any(partial):
                vals = grid[partial].astype(np.float32) / 50.0
                rgba[partial, 0] = (10 + vals * (0 - 10)).astype(np.uint8)
                rgba[partial, 1] = (14 + vals * (229 - 14)).astype(np.uint8)
                rgba[partial, 2] = (23 + vals * (255 - 23)).astype(np.uint8)
                rgba[partial, 3] = (180 + vals * (255 - 180)).astype(np.uint8)

            # ROS Y-oben -> Bild Y-unten
            rgba = np.flipud(rgba)

            # BGRA fuer cv2 (OpenCV erwartet BGRA, nicht RGBA)
            bgra = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
            ok, buf = cv2.imencode(
                '.png', bgra,
                [cv2.IMWRITE_PNG_COMPRESSION, MAP_PNG_QUALITY]
            )
            if not ok:
                return
            png_b64 = base64.b64encode(buf.tobytes()).decode('ascii')
            metadata = {
                'width': width,
                'height': height,
                'resolution': msg.info.resolution,
                'origin_x': msg.info.origin.position.x,
                'origin_y': msg.info.origin.position.y,
            }
            with self.lock:
                self.latest_map_png = png_b64
                self.map_metadata = metadata
        except Exception as e:
            self.get_logger().warn('Map-Konvertierung fehlgeschlagen: %s' % e)

    def _tf_cb(self, msg):
        """Speichert map->odom Transform."""
        for tf in msg.transforms:
            if tf.header.frame_id == 'map' and tf.child_frame_id == 'odom':
                t = tf.transform.translation
                q = tf.transform.rotation
                yaw = math.atan2(
                    2.0 * (q.w * q.z + q.x * q.y),
                    1.0 - 2.0 * (q.y * q.y + q.z * q.z)
                )
                with self.lock:
                    self.map_to_odom_tf = {
                        'x': t.x,
                        'y': t.y,
                        'yaw': yaw,
                    }

    def _get_host_ip(self):
        """Ermittelt die Host-IP-Adresse ueber UDP-Socket-Trick."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            pass
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

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

    def record_heartbeat(self):
        """Aktualisiert den Heartbeat-Zeitstempel."""
        with self.lock:
            self.last_heartbeat_time = time.time()

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

    def build_telemetry(self):
        """Erstellt das Telemetrie-JSON-Dictionary."""
        with self.lock:
            odom = self.latest_odom
            imu = self.latest_imu
            odom_hz = self._compute_hz(self.odom_times)
            scan_hz = self._compute_hz(self.scan_times)

        # Odom-Daten
        odom_data = {
            'x': 0.0, 'y': 0.0, 'yaw_deg': 0.0,
            'vel_linear': 0.0, 'vel_angular': 0.0,
        }
        if odom is not None:
            yaw = quaternion_to_yaw(odom.pose.pose.orientation)
            odom_data = {
                'x': round(odom.pose.pose.position.x, 4),
                'y': round(odom.pose.pose.position.y, 4),
                'yaw_deg': round(math.degrees(yaw), 2),
                'vel_linear': round(odom.twist.twist.linear.x, 4),
                'vel_angular': round(odom.twist.twist.angular.z, 4),
            }

        # IMU-Daten
        imu_data = {'heading_deg': 0.0, 'gz_deg_s': 0.0}
        if imu is not None:
            imu_yaw = quaternion_to_yaw(imu.orientation)
            imu_data = {
                'heading_deg': round(math.degrees(imu_yaw), 2),
                'gz_deg_s': round(math.degrees(imu.angular_velocity.z), 2),
            }

        # Verbindungsstatus
        esp32_active = odom_hz > 1.0

        return {
            'op': 'telemetry',
            'ts': round(time.time(), 3),
            'odom': odom_data,
            'imu': imu_data,
            'connection': {
                'esp32_active': esp32_active,
                'odom_hz': round(odom_hz, 1),
                'scan_hz': round(scan_hz, 1),
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
            'op': 'scan',
            'angle_min': round(scan.angle_min, 4),
            'angle_max': round(scan.angle_max, 4),
            'angle_increment': round(scan.angle_increment, 6),
            'ranges': ranges,
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
                tf_yaw = tf_data['yaw']
                cos_y = math.cos(tf_yaw)
                sin_y = math.sin(tf_yaw)
                robot_x = tf_data['x'] + cos_y * ox - sin_y * oy
                robot_y = tf_data['y'] + sin_y * ox + cos_y * oy
                robot_yaw = tf_yaw + o_yaw
            else:
                # Ohne TF: Odom direkt als Naeherung
                robot_x = ox
                robot_y = oy
                robot_yaw = o_yaw

        return {
            'op': 'map',
            'ts': round(time.time(), 3),
            'png_b64': png_b64,
            'width': metadata['width'],
            'height': metadata['height'],
            'resolution': metadata['resolution'],
            'origin_x': metadata['origin_x'],
            'origin_y': metadata['origin_y'],
            'robot': {
                'x': round(robot_x, 4),
                'y': round(robot_y, 4),
                'yaw': round(robot_yaw, 4),
            },
        }

    def build_system_msg(self):
        """Erstellt das System-Metriken-JSON-Dictionary."""
        # CPU-Temperatur
        cpu_temp = 0.0
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                cpu_temp = int(f.read().strip()) / 1000.0
        except (IOError, ValueError):
            pass

        # CPU-Load
        load_1m, load_5m = 0.0, 0.0
        try:
            with open('/proc/loadavg', 'r') as f:
                parts = f.read().strip().split()
                load_1m = float(parts[0])
                load_5m = float(parts[1])
        except (IOError, ValueError, IndexError):
            pass

        # CPU-Frequenzen
        freq_mhz = []
        for path in sorted(globmod.glob(
            '/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq'
        )):
            try:
                with open(path, 'r') as f:
                    freq_mhz.append(int(f.read().strip()) // 1000)
            except (IOError, ValueError):
                pass

        # RAM
        ram_total, ram_avail = 0, 0
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        ram_total = int(line.split()[1])
                    elif line.startswith('MemAvailable:'):
                        ram_avail = int(line.split()[1])
        except (IOError, ValueError):
            pass
        ram_total_mb = ram_total / 1024.0
        ram_used_mb = (ram_total - ram_avail) / 1024.0
        ram_pct = (ram_used_mb / ram_total_mb * 100.0) if ram_total_mb > 0 else 0.0

        # Disk
        disk_total_gb, disk_used_gb, disk_pct = 0.0, 0.0, 0.0
        try:
            st = os.statvfs('/')
            disk_total_gb = (st.f_blocks * st.f_frsize) / (1024 ** 3)
            disk_free_gb = (st.f_bfree * st.f_frsize) / (1024 ** 3)
            disk_used_gb = disk_total_gb - disk_free_gb
            disk_pct = (disk_used_gb / disk_total_gb * 100.0) if disk_total_gb > 0 else 0.0
        except OSError:
            pass

        # Geraete-Status
        with self.lock:
            odom_hz = self._compute_hz(self.odom_times)
            scan_hz = self._compute_hz(self.scan_times)
            has_jpeg = self.latest_jpeg is not None

        return {
            'op': 'system',
            'ts': round(time.time(), 3),
            'cpu': {
                'temp_c': round(cpu_temp, 1),
                'load_1m': round(load_1m, 2),
                'load_5m': round(load_5m, 2),
                'freq_mhz': freq_mhz,
            },
            'ram': {
                'total_mb': round(ram_total_mb, 0),
                'used_mb': round(ram_used_mb, 0),
                'usage_pct': round(ram_pct, 1),
            },
            'disk': {
                'total_gb': round(disk_total_gb, 1),
                'used_gb': round(disk_used_gb, 1),
                'usage_pct': round(disk_pct, 1),
            },
            'devices': {
                'esp32': odom_hz > 1.0,
                'lidar': scan_hz > 1.0,
                'camera': has_jpeg,
                'hailo': os.path.exists('/dev/hailo0'),
            },
            'ip': self._get_host_ip(),
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
        node.get_logger().info('Beende DashboardBridge...')
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
