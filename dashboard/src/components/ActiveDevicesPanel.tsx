import { useTelemetryStore } from '../store/telemetryStore';

export default function ActiveDevicesPanel() {
  const esp32Active = useTelemetryStore((s) => s.esp32Active);
  const odomHz = useTelemetryStore((s) => s.odomHz);
  const sensorNodeActive = useTelemetryStore((s) => s.sensorNodeActive);
  const imuHz = useTelemetryStore((s) => s.imuHz);
  const ultrasonicHz = useTelemetryStore((s) => s.ultrasonicHz);
  const cliffHz = useTelemetryStore((s) => s.cliffHz);

  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        Aktive Geraete
      </h2>

      {/* Device 1: ESP32-S3 Drive */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              esp32Active
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
                : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
            }`}
          />
          <span className="text-sm text-hud-text font-semibold">ESP32-S3 Drive</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">Fahrkern</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs ml-4">
          <span className="text-hud-text-dim">Odometrie</span>
          <span className="text-hud-cyan font-mono">{odomHz.toFixed(1)} Hz</span>
        </div>
      </div>

      {/* Device 2: ESP32-S3 Sensoren */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              sensorNodeActive
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
                : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
            }`}
          />
          <span className="text-sm text-hud-text font-semibold">ESP32-S3 Sensoren</span>
          <span className="text-[10px] text-hud-text-dim ml-auto">Sensor- und Sicherheitsbasis</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs ml-4">
          <span className="text-hud-text-dim">IMU</span>
          <span className="text-hud-cyan font-mono">{imuHz.toFixed(1)} Hz</span>
          <span className="text-hud-text-dim">Ultraschall</span>
          <span className="text-hud-cyan font-mono">{ultrasonicHz.toFixed(1)} Hz</span>
          <span className="text-hud-text-dim">Cliff</span>
          <span className="text-hud-cyan font-mono">{cliffHz.toFixed(1)} Hz</span>
        </div>
      </div>
    </div>
  );
}
