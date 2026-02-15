# Systemdokumentation-Audit

## 1 Zusammenfassung

Das vorliegende Audit prueft 9 Dokumentationsdateien des AMR-Projekts auf inhaltliche Korrektheit gegenueber dem Quellcode und `hardware/config.h`. Insgesamt wurden 18 Diskrepanzen identifiziert: 2 hoch, 5 mittel, 9 niedrig sowie 2 informelle Hinweise. Die READMEs sind nahezu fehlerfrei. Die technischen Dokumente in `hardware/docs/` weisen einen kritischen Frame-Bezeichnungsfehler auf. CLAUDE.md enthaelt den schwerwiegendsten Befund: einen veralteten Raddurchmesser, der dem deklarierten Single-Source-of-Truth-Prinzip widerspricht.

## 2 Methodik

Die Pruefung erfolgte als systematischer Zeilenvergleich jeder Dokumentationsdatei gegen primaere Ground-Truth-Quellen. Als autoritative Referenz dient `hardware/config.h`, die alle Hardware-Parameter zentral definiert. Ergaenzend wurden Firmware-Quelldateien (`main.cpp`, `robot_hal.hpp`), `platformio.ini`, `full_stack.launch.py`, `nav2_params.yaml`, `setup.py` und `docker-compose.yml` herangezogen. Der Audit gliedert sich in drei Bereiche: READMEs (3 Dateien), technische Referenzdokumentation in `hardware/docs/` (5 Dateien) sowie CLAUDE.md. Jeder dokumentierte Parameter wurde einzeln gegen den Quellcode verifiziert und bei Abweichung nach Schwere klassifiziert.

## 3 Befunde nach Dokumentgruppe

### 3.1 READMEs

Die drei README-Dateien erwiesen sich als nahezu fehlerfrei. Saemtliche Hardware-Parameter, PID-Gains, Docker-Konfigurationen, Launch-Parameter und Entry Points stimmen mit den Ground-Truth-Quellen ueberein. Die einzige Abweichung betrifft einen vereinfacht dargestellten Symlink-Pfad in der my_bot-README ohne funktionale Auswirkung.

### 3.2 hardware/docs

Unter den fuenf Dateien sticht ein Befund hervor: Die Umsetzungsanleitung bezeichnet in Anhang C.4 den dynamischen TF-Frame als `base_footprint`, waehrend Firmware, `odom_to_tf.py` und Launch-File einheitlich `base_link` verwenden. Die Kostendokumentation weist eine nicht nachvollziehbare Differenz zwischen `kosten.md` (487,98 EUR) und dem Abschlussbericht (~513 EUR) auf. In `toolchain_analyse.md` verwenden zwei Code-Beispiele den unkalibrierten Raddurchmesser 65.0 mm statt 65.67 mm. Weitere Befunde betreffen unvollstaendige Skript-Auflistungen und eine geringe dt-Ungenauigkeit. Die Kalibrierungsanleitung ist fehlerfrei.

### 3.3 CLAUDE.md

Die CLAUDE.md weist 9 Befunde auf. Der schwerwiegendste ist der Raddurchmesser von 65 mm (statt 65.67 mm), der dem deklarierten Single-Source-of-Truth-Prinzip widerspricht. Die Topic-Tabelle referenziert einen nicht existierenden `robot_state_publisher`-Node statt `static_transform_publisher`. Die Versionsangabe der Umsetzungsanleitung (v2.0 statt v3.0), eine unvollstaendige Skript-Aufzaehlung, ein irrefuehrendes "Nur Kamera"-Beispiel und eine unpraezise LED-Status-Beschreibung bilden die weiteren Befunde.

## 4 Redundanzanalyse

Zentrale Parameter wie Raddurchmesser, Spurbreite, Encoder-Ticks, PWM-Deadzone, Failsafe-Timeout und PID-Gains werden in bis zu fuenf Dokumentationsdateien redundant gefuehrt. Die Mehrzahl dieser Werte ist konsistent: Spurbreite (178 mm), Encoder-Ticks (~748), PWM-Deadzone (35), Failsafe-Timeout (500 ms), PID-Gains (0.4/0.1/0.0) und EMA-Filter (alpha=0.3) stimmen ueberall ueberein.

Der kritischste Inkonsistenzfall betrifft den Raddurchmesser. Nach der Boden-Kalibrierung wurde `config.h` korrekt auf 65.67 mm aktualisiert. Die ESP32-README, `hardware-setup.md` und die Kalibrierungsanleitung fuehren den kalibrierten Wert. Hingegen verwenden CLAUDE.md (65 mm) und zwei Code-Beispiele in `toolchain_analyse.md` (0.065f) weiterhin den urspruenglichen Wert. Diese partielle Aktualisierung ist typisch fuer verteilte Dokumentation und unterstreicht die Bedeutung des Single-Source-of-Truth-Ansatzes.

Die Versionsangabe der Umsetzungsanleitung ist ein weiterer Redundanz-Konflikt: CLAUDE.md nennt v2.0, die Datei selbst deklariert v3.0. Alle uebrigen redundanten Informationen (Docker-Konfiguration, Launch-Parameter, TF-Baum, micro-ROS-Constraints) sind dateienuebergreifend konsistent.

## 5 Befund-Uebersicht

| Nr | Schwere | Datei(en) | Befund | Ground Truth |
|---|---|---|---|---|
| D01 | Hoch | CLAUDE.md (Zeile 200) | Raddurchmesser als 65 mm dokumentiert | `config.h` Zeile 54: `WHEEL_DIAMETER 0.06567f` = 65.67 mm (kalibriert) |
| D02 | Hoch | umsetzungsanleitung.md (Anhang C.4) | TF-Frame als `odom -> base_footprint` bezeichnet | `main.cpp` Zeile 248 und `odom_to_tf.py`: `base_link` |
| D03 | Mittel | CLAUDE.md (Zeile 143) | `robot_state_publisher` als TF-Quelle genannt | Kein solcher Node im Launch-File; statische TFs von `static_transform_publisher` |
| D04 | Mittel | CLAUDE.md (Zeile 253) | Umsetzungsanleitung als "v2.0" bezeichnet | `umsetzungsanleitung.md` Zeile 8: Version 3.0 |
| D05 | Mittel | CLAUDE.md (Zeile 214) | Skript-Beschreibung verschweigt `hardware_info.py` | 12 .py-Dateien in `amr/scripts/`, `hardware_info.py` fehlt in der Aufzaehlung |
| D06 | Mittel | toolchain_analyse.md (Abschnitt 3.2) | Zwei Code-Beispiele mit `WHEEL_DIAMETER 0.065f` | `config.h`: kalibrierter Wert `0.06567f` |
| D07 | Mittel | kosten.md vs. abschlussbericht.md | Gesamtkosten 487,98 EUR vs. ~513 EUR | Differenz (~25 EUR) nicht nachvollziehbar herleitbar |
| D08 | Niedrig | CLAUDE.md (Zeile 201) | Gier-Toleranz als 8 Grad dokumentiert | `nav2_params.yaml`: `yaw_goal_tolerance: 0.15` rad = 8.59 Grad |
| D09 | Niedrig | CLAUDE.md (Zeile 121) | LED-Status "Dauer-An = Publish-Fehler" | `main.cpp`: LED auf 255 gesetzt, aber kein `return` -- naechster Zyklus ueberschreibt |
| D10 | Niedrig | CLAUDE.md (Zeile 34) | Launch-Beispiel "Nur Kamera" suggeriert isolierten Kamera-Betrieb | Agent, RPLidar und odom_to_tf laufen stets mit |
| D11 | Niedrig | hardware-setup.md (Abschnitt 11.7) | Beschleunigungsrampe mit festem dt = 0.02s dokumentiert | `main.cpp` Zeile 49/85: dynamisches `dt` aus Zeitdifferenz berechnet |
| D12 | Niedrig | umsetzungsanleitung.md (Abschnitt 1.6) | Verweis auf frueheren Failsafe-Wert 1000 ms | `config.h` Zeile 93: 500 ms (Hinweis korrekt formuliert, aber potenziell verwirrend) |
| D13 | Niedrig | umsetzungsanleitung.md (Anhang B) | `hardware_info.py` fehlt in Skript-Tabelle | Datei existiert in `amr/scripts/` |
| D14 | Niedrig | umsetzungsanleitung.md (Anhang C.5) | `hardware_info.py` und `amr_utils.py` fehlen in Quelldateien-Tabelle | Beide Dateien existieren in `amr/scripts/` |
| D15 | Niedrig | toolchain_analyse.md (Abschnitt 3.2) | "28 Defines in config.h" | Tatsaechlich 26 aktive `#define`-Direktiven |
| D16 | Niedrig | my_bot README (Paketstruktur) | Symlink-Pfad vereinfacht als `amr/scripts/amr_utils.py` | Tatsaechlich relativer Pfad mit 5 Ebenen (`../../../../../scripts/amr_utils.py`) |
| D17 | Info | CLAUDE.md (Zeile 108) | "Encoder-Feedback (Hall, Quadratur A+B)" | Korrekt, aber "Hall" allein wenig aussagekraeftig |
| D18 | Info | my_bot README (Standalone-Skripte) | 4 Standalone-Skripte gelistet | Vollstaendig fuer Nicht-ROS2-Skripte; kein Fehler |

## 6 Empfehlungen

Die folgenden Massnahmen sind nach Dringlichkeit priorisiert.

**Sofort (hohe Diskrepanzen):**

- D01: Den Raddurchmesser in CLAUDE.md von 65 mm auf 65.67 mm korrigieren. Dieser Wert wurde durch Boden-Kalibrierung ermittelt und ist in `config.h` als autoritative Quelle hinterlegt.
- D02: In `umsetzungsanleitung.md` Anhang C.4 den Frame-Namen `base_footprint` durch `base_link` ersetzen. Saemtliche Quellcode-Referenzen verwenden konsistent `base_link`.

**Naechste Revision (mittlere Diskrepanzen):**

- D03: In der CLAUDE.md Topic-Tabelle `robot_state_publisher` durch `static_transform_publisher` ersetzen.
- D04: Die Versionsangabe der Umsetzungsanleitung in CLAUDE.md von v2.0 auf v3.0 aktualisieren.
- D05: `hardware_info.py` in der Skript-Beschreibung der CLAUDE.md ergaenzen oder die Zaehlung auf 12 Skripte (plus Shared-Modul) korrigieren.
- D06: Die Code-Beispiele in `toolchain_analyse.md` Abschnitt 3.2 auf den kalibrierten Wert `0.06567f` aktualisieren.
- D07: Die Gesamtkosten im Abschlussbericht mit einer nachvollziehbaren Herleitung versehen oder an den Wert aus `kosten.md` angleichen.

**Optional (niedrige Diskrepanzen):**

- D08-D16 betreffen Rundungen, vereinfachte Darstellungen und unvollstaendige Auflistungen in Anhaengen. Diese Punkte haben keine funktionale Auswirkung, sollten aber bei der naechsten umfassenden Dokumentationsrevision bereinigt werden. Besonders empfehlenswert ist die Ergaenzung fehlender Skripte in den Anhaengen B und C.5 der Umsetzungsanleitung (D13, D14) sowie die Praezisierung der LED-Status-Beschreibung (D09) und des "Nur Kamera"-Beispiels (D10) in CLAUDE.md.
