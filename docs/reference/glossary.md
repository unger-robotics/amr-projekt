---
title: Glossar
description: Zentrale Begriffe und Terminologie der AMR-Plattform.
---

# Glossar

## Ebenen-Modell

| Begriff | Beschreibung |
|---------|-------------|
| **Ebene A – Fahrkern** | ESP32-S3 Drive-Knoten und Sensor-Knoten. Echtzeit-Regelung, Sensorerfassung, Sicherheits-Basisfunktionen |
| **Ebene B – Bedien- und Leitstandsebene** | Pi 5 mit ROS2, SLAM, Navigation, Benutzeroberflaeche |
| **Ebene C – Intelligente Interaktion** | Hailo-8L, Gemini Cloud, gTTS, ReSpeaker (optional) |

## Knoten und Komponenten

| Begriff | Beschreibung |
|---------|-------------|
| **Drive-Knoten (Fahrkern)** | ESP32-S3 fuer Motorregelung, Encoder, PID, Odometrie, LED |
| **Sensor-Knoten (Sensor- und Sicherheitsbasis)** | ESP32-S3 fuer IMU, Ultraschall, Cliff, Batterie, Servo |
| **Pi 5** | Zentrale ROS2- und Docker-Laufzeit (Raspberry Pi 5, 8 GB) |
| **micro-ROS Agent** | Serial-Bridge zwischen ROS2 und den ESP32-Knoten |
| **Benutzeroberflaeche** | React/Vite Weboberflaeche fuer Telemetrie und Fernsteuerung |

## Funktionen und Systeme

| Begriff | Beschreibung |
|---------|-------------|
| **Lokalisierung und Kartierung** | SLAM Toolbox — simultane Positionsbestimmung und Kartenerstellung |
| **Navigation** | Nav2-Stack mit RPP Controller und NavFn Planer |
| **Sicherheitslogik** | Cliff-Safety-Knoten: multiplext `/cmd_vel`, blockiert bei Cliff oder Hindernis |
| **Freigabelogik** | Prueft Sprachbefehle auf zulaessige Missionskommandos |
| **Sprachschnittstelle** | ReSpeaker + Gemini Audio-STT (Cloud, primaer) / faster-whisper (Offline-Fallback) fuer freihaendige Bedienung |
| **Dual-Path** | micro-ROS/UART (primaer) + CAN-Bus (sekundaer, Redundanz) |

## Projektbezogene Begriffe

| Begriff | Beschreibung |
|---------|-------------|
| **Projektfrage (PF)** | Forschungsleitende Fragen der Projektarbeit (PF1, PF2, PF3) |
| **VDI 2206** | Richtlinie fuer die Entwicklung mechatronischer Systeme (V-Modell) |
| **V-Modell** | Entwicklungsprozess mit Phasen (Entwurf → Implementierung → Validierung) |
| **Missionskommando** | Freigegebener Befehl aus der Sprachverarbeitung (z.B. "Fahre zur Ladestation") |
| **Intent** | Semantisch erkannter Zweck eines Sprachbefehls |

## Abkuerzungen

| Kuerzel | Bedeutung |
|---------|-----------|
| AMR | Autonomous Mobile Robot |
| ATE | Absolute Trajectory Error |
| CAN | Controller Area Network |
| DoA | Direction of Arrival |
| DDS | Data Distribution Service |
| IMU | Inertial Measurement Unit |
| Nav2 | ROS 2 Navigation Stack |
| PID | Proportional-Integral-Derivative (Regelung) |
| QoS | Quality of Service |
| RPP | Regulated Pure Pursuit (Controller) |
| SLAM | Simultaneous Localization and Mapping |
| STT | Speech-to-Text |
| TF | Transform (ROS2 Koordinatensystem) |
| TTS | Text-to-Speech |
| TWAI | Two-Wire Automotive Interface (ESP32 CAN) |
| VAD | Voice Activity Detection |
| XRCE-DDS | eXtremely Resource Constrained Environments DDS |

## Steuergeraetearchitektur und Funktionskette (Zielbild)

Begriffe des laufenden Ausbaus. Das Zielbild beschreibt
[Zielarchitektur](../architecture/zielarchitektur.md); der gemessene
Ausgangszustand steht in `planung/baseline_k0_referenzwerte.md`.

| Begriff | Beschreibung |
|---------|-------------|
| **Steuergeraet** | Deutscher Begriff fuer ECU. Drive-ECU und Sensor-ECU bleiben als Eigennamen der beiden ESP32-S3-Knoten zulaessig |
| **Fahrzeug-CAN-Gateway** | Der eine ROS-2-Knoten auf dem Pi 5, der den gesamten CAN-Zugriff in Sende- und Empfangsrichtung kapselt (SA-12) |
| **Betriebsbus** | Der Bus, ueber den im Regelbetrieb Fahr- und Sicherheitssignale laufen. Im Zielbild der CAN-Bus |
| **Referenzpfad** | Der USB-/micro-ROS-Pfad, solange er den Betriebspfad stellt oder als Rueckfallebene dient |
| **Servicepfad** | Der USB-Pfad nach der Umstellung: Service, Flashen und Fehlersuche, keine Betriebsdaten (SA-16) |
| **Arbitrierung** | Auswahl der gueltigen Fahrbefehlsquelle im Fahrkern nach fester Prioritaet und Zeitueberwachung (SIA-11) |
| **Signaldatenbank** | Versionierte Beschreibung aller CAN-Signale; alleinige Quelle fuer Firmware-Konstanten und Pi-seitige Dekodierung (SA-10) |
| **Signalbedarf** | Fachliche Beschreibung der benoetigten Signale ohne Kennung und Bitbelegung; Eingangsgroesse der Signaldatenbank |
| **Sensorvorverarbeitung** | Filterung, Plausibilisierung und Zeitsynchronisation der Rohdaten vor der Wahrnehmung (FA-18) |
| **Umfeldmodell** | Fusionierte Objektliste mit stabiler Verfolgungskennung aus LiDAR, Ultraschall, Kamera und Radar (FA-19) |
| **Praediktion** | Schaetzung kuenftiger Objekttrajektorien ueber einen definierten Horizont (FA-20) |
| **Verhaltensentscheidung** | Wahl des Fahrmanoevers als Zustandsautomat. Publiziert keine Fahrbefehle (FA-21, SIA-15) |
| **Trajektorienplanung** | Erzeugung der kollisionsfreien Solltrajektorie aus der Verhaltensvorgabe (FA-22) |
| **Fahrzeugbewegungsregelung** | Stufe 1 der Regelung auf dem Pi 5. Ausgang sind Fahrzeug-Sollgroessen v und omega |
| **Raddrehzahlregelung** | Stufe 2 der Regelung auf dem Fahrkern. PID mit 50 Hz, Rueckfuehrung ueber die Encoder (SIA-17) |
| **Baseline** | Gemessener Referenzzustand vor dem Ausbau. Beschreibt den Istwert und ist ausdruecklich keine Anforderung |
| **Regressionstoleranz** | Zulaessige Verschlechterung gegenueber der Baseline, unabhaengig von der Mindestanforderung |
| **Ausbaupaket** | Eine der Einheiten K0 bis K10, in denen der Ausbau umgesetzt und einzeln nachgewiesen wird |
| **Freigabe-Gate** | Pruefpunkt zwischen zwei Ausbaupaketen, der ohne bestandenen Nachweis nicht ueberschritten wird |
