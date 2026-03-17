#!/usr/bin/env python3
"""
Zweck: Abfrage und Auflistung verfügbarer Gemini-Modelle über die Google Generative Language API.
echo "GEMINI_API_KEY" > .gemini_api.key
source .venv/bin/activate
pip install requests
Aufruf: ./scripts/gemini_modelle_auflisten.py
Abhängigkeiten: Python 3.x, externe Bibliothek `requests`.
Umgebung: Kommandozeile unter Linux/macOS/Windows.
Einschränkungen: Setzt eine gültige `.gemini_api.key`-Datei im Ausführungsverzeichnis voraus.
"""

import os
import sys

import requests


def lese_api_schluessel() -> str:
    """Liest den API-Schlüssel sicher aus der lokalen Konfigurationsdatei."""
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


def main() -> None:
    """Führt die API-Abfrage aus und formatiert die Konsolenausgabe."""
    try:
        api_key = lese_api_schluessel()
    except Exception as fehler:
        print(f"Initialisierungsfehler: {fehler}", file=sys.stderr)
        sys.exit(1)

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    print("Frage verfügbare Modelle ab...\n")

    try:
        antwort = requests.get(url, timeout=15)
        antwort.raise_for_status()

        daten = antwort.json()

        # Tabellarische Ausgabe formatieren
        print(f"{'Modellname':<40} | {'Version'}")
        print("-" * 55)

        for modell in daten.get("models", []):
            if "generateContent" in modell.get("supportedGenerationMethods", []):
                name = modell.get("name", "Unbekannt")
                version = modell.get("version", "N/A")
                print(f"{name:<40} | {version}")

    except requests.exceptions.RequestException as netzwerk_fehler:
        print(f"\nNetzwerk- oder API-Fehler: {netzwerk_fehler}", file=sys.stderr)
        sys.exit(1)
    except ValueError as parse_fehler:
        print(
            f"\nFehler beim Verarbeiten der API-Antwort: {parse_fehler}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
