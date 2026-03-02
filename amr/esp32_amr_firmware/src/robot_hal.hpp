#pragma once
#include <Arduino.h>
#include "config.h"

volatile int32_t encoder_left_count = 0;
volatile int32_t encoder_right_count = 0;

// Overflow-Analyse: int32_t max ~2.147 Mrd Ticks
// Bei 2x-Quadratur (0,273 mm/Tick) entspricht dies ~586 km Gesamtfahrstrecke

void IRAM_ATTR isr_enc_left() {
    if (digitalRead(PIN_ENC_LEFT_A) ^ digitalRead(PIN_ENC_LEFT_B)) {
        encoder_left_count--;
    } else {
        encoder_left_count++;
    }
}

void IRAM_ATTR isr_enc_right() {
    if (digitalRead(PIN_ENC_RIGHT_A) ^ digitalRead(PIN_ENC_RIGHT_B)) {
        encoder_right_count++;
    } else {
        encoder_right_count--;
    }
}

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
            constrain(static_cast<int16_t>(fabsf(speed) * amr::pwm::motor_max),
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
        pinMode(PIN_ENC_LEFT_A, INPUT_PULLUP);
        pinMode(PIN_ENC_RIGHT_A, INPUT_PULLUP);
        pinMode(PIN_ENC_LEFT_B, INPUT_PULLUP);
        pinMode(PIN_ENC_RIGHT_B, INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_LEFT_A), isr_enc_left, CHANGE);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_RIGHT_A), isr_enc_right, CHANGE);

        // Motor-PWM: 4 Kanaele
        ledcSetup(PWM_CH_LEFT_A, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcSetup(PWM_CH_LEFT_B, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcSetup(PWM_CH_RIGHT_A, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcSetup(PWM_CH_RIGHT_B, amr::pwm::motor_freq_hz, amr::pwm::motor_bits);
        ledcAttachPin(PIN_MOTOR_LEFT_A, PWM_CH_LEFT_A);
        ledcAttachPin(PIN_MOTOR_LEFT_B, PWM_CH_LEFT_B);
        ledcAttachPin(PIN_MOTOR_RIGHT_A, PWM_CH_RIGHT_A);
        ledcAttachPin(PIN_MOTOR_RIGHT_B, PWM_CH_RIGHT_B);

        // LED-PWM: Kanal aus config.h
        ledcSetup(amr::pwm::led_channel, amr::pwm::led_freq_hz, amr::pwm::led_bits);
        ledcAttachPin(PIN_LED_MOSFET, amr::pwm::led_channel);
    }

    void readEncoders(int32_t &left, int32_t &right) {
        portENTER_CRITICAL(&mux);
        left = encoder_left_count;
        right = encoder_right_count;
        portEXIT_CRITICAL(&mux);
    }

    void setMotors(float pwm_l, float pwm_r) {
        driveMotor(PWM_CH_LEFT_A, PWM_CH_LEFT_B, pwm_l);
        driveMotor(PWM_CH_RIGHT_A, PWM_CH_RIGHT_B, pwm_r);
    }
};
