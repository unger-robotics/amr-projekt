#!/usr/bin/env python3
"""
Gemini API Modell-Scanner

Ein Kommandozeilen-Werkzeug zur Abfrage der Google Generative Language API.
Das Skript ermittelt und listet alle verfügbaren KI-Modelle auf, die die
Methode zur Textgenerierung ('generateContent') unterstützen.

Voraussetzungen:
    - Python 3.x
    - Bibliothek `requests` (Installation: `pip install requests`)
    - Eine Datei namens `GEMINI_API_KEY` (ohne Dateiendung) im selben Verzeichnis
      wie dieses Skript. Diese Datei darf ausschließlich den API-Schlüssel enthalten.

Verwendung:
    Das Skript wird ohne zusätzliche Argumente direkt im Terminal ausgeführt:
    $ ./modelle_auflisten.py

Ausgabe:
    Das Skript gibt eine formatierte Liste der unterstützten Modellnamen
    (z. B. 'models/gemini-3.1-pro-preview') direkt auf der Konsole (stdout) aus.
"""

import os
import sys

import requests


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


def main():
    # 1. Konfiguration laden
    try:
        api_key = lese_api_schluessel()
    except Exception as fehler:
        print(f"Initialisierungsfehler: {fehler}", file=sys.stderr)
        sys.exit(1)

    # 2. URL für die ListModels-Methode definieren
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    print("Frage verfügbare Modelle ab...")

    # 3. HTTP-Anfrage mit Fehlerbehandlung durchführen
    try:
        # Senden einer reinen Lese-Anfrage (GET) mit 15 Sekunden Timeout
        antwort = requests.get(url, timeout=15)
        antwort.raise_for_status()  # Wirft Exception bei HTTP-Fehlercodes (4xx, 5xx)

        daten = antwort.json()

        print("\nVerfügbare API-Modelle für Textgenerierung:")
        print("-" * 45)

        # Iterieren durch die Antwort und filtern nach Modellen, die Prompts verarbeiten
        for modell in daten.get("models", []):
            if "generateContent" in modell.get("supportedGenerationMethods", []):
                print(modell["name"])

    except requests.exceptions.RequestException as netzwerk_fehler:
        print(f"\nNetzwerk- oder API-Fehler: {netzwerk_fehler}", file=sys.stderr)
        sys.exit(1)
    except ValueError as parse_fehler:
        print(
            f"\nFehler beim Verarbeiten der API-Antwort (JSON ungültig): {parse_fehler}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
