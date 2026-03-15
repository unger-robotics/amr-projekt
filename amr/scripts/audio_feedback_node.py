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
from std_msgs.msg import Int32, String

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

# ALSA-Konfiguration: softvol-Device und Mixer-Control
ALSA_DEVICE = "default"  # Nutzt softvol via /etc/asound.conf
ALSA_MIXER_CONTROL = "SoftMaster"  # softvol-Kontrollname
DEFAULT_VOLUME_PCT = 50


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
        self._volume_pct = DEFAULT_VOLUME_PCT

        self.create_subscription(String, "/audio/play", self._play_callback, 10)
        self.create_subscription(Int32, "/audio/volume", self._volume_callback, 10)

        # softvol-Control initialisieren (lazy — entsteht erst beim ersten Abspielen)
        self._init_softvol()

        # Initiale Lautstaerke setzen
        self._apply_volume(self._volume_pct)

        self.get_logger().info(
            f"Audio-Feedback-Node gestartet. Sounds: {self._sounds_dir}, "
            f"Lautstaerke: {self._volume_pct}%"
        )

    def _init_softvol(self):
        """Initialisiert ALSA softvol-Control durch kurze Stille-Wiedergabe.

        softvol-Controls werden von ALSA erst beim ersten Oeffnen des PCM-Geraets
        angelegt. Ohne diesen Schritt schlaegt amixer sset SoftMaster fehl.
        """
        try:
            subprocess.run(
                [
                    "aplay",
                    "-q",
                    "-D",
                    ALSA_DEVICE,
                    "/dev/zero",
                    "-d",
                    "1",
                    "-f",
                    "S16_LE",
                    "-r",
                    "8000",
                    "-c",
                    "1",
                ],
                capture_output=True,
                timeout=3,
            )
            self.get_logger().info("ALSA softvol-Control initialisiert")
        except Exception:
            self.get_logger().warning("softvol-Initialisierung fehlgeschlagen")

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

    def _volume_callback(self, msg):
        """Callback fuer /audio/volume — setzt ALSA-Lautstaerke (0-100%)."""
        vol = max(0, min(100, msg.data))
        if vol == self._volume_pct:
            return
        self._volume_pct = vol
        self._apply_volume(vol)

    def _apply_volume(self, volume_pct):
        """Setzt die ALSA-Softwarelautstaerke via amixer."""
        try:
            result = subprocess.run(
                ["amixer", "-q", "sset", ALSA_MIXER_CONTROL, f"{volume_pct}%"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode != 0:
                self.get_logger().warning(
                    f"amixer Fehler (rc={result.returncode}): {result.stderr.strip()}"
                )
            else:
                self.get_logger().info(f"Lautstaerke: {volume_pct}%")
        except FileNotFoundError:
            self.get_logger().warning("amixer nicht gefunden — Lautstaerke nicht einstellbar")
        except subprocess.TimeoutExpired:
            self.get_logger().warning("amixer Timeout")
        except OSError as e:
            self.get_logger().warning(f"amixer Fehler: {e}")

    @property
    def volume_pct(self):
        """Aktuelle Lautstaerke in Prozent."""
        return self._volume_pct

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
                ["aplay", "-q", "-D", ALSA_DEVICE, filepath],
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
