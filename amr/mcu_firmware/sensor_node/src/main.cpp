/**
 * @file main.cpp
 * @brief Hauptprogramm fuer den AMR Sensor-Node (ESP32-S3 #2)
 * @version 2.0.0
 * @date 2026-03-04
 *
 * Dual-Core-Architektur fuer Sensorik + I2C-Geraete (IMU, Batterie, Servo):
 *
 * - Core 1 (FreeRTOS Task "Sensors", 10 ms Basistakt): Ultraschall-Messung
 *   (10 Hz, pulseIn blockiert bis 25 ms), Cliff-Erkennung (20 Hz, digitalRead),
 *   IMU-Read (50 Hz, I2C mit i2c_mutex).
 * - Core 0 (Arduino loop): micro-ROS Executor (2 Publisher + 3 Subscriber +
 *   IMU/Battery Publisher), Deferred Servo I2C (Rampe), LED-Heartbeat,
 *   Inter-Core-Watchdog, CAN-Bus Dual-Path (TWAI, parallel zu micro-ROS).
 *
 * Thread-Safety: `mutex` schuetzt SharedSensorData zwischen Cores,
 * `i2c_mutex` (5 ms Timeout) arbitriert alle I2C-Zugriffe — Arduino Wire
 * ist NICHT thread-safe. Kein I2C in Subscriber-Callbacks (Deferred-Pattern).
 *
 * Topics: /range/front (10 Hz), /cliff (20 Hz),
 *         /imu (50 Hz), /battery (2 Hz), /battery_shutdown (2 Hz),
 *         /servo_cmd (Sub), /hardware_cmd (Sub), /odom (Sub)
 */
#include <Arduino.h>
#include <Wire.h>
#include "config_sensors.h"
#include "range_sensor.hpp"
#include "cliff_sensor.hpp"
#include "mpu6050.hpp"
#include "ina260.hpp"
#include "pca9685.hpp"
#include "twai_can.hpp"
#include <algorithm>
#include <cmath>
#include <micro_ros_platformio.h>
#include <sensor_msgs/msg/range.h>
#include <sensor_msgs/msg/imu.h>
#include <sensor_msgs/msg/battery_state.h>
#include <std_msgs/msg/bool.h>
#include <geometry_msgs/msg/point.h>
#include <nav_msgs/msg/odometry.h>
#include <rcl/rcl.h>
#include <rclc/executor.h>
#include <rclc/rclc.h>
#include <rmw_microros/rmw_microros.h>

// --- Namespace-Aliase ---
using amr::drivers::INA260;
using amr::drivers::MPU6050;
using amr::drivers::PCA9685;
using amr::drivers::TwaiCan;
using amr::hardware::CliffSensor;
using amr::hardware::RangeSensor;

// --- Sensor-Objekte instanziieren ---
RangeSensor sonar(amr::hal::pin_us_trig, amr::hal::pin_us_echo);
CliffSensor cliff_sensor(amr::hal::pin_ir_cliff);

// --- I2C-Geraete ---
MPU6050 imu;
bool imu_ok = false;
INA260 ina260;
bool ina260_ok = false;
PCA9685 pca9685;
bool pca9685_ok = false;

// --- CAN-Bus (TWAI) ---
TwaiCan can;
bool can_ok = false;

// --- I2C Thread-Safety (Cross-Core Mutex) ---
SemaphoreHandle_t i2c_mutex;
uint32_t i2c_contention_errors = 0;

// --- Batterie-Unterspannungs-Flag ---
volatile bool battery_motor_shutdown = false;

/** Mutex-geschuetzter Datenaustausch zwischen Core 0 und Core 1.
 *  Core 1 schreibt: Ultraschall-Distanz, Cliff-Status, IMU-Daten.
 *  Core 0 liest: Werte fuer micro-ROS Publish. */
struct SharedSensorData {
    float distance_m = 0.0f;
    bool cliff_detected = false;
    float imu_ax = 0, imu_ay = 0, imu_az = 0;
    float imu_gx = 0, imu_gy = 0, imu_gz = 0;
    float imu_heading = 0;
    float encoder_heading = 0;
};
SharedSensorData shared;
SemaphoreHandle_t mutex;
volatile uint32_t core1_heartbeat = 0;

/** Deferred Servo: Callback schreibt Zielwinkel (RAM), loop() fuehrt I2C aus.
 *  Noetig weil Wire-Operationen in rclc_executor_spin_some() still fehlschlagen. */
struct ServoCommand {
    volatile float pan = 90.0f;
    volatile float tilt = 90.0f;
    volatile bool update_pending = false;
};
ServoCommand servo_cmd;

/** Deferred Hardware: Callback schreibt Werte (RAM), loop() wendet sie an. */
struct HardwareCommand {
    volatile float servo_speed = 5.0f;
    volatile bool update_pending = false;
};
HardwareCommand hw_cmd;

// --- micro-ROS Variablen ---
rcl_publisher_t pub_range;
rcl_publisher_t pub_cliff;
rcl_publisher_t pub_imu;
rcl_publisher_t pub_battery;
rcl_publisher_t pub_battery_shutdown;
rcl_subscription_t sub_servo;
rcl_subscription_t sub_hardware;
rcl_subscription_t sub_odom;
sensor_msgs__msg__Range msg_range;
std_msgs__msg__Bool msg_cliff;
sensor_msgs__msg__Imu msg_imu;
sensor_msgs__msg__BatteryState msg_bat;
std_msgs__msg__Bool msg_bat_shutdown;
geometry_msgs__msg__Point msg_servo_in;
geometry_msgs__msg__Point msg_hardware_in;
nav_msgs__msg__Odometry msg_odom_in;

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

/**
 * SOC-Schaetzung per linearer Interpolation zwischen Cutoff- und Ladeschlussspannung.
 * @param voltage Packspannung [V] (3S, 7.95..12.60 V)
 * @return State of Charge [0.0..1.0]
 */
static float estimateSOC(float voltage) {
    if (voltage >= amr::battery::pack_charge_max_v)
        return 1.0f;
    if (voltage <= amr::battery::pack_cutoff_v)
        return 0.0f;
    return (voltage - amr::battery::pack_cutoff_v) /
           (amr::battery::pack_charge_max_v - amr::battery::pack_cutoff_v);
}

// --- Subscriber-Callbacks (Deferred-Pattern: RAM-only, kein I2C) ---

/** /servo_cmd Subscriber-Callback: Speichert Pan/Tilt in ServoCommand (RAM, kein I2C). */
void servo_cmd_callback(const void *m) {
    if (m == nullptr)
        return;
    const geometry_msgs__msg__Point *msg = (const geometry_msgs__msg__Point *)m;
    if (pca9685_ok) {
        servo_cmd.pan = std::clamp(static_cast<float>(msg->x), amr::servo::angle_min_deg,
                                   amr::servo::angle_max_deg);
        servo_cmd.tilt = std::clamp(static_cast<float>(msg->y), amr::servo::angle_min_deg,
                                    amr::servo::angle_max_deg);
        servo_cmd.update_pending = true;
    }
}

/** /hardware_cmd Subscriber-Callback: Servo-Speed (RAM, kein I2C). */
void hardware_cmd_callback(const void *m) {
    if (m == nullptr)
        return;
    const geometry_msgs__msg__Point *msg = (const geometry_msgs__msg__Point *)m;
    hw_cmd.servo_speed = std::clamp(static_cast<float>(msg->y), 1.0f, 10.0f);
    hw_cmd.update_pending = true;
}

/** /odom Subscriber-Callback: Extrahiert Encoder-Heading fuer Komplementaerfilter. */
void odom_callback(const void *m) {
    if (m == nullptr)
        return;
    const nav_msgs__msg__Odometry *msg = (const nav_msgs__msg__Odometry *)m;
    float qz = static_cast<float>(msg->pose.pose.orientation.z);
    float qw = static_cast<float>(msg->pose.pose.orientation.w);
    float yaw = 2.0f * atan2f(qz, qw);
    if (xSemaphoreTake(mutex, pdMS_TO_TICKS(5))) {
        shared.encoder_heading = yaw;
        xSemaphoreGive(mutex);
    }
}

/**
 * Sensorerfassung auf Core 1 (10 ms Basistakt via vTaskDelayUntil).
 *
 * Cliff-Sensor (20 Hz): digitalRead, nicht-blockierend (~1 us).
 * Ultraschall (10 Hz): pulseIn blockiert bis zu 25 ms (Timeout aus Config).
 * IMU (50 Hz): I2C-Read mit i2c_mutex, Komplementaerfilter-Fusion.
 *
 * Hinweis: pulseIn-Blockierung kann den 10 ms Basistakt ueberschreiten.
 * vTaskDelayUntil kompensiert dies automatisch (naechster Tick sofort).
 * Die millis()-basierten Rate-Checks stellen die Publish-Raten sicher.
 */
void sensorTask(void *p) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    uint32_t last_us_time = 0;
    uint32_t last_cliff_time = 0;
    uint32_t last_imu_time = 0;

    while (1) {
        uint32_t now = millis();

        // 1. Infrarot Cliff-Sensor auslesen
        if (now - last_cliff_time >= amr::timing::cliff_publish_period_ms) {
            last_cliff_time = now;
            bool cliff = cliff_sensor.isCliffDetected();

            if (xSemaphoreTake(mutex, pdMS_TO_TICKS(5))) {
                shared.cliff_detected = cliff;
                xSemaphoreGive(mutex);
            }
            if (can_ok)
                can.sendCliff(cliff);
        }

        // 2. Ultraschall HC-SR04 auslesen
        if (now - last_us_time >= amr::timing::us_publish_period_ms) {
            last_us_time = now;
            float dist =
                sonar.readDistance(amr::timing::us_timeout_us, amr::sensor::us_to_meters_factor,
                                   amr::sensor::us_max_range_m);

            if (xSemaphoreTake(mutex, pdMS_TO_TICKS(5))) {
                shared.distance_m = dist;
                xSemaphoreGive(mutex);
            }
            if (can_ok)
                can.sendRange(dist);
        }

        // 3. IMU lesen (50 Hz, I2C mit Mutex)
        if (imu_ok && (now - last_imu_time >= amr::timing::imu_sample_period_ms)) {
            last_imu_time = now;
            float ax, ay, az, gx, gy, gz;
            bool imu_read_ok = false;
            if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
                imu_read_ok = imu.read(ax, ay, az, gx, gy, gz);
                xSemaphoreGive(i2c_mutex);
            } else {
                i2c_contention_errors++;
            }
            if (imu_read_ok) {
                float enc_h = 0;
                if (xSemaphoreTake(mutex, pdMS_TO_TICKS(2))) {
                    enc_h = shared.encoder_heading;
                    xSemaphoreGive(mutex);
                }
                float fused =
                    imu.updateHeading(enc_h, gz, amr::timing::imu_sample_period_ms / 1000.0f);
                if (xSemaphoreTake(mutex, pdMS_TO_TICKS(5))) {
                    shared.imu_ax = ax;
                    shared.imu_ay = ay;
                    shared.imu_az = az;
                    shared.imu_gx = gx;
                    shared.imu_gy = gy;
                    shared.imu_gz = gz;
                    shared.imu_heading = fused;
                    xSemaphoreGive(mutex);
                }
                if (can_ok) {
                    can.sendImuAccel(ax, ay, az, gz);
                    can.sendImuHeading(fused);
                }
            }
        }

        // 4. Battery lesen + CAN senden (2 Hz, I2C mit Mutex)
        if (ina260_ok && can_ok) {
            static uint32_t last_bat_can = 0;
            if (now - last_bat_can >= amr::timing::battery_publish_period_ms) {
                last_bat_can = now;
                float voltage = 0, current = 0, power = 0;
                if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
                    if (ina260.read(voltage, current, power)) {
                        can.sendBattery(voltage, current, power);
                    }
                    xSemaphoreGive(i2c_mutex);
                }
            }
        }

        // CAN Heartbeat (1 Hz, in sensorTask damit unabhaengig von micro-ROS)
        if (can_ok) {
            static uint32_t last_can_hb_task = 0;
            if (now - last_can_hb_task >= amr::can::heartbeat_period_ms) {
                last_can_hb_task = now;
                bool core1_ok_flag = true; // Core 1 laeuft offensichtlich
                can.sendHeartbeat(imu_ok, ina260_ok, pca9685_ok, battery_motor_shutdown,
                                  core1_ok_flag);
            }
        }

        core1_heartbeat++;
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(10));
    }
}

/**
 * Initialisierung auf Core 0: GPIO-Sensoren (HC-SR04, MH-B), I2C-Geraete
 * (MPU6050, INA260, PCA9685), FreeRTOS-Task fuer Core 1, micro-ROS
 * (Agent-Verbindung, Node, 5 Publisher, 3 Subscriber), Zeitsync,
 * Range-Message statische Felder.
 *
 * Blockiert bis micro-ROS Agent erreichbar ist (langsames LED-Blinken).
 * Bei Init-Fehler: Endlosschleife mit schnellem Blinken.
 */
void setup() {
    Serial.begin(115200);
    Serial.setTxTimeoutMs(50);
    set_microros_serial_transports(Serial);

    // Interne LED als Statusanzeige
    pinMode(amr::hal::pin_led_internal, OUTPUT);
    digitalWrite(amr::hal::pin_led_internal, HIGH);

    // GPIO-Sensoren initialisieren
    sonar.init();
    cliff_sensor.init();

    // I2C-Bus explizit initialisieren (fuer alle I2C-Geraete)
    Wire.begin(amr::hal::pin_i2c_sda, amr::hal::pin_i2c_scl);
    Wire.setClock(amr::i2c::master_freq_hz);

    // I2C-Geraete initialisieren
    imu_ok = imu.init(amr::hal::pin_i2c_sda, amr::hal::pin_i2c_scl, amr::i2c::addr_mpu6050);
    if (imu_ok) {
        imu.calibrateGyro(amr::imu::calibration_samples);
    }

    ina260_ok = ina260.init();

    pca9685_ok = pca9685.init();
    if (pca9685_ok) {
        pca9685.setAngle(amr::servo::ch_pan, 90.0f);
        pca9685.setAngle(amr::servo::ch_tilt, 90.0f);
    }

    // CAN-Bus (TWAI) initialisieren — fehlschlag nicht fatal
    can_ok = can.init();

    // Multithreading vorbereiten
    mutex = xSemaphoreCreateMutex();
    i2c_mutex = xSemaphoreCreateMutex();
    xTaskCreatePinnedToCore(sensorTask, "Sensors", 8192, NULL, 1, NULL, 1);
    delay(1000);

    memset(&msg_range, 0, sizeof(msg_range));
    memset(&msg_cliff, 0, sizeof(msg_cliff));
    memset(&msg_imu, 0, sizeof(msg_imu));
    memset(&msg_bat, 0, sizeof(msg_bat));
    memset(&msg_bat_shutdown, 0, sizeof(msg_bat_shutdown));

    allocator = rcl_get_default_allocator();

    // Warten auf Host-Verbindung
    while (rmw_uros_ping_agent(1000, 1) != RMW_RET_OK) {
        digitalWrite(amr::hal::pin_led_internal, LOW);
        delay(100);
        digitalWrite(amr::hal::pin_led_internal, HIGH);
        delay(900);
    }

    rcl_ret_t rc;
    bool init_ok = true;

    rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_node_init_default(&node, "esp32_sensors", "", &support);
    if (rc != RCL_RET_OK)
        init_ok = false;

    // Executor: 1 (bestehend, fuer spin_some) + 3 Subscriber = 4 Handles
    rc = rclc_executor_init(&executor, &support.context, 4, &allocator);
    if (rc != RCL_RET_OK)
        init_ok = false;

    // --- Publisher einrichten ---
    rc = rclc_publisher_init_default(
        &pub_range, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Range), "range/front");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_publisher_init_default(&pub_cliff, &node,
                                     ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Bool), "cliff");
    if (rc != RCL_RET_OK)
        init_ok = false;

    if (imu_ok) {
        rc = rclc_publisher_init_default(&pub_imu, &node,
                                         ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu), "imu");
        if (rc != RCL_RET_OK)
            init_ok = false;
    }

    if (ina260_ok) {
        rc = rclc_publisher_init_default(
            &pub_battery, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, BatteryState),
            "battery");
        if (rc != RCL_RET_OK)
            init_ok = false;

        rc = rclc_publisher_init_default(&pub_battery_shutdown, &node,
                                         ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Bool),
                                         "battery_shutdown");
        if (rc != RCL_RET_OK)
            init_ok = false;
    }

    // --- Subscriber einrichten ---
    rc = rclc_subscription_init_default(
        &sub_servo, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Point), "servo_cmd");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_servo, &msg_servo_in, &servo_cmd_callback,
                                        ON_NEW_DATA);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_subscription_init_default(&sub_hardware, &node,
                                        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Point),
                                        "hardware_cmd");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_hardware, &msg_hardware_in,
                                        &hardware_cmd_callback, ON_NEW_DATA);
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_subscription_init_default(
        &sub_odom, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry), "odom");
    if (rc != RCL_RET_OK)
        init_ok = false;

    rc = rclc_executor_add_subscription(&executor, &sub_odom, &msg_odom_in, &odom_callback,
                                        ON_NEW_DATA);
    if (rc != RCL_RET_OK)
        init_ok = false;

    if (!init_ok) {
        while (1) {
            digitalWrite(amr::hal::pin_led_internal, LOW);
            delay(200);
            digitalWrite(amr::hal::pin_led_internal, HIGH);
            delay(200);
        }
    }

    rmw_uros_sync_session(1000);

    // Statische Felder der Range-Message initialisieren
    msg_range.header.frame_id.data = (char *)"ultrasonic_link";
    msg_range.header.frame_id.size = 15;
    msg_range.header.frame_id.capacity = 16;
    msg_range.radiation_type = sensor_msgs__msg__Range__ULTRASOUND;
    msg_range.field_of_view = 0.26f;
    msg_range.min_range = amr::sensor::us_min_range_m;
    msg_range.max_range = amr::sensor::us_max_range_m;
}

/**
 * Hauptschleife auf Core 0 (~50 Hz durch spin_some + delay).
 *
 * Reihenfolge pro Zyklus: Inter-Core-Watchdog → spin_some (Callbacks) →
 * LED-Heartbeat → Deferred Servo I2C (Rampe) → Deferred Hardware →
 * Cliff Publish (20 Hz) → Range Publish (10 Hz) →
 * IMU Publish (50 Hz) → Battery Publish (2 Hz).
 *
 * Batterie-Unterspannung (< 9.5 V): Servos abschalten (PCA9685 allOff()),
 * publiziere battery_shutdown=true. Wiederaktivierung bei 9.8 V (Hysterese).
 */
void loop() {
    // Inter-Core Watchdog: Core 1 Heartbeat pruefen
    static uint32_t last_hb = 0;
    static uint32_t hb_miss_count = 0;
    uint32_t hb = core1_heartbeat;
    if (hb == last_hb) {
        if (++hb_miss_count > amr::timing::watchdog_miss_limit) {
            // Core 1 blockiert — LED Dauer-An als Warnung
            digitalWrite(amr::hal::pin_led_internal, LOW);
        }
    } else {
        hb_miss_count = 0;
    }
    last_hb = hb;

    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
    delay(1);

    // LED-Heartbeat
    static uint32_t hb_counter = 0;
    static bool hb_on = false;
    if (++hb_counter > 20) {
        hb_counter = 0;
        hb_on = !hb_on;
        digitalWrite(amr::hal::pin_led_internal, hb_on ? LOW : HIGH);
    }

    // --- Deferred Servo I2C (nach spin_some, Core 0) ---
    if (pca9685_ok && servo_cmd.update_pending) {
        servo_cmd.update_pending = false;
        pca9685.setTargetAngle(amr::servo::ch_pan, servo_cmd.pan);
        pca9685.setTargetAngle(amr::servo::ch_tilt, servo_cmd.tilt);
    }

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
        if (pca9685_ok)
            pca9685.setRampSpeed(hw_cmd.servo_speed * 0.5f);
    }

    // --- 1. Cliff publizieren (20 Hz) ---
    static unsigned long last_pub_cliff = 0;
    if (millis() - last_pub_cliff >= amr::timing::cliff_publish_period_ms) {
        last_pub_cliff = millis();
        bool cliff_state = false;

        if (xSemaphoreTake(mutex, 10)) {
            cliff_state = shared.cliff_detected;
            xSemaphoreGive(mutex);
        }

        msg_cliff.data = cliff_state;
        rcl_ret_t rc = rcl_publish(&pub_cliff, &msg_cliff, NULL);
        if (rc != RCL_RET_OK) {
            digitalWrite(amr::hal::pin_led_internal, LOW);
        }
        // CAN-Send laeuft in sensorTask (Core 1)
    }

    // --- 2. Ultraschall publizieren (10 Hz) ---
    static unsigned long last_pub_us = 0;
    if (millis() - last_pub_us >= amr::timing::us_publish_period_ms) {
        last_pub_us = millis();
        float dist = 0.0f;

        if (xSemaphoreTake(mutex, 10)) {
            dist = shared.distance_m;
            xSemaphoreGive(mutex);
        }

        int64_t t = rmw_uros_epoch_nanos();
        msg_range.header.stamp.sec = (int32_t)(t / 1000000000LL);
        msg_range.header.stamp.nanosec = (uint32_t)(t % 1000000000LL);
        msg_range.range = dist;

        rcl_ret_t rc = rcl_publish(&pub_range, &msg_range, NULL);
        if (rc != RCL_RET_OK) {
            digitalWrite(amr::hal::pin_led_internal, LOW);
        }
        // CAN-Send laeuft in sensorTask (Core 1)
    }

    // --- 3. IMU publizieren (50 Hz) ---
    if (imu_ok) {
        static unsigned long last_imu_pub = 0;
        if (millis() - last_imu_pub >= amr::timing::imu_publish_period_ms) {
            last_imu_pub = millis();
            float iax = 0, iay = 0, iaz = 0, igx = 0, igy = 0, igz = 0, ih = 0;
            if (xSemaphoreTake(mutex, 10)) {
                iax = shared.imu_ax;
                iay = shared.imu_ay;
                iaz = shared.imu_az;
                igx = shared.imu_gx;
                igy = shared.imu_gy;
                igz = shared.imu_gz;
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
            msg_imu.orientation.z = sinf(ih / 2);
            msg_imu.orientation.w = cosf(ih / 2);
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
            if (imu_rc != RCL_RET_OK) {
                digitalWrite(amr::hal::pin_led_internal, LOW);
            }
            // CAN-Send laeuft in sensorTask (Core 1)
        }
    }

    // --- 4. Battery publizieren (2 Hz, INA260) ---
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
                    // Shutdown-Status publizieren
                    msg_bat_shutdown.data = true;
                    rcl_publish(&pub_battery_shutdown, &msg_bat_shutdown, NULL);
                    if (can_ok)
                        can.sendBatteryShutdown(true);
                } else if (voltage > amr::battery::threshold_motor_shutdown_v +
                                         amr::battery::threshold_hysteresis_v) {
                    if (battery_motor_shutdown) {
                        battery_motor_shutdown = false;
                        if (pca9685_ok) {
                            if (xSemaphoreTake(i2c_mutex, pdMS_TO_TICKS(5))) {
                                pca9685.clearAllOff();
                                xSemaphoreGive(i2c_mutex);
                            } else {
                                i2c_contention_errors++;
                            }
                        }
                        msg_bat_shutdown.data = false;
                        rcl_publish(&pub_battery_shutdown, &msg_bat_shutdown, NULL);
                        if (can_ok)
                            can.sendBatteryShutdown(false);
                    }
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
                msg_bat.power_supply_technology =
                    sensor_msgs__msg__BatteryState__POWER_SUPPLY_TECHNOLOGY_LION;
                msg_bat.present = true;
                rcl_ret_t bat_rc = rcl_publish(&pub_battery, &msg_bat, NULL);
                if (bat_rc != RCL_RET_OK) {
                    digitalWrite(amr::hal::pin_led_internal, LOW);
                }
                if (can_ok)
                    can.sendBattery(voltage, current, power);
            }
        }
    }

    // CAN Heartbeat + Cliff/Range/IMU laufen in sensorTask (Core 1)
    // Battery CAN-Sends bleiben hier (I2C-Read nur in loop())
}
