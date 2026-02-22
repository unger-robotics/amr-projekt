import { useRef, useEffect, useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

const MAX_DISPLAY_RANGE = 4.0; // meters
const GRID_STEP = 1.0; // meters between grid circles
const POINT_RADIUS = 2;
const SENSOR_YAW_OFFSET = Math.PI; // LiDAR 180° gedreht montiert (TF: base_link→laser, yaw=π)

function rangeToColor(range: number): string {
  if (range < 1.0) return '#00e5ff';
  if (range < 2.0) return '#00b8d4';
  if (range < 3.0) return '#0097a7';
  return '#00695c';
}

export function LidarView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const scanRanges = useTelemetryStore((s) => s.scanRanges);
  const scanAngleMin = useTelemetryStore((s) => s.scanAngleMin);
  const scanAngleIncrement = useTelemetryStore((s) => s.scanAngleIncrement);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const width = rect.width;
    const height = rect.height;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.scale(dpr, dpr);

    // Clear
    ctx.fillStyle = '#0a0e17';
    ctx.fillRect(0, 0, width, height);

    const cx = width / 2;
    const cy = height / 2;
    const maxPixelRadius = Math.min(cx, cy) - 10;
    const scale = maxPixelRadius / MAX_DISPLAY_RANGE;

    // Grid circles
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.15)';
    ctx.lineWidth = 0.5;
    const gridSteps = Math.floor(MAX_DISPLAY_RANGE / GRID_STEP);
    for (let i = 1; i <= gridSteps; i++) {
      const r = i * GRID_STEP * scale;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Grid labels
    ctx.fillStyle = 'rgba(0, 229, 255, 0.4)';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    for (let i = 1; i <= gridSteps; i++) {
      ctx.fillText(`${i}m`, cx, cy - i * GRID_STEP * scale + 12);
    }

    // Cross-hair axes
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy - maxPixelRadius);
    ctx.lineTo(cx, cy + maxPixelRadius);
    ctx.moveTo(cx - maxPixelRadius, cy);
    ctx.lineTo(cx + maxPixelRadius, cy);
    ctx.stroke();

    // LiDAR points
    for (let i = 0; i < scanRanges.length; i++) {
      const range = scanRanges[i];
      if (!isFinite(range) || range <= 0 || range > MAX_DISPLAY_RANGE) continue;

      const angle = scanAngleMin + i * scanAngleIncrement + SENSOR_YAW_OFFSET;
      // Forward = up on screen. Sensor mounted 180° rotated → add π offset.
      // ROS convention: 0 rad = forward, positive = left.
      // Canvas: x-right, y-down.
      const sx = cx + range * Math.sin(angle) * scale;
      const sy = cy - range * Math.cos(angle) * scale;

      ctx.fillStyle = rangeToColor(range);
      ctx.beginPath();
      ctx.arc(sx, sy, POINT_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    }

    // Robot triangle at center (pointing up = forward) with glow
    const triSize = 8;
    ctx.save();
    ctx.shadowColor = '#00e5ff';
    ctx.shadowBlur = 8;
    ctx.fillStyle = '#00e5ff';
    ctx.beginPath();
    ctx.moveTo(cx, cy - triSize);
    ctx.lineTo(cx - triSize * 0.6, cy + triSize * 0.5);
    ctx.lineTo(cx + triSize * 0.6, cy + triSize * 0.5);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }, [scanRanges, scanAngleMin, scanAngleIncrement]);

  useEffect(() => {
    draw();
  }, [draw]);

  // Resize handling
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(() => {
      draw();
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, [draw]);

  return (
    <div ref={containerRef} className="bg-hud-bg w-full h-full relative">
      <canvas ref={canvasRef} className="absolute inset-0" />
      {/* LiDAR label */}
      <div className="absolute top-2 left-3 text-hud-cyan/60 text-[10px] uppercase tracking-widest pointer-events-none z-10">
        LIDAR RPL-A1
      </div>
    </div>
  );
}
