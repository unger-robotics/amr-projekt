#!/usr/bin/env python3
"""
ReSpeaker DoA/VAD-Node fuer den AMR-Roboter.

Pollt Direction-of-Arrival (0-359 Grad) und Voice Activity Detection
vom ReSpeaker Mic Array v2.0 (XMOS XVF-3000) via USB Vendor Control
Transfers und publiziert die Werte als ROS2-Topics.

Topics:
  /sound_direction  (std_msgs/Int32)   — Azimut 0-359 Grad (roh, offset-korrigiert)
  /is_voice         (std_msgs/Bool)    — Sprache erkannt (VAD)
  /doa/filtered     (std_msgs/Int32)   — Median-gefilterter DoA (nur bei VAD)
  /doa/quadrant     (std_msgs/String)  — Quadrant: vorne/hinten/links/rechts

Parameter:
  poll_rate_hz      (float, default 10.0) — Abfragerate
  doa_offset_deg    (int,   default 0)    — Montage-Offset-Korrektur (Grad)
  doa_filter_size   (int,   default 7)    — Median-Fenstergroesse (Samples)
"""

from __future__ import annotations

import math
import struct
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Int32, String

# XMOS XVF-3000 USB Register-Adressen
_DOAANGLE = 21  # Read-Only, int 0-359
_SPEECHDETECTED = 19  # Read-Only, int 0/1 — Spracherkennung (VAD)

# USB Vendor Control Transfer Parameter
_CTRL_IN = 0xC0  # Device-to-host, Vendor, Device
_CMD_READ = 0  # bRequest
_REG_BASE = 0x80  # wValue fuer Register-Zugriff
_RESP_LEN = 8  # Antwortlaenge in Bytes

# Quadrant-Sektoren (Mitte, Name) — 0=vorne, 90=links, 180=hinten, 270=rechts
_QUADRANTS = [(0, "vorne"), (90, "links"), (180, "hinten"), (270, "rechts")]
_QUADRANT_HALF = 45  # Halbe Sektorbreite
_HYSTERESIS = 15  # Grad Hysterese an Sektorgrenzen
_MIN_FILTER_SAMPLES = 3  # Mindest-Samples fuer Median


class RespeakerDoaNode(Node):
    """ROS2-Node: Direction-of-Arrival und VAD vom ReSpeaker Mic Array."""

    def __init__(self) -> None:
        super().__init__("respeaker_doa_node")

        self.declare_parameter("poll_rate_hz", 10.0)
        self.declare_parameter("doa_offset_deg", 0)
        self.declare_parameter("doa_filter_size", 7)
        poll_rate = self.get_parameter("poll_rate_hz").value
        self._offset = int(self.get_parameter("doa_offset_deg").value)
        filter_size = int(self.get_parameter("doa_filter_size").value)

        self._dev = None
        self._available = False
        self._error_count = 0
        self._max_errors = 10

        # DoA-Filter-State
        self._doa_buffer: deque[int] = deque(maxlen=max(filter_size, 3))
        self._filtered_doa: int = 0
        self._quadrant: str = ""
        self._prev_vad: bool = False

        try:
            import usb.core  # noqa: PLC0415
            import usb.util  # noqa: PLC0415

            self._usb_core = usb.core
            self._usb_util = usb.util
            dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
            if dev is None:
                self.get_logger().warning(
                    "ReSpeaker Mic Array nicht gefunden — DoA/VAD deaktiviert"
                )
                return
            # Nur HID/Vendor-Interfaces (3, 4) detachen — Audio-Interfaces
            # (0-2) muessen fuer snd_usb_audio / arecord erhalten bleiben
            for iface in (3, 4):
                try:
                    if dev.is_kernel_driver_active(iface):
                        dev.detach_kernel_driver(iface)
                except Exception:  # noqa: BLE001
                    pass
            self._dev = dev
            self._available = True
        except ImportError:
            self.get_logger().error("pyusb nicht installiert — pip3 install pyusb")
            return

        self._pub_direction = self.create_publisher(Int32, "/sound_direction", 10)
        self._pub_voice = self.create_publisher(Bool, "/is_voice", 10)
        self._pub_doa_filtered = self.create_publisher(Int32, "/doa/filtered", 10)
        self._pub_doa_quadrant = self.create_publisher(String, "/doa/quadrant", 10)

        period = 1.0 / float(poll_rate)
        self._timer = self.create_timer(period, self._poll_callback)

        self.get_logger().info(
            f"ReSpeaker DoA/VAD-Node gestartet ({poll_rate} Hz, "
            f"Offset {self._offset}°, Filter {filter_size})"
        )

    @staticmethod
    def _circular_median(angles: list[int]) -> int:
        """Berechnet den zirkulaeren Median (beruecksichtigt 0/360-Wraparound)."""
        if not angles:
            return 0
        rads = [a * math.pi / 180.0 for a in angles]
        # Zirkulaerer Mittelwert als Referenzpunkt
        sin_sum = sum(math.sin(r) for r in rads)
        cos_sum = sum(math.cos(r) for r in rads)
        ref = math.atan2(sin_sum, cos_sum)
        # Winkel relativ zum Referenzpunkt unwrappen
        unwrapped = []
        for r in rads:
            diff = r - ref
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            unwrapped.append(ref + diff)
        unwrapped.sort()
        median_rad = unwrapped[len(unwrapped) // 2]
        return int(round(math.degrees(median_rad))) % 360

    def _classify_quadrant(self, deg: int) -> str:
        """Klassifiziert gefilterten DoA in Quadrant mit Hysterese."""
        for center, name in _QUADRANTS:
            # Zirkulaere Differenz zum Sektorzentrum
            diff = abs(((deg - center + 180) % 360) - 180)
            if diff <= _QUADRANT_HALF - _HYSTERESIS:
                return name
        # Innerhalb Hysterese-Band: vorherigen Quadrant beibehalten
        return self._quadrant if self._quadrant else "vorne"

    def _read_register(self, reg_id: int) -> int:
        """Liest ein XMOS-DSP-Register via USB Vendor Control Transfer."""
        result = self._dev.ctrl_transfer(  # type: ignore[union-attr]
            _CTRL_IN, _CMD_READ, _REG_BASE, reg_id, _RESP_LEN
        )
        return struct.unpack("<i", bytes(result[:4]))[0]

    def _poll_callback(self) -> None:
        """Timer-Callback: DoA und VAD lesen, filtern und publizieren."""
        if not self._available:
            return

        try:
            raw_angle = self._read_register(_DOAANGLE)
            voice = self._read_register(_SPEECHDETECTED)

            # Offset-Korrektur
            angle = (raw_angle + self._offset) % 360
            is_voice = bool(voice)

            # Roh-Werte immer publizieren
            self._pub_direction.publish(Int32(data=angle))
            self._pub_voice.publish(Bool(data=is_voice))

            # DoA-Filter nur bei aktiver Sprache
            if is_voice:
                if not self._prev_vad:
                    # VAD-Flanke false→true: Buffer leeren (neue Aeusserung)
                    self._doa_buffer.clear()
                self._doa_buffer.append(angle)

                if len(self._doa_buffer) >= _MIN_FILTER_SAMPLES:
                    filtered = self._circular_median(list(self._doa_buffer))
                    quadrant = self._classify_quadrant(filtered)
                    self._filtered_doa = filtered
                    self._quadrant = quadrant
                    self._pub_doa_filtered.publish(Int32(data=filtered))
                    self._pub_doa_quadrant.publish(String(data=quadrant))

            self._prev_vad = is_voice
            self._error_count = 0

        except Exception as e:  # noqa: BLE001
            self._error_count += 1
            if self._error_count <= 3:
                self.get_logger().warning(f"USB-Lesefehler ({self._error_count}): {e}")
            if self._error_count >= self._max_errors:
                self.get_logger().error(
                    f"{self._max_errors} konsekutive USB-Fehler — DoA deaktiviert"
                )
                self._available = False

    def destroy_node(self) -> None:
        """Bereinigung: USB-Ressourcen freigeben."""
        if self._dev is not None:
            try:
                import usb.util  # noqa: PLC0415

                usb.util.dispose_resources(self._dev)
            except Exception:  # noqa: BLE001
                pass
        super().destroy_node()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = RespeakerDoaNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
