import { Fragment } from 'react';

const specs = [
  { label: 'Gewicht', value: '2,04 kg' },
  { label: 'LiDAR-Hoehe', value: '235 mm' },
  { label: 'Ultraschall-Hoehe', value: '50 mm' },
  { label: 'Kamera-Ueberstand', value: '60 mm vor Ultraschall' },
];

export default function RobotInfoPanel() {
  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        Roboter-Daten
      </h2>

      {/* Simple side-view SVG diagram */}
      <svg viewBox="0 0 240 140" className="w-full max-w-[240px] mx-auto my-3">
        {/* Ground line */}
        <line
          x1="10" y1="130" x2="230" y2="130"
          stroke="currentColor" className="text-hud-border" strokeWidth="1"
        />
        {/* Robot body */}
        <rect
          x="60" y="70" width="120" height="50" rx="4"
          fill="none" stroke="currentColor" className="text-hud-cyan" strokeWidth="1.5"
        />
        {/* Wheels */}
        <circle
          cx="85" cy="125" r="8"
          fill="none" stroke="currentColor" className="text-hud-text-dim" strokeWidth="1.5"
        />
        <circle
          cx="155" cy="125" r="8"
          fill="none" stroke="currentColor" className="text-hud-text-dim" strokeWidth="1.5"
        />
        {/* LiDAR tower */}
        <rect
          x="105" y="45" width="30" height="25" rx="2"
          fill="none" stroke="currentColor" className="text-hud-amber" strokeWidth="1"
        />
        <line
          x1="120" y1="57" x2="150" y2="50"
          stroke="currentColor" className="text-hud-amber" strokeWidth="0.5" strokeDasharray="3"
        />
        <text x="155" y="55" className="text-[8px] fill-hud-amber">235mm</text>
        {/* Ultrasonic */}
        <rect
          x="175" y="100" width="15" height="10" rx="1"
          fill="none" stroke="currentColor" className="text-hud-green" strokeWidth="1"
        />
        <text x="195" y="108" className="text-[8px] fill-hud-green">50mm</text>
        {/* Camera */}
        <rect
          x="185" y="85" width="12" height="10" rx="1"
          fill="none" stroke="currentColor" className="text-hud-cyan" strokeWidth="1"
        />
        <text x="200" y="92" className="text-[8px] fill-hud-cyan">Kamera</text>
      </svg>

      {/* Specs table */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
        {specs.map((s) => (
          <Fragment key={s.label}>
            <span className="text-hud-text-dim">{s.label}</span>
            <span className="text-hud-text font-mono">{s.value}</span>
          </Fragment>
        ))}
      </div>
    </div>
  );
}
