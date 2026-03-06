#pragma once

#include <Arduino.h>

namespace amr::hardware {

class RangeSensor {
  public:
    RangeSensor(uint8_t trig_pin, uint8_t echo_pin)
        : trig_pin_(trig_pin)
        , echo_pin_(echo_pin) {}

    void init() const {
        pinMode(trig_pin_, OUTPUT);
        pinMode(echo_pin_, INPUT);
        digitalWrite(trig_pin_, LOW);
    }

    float readDistance(uint32_t timeout_us, float conversion_factor, float max_range) const {
        digitalWrite(trig_pin_, LOW);
        delayMicroseconds(2);
        digitalWrite(trig_pin_, HIGH);
        delayMicroseconds(10);
        digitalWrite(trig_pin_, LOW);

        unsigned long duration = pulseIn(echo_pin_, HIGH, timeout_us);

        if (duration == 0) {
            return max_range + 0.01f;
        }

        return duration * conversion_factor;
    }

  private:
    uint8_t trig_pin_;
    uint8_t echo_pin_;
};

} // namespace amr::hardware
