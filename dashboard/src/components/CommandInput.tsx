import { useState, useCallback, useRef, useEffect } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';
import type { ClientMessage } from '../types/ros';

interface CommandRef {
  syntax: string;
  example: string;
  desc: string;
}

const COMMAND_REFERENCE: { category: string; commands: CommandRef[] }[] = [
  {
    category: "Navigation",
    commands: [
      { syntax: "nav X Y [YAW]", example: "nav 1.5 2.0", desc: "Navigationsziel" },
      { syntax: "navigiere zu X Y", example: "navigiere zu 1 2", desc: "Navigation (deutsch)" },
      { syntax: "cancel", example: "cancel", desc: "Navigation abbrechen" },
    ],
  },
  {
    category: "Bewegung",
    commands: [
      { syntax: "forward DIST", example: "forward 1", desc: "Geradeaus (0-5 m)" },
      { syntax: "turn GRAD", example: "turn 90", desc: "Drehen (+=links)" },
      { syntax: "stop", example: "stop", desc: "Motorstopp + Nav abbrechen" },
      { syntax: "fahre X m vorwaerts", example: "fahre 2 m vorwaerts", desc: "Geradeaus (deutsch)" },
      { syntax: "drehe X grad links", example: "drehe 90 grad links", desc: "Links drehen" },
    ],
  },
  {
    category: "Sprache / Abfragen",
    commands: [
      { syntax: "halt an / anhalten", example: "halt an", desc: "Sofortstopp" },
      { syntax: "schau nach links/rechts", example: "schau nach links", desc: "Kamera schwenken" },
      { syntax: "licht an [%]/aus", example: "licht an 50", desc: "LED (0-100%)" },
      { syntax: "wie weit / abstand", example: "wie weit", desc: "Ultraschall-Distanz" },
      { syntax: "akku / batterie", example: "akku", desc: "Batteriestatus" },
      { syntax: "fahr zurueck X m", example: "fahr zurueck 1 m", desc: "Rueckwaerts" },
    ],
  },
  {
    category: "Tests",
    commands: [
      { syntax: "test list", example: "test list", desc: "Tests auflisten" },
      { syntax: "test NAME", example: "test rplidar", desc: "Test ausfuehren" },
    ],
  },
  {
    category: "Sonstiges",
    commands: [
      { syntax: "help", example: "help", desc: "Hilfe anzeigen" },
    ],
  },
];

interface CommandInputProps {
  send: (msg: ClientMessage) => void;
}

export default function CommandInput({ send }: CommandInputProps) {
  const [value, setValue] = useState('');
  const [refOpen, setRefOpen] = useState(false);
  const history = useTelemetryStore((s) => s.commandHistory);
  const appendCommand = useTelemetryStore((s) => s.appendCommand);
  const inputRef = useRef<HTMLInputElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [history]);

  const fillCommand = useCallback((example: string) => {
    setValue(example);
    setRefOpen(false);
    inputRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(() => {
    const text = value.trim();
    if (!text) return;
    appendCommand(text);
    send({ op: 'command', text });
    setValue('');
  }, [value, send, appendCommand]);

  return (
    <section className="border-t border-hud-border p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
        Kommando
      </h2>
      {refOpen && (
        <div className="mb-2 max-h-[200px] overflow-y-auto border border-hud-border bg-hud-bg p-2">
          {COMMAND_REFERENCE.map((cat) => (
            <div key={cat.category} className="mb-1.5 last:mb-0">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-hud-amber mb-0.5">
                {cat.category}
              </div>
              {cat.commands.map((cmd) => (
                <button
                  key={cmd.example}
                  type="button"
                  onClick={() => fillCommand(cmd.example)}
                  className="flex w-full items-baseline gap-2 px-1 py-0.5 text-[10px] font-mono hover:bg-hud-panel cursor-pointer text-left"
                >
                  <span className="text-hud-cyan shrink-0">{cmd.syntax}</span>
                  <span className="text-hud-text-dim truncate">{cmd.desc}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
      {history.length > 0 && (
        <div ref={historyRef} className="flex flex-col gap-0.5 mb-2 max-h-[120px] overflow-y-auto">
          {history.map((h, i) => (
            <span
              key={i}
              className={`text-[10px] font-mono whitespace-pre-wrap break-words ${
                h.isCmd ? 'text-hud-text-dim' : h.pending ? 'text-yellow-400' : h.success ? 'text-hud-green' : 'text-hud-red'
              }`}
            >
              {h.isCmd ? '> ' : '  '}{h.text}
            </span>
          ))}
        </div>
      )}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
        className="flex gap-1"
      >
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="nav 1 2 | forward 1 | test list | help"
          className="flex-1 bg-hud-bg border border-hud-border text-hud-text text-xs font-mono px-2 py-1.5 placeholder:text-hud-text-dim/40 focus:border-hud-cyan focus:outline-none"
        />
        <button
          type="button"
          onClick={() => setRefOpen((o) => !o)}
          className="bg-hud-bg border border-hud-border text-hud-amber text-xs px-2 py-1.5 hover:bg-hud-panel transition-colors"
          title="Befehlsreferenz"
        >
          ?
        </button>
        <button
          type="submit"
          className="bg-hud-bg border border-hud-border text-hud-cyan text-xs px-2 py-1.5 hover:bg-hud-panel transition-colors"
        >
          &gt;
        </button>
      </form>
    </section>
  );
}
