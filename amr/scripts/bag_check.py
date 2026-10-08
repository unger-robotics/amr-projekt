#!/usr/bin/env python3
"""Prueft eine Referenzaufnahme (rosbag2, sqlite3) und schreibt einen Markdown-Bericht.

K7-V, Phase 3 (transfer/auftrag-k7v.md). Topicliste, Sollraten, Szenen und
Bewertungsgrundlagen stehen in my_bot/config/reference_bags.yaml.

Ausgewertet werden:
  - je Topic Anzahl, mittlere und minimale Rate, Luecken > 2 Sollperioden,
    Nachrichtengroesse; fehlende erwartete Topics und abweichende Typen
  - Abstand Aufnahmezeit minus header.stamp (Median, P95, Max); Stempel mit
    sec < 1e9 (MCU ohne Zeitsync) werden getrennt gezaehlt
  - /tf je Kante; /vision/detections: capture_time <= timestamp, Abstand
    timestamp - capture_time, Luecken und Ruecksprunge in seq
  - Bewertung nach Anforderungsliste L1 v1.1, Abschnitt 10.2 (Anforderung,
    K0-Baseline, Messwert und Regressionstoleranz getrennt)

Aufnahmezeit ist der Empfangszeitpunkt beim Recorder (Systemuhr). Median und
P95 nach naechstem Rang wie in der Phase-0-Messung (bericht-k7v-phase0.md,
Anhang A). Die Statistikfunktionen kommen ohne ROS aus (pytest auf dem Host);
rosbag2_py, rclpy und yaml werden erst beim Lesen geladen.

Verwendung (im Container amr_ros2 oder amr_ros2_dev):
  ros2 run my_bot bag_check /amr_bags/<JJJJMMTT_HHMM>_<szene> [-o bag_check.md]
  python3 /scripts/bag_check.py /amr_bags/<JJJJMMTT_HHMM>_<szene>

Hilfsmodi fuer amr/scripts/record_reference_bags.sh:
  --szene-plan SZENE --launch-zeile ZEILE   Topicliste und Pruefung der Launch-Argumente
  --metadaten BAGORDNER --szene SZENE ...   schreibt metadata_amr.yaml

Exit-Code: 0 = in Ordnung, 1 = Befund (erwartetes Topic fehlt, Typ weicht ab),
2 = Bedien- oder Lesefehler.
"""

from __future__ import annotations

import argparse
import json
import math
import numbers
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

NS_PER_S = 1_000_000_000
# Stempel vor 2001-09-09 (sec < 1e9): MCU ohne Zeitsync, Zeit seit Boot
UNSYNCED_LIMIT_NS = 10**9 * NS_PER_S
LAUNCH_DATEI = "full_stack.launch.py"
CONFIG_NAME = "reference_bags.yaml"
METADATEN_NAME = "metadata_amr.yaml"

SHOW_ARGS_NAME_RE = re.compile(r"^\s*'(?P<name>[^']+)':\s*$")
SHOW_ARGS_DEFAULT_RE = re.compile(r"^\s*\(default: '(?P<wert>[^']*)'\)\s*$")


# ---------------------------------------------------------------------------
# Statistik (ohne ROS)
# ---------------------------------------------------------------------------


def percentile(sorted_vals: list[float], p: float) -> float:
    """Perzentil nach naechstem Rang (wie Phase 0, Anhang A); Liste aufsteigend sortiert."""
    if not sorted_vals:
        return math.nan
    k = min(len(sorted_vals) - 1, max(0, int(round(p * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


@dataclass
class Verteilung:
    """Kenngroessen einer Messreihe (Einheit wie die Eingabe)."""

    n: int
    minimum: float
    median: float
    p95: float
    maximum: float


def verteilung(values: list[float]) -> Verteilung | None:
    """Min, Median, P95 und Max einer Messreihe; None bei leerer Reihe."""
    if not values:
        return None
    s = sorted(values)
    return Verteilung(len(s), s[0], percentile(s, 0.5), percentile(s, 0.95), s[-1])


@dataclass
class Rate:
    """Rate aus Aufnahmezeiten."""

    n: int
    mittel_hz: float
    min_hz: float
    luecken: int
    max_luecke_ms: float


def rate_stats(times_ns: list[int], soll_hz: float) -> Rate:
    """Mittlere Rate, minimale Rate (1/groesster Abstand) und Luecken > 2 Sollperioden.

    Luecken werden nur bei soll_hz > 0 gezaehlt (ereignisgetriebene und latched
    Topics haben keine Sollperiode).
    """
    n = len(times_ns)
    if n < 2:
        return Rate(n, math.nan, math.nan, 0, math.nan)
    t = sorted(times_ns)
    dts = [b - a for a, b in pairwise(t)]
    span_ns = t[-1] - t[0]
    max_dt = max(dts)
    mittel = (n - 1) * NS_PER_S / span_ns if span_ns > 0 else math.nan
    min_hz = NS_PER_S / max_dt if max_dt > 0 else math.nan
    luecken = 0
    if soll_hz > 0:
        grenze_ns = 2 * NS_PER_S / soll_hz
        luecken = sum(1 for dt in dts if dt > grenze_ns)
    return Rate(n, mittel, min_hz, luecken, max_dt / 1e6)


def stamp_offsets_ms(pairs: list[tuple[int, int]]) -> tuple[list[float], int]:
    """Aufnahmezeit minus Stempel in ms; Stempel ohne Zeitsync (sec < 1e9) nur gezaehlt."""
    offsets: list[float] = []
    unsynced = 0
    for t_rx, stamp in pairs:
        if stamp < UNSYNCED_LIMIT_NS:
            unsynced += 1
        else:
            offsets.append((t_rx - stamp) / 1e6)
    return offsets, unsynced


@dataclass
class SeqStats:
    """Auswertung der Sequenznummern in Empfangsreihenfolge."""

    n: int
    erste: int | None
    letzte: int | None
    fehlend: int
    ruecksprung: int


def seq_stats(seqs: list[int]) -> SeqStats:
    """Fehlende Nummern und Ruecksprunge (z. B. Neustart des Runners) in seq."""
    if not seqs:
        return SeqStats(0, None, None, 0, 0)
    fehlend = 0
    ruecksprung = 0
    for a, b in pairwise(seqs):
        if b > a + 1:
            fehlend += b - a - 1
        elif b <= a:
            ruecksprung += 1
    return SeqStats(len(seqs), seqs[0], seqs[-1], fehlend, ruecksprung)


def _as_float(value: Any) -> float | None:
    # bool ist eine Unterklasse von int und zaehlt hier nicht als Zahl
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        return None
    return float(value)


@dataclass
class DetektionStats:
    """Auswertung von /vision/detections (Zeiten in ms)."""

    pakete: int
    ungueltig: int
    mit_capture: int
    mit_seq: int
    mit_beiden: int  # capture_time und timestamp vorhanden
    capture_ok: int
    mit_objekten: int
    verarbeitung: Verteilung | None  # timestamp - capture_time
    transport: Verteilung | None  # Aufnahmezeit - timestamp
    alter: Verteilung | None  # Aufnahmezeit - capture_time
    seq: SeqStats


def detection_stats(records: list[tuple[int, Any]]) -> DetektionStats:
    """records: (Aufnahmezeit in ns, geparstes JSON oder None bei ungueltigem JSON)."""
    ungueltig = mit_capture = mit_beiden = capture_ok = mit_objekten = 0
    seqs: list[int] = []
    verarbeitung: list[float] = []
    transport: list[float] = []
    alter: list[float] = []
    for t_rx, payload in records:
        if not isinstance(payload, dict):
            ungueltig += 1
            continue
        ts = _as_float(payload.get("timestamp"))
        cap = _as_float(payload.get("capture_time"))
        seq = payload.get("seq")
        if isinstance(seq, int) and not isinstance(seq, bool):
            seqs.append(seq)
        if payload.get("detections"):
            mit_objekten += 1
        t_rx_s = t_rx / NS_PER_S
        if ts is not None:
            transport.append((t_rx_s - ts) * 1e3)
        if cap is not None:
            mit_capture += 1
            alter.append((t_rx_s - cap) * 1e3)
            if ts is not None:
                mit_beiden += 1
                verarbeitung.append((ts - cap) * 1e3)
                if cap <= ts:
                    capture_ok += 1
    return DetektionStats(
        pakete=len(records),
        ungueltig=ungueltig,
        mit_capture=mit_capture,
        mit_seq=len(seqs),
        mit_beiden=mit_beiden,
        capture_ok=capture_ok,
        mit_objekten=mit_objekten,
        verarbeitung=verteilung(verarbeitung),
        transport=verteilung(transport),
        alter=verteilung(alter),
        seq=seq_stats(seqs),
    )


def regression_grenze(
    k0_hz: float | None, toleranz_min_hz: float | None, max_abfall: float | None
) -> float | None:
    """Untere Grenze der Regressionstoleranz nach L1 Abschnitt 10.2; None ohne Kriterium."""
    grenzen: list[float] = []
    if toleranz_min_hz is not None:
        grenzen.append(float(toleranz_min_hz))
    if max_abfall is not None and k0_hz is not None:
        grenzen.append((1.0 - float(max_abfall)) * float(k0_hz))
    return max(grenzen) if grenzen else None


# ---------------------------------------------------------------------------
# Launch-Argumente (ohne ROS)
# ---------------------------------------------------------------------------


def parse_launch_line(line: str) -> dict[str, str]:
    """name:=wert-Paare hinter full_stack.launch.py aus der Befehlszeile von ros2 launch."""
    tokens = line.split()
    if LAUNCH_DATEI in tokens:
        tokens = tokens[tokens.index(LAUNCH_DATEI) + 1 :]
    args: dict[str, str] = {}
    for tok in tokens:
        if ":=" in tok:
            name, _, wert = tok.partition(":=")
            args[name] = wert.strip("'\"")
    return args


def parse_show_args(text: str) -> dict[str, str]:
    """Standardwerte aus 'ros2 launch ... --show-args'; nur woertliche Werte in Hochkommas."""
    defaults: dict[str, str] = {}
    name: str | None = None
    for line in text.splitlines():
        m_name = SHOW_ARGS_NAME_RE.match(line)
        if m_name:
            name = m_name.group("name")
            continue
        m_default = SHOW_ARGS_DEFAULT_RE.match(line)
        if m_default and name is not None:
            defaults[name] = m_default.group("wert")
            name = None
    return defaults


def compare_launch(
    soll: dict[str, Any], explizit: dict[str, str], standard: dict[str, str] | None
) -> tuple[dict[str, str], list[str]]:
    """Wirksame Werte der geprueften Argumente und Abweichungen vom Szenenkatalog.

    Verglichen wird woertlich, weil die Bedingungen fuer Nav2 und die
    Benutzeroberflaeche in full_stack.launch.py auf 'True'/'False' pruefen (B-V10).
    """
    wirksam: dict[str, str] = {}
    abweichungen: list[str] = []
    for name, wert_soll_roh in soll.items():
        wert_soll = str(wert_soll_roh)
        if name in explizit:
            wert = explizit[name]
        elif standard is not None and name in standard:
            wert = standard[name]
        else:
            abweichungen.append(f"{name}: Wert nicht bestimmbar, erwartet {wert_soll}")
            continue
        wirksam[name] = wert
        if wert != wert_soll:
            hinweis = ""
            if wert.lower() == wert_soll.lower():
                hinweis = " (Schreibweise: der Launch vergleicht woertlich, B-V10)"
            abweichungen.append(f"{name}={wert}, erwartet {wert_soll}{hinweis}")
    return wirksam, abweichungen


# ---------------------------------------------------------------------------
# Formatierung (ohne ROS)
# ---------------------------------------------------------------------------


def fmt(value: float | None, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma; n/a fuer fehlende Werte."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{value:.{digits}f}".replace(".", ",")


def fmt_anteil(teil: int, ganz: int) -> str:
    if ganz == 0:
        return "n/a"
    return f"{fmt(100.0 * teil / ganz, 1)} % ({teil}/{ganz})"


def _zeile(*zellen: object) -> str:
    return "| " + " | ".join(str(z) for z in zellen) + " |"


def _tabelle(kopf: list[str], zeilen: list[list[object]]) -> list[str]:
    out = [_zeile(*kopf), _zeile(*["---"] * len(kopf))]
    out.extend(_zeile(*z) for z in zeilen)
    return out


def _verteilung_zellen(v: Verteilung | None) -> list[str]:
    if v is None:
        return ["n/a"] * 4
    return [fmt(v.minimum), fmt(v.median), fmt(v.p95), fmt(v.maximum)]


# ---------------------------------------------------------------------------
# Konfiguration und Metadaten (yaml erst beim Aufruf)
# ---------------------------------------------------------------------------


def default_config_path() -> Path:
    """Sucht reference_bags.yaml: Repo (Host), Quellbaum im Container, Share-Verzeichnis."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "pi5" / "ros2_ws" / "src" / "my_bot" / "config" / CONFIG_NAME,
        Path("/ros2_ws/src/my_bot/config") / CONFIG_NAME,
    ]
    try:
        from ament_index_python.packages import get_package_share_directory

        candidates.append(Path(get_package_share_directory("my_bot")) / "config" / CONFIG_NAME)
    except (ImportError, LookupError, ValueError):
        pass
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"{CONFIG_NAME} nicht gefunden: {', '.join(map(str, candidates))}")


def load_yaml(path: Path) -> Any:
    import yaml

    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def szene_eintrag(cfg: dict[str, Any], szene: str) -> dict[str, Any]:
    szenen = cfg.get("szenen", {})
    if szene not in szenen:
        raise KeyError(f"Szene '{szene}' unbekannt (bekannt: {', '.join(szenen)})")
    return szenen[szene]


def launch_defaults() -> dict[str, str] | None:
    """Standardwerte der Launch-Argumente per --show-args; None, wenn nicht ermittelbar."""
    try:
        out = subprocess.run(
            ["ros2", "launch", "my_bot", LAUNCH_DATEI, "--show-args"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_show_args(out) or None


def rosbag2_version() -> str:
    try:
        return subprocess.run(
            ["dpkg-query", "-W", "-f=${Version}", "ros-humble-rosbag2"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unbekannt"


def lese_metadaten_amr(bag: Path) -> dict[str, Any]:
    pfad = bag / METADATEN_NAME
    if not pfad.is_file():
        return {}
    daten = load_yaml(pfad)
    return daten if isinstance(daten, dict) else {}


# ---------------------------------------------------------------------------
# Lesen der Aufnahme (rosbag2_py)
# ---------------------------------------------------------------------------


@dataclass
class TopicDaten:
    name: str
    typ: str
    zeiten: list[int] = field(default_factory=list)
    groessen: list[int] = field(default_factory=list)
    stempel: list[tuple[int, int]] = field(default_factory=list)
    frames: set[str] = field(default_factory=set)
    kanten: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    json: list[tuple[int, Any]] = field(default_factory=list)


@dataclass
class BagDaten:
    pfad: Path
    start_ns: int
    dauer_ns: int
    nachrichten: int
    groesse_b: int
    speicher: str
    topics: dict[str, TopicDaten]


def _stamp_ns(stamp: Any) -> int:
    return int(stamp.sec) * NS_PER_S + int(stamp.nanosec)


def erfasse_nachricht(td: TopicDaten, art: str, msg: Any, t_rx: int) -> None:
    """Uebernimmt Stempel, frame_id, TF-Kanten oder Detektions-JSON einer Nachricht."""
    if art == "header":
        td.stempel.append((t_rx, _stamp_ns(msg.header.stamp)))
        td.frames.add(msg.header.frame_id)
    elif art in ("tf", "tf_static"):
        for tr in msg.transforms:
            kante = f"{tr.header.frame_id}->{tr.child_frame_id}"
            td.kanten.setdefault(kante, []).append((t_rx, _stamp_ns(tr.header.stamp)))
    elif art == "json":
        try:
            td.json.append((t_rx, json.loads(msg.data)))
        except (ValueError, TypeError):
            td.json.append((t_rx, None))


def lese_bag(pfad: Path, stempelart: dict[str, str]) -> BagDaten:
    """Liest alle Nachrichten; deserialisiert nur Topics mit Stempelauswertung."""
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(pfad), storage_id="sqlite3"),
        rosbag2_py.ConverterOptions("cdr", "cdr"),
    )
    meta = reader.get_metadata()
    topics = {
        info.name: TopicDaten(info.name, info.type) for info in reader.get_all_topics_and_types()
    }
    klassen: dict[str, Any] = {}
    while reader.has_next():
        name, data, t_rx = reader.read_next()
        td = topics[name]
        td.zeiten.append(t_rx)
        td.groessen.append(len(data))
        art = stempelart.get(name, "keine")
        if art == "keine":
            continue
        if td.typ not in klassen:
            klassen[td.typ] = get_message(td.typ)
        erfasse_nachricht(td, art, deserialize_message(data, klassen[td.typ]), t_rx)
    return BagDaten(
        pfad=pfad,
        start_ns=meta.starting_time.nanoseconds,
        dauer_ns=meta.duration.nanoseconds,
        nachrichten=meta.message_count,
        groesse_b=speichergroesse(pfad, list(meta.relative_file_paths)),
        speicher=meta.storage_identifier,
        topics=topics,
    )


def speichergroesse(pfad: Path, dateien: list[str]) -> int:
    """Summe der Speicherdateien der Aufnahme.

    bag_size von rosbag2 (Humble) zaehlt den ganzen Ordner, also auch
    bag_check.md und metadata_amr.yaml; der Bericht haenge sonst davon ab.
    """
    summe = 0
    for name in dateien:
        for kandidat in (pfad / name, pfad.parent / name):
            if kandidat.is_file():
                summe += kandidat.stat().st_size
                break
    return summe


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------


@dataclass
class Befunde:
    fehlend: list[str] = field(default_factory=list)
    typ: list[str] = field(default_factory=list)


def pruefe_erwartung(
    daten: BagDaten, cfg: dict[str, Any], szene: str | None
) -> tuple[list[str], Befunde]:
    """Erwartete Topics der Szene und Typen gegen den Katalog."""
    befunde = Befunde()
    hinweise: list[str] = []
    for name, td in daten.topics.items():
        soll_typ = cfg["topics"].get(name, {}).get("typ")
        if soll_typ is not None and soll_typ != td.typ:
            befunde.typ.append(f"{name}: {td.typ}, erwartet {soll_typ}")
    if szene is None or szene not in cfg.get("szenen", {}):
        hinweise.append("Szene unbekannt: erwartete Topics nicht geprueft")
        return hinweise, befunde
    for name in szene_eintrag(cfg, szene).get("erwartet", []):
        gefunden = daten.topics.get(name)
        if gefunden is None:
            befunde.fehlend.append(f"{name} (nicht aufgenommen)")
        elif not gefunden.zeiten:
            befunde.fehlend.append(f"{name} (0 Nachrichten)")
    return hinweise, befunde


def _abschnitt_kopf(daten: BagDaten, szene: str | None, meta: dict[str, Any]) -> list[str]:
    start = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(daten.start_ns / NS_PER_S))
    git = meta.get("git_commit", "n/a")
    if meta.get("git_dirty"):
        git = f"{git} (Arbeitsbaum mit Aenderungen)"
    szene_text = szene or "unbekannt"
    if meta.get("beschreibung"):
        szene_text = f"{szene_text}: {meta['beschreibung']}"
    zeilen: list[list[object]] = [
        ["Aufnahme", f"`{daten.pfad}`"],
        ["Szene", szene_text],
        ["Start (Systemuhr)", start],
        ["Dauer", f"{fmt(daten.dauer_ns / NS_PER_S, 1)} s"],
        ["Nachrichten", daten.nachrichten],
        ["Groesse", f"{fmt(daten.groesse_b / 1e6, 2)} MB"],
        ["Speicher", f"{daten.speicher}, rosbag2 {meta.get('rosbag2_version', 'n/a')}"],
        ["Git-Commit", git],
        ["Launch", f"`{meta.get('launch_zeile', 'n/a')}`"],
    ]
    abw = meta.get("launch_abweichungen") or []
    zeilen.append(["Abweichungen Launch", "; ".join(abw) if abw else "keine"])
    if meta.get("abgebrochen"):
        zeilen.append(["Abbruch", "Aufnahme vorzeitig beendet"])
    return [f"# bag_check: {daten.pfad.name}", "", *_tabelle(["Feld", "Inhalt"], zeilen)]


def katalog_reihenfolge(daten: BagDaten, cfg: dict[str, Any]) -> list[TopicDaten]:
    """Topics der Aufnahme in der Reihenfolge des Katalogs, danach weitere alphabetisch."""
    namen = [n for n in cfg["topics"] if n in daten.topics]
    namen += sorted(n for n in daten.topics if n not in cfg["topics"])
    return [daten.topics[n] for n in namen]


def _frames_text(frames: set[str]) -> str:
    if not frames:
        return "–"
    return ", ".join(f or "(leer)" for f in sorted(frames))


def _abschnitt_topics(daten: BagDaten, cfg: dict[str, Any]) -> list[str]:
    zeilen: list[list[object]] = []
    for td in katalog_reihenfolge(daten, cfg):
        name = td.name
        eintrag = cfg["topics"].get(name, {})
        soll = float(eintrag.get("soll_hz", 0) or 0)
        rate = rate_stats(td.zeiten, soll)
        mittel_b = sum(td.groessen) / len(td.groessen) if td.groessen else math.nan
        frames = _frames_text(td.frames)
        # Latched: Rate und Abstaende haengen nur vom Start der Publisher ab
        latched = eintrag.get("stempel") == "tf_static"
        zeilen.append(
            [
                f"`{name}`",
                td.typ,
                rate.n,
                "–" if latched else fmt(rate.mittel_hz, 2),
                "–" if latched else fmt(rate.min_hz, 2),
                fmt(soll, 1) if soll > 0 else "–",
                rate.luecken if soll > 0 else "–",
                "–" if latched else fmt(rate.max_luecke_ms, 1),
                fmt(mittel_b, 0),
                fmt(sum(td.groessen) / 1e6, 2),
                frames,
            ]
        )
    kopf = [
        "Topic",
        "Typ",
        "Anzahl",
        "Rate Mittel [Hz]",
        "Rate Min [Hz]",
        "Soll [Hz]",
        "Luecken > 2 T",
        "groesster Abstand [ms]",
        "Groesse Mittel [B]",
        "Summe [MB]",
        "frame_id",
    ]
    return ["## 2 Topics", "", *_tabelle(kopf, zeilen)]


def _abschnitt_kanten(daten: BagDaten, cfg: dict[str, Any]) -> list[str]:
    out = ["## 3 TF-Kanten", ""]
    tf = daten.topics.get("/tf")
    kanten_cfg = cfg["topics"].get("/tf", {}).get("kanten", {}) or {}
    zeilen: list[list[object]] = []
    if tf is not None:
        for kante, paare in sorted(tf.kanten.items()):
            soll = float(kanten_cfg.get(kante, {}).get("soll_hz", 0) or 0)
            rate = rate_stats([t for t, _ in paare], soll)
            zeilen.append(
                [
                    f"`{kante}`",
                    rate.n,
                    fmt(rate.mittel_hz, 2),
                    fmt(rate.min_hz, 2),
                    fmt(soll, 1) if soll > 0 else "–",
                    rate.luecken if soll > 0 else "–",
                    fmt(rate.max_luecke_ms, 1),
                ]
            )
    kopf = ["/tf-Kante", "Anzahl", "Rate Mittel [Hz]", "Rate Min [Hz]", "Soll [Hz]"]
    out += _tabelle([*kopf, "Luecken > 2 T", "groesster Abstand [ms]"], zeilen)
    statisch = daten.topics.get("/tf_static")
    if statisch is not None and statisch.kanten:
        out += ["", "Statische Kanten (/tf_static): " + ", ".join(sorted(statisch.kanten))]
    return out


def _abschnitt_stempel(daten: BagDaten, cfg: dict[str, Any]) -> list[str]:
    zeilen: list[list[object]] = []
    for td in katalog_reihenfolge(daten, cfg):
        if not td.stempel:
            continue
        offs, unsynced = stamp_offsets_ms(td.stempel)
        zeitbasis = cfg["topics"].get(td.name, {}).get("zeitbasis", "–")
        zeilen.append(
            [
                f"`{td.name}`",
                zeitbasis,
                len(td.stempel),
                unsynced,
                *_verteilung_zellen(verteilung(offs)),
            ]
        )
    tf = daten.topics.get("/tf")
    kanten_cfg = cfg["topics"].get("/tf", {}).get("kanten", {}) or {}
    if tf is not None:
        for kante, paare in sorted(tf.kanten.items()):
            offs, unsynced = stamp_offsets_ms(paare)
            zeitbasis = kanten_cfg.get(kante, {}).get("zeitbasis", "–")
            zeilen.append(
                [
                    f"`/tf {kante}`",
                    zeitbasis,
                    len(paare),
                    unsynced,
                    *_verteilung_zellen(verteilung(offs)),
                ]
            )
    kopf = ["Topic / Kante", "Zeitbasis", "N", "ungesynct", "Min", "Median", "P95", "Max"]
    return [
        "## 4 Stempelabstand: Aufnahmezeit minus Stempel [ms]",
        "",
        "Positive Werte: Stempel liegt vor dem Empfang beim Recorder. Ungesyncte "
        "Stempel (sec < 1e9) sind nur gezaehlt.",
        "",
        *_tabelle(kopf, zeilen),
    ]


def _abschnitt_detektionen(daten: BagDaten) -> list[str]:
    td = daten.topics.get("/vision/detections")
    out = ["## 5 Detektionen (/vision/detections)", ""]
    if td is None or not td.json:
        return [*out, "Keine Detektionen in der Aufnahme."]
    st = detection_stats(td.json)
    zeilen: list[list[object]] = [
        ["Pakete (davon ungueltiges JSON)", f"{st.pakete} ({st.ungueltig})"],
        ["Pakete mit Objekten", st.mit_objekten],
        ["mit capture_time / mit seq", f"{st.mit_capture} / {st.mit_seq}"],
        ["capture_time <= timestamp", fmt_anteil(st.capture_ok, st.mit_beiden)],
    ]
    for titel, v in (
        ("timestamp - capture_time [ms] (Runner)", st.verarbeitung),
        ("Aufnahmezeit - timestamp [ms] (UDP und ROS)", st.transport),
        ("Aufnahmezeit - capture_time [ms] (gesamt)", st.alter),
    ):
        if v is None:
            zeilen.append([titel, "n/a"])
        else:
            zeilen.append(
                [titel, f"Median {fmt(v.median)}, P95 {fmt(v.p95)}, Max {fmt(v.maximum)}"]
            )
    s = st.seq
    if s.n:
        zeilen.append(
            [
                "seq",
                f"{s.erste} bis {s.letzte}, fehlend {s.fehlend}, Ruecksprunge {s.ruecksprung}",
            ]
        )
    else:
        zeilen.append(["seq", "n/a"])
    hinweis = (
        "timestamp und capture_time sind Host-Uhr des Runners; die Aufnahmezeit ist "
        "Systemuhr desselben Pi. capture_time ist die Entnahme des Bildes im Runner "
        "und eine Obergrenze des Bildzeitpunkts (B-V7), keine Sensorzeit."
    )
    return [*out, *_tabelle(["Kenngroesse", "Wert"], zeilen), "", hinweis]


def _abschnitt_bewertung(daten: BagDaten, cfg: dict[str, Any]) -> list[str]:
    zeilen: list[list[object]] = []
    for eintrag in cfg.get("bewertung", []):
        name = eintrag["topic"]
        td = daten.topics.get(name)
        soll = float(cfg["topics"].get(name, {}).get("soll_hz", 0) or 0)
        mittel = rate_stats(td.zeiten, soll).mittel_hz if td is not None else math.nan
        zeilen.append(
            [
                f"{eintrag['groesse']} (`{name}`)",
                eintrag.get("anforderung", "–"),
                f"{fmt(eintrag.get('k0_hz'), 2)} Hz",
                f"{fmt(mittel, 2)} Hz",
                eintrag.get("toleranz", "–"),
                bewertung_ergebnis(eintrag, mittel),
            ]
        )
    kopf = ["Groesse", "Anforderung", "K0-Baseline", "Messwert", "Regressionstoleranz", "Ergebnis"]
    return [
        "## 6 Bewertung nach L1 v1.1, Abschnitt 10.2",
        "",
        "Anforderung, K0-Baseline, Messwert und Regressionstoleranz sind getrennt "
        "(L1 Abschnitt 10.1). Messwert: mittlere Rate ueber die Aufnahme.",
        "",
        *_tabelle(kopf, zeilen),
    ]


def bewertung_ergebnis(eintrag: dict[str, Any], mittel_hz: float) -> str:
    """Ergebnistext je Zeile der Bewertungstabelle."""
    if math.isnan(mittel_hz):
        return "kein Messwert"
    teile: list[str] = []
    anf_min = eintrag.get("anforderung_min_hz")
    if anf_min is not None:
        teile.append("Anforderung " + ("erfuellt" if mittel_hz >= anf_min else "NICHT erfuellt"))
    grenze = regression_grenze(
        eintrag.get("k0_hz"), eintrag.get("toleranz_min_hz"), eintrag.get("toleranz_max_abfall")
    )
    if grenze is not None:
        status = "eingehalten" if mittel_hz >= grenze else "NICHT eingehalten"
        teile.append(f"Toleranz {status} (Grenze {fmt(grenze, 2)} Hz)")
    return "; ".join(teile) if teile else "kein Kriterium"


def erzeuge_bericht(
    daten: BagDaten, cfg: dict[str, Any], szene: str | None, meta: dict[str, Any]
) -> tuple[str, Befunde]:
    hinweise, befunde = pruefe_erwartung(daten, cfg, szene)
    ergebnis = [
        "## 1 Ergebnis",
        "",
        "- Fehlende erwartete Topics: " + ("; ".join(befunde.fehlend) or "keine"),
        "- Typabweichungen gegen den Katalog: " + ("; ".join(befunde.typ) or "keine"),
    ]
    ergebnis += [f"- {h}" for h in hinweise]
    teile = [
        _abschnitt_kopf(daten, szene, meta),
        ergebnis,
        _abschnitt_topics(daten, cfg),
        _abschnitt_kanten(daten, cfg),
        _abschnitt_stempel(daten, cfg),
        _abschnitt_detektionen(daten),
        _abschnitt_bewertung(daten, cfg),
        [
            "## 7 Hinweise",
            "",
            "- Aufnahmezeit = Empfang beim Recorder (Systemuhr). MCU-Stempel sind "
            "Publizierzeit, nicht Messzeit; das Messalter steckt nicht im Stempelabstand.",
            "- /scan ist am Beginn des Umlaufs gestempelt, map->odom liegt um "
            "transform_timeout in der Zukunft (Phase-0-Bericht, Abschnitt c).",
            "- Median und P95 nach naechstem Rang. Luecke: Abstand > 2 Sollperioden.",
            "- Erzeugt mit amr/scripts/bag_check.py (K7-V).",
        ],
    ]
    text = "\n\n".join("\n".join(t) for t in teile) + "\n"
    return text, befunde


# ---------------------------------------------------------------------------
# Hilfsmodi fuer record_reference_bags.sh
# ---------------------------------------------------------------------------


def pruefe_launch(sz: dict[str, Any], launch_zeile: str) -> tuple[dict[str, str], list[str]]:
    explizit = parse_launch_line(launch_zeile)
    soll = sz.get("launch", {}) or {}
    return compare_launch(soll, explizit, launch_defaults())


def drucke_plan(cfg: dict[str, Any], szene: str, launch_zeile: str) -> int:
    """Zeilen fuer das Aufnahmeskript: SCHLUESSEL Wert."""
    sz = szene_eintrag(cfg, szene)
    print(f"BESCHREIBUNG {sz.get('beschreibung', '')}")
    for name in cfg["topics"]:
        print(f"TOPIC {name}")
    for name in sz.get("erwartet", []):
        print(f"ERWARTET {name}")
    _, abweichungen = pruefe_launch(sz, launch_zeile)
    for text in abweichungen:
        print(f"ABWEICHUNG {text}")
    return 0


def schreibe_metadaten(cfg: dict[str, Any], args: argparse.Namespace) -> int:
    """metadata_amr.yaml ohne Umgebungsvariablen und ohne Schluessel."""
    import yaml

    sz = szene_eintrag(cfg, args.szene)
    wirksam, abweichungen = pruefe_launch(sz, args.launch_zeile or "")
    daten = {
        "format": "amr-referenzaufnahme/1",
        "szene": args.szene,
        "beschreibung": sz.get("beschreibung", ""),
        "aufnahme_start": args.start,
        "dauer_soll_s": args.dauer,
        "abgebrochen": bool(args.abgebrochen),
        "host": args.host,
        "git_commit": args.git_commit,
        "git_dirty": args.git_dirty == "true",
        "git_aenderungen": args.git_aenderung or [],
        "launch_zeile": args.launch_zeile,
        "launch_argumente": parse_launch_line(args.launch_zeile or ""),
        "launch_wirksam": wirksam,
        "launch_abweichungen": abweichungen,
        "topics": list(cfg["topics"]),
        "katalog_version": cfg.get("version"),
        "qos_overrides": "my_bot/config/reference_bags_qos.yaml",
        "image_id": args.image_id,
        "rosbag2_version": rosbag2_version(),
        "storage": "sqlite3",
    }
    kopf = (
        "# K7-V Referenzaufnahme, erzeugt von amr/scripts/record_reference_bags.sh\n"
        "# Enthaelt keine Umgebungsvariablen und keine Schluessel.\n"
    )
    ziel = Path(args.metadaten) / METADATEN_NAME
    ziel.write_text(
        kopf + yaml.safe_dump(daten, sort_keys=False, allow_unicode=False), encoding="utf-8"
    )
    print(f"geschrieben: {ziel}")
    return 0


# ---------------------------------------------------------------------------
# Kommandozeile
# ---------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Prueft eine Referenzaufnahme (rosbag2, sqlite3) und schreibt einen Bericht."
    )
    p.add_argument("bagordner", nargs="?", help="Ordner der Aufnahme (mit metadata.yaml)")
    p.add_argument("-o", "--output", help="Bericht in diese Datei statt nach stdout")
    p.add_argument("--config", help="Pfad zu reference_bags.yaml")
    p.add_argument("--szene", help="Szene (sonst aus metadata_amr.yaml)")
    p.add_argument("--szene-plan", metavar="SZENE", help="Hilfsmodus fuer das Aufnahmeskript")
    p.add_argument("--launch-zeile", help="Befehlszeile von ros2 launch")
    p.add_argument("--metadaten", metavar="BAGORDNER", help="schreibt metadata_amr.yaml")
    p.add_argument("--start", help="Startzeit der Aufnahme (ISO 8601)")
    p.add_argument("--dauer", type=int, help="Solldauer in s")
    p.add_argument("--abgebrochen", action="store_true", help="Aufnahme vorzeitig beendet")
    p.add_argument("--host", help="Rechnername")
    p.add_argument("--git-commit", help="Git-Commit des Repos")
    p.add_argument("--git-dirty", choices=["true", "false"], help="Arbeitsbaum geaendert")
    p.add_argument("--git-aenderung", action="append", help="geaenderter Pfad (mehrfach)")
    p.add_argument("--image-id", help="Image-ID des Containers")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        cfg_pfad = Path(args.config) if args.config else default_config_path()
        cfg = load_yaml(cfg_pfad)
        if args.szene_plan:
            return drucke_plan(cfg, args.szene_plan, args.launch_zeile or "")
        if args.metadaten:
            if not args.szene:
                raise ValueError("--metadaten braucht --szene")
            return schreibe_metadaten(cfg, args)
        if not args.bagordner:
            raise ValueError("Bagordner fehlt")
        bag = Path(args.bagordner)
        meta = lese_metadaten_amr(bag)
        szene = args.szene or meta.get("szene")
        stempelart = {n: e.get("stempel", "keine") for n, e in cfg["topics"].items()}
        daten = lese_bag(bag, stempelart)
        text, befunde = erzeuge_bericht(daten, cfg, szene, meta)
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        meldung = str(exc.args[0]) if isinstance(exc, KeyError) and exc.args else str(exc)
        print(f"FEHLER: {meldung}", file=sys.stderr)
        return 2
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 1 if befunde.fehlend or befunde.typ else 0


if __name__ == "__main__":
    sys.exit(main())
