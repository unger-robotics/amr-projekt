#include <Arduino.h>
#include "config.h"
#include <geometry_msgs/msg/twist.h>
#include <geometry_msgs/msg/point.h>
#include <micro_ros_platformio.h>
#include <nav_msgs/msg/odometry.h>
#include <sensor_msgs/msg/imu.h>
#include <sensor_msgs/msg/battery_state.h>
#include <rcl/rcl.h>
#include <rclc/executor.h>
#include <rclc/rclc.h>
#include <rmw_microros/rmw_microros.h>

#include "diff_drive_kinematics.hpp"
#include "pid_controller.hpp"
#include "robot_hal.hpp"
#include "mpu6050.hpp"
#include "ina260.hpp"
#include "pca9685.hpp"

// --- SETUP ---
RobotHAL hal;
DiffDriveKinematics kinematics(amr::kinematics::wheel_radius, amr::kinematics::wheel_base);
PidController pid_l(amr::pid::kp, amr::pid::ki, amr::pid::kd, amr::pid::output_min, amr::pid::output_max);
PidController pid_r(amr::pid::kp, amr::pid::ki, amr::pid::kd, amr::pid::output_min, amr::pid::output_max);
MPU6050 imu;
bool imu_ok = false;
INA260 ina260;
bool ina260_ok = false;
PCA9685 pca9685;
bool pca9685_ok = false;

struct SharedData {
    float tv = 0, tw = 0, ox = 0, oy = 0, oth = 0, ov = 0, ow = 0;
    float imu_ax = 0, imu_ay = 0, imu_az = 0;
    float imu_gx = 0, imu_gy = 0, imu_gz = 0;
    float imu_heading = 0;
    float bat_voltage = 0, bat_current = 0, bat_power = 0;
};
SharedData shared;
SemaphoreHandle_t mutex;

volatile uint32_t last_cmd_time = 0;
volatile uint32_t core1_heartbeat = 0;

rcl_publisher_t pub_odom;
rcl_publisher_t pub_imu;
rcl_publisher_t pub_battery;
rcl_subscription_t sub_vel;
rcl_subscription_t sub_servo;
rcl_subscription_t sub_hardware;
geometry_msgs__msg__Twist msg_vel;
geometry_msgs__msg__Point msg_servo;
geometry_msgs__msg__Point msg_hardware;
nav_msgs__msg__Odometry msg_odom;
sensor_msgs__msg__Imu msg_imu;
sensor_msgs__msg__BatteryState msg_bat;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

// Batterie-Unterspannungs-Flag (gesetzt in Core 0, gelesen in Core 1)
volatile bool battery_motor_shutdown = false;

// I2C Thread-Safety (Cross-Core Mutex)
SemaphoreHandle_t i2c_mutex;
uint32_t i2c_contention_errors = 0;

// Deferred Servo Command (Callback → RAM, loop() → I2C)
struct ServoCommand {
    volatile float pan;
    volatile float tilt;
    volatile bool update_pending;
};
ServoCommand servo_cmd = {90.0f, 90.0f, false};

// Deferred Hardware Command (Callback → RAM, loop() → I2C/PWM)
struct HardwareCommand {
    volatile float motor_limit_pct;   // 0-100
    volatile float servo_speed;       // 1-10 (Grad/Schritt)
    volatile float led_pwm;           // 0-255, 0 = auto heartbeat
    volatile bool update_pending;
};
HardwareCommand hw_cmd = {100.0f, 5.0f, 0.0f, false};

void controlTask(void *p) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    float last_sp_l = 0, last_sp_r = 0;
    float ml_filt = 0, mr_filt = 0;
    uint32_t last_us = micros();
    while (1) {
        uint32_t now_us = micros();
        float dt = (now_us - last_us) / 1000000.0f;
        last_us = now_us;
        if (dt < 0.001f) dt = 0.001f;
        if (dt > 0.1f) dt = 0.1f;

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

        // Batterie-Unterspannung: Motoren stoppen
        if (battery_motor_shutdown) {
            tv = 0;
            tw = 0;
        }

        WheelTargets t = kinematics.computeMotorSpeeds(tv, tw);

        // Motor-Limit anwenden (0-100% → 0.0-1.0 Faktor)
        float motor_scale = hw_cmd.motor_limit_pct / 100.0f;
        t.left_rad_s *= motor_scale;
        t.right_rad_s *= motor_scale;

        // Hard-Stop: Bei Zielgeschwindigkeit Null Rampe umgehen
        if (fabsf(tv) < amr::pid::hard_stop_threshold && fabsf(tw) < amr::pid::hard_stop_threshold) {
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
        if (fabsf(last_sp_l) < amr::pid::stillstand_threshold && fabsf(last_sp_r) < amr::pid::stillstand_threshold) {
            hal.setMotors(0, 0);
            pid_l.reset();
            pid_r.reset();
        } else {
            hal.setMotors(pid_l.compute(last_sp_l, ml_filt, dt),
                          pid_r.compute(last_sp_r, mr_filt, dt));
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
        // IMU lesen und Heading fusionieren (I2C mit Mutex geschuetzt)
        if (imu_ok) {
            float ax, ay, az, gx, gy, gz;
            bool imu_read_ok = false;
            if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
                imu_read_ok = imu.read(ax, ay, az, gx, gy, gz);
                xSemaphoreGive(i2c_mutex);
            } else {
                i2c_contention_errors++;
            }
            if (imu_read_ok) {
                float fused_heading = imu.updateHeading(s.theta, gz, dt);
                if (xSemaphoreTake(mutex, 10)) {
                    shared.imu_ax = ax; shared.imu_ay = ay; shared.imu_az = az;
                    shared.imu_gx = gx; shared.imu_gy = gy; shared.imu_gz = gz;
                    shared.imu_heading = fused_heading;
                    xSemaphoreGive(mutex);
                }
            }
        }
        core1_heartbeat++;
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(amr::timing::control_loop_period_ms));
    }
}

void vel_cb(const void *m) {
    if (m == nullptr) return;
    const geometry_msgs__msg__Twist *msg = (const geometry_msgs__msg__Twist *)m;
    if (xSemaphoreTake(mutex, 10)) {
        shared.tv = msg->linear.x;
        shared.tw = msg->angular.z;
        xSemaphoreGive(mutex);
    }
    last_cmd_time = millis();
}

void servo_cmd_callback(const void *m) {
    if (m == nullptr) return;
    const geometry_msgs__msg__Point *msg = (const geometry_msgs__msg__Point *)m;
    if (pca9685_ok) {
        float pan = static_cast<float>(msg->x);
        if (pan < amr::servo::angle_min_deg) pan = amr::servo::angle_min_deg;
        if (pan > amr::servo::angle_max_deg) pan = amr::servo::angle_max_deg;
        float tilt = static_cast<float>(msg->y);
        if (tilt < amr::servo::angle_min_deg) tilt = amr::servo::angle_min_deg;
        if (tilt > amr::servo::angle_max_deg) tilt = amr::servo::angle_max_deg;
        servo_cmd.pan = pan;
        servo_cmd.tilt = tilt;
        servo_cmd.update_pending = true;
    }
}

void hardware_cmd_callback(const void *m) {
    if (m == nullptr) return;
    const geometry_msgs__msg__Point *msg = (const geometry_msgs__msg__Point *)m;
    float motor = static_cast<float>(msg->x);
    if (motor < 0.0f) motor = 0.0f;
    if (motor > 100.0f) motor = 100.0f;
    float speed = static_cast<float>(msg->y);
    if (speed < 1.0f) speed = 1.0f;
    if (speed > 10.0f) speed = 10.0f;
    float led = static_cast<float>(msg->z);
    if (led < 0.0f) led = 0.0f;
    if (led > 255.0f) led = 255.0f;
    hw_cmd.motor_limit_pct = motor;
    hw_cmd.servo_speed = speed;
    hw_cmd.led_pwm = led;
    hw_cmd.update_pending = true;
}

// SOC-Schaetzung (lineare Interpolation aus Spannungskurve)
static float estimateSOC(float voltage) {
    if (voltage >= amr::battery::pack_charge_max_v) return 1.0f;
    if (voltage <= amr::battery::pack_cutoff_v) return 0.0f;
    return (voltage - amr::battery::pack_cutoff_v) /
           (amr::battery::pack_charge_max_v - amr::battery::pack_cutoff_v);
}

void setup() {
    Serial.begin(115200);
    Serial.setTxTimeoutMs(50);
    set_microros_serial_transports(Serial);
    hal.init();
    imu_ok = imu.init(PIN_I2C_SDA, PIN_I2C_SCL, amr::i2c::addr_mpu6050);
    if (imu_ok) {
        imu.calibrateGyro(amr::imu::calibration_samples);
    }

    // INA260 Leistungsmonitor
    ina260_ok = ina260.init();

    // PCA9685 Servo-Controller
    pca9685_ok = pca9685.init();
    if (pca9685_ok) {
        // Servos auf Mittelstellung (90 deg) bei Startup
        pca9685.setAngle(amr::servo::ch_pan, 90.0f);
        pca9685.setAngle(amr::servo::ch_tilt, 90.0f);
    }

    mutex = xSemaphoreCreateMutex();
    i2c_mutex = xSemaphoreCreateMutex();
    xTaskCreatePinnedToCore(controlTask, "Ctrl", 10000, NULL, 1, NULL, 1);
    delay(2000);

    memset(&msg_odom, 0, sizeof(msg_odom));
    memset(&msg_imu, 0, sizeof(msg_imu));
    memset(&msg_bat, 0, sizeof(msg_bat));

    allocator = rcl_get_default_allocator();

    // Warten bis Agent erreichbar ist
    while (rmw_uros_ping_agent(1000, 1) != RMW_RET_OK) {
        ledcWrite(amr::pwm::led_channel, 128);
        delay(100);
        ledcWrite(amr::pwm::led_channel, 0);
        delay(900);
    }

    rcl_ret_t rc;
    bool init_ok = true;

    rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_node_init_default(&node, "esp32_bot", "", &support);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_executor_init(&executor, &support.context, 3, &allocator);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_subscription_init_default(
        &sub_vel, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
        "cmd_vel");
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_vel, &msg_vel, &vel_cb,
                                        ON_NEW_DATA);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_subscription_init_default(
        &sub_servo, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Point),
        "servo_cmd");
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_servo, &msg_servo,
                                        &servo_cmd_callback, ON_NEW_DATA);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_subscription_init_default(
        &sub_hardware, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Point),
        "hardware_cmd");
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_hardware, &msg_hardware,
                                        &hardware_cmd_callback, ON_NEW_DATA);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_publisher_init_default(&pub_odom, &node,
                             ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry),
                             "odom");
    if (rc != RCL_RET_OK) init_ok = false;

    if (imu_ok) {
        rc = rclc_publisher_init_default(&pub_imu, &node,
            ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu), "imu");
        if (rc != RCL_RET_OK) init_ok = false;
    }

    if (ina260_ok) {
        rc = rclc_publisher_init_default(&pub_battery, &node,
            ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, BatteryState), "battery");
        if (rc != RCL_RET_OK) init_ok = false;
    }

    if (!init_ok) {
        while (1) {
            ledcWrite(amr::pwm::led_channel, 255);
            delay(200);
            ledcWrite(amr::pwm::led_channel, 0);
            delay(200);
        }
    }

    rmw_uros_sync_session(1000);

    // LED-Ramp-Test: 0% → 100% → 0% (3s, verifiziert LEDC 10-bit + MOSFET)
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
    // LED an = Setup erfolgreich
    ledcWrite(amr::pwm::led_channel, 64);
}

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

    // LED-Heartbeat / Manual Override (nach spin_some, damit Callback-Werte gelten)
    {
        static uint32_t hb_counter = 0;
        static bool hb_on = false;
        float led_override = hw_cmd.led_pwm;
        if (led_override > 0.5f) {
            // Manueller LED-Modus: Slider 0-255 auf 10-bit (0-1023) skalieren
            uint32_t duty = static_cast<uint32_t>(led_override * (static_cast<float>(amr::pwm::led_max) / 255.0f));
            if (duty > amr::pwm::led_max) duty = amr::pwm::led_max;
            ledcWrite(amr::pwm::led_channel, duty);
        } else {
            // Auto-Heartbeat
            if (++hb_counter > 20) {
                hb_counter = 0;
                hb_on = !hb_on;
                ledcWrite(amr::pwm::led_channel, hb_on ? 32 : 0);
            }
        }
    }

    // Deferred Servo I2C (nach spin_some, Core 0)
    if (pca9685_ok && servo_cmd.update_pending) {
        servo_cmd.update_pending = false;
        // Zielwinkel setzen (RAM-only, kein I2C)
        pca9685.setTargetAngle(amr::servo::ch_pan, servo_cmd.pan);
        pca9685.setTargetAngle(amr::servo::ch_tilt, servo_cmd.tilt);
    }

    // Servo-Rampenfahrt: Schrittweise zum Ziel (I2C, mit Mutex)
    if (pca9685_ok) {
        if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
            pca9685.updateRamp(amr::servo::ch_pan);
            pca9685.updateRamp(amr::servo::ch_tilt);
            xSemaphoreGive(i2c_mutex);
        } else {
            i2c_contention_errors++;
        }
    }

    // Deferred Hardware Command (Servo-Speed → RAM, kein I2C noetig)
    if (hw_cmd.update_pending) {
        hw_cmd.update_pending = false;
        // Servo-Speed: 1-10 → 0.5-5.0 deg/step
        pca9685.setRampSpeed(hw_cmd.servo_speed * 0.5f);
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
            ledcWrite(amr::pwm::led_channel, 255);
        }

        rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5));
    }

    // IMU publish
    if (imu_ok) {
        static unsigned long last_imu = 0;
        if (millis() - last_imu >= amr::timing::imu_publish_period_ms) {
            last_imu = millis();
            float iax = 0, iay = 0, iaz = 0, igx = 0, igy = 0, igz = 0, ih = 0;
            if (xSemaphoreTake(mutex, 10)) {
                iax = shared.imu_ax; iay = shared.imu_ay; iaz = shared.imu_az;
                igx = shared.imu_gx; igy = shared.imu_gy; igz = shared.imu_gz;
                ih = shared.imu_heading;
                xSemaphoreGive(mutex);
            }
            int64_t t_imu = rmw_uros_epoch_nanos();
            msg_imu.header.stamp.sec = (int32_t)(t_imu / 1000000000LL);
            msg_imu.header.stamp.nanosec = (uint32_t)(t_imu % 1000000000LL);
            msg_imu.header.frame_id.data = (char *)"base_link";
            msg_imu.header.frame_id.size = 9;
            msg_imu.header.frame_id.capacity = 10;
            msg_imu.linear_acceleration.x = iax;
            msg_imu.linear_acceleration.y = iay;
            msg_imu.linear_acceleration.z = iaz;
            msg_imu.angular_velocity.x = igx;
            msg_imu.angular_velocity.y = igy;
            msg_imu.angular_velocity.z = igz;
            msg_imu.orientation.z = sin(ih / 2);
            msg_imu.orientation.w = cos(ih / 2);
            msg_imu.orientation_covariance[0] = 0.01;
            msg_imu.orientation_covariance[4] = 0.01;
            msg_imu.orientation_covariance[8] = 0.01;
            msg_imu.angular_velocity_covariance[0] = 0.001;
            msg_imu.angular_velocity_covariance[4] = 0.001;
            msg_imu.angular_velocity_covariance[8] = 0.001;
            msg_imu.linear_acceleration_covariance[0] = 0.1;
            msg_imu.linear_acceleration_covariance[4] = 0.1;
            msg_imu.linear_acceleration_covariance[8] = 0.1;
            rcl_ret_t imu_rc = rcl_publish(&pub_imu, &msg_imu, NULL);
            if (imu_rc != RCL_RET_OK && hw_cmd.led_pwm < 0.5f) {
                ledcWrite(amr::pwm::led_channel, 255);
            }
        }
    }

    // Battery publish (INA260)
    if (ina260_ok) {
        static unsigned long last_bat = 0;
        if (millis() - last_bat >= amr::timing::battery_publish_period_ms) {
            last_bat = millis();
            float voltage = 0, current = 0, power = 0;
            bool bat_read_ok = false;
            if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
                bat_read_ok = ina260.read(voltage, current, power);
                xSemaphoreGive(i2c_mutex);
            } else {
                i2c_contention_errors++;
            }
            if (bat_read_ok) {
                // Batterie-Unterspannungsabschaltung
                if (voltage > 0.5f && voltage < amr::battery::threshold_motor_shutdown_v) {
                    battery_motor_shutdown = true;
                    if (pca9685_ok) {
                        if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
                            pca9685.allOff();
                            xSemaphoreGive(i2c_mutex);
                        } else {
                            i2c_contention_errors++;
                        }
                    }
                } else if (voltage > amr::battery::threshold_motor_shutdown_v + amr::battery::threshold_hysteresis_v) {
                    battery_motor_shutdown = false;
                }

                if (xSemaphoreTake(mutex, 10)) {
                    shared.bat_voltage = voltage;
                    shared.bat_current = current;
                    shared.bat_power = power;
                    xSemaphoreGive(mutex);
                }

                int64_t t_bat = rmw_uros_epoch_nanos();
                msg_bat.header.stamp.sec = (int32_t)(t_bat / 1000000000LL);
                msg_bat.header.stamp.nanosec = (uint32_t)(t_bat % 1000000000LL);
                msg_bat.header.frame_id.data = (char *)"base_link";
                msg_bat.header.frame_id.size = 9;
                msg_bat.header.frame_id.capacity = 10;
                msg_bat.voltage = voltage;
                msg_bat.current = current;
                msg_bat.percentage = estimateSOC(voltage);
                msg_bat.capacity = amr::battery::capacity_design_ah;
                msg_bat.design_capacity = amr::battery::capacity_design_ah;
                msg_bat.power_supply_technology = sensor_msgs__msg__BatteryState__POWER_SUPPLY_TECHNOLOGY_LION;
                msg_bat.present = true;
                rcl_ret_t bat_rc = rcl_publish(&pub_battery, &msg_bat, NULL);
                if (bat_rc != RCL_RET_OK && hw_cmd.led_pwm < 0.5f) {
                    ledcWrite(amr::pwm::led_channel, 255);
                }
            }
        }
    }
}
