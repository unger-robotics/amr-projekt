"""Erzeugt den CAN-Signalkatalog fuer die Online-Dokumentation aus der DBC.

Quelle: hardware/can-bus/amr_vehicle.dbc
Ziel:   docs/architecture/can-signalkatalog.md

Die Zieldatei wird nicht handeditiert; Aenderungen erfolgen in der
Signaldatenbank und werden mit scripts/can_generate.sh uebernommen.

Ausbaupaket K2, Phasenplan v2.1.
"""

from __future__ import annotations

import argparse

import can_model

TITEL = "CAN-Signalkatalog"
BESCHREIBUNG = (
    "Aus der Signaldatenbank amr_vehicle.dbc erzeugte Uebersicht aller "
    "CAN-Nachrichten, Signale, Zykluszeiten und Sendeoffsets."
)


def _signaltyp(signal) -> str:
    """Kurzbezeichnung des Datentyps eines Signals."""
    if signal.is_float:
        return f"float{signal.length}"
    vorzeichen = "" if signal.is_signed else "u"
    return f"{vorzeichen}int{signal.length}"


def _zahl(wert) -> str:
    """Zahlenformat ohne unnoetige Nachkommastellen."""
    if wert is None:
        return "-"
    if isinstance(wert, float) and wert == int(wert):
        return str(int(wert))
    return str(wert)


def _zelle(text: str | None) -> str:
    """Text fuer eine Tabellenzelle; Zeilenumbrueche werden entfernt."""
    if not text:
        return "-"
    return " ".join(text.split())


def _kopf(db) -> list[str]:
    zeilen = [
        "---",
        f"title: {TITEL}",
        f"description: {BESCHREIBUNG}",
        "---",
        "",
        f"# {TITEL}",
        "",
        '!!! info "Erzeugte Datei"',
        "    Diese Seite wird aus `hardware/can-bus/amr_vehicle.dbc` erzeugt",
        "    (`./scripts/can_generate.sh`). Aenderungen erfolgen ausschliesslich in der",
        "    Signaldatenbank, nicht in dieser Datei. Der Abgleich wird mit Testfall",
        "    T-09 (`tests/test_can_dbc_check.py`, Schritt 5) geprueft.",
        "",
        "Die Signaldatenbank ist die alleinige Quelle fuer Kennungen, Nutzdatenlaengen,",
        "Bitlagen, Skalierungen und Zykluszeiten (SA-10). Byte-Order ist durchgehend",
        "Intel (Little Endian); float32-Signale entsprechen dem `memcpy` der Firmware.",
        "",
        "| Kennwert | Wert |",
        "| --- | --- |",
        f"| Bitrate | {can_model.BITRATE_BIT_S} bit/s |",
        f"| Nachrichten | {len(db.messages)} |",
        "| Knoten | {} |".format(", ".join(node.name for node in db.nodes)),
        f"| Rechnerische Buslast | {can_model.bus_load_percent(db):.2f} Prozent (ohne Bitstopfen) |",
        "",
    ]
    return zeilen


def _uebersicht(db) -> list[str]:
    zeilen = [
        "## Uebersicht",
        "",
        "| Kennung | Name | Sender | Empfaenger | DLC | Zyklus [ms] | Offset [ms] | Sendeart |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for message in sorted(db.messages, key=lambda m: m.frame_id):
        attribute = {name: wert.value for name, wert in message.dbc.attributes.items()}
        zeilen.append(
            "| 0x{:03X} | {} | {} | {} | {} | {} | {} | {} |".format(
                message.frame_id,
                message.name,
                can_model.sender_of(message) or "-",
                ", ".join(can_model.receivers_of(message)) or "-",
                message.length,
                message.cycle_time if message.cycle_time else "-",
                attribute.get("GenMsgStartDelayTime", "-"),
                message.send_type or "-",
            )
        )
    zeilen.append("")
    return zeilen


def _sendeplan(db) -> list[str]:
    zeilen = [
        "## Sendeplan je Steuergeraet",
        "",
        "Die Offsets gelten innerhalb eines Senders; die Takte der Steuergeraete sind",
        "nicht synchronisiert. Zykluszeiten sind ganzzahlige Vielfache des Sendertakts",
        "(Fahrkern 20 ms, Sensorbasis 10 ms).",
        "",
    ]
    for node in db.nodes:
        nachrichten = [
            m
            for m in sorted(db.messages, key=lambda m: m.frame_id)
            if can_model.sender_of(m) == node.name
        ]
        if not nachrichten:
            continue
        takt = can_model.TICK_MS.get(node.name)
        taktangabe = f" (Takt {takt} ms)" if takt else ""
        zeilen.append(f"### {node.name}{taktangabe}")
        zeilen.append("")
        zeilen.append("| Kennung | Name | Zyklus [ms] | Offset [ms] | Rate [Hz] |")
        zeilen.append("| --- | --- | --- | --- | --- |")
        for message in nachrichten:
            attribute = {name: wert.value for name, wert in message.dbc.attributes.items()}
            rate = can_model.message_rate_hz(message)
            zeilen.append(
                "| 0x{:03X} | {} | {} | {} | {} |".format(
                    message.frame_id,
                    message.name,
                    message.cycle_time if message.cycle_time else "-",
                    attribute.get("GenMsgStartDelayTime", "-"),
                    f"{rate:.1f}" if rate else "-",
                )
            )
        zeilen.append("")
    return zeilen


def _nachrichten(db) -> list[str]:
    zeilen = ["## Nachrichten im Einzelnen", ""]
    for message in sorted(db.messages, key=lambda m: m.frame_id):
        zeilen.append(f"### 0x{message.frame_id:03X} {message.name}")
        zeilen.append("")
        if message.comment:
            zeilen.append(_zelle(message.comment))
            zeilen.append("")
        zeilen.append("| Signal | Startbit | Laenge | Typ | Faktor | Offset | Bereich | Einheit |")
        zeilen.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for signal in sorted(message.signals, key=lambda s: s.start):
            zeilen.append(
                "| {} | {} | {} | {} | {} | {} | {} bis {} | {} |".format(
                    signal.name,
                    signal.start,
                    signal.length,
                    _signaltyp(signal),
                    _zahl(signal.scale),
                    _zahl(signal.offset),
                    _zahl(signal.minimum),
                    _zahl(signal.maximum),
                    signal.unit or "-",
                )
            )
        zeilen.append("")
        for signal in sorted(message.signals, key=lambda s: s.start):
            if signal.choices:
                werte = ", ".join(
                    f"{schluessel} {wert}" for schluessel, wert in sorted(signal.choices.items())
                )
                zeilen.append(f"Wertetabelle `{signal.name}`: {werte}")
                zeilen.append("")
            if signal.comment:
                zeilen.append(f"Hinweis `{signal.name}`: {_zelle(signal.comment)}")
                zeilen.append("")
    return zeilen


def _globaler_kommentar(dbc_pfad: str) -> list[str]:
    """Liest den globalen Kommentarblock (CM_) aus der Signaldatenbank.

    cantools haelt den datenbankweiten Kommentar nicht im Objektmodell vor,
    deshalb wird er hier aus dem Quelltext der DBC gelesen.
    """
    with open(dbc_pfad, encoding="utf-8") as datei:
        inhalt = datei.read()
    beginn = inhalt.find('\nCM_ "')
    if beginn < 0:
        return []
    beginn += len('\nCM_ "')
    ende = inhalt.find('";', beginn)
    if ende < 0:
        return []
    return inhalt[beginn:ende].splitlines()


def _traceability(dbc_pfad: str) -> list[str]:
    zeilen = ["## Herkunft der Festlegungen", ""]
    kommentar = _globaler_kommentar(dbc_pfad)
    if not kommentar:
        return []
    zeilen.append("Wortlaut des datenbankweiten Kommentars in `amr_vehicle.dbc`:")
    zeilen.append("")
    zeilen.append("```text")
    zeilen.extend(kommentar)
    zeilen.append("```")
    zeilen.append("")
    return zeilen


def erzeuge(dbc_pfad: str | None = None) -> str:
    """Erzeugt den Signalkatalog als Markdown-Text."""
    db = can_model.load_database(dbc_pfad)
    zeilen: list[str] = []
    zeilen.extend(_kopf(db))
    zeilen.extend(_uebersicht(db))
    zeilen.extend(_sendeplan(db))
    zeilen.extend(_nachrichten(db))
    zeilen.extend(_traceability(dbc_pfad or can_model.DBC_PATH))
    return "\n".join(zeilen).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dbc", default=can_model.DBC_PATH, help="Pfad der Signaldatenbank")
    parser.add_argument("--output", required=True, help="Pfad der zu schreibenden Markdown-Datei")
    argumente = parser.parse_args()
    with open(argumente.output, "w", encoding="utf-8") as datei:
        datei.write(erzeuge(argumente.dbc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
