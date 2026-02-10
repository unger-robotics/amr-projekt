# Grundlagen und Stand der Technik

## Woche 1: Architektur & Kinematik

**Thema:** Wie ist das System aufgebaut und wie bewegt es sich mathematisch?

### 1. ROS 2 & Middleware (DDS)

* **Quelle:** [01_Macenski_2022_ROS2_Arch.pdf]
* **Theorie:** Im Gegensatz zu ROS 1 nutzt ROS 2 keinen zentralen Master mehr, sondern den **Data Distribution Service (DDS)**.
* **Discovery:** Nodes finden sich automatisch im Netzwerk (Multicast), was die Verbindung zwischen Raspberry Pi und ESP32 robust macht.
* **Lifecycle Management:** Nodes haben definierte Zustände (`Unconfigured`, `Inactive`, `Active`). Das ist kritisch für Hardware-Treiber: Der Motor-Treiber darf erst Strom geben (`Active`), wenn die Parameter geladen sind.


* **Echtzeit auf Mikrocontrollern (micro-ROS):**
* **Quelle:** [14_Staschulat_2020_RCLC_Executor.pdf]
* Standard-ROS 2 (C++) ist zu speicherhungrig und nicht deterministisch genug für Regelkreise.
* Der **rclc-Executor** (C-API) garantiert eine deterministische Ausführungsreihenfolge (z. B. "Motor-Regelung immer vor WLAN-Ping").



### 2. Kinematik des Differentialantriebs

* **Quelle:** [04_Siegwart_2004_Mobile_Robots.pdf] (Kapitel 3)
* **Theorie:** Der Roboter unterliegt einer nicht-holonomen Zwangsbedingung (er kann nicht seitwärts fahren).
* **Vorwärtskinematik (Odometrie):** Berechnung der Pose  aus den Radgeschwindigkeiten .


* **Inverse Kinematik (Steuerung):** Umrechnung von Soll-Geschwindigkeiten  in Raddrehzahlen für die Motoren.



---

## Woche 2: SLAM (Simultaneous Localization and Mapping)

**Thema:** Wie baut der Roboter eine Karte und findet sich darin zurecht?

### 1. Graph-based SLAM (SLAM Toolbox)

* **Quelle:** [05_Macenski_SLAM_Toolbox.pdf]
* **Theorie:** Moderne SLAM-Systeme nutzen **Pose Graph Optimization**.
* **Der Graph:** Jeder Knoten ist eine Roboter-Pose, jede Kante ist eine Messung (Odometrie oder Laserscan-Match).
* **Loop Closure:** Erkennt der Roboter einen bereits besuchten Ort wieder, wird eine "Closing Edge" eingefügt. Ein Optimierungsalgorithmus (z. B. Ceres Solver) minimiert dann den Fehler im gesamten Graphen. Das korrigiert den akkumulierten Drift der Odometrie.
* **Lifelong Mapping:** Der Graph kann serialisiert (gespeichert) und später erweitert werden.



### 2. Vergleich der Verfahren

* **Quelle:** [13_MDPI_2025_SLAM_Comparison.pdf] & [06_Hess_2016_Cartographer.pdf]
* **Theorie:**
* **Gmapping (Partikelfilter):** Veraltet. Benötigt viele Ressourcen für Partikel, driftet stark bei großen Karten.
* **Cartographer (Submaps):** Baut lokale Unterkarten. Sehr präzise, aber speicherintensiv und komplex zu tunen.
* **SLAM Toolbox (Karto):** Bietet in aktuellen Benchmarks (2025) den besten Kompromiss aus CPU-Last und Genauigkeit für Embedded-Systeme wie den Pi 5.



---

## Woche 3: Hardware-Integration & Regelung

**Thema:** Wie wird die Theorie in echtzeitfähige Hardware umgesetzt?

### 1. Dual-Core Architektur (Partitionierung)

* **Quelle:** [12_Yordanov_2025_ESP32_Partitioning.pdf]
* **Theorie:** Auf Dual-Core-Mikrocontrollern (ESP32) konkurrieren Kommunikation (WLAN) und Regelung (Motor) um Rechenzeit.
* **Jitter:** Wenn der WLAN-Stack (Software-Interrupts) die Motor-Routine unterbricht, schwankt die Abtastzeit . Das macht PID-Regler instabil (-Anteil verstärkt Rauschen).
* **Lösung:** Strikte Trennung (Pinning). Core 0 übernimmt den `micro-ROS Agent` (Kommunikation), Core 1 übernimmt den `Control Loop` (Echtzeit).



### 2. Kaskadierte Regelung (PID)

* **Quelle:** [11_Albarran_2023_ESP32_DiffDrive.pdf]
* **Theorie:**
* **Low-Level (ESP32):** Ein Geschwindigkeitsregler (PID) sorgt dafür, dass die Räder die Soll-Drehzahl halten (Störgrößenausgleich, z. B. Teppichkante).
* *Anti-Windup:* Verhindert, dass der I-Anteil bei blockiertem Rad ins Unendliche läuft.
* *Dead-Zone:* Kompensation der Mindestspannung, die der Motor zum Anlaufen braucht.


* **High-Level (Nav2):** Ein Positionsregler sendet Geschwindigkeitsbefehle (`cmd_vel`).



### 3. Sensorfusion (EKF)

* **Quelle:** [10_Abaza_2025_ESP32_Stack.pdf]
* **Theorie:** Odometrie allein driftet unbegrenzt.
* **Extended Kalman Filter (EKF):** Fusioniert Encoder (präzise kurzfristig/linear) mit IMU (Gyroskop präzise bei Drehung). Das verringert den Fehler bei Radschlupf signifikant.



---

## Woche 4: Navigation & Autonomie

**Thema:** Wie plant der Roboter Wege und interagiert präzise mit der Umwelt?

### 1. Nav2 Architektur (Behavior Trees)

* **Quelle:** [02_Macenski_2023_Nav2_Survey.pdf]
* **Theorie:** Nav2 ersetzt starre Zustandsautomaten durch **Behavior Trees (BT)**.
* BTs sind modular und reaktiv (z. B. "Recovery"-Zweige: Wenn Weg blockiert -> Warte -> Drehe -> Plane neu).
* **Controller-Wahl:** Für Differential Drive und begrenzte Rechenleistung ist der **Regulated Pure Pursuit (RPP)** Controller dem DWB (Dynamic Window Approach) überlegen, da er Pfade glatter abfährt und oszillationsärmer ist.



### 2. Systematische Fehlerkorrektur (Kalibrierung)

* **Quelle:** [18_DeGiorgi_2024_Odom_Calibration.pdf]
* **Theorie:** Odometrie-Fehler teilen sich in *systematische* und *nicht-systematische* Fehler.
* Systematische Fehler (falscher Raddurchmesser, falscher Radabstand) akkumulieren sich deterministisch.
* Der **UMBmark-Test** (quadratischer Pfad) isoliert diese Fehler, sodass sie durch Anpassung der Kinematik-Parameter (`kinematics` Klasse) eliminiert werden können.



### 3. Visuelles Docking (ArUco)

* **Quelle:** [15_MDPI_2025_ArUco_Docking.pdf]
* **Theorie:** Lidar-basierte Navigation hat eine Genauigkeit von  cm. Für Ladekontakte ist das zu ungenau.
* **PnP-Problem (Perspective-n-Point):** Mit einem ArUco-Marker kann die Kamera die exakte 6D-Pose des Markers relativ zum Roboter berechnen.
* **Visual Servoing:** Ein geschlossener Regelkreis minimiert den lateralen Fehler (y-Achse) und den Winkelfehler (Yaw), um den Roboter zentriert in die Station zu führen.
