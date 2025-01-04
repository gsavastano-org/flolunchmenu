from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleDriveHelper:
    def __init__(self, credentials_path, scopes=None):
        self.credentials_path = credentials_path
        self.scopes = scopes or [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/forms'
        ]
        self.credentials = self._load_credentials()
        self.drive_service = self._get_drive_service()

    def _load_credentials(self):
        """Loads credentials from the service account file."""
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes
        )
        return creds

    def _get_drive_service(self):
        """Builds and returns the Google Drive service."""
        return build('drive', 'v3', credentials=self.credentials)

    def get_file_id(self, file_name, parent_folder_id):
        """Retrieves the ID of a file by its name within a specific parent folder."""
        logging.info(f"Getting file id for file: {file_name} in folder: {parent_folder_id}")
        query = f"name = '{file_name}' and '{parent_folder_id}' in parents and trashed = false"
        response = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webViewLink)'
        ).execute()
        files = response.get('files', [])
        file_id = files[0]['id'] if files else None
        logging.info(f"File id: {file_id} found for file: {file_name}")
        return file_id

    def get_folder_id(self, folder_name, parent_folder_id):
        """Retrieves the ID of a folder by its name."""
        logging.info(f"Getting folder id for folder: {folder_name} in folder: {parent_folder_id}")
        query = f"name = '{folder_name}' and '{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        response = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webViewLink)'
        ).execute()
        files = response.get('files', [])
        folder_id = files[0]['id'] if files else None
        logging.info(f"Folder id: {folder_id} found for folder: {folder_name}")
        return folder_id

    def create_folder(self, folder_name, parent_folder_id):
        """Creates a new folder."""
        logging.info(f"Creating folder: {folder_name} in folder: {parent_folder_id}")
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = self.drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        folder_id = folder.get('id')
        logging.info(f"Folder created with id: {folder_id}")
        return folder_id

    def upload_image(self, file_path, file_name, parent_folder_id):
        """Uploads an image to Google Drive."""
        logging.info(f"Uploading image: {file_name} to folder: {parent_folder_id}")
        file_metadata = {
            'name': file_name,
            'parents': [parent_folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = file.get('id')
        logging.info(f"Image uploaded with id: {file_id}")
        return file_id
    
    def get_form_webViewLink(self, form_id):
        """Retrieves the webViewLink of a form by its ID."""
        file = self.drive_service.files().get(fileId=form_id, fields="webViewLink").execute()
        return file.get('webViewLink')
