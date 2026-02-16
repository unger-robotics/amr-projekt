/**
 * @file config.h
 * @brief Zentrale Konfiguration für AMR Slave-Node (ESP32-S3)
 * @version 1.0.0
 * @date 2025-12-12
 *
 * @standard REP-103 (SI-Einheiten), REP-105 (Frames), Safety-First
 * @hardware Seeed Studio XIAO ESP32-S3, Cytron MDD3A, JGA25-370
 */

#ifndef CONFIG_H
#define CONFIG_H

// ==========================================================================
// 1. HARDWARE ABSTRACTION LAYER (HAL)
// ==========================================================================

// --- Antriebsstrang (Cytron MDD3A - DUAL PWM MODE) ---
#define PIN_MOTOR_LEFT_A D0  // MDD3A M1A (Vorwärts-PWM)
#define PIN_MOTOR_LEFT_B D1  // MDD3A M1B (Rückwärts-PWM)
#define PIN_MOTOR_RIGHT_A D2 // MDD3A M2A (Vorwärts-PWM)
#define PIN_MOTOR_RIGHT_B D3 // MDD3A M2B (Rückwärts-PWM)

// PWM-Kanäle (ESP32 LEDC) - A und B getauscht für korrekte Richtung
#define PWM_CH_LEFT_A 1  // war 0
#define PWM_CH_LEFT_B 0  // war 1
#define PWM_CH_RIGHT_A 3 // war 2
#define PWM_CH_RIGHT_B 2 // war 3

// --- Encoder Phase A (Hall-Encoder JGA25-370) ---
#define PIN_ENC_LEFT_A D6  // Phase A (Interrupt-fähig)
#define PIN_ENC_RIGHT_A D7 // Phase A (Interrupt-fähig)

// --- Encoder Phase B (Quadratur-Richtungserkennung) ---
#define PIN_ENC_LEFT_B D8  // Phase B (Quadratur-Richtung)
#define PIN_ENC_RIGHT_B D9 // Phase B (Quadratur-Richtung)

// --- Peripherie & Status ---
#define PIN_LED_MOSFET D10 // IRLZ24N Low-Side Switch

// --- I2C Bus (MPU6050 / Future Use) ---
#define PIN_I2C_SDA D4
#define PIN_I2C_SCL D5
#define IMU_I2C_ADDR 0x68

// --- Servos (Pan/Tilt - Optional - Status: nicht angeschlossen) ---
// #define PIN_SERVO_PAN D8
// #define PIN_SERVO_TILT D9

// ==========================================================================
// 2. KINEMATISCHE PARAMETER (SI-Einheiten / REP-103)
// ==========================================================================

#define WHEEL_DIAMETER 0.06567f // [m] Raddurchmesser (kalibriert: 2x 1m-Bodentest, Faktor 98.5/97.55)
#define WHEEL_RADIUS (WHEEL_DIAMETER / 2.0f)
#define WHEEL_BASE 0.178f // [m] Spurbreite
#define WHEEL_CIRCUMFERENCE (WHEEL_DIAMETER * 3.14159265359f)

// ==========================================================================
// 2.1 ENCODER-KALIBRIERUNG (2025-12-12)
// ==========================================================================
// Methode: 10-Umdrehungen-Test (A-only: 374.3/373.6, 2x-Quadratur: 748.6/747.2)
// Rekalibrierung mit Quadratur empfohlen

#define TICKS_PER_REV_LEFT 748.6f  // kalibriert (10-Umdrehungen-Test, 2x Quadratur-Zaehlung)
#define TICKS_PER_REV_RIGHT 747.2f // kalibriert (10-Umdrehungen-Test, 2x Quadratur-Zaehlung)
#define TICKS_PER_REV ((TICKS_PER_REV_LEFT + TICKS_PER_REV_RIGHT) / 2.0f)

#define METERS_PER_TICK_LEFT (WHEEL_CIRCUMFERENCE / TICKS_PER_REV_LEFT)
#define METERS_PER_TICK_RIGHT (WHEEL_CIRCUMFERENCE / TICKS_PER_REV_RIGHT)

// ==========================================================================
// 3. REGELUNGSTECHNIK
// ==========================================================================

// --- PWM Konfiguration ---
#define MOTOR_PWM_FREQ 20000 // 20 kHz (unhörbar)
#define MOTOR_PWM_BITS 8     // 8-bit Auflösung (0-255)
#define MOTOR_PWM_MAX 255

// --- Motor Deadzone ---
#define PWM_DEADZONE 35 // PWM unter dem Motor nicht anläuft

// --- LED-Streifen PWM ---
#define LED_PWM_FREQ 5000
#define LED_PWM_BITS 8
#define LED_PWM_CHANNEL 4

// ==========================================================================
// 4. SAFETY & TIMING
// ==========================================================================

#define FAILSAFE_TIMEOUT_MS 500 // Motoren stopp nach 500ms ohne cmd_vel
#define CONTROL_LOOP_HZ 50      // Regelfrequenz [Hz]
#define CONTROL_LOOP_PERIOD_MS (1000 / CONTROL_LOOP_HZ)
#define ODOM_PUBLISH_HZ 20 // Odometrie-Publikationsrate [Hz]
#define ODOM_PUBLISH_PERIOD_MS (1000 / ODOM_PUBLISH_HZ)
#define IMU_PUBLISH_HZ 20
#define IMU_PUBLISH_PERIOD_MS (1000 / IMU_PUBLISH_HZ)
#define IMU_CALIBRATION_SAMPLES 500
#define IMU_COMPLEMENTARY_ALPHA 0.02f  // Gyro-Gewicht (0.02 = 98% Gyro, 2% Encoder)

// ==========================================================================
// 5. COMPILE-TIME VALIDIERUNG (MISRA-inspiriert)
// ==========================================================================

static_assert(WHEEL_RADIUS > 0, "WHEEL_RADIUS must be positive");
static_assert(WHEEL_BASE > 0, "WHEEL_BASE must be positive");
static_assert(TICKS_PER_REV_LEFT > 0, "TICKS_PER_REV_LEFT must be positive");
static_assert(TICKS_PER_REV_RIGHT > 0, "TICKS_PER_REV_RIGHT must be positive");
static_assert(PWM_DEADZONE >= 0 && PWM_DEADZONE < MOTOR_PWM_MAX,
              "PWM_DEADZONE out of range");
static_assert(MOTOR_PWM_FREQ > 0, "MOTOR_PWM_FREQ must be positive");
static_assert(PIN_ENC_LEFT_B != PIN_ENC_LEFT_A, "Encoder L: Phase A und B muessen unterschiedliche Pins sein");
static_assert(PIN_ENC_RIGHT_B != PIN_ENC_RIGHT_A, "Encoder R: Phase A und B muessen unterschiedliche Pins sein");

#endif // CONFIG_H
