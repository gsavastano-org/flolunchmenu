from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.core.utils import handle_error, logging

class GoogleDriveHelperError(Exception):
    """Custom exception for GoogleDriveHelper errors."""
    pass

class GoogleDriveHelper:
    def __init__(self, credentials):
        self.credentials = credentials
        self.drive_service = self._get_drive_service()

    def _get_drive_service(self):
        """Builds and returns the Google Drive service."""
        return build('drive', 'v3', credentials=self.credentials)

    def get_folder_id(self, folder_name, parent_folder_id=None):
        """Retrieves the ID of a folder by its name."""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            response = self.drive_service.files().list(q=query, fields='files(id, name)').execute()
            folder = response.get('files')
            if folder:
                folder_id = folder[0].get('id')
                logging.info(f"Folder id: {folder_id}")
                return folder_id
            else:
                logging.warning(f"Folder not found: {folder_name}")
                return None
        except Exception as e:
            handle_error(f"Error getting folder ID for '{folder_name}'", e)
            raise GoogleDriveHelperError(f"Could not get folder ID: {e}") from e

    def create_folder(self, folder_name, parent_folder_id=None):
        """Creates a new folder with the given name."""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            logging.info(f"Folder created with id: {folder_id}")
            return folder_id
        except Exception as e:
            handle_error(f"Error creating folder '{folder_name}'", e)
            raise GoogleDriveHelperError(f"Could not create folder: {e}") from e

    def get_file_id(self, file_name, parent_folder_id=None):
        """Retrieves the ID of a file by its name."""
        try:
            query = f"name='{file_name}' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            response = self.drive_service.files().list(q=query, fields='files(id, name)').execute()
            file = response.get('files')
            if file:
                file_id = file[0].get('id')
                logging.info(f"File id: {file_id}")
                return file_id
            else:
                logging.warning(f"File not found: {file_name}")
                return None
        except Exception as e:
            handle_error(f"Error getting file ID for '{file_name}'", e)
            raise GoogleDriveHelperError(f"Could not get file ID: {e}") from e

    def move_file(self, file_id, new_parent_folder_id, old_parent_folder_id, new_name=None):
        """Moves a file to a new folder."""
        logging.info(f"Moving file: {file_id} to folder: {new_parent_folder_id}")
        try:
            # Retrieve the existing parents to remove
            file = self.drive_service.files().get(fileId=file_id, fields='parents, name').execute()
            previous_parents = ",".join(file.get('parents'))

            # File's new metadata.
            file_metadata = {}
            if new_name:
                file_metadata['name'] = new_name

            # Move the file to the new folder
            file = self.drive_service.files().update(
                fileId=file_id,
                body=file_metadata,
                addParents=new_parent_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            logging.info(f"File moved with id: {file.get('id')}")
            return file.get('id')
        except Exception as e:
            handle_error(f"Error moving file '{file_id}'", e)
            raise GoogleDriveHelperError(f"Could not move file: {e}") from e

    def get_form_webViewLink(self, form_id):
        """Retrieves the webViewLink of a form by its ID."""
        logging.info(f"Getting webViewLink for form: {form_id}")
        try:
            file = self.drive_service.files().get(fileId=form_id, fields='webViewLink').execute()
            webViewLink = file.get('webViewLink')
            logging.info(f"webViewLink: {webViewLink}")
            return webViewLink
        except Exception as e:
            handle_error(f"Error getting webViewLink for form '{form_id}'", e)
            raise GoogleDriveHelperError(f"Could not get webViewLink: {e}") from e

    def get_root_folder_id(self):
        """Retrieves the ID of the root folder."""
        logging.info("Getting root folder id")
        try:
            file = self.drive_service.files().get(fileId='root').execute()
            root_folder_id = file.get('id')
            logging.info(f"Root folder id: {root_folder_id}")
            return root_folder_id
        except Exception as e:
            handle_error(f"Error getting root folder ID", e)
            raise GoogleDriveHelperError(f"Could not get root folder ID: {e}") from e

    def upload_file(self, file, file_name, parent_folder_id, mime_type):
        """Uploads a file to Google Drive."""
        logging.info(f"Uploading file: {file_name} to folder: {parent_folder_id}")
        try:
            file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
            media = MediaFileUpload(file, mimetype=mime_type, resumable=True)
            file = self.drive_service.files().create(body=file_metadata,
                                                    media_body=media,
                                                    fields='id').execute()
            logging.info(f"File uploaded with id: {file.get('id')}")
            return file.get('id')
        except Exception as e:
            handle_error(f"Error uploading file '{file_name}'", e)
            raise GoogleDriveHelperError(f"Could not upload file: {e}") from e
