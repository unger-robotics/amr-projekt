#pragma once

#include <Arduino.h>

namespace amr::hardware {

class RangeSensor {
  public:
    RangeSensor(uint8_t trig_pin, uint8_t echo_pin)
        : trig_pin_(trig_pin)
        , echo_pin_(echo_pin)
        , last_distance_(0)
        , trigger_pending_(false)
        , trigger_time_us_(0)
        , echo_start_(nullptr)
        , echo_end_(nullptr)
        , meas_ready_(nullptr)
        , echo_active_(nullptr) {}

    /**
     * Initialisiert Pins und registriert die Echo-ISR.
     * @param isr ISR-Funktion (IRAM_ATTR, CHANGE-Trigger)
     * @param start Pointer auf volatile echo_start_us
     * @param end Pointer auf volatile echo_end_us
     * @param ready Pointer auf volatile measurement_ready
     * @param active Pointer auf volatile echo_active
     */
    void init(void (*isr)(), volatile uint32_t *start, volatile uint32_t *end, volatile bool *ready,
              volatile bool *active) {
        echo_start_ = start;
        echo_end_ = end;
        meas_ready_ = ready;
        echo_active_ = active;

        pinMode(trig_pin_, OUTPUT);
        pinMode(echo_pin_, INPUT);
        digitalWrite(trig_pin_, LOW);
        attachInterrupt(digitalPinToInterrupt(echo_pin_), isr, CHANGE);
    }

    /**
     * Nicht-blockierenden Trigger senden (~12 us).
     * Muss alle 100 ms aufgerufen werden (10 Hz).
     */
    void trigger() {
        *meas_ready_ = false;
        *echo_active_ = false;
        *echo_start_ = 0;
        *echo_end_ = 0;

        digitalWrite(trig_pin_, LOW);
        delayMicroseconds(2);
        digitalWrite(trig_pin_, HIGH);
        delayMicroseconds(10);
        digitalWrite(trig_pin_, LOW);

        trigger_pending_ = true;
        trigger_time_us_ = micros();
    }

    /**
     * Prueft ob eine Messung vorliegt und gibt die Distanz zurueck.
     * Non-blocking: kehrt sofort zurueck.
     * @return true wenn neue Messung verfuegbar.
     */
    bool tryRead(float conversion_factor, float max_range, uint32_t timeout_us, float &distance) {
        if (!trigger_pending_)
            return false;

        if (*meas_ready_) {
            trigger_pending_ = false;
            uint32_t duration = *echo_end_ - *echo_start_;
            if (duration > 0 && duration < timeout_us) {
                last_distance_ = duration * conversion_factor;
            } else {
                last_distance_ = max_range + 0.01f;
            }
            distance = last_distance_;
            return true;
        }

        // Timeout: kein Echo nach max. Wartezeit
        if (micros() - trigger_time_us_ > timeout_us + 1000) {
            trigger_pending_ = false;
            last_distance_ = max_range + 0.01f;
            distance = last_distance_;
            return true;
        }

        return false;
    }

    float lastDistance() const { return last_distance_; }

  private:
    uint8_t trig_pin_;
    uint8_t echo_pin_;
    float last_distance_;
    bool trigger_pending_;
    uint32_t trigger_time_us_;
    volatile uint32_t *echo_start_;
    volatile uint32_t *echo_end_;
    volatile bool *meas_ready_;
    volatile bool *echo_active_;
};

} // namespace amr::hardware
