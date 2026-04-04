# 5. Implementierung

Dieses Kapitel beantwortet die Umsetzungsfrage der Arbeit: Wie wurde die in Kapitel 4 entworfene Architektur technisch realisiert, so dass der Fahrkern reproduzierbar arbeitet, sicherheitsrelevante Signale Vorrang erhalten und Bedien- und Leitstandsfunktionen den Kernbetrieb nicht stoeren? Die Darstellung folgt der Roadmap-Struktur und trennt deshalb konsequent zwischen Fahrkern, Sensor- und Sicherheitsbasis, hostseitiger ROS-2-Integration, Sicherheitslogik, Bedien- und Leitstandsebene sowie anschlussfaehigen Erweiterungen fuer intelligente Interaktion.

## 5.1 Hardwareaufbau und elektrische Inbetriebnahme

Die Hardwareimplementierung verfolgt zwei Ziele. Erstens muss der Fahrkern mechanisch und elektrisch so aufgebaut sein, dass Odometrie und Antriebsregelung reproduzierbare Mess- und Stellgroessen erhalten. Zweitens muss die Sensor- und Sicherheitsbasis so angebunden sein, dass sicherheitsnahe Signale unabhaengig von rechenintensiven Host-Funktionen erfasst werden koennen.

### 5.1.1 Chassis, Antrieb und Grundgeometrie

Die mechanische Basis bildet ein Differentialantrieb mit zwei koaxial angeordneten Getriebemotoren und einer frei nachlaufenden Stuetzstruktur. Die praezise Ausrichtung der Motorachsen ist fuer die Odometrie wesentlich, weil eine fehlerhafte Spurbreite systematische Bahnabweichungen verursacht. Die Antriebsraeder wurden deshalb spielfrei auf den Motorwellen montiert. Der verwendete Radradius betraegt

$$
r = 32{,}835\,\mathrm{mm}
$$

Dieser Wert entspricht dem kalibrierten Raddurchmesser von $65{,}67\,\mathrm{mm}$, der aus Bodentests mit Massbandvergleich hervorging (siehe Kapitel 6).

Die Stuetzstruktur wurde so positioniert, dass ein moeglichst grosser Anteil der Fahrzeugmasse auf den angetriebenen Raedern lastet. Diese Massnahme reduziert den Einfluss nicht modellierter Roll- und Schlupfeffekte bei Richtungswechseln.

### 5.1.2 Verdrahtung der Dual-Node-Architektur

Die Low-Level-Ebene wurde mit zwei physisch getrennten XIAO-ESP32-S3-Knoten aufgebaut. Diese Trennung folgt direkt dem Entwurf aus Kapitel 4: Der Drive-Knoten verarbeitet ausschliesslich fahrkritische Funktionen, waehrend der Sensor-Knoten I2C-basierte Peripherie und sicherheitsnahe Signale uebernimmt. Die Verdrahtung bildet diese Zustaendigkeiten eindeutig ab.

Am Drive-Knoten sind die Hall-Encoder mit den Phasen A und B an die Pins D4 und D5 (Phase A) sowie D8 und D9 (Phase B) angeschlossen. Die PWM-Signale fuer den Cytron-MDD3A-Motortreiber liegen im Dual-PWM-Modus an den Pins D0 bis D3 an. Die Signalleitungen der Encoder wurden raeumlich getrennt von den PWM-fuehrenden Motorleitungen verlegt, um kapazitive Einkopplungen der Schaltflanken zu verringern. Die PWM-Frequenz betraegt

$$
f_{\mathrm{PWM}} = 20\,\mathrm{kHz}
$$

Am Sensor-Knoten bindet der I2C-Bus mit SDA auf D4 und SCL auf D5 die MPU6050, den INA260 und den PCA9685 an. Ein MH-B-Kanten-Sensor ist direkt an einen digitalen GPIO-Pin angeschlossen. Diese Aufteilung vermeidet, dass I2C-Zugriffe den Fahrkern blockieren.

### 5.1.3 Host-nahe Peripherie

Der Raspberry Pi 5 bindet die hostseitigen Komponenten fuer Lokalisierung und Kartierung, Navigation, Bedien- und Leitstandsebene sowie spaetere Interaktion an. Der RPLIDAR A1 ist per USB angeschlossen und liefert die Distanzdaten fuer Kartenaufbau und Navigation. Die Scan-Frequenz ist auf $7{,}0\,\mathrm{Hz}$ konfiguriert; gemessen wurden $7{,}7$ bis $7{,}8\,\mathrm{Hz}$ (Messprotokoll Phase 3, T3.1/T3.2). Eine frontseitig montierte Sony-IMX296-Kamera ist ueber CSI angebunden. Fuer hardwarebeschleunigte Bildverarbeitung wurde ein Hailo-8L-Beschleuniger ueber ein M.2-HAT integriert. Der Audiopfad nutzt einen MAX98357A-Verstaerker als Ausgabestufe.

Diese Peripherie liegt bewusst ausserhalb des Low-Level-Regelpfads. Damit bleiben Kamera, Vision und Audio anschlussfaehig, ohne die Zykluszeit der Motorregelung direkt zu beeinflussen.

### 5.1.4 Spannungsversorgung und Massekonzept

Die Spannungsversorgung trennt Rechenlast, Logik und Leistungspfad. Der Raspberry Pi 5 wird ueber einen Step-Down-Regler mit

$$
U = 5\,\mathrm{V}
$$

versorgt. Die beiden ESP32-S3-Knoten beziehen ihre Versorgung ueber USB; die Boards erzeugen die Logikspannung von

$$
U = 3{,}3\,\mathrm{V}
$$

ueber interne Regler. Die Energiequelle ist ein Akkupack aus drei Samsung INR18650-35E (NCA) in 3S1P-Konfiguration mit einer Nennspannung von $10{,}8\,\mathrm{V}$ und einer Kapazitaet von $3.350\,\mathrm{mAh}$. Der Motortreiber schaltet die Akkuspannung direkt auf die Antriebe. Der Leistungsbereich liegt damit im Bereich von

$$
U = 10{,}8\,\mathrm{V}\ \text{bis}\ 12{,}6\,\mathrm{V}
$$

Ein gemeinsamer Sternpunkt fuer die Masse reduziert Ausgleichsstroeme und erschwert Masseschleifen zwischen Host, Mikrocontrollern und Leistungsstufe.

## 5.2 Firmware von Fahrkern sowie Sensor- und Sicherheitsbasis

Die Firmware wurde in zwei getrennten PlatformIO-Projekten umgesetzt. Jedes Projekt laeuft auf einem eigenen ESP32-S3-Knoten und nutzt FreeRTOS zur funktionalen und zeitlichen Partitionierung. Diese Trennung ueberfuehrt die Architekturentscheidung aus Kapitel 4 in lauffaehige Firmware.

### 5.2.1 Drive-Knoten fuer Fahrkern und Odometrie

Der Drive-Knoten realisiert den Fahrkern. Er verarbeitet Encoder-Signale, berechnet Odometrie und setzt freigegebene Geschwindigkeitsvorgaben in PWM-Signale fuer den Motortreiber um. Die Software ist in hardwarenahe und regelungstechnische Komponenten gegliedert, darunter `robot_hal.hpp`, `pid_controller.hpp` und `diff_drive_kinematics.hpp`.

Die Regelaufgabe laeuft auf Core 1 als `controlTask` mit einer Zyklusfrequenz von

$$
f_{\mathrm{ctrl}} = 50\,\mathrm{Hz}
$$

Die Encoder-Impulse werden per Interrupt erfasst. Die kalibrierten Encoder-Werte betragen $\mathrm{ticks\_per\_rev\_left} = 748{,}6$ und $\mathrm{ticks\_per\_rev\_right} = 747{,}2$ Ticks pro Radumdrehung (`config_drive.h`). Die asymmetrische Kalibrierung kompensiert fertigungsbedingte Toleranzen der Hall-Encoder und reduziert systematische Bahnabweichungen. Der Regler nutzt die Parametrierung

$$
K_p = 0{,}4 \qquad K_i = 0{,}1 \qquad K_d = 0{,}0
$$

Zur Glaettung der Drehzahlmessung verwendet der Knoten einen Exponential-Moving-Average-Filter mit

$$
\alpha = 0{,}3
$$

Core 0 betreibt den `rclc_executor`, publiziert Odometrie auf `/odom` mit einer konfigurierten Sollrate von

$$
f_{\mathrm{odom,soll}} = 20\,\mathrm{Hz}
$$

Die gemessene Ist-Rate lag bei $18{,}5$ bis $18{,}8\,\mathrm{Hz}$ (Messprotokoll Phase 3, T3.1/T3.2). Die Abweichung gegenueber dem Sollwert resultiert aus der Ausfuehrungslast des micro-ROS-Executors und der Mutex-Synchronisation mit dem Regelkern. Der Executor empfaengt zudem Geschwindigkeitskommandos ueber `/cmd_vel`. Eine gemeinsam genutzte Datenstruktur wird durch einen Mutex geschuetzt, damit Regelkern und Kommunikationskern konsistente Zustaende verarbeiten.

### 5.2.2 Sensor-Knoten fuer I2C-Peripherie und sicherheitsnahe Signale

Der Sensor-Knoten realisiert die Sensor- und Sicherheitsbasis. Er liest IMU, Batterieueberwachung und Kanten-Sensorik aus und stellt die Messgroessen dem ROS-2-System ueber micro-ROS bereit. Die Auslagerung dieser Aufgaben verhindert, dass langsame oder blockierende Sensorzugriffe die Fahrregelung beeintraechtigen.

Die I2C-Abfragen laufen auf Core 1. Da die verwendete Wire-Bibliothek nicht thread-sicher arbeitet, serialisiert ein `i2c_mutex` alle Buszugriffe. Der Timeout betraegt

$$
t_{\mathrm{mutex}} = 5\,\mathrm{ms}
$$

Fuer die Schaetzung der Gierrichtung kombiniert ein Complementary-Filter Gyroskop- und Encoderinformation mit der Gewichtung

$$
98\,\%\ \text{Gyroskop} \qquad \text{und} \qquad 2\,\%\ \text{Encoder}
$$

Core 0 publiziert IMU-Daten auf `/imu` mit einer Sollfrequenz von

$$
f_{\mathrm{imu,soll}} = 50\,\mathrm{Hz}
$$

Die tatsaechlich erreichte Frequenz betraegt aufgrund von I2C-Bus-Contention etwa $33\,\mathrm{Hz}$.

Batteriedaten auf `/battery` mit

$$
f_{\mathrm{battery}} = 2\,\mathrm{Hz}
$$

und den Kantenstatus auf `/cliff` mit

$$
f_{\mathrm{cliff}} = 20\,\mathrm{Hz}
$$

Aktorkommandos, etwa fuer Servos, werden nicht direkt im Kommunikations-Callback ausgefuehrt. Stattdessen nutzt der Knoten ein Deferred-Pattern: Der Callback schreibt nur den Sollzustand in den Arbeitsspeicher, die eigentliche I2C-Ausgabe erfolgt in der regulaeren Ablaufsteuerung. Dieses Muster reduziert Jitter und vermeidet blockierende Buszugriffe im Callback-Kontext.

Der Ultraschallsensor HC-SR04 nutzt eine ISR-basierte, nicht blockierende Messung. Eine Interrupt-Service-Routine auf dem Echo-Pin erfasst die Laufzeit ueber GPIO-Register-Zugriffe. Das Trigger-Echo-Pattern ersetzt das blockierende `pulseIn()` und gibt die Rechenzeit des Sensor-Tasks fuer IMU-Abfragen frei. Die Entfernungsdaten erscheinen auf `/range/front` mit einer konfigurierten Sollrate von $10\,\mathrm{Hz}$.

## 5.3 Hostseitige ROS-2-Integration

Die hostseitige Software laeuft auf dem Raspberry Pi 5 mit ROS 2 Humble in einer Container-Umgebung. Diese Ebene buendelt Lokalisierung und Kartierung, Navigation, Benutzeroberflaeche, Sicherheitslogik und vorbereitete Interaktionsfunktionen. Die Implementierung haelt damit die Trennung zwischen Low-Level-Regelung und rechenintensiver Verarbeitung aus dem Systementwurf ein.

### 5.3.1 micro-ROS-Anbindung der Low-Level-Knoten

Die beiden ESP32-S3-Knoten sind nicht als proprietaere Peripherie gekoppelt, sondern als micro-ROS-Teilnehmer in den ROS-2-Verbund eingebunden. Zwei getrennte `micro_ros_agent`-Prozesse binden den Drive-Knoten ueber `/dev/amr_drive` und den Sensor-Knoten ueber `/dev/amr_sensor` mit jeweils $921600\,\mathrm{Bd}$ an. Die serielle Kopplung folgt dem in Kapitel 3 begruendeten Ziel, den Regelpfad deterministisch und stoerarm zu halten.

Zusaetzlich synchronisiert `rmw_uros_sync_session(1000)` die Zeitbasis der Mikrocontroller mit der Host-Uhr. Diese Synchronisation ist fuer konsistente Zeitstempel von Odometrie, Sensorik und Transformationsketten erforderlich.

### 5.3.2 CAN-Bus als redundanter Kommunikationspfad

Zusaetzlich zur UART-basierten micro-ROS-Anbindung uebertragen beide ESP32-S3-Knoten ihre Daten parallel ueber einen CAN-Bus mit $1\,\mathrm{Mbit/s}$ (ISO 11898, SN65HVD230-Transceiver). Die CAN-Sends laufen auf Core 1, damit sie unabhaengig vom micro-ROS Agent arbeiten. Der Sensor-Knoten sendet Cliff-Signale (CAN-ID 0x120, 20 Hz) und Unterspannungsereignisse (CAN-ID 0x141) direkt an den Drive-Knoten. Der Drive-Knoten empfaengt diese Frames im Regelungs-Task und setzt bei Schutzausloesung die Sollgeschwindigkeiten auf null. Dieser Pfad arbeitet unabhaengig vom Raspberry Pi und bildet damit einen hardwarenahen Sicherheitspfad. Auf dem Raspberry Pi empfaengt ein optionaler `can_bridge_node` die CAN-Frames via SocketCAN und republiziert sie als ROS-2-Topics.

### 5.3.3 Integration von Lokalisierung und Kartierung sowie Navigation

Die Implementierung bindet LiDAR, Odometrie und IMU in die hostseitige Verarbeitung ein. Auf dieser Grundlage laufen die Knoten fuer Lokalisierung und Kartierung sowie Navigation. Der Host verarbeitet damit genau die Funktionsgruppen, die in der Roadmap den Ebenen „Lokalisierung und Kartierung“ sowie „Navigation“ zugeordnet sind. Die Low-Level-Knoten liefern dafuer Zustandsgroessen und sicherheitsnahe Signale, uebernehmen jedoch keine globale Zielplanung.

Die Aufgabentrennung hat eine klare Folge: Der Host darf Bewegungsziele, Kartenbezug und Pfadverfolgung berechnen, der Fahrkern setzt ausschliesslich freigegebene Sollgroessen um. Damit bleibt die Umsetzungslogik auch bei hoeherer Systemlast stabil.

## 5.4 Sicherheitslogik und Kommandopfad

Die Implementierung enthaelt eine eigene Sicherheitslogik, die regulaere Fahrkommandos ueberstimmen kann. Diese Logik setzt die in der Roadmap geforderte Trennung zwischen Navigation, Bedienung und Schutzreaktion technisch um.

### 5.4.1 Cliff-Sicherheitsmultiplexer

Der `cliff_safety_node` bildet den sicherheitsnahen Multiplexer fuer Kanten- und Hinderniserkennung. Er abonniert `/cliff` sowie `/range/front` und ueberwacht gleichzeitig die eingehenden Fahrkommandos. Erkennt der Sensor-Knoten eine Kante oder unterschreitet die Ultraschall-Distanz $100\,\mathrm{mm}$, unterbricht der Multiplexer den regulaeren Kommandopfad und sendet stattdessen einen Stopp auf das finale Topic `/cmd_vel`. Die Freigabe erfolgt erst bei einer Distanz ueber $140\,\mathrm{mm}$ (Hysterese).

Der sichere Halt entspricht im Ausloesefall der Vorgabe

$$
v = 0\,\mathrm{m/s}
$$

Diese Umsetzung verschiebt die Kantenerkennung bewusst vor regulaere Navigationsentscheidungen. Eine erkannte Kante ist kein normaler Navigationsfehler, sondern ein Schutzereignis mit Vorrang.

### 5.4.2 Freigegebene Kommandokette

Die Implementierung folgt nicht dem Muster direkter Motoransteuerung durch beliebige Eingaben. Stattdessen entsteht der Fahrbefehl aus einer freigegebenen Kommandokette. Autonome Navigation, manuelle Bedienung und spaetere Sprachbefehle bleiben logisch getrennte Eingangsquellen. Erst nach Freigabe darf ein Ziel- oder Moduskommando in einen Fahrbefehl ueberfuehrt werden.

Die zulaessige Kette lautet damit konzeptionell:

$$
\text{Interaktion} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation oder Bedienung} \rightarrow /\text{cmd\_vel} \rightarrow \text{Fahrkern}.
$$

Diese Struktur verhindert, dass eine spaetere Sprachschnittstelle die Sicherheitslogik umgeht. Gleichzeitig bleibt die Bedien- und Leitstandsebene handlungsfaehig, weil sie den Betriebszustand beobachten und freigegebene Kommandos ausloesen kann.

## 5.5 Bedien- und Leitstandsebene

Die Bedien- und Leitstandsebene wurde als eigenstaendiger Implementierungsblock aufgebaut. Sie stellt Telemetrie, Videostream, manuelle Bedienung und Zustandsanzeige bereit und dient damit sowohl dem Betrieb als auch der Diagnose. Diese Ebene greift nicht direkt in die Motorregelung ein, sondern nutzt die definierte Kommandokette.

### 5.5.1 Dashboard-Bruecke und Kommunikationspfade

Das System stellt eine browserbasierte Benutzeroberflaeche auf Basis von Vite und React bereit. Ein massgeschneiderter `dashboard_bridge` verbindet ROS-2-Datenpfade mit der Benutzeroberflaeche. Im Unterschied zu einer generischen `rosbridge_suite` reduziert diese Bruecke den Protokoll-Overhead fuer den konkreten Anwendungsfall.

Die Bruecke kombiniert einen WebSocket-Server fuer Telemetrie auf Port

$$
9090
$$

mit einem HTTP-Endpunkt fuer den MJPEG-Stream auf Port

$$
8082
$$

Die Benutzeroberflaeche ist auf dem Host ueber Port

$$
5173
$$

erreichbar. Diese Aufteilung trennt zustandsarme Telemetrie von bandbreitenintensivem Videostream.

### 5.5.2 Betriebsfunktionen der Benutzeroberflaeche

Die Benutzeroberflaeche visualisiert LiDAR-Daten, Kamerabild, Telemetrie und manuelle Bedienelemente. Damit bildet sie die in der Roadmap geforderte Bedien- und Leitstandsebene mit Diagnosefunktion ab. Die manuelle Steuerung erfolgt ueber einen Joystick. Zusaetzlich stehen Zustandsanzeigen zur Verfuegung, die den aktuellen Betriebszustand nachvollziehbar machen.

Ein dreistufiger Deadman-Mechanismus sichert die Teleoperation ab. Die erste Stufe liegt im Browser und sendet beim Loslassen des Joysticks sofort einen Stopp. Die zweite Stufe liegt in der Dashboard-Bruecke und stoppt die Ausgabe bei ausbleibendem WebSocket-Heartbeat nach mehr als

$$
300\,\mathrm{ms}
$$

Die dritte Stufe liegt in der Firmware und greift bei ausbleibenden `cmd_vel`-Nachrichten nach mehr als

$$
500\,\mathrm{ms}
$$

ein. Die drei Stufen wirken nacheinander und erhoehen damit die Robustheit der manuellen Bedienung.

## 5.6 Erweiterungen fuer Vision, Audio und Sprachschnittstelle

Die Ebene der intelligenten Interaktion wurde nur teilweise als Kernfunktion umgesetzt. Realisiert wurden die Kameraanbindung, der hardwarebeschleunigte Vision-Pfad und ein Audiopfad. Die Sprachschnittstelle bleibt als vorbereitete Erweiterung anschlussfaehig, ist jedoch nicht Teil des fahrkritischen Kernpfads.

### 5.6.1 Hybride Vision-Pipeline

Die Vision-Verarbeitung wurde aus dem ROS-Echtzeitgraphen ausgelagert, damit Kartierung, Navigation und Sicherheitslogik nicht durch Bildverarbeitung blockiert werden. Der `v4l2_camera_node` erfasst den Kamerastrom. Die Dashboard-Bruecke stellt daraus einen MJPEG-Stream bereit. Ein nativer Host-Prozess `host_hailo_runner.py` fuehrt die Objekterkennung auf dem Hailo-8L aus und uebertraegt erkannte Begrenzungsrahmen per UDP auf Port

$$
5005
$$

zurueck in die Container-Umgebung.

Zusaetzlich ist eine asynchrone Semantikstufe mit `gemini_semantic_node` vorgesehen. Diese Stufe bleibt bewusst vom Fahrkern entkoppelt und ergaenzt den Wahrnehmungspfad nur oberhalb der Sicherheits- und Freigabelogik.

### 5.6.2 Audioausgabe und vorbereitete Sprachintegration

Der Audiopfad unterstuetzt definierte Rueckmeldungen an die Bedien- und Leitstandsebene. Die Roadmap ordnet zusaetzlich eine Sprachschnittstelle mit ReSpeaker Mic Array v2.0 der Ebene der intelligenten Interaktion zu. Fuer die Projektarbeit ist entscheidend, dass diese Erweiterung architektonisch vorbereitet bleibt: Sprachbefehle duerfen ausschliesslich ueber Intent-Erkennung, Freigabelogik und Missionskommando auf das System wirken.

Damit gilt auch fuer die Erweiterung der Grundsatz, dass Sprachverarbeitung keine direkte Motoransteuerung ausloesen darf. Die spaetere Integrationskette lautet daher:

$$
\text{Sprachbefehl} \rightarrow \text{Intent} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation, Leitstand oder Audio}.
$$

## 5.7 Ergebnis der Implementierung

Die Implementierung ueberfuehrt den Entwurf in eine funktionsfaehige, klar getrennte Systemstruktur. Zwei ESP32-S3-Knoten realisieren Fahrkern sowie Sensor- und Sicherheitsbasis. Der Raspberry Pi 5 buendelt ROS 2, Lokalisierung und Kartierung, Navigation, Sicherheitslogik und die Bedien- und Leitstandsebene. Kamera, Hailo-8L und Audiopfad erweitern das System oberhalb des fahrkritischen Kerns. Damit liegt eine Implementierung vor, die die Roadmap-Themen in eine konsistente technische Gesamtstruktur ueberfuehrt und die spaetere Validierung gezielt vorbereitet.
