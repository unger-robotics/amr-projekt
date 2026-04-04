#!/usr/bin/env python3
"""ROS2-Node: Sprachsteuerung via ReSpeaker + Gemini Audio-STT / Whisper.

Audio-Architektur: Ein einziger arecord-Prozess liest den ReSpeaker-Stream.
- Wake-Word-Modus (stumm): openwakeword erkennt Aktivierungswort, dann Aufnahme
- VAD-Modus (Mikrofon an): Software-VAD via RMS-Energie erkennt Sprache
Gepufferte PCM-Chunks werden als WAV transkribiert. Kein zweiter arecord noetig.

STT-Engines:
- Gemini Audio-STT (use_gemini_stt=True): Audio → Gemini Cloud → Transkript + Intent
  in einem API-Call. Genauer bei Deutsch, erfordert GEMINI_API_KEY.
- Whisper (Fallback): Lokales faster-whisper → Transkript, dann Regex + Gemini-Text-Intent.

Subscriptions:
  /voice/mute     (std_msgs/Bool)   — Mikrofon-Toggle vom Dashboard

Publications:
  /voice/command  (std_msgs/String) — Strukturierter Befehl (Freitext fuer _handle_command)
  /voice/text     (std_msgs/String) — Rohtranskription (fuer Dashboard/Logging)

Parameter:
  audio_device   (string, "auto")           — ALSA-Device (auto = ReSpeaker erkennen)
  whisper_model  (string, "base")           — Whisper-Modellgroesse (tiny/base/small)
  use_gemini_stt (bool, True)              — Gemini Audio-STT (Cloud, GEMINI_API_KEY)
  max_record_s   (float, 10.0)              — Max. Aufnahmedauer [s]
  min_record_s   (float, 0.5)               — Min. Aufnahmedauer [s]
  cooldown_s     (float, 0.5)               — VAD-Cooldown nach Sprachende [s]
  rate_limit_s   (float, 2.0)               — Min. Zeit zwischen STT-Verarbeitungen [s]
  barge_in_s     (float, 2.0)               — Aufnahme-Sperre nach eigenem TTS [s]
  dedup_s        (float, 5.0)               — Deduplizierung: gleicher Befehl innerhalb [s] unterdrueckt
  confirm_tts    (bool, True)               — TTS-Bestaetigung nach Befehl
  min_vad_s      (float, 0.3)              — Min. kontinuierliche VAD-Dauer vor Aufnahme [s]
  energy_threshold_rms (float, 80.0)      — RMS-Schwelle: Aufnahmen unter Schwelle verwerfen
  use_wakeword   (bool, True)             — Lokale Wake-Word-Erkennung (openwakeword)
  wakeword_model (string, "hey_jarvis_v0.1") — openwakeword-Modellname
  wakeword_threshold (float, 0.3)         — Wake-Word-Erkennungsschwelle (0.0-1.0)

Verwendung:
  ros2 run my_bot voice_command_node
  ros2 run my_bot voice_command_node --ros-args -p use_gemini_stt:=false -p whisper_model:=small
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import os
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

try:
    from google import genai
    from google.genai import types as genai_types

    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# State-Konstanten
_IDLE = "idle"
_WAKE_LISTENING = "wake_listening"
_PROCESSING = "processing"

# Rate-Limiting
MIN_REQUEST_INTERVAL_S = 2.0
WAV_HEADER_SIZE = 44  # Standard-WAV-Header-Laenge in Bytes
OWW_CHUNK_SAMPLES = 1280  # 80 ms bei 16 kHz (openwakeword erwartet 80ms-Chunks)
OWW_CHUNK_BYTES = OWW_CHUNK_SAMPLES * 2  # int16 = 2 Bytes/Sample

# Gemini-Fallback Intent-Prompt (nur verwendet wenn Regex keinen Intent erkennt)
VOICE_INTENT_PROMPT = (
    "Du bist der Sprachassistent eines autonomen mobilen Roboters (AMR).\n"
    "Der Benutzer hat folgenden Sprachbefehl gegeben:\n"
    '"{transcript}"\n'
    "\n"
    "Erkenne den Intent und antworte NUR mit dem passenden Befehlsstring.\n"
    "Verfuegbare Befehle:\n"
    "\n"
    "stop                     — Sofortstopp\n"
    "forward <meter>          — Vorwaerts fahren (0.1-5.0 m, Default 1)\n"
    "backward <meter>         — Rueckwaerts fahren (0.1-5.0 m, Default 1)\n"
    "turn <grad>              — Drehen (positiv=links, negativ=rechts)\n"
    "turn_to_speaker          — Zum Sprecher drehen\n"
    "nav <x> <y>              — Navigation zu Koordinaten\n"
    "schau nach links         — Kamera nach links\n"
    "schau nach rechts        — Kamera nach rechts\n"
    "schau nach vorne         — Kamera geradeaus\n"
    "licht an                 — LED an (80%)\n"
    "licht an <0-100>         — LED mit Helligkeit\n"
    "licht aus                — LED aus\n"
    "wie weit                 — Ultraschall-Distanz abfragen\n"
    "akku                     — Batteriestatus abfragen\n"
    "wo bin ich               — Position abfragen\n"
    "wetter                   — Wetter abfragen\n"
    "help                     — Hilfe anzeigen\n"
    "test <name>              — Test starten (rplidar|imu|motor|encoder|sensor|\n"
    "                           kinematic|straight_drive|rotation|cliff_latency|\n"
    "                           slam|nav|nav_square|docking|dashboard_latency|can)\n"
    "was siehst du            — Vision-Analyse anfordern\n"
    "beschreibe umgebung      — Umgebungsbeschreibung\n"
    "\n"
    'Wenn der Befehl zu keinem Intent passt: antworte mit leerem String "".\n'
    "Antworte NUR mit dem Befehlsstring, KEINE Erklaerung."
)

# Gemini Audio-STT Prompt (Audio beigefuegt → Transkript + Intent in einem Call)
_VOICE_COMMANDS_BLOCK = (
    "stop                     — Sofortstopp\n"
    "forward <meter>          — Vorwaerts fahren (0.1-5.0 m, Default 1)\n"
    "backward <meter>         — Rueckwaerts fahren (0.1-5.0 m, Default 1)\n"
    "turn <grad>              — Drehen (positiv=links, negativ=rechts)\n"
    "turn_to_speaker          — Zum Sprecher drehen\n"
    "nav <x> <y>              — Navigation zu Koordinaten\n"
    "schau nach links         — Kamera nach links\n"
    "schau nach rechts        — Kamera nach rechts\n"
    "schau nach vorne         — Kamera geradeaus\n"
    "licht an                 — LED an (80%)\n"
    "licht an <0-100>         — LED mit Helligkeit\n"
    "licht aus                — LED aus\n"
    "wie weit                 — Ultraschall-Distanz abfragen\n"
    "akku                     — Batteriestatus abfragen\n"
    "wo bin ich               — Position abfragen\n"
    "wetter                   — Wetter abfragen\n"
    "help                     — Hilfe anzeigen\n"
    "test <name>              — Test starten (rplidar|imu|motor|encoder|sensor|\n"
    "                           kinematic|straight_drive|rotation|cliff_latency|\n"
    "                           slam|nav|nav_square|docking|dashboard_latency|can)\n"
    "was siehst du            — Vision-Analyse anfordern\n"
    "beschreibe umgebung      — Umgebungsbeschreibung\n"
)

VOICE_AUDIO_PROMPT = (
    "Du bist der Sprachassistent eines autonomen mobilen Roboters (AMR).\n"
    "Der Benutzer hat einen Sprachbefehl gesprochen (Audio beigefuegt).\n"
    "\n"
    "1. Transkribiere die Sprache wortwoertlich auf Deutsch.\n"
    "2. Erkenne den Intent und gib den passenden Befehlsstring zurueck.\n"
    "\n"
    "Verfuegbare Befehle:\n\n" + _VOICE_COMMANDS_BLOCK + "\n"
    'Wenn kein Intent erkannt wird: command = ""\n'
    "\n"
    'Antworte NUR mit JSON: {"transcript": "...", "command": "..."}\n'
    "Keine Erklaerung, kein Markdown."
)

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
        self.declare_parameter("cooldown_s", 0.8)
        self.declare_parameter("rate_limit_s", 2.0)
        self.declare_parameter("barge_in_s", 2.0)
        self.declare_parameter("dedup_s", 5.0)
        self.declare_parameter("confirm_tts", True)
        self.declare_parameter("min_vad_s", 0.3)
        self.declare_parameter("energy_threshold_rms", 80.0)
        self.declare_parameter("use_gemini_stt", True)
        self.declare_parameter("use_wakeword", True)
        self.declare_parameter("wakeword_model", "hey_jarvis_v0.1")
        self.declare_parameter("wakeword_threshold", 0.3)

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
        self._use_gemini_stt = self.get_parameter("use_gemini_stt").value
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

        # -- Gemini-Fallback fuer Intent-Erkennung (optional, Cloud) --
        self._gemini_client = None
        self._gemini_model: str | None = None
        if HAS_GENAI:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self._gemini_client = genai.Client(api_key=api_key)
                self._gemini_model = (
                    os.environ.get("GEMINI_VOICE_MODEL")
                    or os.environ.get("GEMINI_MODEL")
                    or "gemini-2.5-flash"
                )
                self.get_logger().info(f"Gemini Voice-Fallback aktiv: {self._gemini_model}")
            else:
                self.get_logger().info("GEMINI_API_KEY nicht gesetzt — Voice bleibt Regex-only")
        else:
            self.get_logger().info("google-genai nicht installiert — Voice Regex-only")

        # Gemini-STT-Verfuegbarkeit pruefen
        if self._use_gemini_stt:
            if self._gemini_client:
                self.get_logger().info(
                    f"Gemini Audio-STT aktiv: {self._gemini_model} (Whisper als Fallback)"
                )
            else:
                self.get_logger().warn("use_gemini_stt=True aber kein GEMINI_API_KEY — nur Whisper")
                self._use_gemini_stt = False

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
        self.create_subscription(Bool, "/voice/mute", self._mute_cb, 10)

        # -- State Machine --
        self._muted = True  # Default: Mikrofon aus (Dashboard-Toggle aktiviert VAD-Modus)
        self._last_stt_time = 0.0
        self._last_tts_time = 0.0
        self._last_command = ""
        self._last_command_time = 0.0
        self._pending = False

        # -- Wake-Word-Erkennung (openwakeword, optional) --
        self._oww_model = None  # Optional[OwwModel] — nur wenn HAS_OWW
        self._stream_proc: subprocess.Popen | None = None
        self._stream_running = False

        # Startzustand VOR Thread-Start setzen (Race Condition vermeiden)
        self._state = _WAKE_LISTENING if self._use_wakeword else _IDLE

        if self._use_wakeword and HAS_OWW:
            try:
                self._oww_model = OwwModel(
                    wakeword_models=[self._wakeword_model],
                    inference_framework="onnx",
                )
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

        # Audio-Stream-Thread immer starten (fuer Wake-Word UND VAD-Modus)
        self._stream_running = True
        self._stream_thread = threading.Thread(target=self._audio_stream_listener, daemon=True)
        self._stream_thread.start()

        # Timer: 20 Hz State-Machine Tick (nur PROCESSING → idle)
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
    # Mute Callback
    # -----------------------------------------------------------------

    def _mute_cb(self, msg: Bool) -> None:
        """Mute-Callback: Mikrofon stumm schalten / aktivieren.

        Mikrofon an  (muted=False) → VAD-Modus: Software-VAD via RMS-Energie
        Mikrofon aus (muted=True)  → Wake-Word-Modus (openwakeword)
        """
        self._muted = msg.data
        if msg.data:
            self._state = self._idle_state
            self.get_logger().info("Mikrofon stumm — Wake-Word-Modus")
        else:
            self._state = _IDLE
            self.get_logger().info("Mikrofon aktiv — VAD-Modus (kein Wake-Word)")

    # -----------------------------------------------------------------
    # Audio-Stream (Wake-Word + Software-VAD, ein arecord-Prozess)
    # -----------------------------------------------------------------

    def _audio_stream_listener(self) -> None:
        """Dauerhafter Audio-Stream fuer Wake-Word und VAD (Daemon-Thread)."""
        self.get_logger().info("Audio-Stream-Listener gestartet")
        while self._stream_running:
            try:
                self._stream_proc = subprocess.Popen(
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
                    stderr=subprocess.PIPE,
                )
                self._audio_stream_loop()
                # Stream-Loop beendet — arecord-Exitcode und stderr pruefen
                if self._stream_proc is not None:
                    rc = self._stream_proc.poll()
                    stderr_out = b""
                    if self._stream_proc.stderr:
                        with contextlib.suppress(Exception):
                            stderr_out = self._stream_proc.stderr.read(512) or b""
                    if rc is not None and rc != 0 and self._stream_running:
                        self.get_logger().warn(
                            f"arecord beendet (rc={rc}): "
                            f"{stderr_out.decode(errors='replace').strip()[:200]}"
                        )
            except Exception as e:  # noqa: BLE001
                if self._stream_running:
                    self.get_logger().warn(f"Audio-Stream-Fehler: {e}, Neustart in 2s")
                    time.sleep(2.0)
            finally:
                if self._stream_proc is not None:
                    try:
                        self._stream_proc.kill()
                        self._stream_proc.wait(timeout=2.0)
                    except Exception:  # noqa: BLE001
                        pass
                    self._stream_proc = None

    def _audio_stream_loop(self) -> None:  # noqa: C901
        """Unified audio loop: Wake-Word (stumm) + Software-VAD (aktiv).

        Ein einziger arecord-Stream fuer beide Modi. Im Wake-Word-Modus wird
        openwakeword gefuettert; im VAD-Modus erkennt RMS-Energie Sprache.
        Erkannte Sprache wird als PCM gepuffert, als WAV gebaut und an
        Whisper uebergeben.
        """
        proc = self._stream_proc
        if proc is None or proc.stdout is None:
            return

        chunk_count = 0
        max_rms_seen = 0.0
        max_score_seen = 0.0
        last_diag_time = time.monotonic()

        # Buffering-State
        audio_buffer: list[bytes] = []
        buffering = False
        buffer_start = 0.0
        last_energy_time = 0.0
        energy_active = False
        energy_active_start = 0.0
        prev_muted = self._muted

        # Pre-Buffer: letzte ~0.5s Audio vor VAD-Trigger mitpuffern,
        # damit der Wortanfang nicht verloren geht
        pre_buffer_max = 8  # 8 * 80ms = 640ms
        pre_buffer: list[bytes] = []

        # VAD-Trigger: halbe Schwelle fuer sensitivere Sprach-Erkennung
        vad_trigger_rms = self._energy_threshold_rms * 0.5

        while self._stream_running and proc.poll() is None:
            # Waehrend Processing pausieren (Audio-Buffer verwerfen)
            if self._pending:
                buffering = False
                audio_buffer.clear()
                pre_buffer.clear()
                energy_active = False
                time.sleep(0.1)
                continue

            chunk = proc.stdout.read(OWW_CHUNK_BYTES)
            if not chunk or len(chunk) < OWW_CHUNK_BYTES:
                break

            chunk_count += 1
            now = time.monotonic()

            # RMS berechnen
            samples = struct.unpack(f"<{OWW_CHUNK_SAMPLES}h", chunk)
            rms = math.sqrt(sum(s * s for s in samples) / OWW_CHUNK_SAMPLES)
            if rms > max_rms_seen:
                max_rms_seen = rms

            # Barge-In-Schutz: Audio nach TTS verwerfen
            if now - self._last_tts_time < self._barge_in_s:
                buffering = False
                audio_buffer.clear()
                energy_active = False
                continue

            # Mode-Switch erkennen: Buffer verwerfen
            if self._muted != prev_muted:
                buffering = False
                audio_buffer.clear()
                pre_buffer.clear()
                energy_active = False
                prev_muted = self._muted
                if self._oww_model is not None:
                    self._oww_model.reset()

            # Pre-Buffer fuellen (rollierendes Fenster, immer aktiv)
            if not buffering:
                pre_buffer.append(chunk)
                if len(pre_buffer) > pre_buffer_max:
                    pre_buffer.pop(0)

            if self._muted:
                # === WAKE-WORD-MODUS ===
                if not buffering:
                    if self._oww_model is not None:
                        audio_array = np.frombuffer(chunk, dtype=np.int16)
                        predictions = self._oww_model.predict(audio_array)
                        for model_name, score in predictions.items():
                            if score > max_score_seen:
                                max_score_seen = score
                            if score >= self._wakeword_threshold:
                                # Wake-Word erkannt → Pre-Buffer + Puffern
                                if now - self._last_stt_time >= self._rate_limit_s:
                                    buffering = True
                                    buffer_start = now - len(pre_buffer) * 0.08
                                    audio_buffer = list(pre_buffer)
                                    pre_buffer.clear()
                                    last_energy_time = now
                                self._oww_model.reset()
                                self.get_logger().info(
                                    f"Wake-Word erkannt: '{model_name}' (Score: {score:.2f})"
                                )
                                break
                else:
                    # Puffern nach Wake-Word bis Stille eintritt
                    audio_buffer.append(chunk)
                    if rms >= vad_trigger_rms:
                        last_energy_time = now
                    elapsed = now - buffer_start
                    silence_dur = now - last_energy_time
                    if (
                        silence_dur >= self._cooldown_s and elapsed >= self._min_record_s
                    ) or elapsed >= self._max_record_s:
                        self._submit_buffered_audio(audio_buffer, elapsed)
                        audio_buffer = []
                        buffering = False
            else:
                # === VAD-MODUS (Mikrofon aktiv, Software-Energie-VAD) ===
                was_active = energy_active
                energy_active = rms >= vad_trigger_rms
                if energy_active and not was_active:
                    energy_active_start = now
                if energy_active:
                    last_energy_time = now

                if not buffering:
                    # Warten auf anhaltende Energie ueber Schwelle
                    if (
                        energy_active
                        and now - energy_active_start >= self._min_vad_s
                        and now - self._last_stt_time >= self._rate_limit_s
                    ):
                        buffering = True
                        # Pre-Buffer einbeziehen (Wortanfang retten)
                        buffer_start = now - len(pre_buffer) * 0.08
                        audio_buffer = list(pre_buffer)
                        pre_buffer.clear()
                        self.get_logger().info(
                            f"VAD: Sprache erkannt (RMS={rms:.0f}), nehme auf..."
                        )
                else:
                    audio_buffer.append(chunk)
                    elapsed = now - buffer_start
                    silence_dur = now - last_energy_time
                    if (
                        silence_dur >= self._cooldown_s and elapsed >= self._min_record_s
                    ) or elapsed >= self._max_record_s:
                        self._submit_buffered_audio(audio_buffer, elapsed)
                        audio_buffer = []
                        buffering = False

            # Periodische Diagnose (alle 30s)
            if now - last_diag_time >= 30.0:
                mode = "Wake-Word" if self._muted else "VAD"
                self.get_logger().info(
                    f"{mode}-Diag: {chunk_count} Chunks, "
                    f"max_RMS={max_rms_seen:.0f}, "
                    f"max_Score={max_score_seen:.3f} "
                    f"(WW-Schwelle={self._wakeword_threshold}, "
                    f"VAD-Schwelle={vad_trigger_rms:.0f})"
                )
                chunk_count = 0
                max_rms_seen = 0.0
                max_score_seen = 0.0
                last_diag_time = now

    # -----------------------------------------------------------------
    # Audio-Buffer → WAV → Whisper
    # -----------------------------------------------------------------

    @staticmethod
    def _build_wav(chunks: list[bytes]) -> bytes:
        """Erzeugt WAV-Bytes (16 kHz, mono, int16) aus rohen PCM-Chunks."""
        pcm_data = b"".join(chunks)
        data_size = len(pcm_data)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,  # fmt chunk size
            1,  # PCM format
            1,  # mono
            16000,  # sample rate
            32000,  # byte rate (16000 * 1 * 2)
            2,  # block align (1 * 2)
            16,  # bits per sample
            b"data",
            data_size,
        )
        return header + pcm_data

    def _submit_buffered_audio(self, chunks: list[bytes], duration: float) -> None:
        """Erstellt WAV aus gepufferten Chunks und startet Whisper-Verarbeitung."""
        if not chunks:
            return
        wav_bytes = self._build_wav(chunks)
        rms = self._compute_rms(wav_bytes)
        if rms < self._energy_threshold_rms:
            self.get_logger().info(
                f"Aufnahme verworfen: RMS={rms:.0f} < Schwelle {self._energy_threshold_rms:.0f}"
            )
            return
        self._pending = True
        self._state = _PROCESSING
        self.get_logger().info(
            f"Aufnahme beendet ({duration:.1f} s, RMS={rms:.0f}), transkribiere lokal..."
        )
        thread = threading.Thread(target=self._process_audio, args=(wav_bytes,), daemon=True)
        thread.start()

    # -----------------------------------------------------------------
    # State Machine
    # -----------------------------------------------------------------

    @property
    def _idle_state(self) -> str:
        """Gibt den korrekten Ruhezustand zurueck (WAKE_LISTENING oder IDLE)."""
        if self._use_wakeword and self._muted:
            return _WAKE_LISTENING
        return _IDLE

    def _tick(self) -> None:
        """State-Machine Tick (20 Hz): PROCESSING → idle Transition."""
        if self._state == _PROCESSING and not self._pending:
            self._state = self._idle_state

    # -----------------------------------------------------------------
    # Whisper-Verarbeitung
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

    def _process_audio(self, wav_bytes: bytes) -> None:
        """Transkribiert WAV via Gemini Audio-STT oder Whisper, erkennt Intent."""
        try:
            transcript = ""
            command = ""

            # 1. Gemini Audio-STT (Cloud: Audio → Transkript + Intent in einem Call)
            if self._use_gemini_stt and self._gemini_client:
                result = self._gemini_audio_stt(wav_bytes)
                if result:
                    transcript, command = result

            # 2. Whisper-Fallback (lokal, offline)
            if not transcript:
                audio_stream = io.BytesIO(wav_bytes)
                segments, _info = self._whisper.transcribe(
                    audio_stream,
                    language="de",
                    beam_size=3,
                    vad_filter=True,
                )
                transcript = " ".join(seg.text.strip() for seg in segments).strip()
                self._last_stt_time = time.monotonic()

                if not transcript:
                    self.get_logger().info("STT: Keine Sprache erkannt")
                    return

                # Intent-Erkennung: Regex primaer, Gemini-Text als Fallback
                command = self._parse_intent(transcript)
                if not command and self._gemini_client:
                    command = self._gemini_parse_intent(transcript)

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
            self.get_logger().error(f"STT-Fehler: {e}")
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

    def _gemini_parse_intent(self, transcript: str) -> str:
        """Fallback-Intent-Parser via Gemini (Cloud, ~200 ms Latenz)."""
        if not self._gemini_client:
            return ""
        try:
            prompt = VOICE_INTENT_PROMPT.format(transcript=transcript)
            response = self._gemini_client.models.generate_content(
                model=self._gemini_model,
                contents=[prompt],
                config=genai_types.GenerateContentConfig(
                    max_output_tokens=50,
                    temperature=0.0,
                ),
            )
            if response and response.text:
                result = response.text.strip().strip('"').strip("'")
                if result:
                    self.get_logger().info(f"Gemini-Intent: '{result}' (aus: '{transcript}')")
                return result
            return ""
        except Exception as e:
            self.get_logger().warn(f"Gemini-Voice-Fehler: {e}")
            return ""

    def _gemini_audio_stt(self, wav_bytes: bytes) -> tuple[str, str] | None:
        """Gemini Audio-STT: WAV → Transkript + Intent in einem API-Call.

        Sendet Audio als Inline-Daten an Gemini, erhaelt JSON mit
        transcript und command. Latenz ~500-1500 ms je nach Audiolaenge.
        """
        if not self._gemini_client:
            return None

        # Mindest-Audiolaenge: 0.5 s bei 16 kHz mono int16 = 16000 Bytes PCM
        pcm_length = len(wav_bytes) - WAV_HEADER_SIZE
        if pcm_length < 16000:
            self.get_logger().info(
                f"Gemini-STT: Audio zu kurz ({pcm_length / 32000:.1f} s), ueberspringe"
            )
            return None

        try:
            response = self._gemini_client.models.generate_content(
                model=self._gemini_model,
                contents=[
                    genai_types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                    VOICE_AUDIO_PROMPT,
                ],
                config=genai_types.GenerateContentConfig(
                    max_output_tokens=200,
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            if not response or not response.text or not response.text.strip():
                self.get_logger().info("Gemini-STT: Leere API-Antwort")
                return None

            text = response.text.strip()
            # Markdown-Fences entfernen (Gemini antwortet manchmal mit ```json)
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)
                text = text.strip()

            if not text:
                self.get_logger().info("Gemini-STT: Leerer Text nach Markdown-Cleaning")
                return None

            data = json.loads(text)
            transcript = data.get("transcript", "").strip()
            command = data.get("command", "").strip()

            if transcript:
                self._last_stt_time = time.monotonic()
                self.get_logger().info(f"Gemini-STT: '{transcript}' → Befehl: '{command}'")
                return (transcript, command)
            return None

        except json.JSONDecodeError as e:
            self.get_logger().warn(f"Gemini-STT JSON-Fehler: {e}")
            return None
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn(f"Gemini-STT-Fehler: {e}")
            return None

    # -----------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------

    def destroy_node(self) -> None:
        """Bereinigung: Audio-Stream beenden."""
        self._stream_running = False
        if self._stream_proc is not None:
            try:
                self._stream_proc.kill()
                self._stream_proc.wait(timeout=2.0)
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
