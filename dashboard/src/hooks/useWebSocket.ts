import { useEffect, useRef, useCallback, useState } from 'react';
import type { ServerMessage, ClientMessage, ServoCmdMsg } from '../types/ros';

const WS_PORT = 9090;
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000];

export function useWebSocket(onMessage: (msg: ServerMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [latencyMs, setLatencyMs] = useState(0);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastPongRef = useRef(0);

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
        onMessage(msg);
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
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [getUrl, onMessage]);

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

  return { connected, latencyMs, send, sendServoCmd };
}
