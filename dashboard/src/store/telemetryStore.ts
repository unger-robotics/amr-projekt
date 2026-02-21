import { create } from 'zustand';
import type { TelemetryMsg, ScanMsg } from '../types/ros';

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
  // Actions
  updateTelemetry: (msg: TelemetryMsg) => void;
  updateScan: (msg: ScanMsg) => void;
}

export const useTelemetryStore = create<TelemetryState>((set) => ({
  // Defaults
  x: 0, y: 0, yawDeg: 0, velLinear: 0, velAngular: 0,
  headingDeg: 0, gzDegS: 0,
  esp32Active: false, odomHz: 0, scanHz: 0,
  scanRanges: [], scanAngleMin: 0, scanAngleMax: 0, scanAngleIncrement: 0,
  lastTelemetryTs: 0, lastScanTs: 0,

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
}));
