# Messprotokoll Phase 3: Lokalisierung und Kartierung

Datum: 10.03.2026
Pruefer: Jan
Testareal: Innenraum, ca. 15 m^2, ebener Hartboden (Laminat)
Akkuspannung: 10.84 V (kontinuierlich ueberwacht via INA260, SOC 22 %)
Firmware: Drive-Node v4.0.0, Sensor-Node v3.0.0
Software: ROS2 Humble (Docker), SLAM Toolbox (async)

---

## Phase 3: Lokalisierung und Kartierung (F03)

### Testfall 3.1: Loop-Closure-Kartenqualitaet

| Parameter | Wert |
|---|---|
| Skript | `slam_validation --live --duration 120` |
| Raum | ca. 15 m^2 |
| Steuerung | Manuell per Dashboard-Joystick |
| Kartenqualitaet (visuell) | Keine doppelten Waende, sauberer Loop Closure |
| TF-Rate map->odom | 7.7 Hz |
| Akzeptanz map->odom | >= 1.5 Hz |
| TF-Rate odom->base_link | 18.5 Hz |
| Akzeptanz odom->base_link | >= 15 Hz |
| Topic-Rate /odom | 18.6 Hz |
| Akzeptanz /odom | >= 15 Hz |
| Topic-Rate /scan | 7.7 Hz |
| Akzeptanz /scan | >= 5 Hz |
| Topic-Rate /imu | 30.1 Hz |
| Akzeptanz /imu | >= 25 Hz |
| ATE (RMSE) | 0.1898 m |
| Max. Fehler | 0.3583 m |
| Mittlerer Fehler | 0.1608 m |
| Odom-Posen | 2230 |
| SLAM-Posen | 598 |
| Dauer | 119.4 s |
| Akzeptanz ATE | < 0.20 m |
| **Ergebnis TF-Raten** | **PASS** |
| **Ergebnis Topic-Raten** | **PASS** |
| **Ergebnis ATE** | **PASS** (0.19 < 0.20 m) |
| **Ergebnis Karte** | **PASS** |

### Testfall 3.2: ATE (Absolute Trajectory Error)

| Parameter | Wert |
|---|---|
| Skript | `slam_validation --live --duration 120` |
| Modus | Manuelle Steuerung per Dashboard-Joystick (Nav2 aktiv) |
| TF-Rate map->odom | 7.7 Hz |
| TF-Rate odom->base_link | 18.8 Hz |
| Topic-Rate /odom | 18.8 Hz |
| Topic-Rate /scan | 7.8 Hz |
| Topic-Rate /imu | 29.0 Hz |
| Odom-Posen | 2258 |
| SLAM-Posen | 596 |
| ATE (RMSE) | 0.0296 m |
| Dauer | 120.1 s |
| Akzeptanz | < 0.20 m |
| **Ergebnis** | **PASS** (0.030 < 0.20 m) |

### Bewertung Phase 3

F03 (Lokalisierung und Kartierung mit SLAM): **erfuellt**

Anmerkung: TF- und Topic-Raten uebertreffen alle Akzeptanzkriterien deutlich.
Die ATE liegt mit 0.030-0.19 m innerhalb des Akzeptanzkriteriums.
Kartenqualitaet visuell geprueft: Keine verdoppelten Waende, saubere
Wandkonturen nach Loop Closure.

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | erfuellt | 2/2 PASS |

JSON-Ergebnisdateien:
- `slam_results.json`
