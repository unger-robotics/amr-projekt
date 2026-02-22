import { useState, useCallback } from 'react';

const STREAM_PORT = 8082;

export function CameraView() {
  const [error, setError] = useState(false);

  const streamUrl = `http://${window.location.hostname}:${STREAM_PORT}/stream`;

  const handleError = useCallback(() => {
    setError(true);
  }, []);

  const handleLoad = useCallback(() => {
    setError(false);
  }, []);

  return (
    <div className="bg-hud-bg flex items-center justify-center w-full h-full relative overflow-hidden">
      {error ? (
        <div className="flex flex-col items-center gap-2 text-hud-text-dim">
          <svg
            className="w-12 h-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9A2.25 2.25 0 0013.5 5.25h-9A2.25 2.25 0 002.25 7.5v9A2.25 2.25 0 004.5 18.75z"
            />
          </svg>
          <span className="text-sm">Kamera offline</span>
        </div>
      ) : (
        <img
          src={streamUrl}
          alt="Kamera-Stream"
          className="w-full h-full object-contain"
          style={{ aspectRatio: '4 / 3' }}
          onError={handleError}
          onLoad={handleLoad}
        />
      )}

      {/* HUD Overlay Elements (pointer-events-none) */}
      {/* Scanline overlay */}
      <div className="absolute inset-0 hud-scanline pointer-events-none" />

      {/* Crosshair - vertical */}
      <div className="absolute top-0 bottom-0 left-1/2 w-px bg-hud-cyan/20 pointer-events-none" />
      {/* Crosshair - horizontal */}
      <div className="absolute left-0 right-0 top-1/2 h-px bg-hud-cyan/20 pointer-events-none" />

      {/* Corner brackets */}
      <div className="absolute top-3 left-3 w-5 h-5 border-t border-l border-hud-cyan/50 pointer-events-none" />
      <div className="absolute top-3 right-3 w-5 h-5 border-t border-r border-hud-cyan/50 pointer-events-none" />
      <div className="absolute bottom-3 left-3 w-5 h-5 border-b border-l border-hud-cyan/50 pointer-events-none" />
      <div className="absolute bottom-3 right-3 w-5 h-5 border-b border-r border-hud-cyan/50 pointer-events-none" />

      {/* Camera label */}
      <div className="absolute top-2 left-7 text-hud-cyan/60 text-[10px] uppercase tracking-widest pointer-events-none">
        CAM IMX296
      </div>
    </div>
  );
}
