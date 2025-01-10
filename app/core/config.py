import os
import json
from dotenv import load_dotenv

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    def __init__(self, env_path=".env"):
        load_dotenv(dotenv_path=env_path)

        self.GEMINI_API_KEY = self._get_env("GEMINI_API_KEY")
        self.GEMINI_MODEL_NAME = self._get_env("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp")
        self.GOOGLE_DRIVE_PROJECT_FOLDER_ID = self._get_env("GOOGLE_DRIVE_PROJECT_FOLDER_ID")
        self.GOOGLE_PROJECT_UUID = self._get_env("GOOGLE_PROJECT_UUID", "your-project-id")
        self.GOOGLE_OAUTH2_FILE = self._get_env("GOOGLE_OAUTH2_FILE")
        self.GOOGLE_PROJECT_SCOPES = json.loads(self._get_env('GOOGLE_PROJECT_SCOPES'))
        self.YOUR_EMAIL = self._get_env("YOUR_EMAIL")
        self.GEMINI_PROMPT = None

        # Load the prompt from a separate file
        try:
            with open("app/assets/prompt.txt", "r") as prompt_file:
                self.GEMINI_PROMPT = prompt_file.read()
        except FileNotFoundError:
            self.GEMINI_PROMPT = None
            raise ConfigError("Error: prompt.txt file not found.")



    def _get_env(self, key, default=None):
        value = os.getenv(key, default)
        if value is None:
            raise ConfigError(f"Environment variable '{key}' is not set.")
        return value
