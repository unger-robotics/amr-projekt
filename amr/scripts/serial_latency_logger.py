#!/usr/bin/env python3
"""Serial-Latenz-Logger: Misst ESP32->Pi Transportlatenz via header.stamp.

Subscribt /odom und /imu, berechnet die Differenz zwischen header.stamp
(ESP32 rmw_uros_epoch_nanos) und der lokalen Pi-Systemzeit.
Schreibt Ergebnisse in eine CSV-Datei fuer Bachelorarbeit-Auswertung.

Nutzung:
    ros2 run my_bot serial_latency_logger
    ros2 run my_bot serial_latency_logger --ros-args -p duration:=60 -p output:=latenz.csv
"""

import csv
import statistics
import time
from collections import defaultdict
from datetime import datetime

try:
    from amr_utils import print_header
except ImportError:
    try:
        from my_bot.amr_utils import print_header
    except ImportError:
        def print_header(title):
            print(f'\n=== {title} ===')

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu


class SerialLatencyLogger(Node):
    """ROS2-Node zur Messung der Serial-Transportlatenz zwischen ESP32 und Pi."""

    def __init__(self):
        super().__init__('serial_latency_logger')

        # Parameter
        self.declare_parameter('duration', 0)
        self.declare_parameter(
            'output',
            f'serial_latency_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

        self.duration = self.get_parameter('duration').value
        self.output_file = self.get_parameter('output').value

        # Datenstrukturen
        self.latencies = defaultdict(list)

        # CSV oeffnen
        self.csv_file = open(self.output_file, 'w', newline='')
        self.writer = csv.writer(self.csv_file)
        self.writer.writerow(['timestamp', 'topic', 'latency_ms'])

        # QoS: Reliable, depth=10
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Subscriptions
        self.create_subscription(
            Odometry, '/odom', self._odom_cb, qos
        )
        self.create_subscription(
            Imu, '/imu', self._imu_cb, qos
        )

        # Timer fuer duration-basiertes Ende
        if self.duration > 0:
            self.create_timer(float(self.duration), self._timeout_cb)

        self.get_logger().info(
            f'Serial-Latenz-Logger gestartet '
            f'(Dauer: {"unbegrenzt" if self.duration == 0 else f"{self.duration}s"}, '
            f'Ausgabe: {self.output_file})'
        )

    def _record_latency(self, msg, topic_name):
        """Berechnet und speichert die Latenz aus dem header.stamp."""
        stamp_s = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if stamp_s > 1e9:  # Plausibilitaetspruefung
            latency_ms = (time.time() - stamp_s) * 1000.0
            if -500.0 < latency_ms < 2000.0:
                self.writer.writerow([time.time(), topic_name, round(latency_ms, 2)])
                self.latencies[topic_name].append(latency_ms)

    def _odom_cb(self, msg):
        self._record_latency(msg, '/odom')

    def _imu_cb(self, msg):
        self._record_latency(msg, '/imu')

    def _timeout_cb(self):
        """Timer-Callback: Beendet den Logger nach Ablauf der konfigurierten Dauer."""
        self.get_logger().info(f'Dauer von {self.duration}s erreicht, beende...')
        self._print_summary()
        self.csv_file.close()
        rclpy.shutdown()

    def _print_summary(self):
        """Gibt eine Statistik-Zusammenfassung auf der Konsole aus."""
        print_header('Serial-Latenz Zusammenfassung')
        for topic in sorted(self.latencies.keys()):
            values = self.latencies[topic]
            n = len(values)
            if n == 0:
                print(f'  {topic}: keine Daten')
                continue
            avg = statistics.mean(values)
            med = statistics.median(values)
            mn = min(values)
            mx = max(values)
            p95 = sorted(values)[int(n * 0.95)] if n >= 20 else mx
            sd = statistics.stdev(values) if n >= 2 else 0.0
            print(
                f'  {topic} (N={n}):  '
                f'min={mn:.1f}  avg={avg:.1f}  median={med:.1f}  '
                f'p95={p95:.1f}  max={mx:.1f}  stddev={sd:.1f} ms'
            )
        print(f'  CSV gespeichert: {self.output_file}')

    def destroy_node(self):
        """Sauberes Herunterfahren: CSV schliessen, Zusammenfassung ausgeben."""
        if not self.csv_file.closed:
            self._print_summary()
            self.csv_file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SerialLatencyLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
