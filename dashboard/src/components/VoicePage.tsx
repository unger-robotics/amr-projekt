import { useTelemetryStore } from '../store/telemetryStore';
import type { ClientMessage } from '../types/ros';
import CommandInput from './CommandInput';

interface VoicePageProps {
  send: (msg: ClientMessage) => void;
  sendVoiceMute: (muted: boolean) => void;
}

/** Alle verfuegbaren Sprachbefehle (aus voice_command_node.py SYSTEM_PROMPT) */
const VOICE_COMMANDS = [
  { command: 'nav X Y', example: '"Fahr zu Position eins drei"', description: 'Navigation zu Koordinaten (Meter)' },
  { command: 'forward X', example: '"Fahr zwei Meter nach vorne"', description: 'X Meter geradeaus fahren (0-5 m)' },
  { command: 'turn X', example: '"Dreh dich 90 Grad nach links"', description: 'X Grad drehen (+links, -rechts)' },
  { command: 'turn_to_speaker', example: '"Dreh dich zu mir"', description: 'Zum Sprecher drehen (DoA-basiert)' },
  { command: 'stop', example: '"Stopp!"', description: 'Sofortstopp aller Motoren' },
  { command: 'backward X', example: '"Fahr 1 Meter zurueck"', description: 'X Meter rueckwaerts fahren (0-5 m)' },
  { command: 'schau nach links', example: '"Schau nach links"', description: 'Kamera nach links schwenken' },
  { command: 'schau nach rechts', example: '"Schau nach rechts"', description: 'Kamera nach rechts schwenken' },
  { command: 'schau nach vorne', example: '"Schau nach vorne"', description: 'Kamera geradeaus' },
  { command: 'licht an [%]', example: '"Licht an 50"', description: 'LED (0-100%, Standard 80%)' },
  { command: 'licht aus', example: '"Licht aus"', description: 'LED ausschalten' },
  { command: 'wie weit', example: '"Wie weit ist das Hindernis?"', description: 'Ultraschall-Distanz abfragen' },
  { command: 'akku', example: '"Wie ist der Akku?"', description: 'Batteriestatus abfragen' },
  { command: 'wo bin ich', example: '"Wo bin ich?"', description: 'Aktuelle Position und Ausrichtung' },
  { command: 'wetter', example: '"Wie ist das Wetter?"', description: 'Aktuelle Wetterdaten' },
  { command: 'test <name>', example: '"Starte Motor-Test"', description: 'Validierungstest ausfuehren' },
  { command: 'help', example: '"Hilfe"', description: 'Hilfe anzeigen' },
] as const;

const TEST_NAMES = [
  'rplidar', 'imu', 'motor', 'encoder', 'sensor', 'kinematic',
  'straight_drive', 'rotation', 'cliff_latency', 'slam', 'nav',
  'nav_square', 'docking', 'dashboard_latency', 'can',
];

function formatTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function VoicePage({ send, sendVoiceMute }: VoicePageProps) {
  const respeakerActive = useTelemetryStore((s) => s.respeakerActive);
  const isVoiceActive = useTelemetryStore((s) => s.isVoiceActive);
  const micMuted = useTelemetryStore((s) => s.micMuted);
  const soundDirection = useTelemetryStore((s) => s.soundDirection);
  const doaFiltered = useTelemetryStore((s) => s.doaFiltered);
  const doaQuadrant = useTelemetryStore((s) => s.doaQuadrant);
  const voiceHistory = useTelemetryStore((s) => s.voiceHistory);

  const handleSendCommand = (command: string) => {
    send({ op: 'command', text: command });
  };

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-5xl mx-auto space-y-4">

        {/* Live-Status */}
        <div className="bg-hud-panel border border-hud-border p-4">
          <div className="flex items-center justify-between border-b border-hud-border pb-1 mb-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70">
              Sprachsteuerung — Status
            </h2>
            <button
              onClick={() => sendVoiceMute(!micMuted)}
              className={`flex items-center gap-2 px-3 py-1.5 border text-xs uppercase tracking-wider transition-colors ${
                micMuted
                  ? 'border-hud-red/50 text-hud-red bg-hud-red/10 hover:bg-hud-red/20'
                  : 'border-hud-green/50 text-hud-green bg-hud-green/10 hover:bg-hud-green/20'
              }`}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                {micMuted ? (
                  <>
                    <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 7.46 2.05l-1.42-1.42A2 2 0 0 1 10 11V5a2 2 0 1 1 4 0v3.17l2 2V5a4 4 0 0 0-4-4z" />
                    <path d="M18 11a1 1 0 0 0-2 0 3.45 3.45 0 0 1-.09.8l1.53 1.53A5.98 5.98 0 0 0 18 11zM6 11a1 1 0 0 0-2 0 8 8 0 0 0 7 7.93V21H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3v-2.07A8 8 0 0 0 17.73 16l-1.42-1.42A6 6 0 0 1 6 11z" />
                    <path d="M3.71 3.29a1 1 0 0 0-1.42 1.42l18 18a1 1 0 0 0 1.42-1.42l-18-18z" />
                  </>
                ) : (
                  <>
                    <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4zm2 11a2 2 0 1 1-4 0V5a2 2 0 1 1 4 0v7z" />
                    <path d="M18 11a1 1 0 0 0-2 0 4 4 0 1 1-8 0 1 1 0 0 0-2 0 6 6 0 0 0 5 5.91V21H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3v-4.09A6 6 0 0 0 18 11z" />
                  </>
                )}
              </svg>
              {micMuted ? 'Mikrofon aus' : 'Mikrofon an'}
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* ReSpeaker */}
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-2.5 h-2.5 rounded-full ${
                  respeakerActive
                    ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
                    : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
                }`}
              />
              <span className="text-xs text-hud-text-dim uppercase tracking-wider">ReSpeaker</span>
              <span className={`text-xs ${respeakerActive ? 'text-hud-green' : 'text-hud-red'}`}>
                {respeakerActive ? 'Verbunden' : 'Getrennt'}
              </span>
            </div>
            {/* VAD */}
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-2.5 h-2.5 rounded-full ${
                  isVoiceActive && !micMuted
                    ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)] animate-pulse'
                    : 'bg-hud-text-dim'
                }`}
              />
              <span className="text-xs text-hud-text-dim uppercase tracking-wider">VAD</span>
              <span className={`text-xs ${isVoiceActive && !micMuted ? 'text-hud-green' : 'text-hud-text-dim'}`}>
                {micMuted ? 'Stumm' : isVoiceActive ? 'Sprache erkannt' : 'Stille'}
              </span>
            </div>
            {/* DoA */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-hud-text-dim uppercase tracking-wider">Richtung</span>
              <span className="text-xs text-hud-cyan font-mono">{(doaFiltered || soundDirection).toFixed(0)}&deg;</span>
              {doaQuadrant && (
                <span className="text-[10px] text-hud-amber uppercase tracking-wider">{doaQuadrant}</span>
              )}
            </div>
          </div>
        </div>

        {/* Befehlsreferenz */}
        <div className="bg-hud-panel border border-hud-border p-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
            Befehlsreferenz
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-hud-border text-hud-text-dim uppercase tracking-wider">
                  <th className="text-left py-2 pr-3">Befehl</th>
                  <th className="text-left py-2 pr-3">Beispiel</th>
                  <th className="text-left py-2 pr-3">Beschreibung</th>
                  <th className="text-right py-2 w-16"></th>
                </tr>
              </thead>
              <tbody>
                {VOICE_COMMANDS.map((cmd) => (
                  <tr key={cmd.command} className="border-b border-hud-border/30 hover:bg-hud-cyan/5">
                    <td className="py-2 pr-3 font-mono text-hud-cyan whitespace-nowrap">{cmd.command}</td>
                    <td className="py-2 pr-3 text-hud-text-dim italic">{cmd.example}</td>
                    <td className="py-2 pr-3 text-hud-text">{cmd.description}</td>
                    <td className="py-2 text-right">
                      {!cmd.command.includes('X') && !cmd.command.includes('<') && (
                        <button
                          onClick={() => handleSendCommand(cmd.command)}
                          className="px-2 py-0.5 text-[10px] border border-hud-border text-hud-cyan hover:bg-hud-cyan/10 transition-colors uppercase tracking-wider"
                        >
                          Senden
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Verfuegbare Tests */}
          <div className="mt-3 pt-3 border-t border-hud-border/30">
            <span className="text-[10px] text-hud-text-dim uppercase tracking-wider">
              Verfuegbare Tests fuer &quot;test &lt;name&gt;&quot;:
            </span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {TEST_NAMES.map((name) => (
                <button
                  key={name}
                  onClick={() => handleSendCommand(`test ${name}`)}
                  className="px-2 py-0.5 text-[10px] font-mono border border-hud-border/50 text-hud-text-dim hover:text-hud-cyan hover:border-hud-cyan/30 hover:bg-hud-cyan/5 transition-colors"
                >
                  {name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Kommandofeld */}
        <div className="bg-hud-panel border border-hud-border">
          <CommandInput send={send} />
        </div>

        {/* Sprachverlauf */}
        <div className="bg-hud-panel border border-hud-border p-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
            Sprachverlauf
            {voiceHistory.length > 0 && (
              <span className="ml-2 text-hud-text-dim font-normal">({voiceHistory.length})</span>
            )}
          </h2>

          {voiceHistory.length === 0 ? (
            <p className="text-xs text-hud-text-dim italic">
              Noch keine Sprachbefehle erkannt. Sprechen Sie einen Befehl in das ReSpeaker-Mikrofon.
            </p>
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {[...voiceHistory].reverse().map((entry, i) => (
                <div
                  key={`${entry.ts}-${i}`}
                  className="flex items-start gap-3 py-1.5 border-b border-hud-border/20 last:border-0"
                >
                  <span className="text-[10px] text-hud-text-dim font-mono whitespace-nowrap mt-0.5">
                    {formatTime(entry.ts)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-hud-text truncate">
                      &ldquo;{entry.text}&rdquo;
                    </p>
                    {entry.command && (
                      <span className="text-[10px] font-mono text-hud-cyan">
                        &rarr; {entry.command}
                      </span>
                    )}
                    {!entry.command && (
                      <span className="text-[10px] text-hud-text-dim italic">
                        Kein Befehl erkannt
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
