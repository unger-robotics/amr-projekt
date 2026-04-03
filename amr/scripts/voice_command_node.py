#!/usr/bin/env python3
"""ROS2-Node: Sprachsteuerung via ReSpeaker + lokales Whisper STT.

Nimmt gesprochene Befehle ueber das ReSpeaker-Mikrofon auf (VAD-gesteuert),
transkribiert lokal via faster-whisper und erkennt Intents per Regex-Parser.
Keine Cloud-Abhaengigkeit, laeuft vollstaendig offline auf dem Pi 5.

Subscriptions:
  /is_voice       (std_msgs/Bool)   — VAD-Signal vom respeaker_doa_node (10 Hz)

Publications:
  /voice/command  (std_msgs/String) — Strukturierter Befehl (Freitext fuer _handle_command)
  /voice/text     (std_msgs/String) — Rohtranskription (fuer Dashboard/Logging)

Parameter:
  audio_device   (string, "auto")           — ALSA-Device (auto = ReSpeaker erkennen)
  whisper_model  (string, "base")           — Whisper-Modellgroesse (tiny/base/small)
  max_record_s   (float, 10.0)              — Max. Aufnahmedauer [s]
  min_record_s   (float, 0.5)               — Min. Aufnahmedauer [s]
  cooldown_s     (float, 0.5)               — VAD-Cooldown nach Sprachende [s]
  rate_limit_s   (float, 2.0)               — Min. Zeit zwischen STT-Verarbeitungen [s]
  barge_in_s     (float, 2.0)               — Aufnahme-Sperre nach eigenem TTS [s]
  dedup_s        (float, 5.0)               — Deduplizierung: gleicher Befehl innerhalb [s] unterdrueckt
  confirm_tts    (bool, True)               — TTS-Bestaetigung nach Befehl
  min_vad_s      (float, 0.3)              — Min. kontinuierliche VAD-Dauer vor Aufnahme [s]
  energy_threshold_rms (float, 500.0)     — RMS-Schwelle: Aufnahmen unter Schwelle verwerfen
  use_wakeword   (bool, True)             — Lokale Wake-Word-Erkennung (openwakeword)
  wakeword_model (string, "hey_jarvis_v0.1") — openwakeword-Modellname
  wakeword_threshold (float, 0.5)         — Wake-Word-Erkennungsschwelle (0.0-1.0)

Verwendung:
  ros2 run my_bot voice_command_node
  ros2 run my_bot voice_command_node --ros-args -p whisper_model:=small
"""

from __future__ import annotations

import io
import math
import re
import shutil
import struct
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String

try:
    from faster_whisper import WhisperModel

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    import numpy as np
    from openwakeword.model import Model as OwwModel

    HAS_OWW = True
except ImportError:
    HAS_OWW = False

# State-Konstanten
_IDLE = "idle"
_WAKE_LISTENING = "wake_listening"
_LISTENING = "listening"
_COOLDOWN = "cooldown"
_PROCESSING = "processing"

# Rate-Limiting
MIN_REQUEST_INTERVAL_S = 2.0
WAV_HEADER_SIZE = 44  # Standard-WAV-Header-Laenge in Bytes
OWW_CHUNK_SAMPLES = 1280  # 80 ms bei 16 kHz (openwakeword erwartet 80ms-Chunks)
OWW_CHUNK_BYTES = OWW_CHUNK_SAMPLES * 2  # int16 = 2 Bytes/Sample

# Deutsche Zahlwoerter fuer Intent-Parser
_ZAHLWOERTER: dict[str, float] = {
    "null": 0,
    "eins": 1,
    "ein": 1,
    "einen": 1,
    "einem": 1,
    "einer": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fuenf": 5,
    "fünf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
    "elf": 11,
    "zwoelf": 12,
    "zwölf": 12,
    "dreizehn": 13,
    "vierzehn": 14,
    "fuenfzehn": 15,
    "fünfzehn": 15,
    "sechzehn": 16,
    "siebzehn": 17,
    "achtzehn": 18,
    "neunzehn": 19,
    "zwanzig": 20,
    "dreissig": 30,
    "dreißig": 30,
    "vierzig": 40,
    "fuenfzig": 50,
    "fünfzig": 50,
    "sechzig": 60,
    "siebzig": 70,
    "achtzig": 80,
    "neunzig": 90,
    "hundert": 100,
    "halber": 0.5,
    "halben": 0.5,
    "halb": 0.5,
    "anderthalb": 1.5,
}

# Bekannte Testnamen fuer "test <name>" Befehl
_TEST_NAMES = {
    "rplidar",
    "imu",
    "motor",
    "encoder",
    "sensor",
    "kinematic",
    "straight_drive",
    "geradeaus",
    "rotation",
    "cliff_latency",
    "cliff",
    "slam",
    "nav",
    "nav_square",
    "quadrat",
    "docking",
    "dashboard_latency",
    "dashboard",
    "can",
}

# Mapping fuer umgangssprachliche Testnamen
_TEST_ALIASES: dict[str, str] = {
    "geradeaus": "straight_drive",
    "quadrat": "nav_square",
    "dashboard": "dashboard_latency",
    "cliff": "cliff_latency",
}


class VoiceCommandNode(Node):
    """ROS2-Node: Sprachsteuerung via ReSpeaker VAD + lokales Whisper STT."""

    def __init__(self) -> None:
        super().__init__("voice_command_node")

        # -- Parameter --
        self.declare_parameter("audio_device", "auto")
        self.declare_parameter("whisper_model", "base")
        self.declare_parameter("max_record_s", 10.0)
        self.declare_parameter("min_record_s", 0.5)
        self.declare_parameter("cooldown_s", 0.5)
        self.declare_parameter("rate_limit_s", 2.0)
        self.declare_parameter("barge_in_s", 2.0)
        self.declare_parameter("dedup_s", 5.0)
        self.declare_parameter("confirm_tts", True)
        self.declare_parameter("min_vad_s", 0.3)
        self.declare_parameter("energy_threshold_rms", 500.0)
        self.declare_parameter("use_wakeword", True)
        self.declare_parameter("wakeword_model", "hey_jarvis_v0.1")
        self.declare_parameter("wakeword_threshold", 0.5)

        whisper_size = self.get_parameter("whisper_model").get_parameter_value().string_value
        self._max_record_s = self.get_parameter("max_record_s").value
        self._min_record_s = self.get_parameter("min_record_s").value
        self._cooldown_s = self.get_parameter("cooldown_s").value
        self._rate_limit_s = self.get_parameter("rate_limit_s").value
        self._barge_in_s = self.get_parameter("barge_in_s").value
        self._dedup_s = self.get_parameter("dedup_s").value
        self._confirm_tts = self.get_parameter("confirm_tts").value
        self._min_vad_s = self.get_parameter("min_vad_s").value
        self._energy_threshold_rms = self.get_parameter("energy_threshold_rms").value
        self._use_wakeword = self.get_parameter("use_wakeword").value
        self._wakeword_model = (
            self.get_parameter("wakeword_model").get_parameter_value().string_value
        )
        self._wakeword_threshold = self.get_parameter("wakeword_threshold").value

        # -- Abhaengigkeiten pruefen --
        if not HAS_WHISPER:
            self.get_logger().error("faster-whisper nicht installiert! pip3 install faster-whisper")
            return

        if not shutil.which("arecord"):
            self.get_logger().error("arecord nicht gefunden! alsa-utils installieren.")
            return

        # -- Whisper-Modell laden (lokal, offline) --
        self.get_logger().info(f"Lade Whisper-Modell '{whisper_size}' (CPU/int8)...")
        self._whisper = WhisperModel(whisper_size, device="cpu", compute_type="int8")
        self.get_logger().info(f"Whisper-Modell '{whisper_size}' geladen")

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
        self._vad_active = False
        self._vad_last_true = 0.0
        self._vad_continuous_start = 0.0  # Beginn der aktuellen VAD-Aktivphase
        self._record_proc: subprocess.Popen | None = None
        self._record_start = 0.0
        self._last_stt_time = 0.0
        self._last_tts_time = 0.0
        self._last_command = ""
        self._last_command_time = 0.0
        self._pending = False

        # -- Wake-Word-Erkennung (openwakeword) --
        self._oww_model = None  # Optional[OwwModel] — nur wenn HAS_OWW
        self._wakeword_detected = False
        self._ww_stream_proc: subprocess.Popen | None = None
        self._ww_running = False

        if self._use_wakeword and HAS_OWW:
            try:
                self._oww_model = OwwModel(
                    wakeword_models=[self._wakeword_model],
                    inference_framework="onnx",
                )
                self._ww_running = True
                self._ww_thread = threading.Thread(target=self._wakeword_listener, daemon=True)
                self._ww_thread.start()
                self.get_logger().info(
                    f"Wake-Word-Erkennung aktiv (Modell: {self._wakeword_model}, "
                    f"Schwelle: {self._wakeword_threshold})"
                )
            except Exception as e:  # noqa: BLE001
                self.get_logger().warn(
                    f"Wake-Word-Initialisierung fehlgeschlagen: {e} — Fallback auf VAD-Modus"
                )
                self._use_wakeword = False
        elif self._use_wakeword and not HAS_OWW:
            self.get_logger().warn(
                "openwakeword nicht installiert (pip3 install openwakeword onnxruntime) "
                "— Fallback auf VAD-Modus"
            )
            self._use_wakeword = False

        # Startzustand: Wake-Listening oder Idle (je nach Modus)
        self._state = _WAKE_LISTENING if self._use_wakeword else _IDLE

        # Timer: 20 Hz State-Machine Tick
        self.create_timer(0.05, self._tick)

        ww_info = f", Wake-Word: {self._wakeword_model}" if self._use_wakeword else ""
        self.get_logger().info(
            f"VoiceCommandNode gestartet (Whisper: {whisper_size}, "
            f"Device: {self._audio_device}{ww_info})"
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
    # Wake-Word-Erkennung (openwakeword)
    # -----------------------------------------------------------------

    def _wakeword_listener(self) -> None:
        """Dauerhafter Audio-Stream fuer lokale Wake-Word-Erkennung (Daemon-Thread)."""
        self.get_logger().info("Wake-Word-Listener gestartet")
        while self._ww_running:
            try:
                self._ww_stream_proc = subprocess.Popen(
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
                        "raw",
                        "-q",
                        "-",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                self._wakeword_stream_loop()
            except Exception as e:  # noqa: BLE001
                if self._ww_running:
                    self.get_logger().warn(f"Wake-Word-Stream-Fehler: {e}, Neustart in 2s")
                    time.sleep(2.0)
            finally:
                if self._ww_stream_proc is not None:
                    try:
                        self._ww_stream_proc.kill()
                        self._ww_stream_proc.wait(timeout=2.0)
                    except Exception:  # noqa: BLE001
                        pass
                    self._ww_stream_proc = None

    def _wakeword_stream_loop(self) -> None:
        """Liest Chunks aus dem arecord-Stream und fuettert openwakeword."""
        proc = self._ww_stream_proc
        if proc is None or proc.stdout is None or self._oww_model is None:
            return

        while self._ww_running and proc.poll() is None:
            # Waehrend Recording oder Processing pausieren (ALSA Device Sharing)
            if self._state in (_LISTENING, _COOLDOWN, _PROCESSING):
                time.sleep(0.1)
                continue

            chunk = proc.stdout.read(OWW_CHUNK_BYTES)
            if not chunk or len(chunk) < OWW_CHUNK_BYTES:
                break

            # Energy-Gate: RMS-Vorfilter vor Inference
            samples = struct.unpack(f"<{OWW_CHUNK_SAMPLES}h", chunk)
            rms = math.sqrt(sum(s * s for s in samples) / OWW_CHUNK_SAMPLES)
            if rms < self._energy_threshold_rms:
                continue

            # openwakeword Inference
            audio_array = np.frombuffer(chunk, dtype=np.int16)
            predictions = self._oww_model.predict(audio_array)
            for model_name, score in predictions.items():
                if score >= self._wakeword_threshold:
                    self._wakeword_detected = True
                    self._oww_model.reset()
                    self.get_logger().info(
                        f"Wake-Word erkannt: '{model_name}' (Score: {score:.2f})"
                    )
                    break

    # -----------------------------------------------------------------
    # State Machine
    # -----------------------------------------------------------------

    @property
    def _idle_state(self) -> str:
        """Gibt den korrekten Ruhezustand zurueck (WAKE_LISTENING oder IDLE)."""
        return _WAKE_LISTENING if self._use_wakeword else _IDLE

    def _tick(self) -> None:
        """State-Machine Tick (20 Hz)."""
        now = time.monotonic()

        # Barge-In-Schutz: Nicht aufnehmen waehrend TTS-Ausgabe
        if now - self._last_tts_time < self._barge_in_s:
            return

        if self._state == _WAKE_LISTENING:
            # Wake-Word-Modus: Nur auf Wake-Word-Flag reagieren
            if (
                self._wakeword_detected
                and not self._muted
                and now - self._last_stt_time >= self._rate_limit_s
            ):
                self._wakeword_detected = False
                self._start_recording()
                self._state = _LISTENING
                self.get_logger().info("WAKE_LISTENING -> LISTENING: Wake-Word erkannt")

        elif self._state == _IDLE:
            # VAD-Modus (Fallback): Warte auf VAD=True
            if (
                self._vad_active
                and not self._muted
                and now - self._last_stt_time >= self._rate_limit_s
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
            self._state = self._idle_state

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

    @staticmethod
    def _compute_rms(wav_bytes: bytes) -> float:
        """Berechnet RMS-Energie der PCM-Samples (int16, nach WAV-Header)."""
        pcm = wav_bytes[WAV_HEADER_SIZE:]
        if len(pcm) < 2:
            return 0.0
        n_samples = len(pcm) // 2
        samples = struct.unpack(f"<{n_samples}h", pcm[: n_samples * 2])
        sum_sq = sum(s * s for s in samples)
        return math.sqrt(sum_sq / n_samples)

    def _transition_to_processing(self) -> None:
        """Stoppt Aufnahme und startet Gemini-Verarbeitung."""
        wav_bytes = self._stop_recording()
        duration = time.monotonic() - self._record_start

        if duration < self._min_record_s or len(wav_bytes) < 1000:
            self.get_logger().debug(f"Aufnahme zu kurz ({duration:.1f} s) oder leer — verworfen")
            self._state = self._idle_state
            return

        # Energy-Gate: RMS unter Schwellwert → kein API-Call
        rms = self._compute_rms(wav_bytes)
        if rms < self._energy_threshold_rms:
            self.get_logger().info(
                f"Aufnahme verworfen: RMS={rms:.0f} < Schwelle {self._energy_threshold_rms:.0f}"
            )
            self._state = self._idle_state
            return

        self._pending = True
        self._state = _PROCESSING
        self.get_logger().info(
            f"Aufnahme beendet ({duration:.1f} s, RMS={rms:.0f}), transkribiere lokal..."
        )

        thread = threading.Thread(target=self._process_audio, args=(wav_bytes,), daemon=True)
        thread.start()

    def _process_audio(self, wav_bytes: bytes) -> None:
        """Transkribiert WAV lokal via Whisper, erkennt Intent per Regex."""
        try:
            # faster-whisper akzeptiert file-like objects (BinaryIO)
            audio_stream = io.BytesIO(wav_bytes)
            segments, info = self._whisper.transcribe(
                audio_stream,
                language="de",
                beam_size=3,
                vad_filter=True,
            )
            transcript = " ".join(seg.text.strip() for seg in segments).strip()
            self._last_stt_time = time.monotonic()

            if not transcript:
                self.get_logger().info("Whisper: Keine Sprache erkannt")
                return

            # Intent-Erkennung per erweitertem Regex-Parser
            command = self._parse_intent(transcript)

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

        except Exception as e:  # noqa: BLE001
            self.get_logger().error(f"Whisper-Fehler: {e}")
        finally:
            self._pending = False

    # -----------------------------------------------------------------
    # Intent-Parser (lokale Regex-basierte Befehlserkennung)
    # -----------------------------------------------------------------

    @staticmethod
    def _extract_number(text: str) -> float | None:
        """Extrahiert eine Zahl aus deutschem Text (Ziffern oder Zahlwoerter)."""
        # Dezimalzahl mit Punkt oder Komma: "1.5", "1,5"
        m = re.search(r"(\d+)[.,](\d+)", text)
        if m:
            return float(f"{m.group(1)}.{m.group(2)}")

        # Ganzzahl
        m = re.search(r"\d+", text)
        if m:
            return float(m.group())

        # Zahlwort mit "komma": "eins komma fuenf" → 1.5
        m = re.search(r"(\w+)\s+komma\s+(\w+)", text)
        if m:
            ganzzahl = _ZAHLWOERTER.get(m.group(1).lower())
            dezimal = _ZAHLWOERTER.get(m.group(2).lower())
            if ganzzahl is not None and dezimal is not None:
                # "zwei komma fuenf" → 2.5 (dezimal < 10 → Zehntel)
                if dezimal < 10:
                    return ganzzahl + dezimal / 10
                return ganzzahl + dezimal / 100

        # Einzelnes Zahlwort
        for word in text.lower().split():
            val = _ZAHLWOERTER.get(word)
            if val is not None:
                return val

        return None

    # Einfache Patterns (ohne Zahlextraktion, Prioritaet hoch → niedrig)
    _SIMPLE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"(?:halt|stopp|stop|anhalten|bleib\s+stehen|not\s*aus)"), "stop"),
        (
            re.compile(r"dreh.*zu\s+mir|schau.*(?:zu\s+mir|mich\s+an)|komm.*zu\s+mir"),
            "turn_to_speaker",
        ),
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

    # Patterns mit Zahlextraktion
    _RE_LICHT_AN = re.compile(r"licht\s+an|led\s+an|beleuchtung\s+an")
    _RE_FORWARD = re.compile(
        r"(?:fahr|fahre|geh|bewege?)\s+.*?(?:nach\s+vorne|vorwaerts|geradeaus|vor)"
        r"|(?:nach\s+vorne|vorwaerts|geradeaus)\s+.*?(?:fahr|fahre|geh)"
        r"|forward"
    )
    _RE_BACKWARD = re.compile(
        r"(?:fahr|fahre|geh|bewege?)\s+.*?(?:zurueck|rueckwaerts)"
        r"|(?:zurueck|rueckwaerts)\s+.*?(?:fahr|fahre|geh)"
        r"|backward"
    )
    _RE_TURN = re.compile(
        r"(?:dreh|drehe|turn)\s+.*?(?:grad|degree)"
        r"|(?:dreh|drehe)\s+dich"
    )
    _RE_NAV = re.compile(r"(?:navigier|fahr\s+zu|geh\s+zu|nav)\s")
    _RE_TEST = re.compile(r"(?:test|teste|starte?\s+test)\s+(\w+)")

    @classmethod
    def _parse_numeric_intent(cls, t: str) -> str:  # noqa: C901
        """Erkennt Befehle mit Zahlextraktion (forward, turn, nav, licht, test)."""
        if cls._RE_LICHT_AN.search(t):
            val = cls._extract_number(t)
            if val is not None and 0 < val <= 100:
                return f"licht an {int(val)}"
            return "licht an"

        if cls._RE_FORWARD.search(t):
            val = cls._extract_number(t)
            if val is not None and 0 < val <= 5:
                return f"forward {val:g}"
            return "forward 1"

        if cls._RE_BACKWARD.search(t):
            val = cls._extract_number(t)
            if val is not None and 0 < val <= 5:
                return f"backward {val:g}"
            return "backward 1"

        if cls._RE_TURN.search(t):
            val = cls._extract_number(t)
            if val is not None:
                if re.search(r"rechts", t):
                    val = -abs(val)
                else:
                    val = abs(val)
                return f"turn {val:g}"
            return ""

        if cls._RE_NAV.search(t):
            nums = re.findall(r"-?\d+(?:[.,]\d+)?", t)
            if len(nums) >= 2:
                x = float(nums[0].replace(",", "."))
                y = float(nums[1].replace(",", "."))
                return f"nav {x:g} {y:g}"
            return ""

        m = cls._RE_TEST.search(t)
        if m:
            name = m.group(1).lower()
            name = _TEST_ALIASES.get(name, name)
            if name in _TEST_NAMES:
                return f"test {name}"

        return ""

    @classmethod
    def _parse_intent(cls, transcript: str) -> str:
        """Erkennt Roboter-Befehl aus Transkription (primaerer Intent-Parser)."""
        t = transcript.lower().strip()

        # 1. Einfache Patterns (stop, licht aus, akku, etc.)
        for pattern, cmd in cls._SIMPLE_PATTERNS:
            if pattern.search(t):
                return cmd

        # 2. Patterns mit Zahlextraktion (forward, turn, licht an, nav, test)
        return cls._parse_numeric_intent(t)

    # -----------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------

    def destroy_node(self) -> None:
        """Bereinigung: Laufende arecord-Prozesse und Wake-Word-Stream beenden."""
        self._ww_running = False
        for proc in (self._record_proc, self._ww_stream_proc):
            if proc is not None:
                try:
                    proc.kill()
                    proc.wait(timeout=2.0)
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
