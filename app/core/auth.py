from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app.core.utils import logging
import os

class GoogleAuth:
    def __init__(self, config):
        self.config = config
        self.credentials = None

    def authenticate(self):
        """Authenticates the user using OAuth 2.0 and stores credentials."""
        creds = None
        # Use a known writable location for token.json (e.g., user's home directory)
        token_path = os.path.join(os.path.expanduser("~"), "token.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.config.GOOGLE_PROJECT_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logging.info("Refreshing Google API token...")
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.GOOGLE_OAUTH2_FILE,
                    self.config.GOOGLE_PROJECT_SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.credentials = creds
        return creds

    def get_credentials(self):
        """Returns the user's credentials."""
        if not self.credentials:
            self.credentials = self.authenticate()
        return self.credentials