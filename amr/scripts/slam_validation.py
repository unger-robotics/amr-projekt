#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLAM-Validierung: Berechnet den Absolute Trajectory Error (ATE)
zwischen SLAM-korrigierter Pose und reiner Odometrie.

Zwei Modi:
  1. Live-Modus:  Subscribt /odom und hoert map->base_link via TF
  2. Rosbag-Modus: Liest gespeicherte rosbag2-Datenbank aus

Da kein Motion-Capture-System als Ground Truth vorhanden ist, wird
der Drift zwischen SLAM-korrigierter Position (map->base_link) und
reiner Odometrie (odom->base_link) als Qualitaetsmass verwendet.
Die map->odom Transformation zeigt den Korrekturbedarf des SLAM.

Akzeptanzkriterium: ATE (RMSE) < 0.20 m

Verwendung:
  # Live (laeuft bis Ctrl+C, dann Auswertung):
  python3 slam_validation.py --live --duration 120

  # Rosbag:
  python3 slam_validation.py --bag /pfad/zur/rosbag2_db
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

# ROS2-Imports (nur verfuegbar auf dem Roboter mit installiertem ROS2)
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.time import Time
    from nav_msgs.msg import Odometry
    from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False

# Rosbag-Import
try:
    from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
    from rclpy.serialization import deserialize_message
    ROSBAG_AVAILABLE = True
except ImportError:
    ROSBAG_AVAILABLE = False

# Matplotlib fuer Plots
try:
    import matplotlib
    matplotlib.use('Agg')  # Headless-Backend fuer Roboter ohne Display
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def quaternion_to_yaw(q):
    """Quaternion (x, y, z, w) -> Yaw-Winkel (rad)."""
    siny_cosp = 2.0 * (q[3] * q[2] + q[0] * q[1])
    cosy_cosp = 1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2])
    return math.atan2(siny_cosp, cosy_cosp)


def compute_ate(odom_poses, slam_poses):
    """
    Berechnet den Absolute Trajectory Error (ATE) als RMSE.

    Parameter:
        odom_poses: Liste von (timestamp, x, y, yaw) - reine Odometrie
        slam_poses: Liste von (timestamp, x, y, yaw) - SLAM-korrigiert

    Rueckgabe:
        ate_rmse: RMSE ueber alle Zeitpunkte
        errors:   Liste von (timestamp, error) Tupeln
    """
    if len(odom_poses) == 0 or len(slam_poses) == 0:
        return float('nan'), []

    odom_arr = np.array(odom_poses)
    slam_arr = np.array(slam_poses)

    # Timestamps synchronisieren: fuer jeden SLAM-Zeitpunkt naechsten Odom-Zeitpunkt suchen
    errors = []
    squared_errors = []

    for s in slam_arr:
        t_slam = s[0]
        # Naechsten Odom-Zeitpunkt finden
        idx = np.argmin(np.abs(odom_arr[:, 0] - t_slam))
        t_diff = abs(odom_arr[idx, 0] - t_slam)

        # Nur synchronisierte Paare (max 0.1s Differenz)
        if t_diff > 0.1:
            continue

        dx = s[1] - odom_arr[idx, 1]
        dy = s[2] - odom_arr[idx, 2]
        err = math.sqrt(dx * dx + dy * dy)
        errors.append((t_slam, err))
        squared_errors.append(err * err)

    if len(squared_errors) == 0:
        return float('nan'), []

    ate_rmse = math.sqrt(np.mean(squared_errors))
    return ate_rmse, errors


def verify_tf_chain(tf_buffer, node):
    """
    Prueft ob alle erwarteten TF-Frames verfuegbar sind.

    Erwartete Kette: map -> odom -> base_link -> laser
    """
    required_transforms = [
        ('map', 'odom'),
        ('odom', 'base_link'),
        ('base_link', 'laser'),
    ]

    results = {}
    for parent, child in required_transforms:
        key = f'{parent} -> {child}'
        try:
            tf_buffer.lookup_transform(parent, child, Time())
            results[key] = 'OK'
            node.get_logger().info(f'TF {key}: verfuegbar')
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            results[key] = f'FEHLT: {e}'
            node.get_logger().warn(f'TF {key}: {e}')

    return results


def generate_report(ate_rmse, errors, odom_poses, slam_poses, tf_results, output_dir='.'):
    """Erzeugt Markdown-Report und optionalen Matplotlib-Plot."""
    # Akzeptanzkriterium
    passed = ate_rmse < 0.20

    # --- Markdown-Report ---
    report = []
    report.append('# SLAM-Validierungsbericht')
    report.append('')
    report.append(f'Datum: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    report.append('')

    report.append('## TF-Ketten-Verifikation')
    report.append('')
    report.append('| Transform | Status |')
    report.append('|-----------|--------|')
    for tf_name, status in tf_results.items():
        report.append(f'| {tf_name} | {status} |')
    report.append('')

    report.append('## Absolute Trajectory Error (ATE)')
    report.append('')
    report.append(f'- Anzahl synchronisierter Posen-Paare: {len(errors)}')
    report.append(f'- ATE (RMSE): **{ate_rmse:.4f} m**')
    if len(errors) > 0:
        max_err = max(e[1] for e in errors)
        min_err = min(e[1] for e in errors)
        report.append(f'- Max. Fehler: {max_err:.4f} m')
        report.append(f'- Min. Fehler: {min_err:.4f} m')
    report.append(f'- Akzeptanzkriterium: ATE < 0.20 m')
    report.append(f'- Ergebnis: **{"BESTANDEN" if passed else "NICHT BESTANDEN"}**')
    report.append('')

    report_text = '\n'.join(report)
    report_path = os.path.join(output_dir, 'slam_validation_report.md')
    with open(report_path, 'w') as f:
        f.write(report_text)
    print(f'Report gespeichert: {report_path}')

    # --- JSON-Export fuer validation_report.py ---
    max_err = max(e[1] for e in errors) if errors else None
    mean_err = float(np.mean([e[1] for e in errors])) if errors else None
    duration_s = None
    if errors:
        duration_s = round(errors[-1][0] - errors[0][0], 2)

    json_export = {
        "ate_m": round(ate_rmse, 4) if not math.isnan(ate_rmse) else None,
        "max_error_m": round(max_err, 4) if max_err is not None else None,
        "mean_error_m": round(mean_err, 4) if mean_err is not None else None,
        "duration_s": duration_s,
        "num_samples": len(errors),
        "num_odom_poses": len(odom_poses),
        "num_slam_poses": len(slam_poses),
        "passed": passed,
    }
    json_path = os.path.join(output_dir, 'slam_results.json')
    with open(json_path, 'w') as f:
        json.dump(json_export, f, indent=2)
    print(f'JSON gespeichert: {json_path}')

    # --- Plot ---
    if MATPLOTLIB_AVAILABLE and len(odom_poses) > 0 and len(slam_poses) > 0:
        odom_arr = np.array(odom_poses)
        slam_arr = np.array(slam_poses)

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Trajektorien-Vergleich
        ax1 = axes[0]
        ax1.plot(odom_arr[:, 1], odom_arr[:, 2], 'b-', label='Odometrie', linewidth=1)
        ax1.plot(slam_arr[:, 1], slam_arr[:, 2], 'r-', label='SLAM', linewidth=1)
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')
        ax1.set_title('Trajektorien-Vergleich')
        ax1.legend()
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)

        # ATE ueber Zeit
        if len(errors) > 0:
            ax2 = axes[1]
            err_arr = np.array(errors)
            t_rel = err_arr[:, 0] - err_arr[0, 0]  # Relative Zeit
            ax2.plot(t_rel, err_arr[:, 1], 'k-', linewidth=1)
            ax2.axhline(y=0.20, color='r', linestyle='--', label='Akzeptanz (0.20 m)')
            ax2.set_xlabel('Zeit (s)')
            ax2.set_ylabel('ATE (m)')
            ax2.set_title('Absolute Trajectory Error ueber Zeit')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, 'slam_validation_plot.png')
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f'Plot gespeichert: {plot_path}')

    return passed


# ---------------------------------------------------------------------------
# Live-Modus: ROS2-Node
# ---------------------------------------------------------------------------

class SlamValidationNode(Node):
    """ROS2-Node fuer die Live-SLAM-Validierung."""

    def __init__(self, duration):
        super().__init__('slam_validation')
        self.duration = duration
        self.odom_poses = []
        self.slam_poses = []
        self.start_time = None

        # TF-Listener fuer map->base_link
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Odometrie-Subscriber
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )

        # Timer: Alle 200 ms SLAM-Pose aus TF abfragen
        self.sample_timer = self.create_timer(0.2, self.sample_slam_pose)

        self.get_logger().info(
            f'SLAM-Validierung gestartet (Dauer: {duration}s). '
            f'Warte auf Daten...'
        )

    def odom_callback(self, msg):
        """Speichert reine Odometrie-Posen."""
        if self.start_time is None:
            self.start_time = time.time()

        t = time.time()
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation
        yaw = quaternion_to_yaw([ori.x, ori.y, ori.z, ori.w])
        self.odom_poses.append((t, pos.x, pos.y, yaw))

    def sample_slam_pose(self):
        """Holt SLAM-korrigierte Pose aus der TF map->base_link."""
        if self.start_time is None:
            return

        # Dauer pruefen
        elapsed = time.time() - self.start_time
        if elapsed > self.duration:
            self.get_logger().info(
                f'Aufzeichnung beendet nach {elapsed:.1f}s. '
                f'Odom: {len(self.odom_poses)}, SLAM: {len(self.slam_poses)} Posen.'
            )
            raise SystemExit(0)

        try:
            transform = self.tf_buffer.lookup_transform(
                'map', 'base_link', Time()
            )
            t = time.time()
            pos = transform.transform.translation
            ori = transform.transform.rotation
            yaw = quaternion_to_yaw([ori.x, ori.y, ori.z, ori.w])
            self.slam_poses.append((t, pos.x, pos.y, yaw))
        except (LookupException, ConnectivityException, ExtrapolationException):
            pass  # TF noch nicht verfuegbar, normal beim Start

    def get_tf_results(self):
        """TF-Kette pruefen."""
        return verify_tf_chain(self.tf_buffer, self)


def run_live_mode(duration, output_dir):
    """Fuehrt die Live-Validierung aus."""
    if not ROS2_AVAILABLE:
        print('FEHLER: ROS2 (rclpy) nicht verfuegbar. '
              'Bitte ROS2 Humble sourcing durchfuehren.')
        sys.exit(1)

    rclpy.init()
    node = SlamValidationNode(duration)

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass

    # TF-Kette pruefen (am Ende, wenn alles laeuft)
    tf_results = node.get_tf_results()

    # ATE berechnen
    ate_rmse, errors = compute_ate(node.odom_poses, node.slam_poses)

    print(f'\n--- Ergebnis ---')
    print(f'Odom-Posen:  {len(node.odom_poses)}')
    print(f'SLAM-Posen:  {len(node.slam_poses)}')
    print(f'ATE (RMSE):  {ate_rmse:.4f} m')

    passed = generate_report(
        ate_rmse, errors, node.odom_poses, node.slam_poses,
        tf_results, output_dir
    )

    node.destroy_node()
    rclpy.shutdown()

    return passed


# ---------------------------------------------------------------------------
# Rosbag-Modus
# ---------------------------------------------------------------------------

def run_bag_mode(bag_path, output_dir):
    # TODO: Rosbag-Modus nicht implementiert – TF-Replay fuer SLAM-Posen fehlt.
    """Liest eine rosbag2-Aufzeichnung und berechnet ATE."""
    if not ROSBAG_AVAILABLE:
        print('FEHLER: rosbag2_py nicht verfuegbar. '
              'Bitte ROS2 Humble sourcing durchfuehren.')
        sys.exit(1)

    if not ROS2_AVAILABLE:
        print('FEHLER: rclpy nicht verfuegbar.')
        sys.exit(1)

    rclpy.init()

    storage_options = StorageOptions(uri=bag_path, storage_id='sqlite3')
    converter_options = ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )

    reader = SequentialReader()
    reader.open(storage_options, converter_options)

    odom_poses = []
    # Hinweis: TF-basierte SLAM-Posen sind in rosbag unter /tf verfuegbar,
    # aber die Extraktion erfordert einen TF-Buffer-Replay.
    # Vereinfachter Ansatz: /odom mit /slam_toolbox/map_to_odom vergleichen.

    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        t_sec = timestamp / 1e9  # Nanosekunden -> Sekunden

        if topic == '/odom':
            msg = deserialize_message(data, Odometry)
            pos = msg.pose.pose.position
            ori = msg.pose.pose.orientation
            yaw = quaternion_to_yaw([ori.x, ori.y, ori.z, ori.w])
            odom_poses.append((t_sec, pos.x, pos.y, yaw))

    print(f'Rosbag gelesen: {len(odom_poses)} Odometrie-Nachrichten')
    print('Hinweis: Fuer vollstaendige ATE-Berechnung aus rosbag '
          'wird ein TF-Replay benoetigt.')
    print('Die Odometrie-Trajektorie wurde extrahiert.')

    # Einfacher Report ohne SLAM-Vergleich (nur Odom-Trajektorie)
    tf_results = {'Rosbag-Modus': 'TF-Replay nicht implementiert'}
    ate_rmse = float('nan')
    errors = []
    slam_poses = []

    generate_report(ate_rmse, errors, odom_poses, slam_poses,
                    tf_results, output_dir)

    rclpy.shutdown()
    return False


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description='SLAM-Validierung: ATE-Berechnung fuer AMR'
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--live', action='store_true',
        help='Live-Modus: Subscribt auf /odom und TF'
    )
    mode_group.add_argument(
        '--bag', type=str,
        help='Rosbag-Modus: Pfad zur rosbag2-Datenbank'
    )
    parser.add_argument(
        '--duration', type=int, default=120,
        help='Aufzeichnungsdauer im Live-Modus (Sekunden, Standard: 120)'
    )
    parser.add_argument(
        '--output', type=str, default=os.path.dirname(os.path.abspath(__file__)),
        help='Ausgabeverzeichnis fuer Report und Plots'
    )

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.live:
        passed = run_live_mode(args.duration, args.output)
    else:
        passed = run_bag_mode(args.bag, args.output)

    if passed:
        print('\nSLAM-Validierung BESTANDEN (ATE < 0.20 m)')
    else:
        print('\nSLAM-Validierung NICHT BESTANDEN oder unvollstaendig')

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
