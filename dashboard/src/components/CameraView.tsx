import { useState, useCallback, useRef } from 'react';
import { useImageFit } from '../hooks/useImageFit';
import { useTelemetryStore } from '../store/telemetryStore';
import type { Detection } from '../types/ros';

const STREAM_PORT = 8082;

function confidenceColor(conf: number): string {
  if (conf >= 0.8) return 'rgb(0, 230, 118)';   // gruen
  if (conf >= 0.5) return 'rgb(249, 115, 22)';   // orange
  return 'rgb(239, 68, 68)';                      // rot
}

function DetectionBox({ det, fitW, fitH }: { det: Detection; fitW: number; fitH: number }) {
  const [x1, y1, x2, y2] = det.bbox_norm;
  const color = confidenceColor(det.confidence);

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        left: `${x1 * fitW}px`,
        top: `${y1 * fitH}px`,
        width: `${(x2 - x1) * fitW}px`,
        height: `${(y2 - y1) * fitH}px`,
        border: `1px solid ${color}`,
        boxShadow: `0 0 4px ${color}40`,
      }}
    >
      <span
        className="absolute -top-4 left-0 text-[9px] font-mono leading-none px-0.5 whitespace-nowrap"
        style={{ backgroundColor: `${color}cc`, color: '#0a0e17' }}
      >
        {det.label} {(det.confidence * 100).toFixed(0)}%
      </span>
    </div>
  );
}

interface CameraViewProps {
  sendVisionControl: (enabled: boolean) => void;
}

export function CameraView({ sendVisionControl }: CameraViewProps) {
  const [error, setError] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const fit = useImageFit(containerRef, imgRef);

  const visionEnabled = useTelemetryStore((s) => s.visionEnabled);
  const visionDetections = useTelemetryStore((s) => s.visionDetections);
  const inferenceMs = useTelemetryStore((s) => s.inferenceMs);
  const semanticAnalysis = useTelemetryStore((s) => s.semanticAnalysis);
  const semanticFusionSources = useTelemetryStore((s) => s.semanticFusionSources);

  const streamProtocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
  const streamUrl = `${streamProtocol}//${window.location.hostname}:${STREAM_PORT}/stream`;

  const handleError = useCallback(() => {
    setError(true);
  }, []);

  const handleLoad = useCallback(() => {
    setError(false);
  }, []);

  return (
    <div ref={containerRef} className="bg-hud-bg flex items-center justify-center w-full h-full relative overflow-hidden">
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
          ref={imgRef}
          src={streamUrl}
          alt="Kamera-Stream"
          className="max-w-full max-h-full object-contain rotate-180"
          onError={handleError}
          onLoad={handleLoad}
        />
      )}

      {/* BBox Overlay — nur wenn Vision aktiviert */}
      {visionEnabled && !error && fit.width > 0 && visionDetections.length > 0 && (
        <div
          className="absolute pointer-events-none"
          style={{
            left: `${fit.offsetX}px`,
            top: `${fit.offsetY}px`,
            width: `${fit.width}px`,
            height: `${fit.height}px`,
          }}
        >
          {visionDetections.map((det, i) => (
            <DetectionBox key={i} det={det} fitW={fit.width} fitH={fit.height} />
          ))}
        </div>
      )}

      {/* Inference HUD Label — nur wenn Vision aktiviert */}
      {visionEnabled && inferenceMs > 0 && (
        <div className="absolute top-2 right-7 text-[10px] font-mono uppercase tracking-widest pointer-events-none text-orange-400/70">
          HAILO {inferenceMs.toFixed(0)} MS
        </div>
      )}

      {/* Gemini Semantic Streifen — nur wenn Vision aktiviert */}
      {visionEnabled && semanticAnalysis && (
        <div className="absolute bottom-0 left-0 right-0 bg-hud-bg/70 backdrop-blur-sm px-2 py-1 pointer-events-none">
          <div className="flex items-center gap-1.5">
            {semanticFusionSources.length > 2 && (
              <span className="text-[8px] font-mono text-hud-green/70 uppercase shrink-0">
                FUSION
              </span>
            )}
            <p className="text-[10px] font-mono text-hud-cyan/80 line-clamp-2 leading-tight">
              {semanticAnalysis}
            </p>
          </div>
        </div>
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

      {/* AI Vision Toggle */}
      <button
        onClick={() => sendVisionControl(!visionEnabled)}
        className={`absolute top-2 left-[6.5rem] text-[10px] font-mono uppercase tracking-widest px-1.5 py-0.5 border transition-colors z-10
          ${visionEnabled
            ? 'text-orange-400 border-orange-400/50 bg-orange-400/10'
            : 'text-hud-text-dim border-hud-border bg-hud-bg/50 hover:text-hud-text'
          }`}
      >
        AI {visionEnabled ? 'ON' : 'OFF'}
      </button>
    </div>
  );
}
