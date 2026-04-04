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
| Sicherheitslogik             | uebergeordnete Stop-, Freigabe- und Schutzmechanismen                                            |
| Freigabelogik                | Regelwerk, das Kommandos zulaesst, blockiert oder umsetzt                                        |
| Missionskommando             | freigegebenes Ziel- oder Moduskommando oberhalb roher Fahrbefehle                                |
| Intent                       | klassifizierte Befehlsabsicht aus der Sprachverarbeitung                                         |
| ROS-2-Knoten                 | fachlicher Begriff im Fliesstext                                                                 |
| Topic                        | technischer ROS-2-Begriff                                                                        |
| Launch-Datei                 | technische Startkonfiguration                                                                    |
| Benutzeroberflaeche          | statt gemischter Schreibweisen wie UI, Web-UI oder Frontend, sofern kein Produktname gemeint ist |

---

## 1. Systementwurf und Zielbild

Das AMR gliedert sich gemaess Systementwurf in drei Ebenen.

### Ebene A – Fahrkern sowie Sensor- und Sicherheitsbasis

Der Fahrkern muss fahren, stoppen und Fehler behandeln.
Diese Ebene umfasst Odometrie, IMU, die Sicherheitslogik fuer Kanten sowie die verteilte Architektur aus ESP32-S3 und Raspberry Pi 5. LiDAR (RPLIDAR A1) ist direkt am Pi 5 angeschlossen. SLAM und Nav2 laufen auf dem Pi 5 im Docker-Container (Ebene A).

### Ebene B – Bedien- und Leitstandsebene

Die Bedien- und Leitstandsebene umfasst Dashboard, Telemetrie, manuelle Kommandos und Audio-Rueckmeldungen.
Vorhanden sind bereits ein WebSocket-/MJPEG-Dashboard sowie die Schnittstellen `/cmd_vel`, `/servo_cmd`, `/hardware_cmd` und `/audio/play`.

### Ebene C – Intelligente Interaktion

Die Ebene der intelligenten Interaktion umfasst Sprachbefehle, semantische Interpretation, Vision und spaeter multimodale Bedienung.
Das ReSpeaker Mic Array v2.0 gehoert in diese Ebene. Die Hardware ist bereits als USB-Audio-Eingabe am Raspberry Pi 5 integriert.

## 2. Projektlandkarte und Integration (VDI 2206)

### Phase 1 – Entwurf und Eigenschaftsabsicherung: Fahrkern (F01)

#### Ziel

Die Grundfahrt muss messbar stabil arbeiten, bevor zusaetzliche Systemkomplexitaet im Rahmen der Integration folgt.

#### Module

* Drive-ESP32 mit PID-Regelung
* Encoder und Odometrie
* Cytron MDD3A
* grundlegende `cmd_vel`-Kette vom Raspberry Pi ueber micro-ROS zum ESP32-S3

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
* Deadzone, Saettigung und Schlupf
* messbasierte Eigenschaftsabsicherung

#### Definition of Done

* Geradeausfahrt ueber 1 m mit Seitenfehler < 5 cm und Heading-Fehler < 5 Grad (mit IMU-Fusion)
* Rotation um 360 Grad mit reproduzierbarem Winkelfehler < 5 Grad
* kein ungewolltes Nachlaufen nach dem Stopp
* mehrfache Wiederholung bei gleichem Ladezustand des Akkus

#### Ergebnis

Die Phase liefert einen quantitativ charakterisierten Fahrkern.

### Phase 2 – Entwurf und Eigenschaftsabsicherung: Sensor- und Sicherheitsbasis (F02)

#### Ziel

Pose und Nahbereichserfassung muessen ausreichend zuverlaessig arbeiten, damit Lokalisierung und Kartierung sowie Navigation belastbar werden.

#### Module

* IMU
* Ultraschall
* Cliff-Sensor
* Batterieueberwachung
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
* Priorisierung sicherheitsrelevanter Signale gemaess funktionaler Anforderungsdefinition

#### Definition of Done

* IMU-Drehung stimmt mit einer Referenzfahrt plausibel ueberein (Fehler < 2 Grad)
* Kanten-Erkennung stoppt reproduzierbar (Latenz < 50 ms)
* Ultraschall arbeitet innerhalb der Genauigkeitstoleranz (< 5 % Fehler)
* Unterspannungsreaktion funktioniert

#### Ergebnis

Die Phase liefert eine belastbare Sensor- und Sicherheitsbasis.

### Phase 3 – Lokalisierung und Kartierung

#### Ziel

Der Roboter muss eine Umgebungskarte erzeugen und sich in dieser Karte wiederfinden.

#### Module

* RPLIDAR A1
* TF-Baum
* `slam_toolbox`
* `odom_to_tf`
* statische Sensortransformationen

#### Hardware

* RPLIDAR A1 am Raspberry Pi 5 ueber USB

#### Software

* `/scan`
* `/tf`
* `/tf_static`
* `slam_toolbox`
* Kartenaufloesung von 5 cm

#### Lernziele

* Koordinatensysteme
* Extrinsik
* Scan-Matching
* Drift und Korrektur

#### Definition of Done

* wiederholbare Karten im selben Raum
* erkennbare Waende und Moebel ohne ausgepraegte Doppelkonturen
* Re-Lokalisierung nach Neustart moeglich
* konsistenter TF-Baum ohne Spruenge

#### Ergebnis

Die Phase liefert Lokalisierung und Kartierung fuer den Innenraum.

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

Die Phase liefert autonome Mobilitaet auf Kartenbasis.

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
* Audio-Rueckmeldung

#### Software

* `dashboard_bridge`
* React-/Vite-Benutzeroberflaeche
* `/servo_cmd`
* `/hardware_cmd`
* `/audio/play`
* `audio_feedback_node`

#### Lernziele

* Gestaltung technischer Benutzeroberflaechen
* Betriebsdiagnose
* Trennung von Bedienung und Fahrlogik
* Leitstandkonzept aus Fahrzeug- und Robotikentwicklung

#### Definition of Done

* stabile Telemetrie
* saubere Browser-Bedienung
* definierte Audio-Rueckmeldungen fuer wichtige Zustaende
* manuelle Eingriffe ohne unklare Systemzustaende

#### Ergebnis

Die Phase liefert eine Bedien- und Leitstandsebene mit Diagnosefunktion.

## 3. Erweiterung: Sprachschnittstelle mit ReSpeaker Mic Array v2.0

Sprachsteuerung ersetzt weder Navigation noch Sicherheitslogik.
Die Sprachschnittstelle bildet eine Bedienebene, die Befehle in freigegebene Missionskommandos uebersetzt.

Nicht zulaessig ist die Kette:

> Sprachbefehl → direkte Motoransteuerung

Zulaessig ist die Kette:

> Sprachbefehl → Intent → Freigabelogik → Missionskommando → Navigation / Leitstand / Audio

### 3.1 Teilarchitektur der Sprachschnittstelle

#### Hardware

* ReSpeaker Mic Array v2.0 als USB-Audio-Eingabe am Raspberry Pi 5
* MAX98357A I2S-Verstaerker und Lautsprecher als Audio-Ausgabe

#### Software-Module (geplante Architektur)

Die folgenden Module beschreiben die geplante Zielarchitektur. Die aktuelle Implementierung konsolidiert die Module 1 bis 4 in `voice_command_node` (ReSpeaker VAD + Gemini Audio-STT Cloud primaer / faster-whisper STT lokal als Offline-Fallback + Regex-Intent-Parser, optional Wake-Word via openwakeword) und Modul 5 in `tts_speak_node`.

**1. `voice_input_node`** (geplant, derzeit in `voice_command_node` integriert)
liest das ReSpeaker-Mikrofon ein und verarbeitet Pegel, Wake-Word oder Push-to-Talk.

**2. `speech_to_text_node`** (geplant, derzeit in `voice_command_node` integriert)
wandelt Audiodaten in Text um.

**3. `voice_intent_node`** (geplant, derzeit in `voice_command_node` integriert)
ordnet den Text einer klaren Befehlsabsicht zu.

**4. `voice_command_mux`** (geplant, derzeit in `voice_command_node` integriert)
gibt nur freigegebene Kommandos frei und uebersetzt sie in ROS-2-Aktionen oder Topics.

**5. `text_to_speech_node`** (implementiert als `tts_speak_node`)
gibt Rueckmeldungen aus, direkt per TTS oder ueber `/audio/play`.

### 3.2 Befehlsgruppen

#### Klasse A – sichere Sofortkommandos

* "Stopp"
* "Halt"
* "Notstopp"
* "Sprache aus"

Diese Kommandos duerfen ausschliesslich einen sicheren Halt ausloesen.

#### Klasse B – Betriebsmodus

* "Manuell"
* "Autonom"
* "Docking starten"
* "Mapping starten"
* "Navigation abbrechen"

Diese Kommandos aendern den Betriebsmodus, senden aber keine direkten Geschwindigkeitswerte an den Antrieb.

#### Klasse C – Missionskommandos

* "Fahre zur Ladestation"
* "Fahre zum Wohnzimmerpunkt"
* "Starte Rundfahrt"

Diese Kommandos uebersetzt das System in Zielpunkte oder Aktionen.

#### Klasse D – Informationskommandos

* "Wie ist der Akkustand?"
* "Was sieht die Kamera?"
* "Wo befindet sich der Roboter?"
* "Ist die Navigation aktiv?"

Diese Kommandos unterstuetzen die Bedien- und Leitstandsebene bei geringem Risiko.

### 3.3 Grenzen der Sprachschnittstelle

Nicht direkt freigeben:

* rohe Geschwindigkeitsbefehle
* unbestaetigte Rueckwaertsfahrt
* Servo-Bewegungen ohne Kontext
* sicherheitskritische Overrides
* Deaktivierung der Kanten-Erkennung per Sprache

## 4. Phase 6 – Sprachschnittstelle integrieren

#### Ziel

Der Roboter soll natuerlich bedienbar werden, ohne die Kernarchitektur aufzuweichen.

#### Module

* ReSpeaker Mic Array v2.0
* Audioaufnahme
* Speech-to-Text
* Intent-Parser
* Befehlsmultiplexer
* Audio-Antwort

#### Hardware

* ReSpeaker Mic Array v2.0
* MAX98357A I2S-Verstaerker
* Lautsprecher

#### Software-Zuordnung

**Host / Raspberry Pi 5**

* Audioaufnahme
* Wake-Word
* Speech-to-Text
* Intent-Erkennung
* Text-to-Speech

**ROS-2-Container**

* `voice_command_node` (implementiert: ReSpeaker VAD + Gemini Audio-STT Cloud primaer / faster-whisper STT lokal Fallback + Regex-Intent-Parser, publiziert `/voice/command` und `/voice/text`, GEMINI_API_KEY fuer Cloud-STT)
* `tts_speak_node` (implementiert: Gemini-TTS-Sprachausgabe ueber MAX98357A)
* `voice_intent_node` (geplant, derzeit in `voice_command_node` integriert)
* `voice_command_mux` (geplant, derzeit in `voice_command_node` integriert)
* Uebergabe an Navigation, Leitstand und Audio

**ESP32-S3**

* keine direkte Sprachverarbeitung
* nur Ausfuehrung freigegebener Kommandos

#### Lernziele

* Sprachschnittstellen im Robotiksystem
* Entkopplung von Bedienebene und Fahrfunktion
* Ereignisverarbeitung
* sichere Freigabelogik
* Multimodalitaet aus Sprache, Dashboard und Autonomie

#### Definition of Done

* Wake-Word oder Push-to-Talk arbeitet stabil
* definierter Wortschatz mit etwa 10 bis 20 Befehlen
* "Stopp" wird priorisiert und zuverlaessig erkannt
* Missionskommandos werden korrekt in ROS-2-Aktionen uebersetzt
* Audio-Rueckmeldung bestaetigt jeden angenommenen Befehl
* Fehlinterpretationen fuehren zu keiner unsicheren Bewegung

#### Ergebnis

Die Phase erweitert das AMR zu einem interaktiven MINT-System mit natuerlicher Bedienung.
