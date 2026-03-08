/**
 * @file config_drive.h
 * @brief Zentrale Konfiguration fuer AMR Drive-Node (ESP32-S3 #1 - Antriebsebene)
 * @version 4.0.0
 * @date 2026-03-04
 *
 * @note HINWEIS: Die aktuelle Kommunikation zwischen dem Raspberry Pi 5,
 * dem ESP32-S3 #1 (Drive Node) und dem ESP32-S3 #2 (Sensor Node) erfolgt
 * ueber USB-CDC. Die folgende CAN-Bus-Architektur dient der Hardwareplanung
 * und Verdrahtung, um das System zukunftssicher vorzubereiten. Die
 * USB-Verbindung bleibt bis zur finalen Inbetriebnahme bestehen.
 *
 * @standard REP-103 (SI-Einheiten), REP-105 (Frames), Safety-First
 * @hardware Seeed Studio XIAO ESP32-S3 (#1), Cytron MDD3A, JGA25-370 (1:34),
 * 3.3V CAN Transceiver (SN65HVD230), LED-Streifen SMD 5050
 * @battery  Samsung INR18650-35E 3S1P (NCA, 10,80 V / 3.350 mAh)
 */

#pragma once

#include <cstdint>

// ==========================================================================
// 1. HARDWARE ABSTRACTION LAYER (HAL)
// ==========================================================================
// Nutzung roher GPIO-Integer statt Arduino-Makros (Dx) fuer ESP-IDF Kompatibilitaet.

namespace amr::hal {

// --- Antriebsstrang (Cytron MDD3A - DUAL PWM MODE) ---
inline constexpr uint8_t pin_motor_left_a = 1;  // D0
inline constexpr uint8_t pin_motor_left_b = 2;  // D1
inline constexpr uint8_t pin_motor_right_a = 3; // D2
inline constexpr uint8_t pin_motor_right_b = 4; // D3

// PWM-Kanaele (ESP32 LEDC)
inline constexpr uint8_t pwm_ch_left_a = 0;
inline constexpr uint8_t pwm_ch_left_b = 1;
inline constexpr uint8_t pwm_ch_right_a = 2;
inline constexpr uint8_t pwm_ch_right_b = 3;

// --- Encoder (Hall-Encoder JGA25-370, 11 CPR) ---
inline constexpr uint8_t pin_enc_left_a = 5;  // D4 - Interrupt-faehig (Zuvor D6)
inline constexpr uint8_t pin_enc_right_a = 6; // D5 - Interrupt-faehig (Zuvor D7)
inline constexpr uint8_t pin_enc_left_b = 7;  // D8 - Richtungserkennung
inline constexpr uint8_t pin_enc_right_b = 8; // D9 - Richtungserkennung

// --- CAN-Bus Kommunikation (TWAI) ---
inline constexpr uint8_t pin_can_tx = 43; // D6 - Hardware UART TX
inline constexpr uint8_t pin_can_rx = 44; // D7 - Hardware UART RX

// --- Peripherie & Status ---
inline constexpr uint8_t pin_led_mosfet = 9;    // D10 - IRLZ24N Low-Side Switch
inline constexpr uint8_t pin_led_internal = 21; // Onboard-LED (Gelb) - Active Low!

} // namespace amr::hal

// ==========================================================================
// 2. KINEMATISCHE PARAMETER (SI-Einheiten / REP-103)
// ==========================================================================

namespace amr::kinematics {

inline constexpr float wheel_diameter = 0.06567f; // [m] kalibriert
inline constexpr float wheel_radius = wheel_diameter / 2.0f;
inline constexpr float wheel_base = 0.178f; // [m] Spurbreite Mitte-Mitte
inline constexpr float wheel_circumference = wheel_diameter * 3.14159265359f;

inline constexpr float ticks_per_rev_left = 748.6f;  // kalibriert
inline constexpr float ticks_per_rev_right = 747.2f; // kalibriert

} // namespace amr::kinematics

// ==========================================================================
// 3. REGELUNGSTECHNIK
// ==========================================================================

// --- PWM Konfiguration (Motoren) ---
namespace amr::pwm {

inline constexpr uint32_t motor_freq_hz = 20000;              // 20 kHz
inline constexpr uint8_t motor_bits = 8;                      // 8-bit
inline constexpr uint32_t motor_max = (1u << motor_bits) - 1; // 255
inline constexpr uint32_t deadzone = 35;                      // Anlaufschwelle

// --- LED-Streifen PWM ---
inline constexpr uint32_t led_freq_hz = 5000;             // 5 kHz
inline constexpr uint8_t led_bits = 10;                   // 10-bit
inline constexpr uint32_t led_max = (1u << led_bits) - 1; // 1023
inline constexpr uint8_t led_channel = 4;                 // LEDC-Kanal
} // namespace amr::pwm

// --- PID-Parameter ---
namespace amr::pid {

inline constexpr float kp = 0.4f;
inline constexpr float ki = 0.1f;
inline constexpr float kd = 0.0f;

inline constexpr float i_min = -1.0f; // Anti-Windup
inline constexpr float i_max = 1.0f;

inline constexpr float output_min = -1.0f;
inline constexpr float output_max = 1.0f;

inline constexpr float d_filter_tau = 0.02f;         // [s]
inline constexpr float ema_alpha = 0.3f;             // Encoder-Filter
inline constexpr float max_accel_rad_s2 = 5.0f;      // Rampe [rad/s^2]
inline constexpr float deadband_threshold = 0.08f;   // Totzone
inline constexpr float hard_stop_threshold = 0.01f;  // Rampe umgehen
inline constexpr float stillstand_threshold = 0.01f; // PID umgehen

} // namespace amr::pid

// ==========================================================================
// 4. SAFETY & TIMING
// ==========================================================================

namespace amr::timing {

inline constexpr uint32_t control_loop_hz = 50;
inline constexpr uint32_t control_loop_period_ms = 1000 / control_loop_hz; // 20 ms

inline constexpr uint32_t odom_publish_hz = 20;
inline constexpr uint32_t odom_publish_period_ms = 1000 / odom_publish_hz; // 50 ms

inline constexpr uint32_t failsafe_timeout_ms = 500;
inline constexpr uint32_t watchdog_miss_limit = 50;

} // namespace amr::timing

// ==========================================================================
// 5. CAN-BUS KONFIGURATION (TWAI, SN65HVD230)
// ==========================================================================

namespace amr::can {

inline constexpr uint32_t bitrate = 1000000; // 1 Mbit/s (ISO 11898)
inline constexpr uint32_t tx_timeout_ms = 10;

// CAN-IDs (11-Bit Standard-Frame, Bereich 0x200..0x2FF)
// Kein Overlap mit Sensor-Node (0x110..0x1F0)
inline constexpr uint32_t id_odom_pos = 0x200;
inline constexpr uint32_t id_odom_heading = 0x201;
inline constexpr uint32_t id_encoder = 0x210;
inline constexpr uint32_t id_motor_pwm = 0x220;
inline constexpr uint32_t id_heartbeat = 0x2F0;

inline constexpr uint32_t heartbeat_period_ms = 1000;
inline constexpr uint32_t encoder_can_period_ms = 100; // 10 Hz
inline constexpr uint32_t motor_can_period_ms = 100;   // 10 Hz

// Empfangs-IDs (Sensor-Node → Drive-Node, Sicherheitspfad)
inline constexpr uint32_t id_cliff_rx = 0x120;           // Cliff-Signal vom Sensor-Node
inline constexpr uint32_t id_battery_shutdown_rx = 0x141; // Battery-Shutdown vom Sensor-Node

} // namespace amr::can

// ==========================================================================
// 6. COMPILE-TIME VALIDIERUNG
// ==========================================================================

static_assert(amr::kinematics::wheel_radius > 0, "wheel_radius > 0");
static_assert(amr::kinematics::wheel_base > 0, "wheel_base > 0");
static_assert(amr::kinematics::ticks_per_rev_left > 0, "ticks L > 0");
static_assert(amr::kinematics::ticks_per_rev_right > 0, "ticks R > 0");

static_assert(amr::pwm::deadzone < amr::pwm::motor_max, "deadzone < motor_max");
static_assert(amr::pwm::motor_freq_hz > 0 && amr::pwm::motor_freq_hz <= 20000,
              "PWM 0 < f <= 20 kHz");

static_assert(amr::hal::pin_enc_left_b != amr::hal::pin_enc_left_a,
              "Encoder L: Phase A != Phase B");
static_assert(amr::hal::pin_enc_right_b != amr::hal::pin_enc_right_a,
              "Encoder R: Phase A != Phase B");

static_assert(amr::pid::i_min < amr::pid::i_max, "PID: i_min < i_max");
static_assert(amr::pid::output_min < amr::pid::output_max, "PID: output_min < output_max");

static_assert(amr::timing::control_loop_hz > 0, "control_loop_hz > 0");
static_assert(amr::timing::failsafe_timeout_ms > amr::timing::control_loop_period_ms,
              "failsafe_timeout > Regelzyklus");

// --- CAN-Bus ---
static_assert(amr::can::id_odom_pos >= 0x200 && amr::can::id_heartbeat <= 0x2FF,
              "Drive CAN-IDs im Bereich 0x200..0x2FF");
static_assert(amr::can::bitrate == 1000000, "CAN-Bitrate 1 Mbit/s");
