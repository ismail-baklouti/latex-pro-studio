import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        # Path logic
        self.base_dir = Path(__file__).resolve().parent.parent
        self.settings_file = self.base_dir / "settings.json"
        self.env_file = self.base_dir / ".env"
        
        # Load .env keys
        self._init_env()
        
        # Load user settings
        self.settings = self._load_settings()

    def _init_env(self):
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info("Environment variables loaded.")
        else:
            # Create a blank .env if it doesn't exist to prevent errors
            self.env_file.touch()



    def _load_settings(self) -> dict:
        defaults = {
            "theme": "cosmo",
            "font_size": 12,
            "last_project": "",
        }
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception as e:
                logger.error(f"Settings error: {e}")
        return defaults

    def load_api_keys(self):
        """Returns keys from .env for the AI Engine."""
        return {
            "gemini": os.getenv("GEMINI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY")
        }

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)