#!/usr/bin/env python3
"""
Kinematik-Verifikationstest fuer AMR-Differentialantrieb.

ROS2-Node, die drei Tests durchfuehrt:
  a) Geradeausfahrt 1 m
  b) 90-Grad-Drehung (5x CW, 5x CCW)
  c) Kreisfahrt (1 volle Umdrehung)

Zeichnet Odometrie auf, berechnet Abweichungen und gibt Markdown-Protokoll + JSON aus.

Voraussetzung: ROS2 Humble, micro-ROS Agent laeuft, Roboter bereit.

Verwendung:
    python3 kinematic_test.py              # Alle Tests
    python3 kinematic_test.py gerade       # Nur Geradeausfahrt
    python3 kinematic_test.py drehung      # Nur 90-Grad-Drehungen
    python3 kinematic_test.py kreis        # Nur Kreisfahrt
"""

import sys
import time
import json
import math
from pathlib import Path

import numpy as np

try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
except ImportError:
    print("Fehler: ROS2 (rclpy) nicht verfuegbar.")
    print("Bitte ROS2 Humble installieren und workspace sourcen.")
    sys.exit(1)


# ===========================================================================
# Roboter-Parameter (aus hardware/config.h)
# ===========================================================================
from amr_utils import WHEEL_RADIUS, WHEEL_BASE, quaternion_zu_yaw, normalisiere_winkel

# Odom- und cmd_vel-Topics
ODOM_TOPIC = "/odom"
CMD_VEL_TOPIC = "/cmd_vel"

# Akzeptanzkriterien
AKZEPTANZ_STRECKE_PCT = 5.0     # [%] Streckenabweichung
AKZEPTANZ_DRIFT_M = 0.05        # [m] Laterale Drift
AKZEPTANZ_WINKEL_DEG = 5.0      # [Grad] Winkelabweichung

# Pause zwischen Tests [s]
PAUSE_ZWISCHEN_TESTS = 3.0
# Pause nach Stopp fuer Odometrie-Einschwingen [s]
PAUSE_NACH_STOPP = 1.0



class KinematikTestNode(Node):
    """ROS2-Node fuer Kinematik-Verifikationstests."""

    def __init__(self):
        super().__init__("kinematik_test")
        self.publisher = self.create_publisher(Twist, CMD_VEL_TOPIC, 10)
        self.subscription = self.create_subscription(
            Odometry, ODOM_TOPIC, self.odom_callback, 10
        )
        self.letzte_odom = None
        self.odom_aufnahme = []
        self.aufnahme_aktiv = False

    def odom_callback(self, msg):
        """Speichert aktuelle Odometrie-Nachricht."""
        self.letzte_odom = msg
        if self.aufnahme_aktiv:
            self.odom_aufnahme.append(msg)

    def warte_auf_odom(self, timeout=5.0):
        """Wartet bis eine Odometrie-Nachricht empfangen wird."""
        t0 = time.time()
        while self.letzte_odom is None and (time.time() - t0) < timeout:
            rclpy.spin_once(self, timeout_sec=0.05)
        if self.letzte_odom is None:
            print("Fehler: Keine Odometrie empfangen. Ist der micro-ROS Agent aktiv?")
            return False
        return True

    def hole_position(self):
        """Gibt aktuelle (x, y, yaw) Position zurueck."""
        rclpy.spin_once(self, timeout_sec=0.05)
        if self.letzte_odom is None:
            return None
        pos = self.letzte_odom.pose.pose.position
        ori = self.letzte_odom.pose.pose.orientation
        yaw = quaternion_zu_yaw(ori)
        return (pos.x, pos.y, yaw)

    def sende_cmd_vel(self, v_linear, v_angular):
        """Sendet cmd_vel Twist-Nachricht."""
        twist = Twist()
        twist.linear.x = float(v_linear)
        twist.angular.z = float(v_angular)
        self.publisher.publish(twist)

    def stopp(self):
        """Sendet Stopp-Befehl."""
        self.sende_cmd_vel(0.0, 0.0)

    def fahre_dauer(self, v_linear, v_angular, dauer_s):
        """Faehrt mit gegebener Geschwindigkeit fuer gegebene Dauer.

        Sendet cmd_vel alle 100 ms (innerhalb Failsafe-Timeout von 500 ms).
        """
        self.odom_aufnahme = []
        self.aufnahme_aktiv = True

        t_start = time.time()
        while (time.time() - t_start) < dauer_s:
            self.sende_cmd_vel(v_linear, v_angular)
            rclpy.spin_once(self, timeout_sec=0.05)
            time.sleep(0.05)  # ~20 Hz Senderate

        self.stopp()
        self.aufnahme_aktiv = False

        # Kurz warten fuer letzte Odometrie-Updates
        t_warte = time.time()
        while (time.time() - t_warte) < PAUSE_NACH_STOPP:
            rclpy.spin_once(self, timeout_sec=0.05)


# ===========================================================================
# Test a) Geradeausfahrt 1 m
# ===========================================================================
def test_geradeausfahrt(node):
    """Geradeausfahrt: v=0.2 m/s, omega=0, Dauer=5 s (= 1 m).

    Bewertet: Streckenabweichung, laterale Drift.
    """
    print()
    print("=" * 60)
    print("Test A: Geradeausfahrt 1 m")
    print("=" * 60)

    v = 0.2       # [m/s]
    dauer = 5.0   # [s] -> 1 m Soll-Strecke
    soll_strecke = v * dauer  # 1.0 m

    pos_start = node.hole_position()
    if pos_start is None:
        print("Fehler: Keine Startposition verfuegbar.")
        return None
    print(f"  Start: x={pos_start[0]:.4f} m, y={pos_start[1]:.4f} m, yaw={math.degrees(pos_start[2]):.2f} deg")

    print(f"  Fahre: v={v} m/s, omega=0, Dauer={dauer} s")
    node.fahre_dauer(v, 0.0, dauer)

    pos_end = node.hole_position()
    print(f"  Ende:  x={pos_end[0]:.4f} m, y={pos_end[1]:.4f} m, yaw={math.degrees(pos_end[2]):.2f} deg")

    # Berechnung in lokalen Koordinaten (Start als Ursprung)
    dx = pos_end[0] - pos_start[0]
    dy = pos_end[1] - pos_start[1]
    yaw_start = pos_start[2]

    # Transformation in Startframe
    d_vorwaerts = dx * math.cos(yaw_start) + dy * math.sin(yaw_start)
    d_lateral = -dx * math.sin(yaw_start) + dy * math.cos(yaw_start)

    strecke_fehler_pct = abs(d_vorwaerts - soll_strecke) / soll_strecke * 100.0
    drift_m = abs(d_lateral)

    ergebnis = {
        "test": "Geradeausfahrt",
        "soll_strecke_m": soll_strecke,
        "ist_vorwaerts_m": d_vorwaerts,
        "strecke_fehler_pct": strecke_fehler_pct,
        "laterale_drift_m": drift_m,
        "strecke_ok": strecke_fehler_pct < AKZEPTANZ_STRECKE_PCT,
        "drift_ok": drift_m < AKZEPTANZ_DRIFT_M,
        "start": list(pos_start),
        "ende": list(pos_end),
    }

    # Sofortige Ausgabe
    print()
    print(f"  Vorwaerts-Strecke: {d_vorwaerts:.4f} m (Soll: {soll_strecke} m, Fehler: {strecke_fehler_pct:.2f}%)")
    print(f"  Laterale Drift:    {drift_m:.4f} m (Akzeptanz: < {AKZEPTANZ_DRIFT_M} m)")
    print(f"  Bewertung: Strecke {'OK' if ergebnis['strecke_ok'] else 'NICHT OK'}, "
          f"Drift {'OK' if ergebnis['drift_ok'] else 'NICHT OK'}")

    return ergebnis


# ===========================================================================
# Test b) 90-Grad-Drehung
# ===========================================================================
def test_drehung(node):
    """90-Grad-Drehung: v=0, omega=pi/2, Dauer=1 s. 5x CW, 5x CCW.

    Bewertet: Winkelabweichung, CW/CCW-Asymmetrie.
    """
    print()
    print("=" * 60)
    print("Test B: 90-Grad-Drehung (5x CW, 5x CCW)")
    print("=" * 60)

    omega = math.pi / 2.0  # [rad/s]
    dauer = 1.0            # [s] -> 90 Grad
    soll_winkel = 90.0     # [Grad]

    ergebnisse_cw = []
    ergebnisse_ccw = []

    # 5x CW (positive omega -> CCW in ROS, negative -> CW)
    # ROS-Konvention: positive omega = links (CCW von oben), negative = rechts (CW)
    print()
    print("  --- CW-Drehungen (5x) ---")
    for i in range(5):
        pos_start = node.hole_position()
        if pos_start is None:
            print(f"    CW {i+1}: Fehler - keine Position")
            continue

        node.fahre_dauer(0.0, -omega, dauer)  # Negativ = CW

        pos_end = node.hole_position()
        delta_yaw = normalisiere_winkel(pos_end[2] - pos_start[2])
        ist_winkel = abs(math.degrees(delta_yaw))
        fehler = ist_winkel - soll_winkel

        ergebnisse_cw.append({
            "lauf": i + 1,
            "ist_winkel_deg": ist_winkel,
            "fehler_deg": fehler,
            "start_yaw_deg": math.degrees(pos_start[2]),
            "end_yaw_deg": math.degrees(pos_end[2]),
        })
        print(f"    CW {i+1}: {ist_winkel:.2f} deg (Fehler: {fehler:+.2f} deg)")
        time.sleep(PAUSE_ZWISCHEN_TESTS)

    # 5x CCW
    print()
    print("  --- CCW-Drehungen (5x) ---")
    for i in range(5):
        pos_start = node.hole_position()
        if pos_start is None:
            print(f"    CCW {i+1}: Fehler - keine Position")
            continue

        node.fahre_dauer(0.0, omega, dauer)  # Positiv = CCW

        pos_end = node.hole_position()
        delta_yaw = normalisiere_winkel(pos_end[2] - pos_start[2])
        ist_winkel = abs(math.degrees(delta_yaw))
        fehler = ist_winkel - soll_winkel

        ergebnisse_ccw.append({
            "lauf": i + 1,
            "ist_winkel_deg": ist_winkel,
            "fehler_deg": fehler,
            "start_yaw_deg": math.degrees(pos_start[2]),
            "end_yaw_deg": math.degrees(pos_end[2]),
        })
        print(f"    CCW {i+1}: {ist_winkel:.2f} deg (Fehler: {fehler:+.2f} deg)")
        time.sleep(PAUSE_ZWISCHEN_TESTS)

    # Auswertung
    cw_winkel = [e["ist_winkel_deg"] for e in ergebnisse_cw]
    ccw_winkel = [e["ist_winkel_deg"] for e in ergebnisse_ccw]

    if cw_winkel and ccw_winkel:
        mittel_cw = np.mean(cw_winkel)
        mittel_ccw = np.mean(ccw_winkel)
        asymmetrie = abs(mittel_cw - mittel_ccw)
        max_fehler = max(abs(np.mean(cw_winkel) - soll_winkel),
                         abs(np.mean(ccw_winkel) - soll_winkel))
    else:
        mittel_cw = 0
        mittel_ccw = 0
        asymmetrie = 0
        max_fehler = float('nan')

    ergebnis = {
        "test": "90-Grad-Drehung",
        "soll_winkel_deg": soll_winkel,
        "cw": ergebnisse_cw,
        "ccw": ergebnisse_ccw,
        "mittel_cw_deg": mittel_cw,
        "mittel_ccw_deg": mittel_ccw,
        "asymmetrie_deg": asymmetrie,
        "max_fehler_deg": max_fehler,
        "winkel_ok": max_fehler < AKZEPTANZ_WINKEL_DEG,
    }

    print()
    print(f"  Mittel CW:  {mittel_cw:.2f} deg")
    print(f"  Mittel CCW: {mittel_ccw:.2f} deg")
    print(f"  Asymmetrie: {asymmetrie:.2f} deg")
    print(f"  Max. Fehler: {max_fehler:.2f} deg (Akzeptanz: < {AKZEPTANZ_WINKEL_DEG} deg)")
    print(f"  Bewertung: {'OK' if ergebnis['winkel_ok'] else 'NICHT OK'}")

    return ergebnis


# ===========================================================================
# Test c) Kreisfahrt
# ===========================================================================
def test_kreisfahrt(node):
    """Kreisfahrt: v=0.2 m/s, omega=0.5 rad/s (Radius=0.4 m), 1 volle Umdrehung.

    Bewertet: Endposition vs. Startposition.
    """
    print()
    print("=" * 60)
    print("Test C: Kreisfahrt (1 volle Umdrehung)")
    print("=" * 60)

    v = 0.2         # [m/s]
    omega = 0.5     # [rad/s]
    radius = v / omega  # 0.4 m
    umfang = 2.0 * math.pi * radius
    dauer = umfang / v  # Zeit fuer 1 Umdrehung

    print(f"  Parameter: v={v} m/s, omega={omega} rad/s")
    print(f"  Radius: {radius:.3f} m, Umfang: {umfang:.3f} m")
    print(f"  Dauer: {dauer:.2f} s")

    pos_start = node.hole_position()
    if pos_start is None:
        print("Fehler: Keine Startposition verfuegbar.")
        return None
    print(f"  Start: x={pos_start[0]:.4f} m, y={pos_start[1]:.4f} m, yaw={math.degrees(pos_start[2]):.2f} deg")

    node.fahre_dauer(v, omega, dauer)

    pos_end = node.hole_position()
    print(f"  Ende:  x={pos_end[0]:.4f} m, y={pos_end[1]:.4f} m, yaw={math.degrees(pos_end[2]):.2f} deg")

    # Positionsfehler (Endposition vs. Startposition)
    dx = pos_end[0] - pos_start[0]
    dy = pos_end[1] - pos_start[1]
    positions_fehler = math.sqrt(dx**2 + dy**2)

    # Winkelfehler (soll: 360 Grad = 0 Grad relativ)
    delta_yaw = normalisiere_winkel(pos_end[2] - pos_start[2])
    winkel_fehler = abs(math.degrees(delta_yaw))

    # Kreisradius aus Trajektorie schaetzen
    if len(node.odom_aufnahme) > 2:
        xs = [m.pose.pose.position.x for m in node.odom_aufnahme]
        ys = [m.pose.pose.position.y for m in node.odom_aufnahme]
        cx = np.mean(xs)
        cy = np.mean(ys)
        radien = [math.sqrt((x - cx)**2 + (y - cy)**2) for x, y in zip(xs, ys)]
        ist_radius = np.mean(radien)
        radius_fehler_pct = abs(ist_radius - radius) / radius * 100.0
    else:
        ist_radius = float('nan')
        radius_fehler_pct = float('nan')

    # Akzeptanzkriterium: Kreisradius-Fehler < 20%
    AKZEPTANZ_RADIUS_PCT = 20.0
    passed = (not math.isnan(radius_fehler_pct)
              and radius_fehler_pct < AKZEPTANZ_RADIUS_PCT)

    ergebnis = {
        "test": "Kreisfahrt",
        "radius_m": radius,
        "ist_radius_m": float(ist_radius),
        "radius_fehler_pct": float(radius_fehler_pct),
        "dauer_s": dauer,
        "positions_fehler_m": positions_fehler,
        "winkel_fehler_deg": winkel_fehler,
        "dx_m": dx,
        "dy_m": dy,
        "start": list(pos_start),
        "ende": list(pos_end),
        "passed": passed,
    }

    print()
    print(f"  Positionsfehler (dx,dy): ({dx:.4f}, {dy:.4f}) m")
    print(f"  Positionsfehler (abs):   {positions_fehler:.4f} m")
    print(f"  Winkelfehler:            {winkel_fehler:.2f} deg")
    if not math.isnan(ist_radius):
        print(f"  Kreisradius (soll):      {radius:.3f} m")
        print(f"  Kreisradius (ist):       {ist_radius:.3f} m")
        print(f"  Radius-Fehler:           {radius_fehler_pct:.1f}% (Akzeptanz: < {AKZEPTANZ_RADIUS_PCT}%)")
    print(f"  Bewertung: {'OK' if passed else 'NICHT OK'}")

    return ergebnis


# ===========================================================================
# Ergebnis-Ausgabe
# ===========================================================================
def ausgabe_protokoll(ergebnisse):
    """Gibt das Gesamtprotokoll als Markdown-Tabelle aus."""
    print()
    print()
    print("=" * 70)
    print("Kinematik-Verifikationsprotokoll")
    print("=" * 70)
    print()

    for erg in ergebnisse:
        if erg is None:
            continue

        if erg["test"] == "Geradeausfahrt":
            print("### Test A: Geradeausfahrt 1 m")
            print()
            print("| Kenngroesse          | Wert          | Akzeptanz        | Bewertung |")
            print("|:--------------------|:--------------|:-----------------|:----------|")
            print(f"| Streckenabweichung  | {erg['strecke_fehler_pct']:.2f} %       | < {AKZEPTANZ_STRECKE_PCT} %           | {'OK' if erg['strecke_ok'] else 'NICHT OK':9s} |")
            print(f"| Laterale Drift      | {erg['laterale_drift_m']*1000:.1f} mm      | < {AKZEPTANZ_DRIFT_M*1000:.0f} mm          | {'OK' if erg['drift_ok'] else 'NICHT OK':9s} |")
            print()

        elif erg["test"] == "90-Grad-Drehung":
            print("### Test B: 90-Grad-Drehung")
            print()
            print("| Lauf | CW [deg] | CCW [deg] |")
            print("|:-----|:---------|:----------|")
            for i in range(5):
                cw_str = f"{erg['cw'][i]['ist_winkel_deg']:.2f}" if i < len(erg['cw']) else "N/A"
                ccw_str = f"{erg['ccw'][i]['ist_winkel_deg']:.2f}" if i < len(erg['ccw']) else "N/A"
                print(f"|  {i+1}   | {cw_str:8s} | {ccw_str:9s} |")
            print()
            print(f"| Mittelwert CW:  {erg['mittel_cw_deg']:.2f} deg |")
            print(f"| Mittelwert CCW: {erg['mittel_ccw_deg']:.2f} deg |")
            print(f"| Asymmetrie:     {erg['asymmetrie_deg']:.2f} deg |")
            print(f"| Bewertung:      {'OK' if erg['winkel_ok'] else 'NICHT OK'} (Akzeptanz: < {AKZEPTANZ_WINKEL_DEG} deg) |")
            print()

        elif erg["test"] == "Kreisfahrt":
            print("### Test C: Kreisfahrt")
            print()
            print("| Kenngroesse         | Wert        |")
            print("|:-------------------|:------------|")
            print(f"| Radius (soll)      | {erg['radius_m']:.3f} m    |")
            print(f"| Positionsfehler    | {erg['positions_fehler_m']*1000:.1f} mm   |")
            print(f"| Winkelfehler       | {erg['winkel_fehler_deg']:.2f} deg |")
            print()


def speichere_json(ergebnisse, pfad):
    """Speichert Ergebnisse als JSON-Datei."""
    # numpy-Typen konvertieren
    def konvertiere(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    sauber = json.loads(json.dumps(ergebnisse, default=konvertiere))

    with open(pfad, "w") as f:
        json.dump(sauber, f, indent=2, ensure_ascii=False)
    print(f"JSON-Export: {pfad}")


def main():
    """Hauptprogramm: Tests durchfuehren, Protokoll ausgeben."""
    # Verfuegbare Tests
    alle_tests = {"gerade", "drehung", "kreis"}

    # Zu ausfuehrende Tests bestimmen
    if len(sys.argv) > 1:
        auswahl = sys.argv[1].lower()
        if auswahl not in alle_tests:
            print(f"Fehler: Unbekannter Test '{auswahl}'")
            print(f"Verfuegbar: {', '.join(sorted(alle_tests))}")
            sys.exit(1)
        tests = [auswahl]
    else:
        tests = ["gerade", "drehung", "kreis"]

    # ROS2 initialisieren
    rclpy.init()
    node = KinematikTestNode()

    print("Kinematik-Verifikationstest")
    print(f"  WHEEL_RADIUS = {WHEEL_RADIUS} m")
    print(f"  WHEEL_BASE = {WHEEL_BASE} m")
    print()
    print("Warte auf Odometrie...")
    if not node.warte_auf_odom():
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)
    print("Odometrie empfangen. Tests starten.")

    ergebnisse = []

    try:
        if "gerade" in tests:
            erg = test_geradeausfahrt(node)
            ergebnisse.append(erg)
            if len(tests) > 1:
                print(f"\n  Pause {PAUSE_ZWISCHEN_TESTS:.0f} s...")
                time.sleep(PAUSE_ZWISCHEN_TESTS)

        if "drehung" in tests:
            erg = test_drehung(node)
            ergebnisse.append(erg)
            if "kreis" in tests:
                print(f"\n  Pause {PAUSE_ZWISCHEN_TESTS:.0f} s...")
                time.sleep(PAUSE_ZWISCHEN_TESTS)

        if "kreis" in tests:
            erg = test_kreisfahrt(node)
            ergebnisse.append(erg)

    except KeyboardInterrupt:
        print("\nTest abgebrochen durch Benutzer.")
        node.stopp()
    finally:
        node.stopp()

    # Protokoll ausgeben
    ausgabe_protokoll(ergebnisse)

    # JSON speichern
    skript_verzeichnis = Path(__file__).parent
    json_pfad = skript_verzeichnis / "kinematic_results.json"
    speichere_json(ergebnisse, json_pfad)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
