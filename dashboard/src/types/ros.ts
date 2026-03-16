/** Batterie-Daten (INA260, 2 Hz) */
export interface BatteryData {
  voltage: number;
  current: number;
  power: number;
  percentage: number;
  runtime_min: number;
}

/** Servo-Daten (PCA9685 Pan/Tilt) */
export interface ServoData {
  pan: number;
  tilt: number;
}

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
    latency?: {
      min_ms: number;
      avg_ms: number;
      max_ms: number;
      p95_ms: number;
      samples: number;
    };
  };
  battery?: BatteryData;
  servo?: ServoData;
  hardware?: HardwareData;
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

/** Servo-Steuerbefehl ans Backend (PCA9685 Pan/Tilt) */
export interface ServoCmdMsg {
  op: 'servo_cmd';
  pan: number;
  tilt: number;
}

/** Hardware-Steuerbefehl ans Backend (Motor/Servo/LED) */
export interface HardwareCmdMsg {
  op: 'hardware_cmd';
  motor_limit: number;   // 0-100 (%)
  servo_speed: number;   // 1-10 (Grad/Schritt)
  led_pwm: number;       // 0-255 (0 = Auto-Heartbeat)
}

/** Hardware-Daten (Telemetrie-Feedback) */
export interface HardwareData {
  motor_limit: number;
  servo_speed: number;
  led_pwm: number;
}

/** System-Metriken vom Backend (1 Hz) */
export interface SystemMsg {
  op: 'system';
  ts: number;
  cpu: { temp_c: number; load_1m: number; load_5m: number; load_15m: number; freq_mhz: number[]; per_cpu_pct: number[] };
  ram: { total_mb: number; used_mb: number; usage_pct: number };
  disk: { total_gb: number; used_gb: number; usage_pct: number };
  devices: { esp32: boolean; lidar: boolean; camera: boolean; hailo: boolean; ina260: boolean; audio: boolean; respeaker: boolean };
  ip: string;
  uptime_s: number;
  processes: { running: number; total: number };
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

/** Navigationsziel ans Backend */
export interface NavGoalMsg {
  op: 'nav_goal';
  x: number;
  y: number;
  yaw: number;
}

/** Navigations-Abbruch ans Backend */
export interface NavCancelMsg {
  op: 'nav_cancel';
}

/** Navigationsstatus vom Backend (1 Hz) */
export interface NavStatusMsg {
  op: 'nav_status';
  ts: number;
  status: 'idle' | 'navigating' | 'reached' | 'failed' | 'cancelled';
  goal_x: number;
  goal_y: number;
  goal_yaw: number;
  remaining_distance_m: number;
}

/** Sensor-Status vom Backend (2 Hz) */
export interface SensorStatusMsg {
  op: 'sensor_status';
  ts: number;
  ultrasonic: { range_m: number; hz: number };
  cliff: { detected: boolean; hz: number };
  imu_hz: number;
  sensor_node_active: boolean;
}

/** Audio-Status vom Backend (2 Hz) */
export interface AudioStatusMsg {
  op: 'audio_status';
  ts: number;
  direction_deg: number;
  is_voice: boolean;
  volume_percent: number;
}

/** Audio-Abspielbefehl ans Backend */
export interface AudioPlayMsg {
  op: 'audio_play';
  sound_key: string;
}

/** Lautstaerke-Aenderung ans Backend */
export interface AudioVolumeMsg {
  op: 'audio_volume';
  volume_percent: number;
}

/** Freitext-Kommando ans Backend */
export interface CommandMsg {
  op: 'command';
  text: string;
}

/** Kommando-Antwort vom Backend */
export interface CommandResponseMsg {
  op: 'command_response';
  text: string;
  success: boolean;
}

/** Vision-Steuerung ans Backend (ein/aus) */
export interface VisionControlMsg {
  op: 'vision_control';
  enabled: boolean;
}

/** Vision-Status vom Backend (Bestaetigung) */
export interface VisionStatusMsg {
  op: 'vision_status';
  enabled: boolean;
}

export type ServerMessage = TelemetryMsg | ScanMsg | SystemMsg | MapMsg | VisionDetectionsMsg | VisionSemanticsMsg | NavStatusMsg | SensorStatusMsg | AudioStatusMsg | VisionStatusMsg | CommandResponseMsg;
export type ClientMessage = CmdVelMsg | HeartbeatMsg | ServoCmdMsg | HardwareCmdMsg | NavGoalMsg | NavCancelMsg | AudioPlayMsg | AudioVolumeMsg | VisionControlMsg | CommandMsg;
