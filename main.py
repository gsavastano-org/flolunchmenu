from datetime import datetime
from dotenv import load_dotenv
import os
import json
import logging
from helper.gdrive import GoogleDriveHelper
from helper.gforms import GoogleFormsHelper

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the script")

YOUR_EMAIL = os.getenv('YOUR_EMAIL')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SCOPES = json.loads(os.getenv('SCOPES'))
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

# Initialize the GoogleDriveHelper and GoogleFormsHelper
drive_helper = GoogleDriveHelper(credentials_path=SERVICE_ACCOUNT_FILE, scopes=SCOPES)
forms_helper = GoogleFormsHelper(credentials_path=SERVICE_ACCOUNT_FILE, scopes=SCOPES)

week_number = datetime.now().isocalendar()[1]

MENU_DATA = {}
DAY_IMAGE_PATHS = {}
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for i, day in enumerate(days):
    if os.path.exists(f'static/menu/{week_number}/0{i+1}.json'):
        with open(f'static/menu/{week_number}/0{i+1}.json', 'r') as f:
            MENU_DATA[day] = json.load(f)
    else:
        logging.warning(f"Menu file not found for {day} (week {week_number}). Skipping day.")
        MENU_DATA[day] = []  # Handle case where menu file is missing

    if os.path.exists(f'static/pictures/{week_number}/0{i+1}.jpeg'):
        DAY_IMAGE_PATHS[day] = f'static/pictures/{week_number}/0{i+1}.jpeg'
    else:
        logging.warning(f"Image file not found for {day} (week {week_number}). Skipping day.")
        DAY_IMAGE_PATHS[day] = None # Handle case where image file is missing
    

# --- Set the form file name and title ---
form_file_name = f'Weekly_Meals_Order_Week_{week_number}'
form_title = f'Meals Order for Week #{week_number}'

# --- Use the helper to check for or create the week folder ---
week_folder_name = str(week_number)
week_folder_id = drive_helper.get_folder_id(week_folder_name, GOOGLE_DRIVE_FOLDER_ID)
if not week_folder_id:
    logging.info(f"Creating week folder: {week_folder_name}")
    week_folder_id = drive_helper.create_folder(week_folder_name, GOOGLE_DRIVE_FOLDER_ID)
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
    exit() # Stop the script if the form already exists
else:
    # --- Create the form using Forms helper ---
    logging.info(f"Creating form with title: {form_title}")
    form = forms_helper.create_form(form_title)
    form_id = form['formId']
    logging.info(f"Form created with formId: {form_id}")
    print(f"Form created: {form.get('responderUri')}")

    # --- Move the created form to the week folder using Drive helper---
    drive_helper.drive_service.files().update(
        fileId=form_id,
        addParents=week_folder_id,
        removeParents=drive_helper.drive_service.files().get(fileId=form_id, fields='parents').execute().get('parents')[0], # Get the current parents of the file and remove them
        body={'name': form_file_name},
        fields='id, parents',
    ).execute()

    # --- Share and set permissions for the form using Drive helper---
    batch = drive_helper.drive_service.new_batch_http_request()
    permissions = [
        {'type': 'anyone', 'role': 'reader'},
        {'type': 'user', 'role': 'owner', 'emailAddress': YOUR_EMAIL, 'transferOwnership': True},
        {'type': 'user', 'role': 'writer', 'emailAddress': YOUR_EMAIL},
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

# --- Upload images and create form questions ---
for day, menu in reversed(MENU_DATA.items()):
    if not menu or not DAY_IMAGE_PATHS[day]:
        logging.warning(f"Skipping {day} due to missing menu or image data.")
        continue  # Skip to the next day if menu or image is missing
    
    # Check if image exists and upload if needed using Drive helper
    image_file_name = f'{day}_image.jpg'
    image_id = drive_helper.get_file_id(image_file_name, week_folder_id)
    if not image_id:
        logging.info(f"Uploading image for {day}: {image_file_name}")
        image_id = drive_helper.upload_image(DAY_IMAGE_PATHS[day], image_file_name, week_folder_id)
        logging.info(f"Image uploaded with id: {image_id}")

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