#!/usr/bin/env python3
"""
Docking-Validierungstest fuer AMR Ladestation.

Fuehrt 10 Docking-Versuche durch und protokolliert Erfolgsquote,
lateralen Versatz und Orientierungsfehler.

Ablauf pro Versuch:
  1. Benutzer positioniert Roboter manuell (~1.5 m vor Marker)
  2. Docking-Node wird gestartet (ArUco-Marker-Suche + Annaeherung)
  3. Warten auf DOCKED-State oder Timeout (60 s)
  4. Ergebnis messen (Marker-Position, Dauer)
  5. Roboter faehrt 3 s rueckwaerts zur Ausgangsposition

Topics:
  - Subscribes: /camera/image_raw, /odom
  - Publishes:  /cmd_vel

Ergebnis: Markdown-Tabelle + JSON-Export (docking_results.json)
"""

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
from sensor_msgs.msg import Image

from amr_utils import quaternion_to_yaw

# Pixel-zu-cm Umrechnung (Naeherung).
# Annahme: 5 cm Markergroesse, ~150 px Markerbreite bei ~20 cm Docking-Distanz.
# Kann spaeter mit bekannter Markergroesse und Kamerakalibrierung verfeinert werden.
CM_PER_PIXEL = 0.033


class DockingTestNode(Node):
    """Fuehrt wiederholte Docking-Tests durch und sammelt Ergebnisse."""

    # Zustaende fuer einzelnen Versuch
    SEARCHING = "SEARCHING"
    APPROACHING = "APPROACHING"
    DOCKED = "DOCKED"
    TIMEOUT = "TIMEOUT"

    def __init__(self):
        super().__init__("docking_test")

        # Publisher / Subscriber
        self.cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.image_sub = self.create_subscription(
            Image, "/camera/image_raw", self.image_callback, 10
        )
        self.odom_sub = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)

        # Parameter
        self.bridge = CvBridge()
        self.kp_angular = 0.5
        self.approach_vel = 0.05
        self.search_vel = 0.2
        self.target_marker_id = 42
        self.docking_threshold = 150
        self.timeout_sec = 60.0
        self.marker_lost_timeout = 3.0
        self.num_versuche = 10
        self.rueckfahrt_vel = -0.2
        self.rueckfahrt_dauer = 3.0

        # ArUco Detector (moderne API)
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(dictionary, parameters)

        # Test-Zustand
        self.aktueller_versuch = 0
        self.state = self.SEARCHING
        self.versuch_start_time = 0.0
        self.last_marker_time = 0.0
        self.last_marker_center_x = None
        self.last_marker_width = None
        self.image_width = None
        self.test_aktiv = False

        # Odometrie
        self.odom_yaw = 0.0
        self.odom_yaw_start = 0.0

        # Ergebnisse
        self.ergebnisse = []

        # Skript-Verzeichnis fuer JSON-Export
        self.skript_verzeichnis = Path(os.path.dirname(os.path.abspath(__file__)))

        self.get_logger().info(f"Docking-Test bereit. {self.num_versuche} Versuche geplant.")
        self.get_logger().info('Eingabe "s" + Enter im Terminal startet den naechsten Versuch.')

    def odom_callback(self, msg):
        """Speichert aktuelle Gier-Orientierung aus Odometrie."""
        q = msg.pose.pose.orientation
        self.odom_yaw = quaternion_to_yaw(q)

    def image_callback(self, msg):
        """Verarbeitet Kamerabild waehrend aktivem Docking-Versuch."""
        if not self.test_aktiv:
            return
        if self.state in (self.DOCKED, self.TIMEOUT):
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().warning(f"CvBridge Fehler: {e}")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.image_width = frame.shape[1]
        img_center_x = self.image_width / 2.0

        corners, ids, _rejected = self.detector.detectMarkers(gray)

        cmd = Twist()

        if ids is not None and self.target_marker_id in ids.flatten():
            index = np.where(ids.flatten() == self.target_marker_id)[0][0]
            c = corners[index][0]

            center_x = np.mean(c[:, 0])
            marker_width = np.max(c[:, 0]) - np.min(c[:, 0])

            self.last_marker_center_x = center_x
            self.last_marker_width = marker_width
            self.last_marker_time = time.time()

            error_x = (center_x - img_center_x) / img_center_x

            if self.state == self.SEARCHING:
                self.state = self.APPROACHING
                self.get_logger().info(
                    f"  Versuch {self.aktueller_versuch}: Marker erkannt -> APPROACHING"
                )

            if marker_width > self.docking_threshold:
                self.state = self.DOCKED
                self.get_logger().info(
                    f"  Versuch {self.aktueller_versuch}: DOCKED (Breite: {marker_width:.0f} px)"
                )
                self.stop_robot()
                self.versuch_abschliessen()
                return

            cmd.angular.z = -1.0 * error_x * self.kp_angular
            cmd.linear.x = self.approach_vel
        else:
            cmd.angular.z = self.search_vel

        self.cmd_pub.publish(cmd)

    def versuch_starten(self):
        """Initialisiert einen neuen Docking-Versuch."""
        self.aktueller_versuch += 1
        self.state = self.SEARCHING
        self.versuch_start_time = time.time()
        self.last_marker_time = 0.0
        self.last_marker_center_x = None
        self.last_marker_width = None
        self.odom_yaw_start = self.odom_yaw
        self.test_aktiv = True

        self.get_logger().info(
            f"--- Versuch {self.aktueller_versuch}/{self.num_versuche} gestartet ---"
        )

        # Watchdog-Timer fuer diesen Versuch
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_callback)

    def watchdog_callback(self):
        """Ueberwacht Timeout und Marker-Verlust fuer aktuellen Versuch."""
        if not self.test_aktiv:
            return
        if self.state in (self.DOCKED, self.TIMEOUT):
            return

        now = time.time()

        if (now - self.versuch_start_time) > self.timeout_sec:
            self.state = self.TIMEOUT
            self.get_logger().warning(
                f"  Versuch {self.aktueller_versuch}: TIMEOUT nach {self.timeout_sec:.0f} s"
            )
            self.stop_robot()
            self.versuch_abschliessen()
            return

        if self.state == self.APPROACHING:
            if (
                self.last_marker_time > 0
                and (now - self.last_marker_time) > self.marker_lost_timeout
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

        # Lateraler Versatz [px -> cm] (grobe Schaetzung: 0.05 cm/px bei ~1m Abstand)
        lat_versatz_px = None
        if self.last_marker_center_x is not None and self.image_width is not None:
            lat_versatz_px = self.last_marker_center_x - (self.image_width / 2.0)

        # Orientierungsfehler [rad -> Grad] mit Wraparound-Korrektur
        yaw_diff = math.atan2(
            math.sin(self.odom_yaw - self.odom_yaw_start),
            math.cos(self.odom_yaw - self.odom_yaw_start),
        )
        orient_fehler_deg = math.degrees(yaw_diff)

        # Pixel -> cm Umrechnung
        lat_versatz_cm = None
        if lat_versatz_px is not None:
            lat_versatz_cm = lat_versatz_px * CM_PER_PIXEL

        ergebnis = {
            "versuch": self.aktueller_versuch,
            "erfolg": erfolg,
            "dauer_s": round(dauer, 2),
            "lat_versatz_px": round(lat_versatz_px, 1) if lat_versatz_px is not None else None,
            "lat_versatz_cm": round(lat_versatz_cm, 2) if lat_versatz_cm is not None else None,
            "orient_fehler_deg": round(orient_fehler_deg, 2),
            "marker_breite_px": round(self.last_marker_width, 0)
            if self.last_marker_width
            else None,
            "state": self.state,
        }
        self.ergebnisse.append(ergebnis)

        status = "ERFOLG" if erfolg else "FEHLSCHLAG"
        versatz_cm_str = f"{lat_versatz_cm:.2f} cm" if lat_versatz_cm is not None else "N/A"
        self.get_logger().info(
            f"  Ergebnis: {status}, Dauer: {dauer:.1f} s, "
            f"Versatz: {versatz_cm_str}, Orient: {orient_fehler_deg:.1f} deg"
        )

        # Rueckwaertsfahrt (timer-basiert, nicht blockierend)
        self.get_logger().info("  Rueckwaertsfahrt...")
        self._rueckfahrt_start = time.time()
        self._rueckfahrt_timer = self.create_timer(0.1, self._rueckfahrt_callback)

    def _rueckfahrt_callback(self):
        """Timer-Callback: publiziert Rueckwaertsfahrt-Kommandos fuer die konfigurierte Dauer."""
        elapsed = time.time() - self._rueckfahrt_start
        if elapsed < self.rueckfahrt_dauer:
            cmd = Twist()
            cmd.linear.x = self.rueckfahrt_vel
            self.cmd_pub.publish(cmd)
        else:
            # Rueckwaertsfahrt beendet
            self._rueckfahrt_timer.cancel()
            self.destroy_timer(self._rueckfahrt_timer)
            self.stop_robot()
            self.get_logger().info("  Rueckwaertsfahrt abgeschlossen.")

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
            "| Versuch | Erfolg | Dauer [s] | Lat. Versatz [cm] | Orient. [deg] |"
        )
        self.get_logger().info(
            "|---------|--------|-----------|-------------------|---------------|"
        )

        for e in self.ergebnisse:
            erfolg_str = "Ja" if e["erfolg"] else "Nein"
            versatz_str = f"{e['lat_versatz_cm']:.2f}" if e["lat_versatz_cm"] is not None else "N/A"
            self.get_logger().info(
                f"| {e['versuch']:>7} | {erfolg_str:>6} | {e['dauer_s']:>9.1f} | "
                f"{versatz_str:>17} | {e['orient_fehler_deg']:>13.1f} |"
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

        # JSON-Export
        export = {
            "test": "docking",
            "num_versuche": len(self.ergebnisse),
            "versuche": self.ergebnisse,
            "statistik": {
                "erfolgsquote_pct": round(erfolgsquote, 1),
                "erfolge": erfolge,
                "gesamt": len(self.ergebnisse),
                "mittlerer_versatz_cm": round(float(np.mean(versatz_werte_cm)), 2)
                if versatz_werte_cm
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
            },
        }

        json_pfad = self.skript_verzeichnis / "docking_results.json"
        with open(json_pfad, "w") as f:
            json.dump(export, f, indent=2)
        self.get_logger().info(f"Ergebnisse gespeichert: {json_pfad}")


def main(args=None):
    rclpy.init(args=args)
    node = DockingTestNode()

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
