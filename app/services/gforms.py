from googleapiclient.discovery import build
from app.core.utils import handle_error, configure_logging, logging

configure_logging()

class GoogleFormsHelper:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = self._get_forms_service()

    def _get_forms_service(self):
        """Builds and returns the Google Forms service."""
        return build('forms', 'v1', credentials=self.credentials)

    def create_form(self, title):
        """Creates a new Google Form with the given title."""
        logging.info(f"Creating form with title: {title}")
        try:
            form = self.service.forms().create(
                body={'info': {'title': title}}
            ).execute()
            form_id = form.get('formId')
            logging.info(f"Form created with id: {form_id}")
            return form
        except Exception as e:
            handle_error(f"Error creating form with title '{title}'", e)
            return None

    def get_form(self, form_id):
        """Retrieves a Google Form by its ID."""
        logging.info(f"Getting form with id: {form_id}")
        try:
            form = self.service.forms().get(formId=form_id).execute()
            logging.info(f"Form retrieved with id: {form_id}")
            return form
        except Exception as e:
            handle_error(f"Error getting form with ID {form_id}", e)
            return None

    def update_form(self, form_id, requests):
        """Updates a Google Form with the given requests."""
        logging.info(f"Updating form with id: {form_id}")
        try:
            form = self.service.forms().batchUpdate(
                formId=form_id, body={'requests': requests}
            ).execute()
            logging.info(f"Form updated with id: {form_id}")
            return form
        except Exception as e:
            handle_error(f"Error updating form with ID {form_id}", e)
            return None
