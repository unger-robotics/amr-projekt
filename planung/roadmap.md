# Roadmap

## Terminologie-Norm

| Bevorzugter Begriff          | Verwendung                                                                                       |
|------------------------------|--------------------------------------------------------------------------------------------------|
| Fahrkern                     | Antrieb, Odometrie, Grundbewegung                                                                |
| Sensor- und Sicherheitsbasis | IMU, Cliff-Sensor, Batterie, Ultraschall, sicherheitsnahe Signale                                |
| Lokalisierung und Kartierung | TF, LiDAR, SLAM, Karte, Re-Lokalisierung                                                         |
| Navigation                   | AMCL, Nav2, Zielanfahrt, Recovery-Verhalten                                                      |
| Bedien- und Leitstandsebene  | Dashboard, Telemetrie, Audio, manuelle Bedienung                                                 |
| Sprachschnittstelle          | Audioaufnahme, STT, Intent-Erkennung, TTS                                                        |
| Sicherheitslogik             | übergeordnete Stop-, Freigabe- und Schutzmechanismen                                             |
| Freigabelogik                | Regelwerk, das Kommandos zulässt, blockiert oder umsetzt                                         |
| Missionskommando             | freigegebenes Ziel- oder Moduskommando oberhalb roher Fahrbefehle                                |
| Intent                       | klassifizierte Befehlsabsicht aus der Sprachverarbeitung                                         |
| ROS-2-Knoten                 | fachlicher Begriff im Fließtext                                                                  |
| Topic                        | technischer ROS-2-Begriff                                                                        |
| Launch-Datei                 | technische Startkonfiguration                                                                    |
| Benutzeroberfläche           | statt gemischter Schreibweisen wie UI, Web-UI oder Frontend, sofern kein Produktname gemeint ist |

---

## 1. Zielbild

Das AMR gliedert sich in drei Ebenen.

### Ebene A – Fahrkern

Der Fahrkern muss lokalisieren, planen, fahren, stoppen und Fehler behandeln.
Diese Ebene umfasst Odometrie, IMU, LiDAR, SLAM, Nav2, die Sicherheitslogik für Kanten sowie die verteilte Architektur aus ESP32-S3 und Raspberry Pi 5.

### Ebene B – Bedien- und Leitstandsebene

Die Bedien- und Leitstandsebene umfasst Dashboard, Telemetrie, manuelle Kommandos und Audio-Rückmeldungen.
Vorhanden sind bereits ein WebSocket-/MJPEG-Dashboard sowie die Schnittstellen `/cmd_vel`, `/servo_cmd`, `/hardware_cmd` und `/audio/play`.

### Ebene C – Intelligente Interaktion

Die Ebene der intelligenten Interaktion umfasst Sprachbefehle, semantische Interpretation, Vision und später multimodale Bedienung.
Das ReSpeaker Mic Array v2.0 gehört in diese Ebene. Die Hardware ist bereits als USB-Audio-Eingabe am Raspberry Pi 5 vorgesehen.

## 2. Projektlandkarte mit Phasen

### Phase 1 – Fahrplattform quantitativ schließen

#### Ziel

Die Grundfahrt muss messbar stabil arbeiten, bevor zusätzliche Systemkomplexität folgt.

#### Module

* Drive-ESP32 mit PID-Regelung
* Encoder und Odometrie
* Cytron MDD3A
* grundlegende `cmd_vel`-Kette vom Raspberry Pi über micro-ROS zum ESP32-S3

#### Hardware

* JGA25-370
* Encoder
* Cytron MDD3A
* XIAO ESP32-S3 Nummer 1

#### Software

* Firmware des Drive-Knotens
* micro-ROS Agent
* Odometrie-Publisher `/odom`

#### Lernziele

* Differentialkinematik
* PID-Regelung
* Deadzone, Sättigung und Schlupf
* messbasierte Bewertung

#### Definition of Done

* Geradeausfahrt über $1\,\mathrm{m}$ mit kleinem Seitenfehler
* Rotation um $360^\circ$ mit reproduzierbarem Winkelfehler
* kein ungewolltes Nachlaufen nach dem Stopp
* mehrfache Wiederholung bei gleichem Ladezustand des Akkus

#### Ergebnis

Die Phase liefert einen charakterisierten Fahrkern.

### Phase 2 – Sensor- und Sicherheitsbasis schließen

#### Ziel

Pose und Nahbereichserfassung müssen ausreichend zuverlässig arbeiten, damit Lokalisierung und Kartierung sowie Navigation belastbar werden.

#### Module

* IMU
* Ultraschall
* Cliff-Sensor
* Batterieüberwachung
* Sensor-ESP32

#### Hardware

* MPU6050
* HC-SR04
* MH-B
* INA260
* XIAO ESP32-S3 Nummer 2

#### Software

* `/imu`
* `/range/front`
* `/cliff`
* `/battery`
* `battery_shutdown`

#### Lernziele

* Sensordrift
* Bias und Kalibrierung
* Messrate und Latenz
* Priorisierung sicherheitsrelevanter Signale

#### Definition of Done

* IMU-Drehung stimmt mit einer Referenzfahrt plausibel überein
* Kanten-Erkennung stoppt reproduzierbar
* Unterspannungsreaktion funktioniert
* Front-Ultraschall löst sauber aus, ohne dauerhafte Fehltrigger

#### Ergebnis

Die Phase liefert eine belastbare Sensor- und Sicherheitsbasis.

### Phase 3 – TF, LiDAR und SLAM in der Wohnung reproduzierbar machen

#### Ziel

Der Roboter muss eine Umgebungskarte erzeugen und sich in dieser Karte wiederfinden.

#### Module

* RPLIDAR A1
* TF-Baum
* `slam_toolbox`
* `odom_to_tf`
* statische Sensortransformationen

#### Hardware

* RPLIDAR A1 am Raspberry Pi 5 über USB

#### Software

* `/scan`
* `/tf`
* `/tf_static`
* `slam_toolbox`
* Kartenauflösung von $5\,\mathrm{cm}$

#### Lernziele

* Koordinatensysteme
* Extrinsik
* Scan-Matching
* Drift und Korrektur

#### Definition of Done

* wiederholbare Karten im selben Raum
* erkennbare Wände und Möbel ohne ausgeprägte Doppelkonturen
* Re-Lokalisierung nach Neustart möglich
* konsistenter TF-Baum ohne Sprünge

#### Ergebnis

Die Phase liefert Lokalisierung und Kartierung für den Innenraum.

### Phase 4 – Navigation mit klarer Missionslogik

#### Ziel

Das System soll nicht nur Karten erzeugen, sondern Ziele sicher anfahren.

#### Module

* Nav2
* AMCL
* Regulated Pure Pursuit
* Recovery-Verhalten
* Cliff-Sicherheitsmultiplexer

#### Software

* `full_stack.launch.py`
* `nav2_params.yaml`
* `cliff_safety_node`
* `/nav_cmd_vel`
* `/dashboard_cmd_vel`
* `/cmd_vel`

#### Lernziele

* globaler Pfad und lokale Bahnverfolgung
* Recovery-Verhalten
* sicherer Zustand
* Missionslogik statt Einzelreaktion

#### Definition of Done

* 10 definierte Zielanfahrten in der Wohnung
* keine Kollision
* Stopp bei Kante oder Hindernis
* nachvollziehbares Recovery bei blockiertem Weg
* dokumentierter Zielradius und dokumentierte Fehlfahrten

#### Ergebnis

Die Phase liefert autonome Mobilität auf Kartenbasis.

### Phase 5 – Bedien- und Leitstandsebene als Betriebswerkzeug

#### Ziel

Das System muss beobachtbar und bedienbar sein.

#### Module

* Dashboard
* WebSocket
* MJPEG
* Joystick
* Zustandsanzeige
* Hardware-Slider
* Audio-Rückmeldung

#### Software

* `dashboard_bridge`
* React-/Vite-Benutzeroberfläche
* `/servo_cmd`
* `/hardware_cmd`
* `/audio/play`
* `audio_feedback_node`

#### Lernziele

* Gestaltung technischer Benutzeroberflächen
* Betriebsdiagnose
* Trennung von Bedienung und Fahrlogik
* Leitstandkonzept aus Fahrzeug- und Robotikentwicklung

#### Definition of Done

* stabile Telemetrie
* saubere Browser-Bedienung
* definierte Audio-Rückmeldungen für wichtige Zustände
* manuelle Eingriffe ohne unklare Systemzustände

#### Ergebnis

Die Phase liefert eine Bedien- und Leitstandsebene mit Diagnosefunktion.

## 3. Erweiterung: Sprachschnittstelle mit ReSpeaker Mic Array v2.0

Sprachsteuerung ersetzt weder Navigation noch Sicherheitslogik.
Die Sprachschnittstelle bildet eine Bedienebene, die Befehle in freigegebene Missionskommandos übersetzt.

Nicht zulässig ist die Kette:

> Sprachbefehl → direkte Motoransteuerung

Zulässig ist die Kette:

> Sprachbefehl → Intent → Freigabelogik → Missionskommando → Navigation / Leitstand / Audio

### 3.1 Teilarchitektur der Sprachschnittstelle

#### Hardware

* ReSpeaker Mic Array v2.0 als USB-Audio-Eingabe am Raspberry Pi 5
* MAX98357A und Lautsprecher als Audio-Ausgabe

#### Software-Module

**1. `voice_input_node`**
liest das ReSpeaker-Mikrofon ein und verarbeitet Pegel, Wake-Word oder Push-to-Talk.

**2. `speech_to_text_node`**
wandelt Audiodaten in Text um.

**3. `voice_intent_node`**
ordnet den Text einer klaren Befehlsabsicht zu.

**4. `voice_command_mux`**
gibt nur freigegebene Kommandos frei und übersetzt sie in ROS-2-Aktionen oder Topics.

**5. `text_to_speech_node`**
gibt Rückmeldungen aus, direkt per TTS oder über `/audio/play`.

### 3.2 Befehlsgruppen

#### Klasse A – sichere Sofortkommandos

* „Stopp“
* „Halt“
* „Notstopp“
* „Sprache aus“

Diese Kommandos dürfen ausschließlich einen sicheren Halt auslösen.

#### Klasse B – Betriebsmodus

* „Manuell“
* „Autonom“
* „Docking starten“
* „Mapping starten“
* „Navigation abbrechen“

Diese Kommandos ändern den Betriebsmodus, senden aber keine direkten Geschwindigkeitswerte an den Antrieb.

#### Klasse C – Missionskommandos

* „Fahre zur Ladestation“
* „Fahre zum Wohnzimmerpunkt“
* „Starte Rundfahrt“

Diese Kommandos übersetzt das System in Zielpunkte oder Aktionen.

#### Klasse D – Informationskommandos

* „Wie ist der Akkustand?“
* „Was sieht die Kamera?“
* „Wo befindet sich der Roboter?“
* „Ist die Navigation aktiv?“

Diese Kommandos unterstützen die Bedien- und Leitstandsebene bei geringem Risiko.

### 3.3 Grenzen der Sprachschnittstelle

Nicht direkt freigeben:

* rohe Geschwindigkeitsbefehle
* unbestätigte Rückwärtsfahrt
* Servo-Bewegungen ohne Kontext
* sicherheitskritische Overrides
* Deaktivierung der Kanten-Erkennung per Sprache

## 4. Neue Phase 6 – Sprachschnittstelle integrieren

#### Ziel

Der Roboter soll natürlich bedienbar werden, ohne die Kernarchitektur aufzuweichen.

#### Module

* ReSpeaker Mic Array v2.0
* Audioaufnahme
* Speech-to-Text
* Intent-Parser
* Befehlsmultiplexer
* Audio-Antwort

#### Hardware

* ReSpeaker Mic Array v2.0
* MAX98357A
* Lautsprecher

#### Software-Zuordnung

**Host / Raspberry Pi 5**

* Audioaufnahme
* Wake-Word
* Speech-to-Text
* Intent-Erkennung
* Text-to-Speech

**ROS-2-Container**

* `voice_intent_node`
* `voice_command_mux`
* Übergabe an Navigation, Leitstand und Audio

**ESP32-S3**

* keine direkte Sprachverarbeitung
* nur Ausführung freigegebener Kommandos

#### Lernziele

* Sprachschnittstellen im Robotiksystem
* Entkopplung von Bedienebene und Fahrfunktion
* Ereignisverarbeitung
* sichere Freigabelogik
* Multimodalität aus Sprache, Dashboard und Autonomie

#### Definition of Done

* Wake-Word oder Push-to-Talk arbeitet stabil
* definierter Wortschatz mit etwa 10 bis 20 Befehlen
* „Stopp“ wird priorisiert und zuverlässig erkannt
* Missionskommandos werden korrekt in ROS-2-Aktionen übersetzt
* Audio-Rückmeldung bestätigt jeden angenommenen Befehl
* Fehlinterpretationen führen zu keiner unsicheren Bewegung

#### Ergebnis

Die Phase erweitert das AMR zu einem interaktiven MINT-System mit natürlicher Bedienung.
