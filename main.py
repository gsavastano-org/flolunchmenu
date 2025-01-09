import asyncio
import json
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
from app.core.utils import configure_logging, logging
from app.core.config import Config
from app.core.auth import GoogleAuth
from app.services.gdrive import GoogleDriveHelper
from app.services.gforms import GoogleFormsHelper
from app.services.gemini import GoogleGeminiHelper

configure_logging()

class ScriptRunner:
    def __init__(self, config, output_widget):
        self.config = config
        self.output_widget = output_widget

    async def run_script(self):
        auth = GoogleAuth(self.config)
        credentials = auth.get_credentials()

        drive_helper = GoogleDriveHelper(credentials)
        forms_helper = GoogleFormsHelper(credentials)
        gemini_helper = GoogleGeminiHelper(self.config.GEMINI_API_KEY, self.config.GEMINI_MODEL_NAME,
                                           drive_helper.drive_service)

        week_number = datetime.now().isocalendar()[1]

        MENU_DATA = {}
        DAY_IMAGE_PATHS = {}
        NEW_IMAGE_IDS = {}
        OLD_IMAGE_IDS = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for i, day in enumerate(days):
            MENU_DATA[day] = []
            DAY_IMAGE_PATHS[day] = None
            NEW_IMAGE_IDS[day] = None
            OLD_IMAGE_IDS[day] = None

        # --- Set the form file name and title ---
        form_file_name = f'Weekly_Meals_Order_Week_{week_number}'
        form_title = f'Meals Order for Week #{week_number}'

        # --- Use the helper to check for or create the week folder ---
        week_folder_name = str(week_number)
        week_folder_id = drive_helper.get_folder_id(week_folder_name, self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
        if not week_folder_id:
            self.log_message(f"Creating week folder: {week_folder_name}")
            week_folder_id = drive_helper.create_folder(week_folder_name, self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
            self.log_message(f"Week folder created with id: {week_folder_id}")

        # --- Check if form already exists using Drive helper ---
        form_id = drive_helper.get_file_id(form_file_name, week_folder_id)

        if form_id:
            # Form already exists, retrieve form using Forms helper
            self.log_message(f"Form already exists with id: {form_id}")
            form = forms_helper.get_form(form_id)
            # form_id is actually a file_id, so we need to get form_id from form
            form_id = form.get('formId')
            self.log_message(f"Form already exists: {drive_helper.get_form_webViewLink(form_id)}")
            self.log_message("Script finished - Form already exists")
            return  # Stop the script if the form already exists
        else:
            self.log_message("Form does not exist, proceeding with creation.")

            # Check if images already exist in the week's folder
            images_exist_in_week_folder = True
            for i in range(1, 6):
                image_file_name = f'{i}.jpeg'
                image_id = drive_helper.get_file_id(image_file_name, week_folder_id)
                if not image_id:
                    images_exist_in_week_folder = False
                    break
                else:
                    OLD_IMAGE_IDS[days[i - 1]] = image_id

            if images_exist_in_week_folder and len(OLD_IMAGE_IDS) == 5:
                self.log_message("Images found in the week's folder. Processing with Gemini.")
                for i, day in enumerate(days):
                    menu_data_str = gemini_helper.get_menu_json_from_drive_id(OLD_IMAGE_IDS[day])
                    if menu_data_str:
                        try:
                            MENU_DATA[day] = json.loads(menu_data_str)
                            DAY_IMAGE_PATHS[day] = image_file_name  # Use filename as it's already in the target
                        except json.JSONDecodeError as e:
                            self.log_message(f"Error decoding JSON for {day}: {e}")
            else:
                # Check the input folder for images
                input_folder_id = drive_helper.get_folder_id(self.config.GOOGLE_DRIVE_INPUT_FOLDER_NAME,
                                                             self.config.GOOGLE_DRIVE_PROJECT_FOLDER_ID)
                if input_folder_id:
                    self.log_message(
                        f"Checking input folder for images: {self.config.GOOGLE_DRIVE_INPUT_FOLDER_NAME}")
                    images_found_in_input = True
                    for i in range(1, 6):
                        image_file_name = f'{i}.jpeg'
                        image_id = drive_helper.get_file_id(image_file_name, input_folder_id)
                        if not image_id:
                            self.log_message(f"Image {image_file_name} not found in the input folder.")
                            images_found_in_input = False
                            break
                        else:
                            NEW_IMAGE_IDS[days[i - 1]] = image_id

                    if images_found_in_input and len(NEW_IMAGE_IDS) == 5:
                        self.log_message(
                            "All images found in the input folder. Moving to week folder and processing.")
                        for i, day in enumerate(days):
                            file_name = f'{i + 1}.jpeg'               
                            moved_file_id = drive_helper.move_file(NEW_IMAGE_IDS[day], week_folder_id,
                                                                    input_folder_id,
                                                                    new_name=file_name)
                            # override the image id with the new id
                            NEW_IMAGE_IDS[day] = moved_file_id
                            if moved_file_id:
                                self.log_message(f"Moved {file_name} to week folder as {file_name}")
                                # Add a delay after moving the file
                                await asyncio.sleep(5)  # Adjust delay as needed (e.g., 5 seconds)
                                # Process the moved image
                                menu_data_str = gemini_helper.get_menu_json_from_drive_id(moved_file_id)
                                if menu_data_str:
                                    try:
                                        MENU_DATA[day] = json.loads(menu_data_str)
                                        DAY_IMAGE_PATHS[day] = file_name
                                    except json.JSONDecodeError as e:
                                        self.log_message(f"Error decoding JSON for {day}: {e}")
                            else:
                                self.log_message(f"Failed to move {file_name} to the week folder.")

                    else:
                        self.log_message("Not all images found in the input folder. Exiting.")
                        return
                else:
                    self.log_message(
                        f"Input folder '{self.config.GOOGLE_DRIVE_INPUT_FOLDER_NAME}' not found. Exiting.")
                    return

            # --- Create the form using Forms helper ---
            self.log_message(f"Creating form with title: {form_title}")
            form = forms_helper.create_form(form_title)

            if form is None:
                self.log_message("Failed to create form. Exiting.")
                return

            form_id = form['formId']
            self.log_message(f"Empty Form Created: formId {form_id}")
            self.log_message(f"Empty Form URL: {form.get('responderUri')}")

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
                if not menu or not DAY_IMAGE_PATHS[day]:
                    self.log_message(f"Skipping {day} due to missing menu or image data.")
                    continue  # Skip to the next day if menu or image is missing

                image_file_name = DAY_IMAGE_PATHS[day]
                image_id = NEW_IMAGE_IDS[day]
                if not image_id:
                    self.log_message(
                        f"Image {image_file_name} not found in week folder for {day}. Skipping questions.")
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
                self.log_message(f"Updating form with id: {form_id} for {day}")
                forms_helper.update_form(form_id, requests)
                self.log_message(f"Form updated for {day}")

        self.log_message("Script finished")

    def log_message(self, message):
        """Logs a message to the output widget and console."""
        logging.info(message)
        self.output_widget.insert(tk.END, message + "\n")
        self.output_widget.see(tk.END)  # Scroll to the end

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Script Runner")
        self.pack()
        self.create_widgets()
        self.script_runner = None

    def create_widgets(self):
        self.start_button = tk.Button(self, text="Start", command=self.run_script_in_thread)
        self.start_button.pack(pady=20)

        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create Exit button but don't pack it yet
        self.exit_button = tk.Button(self, text="Exit", command=self.master.destroy, state=tk.DISABLED) 

    def run_script_in_thread(self):
        self.start_button.config(state=tk.DISABLED)
        self.output_text.delete('1.0', tk.END)  # Clear output

        config = Config()
        self.script_runner = ScriptRunner(config, self.output_text)

        # Run the script in a separate thread
        thread = Thread(target=self.run_async_script)
        thread.start()

    def run_async_script(self):
        asyncio.run(self.script_runner.run_script())
        self.master.after(0, self.enable_buttons)  # Enable buttons after script completion

    def enable_buttons(self):
        self.start_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.NORMAL) # Enable the exit button
        self.exit_button.pack(pady=10)  # Now pack the Exit button

def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()