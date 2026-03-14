#!/usr/bin/env python3
"""Generiert ein Schachbrettmuster als PNG fuer die Kamerakalibrierung.

Standard: 9x6 innere Ecken (10x7 Quadrate), 30 mm Quadratgroesse.
Ausgabe als A4-optimiertes PNG zum Anzeigen auf Bildschirm oder Ausdrucken.
"""

import argparse

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Schachbrettmuster generieren")
    parser.add_argument("--cols", type=int, default=9, help="Innere Ecken horizontal (default: 9)")
    parser.add_argument("--rows", type=int, default=6, help="Innere Ecken vertikal (default: 6)")
    parser.add_argument(
        "--square-px", type=int, default=80, help="Quadratgroesse in Pixel (default: 80)"
    )
    parser.add_argument("--output", type=str, default="checkerboard_9x6.png", help="Ausgabedatei")
    args = parser.parse_args()

    # Quadrate = innere Ecken + 1
    board_cols = args.cols + 1
    board_rows = args.rows + 1
    sq = args.square_px

    # Weisser Rand (1 Quadrat)
    margin = sq
    w = board_cols * sq + 2 * margin
    h = board_rows * sq + 2 * margin

    img = np.ones((h, w), dtype=np.uint8) * 255

    for r in range(board_rows):
        for c in range(board_cols):
            if (r + c) % 2 == 0:
                x0 = margin + c * sq
                y0 = margin + r * sq
                img[y0 : y0 + sq, x0 : x0 + sq] = 0

    cv2.imwrite(args.output, img)
    print(f"Schachbrett gespeichert: {args.output} ({w}x{h} px)")
    print(f"Innere Ecken: {args.cols}x{args.rows}, Quadrate: {board_cols}x{board_rows}")
    print("Zum Kalibrieren: python3 amr/scripts/camera_calibration.py --square-size 0.030")


if __name__ == "__main__":
    main()
