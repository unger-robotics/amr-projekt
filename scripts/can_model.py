"""Gemeinsame Auswertung der CAN-Signaldatenbank hardware/can-bus/amr_vehicle.dbc.

Wird vom Signalkatalog-Generator (scripts/can_signalkatalog.py) und von
Testfall T-09 (tests/test_can_dbc_check.py) genutzt, damit Buslast und
Sendeplan nur an einer Stelle berechnet werden.

Ausbaupaket K2, Phasenplan v2.1.
"""

from __future__ import annotations

import os
from typing import cast

import cantools

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DBC_PATH = os.path.join(REPO_ROOT, "hardware", "can-bus", "amr_vehicle.dbc")

#: Bitrate des Busses laut config_drive.h und config_sensors.h.
BITRATE_BIT_S = 1_000_000

#: Sendetakt der Steuergeraete. Zykluszeiten sind ganzzahlige Vielfache davon
#: (Tick-Regel aus der Messung S-A vorher, Arbeitsplan 3.2 und 3.4).
TICK_MS: dict[str, int] = {
    "DRIVE_ECU": 20,
    "SENSOR_ECU": 10,
}

#: Fuer ereignisgesteuerte Nachrichten ohne Zykluszeit wird die im Signalbedarf
#: genannte Hoechstrate angesetzt, damit die Buslast nach oben abgeschaetzt ist.
EVENT_RATE_HZ: dict[int, float] = {
    0x150: 10.0,  # P-07 Servosollwert, bei Aenderung, hoechstens 10 Hz
}

#: Kennungen des Ist-Zustands. Layout und Bitlagen sind unveraendert zu halten.
LEGACY_FRAME_IDS: tuple[int, ...] = (
    0x110,
    0x120,
    0x130,
    0x131,
    0x140,
    0x141,
    0x150,
    0x1F0,
    0x200,
    0x201,
    0x210,
    0x220,
    0x2F0,
)

#: In K2 neu spezifizierte Nachrichten (in K2 ohne Wirkung).
NEW_FRAME_IDS: tuple[int, ...] = (0x160, 0x170, 0x230, 0x400, 0x410)

#: Reservierter Bereich fuer die Radar-ECU (Layout in Spike S-B zu bestaetigen).
RADAR_FRAME_IDS: tuple[int, ...] = (0x300,) + tuple(range(0x301, 0x309)) + (0x3F0,)

EXPECTED_FRAME_IDS: tuple[int, ...] = tuple(
    sorted(LEGACY_FRAME_IDS + NEW_FRAME_IDS + RADAR_FRAME_IDS)
)


def load_database(path: str | None = None) -> cantools.database.can.database.Database:
    """Laedt die Signaldatenbank mit strenger Pruefung (T-09 Schritt 1)."""
    # load_file ist als Vereinigung aus CAN- und Diagnose-Datenbank typisiert;
    # eine DBC-Datei liefert immer die CAN-Datenbank.
    return cast(
        "cantools.database.can.database.Database",
        cantools.database.load_file(path or DBC_PATH, strict=True),
    )


def frame_bits(dlc: int) -> int:
    """Bits eines Standardrahmens ohne Bitstopfen: 47 Kopf- und Rahmenbits."""
    return 47 + 8 * dlc


def message_rate_hz(message: cantools.database.can.message.Message) -> float:
    """Senderate einer Nachricht in Hz; 0.0 wenn weder zyklisch noch bekannt."""
    if message.cycle_time:
        return 1000.0 / float(message.cycle_time)
    return EVENT_RATE_HZ.get(message.frame_id, 0.0)


def bus_load_percent(db: cantools.database.can.database.Database) -> float:
    """Rechnerische Buslast in Prozent bei 1 Mbit/s, ohne Bitstopfen."""
    bits_per_second = 0.0
    for message in db.messages:
        bits_per_second += message_rate_hz(message) * frame_bits(message.length)
    return 100.0 * bits_per_second / BITRATE_BIT_S


def sender_of(message: cantools.database.can.message.Message) -> str:
    """Sendender Knoten; leerer Text, wenn die Datenbank keinen nennt."""
    return message.senders[0] if message.senders else ""


def receivers_of(message: cantools.database.can.message.Message) -> list[str]:
    """Empfangende Knoten, aus den Signalen zusammengefasst und sortiert."""
    receivers: list[str] = []
    for signal in message.signals:
        for receiver in signal.receivers:
            if receiver not in receivers:
                receivers.append(receiver)
    return sorted(receivers)
