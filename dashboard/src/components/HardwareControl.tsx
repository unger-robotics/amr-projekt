import { useState, useCallback, useEffect } from 'react';
import { useTelemetryStore } from '../store/telemetryStore';

interface HardwareSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  onChange: (value: number) => void;
}

function HardwareSlider({ label, value, min, max, unit, onChange }: HardwareSliderProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs">
        <span className="text-hud-text-dim uppercase tracking-wider">{label}</span>
        <span className="text-hud-cyan font-mono">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1 appearance-none cursor-pointer bg-hud-bg rounded-none
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
          [&::-webkit-slider-thumb]:bg-hud-cyan [&::-webkit-slider-thumb]:shadow-[0_0_6px_rgba(0,229,255,0.6)]
          [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:border-none
          [&::-moz-range-thumb]:bg-hud-cyan [&::-moz-range-thumb]:shadow-[0_0_6px_rgba(0,229,255,0.6)]
          [&::-moz-range-track]:bg-hud-bg [&::-moz-range-track]:h-1"
      />
      <div className="flex justify-between text-[10px] text-hud-text-dim">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

interface HardwareControlProps {
  sendHardwareCmd: (motorLimit: number, servoSpeed: number, ledPwm: number) => void;
}

export default function HardwareControl({ sendHardwareCmd }: HardwareControlProps) {
  const storeMotorLimit = useTelemetryStore((s) => s.hwMotorLimit);
  const storeServoSpeed = useTelemetryStore((s) => s.hwServoSpeed);
  const storeLedPwm = useTelemetryStore((s) => s.hwLedPwm);

  const [motorLimit, setMotorLimit] = useState(storeMotorLimit);
  const [servoSpeed, setServoSpeed] = useState(storeServoSpeed);
  const [ledPwm, setLedPwm] = useState(storeLedPwm);

  // Sync from store when server reports actual values
  useEffect(() => { setMotorLimit(storeMotorLimit); }, [storeMotorLimit]);
  useEffect(() => { setServoSpeed(storeServoSpeed); }, [storeServoSpeed]);
  useEffect(() => { setLedPwm(storeLedPwm); }, [storeLedPwm]);

  const handleMotorLimit = useCallback((v: number) => {
    setMotorLimit(v);
    sendHardwareCmd(v, servoSpeed, ledPwm);
  }, [sendHardwareCmd, servoSpeed, ledPwm]);

  const handleServoSpeed = useCallback((v: number) => {
    setServoSpeed(v);
    sendHardwareCmd(motorLimit, v, ledPwm);
  }, [sendHardwareCmd, motorLimit, ledPwm]);

  const handleLedPwm = useCallback((v: number) => {
    setLedPwm(v);
    sendHardwareCmd(motorLimit, servoSpeed, v);
  }, [sendHardwareCmd, motorLimit, servoSpeed]);

  const handleReset = useCallback(() => {
    setMotorLimit(100);
    setServoSpeed(5);
    setLedPwm(0);
    sendHardwareCmd(100, 5, 0);
  }, [sendHardwareCmd]);

  return (
    <div className="bg-hud-panel text-hud-text p-4 flex flex-col gap-4 border-t border-hud-border">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-hud-cyan/70 border-b border-hud-border pb-1">
        Hardware
      </h2>

      <HardwareSlider label="Motor-Limit" value={motorLimit} min={0} max={100} unit="%" onChange={handleMotorLimit} />
      <HardwareSlider label="Servo-Speed" value={servoSpeed} min={1} max={10} unit="" onChange={handleServoSpeed} />
      <HardwareSlider label="LED-PWM" value={ledPwm} min={0} max={255} unit="" onChange={handleLedPwm} />

      <button
        onClick={handleReset}
        className="w-full py-1.5 text-xs uppercase tracking-wider font-semibold
          border border-hud-border text-hud-cyan hover:bg-hud-cyan/10
          transition-colors duration-150"
      >
        Reset
      </button>
    </div>
  );
}
