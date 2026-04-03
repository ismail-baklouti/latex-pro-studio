"""
Latex Pro Studio - Configuration Manager
Handles .env secrets and persistent user settings.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        # 1. Path Setup
        self.base_dir = Path(__file__).resolve().parent.parent
        self.settings_file = self.base_dir / "settings.json"
        self.env_file = self.base_dir / ".env"
        
        # 2. Load API Keys from .env
        self._init_env()
        
        # 3. Load/Initialize User Preferences
        self.settings = self._load_settings()

    def _init_env(self):
        """Loads the .env file if it exists."""
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info("Environment variables loaded from .env")
        else:
            logger.warning(".env file not found. AI and Citations might be disabled.")

    def _load_settings(self) -> dict:
        """Reads the settings.json file or creates defaults."""
        defaults = {
            "theme": "cosmo",
            "font_size": 12,
            "last_project": "",
            "auto_save": True,
            "show_outline": True
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    user_settings = json.load(f)
                    # Merge user settings with defaults in case new keys were added
                    defaults.update(user_settings)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
        
        return defaults

    def save_settings(self):
        """Writes the current settings dictionary to settings.json."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    # --- API Key Accessors ---

    def get_api_keys(self) -> dict:
        """Returns a dictionary of all loaded API keys."""
        return {
            "gemini": os.getenv("GEMINI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "mendeley_id": os.getenv("MENDELEY_APP_ID"),
            "mendeley_secret": os.getenv("MENDELEY_APP_SECRET"),
            "zotero_id": os.getenv("ZOTERO_USER_ID"),
            "zotero_key": os.getenv("ZOTERO_API_KEY")
        }

    # --- Property Accessors ---

    def get(self, key, default=None):
        """Generic getter for settings."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Generic setter for settings (requires save_settings call afterward)."""
        self.settings[key] = value
        self.save_settings()

    def get_app_theme(self):
        return self.settings.get("theme", "cosmo")

    def get_font_size(self):
        return int(self.settings.get("font_size", 12))