#!/usr/bin/env python3
"""
Motor-Test-Tool fuer den AMR-Roboter.
ROS2-Node: publiziert /cmd_vel und subscribt /odom fuer Feedback.

Modi:
  a) Deadzone-Test: Findet minimale Geschwindigkeit die Bewegung erzeugt
  b) Richtungstest: Einzelrad-Ansteuerung in alle Richtungen
  c) Failsafe-Test: Prueft FAILSAFE_TIMEOUT_MS (500ms)
  d) Rampen-Test: Graduelle Beschleunigung auf 0.4 m/s

Sicherheit: Ctrl+C sendet sofort cmd_vel=0.
Ergebnis: Markdown-Protokoll + JSON.
"""

import datetime
import json
import os
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from amr_utils import FAILSAFE_TIMEOUT_MS, MAX_VELOCITY, PWM_DEADZONE, WHEEL_BASE

# ===========================================================================
# ROS2-Node
# ===========================================================================


class MotorTestNode(Node):
    """ROS2-Node fuer Motor-Tests mit cmd_vel und Odometrie-Feedback."""

    def __init__(self):
        super().__init__("motor_test_node")

        # Publisher fuer Geschwindigkeitsbefehle
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)

        # Subscriber fuer Odometrie-Feedback
        self.odom_sub = self.create_subscription(Odometry, "/odom", self._odom_callback, 10)

        # Aktuelle Odometrie
        self.odom_v = 0.0  # [m/s] lineare Geschwindigkeit
        self.odom_omega = 0.0  # [rad/s] Winkelgeschwindigkeit
        self.odom_x = 0.0  # [m] Position x
        self.odom_y = 0.0  # [m] Position y
        self.odom_received = False
        self.last_odom_time = None

        self.get_logger().info("Motor-Test-Node gestartet. Warte auf /odom...")

    def _odom_callback(self, msg):
        """Speichert aktuelle Odometrie-Daten."""
        self.odom_v = msg.twist.twist.linear.x
        self.odom_omega = msg.twist.twist.angular.z
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y
        self.odom_received = True
        self.last_odom_time = self.get_clock().now()

    def send_cmd_vel(self, linear_x=0.0, angular_z=0.0):
        """Sendet Geschwindigkeitsbefehl."""
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self.cmd_pub.publish(msg)

    def stop(self):
        """Sendet sofort Stopp-Befehl (cmd_vel = 0)."""
        self.send_cmd_vel(0.0, 0.0)
        # Mehrfach senden fuer Zuverlaessigkeit
        for _ in range(5):
            self.send_cmd_vel(0.0, 0.0)
            rclpy.spin_once(self, timeout_sec=0.01)

    def wait_for_odom(self, timeout_s=10.0):
        """Wartet auf erste /odom-Nachricht."""
        start = time.time()
        while not self.odom_received:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start > timeout_s:
                self.get_logger().error("Timeout: Keine /odom empfangen.")
                return False
        self.get_logger().info("/odom empfangen.")
        return True

    def spin_for(self, duration_s):
        """Dreht den ROS2-Eventloop fuer eine bestimmte Dauer."""
        start = time.time()
        while time.time() - start < duration_s:
            rclpy.spin_once(self, timeout_sec=0.02)

    def is_moving(self, threshold=0.005):
        """Prueft ob der Roboter sich bewegt (Odometrie-Geschwindigkeit)."""
        return abs(self.odom_v) > threshold or abs(self.odom_omega) > threshold


# ===========================================================================
# Test-Modi
# ===========================================================================


def run_deadzone_test(node):
    """
    Deadzone-Test: Erhoehe cmd_vel in kleinen Schritten,
    pruefe ab welcher Geschwindigkeit Odometrie Bewegung zeigt.
    """
    print("\n" + "=" * 60)
    print("  DEADZONE-TEST")
    print("=" * 60)
    print("  Erhoeht cmd_vel von 0.0 bis 0.2 m/s in 0.01-Schritten.")
    print("  Wartet 2s pro Schritt und prueft ob Odometrie sich aendert.")
    print("  ACHTUNG: Roboter bewegt sich! Raeder frei drehen lassen.\n")

    input("  Bereit? [Enter] zum Starten...")

    results = []
    deadzone_threshold = None

    try:
        step = 0.01
        v = 0.0
        while v <= 0.21:
            node.send_cmd_vel(linear_x=v)
            node.spin_for(2.0)

            moving = node.is_moving()
            status = "BEWEGT" if moving else "steht"

            sys.stdout.write(
                f"\r  cmd_vel={v:.2f} m/s -> odom_v={node.odom_v:+.4f} m/s  [{status}]          "
            )
            sys.stdout.flush()

            results.append(
                {
                    "cmd_vel": round(v, 3),
                    "odom_v": node.odom_v,
                    "moving": moving,
                }
            )

            if moving and deadzone_threshold is None:
                deadzone_threshold = v
                print(f"\n  >>> Erste Bewegung bei cmd_vel = {v:.2f} m/s <<<")

            v += step

    except KeyboardInterrupt:
        pass
    finally:
        node.stop()

    print()
    if deadzone_threshold is not None:
        print(f"\n  Deadzone-Grenze: {deadzone_threshold:.2f} m/s")
        print("  (Motoren laufen erst ab dieser Geschwindigkeit an)")
    else:
        print("\n  WARNUNG: Keine Bewegung erkannt. Motoren pruefen!")

    return {
        "steps": results,
        "deadzone_threshold_mps": deadzone_threshold,
    }


def run_direction_test(node):
    """
    Richtungstest: Steuert einzelne Raeder/Richtungen nacheinander an.
    Nutzt Kombination aus linear.x und angular.z fuer Einzelrad-Ansteuerung.
    """
    print("\n" + "=" * 60)
    print("  RICHTUNGSTEST")
    print("=" * 60)
    print("  Testet alle 4 Richtungen einzeln (je 3 Sekunden).")
    print("  ACHTUNG: Roboter bewegt sich!\n")

    # Fuer Einzelrad-Ansteuerung via Differentialkinematik:
    # Nur rechts vorwaerts: linear.x = v/2, angular.z = v/WHEEL_BASE
    # Nur links vorwaerts:  linear.x = v/2, angular.z = -v/WHEEL_BASE
    v_test = 0.15  # [m/s] Testgeschwindigkeit pro Rad

    tests = [
        ("Rechts vorwaerts", v_test / 2.0, v_test / WHEEL_BASE),
        ("Rechts rueckwaerts", -v_test / 2.0, -v_test / WHEEL_BASE),
        ("Links vorwaerts", v_test / 2.0, -v_test / WHEEL_BASE),
        ("Links rueckwaerts", -v_test / 2.0, v_test / WHEEL_BASE),
        ("Beide vorwaerts", v_test, 0.0),
        ("Beide rueckwaerts", -v_test, 0.0),
    ]

    results = {}

    try:
        for name, lin_x, ang_z in tests:
            input(f"  Test '{name}': [Enter] zum Starten (3s)...")

            node.send_cmd_vel(linear_x=lin_x, angular_z=ang_z)
            node.spin_for(3.0)

            v_measured = node.odom_v
            omega_measured = node.odom_omega
            moving = node.is_moving()

            node.stop()
            node.spin_for(0.5)  # Auslaufen lassen

            status = "\033[32mOK\033[0m" if moving else "\033[31mKEINE BEWEGUNG\033[0m"
            print(
                f"  {name}: v={v_measured:+.4f} m/s, omega={omega_measured:+.4f} rad/s  [{status}]"
            )

            results[name] = {
                "cmd_linear_x": lin_x,
                "cmd_angular_z": ang_z,
                "odom_v": v_measured,
                "odom_omega": omega_measured,
                "moving": moving,
            }

    except KeyboardInterrupt:
        node.stop()
        print("\n  Abgebrochen.")

    return results


def run_failsafe_test(node):
    """
    Failsafe-Test: Sendet cmd_vel, stoppt dann Node-Ausgabe,
    misst Zeit bis Odometrie-Geschwindigkeit = 0.
    Erwartet: ~500ms (FAILSAFE_TIMEOUT_MS).
    """
    print("\n" + "=" * 60)
    print("  FAILSAFE-TEST")
    print("=" * 60)
    print(f"  Erwartetes Timeout: {FAILSAFE_TIMEOUT_MS} ms")
    print("  Sendet cmd_vel=0.2 m/s fuer 3s, stoppt dann Senden,")
    print("  und misst wie lange der Roboter noch faehrt.\n")

    input("  Bereit? [Enter] zum Starten...")

    # Phase 1: Roboter auf Geschwindigkeit bringen
    print("  Phase 1: Beschleunigen (3s)...")
    start = time.time()
    while time.time() - start < 3.0:
        node.send_cmd_vel(linear_x=0.2)
        rclpy.spin_once(node, timeout_sec=0.02)

    if not node.is_moving():
        print("  WARNUNG: Roboter bewegt sich nicht. Test abgebrochen.")
        node.stop()
        return {"error": "Keine Bewegung bei cmd_vel=0.2"}

    v_before = node.odom_v
    print(f"  Geschwindigkeit vor Stopp: {v_before:.4f} m/s")

    # Phase 2: Aufhoeren cmd_vel zu senden (Failsafe soll greifen)
    print("  Phase 2: cmd_vel wird NICHT mehr gesendet. Warte auf Failsafe...")
    stop_time = time.time()
    failsafe_triggered = False
    timeout_measured = None

    try:
        while time.time() - stop_time < 3.0:
            rclpy.spin_once(node, timeout_sec=0.02)

            elapsed_ms = (time.time() - stop_time) * 1000.0
            sys.stdout.write(f"\r  t={elapsed_ms:.0f} ms  odom_v={node.odom_v:+.4f} m/s    ")
            sys.stdout.flush()

            if not node.is_moving() and not failsafe_triggered:
                failsafe_triggered = True
                timeout_measured = elapsed_ms
                break

    except KeyboardInterrupt:
        node.stop()

    node.stop()
    print()

    if failsafe_triggered:
        assert timeout_measured is not None
        print(f"\n  Failsafe ausgeloest nach: {timeout_measured:.0f} ms")
        deviation = abs(timeout_measured - FAILSAFE_TIMEOUT_MS)
        tolerance = 200  # +/- 200ms Toleranz

        if deviation <= tolerance:
            print(f"  Abweichung: {deviation:.0f} ms (Toleranz: +/-{tolerance} ms)")
            print("  Bewertung: \033[32mPASS\033[0m")
        else:
            print(f"  Abweichung: {deviation:.0f} ms (Toleranz: +/-{tolerance} ms)")
            print("  Bewertung: \033[31mFAIL\033[0m")
    else:
        print("\n  WARNUNG: Failsafe nicht innerhalb 3s ausgeloest!")
        print("  Bewertung: \033[31mFAIL\033[0m")
        timeout_measured = -1

    return {
        "v_before_stop_mps": v_before,
        "failsafe_triggered": failsafe_triggered,
        "timeout_measured_ms": timeout_measured,
        "expected_timeout_ms": FAILSAFE_TIMEOUT_MS,
    }


def run_ramp_test(node):
    """
    Rampen-Test: Graduelle Beschleunigung von 0 auf MAX_VELOCITY.
    Beobachtet ob Beschleunigung gleichmaessig ist.
    """
    print("\n" + "=" * 60)
    print("  RAMPEN-TEST")
    print("=" * 60)
    print(f"  Beschleunigt von 0 auf {MAX_VELOCITY} m/s in 5 Sekunden.")
    print("  Beobachtet Odometrie-Verlauf.\n")

    input("  Bereit? [Enter] zum Starten...")

    ramp_duration = 5.0  # [s]
    data_points = []
    v_at_max = None

    try:
        start = time.time()
        while True:
            elapsed = time.time() - start

            if elapsed >= ramp_duration:
                break

            # Linearer Anstieg
            target_v = (elapsed / ramp_duration) * MAX_VELOCITY
            node.send_cmd_vel(linear_x=target_v)
            rclpy.spin_once(node, timeout_sec=0.02)

            data_points.append(
                {
                    "time_s": round(elapsed, 3),
                    "cmd_v": round(target_v, 4),
                    "odom_v": round(node.odom_v, 4),
                }
            )

            sys.stdout.write(
                f"\r  t={elapsed:.1f}s  cmd={target_v:.3f} m/s  odom={node.odom_v:+.4f} m/s    "
            )
            sys.stdout.flush()

        # Halte MAX_VELOCITY fuer 2s
        print(f"\n  Halte {MAX_VELOCITY} m/s fuer 2s...")
        hold_start = time.time()
        while time.time() - hold_start < 2.0:
            node.send_cmd_vel(linear_x=MAX_VELOCITY)
            rclpy.spin_once(node, timeout_sec=0.02)

        v_at_max = node.odom_v
        print(f"  Odometrie bei Ziel: {v_at_max:.4f} m/s")

    except KeyboardInterrupt:
        pass
    finally:
        print("  Abbremsen...")
        node.stop()
        node.spin_for(1.0)

    # Auswertung: Pruefe ob Endgeschwindigkeit nah am Ziel
    if v_at_max is not None and data_points:
        tracking_error = abs(v_at_max - MAX_VELOCITY)
        print(f"  Tracking-Error: {tracking_error:.4f} m/s")

        if tracking_error < 0.05:
            print("  Bewertung: \033[32mGUT (< 50 mm/s Abweichung)\033[0m")
        elif tracking_error < 0.10:
            print("  Bewertung: \033[33mAKZEPTABEL (50-100 mm/s)\033[0m")
        else:
            print("  Bewertung: \033[31mSCHLECHT (> 100 mm/s)\033[0m")

    return {
        "ramp_duration_s": ramp_duration,
        "target_velocity_mps": MAX_VELOCITY,
        "final_odom_v_mps": v_at_max if data_points else None,
        "data_points": data_points,
    }


# ===========================================================================
# Protokoll
# ===========================================================================


def generate_markdown(test_results):
    """Erzeugt Markdown-Protokoll."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# Motor-Test Protokoll AMR")
    lines.append("")
    lines.append(f"Datum: {ts}")
    lines.append("")

    # Deadzone
    dz = test_results.get("deadzone")
    if dz:
        lines.append("## Deadzone-Test")
        lines.append("")
        threshold = dz.get("deadzone_threshold_mps")
        if threshold is not None:
            lines.append(f"Deadzone-Grenze: {threshold:.2f} m/s")
        else:
            lines.append("Deadzone-Grenze: Nicht erkannt (keine Bewegung)")
        lines.append("")
        lines.append("| cmd_vel [m/s] | odom_v [m/s] | Bewegt |")
        lines.append("|---|---|---|")
        for step in dz.get("steps", []):
            lines.append(
                f"| {step['cmd_vel']:.3f} | {step['odom_v']:.4f} | "
                f"{'ja' if step['moving'] else 'nein'} |"
            )
        lines.append("")

    # Richtung
    dr = test_results.get("direction")
    if dr:
        lines.append("## Richtungstest")
        lines.append("")
        lines.append(
            "| Test | cmd_lin [m/s] | cmd_ang [rad/s] | "
            "odom_v [m/s] | odom_omega [rad/s] | Bewegt |"
        )
        lines.append("|---|---|---|---|---|---|")
        for name, data in dr.items():
            lines.append(
                f"| {name} | {data['cmd_linear_x']:.3f} | "
                f"{data['cmd_angular_z']:.3f} | {data['odom_v']:.4f} | "
                f"{data['odom_omega']:.4f} | "
                f"{'ja' if data['moving'] else 'nein'} |"
            )
        lines.append("")

    # Failsafe
    fs = test_results.get("failsafe")
    if fs:
        lines.append("## Failsafe-Test")
        lines.append("")
        lines.append("| Parameter | Wert |")
        lines.append("|---|---|")
        lines.append(f"| Erwartetes Timeout | {fs.get('expected_timeout_ms')} ms |")
        lines.append(f"| Gemessenes Timeout | {fs.get('timeout_measured_ms', 'N/A')} ms |")
        lines.append(f"| Ausgeloest | {'ja' if fs.get('failsafe_triggered') else 'nein'} |")
        lines.append("")

    # Rampe
    ramp = test_results.get("ramp")
    if ramp:
        lines.append("## Rampen-Test")
        lines.append("")
        lines.append("| Parameter | Wert |")
        lines.append("|---|---|")
        lines.append(f"| Zielgeschwindigkeit | {ramp.get('target_velocity_mps')} m/s |")
        lines.append(f"| Rampendauer | {ramp.get('ramp_duration_s')} s |")
        final_v = ramp.get("final_odom_v_mps")
        if final_v is not None:
            lines.append(f"| Endgeschwindigkeit (Odom) | {final_v:.4f} m/s |")
        lines.append("")

    return "\n".join(lines)


def save_results(test_results):
    """Speichert Ergebnisse als JSON und Markdown."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # JSON
    json_path = os.path.join(script_dir, "motor_results.json")

    # Nicht-serialisierbare Daten filtern (ramp data_points koennen gross sein)
    json_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "config": {
            "wheel_base_m": WHEEL_BASE,
            "failsafe_timeout_ms": FAILSAFE_TIMEOUT_MS,
            "max_velocity_mps": MAX_VELOCITY,
            "pwm_deadzone": PWM_DEADZONE,
        },
    }
    for key in ("deadzone", "direction", "failsafe", "ramp"):
        if key in test_results:
            json_data[key] = test_results[key]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"  JSON gespeichert: {json_path}")

    # Markdown
    md_path = os.path.join(script_dir, f"motor_test_{ts}.md")
    md_content = generate_markdown(test_results)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  Markdown gespeichert: {md_path}")

    return json_path, md_path


# ===========================================================================
# Hauptprogramm
# ===========================================================================


def print_menu():
    """Zeigt das Hauptmenue an."""
    print("\n" + "-" * 40)
    print("  Motor-Test-Modi:")
    print("  a) Deadzone-Test")
    print("  b) Richtungstest")
    print("  c) Failsafe-Test")
    print("  d) Rampen-Test")
    print("  s) Ergebnisse speichern und beenden")
    print("  q) Beenden ohne Speichern")
    print("-" * 40)


def main(args=None):
    rclpy.init(args=args)

    print()
    print("*" * 60)
    print("  AMR Motor-Test-Tool")
    print("  ROS2-Node: motor_test_node")
    print(f"  Zeitpunkt: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("*" * 60)
    print()
    print("  SICHERHEITSHINWEIS: Ctrl+C sendet sofort cmd_vel=0!")
    print("  Roboter muss auf Bloecken stehen (Raeder frei drehend)")
    print("  ODER in sicherer Umgebung fahren.")

    node = MotorTestNode()

    # Auf erste /odom warten
    print("\n  Warte auf /odom...")
    if not node.wait_for_odom(timeout_s=15.0):
        print("  FEHLER: /odom nicht empfangen. Ist der micro-ROS Agent aktiv?")
        node.destroy_node()
        rclpy.shutdown()
        return 1

    test_results = {}

    try:
        while True:
            print_menu()
            choice = input("  Auswahl: ").strip().lower()

            if choice == "a":
                test_results["deadzone"] = run_deadzone_test(node)
            elif choice == "b":
                test_results["direction"] = run_direction_test(node)
            elif choice == "c":
                test_results["failsafe"] = run_failsafe_test(node)
            elif choice == "d":
                test_results["ramp"] = run_ramp_test(node)
            elif choice == "s":
                if test_results:
                    save_results(test_results)
                else:
                    print("  Keine Testergebnisse vorhanden.")
                break
            elif choice == "q":
                print("  Beendet ohne Speichern.")
                break
            else:
                print("  Ungueltige Eingabe.")

    except KeyboardInterrupt:
        print("\n\n  NOTAUS: Sende cmd_vel=0...")
        node.stop()
        print("  Motoren gestoppt.")
        if test_results:
            print("  Speichere bisherige Ergebnisse...")
            save_results(test_results)

    node.stop()
    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
