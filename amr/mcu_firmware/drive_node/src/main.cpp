/**
 * @file main.cpp
 * @brief Hauptprogramm fuer den AMR Drive-Node (ESP32-S3 #1)
 * @version 4.0.0
 * @date 2026-03-04
 *
 * Dual-Core-Architektur fuer deterministische Motorregelung:
 *
 * - Core 1 (FreeRTOS Task "Ctrl", 50 Hz): Encoder-Auswertung, EMA-Filter,
 *   Beschleunigungsrampe, PID-Regelung, Odometrie.
 * - Core 0 (Arduino loop): micro-ROS Executor (3 Subscriber, 1 Publisher),
 *   LED-Heartbeat, Inter-Core-Watchdog, CAN-Bus Dual-Path (TWAI, parallel zu micro-ROS).
 *
 * Antrieb, PID, Odometrie, LED. Kein I2C — alle Sensoren/Aktoren auf Sensor-Node.
 *
 * Topics: /odom (20 Hz),
 *         /cmd_vel (Sub), /hardware_cmd (Sub), /battery_shutdown (Sub)
 */
#include <Arduino.h>
#include "config_drive.h"
#include <algorithm>
#include <geometry_msgs/msg/twist.h>
#include <geometry_msgs/msg/point.h>
#include <micro_ros_platformio.h>
#include <nav_msgs/msg/odometry.h>
#include <std_msgs/msg/bool.h>
#include <rcl/rcl.h>
#include <rclc/executor.h>
#include <rclc/rclc.h>
#include <rmw_microros/rmw_microros.h>

#include "diff_drive_kinematics.hpp"
#include "pid_controller.hpp"
#include "robot_hal.hpp"
#include "twai_can.hpp"

// --- Namespace-Aliase ---
using amr::control::PidController;
using amr::drivers::TwaiCan;
using amr::hardware::RobotHAL;
using amr::kinematics::DiffDriveKinematics;
using amr::kinematics::RobotState;
using amr::kinematics::WheelTargets;

// --- SETUP ---
RobotHAL hal;
DiffDriveKinematics kinematics(amr::kinematics::wheel_radius, amr::kinematics::wheel_base);
PidController pid_l(amr::pid::kp, amr::pid::ki, amr::pid::kd, amr::pid::output_min,
                    amr::pid::output_max);
PidController pid_r(amr::pid::kp, amr::pid::ki, amr::pid::kd, amr::pid::output_min,
                    amr::pid::output_max);

// --- CAN-Bus (TWAI) ---
TwaiCan can;
bool can_ok = false;

/** Mutex-geschuetzter Datenaustausch zwischen Core 0 und Core 1.
 *  Core 1 schreibt: Odometrie (ox/oy/oth/ov/ow).
 *  Core 0 schreibt: Sollwerte (tv/tw). */
struct SharedData {
    float tv = 0, tw = 0, ox = 0, oy = 0, oth = 0, ov = 0, ow = 0;
};
SharedData shared;
SemaphoreHandle_t mutex;

volatile uint32_t last_cmd_time = 0;
volatile uint32_t core1_heartbeat = 0;

rcl_publisher_t pub_odom;
rcl_subscription_t sub_vel;
rcl_subscription_t sub_hardware;
rcl_subscription_t sub_battery_shutdown;
geometry_msgs__msg__Twist msg_vel;
geometry_msgs__msg__Point msg_hardware;
std_msgs__msg__Bool msg_battery_shutdown;
nav_msgs__msg__Odometry msg_odom;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

// Batterie-Unterspannungs-Flag (gesteuert via /battery_shutdown Topic vom Sensor-Node)
volatile bool battery_motor_shutdown = false;

// CAN-Notstopp-Flags (Sensor-Node → Drive-Node, Hardware-Redundanzpfad)
volatile bool can_cliff_stop = false;
volatile bool can_battery_stop = false;

/** Deferred Hardware: Callback schreibt Werte (RAM), loop() wendet sie an.
 *  motor_limit_pct skaliert PID-Sollwerte, led_pwm=0 aktiviert Auto-Heartbeat. */
struct HardwareCommand {
    volatile float motor_limit_pct; // 0-100
    volatile float led_pwm;         // 0-255, 0 = auto heartbeat
    volatile bool update_pending;
};
HardwareCommand hw_cmd = {100.0f, 0.0f, false};

/**
 * Echtzeit-Regelschleife auf Core 1 (50 Hz, vTaskDelayUntil).
 *
 * Pipeline pro Zyklus: Encoder lesen → Drehzahl berechnen (rad/s) →
 * EMA-Filter → Sollwerte aus SharedData → Failsafe/Batterie-Check →
 * Inverskinematik → Motor-Limit → Beschleunigungsrampe → PID →
 * Motoren ansteuern → Vorwaertskinematik → Odometrie schreiben.
 */
void controlTask(void *p) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    float last_sp_l = 0, last_sp_r = 0;
    float ml_filt = 0, mr_filt = 0;
    uint32_t last_us = micros();

    while (1) {
        uint32_t now_us = micros();
        float dt = (now_us - last_us) / 1000000.0f;
        last_us = now_us;

        if (dt < 0.001f)
            dt = 0.001f;
        if (dt > 0.1f)
            dt = 0.1f;

        int32_t tl, tr;
        hal.readEncoders(tl, tr);
        static int32_t ptl = 0, ptr = 0;
        float ml =
            (static_cast<float>(tl - ptl) / amr::kinematics::ticks_per_rev_left) * 2 * PI / dt;
        float mr =
            (static_cast<float>(tr - ptr) / amr::kinematics::ticks_per_rev_right) * 2 * PI / dt;
        ptl = tl;
        ptr = tr;

        // EMA-Filter: Glaettet Quantisierungsrauschen fuer PID
        ml_filt = amr::pid::ema_alpha * ml + (1.0f - amr::pid::ema_alpha) * ml_filt;
        mr_filt = amr::pid::ema_alpha * mr + (1.0f - amr::pid::ema_alpha) * mr_filt;

        float tv = 0, tw = 0;
        if (xSemaphoreTake(mutex, 10)) {
            tv = shared.tv;
            tw = shared.tw;
            xSemaphoreGive(mutex);
        }

        // Failsafe: Motoren stoppen wenn kein cmd_vel empfangen
        if (millis() - last_cmd_time > amr::timing::failsafe_timeout_ms) {
            tv = 0;
            tw = 0;
        }

        // Batterie-Unterspannung oder CAN-Notstopp: Motoren stoppen
        if (battery_motor_shutdown || can_cliff_stop || can_battery_stop) {
            tv = 0;
            tw = 0;
        }

        WheelTargets t = kinematics.computeMotorSpeeds(tv, tw);

        // Motor-Limit anwenden (0-100% → 0.0-1.0 Faktor)
        float motor_scale = hw_cmd.motor_limit_pct / 100.0f;
        t.left_rad_s *= motor_scale;
        t.right_rad_s *= motor_scale;

        // Hard-Stop: Bei Zielgeschwindigkeit Null Rampe umgehen
        if (fabsf(tv) < amr::pid::hard_stop_threshold &&
            fabsf(tw) < amr::pid::hard_stop_threshold) {
            last_sp_l = 0.0f;
            last_sp_r = 0.0f;
        } else {
            // Rampe (skaliert mit tatsaechlichem dt)
            float max_d = amr::pid::max_accel_rad_s2 * dt;
            if (t.left_rad_s > last_sp_l + max_d)
                last_sp_l += max_d;
            else if (t.left_rad_s < last_sp_l - max_d)
                last_sp_l -= max_d;
            else
                last_sp_l = t.left_rad_s;

            if (t.right_rad_s > last_sp_r + max_d)
                last_sp_r += max_d;
            else if (t.right_rad_s < last_sp_r - max_d)
                last_sp_r -= max_d;
            else
                last_sp_r = t.right_rad_s;
        }

        // Bei Zielgeschwindigkeit ~0: PID umgehen, Motoren direkt stoppen
        float pid_out_l = 0.0f, pid_out_r = 0.0f;
        if (fabsf(last_sp_l) < amr::pid::stillstand_threshold &&
            fabsf(last_sp_r) < amr::pid::stillstand_threshold) {
            hal.setMotors(0, 0);
            pid_l.reset();
            pid_r.reset();
        } else {
            pid_out_l = pid_l.compute(last_sp_l, ml_filt, dt);
            pid_out_r = pid_r.compute(last_sp_r, mr_filt, dt);
            hal.setMotors(pid_out_l, pid_out_r);
        }

        RobotState s = kinematics.updateOdometry(ml, mr, dt);

        if (xSemaphoreTake(mutex, 10)) {
            shared.ox = s.x;
            shared.oy = s.y;
            shared.oth = s.theta;
            shared.ov = (ml + mr) * amr::kinematics::wheel_radius / 2;
            shared.ow = (mr - ml) * amr::kinematics::wheel_radius / amr::kinematics::wheel_base;
            xSemaphoreGive(mutex);
        }

        // CAN-Empfang: Cliff + Battery-Shutdown vom Sensor-Node (Notstopp-Redundanzpfad)
        if (can_ok) {
            twai_message_t rx_msg;
            while (can.receiveMessage(rx_msg)) {
                if (rx_msg.identifier == amr::can::id_cliff_rx) {
                    can_cliff_stop = (rx_msg.data[0] == 0x01);
                }
                if (rx_msg.identifier == amr::can::id_battery_shutdown_rx) {
                    can_battery_stop = (rx_msg.data[0] == 0x01);
                }
            }
        }

        // CAN: Encoder-Feedback + Motor-PWM (10 Hz) + Odom (20 Hz) + Heartbeat (1 Hz)
        // Alle CAN-Sends in controlTask (Core 1), damit sie unabhaengig von
        // micro-ROS-Verbindungsstatus laufen (setup() blockiert bis Agent da).
        if (can_ok) {
            uint32_t now_ms = millis();

            // Encoder + Motor-PWM (10 Hz)
            static uint32_t last_can_ctrl = 0;
            if (now_ms - last_can_ctrl >= amr::can::encoder_can_period_ms) {
                last_can_ctrl = now_ms;
                can.sendEncoder(ml_filt, mr_filt);
                int16_t duty_l = static_cast<int16_t>(pid_out_l * amr::pwm::motor_max);
                int16_t duty_r = static_cast<int16_t>(pid_out_r * amr::pwm::motor_max);
                can.sendMotorPwm(duty_l, duty_r);
            }

            // Odom Position + Heading (20 Hz)
            static uint32_t last_can_odom = 0;
            if (now_ms - last_can_odom >= amr::timing::odom_publish_period_ms) {
                last_can_odom = now_ms;
                can.sendOdomPos(s.x, s.y);
                float v_lin = (ml + mr) * amr::kinematics::wheel_radius / 2;
                can.sendOdomHeading(s.theta, v_lin);
            }

            // Heartbeat (1 Hz)
            static uint32_t last_can_hb_ctrl = 0;
            if (now_ms - last_can_hb_ctrl >= amr::can::heartbeat_period_ms) {
                last_can_hb_ctrl = now_ms;
                bool c1_ok = true; // Core 1 laeuft offensichtlich
                bool fs = (now_ms - last_cmd_time > amr::timing::failsafe_timeout_ms);
                bool pid_act = (tv != 0 || tw != 0);
                can.sendHeartbeat(true, c1_ok, pid_act, battery_motor_shutdown || can_battery_stop,
                                  c1_ok, fs || can_cliff_stop);
            }
        }

        core1_heartbeat++;
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(amr::timing::control_loop_period_ms));
    }
}

/** /cmd_vel Subscriber-Callback: Speichert v/omega in SharedData, setzt Failsafe-Timer. */
void vel_cb(const void *m) {
    if (m == nullptr)
        return;
    const geometry_msgs__msg__Twist *msg = (const geometry_msgs__msg__Twist *)m;
    if (xSemaphoreTake(mutex, 10)) {
        shared.tv = msg->linear.x;
        shared.tw = msg->angular.z;
        xSemaphoreGive(mutex);
    }
    last_cmd_time = millis();
}

/** /hardware_cmd Subscriber-Callback: Motor-Limit, LED-PWM (RAM, kein I2C). */
void hardware_cmd_callback(const void *m) {
    if (m == nullptr)
        return;
    const geometry_msgs__msg__Point *msg = (const geometry_msgs__msg__Point *)m;
    hw_cmd.motor_limit_pct = std::clamp(static_cast<float>(msg->x), 0.0f, 100.0f);
    hw_cmd.led_pwm = std::clamp(static_cast<float>(msg->z), 0.0f, 255.0f);
    hw_cmd.update_pending = true;
}

/** /battery_shutdown Subscriber-Callback: Motoren stoppen bei Unterspannung (vom Sensor-Node). */
void battery_shutdown_callback(const void *m) {
    if (m == nullptr)
        return;
    const std_msgs__msg__Bool *msg = (const std_msgs__msg__Bool *)m;
    battery_motor_shutdown = msg->data;
}

/**
 * Initialisierung auf Core 0: Hardware (HAL), FreeRTOS-Task fuer Core 1,
 * micro-ROS (Agent-Verbindung, Node, 3 Subscriber, 1 Publisher),
 * Zeitsync, LED-Ramp-Test.
 *
 * Blockiert bis micro-ROS Agent erreichbar ist (langsames LED-Blinken).
 * Bei Init-Fehler: Endlosschleife mit schnellem Blinken.
 */
void setup() {
    Serial.begin(921600);
    Serial.setTxTimeoutMs(50);

    // Konfiguration der internen LED (Active Low)
    pinMode(amr::hal::pin_led_internal, OUTPUT);
    digitalWrite(amr::hal::pin_led_internal, HIGH); // Schalte interne LED aus

    hal.init();

    // CAN-Bus (TWAI) initialisieren — Fehlschlag nicht fatal
    can_ok = can.init();
    Serial.printf("[CAN] init %s (TX=%d, RX=%d)\n", can_ok ? "OK" : "FAILED", amr::hal::pin_can_tx,
                  amr::hal::pin_can_rx);
    // LED-Feedback: CAN FAILED = 5x schnelles Blinken, CAN OK = 1x kurz
    if (!can_ok) {
        for (int i = 0; i < 5; i++) {
            digitalWrite(amr::hal::pin_led_internal, LOW);
            delay(80);
            digitalWrite(amr::hal::pin_led_internal, HIGH);
            delay(80);
        }
    } else {
        digitalWrite(amr::hal::pin_led_internal, LOW);
        delay(200);
        digitalWrite(amr::hal::pin_led_internal, HIGH);
    }

    set_microros_serial_transports(Serial);

    mutex = xSemaphoreCreateMutex();
    xTaskCreatePinnedToCore(controlTask, "Ctrl", 10000, NULL, 1, NULL, 1);
    delay(2000);

    memset(&msg_odom, 0, sizeof(msg_odom));

    allocator = rcl_get_default_allocator();

    // Warten bis Agent erreichbar ist (Blinken der internen LED)
    while (rmw_uros_ping_agent(1000, 1) != RMW_RET_OK) {
        digitalWrite(amr::hal::pin_led_internal, LOW); // Ein
        delay(100);
        digitalWrite(amr::hal::pin_led_internal, HIGH); // Aus
        delay(900);
    }

    rcl_ret_t rc;
    bool init_ok = true;

    rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_node_init_default(&node, "esp32_bot", "", &support);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_init(&executor, &support.context, 3, &allocator);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_subscription_init_default(
        &sub_vel, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "cmd_vel");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_vel, &msg_vel, &vel_cb, ON_NEW_DATA);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_subscription_init_default(&sub_hardware, &node,
                                        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Point),
                                        "hardware_cmd");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_hardware, &msg_hardware,
                                        &hardware_cmd_callback, ON_NEW_DATA);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_subscription_init_default(&sub_battery_shutdown, &node,
                                        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Bool),
                                        "battery_shutdown");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_battery_shutdown, &msg_battery_shutdown,
                                        &battery_shutdown_callback, ON_NEW_DATA);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_publisher_init_default(&pub_odom, &node,
                                     ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry), "odom");
    if (rc != RCL_RET_OK)
        init_ok = false;

    if (!init_ok) {
        while (1) {
            digitalWrite(amr::hal::pin_led_internal, LOW); // Schnelles Blinken bei Init-Fehler
            delay(200);
            digitalWrite(amr::hal::pin_led_internal, HIGH);
            delay(200);
        }
    }

    rmw_uros_sync_session(1000);

    // LED-Ramp-Test: 0% → 100% → 0% (3s, verifiziert LEDC 10-bit + MOSFET auf Haupt-LED)
    for (uint32_t d = 0; d <= amr::pwm::led_max; d += 64) {
        ledcWrite(amr::pwm::led_channel, d);
        delay(100);
    }
    ledcWrite(amr::pwm::led_channel, amr::pwm::led_max);
    delay(500);
    for (int32_t d = amr::pwm::led_max; d >= 0; d -= 64) {
        ledcWrite(amr::pwm::led_channel, static_cast<uint32_t>(d));
        delay(100);
    }

    // Nach dem erfolgreichen Boot-Test Haupt-LED abschalten
    ledcWrite(amr::pwm::led_channel, 0);
}

/**
 * Hauptschleife auf Core 0 (~50 Hz durch spin_some + delay).
 *
 * Reihenfolge pro Zyklus: Inter-Core-Watchdog → spin_some (Callbacks) →
 * LED-Heartbeat/Override → Odom Publish (20 Hz).
 */
void loop() {
    // Inter-Core Watchdog: Core 1 Heartbeat pruefen
    static uint32_t last_hb = 0;
    static uint32_t hb_miss_count = 0;
    uint32_t hb = core1_heartbeat;
    if (hb == last_hb) {
        if (++hb_miss_count > amr::timing::watchdog_miss_limit) {
            hal.setMotors(0, 0);
        }
    } else {
        hb_miss_count = 0;
    }
    last_hb = hb;

    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
    delay(1);

    // LED-Heartbeat / Manual Override (nach spin_some)
    {
        static uint32_t hb_counter = 0;
        static bool hb_on = false;
        float led_override = hw_cmd.led_pwm;

        if (led_override > 0.5f) {
            // Manueller LED-Modus: Slider 0-255 auf 10-bit (0-1023) skalieren
            uint32_t duty = static_cast<uint32_t>(led_override *
                                                  (static_cast<float>(amr::pwm::led_max) / 255.0f));
            if (duty > amr::pwm::led_max)
                duty = amr::pwm::led_max;
            ledcWrite(amr::pwm::led_channel, duty);

            // Auto-Heartbeat auf interner LED deaktivieren, wenn Override aktiv
            digitalWrite(amr::hal::pin_led_internal, HIGH);
        } else {
            // Haupt-LED aus, Auto-Heartbeat auf der internen LED
            ledcWrite(amr::pwm::led_channel, 0);
            if (++hb_counter > 20) {
                hb_counter = 0;
                hb_on = !hb_on;
                digitalWrite(amr::hal::pin_led_internal, hb_on ? LOW : HIGH);
            }
        }
    }

    // Odom publish
    static unsigned long last = 0;
    if (millis() - last >= amr::timing::odom_publish_period_ms) {
        last = millis();
        float x = 0, y = 0, th = 0, v = 0, w = 0;
        if (xSemaphoreTake(mutex, 10)) {
            x = shared.ox;
            y = shared.oy;
            th = shared.oth;
            v = shared.ov;
            w = shared.ow;
            xSemaphoreGive(mutex);
        }

        int64_t t = rmw_uros_epoch_nanos();
        msg_odom.header.stamp.sec = (int32_t)(t / 1000000000LL);
        msg_odom.header.stamp.nanosec = (uint32_t)(t % 1000000000LL);
        msg_odom.header.frame_id.data = (char *)"odom";
        msg_odom.header.frame_id.size = 4;
        msg_odom.header.frame_id.capacity = 5;
        msg_odom.child_frame_id.data = (char *)"base_link";
        msg_odom.child_frame_id.size = 9;
        msg_odom.child_frame_id.capacity = 10;
        msg_odom.pose.pose.position.x = x;
        msg_odom.pose.pose.position.y = y;
        msg_odom.pose.pose.orientation.z = sin(th / 2);
        msg_odom.pose.pose.orientation.w = cos(th / 2);
        msg_odom.twist.twist.linear.x = v;
        msg_odom.twist.twist.angular.z = w;
        rcl_ret_t pub_rc = rcl_publish(&pub_odom, &msg_odom, NULL);
        if (pub_rc != RCL_RET_OK && hw_cmd.led_pwm < 0.5f) {
            digitalWrite(amr::hal::pin_led_internal, LOW); // Zeige Fehler auf interner LED
        }
        rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5));
    }
    // CAN-Sends (Odom, Heartbeat) laufen jetzt in controlTask (Core 1)
}
