interface ParamRow {
  param: string;
  wert: string;
  quelle: string;
}

/* ── Hilfskomponenten ─────────────────────────────────────────────── */

function Section({
  title,
  titleColor = 'text-hud-cyan/70',
  children,
}: {
  title: string;
  titleColor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-hud-panel border border-hud-border p-4">
      <h2
        className={`text-xs font-semibold uppercase tracking-wider ${titleColor} border-b border-hud-border pb-1 mb-3`}
      >
        {title}
      </h2>
      {children}
    </div>
  );
}

function ParamTable({ rows }: { rows: ParamRow[] }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-hud-border text-hud-text-dim uppercase tracking-wider">
          <th className="text-left py-2 pr-3">Parameter</th>
          <th className="text-left py-2 pr-3">Wert</th>
          <th className="text-left py-2">Quelle</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.param} className="border-b border-hud-border/30 hover:bg-hud-cyan/5">
            <td className="py-2 pr-3 text-hud-text">{row.param}</td>
            <td className="py-2 pr-3 font-mono text-hud-cyan whitespace-nowrap">{row.wert}</td>
            <td className="py-2 text-hud-text-dim text-[10px]">{row.quelle}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Desc({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-hud-text mb-3 leading-relaxed">{children}</p>;
}

function Code({ children }: { children: string }) {
  return (
    <code className="text-[11px] font-mono text-hud-cyan bg-hud-bg px-1.5 py-0.5 border border-hud-border/40">
      {children}
    </code>
  );
}

/* ── Daten ────────────────────────────────────────────────────────── */

const JOYSTICK_PARAMS: ParamRow[] = [
  { param: 'Max. Lineargeschwindigkeit', wert: '0,4 m/s', quelle: 'dashboard_bridge.py' },
  { param: 'Max. Winkelgeschwindigkeit', wert: '1,0 rad/s', quelle: 'dashboard_bridge.py' },
  { param: 'Deadman-Timer', wert: '300 ms', quelle: 'dashboard_bridge.py' },
  { param: 'Heartbeat-Rate', wert: '5 Hz (200 ms)', quelle: 'useWebSocket.ts' },
  { param: 'Sende-Rate', wert: '10 Hz', quelle: 'useJoystick.ts' },
];

const NAV_STATES = [
  { zustand: 'idle', farbe: 'text-hud-text-dim', beschreibung: 'Kein Ziel aktiv' },
  { zustand: 'navigating', farbe: 'text-hud-cyan', beschreibung: 'Navigation läuft, Restdistanz wird gemeldet' },
  { zustand: 'reached', farbe: 'text-hud-green', beschreibung: 'Ziel erreicht' },
  { zustand: 'failed', farbe: 'text-hud-red', beschreibung: 'Navigation fehlgeschlagen (Hindernis, Timeout)' },
  { zustand: 'cancelled', farbe: 'text-hud-amber', beschreibung: 'Vom Benutzer abgebrochen' },
] as const;

const SERVO_PARAMS: ParamRow[] = [
  { param: 'Pan-Bereich', wert: '45–135°', quelle: 'config_sensors.h' },
  { param: 'Tilt-Bereich', wert: '80–135°', quelle: 'config_sensors.h' },
  { param: 'Pan-Offset (mechanisch)', wert: '+8°', quelle: 'config_sensors.h' },
  { param: 'Tilt-Offset (mechanisch)', wert: '+1°', quelle: 'config_sensors.h' },
  { param: 'Rampe', wert: '2°/Step @ 20 Hz', quelle: 'config_sensors.h' },
  { param: 'Throttling (Dashboard)', wert: '10 Hz', quelle: 'useWebSocket.ts' },
];

const HARDWARE_PARAMS: ParamRow[] = [
  { param: 'Motor-Limit', wert: '0–100 %', quelle: 'dashboard_bridge.py' },
  { param: 'Servo-Speed', wert: '1–10 °/Step', quelle: 'dashboard_bridge.py' },
  { param: 'LED-Helligkeit', wert: '0–100 %', quelle: 'dashboard_bridge.py' },
];

const SAFETY_ROWS = [
  { mechanismus: 'Geschwindigkeitslimit', beschreibung: 'Hart in Bridge begrenzt', wert: '0,4 m/s / 1,0 rad/s' },
  { mechanismus: 'Deadman-Timer (Bridge)', beschreibung: 'Stopp bei fehlendem Heartbeat', wert: '300 ms' },
  { mechanismus: 'Failsafe-Timeout (Firmware)', beschreibung: 'MCU stoppt ohne cmd_vel', wert: '500 ms' },
  { mechanismus: 'Cliff-Safety', beschreibung: 'Blockiert bei Abgrund (IR-Sensor)', wert: '20 Hz Abtastung' },
  { mechanismus: 'Ultraschall-Schutz', beschreibung: 'Stoppt Vorwaertsfahrt bei Hindernis, Rueckwaerts erlaubt', wert: '< 100 mm Stopp, > 140 mm frei' },
  { mechanismus: 'CAN-Bus Notstopp', beschreibung: 'MCU-zu-MCU ohne Pi 5', wert: '0x120 Cliff, 0x141 Batterie' },
  { mechanismus: 'Verbindungsverlust', beschreibung: 'Sofortiger Stopp', wert: 'Deadman + Firmware-Timeout' },
] as const;

const ESTOP_ACTIONS = [
  'Null-Twist auf /cmd_vel (5× gesendet)',
  'Laufende Navigation abgebrochen',
  '/emergency_stop Bool publiziert',
  'Audio-Alarm ausgelöst (cliff_alarm)',
  'Broadcast an alle Dashboard-Clients',
] as const;

/* ── Hauptkomponente ──────────────────────────────────────────────── */

export default function ControlReferencePage() {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-5xl mx-auto space-y-4">
        {/* 1. Steuerungskette */}
        <Section title="Steuerungskette">
          <Desc>
            Dual-Path-Architektur: Primär micro-ROS/UART über den Pi 5, sekundär CAN-Bus
            direkt zwischen den MCUs. Der CAN-Pfad funktioniert autonom — Ebene A benötigt
            den Pi 5 nicht für den Notstopp.
          </Desc>
          <pre className="text-[10px] font-mono text-hud-text leading-relaxed overflow-x-auto bg-hud-bg border border-hud-border/40 p-3">
{`Dashboard (Browser)
    │ WebSocket (wss:9090)
    ▼
dashboard_bridge.py
    ├──► /dashboard_cmd_vel ──┐
    │                         ▼
    │                  cliff_safety_node ◄── /cliff (20 Hz)
    │                    │              ◄── /range/front (10 Hz)
    │                    ▼
    │               /cmd_vel (Twist)
    │                    │ micro-ROS / UART 921600
    │                    ▼
    │              Drive-Node (ESP32-S3)
    │                50 Hz PID-Regelung
    │
    └──► Nav2 (NavigateToPose)
              └──► /nav_cmd_vel ──► cliff_safety_node


CAN-Bus Bypass (1 Mbit/s, MCU-zu-MCU, ohne Pi 5):
  Sensor-Node ──0x120──► Drive-Node  (Cliff → Motorstopp)
  Sensor-Node ──0x141──► Drive-Node  (Batterie → Shutdown)`}
          </pre>
        </Section>

        {/* 2. Dashboard-Joystick */}
        <Section title="Dashboard-Joystick (Manuell)">
          <Desc>
            nipplejs-basierter 2D-Joystick im Steuerung-Tab. Sendet Fahrbefehle
            als Twist-Nachrichten. Single-Controller-Logik: nur ein aktiver Client
            kann gleichzeitig steuern. Bei Verbindungsverlust erfolgt sofortiger Stopp.
          </Desc>
          <ParamTable rows={JOYSTICK_PARAMS} />
        </Section>

        {/* 3. Kartenklick-Navigation */}
        <Section title="Kartenklick-Navigation (Autonom)">
          <Desc>
            Ein Klick auf die SLAM-Karte sendet ein Navigationsziel über die
            Nav2 <Code>NavigateToPose</Code> Action. Der Navigationsstatus wird mit 1 Hz
            an alle Clients gemeldet. Abbruch jederzeit über den Cancel-Button
            oder den Sprachbefehl <Code>stop</Code>.
          </Desc>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-hud-border text-hud-text-dim uppercase tracking-wider">
                <th className="text-left py-2 pr-3">Zustand</th>
                <th className="text-left py-2">Beschreibung</th>
              </tr>
            </thead>
            <tbody>
              {NAV_STATES.map((s) => (
                <tr key={s.zustand} className="border-b border-hud-border/30 hover:bg-hud-cyan/5">
                  <td className={`py-2 pr-3 font-mono ${s.farbe}`}>{s.zustand}</td>
                  <td className="py-2 text-hud-text">{s.beschreibung}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {/* 4. RViz2 */}
        <Section title="RViz2 Navigation">
          <Desc>
            Zielpunkte können klassisch über das RViz2 <Code>2D Nav Goal</Code> Tool gesetzt
            werden. Voraussetzung: <Code>use_rviz:=True</Code> im Launch und X11-Forwarding
            zum Host.
          </Desc>
        </Section>

        {/* 5. CLI-Steuerung */}
        <Section title="Programmatische Steuerung (CLI)">
          <Desc>
            Manuelles Fahren über die ROS2-Kommandozeile. Der Firmware-Failsafe stoppt
            die Motoren automatisch nach 500 ms ohne neue Befehle.
          </Desc>
          <div className="bg-hud-bg border border-hud-border/40 p-3 mb-2">
            <code className="text-[11px] font-mono text-hud-cyan break-all">
              ros2 topic pub /cmd_vel geometry_msgs/msg/Twist
              {' "'}{'{'} linear: {'{'} x: 0.2 {'}'}, angular: {'{'} z: 0.0 {'}'} {'}'}
              {'"'}
            </code>
          </div>
          <p className="text-[10px] text-hud-text-dim">
            Firmware-Failsafe: 500 ms (config_drive.h) · Watchdog: 50 Miss-Counts
          </p>
        </Section>

        {/* 6. Kamerasteuerung */}
        <Section title="Kamerasteuerung (Pan/Tilt)">
          <Desc>
            PCA9685-PWM-Servos über Slider im Steuerung-Tab oder per Sprachbefehl
            (<Code>schau nach links/rechts/vorne</Code>). Rampensteuerung verhindert
            ruckartige Bewegungen und I2C-Contention.
          </Desc>
          <ParamTable rows={SERVO_PARAMS} />
        </Section>

        {/* 7. Hardware-Kontrolle */}
        <Section title="Hardware-Kontrolle">
          <Desc>
            Motor-Limit skaliert den PID-Output (100 % = volle Leistung).
            LED bei 0 % aktiviert den automatischen Heartbeat-Modus (langsames Pulsieren).
          </Desc>
          <ParamTable rows={HARDWARE_PARAMS} />
        </Section>

        {/* 8. E-Stop */}
        <Section title="Notstopp (E-Stop)" titleColor="text-hud-red/70">
          <Desc>
            Der Notstopp kann über drei Wege ausgelöst werden: den E-Stop-Button
            im Dashboard, den Sprachbefehl <Code>Stopp!</Code> oder einen
            Hardware-E-Stop. Bei Auslösung werden folgende Aktionen ausgeführt:
          </Desc>
          <ol className="list-decimal list-inside text-xs text-hud-text space-y-1 mb-3">
            {ESTOP_ACTIONS.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ol>
          <p className="text-[10px] text-hud-text-dim">
            Freigabe über den Release-Button im Dashboard. Nach Freigabe muss die Steuerung
            manuell wieder aufgenommen werden.
          </p>
        </Section>

        {/* 9. Sicherheitsmechanismen */}
        <Section title="Sicherheitsmechanismen" titleColor="text-hud-amber/70">
          <Desc>
            Mehrstufiges Sicherheitskonzept: Software-Limits im Bridge-Node, Cliff-Safety
            als ROS2-Multiplexer und Firmware-Failsafe auf der MCU. Der CAN-Bus-Notstopp
            arbeitet auf Ebene A autonom — der Pi 5 ist dafür nicht erforderlich.
          </Desc>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-hud-border text-hud-text-dim uppercase tracking-wider">
                <th className="text-left py-2 pr-3">Mechanismus</th>
                <th className="text-left py-2 pr-3">Beschreibung</th>
                <th className="text-left py-2">Parameter</th>
              </tr>
            </thead>
            <tbody>
              {SAFETY_ROWS.map((row) => (
                <tr key={row.mechanismus} className="border-b border-hud-border/30 hover:bg-hud-cyan/5">
                  <td className="py-2 pr-3 text-hud-text font-semibold">{row.mechanismus}</td>
                  <td className="py-2 pr-3 text-hud-text">{row.beschreibung}</td>
                  <td className="py-2 font-mono text-hud-cyan whitespace-nowrap text-[10px]">{row.wert}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>
    </div>
  );
}
