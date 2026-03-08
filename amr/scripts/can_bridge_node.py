#!/usr/bin/env python3
"""CAN-to-ROS2 Bridge: Empfaengt SocketCAN-Frames und publiziert Sensor-Topics.

Ersetzt die micro-ROS Publisher des Sensor-Nodes durch CAN-basierte
Publikation. Vorteile gegenueber micro-ROS Serial:
- Kein XRCE-DDS Overhead (Fragmentierung, ACK)
- Separater physischer Kanal (1 Mbit/s CAN vs. 921600 Baud Serial)
- 8-Byte CAN-Frames statt 200+ Byte Imu-Nachrichten
- Sensor micro-ROS Agent traegt nur noch Subscriber-Last

CAN-ID Layout (Sensor-Node 0x110-0x1F0):
  0x110: Range [float32 m]                     10 Hz
  0x120: Cliff [uint8]                          20 Hz
  0x130: IMU Accel ax,ay,az + GyroZ [4x int16]  50 Hz
  0x131: IMU Heading [float32 rad]              50 Hz
  0x140: Battery V/I/P [uint16+int16+uint16]     2 Hz
  0x141: Battery Shutdown [uint8]               Event
  0x1F0: Heartbeat [uint8+uint8]                 1 Hz

CAN-ID Layout (Drive-Node 0x200-0x2F0, wenn CAN angeschlossen):
  0x200: Odom Position x,y [2x float32]         20 Hz
  0x201: Odom Heading+Speed [2x float32]        20 Hz
  0x2F0: Heartbeat [uint8+uint8]                 1 Hz

Blocking-Architektur: Eigener Thread liest CAN via select() (kein Polling,
<1% CPU). Frames werden in einer Queue zwischengespeichert und per ROS2-Timer
in den Executor-Thread dispatcht (thread-safe).
"""

import contextlib
import math
import queue
import select
import socket
import struct
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import BatteryState, Imu, Range
from std_msgs.msg import Bool

# SocketCAN Frame-Format: CAN-ID (4B) + DLC (1B) + Padding (3B) + Data (8B)
CAN_FRAME_FMT = "=IB3x8s"
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)

# CAN-IDs (muss mit config_sensors.h / config_drive.h uebereinstimmen)
ID_RANGE = 0x110
ID_CLIFF = 0x120
ID_IMU_ACCEL = 0x130
ID_IMU_HEADING = 0x131
ID_BATTERY = 0x140
ID_BAT_SHUTDOWN = 0x141
ID_SENSOR_HB = 0x1F0
ID_DRIVE_HB = 0x2F0


class CanBridgeNode(Node):
    def __init__(self):
        super().__init__("can_bridge_node")

        # --- SocketCAN oeffnen ---
        try:
            self.sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
            self.sock.bind(("can0",))
            # Blocking-Modus fuer select() im Reader-Thread
            self.sock.setblocking(True)
        except OSError as e:
            self.get_logger().error(f"CAN-Bus nicht verfuegbar: {e}")
            raise SystemExit(1) from e

        # --- Publisher (gleiche Topics wie micro-ROS Sensor-Node) ---
        reliable_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        best_effort_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)

        self.pub_imu = self.create_publisher(Imu, "imu", reliable_qos)
        self.pub_range = self.create_publisher(Range, "range/front", reliable_qos)
        self.pub_cliff = self.create_publisher(Bool, "cliff", best_effort_qos)
        self.pub_battery = self.create_publisher(BatteryState, "battery", reliable_qos)
        self.pub_bat_shutdown = self.create_publisher(Bool, "battery_shutdown", reliable_qos)

        # --- IMU-State: Heading kommt in separatem Frame (0x131) ---
        self._imu_heading = 0.0

        # --- Range-Message (statische Felder vorbelegen) ---
        self._range_msg = Range()
        self._range_msg.header.frame_id = "ultrasonic_link"
        self._range_msg.radiation_type = Range.ULTRASOUND
        self._range_msg.field_of_view = 0.26
        self._range_msg.min_range = 0.02
        self._range_msg.max_range = 4.0

        # --- Thread-safe Queue fuer CAN-Frames ---
        self._frame_queue: queue.Queue[bytes] = queue.Queue(maxsize=512)
        self._running = True

        # --- Statistik ---
        self.frame_count = 0
        self.sensor_hb_count = 0
        self.drive_hb_count = 0

        # Reader-Thread: blockiert auf select(), CPU-effizient
        self._reader_thread = threading.Thread(target=self._can_reader, daemon=True)
        self._reader_thread.start()

        # Dispatch-Timer: Queue leeren und ROS2-Publish (10 ms = 100 Hz)
        # 100 Hz reicht fuer 50 Hz IMU (max 1 Frame Latenz = 10 ms)
        self.create_timer(0.01, self._dispatch_frames)

        # Statistik-Log (alle 10s)
        self.create_timer(10.0, self._log_stats)

        self.get_logger().info(
            "CAN-Bridge gestartet: Sensor-Topics via SocketCAN (can0, 1 Mbit/s, select-basiert)"
        )

    def _can_reader(self):
        """Liest CAN-Frames blockierend via select() (eigener Thread)."""
        while self._running:
            try:
                ready, _, _ = select.select([self.sock], [], [], 1.0)
                if not ready:
                    continue
                frame = self.sock.recv(CAN_FRAME_SIZE)
                with contextlib.suppress(queue.Full):
                    self._frame_queue.put_nowait(frame)
            except OSError:
                break

    def _dispatch_frames(self):
        """Verarbeitet alle gepufferten CAN-Frames im ROS2-Executor-Thread."""
        processed = 0
        while processed < 64:  # Max. 64 Frames pro Dispatch-Zyklus
            try:
                frame = self._frame_queue.get_nowait()
            except queue.Empty:
                break
            processed += 1

            can_id, dlc, data = struct.unpack(CAN_FRAME_FMT, frame)
            can_id &= 0x1FFFFFFF  # Extended-ID Maske
            self.frame_count += 1

            if can_id == ID_IMU_ACCEL and dlc >= 8:
                self._handle_imu_accel(data)
            elif can_id == ID_IMU_HEADING and dlc >= 4:
                self._handle_imu_heading(data)
            elif can_id == ID_RANGE and dlc >= 4:
                self._handle_range(data)
            elif can_id == ID_CLIFF and dlc >= 1:
                self._handle_cliff(data)
            elif can_id == ID_BATTERY and dlc >= 6:
                self._handle_battery(data)
            elif can_id == ID_BAT_SHUTDOWN and dlc >= 1:
                self._handle_bat_shutdown(data)
            elif can_id == ID_SENSOR_HB:
                self.sensor_hb_count += 1
            elif can_id == ID_DRIVE_HB:
                self.drive_hb_count += 1

    def _handle_imu_accel(self, data: bytes):
        """0x130: ax,ay,az [int16 milli-m/s^2] + gz [int16 0.01 rad/s]."""
        ax_raw, ay_raw, az_raw, gz_crad = struct.unpack_from("<hhhh", data)

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        # Firmware kodiert: int16_t iax = (int16_t)(ax * 1000.0f)
        # wobei ax in m/s^2 → Division durch 1000 ergibt m/s^2
        msg.linear_acceleration.x = ax_raw / 1000.0
        msg.linear_acceleration.y = ay_raw / 1000.0
        msg.linear_acceleration.z = az_raw / 1000.0

        # int16 0.01 rad/s -> float rad/s
        msg.angular_velocity.z = gz_crad / 100.0

        # Heading aus letztem 0x131 Frame
        msg.orientation.z = math.sin(self._imu_heading / 2.0)
        msg.orientation.w = math.cos(self._imu_heading / 2.0)

        # Kovarianz (identisch zu Firmware)
        msg.orientation_covariance[0] = 0.01
        msg.orientation_covariance[4] = 0.01
        msg.orientation_covariance[8] = 0.01
        msg.angular_velocity_covariance[0] = 0.001
        msg.angular_velocity_covariance[4] = 0.001
        msg.angular_velocity_covariance[8] = 0.001
        msg.linear_acceleration_covariance[0] = 0.1
        msg.linear_acceleration_covariance[4] = 0.1
        msg.linear_acceleration_covariance[8] = 0.1

        self.pub_imu.publish(msg)

    def _handle_imu_heading(self, data: bytes):
        """0x131: heading [float32 rad] — wird mit naechstem 0x130 publiziert."""
        (self._imu_heading,) = struct.unpack_from("<f", data)

    def _handle_range(self, data: bytes):
        """0x110: distance [float32 m] -> Range msg."""
        (distance_m,) = struct.unpack_from("<f", data)
        msg = self._range_msg
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.range = distance_m
        self.pub_range.publish(msg)

    def _handle_cliff(self, data: bytes):
        """0x120: cliff [uint8] -> Bool msg."""
        msg = Bool()
        msg.data = data[0] != 0
        self.pub_cliff.publish(msg)

    def _handle_battery(self, data: bytes):
        """0x140: V [uint16 mV] + I [int16 mA] + P [uint16 mW]."""
        v_mv, i_ma, _p_mw = struct.unpack_from("<HhH", data)
        voltage = v_mv / 1000.0
        current = i_ma / 1000.0

        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.voltage = voltage
        msg.current = current
        msg.percentage = self._estimate_soc(voltage)
        msg.capacity = 3.35
        msg.design_capacity = 3.35
        msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        msg.present = True
        self.pub_battery.publish(msg)

    def _handle_bat_shutdown(self, data: bytes):
        """0x141: shutdown [uint8] -> Bool msg."""
        msg = Bool()
        msg.data = data[0] != 0
        self.pub_bat_shutdown.publish(msg)

    @staticmethod
    def _estimate_soc(voltage: float) -> float:
        """SOC-Schaetzung (linear, identisch zu Firmware)."""
        pack_charge_max = 12.60
        pack_cutoff = 7.95
        if voltage >= pack_charge_max:
            return 1.0
        if voltage <= pack_cutoff:
            return 0.0
        return (voltage - pack_cutoff) / (pack_charge_max - pack_cutoff)

    def _log_stats(self):
        self.get_logger().info(
            f"CAN-Bridge: {self.frame_count} Frames, "
            f"Sensor-HB: {self.sensor_hb_count}, "
            f"Drive-HB: {self.drive_hb_count}"
        )

    def destroy_node(self):
        self._running = False
        if self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2.0)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CanBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
