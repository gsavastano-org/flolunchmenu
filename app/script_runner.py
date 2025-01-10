# --- Core Logic Layer: script_runner.py ---
import asyncio
import json
from datetime import datetime
from app.core.utils import configure_logging, is_valid_jpeg
from app.core.auth import GoogleAuth
from app.services.gdrive import GoogleDriveHelper, GoogleDriveHelperError
from app.services.gforms import GoogleFormsHelper, GoogleFormsHelperError
from app.services.gemini import GoogleGeminiHelper, GoogleGeminiHelperError

configure_logging()

class ScriptRunnerError(Exception):
    """Custom exception for ScriptRunner errors."""
    pass

class ScriptRunner:
    def __init__(self, config):
        self.config = config
        self.ui_handler = None
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.data = {day: {'menu': [], 'image_id': None} for day in self.days}

    async def run_script(self, selected_image_paths, ui_handler):
        self.ui_handler = ui_handler
        try:
            await self.validate_inputs(selected_image_paths)
            await self.initialize_helpers()
            week_number = datetime.now().isocalendar()[1]
            await self.process_week_folder(week_number)
            form_id = await self.check_or_create_form(week_number)
            if not form_id:  # Form already exists, stop execution
                return
            await self.upload_and_process_images(selected_image_paths, form_id)
            await self.configure_form(form_id)
            self.ui_handler.update_progress(100)
            self.ui_handler.log_message("Script finished")
        except ScriptRunnerError as e:
            self.ui_handler.log_message(str(e), error=True)
        finally:
            self.ui_handler.enable_buttons()

    async def validate_inputs(self, selected_image_paths):
        if not all(selected_image_paths.values()):
            raise ScriptRunnerError("Error: Please select an image for each day.")
        for day, path in selected_image_paths.items():
            if not is_valid_jpeg(path):
                raise ScriptRunnerError(f"Error: Invalid file type for {day}. Please select a .jpeg image.")
        self.ui_handler.update_progress(0)

    async def initialize_helpers(self):
        auth = GoogleAuth(self.config)
        credentials = auth.get_credentials()
        self.drive_helper = GoogleDriveHelper(credentials)
        self.forms_helper = GoogleFormsHelper(credentials)
        self.gemini_helper = GoogleGeminiHelper(self.config.GEMINI_API_KEY, 
                                                self.config.GEMINI_MODEL_NAME, 
                                                self.config.GEMINI_PROMPT,
                                                self.drive_helper.drive_service
                                                )

    async def process_week_folder(self, week_number):
        week_folder_name = str(week_number)
        try:
            week_folder_id = self.drive_helper.get_folder_id(week_folder_name,
                                                            self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
            if not week_folder_id:
                week_folder_id = self.drive_helper.create_folder(week_folder_name,
                                                                 self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
                self.ui_handler.log_message(f"Week folder created with id: {week_folder_id}")
        except GoogleDriveHelperError as e:
            raise ScriptRunnerError(f"Error processing week folder: {e}") from e
        self.week_folder_id = week_folder_id
        self.ui_handler.update_progress(10)

    async def check_or_create_form(self, week_number):
        form_file_name = f'Weekly_Meals_Order_Week_{week_number}'
        try:
            form_id = self.drive_helper.get_file_id(form_file_name, self.week_folder_id)
            if form_id:
                self.ui_handler.log_message(f"Form already exists with id: {form_id}")
                form = self.forms_helper.get_form(form_id)
                form_id = form.get('formId')
                self.ui_handler.log_message(
                    f"Form already exists: {self.drive_helper.get_form_webViewLink(form_id)}")
                self.ui_handler.log_message("Script finished - Form already exists")
                return None
            else:
                self.ui_handler.log_message("Form does not exist, proceeding with creation.")
                form_title = f'Meals Order for Week #{week_number}'
                form = self.forms_helper.create_form(form_title)
                if form is None:
                    raise ScriptRunnerError("Failed to create form. Exiting.")
                form_id = form['formId']
                self.ui_handler.log_message(f"Empty Form Created: formId {form_id}")
                self.ui_handler.log_message(f"Empty Form URL: {form.get('responderUri')}")
                self.drive_helper.move_file(form_id, self.week_folder_id, self.drive_helper.get_root_folder_id(),
                                            form_file_name)
                self.set_form_permissions(form_id)
                return form_id
        except (GoogleDriveHelperError, GoogleFormsHelperError) as e:
            raise ScriptRunnerError(f"Error checking or creating form: {e}") from e

    async def upload_and_process_images(self, selected_image_paths, form_id):
        for i, day in enumerate(self.days):
            file_name = f'{i + 1}.jpeg'
            try:
                uploaded_file_id = await self.async_upload_file(
                    selected_image_paths[day], file_name, self.week_folder_id, 'image/jpeg'
                )
                self.data[day]['image_id'] = uploaded_file_id
                if uploaded_file_id:
                    self.ui_handler.log_message(f"Uploaded {file_name} to week folder as {file_name}")
                    await asyncio.sleep(5)
                    try:
                        menu_data_str = await self.async_get_menu_json(uploaded_file_id)
                        self.data[day]['menu'] = json.loads(menu_data_str)
                    except (json.JSONDecodeError, GoogleGeminiHelperError) as e:
                        raise ScriptRunnerError(f"Error processing menu for {day}: {e}") from e
                else:
                    self.ui_handler.log_message(f"Failed to upload {file_name} to the week folder.", error=True)
            except ScriptRunnerError as e:
                raise
            except Exception as e:
                raise ScriptRunnerError(f"Unexpected error processing images: {e}") from e
            self.ui_handler.update_progress(10 + int((i + 1) * (90 / 5)))

    async def async_upload_file(self, file_path, file_name, folder_id, mime_type):
        """Asynchronously uploads a file."""
        # Use asyncio-compatible method for file upload if possible
        # This is a placeholder for demonstration
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.drive_helper.upload_file, file_path, file_name, folder_id, mime_type)
        except GoogleDriveHelperError as e:
            raise ScriptRunnerError(f"Error uploading file: {e}") from e

    async def async_get_menu_json(self, file_id):
        """Asynchronously gets menu data from Gemini."""
        # Use asyncio-compatible method for network requests if possible
        # This is a placeholder for demonstration
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.gemini_helper.get_menu_json_from_drive_id, file_id)
        except GoogleGeminiHelperError as e:
            raise ScriptRunnerError(f"Error getting menu data: {e}") from e

    def set_form_permissions(self, form_id):
        try:
            batch = self.drive_helper.drive_service.new_batch_http_request()
            permissions = [
                {'type': 'anyone', 'role': 'reader'},
                {'type': 'user', 'role': 'owner', 'emailAddress': self.config.YOUR_EMAIL, 'transferOwnership': True},
                {'type': 'user', 'role': 'writer', 'emailAddress': self.config.YOUR_EMAIL},
            ]
            for permission in permissions:
                batch.add(
                    self.drive_helper.drive_service.permissions().create(
                        fileId=form_id,
                        body=permission,
                        fields='id',
                        **({'transferOwnership': True} if permission['role'] == 'owner' else {}),
                    )
                )
            batch.execute()
            self.drive_helper.drive_service.permissions().create(
                fileId=form_id,
                body={'type': 'user', 'role': 'owner', 'emailAddress': self.config.YOUR_EMAIL},
                fields='id',
                transferOwnership=True
            ).execute()
        except Exception as e:
            raise ScriptRunnerError(f"Error setting form permissions: {e}") from e

    async def configure_form(self, form_id):
        try:
            for day, data in reversed(self.data.items()):
                if not data['menu'] or not data['image_id']:
                    self.ui_handler.log_message(f"Skipping {day} due to missing menu or image data.", error=True)
                    continue
                image_id = data['image_id']
                image_url = f'https://drive.google.com/uc?id={image_id}'
                requests = self.create_form_update_requests(day, image_url, data['menu'])
                self.ui_handler.log_message(f"{form_id}: Adding {day}")
                self.forms_helper.update_form(form_id, requests)
                self.ui_handler.log_message(f"{form_id}: {day} Added")
        except GoogleFormsHelperError as e:
            raise ScriptRunnerError(f"Error configuring form: {e}") from e

    def create_form_update_requests(self, day, image_url, menu):
        """Creates form update requests for a given day."""
        return [
            {
                'createItem': {
                    'item': {
                        'title': ' ',
                        'imageItem': {'image': {'sourceUri': image_url}}
                    },
                    'location': {'index': 0},
                }
            },
            {
                'createItem': {
                    'item': {
                        'title': f'Choose your soup for {day}:',
                        'questionItem': {
                            'question': {
                                'required': False,
                                'choiceQuestion': {
                                    'type': 'RADIO',
                                    'options': [{'value': item['name']} for item in menu[:2]],
                                },
                            }
                        },
                    },
                    'location': {'index': 1},
                }
            },
            {
                'createItem': {
                    'item': {
                        'title': f'Choose your main course for {day}:',
                        'questionItem': {
                            'question': {
                                'required': True,
                                'choiceQuestion': {
                                    'type': 'RADIO',
                                    'options': [{'value': item['name']} for item in menu[2:]],
                                },
                            }
                        },
                    },
                    'location': {'index': 2},
                }
            },
        ]
