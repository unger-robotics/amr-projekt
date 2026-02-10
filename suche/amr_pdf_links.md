# PDF-Links und Zugangsstatus – AMR-Bachelorarbeit

Stand: 10. Februar 2026

Die folgende Tabelle listet alle priorisierten Quellen mit direktem PDF-Link, Zugangsstatus und ggf. Alternativweg auf. Die Reihenfolge entspricht dem 4-Wochen-Leseplan.

---

## Legende Zugangsstatus

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Frei zugänglich (Open Access, arXiv, JOSS, MDPI, Tech Report) |
| 🔑 | Über WBH-Hochschulzugang (SpringerLink / IEEE Xplore) erreichbar |
| 🔒 | Paywall — Alternativweg angegeben |
| 📖 | Lehrbuch — Bibliothek / Fernleihe / SpringerLink empfohlen |

---

## Woche 1 — Architektonische Grundlagen

### 1. Macenski et al. (2022) — ROS 2 Architektur ★

- **Venue:** Science Robotics 7(66)
- **Status:** ✅ arXiv-Preprint frei, Verlagsversion über Open-Robotics-Link
- **arXiv PDF:** https://arxiv.org/pdf/2211.07752
- **Verlagsversion (freier Zugang über Open Robotics):** https://www.openrobotics.org/blog/2022/5/12/science-robotics-paper
- **ResearchGate PDF:** https://www.researchgate.net/publication/365414963

---

### 2. Macenski et al. (2023) — Nav2 Survey ★

- **Venue:** Robotics and Autonomous Systems 168, 104493
- **Status:** ✅ arXiv-Preprint frei
- **arXiv PDF:** https://arxiv.org/pdf/2307.15236
- **ResearchGate PDF:** https://www.researchgate.net/publication/372767083
- **Verlagsversion (Paywall):** https://www.sciencedirect.com/science/article/abs/pii/S092188902300132X

---

### 3. Belsare et al. (2023) — micro-ROS Buchkapitel ★

- **Venue:** Springer, Robot Operating System (ROS): The Complete Reference, Bd. 7, S. 3–55
- **Status:** 🔒 Paywall (Springer), kein Hochschulzugang verfügbar
- **Ersatz (✅ frei):** Die micro-ROS-Projektdokumentation auf https://micro.ros.org deckt denselben Inhalt ab: Architektur, XRCE-DDS, rclc API, Executor-Modell, unterstützte Plattformen
- **Ergänzend:** Staschulat et al. (2020) — rclc Executor (Nr. 14 in dieser Liste) liefert die wissenschaftliche Grundlage
- **Hinweis:** Für die Arbeit genügt die Kombination micro.ros.org + Staschulat-Paper als Quellengrundlage

---

### 4. Siegwart, Nourbakhsh, Scaramuzza (2011) — Mobilroboter-Kinematik ★

- **Venue:** MIT Press, 2. Auflage
- **Status:** ✅ 1. Auflage (2004) als PDF frei verfügbar — Kinematik-Kapitel (Kap. 3) ist zwischen den Auflagen weitgehend identisch
- **PDF 1. Auflage (frei):** http://vigir.missouri.edu/~gdesouza/Research/MobileRobotics/Autonomous_Mobile_Robots_Siegwart-Nourbakhsh.pdf
- **ETH-Vorlesungsfolien Kap. 4 (Kinematik):** https://rpg.ifi.uzh.ch/docs/teaching/2024/Ch4_AMRobots.pdf
- **Relevante Kapitel:** Kap. 3 (Kinematik, Diff-Drive-Herleitung) — ca. 40 Seiten
- **Hinweis:** Für die Bachelorarbeit reicht die 1. Auflage aus. Die 2. Auflage ergänzt Kap. zu visueller Odometrie (Scaramuzza), das für das Projekt nicht benötigt wird.

---

## Woche 2 — Kernalgorithmen

### 5. Macenski & Jambrecic (2021) — SLAM Toolbox

- **Venue:** JOSS 6(61), 2783
- **Status:** ✅ Open Access (CC BY 4.0)
- **JOSS PDF:** https://www.theoj.org/joss-papers/joss.02783/10.21105.joss.02783.pdf
- **JOSS Landingpage:** https://joss.theoj.org/papers/10.21105/joss.02783

---

### 6. Hess et al. (2016) — Google Cartographer

- **Venue:** IEEE ICRA 2016, S. 1271–1278
- **Status:** ✅ Google Research stellt PDF frei bereit
- **Google Research PDF:** https://research.google.com/pubs/archive/45466.pdf
- **IEEE Xplore (Paywall/WBH):** https://ieeexplore.ieee.org/document/7487258/

---

### 7. Moore & Stouch (2014) — robot_localization EKF ★

- **Venue:** Springer AISC 302, S. 335–348 (IAS-13)
- **Status:** ✅ Volltext frei auf der ROS-Dokumentationsseite
- **PDF (frei):** https://docs.ros.org/en/lunar/api/robot_localization/html/_downloads/robot_localization_ias13_revised.pdf
- **Ergänzend:** `robot_localization` Wiki auf GitHub: https://github.com/cra-ros-pkg/robot_localization/wiki

---

### 8. Fox, Burgard, Thrun (1997) — DWA

- **Venue:** IEEE Robotics & Automation Magazine 4(1)
- **Status:** 🔒 IEEE Paywall
- **IEEE Xplore:** https://ieeexplore.ieee.org/document/580977
- **Alternativ:** Zahlreiche universitäre Spiegelungen über Google Scholar auffindbar. Macenski et al. (2023) Nr. 2 fasst DWA im Nav2-Kontext zusammen.

---

### 9. Borenstein, Everett, Feng (1996) — „Where Am I?"

- **Venue:** University of Michigan Tech Report, 282 Seiten
- **Status:** ✅ Frei verfügbar (Autoren-Website)
- **Autoren-Website PDF:** http://www-personal.umich.edu/~johannb/Papers/pos96rep.pdf
- **CMU Mirror:** https://www.cs.cmu.edu/~motionplanning/papers/sbp_papers/integrated1/borenstein_robot_positioning.pdf

---

## Woche 3 — Hardware-spezifisch und angewandt

### 10. Abaza (2025) — ESP32 + RPi + ROS 2 + EKF (**exakte Stack-Übereinstimmung**)

- **Venue:** Sensors 25(10), 3026
- **Status:** ✅ MDPI Open Access (CC BY 4.0)
- **MDPI Volltext:** https://www.mdpi.com/1424-8220/25/10/3026
- **PMC Volltext:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12114818/
- **GitHub (Code):** https://github.com/bogdan-abaza/ROS_ESP32_Bridge

---

### 11. Albarran et al. (2023) — ESP32 Diff-Drive mit micro-ROS

- **Venue:** Revista Elektron 7(2), S. 53–60
- **Status:** ✅ Frei zugänglich
- **Dialnet PDF:** https://dialnet.unirioja.es/descarga/articulo/9366528.pdf
- **ResearchGate PDF:** https://www.researchgate.net/publication/376574069

---

### 12. Yordanov et al. (2025) — Dual-Core ESP32 Partitionierung

- **Venue:** arXiv 2509.04061 (RWTH Aachen / ITSC 2025)
- **Status:** ✅ arXiv Open Access
- **arXiv PDF:** https://arxiv.org/pdf/2509.04061
- **arXiv HTML:** https://arxiv.org/html/2509.04061v1

---

### 13. MDPI Electronics (2025) — SLAM Toolbox vs. Cartographer

- **Venue:** Electronics 14(24), 4822
- **Status:** ✅ MDPI Open Access
- **MDPI Volltext:** https://www.mdpi.com/2079-9292/14/24/4822

---

### 14. Staschulat, Lütkebohle, Lange (2020) — rclc Executor

- **Venue:** EMSOFT 2020 (IEEE), S. 18–19
- **Status:** ✅ OFERA-Projektseite stellt PDF frei bereit
- **OFERA PDF:** https://www.ofera.eu/storage/publications/Staschulat_et_al_2020_The_rclc_Executor_Domain-specific_deterministic_scheduling_mechanisms.pdf
- **IEEE Xplore:** https://ieeexplore.ieee.org/document/9244014/

---

## Woche 4 — Spezialisierung

### 15. ArUco-Docking (Sensors 2025)

- **Venue:** Sensors 25(12), 3742
- **Status:** ✅ MDPI Open Access
- **MDPI Volltext:** https://www.mdpi.com/1424-8220/25/12/3742

---

### 16. 2DLIW-SLAM (arXiv 2024)

- **Venue:** arXiv 2404.07644
- **Status:** ✅ arXiv Open Access
- **arXiv PDF:** https://arxiv.org/pdf/2404.07644

---

### 17. Naragani et al. (2024) — Unified Dual-Wheel PID

- **Venue:** IEEE Conference
- **Status:** 🔒 IEEE Paywall, kein Hochschulzugang verfügbar
- **Ersatz:** Das Konzept (synchronisierte PID-Regelung für Diff-Drive) wird in Abaza (2025, Nr. 10) und Albarran (2023, Nr. 11) ebenfalls behandelt — beide frei verfügbar. Für die Arbeit als ergänzende Quelle verzichtbar.

---

### 18. De Giorgi et al. (2024) — Online Odometry Calibration

- **Venue:** Robotics 13(1), 7
- **Status:** ✅ MDPI Open Access
- **MDPI Volltext:** https://www.mdpi.com/2218-6581/13/1/7

---

### 19. Nguyen (2022) — M.Sc.-Thesis micro-ROS

- **Venue:** Mälardalen University
- **Status:** ✅ Schwedisches Hochschularchiv (DiVA Portal), frei zugänglich
- **DiVA PDF:** https://www.diva-portal.org/smash/get/diva2:1670378/FULLTEXT01.pdf

---

## Weitere Pflichtquellen (Lehrbücher und Klassiker)

### Thrun, Burgard, Fox (2005) — Probabilistic Robotics

- **Status:** 📖 Lehrbuch (MIT Press)
- **Zugang:** Fernleihe; Draft-Kapitel teilweise über Google Scholar auffindbar
- **Hinweis:** Kap. 5 (Motion Models) und Kap. 6 (Robot Perception) sind die relevanten Abschnitte. Für die Bachelorarbeit genügt es, die EKF-Grundlagen aus Moore & Stouch (2014, Nr. 7) und Abaza (2025, Nr. 10) zu beziehen.

---

### Siciliano, Sciavicco et al. (2009) — Robotics: Modelling, Planning and Control

- **Status:** 📖 Springer-Lehrbuch
- **Zugang:** Fernleihe; für die Bachelorarbeit nicht zwingend benötigt
- **Hinweis:** Regelungstheorie für PID-Tuning findet sich ausreichend in Albarran (2023) und Abaza (2025)

---

### Corke (2023) — Robotics, Vision and Control, 3. Aufl.

- **Status:** 📖 Springer-Lehrbuch
- **Zugang:** Companion-Website mit Python-Code und Algorithmen-Erklärungen ist frei: https://petercorke.com/rvc/
- **Hinweis:** Für Kinematik und Odometrie reicht Siegwart (Nr. 4). Corke ist hilfreich für Simulationsexperimente, aber nicht zwingend erforderlich.

---

### Borenstein & Feng (1996) — UMBmark

- **Venue:** IEEE Transactions on Robotics and Automation
- **Status:** 🔒 IEEE Paywall
- **Ersatz:** „Where Am I?"-Report (Nr. 9, ✅ frei) enthält die UMBmark-Methode vollständig in Kap. 1

---

### Macenski, Singh et al. (2023) — Regulated Pure Pursuit

- **Venue:** Autonomous Robots (Springer)
- **Status:** 🔒 Springer Paywall
- **Ersatz (✅ frei):** Nav2-Dokumentation erklärt RPP-Controller ausführlich: https://docs.nav2.org/configuration/packages/configuring-regulated-pp.html
- **Ergänzend:** Macenski et al. (2023, Nr. 2) enthält RPP-Vergleichsdaten in der Nav2-Survey

---

### Wang, Liu et al. (2024) — Priority-Driven micro-ROS Scheduling

- **Venue:** Electronics 13(9), 1658
- **Status:** ✅ MDPI Open Access
- **MDPI Volltext:** https://www.mdpi.com/2079-9292/13/9/1658

---

## Offizielle Dokumentation (alle ✅ frei)

| Ressource | URL |
|-----------|-----|
| micro-ROS Projekt | https://micro.ros.org |
| Nav2 Dokumentation | https://docs.nav2.org |
| ROS 2 Humble Dokumentation | https://docs.ros.org/en/humble/ |
| ros2_control (diff_drive_controller) | https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html |
| micro_ros_espidf_component | https://github.com/micro-ROS/micro_ros_espidf_component |
| linorobot2_hardware (Referenz-Firmware) | https://github.com/linorobot/linorobot2_hardware |
| Micro XRCE-DDS (eProsima) | https://github.com/eProsima/Micro-XRCE-DDS |
| DDS-XRCE Spezifikation (OMG) | https://www.omg.org/spec/DDS-XRCE/ |

---

## Zusammenfassung: Was ist frei, was fehlt?

### Sofort verfügbar (✅) — 18 von 19 priorisierten Quellen

Durch die freien Alternativen sind nun fast alle Quellen **ohne Kosten und ohne Hochschulzugang** als PDF verfügbar: arXiv-Preprints, MDPI Open-Access-Journale, JOSS, Google Research, DiVA Portal, ROS-Dokumentation und universitäre Tech Reports decken den gesamten Lesebedarf ab.

### Nicht frei verfügbar (🔒) — 1 Quelle

| Quelle | Status | Empfehlung |
|--------|--------|------------|
| Naragani et al. (2024) — Dual-Wheel PID | IEEE Paywall | Verzichtbar — Abaza (2025) und Albarran (2023) decken das Thema ab |

### Lehrbücher — alle ohne Kauf zugänglich

| Buch | Lösung |
|------|--------|
| Siegwart et al. (2004/2011) | ✅ 1. Auflage als PDF frei + ETH-Vorlesungsfolien |
| Thrun et al. (2005) | Fernleihe oder Draft-Kapitel über Scholar auffindbar |
| Siciliano et al. (2009) | Nicht zwingend benötigt; ggf. Fernleihe |
| Corke (2023) | Companion-Website mit Code frei: https://petercorke.com/rvc/ |

### Gesamtbilanz

**Kein einziger Kauf erforderlich.** Die 18 frei verfügbaren Quellen plus die offizielle Dokumentation (micro.ros.org, Nav2, ROS 2) liefern eine vollständige Literaturbasis für die Bachelorarbeit.
