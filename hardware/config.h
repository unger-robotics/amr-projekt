/**
 * @file config.h
 * @brief Zentrale Konfiguration fuer AMR Slave-Node (ESP32-S3)
 * @version 2.3.2
 * @date 2026-02-27
 *
 * @standard REP-103 (SI-Einheiten), REP-105 (Frames), Safety-First
 * @hardware Seeed Studio XIAO ESP32-S3, Cytron MDD3A, JGA25-370 (1:34),
 *           INA260, PCA9685, MPU6050 (GY-521), 2x MG996R,
 *           Pololu D36V50F6 (6 V Buck), LED-Streifen SMD 5050
 * @battery  Samsung INR18650-35E 3S1P (NCA, 10,80 V / 3.350 mAh)
 *
 * I2C-Bus: 400 kHz Fast-mode
 *   0x40 – INA260  (Leistungsmonitor, Default-Adresse)
 *   0x41 – PCA9685 (Servo-PWM, Loetbruecke A0 geschlossen)
 *   0x68 – MPU6050 (IMU, AD0 = GND)
 *
 * Spannungsversorgung:
 *   3S-Pack (9,0…12,6 V) ---> INA260 (High-Side) --+-- Pololu D36V50F6 --> 6 V (Servos)
 *                                                  +-- Buck --> 5 V (Pi 5)
 *                                                  +-- Buck --> 3,3 V (ESP32-S3)
 *
 * Aenderungen gegenueber v2.3.1:
 *   [ENT] amr::adc Namespace entfernt (kein GPIO verfuegbar, kein Pin zugewiesen)
 *   [FIX] pack_impedance_mohm: 105 -> 183 mOhm (DC-Puls-Messung B6AC V2)
 *   [DOK] cell_impedance_ac_mohm als Datenblatt-Referenz beibehalten
 *
 * Aenderungen gegenueber v2.3.0:
 *   [FIX] JGA25-370 Getriebeuebersetzung: 1:100 -> 1:34 (4 Stellen)
 *   [FIX] Theoretische Encoder-Ticks: 4400 -> 1496 (4x-Quadratur)
 *   [DOK] Kalibrierte Werte (748,6 / 747,2) waren bereits korrekt
 *
 * Aenderungen gegenueber v2.2.0:
 *   [NEU] amr::servo Namespace (PCA9685 + MG996R Pulsparameter, Rampe)
 *   [NEU] amr::regulator Namespace (D36V50F6 PG-Pin, Spannungsdaten)
 *   [DOK] PCA9685 OE-Pin fest auf GND (Hardware-Bruecke, immer aktiv)
 *   [DOK] Servo-Stall-Timeout in amr::safety ergaenzt
 *
 * Quellen:
 *   - Samsung SDI Spec. INR18650-35E, Version 1.1
 *   - TI INA260 Datenblatt SBOS656C, Rev. C
 *   - Adafruit INA260 Breakout, Art.-Nr. 4226
 *   - InvenSense MPU-6050 Product Specification Rev 3.4
 *   - Cytron MDD3A Datasheet Rev 1.0
 *   - JGA25-370 Encoder-Spezifikation (11 CPR, Quadratur)
 *   - NXP PCA9685 Datenblatt Rev. 4
 *   - TowerPro MG996R Spezifikation
 *   - Pololu D36V50F6 Produktseite (#4092)
 *   - LongLife LED Art.-Nr. 1845 (SMD 5050, 12 V)
 */

#pragma once

#include <cstdint>

// ==========================================================================
// 1. HARDWARE ABSTRACTION LAYER (HAL)
// ==========================================================================

// --- Antriebsstrang (Cytron MDD3A - DUAL PWM MODE) ---
//
// Physische Verkabelung:
//   MDD3A M1A -> D0 (GPIO1)   Vorwaerts-PWM links
//   MDD3A M1B -> D1 (GPIO2)   Rueckwaerts-PWM links
//   MDD3A M2A -> D2 (GPIO3)   Vorwaerts-PWM rechts
//   MDD3A M2B -> D3 (GPIO4)   Rueckwaerts-PWM rechts
//
// HINWEIS: D3 (GPIO4) ist belegt. Die MPU6050-Doku schlaegt D3 fuer
// den optionalen INT-Pin vor – dieser Konflikt ist bekannt. Die IMU
// wird im Polling-Modus betrieben (kein Data-Ready-Interrupt).

#define PIN_MOTOR_LEFT_A D0  // GPIO1
#define PIN_MOTOR_LEFT_B D1  // GPIO2
#define PIN_MOTOR_RIGHT_A D2 // GPIO3
#define PIN_MOTOR_RIGHT_B D3 // GPIO4

// PWM-Kanaele (ESP32 LEDC)
// Kanaele in logischer Reihenfolge (A=Vorwaerts, B=Rueckwaerts).
// Richtungskorrektur ueber MOTOR_DIRECTION_*, nicht ueber Kanaltausch.
#define PWM_CH_LEFT_A 0
#define PWM_CH_LEFT_B 1
#define PWM_CH_RIGHT_A 2
#define PWM_CH_RIGHT_B 3

// --- Richtungsfaktoren ---
// +1 = Standardrichtung, -1 = invertiert.
// Ursache Invertierung links: Motor physisch gedreht montiert.
constexpr int8_t MOTOR_DIRECTION_LEFT = -1;
constexpr int8_t MOTOR_DIRECTION_RIGHT = +1;

// --- Encoder Phase A (Hall-Encoder JGA25-370, 11 CPR) ---
#define PIN_ENC_LEFT_A D6  // GPIO7  – Phase A (Interrupt-faehig)
#define PIN_ENC_RIGHT_A D7 // GPIO8  – Phase A (Interrupt-faehig)

// --- Encoder Phase B (Quadratur-Richtungserkennung) ---
#define PIN_ENC_LEFT_B D8  // GPIO9  – Phase B
#define PIN_ENC_RIGHT_B D9 // GPIO10 – Phase B

// --- Peripherie & Status ---
#define PIN_LED_MOSFET D10 // GPIO21 – IRLZ24N Low-Side Switch (LED-Streifen)

// --- I2C Bus (Sensoren & Aktoren) ---
#define PIN_I2C_SDA D4 // GPIO5
#define PIN_I2C_SCL D5 // GPIO6

// ==========================================================================
// 1.1 I2C-KONFIGURATION
// ==========================================================================
//
// Bus-Topologie:
//   ESP32-S3 (Master) -- SDA/SCL 400 kHz --+-- INA260  (0x40)
//                                           +-- PCA9685 (0x41)
//                                           +-- MPU6050 (0x68)
//
// Pull-Up-Widerstaende (parallel):
//   INA260 Breakout:  10 kOhm
//   PCA9685 Breakout: 10 kOhm
//   MPU6050 GY-521:   4,7 kOhm
//   Resultierend:     ca. 2,42 kOhm -> ESP32-interne Pullups deaktivieren

namespace amr::i2c {

constexpr uint8_t addr_ina260 = 0x40;  // Leistungsmonitor (A0=GND, A1=GND)
constexpr uint8_t addr_pca9685 = 0x41; // Servo-PWM (Loetbruecke A0 geschlossen!)
constexpr uint8_t addr_mpu6050 = 0x68; // IMU (AD0=GND)

constexpr uint32_t master_freq_hz = 400000; // Fast-mode 400 kHz

constexpr bool internal_pullup_enabled = false;

} // namespace amr::i2c

// ==========================================================================
// 2. KINEMATISCHE PARAMETER (SI-Einheiten / REP-103)
// ==========================================================================

namespace amr::kinematics {

constexpr float wheel_diameter = 0.06567f; // [m] kalibriert: 2x 1m-Bodentest
constexpr float wheel_radius = wheel_diameter / 2.0f;
constexpr float wheel_base = 0.178f; // [m] Spurbreite Mitte-Mitte
constexpr float wheel_circumference = wheel_diameter * 3.14159265359f;

// ------------------------------------------------------------------
// ENCODER-KALIBRIERUNG (2025-12-12)
// ------------------------------------------------------------------
// Motor: JGA25-370, 1:34 Getriebe, 11 CPR Hall-Encoder
// Theoretisch: 11 CPR * 4 (Quadratur) * 34 (Getriebe) = 1496 Ticks
// Kalibriert: 10-Umdrehungen-Test, 2x-Quadratur-Zaehlung (nicht 4x)
// Rekalibrierung empfohlen bei: Riemenwechsel, Getriebetausch,
// oder wenn Odometrie-Drift in Phase 3 (SLAM) > 5 % ueber 1 m.

constexpr float ticks_per_rev_left = 748.6f;
constexpr float ticks_per_rev_right = 747.2f;

constexpr float ticks_per_rev_avg = (ticks_per_rev_left + ticks_per_rev_right) / 2.0f;

constexpr float meters_per_tick_left = wheel_circumference / ticks_per_rev_left;
constexpr float meters_per_tick_right = wheel_circumference / ticks_per_rev_right;

} // namespace amr::kinematics

// ==========================================================================
// 3. REGELUNGSTECHNIK
// ==========================================================================

// --- PWM Konfiguration (Motoren) ---
namespace amr::pwm {

constexpr uint32_t motor_freq_hz = 20000;              // 20 kHz (unhoerbar, MDD3A-Limit)
constexpr uint8_t motor_bits = 8;                      // 8-bit Aufloesung
constexpr uint32_t motor_max = (1u << motor_bits) - 1; // 255

// Deadzone: minimaler PWM-Wert, ab dem der Motor anlaeuft.
// Kalibriert bei 10,8 V (3S-Pack Nennspannung).
//   12,6 V (voll):  Motor laeuft bei ~30 an
//   9,5 V (leer):   Motor braucht ~45
constexpr uint32_t deadzone = 35;

// --- LED-Streifen PWM ---
// 10-bit (0…1023) fuer glattes Gamma-Dimmen.
constexpr uint32_t led_freq_hz = 5000;             // 5 kHz
constexpr uint8_t led_bits = 10;                   // 10-bit
constexpr uint32_t led_max = (1u << led_bits) - 1; // 1023
constexpr uint8_t led_channel = 4;                 // LEDC-Kanal
constexpr float led_gamma = 2.2f;                  // Gamma-Korrektur

} // namespace amr::pwm

// --- PID-Defaultwerte ---
// Tuning-Empfehlung (JGA25-370 @ 12 V, 1:34):
//   Kp 1,5…3,0 | Ki 3,0…8,0 | Kd 0,05…0,2
namespace amr::pid {

constexpr float kp = 0.4f;  // Getuned (Sprungantwort-Analyse)
constexpr float ki = 0.1f;  // Getuned
constexpr float kd = 0.0f;  // Getuned (kein D-Anteil noetig)

constexpr float i_min = -1.0f; // Anti-Windup untere Grenze
constexpr float i_max = 1.0f;  // Anti-Windup obere Grenze

constexpr float output_min = -1.0f; // Normierte Stellgroesse
constexpr float output_max = 1.0f;

constexpr float d_filter_tau = 0.02f; // [s] D-Term-Tiefpass

// --- Encoder-Filter & Rampe ---
constexpr float ema_alpha = 0.3f;           // EMA-Glaettungsfaktor fuer Encoder-Geschwindigkeit
constexpr float max_accel_rad_s2 = 5.0f;    // [rad/s^2] Beschleunigungsrampe
constexpr float deadband_threshold = 0.08f; // Normierte Motor-Totband-Schwelle
constexpr float hard_stop_threshold = 0.001f; // Stopp-Bypass-Schwelle (v/w)
constexpr float stillstand_threshold = 0.01f; // PID-Reset-Schwelle (rad/s)

} // namespace amr::pid

// ==========================================================================
// 3.1 SERVO-KONFIGURATION (PCA9685 + 2x MG996R)
// ==========================================================================
//
// Quellen:
//   - NXP PCA9685 Datenblatt Rev. 4 (PRE_SCALE, Oszillator 25 MHz)
//   - TowerPro MG996R Spezifikation (Pulsbreite, Stall-Strom)
//   - Pololu D36V50F6 liefert 6 V Servo-Versorgung
//
// Topologie:
//   3S-Pack -> INA260 -> D36V50F6 (6 V) -> PCA9685 V+ Schraubklemme
//   ESP32-S3 3,3 V -> PCA9685 VCC (Logik)
//   PCA9685 CH0 -> MG996R Pan | CH1 -> MG996R Tilt
//
// OE-Pin: Fest auf GND geloetet (Hardware-Bruecke).
//   Konsequenz: Alle 16 PWM-Ausgaenge sind permanent aktiv.
//   Software-Abschaltung: pca9685_all_off() setzt Full-OFF-Bit
//   (ALL_LED_OFF_H Register 0xFD, Bit 4 = 1).

namespace amr::servo {

// --- PCA9685 Registerparameter ---
//
// PRE_SCALE = round(25.000.000 / (4096 * 50)) - 1 = 121
// Tatsaechliche Frequenz: 50,08 Hz (Periodendauer 19,97 ms)
// Zeitaufloesung: 19,97 ms / 4096 = 4,88 µs pro Tick
constexpr uint8_t pca_prescale = 121;      // 50 Hz Servo-PWM
constexpr uint16_t pca_ticks_total = 4096; // 12-bit Aufloesung
constexpr float pca_tick_us = 4.88f;       // [µs] pro Tick

// Oszillator-Korrektur (optional):
// Falls gemessene Frequenz != 50 Hz, hier anpassen:
//   f_osc_real = 25.000.000 * (f_gemessen / 50)
// Default: Nominalwert 25 MHz
constexpr uint32_t pca_osc_hz = 25000000;

// --- Servo-Kanalnummern ---
constexpr uint8_t ch_pan = 0;
constexpr uint8_t ch_tilt = 1;

// --- MG996R Pulsbreiten ---
//
// Theoretischer Bereich: 500 … 2500 µs (±90°, 180° gesamt)
// Sicherer Bereich:      600 … 2400 µs (Endanschlag-Brummen vermeiden)
//
// Kalibrierung: Empirisch pro Exemplar bestimmen. Die Default-Werte
// lassen 100 µs Sicherheitsmarge zu den mechanischen Endanschlaegen.
constexpr uint16_t pulse_min_us = 600;     // [µs] Sicheres Minimum
constexpr uint16_t pulse_center_us = 1500; // [µs] Mittelstellung (0°)
constexpr uint16_t pulse_max_us = 2400;    // [µs] Sicheres Maximum

// Tick-Werte (vorberechnet, bei ON=0):
//   ticks = pulse_us * 4096 / 20000
constexpr uint16_t ticks_min = 123;    // 600 µs
constexpr uint16_t ticks_center = 307; // 1500 µs
constexpr uint16_t ticks_max = 491;    // 2400 µs

// --- MG996R Stellbereich ---
constexpr float angle_range_deg = 180.0f; // Gesamtstellbereich
constexpr float angle_min_deg = 0.0f;     // Entspricht pulse_min_us
constexpr float angle_max_deg = 180.0f;   // Entspricht pulse_max_us

// --- Bewegungsprofil (Rampe) ---
//
// Sanftes Anfahren/Bremsen reduziert Stromspitzen und mechanische
// Belastung. PCA9685-Doku Abschnitt 12.3: 1°/20 ms empfohlen.
constexpr float ramp_deg_per_step = 1.0f; // [°] pro PWM-Zyklus
constexpr uint32_t ramp_step_ms = 20;     // [ms] = ein PWM-Zyklus (50 Hz)
// Resultierende Maximalgeschwindigkeit: 50°/s (1°/20ms)
// Volle Traverse (180°): 3,6 s

// --- MG996R Strombedarf (bei 6 V Versorgung) ---
constexpr float idle_current_ma = 10.0f;  // [mA] pro Servo, Haltestrom
constexpr float move_current_ma = 900.0f; // [mA] pro Servo, unter Last
constexpr float stall_current_a = 2.5f;   // [A] pro Servo, Blockierung

} // namespace amr::servo

// ==========================================================================
// 3.2 SPANNUNGSREGLER (Pololu D36V50F6, 6 V)
// ==========================================================================
//
// Quelle: Pololu Produktseite #4092
// Topologie: Synchroner Buck-Konverter, 6 V fest, max. 5,5 A @ 36 V
// Eingang: 3S-Pack ueber INA260 (9,0 … 12,6 V)
// Ausgang: PCA9685 V+ Schraubklemme -> 2x MG996R Servos
//
// Dropout bei 5 A: ca. 0,8 V -> min. 6,8 V Eingang
// Pack-Minimum 9,0 V >> 6,8 V -> komfortabel erfuellt
//
// Max. Dauerstrom bei 12 V Eingang: ca. 7 A
// 2x MG996R Stall: 5 A -> unterhalb des Limits
//
// EN-Pin: Interner 100 kOhm Pull-up nach VIN (Default: aktiv).
//   Fuer Hardware-Unterspannungsabschaltung kann ein Spannungsteiler
//   am EN-Pin die Servos bei Pack < 9,5 V abschalten – alternativ
//   zur Software-Stufe-2-Abschaltung in amr::battery.

namespace amr::regulator {

constexpr float vout_nominal_v = 6.0f;  // [V] Feste Ausgangsspannung
constexpr float vout_tolerance = 0.04f; // ±4 %
constexpr float vin_min_v = 6.5f;       // [V] Minimum (Datenblatt)
constexpr float vin_max_v = 50.0f;      // [V] Maximum
constexpr float iout_max_a = 5.5f;      // [A] @ 36 V, Raumtemperatur
constexpr float efficiency_typ = 0.92f; // 92 % bei 12 V / 3 A

// Power-Good-Ausgang (PG)
//   Open-Drain, Low bei: V_OUT < 90 % (5,4 V) oder V_OUT > 120 % (7,2 V)
//   Externer Pull-up: 10 kOhm nach 3,3 V (oder ESP32 interner Pullup)
//
// HINWEIS: PG-Pin ist optional. Falls kein GPIO verfuegbar,
//          reicht die INA260-Spannungsueberwachung als Redundanz.
//          Aktuell: nicht verdrahtet (kein freier GPIO zugewiesen).
//          Bei Bedarf hier GPIO definieren und in amr::safety einbinden.
// #define PIN_PG_D36V50F6  DX   // GPIO – falls verdrahtet

// Verlustleistungsabschaetzung fuer Energiebilanz:
//   P_verlust = P_out * (1/eta - 1)
//   Bei 6 V, 3 A, eta=92 %: P_verlust = 18 * 0.087 = 1,57 W
//   Bei 6 V, 5 A, eta=90 %: P_verlust = 30 * 0.111 = 3,33 W

} // namespace amr::regulator

// ==========================================================================
// 4. SAFETY & TIMING
// ==========================================================================

namespace amr::timing {

// --- Regelschleife ---
constexpr uint32_t control_loop_hz = 50;
constexpr uint32_t control_loop_period_ms = 1000 / control_loop_hz; // 20 ms

// --- Publikationsraten ---
constexpr uint32_t odom_publish_hz = 20;
constexpr uint32_t odom_publish_period_ms = 1000 / odom_publish_hz; // 50 ms

// IMU: 50 Hz (konsistent mit MPU6050 SMPLRT_DIV=19, DLPF_CFG=3)
constexpr uint32_t imu_publish_hz = 50;
constexpr uint32_t imu_publish_period_ms = 1000 / imu_publish_hz; // 20 ms

// Batterie-Monitoring: INA260
constexpr uint32_t battery_publish_hz = 2;
constexpr uint32_t battery_publish_period_ms = 1000 / battery_publish_hz; // 500 ms

// --- Failsafe ---
constexpr uint32_t failsafe_timeout_ms = 500;

// --- Watchdog ---
constexpr uint32_t watchdog_miss_limit = 50; // Core1-Heartbeat Fehltakte bis Notfall-Stopp

} // namespace amr::timing

// ==========================================================================
// 4.1 IMU-KONFIGURATION (MPU6050 / GY-521)
// ==========================================================================

namespace amr::imu {

constexpr uint32_t calibration_samples = 500;

// Komplementaerfilter:
//   theta[k] = alpha * (theta[k-1] + omega_gyro * dt)
//            + (1 - alpha) * theta_accel
// alpha = 0.98 -> 98 % Gyro, 2 % Beschleunigungsmesser
constexpr float complementary_alpha = 0.98f;

constexpr float gyro_sensitivity = 131.0f;    // [LSB/(°/s)] FS_SEL=0 (±250 °/s)
constexpr float accel_sensitivity = 16384.0f; // [LSB/g] AFS_SEL=0 (±2 g)

} // namespace amr::imu

// ==========================================================================
// 4.2 STALL-ERKENNUNG UND MOTORSCHUTZ
// ==========================================================================
//
// DC-Motoren: Cytron MDD3A max. 3 A Dauer, JGA25-370 Stall 2,5…3,0 A
// Servos:     MG996R Stall 2,5 A @ 6 V, kein eingebauter Schutz

namespace amr::safety {

// --- DC-Motor Stall-Schutz ---
constexpr uint32_t motor_stall_timeout_ms = 2000;     // [ms]
constexpr float motor_stall_velocity = 0.01f;         // [m/s]
constexpr float motor_stall_current_a = 2.5f;         // [A] INA260
constexpr float motor_overcurrent_immediate_a = 5.0f; // [A] Sofort-Aus

// --- Servo Stall-Schutz ---
// PCA9685-Doku Abschnitt 12.3: Falls Servo Zielposition nach
// 2 s nicht erreicht, PWM abschalten (pca9685_all_off).
// Erkennung: Winkel-Soll vs. Winkel-Ist (falls Feedback vorhanden)
// oder zeitbasiert (Bewegung gestartet, kein Erreichen der Position).
constexpr uint32_t servo_stall_timeout_ms = 2000; // [ms]

// Software-Not-Aus fuer Servos:
//   pca9685_all_off() setzt ALL_LED_OFF_H (0xFD) Bit 4 = 1
//   OE-Pin liegt auf GND (Hardware), daher kein GPIO-Not-Aus.
//   Fuer Hardware-Not-Aus muesste OE auf einen GPIO umverdrahtet
//   werden – aktuell nicht vorgesehen.

} // namespace amr::safety

// ==========================================================================
// 5. BATTERIE-KONFIGURATION (Samsung INR18650-35E, 3S1P)
// ==========================================================================
//
// Max. Dauerstrom: 8 A (13 A = nur Impulsstrom)
// Minimalkapazitaet: 3.350 mAh (3.500 mAh = typisch)

namespace amr::battery {

// --- Zellparameter ---
constexpr uint8_t cell_count = 3;
constexpr float cell_nominal_v = 3.60f;
constexpr float cell_charge_max_v = 4.20f;
constexpr float cell_cutoff_v = 2.65f;
constexpr float cell_bms_uvp_v = 2.50f;

// --- Kapazitaet ---
constexpr float capacity_min_mah = 3350.0f;
constexpr float capacity_typ_mah = 3500.0f;
constexpr float capacity_design_ah = capacity_min_mah / 1000.0f;

// --- Stromlimits ---
constexpr float max_continuous_a = 8.0f;
constexpr float max_pulse_a = 13.0f;
constexpr float charge_standard_a = 1.7f;
constexpr float charge_max_a = 2.0f;

// --- Innenwiderstand ---
// Datenblatt (AC, 1 kHz): 35 mOhm/Zelle
// Gemessen (DC-Puls, IMAX B6AC V2, 2026-02-27): 58 / 61 / 64 mOhm
// DC-Werte enthalten Uebergangs- und Kabelwiderstaende und sind fuer
// Spannungseinbruch-Abschaetzung unter Last realistischer.
constexpr float cell_impedance_ac_mohm = 35.0f;   // [mOhm] Datenblatt (AC 1 kHz)
constexpr float pack_impedance_mohm = 183.0f;     // [mOhm] gemessen DC-Puls (58+61+64)

// --- 3S-Pack ---
constexpr float pack_nominal_v = cell_nominal_v * cell_count;       // 10,80 V
constexpr float pack_charge_max_v = cell_charge_max_v * cell_count; // 12,60 V
constexpr float pack_cutoff_v = cell_cutoff_v * cell_count;         //  7,95 V

constexpr float cell_charge_eco_v = 4.10f;
constexpr float pack_charge_eco_v = cell_charge_eco_v * cell_count; // 12,30 V

// --- Energie ---
constexpr float energy_nominal_wh = pack_nominal_v * capacity_design_ah; // 36,18 Wh
constexpr float soc_usable_fraction = 0.80f;
constexpr float energy_usable_wh = energy_nominal_wh * soc_usable_fraction; // 28,94 Wh

// --- Schutzkonzept (Packspannung) ---
constexpr float threshold_warning_v = 10.0f;
constexpr float threshold_motor_shutdown_v = 9.5f;
constexpr float threshold_system_shutdown_v = 9.0f;
constexpr float threshold_critical_v = 7.5f;
constexpr float threshold_hysteresis_v = 0.3f;

// --- Temperaturlimits ---
constexpr float temp_charge_min_c = 0.0f;
constexpr float temp_charge_max_c = 45.0f;
constexpr float temp_discharge_min_c = -10.0f;
constexpr float temp_discharge_max_c = 60.0f;

} // namespace amr::battery

// ==========================================================================
// 5.1 INA260-KONFIGURATION (Leistungsmonitor)
// ==========================================================================

namespace amr::ina260 {

constexpr float current_lsb_ma = 1.25f;
constexpr float voltage_lsb_mv = 1.25f;
constexpr float power_lsb_mw = 10.0f;

// Konfigurationsregister (0x00): 0x6927
//   CT = 1,1 ms (beide), AVG = 4, MODE = continuous
//   t_update = 8,8 ms -> ca. 114 Messungen/s
constexpr uint16_t config_register = 0x6927;

constexpr float current_offset_max_ma = 5.0f;

// Alert bei Unterspannung: 10,0 V / 1,25 mV = 8000 = 0x1F40
constexpr uint16_t alert_voltage_limit = 0x1F40;

constexpr float coulomb_capacity_mah = amr::battery::capacity_min_mah;

} // namespace amr::ina260

// ==========================================================================
// 7. COMPILE-TIME VALIDIERUNG
// ==========================================================================

// --- Kinematik ---
static_assert(amr::kinematics::wheel_radius > 0, "wheel_radius muss positiv sein");
static_assert(amr::kinematics::wheel_base > 0, "wheel_base muss positiv sein");
static_assert(amr::kinematics::ticks_per_rev_left > 0, "ticks_per_rev_left muss positiv sein");
static_assert(amr::kinematics::ticks_per_rev_right > 0, "ticks_per_rev_right muss positiv sein");

// --- PWM ---
static_assert(amr::pwm::deadzone < amr::pwm::motor_max, "deadzone < motor_max");
static_assert(amr::pwm::motor_freq_hz > 0 && amr::pwm::motor_freq_hz <= 20000,
              "MDD3A: PWM 0 < f <= 20 kHz");

// --- Encoder-Pin-Kollision ---
static_assert(PIN_ENC_LEFT_B != PIN_ENC_LEFT_A, "Encoder L: Phase A != Phase B");
static_assert(PIN_ENC_RIGHT_B != PIN_ENC_RIGHT_A, "Encoder R: Phase A != Phase B");

// --- I2C-Adress-Kollision ---
static_assert(amr::i2c::addr_ina260 != amr::i2c::addr_pca9685, "Adresskollision: INA260 / PCA9685");
static_assert(amr::i2c::addr_ina260 != amr::i2c::addr_mpu6050, "Adresskollision: INA260 / MPU6050");
static_assert(amr::i2c::addr_pca9685 != amr::i2c::addr_mpu6050,
              "Adresskollision: PCA9685 / MPU6050");

// --- PID ---
static_assert(amr::pid::i_min < amr::pid::i_max, "PID: i_min < i_max");
static_assert(amr::pid::output_min < amr::pid::output_max, "PID: output_min < output_max");
static_assert(amr::pid::ema_alpha > 0.0f && amr::pid::ema_alpha <= 1.0f,
              "PID: ema_alpha in (0, 1]");
static_assert(amr::pid::max_accel_rad_s2 > 0.0f, "PID: max_accel > 0");
static_assert(amr::pid::deadband_threshold > 0.0f && amr::pid::deadband_threshold < 1.0f,
              "PID: deadband_threshold in (0, 1)");

// --- Timing ---
static_assert(amr::timing::control_loop_hz > 0, "control_loop_hz > 0");
static_assert(amr::timing::failsafe_timeout_ms > amr::timing::control_loop_period_ms,
              "failsafe_timeout > Regelzyklus");
static_assert(amr::timing::imu_publish_hz <= amr::timing::control_loop_hz,
              "IMU-Rate <= Regelfrequenz");

// --- IMU ---
static_assert(amr::imu::complementary_alpha > 0.5f && amr::imu::complementary_alpha < 1.0f,
              "alpha in (0.5, 1.0) – Gyro muss dominieren");

// --- Servo: Pulsbreiten ---
static_assert(amr::servo::pulse_min_us < amr::servo::pulse_center_us,
              "Servo: pulse_min < pulse_center");
static_assert(amr::servo::pulse_center_us < amr::servo::pulse_max_us,
              "Servo: pulse_center < pulse_max");
static_assert(amr::servo::pulse_min_us >= 500, "Servo: Pulsbreite < 500 µs nicht zulaessig");
static_assert(amr::servo::pulse_max_us <= 2500, "Servo: Pulsbreite > 2500 µs nicht zulaessig");
static_assert(amr::servo::ticks_min < amr::servo::ticks_max, "Servo: ticks_min < ticks_max");
static_assert(amr::servo::ticks_max < amr::servo::pca_ticks_total,
              "Servo: ticks_max < 4096 (12-bit Ueberlauf)");
static_assert(amr::servo::ch_pan != amr::servo::ch_tilt,
              "Servo: Pan und Tilt auf unterschiedlichen Kanaelen");

// --- Servo: Rampe ---
static_assert(amr::servo::ramp_deg_per_step > 0, "Servo: Rampengeschwindigkeit > 0");
static_assert(amr::servo::ramp_step_ms > 0, "Servo: Rampenschritt > 0 ms");

// --- Regulator ---
static_assert(amr::regulator::vout_nominal_v > 0, "Regler: V_OUT > 0");
static_assert(amr::battery::threshold_system_shutdown_v > amr::regulator::vin_min_v,
              "System-Shutdown-Spannung muss ueber Regler-Dropout liegen");

// --- Batterie: Spannungskaskade ---
static_assert(amr::battery::cell_bms_uvp_v < amr::battery::cell_cutoff_v,
              "BMS-UVP < Entladeschluss");
static_assert(amr::battery::cell_cutoff_v < amr::battery::cell_nominal_v,
              "Entladeschluss < Nennspannung");
static_assert(amr::battery::cell_nominal_v < amr::battery::cell_charge_max_v,
              "Nennspannung < Ladeschluss");

// --- Batterie: Schwellwert-Reihenfolge ---
static_assert(amr::battery::threshold_critical_v < amr::battery::threshold_system_shutdown_v,
              "Critical < System-Shutdown");
static_assert(amr::battery::threshold_system_shutdown_v < amr::battery::threshold_motor_shutdown_v,
              "System-Shutdown < Motor-Shutdown");
static_assert(amr::battery::threshold_motor_shutdown_v < amr::battery::threshold_warning_v,
              "Motor-Shutdown < Warnung");

// --- Batterie: Stromlimits ---
static_assert(amr::battery::max_continuous_a > 0, "Dauerstrom > 0");
static_assert(amr::battery::max_continuous_a < amr::battery::max_pulse_a,
              "Dauerstrom < Impulsstrom");

// --- Safety ---
static_assert(amr::safety::motor_stall_timeout_ms > 0, "Motor-Stall-Timeout > 0");
static_assert(amr::safety::servo_stall_timeout_ms > 0, "Servo-Stall-Timeout > 0");
static_assert(amr::safety::motor_overcurrent_immediate_a < amr::battery::max_continuous_a,
              "Motor-Sofortabschaltung muss unter Pack-Dauerstrom liegen");

// --- INA260 ---
static_assert(amr::ina260::coulomb_capacity_mah > 0, "Coulomb-Referenz > 0");

// --- Regulator vs. Servo-Strombedarf ---
static_assert(2.0f * amr::servo::stall_current_a < amr::regulator::iout_max_a,
              "2x Servo-Stall muss unter Regler-Maximum liegen");
