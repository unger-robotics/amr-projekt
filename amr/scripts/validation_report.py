#!/usr/bin/env python3
"""
Gesamt-Validierungsbericht-Generator fuer den AMR-Roboter.

Liest JSON-Ergebnisdateien aus dem scripts/-Verzeichnis und generiert
einen Markdown-Report mit Pass/Fail-Bewertung aller Testbereiche.

Standalone-Skript ohne ROS2-Abhaengigkeit (nur json, math, datetime, os, pathlib).

Verwendung:
    python3 validation_report.py
    python3 validation_report.py /pfad/zu/ergebnissen/

Ergebnis: validation_report_YYYYMMDD.md im Skript-Verzeichnis.
"""

import json
import math
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
    # --- Encoder ---
    {
        'bereich': 'Encoder',
        'kriterium': 'Ticks/Rev',
        'anforderung': '740-760',
        'datei': 'encoder',
        'pfad': None,  # Aggregation ueber pruef_fn
        'pruef_fn': lambda daten: _encoder_ticks_check(daten),
    },
    # --- Motor ---
    {
        'bereich': 'Motor',
        'kriterium': 'Deadzone (PWM)',
        'anforderung': '30-40',
        'datei': 'motor',
        'pfad': 'config.pwm_deadzone',
        'pruef': lambda v: 30 <= v <= 40 if v is not None else None,
    },
    {
        'bereich': 'Safety',
        'kriterium': 'Failsafe',
        'anforderung': '400-600 ms',
        'datei': 'motor',
        'pfad': 'failsafe.timeout_measured_ms',
        'pruef': lambda v: 400 <= v <= 600 if v is not None else None,
    },
    {
        'bereich': 'Safety',
        'kriterium': 'Failsafe ausgeloest',
        'anforderung': 'true',
        'datei': 'motor',
        'pfad': 'failsafe.failsafe_triggered',
        'pruef': lambda v: v is True if v is not None else None,
    },
    # --- PID ---
    {
        'bereich': 'PID',
        'kriterium': 'Anstiegszeit',
        'anforderung': '< 5000 ms',
        'datei': 'pid',
        'pfad': 'rise_time_ms',
        'pruef': lambda v: v < 5000 if v is not None else None,
    },
    {
        'bereich': 'PID',
        'kriterium': 'Ueberschwingen',
        'anforderung': '< 15%',
        'datei': 'pid',
        'pfad': 'overshoot_pct',
        'pruef': lambda v: v < 15.0 if v is not None else None,
    },
    # --- Kinematik ---
    {
        'bereich': 'Kinematik',
        'kriterium': 'Geradeaus-Fehler',
        'anforderung': '< 5%',
        'datei': 'kinematic',
        'pfad': None,
        'pruef_fn': lambda daten: _kinematic_gerade_check(daten),
    },
    {
        'bereich': 'Kinematik',
        'kriterium': 'Laterale Drift',
        'anforderung': '< 50 mm',
        'datei': 'kinematic',
        'pfad': None,
        'pruef_fn': lambda daten: _kinematic_drift_check(daten),
    },
    {
        'bereich': 'Kinematik',
        'kriterium': 'Drehwinkel-Fehler',
        'anforderung': '< 5 deg',
        'datei': 'kinematic',
        'pfad': None,
        'pruef_fn': lambda daten: _kinematic_drehung_check(daten),
    },
    # --- UMBmark ---
    {
        'bereich': 'UMBmark',
        'kriterium': 'E_max_syst',
        'anforderung': '< 50 mm',
        'datei': 'umbmark',
        'pfad': 'ergebnisse.E_max_syst_mm',
        'pruef': lambda v: v < 50.0 if v is not None else None,
    },
    # --- SLAM ---
    {
        'bereich': 'SLAM',
        'kriterium': 'ATE',
        'anforderung': '< 0.20 m',
        'datei': 'slam',
        'pfad': 'ate_m',
        'pruef': lambda v: v < 0.20 if v is not None else None,
    },
    # --- Navigation ---
    {
        'bereich': 'Navigation',
        'kriterium': 'xy-Genauigkeit',
        'anforderung': '< 0.10 m',
        'datei': 'nav',
        'pfad': None,
        'pruef_fn': lambda daten: _nav_xy_check(daten),
    },
    {
        'bereich': 'Navigation',
        'kriterium': 'Gier-Genauigkeit',
        'anforderung': '< 0.15 rad',
        'datei': 'nav',
        'pfad': None,
        'pruef_fn': lambda daten: _nav_yaw_check(daten),
    },
    # --- Docking ---
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
        'pfad': None,
        'pruef_fn': lambda daten: _docking_versatz_check(daten),
    },
]

# Forschungsfragen-Zuordnung
FF_ZUORDNUNG = {
    'FF1': {
        'titel': 'Echtzeit (PID + Safety)',
        'bereiche': ['PID', 'Safety'],
    },
    'FF2': {
        'titel': 'Praezision (Encoder + Kinematik + UMBmark + SLAM + Navigation)',
        'bereiche': ['Encoder', 'Kinematik', 'UMBmark', 'SLAM', 'Navigation'],
    },
    'FF3': {
        'titel': 'Docking (ArUco-Marker)',
        'bereiche': ['Docking'],
    },
}


# ===========================================================================
# Aggregations-Hilfsfunktionen fuer pruef_fn
# ===========================================================================

def _encoder_ticks_check(daten):
    """Mittelwert aus recommended_ticks_per_rev_left/right, pruefe 740-760."""
    if not isinstance(daten, dict):
        return (None, None)
    left = daten.get('recommended_ticks_per_rev_left')
    right = daten.get('recommended_ticks_per_rev_right')
    if left is None or right is None:
        return (None, None)
    mittel = (left + right) / 2.0
    passed = 740 <= mittel <= 760
    return (round(mittel, 1), passed)


def _kinematic_gerade_check(daten):
    """Strecken-Fehler aus Geradeausfahrt-Test, pruefe < 5%."""
    erg = _finde_kinematic_test(daten, 'Geradeausfahrt')
    if erg is None:
        return (None, None)
    val = erg.get('strecke_fehler_pct')
    if val is None:
        return (None, None)
    return (round(val, 2), val < 5.0)


def _kinematic_drift_check(daten):
    """Laterale Drift aus Geradeausfahrt-Test, pruefe < 50 mm."""
    erg = _finde_kinematic_test(daten, 'Geradeausfahrt')
    if erg is None:
        return (None, None)
    val = erg.get('laterale_drift_m')
    if val is None:
        return (None, None)
    val_mm = val * 1000.0
    return (f'{val_mm:.1f} mm', val_mm < 50.0)


def _kinematic_drehung_check(daten):
    """Max. Winkelfehler aus 90-Grad-Drehung, pruefe < 5 deg."""
    erg = _finde_kinematic_test(daten, '90-Grad-Drehung')
    if erg is None:
        return (None, None)
    val = erg.get('max_fehler_deg')
    if val is None:
        return (None, None)
    return (round(val, 2), val < 5.0)


def _finde_kinematic_test(daten, testname):
    """Findet einen Test in der Kinematik-Ergebnis-Liste (Array)."""
    if not isinstance(daten, list):
        return None
    for eintrag in daten:
        if isinstance(eintrag, dict) and eintrag.get('test') == testname:
            return eintrag
    return None


def _nav_xy_check(daten):
    """Max. xy_error ueber alle Waypoints, pruefe < 0.10 m."""
    if not isinstance(daten, dict):
        return (None, None)
    waypoints = daten.get('waypoints')
    if not waypoints or not isinstance(waypoints, list):
        return (None, None)
    errors = [w['xy_error'] for w in waypoints
              if isinstance(w, dict) and 'xy_error' in w
              and not math.isnan(w['xy_error'])]
    if not errors:
        return (None, None)
    max_err = max(errors)
    return (f'{max_err:.4f} m', max_err < 0.10)


def _nav_yaw_check(daten):
    """Max. abs(yaw_error) ueber alle Waypoints, pruefe < 0.15 rad."""
    if not isinstance(daten, dict):
        return (None, None)
    waypoints = daten.get('waypoints')
    if not waypoints or not isinstance(waypoints, list):
        return (None, None)
    errors = [abs(w['yaw_error']) for w in waypoints
              if isinstance(w, dict) and 'yaw_error' in w
              and not math.isnan(w['yaw_error'])]
    if not errors:
        return (None, None)
    max_err = max(errors)
    return (f'{max_err:.4f} rad', max_err < 0.15)


def _docking_versatz_check(daten):
    """Lateraler Versatz: pruefe mittlerer_versatz_cm oder mittlerer_versatz_px <= 2."""
    if not isinstance(daten, dict):
        return (None, None)
    stat = daten.get('statistik')
    if not isinstance(stat, dict):
        return (None, None)
    # Bevorzuge cm-Key (nach Fix in docking_test.py), Fallback auf px-Key
    val = stat.get('mittlerer_versatz_cm')
    einheit = 'cm'
    if val is None:
        val = stat.get('mittlerer_versatz_px')
        einheit = 'px'
    if val is None:
        return (None, None)
    return (f'{val:.1f} {einheit}', val <= 2.0)


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

    Unterstuetzt zwei Modi:
    - 'pruef' + 'pfad': Einfacher Wert-Lookup ueber Punkt-Pfad, dann Lambda
    - 'pruef_fn': Aggregationsfunktion, erhaelt das gesamte Daten-Dict,
      gibt (wert, passed) zurueck

    Rueckgabe: (wert_str, status_str)
        wert_str:   Formatierter Messwert oder 'AUSSTEHEND'
        status_str: 'PASS', 'FAIL', oder 'AUSSTEHEND'
    """
    datei_key = kriterium['datei']
    daten = alle_daten.get(datei_key)

    if daten is None:
        return ('AUSSTEHEND', 'AUSSTEHEND')

    # Modus 1: pruef_fn (Aggregation ueber gesamtes Dict/Liste)
    if 'pruef_fn' in kriterium:
        wert, passed = kriterium['pruef_fn'](daten)
        if wert is None:
            return ('N/A', 'AUSSTEHEND')
        if passed is None:
            return (str(wert), 'AUSSTEHEND')
        return (str(wert), 'PASS' if passed else 'FAIL')

    # Modus 2: Einfacher pfad + pruef Lambda
    pfad = kriterium.get('pfad')
    if pfad is None:
        return ('N/A', 'AUSSTEHEND')

    wert = wert_aus_pfad(daten, pfad)

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
