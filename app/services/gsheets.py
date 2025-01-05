from googleapiclient.discovery import build
from app.core.utils import handle_error, configure_logging, logging

configure_logging()

class GoogleSheetsHelper:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = self._get_sheets_service()

    def _get_sheets_service(self):
        """Builds and returns the Google Sheets service."""
        return build('sheets', 'v4', credentials=self.credentials)

    def create_spreadsheet(self, title):
        """Creates a new Google Spreadsheet with the given title."""
        logging.info(f"Creating spreadsheet with title: {title}")
        try:
            spreadsheet = self.service.spreadsheets().create(
                body={'properties': {'title': title}}
            ).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            logging.info(f"Spreadsheet created with id: {spreadsheet_id}")
            return spreadsheet_id
        except Exception as e:
            handle_error(f"Error creating spreadsheet with title '{title}'", e)
            return None
