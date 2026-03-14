#!/usr/bin/env python3
"""Kamerakalibrierung ueber MJPEG-Stream mit Schachbrettmuster.

Verbindet sich mit dem MJPEG-Stream der dashboard_bridge (Port 8082),
erkennt automatisch Schachbrett-Ecken und fuehrt eine OpenCV-Kalibrierung
durch. Ergebnis wird als ROS2-kompatible YAML-Datei gespeichert.

Verwendung:
  python3 camera_calibration.py
  python3 camera_calibration.py --square-size 0.025 --min-frames 20
  python3 camera_calibration.py --cols 9 --rows 6 --output amr_camera.yaml

Ablauf:
  1. Schachbrettmuster (9x6 innere Ecken) vor die Kamera halten
  2. Muster langsam in verschiedenen Positionen und Winkeln bewegen
  3. Skript sammelt automatisch gute Frames (diverse Perspektiven)
  4. Nach genuegend Frames wird kalibriert und das Ergebnis gespeichert
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np


# --- MJPEG-Stream Reader ---
class MJPEGReader:
    """Liest Frames aus einem MJPEG-HTTP-Stream."""

    def __init__(self, url: str):
        self.cap = cv2.VideoCapture(url)
        if not self.cap.isOpened():
            raise ConnectionError(f"MJPEG-Stream nicht erreichbar: {url}")

    def read(self) -> tuple[bool, np.ndarray | None]:
        return self.cap.read()

    def release(self):
        self.cap.release()


# --- Diversitaetspruefung ---
def is_diverse(corners: np.ndarray, collected: list[np.ndarray], threshold: float = 40.0) -> bool:
    """Prueft ob die Ecken ausreichend verschieden von bereits gesammelten sind."""
    if not collected:
        return True
    center = corners.mean(axis=0)
    for prev in collected:
        prev_center = prev.mean(axis=0)
        dist = np.linalg.norm(center - prev_center)
        if dist < threshold:
            return False
    return True


# --- Kalibrierung ---
def calibrate(
    obj_points: list[np.ndarray],
    img_points: list[np.ndarray],
    image_size: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, float]:
    """Fuehrt OpenCV-Kamerakalibrierung durch."""
    ret, camera_matrix, dist_coeffs, _rvecs, _tvecs = cv2.calibrateCamera(
        obj_points, img_points, image_size, None, None
    )
    return camera_matrix, dist_coeffs, ret


# --- ROS2 YAML speichern ---
def save_ros2_yaml(
    path: str,
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
    image_size: tuple[int, int],
    rms_error: float,
):
    """Speichert Kalibrierung im ROS2 camera_calibration_parsers Format."""
    w, h = image_size
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]
    d = dist_coeffs.flatten()

    yaml_content = f"""\
# =============================================================================
# ROS2 Camera Calibration File — IMX296 Global Shutter (640x480 via v4l2loopback)
#
# Calibrated using OpenCV camera_calibration with checkerboard pattern.
# RMS reprojection error: {rms_error:.4f} px
# Date: {time.strftime("%Y-%m-%d %H:%M")}
#
# Sensor: Sony IMX296 (native 1440x1088), downscaled to {w}x{h}
# Lens: Wide-angle M12 (PT361060M3MP12)
# Format: ROS2 camera_calibration_parsers (YAML)
# =============================================================================

image_width: {w}
image_height: {h}
camera_name: amr_camera
camera_matrix:
  rows: 3
  cols: 3
  data: [{fx:.6f}, 0.0, {cx:.6f},
         0.0, {fy:.6f}, {cy:.6f},
         0.0, 0.0, 1.0]
distortion_model: plumb_bob
distortion_coefficients:
  rows: 1
  cols: 5
  data: [{d[0]:.6f}, {d[1]:.6f}, {d[2]:.6f}, {d[3]:.6f}, {d[4]:.6f}]
rectification_matrix:
  rows: 3
  cols: 3
  data: [1.0, 0.0, 0.0,
         0.0, 1.0, 0.0,
         0.0, 0.0, 1.0]
projection_matrix:
  rows: 3
  cols: 4
  data: [{fx:.6f}, 0.0, {cx:.6f}, 0.0,
         0.0, {fy:.6f}, {cy:.6f}, 0.0,
         0.0, 0.0, 1.0, 0.0]
"""
    Path(path).write_text(yaml_content)


# --- Hauptprogramm ---
def main():
    parser = argparse.ArgumentParser(description="Kamerakalibrierung via MJPEG-Stream")
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8082/stream",
        help="MJPEG-Stream URL (default: dashboard_bridge)",
    )
    parser.add_argument("--cols", type=int, default=9, help="Innere Ecken horizontal (default: 9)")
    parser.add_argument("--rows", type=int, default=6, help="Innere Ecken vertikal (default: 6)")
    parser.add_argument(
        "--square-size",
        type=float,
        default=0.030,
        help="Quadratgroesse in Metern (default: 0.030 = 30 mm)",
    )
    parser.add_argument(
        "--min-frames", type=int, default=20, help="Mindestanzahl guter Frames (default: 20)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="amr/pi5/ros2_ws/src/my_bot/config/amr_camera.yaml",
        help="Ausgabedatei (ROS2 YAML)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Mindestabstand zwischen Aufnahmen in Sekunden (default: 1.5)",
    )
    args = parser.parse_args()

    pattern_size = (args.cols, args.rows)

    # 3D-Objektpunkte (Schachbrett in der XY-Ebene, Z=0)
    objp = np.zeros((args.cols * args.rows, 3), np.float32)
    objp[:, :2] = np.mgrid[0 : args.cols, 0 : args.rows].T.reshape(-1, 2)
    objp *= args.square_size

    obj_points: list[np.ndarray] = []
    img_points: list[np.ndarray] = []
    collected_centers: list[np.ndarray] = []

    print("=" * 60)
    print("  AMR Kamerakalibrierung")
    print("=" * 60)
    print(f"  Schachbrett: {args.cols}x{args.rows} innere Ecken")
    print(f"  Quadratgroesse: {args.square_size * 1000:.0f} mm")
    print(f"  Ziel: {args.min_frames} diverse Aufnahmen")
    print(f"  Stream: {args.url}")
    print("=" * 60)
    print()
    print("Halte das Schachbrettmuster vor die Kamera.")
    print("Bewege es langsam in verschiedene Positionen und Winkel:")
    print("  - Mitte, links, rechts, oben, unten")
    print("  - Verschiedene Neigungen (gekippt, gedreht)")
    print("  - Verschiedene Entfernungen (nah und fern)")
    print()
    print("Druecke Ctrl+C zum Abbrechen.")
    print()

    # Verbindung zum MJPEG-Stream
    try:
        reader = MJPEGReader(args.url)
    except ConnectionError as e:
        print(f"FEHLER: {e}")
        print("Ist der Full-Stack mit use_dashboard:=True gestartet?")
        sys.exit(1)

    print("Stream verbunden. Suche Schachbrett...\n")

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    last_capture = 0.0
    frame_count = 0
    image_size = None

    try:
        while len(obj_points) < args.min_frames:
            ok, frame = reader.read()
            if not ok or frame is None:
                time.sleep(0.1)
                continue

            frame_count += 1
            if image_size is None:
                h, w = frame.shape[:2]
                image_size = (w, h)
                print(f"Bildgroesse: {w}x{h}")

            # Nicht zu schnell aufnehmen
            now = time.time()
            if now - last_capture < args.delay:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(
                gray,
                pattern_size,
                cv2.CALIB_CB_ADAPTIVE_THRESH
                + cv2.CALIB_CB_NORMALIZE_IMAGE
                + cv2.CALIB_CB_FAST_CHECK,
            )

            if found:
                # Subpixel-Verfeinerung
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

                # Diversitaetspruefung
                if is_diverse(corners_refined, collected_centers):
                    obj_points.append(objp)
                    img_points.append(corners_refined)
                    collected_centers.append(corners_refined)
                    last_capture = now

                    n = len(obj_points)
                    # Ecken-Spread als Qualitaetsindikator
                    spread = np.ptp(corners_refined, axis=0).flatten()
                    print(
                        f"  [{n:2d}/{args.min_frames}] Aufnahme gespeichert "
                        f"(Spread: {spread[0]:.0f}x{spread[1]:.0f} px, "
                        f"Frame #{frame_count})"
                    )
                else:
                    # Nur alle 3s melden um Spam zu vermeiden
                    if now - last_capture > 3.0:
                        print(
                            "  [--] Schachbrett erkannt, aber zu aehnlich "
                            "— bitte Position/Winkel aendern"
                        )
                        last_capture = now - args.delay + 1.0  # Bald nochmal pruefen

    except KeyboardInterrupt:
        print(f"\n\nAbgebrochen. {len(obj_points)} Aufnahmen gesammelt.")
        if len(obj_points) < 5:
            print("Zu wenige Aufnahmen fuer eine Kalibrierung (min. 5).")
            reader.release()
            sys.exit(1)
        print("Versuche Kalibrierung mit vorhandenen Aufnahmen...\n")

    reader.release()

    # Kalibrierung
    assert image_size is not None, "Keine Bildgroesse ermittelt (keine Aufnahmen geladen)"
    print(f"\nKalibriere mit {len(obj_points)} Aufnahmen...")
    camera_matrix, dist_coeffs, rms = calibrate(obj_points, img_points, image_size)

    print(f"\n{'=' * 60}")
    print("  Kalibrierung abgeschlossen")
    print(f"{'=' * 60}")
    print(f"  RMS Reprojektionsfehler: {rms:.4f} px")
    print("  (gut: < 0.5, akzeptabel: < 1.0, schlecht: > 1.0)")
    print()
    print("  Kameramatrix:")
    print(f"    fx = {camera_matrix[0, 0]:.2f} px")
    print(f"    fy = {camera_matrix[1, 1]:.2f} px")
    print(f"    cx = {camera_matrix[0, 2]:.2f} px")
    print(f"    cy = {camera_matrix[1, 2]:.2f} px")
    print()
    d = dist_coeffs.flatten()
    print("  Verzeichnung (plumb_bob):")
    print(f"    k1={d[0]:.6f}  k2={d[1]:.6f}  p1={d[2]:.6f}  p2={d[3]:.6f}  k3={d[4]:.6f}")
    print()

    # Speichern
    output_path = args.output
    save_ros2_yaml(output_path, camera_matrix, dist_coeffs, image_size, rms)
    print(f"  Gespeichert: {output_path}")
    print()

    # Qualitaetsbewertung
    if rms < 0.5:
        print("  Qualitaet: SEHR GUT — geeignet fuer ArUco-Docking")
    elif rms < 1.0:
        print("  Qualitaet: GUT — geeignet fuer die meisten Anwendungen")
    else:
        print("  Qualitaet: MAESSIG — erneute Kalibrierung empfohlen")
        print("  Tipps: Mehr Aufnahmen, verschiedenere Winkel, Muster plan halten")

    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
