#pragma once
#include <Arduino.h>
#include "config.h"

volatile int32_t encoder_left_count = 0;
volatile int32_t encoder_right_count = 0;

// Overflow-Analyse: int32_t max ~2.147 Mrd Ticks
// Bei 0,546 mm/Tick entspricht dies ~1.172 km Gesamtfahrstrecke
// Fuer Indoor-AMR praktisch kein Overflow-Risiko

// Drehrichtung wird aus der PWM-Ansteuerung abgeleitet,
// nicht aus dem Encoder-Signal (A-only, kein Phase B).
volatile int8_t enc_left_dir = 1;
volatile int8_t enc_right_dir = 1;

void IRAM_ATTR isr_enc_left() {
    encoder_left_count += enc_left_dir;
}

void IRAM_ATTR isr_enc_right() {
    encoder_right_count += enc_right_dir;
}

class RobotHAL {
  private:
    portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

    void driveMotor(uint8_t ch_a, uint8_t ch_b, float speed, volatile int8_t &dir) {
        int16_t duty = constrain(abs(speed) * MOTOR_PWM_MAX, 0, MOTOR_PWM_MAX);
        // Deadzone-Kompensation: Werte unter PWM_DEADZONE erzeugen keine Bewegung
        if (duty > 0 && duty < PWM_DEADZONE) {
            duty = PWM_DEADZONE;
        }
        if (speed > 0) {
            dir = 1;
            ledcWrite(ch_a, duty);
            ledcWrite(ch_b, 0);
        } else if (speed < 0) {
            dir = -1;
            ledcWrite(ch_a, 0);
            ledcWrite(ch_b, duty);
        } else {
            ledcWrite(ch_a, 0);
            ledcWrite(ch_b, 0);
        }
    }

  public:
    void init() {
        // Encoder: nur Phase A, Pins aus config.h
        pinMode(PIN_ENC_LEFT_A, INPUT_PULLUP);
        pinMode(PIN_ENC_RIGHT_A, INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_LEFT_A), isr_enc_left,
                        RISING);
        attachInterrupt(digitalPinToInterrupt(PIN_ENC_RIGHT_A), isr_enc_right,
                        RISING);

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
        driveMotor(PWM_CH_LEFT_A, PWM_CH_LEFT_B, pwm_l, enc_left_dir);
        driveMotor(PWM_CH_RIGHT_A, PWM_CH_RIGHT_B, pwm_r, enc_right_dir);
    }
};
