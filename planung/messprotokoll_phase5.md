# Messprotokoll Phase 5: Bedien- und Leitstandsebene

Datum: 15.03.2026
Pruefer: ---
Testareal: Innenraum, ebener Hartboden
Akkuspannung: > 10 V
Firmware: Drive-Node v___, Sensor-Node v___
Software: ROS2 Humble (Docker), Dashboard (React/Vite)
Audio: MAX98357A I2S + 3W Lautsprecher
ESP32: inaktiv (Dashboard-only Test)

---

## Phase 5: Bedien- und Leitstandsebene (F05)

### Testfall 5.1: cmd_vel-Latenz

| Parameter | Wert |
|---|---|
| Skript | `dashboard_latency_test.py --samples 100` |
| WebSocket-URL | ws://localhost:9090 |
| Datenpfad | WebSocket -> dashboard_bridge -> cliff_safety -> /cmd_vel |
| Samples | 100 |
| min Latenz | 1,0 ms |
| avg Latenz | 5,9 ms |
| p95 Latenz | 2,7 ms |
| max Latenz | 435,0 ms |
| Akzeptanz p95 | < 100 ms: PASS |
| Akzeptanz avg | < 50 ms: PASS |
| **Ergebnis** | **PASS** |

### Testfall 5.2: Telemetrie-Vollstaendigkeit

| Parameter | Wert |
|---|---|
| Messdauer | 30 s |
| telemetry Hz | 9,9 (Soll >= 4 Hz) |
| system Hz | 1,0 (Soll >= 0,25 Hz) |
| nav_status Hz | 1,0 (Soll >= 0,25 Hz) |
| sensor_status Hz | 2,0 (Soll >= 0,5 Hz) |
| audio_status Hz | 2,0 (Soll >= 0,5 Hz) |
| Pflicht-Typen empfangen | 5/5 |
| Optionale Typen empfangen | scan: nein, map: nein, vision_detections: nein, vision_semantics: nein |
| **Ergebnis** | **PASS** |

### Testfall 5.3: Deadman-Timer

| Parameter | Wert |
|---|---|
| Fahrdauer vor Abbruch | 3 s |
| Deadman-Timeout (Soll) | 300 ms |
| Gemessene Stopp-Latenz | 251,6 ms |
| Akzeptanz | < 500 ms: PASS |
| **Ergebnis** | **PASS** |

### Testfall 5.4: Audio-Feedback

| Sound-Key | Auf /audio/play empfangen | Akustisch gehoert |
|---|---|---|
| startup | ja | --- |
| nav_start | ja | --- |
| nav_reached | ja | --- |
| cliff_alarm | ja | --- |

| Parameter | Wert |
|---|---|
| Keys empfangen | 4/4 |
| Akzeptanz | 4/4: PASS |
| **Ergebnis** | **PASS** |

### Testfall 5.5: Notaus

| Parameter | Wert |
|---|---|
| Fahrdauer vor Notaus | 2 s |
| Notaus-Pattern | 5x cmd_vel(0, 0) |
| Gemessene Stopp-Latenz | 2,1 ms |
| Akzeptanz | < 100 ms: PASS |
| **Ergebnis** | **PASS** |

### Bewertung Phase 5

F05 (Bedien- und Leitstandsebene):
- Test 5.1 (cmd_vel-Latenz): PASS
- Test 5.2 (Telemetrie-Vollstaendigkeit): PASS
- Test 5.3 (Deadman-Timer): PASS
- Test 5.4 (Audio-Feedback): PASS
- Test 5.5 (Notaus): PASS

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | erfuellt | 2/2 PASS |
| 4 | F04 Navigation | erfuellt | 4.1 PASS, 4.2 PASS |
| 5 | F05 Bedien- und Leitstandsebene | erfuellt | 5/5 PASS |

JSON-Ergebnisdateien:
- `dashboard_results.json`
