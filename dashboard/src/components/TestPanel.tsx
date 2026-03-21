import { useState, useEffect } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';
import type { ClientMessage, TestInfo } from '../types/ros';

const TEST_CATEGORIES: Record<string, string> = {
  rplidar: "Sensorik",
  imu: "Sensorik",
  sensor: "Sensorik",
  cliff_latency: "Sensorik",
  encoder: "Antrieb",
  motor: "Antrieb",
  kinematic: "Antrieb",
  straight_drive: "Antrieb",
  rotation: "Antrieb",
  slam: "Navigation",
  nav: "Navigation",
  nav_square: "Navigation",
  docking: "Navigation",
  dashboard_latency: "System",
  can: "System",
};

const CATEGORY_ORDER = ["Sensorik", "Antrieb", "Navigation", "System", "Sonstiges"];

interface TestPanelProps {
  send: (msg: ClientMessage) => void;
}

export default function TestPanel({ send }: TestPanelProps) {
  const availableTests = useTelemetryStore((s) => s.availableTests);
  const runningTest = useTelemetryStore((s) => s.runningTest);
  const testResults = useTelemetryStore((s) => s.testResults);
  const setRunningTest = useTelemetryStore((s) => s.setRunningTest);
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  // Testliste anfordern falls leer
  useEffect(() => {
    if (availableTests.length === 0) {
      send({ op: 'test_list' });
    }
  }, [availableTests.length, send]);

  const handleRunTest = (key: string) => {
    setRunningTest(key);
    send({ op: 'test_run', test_key: key });
  };

  const handleStopTest = () => {
    send({ op: 'test_stop' });
  };

  // Tests nach Kategorie gruppieren
  const grouped = new Map<string, TestInfo[]>();
  for (const cat of CATEGORY_ORDER) {
    grouped.set(cat, []);
  }
  for (const test of availableTests) {
    const cat = TEST_CATEGORIES[test.key] ?? "Sonstiges";
    const arr = grouped.get(cat);
    if (arr) arr.push(test);
    else grouped.set(cat, [test]);
  }

  const getStatusColor = (key: string) => {
    if (runningTest === key) return "bg-hud-amber animate-pulse";
    const result = testResults[key];
    if (!result) return "bg-hud-text-dim";
    return result.success ? "bg-hud-green" : "bg-hud-red";
  };

  const getStatusLabel = (key: string) => {
    if (runningTest === key) return null;
    const result = testResults[key];
    if (!result) return null;
    return result.success ? "PASS" : "FAIL";
  };

  return (
    <div className="border border-hud-border bg-hud-panel p-3">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1 mb-2">
        Validierungstests ({availableTests.length})
      </h3>

      {availableTests.length === 0 ? (
        <p className="text-[10px] text-hud-text-dim">Keine Tests verfuegbar</p>
      ) : (
        <div className="space-y-2">
          {CATEGORY_ORDER.map((cat) => {
            const tests = grouped.get(cat);
            if (!tests || tests.length === 0) return null;
            return (
              <div key={cat}>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-hud-amber mb-1">
                  {cat}
                </div>
                <div className="space-y-0.5">
                  {tests.map((test) => {
                    const result = testResults[test.key];
                    const statusLabel = getStatusLabel(test.key);
                    const isExpanded = expandedTest === test.key;
                    const isRunning = runningTest === test.key;
                    return (
                      <div key={test.key}>
                        <div className="flex items-center gap-2 text-[10px] font-mono">
                          <span className={`w-2 h-2 rounded-full shrink-0 ${getStatusColor(test.key)}`} />
                          <button
                            type="button"
                            onClick={() => result && setExpandedTest(isExpanded ? null : test.key)}
                            className={`flex-1 text-left truncate ${result ? 'cursor-pointer hover:text-hud-cyan' : ''} text-hud-text`}
                          >
                            <span className="text-hud-text">{test.key}</span>
                            {test.description && (
                              <span className="text-hud-text-dim ml-2 text-[9px]">{test.description}</span>
                            )}
                          </button>
                          {statusLabel && (
                            <span className={`text-[9px] font-semibold px-1 ${result?.success ? 'text-hud-green' : 'text-hud-red'}`}>
                              {statusLabel}
                            </span>
                          )}
                          {isRunning ? (
                            <button
                              type="button"
                              onClick={handleStopTest}
                              className="text-[9px] px-1.5 py-0.5 border border-hud-red text-hud-red hover:bg-hud-red/20 transition-colors"
                            >
                              Stoppen
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleRunTest(test.key)}
                              disabled={runningTest !== null}
                              className="text-[9px] px-1.5 py-0.5 border border-hud-border text-hud-cyan hover:bg-hud-bg disabled:text-hud-text-dim disabled:cursor-not-allowed transition-colors"
                            >
                              Starten
                            </button>
                          )}
                        </div>
                        {isExpanded && result && (
                          <pre className="mt-1 ml-4 p-2 text-[9px] bg-hud-bg border border-hud-border text-hud-text overflow-x-auto max-h-[150px] overflow-y-auto whitespace-pre-wrap">
                            {result.output}
                          </pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
