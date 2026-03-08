# Definition of Done – Checkliste für die Phasen 1 bis 6

## Phase 1: Fahrplattform quantitativ schließen

**Problem:** Unkalibrierte Motoren erzeugen asymmetrische Fahrbewegungen und verfälschen die Odometrie.
**Messgröße / Modell:** Encoder-Ticks der Räder und berechnete Pose über der Zeit.

* **Dateien:** `mcu_firmware/drive_node/src/main.cpp`, `full_stack.launch.py`
* **ROS-2-Knoten:** `micro_ros_agent_drive` (ESP32 publiziert via micro-ROS Agent), `teleop_twist_keyboard` für Tests
* **Topics:** `/cmd_vel` (Sub), `/odom` (Pub)
* **Testfall 1:** Geradeausfahrt über $1\,\mathrm{m}$ auf hartem Boden per Kommando
* **Kriterium 1:** Seitenabweichung am Zielpunkt kleiner als $5\,\mathrm{cm}$
* **Testfall 2:** Rotation um $360^\circ$ um die Hochachse
* **Kriterium 2:** Winkelfehler nach dem Stopp kleiner als $5^\circ$

## Phase 2: Sensor- und Sicherheitsbasis

**Problem:** Sensor- oder Versorgungsausfälle können unkontrolliertes Verhalten auslösen.
**Messgröße / Modell:** Latenz zwischen Sensortrigger und Motorstopp.

* **Dateien:** `mcu_firmware/sensor_node/src/main.cpp`, `full_stack.launch.py` (mit `use_cliff_safety`) + `scripts/cliff_safety_node.py`
* **ROS-2-Knoten:** `micro_ros_agent_sensor` (ESP32 publiziert via micro-ROS Agent), `cliff_safety_node`
* **Topics:** `/imu` (Pub), `/cliff` (Pub), `/battery` (Pub, `sensor_msgs/BatteryState`), `/range/front` (Pub)
* **Testfall 1:** Auslösen des Kanten-Sensors während der Vorwärtsfahrt mit $0{,}2\,\mathrm{m/s}$
* **Kriterium 1:** Die Motoren stoppen in weniger als $50\,\mathrm{ms}$ nach Signaleingang; der Sicherheitsknoten überschreibt `/cmd_vel` mit einem Nullvektor
* **Testfall 2:** IMU-Gierratenmessung bei einer manuellen Drehung um $90^\circ$
* **Kriterium 2:** Das integrierte IMU-Signal weicht höchstens um $2^\circ$ von der physischen Referenz ab

## Phase 3: Lokalisierung und Kartierung

**Problem:** Fehlerhafte Extrinsik-Kalibrierung oder unsauberes Scan-Matching erzeugen Kartendrift.
**Messgröße / Modell:** Konsistenz der erzeugten Belegungskarte und TF-Frequenz.

* **Dateien:** `full_stack.launch.py`, `mapper_params_online_async.yaml`
* **ROS-2-Knoten:** `rplidar_node`, `slam_toolbox`, `odom_to_tf`
* **Topics:** `/scan` (Pub), `/tf`, `/tf_static`, `/map` (Pub)
* **Testfall:** Manuelle Rundfahrt durch einen Raum mit $15\,\mathrm{m^2}$ und Rückkehr zum Startpunkt für einen Loop-Closure-Test
* **Kriterium:** Die generierte Karte zeigt nach dem Loop Closure keine doppelten Wandlinien; der TF-Baum publiziert die Transformation `map` nach `odom` mit mindestens $20\,\mathrm{Hz}$

## Phase 4: Navigation

**Problem:** Der Roboter bleibt an Hindernissen hängen oder plant ineffiziente Pfade.
**Messgröße / Modell:** Erfolgsquote der Zielerreichung und Positionstoleranz.

* **Dateien:** `nav2_params.yaml`, `full_stack.launch.py` (mit `use_nav`)
* **ROS-2-Knoten:** `controller_server`, `planner_server`, `amcl`, `bt_navigator`
* **Topics:** `/goal_pose` (Sub), `/nav_cmd_vel` (Pub), `/local_plan` (Pub)
* **Testfall:** Vorgabe von 10 verschiedenen Zielen innerhalb der kartierten Wohnung
* **Kriterium:** 10 von 10 Zielen werden ohne physische Kollision erreicht; die Endposition liegt innerhalb eines Radius von $10\,\mathrm{cm}$ um die Zielkoordinate

## Phase 5: Bedien- und Leitstandsebene

**Problem:** Fehlende Transparenz über den internen Zustand erschwert die Fehlersuche.
**Messgröße / Modell:** Systemlatenz der Benutzeroberfläche und Vollständigkeit der Telemetrie.

* **Dateien:** `full_stack.launch.py` (mit `use_dashboard`), `dashboard/src/App.tsx`
* **ROS-2-Knoten:** `dashboard_bridge`, `audio_feedback_node`
* **Topics:** `/dashboard_cmd_vel` (Pub), `/audio/play` (Sub)
* **Testfall:** Eingabe eines manuellen Fahrbefehls über das Browser-Dashboard
* **Kriterium:** Die Latenz zwischen Klick im Browser und Motoranlauf, sichtbar im Topic `/cmd_vel`, liegt unter $100\,\mathrm{ms}$

## Phase 6: Sprachschnittstelle

**Problem:** Sprachbefehle könnten fälschlich als rohe Fahrbefehle interpretiert werden und Kollisionen auslösen.
**Messgröße / Modell:** Zuordnungsgenauigkeit der Intents und Einhaltung der Freigabelogik.

* **Dateien:** `voice_pipeline.launch.py`, `intent_config.yaml`
* **ROS-2-Knoten:** `voice_input_node`, `speech_to_text_node`, `voice_intent_node`, `voice_command_mux`
* **Topics:** `/voice/audio_raw`, `/voice/text`, `/voice/intent`, `/cmd_vel_mux/voice`
* **Testfall 1:** Sprachbefehl „Notstopp“ während einer aktiven Nav2-Fahrt
* **Kriterium 1:** Der Intent wird erkannt, und der `voice_command_mux` stoppt die Fahrt in weniger als $500\,\mathrm{ms}$, ohne dass der Nav2-Controller den Stopp überschreiben kann
* **Testfall 2:** Sprachbefehl „Fahre zur Ladestation“
* **Kriterium 2:** Der Intent triggert eine ROS-2-Aktion für Nav2, sendet aber keine direkten PWM- oder Geschwindigkeitswerte an den Drive-Knoten
