# Messprotokoll Phase 5: Bedien- und Leitstandsebene

Datum: ___
Pruefer: ---
Testareal: Innenraum, ebener Hartboden
Akkuspannung: > 10 V
Firmware: Drive-Node v___, Sensor-Node v___
Software: ROS2 Humble (Docker), Dashboard (React/Vite)
Audio: MAX98357A I2S + 3W Lautsprecher

---

## Phase 5: Bedien- und Leitstandsebene (F05)

### Testfall 5.1: cmd_vel-Latenz

| Parameter | Wert |
|---|---|
| Skript | `dashboard_latency_test.py --samples 100` |
| WebSocket-URL | ws://localhost:9090 |
| Datenpfad | WebSocket -> dashboard_bridge -> cliff_safety -> /cmd_vel |
| Samples | ___ |
| min Latenz | ___ ms |
| avg Latenz | ___ ms |
| p95 Latenz | ___ ms |
| max Latenz | ___ ms |
| Akzeptanz p95 | < 100 ms: ___ |
| Akzeptanz avg | < 50 ms: ___ |
| **Ergebnis** | ___ |

### Testfall 5.2: Telemetrie-Vollstaendigkeit

| Parameter | Wert |
|---|---|
| Messdauer | 30 s |
| telemetry Hz | ___ (Soll >= 4 Hz) |
| system Hz | ___ (Soll >= 0.25 Hz) |
| nav_status Hz | ___ (Soll >= 0.25 Hz) |
| sensor_status Hz | ___ (Soll >= 0.5 Hz) |
| audio_status Hz | ___ (Soll >= 0.5 Hz) |
| Pflicht-Typen empfangen | ___/5 |
| Optionale Typen empfangen | scan: ___, map: ___, vision_detections: ___, vision_semantics: ___ |
| **Ergebnis** | ___ |

### Testfall 5.3: Deadman-Timer

| Parameter | Wert |
|---|---|
| Fahrdauer vor Abbruch | 3 s |
| Deadman-Timeout (Soll) | 300 ms |
| Gemessene Stopp-Latenz | ___ ms |
| Akzeptanz | < 500 ms: ___ |
| **Ergebnis** | ___ |

### Testfall 5.4: Audio-Feedback

| Sound-Key | Auf /audio/play empfangen | Akustisch gehoert |
|---|---|---|
| startup | ___ | ___ |
| nav_start | ___ | ___ |
| nav_reached | ___ | ___ |
| cliff_alarm | ___ | ___ |

| Parameter | Wert |
|---|---|
| Keys empfangen | ___/4 |
| Akzeptanz | 4/4: ___ |
| **Ergebnis** | ___ |

### Testfall 5.5: Notaus

| Parameter | Wert |
|---|---|
| Fahrdauer vor Notaus | 2 s |
| Notaus-Pattern | 5x cmd_vel(0, 0) |
| Gemessene Stopp-Latenz | ___ ms |
| Akzeptanz | < 100 ms: ___ |
| **Ergebnis** | ___ |

### Bewertung Phase 5

F05 (Bedien- und Leitstandsebene):
- Test 5.1 (cmd_vel-Latenz): ___
- Test 5.2 (Telemetrie-Vollstaendigkeit): ___
- Test 5.3 (Deadman-Timer): ___
- Test 5.4 (Audio-Feedback): ___
- Test 5.5 (Notaus): ___

---

## Gesamtuebersicht

| Phase | Anforderung | Status | Testfaelle |
|---|---|---|---|
| 1 | F01 Fahrkern | erfuellt | 3/3 PASS |
| 2 | F02 Sensor- und Sicherheitsbasis | erfuellt | 11/11 PASS |
| 3 | F03 Lokalisierung und Kartierung | erfuellt | 2/2 PASS |
| 4 | F04 Navigation | erfuellt | 4.1 PASS, 4.2 PASS |
| 5 | F05 Bedien- und Leitstandsebene | ___ | 5.1-5.5 ___ |

JSON-Ergebnisdateien:
- `dashboard_results.json`
