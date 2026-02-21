import { useRef, useCallback } from 'react';
import type { ClientMessage } from '../types/ros';

const MAX_LINEAR = 0.4;   // m/s (from nav2_params.yaml)
const MAX_ANGULAR = 1.0;  // rad/s
const SEND_INTERVAL_MS = 100; // 10 Hz rate limit
const HEARTBEAT_INTERVAL_MS = 200;

export function useJoystick(send: (msg: ClientMessage) => void) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const currentCmd = useRef({ linear_x: 0, angular_z: 0 });

  const startSending = useCallback(() => {
    // Rate-limited cmd_vel sending at 10 Hz
    if (!intervalRef.current) {
      intervalRef.current = setInterval(() => {
        send({
          op: 'cmd_vel',
          linear_x: currentCmd.current.linear_x,
          angular_z: currentCmd.current.angular_z,
        });
      }, SEND_INTERVAL_MS);
    }
    // Heartbeat at 5 Hz for deadman switch
    if (!heartbeatRef.current) {
      heartbeatRef.current = setInterval(() => {
        send({ op: 'heartbeat' });
      }, HEARTBEAT_INTERVAL_MS);
    }
  }, [send]);

  const stopSending = useCallback(() => {
    // Clear intervals
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = undefined;
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
