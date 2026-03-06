# Handout: Architektur und Datenfluss eines KI-gestützten AMR

**Datum:** 21. Februar 2026
**Thema:** Konzeption, Datenfluss und Validierung eines Autonomen Mobilen Roboters (AMR)

---

## 1. Systemauslegung und Architektur

Industrielle AMR für den Kleinladungsträger-Transport (KLT) verursachen Hardwarekosten von $> 25.000\,\mathrm{EUR}$. Ein kosteneffizienter Systementwurf für $\sim 500\,\mathrm{EUR}$ erzwingt eine strikte Partitionierung der Rechenressourcen. Echtzeitkritische Regelkreise und rechenintensive High-Level-Navigation teilen wir auf dedizierte Hardware-Kerne auf.

Der Datenfluss durchläuft vier definierte Ebenen:

1. **Sensorik (Datenerfassung):** * **RPLIDAR A1:** Erfasst 2D-Scandaten mit einer Frequenz von $7,6\,\mathrm{Hz}$ bis zu einer Reichweite von $12\,\mathrm{m}$.
   * **IMX296 Kamera:** Liefert optische Rohdaten ($1456 \times 1088$ Pixel bei $15\,\mathrm{fps}$) über eine v4l2loopback-Bridge.
   * **Hall-Encoder:** Erfassen die Motorrotation über Quadratur-Dekodierung mit $\sim 748\,\mathrm{Ticks/Umdrehung}$.
2. **Edge-Computing (Lokale Verarbeitung):**
   * **Raspberry Pi 5:** Berechnet mittels ROS 2 (Nav2 und SLAM Toolbox) eine lokale Belegungskarte mit $5\,\mathrm{cm}$ Auflösung.
   * **Hailo-8L NPU:** Übernimmt die hardwarebeschleunigte Objekterkennung (YOLOv8), um die Host-CPU zu entlasten.
3. **Cloud-KI (Strategische Entscheidung):** * **Gemini API / Claude AI:** Empfängt aggregierte, semantische JSON-Daten (erkannte Objekte, Koordinaten). Plant übergeordnete Vermeidungsstrategien oder Sprachausgaben bei komplexen Hindernissen (z. B. "Gabelstapler im Weg").
4. **Aktorik (Physische Ausführung):** * **XIAO ESP32-S3:** Core 1 führt die PID-Motorregelung deterministisch bei $50\,\mathrm{Hz}$ aus, während Core 0 die micro-ROS-Kommunikation abwickelt.
   * **Cytron MDD3A:** Wandelt Stellgrößen in $20\,\mathrm{kHz}$ PWM-Signale für die JGA25-370 Motoren um.

---

## 2. Kinematik und Regelung

Um die translatorischen Vorgaben in Rotationsgeschwindigkeiten für den Differentialantrieb zu übersetzen, leiten wir die Zielwerte über die Inverskinematik her:

$$\omega_l = \frac{v - \omega \cdot \frac{L}{2}}{r}$$
$$\omega_r = \frac{v + \omega \cdot \frac{L}{2}}{r}$$

**Systemparameter:**
* Zielgeschwindigkeit ($v$): $0,4\,\mathrm{m/s}$ (Regulated Pure Pursuit Controller).
* Spurbreite ($L$): $178\,\mathrm{mm}$.
* Radradius ($r$): $32,835\,\mathrm{mm}$ (Kalibrierter Raddurchmesser: $65,67\,\mathrm{mm}$).

---

## 3. Validierungsdaten und Evidenz

Das System erreicht die definierten Zielvorgaben durch systematische Kalibrierung:

* **Regelungsgüte:** Die PID-Regelschleife auf dem ESP32 erreicht die geforderten $50\,\mathrm{Hz}$ mit einem Jitter von $< 2\,\mathrm{ms}$.
* **Odometrie:** Die systematische UMBmark-Kalibrierung senkte Translations- und Rotationsfehler um den Faktor 10 bis 20.
* **Kartierung:** Der absolute Trajektorienfehler (ATE) beim SLAM-Mapping liegt bei $0,16\,\mathrm{m}$ (Referenz/Ziel: $< 0,20\,\mathrm{m}$).
* **ArUco-Docking:** Der laterale Versatz beim Andocken an eine Ladestation beträgt $1,3\,\mathrm{cm}$ (Toleranzgrenze: $< 2\,\mathrm{cm}$).

---

## 4. Randbedingungen und Limitierungen

* **Kommunikationsbandbreite:** Die serielle UART-Verbindung ($115200\,\mathrm{Baud}$) nutzt das XRCE-DDS-Protokoll. Die Maximum Transmission Unit (MTU) ist auf $512\,\mathrm{Bytes}$ limitiert. Fragmentierung über *Reliable QoS* ist zwingend erforderlich, um größere Pakete (z. B. Odometrie-Kovarianzmatrizen) ohne Datenverlust zu übertragen.
* **Cloud-Abhängigkeit:** Die strategische Objektauswertung setzt eine lückenlose Netzwerkverbindung voraus. Ein Verbindungsabbruch zwingt das System auf die rein lokale, reaktive Hindernisvermeidung des Nav2-Stacks zurück.
