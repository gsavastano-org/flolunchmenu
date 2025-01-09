import asyncio
import json
from datetime import datetime
from app.core.utils import configure_logging, logging
from app.core.config import Config
from app.core.auth import GoogleAuth
from app.services.gdrive import GoogleDriveHelper
from app.services.gforms import GoogleFormsHelper
from app.services.gemini import GoogleGeminiHelper

configure_logging()

async def main():
    config = Config()
    auth = GoogleAuth(config)
    credentials = auth.get_credentials()

    drive_helper = GoogleDriveHelper(credentials)
    forms_helper = GoogleFormsHelper(credentials)
    gemini_helper = GoogleGeminiHelper(config.GEMINI_API_KEY, config.GEMINI_MODEL_NAME, drive_helper.drive_service)

    week_number = datetime.now().isocalendar()[1]

    MENU_DATA = {}
    DAY_IMAGE_PATHS = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for i, day in enumerate(days):
        MENU_DATA[day] = []
        DAY_IMAGE_PATHS[day] = None

    # --- Set the form file name and title ---
    form_file_name = f'Weekly_Meals_Order_Week_{week_number}'
    form_title = f'Meals Order for Week #{week_number}'

    # --- Use the helper to check for or create the week folder ---
    week_folder_name = str(week_number)
    week_folder_id = drive_helper.get_folder_id(week_folder_name, config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
    if not week_folder_id:
        logging.info(f"Creating week folder: {week_folder_name}")
        week_folder_id = drive_helper.create_folder(week_folder_name, config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
        logging.info(f"Week folder created with id: {week_folder_id}")

    # --- Check if form already exists using Drive helper ---
    form_id = drive_helper.get_file_id(form_file_name, week_folder_id)

    if form_id:
        # Form already exists, retrieve form using Forms helper
        logging.info(f"Form already exists with id: {form_id}")
        form = forms_helper.get_form(form_id)
        # form_id is actually a file_id, so we need to get form_id from form
        form_id = form.get('formId')
        logging.info(f"Retrieved form with formId: {form_id}")
        print(f"Form already exists: {drive_helper.get_form_webViewLink(form_id)}")
        logging.info("Script finished - Form already exists")
        return  # Stop the script if the form already exists
    else:
        logging.info("Form does not exist, proceeding with creation.")

        # Check if images already exist in the week's folder
        images_exist_in_week_folder = True
        for i in range(1, 6):
            image_file_name = f'{i}.jpeg'
            image_id = drive_helper.get_file_id(image_file_name, week_folder_id)
            if not image_id:
                images_exist_in_week_folder = False
                break

        if images_exist_in_week_folder:
            logging.info("Images found in the week's folder. Processing with Gemini.")
            for i, day in enumerate(days):
                image_file_name = f'{i + 1}.jpeg'
                image_id = drive_helper.get_file_id(image_file_name, week_folder_id)
                if image_id:
                    # Pass the file ID to Gemini helper
                    menu_data_str = gemini_helper.get_menu_json_from_drive_id(image_id)
                    if menu_data_str:
                        try:
                            MENU_DATA[day] = json.loads(menu_data_str)
                            DAY_IMAGE_PATHS[day] = image_file_name  # Use filename as it's already in the target
                        except json.JSONDecodeError as e:
                            logging.error(f"Error decoding JSON for {day}: {e}")
                else:
                    logging.warning(f"Image {image_file_name} not found in week folder for {day}.")

        else:
            # Check the input folder for images
            input_folder_id = drive_helper.get_folder_id(config.GOOGLE_DRIVE_INPUT_FOLDER_NAME, config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
            if input_folder_id:
                logging.info(f"Checking input folder for images: {config.GOOGLE_DRIVE_INPUT_FOLDER_NAME}")
                images_found_in_input = True
                for i in range(1, 6):
                    image_file_name = f'{i}.jpeg'
                    image_id = drive_helper.get_file_id(image_file_name, input_folder_id)
                    if not image_id:
                        logging.warning(f"Image {image_file_name} not found in the input folder.")
                        images_found_in_input = False
                        break

                if images_found_in_input:
                    logging.info("All images found in the input folder. Moving to week folder and processing.")
                    for i, day in enumerate(days):
                        file_name = f'{i + 1}.jpeg'
                        source_file_id = drive_helper.get_file_id(file_name, input_folder_id)
                        if source_file_id:
                            # Move the file
                            moved_file_id = drive_helper.move_file(source_file_id, week_folder_id, input_folder_id,
                                                                   new_name=file_name)
                            if moved_file_id:
                                logging.info(f"Moved {file_name} to week folder as {file_name}")
                                # Add a delay after moving the file
                                await asyncio.sleep(5)  # Adjust delay as needed (e.g., 5 seconds)
                                # Process the moved image
                                menu_data_str = gemini_helper.get_menu_json_from_drive_id(moved_file_id)
                                if menu_data_str:
                                    try:
                                        MENU_DATA[day] = json.loads(menu_data_str)
                                        DAY_IMAGE_PATHS[day] = file_name
                                    except json.JSONDecodeError as e:
                                        logging.error(f"Error decoding JSON for {day}: {e}")
                            else:
                                logging.error(f"Failed to move {file_name} to the week folder.")
                        else:
                            logging.error(f"Could not find {file_name} in the input folder.")

                else:
                    logging.warning("Not all images found in the input folder. Exiting.")
                    return
            else:
                logging.warning(f"Input folder '{config.GOOGLE_DRIVE_INPUT_FOLDER_NAME}' not found. Exiting.")
                return

        # --- Create the form using Forms helper ---
        logging.info(f"Creating form with title: {form_title}")
        form = forms_helper.create_form(form_title)

        if form is None:
            logging.error("Failed to create form. Exiting.")
            return

        form_id = form['formId']
        logging.info(f"Form created with formId: {form_id}")
        print(f"Form created: {form.get('responderUri')}")

        # --- Move the created form to the week folder using Drive helper---
        drive_helper.move_file(form_id, week_folder_id, drive_helper.get_root_folder_id(), form_file_name)

        # --- Share and set permissions for the form using Drive helper---
        batch = drive_helper.drive_service.new_batch_http_request()
        permissions = [
            {'type': 'anyone', 'role': 'reader'},
            {'type': 'user', 'role': 'owner', 'emailAddress': config.YOUR_EMAIL, 'transferOwnership': True},
            {'type': 'user', 'role': 'writer', 'emailAddress': config.YOUR_EMAIL},
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
            body={'type': 'user', 'role': 'owner', 'emailAddress': config.YOUR_EMAIL},
            fields='id',
            transferOwnership=True
        ).execute()

        # --- Attache images and create form questions for each day---
        for day, menu in reversed(MENU_DATA.items()):
            if not menu or not DAY_IMAGE_PATHS[day]:
                logging.warning(f"Skipping {day} due to missing menu or image data.")
                continue  # Skip to the next day if menu or image is missing

            image_file_name = DAY_IMAGE_PATHS[day]
            image_id = drive_helper.get_file_id(image_file_name, week_folder_id)
            if not image_id:
                logging.error(f"Image {image_file_name} not found in week folder for {day}. Skipping questions.")
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
            logging.info(f"Updating form with id: {form_id} for {day}")
            forms_helper.update_form(form_id, requests)
            logging.info(f"Form updated for {day}")

    logging.info("Script finished")

if __name__ == "__main__":
    asyncio.run(main())