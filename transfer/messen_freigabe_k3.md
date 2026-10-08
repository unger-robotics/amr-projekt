# Messen

Beides sind Messungen am unveränderten System — kein Flash, keine Codeänderung, Roboter aufgebockt (Räder frei), voller Stack läuft.

## J3 — P-CAN2 Teil B (nachher)

**Voraussetzung prüfen** (sonst misst du das Falsche):

```bash
ip -details link show can0        # muss "mcp251xfd" und "sample-point 0.800" zeigen, bitrate 1000000
dmesg | grep -i mcp251xfd         # Treiber geladen, keine "CRC"- oder "FIFO"-Fehler
```

Firmware auf beiden XIAO = Baseline-Commit, nichts geflasht. V4 vorher stromlos messen: CAN_H–CAN_L, Soll 60 Ω.

**Messen** — exakt wie Teil A, nur mit dem Label B:

```bash
sudo ./s_a_vorher.sh B1 600        # Stack an, Objekterkennung AUS, Dashboard ohne Kamera-Overlay
python3 s_a_analyse.py validation/P-CAN2/<datum>_B1
sudo ./s_a_vorher.sh B2 600        # Objekterkennung AN, wie bei A2
python3 s_a_analyse.py validation/P-CAN2/<datum>_B2
```

Gleiche Dashboard-Ansichten wie in A1/A2, gleiche 600 s. Der mcp251xfd-Treiber führt `rx_over_errors` und `bus_error` unter denselben Namen — das Skript passt unverändert.

**Lesen — drei Zahlen entscheiden:**

| Größe                      | Soll (NFA-13) | Teil A zum Vergleich |
|----------------------------|---------------|----------------------|
| Verlust 0x200 in B1 und B2 | < 0,1 %       | 21,5 / 27,4 %        |
| `rx_over_errors` Δ         | 0             | 6674 / 6001          |
| `bus_error` Δ              | 0             | 0 / 0                |

Bestanden → in P-CAN2-B die Vorher-Nachher-Tabelle je ID ausfüllen, Bit-Timing-Zeile aus `meta.txt` und V4 eintragen. Nicht bestanden → `dmesg` nach "overflow" oder "CRC" durchsuchen; bleibt Verlust bei Δ 0, liegt es nicht mehr am Controller, sondern beim Sender (Fall 3) — dann nicht flashen, sondern melden.

## J4 — BA-05 Diagnoseleiter

Ziel: die Stelle finden, an der der Steuerpfad unter Objekterkennung stirbt. Drei Terminals: zwei im ROS-2-Container (`docker exec -it <container> bash`, `source /opt/ros/humble/setup.bash`), eines auf dem Host.

**Vorbereitung:** Topic-Namen einmal nachsehen:

```bash
ros2 topic list | grep -iE 'servo|heart|dead|alive|imu'
```

**Jeder der drei Schritte wird zweimal gemacht**: erst Objekterkennung AUS (Referenz, 2 min), dann AN (3 min). Während jeder Messung den Pan-Slider im Dashboard ständig bewegen, damit `/servo_cmd` durchgehend fließt.

**Messung 1 — Kommt das Kommando aus der Bridge?**

```bash
ros2 topic hz /servo_cmd --window 20
```

Referenz ≈ 10 Hz. Unter Detektion weiter ≈ 10 Hz → Ursache liegt *hinter* der Bridge (Agent, Seriell, MCU). Rate bricht ein oder stoppt → *vor* der Bridge (Bridge, WebSocket, Browser).
Gegenprobe, wenn es stoppt: `/servo_cmd` mit `ros2 topic pub -r 10 /servo_cmd <Typ> "{...}"` direkt aus dem Container senden. Bewegt sich der Servo jetzt trotz Detektion, ist die Bridge/Browser-Seite schuldig, nicht der Pfad zur MCU.

**Messung 2 — Lebt die micro-ROS-Session, lebt die MCU?**

```bash
ros2 topic hz /imu --window 50 --qos-reliability best_effort     # Container
candump -td can0,130:7FF,1F0:7FF                                 # Host
```

Referenz `/imu` ≈ 30–50 Hz, CAN 0x130 alle 20 ms, 0x1F0 alle 1000 ms. Bricht `/imu` ein, während 0x130 sauber weiterläuft → Session gestört, MCU lebt. Springt der Uptime-Wert in 0x1F0 zurück → MCU bootet (dann doch Strom oder Watchdog). Dazu einmal `docker logs <micro-ros-agent> --since 5m | grep -iE 'session|timeout|ping'`.

**Messung 3 — Wer frisst die CPU, hält der Deadman?**

```bash
top -H -d 1            # Host; Taste P sortiert nach CPU; die obersten fünf Threads notieren
ros2 topic hz /<deadman-topic> --window 20                       # Container, parallel
```

Notieren: Gesamtauslastung (Zeile `%Cpu(s)`, Wert `id`), Threads von `python3` (dashboard_bridge), `micro_ros_agent`, `host_hailo_runner`. Deadman: Soll ≥ 5 Hz; entscheidend ist `max` im hz-Ausgang — über 0,5 s heißt SIA-04 hat ausgelöst, dann ist nicht der Servo tot, sondern das Fahrzeug.

**Was du mir schickst — eine Tabelle, zwei Zeilen (Detektion aus / an):**

| /servo_cmd Hz | /imu Hz | 0x130 dt | 0x1F0 Uptime stetig? | Deadman Hz / max-Intervall | %Cpu idle | Top-3-Threads | Agent-Log | Servo reagiert |
|---------------|---------|----------|----------------------|----------------------------|-----------|---------------|-----------|----------------|

Daraus folgt der Fall für D-09: (a) `/servo_cmd` bricht ein und der Bridge-Thread steht bei 100 % oder wartet → blockierender Callback; (b) CPU idle nahe 0, `/imu` fällt, `/servo_cmd` wird noch publiziert, Agent-Log meldet Timeouts → Scheduling; (c) `/servo_cmd` fehlt, Bridge-CPU niedrig, Gegenprobe funktioniert → Browser/WebSocket. Danach weiß Claude Code in Phase 4, was es fixt — und nicht vorher.
