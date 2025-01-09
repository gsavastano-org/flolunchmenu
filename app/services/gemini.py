import google.generativeai as genai
from app.core.utils import handle_error, configure_logging, logging

configure_logging()

class GoogleGeminiHelper:
    def __init__(self, api_key, model_name, drive_service):
        self.api_key = api_key
        self.model_name = model_name
        self.model = self._configure_model()
        self.drive_service = drive_service

    def _configure_model(self):
        """Configures and returns the Gemini model."""
        try:
            genai.configure(api_key=self.api_key)
        except KeyError:
            handle_error(
                f"Error: GEMINI_API_KEY environment variable not set. "
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
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction="""## Purpose and Goals

*   The input menu image contains multiple dishes, their name, and their allergens.
*   Analyze the input image to identify individual menu dishes.
*   Extrapolate names and allergens, ignore prices.

## Behaviors and Rules

1. **Image Processing:**
    *   Analyze the input image to identify individual menu dishes.
    *   Extrapolate names and allergens, ignore prices

2. **JSON Creation:**
    *   Order the items the same way they appear on the image, from left to right, from top line to bottom.
    *   **Strictly return only valid JSON. Do not include any text outside of the JSON structure.**

**Required JSON Format:**

```json
[
  {
    "name": "Spaghetti Bolognese",
    "allergens": "(3,9)"
  },
  {
    "name": "Soup of the day",
    "allergens": "(1,3,9)"
  }
]
```
""",
        )
        return model

    def _load_image_from_drive(self, file_id):
        """Loads image data from Google Drive using its file ID."""
        if not self.drive_service:
            handle_error("Drive service not initialized.")
            return None
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            response = request.execute()
            return response
        except Exception as e:
            handle_error(f"Error loading image from Google Drive: {e}")
            return None

    def get_menu_json_from_drive_id(self, file_id):
        """Generates a menu JSON string for the given Google Drive file ID."""
        if self.model is None:
            handle_error("Gemini model not configured.")
            return None

        image_data = self._load_image_from_drive(file_id)
        if image_data:
            image_part = {"mime_type": "image/jpeg", "data": image_data}

            text_prompt = "Analyze the menu in the image and extract the dishes and their allergens in JSON format."

            try:
                response = self.model.generate_content([text_prompt, image_part])

                if response.prompt_feedback:
                    logging.warning(f"Prompt feedback: {response.prompt_feedback}")

                if not response.candidates:
                    handle_error("No candidates returned in the response.")
                    return None

                return response.candidates[0].content.parts[0].text

            except Exception as e:
                handle_error(f"An error occurred during the message sending: {e}")
                return None
        else:
            handle_error("Could not load the image from Google Drive.")
            return None
