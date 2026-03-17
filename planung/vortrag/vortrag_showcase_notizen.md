# Sprechernotizen: AMR Showcase

Diese Notizen sind dein roter Faden fuer die Pandoc-Praesentation (`vortrag_showcase.md`).

---\n
## Folie 1: AMR Showcase
* **Begruessung:** Willkommen! Wir schauen uns heute an, wie man moderne Edge-KI und klassische Robotik fuer rund 700 Euro verheiratet.
* **Fokus:** Wir gehen den Weg des Datenflusses durch – vom dummen Sensorwert bis zur schlauen Cloud-Entscheidung.

## Folie 2: Das Ziel
* **Aufhaenger:** Wer schon mal einen MiR oder Clearpath Roboter gekauft hat, kennt die Preise (25k aufwaerts). Fuer schwere Paletten ist das okay, fuer leichte KLT-Kisten im Gang viel zu teuer.
* **Die Falle:** Viele bauen dann einen Raspberry Pi auf Raeder. Das Resultat: Wenn die CPU voll ausgelastet ist, stottern die Raeder, weil die PWM-Signale aussetzen.
* **Unser Weg:** Die Loesung liegt in der verteilten Architektur.

## Folie 3: Die 4 Saeulen
* **Fokus auf die Grafik (`amr_datenfluss.svg`):** Zeige, wie die Daten fliessen. Es gibt keine Schleifen zurueck, sondern eine klare Pipeline.
* **Erklaerung:** Sensoren liefern Daten. Der Raspberry baut die Karte. Die Cloud greift nur bei strategischen Fragen ein. Der ESP32 setzt die Befehle um.

## Folie 4: Edge-KI
* **Fokus auf die Grafik (`amr_nav2_pipeline.svg`):**
* Der ROS 2 Nav2 Stack ist extrem maechtig, frisst aber CPU.
* Deshalb ist der **Hailo-8L Chip** der Gamechanger. Er haengt per PCIe am Pi 5 und macht die Objekterkennung (YOLOv8) in 34 Millisekunden. Die Haupt-CPU bleibt frei fuer SLAM.

## Folie 5: Aktorik
* **Fokus auf die Grafik (`amr_esp32_dualcore.svg`):**
* Die Trennung der Kerne auf dem ESP32 ist essenziell.
* Wuerde Core 0 (der mit ROS funkt) kurz haengen bleiben, wuerde Core 1 trotzdem weiter die Motoren regeln.
* **Sicherheit:** Erwaehne den CAN-Bus! Faellt der Raspberry Pi komplett aus (Kernel Panic), greift der Hardware-CAN-Bus und stoppt das Geraet vor der Treppe.

## Folie 6: Semantische Cloud-Entscheidung
* **Das Highlight:** Standard-Roboter drehen um, wenn etwas im Weg steht.
* Unser Roboter erkennt durch YOLO und Gemini, *was* im Weg steht.
* Steht eine Palette im Weg, wird umgeplant. Steht ein Mensch im Weg, wartet der Roboter und gibt eine akustische Warnung ueber den Lautsprecher aus.

## Folie 7: Live-Demo
* Wechsel nun in das Terminal und starte den Stack.
* Zeige im Browser das Dashboard.
* Erwaehne, dass die micro-ROS Verbindung bei stabilen 921.600 Baud laeuft und die Einweg-Latenz im einstelligen Millisekundenbereich liegt.
