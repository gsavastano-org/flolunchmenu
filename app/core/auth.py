from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

class GoogleAuth:
    def __init__(self, config):
        self.config = config
        self.credentials = None

    def authenticate(self):
        """Authenticates the user using OAuth 2.0 and stores credentials."""
        creds = None
        token_path = 'token.json'  # File to store user tokens
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.config.GOOGLE_PROJECT_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.GOOGLE_OAUTH2_FILE,  # Your downloaded OAuth credentials
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
