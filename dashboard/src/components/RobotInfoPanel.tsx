import { Fragment } from 'react';

const specs = [
  { label: 'Gewicht', value: '2,04 kg' },
  { label: 'LiDAR-Hoehe', value: '235 mm (ueber HA)' },
  { label: 'Ultraschall-Hoehe', value: '50 mm' },
  { label: 'Kamera-Ueberstand', value: '60 mm vor Ultraschall' },
  { label: 'Stuetzrad', value: '70 mm hinter Ultraschall' },
  { label: 'Antrieb', value: 'Differentialantrieb (2 Radmotoren)' },
];

export default function RobotInfoPanel() {
  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-3">
        Roboter-Daten
      </h2>

      {/* Side-view SVG: hinten (links) → vorne (rechts) */}
      {/* HA+LiDAR → Koerper → Stuetzrad → US+IR → Kamera */}
      <svg viewBox="0 0 280 160" className="w-full max-w-[280px] mx-auto my-3">
        {/* Ground line */}
        <line x1="5" y1="145" x2="275" y2="145" stroke="currentColor" className="text-hud-border" strokeWidth="1" />
        {/* Direction arrow */}
        <text x="245" y="155" className="text-[8px] fill-hud-text-dim">→ Fahrt</text>

        {/* Robot body */}
        <rect x="50" y="80" width="150" height="50" rx="4" fill="none" stroke="currentColor" className="text-hud-cyan" strokeWidth="1.5" />

        {/* Drive wheels (HA, hinten) — zwei Radmotoren */}
        <circle cx="80" cy="133" r="14" fill="none" stroke="currentColor" className="text-hud-text" strokeWidth="2" />
        <text x="62" y="155" className="text-[7px] fill-hud-text-dim">HA (2x Motor)</text>

        {/* LiDAR (ueber HA) */}
        <rect x="65" y="52" width="30" height="28" rx="3" fill="none" stroke="currentColor" className="text-hud-amber" strokeWidth="1.5" />
        {/* Laser beam */}
        <line x1="80" y1="66" x2="105" y2="58" stroke="currentColor" className="text-hud-amber" strokeWidth="0.5" strokeDasharray="3" />
        {/* Height annotation */}
        <line x1="55" y1="66" x2="55" y2="145" stroke="currentColor" className="text-hud-amber" strokeWidth="0.5" strokeDasharray="2" />
        <text x="30" y="110" className="text-[7px] fill-hud-amber" transform="rotate(-90,38,110)">235 mm</text>

        {/* Caster wheel (Stuetzrad, vorne) */}
        <circle cx="175" cy="141" r="5" fill="none" stroke="currentColor" className="text-hud-text-dim" strokeWidth="1.5" />
        <line x1="175" y1="130" x2="175" y2="134" stroke="currentColor" className="text-hud-text-dim" strokeWidth="1" />
        <text x="165" y="155" className="text-[7px] fill-hud-text-dim">Stuetzrad</text>

        {/* Ultrasonic (vorne, 50mm ueber Boden) */}
        <rect x="200" y="108" width="14" height="10" rx="1" fill="none" stroke="currentColor" className="text-hud-green" strokeWidth="1.5" />
        {/* US beam cone */}
        <line x1="214" y1="110" x2="235" y2="100" stroke="currentColor" className="text-hud-green" strokeWidth="0.5" strokeDasharray="2" />
        <line x1="214" y1="116" x2="235" y2="126" stroke="currentColor" className="text-hud-green" strokeWidth="0.5" strokeDasharray="2" />
        {/* Height annotation */}
        <text x="237" y="115" className="text-[7px] fill-hud-green">50 mm</text>

        {/* IR cliff sensor (neben US) */}
        <rect x="200" y="122" width="8" height="6" rx="1" fill="none" stroke="currentColor" className="text-hud-red" strokeWidth="1" />
        <line x1="204" y1="128" x2="204" y2="140" stroke="currentColor" className="text-hud-red" strokeWidth="0.5" strokeDasharray="2" />
        <text x="210" y="128" className="text-[7px] fill-hud-red">IR</text>

        {/* Camera (60mm vor US) */}
        <rect x="220" y="95" width="12" height="12" rx="2" fill="none" stroke="currentColor" className="text-hud-cyan" strokeWidth="1.5" />
        <circle cx="226" cy="101" r="3" fill="none" stroke="currentColor" className="text-hud-cyan" strokeWidth="0.5" />
        <text x="234" y="103" className="text-[7px] fill-hud-cyan">Kamera</text>
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
