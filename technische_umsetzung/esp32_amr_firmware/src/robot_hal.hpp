#pragma once
#include <Arduino.h>

// --- PIN DEFINITIONEN (Anpassen an deine Verdrahtung!) ---
#define ENC_LEFT_A 18
#define ENC_LEFT_B 19
#define ENC_RIGHT_A 22
#define ENC_RIGHT_B 23

#define MOT_LEFT_IN1 25
#define MOT_LEFT_IN2 26
#define MOT_RIGHT_IN1 32
#define MOT_RIGHT_IN2 33

#define PWM_FREQ 20000 // 20 kHz (Lautlos)
#define PWM_RES 8
#define PWM_CH_L 0
#define PWM_CH_R 1

volatile long encoder_left_count = 0;
volatile long encoder_right_count = 0;

void IRAM_ATTR isr_enc_left() {
    if (digitalRead(ENC_LEFT_B) == digitalRead(ENC_LEFT_A))
        encoder_left_count++;
    else
        encoder_left_count--;
}

void IRAM_ATTR isr_enc_right() {
    if (digitalRead(ENC_RIGHT_B) == digitalRead(ENC_RIGHT_A))
        encoder_right_count++;
    else
        encoder_right_count--;
}

class RobotHAL {
  private:
    portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

    void driveMotor(int ch_in1, int ch_in2, float speed) {
        int duty = constrain(abs(speed) * 255, 0, 255);
        if (speed > 0) {
            ledcWrite(ch_in1, duty);
            ledcWrite(ch_in2, 0);
        } else {
            ledcWrite(ch_in1, 0);
            ledcWrite(ch_in2, duty);
        }
    }

  public:
    void init() {
        pinMode(ENC_LEFT_A, INPUT_PULLUP);
        pinMode(ENC_LEFT_B, INPUT_PULLUP);
        pinMode(ENC_RIGHT_A, INPUT_PULLUP);
        pinMode(ENC_RIGHT_B, INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(ENC_LEFT_A), isr_enc_left,
                        CHANGE);
        attachInterrupt(digitalPinToInterrupt(ENC_RIGHT_A), isr_enc_right,
                        CHANGE);

        ledcSetup(0, PWM_FREQ, PWM_RES);
        ledcSetup(1, PWM_FREQ, PWM_RES);
        ledcSetup(2, PWM_FREQ, PWM_RES);
        ledcSetup(3, PWM_FREQ, PWM_RES);
        ledcAttachPin(MOT_LEFT_IN1, 0);
        ledcAttachPin(MOT_LEFT_IN2, 1);
        ledcAttachPin(MOT_RIGHT_IN1, 2);
        ledcAttachPin(MOT_RIGHT_IN2, 3);
    }

    void readEncoders(long &left, long &right) {
        portENTER_CRITICAL(&mux);
        left = encoder_left_count;
        right = encoder_right_count;
        portEXIT_CRITICAL(&mux);
    }

    void setMotors(float pwm_l, float pwm_r) {
        driveMotor(0, 1, pwm_l);
        driveMotor(2, 3, pwm_r);
    }
};
