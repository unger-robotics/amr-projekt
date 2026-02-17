# Abgleich: Lernplan Programmierung — AMR-Codebasis

**Datum:** 2026-02-17
**Methodik:** 4-Agent-Team analysiert alle 4 Programmier-Module (M1-M4) gegen Firmware (`amr/esp32_amr_firmware/`), ROS2 (`my_bot/`), Docker (`amr/docker/`), Validierungsskripte (`amr/scripts/`) und `hardware/config.h`.

---

## Uebersicht

| Modul | Thema | Status | Implementierungsgrad |
|-------|-------|--------|---------------------|
| M1 | Modernes C++ (C++17/20) | ❌ Kaum impl. | ~15-20% |
| M2 | Python fuer Robotik | ✅ Weitgehend | ~70-80% |
| M3 | Algorithmik & Datenstrukturen | ❌ Kaum impl. | ~5-10% |
| M4 | Software-Architektur & Clean Code | ⚠️ Teilweise | ~40-50% |

**Zentrale Abweichung:** Die ESP32-Toolchain (`xtensa-esp32s3-elf-gcc 8.4.0`, espressif32 v6.12.0) kompiliert mit **C++11**. Der Lernplan setzt C++17/20 voraus. Dies betrifft M1 direkt und M3/M4 indirekt.

---

# M1 — Modernes C++ (C++17/20) und Design Patterns

## W1-W2: Move-Semantik und Speicherverwaltung

### Status: Nur theoretisch

### Implementierte Konzepte

**Zero-Heap-Allocation-Design:** Die Firmware nutzt bewusst keine dynamische Speicherallokation zur Laufzeit. Alle Objekte sind globale Stack-Variablen (`main.cpp:19-24`): `RobotHAL hal`, `DiffDriveKinematics kinematics`, `PidController pid_l/pid_r`, `MPU6050 imu`.

**Implizites RAII:** FreeRTOS-Mutex via `xSemaphoreCreateMutex()` (`main.cpp:168`), `portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED` (`robot_hal.hpp:36`). Allerdings kein C++-RAII-Wrapper (kein `std::lock_guard`-Aequivalent).

### Luecken
- Smart Pointer (`unique_ptr`, `shared_ptr`, `weak_ptr`) komplett absent — architektonisch nicht vorgesehen
- Manuelles `xSemaphoreTake`/`xSemaphoreGive` statt Scoped-Lock-Wrapper (`main.cpp:79-83`, `main.cpp:122-129`)
- Move-Semantik irrelevant, da keine Objekte kopiert/verschoben werden
- Rule of Zero/Five nicht anwendbar (triviale Destruktoren)

---

## W3-W4: Templates, constexpr und Compile-Time-Berechnung

### Status: ⚠️ Teilweise implementiert

### Implementierte Konzepte

**`static constexpr` (C++11-kompatibel):** `mpu6050.hpp:11-20` — 9x Compile-Time-Konstanten:
```cpp
static constexpr uint8_t REG_SMPLRT_DIV   = 0x19;
static constexpr float ACCEL_SENSITIVITY = 16384.0f;
static constexpr float GYRO_SENSITIVITY  = 131.0f;
```

**`static_assert`:** `config.h:107-115` — Compile-Time-Validierung von Parametern.

### Luecken
- **Keine Templates** im gesamten Firmware-Code (kein `RingBuffer<T, N>`, kein `Publisher<MsgType>`)
- `constexpr if` (C++17), Structured Bindings (C++17), Variadic Templates nicht verfuegbar
- `config.h:54-101` nutzt `#define`-Makros statt `constexpr` fuer Roboterparameter
- `constexpr`-Funktionen nicht genutzt, nur `static constexpr`-Variablen

---

## W5-W6: Standardbibliothek und funktionale Elemente

### Status: Nur theoretisch

### Implementierte Konzepte

**Minimale STL-Nutzung:** `pid_controller.hpp:2` — `#include <algorithm>` als einziger STL-Include. `std::max`/`std::min` als Ersatz fuer `std::clamp` (C++17):
```cpp
integral = std::max(min_out, std::min(integral, max_out));
```

### Luecken
- Keine STL-Container (`std::array`, `std::vector`, `std::optional`)
- Keine Lambda-Ausdruecke
- Keine STL-Algorithmen (`std::transform`, `std::accumulate`, `std::find_if`)
- `std::variant`/`std::visit` (C++17) nicht verfuegbar
- Zustandsautomat nur Python-seitig (`aruco_docking.py:28-31`), nicht als C++-Implementierung

---

## W7-W8: Design Patterns fuer Embedded und ROS2

### Status: ⚠️ Teilweise (implizit)

### Implementierte Konzepte

**HAL/Facade Pattern:** `robot_hal.hpp:34-101` — Klasse abstrahiert GPIO, PWM, Encoder mit 3 oeffentlichen Methoden (`init()`, `readEncoders()`, `setMotors()`).

**Observer Pattern (implizit):** `main.cpp:199-206` — micro-ROS Subscriber/Publisher-Entkopplung via rclc C-API.

**State Machine (Python):** `aruco_docking.py:28-31` — SEARCHING → APPROACHING → DOCKED / TIMEOUT. String-Vergleich, kein State Pattern.

### Luecken
- Kein Strategy Pattern (PID-Gains hardcoded in `main.cpp:21-22`)
- Kein State Pattern in C++ (nur `if/else`-Ketten in `main.cpp:179-227`)
- Dependency Injection fehlt (alle Abhaengigkeiten sind globale Variablen)
- SOLID nur teilweise: SRP bei Headern gut, aber `main.cpp` hat 6+ Verantwortlichkeiten (341 Zeilen)

---

# M2 — Python fuer Robotik und Datenanalyse

## W1-W2: Python-Grundlagen

### Status: ✅ Voll implementiert

### Implementierte Konzepte

**Datenstrukturen:** `dict`, `list`, `tuple` durchgehend genutzt (`kinematic_test.py:175-185`, `validation_report.py:29-39`).

**List Comprehensions:** `validation_report.py:286-288`.

**Context Manager:** `amr_utils.py:118-119` — `with open(pfad, "w", encoding="utf-8") as f:`.

**Klassen mit Vererbung:** `kinematic_test.py:61-131` — `KinematikTestNode(Node)`.

**Pathlib:** `kinematic_test.py:25,530` — `from pathlib import Path`, `Path(__file__).parent`.

### Luecken
- **Type Hints fehlen weitgehend** (Grep nach `-> `, `List[`, `Dict[`, `Optional[` ergab keine Treffer in `amr/scripts/`)
- Keine Generatoren (`yield`)
- Keine Dunder-Methoden (`__repr__`/`__eq__`) in eigenen Klassen

---

## W3-W4: NumPy, Matplotlib und Datenanalyse

### Status: ✅ Voll implementiert

### Implementierte Konzepte

**NumPy:** `np.mean()`, `np.std(ddof=1)`, `np.where()` — Nutzung in `kinematic_test.py`, `umbmark_analysis.py`, `aruco_docking.py`.

**Matplotlib (objektorientiert):** `umbmark_analysis.py:289-344` — korrekte Figure/Axes-API:
```python
fig, ax = plt.subplots(1, 1, figsize=(8, 8))
ax.scatter(...); ax.set_xlabel(...); ax.legend(...)
fig.savefig(pfad, dpi=150, bbox_inches="tight")
```

**UMBmark-Analyse:** `umbmark_analysis.py:103-200` — Borenstein 1996, numpy-Arrays, Schwerpunktberechnung, Korrekturfaktoren.

**JSON-I/O:** `amr_utils.py:107-135` — `save_json()` mit `numpy_safe_json()` Serialisierer.

### Luecken
- **Pandas nicht verwendet** (kein DataFrame, kein groupby, kein Zeitreihenindex)
- Bag-Datei-Analyse nicht als Skript vorhanden
- Polardiagramm fuer Lidar-Daten fehlt
- Latenzverteilungs-Analyse (Histogramm, Perzentile) nicht implementiert

---

## W5-W6: Python in ROS2 und Automatisierung

### Status: ✅ Voll implementiert

### Implementierte Konzepte

**12 rclpy-Node-Klassen:** `odom_to_tf.py`, `kinematic_test.py`, `rplidar_test.py`, `docking_test.py`, `nav_test.py`, `motor_test.py`, `pid_tuning.py`, `encoder_test.py`, `imu_test.py`, `straight_drive_test.py`, `slam_validation.py`, `rotation_test.py`.

**Publisher/Subscriber/Timer:** `aruco_docking.py:38-40` — `create_publisher(Twist, 'cmd_vel', 10)`, `create_subscription(Image, ...)`, `create_timer(0.1, self.watchdog_callback)`.

**Launch-File:** `full_stack.launch.py:1-227` — 8 `DeclareLaunchArgument`, `IfCondition`, `IncludeLaunchDescription`, `PathJoinSubstitution`.

**Package-Struktur:** `setup.py` — ament_python mit 13 entry_points.

### Luecken
- **pytest komplett absent** (Validierungsskripte sind experimentelle ROS2-Nodes, keine Unit-Tests)
- Keine `launch_testing` Integrationstests
- ROS2 Services nicht implementiert (nur Topics)
- ROS2 Parameter nur via Launch-Arguments, nicht via `declare_parameter()` in Nodes

---

# M3 — Algorithmik und Datenstrukturen

## W1-W2: Komplexitaetsanalyse und grundlegende Datenstrukturen

### Status: ⚠️ Teilweise (implizit)

### Implementierte Konzepte

**EMA-Filter:** `main.cpp:52-53` — Single-Value-Filter statt explizitem Ringpuffer.

**Thread-Safety-Primitiven:** `robot_hal.hpp:36-37` — `portMUX_TYPE mux` fuer ISR-Abschnitte. `main.cpp:33` — FreeRTOS-Mutex fuer `SharedData`.

**Python-dict (O(1)-Lookup):** `validation_report.py:29-39` — `ERGEBNIS_DATEIEN` als Dictionary.

### Luecken
- Kein Ringpuffer-Template (`RingBuffer<T, N>`)
- Keine Hash-Map-Implementierung in C++
- Keine Komplexitaetsanalyse dokumentiert
- Keine verketteten Listen

---

## W3-W4: Sortier- und Suchalgorithmen

### Status: Nur theoretisch

Keine Sortier- oder Suchalgorithmen in Firmware oder Python-Skripten implementiert. Einzige Suche: `aruco_docking.py:98` — `np.where(ids.flatten() == self.target_marker_id)` (lineare Suche, O(n), n < 10).

### Luecken
- Merge Sort, Quick Sort, binaere Suche — alles absent
- Kein Benchmark-Vergleich mit `std::sort`
- Keine optimierte Hindernis-Erkennung auf Lidar-Daten

---

## W5-W8: Baeume, Graphen und Pfadplanung

### Status: Nur theoretisch (via Nav2-Blackbox)

**Nav2 nutzt intern A* und Dijkstra** (`nav2_params.yaml` konfiguriert NavFn-Planer) und SLAM Toolbox nutzt Ceres-Solver fuer Graphoptimierung. Beides ist Drittanbieter-Code, keine eigene Implementierung.

### Luecken
- BST, BFS, DFS, Graph-Traversierung — nicht eigens implementiert
- Occupancy-Grid-als-Graph-Modellierung fehlt
- Priority Queue / Heap nicht implementiert
- Kein Benchmark (Knotenzahl-Vergleich Dijkstra vs. A*)

---

# M4 — Software-Architektur und Clean Code

## W1-W2: Clean-Code-Prinzipien

### Status: ⚠️ Teilweise

### Implementierte Konzepte

**Beschreibende Namen:** `config.h:54` — `WHEEL_DIAMETER`, `WHEEL_BASE`, `FAILSAFE_TIMEOUT_MS`.

**Funktionen/Eine Aufgabe:** `robot_hal.hpp:38-61` — `driveMotor()`, `readEncoders()` — klar abgegrenzt.

**Erklaerende Kommentare (Warum):** `main.cpp:74` — `// EMA-Filter: Glaettet Quantisierungsrauschen fuer PID`. `config.h:54` — `// [m] Raddurchmesser (kalibriert: 2x 1m-Bodentest, Faktor 98.5/97.55)`.

**DRY:** `amr_utils.py:14-48` — Zentrale Konstanten als Single Source of Truth (Spiegel von `config.h`). Alle Validierungsskripte importieren von dort.

### Luecken
- `main.cpp` hat 6+ Verantwortlichkeiten in 341 Zeilen (monolithisch)
- `SharedData` struct mit 14 Einbuchstaben-Feldern (`tv, tw, ox, oy, oth, ...`) — nicht selbsterklaerend
- Kein Coding-Standard-Dokument
- Kein Doxygen-Format in der Firmware

---

## W3-W4: Architektur-Prinzipien und Modularisierung

### Status: ⚠️ Teilweise

### Implementierte Konzepte

**Schichtenarchitektur (4 Module):** HAL → Kinematik → PID → main/ROS. Keine zyklischen Abhaengigkeiten.

**Single Responsibility (bei Headern):** `robot_hal.hpp` (Hardware), `pid_controller.hpp` (PID), `diff_drive_kinematics.hpp` (Kinematik), `mpu6050.hpp` (IMU) — jeder Header genau eine Aufgabe.

**Interface Segregation:** `robot_hal.hpp` — schlanke Schnittstelle mit 3 oeffentlichen Methoden.

**V-Modell (VDI 2206):** Bachelorarbeit folgt V-Modell, Validierungsskripte bilden rechte V-Seite ab.

### Luecken
- Keine abstrakten Interfaces (`ISensorHAL`, `IMotorHAL`)
- Open/Closed verletzt (neuer Sensor erfordert `main.cpp`-Modifikation)
- Dependency Inversion fehlt (direkte Abhaengigkeit von konkreten Klassen)
- Kein Komponentendiagramm, kein Architecture Decision Record (ADR)

---

## W5-W6: Testen, Fehlerbehandlung und technische Schuld

### Status: ⚠️ Teilweise

### Implementierte Konzepte

**12 experimentelle Validierungsskripte:** Mit Akzeptanzkriterien (z.B. `kinematic_test.py:50-52` — `AKZEPTANZ_STRECKE_PCT = 5.0`, `AKZEPTANZ_DRIFT_M = 0.05`).

**Fehlerbehandlung (Firmware):** Return-Code-Pattern (`rcl_ret_t rc`, `main.cpp:187-211`). LED-Signale fuer verschiedene Fehler.

**Fehlerbehandlung (Python):** `try/except` fuer ImportError (`kinematic_test.py:29-37`), CvBridge-Fehler (`aruco_docking.py:81-84`), JSON-Parsing (`validation_report.py:336-341`).

**Failsafe:** `main.cpp:86-89` — Motoren stoppen nach 500 ms ohne cmd_vel. `main.cpp:236-246` — Inter-Core-Watchdog.

### Luecken
- **Keine automatisierten Unit-Tests** (kein gtest, kein pytest)
- Keine CI-Pipeline (GitHub Actions)
- Keine Code-Abdeckungsmetriken
- Kein `enum class ErrorCode` (Firmware nutzt `rcl_ret_t`)
- Keine technische-Schulden-Liste dokumentiert
- Keine Reconnection-Logik in der Firmware

---

# Kernabweichungen (Top 5)

| # | Bereich | Lernplan | Code | Begruendung |
|---|---------|----------|------|-------------|
| 1 | C++-Standard | C++17/20 | C++11 | ESP32-Toolchain-Limit (xtensa-gcc 8.4.0) |
| 2 | Unit-Tests | gtest + pytest + 80% Coverage | 12 experimentelle Validierungsskripte | V-Modell-Ansatz: Systemtest statt Unit-Test |
| 3 | Algorithmen | Eigene A*/Dijkstra/BST | Nav2/SLAM Toolbox als Blackbox | Fokus auf Integration statt Reimplementation |
| 4 | Type Hints | Durchgehend (PEP 484) | Komplett absent | Prototyping-Tempo priorisiert |
| 5 | Pandas | DataFrame, groupby, Zeitreihen | Listen/Dicts + NumPy | Ausreichend fuer 12 Validierungsskripte |

---

# Bewertung nach Modul

**M1 (C++17/20): ~15-20% implementiert.** Die C++11-Einschraenkung der ESP32-Toolchain macht ueber 50% des Lernplans nicht direkt anwendbar. Vorhandene C++11-Features (`static constexpr`, `static_assert`, Header-only-Module) werden korrekt genutzt.

**M2 (Python): ~70-80% implementiert.** Starke rclpy-Nutzung mit 12 Node-Klassen, vollstaendiges Launch-System, NumPy/Matplotlib fuer Datenanalyse. Fehlende Type Hints und pytest sind die Hauptluecken.

**M3 (Algorithmik): ~5-10% implementiert.** Algorithmen werden ausschliesslich ueber Drittanbieter-Frameworks (Nav2, SLAM Toolbox) genutzt, nicht eigens implementiert. FreeRTOS-Synchronisationsprimitive sind die einzigen direkt relevanten Datenstrukturen.

**M4 (Architektur): ~40-50% implementiert.** Grundstruktur gut (4-Modul-Schichtenarchitektur, HAL-Abstraktion, V-Modell, DRY via amr_utils.py). Hauptluecken: fehlende automatisierte Tests, keine abstrakten Interfaces, monolithische `main.cpp`.

---

*Erstellt: 2026-02-17 | 4-Agent-Team (mathe-nawi, info-technik, programmierung, hardware-params) | Codebasis: AMR v3.0.0*
