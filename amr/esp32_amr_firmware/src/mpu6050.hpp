#pragma once
#include <Wire.h>
#include "config.h"

#ifndef IMU_COMPLEMENTARY_ALPHA
#define IMU_COMPLEMENTARY_ALPHA 0.02f
#endif

class MPU6050 {
  private:
    static constexpr uint8_t REG_SMPLRT_DIV   = 0x19;
    static constexpr uint8_t REG_GYRO_CONFIG   = 0x1B;
    static constexpr uint8_t REG_ACCEL_CONFIG  = 0x1C;
    static constexpr uint8_t REG_ACCEL_XOUT_H  = 0x3B;
    static constexpr uint8_t REG_PWR_MGMT_1    = 0x6B;
    static constexpr uint8_t REG_WHO_AM_I      = 0x75;

    static constexpr float ACCEL_SENSITIVITY = 16384.0f; // LSB/g at +/-2g
    static constexpr float GYRO_SENSITIVITY  = 131.0f;   // LSB/(deg/s) at +/-250 deg/s
    static constexpr float GRAVITY           = 9.80665f; // m/s^2
    // DEG_TO_RAD is provided by Arduino.h

    uint8_t addr_;
    float gx_bias_;
    float gy_bias_;
    float gz_bias_;
    float heading_;
    float alpha_;

    void writeRegister(uint8_t reg, uint8_t val) {
        Wire.beginTransmission(addr_);
        Wire.write(reg);
        Wire.write(val);
        Wire.endTransmission();
    }

    uint8_t readRegister(uint8_t reg) {
        Wire.beginTransmission(addr_);
        Wire.write(reg);
        Wire.endTransmission(false);
        Wire.requestFrom(addr_, (uint8_t)1);
        return Wire.read();
    }

  public:
    MPU6050()
        : addr_(0), gx_bias_(0), gy_bias_(0), gz_bias_(0),
          heading_(0), alpha_(IMU_COMPLEMENTARY_ALPHA) {}

    bool init(uint8_t sda = PIN_I2C_SDA, uint8_t scl = PIN_I2C_SCL,
              uint8_t addr = IMU_I2C_ADDR) {
        addr_ = addr;
        alpha_ = IMU_COMPLEMENTARY_ALPHA;

        Wire.begin(sda, scl);
        Wire.setClock(400000); // 400 kHz Fast Mode

        // WHO_AM_I check
        uint8_t who = readRegister(REG_WHO_AM_I);
        if (who != 0x68) {
            return false;
        }

        // Wake up: clear sleep bit, select PLL with X-Gyro reference
        writeRegister(REG_PWR_MGMT_1, 0x01);
        delay(10);

        // Sample Rate = 1 kHz / (1 + 9) = 100 Hz
        writeRegister(REG_SMPLRT_DIV, 9);

        // Gyro: +/- 250 deg/s (FS_SEL = 0)
        writeRegister(REG_GYRO_CONFIG, 0x00);

        // Accel: +/- 2g (AFS_SEL = 0)
        writeRegister(REG_ACCEL_CONFIG, 0x00);

        delay(50); // Settle time

        return true;
    }

    void calibrateGyro(uint16_t samples = 500) {
        int32_t sum_gx = 0, sum_gy = 0, sum_gz = 0;

        for (uint16_t i = 0; i < samples; i++) {
            Wire.beginTransmission(addr_);
            Wire.write(REG_ACCEL_XOUT_H);
            Wire.endTransmission(false);
            Wire.requestFrom(addr_, (uint8_t)14);

            // Skip accel (6 bytes) + temp (2 bytes) = 8 bytes
            for (uint8_t j = 0; j < 8; j++) {
                Wire.read();
            }

            int16_t raw_gx = (int16_t)((Wire.read() << 8) | Wire.read());
            int16_t raw_gy = (int16_t)((Wire.read() << 8) | Wire.read());
            int16_t raw_gz = (int16_t)((Wire.read() << 8) | Wire.read());

            sum_gx += raw_gx;
            sum_gy += raw_gy;
            sum_gz += raw_gz;

            delay(2); // ~500 Hz sampling during calibration
        }

        gx_bias_ = (float)sum_gx / (float)samples;
        gy_bias_ = (float)sum_gy / (float)samples;
        gz_bias_ = (float)sum_gz / (float)samples;
    }

    bool read(float &ax, float &ay, float &az,
              float &gx, float &gy, float &gz) {
        Wire.beginTransmission(addr_);
        Wire.write(REG_ACCEL_XOUT_H);
        Wire.endTransmission(false);

        uint8_t count = Wire.requestFrom(addr_, (uint8_t)14);
        if (count != 14) {
            return false;
        }

        int16_t raw_ax = (int16_t)((Wire.read() << 8) | Wire.read());
        int16_t raw_ay = (int16_t)((Wire.read() << 8) | Wire.read());
        int16_t raw_az = (int16_t)((Wire.read() << 8) | Wire.read());

        // Skip temperature (2 bytes)
        Wire.read();
        Wire.read();

        int16_t raw_gx = (int16_t)((Wire.read() << 8) | Wire.read());
        int16_t raw_gy = (int16_t)((Wire.read() << 8) | Wire.read());
        int16_t raw_gz = (int16_t)((Wire.read() << 8) | Wire.read());

        // Accel: raw / sensitivity * gravity -> m/s^2
        ax = (float)raw_ax / ACCEL_SENSITIVITY * GRAVITY;
        ay = (float)raw_ay / ACCEL_SENSITIVITY * GRAVITY;
        az = (float)raw_az / ACCEL_SENSITIVITY * GRAVITY;

        // Gyro: (raw - bias) / sensitivity * deg_to_rad -> rad/s
        gx = ((float)raw_gx - gx_bias_) / GYRO_SENSITIVITY * DEG_TO_RAD;
        gy = ((float)raw_gy - gy_bias_) / GYRO_SENSITIVITY * DEG_TO_RAD;
        gz = ((float)raw_gz - gz_bias_) / GYRO_SENSITIVITY * DEG_TO_RAD;

        return true;
    }

    float updateHeading(float encoder_heading, float gz, float dt) {
        heading_ = alpha_ * encoder_heading
                 + (1.0f - alpha_) * (heading_ + gz * dt);
        return heading_;
    }

    float getHeading() const { return heading_; }

    void resetHeading(float h = 0.0f) { heading_ = h; }
};
