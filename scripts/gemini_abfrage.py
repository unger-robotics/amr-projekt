#!/usr/bin/env python3
"""
Gemini API CLI-Client

Ein Kommandozeilen-Werkzeug zur direkten Abfrage des Gemini-Modells.
Sendet Benutzereingaben (Prompts) zusammen mit vordefinierten Systemanweisungen
an die API und speichert die Antwort in einer Markdown-Datei.

Voraussetzungen:
    - Python 3.x
    - Bibliothek `requests`
    - Eine Datei namens `GEMINI_API_KEY` (ohne Endung) im selben Verzeichnis
      wie dieses Skript, welche ausschließlich den API-Schlüssel enthält.
"""

import os
import sys
from datetime import datetime

import requests

# Globale Verhaltensregeln (System Instructions)
SYSTEM_VORGABE = (
    "Agiere als wissenschaftlicher Assistent. Die Zielgruppe umfasst sowohl technische Laien als auch Fachexperten/Ingenieure. "
    "Formuliere ausschließlich aktiv und neutral. Verwende weder 'du' noch 'wir', verzichte auf jegliche Moderationsfloskeln und vermeide unklare Verweise (wie 'dieser Wert', 'das', 'hier') ohne expliziten Bezug. "
    "Strukturiere jede Antwort nach dem strikten Ablauf: Daten -> Regel -> Schluss -> Konsequenz. "
    "Beginne mit einer klaren Leitfrage und behandle in jedem Abschnitt exakt ein Thema. "
    "Verankere Fachbegriffe beim ersten Auftreten zwingend durch eine kurze, greifbare Erklärung (physische Entsprechung), sodass der Text ohne Zusatzwissen verstanden wird. "
    "Nenne Annahmen und Randbedingungen immer vor der eigentlichen Bewertung. Evidenz steht zwingend vor dem Urteil. "
    "Trenne Ursache und Wirkung sauber. Nenne für jede Bewertung das zugrundeliegende Kriterium. "
    "Versehe jede Zahl ausnahmslos mit Einheit, Bezug, Referenzwert und Quelle. "
    "Formatiere die Antwort in GFM (GitHub Flavored Markdown). Nutze LaTeX für mathematische Formeln (Inline mit $, Display mit $$). "
    "Beende die Antwort mit einem knappen, merkfähigen Schluss, der sich ausschließlich auf die zuvor gezeigten Daten zurückführen lässt und die fachliche Klarheit bestätigt."
)


def lese_api_schluessel() -> str:
    """Liest den API-Schlüssel sicher aus der lokalen Konfigurationsdatei."""
    skript_verzeichnis = os.path.dirname(os.path.abspath(__file__))
    schluessel_datei = os.path.join(skript_verzeichnis, "GEMINI_API_KEY")

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
    """Extrahiert den Prompt aus den Startargumenten oder der interaktiven Eingabe."""
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Gib deinen Prompt an das Modell ein (beende mit Enter):\n> ")

    if not prompt.strip():
        raise ValueError("Die Eingabe darf nicht leer sein. Abbruch.")
    return prompt


def main():
    # 1. Initialisierung und Datenerfassung
    try:
        api_key = lese_api_schluessel()
        mein_prompt = hole_prompt()
    except Exception as fehler:
        print(f"Initialisierungsfehler: {fehler}", file=sys.stderr)
        sys.exit(1)

    # 2. API-Endpunkt und Datenstruktur
    modell_id = "gemini-3.1-pro-preview"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modell_id}:generateContent?key={api_key}"

    daten_nutzlast = {
        "system_instruction": {"parts": [{"text": SYSTEM_VORGABE}]},
        "contents": [{"parts": [{"text": mein_prompt}]}],
    }
    header = {"Content-Type": "application/json"}

    print("Anfrage wird verarbeitet, bitte warten...")

    # 3. HTTP-Anfrage und Fehlerbehandlung
    try:
        antwort = requests.post(url, headers=header, json=daten_nutzlast, timeout=120)
        antwort.raise_for_status()  # Wirft Exception bei HTTP-Fehlercodes (4xx, 5xx)

        antwort_daten = antwort.json()
        generierter_text = antwort_daten["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.RequestException as netzwerk_fehler:
        print(f"\nNetzwerk- oder API-Fehler: {netzwerk_fehler}", file=sys.stderr)
        if "antwort" in locals() and antwort.text:
            print(f"Details von der API: {antwort.text}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError) as parse_fehler:
        print(
            f"\nFehler beim Lesen der API-Antwort (unerwartetes Datenformat): {parse_fehler}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 4. Dateiexport
    zeitstempel = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dateiname = f"antwort_{zeitstempel}.md"

    try:
        with open(dateiname, "w", encoding="utf-8") as export_datei:
            export_datei.write(f"# Prompt: {mein_prompt}\n\n")
            export_datei.write(generierter_text)
        print(f"\nErfolg: Die Antwort wurde in '{dateiname}' gespeichert.")
    except OSError as io_fehler:
        print(f"\nSchreibfehler beim Speichern der Datei: {io_fehler}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
