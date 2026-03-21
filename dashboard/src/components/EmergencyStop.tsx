import { useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

interface EmergencyStopProps {
  onStop: () => void;
  onRelease: () => void;
  inline?: boolean;
}

export function EmergencyStop({ onStop, onRelease, inline }: EmergencyStopProps) {
  const velLinear = useTelemetryStore((s) => s.velLinear);
  const velAngular = useTelemetryStore((s) => s.velAngular);
  const engaged = useTelemetryStore((s) => s.estopEngaged);
  const source = useTelemetryStore((s) => s.estopSource);

  const isMoving = Math.abs(velLinear) > 0.01 || Math.abs(velAngular) > 0.01;

  const handleStop = useCallback(() => {
    if (navigator.vibrate) {
      navigator.vibrate(200);
    }
    onStop();
  }, [onStop]);

  const handleRelease = useCallback(() => {
    if (navigator.vibrate) {
      navigator.vibrate(100);
    }
    onRelease();
  }, [onRelease]);

  if (engaged) {
    return (
      <div className={`flex items-center gap-1.5 ${inline ? '' : 'flex-col'}`}>
        <div
          className={`${inline ? 'w-12 h-12 text-[9px]' : 'w-20 h-20 text-sm'}
            bg-hud-red
            border-2 border-white/60
            text-white font-bold
            shadow-[0_0_30px_rgba(255,23,68,0.6)]
            flex items-center justify-center shrink-0
            animate-pulse`}
        >
          E-STOP
        </div>
        <button
          onClick={handleRelease}
          className={`${inline ? 'px-2 py-1 text-[9px]' : 'px-3 py-1.5 text-xs'}
            bg-hud-amber/20 hover:bg-hud-amber/40
            border border-hud-amber/50
            text-hud-amber font-bold uppercase
            transition-colors`}
          title={`Quelle: ${source}`}
        >
          Freigabe
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleStop}
      className={`${inline ? 'w-12 h-12 text-sm' : 'w-20 h-20 text-lg'}
        bg-hud-red hover:bg-red-700 active:bg-red-800
        border border-hud-red/50
        text-white font-bold
        shadow-[0_0_20px_rgba(255,23,68,0.3)]
        flex items-center justify-center shrink-0
        transition-transform active:scale-95
        ${isMoving ? 'animate-pulse' : ''}`}
      aria-label="Notaus"
    >
      STOP
    </button>
  );
}
