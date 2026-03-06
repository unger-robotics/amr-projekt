# Zusammenfassung des SDS1104X-E Oszilloskops

Das SDS1104X-E ist Teil der SDS1000X-E Serie von Siglent und bietet folgende Hauptmerkmale:

- 4 analoge Eingangskanäle
- 100 MHz Bandbreite
- Zwei 1 GSa/s ADCs
- Super Phosphor Oszilloskop (SPO) Technologie
- 7 Zoll TFT-LCD Farbdisplay mit 800x480 Auflösung

Tabelle mit den wichtigsten technischen Daten:

| Parameter               | Spezifikation                                                             |
| ----------------------- | ------------------------------------------------------------------------- |
| Bandbreite              | 100 MHz                                                                   |
| Kanäle                  | 4                                                                         |
| Max. Abtastrate         | 1 GSa/s (2 Kanäle), 500 MSa/s (4 Kanäle)                                  |
| Speichertiefe           | 14 Mpts/CH (single channel), 7 Mpts/CH (dual channels)                    |
| Vertikale Auflösung     | 8 Bit                                                                     |
| Vertikale Skala         | 500 μV/div - 10 V/div                                                     |
| Eingangsimpedanz        | 1 MΩ ± 2%                                                                 |  | 15 pF ± 2 pF |
| Zeitbasis               | 1.0 ns/div - 100 s/div                                                    |
| Waveform Capture Rate   | Bis zu 400,000 wfm/s (Sequence-Modus)                                     |
| Trigger-Typen           | Edge, Slope, Pulse Width, Window, Runt, Interval, Dropout, Pattern, Video |
| Serielle Busdekodierung | I2C, SPI, UART, CAN, LIN                                                  |
| Math-Funktionen         | +, -, *, /, FFT, d/dt, ∫dt, √                                             |
| Display                 | 7 Zoll TFT-LCD, 800x480 Pixel, 256 Intensitätsstufen                      |
| Schnittstellen          | USB Host, USB Device, LAN, Pass/Fail, Trigger Out                         |

Mit dem SDS1104X-E können Sie:

1. Elektrische Signale mit hoher Erfassungsrate visualisieren und analysieren
2. Komplexe Triggerfunktionen nutzen, einschließlich serieller Bustrigger
3. Serielle Busprotokolle dekodieren und analysieren
4. Automatische Messungen von 38 Signalparametern durchführen
5. Math-Funktionen und FFT-Analyse mit bis zu 1 Mpts durchführen
6. Die History-Funktion zur Aufzeichnung und Analyse von Wellenformen nutzen
7. Segmentierte Erfassung (Sequence-Modus) für die Erfassung seltener Ereignisse verwenden
8. Pass/Fail-Tests für die Qualitätskontrolle durchführen
9. Daten über USB oder LAN exportieren und das Gerät fernsteuern
10. Mit optionalen Erweiterungen wie 16 digitalen Kanälen (MSO), AWG-Modul oder WLAN-Adapter arbeiten


## allgemeine Merkmale

1. Bandbreite und Kanäle:
   - Modelle mit 100 MHz und 200 MHz Bandbreite
   - 2-Kanal und 4-Kanal Varianten verfügbar

2. Abtastrate:
   - Bis zu 1 GSa/s bei Verwendung eines Kanals
   - 500 MSa/s bei Nutzung aller Kanäle

3. Speichertiefe:
   - Bis zu 14 Mpts pro Kanal (im Interleave-Modus)
   - 7 Mpts pro Kanal bei Nutzung aller Kanäle

4. Erfassungsrate:
   - Bis zu 400.000 Wellenformen pro Sekunde im Sequence-Modus

5. Vertikales System:
   - 8-Bit vertikale Auflösung
   - Vertikale Skala von 500 μV/div bis 10 V/div

6. Display:
   - 7 Zoll TFT-LCD Farbdisplay
   - Auflösung von 800x480 Pixeln
   - 256 Intensitätsstufen für Signaldarstellung

7. Trigger:
   - Vielfältige Trigger-Typen wie Edge, Pulse, Video, Slope etc.
   - Serielle Bus-Trigger für I2C, SPI, UART, CAN und LIN

8. Analyse-Funktionen:
   - FFT mit bis zu 1 Million Punkten
   - Mathematische Operationen zwischen Kanälen
   - Automatische Messungen von 38 Parametern

9. Zusätzliche Funktionen:
   - Segmentierter Speicher (Sequence-Modus)
   - History-Funktion für Wellenform-Aufzeichnung
   - Such- und Navigations-Funktionen
   - Bode-Plot (nur 4-Kanal Modelle)

10. Schnittstellen:
    - USB Host, USB Device, LAN
    - Pass/Fail-Ausgang

11. Optionale Erweiterungen:
    - 16 digitale Kanäle (MSO-Funktion)
    - Arbiträrer Funktionsgenerator (AWG)
    - WLAN-Adapter

## ersten Schritte zur Nutzung des SDS1000X-E Oszilloskops

1. Anschlüsse und Einrichtung:

   - Netzanschluss: Verbinden Sie das Gerät mit dem mitgelieferten Netzkabel.
   - Einschalten: Drücken Sie den Power-Knopf an der Frontseite.
   - Tastkopf anschließen: Verbinden Sie die Tastköpfe mit den BNC-Eingängen der Kanäle.
   - Tastkopf-Kompensation: Führen Sie eine Tastkopf-Kompensation durch, um die Genauigkeit zu optimieren.
   - Selbstkalibrierung: Führen Sie bei Bedarf eine Selbstkalibrierung des Geräts durch.

2. Frontplatte und Benutzeroberfläche:

   - Vertikale Bedienelemente: Knöpfe für Skalierung und Position jedes Kanals.
   - Horizontale Bedienelemente: Knöpfe für Zeitbasis und horizontale Position.
   - Trigger-Bedienelemente: Knöpfe und Tasten für Trigger-Einstellungen.
   - Menü-Tasten: Softkeys neben dem Bildschirm für verschiedene Funktionen.
   - Universal-Knopf: Multifunktionsknopf für verschiedene Einstellungen.
   - Display: 7-Zoll Farbdisplay zeigt Wellenformen, Messungen und Menüs.

3. Grundlegende Bedienung:

   - Kanal aktivieren: Drücken Sie die Kanaltaste (CH1, CH2 etc.) zum Ein-/Ausschalten.
   - Vertikale Einstellung: Nutzen Sie die SCALE und POSITION Knöpfe des jeweiligen Kanals.
   - Horizontale Einstellung: Stellen Sie die Zeitbasis und horizontale Position ein.
   - Trigger einstellen: Wählen Sie Trigger-Quelle und -Typ, stellen Sie Trigger-Level ein.
   - Auto-Setup: Nutzen Sie die AUTO-Taste für schnelle automatische Einstellung.
   - Messungen: Verwenden Sie die MEASURE-Taste für automatische Messungen.
   - Speichern/Abrufen: Nutzen Sie die SAVE/RECALL-Taste zum Speichern von Einstellungen oder Wellenformen.



## serielle Busdekodierung von I2C, SPI, UART, CAN und LIN

1. Integrierte Funktionen: Laut der Produktbeschreibung in der PDF sind die seriellen Bustrigger und -dekodierungsfunktionen für I2C, SPI, UART, CAN und LIN bereits im Standardlieferumfang des SDS1104X-E enthalten.

2. Standardzubehör: Das Oszilloskop wird mit 4 passiven Tastkopfen geliefert, die für die meisten seriellen Busanwendungen ausreichend sind.

3. Anschluss: Sie können die seriellen Bussignale direkt an die Eingänge des Oszilloskops anschließen, indem Sie die mitgelieferten Tastköpfe verwenden.

4. Software: Die notwendige Software für die Dekodierung ist bereits im Gerät vorinstalliert.

Allerdings gibt es einige Situationen, in denen zusätzliches Zubehör nützlich sein könnte:

1. Differenzielle Messungen: Für einige Bustypen wie CAN könnte eine differenzielle Tastkopf wie der DPB4080 oder DPB5150 nützlich sein, um differenzielle Signale genauer zu messen.

2. **Logikanalysator**: Für komplexere digitale Analysen könnte das optionale 16-Kanal MSO-Modul (SDS1000X-E-16LA) hilfreich sein.

3. **Demo-Board**: Das optionale STB-3 Demo-Board könnte für Schulungs- und Demonstrationszwecke nützlich sein, da es verschiedene Signaltypen erzeugen kann, einschließlich I2C, CAN und LIN.


### Vertikales System

1. Kanäle aktivieren/deaktivieren:
   - Drücken Sie die Kanaltaste (CH1, CH2 etc.) auf der Frontplatte, um den Kanal ein- oder auszuschalten.
   - Ein aktivierter Kanal wird auf dem Bildschirm angezeigt und sein Menü erscheint.

2. Vertikale Skala und Position einstellen:
   - Verwenden Sie den SCALE-Knopf des jeweiligen Kanals, um die Volt/Division einzustellen.
   - Mit dem POSITION-Knopf können Sie die vertikale Position der Wellenform verschieben.

3. Kopplung, Bandbreitenbegrenzung, Sonde etc.:
   - Im Kanalmenü können Sie die Kopplung (AC, DC, GND) auswählen.
   - Die Bandbreitenbegrenzung kann aktiviert werden, um hochfrequentes Rauschen zu reduzieren.
   - Stellen Sie den korrekten Teilungsfaktor für Ihre Sonde ein (z.B. 1X, 10X).

### Horizontales System

1. Zeitbasis einstellen:
   - Nutzen Sie den horizontalen SCALE-Knopf, um die Zeit pro Division einzustellen.
   - Der POSITION-Knopf verschiebt den Trigger-Punkt horizontal.

2. Zoom-Funktion:
   - Aktivieren Sie den Zoom-Modus, um einen Teil der Wellenform vergrößert darzustellen.
   - Sie können gleichzeitig die Übersicht und den vergrößerten Ausschnitt sehen.

3. Roll-Modus:
   - Bei langsamen Zeitbasen (typisch ≥50 ms/div) wird der Roll-Modus automatisch aktiviert.
   - Die Wellenform "rollt" von rechts nach links über den Bildschirm.

### Erfassungssystem

1. Abtastrate und Speichertiefe:
   - Die Abtastrate wird automatisch basierend auf der Zeitbasis eingestellt.
   - Die Speichertiefe kann manuell oder automatisch gewählt werden (bis zu 14 Mpts).

2. Erfassungsmodus:
   - Normal: Standardmodus für die meisten Signale.
   - Spitzenwertdetektion: Erfasst schnelle Signalspitzen, gut für Störimpulse.
   - Mittelwert: Reduziert Rauschen durch Mittelung mehrerer Erfassungen.
   - Hochauflösung (Eres): Erhöht die vertikale Auflösung durch Überabtastung.

### Trigger-System

Trigger-Typen und Einstellungen:

1. Edge-Trigger:
   - Löst bei Überschreiten eines Spannungspegels aus
   - Einstellbar für steigende, fallende oder beide Flanken

2. Pulse-Trigger:
   - Triggert auf Pulse bestimmter Breite
   - Bedingungen wie "<", ">", "=" einer bestimmten Pulsbreite möglich

3. Slope-Trigger:
   - Reagiert auf Signalflanken mit bestimmter Anstiegs- oder Abfallzeit

4. Video-Trigger:
   - Speziell für Videosignale (NTSC, PAL, HDTV)
   - Trigger auf bestimmte Zeilen oder Felder möglich

5. Window-Trigger:
   - Definiert ein "Fenster" mit oberem und unterem Spannungspegel
   - Trigger beim Eintreten in oder Verlassen des Fensters

6. Interval-Trigger:
   - Löst aus basierend auf dem Zeitintervall zwischen zwei Flanken

7. Dropout-Trigger:
   - Erkennt, wenn ein Signal für eine bestimmte Zeit ausbleibt

8. Runt-Trigger:
   - Für Pulse, die eine Schwelle überschreiten, aber eine zweite nicht erreichen

9. Pattern-Trigger:
   - Triggert auf logische Kombinationen mehrerer Kanäle

10. Serielle Bus-Trigger (optional):
    - Für Protokolle wie I2C, SPI, UART, CAN, LIN

Holdoff und Kopplung:

1. Trigger-Holdoff:
   - Definiert eine Totzeit nach einem Trigger, in der kein neuer Trigger akzeptiert wird
   - Nützlich bei komplexen oder sich wiederholenden Signalen
   - Einstellbar von 80 ns bis 1.5 s

2. Trigger-Kopplung:
   - DC: Lässt alle Signalkomponenten durch
   - AC: Blockiert DC-Komponenten, nützlich bei Signalen mit großem DC-Offset
   - LF Reject: Unterdrückt niederfrequente Störungen
   - HF Reject: Filtert hochfrequente Störungen

3. Noise Rejection:
   - Erhöht die Trigger-Hysterese zur Unterdrückung von Rauschen

4. Trigger-Modus:
   - Auto: Triggert automatisch, wenn kein gültiger Trigger erkannt wird
   - Normal: Erfasst nur bei gültigem Trigger
   - Single: Einmaliger Trigger, dann Stopp

### serielle Bus-Analyse und Trigger-Funktionen für die Protokolle I2C, SPI, UART, CAN und LIN

1. Allgemeine Funktionen:
   - Dekodierung der seriellen Daten in lesbares Format
   - Trigger auf spezifische Protokoll-Events
   - Anzeige der dekodierten Daten als Overlay auf dem Analogsignal
   - Tabellarische Auflistung der dekodierten Daten

2. I2C (Inter-Integrated Circuit):
   - Trigger-Optionen: Start, Stop, Restart, NACK, Address, Data, Address & Data
   - Dekodierung von 7-Bit und 10-Bit Adressen
   - Anzeige von Start/Stop-Bedingungen, Adressen, Daten, ACK/NACK

3. SPI (Serial Peripheral Interface):
   - Unterstützung für 2-Wire und 3-Wire SPI
   - Trigger auf Datenpatterns
   - Einstellbare Bit-Ordnung (MSB/LSB first)
   - Dekodierung von MOSI und MISO Daten

4. UART (Universal Asynchronous Receiver/Transmitter):
   - Einstellbare Baudrate, Datenbits, Parität, Stop-Bits
   - Trigger auf Start-Bit, Daten, Parity-Error
   - Hexadezimale oder ASCII Darstellung der Daten

5. CAN (Controller Area Network):
   - Unterstützung für CAN 2.0A und 2.0B
   - Trigger auf Frame-Start, Frame-Typ, Identifier, Data, Error
   - Dekodierung von Standard- und Extended-Identifier, DLC, Daten, CRC

6. LIN (Local Interconnect Network):
   - Einstellbare Baudrate und LIN-Standard-Version
   - Trigger auf Sync Break, Identifier, Data, Error
   - Dekodierung von Sync, Identifier, Data, Checksum

Allgemeine Einstellungen:

- Konfiguration der Signalquellen (welche Kanäle für welche Busleitungen)
- Einstellung der Schwellenwerte für logisch High und Low
- Auswahl der Bit-Rate oder Abtastrate

Analyse-Features:

- Automatische Erfassung und Dekodierung der Busaktivität
- Tabellarische Anzeige der dekodierten Daten mit Zeitstempel
- Such- und Navigationsfunktionen innerhalb der dekodierten Daten
- Export der dekodierten Daten für weitere Analysen

## Überblick über den Inhalt des SDS1000X-E Service Manuals

1. Einleitung
   - Copyright und Erklärung
   - Produktzertifizierung
   - Allgemeine Sicherheitshinweise

2. Allgemeine Eigenschaften
   - Übersicht der Modelle und Hauptmerkmale

3. Vorbereitende Informationen
   - Funktionsprüfung (Einschalten, Tastkopf-Kompensation, Autokalibrierung)
   - Schnittstellentest (USB Host, USB Device, LAN, Pass/Fail Out)

4. Leistungstest
   - Erforderliche Ausrüstung
   - Testaufbau
   - Detaillierte Testprozeduren für verschiedene Parameter (DC-Genauigkeit, Offset, Zeitbasis, Trigger, Bandbreite etc.)

5. Demontageanleitung
   - Sicherheitshinweise
   - Benötigte Werkzeuge  
   - Schrittweise Anleitung zur Demontage für 2-Kanal und 4-Kanal Modelle

6. Lösung allgemeiner Probleme
   - Fehlersuche bei häufigen Problemen (kein Display, kein Signalbild etc.)

7. Fehlerbehebung
   - Sicherheitshinweise
   - Benötigte Ausrüstung
   - Flussdiagramm zur Fehlerbehebung
   - Detaillierte Prüfschritte für verschiedene Komponenten (Netzteil, Hauptplatine, Prozessorsystem, Erfassungssystem, LCD)


### Benötigte Ausrüstung

Das Manual listet die für die Fehlerbehebung erforderlichen Geräte auf:

- Digitalmultimeter: Genauigkeit ±0.05%, 1 mV Auflösung (empfohlen: SIGLENT SDM3065X oder Agilent 34401A)
- Oszilloskop: 200MHz Bandbreite, 1MΩ Eingangsimpedanz (empfohlen: SIGLENT SDS1204X-E)

### Flussdiagramm zur Fehlerbehebung

1. Start
2. Netzteil prüfen -> Wenn nicht in Ordnung: Netzteil ersetzen
3. Hauptplatine prüfen -> Wenn nicht in Ordnung: Hauptplatine ersetzen
4. LCD prüfen -> Wenn nicht in Ordnung: LCD ersetzen
5. Ende

### Detaillierte Prüfschritte für verschiedene Komponenten

a) Netzteil:

- Entfernen der Abdeckungen
- Messen der Ausgangsspannungen an bestimmten Testpunkten
- Vergleich mit Sollwerten (z.B. +6.5V ±10%, +3.4V ±100mV, etc.)

b) Hauptplatine:

- Überprüfung der Stromversorgung
- Hören auf Relais-Klicks beim Einschalten
- Prüfen verschiedener Spannungen auf der Platine

c) Prozessorsystem:

- Messen der Prozessor-Versorgungsspannungen an Testpunkten
- Überprüfung der Taktfrequenzen (z.B. 33.333333 MHz ±50PPM für Prozessor-Referenz)

d) Erfassungssystem:

- Messen der Versorgungsspannungen für das Erfassungssystem
- Überprüfung der Taktfrequenzen (z.B. 25.000000 MHz ±25PPM für Erfassungssystem-Takt)

e) LCD:

- Überprüfung der LCD-Versorgungsspannungen
- Messen der LCD-Signale (DCLK, VSYNC, HSYNC) und Vergleich mit Sollwerten
