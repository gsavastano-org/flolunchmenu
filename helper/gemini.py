# helper/gemini.py

import os
import glob
import google.generativeai as genai
from dotenv import load_dotenv
import mimetypes
import json
import logging
from datetime import datetime
from typing import Optional, Any

load_dotenv()

# Configure logging (consider moving this to a central logging config)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleGeminiHelper:
    def __init__(self, api_key_env_var="GEMINI_API_KEY"):
        self.api_key_env_var = api_key_env_var
        self.model = self._configure_model()

    def _configure_model(self):
        """Configures and returns the Gemini model."""
        try:
            genai.configure(api_key=os.environ[self.api_key_env_var])
        except KeyError:
            logging.error(
                f"Error: {self.api_key_env_var} environment variable not set. "
                f"Please set it in your .env file."
            )
            return None  # Return None to indicate failure

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",  # or your preferred model
            generation_config=generation_config,
            system_instruction="## Purpose and Goals\n\n* The input menu  image contains multiple dishes, their name, their allergens and picture\n\n## Behaviors and Rules\n\n1. **Image Processing:**\n    - Analyze the input image to identify individual menu dishes.\n    - Extrapolate names and allergens, ignore prices\n\n2. **JSON Creation:**\n    - Order the items the same way they appear on the image, from left to right, from top line to bottom.\n\nHere is an example of the format that you should return the data in:\n\n```json\n[\n  {\n     \"name\": \"Spaghetti Bolognese\",\n     \"allergens\": \"(3,9)\",\n  },\n  {\n     \"name\": \"Soup of the day\",\n     \"allergens\": \"(1,3,9)\",\n  }\n]\n```",
        )
        return model

    def upload_menu_image(self, file_path: str) -> Optional[Any]:
        """Returns the uploaded file from the given file path."""
        mime_type, _ = mimetypes.guess_type(file_path)

        if not mime_type:
            logging.error(f"Could not determine mime type for {file_path}")
            return None

        try:
            uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
            return uploaded_file
        except Exception as e:
            logging.error(f"Error uploading the image {file_path}: {e}")
            return None

    def get_menu_json(self, filename: str) -> Optional[str]:
        """Generates a menu JSON string for the given filename."""
        if self.model is None:
            logging.error("Gemini model not configured.")
            return None
        
        uploaded_menu = self.upload_menu_image(filename)

        if uploaded_menu:
            chat_session = self.model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [uploaded_menu],
                    },
                ]
            )
            try:
                response = chat_session.send_message("Extract the menu please.")
                # Clean the response to remove markdown code block delimiters
                cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
                return cleaned_response
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing JSON response: {e}")
                print(f"Error parsing JSON response: {response.text}")
                return None
            except Exception as e:
                logging.error(f"An error occurred during the message sending: {e}")
                return None
        else:
            logging.error("Could not get the menu. Please see the logs for details.")
            return None

    def process_menu(self, filename: str):
        """Generates a menu JSON file for the given filename."""
        week_number = datetime.now().isocalendar()[1]
        menu_dir = os.path.join("static", "menu", str(week_number))
        logging.info(f"Processing menu for {filename}...")
        logging.info(f"Menu directory: {menu_dir}")
        os.makedirs(menu_dir, exist_ok=True)

        menu_data = self.get_menu_json(filename)
        if menu_data:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            json_file_path = os.path.join(menu_dir, base_name + ".json")
            try:
                with open(json_file_path, "w") as f:
                    # Attempt to parse and then dump the JSON to format it nicely
                    parsed_json = json.loads(menu_data)
                    json.dump(parsed_json, f, indent=2)
                logging.info(f"Menu saved successfully to {json_file_path}")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON for formatting: {e}")
                # Fallback to writing the raw string if parsing fails
                with open(json_file_path, "w") as f:
                    f.write(menu_data)
                logging.info(f"Menu saved with potential formatting issues to {json_file_path}")
        else:
            logging.error("Could not get the menu. Please see the logs for details.")