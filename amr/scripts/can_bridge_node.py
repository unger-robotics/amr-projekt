#!/usr/bin/env python3
"""CAN-Bridge: Liest SocketCAN-Frames und publiziert Diagnostik.

Empfaengt CAN-Frames von beiden ESP32-S3 Nodes (Drive: 0x200-0x2F0,
Sensor: 0x110-0x1F0) und publiziert sie als DiagnosticArray auf
/diagnostics/can. Reiner Monitoring-Kanal — kein Duplikat zu micro-ROS.
"""

import struct

import can
import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node

# CAN-ID → menschenlesbare Bezeichnung
CAN_ID_NAMES = {
    # Sensor-Node (0x110-0x1F0)
    0x110: "Sensor/Range",
    0x120: "Sensor/Cliff",
    0x130: "Sensor/IMU_Accel",
    0x131: "Sensor/IMU_Heading",
    0x140: "Sensor/Battery",
    0x141: "Sensor/BatShutdown",
    0x1F0: "Sensor/Heartbeat",
    # Drive-Node (0x200-0x2F0)
    0x200: "Drive/OdomPos",
    0x201: "Drive/OdomHeading",
    0x210: "Drive/Encoder",
    0x220: "Drive/MotorPWM",
    0x2F0: "Drive/Heartbeat",
}


class CanBridgeNode(Node):
    def __init__(self):
        super().__init__("can_bridge_node")

        try:
            self.bus = can.interface.Bus(channel="can0", interface="socketcan")
        except OSError as e:
            self.get_logger().error(f"CAN-Bus nicht verfuegbar: {e}")
            self.get_logger().error(
                "Pruefen: dtoverlay=mcp2515-can0 in config.txt, "
                "sudo ip link set can0 up type can bitrate 500000"
            )
            raise SystemExit(1) from e

        self.pub = self.create_publisher(DiagnosticArray, "/diagnostics/can", 10)
        self.create_timer(0.01, self.poll_can)  # 100 Hz polling
        self.frame_count = 0
        self.get_logger().info("CAN-Bridge gestartet (can0, 1 Mbit/s)")

    def poll_can(self):
        msg = self.bus.recv(timeout=0.001)
        if msg is None:
            return
        self.frame_count += 1

        diag = DiagnosticArray()
        diag.header.stamp = self.get_clock().now().to_msg()

        status = DiagnosticStatus()
        name = CAN_ID_NAMES.get(msg.arbitration_id, "Unknown")
        status.name = f"CAN/{name}"
        status.level = DiagnosticStatus.OK
        status.message = f"0x{msg.arbitration_id:03X} ({msg.dlc} B)"
        status.values = [
            KeyValue(key="id", value=f"0x{msg.arbitration_id:03X}"),
            KeyValue(key="data", value=msg.data[: msg.dlc].hex()),
            KeyValue(key="total_frames", value=str(self.frame_count)),
        ]

        # Heartbeat-Frames decodieren
        if msg.arbitration_id in (0x1F0, 0x2F0) and msg.dlc >= 2:
            flags = msg.data[0]
            uptime = msg.data[1]
            status.values.append(KeyValue(key="flags", value=f"0b{flags:08b}"))
            status.values.append(KeyValue(key="uptime_s_mod256", value=str(uptime)))

        # Float-Werte decodieren (Odom, Encoder, Range, IMU)
        elif msg.dlc == 8:
            val1, val2 = struct.unpack("<ff", bytes(msg.data[:8]))
            status.values.append(KeyValue(key="float1", value=f"{val1:.4f}"))
            status.values.append(KeyValue(key="float2", value=f"{val2:.4f}"))
        elif msg.dlc == 4 and msg.arbitration_id == 0x220:
            pwm_l, pwm_r = struct.unpack("<hh", bytes(msg.data[:4]))
            status.values.append(KeyValue(key="pwm_left", value=str(pwm_l)))
            status.values.append(KeyValue(key="pwm_right", value=str(pwm_r)))
        elif msg.dlc == 4 and msg.arbitration_id == 0x110:
            (range_m,) = struct.unpack("<f", bytes(msg.data[:4]))
            status.values.append(KeyValue(key="range_m", value=f"{range_m:.3f}"))

        diag.status.append(status)
        self.pub.publish(diag)


def main(args=None):
    rclpy.init(args=args)
    node = CanBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.bus.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
