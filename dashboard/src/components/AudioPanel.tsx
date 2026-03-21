import { useTelemetryStore } from '../store/telemetryStore';

interface AudioPanelProps {
  sendAudioPlay: (soundKey: string) => void;
  sendAudioVolume: (volumePercent: number) => void;
}

const SOUND_BUTTONS = [
  { key: 'startup', label: 'Startup' },
  { key: 'nav_start', label: 'Nav Start' },
  { key: 'nav_reached', label: 'Nav Erreicht' },
  { key: 'cliff_alarm', label: 'Alarm' },
] as const;

export default function AudioPanel({ sendAudioPlay, sendAudioVolume }: AudioPanelProps) {
  const soundDirection = useTelemetryStore((s) => s.soundDirection);
  const doaFiltered = useTelemetryStore((s) => s.doaFiltered);
  const doaQuadrant = useTelemetryStore((s) => s.doaQuadrant);
  const isVoiceActive = useTelemetryStore((s) => s.isVoiceActive);
  const respeakerActive = useTelemetryStore((s) => s.respeakerActive);
  const audioNodeActive = useTelemetryStore((s) => s.audioNodeActive);
  const audioVolume = useTelemetryStore((s) => s.audioVolume);
  const voiceTranscript = useTelemetryStore((s) => s.voiceTranscript);

  // DoA compass geometry
  const compassSize = 120;
  const cx = compassSize / 2;
  const cy = compassSize / 2;
  const r = cx - 15;
  // Map compass degrees (0=North, clockwise) to SVG coordinates
  const displayDeg = doaFiltered || soundDirection;
  const rad = ((displayDeg - 90) * Math.PI) / 180;
  const lineX = cx + r * Math.cos(rad);
  const lineY = cy + r * Math.sin(rad);

  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        Audio
      </h2>

      {/* Mikrofon (ReSpeaker) */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              respeakerActive
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
                : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
            }`}
          />
          <span className="text-xs text-hud-text-dim uppercase tracking-wider">Mikrofon (ReSpeaker)</span>
        </div>

        {/* VAD Indicator */}
        <div className="flex items-center gap-2 text-xs mb-3 ml-4">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              isVoiceActive
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)] animate-pulse'
                : 'bg-hud-text-dim'
            }`}
          />
          <span className="text-hud-text-dim">VAD</span>
          <span className={isVoiceActive ? 'text-hud-green' : 'text-hud-text-dim'}>
            {isVoiceActive ? 'Sprache erkannt' : 'Stille'}
          </span>
        </div>

        {/* Sprach-Transkript */}
        {voiceTranscript && (
          <div className="ml-4 mb-3 px-2 py-1 border border-hud-border/50 bg-hud-bg/50">
            <span className="text-[10px] text-hud-text-dim uppercase tracking-wider">Letzter Sprachbefehl</span>
            <p className="text-xs text-hud-cyan italic truncate">&ldquo;{voiceTranscript}&rdquo;</p>
          </div>
        )}

        {/* DoA Compass */}
        <div className="flex flex-col items-center gap-1">
          <svg
            width={compassSize}
            height={compassSize}
            viewBox={`0 0 ${compassSize} ${compassSize}`}
            className="mx-auto"
          >
            {/* Circle outline */}
            <circle
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke="currentColor"
              className="text-hud-border"
              strokeWidth="1"
            />
            {/* N/S/E/W labels */}
            <text x={cx} y={12} textAnchor="middle" className="text-[10px] fill-hud-text-dim">N</text>
            <text x={cx} y={compassSize - 4} textAnchor="middle" className="text-[10px] fill-hud-text-dim">S</text>
            <text x={compassSize - 6} y={cy + 4} textAnchor="middle" className="text-[10px] fill-hud-text-dim">E</text>
            <text x={6} y={cy + 4} textAnchor="middle" className="text-[10px] fill-hud-text-dim">W</text>
            {/* Direction line */}
            <line
              x1={cx}
              y1={cy}
              x2={lineX}
              y2={lineY}
              stroke="currentColor"
              className="text-hud-cyan"
              strokeWidth="2"
              strokeLinecap="round"
            />
            {/* Center dot */}
            <circle cx={cx} cy={cy} r={3} fill="currentColor" className="text-hud-cyan" />
          </svg>
          <span className="text-xs text-hud-cyan font-mono">{displayDeg.toFixed(0)}&deg;</span>
          {doaQuadrant && (
            <span className="text-[10px] text-hud-amber uppercase tracking-wider">{doaQuadrant}</span>
          )}
          {doaFiltered > 0 && (
            <span className="text-[10px] text-hud-text-dim font-mono">roh: {soundDirection.toFixed(0)}&deg;</span>
          )}
        </div>
      </div>

      {/* Lautsprecher (MAX98357A I2S-Verstaerker) */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              audioNodeActive
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,230,118,0.6)]'
                : 'bg-hud-red shadow-[0_0_6px_rgba(255,23,68,0.6)]'
            }`}
          />
          <span className="text-xs text-hud-text-dim uppercase tracking-wider">Lautsprecher (MAX98357A)</span>
        </div>
        <div className="flex items-center gap-2 ml-4 mb-3">
          <span className="text-xs text-hud-text-dim w-8 font-mono">{audioVolume}%</span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={audioVolume}
            onChange={(e) => sendAudioVolume(Number(e.target.value))}
            className="flex-1 h-1 accent-hud-cyan bg-hud-border rounded appearance-none cursor-pointer"
          />
        </div>
        <div className="grid grid-cols-2 gap-2 ml-4">
          {SOUND_BUTTONS.map((btn) => (
            <button
              key={btn.key}
              onClick={() => sendAudioPlay(btn.key)}
              className="px-2 py-1.5 text-xs border border-hud-border text-hud-cyan hover:bg-hud-cyan/10 transition-colors tracking-wider"
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
