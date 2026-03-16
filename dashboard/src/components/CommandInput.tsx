import { useState, useCallback } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';
import type { ClientMessage } from '../types/ros';

interface CommandInputProps {
  send: (msg: ClientMessage) => void;
}

export default function CommandInput({ send }: CommandInputProps) {
  const [value, setValue] = useState('');
  const history = useTelemetryStore((s) => s.commandHistory);
  const appendCommand = useTelemetryStore((s) => s.appendCommand);

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
      {history.length > 0 && (
        <div className="flex flex-col gap-0.5 mb-2 max-h-[120px] overflow-y-auto">
          {history.map((h, i) => (
            <span
              key={i}
              className={`text-[10px] font-mono truncate ${
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
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="nav 1 2 | forward 1 | test list | help"
          className="flex-1 bg-hud-bg border border-hud-border text-hud-text text-xs font-mono px-2 py-1.5 placeholder:text-hud-text-dim/40 focus:border-hud-cyan focus:outline-none"
        />
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
