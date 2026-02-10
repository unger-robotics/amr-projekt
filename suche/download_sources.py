import os
import requests
import time

# Konfiguration
DOWNLOAD_DIR = "AMR_Sources"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

# Liste der Quellen (Priorisierte Auswahl aus amr_pdf_links.md)
# Format: ("Dateiname.pdf", "URL")
sources = [
    # Woche 1
    ("01_Macenski_2022_ROS2_Arch.pdf", "https://arxiv.org/pdf/2211.07752"),
    ("02_Macenski_2023_Nav2_Survey.pdf", "https://arxiv.org/pdf/2307.15236"),
    ("04_Siegwart_2004_Mobile_Robots.pdf", "http://vigir.missouri.edu/~gdesouza/Research/MobileRobotics/Autonomous_Mobile_Robots_Siegwart-Nourbakhsh.pdf"),
    
    # Woche 2
    ("05_Macenski_SLAM_Toolbox.pdf", "https://www.theoj.org/joss-papers/joss.02783/10.21105.joss.02783.pdf"),
    ("06_Hess_2016_Cartographer.pdf", "https://research.google.com/pubs/archive/45466.pdf"),
    ("07_Moore_2014_Robot_Localization.pdf", "https://docs.ros.org/en/lunar/api/robot_localization/html/_downloads/robot_localization_ias13_revised.pdf"),
    ("09_Borenstein_1996_Where_Am_I.pdf", "http://www-personal.umich.edu/~johannb/Papers/pos96rep.pdf"),
    
    # Woche 3 (MDPI Links korrigiert auf Direkt-PDF)
    ("10_Abaza_2025_ESP32_Stack.pdf", "https://www.mdpi.com/1424-8220/25/10/3026/pdf"),
    ("11_Albarran_2023_ESP32_DiffDrive.pdf", "https://dialnet.unirioja.es/descarga/articulo/9366528.pdf"),
    ("12_Yordanov_2025_ESP32_Partitioning.pdf", "https://arxiv.org/pdf/2509.04061"),
    ("13_MDPI_2025_SLAM_Comparison.pdf", "https://www.mdpi.com/2079-9292/14/24/4822/pdf"),
    ("14_Staschulat_2020_RCLC_Executor.pdf", "https://www.ofera.eu/storage/publications/Staschulat_et_al_2020_The_rclc_Executor_Domain-specific_deterministic_scheduling_mechanisms.pdf"),
    
    # Woche 4
    ("15_MDPI_2025_ArUco_Docking.pdf", "https://www.mdpi.com/1424-8220/25/12/3742/pdf"),
    ("16_Li_2024_2DLIW_SLAM.pdf", "https://arxiv.org/pdf/2404.07644"),
    ("18_DeGiorgi_2024_Odom_Calibration.pdf", "https://www.mdpi.com/2218-6581/13/1/7/pdf"),
    ("19_Nguyen_2022_MicroROS_Thesis.pdf", "https://www.diva-portal.org/smash/get/diva2:1670378/FULLTEXT01.pdf"),
    
    # Ergänzung
    ("20_Wang_2024_Scheduling.pdf", "https://www.mdpi.com/2079-9292/13/9/1658/pdf")
]

def download_file(filename, url):
    """Lädt eine Datei herunter, falls sie noch nicht existiert."""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"[SKIP] {filename} existiert bereits.")
        return

    print(f"[LADE] {filename} ...")
    try:
        # Headers setzen, um 403 Forbidden bei arXiv/MDPI zu vermeiden
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"   ✅ Gespeichert.")
        
        # Höflichkeitspause für den Server
        time.sleep(1) 
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Fehler bei {url}: {e}")

def main():
    # Verzeichnis erstellen
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Ordner '{DOWNLOAD_DIR}' erstellt.")
    
    print(f"Starte Download von {len(sources)} Quellen...\n")
    
    for filename, url in sources:
        download_file(filename, url)
        
    print("\n--- Download abgeschlossen ---")
    print(f"Dateien befinden sich in: {os.path.abspath(DOWNLOAD_DIR)}")

if __name__ == "__main__":
    main()
