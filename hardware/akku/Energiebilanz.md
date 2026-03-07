### Energiebilanz und Laufzeitberechnung

**Randbedingungen:**

- Akkupack: Samsung INR18650-35E, 3S1P (NCA-Zellchemie)
- Kapazitätsreferenz: **3.350 mAh** (Minimalkapazität laut Datenblatt;
  der typische Wert von 3.500 mAh dient nicht als Berechnungsgrundlage)
- Max. Dauerentladestrom: **8 A** (der häufig zitierte Wert von 13 A
  gilt ausschließlich für Impulsbelastung, nicht für Dauerbetrieb)
- Messinstrument: INA260 (High-Side, 1,25 mA / 1,25 mV Auflösung)
- Empirische Referenzmessung: Labornetzteil bei 12 V

---

**Beobachtung:** Die empirische Messung am Labornetzteil verankert den realen
Energiebedarf des Gesamtsystems. Bei 12 V und 1 A ergibt sich eine statische
Leistungsaufnahme von 12 W im Stillstand – Kamera, LiDAR, Raspberry Pi 5 und
Hailo-8L-Inferenz aktiv, Antrieb abgeschaltet.

Die folgende Aufschlüsselung ordnet den Subsystemen ihre typischen Anteile zu
(Quelle: Datenblätter der Einzelkomponenten, gerundet):

| Subsystem | Spannung | Strom (typ.) | Leistung |
|---|---|---|---|
| Raspberry Pi 5 (aktiv, keine GPU-Last) | 5 V (via Regler) | 800 mA | 4,0 W |
| Hailo-8L (Inferenz, YOLOv8n) | 5 V (via Pi) | 400 mA | 2,0 W |
| RPLIDAR A1 (Scan-Betrieb) | 5 V | 250 mA | 1,3 W |
| ESP32-S3 (aktiv, micro-ROS) | 3,3 V (via Regler) | 150 mA | 0,5 W |
| CSI-Kamera (30 fps) | 3,3 V (via Pi) | 200 mA | 0,7 W |
| IMU, INA260, PCA9685 (I²C-Peripherie) | 3,3 V | 50 mA | 0,2 W |
| Reglerverluste (geschätzt, η ≈ 85 %) | – | – | 2,3 W |
| **Summe Grundlast (Stillstand)** | – | – | **≈ 11 W** |

**Limitierung:** Die gemessenen 12 W am Labornetzteil liegen geringfügig über
der Komponentensumme von 11 W. Die Differenz erklärt sich durch I²C-Pullup-
Verluste, LED-Ruheströme und Messtoleranz des Netzteils. Für die
Laufzeitberechnung gilt der konservativere Messwert von **12 W**.

---

**Daten:** Der 3S1P-Pack erreicht eine Nennspannung von 10,8 V (3 × 3,6 V)
bei einer garantierten Minimalkapazität von 3.350 mAh (3,35 Ah). Die nominale
Gesamtenergie berechnet sich zu:

$$
E_{\mathrm{nom}} = 10{,}8\,\mathrm{V} \cdot 3{,}35\,\mathrm{Ah} = 36{,}18\,\mathrm{Wh}
$$

**Regel:** Li-Ion-Zellen mit NCA-Kathode degradieren bei tiefer Entladung nahe
der Schlussspannung von 2,65 V/Zelle unverhältnismäßig schnell. Samsung empfiehlt
für Robotikanwendungen (Kategorie „E-Bike/E-Scooter") ein nutzbares Entladefenster
von SoC 90 % bis 10 %, entsprechend 80 % der Nennkapazität:

$$
E_{\mathrm{nutz}} = 36{,}18\,\mathrm{Wh} \cdot 0{,}80 = 28{,}94\,\mathrm{Wh}
$$

Zum Vergleich: Bei Verwendung des typischen Kapazitätswerts (3.500 mAh) ergäbe
sich $E_{\mathrm{nutz}} = 10{,}8 \cdot 3{,}50 \cdot 0{,}80 = 30{,}24\,\mathrm{Wh}$ –
die Differenz von 1,3 Wh entspricht ca. 6 Minuten Laufzeit im Fahrbetrieb.

---

**Anwendung:** Die Laufzeit $t$ ergibt sich aus dem Quotienten der nutzbaren
Energie und der mittleren Systemleistung:

$$
t = \frac{E_{\mathrm{nutz}}}{P_{\mathrm{sys}}}
$$

*Stillstand* – Der Roboter verarbeitet kontinuierlich Sensordaten und führt die
KI-Pipeline (Hailo-8L) aus, navigiert jedoch nicht. Die Systemleistung entspricht
der empirisch gemessenen Grundlast von 12 W:

$$
t_{\mathrm{still}} = \frac{28{,}94\,\mathrm{Wh}}{12\,\mathrm{W}} \approx 2{,}41\,\mathrm{h} \approx 2\,\mathrm{h}\;25\,\mathrm{min}
$$

*Fahrbetrieb* – Die DC-Motoren (JGA25-370) des Differentialantriebs addieren bei
einer Fahrgeschwindigkeit von 0,4 m/s erfahrungsgemäß 3 W bis 5 W zur Grundlast.
Bei einer gemittelten Gesamtleistung von 16 W verkürzt sich die Laufzeit auf:

$$
t_{\mathrm{fahr}} = \frac{28{,}94\,\mathrm{Wh}}{16\,\mathrm{W}} \approx 1{,}81\,\mathrm{h} \approx 1\,\mathrm{h}\;49\,\mathrm{min}
$$

*Zusammenfassung der Szenarien:*

| Betriebsmodus | Mittlere Leistung | Laufzeit (konservativ) |
|---|---|---|
| Standby (Pi + ESP32 + Sensorik, kein Hailo) | 6 W | 4 h 49 min |
| Stillstand (volle Pipeline, kein Antrieb) | 12 W | 2 h 25 min |
| Fahrbetrieb (0,4 m/s, Navigation aktiv) | 16 W | 1 h 49 min |
| Maximallast (Servos + Antrieb + Compute) | 22 W | 1 h 19 min |

---

**Konsequenz – Stromlimits:** Der maximale Dauerentladestrom der
Samsung INR18650-35E beträgt laut Datenblatt **8 A**. Die geschätzten
Spitzenlasten des AMR beim Anfahrmoment der Motoren liegen bei 2 A bis 3 A.
Der Betriebspunkt liegt damit dauerhaft unter 40 % des zulässigen Dauerstroms –
thermisch unkritisch. Selbst bei 8 A Dauerlast bleiben laut Entladeraten-
Kennlinie noch 92 % der Nennkapazität nutzbar.

Der Impulsstrom von 13 A steht ausschließlich für kurzzeitige Spitzen zur
Verfügung (z. B. gleichzeitiges Anfahren beider Motoren unter Volllast). Eine
Dauerbelastung mit 13 A ist **nicht zulässig** und führt zu thermischer
Degradation der Zelle.

**Konsequenz – Spannungsüberwachung:** Das mehrstufige Schutzkonzept in der
Firmware (`config_sensors.h`, Namespace `amr::battery`) implementiert vier
Abschaltschwellen:

1. Soft-Warnung bei $\leq 10{,}0\,\mathrm{V}$ (Packspannung)
2. Motor-Abschaltung bei $\leq 9{,}5\,\mathrm{V}$
3. System-Shutdown bei $\leq 9{,}0\,\mathrm{V}$
4. BMS-Hardware-Trennung bei $\leq 7{,}5\,\mathrm{V}$

Die primäre Spannungsmessung erfolgt über den INA260 (Busspannungsregister,
1,25 mV Auflösung, 0,1 % Genauigkeit). Als redundante Messung dient der
ESP32-S3 ADC mit Spannungsteiler (100 kΩ / 27 kΩ). Die Stufe-1-Warnung löst
zusätzlich über den Alert-Pin (Open-Drain) des INA260 aus – diese
Hardware-Signalisierung funktioniert unabhängig von der Firmware-Schleife.

**Validierung:** Die Coulomb-Zählung über den INA260 (Stromintegration mit
$\Delta t$ = 500 ms bei 2 Hz Abfragerate) liefert eine laufende SoC-Schätzung.
Da reine Stromintegration über die Zeit driftet, erfolgt eine periodische
Korrektur anhand der OCV-SoC-Kennlinie (Open Circuit Voltage) bei Lastpausen
($\geq 30\,\mathrm{s}$ Relaxationszeit).
