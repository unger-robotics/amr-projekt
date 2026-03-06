#pragma once

#include <Arduino.h>

namespace amr::hardware {

class CliffSensor {
  public:
    explicit CliffSensor(uint8_t out_pin)
        : out_pin_(out_pin) {}

    void init() const { pinMode(out_pin_, INPUT); }

    bool isCliffDetected() const { return (digitalRead(out_pin_) == HIGH); }

  private:
    uint8_t out_pin_;
};

} // namespace amr::hardware
