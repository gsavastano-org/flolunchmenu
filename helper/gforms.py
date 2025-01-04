# helper/forms.py
from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleFormsHelper:
    def __init__(self, credentials_path, scopes=None):
        self.credentials_path = credentials_path
        self.scopes = scopes or [
            'https://www.googleapis.com/auth/forms',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = self._load_credentials()
        self.service = self._get_forms_service()

    def _load_credentials(self):
        """Loads credentials from the service account file."""
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes
        )
        return creds

    def _get_forms_service(self):
        """Builds and returns the Google Forms service."""
        return build('forms', 'v1', credentials=self.credentials)

    def create_form(self, title):
        """Creates a new Google Form with the given title."""
        logging.info(f"Creating form with title: {title}")
        form = self.service.forms().create(
            body={'info': {'title': title}}
        ).execute()
        form_id = form.get('formId')
        logging.info(f"Form created with id: {form_id}")
        return form

    def get_form(self, form_id):
        """Retrieves a Google Form by its ID."""
        logging.info(f"Getting form with id: {form_id}")
        form = self.service.forms().get(formId=form_id).execute()
        logging.info(f"Form retrieved with id: {form_id}")
        return form

    def update_form(self, form_id, requests):
        """Updates a Google Form with the given requests."""
        logging.info(f"Updating form with id: {form_id}")
        form = self.service.forms().batchUpdate(
            formId=form_id, body={'requests': requests}
        ).execute()
        logging.info(f"Form updated with id: {form_id}")
        return form
