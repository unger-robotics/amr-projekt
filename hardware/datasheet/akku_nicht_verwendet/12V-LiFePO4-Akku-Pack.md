# 12V-LiFePO4-Akku-Pack

### 1. Check

* **Zellen (Cottcell IFR26650):** 4 Stück ergeben $12,8\text{ V}$ Nennspannung. Flacher Pluspol ("Flat Top") passt perfekt in die Halter,.
* **Halter (Keystone 1108):** Das ist ein **Doppelhalter**. Sie brauchen **2 Stück** davon (ergibt 4 Plätze). Die Kontakte sind massiv und vergoldet/vernickelt – viel besserer Stromfluss als bei einfachen Spiralfedern. **Achtung:** Sie müssen 2 Stück bestellen ($2 \times 9,15\text{ €} \approx 18,30\text{ €}$).
* **BMS (i-tecc 4S 12A):** Passt exakt. 12 A Dauerlast reicht locker für Ihren Roboter (Pi 5 + Motoren ziehen $\approx 4\text{ A}$). Ladeschluss $14,4\text{ V}$ passt zum LiFePO4-Ladeprogramm.
* **Wandler (DC/DC 5V 5A):** Der Eingangsbereich $8\text{--}32\text{ V}$ deckt Ihren Akku ($10\text{--}14,6\text{ V}$) komplett ab. Liefert genug Power für den Raspberry Pi 5.

---

### 2. Zusammenfassung: Ihr Bauplan für den "AMR Power-Pack"

#### A. Die Einkaufsliste

1. **4x** Akku: Cottcell IFR26650 ($3300\text{ mAh}$, LiFePO4).
2. **2x** Halter: Keystone 1108 (bei Reichelt).
3. **1x** BMS: i-tecc LiFePO4 4S 12A.
4. **1x** Wandler: DC-DC 12V/24V auf 5V USB-C (5A).

#### B. Verkabelung (Schritt-für-Schritt)

**Schritt 1: Mechanik**

* Kleben Sie die beiden Keystone-Halter Rücken an Rücken oder nebeneinander zu einem festen Block zusammen.
* Setzen Sie die Zellen **noch nicht** ein!

**Schritt 2: Die Brücken (Dicke Kabel $1,5\text{ mm}^2$)**
Wir bauen eine Serienschaltung (4S).

* Verbinden Sie die Lötfahnen der Halter so:
  * **Halter 1 (Zelle 1) Minus** $\rightarrow$ Dies ist der Haupt-Minus für das BMS (**B-**).
  * Halter 1 (Zelle 1) Plus $\rightarrow$ Halter 1 (Zelle 2) Minus.
  * Halter 1 (Zelle 2) Plus $\rightarrow$ Halter 2 (Zelle 3) Minus.
  * Halter 2 (Zelle 3) Plus $\rightarrow$ Halter 2 (Zelle 4) Minus.
  * **Halter 2 (Zelle 4) Plus** $\rightarrow$ Geht zur **Sicherung** (Haupt-Plus).

**Schritt 3: Das BMS (Dünne Kabel $0,25\text{ mm}^2$)**
Löten Sie die Messleitungen genau an die Punkte, wo Sie eben die Brücken gebaut haben:

1. **0V (Schwarz):** An Minus Zelle 1.
2. **3.6V:** An Plus Zelle 1.
3. **7.2V:** An Plus Zelle 2.
4. **10.8V:** An Plus Zelle 3.
5. **14.4V (Rot):** An Plus Zelle 4.

**Schritt 4: Leistungsanschluss**

* Löten Sie das dicke Kabel von **Minus Zelle 1** an das Pad **B-** auf dem BMS.
* Der Ausgang Ihres Akkus ist nun:
  * **MINUS:** Das Pad **P-** am BMS.
  * **PLUS:** Das Ende der Sicherung (die an Plus Zelle 4 hängt).

**Schritt 5: Komponenten anschließen**
An Ihren neuen Akku-Ausgang (P- und Sicherung) kommen parallel:

1. Der **DC/DC-Wandler** (USB-C Stecker in den Pi).
2. Der **Motortreiber MDD3A** (Schraubklemmen Power Input).

#### C. Inbetriebnahme

1. Zellen einlegen (auf Polung achten!).
2. Sicherung einstecken (15 A).
3. **Wichtig:** Falls am Ausgang (P-) keine Spannung anliegt $\rightarrow$ Kurz das Ladegerät anschließen ("Impuls"), um das BMS zu wecken.
4. Lader (IMAX B6) auf **LiFe 4S (3.3V)** stellen und voll laden.
