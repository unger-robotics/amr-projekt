import { useEffect, useRef, useCallback, useState } from 'react';
import type { ServerMessage, ClientMessage, ServoCmdMsg, HardwareCmdMsg, AudioPlayMsg, AudioVolumeMsg } from '../types/ros';

const WS_PORT = 9090;
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000];

export function useWebSocket(onMessage: (msg: ServerMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [latencyMs, setLatencyMs] = useState(0);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastPongRef = useRef(0);
  const connectRef = useRef<(() => void) | undefined>(undefined);
  const onMessageRef = useRef(onMessage);

  // Immer aktuelle onMessage-Referenz halten, ohne connect neu zu bauen
  useEffect(() => {
    onMessageRef.current = onMessage;
  });

  const getUrl = useCallback(() => {
    const host = window.location.hostname || 'localhost';
    return `ws://${host}:${WS_PORT}`;
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getUrl());

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempt.current = 0;
      lastPongRef.current = Date.now();
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as ServerMessage;
        if (msg.op === 'telemetry') {
          setLatencyMs(Date.now() - msg.ts * 1000);
        }
        onMessageRef.current(msg);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      const delay = RECONNECT_DELAYS[
        Math.min(reconnectAttempt.current, RECONNECT_DELAYS.length - 1)
      ];
      reconnectAttempt.current++;
      reconnectTimer.current = setTimeout(() => connectRef.current?.(), delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [getUrl]);

  useEffect(() => {
    connectRef.current = connect;
  });

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  /** Throttled servo command sender (max 10 Hz / 100ms between sends) */
  const lastServoCmdRef = useRef(0);
  const sendServoCmd = useCallback((pan: number, tilt: number) => {
    const now = Date.now();
    if (now - lastServoCmdRef.current < 100) return;
    lastServoCmdRef.current = now;
    const msg: ServoCmdMsg = { op: 'servo_cmd', pan, tilt };
    send(msg);
  }, [send]);

  /** Throttled hardware command sender (max 10 Hz / 100ms between sends) */
  const lastHwCmdRef = useRef(0);
  const sendHardwareCmd = useCallback((motorLimit: number, servoSpeed: number, ledPwm: number) => {
    const now = Date.now();
    if (now - lastHwCmdRef.current < 100) return;
    lastHwCmdRef.current = now;
    const msg: HardwareCmdMsg = { op: 'hardware_cmd', motor_limit: motorLimit, servo_speed: servoSpeed, led_pwm: ledPwm };
    send(msg);
  }, [send]);

  const sendNavGoal = useCallback((x: number, y: number, yaw: number) => {
    send({ op: 'nav_goal', x, y, yaw });
  }, [send]);

  const sendNavCancel = useCallback(() => {
    send({ op: 'nav_cancel' });
  }, [send]);

  const sendAudioPlay = useCallback((soundKey: string) => {
    const msg: AudioPlayMsg = { op: 'audio_play', sound_key: soundKey };
    send(msg);
  }, [send]);

  const lastVolCmdRef = useRef(0);
  const sendAudioVolume = useCallback((volumePercent: number) => {
    const now = Date.now();
    if (now - lastVolCmdRef.current < 200) return;
    lastVolCmdRef.current = now;
    const msg: AudioVolumeMsg = { op: 'audio_volume', volume_percent: volumePercent };
    send(msg);
  }, [send]);

  return { connected, latencyMs, send, sendServoCmd, sendHardwareCmd, sendNavGoal, sendNavCancel, sendAudioPlay, sendAudioVolume };
}
