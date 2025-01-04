from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from dotenv import load_dotenv
import os
import json

load_dotenv()

YOUR_EMAIL = os.getenv('YOUR_EMAIL')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SCOPES = json.loads(os.getenv('SCOPES'))
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

week_number = datetime.now().isocalendar()[1]

MENU_DATA = {}
DAY_IMAGE_PATHS = {}
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for i, day in enumerate(days):
    with open(f'static/menu/{week_number}/0{i+1}.json', 'r') as f:
        MENU_DATA[day] = json.load(f)
        DAY_IMAGE_PATHS[day] = f'static/pictures/{week_number}/0{i+1}.jpeg'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
forms_service = build('forms', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

# --- Set the form file name and title---
form_file_name = f'Weekly_Meals_Order_Week_{week_number}'
form_title = f'Meals Order for Week #{week_number}'

# --- Check if the week folder exists, create if not ---
week_folder_name = str(week_number)
query = f"mimeType='application/vnd.google-apps.folder' and name='{week_folder_name}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"
results = drive_service.files().list(
    q=query, fields="files(id)"
).execute()
week_folder_id = None

if results.get('files'):
    week_folder_id = results.get('files')[0].get('id')
else:
    file_metadata_folder = {
        'name': week_folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [GOOGLE_DRIVE_FOLDER_ID],
    }
    folder = drive_service.files().create(
        body=file_metadata_folder, fields='id'
    ).execute()
    week_folder_id = folder.get('id')

# --- Check if form already exists in the week folder ---
query = f"name='{form_file_name}' and '{week_folder_id}' in parents and trashed=false"
results = drive_service.files().list(q=query, fields="files(id)").execute()
existing_form = results.get('files')

if existing_form:
    # Form already exists, retrieve formId
    form_id = existing_form[0].get('id')
    print(f"Form already exists: https://docs.google.com/forms/d/{form_id}/edit")
else:
    # --- Create the form ---
    form = forms_service.forms().create(
        body={'info': {'title': form_title}}
    ).execute()
    form_id = form['formId']
    print(f"Form created: https://docs.google.com/forms/d/{form_id}/edit")

    # --- Move and rename the created form to the week folder ---
    drive_service.files().update(
        fileId=form_id,
        addParents=week_folder_id,
        body={'name': form_file_name},
        fields='id, parents',
    ).execute()

    # --- Share and set permissions for the form ---
    batch = drive_service.new_batch_http_request()

    # Permissions: Anyone with link can view, owner and writer
    permissions = [
        {'type': 'anyone', 'role': 'reader'},
        {'type': 'user', 'role': 'owner', 'emailAddress': YOUR_EMAIL, 'transferOwnership': True},
        {'type': 'user', 'role': 'writer', 'emailAddress': YOUR_EMAIL},
    ]

    for permission in permissions:
        batch.add(
            drive_service.permissions().create(
                fileId=form_id,
                body=permission,
                fields='id',
                **({'transferOwnership': True} if permission['role'] == 'owner' else {}),
            )
        )

    batch.execute()

    # --- Upload images and create form questions ---
    for day, menu in reversed(MENU_DATA.items()):
        # Check if image already exists
        image_file_name = f'{day}_image.jpg'
        query = f"name='{image_file_name}' and '{week_folder_id}' in parents and trashed=false"
        results = drive_service.files().list(
            q=query, fields="files(id)"
        ).execute()
        image_id = None

        if results.get('files'):
            image_id = results.get('files')[0].get('id')
        else:
            # Upload the image
            file_metadata = {
                'name': image_file_name,
                'parents': [week_folder_id],
            }
            media = MediaFileUpload(
                DAY_IMAGE_PATHS[day], mimetype='image/jpeg'
            )
            file = drive_service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()
            image_id = file.get('id')

        # Get the image URL
        image_url = f'https://drive.google.com/uc?id={image_id}'

        # Create form update requests
        requests = [
            {
                'createItem': {
                    'item': {
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

        # Update the form
        forms_service.forms().batchUpdate(
            formId=form_id, body={'requests': requests}
        ).execute()