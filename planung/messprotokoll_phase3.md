# Messprotokoll Phase 3: Lokalisierung und Kartierung

Datum: 10.03.2026
Pruefer: Jan
Testareal: Innenraum, ca. 15 m^2, ebener Hartboden (Laminat)
Akkuspannung: > 10 V (kontinuierlich ueberwacht via INA260)
Firmware: Drive-Node v4.0.0, Sensor-Node v3.0.0
Software: ROS2 Humble (Docker), SLAM Toolbox (async)

---

## Phase 3: Lokalisierung und Kartierung (F03)

### Testfall 3.1: Loop-Closure-Kartenqualitaet

| Parameter | Wert |
|---|---|
| Skript | `slam_validation --live --duration 180` |
| Raum | ca. 15 m^2 |
| Rundweg-Laenge | ca. ___ m |
| Kartenqualitaet (visuell) | ___ (keine doppelten Waende: ja/nein) |
| TF-Rate map->odom | 7.6 Hz |
| Akzeptanz map->odom | >= 1.5 Hz |
| TF-Rate odom->base_link | 18.7 Hz |
| Akzeptanz odom->base_link | >= 15 Hz |
| Topic-Rate /odom | 18.7 Hz |
| Akzeptanz /odom | >= 15 Hz |
| Topic-Rate /scan | 7.6 Hz |
| Akzeptanz /scan | >= 5 Hz |
| Topic-Rate /imu | 32.5 Hz |
| Akzeptanz /imu | >= 25 Hz |
| ATE (RMSE) | 0.3914 m |
| Max. Fehler | 0.8046 m |
| Mittlerer Fehler | 0.3194 m |
| Odom-Posen | 3365 |
| SLAM-Posen | 898 |
| Dauer | 179.4 s |
| Akzeptanz ATE | < 0.20 m |
| **Ergebnis TF-Raten** | **PASS** |
| **Ergebnis Topic-Raten** | **PASS** |
| **Ergebnis ATE** | **FAIL** (0.39 > 0.20 m) |
| **Ergebnis Karte** | **___** |

### Testfall 3.2: ATE (Absolute Trajectory Error)

| Parameter | Wert |
|---|---|
| Skript | `slam_validation --live --duration 120` |
| Modus | Autonome Navigation (Nav2) |
| Odom-Posen | ___ |
| SLAM-Posen | ___ |
| ATE (RMSE) | ___ m |
| Max. Fehler | ___ m |
| Mittlerer Fehler | ___ m |
| Dauer | ___ s |
| Akzeptanz | < 0.20 m |
| **Ergebnis** | **___** |

### Bewertung Phase 3

F03 (Lokalisierung und Kartierung mit SLAM): ___

Anmerkung: TF- und Topic-Raten uebertreffen alle Akzeptanzkriterien deutlich.
Die ATE von 0.39 m zeigt den erwarteten Odometrie-Drift bei laengerer Fahrt
ohne optimalen Loop Closure.

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | ___ | ___/2 PASS |

JSON-Ergebnisdateien:
- `slam_results.json`
