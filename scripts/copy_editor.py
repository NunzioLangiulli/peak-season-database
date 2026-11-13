"""Moved: the text editor is now part of the Peak Season Admin Studio (admin_studio/studio.py), together with the
Images, Icons and Build & Deploy tabs. This file remains only for compatibility and starts the Studio.
Recommended use:  double-click admin_studio/Avvia_Admin_Studio.bat (Windows) or Avvia_Admin_Studio.sh
"""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent.parent / "admin_studio" / "studio.py"), run_name="__main__")
