import { useState } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';
import type { ClientMessage } from '../types/ros';

/* ── Hilfskomponenten ─────────────────────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        {title}
      </h2>
      {children}
    </div>
  );
}

function StatusDot({ color, pulse }: { color: string; pulse?: boolean }) {
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${color} ${pulse ? 'animate-pulse' : ''}`}
    />
  );
}

function LaunchBadge({ text }: { text: string }) {
  return (
    <span className="text-[9px] font-mono px-1.5 py-0.5 border border-hud-border/40 text-hud-text-dim bg-hud-bg">
      {text}
    </span>
  );
}

/* ── Vordefinierte Missionen ─────────────────────────────────────── */

interface Mission {
  label: string;
  description: string;
  action: 'nav_goal' | 'test_run' | 'command';
  /** Fuer nav_goal: [x, y, yaw_rad] */
  navGoal?: [number, number, number];
  /** Fuer test_run: test_key */
  testKey?: string;
  /** Fuer command: Freitextbefehl */
  commandText?: string;
}

const MISSIONS: Mission[] = [
  {
    label: '1 m geradeaus',
    description: '1 m vorwaerts mit Odometrie-Regelung',
    action: 'command',
    commandText: 'forward 1.0',
  },
  {
    label: '1 m zurueck',
    description: '1 m rueckwaerts fahren',
    action: 'command',
    commandText: 'backward 1.0',
  },
  {
    label: '90° links',
    description: 'Drehung 90° gegen den Uhrzeigersinn',
    action: 'command',
    commandText: 'turn 90',
  },
  {
    label: '90° rechts',
    description: 'Drehung 90° im Uhrzeigersinn',
    action: 'command',
    commandText: 'turn -90',
  },
  {
    label: '360° Drehung',
    description: 'Volle Drehung, IMU-geregelt',
    action: 'command',
    commandText: 'turn 360',
  },
  {
    label: 'Quadratfahrt (Nav2)',
    description: '1 m x 1 m Rechteck ueber Nav2-Wegpunkte',
    action: 'test_run',
    testKey: 'nav',
  },
  {
    label: 'Quadratfahrt (Odom)',
    description: '1 m x 1 m Rechteck ueber Odometrie',
    action: 'test_run',
    testKey: 'nav_square',
  },
];

/* ── Aufgaben-Karten ─────────────────────────────────────────────── */

function NavigationCard({
  send,
  sendNavGoal,
  sendNavCancel,
}: {
  send: (msg: ClientMessage) => void;
  sendNavGoal: (x: number, y: number, yaw: number) => void;
  sendNavCancel: () => void;
}) {
  const navStatus = useTelemetryStore((s) => s.navStatus);
  const navRemainingM = useTelemetryStore((s) => s.navRemainingM);
  const runningTest = useTelemetryStore((s) => s.runningTest);
  const [goalX, setGoalX] = useState(0);
  const [goalY, setGoalY] = useState(0);
  const [goalYaw, setGoalYaw] = useState(0);
  const [showCoords, setShowCoords] = useState(false);

  const isNavigating = navStatus === 'navigating';
  const isBusy = isNavigating || runningTest !== null;

  const dotColor =
    navStatus === 'navigating' ? 'bg-hud-cyan' :
    navStatus === 'reached' ? 'bg-hud-green' :
    navStatus === 'failed' ? 'bg-hud-red' :
    navStatus === 'cancelled' ? 'bg-hud-amber' :
    'bg-hud-text-dim';

  const statusText =
    navStatus === 'navigating' ? `Navigiert ... ${navRemainingM.toFixed(2)} m verbleibend` :
    navStatus === 'reached' ? 'Ziel erreicht' :
    navStatus === 'failed' ? 'Navigation fehlgeschlagen' :
    navStatus === 'cancelled' ? 'Abgebrochen' :
    'Bereit';

  const executeMission = (m: Mission) => {
    if (m.action === 'nav_goal' && m.navGoal) {
      sendNavGoal(m.navGoal[0], m.navGoal[1], m.navGoal[2]);
    } else if (m.action === 'test_run' && m.testKey) {
      send({ op: 'test_run', test_key: m.testKey });
    } else if (m.action === 'command' && m.commandText) {
      send({ op: 'command', text: m.commandText });
    }
  };

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2 md:col-span-2 lg:col-span-3">
      <div className="flex items-center gap-2">
        <StatusDot color={dotColor} pulse={isNavigating} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          Autonome Navigation (Nav2)
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        Der Nav2-Stack stellt autonome Zielnavigation bereit. Zielpunkte koennen ueber
        Kartenklick im Steuerung-Tab, per Koordinaten-Eingabe oder als vordefinierte
        Mission gesetzt werden. Die Cliff-Safety-Node ueberwacht alle Fahrbefehle und
        blockiert bei Abgrunderkennung oder Hindernis unter 80 mm automatisch.
      </p>
      <p className="text-[10px] font-mono text-hud-text">{statusText}</p>

      {/* Vordefinierte Missionen */}
      <div className="mt-1">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-hud-cyan/50 mb-1.5">
          Schnellstart-Missionen
        </div>
        <div className="flex flex-wrap gap-1.5">
          {MISSIONS.map((m) => (
            <button
              key={m.label}
              type="button"
              title={m.description}
              onClick={() => executeMission(m)}
              disabled={isBusy}
              className="text-[10px] font-mono px-2.5 py-1 border border-hud-border text-hud-text hover:bg-hud-cyan/10 hover:border-hud-cyan/40 hover:text-hud-cyan disabled:text-hud-text-dim disabled:cursor-not-allowed transition-colors"
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Koordinaten-Eingabe (aufklappbar) */}
      <div className="mt-1">
        <button
          type="button"
          onClick={() => setShowCoords(!showCoords)}
          className="text-[10px] text-hud-cyan/50 hover:text-hud-cyan transition-colors uppercase tracking-wider"
        >
          {showCoords ? '- Koordinaten ausblenden' : '+ Koordinaten-Eingabe'}
        </button>
        {showCoords && (
          <div className="mt-2 space-y-2">
            <div className="grid grid-cols-3 gap-2 max-w-md">
              <input
                type="number"
                step="0.1"
                value={goalX}
                onChange={(e) => setGoalX(parseFloat(e.target.value) || 0)}
                className="w-full bg-hud-bg border border-hud-border text-hud-text text-xs font-mono px-2 py-1 placeholder:text-hud-text-dim/40 focus:border-hud-cyan focus:outline-none"
                placeholder="X (m)"
              />
              <input
                type="number"
                step="0.1"
                value={goalY}
                onChange={(e) => setGoalY(parseFloat(e.target.value) || 0)}
                className="w-full bg-hud-bg border border-hud-border text-hud-text text-xs font-mono px-2 py-1 placeholder:text-hud-text-dim/40 focus:border-hud-cyan focus:outline-none"
                placeholder="Y (m)"
              />
              <input
                type="number"
                step="1"
                value={goalYaw}
                onChange={(e) => setGoalYaw(parseFloat(e.target.value) || 0)}
                className="w-full bg-hud-bg border border-hud-border text-hud-text text-xs font-mono px-2 py-1 placeholder:text-hud-text-dim/40 focus:border-hud-cyan focus:outline-none"
                placeholder="Yaw (\u00b0)"
              />
            </div>
            <button
              type="button"
              onClick={() => sendNavGoal(goalX, goalY, (goalYaw * Math.PI) / 180)}
              disabled={isBusy}
              className="text-xs px-3 py-1.5 border border-hud-cyan text-hud-cyan hover:bg-hud-cyan/10 disabled:text-hud-text-dim disabled:border-hud-border disabled:cursor-not-allowed transition-colors uppercase tracking-wider"
            >
              Navigieren
            </button>
          </div>
        )}
      </div>

      {/* Abbrechen-Button wenn aktiv */}
      {isNavigating && (
        <div className="mt-1">
          <button
            type="button"
            onClick={sendNavCancel}
            className="text-xs px-3 py-1.5 border border-hud-red text-hud-red hover:bg-hud-red/20 transition-colors uppercase tracking-wider"
          >
            Navigation abbrechen
          </button>
        </div>
      )}

      <div className="flex flex-wrap gap-1 mt-1">
        <LaunchBadge text="use_nav:=True" />
        <LaunchBadge text="use_slam:=True" />
      </div>
    </div>
  );
}

function SlamCard() {
  const mapPngB64 = useTelemetryStore((s) => s.mapPngB64);
  const mapWidth = useTelemetryStore((s) => s.mapWidth);
  const mapHeight = useTelemetryStore((s) => s.mapHeight);
  const mapResolution = useTelemetryStore((s) => s.mapResolution);

  const active = !!mapPngB64;

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <StatusDot color={active ? 'bg-hud-green' : 'bg-hud-text-dim'} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          SLAM-Kartierung
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        SLAM Toolbox erstellt und aktualisiert die Umgebungskarte in Echtzeit.
        Die Validierung berechnet den Absolute Trajectory Error zwischen
        SLAM-korrigierter Pose und reiner Odometrie.
      </p>
      <p className="text-[10px] font-mono text-hud-text">
        {active
          ? `Karte aktiv: ${mapWidth}\u00d7${mapHeight} @ ${mapResolution} m/px`
          : 'Warte auf SLAM-Daten...'}
      </p>
      <div className="flex flex-wrap gap-1">
        <LaunchBadge text="use_slam:=True" />
      </div>
    </div>
  );
}

function CliffCard() {
  const cliffDetected = useTelemetryStore((s) => s.cliffDetected);
  const ultrasonicRange = useTelemetryStore((s) => s.ultrasonicRange);
  const sensorNodeActive = useTelemetryStore((s) => s.sensorNodeActive);

  const obstacleTooClose = ultrasonicRange > 0 && ultrasonicRange < 0.10;
  const dotColor = !sensorNodeActive
    ? 'bg-hud-text-dim'
    : cliffDetected
      ? 'bg-hud-red'
      : obstacleTooClose
        ? 'bg-hud-amber'
        : 'bg-hud-green';

  const rangeMMDisplay = (ultrasonicRange * 1000).toFixed(0);

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <StatusDot color={dotColor} pulse={cliffDetected || obstacleTooClose} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          Cliff Detection
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        Der cliff_safety_node multiplext alle Fahrbefehle und blockiert bei
        Abgrunderkennung mit 20 Hz Null-Twist. Zusaetzlich greift die
        Ultraschall-Hinderniserkennung mit Hysterese.
      </p>
      <p className="text-[10px] font-mono text-hud-text">
        {!sensorNodeActive
          ? 'Sensor-Node inaktiv'
          : cliffDetected
            ? 'KANTE ERKANNT \u2014 Fahrbefehle blockiert'
            : obstacleTooClose
              ? `HINDERNIS bei ${rangeMMDisplay} mm \u2014 Vorwaertsfahrt blockiert`
              : `Sicher \u2014 Ultraschall: ${rangeMMDisplay} mm`}
      </p>
      <p className="text-[9px] text-hud-text-dim">
        Stopp &lt; 100 mm | Freigabe &gt; 140 mm (Hysterese)
      </p>
    </div>
  );
}

function DockingCard({ send }: { send: (msg: ClientMessage) => void }) {
  const runningTest = useTelemetryStore((s) => s.runningTest);
  const isDocking = runningTest === 'docking';

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <StatusDot color={isDocking ? 'bg-hud-amber' : 'bg-hud-text-dim'} pulse={isDocking} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          ArUco-Docking
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        ArUco-Marker-basiertes Docking fuer die Ladestation. Der Roboter sucht
        den Marker (ID 42), zentriert sich per P-Regler und faehrt per
        Ultraschall-Distanz bis auf 30 cm an.
      </p>
      <p className="text-[10px] font-mono text-hud-text">
        {isDocking ? 'Docking laeuft...' : 'Bereit'}
      </p>
      <div className="flex gap-2">
        {isDocking ? (
          <button
            type="button"
            onClick={() => send({ op: 'test_stop' })}
            className="text-xs px-3 py-1.5 border border-hud-red text-hud-red hover:bg-hud-red/20 transition-colors uppercase tracking-wider"
          >
            Stoppen
          </button>
        ) : (
          <button
            type="button"
            onClick={() => send({ op: 'test_run', test_key: 'docking' })}
            disabled={runningTest !== null}
            className="text-xs px-3 py-1.5 border border-hud-cyan text-hud-cyan hover:bg-hud-cyan/10 disabled:text-hud-text-dim disabled:border-hud-border disabled:cursor-not-allowed transition-colors uppercase tracking-wider"
          >
            Docking starten
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-1">
        <LaunchBadge text="use_camera:=True" />
      </div>
    </div>
  );
}

function VisionCard({
  sendVisionControl,
}: {
  sendVisionControl: (enabled: boolean) => void;
}) {
  const visionEnabled = useTelemetryStore((s) => s.visionEnabled);
  const detectionHz = useTelemetryStore((s) => s.detectionHz);
  const inferenceMs = useTelemetryStore((s) => s.inferenceMs);
  const hailoDetected = useTelemetryStore((s) => s.hailoDetected);
  const cameraActive = useTelemetryStore((s) => s.cameraActive);

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <StatusDot color={visionEnabled ? 'bg-hud-green' : 'bg-hud-text-dim'} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          KI-Objekterkennung
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        Der host_hailo_runner fuehrt YOLOv8-Inferenz via Hailo-8L NPU bei 5 Hz
        aus und sendet Detektionen per UDP an den Docker-Container.
      </p>
      <p className="text-[10px] font-mono text-hud-text">
        {visionEnabled
          ? `Aktiv \u2014 ${detectionHz.toFixed(1)} Hz, ${inferenceMs.toFixed(0)} ms Inferenz`
          : 'Deaktiviert'}
      </p>
      {(!hailoDetected || !cameraActive) && (
        <p className="text-[10px] text-hud-amber">
          {!cameraActive && !hailoDetected
            ? 'Kamera + Hailo nicht erkannt'
            : !cameraActive
              ? 'Kamera nicht erkannt'
              : 'Hailo nicht erkannt'}
        </p>
      )}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => sendVisionControl(!visionEnabled)}
          className={`text-xs px-3 py-1.5 border transition-colors uppercase tracking-wider ${
            visionEnabled
              ? 'border-hud-amber text-hud-amber hover:bg-hud-amber/10'
              : 'border-hud-cyan text-hud-cyan hover:bg-hud-cyan/10'
          }`}
        >
          {visionEnabled ? 'Deaktivieren' : 'Aktivieren'}
        </button>
      </div>
      <div className="flex flex-wrap gap-1">
        <LaunchBadge text="use_vision:=True" />
        <LaunchBadge text="use_camera:=True" />
      </div>
    </div>
  );
}

function SemanticsCard() {
  const semanticAnalysis = useTelemetryStore((s) => s.semanticAnalysis);
  const visionEnabled = useTelemetryStore((s) => s.visionEnabled);

  const active = visionEnabled && semanticAnalysis.length > 0;
  const truncated =
    semanticAnalysis.length > 100
      ? semanticAnalysis.slice(0, 100) + '...'
      : semanticAnalysis;

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <StatusDot color={active ? 'bg-hud-green' : 'bg-hud-text-dim'} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          Semantische Szenenanalyse
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        Der gemini_semantic_node wertet YOLOv8-Detektionen ueber die Gemini
        Cloud API aus (nur bei aktiviertem AI-Toggle) und publiziert
        semantische Beschreibungen auf Deutsch.
      </p>
      <p className="text-[10px] font-mono text-hud-text">
        {active ? truncated : 'Warte auf Vision-Pipeline...'}
      </p>
      <div className="flex flex-wrap gap-1">
        <LaunchBadge text="use_vision:=True" />
        <LaunchBadge text="GEMINI_API_KEY" />
      </div>
    </div>
  );
}

function TtsCard({ send }: { send: (msg: ClientMessage) => void }) {
  const audioNodeActive = useTelemetryStore((s) => s.audioNodeActive);

  return (
    <div className="bg-hud-bg border border-hud-border p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <StatusDot color={audioNodeActive ? 'bg-hud-green' : 'bg-hud-text-dim'} />
        <span className="text-xs font-semibold text-hud-text uppercase tracking-wider">
          Text-to-Speech
        </span>
      </div>
      <p className="text-[10px] text-hud-text-dim leading-relaxed">
        Der tts_speak_node subscribt /vision/semantics und spricht die
        Szenenanalyse ueber den MAX98357A-I2S-Lautsprecher via gTTS
        auf Deutsch aus, mit Rate-Limiting von maximal alle 10 Sekunden.
      </p>
      <p className="text-[10px] font-mono text-hud-text">
        {audioNodeActive ? 'Audio-Node aktiv' : 'Audio-Node inaktiv'}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => send({ op: 'tts_test', text: 'Hallo, ich bin ein autonomer mobiler Roboter' })}
          disabled={!audioNodeActive}
          className="text-xs px-3 py-1.5 border border-hud-cyan text-hud-cyan hover:bg-hud-cyan/10 disabled:text-hud-text-dim disabled:border-hud-border disabled:cursor-not-allowed transition-colors uppercase tracking-wider"
        >
          Test-Ansage
        </button>
      </div>
      <div className="flex flex-wrap gap-1">
        <LaunchBadge text="use_tts:=True" />
        <LaunchBadge text="use_audio:=True" />
      </div>
    </div>
  );
}

/* ── Hauptkomponente ──────────────────────────────────────────────── */

interface AufgabenPageProps {
  send: (msg: ClientMessage) => void;
  sendNavGoal: (x: number, y: number, yaw: number) => void;
  sendNavCancel: () => void;
  sendVisionControl: (enabled: boolean) => void;
}

export default function AufgabenPage({
  send,
  sendNavGoal,
  sendNavCancel,
  sendVisionControl,
}: AufgabenPageProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-5xl mx-auto space-y-4">
        {/* Kernfunktionen */}
        <Section title="Kernfunktionen">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <NavigationCard send={send} sendNavGoal={sendNavGoal} sendNavCancel={sendNavCancel} />
            <SlamCard />
            <CliffCard />
          </div>
        </Section>

        {/* Erweiterte Funktionen */}
        <Section title="Erweiterte Funktionen">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <DockingCard send={send} />
            <VisionCard sendVisionControl={sendVisionControl} />
            <SemanticsCard />
            <TtsCard send={send} />
          </div>
        </Section>

      </div>
    </div>
  );
}
