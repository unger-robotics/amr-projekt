#pragma once
#include <cmath>

namespace amr::kinematics {

struct WheelTargets {
    float left_rad_s;
    float right_rad_s;
};
struct RobotState {
    float x;
    float y;
    float theta;
};

class DiffDriveKinematics {
  private:
    float r, l; // Radius, Spurbreite
    RobotState odom;

  public:
    DiffDriveKinematics(float wheel_radius, float wheel_sep)
        : r(wheel_radius)
        , l(wheel_sep)
        , odom{0, 0, 0} {}

    WheelTargets computeMotorSpeeds(float v, float omega) {
        return {(v - (omega * l / 2.0f)) / r, (v + (omega * l / 2.0f)) / r};
    }

    RobotState updateOdometry(float wl, float wr, float dt) {
        float v = (r / 2.0f) * (wr + wl);
        float w = (r / l) * (wr - wl);
        odom.theta += w * dt;
        // Winkel normalisieren (-PI bis PI)
        if (odom.theta > M_PI)
            odom.theta -= 2 * M_PI;
        else if (odom.theta < -M_PI)
            odom.theta += 2 * M_PI;
        odom.x += v * cos(odom.theta) * dt;
        odom.y += v * sin(odom.theta) * dt;
        return odom;
    }
};

} // namespace amr::kinematics
