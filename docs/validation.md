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

## Sensor-Validierung (Ultraschall + Cliff)

`amr/scripts/sensor_test.py` — ROS2-Node, subscribt `/range/front` und `/cliff`.

```bash
ros2 run my_bot sensor_test
```

8 Tests: US-Konnektivitaet (>= 7 Hz), statische Messung (< 5% Fehler, interaktiv), Bereichstest (min/max/fov), Wiederholgenauigkeit (Std < 15 mm), Cliff-Konnektivitaet (>= 15 Hz), Cliff-Boden (0 Fehlalarme), Cliff-Erkennung (interaktiv), Temperaturkorrektur (optional). Ergebnis: `sensor_results.json`.

**Hinweis:** `/cliff` nutzt Best-Effort QoS. Cliff-Sensor (MH-B) erkennt dunkle/matte Oberflaechen schlecht — weisses Papier als Boden-Ersatz beim Test auf dem Tisch verwenden.

## Regel

Messkriterien vor Bewertung nennen: Messgroesse -> Kriterium -> Schluss -> Konsequenz.
