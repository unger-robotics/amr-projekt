#include <Arduino.h>
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
DiffDriveKinematics kinematics(0.032,
                               0.145); // <-- HIER DEINE WERTE (Radius, Spur)
PidController pid_l(1.5, 0.5, 0.0, -1.0, 1.0);
PidController pid_r(1.5, 0.5, 0.0, -1.0, 1.0);

struct SharedData {
    float tv = 0, tw = 0, ox = 0, oy = 0, oth = 0, ov = 0, ow = 0;
};
SharedData shared;
SemaphoreHandle_t mutex;

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
        long tl, tr;
        hal.readEncoders(tl, tr);
        static long ptl = 0, ptr = 0;
        float ml =
            ((tl - ptl) / 1440.0) * 2 * PI / 0.02; // 1440 Ticks/Rev anpassen!
        float mr = ((tr - ptr) / 1440.0) * 2 * PI / 0.02;
        ptl = tl;
        ptr = tr;

        float tv, tw;
        if (xSemaphoreTake(mutex, 10)) {
            tv = shared.tv;
            tw = shared.tw;
            xSemaphoreGive(mutex);
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
            shared.ov = (ml + mr) * 0.032 / 2;
            shared.ow = (mr - ml) * 0.032 / 0.145;
            xSemaphoreGive(mutex);
        }
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(20));
    }
}

void vel_cb(const void *m) {
    const geometry_msgs__msg__Twist *msg = (const geometry_msgs__msg__Twist *)m;
    if (xSemaphoreTake(mutex, 10)) {
        shared.tv = msg->linear.x;
        shared.tw = msg->angular.z;
        xSemaphoreGive(mutex);
    }
}

void setup() {
    Serial.begin(115200);
    set_microros_serial_transports(Serial);
    hal.init();
    mutex = xSemaphoreCreateMutex();
    xTaskCreatePinnedToCore(controlTask, "Ctrl", 10000, NULL, 1, NULL, 1);
    delay(2000);

    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "esp32_bot", "", &support);
    rclc_executor_init(&executor, &support.context, 1, &allocator);
    rclc_subscription_init_default(
        &sub_vel, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
        "cmd_vel");
    rclc_executor_add_subscription(&executor, &sub_vel, &msg_vel, &vel_cb,
                                   ON_NEW_DATA);

    rmw_qos_profile_t qos = rmw_qos_profile_sensor_data;
    rclc_publisher_init(&pub_odom, &node,
                        ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry),
                        "odom", &qos);
    rmw_uros_sync_session(1000);
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
    static unsigned long last = 0;
    if (millis() - last > 50) {
        float x, y, th, v, w;
        if (xSemaphoreTake(mutex, 10)) {
            x = shared.ox;
            y = shared.oy;
            th = shared.oth;
            v = shared.ov;
            w = shared.ow;
            xSemaphoreGive(mutex);
        }

        int64_t t = rmw_uros_epoch_nanos();
        msg_odom.header.stamp.sec = t / 1e9;
        msg_odom.header.stamp.nanosec = t % 1000000000;
        msg_odom.header.frame_id.data = (char *)"odom";
        msg_odom.header.frame_id.size = 4;
        msg_odom.child_frame_id.data = (char *)"base_link";
        msg_odom.child_frame_id.size = 9;
        msg_odom.pose.pose.position.x = x;
        msg_odom.pose.pose.position.y = y;
        msg_odom.pose.pose.orientation.z = sin(th / 2);
        msg_odom.pose.pose.orientation.w = cos(th / 2);
        msg_odom.twist.twist.linear.x = v;
        msg_odom.twist.twist.angular.z = w;
        rcl_publish(&pub_odom, &msg_odom, NULL);
        last = millis();
    }
}
