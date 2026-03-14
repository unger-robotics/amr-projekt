import { useTelemetryStore } from '../store/telemetryStore';

export default function SensorDetailPanel() {
  const ultrasonicRange = useTelemetryStore((s) => s.ultrasonicRange);
  const cliffDetected = useTelemetryStore((s) => s.cliffDetected);
  const scanHz = useTelemetryStore((s) => s.scanHz);
  const lidarActive = useTelemetryStore((s) => s.lidarActive);

  // Ultrasonic bar: max 4.0m range
  const barPct = Math.min(100, (ultrasonicRange / 4.0) * 100);
  // Color: green > 0.5m, amber 0.2-0.5m, red < 0.2m
  const barColor =
    ultrasonicRange > 0.5
      ? 'bg-hud-green'
      : ultrasonicRange > 0.2
        ? 'bg-hud-amber'
        : 'bg-hud-red';

  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        Sensorik
      </h2>

      {/* Ultrasonic */}
      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-hud-text-dim uppercase tracking-wider">Ultraschall (HC-SR04)</span>
          <span className="text-hud-cyan font-mono">{(ultrasonicRange * 100).toFixed(1)} cm</span>
        </div>
        <div className="h-2 bg-hud-bg rounded-sm overflow-hidden">
          <div
            className={`h-full ${barColor} transition-all duration-200`}
            style={{ width: `${barPct}%` }}
          />
        </div>
        <span className="text-[10px] text-hud-text-dim">Montagehoehe: 50 mm ueber Boden</span>
      </div>

      {/* Cliff */}
      <div className="mb-4">
        <div className="flex items-center gap-3">
          <span className="text-xs text-hud-text-dim uppercase tracking-wider">IR Cliff-Sensor (MH-B)</span>
          <div
            className={`px-3 py-1 text-xs font-bold uppercase tracking-wider ${
              cliffDetected
                ? 'bg-hud-red/20 text-hud-red border border-hud-red/50'
                : 'bg-hud-green/20 text-hud-green border border-hud-green/50'
            }`}
          >
            {cliffDetected ? 'KANTE' : 'SICHER'}
          </div>
        </div>
      </div>

      {/* LiDAR */}
      <div>
        <div className="flex justify-between text-xs">
          <span className="text-hud-text-dim uppercase tracking-wider">LiDAR (RPLiDAR A1)</span>
          <span className="text-hud-cyan font-mono">{scanHz.toFixed(1)} Hz</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              lidarActive
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
                : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
            }`}
          />
          <span className="text-[10px] text-hud-text-dim">Laserhoehe: 235 mm</span>
        </div>
      </div>
    </div>
  );
}
