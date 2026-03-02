import { useRef, useEffect, useState, useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

const MARGIN_FRACTION = 0.05; // 5% Rand
const ROBOT_ARROW_SIZE = 10; // px (Dreieck-Groesse)
const ROBOT_DOT_RADIUS = 3; // px (gruener Mittelpunkt)
const ROBOT_GLOW_RADIUS = 14; // px (aeusserer Glow)
const SCALE_BAR_MARGIN = 16; // px Abstand vom Rand
const MAX_TRAIL_POINTS = 500; // Max Pfad-Punkte

export function MapView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapImageRef = useRef<HTMLImageElement | null>(null);
  const trailRef = useRef<{ x: number; y: number }[]>([]);

  const [mapVersion, setMapVersion] = useState(0);

  const mapPngB64 = useTelemetryStore((s) => s.mapPngB64);
  const mapWidth = useTelemetryStore((s) => s.mapWidth);
  const mapHeight = useTelemetryStore((s) => s.mapHeight);
  const mapResolution = useTelemetryStore((s) => s.mapResolution);
  const mapOriginX = useTelemetryStore((s) => s.mapOriginX);
  const mapOriginY = useTelemetryStore((s) => s.mapOriginY);
  const robotMapX = useTelemetryStore((s) => s.robotMapX);
  const robotMapY = useTelemetryStore((s) => s.robotMapY);
  const robotMapYaw = useTelemetryStore((s) => s.robotMapYaw);

  // Base64 PNG → HTMLImageElement
  useEffect(() => {
    if (!mapPngB64) {
      mapImageRef.current = null;
      return;
    }

    const img = new Image();
    img.onload = () => {
      mapImageRef.current = img;
      setMapVersion(v => v + 1);
    };
    img.onerror = () => {
      mapImageRef.current = null;
      setMapVersion(v => v + 1);
    };
    img.src = `data:image/png;base64,${mapPngB64}`;
  }, [mapPngB64]);

  // Roboter-Pfad aktualisieren
  useEffect(() => {
    if (robotMapX === 0 && robotMapY === 0) return;
    const trail = trailRef.current;
    const last = trail[trail.length - 1];
    // Deduplizierung: nur hinzufuegen wenn Mindestabstand 2cm
    if (last) {
      const dx = robotMapX - last.x;
      const dy = robotMapY - last.y;
      if (dx * dx + dy * dy < 0.0004) return; // < 2cm
    }
    trail.push({ x: robotMapX, y: robotMapY });
    if (trail.length > MAX_TRAIL_POINTS) {
      trail.splice(0, trail.length - MAX_TRAIL_POINTS);
    }
  }, [robotMapX, robotMapY]);

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

    const mapImg = mapImageRef.current;
    // mapVersion is used to invalidate draw when the image loads/errors
    void mapVersion;
    if (!mapImg || mapWidth === 0 || mapHeight === 0) {
      // Platzhalter
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.font = '14px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('Warte auf SLAM-Karte...', width / 2, height / 2);
      return;
    }

    // Verfuegbarer Bereich mit 5% Rand
    const margin = Math.min(width, height) * MARGIN_FRACTION;
    const availW = width - 2 * margin;
    const availH = height - 2 * margin;

    // Map skalieren (aspect-ratio beibehalten)
    const mapScale = Math.min(availW / mapWidth, availH / mapHeight);
    const drawW = mapWidth * mapScale;
    const drawH = mapHeight * mapScale;
    const offsetX = (width - drawW) / 2;
    const offsetY = (height - drawH) / 2;

    // Map zeichnen (geglaettet fuer Saugroboter-Look)
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(mapImg, offsetX, offsetY, drawW, drawH);

    // Hilfsfunktion: Map-Meter → Canvas-Pixel
    const toCanvas = (mx: number, my: number) => ({
      cx: offsetX + ((mx - mapOriginX) / mapResolution) * mapScale,
      cy: offsetY + (mapHeight - (my - mapOriginY) / mapResolution) * mapScale,
    });

    // --- Roboter-Pfad-Trail ---
    const trail = trailRef.current;
    if (trail.length > 1) {
      ctx.beginPath();
      const p0 = toCanvas(trail[0].x, trail[0].y);
      ctx.moveTo(p0.cx, p0.cy);
      for (let i = 1; i < trail.length; i++) {
        const p = toCanvas(trail[i].x, trail[i].y);
        ctx.lineTo(p.cx, p.cy);
      }
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.lineWidth = 2;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.stroke();
    }

    // Roboter-Position
    const { cx: canvasRobotX, cy: canvasRobotY } = toCanvas(robotMapX, robotMapY);

    // --- Roboter-Icon ---
    // Aeusserer Glow-Kreis (weiss)
    ctx.beginPath();
    ctx.arc(canvasRobotX, canvasRobotY, ROBOT_GLOW_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.fill();

    // Richtungspfeil (weiss)
    ctx.save();
    ctx.translate(canvasRobotX, canvasRobotY);
    ctx.rotate(-robotMapYaw); // ROS CCW positiv → Canvas CW positiv
    ctx.beginPath();
    ctx.moveTo(0, -ROBOT_ARROW_SIZE); // Spitze (vorwaerts = -Y im Canvas)
    ctx.lineTo(-ROBOT_ARROW_SIZE * 0.6, ROBOT_ARROW_SIZE * 0.5);
    ctx.lineTo(ROBOT_ARROW_SIZE * 0.6, ROBOT_ARROW_SIZE * 0.5);
    ctx.closePath();
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    // Gruener Mittelpunkt (Saugroboter-Stil)
    ctx.beginPath();
    ctx.arc(canvasRobotX, canvasRobotY, ROBOT_DOT_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = '#00e676';
    ctx.fill();

    // --- Massstabsleiste (1m, weiss) ---
    const oneMetrePixels = (1.0 / mapResolution) * mapScale;
    const barY = offsetY + drawH - SCALE_BAR_MARGIN;
    const barX = offsetX + SCALE_BAR_MARGIN;
    const endCapH = 6;

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    // Horizontale Linie
    ctx.moveTo(barX, barY);
    ctx.lineTo(barX + oneMetrePixels, barY);
    // Linke Endmarke
    ctx.moveTo(barX, barY - endCapH / 2);
    ctx.lineTo(barX, barY + endCapH / 2);
    // Rechte Endmarke
    ctx.moveTo(barX + oneMetrePixels, barY - endCapH / 2);
    ctx.lineTo(barX + oneMetrePixels, barY + endCapH / 2);
    ctx.stroke();

    // Label
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('1m', barX + oneMetrePixels / 2, barY - endCapH / 2 - 2);
  }, [
    mapVersion, mapWidth, mapHeight, mapResolution,
    mapOriginX, mapOriginY, robotMapX, robotMapY, robotMapYaw,
  ]);

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

  // Resolution als cm/px und Map-Dimensionen fuer HUD-Label
  const resolutionCm = mapResolution > 0 ? Math.round(mapResolution * 100) : 0;
  const hasMap = mapPngB64 !== null && mapWidth > 0;

  return (
    <div ref={containerRef} className="bg-hud-bg w-full h-full relative">
      <canvas ref={canvasRef} className="absolute inset-0" />
      {/* SLAM MAP label */}
      <div className="absolute top-2 left-3 text-hud-cyan/60 text-[10px] uppercase tracking-widest pointer-events-none z-10">
        SLAM MAP
      </div>
      {/* Resolution + Dimensionen */}
      {hasMap && (
        <div className="absolute top-2 right-3 text-hud-text-dim text-[10px] font-mono pointer-events-none z-10">
          {resolutionCm} cm/px | {mapWidth}x{mapHeight}
        </div>
      )}
    </div>
  );
}
