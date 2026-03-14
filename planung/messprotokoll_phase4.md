# Messprotokoll Phase 4: Navigation

Datum: 14.03.2026
Pruefer: —
Testareal: Innenraum, ebener Hartboden (Laminat)
Akkuspannung: > 10 V
Firmware: Drive-Node v4.0.0, Sensor-Node v3.0.0
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
| **Ergebnis** | **ausstehend** |

### Testfall 4.2: ArUco-Docking (10 Versuche)

| Parameter | Wert |
|---|---|
| Skript | `docking_test` |
| Marker-ID | 0 (DICT_4X4_50) |
| Marker-Groesse | 10 cm |
| Startabstand | ca. 1,5-2 m |
| Docking-Distanz | 0,60 m (Ultraschall) |
| Approach-Geschwindigkeit | 0,08 m/s |
| Kamera | IMX296 640x480, kalibriert |

| Versuch | Erfolg | Dauer [s] | Lat. Versatz [cm] | Orient. [deg] | Dist. [m] |
|---------|--------|-----------|-------------------|---------------|-----------|
| 1 | Ja | 19,3 | 0,04 | -9,2 | 0,60 |
| 2 | Ja | 19,2 | -0,89 | -22,5 | 0,60 |
| 3 | Ja | 20,4 | -1,13 | 2,3 | 0,60 |
| 4 | Ja | 19,0 | -0,20 | -6,2 | 0,59 |
| 5 | Ja | 39,3 | -1,22 | -41,4 | 0,59 |
| 6 | Ja | 58,0 | -6,13 | -39,9 | 0,60 |
| 7 | Ja | 29,6 | -3,38 | -3,6 | 0,59 |
| 8 | Ja | 30,3 | -3,26 | 20,3 | 0,60 |
| 9 | Ja | 28,7 | -3,44 | -4,5 | 0,59 |
| 10 | Nein | 60,0 | 0,94 | 3,1 | 0,85 |

| Statistik | Wert |
|---|---|
| Erfolgsquote | 9/10 (90%) |
| Mittl. Versatz | 2,19 cm |
| Std. Versatz | 1,89 cm |
| Mittl. Orient. | 16,6 deg |
| Std. Orient. | 14,5 deg |
| Mittl. Dauer | 29,3 s |
| Std. Dauer | 12,1 s |
| Akzeptanz Erfolgsquote | >= 80 %: **PASS** (90%) |
| Akzeptanz Versatz | < 2 cm: **FAIL** (2,19 cm) |
| **Ergebnis** | **FAIL** (Versatz knapp ueber Schwelle) |

**Bemerkungen:**
- Versuch 6 mit -6,13 cm Versatz ist Ausreisser (Marker bei Annaeherung
  mehrfach verloren, Roboter naeherte sich unter starkem Winkel)
- Ohne Versuch 6: Mittl. Versatz = 1,57 cm (PASS)
- Docking-Kriterium: Ultraschall <= 0,60 m UND Marker innerhalb 2 s sichtbar
- Roboter stoppt nach DOCKED, keine automatische Rueckwaertsfahrt

### Bewertung Phase 4

F04 (Navigation):
- Test 4.1: **ausstehend**
- Test 4.2: **FAIL** (Versatz 2,19 cm, Schwelle 2,0 cm — knapp verfehlt)

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | erfuellt | 2/2 PASS |
| 4 | F04 Navigation | ausstehend | 4.1 ausstehend, 4.2 FAIL |

JSON-Ergebnisdateien:
- `nav_results.json`
- `docking_results.json`
