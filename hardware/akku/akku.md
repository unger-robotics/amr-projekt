# 3S1P Samsung INR18650-35E am IMAX B6AC V2

## Akkutyp und Grundkonfiguration

Der B6AC V2 stellt im **LiIon-Programm** die Ladeschlussspannung standardmäßig auf 4,10 V/Zelle ein. Die 35E erlaubt laut Datenblatt 4,20 V/Zelle – dieser Unterschied ist entscheidend für die Programmwahl.

| Parameter              | Einstellung        | Begründung                                                                              |
|------------------------|--------------------|-----------------------------------------------------------------------------------------|
| Akkutyp                | **LiIo** (LiIon)   | NCA-Zellchemie → Li-Ion-Ladeprofil                                                      |
| Zellenzahl             | **3S** (10,8 V)    | 3 Zellen in Reihe                                                                       |
| Modus                  | **Balance Charge** | Zellenausgleich über Balancer-Port                                                      |
| Ladestrom              | **1,7 A**          | 0,5C Standard; max. 2,0 A zulässig                                                      |
| Entladestrom           | **1,0 A**          | Ladegerät-Limit: 2,0 A; 5 W Entladeleistung begrenzt bei 10,8 V auf ca. 0,46 A effektiv |
| Entladeschlussspannung | **3,0 V/Zelle**    | Konservativ; Datenblatt erlaubt bis 2,65 V                                              |

## TVC-Einstellung (Terminal Voltage Control)


| Variante                        | TVC-Wert     | Packspannung | Kapazität   | Zyklenlebensdauer       |
|---------------------------------|--------------|--------------|-------------|-------------------------|
| **Zyklenoptimiert** (empfohlen) | 4,10 V/Zelle | 12,30 V      | ca. 85–90 % | Deutlich verlängert     |
| **Volle Kapazität**             | 4,20 V/Zelle | 12,60 V      | 100 %       | Standard (≥ 500 Zyklen) |

Die 4,10-V-Variante verlängert die Lebensdauer signifikant – Samsung empfiehlt diesen Wert explizit für E-Bike-/ESS-Anwendungen. Für das AMR-Projekt, bei dem die Zellen viele Zyklen durchlaufen, ist diese Einstellung sinnvoll. Die TVC-Änderung auf 4,20 V erfolgt über das Profilmenü unter `TVC=YOUR RISK`.

## Systemeinstellungen

| Parameter        | Wert              | Begründung                                     |
|------------------|-------------------|------------------------------------------------|
| Safety Timer     | **ON, 300 min**   | Puffer über die Standard-Ladezeit von ca. 4 h  |
| Capacity Cut-Off | **ON, 3.500 mAh** | Knapp über Nennkapazität als Sicherheitsgrenze |
| Temp Cut-Off     | **ON, 45 °C**     | Maximale Ladetemperatur laut Datenblatt        |
| Rest Time        | **10 min**        | Abkühlpause zwischen Lade-/Entladezyklen       |

## Profilspeicher-Beispiel

Im Speicherprofil (BATT MEMORY) sieht die Konfiguration so aus:

```
Akkutyp:               LiIo
Spannung:              10.8V (3S)
Ladestrom:             1.7A
Entladestrom:          1.0A
Entladeschlussspannung: 3.0V/Cell
TVC:                   4.10V  (oder 4.20V)
```

## Anschlussreihenfolge

Beim Laden immer beide Kabel anschließen: das Hauptladekabel (4-mm-Bananenstecker) **und** das Balancerkabel (JST-XH, 4-polig für 3S) am Balancer-Port. Der Lader prüft vor dem Start, ob die erkannte Zellenzahl (R) mit der eingestellten (S) übereinstimmt – erst bei `R:3SER S:3SER` den Vorgang bestätigen.

**Wichtig:** Die Entladeleistung des B6AC V2 beträgt nur 5 W. Bei einem 3S-Pack ergibt das einen effektiven maximalen Entladestrom von ca. $5\,\text{W} \div 10{,}8\,\text{V} \approx 0{,}46\,\text{A}$, auch wenn im Display 1,0 A eingestellt steht. Der Lader regelt den Strom automatisch herunter.

---

## Innenwiderstandsmessung (Bild 1)

| Zelle | Innenwiderstand |
|-------|-----------------|
| 1     | 58 mΩ           |
| 2     | 61 mΩ           |
| 3     | 64 mΩ           |

Die Werte liegen deutlich über den 35 mΩ aus dem Datenblatt (Einzelzelle, AC 1 kHz). Zwei Faktoren erklären die Differenz: Der B6AC V2 misst per DC-Pulsverfahren statt AC bei 1 kHz, was systematisch höhere Werte liefert. Zusätzlich addieren sich die Übergangswiderstände der Nickelstreifen, Lötverbindungen und Kabelstrecken bis zum Balancer-Port. Die Zellen untereinander liegen mit einer Spreizung von nur 6 mΩ (58 … 64 mΩ) eng beisammen – das deutet auf einen gut balancierten Pack mit gleichmäßiger Alterung hin.

## Zellenspannungen (Bild 2)

Alle drei Zellen zeigen **3,48 V** – absolut identisch. Laut SoC-Tabelle entspricht das ca. 20 % Ladezustand. Der Pack wurde also bereits merklich entladen, befindet sich aber noch im sicheren Bereich oberhalb der empfohlenen BMS-Abschaltung bei 3,0 V/Zelle.

## Laufender Ladevorgang (Bild 3)

```
LI3s  1.7A  10.85V
BAL   000:14  00004
```

Der Lader arbeitet im **LiIon Balance Charge**-Modus mit den richtigen Parametern: 3S-Konfiguration, 1,7 A Ladestrom (0,5C). Nach 14 Minuten Ladezeit hat er 4 mAh eingespeist und die Packspannung ist bereits von $3 \times 3{,}48\,\text{V} = 10{,}44\,\text{V}$ (Leerlauf) auf 10,85 V gestiegen. Die Differenz zwischen Leerlauf- und Klemmenspannung ($10{,}85\,\text{V} - 10{,}44\,\text{V} = 0{,}41\,\text{V}$) ergibt sich aus dem Spannungsabfall über den Innenwiderstand bei 1,7 A Ladestrom: $1{,}7\,\text{A} \times (58 + 61 + 64)\,\text{m}\Omega \approx 0{,}31\,\text{V}$ plus Kabel- und Kontaktwiderstände – das passt konsistent zusammen.

Der Ladevorgang wird bei ca. 20 % SoC Startpunkt etwa 3–3,5 Stunden bis zur Vollladung benötigen (CC-Phase bis 12,6 V bzw. 12,3 V bei TVC 4,10 V, dann CV-Phase bis Cut-off).
