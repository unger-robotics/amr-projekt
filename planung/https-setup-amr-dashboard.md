# HTTPS-Setup fuer das AMR-Dashboard

## Problemstellung

Das AMR-Dashboard (Vite + React) auf dem Raspberry Pi 5 soll ueber HTTPS erreichbar sein. Die Loesung muss mit wechselnden Netzwerken funktionieren (Home-WLAN, iPhone-Hotspot, Ethernet).

## Architektur

```
Mac (mac / MacBook)              Raspberry Pi 5
┌──────────────────┐              ┌──────────────────────────┐
│  mkcert -install │              │  ~/amr-projekt/dashboard │
│  (lokale CA)     │──Zertifikat──│  ├── amr.local+5.pem     │
│                  │    via scp   │  ├── amr.local+5-key.pem  │
│  Chrome/Safari   │──HTTPS──────▶│  └── vite.config.ts      │
│  vertraut CA     │              │      (https: {...})       │
└──────────────────┘              └──────────────────────────┘
```

**Prinzip:** Die CA wird auf dem Mac erzeugt und dort im Trust Store registriert. Das Zertifikat wird auf den Pi kopiert. Der Browser vertraut dem Zertifikat, weil er die CA kennt.

## Voraussetzung: mkcert auf jedem Mac

Jeder Mac (mac, MacBook), der das Dashboard per HTTPS aufrufen soll, benoetigt eine eigene mkcert-Installation. Es gibt zwei Wege:

### Weg A – Eigene CA pro Mac (empfohlen, einfacher)

Auf **jedem** Mac:

```bash
brew install mkcert nss
mkcert -install
```

Dann auf **einem** Mac das Zertifikat erzeugen (siehe Abschnitt "Zertifikat generieren") und auf den Pi kopieren. Auf dem **zweiten** Mac nur die Root-CA des ersten importieren:

```bash
# Auf dem mac – CA-Pfad:
# /Users/jan/Library/Application Support/mkcert

# CA-Datei vom mac auf das MacBook kopieren und importieren:
scp jan@mac.local:"/Users/jan/Library/Application Support/mkcert/rootCA.pem" ~/Downloads/rootCA-mac.pem
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/Downloads/rootCA-mac.pem
```

### Weg B – Gemeinsame CA (beide Macs teilen eine CA)

1. CA auf Mac 1 erzeugen (`mkcert -install`)
2. `rootCA.pem` und `rootCA-key.pem` auf Mac 2 kopieren nach `$(mkcert -CAROOT)/`
3. Auf Mac 2: `mkcert -install`

**Sicherheitshinweis:** Die Datei `rootCA-key.pem` ist ein privater Schluessel. Nur ueber sichere Kanaele uebertragen.

## Zertifikat generieren

### Dualnetzwerk: Alle Hostnamen und IPs abdecken

Das Zertifikat muss alle moeglichen Zugriffswege enthalten. Bei wechselnden Netzwerken (Home-WLAN, Hotspot, Ethernet) aendern sich die IPs. Der stabile Zugriffspunkt ist **amr.local** via mDNS.

```bash
# Auf dem Mac, der die CA besitzt:
mkcert amr.local \
       192.168.1.24 \
       10.0.0.1 \
       172.20.10.2 \
       localhost \
       127.0.0.1
```

Erklaerung der SANs (Subject Alternative Names):

| SAN          | Netzwerk        | Bemerkung                      |
|--------------|-----------------|--------------------------------|
| amr.local    | alle            | mDNS – funktioniert immer      |
| 192.168.1.24 | Home-WLAN       | statisch oder DHCP-Reservation |
| 10.0.0.1     | Ethernet direkt | falls Point-to-Point genutzt   |
| 172.20.10.x  | iPhone-Hotspot  | typischer Hotspot-Bereich      |
| localhost    | Pi lokal        | lokale Entwicklung             |
| 127.0.0.1    | Pi lokal        | lokale Entwicklung             |

Falls sich Hotspot-IPs aendern, Zertifikat mit neuer IP neu generieren und erneut auf den Pi kopieren. Alternativ ausschliesslich `amr.local` verwenden – dann sind feste IPs im Zertifikat nicht zwingend noetig.

### Minimalvariante (nur mDNS)

```bash
mkcert amr.local localhost 127.0.0.1
```

Funktioniert, solange der Browser `https://amr.local:5173/` aufruft (nicht die IP direkt).

## Zertifikat auf den Pi kopieren

```bash
scp amr.local+5*.pem pi@amr.local:~/amr-projekt/dashboard/
```

## vite.config.ts anpassen

Auf dem Pi (`~/amr-projekt/dashboard/vite.config.ts`):

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import path from 'path'

// Zertifikatsdateien suchen (Dateiname variiert je nach SANs)
function findCert(dir: string, suffix: string): string {
  const files = fs.readdirSync(dir)
  const match = files.find(f => f.endsWith(suffix))
  if (!match) throw new Error(`Kein Zertifikat (*${suffix}) in ${dir} gefunden`)
  return path.resolve(dir, match)
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    https: {
      key:  fs.readFileSync(findCert(__dirname, '-key.pem')),
      cert: fs.readFileSync(findCert(__dirname, '.pem').replace('-key.pem', '.pem')),
    },
  },
})
```

Einfachere Variante mit festen Dateinamen:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    https: {
      key:  fs.readFileSync(path.resolve(__dirname, 'amr.local+5-key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, 'amr.local+5.pem')),
    },
  },
})
```

## Mixed Content vermeiden

HTTPS-Seiten duerfen keine Ressourcen ueber HTTP nachladen. Alle Protokollverweise im Quellcode muessen dynamisch sein:

### WebSocket (`src/hooks/useWebSocket.ts`)

```ts
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
return `${protocol}//${host}:${WS_PORT}`;
```

### Kamera-Stream (`src/components/CameraView.tsx`)

```ts
const streamProtocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
const streamUrl = `${streamProtocol}//${window.location.hostname}:${STREAM_PORT}/stream`;
```

**Wichtig:** Wenn `wss://` verwendet wird, muss der WebSocket-Server auf dem Pi ebenfalls TLS unterstuetzen. Gleiches gilt fuer den Kamera-Stream-Server. Falls die Server kein TLS koennen, gibt es zwei Optionen:

1. **Reverse-Proxy** (Caddy oder nginx) terminiert TLS und leitet intern auf `ws://` / `http://` weiter
2. **TLS direkt im Server** einbauen (Python-Beispiel unten)

### Python-WebSocket-Server mit TLS

```python
import ssl
import asyncio
import websockets

ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_ctx.load_cert_chain(
    certfile='/home/pi/amr-projekt/dashboard/amr.local+5.pem',
    keyfile='/home/pi/amr-projekt/dashboard/amr.local+5-key.pem'
)

async def handler(ws):
    async for msg in ws:
        await ws.send(msg)

async def main():
    async with websockets.serve(handler, '0.0.0.0', 9090, ssl=ssl_ctx):
        await asyncio.Future()

asyncio.run(main())
```

## Alte Pi-CA entfernen

Falls zuvor eine CA direkt auf dem Pi erzeugt wurde (`mkcert pi@amr`), diese aufraeumen:

### Auf dem Pi

```bash
mkcert -uninstall
rm -rf ~/.local/share/mkcert
```

### Auf dem Mac (Schluesselbundverwaltung)

1. Schluesselbundverwaltung oeffnen: `open /Applications/Utilities/Keychain\ Access.app`
2. Links: **System** auswaehlen
3. Oben: **Zertifikate** Tab
4. Suche: `mkcert pi@amr`
5. Rechtsklick → **Loeschen**

Alternativ per Terminal:

```bash
sudo security delete-certificate -c "mkcert pi@amr" /Library/Keychains/System.keychain
```

## Zusammenfassung: Checkliste neuer Mac

| Schritt                                                                                   | Befehl                                                                                            |
|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| 1. mkcert installieren                                                                    | `brew install mkcert nss`                                                                         |
| 2. CA registrieren                                                                        | `mkcert -install`                                                                                 |
| 3. Root-CA des Zertifikat-Macs importieren (falls anderer Mac das Zertifikat erzeugt hat) | `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain rootCA.pem` |
| 4. Browser neu starten                                                                    | `Cmd+Q` → Chrome/Safari oeffnen                                                                    |
| 5. Dashboard aufrufen                                                                     | `https://amr.local:5173/`                                                                         |

## Fehlerbehebung

| Symptom                                          | Ursache                                         | Loesung                                                     |
|--------------------------------------------------|-------------------------------------------------|------------------------------------------------------------|
| Chrome: "Nicht sicher" trotz gueltigem Zertifikat | Mixed Content (HTTP-Ressourcen auf HTTPS-Seite) | Alle `ws://` → `wss://`, alle `http://` → `https://`       |
| Chrome: Zertifikat nicht vertrauenswuerdig        | CA nicht im Chrome Root Store                   | `brew install nss`, dann `mkcert -install` erneut          |
| Safari funktioniert, Chrome nicht                | Chrome nutzt eigenen Root Store                 | `nss` installieren, `mkcert -uninstall && mkcert -install` |
| WebSocket verbindet nicht                        | WS-Server spricht kein TLS                      | TLS im Server aktivieren oder Reverse-Proxy nutzen         |
| Zertifikat ungueltig bei IP-Zugriff               | IP nicht im SAN                                 | Zertifikat mit allen IPs neu generieren                    |
| Zertifikat ungueltig nach Netzwerkwechsel         | Neue IP nicht im SAN                            | `amr.local` statt IP verwenden                             |
