import os
import json
from dotenv import load_dotenv
import sys

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    def __init__(self, env_path=".env"):
        # Check if the app is running as a bundled executable
        if getattr(sys, 'frozen', False):
            # If so, use the directory of the executable
            application_path = sys._MEIPASS
        else:
            # Otherwise, use the script's directory
            application_path = os.path.dirname(__file__)

        env_path = os.path.join(application_path, env_path)
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
        prompt_path = os.path.join(application_path, "app/assets/prompt.txt")
        
        # If the GOOGLE_OAUTH2_FILE is not an absolute path, assume it is in the same directory as the app
        self.GOOGLE_OAUTH2_FILE = os.path.join(application_path, self.GOOGLE_OAUTH2_FILE)

        try:
            with open(prompt_path, "r") as prompt_file:
                self.GEMINI_PROMPT = prompt_file.read()
        except FileNotFoundError:
            self.GEMINI_PROMPT = None
            raise ConfigError("Error: prompt.txt file not found.")

    def _get_env(self, key, default=None):
        value = os.getenv(key, default)
        if value is None:
            raise ConfigError(f"Environment variable '{key}' is not set.")
        return value