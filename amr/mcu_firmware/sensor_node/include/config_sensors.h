/**
 * @file config_sensors.h
 * @brief Zentrale Konfiguration fuer AMR Sensor-Node (ESP32-S3 #2)
 * @version 3.0.0
 * @date 2026-03-04
 *
 * @note HINWEIS: Die aktuelle Kommunikation zwischen dem Raspberry Pi 5,
 * dem ESP32-S3 #1 (Drive Node) und dem ESP32-S3 #2 (Sensor Node) erfolgt
 * ueber USB-CDC. Die folgende CAN-Bus-Architektur dient der Hardwareplanung
 * und Verdrahtung, um das System zukunftssicher vorzubereiten. Die
 * USB-Verbindung bleibt bis zur finalen Inbetriebnahme bestehen.
 *
 * @standard REP-103 (SI-Einheiten), REP-105 (Frames)
 * @hardware Seeed Studio XIAO ESP32-S3 (#2), HC-SR04, MH-B (YL-63),
 * INA260, PCA9685, MPU6050 (GY-521), 3.3V CAN Transceiver (SN65HVD230)
 */

#pragma once

#include <cstdint>

// ==========================================================================
// 1. HARDWARE ABSTRACTION LAYER (HAL)
// ==========================================================================
// Nutzung roher GPIO-Integer statt Arduino-Makros fuer ESP-IDF Kompatibilitaet.

namespace amr::hal {

// --- Ultraschall & Cliff ---
inline constexpr uint8_t pin_us_trig = 1;  // D0 - HC-SR04 Trigger (Ausgang)
inline constexpr uint8_t pin_us_echo = 2;  // D1 - HC-SR04 Echo (Eingang via Spannungsteiler)
inline constexpr uint8_t pin_ir_cliff = 3; // D2 - MH-B OUT (Eingang, LOW = Boden)

// --- I2C Bus (Sensoren & Aktoren) ---
inline constexpr uint8_t pin_i2c_sda = 5; // D4 - Zuvor auf Drive-Node
inline constexpr uint8_t pin_i2c_scl = 6; // D5 - Zuvor auf Drive-Node

// --- CAN-Bus Kommunikation (TWAI) ---
inline constexpr uint8_t pin_can_tx = 43; // D6 - Hardware UART TX
inline constexpr uint8_t pin_can_rx = 44; // D7 - Hardware UART RX

// --- System ---
inline constexpr uint8_t pin_led_internal = 21; // Onboard-LED (Ausgang, Active Low)

} // namespace amr::hal

// ==========================================================================
// 1.1 I2C-KONFIGURATION
// ==========================================================================

namespace amr::i2c {

inline constexpr uint8_t addr_ina260 = 0x40;  // Leistungsmonitor (A0=GND, A1=GND)
inline constexpr uint8_t addr_pca9685 = 0x41; // Servo-PWM (Loetbruecke A0 geschlossen)
inline constexpr uint8_t addr_mpu6050 = 0x68; // IMU (AD0=GND)

inline constexpr uint32_t master_freq_hz = 400000; // Fast-mode 400 kHz

} // namespace amr::i2c

// ==========================================================================
// 1.2 IMU-KONFIGURATION (MPU6050)
// ==========================================================================

namespace amr::imu {

// Yaw-Fusion: 98 % Gyro-Integration, 2 % Encoder-Heading
inline constexpr float complementary_alpha = 0.98f;
inline constexpr float gyro_sensitivity = 131.0f;
inline constexpr float accel_sensitivity = 16384.0f;
inline constexpr uint16_t calibration_samples = 500;

} // namespace amr::imu

// ==========================================================================
// 1.3 BATTERIE-KONFIGURATION (INA260 + Samsung INR18650-35E 3S1P)
// ==========================================================================

namespace amr::battery {

inline constexpr float threshold_warning_v = 10.0f;        // Stufe 1: Soft-Warnung
inline constexpr float threshold_motor_shutdown_v = 9.5f;  // Stufe 2: Motoren aus
inline constexpr float threshold_system_shutdown_v = 9.0f; // Stufe 3: System-Shutdown
inline constexpr float threshold_bms_disconnect_v = 7.5f;  // Stufe 4: BMS trennt Last
inline constexpr float threshold_hysteresis_v = 0.3f;
inline constexpr float pack_charge_max_v = 12.60f;
inline constexpr float capacity_design_ah = 3.35f;
inline constexpr float fuse_rating_a = 10.0f; // KFZ-Flachsicherung 10 A

} // namespace amr::battery

// ==========================================================================
// 1.4 INA260-REGISTER-KONFIGURATION
// ==========================================================================

namespace amr::ina260 {

inline constexpr uint16_t config_register = 0x6527;
inline constexpr uint16_t alert_voltage_limit = 8000;
inline constexpr float current_lsb_ma = 1.25f;
inline constexpr float voltage_lsb_mv = 1.25f;
inline constexpr float power_lsb_mw = 10.0f;

} // namespace amr::ina260

// ==========================================================================
// 1.5 SERVO-KONFIGURATION (PCA9685 + MG996R/MG90S)
// ==========================================================================

namespace amr::servo {

inline constexpr uint8_t ch_pan = 0;
inline constexpr uint8_t ch_tilt = 1;

// PWM-Bereich (PCA9685 Ticks fuer 0-180° Gesamtbereich)
inline constexpr float angle_min_deg = 0.0f;
inline constexpr float angle_max_deg = 180.0f;
inline constexpr float angle_range_deg = angle_max_deg - angle_min_deg;
inline constexpr uint16_t ticks_min = 123;
inline constexpr uint16_t ticks_max = 492;
inline constexpr uint8_t pca_prescale = 121;
inline constexpr float ramp_deg_per_step = 2.0f;

// Kalibrierung: Offset addiert auf den Soll-Winkel, damit 90° = geradeaus
inline constexpr float pan_offset_deg = 8.0f;
inline constexpr float tilt_offset_deg = 1.0f;

// Zul. Schwenkbereich (logisch, vor Offset-Anwendung)
inline constexpr float pan_limit_min_deg = 45.0f;
inline constexpr float pan_limit_max_deg = 135.0f;
inline constexpr float tilt_limit_min_deg = 80.0f;
inline constexpr float tilt_limit_max_deg = 135.0f;

} // namespace amr::servo

// ==========================================================================
// 1.6 CAN-BUS KONFIGURATION (TWAI, SN65HVD230)
// ==========================================================================

namespace amr::can {

inline constexpr uint32_t bitrate = 1000000; // 1 Mbit/s (ISO 11898)
inline constexpr uint32_t tx_timeout_ms = 3; // Kurz halten: 1-Mbit/s Frame ~130 us

// CAN-IDs (11-Bit Standard-Frame, Bereich 0x110..0x1FF)
inline constexpr uint32_t id_range = 0x110;
inline constexpr uint32_t id_cliff = 0x120;
inline constexpr uint32_t id_imu_accel = 0x130;
inline constexpr uint32_t id_imu_heading = 0x131;
inline constexpr uint32_t id_battery = 0x140;
inline constexpr uint32_t id_battery_shutdown = 0x141;
inline constexpr uint32_t id_heartbeat = 0x1F0;

inline constexpr uint32_t heartbeat_period_ms = 1000;

} // namespace amr::can

// ==========================================================================
// 2. TIMING & PUBLISHING RATEN
// ==========================================================================

namespace amr::timing {

inline constexpr uint32_t us_publish_hz = 10;
inline constexpr uint32_t us_publish_period_ms = 1000 / us_publish_hz; // 100 ms

inline constexpr uint32_t cliff_publish_hz = 20;
inline constexpr uint32_t cliff_publish_period_ms = 1000 / cliff_publish_hz; // 50 ms

// ISR-Echo-Timeout: maximale Laufzeit bis Echo-Puls als ungueltig gilt.
// 20.000 µs entsprechen ca. 3,4 m Hin- und Rueckweg (> us_max_range_m).
inline constexpr uint32_t us_timeout_us = 20000;

// IMU-Timing (50 Hz)
inline constexpr uint32_t imu_sample_hz = 50;
inline constexpr uint32_t imu_sample_period_ms = 1000 / imu_sample_hz;
inline constexpr uint32_t imu_publish_period_ms = 20;

// Batterie-Timing (2 Hz)
inline constexpr uint32_t battery_publish_hz = 2;
inline constexpr uint32_t battery_publish_period_ms = 500;

// Watchdog
inline constexpr uint32_t watchdog_miss_limit = 50;

} // namespace amr::timing

// ==========================================================================
// 3. PHYSIKALISCHE PARAMETER (HC-SR04)
// ==========================================================================

namespace amr::sensor {

// Schallgeschwindigkeit bei 20 °C in trockener Luft
inline constexpr float speed_of_sound_m_s = 343.2f;

// Umrechnungsfaktor: Laufzeit [µs] -> Distanz [m]
// d = (t * 10^-6 * v) / 2 = t * (v / 2000000)
// Die Multiplikation ist auf Mikrocontrollern effizienter als die Division.
inline constexpr float us_to_meters_factor = speed_of_sound_m_s / 2000000.0f;

// Gueltigkeitsbereich nach Datenblatt (in SI-Einheiten)
inline constexpr float us_min_range_m = 0.02f; // 2 cm
inline constexpr float us_max_range_m = 4.00f; // 400 cm

} // namespace amr::sensor

// ==========================================================================
// 4. COMPILE-TIME VALIDIERUNG
// ==========================================================================

// --- Timing ---
static_assert(amr::timing::us_publish_hz > 0, "US-Rate > 0");
static_assert(amr::timing::cliff_publish_hz > 0, "Cliff-Rate > 0");
static_assert(amr::timing::us_timeout_us < (amr::timing::us_publish_period_ms * 1000),
              "US-Timeout muss kleiner als die Publish-Periode sein");

// --- Sensorik ---
static_assert(amr::sensor::us_min_range_m < amr::sensor::us_max_range_m, "US Range Min < Max");

// --- I2C Adress-Kollisionspruefung ---
static_assert(amr::i2c::addr_ina260 != amr::i2c::addr_pca9685, "Kollision: INA260 / PCA9685");
static_assert(amr::i2c::addr_ina260 != amr::i2c::addr_mpu6050, "Kollision: INA260 / MPU6050");
static_assert(amr::i2c::addr_pca9685 != amr::i2c::addr_mpu6050, "Kollision: PCA9685 / MPU6050");

// --- IMU ---
static_assert(amr::imu::complementary_alpha > 0.0f && amr::imu::complementary_alpha < 1.0f,
              "Komplementaerfilter-Alpha: 0 < alpha < 1");
static_assert(amr::imu::calibration_samples > 0, "Kalibrierproben > 0");

// --- Batterie ---
static_assert(amr::battery::pack_charge_max_v > amr::battery::threshold_warning_v,
              "Charge-Max > Warning");
static_assert(amr::battery::threshold_warning_v > amr::battery::threshold_motor_shutdown_v,
              "Warning > Motor-Shutdown");
static_assert(amr::battery::threshold_motor_shutdown_v > amr::battery::threshold_system_shutdown_v,
              "Motor-Shutdown > System-Shutdown");
static_assert(amr::battery::threshold_system_shutdown_v > amr::battery::threshold_bms_disconnect_v,
              "System-Shutdown > BMS-Disconnect");
static_assert(amr::battery::threshold_hysteresis_v > 0.0f, "Hysterese muss positiv sein");
static_assert(amr::battery::fuse_rating_a > 0.0f, "Sicherungsbewertung muss positiv sein");

// --- Servo ---
static_assert(amr::servo::ticks_min < amr::servo::ticks_max, "Servo Ticks: Min < Max");
static_assert(amr::servo::angle_min_deg < amr::servo::angle_max_deg, "Servo: 0 < 180 deg");
static_assert(amr::servo::pan_limit_min_deg >= amr::servo::angle_min_deg, "Pan-Min im PWM-Bereich");
static_assert(amr::servo::pan_limit_max_deg + amr::servo::pan_offset_deg <=
                  amr::servo::angle_max_deg,
              "Pan-Max + Offset im PWM-Bereich");
static_assert(amr::servo::tilt_limit_min_deg >= amr::servo::angle_min_deg,
              "Tilt-Min im PWM-Bereich");
static_assert(amr::servo::tilt_limit_max_deg + amr::servo::tilt_offset_deg <=
                  amr::servo::angle_max_deg,
              "Tilt-Max + Offset im PWM-Bereich");

// --- CAN-Bus ---
static_assert(amr::can::id_range >= 0x100 && amr::can::id_range <= 0x7FF, "CAN-ID 11-Bit");
static_assert(amr::can::id_heartbeat >= 0x100 && amr::can::id_heartbeat <= 0x7FF, "CAN-ID 11-Bit");
static_assert(amr::can::bitrate == 1000000, "CAN-Bitrate 1 Mbit/s");
