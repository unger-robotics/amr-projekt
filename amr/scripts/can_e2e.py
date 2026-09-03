"""E2E-Absicherung der CAN-Kommandoframes: CRC-8 und Alive-Counter.

Referenzimplementierung zur Signaldatenbank hardware/can-bus/amr_vehicle.dbc.
Reines Python-Modul ohne ROS-2-Abhaengigkeit, deshalb kein Eintrag in setup.py.
Wird von Testfall T-09 genutzt und steht ab Ausbaupaket K4 der CAN-Bruecke und
der Firmware-Portierung als Vergleichsmassstab zur Verfuegung.

Verfahren: CRC-8 nach SAE J1850 (Polynom 0x1D, Startwert 0xFF, Endverknuepfung
0xFF, keine Bitspiegelung). Gerechnet wird ueber die Nutzdatenbytes ohne das
Pruefsummenbyte, gefolgt von einer nachrichtenspezifischen Data-ID. Die Data-ID
verhindert, dass ein auf dem Bus wiederholter Rahmen einer anderen Kennung als
gueltig angenommen wird (Vertauschungsschutz).

Ausbaupaket K2, Phasenplan v2.1.
"""

from __future__ import annotations

from collections.abc import Iterable

CRC8_POLYNOMIAL = 0x1D
CRC8_INITIAL = 0xFF
CRC8_FINAL_XOR = 0xFF

#: Data-ID je abgesicherter Nachricht: unteres Byte der CAN-Kennung.
DATA_ID: dict[int, int] = {
    0x160: 0x60,  # VCU_EMERGENCY_STOP
    0x170: 0x70,  # VCU_HEARTBEAT
    0x230: 0x30,  # DRIVE_PATH_STATUS
    0x400: 0x00,  # VCU_DRIVE_COMMAND
    0x410: 0x10,  # VCU_SENSOR_COMMAND
}

#: Bytelage der Pruefsumme je abgesicherter Nachricht (letztes Nutzdatenbyte).
CRC_BYTE_INDEX: dict[int, int] = {
    0x160: 3,
    0x170: 7,
    0x230: 7,
    0x400: 7,
    0x410: 7,
}

ALIVE_COUNTER_MODULUS = 16


def crc8(data: Iterable[int]) -> int:
    """CRC-8 nach SAE J1850 ueber eine Bytefolge."""
    crc = CRC8_INITIAL
    for byte in data:
        crc ^= byte & 0xFF
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ CRC8_POLYNOMIAL) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc ^ CRC8_FINAL_XOR


def frame_crc8(frame_id: int, payload: bytes) -> int:
    """Pruefsumme eines Kommandorahmens: Nutzdaten ohne CRC-Byte plus Data-ID."""
    if frame_id not in DATA_ID:
        raise KeyError(f"Kennung 0x{frame_id:03X} ist nicht E2E-abgesichert")
    crc_index = CRC_BYTE_INDEX[frame_id]
    if len(payload) <= crc_index:
        raise ValueError(f"Nutzdaten zu kurz: {len(payload)} Byte, erwartet mehr als {crc_index}")
    protected = bytes(payload[:crc_index]) + bytes([DATA_ID[frame_id]])
    return crc8(protected)


def apply_crc8(frame_id: int, payload: bytes) -> bytes:
    """Setzt die Pruefsumme im Rahmen und gibt die vollstaendigen Nutzdaten zurueck."""
    result = bytearray(payload)
    result[CRC_BYTE_INDEX[frame_id]] = frame_crc8(frame_id, bytes(payload))
    return bytes(result)


def check_crc8(frame_id: int, payload: bytes) -> bool:
    """Prueft die Pruefsumme eines empfangenen Rahmens."""
    return payload[CRC_BYTE_INDEX[frame_id]] == frame_crc8(frame_id, payload)


def next_alive_counter(previous: int) -> int:
    """Naechster Wert des rollierenden Zaehlers mit 4 Bit."""
    return (previous + 1) % ALIVE_COUNTER_MODULUS


def alive_counter_gap(previous: int, current: int) -> int:
    """Zahl der ausgelassenen Zaehlerschritte; 0 bei luekenloser Folge."""
    return (current - previous - 1) % ALIVE_COUNTER_MODULUS
