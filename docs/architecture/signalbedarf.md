---
title: Signalbedarf
description: Fachlicher Signalbedarf der Steuergeraetearchitektur als Eingangsgroesse fuer die CAN-Signaldatenbank.
---

# Signalbedarf der Steuergeraetearchitektur

Dieses Dokument benennt, **welche** Signale die Zielarchitektur benoetigt, mit
Richtung, Rate, Genauigkeit, Sicherheitsrelevanz und Begruendung.

**Es legt bewusst nicht fest:** CAN-Kennungen, Nutzdatenlaengen, Bitpositionen,
Byteanordnung oder Skalierungsfaktoren. Diese Festlegungen entstehen in
Ausbaupaket K2 in der Signaldatenbank `hardware/can-bus/`. Der hier
beschriebene Bedarf ist deren Eingangsgroesse und Pruefmassstab: Jedes Signal
der Datenbank muss sich auf eine Zeile dieses Dokuments zurueckfuehren lassen,
und jede Zeile muss abgedeckt sein (SA-10, Testfall T-09).

Die Zuordnung zu bestehenden CAN-Kennungen in Abschnitt 5 ist rein
informativ und beschreibt den Ist-Zustand.

---

## 1 Sicherheitsrelevanz

| Stufe | Bedeutung | Folge fuer den Entwurf |
|---|---|---|
| **S** | sicherheitsrelevant: das Signal wirkt unmittelbar auf den sicheren Zustand des Fahrzeugs | hohe Buspriorisierung, Ausbleiben muss erkannt werden, Wirkung ohne Zentralrechner erforderlich |
| **B** | betriebsrelevant: das Signal wird fuer die bestimmungsgemaesse Fahrfunktion benoetigt | Ausbleiben muss zu einem definierten Ersatzverhalten fuehren |
| **D** | diagnoserelevant: das Signal dient der Beobachtung und Fehlersuche | Ausbleiben darf die Fahrfunktion nicht beeintraechtigen |

---

## 2 Signale vom Pi 5 an die Steuergeraete

| Nr. | Signal | Empfaenger | Rate | Genauigkeit und Wertebereich | Sich. | Begruendung |
|---|---|---|---|---|---|---|
| P-01 | Fahrzeug-Sollgeschwindigkeit laengs | Drive-ECU | 50 Hz | Aufloesung mindestens 1 mm/s, Bereich mindestens -0,5 bis +0,5 m/s | S | Ausgang der Fahrzeugbewegungsregelung (Stufe 1). 50 Hz entsprechen der Zykluszeit der Raddrehzahlregelung; eine niedrigere Rate erzeugt Stufen im Sollwert. SA-11, NFA-14 |
| P-02 | Fahrzeug-Solldrehrate | Drive-ECU | 50 Hz | Aufloesung mindestens 0,001 rad/s, Bereich mindestens -1,5 bis +1,5 rad/s | S | wie P-01; Bereich deckt NFA-07 mit Reserve ab |
| P-03 | Betriebsmodus des Fahrbefehlspfads | Drive-ECU | 1 Hz und bei Aenderung | drei Zustaende: Ruhe, Referenzpfad fuehrend, CAN-Pfad fuehrend | S | Die Firmware muss wissen, welcher Pfad Vorrang hat. Ohne dieses Signal waere die Arbitrierung fest verdrahtet und der Rueckfallbetrieb nicht ohne Flashen umschaltbar. SIA-11, SIA-16 |
| P-04 | Begrenzung der Stellgroesse | Drive-ECU | 1 Hz und bei Aenderung | 0 bis 100 Prozent | B | erlaubt das Herabsetzen der Antriebsleistung im Einfahr- und Diagnosebetrieb ohne Flashen; ersetzt den heutigen Weg ueber `hardware_cmd` |
| P-05 | Notstopp-Anforderung | Drive-ECU und Sensor-ECU | 10 Hz und bei Aenderung | binaer, zusaetzlich Quellenkennung und fortlaufender Zaehler | S | Muss beide Steuergeraete ohne Mitwirkung der Anwendungsschicht erreichen. Zyklische Wiederholung, damit ein verlorenes Ereignis nicht unbemerkt bleibt; der Zaehler macht Verlust erkennbar. SIA-13 |
| P-06 | Lebenszeichen des Gateways | Drive-ECU und Sensor-ECU | 10 Hz | fortlaufender Zaehler, Betriebszustand, Laufzeit | S | Die Steuergeraete muessen den Ausfall des Zentralrechners erkennen koennen, ohne auf das Ausbleiben von Fahrbefehlen zu warten. SIA-11 |
| P-07 | Servosollwert Schwenk und Neigung | Sensor-ECU | bei Aenderung, hoechstens 10 Hz | Aufloesung 0,1 Grad, Bereich nach `config_sensors.h` | B | vorhanden im Ist-Zustand; wird unveraendert uebernommen |

---

## 3 Signale von der Drive-ECU an den Pi 5

| Nr. | Signal | Rate | Genauigkeit und Wertebereich | Sich. | Begruendung |
|---|---|---|---|---|---|
| D-01 | Odometrie-Position x und y | 20 Hz | Aufloesung mindestens 1 mm, Bereich mindestens -100 bis +100 m | B | Eingangsgroesse fuer Lokalisierung und Kartierung. 20 Hz aus `odom_publish_hz`; NFA-03 fordert mindestens 10 Hz |
| D-02 | Odometrie-Gierwinkel und Laengsgeschwindigkeit | 20 Hz | Winkel mindestens 0,001 rad, Geschwindigkeit mindestens 1 mm/s | B | wie D-01; getrennt von D-01, weil beide zusammen die Nutzdatenlaenge eines Standardrahmens ueberschreiten |
| D-03 | Raddrehzahl links und rechts | 10 Hz | Aufloesung mindestens 0,01 rad/s | D | Nachweis der Raddrehzahlregelung, Grundlage fuer die Reglerabstimmung |
| D-04 | Stellgroesse links und rechts | 10 Hz | ganzzahlig, Bereich -255 bis +255 | D | Nachweis, dass der Regler wirkt; Eingangsgroesse fuer die Latenzmessung nach NFA-14 |
| D-05 | Status des aktiven Fahrbefehlspfads | 5 Hz | aktive Quelle, Alter des Referenzpfad-Befehls, Alter des CAN-Befehls, Zustandsbits | S | **Neu erforderlich.** Ohne dieses Signal ist die Arbitrierung von aussen nicht beobachtbar, und ein Failover waere nicht nachweisbar. Traegt zusaetzlich die Bits fuer scharf geschaltete Kantenueberwachung, Kantenzeitueberschreitung und gehaltenen Notstopp. SIA-11, SIA-12, NFA-18 |
| D-06 | Lebenszeichen des Fahrkerns | 1 Hz | Zustandsbits fuer Encoder, Motortreiber, Regleraktivitaet, Batterieabschaltung, Echtzeitkern, Failsafe; Laufzeit | D | vorhanden; die Zustandsbits muessen kuenftig echte Zustaende fuehren statt fester Werte |

---

## 4 Signale von der Sensor-ECU

| Nr. | Signal | Empfaenger | Rate | Genauigkeit und Wertebereich | Sich. | Begruendung |
|---|---|---|---|---|---|---|
| S-01 | Kantenerkennung | Drive-ECU und Pi 5 | 20 Hz | binaer | S | Der Fahrkern muss ohne Zentralrechner stoppen koennen. Die Rate bestimmt zugleich die Ansprechzeit der Zeitueberwachung nach SIA-12 |
| S-02 | Batterie-Abschaltanforderung | Drive-ECU und Pi 5 | bei Ereignis, zusaetzlich zyklische Wiederholung | binaer | S | wie S-01. Die zyklische Wiederholung ist neu erforderlich, damit ein verlorenes Ereignis nicht unbemerkt bleibt |
| S-03 | Abstand voraus | Pi 5 | 10 Hz | Aufloesung mindestens 1 mm, Bereich 0,02 bis 4,00 m | S | Eingangsgroesse der Sicherheitslogik nach SIA-02 und der Sensorvorverarbeitung nach FA-18 |
| S-04 | Beschleunigung in drei Achsen und Gierrate | Pi 5 | 50 Hz | Beschleunigung mindestens 0,01 m/s^2, Gierrate mindestens 0,01 rad/s | B | Eingangsgroesse fuer Lokalisierung und Odometriekorrektur. NFA-04 fordert mindestens 20 Hz |
| S-05 | Gierwinkel aus Komplementaerfilter | Pi 5 | 50 Hz | Aufloesung mindestens 0,001 rad | B | wird von der Firmware bereits gefiltert bereitgestellt |
| S-06 | Batteriespannung, Strom und Leistung | Pi 5 | 2 Hz | Spannung mindestens 1 mV, Strom mindestens 1 mA, Leistung ausreichend fuer mindestens 100 W | D | **Aenderungsbedarf:** Die heutige Aufloesung der Leistung erreicht ihre Obergrenze bei 65,5 W, waehrend der Betriebspunkt bei rund 60 W liegt. Der Wertebereich ist in K2 anzupassen oder der Wert zu begrenzen |
| S-07 | Lebenszeichen der Sensorbasis | Pi 5 | 1 Hz | Zustandsbits fuer IMU, Strommessung, Servotreiber, Batterieabschaltung, Echtzeitkern; Laufzeit; Fehlerzaehler | D | vorhanden; die Fehlerzaehler sollen kuenftig nach ROS 2 gelangen statt nur protokolliert zu werden. SA-15 |

---

## 5 Zuordnung zum Ist-Zustand

Rein informativ. Die verbindliche Festlegung erfolgt in K2.

| Bedarf | Im Ist-Zustand vorhanden | Bemerkung |
|---|---|---|
| P-01, P-02 | nein | Kommandopfad ueber CAN existiert nicht (BA/OP-08) |
| P-03, P-04 | nein | neu |
| P-05 | nein | neu |
| P-06 | nein | neu |
| P-07 | ja | Servosollwert, im Ist-Zustand nicht in `hardware/can-bus/CAN-Bus.md` dokumentiert |
| D-01 bis D-04 | ja | werden gesendet, von der Bruecke im Ist-Zustand jedoch verworfen |
| D-05 | nein | neu |
| D-06 | ja | Zustandsbits teilweise fest verdrahtet |
| S-01 bis S-05, S-07 | ja | vollstaendig vorhanden |
| S-02 zyklische Wiederholung | nein | heute nur ereignisgesteuert |
| S-06 | ja | Wertebereich der Leistung zu klein |

**Neu hinzukommend:** P-01 bis P-06 und D-05, also acht Signalgruppen. Alle
uebrigen sind vorhanden und werden uebernommen.

---

## 6 Buslastabschaetzung

Die Abschaetzung dient der Entwurfsentscheidung in K2 und ersetzt keine
Messung. Der belastbare Wert entsteht mit Testfall T-10 (NFA-13).

| Anteil | Rate | Anmerkung |
|---|---|---|
| Bestand (gemessen in K0) | 193,1 Frames/s | rechnerisch rund 2,5 Prozent bei 1 Mbit/s |
| Fahrbefehl P-01 und P-02 | 50 Frames/s | bei gemeinsamer Uebertragung in einem Rahmen |
| Betriebsmodus P-03, Begrenzung P-04 | rund 2 Frames/s | zyklisch mit Ereignisergaenzung |
| Notstopp P-05 | 10 Frames/s | |
| Gateway-Lebenszeichen P-06 | 10 Frames/s | |
| Pfadstatus D-05 | 5 Frames/s | |
| Wiederholung Batterieabschaltung S-02 | 1 Frames/s | |
| **Summe** | **rund 271 Frames/s** | rechnerisch rund 3,5 Prozent |

Die Anforderung NFA-13 von hoechstens 30 Prozent wird rechnerisch deutlich
eingehalten. **Achtung:** Die Baseline-Aufnahme hat einen ungeklaerten
Frameverlust auf der Odometrie-Positionsnachricht und einen ungeklaerten
Anstieg des Empfangsfehlerzaehlers ergeben (OP-10). Eine geringe rechnerische
Buslast ist daher kein Nachweis fuer eine ausreichende Uebertragungsguete. Der
Nachweis erfolgt ueber NFA-19 und das Freigabe-Gate vor Ausbaupaket K4.

---

## 7 Anforderungen an die Signaldatenbank

Diese Punkte sind in K2 umzusetzen und mit Testfall T-09 nachzuweisen:

1. Die Datenbank ist die alleinige Quelle fuer Signalkennungen,
   Nutzdatenlaengen und Zykluszeiten. Firmware-Konstanten und die Pi-seitige
   Dekodierung werden daraus abgeleitet, nicht parallel gepflegt (SA-10).
2. Jedes Signal traegt Sender und Empfaenger, damit der Sicherheitspfad
   zwischen Sensor-ECU und Drive-ECU aus der Datenbank ablesbar ist.
3. Bestehende Signalkennungen bleiben unveraendert, damit eine aeltere
   Firmware weiterhin betrieben werden kann. Neue Signale belegen bisher
   ungenutzte Bereiche.
4. Sicherheitsrelevante Signale erhalten eine hoehere Buspriorisierung als
   Diagnosesignale.
5. Abweichungen zwischen Datenbank und abgeleiteten Artefakten fuehren zu
   einem Fehler beim Uebersetzen, nicht erst im Betrieb.
6. Die drei bekannten Dokumentationsabweichungen des Ist-Zustands werden
   bereinigt: die fehlende Dokumentation des Servosollwerts, die fehlende
   Kennzeichnung der vom Fahrkern empfangenen Sicherheitssignale und die
   veraltete Angabe der Nutzdatenlaenge des Sensor-Lebenszeichens.
