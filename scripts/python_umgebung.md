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

# 5. Gemini API-Schlüssel-Datei anlegen (https://aistudio.google.com/app/apikey)
vim /home/pi/amr-projekt/scripts/.gemini_api.key

# 6. Skripte ausführen und testen
./gemini_modelle_auflisten.py

./gemini_abfrage.py "Was ist ROS2?"

# Jupyter Lab
# venv erstellen und aktivieren
python3 -m venv .venv
source .venv/bin/activate

# Pakete installieren
pip install --upgrade pip
pip install jupyterlab numpy matplotlib scipy

# PDF-Export (nbconvert + LaTeX)
pip install nbconvert[webpdf]
playwright install chromium

# Jupyter Lab starten
jupyter lab --no-browser --ip=0.0.0.0 --port=8888

# Notebook als PDF exportieren
jupyter nbconvert --to webpdf trajektorienanalyse.ipynb

# venv verlassen
deactivate
```
