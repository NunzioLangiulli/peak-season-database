"""Spostato: l'editor dei testi fa ora parte del Peak Season Admin Studio (admin_studio/studio.py), insieme alle schede
Immagini, Icone e Build & Deploy. Questo file resta solo per compatibilità e avvia lo studio.
Uso consigliato:  doppio clic su admin_studio/Avvia_Admin_Studio.bat (Windows) o Avvia_Admin_Studio.sh
"""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent.parent / "admin_studio" / "studio.py"), run_name="__main__")
