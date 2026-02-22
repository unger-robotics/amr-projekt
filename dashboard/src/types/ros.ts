/** Telemetrie-Nachricht vom Backend (10 Hz) */
export interface TelemetryMsg {
  op: 'telemetry';
  ts: number;
  odom: {
    x: number;
    y: number;
    yaw_deg: number;
    vel_linear: number;
    vel_angular: number;
  };
  imu: {
    heading_deg: number;
    gz_deg_s: number;
  };
  connection: {
    esp32_active: boolean;
    odom_hz: number;
    scan_hz: number;
  };
}

/** LiDAR-Scan vom Backend (2 Hz) */
export interface ScanMsg {
  op: 'scan';
  ts: number;
  angle_min: number;
  angle_max: number;
  angle_increment: number;
  ranges: number[];
}

/** Steuerbefehl ans Backend */
export interface CmdVelMsg {
  op: 'cmd_vel';
  linear_x: number;
  angular_z: number;
}

/** Heartbeat ans Backend (Deadman-Switch) */
export interface HeartbeatMsg {
  op: 'heartbeat';
}

/** System-Metriken vom Backend (1 Hz) */
export interface SystemMsg {
  op: 'system';
  ts: number;
  cpu: { temp_c: number; load_1m: number; load_5m: number; freq_mhz: number[] };
  ram: { total_mb: number; used_mb: number; usage_pct: number };
  disk: { total_gb: number; used_gb: number; usage_pct: number };
  devices: { esp32: boolean; lidar: boolean; camera: boolean; hailo: boolean };
  ip: string;
}

/** SLAM-Karte vom Backend (~0.5 Hz) */
export interface MapMsg {
  op: 'map';
  ts: number;
  png_b64: string;
  width: number;
  height: number;
  resolution: number;
  origin_x: number;
  origin_y: number;
  robot: { x: number; y: number; yaw: number; };
}

/** Einzelne Objekterkennung (Hailo-8 YOLOv8) */
export interface Detection {
  class_id: number;
  label: string;
  confidence: number;
  /** Normalisierte BBox [x1, y1, x2, y2] im Bereich 0.0-1.0 */
  bbox_norm: [number, number, number, number];
}

/** Vision-Detektionen vom Backend (5 Hz) */
export interface VisionDetectionsMsg {
  op: 'vision_detections';
  ts: number;
  inference_ms: number;
  detections: Detection[];
  detection_hz: number;
}

/** Semantische Analyse vom Backend (~0.5 Hz) */
export interface VisionSemanticsMsg {
  op: 'vision_semantics';
  ts: number;
  analysis: string;
  model: string;
}

export type ServerMessage = TelemetryMsg | ScanMsg | SystemMsg | MapMsg | VisionDetectionsMsg | VisionSemanticsMsg;
export type ClientMessage = CmdVelMsg | HeartbeatMsg;
