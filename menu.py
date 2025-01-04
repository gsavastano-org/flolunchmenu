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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    logging.error("Error: GEMINI_API_KEY environment variable not set. Please set it in your .env file.")
    exit(1)

# Create the model
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
  system_instruction="## Purpose and Goals\n\n* The input menu  image contains multiple dishes, their name, their allergens and picture\n\n## Behaviors and Rules\n\n1. **Image Processing:**\n    - Analyze the input image to identify individual menu dishes.\n    - Extrapolate names and allergens, ignore prices\n\n2. **JSON Creation:**\n    - Order the items the same way they appear on the image, from left to right, from top line to bottom.\n\nHere is an example of the format that you should return the data in:\n\n```json\n[\n  {\n     \"name\": \"Spaghetti Bolognese\",\n     \"allergens\": \"(3,9)\",\n  },\n  {\n     \"name\": \"Soup of the day\",\n     \"allergens\": \"(1,3,9)\",\n  }\n]\n```",
)


def upload_menu_image(file_path: str) -> Optional[Any]:
    """Returns the uploaded file from the given file path."""
    mime_type, _ = mimetypes.guess_type(file_path)

    if not mime_type:
        logging.error(f"Could not determine mime type for {file_path}")
        return None

    try:
      uploaded_file = genai.upload_file(
          file_path, mime_type=mime_type
      )
      return uploaded_file
    except Exception as e:
      logging.error(f"Error uploading the image {file_path}: {e}")
      return None


def get_menu(filename: str) -> Optional[str]:
    """Generates a menu JSON string for the given filename."""
    uploaded_menu = upload_menu_image(filename)

    if uploaded_menu:
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [uploaded_menu],
                },
            ]
        )
        try:
            response = chat_session.send_message("Extract the menu please.")
            return response.text
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON response: {e}")
            print(f"Error parsing JSON response: {response.text}")
            return None
        except Exception as e:
            logging.error(f"An error occurred during the message sending: {e}")
            return None
    else:
        print("Could not get the menu. Please see the logs for details.")


def process_menu(filename: str):
    """Generates a menu JSON file for the given filename."""
    week_number = datetime.now().isocalendar()[1]
    menu_dir = os.path.join("static", "menu", str(week_number))
    print(f"Processing menu for {filename}...")
    print(f"Menu directory: {menu_dir}")
    os.makedirs(menu_dir, exist_ok=True)

    menu_data = get_menu(filename)
    if menu_data:
        base_name = os.path.splitext(os.path.basename(filename))[0]
        with open(os.path.join(menu_dir, base_name + ".json"), "w") as f:
            f.write(menu_data)
        print("Menu saved successfully.")
    else:
        print("Could not get the menu. Please see the logs for details.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        process_menu(filename)
    else:
        print("Please provide a filename as a command line argument.")
