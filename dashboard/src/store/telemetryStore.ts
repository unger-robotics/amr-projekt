import { create } from 'zustand';
import type { TelemetryMsg, ScanMsg, SystemMsg, MapMsg, VisionDetectionsMsg, VisionSemanticsMsg, NavStatusMsg, Detection, SensorStatusMsg, AudioStatusMsg } from '../types/ros';

interface TelemetryState {
  // Odometry
  x: number;
  y: number;
  yawDeg: number;
  velLinear: number;
  velAngular: number;
  // IMU
  headingDeg: number;
  gzDegS: number;
  // Connection
  esp32Active: boolean;
  odomHz: number;
  scanHz: number;
  // LiDAR
  scanRanges: number[];
  scanAngleMin: number;
  scanAngleMax: number;
  scanAngleIncrement: number;
  // Timestamps
  lastTelemetryTs: number;
  lastScanTs: number;
  // System metrics
  cpuTempC: number;
  cpuLoad1m: number;
  ramUsedMb: number;
  ramTotalMb: number;
  diskUsedGb: number;
  diskTotalGb: number;
  diskUsagePct: number;
  lidarActive: boolean;
  cameraActive: boolean;
  hailoDetected: boolean;
  lastSystemTs: number;
  // Host network
  hostIp: string;
  // SLAM Map
  mapPngB64: string | null;
  mapWidth: number;
  mapHeight: number;
  mapResolution: number;
  mapOriginX: number;
  mapOriginY: number;
  robotMapX: number;
  robotMapY: number;
  robotMapYaw: number;
  // Vision
  visionDetections: Detection[];
  inferenceMs: number;
  detectionHz: number;
  lastDetectionTs: number;
  semanticAnalysis: string;
  semanticModel: string;
  lastSemanticsTs: number;
  // Battery (INA260)
  batteryVoltage: number;
  batteryCurrent: number;
  batteryPower: number;
  batteryPercentage: number;
  batteryRuntimeMin: number;
  // System extended
  cpuLoad5m: number;
  cpuLoad15m: number;
  cpuFreqMhz: number[];
  cpuPerCorePct: number[];
  uptimeS: number;
  processesRunning: number;
  processesTotal: number;
  ina260Active: boolean;
  // Servo (PCA9685 Pan/Tilt)
  servoPan: number;
  servoTilt: number;
  // Hardware (Motor-Limit, Servo-Speed, LED)
  hwMotorLimit: number;
  hwServoSpeed: number;
  hwLedPwm: number;
  // Serial-Transport Latenz (ESP32 → Pi)
  serialLatencyAvg: number;
  serialLatencyP95: number;
  // Navigation
  navStatus: 'idle' | 'navigating' | 'reached' | 'failed' | 'cancelled';
  navGoalX: number;
  navGoalY: number;
  navGoalYaw: number;
  navRemainingM: number;
  // Sensor-Node Detail
  sensorNodeActive: boolean;
  imuHz: number;
  ultrasonicHz: number;
  cliffHz: number;
  ultrasonicRange: number;
  cliffDetected: boolean;
  // Audio (ReSpeaker + HifiBerry)
  soundDirection: number;
  isVoiceActive: boolean;
  audioNodeActive: boolean;
  respeakerActive: boolean;
  audioVolume: number;
  // Actions
  updateTelemetry: (msg: TelemetryMsg) => void;
  updateScan: (msg: ScanMsg) => void;
  updateSystem: (msg: SystemMsg) => void;
  updateMap: (msg: MapMsg) => void;
  updateVisionDetections: (msg: VisionDetectionsMsg) => void;
  updateVisionSemantics: (msg: VisionSemanticsMsg) => void;
  updateNavStatus: (msg: NavStatusMsg) => void;
  updateSensorStatus: (msg: SensorStatusMsg) => void;
  updateAudioStatus: (msg: AudioStatusMsg) => void;
}

export const useTelemetryStore = create<TelemetryState>((set) => ({
  // Defaults
  x: 0, y: 0, yawDeg: 0, velLinear: 0, velAngular: 0,
  headingDeg: 0, gzDegS: 0,
  esp32Active: false, odomHz: 0, scanHz: 0,
  scanRanges: [], scanAngleMin: 0, scanAngleMax: 0, scanAngleIncrement: 0,
  lastTelemetryTs: 0, lastScanTs: 0,
  cpuTempC: 0, cpuLoad1m: 0, ramUsedMb: 0, ramTotalMb: 0,
  diskUsedGb: 0, diskTotalGb: 0, diskUsagePct: 0,
  lidarActive: false, cameraActive: false, hailoDetected: false,
  lastSystemTs: 0,
  hostIp: '',
  mapPngB64: null, mapWidth: 0, mapHeight: 0, mapResolution: 0.05,
  mapOriginX: 0, mapOriginY: 0, robotMapX: 0, robotMapY: 0, robotMapYaw: 0,
  visionDetections: [], inferenceMs: 0, detectionHz: 0, lastDetectionTs: 0,
  semanticAnalysis: '', semanticModel: '', lastSemanticsTs: 0,
  batteryVoltage: 0, batteryCurrent: 0, batteryPower: 0, batteryPercentage: 0, batteryRuntimeMin: -1,
  cpuLoad5m: 0, cpuLoad15m: 0, cpuFreqMhz: [], cpuPerCorePct: [], uptimeS: 0,
  processesRunning: 0, processesTotal: 0, ina260Active: false,
  servoPan: 90, servoTilt: 90,
  hwMotorLimit: 100, hwServoSpeed: 5, hwLedPwm: 0,
  serialLatencyAvg: 0, serialLatencyP95: 0,
  navStatus: 'idle', navGoalX: 0, navGoalY: 0, navGoalYaw: 0, navRemainingM: 0,
  sensorNodeActive: false, imuHz: 0, ultrasonicHz: 0, cliffHz: 0,
  ultrasonicRange: 0, cliffDetected: false,
  soundDirection: 0, isVoiceActive: false, audioNodeActive: false, respeakerActive: false, audioVolume: 80,

  updateTelemetry: (msg) => set({
    x: msg.odom.x,
    y: msg.odom.y,
    yawDeg: msg.odom.yaw_deg,
    velLinear: msg.odom.vel_linear,
    velAngular: msg.odom.vel_angular,
    headingDeg: msg.imu.heading_deg,
    gzDegS: msg.imu.gz_deg_s,
    esp32Active: msg.connection.esp32_active,
    odomHz: msg.connection.odom_hz,
    scanHz: msg.connection.scan_hz,
    lastTelemetryTs: msg.ts,
    ...(msg.battery && {
      batteryVoltage: msg.battery.voltage,
      batteryCurrent: msg.battery.current,
      batteryPower: msg.battery.power,
      batteryPercentage: msg.battery.percentage,
      batteryRuntimeMin: msg.battery.runtime_min ?? -1,
    }),
    ...(msg.servo && {
      servoPan: msg.servo.pan,
      servoTilt: msg.servo.tilt,
    }),
    ...(msg.hardware && {
      hwMotorLimit: msg.hardware.motor_limit,
      hwServoSpeed: msg.hardware.servo_speed,
      hwLedPwm: msg.hardware.led_pwm,
    }),
    ...(msg.connection.latency && {
      serialLatencyAvg: msg.connection.latency.avg_ms,
      serialLatencyP95: msg.connection.latency.p95_ms,
    }),
  }),

  updateScan: (msg) => set({
    scanRanges: msg.ranges,
    scanAngleMin: msg.angle_min,
    scanAngleMax: msg.angle_max,
    scanAngleIncrement: msg.angle_increment,
    lastScanTs: msg.ts,
  }),

  updateSystem: (msg) => set({
    cpuTempC: msg.cpu.temp_c,
    cpuLoad1m: msg.cpu.load_1m,
    cpuLoad5m: msg.cpu.load_5m ?? 0,
    cpuLoad15m: msg.cpu.load_15m ?? 0,
    cpuFreqMhz: msg.cpu.freq_mhz ?? [],
    cpuPerCorePct: msg.cpu.per_cpu_pct ?? [],
    ramUsedMb: msg.ram.used_mb,
    ramTotalMb: msg.ram.total_mb,
    diskUsedGb: msg.disk.used_gb,
    diskTotalGb: msg.disk.total_gb,
    diskUsagePct: msg.disk.usage_pct,
    lidarActive: msg.devices.lidar,
    cameraActive: msg.devices.camera,
    hailoDetected: msg.devices.hailo,
    ina260Active: msg.devices.ina260 ?? false,
    audioNodeActive: msg.devices.audio ?? false,
    respeakerActive: msg.devices.respeaker ?? false,
    lastSystemTs: msg.ts,
    hostIp: msg.ip ?? '',
    uptimeS: msg.uptime_s ?? 0,
    processesRunning: msg.processes?.running ?? 0,
    processesTotal: msg.processes?.total ?? 0,
  }),

  updateMap: (msg) => set({
    mapPngB64: msg.png_b64,
    mapWidth: msg.width,
    mapHeight: msg.height,
    mapResolution: msg.resolution,
    mapOriginX: msg.origin_x,
    mapOriginY: msg.origin_y,
    robotMapX: msg.robot.x,
    robotMapY: msg.robot.y,
    robotMapYaw: msg.robot.yaw,
  }),

  updateVisionDetections: (msg) => set({
    visionDetections: msg.detections,
    inferenceMs: msg.inference_ms,
    detectionHz: msg.detection_hz,
    lastDetectionTs: msg.ts,
  }),

  updateVisionSemantics: (msg) => set({
    semanticAnalysis: msg.analysis,
    semanticModel: msg.model,
    lastSemanticsTs: msg.ts,
  }),

  updateNavStatus: (msg) => set({
    navStatus: msg.status,
    navGoalX: msg.goal_x,
    navGoalY: msg.goal_y,
    navGoalYaw: msg.goal_yaw,
    navRemainingM: msg.remaining_distance_m,
  }),

  updateSensorStatus: (msg) => set({
    sensorNodeActive: msg.sensor_node_active,
    imuHz: msg.imu_hz,
    ultrasonicHz: msg.ultrasonic.hz,
    cliffHz: msg.cliff.hz,
    ultrasonicRange: msg.ultrasonic.range_m,
    cliffDetected: msg.cliff.detected,
  }),

  updateAudioStatus: (msg) => set({
    soundDirection: msg.direction_deg,
    isVoiceActive: msg.is_voice,
    audioVolume: msg.volume_percent ?? 80,
  }),
}));
