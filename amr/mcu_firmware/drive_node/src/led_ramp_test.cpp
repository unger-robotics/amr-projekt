/**
 * @file led_ramp_test.cpp
 * @brief MOSFET-Diagnose: GPIO 9 (D10) → IRLZ24N Gate
 *
 * Testet in 4 Phasen:
 *   1. digitalWrite HIGH/LOW (grundlegender GPIO-Test)
 *   2. LEDC PWM 0 → 100 % Rampe (10-bit, identisch zu main.cpp)
 *   3. LEDC Einzelstufen (0, 25 %, 50 %, 100 %)
 *   4. Schnelles Blinken (Zustandswechsel sichtbar?)
 *
 * Flash: pio run -e led_test -t upload -t monitor
 *
 * Erwartung bei funktionierender Schaltung:
 *   Phase 1: LED wechselt zwischen an/aus
 *   Phase 2: LED dimmt hoch und runter
 *   Phase 3: LED zeigt 4 Helligkeitsstufen
 *   Phase 4: LED blinkt schnell
 *
 * Wenn LED dauerhaft gedimmt bleibt: Gate floatet (Leitung pruefen)
 * Wenn LED dauerhaft voll an: Drain-Source Kurzschluss oder vertauscht
 * Wenn LED dauerhaft aus: Kein Strom (Streifen-Versorgung pruefen)
 */

#include <Arduino.h>
#include "config_drive.h"

// ---------------------------------------------------------------
// Konstanten
// ---------------------------------------------------------------
constexpr uint8_t PIN = amr::hal::pin_led_mosfet;     // D10 = GPIO 9
constexpr uint8_t LEDC_CH = amr::pwm::led_channel;    // Kanal 4
constexpr uint32_t LEDC_FREQ = amr::pwm::led_freq_hz; // 5 kHz
constexpr uint8_t LEDC_BITS = amr::pwm::led_bits;     // 10
constexpr uint32_t LEDC_MAX = amr::pwm::led_max;      // 1023

// ---------------------------------------------------------------
// Hilfsfunktion: Serielle Ausgabe mit Zeitstempel
// ---------------------------------------------------------------
static void logMsg(const char *msg) {
    Serial.printf("[%6lu ms] %s\n", millis(), msg);
}

static void logDuty(const char *label, uint32_t duty) {
    float pct = static_cast<float>(duty) / LEDC_MAX * 100.0f;
    Serial.printf("[%6lu ms] %s  duty=%4u/%u (%.0f %%)\n", millis(), label, duty, LEDC_MAX, pct);
}

// ---------------------------------------------------------------
// Phase 1: digitalWrite (ohne LEDC)
// ---------------------------------------------------------------
static void testDigitalWrite() {
    // LEDC abkoppeln, damit digitalWrite direkt wirkt
    ledcDetachPin(PIN);
    pinMode(PIN, OUTPUT);

    logMsg("=== Phase 1: digitalWrite ===");
    logMsg("Erwartung: LED wechselt an/aus");

    for (int i = 0; i < 4; i++) {
        logMsg("  HIGH (LED soll AN)");
        digitalWrite(PIN, HIGH);
        delay(2000);

        logMsg("  LOW  (LED soll AUS)");
        digitalWrite(PIN, LOW);
        delay(2000);
    }
}

// ---------------------------------------------------------------
// Phase 2: LEDC Rampe 0 → 100 % → 0 %
// ---------------------------------------------------------------
static void testLedcRamp() {
    ledcSetup(LEDC_CH, LEDC_FREQ, LEDC_BITS);
    ledcAttachPin(PIN, LEDC_CH);

    logMsg("=== Phase 2: LEDC Rampe (0 -> 100 -> 0 %%) ===");
    logMsg("Erwartung: LED dimmt hoch, dann runter");

    // Hoch
    for (uint32_t d = 0; d <= LEDC_MAX; d += 32) {
        ledcWrite(LEDC_CH, d);
        if (d % 256 == 0)
            logDuty("  ramp up ", d);
        delay(30);
    }
    ledcWrite(LEDC_CH, LEDC_MAX);
    logDuty("  peak    ", LEDC_MAX);
    delay(1000);

    // Runter
    for (int32_t d = LEDC_MAX; d >= 0; d -= 32) {
        ledcWrite(LEDC_CH, static_cast<uint32_t>(d));
        if (d % 256 == 0)
            logDuty("  ramp dn ", static_cast<uint32_t>(d));
        delay(30);
    }
    ledcWrite(LEDC_CH, 0);
    logDuty("  bottom  ", 0);
    delay(1000);
}

// ---------------------------------------------------------------
// Phase 3: Feste Stufen (0, 25, 50, 100 %)
// ---------------------------------------------------------------
static void testLedcSteps() {
    logMsg("=== Phase 3: LEDC Stufen ===");
    logMsg("Erwartung: 4 unterscheidbare Helligkeiten");

    const uint32_t steps[] = {0, LEDC_MAX / 4, LEDC_MAX / 2, LEDC_MAX};
    const char *labels[] = {"  0 %%  ", " 25 %% ", " 50 %% ", "100 %% "};

    for (int i = 0; i < 4; i++) {
        logDuty(labels[i], steps[i]);
        ledcWrite(LEDC_CH, steps[i]);
        delay(3000);
    }
    ledcWrite(LEDC_CH, 0);
    delay(500);
}

// ---------------------------------------------------------------
// Phase 4: Schnelles Blinken (Heartbeat-Simulation)
// ---------------------------------------------------------------
static void testBlink() {
    logMsg("=== Phase 4: Blinken (250 ms) ===");
    logMsg("Erwartung: LED blinkt sichtbar");

    for (int i = 0; i < 20; i++) {
        ledcWrite(LEDC_CH, LEDC_MAX);
        delay(250);
        ledcWrite(LEDC_CH, 0);
        delay(250);
    }
}

// ---------------------------------------------------------------
// Setup & Loop
// ---------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(3000);

    Serial.println();
    Serial.println("========================================");
    Serial.println("  MOSFET-Diagnose: IRLZ24N an GPIO 9");
    Serial.println("========================================");
    Serial.printf("  PIN_LED_MOSFET = D10 = GPIO %d\n", PIN);
    Serial.printf("  LEDC: Kanal %d, %lu Hz, %d bit\n", LEDC_CH, LEDC_FREQ, LEDC_BITS);
    Serial.println("========================================\n");
}

void loop() {
    testDigitalWrite();
    testLedcRamp();
    testLedcSteps();
    testBlink();

    logMsg("=== Alle Phasen abgeschlossen ===");
    logMsg("Beobachtung notieren, dann Neustart in 10 s\n");
    ledcWrite(LEDC_CH, 0);
    delay(10000);
}
