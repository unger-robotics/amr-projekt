#!/usr/bin/env python3
"""S-A Auswertung: Verlust je ID, Zwischenankunftszeiten, Burst-Fenster, Zaehler-Deltas.

Aufruf:  python3 s_a_analyse.py validation/P-CAN2/<datum>_<Label> [--window-us 1000]
Eingabe: candump.log (candump -L, inkl. Error-Frames), stats_before.{json,txt},
         stats_after.{json,txt}, meta.txt
Ausgabe: Markdown-Tabellen auf stdout (in P-CAN2-A.md uebernehmen).
Nur Standardbibliothek, Python >= 3.10.

Error-Frames (SocketCAN CAN_ERR_FLAG 0x20000000) werden aus der ID-Statistik
ausgeschlossen und getrennt gezaehlt. Ein RX-Pufferueberlauf des MCP2515 erscheint
als Error-Frame mit CAN_ERR_CRTL (0x04 in der Kennung) und Datenbyte 1 mit gesetztem
CAN_ERR_CRTL_RX_OVERFLOW (0x01); der Treiber erhoeht dabei rx_over_errors und rx_errors.

Zeitstempel im candump-Log sind Host-Zeiten beim Auslesen des MCP2515 ueber SPI, nicht
Buszeiten: Aufeinanderfolgende Frames liegen dadurch mindestens ca. 140 us auseinander
(Probelauf 03.09.2026: min 141 us, p10 196 us). Ein 300-us-Fenster erfasst daher keine
Bursts; Standard ist 1000 us, die Zaehlung wird fuer mehrere Fenster ausgegeben.
"""

import bisect
import json
import re
import sys
from pathlib import Path
from statistics import median

# Soll-Raten des Bestands [Hz]. Quellen: amr/mcu_firmware/*/include/config_*.h und
# src/main.cpp (Sendetakte), identisch mit EXPECTED in amr/scripts/can_validation_test.py.
# Event-Nachrichten (0x141 Battery-Shutdown, 0x150 Servo-Kommando Pi -> Sensor) und
# unbekannte IDs bekommen keine Verlustangabe.
EXPECTED_HZ = {
    0x110: 10,
    0x120: 20,
    0x130: 50,
    0x131: 50,
    0x140: 2,
    0x1F0: 1,
    0x200: 20,
    0x201: 20,
    0x210: 10,
    0x220: 10,
    0x2F0: 1,
}
CAN_ERR_FLAG = 0x20000000
CAN_ERR_CRTL = 0x00000004
CAN_ERR_CRTL_RX_OVERFLOW = 0x01
LINE = re.compile(r"^\((\d+)\.(\d+)\)\s+(\S+)\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)")


def read_log(path):
    """Liefert (Datenframes, Error-Frames); je Eintrag (t_us, id, dlc, data)."""
    frames, errors = [], []
    with open(path) as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            t_us = int(m.group(1)) * 1_000_000 + int(m.group(2).ljust(6, "0")[:6])
            can_id = int(m.group(4), 16)
            data = bytes.fromhex(m.group(5))
            entry = (t_us, can_id, len(data), data)
            if can_id & CAN_ERR_FLAG:
                errors.append(entry)
            else:
                frames.append(entry)
    frames.sort()
    errors.sort()
    return frames, errors


def read_stats(base):
    """Zaehler aus <base>.json (bevorzugt) oder <base>.txt lesen."""
    stats = {}
    json_path = Path(f"{base}.json")
    txt_path = Path(f"{base}.txt")
    if json_path.exists():
        link = json.loads(json_path.read_text())[0]
        rx = link.get("stats64", {}).get("rx", {})
        stats["rx_packets"] = rx.get("packets")
        stats["rx_errors"] = rx.get("errors")
        stats["rx_over_errors"] = rx.get("over_errors")
        stats["rx_dropped"] = rx.get("dropped")
        xstats = link.get("linkinfo", {}).get("info_xstats", {})
        for k in (
            "bus_error",
            "restarts",
            "arbitration_lost",
            "error_warning",
            "error_passive",
            "bus_off",
        ):
            stats[k] = xstats.get(k)
    if txt_path.exists():
        txt = txt_path.read_text()
        for k, v in re.findall(r"^(\w+)=(\d+)$", txt, re.M):
            stats.setdefault(k, int(v))
        # Zeile "re-started bus-errors arbit-lost error-warn error-pass bus-off", Werte darunter
        m = re.search(
            r"re-started\s+bus-errors\s+arbit-lost\s+error-warn\s+error-pass\s+bus-off\s*\n"
            r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            txt,
        )
        if m:
            for k, v in zip(
                (
                    "restarts",
                    "bus_error",
                    "arbitration_lost",
                    "error_warning",
                    "error_passive",
                    "bus_off",
                ),
                m.groups(),
                strict=True,
            ):
                stats.setdefault(k, int(v))
    if not stats:
        raise FileNotFoundError(base)
    return stats


def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    k = min(len(s) - 1, max(0, int(round(p / 100 * (len(s) - 1)))))
    return s[k]


def print_counter_deltas(out):
    try:
        b = read_stats(out / "stats_before")
        a = read_stats(out / "stats_after")
    except FileNotFoundError:
        print("(stats_before/after fehlen: Zaehler-Deltas uebersprungen)\n")
        return
    print("## Zaehler-Deltas (nachher - vorher)\n")
    print("| Zaehler | vorher | nachher | Delta |\n| --- | --- | --- | --- |")
    keys = (
        "rx_packets",
        "rx_errors",
        "rx_over_errors",
        "rx_fifo_errors",
        "rx_missed_errors",
        "rx_dropped",
        "bus_error",
        "arbitration_lost",
        "error_warning",
        "error_passive",
        "bus_off",
        "restarts",
    )
    for k in keys:
        if b.get(k) is None or a.get(k) is None:
            continue
        print(f"| {k} | {b[k]} | {a[k]} | {a[k] - b[k]} |")
    print()


def print_per_id(frames, dur_s):
    per_id = {}
    dlc_of = {}
    for t, cid, dlc, _data in frames:
        per_id.setdefault(cid, []).append(t)
        dlc_of.setdefault(cid, dlc)
    print("## Je ID: Empfang, Verlust, Zwischenankunftszeit\n")
    print(
        "| ID | Soll [Hz] | erwartet | empfangen | Verlust [%] | dt Median [ms] "
        "| dt p99 [ms] | dt max [ms] |"
    )
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    bits_total = 0.0
    for cid in sorted(per_id):
        ts = per_id[cid]
        dts = [(ts[i] - ts[i - 1]) / 1000 for i in range(1, len(ts))]
        hz = EXPECTED_HZ.get(cid)
        exp = round(hz * dur_s) if hz else None
        # < 0 waere Rundung der Messdauer, daher auf 0 begrenzt
        loss = f"{max(0.0, (1 - len(ts) / exp) * 100):.2f}" if exp else "-"
        bits_total += (47 + 8 * dlc_of[cid]) * len(ts) / dur_s
        if dts:
            dt_cols = f"{median(dts):.1f} | {percentile(dts, 99):.1f} | {max(dts):.1f}"
        else:
            dt_cols = "- | - | -"
        print(f"| 0x{cid:03X} | {hz or '-'} | {exp or '-'} | {len(ts)} | {loss} | {dt_cols} |")
    print(f"\nRechnerische Buslast (ohne Stuffing): {bits_total / 1e6 * 100:.2f} % bei 1 Mbit/s\n")


def count_bursts(frames, window_us):
    """Zaehlt Fenster mit >= 3 Frames innerhalb window_us; liefert (Anzahl, IDs ab 3. Frame)."""
    bursts, third = 0, {}
    i = 0
    while i < len(frames):
        j = i
        while j + 1 < len(frames) and frames[j + 1][0] - frames[i][0] <= window_us:
            j += 1
        if j - i + 1 >= 3:
            bursts += 1
            for _t, cid, _dlc, _data in frames[i + 2 : j + 1]:
                third[cid] = third.get(cid, 0) + 1
            i = j + 1
        else:
            i += 1
    return bursts, third


def print_bursts(frames, window_us):
    """Burst-Fenster (Kandidaten fuer den 2-Puffer-Ueberlauf des MCP2515)."""
    print("## Burst-Fenster (>= 3 Frames innerhalb Fenster)\n")
    print("| Fenster [us] | Anzahl |\n| --- | --- |")
    for w in sorted({300, 500, 1000, 2000, window_us}):
        print(f"| {w} | {count_bursts(frames, w)[0]} |")
    print()
    _bursts, third = count_bursts(frames, window_us)
    if third:
        print(
            f"| ID als 3. oder spaeterer Frame im Burst ({window_us} us) | Anzahl |\n| --- | --- |"
        )
        for cid, n in sorted(third.items(), key=lambda x: -x[1]):
            print(f"| 0x{cid:03X} | {n} |")
        print()


def print_error_frames(frames, errors):
    """Error-Frames zaehlen; bei RX-Ueberlauf die zuletzt empfangene Daten-ID zuordnen."""
    overflow = [
        e
        for e in errors
        if e[1] & CAN_ERR_CRTL and len(e[3]) > 1 and e[3][1] & CAN_ERR_CRTL_RX_OVERFLOW
    ]
    print(
        f"## Error-Frames im Log: {len(errors)}, davon RX-Ueberlauf (CAN_ERR_CRTL_RX_OVERFLOW): {len(overflow)}\n"
    )
    if not overflow:
        return
    # Fuer jeden Ueberlauf: welche Daten-ID kam unmittelbar davor am Pi an
    prev = {}
    times = [f[0] for f in frames]
    for t, _cid, _dlc, _data in overflow:
        k = bisect.bisect_right(times, t) - 1
        if k >= 0:
            cid = frames[k][1]
            prev[cid] = prev.get(cid, 0) + 1
    print("| Daten-ID unmittelbar vor dem Ueberlauf-Frame | Anzahl |\n| --- | --- |")
    for cid, n in sorted(prev.items(), key=lambda x: -x[1]):
        print(f"| 0x{cid:03X} | {n} |")
    print()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    window_us = 1000
    if "--window-us" in sys.argv:
        window_us = int(sys.argv[sys.argv.index("--window-us") + 1])

    frames, errors = read_log(out / "candump.log")
    if not frames:
        sys.exit("candump.log leer oder Format nicht erkannt (candump -L erwartet)")
    t0, t1 = frames[0][0], frames[-1][0]
    dur_s = (t1 - t0) / 1e6
    print(f"# S-A Auswertung: {out.name}\n")
    print(
        f"Datenframes gesamt: {len(frames)}, Messdauer aus Log: {dur_s:.1f} s, "
        f"mittlere Rate: {len(frames) / dur_s:.1f} Frames/s\n"
    )
    print_counter_deltas(out)
    print_per_id(frames, dur_s)
    print_bursts(frames, window_us)
    print_error_frames(frames, errors)
    print(
        "Lesart: Faellt der Verlust genau auf die IDs, die im Burst als 3. Frame ankommen, "
        "und steigt rx_over_errors (Ueberlauf-Error-Frames im Log), ist es Fall 1 (MCP2515). "
        "Steigt bus_error, Fall 2. Beides 0 bei Verlust > 0,1 %: Fall 3."
    )


if __name__ == "__main__":
    main()
