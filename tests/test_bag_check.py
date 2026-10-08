"""Tests fuer die ROS-freien Funktionen von amr/scripts/bag_check.py (K7-V, Phase 3).

Die Statistik- und Launch-Funktionen werden mit synthetischen Daten geprueft.
Das Lesen einer Aufnahme (rosbag2_py) ist hier nicht abgedeckt; es wird im
Container mit einer Probeaufnahme geprueft.
"""

from __future__ import annotations

import math

import bag_check as bc
import pytest

NS = bc.NS_PER_S
SYNC_T0 = 1_791_490_000 * NS  # Oktober 2026, gesyncte Epoch-Zeit


def test_percentile_naechster_rang():
    werte = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert bc.percentile(werte, 0.5) == 3.0
    assert bc.percentile(werte, 0.95) == 5.0
    assert bc.percentile(werte, 0.0) == 1.0
    assert math.isnan(bc.percentile([], 0.5))


def test_verteilung():
    assert bc.verteilung([]) is None
    v = bc.verteilung([3.0, 1.0, 2.0])
    assert v is not None
    assert (v.n, v.minimum, v.median, v.maximum) == (3, 1.0, 2.0, 3.0)


def test_rate_ohne_luecke():
    zeiten = [SYNC_T0 + i * NS // 10 for i in range(21)]  # 10 Hz ueber 2 s
    r = bc.rate_stats(zeiten, 10.0)
    assert r.n == 21
    assert r.mittel_hz == pytest.approx(10.0)
    assert r.min_hz == pytest.approx(10.0)
    assert r.luecken == 0


def test_rate_mit_luecke():
    zeiten = [SYNC_T0 + i * NS // 10 for i in range(10)]
    zeiten.append(zeiten[-1] + NS // 2)  # 500 ms, also > 2 Sollperioden (200 ms)
    r = bc.rate_stats(zeiten, 10.0)
    assert r.luecken == 1
    assert r.max_luecke_ms == pytest.approx(500.0)
    assert r.min_hz == pytest.approx(2.0)


def test_rate_ereignisgetrieben_und_zu_kurz():
    zeiten = [SYNC_T0, SYNC_T0 + 5 * NS]
    assert bc.rate_stats(zeiten, 0).luecken == 0
    einzeln = bc.rate_stats([SYNC_T0], 20.0)
    assert einzeln.n == 1
    assert math.isnan(einzeln.mittel_hz)


def test_stempelabstand_und_ungesynct():
    paare = [
        (SYNC_T0 + 2_000_000, SYNC_T0),  # 2 ms alt
        (SYNC_T0, SYNC_T0 + 1_000_000),  # 1 ms in der Zukunft
        (SYNC_T0, 42 * NS),  # Zeit seit MCU-Boot, ohne Sync
    ]
    offs, unsynced = bc.stamp_offsets_ms(paare)
    assert unsynced == 1
    assert offs == pytest.approx([2.0, -1.0])


def test_seq_luecken_und_ruecksprung():
    assert bc.seq_stats([0, 1, 2, 4, 5]).fehlend == 1
    s = bc.seq_stats([0, 1, 2, 0, 1])
    assert (s.ruecksprung, s.fehlend, s.erste, s.letzte) == (1, 0, 0, 1)
    leer = bc.seq_stats([])
    assert (leer.n, leer.erste) == (0, None)


def test_detektionen():
    t = SYNC_T0 / NS
    records = [
        (SYNC_T0 + 50_000_000, {"timestamp": t, "capture_time": t - 0.03, "seq": 0}),
        (SYNC_T0 + 250_000_000, {"timestamp": t + 0.2, "capture_time": t + 0.17, "seq": 1}),
        (SYNC_T0 + 450_000_000, {"timestamp": t + 0.4, "seq": 3, "detections": [{"label": "x"}]}),
        (SYNC_T0 + 500_000_000, None),  # ungueltiges JSON
    ]
    st = bc.detection_stats(records)
    assert (st.pakete, st.ungueltig, st.mit_capture, st.mit_seq) == (4, 1, 2, 3)
    assert (st.mit_beiden, st.capture_ok, st.mit_objekten) == (2, 2, 1)
    assert st.verarbeitung is not None
    assert st.verarbeitung.maximum == pytest.approx(30.0, abs=1e-3)
    assert st.transport is not None
    assert st.transport.median == pytest.approx(50.0, abs=1e-3)
    assert st.seq.fehlend == 1


def test_detektion_capture_nach_timestamp_wird_erkannt():
    t = SYNC_T0 / NS
    st = bc.detection_stats([(SYNC_T0, {"timestamp": t, "capture_time": t + 0.01})])
    assert (st.mit_beiden, st.capture_ok) == (1, 0)


def test_regressionsgrenze_nach_l1():
    assert bc.regression_grenze(19.85, 15.0, 0.25) == pytest.approx(15.0)
    assert bc.regression_grenze(38.07, 20.0, 0.25) == pytest.approx(28.5525)
    assert bc.regression_grenze(7.51, 5.0, None) == pytest.approx(5.0)
    assert bc.regression_grenze(15.86, None, None) is None


def test_bewertung_ergebnis():
    odom = {
        "anforderung_min_hz": 10.0,
        "k0_hz": 19.85,
        "toleranz_min_hz": 15.0,
        "toleranz_max_abfall": 0.25,
    }
    assert bc.bewertung_ergebnis(odom, 20.0) == (
        "Anforderung erfuellt; Toleranz eingehalten (Grenze 15,00 Hz)"
    )
    assert "Toleranz NICHT eingehalten" in bc.bewertung_ergebnis(odom, 12.0)
    assert "Anforderung NICHT erfuellt" in bc.bewertung_ergebnis(odom, 9.0)
    assert bc.bewertung_ergebnis(odom, math.nan) == "kein Messwert"
    assert bc.bewertung_ergebnis({"k0_hz": 15.86}, 16.0) == "kein Kriterium"


def test_launch_zeile():
    zeile = "ros2 launch my_bot full_stack.launch.py use_camera:=True use_nav:=true"
    assert bc.parse_launch_line(zeile) == {"use_camera": "True", "use_nav": "true"}
    assert bc.parse_launch_line("ros2 launch my_bot full_stack.launch.py") == {}


SHOW_ARGS = """Arguments (pass arguments as '<name>:=<value>'):

    'use_slam':
        SLAM Toolbox starten (async Modus)
        (default: 'True')

    'drive_serial_port':
        Serieller Port fuer micro-ROS Agent Drive-Node
        (default: '/dev/amr_drive')

    'params_file':
        Pfad zur Nav2 Parameter-YAML-Datei
        (default: PathJoinSubstitution('FindPackageShare(pkg='my_bot'), 'config'))

    'use_dashboard':
        Benutzeroberflaeche
        (default: 'False')
"""


def test_show_args():
    defaults = bc.parse_show_args(SHOW_ARGS)
    assert defaults == {
        "use_slam": "True",
        "drive_serial_port": "/dev/amr_drive",
        "use_dashboard": "False",
    }


def test_launch_vergleich_woertlich():
    soll = {"use_nav": "True", "use_dashboard": "True", "use_can": "False", "use_x": "True"}
    explizit = {"use_nav": "true", "use_dashboard": "True"}
    standard = {"use_nav": "True", "use_dashboard": "False", "use_can": "False"}
    wirksam, abw = bc.compare_launch(soll, explizit, standard)
    assert wirksam == {"use_nav": "true", "use_dashboard": "True", "use_can": "False"}
    assert len(abw) == 2
    assert abw[0].startswith("use_nav=true, erwartet True (Schreibweise")
    assert abw[1].startswith("use_x: Wert nicht bestimmbar")


def test_launch_vergleich_yaml_bool():
    # Unquotiertes True im YAML wird zu bool und muss trotzdem 'True' bedeuten
    _, abw = bc.compare_launch({"use_slam": True}, {}, {"use_slam": "True"})
    assert abw == []


def test_fmt():
    assert bc.fmt(1.26) == "1,3"
    assert bc.fmt(None) == "n/a"
    assert bc.fmt(math.nan) == "n/a"
    assert bc.fmt_anteil(3, 4) == "75,0 % (3/4)"
    assert bc.fmt_anteil(0, 0) == "n/a"


def test_speichergroesse_ohne_zusatzdateien(tmp_path):
    bag = tmp_path / "20261008_2335_probe"
    bag.mkdir()
    (bag / "20261008_2335_probe_0.db3").write_bytes(b"x" * 1000)
    (bag / "bag_check.md").write_text("Bericht", encoding="utf-8")  # zaehlt nicht
    assert bc.speichergroesse(bag, ["20261008_2335_probe_0.db3"]) == 1000
    # aeltere rosbag2-Staende nennen den Ordner mit
    assert bc.speichergroesse(bag, ["20261008_2335_probe/20261008_2335_probe_0.db3"]) == 1000
    assert bc.speichergroesse(bag, ["fehlt.db3"]) == 0


def test_katalog_konsistent():
    yaml = pytest.importorskip("yaml")
    cfg = yaml.safe_load(bc.default_config_path().read_text(encoding="utf-8"))
    topics = cfg["topics"]
    erlaubt = {"header", "tf", "tf_static", "json", "keine"}
    assert all(e["stempel"] in erlaubt for e in topics.values())
    for name, szene in cfg["szenen"].items():
        assert set(szene["erwartet"]) <= set(topics), name
        assert szene["launch"].get("use_can") == "False", name
    assert {e["topic"] for e in cfg["bewertung"]} <= set(topics)
