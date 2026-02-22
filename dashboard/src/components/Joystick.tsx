import { useRef, useEffect } from 'react';
import nipplejs from 'nipplejs';

const MAX_LINEAR = 0.4; // m/s
const MAX_ANGULAR = 1.0; // rad/s
const JOYSTICK_SIZE = 150;

interface JoystickProps {
  onMove: (linearX: number, angularZ: number) => void;
  onEnd: () => void;
  disabled?: boolean;
}

export function Joystick({ onMove, onEnd, disabled }: JoystickProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const managerRef = useRef<nipplejs.JoystickManager | null>(null);

  // Keep stable refs to callbacks so we don't recreate the joystick on every render
  const onMoveRef = useRef(onMove);
  const onEndRef = useRef(onEnd);
  onMoveRef.current = onMove;
  onEndRef.current = onEnd;

  useEffect(() => {
    if (!containerRef.current || disabled) return;

    const manager = nipplejs.create({
      zone: containerRef.current,
      mode: 'static',
      position: { bottom: '50%', left: '50%' },
      color: '#00e5ff',
      size: JOYSTICK_SIZE,
    });
    managerRef.current = manager;

    manager.on('move', (_evt, data) => {
      // data.force is normalized (0 at center, ~1 at edge, can exceed 1)
      const force = Math.min(data.force, 1.0);
      const angle = data.angle.radian;

      // nipplejs angle convention (standard math): 0=right, PI/2=up, PI=left, 3PI/2=down
      // ROS: forward=+linear_x, left(CCW)=+angular_z
      const linearX = Math.sin(angle) * force * MAX_LINEAR;
      const angularZ = -Math.cos(angle) * force * MAX_ANGULAR;

      onMoveRef.current(linearX, angularZ);
    });

    manager.on('end', () => {
      onEndRef.current();
    });

    return () => {
      manager.destroy();
      managerRef.current = null;
    };
  }, [disabled]);

  return (
    <div className="flex items-center justify-center h-full w-full">
      <div
        ref={containerRef}
        className={`relative w-[180px] h-[180px] border border-hud-border ${disabled ? 'opacity-20 pointer-events-none' : ''}`}
      />
    </div>
  );
}
