import { useState, useCallback, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useTelemetryStore } from './store/telemetryStore';
import { Dashboard } from './components/Dashboard';
import DetailPage from './components/DetailPage';
import ValidationPage from './components/ValidationPage';
import VoicePage from './components/VoicePage';
import AufgabenPage from './components/AufgabenPage';
import ControlReferencePage from './components/ControlReferencePage';
import { EmergencyStop } from './components/EmergencyStop';
import type { ServerMessage } from './types/ros';

function App() {
  const [tab, setTab] = useState<'steuerung' | 'aufgaben' | 'details' | 'validierung' | 'sprache' | 'referenz'>('steuerung');

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
  const updateVoiceTranscript = useTelemetryStore((s) => s.updateVoiceTranscript);
  const setMicMuted = useTelemetryStore((s) => s.setMicMuted);
  const appendCommandResponse = useTelemetryStore((s) => s.appendCommandResponse);
  const setAvailableTests = useTelemetryStore((s) => s.setAvailableTests);
  const addTestResult = useTelemetryStore((s) => s.addTestResult);
  const setEstopStatus = useTelemetryStore((s) => s.setEstopStatus);

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
      else if (msg.op === 'voice_transcript') updateVoiceTranscript(msg.text, msg.command ?? '', msg.ts);
      else if (msg.op === 'voice_mute_status') setMicMuted(msg.muted);
      else if (msg.op === 'command_response') {
        appendCommandResponse(msg.text, msg.success, msg.pending);
        // Testergebnis erkennen und im Store ablegen
        if (!msg.pending && msg.text?.startsWith("Test ")) {
          const match = msg.text.match(/^Test (\S+):\s*(PASS|FAIL)/);
          if (match) {
            const entryPoint = match[1];
            const state = useTelemetryStore.getState();
            const testInfo = state.availableTests.find((t) => t.entry_point === entryPoint);
            if (testInfo) {
              addTestResult(testInfo.key, msg.text, msg.success);
            }
          }
        }
      }
      else if (msg.op === 'test_list') setAvailableTests(msg.tests);
      else if (msg.op === 'estop_status') setEstopStatus(msg.engaged, msg.source);
    },
    [updateTelemetry, updateScan, updateSystem, updateMap, updateVisionDetections, updateVisionSemantics, setVisionEnabled, updateNavStatus, updateSensorStatus, updateAudioStatus, updateVoiceTranscript, setMicMuted, appendCommandResponse, setAvailableTests, addTestResult, setEstopStatus],
  );

  const { connected, latencyMs, send, sendServoCmd, sendHardwareCmd, sendNavGoal, sendNavCancel, sendAudioPlay, sendAudioVolume, sendVisionControl, sendVoiceMute, sendEstop, sendEstopRelease } = useWebSocket(onMessage);

  // Testliste beim Verbindungsaufbau anfordern
  useEffect(() => {
    if (connected) {
      send({ op: 'test_list' });
    }
  }, [connected, send]);

  const handleEmergencyStop = useCallback(() => {
    sendEstop();
  }, [sendEstop]);

  const handleEmergencyRelease = useCallback(() => {
    sendEstopRelease();
  }, [sendEstopRelease]);

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
          onClick={() => setTab('aufgaben')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'aufgaben' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Aufgaben
        </button>
        <button
          onClick={() => setTab('details')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'details' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Details
        </button>
        <button
          onClick={() => setTab('validierung')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'validierung' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Validierung
        </button>
        <button
          onClick={() => setTab('sprache')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'sprache' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Sprache
        </button>
        <button
          onClick={() => setTab('referenz')}
          className={`px-4 py-2 text-xs uppercase tracking-wider font-semibold transition-colors
            ${tab === 'referenz' ? 'text-hud-cyan border-b-2 border-hud-cyan bg-hud-bg' : 'text-hud-text-dim hover:text-hud-text'}`}
        >
          Referenz
        </button>
        {/* Connection indicator + Emergency Stop on the right */}
        <div className="ml-auto px-3 flex items-center gap-3">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-hud-green' : 'bg-hud-red'}`} />
          <span className="text-[10px] text-hud-text-dim">{connected ? 'Verbunden' : 'Getrennt'}</span>
          <EmergencyStop onStop={handleEmergencyStop} onRelease={handleEmergencyRelease} inline />
        </div>
      </div>

      {/* Active page */}
      {tab === 'steuerung' && (
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
      )}
      {tab === 'aufgaben' && (
        <AufgabenPage
          send={send}
          sendNavGoal={sendNavGoal}
          sendNavCancel={sendNavCancel}
          sendVisionControl={sendVisionControl}
          sendAudioPlay={sendAudioPlay}
        />
      )}
      {tab === 'details' && (
        <DetailPage sendAudioPlay={sendAudioPlay} sendAudioVolume={sendAudioVolume} />
      )}
      {tab === 'validierung' && (
        <ValidationPage send={send} />
      )}
      {tab === 'sprache' && (
        <VoicePage send={send} sendVoiceMute={sendVoiceMute} />
      )}
      {tab === 'referenz' && <ControlReferencePage />}
    </div>
  );
}

export default App;
