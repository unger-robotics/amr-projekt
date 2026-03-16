import { useState, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useTelemetryStore } from './store/telemetryStore';
import { Dashboard } from './components/Dashboard';
import DetailPage from './components/DetailPage';
import { EmergencyStop } from './components/EmergencyStop';
import type { ServerMessage } from './types/ros';

function App() {
  const [tab, setTab] = useState<'steuerung' | 'details'>('steuerung');

  const updateTelemetry = useTelemetryStore((s) => s.updateTelemetry);
  const updateScan = useTelemetryStore((s) => s.updateScan);
  const updateSystem = useTelemetryStore((s) => s.updateSystem);
  const updateMap = useTelemetryStore((s) => s.updateMap);
  const updateVisionDetections = useTelemetryStore((s) => s.updateVisionDetections);
  const updateVisionSemantics = useTelemetryStore((s) => s.updateVisionSemantics);
  const setVisionEnabled = useTelemetryStore((s) => s.setVisionEnabled);
  const updateNavStatus = useTelemetryStore((s) => s.updateNavStatus);
  const updateSensorStatus = useTelemetryStore((s) => s.updateSensorStatus);
  const updateAudioStatus = useTelemetryStore((s) => s.updateAudioStatus);
  const appendCommandResponse = useTelemetryStore((s) => s.appendCommandResponse);

  const onMessage = useCallback(
    (msg: ServerMessage) => {
      if (msg.op === 'telemetry') updateTelemetry(msg);
      else if (msg.op === 'scan') updateScan(msg);
      else if (msg.op === 'system') updateSystem(msg);
      else if (msg.op === 'map') updateMap(msg);
      else if (msg.op === 'vision_detections') updateVisionDetections(msg);
      else if (msg.op === 'vision_semantics') updateVisionSemantics(msg);
      else if (msg.op === 'vision_status') setVisionEnabled(msg.enabled);
      else if (msg.op === 'nav_status') updateNavStatus(msg);
      else if (msg.op === 'sensor_status') updateSensorStatus(msg);
      else if (msg.op === 'audio_status') updateAudioStatus(msg);
      else if (msg.op === 'command_response') appendCommandResponse(msg.text, msg.success);
    },
    [updateTelemetry, updateScan, updateSystem, updateMap, updateVisionDetections, updateVisionSemantics, setVisionEnabled, updateNavStatus, updateSensorStatus, updateAudioStatus, appendCommandResponse],
  );

  const { connected, latencyMs, send, sendServoCmd, sendHardwareCmd, sendNavGoal, sendNavCancel, sendAudioPlay, sendAudioVolume, sendVisionControl } = useWebSocket(onMessage);

  const handleEmergencyStop = useCallback(() => {
    for (let i = 0; i < 5; i++) {
      send({ op: 'cmd_vel', linear_x: 0, angular_z: 0 });
    }
  }, [send]);

  return (
    <div className="h-dvh bg-hud-bg text-hud-text flex flex-col overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-center gap-0 bg-hud-panel border-b border-hud-border">
        <button
          onClick={() => setTab('steuerung')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'steuerung' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Steuerung
        </button>
        <button
          onClick={() => setTab('details')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'details' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Details
        </button>
        {/* Connection indicator + Emergency Stop on the right */}
        <div className="ml-auto px-3 flex items-center gap-3">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-hud-green' : 'bg-hud-red'}`} />
          <span className="text-[10px] text-hud-text-dim">{connected ? 'Verbunden' : 'Getrennt'}</span>
          <EmergencyStop onStop={handleEmergencyStop} inline />
        </div>
      </div>

      {/* Active page */}
      {tab === 'steuerung' ? (
        <Dashboard
          connected={connected}
          latencyMs={latencyMs}
          send={send}
          sendServoCmd={sendServoCmd}
          sendHardwareCmd={sendHardwareCmd}
          sendNavGoal={sendNavGoal}
          sendNavCancel={sendNavCancel}
          sendVisionControl={sendVisionControl}
        />
      ) : (
        <DetailPage sendAudioPlay={sendAudioPlay} sendAudioVolume={sendAudioVolume} />
      )}
    </div>
  );
}

export default App;
