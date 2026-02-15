#!/usr/bin/env python3
"""
UMBmark-Auswertungstool fuer AMR-Differentialantrieb.

Implementiert die systematische Odometrie-Kalibrierung nach Borenstein & Feng 1996
(Measurement and Correction of Systematic Odometry Errors, S. 139-142, Gl. 5.9-5.15).

Standalone-Skript ohne ROS2-Abhaengigkeit.
Eingabe: 5x CW und 5x CCW Endpositionen (x,y) nach 4x4m-Quadratfahrt.
Ausgabe: Korrekturfaktoren E_b, E_d, korrigierte Radradien, Scatterplot.

Verwendung:
    python3 umbmark_analysis.py                 # Interaktive Eingabe
    python3 umbmark_analysis.py data.json       # Aus JSON-Datei laden
"""

import sys
import json
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ===========================================================================
# Roboter-Parameter (aus hardware/config.h)
# ===========================================================================
L = 16.0                    # Gesamtpfadlaenge 4x4m Quadrat [m]
B_NOMINAL = 0.178           # WHEEL_BASE [m]
WHEEL_RADIUS = 0.0325       # [m]
TICKS_PER_REV_NOMINAL = 374.0  # Nennwert JGA25-370


def eingabe_interaktiv():
    """Liest 5 CW- und 5 CCW-Endpositionen interaktiv von stdin ein."""
    print("=" * 60)
    print("UMBmark-Auswertung nach Borenstein & Feng 1996")
    print("=" * 60)
    print()
    print(f"Roboter-Parameter: b = {B_NOMINAL} m, r = {WHEEL_RADIUS} m")
    print(f"Pfad: 4x4 m Quadrat, Gesamtlaenge L = {L} m")
    print()
    print("Bitte 5 CW-Endpositionen eingeben (x y in mm):")
    print("-" * 40)

    cw_positionen = []
    for i in range(5):
        while True:
            try:
                eingabe = input(f"  CW Lauf {i+1} (x y): ").strip()
                x, y = map(float, eingabe.split())
                cw_positionen.append((x, y))
                break
            except ValueError:
                print("  Fehler: Bitte zwei Zahlen eingeben (x y)")

    print()
    print("Bitte 5 CCW-Endpositionen eingeben (x y in mm):")
    print("-" * 40)

    ccw_positionen = []
    for i in range(5):
        while True:
            try:
                eingabe = input(f"  CCW Lauf {i+1} (x y): ").strip()
                x, y = map(float, eingabe.split())
                ccw_positionen.append((x, y))
                break
            except ValueError:
                print("  Fehler: Bitte zwei Zahlen eingeben (x y)")

    return cw_positionen, ccw_positionen


def eingabe_json(dateipfad):
    """Liest CW/CCW-Endpositionen aus einer JSON-Datei.

    Erwartetes Format:
    {
        "cw": [[x1,y1], [x2,y2], ...],
        "ccw": [[x1,y1], [x2,y2], ...]
    }
    """
    pfad = Path(dateipfad)
    if not pfad.exists():
        print(f"Fehler: Datei '{dateipfad}' nicht gefunden.")
        sys.exit(1)

    with open(pfad, "r") as f:
        daten = json.load(f)

    cw_positionen = [tuple(p) for p in daten["cw"]]
    ccw_positionen = [tuple(p) for p in daten["ccw"]]

    if len(cw_positionen) != 5 or len(ccw_positionen) != 5:
        print("Fehler: Genau 5 CW- und 5 CCW-Positionen erforderlich.")
        sys.exit(1)

    return cw_positionen, ccw_positionen


def berechne_umbmark(cw_positionen, ccw_positionen):
    """Fuehrt die vollstaendige UMBmark-Berechnung nach Borenstein 1996 durch.

    Parameter:
        cw_positionen:  Liste von 5 (x,y)-Tupeln in mm (Uhrzeigersinn)
        ccw_positionen: Liste von 5 (x,y)-Tupeln in mm (Gegen-Uhrzeigersinn)

    Rueckgabe:
        Dictionary mit allen Zwischen- und Endergebnissen.
    """
    # Positionen als numpy-Arrays [mm]
    cw = np.array(cw_positionen)
    ccw = np.array(ccw_positionen)

    # 1. Schwerpunkte [mm]
    x_cg_cw = np.mean(cw[:, 0])
    y_cg_cw = np.mean(cw[:, 1])
    x_cg_ccw = np.mean(ccw[:, 0])
    y_cg_ccw = np.mean(ccw[:, 1])

    # 2. Schwerpunkte in Meter umrechnen fuer Formeln
    x_cg_cw_m = x_cg_cw / 1000.0
    y_cg_cw_m = y_cg_cw / 1000.0
    x_cg_ccw_m = x_cg_ccw / 1000.0
    y_cg_ccw_m = y_cg_ccw / 1000.0

    # 3. Fehlerwinkel (Borenstein Gl. 5.9, 5.10)
    alpha = ((x_cg_cw_m + x_cg_ccw_m) / (-4.0 * L)) * (180.0 / math.pi)
    beta = ((x_cg_cw_m - x_cg_ccw_m) / (-4.0 * L)) * (180.0 / math.pi)

    # 4. Kruemmungsradius (Borenstein Gl. 5.11)
    beta_rad = math.radians(beta)
    if abs(beta_rad) < 1e-12:
        # Kein Typ-B-Fehler: R -> unendlich
        R = float('inf')
        E_d = 1.0
    else:
        R = (L / 2.0) / math.sin(beta_rad / 2.0)
        # 5. Korrekturfaktor E_d (Raddurchmesser-Verhaeltnis, Gl. 5.12)
        E_d = (R + B_NOMINAL / 2.0) / (R - B_NOMINAL / 2.0)

    # 6. Korrekturfaktor E_b (Spurbreite, Gl. 5.13)
    if abs(90.0 - alpha) < 1e-12:
        E_b = 1.0
    else:
        E_b = 90.0 / (90.0 - alpha)

    # 7. Korrigierte Spurbreite
    b_actual = E_b * B_NOMINAL

    # 8. Korrigierte Radradien (Gl. 5.14, 5.15)
    r_right = WHEEL_RADIUS * (2.0 * E_d / (E_d + 1.0))
    r_left = WHEEL_RADIUS * (2.0 / (E_d + 1.0))

    # 9. Fehlervektoren und E_max,syst [mm]
    r_cg_cw = math.sqrt(x_cg_cw**2 + y_cg_cw**2)
    r_cg_ccw = math.sqrt(x_cg_ccw**2 + y_cg_ccw**2)
    E_max_syst = max(r_cg_cw, r_cg_ccw)

    # 10. Standardabweichungen der Endpositionen [mm]
    std_cw_x = np.std(cw[:, 0], ddof=1)
    std_cw_y = np.std(cw[:, 1], ddof=1)
    std_ccw_x = np.std(ccw[:, 0], ddof=1)
    std_ccw_y = np.std(ccw[:, 1], ddof=1)

    ergebnisse = {
        # Rohdaten [mm]
        "cw_positionen": cw_positionen,
        "ccw_positionen": ccw_positionen,
        # Schwerpunkte [mm]
        "x_cg_cw_mm": x_cg_cw,
        "y_cg_cw_mm": y_cg_cw,
        "x_cg_ccw_mm": x_cg_ccw,
        "y_cg_ccw_mm": y_cg_ccw,
        # Fehlerwinkel [Grad]
        "alpha_deg": alpha,
        "beta_deg": beta,
        # Kruemmungsradius [m]
        "R_m": R,
        # Korrekturfaktoren
        "E_d": E_d,
        "E_b": E_b,
        # Korrigierte Geometrie
        "b_actual_m": b_actual,
        "r_left_m": r_left,
        "r_right_m": r_right,
        # Fehlermetrik [mm]
        "r_cg_cw_mm": r_cg_cw,
        "r_cg_ccw_mm": r_cg_ccw,
        "E_max_syst_mm": E_max_syst,
        # Streuung [mm]
        "std_cw_x_mm": std_cw_x,
        "std_cw_y_mm": std_cw_y,
        "std_ccw_x_mm": std_ccw_x,
        "std_ccw_y_mm": std_ccw_y,
    }

    return ergebnisse


def ausgabe_markdown(erg):
    """Gibt die UMBmark-Ergebnisse als formatierte Markdown-Tabelle aus."""
    print()
    print("=" * 70)
    print("UMBmark-Ergebnisse")
    print("=" * 70)
    print()

    # Schwerpunkte
    print("### Schwerpunkte der Endpositionen")
    print()
    print("| Groesse      |   CW [mm]  |   CCW [mm] |")
    print("|:-------------|----------:|-----------:|")
    print(f"| x_cg         | {erg['x_cg_cw_mm']:10.2f} | {erg['x_cg_ccw_mm']:10.2f} |")
    print(f"| y_cg         | {erg['y_cg_cw_mm']:10.2f} | {erg['y_cg_ccw_mm']:10.2f} |")
    print(f"| r_cg         | {erg['r_cg_cw_mm']:10.2f} | {erg['r_cg_ccw_mm']:10.2f} |")
    print(f"| std(x)       | {erg['std_cw_x_mm']:10.2f} | {erg['std_ccw_x_mm']:10.2f} |")
    print(f"| std(y)       | {erg['std_cw_y_mm']:10.2f} | {erg['std_ccw_y_mm']:10.2f} |")
    print()

    # Fehlerwinkel
    print("### Fehleranalyse nach Borenstein 1996")
    print()
    print("| Parameter                   | Wert            |")
    print("|:----------------------------|:----------------|")
    print(f"| alpha (Typ-A, E_b)          | {erg['alpha_deg']:+.6f} deg  |")
    print(f"| beta  (Typ-B, E_d)          | {erg['beta_deg']:+.6f} deg  |")
    if erg['R_m'] != float('inf'):
        print(f"| Kruemmungsradius R           | {erg['R_m']:.3f} m       |")
    else:
        print("| Kruemmungsradius R           | inf (kein Typ-B-Fehler) |")
    print(f"| E_d (Raddurchmesser-Ratio)  | {erg['E_d']:.6f}        |")
    print(f"| E_b (Spurbreite-Korrektor)  | {erg['E_b']:.6f}        |")
    print()

    # Korrigierte Geometrie
    print("### Korrigierte Roboter-Geometrie")
    print()
    print("| Parameter           | Nominal [m]  | Korrigiert [m] | Abweichung  |")
    print("|:--------------------|:-------------|:---------------|:------------|")
    print(f"| WHEEL_BASE          | {B_NOMINAL:.4f}       | {erg['b_actual_m']:.6f}       | {(erg['b_actual_m'] - B_NOMINAL) * 1000:+.3f} mm |")
    print(f"| WHEEL_RADIUS_LEFT   | {WHEEL_RADIUS:.4f}      | {erg['r_left_m']:.6f}       | {(erg['r_left_m'] - WHEEL_RADIUS) * 1000:+.3f} mm |")
    print(f"| WHEEL_RADIUS_RIGHT  | {WHEEL_RADIUS:.4f}      | {erg['r_right_m']:.6f}       | {(erg['r_right_m'] - WHEEL_RADIUS) * 1000:+.3f} mm |")
    print()

    # Fehlermetrik
    print("### Fehlermetrik")
    print()
    print(f"| E_max,syst (vor Kalibrierung) | {erg['E_max_syst_mm']:.1f} mm |")
    print()

    # config.h-Werte
    # Die Firmware verwendet einen einzigen WHEEL_RADIUS (symmetrisch).
    # Die Rad-Asymmetrie wird ueber TICKS_PER_REV_LEFT/RIGHT korrigiert:
    #   ticks_corrected = ticks_nominal * (r_nominal / r_corrected)
    r_nominal = WHEEL_RADIUS
    ticks_left = TICKS_PER_REV_NOMINAL * (r_nominal / erg['r_left_m'])
    ticks_right = TICKS_PER_REV_NOMINAL * (r_nominal / erg['r_right_m'])

    print("### Korrigierte config.h-Werte (Copy-Paste)")
    print()
    print("```c")
    print(f"#define WHEEL_BASE            {erg['b_actual_m']:.6f}f  // [m] UMBmark-korrigiert")
    print(f"#define TICKS_PER_REV_LEFT    {ticks_left:.1f}f    // UMBmark-korrigiert (nominal: {TICKS_PER_REV_NOMINAL:.0f})")
    print(f"#define TICKS_PER_REV_RIGHT   {ticks_right:.1f}f    // UMBmark-korrigiert (nominal: {TICKS_PER_REV_NOMINAL:.0f})")
    print(f"// Korrigierte Radradien (zur Referenz, nicht als Define verwendet):")
    print(f"//   r_left  = {erg['r_left_m']:.6f} m  (Abweichung: {(erg['r_left_m'] - r_nominal) * 1000:+.3f} mm)")
    print(f"//   r_right = {erg['r_right_m']:.6f} m  (Abweichung: {(erg['r_right_m'] - r_nominal) * 1000:+.3f} mm)")
    print("```")
    print()

    # Bewertung
    print("### Bewertung")
    print()
    if erg['E_max_syst_mm'] < 10.0:
        print("ERGEBNIS: E_max,syst < 10 mm - Odometrie bereits sehr gut.")
        print("Kalibrierung bringt voraussichtlich nur marginale Verbesserung.")
    elif erg['E_max_syst_mm'] > 100.0:
        print(f"ERGEBNIS: E_max,syst = {erg['E_max_syst_mm']:.1f} mm - Signifikanter systematischer Fehler.")
        print("Kalibrierung wird deutliche Verbesserung bringen.")
        print("Erwarteter Reduktionsfaktor: >= 10 (Borenstein 1996).")
    else:
        print(f"ERGEBNIS: E_max,syst = {erg['E_max_syst_mm']:.1f} mm - Moderater systematischer Fehler.")
        print("Kalibrierung empfohlen.")


def erstelle_plot(erg, speicherpfad=None):
    """Erstellt Scatterplot der CW/CCW-Endpositionen mit Schwerpunkten."""
    cw = np.array(erg["cw_positionen"])
    ccw = np.array(erg["ccw_positionen"])

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    # Endpositionen
    ax.scatter(cw[:, 0], cw[:, 1], c="red", s=60, marker="o",
               label="CW Endpositionen", zorder=3)
    ax.scatter(ccw[:, 0], ccw[:, 1], c="blue", s=60, marker="s",
               label="CCW Endpositionen", zorder=3)

    # Schwerpunkte
    ax.scatter(erg["x_cg_cw_mm"], erg["y_cg_cw_mm"],
               c="red", s=200, marker="X", edgecolors="black", linewidths=1.5,
               label=f"CW Schwerpunkt ({erg['x_cg_cw_mm']:.1f}, {erg['y_cg_cw_mm']:.1f})",
               zorder=4)
    ax.scatter(erg["x_cg_ccw_mm"], erg["y_cg_ccw_mm"],
               c="blue", s=200, marker="X", edgecolors="black", linewidths=1.5,
               label=f"CCW Schwerpunkt ({erg['x_cg_ccw_mm']:.1f}, {erg['y_cg_ccw_mm']:.1f})",
               zorder=4)

    # Ursprung
    ax.scatter(0, 0, c="green", s=150, marker="+", linewidths=2,
               label="Sollposition (0, 0)", zorder=5)

    # Fehlerkreise
    if erg["r_cg_cw_mm"] > 0:
        kreis_cw = plt.Circle((0, 0), erg["r_cg_cw_mm"], fill=False,
                              color="red", linestyle="--", alpha=0.5)
        ax.add_patch(kreis_cw)
    if erg["r_cg_ccw_mm"] > 0:
        kreis_ccw = plt.Circle((0, 0), erg["r_cg_ccw_mm"], fill=False,
                               color="blue", linestyle="--", alpha=0.5)
        ax.add_patch(kreis_ccw)

    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title("UMBmark-Ergebnisse: Endpositionen nach 4x4 m Quadratfahrt")
    ax.legend(loc="best", fontsize=9)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.axvline(x=0, color="gray", linewidth=0.5)

    plt.tight_layout()

    if speicherpfad:
        pfad = Path(speicherpfad)
        fig.savefig(pfad, dpi=150, bbox_inches="tight")
        print(f"Plot gespeichert: {pfad}")
    else:
        plt.show()

    plt.close(fig)


def main():
    """Hauptprogramm: Eingabe lesen, UMBmark berechnen, Ergebnisse ausgeben."""
    # Eingabemodus bestimmen
    if len(sys.argv) > 1:
        cw_pos, ccw_pos = eingabe_json(sys.argv[1])
        print(f"Daten geladen aus: {sys.argv[1]}")
    else:
        cw_pos, ccw_pos = eingabe_interaktiv()

    # Berechnung
    ergebnisse = berechne_umbmark(cw_pos, ccw_pos)

    # Ausgabe
    ausgabe_markdown(ergebnisse)

    # Plot
    skript_verzeichnis = Path(__file__).parent
    plot_pfad = skript_verzeichnis / "umbmark_ergebnis.png"
    erstelle_plot(ergebnisse, speicherpfad=plot_pfad)

    # JSON-Export
    json_pfad = skript_verzeichnis / "umbmark_results.json"
    export = {
        "parameter": {
            "L_m": L,
            "b_nominal_m": B_NOMINAL,
            "wheel_radius_m": WHEEL_RADIUS,
        },
        "rohdaten": {
            "cw_mm": ergebnisse["cw_positionen"],
            "ccw_mm": ergebnisse["ccw_positionen"],
        },
        "ergebnisse": {
            "alpha_deg": ergebnisse["alpha_deg"],
            "beta_deg": ergebnisse["beta_deg"],
            "E_d": ergebnisse["E_d"],
            "E_b": ergebnisse["E_b"],
            "b_actual_m": ergebnisse["b_actual_m"],
            "r_left_m": ergebnisse["r_left_m"],
            "r_right_m": ergebnisse["r_right_m"],
            "E_max_syst_mm": ergebnisse["E_max_syst_mm"],
        },
    }
    with open(json_pfad, "w") as f:
        json.dump(export, f, indent=2)
    print(f"JSON-Export: {json_pfad}")


if __name__ == "__main__":
    main()
