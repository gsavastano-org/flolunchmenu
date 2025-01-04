from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from datetime import datetime

YOUR_EMAIL = 'gsavastano@gmail.com'
SERVICE_ACCOUNT_FILE = 'flow-lunch-menu.json'
SCOPES = ['https://www.googleapis.com/auth/forms.body',
          'https://www.googleapis.com/auth/drive']
import json

week_number = datetime.now().isocalendar()[1]

MENU_DATA = {}
DAY_IMAGE_PATHS = {}
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for i, day in enumerate(days):
    with open(f'static/menu/{week_number}/0{i+1}.json', 'r') as f:
        MENU_DATA[day] = json.load(f)
        DAY_IMAGE_PATHS[day] = f'static/pictures/{week_number}/0{i+1}.jpeg'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
forms_service = build('forms', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

form = forms_service.forms().create(body={
    'info': {'title': 'Weekly Meals Order'}
}).execute()
form_id = form['formId']

# Share ownership with your email address
batch = drive_service.new_batch_http_request()
user_permission = {
    'type': 'user',
    'role': 'owner',
    'emailAddress': YOUR_EMAIL
}
batch.add(drive_service.permissions().create(
    fileId=form_id,
    body=user_permission,
    transferOwnership=True,  # Transfer ownership to you
    fields='id',
))
batch.execute()

for day, menu in reversed(MENU_DATA.items()):
    # Upload the image to Google Drive
    file_metadata = {
        'name': f'{day}_image.jpg',
        'parents': ['10pxvySzQlNjBbyR2JFSUNfmuAhleAk0H']
    }  # Optional: Specify a folder
    media = MediaFileUpload(DAY_IMAGE_PATHS[day], mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    image_id = file.get('id')

    # Get the image URL
    image_url = f'https://drive.google.com/uc?id={image_id}'

    # Add the image to the form
    image_request = {
        'createItem': {
            'item': {
                'imageItem': {
                    'image': {
                        'sourceUri': image_url
                    }
                }
            },
            'location': {
                'index': 0
            }
        }
    }
    forms_service.forms().batchUpdate(formId=form_id,
                                     body={'requests': [image_request]}).execute()

    # Add the soup question
    soup_question = {
        'createItem': {
            'item': {
                'title': f'Choose your soup for {day}:',
                'questionItem': {
                    'question': {
                        'required': False,
                        'choiceQuestion': {
                            'type':
                            'RADIO',  # Single choice for soup
                            'options': [{
                                'value': item['name']
                            } for item in menu[:2]]  # First 2 items are soups
                        }
                    }
                }
            },
            'location': {
                'index': 1
            }
        }
    }
    forms_service.forms().batchUpdate(formId=form_id,
                                     body={'requests': [soup_question]}).execute()

    # Add the main course question
    main_question = {
        'createItem': {
            'item': {
                'title': f'Choose your main course for {day}:',
                'questionItem': {
                    'question': {
                        'required': True,
                        'choiceQuestion': {
                            'type':
                            'RADIO',  # Single choice for main course
                            'options': [{
                                'value': item['name']
                            } for item in menu[2:]]  # Items 3 to 8 are mains
                        }
                    }
                }
            },
            'location': {
                'index': 2
            }
        }
    }

    forms_service.forms().batchUpdate(formId=form_id,
                                     body={'requests': [main_question]}).execute()

print(f'Form URL: https://docs.google.com/forms/d/{form_id}/edit')