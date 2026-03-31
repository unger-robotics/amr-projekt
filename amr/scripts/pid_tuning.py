#!/usr/bin/env python3
"""
PID-Sprungantwort-Analyse fuer AMR-Differentialantrieb.

Zwei Modi:
  a) Live-Aufnahme: Sendet Sprung cmd_vel (0 -> 0.4 m/s), zeichnet /odom 10 s auf.
  b) Rosbag-Analyse: Liest existierende rosbag2-Datei.

Berechnet Anstiegszeit, Ueberschwingen, Einschwingzeit und stationaeren Regelfehler.
Gibt Tuning-Empfehlungen und Matplotlib-Plot aus.

Verwendung:
    python3 pid_tuning.py live                  # Live-Aufnahme (ROS2 erforderlich)
    python3 pid_tuning.py bag /pfad/zur/rosbag  # Rosbag2-Analyse
"""

import json
import math
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

try:
    from amr_utils import PID_KD, PID_KI, PID_KP
except ImportError:
    from my_bot.amr_utils import PID_KD, PID_KI, PID_KP

# ===========================================================================
# Roboter-Parameter
# ===========================================================================
SOLL_GESCHWINDIGKEIT = 0.4  # [m/s] Zielgeschwindigkeit
AUFNAHME_DAUER = 10.0  # [s] Aufnahmedauer Live-Modus
SPRUNG_VERZOEGERUNG = 2.0  # [s] Wartezeit vor Sprung

# Aktuelle PID-Werte (aus amr_utils / mcu_firmware/drive_node/include/config_drive.h)
KP = PID_KP
KI = PID_KI
KD = PID_KD

# Akzeptanzkriterien
# Firmware-Rampe (MAX_ACCEL=5.0 rad/s^2) dominiert: ~2.5s theoretisch
AKZEPTANZ_ANSTIEGSZEIT = 3.0  # [s]
AKZEPTANZ_UEBERSCHWINGEN = 15  # [%]
AKZEPTANZ_EINSCHWINGZEIT = 1.0  # [s]
AKZEPTANZ_REGELFEHLER = 5  # [%]


def live_aufnahme():
    """Sendet Sprung-cmd_vel und zeichnet Odometrie auf (ROS2 erforderlich).

    Rueckgabe:
        timestamps: numpy-Array mit Zeitstempeln [s] relativ zum Sprungzeitpunkt
        velocities: numpy-Array mit Ist-Geschwindigkeiten [m/s]
    """
    try:
        import rclpy
        from geometry_msgs.msg import Twist
        from nav_msgs.msg import Odometry
        from rclpy.node import Node
    except ImportError:
        print("Fehler: ROS2 (rclpy) nicht verfuegbar.")
        print("Bitte ROS2 Humble installieren oder Rosbag-Modus verwenden.")
        sys.exit(1)

    rclpy.init()

    class SprungantwortNode(Node):
        def __init__(self):
            super().__init__("pid_sprungantwort")
            self.publisher = self.create_publisher(Twist, "/cmd_vel", 10)
            self.subscription = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)
            self.timestamps = []
            self.velocities = []
            self.start_time = None
            self.sprung_gesendet = False

        def odom_callback(self, msg):
            jetzt = self.get_clock().now().nanoseconds / 1e9
            if self.start_time is None:
                self.start_time = jetzt
            t_rel = jetzt - self.start_time
            v = msg.twist.twist.linear.x
            self.timestamps.append(t_rel)
            self.velocities.append(v)

    node = SprungantwortNode()

    # Warte auf erste Odometrie-Nachrichten
    print(f"Warte {SPRUNG_VERZOEGERUNG:.0f} s auf Odometrie-Verbindung...")
    t_start = time.time()
    while time.time() - t_start < SPRUNG_VERZOEGERUNG:
        rclpy.spin_once(node, timeout_sec=0.05)

    # Sprung senden
    print(f"Sende cmd_vel: v = {SOLL_GESCHWINDIGKEIT} m/s")
    twist = Twist()
    twist.linear.x = SOLL_GESCHWINDIGKEIT
    twist.angular.z = 0.0
    node.publisher.publish(twist)
    node.sprung_gesendet = True

    # Merke Sprungzeitpunkt
    if node.start_time is not None:
        sprung_offset = node.timestamps[-1] if node.timestamps else 0.0
    else:
        sprung_offset = 0.0

    # Aufzeichnung
    print(f"Zeichne {AUFNAHME_DAUER:.0f} s auf...")
    t_aufnahme = time.time()
    letzte_pub = 0.0
    while time.time() - t_aufnahme < AUFNAHME_DAUER:
        rclpy.spin_once(node, timeout_sec=0.02)
        # cmd_vel regelmaessig wiederholen (Failsafe-Timeout = 500 ms)
        if node.sprung_gesendet and (time.time() - letzte_pub > 0.2):
            node.publisher.publish(twist)
            letzte_pub = time.time()

    # Stopp senden
    twist_stop = Twist()
    node.publisher.publish(twist_stop)
    print("Stopp gesendet.")

    timestamps = np.array(node.timestamps) - sprung_offset
    velocities = np.array(node.velocities)

    node.destroy_node()
    rclpy.shutdown()

    return timestamps, velocities


def rosbag_analyse(bag_pfad):
    """Liest Odometrie-Daten aus einer rosbag2-Datei.

    Parameter:
        bag_pfad: Pfad zur rosbag2-Datei/Verzeichnis

    Rueckgabe:
        timestamps: numpy-Array mit Zeitstempeln [s] relativ zum ersten Sample
        velocities: numpy-Array mit Ist-Geschwindigkeiten [m/s]
    """
    try:
        from nav_msgs.msg import Odometry
        from rclpy.serialization import deserialize_message
        from rosbag2_py import ConverterOptions, SequentialReader, StorageOptions
    except ImportError:
        print("Fehler: rosbag2_py nicht verfuegbar.")
        print("Bitte ROS2 Humble installieren.")
        sys.exit(1)

    bag_pfad = str(Path(bag_pfad).resolve())

    storage_options = StorageOptions(uri=bag_pfad, storage_id="sqlite3")
    converter_options = ConverterOptions(
        input_serialization_format="cdr", output_serialization_format="cdr"
    )

    reader = SequentialReader()
    reader.open(storage_options, converter_options)

    timestamps = []
    velocities = []
    t0 = None

    while reader.has_next():
        topic, data, t_ns = reader.read_next()
        if topic == "/odom":
            msg = deserialize_message(data, Odometry)
            t_sec = t_ns / 1e9
            if t0 is None:
                t0 = t_sec
            timestamps.append(t_sec - t0)
            velocities.append(msg.twist.twist.linear.x)

    if not timestamps:
        print("Fehler: Keine /odom-Nachrichten in der Rosbag gefunden.")
        sys.exit(1)

    return np.array(timestamps), np.array(velocities)


def analysiere_sprungantwort(timestamps, velocities, soll=SOLL_GESCHWINDIGKEIT):
    """Berechnet Kenngroessen der PID-Sprungantwort.

    Parameter:
        timestamps:  Zeitstempel-Array [s]
        velocities:  Geschwindigkeits-Array [m/s]
        soll:        Sollwert [m/s]

    Rueckgabe:
        Dictionary mit allen Kenngroessen.
    """
    if len(timestamps) < 2:
        print("Fehler: Zu wenige Datenpunkte fuer Analyse.")
        sys.exit(1)

    # Nur Daten ab dem Sprung (t >= 0)
    maske = timestamps >= 0
    t = timestamps[maske]
    v = velocities[maske]

    if len(t) < 2:
        print("Fehler: Keine Daten nach Sprungzeitpunkt.")
        sys.exit(1)

    # --- Anstiegszeit: t(10%) bis t(90%) ---
    schwelle_10 = 0.1 * soll
    schwelle_90 = 0.9 * soll

    t_10 = None
    t_90 = None
    for i in range(len(v)):
        if t_10 is None and v[i] >= schwelle_10:
            t_10 = t[i]
        if t_90 is None and v[i] >= schwelle_90:
            t_90 = t[i]

    if t_10 is not None and t_90 is not None:
        t_rise = t_90 - t_10
    else:
        t_rise = float("nan")

    # --- Ueberschwingen ---
    v_max = np.max(v)
    if soll > 0:
        overshoot_pct = (v_max - soll) / soll * 100.0
    else:
        overshoot_pct = 0.0
    overshoot_pct = max(overshoot_pct, 0.0)  # Kein negatives Ueberschwingen

    # --- Einschwingzeit: dauerhaft innerhalb +/- 5% ---
    toleranz = 0.05 * soll
    t_settle = float("nan")
    # Von hinten suchen: letzte Ueberschreitung der Toleranz
    for i in range(len(v) - 1, -1, -1):
        if abs(v[i] - soll) > toleranz:
            if i + 1 < len(t):
                t_settle = t[i + 1]
            break
    else:
        # Nie ausserhalb der Toleranz
        t_settle = 0.0

    # --- Stationaerer Regelfehler (letzte 20% der Daten) ---
    n_steady = max(1, len(v) // 5)
    v_steady = np.mean(v[-n_steady:])
    if soll > 0:
        e_ss_pct = abs(v_steady - soll) / soll * 100.0
    else:
        e_ss_pct = 0.0

    ergebnisse = {
        "soll_m_s": soll,
        "t_rise_s": t_rise,
        "t_10_s": t_10,
        "t_90_s": t_90,
        "overshoot_pct": overshoot_pct,
        "v_max_m_s": v_max,
        "t_settle_s": t_settle,
        "e_ss_pct": e_ss_pct,
        "v_steady_m_s": v_steady,
        "timestamps": t,
        "velocities": v,
    }

    return ergebnisse


def tuning_empfehlungen(erg):
    """Gibt PID-Tuning-Empfehlungen basierend auf den Analyseergebnissen."""
    print()
    print("### Tuning-Empfehlungen")
    print()
    print(f"Aktuelle PID-Werte: Kp = {KP}, Ki = {KI}, Kd = {KD}")
    print()

    empfehlungen = []

    # Anstiegszeit
    if not math.isnan(erg["t_rise_s"]) and erg["t_rise_s"] > AKZEPTANZ_ANSTIEGSZEIT:
        empfehlungen.append(
            f"- Anstiegszeit zu langsam ({erg['t_rise_s']:.3f} s > {AKZEPTANZ_ANSTIEGSZEIT} s): "
            "Kp erhoehen"
        )

    # Ueberschwingen
    if erg["overshoot_pct"] > AKZEPTANZ_UEBERSCHWINGEN:
        empfehlungen.append(
            f"- Ueberschwingen zu hoch ({erg['overshoot_pct']:.1f}% > {AKZEPTANZ_UEBERSCHWINGEN}%): "
            "Kp reduzieren, Kd > 0 erwaegen"
        )

    # Einschwingzeit
    if not math.isnan(erg["t_settle_s"]) and erg["t_settle_s"] > AKZEPTANZ_EINSCHWINGZEIT:
        empfehlungen.append(
            f"- Einschwingzeit zu lang ({erg['t_settle_s']:.3f} s > {AKZEPTANZ_EINSCHWINGZEIT} s): "
            "Kd erhoehen fuer schnellere Daempfung"
        )

    # Stationaerer Regelfehler
    if erg["e_ss_pct"] > AKZEPTANZ_REGELFEHLER:
        empfehlungen.append(
            f"- Stationaerer Regelfehler zu gross ({erg['e_ss_pct']:.1f}% > {AKZEPTANZ_REGELFEHLER}%): "
            "Ki erhoehen"
        )

    # Schwingung erkennen (Nulldurchgaenge um Sollwert zaehlen)
    v = erg["velocities"]
    soll = erg["soll_m_s"]
    nulldurchgaenge = 0
    for i in range(1, len(v)):
        if (v[i - 1] - soll) * (v[i] - soll) < 0:
            nulldurchgaenge += 1
    if nulldurchgaenge > 6:
        empfehlungen.append(
            f"- Oszillation erkannt ({nulldurchgaenge} Nulldurchgaenge um Sollwert): "
            "Kp reduzieren, Kd > 0 erwaegen"
        )

    if empfehlungen:
        for e in empfehlungen:
            print(e)
    else:
        print("- Alle Kenngroessen innerhalb der Akzeptanzkriterien.")
        print("- Keine Aenderung erforderlich.")


def ausgabe_markdown(erg):
    """Gibt die Sprungantwort-Kenngroessen als Markdown-Tabelle aus."""
    print()
    print("=" * 70)
    print("PID-Sprungantwort-Analyse")
    print("=" * 70)
    print()

    # Ergebnis-Bewertung
    def bewertung(wert, grenze, kleiner_ist_gut=True):
        if math.isnan(wert):
            return "N/A"
        if kleiner_ist_gut:
            return "OK" if wert <= grenze else "NICHT OK"
        return "OK" if wert >= grenze else "NICHT OK"

    print("### Kenngroessen der Sprungantwort")
    print()
    print("| Kenngroesse              | Wert          | Akzeptanz     | Bewertung |")
    print("|:-------------------------|:--------------|:--------------|:----------|")

    t_rise_str = f"{erg['t_rise_s']:.3f} s" if not math.isnan(erg["t_rise_s"]) else "N/A"
    bew_rise = bewertung(erg["t_rise_s"], AKZEPTANZ_ANSTIEGSZEIT)
    print(
        f"| Anstiegszeit (10%-90%)   | {t_rise_str:13s} | < {AKZEPTANZ_ANSTIEGSZEIT} s        | {bew_rise:9s} |"
    )

    print(
        f"| Ueberschwingen           | {erg['overshoot_pct']:.1f} %        | < {AKZEPTANZ_UEBERSCHWINGEN} %        | {bewertung(erg['overshoot_pct'], AKZEPTANZ_UEBERSCHWINGEN):9s} |"
    )

    t_settle_str = f"{erg['t_settle_s']:.3f} s" if not math.isnan(erg["t_settle_s"]) else "N/A"
    bew_settle = bewertung(erg["t_settle_s"], AKZEPTANZ_EINSCHWINGZEIT)
    print(
        f"| Einschwingzeit (+/-5%)   | {t_settle_str:13s} | < {AKZEPTANZ_EINSCHWINGZEIT} s        | {bew_settle:9s} |"
    )

    print(
        f"| Stationaerer Fehler      | {erg['e_ss_pct']:.1f} %        | < {AKZEPTANZ_REGELFEHLER} %         | {bewertung(erg['e_ss_pct'], AKZEPTANZ_REGELFEHLER):9s} |"
    )
    print(
        f"| v_max                    | {erg['v_max_m_s']:.4f} m/s   |               |           |"
    )
    print(
        f"| v_steady                 | {erg['v_steady_m_s']:.4f} m/s   |               |           |"
    )

    tuning_empfehlungen(erg)


def erstelle_plot(erg, speicherpfad=None):
    """Erstellt Sprungantwort-Plot mit Markierungen."""
    t = erg["timestamps"]
    v = erg["velocities"]
    soll = erg["soll_m_s"]

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Ist-Geschwindigkeit
    ax.plot(t, v, "b-", linewidth=1.5, label="Ist-Geschwindigkeit")

    # Sollwert
    ax.axhline(y=soll, color="green", linestyle="--", linewidth=1, label=f"Soll = {soll} m/s")

    # Toleranzband (+/- 5%)
    ax.axhline(y=soll * 1.05, color="gray", linestyle=":", linewidth=0.8, alpha=0.7)
    ax.axhline(
        y=soll * 0.95,
        color="gray",
        linestyle=":",
        linewidth=0.8,
        alpha=0.7,
        label="+/- 5% Toleranz",
    )

    # 10%- und 90%-Schwellen
    ax.axhline(y=soll * 0.1, color="orange", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.axhline(y=soll * 0.9, color="orange", linestyle=":", linewidth=0.8, alpha=0.5)

    # Anstiegszeit markieren
    if erg["t_10_s"] is not None and erg["t_90_s"] is not None:
        ax.axvline(x=erg["t_10_s"], color="orange", linestyle="-", linewidth=0.8, alpha=0.5)
        ax.axvline(x=erg["t_90_s"], color="orange", linestyle="-", linewidth=0.8, alpha=0.5)
        t_mitte = (erg["t_10_s"] + erg["t_90_s"]) / 2
        ax.annotate(
            f"t_rise = {erg['t_rise_s']:.3f} s",
            xy=(t_mitte, soll * 0.5),
            fontsize=9,
            ha="center",
            bbox={"boxstyle": "round,pad=0.3", "fc": "lightyellow"},
        )

    # Ueberschwingen markieren
    if erg["overshoot_pct"] > 0:
        idx_max = np.argmax(v)
        ax.annotate(
            f"OS = {erg['overshoot_pct']:.1f}%",
            xy=(t[idx_max], v[idx_max]),
            xytext=(t[idx_max] + 0.3, v[idx_max] + 0.02),
            arrowprops={"arrowstyle": "->", "color": "red"},
            fontsize=9,
            color="red",
        )

    # Einschwingzeit markieren
    if not math.isnan(erg["t_settle_s"]) and erg["t_settle_s"] > 0:
        ax.axvline(
            x=erg["t_settle_s"] + t[0],
            color="purple",
            linestyle="-.",
            linewidth=1,
            alpha=0.7,
            label=f"t_settle = {erg['t_settle_s']:.3f} s",
        )

    ax.set_xlabel("Zeit [s]")
    ax.set_ylabel("Geschwindigkeit [m/s]")
    ax.set_title(f"PID-Sprungantwort (Kp={KP}, Ki={KI}, Kd={KD})")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=-0.05)

    plt.tight_layout()

    if speicherpfad:
        pfad = Path(speicherpfad)
        fig.savefig(pfad, dpi=150, bbox_inches="tight")
        print(f"\nPlot gespeichert: {pfad}")
    else:
        plt.show()

    plt.close(fig)


def main():
    """Hauptprogramm: Modus bestimmen, Daten erfassen, analysieren, ausgeben."""
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python3 pid_tuning.py live                  # Live-Aufnahme")
        print("  python3 pid_tuning.py bag /pfad/zur/rosbag  # Rosbag-Analyse")
        sys.exit(1)

    modus = sys.argv[1].lower()

    if modus == "live":
        print("Starte Live-Aufnahme...")
        timestamps, velocities = live_aufnahme()
    elif modus == "bag":
        if len(sys.argv) < 3:
            print("Fehler: Bitte Pfad zur Rosbag-Datei angeben.")
            sys.exit(1)
        bag_pfad = sys.argv[2]
        print(f"Lese Rosbag: {bag_pfad}")
        timestamps, velocities = rosbag_analyse(bag_pfad)
    else:
        print(f"Fehler: Unbekannter Modus '{modus}'")
        print("Verfuegbare Modi: live, bag")
        sys.exit(1)

    if len(timestamps) == 0:
        print("Keine Daten aufgezeichnet!")
        return

    print(f"Daten: {len(timestamps)} Samples, {timestamps[-1] - timestamps[0]:.1f} s")

    # Analyse
    ergebnisse = analysiere_sprungantwort(timestamps, velocities)

    # Ausgabe
    ausgabe_markdown(ergebnisse)

    # Plot
    skript_verzeichnis = Path(__file__).parent
    plot_pfad = skript_verzeichnis / "pid_sprungantwort.png"
    erstelle_plot(ergebnisse, speicherpfad=plot_pfad)

    # JSON-Export fuer validation_report.py
    json_export = {
        "soll_m_s": SOLL_GESCHWINDIGKEIT,
        "rise_time_ms": round(ergebnisse["t_rise_s"] * 1000.0, 1)
        if not math.isnan(ergebnisse["t_rise_s"])
        else None,
        "overshoot_pct": round(ergebnisse["overshoot_pct"], 2),
        "settle_time_ms": round(ergebnisse["t_settle_s"] * 1000.0, 1)
        if not math.isnan(ergebnisse["t_settle_s"])
        else None,
        "steady_state_error_pct": round(ergebnisse["e_ss_pct"], 2),
        "v_max_m_s": round(float(ergebnisse["v_max_m_s"]), 4),
        "v_steady_m_s": round(float(ergebnisse["v_steady_m_s"]), 4),
        "pid": {
            "Kp": KP,
            "Ki": KI,
            "Kd": KD,
        },
        "num_samples": len(ergebnisse["timestamps"]),
    }
    json_pfad = skript_verzeichnis / "pid_results.json"
    with open(json_pfad, "w") as f:
        json.dump(json_export, f, indent=2)
    print(f"JSON-Export: {json_pfad}")


if __name__ == "__main__":
    main()
