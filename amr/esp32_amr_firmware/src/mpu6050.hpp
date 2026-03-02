#pragma once
#include <Wire.h>
#include "config.h"

class MPU6050 {
  private:
    static constexpr uint8_t REG_SMPLRT_DIV = 0x19;
    static constexpr uint8_t REG_GYRO_CONFIG = 0x1B;
    static constexpr uint8_t REG_ACCEL_CONFIG = 0x1C;
    static constexpr uint8_t REG_ACCEL_XOUT_H = 0x3B;
    static constexpr uint8_t REG_PWR_MGMT_1 = 0x6B;
    static constexpr uint8_t REG_WHO_AM_I = 0x75;

    static constexpr float GRAVITY = 9.80665f; // m/s^2
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
        : addr_(0)
        , gx_bias_(0)
        , gy_bias_(0)
        , gz_bias_(0)
        , heading_(0)
        , alpha_(amr::imu::complementary_alpha) {}

    bool init(uint8_t sda = PIN_I2C_SDA, uint8_t scl = PIN_I2C_SCL,
              uint8_t addr = amr::i2c::addr_mpu6050) {
        addr_ = addr;
        alpha_ = amr::imu::complementary_alpha;

        Wire.begin(sda, scl);
        Wire.setClock(amr::i2c::master_freq_hz);

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

            delay(2);
        }

        gx_bias_ = (float)sum_gx / (float)samples;
        gy_bias_ = (float)sum_gy / (float)samples;
        gz_bias_ = (float)sum_gz / (float)samples;
    }

    bool read(float &ax, float &ay, float &az, float &gx, float &gy, float &gz) {
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
        ax = (float)raw_ax / amr::imu::accel_sensitivity * GRAVITY;
        ay = (float)raw_ay / amr::imu::accel_sensitivity * GRAVITY;
        az = (float)raw_az / amr::imu::accel_sensitivity * GRAVITY;

        // Gyro: (raw - bias) / sensitivity * deg_to_rad -> rad/s
        gx = ((float)raw_gx - gx_bias_) / amr::imu::gyro_sensitivity * DEG_TO_RAD;
        gy = ((float)raw_gy - gy_bias_) / amr::imu::gyro_sensitivity * DEG_TO_RAD;
        gz = ((float)raw_gz - gz_bias_) / amr::imu::gyro_sensitivity * DEG_TO_RAD;

        return true;
    }

    // Komplementaerfilter: alpha = 98% Gyro, (1-alpha) = 2% Encoder
    // Konsistent mit config.h-Konvention (alpha = Gyro-Anteil)
    float updateHeading(float encoder_heading, float gz, float dt) {
        heading_ = alpha_ * (heading_ + gz * dt) + (1.0f - alpha_) * encoder_heading;
        return heading_;
    }

    float getHeading() const { return heading_; }

    void resetHeading(float h = 0.0f) { heading_ = h; }
};
