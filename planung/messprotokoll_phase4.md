# Messprotokoll Phase 4: Navigation

Datum: 15.03.2026
Pruefer: —
Testareal: Innenraum, ebener Hartboden (Laminat)
Akkuspannung: > 10 V
Firmware: Drive-Node v4.0.0, Sensor-Node v3.0.0
Software: ROS2 Humble (Docker), Nav2 (Regulated Pure Pursuit)

---

## Phase 4: Navigation (F04)

### Testfall 4.1: Waypoint-Navigation (1 m x 1 m Rechteck, zweistufig)

#### Schritt 1: Karte aufzeichnen (cmd_vel-Quadrat)

| Parameter | Wert |
|---|---|
| Skript | `nav_square_test.py --speed 0.10` |
| Freie Flaeche | ca. ___ m x ___ m |
| Waypoints | 4 (1 m x 1 m Rechteck, cmd_vel) |
| WP1 xy-Fehler | ___ m |
| WP1 yaw-Fehler | ___ rad |
| WP2 xy-Fehler | ___ m |
| WP2 yaw-Fehler | ___ rad |
| WP3 xy-Fehler | ___ m |
| WP3 yaw-Fehler | ___ rad |
| WP4 xy-Fehler | ___ m |
| WP4 yaw-Fehler | ___ rad |
| Gesamtdauer | ___ s |
| Karte gespeichert | testfeld.yaml / testfeld.pgm |
| Bemerkungen | ___ |

#### Schritt 2: Karte speichern

```
ros2 run nav2_map_server map_saver_cli -f /ros2_ws/src/my_bot/maps/testfeld
```

Karte gespeichert: Ja / Nein

#### Schritt 3: Nav2-Waypoint-Navigation

| Parameter | Wert |
|---|---|
| Skript | `nav_test.py --timeout 60` |
| Karte | testfeld (aus Schritt 2) |
| Waypoints | 4 (1 m x 1 m Rechteck, Nav2) |
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
| Docking-Distanz | 0,30 m (Ultraschall) |
| Approach-Geschwindigkeit | 0,08 m/s |
| Kamera | IMX296 640x480, kalibriert |

| Versuch | Erfolg | Dauer [s] | Lat. Versatz [cm] | Orient. [deg] | Dist. [m] |
|---------|--------|-----------|-------------------|---------------|-----------|
| 1 | Ja | 22,3 | 0,37 | -5,8 | 0,29 |
| 2 | Ja | 47,8 | -0,10 | -13,2 | 0,29 |
| 3 | Ja | 22,1 | 0,26 | 3,9 | 0,29 |
| 4 | Ja | 55,2 | 0,04 | -11,0 | 0,29 |
| 5 | Ja | 45,4 | 0,34 | -20,8 | 0,29 |
| 6 | Ja | 22,6 | 0,69 | -18,8 | 0,30 |
| 7 | Ja | 44,2 | 0,45 | -32,9 | 0,29 |
| 8 | Ja | 24,8 | 0,87 | -9,4 | 0,30 |
| 9 | Ja | 36,8 | -3,18 | -13,0 | 0,29 |
| 10 | Ja | 40,6 | -0,96 | -12,2 | 0,30 |

| Statistik | Wert |
|---|---|
| Erfolgsquote | 10/10 (100%) |
| Mittl. Versatz | 0,73 cm |
| Std. Versatz | 0,87 cm |
| Mittl. Orient. | 14,1 deg |
| Std. Orient. | 7,9 deg |
| Mittl. Dauer | 36,2 s |
| Std. Dauer | 11,7 s |
| Akzeptanz Erfolgsquote | >= 80 %: **PASS** (100%) |
| Akzeptanz Versatz | < 2 cm: **PASS** (0,73 cm) |
| **Ergebnis** | **PASS** |

**Bemerkungen:**
- Dreifach-Docking-Bedingung: Ultraschall <= 0,30 m UND Marker sichtbar UND Versatz <= 5 cm
- Versuch 9 mit -3,18 cm Versatz groesster Ausreisser (Marker bei Annaeherung
  seitlich versetzt, Roboter korrigierte spaet)
- Ohne Versuch 9: Mittl. Versatz = 0,45 cm
- Bei Marker-Verlust: sofortige Drehung um Hochachse zur Markersuche
- Fehlausrichtungs-Recovery: Zuruecksetzen + Neuausrichtung bei Nah-aber-schlecht
- Roboter stoppt nach DOCKED, keine automatische Rueckwaertsfahrt

### Bewertung Phase 4

F04 (Navigation):
- Test 4.1: **ausstehend**
- Test 4.2: **PASS** (100% Erfolgsquote, 0,73 cm mittl. Versatz)

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | erfuellt | 2/2 PASS |
| 4 | F04 Navigation | ausstehend | 4.1 ausstehend, 4.2 PASS |

JSON-Ergebnisdateien:
- `nav_results.json`
- `docking_results.json`
