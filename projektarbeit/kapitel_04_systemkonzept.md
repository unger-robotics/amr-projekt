# 4. Systemkonzept und Entwurf

Dieses Kapitel beantwortet die Entwurfsfrage der Arbeit: Wie laesst sich ein Innenraum-AMR fuer Kartierung, Zielanfahrt und sichere Bedienung so strukturieren, dass der Fahrkern reproduzierbar arbeitet, sicherheitsrelevante Signale Vorrang erhalten und spaetere Erweiterungen wie Vision oder Sprachschnittstelle anschlussfaehig bleiben? Die Darstellung ueberfuehrt die Anforderungen aus Kapitel 3 in eine konkrete Zielarchitektur. Im Mittelpunkt stehen die Konzeptauswahl, die funktionale Partitionierung, die Daten- und Kommandokette sowie die Einordnung von Lokalisierung und Kartierung, Navigation, Bedien- und Leitstandsebene und intelligenter Interaktion.

## 4.1 Entwurfsziele und Auswahlkriterien

Das Systemkonzept folgt vier Entwurfszielen. Erstens muss der Fahrkern zeitlich stabil arbeiten, damit Geschwindigkeitsvorgaben reproduzierbar in Bewegung umgesetzt werden. Zweitens muss die Sensor- und Sicherheitsbasis sicherheitsnahe Signale priorisieren, damit eine erkannte Kante oder ein kritischer Betriebszustand eine sofortige Schutzreaktion ausloesen kann. Drittens muss die Architektur Funktionen sauber trennen, damit Kartierung, Navigation, Telemetrie und Audio die hardwarenahe Regelung nicht stoeren. Viertens muss die Struktur spaetere Erweiterungen aufnehmen, ohne die Kernlogik des Fahrkerns umzubauen.

Aus diesen Zielen ergeben sich die Auswahlkriterien fuer den Entwurf:

| Kriterium                        | Bedeutung fuer den Entwurf                                                                                                 |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Determinismus                    | Der Fahrkern muss Sollwerte und Messwerte mit konstanter Zykluszeit verarbeiten.                                          |
| Priorisierte Sicherheitsreaktion | Sicherheitslogik und Freigabelogik muessen Fahrkommandos ueberstimmen koennen.                                               |
| Modulare Struktur                | Fahrkern, Sensor- und Sicherheitsbasis, Lokalisierung und Kartierung, Navigation sowie Bedienung muessen getrennt bleiben. |
| Innenraumeignung                 | Kinematik, Sensorik und Navigation muessen fuer enge Raeume, Kurven und variable Hindernisse geeignet sein.                  |
| Erweiterbarkeit                  | Benutzeroberflaeche, Audio, Vision und Sprachschnittstelle muessen anschliessbar bleiben.                                    |

Diese Kriterien verschieben die Entwurfsentscheidung bewusst weg von maximaler Rechenleistung oder maximaler Funktionsvielfalt. Vorrang erhalten stattdessen klare Zustaendigkeiten, stabile Datenpfade und nachvollziehbare Zustandsuebergaenge.

## 4.2 Konzeptauswahl

Der morphologische Kasten reduziert den Variantenraum auf die Teilfunktionen, die den Systemcharakter am staerksten praegen. Die ausgewaehlte Loesung erfuellt die Anforderungen des Innenraum-AMR mit dem geringsten Integrationsrisiko.

| Teilfunktion                 | Alternative A                                            | Alternative B                 | Alternative C     |
|------------------------------|----------------------------------------------------------|-------------------------------|-------------------|
| Host-Recheneinheit           | **Raspberry Pi 5 mit optionalem Hailo-8L-Beschleuniger** | Jetson Nano                   | Intel NUC         |
| Low-Level-Steuerung          | **2 x ESP32-S3**                                         | 1 x ESP32-S3                  | STM32F767ZI       |
| Kommunikation Host-Low-Level | **micro-ROS ueber UART**                                  | USB mit proprietaerer Kopplung | WLAN ueber UDP     |
| Antriebskonzept              | **Differentialantrieb**                                  | Mecanum-Antrieb               | Ackermann-Lenkung |
| Lokalisierung und Kartierung | **SLAM Toolbox**                                         | Cartographer                  | GMapping          |
| Lokaler Navigationsregler    | **Regulated Pure Pursuit**                               | Dynamic Window Approach       | MPPI              |

Die Wahl des Raspberry Pi 5 folgt der Anforderung, ROS 2, LiDAR, Kartierung, Navigation, Benutzeroberflaeche und Audio auf einer einzigen Host-Plattform zusammenzufuehren. Ein zusaetzlicher Hailo-8L-Beschleuniger bleibt als Erweiterung fuer Vision-Aufgaben moeglich, ist jedoch nicht Voraussetzung fuer den Kernbetrieb. Der Host bildet damit die Rechenbasis fuer Lokalisierung und Kartierung, Navigation sowie Bedien- und Leitstandsebene.

Die Aufteilung der Low-Level-Ebene auf zwei ESP32-S3 ist die zentrale Entwurfsentscheidung. Der Drive-Knoten uebernimmt ausschliesslich Fahrkern und Odometrie. Der Sensor-Knoten uebernimmt I2C-basierte Sensorik, Batterieueberwachung und sicherheitsnahe Signale. Diese physische Trennung senkt das Risiko, dass blockierende Sensorzugriffe oder langsame Peripherieoperationen die Motorregelung stoeren.

Fuer die Kommunikation zwischen Host und Low-Level-Ebene wurde micro-ROS ueber UART gewaehlt. Die serielle Kopplung reduziert den Integrationsaufwand, erlaubt eine direkte Einbindung der Mikrocontroller in das ROS-2-System und vermeidet die zusaetzliche Unsicherheit einer drahtlosen Uebertragung im Regelpfad.

Zusaetzlich verbindet ein CAN-Bus mit $1\,\mathrm{Mbit/s}$ (ISO 11898, SN65HVD230-Transceiver) die beiden ESP32-S3-Knoten direkt miteinander. Dieser Dual-Path erlaubt sicherheitsrelevante Signale wie Cliff-Erkennung und Unterspannungsabschaltung unabhaengig vom Host und micro-ROS Agent zu uebertragen. Der CAN-Bus bildet damit einen redundanten Sicherheitspfad neben der UART-basierten micro-ROS-Kommunikation.

Der Differentialantrieb ist fuer enge Innenraeume die zweckmaessige Wahl. Das Konzept benoetigt wenig mechanische Komplexitaet, unterstuetzt Rotation auf engem Raum und laesst sich mit ueberschaubarem Rechenaufwand modellieren. Mecanum- und Ackermann-Konzepte wuerden den mechanischen und regelungstechnischen Aufwand erhoehen, ohne fuer die Zielumgebung einen zwingenden Vorteil zu liefern.

Fuer Lokalisierung und Kartierung wurde die SLAM Toolbox gewaehlt, weil sie Kartenaufbau und Re-Lokalisierung in einer ROS-2-nahen Toolchain abbildet. Fuer die lokale Bahnverfolgung wurde Regulated Pure Pursuit gewaehlt, weil das Verfahren kinematisch einfache Plattformen gut unterstuetzt und Geschwindigkeiten in Kurven oder bei Hindernisannaeherung begrenzen kann.

## 4.3 Zielarchitektur des Gesamtsystems

Das Zielbild folgt der Roadmap mit drei Ebenen. Die Ebenen trennen fahrkritische Funktionen, Betriebsfunktionen und intelligente Interaktion.

| Ebene                                                 | Hauptfunktionen                                                                              | Zentrale Recheneinheit                      |
|-------------------------------------------------------|----------------------------------------------------------------------------------------------|---------------------------------------------|
| Ebene A – Fahrkern sowie Sensor- und Sicherheitsbasis | Antrieb, Odometrie, IMU, Ultraschall, Cliff-Sensor, Batterieueberwachung, Servo-Steuerung, LED-Statusanzeige, Sicherheitsreaktion | 2 x ESP32-S3 und Raspberry Pi 5             |
| Ebene B – Bedien- und Leitstandsebene                 | Benutzeroberflaeche, Telemetrie, manuelle Kommandos, Videostream, Audio-Rueckmeldungen         | Raspberry Pi 5                              |
| Ebene C – Intelligente Interaktion                    | Sprachschnittstelle, semantische Interpretation, Vision, spaetere multimodale Bedienung       | Raspberry Pi 5 mit optionalem Beschleuniger |

Die physische Ausfuehrung ordnet den Ebenen feste Komponenten zu. Der Raspberry Pi 5 traegt die hostseitigen ROS-2-Knoten fuer Lokalisierung und Kartierung, Navigation, Benutzeroberflaeche, Audio und spaetere Interaktionsfunktionen. Ein ESP32-S3 bildet den Drive-Knoten des Fahrkerns. Ein weiterer ESP32-S3 bildet den Sensor-Knoten der Sensor- und Sicherheitsbasis. LiDAR, Kamera und Audio-Hardware sind an den Host angebunden.

Die Architektur trennt nicht nur Hardware, sondern auch Verantwortlichkeiten. Der Fahrkern setzt freigegebene Fahrvorgaben um. Die Sensor- und Sicherheitsbasis liefert Zustaende und Schutzsignale. Lokalisierung und Kartierung sowie Navigation berechnen Bewegungsziele auf Kartenbasis. Die Bedien- und Leitstandsebene beobachtet und bedient das System. Die Sprachschnittstelle bleibt eine Interaktionsschicht oberhalb der Freigabelogik.

## 4.4 Mechanisches und elektronisches Konzept

Das mechanische Konzept basiert auf einem Differentialantrieb mit zwei angetriebenen Raedern und einer frei laufenden Stuetzstruktur. Der Aufbau unterstuetzt enge Kurvenradien und Richtungswechsel auf engem Raum. Fuer den Prototyp sind ein Raddurchmesser von $65{,}67\,\mathrm{mm}$ und eine kalibrierte Spurbreite von $178\,\mathrm{mm}$ vorgesehen. Diese Groessen gehen direkt in Kinematik, Odometrie und spaetere Kalibrierung ein.

Die Antriebseinheit nutzt JGA25-370-Motoren mit Encoder-Rueckfuehrung. Die Leistungsstufe bildet ein Cytron-MDD3A-Motortreiber. Die PWM-Frequenz betraegt $20\,\mathrm{kHz}$, um die Ansteuerung oberhalb des gut hoerbaren Bereichs zu betreiben und gleichzeitig eine fein genug aufgeloeste Stellgroesse bereitzustellen.

Die Sensorik folgt der funktionalen Trennung des Gesamtsystems. Encoder erfassen die Radbewegung des Fahrkerns. Eine MPU6050 liefert inertiale Messgroessen. Ein Front-Ultraschallsensor erfasst den Nahbereich. Ein Cliff-Sensor erkennt Kanten. Eine INA260 ueberwacht Spannung und Strom des Energiesystems. I2C-basierte Baugruppen einschliesslich der Servo-Steuerung ueber einen PCA9685-PWM-Treiber liegen vollstaendig auf dem Sensor-Knoten, damit der Fahrkern nicht durch Sensorzugriffe belastet wird.

Zusaetzliche Hardware fuer die Bedien- und Leitstandsebene und die intelligente Interaktion wird bewusst vom Kernpfad getrennt. Eine frontseitige Kamera unterstuetzt Videostream und spaetere Vision-Funktionen. Das ReSpeaker Mic Array v2.0 dient als Audioeingang fuer die Sprachschnittstelle. Ein Lautsprecherpfad ermoeglicht definierte Audio-Rueckmeldungen. Diese Komponenten erweitern die Beobachtbarkeit und Interaktion, ohne die Grundfahrt direkt zu steuern.

## 4.5 Software-Architektur und funktionale Partitionierung

Die Software-Architektur kombiniert ROS 2 auf dem Host mit micro-ROS auf den Mikrocontrollern. Auf dem Raspberry Pi 5 laufen die ROS-2-Knoten fuer Lokalisierung und Kartierung, Navigation, Benutzeroberflaeche, Audio und Schnittstellenlogik. Auf den ESP32-S3 laeuft FreeRTOS als harte Partitionierung der Low-Level-Aufgaben. Damit entsteht eine verteilte Architektur mit klarer Zustaendigkeit pro Knoten.

Der Drive-Knoten verarbeitet ausschliesslich fahrkritische Funktionen. Dazu gehoeren die Umsetzung von Geschwindigkeitsvorgaben, die Encoder-Auswertung, die Odometrie und die Motorregelung mit einem Arbeitstakt von $50\,\mathrm{Hz}$. Die hostseitige Navigation liefert translatorische und rotatorische Sollgroessen, der Drive-Knoten setzt diese ueber das kinematische Modell in Radgroessen um.

Der Sensor-Knoten verarbeitet die Sensor- und Sicherheitsbasis. Er liest IMU, Ultraschall, Batterieueberwachung und Kanten-Erkennung aus und veroeffentlicht die Daten als ROS-2-nahe Informationen ueber micro-ROS. Zusaetzlich liefert er sicherheitsnahe Zustaende an die hostseitige Sicherheitslogik.

Die hostseitige Ebene buendelt Kartenaufbau, Re-Lokalisierung, Zielplanung, Benutzeroberflaeche und Audio. Diese Aufteilung erlaubt eine klare Trennung zwischen hardwarenaher Reaktion und rechenintensiver Verarbeitung. Zugleich vermeidet sie eine proprietaere Nebenarchitektur, weil beide Mikrocontroller als eingebundene ROS-2-Teilnehmer auftreten.

Die Kommandokette bildet ein zentrales Entwurfselement. Sie verhindert, dass Bedienung oder Sprache rohe Motorbefehle direkt in den Fahrkern einspeisen. Zulaessig ist nur eine freigegebene Kette:

$$
\text{Interaktion} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation oder manuelle Bedienung} \rightarrow /\text{cmd\_vel} \rightarrow \text{Fahrkern}
$$

Nicht zulaessig ist eine direkte Kette der Form

$$
\text{Sprachbefehl} \rightarrow \text{direkte Motoransteuerung}
$$

Diese Trennung gibt der Sicherheitslogik und der Freigabelogik einen festen Ort in der Architektur. Ein Stopp-Kommando hat Vorrang vor Fahr- und Missionskommandos. Nicht freigegebene Eingaben werden blockiert oder in einen sicheren Zustand ueberfuehrt.

## 4.6 Datenfluss, Sicherheitslogik und Freigabelogik

Die Daten- und Befehlsfluesse folgen dem Prinzip „Zustand nach oben, Freigabe nach unten“. Sensorwerte, Odometrie und Diagnoseinformationen laufen von den Mikrocontrollern zum Host. Missionskommandos, Zielzustaende und freigegebene Fahrbefehle laufen vom Host zum Fahrkern.

Fuer die Navigation entstehen mindestens drei logisch getrennte Befehlsquellen: autonome Fahrbefehle der Navigation, manuelle Fahrbefehle der Benutzeroberflaeche und Stopp- oder Schutzkommandos der Sicherheitslogik. Die Architektur fuehrt diese Quellen nicht unkontrolliert zusammen, sondern ueber eine Freigabelogik mit eindeutigem Vorrang. Die Sicherheitslogik steht oberhalb der regulaeren Fahrvorgaben. Eine erkannte Kante darf daher eine aktive Zielanfahrt unmittelbar unterbrechen.

Der Cliff-Sicherheitsmultiplexer bildet diese Regel technisch ab. Er blockiert eingehende Fahrbefehle auf dem Topic `/cmd_vel`, sobald der Cliff-Sensor eine Kante erkennt oder die Ultraschall-Distanz unter $80\,\mathrm{mm}$ faellt. Die Freigabe erfolgt erst bei einer Distanz ueber $120\,\mathrm{mm}$ (Hysterese), um ein wiederholtes Umschalten im Grenzbereich zu vermeiden. Intern wird die Blockierung durch die Bedingung `_cliff_detected or _obstacle_too_close` ausgeloest. Das Ergebnis ist kein konkurrierender Fahrkanal, sondern eine uebergeordnete Schutzinstanz. Damit trennt das System bewusst zwischen Navigationsfehlern, die Recovery-Verhalten ausloesen koennen, und Schutzereignissen, die unmittelbar zum Halt fuehren muessen.

Die Freigabelogik regelt zusaetzlich die Uebergaenge zwischen Betriebsarten. Navigation darf nur freigegebene Missionskommandos ausfuehren. Manuelle Eingriffe der Benutzeroberflaeche duerfen den Fahrzustand beeinflussen, aber keine Schutzmechanismen umgehen. Sprachkommandos duerfen nur freigegebene Missionskommandos erzeugen. Dadurch bleibt die gesamte Befehlskette auch bei spaeteren Erweiterungen nachvollziehbar.

## 4.7 Entwurf von Fahrkern, Lokalisierung und Kartierung sowie Navigation

Der Fahrkern arbeitet mit dem kinematischen Modell des Differentialantriebs. Die hostseitige Ebene erzeugt eine Translationsgeschwindigkeit $v$ und eine Drehrate $\omega$. Der Drive-Knoten berechnet daraus die Radsollwerte

$$
\omega_L = \frac{v - \omega \cdot \frac{b}{2}}{r}
$$

$$
\omega_R = \frac{v + \omega \cdot \frac{b}{2}}{r}
$$

mit dem Radradius $r$ und der Spurbreite $b$. Die konkrete Parametrierung der Motorregelung gehoert zur Implementierung und Validierung. Im Systemkonzept reicht die Festlegung, dass der Fahrkern freigegebene Sollgroessen deterministisch und reproduzierbar umsetzen muss.

Fuer Lokalisierung und Kartierung sind zwei Betriebsarten vorgesehen. Im Kartierungsbetrieb erzeugt die SLAM Toolbox aus LiDAR-Daten, Odometrie und Transformationsbeziehungen eine Karte des Innenraums. Im Navigationsbetrieb nutzt das System eine vorhandene Karte, lokalisiert sich darin erneut und faehrt Zielpunkte auf Kartenbasis an. Diese Trennung reduziert Komplexitaet, weil Kartenaufbau und autonome Zielanfahrt nicht dauerhaft denselben Optimierungszustand teilen muessen.

Die Navigation kombiniert globale Pfadplanung mit lokaler Bahnverfolgung. Globale Planer erzeugen eine Route auf Basis der Karte. Der lokale Regler verfolgt diese Route unter Beruecksichtigung der Fahrzeugkinematik. Recovery-Verhalten bleibt Teil der Navigation, etwa bei blockiertem Weg oder unguenstiger Pose. Recovery ersetzt jedoch keine Sicherheitslogik. Eine Kante, ein kritischer Energiezustand oder eine gesperrte Freigabe sind Abbruchkriterien und keine regulaeren Navigationsprobleme.

## 4.8 Bedien- und Leitstandsebene sowie Sprachschnittstelle

Die Bedien- und Leitstandsebene ist kein Nebenprodukt des Entwurfs, sondern ein eigenes Systemelement. Sie stellt Telemetrie, Zustandsanzeige, Videostream, manuelle Kommandos und Audio-Rueckmeldungen bereit. Damit unterstuetzt sie Diagnose, Versuchsdurchfuehrung und den sicheren Betrieb. Die Benutzeroberflaeche dient folglich nicht nur der Interaktion, sondern auch der Beobachtbarkeit des Systems.

Die Sprachschnittstelle wird als Erweiterung der Ebene der intelligenten Interaktion eingeordnet. Das ReSpeaker Mic Array v2.0 liefert Audiodaten an den Host. Nachgelagerte ROS-2-Knoten koennen Sprache in Text, Text in einen Intent und den Intent in ein freigegebenes Missionskommando ueberfuehren. Die Sprachschnittstelle bleibt damit oberhalb von Freigabelogik und Missionskommando. Sie ergaenzt die Benutzeroberflaeche, ersetzt aber weder Navigation noch Sicherheitslogik.

Die daraus entstehende Kette lautet:

$$
\text{Sprachbefehl} \rightarrow \text{Intent} \rightarrow \text{Freigabelogik} \rightarrow \text{Missionskommando} \rightarrow \text{Navigation, Leitstand oder Audio}
$$

Durch diese Einordnung laesst sich die Sprachschnittstelle in die Projektarbeit aufnehmen, ohne den Kernnachweis des Fahr- und Navigationssystems zu verwaessern.

## 4.9 Ergebnis des Systementwurfs

Der Entwurf ueberfuehrt die Anforderungen des Innenraum-AMR in eine klar gegliederte Zielarchitektur. Die Dual-Node-Struktur trennt Fahrkern und Sensor- und Sicherheitsbasis. Der Raspberry Pi 5 buendelt Lokalisierung und Kartierung, Navigation, Benutzeroberflaeche und spaetere Interaktionsfunktionen. Sicherheitslogik und Freigabelogik sichern die Kommandokette gegen unkontrollierte Eingriffe. Damit liegt ein Systemkonzept vor, das den Kernbetrieb der Projektarbeit traegt und zugleich Erweiterungen wie Audio, Vision und Sprachschnittstelle geordnet einbindet.
