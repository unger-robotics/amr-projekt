import { useTelemetryStore } from '../store/telemetryStore';

function DeviceDot({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${
        active
          ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
          : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
      }`}
    />
  );
}

export default function ActiveDevicesPanel() {
  const esp32Active = useTelemetryStore((s) => s.esp32Active);
  const odomHz = useTelemetryStore((s) => s.odomHz);
  const sensorNodeActive = useTelemetryStore((s) => s.sensorNodeActive);
  const imuHz = useTelemetryStore((s) => s.imuHz);
  const ultrasonicHz = useTelemetryStore((s) => s.ultrasonicHz);
  const cliffHz = useTelemetryStore((s) => s.cliffHz);
  const lidarActive = useTelemetryStore((s) => s.lidarActive);
  const scanHz = useTelemetryStore((s) => s.scanHz);
  const cameraActive = useTelemetryStore((s) => s.cameraActive);
  const hailoDetected = useTelemetryStore((s) => s.hailoDetected);
  const detectionHz = useTelemetryStore((s) => s.detectionHz);
  const ina260Active = useTelemetryStore((s) => s.ina260Active);
  const batteryVoltage = useTelemetryStore((s) => s.batteryVoltage);
  const batteryCurrent = useTelemetryStore((s) => s.batteryCurrent);

  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        Aktive Geraete
      </h2>

      {/* ESP32-S3 Drive */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <DeviceDot active={esp32Active} />
          <span className="text-sm text-hud-text font-semibold">ESP32-S3 Drive</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">Fahrkern</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs ml-4">
          <span className="text-hud-text-dim">Odometrie</span>
          <span className="text-hud-cyan font-mono">{odomHz.toFixed(1)} Hz</span>
        </div>
      </div>

      {/* ESP32-S3 Sensoren */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <DeviceDot active={sensorNodeActive} />
          <span className="text-sm text-hud-text font-semibold">ESP32-S3 Sensoren</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">Sensor- und Sicherheitsbasis</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs ml-4">
          <span className="text-hud-text-dim">IMU</span>
          <span className="text-hud-cyan font-mono">{imuHz.toFixed(1)} Hz</span>
          <span className="text-hud-text-dim">Ultraschall</span>
          <span className="text-hud-cyan font-mono">{ultrasonicHz.toFixed(1)} Hz</span>
          <span className="text-hud-text-dim">Cliff</span>
          <span className="text-hud-cyan font-mono">{cliffHz.toFixed(1)} Hz</span>
        </div>
      </div>

      {/* RPLidar A1 */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <DeviceDot active={lidarActive} />
          <span className="text-sm text-hud-text font-semibold">RPLidar A1</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">2D-LiDAR</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs ml-4">
          <span className="text-hud-text-dim">Scan</span>
          <span className="text-hud-cyan font-mono">{scanHz.toFixed(1)} Hz</span>
        </div>
      </div>

      {/* IMX296 Kamera */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <DeviceDot active={cameraActive} />
          <span className="text-sm text-hud-text font-semibold">IMX296 Kamera</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">Global Shutter</span>
        </div>
      </div>

      {/* Hailo-8L */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <DeviceDot active={hailoDetected} />
          <span className="text-sm text-hud-text font-semibold">Hailo-8L</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">13 TOPS NPU</span>
        </div>
        {hailoDetected && detectionHz > 0 && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs ml-4">
            <span className="text-hud-text-dim">Inferenz</span>
            <span className="text-hud-cyan font-mono">{detectionHz.toFixed(1)} Hz</span>
          </div>
        )}
      </div>

      {/* INA260 */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <DeviceDot active={ina260Active} />
          <span className="text-sm text-hud-text font-semibold">INA260</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">Batteriemonitor</span>
        </div>
        {ina260Active && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs ml-4">
            <span className="text-hud-text-dim">Spannung</span>
            <span className="text-hud-cyan font-mono">{batteryVoltage.toFixed(2)} V</span>
            <span className="text-hud-text-dim">Strom</span>
            <span className="text-hud-cyan font-mono">{batteryCurrent.toFixed(2)} A</span>
          </div>
        )}
      </div>
    </div>
  );
}
