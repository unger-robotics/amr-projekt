import { useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

interface EmergencyStopProps {
  onStop: () => void;
}

export function EmergencyStop({ onStop }: EmergencyStopProps) {
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
      className={`fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full
        bg-red-600 hover:bg-red-700 active:bg-red-800
        text-white font-bold text-sm
        shadow-lg shadow-red-900/50
        flex items-center justify-center
        transition-transform active:scale-95
        ${isMoving ? 'animate-pulse' : ''}`}
      aria-label="Notaus"
    >
      STOP
    </button>
  );
}
