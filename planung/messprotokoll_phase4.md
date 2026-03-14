# Messprotokoll Phase 4: Navigation

Datum:
Pruefer:
Testareal: Innenraum, ca. ___ m^2, ebener Hartboden (___)
Akkuspannung: ___ V (SOC ___ %)
Firmware: Drive-Node v___, Sensor-Node v___
Software: ROS2 Humble (Docker), Nav2 (Regulated Pure Pursuit)

---

## Phase 4: Navigation (F04)

### Testfall 4.1: Waypoint-Navigation (1 m x 1 m Rechteck)

| Parameter | Wert |
|---|---|
| Skript | `nav_test --timeout 60` |
| Freie Flaeche | ca. ___ m x ___ m |
| Waypoints | 4 (1 m x 1 m Rechteck) |
| WP1 xy-Fehler | ___ m |
| WP1 Gier-Fehler | ___ rad |
| WP1 Dauer | ___ s |
| WP1 Status | ___ |
| WP2 xy-Fehler | ___ m |
| WP2 Gier-Fehler | ___ rad |
| WP2 Dauer | ___ s |
| WP2 Status | ___ |
| WP3 xy-Fehler | ___ m |
| WP3 Gier-Fehler | ___ rad |
| WP3 Dauer | ___ s |
| WP3 Status | ___ |
| WP4 xy-Fehler | ___ m |
| WP4 Gier-Fehler | ___ rad |
| WP4 Dauer | ___ s |
| WP4 Status | ___ |
| Max. xy-Fehler | ___ m |
| Max. Gier-Fehler | ___ rad |
| Kollision | Nein / Ja (___) |
| Recovery beobachtet | Nein / Ja (___) |
| Cliff-Safety aktiv | Ja / Nein |
| Akzeptanz xy | < 0,10 m |
| Akzeptanz Gier | < 0,15 rad (~8,6 Grad) |
| **Ergebnis** | **PASS / FAIL** |

### Testfall 4.2: ArUco-Docking (10 Versuche)

| Parameter | Wert |
|---|---|
| Skript | `docking_test` |
| Marker-ID | 0 (DICT_4X4_50) |
| Marker-Groesse | 10 cm |
| Startabstand | ca. 1,5 m |

| Versuch | Erfolg | Dauer [s] | Lat. Versatz [cm] | Orient. [deg] |
|---------|--------|-----------|-------------------|---------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |

| Statistik | Wert |
|---|---|
| Erfolgsquote | ___/10 (___%) |
| Mittl. Versatz | ___ cm |
| Std. Versatz | ___ cm |
| Mittl. Orient. | ___ deg |
| Mittl. Dauer | ___ s |
| Akzeptanz Erfolgsquote | >= 80 % |
| Akzeptanz Versatz | < 2 cm |
| **Ergebnis** | **PASS / FAIL** |

### Bewertung Phase 4

F04 (Navigation): **erfuellt / nicht erfuellt**

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | erfuellt | 2/2 PASS |
| 4 | F04 Navigation | ___ | ___/___ |

JSON-Ergebnisdateien:
- `nav_results.json`
- `docking_results.json`
