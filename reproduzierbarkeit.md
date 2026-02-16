# Reproduzierbarkeits-Snapshot: AMR-Projekt

**Erfasst:** 2026-02-16, Commit `f6c807f`
**Zweck:** Vollstaendige Dokumentation aller Hardware- und Software-Versionen fuer die Reproduzierbarkeit der Bachelorarbeit-Ergebnisse.

---

## 1. Hardware-Plattform

### 1.1 Recheneinheiten

| Komponente | Modell | Details |
|---|---|---|
| SBC | Raspberry Pi 5 Model B Rev 1.1 | 8 GB RAM, Debian 13 (Trixie), aarch64 |
| Mikrocontroller | Seeed Studio XIAO ESP32-S3 | Dual-Core Xtensa LX7, 240 MHz, 8 MB Flash, 8 MB PSRAM |
| ESP32 MAC | `e8:06:90:9d:9b:a0` | USB JTAG/serial debug unit |
| AI-Beschleuniger | Hailo-8 (PCIe, Rev 01) | `0001:01:00.0`, HailoRT 4.23.0 |

### 1.2 Sensorik

| Sensor | Modell | Schnittstelle | Details |
|---|---|---|---|
| 2D-LiDAR | RPLIDAR A1 (Slamtec) | USB `/dev/ttyUSB0` (CP2102, 115200 Baud) | 360 Grad, ~7.6 Hz, 12 m Reichweite |
| IMU | MPU6050 (GY-521) | I2C (SDA=D4, SCL=D5, 400 kHz, Addr 0x68) | +-2g / +-250 deg/s, 500-Sample Gyro-Kalibrierung |
| Kamera | RPi Global Shutter (IMX296) | CSI (22-pin Mini, `dtoverlay=imx296`) | 1456x1088 @ 30fps, 10-bit Bayer SBGGR10 |
| Encoder | JGA25-370 Hall-Encoder (2x) | GPIO Quadratur (D6/D8 links, D7/D9 rechts) | 2x-Zaehlung: 748.6 / 747.2 Ticks/Rev |

### 1.3 Aktuatoren

| Komponente | Modell | Details |
|---|---|---|
| Motortreiber | Cytron MDD3A | Dual-PWM-Modus, 20 kHz, 8-bit (0-255) |
| Motoren | JGA25-370 (2x) | DC-Getriebemotoren mit Hall-Encoder |
| LED-Treiber | IRLZ24N N-MOSFET (D10) | Low-Side Switch, PWM-Kanal 4, 5 kHz |
| Akku | 3S1P Li-Ion | 11.1-12.6 V, 15-A-Sicherung |
| Spannungswandler | DC/DC Buck USB-C | 5V/5A (25W) fuer RPi5 |

### 1.4 Kinematische Parameter (`hardware/config.h`)

| Parameter | Wert | Einheit | Kalibrierung |
|---|---|---|---|
| Raddurchmesser | 65.67 | mm | 3x 1m-Bodentest, Massband-Vergleich |
| Radradius | 32.835 | mm | WHEEL_DIAMETER / 2 |
| Spurbreite | 178 | mm | Mechanisch gemessen |
| Ticks/Rev links | 748.6 | Ticks | 10-Umdrehungen-Test, 2x Quadratur |
| Ticks/Rev rechts | 747.2 | Ticks | 10-Umdrehungen-Test, 2x Quadratur |
| Meter/Tick | ~0.000276 | m/Tick | pi * 65.67mm / 748 |
| PWM-Deadzone | 35 | PWM-Wert | Empirisch (Motor laeuft nicht an) |
| Failsafe-Timeout | 500 | ms | Motorstopp ohne cmd_vel |

### 1.5 Pin-Belegung XIAO ESP32-S3

| Pin | GPIO | Funktion |
|---|---|---|
| D0 | GPIO1 | Motor Links A (Vorwaerts-PWM, Kanal 1) |
| D1 | GPIO2 | Motor Links B (Rueckwaerts-PWM, Kanal 0) |
| D2 | GPIO3 | Motor Rechts A (Vorwaerts-PWM, Kanal 3) |
| D3 | GPIO4 | Motor Rechts B (Rueckwaerts-PWM, Kanal 2) |
| D4 | GPIO5 | I2C SDA (MPU6050) |
| D5 | GPIO6 | I2C SCL (MPU6050) |
| D6 | GPIO43 | Encoder Links Phase A (CHANGE-Interrupt, IRAM_ATTR) |
| D7 | GPIO44 | Encoder Rechts Phase A (CHANGE-Interrupt, IRAM_ATTR) |
| D8 | GPIO7 | Encoder Links Phase B (Richtungserkennung) |
| D9 | GPIO8 | Encoder Rechts Phase B (Richtungserkennung) |
| D10 | GPIO9 | LED-MOSFET (IRLZ24N, PWM-Kanal 4, 5 kHz) |

---

## 2. Software-Versionen

### 2.1 Raspberry Pi 5 (Host)

| Komponente | Version |
|---|---|
| OS | Debian GNU/Linux 13 (Trixie) |
| Kernel | 6.12.62+rpt-rpi-2712 |
| Architektur | aarch64 |
| Python | 3.13.5 |
| GCC | 14.2.0 (Debian 14.2.0-19) |
| Docker | 29.2.1, Build a5c7197 |
| Docker Compose | v5.0.2 |
| PlatformIO Core | 6.1.19 |
| esptool | 5.1.0 |

### 2.2 Python-Pakete (Host, apt)

| Paket | Version | Funktion |
|---|---|---|
| python3-opencv | 4.10.0+dfsg-5 | Computer Vision, ArUco-Erkennung |
| python3-serial | 3.5-2 | Serial-Kommunikation |
| python3-numpy | 1:2.2.4+ds-1 | Numerische Berechnungen |
| python3-hailort | 4.23.0-1 | Hailo-8 AI Runtime |
| v4l2loopback-dkms | 0.15.0-2 | Kamera-Bridge Kernelmodul |
| rpicam-apps | 1.10.1-1 | Kamera-Tools (rpicam-hello/vid) |

### 2.3 ESP32 Toolchain (PlatformIO)

| Komponente | Version |
|---|---|
| Platform | espressif32 v6.12.0 |
| Framework | Arduino (framework-arduinoespressif32) |
| Toolchain | xtensa-esp32s3-elf-gcc 8.4.0 (crosstool-NG esp-2021r2-patch5) |
| Board | seeed_xiao_esp32s3 |
| Upload-Baudrate | 921600 |
| Monitor-Baudrate | 115200 |
| micro-ROS | micro_ros_platformio (GitHub, Branch humble) |
| C++-Standard | C++11 (ESP32-Arduino default) |

### 2.4 Docker-Container (ROS2 Humble)

| Komponente | Version |
|---|---|
| Docker-Image | amr-ros2-humble:latest (3.8 GB, gebaut 2026-02-14) |
| Basis-Image | ros:humble-ros-base (Ubuntu 22.04 Jammy, arm64) |
| ROS2 Distribution | Humble Hawksbill |

**ROS2-Pakete im Container:**

| Paket | Version |
|---|---|
| nav2-bringup | 1.1.20 |
| nav2-regulated-pure-pursuit-controller | 1.1.20 |
| nav2-navfn-planner | 1.1.20 |
| nav2-amcl | 1.1.20 |
| nav2-costmap-2d | 1.1.20 |
| nav2-map-server | 1.1.20 |
| slam-toolbox | 2.6.10 |
| rplidar-ros | 2.1.4 |
| cv-bridge | 3.2.1 |
| v4l2-camera | 0.6.2 |
| micro-ros-agent | Aus Source gebaut (kein apt fuer arm64) |

### 2.5 Raspberry Pi Boot-Konfiguration (`/boot/firmware/config.txt`)

```
dtparam=i2c_arm=on
dtparam=audio=on
dtoverlay=vc4-kms-v3d
arm_64bit=1
arm_boost=1
dtoverlay=dwc2,dr_mode=host
dtoverlay=imx296
```

---

## 3. Firmware-Parameter

### 3.1 PID-Regelung

| Parameter | Wert | Beschreibung |
|---|---|---|
| Kp | 0.4 | Proportionalverstaerkung |
| Ki | 0.1 | Integralverstaerkung |
| Kd | 0.0 | Differentialverstaerkung (nicht verwendet) |
| Anti-Windup | [-1.0, 1.0] | Integral-Clamping |
| EMA-Filter alpha | 0.3 | Encoder-Geschwindigkeitsglaettung fuer PID |
| MAX_ACCEL | 5.0 rad/s^2 | Beschleunigungsrampe |
| Dead-Band | 0.08 | driveMotor() Schwelle |
| Stillstand-Bypass | |Sollwert| < 0.01 | Motoren direkt stoppen, PID-Reset |

### 3.2 IMU-Konfiguration (MPU6050)

| Parameter | Wert | Beschreibung |
|---|---|---|
| Messbereich Accel | +-2 g | Register-Konfiguration |
| Messbereich Gyro | +-250 deg/s | Register-Konfiguration |
| I2C-Frequenz | 400 kHz | Fast Mode |
| Sample Rate (intern) | 100 Hz | Firmware-seitig |
| Publish Rate | 20 Hz | `/imu` Topic |
| Kalibrierungs-Samples | 500 | Gyro-Bias beim Startup |
| Complementary alpha | 0.02 | 98% Gyro, 2% Encoder-Heading |
| Kovarianz orientation | 0.01 | Imu-Nachricht |
| Kovarianz angular_vel | 0.001 | Imu-Nachricht |
| Kovarianz linear_acc | 0.1 | Imu-Nachricht |

### 3.3 micro-ROS Konfiguration

| Parameter | Wert | Beschreibung |
|---|---|---|
| Transport | Serial (USB-CDC) | 115200 Baud |
| Distribution | Humble | Passend zu Pi-Container |
| Node-Name | esp32_bot | micro-ROS Node |
| MTU | 512 Bytes | UXR_CONFIG_CUSTOM_TRANSPORT_MTU |
| QoS | Reliable | rclc_publisher_init_default() |
| Max Output-Buffer | 2048 Bytes | MTU * STREAM_HISTORY (4) |
| Odom-Rate | 20 Hz | nav_msgs/Odometry |
| IMU-Rate | 20 Hz | sensor_msgs/Imu |

### 3.4 Timing

| Task | Core | Frequenz | Prioritaet |
|---|---|---|---|
| micro-ROS Executor (loop) | Core 0 | ~20 Hz | Standard |
| PID-Regelschleife (controlTask) | Core 1 | 50 Hz (20 ms) | Prioritaet 1, pinned |

---

## 4. Navigation-Stack Konfiguration

### 4.1 SLAM Toolbox (`mapper_params_online_async.yaml`)

| Parameter | Wert |
|---|---|
| Modus | Async Online |
| Solver | Ceres (SPARSE_NORMAL_CHOLESKY, Levenberg-Marquardt) |
| Kartenaufloesung | 5 cm |
| Max. Laser-Range | 12 m |
| Loop Closure | aktiv |
| Min. Travel Distance | 0.5 m |
| Map Update Interval | 0.5 s |

### 4.2 Nav2 (`nav2_params.yaml`)

| Parameter | Wert |
|---|---|
| Controller | Regulated Pure Pursuit (RPP) |
| Max. Geschwindigkeit | 0.4 m/s |
| Lookahead | 0.3-0.7 m (Standard 0.5 m) |
| Controller-Frequenz | 10 Hz |
| Planner | NavFn (Dijkstra) |
| xy-Toleranz | 0.10 m |
| Yaw-Toleranz | 0.15 rad (~8.6 Grad) |
| Costmap-Aufloesung | 5 cm |
| Roboter-Radius | 15 cm |
| Inflation | 35 cm |
| AMCL Partikel | 500-2000 |
| AMCL Modell | differential, likelihood_field |
| Recovery | Spin, Backup, Wait |

### 4.3 TF-Baum

```
map -> odom -> base_link -> laser (statisch: X=0.10m, Z=0.05m, Yaw=pi)
  (SLAM)  (odom_to_tf)   -> camera_link (statisch: X=0.10m, Z=0.08m, optional)
```

---

## 5. Validierungsergebnisse (Referenzwerte)

### 5.1 Subsystem-Verifikation

| Test | Ergebnis | Akzeptanzkriterium | Status |
|---|---|---|---|
| PID-Regelfrequenz | 50 Hz, Jitter < 2 ms | 50 Hz | PASS |
| Odom-Publikationsrate | 20 Hz stabil | 20 Hz | PASS |
| Odom-Genauigkeit (aufgebockt) | 0.985 m bei Soll 1.0 m (98.5%) | > 95% | PASS |
| Raddurchmesser-Kalibrierung | 65.67 mm (Fehler 0.5%) | < 5% | PASS |
| Laterale Drift (1m, ohne IMU) | 3.5 cm | < 5 cm | PASS |
| Laterale Drift (1m, mit IMU) | 1.5 cm | < 5 cm | PASS |
| IMU Gyro-Drift | 0.218 deg/min | < 1.0 deg/min | PASS |
| IMU Accel-Bias | 0.49 m/s^2 | < 0.6 m/s^2 | PASS |
| IMU Heading-Diff | 0.01 deg | < 5.0 deg | PASS |
| Open-Loop 360-Grad-Drehung | 12.7 deg Defizit | informativ | -- |
| Closed-Loop Drehung (IMU) | < 2 deg Fehler | < 5 deg | PASS |
| Bremsrampe Overshoot | 0.4 cm (vorher 3.2 cm) | < 2 cm | PASS |

### 5.2 Integrationstest (SLAM)

| Test | Ergebnis | Akzeptanzkriterium | Status |
|---|---|---|---|
| Odom-Drift nach 4m | 19 cm Position, 23 deg Heading | informativ (Open-Loop) | -- |
| SLAM-Korrektur (map->odom) | 38 cm Translation, 16.6 deg Rotation | aktiv | PASS |
| Karte | 107x94 Zellen @ 5 cm = 5.4x4.7 m | plausibel | PASS |
| LiDAR-Rate | ~7.6 Hz | > 5 Hz | PASS |

---

## 6. Serielle Geraete-Identifikation

| Geraet | Pfad | by-id Symlink |
|---|---|---|
| ESP32-S3 | /dev/ttyACM0 | usb-Espressif_USB_JTAG_serial_debug_unit_E8:06:90:9D:9B:A0-if00 |
| RPLIDAR A1 | /dev/ttyUSB0 | usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 |

---

## 7. Docker-Container-Konfiguration

```yaml
# docker-compose.yml (Kern-Einstellungen)
network_mode: host          # DDS Multicast Discovery
privileged: true             # Serial, Kamera, GPIO
volumes:
  - ../pi5/ros2_ws/src/my_bot:/ros2_ws/src/my_bot:rw
  - ../scripts:/amr_scripts:ro
  - ../scripts:/scripts:ro   # Symlink-Aufloesung
  - ../../hardware:/hardware:ro
  - /tmp/.X11-unix:/tmp/.X11-unix:rw
device_cgroup_rules:
  - 'c 166:*'               # ttyACM (ESP32)
  - 'c 188:*'               # ttyUSB (RPLIDAR)
  - 'c 81:*'                # video4linux (Kamera)
```

---

## 8. Kamera-Pipeline

```
IMX296 (CSI) -> rpicam-vid --codec mjpeg (Host)
             -> ffmpeg -f v4l2 -pix_fmt yuyv422
             -> /dev/video10 (v4l2loopback, video_nr=10)
             -> v4l2_camera_node (Docker/ROS2, /camera/image_raw)
```

- Host-Service: `camera-v4l2-bridge.service` (systemd)
- Aufloesung: 1456x1088 @ 15 fps (MJPEG -> YUYV)
- Kernel-Modul: v4l2loopback-dkms 0.15.0-2
