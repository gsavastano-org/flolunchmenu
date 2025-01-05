import os
import json
from dotenv import load_dotenv

class Config:
    def __init__(self, env_path=".env"):
        load_dotenv(dotenv_path=env_path)

        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.YOUR_EMAIL = os.getenv("YOUR_EMAIL")
        self.GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.INPUT_FOLDER_NAME = "new_menus"
        self.SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
        self.SCOPES = json.loads(os.getenv('SCOPES'))

    def get_org_config(self, org_id):
        """
        Placeholder for organization-specific configuration.
        """
        return {}
