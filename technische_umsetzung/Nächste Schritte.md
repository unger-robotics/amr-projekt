# Nächste Schritte

PlatformIO: Projekt erstellen, Dateien in src einfügen, flashen.

Raspberry Pi: ROS 2 Workspace erstellen, Configs ablegen.

Docker: micro-ROS-agent starten.

Start: ros2 launch slam_toolbox ... und ros2 launch nav2_bringup

---



## Die "Formalia-Checkliste"

Damit deine inhaltlich starke Arbeit nicht durch Formfehler abgewertet wird, hier die versprochene Checkliste vor der Abgabe:

**I. Formale Konsistenz**

* [ ] **Einheiten:** Immer ein geschütztes Leerzeichen zwischen Zahl und Einheit (z. B. `50\,\mathrm{Hz}` oder `12\,\mathrm{V}`). In LaTeX: `50\,Hz`.
* [ ] **Abbildungen:** Jede Abbildung hat eine *Unterschrift* (unten), jede Tabelle eine *Überschrift* (oben).
* [ ] **Referenzierung:** Jede Abbildung/Tabelle wird im Text erwähnt ("Wie in Abbildung 4.2 zu sehen..."). Bilder, die nicht erklärt werden, gehören in den Anhang oder gelöscht.
* [ ] **Code:** Keine Screenshots von Code! Nutze Listings (Monospace Font, Syntax Highlighting).

**II. Zitierweise & Quellen**

* [ ] **Papers:** Hast du Macenski, Staschulat, DeGiorgi, Yordanov korrekt zitiert?
* [ ] **URLs:** GitHub-Repos und Datasheets brauchen ein "Abrufdatum" (Zugriff am: DD.MM.YYYY).
* [ ] **Plagiat:** Hast du wörtliche Zitate in Anführungszeichen? (Besser: Paraphrasieren).

**III. Sprache & Stil**

* [ ] **Aktiv/Passiv:** Bleibe konsistent. In technischen Arbeiten ist das "Passiv" oft üblich ("Es wurde gemessen..."), modernes "Wir" ("Wir zeigen...") ist seltener, "Ich" ("Ich habe gelötet") ist meist tabu.
* [ ] **Zeitformen:**
* Was du gemacht hast: **Präteritum** ("Der Roboter fuhr...").
* Was allgemein gilt (Theorie): **Präsens** ("Ein PID-Regler minimiert...").



**IV. Der "Rote Faden" Check**

* [ ] Passt das **Fazit** (Kap. 7) zur **Einleitung** (Kap. 1)? Werden die dort gestellten Fragen beantwortet?
* [ ] Werden alle **Anforderungen** aus dem Lastenheft (Kap. 3) in der **Validierung** (Kap. 6) geprüft?

---

### Nächster Schritt (Mein Angebot)

Du hast jetzt alles:

1. Die Theorie (Papers).
2. Den Code (Repo).
3. Die Gliederung (1-7).
4. Die Checkliste.

---

## Inhaltsverzeichnis

**1. Einleitung**
1.1 Ausgangssituation und Problemstellung
1.2 Zielsetzung und Forschungsfragen
1.3 Vorgehensweise und Methodik
1.4 Aufbau der Arbeit

**2. Grundlagen und Stand der Technik**
2.1 AMR in der Intralogistik und Entwicklungsmethodik
2.2 Mathematische Modellierung mobiler Roboter
2.3 Sensorik und Aktorik
2.4 Software-Architektur und Middleware
2.5 Kartierung und Lokalisierung (SLAM)
2.6 Autonome Navigation (Nav2)

**3. Anforderungsanalyse**
3.1 Szenariobeschreibung und Prozessanalyse
3.2 Technische Randbedingungen und Restriktionen
3.3 Funktionale Anforderungen
3.4 Nicht-funktionale Anforderungen
3.5 Anforderungsliste (Lastenheft)

**4. Systemkonzept und Entwurf**
4.1 Morphologischer Kasten und Konzeptauswahl
4.2 Gesamtsystemarchitektur
4.3 Mechanischer und Elektronischer Entwurf
4.4 Software-Architektur und Partitionierung
4.5 Entwurf der Regelung und Navigation

**5. Implementierung**
5.1 Hardwareaufbau und elektrische Inbetriebnahme
5.2 Firmware-Entwicklung auf dem ESP32
5.3 ROS 2 Systemintegration und Treiber
5.4 Kalibrierung und Mapping (SLAM)
5.5 Navigation und Applikationslogik
5.6 Systemtest und Validierung

**6. Validierung und Testergebnisse**
6.1 Testkonzept und Versuchsaufbau
6.2 Verifikation der Subsysteme
6.3 Validierung der Navigation
6.4 Validierung des Docking-Systems
6.5 Ressourcenverbrauch und Systemlast
6.6 Diskussion der Ergebnisse und Soll-Ist-Vergleich

**7. Fazit und Ausblick**
7.1 Zusammenfassung der Ergebnisse
7.2 Kritische Würdigung und Limitationen
7.3 Ausblick und Weiterentwicklung



