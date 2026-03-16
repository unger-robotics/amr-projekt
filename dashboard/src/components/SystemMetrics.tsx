import { useTelemetryStore } from '../store/telemetryStore';

function MetricBar({ label, value, max, unit }: { label: string; value: number; max: number; unit: string }) {
  const pct = Math.min((value / max) * 100, 100);
  const warn = pct > 80;

  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex justify-between text-xs">
        <span className="text-hud-text-dim uppercase tracking-wider">{label}</span>
        <span className={warn ? 'text-hud-amber' : 'text-hud-cyan'}>
          {typeof value === 'number' ? value.toFixed(1) : value}{unit}
        </span>
      </div>
      <div className="h-1 bg-hud-bg">
        <div
          className={`h-full transition-all duration-500 ${warn ? 'bg-hud-amber' : 'bg-hud-cyan'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

/** Returns a Tailwind color class based on battery voltage level */
function batteryColor(voltage: number): string {
  if (voltage < 9.5) return 'bg-hud-red';
  if (voltage < 10.5) return 'bg-hud-amber';
  if (voltage < 11.5) return 'bg-yellow-400';
  return 'bg-hud-green';
}

/** Returns a Tailwind text color class based on battery voltage level */
function batteryTextColor(voltage: number): string {
  if (voltage < 9.5) return 'text-hud-red';
  if (voltage < 10.5) return 'text-hud-amber';
  if (voltage < 11.5) return 'text-yellow-400';
  return 'text-hud-green';
}

function BatteryBar({ label, value, min, max, unit, voltage }: {
  label: string; value: number; min: number; max: number; unit: string; voltage: number;
}) {
  const pct = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);
  const barColor = batteryColor(voltage);
  const txtColor = batteryTextColor(voltage);

  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex justify-between text-xs">
        <span className="text-hud-text-dim uppercase tracking-wider">{label}</span>
        <span className={`${txtColor} font-mono`}>
          {value.toFixed(label === 'SOC' ? 0 : 2)}{unit}
        </span>
      </div>
      <div className="h-1 bg-hud-bg">
        <div
          className={`h-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function formatUptime(seconds: number): string {
  if (seconds <= 0) return '--';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function SystemMetrics() {
  const cpuTempC = useTelemetryStore((s) => s.cpuTempC);
  const cpuLoad1m = useTelemetryStore((s) => s.cpuLoad1m);
  const ramUsedMb = useTelemetryStore((s) => s.ramUsedMb);
  const ramTotalMb = useTelemetryStore((s) => s.ramTotalMb);
  const diskUsagePct = useTelemetryStore((s) => s.diskUsagePct);
  const cpuLoad5m = useTelemetryStore((s) => s.cpuLoad5m);
  const cpuLoad15m = useTelemetryStore((s) => s.cpuLoad15m);
  const cpuFreqMhz = useTelemetryStore((s) => s.cpuFreqMhz);
  const cpuPerCorePct = useTelemetryStore((s) => s.cpuPerCorePct);
  const uptimeS = useTelemetryStore((s) => s.uptimeS);
  const inferenceMs = useTelemetryStore((s) => s.inferenceMs);
  const detectionHz = useTelemetryStore((s) => s.detectionHz);
  const visionDetections = useTelemetryStore((s) => s.visionDetections);
  const batteryVoltage = useTelemetryStore((s) => s.batteryVoltage);
  const batteryCurrent = useTelemetryStore((s) => s.batteryCurrent);
  const batteryPower = useTelemetryStore((s) => s.batteryPower);
  const batteryPercentage = useTelemetryStore((s) => s.batteryPercentage);
  const batteryRuntimeMin = useTelemetryStore((s) => s.batteryRuntimeMin);
  const hasBattery = batteryVoltage > 0 || batteryCurrent > 0 || batteryPower > 0 || batteryPercentage > 0;

  return (
    <div className="bg-hud-panel text-hud-text p-4 flex flex-col gap-4 border-t border-hud-border">
      {/* Batterie */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
          Batterie
        </h2>
        {hasBattery ? (
          <div className="flex flex-col gap-2">
            <BatteryBar label="Spannung" value={batteryVoltage} min={9.0} max={12.6} unit=" V" voltage={batteryVoltage} />
            <BatteryBar label="SOC" value={batteryPercentage} min={0} max={100} unit="%" voltage={batteryVoltage} />
            <div className="flex justify-between text-xs">
              <span className="text-hud-text-dim uppercase tracking-wider">Strom / Leistung</span>
              <span className="text-hud-cyan font-mono">{batteryCurrent.toFixed(2)} A / {batteryPower.toFixed(1)} W</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-hud-text-dim uppercase tracking-wider">Restlaufzeit</span>
              <span className={`font-mono ${batteryTextColor(batteryVoltage)}`}>
                {batteryRuntimeMin > 0
                  ? `~${Math.floor(batteryRuntimeMin / 60)}h ${String(Math.round(batteryRuntimeMin % 60)).padStart(2, '0')}min`
                  : '-- : --'}
              </span>
            </div>
            <div className="text-[10px] text-hud-text-dim tracking-wider">3S1P INR18650-35E</div>
          </div>
        ) : (
          <div className="text-xs text-hud-text-dim">Nicht verfuegbar</div>
        )}
      </section>

      {/* System */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
          System
        </h2>
        <div className="flex flex-col gap-2">
          <MetricBar label="CPU Temp" value={cpuTempC} max={85} unit="°C" />
          {/* Load 1/5/15m */}
          <div className="flex justify-between text-xs">
            <span className="text-hud-text-dim uppercase tracking-wider">Load</span>
            <span className="text-hud-cyan font-mono">
              {cpuLoad1m.toFixed(2)} / {cpuLoad5m.toFixed(2)} / {cpuLoad15m.toFixed(2)}
            </span>
          </div>
          {/* Per-CPU-Balken */}
          {cpuPerCorePct.length > 0 && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-hud-text-dim uppercase tracking-wider">Per-CPU</span>
              <div className="flex gap-1">
                {cpuPerCorePct.map((pct, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                    <div className="w-full h-3 bg-hud-bg relative">
                      <div
                        className={`absolute bottom-0 w-full transition-all duration-500 ${pct > 80 ? 'bg-hud-amber' : 'bg-hud-cyan'}`}
                        style={{ height: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                    <span className="text-[9px] text-hud-text-dim font-mono">{Math.round(pct)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* CPU-Frequenzen */}
          {cpuFreqMhz.length > 0 && (
            <div className="flex justify-between text-xs">
              <span className="text-hud-text-dim uppercase tracking-wider">Freq</span>
              <span className="text-hud-cyan font-mono text-[10px]">
                {cpuFreqMhz.map((f) => `${f}`).join(' / ')} MHz
              </span>
            </div>
          )}
          <MetricBar label="RAM" value={ramUsedMb} max={ramTotalMb || 1} unit=" MB" />
          <MetricBar label="Disk" value={diskUsagePct} max={100} unit="%" />
          {/* Uptime */}
          <div className="flex justify-between text-xs">
            <span className="text-hud-text-dim uppercase tracking-wider">Uptime</span>
            <span className="text-hud-cyan font-mono">{formatUptime(uptimeS)}</span>
          </div>
        </div>
      </section>

      {/* Vision (nur sichtbar wenn Hailo aktiv) */}
      {detectionHz > 0 && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
            Vision
          </h2>
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs">
              <span className="text-hud-text-dim uppercase tracking-wider">Inference</span>
              <span className="text-orange-400 font-mono">{inferenceMs.toFixed(0)} ms</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-hud-text-dim uppercase tracking-wider">Det. Hz</span>
              <span className="text-hud-cyan font-mono">{detectionHz.toFixed(1)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-hud-text-dim uppercase tracking-wider">Objekte</span>
              <span className="text-hud-cyan font-mono">{visionDetections.length}</span>
            </div>
          </div>
        </section>
      )}

    </div>
  );
}
