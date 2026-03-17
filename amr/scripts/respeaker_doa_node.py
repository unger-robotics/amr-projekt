#!/usr/bin/env python3
"""
ReSpeaker DoA/VAD-Node fuer den AMR-Roboter.

Pollt Direction-of-Arrival (0-359 Grad) und Voice Activity Detection
vom ReSpeaker Mic Array v2.0 (XMOS XVF-3000) via USB Vendor Control
Transfers und publiziert die Werte als ROS2-Topics.

Topics:
  /sound_direction  (std_msgs/Int32)  — Azimut 0-359 Grad
  /is_voice         (std_msgs/Bool)   — Sprache erkannt (VAD)

Parameter:
  poll_rate_hz   (float, default 10.0) — Abfragerate
"""

from __future__ import annotations

import struct

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Int32

# XMOS XVF-3000 USB Register-Adressen
_DOAANGLE = 21  # Read-Only, int 0-359
_SPEECHDETECTED = 19  # Read-Only, int 0/1 — Spracherkennung (VAD)

# USB Vendor Control Transfer Parameter
_CTRL_IN = 0xC0  # Device-to-host, Vendor, Device
_CMD_READ = 0  # bRequest
_REG_BASE = 0x80  # wValue fuer Register-Zugriff
_RESP_LEN = 8  # Antwortlaenge in Bytes


class RespeakerDoaNode(Node):
    """ROS2-Node: Direction-of-Arrival und VAD vom ReSpeaker Mic Array."""

    def __init__(self) -> None:
        super().__init__("respeaker_doa_node")

        self.declare_parameter("poll_rate_hz", 10.0)
        poll_rate = self.get_parameter("poll_rate_hz").value

        self._dev = None
        self._available = False
        self._error_count = 0
        self._max_errors = 10

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
            # USB-Reset: XVF-3000 kann in fehlerhaftem Zustand sein
            try:
                dev.reset()
                import time  # noqa: PLC0415

                time.sleep(1.5)
                dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
                if dev is None:
                    self.get_logger().warning("ReSpeaker nach USB-Reset nicht mehr gefunden")
                    return
                self.get_logger().info("USB-Reset erfolgreich")
            except Exception as e:  # noqa: BLE001
                self.get_logger().warning(f"USB-Reset fehlgeschlagen (nicht fatal): {e}")
            # Kernel-Audio-Treiber detachen (snd-usb-audio beansprucht Interfaces)
            for iface in range(5):
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

        period = 1.0 / float(poll_rate)
        self._timer = self.create_timer(period, self._poll_callback)

        self.get_logger().info(f"ReSpeaker DoA/VAD-Node gestartet ({poll_rate} Hz)")

    def _read_register(self, reg_id: int) -> int:
        """Liest ein XMOS-DSP-Register via USB Vendor Control Transfer."""
        result = self._dev.ctrl_transfer(  # type: ignore[union-attr]
            _CTRL_IN, _CMD_READ, _REG_BASE, reg_id, _RESP_LEN
        )
        return struct.unpack("<i", bytes(result[:4]))[0]

    def _poll_callback(self) -> None:
        """Timer-Callback: DoA und VAD lesen und publizieren."""
        if not self._available:
            return

        try:
            angle = self._read_register(_DOAANGLE)
            voice = self._read_register(_SPEECHDETECTED)

            self._pub_direction.publish(Int32(data=angle))
            self._pub_voice.publish(Bool(data=bool(voice)))

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
