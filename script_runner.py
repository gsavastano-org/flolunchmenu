# --- Core Logic Layer: script_runner.py ---
import asyncio
import json
from datetime import datetime
from app.core.utils import configure_logging, logging, is_valid_jpeg
from app.core.auth import GoogleAuth
from app.services.gdrive import GoogleDriveHelper
from app.services.gforms import GoogleFormsHelper
from app.services.gemini import GoogleGeminiHelper

configure_logging()

class ScriptRunner:
    def __init__(self, config):
        self.config = config

    async def run_script(self, selected_image_paths, ui_handler):
        # --- Validation ---
        if not all(selected_image_paths.values()):
            ui_handler.log_message("Error: Please select an image for each day.", error=True)
            return

        for day, path in selected_image_paths.items():
            if not is_valid_jpeg(path):
                ui_handler.log_message(f"Error: Invalid file type for {day}. Please select a .jpeg image.", error=True)
                return

        ui_handler.update_progress(0)  # Reset progress

        auth = GoogleAuth(self.config)
        credentials = auth.get_credentials()

        drive_helper = GoogleDriveHelper(credentials)
        forms_helper = GoogleFormsHelper(credentials)
        gemini_helper = GoogleGeminiHelper(self.config.GEMINI_API_KEY, self.config.GEMINI_MODEL_NAME,
                                           drive_helper.drive_service)

        week_number = datetime.now().isocalendar()[1]

        MENU_DATA = {}
        NEW_IMAGE_IDS = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for i, day in enumerate(days):
            MENU_DATA[day] = []
            NEW_IMAGE_IDS[day] = None

        # --- Set the form file name and title ---
        form_file_name = f'Weekly_Meals_Order_Week_{week_number}'
        form_title = f'Meals Order for Week #{week_number}'

        # --- Use the helper to check for or create the week folder ---
        week_folder_name = str(week_number)
        week_folder_id = drive_helper.get_folder_id(week_folder_name, self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
        if not week_folder_id:
            ui_handler.log_message(f"Creating week folder: {week_folder_name}")
            week_folder_id = drive_helper.create_folder(week_folder_name, self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
            ui_handler.log_message(f"Week folder created with id: {week_folder_id}")

        # Update progress
        ui_handler.update_progress(10)

        # --- Check if form already exists using Drive helper ---
        form_id = drive_helper.get_file_id(form_file_name, week_folder_id)

        if form_id:
            # Form already exists, retrieve form using Forms helper
            ui_handler.log_message(f"Form already exists with id: {form_id}")
            form = forms_helper.get_form(form_id)
            # form_id is actually a file_id, so we need to get form_id from form
            form_id = form.get('formId')
            ui_handler.log_message(f"Form already exists: {drive_helper.get_form_webViewLink(form_id)}")
            ui_handler.log_message("Script finished - Form already exists")
            ui_handler.enable_buttons()
            return  # Stop the script if the form already exists
        else:
            ui_handler.log_message("Form does not exist, proceeding with creation.")

            # Upload the images to the week folder
            for i, day in enumerate(days):
                file_name = f'{i + 1}.jpeg'
                # Pass the file path to upload_file instead of the file object
                uploaded_file_id = drive_helper.upload_file(selected_image_paths[day], file_name, week_folder_id, 'image/jpeg')
                # override the image id with the new id
                NEW_IMAGE_IDS[day] = uploaded_file_id
                if uploaded_file_id:
                    ui_handler.log_message(f"Uploaded {file_name} to week folder as {file_name}")
                    # Add a delay after moving the file
                    await asyncio.sleep(5)  # Adjust delay as needed (e.g., 5 seconds)
                    # Process the moved image
                    menu_data_str = gemini_helper.get_menu_json_from_drive_id(uploaded_file_id)
                    if menu_data_str:
                        try:
                            MENU_DATA[day] = json.loads(menu_data_str)
                        except json.JSONDecodeError as e:
                            ui_handler.log_message(f"Error decoding JSON for {day}: {e}", error=True)
                else:
                    ui_handler.log_message(f"Failed to upload {file_name} to the week folder.", error=True)
                ui_handler.update_progress(10 + int((i + 1) * (90/5)))  # Update progress after each upload

            # --- Create the form using Forms helper ---
            form = forms_helper.create_form(form_title)

            if form is None:
                ui_handler.log_message("Failed to create form. Exiting.", error=True)
                ui_handler.enable_buttons()
                return

            form_id = form['formId']
            ui_handler.log_message(f"Empty Form Created: formId {form_id}")
            ui_handler.log_message(f"Empty Form URL: {form.get('responderUri')}")

            # --- Move the created form to the week folder using Drive helper---
            drive_helper.move_file(form_id, week_folder_id, drive_helper.get_root_folder_id(), form_file_name)

            # --- Share and set permissions for the form using Drive helper---
            batch = drive_helper.drive_service.new_batch_http_request()
            permissions = [
                {'type': 'anyone', 'role': 'reader'},
                {'type': 'user', 'role': 'owner', 'emailAddress': self.config.YOUR_EMAIL, 'transferOwnership': True},
                {'type': 'user', 'role': 'writer', 'emailAddress': self.config.YOUR_EMAIL},
            ]
            for permission in permissions:
                batch.add(
                    drive_helper.drive_service.permissions().create(
                        fileId=form_id,
                        body=permission,
                        fields='id',
                        **({'transferOwnership': True} if permission['role'] == 'owner' else {}),
                    )
                )
            batch.execute()

            # Transfer ownership
            drive_helper.drive_service.permissions().create(
                fileId=form_id,
                body={'type': 'user', 'role': 'owner', 'emailAddress': self.config.YOUR_EMAIL},
                fields='id',
                transferOwnership=True
            ).execute()

            # --- Attach images and create form questions for each day ---
            # --- Reverse the menu data to start with Friday so it's the last day in the form ---
            for day, menu in reversed(MENU_DATA.items()):
                if not menu or not NEW_IMAGE_IDS[day]:
                    ui_handler.log_message(f"Skipping {day} due to missing menu or image data.", error=True)
                    continue  # Skip to the next day if menu or image is missing

                image_id = NEW_IMAGE_IDS[day]
                if not image_id:
                    ui_handler.log_message(
                        f"Image not found in week folder for {day}. Skipping questions.", error=True)
                    continue

                # Get the image URL
                image_url = f'https://drive.google.com/uc?id={image_id}'

                # Create form update requests
                requests = [
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
                                            'options': [
                                                {'value': item['name']}
                                                for item in menu[:2]
                                            ],
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
                                            'options': [
                                                {'value': item['name']}
                                                for item in menu[2:]
                                            ],
                                        },
                                    }
                                },
                            },
                            'location': {'index': 2},
                        }
                    },
                ]

                # Update the form using Forms helper
                ui_handler.log_message(f"{form_id}: Adding {day}")
                forms_helper.update_form(form_id, requests)
                ui_handler.log_message(f"{form_id}: {day} Added")

        ui_handler.update_progress(100)  # Update progress to 100%
        ui_handler.log_message("Script finished")
        ui_handler.enable_buttons()