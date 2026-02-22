import { create } from 'zustand';
import type { TelemetryMsg, ScanMsg, SystemMsg, MapMsg, VisionDetectionsMsg, VisionSemanticsMsg, Detection } from '../types/ros';

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
  // Actions
  updateTelemetry: (msg: TelemetryMsg) => void;
  updateScan: (msg: ScanMsg) => void;
  updateSystem: (msg: SystemMsg) => void;
  updateMap: (msg: MapMsg) => void;
  updateVisionDetections: (msg: VisionDetectionsMsg) => void;
  updateVisionSemantics: (msg: VisionSemanticsMsg) => void;
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
    ramUsedMb: msg.ram.used_mb,
    ramTotalMb: msg.ram.total_mb,
    diskUsedGb: msg.disk.used_gb,
    diskTotalGb: msg.disk.total_gb,
    diskUsagePct: msg.disk.usage_pct,
    lidarActive: msg.devices.lidar,
    cameraActive: msg.devices.camera,
    hailoDetected: msg.devices.hailo,
    lastSystemTs: msg.ts,
    hostIp: msg.ip ?? '',
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
}));
