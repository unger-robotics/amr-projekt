#!/usr/bin/env python3
"""ROS2-Node: Text-to-Speech Sprachausgabe fuer Gemini-Semantik.

Subscribt /vision/semantics (std_msgs/String, JSON) und spricht die
semantische Analyse ueber den Lautsprecher (MAX98357A) via gTTS + mpg123.

Rate-Limiting: Mindestens 10 Sekunden zwischen Sprachausgaben,
damit nicht jede Gemini-Antwort sofort gesprochen wird.

Subscriptions:
  /vision/semantics (std_msgs/String) - Gemini-Analyse als JSON
  /audio/volume (std_msgs/Int32) - Lautstaerke-Aenderungen mitlesen

Verwendung:
  ros2 run my_bot tts_speak_node
"""

import json
import shutil
import subprocess
import tempfile
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

try:
    from gtts import gTTS

    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# Mindestabstand zwischen Sprachausgaben (Sekunden)
MIN_SPEAK_INTERVAL_S = 10.0

# gTTS-Sprache
TTS_LANG = "de"


class TtsSpeakNode(Node):
    """ROS2-Node fuer TTS-Sprachausgabe der Gemini-Semantik."""

    def __init__(self):
        super().__init__("tts_speak_node")

        if not HAS_GTTS:
            self.get_logger().error("gTTS nicht installiert! pip3 install gTTS")
            return

        self._mpg123_available = shutil.which("mpg123") is not None
        if not self._mpg123_available:
            self.get_logger().error("mpg123 nicht gefunden — TTS-Wiedergabe nicht moeglich")
            return

        self._speaking = False
        self._last_speak_time = 0.0

        self.create_subscription(String, "/vision/semantics", self._semantics_cb, 10)

        self.get_logger().info(
            f"TTS-Speak-Node gestartet (Sprache: {TTS_LANG}, "
            f"Mindestintervall: {MIN_SPEAK_INTERVAL_S}s)"
        )

    def _semantics_cb(self, msg):
        """Callback fuer /vision/semantics — spricht die Gemini-Analyse."""
        if self._speaking:
            return

        now = time.monotonic()
        if now - self._last_speak_time < MIN_SPEAK_INTERVAL_S:
            return

        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return

        text = data.get("semantic_analysis", "").strip()
        if not text:
            return

        self._speaking = True
        self._last_speak_time = now

        thread = threading.Thread(target=self._speak, args=(text,), daemon=True)
        thread.start()

    def _speak(self, text):
        """Text via gTTS synthetisieren und mit mpg123 abspielen."""
        try:
            tts = gTTS(text=text, lang=TTS_LANG)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
                tts.save(tmp_path)

            self.get_logger().info(f"TTS: {text[:80]}")
            subprocess.run(
                ["mpg123", "-q", tmp_path],
                timeout=30,
                capture_output=True,
            )
        except subprocess.TimeoutExpired:
            self.get_logger().warning("TTS-Wiedergabe Timeout (>30s)")
        except Exception as e:
            self.get_logger().error(f"TTS-Fehler: {e}")
        finally:
            self._speaking = False
            try:
                import os

                os.unlink(tmp_path)
            except Exception:
                pass


def main(args=None):
    rclpy.init(args=args)
    node = TtsSpeakNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
