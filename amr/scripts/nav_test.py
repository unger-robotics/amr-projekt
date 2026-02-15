#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatisierter Navigationstest fuer den AMR.

Sendet eine Sequenz von Waypoints ueber den Nav2 NavigateToPose Action-Server
und misst die Abweichung zwischen Soll- und Ist-Position.

Testparcours: 2m x 2m Rechteck im 10x10m Testfeld.

Akzeptanzkriterien:
  - Positionsfehler (xy): < 0.10 m
  - Orientierungsfehler (yaw): < 0.15 rad (~8.6 Grad)

Verwendung:
  python3 nav_test.py
  python3 nav_test.py --timeout 90
  python3 nav_test.py --output /tmp/nav_results
"""

import argparse
import json
import math
import os
import sys
import time

# ROS2-Imports
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from action_msgs.msg import GoalStatus
    from geometry_msgs.msg import PoseStamped
    from nav_msgs.msg import Odometry
    from nav2_msgs.action import NavigateToPose
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


# ---------------------------------------------------------------------------
# Waypoints im map-Frame (2m x 2m Rechteck)
# ---------------------------------------------------------------------------

WAYPOINTS = [
    {'x': 2.0, 'y': 0.0, 'yaw': 0.0,       'name': 'WP1: 2m geradeaus'},
    {'x': 2.0, 'y': 2.0, 'yaw': 1.5708,     'name': 'WP2: 2m links'},
    {'x': 0.0, 'y': 2.0, 'yaw': 3.1416,     'name': 'WP3: zurueck (x-Richtung)'},
    {'x': 0.0, 'y': 0.0, 'yaw': 0.0,        'name': 'WP4: Start'},
]

# Akzeptanzkriterien
XY_TOLERANCE = 0.10    # 10 cm
YAW_TOLERANCE = 0.15   # ~8.6 Grad


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def yaw_to_quaternion(yaw):
    """Yaw-Winkel (rad) -> Quaternion (x, y, z, w)."""
    qz = math.sin(yaw / 2.0)
    qw = math.cos(yaw / 2.0)
    return (0.0, 0.0, qz, qw)


def quaternion_to_yaw(q):
    """Quaternion (x, y, z, w) -> Yaw-Winkel (rad)."""
    siny_cosp = 2.0 * (q[3] * q[2] + q[0] * q[1])
    cosy_cosp = 1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2])
    return math.atan2(siny_cosp, cosy_cosp)


def normalize_angle(angle):
    """Winkel auf [-pi, pi] normalisieren."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


# ---------------------------------------------------------------------------
# Navigationstest-Node
# ---------------------------------------------------------------------------

class NavTestNode(Node):
    """ROS2-Node fuer den automatisierten Navigationstest."""

    def __init__(self, timeout):
        super().__init__('nav_test')
        self.timeout = timeout
        self.current_odom = None
        self.results = []

        # Odometrie-Subscriber fuer Ist-Position
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )

        # NavigateToPose Action Client
        self.nav_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose'
        )

        self.get_logger().info('Navigationstest initialisiert. Warte auf Action-Server...')

    def odom_callback(self, msg):
        """Speichert aktuelle Odometrie-Pose."""
        self.current_odom = msg

    def get_current_pose(self):
        """Liest aktuelle Pose aus Odometrie."""
        if self.current_odom is None:
            return None
        pos = self.current_odom.pose.pose.position
        ori = self.current_odom.pose.pose.orientation
        yaw = quaternion_to_yaw([ori.x, ori.y, ori.z, ori.w])
        return (pos.x, pos.y, yaw)

    def create_goal_pose(self, waypoint):
        """Erstellt PoseStamped aus Waypoint-Dict."""
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = waypoint['x']
        goal.pose.position.y = waypoint['y']
        goal.pose.position.z = 0.0
        qx, qy, qz, qw = yaw_to_quaternion(waypoint['yaw'])
        goal.pose.orientation.x = qx
        goal.pose.orientation.y = qy
        goal.pose.orientation.z = qz
        goal.pose.orientation.w = qw
        return goal

    def navigate_to_waypoint(self, waypoint):
        """
        Sendet NavigateToPose-Goal und wartet auf Ergebnis.

        Rueckgabe: Dict mit Ergebnis-Metriken
        """
        name = waypoint['name']
        self.get_logger().info(f'Navigiere zu: {name} '
                               f'(x={waypoint["x"]}, y={waypoint["y"]}, '
                               f'yaw={waypoint["yaw"]:.4f})')

        # Warte auf Action-Server
        if not self.nav_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('NavigateToPose Action-Server nicht erreichbar!')
            return {
                'waypoint': name,
                'status': 'SERVER_NICHT_ERREICHBAR',
                'xy_error': float('nan'),
                'yaw_error': float('nan'),
                'duration': 0.0,
                'passed': False,
            }

        # Goal senden
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = self.create_goal_pose(waypoint)

        t_start = time.time()
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal_future, timeout_sec=10.0)

        goal_handle = send_goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f'Goal abgelehnt: {name}')
            return {
                'waypoint': name,
                'status': 'ABGELEHNT',
                'xy_error': float('nan'),
                'yaw_error': float('nan'),
                'duration': 0.0,
                'passed': False,
            }

        self.get_logger().info(f'Goal akzeptiert: {name}')

        # Auf Ergebnis warten
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=self.timeout)

        duration = time.time() - t_start

        if not result_future.done():
            self.get_logger().warn(f'Timeout ({self.timeout}s) fuer: {name}')
            # Goal abbrechen
            goal_handle.cancel_goal_async()
            status_str = 'TIMEOUT'
        else:
            result = result_future.result()
            if result.status == GoalStatus.STATUS_SUCCEEDED:
                status_str = 'ERREICHT'
            elif result.status == GoalStatus.STATUS_CANCELED:
                status_str = 'ABGEBROCHEN'
            else:
                status_str = f'FEHLGESCHLAGEN (Status: {result.status})'

        # Kurz warten, damit Odometrie aktuell ist
        time.sleep(0.5)
        rclpy.spin_once(self, timeout_sec=0.1)

        # Ist-Position auslesen
        current = self.get_current_pose()
        if current is None:
            self.get_logger().warn('Keine Odometrie verfuegbar!')
            return {
                'waypoint': name,
                'status': status_str,
                'xy_error': float('nan'),
                'yaw_error': float('nan'),
                'duration': duration,
                'passed': False,
            }

        x_ist, y_ist, yaw_ist = current

        # Fehler berechnen
        dx = waypoint['x'] - x_ist
        dy = waypoint['y'] - y_ist
        xy_error = math.sqrt(dx * dx + dy * dy)
        yaw_error = abs(normalize_angle(waypoint['yaw'] - yaw_ist))

        xy_ok = xy_error < XY_TOLERANCE
        yaw_ok = yaw_error < YAW_TOLERANCE
        passed = xy_ok and yaw_ok and status_str == 'ERREICHT'

        self.get_logger().info(
            f'  Ergebnis: {status_str} | '
            f'xy_err={xy_error:.4f}m ({"OK" if xy_ok else "FAIL"}) | '
            f'yaw_err={yaw_error:.4f}rad ({"OK" if yaw_ok else "FAIL"}) | '
            f'Dauer={duration:.1f}s'
        )

        return {
            'waypoint': name,
            'status': status_str,
            'soll': {'x': waypoint['x'], 'y': waypoint['y'], 'yaw': waypoint['yaw']},
            'ist': {'x': x_ist, 'y': y_ist, 'yaw': yaw_ist},
            'xy_error': xy_error,
            'yaw_error': yaw_error,
            'duration': duration,
            'passed': passed,
        }

    def run_test(self):
        """Fuehrt den vollstaendigen Navigationstest durch."""
        self.get_logger().info(
            f'Starte Navigationstest: {len(WAYPOINTS)} Waypoints, '
            f'Timeout={self.timeout}s pro Waypoint'
        )

        # Warte auf erste Odometrie-Nachricht
        self.get_logger().info('Warte auf Odometrie...')
        for _ in range(50):
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.current_odom is not None:
                break
        else:
            self.get_logger().error('Keine Odometrie empfangen nach 5s!')
            return []

        start_pose = self.get_current_pose()
        self.get_logger().info(
            f'Startposition: x={start_pose[0]:.3f}, y={start_pose[1]:.3f}, '
            f'yaw={start_pose[2]:.3f}'
        )

        for wp in WAYPOINTS:
            result = self.navigate_to_waypoint(wp)
            self.results.append(result)

            # Bei kritischem Fehler (Server weg) abbrechen
            if result['status'] == 'SERVER_NICHT_ERREICHBAR':
                self.get_logger().error('Action-Server verloren, breche ab.')
                break

        return self.results


# ---------------------------------------------------------------------------
# Report-Generierung
# ---------------------------------------------------------------------------

def generate_report(results, output_dir):
    """Erzeugt Markdown-Report und JSON-Ergebnis."""
    if len(results) == 0:
        print('Keine Ergebnisse vorhanden.')
        return False

    all_passed = all(r['passed'] for r in results)
    total_duration = sum(r['duration'] for r in results)

    # --- Markdown-Report ---
    report = []
    report.append('# Navigationstest-Bericht')
    report.append('')
    report.append(f'Datum: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    report.append(f'Waypoints: {len(results)}')
    report.append(f'Gesamtdauer: {total_duration:.1f} s')
    report.append(f'Ergebnis: **{"BESTANDEN" if all_passed else "NICHT BESTANDEN"}**')
    report.append('')
    report.append('## Akzeptanzkriterien')
    report.append('')
    report.append(f'- Positionsfehler (xy): < {XY_TOLERANCE} m')
    report.append(f'- Orientierungsfehler (yaw): < {YAW_TOLERANCE} rad ({math.degrees(YAW_TOLERANCE):.1f} Grad)')
    report.append('')
    report.append('## Ergebnisse')
    report.append('')
    report.append('| Waypoint | Status | xy-Fehler (m) | yaw-Fehler (rad) | Dauer (s) | Bestanden |')
    report.append('|----------|--------|---------------|-------------------|-----------|-----------|')

    for r in results:
        xy = f'{r["xy_error"]:.4f}' if not math.isnan(r['xy_error']) else 'N/A'
        yaw = f'{r["yaw_error"]:.4f}' if not math.isnan(r['yaw_error']) else 'N/A'
        status = 'Ja' if r['passed'] else 'Nein'
        report.append(
            f'| {r["waypoint"]} | {r["status"]} | {xy} | {yaw} | '
            f'{r["duration"]:.1f} | {status} |'
        )

    report.append('')

    # Zusammenfassung
    passed_count = sum(1 for r in results if r['passed'])
    xy_errors = [r['xy_error'] for r in results if not math.isnan(r['xy_error'])]
    yaw_errors = [r['yaw_error'] for r in results if not math.isnan(r['yaw_error'])]

    report.append('## Zusammenfassung')
    report.append('')
    report.append(f'- Waypoints bestanden: {passed_count}/{len(results)}')
    if xy_errors:
        report.append(f'- Mittlerer xy-Fehler: {sum(xy_errors)/len(xy_errors):.4f} m')
        report.append(f'- Max. xy-Fehler: {max(xy_errors):.4f} m')
    if yaw_errors:
        report.append(f'- Mittlerer yaw-Fehler: {sum(yaw_errors)/len(yaw_errors):.4f} rad')
        report.append(f'- Max. yaw-Fehler: {max(yaw_errors):.4f} rad')
    report.append('')

    report_text = '\n'.join(report)

    # Dateien schreiben
    report_path = os.path.join(output_dir, 'nav_test_report.md')
    with open(report_path, 'w') as f:
        f.write(report_text)
    print(f'Report gespeichert: {report_path}')

    json_path = os.path.join(output_dir, 'nav_results.json')
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'all_passed': all_passed,
            'total_duration_s': total_duration,
            'waypoints': results,
        }, f, indent=2)
    print(f'JSON gespeichert: {json_path}')

    # Terminal-Ausgabe
    print(f'\n{"=" * 60}')
    print(f'NAVIGATIONSTEST: {"BESTANDEN" if all_passed else "NICHT BESTANDEN"}')
    print(f'Waypoints: {passed_count}/{len(results)} bestanden')
    print(f'{"=" * 60}')

    return all_passed


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main():
    if not ROS2_AVAILABLE:
        print('FEHLER: ROS2 (rclpy, nav2_msgs) nicht verfuegbar. '
              'Bitte ROS2 Humble sourcing durchfuehren.')
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Automatisierter Navigationstest fuer AMR'
    )
    parser.add_argument(
        '--timeout', type=int, default=60,
        help='Timeout pro Waypoint in Sekunden (Standard: 60)'
    )
    parser.add_argument(
        '--output', type=str, default='.',
        help='Ausgabeverzeichnis fuer Report und JSON'
    )

    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)

    rclpy.init()
    node = NavTestNode(args.timeout)

    try:
        results = node.run_test()
    except KeyboardInterrupt:
        print('\nTest abgebrochen durch Benutzer.')
        results = node.results

    passed = generate_report(results, args.output)

    node.destroy_node()
    rclpy.shutdown()

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
