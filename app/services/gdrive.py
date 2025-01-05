from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.core.utils import configure_logging, handle_error, logging

configure_logging()

class GoogleDriveHelper:
    def __init__(self, credentials):
        self.credentials = credentials
        self.drive_service = self._get_drive_service()

    def _get_drive_service(self):
        """Builds and returns the Google Drive service."""
        return build('drive', 'v3', credentials=self.credentials)

    def get_file_id(self, file_name, parent_folder_id):
        """Retrieves the ID of a file by its name within a specific parent folder."""
        logging.info(f"Getting file id for file: {file_name} in folder: {parent_folder_id}")
        try:
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
        except Exception as e:
            handle_error(f"Error getting file ID for {file_name}", e)
            return None

    def get_folder_id(self, folder_name, parent_folder_id):
        """Retrieves the ID of a folder by its name."""
        logging.info(f"Getting folder id for folder: {folder_name} in folder: {parent_folder_id}")
        try:
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
        except Exception as e:
            handle_error(f"Error getting folder ID for {folder_name}", e)
            return None

    def create_folder(self, folder_name, parent_folder_id):
        """Creates a new folder."""
        logging.info(f"Creating folder: {folder_name} in folder: {parent_folder_id}")
        try:
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
        except Exception as e:
            handle_error(f"Error creating folder {folder_name}", e)
            return None

    def upload_image(self, file_path, file_name, parent_folder_id):
        """Uploads an image to Google Drive."""
        logging.info(f"Uploading image: {file_name} to folder: {parent_folder_id}")
        try:
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
        except Exception as e:
            handle_error(f"Error uploading image {file_name}", e)
            return None

    def get_form_webViewLink(self, form_id):
        """Retrieves the webViewLink of a form by its ID."""
        try:
            file = self.drive_service.files().get(fileId=form_id, fields="webViewLink").execute()
            return file.get('webViewLink')
        except Exception as e:
            handle_error(f"Error getting webViewLink for form {form_id}", e)
            return None

    def move_file(self, file_id, new_parent_id, current_parent_id, new_name=None):
        """Moves a file from one folder to another."""
        logging.info(f"Moving file with id: {file_id} to folder: {new_parent_id}")
        try:
            body = {}
            if new_name:
                body['name'] = new_name

            updated_file = self.drive_service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=current_parent_id,
                body=body,
                fields='id, parents'
            ).execute()
            logging.info(f"File moved successfully. New file id: {updated_file.get('id')}")
            return updated_file.get('id')
        except Exception as e:
            handle_error(f"Error moving file {file_id}", e)
            return None
