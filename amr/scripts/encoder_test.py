#!/usr/bin/env python3
"""
Encoder-Kalibrierungs-Tool fuer den AMR-Roboter.
ROS2-Node: subscribt /odom und berechnet Encoder-Ticks zurueck.

Modi:
  - 10-Umdrehungen-Test: Bestimmt TICKS_PER_REV (3 Durchgaenge)
  - Live-Anzeige: Geschwindigkeit und abgeleitete Tick-Raten
  - Richtungstest: Prueft Vorzeichen-Konvention
  - Asymmetrie-Test: Vergleicht linkes/rechtes Rad

Ergebnis: Empfohlene config.h-Werte + JSON-Protokoll.
"""

import sys
import os
import json
import math
import time
import datetime

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


# ===========================================================================
# Konstanten aus config.h
# ===========================================================================

WHEEL_DIAMETER = 0.065          # [m]
WHEEL_RADIUS = WHEEL_DIAMETER / 2.0
WHEEL_BASE = 0.178              # [m] Spurbreite
WHEEL_CIRCUMFERENCE = WHEEL_DIAMETER * math.pi  # ~0.20420 m
TICKS_PER_REV_NOMINAL = 374.0   # Nennwert JGA25-370
METERS_PER_TICK_NOMINAL = WHEEL_CIRCUMFERENCE / TICKS_PER_REV_NOMINAL

# Akzeptanzkriterien
TICKS_PER_REV_MIN = 370.0
TICKS_PER_REV_MAX = 380.0
REPRODUCIBILITY_MAX_TICKS = 2.0  # Maximale Abweichung zwischen Durchgaengen


# ===========================================================================
# ROS2-Node
# ===========================================================================

class EncoderTestNode(Node):
    """ROS2-Node fuer Encoder-Kalibrierung via /odom-Rueckrechnung."""

    def __init__(self):
        super().__init__("encoder_test_node")

        # Subscriber auf /odom
        self.odom_sub = self.create_subscription(
            Odometry, "/odom", self._odom_callback, 10)

        # Aktuelle Odometrie-Daten
        self.last_odom_time = None
        self.total_ticks_left = 0.0
        self.total_ticks_right = 0.0
        self.last_v_left = 0.0
        self.last_v_right = 0.0
        self.odom_received = False
        self.recording = False

        # Testdaten
        self.calibration_results = []

        self.get_logger().info("Encoder-Test-Node gestartet. Warte auf /odom...")

    def _odom_callback(self, msg):
        """Verarbeitet Odometrie-Nachrichten und berechnet Einzel-Rad-Ticks."""
        now = self.get_clock().now()

        # Lineare und Winkelgeschwindigkeit aus Odometrie
        v = msg.twist.twist.linear.x    # [m/s] Roboter-Geschwindigkeit
        omega = msg.twist.twist.angular.z  # [rad/s] Drehrate

        # Differentialkinematik: Einzelrad-Geschwindigkeiten
        v_left = v - omega * WHEEL_BASE / 2.0
        v_right = v + omega * WHEEL_BASE / 2.0

        self.last_v_left = v_left
        self.last_v_right = v_right
        self.odom_received = True

        if not self.recording:
            self.last_odom_time = now
            return

        if self.last_odom_time is not None:
            dt_ns = (now - self.last_odom_time).nanoseconds
            dt = dt_ns / 1e9  # [s]

            if dt > 0.0 and dt < 1.0:
                # Zurueckgerechnete Ticks seit letztem Callback
                delta_ticks_left = v_left * dt / METERS_PER_TICK_NOMINAL
                delta_ticks_right = v_right * dt / METERS_PER_TICK_NOMINAL

                self.total_ticks_left += delta_ticks_left
                self.total_ticks_right += delta_ticks_right

        self.last_odom_time = now

    def reset_ticks(self):
        """Setzt Tick-Zaehler zurueck."""
        self.total_ticks_left = 0.0
        self.total_ticks_right = 0.0

    def wait_for_odom(self, timeout_s=10.0):
        """Wartet bis erste Odometrie empfangen wird."""
        start = time.time()
        while not self.odom_received:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start > timeout_s:
                self.get_logger().error(
                    f"Timeout: Keine /odom nach {timeout_s}s empfangen.")
                return False
        self.get_logger().info("/odom empfangen.")
        return True


# ===========================================================================
# Test-Modi
# ===========================================================================

def run_10_rev_test(node):
    """10-Umdrehungen-Test: Bestimmt TICKS_PER_REV fuer beide Raeder."""
    print("\n" + "=" * 60)
    print("  10-UMDREHUNGEN-TEST")
    print("=" * 60)
    print("  Drehe ein Rad manuell genau 10 Umdrehungen.")
    print("  Das Skript zaehlt die Ticks ueber die Odometrie.")
    print("  Es werden 3 Durchgaenge fuer jedes Rad durchgefuehrt.\n")

    results_left = []
    results_right = []

    for rad_name, results_list in [("LINKS", results_left),
                                    ("RECHTS", results_right)]:
        print(f"\n--- Rad {rad_name} ---")

        for durchgang in range(1, 4):
            print(f"\n  Durchgang {durchgang}/3:")
            input(f"  Bereit? Rad {rad_name} auf Startposition. [Enter]")

            node.reset_ticks()
            node.recording = True

            print("  Aufzeichnung laeuft... Drehe jetzt 10 Umdrehungen.")
            print("  Druecke [Enter] wenn fertig.")

            # Spin waehrend der Aufzeichnung
            try:
                while True:
                    rclpy.spin_once(node, timeout_sec=0.05)
                    ticks_l = abs(node.total_ticks_left)
                    ticks_r = abs(node.total_ticks_right)

                    # Aktuelle Tick-Anzeige (ueberschreibe Zeile)
                    sys.stdout.write(
                        f"\r  Ticks: L={ticks_l:.1f}  R={ticks_r:.1f}  "
                        f"(v_L={node.last_v_left:.4f} m/s, "
                        f"v_R={node.last_v_right:.4f} m/s)    ")
                    sys.stdout.flush()

                    # Pruefen ob Enter gedrueckt (non-blocking)
                    import select
                    if select.select([sys.stdin], [], [], 0.0)[0]:
                        sys.stdin.readline()
                        break
            except KeyboardInterrupt:
                print("\n  Abgebrochen.")
                node.recording = False
                return None

            node.recording = False
            print()

            if rad_name == "LINKS":
                total_ticks = abs(node.total_ticks_left)
            else:
                total_ticks = abs(node.total_ticks_right)

            ticks_per_rev = total_ticks / 10.0 if total_ticks > 0 else 0.0

            print(f"  Ergebnis: {total_ticks:.1f} Ticks gesamt, "
                  f"{ticks_per_rev:.1f} Ticks/Rev")
            results_list.append(ticks_per_rev)

    # Auswertung
    print("\n" + "=" * 60)
    print("  AUSWERTUNG 10-UMDREHUNGEN-TEST")
    print("=" * 60)

    for rad_name, results_list in [("LINKS", results_left),
                                    ("RECHTS", results_right)]:
        if not results_list:
            continue

        mittelwert = sum(results_list) / len(results_list)
        abweichung = max(results_list) - min(results_list)

        print(f"\n  Rad {rad_name}:")
        for i, val in enumerate(results_list, 1):
            print(f"    Durchgang {i}: {val:.1f} Ticks/Rev")
        print(f"    Mittelwert:   {mittelwert:.1f} Ticks/Rev")
        print(f"    Spannweite:   {abweichung:.1f} Ticks")

        # Akzeptanzkriterien
        in_range = TICKS_PER_REV_MIN <= mittelwert <= TICKS_PER_REV_MAX
        reproducible = abweichung <= REPRODUCIBILITY_MAX_TICKS

        if in_range:
            print(f"    Bereich [{TICKS_PER_REV_MIN}-{TICKS_PER_REV_MAX}]: "
                  f"\033[32mPASS\033[0m")
        else:
            print(f"    Bereich [{TICKS_PER_REV_MIN}-{TICKS_PER_REV_MAX}]: "
                  f"\033[31mFAIL\033[0m")

        if reproducible:
            print(f"    Reproduzierbarkeit (<{REPRODUCIBILITY_MAX_TICKS}): "
                  f"\033[32mPASS\033[0m")
        else:
            print(f"    Reproduzierbarkeit (<{REPRODUCIBILITY_MAX_TICKS}): "
                  f"\033[31mFAIL\033[0m")

    return {
        "left": results_left,
        "right": results_right,
    }


def run_direction_test(node):
    """Prueft Vorzeichenkonvention: Vorwaerts=positiv, Rueckwaerts=negativ."""
    print("\n" + "=" * 60)
    print("  RICHTUNGSTEST")
    print("=" * 60)
    print("  Prueft ob Vorwaerts=positiv und Rueckwaerts=negativ.")
    print("  Drehe ein Rad manuell in die jeweilige Richtung.\n")

    results = {}

    for richtung, soll_vorzeichen in [("VORWAERTS", "positiv"),
                                       ("RUECKWAERTS", "negativ")]:
        input(f"  Drehe beide Raeder {richtung}. [Enter] zum Starten...")

        node.reset_ticks()
        node.recording = True

        print("  Aufzeichnung (3 Sekunden)...")
        start = time.time()
        while time.time() - start < 3.0:
            rclpy.spin_once(node, timeout_sec=0.05)
            sys.stdout.write(
                f"\r  v_L={node.last_v_left:+.4f}  "
                f"v_R={node.last_v_right:+.4f}  "
                f"ticks_L={node.total_ticks_left:+.1f}  "
                f"ticks_R={node.total_ticks_right:+.1f}    ")
            sys.stdout.flush()

        node.recording = False
        print()

        v_l_sign = "positiv" if node.total_ticks_left > 0 else "negativ"
        v_r_sign = "positiv" if node.total_ticks_right > 0 else "negativ"

        ok_l = (v_l_sign == soll_vorzeichen) or abs(node.total_ticks_left) < 1
        ok_r = (v_r_sign == soll_vorzeichen) or abs(node.total_ticks_right) < 1

        print(f"  {richtung}: Links={v_l_sign} ({'OK' if ok_l else 'FALSCH'}), "
              f"Rechts={v_r_sign} ({'OK' if ok_r else 'FALSCH'})")

        results[richtung.lower()] = {
            "ticks_left": node.total_ticks_left,
            "ticks_right": node.total_ticks_right,
            "sign_left_ok": ok_l,
            "sign_right_ok": ok_r,
        }

    return results


def run_asymmetry_test(node):
    """Vergleicht Tick-Rate beider Raeder bei gleicher Ansteuerung."""
    print("\n" + "=" * 60)
    print("  ASYMMETRIE-TEST")
    print("=" * 60)
    print("  Beide Raeder sollten bei gleicher PWM aehnliche Tick-Raten")
    print("  erzeugen. Drehe beide Raeder gleichzeitig vorwaerts.\n")

    input("  Bereit? [Enter] zum Starten (5 Sekunden Aufzeichnung)...")

    node.reset_ticks()
    node.recording = True

    start = time.time()
    while time.time() - start < 5.0:
        rclpy.spin_once(node, timeout_sec=0.05)
        elapsed = time.time() - start
        tps_l = abs(node.total_ticks_left) / elapsed if elapsed > 0 else 0
        tps_r = abs(node.total_ticks_right) / elapsed if elapsed > 0 else 0
        sys.stdout.write(
            f"\r  Ticks/s: L={tps_l:.1f}  R={tps_r:.1f}  "
            f"Diff={abs(tps_l - tps_r):.1f}    ")
        sys.stdout.flush()

    node.recording = False
    print()

    total_l = abs(node.total_ticks_left)
    total_r = abs(node.total_ticks_right)

    if total_l > 0 and total_r > 0:
        asymmetrie = abs(total_l - total_r) / max(total_l, total_r) * 100.0
    else:
        asymmetrie = 0.0

    print(f"\n  Gesamt-Ticks: Links={total_l:.1f}, Rechts={total_r:.1f}")
    print(f"  Asymmetrie: {asymmetrie:.1f}%")

    if asymmetrie < 5.0:
        print(f"  Bewertung: \033[32mGUT (< 5%)\033[0m")
    elif asymmetrie < 10.0:
        print(f"  Bewertung: \033[33mAKZEPTABEL (5-10%)\033[0m")
    else:
        print(f"  Bewertung: \033[31mSCHLECHT (> 10%)\033[0m")

    return {
        "total_ticks_left": total_l,
        "total_ticks_right": total_r,
        "asymmetrie_prozent": asymmetrie,
    }


def run_live_display(node):
    """Live-Anzeige der Encoder-Daten."""
    print("\n" + "=" * 60)
    print("  LIVE-ANZEIGE")
    print("=" * 60)
    print("  Zeigt aktuelle Geschwindigkeiten und Tick-Raten an.")
    print("  Beenden mit Ctrl+C.\n")

    node.recording = True
    node.reset_ticks()

    try:
        start = time.time()
        while True:
            rclpy.spin_once(node, timeout_sec=0.05)
            elapsed = time.time() - start

            tps_l = abs(node.total_ticks_left) / elapsed if elapsed > 0.5 else 0
            tps_r = abs(node.total_ticks_right) / elapsed if elapsed > 0.5 else 0

            sys.stdout.write(
                f"\r  v_L={node.last_v_left:+.4f} m/s  "
                f"v_R={node.last_v_right:+.4f} m/s  |  "
                f"Ticks/s: L={tps_l:.1f} R={tps_r:.1f}  |  "
                f"Total: L={node.total_ticks_left:+.0f} "
                f"R={node.total_ticks_right:+.0f}    ")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass

    node.recording = False
    print("\n  Live-Anzeige beendet.")


# ===========================================================================
# config.h Empfehlungen
# ===========================================================================

def print_config_recommendations(rev_results):
    """Gibt empfohlene config.h-Werte aus."""
    if rev_results is None:
        return

    print("\n" + "=" * 60)
    print("  EMPFOHLENE config.h WERTE")
    print("=" * 60)

    left_vals = rev_results.get("left", [])
    right_vals = rev_results.get("right", [])

    if left_vals:
        avg_left = sum(left_vals) / len(left_vals)
        print(f"  #define TICKS_PER_REV_LEFT  {avg_left:.1f}f")
    if right_vals:
        avg_right = sum(right_vals) / len(right_vals)
        print(f"  #define TICKS_PER_REV_RIGHT {avg_right:.1f}f")
    if left_vals and right_vals:
        avg_total = (avg_left + avg_right) / 2.0
        mpt_left = WHEEL_CIRCUMFERENCE / avg_left
        mpt_right = WHEEL_CIRCUMFERENCE / avg_right
        print(f"  // TICKS_PER_REV = {avg_total:.1f}")
        print(f"  // METERS_PER_TICK_LEFT  = {mpt_left:.6f} m/tick")
        print(f"  // METERS_PER_TICK_RIGHT = {mpt_right:.6f} m/tick")
    print()


# ===========================================================================
# Protokoll speichern
# ===========================================================================

def save_results(rev_results, direction_results, asymmetry_results):
    """Speichert alle Ergebnisse als JSON-Datei."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "config": {
            "wheel_diameter_m": WHEEL_DIAMETER,
            "wheel_base_m": WHEEL_BASE,
            "wheel_circumference_m": WHEEL_CIRCUMFERENCE,
            "nominal_ticks_per_rev": TICKS_PER_REV_NOMINAL,
        },
        "10_rev_test": rev_results,
        "direction_test": direction_results,
        "asymmetry_test": asymmetry_results,
    }

    # Empfohlene Werte berechnen
    if rev_results:
        left_vals = rev_results.get("left", [])
        right_vals = rev_results.get("right", [])
        if left_vals:
            data["recommended_ticks_per_rev_left"] = sum(left_vals) / len(left_vals)
        if right_vals:
            data["recommended_ticks_per_rev_right"] = sum(right_vals) / len(right_vals)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "encoder_results.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Ergebnisse gespeichert: {filepath}")
    return filepath


# ===========================================================================
# Hauptprogramm
# ===========================================================================

def print_menu():
    """Zeigt das Hauptmenue an."""
    print("\n" + "-" * 40)
    print("  Encoder-Test-Modi:")
    print("  1) 10-Umdrehungen-Test (Kalibrierung)")
    print("  2) Richtungstest (Vorzeichenkonvention)")
    print("  3) Asymmetrie-Test (Links vs. Rechts)")
    print("  4) Live-Anzeige")
    print("  5) Ergebnisse speichern und beenden")
    print("  q) Beenden ohne Speichern")
    print("-" * 40)


def main(args=None):
    rclpy.init(args=args)

    print()
    print("*" * 60)
    print("  AMR Encoder-Kalibrierungstool")
    print("  ROS2-Node: encoder_test_node")
    print(f"  Zeitpunkt: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("*" * 60)

    node = EncoderTestNode()

    # Auf erste /odom-Nachricht warten
    print("\n  Warte auf /odom (micro-ROS Agent muss laufen)...")
    if not node.wait_for_odom(timeout_s=15.0):
        print("  FEHLER: /odom nicht empfangen. Ist der micro-ROS Agent aktiv?")
        print("  Starte mit: ros2 run micro_ros_agent micro_ros_agent serial "
              "--dev /dev/ttyACM0")
        node.destroy_node()
        rclpy.shutdown()
        return 1

    rev_results = None
    direction_results = None
    asymmetry_results = None

    try:
        while True:
            print_menu()
            choice = input("  Auswahl: ").strip().lower()

            if choice == "1":
                rev_results = run_10_rev_test(node)
                if rev_results:
                    print_config_recommendations(rev_results)
            elif choice == "2":
                direction_results = run_direction_test(node)
            elif choice == "3":
                asymmetry_results = run_asymmetry_test(node)
            elif choice == "4":
                run_live_display(node)
            elif choice == "5":
                save_results(rev_results, direction_results, asymmetry_results)
                break
            elif choice == "q":
                print("  Beendet ohne Speichern.")
                break
            else:
                print("  Ungueltige Eingabe.")
    except KeyboardInterrupt:
        print("\n\n  Abgebrochen. Speichere Ergebnisse...")
        save_results(rev_results, direction_results, asymmetry_results)

    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
