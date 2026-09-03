"""T-09 can_dbc_check: Pruefung der CAN-Signaldatenbank.

Testtyp R1 (Pruefstandtest ohne Hardware). Weist SA-10 nach: die Datenbank
hardware/can-bus/amr_vehicle.dbc ist die alleinige Quelle fuer Kennungen,
Nutzdatenlaengen, Bitlagen, Skalierungen und Zykluszeiten.

Testplan: docs/plan/arbeitsplan-k0-k2-s-a.md, Abschnitt 3.6 (Schritte 1 bis 10).
Ausbaupaket K2, Phasenplan v2.1.

Aufruf: .venv/bin/python -m pytest tests/ -v
"""

from __future__ import annotations

import os
import random
import struct
import subprocess

import can_e2e
import can_model
import pytest

REPO_ROOT = can_model.REPO_ROOT

#: Erwarteter Sendertakt je Steuergeraet (Schritt 9).
TICK_MS = can_model.TICK_MS

#: Zuordnung Signalbedarf (docs/architecture/signalbedarf.md) zu Nachricht und
#: Signal (Schritt 10). Jede Zeile des Signalbedarfs muss abgedeckt sein.
SIGNALBEDARF = {
    "P-01": (0x400, "target_velocity"),
    "P-02": (0x400, "target_yaw_rate"),
    "P-03": (0x400, "operating_mode"),
    "P-04": (0x400, "motor_limit_percent"),
    "P-05": (0x160, "estop_request"),
    "P-06": (0x170, "vcu_hb_counter"),
    "P-07": (0x410, "servo_pan"),
    "P-07-legacy": (0x150, "servo_pan_legacy"),
    "D-01": (0x200, "odom_x"),
    "D-02": (0x201, "odom_theta"),
    "D-03": (0x210, "wheel_speed_left"),
    "D-04": (0x220, "motor_pwm_left"),
    "D-05": (0x230, "path_active_source"),
    "D-06": (0x2F0, "drive_failsafe_active"),
    "S-01": (0x120, "cliff_detected"),
    "S-02": (0x141, "battery_shutdown"),
    "S-03": (0x110, "range_front"),
    "S-04": (0x130, "accel_x"),
    "S-05": (0x131, "heading"),
    "S-06": (0x140, "battery_power"),
    "S-07": (0x1F0, "sensor_imu_ok"),
}

#: Bekannte Pruefsummenvektoren (Schritt 7). Der erste Wert ist der
#: Pruefwert des Verfahrens CRC-8/SAE-J1850 aus dem CRC-Katalog und dient als
#: unabhaengiger Anker; die beiden anderen sind Rahmen dieser Datenbank.
CRC8_VEKTOREN = (
    (b"123456789", 0x4B),
    (bytes([0x00] * 7) + bytes([can_e2e.DATA_ID[0x400]]), 0xE9),
    (bytes([0x01, 0x2A, 0x07]) + bytes([can_e2e.DATA_ID[0x160]]), 0x96),
)


def _float32(value):
    """Rundet einen Wert auf die Genauigkeit von IEEE-754 mit einfacher Breite."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _sample(message, mode, rng):
    """Erzeugt einen Signalsatz an der Unter-, Obergrenze oder zufaellig."""
    values = {}
    for signal in message.signals:
        low = signal.minimum
        high = signal.maximum
        if signal.is_float:
            if mode == "min":
                value = low
            elif mode == "max":
                value = high
            else:
                value = rng.uniform(low, high)
        else:
            raw_low = round((low - signal.offset) / signal.scale)
            raw_high = round((high - signal.offset) / signal.scale)
            if mode == "min":
                raw = raw_low
            elif mode == "max":
                raw = raw_high
            else:
                raw = rng.randint(raw_low, raw_high)
            value = raw * signal.scale + signal.offset
        values[signal.name] = value
    return values


# --- Schritt 1: Laden ------------------------------------------------------


def test_schritt_1_laedt_streng(dbc_path):
    database = can_model.load_database(dbc_path)
    assert database.messages, "Signaldatenbank enthaelt keine Nachrichten"
    assert [node.name for node in database.nodes] == [
        "PI_VCU",
        "DRIVE_ECU",
        "SENSOR_ECU",
        "RADAR_ECU",
    ]


# --- Schritt 2: Kennungen --------------------------------------------------


def test_schritt_2_kennungen_vollstaendig(db):
    vorhanden = tuple(sorted(message.frame_id for message in db.messages))
    assert vorhanden == can_model.EXPECTED_FRAME_IDS
    assert len(vorhanden) == 28, "13 Bestand, 5 neu, 10 Radar-Platzhalter"


def test_schritt_2_bestandskennungen_unveraendert(db):
    """Nutzdatenlaengen des Ist-Zustands nach Arbeitsplan Anhang A.3."""
    erwartete_dlc = {
        0x110: 4,
        0x120: 1,
        0x130: 8,
        0x131: 4,
        0x140: 6,
        0x141: 1,
        0x150: 4,
        0x1F0: 8,
        0x200: 8,
        0x201: 8,
        0x210: 8,
        0x220: 4,
        0x2F0: 2,
    }
    for frame_id, dlc in erwartete_dlc.items():
        assert db.get_message_by_frame_id(frame_id).length == dlc, hex(frame_id)


# --- Schritt 3: Roundtrip --------------------------------------------------


@pytest.mark.parametrize("frame_id", can_model.EXPECTED_FRAME_IDS)
def test_schritt_3_roundtrip(db, frame_id):
    message = db.get_message_by_frame_id(frame_id)
    rng = random.Random(frame_id)
    for mode in ("min", "max", "random"):
        values = _sample(message, mode, rng)
        data = message.encode(values, strict=True)
        assert len(data) == message.length
        zurueck = message.decode(data, decode_choices=False)
        for signal in message.signals:
            erwartet = values[signal.name]
            gemessen = zurueck[signal.name]
            if signal.is_float:
                assert gemessen == _float32(erwartet), f"{message.name}.{signal.name}"
            else:
                abweichung = abs(gemessen - erwartet)
                assert abweichung <= abs(signal.scale) + 1e-9, f"{message.name}.{signal.name}"


# --- Schritt 4: Attribute --------------------------------------------------


def test_schritt_4_attribute_vollstaendig(db):
    for message in db.messages:
        attribute = {name: wert.value for name, wert in message.dbc.attributes.items()}
        assert "GenMsgSendType" in attribute, message.name
        assert "GenMsgStartDelayTime" in attribute, message.name
        assert "GenMsgCycleTime" in attribute, message.name
        if message.send_type in ("cyclic", "cyclicAndEvent"):
            assert message.cycle_time and message.cycle_time > 0, message.name


def test_schritt_4_sendearten(db):
    assert db.get_message_by_frame_id(0x150).send_type == "event"
    assert db.get_message_by_frame_id(0x141).send_type == "cyclicAndEvent"
    assert db.get_message_by_frame_id(0x141).cycle_time == 1000
    zyklisch = [
        m.name
        for m in db.messages
        if m.frame_id not in (0x150,) and m.send_type not in ("cyclic", "cyclicAndEvent")
    ]
    assert zyklisch == [], f"unerwartet nicht zyklische Nachrichten: {zyklisch}"


# --- Schritt 5: Codegenerierung -------------------------------------------


def test_schritt_5_generat_aktuell():
    skript = os.path.join(REPO_ROOT, "scripts", "can_generate.sh")
    ergebnis = subprocess.run(
        [skript, "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ergebnis.returncode == 0, ergebnis.stdout + ergebnis.stderr


# --- Schritt 6: Buslast ----------------------------------------------------


def test_schritt_6_buslast(db):
    last = can_model.bus_load_percent(db)
    print(f"\nRechnerische Buslast: {last:.2f} Prozent bei {can_model.BITRATE_BIT_S} bit/s")
    assert last < 30.0, "NFA-14: Buslast hoechstens 30 Prozent"


# --- Schritt 7: Pruefsumme -------------------------------------------------


def test_schritt_7_crc8_referenzvektoren():
    for daten, erwartet in CRC8_VEKTOREN:
        assert can_e2e.crc8(daten) == erwartet, daten.hex()


def test_schritt_7_crc8_am_rahmen(db):
    message = db.get_message_by_frame_id(0x400)
    daten = message.encode(
        {
            "target_velocity": 0.15,
            "target_yaw_rate": -1.0,
            "drive_cmd_enable": 1,
            "operating_mode": 2,
            "motor_limit_percent": 100,
            "drive_cmd_alive_counter": 7,
            "drive_cmd_crc8": 0,
        },
        strict=True,
    )
    abgesichert = can_e2e.apply_crc8(0x400, daten)
    assert can_e2e.check_crc8(0x400, abgesichert)
    verfaelscht = bytearray(abgesichert)
    verfaelscht[0] ^= 0x01
    assert not can_e2e.check_crc8(0x400, bytes(verfaelscht))
    zurueck = message.decode(abgesichert, decode_choices=False)
    assert abs(zurueck["target_velocity"] - 0.15) <= 0.001
    assert zurueck["drive_cmd_alive_counter"] == 7


def test_schritt_7_alive_counter():
    assert can_e2e.next_alive_counter(15) == 0
    assert can_e2e.alive_counter_gap(15, 0) == 0
    assert can_e2e.alive_counter_gap(3, 6) == 2


# --- Schritt 8: Kennungsregel ---------------------------------------------


def test_schritt_8_kommandokennungen_ueber_0x141(db):
    for message in db.messages:
        if can_model.sender_of(message) == "PI_VCU":
            assert message.frame_id > 0x141, message.name


def test_schritt_8_sicherheit_vor_diagnose(db):
    """signalbedarf.md 7.4: Sicherheitssignale gewinnen gegen Diagnosesignale."""
    notstopp = db.get_message_by_frame_id(0x160).frame_id
    lebenszeichen = db.get_message_by_frame_id(0x170).frame_id
    assert db.get_message_by_frame_id(0x120).frame_id < notstopp
    assert db.get_message_by_frame_id(0x141).frame_id < notstopp
    assert notstopp < lebenszeichen
    for diagnose in (0x1F0, 0x200, 0x210, 0x220, 0x230, 0x2F0):
        assert lebenszeichen < diagnose, hex(diagnose)


# --- Schritt 9: Tick-Regel -------------------------------------------------


def test_schritt_9_tickregel(db):
    for message in db.messages:
        sender = can_model.sender_of(message)
        tick = TICK_MS.get(sender)
        if tick is None or not message.cycle_time:
            continue
        assert message.cycle_time % tick == 0, (
            f"{message.name}: {message.cycle_time} ms ist kein Vielfaches von {tick} ms"
        )


def test_schritt_9_odometrie_40ms(db):
    assert db.get_message_by_frame_id(0x200).cycle_time == 40
    assert db.get_message_by_frame_id(0x201).cycle_time == 40


# --- Schritt 10: Abdeckung des Signalbedarfs ------------------------------


@pytest.mark.parametrize("bedarf", sorted(SIGNALBEDARF))
def test_schritt_10_signalbedarf_abgedeckt(db, bedarf):
    frame_id, signalname = SIGNALBEDARF[bedarf]
    message = db.get_message_by_frame_id(frame_id)
    assert signalname in [signal.name for signal in message.signals], bedarf


def test_schritt_10_keine_unbegruendete_nachricht(db):
    zugeordnet = {frame_id for frame_id, _ in SIGNALBEDARF.values()}
    offen = [
        hex(message.frame_id)
        for message in db.messages
        if message.frame_id not in zugeordnet and message.frame_id not in can_model.RADAR_FRAME_IDS
    ]
    assert offen == [], f"Nachrichten ohne Zeile im Signalbedarf: {offen}"


def test_schritt_10_radar_reserviert(db):
    for frame_id in can_model.RADAR_FRAME_IDS:
        message = db.get_message_by_frame_id(frame_id)
        assert can_model.sender_of(message) == "RADAR_ECU", hex(frame_id)
        assert 0x300 <= frame_id <= 0x3F0
