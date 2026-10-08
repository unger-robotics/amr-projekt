# Messprotokoll P-AD1: Referenzaufnahmen und Auswertungen

P-AD1 ist nach `docs/anforderungsliste-L1.md` (v1.1, Abschnitt 8.2) das Messprotokoll fuer die Pakete K7 und K8. In der Vorbereitung K7-V (`transfer/auftrag-k7v.md`) liegen hier die bag_check-Berichte der Referenzaufnahmen. Die Aufnahmen selbst liegen ausserhalb des Repos unter `~/amr_bags/` auf dem Pi.

| Pfad | Inhalt |
| --- | --- |
| `<JJJJMMTT_HHMM>_<szene>/bag_check.md` | Bericht von `amr/scripts/bag_check.py` |
| `<JJJJMMTT_HHMM>_<szene>/metadata_amr.yaml` | Kopie der Metadaten: Szene, Git-Commit, Launch-Argumente; ohne Umgebungsvariablen und Schluessel |

Erzeugt werden beide Dateien von `amr/scripts/record_reference_bags.sh <szene> <dauer_s>`. Szenen und Topicliste stehen in `amr/pi5/ros2_ws/src/my_bot/config/reference_bags.yaml`, die Bedienung in `docs/ros2/referenz-bags.md`.
