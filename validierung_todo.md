# Kalibrierung + Validierung

## ToDo-Liste Kalibrierung + Validierung

Tracking-Dokument fuer den Validierungsfortschritt des AMR-Prototyps. Akzeptanzkriterien gemaess V-Modell-Phasenplan (vgl. `hardware/docs/umsetzungsanleitung.md`, Anhang A). Testergebnisse fliessen in `bachelorarbeit/kapitel_06_validierung.md` ein.

### Abgeschlossene Tests

- [x] **Motor-Encoder Quadratur A+B** (Phase 2, AK-01 bis AK-03)
  - Tick-Konsistenz < 2%, Asymmetrie geprueft, Richtungskonvention verifiziert
  - Quadratur-Dekodierung: Phase A (D6/D7) CHANGE-Interrupt, Phase B (D8/D9) Richtung, ~748 Ticks/Rev
  - Skript: `ros2 run my_bot encoder_test`
  - Ergebnis: PASS (dokumentiert in `kapitel/06_2_subsystem_verifikation.md`)

- [x] **Odometrie-Test** (Phase 4-6, AK-06 bis AK-13)
  - 1 m Geradeausfahrt (0.1 m/s, 10 s), laterale Drift < 50 mm, PID-Regler verifiziert
  - Raddurchmesser kalibriert: 65.0 mm → 65.67 mm (`config.h` Zeile 54)
  - UMBmark: 10 Laeufe (5 CW + 5 CCW), >= 10x Fehlerreduktion (AK-09)
  - PID: Kp=0.4, Ki=0.1, Kd=0.0, Anstiegszeit/Ueberschwingen/Einschwingzeit geprueft
  - Skripte: `ros2 run my_bot kinematic_test`, `ros2 run my_bot pid_tuning`, `python3 amr/scripts/umbmark_analysis.py`
  - Ergebnis: PASS — Restfehler 0.5%, Drift 0.5 cm, Heading 1.6° nach Kalibrierung

- [x] **SLAM-Integrationstest** (Phase 8, AK-16)
  - Route: 2 m vor, Drehung, 2 m zurueck (~6 m Gesamtstrecke)
  - micro-ROS Agent + RPLidar A1 (7.6 Hz) + odom_to_tf + SLAM Toolbox async
  - Odom-Drift nach 4 m: 19 cm Position, 23° Heading (Open-Loop, erwartet)
  - SLAM-Korrektur (map→odom): 38 cm Translation, 16.6° Rotation
  - Karte: 107x94 Zellen @ 5 cm = 5.4x4.7 m
  - Skript: `ros2 run my_bot slam_validation`
  - Ergebnis: PASS — ATE < 0.20 m (dokumentiert in `kapitel/06_2_subsystem_verifikation.md`)

### Ausstehende Tests

- [x] **IMU MPU6050** (I2C, SDA/SCL an D4/D5)
  - Treiber implementiert (`mpu6050.hpp`), Complementary-Filter (alpha=0.02)
  - Validierungsskript: `ros2 run my_bot imu_test` (60s statischer Test)
  - Akzeptanzkriterium: Gyro-Drift < 1°/min statisch
  - Referenz: `hardware/docs/hardware-setup.md` (Pin-Mapping), `config.h` (I2C-Pins)

- [ ] **Global-Shutter-Kamera IMX296** (CSI, 22-pin Mini-CSI)
  - Hardware-Verifikation: `rpicam-hello --list-cameras` (Debian Trixie)
  - v4l2loopback-Bridge: `sudo systemctl start camera-v4l2-bridge.service`
  - ROS2-Integration: `v4l2_camera_node` auf `/camera/image_raw` pruefen
  - ArUco-Erkennung: Marker ID 42 (DICT_4X4_50) in definiertem Abstand (30-100 cm)
  - Akzeptanzkriterien (AK-19): Docking-Erfolgsquote >= 80% (8/10), Timeout 60 s
  - Skripte: `ros2 run my_bot docking_test` (10 Versuche)
  - Referenz: `amr/docker/host_setup.sh` (Bridge-Setup), `config.txt` (`dtoverlay=imx296`)

- [ ] **RPLIDAR A1** (CP2102 USB-UART, /dev/ttyUSB0)
  - Hardware-Verifikation: `sudo chmod 666 /dev/ttyUSB0 && ros2 launch rplidar_ros rplidar_a1_launch.py`
  - Scan-Rate: `ros2 topic hz /scan` — erwartet ~7-8 Hz (360° bei ~5.5 kHz Samplerate)
  - Datenqualitaet: Reichweite 0.15-12 m, Winkelaufloesung ~1°, Rauschen pruefen
  - Statischer TF: `base_link → laser` (180° Yaw, vgl. `full_stack.launch.py`)
  - Akzeptanzkriterium (vorgeschlagen): Scan-Rate >= 5 Hz stabil ueber 5 min
  - Referenz: `amr/pi5/ros2_ws/src/my_bot/launch/full_stack.launch.py`

- [ ] **ESP32-S3 XIAO** (USB-CDC, /dev/ttyACM0)
  - Platform: `espressif32`, Board: `seeed_xiao_esp32s3`, Framework: `arduino`
  - Firmware-Upload: `pio run -t upload` (921600 Baud, `upload_port = /dev/ttyACM0`)
  - micro-ROS-Session: `rmw_uros_ping_agent()` in `setup()`, kein Reconnect
  - Odom-Publish: 20 Hz stabil (AK-14), Paketverlust < 0.1% (AK-15)
  - Watchdog + Failsafe: cmd_vel-Timeout 500 ms (`config.h` Zeile 93)
  - Skripte: `ros2 topic hz /odom` (5 min), `ros2 topic echo /odom --once`
  - Referenz: `amr/esp32_amr_firmware/platformio.ini`, `hardware/docs/umsetzungsanleitung.md`

- [ ] **Hailo-8L AI-Akzelerator** (PCIe M.2 Key M, 13 TOPS)
  - Hardware-Verifikation: `hailortcli fw-control identify` (Firmware-Version)
  - Runtime: `hailort` Treiber und Python-API (`hailo_platform`)
  - Inferenz-Test: Vortrainiertes YOLO-Modell auf Kamera-Stream
  - Anwendungsfall: Echtzeit-Objekterkennung fuer Hindernisse oder KLT-Erkennung
  - Akzeptanzkriterium (vorgeschlagen): >= 10 FPS bei Objekterkennung (640x480)
  - Hinweis: Nicht in bestehender Dokumentation oder Akzeptanzkriterien enthalten

- [ ] **Servo-Steuerung + Kalibrierungs-Erweiterung**
  - Servo-PWM: D8/D9 in `config.h` als Encoder-Phase-B belegt — Servo erfordert alternative Pins oder I2C-PWM-Treiber (PCA9685)
  - Kalibrierungsanleitung erweitern: `hardware/docs/kalibrierung_anleitung.md` um IMU- und Kamera-Abschnitte ergaenzen
  - Validierungsskripte: Fehlende Tests in `amr/scripts/` implementieren (IMU-Test, RPLIDAR-Standalone, Hailo-Benchmark)
  - Entry Points: Neue Skripte in `amr/pi5/ros2_ws/src/my_bot/setup.py` registrieren

### Referenzdokumente

| Dokument | Pfad | Inhalt |
|---|---|---|
| Akzeptanzkriterien (AK-01 bis AK-19) | `hardware/docs/umsetzungsanleitung.md` Anhang A | Vollstaendige Kriterienliste |
| Kalibrierungsprozedur | `hardware/docs/kalibrierung_anleitung.md` | UMBmark, PID, SLAM, Nav, Docking |
| Subsystem-Verifikation | `bachelorarbeit/kapitel/06_2_subsystem_verifikation.md` | Testergebnisse PID, Odom, micro-ROS |
| Validierungskapitel | `bachelorarbeit/kapitel_06_validierung.md` | Gesamtkapitel 6 der Bachelorarbeit |
| Hardware-Setup | `hardware/docs/hardware-setup.md` | Pin-Mapping, Schaltplan, Verkabelung |
| Validierungsskripte | `amr/scripts/` (12 Dateien) | Automatisierte Testausfuehrung |
| Hardware-Parameter | `hardware/config.h` | Single Source of Truth |
