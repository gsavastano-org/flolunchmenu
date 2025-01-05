# Google Workspace Menu Ordering Application - Setup Guide for IT Managers

This guide provides detailed instructions for setting up the Google Workspace Menu Ordering application within your organization.

## 1. Google Cloud Project Setup

### 1.1 Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown (top left) and select **New Project**.
3. Give your project a descriptive name (e.g., "Menu-Ordering-App").
4. Choose your organization and location (if applicable).
5. Click **Create**.

### 1.2 Enable APIs

1. In your project, navigate to **APIs & Services** -> **Library**.
2. Enable the following APIs:
    * **Google Drive API**
    * **Google Forms API**
    * **Gemini API** (or Vertex AI API if you're using the Vertex AI version of Gemini)

### 1.3 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** -> **Credentials**.
2. Click **Create Credentials** -> **OAuth client ID**.
3. Select **Desktop app** as the application type.
4. Give your client a name (e.g., "Menu App Client").
5. Click **Create**.
6. Download the JSON file containing your credentials. **Rename it to `credentials.json` and place it in the project's root directory.**

**Important Security Note:** The `credentials.json` file contains sensitive information. Do not commit it to version control or share it publicly.

### 1.4 Obtain a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey).
2. Click on **Create API Key**.
3. Copy the generated API key. You will need this later.

## 2. Python Environment Setup

### 2.1 Install Python

Ensure that Python 3.12 or later is installed on your system. You can verify this by running `python --version` or `python3 --version` in your terminal.

### 2.2 Create a Virtual Environment (Recommended)

1. Navigate to the project's root directory in your terminal.
2. Create a virtual environment:
    ```bash
    python3 -m venv venv
    ```

### 2.3 Activate the Virtual Environment

* **Linux/macOS:**
    ```bash
    source venv/bin/activate
    ```
* **Windows:**
    ```bash
    venv\Scripts\activate
    ```

### 2.4 Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Application Configuration

### 3.1 Configure Environment Variables

1. Create a file named `.env` in the project's root directory.
2. Copy the contents of the example `.env` provided in the repository into your `.env` file.
3. Fill in the following values:
    * `GEMINI_API_KEY`: Paste your Gemini API key here.
    * `YOUR_EMAIL`: Enter the email address that will be used as the owner of the generated Google Forms.
    * `SERVICE_ACCOUNT_FILE`: This should be set to `credentials.json` (the file you downloaded earlier).
    * `GOOGLE_DRIVE_FOLDER_ID`: 
        1. Create a folder in your Google Drive where the application will store data (e.g., "Menu Orders").
        2. Open the folder and copy the ID from the URL (the part after `/folders/`).
        3. Paste the folder ID here.
    * `SCOPES`: This should be pre-filled with the necessary authorization scopes. Do not modify unless you have specific requirements.

**Security Note:** The `.env` file also contains sensitive information. Do not commit it to version control or share it publicly.

## 4. First-Time Authentication

1. Run the application:
    ```bash
    python app/main.py
    ```
2. The first time you run the application, it will open a browser window and prompt you to authenticate with your Google account.
3. Grant the application permission to access Google Drive and Google Forms.
4. After successful authentication, a `token.json` file will be created in the project's root directory. This file stores your authentication token, so you won't have to authenticate every time.

**Note:** If you need to re-authenticate (e.g., due to changed permissions), delete the `token.json` file and run the application again.

## 5. Automation (Optional)

You can automate the weekly execution of the script using task schedulers:
* **Linux/macOS:** Use cron jobs.
* **Windows:** Use Task Scheduler.

Refer to the documentation for your operating system on how to schedule tasks.

## 6. Troubleshooting

### Authentication Errors:

* Delete `token.json` and try again.
* Ensure `credentials.json` is correctly placed and named.

### API Errors:

* Verify that all required APIs are enabled in your Google Cloud project.
* Check your API key and other `.env` settings.

### General Errors:

* Examine the console output and log messages for debugging information.

## 7. Support

If you encounter any issues or have questions, please open an issue on the project's GitHub repository.
