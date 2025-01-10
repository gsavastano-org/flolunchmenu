# Weekly Meal Order Form Generator

This application generates a Google Form for weekly meal orders by analyzing menu images using Google Gemini and creating a structured form with the extracted meal options.

## Project Setup on Google Cloud Console

To use this application, you need to set up a project on Google Cloud Console and configure the necessary services and credentials. Here's a step-by-step guide:

### Step 1: Create a Google Cloud Project

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  If you don't have a project, click on "Select a project" at the top, then "New Project".
3.  Enter a **Project name** (e.g., `flolunchmenu`) and a **Project ID** (e.g., `gs-playground-446613`, this should be unique)
    .
4.  Click "Create".

### Step 2: Enable APIs

1.  In your project, navigate to **APIs & Services > Library**.
2.  Enable the following APIs:
    *   **Google Drive API:** Search for "Google Drive API" and click "Enable".
    *   **Google Forms API:** Search for "Google Forms API" and click "Enable".
    *   **Generative Language API:** Search for "Generative Language API" and click "Enable".

### Step 3: Create OAuth 2.0 Credentials

1.  In your project, navigate to **APIs & Services > Credentials**.
2.  Click on **+ CREATE CREDENTIALS** and select **OAuth client ID**.
3.  Select **Desktop app** as the application type, give it a name (e.g., `WeeklyMealOrder`).
4.  Click **Create**.
5.  Click **Download JSON** to download the credentials file.
6.  Rename the downloaded file to `credentials.json` and save it in the `app/core/` directory of your project.
    *   **Important:** Make sure that the path defined in your `.env` file `GOOGLE_OAUTH2_FILE=app/core/credentials.json` matches the file location you just set up.

### Step 4: Configure Environment Variables

1.  Create a `.env` file in the root directory of your project.
2.  Add the following environment variables to the `.env` file.  
    *   You can find the Project ID in the Google Cloud console under Project info.
    *   You'll get the Project Folder ID after you create it in the next step.

    ```env
    GEMINI_API_KEY=<your_gemini_api_key>
    GEMINI_MODEL_NAME=gemini-2.0-flash-exp
    GOOGLE_PROJECT_UUID=<your_google_project_id>
    GOOGLE_OAUTH2_FILE=app/core/credentials.json
    GOOGLE_PROJECT_SCOPES=["https://www.googleapis.com/auth/forms.body","https://www.googleapis.com/auth/drive"]
    GOOGLE_DRIVE_PROJECT_FOLDER_ID=<your_google_drive_project_folder_id>
    YOUR_EMAIL=<your_email>
    ```
    *   Replace placeholders like `<your_gemini_api_key>`, `<your_google_project_id>`, `<your_google_drive_project_folder_id>`, and `<your_email>` with your actual values.
    *   **GEMINI_API_KEY**: Get this from [Google AI Studio](https://makersuite.google.com/). Create a new API key under "Get API Key", and make sure the Google Cloud project selected in that page is the same one as the project ID you are using here.
    *   **GOOGLE_PROJECT_UUID**: This is your Google Cloud Project ID.
    *  **GOOGLE_OAUTH2_FILE**: This is the path to your `credentials.json` file.
    *  **GOOGLE_PROJECT_SCOPES**:  These are the necessary permissions the app needs.
    *  **GOOGLE_DRIVE_PROJECT_FOLDER_ID**:  This is the ID of the folder where all the forms and folders related to your app will be stored. You need to create this folder in the next step
    *   **YOUR_EMAIL**: This is the email address that you use for Google Cloud.

### Step 5: Create the Google Drive Project Folder

1. Go to [Google Drive](https://drive.google.com).
2. Create a new folder that will serve as the root folder of your application
3. Get the folder ID from the URL (e.g. `https://drive.google.com/drive/folders/10pxvySzQlNjBbyR2JFSUNfmuAhleAk0H` the folder id will be `10pxvySzQlNjBbyR2JFSUNfmuAhleAk0H`)
4. Update the `GOOGLE_DRIVE_PROJECT_FOLDER_ID` in the .env file with that ID.

## Building the macOS Application (optional)

This project includes a `build-dmg.sh` script to automate the process of building the application for macOS.

### Prerequisites

*   Python 3.11 or higher with [Homebrew](https://brew.sh/)
*   [PyInstaller](https://pyinstaller.org/)
*   `hdiutil` (usually pre-installed on macOS)

### Steps

1. **Prepare the developement environment**

* install Python (with Homebrew)
    ```bash
    # install Homebrew
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # install Python 3.11
    brew install python@3.11
    ```

* **IMPORTANT: restart your terminal**

* create a project directory
    ```bash
    # create the directory
    mkdir flo-lunch-menu

    # clone the repo
    git clone https://github.com/gsavastano-org/flolunchmenu.git flo-lunch-menu

    # move in the project directory
    cd flo-lunch-menu
    
    # setup and start Python environment
    python3.11 -m venv .venv

    # activate the environment
    source .venv/bin/activate

    # install requirements
    pip install -r requirements.txt
    ```

* Install PyInstaller if you haven't already.
    ```bash
    pip install pyinstaller
    ```

2.  **Ensure the application files are set up correctly**:
    *   Verify that the `.env` file is in the root of the repository.
    *   Verify that you placed the `credentials.json` file inside the `app/core/` folder, as per step 3.
    *   Verify that the app icon `app/assets/icon.icns` is in place.

3.  **Run the `build-dmg.sh` script** from the project root:
    ```bash
    ./build-dmg.sh
    ```
4.  The script will:
    *   Use PyInstaller to create a standalone application bundle.
    *   Create a DMG file containing the application.
    *   The output `WeeklyMealOrder.dmg` will be created in the same directory as the script.

5. Open the `WeeklyMealOrder.dmg` and double click on`WeeklyMealOrder.app` to start the application.

### Troubleshooting

*   **Permissions issues:** Ensure the script has execute permissions (`chmod +x build-dmg.sh`).
*   **PyInstaller issues:** Check the PyInstaller documentation for common errors.
*   **Missing files:** Verify that paths to the files in the script and in your `.env` are correct.

## .env File Configuration
Here's a description of the variables in the .env file:

*   **GEMINI_API_KEY**: Your Google Gemini API key from Google AI Studio.
*   **GEMINI_MODEL_NAME**: The name of the Gemini model used for text generation, by default is `gemini-2.0-flash-exp`.
*   **GOOGLE_PROJECT_UUID**: The ID of your Google Cloud project.
*   **GOOGLE_OAUTH2_FILE**: The path to the OAuth 2.0 client secrets JSON file.
*   **GOOGLE_PROJECT_SCOPES**: A JSON array of required API scopes (Forms and Drive).
*   **GOOGLE_DRIVE_PROJECT_FOLDER_ID**: The ID of the Google Drive folder where forms and menu images are stored.
*   **YOUR_EMAIL**: The email address associated with your Google Cloud account.

This setup should allow you to run the application successfully and generate weekly meal order forms based on the menu images you provide.
