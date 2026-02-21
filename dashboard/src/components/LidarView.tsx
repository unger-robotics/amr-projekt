import { useRef, useEffect, useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

const MAX_DISPLAY_RANGE = 4.0; // meters
const GRID_STEP = 1.0; // meters between grid circles
const POINT_RADIUS = 2;

function rangeToColor(range: number): string {
  if (range < 1.0) return '#ef4444'; // red-500
  if (range < 2.0) return '#eab308'; // yellow-500
  return '#22c55e'; // green-500
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
    ctx.fillStyle = '#030712'; // gray-950
    ctx.fillRect(0, 0, width, height);

    const cx = width / 2;
    const cy = height / 2;
    const maxPixelRadius = Math.min(cx, cy) - 10;
    const scale = maxPixelRadius / MAX_DISPLAY_RANGE;

    // Grid circles
    ctx.strokeStyle = '#374151'; // gray-700
    ctx.lineWidth = 0.5;
    const gridSteps = Math.floor(MAX_DISPLAY_RANGE / GRID_STEP);
    for (let i = 1; i <= gridSteps; i++) {
      const r = i * GRID_STEP * scale;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Grid labels
    ctx.fillStyle = '#6b7280'; // gray-500
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    for (let i = 1; i <= gridSteps; i++) {
      ctx.fillText(`${i}m`, cx, cy - i * GRID_STEP * scale + 12);
    }

    // Cross-hair axes
    ctx.strokeStyle = '#374151';
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

      const angle = scanAngleMin + i * scanAngleIncrement;
      // Forward = up on screen. ROS convention: 0 rad = forward, positive = left.
      // Canvas: x-right, y-down.
      // screen_x = cx + range * sin(angle) * scale   (sin because left-positive maps to screen-right for negative angles)
      // screen_y = cy - range * cos(angle) * scale   (cos maps forward to screen-up)
      const sx = cx + range * Math.sin(angle) * scale;
      const sy = cy - range * Math.cos(angle) * scale;

      ctx.fillStyle = rangeToColor(range);
      ctx.beginPath();
      ctx.arc(sx, sy, POINT_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    }

    // Robot triangle at center (pointing up = forward)
    const triSize = 8;
    ctx.fillStyle = '#3b82f6'; // blue-500
    ctx.beginPath();
    ctx.moveTo(cx, cy - triSize);
    ctx.lineTo(cx - triSize * 0.6, cy + triSize * 0.5);
    ctx.lineTo(cx + triSize * 0.6, cy + triSize * 0.5);
    ctx.closePath();
    ctx.fill();
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
    <div ref={containerRef} className="bg-gray-950 w-full h-full relative">
      <canvas ref={canvasRef} className="absolute inset-0" />
    </div>
  );
}
