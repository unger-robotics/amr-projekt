# Farbdesign

### 1. Semantische Nomenklatur

Wir trennen die visuelle Eigenschaft (z. B. „Cyan“) von der systematischen Funktion (z. B. „Primärakzent“). Dies stellt sicher, dass du bei späteren Anpassungen oder bei der Implementierung eines weiteren Themes die Variablennamen im Quellcode nicht umschreiben musst.

### 2. Entwickler-Tabelle

Die folgende Tabelle verknüpft die Hexadezimalwerte mit semantischen CSS-Variablen und definiert den strikten Anwendungsbereich innerhalb der Applikation.

| Funktion                | CSS-Variable        | Hex-Wert  | Anwendungsbereich im Interface                                               |
|-------------------------|---------------------|-----------|------------------------------------------------------------------------------|
| **Hintergrund (Basis)** | `--bg-base`         | `#0B131E` | Main-Viewport, tieferliegende Fläche hinter den Panels.                      |
| **Hintergrund (Panel)** | `--bg-panel`        | `#111D2B` | Container-Hintergrund für linke Navigation, Sensordaten und Karten.          |
| **Text (Label)**        | `--text-secondary`  | `#517C96` | Statische Bezeichner (z. B. „LATENZ“), Einheiten und Achsenbeschriftungen.   |
| **Akzent (Daten)**      | `--accent-primary`  | `#00E5FF` | Dynamische Sensorwerte, Lidar-Punkte, SLAM-Geometrie und Fortschrittsbalken. |
| **Status (Aktiv)**      | `--status-success`  | `#00FF66` | Verbindungsindikatoren und Status-LEDs (z. B. „WebSocket verbunden“).        |
| **Aktion (Kritisch)**   | `--status-critical` | `#FF2A40` | Not-Halt („STOP“-Button) und potenziell kritische Systemwarnungen.           |

### 3. Implementierung

Du definierst diese Werte zentral in der Wurzel des Dokuments. Dadurch machst du die Farben für alle untergeordneten DOM-Elemente global verfügbar.

```css
:root {
  /* Backgrounds */
  --bg-base: #0B131E;
  --bg-panel: #111D2B;

  /* Typography & Accents */
  --text-secondary: #517C96;
  --accent-primary: #00E5FF;

  /* Status */
  --status-success: #00FF66;
  --status-critical: #FF2A40;
}

```


---

### Tailwind CSS Konfiguration

**Randbedingungen:** Tailwind CSS v3.x oder neuer. Die Konfiguration erfolgt in der `tailwind.config.js`.

Wir erweitern das `colors`-Objekt innerhalb von `theme.extend`. Dies erhält die Standard-Farbpalette von Tailwind und fügt die spezifischen Dashboard-Farben nahtlos hinzu.

```javascript
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        'bg-base': '#0B131E',
        'bg-panel': '#111D2B',
        'text-secondary': '#517C96',
        'accent-primary': '#00E5FF',
        'status-success': '#00FF66',
        'status-critical': '#FF2A40',
      }
    }
  },
  plugins: [],
}

```

Du wendest die definierten Variablen im HTML-Markup direkt über die Standard-Präfixe von Tailwind an (z. B. `bg-`, `text-`, `border-`).

**Anwendungsbeispiel:** `<div class="bg-bg-panel text-accent-primary border-status-critical">...</div>`

### LaTeX Farbdefinition

**Voraussetzung:** Das Paket `xcolor` ist in der Präambel eingebunden.
Das Hexadezimal-Format verlangt im `xcolor`-Paket zwingend den Farbmodell-Parameter `HTML`. Du lässt das Raute-Zeichen (`#`) bei der Wertzuweisung weg.

Wir definieren die Farbnamen global in der Präambel des Dokuments. Nutze PascalCase für die Bezeichner, um Überschneidungen mit vordefinierten LaTeX-Farben zu vermeiden.

```latex
\documentclass{article}
\usepackage{xcolor}

% Dashboard Theme Definitionen
\definecolor{BgBase}{HTML}{0B131E}
\definecolor{BgPanel}{HTML}{111D2B}
\definecolor{TextSecondary}{HTML}{517C96}
\definecolor{AccentPrimary}{HTML}{00E5FF}
\definecolor{StatusSuccess}{HTML}{00FF66}
\definecolor{StatusCritical}{HTML}{FF2A40}

\begin{document}

% ...

\end{document}

```

Du rufst die Farben anschließend im Textfluss über `\textcolor` auf oder nutzt sie zur Formatierung in Grafikpaketen wie Ti*k*Z oder pgfplots.

**Anwendungsbeispiel:** `\textcolor{AccentPrimary}{System aktiv: $54.5\,\^\circ\mathrm{C}$}`

---

### JSON-Datenstruktur

Wir strukturieren die Farbpalette als verschachteltes JSON-Objekt. Jeder Farbschlüssel (`key`) enthält den Hexadezimal-String, ein numerisches Array für die RGB-Werte und den funktionalen Bezeichner.

```json
{
  "theme": {
    "amr-dashboard": {
      "colors": {
        "bg-base": {
          "hex": "#0B131E",
          "rgb": [11, 19, 30],
          "label": "Hintergrund (Basis)"
        },
        "bg-panel": {
          "hex": "#111D2B",
          "rgb": [17, 29, 43],
          "label": "Hintergrund (Panel)"
        },
        "text-secondary": {
          "hex": "#517C96",
          "rgb": [81, 124, 150],
          "label": "Text (Label)"
        },
        "accent-primary": {
          "hex": "#00E5FF",
          "rgb": [0, 229, 255],
          "label": "Akzent (Daten)"
        },
        "status-success": {
          "hex": "#00FF66",
          "rgb": [0, 255, 102],
          "label": "Status (Aktiv)"
        },
        "status-critical": {
          "hex": "#FF2A40",
          "rgb": [255, 42, 64],
          "label": "Aktion (Kritisch)"
        }
      }
    }
  }
}

```

Du importierst dieses JSON-Objekt direkt in deine Build-Pipeline (beispielsweise via Webpack, Vite oder Gulp). Dies definiert die Datei als zentrale Referenz ("Single Source of Truth"). Du aktualisierst Farbwerte somit ausschließlich im JSON-Dokument; die Build-Werkzeuge propagieren die Änderungen anschließend automatisch in alle abhängigen Formate (CSS, Tailwind-Konfiguration, TypeScript-Typisierungen).
