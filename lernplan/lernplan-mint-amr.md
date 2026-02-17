# Lernplan MINT — Autonome Mobile Robotik

**Kontext:** AMR-Plattform v3.0.0 (ESP32-S3 + Raspberry Pi 5, ROS 2 Humble, micro-ROS)
**Methodik:** Theorie → Übung → Anwendung je Themenblock
**Struktur:** Vier MINT-Säulen, aufeinander abgestimmt

---

## Gesamtarchitektur

```
MINT-Säulen und ihre Verbindung zum AMR-Projekt
═══════════════════════════════════════════════════════════════

  M – Mathematik         I – Informatik        N – Naturwiss.       T – Technik
  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐     ┌─────────────┐
  │ Lineare     │       │ Echtzeit-   │       │ Kinematik & │     │ Elektro-    │
  │ Algebra     │──────▶│ systeme     │       │ Dynamik     │     │ technik     │
  │             │       │ (FreeRTOS)  │       │             │     │ (Sensorik)  │
  ├─────────────┤       ├─────────────┤       ├─────────────┤     ├─────────────┤
  │ Wahr-       │       │ SLAM &      │◀──────│ Sensor-     │────▶│ Antriebs-   │
  │ scheinlich- │──────▶│ Navigation  │       │ physik      │     │ technik     │
  │ keitstheorie│       │             │       │ (Lidar,IMU) │     │ (Motoren)   │
  ├─────────────┤       ├─────────────┤       ├─────────────┤     ├─────────────┤
  │ Regelungs-  │       │ ROS 2 &     │       │ Thermo-     │     │ Mechanik &  │
  │ mathematik  │──────▶│ Kommuni-    │       │ dynamik &   │     │ Konstruk-   │
  │             │       │ kation      │       │ Energetik   │     │ tion        │
  └──────┬──────┘       └──────┬──────┘       └──────┬──────┘     └──────┬──────┘
         │                     │                     │                    │
         └─────────────────────┴─────────────────────┴────────────────────┘
                                      │
                              ┌───────▼───────┐
                              │  AMR-Plattform │
                              │  v3.0.0        │
                              └────────────────┘
```

---

## Modulübersicht

| ID | Säule               | Modul                                 | Wochen  | Phase |
|----|---------------------|---------------------------------------|---------|-------|
| M1 | Mathematik          | Lineare Algebra für Robotik           | W01–W06 | I     |
| M2 | Mathematik          | Wahrscheinlichkeitstheorie & Sensorik | W07–W12 | I     |
| N1 | Naturwissenschaften | Physik: Kinematik & Dynamik           | W01–W06 | I     |
| N2 | Naturwissenschaften | Sensorphysik & Messtechnik            | W07–W10 | I     |
| T1 | Technik             | Elektrotechnik & Sensorintegration    | W05–W10 | II    |
| T2 | Technik             | Antriebstechnik & Motorsteuerung      | W11–W16 | II    |
| I1 | Informatik          | Echtzeitsysteme & FreeRTOS-Vertiefung | W11–W16 | II    |
| I2 | Informatik          | SLAM, Navigation & Pfadplanung        | W17–W22 | III   |
| M3 | Mathematik          | Regelungstechnik                      | W17–W22 | III   |
| N3 | Naturwissenschaften | Energetik & Thermomanagement          | W23–W26 | III   |
| T3 | Technik             | Systemintegration & V-Modell          | W23–W28 | IV    |
| I3 | Informatik          | ROS 2 Advanced & Systemarchitektur    | W27–W32 | IV    |

```
Phasenplan:
Phase I   ██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  W01–W12
Phase II  ░░░░░░░░░░░░██████████████████████████░░░░░░░░░░░░░░░░░░░░  W05–W16
Phase III ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████████░░░░░░░░░░  W17–W26
Phase IV  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████████  W23–W32
          |       |       |       |       |       |       |       |
          W01     W05     W09     W13     W17     W21     W25     W32
```

---

# Säule M — Mathematik

---

## M1 — Lineare Algebra für Robotik (W01–W06)

### Lernziel

Vektoren, Matrizen und Transformationen sicher anwenden, um
Positionen, Orientierungen und Koordinatenwechsel im 2D- und
3D-Raum des AMR zu beschreiben und zu berechnen.

### W01–W02: Vektoren & Matrizen — Grundoperationen

**Theorie:**

Vektoren beschreiben Positionen und Richtungen im Raum. Ein
Positionsvektor $\vec{p} = (x, y)^T$ legt die Lage des AMR in der
Ebene fest. Matrizen bilden die algebraische Grundlage für lineare
Abbildungen — Drehungen, Skalierungen und Projektionen lassen sich
als Matrizenmultiplikation formulieren.

Zentrale Operationen und ihre Robotik-Bedeutung:

- Skalarprodukt $\vec{a} \cdot \vec{b} = |\vec{a}||\vec{b}|\cos\theta$:
  Winkel zwischen Vektoren bestimmen, z. B. Abweichung der
  Fahrtrichtung von der Sollrichtung.
- Kreuzprodukt (3D) $\vec{a} \times \vec{b}$: Drehachse und
  Drehrichtung bestimmen; im 2D-Fall als skalares Kreuzprodukt
  $a_x b_y - a_y b_x$ zur Orientierungsprüfung (links/rechts
  vom Fahrvektor).
- Matrizenmultiplikation: Verkettung von Transformationen;
  Reihenfolge ist entscheidend ($A \cdot B \neq B \cdot A$
  im Allgemeinen).

**Übung:**

1. Gegeben: AMR-Position $\vec{p}_1 = (2{,}0;\; 1{,}5)^T\,\mathrm{m}$,
   Zielposition $\vec{p}_2 = (4{,}0;\; 3{,}0)^T\,\mathrm{m}$.
   Berechne Richtungsvektor, Distanz und Winkel zur x-Achse.
   Implementiere in C++ mit `std::array<float, 2>`.

2. Schreibe eine Funktion `float dot2d(Vec2 a, Vec2 b)` und
   `float cross2d(Vec2 a, Vec2 b)`. Teste: Wenn das Kreuzprodukt
   positiv ist, liegt $\vec{b}$ links von $\vec{a}$ (Gegenuhrzeigersinn).

3. Implementiere eine 2×2-Matrixmultiplikation ohne externe
   Bibliothek. Verifiziere: Drehmatrix $R(\theta) \cdot R(-\theta) = I$
   (Einheitsmatrix, numerische Toleranz $\epsilon < 10^{-6}$).

**Anwendung (AMR):**

Berechne im AMR-Code den Winkel zwischen aktueller Fahrtrichtung
und nächstem Wegpunkt. Nutze das Skalarprodukt zur Winkelbestimmung
und das Kreuzprodukt zur Entscheidung, ob eine Links- oder
Rechtsdrehung kürzer ist.

---

### W03–W04: Koordinatentransformationen & Homogene Matrizen

**Theorie:**

Ein mobiler Roboter operiert in mehreren Koordinatensystemen
gleichzeitig: Welt-Frame (map), Odometrie-Frame (odom),
Roboter-Frame (base_link) und Sensor-Frames (laser_frame, imu_link).
Der TF-Tree in ROS 2 verwaltet diese Beziehungen als Kette von
Transformationen.

Eine 2D-Transformation besteht aus Rotation und Translation.
Die homogene Darstellung fasst beides in einer 3×3-Matrix zusammen:

$$
T = \begin{pmatrix}
\cos\theta & -\sin\theta & t_x \\
\sin\theta &  \cos\theta & t_y \\
0 & 0 & 1
\end{pmatrix}
$$

Verkettung: Ein Punkt $\vec{p}_{\text{sensor}}$ im Sensorkoordinatensystem
wird in Weltkoordinaten überführt durch:

$$
\vec{p}_{\text{welt}} = T_{\text{welt}}^{\text{odom}} \cdot
T_{\text{odom}}^{\text{base}} \cdot
T_{\text{base}}^{\text{sensor}} \cdot \vec{p}_{\text{sensor}}
$$

Die Reihenfolge der Multiplikation entspricht dem Pfad im TF-Tree
von der Wurzel (map) zum Blatt (sensor).

**Übung:**

1. Konstruiere die homogene Transformationsmatrix für:
   Roboter bei $(1;\;2)\,\mathrm{m}$, Orientierung
   $\theta = 30°$. Transformiere den Punkt
   $\vec{p}_{\text{lokal}} = (0{,}5;\; 0)^T\,\mathrm{m}$
   (0,5 m vor dem Roboter) in Weltkoordinaten. Handrechnung,
   dann C++-Verifikation.

2. Schreibe eine Klasse `Transform2D` mit Methoden `compose(other)`,
   `inverse()` und `transformPoint(p)`. Teste die Eigenschaft
   $T \cdot T^{-1} = I$.

3. Verkette drei Transformationen (map→odom→base→laser) mit
   realistischen Werten aus dem AMR-Projekt. Überprüfe das Ergebnis
   gegen die ROS-2-`tf2`-Ausgabe (`ros2 run tf2_ros tf2_echo`).

**Anwendung (AMR):**

Verifiziere den TF-Tree des AMR-Projekts: Lies die statischen
Transformationen aus dem URDF/Launch-File, berechne die Gesamt-
transformation base_link→laser_frame manuell und vergleiche mit
der `tf2`-Laufzeitausgabe. Dokumentiere Abweichungen.

---

### W05–W06: Rotationen in 3D & Quaternionen

**Theorie:**

Für 3D-Rotationen existieren mehrere Darstellungsformen. Jede hat
Vor- und Nachteile:

- **Euler-Winkel** (Roll, Pitch, Yaw): Intuitiv, aber anfällig
  für Gimbal Lock — ein Freiheitsgrad geht verloren, wenn
  Pitch = ±90°.
- **Rotationsmatrizen** (3×3, orthogonal, $\det = 1$):
  Numerisch stabil, aber 9 Parameter für 3 Freiheitsgrade;
  Orthogonalität kann bei wiederholter Multiplikation driften.
- **Quaternionen** $q = w + xi + yj + zk$: 4 Parameter,
  kompakt, interpolierbar (SLERP), kein Gimbal Lock.
  ROS 2 nutzt Quaternionen als Standarddarstellung
  (`geometry_msgs/Quaternion`).

Umrechnung Yaw → Quaternion (2D-Fall, Roll = Pitch = 0):

$$
q = \left(\cos\frac{\theta}{2},\; 0,\; 0,\; \sin\frac{\theta}{2}\right)
$$

**Übung:**

1. Implementiere Umrechnungsfunktionen: Euler → Quaternion,
   Quaternion → Euler, Quaternion → Rotationsmatrix.
   Teste Roundtrip-Konsistenz mit 1000 Zufallswinkeln.

2. Demonstriere Gimbal Lock: Setze Pitch = 90° und variiere
   Roll und Yaw — zeige, dass sich die Euler-Darstellung
   mehrdeutig verhält, während die Quaternion-Darstellung
   stabil bleibt.

3. Implementiere Quaternion-Multiplikation
   ($q_1 \otimes q_2$ für Rotationsverkettung) und
   SLERP ($\text{slerp}(q_1, q_2, t)$ für $t \in [0, 1]$).

**Anwendung (AMR):**

Analysiere die Quaternion-Werte in den TF-Broadcasts des AMR.
Da der AMR in der Ebene fährt, sollten $q_x \approx 0$ und
$q_y \approx 0$ gelten. Schreibe einen Diagnose-Node, der warnt,
falls die Quaternion eine unerwartete 3D-Rotation anzeigt
(z. B. durch IMU-Drift), mit Schwellenwert $|q_x| + |q_y| > 0{,}01$.

---

## M2 — Wahrscheinlichkeitstheorie & Sensorik (W07–W12)

### Lernziel

Stochastische Modelle für Sensorunsicherheit verstehen und
anwenden: Rauschen quantifizieren, Messungen fusionieren und
Roboterposen schätzen.

### W07–W08: Wahrscheinlichkeitsverteilungen & Sensorrauschen

**Theorie:**

Kein Sensor misst perfekt. Das Rauschen eines Sensors lässt sich
als Zufallsvariable modellieren. Die Normalverteilung (Gaußverteilung)
ist das zentrale Modell für Sensorrauschen:

$$
p(x) = \frac{1}{\sigma\sqrt{2\pi}} \exp\left(-\frac{(x - \mu)^2}{2\sigma^2}\right)
$$

$\mu$ ist der Erwartungswert (systematischer Fehler, Bias), $\sigma$
die Standardabweichung (Streuung). Für den RPLidar A1 gibt das
Datenblatt eine Distanzgenauigkeit von $\pm 1\,\%$ bei Distanzen
$< 6\,\mathrm{m}$ an — das entspricht $\sigma \approx 30\,\mathrm{mm}$
bei $3\,\mathrm{m}$ Messdistanz (unter der Annahme, dass $\pm 1\,\%$
einem $2\sigma$-Intervall entspricht).

Weitere relevante Verteilungen:

- **Gleichverteilung:** Modelliert Quantisierungsrauschen
  (z. B. ADC-Auflösung: 12 Bit über 3,3 V ergibt
  $\Delta = 0{,}8\,\mathrm{mV}$ Quantisierungsstufe).
- **Poisson-Verteilung:** Modelliert seltene Ereignisse
  (z. B. Kommunikationsausfälle pro Zeiteinheit).

**Übung:**

1. Erfasse 1000 Lidar-Messungen auf einen festen Reflektor bei
   bekannter Distanz ($d = 1{,}000\,\mathrm{m}$). Berechne $\mu$,
   $\sigma$ und plotte das Histogramm mit überlagernder Gaußkurve
   (Python/Matplotlib). Beurteile: Ist die Normalverteilungsannahme
   gerechtfertigt (Shapiro-Wilk-Test)?

2. Simuliere in C++ einen verrauschten Distanzsensor:
   `float noisyReading(float trueDistance, float sigma)` mit
   `std::normal_distribution`. Erzeuge 10.000 Werte und
   verifiziere, dass 68,3 % innerhalb $\pm 1\sigma$ liegen.

3. Berechne die Fehlerfortpflanzung: Wenn die Roboterposition
   aus Odometrie geschätzt wird (Radumfang $\sigma_r = 0{,}5\,\mathrm{mm}$,
   Radabstand $\sigma_L = 1\,\mathrm{mm}$), wie groß ist die
   Positionsunsicherheit nach $10\,\mathrm{m}$ Geradeausfahrt?

**Anwendung (AMR):**

Charakterisiere das Rauschprofil des RPLidar A1 im AMR-Aufbau:
Messreihe bei 0,5 m, 1,0 m, 2,0 m, 4,0 m. Erstelle eine
Kalibrierungstabelle $\sigma(d)$ und hinterlege sie als Konfiguration
im AMR-Projekt (YAML-Datei für den Lidar-Node).

---

### W09–W10: Bayes-Theorem & Sensormodelle

**Theorie:**

Das Bayes-Theorem verknüpft Vorwissen (Prior) mit neuer Messinformation
(Likelihood) zu einer aktualisierten Schätzung (Posterior):

$$
P(\text{Zustand} \mid \text{Messung}) =
\frac{P(\text{Messung} \mid \text{Zustand}) \cdot P(\text{Zustand})}
{P(\text{Messung})}
$$

Robotik-Kontext: Der Zustand ist die Roboterpose $(x, y, \theta)$,
die Messung kommt vom Lidar oder der Odometrie. Das Sensormodell
$P(z \mid x)$ beschreibt, wie wahrscheinlich eine Messung $z$ bei
gegebener Pose $x$ ist.

Beam-Modell des Lidars (vereinfacht): Die gemessene Distanz $z$
bei wahrer Distanz $d$ setzt sich zusammen aus:

- Gaußsches Rauschen um $d$ (korrekte Messung)
- Gleichverteilung über $[0, z_{\max}]$ (zufälliger Fehler)
- Exponentialverteilung (unerwartete Hindernisse)
- Punktmasse bei $z_{\max}$ (Maximalreichweite, kein Echo)

**Übung:**

1. Implementiere den Bayes-Filter für ein 1D-Problem: Ein Roboter
   fährt auf einer Linie mit 20 diskreten Positionen. Er hat einen
   binären Sensor (Tür erkannt / nicht erkannt). Aktualisiere die
   Positionswahrscheinlichkeit nach jeder Messung und Bewegung.
   Visualisiere die Verteilung als Balkendiagramm.

2. Implementiere das vereinfachte Beam-Modell des Lidars in Python.
   Plotte $P(z \mid d)$ für $d = 2\,\mathrm{m}$ mit realistischen
   Gewichtungsparametern.

3. Vergleiche zwei Sensoren: Lidar ($\sigma = 30\,\mathrm{mm}$) und
   Ultraschall ($\sigma = 150\,\mathrm{mm}$). Zeige anhand des
   Bayes-Updates, wie viele Messungen der Ultraschall benötigt,
   um die gleiche Posterior-Varianz wie der Lidar zu erreichen.

**Anwendung (AMR):**

Implementiere einen einfachen Grid-basierten Bayes-Filter, der die
RPLidar-Daten nutzt, um die Belegungswahrscheinlichkeit einzelner
Zellen in einer 2D-Karte zu aktualisieren (Occupancy Grid Mapping).

---

### W11–W12: Kalman-Filter

**Theorie:**

Der Kalman-Filter ist der optimale lineare Schätzer für gaußverteilte
Systeme. Er besteht aus zwei Schritten:

**Prädiktionsschritt** (Bewegungsmodell):

$$
\hat{x}_{k|k-1} = F \cdot \hat{x}_{k-1} + B \cdot u_k
$$
$$
P_{k|k-1} = F \cdot P_{k-1} \cdot F^T + Q
$$

**Korrekturschritt** (Messmodell):

$$
K_k = P_{k|k-1} \cdot H^T \cdot (H \cdot P_{k|k-1} \cdot H^T + R)^{-1}
$$
$$
\hat{x}_k = \hat{x}_{k|k-1} + K_k \cdot (z_k - H \cdot \hat{x}_{k|k-1})
$$
$$
P_k = (I - K_k \cdot H) \cdot P_{k|k-1}
$$

$F$: Systemmatrix, $B$: Steuermatrix, $H$: Messmatrix,
$Q$: Prozessrauschen, $R$: Messrauschen, $K$: Kalman-Gain.

Für nichtlineare Systeme (Roboter-Odometrie ist nichtlinear):
Extended Kalman Filter (EKF), der die Jacobi-Matrizen von $f$ und $h$
verwendet.

**Übung:**

1. Implementiere einen 1D-Kalman-Filter in C++ für einen Distanzsensor:
   Zustand = Position, Messung = Lidar-Distanz, Prozessrauschen aus
   Odometrie. Plotte Schätzung vs. wahren Wert vs. verrauschte Messung.

2. Erweitere auf 2D: Zustand $= (x, y, v_x, v_y)^T$, Messung
   $= (x_{\text{lidar}}, y_{\text{lidar}})^T$. Implementiere in
   Python mit NumPy. Zeige, wie die Kovarianzellipse schrumpft.

3. Implementiere einen EKF für das Differentialantrieb-Modell:
   Zustand $(x, y, \theta)$, Eingabe $(v, \omega)$, Messung
   $(x_{\text{GPS}}, y_{\text{GPS}})$. Berechne die Jacobi-Matrix $F$
   des Bewegungsmodells analytisch.

**Anwendung (AMR):**

Integriere einen EKF-Node in das AMR-Projekt, der Odometrie-Daten
(Raddrehgeber) und IMU-Daten fusioniert, um eine geglättete
Pose-Schätzung zu liefern. Vergleiche die EKF-Ausgabe mit der
rohen Odometrie durch Aufzeichnung einer Teststrecke (Quadrat,
$2 \times 2\,\mathrm{m}$, Endposition = Startposition).

---

## M3 — Regelungstechnik (W17–W22)

### Lernziel

PID-Regler entwerfen, parametrieren und auf dem AMR implementieren,
mit Verständnis der zugrunde liegenden mathematischen Modelle.

### W17–W18: Systemmodellierung & Übertragungsfunktionen

**Theorie:**

Ein geregeltes System besteht aus Regler, Strecke (Plant) und
Rückführung. Die Strecke des AMR lässt sich als Übertragungsfunktion
modellieren.

Beispiel: Ein DC-Motor mit Trägheitsmoment $J$ und Reibung $b$ hat
die Übertragungsfunktion (Winkelgeschwindigkeit / Spannung):

$$
G(s) = \frac{\Omega(s)}{U(s)} = \frac{K}{Js + b}
$$

Das ist ein PT1-Glied (Verzögerungsglied 1. Ordnung) mit Zeitkonstante
$\tau = J/b$ und stationärer Verstärkung $K_s = K/b$.

Sprungantwort: Nach einem Spannungssprung erreicht der Motor nach
$t = 3\tau$ etwa 95 % der Enddrehzahl.

**Übung:**

1. Bestimme die Motorparameter des AMR experimentell: Lege eine
   Stufenspannung an und messe die Drehzahl über die Encoder.
   Bestimme $\tau$ und $K_s$ aus der Sprungantwort. Dokumentiere
   Messwerte mit Zeitstempeln.

2. Simuliere das PT1-Modell in Python (Euler-Integration mit
   $\Delta t = 1\,\mathrm{ms}$). Vergleiche die simulierte mit der
   gemessenen Sprungantwort. Berechne den mittleren quadratischen
   Fehler (RMSE) als Modellgüte.

3. Erweitere das Modell um ein PT2-Verhalten (Masse + Feder/Dämpfer),
   das die mechanische Kopplung Rad-Boden beschreibt. Vergleiche
   die Sprungantworten von PT1 und PT2.

**Anwendung (AMR):**

Erstelle ein dokumentiertes Streckenmodell für den AMR-Antrieb.
Parametriere es aus experimentellen Daten und hinterlege die
Modellparameter als Konfigurationsdatei im AMR-Repository.

---

### W19–W20: PID-Regler — Entwurf & Implementierung

**Theorie:**

Der PID-Regler berechnet die Stellgröße $u(t)$ aus dem Regelfehler
$e(t) = w(t) - y(t)$ (Sollwert minus Istwert):

$$
u(t) = K_p \cdot e(t) + K_i \int_0^t e(\tau)\,d\tau + K_d \cdot \frac{de(t)}{dt}
$$

Diskrete Implementierung (Abtastzeit $T_s$):

$$
u[k] = K_p \cdot e[k] + K_i \cdot T_s \sum_{j=0}^{k} e[j] + K_d \cdot \frac{e[k] - e[k-1]}{T_s}
$$

Praktische Erweiterungen für Embedded:

- **Anti-Windup:** I-Anteil begrenzen, um Überschwingen nach
  Sättigung zu vermeiden (Integrator-Clamping).
- **Derivative Filtering:** D-Anteil tiefpassfiltern, um
  Rauschverstärkung zu unterdrücken
  ($D_{\text{filt}} = \alpha \cdot D_{\text{filt,alt}} + (1-\alpha) \cdot D_{\text{roh}}$).
- **Abtastzeit-Konsistenz:** Auf dem ESP32 per FreeRTOS-Timer
  sicherstellen, dass $T_s$ konstant bleibt (Jitter $< 1\,\%$).

Parametrierung nach Ziegler-Nichols: Kritische Verstärkung $K_{\text{krit}}$
und Periodendauer $T_{\text{krit}}$ experimentell bestimmen, dann:
$K_p = 0{,}6 \cdot K_{\text{krit}}$,
$T_i = 0{,}5 \cdot T_{\text{krit}}$,
$T_d = 0{,}125 \cdot T_{\text{krit}}$.

**Übung:**

1. Implementiere einen PID-Regler als C++-Klasse:

   ```cpp
   class PIDController {
       float kp_, ki_, kd_;
       float integral_, prev_error_;
       float output_min_, output_max_;  // Anti-Windup
       float dt_;
   public:
       float compute(float setpoint, float measurement);
       void reset();
       void setGains(float kp, float ki, float kd);
   };
   ```

   Teste mit dem simulierten PT1-Modell aus W17.

2. Führe das Ziegler-Nichols-Verfahren am simulierten Modell durch:
   Erhöhe $K_p$ schrittweise (nur P-Anteil), bis Dauerschwingung
   eintritt. Bestimme $K_{\text{krit}}$ und $T_{\text{krit}}$.
   Vergleiche die resultierenden PID-Parameter mit manueller
   Optimierung.

3. Implementiere Anti-Windup und D-Filterung. Vergleiche die
   Sprungantwort mit und ohne diese Erweiterungen (Überschwingen,
   Anregelzeit, Einschwingzeit).

**Anwendung (AMR):**

Implementiere einen PID-Drehzahlregler auf dem ESP32-S3 für einen
Motor des AMR. Der Regler läuft als FreeRTOS-Task auf Core 1 mit
$T_s = 10\,\mathrm{ms}$. Encoder-Feedback über Hardware-Timer.
Parametriere mit Ziegler-Nichols, optimiere dann manuell für
Überschwingen $< 5\,\%$.

---

### W21–W22: Kaskadenregelung & Trajektorienfolgung

**Theorie:**

Ein einzelner PID-Regler steuert eine Größe (z. B. Drehzahl). Für
autonome Navigation benötigt der AMR eine Kaskade:

```
Sollposition     Regler 1       Soll-v, ω      Regler 2       PWM
────────────────▶ (Pfad-  )────────────────────▶ (Motor- )────────▶ Motoren
                  folger                         regler
        ▲                                                    │
        │              Odometrie / IMU                        │
        └─────────────────────────────────────────────────────┘
```

- **Äußere Schleife** (Pfadfolgeregler): Berechnet aus dem
  Positionsfehler die Soll-Geschwindigkeit $v$ und Soll-Drehrate
  $\omega$ (z. B. Pure-Pursuit-Algorithmus).
- **Innere Schleife** (Motorregler): Regelt die einzelnen
  Radgeschwindigkeiten, um $v$ und $\omega$ umzusetzen.

Pure-Pursuit-Algorithmus: Wähle einen Vorausschaupunkt (Lookahead)
auf der Solltrajektorie im Abstand $L_d$ vor dem Roboter.
Die Krümmung $\kappa$ zum Ziel ergibt sich geometrisch als:

$$
\kappa = \frac{2 \cdot \sin(\alpha)}{L_d}
$$

wobei $\alpha$ der Winkel zwischen Fahrtrichtung und Zielrichtung ist.

**Übung:**

1. Implementiere Pure Pursuit in Python: Gegeben eine Wegpunktliste,
   berechne zu jeder Roboterpose den Lookahead-Punkt und die
   resultierende Krümmung. Simuliere die Fahrt und plotte
   Soll- vs. Ist-Trajektorie.

2. Variiere den Lookahead-Abstand $L_d$: Untersuche den Einfluss
   auf die Glättung (kleines $L_d$ → genauer, aber oszillierend;
   großes $L_d$ → glatter, aber schneidet Kurven).

3. Integriere den Kaskadenregler in die Simulation: Pure Pursuit
   als äußere Schleife, PID als innere Schleife. Miss das
   Folgeverhalten bei einer Achttrajektorie.

**Anwendung (AMR):**

Implementiere den Kaskadenregler als ROS-2-Architektur:
`/cmd_vel` (äußere Schleife, Python-Node) →
micro-ROS-Bridge → ESP32-S3 PID-Regler (innere Schleife, C++).
Teste die Trajektorienfolgung auf einer vordefinierten Route
($2 \times 2\,\mathrm{m}$ Quadrat) und dokumentiere den
Querspurfehler.

---

# Säule I — Informatik

---

## I1 — Echtzeitsysteme & FreeRTOS-Vertiefung (W11–W16)

### Lernziel

FreeRTOS-Konzepte vertiefen, Scheduling-Verhalten analysieren
und die Dual-Core-Architektur des ESP32-S3 gezielt für die
AMR-Echtzeitanforderungen nutzen.

### W11–W12: Scheduling, Prioritäten & Timing-Analyse

**Theorie:**

FreeRTOS nutzt ein präemptives Prioritäts-Scheduling: Der
lauffähige Task mit der höchsten Priorität erhält die CPU.
Bei gleicher Priorität greift Round-Robin mit konfigurierbarer
Zeitscheibe (Time Slice, Standard: 1 ms auf ESP32).

Echtzeitanforderungen des AMR:

| Task                    | Deadline       | Priorität | Core   |
|-------------------------|----------------|-----------|--------|
| Motorregelung           | 10 ms (hart)   | Höchste   | Core 1 |
| Lidar-Datenempfang      | 100 ms (weich) | Hoch      | Core 0 |
| micro-ROS-Kommunikation | 50 ms (weich)  | Mittel    | Core 0 |
| LED-/Statusanzeige      | 500 ms (keine) | Niedrig   | Core 0 |

Prioritätsinversion: Ein hochpriorer Task blockiert, weil ein
niedrigpriorer Task eine Mutex hält, während ein mittelpriorer
Task die CPU belegt. FreeRTOS bietet Priority Inheritance Mutexes
als Gegenmaßnahme — der niedrigpriore Task erbt temporär die
Priorität des wartenden Tasks.

**Übung:**

1. Messe die tatsächliche Ausführungszeit und den Jitter der
   Motorregelung mit `esp_timer_get_time()`. Erfasse 10.000
   Zyklen, berechne Min, Max, Mittelwert und Standardabweichung.
   Ziel: Jitter $< 100\,\mu\mathrm{s}$.

2. Provoziere eine Prioritätsinversion: Task A (hoch) und Task C
   (niedrig) teilen eine Mutex, Task B (mittel) rechnet.
   Messe die Blockierzeit von A. Wiederhole mit Priority
   Inheritance Mutex und vergleiche.

3. Implementiere einen Watchdog-Task, der überwacht, ob alle
   Tasks ihre Deadlines einhalten. Bei Überschreitung: Logmeldung
   mit Task-Name und Überschreitungsdauer.

**Anwendung (AMR):**

Erstelle eine Timing-Analyse für alle FreeRTOS-Tasks im AMR-Projekt.
Dokumentiere Worst-Case-Execution-Time (WCET), Deadline und
CPU-Auslastung pro Core. Prüfe, ob Rate-Monotonic-Scheduling (RMS)
die Schedulability-Bedingung erfüllt:

$$
\sum_{i=1}^{n} \frac{C_i}{T_i} \leq n \cdot (2^{1/n} - 1)
$$

---

### W13–W14: Inter-Task-Kommunikation & Synchronisation

**Theorie:**

Tasks im AMR müssen Daten austauschen, ohne Race Conditions zu
erzeugen. FreeRTOS bietet folgende Mechanismen:

- **Queue:** FIFO-Puffer zwischen Tasks. Thread-safe, blockierend.
  Verwendung: Sensordaten von Lese-Task an Verarbeitungs-Task.
- **Mutex (Mutual Exclusion):** Schützt gemeinsame Ressourcen.
  Nur ein Task gleichzeitig im kritischen Abschnitt.
- **Semaphore:** Signalisierung zwischen Tasks (binär) oder
  Ressourcenzählung (counting).
- **Event Groups:** Bit-basierte Flags für komplexe Synchronisation
  (z. B. „warte, bis Lidar UND IMU initialisiert sind").
- **Task Notifications:** Leichtgewichtige 1:1-Signalisierung,
  schneller als Semaphoren (kein Kernel-Objekt).

Dual-Core-Besonderheit (ESP32-S3): Queues und Mutexe funktionieren
core-übergreifend, aber der Cache-Kohärenz-Overhead ist messbar.
Für zeitkritische Daten zwischen Cores: Ring-Buffer mit
Atomic-Operationen als Alternative.

**Übung:**

1. Implementiere eine Queue-basierte Pipeline:
   Task 1 (Core 0) liest Lidar-Rohdaten →
   Queue (Tiefe: 5 Scans) →
   Task 2 (Core 1) verarbeitet und publiziert.
   Messe die Latenz durch die Queue.

2. Vergleiche Mutex vs. Task Notification für ein einfaches
   Signal (Sensor-Daten bereit). Messe die Wechselzeit
   (Context Switch + Signalisierung) für 10.000 Iterationen.

3. Implementiere ein Event-Group-Muster: Der Haupt-Task wartet,
   bis alle Subsysteme (Lidar, IMU, Motor) ihre Initialisierung
   abgeschlossen haben, bevor er in den Betriebsmodus wechselt.

**Anwendung (AMR):**

Überarbeite die Inter-Task-Kommunikation im AMR-Projekt: Ersetze
globale Variablen durch Queues oder Task Notifications. Dokumentiere
jeden Kommunikationskanal in einem Datenflussdiagramm (Task →
Mechanismus → Task, mit Datentyp und Frequenz).

---

### W15–W16: micro-ROS-Integration & Latenzoptimierung

**Theorie:**

micro-ROS bildet die Brücke zwischen dem ESP32-S3 (Embedded) und dem
ROS-2-Graphen auf dem Raspberry Pi 5. Die Kommunikation läuft über
einen micro-ROS-Agent (auf dem Pi), der DDS-Nachrichten im XRCE-DDS-
Protokoll transportiert.

Latenzquellen in der Kette:

```
Sensor → ESP32 Task → micro-ROS Client → Serial/WiFi → Agent → ROS 2 Topic
  t1        t2              t3                t4           t5       t6
```

- $t_1$: Sensorabtastung (hardware-abhängig)
- $t_2$: FreeRTOS Task-Scheduling (Jitter)
- $t_3$: XRCE-DDS-Serialisierung ($\sim 50\,\mu\mathrm{s}$)
- $t_4$: Transportschicht (Serial: $\sim 1\,\mathrm{ms}$ bei 921600 Baud;
  WiFi: $2$–$20\,\mathrm{ms}$, abhängig von Netzlast)
- $t_5$: Agent-Deserialisierung
- $t_6$: ROS-2-Middleware-Dispatch

**Übung:**

1. Instrumentiere die gesamte Kette mit Zeitstempeln: Sende den
   `esp_timer_get_time()`-Wert als Feld in einer Custom-Message.
   Vergleiche am Pi mit `rclpy`-Empfangszeitstempel.
   Berechne die End-to-End-Latenz.

2. Variiere den Transportmodus (Serial vs. WiFi) und die Baudrate.
   Erstelle eine Messtabelle:

   | Transport | Baudrate/Config | Latenz (Median) | Latenz (P95) |
   |-----------|-----------------|-----------------|--------------|
   | UART      | 115200          | ...             | ...          |
   | UART      | 921600          | ...             | ...          |
   | WiFi      | 2,4 GHz         | ...             | ...          |

3. Optimiere die micro-ROS-Konfiguration: Puffergröße, Heartbeat-
   Intervall, Reliable vs. Best-Effort QoS. Messe die Auswirkung
   auf Latenz und Paketverlustrate.

**Anwendung (AMR):**

Definiere ein Latenz-Budget für den AMR: Gesamtlatenz von
Lidar-Messung bis Motorreaktion $< 50\,\mathrm{ms}$. Verteile
das Budget auf die Teilstrecken und identifiziere den Engpass.
Dokumentiere die Ergebnisse als Performance-Baseline für das
AMR-Projekt.

---

## I2 — SLAM, Navigation & Pfadplanung (W17–W22)

### Lernziel

Die theoretischen Grundlagen von SLAM und autonomer Navigation
verstehen und auf dem AMR mit ROS 2 umsetzen.

### W17–W18: Occupancy Grid Mapping

**Theorie:**

Eine Belegungskarte (Occupancy Grid) diskretisiert die Umgebung
in Zellen der Größe $r \times r$ (typisch: $r = 50\,\mathrm{mm}$).
Jede Zelle speichert die Log-Odds der Belegungswahrscheinlichkeit:

$$
l_{t} = l_{t-1} + \log\frac{P(m \mid z_t)}{1 - P(m \mid z_t)} - l_0
$$

$l_0 = \log\frac{P(m)}{1 - P(m)}$ ist der Prior (typisch: $l_0 = 0$
für $P(m) = 0{,}5$). Log-Odds vermeiden numerische Probleme bei
wiederholter Multiplikation kleiner Wahrscheinlichkeiten.

Inverse Sensormodell: Für jede Lidar-Messung bestimme die Zellen
auf dem Strahlverlauf (Bresenham-Algorithmus oder Raytracing):
Zellen vor dem Messpunkt → frei ($l \downarrow$),
Zelle am Messpunkt → belegt ($l \uparrow$).

**Übung:**

1. Implementiere einen Occupancy-Grid-Mapper in Python:
   $200 \times 200$ Zellen, $r = 50\,\mathrm{mm}$, Log-Odds-Update.
   Simuliere einen rotierenden Lidar (360°, 1°-Auflösung) in einem
   rechteckigen Raum. Visualisiere die Karte als Heatmap.

2. Implementiere Raytracing mit dem Bresenham-Algorithmus: Bestimme
   alle Zellen zwischen Sensorursprung und Messpunkt. Teste mit
   bekannten Geometrien.

3. Untersuche den Einfluss der Zellgröße: Vergleiche
   $r = 25\,\mathrm{mm}$ vs. $r = 100\,\mathrm{mm}$ hinsichtlich
   Speicherbedarf, Rechenzeit und Kartenqualität.

**Anwendung (AMR):**

Zeichne eine ROS-2-Bag-Datei mit Lidar-Scans und Odometrie auf.
Nutze die eigene Occupancy-Grid-Implementierung, um daraus eine
Karte zu erzeugen. Vergleiche das Ergebnis mit `slam_toolbox`.

---

### W19–W20: SLAM — Simultaneous Localization and Mapping

**Theorie:**

SLAM löst ein Henne-Ei-Problem: Um eine Karte zu erstellen, braucht
der Roboter seine Position; um sich zu lokalisieren, braucht er
eine Karte. SLAM löst beides gleichzeitig.

Graph-basiertes SLAM (wie `slam_toolbox`): Knoten repräsentieren
Roboterposen, Kanten repräsentieren Bewegungsmessungen (Odometrie)
und Beobachtungsübereinstimmungen (Scan Matching). Das Backend
minimiert den Gesamtfehler durch nichtlineare Optimierung.

Scan Matching (Iterative Closest Point, ICP): Zwei aufeinander-
folgende Lidar-Scans werden so zueinander verschoben und rotiert,
dass die Punktkorrespondenz minimiert wird.

Loop Closure: Erkennung, dass der Roboter einen zuvor besuchten
Ort erreicht hat. Korrigiert den akkumulierten Drift der Odometrie.

**Übung:**

1. Implementiere ICP in 2D (Python): Zwei Punktwolken (simulierte
   Lidar-Scans), finde die optimale Transformation $(R, t)$ durch
   iterative Minimierung. Teste mit bekanntem Ground-Truth.

2. Simuliere Odometrie-Drift: Fahre einen geschlossenen Kreis,
   addiere bei jedem Schritt gaußsches Rauschen. Zeige den
   akkumulierten Fehler. Implementiere eine einfache Loop-Closure-
   Korrektur (Endpose ≈ Startpose → verteile Fehler gleichmäßig).

3. Konfiguriere `slam_toolbox` für den AMR: Passe Parameter an
   (Auflösung, Scan-Matching-Methode, Loop-Closure-Schwellenwert).
   Dokumentiere die Parameterwahl.

**Anwendung (AMR):**

Erstelle mit dem AMR und `slam_toolbox` eine Karte eines realen
Raums. Bewerte die Kartenqualität: Gerade Wände sollten gerade
sein, bekannte Abstände sollten stimmen (Messung mit Zollstock
als Ground Truth). Dokumentiere den Kartierungsprozess und die
erreichbare Genauigkeit.

---

### W21–W22: Pfadplanung & Navigation Stack

**Theorie:**

ROS 2 Navigation Stack (`nav2`) orchestriert die autonome
Navigation: Globaler Planer (A*, Dijkstra, NavFn) berechnet
den Pfad auf der statischen Karte; lokaler Planer (DWB, TEB,
MPPI) erzeugt `cmd_vel`-Befehle unter Berücksichtigung dynamischer
Hindernisse.

Costmap-Konzept: Überlagert die Occupancy Grid Map mit
Kostenschichten (Inflation Layer: Sicherheitsabstand zu
Hindernissen, exponentiell abklingend).

Recovery Behaviors: Automatische Maßnahmen bei Blockierung
(Rückwärtsfahren, Drehen auf der Stelle, Karte löschen und
neu planen).

**Übung:**

1. Konfiguriere den `nav2`-Stack für den AMR: `bt_navigator`,
   globaler Planer (NavFn), lokaler Planer (DWB), Costmaps.
   Erstelle die YAML-Konfigurationsdatei mit dokumentierten
   Parametern.

2. Sende Navigationsziele über `rviz2` oder programmatisch
   (`NavigateToPose` Action). Messe die Pfadlänge und
   Fahrzeit für definierte Start-Ziel-Paare.

3. Teste Recovery Behaviors: Stelle ein unerwartetes Hindernis
   in den geplanten Pfad. Beobachte das Verhalten des lokalen
   Planers und der Recovery-Strategie.

**Anwendung (AMR):**

Integriere den vollständigen `nav2`-Stack auf dem Raspberry Pi 5.
Definiere eine Teststrecke mit drei Wegpunkten. Der AMR soll
autonom navigieren: SLAM-Karte laden → Pfad planen → ausführen →
dynamischen Hindernissen ausweichen. Dokumentiere das Ergebnis
als Video und Performance-Report.

---

# Säule N — Naturwissenschaften

---

## N1 — Physik: Kinematik & Dynamik (W01–W06)

### Lernziel

Die physikalischen Gesetze der Roboterbewegung verstehen und als
mathematische Modelle für Simulation und Regelung nutzen.

### W01–W02: Kinematik des Differentialantriebs

**Theorie:**

Der AMR nutzt einen Differentialantrieb (Differential Drive):
Zwei unabhängig angetriebene Räder auf einer Achse bestimmen
die Bewegung. Ein oder mehrere Stützräder (Castor) stabilisieren.

Kinematisches Modell (Forward Kinematics): Aus den Radgeschwindigkeiten
$v_L$ (links) und $v_R$ (rechts) folgen Translationsgeschwindigkeit $v$
und Drehrate $\omega$:

$$
v = \frac{v_R + v_L}{2}, \qquad \omega = \frac{v_R - v_L}{L}
$$

$L$ ist der Radabstand (Track Width). Die Positionsaktualisierung
(Odometrie) bei Abtastzeit $\Delta t$:

$$
x_{k+1} = x_k + v \cdot \cos(\theta_k) \cdot \Delta t
$$
$$
y_{k+1} = y_k + v \cdot \sin(\theta_k) \cdot \Delta t
$$
$$
\theta_{k+1} = \theta_k + \omega \cdot \Delta t
$$

Inverse Kinematics: Aus gewünschtem $(v, \omega)$ die Radgeschwindigkeiten
berechnen:

$$
v_R = v + \frac{\omega \cdot L}{2}, \qquad v_L = v - \frac{\omega \cdot L}{2}
$$

**Übung:**

1. Messe den Radabstand $L$ und den Raddurchmesser $d$ des AMR.
   Berechne: Welche Encoder-Auflösung (Ticks pro Umdrehung) ist
   nötig, um eine Positionsauflösung $< 1\,\mathrm{mm}$ zu erreichen?

2. Implementiere Forward und Inverse Kinematics in C++ auf dem ESP32.
   Teste: Fahre ein Quadrat ($1 \times 1\,\mathrm{m}$) durch
   Sequenz von Geradeausfahrt und 90°-Drehung. Messe den
   Endpositionsfehler.

3. Simuliere die Odometrie in Python über 100 m Geradeausfahrt
   mit Rauschmodell ($\sigma_v = 1\,\%$, $\sigma_\omega = 2\,\%$).
   Plotte die Positions-Unsicherheitsellipse (Monte-Carlo, 1000 Runs).

**Anwendung (AMR):**

Integriere die Odometrie-Berechnung in den ESP32-Code. Publiziere
die berechnete Pose über micro-ROS als `nav_msgs/Odometry`.
Verifiziere gegen eine externe Referenz (Maßband oder Kameramessung)
für definierte Teststrecken.

---

### W03–W04: Dynamik — Kräfte & Momente

**Theorie:**

Die Kinematik beschreibt die Bewegung, die Dynamik die Ursachen
(Kräfte und Momente). Für den AMR relevant:

Newtons 2. Gesetz (Translation): $F = m \cdot a$

Drehmomentgleichung: $M = J \cdot \dot{\omega}$

$J$ ist das Trägheitsmoment des Roboters um die Vertikalachse.
Für eine zylindrische Annäherung: $J = \frac{1}{2} m r^2$ (Vollzylinder).

Reibungsmodelle:

- Coulomb-Reibung: $F_r = \mu \cdot F_N$ (konstant, geschwindigkeits-
  unabhängig). Dominiert bei niedrigen Geschwindigkeiten.
- Viskose Reibung: $F_v = b \cdot v$ (proportional zur Geschwindigkeit).
  Dominiert bei höheren Geschwindigkeiten.
- Kombiniertes Modell: $F_{\text{ges}} = \mu \cdot F_N + b \cdot v$

Antriebskraft des Motors: $F_{\text{Antrieb}} = \frac{M_{\text{Motor}}}{r_{\text{Rad}}}$

Die maximale Beschleunigung ergibt sich aus:
$a_{\max} = \frac{F_{\text{Antrieb}} - F_{\text{Reibung}}}{m}$

**Übung:**

1. Bestimme die Masse des AMR (Waage) und schätze das Trägheitsmoment
   aus den geometrischen Abmessungen. Vergleiche mit einem
   experimentellen Wert: Befestige eine bekannte Masse am Rand
   und messe die Winkelbeschleunigung.

2. Bestimme die Reibungskoeffizienten experimentell: Lege verschiedene
   PWM-Werte an und messe die stationäre Geschwindigkeit. Plotte
   $F_{\text{Antrieb}}$ vs. $v$ — der y-Achsenabschnitt gibt die
   Coulomb-Reibung, die Steigung die viskose Reibung.

3. Berechne die maximale Steigung, die der AMR bewältigen kann:
   $\sin(\alpha) = \frac{F_{\text{Antrieb}} - F_{\text{Reibung}}}{m \cdot g}$.
   Verifiziere experimentell mit einer Rampe.

**Anwendung (AMR):**

Erstelle ein dynamisches Modell des AMR: Masse, Trägheitsmoment,
Reibungskoeffizienten, Motorkenndaten. Hinterlege als parametriertes
Simulationsmodell (Python-Klasse), das für Reglerentwurf und
Trajektorienplanung verwendet werden kann.

---

### W05–W06: Energetik & Batterie-Betriebsmodell

**Theorie:**

Der AMR wird batteriebetrieben. Die verfügbare Energie bestimmt
die Einsatzdauer. Ein Energiemodell verknüpft Fahrtprofil mit
Energieverbrauch.

Elektrische Leistung: $P = U \cdot I = R \cdot I^2$

Motorleistung: $P_{\text{mech}} = M \cdot \omega = F \cdot v$

Wirkungsgrad: $\eta = \frac{P_{\text{mech}}}{P_{\text{el}}}$
(typisch 60–80 % für DC-Motoren)

Batteriekapazität: Angabe in $\mathrm{Wh}$ oder $\mathrm{mAh}$ bei
Nennspannung. Nutzbare Kapazität: $C_{\text{nutz}} = C_{\text{nenn}} \cdot$ DoD
(Depth of Discharge, typisch 80 % für LiPo).

Reichweite: $s = \frac{C_{\text{nutz}}}{P_{\text{mittel}} / v_{\text{mittel}}}$

**Übung:**

1. Messe den Stromverbrauch des AMR in verschiedenen Betriebszuständen:
   Stillstand (Elektronik), Geradeausfahrt ($v = 0{,}2\,\mathrm{m/s}$),
   Drehung, SLAM aktiv. Erstelle eine Leistungsmatrix.

2. Berechne die theoretische Einsatzdauer aus Batteriekapazität
   und gemessenem Durchschnittsverbrauch. Vergleiche mit
   experimenteller Messung (Fahrt bis Abschaltspannung).

3. Implementiere einen SoC-Schätzer (State of Charge) auf dem ESP32:
   Coulomb-Counting ($\text{SoC} = \text{SoC}_0 - \frac{1}{C} \int I\,dt$).
   Publiziere als micro-ROS-Topic.

**Anwendung (AMR):**

Integriere eine Batterieanzeige in das AMR-System: SoC-Schätzung
auf dem ESP32, Anzeige im Web-Dashboard, ROS-2-Topic für
autonome Rückkehr zum Ladepunkt bei SoC < 20 %.

---

## N2 — Sensorphysik & Messtechnik (W07–W10)

### Lernziel

Die physikalischen Messprinzipien der AMR-Sensoren verstehen, um
Messfehler einordnen und Sensorparameter optimieren zu können.

### W07–W08: Lidar — Optische Entfernungsmessung

**Theorie:**

Der RPLidar A1 nutzt Triangulation: Ein Laserdiode sendet einen
Strahl, eine Linse fokussiert den reflektierten Punkt auf einen
Positionsdetektor (PSD oder CMOS). Aus dem Einfallswinkel ergibt
sich die Distanz (keine Laufzeitmessung wie bei ToF-Lidars).

Triangulationsprinzip:

$$
d = \frac{f \cdot B}{\Delta p}
$$

$f$: Brennweite der Empfangsoptik, $B$: Basisabstand Sender-Empfänger,
$\Delta p$: Pixelverschiebung auf dem Detektor.

Konsequenz: Die Distanzauflösung sinkt quadratisch mit der Entfernung
($\Delta d \propto d^2$). Bei $d = 6\,\mathrm{m}$ ist der RPLidar A1
an seiner Leistungsgrenze.

Störquellen: Umgebungslicht (Sonnenlicht: Infrarot-Rauschen),
Oberflächenreflektivität (schwarze Oberflächen absorbieren,
Spiegel reflektieren spekular), Mehrfachreflexionen.

**Übung:**

1. Messe die Distanzgenauigkeit des RPLidar A1 bei verschiedenen
   Oberflächen (weiße Wand, schwarzes Tuch, Glas) und Distanzen
   (0,5 m, 1 m, 3 m, 6 m). Dokumentiere als Tabelle mit $\mu$
   und $\sigma$.

2. Untersuche den Einfluss von Umgebungslicht: Messe dieselbe
   Distanz bei Kunstlicht, Tageslicht und direkter Sonneneinstrahlung.
   Quantifiziere den Unterschied in $\sigma$.

3. Implementiere einen Medianfilter (Fenstergröße 5) für Lidar-Daten
   auf dem ESP32. Vergleiche die Streuung vor und nach Filterung.

**Anwendung (AMR):**

Erstelle ein Kalibrierungsprotokoll für den RPLidar A1 im AMR-Aufbau:
Messmatrix (Distanz × Oberfläche × Lichtverhältnisse), systematische
Fehler dokumentieren, Kompensationsparameter ableiten.

---

### W09–W10: IMU — Inertiale Messtechnik

**Theorie:**

Die IMU (Inertial Measurement Unit) kombiniert typischerweise:

- **Beschleunigungssensor (Accelerometer):** Misst spezifische Kraft
  (Beschleunigung + Schwerkraft). MEMS-Prinzip: Eine seismische Masse
  lenkt einen Kondensator aus; die Kapazitätsänderung ist proportional
  zur Beschleunigung. Im Stillstand misst der Sensor
  $\vec{g} = (0, 0, 9{,}81)^T\,\mathrm{m/s^2}$ — daraus lassen
  sich Roll und Pitch bestimmen.

- **Gyroskop:** Misst Drehrate $\omega$ (°/s oder rad/s).
  MEMS-Prinzip: Coriolis-Kraft auf eine schwingende Struktur.
  Hauptproblem: Bias-Drift — ein kleiner konstanter Offset integriert
  sich über die Zeit zu einem wachsenden Winkelfehler.

Drift-Abschätzung: Bei einem Bias von $0{,}1\,°/\mathrm{s}$ beträgt
der Winkelfehler nach 1 Minute $6°$ und nach 10 Minuten $60°$ —
ohne Korrektur durch externe Referenz (Magnetometer oder Lidar).

Sensorfusion: Komplementärfilter oder Kalman-Filter kombinieren
Accelerometer (langsam, aber driftfrei) mit Gyroskop (schnell,
aber driftend) zu einer stabilen Orientierungsschätzung.

**Übung:**

1. Lese die Rohdaten der AMR-IMU (Accelerometer + Gyroskop) mit
   $100\,\mathrm{Hz}$ aus. Zeichne $10\,\mathrm{s}$ Stillstandsdaten
   auf. Berechne den Bias (Mittelwert) und das Rauschen ($\sigma$)
   für jede Achse.

2. Implementiere einen Komplementärfilter für die Yaw-Schätzung:
   $\theta = \alpha \cdot (\theta_{\text{prev}} + \omega \cdot \Delta t)
   + (1 - \alpha) \cdot \theta_{\text{acc}}$ mit $\alpha = 0{,}98$.
   Vergleiche mit reiner Gyroskop-Integration über 5 Minuten.

3. Messe die Allan-Varianz des Gyroskops (Python): Identifiziere
   Rauschparameter (Angle Random Walk) und Bias-Instabilität
   aus dem Allan-Varianz-Plot.

**Anwendung (AMR):**

Integriere die IMU-Daten in die Odometrie des AMR: Nutze den
Komplementärfilter (oder den EKF aus M2) zur Korrektur des
Yaw-Winkels. Vergleiche die Trajektoriengenauigkeit mit und ohne
IMU-Fusion auf einer Teststrecke.

---

## N3 — Energetik & Thermomanagement (W23–W26)

### Lernziel

Thermische Grenzen des AMR-Systems kennen und ein einfaches
Thermomanagement implementieren.

### W23–W24: Wärmeentwicklung & Kühlung

**Theorie:**

Elektronische Komponenten erzeugen Verlustleistung, die als Wärme
abgeführt werden muss. Überschreitet die Betriebstemperatur den
zulässigen Bereich, drohen Fehlfunktionen oder Beschädigung.

Kritische Komponenten im AMR:

| Komponente                     | Verlustleistung (typ.)          | $T_{\max}$                                          |
|--------------------------------|---------------------------------|-----------------------------------------------------|
| ESP32-S3 (Dual Core, Volllast) | $0{,}5$–$1{,}0\,\mathrm{W}$     | $85\,°\mathrm{C}$                                   |
| Raspberry Pi 5                 | $5$–$10\,\mathrm{W}$            | $85\,°\mathrm{C}$ (Throttling ab $80\,°\mathrm{C}$) |
| Motortreiber (H-Brücke)        | $I^2 \cdot R_{\text{DS(on)}}$   | $150\,°\mathrm{C}$ (Junction)                       |
| DC-Motoren                     | $I^2 \cdot R_{\text{Wicklung}}$ | $130\,°\mathrm{C}$ (Wicklung)                       |

Thermisches Ersatzschaltbild:
$\Delta T = P_{\text{Verlust}} \cdot R_{\text{th}}$

$R_{\text{th}}$ ist der thermische Widerstand (K/W) vom Chip zur
Umgebung (Junction-to-Ambient).

**Übung:**

1. Messe die Temperatur des Raspberry Pi 5 unter verschiedenen
   Lasten (Idle, SLAM, SLAM + Navigation + Kamera). Nutze
   `vcgencmd measure_temp`. Plotte Temperatur vs. Zeit.

2. Berechne: Reicht passive Kühlung (Kühlkörper) oder ist ein
   Lüfter nötig? Gegeben: $R_{\text{th,passiv}} = 8\,\mathrm{K/W}$,
   $R_{\text{th,aktiv}} = 3\,\mathrm{K/W}$, $P = 8\,\mathrm{W}$,
   $T_{\text{Umgebung}} = 25\,°\mathrm{C}$.

3. Implementiere Thermal Throttling auf dem ESP32: Lese den internen
   Temperatursensor aus. Bei $T > 70\,°\mathrm{C}$: CPU-Frequenz
   reduzieren; bei $T > 80\,°\mathrm{C}$: nicht-kritische Tasks
   suspendieren.

**Anwendung (AMR):**

Erstelle ein Thermomanagement-Konzept für den AMR: Temperatur-
monitoring aller kritischen Komponenten (ESP32 intern, Pi über
`vcgencmd`, Motortreiber über NTC), Schwellenwerte definieren,
Schutzmaßnahmen implementieren. Publiziere die Temperaturdaten
als ROS-2-Diagnose-Topics.

---

# Säule T — Technik

---

## T1 — Elektrotechnik & Sensorintegration (W05–W10)

### Lernziel

Elektrische Schaltungen für Sensoranbindung und Motorsteuerung
dimensionieren, aufbauen und systematisch in Betrieb nehmen.

### W05–W06: Signalkonditionierung & ADC

**Theorie:**

Analoge Sensorsignale müssen vor der Digitalisierung aufbereitet
werden (Signal Conditioning):

- **Spannungsteiler:** Pegelanpassung für den ADC-Eingangsbereich
  des ESP32-S3 (0–3,3 V). $V_{\text{out}} = V_{\text{in}} \cdot R_2 / (R_1 + R_2)$.
- **Tiefpassfilter (RC):** Hochfrequentes Rauschen unterdrücken.
  Grenzfrequenz $f_g = 1 / (2\pi RC)$. Empfehlung: $f_g$ mindestens
  10× höher als die Signalfrequenz (Nyquist beachten).
- **Operationsverstärker:** Impedanzwandler (Eingangsimpedanz erhöhen),
  Verstärkung (Kleinsignale des Sensors aufbereiten).

ADC des ESP32-S3: 12 Bit Auflösung, SAR-Architektur.
Quantisierungsstufe: $\Delta V = 3{,}3\,\mathrm{V} / 4096 \approx 0{,}8\,\mathrm{mV}$.
Nichtlinearität: Kalibrierung mit `esp_adc_cal` empfohlen.

**Übung:**

1. Dimensioniere einen Spannungsteiler für die Batteriespannungs-
   messung: $V_{\text{Batt}} = 7{,}4$–$8{,}4\,\mathrm{V}$ (2S LiPo)
   auf $0$–$3{,}3\,\mathrm{V}$ abbilden. Berechne $R_1$, $R_2$.
   Berücksichtige den Eingangswiderstand des ADC
   ($R_{\text{in}} \approx 10\,\mathrm{M\Omega}$).

2. Baue einen RC-Tiefpass ($f_g = 100\,\mathrm{Hz}$) für einen
   analogen Temperatursensor (NTC). Messe das Frequenzverhalten
   mit einem Funktionsgenerator oder durch Software-FFT.

3. Kalibriere den ESP32-ADC: Messe mit Multimeter und ADC
   gleichzeitig bei 10 Spannungspunkten. Erstelle eine
   Korrekturtabelle (Lookup Table) oder lineare Regression.

**Anwendung (AMR):**

Implementiere die Batteriespannungsmessung im AMR: Spannungsteiler
→ ADC → Kalibrierung → SoC-Berechnung → micro-ROS-Topic.
Alarmierung bei $V < 6{,}6\,\mathrm{V}$ (Unterspannungsschutz).

---

### W07–W08: I²C, SPI & UART — Busprotokoll-Praxis

**Theorie:**

Die AMR-Sensoren kommunizieren über serielle Busse:

| Bus  | Takt                    | Leitungen               | Topologie                 | AMR-Verwendung           |
|------|-------------------------|-------------------------|---------------------------|--------------------------|
| I²C  | bis 400 kHz (Fast Mode) | 2 (SDA, SCL)            | Multi-Master, Multi-Slave | IMU, Temperatursensor    |
| SPI  | bis 80 MHz (ESP32)      | 4 (MOSI, MISO, SCK, CS) | Master-Slave              | (optional: Display)      |
| UART | konfigurierbar          | 2 (TX, RX)              | Punkt-zu-Punkt            | RPLidar, micro-ROS-Agent |

I²C-Adressierung: 7-Bit-Adresse, maximal 128 Geräte pro Bus
(praktisch weniger wegen Adresskonflikten und Kapazitätsgrenze
$C_{\text{Bus}} < 400\,\mathrm{pF}$).

Fehlerquellen: Taktdehnung (Clock Stretching) durch langsame Slaves,
Bus-Lockup bei fehlerhaftem Slave (Lösung: Bus-Recovery-Sequenz),
EMV-Störungen bei langen Leitungen.

**Übung:**

1. Lese die IMU (z. B. MPU6050 oder BNO055) über I²C aus:
   Initialisierung, Registerkonfiguration, Datenauslese mit
   `i2c_master_transmit_receive`. Messe die tatsächliche
   I²C-Taktfrequenz mit Oszilloskop oder Logic Analyzer.

2. Implementiere eine I²C-Fehlerbehandlung: Timeout-Erkennung,
   automatischer Bus-Recovery (9 SCL-Taktimpulse bei SDA-Low-Blockade),
   Retry-Strategie mit exponentiellem Backoff.

3. Vergleiche UART-Baudraten für den RPLidar: 115200 vs. 256000 Baud.
   Messe Datenrate, Fehlerrate und CPU-Last bei beiden Einstellungen.

**Anwendung (AMR):**

Erstelle eine HAL-Schicht (Hardware Abstraction Layer) für alle
Buskommunikationen im AMR-Projekt: Einheitliche Fehlerbehandlung,
Retry-Logik, Logging. Jeder Sensor-Treiber nutzt die HAL statt
direkte ESP-IDF-Aufrufe.

---

### W09–W10: Schaltungsschutz & EMV-Grundlagen

**Theorie:**

Mobile Roboter operieren in unvorhersehbaren Umgebungen. Die
Elektronik benötigt Schutz gegen:

- **Verpolung:** Schottky-Diode in Reihe ($V_{\text{drop}} \approx 0{,}3\,\mathrm{V}$)
  oder P-MOSFET-Schutzschaltung (nahezu verlustfrei).
- **Überspannung:** TVS-Diode (Transient Voltage Suppressor) parallel
  zur Versorgung. Ansprechzeit $< 1\,\mathrm{ns}$.
- **ESD:** Schutzdioden an exponierten Stecker-Pins (USB, Sensor-
  Anschlüsse). Norm: IEC 61000-4-2.
- **Motorentstörung:** Freilaufdioden an Motoranschlüssen,
  Keramikkondensatoren ($100\,\mathrm{nF}$) direkt an Motorklemmen.

EMV (Elektromagnetische Verträglichkeit): Motoren und PWM-Signale
erzeugen Störungen. Gegenmaßnahmen: Leitungsführung (Motor- und
Signalleitungen trennen), Masseführung (Sternpunkt, keine
Masseschleifen), Schirmung.

**Übung:**

1. Analysiere die aktuelle AMR-Platine: Welche Schutzmaßnahmen
   sind vorhanden? Welche fehlen? Erstelle eine Checkliste.

2. Messe mit dem Oszilloskop die Spannungsspitzen beim
   Motorschaltvorgang (PWM-Flanke). Dokumentiere Amplitude und
   Dauer. Beurteile, ob TVS-Dioden nötig sind.

3. Teste die EMV-Empfindlichkeit: Betreibe die Motoren mit PWM und
   beobachte die I²C-Kommunikation (IMU-Daten). Quantifiziere die
   Fehlerrate mit und ohne Entstörmaßnahmen.

**Anwendung (AMR):**

Erstelle einen Schutzkonzept-Plan für die AMR-Elektronik: Verpolschutz,
Überspannung, ESD, Motorentstörung. Dokumentiere als Schaltplan-
Ergänzung mit Bauteilauswahl und Begründung.

---

## T2 — Antriebstechnik & Motorsteuerung (W11–W16)

### Lernziel

DC-Motoren mit Encoder ansteuern, die PWM-Erzeugung auf dem ESP32
beherrschen und einen geschlossenen Regelkreis implementieren.

### W11–W12: DC-Motor & H-Brücke

**Theorie:**

Gleichstrommotor-Modell:

$$
U = R \cdot I + L \cdot \frac{dI}{dt} + K_e \cdot \omega
$$

$R$: Wicklungswiderstand, $L$: Induktivität (oft vernachlässigbar
bei kleinen Motoren), $K_e$: Gegen-EMK-Konstante, $\omega$: Drehzahl.

Im stationären Zustand ($dI/dt = 0$):
$I = (U - K_e \cdot \omega) / R$

Motormoment: $M = K_t \cdot I$ (mit Drehmomentkonstante $K_t = K_e$
im SI-System).

H-Brücke: Vier Schalter (MOSFETs) ermöglichen Vorwärts, Rückwärts
und Bremsen. PWM auf den High-Side-FETs steuert die effektive
Spannung. Totzeit (Dead Time) zwischen High- und Low-Side-Schalten
verhindert Kurzschlüsse (Shoot-Through).

**Übung:**

1. Bestimme die Motorparameter ($R$, $K_e$) experimentell:
   Blockierter Motor → $R = U/I$. Leerlauf → $K_e = (U - R \cdot I_0)/\omega_0$.
   Dokumentiere Messwerte mit Einheiten.

2. Konfiguriere die MCPWM-Peripherie des ESP32-S3 für die H-Brücke:
   $f_{\text{PWM}} = 20\,\mathrm{kHz}$ (unhörbar), Dead Time $= 200\,\mathrm{ns}$.
   Verifiziere die PWM-Signale mit Oszilloskop.

3. Implementiere die vier Betriebsmodi: Vorwärts (PWM%), Rückwärts
   (PWM%), Bremsen (beide Low-Side aktiv), Freilauf (alle FETs aus).
   Teste mit verschiedenen Duty Cycles.

**Anwendung (AMR):**

Integriere die Motoransteuerung in die AMR-Softwarearchitektur:
`MotorDriver`-Klasse mit HAL-Abstraktion, Mutex-geschützter
Zugriff (da von PID-Task und Kommando-Task genutzt).

---

### W13–W14: Encoder & Drehzahlmessung

**Theorie:**

Inkrementalgeber (Quadrature Encoder) erzeugen zwei um 90° phasen-
verschobene Rechtecksignale (A und B). Aus der Flankenfolge ergibt
sich Drehrichtung und Position:

| A-Flanke | B-Zustand | Richtung  |
|----------|-----------|-----------|
| steigend | Low       | vorwärts  |
| steigend | High      | rückwärts |

Auflösungserhöhung (4× Decoding): Alle Flanken von A und B zählen →
4 Inkremente pro Encoder-Periode.

Drehzahlberechnung: Zwei Methoden:

- **Frequenzmessung:** $\omega = \frac{\Delta\text{Ticks}}{\text{CPR} \cdot \Delta t} \cdot 2\pi$.
  Gut bei hohen Drehzahlen.
- **Periodenmessung:** Zeitdauer zwischen zwei Flanken messen.
  Besser bei niedrigen Drehzahlen (höhere Auflösung).

ESP32-S3: Hardware-PCNT (Pulse Counter) Peripherie für
Encoder-Auswertung ohne CPU-Last.

**Übung:**

1. Konfiguriere den PCNT des ESP32-S3 für Quadrature Decoding (4×).
   Messe Ticks pro Radumdrehung und berechne die Distanz pro Tick.

2. Implementiere beide Drehzahl-Berechnungsmethoden. Vergleiche
   die Genauigkeit bei $v = 0{,}05\,\mathrm{m/s}$ (langsam) und
   $v = 0{,}5\,\mathrm{m/s}$ (schnell).

3. Implementiere einen Encoder-Diagnose-Modus: Prüfe auf fehlende
   Flanken, Signalstörungen (Glitches) und Zählerüberlauf.

**Anwendung (AMR):**

Integriere die Encoder-Auswertung in die Odometrie: PCNT → Ticks →
Radgeschwindigkeit → Forward Kinematics → Pose. Teste die
Odometrie-Genauigkeit auf einer kalibrierten Strecke ($5{,}000 \pm 0{,}005\,\mathrm{m}$).

---

### W15–W16: Geschlossener Regelkreis & Systemtest

**Theorie:**

Der vollständige Antriebsregelkreis integriert alle bisherigen
Komponenten:

```
 Soll-v    ┌─────────┐    PWM     ┌─────────┐    ω     ┌─────────┐   Ticks
───────────▶│  PID    │──────────▶│ H-Brücke│──────────▶│ Encoder │─────┐
            │ Regler  │           │ + Motor │           │ + PCNT  │     │
            └────▲────┘           └─────────┘           └─────────┘     │
                 │                                                      │
                 └────────────────── Ist-v ◀────────────────────────────┘
```

Systemidentifikation: Messe die Sprungantwort des geschlossenen
Regelkreises (Soll-Geschwindigkeit $0 \to 0{,}3\,\mathrm{m/s}$).
Bewertungskriterien:

- Anregelzeit $t_r$ (10 %–90 %): Wie schnell erreicht das System
  den Sollwert?
- Überschwingen $M_p$: Maximale Abweichung über den Sollwert hinaus
  ($M_p < 5\,\%$ anstreben).
- Einschwingzeit $t_s$ (innerhalb $\pm 2\,\%$): Wann bleibt das
  System stabil am Sollwert?
- Stationäre Genauigkeit: Abweichung im eingeschwungenen Zustand
  ($< 1\,\%$).

**Übung:**

1. Integriere PID-Regler (aus M3), H-Brücke (aus T2 W11) und
   Encoder (aus T2 W13) zum vollständigen Regelkreis. Messe und
   dokumentiere die Sprungantwort.

2. Teste Störungsunterdrückung: Bringe bei konstanter Soll-
   Geschwindigkeit eine manuelle Bremskraft auf. Messe, wie schnell
   und genau der Regler die Störung ausregelt.

3. Implementiere einen Biquad-Filter auf die Encoder-Drehzahl,
   um Quantisierungsrauschen zu glätten, ohne die Regelschleife
   zu verlangsamen (Phasenreserve beachten).

**Anwendung (AMR):**

Führe einen vollständigen Systemtest des AMR-Antriebs durch:
Sprungantwort, Rampenantwort, Störungstest, Langzeitstabilität
(30 Minuten Dauerlauf). Dokumentiere alle Ergebnisse als
Testprotokoll mit Messdiagrammen und Bewertung gegen die
Anforderungen.

---

## T3 — Systemintegration & V-Modell (W23–W28)

### Lernziel

Das Gesamtsystem nach ingenieurwissenschaftlicher Methodik
(VDI 2206 V-Modell) integrieren, testen und dokumentieren.

### W23–W24: Anforderungsmanagement & Systemspezifikation

**Theorie:**

Das V-Modell nach VDI 2206 strukturiert die Entwicklung
mechatronischer Systeme:

```
Anforderungen ──────────────────────────────────── Abnahmetest
       │                                                ▲
       ▼                                                │
  Systementwurf ────────────────────────── Integrationstest
       │                                          ▲
       ▼                                          │
  Komponentenentwurf ──────────── Komponententest
       │                                ▲
       ▼                                │
       └──────── Implementierung ───────┘
```

Linker Ast: Anforderungen verfeinern (Top-Down).
Rechter Ast: Testen und integrieren (Bottom-Up).
Jede Ebene links korrespondiert mit einer Testebene rechts.

Anforderungskategorien für den AMR:

- **Funktionale Anforderungen:** „Der AMR navigiert autonom zum
  Zielpunkt mit $< 50\,\mathrm{mm}$ Positionsfehler."
- **Nichtfunktionale Anforderungen:** „Die End-to-End-Latenz von
  Lidar-Messung bis Motorreaktion beträgt $< 50\,\mathrm{ms}$."
- **Randbedingungen:** „Der AMR verwendet ROS 2 Humble auf
  Raspberry Pi 5."

**Übung:**

1. Erstelle eine Anforderungsliste (REQ-ID, Beschreibung, Priorität,
   Verifikationsmethode) mit mindestens 15 Anforderungen für den AMR.
   Kategorisiere in funktional, nichtfunktional, Randbedingung.

2. Leite aus den Systemanforderungen Komponentenanforderungen ab:
   Welche Anforderungen hat der ESP32? Welche der Pi? Welche die
   Mechanik? Erstelle eine Traceability-Matrix.

3. Definiere Abnahmekriterien für drei kritische Anforderungen:
   Messverfahren, Toleranzen, Pass/Fail-Kriterien.

**Anwendung (AMR):**

Erstelle ein Anforderungsdokument (Lastenheft) für das AMR-Projekt
v3.0.0. Hinterlege im Repository unter `/docs/requirements/`.
Nutze als Basis für die Bachelorarbeit.

---

### W25–W26: Integration & Systemtest

**Theorie:**

Integration folgt einer Strategie — nicht dem Zufall:

- **Bottom-Up:** Einzelne Komponenten testen, dann schrittweise
  zusammenführen. Vorteil: Fehler lassen sich lokalisieren.
- **Top-Down:** Gesamtsystem mit Stubs aufbauen, dann Stubs durch
  reale Komponenten ersetzen. Vorteil: Frühes Systemverhalten.
- **Sandwich:** Kombination aus beiden.

Integrationsreihenfolge für den AMR:

1. ESP32 + Motortreiber + Encoder → Antriebstest
2. ESP32 + Lidar → Scandatenverifikation
3. ESP32 + micro-ROS-Agent + Pi → Kommunikationstest
4. Pi + SLAM + Navigation → Navigationstest
5. Gesamtsystem → Autonomietest

**Übung:**

1. Erstelle einen Integrations-Testplan: Für jeden Integrationsschritt
   definiere Testfälle, erwartete Ergebnisse und Abbruchkriterien.

2. Implementiere automatisierte Integrationstests: ROS-2-Launch-Test,
   der prüft, ob alle Nodes starten, Topics publiziert werden und
   TF-Tree konsistent ist.

3. Führe einen 60-Minuten-Dauertest durch: AMR fährt autonom eine
   Schleife. Logge alle Topics. Analysiere auf Speicherlecks,
   Temperaturanstieg, Kommunikationsfehler.

**Anwendung (AMR):**

Dokumentiere den Integrationsprozess als Testbericht nach
VDI 2206: Testaufbau, Durchführung, Ergebnisse, Abweichungsanalyse,
Maßnahmen. Einbindung in die Bachelorarbeit.

---

### W27–W28: Dokumentation & Projektabschluss

**Theorie:**

Technische Dokumentation ist kein Nachgedanke, sondern integraler
Bestandteil des Entwicklungsprozesses. Für die Bachelorarbeit und
das AMR-Projekt als Open-Source-Projekt ist sie besonders relevant.

Dokumentationsebenen:

- **Code-Dokumentation:** Doxygen (C++), docstrings (Python).
  Automatisierte API-Dokumentation.
- **Architekturdokumentation:** arc42-Template oder C4-Modell.
  Kontextdiagramm, Bausteinsicht, Laufzeitsicht.
- **Benutzer-/Betriebsdokumentation:** Setup-Anleitung, Konfiguration,
  Troubleshooting.
- **Wissenschaftliche Dokumentation:** Bachelorarbeit nach
  Hochschulvorgaben (WBH).

**Übung:**

1. Erstelle Doxygen-Kommentare für alle öffentlichen Funktionen
   der AMR-Firmware. Generiere die HTML-Dokumentation und prüfe
   auf Vollständigkeit.

2. Erstelle ein C4-Diagramm (Kontext → Container → Komponente)
   für die AMR-Systemarchitektur.

3. Schreibe eine Setup-Anleitung: Von leerem Raspberry Pi bis
   zum fahrenden AMR in reproduzierbaren Schritten.

**Anwendung (AMR):**

Kompiliere die gesamte Dokumentation im AMR-Repository:
README, ARCHITECTURE.md, TESTING.md, SETUP.md. Struktur als
Grundlage für die VDI-2206-konforme Bachelorarbeit.

---

## Fortschrittskontrolle

Jedes Modul endet mit einer Selbstbewertung:

| Kriterium                                               | Skala 1–5 |
|---------------------------------------------------------|-----------|
| Theorie verstanden und erklärbar (Fachgespräch-fähig)   | ☐         |
| Übungen eigenständig gelöst (kein Copy-Paste)           | ☐         |
| Anwendungsaufgabe im AMR-Projekt umgesetzt und getestet | ☐         |
| Ergebnisse dokumentiert (Git-Commit, Messprotokoll)     | ☐         |
| Querbezüge zu anderen Modulen hergestellt               | ☐         |

**Schwellenwert:** Mindestens 4/5 in jedem Kriterium, bevor das
nächste Modul beginnt.

**Meilensteine:**

| Woche | Meilenstein                                | Prüfkriterium                                          |
|-------|--------------------------------------------|--------------------------------------------------------|
| W08   | AMR fährt mit kalibrierter Odometrie       | Quadrattest: Endfehler $< 50\,\mathrm{mm}$             |
| W16   | PID-geregelte Motoren, Latenz dokumentiert | Sprungantwort: $M_p < 5\,\%$, $t_s < 500\,\mathrm{ms}$ |
| W22   | AMR navigiert autonom mit SLAM             | 3 Wegpunkte, Positionsfehler $< 100\,\mathrm{mm}$      |
| W28   | Systemtest bestanden, Doku komplett        | VDI-2206-Testbericht, Anforderungen erfüllt            |
| W32   | Bachelorarbeit-Entwurf fertig              | Kapitelstruktur, Methodik, Ergebnisse                  |

---

*Erstellt: Februar 2026 | Methodik: Bloch+Akademisch | Version: 1.0*
*Bezugsprojekt: AMR-Plattform v1.0.0 (https://github.com/unger-robotics)*
