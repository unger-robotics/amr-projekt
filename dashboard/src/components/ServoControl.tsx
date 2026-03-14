import { useState, useCallback, useRef } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

interface SliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
}

function ServoSlider({ label, value, onChange }: SliderProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs">
        <span className="text-hud-text-dim uppercase tracking-wider">{label}</span>
        <span className="text-hud-cyan font-mono">{value}&deg;</span>
      </div>
      <input
        type="range"
        min={45}
        max={135}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1 appearance-none cursor-pointer bg-hud-bg rounded-none
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
          [&::-webkit-slider-thumb]:bg-hud-cyan [&::-webkit-slider-thumb]:shadow-[0_0_6px_rgba(0,229,255,0.6)]
          [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:border-none
          [&::-moz-range-thumb]:bg-hud-cyan [&::-moz-range-thumb]:shadow-[0_0_6px_rgba(0,229,255,0.6)]
          [&::-moz-range-track]:bg-hud-bg [&::-moz-range-track]:h-1"
      />
      <div className="flex justify-between text-[10px] text-hud-text-dim">
        <span>45&deg;</span>
        <span>90&deg;</span>
        <span>135&deg;</span>
      </div>
    </div>
  );
}

interface ServoControlProps {
  sendServoCmd: (pan: number, tilt: number) => void;
  layout?: 'vertical' | 'horizontal';
}

export default function ServoControl({ sendServoCmd, layout = 'vertical' }: ServoControlProps) {
  const storePan = useTelemetryStore((s) => s.servoPan);
  const storeTilt = useTelemetryStore((s) => s.servoTilt);

  // Local overrides while user is actively dragging
  const [localPan, setLocalPan] = useState<number | null>(null);
  const [localTilt, setLocalTilt] = useState<number | null>(null);
  const panTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tiltTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Show local value during interaction, store value otherwise
  const pan = localPan ?? storePan;
  const tilt = localTilt ?? storeTilt;

  const handlePan = useCallback((v: number) => {
    setLocalPan(v);
    if (panTimer.current) clearTimeout(panTimer.current);
    panTimer.current = setTimeout(() => setLocalPan(null), 1000);
    sendServoCmd(v, localTilt ?? storeTilt);
  }, [sendServoCmd, localTilt, storeTilt]);

  const handleTilt = useCallback((v: number) => {
    setLocalTilt(v);
    if (tiltTimer.current) clearTimeout(tiltTimer.current);
    tiltTimer.current = setTimeout(() => setLocalTilt(null), 1000);
    sendServoCmd(localPan ?? storePan, v);
  }, [sendServoCmd, localPan, storePan]);

  const handleCenter = useCallback(() => {
    setLocalPan(null);
    setLocalTilt(null);
    sendServoCmd(90, 90);
  }, [sendServoCmd]);

  if (layout === 'horizontal') {
    return (
      <div className="flex items-center gap-4 text-hud-text">
        <span className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 shrink-0">Servo</span>
        <div className="flex-1 min-w-[100px]">
          <ServoSlider label="Pan" value={pan} onChange={handlePan} />
        </div>
        <div className="flex-1 min-w-[100px]">
          <ServoSlider label="Tilt" value={tilt} onChange={handleTilt} />
        </div>
        <button
          onClick={handleCenter}
          className="py-1 px-3 text-xs uppercase tracking-wider font-semibold shrink-0
            border border-hud-border text-hud-cyan hover:bg-hud-cyan/10
            transition-colors duration-150"
        >
          Mitte
        </button>
      </div>
    );
  }

  return (
    <div className="bg-hud-panel text-hud-text p-4 flex flex-col gap-4 border-t border-hud-border">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1">
        Servo (Pan/Tilt)
      </h2>

      <ServoSlider label="Pan" value={pan} onChange={handlePan} />
      <ServoSlider label="Tilt" value={tilt} onChange={handleTilt} />

      <button
        onClick={handleCenter}
        className="w-full py-1.5 text-xs uppercase tracking-wider font-semibold
          border border-hud-border text-hud-cyan hover:bg-hud-cyan/10
          transition-colors duration-150"
      >
        Zentrieren
      </button>
    </div>
  );
}
