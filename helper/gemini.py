# helper/gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import logging
from typing import Optional
from googleapiclient.discovery import build

load_dotenv()

# Configure logging (consider moving this to a central logging config)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleGeminiHelper:
    def __init__(self, api_key_env_var="GEMINI_API_KEY", drive_service=None):
        self.api_key_env_var = api_key_env_var
        self.model = self._configure_model()
        self.drive_service = drive_service

    def _configure_model(self):
        """Configures and returns the Gemini model."""
        try:
            genai.configure(api_key=os.environ[self.api_key_env_var])
        except KeyError:
            logging.error(
                f"Error: {self.api_key_env_var} environment variable not set. "
                f"Please set it in your .env file."
            )
            return None

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
            system_instruction="## Purpose and Goals\n\n* The input menu image contains multiple dishes, their name, their allergens and picture\n\n## Behaviors and Rules\n\n1. **Image Processing:**\n    - Analyze the input image to identify individual menu dishes.\n    - Extrapolate names and allergens, ignore prices\n\n2. **JSON Creation:**\n    - Order the items the same way they appear on the image, from left to right, from top line to bottom.\n\nHere is an example of the format that you should return the data in:\n\n```json\n[\n  {\n     \"name\": \"Spaghetti Bolognese\",\n     \"allergens\": \"(3,9)\",\n  },\n  {\n     \"name\": \"Soup of the day\",\n     \"allergens\": \"(1,3,9)\",\n  }\n]\n```",
        )
        return model

    def _load_image_from_drive(self, file_id: str) -> Optional[bytes]:
        """Loads image data from Google Drive using its file ID."""
        if not self.drive_service:
            logging.error("Drive service not initialized.")
            return None
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            response = request.execute()
            return response
        except Exception as e:
            logging.error(f"Error loading image from Google Drive: {e}")
            return None

    def get_menu_json_from_drive_id(self, file_id: str) -> Optional[str]:
        """Generates a menu JSON string for the given Google Drive file ID."""
        if self.model is None:
            logging.error("Gemini model not configured.")
            return None

        image_data = self._load_image_from_drive(file_id)
        if image_data:
            image_part = {"mime_type": "image/jpeg", "data": image_data}

            # Add a text prompt
            text_prompt = "Analyze the menu in the image and extract the dishes and their allergens in JSON format."

            try:
                # Pass both the text prompt and the image part to generate_content
                response = self.model.generate_content([text_prompt, image_part])

                # Check for prompt feedback or candidates
                if response.prompt_feedback:
                    logging.warning(f"Prompt feedback: {response.prompt_feedback}")

                if not response.candidates:
                    logging.error("No candidates returned in the response.")
                    return None

                # Extract and return the text from the first candidate
                return response.candidates[0].content.parts[0].text

            except Exception as e:
                logging.error(f"An error occurred during the message sending: {e}")
                return None
        else:
            logging.error("Could not load the image from Google Drive.")
            return None