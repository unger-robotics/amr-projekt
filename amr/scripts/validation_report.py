#!/usr/bin/env python3
"""
Gesamt-Validierungsbericht-Generator fuer den AMR-Roboter.

Liest JSON-Ergebnisdateien aus dem scripts/-Verzeichnis und generiert
einen Markdown-Report mit Pass/Fail-Bewertung aller Testbereiche.

Standalone-Skript ohne ROS2-Abhaengigkeit (nur json, datetime, os, pathlib).

Verwendung:
    python3 validation_report.py
    python3 validation_report.py /pfad/zu/ergebnissen/

Ergebnis: validation_report_YYYYMMDD.md im Skript-Verzeichnis.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


# ===========================================================================
# Konfiguration: Erwartete Ergebnis-Dateien
# ===========================================================================

ERGEBNIS_DATEIEN = {
    'encoder':   'encoder_results.json',
    'motor':     'motor_results.json',
    'umbmark':   'umbmark_results.json',
    'pid':       'pid_results.json',
    'kinematic': 'kinematic_results.json',
    'slam':      'slam_results.json',
    'nav':       'nav_results.json',
    'docking':   'docking_results.json',
}

# ===========================================================================
# Akzeptanzkriterien (Anforderung -> Prueffunktion)
# ===========================================================================

KRITERIEN = [
    {
        'bereich': 'Encoder',
        'kriterium': 'Ticks/Rev',
        'anforderung': '370-380',
        'datei': 'encoder',
        'pfad': 'ticks_per_rev',
        'pruef': lambda v: 370 <= v <= 380 if v is not None else None,
    },
    {
        'bereich': 'Motor',
        'kriterium': 'Deadzone',
        'anforderung': '30-40',
        'datei': 'motor',
        'pfad': 'deadzone',
        'pruef': lambda v: 30 <= v <= 40 if v is not None else None,
    },
    {
        'bereich': 'PID',
        'kriterium': 'Anstiegszeit',
        'anforderung': '< 500 ms',
        'datei': 'pid',
        'pfad': 'rise_time_ms',
        'pruef': lambda v: v < 500 if v is not None else None,
    },
    {
        'bereich': 'PID',
        'kriterium': 'Ueberschwingen',
        'anforderung': '< 15%',
        'datei': 'pid',
        'pfad': 'overshoot_pct',
        'pruef': lambda v: v < 15.0 if v is not None else None,
    },
    {
        'bereich': 'UMBmark',
        'kriterium': 'Fehlerreduktion',
        'anforderung': '>= 10x',
        'datei': 'umbmark',
        'pfad': 'reduction_factor',
        'pruef': lambda v: v >= 10.0 if v is not None else None,
    },
    {
        'bereich': 'SLAM',
        'kriterium': 'ATE',
        'anforderung': '< 0.20 m',
        'datei': 'slam',
        'pfad': 'ate_m',
        'pruef': lambda v: v < 0.20 if v is not None else None,
    },
    {
        'bereich': 'Navigation',
        'kriterium': 'xy-Genauigkeit',
        'anforderung': '< 10 cm',
        'datei': 'nav',
        'pfad': 'xy_error_cm',
        'pruef': lambda v: v < 10.0 if v is not None else None,
    },
    {
        'bereich': 'Navigation',
        'kriterium': 'Gier-Genauigkeit',
        'anforderung': '< 8 Grad',
        'datei': 'nav',
        'pfad': 'yaw_error_deg',
        'pruef': lambda v: v < 8.0 if v is not None else None,
    },
    {
        'bereich': 'Docking',
        'kriterium': 'Erfolgsquote',
        'anforderung': '>= 80%',
        'datei': 'docking',
        'pfad': 'statistik.erfolgsquote_pct',
        'pruef': lambda v: v >= 80.0 if v is not None else None,
    },
    {
        'bereich': 'Docking',
        'kriterium': 'Lat. Versatz',
        'anforderung': '<= 2 cm',
        'datei': 'docking',
        'pfad': 'statistik.mittlerer_versatz_cm',
        'pruef': lambda v: v <= 2.0 if v is not None else None,
    },
    {
        'bereich': 'micro-ROS',
        'kriterium': 'Odom-Rate',
        'anforderung': '20 Hz +/- 2',
        'datei': 'encoder',
        'pfad': 'odom_rate_hz',
        'pruef': lambda v: 18 <= v <= 22 if v is not None else None,
    },
    {
        'bereich': 'micro-ROS',
        'kriterium': 'Paketverlust',
        'anforderung': '< 0.1%',
        'datei': 'encoder',
        'pfad': 'packet_loss_pct',
        'pruef': lambda v: v < 0.1 if v is not None else None,
    },
    {
        'bereich': 'Safety',
        'kriterium': 'Failsafe',
        'anforderung': '500 ms',
        'datei': 'motor',
        'pfad': 'failsafe_ms',
        'pruef': lambda v: 400 <= v <= 600 if v is not None else None,
    },
    {
        'bereich': 'Ressourcen',
        'kriterium': 'RPi5 CPU',
        'anforderung': '< 80%',
        'datei': 'nav',
        'pfad': 'cpu_usage_pct',
        'pruef': lambda v: v < 80.0 if v is not None else None,
    },
]

# Forschungsfragen-Zuordnung
FF_ZUORDNUNG = {
    'FF1': {
        'titel': 'Echtzeit (PID + micro-ROS)',
        'bereiche': ['PID', 'micro-ROS', 'Safety'],
    },
    'FF2': {
        'titel': 'Praezision (UMBmark + SLAM + Navigation)',
        'bereiche': ['UMBmark', 'SLAM', 'Navigation', 'Encoder'],
    },
    'FF3': {
        'titel': 'Docking (ArUco-Marker)',
        'bereiche': ['Docking'],
    },
}


# ===========================================================================
# Hilfsfunktionen
# ===========================================================================

def lade_json(pfad):
    """Laedt eine JSON-Datei. Gibt None zurueck wenn nicht vorhanden."""
    if not pfad.exists():
        return None
    try:
        with open(pfad, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def wert_aus_pfad(daten, pfad_str):
    """Extrahiert einen Wert aus verschachteltem Dict ueber Punkt-Pfad.

    Beispiel: wert_aus_pfad(d, 'statistik.erfolgsquote_pct')
    entspricht d['statistik']['erfolgsquote_pct']
    """
    if daten is None:
        return None
    teile = pfad_str.split('.')
    aktuell = daten
    for teil in teile:
        if isinstance(aktuell, dict) and teil in aktuell:
            aktuell = aktuell[teil]
        else:
            return None
    return aktuell


def bewerte_kriterium(kriterium, alle_daten):
    """Bewertet ein einzelnes Kriterium gegen die geladenen Daten.

    Rueckgabe: (wert_str, status_str)
        wert_str:   Formatierter Messwert oder 'AUSSTEHEND'
        status_str: 'PASS', 'FAIL', oder 'AUSSTEHEND'
    """
    datei_key = kriterium['datei']
    daten = alle_daten.get(datei_key)

    if daten is None:
        return ('AUSSTEHEND', 'AUSSTEHEND')

    wert = wert_aus_pfad(daten, kriterium['pfad'])

    if wert is None:
        return ('N/A', 'AUSSTEHEND')

    # Prueffunktion anwenden
    ergebnis = kriterium['pruef'](wert)

    if ergebnis is None:
        return (str(wert), 'AUSSTEHEND')

    wert_str = str(wert)
    status_str = 'PASS' if ergebnis else 'FAIL'
    return (wert_str, status_str)


# ===========================================================================
# Report-Generierung
# ===========================================================================

def generiere_report(ergebnis_verzeichnis):
    """Generiert den vollstaendigen Validierungsbericht als Markdown-String."""
    # Alle JSON-Dateien laden
    alle_daten = {}
    for key, dateiname in ERGEBNIS_DATEIEN.items():
        pfad = ergebnis_verzeichnis / dateiname
        alle_daten[key] = lade_json(pfad)

    # Zeitstempel
    jetzt = datetime.now()
    ts = jetzt.strftime('%Y-%m-%d %H:%M')

    # Kriterien bewerten
    bewertungen = []
    for k in KRITERIEN:
        wert_str, status_str = bewerte_kriterium(k, alle_daten)
        bewertungen.append({
            'bereich': k['bereich'],
            'kriterium': k['kriterium'],
            'anforderung': k['anforderung'],
            'wert': wert_str,
            'status': status_str,
        })

    # Zaehlung
    gesamt = len(bewertungen)
    bestanden = sum(1 for b in bewertungen if b['status'] == 'PASS')
    fehlgeschlagen = sum(1 for b in bewertungen if b['status'] == 'FAIL')
    ausstehend = sum(1 for b in bewertungen if b['status'] == 'AUSSTEHEND')

    # Geladene / fehlende Dateien
    geladene = [k for k, v in alle_daten.items() if v is not None]
    fehlende = [k for k, v in alle_daten.items() if v is None]

    # Report zusammenbauen
    zeilen = []
    zeilen.append('# AMR Validierungsbericht')
    zeilen.append('')
    zeilen.append(f'**Datum:** {ts}')
    zeilen.append('**Hardware:** XIAO ESP32-S3 + RPi5 + Cytron MDD3A')
    zeilen.append(f'**Roboter:** AMR Differentialantrieb, 65 mm Raeder, 178 mm Spurbreite')
    zeilen.append('')

    # Zusammenfassung
    zeilen.append('## Zusammenfassung')
    zeilen.append('')
    zeilen.append(f'Bestanden: {bestanden}/{gesamt} Kriterien')
    if fehlgeschlagen > 0:
        zeilen.append(f'Fehlgeschlagen: {fehlgeschlagen}')
    if ausstehend > 0:
        zeilen.append(f'Ausstehend: {ausstehend}')
    zeilen.append('')

    # Datenstatus
    zeilen.append('### Datenquellen')
    zeilen.append('')
    if geladene:
        zeilen.append(f'Geladen: {", ".join(geladene)}')
    if fehlende:
        zeilen.append(f'Fehlend: {", ".join(fehlende)}')
    zeilen.append('')

    # Detailergebnisse
    zeilen.append('## Detailergebnisse')
    zeilen.append('')
    zeilen.append('| Testbereich | Kriterium | Anforderung | Ergebnis | Status |')
    zeilen.append('|-------------|-----------|-------------|----------|--------|')

    for b in bewertungen:
        zeilen.append(
            f"| {b['bereich']} | {b['kriterium']} | {b['anforderung']} "
            f"| {b['wert']} | {b['status']} |")

    zeilen.append('')

    # Forschungsfragen-Zuordnung
    zeilen.append('## Forschungsfragen-Zuordnung')
    zeilen.append('')

    for ff_key, ff_info in FF_ZUORDNUNG.items():
        relevante = [b for b in bewertungen
                     if b['bereich'] in ff_info['bereiche']]

        if not relevante:
            ff_status = 'AUSSTEHEND'
        elif all(b['status'] == 'PASS' for b in relevante):
            ff_status = 'PASS'
        elif any(b['status'] == 'FAIL' for b in relevante):
            ff_status = 'FAIL'
        else:
            ff_status = 'AUSSTEHEND'

        bereiche_str = ', '.join(
            f"{b['bereich']}/{b['kriterium']}={b['status']}" for b in relevante)
        zeilen.append(f'- **{ff_key} ({ff_info["titel"]}):** {ff_status}')
        zeilen.append(f'  - Kriterien: {bereiche_str}')

    zeilen.append('')

    # Gesamtbewertung
    if fehlgeschlagen == 0 and ausstehend == 0:
        zeilen.append('## Gesamtbewertung: BESTANDEN')
    elif fehlgeschlagen > 0:
        zeilen.append('## Gesamtbewertung: NICHT BESTANDEN')
    else:
        zeilen.append('## Gesamtbewertung: UNVOLLSTAENDIG')
    zeilen.append('')

    return '\n'.join(zeilen)


# ===========================================================================
# Hauptprogramm
# ===========================================================================

def main():
    """Hauptprogramm: Report generieren und speichern."""
    # Ergebnis-Verzeichnis bestimmen
    skript_verzeichnis = Path(os.path.dirname(os.path.abspath(__file__)))

    if len(sys.argv) > 1:
        ergebnis_verzeichnis = Path(sys.argv[1])
        if not ergebnis_verzeichnis.is_dir():
            print(f'Fehler: Verzeichnis "{sys.argv[1]}" nicht gefunden.')
            sys.exit(1)
    else:
        ergebnis_verzeichnis = skript_verzeichnis

    print(f'Ergebnis-Verzeichnis: {ergebnis_verzeichnis}')
    print(f'Suche JSON-Dateien...')
    print()

    # Status der Dateien anzeigen
    for key, dateiname in ERGEBNIS_DATEIEN.items():
        pfad = ergebnis_verzeichnis / dateiname
        status = 'gefunden' if pfad.exists() else 'FEHLT'
        print(f'  {dateiname:30s} {status}')

    print()

    # Report generieren
    report = generiere_report(ergebnis_verzeichnis)

    # Ausgabe auf stdout
    print(report)

    # Als Datei speichern
    datum = datetime.now().strftime('%Y%m%d')
    dateiname = f'validation_report_{datum}.md'
    ausgabe_pfad = skript_verzeichnis / dateiname

    with open(ausgabe_pfad, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f'Report gespeichert: {ausgabe_pfad}')


if __name__ == '__main__':
    main()
