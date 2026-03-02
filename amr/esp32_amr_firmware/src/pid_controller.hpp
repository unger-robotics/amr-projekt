#pragma once
#include <algorithm>
#include "config.h"

class PidController {
  private:
    float kp, ki, kd, prev_error, integral, min_out, max_out;
    float d_filtered_;

  public:
    PidController(float p, float i, float d, float mn, float mx)
        : kp(p)
        , ki(i)
        , kd(d)
        , prev_error(0)
        , integral(0)
        , min_out(mn)
        , max_out(mx)
        , d_filtered_(0) {}

    float compute(float setpoint, float measured, float dt) {
        float error = setpoint - measured;
        integral += error * dt * ki;
        integral = std::max(min_out, std::min(integral, max_out)); // Anti-Windup
        float derivative = (error - prev_error) / dt;
        // D-Term-Tiefpass: alpha_d = dt / (tau + dt)
        float alpha_d = dt / (amr::pid::d_filter_tau + dt);
        d_filtered_ = alpha_d * derivative + (1.0f - alpha_d) * d_filtered_;
        float output = (kp * error) + integral + (kd * d_filtered_);
        prev_error = error;
        return std::max(min_out, std::min(output, max_out));
    }

    void reset() {
        integral = 0;
        prev_error = 0;
        d_filtered_ = 0;
    }
};
