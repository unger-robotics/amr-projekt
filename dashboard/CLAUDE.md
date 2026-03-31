# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ueberblick

Dashboard (Bedien- und Leitstandsebene) fuer einen Autonomen Mobilen Roboter (AMR). React-SPA mit fuenf Tabs: **Steuerung** (Kamera, SLAM-Karte mit Heading-Up-Rotation, LiDAR, Joystick, Servo/Hardware, Kommandofeld), **Aufgaben** (Navigation, SLAM, Cliff, Docking, Vision, Semantik, TTS, Schnellstart-Missionen), **Details** (Geraetepanel, Sensordetails, Audio, Roboter-Daten), **Sprache** (Voice-Transkription, Mikrofon-Mute, Kommandoverlauf) und **Referenz** (Steuerungskette, Parameter, Sicherheitsmechanismen).

## Build-Befehle

```bash
npm install          # Abhaengigkeiten installieren
npm run dev          # Entwicklungsserver (https://amr.local:5173)
npm run build        # Produktion (tsc -b && vite build)
npm run lint         # ESLint
```

HTTPS erfordert mkcert-Zertifikate (`amr.local+5.pem` / `amr.local+5-key.pem`) im Dashboard-Verzeichnis. Ohne Zertifikate schlaegt `npm run dev` fehl (vite.config.ts liest sie synchron).

## Betrieb im Gesamtsystem

Das Dashboard benoetigt zwei parallele Prozesse:
1. ROS2-seitig: `use_dashboard:=True` im `full_stack.launch.py` (startet `dashboard_bridge.py` als WebSocket/MJPEG-Backend im Docker-Container)
2. Lokal: `npm run dev -- --host 0.0.0.0`

WebSocket-Backend laeuft auf Port 9090 (wss/ws), MJPEG-Kamerastream auf Port 8082.

## Architektur

### Tech-Stack
- React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4 (Vite-Plugin)
- Zustand fuer State-Management (ein einzelner `telemetryStore`)
- nipplejs fuer Joystick-Input
- Kein Router — Tab-State (`steuerung` | `aufgaben` | `details` | `sprache` | `referenz`) in `App.tsx`

### Datenfluss
1. `useWebSocket` Hook verbindet sich zu `wss://<host>:9090` (auto-reconnect mit exponentiellem Backoff)
2. Eingehende JSON-Nachrichten werden nach `op`-Feld dispatcht (`telemetry`, `scan`, `system`, `map`, `vision_*`, `nav_status`, `sensor_status`, `audio_status`, `command_response`, `test_list`, `voice_transcript`, `voice_mute_status`)
3. `telemetryStore` (Zustand) haelt den gesamten Roboterzustand flach (kein Nesting)
4. Komponenten selektieren per `useTelemetryStore((s) => s.field)` nur die benoetigten Felder
5. Ausgehende Befehle (`cmd_vel`, `servo_cmd`, `hardware_cmd`, `nav_goal`, `command`, `test_list`, `test_run`, `voice_mute`, etc.) werden ueber typisierte Send-Funktionen gesendet

### Nachrichten-Protokoll
Alle Typen sind in `src/types/ros.ts` definiert:
- `ServerMessage` — Union aller vom Backend empfangenen Nachrichtentypen
- `ClientMessage` — Union aller ans Backend gesendeten Nachrichtentypen
- Throttling: Servo/Hardware-Befehle max 10 Hz, Audio-Volume max 5 Hz

### Design-System
HUD-Style mit dunklem Theme. Farben als CSS Custom Properties in `src/index.css` (`--color-hud-*`). Tailwind-Klassen: `hud-bg`, `hud-panel`, `hud-border`, `hud-cyan`, `hud-amber`, `hud-red`, `hud-green`, `hud-text`, `hud-text-dim`. Monospace-Schrift (JetBrains Mono) fuer alle Elemente.

### Dateistruktur-Konventionen
- `src/components/` — React-Komponenten (eine Datei pro Komponente, inkl. AufgabenPage, VoicePage, ControlReferencePage)
- `src/hooks/` — Custom Hooks (`useWebSocket`, `useJoystick`)
- `src/store/` — Zustand Store (`telemetryStore`)
- `src/types/` — TypeScript-Interfaces fuer das WebSocket-Protokoll (`ros.ts`)
- Hooks und Utility-Dateien (`useImageFit.ts`, `useJoystick.ts`, `useWebSocket.ts`) liegen teilweise auch direkt in `src/components/`

## Harte Randbedingungen

- Aenderungen am WebSocket-Protokoll (`types/ros.ts`) muessen konsistent mit dem Python-Backend (`dashboard_bridge.py` in `amr/scripts/`) bleiben
- Sprache in der Benutzeroberflaeche: Deutsch
- Keine UTF-8-Umlaute in Markdown-Dateien (ae, oe, ue, ss verwenden)
