# 3S1P Samsung INR18650-35E am IMAX B6AC V2 Ladegerät

## Akkutyp und Grundkonfiguration

Der B6AC V2 stellt im **LiIon-Programm** die Ladeschlussspannung standardmäßig auf 4,10 V/Zelle ein. Die 35E erlaubt laut Datenblatt 4,20 V/Zelle.

### Konfigurationstabelle: IMAX B6AC V2

**Geräteeinstellungen (BATT MEMORY)**

| Parameter                  | Einstellwert   | Begründung                                                                    |
|----------------------------|----------------|-------------------------------------------------------------------------------|
| **Akkutyp**                | LiIo (LiIon)   | Optimiert für NCA-Zellchemie.                                                 |
| **Zellenzahl / Spannung**  | 3S / 10,8 V    | 3 Zellen in Reihenschaltung.                                                  |
| **Lademodus**              | Balance Charge | Zwingend für Zellenausgleich über den Balancer-Port.                          |
| **Ladestrom**              | 1,7 A          | Entspricht schonenden 0,5C.                                                   |
| **Entladestrom**           | 1,0 A          | Hardware-Limit des Laders regelt effektiv auf ca. 0,46 A bei 10,8 V herunter. |
| **Entladeschlussspannung** | 3,0 V/Zelle    | Konservativer Schutzwert oberhalb der Datenblattgrenze von 2,65 V.            |
| **TVC (Ladeschluss)**      | 4,10 V/Zelle   | Zyklenoptimierte Einstellung zur signifikanten Erhöhung der Lebensdauer.      |

**Sicherheits- und Systemgrenzen (System Settings)**

| Parameter            | Einstellwert  | Begründung                                                      |
|----------------------|---------------|-----------------------------------------------------------------|
| **Safety Timer**     | ON, 300 min   | Sicherheitspuffer für den ca. 3,5- bis 4-stündigen Ladevorgang. |
| **Capacity Cut-Off** | ON, 3.500 mAh | Hardware-Abbruch knapp über der Nennkapazität.                  |
| **Temp Cut-Off**     | ON, 45 °C     | Maximal zulässige Ladetemperatur laut Zellenspezifikation.      |
| **Rest Time**        | 10 min        | Thermische Abkühlpause zwischen Zyklen.                         |


---

### Checkliste: IMAX B6AC V2 (3S1P Li-Ion)

**1. Hardware-Anschluss**

* [ ] Hauptladekabel (4-mm-Bananenstecker) eingesteckt?
* [ ] Balancerkabel (JST-XH, 4-polig) im 3S-Port eingesteckt?

**2. Systemeinstellungen (System Settings)**

* [ ] Safety Timer: **ON, 300 min**?
* [ ] Capacity Cut-Off: **ON, 3500 mAh**?
* [ ] Temp Cut-Off: **ON, 45 °C**?

**3. Ladeprofil (BATT MEMORY)**

* [ ] Akkutyp: **LiIo**?
* [ ] Zellenzahl: **3S (10.8V)**?
* [ ] Modus: **Balance**?
* [ ] Ladestrom: **1.7A**?
* [ ] TVC (Terminal Voltage): **4.10V**?

**4. Start-Freigabe (Pre-Flight)**

* [ ] Ladevorgang initiieren (ENTER gedrückt halten).
* [ ] Plausibilitätsprüfung des Laders abwarten.
* [ ] Display meldet exakt: **`R:3SER S:3SER`**?
* [ ] Vorgang mit ENTER final bestätigen.

---
