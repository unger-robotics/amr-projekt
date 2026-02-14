#include <Arduino.h>
#include "config.h"
#include <geometry_msgs/msg/twist.h>
#include <micro_ros_platformio.h>
#include <nav_msgs/msg/odometry.h>
#include <rcl/rcl.h>
#include <rclc/executor.h>
#include <rclc/rclc.h>
#include <rmw_microros/rmw_microros.h>

#include "diff_drive_kinematics.hpp"
#include "pid_controller.hpp"
#include "robot_hal.hpp"

// --- SETUP ---
const float MAX_ACCEL = 5.0; // rad/s^2 Rampe
RobotHAL hal;
DiffDriveKinematics kinematics(WHEEL_RADIUS, WHEEL_BASE);
PidController pid_l(1.5, 0.5, 0.0, -1.0, 1.0);
PidController pid_r(1.5, 0.5, 0.0, -1.0, 1.0);

struct SharedData {
    float tv = 0, tw = 0, ox = 0, oy = 0, oth = 0, ov = 0, ow = 0;
};
SharedData shared;
SemaphoreHandle_t mutex;

volatile uint32_t last_cmd_time = 0;
volatile uint32_t core1_heartbeat = 0;

rcl_publisher_t pub_odom;
rcl_subscription_t sub_vel;
geometry_msgs__msg__Twist msg_vel;
nav_msgs__msg__Odometry msg_odom;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

void controlTask(void *p) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    float last_sp_l = 0, last_sp_r = 0;
    while (1) {
        int32_t tl, tr;
        hal.readEncoders(tl, tr);
        static int32_t ptl = 0, ptr = 0;
        float ml =
            (static_cast<float>(tl - ptl) / TICKS_PER_REV_LEFT) * 2 * PI / 0.02;
        float mr =
            (static_cast<float>(tr - ptr) / TICKS_PER_REV_RIGHT) * 2 * PI / 0.02;
        ptl = tl;
        ptr = tr;

        float tv, tw;
        if (xSemaphoreTake(mutex, 10)) {
            tv = shared.tv;
            tw = shared.tw;
            xSemaphoreGive(mutex);
        }

        // Failsafe: Motoren stoppen wenn kein cmd_vel empfangen
        if (millis() - last_cmd_time > FAILSAFE_TIMEOUT_MS) {
            tv = 0;
            tw = 0;
        }

        WheelTargets t = kinematics.computeMotorSpeeds(tv, tw);

        // Rampe
        float max_d = MAX_ACCEL * 0.02;
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

        hal.setMotors(pid_l.compute(last_sp_l, ml, 0.02),
                      pid_r.compute(last_sp_r, mr, 0.02));
        RobotState s = kinematics.updateOdometry(ml, mr, 0.02);

        if (xSemaphoreTake(mutex, 10)) {
            shared.ox = s.x;
            shared.oy = s.y;
            shared.oth = s.theta;
            shared.ov = (ml + mr) * WHEEL_RADIUS / 2;
            shared.ow = (mr - ml) * WHEEL_RADIUS / WHEEL_BASE;
            xSemaphoreGive(mutex);
        }
        core1_heartbeat++;
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(CONTROL_LOOP_PERIOD_MS));
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

void setup() {
    Serial.begin(115200);
    Serial.setTxTimeoutMs(50);  // USB CDC Write-Timeout begrenzen
    set_microros_serial_transports(Serial);
    hal.init();
    mutex = xSemaphoreCreateMutex();
    xTaskCreatePinnedToCore(controlTask, "Ctrl", 10000, NULL, 1, NULL, 1);
    delay(2000);

    // Odom-Nachricht komplett nullen (Kovarianz-Arrays etc.)
    memset(&msg_odom, 0, sizeof(msg_odom));

    allocator = rcl_get_default_allocator();

    // Warten bis Agent erreichbar ist (blockiert bis Verbindung steht)
    while (rmw_uros_ping_agent(1000, 1) != RMW_RET_OK) {
        // LED kurz blinken waehrend Warten auf Agent
        ledcWrite(LED_PWM_CHANNEL, 128);
        delay(100);
        ledcWrite(LED_PWM_CHANNEL, 0);
        delay(900);
    }

    rcl_ret_t rc;
    bool init_ok = true;

    rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_node_init_default(&node, "esp32_bot", "", &support);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_executor_init(&executor, &support.context, 1, &allocator);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_subscription_init_default(
        &sub_vel, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
        "cmd_vel");
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_vel, &msg_vel, &vel_cb,
                                        ON_NEW_DATA);
    if (rc != RCL_RET_OK) init_ok = false;

    rc = rclc_publisher_init_default(&pub_odom, &node,
                             ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry),
                             "odom");
    if (rc != RCL_RET_OK) init_ok = false;

    if (!init_ok) {
        // LED-Blinken als Fehlersignal
        while (1) {
            ledcWrite(LED_PWM_CHANNEL, 255);
            delay(200);
            ledcWrite(LED_PWM_CHANNEL, 0);
            delay(200);
        }
    }

    rmw_uros_sync_session(1000);

    // LED an = Setup erfolgreich
    ledcWrite(LED_PWM_CHANNEL, 64);
}

void loop() {
    // Inter-Core Watchdog: Core 1 Heartbeat pruefen
    static uint32_t last_hb = 0;
    static uint32_t hb_miss_count = 0;
    uint32_t hb = core1_heartbeat;
    if (hb == last_hb) {
        if (++hb_miss_count > 50) {  // ~50 loop() Zyklen ohne Heartbeat
            hal.setMotors(0, 0);      // Notfall-Stopp
        }
    } else {
        hb_miss_count = 0;
    }
    last_hb = hb;

    // LED-Heartbeat: loop() laeuft (toggle alle ~1s)
    static uint32_t led_counter = 0;
    if (++led_counter > 20) {
        led_counter = 0;
        static bool led_on = false;
        led_on = !led_on;
        ledcWrite(LED_PWM_CHANNEL, led_on ? 32 : 0);
    }

    // Executor mit genuegend Zeit fuer Buffer-Flush
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
    delay(1);  // USB-CDC-Flush und Watchdog-Feed ermoeglichen

    static unsigned long last = 0;
    if (millis() - last >= ODOM_PUBLISH_PERIOD_MS) {
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
        if (pub_rc != RCL_RET_OK) {
            // LED schnell blinken bei Publish-Fehler
            ledcWrite(LED_PWM_CHANNEL, 255);
        }

        // Buffer nach Publish flushen
        rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5));
    }
}
