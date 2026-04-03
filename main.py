"""
Latex Pro Studio - v1.0
Developed by: Ismail Baklouti
GitHub: https://github.com/ismail-baklouti
License: MIT
Description: A modular, AI-integrated LaTeX Editor with Mendeley/Zotero Sync.
"""

import sys
import logging
import shutil
import ttkbootstrap as ttk
from pathlib import Path

# Import Modular Components (to be created in subfolders)
from ui.main_window import MainWindow
from core.project_manager import ProjectManager
from core.ai_engine import AIEngine
from utils.config_manager import ConfigManager

# Setup Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class LatexProApp:
    def __init__(self):
        self._setup_environment()
        
        # 1. Initialize Configuration & Theme
        # Using 'cosmo' for a professional 'Blue/White' look
        self.style = ttk.Style(theme="cosmo")
        self.root = self.style.master
        self.root.title("Latex Pro Studio")
        self.root.geometry("1400x900")

        # 2. Initialize Core Logic Engines
        self.config = ConfigManager()
        self.project_manager = ProjectManager()
        self.ai_engine = AIEngine(api_keys=self.config.load_api_keys())

        # 3. Initialize UI
        self.main_ui = MainWindow(
            root=self.root,
            project=self.project_manager,
            ai=self.ai_engine,
            config=self.config
        )

        self._check_latex_path()

    def _setup_environment(self):
        """Enable High DPI for Windows and clean pathing."""
        if sys.platform == "win32":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception as e:
                logger.warning(f"High DPI not enabled: {e}")

    def _check_latex_path(self):
        """Check if pdflatex is installed."""
        if not shutil.which("pdflatex"):
            logger.error("pdflatex not found. Please install MikTeX or TeX Live.")

    def run(self):
        logger.info("Launching Latex Pro Studio...")
        self.root.mainloop()

if __name__ == "__main__":
    app = LatexProApp()
    app.run()