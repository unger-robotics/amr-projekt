import { useCallback, useState } from 'react';
import { useJoystick } from '../hooks/useJoystick';
import { useTelemetryStore } from '../store/telemetryStore';
import type { ClientMessage } from '../types/ros';
import { StatusPanel } from './StatusPanel';
import { CameraView } from './CameraView';
import { LidarView } from './LidarView';
import { Joystick } from './Joystick';
import { EmergencyStop } from './EmergencyStop';
import { SystemMetrics } from './SystemMetrics';
import { MapView } from './MapView';
import ServoControl from './ServoControl';
import HardwareControl from './HardwareControl';

interface DashboardProps {
  connected: boolean;
  latencyMs: number;
  send: (msg: ClientMessage) => void;
  sendServoCmd: (pan: number, tilt: number) => void;
  sendHardwareCmd: (motorLimit: number, servoSpeed: number, ledPwm: number) => void;
  sendNavGoal: (x: number, y: number, yaw: number) => void;
  sendNavCancel: () => void;
  sendVisionControl: (enabled: boolean) => void;
}

export function Dashboard({ connected, latencyMs, send, sendServoCmd, sendHardwareCmd, sendNavGoal, sendNavCancel, sendVisionControl }: DashboardProps) {
  const [statusVisible, setStatusVisible] = useState(false);

  const navStatus = useTelemetryStore((s) => s.navStatus);
  const navGoalX = useTelemetryStore((s) => s.navGoalX);
  const navGoalY = useTelemetryStore((s) => s.navGoalY);
  const navRemainingM = useTelemetryStore((s) => s.navRemainingM);

  const { onJoystickMove, onJoystickEnd } = useJoystick(send);

  const handleEmergencyStop = useCallback(() => {
    for (let i = 0; i < 5; i++) {
      send({ op: 'cmd_vel', linear_x: 0, angular_z: 0 });
    }
    onJoystickEnd();
  }, [send, onJoystickEnd]);

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-y-auto lg:overflow-hidden lg:grid lg:grid-cols-[320px_1fr_1fr_1fr] lg:grid-rows-[repeat(6,minmax(0,1fr))]">
      {/* Sidebar: alle 6 Zeilen, scrollbar */}
      <aside className="hidden lg:flex lg:flex-col lg:col-start-1 lg:row-start-1 lg:row-end-7 border-r border-hud-border overflow-y-auto">
        <StatusPanel connected={connected} latencyMs={latencyMs} />
        <SystemMetrics />
        <HardwareControl sendHardwareCmd={sendHardwareCmd} />
      </aside>

      {/* Kamera (Zeile 1-3, Spalte 2) */}
      <div className="min-h-[200px] lg:min-h-0 lg:col-start-2 lg:row-start-1 lg:row-end-4 overflow-hidden">
        <CameraView sendVisionControl={sendVisionControl} />
      </div>

      {/* SLAM-Karte (Zeile 1-3, Spalte 3) */}
      <div className="min-h-[200px] lg:min-h-0 lg:col-start-3 lg:row-start-1 lg:row-end-4 overflow-hidden relative">
        <MapView
          onNavGoal={connected ? sendNavGoal : undefined}
          navStatus={navStatus}
          navGoalX={navGoalX}
          navGoalY={navGoalY}
        />
        {navStatus !== 'idle' && (
          <div className="absolute bottom-2 left-2 right-2 flex items-center gap-2 bg-hud-panel/90 border border-hud-border px-3 py-1.5 text-xs z-10">
            <span className={
              navStatus === 'navigating' ? 'text-hud-cyan' :
              navStatus === 'reached' ? 'text-green-400' :
              'text-red-400'
            }>
              {navStatus === 'navigating' ? `NAV ${navRemainingM.toFixed(1)}m` :
               navStatus === 'reached' ? 'ZIEL ERREICHT' :
               navStatus === 'failed' ? 'NAV FEHLER' :
               'ABGEBROCHEN'}
            </span>
            {navStatus === 'navigating' && (
              <button
                onClick={sendNavCancel}
                className="ml-auto text-red-400 hover:text-red-300 border border-red-400/50 px-2 py-0.5"
              >
                Abbrechen
              </button>
            )}
          </div>
        )}
      </div>

      {/* LiDAR (Zeile 1-3, Spalte 4) */}
      <div className="min-h-[200px] lg:min-h-0 lg:col-start-4 lg:row-start-1 lg:row-end-4 overflow-hidden">
        <LidarView />
      </div>

      {/* Joystick — unter Kamera (Zeile 4-6, Spalte 2) */}
      <div className="shrink-0 lg:shrink lg:col-start-2 lg:row-start-4 lg:row-end-7 flex items-center justify-center p-2 border-t border-hud-border lg:border-t-0">
        <Joystick
          onMove={onJoystickMove}
          onEnd={onJoystickEnd}
          disabled={!connected}
          compact
        />
      </div>

      {/* ServoControl — unter SLAM (Zeile 4-6, Spalte 3) */}
      <div className="shrink-0 lg:shrink lg:col-start-3 lg:row-start-4 lg:row-end-7 flex flex-col justify-center border-t border-hud-border lg:border-t-0">
        <ServoControl sendServoCmd={sendServoCmd} />
      </div>

      {/* EmergencyStop — unter LiDAR (Zeile 4-6, Spalte 4) */}
      <div className="shrink-0 lg:shrink lg:col-start-4 lg:row-start-4 lg:row-end-7 flex items-center justify-center p-4 border-t border-hud-border lg:border-t-0">
        <EmergencyStop onStop={handleEmergencyStop} />
      </div>

      {/* Mobile status toggle button */}
      <button
        onClick={() => setStatusVisible((v) => !v)}
        className="fixed top-12 left-3 z-40 lg:hidden bg-hud-panel hover:bg-hud-bg text-hud-text-dim p-2 border border-hud-border text-xs"
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
            className="absolute top-20 left-3 w-64 max-h-[80vh] border border-hud-border overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Statusanzeige"
          >
            <StatusPanel connected={connected} latencyMs={latencyMs} />
            <SystemMetrics />
          </div>
        </div>
      )}
    </div>
  );
}
