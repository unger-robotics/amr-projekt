#!/usr/bin/env python3
"""ROS2-Node: Sprachsteuerung via ReSpeaker + Gemini Flash STT.

Nimmt gesprochene Befehle ueber das ReSpeaker-Mikrofon auf (VAD-gesteuert),
transkribiert und erkennt Intents via Gemini Flash in einem API-Call und
publiziert das Ergebnis als strukturierten Befehl fuer die dashboard_bridge.

Subscriptions:
  /is_voice       (std_msgs/Bool)   — VAD-Signal vom respeaker_doa_node (10 Hz)

Publications:
  /voice/command  (std_msgs/String) — Strukturierter Befehl (Freitext fuer _handle_command)
  /voice/text     (std_msgs/String) — Rohtranskription (fuer Dashboard/Logging)

Umgebungsvariable:
  GEMINI_API_KEY — Google AI API-Schluessel (erforderlich)

Parameter:
  audio_device   (string, "auto")           — ALSA-Device (auto = ReSpeaker erkennen)
  gemini_model   (string, "gemini-2.5-flash") — Gemini-Modell
  max_record_s   (float, 10.0)              — Max. Aufnahmedauer [s]
  min_record_s   (float, 0.5)               — Min. Aufnahmedauer [s]
  cooldown_s     (float, 0.5)               — VAD-Cooldown nach Sprachende [s]
  rate_limit_s   (float, 2.0)               — Min. Zeit zwischen Gemini-Calls [s]
  barge_in_s     (float, 2.0)               — Aufnahme-Sperre nach eigenem TTS [s]
  dedup_s        (float, 5.0)               — Deduplizierung: gleicher Befehl innerhalb [s] unterdrueckt
  confirm_tts    (bool, True)               — TTS-Bestaetigung nach Befehl
  min_vad_s      (float, 0.3)              — Min. kontinuierliche VAD-Dauer vor Aufnahme [s]

Verwendung:
  ros2 run my_bot voice_command_node
  ros2 run my_bot voice_command_node --ros-args -p gemini_model:=gemini-2.5-flash
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String

try:
    from google import genai
    from google.genai import types

    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# State-Konstanten
_IDLE = "idle"
_LISTENING = "listening"
_COOLDOWN = "cooldown"
_PROCESSING = "processing"

# Rate-Limiting / Backoff
MIN_REQUEST_INTERVAL_S = 2.0
QUOTA_BACKOFF_S = 300.0

SYSTEM_PROMPT = """\
Du bist der Sprachassistent eines autonomen mobilen Roboters (AMR).
Extrahiere aus dem gesprochenen deutschen Befehl EINEN Roboter-Befehl.

Antworte AUSSCHLIESSLICH mit einem JSON-Objekt, kein weiterer Text.
Format: {"command": "<befehl>", "transcript": "<transkription>"}

Verfuegbare Befehle (Feld "command"):
- "nav X Y"           Navigation zu Koordinaten (Meter, Dezimalpunkt)
- "stop"              Sofortstopp aller Motoren
- "forward X"         X Meter geradeaus fahren (0-5 m)
- "backward X"        X Meter rueckwaerts fahren (0-5 m)
- "turn X"            X Grad drehen (positiv=links, negativ=rechts)
- "turn_to_speaker"   Zum Sprecher drehen (Richtung per Mikrofon-Array)
- "test <name>"       Test ausfuehren (rplidar, imu, motor, encoder, sensor,
                       kinematic, straight_drive, rotation, cliff_latency,
                       slam, nav, nav_square, docking, dashboard_latency, can)
- "schau nach links"  Kamera nach links schwenken
- "schau nach rechts" Kamera nach rechts schwenken
- "schau nach vorne"  Kamera geradeaus
- "licht an"          LED einschalten
- "licht aus"         LED ausschalten
- "wie weit"          Ultraschall-Distanz abfragen
- "akku"              Batteriestatus abfragen
- "wo bin ich"        Aktuelle Position und Ausrichtung
- "wetter"            Aktuelle Wetterdaten abfragen
- "help"              Hilfe anzeigen
- ""                  Kein Befehl erkannt (Geraeusch, unverstaendlich)

Beispiele:
- "Fahr mal zwei Meter nach vorne" -> {"command": "forward 2", "transcript": "fahr mal zwei meter nach vorne"}
- "Fahr einen Meter zurueck" -> {"command": "backward 1", "transcript": "fahr einen meter zurueck"}
- "Dreh dich neunzig Grad nach links" -> {"command": "turn 90", "transcript": "dreh dich neunzig grad nach links"}
- "Stopp!" -> {"command": "stop", "transcript": "stopp"}
- "Wie weit ist das Hindernis?" -> {"command": "wie weit", "transcript": "wie weit ist das hindernis"}
- "Dreh dich zu mir" -> {"command": "turn_to_speaker", "transcript": "dreh dich zu mir"}
- "Schau mich an" -> {"command": "turn_to_speaker", "transcript": "schau mich an"}
- "Wo bin ich?" -> {"command": "wo bin ich", "transcript": "wo bin ich"}
- "Wie ist das Wetter?" -> {"command": "wetter", "transcript": "wie ist das wetter"}
- [Hintergrundgeraeusch] -> {"command": "", "transcript": ""}
- [kurzes Geraeusch, Piepen, Klicken] -> {"command": "", "transcript": ""}
- [unverstaendliches Gemurmel] -> {"command": "", "transcript": ""}

WICHTIG: Im Zweifel IMMER leeren command zurueckgeben. Nur bei klar
verstaendlichen deutschen Saetzen einen Befehl erkennen. Einzelne Silben,
Atemgeraeusche, Umgebungslaerm oder unklare Fragmente sind KEIN Befehl.
"""


class VoiceCommandNode(Node):
    """ROS2-Node: Sprachsteuerung via ReSpeaker VAD + Gemini Flash STT."""

    def __init__(self) -> None:
        super().__init__("voice_command_node")

        # -- Parameter --
        self.declare_parameter("audio_device", "auto")
        self.declare_parameter("gemini_model", "gemini-2.5-flash")
        self.declare_parameter("max_record_s", 10.0)
        self.declare_parameter("min_record_s", 0.5)
        self.declare_parameter("cooldown_s", 0.5)
        self.declare_parameter("rate_limit_s", 2.0)
        self.declare_parameter("barge_in_s", 2.0)
        self.declare_parameter("dedup_s", 5.0)
        self.declare_parameter("confirm_tts", True)
        self.declare_parameter("min_vad_s", 0.3)

        model_name = self.get_parameter("gemini_model").get_parameter_value().string_value
        self._max_record_s = self.get_parameter("max_record_s").value
        self._min_record_s = self.get_parameter("min_record_s").value
        self._cooldown_s = self.get_parameter("cooldown_s").value
        self._rate_limit_s = self.get_parameter("rate_limit_s").value
        self._barge_in_s = self.get_parameter("barge_in_s").value
        self._dedup_s = self.get_parameter("dedup_s").value
        self._confirm_tts = self.get_parameter("confirm_tts").value
        self._min_vad_s = self.get_parameter("min_vad_s").value

        # -- Abhaengigkeiten pruefen --
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

        if not shutil.which("arecord"):
            self.get_logger().error("arecord nicht gefunden! alsa-utils installieren.")
            return

        # -- Gemini Client --
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        # -- ALSA-Device erkennen --
        device_param = self.get_parameter("audio_device").get_parameter_value().string_value
        detected = self._find_respeaker_device() if device_param == "auto" else device_param

        if not detected:
            self.get_logger().error(
                "ReSpeaker ALSA-Device nicht gefunden! "
                "Manuell setzen: --ros-args -p audio_device:=plughw:CARD=ArrayUAC10"
            )
            return
        self._audio_device: str = detected

        # -- Publisher / Subscriber --
        self._pub_command = self.create_publisher(String, "/voice/command", 10)
        self._pub_text = self.create_publisher(String, "/voice/text", 10)
        self._pub_audio_play = self.create_publisher(String, "/audio/play", 10)
        self.create_subscription(Bool, "/is_voice", self._vad_cb, 10)
        self.create_subscription(Bool, "/voice/mute", self._mute_cb, 10)

        # -- State Machine --
        self._muted = False
        self._state = _IDLE
        self._vad_active = False
        self._vad_last_true = 0.0
        self._vad_continuous_start = 0.0  # Beginn der aktuellen VAD-Aktivphase
        self._record_proc: subprocess.Popen | None = None
        self._record_start = 0.0
        self._last_gemini_time = 0.0
        self._last_tts_time = 0.0
        self._last_command = ""
        self._last_command_time = 0.0
        self._pending = False

        # Timer: 20 Hz State-Machine Tick
        self.create_timer(0.05, self._tick)

        self.get_logger().info(
            f"VoiceCommandNode gestartet (Modell: {model_name}, Device: {self._audio_device})"
        )

    # -----------------------------------------------------------------
    # ALSA-Device Auto-Detection
    # -----------------------------------------------------------------

    def _find_respeaker_device(self) -> str | None:
        """Erkennt ReSpeaker ALSA-Device ueber Kartennamen."""
        try:
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if "ArrayUAC10" in line or "ReSpeaker" in line:
                    # "card 2: ArrayUAC10 [...]" → "plughw:2,0"
                    m = re.search(r"card\s+(\d+)", line)
                    if m:
                        card_num = m.group(1)
                        device = f"plughw:{card_num},0"
                        self.get_logger().info(f"ReSpeaker erkannt: {device}")
                        return device
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn(f"ALSA-Device-Erkennung fehlgeschlagen: {e}")
        return None

    # -----------------------------------------------------------------
    # VAD Callback
    # -----------------------------------------------------------------

    def _mute_cb(self, msg: Bool) -> None:
        """Mute-Callback: Mikrofon stumm schalten / aktivieren."""
        self._muted = msg.data
        self.get_logger().info(f"Mikrofon {'stumm' if msg.data else 'aktiv'}")

    def _vad_cb(self, msg: Bool) -> None:
        """VAD-Callback: Aktualisiert Zeitstempel bei Spracherkennung."""
        was_active = self._vad_active
        self._vad_active = msg.data
        if msg.data:
            self._vad_last_true = time.monotonic()
            # Beginn einer neuen kontinuierlichen VAD-Phase merken
            if not was_active:
                self._vad_continuous_start = time.monotonic()

    # -----------------------------------------------------------------
    # State Machine
    # -----------------------------------------------------------------

    def _tick(self) -> None:
        """State-Machine Tick (20 Hz)."""
        now = time.monotonic()

        # Barge-In-Schutz: Nicht aufnehmen waehrend TTS-Ausgabe
        if now - self._last_tts_time < self._barge_in_s:
            return

        if self._state == _IDLE:
            # Warte auf VAD=True fuer mindestens min_vad_s + Rate-Limit (nicht im Mute-Modus)
            if (
                self._vad_active
                and not self._muted
                and now - self._last_gemini_time >= self._rate_limit_s
                and now - self._vad_continuous_start >= self._min_vad_s
            ):
                self._start_recording()
                self._state = _LISTENING
                self.get_logger().debug("IDLE -> LISTENING: VAD aktiv")

        elif self._state == _LISTENING:
            elapsed = now - self._record_start

            # Max-Aufnahmedauer erreicht → direkt zu PROCESSING
            if elapsed >= self._max_record_s:
                self._transition_to_processing()
                return

            # VAD wurde inaktiv → COOLDOWN starten
            if not self._vad_active:
                self._state = _COOLDOWN
                self.get_logger().debug("LISTENING -> COOLDOWN: VAD inaktiv")

        elif self._state == _COOLDOWN:
            elapsed = now - self._record_start

            # Max-Aufnahmedauer auch im Cooldown beachten
            if elapsed >= self._max_record_s:
                self._transition_to_processing()
                return

            # VAD wieder aktiv → zurueck zu LISTENING
            if self._vad_active:
                self._state = _LISTENING
                self.get_logger().debug("COOLDOWN -> LISTENING: VAD wieder aktiv")
                return

            # Cooldown abgelaufen → PROCESSING
            time_since_last_voice = now - self._vad_last_true
            if time_since_last_voice >= self._cooldown_s:
                self._transition_to_processing()

        elif self._state == _PROCESSING and not self._pending:
            self._state = _IDLE

    # -----------------------------------------------------------------
    # Audio-Aufnahme
    # -----------------------------------------------------------------

    def _start_recording(self) -> None:
        """Startet arecord als Subprocess (stdout=PIPE fuer WAV-Daten)."""
        max_s = str(int(self._max_record_s + 1))
        self._record_proc = subprocess.Popen(
            [
                "arecord",
                "-D",
                self._audio_device,
                "-f",
                "S16_LE",
                "-r",
                "16000",
                "-c",
                "1",
                "-t",
                "wav",
                "-d",
                max_s,
                "-q",
                "-",  # stdout
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._record_start = time.monotonic()

    def _stop_recording(self) -> bytes:
        """Stoppt arecord und gibt WAV-Bytes zurueck."""
        if self._record_proc is None:
            return b""
        try:
            self._record_proc.terminate()
            stdout, _ = self._record_proc.communicate(timeout=3.0)
            return stdout or b""
        except (subprocess.TimeoutExpired, Exception):  # noqa: BLE001
            self._record_proc.kill()
            self._record_proc.wait(timeout=2.0)
            return b""
        finally:
            self._record_proc = None

    # -----------------------------------------------------------------
    # Processing (Gemini API im Daemon-Thread)
    # -----------------------------------------------------------------

    def _transition_to_processing(self) -> None:
        """Stoppt Aufnahme und startet Gemini-Verarbeitung."""
        wav_bytes = self._stop_recording()
        duration = time.monotonic() - self._record_start

        if duration < self._min_record_s or len(wav_bytes) < 1000:
            self.get_logger().debug(f"Aufnahme zu kurz ({duration:.1f} s) oder leer — verworfen")
            self._state = _IDLE
            return

        self._pending = True
        self._state = _PROCESSING
        self.get_logger().info(f"Aufnahme beendet ({duration:.1f} s), sende an Gemini...")

        thread = threading.Thread(target=self._process_audio, args=(wav_bytes,), daemon=True)
        thread.start()

    def _process_audio(self, wav_bytes: bytes) -> None:
        """Sendet WAV an Gemini, parst JSON-Antwort, publiziert Befehl."""
        try:
            audio_part = types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[SYSTEM_PROMPT, audio_part],
                config=types.GenerateContentConfig(
                    max_output_tokens=256,
                    temperature=0.1,
                ),
            )
            self._last_gemini_time = time.monotonic()

            if not response or not response.text:
                self.get_logger().warn("Gemini: Leere Antwort erhalten")
                return

            # JSON-Antwort parsen (Markdown-Fences entfernen falls vorhanden)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            result = json.loads(text)
            command = result.get("command", "").strip()
            transcript = result.get("transcript", "").strip()

            # Lokaler Regex-Fallback: wenn Gemini keinen command liefert,
            # aber die Transkription ein bekanntes Muster enthaelt
            if not command and transcript:
                command = self._fallback_intent(transcript)
                if command:
                    self.get_logger().info(
                        f"Fallback-Intent: '{command}' (Transkription: '{transcript}')"
                    )

            # Deduplizierung: gleichen Befehl innerhalb dedup_s unterdruecken
            now = time.monotonic()
            is_duplicate = (
                command
                and command == self._last_command
                and now - self._last_command_time < self._dedup_s
            )

            # Befehl publizieren (VOR Transkript, damit Bridge den Befehl
            # bereits gespeichert hat, wenn das Transkript eintrifft)
            if command and is_duplicate:
                self.get_logger().info(
                    f"Duplikat unterdrueckt: '{command}' "
                    f"({now - self._last_command_time:.1f} s seit letztem)"
                )
            elif command:
                self._last_command = command
                self._last_command_time = now
                cmd_msg = String()
                cmd_msg.data = command
                self._pub_command.publish(cmd_msg)
                self.get_logger().info(f"Befehl: '{command}'")

                # TTS-Bestaetigung
                if self._confirm_tts:
                    ack_msg = String()
                    ack_msg.data = "nav_start"
                    self._pub_audio_play.publish(ack_msg)
                    self._last_tts_time = time.monotonic()
            else:
                self.get_logger().info(f"Kein Befehl erkannt (Transkription: '{transcript}')")

            # Rohtranskription publizieren (NACH Befehl), bei Duplikat unterdruecken
            if transcript and not is_duplicate:
                txt_msg = String()
                txt_msg.data = transcript
                self._pub_text.publish(txt_msg)
                self.get_logger().info(f"Transkription: '{transcript}'")

        except json.JSONDecodeError as e:
            self.get_logger().warn(f"Gemini-JSON ungueltig: {e}")
        except Exception as e:  # noqa: BLE001
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                self._last_gemini_time = time.monotonic() + QUOTA_BACKOFF_S - MIN_REQUEST_INTERVAL_S
                self.get_logger().warn(
                    f"Gemini-Quota erschoepft — pausiere {QUOTA_BACKOFF_S:.0f}s. {err_str[:120]}"
                )
            else:
                self.get_logger().error(f"Gemini-API-Fehler: {e}")
        finally:
            self._pending = False

    # -----------------------------------------------------------------
    # Lokaler Regex-Fallback (wenn Gemini keinen command liefert)
    # -----------------------------------------------------------------

    _FALLBACK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (
            re.compile(r"dreh.*zu\s+mir|schau.*(?:zu\s+mir|mich\s+an)|komm.*zu\s+mir"),
            "turn_to_speaker",
        ),
        (re.compile(r"(?:halt|stopp|anhalten|bleib\s+stehen|not\s*aus)"), "stop"),
        (re.compile(r"licht\s+an|led\s+an|beleuchtung\s+an"), "licht an"),
        (re.compile(r"licht\s+aus|led\s+aus|beleuchtung\s+aus"), "licht aus"),
        (re.compile(r"schau\s+nach\s+links|kamera\s+links"), "schau nach links"),
        (re.compile(r"schau\s+nach\s+rechts|kamera\s+rechts"), "schau nach rechts"),
        (
            re.compile(r"schau\s+nach\s+vorne|kamera\s+vorne|geradeaus\s+schauen"),
            "schau nach vorne",
        ),
        (re.compile(r"wie\s+weit|abstand|distanz|hindernis"), "wie weit"),
        (re.compile(r"akku|batterie"), "akku"),
        (re.compile(r"wo\s+bin\s+ich|position|standort|koordinaten"), "wo bin ich"),
        (re.compile(r"wetter|weather|temperatur\s+draussen"), "wetter"),
        (re.compile(r"hilfe|help|was\s+kannst\s+du"), "help"),
    ]

    @staticmethod
    def _fallback_intent(transcript: str) -> str:
        """Matcht Transkription gegen bekannte Muster, gibt command oder '' zurueck."""
        t = transcript.lower().strip()
        for pattern, cmd in VoiceCommandNode._FALLBACK_PATTERNS:
            if pattern.search(t):
                return cmd
        return ""

    # -----------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------

    def destroy_node(self) -> None:
        """Bereinigung: Laufende arecord-Prozesse beenden."""
        if self._record_proc is not None:
            try:
                self._record_proc.kill()
                self._record_proc.wait(timeout=2.0)
            except Exception:  # noqa: BLE001
                pass
        super().destroy_node()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = VoiceCommandNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
