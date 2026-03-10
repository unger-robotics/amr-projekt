# Abaza (2025) -- AI-Driven Dynamic Covariance for ROS 2 Mobile Robot Localization

## Bibliografische Angaben
- **Autor:** Bogdan Felician Abaza
- **Institution:** Manufacturing Engineering Department, National University of Science and Technology POLITEHNICA Bucharest, Rumaenien
- **Venue:** Sensors 2025, 25(10), 3026
- **DOI:** https://doi.org/10.3390/s25103026
- **Eingereicht:** 14. April 2025, angenommen: 9. Mai 2025, publiziert: 11. Mai 2025
- **Open Access:** CC BY 4.0
- **Repositories:** [ROS_ESP32_Bridge](https://github.com/bogdan-abaza/ROS_ESP32_Bridge), [ai_tools](https://github.com/bogdan-abaza/ai_tools)

## Zusammenfassung (Abstract)

Die Studie evaluiert einen KI-gestuetzten Ansatz zur dynamischen Anpassung von Kovarianzparametern fuer verbesserte Pose-Schaetzung bei einem Differentialantrieb-Roboter unter ROS 2. Ein Regressionsmodell (Random Forest) wurde in das `robot_localization`-Paket integriert, um die EKF-Kovarianz in Echtzeit anzupassen. Die Experimente in einer kontrollierten Indoor-Umgebung zeigen, dass die KI-gestuetzte dynamische Kovarianz-Vorhersage die Yaw-Vorhersagefehler bei statischer und moderater Dynamik auf Medianwerte von 0.0362 rad bzw. 0.0381 rad reduziert -- mit engeren Interquartilsbereichen (0.0489 rad statisch, 0.1069 rad moderat) gegenueber der Baseline (0.0222 rad, 0.1399 rad). Bei aggressiver Dynamik stiegen die Fehler auf bis zu 0.9491 rad aufgrund unzureichender Trainingsdaten fuer schnelle Rotationsbewegungen.

## Kernaussagen

### 1. Hardware-Plattform AMR2AX (S. 5-6)
- Eigenentwickelter Differentialantrieb-Roboter "AMR2AX", entwickelt von Studierenden im Rahmen einer universitaeren Lehrveranstaltung (S. 5)
- Modulares Aluminium-Chassis (U-Channel + Metallwinkel), CAD-basierter iterativer Designprozess (S. 5)
- **Komponentenliste (Table 1, S. 6):**
  - Antrieb: NeveRest 40 DC-Getriebemotoren mit Quadratur-Encodern (kettengetrieben)
  - Motortreiber: Pololu VNH5019 Motor Shield
  - Mikrocontroller: ESP32 NodeMCU-32S (Motorsteuerung + Encoder-Feedback)
  - Prozessor: Raspberry Pi 4 (4 GB RAM), Ubuntu 22.04 LTS, ROS 2 Humble
  - IMU: BNO-055 (USB-Anbindung an RPi)
  - Lidar: LDROBOT STL-19 (USB-Anbindung an RPi)
  - Kamera: Logitech C922 Pro HD (fuer zukuenftige Vision-Integration)
  - Stromversorgung: 12 V NiMH-Akku

### 2. Kommunikationsarchitektur ESP32 <-> Raspberry Pi (S. 6-7)
- ESP32 kommuniziert mit Raspberry Pi ueber **serielle Vollduplex-Verbindung** (USB-Link), nicht ueber WiFi (S. 6)
- Custom-Paket `ROS_ESP32_Bridge` fuer die serielle Kommunikation entwickelt (S. 7)
- ESP32 publiziert Rad-Zustandsdaten (Odometrie, Joint States) als ROS 2 Topics und empfaengt Velocity Commands (S. 6-7)
- Die Architektur unterscheidet sich vom eigenen Projekt: Abaza nutzt **ros2_control + diff_drive_controller** statt micro-ROS/UART (S. 7)
- Das Paket ist modular und kann fuer verschiedene Motortreiber und Encoder angepasst werden (S. 7)

### 3. Software-Stack und ROS 2 Setup (S. 7-8)
- ROS 2 Humble auf Raspberry Pi 4 mit Ubuntu 22.04 LTS (S. 7)
- `ros2_control` Framework mit `diff_drive_controller` Plugin fuer Differentialantrieb-Kinematik (S. 7)
- Radparameter, Grenzwerte und Odometrie-Kovarianz-Schaetzungen in `ros_control.yaml` definiert (S. 7)
- Regelrate: 20-50 Hz fuer Encoder-Feedback und Positionsberechnung (S. 7)
- **AMR2AX Bringup-Paket** initialisiert alle Hardware- und Software-Komponenten (S. 8):
  - `base.launch.py`: Controller, ros2_control_node, EKF (ekf_node) aus robot_localization
  - `sensors.launch.py`: BNO-055 IMU- und LD19 Lidar-Treiber
- `robot_state_publisher` fuer URDF-basierte TF-Transforms (S. 8)
- Gefilterte Odometrie wird auf `/platform/odom/filtered` publiziert (S. 8)

### 4. EKF-Konfiguration mit robot_localization (S. 8-9)
- **EKF-Node (ekf_node)** fusioniert Rad-Odometrie und IMU-Daten (S. 8)
- **Odometrie-Konfiguration (odom0)** -- Topic: `/odom` (S. 8):
  - odom0_config: Nutzt vx, vy (linear velocities) und yaw-Rate (angular z) + yaw (orientation)
  - `odom0_differential: true` -- differentielle Verarbeitung fuer Drift-Schutz
- **IMU-Konfiguration (imu0)** -- Topic: `/bno055/imu_raw` (S. 8):
  - imu0_config: Nutzt Roll, Pitch, Yaw (Orientierung)
  - `imu0_differential: false` -- absolute Orientierungswerte
- Designentscheidung: Odometrie ist besser fuer lineare Bewegung/Yaw-Drift (differential mode), IMU liefert glattere absolute Messungen fuer Rotationszustaende (S. 8)
- **Problem statischer Kovarianzen:** Unzureichend bei variablen Bedingungen wie Motorschlupf, unebene Oberflaechen, Sensorrauschen durch Waerme/Spannungsschwankungen (S. 8)
- System operiert bei 50 Hz mit zeitgestempelten Nachrichten und konsistenten TF-Frames (S. 9)

### 5. Datenerfassung und Feature Engineering (S. 9-11)
- Datensatz durch manuelle Teleoperation erfasst: verschiedene Bewegungsprofile (vorwaerts/rueckwaerts, Kurven, gemischte Trajektorien) (S. 9)
- Aufgezeichnete ROS 2 Topics: `/odom`, `/platform/odom/filtered`, `/cmd_vel`, `/bno055/imu_raw`, `/joint_states` (S. 9)
- rosbag-Aufzeichnung mit spezifischem Befehl, Konvertierung in CSV (S. 9-10)
- Datensatz v7: ueber 21.000 Samples (90/10 Train/Test-Split) (S. 11)
- **15 Input-Features** fuer das ML-Modell (S. 10-11):
  - Beschleunigungen: acc_x, acc_y, acc_z (m/s^2) von IMU
  - Gyroskop: gyro_z (rad/s) von IMU
  - Odometrie-Geschwindigkeiten: linear_x (m/s), angular_z (rad/s)
  - Orientierung: yaw_odom, yaw_filtered (rad)
  - Yaw-Diskrepanz: yaw_diff = yaw_odom - yaw_filtered (rad)
  - Interaktionsterme: acc_y_mul_gyro_z, gyro_z_mul_linear_x
  - Kommandierte Geschwindigkeiten: cmd_linear_x, cmd_angular_z
  - Temporale Aenderungen: delta_angular_z, delta_cmd_angular_z
- **Target-Variablen:** error_x (m), error_y (m), error_yaw (rad) (S. 11)
- Fehlerberechnung: Differenz zwischen Roh-Odometrie und gefiltertem EKF-Output (S. 10)

### 6. KI-Modellwahl: Random Forest Regressor (S. 11-13)
- **Vergleich verschiedener ML-Modelle fuer Raspberry Pi 4** (S. 11):
  - DNNs (z.B. YOLOv8 Medium): bis 3671 ms Inferenz -- zu langsam
  - RNNs/LSTMs: sequentielle Natur -> hoher Overhead -> nicht echtzeitfaehig auf RPi 4
  - Gaussian Processes: O(n^3) Skalierung -> unfeasible fuer 21k Samples
  - **Random Forest Regressor: gewaehlt** wegen Genauigkeit/Effizienz-Balance
- Random Forest mit 100 Baeumen, scikit-learn Standardhyperparameter (S. 12)
- **Trainings-Performance (S. 12, 16):**
  - MAE gesamt: 0.0061
  - R^2 gesamt: 0.989
  - R^2 pro Dimension: error_x (0.98), error_y (0.97), error_yaw (0.99)
- **Inferenzzeit: ~10 ms** auf Raspberry Pi 4 (S. 12)
- Ressourcenverbrauch: ~15% CPU, ~120 MB RAM (S. 12)
- Out-of-Bag (OOB) Fehler stabilisiert sich nach ~30 Baeumen (S. 13)
- Vergleich mit LightGBM (1-5% niedrigerer MAE, aber 15-20 ms Latenz, 20-25% CPU) und Compact MLPs (5-10 ms, aber 5-10% hoeherer MAE, 25-30% CPU) (S. 12)

### 7. Dual-Node ROS 2 Architektur fuer KI-Integration (S. 13-15)
- **ai_tools Paket** mit zwei Kernknoten, gestartet via `ai_covariance.launch.py` (S. 13):
  - `enable_ai` Parameter (Standard: true) zum Ein-/Ausschalten der KI-Inferenz
- **ai_covariance_node** (Inferenz-Engine, S. 14):
  - Subscribes: `/odom`, `/bno055/imu_raw`, `/cmd_vel`
  - Berechnet alle 0.2 s einen Feature-Vektor (15 Features)
  - Laedt vortrainiertes Random Forest Modell (`ai_covariance_model_full.joblib`)
  - Publiziert Fehler-Vorhersagen auf `/ai_tools/covariance_prediction` (Float32MultiArray)
  - Wenn `enable_ai=false`: publiziert Nullen (0.0 fuer alle Fehler)
  - Kontinuierliches Datalogging in CSV-Dateien fuer spaeteres Re-Training
- **ai_covariance_updater** (Kovarianz-Update-Knoten, S. 15):
  - Subscribes: `/ai_tools/covariance_prediction`
  - Berechnet Kovarianzen als Quadrat der vorhergesagten Fehler: cov_x = error_x^2 (m^2), cov_y = error_y^2 (m^2), cov_yaw = error_yaw^2 (rad^2)
  - Konstruiert 6x6 Kovarianzmatrix: cov_x auf Position [0,0], cov_y auf [7,7], cov_yaw auf [35,35], Rest: 1e-3
  - **Aktualisiert EKF dynamisch** via `/ekf_node/set_parameters` Service (Async-Call fuer `initial_estimate_covariance`)
  - Publiziert Kovarianzen auf `/ai_tools/covariance` (Float32MultiArray)

### 8. Datalogging-Pipeline fuer iteratives Re-Training (S. 10, 14-15)
- `ai_covariance_node` erstellt bei jedem Start eine CSV-Logdatei mit Zeitstempel (S. 14)
- Log-Intervall: alle 0.2 s (S. 14)
- Protokollierte Daten: ROS 2 Timestamps, verstrichene Zeit, AI-Status, vorhergesagte Fehler, alle 15 Features (S. 14)
- Datensatz wuchs iterativ von 16.000 auf ueber 21.000 Samples durch Integration operationeller Logs (S. 10, 22)
- Ermoeglicht zukuenftiges Online Learning und automatisierte Re-Training-Pipelines (S. 14-15)

### 9. Experimentelles Setup: Drei Bewegungsregime (S. 16-17)
- Real-World-Tests mit autonomer Nav2-Navigation zwischen 4 Wegpunkten (S. 16)
- Vergleich: AI-enabled vs. AI-disabled (statische Kovarianzen) (S. 16)
- **Drei Bewegungsregime** basierend auf |cmd_angular_z| (S. 16-17):
  - Static: |cmd_angular_z| <= 0.01 rad/s
  - Moderate: 0.01 < |cmd_angular_z| <= 0.7 rad/s
  - Aggressive: |cmd_angular_z| > 0.5 rad/s (angepasst, da keine Werte > 0.7 rad/s auftraten)
- Ausreisser-Filterung: |error_yaw| > 1.5 rad oder |yaw_diff| > 1.5 rad wurden entfernt (S. 17)

### 10. Ergebnisse: Raeumliche Fehler (AI-enabled) (S. 17-18, Table 2)
- **Static:** error_x Mean = -0.0021 m (Std 0.0892), error_y Mean = 0.0526 m (Std 0.0926)
- **Moderate:** error_x Mean = -0.0570 m (Std 0.0935), error_y Mean = 0.0790 m (Std 0.0573)
- **Aggressive:** error_x Mean = -0.1596 m (Std 0.0829), error_y Mean = 0.0927 m (Std 0.0825)
- Raeumliche Fehler in der realen Welt groesser als im Training (MAE Training: 0.0052 m fuer error_x, 0.0035 m fuer error_y) (S. 18)

### 11. Ergebnisse: Yaw-Vorhersagefehler (S. 18-19, Table 3)
- Metrik: |error_yaw - yaw_diff| (Diskrepanz zwischen vorhergesagtem und tatsaechlichem Yaw-Fehler)
- **Static:** Mean 0.0543 rad (Std 0.0899), Median 0.0362 rad, IQR 0.0489 rad
- **Moderate:** Mean 0.0710 rad (Std 0.0975), Median 0.0381 rad, IQR 0.1069 rad
- **Aggressive:** Mean 0.2257 rad (Std 0.2600), Max 0.9491 rad

### 12. AI vs. Baseline-Vergleich (S. 19-20)
- **AI-enabled (IQR):** Static 0.0489 rad, Moderate 0.1069 rad -- **engere Verteilungen**
- **AI-disabled (IQR):** Static 0.0222 rad, Moderate 0.1399 rad, Std Moderate 0.1070 rad
- AI-enabled zeigt konsistentere Lokalisierung bei statischer und moderater Dynamik (S. 19-20)
- Maximum yaw_diff: AI-enabled 0.4943 rad vs. AI-disabled 0.5771 rad (S. 19)
- **Wichtig:** Bei aggressiver Dynamik bleibt die AI-Variante herausfordernd -- hoehere IQR (0.2695 rad) und Standardabweichung (0.2097 rad) (S. 19)

### 13. Echtzeit-Performance auf Raspberry Pi 4 (S. 17)
- AI-System (ai_covariance_node + ai_covariance_updater): max. 20 Hz, stabil bei 5-10 Hz (S. 17)
- Baseline (ohne AI): 50 Hz (S. 17)
- CPU-Auslastung: durchschnittlich 25%, Peak 40% (S. 17)
- RAM-Verbrauch: ca. 350 MB (innerhalb 4 GB) (S. 17)
- Echtzeitfaehig fuer ROS 2 Navigationsanforderungen (typisch 50-100 Hz) (S. 17)

### 14. Limitationen und Herausforderungen (S. 21-22)
- **Aggressive Dynamik:** Fehler bis 0.9491 rad wegen unzureichender Trainingsdaten fuer schnelle Rotationen (S. 21-22)
- Random Forest hat begrenzte Extrapolationskapazitaet bei extremen Eingaben (S. 22)
- EMA-Glaettung (alpha = 0.7) bei Runtime erzeugt Mismatch zwischen Training und Inferenz (S. 11)
- Modell nur offline trainiert, kein Online Learning waehrend des Betriebs (S. 22)
- Keine statistische Signifikanztests (z.B. Wilcoxon Signed-Rank) durchgefuehrt (S. 22)

### 15. Vorgeschlagene Verbesserungen (S. 22)
- Erweiterung des Datensatzes mit aggressiveren Rotationsmanoevern (S. 22)
- LSTM-basiertes temporales Modell fuer sequentielle Muster (mit Sliding Windows, Model Quantization) (S. 22)
- Integration visueller Features von RGB-Kamera fuer raeumlichen Kontext (S. 22)
- Online Learning / Continual Learning waehrend des Betriebs (S. 22)
- Federated Learning fuer Multi-Roboter-Systeme (S. 22)
- Dynamische Schwellenwerte: Umschalten zwischen AI und statischem Fallback bei aggressiver Dynamik (S. 22)
- Deployment in industriellen Umgebungen mit variablen Lasten und unebenen Boeden (S. 22)

## Relevanz fuer die Projektarbeit

Diese Studie ist die **wichtigste Vergleichsquelle** fuer die eigene Projektarbeit, da sie einen nahezu identischen Hardware-Stack verwendet: ESP32-Mikrocontroller fuer Low-Level-Motorsteuerung, Raspberry Pi als High-Level-Rechner, ROS 2 Humble als Middleware und Differentialantrieb als Kinematikmodell. Der zentrale Unterschied liegt in der Kommunikationsschicht: Abaza nutzt ein eigenes `ROS_ESP32_Bridge`-Paket ueber USB-Serial mit `ros2_control`/`diff_drive_controller`, waehrend die eigene Arbeit micro-ROS ueber UART einsetzt -- ein architektonisch relevanter Vergleichspunkt fuer die Diskussion von Echtzeit-Determinismus und Protokoll-Overhead.

Die EKF-Konfiguration mit `robot_localization` (odom0 im Differential-Modus, imu0 als absolute Orientierung, 50 Hz Takt) bietet eine direkt uebertragbare Referenzkonfiguration. Die identifizierte Problematik statischer Kovarianzen bei variablen Betriebsbedingungen (Motorschlupf, Oberflaechenwechsel, thermisches Sensorrauschen) ist unmittelbar relevant fuer die Validierung des eigenen Systems.

Besonders wertvoll sind die konkreten Messwerte: raeumliche Fehler im Bereich von -0.31 bis +0.23 m und Yaw-Fehler unter 0.1 rad bei moderater Dynamik liefern realistische Benchmarks fuer den eigenen AMR. Die detaillierte Komponentenliste (Pololu VNH5019, NeveRest 40, BNO-055, STL-19 Lidar) ermoeglicht einen praezisen Hardware-Vergleich. Die Erkenntnis, dass ein Random Forest mit ~10 ms Inferenzzeit auf dem RPi 4 echtzeitfaehig ist (~15% CPU), ist methodisch relevant fuer die eigene Ressourcenplanung auf dem RPi 5.
