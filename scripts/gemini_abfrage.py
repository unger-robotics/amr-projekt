#!/usr/bin/env python3
"""
Zweck: Kommandozeilen-Client zur direkten Textgenerierung über die Gemini API.
echo "GEMINI_API_KEY" > scripts/.gemini_api.key
source .venv/bin/activate
pip install requests
Aufruf: ./scripts/gemini_abfrage.py [Was ist Docker?]
Aufruf: ./scripts/gemini_abfrage.py "Beantworte die folgenden 5 Fragen ausschließlich basierend auf dem nachstehenden Text der Dokumentation.

Fragen:

1. Wie ist das Drei-Ebenen-Modell aufgebaut und welche Komponenten bilden Ebene A?

2. Welche Funktion erfuellt der redundante CAN-Notstopp-Pfad und wie verhaelt sich seine Latenz?

3. Wie teilt das FreeRTOS Dual-Core-Pattern die Aufgaben auf?

4. Warum wird ROS 2 in einem Docker-Container im Host-Network-Modus ausgefuehrt?

5. Wie loest die Vision-Pipeline das Python-Kompatibilitaetsproblem?" -f docs/systemdokumentation.md

Abhängigkeiten: Python 3.x, externe Bibliothek `requests`.
Umgebung: Linux/macOS/Windows Kommandozeile.
Einschränkungen: Setzt die Datei `scripts/.gemini_api.key` im Ausführungsverzeichnis voraus.
"""

import os
import sys
from datetime import datetime

import requests

# Globale Verhaltensregeln für das KI-Modell (System Instructions)
SYSTEM_VORGABE = (
    "Agiere als wissenschaftlich-technischer Assistent und Code-Reviewer. Die Zielgruppe umfasst sowohl technische Laien als auch Fachexperten/Ingenieure. "
    "Formuliere ausschließlich aktiv und neutral. Verwende weder 'du' noch 'wir', verzichte auf jegliche Moderationsfloskeln und vermeide unklare Verweise ohne expliziten Bezug. "
    "Beginne den Text mit einer klar formulierten Leitfrage, die den Untersuchungsgegenstand eingrenzt. "
    "Strukturiere jede Argumentation nach dem strikten Ablaufschema: Daten -> Regel -> Schluss -> Konsequenz. Behandle in jedem Abschnitt exakt ein Thema. "
    "Nutze zur Strukturierung von Sachtexten Fließtext, Listen, Tabellen, Rechenbeispiele oder Visualisierungen, wenn sie die Verständlichkeit steigern. "
    "Verankere Fachbegriffe beim ersten Auftreten zwingend durch eine kurze, greifbare Erklärung (physische Entsprechung), sodass der Text ohne Zusatzwissen verstanden wird. "
    "Nenne Annahmen und Randbedingungen immer vor der eigentlichen Bewertung. Trenne Ursache und Wirkung sauber: Benenne für jede Bewertung das zugrundeliegende Kriterium ohne versteckte Kausalannahmen. "
    "Versehe jede Zahl ausnahmslos mit Einheit, Bezug, Referenzwert und Quelle (Beispiel: 'Lateraldrift 2,1 cm (Messung Kapitel 6, Referenz: <= 5 cm)'). "
    "Wende bei ausführbarem Code und Admin-Befehlen das Prinzip 'Simple is best, teile und herrsche' an (Fokus auf C/C++, Python, React+TypeScript+Vite+Tailwind CSS). "
    "Dokumentiere Skripte zwingend hinsichtlich Zweck, Aufruf, Abhängigkeiten, Umgebung und Einschränkungen. Folge dabei der projektüblichen Kommentarkonvention (Doxygen, JSDoc, Docstrings). "
    "Fasse Terminal-Befehle stets kompakt zum Kopieren zusammen. "
    "Gib bei Code-Artefakten immer die Testbarkeit an, einschließlich des erwarteten Ein-/Ausgabeverhaltens und relevanter Grenzwerte. "
    "Formatiere die Antwort in GFM (GitHub Flavored Markdown). Nutze LaTeX ausschließlich für mathematische Formeln (Inline mit $, Display mit $$). "
    "Beende die Antwort mit einem knappen, merkfähigen Schluss oder Fazit, das sich ausschließlich auf die zuvor gezeigten Daten zurückführen lässt."
)


def lese_api_schluessel() -> str:
    """Liest den API-Schlüssel sicher aus der versteckten lokalen Konfigurationsdatei."""
    skript_verzeichnis = os.path.dirname(os.path.abspath(__file__))
    schluessel_datei = os.path.join(skript_verzeichnis, ".gemini_api.key")

    try:
        with open(schluessel_datei, encoding="utf-8") as datei:
            api_key = datei.read().strip()
        if not api_key:
            raise ValueError(f"Die Datei '{schluessel_datei}' ist leer.")
        return api_key
    except FileNotFoundError as err:
        raise FileNotFoundError(
            f"Die Datei '{schluessel_datei}' fehlt. Bitte anlegen und den Schlüssel einfügen."
        ) from err


def hole_prompt() -> str:
    """Extrahiert den Prompt und liest optional referenzierte Dateien ein."""
    import argparse

    parser = argparse.ArgumentParser(description="Gemini API CLI-Client")
    parser.add_argument("prompt_text", nargs="*", help="Der eigentliche Fragstext")
    parser.add_argument(
        "-f", "--file", type=str, help="Pfad zu einer Kontext-Datei (z.B. systemdokumentation.md)"
    )

    args = parser.parse_args()

    prompt = " ".join(args.prompt_text)

    # Dateiinhalt anhaengen, falls Parameter -f gesetzt ist
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                datei_inhalt = f.read()
            prompt += f"\n\n--- KONTEXT AUS DATEI ({args.file}) ---\n{datei_inhalt}"
        except Exception as e:
            raise OSError(f"Fehler beim Lesen der Datei '{args.file}': {e}") from e

    # Fallback auf interaktive Eingabe, falls nichts uebergeben wurde
    if not prompt.strip():
        prompt = input("Gib deinen Prompt an das Modell ein (beende mit Enter):\n> ")

    if not prompt.strip():
        raise ValueError("Die Eingabe darf nicht leer sein. Abbruch.")
    return prompt


def main() -> None:
    """Steuert den Ablauf von Eingabe, API-Aufruf und Dateiexport."""
    try:
        api_key = lese_api_schluessel()
        mein_prompt = hole_prompt()
    except Exception as fehler:
        print(f"Initialisierungsfehler: {fehler}", file=sys.stderr)
        sys.exit(1)

    MODEL_ID = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={api_key}"

    # Datenstruktur für die REST-API initialisieren
    daten_nutzlast = {
        "system_instruction": {"parts": [{"text": SYSTEM_VORGABE}]},
        "contents": [{"parts": [{"text": mein_prompt}]}],
    }
    header = {"Content-Type": "application/json"}

    print("Anfrage wird verarbeitet, bitte warten...\n")

    try:
        antwort = requests.post(url, headers=header, json=daten_nutzlast, timeout=120)
        antwort.raise_for_status()

        antwort_daten = antwort.json()
        generierter_text = antwort_daten["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.RequestException as netzwerk_fehler:
        print(f"Netzwerk- oder API-Fehler: {netzwerk_fehler}", file=sys.stderr)
        if "antwort" in locals() and antwort.text:
            print(f"Details von der API: {antwort.text}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError) as parse_fehler:
        print(
            f"Fehler beim Lesen der API-Antwort (unerwartetes Datenformat): {parse_fehler}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Dateiexport mit Zeitstempel
    zeitstempel = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dateiname = f"antwort_{zeitstempel}.md"

    try:
        with open(dateiname, "w", encoding="utf-8") as export_datei:
            export_datei.write(f"# Prompt: {mein_prompt}\n\n")
            export_datei.write(generierter_text)
        print(f"Erfolg: Die Antwort wurde in '{dateiname}' gespeichert.")
    except OSError as io_fehler:
        print(f"Schreibfehler beim Speichern der Datei: {io_fehler}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
