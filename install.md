# Installing the Google Workspace Menu Ordering Application

This guide helps you install and run the Google Workspace Menu Ordering application.

## Prerequisites

1. **Google Cloud Project:**
    *   Create a project in the Google Cloud Console.
2. **Enable APIs:**
    *   Enable the following APIs in your Google Cloud project:
        *   Google Drive API
        *   Google Forms API
        *   Vertex AI API (for Gemini)
3. **Create OAuth Credentials:**
    *   Go to **APIs & Services** -> **Credentials** in the Google Cloud Console.
    *   Click **Create Credentials** -> **OAuth client ID**.
    *   Choose **Desktop app** as the application type.
    *   Give it a name (e.g., "Menu Ordering App").
    *   Click **Create**.
    *   Download the JSON file containing your credentials and save it as `credentials.json` in the project's root directory.
4. **Install Python:**
    *   Make sure you have Python 3.7 or later installed on your system.
5. **Install `pip`:**
    *   `pip` is usually installed with Python. You can verify by running `pip --version` in your terminal.

## Installation Steps

1. **Clone the Repository (or Download the Code):**
    ```bash
    git clone <repository_url>  # Replace with the actual repository URL
    cd <repository_name>
    ```

2. **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    ```

3. **Activate the Virtual Environment:**
    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```

4. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Configure Environment Variables (Continued):**
    *   Create a file named `.env` in the project's root directory.
    *   Copy the contents of the example `.env` provided in the repository into your `.env` file.
    *   Fill in the values for:
        *   `GEMINI_API_KEY`: Your Gemini API key.
        *   `YOUR_EMAIL`: Your email address (used for form ownership).
        *   `GOOGLE_DRIVE_FOLDER_ID`: The ID of the main Google Drive folder where the application will store data.
        *   `SCOPES`: The necessary authorization scopes (should be pre-filled).

    **Important:**
    *   **Do not share your `.env` file or commit it to version control.** It contains sensitive information.
    *   **Do not share your `credentials.json` file or commit it to version control.** It contains sensitive information.

6. **Run the Application:**
    ```bash
    python app/main.py
    ```

## First-Time Run

*   The first time you run the application, it will open a browser window and ask you to authenticate with your Google account.
*   Grant the application the necessary permissions to access Google Drive and Google Forms.
*   After successful authentication, a `token.json` file will be created in the project's root directory. This file stores your authentication token, so you don't have to authenticate every time you run the application.

## Usage

1. **Prepare Menu Images:**
    *   Make sure you have image files named `1.jpeg`, `2.jpeg`, ..., `5.jpeg` (for Monday to Friday) in a folder named `new_menus` within your designated Google Drive folder (the `GOOGLE_DRIVE_FOLDER_ID` you set in your `.env` file).
2. **Run the Script:**
    *   Execute the script using `python app/main.py`.
3. **Check Google Drive:**
    *   The script will create a new folder for the current week (named with the week number) inside your designated Google Drive folder.
    *   Inside the week folder, you'll find:
        *   The menu images (`1.jpeg` to `5.jpeg`).
        *   A Google Form named `Weekly_Meals_Order_Week_<week_number>`.
4. **Share the Form:**
    *   Open the generated Google Form.
    *   Click the **Send** button to share the form with your users (e.g., via email or by embedding it on a website).

## Troubleshooting

*   **Authentication Errors:**
    *   If you encounter authentication errors, delete the `token.json` file and try running the script again.
    *   Make sure the `credentials.json` file is correctly placed in the project's root directory.
*   **API Errors:**
    *   Ensure that you have enabled the Google Drive API, Google Forms API, and Vertex AI API in your Google Cloud project.
    *   Verify that your API key and other configuration settings in the `.env` file are correct.
*   **Other Errors:**
    *   Check the console output for error messages.
    *   Use the logging information to help debug the issue.

## Notes

*   This application is designed to be run weekly. You can automate the execution using task schedulers (like cron on Linux/macOS or Task Scheduler on Windows) or by deploying it to a cloud environment.
*   Consider adding a user interface (e.g., using a web framework) to make the application more user-friendly.
*   Implement organization-specific settings if you plan to distribute this application to multiple organizations.

## Disclaimer

This application is provided as a starting point and may require further modifications to meet your specific needs. Use it responsibly and be aware of Google API usage limits and quotas.