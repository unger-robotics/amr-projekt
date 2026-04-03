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
import contextlib
import glob as globmod
import json
import math
import os
import re
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
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

# TLS-Zertifikate (mkcert, im Container unter /dashboard/ gemountet)
TLS_CERT_DIR = "/dashboard"


def _create_ssl_context():
    """Erzeugt SSL-Kontext aus mkcert-Zertifikaten, falls vorhanden."""
    cert_file = None
    key_file = None
    for f in sorted(globmod.glob(os.path.join(TLS_CERT_DIR, "*.pem"))):
        if f.endswith("-key.pem"):
            key_file = f
        elif f.endswith(".pem"):
            cert_file = f
    if cert_file and key_file and os.path.isfile(cert_file) and os.path.isfile(key_file):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
        return ctx
    return None


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


def _quaternion_to_yaw_deg(q):
    """Quaternion -> Yaw-Winkel in Grad."""
    return math.degrees(quaternion_to_yaw(q))


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


def start_mjpeg_server(node, ssl_ctx=None):
    """Startet den MJPEG-HTTP(S)-Server in einem Daemon-Thread."""
    MjpegHandler.bridge_node = node
    server = ThreadingHTTPServer(("0.0.0.0", MJPEG_PORT), MjpegHandler)
    if ssl_ctx:
        server.socket = ssl_ctx.wrap_socket(server.socket, server_side=True)
    server.daemon_threads = True
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    proto = "https" if ssl_ctx else "http"
    node.get_logger().info(f"MJPEG-Server gestartet auf {proto}://0.0.0.0:{MJPEG_PORT}/stream")


# ---------------------------------------------------------------------------
# Verfuegbare Tests (Mapping Kurzname -> ROS2 Entry-Point)
# ---------------------------------------------------------------------------
AVAILABLE_TESTS = {
    "rplidar": "rplidar_test",
    "imu": "imu_test",
    "motor": "motor_test",
    "encoder": "encoder_test",
    "sensor": "sensor_test",
    "kinematic": "kinematic_test",
    "straight_drive": "straight_drive_test",
    "rotation": "rotation_test",
    "cliff_latency": "cliff_latency_test",
    "docking": "docking_test",
    "nav_square": "nav_square_test",
    "nav": "nav_test",
    "slam": "slam_validation",
    "dashboard_latency": "dashboard_latency_test",
    "can": "can_validation_test",
}

TEST_DESCRIPTIONS = {
    "rplidar": "RPLidar-Scan Frequenz und Reichweite",
    "imu": "MPU6050 Heading-Drift und Datenrate",
    "motor": "Motoransteuerung PWM und Drehrichtung",
    "encoder": "Encoder-Ticks und Distanzmessung",
    "sensor": "Alle Sensoren Gesamttest",
    "kinematic": "Differentialkinematik Vorwaerts/Kurve",
    "straight_drive": "Geradeausfahrt Abweichung",
    "rotation": "Drehung 90/180/360 Grad Genauigkeit",
    "cliff_latency": "Cliff-Sensor Reaktionszeit",
    "docking": "ArUco-Marker Docking-Anfahrt",
    "nav_square": "Nav2 Quadratfahrt Wiederholgenauigkeit",
    "nav": "Nav2 Punkt-zu-Punkt Navigation",
    "slam": "SLAM Toolbox Kartierung Konsistenz",
    "dashboard_latency": "WebSocket Round-Trip Latenz",
    "can": "CAN-Bus Nachrichtentransport",
}


# =========================================================================
# WebSocket Server (asyncio)
# =========================================================================
class WebSocketServer:
    """Asyncio-basierter WebSocket-Server fuer Telemetrie und Steuerung."""

    def __init__(self, node, ssl_ctx=None):
        self.node = node
        self.clients = set()
        self.controller_ws = None  # Nur ein Client darf cmd_vel senden
        self.loop = None
        self.ssl_ctx = ssl_ctx
        self._motion_active = False
        self._motion_cancel = False
        self._test_proc = None  # asyncio.subprocess.Process des laufenden Tests
        self._test_key = None  # Key des laufenden Tests

    async def handler(self, ws):
        """Verbindungs-Handler fuer neue WebSocket-Clients."""
        self.clients.add(ws)
        self.node.get_logger().info(f"WebSocket-Client verbunden ({len(self.clients)} aktiv)")
        # Aktuellen Vision-Status an neuen Client senden
        try:
            status = json.dumps({"op": "vision_status", "enabled": self.node.vision_enabled})
            await ws.send(status)
        except Exception:
            pass
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
            # Totmannschalter: alle Clients weg → Motoren stoppen (kein voller E-STOP,
            # damit Reconnect ohne manuelle Freigabe funktioniert)
            if len(self.clients) == 0 and self.node.dashboard_was_connected:
                self.node.publish_stop()
                self.node.cancel_nav_goal()
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
            led_pct = max(0.0, min(100.0, float(msg.get("led_pwm", 0.0))))
            led_pwm = led_pct * 2.55  # 0-100% → 0-255
            self.node.publish_hardware_cmd(motor_limit, servo_speed, led_pwm, led_pct)
        elif op == "heartbeat":
            self.node.record_heartbeat()
        elif op == "estop":
            self.node.unified_estop("dashboard")
        elif op == "estop_release":
            self.node.unified_estop_release()
        elif op == "nav_goal":
            x = float(msg.get("x", 0.0))
            y = float(msg.get("y", 0.0))
            yaw = float(msg.get("yaw", 0.0))
            self.node.send_nav_goal(x, y, yaw)
        elif op == "nav_cancel":
            self.node.cancel_nav_goal()
        elif op == "tts_test":
            text = str(msg.get("text", ""))[:200]
            if text:
                tts_msg = String()
                tts_msg.data = text
                self.node.pub_tts_speak.publish(tts_msg)
        elif op == "audio_play":
            key = msg.get("sound_key", "")
            if key in ("cliff_alarm", "nav_start", "nav_reached", "startup"):
                self.node.publish_audio_play(key)
        elif op == "audio_volume":
            vol = max(0, min(100, int(msg.get("volume_percent", 80))))
            self.node.publish_audio_volume(vol)
        elif op == "vision_control":
            self.node.vision_enabled = bool(msg.get("enabled", False))
            self.node.get_logger().info(
                f"Vision {'aktiviert' if self.node.vision_enabled else 'deaktiviert'}"
            )
            # ROS2-Topic fuer TTS und andere Nodes
            enable_msg = Bool()
            enable_msg.data = self.node.vision_enabled
            self.node.pub_vision_enable.publish(enable_msg)
            # WebSocket-Status an alle Clients
            status = json.dumps({"op": "vision_status", "enabled": self.node.vision_enabled})
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.broadcast(status), self.loop)
        elif op == "voice_mute":
            self.node.mic_muted = bool(msg.get("muted", False))
            self.node.get_logger().info(f"Mikrofon {'stumm' if self.node.mic_muted else 'aktiv'}")
            mute_msg = Bool()
            mute_msg.data = self.node.mic_muted
            self.node.pub_voice_mute.publish(mute_msg)
            status = json.dumps({"op": "voice_mute_status", "muted": self.node.mic_muted})
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.broadcast(status), self.loop)
        elif op == "test_list":
            tests = [
                {
                    "key": k,
                    "entry_point": v,
                    "description": TEST_DESCRIPTIONS.get(k, ""),
                }
                for k, v in sorted(AVAILABLE_TESTS.items())
            ]
            resp = json.dumps({"op": "test_list", "tests": tests})
            if self.loop:
                asyncio.run_coroutine_threadsafe(ws.send(resp), self.loop)
        elif op == "test_run":
            test_key = str(msg.get("test_key", "")).strip().lower()
            if test_key in AVAILABLE_TESTS:
                asyncio.run_coroutine_threadsafe(self._execute_test(ws, test_key), self.loop)
            else:
                resp = json.dumps(
                    {
                        "op": "command_response",
                        "text": f"Unbekannter Test: {test_key}",
                        "success": False,
                    }
                )
                if self.loop:
                    asyncio.run_coroutine_threadsafe(ws.send(resp), self.loop)
        elif op == "test_stop":
            asyncio.run_coroutine_threadsafe(self._stop_test(ws), self.loop)
        elif op == "command":
            text = str(msg.get("text", "")).strip()
            resp = self._handle_command(text, ws)
            if resp is not None:
                with contextlib.suppress(Exception):
                    asyncio.get_event_loop().create_task(ws.send(json.dumps(resp)))

    def _handle_command(self, text, ws=None):
        """Parst Freitext-Kommandos und fuehrt sie aus."""
        parts = text.split()
        if not parts:
            return {"op": "command_response", "text": "Leeres Kommando", "success": False}

        # -- Natuerlichsprachlicher Parser (vor cmd-Parser) --
        text_lower = text.lower()
        # Normalisierung fuer STT-Output (Whisper/Gemini):
        text_lower = (
            text_lower.replace(",", ".")
            .replace("\u00e4", "ae")
            .replace("\u00f6", "oe")
            .replace("\u00fc", "ue")
            .replace("\u00df", "ss")
            .rstrip(".!?")
        )

        # "navigiere zu X Y" oder "fahre zu X Y"
        m = re.match(
            r"(?:navigiere|fahre)\s+zu\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*(-?\d+\.?\d*)?",
            text_lower,
        )
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            yaw = float(m.group(3)) if m.group(3) else 0.0
            self.node.send_nav_goal(x, y, yaw)
            return {
                "op": "command_response",
                "text": f"Nav-Ziel: x={x}, y={y}, yaw={yaw}",
                "success": True,
            }

        # "fahre X m vorwaerts/geradeaus"
        m = re.match(
            r"fahre\s+(\d+\.?\d*)\s*(?:m|meter)?\s*(?:vorwaerts|geradeaus|vor)", text_lower
        )
        if m:
            dist = float(m.group(1))
            if dist <= 0 or dist > 5.0:
                return {
                    "op": "command_response",
                    "text": "Distanz muss 0-5 m sein",
                    "success": False,
                }
            if self._motion_active:
                return {
                    "op": "command_response",
                    "text": "Bewegung bereits aktiv",
                    "success": False,
                }
            asyncio.run_coroutine_threadsafe(self._execute_forward(ws, dist), self.loop)
            return None

        # "dreh dich zu mir" / "schau zu mir" / "schau mich an"
        if re.match(r"dreh.*zu\s+mir|schau.*(?:zu\s+mir|mich\s+an)|komm.*zu\s+mir", text_lower):
            return self._handle_turn_to_speaker(ws)

        # "dreh(e) X grad links/rechts"
        m = re.match(
            r"dreh(?:e)?\s*(?:dich\s+)?(\d+\.?\d*)\s*(?:grad|°)?\s*(links|rechts)?", text_lower
        )
        if m:
            angle = float(m.group(1))
            if m.group(2) == "rechts":
                angle = -angle
            if abs(angle) > 360:
                return {
                    "op": "command_response",
                    "text": "Winkel muss -360..360 sein",
                    "success": False,
                }
            if self._motion_active:
                return {
                    "op": "command_response",
                    "text": "Bewegung bereits aktiv",
                    "success": False,
                }
            asyncio.run_coroutine_threadsafe(self._execute_turn(ws, angle), self.loop)
            return None

        # -- Stopp-Phrasen (Sprache/Text) → einheitlicher Notstopp --
        if text_lower in (
            "halt an",
            "anhalten",
            "bleib stehen",
            "stopp",
            "stopp sofort",
            "not aus",
            "notaus",
        ):
            self.node.unified_estop("voice")
            return {
                "op": "command_response",
                "text": "Notstopp ausgeloest",
                "success": True,
            }

        # "fahr(e) zurueck/rueckwaerts X m"
        m = re.match(
            r"(?:fahr(?:e)?|geh)\s+(?:zurueck|rueckwaerts)\s+(\d+\.?\d*)\s*(?:m|meter)?",
            text_lower,
        )
        if m:
            dist = float(m.group(1))
            if dist <= 0 or dist > 5.0:
                return {
                    "op": "command_response",
                    "text": "Distanz muss 0-5 m sein",
                    "success": False,
                }
            if self._motion_active:
                return {
                    "op": "command_response",
                    "text": "Bewegung bereits aktiv",
                    "success": False,
                }
            asyncio.run_coroutine_threadsafe(
                self._execute_forward(ws, dist, reverse=True), self.loop
            )
            return None

        # "schau nach links/rechts/mitte"
        m = re.match(
            r"(?:schau|kamera|guck)\s+(?:nach\s+)?(links|rechts|mitte|zentrum|geradeaus)",
            text_lower,
        )
        if m:
            direction = m.group(1)
            pan_map = {
                "links": 135,
                "rechts": 45,
                "mitte": 90,
                "zentrum": 90,
                "geradeaus": 90,
            }
            self.node.publish_servo_cmd(float(pan_map[direction]), 90.0)
            return {
                "op": "command_response",
                "text": f"Kamera: {direction} (Pan={pan_map[direction]})",
                "success": True,
            }

        # "licht an/aus" mit optionalem Prozentwert: "led an 50", "licht an (80%)", "led aus"
        m = re.match(r"(?:licht|led)\s+(an|aus|ein)(?:\s*\(?(\d{1,3})%?\)?)?", text_lower)
        if m:
            if m.group(1) == "aus":
                led_pct = 0.0
            elif m.group(2):
                led_pct = max(0.0, min(100.0, float(m.group(2))))
            else:
                led_pct = 80.0
            led_pwm = led_pct * 2.55  # 0-100% → 0-255
            self.node.publish_hardware_cmd(
                self.node.hw_motor_limit, self.node.hw_servo_speed, led_pwm, led_pct
            )
            return {
                "op": "command_response",
                "text": f"LED {'an (' + str(int(led_pct)) + '%)' if led_pct > 0 else 'aus'}",
                "success": True,
            }

        # -- Status-Abfragen (keine Aktorik) --
        if any(
            w in text_lower for w in ("wie weit", "abstand", "hindernis", "ultraschall", "range")
        ):
            with self.node.lock:
                dist = self.node.ultrasonic_range
            return {
                "op": "command_response",
                "text": f"Ultraschall: {dist:.2f} m",
                "success": True,
            }

        if any(w in text_lower for w in ("akku", "batterie", "spannung", "battery")):
            with self.node.lock:
                bat = self.node.battery_data
            if bat:
                return {
                    "op": "command_response",
                    "text": (
                        f"Batterie: {bat.get('voltage', 0):.1f} V, {bat.get('percentage', 0):.0f} %"
                    ),
                    "success": True,
                }
            return {
                "op": "command_response",
                "text": "Keine Batteriedaten verfuegbar",
                "success": False,
            }

        # "wo bin ich" / "position" / "standort"
        if any(
            w in text_lower
            for w in ("wo bin ich", "position", "standort", "koordinaten", "location")
        ):
            return self._handle_location()

        # "wetter" / "wie ist das wetter" / "temperatur draussen"
        if any(w in text_lower for w in ("wetter", "weather", "temperatur draussen")):
            return self._handle_weather()

        # -- Keyword-basierter Parser --
        cmd = parts[0].lower()
        try:
            if cmd == "nav" and len(parts) >= 3:
                x = float(parts[1])
                y = float(parts[2])
                yaw = float(parts[3]) if len(parts) >= 4 else 0.0
                self.node.send_nav_goal(x, y, yaw)
                return {
                    "op": "command_response",
                    "text": f"Nav-Ziel: x={x}, y={y}, yaw={yaw}",
                    "success": True,
                }
            elif cmd in ("stop", "stopp", "halt", "anhalten"):
                self.node.unified_estop("voice")
                return {
                    "op": "command_response",
                    "text": "Notstopp ausgeloest",
                    "success": True,
                }
            elif cmd == "cancel":
                self.node.cancel_nav_goal()
                return {"op": "command_response", "text": "Navigation abgebrochen", "success": True}
            elif cmd in ("forward", "vor", "vorwaerts", "geradeaus") and len(parts) >= 2:
                dist = float(parts[1])
                if dist <= 0 or dist > 5.0:
                    return {
                        "op": "command_response",
                        "text": "Distanz muss 0-5 m sein",
                        "success": False,
                    }
                if self._motion_active:
                    return {
                        "op": "command_response",
                        "text": "Bewegung bereits aktiv",
                        "success": False,
                    }
                asyncio.run_coroutine_threadsafe(self._execute_forward(ws, dist), self.loop)
                return None
            elif cmd in ("backward", "zurueck", "rueckwaerts") and len(parts) >= 2:
                dist = float(parts[1])
                if dist <= 0 or dist > 5.0:
                    return {
                        "op": "command_response",
                        "text": "Distanz muss 0-5 m sein",
                        "success": False,
                    }
                if self._motion_active:
                    return {
                        "op": "command_response",
                        "text": "Bewegung bereits aktiv",
                        "success": False,
                    }
                asyncio.run_coroutine_threadsafe(
                    self._execute_forward(ws, dist, reverse=True), self.loop
                )
                return None
            elif cmd in ("turn", "dreh", "drehe", "drehung") and len(parts) >= 2:
                angle = float(parts[1])
                if abs(angle) > 360:
                    return {
                        "op": "command_response",
                        "text": "Winkel muss -360..360 sein",
                        "success": False,
                    }
                if self._motion_active:
                    return {
                        "op": "command_response",
                        "text": "Bewegung bereits aktiv",
                        "success": False,
                    }
                asyncio.run_coroutine_threadsafe(self._execute_turn(ws, angle), self.loop)
                return None
            elif cmd == "turn_to_speaker":
                return self._handle_turn_to_speaker(ws)
            elif cmd == "help":
                return {
                    "op": "command_response",
                    "text": (
                        "Befehle: nav X Y [YAW], stop, "
                        "forward DIST, backward DIST, turn GRAD, "
                        "turn_to_speaker, test list, test <name>, help"
                    ),
                    "success": True,
                }
            elif cmd == "test" and len(parts) >= 2:
                sub = parts[1].lower()
                if sub == "list":
                    names = ", ".join(sorted(AVAILABLE_TESTS.keys()))
                    return {
                        "op": "command_response",
                        "text": f"Tests: {names}",
                        "success": True,
                    }
                elif sub in AVAILABLE_TESTS:
                    asyncio.run_coroutine_threadsafe(self._execute_test(ws, sub), self.loop)
                    return None
                else:
                    return {
                        "op": "command_response",
                        "text": f"Unbekannter Test: {sub}. 'test list' fuer Uebersicht.",
                        "success": False,
                    }
            elif cmd == "test":
                return {
                    "op": "command_response",
                    "text": "Verwendung: test list | test <name>",
                    "success": False,
                }
            else:
                return {
                    "op": "command_response",
                    "text": f"Unbekannt: {text}. Tippe 'help' fuer Befehle.",
                    "success": False,
                }
        except (ValueError, IndexError) as e:
            return {"op": "command_response", "text": f"Fehler: {e}", "success": False}

    async def _send_response(self, ws, text, success, pending=False):
        """Sendet command_response an einen spezifischen Client."""
        resp = {"op": "command_response", "text": text, "success": success}
        if pending:
            resp["pending"] = True
        with contextlib.suppress(Exception):
            await ws.send(json.dumps(resp))

    async def _execute_forward(self, ws, distance_m, reverse=False):
        """Faehrt distance_m Meter geradeaus/rueckwaerts mittels cmd_vel + Odometrie-Feedback."""
        self._motion_active = True
        self._motion_cancel = False
        direction_str = "rueckwaerts" if reverse else "vorwaerts"
        abs_dist = abs(distance_m)
        await self._send_response(ws, f"Fahre {abs_dist} m {direction_str}...", True, pending=True)

        odom = self.node.latest_odom
        if odom is None:
            self._motion_active = False
            await self._send_response(ws, "Keine Odometrie verfuegbar", False)
            return

        start_x = odom.pose.pose.position.x
        start_y = odom.pose.pose.position.y
        timeout = abs_dist / 0.10 + 5.0
        start_time = asyncio.get_event_loop().time()
        vel = -0.15 if reverse else 0.15  # m/s
        traveled = 0.0

        try:
            while not self._motion_cancel:
                self.node.publish_cmd_vel(vel, 0.0)
                await asyncio.sleep(0.05)  # 20 Hz

                odom = self.node.latest_odom
                if odom is None:
                    continue
                dx = odom.pose.pose.position.x - start_x
                dy = odom.pose.pose.position.y - start_y
                traveled = math.sqrt(dx * dx + dy * dy)

                if traveled >= abs_dist:
                    break
                if (asyncio.get_event_loop().time() - start_time) > timeout:
                    self.node.publish_stop()
                    self._motion_active = False
                    await self._send_response(ws, f"Timeout nach {traveled:.2f} m", False)
                    return
        finally:
            self.node.publish_stop()
            self._motion_active = False

        if self._motion_cancel:
            await self._send_response(ws, "Bewegung abgebrochen", False)
        else:
            await self._send_response(
                ws,
                f"{direction_str.capitalize()} {abs_dist} m abgeschlossen ({traveled:.2f} m)",
                True,
            )

    def _handle_location(self):
        """Ermittelt Standort via AMR_LOCATION oder IP-Geolocation, kombiniert mit Odometrie."""
        # Bevorzugt: konfigurierter Standort (z.B. AMR_LOCATION="Wuppertal Vohwinkel")
        configured = os.environ.get("AMR_LOCATION", "").strip()
        geo_text = ""
        if configured:
            geo_text = f"Standort: {configured}"
        else:
            # Fallback: IP-Geolocation via ipinfo.io (kostenlos, kein API-Key)
            try:
                with urllib.request.urlopen("https://ipinfo.io/json", timeout=5) as resp:
                    geo = json.loads(resp.read().decode())
                city = geo.get("city", "")
                region = geo.get("region", "")
                country = geo.get("country", "")
                parts = [p for p in (city, region, country) if p]
                if parts:
                    geo_text = f"Standort: {', '.join(parts)}"
            except Exception:  # noqa: BLE001
                geo_text = "Geo-Standort nicht ermittelbar"

        # Odometrie-Position
        odom_text = ""
        with self.node.lock:
            odom = self.node.latest_odom
        if odom:
            x = odom.pose.pose.position.x
            y = odom.pose.pose.position.y
            yaw = _quaternion_to_yaw_deg(odom.pose.pose.orientation)
            odom_text = f"Odometrie: x={x:.2f} m, y={y:.2f} m, Ausrichtung={yaw:.0f}\u00b0"

        if geo_text and odom_text:
            text = f"{geo_text}. {odom_text}"
        elif geo_text:
            text = geo_text
        elif odom_text:
            text = odom_text
        else:
            text = "Weder Geo-Standort noch Odometrie verfuegbar"

        return {
            "op": "command_response",
            "text": text,
            "success": bool(geo_text or odom_text),
        }

    def _handle_weather(self):
        """Ruft aktuelle Wetterdaten via OpenWeatherMap ab."""
        api_key = os.environ.get("OPENWEATHER_API_KEY", "")
        if not api_key:
            return {
                "op": "command_response",
                "text": "Kein OPENWEATHER_API_KEY konfiguriert",
                "success": False,
            }
        # Standort aus AMR_LOCATION (Stadtname), Fallback Nuernberg-Koordinaten
        location = os.environ.get("AMR_LOCATION", "").strip()
        if location:
            # Erster Teil vor Komma als Stadtname (z.B. "Wuppertal" aus "Wuppertal Vohwinkel")
            city_query = location.split(",")[0].split()[0]
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={urllib.parse.quote(city_query)},DE&units=metric&lang=de&appid={api_key}"
            )
        else:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat=49.45&lon=11.08&units=metric&lang=de&appid={api_key}"
            )
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            city = data.get("name", "Unbekannt")
            return {
                "op": "command_response",
                "text": f"Wetter {city}: {desc}, {temp:.1f}°C, Luftfeuchte {humidity}%, Wind {wind:.1f} m/s",
                "success": True,
            }
        except (urllib.error.URLError, KeyError, Exception) as e:  # noqa: BLE001
            return {
                "op": "command_response",
                "text": f"Wetterabfrage fehlgeschlagen: {e}",
                "success": False,
            }

    def _handle_turn_to_speaker(self, ws):
        """Dreht den Roboter in Richtung der letzten erkannten Stimme."""
        with self.node.lock:
            doa = self.node.doa_filtered
            quadrant = self.node.doa_quadrant
            last_time = self.node._last_doa_time

        # DoA muss aktuell sein (max 30 s)
        if time.time() - last_time > 30.0 or not quadrant:
            return {
                "op": "command_response",
                "text": "Keine aktuelle Sprachrichtung verfuegbar",
                "success": False,
            }

        # Kuerzester Drehweg: 0-180 → links, 181-359 → rechts
        turn_angle = doa if doa <= 180 else doa - 360

        # Totzone: Sprecher bereits vorne
        if abs(turn_angle) < 10:
            return {
                "op": "command_response",
                "text": f"Sprecher bereits vorne (DoA {doa}°)",
                "success": True,
            }

        if self._motion_active:
            return {
                "op": "command_response",
                "text": "Bewegung bereits aktiv",
                "success": False,
            }

        direction = "links" if turn_angle > 0 else "rechts"
        label = f"Drehe zum Sprecher ({quadrant}, DoA {doa}°, {abs(turn_angle)}° {direction})..."
        asyncio.run_coroutine_threadsafe(self._execute_turn(ws, turn_angle, label=label), self.loop)
        return None

    async def _execute_turn(self, ws, angle_deg, label=None):
        """Dreht um angle_deg Grad (positiv=links, negativ=rechts)."""
        self._motion_active = True
        self._motion_cancel = False
        direction = "links" if angle_deg > 0 else "rechts"
        start_msg = label or f"Drehe {abs(angle_deg)} Grad {direction}..."
        await self._send_response(ws, start_msg, True, pending=True)

        odom = self.node.latest_odom
        if odom is None:
            self._motion_active = False
            await self._send_response(ws, "Keine Odometrie verfuegbar", False)
            return

        start_yaw = quaternion_to_yaw(odom.pose.pose.orientation)
        target_rad = math.radians(angle_deg)
        omega = 0.3 if angle_deg > 0 else -0.3  # rad/s
        timeout = abs(angle_deg) / 15.0 + 5.0  # mind. 15 deg/s
        start_time = asyncio.get_event_loop().time()
        accumulated = 0.0
        prev_yaw = start_yaw

        try:
            while not self._motion_cancel:
                self.node.publish_cmd_vel(0.0, omega)
                await asyncio.sleep(0.05)  # 20 Hz

                odom = self.node.latest_odom
                if odom is None:
                    continue
                current_yaw = quaternion_to_yaw(odom.pose.pose.orientation)

                # Winkel-Differenz mit Wrapping
                diff = current_yaw - prev_yaw
                if diff > math.pi:
                    diff -= 2 * math.pi
                elif diff < -math.pi:
                    diff += 2 * math.pi
                accumulated += diff
                prev_yaw = current_yaw

                if abs(accumulated) >= abs(target_rad):
                    break
                if (asyncio.get_event_loop().time() - start_time) > timeout:
                    self.node.publish_stop()
                    self._motion_active = False
                    await self._send_response(
                        ws, f"Timeout nach {math.degrees(accumulated):.1f} Grad", False
                    )
                    return
        finally:
            self.node.publish_stop()
            self._motion_active = False

        if self._motion_cancel:
            await self._send_response(ws, "Drehung abgebrochen", False)
        else:
            await self._send_response(
                ws,
                f"Drehung {abs(angle_deg)} Grad {direction} abgeschlossen"
                f" ({math.degrees(accumulated):.1f} Grad)",
                True,
            )

    async def _execute_test(self, ws, test_key):
        """Startet einen Test als Subprocess und sendet das Ergebnis."""
        entry_point = AVAILABLE_TESTS[test_key]
        await self._send_response(ws, f"Starte Test: {entry_point}...", True, pending=True)
        try:
            proc = await asyncio.create_subprocess_exec(
                "ros2",
                "run",
                "my_bot",
                entry_point,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            self._test_proc = proc
            self._test_key = test_key
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                self._test_proc = None
                self._test_key = None
                await self._send_response(ws, f"Test {entry_point}: Timeout (300s)", False)
                return

            self._test_proc = None
            self._test_key = None
            output = stdout.decode(errors="replace") if stdout else ""
            # Letzte nicht-leere Zeilen fuer Ergebnis
            lines = [l.strip() for l in output.splitlines() if l.strip()]
            tail = "\n".join(lines[-5:]) if lines else "(keine Ausgabe)"

            success = proc.returncode == 0
            status = "PASS" if success else f"FAIL (rc={proc.returncode})"
            await self._send_response(ws, f"Test {entry_point}: {status}\n{tail}", success)
        except Exception as e:
            self._test_proc = None
            self._test_key = None
            await self._send_response(ws, f"Test {entry_point}: Fehler: {e}", False)

    async def _stop_test(self, ws):
        """Stoppt den laufenden Test-Subprocess."""
        proc = self._test_proc
        test_key = self._test_key
        if proc is None or proc.returncode is not None:
            await self._send_response(ws, "Kein Test aktiv", False)
            return
        entry_point = AVAILABLE_TESTS.get(test_key, test_key)
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        except ProcessLookupError:
            pass
        self._test_proc = None
        self._test_key = None
        await self._send_response(ws, f"Test {entry_point}: Abgebrochen", False)

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
            ssl=self.ssl_ctx,
        ):
            proto = "wss" if self.ssl_ctx else "ws"
            self.node.get_logger().info(
                f"WebSocket-Server gestartet auf {proto}://0.0.0.0:{WS_PORT}"
            )
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
        """Sendet Vision-Detektionen mit 5 Hz (nur wenn vision_enabled)."""
        interval = 1.0 / DETECTION_BROADCAST_HZ
        while True:
            if self.node.vision_enabled:
                data = self.node.build_detections_msg()
                if data is not None:
                    await self.broadcast(json.dumps(data))
            await asyncio.sleep(interval)

    async def _semantics_loop(self):
        """Sendet semantische Analyse mit 0.5 Hz (nur wenn vision_enabled)."""
        interval = 1.0 / SEMANTICS_BROADCAST_HZ
        while True:
            if self.node.vision_enabled:
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
        self._clock_offset_ms = 0.0
        self._offset_samples = deque(maxlen=200)
        self._offset_calibrated = False
        self.last_cmd_time = 0.0
        self.last_heartbeat_time = 0.0
        self.battery_data = None  # dict: voltage, current, power, percentage, runtime_min
        self.battery_ema_current_a = 0.0
        self.battery_ema_initialized = False
        self.servo_pan = 90.0  # Letzte Servo-Pan-Position (Grad)
        self.servo_tilt = 90.0  # Letzte Servo-Tilt-Position (Grad)
        self.hw_motor_limit = 100.0  # Motor-Limit 0-100%
        self.hw_servo_speed = 5.0  # Servo-Speed 1-10
        self.hw_led_pwm = 0.0  # LED 0-100% (0 = Auto-Heartbeat)
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
        self.doa_filtered = 0
        self.doa_quadrant = ""
        self._last_doa_time = 0.0
        self._last_voice_command = ""  # Letzter erkannter Sprachbefehl
        self._last_voice_transcript = ""  # Letztes Transkript (Merge-Buffer)
        self._voice_merge_timer = None  # Timer fuer Command/Transcript-Merge

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
        self.sub_doa_filtered = self.create_subscription(
            Int32, "/doa/filtered", self._doa_filtered_cb, 10
        )
        self.sub_doa_quadrant = self.create_subscription(
            String, "/doa/quadrant", self._doa_quadrant_cb, 10
        )

        # --- Voice Command (Sprachsteuerung, optional) ---
        self.create_subscription(String, "/voice/command", self._voice_command_cb, 10)
        self.create_subscription(String, "/voice/text", self._voice_text_cb, 10)

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
        self.pub_vision_enable = self.create_publisher(Bool, "/vision/enable", 10)
        self.pub_voice_mute = self.create_publisher(Bool, "/voice/mute", 10)
        self.pub_tts_speak = self.create_publisher(String, "/tts/speak", 10)
        self.pub_emergency_stop = self.create_publisher(Bool, "/emergency_stop", 10)
        self.audio_volume_pct = 80  # Default-Lautstaerke
        self.vision_enabled = False  # Vision-Broadcast Default: aus
        self.mic_muted = False  # Mikrofon-Mute Default: aus

        # --- E-Stop State (Totmannschalter) ---
        self.estop_engaged = False
        self.estop_source = ""
        self.dashboard_was_connected = False

        # --- /emergency_stop Subscriber (Hardware-E-Stop, Phase 2) ---
        self.create_subscription(Bool, "/emergency_stop", self._emergency_stop_cb, 10)

        # --- Deadman-Timer (300 ms) ---
        self.deadman_timer = self.create_timer(DEADMAN_TIMEOUT_S, self._deadman_cb)

        # --- TLS-Kontext (optional, fuer HTTPS/WSS) ---
        ssl_ctx = _create_ssl_context()
        if ssl_ctx:
            self.get_logger().info("TLS-Zertifikate geladen -> HTTPS/WSS aktiv")
        else:
            self.get_logger().info("Keine TLS-Zertifikate gefunden -> HTTP/WS (unverschluesselt)")

        # --- WebSocket-Server ---
        if websockets is None:
            self.get_logger().error(
                'Python-Paket "websockets" nicht installiert! WebSocket-Server deaktiviert.'
            )
            self.ws_server = None
        else:
            self.ws_server = WebSocketServer(self, ssl_ctx=ssl_ctx)
            self.ws_server.start()

        # --- MJPEG-Server ---
        if HAS_CAMERA:
            start_mjpeg_server(self, ssl_ctx=ssl_ctx)
        else:
            self.get_logger().warn("cv2/cv_bridge nicht verfuegbar -> MJPEG-Server deaktiviert")

        self.get_logger().info("DashboardBridge gestartet")

    # --- ROS2 Callbacks ---

    def _update_clock_offset(self, stamp_s, now):
        """Aktualisiert Clock-Offset zwischen ESP32 und Pi (Lock muss gehalten werden)."""
        raw_diff_ms = (stamp_s - now) * 1000.0
        self._offset_samples.append(raw_diff_ms)
        if len(self._offset_samples) >= 20:
            sorted_diffs = sorted(self._offset_samples)
            idx = max(0, len(sorted_diffs) // 20)  # 5. Perzentil
            self._clock_offset_ms = sorted_diffs[idx]
            self._offset_calibrated = True

    def _corrected_latency(self, stamp_s, now):
        """Berechnet offset-korrigierte Latenz in ms."""
        latency_ms = (now - stamp_s) * 1000.0 + self._clock_offset_ms
        return latency_ms if 0.0 <= latency_ms < 500.0 else None

    def _odom_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_odom = msg
            self.odom_times.append(now)
            stamp_s = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp_s > 1e9:
                self._update_clock_offset(stamp_s, now)
                latency_ms = self._corrected_latency(stamp_s, now)
                if latency_ms is not None:
                    self.odom_latencies.append(latency_ms)

    def _imu_cb(self, msg):
        now = time.time()
        with self.lock:
            self.latest_imu = msg
            self.imu_times.append(now)
            stamp_s = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp_s > 1e9:
                self._update_clock_offset(stamp_s, now)
                latency_ms = self._corrected_latency(stamp_s, now)
                if latency_ms is not None:
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

    def _doa_filtered_cb(self, msg):
        """Speichert gefilterte Schallrichtung (Int32, Grad)."""
        with self.lock:
            self.doa_filtered = msg.data
            self._last_doa_time = time.time()

    def _doa_quadrant_cb(self, msg):
        """Speichert DoA-Quadrant (String: vorne/hinten/links/rechts)."""
        with self.lock:
            self.doa_quadrant = msg.data

    def _voice_command_cb(self, msg):
        """Verarbeitet Sprachbefehle via voice_command_node."""
        text = msg.data.strip()
        if not text or self.ws_server is None:
            return
        self.get_logger().info(f"Sprachbefehl empfangen: {text}")
        with self.lock:
            self._last_voice_command = text
        # Befehl ausfuehren
        resp = self.ws_server._handle_command(text)
        if resp is not None:
            resp["source"] = "voice"
            resp_str = json.dumps(resp)
            if self.ws_server.loop:
                asyncio.run_coroutine_threadsafe(
                    self.ws_server.broadcast(resp_str), self.ws_server.loop
                )
            # Antwort per TTS aussprechen
            resp_text = resp.get("text", "")
            if resp_text:
                tts_msg = String()
                tts_msg.data = resp_text
                self.pub_tts_speak.publish(tts_msg)
        # Falls Transkript bereits da ist, sofort mergen und senden
        self._try_send_voice_transcript()

    def _voice_text_cb(self, msg):
        """Speichert Transkript und versucht Merge mit Befehl."""
        text = msg.data.strip()
        if not text or self.ws_server is None:
            return
        with self.lock:
            self._last_voice_transcript = text
        # Falls Befehl bereits da ist, sofort mergen und senden
        self._try_send_voice_transcript()
        # Fallback-Timer: nach 200 ms senden, auch ohne Befehl
        if self._voice_merge_timer is not None:
            self._voice_merge_timer.cancel()
        self._voice_merge_timer = self.create_timer(0.2, self._voice_merge_timeout)

    def _voice_merge_timeout(self):
        """Fallback: Transkript ohne Befehl senden nach Timeout."""
        if self._voice_merge_timer is not None:
            self._voice_merge_timer.cancel()
            self._voice_merge_timer = None
        self._try_send_voice_transcript()

    def _try_send_voice_transcript(self):
        """Sendet voice_transcript wenn Transkript vorhanden ist."""
        with self.lock:
            transcript = self._last_voice_transcript
            if not transcript:
                return
            command = self._last_voice_command
            self._last_voice_transcript = ""
            self._last_voice_command = ""
        if self._voice_merge_timer is not None:
            self._voice_merge_timer.cancel()
            self._voice_merge_timer = None
        transcript_msg = json.dumps(
            {
                "op": "voice_transcript",
                "text": transcript,
                "command": command,
                "ts": round(time.time(), 3),
            }
        )
        if self.ws_server.loop:
            asyncio.run_coroutine_threadsafe(
                self.ws_server.broadcast(transcript_msg), self.ws_server.loop
            )

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
            was_connected = self.dashboard_was_connected
        # Pruefen ob Steuerbefehle oder Heartbeat empfangen wurden
        # Nur stoppen wenn Dashboard irgendwann verbunden war (Totmannschalter)
        last_activity = max(last_cmd, last_hb)
        if was_connected and last_activity > 0.0 and (now - last_activity) > DEADMAN_TIMEOUT_S:
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
        self.get_logger().info(f"Servo-Cmd: pan={pan:.0f}, tilt={tilt:.0f}")
        with self.lock:
            self.servo_pan = float(pan)
            self.servo_tilt = float(tilt)

    def publish_hardware_cmd(self, motor_limit, servo_speed, led_pwm, led_pct=None):
        """Publiziert Hardware-Parameter auf /hardware_cmd (Point: x=motor, y=servo_speed, z=led).

        led_pwm: 0-255 (Firmware-Wert), led_pct: 0-100 (%-Wert fuer Dashboard-Feedback).
        """
        msg = Point()
        msg.x = float(motor_limit)
        msg.y = float(servo_speed)
        msg.z = float(led_pwm)
        self.pub_hardware_cmd.publish(msg)
        with self.lock:
            self.hw_motor_limit = motor_limit
            self.hw_servo_speed = servo_speed
            self.hw_led_pwm = led_pct if led_pct is not None else led_pwm

    def record_heartbeat(self):
        """Aktualisiert den Heartbeat-Zeitstempel."""
        with self.lock:
            self.last_heartbeat_time = time.time()
            if not self.dashboard_was_connected:
                self.dashboard_was_connected = True
                self.get_logger().info("Dashboard-Heartbeat aktiv -> Totmannschalter scharf")

    # --- Einheitlicher Notstopp (Totmannschalter) ---

    def unified_estop(self, source="unknown"):
        """Einheitlicher Notstopp: Motoren + Navigation + Broadcast."""
        self.publish_stop()
        self.cancel_nav_goal()
        if self.ws_server:
            self.ws_server._motion_cancel = True
        # ROS2 /emergency_stop
        estop_msg = Bool()
        estop_msg.data = True
        self.pub_emergency_stop.publish(estop_msg)
        # Audio-Alarm
        self.publish_audio_play("cliff_alarm")
        # State
        self.estop_engaged = True
        self.estop_source = source
        # Dashboard-Broadcast
        status = json.dumps({"op": "estop_status", "engaged": True, "source": source})
        if self.ws_server and self.ws_server.loop:
            asyncio.run_coroutine_threadsafe(self.ws_server.broadcast(status), self.ws_server.loop)
        self.get_logger().warn(f"NOTSTOPP ausgeloest (Quelle: {source})")

    def unified_estop_release(self):
        """Notstopp aufheben."""
        self.estop_engaged = False
        self.estop_source = ""
        # ROS2 /emergency_stop release
        estop_msg = Bool()
        estop_msg.data = False
        self.pub_emergency_stop.publish(estop_msg)
        # Dashboard-Broadcast
        status = json.dumps({"op": "estop_status", "engaged": False, "source": ""})
        if self.ws_server and self.ws_server.loop:
            asyncio.run_coroutine_threadsafe(self.ws_server.broadcast(status), self.ws_server.loop)
        self.get_logger().info("Notstopp aufgehoben")

    def _emergency_stop_cb(self, msg):
        """Callback fuer /emergency_stop (Hardware-E-Stop, Phase 2)."""
        if msg.data and not self.estop_engaged:
            self.unified_estop("hardware")

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
                offset_info = (
                    f", clock_offset={self._clock_offset_ms:.1f} ms"
                    if self._offset_calibrated
                    else ""
                )
                self.get_logger().info(
                    f"Serial-Latenz: avg={latency_stats['avg_ms']:.1f} ms, "
                    f"p95={latency_stats['p95_ms']:.1f} ms, "
                    f"max={latency_stats['max_ms']:.1f} ms"
                    f"{offset_info} "
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
                "direction_filtered_deg": self.doa_filtered,
                "quadrant": self.doa_quadrant,
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
