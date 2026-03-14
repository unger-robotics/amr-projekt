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
* **Kriterium:** Die generierte Karte zeigt nach dem Loop Closure keine doppelten Wandlinien; der TF-Baum publiziert die Transformation `map` nach `odom` mit mindestens 20 Hz.
* **Testfall 2 (ATE):** Autonome Rundfahrt durch den kartierten Raum mit Rueckkehr zum Startpunkt.
* **Kriterium 2:** Der Absolute Trajectory Error (ATE) liegt unter 0,20 m nach einer Rundfahrt ueber einen Raum mit 15 m^2.

## Phase 4: Navigation

**Problem:** Der Roboter bleibt an Hindernissen haengen oder plant ineffiziente Pfade.
**Messgroesse / Modell:** Erfolgsquote der Zielerreichung und Positionstoleranz.

* **Dateien:** `nav2_params.yaml`, `full_stack.launch.py` (mit `use_nav`)
* **ROS-2-Knoten:** `controller_server`, `planner_server`, `amcl`, `bt_navigator`
* **Topics:** `/goal_pose` (Sub), `/nav_cmd_vel` (Pub), `/local_plan` (Pub)
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
