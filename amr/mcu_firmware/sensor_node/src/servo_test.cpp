/**
 * @file servo_test.cpp
 * @brief Interaktive Pan/Tilt-Servo Kalibrierung (ohne micro-ROS)
 *
 * Befehle ueber Serial (USB-CDC):
 *   p  /  t    Achse wechseln (Pan / Tilt)
 *   +  /  -    Winkel um 1° erhoehen / verringern
 *   f  /  b    Winkel um 0.5° feinjustieren (forward / back)
 *   c          Aktuellen Winkel als Neutral-Mitte ausgeben
 *   Zahl+Enter Winkel direkt setzen (z.B. "92")
 */
#include <Arduino.h>
#include <Wire.h>
#include "config_sensors.h"
#include "pca9685.hpp"

amr::drivers::PCA9685 pca9685;

static uint8_t active_ch = amr::servo::ch_pan;
static float current_angle[2] = {90.0f, 90.0f};

static const char *chName() {
    return active_ch == amr::servo::ch_pan ? "Pan" : "Tilt";
}

static void printAngle() {
    Serial.printf("%s = %.1f\xC2\xB0\n", chName(), current_angle[active_ch]);
}

static void setAndPrint(float angle) {
    angle = constrain(angle, 45.0f, 135.0f);
    current_angle[active_ch] = angle;
    // Direkt ohne Offset schreiben — Kalibrierung misst den Roh-Winkel
    uint16_t ticks = 123 + static_cast<uint16_t>((angle / 180.0f) * (492 - 123));
    Wire.beginTransmission(amr::i2c::addr_pca9685);
    Wire.write(0x06 + 4 * active_ch);
    Wire.write(0x00);
    Wire.write(0x00);
    Wire.write((uint8_t)(ticks & 0xFF));
    Wire.write((uint8_t)(ticks >> 8));
    Wire.endTransmission();
    printAngle();
}

static void printHelp() {
    Serial.println("=== Pan/Tilt-Servo Kalibrierung ===");
    Serial.println("Befehle:");
    Serial.println("  p/t    : Achse wechseln (Pan/Tilt)");
    Serial.println("  +/-    : +/- 1\xC2\xB0");
    Serial.println("  f/b    : +/- 0.5\xC2\xB0 (fein)");
    Serial.println("  c      : Neutral-Winkel ausgeben");
    Serial.println("  Zahl   : Winkel direkt setzen");
    Serial.println("Bereich: 45\xC2\xB0 .. 135\xC2\xB0");
    Serial.println();
}

void setup() {
    Serial.begin(921600);
    delay(2000);
    printHelp();

    pinMode(amr::hal::pin_led_internal, OUTPUT);
    digitalWrite(amr::hal::pin_led_internal, HIGH);

    Wire.begin(amr::hal::pin_i2c_sda, amr::hal::pin_i2c_scl);
    Wire.setClock(amr::i2c::master_freq_hz);

    bool ok = pca9685.init();
    Serial.printf("PCA9685 init: %s\n", ok ? "OK" : "FEHLER");

    if (ok) {
        setAndPrint(90.0f);
        active_ch = amr::servo::ch_tilt;
        setAndPrint(90.0f);
        active_ch = amr::servo::ch_pan;
        Serial.printf("Aktive Achse: %s. Justiere mit +/-/f/b.\n", chName());
    }
}

void loop() {
    static String buf;

    while (Serial.available()) {
        char c = Serial.read();

        if (c == 'p') {
            active_ch = amr::servo::ch_pan;
            Serial.printf(">>> Achse: %s (%.1f\xC2\xB0)\n", chName(), current_angle[active_ch]);
        } else if (c == 't') {
            active_ch = amr::servo::ch_tilt;
            Serial.printf(">>> Achse: %s (%.1f\xC2\xB0)\n", chName(), current_angle[active_ch]);
        } else if (c == '+') {
            setAndPrint(current_angle[active_ch] + 1.0f);
        } else if (c == '-') {
            setAndPrint(current_angle[active_ch] - 1.0f);
        } else if (c == 'f') {
            setAndPrint(current_angle[active_ch] + 0.5f);
        } else if (c == 'b') {
            setAndPrint(current_angle[active_ch] - 0.5f);
        } else if (c == 'c') {
            Serial.printf(
                ">>> %s Neutral-Winkel: %.1f\xC2\xB0 (Offset zu 90\xC2\xB0: %+.1f\xC2\xB0)\n",
                chName(), current_angle[active_ch], current_angle[active_ch] - 90.0f);
        } else if (c == '\n' || c == '\r') {
            buf.trim();
            if (buf.length() > 0) {
                float val = buf.toFloat();
                if (val >= 45.0f && val <= 135.0f) {
                    setAndPrint(val);
                } else {
                    Serial.println("Ausserhalb 45-135\xC2\xB0");
                }
            }
            buf = "";
        } else {
            buf += c;
        }
    }
}
