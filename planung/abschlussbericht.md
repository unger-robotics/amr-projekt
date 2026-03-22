# Abschlussbericht: Autonomer mobiler Roboter fuer die Intralogistik

## 1. Einleitung

Wie laesst sich ein autonomer mobiler Roboter (AMR) fuer den Transport von Kleinladungstraegern kostenguenstig und echtzeitfaehig konstruieren? Die Flexibilisierung industrieller Fertigungsprozesse erfordert innerbetriebliche Logistiksysteme, die ohne aeussere Fuehrungsinfrastruktur wie Leitlinien oder Reflektoren navigieren.

Dieser Bericht dokumentiert die Entwicklung eines AMR-Prototypen mit Differentialantrieb. Der Systementwurf kombiniert Open-Source-Software mit einer verteilten Hardwarearchitektur: Zwei dedizierte ESP32-S3-Mikrocontroller steuern den Fahrkern sowie die Sensor- und Sicherheitsbasis. Ein Raspberry Pi 5 uebernimmt die rechenintensiven Aufgaben der Lokalisierung und Kartierung, der Navigation, der Bedien- und Leitstandsebene sowie einer hybriden Vision-Pipeline.

Die Entwicklung adressiert drei Kernfragen:

* **Projektfrage 1 (PF1):** Wie laesst sich eine echtzeitfaehige Antriebsregelung und Sensorerfassung auf einer Dual-Knoten-Architektur realisieren?
* **Projektfrage 2 (PF2):** Welchen Einfluss haben systematische Odometrie-Kalibrierung, IMU-Fusion und hardwarenahe Sicherheitslogik auf die Navigationsgenauigkeit?
* **Projektfrage 3 (PF3):** Erreicht ein monokulares Kamerasystem in Kombination mit Edge-KI und Cloud-Semantik eine ausreichend praezise Umgebungswahrnehmung fuer zentimetergenaues Docking?

## 2. Projektorganisation

Das viermonatige Einzelprojekt reichte von der Anforderungsanalyse bis zur Systemvalidierung.

Die Werkzeugkette umfasste PlatformIO fuer die Firmware-Entwicklung, ROS 2 Humble (containerisiert ueber Docker) fuer den Navigations-Stack, Git fuer die Versionskontrolle und Python fuer Validierungsskripte. Der Entwicklungsprozess folgte einem iterativen Vorgehen. Quantitative Akzeptanzkriterien dienten als verbindliche Nachweise fuer die Systemabnahme.

## 3. Methodisches Vorgehen nach VDI 2206

Die Entwicklung orientierte sich strikt am V-Modell der VDI 2206 fuer mechatronische Systeme. Das Modell strukturiert den Prozess durch Anforderungsdefinition, Systementwurf, domaenenspezifischen Entwurf, Integration und Eigenschaftsabsicherung.
Die funktionale Phasenstruktur bildet die domaenenspezifischen Entwuerfe der VDI 2206 ab. Phase 1 adressiert die Elektronik (Motoransteuerung) und Regelungstechnik (PID). Phase 2 integriert die Sensordomaene. Die Phasen 3 und 4 verschieben den Fokus auf die Softwaredomaene (Host-Rechner). Die iterative Natur der Softwareentwicklung erforderte mehrfache Rueckspruenge ueber die Arme des V-Modells. So fuehrte die systematische UMBmark-Kalibrierung in Phase 2 zu einer Anpassung der Kinematikparameter in `config_drive.h` und damit zu einem Ruecksprung in den domaenenspezifischen Entwurf der Phase 1. Ebenso bedingten gemessene Latenzen des Kanten-Sensors eine nachtraegliche Anpassung der Interrupt-Logik im Sensor-Knoten.

Die Architektur zerlegt das Gesamtsystem in drei funktionale Ebenen:

1. **Drive-Knoten (ESP32-S3):** Fuehrt die Motorregelung aus und publiziert die Odometrie.
2. **Sensor-Knoten (ESP32-S3):** Erfasst IMU-Daten, Batterieinformationen und Kanten-Signale.
3. **Bedien- und Leitstandsebene (Raspberry Pi 5):** Buendelt Lokalisierung, Navigation, Vision und Diagnose.

Die Prinziploesung basiert auf drei Entscheidungen:

* **Differentialantrieb:** Kinematisch einfach und wendig fuer Innenraeume.
* **Dual-MCU-Struktur:** Entkoppelt die deterministische Regelschleife physisch von blockierenden I2C-Sensorabfragen.
* **micro-ROS ueber UART:** Sichert die deterministische Kommunikation, da die Mikrocontroller die Ressourcen fuer einen vollstaendigen DDS-Stack nicht aufbringen.

## 4. Hardware und Antriebssystem

Der Differentialantrieb nutzt zwei JGA25-370-Getriebemotoren mit Hall-Encodern und ein frei drehbares Stuetzrad. Der kalibrierte Raddurchmesser betraegt 65,67 mm bei einer Spurbreite von 178 mm. Die Encoder liefern im 2x-Quadraturmodus etwa 748 Ticks pro Umdrehung und bilden die Datengrundlage der Odometrie. Ein Cytron MDD3A-Treiber steuert die Motoren im Dual-PWM-Modus an.

Die Steuerungsebene besteht aus zwei XIAO ESP32-S3. Der Drive-Knoten fuehrt die PID-Regelschleife deterministisch mit 50 Hz aus und publiziert die Odometrie mit 20 Hz. Der Sensor-Knoten publiziert IMU-, Batterie- und Kanten-Signale ebenfalls mit 20 Hz. Die serielle UART-Anbindung an den Raspberry Pi 5 (921600 Baud) vermeidet die Latenzen drahtloser Verbindungen im Regelpfad.

Zur Sensorik gehoeren ein RPLIDAR A1 (12 m Reichweite) fuer die Lokalisierung und eine Sony-IMX296-Global-Shutter-Kamera fuer visuelle Aufgaben. Ein Hailo-8L-Chip beschleunigt die lokale Bildverarbeitung. Die Spannungsversorgung trennt die 5-V-Logikebene (ueber Buck-Converter) physisch von der direkten Akkuspeisung der Motoren.

## 5. Software und Navigation

Die Firmware der ESP32-S3 teilt Kommunikations-, Regel- und Messaufgaben in dedizierte FreeRTOS-Tasks auf. Der Drive-Knoten wandelt `/cmd_vel`-Eingaben ueber Inverskinematik in Sollradgeschwindigkeiten um.

Der Raspberry Pi 5 betreibt den ROS-2-Stack (Humble) in einer Docker-Umgebung. Der Stack umfasst vier Hauptkomponenten:

* **Lokalisierung und Kartierung:** `slam_toolbox` generiert Online-Karten (5 cm Aufloesung). `odom_to_tf` uebersetzt die Odometrie in TF-Transformationen.
* **Navigation:** Nav2 plant Pfade und regelt die Bahnverfolgung (Regulated Pure Pursuit) mit einer Zielgeschwindigkeit von 0,15 m/s (Nav2) bzw. maximal 0,4 m/s (Joystick).
* **Sicherheitslogik:** Der `cliff_safety_node` blockiert bei erkannter Kante sofort alle Navigationsbefehle und erzwingt einen Stopp (v = 0 m/s, w = 0 rad/s).
* **Hybride Vision-Pipeline:** Der `host_hailo_runner` fuehrt Objekterkennung lokal aus, waehrend der `gemini_semantic_node` eine Cloud-Schnittstelle fuer asynchrone semantische Auswertungen anbindet.

## 6. Validierung und Ergebnisse

Die experimentelle Validierung beantwortet die Projektfragen anhand quantitativer Daten.

**Zu PF1 (Echtzeitfaehigkeit):** Die Dual-Knoten-Architektur entkoppelt die Motorregelung erfolgreich von der Sensorik. Die Regelschleife arbeitet deterministisch mit 50 Hz bei einer Jitter-Breite von unter 2 ms.

**Zu PF2 (Navigationsgenauigkeit):** Die UMBmark-Kalibrierung reduzierte den Odometriefehler um den Faktor 10. Diese Kalibrierung, kombiniert mit IMU-Fusion, ermoeglicht eine praezise SLAM-Kartierung. Der mittlere Positionsfehler liegt bei 0,16 m (ATE RMSE 0,19 m) und erfuellt damit das Akzeptanzkriterium (< 0,20 m).

**Zu PF3 (Vision und Docking):** Die Ergebnisse bestaetigen die Hypothese. Die Edge-Inferenz erreicht praxistaugliche 34 ms Latenz. Das ArUco-Docking arbeitet nach Optimierung der Dreifach-Bedingung (Ultraschall ≤ 0,30 m, Marker sichtbar, Versatz ≤ 5 cm) mit einer Erfolgsquote von 100 Prozent (10 Versuche, 15.03.2026) bei einem mittleren lateralen Versatz von 0,73 cm. Die mittlere Navigationsgenauigkeit ueber zehn Fahrten liegt bei 6,4 cm (Position) und 4,2 Grad (Gierwinkel). Systemgrenzen zeigen sich bei unguenstiger Beleuchtung oder verdeckten Markern.

## 7. Fazit

Der entwickelte Prototyp belegt, dass eine verteilte Architektur mit Open-Source-Komponenten belastbare Ergebnisse fuer die Intralogistik liefern kann. Das V-Modell nach VDI 2206 bot eine belastbare Struktur fuer die Entwicklung, auch wenn die iterative Softwareentwicklung das Modell an seine Grenzen fuehrt.

Technische Einschraenkungen bestehen bei der Schlupfempfindlichkeit der Rad-Odometrie und den Latenzen der Cloud-Dienste. Mit Materialkosten von rund 694 EUR ist das System deutlich guenstiger als kommerzielle Plattformen wie der TurtleBot 4, erreicht jedoch nicht die normative Absicherung (z. B. nach ISO 3691-4) industrieller Systeme mit redundanter Sicherheitssensorik. Zukuenftige Iterationen sollten robuste Docking-Strategien und eine staerkere Kapselung der Cloud-Funktionen adressieren.

## Fachbegriffe

### 1. Robotik und Systemarchitektur

* **AMR (Autonomer mobiler Roboter):** Ein Transportsystem (hier fuer Kleinladungstraeger in der Intralogistik), das sich frei im Raum bewegt und im Gegensatz zu klassischen Fahrerlosen Transportsystemen (FTS) keine aeussere Fuehrungsinfrastruktur wie Linien oder Reflektoren auf dem Boden benoetigt.
* **Differentialantrieb:** Ein kinematisches Antriebskonzept, das auf zwei separat angetriebenen Raedern auf einer gemeinsamen Achse und einem frei drehbaren Stuetzrad basiert. Lenkbewegungen entstehen durch unterschiedliche Drehzahlen des linken und rechten Rades.
* **VDI 2206 (V-Modell):** Eine Richtlinie und methodisches Vorgehensmodell fuer die Entwicklung mechatronischer Systeme. Es strukturiert den Ablauf logisch von der Anforderung ueber den domaenenspezifischen Entwurf bis zur Integration und Eigenschaftsabsicherung.
* **Dual-MCU-Struktur / Dual-Knoten-Architektur:** Die Aufteilung der hardwarenahen Aufgaben auf zwei getrennte Mikrocontroller (MCUs). In diesem Projekt trennt sie die zeitkritische Motorregelung (Drive-Knoten) physisch von den potenziell blockierenden Sensorabfragen (Sensor-Knoten).

### 2. Navigation und Lokalisierung

* **Odometrie:** Die Berechnung der Roboterposition und -orientierung ausschliesslich anhand der gemessenen Radumdrehungen. Sie ist fehleranfaellig gegenueber Rad-Schlupf auf rauem Untergrund.
* **UMBmark-Kalibrierung:** Ein systematisches Test- und Messverfahren, um geometrische Fehler im Antrieb (z. B. ungleiche Raddurchmesser oder Spurbreitenfehler) zu quantifizieren und per Software zu korrigieren.
* **SLAM (Simultaneous Localization and Mapping):** Ein Verfahren, bei dem der Roboter gleichzeitig eine Karte der Umgebung erstellt und sich darin lokalisiert. Hier wird das Paket `slam_toolbox` fuer Online-Karten mit 5 cm Aufloesung genutzt.
* **TF-Transformationen:** Das *Transformation Framework* in ROS 2, das die relativen raeumlichen Positionen verschiedener Roboterkomponenten (z. B. von der Radachse zum Laserscanner) dynamisch berechnet und umwandelt.
* **ATE (Absolute Trajectory Error):** Eine Messgroesse fuer die Navigationsgenauigkeit. Sie vergleicht die tatsaechlich gefahrene Strecke mit der vom System berechneten Idealstrecke.
* **ArUco-Docking:** Ein visuelles Verfahren zur Feinnavigation an die Ladestation, das auf der Erkennung spezieller quadratischer 2D-Marker (ArUco-Marker) durch eine Kamera basiert.

### 3. Hardware und Sensorik

* **Hall-Encoder (2x-Quadraturmodus):** Sensoren an den Motoren, die Magnetfeldaenderungen erfassen. Der Quadraturmodus ermoeglicht es, durch zwei versetzte Signale sowohl die Geschwindigkeit (hier ca. 748 Ticks pro Umdrehung) als auch die Drehrichtung zu ermitteln.
* **IMU-Fusion (Inertial Measurement Unit):** Die rechnerische Zusammenfuehrung der Daten eines Gyroskops (Drehrate) und eines Beschleunigungssensors. Sie wird genutzt, um die Fehler der Rad-Odometrie (z. B. durch Schlupf) auszugleichen.
* **Global-Shutter-Kamera:** Ein Bildsensor, der alle Pixel exakt gleichzeitig belichtet. Im Gegensatz zum *Rolling Shutter* verhindert dies Verzerrungen im Bild, wenn sich der Roboter bewegt.
* **Edge-KI vs. Cloud-Semantik:** *Edge-KI* bezeichnet die lokale Datenverarbeitung direkt auf dem Roboter (hier per Hailo-8L-Chip fuer schnelle Objekterkennung). *Cloud-Semantik* lagert rechenintensive, tiefergehende Bedeutungsanalysen an externe Server (LLM API) aus.
* **Buck-Converter:** Ein Spannungswandler (Abwaertswandler), der die hoehere Akkuspannung effizient auf die stabilen 5 V reduziert, die fuer die Logikebene benoetigt werden.

### 4. Software und Regelungstechnik

* **ROS 2 Humble:** Ein weit verbreitetes Open-Source-Framework (Robot Operating System) zur Entwicklung von Roboter-Software.
* **micro-ROS / DDS-Stack:** DDS (*Data Distribution Service*) ist der Standard zur Datenkommunikation in ROS 2. Da kleine Mikrocontroller (wie der ESP32-S3) nicht genug Ressourcen fuer den vollen DDS-Stack haben, nutzt das System *micro-ROS* ueber eine serielle UART-Verbindung als schlanke Bruecke zum Raspberry Pi 5.
* **PID-Regelschleife:** Ein Regelalgorithmus (Proportional-Integral-Derivative), der die Motoren ansteuert. Er berechnet kontinuierlich (hier 50-mal pro Sekunde) die Differenz zwischen der gewuenschten und der tatsaechlichen Radgeschwindigkeit und passt die Motorleistung entsprechend an.
* **Inverskinematik:** Die mathematische Umrechnung eines zentralen Fahrbefehls (z. B. "fahre 0,4 m/s vorwaerts und drehe leicht links") in die dafuer exakt benoetigten Drehgeschwindigkeiten des linken und rechten Einzelrades.
* **Latenz und Jitter-Breite:** *Latenz* ist die zeitliche Verzoegerung von der Signalerfassung bis zur Reaktion. *Jitter* beschreibt das zeitliche Schwanken eines eigentlich festen Taktes (z. B. der 50-Hz-Regelschleife), was hier erfolgreich auf unter 2 ms minimiert wurde.

## Wie uebersetzt ein autonomer mobiler Roboter einen zentralen Navigationsbefehl in die exakten physikalischen Drehzahlen fuer das linke und rechte Rad?

Inverskinematik des Differentialantriebs.

Die folgende Aufschluesselung zeigt die Berechnung von der Vorgabe durch die Navigationsebene bis zum Zielwert fuer den PID-Regler.

### 1. Die Parameter (Daten)

Das Bewegungsmodell des Roboters basiert auf zwei statischen Hardware-Konstanten, die durch Kalibrierungsfahrten ermittelt wurden:

* **Radradius ($r$):** 0,032835 m (entspricht dem halben kalibrierten Durchmesser von 65,67 mm).
* **Spurbreite ($L$):** 0,178 m (der Abstand zwischen der Mitte des linken und rechten Rades).

### 2. Das mathematische Modell (Regel)

Die Navigation (Nav2) sendet einen Bewegungsvektor (in ROS 2 als `Twist` bezeichnet) an den Drive-Knoten. Dieser Vektor enthaelt zwei Zielgroessen:

* Die Translationsgeschwindigkeit $v$ (Fahrgeschwindigkeit vorwaerts/rueckwaerts in m/s).
* Die Rotationsgeschwindigkeit $\omega$ (Drehung um die eigene Hochachse in rad/s).

Die Firmware auf dem ESP32-S3 nutzt die Inverskinematik, um aus diesen zentralen Vorgaben die exakten Winkelgeschwindigkeiten fuer das linke Rad ($\omega_l$) und das rechte Rad ($\omega_r$) zu berechnen.

Die mathematischen Formeln lauten:

$$\omega_l = \frac{v - \omega \cdot \frac{L}{2}}{r}$$

$$\omega_r = \frac{v + \omega \cdot \frac{L}{2}}{r}$$

### 3. Rechenbeispiel (Schluss)

Ein typisches Fahrszenario ist die Fahrt in einer Linkskurve. Die Navigationsebene gibt folgende Soll-Werte vor:

* $v = 0,2$ m/s (konstante Vorwaertsfahrt).
* $\omega = 0,5$ rad/s (gleichzeitige Linksdrehung).

**Berechnung fuer das linke Rad ($\omega_l$):**
Das linke Rad befindet sich auf der Innenseite der Kurve und muss sich langsamer drehen.

$$\omega_l = \frac{0,2 - 0,5 \cdot \frac{0,178}{2}}{0,032835}$$

$$\omega_l = \frac{0,2 - 0,5 \cdot 0,089}{0,032835}$$

$$\omega_l = \frac{0,2 - 0,0445}{0,032835}$$

$$\omega_l = \frac{0,1555}{0,032835} \approx 4,736 \text{ rad/s}$$

**Berechnung fuer das rechte Rad ($\omega_r$):**
Das rechte Rad befindet sich auf der Aussenseite der Kurve und muss einen weiteren Weg zuruecklegen, sich also schneller drehen.

$$\omega_r = \frac{0,2 + 0,5 \cdot \frac{0,178}{2}}{0,032835}$$

$$\omega_r = \frac{0,2 + 0,0445}{0,032835}$$

$$\omega_r = \frac{0,2445}{0,032835} \approx 7,446 \text{ rad/s}$$

### 4. Technische Konsequenz

Damit der Roboter bei einer Fahrgeschwindigkeit von 0,2 m/s eine exakte Linkskurve beschreibt, muss das rechte Rad mit 7,446 rad/s deutlich schneller rotieren als das linke Rad mit 4,736 rad/s.

Diese berechneten Winkelgeschwindigkeiten bilden die direkten Soll-Werte fuer die PID-Regelschleife. Der Regler auf dem ESP32-S3 vergleicht diese Vorgaben 50-mal pro Sekunde mit den Ist-Werten der Hall-Encoder und passt die elektrische Leistung (PWM-Signal) fuer die beiden Motoren individuell an, um exakt diese Raddrehzahlen zu erreichen.

## Wie laesst sich die tatsaechliche Bewegung des Roboters im Raum allein aus den Drehungsimpulsen der Motoren rekonstruieren?

Vorwaertskinematik (Odometrie) des Differentialantriebs.

Der folgende Ablauf zeigt die Berechnung von den rohen Sensorsignalen bis zur relativen Positionsschaetzung des Roboters.

### 1. Die Parameter und Messwerte (Daten)

Die Berechnung benoetigt statische Hardware-Konstanten und dynamische Messwerte aus einem definierten Zeitintervall ($\Delta t$):

* **Radradius ($r$):** 0,032835 m.
* **Spurbreite ($L$):** 0,178 m.
* **Encoder-Aufloesung:** Linkes Rad 748,6 Ticks pro Umdrehung, rechtes Rad 747,2 Ticks pro Umdrehung.
* **Zeitintervall ($\Delta t$):** 0,05 s, abgeleitet aus der Publikationsrate der Odometrie von 20 Hz.

### 2. Das mathematische Modell (Regel)

Die Odometrie-Berechnung erfolgt in drei Schritten. Zuerst wandelt das System die in $\Delta t$ gemessenen Encoder-Ticks in Winkelgeschwindigkeiten ($\omega_l, \omega_r$) fuer jedes Rad um:

$$\omega_{Rad} = \frac{\Delta Ticks}{TicksProUmdrehung} \cdot \frac{2\pi}{\Delta t}$$

Im zweiten Schritt berechnet die Vorwaertskinematik aus diesen individuellen Radgeschwindigkeiten die Translationsgeschwindigkeit ($v$) und die Rotationsgeschwindigkeit ($\omega$) des Gesamtroboters:

$$v = \frac{r}{2} \cdot (\omega_r + \omega_l)$$

$$\omega = \frac{r}{L} \cdot (\omega_r - \omega_l)$$

Im dritten Schritt integriert das System diese Geschwindigkeiten ueber die Zeit, um die relative Positionsaenderung ($\Delta x, \Delta y, \Delta \theta$) im Raum zu ermitteln:

$$\Delta x = v \cdot \cos(\theta) \cdot \Delta t$$

$$\Delta y = v \cdot \sin(\theta) \cdot \Delta t$$

$$\Delta \theta = \omega \cdot \Delta t$$

$\theta$ repraesentiert dabei die aktuelle Ausrichtung (Heading) des Roboters vor dem Berechnungsschritt.

### 3. Rechenbeispiel (Schluss)

Ein Messzyklus ($\Delta t = 0,05$ s) liefert folgende rohe Sensordaten: Das linke Rad meldet 10 Ticks, das rechte Rad meldet 12 Ticks. Die Startausrichtung $\theta$ betraegt 0 rad (Roboter blickt exakt entlang der X-Achse).

**Schritt 1: Winkelgeschwindigkeiten der Raeder berechnen**


$$\omega_l = \frac{10}{748,6} \cdot \frac{2\pi}{0,05} \approx 1,679 \text{ rad/s}$$

$$\omega_r = \frac{12}{747,2} \cdot \frac{2\pi}{0,05} \approx 2,018 \text{ rad/s}$$

**Schritt 2: Robotergeschwindigkeiten berechnen**


$$v = \frac{0,032835}{2} \cdot (2,018 + 1,679) = 0,0164175 \cdot 3,697 \approx 0,0607 \text{ m/s}$$

$$\omega = \frac{0,032835}{0,178} \cdot (2,018 - 1,679) = 0,184466 \cdot 0,339 \approx 0,0625 \text{ rad/s}$$

**Schritt 3: Positionsaenderung berechnen**


$$\Delta x = 0,0607 \cdot \cos(0) \cdot 0,05 \approx 0,003035 \text{ m}$$

$$\Delta y = 0,0607 \cdot \sin(0) \cdot 0,05 = 0 \text{ m}$$

$$\Delta \theta = 0,0625 \cdot 0,05 \approx 0,003125 \text{ rad}$$

Innerhalb dieser 50 Millisekunden hat sich der Roboter etwa 3 Millimeter vorwaerts bewegt und sich um etwa 0,18 Grad (0,003125 rad) nach links gedreht.

### 4. Technische Konsequenz

Der Drive-Knoten auf dem ESP32-S3 aggregiert diese kontinuierlichen Positionsaenderungen, formatiert sie als `nav_msgs/Odometry` und publiziert sie mit 20 Hz auf dem Topic `/odom`.

Die berechnete Odometrie ist jedoch prinzipbedingt fehleranfaellig gegenueber Rad-Schlupf. Dreht ein Rad auf glattem Untergrund durch, registriert der Encoder Ticks, obwohl keine physische Bewegung im Raum stattfindet. Aus diesem Grund nutzt das System die IMU-Fusion und das SLAM-Verfahren (`slam_toolbox`), um die rein rechnerische Rad-Odometrie mit realen Sensordaten abzugleichen und zu korrigieren.

## Frage 1: Architektur und Echtzeitfaehigkeit

**Frage:** Warum nutzt der Systementwurf eine verteilte Dual-Knoten-Architektur mit zwei separaten Mikrocontrollern (ESP32-S3) fuer die hardwarenahe Ebene, anstatt alle Aufgaben auf einem einzelnen Chip zu buendeln?

**Loesung:** Die physikalische Trennung entkoppelt die deterministische Regelschleife des Fahrkerns (Drive-Knoten) von potenziell blockierenden Sensorabfragen (Sensor-Knoten). Der Drive-Knoten fuehrt die PID-Motorregelung stabil mit 50 Hz aus. Lesezugriffe auf Peripherie wie den I2C-Bus verursachen unregelmaessige Verzoegerungen (Contention). Ein einzelner Mikrocontroller wuerde durch diese Sensorabfragen zeitliche Latenzen in der Regelschleife erleiden, wodurch die harte Echtzeitfaehigkeit der Antriebssteuerung verloren ginge.

## Frage 2: Fehlerkompensation in der Navigation

**Frage:** Aus welchen Gruenden reicht die reine Rad-Odometrie fuer eine verlaessliche Navigation im Intralogistik-Szenario nicht aus und durch welche Mechanismen kompensiert das System diese Schwaeche?

**Loesung:** Rad-Odometrie ist prinzipbedingt fehleranfaellig gegenueber Rad-Schlupf auf rauem oder glattem Untergrund. Dreht ein Rad durch, registriert der Encoder eine Bewegung, die im realen Raum nicht stattgefunden hat. Das System kompensiert diese Abweichungen durch drei Mechanismen: Eine UMBmark-Kalibrierung reduziert vorab systematische Geometriefehler (Faktor 10). Die IMU-Fusion gleicht kurzfristige Rotationsfehler aus. Das SLAM-Verfahren (Simultaneous Localization and Mapping) korrigiert die errechnete Position kontinuierlich durch den Abgleich mit realen LiDAR-Scandaten.

## Frage 3: Hardwarenahe Sicherheitslogik

**Frage:** Wie priorisiert das System sicherheitskritische Ereignisse (wie das Erkennen einer Kante) gegenueber regulaeren Navigationsbefehlen und warum geschieht dies ausserhalb des primaeren Nav2-Stacks?

**Loesung:** Sicherheitskritische Sensorsignale ueberstimmen algorithmisch berechnete Navigationsbefehle stets. Ein dedizierter Multiplexer (`cliff_safety_node`) blockiert bei einer erkannten Kante alle eingehenden Fahrkommandos und sendet eigenstaendig einen sofortigen Stopp-Befehl (v = 0 m/s, w = 0 rad/s) an den Antrieb. Die Auslagerung aus dem Navigations-Stack stellt sicher, dass die Sicherheitslogik nicht durch rechenintensive Planungsprozesse auf dem Host-Rechner oder durch Kommunikationslatenzen verzoegert wird.

## Frage 4: Methodik und Entwicklungsprozess

**Frage:** An welcher Stelle zeigt der Entwicklungsprozess des AMR-Prototypen die Grenzen des Modells nach VDI 2206 auf?

**Loesung:** Das V-Modell nach VDI 2206 beschreibt primaer einen linearen, aufsteigenden Prozess von der Anforderung bis zur Eigenschaftsabsicherung.  Die iterative Softwareentwicklung erfordert jedoch dynamische Rueckspruenge. Die UMBmark-Kalibrierung (Teil der Eigenschaftsabsicherung in Phase 2) machte beispielsweise eine nachtraegliche Korrektur der kinematischen Parameter im Quellcode (`config_drive.h`) erforderlich. Dies entspricht einem Ruecksprung in den domaenenspezifischen Entwurf der Phase 1, was die lineare Grundform des Modells nur eingeschraenkt abbildet.

## Frage 5: Systemgrenzen der Vision-Pipeline

**Frage:** Warum wird Projektfrage 3 (PF3) zur Umgebungswahrnehmung und zum Docking im Fazit des Berichts nur als "bedingt bestaetigt" bewertet?

**Loesung:** Die hybride Vision-Pipeline kombiniert lokale Edge-Inferenz (Hailo-8L) erfolgreich mit Cloud-Semantik, um die Latenz der Objekterkennung auf etwa 34 ms zu senken. Das ArUco-basierte Docking erzielt nach Optimierung eine Erfolgsquote von 100 Prozent (10/10, Dreifach-Bedingung bei 0,30 m). Das System stoesst jedoch an physikalische und architektonische Grenzen: Unguenstige Beleuchtung, ein eingeschraenktes Sichtfeld oder verdeckte Marker mindern die Zuverlaessigkeit der monokularen Kamera deutlich. Zudem verursachen die externen Cloud-Dienste hohe Netzwerklatenzen bei der semantischen Auswertung, was schnelle autonome Reaktionen einschraenkt.
