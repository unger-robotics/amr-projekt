#pragma once
/**
 * @file ina260.hpp
 * @brief Header-only I2C-Treiber fuer TI INA260 Leistungsmonitor
 * @details Datenblatt: SBOS656C, Rev. C
 */
#include <Wire.h>
#include "config.h"

namespace amr::drivers {

class INA260 {
  private:
    static constexpr uint8_t REG_CONFIG = 0x00;
    static constexpr uint8_t REG_CURRENT = 0x01;
    static constexpr uint8_t REG_VOLTAGE = 0x02;
    static constexpr uint8_t REG_POWER = 0x03;
    static constexpr uint8_t REG_MASK_ENABLE = 0x06;
    static constexpr uint8_t REG_ALERT_LIMIT = 0x07;
    static constexpr uint8_t REG_MANUFACTURER = 0xFE;
    static constexpr uint8_t REG_DIE_ID = 0xFF;

    static constexpr uint16_t MANUFACTURER_ID = 0x5449; // "TI"
    static constexpr uint16_t DIE_ID = 0x2270;

    // Alert Mask: Under-Voltage (Bit 12)
    static constexpr uint16_t MASK_UNDER_VOLTAGE = 0x1000;

    uint8_t addr_;

    uint16_t readRegister16(uint8_t reg) {
        Wire.beginTransmission(addr_);
        Wire.write(reg);
        Wire.endTransmission(false);
        Wire.requestFrom(addr_, (uint8_t)2);
        uint16_t val = (uint16_t)(Wire.read() << 8);
        val |= Wire.read();
        return val;
    }

    void writeRegister16(uint8_t reg, uint16_t val) {
        Wire.beginTransmission(addr_);
        Wire.write(reg);
        Wire.write((uint8_t)(val >> 8));
        Wire.write((uint8_t)(val & 0xFF));
        Wire.endTransmission();
    }

  public:
    INA260()
        : addr_(amr::i2c::addr_ina260) {}

    bool init() {
        // Verify Manufacturer ID
        uint16_t mfr = readRegister16(REG_MANUFACTURER);
        if (mfr != MANUFACTURER_ID) {
            return false;
        }

        // Konfiguration schreiben (CT=1.1ms, AVG=4, continuous)
        writeRegister16(REG_CONFIG, amr::ina260::config_register);

        // Alert: Unterspannung
        writeRegister16(REG_MASK_ENABLE, MASK_UNDER_VOLTAGE);
        writeRegister16(REG_ALERT_LIMIT, amr::ina260::alert_voltage_limit);

        return true;
    }

    bool read(float &voltage, float &current, float &power) {
        // Strom: vorzeichenbehaftet (int16_t), LSB = 1.25 mA
        int16_t raw_current = (int16_t)readRegister16(REG_CURRENT);
        current = raw_current * amr::ina260::current_lsb_ma / 1000.0f; // [A]

        // Spannung: vorzeichenlos, LSB = 1.25 mV
        uint16_t raw_voltage = readRegister16(REG_VOLTAGE);
        voltage = raw_voltage * amr::ina260::voltage_lsb_mv / 1000.0f; // [V]

        // Leistung: vorzeichenlos, LSB = 10 mW
        uint16_t raw_power = readRegister16(REG_POWER);
        power = raw_power * amr::ina260::power_lsb_mw / 1000.0f; // [W]

        return true;
    }

    bool isAlertActive() {
        uint16_t mask = readRegister16(REG_MASK_ENABLE);
        return (mask & 0x0010) != 0; // Alert Function Flag (Bit 4)
    }
};

} // namespace amr::drivers
