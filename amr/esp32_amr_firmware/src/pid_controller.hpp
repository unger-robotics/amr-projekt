#pragma once
#include <algorithm>

class PidController {
  private:
    float kp, ki, kd, prev_error, integral, min_out, max_out;

  public:
    PidController(float p, float i, float d, float mn, float mx)
        : kp(p), ki(i), kd(d), prev_error(0), integral(0), min_out(mn),
          max_out(mx) {}

    float compute(float setpoint, float measured, float dt) {
        float error = setpoint - measured;
        integral += error * dt * ki;
        integral = std::max(min_out, std::min(integral, max_out)); // Anti-Windup
        float derivative = (error - prev_error) / dt;
        float output = (kp * error) + integral + (kd * derivative);
        prev_error = error;
        return std::max(min_out, std::min(output, max_out));
    }

    void reset() {
        integral = 0;
        prev_error = 0;
    }
};
