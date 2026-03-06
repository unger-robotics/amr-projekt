#pragma once
/**
 * @file pca9685.hpp
 * @brief Header-only I2C-Treiber fuer NXP PCA9685 16-Kanal PWM (Servo-Steuerung)
 * @details Datenblatt: NXP PCA9685 Rev. 4
 */
#include <Wire.h>
#include <algorithm>
#include "config_sensors.h"

namespace amr::drivers {

class PCA9685 {
  private:
    static constexpr uint8_t REG_MODE1 = 0x00;
    static constexpr uint8_t REG_MODE2 = 0x01;
    static constexpr uint8_t REG_LED0_ON_L = 0x06;
    static constexpr uint8_t REG_ALL_LED_OFF_H = 0xFD;
    static constexpr uint8_t REG_PRESCALE = 0xFE;

    // MODE1 bits
    static constexpr uint8_t MODE1_RESTART = 0x80;
    static constexpr uint8_t MODE1_SLEEP = 0x10;
    static constexpr uint8_t MODE1_AI = 0x20; // Auto-Increment

    uint8_t addr_;

    // Rampen-State pro Kanal (nur Pan + Tilt)
    static constexpr uint8_t NUM_SERVO_CH = 2;
    float current_angle_[NUM_SERVO_CH];
    float target_angle_[NUM_SERVO_CH];
    float ramp_deg_per_step_; // Runtime-konfigurierbar via setRampSpeed()

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

    void setPWM(uint8_t channel, uint16_t on, uint16_t off) {
        uint8_t reg = REG_LED0_ON_L + 4 * channel;
        Wire.beginTransmission(addr_);
        Wire.write(reg);
        Wire.write((uint8_t)(on & 0xFF));
        Wire.write((uint8_t)(on >> 8));
        Wire.write((uint8_t)(off & 0xFF));
        Wire.write((uint8_t)(off >> 8));
        Wire.endTransmission();
    }

    uint16_t angleToPWM(float angle_deg) {
        // Winkel begrenzen
        angle_deg = std::clamp(angle_deg, amr::servo::angle_min_deg, amr::servo::angle_max_deg);
        // Linear interpolieren: angle -> ticks
        float fraction = (angle_deg - amr::servo::angle_min_deg) / amr::servo::angle_range_deg;
        return amr::servo::ticks_min +
               static_cast<uint16_t>(fraction * (amr::servo::ticks_max - amr::servo::ticks_min));
    }

  public:
    PCA9685()
        : addr_(amr::i2c::addr_pca9685)
        , current_angle_{90.0f, 90.0f}
        , target_angle_{90.0f, 90.0f}
        , ramp_deg_per_step_(amr::servo::ramp_deg_per_step) {}

    bool init() {
        // Sleep -> Prescaler -> Wake -> Restart (Datenblatt Abschnitt 7.3.1.1)
        uint8_t mode1 = readRegister(REG_MODE1);

        // Sleep-Modus aktivieren (noetig vor Prescaler-Aenderung)
        writeRegister(REG_MODE1, (mode1 & ~MODE1_RESTART) | MODE1_SLEEP);
        delay(1);

        // Prescaler setzen (nur im Sleep-Modus moeglich)
        writeRegister(REG_PRESCALE, amr::servo::pca_prescale);

        // Aufwachen: Sleep-Bit loeschen, Auto-Increment aktivieren
        writeRegister(REG_MODE1, MODE1_AI);
        delay(1); // Oszillator-Stabilisierung (min. 500 us)

        // Restart (falls zuvor aktiv)
        mode1 = readRegister(REG_MODE1);
        if (mode1 & MODE1_RESTART) {
            writeRegister(REG_MODE1, mode1 | MODE1_RESTART);
        }

        // MODE2: Output-Treiber totem-pole (Default)
        writeRegister(REG_MODE2, 0x04);

        // Prescaler-Verifizierung
        uint8_t prescale = readRegister(REG_PRESCALE);
        if (prescale != amr::servo::pca_prescale) {
            return false;
        }

        return true;
    }

    void setAngle(uint8_t channel, float angle_deg) {
        uint16_t off_ticks = angleToPWM(angle_deg);
        setPWM(channel, 0, off_ticks);
        // State aktualisieren (nur fuer Rampen-Kanaele)
        if (channel < NUM_SERVO_CH) {
            current_angle_[channel] = angle_deg;
            target_angle_[channel] = angle_deg;
        }
    }

    void setTargetAngle(uint8_t channel, float angle_deg) {
        angle_deg = std::clamp(angle_deg, amr::servo::angle_min_deg, amr::servo::angle_max_deg);
        if (channel < NUM_SERVO_CH) {
            target_angle_[channel] = angle_deg;
        }
    }

    // Nicht-blockierende Rampenfahrt: 1 Schritt pro Aufruf
    // Rueckgabe: true wenn Ziel erreicht
    // WICHTIG: Nutzt setPWM() direkt statt setAngle(), da setAngle()
    // target_angle_ zuruecksetzt und damit die Rampe bricht.
    bool updateRamp(uint8_t channel) {
        if (channel >= NUM_SERVO_CH)
            return true;
        float diff = target_angle_[channel] - current_angle_[channel];
        if (fabsf(diff) < 0.5f) {
            current_angle_[channel] = target_angle_[channel];
            setPWM(channel, 0, angleToPWM(current_angle_[channel]));
            return true;
        }
        if (diff > 0) {
            current_angle_[channel] += ramp_deg_per_step_;
            if (current_angle_[channel] > target_angle_[channel]) {
                current_angle_[channel] = target_angle_[channel];
            }
        } else {
            current_angle_[channel] -= ramp_deg_per_step_;
            if (current_angle_[channel] < target_angle_[channel]) {
                current_angle_[channel] = target_angle_[channel];
            }
        }
        setPWM(channel, 0, angleToPWM(current_angle_[channel]));
        return false;
    }

    // Notfall-Abschaltung: ALL_LED_OFF_H Bit 4 = Full OFF
    void allOff() { writeRegister(REG_ALL_LED_OFF_H, 0x10); }

    // Alle Ausgaenge wieder aktivieren (Full-OFF zuruecksetzen)
    void clearAllOff() { writeRegister(REG_ALL_LED_OFF_H, 0x00); }

    float getCurrentAngle(uint8_t channel) const {
        if (channel >= NUM_SERVO_CH)
            return 0.0f;
        return current_angle_[channel];
    }

    void setRampSpeed(float deg_per_step) {
        deg_per_step = std::clamp(deg_per_step, 0.1f, 10.0f);
        ramp_deg_per_step_ = deg_per_step;
    }
};

} // namespace amr::drivers
