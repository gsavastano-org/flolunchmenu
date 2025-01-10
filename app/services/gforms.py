from googleapiclient.discovery import build
from app.core.utils import handle_error, logging

class GoogleFormsHelperError(Exception):
    """Custom exception for GoogleFormsHelper errors."""
    pass

class GoogleFormsHelper:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = self._get_forms_service()

    def _get_forms_service(self):
        """Builds and returns the Google Forms service."""
        return build('forms', 'v1', credentials=self.credentials)

    def create_form(self, title):
        """Creates a new Google Form with the given title."""
        try:
            form = self.service.forms().create(
                body={'info': {'title': title}}
            ).execute()
            form_id = form.get('formId')
            logging.info(f"{form_id}: Form created")
            return form
        except Exception as e:
            handle_error(f"Error creating form with title '{title}'", e)
            raise GoogleFormsHelperError(f"Could not create form: {e}") from e

    def get_form(self, form_id):
        """Retrieves a Google Form by its ID."""
        try:
            form = self.service.forms().get(formId=form_id).execute()
            return form
        except Exception as e:
            handle_error(f"Error getting form with ID {form_id}", e)
            raise GoogleFormsHelperError(f"Could not get form: {e}") from e

    def update_form(self, form_id, requests):
        """Updates a Google Form with the given requests."""
        try:
            form = self.service.forms().batchUpdate(
                formId=form_id, body={'requests': requests}
            ).execute()
            logging.info(f"{form_id}: Form updated")
            return form
        except Exception as e:
            handle_error(f"Error updating form with ID {form_id}", e)
            raise GoogleFormsHelperError(f"Could not update form: {e}") from e
