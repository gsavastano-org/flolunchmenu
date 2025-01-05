# Google Workspace Menu Ordering Application

Automate the creation of weekly meal order forms using Google Workspace and Gemini AI.

## Overview

This application simplifies the process of creating weekly meal order forms for organizations using Google Workspace (Google Drive and Google Forms). It leverages the power of Gemini AI to extract menu information from images, automatically generating interactive forms for users to place their orders.

## Features

*   **Automated Form Creation:** Generates Google Forms for weekly meal orders based on uploaded menu images.
*   **Gemini AI Integration:** Uses Gemini AI to analyze menu images and extract dish names and allergen information.
*   **Google Drive Management:** Organizes weekly menus and forms in a designated Google Drive folder structure.
*   **Customizable:** Adaptable to different organizational needs (with potential future enhancements).
*   **Easy to Use:** Simple setup and intuitive workflow for both administrators and end-users.

## How It Works

1. **Image Upload:** Menu images for each day of the week are uploaded to a specific folder in Google Drive.
2. **Gemini AI Processing:** The application uses Gemini AI to analyze the images, identifying dishes and their corresponding allergens.
3. **Form Generation:** A Google Form is automatically created with the extracted menu information, allowing users to select their meal choices.
4. **Form Distribution:** The generated form can be easily shared with users via a link or embedded in a website.

## Prerequisites

*   Google Cloud Project with enabled APIs (Google Drive, Google Forms, Gemini)
*   OAuth 2.0 Client ID credentials
*   Gemini API Key
*   Python 3.12+
*   `pip` package manager

## Installation

Detailed installation instructions for IT managers and technical teams can be found in the [SETUP.md](SETUP.md) file.


## Disclaimer

This application is provided as-is and may require modifications to suit specific needs. Please be aware of Google API usage limits and quotas.