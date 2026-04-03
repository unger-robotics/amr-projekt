import { useRef, useEffect, useState, useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

const MARGIN_FRACTION = 0.05; // 5% Rand
const ROBOT_ARROW_SIZE = 10; // px (Dreieck-Groesse)
const ROBOT_DOT_RADIUS = 3; // px (gruener Mittelpunkt)
const ROBOT_GLOW_RADIUS = 14; // px (aeusserer Glow)
const SCALE_BAR_MARGIN = 16; // px Abstand vom Rand
const MAX_TRAIL_POINTS = 500; // Max Pfad-Punkte
const GOAL_MARKER_SIZE = 8; // px (Ziel-Marker)
const US_FOV_HALF = 0.13; // rad (halber Oeffnungswinkel HC-SR04, ~15° gesamt)
const US_MAX_RANGE = 4.0; // m

interface MapViewProps {
  onNavGoal?: (x: number, y: number, yaw: number) => void;
  navStatus?: 'idle' | 'navigating' | 'reached' | 'failed' | 'cancelled';
  navGoalX?: number;
  navGoalY?: number;
}

export function MapView({ onNavGoal, navStatus, navGoalX, navGoalY }: MapViewProps = {}) {
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
  const ultrasonicRange = useTelemetryStore((s) => s.ultrasonicRange);

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

    // Hilfsfunktion: Map-Meter → Canvas-Pixel
    const toCanvas = (mx: number, my: number) => ({
      cx: offsetX + ((mx - mapOriginX) / mapResolution) * mapScale,
      cy: offsetY + (mapHeight - (my - mapOriginY) / mapResolution) * mapScale,
    });

    // Roboter-Position auf Canvas (vor Rotation berechnen)
    const { cx: canvasRobotX, cy: canvasRobotY } = toCanvas(robotMapX, robotMapY);

    // --- Heading-Up: Karte drehen, Fahrtrichtung = oben (wie LiDAR-Ansicht) ---
    // Roboter-Heading (Canvas-Winkel -yaw) soll nach oben (-PI/2) zeigen
    ctx.save();
    ctx.translate(canvasRobotX, canvasRobotY);
    ctx.rotate(robotMapYaw - Math.PI / 2);
    ctx.translate(-canvasRobotX, -canvasRobotY);

    // Map zeichnen (rotiert mit Karte)
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(mapImg, offsetX, offsetY, drawW, drawH);

    // --- Roboter-Pfad-Trail (rotiert mit Karte) ---
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

    // --- Navigationsziel-Marker (rotiert mit Karte) ---
    if (navStatus === 'navigating' && navGoalX !== undefined && navGoalY !== undefined) {
      const { cx: goalCx, cy: goalCy } = toCanvas(navGoalX, navGoalY);
      ctx.beginPath();
      ctx.arc(goalCx, goalCy, GOAL_MARKER_SIZE + 4, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(0, 230, 118, 0.4)';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(goalCx, goalCy, GOAL_MARKER_SIZE, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0, 230, 118, 0.6)';
      ctx.fill();
      ctx.strokeStyle = '#00e676';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(goalCx - 4, goalCy);
      ctx.lineTo(goalCx + 4, goalCy);
      ctx.moveTo(goalCx, goalCy - 4);
      ctx.lineTo(goalCx, goalCy + 4);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    ctx.restore();
    // --- Ende Heading-Up ---

    // --- Roboter-Icon (Heading-Up: Pfeil zeigt immer nach oben) ---
    ctx.beginPath();
    ctx.arc(canvasRobotX, canvasRobotY, ROBOT_GLOW_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.fill();

    ctx.save();
    ctx.translate(canvasRobotX, canvasRobotY);
    ctx.beginPath();
    ctx.moveTo(0, -ROBOT_ARROW_SIZE);
    ctx.lineTo(-ROBOT_ARROW_SIZE * 0.6, ROBOT_ARROW_SIZE * 0.5);
    ctx.lineTo(ROBOT_ARROW_SIZE * 0.6, ROBOT_ARROW_SIZE * 0.5);
    ctx.closePath();
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    ctx.beginPath();
    ctx.arc(canvasRobotX, canvasRobotY, ROBOT_DOT_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = '#00e676';
    ctx.fill();

    // --- Ultraschall-Kegel (Heading-Up: vorwaerts = oben, -PI/2) ---
    if (ultrasonicRange > 0 && ultrasonicRange < US_MAX_RANGE && mapResolution > 0) {
      const pixPerMeter = mapScale / mapResolution;
      const coneLen = Math.min(ultrasonicRange, US_MAX_RANGE) * pixPerMeter;
      // Farbe nach Entfernung: gruen >0.5m, amber 0.1-0.5m, rot <0.1m
      let coneFill: string;
      let coneStroke: string;
      if (ultrasonicRange < 0.1) {
        coneFill = 'rgba(255, 42, 64, 0.18)';
        coneStroke = 'rgba(255, 42, 64, 0.6)';
      } else if (ultrasonicRange < 0.5) {
        coneFill = 'rgba(255, 176, 0, 0.14)';
        coneStroke = 'rgba(255, 176, 0, 0.5)';
      } else {
        coneFill = 'rgba(0, 255, 102, 0.10)';
        coneStroke = 'rgba(0, 255, 102, 0.35)';
      }
      ctx.save();
      ctx.translate(canvasRobotX, canvasRobotY);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      // Heading-Up: vorwaerts = -PI/2 (oben auf dem Bildschirm)
      ctx.arc(0, 0, coneLen, -Math.PI / 2 - US_FOV_HALF, -Math.PI / 2 + US_FOV_HALF);
      ctx.closePath();
      ctx.fillStyle = coneFill;
      ctx.fill();
      ctx.strokeStyle = coneStroke;
      ctx.lineWidth = 1;
      ctx.stroke();
      // Reichweite-Label am Kegelende
      ctx.fillStyle = coneStroke;
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(`${(ultrasonicRange * 100).toFixed(0)}cm`, 0, -coneLen - 3);
      ctx.restore();
    }

    // --- Massstabsleiste (1m, bildschirmfest) ---
    const oneMetrePixels = (1.0 / mapResolution) * mapScale;
    const barY = height - SCALE_BAR_MARGIN;
    const barX = SCALE_BAR_MARGIN;
    const endCapH = 6;

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(barX, barY);
    ctx.lineTo(barX + oneMetrePixels, barY);
    ctx.moveTo(barX, barY - endCapH / 2);
    ctx.lineTo(barX, barY + endCapH / 2);
    ctx.moveTo(barX + oneMetrePixels, barY - endCapH / 2);
    ctx.lineTo(barX + oneMetrePixels, barY + endCapH / 2);
    ctx.stroke();

    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('1m', barX + oneMetrePixels / 2, barY - endCapH / 2 - 2);
  }, [
    mapVersion, mapWidth, mapHeight, mapResolution,
    mapOriginX, mapOriginY, robotMapX, robotMapY, robotMapYaw,
    navStatus, navGoalX, navGoalY, ultrasonicRange,
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

  // Klick auf Karte -> Navigationsziel setzen
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onNavGoal || !mapImageRef.current || mapWidth === 0 || mapHeight === 0) return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    const width = rect.width;
    const height = rect.height;

    const margin = Math.min(width, height) * MARGIN_FRACTION;
    const availW = width - 2 * margin;
    const availH = height - 2 * margin;
    const mapScale = Math.min(availW / mapWidth, availH / mapHeight);
    const drawW = mapWidth * mapScale;
    const drawH = mapHeight * mapScale;
    const offsetX = (width - drawW) / 2;
    const offsetY = (height - drawH) / 2;

    // Roboter-Canvas-Position berechnen
    const canvasRobotX = offsetX + ((robotMapX - mapOriginX) / mapResolution) * mapScale;
    const canvasRobotY = offsetY + (mapHeight - (robotMapY - mapOriginY) / mapResolution) * mapScale;

    // Heading-Up-Rotation rueckgaengig machen (Klick → Weltkarte)
    const headingRot = robotMapYaw - Math.PI / 2;
    const cosR = Math.cos(-headingRot);
    const sinR = Math.sin(-headingRot);
    const cdx = clickX - canvasRobotX;
    const cdy = clickY - canvasRobotY;
    const unrotX = canvasRobotX + cdx * cosR - cdy * sinR;
    const unrotY = canvasRobotY + cdx * sinR + cdy * cosR;

    // Canvas-Pixel -> Map-Meter (Inverse von toCanvas)
    const mapX = ((unrotX - offsetX) / mapScale) * mapResolution + mapOriginX;
    const mapY = ((mapHeight - (unrotY - offsetY) / mapScale)) * mapResolution + mapOriginY;

    // Yaw zum Roboter hin berechnen
    const dx = mapX - robotMapX;
    const dy = mapY - robotMapY;
    const yaw = Math.atan2(dy, dx);

    onNavGoal(mapX, mapY, yaw);
  }, [onNavGoal, mapWidth, mapHeight, mapResolution, mapOriginX, mapOriginY, robotMapX, robotMapY, robotMapYaw]);

  // Resolution als cm/px und Map-Dimensionen fuer HUD-Label
  const resolutionCm = mapResolution > 0 ? Math.round(mapResolution * 100) : 0;
  const hasMap = mapPngB64 !== null && mapWidth > 0;

  return (
    <div ref={containerRef} className="bg-hud-bg w-full h-full relative">
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 ${onNavGoal ? 'cursor-crosshair' : ''}`}
        onClick={handleCanvasClick}
      />
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
