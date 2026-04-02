/**
 * @file twai_can.hpp
 * @brief TWAI (CAN 2.0B) Treiber fuer AMR Sensor-Node
 * @version 1.0.0
 *
 * Sendet Sensor-Daten parallel zu micro-ROS via CAN-Bus (SN65HVD230).
 * Fire-and-forget: CAN-Fehler sind nicht fatal, micro-ROS bleibt primaer.
 * TWAI ist intern thread-safe — kein extra Mutex noetig.
 */

#pragma once

#include <cstdint>
#include <cstring>
#include <driver/twai.h>
#include "config_sensors.h"

namespace amr::drivers {

class TwaiCan {
  public:
    /**
     * TWAI-Treiber installieren und starten.
     * @return true bei Erfolg, false wenn kein Transceiver vorhanden
     */
    bool init() {
        twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(
            (gpio_num_t)amr::hal::pin_can_tx, (gpio_num_t)amr::hal::pin_can_rx, TWAI_MODE_NORMAL);
        g_config.intr_flags = 0; // Automatische Interrupt-Auswahl (Level 1 kann belegt sein)
        twai_timing_config_t t_config = TWAI_TIMING_CONFIG_1MBITS();
        twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

        esp_err_t err = twai_driver_install(&g_config, &t_config, &f_config);
        if (err != ESP_OK)
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

    /** HC-SR04 Distanz [float32 LE, Meter], 4 Bytes */
    void sendRange(float distance_m) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_range;
        msg.data_length_code = 4;
        memcpy(msg.data, &distance_m, 4);
        transmit(msg);
    }

    /** Cliff-Status (0x00=OK, 0x01=Cliff), 1 Byte */
    void sendCliff(bool cliff_detected) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_cliff;
        msg.data_length_code = 1;
        msg.data[0] = cliff_detected ? 0x01 : 0x00;
        transmit(msg);
    }

    /** IMU Beschleunigung + Gyro-Z: ax,ay,az [int16, mg] + gz [int16, 0.01 rad/s], 8 Bytes */
    void sendImuAccel(float ax, float ay, float az, float gz) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_imu_accel;
        msg.data_length_code = 8;
        int16_t iax = (int16_t)(ax * 1000.0f); // m/s^2 → mg (approx)
        int16_t iay = (int16_t)(ay * 1000.0f);
        int16_t iaz = (int16_t)(az * 1000.0f);
        int16_t igz = (int16_t)(gz * 100.0f); // rad/s → 0.01 rad/s
        memcpy(&msg.data[0], &iax, 2);
        memcpy(&msg.data[2], &iay, 2);
        memcpy(&msg.data[4], &iaz, 2);
        memcpy(&msg.data[6], &igz, 2);
        transmit(msg);
    }

    /** IMU Heading [float32 LE, rad], 4 Bytes */
    void sendImuHeading(float heading_rad) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_imu_heading;
        msg.data_length_code = 4;
        memcpy(msg.data, &heading_rad, 4);
        transmit(msg);
    }

    /** Batterie: V [uint16 mV] + I [int16 mA] + P [uint16 mW], 6 Bytes */
    void sendBattery(float voltage, float current, float power) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_battery;
        msg.data_length_code = 6;
        uint16_t v_mv = (uint16_t)(voltage * 1000.0f);
        int16_t i_ma = (int16_t)(current * 1000.0f);
        uint16_t p_mw = (uint16_t)(power * 1000.0f);
        memcpy(&msg.data[0], &v_mv, 2);
        memcpy(&msg.data[2], &i_ma, 2);
        memcpy(&msg.data[4], &p_mw, 2);
        transmit(msg);
    }

    /** Battery Shutdown (0x00=OK, 0x01=Shutdown), 1 Byte */
    void sendBatteryShutdown(bool shutdown) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_battery_shutdown;
        msg.data_length_code = 1;
        msg.data[0] = shutdown ? 0x01 : 0x00;
        transmit(msg);
    }

    /** Heartbeat: Status-Flags + Uptime + I2C/Servo-Diagnostik, 8 Bytes
     *  [0] flags  [1] uptime_s  [2-3] i2c_err  [4-5] servo_err  [6-7] servo_ok */
    void sendHeartbeat(bool imu_ok, bool ina260_ok, bool pca9685_ok, bool bat_shutdown,
                       bool core1_ok, uint32_t i2c_err = 0, uint32_t servo_err = 0,
                       uint32_t servo_ok = 0) {
        twai_message_t msg = {};
        msg.identifier = amr::can::id_heartbeat;
        msg.data_length_code = 8;
        uint8_t flags = 0;
        if (imu_ok)
            flags |= (1 << 0);
        if (ina260_ok)
            flags |= (1 << 1);
        if (pca9685_ok)
            flags |= (1 << 2);
        if (bat_shutdown)
            flags |= (1 << 3);
        if (core1_ok)
            flags |= (1 << 4);
        msg.data[0] = flags;
        msg.data[1] = (uint8_t)((millis() / 1000) & 0xFF);
        // Diagnostik-Zaehler (saturiert bei 65535)
        uint16_t i2c_e = (i2c_err > 0xFFFF) ? 0xFFFF : (uint16_t)i2c_err;
        uint16_t srv_e = (servo_err > 0xFFFF) ? 0xFFFF : (uint16_t)servo_err;
        uint16_t srv_o = (servo_ok > 0xFFFF) ? 0xFFFF : (uint16_t)servo_ok;
        memcpy(&msg.data[2], &i2c_e, 2);
        memcpy(&msg.data[4], &srv_e, 2);
        memcpy(&msg.data[6], &srv_o, 2);
        transmit(msg);
    }

    /** Non-blocking CAN-Empfang. Gibt true zurueck wenn eine Nachricht vorliegt. */
    bool receiveMessage(twai_message_t &rx_msg) {
        if (!initialized_)
            return false;
        return twai_receive(&rx_msg, pdMS_TO_TICKS(0)) == ESP_OK;
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
