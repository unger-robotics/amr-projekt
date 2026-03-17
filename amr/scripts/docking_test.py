#!/usr/bin/env python3
"""
Docking-Validierungstest fuer AMR.

Fuehrt 10 Docking-Versuche durch und protokolliert Erfolgsquote,
lateralen Versatz und Orientierungsfehler.

Ablauf pro Versuch:
  1. Benutzer positioniert Roboter manuell (~1.5 m vor Marker)
  2. Kamera erkennt ArUco-Marker und steuert Roboter darauf zu
  3. DOCKED sobald Ultraschall <= 0.30 m misst, Roboter stoppt
  4. Ergebnis messen (lateraler Versatz via solvePnP, Orientierung)
  5. Roboter faehrt 3 s rueckwaerts zur Ausgangsposition

Zustaende:
  SEARCHING   — Marker nicht sichtbar, Roboter dreht sich um Hochachse suchend.
                Nach Ruecksetzen wegen Fehlausrichtung ebenfalls SEARCHING.
  APPROACHING — Marker sichtbar, Kamera steuert Richtung, Roboter faehrt vor.
                Bei kurzem Marker-Verlust: Drehung um Hochachse bis Marker
                wieder sichtbar, dann geradeaus weiter.
  DOCKED      — Dreifach-Bedingung erfuellt: Ultraschall <= 0.30 m UND
                Marker aktuell sichtbar UND lateraler Versatz <= 5 cm.
                Roboter stoppt (Erfolg).
  TIMEOUT     — 60 s ohne Docking (Fehlschlag)

Fehlausrichtungs-Recovery:
  Wenn Ultraschall nah aber Marker nicht sichtbar oder Versatz > 5 cm:
  Roboter setzt 1.5 s zurueck, wechselt zu SEARCHING, dreht um Hochachse
  bis Marker wieder per Kamera erkannt wird, dann erneute Anfahrt.

Topics:
  - Subscribes: /camera/image_raw, /odom, /range/front
  - Publishes:  /cmd_vel

Ergebnis: Markdown-Tabelle + JSON-Export (docking_results.json)
"""

import argparse
import json
import math
import os
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image, Range

from amr_utils import quaternion_to_yaw

# ArUco-Marker physische Groesse [m] — muss mit gedrucktem Marker uebereinstimmen
MARKER_SIZE_M = 0.10  # 10 cm Seitenlaenge (DICT_4X4_50, ID 0)

# Kamerakalibrierung (IMX296 640x480, aus amr_camera.yaml)
CAMERA_MATRIX = np.array(
    [[864.435907, 0.0, 309.080247], [0.0, 862.648938, 263.741198], [0.0, 0.0, 1.0]]
)
DIST_COEFFS = np.array([-0.573493, 1.144172, -0.009577, -0.000665, -3.194487])

# Akzeptanzkriterium lateraler Versatz
VERSATZ_AKZEPTANZ_CM = 2.0

# Maximaler lateraler Versatz fuer Docking-Akzeptanz waehrend Anfahrt [cm]
# Wenn Ultraschall nah aber Versatz groesser: zuruecksetzen + neu ausrichten
DOCKING_VERSATZ_MAX_CM = 5.0


class DockingTestNode(Node):
    """Fuehrt wiederholte Docking-Tests durch und sammelt Ergebnisse."""

    SEARCHING = "SEARCHING"
    APPROACHING = "APPROACHING"
    DOCKED = "DOCKED"
    TIMEOUT = "TIMEOUT"

    def __init__(self, output_dir=None):
        super().__init__("docking_test")

        # Ausgabeverzeichnis
        if output_dir is not None:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Publisher / Subscriber
        self.cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.image_sub = self.create_subscription(
            Image, "/camera/image_raw", self.image_callback, 10
        )
        self.odom_sub = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)
        self.range_sub = self.create_subscription(Range, "/range/front", self.range_callback, 10)

        # Steuerungsparameter
        self.bridge = CvBridge()
        self.kp_angular = 0.3
        self.approach_vel = 0.08  # m/s Vorwaertsgeschwindigkeit
        self.search_vel = 0.3  # rad/s Suchrotation
        self.target_marker_id = 0
        self.docking_distance_m = 0.30  # Ultraschall-Distanz fuer DOCKED [m]
        self.timeout_sec = 60.0
        self.marker_lost_timeout = 3.0
        self.num_versuche = 10

        # ArUco Detector (kompatibel mit OpenCV 4.5+)
        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters_create()

        # Test-Zustand
        self.aktueller_versuch = 0
        self.state = self.SEARCHING
        self.versuch_start_time = 0.0
        self.last_marker_time = 0.0
        self.last_marker_center_x = None
        self.last_marker_width = None
        self.last_marker_corners = None
        self.image_width = None
        self.test_aktiv = False
        self.backup_until = 0.0  # Zeitpunkt bis Rueckwaertsfahrt endet

        # Ultraschall-Distanz
        self.range_m = float("inf")

        # Odometrie
        self.odom_yaw = 0.0
        self.odom_yaw_start = 0.0

        # Ergebnisse
        self.ergebnisse = []

        self.get_logger().info(f"Docking-Test bereit. {self.num_versuche} Versuche geplant.")
        self.get_logger().info(f"Ausgabeverzeichnis: {self.output_dir}")
        self.get_logger().info(f"Docking-Distanz: {self.docking_distance_m:.2f} m (Ultraschall)")
        self.get_logger().info('Eingabe "s" + Enter im Terminal startet den naechsten Versuch.')

    def range_callback(self, msg):
        """Speichert aktuelle Ultraschall-Distanz. Werte <= min_range werden ignoriert."""
        val = float(msg.range)
        if val > msg.min_range:
            self.range_m = val

    def odom_callback(self, msg):
        """Speichert aktuelle Gier-Orientierung aus Odometrie."""
        q = msg.pose.pose.orientation
        self.odom_yaw = quaternion_to_yaw(q)

    def _check_docked(self):
        """Prueft Dreifach-Bedingung: Ultraschall nah + Marker sichtbar + Versatz akzeptabel."""
        if self.range_m > self.docking_distance_m:
            return False

        marker_aktuell = self.last_marker_time > 0 and (time.time() - self.last_marker_time) < 0.5

        if marker_aktuell and self.last_marker_corners is not None:
            versatz_cm = self._estimate_lateral_offset_cm(self.last_marker_corners)
            if versatz_cm is not None and abs(versatz_cm) <= DOCKING_VERSATZ_MAX_CM:
                self.state = self.DOCKED
                self.get_logger().info(
                    f"  Versuch {self.aktueller_versuch}: DOCKED "
                    f"(Ultraschall: {self.range_m:.2f} m, Versatz: {versatz_cm:.1f} cm)"
                )
                self.stop_robot()
                self.versuch_abschliessen()
                return True
            else:
                versatz_str = f"{versatz_cm:.1f}" if versatz_cm is not None else "N/A"
                self.get_logger().warning(
                    f"  Versuch {self.aktueller_versuch}: Nah ({self.range_m:.2f} m) "
                    f"aber Versatz {versatz_str} cm -> zuruecksetzen + suchen",
                    throttle_duration_sec=2.0,
                )
                self._backup_and_search()
                return False
        else:
            self.get_logger().warning(
                f"  Versuch {self.aktueller_versuch}: Ultraschall nah ({self.range_m:.2f} m) "
                f"aber Marker nicht sichtbar -> zuruecksetzen + suchen",
                throttle_duration_sec=2.0,
            )
            self._backup_and_search()
            return False

    def _backup_and_search(self):
        """Faehrt 1.5 s rueckwaerts und wechselt in SEARCHING."""
        self.state = self.SEARCHING
        self.backup_until = time.time() + 1.5
        self.last_marker_time = 0.0
        cmd = Twist()
        cmd.linear.x = -self.approach_vel
        self.cmd_pub.publish(cmd)

    def image_callback(self, msg):
        """Verarbeitet Kamerabild waehrend aktivem Docking-Versuch."""
        if not self.test_aktiv:
            return
        if self.state in (self.DOCKED, self.TIMEOUT):
            return

        # Waehrend Rueckwaertsfahrt keine Steuerung
        now = time.time()
        if now < self.backup_until:
            cmd = Twist()
            cmd.linear.x = -self.approach_vel
            self.cmd_pub.publish(cmd)
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().warning(f"CvBridge Fehler: {e}")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.image_width = frame.shape[1]
        img_center_x = self.image_width / 2.0

        corners, ids, _rejected = cv2.aruco.detectMarkers(
            gray, self.aruco_dict, parameters=self.aruco_params
        )

        # Dreifach-Pruefung: Ultraschall nah + Marker sichtbar + Versatz ok
        if self._check_docked():
            return

        cmd = Twist()
        marker_sichtbar = ids is not None and self.target_marker_id in ids.flatten()

        if marker_sichtbar:
            # --- Marker sichtbar: Richtung korrigieren + vorwaerts ---
            index = np.where(ids.flatten() == self.target_marker_id)[0][0]
            c = corners[index][0]

            center_x = np.mean(c[:, 0])
            marker_width = np.max(c[:, 0]) - np.min(c[:, 0])

            self.last_marker_center_x = center_x
            self.last_marker_width = marker_width
            self.last_marker_corners = corners[index]
            self.last_marker_time = now

            error_x = (center_x - img_center_x) / img_center_x

            if self.state == self.SEARCHING:
                self.state = self.APPROACHING
                self.get_logger().info(
                    f"  Versuch {self.aktueller_versuch}: Marker erkannt -> APPROACHING"
                )

            angular_cmd = error_x * self.kp_angular
            cmd.angular.z = angular_cmd
            cmd.linear.x = self.approach_vel
            self.get_logger().info(
                f"  center_x={center_x:.0f} img_center={img_center_x:.0f} "
                f"error_x={error_x:.3f} angular_z={angular_cmd:.3f} "
                f"range={self.range_m:.2f}m width={marker_width:.0f}px",
                throttle_duration_sec=1.0,
            )

        else:
            # --- Kein Marker sichtbar: Drehung um Hochachse suchen ---
            cmd.angular.z = self.search_vel

        self.cmd_pub.publish(cmd)

    def _estimate_lateral_offset_cm(self, corners):
        """Berechnet lateralen Versatz in cm via solvePnP mit Kamerakalibrierung."""
        obj_points = np.array(
            [
                [-MARKER_SIZE_M / 2, MARKER_SIZE_M / 2, 0],
                [MARKER_SIZE_M / 2, MARKER_SIZE_M / 2, 0],
                [MARKER_SIZE_M / 2, -MARKER_SIZE_M / 2, 0],
                [-MARKER_SIZE_M / 2, -MARKER_SIZE_M / 2, 0],
            ],
            dtype=np.float64,
        )
        img_points = corners.reshape(4, 2).astype(np.float64)
        success, rvec, tvec = cv2.solvePnP(obj_points, img_points, CAMERA_MATRIX, DIST_COEFFS)
        if not success:
            return None
        # tvec[0] = lateraler Versatz (x in Kamera-Frame), Meter -> cm
        return float(tvec[0][0]) * 100.0

    def versuch_starten(self):
        """Initialisiert einen neuen Docking-Versuch."""
        self.aktueller_versuch += 1
        self.state = self.SEARCHING
        self.versuch_start_time = time.time()
        self.last_marker_time = 0.0
        self.last_marker_center_x = None
        self.last_marker_width = None
        self.last_marker_corners = None
        self.range_m = float("inf")
        self.odom_yaw_start = self.odom_yaw
        self.backup_until = 0.0
        self.test_aktiv = True

        self.get_logger().info(
            f"--- Versuch {self.aktueller_versuch}/{self.num_versuche} gestartet ---"
        )

        # Watchdog-Timer fuer Timeout und Marker-Verlust
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_callback)

    def watchdog_callback(self):
        """Ueberwacht Timeout und Marker-Verlust fuer aktuellen Versuch."""
        if not self.test_aktiv:
            return
        if self.state in (self.DOCKED, self.TIMEOUT):
            return

        now = time.time()

        # Waehrend Rueckwaertsfahrt: nur Timeout pruefen
        if now < self.backup_until:
            if (now - self.versuch_start_time) > self.timeout_sec:
                self.backup_until = 0.0
                self.state = self.TIMEOUT
                self.get_logger().warning(
                    f"  Versuch {self.aktueller_versuch}: TIMEOUT nach {self.timeout_sec:.0f} s"
                )
                self.stop_robot()
                self.versuch_abschliessen()
            return

        # Ultraschall-Docking pruefen (10 Hz, unabhaengig von Kamera-Framerate)
        if self._check_docked():
            return

        if (now - self.versuch_start_time) > self.timeout_sec:
            self.state = self.TIMEOUT
            self.get_logger().warning(
                f"  Versuch {self.aktueller_versuch}: TIMEOUT nach {self.timeout_sec:.0f} s"
            )
            self.stop_robot()
            self.versuch_abschliessen()
            return

        if self.state == self.APPROACHING and (
            self.last_marker_time > 0 and (now - self.last_marker_time) > self.marker_lost_timeout
        ):
            self.state = self.SEARCHING
            self.get_logger().warning(
                f"  Versuch {self.aktueller_versuch}: Marker verloren -> SEARCHING"
            )

    def versuch_abschliessen(self):
        """Speichert Ergebnis des aktuellen Versuchs."""
        self.test_aktiv = False

        # Watchdog-Timer entfernen
        if hasattr(self, "watchdog_timer"):
            self.watchdog_timer.cancel()
            self.destroy_timer(self.watchdog_timer)

        dauer = time.time() - self.versuch_start_time
        erfolg = self.state == self.DOCKED

        # Lateraler Versatz via solvePnP (metrisch, kalibriert)
        lat_versatz_cm = None
        if self.last_marker_corners is not None:
            lat_versatz_cm = self._estimate_lateral_offset_cm(self.last_marker_corners)

        # Orientierungsfehler [rad -> Grad] mit Wraparound-Korrektur
        yaw_diff = math.atan2(
            math.sin(self.odom_yaw - self.odom_yaw_start),
            math.cos(self.odom_yaw - self.odom_yaw_start),
        )
        orient_fehler_deg = math.degrees(yaw_diff)

        ergebnis = {
            "versuch": self.aktueller_versuch,
            "erfolg": erfolg,
            "dauer_s": round(dauer, 2),
            "lat_versatz_cm": round(lat_versatz_cm, 2) if lat_versatz_cm is not None else None,
            "orient_fehler_deg": round(orient_fehler_deg, 2),
            "ultraschall_m": round(self.range_m, 3),
            "marker_breite_px": float(round(self.last_marker_width, 0))
            if self.last_marker_width
            else None,
            "state": self.state,
        }
        self.ergebnisse.append(ergebnis)

        status = "ERFOLG" if erfolg else "FEHLSCHLAG"
        versatz_cm_str = f"{lat_versatz_cm:.2f} cm" if lat_versatz_cm is not None else "N/A"
        self.get_logger().info(
            f"  Ergebnis: {status}, Dauer: {dauer:.1f} s, "
            f"Versatz: {versatz_cm_str}, Orient: {orient_fehler_deg:.1f} deg, "
            f"Distanz: {self.range_m:.2f} m"
        )

        # Naechster Versuch oder Auswertung
        if self.aktueller_versuch < self.num_versuche:
            self.get_logger().info(
                '  Roboter fuer naechsten Versuch positionieren. Dann "s" + Enter druecken.'
            )
        else:
            self.auswertung()

    def stop_robot(self):
        """Sendet Null-Twist."""
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def auswertung(self):
        """Berechnet Statistik und gibt Ergebnis-Tabelle aus."""
        self.get_logger().info("")
        self.get_logger().info("=" * 70)
        self.get_logger().info("DOCKING-VALIDIERUNG: ERGEBNISSE")
        self.get_logger().info("=" * 70)

        # Tabelle
        self.get_logger().info("")
        self.get_logger().info(
            "| Versuch | Erfolg | Dauer [s] | Versatz [cm] | Orient. [deg] | Dist. [m] |"
        )
        self.get_logger().info(
            "|---------|--------|-----------|--------------|---------------|-----------|"
        )

        for e in self.ergebnisse:
            erfolg_str = "Ja" if e["erfolg"] else "Nein"
            versatz_str = f"{e['lat_versatz_cm']:.2f}" if e["lat_versatz_cm"] is not None else "N/A"
            dist_str = f"{e['ultraschall_m']:.2f}" if e.get("ultraschall_m") is not None else "N/A"
            self.get_logger().info(
                f"| {e['versuch']:>7} | {erfolg_str:>6} | {e['dauer_s']:>9.1f} | "
                f"{versatz_str:>12} | {e['orient_fehler_deg']:>13.1f} | {dist_str:>9} |"
            )

        # Statistik
        erfolge = sum(1 for e in self.ergebnisse if e["erfolg"])
        erfolgsquote = (erfolge / len(self.ergebnisse)) * 100.0

        versatz_werte_cm = [
            abs(e["lat_versatz_cm"])
            for e in self.ergebnisse
            if e["lat_versatz_cm"] is not None and e["erfolg"]
        ]
        orient_werte = [abs(e["orient_fehler_deg"]) for e in self.ergebnisse if e["erfolg"]]
        dauer_werte = [e["dauer_s"] for e in self.ergebnisse if e["erfolg"]]

        self.get_logger().info("")
        self.get_logger().info(
            f"Erfolgsquote: {erfolge}/{len(self.ergebnisse)} ({erfolgsquote:.0f}%)"
        )

        if versatz_werte_cm:
            self.get_logger().info(
                f"Lateraler Versatz (Erfolge): "
                f"Mittel={np.mean(versatz_werte_cm):.2f} cm, "
                f"Std={np.std(versatz_werte_cm):.2f} cm"
            )
        if orient_werte:
            self.get_logger().info(
                f"Orientierungsfehler (Erfolge): "
                f"Mittel={np.mean(orient_werte):.1f} deg, "
                f"Std={np.std(orient_werte):.1f} deg"
            )
        if dauer_werte:
            self.get_logger().info(
                f"Dauer (Erfolge): "
                f"Mittel={np.mean(dauer_werte):.1f} s, "
                f"Std={np.std(dauer_werte):.1f} s"
            )

        # Akzeptanzkriterien
        self.get_logger().info("")
        self.get_logger().info("--- Akzeptanzkriterien ---")
        pass_erfolg = erfolgsquote >= 80.0
        self.get_logger().info(
            f"Erfolgsquote >= 80%: {'PASS' if pass_erfolg else 'FAIL'} ({erfolgsquote:.0f}%)"
        )

        mittlerer_versatz = float(np.mean(versatz_werte_cm)) if versatz_werte_cm else None
        pass_versatz = mittlerer_versatz is not None and mittlerer_versatz < VERSATZ_AKZEPTANZ_CM
        if mittlerer_versatz is not None:
            self.get_logger().info(
                f"Mittl. Versatz < {VERSATZ_AKZEPTANZ_CM} cm: "
                f"{'PASS' if pass_versatz else 'FAIL'} ({mittlerer_versatz:.2f} cm)"
            )
        else:
            self.get_logger().info("Mittl. Versatz: keine Daten (kein Erfolg)")

        # JSON-Export
        export = {
            "test": "docking",
            "num_versuche": len(self.ergebnisse),
            "versuche": self.ergebnisse,
            "statistik": {
                "erfolgsquote_pct": round(erfolgsquote, 1),
                "erfolge": erfolge,
                "gesamt": len(self.ergebnisse),
                "mittlerer_versatz_cm": round(mittlerer_versatz, 2)
                if mittlerer_versatz is not None
                else None,
                "std_versatz_cm": round(float(np.std(versatz_werte_cm)), 2)
                if versatz_werte_cm
                else None,
                "mittlerer_orient_deg": round(float(np.mean(orient_werte)), 1)
                if orient_werte
                else None,
                "std_orient_deg": round(float(np.std(orient_werte)), 1) if orient_werte else None,
                "mittlere_dauer_s": round(float(np.mean(dauer_werte)), 1) if dauer_werte else None,
            },
            "akzeptanz": {
                "erfolgsquote_pass": pass_erfolg,
                "versatz_pass": pass_versatz,
            },
        }

        json_pfad = self.output_dir / "docking_results.json"
        with open(json_pfad, "w") as f:
            json.dump(export, f, indent=2)
        self.get_logger().info(f"Ergebnisse gespeichert: {json_pfad}")


def main(args=None):
    parser = argparse.ArgumentParser(description="Docking-Validierungstest fuer AMR")
    parser.add_argument(
        "--output",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Ausgabeverzeichnis fuer JSON-Ergebnisse (Default: Skriptverzeichnis)",
    )
    parsed = parser.parse_args()

    rclpy.init(args=args)
    node = DockingTestNode(output_dir=parsed.output)

    # Interaktiver Modus: Benutzer startet jeden Versuch manuell
    import threading

    def input_thread():
        """Wartet auf Benutzereingabe um Versuche zu starten."""
        while node.aktueller_versuch < node.num_versuche:
            try:
                eingabe = input(
                    f"\n[Versuch {node.aktueller_versuch + 1}/"
                    f"{node.num_versuche}] "
                    f'Roboter positionieren, dann "s" + Enter: '
                )
                if eingabe.strip().lower() == "s":
                    node.versuch_starten()
                elif eingabe.strip().lower() == "q":
                    node.get_logger().info("Test abgebrochen durch Benutzer.")
                    node.auswertung()
                    break
            except EOFError:
                break

    thread = threading.Thread(target=input_thread, daemon=True)
    thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutdown durch Benutzer.")
        if node.ergebnisse:
            node.auswertung()
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
