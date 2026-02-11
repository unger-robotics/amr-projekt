# 06 -- Thesis-Aenderungsliste: Hardware-Alignment

**Dokumenttyp:** Aenderungsliste (Source of Truth: `config.h`, `hardware-setup.md`, `kosten.md`)
**Stand:** 2026-02-11
**Zweck:** Dokumentation aller Stellen in der Bachelorarbeit, die nicht mit der tatsaechlich verbauten Hardware uebereinstimmen

---

## Uebersichtstabelle

| Kapitel | Datei (kombiniert) | Anzahl Aenderungen | Prioritaet |
|---|---|---|---|
| Kap. 1 -- Einleitung | `kapitel_01_einleitung.md` | 3 | Hoch |
| Kap. 2 -- Grundlagen | `kapitel_02_grundlagen.md` | 5 | Mittel |
| Kap. 3 -- Anforderungsanalyse | `kapitel_03_anforderungsanalyse.md` | 8 | Hoch |
| Kap. 4 -- Systemkonzept | `kapitel_04_systemkonzept.md` | 22 | Kritisch |
| Kap. 5 -- Implementierung | `kapitel_05_implementierung.md` | 15 | Kritisch |
| Kap. 6 -- Validierung | `kapitel_06_validierung.md` | 6 | Hoch |
| Kap. 7 -- Fazit | `kapitel_07_fazit.md` | 4 | Mittel |
| **Gesamt** | | **63** | |

---

## Diskrepanz-Referenztabelle

Die folgende Tabelle fasst die systematischen Abweichungen zusammen, die sich durch die gesamte Arbeit ziehen:

| ID | Parameter | Thesis (FALSCH) | Hardware (KORREKT) | Betroffene Kapitel |
|---|---|---|---|---|
| D01 | Raddurchmesser | 64 mm (r = 32 mm) | 65 mm (r = 32,5 mm) | 1, 2, 3, 4, 5, 6, 7 |
| D02 | Spurbreite | 145 mm | 178 mm | 1, 2, 3, 4, 5, 6, 7 |
| D03 | Encoder Ticks/Rev | 1440 (Quadratur A+B) | 374,3 / 373,6 (A-only Hall) | 4, 5 |
| D04 | Encoder-Typ | Quadratur (Kanal A + Kanal B) | A-only (Phase B fuer Richtung ungenutzt) | 4, 5 |
| D05 | MCU / SoC | ESP32 / Xtensa LX6 / esp32dev | XIAO ESP32-S3 / Xtensa LX7 / seeed_xiao_esp32s3 | 3, 4, 5 |
| D06 | GPIO-Pins | GPIO 18,19,22,23,25,26,32,33 | D0-D10 (XIAO Pinout) | 4, 5 |
| D07 | PWM-Kanaele | 0,1,2,3 (sequentiell) | 1,0,3,2 (getauscht) + CH4 LED | 4, 5 |
| D08 | Motortreiber | generische H-Bruecke | Cytron MDD3A (Dual-PWM, kein DIR-Pin) | 4, 5 |
| D09 | Motor-Deadzone | nicht vorhanden | PWM_DEADZONE = 35 | 4, 5 |
| D10 | LiDAR | Consumer-LiDAR / implizit LDROBOT STL-19 | RPLIDAR A1 (12 m Reichweite, SLAMTEC) | 3, 5, 6, 7 |
| D11 | Kamera | monokulare Consumer-Kamera ueber USB | RPi Global Shutter Camera + 6 mm CS-Mount ueber CSI | 4, 5 |
| D12 | Akku | nicht spezifiziert / implizit Li-Ion | 4S LiFePO4 (Cottcell IFR26650, 12,8 V nom.) | 4, 5 |
| D13 | Kosten (Kern) | implizit ~250 EUR | 482,48 EUR (beschafft) + ~31 EUR (vorhanden) | 3, 5 |
| D14 | Konversionsfaktor | 0,1396 mm/Tick (aus 1440 Ticks, 64 mm) | 0,546 mm/Tick (aus ~374 Ticks, 65 mm) | 2, 4 |

---

## Kapitel 1 -- Einleitung

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 1.1 | kapitel_01_einleitung.md | 43 | "Der in dieser Arbeit entwickelte AMR weist mit einer Spurbreite von 145 mm und einem Radradius von 32 mm vergleichsweise kleine geometrische Abmessungen auf" | "Der in dieser Arbeit entwickelte AMR weist mit einer Spurbreite von 178 mm und einem Radradius von 32,5 mm vergleichsweise kleine geometrische Abmessungen auf" | D01, D02 |
| 1.2 | kapitel/01_2_zielsetzung.md | 23 | "mit einer Spurbreite von 145 mm und einem Radradius von 32 mm" | "mit einer Spurbreite von 178 mm und einem Radradius von 32,5 mm" | D01, D02 |
| 1.3 | kapitel_01_einleitung.md | 43 | "was ihn gemaess Borenstein et al. besonders anfaellig fuer Orientierungsfehler macht" | Hinweis: Bei 178 mm Spurbreite ist die Anfaelligkeit geringer als bei 145 mm. Argumentation abschwaechen oder Vergleichswert anpassen. | D02 |

---

## Kapitel 2 -- Grundlagen

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 2.1 | kapitel_02_grundlagen.md | 54 | "Der Konversionsfaktor c_m = pi * D / (n * C_e) rechnet dabei die Encoder-Pulse in lineare Raddistanzen um" | Formel korrekt (allgemein), aber der spaeter in Kap. 4 berechnete Wert 0,1396 mm/Tick basiert auf falschen Eingabewerten. Formel hier anpassen fuer Konsistenz mit den korrekten Werten (D = 65 mm, C_e = 374 Ticks -> c_m = 0,546 mm/Tick). | D14 |
| 2.2 | kapitel_02_grundlagen.md | 31 | "Albarran et al. beschreiben den DDRC-ESP32 [...] Die Wahl des ESP32-WROOM-32E mit seinem Xtensa Dual-Core LX6" | Keine Aenderung noetig -- dies beschreibt die Referenzplattform von Albarran, nicht die eigene Hardware. Aber in Kap. 3/4 muss klargestellt werden, dass der eigene Roboter einen ESP32-S3 (LX7) verwendet. | D05 |
| 2.3 | kapitel_02_grundlagen.md | 82 | Implizite Annahme von Raddurchmesser D und Spurbreite b in Odometrie-Fehlermodell-Diskussion | Keine woertliche Aenderung, aber Konsistenz mit Kap. 4/5 pruefen, wo D = 64 mm und b = 145 mm verwendet werden. | D01, D02 |
| 2.4 | kapitel_02_grundlagen.md | 126 | "Phasenquadratur-Encoder -- sowohl die Richtungserkennung als auch eine Vervierfachung der effektiven Aufloesung ermoeglichen" | Dies beschreibt Encoder allgemein (korrekt als Grundlagentext). Aber in Kap. 4/5 wird faelschlich angenommen, dass der eigene Roboter Quadratur-Encoder verwendet. Hinweis auf A-only-Konfiguration als Variante einfuegen. | D04 |
| 2.5 | kapitel_02_grundlagen.md | 33 | "Abaza praesentiert [...] einen LDROBOT STL-19 Lidar" | Keine Aenderung noetig -- beschreibt Abazas Plattform. Aber klarstellen, dass der eigene Roboter einen RPLIDAR A1 verwendet (Abgrenzung in Kap. 3/5). | D10 |

---

## Kapitel 3 -- Anforderungsanalyse

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 3.1 | kapitel_03_anforderungsanalyse.md | 55 | "Der Radradius betraegt 32 Millimeter, die Spurbreite 145 Millimeter." | "Der Radradius betraegt 32,5 Millimeter, die Spurbreite 178 Millimeter." | D01, D02 |
| 3.2 | kapitel_03_anforderungsanalyse.md | 55 | "Diese Parameter gehen als Konstanten in die Vorwaerts- und Inverskinematik ein" | Wert anpassen, Argumentation zur Anfaelligkeit fuer Orientierungsfehler neu bewerten (178 mm ist weniger empfindlich als 145 mm). | D02 |
| 3.3 | kapitel_03_anforderungsanalyse.md | 39 | "Die vorliegende Arbeit verwendet den ESP32-S3, der dieselbe Dual-Core-Architektur bietet" | Text erwaehnt ESP32-S3 korrekt! Allerdings wird in Kap. 4 dann faelschlich auf LX6 und esp32dev zurueckgegriffen. Hier konsistent mit ESP32-S3 / LX7 / XIAO bleiben. | D05 |
| 3.4 | kapitel_03_anforderungsanalyse.md | 59 | "Consumer-LiDAR-Sensor eingesetzt, vergleichbar dem LDROBOT STL-19" | "RPLIDAR A1 von SLAMTEC eingesetzt, ein Consumer-LiDAR mit 12 m Reichweite und 360-Grad-Scanbereich" | D10 |
| 3.5 | kapitel_03_anforderungsanalyse.md | 79 | "Fahrzeuge mit kleiner Spurbreite wie der vorliegende AMR mit 145 Millimetern" | "Fahrzeuge mit kleiner Spurbreite wie der vorliegende AMR mit 178 Millimetern" | D02 |
| 3.6 | kapitel/03_2_randbedingungen.md | 25 | "Der Radradius betraegt 32 Millimeter, die Spurbreite 145 Millimeter." | "Der Radradius betraegt 32,5 Millimeter, die Spurbreite 178 Millimeter." | D01, D02 |
| 3.7 | kapitel/03_2_randbedingungen.md | 29 | "Consumer-LiDAR-Sensor eingesetzt, vergleichbar dem LDROBOT STL-19" | "RPLIDAR A1 von SLAMTEC eingesetzt" | D10 |
| 3.8 | kapitel/03_4_nichtfunktionale_anforderungen.md | 7 | "vorliegende AMR mit 145 Millimetern" | "vorliegende AMR mit 178 Millimetern" | D02 |

---

## Kapitel 4 -- Systemkonzept und Entwurf

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 4.1 | kapitel_04_systemkonzept.md | 110 | "Auswertung der Quadratur-Encoder beider Antriebsraeder" | "Auswertung der Hall-Encoder beider Antriebsraeder (A-only Konfiguration)" | D04 |
| 4.2 | kapitel_04_systemkonzept.md | 157 | "mit dem Radradius R = 32 mm und der Spurbreite L = 145 mm" | "mit dem Radradius R = 32,5 mm und der Spurbreite L = 178 mm" | D01, D02 |
| 4.3 | kapitel_04_systemkonzept.md | 194 | "Der Radradius betraegt 32 mm und die Spurbreite [...] ist mit 145 mm festgelegt" | "Der Radradius betraegt 32,5 mm und die Spurbreite [...] ist mit 178 mm festgelegt" | D01, D02 |
| 4.4 | kapitel_04_systemkonzept.md | 194 | "Die vergleichsweise kleine Spurbreite ergibt sich aus den raeumlichen Anforderungen" | Bei 178 mm ist die Spurbreite groesser. Argumentation anpassen. | D02 |
| 4.5 | kapitel_04_systemkonzept.md | 208 | "Die Motoren werden ueber eine H-Bruecken-Schaltung angesteuert, die jeweils zwei PWM-Signale pro Motor empfaengt" | "Die Motoren werden ueber den Cytron MDD3A Dual-Motortreiber im Dual-PWM-Modus angesteuert, der jeweils zwei PWM-Signale pro Motor empfaengt" | D08 |
| 4.6 | kapitel_04_systemkonzept.md | 208 | "ist eine Pegelanpassung (Level Shifting) zwischen den Subsystemen erforderlich" | Der Cytron MDD3A akzeptiert Logikpegel ab 1,7 V. Keine Pegelanpassung erforderlich bei 3,3 V GPIO. Satz streichen oder korrigieren. | D08 |
| 4.7 | kapitel_04_systemkonzept.md | 216-223 | GPIO-Pin-Tabelle mit GPIO 18, 19, 22, 23, 25, 26, 32, 33 | Ersetzen durch XIAO-Pinout: D0-D3 (Motor), D6/D7 (Encoder), D4/D5 (I2C), D8/D9 (Servo), D10 (LED/MOSFET) | D06 |
| 4.8 | kapitel_04_systemkonzept.md | 229 | "Die Aufloesung der eingesetzten Encoder betraegt 1440 Ticks pro Motorwellenumdrehung" | "Die Aufloesung der eingesetzten Hall-Encoder betraegt ca. 374 Ticks pro Radumdrehung (A-only Konfiguration, 374,3 links / 373,6 rechts)" | D03 |
| 4.9 | kapitel_04_systemkonzept.md | 229 | "Fuer den AMR ergibt sich mit D = 64 mm und C_e = 1440 Ticks ein Konversionsfaktor von c_m = 0,1396 mm pro Tick" | "Fuer den AMR ergibt sich mit D = 65 mm und C_e = 374 Ticks ein Konversionsfaktor von c_m = 0,546 mm pro Tick" | D01, D03, D14 |
| 4.10 | kapitel_04_systemkonzept.md | 229 | "inkrementelle optische Encoder mit Quadratursignal. Jeder Encoder liefert zwei um 90 Grad phasenversetzte Rechtecksignale (Kanal A und Kanal B)" | "Hall-Encoder (JGA25-370). Im aktuellen Design wird nur Phase A verwendet (A-only Konfiguration); Phase B bleibt isoliert. Die Drehrichtung wird aus der PWM-Ansteuerung abgeleitet." | D04 |
| 4.11 | kapitel_04_systemkonzept.md | 231 | "auf den GPIO-Pins 18 (links, Kanal A) und 22 (rechts, Kanal A) erfasst" | "auf den XIAO-Pins D6 (links, Phase A) und D7 (rechts, Phase A) erfasst" | D06 |
| 4.12 | kapitel_04_systemkonzept.md | 233 | "Richtungserkennung erfolgt innerhalb der ISR durch Vergleich der Logikpegel beider Encoder-Kanaele" | "Die Drehrichtung wird nicht ueber den Encoder bestimmt, sondern aus der aktuellen PWM-Ansteuerungsrichtung abgeleitet (A-only Betrieb)." | D04 |
| 4.13 | kapitel_04_systemkonzept.md | 237 | "Kombination aus Differentialantrieb mit Castor-Stuetzrad, ESP32-basierter Motorsteuerung mit H-Bruecke und inkrementellen Quadratur-Encodern" | "Kombination aus Differentialantrieb mit Castor-Stuetzrad, XIAO ESP32-S3-basierter Motorsteuerung mit Cytron MDD3A (Dual-PWM) und Hall-Encodern (A-only)" | D04, D05, D08 |
| 4.14 | kapitel_04_systemkonzept.md | 237 | "Die Empfindlichkeit der kleinen Spurbreite von 145 mm" | "Die Empfindlichkeit der Spurbreite von 178 mm" | D02 |
| 4.15 | kapitel_04_systemkonzept.md | 251 | "Der Xtensa LX6 Dual-Core Prozessor" | "Der Xtensa LX7 Dual-Core Prozessor" | D05 |
| 4.16 | kapitel_04_systemkonzept.md | 302 | "Dabei bezeichnen *r* = 0,032 m den Radradius und *b* = 0,145 m die Spurbreite" | "Dabei bezeichnen *r* = 0,0325 m den Radradius und *b* = 0,178 m die Spurbreite" | D01, D02 |
| 4.17 | kapitel_04_systemkonzept.md | 335 | "maximalen Laserreichweite von 12 m" | Korrekt fuer RPLIDAR A1 (12 m). Keine Aenderung noetig, aber ggf. RPLIDAR A1 namentlich erwaehnen. | D10 |
| 4.18 | kapitel_04_systemkonzept.md | 343 | "Die relativ kleine Spurbreite des AMR von 145 mm" | "Die Spurbreite des AMR von 178 mm" | D02 |
| 4.19 | kapitel_04_systemkonzept.md | 356 | "Kalibrierung [...] Spurbreite 145 mm" (in UMBmark-Abschnitt) | "Spurbreite 178 mm" | D02 |
| 4.20 | kapitel/04_2_gesamtsystemarchitektur.md | 9 | "Auswertung der Quadratur-Encoder" | "Auswertung der Hall-Encoder (A-only)" | D04 |
| 4.21 | kapitel/04_4_software_architektur.md | 13 | "Der Xtensa LX6 Dual-Core Prozessor" | "Der Xtensa LX7 Dual-Core Prozessor" | D05 |
| 4.22 | kapitel/04_3_mechanik_elektronik.md | 31-38 | GPIO-Pin-Tabelle (GPIO 18-33) | Ersetzen durch XIAO D0-D10 Pinout | D06 |

---

## Kapitel 5 -- Implementierung

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 5.1 | kapitel_05_implementierung.md | 9 | Referenzen auf Spurbreite 145 mm im Hardwareaufbau-Kontext | Spurbreite 178 mm | D02 |
| 5.2 | kapitel_05_implementierung.md | 15 | Referenzen auf GPIO 18, 19, 22, 23 fuer Encoder | XIAO-Pins D6, D7 fuer Encoder (A-only) | D06, D04 |
| 5.3 | kapitel_05_implementierung.md | 17, 21, 23 | Referenzen auf H-Bruecke und generischen Motortreiber | Cytron MDD3A im Dual-PWM-Modus | D08 |
| 5.4 | kapitel_05_implementierung.md | 21 | GPIO-Pins 25, 26, 32, 33 fuer Motoransteuerung | XIAO-Pins D0, D1, D2, D3 fuer Motoransteuerung | D06 |
| 5.5 | kapitel_05_implementierung.md | 53 | "Pegelanpassung zwischen ESP32 und H-Bruecke" | Cytron MDD3A akzeptiert 3,3 V Logikpegel direkt. Keine Pegelanpassung noetig. | D08 |
| 5.6 | kapitel_05_implementierung.md | 71 | Referenz auf LX6 CPU-Architektur | LX7 CPU-Architektur (ESP32-S3) | D05 |
| 5.7 | kapitel_05_implementierung.md | 85, 105, 111 | Referenzen auf Quadratur-Encoder mit Kanal A und Kanal B | A-only Hall-Encoder; Phase B isoliert; Drehrichtung aus PWM abgeleitet | D04 |
| 5.8 | kapitel_05_implementierung.md | 93 | Radradius 32 mm in Firmware-Beschreibung | Radradius 32,5 mm | D01 |
| 5.9 | kapitel_05_implementierung.md | 119 | Spurbreite 145 mm in Firmware-Beschreibung | Spurbreite 178 mm | D02 |
| 5.10 | kapitel_05_implementierung.md | 141 | Referenz auf 145 mm Spurbreite in Kinematik-Beschreibung | 178 mm | D02 |
| 5.11 | kapitel_05_implementierung.md | 226 | Encoder-Ticks-Berechnung basierend auf 1440 Ticks | 374,3 / 373,6 Ticks (A-only Hall-Encoder) | D03 |
| 5.12 | kapitel_05_implementierung.md | 230-236 | "DiffDriveKinematics kinematics(0.032, 0.145);" | "DiffDriveKinematics kinematics(0.0325, 0.178);" -- Werte muessen config.h entsprechen | D01, D02 |
| 5.13 | kapitel_05_implementierung.md | 288 | Referenz auf Consumer-LiDAR | RPLIDAR A1 namentlich benennen | D10 |
| 5.14 | kapitel_05_implementierung.md | 322 | Referenz auf Quadratur-Encoder in Systemintegration | Hall-Encoder (A-only) | D04 |
| 5.15 | kapitel_05_implementierung.md | 348-362 | Kostenangaben ueberpruefen | Gesamtkosten 482,48 EUR (beschafft), ~513 EUR inkl. vorhandener Teile | D13 |

---

## Kapitel 6 -- Validierung und Testergebnisse

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 6.1 | kapitel_06_validierung.md | 55 | "bei einem Radradius von 32 mm einer Radwinkelgeschwindigkeit von 12,5 rad/s" | "bei einem Radradius von 32,5 mm einer Radwinkelgeschwindigkeit von 12,3 rad/s" (0,4 / 0,0325 = 12,31) | D01 |
| 6.2 | kapitel_06_validierung.md | 67-71 | Spurbreite 145 mm in UMBmark-Auswertung | Spurbreite 178 mm -- alle UMBmark-Berechnungen mit 178 mm durchfuehren | D02 |
| 6.3 | kapitel_06_validierung.md | 69 | Raddurchmesser-basierte Berechnungen im UMBmark-Kontext | Raddurchmesser 65 mm statt 64 mm | D01 |
| 6.4 | kapitel_06_validierung.md | 259 | Referenz auf 145 mm Spurbreite in Navigationsvalidierung | 178 mm Spurbreite | D02 |
| 6.5 | kapitel_06_validierung.md | 275, 287 | "Consumer-LiDAR" ohne Namensnennung | RPLIDAR A1 namentlich benennen | D10 |
| 6.6 | kapitel_06_validierung.md | 285 | "monokulare Consumer-Kamera ohne Tiefensensor" | "Raspberry Pi Global Shutter Camera (Sony IMX296) mit 6 mm CS-Mount-Objektiv ueber CSI" -- nicht USB, sondern CSI | D11 |

---

## Kapitel 7 -- Fazit und Ausblick

| Nr | Datei | Zeile(n) | IST-Text (Zitat) | SOLL-Text | Diskrepanz-ID |
|---|---|---|---|---|---|
| 7.1 | kapitel_07_fazit.md | 21 | Referenz auf 145 mm Spurbreite im Fazit | 178 mm Spurbreite | D02 |
| 7.2 | kapitel_07_fazit.md | 49 | Referenz auf Raddurchmesser/Radradius im Kontext der Kalibrierungsergebnisse | Radradius 32,5 mm / Raddurchmesser 65 mm | D01 |
| 7.3 | kapitel_07_fazit.md | 53 | "Consumer-LiDAR" | RPLIDAR A1 namentlich benennen | D10 |
| 7.4 | kapitel_07_fazit.md | 63 | Kostenangaben im Fazit ueberpruefen | Gesamtkosten 482,48 EUR (beschafft) | D13 |

---

## Zusammenfassung

### Gesamtstatistik

| Kategorie | Anzahl Einzelaenderungen |
|---|---|
| Raddurchmesser / Radradius (D01) | 12 |
| Spurbreite (D02) | 18 |
| Encoder Ticks/Rev (D03) | 3 |
| Encoder-Typ Quadratur -> A-only (D04) | 8 |
| MCU ESP32 LX6 -> ESP32-S3 LX7 (D05) | 5 |
| GPIO-Pins (D06) | 5 |
| PWM-Kanaele (D07) | 1 |
| Motortreiber H-Bruecke -> Cytron MDD3A (D08) | 5 |
| Deadzone (D09) | 0 (in Thesis nicht erwaehnt, muss ergaenzt werden) |
| LiDAR-Typ (D10) | 6 |
| Kamera-Typ/Anschluss (D11) | 2 |
| Akku-Typ (D12) | 1 |
| Kosten (D13) | 2 |
| Konversionsfaktor (D14) | 2 |
| **Gesamt** | **63** (+ Deadzone-Ergaenzung) |

### Kritische Stellen (hoechste Prioritaet)

Die folgenden Aenderungen sind **inhaltskritisch**, da sie numerische Berechnungen und Validierungsergebnisse betreffen:

1. **Kinematik-Instanziierung** (5.12): `DiffDriveKinematics kinematics(0.032, 0.145)` muss zu `(0.0325, 0.178)` werden -- falsche Werte invalidieren alle Odometrie- und UMBmark-Ergebnisse.

2. **UMBmark-Auswertung** (6.2, 6.3): Alle Kalibrierungsberechnungen in Kapitel 6 verwenden die falschen geometrischen Parameter. Die Korrekturfaktoren E_d und E_b muessen mit den korrekten Werten (r = 32,5 mm, b = 178 mm) neu berechnet werden.

3. **Encoder-Aufloesung und Konversionsfaktor** (4.8, 4.9): Der Konversionsfaktor aendert sich von 0,1396 mm/Tick auf 0,546 mm/Tick -- ein Faktor ~4. Dies beeinflusst die gesamte Odometrie-Praezisionsdiskussion.

4. **Encoder-Typ** (4.10, 4.12): Die Beschreibung der Quadratur-Dekodierung mit Richtungserkennung ueber A/B-Vergleich ist fuer die A-only-Konfiguration falsch und muss grundlegend umgeschrieben werden.

5. **GPIO-Pin-Tabelle** (4.7, 4.22): Die gesamte Pin-Zuordnungstabelle in Kapitel 4.3 muss durch das XIAO-Pinout ersetzt werden.

### Hinweis zu Einzelabschnitten

Die Einzelabschnittsdateien in `bachelorarbeit/kapitel/` enthalten dieselben Texte wie die kombinierten Kapiteldateien. Aenderungen muessen in **beiden** Dateien durchgefuehrt werden, um Konsistenz sicherzustellen. Die relevanten Einzelabschnittsdateien sind:

- `kapitel/01_2_zielsetzung.md`
- `kapitel/02_2_mathematische_modellierung.md`
- `kapitel/02_3_sensorik_aktorik.md`
- `kapitel/03_2_randbedingungen.md`
- `kapitel/03_4_nichtfunktionale_anforderungen.md`
- `kapitel/04_2_gesamtsystemarchitektur.md`
- `kapitel/04_3_mechanik_elektronik.md`
- `kapitel/04_4_software_architektur.md`
- `kapitel/04_5_regelung_navigation.md`
- `kapitel/05_1_hardwareaufbau.md`
- `kapitel/05_2_firmware_esp32.md`
- `kapitel/05_4_kalibrierung_slam.md`
- `kapitel/05_6_systemintegration.md`
- `kapitel/06_2_subsystem_verifikation.md`
- `kapitel/06_6_diskussion.md`
- `kapitel/07_1_zusammenfassung.md`
- `kapitel/07_2_kritische_wuerdigung.md`

---

*Aenderungsliste erstellt: 2026-02-11 | Projekt: AMR Bachelor-Thesis | Quellen: config.h v1.0.0, hardware-setup.md, kosten.md*
