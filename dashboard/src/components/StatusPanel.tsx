import { useTelemetryStore } from '../store/telemetryStore';

interface StatusPanelProps {
  connected: boolean;
  latencyMs: number;
}

function Dot({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block w-2 h-2 ${
        active
          ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
          : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
      }`}
    />
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-hud-text-dim uppercase tracking-wider">{label}</span>
      <span className="text-hud-cyan font-medium">{value}</span>
    </div>
  );
}

export function StatusPanel({ connected, latencyMs }: StatusPanelProps) {
  const x = useTelemetryStore((s) => s.x);
  const y = useTelemetryStore((s) => s.y);
  const yawDeg = useTelemetryStore((s) => s.yawDeg);
  const velLinear = useTelemetryStore((s) => s.velLinear);
  const velAngular = useTelemetryStore((s) => s.velAngular);
  const headingDeg = useTelemetryStore((s) => s.headingDeg);
  const esp32Active = useTelemetryStore((s) => s.esp32Active);
  const odomHz = useTelemetryStore((s) => s.odomHz);
  const scanHz = useTelemetryStore((s) => s.scanHz);

  return (
    <div className="bg-hud-panel text-hud-text p-4 flex flex-col gap-4 overflow-y-auto hud-glow">
      {/* Verbindung */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
          Verbindung
        </h2>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-xs">
            <Dot active={connected} />
            <span className={connected ? 'text-hud-green' : 'text-hud-red'}>
              {connected ? 'WebSocket verbunden' : 'Getrennt'}
            </span>
          </div>
          <Row label="Latenz" value={`${Math.round(latencyMs)} ms`} />
          <div className="flex items-center gap-2 text-xs">
            <Dot active={esp32Active} />
            <span className={esp32Active ? 'text-hud-green' : 'text-hud-red'}>
              ESP32 {esp32Active ? 'aktiv' : 'inaktiv'}
            </span>
          </div>
        </div>
      </section>

      {/* Odometrie */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
          Odometrie
        </h2>
        <div className="flex flex-col gap-1.5">
          <Row label="X" value={`${x.toFixed(2)} m`} />
          <Row label="Y" value={`${y.toFixed(2)} m`} />
          <Row label="Yaw" value={`${yawDeg.toFixed(1)}\u00B0`} />
          <Row label="v linear" value={`${velLinear.toFixed(2)} m/s`} />
          <Row label="v angular" value={`${velAngular.toFixed(2)} rad/s`} />
        </div>
      </section>

      {/* Sensoren */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
          Sensoren
        </h2>
        <div className="flex flex-col gap-1.5">
          <Row label="Odom Hz" value={`${odomHz.toFixed(1)}`} />
          <Row label="Scan Hz" value={`${scanHz.toFixed(1)}`} />
          <Row label="IMU Heading" value={`${headingDeg.toFixed(1)}\u00B0`} />
        </div>
      </section>
    </div>
  );
}
