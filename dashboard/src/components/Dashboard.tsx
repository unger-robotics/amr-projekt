import { useCallback, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useJoystick } from '../hooks/useJoystick';
import { useTelemetryStore } from '../store/telemetryStore';
import type { ServerMessage } from '../types/ros';
import { StatusPanel } from './StatusPanel';
import { CameraView } from './CameraView';
import { LidarView } from './LidarView';
import { Joystick } from './Joystick';
import { EmergencyStop } from './EmergencyStop';
import { SystemMetrics } from './SystemMetrics';
import { MapView } from './MapView';

export function Dashboard() {
  const [statusVisible, setStatusVisible] = useState(false);

  const updateTelemetry = useTelemetryStore((s) => s.updateTelemetry);
  const updateScan = useTelemetryStore((s) => s.updateScan);
  const updateSystem = useTelemetryStore((s) => s.updateSystem);
  const updateMap = useTelemetryStore((s) => s.updateMap);
  const updateVisionDetections = useTelemetryStore((s) => s.updateVisionDetections);
  const updateVisionSemantics = useTelemetryStore((s) => s.updateVisionSemantics);

  const onMessage = useCallback(
    (msg: ServerMessage) => {
      if (msg.op === 'telemetry') updateTelemetry(msg);
      else if (msg.op === 'scan') updateScan(msg);
      else if (msg.op === 'system') updateSystem(msg);
      else if (msg.op === 'map') updateMap(msg);
      else if (msg.op === 'vision_detections') updateVisionDetections(msg);
      else if (msg.op === 'vision_semantics') updateVisionSemantics(msg);
    },
    [updateTelemetry, updateScan, updateSystem, updateMap, updateVisionDetections, updateVisionSemantics],
  );

  const { connected, latencyMs, send } = useWebSocket(onMessage);
  const { onJoystickMove, onJoystickEnd } = useJoystick(send);

  const handleEmergencyStop = useCallback(() => {
    for (let i = 0; i < 5; i++) {
      send({ op: 'cmd_vel', linear_x: 0, angular_z: 0 });
    }
    onJoystickEnd();
  }, [send, onJoystickEnd]);

  return (
    <div className="h-dvh bg-hud-bg text-hud-text grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[280px_1fr_280px] overflow-hidden">
      {/* Status panel -- visible on lg, toggle on mobile/tablet */}
      <aside className="hidden lg:flex flex-col border-r border-hud-border overflow-y-auto">
        <StatusPanel connected={connected} latencyMs={latencyMs} />
        <SystemMetrics />
      </aside>

      {/* Center content: untereinander (mobile/tablet), nebeneinander oben angedockt (desktop) */}
      <main className="flex flex-col lg:flex-row lg:items-start min-h-0 sm:col-span-1">
        <div className="flex-1 min-h-0 lg:min-w-0 lg:h-[50vh]">
          <CameraView />
        </div>
        <div className="flex-1 min-h-0 lg:min-w-0 lg:h-[50vh]">
          <MapView />
        </div>
        <div className="flex-1 min-h-0 lg:min-w-0 lg:h-[50vh]">
          <LidarView />
        </div>
      </main>

      {/* Joystick panel */}
      <aside className="border-t sm:border-t-0 sm:border-l border-hud-border flex flex-col">
        <div className="flex-1 min-h-0">
          <Joystick
            onMove={onJoystickMove}
            onEnd={onJoystickEnd}
            disabled={!connected}
          />
        </div>
      </aside>

      {/* Mobile status toggle button */}
      <button
        onClick={() => setStatusVisible((v) => !v)}
        className="fixed top-3 left-3 z-40 lg:hidden bg-hud-panel hover:bg-hud-bg text-hud-text-dim p-2 border border-hud-border text-xs"
        aria-label="Status anzeigen"
      >
        {statusVisible ? 'Schliessen' : 'Status'}
      </button>

      {/* Mobile status overlay */}
      {statusVisible && (
        <div className="fixed inset-0 z-30 lg:hidden bg-hud-bg/90 backdrop-blur-sm"
          onClick={() => setStatusVisible(false)}
          role="presentation"
        >
          <div
            className="absolute top-12 left-3 w-64 max-h-[80vh] border border-hud-border overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Statusanzeige"
          >
            <StatusPanel connected={connected} latencyMs={latencyMs} />
            <SystemMetrics />
          </div>
        </div>
      )}

      {/* Emergency stop -- always visible */}
      <EmergencyStop onStop={handleEmergencyStop} />
    </div>
  );
}
