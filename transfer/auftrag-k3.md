# Auftrag K3 – Sensor-ECU ueber CAN, Controllertausch, Arbiter, BA-05

| Feld | Inhalt |
| --- | --- |
| Dokumenttyp | Claude-Code-Auftrag und Ablauf fuer Ausbaupaket K3 (Phasenplan v2.2, Abschnitt 4) |
| Version | 1.0 (Entwurf) |
| Datum | 2026-09-03 |
| Eingangsbedingung | G0 erfuellt: Tag k2-dbc-v1, T-09 65/65, P-CAN2 Teil A (Fall 1). Nachtraege aus der K2-Abnahme (0x131-Offset, C-Compile-Test, NFA-Abgleich) erledigt oder in Phase 0 enthalten |
| Ausgangsbedingung | IT-10, IT-11, IT-09 (erweitert) bestanden; P-CAN2 Teil B mit NFA-13 erfuellt; BA-04 geklaert; BA-05 Ursache benannt und behoben; Tag k3-sensor-can-v1 |

## 1 Reihenfolge — wer macht was

Die Reihenfolge ist nicht beliebig: Die Nachher-Messung (Teil B) muss mit **unveraenderter Firmware** laufen, sonst ist der Controller-Effekt nicht vom Offset-Effekt trennbar.

```
Jan                                    Claude Code
---------------------------------      ---------------------------------
1  MCP2518FD einbauen, Overlay,        Phase 0  Bestandsaufnahme (read-only)
   sample-point 0.8, V4 messen                  -> Bericht, STOPP, Freigabe
2  P-CAN2 Teil B: A1 + A2 je 10 min    Phase 1  vehicle_can_gateway (Pi)
   (Firmware = Baseline!)              Phase 3  Arbiter twist_mux
   -> NFA-13: 0x200 < 0,1 %, Delta 0
3  BA-05 Diagnoseleiter (3 Messungen)  Phase 4  BA-05-Fix nach Messwerten,
   BA-04 mit Raedern am Boden                   IT-09 erweitert
4  Freigabe Sensor-Flash               Phase 2  Sensor-Firmware: Offsets,
                                                Pack-Funktionen, ggf. S-02
5  T-06/IT-07 (Failsafe) wiederholen,  Phase 5  Protokolle, Doku, Tests
   P-CAN2 Teil C (optional, Offsets)
6  Review, Tag k3-sensor-can-v1
```

Phase 0 bis 1 und 3 koennen sofort starten; sie aendern keine Firmware. Phase 2 wartet auf Schritt 2 und 4.

## 2 Jans Schritte im Detail

| Nr. | Schritt | Nachweis |
| --- | --- | --- |
| J1 | Modul an SPI0 (dieselben sieben Leitungen), Terminierungs-Jumper nur am Busende; config.txt: alte mcp2515-Zeile raus, `dtoverlay=mcp251xfd,spi0-0,interrupt=<GPIO wie bisher>,oscillator=<Hz vom Modul>`; `ip link set can0 up type can bitrate 1000000 sample-point 0.8`; `dmesg | grep mcp251xfd`; `ip -details link show can0` zeigt mcp251xfd und sample-point 0.800 | Bit-Timing-Zeile + Overlay in P-CAN2-B |
| J2 | V4: Widerstand CAN_H–CAN_L stromlos, Soll 60 Ohm — auch in Teil A nachtragen | P-CAN2-A, P-CAN2-B |
| J3 | Teil B: `sudo ./s_a_vorher.sh B1 600` (ohne Objekterkennung) und `B2` (mit), Auswertung mit s_a_analyse.py. Abnahme NFA-13: 0x200 < 0,1 % in beiden Profilen, rx_over_errors Delta 0, bus_error Delta 0 | P-CAN2-B, Vorher-Nachher-Tabelle |
| J4 | BA-05 Diagnoseleiter mit aktiver Objekterkennung: (1) `ros2 topic hz /servo_cmd`; (2) `ros2 topic hz /imu` parallel zu `candump can0,1F0:7FF`; (3) `top -H` je Thread fuer hailo_runner, micro_ros_agent, dashboard_bridge + Rate des Deadman-Topics | Drei Messwerte an Claude Code (Phase 4) |
| J5 | BA-04: Roboter mit Raedern am Boden, 10 min Stand, `/cliff` muss false bleiben; T-05 wiederholen | T-05-Protokoll |
| J6 | Freigabe Sensor-Flash erst nach J3 (Teil B liegt vor) | — |
| J7 | Nach dem Flash: T-06 und IT-07 wiederholen (Failsafe, Cliff-Direktpfad SIA-01/SIA-03 < 20 ms) — das ist ein geaenderter Sicherheitspfad, kein Doku-Update | Testprotokolle |
| J8 | Optional Teil C (`C1`, `C2`): dieselben Profile mit Offsets aktiv; zeigt den Offset-Effekt getrennt vom Controller | P-CAN2-C |

## 3 Claude-Code-Auftrag K3

```
Implementiere ausschliesslich Ausbaupaket K3 gemaess Phasenplan v2.2 (Abschnitt 4,
Paket K3, G1) und Auftrag K3 (docs/plan/auftrag-k3.md). K1 (signalbedarf.md,
Anforderungsliste L1 Abschnitt 13) hat Vorrang vor Vorschlaegen dieses Auftrags;
jede Abweichung im Bericht markieren.

Ziel:
Die Sensor- und Sicherheitsbasis (SENSOR_ECU) erreicht den Pi 5 parallel zum
micro-ROS-Pfad ueber CAN, dekodiert ueber amr_vehicle.dbc; genau eine wirksame
Kommandoquelle fuer den Fahrkern (Arbiter); Heartbeat-Ueberwachung am Pi;
Sensor-Firmware nutzt die generierten Pack-Funktionen und die Sendeoffsets der
DBC; BA-05 behoben; Testfaelle IT-10, IT-11, IT-09 (erweitert) und die
Protokollvorlagen P-CAN2 Teil B/C.

Arbeite in fuenf Phasen. Phase 0 ist read-only und endet mit einem Bericht
und STOPP — keine Aenderung vor meiner Freigabe.

Phase 0 – Bestandsaufnahme (nur lesen, nichts aendern):
 a) Fahrkern-Firmware: Handler fuer 0x120 und 0x141 in twai_can.hpp / control-
    Task lesen. Frage: Reagiert der Fahrkern auf die ANWESENHEIT von 0x141
    oder auf den WERT (shutdown == 1)? Was passiert bei 0x141 mit Wert 0?
    -> Entscheidet, ob S-02 (0x141 zyklisch 1000 ms) in K3 umsetzbar ist
       oder nach K4 (Fahrkern-Firmware) verschoben wird.
 b) Sensor-Firmware: Welcher Task sendet welchen CAN-Frame, mit welcher
    Zeitbasis (Timer, vTaskDelayUntil, Core)? Wo laesst sich
    GenMsgStartDelayTime je Frame umsetzen, ohne die Messtakte (IMU 50 Hz,
    Cliff 20 Hz) zu aendern? Sendelogik 0x141 heute.
 c) Pi: can_bridge_node.py — was liest und sendet er heute (Frames, Topics,
    Rate), sendet der Pi bereits 0x150? Docker: Netzmodus (host?), Zugriff
    auf can0, Capabilities (CAP_SYS_NICE fuer nice/chrt?). Vorschlag: Gateway
    im Container mit cap_add SYS_NICE, oder auf dem Host wie
    host_hailo_runner — mit Begruendung.
 d) Bedien- und Leitstandsebene: Name und Erzeugungsort des Deadman-/
    Heartbeat-Topics (Browser oder dashboard_bridge?), Rate, Executor-Typ
    der Bridge (Single/MultiThreaded), synchrone Aufrufe (Gemini, MJPEG) im
    selben Callback-Pfad wie /servo_cmd und Heartbeat?
 e) twist_mux: im Image vorhanden (ros-humble-twist-mux)? Heutige Publisher
    auf /cmd_vel (BA-03: zwei) mit Knotennamen.
 f) Semantik der Pi-Frames aus L1 13.1/13.3 und der DBC: 0x160
    VCU_EMERGENCY_STOP (rastend? Freigabe wie?), 0x170 VCU_HEARTBEAT,
    alive_counter in 0x400. Formuliere eine Vorrangregel als Vorschlag
    (siehe Wichtig, Punkt 4) — nur Text, keine Firmware.
 g) Generierten C-Code amr_vehicle.c einmal mit Host-gcc uebersetzen und
    die pack()-Funktionen der 13 Bestandsframes gegen die Bytefolgen aus
    der K2-Auswertung 3.1 pruefen (falls in K2-Nachtrag nicht schon
    geschehen). Ergebnis berichten.
 -> Bericht a–g, dann STOPP.

Phase 1 – vehicle_can_gateway (Pi, ROS 2 Humble, Python):
 - can_bridge_node.py zu vehicle_can_gateway weiterentwickeln: DBC ueber
   cantools laden (cantools ins Docker-Image), alle SENSOR_ECU-Frames
   (0x110, 0x120, 0x130, 0x131, 0x140, 0x141, 0x1F0) dekodieren und auf
   Topics /can/sensor/<name> veroeffentlichen — PARALLEL zu den micro-ROS-
   Topics, nichts ersetzen, nichts umbenennen.
 - Heartbeat-Ueberwachung 0x1F0 und 0x2F0: Zustand ECU_OK / ECU_LOST nach
   <= 3 ausgebliebenen Zyklen (SIA-11), als Topic /can/ecu_state und im
   Diagnose-Topic /can/diag (rx_packets, rx_over_errors, bus_error aus
   /sys/class/net/can0/statistics, je 1 Hz).
 - Eigener Prozess mit erhoehter Prioritaet (nice -10; SCHED_FIFO nur wenn
   Phase 0c es erlaubt). RX-Zeitstempel: SO_TIMESTAMPING Hardware, wenn
   der Treiber mcp251xfd es liefert, sonst Software — im Topic mitfuehren.
 - Der Gateway SENDET in K3 nichts Neues. 0x150 nur, wenn der Bestand es
   heute schon sendet (Phase 0c). 0x160/0x170/0x400/0x410 bleiben aus (K4).
 - IT-10 can_b2b_sensor_test: je Signal Wert CAN vs. micro-ROS und
   Zeitversatz; Abnahme FA-18 (<= 1 Quantisierungsschritt, Versatz <= 1
   Sendezyklus); 10-min-Lauf, Markdown-Bericht.

Phase 2 – Sensor-Firmware (einziger Flash in K3; erst nach meiner Freigabe,
          wenn P-CAN2 Teil B vorliegt):
 - Frames mit den generierten Pack-Funktionen aus amr_vehicle.h bauen,
   memcpy-Layouts ersetzen. Bytegleichheit gegen die 13 Vektoren als
   Host-Test (Phase 0g) — ohne diesen Test kein Flash.
 - Sendeoffsets nach DBC (GenMsgStartDelayTime) umsetzen, Messtakte
   unveraendert. 0x130/0x131 im selben Tick (Offset 0/0), falls die DBC das
   nach dem K2-Nachtrag so fuehrt.
 - S-02 (0x141 zyklisch 1000 ms) NUR, wenn Phase 0a ergibt: Fahrkern prueft
   den Wert. Sonst S-02 -> K4, im Bericht markieren, DBC-Attribut bleibt.
 - Kein Empfang neuer Frames (0x160, 0x170, 0x410) — K4/K5.
 - Versionsstring config_sensors.h hochziehen, CHANGELOG.
 - Testskripte fuer T-06/IT-07 (Failsafe, Cliff-Direktpfad) unveraendert
   lauffaehig; ich messe nach dem Flash.

Phase 3 – Arbiter (BA-03, FA-19):
 - twist_mux mit Prioritaeten: Sicherheitslogik (Cliff/LiDAR-Stop) >
   Joystick > Nav2 > automatisiert (Platzhalter-Topic fuer K7). Ausgang
   ist der einzige Publisher auf dem Topic Richtung Fahrkern. Launch und
   Doku anpassen. Sicherheitslogik darf nie ueberstimmt werden.
 - IT-11 cmd_source_test: Anzahl Publisher == 1; Vorrangtest 100/100
   (Sicherheitslogik gegen Joystick und Nav2); Markdown-Bericht.

Phase 4 – BA-05 (erst nach meinen drei Messwerten aus der Diagnoseleiter):
 - Fix je Befund: blockierender Callback -> eigener Thread/Async,
   MultiThreadedExecutor; Scheduling -> nice/chrt fuer Agents und Bridge,
   taskset fuer hailo_runner, MJPEG-Drossel bei aktiver Detektion;
   Browser -> Heartbeat serverseitig erzeugen.
 - Heartbeat-Erzeugung raus aus der Bedien- und Leitstandsebene in einen
   eigenen Timer/Prozess (Vorbereitung SIA-15).
 - IT-09 um Lastprofil A2 erweitern (NFA-15): Latenz < 300 ms, Deadman
   >= 5 Hz ohne Luecke > 500 ms, /servo_cmd 10/10 Hz ueber 10 min bei
   aktiver Objekterkennung.

Phase 5 – Protokolle, Doku, Abgleich:
 - P-CAN2 Teil B und C: Vorlagen; s_a_vorher.sh/s_a_analyse.py fuer den
   mcp251xfd-Treiber pruefen (Zaehlerpfade identisch?), Vorher-Nachher-
   Tabelle A vs. B je ID.
 - Phasenplan: NFA-13/NFA-14 an L1 angleichen (D-06), D-05 mit 300 ms
   eintragen, Vorrangregel aus Phase 0f als D-10 (offen) aufnehmen.
 - Signalkatalog: Einleitungssatz "Bereiche sind Prioritaetsklassen, nicht
   Sender" (0x150/0x160/0x170 sind PI_VCU-Frames im 0x1xx-Bereich).
 - communication.md nicht umschreiben (K6) — nur Hinweis "K3: Sensorpfad
   parallel ueber CAN".
 - Build/Lint/Tests: pytest, pre-commit, mkdocs --strict, pio run fuer die
   Sensor-Firmware; bei Fehlern stoppen.

Wichtig:
 - Fahrkern-Firmware NICHT aendern (K4). Keine Fahrbefehle ueber CAN.
   micro-ROS/USB unveraendert. Keine Fahrbewegung durch Claude Code.
 - Reihenfolge: P-CAN2 Teil B laeuft mit Baseline-Firmware; Phase 2 erst
   nach meiner Freigabe.
 - Punkt 4 (drei Lebenszeichen vom Pi): alive_counter in 0x400 (50 Hz),
   0x170 (10 Hz), 0x160 (10 Hz). In K3 nur die Vorrangregel als Text
   vorschlagen. Leitgedanke: im Modus CAN_PRIMARY ist der alive_counter
   in 0x400 die Wahrheit fuer den Fahrkern; 0x170 fuer die Sensor-ECU;
   0x160 rastend, Freigabe ueber operating_mode. Alle drei werden im
   Gateway-Prozess erzeugt, nie in der Bedien- und Leitstandsebene (SIA-15).
 - Punkt 5 (S-02, 0x141 zyklisch): aendert den Notstopppfad. Nur mit
   Wertpruefung im Fahrkern; danach T-06/IT-07 pflichtig (SIA-01/SIA-03
   < 20 ms). Im Zweifel nach K4 verschieben.
 - Punkt 6 (t_timeout 300 ms, L1 13.3): in K3 nicht anfassen. Der Shadow
   Mode in K4 liefert die Ankunftsluecken von 0x400; erst dann D-05 mit
   Daten nachschaerfen.
 - Keine Anforderungs-IDs erfinden; bei Konflikt Phasenplan vs. L1 gilt L1,
   Konflikt im Bericht nennen.
 - Generierte Dateien nicht handeditieren. Stilregeln: keine UTF-8-Umlaute
   in Markdown, Terminologie-Norm.

Zeige vor jedem Commit:
 1. Phase-0-Bericht a–g (vor allem anderen),
 2. Aenderungen je Datei mit Bezug auf Phase und Anforderung,
 3. Ergebnisse IT-10, IT-11, IT-09 (erweitert), T-09 (unveraendert gruen),
 4. Firmware-Diff der Sensorbasis mit Bytegleichheitstest,
 5. Liste der Abweichungen von diesem Auftrag und von K1,
 6. geplanten Commit und Tag k3-sensor-can-v1.
Noch nicht committen. Nicht flashen ohne Freigabe.
```

## 4 Abnahme K3 (Ausgang G1-Teil)

| Nachweis | Kriterium | Quelle |
| --- | --- | --- |
| P-CAN2 Teil B | 0x200 < 0,1 % in B1 und B2; rx_over_errors Delta 0; bus_error Delta 0 | NFA-13 |
| IT-10 | Abweichung <= 1 Quantisierungsschritt, Versatz <= 1 Sendezyklus, alle sieben Sensorframes | FA-18 |
| IT-11 | 1 Publisher; Vorrang 100/100 | FA-19 |
| IT-09 erweitert | FA-13-Schwellwerte unter Lastprofil A2 | NFA-15 |
| T-05 | 0 Cliff-Fehlalarme in 10 min mit Bodenkontakt | BA-04 |
| T-06, IT-07 | Failsafe und Cliff-Direktpfad nach Sensor-Flash unveraendert | SIA-01, SIA-03 |
| Bericht | S-02-Entscheidung, Vorrangregel-Vorschlag (D-10), NFA-Abgleich | D-06, Punkt 4/5 |

G1 ist bestanden, wenn NFA-13 und NFA-15 erfuellt sind. Dann K4.

---

Ohne Zwiebel-/Bloch-/Nguyen-Kim-Modul erstellt (Minimal-Set: Ehrlichkeit + Quellen-Traceability).
