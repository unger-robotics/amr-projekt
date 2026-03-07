# Validierung

## Zweck

Beschreibung von Testablaeufen, Validierungsskripten und Nachweisen.

## Inhalte

- Standalone-Skripte
- ROS2-Testknoten
- Hardware-in-the-loop-Pruefungen
- Messgroessen, Kriterien und Ergebnisablage

## CAN-Bus Validierung

`amr/scripts/can_validation_test.py` — Standalone (kein ROS2 noetig), nutzt `python-can` auf SocketCAN.

```bash
python3 amr/scripts/can_validation_test.py --duration 30
```

Prueft 12 CAN-IDs (5 Drive, 7 Sensor), Frame-Raten, Heartbeat-Dekodierung, Daten-Plausibilitaet. Ergebnis: `can_results.json`.

## Regel

Messkriterien vor Bewertung nennen: Messgroesse -> Kriterium -> Schluss -> Konsequenz.
