#pragma once
#include <Arduino.h>
#include <algorithm>
#include "config.h"

volatile int32_t encoder_left_count = 0;
volatile int32_t encoder_right_count = 0;

// Overflow-Analyse: int32_t max ~2.147 Mrd Ticks
// Bei 2x-Quadratur (0,273 mm/Tick) entspricht dies ~586 km Gesamtfahrstrecke

void IRAM_ATTR isr_enc_left() {
    if (digitalRead(amr::hal::pin_enc_left_a) ^ digitalRead(amr::hal::pin_enc_left_b)) {
        encoder_left_count--;
    } else {
        encoder_left_count++;
    }
}

void IRAM_ATTR isr_enc_right() {
    if (digitalRead(amr::hal::pin_enc_right_a) ^ digitalRead(amr::hal::pin_enc_right_b)) {
        encoder_right_count++;
    } else {
        encoder_right_count--;
    }
}

namespace amr::hardware {

class RobotHAL {
  private:
    portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

    void driveMotor(uint8_t ch_a, uint8_t ch_b, float speed) {
        // Dead-Band: PID-Rauschen nahe Null ignorieren
        if (fabsf(speed) < amr::pid::deadband_threshold) {
            ledcWrite(ch_a, 0);
            ledcWrite(ch_b, 0);
            return;
        }
        int16_t duty =
            std::clamp(static_cast<int16_t>(fabsf(speed) * amr::pwm::motor_max),
                       static_cast<int16_t>(0), static_cast<int16_t>(amr::pwm::motor_max));
        if (duty < static_cast<int16_t>(amr::pwm::deadzone)) {
            duty = static_cast<int16_t>(amr::pwm::deadzone);
        }
        if (speed > 0) {
            ledcWrite(ch_a, duty);
            ledcWrite(ch_b, 0);
        } else if (speed < 0) {
            ledcWrite(ch_a, 0);
            ledcWrite(ch_b, duty);
        } else {
            ledcWrite(ch_a, 0);
            ledcWrite(ch_b, 0);
        }
    }

  public:
    void init() {
        // Encoder: Phase A (Interrupt) + Phase B (Richtung)
        pinMode(amr::hal::pin_enc_left_a, INPUT_PULLUP);
        pinMode(amr::hal::pin_enc_right_a, INPUT_PULLUP);
        pinMode(amr::hal::pin_enc_left_b, INPUT_PULLUP);
        pinMode(amr::hal::pin_enc_right_b, INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(amr::hal::pin_enc_left_a), isr_enc_left, CHANGE);
        attachInterrupt(digitalPinToInterrupt(amr::hal::pin_enc_right_a), isr_enc_right, CHANGE);

        // Motor-PWM: 4 Kanaele
        ledcSetup(amr::hal::pwm_ch_left_a, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcSetup(amr::hal::pwm_ch_left_b, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcSetup(amr::hal::pwm_ch_right_a, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcSetup(amr::hal::pwm_ch_right_b, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcAttachPin(amr::hal::pin_motor_left_a, amr::hal::pwm_ch_left_a);
        ledcAttachPin(amr::hal::pin_motor_left_b, amr::hal::pwm_ch_left_b);
        ledcAttachPin(amr::hal::pin_motor_right_a, amr::hal::pwm_ch_right_a);
        ledcAttachPin(amr::hal::pin_motor_right_b, amr::hal::pwm_ch_right_b);

        // LED-PWM: Kanal aus config.h
        ledcSetup(amr::pwm::led_channel, amr::pwm::led_freq_hz, amr::pwm::led_bits);
        ledcAttachPin(amr::hal::pin_led_mosfet, amr::pwm::led_channel);
    }

    void readEncoders(int32_t &left, int32_t &right) {
        portENTER_CRITICAL(&mux);
        left = encoder_left_count;
        right = encoder_right_count;
        portEXIT_CRITICAL(&mux);
    }

    void setMotors(float pwm_l, float pwm_r) {
        driveMotor(amr::hal::pwm_ch_left_a, amr::hal::pwm_ch_left_b, pwm_l);
        driveMotor(amr::hal::pwm_ch_right_a, amr::hal::pwm_ch_right_b, pwm_r);
    }
};

} // namespace amr::hardware
