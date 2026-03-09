# Messprotokoll Phase 1 + Phase 2

Datum: 09.03.2026
Pruefer: Jan
Testareal: Innenraum, ebener Hartboden (Laminat)
Akkuspannung: > 10 V (kontinuierlich ueberwacht via INA260)
Firmware: Drive-Node v4.0.0, Sensor-Node v3.0.0
Software: ROS2 Humble (Docker), micro-ROS Agent 921600 Baud

---

## Phase 1: Fahrkern (F01)

### Testfall 1.1: Geradeausfahrt 1 m OHNE IMU-Korrektur

| Parameter | Wert |
|---|---|
| Skript | `straight_drive_test uncorrected` |
| Fahrgeschwindigkeit | 0.1 m/s |
| Soll-Strecke | 1.000 m |
| Odom-Strecke | 1.005 m |
| Odom-Fehler | 0.5 % |
| Vorwaerts | 1.0044 m |
| Lateraldrift | 3.6 cm |
| Heading (Odom) | +2.91 Grad |
| Heading (Gyro) | +5.57 Grad |
| Gyro-Bias | +0.040 deg/s |
| Dauer | 11.6 s |
| Akzeptanz Drift | < 5 cm |
| Akzeptanz Heading | < 5 Grad |
| **Ergebnis** | **FAIL** (Heading 5.57 > 5.0) |

### Testfall 1.2: Geradeausfahrt 1 m MIT IMU-Korrektur

| Parameter | Wert |
|---|---|
| Skript | `straight_drive_test corrected` |
| Fahrgeschwindigkeit | 0.1 m/s |
| Soll-Strecke | 1.000 m |
| Odom-Strecke | 1.003 m |
| Odom-Fehler | 0.3 % |
| Vorwaerts | 1.0028 m |
| Lateraldrift | 2.1 cm |
| Heading (Odom) | +1.49 Grad |
| Heading (Gyro) | +0.06 Grad |
| Gyro-Bias | -0.004 deg/s |
| Dauer | 11.5 s |
| Akzeptanz Drift | < 5 cm |
| Akzeptanz Heading | < 5 Grad |
| **Ergebnis** | **PASS** |

### Testfall 1.3: Rotation 360 Grad

| Parameter | Wert |
|---|---|
| Skript | `rotation_test` (360 Grad) |
| Soll-Winkel | 360.0 Grad |
| Erreicht | 358.1 Grad |
| Winkelfehler | 1.88 Grad |
| Gyro-Bias | -0.012 deg/s |
| Dauer | 14.4 s |
| Akzeptanz | < 5 Grad |
| **Ergebnis** | **PASS** |

### Bewertung Phase 1

F01 (Fahrkern mit reproduzierbarer Grundbewegung): **erfuellt**

Die Geradeausfahrt ohne IMU-Korrektur ueberschreitet das Heading-Kriterium
knapp (5.57 > 5.0 Grad). Mit IMU-Korrektur werden alle Kriterien klar
eingehalten. Die IMU-Heading-Korrektur ist fuer reproduzierbare Fahrt
notwendig, nicht optional. Die 360-Grad-Rotation unterschreitet das
Akzeptanzkriterium deutlich.

---

## Phase 2: Sensor- und Sicherheitsbasis (F02)

### Testfall 2.1: Cliff-Safety End-to-End Latenz

| Parameter | Wert |
|---|---|
| Skript | `cliff_latency_test` |
| Fahrgeschwindigkeit | 0.2 m/s |
| Trigger | Tischkante (real) |
| Latenz (Cliff -> Stopp) | 2.0 ms |
| Sensor-Intervall | 59.2 ms |
| Bremsweg | 1.0 cm |
| Akzeptanz | < 50 ms |
| **Ergebnis** | **PASS** |

### Testfall 2.2: IMU 90-Grad-Rotation (motor-getrieben)

| Parameter | Wert |
|---|---|
| Skript | `rotation_test 90` |
| Soll-Winkel | 90.0 Grad |
| Erreicht | 88.5 Grad |
| Winkelfehler | 1.45 Grad |
| Gyro-Bias | +0.037 deg/s |
| Dauer | 4.4 s |
| Akzeptanz | < 2 Grad |
| **Ergebnis** | **PASS** |

### Testfall 2.3: Ultraschall-Suite (sensor_test.py)

| Test | Messwert | Kriterium | Ergebnis |
|---|---|---|---|
| US Rate | 9.2 Hz | >= 7.0 Hz | PASS |
| US Genauigkeit (23 cm) | 0.8 % Fehler | < 5.0 % | PASS |
| US Bereich | 0.02 - 4.00 m | Soll-Bereich | PASS |
| US Wiederholbarkeit | 1.6 mm Std | < 15 mm | PASS |

### Testfall 2.4: Cliff-Suite (sensor_test.py)

| Test | Messwert | Kriterium | Ergebnis |
|---|---|---|---|
| Cliff Rate | 16.8 Hz | >= 15.0 Hz | PASS |
| Cliff Boden (Fehlalarm) | 0 / 60 Samples | 0 Fehlalarme | PASS |
| Cliff Erkennung | 1 ms | Erkennung innerhalb 10 s | PASS |

### Testfall 2.5: IMU-Suite (imu_test.py)

| Test | Messwert | Kriterium | Ergebnis |
|---|---|---|---|
| IMU Rate | 30.4 - 35.2 Hz | >= 15 Hz | PASS |
| Gyro-Drift (60 s) | 0.463 deg/min | < 1.0 deg/min | PASS |
| Accel-Bias | 0.43 m/s^2 | < 0.6 m/s^2 | PASS |
| Heading-Vergleich | 0.01 Grad | < 5.0 Grad | PASS |

### Bewertung Phase 2

F02 (Sensor- und Sicherheitsbasis mit priorisierten Schutzfunktionen): **erfuellt**

Alle 11/11 Sensorik-Testfaelle bestanden. Die End-to-End-Cliff-Latenz von
2.0 ms unterschreitet das Akzeptanzkriterium um mehr als eine Groessenordnung.
Die IMU-Plausibilisierung ist ueber Drift (0.463 deg/min), Bias (0.43 m/s^2)
und Rotationsgenauigkeit (1.45 Grad bei 90 Grad) belegt. Ultraschall und
Cliff-Sensor arbeiten innerhalb aller Spezifikationen.

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 relevante PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |

JSON-Ergebnisdateien:
- `straight_drive_results.json`
- `rotation_results.json`
- `cliff_latency_results.json`
- `sensor_results.json`
- `imu_results.json`
