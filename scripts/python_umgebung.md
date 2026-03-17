```bash
# 1. Virtuelle Umgebung erstellen
python3 -m venv .venv

# 2. Umgebung für das aktuelle Terminal aktivieren
source .venv/bin/activate

# 3. Benötigte Bibliothek installieren
pip install --upgrade pip
pip install requests

# 4. Beide Skripte ausführbar machen
chmod +x *.py

# 5. API-Schlüssel-Datei anlegen (WICHTIG: Ersetze "DEIN_API_KEY" mit deinem echten Schlüssel!)
echo "REDACTED_API_KEY" > GEMINI_API_KEY

# 6. Skripte ausführen und testen
./gemini_modelle_auflisten.py

./gemini_abfrage.py "Was ist ROS2?"

# 7. Wenn du fertig bist: Virtuelle Umgebung wieder verlassen
deactivate
```
