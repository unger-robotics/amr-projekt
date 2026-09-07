# Auswertung K2 — CAN-Signaldatenbank amr_vehicle.dbc

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Auswertung des Ausbaupakets K2 (Arbeitsplan K0-K2, Abschnitt 3) |
| Datum | 2026-09-03 |
| Bearbeiter | Jan Unger (Umsetzung mit Claude Code auf dem Pi 5) |
| Commit | `7dd12bf` auf `main` |
| Tag | `k2-dbc-v1` (annotiert, G0) |
| Bezug | docs/plan/arbeitsplan-k0-k2-s-a.md v1.2, docs/plan/phasenplan-v2.md v2.2 |
| Status | K2 abgeschlossen, G0 erfuellt; nicht nach GitHub gepusht |

## 1 Was geliefert wurde

| Artefakt | Pfad | Umfang |
| --- | --- | --- |
| Signaldatenbank | `hardware/can-bus/amr_vehicle.dbc` | 388 Zeilen, 28 Nachrichten, 116 Signale, vier Knoten |
| Generierter C-Code | `amr/mcu_firmware/common/can/amr_vehicle.{h,c}` | 11 279 Zeilen, aus der DBC erzeugt |
| Generator | `scripts/can_generate.sh`, `can_signalkatalog.py`, `can_model.py` | Erzeugen und `--check` |
| E2E-Referenz | `amr/scripts/can_e2e.py` | CRC-8 SAE J1850, Alive-Counter |
| T-09 | `tests/test_can_dbc_check.py`, `tests/conftest.py` | 65 Testfaelle, zehn Schritte |
| Signalkatalog | `docs/architecture/can-signalkatalog.md` | 490 Zeilen, erzeugt, in mkdocs eingehaengt |
| CI | `.github/workflows/can-dbc-check.yml` | pytest bei Aenderungen an DBC, Tests, Generatoren |
| Werkzeuge | `requirements-dev.txt` | cantools 43.0.2, pytest 9.1.1 (Host-venv) |

Geaendert: `docs/plan/arbeitsplan-k0-k2-s-a.md` (v1.1 auf v1.2), `hardware/can-bus/CAN-Bus.md`,
`mkdocs.yml`, `mypy.ini`, `.pre-commit-config.yaml`, `validation/P-CAN2/P-CAN2-A.md`.
Neu uebernommen: `docs/plan/phasenplan-v2.md` (v2.2 aus `transfer/`).

## 2 Nachrichtenmodell

| ID | Name | Sender -> Empfaenger | DLC | Zyklus | Offset | Herkunft |
| --- | --- | --- | --- | --- | --- | --- |
| 0x110 | SENSOR_RANGE | SENSOR_ECU -> PI_VCU | 4 | 100 ms | 15 ms | Bestand |
| 0x120 | SENSOR_CLIFF | SENSOR_ECU -> PI_VCU, DRIVE_ECU | 1 | 50 ms | 5 ms | Bestand |
| 0x130 | SENSOR_IMU_ACC | SENSOR_ECU -> PI_VCU | 8 | 20 ms | 0 ms | Bestand |
| 0x131 | SENSOR_IMU_HEADING | SENSOR_ECU -> PI_VCU | 4 | 20 ms | 10 ms | Bestand |
| 0x140 | SENSOR_BATTERY | SENSOR_ECU -> PI_VCU | 6 | 500 ms | 25 ms | Bestand |
| 0x141 | SENSOR_BATTERY_SHUTDOWN | SENSOR_ECU -> PI_VCU, DRIVE_ECU | 1 | 1000 ms + Event | 45 ms | Bestand, S-02 neu zyklisch |
| 0x150 | VCU_SERVO_COMMAND_LEGACY | PI_VCU -> SENSOR_ECU | 4 | Event, max. 10 Hz | — | Bestand |
| **0x160** | **VCU_EMERGENCY_STOP** | PI_VCU -> DRIVE_ECU, SENSOR_ECU | 4 | 100 ms | 0 ms | neu, P-05 |
| **0x170** | **VCU_HEARTBEAT** | PI_VCU -> DRIVE_ECU, SENSOR_ECU | 8 | 100 ms | 5 ms | neu, P-06 |
| 0x1F0 | SENSOR_HEARTBEAT | SENSOR_ECU -> PI_VCU | 8 | 1000 ms | 35 ms | Bestand |
| 0x200 | DRIVE_ODOM_XY | DRIVE_ECU -> PI_VCU | 8 | **40 ms** | 0 ms | Bestand |
| 0x201 | DRIVE_ODOM_HEADING_SPEED | DRIVE_ECU -> PI_VCU | 8 | **40 ms** | 0 ms | Bestand |
| 0x210 | DRIVE_WHEEL_SPEED | DRIVE_ECU -> PI_VCU | 8 | **80 ms** | 20 ms | Bestand |
| 0x220 | DRIVE_MOTOR_PWM | DRIVE_ECU -> PI_VCU | 4 | **80 ms** | 60 ms | Bestand |
| **0x230** | **DRIVE_PATH_STATUS** | DRIVE_ECU -> PI_VCU | 8 | 200 ms | 40 ms | neu, D-05 |
| 0x2F0 | DRIVE_HEARTBEAT | DRIVE_ECU -> PI_VCU | 2 | 1000 ms | 60 ms | Bestand |
| 0x300 | RADAR_LIST_HEADER | RADAR_ECU -> PI_VCU | 4 | 100 ms | 0 ms | Platzhalter S-B |
| 0x301-0x308 | RADAR_OBJECT_1..8 | RADAR_ECU -> PI_VCU | 8 | 100 ms | 0 ms | Platzhalter S-B |
| 0x3F0 | RADAR_HEARTBEAT | RADAR_ECU -> PI_VCU | 8 | 1000 ms | 50 ms | Platzhalter S-B |
| **0x400** | **VCU_DRIVE_COMMAND** | PI_VCU -> DRIVE_ECU | 8 | 20 ms | 0 ms | neu, P-01 bis P-04 |
| **0x410** | **VCU_SENSOR_COMMAND** | PI_VCU -> SENSOR_ECU | 8 | 100 ms | 5 ms | neu, P-07 |

## 3 Nachweise

### 3.1 Bestandslayouts unveraendert

Jede der dreizehn Bestandsnachrichten wurde byteweise geprueft: Kodierung ueber die DBC
gegen die Bytefolge, die die Firmware per `memcpy` erzeugt. Alle dreizehn identisch.

```
0x110 b6f39d3f          0x140 5c2b24fa0a41      0x201 0000003f9a99193e
0x120 01                0x141 01                0x210 00004040000040c0
0x130 d5030cfe28239600  0x150 84033efe          0x220 c80001ff
0x131 b30cc93f          0x1F0 172a07000300d204  0x2F0 1763
                        0x200 0000c03f000010c0
```

Kennungen und Nutzdatenlaengen stimmen mit `config_drive.h:143-155` und
`config_sensors.h:147-157` sowie den `data_length_code`-Zuweisungen in beiden
`twai_can.hpp` ueberein. Firmware, `can_bridge_node.py`, Launch-Dateien, Dockerfile
und Verdrahtung sind unveraendert. Kein Flash, kein CAN-TX, keine Fahrbewegung.

### 3.2 T-09 can_dbc_check

`.venv/bin/python -m pytest tests/ -q` -> **65 passed**

| Schritt | Pruefung | Ergebnis |
| --- | --- | --- |
| 1 | `load_file(strict=True)` | bestanden |
| 2 | Kennungsmenge 28 (13 + 5 + 10), DLC des Bestands | bestanden |
| 3 | Roundtrip min/max/Zufall je Nachricht | float32 exakt, Ganzzahlen <= 1 Quantisierungsschritt |
| 4 | Attribute vollstaendig, 0x150 event, 0x141 cyclicAndEvent | bestanden |
| 5 | Codegenerierung diff-frei | bestanden |
| 6 | Buslast | **3,94 %** bei 1 Mbit/s (Grenze 30 %) |
| 7 | CRC-8 gegen Katalogpruefwert und zwei Rahmenvektoren | bestanden |
| 8 | PI_VCU-IDs > 0x141, Sicherheit vor Diagnose | bestanden |
| 9 | Tick-Regel, 0x200/0x201 = 40 ms | bestanden |
| 10 | Abdeckung P-01..S-07 (SA-10) | vollstaendig |

Weitere gruene Pruefpfade: `pre-commit run --all-files`, `mkdocs build --strict`,
`ruff check`, `ruff format --check`, `./scripts/can_generate.sh --check`.

## 4 Entscheidungen und Abweichungen

| Punkt | Entwurf im Arbeitsplan | Umsetzung | Begruendung |
| --- | --- | --- | --- |
| Umfang | zwei Kommandoframes | zusaetzlich 0x160, 0x170, 0x230, 0x141 zyklisch | K1 hat Vorrang; SA-10 fordert Abdeckung jeder Zeile des Signalbedarfs |
| Kennung Notstopp / Lebenszeichen | Bereich 0x400-0x4F0 | 0x160 und 0x170 | signalbedarf.md 7.4: Sicherheit vor Diagnose; 0x120 und 0x141 gewinnen weiterhin |
| Betriebsmodus-Enum | OFF/SERVICE/MANUAL/AUTONOMOUS/DEGRADED | SERIAL_REFERENCE 0, CAN_SHADOW 1, CAN_PRIMARY 2, SERVICE 3, FAILSAFE 4 | Anforderungsliste L1, Abschnitt 13.1 |
| t_timeout (D-05 Phasenplan) | 60 ms oder 500 ms | **300 ms** im Modus CAN_PRIMARY | Anforderungsliste L1, Abschnitt 13.3; SIA-17 mit 500 ms bleibt uebergeordnet |
| Zykluszeit 0x200/0x201 | 50 ms | 40 ms (2 Ticks) | Tick-Regel aus S-A vorher; 50 ms sind 2,5 Ticks und erzeugen den 40/60-ms-Wechsel |
| Zykluszeit 0x210/0x220 | 100 ms | 80 ms (4 Ticks), versetzte Offsets | entschaerft den 4-Frame-Burst des Fahrkerns unabhaengig vom Controller |
| T-09 | acht Schritte | zehn Schritte | Tick-Regel und K1-Abdeckung ergaenzt |
| Motor-Limit | offen (D-07) | `motor_limit_percent` in 0x400, 7 Bit, 0-100 % | K1 P-04 |
| 0x150 gegen 0x410 | in K2 zu entscheiden | 0x410 ergaenzt, ersetzt nicht; Umstellung in K5 | signalbedarf.md 7.3: aeltere Firmware muss betriebsfaehig bleiben |
| LED-PWM | offen (D-07) | **weiterhin offen**, keine Kennung vergeben | in K1 nicht als Signalbedarf gelistet |

Die Traceability-Liste "aus K1 uebernommen / aus der Firmware uebernommen / in K2
vorgeschlagen" steht als datenbankweiter `CM_`-Block in der DBC und wird in den
Signalkatalog uebernommen.

## 5 Bereinigte Doku-Abweichungen (signalbedarf.md 7.6)

In `hardware/can-bus/CAN-Bus.md` korrigiert:

1. Servosollwert 0x150 war nicht dokumentiert — jetzt als Empfangsrahmen der
   Sensorbasis mit Layout und Ratenangabe aufgefuehrt.
2. Die vom Fahrkern empfangenen Sicherheitssignale 0x120 und 0x141 waren nicht
   gekennzeichnet — jetzt eigene Tabelle mit der Wirkung im Fahrkern.
3. Nutzdatenlaenge des Sensor-Lebenszeichens 0x1F0 stand mit 2 Byte statt 8 Byte.

Zusaetzlich verweist die Seite jetzt auf die DBC als alleinige Quelle.

## 6 Offene Punkte

| Nr. | Punkt | Zustaendig |
| --- | --- | --- |
| 1 | Push nach GitHub steht aus (`./scripts/sync/push-to-github.sh`), Tag mit `--tags` mitschicken | Jan |
| 2 | D-07 (LED-PWM) weiterhin offen: reservierte Bits in 0x400 oder eigener Frame 0x420 | K2-Nachtrag oder K5 |
| 3 | D-06 (ID-Abgleich Phasenplan gegen L1): NFA-13 und NFA-14 sind zwischen Anforderungsliste und Phasenplan vertauscht — die Buslastgrenze heisst in L1 NFA-13, im Phasenplan NFA-14 | K3 |
| 4 | S-06: Batterieleistung saettigt bei 65,535 W; Erweiterung erfordert Layoutaenderung, in der DBC nur als Kommentar vermerkt | K3 |
| 5 | 0x2F0 Bit0/Bit1/Bit4 fuehren in der Firmware feste Werte statt echter Zustaende | K3 |
| 6 | V4 (Widerstand CAN_H-CAN_L) und Bit-Timing-Zeile im Messprotokoll P-CAN2-A nachtragen | Jan |
| 7 | `mypy` meldet auf dem Host zwei Typfehler in `amr/scripts/can_validation_test.py:179,198` (nur mit installiertem python-can sichtbar; pre-commit-mypy ist gruen). Datei unveraendert, nicht Teil von K2 | offen |
| 8 | cantools im Docker-Image aufnehmen, sobald `can_bridge_node` die DBC nutzt | K3 |

## 7 Naechste Schritte (K3)

1. Controllertausch MCP2515 auf MCP2518FD am Pi 5 (D-01 bestaetigt durch S-A vorher).
2. P-CAN2 Teil B (nachher) mit denselben Skripten und Lastprofilen A1/A2.
3. Sensorbasis auf die generierten Pack-Funktionen und die Sendeoffsets umstellen,
   0x141 zyklisch wiederholen (S-02).
4. Arbiter fuer `/cmd_vel` (BA-03), Bodenkontakt (BA-04), Diagnoseleiter (BA-05).

## 8 Reproduktion auf dem Pi 5

```bash
cd ~/amr-projekt
python3 -m venv .venv                              # falls noch nicht vorhanden
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v               # T-09, 65 Faelle
./scripts/can_generate.sh --check                  # Generat gegen eingecheckten Stand
.venv/bin/python -m cantools dump hardware/can-bus/amr_vehicle.dbc
mkdocs build --strict
```
