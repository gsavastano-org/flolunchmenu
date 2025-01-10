import google.generativeai as genai
from app.core.utils import handle_error, logging

class GoogleGeminiHelperError(Exception):
    """Custom exception for GoogleGeminiHelper errors."""
    pass

class GoogleGeminiHelper:
    def __init__(self, api_key, model_name, prompt, drive_service):
        self.api_key = api_key
        self.model_name = model_name
        self.prompt = prompt
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

        if not self.prompt:
            handle_error("Error: prompt.txt file not found.")
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
            system_instruction=self.prompt,
        )
        return model

    def _load_image_from_drive(self, file_id):
        """Loads image data from Google Drive using its file ID."""
        if not self.drive_service:
            handle_error("Drive service not initialized.")
            raise GoogleGeminiHelperError("Drive service not initialized.")
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            response = request.execute()
            return response
        except Exception as e:
            handle_error(f"Error loading image from Google Drive: {e}")
            raise GoogleGeminiHelperError(f"Could not load image from Drive: {e}") from e

    def get_menu_json_from_drive_id(self, file_id):
        """Generates a menu JSON string for the given Google Drive file ID."""
        if self.model is None:
            handle_error("Gemini model not configured.")
            raise GoogleGeminiHelperError("Gemini model not configured.")

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
                    raise GoogleGeminiHelperError("No candidates returned in the response.")

                return response.candidates[0].content.parts[0].text

            except Exception as e:
                handle_error(f"An error occurred during the message sending: {e}")
                raise GoogleGeminiHelperError(f"Error during message sending: {e}") from e
        else:
            handle_error("Could not load the image from Google Drive.")
            raise GoogleGeminiHelperError("Could not load the image from Google Drive.")
