import { useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

interface EmergencyStopProps {
  onStop: () => void;
  inline?: boolean;
}

export function EmergencyStop({ onStop, inline }: EmergencyStopProps) {
  const velLinear = useTelemetryStore((s) => s.velLinear);
  const velAngular = useTelemetryStore((s) => s.velAngular);

  const isMoving = Math.abs(velLinear) > 0.01 || Math.abs(velAngular) > 0.01;

  const handlePress = useCallback(() => {
    // Haptic feedback if available
    if (navigator.vibrate) {
      navigator.vibrate(200);
    }
    onStop();
  }, [onStop]);

  return (
    <button
      onClick={handlePress}
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
