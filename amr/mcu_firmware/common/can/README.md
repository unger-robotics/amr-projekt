# Generierter CAN-Code

Die Dateien `amr_vehicle.h` und `amr_vehicle.c` in diesem Verzeichnis werden aus
der Signaldatenbank erzeugt und **nicht handeditiert**.

- Quelle: `hardware/can-bus/amr_vehicle.dbc`
- Generator: `./scripts/can_generate.sh` (ruft `cantools generate_c_source` auf)
- Pruefung: `tests/test_can_dbc_check.py`, Schritt 5 (T-09) vergleicht das
  eingecheckte Generat mit einem frisch erzeugten Stand

Der Zeitstempel in der Kopfzeile des Generats wird vom Generatorskript entfernt,
damit der Vergleich reproduzierbar ist.

## Verwendung in der Firmware

Die beiden PlatformIO-Projekte `drive_node` und `sensor_node` nutzen diesen Code
noch **nicht**. Ausbaupaket K2 liefert ausschliesslich die Spezifikation und den
generierten Code; die Umstellung der Firmware auf die generierten Pack- und
Unpack-Funktionen erfolgt fuer die Sensorbasis in K3 und fuer den Fahrkern in K4.
Bis dahin bleiben `drive_node/include/twai_can.hpp` und
`sensor_node/include/twai_can.hpp` unveraendert in Betrieb.

Die generierten Funktionen bilden float32-Signale auf `float`-Strukturfelder ab
und packen sie per `memcpy` in Little-Endian-Bytes. Das entspricht dem heutigen
Verhalten beider Knoten.
