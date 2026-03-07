/**
 * @file twai_can.hpp
 * @brief TWAI (CAN 2.0B) Treiber fuer AMR Drive-Node
 * @version 1.0.0
 *
 * Sendet Antriebs-Daten parallel zu micro-ROS via CAN-Bus (SN65HVD230).
 * Fire-and-forget: CAN-Fehler sind nicht fatal, micro-ROS bleibt primaer.
 * TWAI ist intern thread-safe — kein extra Mutex noetig.
 */

#pragma once

#include <cstdint>
#include <cstring>
#include <driver/twai.h>
#include "config_drive.h"

namespace amr::drivers {

class TwaiCan {
  public:
    bool init() {
        twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(
            (gpio_num_t)amr::hal::pin_can_tx, (gpio_num_t)amr::hal::pin_can_rx, TWAI_MODE_NORMAL);
        twai_timing_config_t t_config = TWAI_TIMING_CONFIG_1MBITS();
        twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

        if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK)
            return false;
        if (twai_start() != ESP_OK) {
            twai_driver_uninstall();
            return false;
        }
        initialized_ = true;
        return true;
    }

    void deinit() {
        if (!initialized_)
            return;
        twai_stop();
        twai_driver_uninstall();
        initialized_ = false;
    }

    /** Odometrie Position: x, y [2x float32 LE, m], 8 Bytes */
    void sendOdomPos(float x, float y) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_odom_pos;
        msg.data_length_code = 8;
        memcpy(&msg.data[0], &x, 4);
        memcpy(&msg.data[4], &y, 4);
        transmit(msg);
    }

    /** Odometrie Heading + Speed: theta [rad], v_linear [m/s], 8 Bytes */
    void sendOdomHeading(float theta, float v_linear) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_odom_heading;
        msg.data_length_code = 8;
        memcpy(&msg.data[0], &theta, 4);
        memcpy(&msg.data[4], &v_linear, 4);
        transmit(msg);
    }

    /** Encoder-Feedback: left, right [2x float32 LE, rad/s], 8 Bytes */
    void sendEncoder(float left_rad_s, float right_rad_s) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_encoder;
        msg.data_length_code = 8;
        memcpy(&msg.data[0], &left_rad_s, 4);
        memcpy(&msg.data[4], &right_rad_s, 4);
        transmit(msg);
    }

    /** Motor-PWM Duty: left, right [2x int16 LE, -255..+255], 4 Bytes */
    void sendMotorPwm(int16_t left_duty, int16_t right_duty) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_motor_pwm;
        msg.data_length_code = 4;
        memcpy(&msg.data[0], &left_duty, 2);
        memcpy(&msg.data[2], &right_duty, 2);
        transmit(msg);
    }

    /** Heartbeat: Status-Flags [uint8] + Uptime [uint8, s mod 256], 2 Bytes
     *  Bit0=EncoderOK, Bit1=MotorOK, Bit2=PID-Active, Bit3=BatShutdown,
     *  Bit4=Core1OK, Bit5=FailsafeActive */
    void sendHeartbeat(bool encoder_ok, bool motor_ok, bool pid_active, bool bat_shutdown,
                       bool core1_ok, bool failsafe_active) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_heartbeat;
        msg.data_length_code = 2;
        uint8_t flags = 0;
        if (encoder_ok)
            flags |= (1 << 0);
        if (motor_ok)
            flags |= (1 << 1);
        if (pid_active)
            flags |= (1 << 2);
        if (bat_shutdown)
            flags |= (1 << 3);
        if (core1_ok)
            flags |= (1 << 4);
        if (failsafe_active)
            flags |= (1 << 5);
        msg.data[0] = flags;
        msg.data[1] = (uint8_t)((millis() / 1000) & 0xFF);
        transmit(msg);
    }

  private:
    bool initialized_ = false;

    void transmit(twai_message_t &msg) {
        if (!initialized_)
            return;
        twai_transmit(&msg, pdMS_TO_TICKS(amr::can::tx_timeout_ms));
    }
};

} // namespace amr::drivers
