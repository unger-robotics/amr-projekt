#pragma once
#include <Arduino.h>
#include "config.h"

volatile int32_t encoder_left_count = 0;
volatile int32_t encoder_right_count = 0;

// Overflow-Analyse: int32_t max ~2.147 Mrd Ticks
// Bei 2x-Quadratur (0,273 mm/Tick) entspricht dies ~586 km Gesamtfahrstrecke
// Fuer Indoor-AMR praktisch kein Overflow-Risiko

// Drehrichtung wird aus Quadratur-Dekodierung (Phase A + B) bestimmt.

void IRAM_ATTR isr_enc_left() {
    // Quadratur: Richtung aus XOR von Phase A und Phase B
    if (digitalRead(PIN_ENC_LEFT_A) ^ digitalRead(PIN_ENC_LEFT_B)) {
        encoder_left_count++;
    } else {
        encoder_left_count--;
    }
}

void IRAM_ATTR isr_enc_right() {
    // Rechter Motor: invertiert (gegenueberliegende Montage)
    if (digitalRead(PIN_ENC_RIGHT_A) ^ digitalRead(PIN_ENC_RIGHT_B)) {
        encoder_right_count--;
    } else {
        encoder_right_count++;
    }
}

class RobotHAL {
  private:
    portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

    void driveMotor(uint8_t ch_a, uint8_t ch_b, float speed) {
        int16_t duty = constrain(abs(speed) * MOTOR_PWM_MAX, 0, MOTOR_PWM_MAX);
        // Deadzone-Kompensation: Werte unter PWM_DEADZONE erzeugen keine Bewegung
        if (duty > 0 && duty < PWM_DEADZONE) {
            duty = PWM_DEADZONE;
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
        // Encoder: Phase A (Interrupt) + Phase B (Richtung), Pins aus config.h
        pinMode(PIN_ENC_LEFT_A, INPUT_PULLUP);
        pinMode(PIN_ENC_RIGHT_A, INPUT_PULLUP);
        pinMode(PIN_ENC_LEFT_B, INPUT_PULLUP);
        pinMode(PIN_ENC_RIGHT_B, INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_LEFT_A), isr_enc_left,
                        CHANGE);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_RIGHT_A), isr_enc_right,
                        CHANGE);

        // Motor-PWM: 4 Kanaele mit Zuordnung aus config.h
        ledcSetup(PWM_CH_LEFT_A, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
        ledcSetup(PWM_CH_LEFT_B, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
        ledcSetup(PWM_CH_RIGHT_A, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
        ledcSetup(PWM_CH_RIGHT_B, MOTOR_PWM_FREQ, MOTOR_PWM_BITS);
        ledcAttachPin(PIN_MOTOR_LEFT_A, PWM_CH_LEFT_A);
        ledcAttachPin(PIN_MOTOR_LEFT_B, PWM_CH_LEFT_B);
        ledcAttachPin(PIN_MOTOR_RIGHT_A, PWM_CH_RIGHT_A);
        ledcAttachPin(PIN_MOTOR_RIGHT_B, PWM_CH_RIGHT_B);

        // LED-PWM: Kanal 4 auf D10
        ledcSetup(LED_PWM_CHANNEL, LED_PWM_FREQ, LED_PWM_BITS);
        ledcAttachPin(PIN_LED_MOSFET, LED_PWM_CHANNEL);
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
