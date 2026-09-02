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
| Steuergeraet                 | ECU im deutschen Fliesstext; Drive-ECU und Sensor-ECU nur als Eigennamen der Knoten          |
| Fahrzeug-CAN-Gateway         | der eine ROS-2-Knoten, der den gesamten CAN-Zugriff des Pi 5 kapselt                         |
| Betriebsbus                  | der Bus, ueber den im Regelbetrieb Fahr- und Sicherheitssignale laufen                       |
| Referenzpfad                 | der USB-/micro-ROS-Pfad, solange er den Betriebspfad stellt oder als Rueckfall dient         |
| Servicepfad                  | der USB-Pfad nach der Umstellung: Service, Flashen, Fehlersuche                              |
| Sensorvorverarbeitung        | Filterung, Plausibilisierung und Zeitsynchronisation vor der Wahrnehmung                     |
| Umfeldmodell                 | fusionierte Objektliste mit Verfolgungskennung                                               |
| Praediktion                  | Schaetzung kuenftiger Objekttrajektorien                                                     |
| Verhaltensentscheidung       | Wahl des Fahrmanoevers (nicht "Behavior")                                                   |
| Trajektorienplanung          | Erzeugung der Solltrajektorie                                                                |
| Fahrzeugbewegungsregelung    | Stufe 1 der Regelung auf dem Pi 5 (v und omega)                                              |
| Raddrehzahlregelung          | Stufe 2 der Regelung auf dem Fahrkern (PID 50 Hz)                                            |
| Baseline                     | gemessener Referenzzustand, ausdruecklich keine Anforderung                                  |
| Ausbaupaket                  | die Einheiten K0 bis K10 des Ausbaus                                                         |

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

---

## 5. Ausbau zur Kfz-nahen Steuergeraetearchitektur

Die technische Erweiterung wird **nicht** als Projektphase gefuehrt. Die Phasen
1 bis 6 dieser Roadmap bilden den Lernpfad des Projekts ab und bleiben
unveraendert. Der Ausbau ist davon getrennt in **Ausbaupaketen K0 bis K10**
organisiert; die beiden Gliederungen werden nicht vermischt.

Zielzustand: `docs/architecture/zielarchitektur.md`.
Referenzzustand vor dem Ausbau: `planung/baseline_k0_referenzwerte.md`.
Anforderungen und Rueckverfolgbarkeit: `docs/anforderungsliste-L1.md`.

### Uebersicht der Ausbaupakete

| Paket | Gegenstand | Firmware-Flash | Reale Bewegung |
|---|---|---|---|
| K0 | Baseline: Referenzzustand messen und dokumentieren | nein | nein |
| K1 | Anforderungen und Architektur | nein | nein |
| K2 | CAN-Signaldatenbank und Signalentwurf | nein (nur Uebersetzen) | nein |
| K3 | Sensor- und Sicherheitsbasis ueber CAN | nur Sensor-Knoten | nein |
| K4 | Fahrkern-CAN im Parallelbetrieb, ohne Wirkung auf den Stellpfad | Drive-Knoten | nur aufgebockt |
| K5 | Fahrkern-CAN wirksam: Betriebsmodi, Zeitueberwachung, Notstopp | beide Knoten | aufgebockt und Fahrversuch |
| K6 | CAN als Betriebsbus, USB als Servicepfad | nein | Fahrversuch |
| K7 | Schnittstellen der Funktionskette und Radar-Simulator | nein | nein |
| K8 | Sensorvorverarbeitung und Umfeldmodell | nein | langsame Fahrt |
| K9 | Praediktion, Verhaltensentscheidung, Trajektorienplanung | nein | Fahrversuch |
| K10 | Reale Radar-Anbindung ueber SPI3 | nein | Fahrversuch |

### Ausbaupakete K2 bis K6: Steuergeraetearchitektur und CAN-Betriebsbus

#### Ziel

Der CAN-Bus wird vom parallelen Telemetriekanal zum Betriebsbus zwischen dem
Pi 5 und den beiden Steuergeraeten. Der USB-Pfad bleibt als Referenzpfad und
spaeter als Servicepfad jederzeit ohne erneutes Flashen verfuegbar. Jede Stufe
wird zuerst im Parallelbetrieb gegen den Referenzpfad vermessen.

#### Module

* Signaldatenbank als alleinige Quelle der Signaldefinition (K2)
* Anbindung der Sensor- und Sicherheitsbasis ueber CAN (K3)
* Fahrkern-Telemetrie und Kommandopfad ohne Wirkung auf den Stellpfad (K4)
* Betriebsmodi, Zeitueberwachung der aktiven Quelle, Notstopp (K5)
* Fahrzeug-CAN-Gateway, Umstellung des Betriebspfads (K6)

#### Hardware

* vorhandener CAN-Aufbau: MCP2515 mit MCP2562 am Pi 5, zwei SN65HVD230 an den
  Steuergeraeten, Linientopologie mit Abschluss an beiden Enden
* keine neue Hardware erforderlich

#### Software

* Fahrzeug-CAN-Gateway als einziger Knoten mit Buszugriff
* Generator, der Firmware-Konstanten und Pi-seitige Dekodierung aus der
  Signaldatenbank ableitet
* Erweiterung der Firmware beider Steuergeraete um Empfangspfad, Betriebsmodi
  und Zeitueberwachung

#### Lernziele

* Aufbau und Priorisierung eines Fahrzeugbusses
* Trennung von Betriebspfad, Rueckfallebene und Servicezugang
* explizite Betriebsmodi statt impliziter Umschaltautomatik
* Nachweisfuehrung ueber Parallelbetrieb statt ueber Umschaltung ins Blaue

#### Definition of Done

* Signaldatenbank ist alleinige Quelle; Abweichungen brechen den Uebersetzungslauf (SA-10)
* Sensorsignale erreichen den Pi 5 ueber CAN (SA-15)
* Transportgleichheit gegenueber dem Referenzpfad nachgewiesen (NFA-16, NFA-20)
* Frameverlust je Signal hoechstens 1 Prozent und Empfangsfehler geklaert (NFA-19)
* Fahrbefehl erreicht den Fahrkern ueber CAN mit 50 Hz (SA-11, NFA-14)
* Betriebsmodi, Zeitueberwachung, Notstopp und Abschaltframe nachgewiesen (SIA-11 bis SIA-14)
* Umstellung auf den CAN-Betriebsmodus und Rueckkehr zum Referenzmodus ohne Flashen (SA-16, SIA-16)
* Buslast hoechstens 30 Prozent (NFA-13)

#### Ergebnis

Das Fahrzeug besitzt eine Steuergeraetetopologie mit einem Betriebsbus, einem
Gateway und definierten Betriebsmodi mit nachweisbarem Rueckfallweg.

### Ausbaupakete K7 bis K9: Funktionskette automatisiertes Fahren

#### Ziel

Die Kette aus Sensorvorverarbeitung, Wahrnehmung, Lokalisierung, Umfeldmodell,
Praediktion, Verhaltensentscheidung und Trajektorienplanung wird als
durchgaengiger Pfad aufgebaut. Wahrnehmung und Lokalisierung werden nicht neu
gebaut, sondern ueber definierte Schnittstellen eingebunden.

#### Module

* Nachrichtendefinitionen und Kettengeruest (K7)
* Sensorvorverarbeitung und Umfeldmodell (K8)
* Praediktion, Verhaltensentscheidung, Trajektorienplanung (K9)

#### Hardware

* vorhandene Sensorik; keine neue Hardware erforderlich

#### Software

* eigenes Nachrichtenpaket im vorhandenen Arbeitsbereich
* je Kettenglied ein Knoten mit definierten Ein- und Ausgaengen
* Anbindung der Trajektorienplanung an die Fahrzeugbewegungsregelung

#### Lernziele

* Gliederung einer Fahrfunktion in getrennte Verarbeitungsstufen
* Objektverfolgung und Fusion mehrerer Sensorquellen
* Trennung von Manoeverentscheidung und Bahnfuehrung
* Zweistufigkeit der Regelung als Architekturprinzip

#### Definition of Done

* Umfeldmodell liefert eine Objektliste mit stabiler Verfolgungskennung (FA-19, SA-14)
* Praediktion wird eigenstaendig gegen eine bekannte Referenztrajektorie geprueft (FA-20)
* Verhaltensentscheidung und Trajektorienplanung arbeiten durchgaengig (FA-21, FA-22)
* auf dem Fahrbefehls-Topic des Fahrkerns publiziert ausschliesslich die Sicherheitslogik (SIA-15)
* Ende-zu-Ende-Latenz der Kette hoechstens 200 ms (NFA-17)
* Zweistufigkeit der Regelung ist mit beiden Regelraten belegt (SIA-17)
* bestehende Navigationskennwerte werden reproduziert

#### Ergebnis

Das Fahrzeug verfuegt ueber eine nachvollziehbare Funktionskette, deren Glieder
einzeln pruefbar sind.

### Ausbaupakete K7 und K10: Radar

#### Ziel

Die Radar-Schnittstelle wird in K7 ohne Hardware vollstaendig anschlussfaehig
vorbereitet und in K10 mit dem realen Sensor betrieben. Die Abstraktion bleibt
dabei unveraendert; nur die Datenquelle wechselt.

#### Module

* Abstraktionsschnittstelle, Koordinatensystem und Simulationsmodus (K7)
* Treiber ueber SPI3 und Fusion in das Umfeldmodell (K10)

#### Hardware

* BGT60TR13C, direkt am Pi 5 ueber SPI3
* keine Radardaten ueber den CAN-Bus (SA-18)

#### Software

* Treiberknoten mit den Betriebsarten Simulation und Hardware
* Erweiterung des Umfeldmodells um die Radarquelle

#### Lernziele

* Vorbereitung einer Sensorschnittstelle vor der Beschaffung
* Trennung von Abstraktion, Simulation und Treiber
* Fusion von Sensoren mit unterschiedlichen Fehlermodellen

#### Definition of Done

* Simulationsmodus liefert Ziele mit mindestens 10 Hz (SA-13)
* Betriebsart Hardware bricht ohne Geraet verstaendlich ab
* reale Anbindung ueber SPI3 nachgewiesen (SA-17)
* Radarziel und LiDAR-Cluster desselben Objekts ergeben eine gemeinsame Verfolgungskennung (FA-23)
* Simulationsmodus bleibt nach der Hardwareintegration funktionsfaehig

#### Ergebnis

Die Umfelderfassung ist um eine Sensorart erweitert, deren Schnittstelle bereits
vor der Beschaffung nachweisbar war.
