import os
import json
from dotenv import load_dotenv

class Config:
    def __init__(self, env_path=".env"):
        load_dotenv(dotenv_path=env_path)

        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
        self.GOOGLE_DRIVE_PROJECT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PROJECT_FOLDER_ID")
        self.GOOGLE_DRIVE_INPUT_FOLDER_NAME = os.getenv("GOOGLE_DRIVE_INPUT_FOLDER_NAME", "new_menus")
        self.GOOGLE_PROJECT_UUID = os.getenv("GOOGLE_PROJECT_UUID", "your-project-id")
        self.GOOGLE_OAUTH2_FILE = os.getenv("GOOGLE_OAUTH2_FILE")
        self.GOOGLE_PROJECT_SCOPES = json.loads(os.getenv('GOOGLE_PROJECT_SCOPES'))
        self.YOUR_EMAIL = os.getenv("YOUR_EMAIL")

    def get_org_config(self, org_id):
        """
        Placeholder for organization-specific configuration.
        """
        return {}
