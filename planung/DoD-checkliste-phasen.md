# Definition of Done – Checkliste fuer den Entwurf und die Eigenschaftsabsicherung (Phasen 1 bis 6)

## Phase 1: Entwurf und Eigenschaftsabsicherung Fahrkern (F01)

**Problem:** Unkalibrierte Motoren erzeugen asymmetrische Fahrbewegungen und verfaelschen die Odometrie.
**Messgroesse / Modell:** Encoder-Ticks der Raeder und berechnete Pose ueber der Zeit.

* **Dateien:** `mcu_firmware/drive_node/src/main.cpp`, `full_stack.launch.py`
* **ROS-2-Knoten:** `micro_ros_agent_drive` (ESP32 publiziert via micro-ROS Agent)
* **Topics:** `/cmd_vel` (Sub), `/odom` (Pub)
* **Testfall 1 (Geradeausfahrt):** Skript `straight_drive_test corrected`. Fahrt ueber 1 m auf hartem Boden.
* **Kriterium 1:** Seitenabweichung (Lateraldrift) am Zielpunkt kleiner als 5 cm UND Heading-Fehler kleiner als 5 Grad bei aktiver IMU-Fusion.
* **Testfall 2 (Rotation):** Skript `rotation_test` (360 Grad). Rotation um die Hochachse.
* **Kriterium 2:** Winkelfehler nach dem Stopp kleiner als 5 Grad.

## Phase 2: Entwurf und Eigenschaftsabsicherung Sensor- und Sicherheitsbasis (F02)

**Problem:** Sensor- oder Versorgungsausfaelle koennen unkontrolliertes Verhalten ausloesen. Schlechte Sensordaten verhindern Navigation.
**Messgroesse / Modell:** Latenz, Drift, Signalrate und Messabweichungen der Sensoren.

* **Dateien:** `mcu_firmware/sensor_node/src/main.cpp`, `full_stack.launch.py` + `scripts/cliff_safety_node.py`
* **ROS-2-Knoten:** `micro_ros_agent_sensor`, `cliff_safety_node`
* **Topics:** `/imu` (Pub), `/cliff` (Pub), `/battery` (Pub), `/range/front` (Pub)
* **Testfall 1 (Cliff-Safety Latenz):** Skript `cliff_latency_test`. Ausloesen des Kanten-Sensors waehrend der Vorwaertsfahrt mit 0.2 m/s.
* **Kriterium 1:** Die Motoren stoppen in weniger als 50 ms nach Signaleingang; der Sicherheitsknoten ueberschreibt `/cmd_vel` mit einem Nullvektor.
* **Testfall 2 (IMU-Rotation):** Skript `rotation_test 90`. Motorgetriebene Drehung um 90 Grad.
* **Kriterium 2:** Das integrierte IMU-Signal weicht hoechstens um 2 Grad von der physischen Referenz ab.
* **Testfall 3 (Ultraschall-Suite):** Skript `sensor_test`. Messung an festem Hindernis in 23 cm Entfernung.
* **Kriterium 3:** Publikationsrate >= 7.0 Hz, Abweichung der Genauigkeit (Soll/Ist) < 5.0 %.
* **Testfall 4 (IMU-Suite Drift):** Skript `imu_test`. Erfassung bei absolutem Stillstand (60 s).
* **Kriterium 4:** Publikationsrate >= 15 Hz, Gyro-Drift < 1.0 deg/min, Accel-Bias < 0.6 m/s^2.

## Phase 3: Lokalisierung und Kartierung

**Problem:** Fehlerhafte Extrinsik-Kalibrierung oder unsauberes Scan-Matching erzeugen Kartendrift.
**Messgroesse / Modell:** Konsistenz der erzeugten Belegungskarte und TF-Frequenz.

* **Dateien:** `full_stack.launch.py`, `mapper_params_online_async.yaml`
* **ROS-2-Knoten:** `rplidar_node`, `slam_toolbox`, `odom_to_tf`
* **Topics:** `/scan` (Pub), `/tf`, `/tf_static`, `/map` (Pub)
* **Testfall:** Manuelle Rundfahrt durch einen Raum mit 15 m^2 und Rueckkehr zum Startpunkt fuer einen Loop-Closure-Test.
* **Kriterium:** Die generierte Karte zeigt nach dem Loop Closure keine doppelten Wandlinien; der TF-Baum publiziert die Transformation `map` nach `odom` mit mindestens 1,5 Hz.
* **Testfall 2 (ATE):** Autonome Rundfahrt durch den kartierten Raum mit Rueckkehr zum Startpunkt.
* **Kriterium 2:** Der Absolute Trajectory Error (ATE) liegt unter 0,20 m nach einer Rundfahrt ueber einen Raum mit 15 m^2.

## Phase 4: Navigation

**Problem:** Der Roboter bleibt an Hindernissen haengen oder plant ineffiziente Pfade.
**Messgroesse / Modell:** Erfolgsquote der Zielerreichung und Positionstoleranz.

* **Dateien:** `nav2_params.yaml`, `full_stack.launch.py` (mit `use_nav`)
* **ROS-2-Knoten:** `controller_server` (Regulated Pure Pursuit), `planner_server` (NavFn), `bt_navigator`, `velocity_smoother`; Lokalisierung ueber `slam_toolbox` (kein `amcl`)
* **Topics:** `/goal_pose` (Sub), `/nav_cmd_vel` (Pub), `/plan` (Pub), `/lookahead_point` (Pub)
* **Testfall:** Skript `nav_test`. Vorgabe von Wegpunkten innerhalb der kartierten Wohnung.
* **Kriterium:** Die Ziele werden ohne physische Kollision erreicht; die Endposition liegt innerhalb eines Radius von 10 cm um die Zielkoordinate; der Gierfehler betraegt weniger als 8,6 Grad (0,15 rad).
* **Testfall 2 (ArUco-Docking):** Skript `docking_test`. Zehn aufeinanderfolgende Docking-Versuche an der ArUco-Ladestation.
* **Kriterium 2:** Erfolgsquote >= 80 %, lateraler Versatz < 2 cm.

ArUco-Marker <chev.me/arucogen>

Minimalstruktur Konfigurationsvorlage (YAML)

```yaml
# aruco_params.yaml
aruco_node:
  ros__parameters:
    marker_size: 0.1
    aruco_dictionary_id: "DICT_4X4_50"
    image_topic: "/camera/image_raw"
    camera_info_topic: "/camera/camera_info"
    camera_frame: "camera_color_optical_frame"
```


## Phase 5: Bedien- und Leitstandsebene

**Problem:** Fehlende Transparenz ueber den internen Zustand erschwert die Fehlersuche.
**Messgroesse / Modell:** Systemlatenz der Benutzeroberflaeche und Vollstaendigkeit der Telemetrie.

* **Dateien:** `full_stack.launch.py` (mit `use_dashboard`), `dashboard/src/App.tsx`
* **ROS-2-Knoten:** `dashboard_bridge`, `audio_feedback_node`
* **Topics:** `/dashboard_cmd_vel` (Pub), `/audio/play` (Sub)
* **Testfall:** Eingabe eines manuellen Fahrbefehls ueber das Browser-Dashboard.
* **Kriterium:** Die Latenz zwischen Klick im Browser und Motoranlauf, sichtbar im Topic `/cmd_vel`, liegt unter 100 ms.

## Phase 6: Sprachschnittstelle

**Problem:** Sprachbefehle koennten faelschlich als rohe Fahrbefehle interpretiert werden und Kollisionen ausloesen.
**Messgroesse / Modell:** Zuordnungsgenauigkeit der Intents und Einhaltung der Freigabelogik.

* **Dateien:** `voice_pipeline.launch.py`, `intent_config.yaml`
* **ROS-2-Knoten:** `voice_input_node`, `speech_to_text_node`, `voice_intent_node`, `voice_command_mux`
* **Topics:** `/voice/audio_raw`, `/voice/text`, `/voice/intent`, `/cmd_vel_mux/voice`
* **Testfall 1:** Sprachbefehl "Notstopp" waehrend einer aktiven Nav2-Fahrt.
* **Kriterium 1:** Der Intent wird erkannt, und der `voice_command_mux` stoppt die Fahrt in weniger als 500 ms, ohne dass der Nav2-Controller den Stopp ueberschreiben kann.
* **Testfall 2:** Sprachbefehl "Fahre zur Ladestation".
* **Kriterium 2:** Der Intent triggert eine ROS-2-Aktion fuer Nav2, sendet aber keine direkten PWM- oder Geschwindigkeitswerte an den Drive-Knoten.

---

# Definition of Done – Ausbaupakete K0 bis K10

Die Ausbaupakete sind **keine** Projektphasen. Die Phasen 1 bis 6 oben bilden
den Lernpfad ab und bleiben unveraendert. Die folgenden Abschnitte gehoeren zur
technischen Erweiterung und werden getrennt gefuehrt.

## Ausbaupakete K2 bis K6: Steuergeraetearchitektur und CAN-Betriebsbus

**Problem:** Der Fahrbefehl laeuft ueber einen einzigen seriellen Pfad. Faellt er aus, gibt es keine zweite Quelle; die dokumentierte Rueckfallebene ueber CAN existiert im Code nicht.
**Messgroesse / Modell:** Frameraten, Frameverlust, Buslast, Transportgleichheit, Latenz des Fahrbefehls und Verhalten beim Moduswechsel.

* **Dateien:** `hardware/can-bus/` (Signaldatenbank), `amr/scripts/vehicle_gateway_node.py`, `mcu_firmware/drive_node/src/main.cpp`, `mcu_firmware/sensor_node/src/main.cpp`, `full_stack.launch.py`
* **ROS-2-Knoten:** `vehicle_gateway_node`, `cliff_safety_node`
* **Topics:** `/cmd_vel` (Sub), `/can/health` (Pub), `/can/mode_state` (Pub), `/imu` `/cliff` `/range/front` `/battery` (Pub im CAN-Betriebsmodus)
* **Testfall 1 (Signalkonsistenz, K2):** Skript `can_dbc_check`. Abgleich von Signaldatenbank, abgeleiteten Firmware-Konstanten und Pi-seitiger Dekodierung ohne Hardwarezugriff.
* **Kriterium 1:** 0 Abweichungen; eine Abweichung bricht den Uebersetzungslauf der Firmware (SA-10).
* **Testfall 2 (Uebertragungsguete, K3):** Skript `can_bus_load_test --duration 120`. Passives Mithoeren am Bus.
* **Kriterium 2:** Buslast hoechstens 30 Prozent, Frameverlust je Signal hoechstens 1 Prozent, Jitter hoechstens 20 Prozent der Nominalperiode, CAN-Zustand durchgehend ERROR-ACTIVE (NFA-13, NFA-15, NFA-19).
* **Testfall 3 (Transportgleichheit, K3 und K4):** Skript `can_shadow_test --duration 120` im Modus CAN_SHADOW. Vergleich zeitlich zugeordneter Wertepaare aus CAN und Referenzpfad.
* **Kriterium 3:** Signale mit float32-Uebertragung sind wertgleich (Abweichung 0, da beide Pfade dieselbe Gleitkommazahl fuehren); quantisierte Signale weichen um hoechstens eine Quantisierungsstufe ab; der Zeitversatz zwischen den Pfaden bleibt innerhalb der Vorgabe (NFA-16, NFA-20).
* **Testfall 4 (Fahrbefehl ueber CAN, K4):** Skript `can_cmd_latency_test`. 100 Sollwertspruenge bei aufgebocktem Fahrzeug mit freien Raedern, Modus CAN_SHADOW.
* **Kriterium 4:** Sendefrequenz 50 Hz mit hoechstens 10 Prozent Abweichung, Latenz bis zur Stellgroesse hoechstens 40 ms im 95-Prozent-Quantil, im Modus CAN_SHADOW ohne jede Wirkung auf den Stellpfad (SA-11, NFA-14).
* **Testfall 5 (Betriebsmodi und Zeitueberwachung, K5):** Skript `can_mode_test`. Nacheinander: Timeout der aktiven Quelle im Modus SERIAL_REFERENCE, expliziter Wechsel nach CAN_PRIMARY, Timeout der aktiven Quelle dort, Ausbleiben des Kantensignals, Notstopp ueber CAN, Betrieb ohne angeschlossenen CAN-Bus.
* **Kriterium 5:** Zu jedem Zeitpunkt ist genau eine Fahrbefehlsquelle aktiv; ein Timeout der aktiven Quelle fuehrt innerhalb von 300 ms in den sicheren Stillstand und **nicht** zu einem selbsttaetigen Quellenwechsel; ein Quellenwechsel erfolgt ausschliesslich durch expliziten Moduswechsel; Sperrung der Vorwaertsfahrt innerhalb von 200 ms nach Ausbleiben des Kantensignals; Notstopp in weniger als 50 ms; ohne angeschlossenen CAN-Bus unveraendertes Verhalten (SIA-11 bis SIA-14, NFA-18).
* **Testfall 6 (Betriebsumstellung, K6):** Skript `nav_square_test` im Modus CAN_PRIMARY, anschliessend Rueckkehr nach SERIAL_REFERENCE allein ueber den Startparameter.
* **Kriterium 6:** Genau ein Knoten haelt den Buszugriff; die Zielgenauigkeit aus Phase 4 wird reproduziert; der Moduswechsel gelingt ohne Neubau und ohne Flashvorgang (SA-12, SA-16, SIA-16).

**Freigabe-Gate:** Testfall 2 muss vor Beginn des Ausbaupakets K4 bestanden sein. Die in der Baseline gemessenen Abweichungen BA-01 und BA-02 sind zuvor zu klaeren (OP-10).

## Ausbaupakete K7 bis K9: Funktionskette automatisiertes Fahren

**Problem:** Wahrnehmung, Umfeldverstaendnis und Bahnfuehrung sind heute nicht als getrennte, einzeln pruefbare Stufen aufgebaut. Fehler lassen sich keinem Kettenglied zuordnen.
**Messgroesse / Modell:** Publikationsraten der Kettenglieder, Konstanz der Objektverfolgung, Praediktionsfehler gegen eine Referenztrajektorie, Umschaltzeit der Verhaltensentscheidung und Latenz der Gesamtkette.

* **Dateien:** `amr/pi5/ros2_ws/src/amr_msgs/`, `amr/scripts/sensor_preprocessing_node.py`, `amr/scripts/environment_model_node.py`, `amr/scripts/prediction_node.py`, `amr/scripts/behavior_node.py`, `amr/scripts/trajectory_planner_node.py`
* **ROS-2-Knoten:** `sensor_preprocessing_node`, `environment_model_node`, `prediction_node`, `behavior_node`, `trajectory_planner_node`
* **Topics:** `/perception/clusters` (Pub), `/environment/objects` (Pub), `/prediction/trajectories` (Pub), `/behavior/state` (Pub), `/trajectory/planned` (Pub)
* **Testfall 1 (Umfeldmodell, K8):** Skript `environment_model_test --duration 120`. Statisches Objekt in 1,0 m, danach ein zweites Objekt seitlich, danach eine langsam querende Person.
* **Kriterium 1:** Publikationsrate mindestens 5 Hz; die Verfolgungskennung des statischen Objekts bleibt ueber 5 s zu mindestens 90 Prozent konstant; zwei getrennte Objekte erzeugen zwei Eintraege; der Zeitstempelversatz der fusionierten Quellen betraegt hoechstens 50 ms (FA-18, FA-19, SA-14).
* **Testfall 2 (Praediktion, K9):** Skript `prediction_test`. Ein Objekt bewegt sich auf einer vermessenen Referenztrajektorie mit bekannter, konstanter Geschwindigkeit. Die vorhergesagten Positionen werden gegen die Referenztrajektorie ausgewertet.
* **Kriterium 2:** Prognosehorizont mindestens 2 s; Positionsfehler nach 1 s hoechstens 0,25 m; der Fehler wird ueber mindestens 30 Vorhersagen als Mittelwert und 95-Prozent-Quantil ausgewiesen (FA-20).
* **Testfall 3 (Verhaltensentscheidung, K9):** Skript `behavior_test`. Statisches Hindernis auf dem Pfad, danach eine querende Person, danach Ausloesen des Kantensensors.
* **Kriterium 3:** Die Verhaltensentscheidung wechselt den Zustand in hoechstens 200 ms; auf dem Fahrbefehls-Topic des Fahrkerns publiziert weiterhin ausschliesslich die Sicherheitslogik (FA-21, SIA-15).
* **Testfall 4 (Trajektorienplanung und Gesamtkette, K9):** Skript `trajectory_test` ueber mindestens 100 Zyklen, anschliessend `nav_square_test` als Regressionsnachweis.
* **Kriterium 4:** Planungsrate mindestens 2 Hz, keine Kollision bei zehn Zielanfahrten, Ende-zu-Ende-Latenz von der Sensorzeitmarke bis zur Solltrajektorie hoechstens 200 ms im 95-Prozent-Quantil, Zielgenauigkeit aus Phase 4 reproduziert (FA-22, NFA-17).
* **Testfall 5 (Zweistufigkeit der Regelung, K9):** Auswertung der Regelraten beider Stufen waehrend einer Zielanfahrt.
* **Kriterium 5:** Die Fahrzeugbewegungsregelung auf dem Pi 5 und die Raddrehzahlregelung mit 50 Hz auf dem Fahrkern sind getrennt belegt; nach Ausbleiben des Fahrzeug-Sollwerts geht der Fahrkern innerhalb des Failsafe-Timeouts in den Stillstand (SIA-17).

## Ausbaupakete K7 und K10: Radar

**Problem:** Die Umfelderfassung stuetzt sich auf LiDAR, Ultraschall und Kamera. Eine Sensorart mit direkter Geschwindigkeitsmessung fehlt, und die Schnittstelle dafuer ist nicht vorbereitet.
**Messgroesse / Modell:** Publikationsrate der Zielliste, Entfernungsfehler, Geschwindigkeitsmessung und Fusionsverhalten im Umfeldmodell.

* **Dateien:** `amr/scripts/radar_node.py`, `amr/pi5/ros2_ws/src/amr_msgs/msg/`, `amr/scripts/environment_model_node.py`, `hardware/docs/radar-bgt60tr13c.md`
* **ROS-2-Knoten:** `radar_node`, `environment_model_node`
* **Topics:** `/radar/targets` (Pub), `/environment/objects` (Pub), Transformation `base_link` nach `radar_link`
* **Testfall 1 (Abstraktion und Simulationsmodus, K7):** Skript `radar_sim_test`. Betrieb ohne Radarhardware.
* **Kriterium 1:** Publikationsrate mindestens 10 Hz; die Transformation `base_link` nach `radar_link` ist vorhanden; simulierte Ziele erscheinen im Umfeldmodell mit gesetzter Radarquelle; die Betriebsart Hardware bricht ohne Geraet mit verstaendlicher Meldung ab, ohne andere Knoten zu beeintraechtigen; auf dem CAN-Bus erscheinen keine Radardaten (SA-13, SA-18, FA-23).
* **Testfall 2 (reale Anbindung, K10):** Skript `radar_hardware_test`. Reflektor in 0,5 m, 1,0 m und 2,0 m, danach ein Ziel mit bekannter Radialgeschwindigkeit.
* **Kriterium 2:** Publikationsrate mindestens 10 Hz ueber SPI3; Entfernungsfehler kleiner als 5 cm im Bereich von 0,5 bis 2,0 m; Radardetektion und LiDAR-Cluster desselben Objekts ergeben eine gemeinsame Verfolgungskennung; der Simulationsmodus bleibt funktionsfaehig (SA-17, FA-23).
