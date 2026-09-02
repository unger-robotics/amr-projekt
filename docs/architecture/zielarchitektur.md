---
title: Zielarchitektur
description: Kfz-nahe Steuergeraetearchitektur und Funktionskette fuer automatisiertes Fahren als Zielbild des Ausbaus.
---

# Zielarchitektur

Dieses Dokument beschreibt das **Zielbild** des Ausbaus, nicht den Ist-Zustand.
Der Ist-Zustand steht in [Systemarchitektur](../architecture.md) und
[Kommunikation](communication.md); der gemessene Referenzzustand vor dem Ausbau
in `planung/baseline_k0_referenzwerte.md`.

Das Zielbild wird in den Ausbaupaketen K2 bis K10 umgesetzt. Solange ein Paket
nicht abgeschlossen ist, gilt fuer den Betrieb weiterhin die bestehende
Architektur.

---

## 1 Leitgedanke

Der AMR bildet die Steuergeraete-Topologie eines Fahrzeugs im Kleinen ab. Zwei
Aussagen tragen die Zielarchitektur:

1. **Der CAN-Bus wird primaerer Betriebsbus** zwischen dem Raspberry Pi 5 und
   den beiden Steuergeraeten. Der USB-Pfad (micro-ROS ueber serielle
   Verbindung) wird auf Service, Flashen und Fehlersuche zurueckgenommen.
2. **Die Regelung ist zweistufig.** Die uebergeordnete Fahrzeugbewegungsregelung
   laeuft auf dem Pi 5, die echtzeitnahe Raddrehzahlregelung auf dem
   Fahrkern-Steuergeraet. Beide Stufen haben getrennte Zykluszeiten,
   Ausfallreaktionen und Nachweise.

Sensordatenstroeme mit hoher Bandbreite bleiben ausserhalb des CAN-Busses.
Kamera, LiDAR und Radar sind direkt am Pi 5 angebunden. Der CAN-Bus traegt
ausschliesslich Fahr-, Sicherheits- und Telemetriesignale der Steuergeraete.

---

## 2 Steuergeraete-Zielarchitektur

``` mermaid
graph TB
  subgraph PI ["Raspberry Pi 5 - Zentralrechner"]
    NAV["Navigation und Bewegungsregelung<br>Nav2, RPP-Regler"]
    SAFE["Sicherheitslogik<br>Freigabe des Fahrbefehls"]
    GW["Fahrzeug-CAN-Gateway<br>einziger CAN-Zugriff"]
    PERC["Wahrnehmung und Umfeldmodell"]
  end

  subgraph DRIVE ["Drive-ECU - Fahrkern"]
    PID["Raddrehzahlregelung<br>PID 50 Hz"]
    ODO["Odometrie und Encoder"]
    FS["Lokale Failsafe-Logik"]
  end

  subgraph SENS ["Sensor-ECU - Sensor- und Sicherheitsbasis"]
    IMU["IMU, Ultraschall, Kante"]
    BAT["Batterieueberwachung"]
    SRV["Servoansteuerung"]
    LSAFE["Lokale Sicherheitsfunktionen"]
  end

  PERC --> NAV
  NAV --> SAFE
  SAFE --> GW
  GW -->|"CAN 1 Mbit/s<br>Fahrbefehl, Betriebsmodus, Notstopp"| PID
  PID --> ODO
  ODO -->|"CAN<br>Odometrie, Encoder, Stellgroesse"| GW
  IMU -->|"CAN<br>Sensorwerte"| GW
  LSAFE -->|"CAN<br>Kante, Batterieabschaltung"| FS
  FS --> PID
  GW -->|"CAN<br>Servosollwert"| SRV

  style GW fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style SAFE fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style FS fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style LSAFE fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style PI fill:#0B131E,stroke:#517C96,color:#cdd9e5
  style DRIVE fill:#0B131E,stroke:#517C96,color:#cdd9e5
  style SENS fill:#0B131E,stroke:#517C96,color:#cdd9e5
```

### 2.1 Rollen der Steuergeraete

| Steuergeraet | Rolle | Kfz-Pendant |
|---|---|---|
| Raspberry Pi 5 | Zentralrechner: Wahrnehmung, Lokalisierung, Umfeldmodell, Praediktion, Verhaltensentscheidung, Trajektorienplanung, Fahrzeugbewegungsregelung, Sicherheitslogik, CAN-Gateway | ADAS-Zentralrechner mit Gateway-Funktion |
| Drive-ECU (XIAO ESP32-S3) | Fahrkern: Raddrehzahlregelung, Encoderauswertung, Odometrie, lokale Failsafe-Logik, Lichtsteuerung | Motorsteuergeraet |
| Sensor-ECU (XIAO ESP32-S3) | Sensor- und Sicherheitsbasis: IMU, Ultraschall, Kantenerkennung, Batterieueberwachung, Servoansteuerung, lokale Sicherheitsfunktionen | Sensor- und Sicherheitssteuergeraet |

### 2.2 Architekturregeln

1. **Genau ein Gateway.** Nur ein ROS-2-Knoten auf dem Pi 5 greift auf den
   CAN-Bus zu, in Sende- und Empfangsrichtung (SA-12).
2. **Keine Rohdaten ueber Classic CAN.** Kamera-, LiDAR- und Radardaten laufen
   nicht ueber den CAN-Bus, sondern direkt an den Pi 5 (SA-18).
3. **Sicherheit wirkt ohne Zentralrechner.** Der Notstopp-Pfad zwischen
   Sensor-ECU und Drive-ECU funktioniert ohne den Pi 5 und ohne micro-ROS
   (SIA-13, SIA-14).
4. **Zeitkritisches bleibt auf dem Steuergeraet.** Die Raddrehzahlregelung
   verlaesst den Fahrkern nicht.
5. **Der Rueckfallbetrieb bleibt erhalten, aber als bewusster Moduswechsel.**
   Der Modus `SERIAL_REFERENCE` ist ohne erneutes Flashen erreichbar (SIA-16).
   Eine selbsttaetige Umschaltung zwischen Fahrbefehlsquellen findet nicht
   statt (SIA-11).
6. **Eine Freigabestelle fuer Fahrbefehle.** Auf dem Fahrbefehls-Topic des
   Fahrkerns publiziert ausschliesslich die Sicherheitslogik (SIA-15).

---

## 3 Zweistufige Trajektorien- und Bewegungsregelung

Die Trennung zwischen uebergeordneter Bahnfuehrung und echtzeitnaher
Aktorregelung ist ein tragendes Prinzip und wird in Anforderungen, Tests und
Messprotokollen durchgaengig so benannt.

``` mermaid
graph TD
  TP["Trajektorienplanung<br>Solltrajektorie"]
  S1["Stufe 1: Fahrzeugbewegungsregelung<br>Pi 5, Nav2 / RPP<br>Ausgang: v [m/s], omega [rad/s]"]
  SL["Sicherheitslogik<br>letzte Freigabestelle"]
  GW["Fahrzeug-CAN-Gateway"]
  CAN["CAN 1 Mbit/s<br>Fahrbefehl 50 Hz"]
  S2["Stufe 2: Raddrehzahlregelung<br>Drive-ECU, PID 50 Hz<br>Rueckfuehrung: Encoder"]
  PWM["Stellgroesse PWM 20 kHz"]
  MOT["Motoren"]
  ODO["Odometrie"]

  TP --> S1 --> SL --> GW --> CAN --> S2 --> PWM --> MOT
  MOT --> ODO
  ODO -->|"Rueckkopplung an Stufe 1"| S1

  style SL fill:#111D2B,stroke:#FF2A40,color:#FF2A40
  style S1 fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style S2 fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
```

| Merkmal | Stufe 1: Fahrzeugbewegungsregelung | Stufe 2: Raddrehzahlregelung |
|---|---|---|
| Ort | Raspberry Pi 5 | Drive-ECU |
| Regelgroesse | Fahrzeugpose und Bahnfolge | Raddrehzahl links und rechts |
| Stellgroesse | v [m/s], omega [rad/s] | PWM-Tastverhaeltnis |
| Rueckfuehrung | Odometrie, Lokalisierung, Umfeldmodell | Encoder-Quadratur |
| Zykluszeit | Reglerrate des Nav2-Controllers | 50 Hz, 20 ms (`control_loop_hz`) |
| Verhalten bei Ausfall der vorgelagerten Stufe | Fahrzeug bleibt beherrschbar, Stufe 2 haelt den letzten Sollwert bis zum Failsafe-Timeout | Stillstand nach Ablauf des Failsafe-Timeouts (SIA-17) |
| Echtzeitanforderung | weich | hart |
| Kfz-Pendant | Fahrdynamikregelung im Zentralrechner | Drehzahlregelung im Motorsteuergeraet |

**Wesentlich:** Stufe 2 uebernimmt keine Bahnfuehrung, und Stufe 1 greift nicht
in die Stellgroesse ein. Faellt Stufe 1 aus, haelt Stufe 2 den zuletzt
gueltigen Fahrzeug-Sollwert nur bis zum Ablauf des Failsafe-Timeouts und geht
danach in den Stillstand (SIA-17). Der Zentralrechner ist damit fuer den
sicheren Zustand nicht erforderlich.

---

## 4 Funktionskette automatisiertes Fahren

Die Kette folgt der in der Fachliteratur zum automatisierten Fahren ueblichen
Gliederung und ordnet jedem Glied einen konkreten Knoten und ein Ausbaupaket
zu.

``` mermaid
graph TD
  ENV["Umgebung"]
  SENSORS["Sensorik<br>LiDAR, Kamera, Ultraschall, IMU, Radar"]
  PRE["Sensorvorverarbeitung"]
  PERC["Wahrnehmung"]
  LOC["Lokalisierung und Kartierung"]
  EM["Umfeldmodell"]
  PRED["Praediktion"]
  BEH["Verhaltensentscheidung"]
  TP["Trajektorienplanung"]
  TC["Trajektorienfolgeregelung<br>Stufe 1 und Stufe 2"]
  ACT["Aktorik"]
  VEH["Fahrzeug"]

  ENV --> SENSORS --> PRE --> PERC --> LOC --> EM --> PRED --> BEH --> TP --> TC --> ACT --> VEH
  VEH -->|"Rueckkopplung"| SENSORS
  VEH -->|"Odometrie und IMU"| LOC
  EM -->|"Hindernisse"| TP

  style EM fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style BEH fill:#111D2B,stroke:#00E5FF,color:#cdd9e5
  style TC fill:#111D2B,stroke:#00FF66,color:#cdd9e5
```

| Kettenglied | Realisierung | Zustand | Paket | Anforderung |
|---|---|---|---|---|
| Sensorik | RPLIDAR A1, IMX296, Ultraschall, MPU6050, BGT60TR13C | vorhanden, Radar offen | K7, K10 | SA-13, SA-17, SA-18 |
| Sensorvorverarbeitung | neuer Knoten: Bereichsfilterung, Clusterbildung, Plausibilisierung, Zeitsynchronisation | offen | K8 | FA-18 |
| Wahrnehmung | Hailo-8L Objekterkennung, Gemini-Szenendeutung | vorhanden, Anbindung offen | K8 | FA-15 (Bestand) |
| Lokalisierung und Kartierung | SLAM Toolbox, AMCL, Odometrie-Transformation | vorhanden | Bestand | FA-01, FA-02 |
| Umfeldmodell | neuer Knoten: Objektliste mit Verfolgungskennung | offen | K8 | FA-19, SA-14 |
| Praediktion | neuer Knoten: Trajektorienschaetzung je Objekt | offen | K9 | FA-20 |
| Verhaltensentscheidung | neuer Knoten: Zustandsautomat | offen | K9 | FA-21, SIA-15 |
| Trajektorienplanung | neuer Knoten als Nav2-Adapter | offen | K9 | FA-22 |
| Trajektorienfolgeregelung | Stufe 1 Nav2/RPP, Stufe 2 PID auf dem Fahrkern | vorhanden, Zweistufigkeit nachzuweisen | K9 | SIA-17, NFA-01 |
| Aktorik | Cytron MDD3A, JGA25-370 | vorhanden | Bestand | SIA-07 |

Wahrnehmung und Lokalisierung werden **nicht neu gebaut**. Die vorhandenen
Knoten werden ueber definierte Schnittstellen eingebunden.

---

## 5 Funktionszuordnung

### 5.1 Raspberry Pi 5

| Funktion | Anforderung | Zustand |
|---|---|---|
| Kartierung und Lokalisierung | FA-01, FA-02 | vorhanden |
| Navigation und Bahnplanung | FA-03, FA-04 | vorhanden |
| Fahrzeugbewegungsregelung (Stufe 1) | NFA-12 | vorhanden |
| Sicherheitslogik und Freigabe des Fahrbefehls | SIA-01, SIA-02, SIA-15 | vorhanden, SIA-15 offen |
| Fahrzeug-CAN-Gateway | SA-12, SA-15 | offen (K6) |
| Wahrnehmung ueber Hailo-8L und Cloud-Semantik | FA-15 | vorhanden |
| Sensorvorverarbeitung | FA-18 | offen (K8) |
| Umfeldmodell | FA-19, SA-14 | offen (K8) |
| Praediktion | FA-20 | offen (K9) |
| Verhaltensentscheidung | FA-21 | offen (K9) |
| Trajektorienplanung | FA-22 | offen (K9) |
| Radar-Abstraktion und Simulator | SA-13, FA-23 | offen (K7) |
| Reale Radaranbindung ueber SPI3 | SA-17 | offen (K10) |
| Bedien- und Leitstandsebene | FA-12 bis FA-14 | vorhanden |
| Sprachschnittstelle | FA-17 | vorhanden |

### 5.2 Drive-ECU (Fahrkern)

| Funktion | Anforderung | Zustand |
|---|---|---|
| Raddrehzahlregelung (Stufe 2), 50 Hz | NFA-01 | vorhanden |
| Encoderauswertung und Odometrie | NFA-03 | vorhanden |
| Failsafe bei ausbleibendem Fahrbefehl | SIA-04, SIA-17 | vorhanden |
| Inter-Core-Watchdog | SIA-05 | vorhanden |
| Geschwindigkeitsbegrenzung auf Hardwareebene | SIA-07 | vorhanden |
| Empfang von Kante und Batterieabschaltung ueber CAN | SIA-03 | vorhanden |
| Empfang von Fahrbefehl und Betriebsmodus ueber CAN | SA-11 | offen (K4) |
| Arbitrierung der Fahrbefehlsquelle | SIA-11 | offen (K5) |
| Ueberwachung des Kantensignals auf Ausbleiben | SIA-12 | offen (K5) |
| Auswertung des Notstoppsignals ueber CAN | SIA-13 | offen (K5) |
| Rueckmeldung des aktiven Pfads | SA-11 | offen (K4) |
| Lichtsteuerung | — | vorhanden |

### 5.3 Sensor-ECU (Sensor- und Sicherheitsbasis)

| Funktion | Anforderung | Zustand |
|---|---|---|
| IMU-Erfassung und Komplementaerfilter | NFA-04 | vorhanden |
| Ultraschallmessung | SIA-02 | vorhanden |
| Kantenerkennung | SIA-01 | vorhanden |
| Batterieueberwachung und Abschaltschwellen | SIA-08, SIA-09 | vorhanden |
| Servoansteuerung | SA-06 | vorhanden |
| Senden von Kante und Batterieabschaltung an den Fahrkern | SIA-03 | vorhanden |
| Senden des Abschaltframes unabhaengig vom Zentralrechner | SIA-14 | offen (K5) |
| Auswertung des Notstoppsignals ueber CAN | SIA-13 | offen (K5) |

### 5.4 Zuordnungsregel

Eine Funktion gehoert auf ein Steuergeraet, wenn sie eine harte
Echtzeitanforderung hat oder im sicheren Zustand ohne Zentralrechner wirken
muss. Alle uebrigen Funktionen gehoeren auf den Pi 5. Diese Regel entscheidet
kuenftige Zuordnungsfragen.

---

## 6 Kommunikationsarchitektur im Zielzustand

| Pfad | Traeger | Inhalt | Rolle |
|---|---|---|---|
| Pi 5 nach Drive-ECU | CAN | Fahrbefehl, Betriebsmodus, Notstopp, Gateway-Lebenszeichen | Betriebspfad |
| Drive-ECU nach Pi 5 | CAN | Odometrie, Encoder, Stellgroesse, Pfadstatus, Lebenszeichen | Betriebspfad |
| Pi 5 nach Sensor-ECU | CAN | Servosollwert, Notstopp | Betriebspfad |
| Sensor-ECU nach Pi 5 | CAN | Ultraschall, Kante, IMU, Batterie, Lebenszeichen | Betriebspfad |
| Sensor-ECU nach Drive-ECU | CAN | Kante, Batterieabschaltung | Sicherheitspfad ohne Zentralrechner |
| Pi 5 nach Steuergeraete | USB, micro-ROS | keine Betriebsdaten | Service, Flashen, Fehlersuche (SA-16) |
| Kamera, LiDAR, Radar nach Pi 5 | CSI, USB, SPI3 | Rohdaten | ausserhalb des CAN-Busses (SA-18) |

### 6.1 Betriebsmodi des Fahrbefehlspfads

Der Fahrkern arbeitet in genau einem explizit gesetzten Betriebsmodus. In jedem
Modus ist genau eine Fahrbefehlsquelle aktiv. **Es gibt keine selbsttaetige
Umschaltung zwischen Quellen**: Bleibt die aktive Quelle aus, geht der Fahrkern
in den sicheren Stillstand, statt sich eine Ersatzquelle zu suchen.

| Modus | Aktive Quelle | CAN-Fahrbefehl | Verwendung |
|---|---|---|---|
| `SERIAL_REFERENCE` | micro-ROS ueber USB | ignoriert | Ausgangszustand, Rueckfallbetrieb |
| `CAN_SHADOW` | micro-ROS ueber USB | empfangen, ohne Wirkung auf den Stellpfad | Nachweis in K4 |
| `CAN_PRIMARY` | CAN | wirksam | Regelbetrieb ab K6 |
| `SERVICE` | keine | ignoriert | Flashen, Diagnose; Antrieb gesperrt |
| `FAILSAFE` | keine | ignoriert | nach Timeout, Notstopp oder Sicherheitsereignis |

`FAILSAFE` wird nicht angefordert, sondern durch ein Ereignis erreicht. Das
Verlassen erfordert einen expliziten Moduswechsel, nachdem die Ursache
entfallen ist; ein selbsttaetiges Fortsetzen der Fahrt findet nicht statt.

Vollstaendige Definition mit Uebergaengen, Zeitueberwachung je Modus und
Begruendung gegen den urspruenglich erwogenen Automatismus:
`docs/anforderungsliste-L1.md`, Abschnitt 13.

Der Signalbedarf, der sich daraus ergibt, ist in [Signalbedarf](signalbedarf.md)
aufgefuehrt. Er ist die Eingangsgroesse fuer die Signaldatenbank in
Ausbaupaket K2.

---

## 7 Hardware-Anbindung im Zielzustand

```text
Raspberry Pi 5
  |
  +-- SPI0  (MCP2515 + MCP2562)  --> CAN 1 Mbit/s --> Drive-ECU, Sensor-ECU   [Betriebsbus]
  +-- USB   (ttyUSB0)            --> RPLIDAR A1
  +-- USB                        --> ReSpeaker Mic Array, Audioausgabe
  +-- CSI                        --> Kamera IMX296 Global Shutter
  +-- PCIe                       --> Hailo-8L
  +-- SPI3                       --> BGT60TR13C                                [Paket K10]
  +-- USB   (ttyACM, /dev/amr_*) --> Drive-ECU, Sensor-ECU                     [nur Service]
```

---

## 8 Abgrenzung

Dieses Dokument legt **kein** Signalformat, **keine** CAN-Kennung und **keine**
Bitbelegung fest. Diese entstehen in Ausbaupaket K2 auf Grundlage des
Signalbedarfs. Es beschreibt ebenfalls keine Implementierung; die betroffenen
Dateien je Paket stehen im Umsetzungsplan.
