#!/usr/bin/env python3
"""
Audio-Feedback-Node fuer den AMR-Roboter.
ROS2-Node: subscribt /audio/play (std_msgs/String) und spielt WAV-Dateien ab.

Features:
  - Priority-Preemption: cliff_alarm unterbricht laufende Sounds
  - Concurrency: Nicht-Priority-Anfragen werden bei laufendem Sound ignoriert
  - Graceful Degradation: Warnung wenn aplay nicht verfuegbar

Sounds werden im Share-Verzeichnis des my_bot-Pakets erwartet (sounds/).
"""

import shutil
import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ===========================================================================
# Sound-Mapping
# ===========================================================================

SOUND_MAP = {
    "cliff_alarm": "alert.wav",
    "nav_start": "nav_start.wav",
    "nav_reached": "nav_reached.wav",
    "startup": "startup.wav",
}

PRIORITY_SOUNDS = {"cliff_alarm"}


# ===========================================================================
# ROS2-Node
# ===========================================================================


class AudioFeedbackNode(Node):
    """ROS2-Node fuer Audio-Feedback via aplay."""

    def __init__(self):
        super().__init__("audio_feedback_node")

        self._aplay_available = shutil.which("aplay") is not None
        if not self._aplay_available:
            self.get_logger().warning("aplay nicht gefunden — Audio-Wiedergabe deaktiviert")

        self._sounds_dir = self._resolve_sounds_dir()
        self._current_proc = None

        self.create_subscription(String, "/audio/play", self._play_callback, 10)

        self.get_logger().info(f"Audio-Feedback-Node gestartet. Sounds: {self._sounds_dir}")

    def _resolve_sounds_dir(self):
        """Ermittelt den Pfad zum sounds/-Verzeichnis."""
        # 1. Installierter Share-Pfad via ament_index
        try:
            from ament_index_python.packages import get_package_share_directory

            share_dir = get_package_share_directory("my_bot")
            return share_dir + "/sounds/"
        except Exception:
            pass

        # 2. Fallback: Workspace-Pfad
        fallback = "/ros2_ws/src/my_bot/sounds/"
        self.get_logger().info(f"ament_index nicht verfuegbar, Fallback: {fallback}")
        return fallback

    def _play_callback(self, msg):
        """Callback fuer /audio/play — spielt den angeforderten Sound ab."""
        key = msg.data.strip()

        if key not in SOUND_MAP:
            self.get_logger().warning(f"Unbekannter Sound-Key: '{key}'")
            return

        if not self._aplay_available:
            self.get_logger().debug(f"aplay nicht verfuegbar, ignoriere: {key}")
            return

        is_priority = key in PRIORITY_SOUNDS

        # Laufender Sound?
        if self._current_proc is not None and self._current_proc.poll() is None:
            if is_priority:
                self._current_proc.terminate()
                self.get_logger().info(f"Priority-Sound '{key}' unterbricht laufende Wiedergabe")
            else:
                self.get_logger().debug(f"Sound '{key}' ignoriert — Wiedergabe laeuft bereits")
                return

        filepath = self._sounds_dir + SOUND_MAP[key]

        try:
            self._current_proc = subprocess.Popen(
                ["aplay", "-q", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.get_logger().info(f"Spiele: {key} ({SOUND_MAP[key]})")
        except FileNotFoundError:
            self.get_logger().warning(f"WAV-Datei nicht gefunden: {filepath}")
        except OSError as e:
            self.get_logger().error(f"Fehler bei Wiedergabe von {key}: {e}")

    def destroy_node(self):
        """Beendet laufende Wiedergabe beim Shutdown."""
        if self._current_proc is not None and self._current_proc.poll() is None:
            self._current_proc.terminate()
        super().destroy_node()


# ===========================================================================
# Entry Point
# ===========================================================================


def main(args=None):
    rclpy.init(args=args)
    node = AudioFeedbackNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
