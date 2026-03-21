import { useRef, useCallback } from 'react';
import type { ClientMessage } from '../types/ros';

const MAX_LINEAR = 0.4;   // m/s (Dashboard-Joystick-Limit)
const MAX_ANGULAR = 1.0;  // rad/s
const SEND_INTERVAL_MS = 100; // 10 Hz rate limit

export function useJoystick(send: (msg: ClientMessage) => void) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const currentCmd = useRef({ linear_x: 0, angular_z: 0 });

  const startSending = useCallback(() => {
    // Rate-limited cmd_vel sending at 10 Hz
    // Heartbeat laeuft global in useWebSocket (5 Hz Totmannschalter)
    if (!intervalRef.current) {
      intervalRef.current = setInterval(() => {
        send({
          op: 'cmd_vel',
          linear_x: currentCmd.current.linear_x,
          angular_z: currentCmd.current.angular_z,
        });
      }, SEND_INTERVAL_MS);
    }
  }, [send]);

  const stopSending = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    // Send zero velocity immediately
    currentCmd.current = { linear_x: 0, angular_z: 0 };
    send({ op: 'cmd_vel', linear_x: 0, angular_z: 0 });
  }, [send]);

  const updateVelocity = useCallback((x: number, z: number) => {
    // Clamp velocities (defense in depth - backend also clamps)
    currentCmd.current = {
      linear_x: Math.max(-MAX_LINEAR, Math.min(x, MAX_LINEAR)),
      angular_z: Math.max(-MAX_ANGULAR, Math.min(z, MAX_ANGULAR)),
    };
  }, []);

  const onJoystickMove = useCallback((linearX: number, angularZ: number) => {
    updateVelocity(linearX, angularZ);
    startSending();
  }, [updateVelocity, startSending]);

  const onJoystickEnd = useCallback(() => {
    stopSending();
  }, [stopSending]);

  return { onJoystickMove, onJoystickEnd, currentCmd };
}
