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
