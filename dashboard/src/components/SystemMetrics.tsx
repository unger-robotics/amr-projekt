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

function DeviceIndicator({ label, active }: { label: string; active: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`inline-block w-2 h-2 ${
          active
            ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
            : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
        }`}
      />
      <span className="text-hud-text-dim uppercase tracking-wider">{label}</span>
    </div>
  );
}

export function SystemMetrics() {
  const cpuTempC = useTelemetryStore((s) => s.cpuTempC);
  const cpuLoad1m = useTelemetryStore((s) => s.cpuLoad1m);
  const ramUsedMb = useTelemetryStore((s) => s.ramUsedMb);
  const ramTotalMb = useTelemetryStore((s) => s.ramTotalMb);
  const diskUsagePct = useTelemetryStore((s) => s.diskUsagePct);
  const esp32Active = useTelemetryStore((s) => s.esp32Active);
  const lidarActive = useTelemetryStore((s) => s.lidarActive);
  const cameraActive = useTelemetryStore((s) => s.cameraActive);
  const hailoDetected = useTelemetryStore((s) => s.hailoDetected);
  const hostIp = useTelemetryStore((s) => s.hostIp);
  const inferenceMs = useTelemetryStore((s) => s.inferenceMs);
  const detectionHz = useTelemetryStore((s) => s.detectionHz);
  const visionDetections = useTelemetryStore((s) => s.visionDetections);
  const batteryVoltage = useTelemetryStore((s) => s.batteryVoltage);
  const batteryCurrent = useTelemetryStore((s) => s.batteryCurrent);
  const batteryPower = useTelemetryStore((s) => s.batteryPower);
  const batteryPercentage = useTelemetryStore((s) => s.batteryPercentage);
  const hasBattery = batteryVoltage > 0 || batteryCurrent > 0 || batteryPower > 0 || batteryPercentage > 0;

  return (
    <div className="bg-hud-panel text-hud-text p-4 flex flex-col gap-4 border-t border-hud-border">
      {/* Netzwerk */}
      {hostIp && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
            Netzwerk
          </h2>
          <div className="flex justify-between text-xs">
            <span className="text-hud-text-dim uppercase tracking-wider">Pi5 IP</span>
            <span className="text-hud-cyan font-medium font-mono">{hostIp}</span>
          </div>
        </section>
      )}

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
          <MetricBar label="CPU Load" value={cpuLoad1m} max={4.0} unit="" />
          <MetricBar label="RAM" value={ramUsedMb} max={ramTotalMb || 1} unit=" MB" />
          <MetricBar label="Disk" value={diskUsagePct} max={100} unit="%" />
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

      {/* Geraete */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
          Geraete
        </h2>
        <div className="flex flex-col gap-1.5">
          <DeviceIndicator label="ESP32-S3" active={esp32Active} />
          <DeviceIndicator label="RPLidar A1" active={lidarActive} />
          <DeviceIndicator label="IMX296 Cam" active={cameraActive} />
          <DeviceIndicator label="Hailo-8" active={hailoDetected} />
        </div>
      </section>
    </div>
  );
}
